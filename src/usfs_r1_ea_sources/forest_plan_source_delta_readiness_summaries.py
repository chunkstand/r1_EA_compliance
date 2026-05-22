from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .forest_plan_source_delta_readiness_models import OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION
from .workbook import R1ForestPlanDocumentRegister
def _register_summary(register: R1ForestPlanDocumentRegister) -> dict[str, Any]:
    rows_by_unit = defaultdict(list)
    for row in register.rows:
        rows_by_unit[row["forest_unit_id"]].append(row)
    return {
        **register.summary(),
        "forest_units": [
            {
                "forest_unit_id": forest_unit_id,
                "row_count": len(rows),
                "status_counts": dict(Counter(row["draft_status"] for row in rows)),
                "source_delta_source_record_ids": [
                    row["proposed_source_record_id"]
                    for row in rows
                    if row["draft_status"] == "source_delta_required"
                ],
                "catalog_confirmed_source_record_ids": [
                    row["proposed_source_record_id"]
                    for row in rows
                    if row["draft_status"] == "catalog_confirmed"
                ],
                "gap_source_record_ids": [
                    row["proposed_source_record_id"]
                    for row in rows
                    if row["draft_status"] == "official_source_gap_documented"
                ],
            }
            for forest_unit_id, rows in sorted(rows_by_unit.items())
        ],
    }

def _batch_capture_summary(
    *,
    batch_summary: dict[str, Any],
    batch_ledger: dict[str, Any],
    repair_queue_path: Path,
) -> dict[str, Any]:
    ledger_batches = list(batch_ledger.get("batches") or [])
    ledger_source_ids = sorted(
        {
            str(source_id)
            for batch in ledger_batches
            for source_id in list(batch.get("source_record_ids") or [])
        }
    )
    return {
        "run_id": batch_summary.get("run_id") or batch_ledger.get("run_id"),
        "all_passed": bool(batch_summary.get("all_passed")),
        "planned_row_count": batch_summary.get("planned_row_count"),
        "passed_batch_count": batch_summary.get("passed_batch_count"),
        "failed_batch_count": batch_summary.get("failed_batch_count"),
        "needs_repair_batch_count": batch_summary.get("needs_repair_batch_count"),
        "artifact_count": batch_summary.get("artifact_count"),
        "ledger_batch_count": len(ledger_batches),
        "ledger_source_record_count": len(ledger_source_ids),
        "repair_queue_non_header_row_count": _repair_queue_non_header_row_count(repair_queue_path),
        "source_delta_input": batch_summary.get("source_delta_input"),
    }

def _catalog_summary(
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    records: list[dict[str, Any]],
    catalog_dir: Path | None,
) -> dict[str, Any]:
    return {
        "catalog_dir": str(catalog_dir) if catalog_dir else None,
        "source_set_id": manifest.get("source_set_id"),
        "validation_passed": bool(validation.get("passed")),
        "source_count": manifest.get("source_count"),
        "artifact_count": manifest.get("artifact_count"),
        "download_batch_run_id": manifest.get("download_batch_run_id"),
        "source_delta_input": manifest.get("source_delta_input"),
        "source_record_id_filter_count": manifest.get("source_record_id_filter_count"),
        "supplemental_source_count": manifest.get("supplemental_source_count"),
        "status_counts": manifest.get("status_counts") or {},
        "document_role_counts": manifest.get("document_role_counts") or {},
        "source_partition_counts": manifest.get("source_partition_counts") or {},
        "catalog_record_count": len(records),
        "catalog_source_record_count": len(
            {str(record.get("source_record_id") or "") for record in records}
        ),
    }

def _official_source_gap_evidence_summary(
    *,
    register: R1ForestPlanDocumentRegister,
    evidence: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    records = _official_source_gap_evidence_records(evidence)
    expected_gap_ids = set(register.gap_source_record_ids)
    record_ids = [record.get("source_record_id") for record in records]
    current_records = [
        _official_source_gap_record_summary(record)
        for record in records
        if record.get("source_record_id") in expected_gap_ids
    ]
    return {
        "path": str(path),
        "exists": path.exists(),
        "schema_version": evidence.get("schema_version"),
        "expected_schema_version": OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION,
        "as_of_date": evidence.get("as_of_date"),
        "record_count": len(records),
        "source_record_ids": record_ids,
        "expected_gap_source_record_ids": register.gap_source_record_ids,
        "missing_gap_source_record_ids": sorted(expected_gap_ids - set(record_ids)),
        "unexpected_source_record_ids": sorted(set(record_ids) - expected_gap_ids),
        "records": current_records,
    }

def _official_source_gap_record_summary(record: dict[str, Any]) -> dict[str, Any]:
    candidates = _official_source_gap_candidate_records(record)
    return {
        "source_record_id": record.get("source_record_id"),
        "decision": record.get("decision"),
        "search_date": record.get("search_date"),
        "conclusion": record.get("conclusion"),
        "candidate_count": len(candidates),
        "candidate_urls": [
            str(candidate.get("url") or "") for candidate in candidates if candidate.get("url")
        ],
    }

def _official_source_gap_evidence_records(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [record for record in evidence.get("gap_records") or [] if isinstance(record, dict)]

def _official_source_gap_candidate_records(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in record.get("candidate_evidence") or []
        if isinstance(candidate, dict)
    ]

def _repair_queue_non_header_row_count(path: Path) -> int:
    if not path.exists():
        return -1
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return 0
    return max(0, len(lines) - 1)
