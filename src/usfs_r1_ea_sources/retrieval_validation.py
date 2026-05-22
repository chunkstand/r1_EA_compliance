from __future__ import annotations

from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from .retrieval_common import REQUIRED_CHUNK_FIELDS, _int_from_summary, _resolve_existing_path


def _validation_report(
    *,
    output_dir: Path,
    source_set_id: str,
    chunks_path: Path,
    catalog_sqlite_path: Path,
    catalog_source_set_id: str | None,
    catalog_source_record_ids: set[str] | None,
    extraction_validation_path: Path,
    extraction_validation: dict | None,
    extraction_manifest_path: Path,
    extraction_manifest_records: list[dict],
    extraction_summary_path: Path,
    extraction_summary: dict | None,
    extraction_accuracy_path: Path,
    extraction_accuracy: dict | None,
    verified_extraction_requirements: dict,
    chunks: list[dict],
    allow_failed_extraction: bool,
    allow_partial_extraction: bool,
) -> dict:
    checks = [
        {
            "name": "extraction_validation_passed",
            "passed": allow_failed_extraction
            or bool(extraction_validation and extraction_validation.get("passed")),
            "details": {
                "path": str(extraction_validation_path),
                "exists": extraction_validation_path.exists(),
                "allow_failed_extraction": allow_failed_extraction,
                "passed": bool(extraction_validation and extraction_validation.get("passed")),
            },
        },
        {
            "name": "extraction_manifest_exists",
            "passed": extraction_manifest_path.exists(),
            "details": {"path": str(extraction_manifest_path)},
        },
        {
            "name": "extraction_summary_exists",
            "passed": extraction_summary_path.exists(),
            "details": {"path": str(extraction_summary_path)},
        },
        _check_verified_extraction_audit_exists(
            extraction_accuracy_path,
            verified_extraction_requirements=verified_extraction_requirements,
        ),
        _check_verified_extraction_audit_allows_knowledge_base_admission(
            source_set_id=source_set_id,
            extraction_accuracy_path=extraction_accuracy_path,
            extraction_accuracy=extraction_accuracy,
            verified_extraction_requirements=verified_extraction_requirements,
        ),
        _check_extraction_scope_is_complete(
            extraction_summary,
            allow_partial_extraction=allow_partial_extraction,
        ),
        {
            "name": "chunks_jsonl_exists",
            "passed": chunks_path.exists(),
            "details": {"path": str(chunks_path)},
        },
        {
            "name": "catalog_sqlite_exists",
            "passed": catalog_sqlite_path.exists(),
            "details": {"path": str(catalog_sqlite_path)},
        },
        _check_catalog_source_set_matches_requested_source_set(
            requested_source_set_id=source_set_id,
            catalog_sqlite_path=catalog_sqlite_path,
            catalog_source_set_id=catalog_source_set_id,
            catalog_source_record_ids=catalog_source_record_ids,
            extraction_manifest_records=extraction_manifest_records,
        ),
        _check_chunks_loaded(chunks),
        _check_source_set_ids_match(source_set_id, chunks),
        _check_chunk_ids_unique(chunks),
        _check_required_chunk_fields(chunks),
        _check_chunk_review_topics(chunks),
        _check_extracted_sources_match_chunks(extraction_manifest_records, chunks),
        _check_chunk_paths_exist(output_dir, chunks),
        _check_chunk_hashes(chunks),
        _check_chunk_offsets(chunks),
    ]
    return {
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_chunks_loaded(chunks: list[dict]) -> dict:
    return {
        "name": "chunks_loaded",
        "passed": bool(chunks),
        "details": {"chunk_count": len(chunks)},
    }


def _check_catalog_source_set_matches_requested_source_set(
    *,
    requested_source_set_id: str,
    catalog_sqlite_path: Path,
    catalog_source_set_id: str | None,
    catalog_source_record_ids: set[str] | None,
    extraction_manifest_records: list[dict],
) -> dict:
    manifest_path = catalog_sqlite_path.parent / "source_set_manifest.json"
    selected_source_record_ids = {
        str(record.get("source_record_id"))
        for record in extraction_manifest_records
        if record.get("source_record_id")
    }
    missing_source_record_ids = sorted(
        selected_source_record_ids - (catalog_source_record_ids or set())
    )
    unexpected_source_record_ids = sorted(
        (catalog_source_record_ids or set()) - selected_source_record_ids
    )
    source_record_sets_match = (
        bool(selected_source_record_ids)
        and catalog_source_record_ids is not None
        and not missing_source_record_ids
        and not unexpected_source_record_ids
    )
    exact_source_set_match = (
        not catalog_source_set_id or catalog_source_set_id == requested_source_set_id
    )
    if exact_source_set_match:
        match_mode = "exact_source_set_id"
    elif source_record_sets_match:
        match_mode = "selected_source_record_set"
    else:
        match_mode = "mismatch"
    return {
        "name": "catalog_source_set_matches_requested_source_set",
        "passed": exact_source_set_match or source_record_sets_match,
        "details": {
            "path": str(catalog_sqlite_path),
            "source_set_manifest_path": str(manifest_path),
            "source_set_manifest_exists": manifest_path.exists(),
            "requested_source_set_id": requested_source_set_id,
            "catalog_source_set_id": catalog_source_set_id,
            "match_mode": match_mode,
            "selected_source_record_count": len(selected_source_record_ids),
            "catalog_source_record_count": (
                len(catalog_source_record_ids) if catalog_source_record_ids is not None else None
            ),
            "missing_source_record_ids": missing_source_record_ids[:50],
            "unexpected_source_record_ids": unexpected_source_record_ids[:50],
        },
    }


def _check_source_set_ids_match(source_set_id: str, chunks: list[dict]) -> dict:
    mismatches = [
        chunk.get("chunk_id")
        for chunk in chunks
        if chunk.get("source_set_id") != source_set_id
    ]
    return {
        "name": "chunk_source_set_ids_match",
        "passed": not mismatches,
        "details": {"chunk_ids": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_extraction_scope_is_complete(
    extraction_summary: dict | None,
    *,
    allow_partial_extraction: bool,
) -> dict:
    complete = _extraction_summary_is_complete(extraction_summary)
    return {
        "name": "extraction_scope_is_complete",
        "passed": complete or allow_partial_extraction,
        "details": {
            "allow_partial_extraction": allow_partial_extraction,
            "catalog_source_count": _int_from_summary(extraction_summary, "catalog_source_count"),
            "selected_source_count": _int_from_summary(extraction_summary, "selected_source_count"),
            "required_extraction_source_count": _int_from_summary(
                extraction_summary,
                "required_extraction_source_count",
            ),
            "selected_required_extraction_source_count": _int_from_summary(
                extraction_summary,
                "selected_required_extraction_source_count",
            ),
            "extracted_count": _int_from_summary(extraction_summary, "extracted_count"),
            "failed_count": _int_from_summary(extraction_summary, "failed_count"),
            "skipped_excluded_count": _int_from_summary(
                extraction_summary,
                "skipped_excluded_count",
            ),
            "filters": (extraction_summary or {}).get("filters", {}),
            "complete": complete,
        },
    }


def _check_verified_extraction_audit_exists(
    extraction_accuracy_path: Path,
    *,
    verified_extraction_requirements: dict,
) -> dict:
    required_source_record_ids = list(verified_extraction_requirements["required_source_record_ids"])
    return {
        "name": "verified_extraction_accuracy_audit_exists",
        "passed": not required_source_record_ids or extraction_accuracy_path.exists(),
        "details": {
            "path": str(extraction_accuracy_path),
            "exists": extraction_accuracy_path.exists(),
            "required_source_record_ids": required_source_record_ids,
            "contract_ids": [
                contract.get("contract_id")
                for contract in verified_extraction_requirements["contracts"]
            ],
        },
    }


def _check_verified_extraction_audit_allows_knowledge_base_admission(
    *,
    source_set_id: str,
    extraction_accuracy_path: Path,
    extraction_accuracy: dict | None,
    verified_extraction_requirements: dict,
) -> dict:
    required_source_record_ids = set(verified_extraction_requirements["required_source_record_ids"])
    if not required_source_record_ids:
        return {
            "name": "required_sources_are_admitted_by_verified_extraction_audit",
            "passed": True,
            "details": {
                "path": str(extraction_accuracy_path),
                "required_source_record_ids": [],
                "admitted_source_record_ids": [],
                "blocked_source_record_ids": [],
            },
        }
    admitted_source_record_ids = set(
        str(value)
        for value in (extraction_accuracy or {}).get("knowledge_base_admitted_source_record_ids", [])
        if str(value)
    )
    blocked_source_record_ids = sorted(required_source_record_ids - admitted_source_record_ids)
    source_set_matches = bool(extraction_accuracy) and str(extraction_accuracy.get("source_set_id") or "") == source_set_id
    audit_passed = bool(extraction_accuracy and extraction_accuracy.get("passed"))
    return {
        "name": "required_sources_are_admitted_by_verified_extraction_audit",
        "passed": source_set_matches and audit_passed and not blocked_source_record_ids,
        "details": {
            "path": str(extraction_accuracy_path),
            "exists": extraction_accuracy_path.exists(),
            "audit_source_set_id": (extraction_accuracy or {}).get("source_set_id"),
            "source_set_matches": source_set_matches,
            "audit_passed": audit_passed,
            "required_source_record_ids": sorted(required_source_record_ids),
            "admitted_source_record_ids": sorted(admitted_source_record_ids),
            "blocked_source_record_ids": blocked_source_record_ids,
            "contract_ids": [
                contract.get("contract_id")
                for contract in verified_extraction_requirements["contracts"]
            ],
        },
    }


def _check_chunk_ids_unique(chunks: list[dict]) -> dict:
    counts = Counter(chunk.get("chunk_id") for chunk in chunks)
    duplicates = sorted(chunk_id for chunk_id, count in counts.items() if chunk_id and count > 1)
    return {
        "name": "chunk_ids_are_unique",
        "passed": not duplicates,
        "details": {"duplicate_chunk_ids": duplicates},
    }


def _check_required_chunk_fields(chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        missing = [
            field for field in sorted(REQUIRED_CHUNK_FIELDS) if chunk.get(field) in (None, "")
        ]
        if missing:
            failures.append({"chunk_id": chunk.get("chunk_id"), "missing_fields": missing})
    return {
        "name": "chunks_have_retrieval_provenance",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_review_topics(chunks: list[dict]) -> dict:
    failures = [
        chunk.get("chunk_id")
        for chunk in chunks
        if not chunk.get("review_topics")
    ]
    return {
        "name": "chunks_have_catalog_review_topics",
        "passed": not failures,
        "details": {"chunk_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_extracted_sources_match_chunks(
    extraction_manifest_records: list[dict],
    chunks: list[dict],
) -> dict:
    extracted_source_ids = {
        str(record.get("source_record_id"))
        for record in extraction_manifest_records
        if record.get("status") == "extracted" and record.get("source_record_id")
    }
    chunk_source_ids = {
        str(chunk.get("source_record_id"))
        for chunk in chunks
        if chunk.get("source_record_id")
    }
    missing_from_chunks = sorted(extracted_source_ids - chunk_source_ids)
    unexpected_chunk_sources = sorted(chunk_source_ids - extracted_source_ids)
    return {
        "name": "indexed_sources_match_extraction_manifest",
        "passed": not missing_from_chunks and not unexpected_chunk_sources,
        "details": {
            "extracted_source_count": len(extracted_source_ids),
            "chunk_source_count": len(chunk_source_ids),
            "missing_from_chunks": missing_from_chunks[:50],
            "unexpected_chunk_sources": unexpected_chunk_sources[:50],
        },
    }


def _check_chunk_paths_exist(output_dir: Path, chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        artifact_path = _resolve_existing_path(output_dir, chunk.get("artifact_path"))
        text_path = _resolve_existing_path(output_dir, chunk.get("source_text_path"))
        missing = []
        if artifact_path is None or not artifact_path.is_file():
            missing.append("artifact_path")
        if chunk.get("source_text_path") and (text_path is None or not text_path.is_file()):
            missing.append("source_text_path")
        if missing:
            failures.append({"chunk_id": chunk.get("chunk_id"), "missing_paths": missing})
    return {
        "name": "chunk_artifact_and_text_paths_exist",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_hashes(chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if chunk.get("content_sha256") != expected:
            failures.append(chunk.get("chunk_id"))
    return {
        "name": "chunk_content_hashes_match_text",
        "passed": not failures,
        "details": {"chunk_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_offsets(chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        try:
            start = int(chunk["char_start"])
            end = int(chunk["char_end"])
        except (KeyError, TypeError, ValueError):
            failures.append(chunk.get("chunk_id"))
            continue
        if start < 0 or end <= start:
            failures.append(chunk.get("chunk_id"))
    return {
        "name": "chunk_offsets_are_valid",
        "passed": not failures,
        "details": {"chunk_ids": failures[:50], "failure_count": len(failures)},
    }


def _sqlite_index_checks(
    path: Path,
    *,
    expected_chunk_count: int,
    expected_source_set_id: str,
    fts_enabled: bool,
) -> list[dict]:
    if not path.exists():
        return [
            {
                "name": "sqlite_index_exists",
                "passed": False,
                "details": {"path": str(path)},
            }
        ]
    try:
        with closing(sqlite3.connect(path)) as connection:
            chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            source_set_values = [
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT source_set_id FROM chunks ORDER BY source_set_id"
                )
            ]
            metadata_source_set_id = _metadata_value(connection, "source_set_id")
            fts_count = None
            if fts_enabled:
                fts_count = connection.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    except sqlite3.Error as error:
        return [
            {
                "name": "sqlite_index_readable",
                "passed": False,
                "details": {"path": str(path), "error": str(error)},
            }
        ]
    return [
        {
            "name": "sqlite_index_chunk_count_matches_jsonl",
            "passed": chunk_count == expected_chunk_count,
            "details": {"expected": expected_chunk_count, "actual": chunk_count},
        },
        {
            "name": "sqlite_index_source_set_matches",
            "passed": source_set_values == [expected_source_set_id]
            and metadata_source_set_id == expected_source_set_id,
            "details": {
                "expected": expected_source_set_id,
                "chunk_source_set_ids": source_set_values,
                "metadata_source_set_id": metadata_source_set_id,
            },
        },
        {
            "name": "sqlite_fts_chunk_count_matches",
            "passed": (not fts_enabled) or fts_count == expected_chunk_count,
            "details": {
                "fts_enabled": fts_enabled,
                "expected": expected_chunk_count if fts_enabled else None,
                "actual": fts_count,
            },
        },
    ]


def _metadata_value(connection: sqlite3.Connection, key: str) -> object | None:
    row = connection.execute(
        "SELECT value_json FROM metadata WHERE key = ?",
        (key,),
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def _with_additional_checks(validation: dict, checks: list[dict]) -> dict:
    merged_checks = [*validation["checks"], *checks]
    return {
        **validation,
        "passed": all(check["passed"] for check in merged_checks),
        "checks": merged_checks,
    }


def _extraction_summary_is_complete(extraction_summary: dict | None) -> bool:
    if not extraction_summary:
        return False
    catalog_count = _int_from_summary(extraction_summary, "catalog_source_count")
    selected_count = _int_from_summary(extraction_summary, "selected_source_count")
    extracted_count = _int_from_summary(extraction_summary, "extracted_count")
    failed_count = _int_from_summary(extraction_summary, "failed_count")
    required_count = (
        _int_from_summary(extraction_summary, "required_extraction_source_count")
        or catalog_count
    )
    selected_required_count = (
        _int_from_summary(extraction_summary, "selected_required_extraction_source_count")
        or selected_count
    )
    if catalog_count <= 0:
        return False
    filters = extraction_summary.get("filters") or {}
    active_filters = [value for value in filters.values() if value not in (None, "", [])]
    return (
        not active_filters
        and selected_count == catalog_count
        and selected_required_count == required_count
        and extracted_count == required_count
        and failed_count == 0
    )
