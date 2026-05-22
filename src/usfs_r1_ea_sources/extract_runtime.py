from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
from typing import Any

from .extract_chunking import _blocks_from_plain_text
from .extract_chunking import _chunks_for_payload
from .extract_common import CURRENT_REUSE_INVENTORY_CLASSIFICATIONS
from .extract_common import NON_EXTRACTABLE_SOURCE_STATUSES
from .extract_common import SUCCESS_STATUSES
from .extract_common import ExtractionBuildResult
from .extract_common import ExtractionFailure
from .extract_common import ExtractionPayload
from .extract_common import _base_manifest_record
from .extract_common import _docling_ocr_for_row
from .extract_common import _failed_record
from .extract_common import _load_proving_placeholder_artifact
from .extract_common import _load_reuse_inventory_records
from .extract_common import _parser_metadata_with_reuse
from .extract_common import _payload_cache_path
from .extract_common import _prefers_docling_for_row
from .extract_common import _read_json
from .extract_common import _read_jsonl
from .extract_common import _resolve_artifact_path
from .extract_common import _resolve_existing_path
from .extract_common import _skipped_record
from .extract_common import _text_path
from .extract_common import _utc_now
from .extract_common import _write_json
from .extract_common import _write_jsonl
from .extract_docling_support import _payload_from_wire
from .extract_docling_support import _payload_to_wire
from .extract_validation import _merge_selected_chunks
from .extract_validation import _merge_selected_records
from .extract_validation import _summary
from .extract_validation import _summary_represents_full_catalog
from .extract_validation import _validation_report
from .records import sha256_file
from .source_set_support import load_support_document_role_overrides
from .source_set_support import resolve_support_document_role
from .source_set_support import source_derived_dir

def build_extraction(
    facade_module: Any,
    *,
    output_dir: Path,
    catalog_dir: Path | None = None,
    id_filter: str | None = None,
    id_filters: set[str] | None = None,
    parser_filter: str | None = None,
    limit: int | None = None,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    prefer_docling: bool = False,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 300.0,
    allow_invalid_catalog: bool = False,
    reuse_existing: bool = False,
    reuse_inventory_path: Path | None = None,
    merge_selected_into_existing: bool = False,
) -> ExtractionBuildResult:
    """Build derived extracted text and chunks from the reviewer catalog."""

    if chunk_max_chars < 256:
        raise ValueError("chunk_max_chars must be at least 256")
    if chunk_overlap_chars < 0:
        raise ValueError("chunk_overlap_chars cannot be negative")
    if chunk_overlap_chars >= chunk_max_chars:
        raise ValueError("chunk_overlap_chars must be smaller than chunk_max_chars")
    if docling_timeout_seconds is not None and docling_timeout_seconds <= 0:
        docling_timeout_seconds = None

    catalog_dir = Path(catalog_dir) if catalog_dir else output_dir / "catalog"
    manifest_path = catalog_dir / "source_set_manifest.json"
    sqlite_path = catalog_dir / "review_sources.sqlite"
    validation_path = catalog_dir / "catalog_validation.json"
    _ensure_catalog_ready(
        manifest_path=manifest_path,
        sqlite_path=sqlite_path,
        validation_path=validation_path,
        allow_invalid_catalog=allow_invalid_catalog,
    )

    source_set_manifest = _read_json(manifest_path)
    source_set_id = source_set_manifest["source_set_id"]
    reuse_inventory_records = _load_reuse_inventory_records(
        reuse_inventory_path,
        source_set_id=source_set_id,
    )
    preserve_existing_outputs = reuse_existing or reuse_inventory_records is not None
    derived_dir = output_dir / "derived"
    source_derived_root = source_derived_dir(derived_dir, source_set_id)
    selected_ids = set(id_filters or set())
    if id_filter:
        selected_ids.add(id_filter)
    merge_selected_into_existing = bool(
        merge_selected_into_existing and selected_ids and source_derived_root.exists()
    )
    if source_derived_root.exists() and not preserve_existing_outputs and not merge_selected_into_existing:
        shutil.rmtree(source_derived_root)
    extracted_text_dir = source_derived_root / "extracted_text"
    docling_json_dir = source_derived_root / "docling_json"
    chunks_dir = source_derived_root / "chunks"
    diagnostics_dir = source_derived_root / "diagnostics"
    payload_cache_dir = diagnostics_dir / "payload_cache"
    for directory in (extracted_text_dir, docling_json_dir, chunks_dir, diagnostics_dir):
        directory.mkdir(parents=True, exist_ok=True)
    if preserve_existing_outputs:
        payload_cache_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_dir / "chunks.jsonl"
    extraction_manifest_path = diagnostics_dir / "extraction_manifest.jsonl"
    extraction_validation_path = diagnostics_dir / "extraction_validation.json"
    summary_path = diagnostics_dir / "summary.json"

    rows = _load_catalog_rows(
        sqlite_path,
        source_set_id=source_set_id,
        id_filters=selected_ids or None,
        parser_filter=parser_filter,
        limit=limit,
    )
    existing_manifest_records = []
    existing_chunks = []
    existing_summary = None
    if merge_selected_into_existing:
        existing_manifest_records = (
            _read_jsonl(extraction_manifest_path) if extraction_manifest_path.exists() else []
        )
        existing_chunks = _read_jsonl(chunks_path) if chunks_path.exists() else []
        existing_summary = _read_json(summary_path) if summary_path.exists() else None
    validation_rows = rows
    if merge_selected_into_existing:
        existing_source_record_ids = {
            str(record.get("source_record_id") or "") for record in existing_manifest_records
        }
        validation_source_record_ids = sorted(existing_source_record_ids | selected_ids)
        if _summary_represents_full_catalog(existing_summary):
            validation_source_record_ids = []
        validation_rows = _load_catalog_rows(
            sqlite_path,
            source_set_id=source_set_id,
            id_filters=set(validation_source_record_ids) or None,
            parser_filter=None,
            limit=None,
        )
    extracted_at = _utc_now()
    refreshed_manifest_records: list[dict] = []
    refreshed_chunks: list[dict] = []

    for row in rows:
        record, row_chunks = _extract_row(
            facade_module=facade_module,
            row=row,
            output_dir=output_dir,
            extracted_text_dir=extracted_text_dir,
            docling_json_dir=docling_json_dir,
            extracted_at=extracted_at,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            prefer_docling=prefer_docling,
            docling_ocr=docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
            reuse_existing=reuse_existing,
            reuse_inventory_record=(reuse_inventory_records or {}).get(row["source_record_id"]),
            reuse_inventory_enforced=reuse_inventory_records is not None,
            payload_cache_dir=payload_cache_dir,
        )
        refreshed_manifest_records.append(record)
        refreshed_chunks.extend(row_chunks)

    if merge_selected_into_existing:
        manifest_records = _merge_selected_records(
            existing_manifest_records,
            refreshed_manifest_records,
            replace_source_record_ids=selected_ids,
        )
        chunks = _merge_selected_chunks(
            existing_chunks,
            refreshed_chunks,
            replace_source_record_ids=selected_ids,
        )
        filters = (
            {"id": None, "ids": None, "parser": None, "limit": None}
            if _summary_represents_full_catalog(existing_summary)
            else dict((existing_summary or {}).get("filters") or {})
            or {
                "id": id_filter,
                "ids": sorted(validation_source_record_ids) if validation_source_record_ids else None,
                "parser": None,
                "limit": None,
            }
        )
    else:
        manifest_records = refreshed_manifest_records
        chunks = refreshed_chunks
        filters = {
            "id": id_filter,
            "ids": sorted(selected_ids) if selected_ids else None,
            "parser": parser_filter,
            "limit": limit,
        }

    _write_jsonl(chunks_path, chunks)
    _write_jsonl(extraction_manifest_path, manifest_records)
    validation = _validation_report(
        source_set_id=source_set_id,
        rows=validation_rows,
        manifest_records=manifest_records,
        chunks=chunks,
    )
    summary = _summary(
        source_set_id=source_set_id,
        source_set_manifest=source_set_manifest,
        rows=validation_rows,
        manifest_records=manifest_records,
        chunks=chunks,
        validation=validation,
        chunks_path=chunks_path,
        extraction_manifest_path=extraction_manifest_path,
        validation_path=extraction_validation_path,
        summary_path=summary_path,
        filters=filters,
        extraction_options={
            "catalog_dir": str(catalog_dir),
            "chunk_max_chars": chunk_max_chars,
            "chunk_overlap_chars": chunk_overlap_chars,
            "prefer_docling": prefer_docling,
            "docling_ocr": docling_ocr,
            "docling_timeout_seconds": docling_timeout_seconds,
            "reuse_existing": reuse_existing,
            "reuse_inventory_path": str(reuse_inventory_path) if reuse_inventory_path else None,
            "merge_selected_into_existing": merge_selected_into_existing,
            "refresh_source_record_ids": sorted(selected_ids) if merge_selected_into_existing else None,
        },
    )
    _write_json(extraction_validation_path, validation)
    _write_json(summary_path, summary)

    return ExtractionBuildResult(
        source_set_id=source_set_id,
        derived_dir=derived_dir,
        extracted_text_dir=extracted_text_dir,
        docling_json_dir=docling_json_dir,
        chunks_path=chunks_path,
        extraction_manifest_path=extraction_manifest_path,
        validation_path=extraction_validation_path,
        summary_path=summary_path,
        summary=summary,
    )



def _ensure_catalog_ready(
    *,
    manifest_path: Path,
    sqlite_path: Path,
    validation_path: Path,
    allow_invalid_catalog: bool,
) -> None:
    missing = [path for path in (manifest_path, sqlite_path, validation_path) if not path.exists()]
    if missing:
        paths = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing reviewer catalog output(s): {paths}")
    if allow_invalid_catalog:
        return
    validation = _read_json(validation_path)
    if not validation.get("passed"):
        raise ValueError(
            f"Reviewer catalog validation has not passed: {validation_path}. "
            "Rebuild or validate the catalog, or pass --allow-invalid-catalog."
        )


def _load_catalog_rows(
    sqlite_path: Path,
    *,
    source_set_id: str,
    id_filters: set[str] | None,
    parser_filter: str | None,
    limit: int | None,
) -> list[dict]:
    support_document_role_overrides = load_support_document_role_overrides()
    query = """
        SELECT
          s.source_record_id,
          s.source_set_id,
          s.sheet,
          s.excel_row,
          s.source_id,
          s.title,
          s.document_role,
          s.authority_level,
          s.issuer,
          s.scope,
          s.layer,
          s.document_type,
          s.unit_or_overlay,
          s.applies_to,
          s.trigger,
          s.review_engine_checks,
          s.currentness_notes,
          s.original_url,
          s.effective_url,
          s.normalized_url,
          s.host,
          s.expected_parser,
          s.source_status,
          s.source_partition,
          s.source_partition_basis,
          s.metadata_json,
          c.citation_label,
          c.final_url AS citation_final_url,
          c.retrieved_at,
          sa.download_run_id,
          a.artifact_sha256,
          a.artifact_path,
          a.artifact_byte_size,
          a.content_type,
          a.final_url AS artifact_final_url
        FROM sources s
        LEFT JOIN citations c ON c.source_record_id = s.source_record_id
        LEFT JOIN source_artifacts sa ON sa.source_record_id = s.source_record_id
        LEFT JOIN artifacts a ON a.artifact_sha256 = sa.artifact_sha256
        WHERE s.source_set_id = ?
    """
    params: list[object] = [source_set_id]
    if id_filters:
        placeholders = ", ".join("?" for _ in id_filters)
        query += f" AND s.source_record_id IN ({placeholders})"
        params.extend(sorted(id_filters))
    if parser_filter:
        query += " AND s.expected_parser = ?"
        params.append(parser_filter)
    query += " ORDER BY s.source_record_id"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(query, params).fetchall()]

    for row in rows:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        row["support_document_role"] = resolve_support_document_role(
            row,
            support_document_role_overrides=support_document_role_overrides,
        )
    return rows


def _extract_row(
    facade_module: Any,
    *,
    row: dict,
    output_dir: Path,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    extracted_at: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    prefer_docling: bool,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
    reuse_existing: bool,
    reuse_inventory_record: dict | None,
    reuse_inventory_enforced: bool,
    payload_cache_dir: Path,
) -> tuple[dict, list[dict]]:
    base_record = _base_manifest_record(row=row, extracted_at=extracted_at)
    if row.get("source_status") in NON_EXTRACTABLE_SOURCE_STATUSES:
        return _skipped_record(
            base_record,
            status=str(row.get("source_status")),
            reason="Catalog row is explicitly non-extractable.",
        ), []

    artifact_path_value = row.get("artifact_path")
    artifact_sha256 = row.get("artifact_sha256")
    if (
        not artifact_path_value
        or not artifact_sha256
        or row.get("source_status") not in SUCCESS_STATUSES
    ):
        return (
            _failed_record(
                base_record,
                status="no_artifact",
                error_class="no_artifact",
                message="Catalog row is not linked to a successful raw artifact.",
            ),
            [],
        )

    artifact_path = _resolve_artifact_path(output_dir, artifact_path_value)
    if not artifact_path.exists():
        return (
            _failed_record(
                base_record,
                status="artifact_missing",
                error_class="artifact_missing",
                message=f"Artifact path does not exist: {artifact_path}",
            ),
            [],
        )
    if not artifact_path.is_file():
        return (
            _failed_record(
                base_record,
                status="artifact_missing",
                error_class="artifact_not_file",
                message=f"Artifact path is not a file: {artifact_path}",
            ),
            [],
        )

    actual_sha256 = sha256_file(artifact_path)
    if actual_sha256 != artifact_sha256:
        record = dict(base_record)
        record.update(
            {
                "status": "hash_mismatch",
                "actual_artifact_sha256": actual_sha256,
                "artifact_sha256_verified": False,
                "failure": {
                    "error_class": "hash_mismatch",
                    "error_message": "Artifact SHA256 does not match reviewer catalog.",
                },
            }
        )
        return record, []

    placeholder_artifact = _load_proving_placeholder_artifact(artifact_path)
    if placeholder_artifact is not None:
        record = dict(base_record)
        record.update(
            {
                "status": "placeholder_artifact",
                "artifact_sha256_verified": True,
                "artifact_is_proving_placeholder": True,
                "proving_placeholder_schema_version": placeholder_artifact.get("schema_version"),
                "parser_metadata": {
                    "placeholder_artifact": placeholder_artifact,
                },
                "failure": None,
            }
        )
        return record, []

    row_prefer_docling = prefer_docling or _prefers_docling_for_row(row)
    row_docling_ocr = docling_ocr or _docling_ocr_for_row(row)
    allow_current_reuse = reuse_existing and (
        not reuse_inventory_enforced
        or (reuse_inventory_record or {}).get("classification")
        in CURRENT_REUSE_INVENTORY_CLASSIFICATIONS
    )
    if allow_current_reuse:
        reused = _reuse_existing_extraction(
            row=row,
            base_record=base_record,
            extracted_text_dir=extracted_text_dir,
            docling_json_dir=docling_json_dir,
            payload_cache_dir=payload_cache_dir,
            extracted_at=extracted_at,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
        )
        if reused is not None:
            return reused
    if reuse_inventory_record is not None:
        reused = _reuse_inventory_extraction(
            row=row,
            base_record=base_record,
            output_dir=output_dir,
            extracted_text_dir=extracted_text_dir,
            docling_json_dir=docling_json_dir,
            payload_cache_dir=payload_cache_dir,
            extracted_at=extracted_at,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            inventory_record=reuse_inventory_record,
        )
        if reused is not None:
            return reused

    try:
        payload = facade_module._extract_payload(
            row=row,
            artifact_path=artifact_path,
            prefer_docling=row_prefer_docling,
            docling_ocr=row_docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
        )
    except ExtractionFailure as error:
        status = "parser_timeout" if error.error_class == "docling_timeout" else "parser_error"
        record = _failed_record(
            base_record,
            status=status,
            error_class=error.error_class,
            message=error.message,
        )
        record["artifact_sha256_verified"] = True
        return record, []

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
        reused=False,
    )


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
    record.update(
        {
            "status": "extracted",
            "artifact_sha256_verified": True,
            "parser_name": payload.parser_name,
            "parser_version": payload.parser_version,
            "parser_metadata": _parser_metadata_with_reuse(payload.metadata, reused=reused),
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
                "reuse_from": "extracted_text",
                "reuse_without_parser_payload": True,
            },
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
        write_text=False,
        reused=True,
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

    text, blocks = _blocks_from_plain_text(text)
    metadata = {
        **(candidate.get("parser_metadata") or {}),
        "reuse_from": reuse_from,
        "reuse_inventory_classification": classification,
        "reuse_source_set_id": candidate.get("source_set_id"),
        "reuse_text_path": str(source_text_path),
        "reuse_text_sha256": actual_text_sha256,
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



def _extract_payload(
    *,
    row: dict,
    artifact_path: Path,
    prefer_docling: bool,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
    facade_module: Any,
) -> ExtractionPayload:
    parser = facade_module._effective_parser(row, artifact_path)
    if parser == "xml":
        return facade_module._extract_xml(artifact_path, row=row)
    if parser == "pdf":
        return facade_module._extract_pdf(
            artifact_path,
            ocr_enabled=docling_ocr,
            timeout_seconds=docling_timeout_seconds,
        )
    if prefer_docling and parser in {"html", "docx"}:
        docling_payload = facade_module._try_extract_docling(
            artifact_path,
            ocr_enabled=docling_ocr,
            timeout_seconds=docling_timeout_seconds,
        )
        if docling_payload is not None:
            return docling_payload
    if parser == "html":
        return facade_module._extract_html(artifact_path)
    if parser == "doc":
        return facade_module._extract_doc(artifact_path)
    if parser == "docx":
        return facade_module._extract_docx(artifact_path)
    if parser == "zip":
        return facade_module._extract_zip(artifact_path)
    if parser == "image":
        return facade_module._extract_image(
            artifact_path,
            ocr_enabled=docling_ocr,
            timeout_seconds=docling_timeout_seconds,
        )
    if parser == "text":
        return facade_module._extract_plain_text(artifact_path)
    raise ExtractionFailure("unsupported_parser", f"Unsupported parser: {parser}")
