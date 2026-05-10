from __future__ import annotations

from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import html
import importlib.util
import importlib.metadata
import json
import multiprocessing
import re
import shutil
import sqlite3
import sys
import tempfile
from urllib.parse import unquote
from urllib.parse import urlparse
import zipfile
import xml.etree.ElementTree as ET

from .records import sha256_file


DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_TEXT_FALLBACK_ERROR_CLASSES = {"docling_timeout"}
PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES = 512 * 1024 * 1024
SUCCESS_STATUSES = {"downloaded", "downloaded_existing", "duplicate_content", "duplicate_url"}
NON_EXTRACTABLE_SOURCE_STATUSES = {"skipped_excluded"}
CURRENT_REUSE_INVENTORY_CLASSIFICATIONS = {"already_current", "already_current_cg_slice"}
TERMINAL_STATUSES = {
    "extracted",
    "skipped_excluded",
    "no_artifact",
    "artifact_missing",
    "hash_mismatch",
    "parser_error",
    "parser_timeout",
    "empty_text",
}
REQUIRED_CHUNK_PROVENANCE = {
    "source_set_id",
    "source_record_id",
    "artifact_sha256",
    "artifact_path",
    "citation_label",
    "original_url",
    "effective_url",
    "final_url",
    "parser_name",
    "parser_version",
    "extracted_at",
    "char_start",
    "char_end",
    "content_sha256",
}


@dataclass(frozen=True)
class ExtractionBuildResult:
    source_set_id: str
    derived_dir: Path
    extracted_text_dir: Path
    docling_json_dir: Path
    chunks_path: Path
    extraction_manifest_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class TextBlock:
    text: str
    heading: str | None = None
    section: str | None = None
    page: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(frozen=True)
class ExtractionPayload:
    text: str
    blocks: list[TextBlock]
    parser_name: str
    parser_version: str
    docling_json: dict | None = None
    metadata: dict | None = None


class ExtractionFailure(Exception):
    def __init__(self, error_class: str, message: str) -> None:
        super().__init__(message)
        self.error_class = error_class
        self.message = message


def build_extraction(
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
    source_derived_dir = _source_derived_dir(derived_dir, source_set_id)
    if source_derived_dir.exists() and not preserve_existing_outputs:
        shutil.rmtree(source_derived_dir)
    extracted_text_dir = source_derived_dir / "extracted_text"
    docling_json_dir = source_derived_dir / "docling_json"
    chunks_dir = source_derived_dir / "chunks"
    diagnostics_dir = source_derived_dir / "diagnostics"
    payload_cache_dir = diagnostics_dir / "payload_cache"
    for directory in (extracted_text_dir, docling_json_dir, chunks_dir, diagnostics_dir):
        directory.mkdir(parents=True, exist_ok=True)
    if preserve_existing_outputs:
        payload_cache_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_dir / "chunks.jsonl"
    extraction_manifest_path = diagnostics_dir / "extraction_manifest.jsonl"
    extraction_validation_path = diagnostics_dir / "extraction_validation.json"
    summary_path = diagnostics_dir / "summary.json"

    selected_ids = set(id_filters or set())
    if id_filter:
        selected_ids.add(id_filter)

    rows = _load_catalog_rows(
        sqlite_path,
        source_set_id=source_set_id,
        id_filters=selected_ids or None,
        parser_filter=parser_filter,
        limit=limit,
    )
    extracted_at = _utc_now()
    manifest_records: list[dict] = []
    chunks: list[dict] = []

    for row in rows:
        record, row_chunks = _extract_row(
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
        manifest_records.append(record)
        chunks.extend(row_chunks)

    _write_jsonl(chunks_path, chunks)
    _write_jsonl(extraction_manifest_path, manifest_records)
    validation = _validation_report(
        source_set_id=source_set_id,
        rows=rows,
        manifest_records=manifest_records,
        chunks=chunks,
    )
    summary = _summary(
        source_set_id=source_set_id,
        source_set_manifest=source_set_manifest,
        rows=rows,
        manifest_records=manifest_records,
        chunks=chunks,
        validation=validation,
        chunks_path=chunks_path,
        extraction_manifest_path=extraction_manifest_path,
        validation_path=extraction_validation_path,
        summary_path=summary_path,
        filters={
            "id": id_filter,
            "ids": sorted(selected_ids) if selected_ids else None,
            "parser": parser_filter,
            "limit": limit,
        },
        extraction_options={
            "catalog_dir": str(catalog_dir),
            "chunk_max_chars": chunk_max_chars,
            "chunk_overlap_chars": chunk_overlap_chars,
            "prefer_docling": prefer_docling,
            "docling_ocr": docling_ocr,
            "docling_timeout_seconds": docling_timeout_seconds,
            "reuse_existing": reuse_existing,
            "reuse_inventory_path": str(reuse_inventory_path) if reuse_inventory_path else None,
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
    return rows


def _extract_row(
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
        payload = _extract_payload(
            row=row,
            artifact_path=artifact_path,
            prefer_docling=prefer_docling,
            docling_ocr=docling_ocr,
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


def _base_manifest_record(*, row: dict, extracted_at: str) -> dict:
    return {
        "source_set_id": row["source_set_id"],
        "source_record_id": row["source_record_id"],
        "title": row["title"],
        "document_role": row["document_role"],
        "authority_level": row["authority_level"],
        "host": row["host"],
        "expected_parser": row["expected_parser"],
        "source_status": row["source_status"],
        "download_run_id": row.get("download_run_id"),
        "artifact_sha256": row.get("artifact_sha256"),
        "artifact_path": row.get("artifact_path"),
        "artifact_byte_size": row.get("artifact_byte_size"),
        "content_type": row.get("content_type"),
        "citation_label": row.get("citation_label"),
        "original_url": row.get("original_url"),
        "effective_url": row.get("effective_url"),
        "final_url": _final_url(row),
        "retrieved_at": row.get("retrieved_at"),
        "extracted_at": extracted_at,
        "status": None,
        "artifact_sha256_verified": None,
        "actual_artifact_sha256": None,
        "parser_name": None,
        "parser_version": None,
        "parser_metadata": None,
        "text_path": None,
        "docling_json_path": None,
        "text_char_count": 0,
        "text_sha256": None,
        "chunk_count": 0,
        "failure": None,
    }


def _failed_record(base_record: dict, *, status: str, error_class: str, message: str) -> dict:
    record = dict(base_record)
    record.update(
        {
            "status": status,
            "failure": {
                "error_class": error_class,
                "error_message": message,
            },
        }
    )
    return record


def _skipped_record(base_record: dict, *, status: str, reason: str) -> dict:
    record = dict(base_record)
    record.update(
        {
            "status": status,
            "artifact_sha256_verified": None,
            "parser_metadata": {"skip_reason": reason},
            "failure": None,
        }
    )
    return record


def _extract_payload(
    *,
    row: dict,
    artifact_path: Path,
    prefer_docling: bool,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
) -> ExtractionPayload:
    parser = _effective_parser(row, artifact_path)
    if parser == "xml":
        return _extract_xml(artifact_path, row=row)
    if parser == "pdf":
        return _extract_pdf(
            artifact_path,
            ocr_enabled=docling_ocr,
            timeout_seconds=docling_timeout_seconds,
        )
    if prefer_docling and parser in {"html", "docx"}:
        docling_payload = _try_extract_docling(
            artifact_path,
            ocr_enabled=docling_ocr,
            timeout_seconds=docling_timeout_seconds,
        )
        if docling_payload is not None:
            return docling_payload
    if parser == "html":
        return _extract_html(artifact_path)
    if parser == "docx":
        return _extract_docx(artifact_path)
    if parser == "text":
        return _extract_plain_text(artifact_path)
    raise ExtractionFailure("unsupported_parser", f"Unsupported parser: {parser}")


def _effective_parser(row: dict, artifact_path: Path) -> str:
    expected = (row.get("expected_parser") or "").lower()
    content_type = (row.get("content_type") or "").lower()
    suffix = artifact_path.suffix.lower()
    if expected in {"html", "xml", "pdf", "docx"}:
        return expected
    if expected == "structured_web_adapter":
        if content_type in {"application/xml", "text/xml"} or suffix == ".xml":
            return "xml"
        return "html"
    if content_type == "application/pdf" or suffix == ".pdf":
        return "pdf"
    if content_type in {"application/xml", "text/xml"} or suffix == ".xml":
        return "xml"
    if content_type in {"text/html", "application/xhtml+xml"} or suffix in {".html", ".htm"}:
        return "html"
    if content_type == DOCX_CONTENT_TYPE or suffix == ".docx":
        return "docx"
    if content_type.startswith("text/"):
        return "text"
    return expected or "text"


def _extract_pdf(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload:
    try:
        payload = _try_extract_docling(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        )
    except ExtractionFailure as error:
        if error.error_class in PDF_TEXT_FALLBACK_ERROR_CLASSES:
            fallback_payload = _try_extract_pdf_text_fallback(artifact_path)
            if fallback_payload is not None:
                return _with_payload_metadata(
                    fallback_payload,
                    {
                        "fallback_from": "docling",
                        "fallback_error_class": error.error_class,
                        "fallback_error_message": error.message,
                        "pypdf_max_decompress_bytes": PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES,
                    },
                )
        raise
    if payload is not None:
        return payload
    raise ExtractionFailure(
        "docling_unavailable",
        "Docling is required for this parser but is not installed in the active Python "
        "environment.",
    )


def _try_extract_docling(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload | None:
    if importlib.util.find_spec("docling") is None:
        return None

    if timeout_seconds is not None:
        return _try_extract_docling_isolated(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        )

    return _convert_docling_in_process(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
    )


def _try_extract_docling_isolated(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float,
) -> ExtractionPayload | None:
    with tempfile.NamedTemporaryFile(
        prefix="usfs-r1-docling-",
        suffix=".json",
        delete=False,
    ) as handle:
        result_path = Path(handle.name)
    try:
        context = multiprocessing.get_context("spawn")
        process = context.Process(
            target=_docling_child_main,
            args=(str(artifact_path), ocr_enabled, timeout_seconds, str(result_path)),
        )
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            _stop_process(process)
            raise ExtractionFailure(
                "docling_timeout",
                f"Docling conversion exceeded hard timeout of {timeout_seconds:g} seconds.",
            )
        if not result_path.exists() or result_path.stat().st_size == 0:
            raise ExtractionFailure(
                "docling_worker_failed",
                f"Docling worker exited without a result file; exitcode={process.exitcode}.",
            )
        result = _read_json(result_path)
        status = result.get("status")
        if status == "unavailable":
            return None
        if status == "error":
            raise ExtractionFailure(
                result.get("error_class") or "docling_conversion_failed",
                result.get("error_message") or "Docling worker failed.",
            )
        if status != "ok":
            raise ExtractionFailure(
                "docling_worker_failed",
                f"Docling worker returned unknown status: {status}",
            )
        return _payload_from_wire(result["payload"])
    finally:
        result_path.unlink(missing_ok=True)


def _stop_process(process: multiprocessing.Process) -> None:
    process.terminate()
    process.join(5)
    if process.is_alive():
        process.kill()
        process.join(5)


def _docling_child_main(
    artifact_path: str,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    result_path: str,
) -> None:
    try:
        payload = _convert_docling_in_process(
            Path(artifact_path),
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        )
        if payload is None:
            result = {"status": "unavailable"}
        else:
            result = {"status": "ok", "payload": _payload_to_wire(payload)}
    except ExtractionFailure as error:
        result = {
            "status": "error",
            "error_class": error.error_class,
            "error_message": error.message,
        }
    except Exception as error:
        result = {
            "status": "error",
            "error_class": type(error).__name__,
            "error_message": str(error),
        }
    Path(result_path).write_text(json.dumps(result, sort_keys=True), encoding="utf-8")


def _try_extract_pdf_text_fallback(artifact_path: Path) -> ExtractionPayload | None:
    if importlib.util.find_spec("pypdf") is None:
        return None
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        version = importlib.metadata.version("pypdf")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    try:
        _raise_pypdf_decompression_limit()
        reader = PdfReader(str(artifact_path))
        blocks = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = _clean_text(page.extract_text() or "")
            if text:
                blocks.append(TextBlock(text=text, page=page_number))
    except Exception as error:
        raise ExtractionFailure("pdf_text_fallback_failed", str(error)) from error
    if not blocks:
        raise ExtractionFailure(
            "pdf_text_fallback_empty",
            "PDF text fallback produced no text.",
        )
    text, blocks = _assemble_blocks(blocks)
    return ExtractionPayload(
        text=text,
        blocks=blocks,
        parser_name="pypdf_text_fallback",
        parser_version=version,
        metadata={"pypdf_max_decompress_bytes": PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES},
    )


def _with_payload_metadata(payload: ExtractionPayload, metadata: dict) -> ExtractionPayload:
    return ExtractionPayload(
        text=payload.text,
        blocks=payload.blocks,
        parser_name=payload.parser_name,
        parser_version=payload.parser_version,
        docling_json=payload.docling_json,
        metadata={**(payload.metadata or {}), **metadata},
    )


def _raise_pypdf_decompression_limit() -> None:
    try:
        from pypdf import filters
    except ImportError:
        return
    current = getattr(filters, "ZLIB_MAX_OUTPUT_LENGTH", 0)
    if current < PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES:
        filters.ZLIB_MAX_OUTPUT_LENGTH = PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES


def _convert_docling_in_process(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload | None:
    try:
        __import__("docling.document_converter")
    except ImportError:
        return None

    try:
        version = importlib.metadata.version("docling")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    try:
        result = _docling_converter(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        ).convert(artifact_path)
        document = getattr(result, "document", None)
        if document is None:
            raise ExtractionFailure("docling_conversion_failed", "Docling returned no document.")
        text = _docling_text(document)
        docling_json = _docling_json(document)
    except ExtractionFailure:
        raise
    except Exception as error:
        raise ExtractionFailure("docling_conversion_failed", str(error)) from error

    text, blocks = _blocks_from_plain_text(text)
    return ExtractionPayload(
        text=text,
        blocks=blocks,
        parser_name="docling",
        parser_version=version,
        docling_json=docling_json,
    )


def _payload_to_wire(payload: ExtractionPayload) -> dict:
    return {
        "text": payload.text,
        "blocks": [
            {
                "text": block.text,
                "heading": block.heading,
                "section": block.section,
                "page": block.page,
                "char_start": block.char_start,
                "char_end": block.char_end,
            }
            for block in payload.blocks
        ],
        "parser_name": payload.parser_name,
        "parser_version": payload.parser_version,
        "docling_json": payload.docling_json,
        "metadata": payload.metadata,
    }


def _payload_from_wire(payload: dict) -> ExtractionPayload:
    return ExtractionPayload(
        text=payload["text"],
        blocks=[
            TextBlock(
                text=block["text"],
                heading=block.get("heading"),
                section=block.get("section"),
                page=block.get("page"),
                char_start=block.get("char_start"),
                char_end=block.get("char_end"),
            )
            for block in payload.get("blocks", [])
        ],
        parser_name=payload["parser_name"],
        parser_version=payload["parser_version"],
        docling_json=payload.get("docling_json"),
        metadata=payload.get("metadata"),
    )


def _docling_converter(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
):  # noqa: ANN202
    from docling.document_converter import DocumentConverter

    if artifact_path.suffix.lower() != ".pdf":
        return DocumentConverter()

    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import PdfFormatOption

    pipeline_options = PdfPipelineOptions(
        document_timeout=timeout_seconds,
        do_ocr=ocr_enabled,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )


def _docling_text(document) -> str:  # noqa: ANN001
    for method_name in ("export_to_markdown", "export_to_text"):
        method = getattr(document, method_name, None)
        if callable(method):
            text = method()
            if text:
                return str(text)
    return str(document)


def _docling_json(document) -> dict | None:  # noqa: ANN001
    for method_name in ("export_to_dict", "model_dump", "dict"):
        method = getattr(document, method_name, None)
        if callable(method):
            try:
                value = method()
            except TypeError:
                continue
            if isinstance(value, dict):
                return value
    return None


def _extract_html(artifact_path: Path) -> ExtractionPayload:
    text = _decode_bytes(artifact_path.read_bytes())
    return _extract_html_text(
        text,
        parser_name="python_htmlparser",
        parser_version=sys.version.split()[0],
    )


def _extract_html_text(text: str, *, parser_name: str, parser_version: str) -> ExtractionPayload:
    parser = _HTMLTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as error:
        raise ExtractionFailure("html_parse_failed", str(error)) from error
    blocks = parser.blocks()
    if not blocks:
        blocks = _blocks_from_text_fragments([_strip_html_text(text)])
    assembled, blocks = _assemble_blocks(blocks)
    return ExtractionPayload(
        text=assembled,
        blocks=blocks,
        parser_name=parser_name,
        parser_version=parser_version,
    )


class _HTMLTextParser(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "caption",
        "dd",
        "div",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "p",
        "pre",
        "section",
        "td",
        "th",
        "title",
        "tr",
    }
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "title"}
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._blocks: list[TextBlock] = []
        self._parts: list[str] = []
        self._skip_depth = 0
        self._heading_parts: list[str] | None = None
        self._current_heading: str | None = None

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001, ARG002
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag in self.BLOCK_TAGS:
            self._flush()
        if tag in self.HEADING_TAGS:
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in self.HEADING_TAGS:
            heading = _clean_text(" ".join(self._heading_parts or []))
            if heading:
                self._current_heading = heading
            self._flush(heading=heading or self._current_heading)
            self._heading_parts = None
            return
        if tag in self.BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        cleaned = _clean_text(data)
        if not cleaned:
            return
        self._parts.append(cleaned)
        if self._heading_parts is not None:
            self._heading_parts.append(cleaned)

    def blocks(self) -> list[TextBlock]:
        self._flush()
        return self._blocks

    def _flush(self, *, heading: str | None = None) -> None:
        cleaned = _clean_text(" ".join(self._parts))
        self._parts = []
        if not cleaned:
            return
        self._blocks.append(TextBlock(text=cleaned, heading=heading or self._current_heading))


def _strip_html_text(text: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|tr|td|th|h[1-6]|section|article)>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return _clean_text(text)


def _looks_like_html_markup(text: str) -> bool:
    sample = text[:4096].lower()
    return "<html" in sample or "<!doctype html" in sample


def _extract_xml(artifact_path: Path, *, row: dict | None = None) -> ExtractionPayload:
    body = artifact_path.read_bytes()
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        text = _decode_bytes(body)
        if _looks_like_html_markup(text):
            return _extract_html_text(
                text,
                parser_name="legal_xml_xhtml_fallback",
                parser_version=sys.version.split()[0],
            )
        raise ExtractionFailure("xml_parse_failed", str(error)) from error
    source_scope = _xml_scope_for_row(row)
    scoped_root = root
    if source_scope is not None:
        scoped_root = _find_xml_scope_element(root, source_scope)
        if scoped_root is None:
            raise ExtractionFailure(
                "xml_scope_not_found",
                (
                    "Could not find XML element for source scope "
                    f"{source_scope['type']} {source_scope['identifier']}."
                ),
            )
    blocks: list[TextBlock] = []
    _walk_xml(scoped_root, path=(), sibling_index=1, heading=None, blocks=blocks)
    if not blocks:
        blocks = _blocks_from_text_fragments([_clean_text(" ".join(scoped_root.itertext()))])
    assembled, blocks = _assemble_blocks(blocks)
    metadata = {"source_scope": source_scope} if source_scope is not None else None
    return ExtractionPayload(
        text=assembled,
        blocks=blocks,
        parser_name="legal_xml_builtin",
        parser_version=sys.version.split()[0],
        metadata=metadata,
    )


XML_BLOCK_TAGS = {
    "AUTH",
    "CITA",
    "FP",
    "HED",
    "HD",
    "HEAD",
    "NOTE",
    "P",
    "SECTNO",
    "SOURCE",
    "SUBJECT",
}
XML_HEADING_TAGS = {"HED", "HD", "HEAD", "SECTNO", "SUBJECT"}


def _walk_xml(
    element: ET.Element,
    *,
    path: tuple[str, ...],
    sibling_index: int,
    heading: str | None,
    blocks: list[TextBlock],
) -> None:
    tag = _xml_local_name(element.tag)
    element_path = (*path, f"{tag}[{sibling_index}]")
    children = list(element)
    text = _clean_text(" ".join(element.itertext()))
    next_heading = heading
    if text and tag in XML_HEADING_TAGS:
        next_heading = text[:240]
    has_block_child = any(_xml_local_name(child.tag) in XML_BLOCK_TAGS for child in children)
    if text and tag in XML_BLOCK_TAGS and not has_block_child:
        blocks.append(
            TextBlock(
                text=text,
                heading=next_heading,
                section="/" + "/".join(element_path),
            )
        )
    tag_counts: Counter[str] = Counter()
    for child in children:
        child_tag = _xml_local_name(child.tag)
        tag_counts[child_tag] += 1
        _walk_xml(
            child,
            path=element_path,
            sibling_index=tag_counts[child_tag],
            heading=next_heading,
            blocks=blocks,
        )


def _xml_local_name(tag: str) -> str:
    if "}" in tag:
        tag = tag.rsplit("}", 1)[1]
    return tag.upper()


def _xml_scope_for_row(row: dict | None) -> dict | None:
    if not row:
        return None
    host = (row.get("host") or "").lower()
    urls = [
        row.get("artifact_final_url"),
        row.get("citation_final_url"),
        row.get("effective_url"),
        row.get("normalized_url"),
        row.get("original_url"),
    ]
    for value in urls:
        if not value:
            continue
        parsed = urlparse(str(value))
        if parsed.netloc and "ecfr.gov" not in parsed.netloc.lower() and "ecfr.gov" not in host:
            continue
        path = unquote(parsed.path or str(value))
        for segment in path.split("/"):
            lowered = segment.lower()
            if lowered.startswith("section-"):
                identifier = segment.split("-", 1)[1]
                if identifier:
                    return {"type": "SECTION", "identifier": identifier, "url": str(value)}
            if lowered.startswith("subpart-"):
                identifier = segment.split("-", 1)[1]
                if identifier:
                    return {"type": "SUBPART", "identifier": identifier.upper(), "url": str(value)}
    return None


def _find_xml_scope_element(root: ET.Element, scope: dict) -> ET.Element | None:
    expected_type = _normalize_xml_scope_identifier(scope["type"])
    expected_identifier = _normalize_xml_scope_identifier(scope["identifier"])
    for element in root.iter():
        element_type = _normalize_xml_scope_identifier(element.attrib.get("TYPE", ""))
        element_identifier = _normalize_xml_scope_identifier(element.attrib.get("N", ""))
        if element_type == expected_type and element_identifier == expected_identifier:
            return element
        metadata = _xml_hierarchy_metadata(element)
        if metadata and _metadata_matches_scope(metadata, scope):
            return element
    return None


def _xml_hierarchy_metadata(element: ET.Element) -> dict | None:
    value = element.attrib.get("hierarchy_metadata")
    if not value:
        return None
    try:
        decoded = html.unescape(value)
        metadata = json.loads(decoded)
    except (TypeError, json.JSONDecodeError):
        return None
    return metadata if isinstance(metadata, dict) else None


def _metadata_matches_scope(metadata: dict, scope: dict) -> bool:
    expected_type = str(scope["type"]).lower()
    expected_identifier = str(scope["identifier"]).lower()
    path = str(metadata.get("path") or "").lower()
    citation = str(metadata.get("citation") or "").lower()
    if expected_type == "section":
        return f"/section-{expected_identifier}" in path or citation.endswith(expected_identifier)
    if expected_type == "subpart":
        return f"/subpart-{expected_identifier}" in path or citation.endswith(f"subpart {expected_identifier}")
    return False


def _normalize_xml_scope_identifier(value: object) -> str:
    return str(value or "").strip().lower()


def _extract_docx(artifact_path: Path) -> ExtractionPayload:
    try:
        with zipfile.ZipFile(artifact_path) as archive:
            document_xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile, OSError) as error:
        raise ExtractionFailure("docx_parse_failed", str(error)) from error

    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError as error:
        raise ExtractionFailure("docx_parse_failed", str(error)) from error

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraph_tag = f"{namespace}p"
    text_tag = f"{namespace}t"
    fragments: list[str] = []
    for paragraph in root.iter(paragraph_tag):
        paragraph_text = "".join(text_node.text or "" for text_node in paragraph.iter(text_tag))
        cleaned = _clean_text(paragraph_text)
        if cleaned:
            fragments.append(cleaned)
    text, blocks = _blocks_from_plain_text("\n\n".join(fragments))
    return ExtractionPayload(
        text=text,
        blocks=blocks,
        parser_name="python_docx_zip_xml",
        parser_version=sys.version.split()[0],
    )


def _extract_plain_text(artifact_path: Path) -> ExtractionPayload:
    text, blocks = _blocks_from_plain_text(_decode_bytes(artifact_path.read_bytes()))
    return ExtractionPayload(
        text=text,
        blocks=blocks,
        parser_name="python_text_decode",
        parser_version=sys.version.split()[0],
    )


def _blocks_from_plain_text(text: str) -> tuple[str, list[TextBlock]]:
    blocks = _blocks_from_text_fragments(re.split(r"\n\s*\n", text))
    return _assemble_blocks(blocks)


def _blocks_from_text_fragments(fragments: list[str]) -> list[TextBlock]:
    return [TextBlock(text=cleaned) for fragment in fragments if (cleaned := _clean_text(fragment))]


def _assemble_blocks(blocks: list[TextBlock]) -> tuple[str, list[TextBlock]]:
    assembled_parts: list[str] = []
    offset = 0
    offset_blocks: list[TextBlock] = []
    for block in blocks:
        text = _clean_text(block.text)
        if not text:
            continue
        if assembled_parts:
            assembled_parts.append("\n\n")
            offset += 2
        start = offset
        assembled_parts.append(text)
        offset += len(text)
        offset_blocks.append(
            TextBlock(
                text=text,
                heading=block.heading,
                section=block.section,
                page=block.page,
                char_start=start,
                char_end=offset,
            )
        )
    return "".join(assembled_parts), offset_blocks


def _chunks_for_payload(
    *,
    row: dict,
    payload: ExtractionPayload,
    extracted_at: str,
    source_text_path: Path,
    max_chars: int,
    overlap_chars: int,
) -> list[dict]:
    chunks: list[dict] = []
    text_chunks = _chunk_text(payload.text, payload.blocks, max_chars, overlap_chars)
    for index, chunk in enumerate(text_chunks):
        content_sha256 = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
        chunk_id = _chunk_id(
            source_set_id=row["source_set_id"],
            source_record_id=row["source_record_id"],
            artifact_sha256=row["artifact_sha256"],
            chunk_index=index,
            char_start=chunk["char_start"],
            content_sha256=content_sha256,
        )
        chunks.append(
            {
                "chunk_id": chunk_id,
                "source_set_id": row["source_set_id"],
                "source_record_id": row["source_record_id"],
                "chunk_index": index,
                "title": row["title"],
                "document_role": row["document_role"],
                "authority_level": row["authority_level"],
                "host": row["host"],
                "expected_parser": row["expected_parser"],
                "artifact_sha256": row["artifact_sha256"],
                "artifact_path": row["artifact_path"],
                "citation_label": row["citation_label"],
                "original_url": row["original_url"],
                "effective_url": row["effective_url"],
                "final_url": _final_url(row),
                "parser_name": payload.parser_name,
                "parser_version": payload.parser_version,
                "extracted_at": extracted_at,
                "source_text_path": str(source_text_path),
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "page": chunk["page"],
                "section": chunk["section"],
                "heading": chunk["heading"],
                "content_sha256": content_sha256,
                "text": chunk["text"],
            }
        )
    return chunks


def _chunk_text(
    text: str,
    blocks: list[TextBlock],
    max_chars: int,
    overlap_chars: int,
) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    chunks: list[dict] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        target_end = min(start + max_chars, text_len)
        end = _choose_chunk_end(text, start, target_end, max_chars)
        raw = text[start:end]
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw.rstrip())
        chunk_start = start + leading
        chunk_end = start + trailing
        chunk_text = text[chunk_start:chunk_end]
        if chunk_text:
            block = _block_for_offset(blocks, chunk_start)
            chunks.append(
                {
                    "text": chunk_text,
                    "char_start": chunk_start,
                    "char_end": chunk_end,
                    "heading": block.heading if block else None,
                    "section": block.section if block else None,
                    "page": block.page if block else None,
                }
            )
        if end >= text_len:
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def _choose_chunk_end(text: str, start: int, target_end: int, max_chars: int) -> int:
    if target_end >= len(text):
        return len(text)
    min_end = start + max(256, max_chars // 2)
    candidate = text.rfind("\n\n", start, target_end)
    if candidate >= min_end:
        return candidate
    candidate = text.rfind(". ", start, target_end)
    if candidate >= min_end:
        return candidate + 1
    candidate = text.rfind(" ", start, target_end)
    if candidate >= min_end:
        return candidate
    return target_end


def _block_for_offset(blocks: list[TextBlock], offset: int) -> TextBlock | None:
    for block in blocks:
        if block.char_start is None or block.char_end is None:
            continue
        if block.char_start <= offset < block.char_end:
            return block
    return blocks[-1] if blocks else None


def _chunk_id(
    *,
    source_set_id: str,
    source_record_id: str,
    artifact_sha256: str,
    chunk_index: int,
    char_start: int,
    content_sha256: str,
) -> str:
    material = "|".join(
        [
            source_set_id,
            source_record_id,
            artifact_sha256,
            str(chunk_index),
            str(char_start),
            content_sha256,
        ]
    )
    return f"chunk:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _validation_report(
    *,
    source_set_id: str,
    rows: list[dict],
    manifest_records: list[dict],
    chunks: list[dict],
) -> dict:
    checks = [
        _check_all_sources_terminal(rows, manifest_records),
        _check_all_required_rows_extracted(manifest_records),
        _check_successes_have_text(manifest_records),
        _check_successes_have_chunks(manifest_records),
        _check_no_hash_mismatches(manifest_records),
        _check_no_parser_errors(manifest_records),
        _check_no_parser_timeouts(manifest_records),
        _check_fallback_records_are_auditable(manifest_records),
        _check_scoped_xml_records_are_auditable(manifest_records),
        _check_chunk_ids_unique(chunks),
        _check_chunks_have_provenance(chunks),
    ]
    return {
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_all_sources_terminal(rows: list[dict], records: list[dict]) -> dict:
    row_ids = {row["source_record_id"] for row in rows}
    record_ids = {record["source_record_id"] for record in records}
    nonterminal = [
        record["source_record_id"]
        for record in records
        if record.get("status") not in TERMINAL_STATUSES
    ]
    missing = sorted(row_ids - record_ids)
    extra = sorted(record_ids - row_ids)
    return {
        "name": "all_catalog_rows_have_terminal_extraction_status",
        "passed": not missing and not extra and not nonterminal,
        "details": {
            "catalog_row_count": len(rows),
            "manifest_record_count": len(records),
            "missing_source_record_ids": missing,
            "unexpected_source_record_ids": extra,
            "nonterminal_source_record_ids": sorted(nonterminal),
        },
    }


def _check_successes_have_text(records: list[dict]) -> dict:
    bad = [
        record["source_record_id"]
        for record in records
        if record["status"] == "extracted" and record.get("text_char_count", 0) <= 0
    ]
    return {
        "name": "extracted_records_have_nonempty_text",
        "passed": not bad,
        "details": {"source_record_ids": sorted(bad)},
    }


def _check_all_required_rows_extracted(records: list[dict]) -> dict:
    failed = [
        record
        for record in records
        if record["status"] != "extracted"
        and record.get("source_status") not in NON_EXTRACTABLE_SOURCE_STATUSES
    ]
    skipped = [
        record["source_record_id"]
        for record in records
        if record.get("source_status") in NON_EXTRACTABLE_SOURCE_STATUSES
    ]
    return {
        "name": "all_required_rows_extracted",
        "passed": not failed,
        "details": {
            "status_counts": dict(Counter(record["status"] for record in records)),
            "skipped_non_extractable_source_record_ids": sorted(skipped),
            "failed_source_record_ids": sorted(record["source_record_id"] for record in failed),
        },
    }


def _check_successes_have_chunks(records: list[dict]) -> dict:
    bad = [
        record["source_record_id"]
        for record in records
        if record["status"] == "extracted" and record.get("chunk_count", 0) <= 0
    ]
    return {
        "name": "extracted_records_have_chunks",
        "passed": not bad,
        "details": {"source_record_ids": sorted(bad)},
    }


def _check_no_hash_mismatches(records: list[dict]) -> dict:
    mismatches = [
        record["source_record_id"]
        for record in records
        if record["status"] == "hash_mismatch"
    ]
    return {
        "name": "no_artifact_hash_mismatches",
        "passed": not mismatches,
        "details": {"source_record_ids": sorted(mismatches)},
    }


def _check_no_parser_errors(records: list[dict]) -> dict:
    errors = [record for record in records if record["status"] == "parser_error"]
    return {
        "name": "no_parser_errors",
        "passed": not errors,
        "details": {
            "source_record_ids": sorted(record["source_record_id"] for record in errors),
            "error_classes": dict(
                Counter((record.get("failure") or {}).get("error_class") for record in errors)
            ),
        },
    }


def _check_no_parser_timeouts(records: list[dict]) -> dict:
    timeouts = [record for record in records if record["status"] == "parser_timeout"]
    return {
        "name": "no_parser_timeouts",
        "passed": not timeouts,
        "details": {
            "source_record_ids": sorted(record["source_record_id"] for record in timeouts),
        },
    }


def _check_fallback_records_are_auditable(records: list[dict]) -> dict:
    failures = []
    for record in records:
        if record.get("parser_name") != "pypdf_text_fallback":
            continue
        metadata = record.get("parser_metadata") or {}
        missing = [
            key
            for key in (
                "fallback_from",
                "fallback_error_class",
                "fallback_error_message",
                "pypdf_max_decompress_bytes",
            )
            if not metadata.get(key)
        ]
        if missing:
            failures.append(
                {
                    "source_record_id": record.get("source_record_id"),
                    "missing_metadata": missing,
                }
            )
    return {
        "name": "fallback_records_are_auditable",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_scoped_xml_records_are_auditable(records: list[dict]) -> dict:
    failures = []
    for record in records:
        if record.get("status") != "extracted" or record.get("parser_name") != "legal_xml_builtin":
            continue
        scope = _xml_scope_for_row(record)
        if scope is None:
            continue
        metadata = record.get("parser_metadata") or {}
        actual_scope = metadata.get("source_scope") if isinstance(metadata, dict) else None
        if not actual_scope:
            failures.append(
                {
                    "source_record_id": record.get("source_record_id"),
                    "expected_scope": scope,
                    "reason": "missing_source_scope_metadata",
                }
            )
            continue
        if (
            _normalize_xml_scope_identifier(actual_scope.get("type"))
            != _normalize_xml_scope_identifier(scope["type"])
            or _normalize_xml_scope_identifier(actual_scope.get("identifier"))
            != _normalize_xml_scope_identifier(scope["identifier"])
        ):
            failures.append(
                {
                    "source_record_id": record.get("source_record_id"),
                    "expected_scope": scope,
                    "actual_scope": actual_scope,
                    "reason": "source_scope_mismatch",
                }
            )
    return {
        "name": "scoped_xml_records_are_auditable",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_ids_unique(chunks: list[dict]) -> dict:
    counts = Counter(chunk["chunk_id"] for chunk in chunks)
    duplicates = sorted(chunk_id for chunk_id, count in counts.items() if count > 1)
    return {
        "name": "chunk_ids_are_unique",
        "passed": not duplicates,
        "details": {"duplicate_chunk_ids": duplicates},
    }


def _check_chunks_have_provenance(chunks: list[dict]) -> dict:
    bad: list[dict] = []
    for chunk in chunks:
        missing = sorted(
            key
            for key in REQUIRED_CHUNK_PROVENANCE
            if chunk.get(key) is None or chunk.get(key) == ""
        )
        if missing:
            bad.append({"chunk_id": chunk.get("chunk_id"), "missing": missing})
    return {
        "name": "chunks_have_required_provenance",
        "passed": not bad,
        "details": {"chunks_missing_provenance": bad[:50], "bad_chunk_count": len(bad)},
    }


def _summary(
    *,
    source_set_id: str,
    source_set_manifest: dict,
    rows: list[dict],
    manifest_records: list[dict],
    chunks: list[dict],
    validation: dict,
    chunks_path: Path,
    extraction_manifest_path: Path,
    validation_path: Path,
    summary_path: Path,
    filters: dict,
    extraction_options: dict,
) -> dict:
    status_counts = Counter(record["status"] for record in manifest_records)
    parser_counts = Counter(
        record["parser_name"] for record in manifest_records if record.get("parser_name")
    )
    fallback_counts = Counter(
        (record.get("parser_metadata") or {}).get("fallback_from")
        for record in manifest_records
        if (record.get("parser_metadata") or {}).get("fallback_from")
    )
    reused_count = sum(
        1
        for record in manifest_records
        if (record.get("parser_metadata") or {}).get("reused_existing")
    )
    source_status_counts = Counter(row["source_status"] for row in rows)
    catalog_source_status_counts = Counter(source_set_manifest.get("status_counts") or {})
    catalog_source_count = int(source_set_manifest.get("source_count") or 0)
    catalog_non_extractable_count = sum(
        catalog_source_status_counts.get(status, 0) for status in NON_EXTRACTABLE_SOURCE_STATUSES
    )
    selected_non_extractable_count = sum(
        count for status, count in source_status_counts.items() if status in NON_EXTRACTABLE_SOURCE_STATUSES
    )
    required_extraction_source_count = max(catalog_source_count - catalog_non_extractable_count, 0)
    selected_required_extraction_source_count = len(rows) - selected_non_extractable_count
    expected_parser_counts = Counter(row["expected_parser"] for row in rows)
    failure_counts = Counter(
        (record.get("failure") or {}).get("error_class")
        for record in manifest_records
        if record.get("failure")
    )
    return {
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "catalog_source_count": catalog_source_count,
        "artifact_bearing_source_count": required_extraction_source_count,
        "required_extraction_source_count": required_extraction_source_count,
        "selected_source_count": len(rows),
        "selected_required_extraction_source_count": selected_required_extraction_source_count,
        "catalog_skipped_excluded_count": catalog_non_extractable_count,
        "skipped_excluded_count": status_counts.get("skipped_excluded", 0),
        "filters": filters,
        "extraction_options": extraction_options,
        "extracted_count": status_counts.get("extracted", 0),
        "failed_count": sum(
            count
            for status, count in status_counts.items()
            if status != "extracted" and status not in NON_EXTRACTABLE_SOURCE_STATUSES
        ),
        "chunk_count": len(chunks),
        "status_counts": dict(status_counts),
        "source_status_counts": dict(source_status_counts),
        "expected_parser_counts": dict(expected_parser_counts),
        "parser_counts": dict(parser_counts),
        "fallback_counts": dict(fallback_counts),
        "reused_count": reused_count,
        "failure_counts": {key: count for key, count in failure_counts.items() if key},
        "failed_source_examples": _failed_source_examples(manifest_records),
        "validation_passed": validation["passed"],
        "chunks_path": str(chunks_path),
        "extraction_manifest_path": str(extraction_manifest_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
    }


def _failed_source_examples(records: list[dict], *, limit: int = 10) -> list[dict]:
    examples = []
    for record in records:
        failure = record.get("failure")
        if not failure:
            continue
        examples.append(
            {
                "source_record_id": record["source_record_id"],
                "expected_parser": record["expected_parser"],
                "status": record["status"],
                "error_class": failure.get("error_class"),
                "error_message": failure.get("error_message"),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def _source_derived_dir(derived_dir: Path, source_set_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", source_set_id):
        raise ValueError(f"Unsafe source_set_id for derived output path: {source_set_id!r}")
    derived_root = derived_dir.resolve()
    path = (derived_root / source_set_id).resolve()
    try:
        path.relative_to(derived_root)
    except ValueError as error:
        message = f"Unsafe derived output path for source_set_id: {source_set_id}"
        raise ValueError(message) from error
    return path


def _resolve_artifact_path(output_dir: Path, artifact_path: str) -> Path:
    path = Path(artifact_path)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return output_dir / path


def _resolve_existing_path(output_dir: Path, value: object | None) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = (
        [path]
        if path.is_absolute()
        else [path, output_dir / path, output_dir.parent / path]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _text_path(extracted_text_dir: Path, *, source_record_id: str, artifact_sha256: str) -> Path:
    return extracted_text_dir / f"{source_record_id}_{artifact_sha256[:16]}.txt"


def _payload_cache_path(payload_cache_dir: Path, row: dict) -> Path:
    source_record_id = str(row["source_record_id"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", source_record_id):
        raise ValueError(f"Unsafe source_record_id for payload cache path: {source_record_id!r}")
    artifact_sha256 = str(row["artifact_sha256"])
    return payload_cache_dir / f"{source_record_id}_{artifact_sha256[:16]}.json"


def _parser_metadata_with_reuse(metadata: dict | None, *, reused: bool) -> dict | None:
    if not reused:
        return metadata
    return {
        **(metadata or {}),
        "reused_existing": True,
    }


def _final_url(row: dict) -> str | None:
    return (
        row.get("artifact_final_url")
        or row.get("citation_final_url")
        or row.get("effective_url")
    )


def _decode_bytes(body: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_reuse_inventory_records(
    reuse_inventory_path: Path | None,
    *,
    source_set_id: str,
) -> dict[str, dict] | None:
    if reuse_inventory_path is None:
        return None
    raw_records = _load_reuse_inventory_payload_records(Path(reuse_inventory_path))
    records: dict[str, dict] = {}
    for record in raw_records:
        if record.get("source_set_id") != source_set_id:
            raise ValueError(
                "Reuse inventory source_set_id does not match catalog source_set_id: "
                f"{record.get('source_set_id')} != {source_set_id}"
            )
        source_record_id = str(record.get("source_record_id") or "")
        if source_record_id:
            records[source_record_id] = record
    return records


def _load_reuse_inventory_payload_records(path: Path) -> list[dict]:
    if path.is_dir():
        return _read_jsonl(path / "reuse_inventory_records.jsonl")
    if path.name == "reuse_inventory.json":
        payload = _read_json(path)
        records = payload.get("records")
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
        sibling_records = path.parent / "reuse_inventory_records.jsonl"
        return _read_jsonl(sibling_records)
    if path.name == "summary.json":
        return _read_jsonl(path.parent / "reuse_inventory_records.jsonl")
    return _read_jsonl(path)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
