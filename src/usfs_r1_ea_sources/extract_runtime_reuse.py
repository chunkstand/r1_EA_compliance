from __future__ import annotations

from pathlib import Path
import hashlib
import json

from .extract_chunking import _blocks_from_plain_text
from .extract_chunking import _chunks_for_payload
from .extract_common import CURRENT_REUSE_INVENTORY_CLASSIFICATIONS
from .extract_common import ExtractionPayload
from .extract_common import _failed_record
from .extract_common import _parser_metadata_with_reuse
from .extract_common import _payload_cache_path
from .extract_common import _read_json
from .extract_common import _resolve_existing_path
from .extract_common import _text_path
from .extract_common import _write_json
from .extract_docling_support import _payload_from_wire
from .extract_docling_support import _payload_to_wire
from .source_set_support import source_derived_dir


def _record_and_chunks_from_payload(
    *,
    row: dict,
    base_record: dict,
    payload: ExtractionPayload,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    payload_cache_dir: Path,
    extracted_at: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    write_text: bool,
    reused: bool,
    reuse_metadata: dict[str, object] | None = None,
) -> tuple[dict, list[dict]]:
    artifact_sha256 = row["artifact_sha256"]
    text = payload.text.strip()
    if not text:
        record = _failed_record(
            base_record,
            status="empty_text",
            error_class="empty_text",
            message="Parser produced no text.",
        )
        record["artifact_sha256_verified"] = True
        record["parser_name"] = payload.parser_name
        record["parser_version"] = payload.parser_version
        return record, []

    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    text_path = _text_path(
        extracted_text_dir,
        source_record_id=row["source_record_id"],
        artifact_sha256=artifact_sha256,
    )
    if write_text:
        text_path.write_text(text + "\n", encoding="utf-8")

    docling_json_path = None
    if payload.docling_json is not None:
        docling_json_path = docling_json_dir / f"{artifact_sha256[:16]}.json"
        if write_text or not docling_json_path.exists():
            _write_json(docling_json_path, payload.docling_json)

    if write_text:
        payload_cache_dir.mkdir(parents=True, exist_ok=True)
        _write_json(_payload_cache_path(payload_cache_dir, row), _payload_to_wire(payload))

    row_chunks = _chunks_for_payload(
        row=row,
        payload=payload,
        extracted_at=extracted_at,
        source_text_path=text_path,
        max_chars=chunk_max_chars,
        overlap_chars=chunk_overlap_chars,
    )
    record = dict(base_record)
    parser_metadata = dict(payload.metadata or {})
    if reuse_metadata:
        parser_metadata.update(
            {
                key: value
                for key, value in reuse_metadata.items()
                if value is not None
            }
        )
    record.update(
        {
            "status": "extracted",
            "artifact_sha256_verified": True,
            "parser_name": payload.parser_name,
            "parser_version": payload.parser_version,
            "parser_metadata": _parser_metadata_with_reuse(parser_metadata, reused=reused),
            "text_path": str(text_path),
            "docling_json_path": str(docling_json_path) if docling_json_path else None,
            "text_char_count": len(text),
            "text_sha256": text_sha256,
            "chunk_count": len(row_chunks),
            "failure": None,
        }
    )
    return record, row_chunks


def _reuse_existing_extraction(
    *,
    row: dict,
    base_record: dict,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    payload_cache_dir: Path,
    extracted_at: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
) -> tuple[dict, list[dict]] | None:
    text_path = _text_path(
        extracted_text_dir,
        source_record_id=row["source_record_id"],
        artifact_sha256=row["artifact_sha256"],
    )
    if not text_path.exists() or not text_path.is_file():
        return None

    payload_path = _payload_cache_path(payload_cache_dir, row)
    payload = None
    reuse_metadata = {
        "reuse_from": "current_payload_cache",
        "reuse_source_set_id": row.get("source_set_id"),
        "reuse_payload_cache_path": str(payload_path),
        "verified_reuse_admissible": True,
    }
    if payload_path.exists():
        try:
            payload = _payload_from_wire(_read_json(payload_path))
        except (KeyError, TypeError, json.JSONDecodeError):
            payload = None
    if payload is None:
        text = text_path.read_text(encoding="utf-8").strip()
        if not text:
            return None
        text, blocks = _blocks_from_plain_text(text)
        payload = ExtractionPayload(
            text=text,
            blocks=blocks,
            parser_name="reused_extracted_text",
            parser_version="1",
            metadata={
                "reuse_from": "current_extracted_text",
                "reuse_without_parser_payload": True,
            },
        )
        reuse_metadata = {
            "reuse_from": "current_extracted_text",
            "reuse_source_set_id": row.get("source_set_id"),
            "verified_reuse_admissible": False,
        }

    return _record_and_chunks_from_payload(
        row=row,
        base_record=base_record,
        payload=payload,
        extracted_text_dir=extracted_text_dir,
        docling_json_dir=docling_json_dir,
        payload_cache_dir=payload_cache_dir,
        extracted_at=extracted_at,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        write_text=False,
        reused=True,
        reuse_metadata=reuse_metadata,
    )


def _reuse_inventory_extraction(
    *,
    row: dict,
    base_record: dict,
    output_dir: Path,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    payload_cache_dir: Path,
    extracted_at: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    inventory_record: dict,
) -> tuple[dict, list[dict]] | None:
    classification = inventory_record.get("classification")
    if classification in CURRENT_REUSE_INVENTORY_CLASSIFICATIONS:
        candidate = inventory_record.get("current_extraction")
        reuse_from = "inventory_current_extraction"
    elif classification == "reuse_extraction":
        candidate = inventory_record.get("reuse_candidate")
        reuse_from = "inventory_prior_extraction"
    else:
        return None

    if not isinstance(candidate, dict):
        return None
    if not _reuse_inventory_record_matches_row(inventory_record, candidate, row):
        return None

    source_text_path = _resolve_existing_path(output_dir, candidate.get("text_path"))
    if source_text_path is None or not source_text_path.is_file():
        return None

    text = source_text_path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    expected_text_sha256 = candidate.get("text_sha256")
    actual_text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if expected_text_sha256 and actual_text_sha256 != expected_text_sha256:
        return None

    candidate_payload_path = _candidate_payload_cache_path(output_dir, candidate)
    payload = _load_candidate_payload_cache(candidate_payload_path)
    reuse_metadata = {
        "reuse_from": reuse_from,
        "reuse_inventory_classification": classification,
        "reuse_source_set_id": candidate.get("source_set_id"),
        "reuse_text_path": str(source_text_path),
        "reuse_text_sha256": actual_text_sha256,
        "verified_reuse_admissible": bool(payload is not None),
        "reuse_payload_cache_path": str(candidate_payload_path) if candidate_payload_path else None,
    }
    if payload is None:
        text, blocks = _blocks_from_plain_text(text)
        metadata = {
            **(candidate.get("parser_metadata") or {}),
            "reuse_without_parser_payload": True,
        }
        payload = ExtractionPayload(
            text=text,
            blocks=blocks,
            parser_name=candidate.get("parser_name") or "reused_extracted_text",
            parser_version=str(candidate.get("parser_version") or "1"),
            metadata=metadata,
        )
    return _record_and_chunks_from_payload(
        row=row,
        base_record=base_record,
        payload=payload,
        extracted_text_dir=extracted_text_dir,
        docling_json_dir=docling_json_dir,
        payload_cache_dir=payload_cache_dir,
        extracted_at=extracted_at,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        write_text=True,
        reused=True,
        reuse_metadata=reuse_metadata,
    )


def _reuse_inventory_record_matches_row(
    inventory_record: dict,
    candidate: dict,
    row: dict,
) -> bool:
    if inventory_record.get("source_record_id") != row.get("source_record_id"):
        return False
    if inventory_record.get("source_set_id") != row.get("source_set_id"):
        return False
    for field in ("source_record_id", "artifact_sha256", "expected_parser", "content_type"):
        expected = row.get(field)
        if expected is None:
            continue
        for value in (inventory_record.get(field), candidate.get(field)):
            if value is not None and str(value) != str(expected):
                return False
    if candidate.get("status") != "extracted":
        return False
    if int(candidate.get("chunk_count") or 0) <= 0:
        return False
    artifact_check = inventory_record.get("artifact_check") or {}
    return artifact_check.get("passed") is not False


def _candidate_payload_cache_path(output_dir: Path, candidate: dict) -> Path | None:
    source_set_id = str(candidate.get("source_set_id") or "").strip()
    source_record_id = str(candidate.get("source_record_id") or "").strip()
    artifact_sha256 = str(candidate.get("artifact_sha256") or "").strip()
    if not source_set_id or not source_record_id or not artifact_sha256:
        return None
    return _payload_cache_path(
        source_derived_dir(output_dir / "derived", source_set_id) / "diagnostics" / "payload_cache",
        {
            "source_record_id": source_record_id,
            "artifact_sha256": artifact_sha256,
        },
    )


def _load_candidate_payload_cache(path: Path | None) -> ExtractionPayload | None:
    if path is None or not path.exists():
        return None
    try:
        return _payload_from_wire(_read_json(path))
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
