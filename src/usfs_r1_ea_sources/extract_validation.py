from __future__ import annotations

from collections import Counter
from pathlib import Path

from .extract_common import NON_EXTRACTABLE_SOURCE_STATUSES
from .extract_common import PROVING_PLACEHOLDER_ARTIFACT_SCHEMA_VERSION
from .extract_common import REQUIRED_CHUNK_PROVENANCE
from .extract_common import TERMINAL_STATUSES
from .extract_common import _normalize_xml_scope_identifier
from .extract_common import _utc_now
from .extract_common import _xml_scope_for_row

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
        _check_placeholder_artifacts_are_auditable(manifest_records),
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
        and record["status"] != "placeholder_artifact"
        and record.get("source_status") not in NON_EXTRACTABLE_SOURCE_STATUSES
    ]
    skipped = [
        record["source_record_id"]
        for record in records
        if record.get("source_status") in NON_EXTRACTABLE_SOURCE_STATUSES
    ]
    placeholders = [
        record["source_record_id"]
        for record in records
        if record.get("status") == "placeholder_artifact"
    ]
    return {
        "name": "all_required_rows_extracted",
        "passed": not failed,
        "details": {
            "status_counts": dict(Counter(record["status"] for record in records)),
            "skipped_non_extractable_source_record_ids": sorted(skipped),
            "placeholder_source_record_ids": sorted(placeholders),
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


def _check_placeholder_artifacts_are_auditable(records: list[dict]) -> dict:
    failures = []
    for record in records:
        if record.get("status") != "placeholder_artifact":
            continue
        metadata = record.get("parser_metadata") or {}
        placeholder = metadata.get("placeholder_artifact") if isinstance(metadata, dict) else None
        if not isinstance(placeholder, dict):
            failures.append(
                {
                    "source_record_id": record.get("source_record_id"),
                    "reason": "missing_placeholder_artifact_metadata",
                }
            )
            continue
        if placeholder.get("schema_version") != PROVING_PLACEHOLDER_ARTIFACT_SCHEMA_VERSION:
            failures.append(
                {
                    "source_record_id": record.get("source_record_id"),
                    "reason": "unexpected_placeholder_artifact_schema_version",
                    "schema_version": placeholder.get("schema_version"),
                }
            )
    return {
        "name": "placeholder_artifacts_are_auditable",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
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
    extraction_priority_counts = Counter(
        record.get("extraction_priority")
        for record in manifest_records
        if record.get("extraction_priority")
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
            if status not in {"extracted", "placeholder_artifact"}
            and status not in NON_EXTRACTABLE_SOURCE_STATUSES
        ),
        "chunk_count": len(chunks),
        "status_counts": dict(status_counts),
        "source_status_counts": dict(source_status_counts),
        "expected_parser_counts": dict(expected_parser_counts),
        "parser_counts": dict(parser_counts),
        "fallback_counts": dict(fallback_counts),
        "reused_count": reused_count,
        "extraction_priority_counts": dict(extraction_priority_counts),
        "direct_document_artifact_required_count": sum(
            1 for record in manifest_records if record.get("direct_document_artifact_required")
        ),
        "failure_counts": {key: count for key, count in failure_counts.items() if key},
        "failed_source_examples": _failed_source_examples(manifest_records),
        "validation_passed": validation["passed"],
        "chunks_path": str(chunks_path),
        "extraction_manifest_path": str(extraction_manifest_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
    }


def _merge_selected_records(
    existing_records: list[dict],
    refreshed_records: list[dict],
    *,
    replace_source_record_ids: set[str],
) -> list[dict]:
    merged = [
        record
        for record in existing_records
        if str(record.get("source_record_id") or "") not in replace_source_record_ids
    ]
    merged.extend(refreshed_records)
    return sorted(merged, key=lambda record: str(record.get("source_record_id") or ""))


def _merge_selected_chunks(
    existing_chunks: list[dict],
    refreshed_chunks: list[dict],
    *,
    replace_source_record_ids: set[str],
) -> list[dict]:
    merged = [
        chunk
        for chunk in existing_chunks
        if str(chunk.get("source_record_id") or "") not in replace_source_record_ids
    ]
    merged.extend(refreshed_chunks)
    return sorted(
        merged,
        key=lambda chunk: (
            str(chunk.get("source_record_id") or ""),
            int(chunk.get("chunk_index") or 0),
            str(chunk.get("chunk_id") or ""),
        ),
    )


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


def _summary_represents_full_catalog(summary: dict | None) -> bool:
    if not isinstance(summary, dict):
        return False
    filters = summary.get("filters") or {}
    active_filters = [value for value in filters.values() if value not in (None, "", [])]
    try:
        selected_source_count = int(summary.get("selected_source_count") or 0)
        catalog_source_count = int(summary.get("catalog_source_count") or 0)
        extracted_count = int(summary.get("extracted_count") or 0)
        required_extraction_source_count = int(summary.get("required_extraction_source_count") or 0)
        failed_count = int(summary.get("failed_count") or 0)
    except (TypeError, ValueError):
        return False
    return (
        not active_filters
        and catalog_source_count > 0
        and selected_source_count == catalog_source_count
        and extracted_count == required_extraction_source_count
        and failed_count == 0
    )
