from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json

from .forest_plan_source_delta_readiness_models import DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH
from .forest_plan_source_delta_readiness_models import EXPECTED_BASE_CANONICAL_SOURCE_COUNT
from .forest_plan_source_delta_readiness_models import OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION
from .forest_plan_source_delta_readiness_summaries import _official_source_gap_candidate_records
from .forest_plan_source_delta_readiness_summaries import _official_source_gap_evidence_records
from .forest_plan_source_delta_readiness_summaries import _repair_queue_non_header_row_count
from .workbook import R1ForestPlanDocumentRegister

def _retrieval_readiness_covers_extracted_source_delta_rows_check(
    retrieval_readiness: dict[str, Any],
) -> dict[str, Any]:
    missing_ids = list(retrieval_readiness.get("missing_indexed_extracted_source_record_ids") or [])
    return {
        "name": "source_delta_retrieval_readiness_covers_extracted_rows",
        "passed": not missing_ids,
        "details": {
            "expected_extracted_source_record_count": retrieval_readiness.get(
                "expected_extracted_source_record_count"
            ),
            "indexed_source_record_count_for_expected_sources": retrieval_readiness.get(
                "indexed_source_record_count_for_expected_sources"
            ),
            "missing_indexed_extracted_source_record_ids": missing_ids,
        },
    }

def _forest_profile_readiness_covers_tracked_units_check(
    profile_readiness: dict[str, Any],
) -> dict[str, Any]:
    expected = set(profile_readiness.get("tracked_forest_unit_ids") or [])
    actual = {
        str(row.get("forest_unit_id") or "")
        for row in profile_readiness.get("profile_rows") or []
        if row.get("forest_unit_id")
    }
    return {
        "name": "forest_profile_readiness_tracks_configured_and_register_units",
        "passed": expected == actual,
        "details": {
            "expected_forest_unit_ids": sorted(expected),
            "actual_forest_unit_ids": sorted(actual),
            "missing_forest_unit_ids": sorted(expected - actual),
            "unexpected_forest_unit_ids": sorted(actual - expected),
        },
    }

def _forest_profile_readiness_blockers_are_source_specific_check(
    profile_readiness: dict[str, Any],
) -> dict[str, Any]:
    missing_source_specific_blockers = [
        str(row.get("forest_unit_id") or "")
        for row in profile_readiness.get("profile_rows") or []
        if row.get("profile_readiness_status") != "ready"
        and not list(row.get("blocker_source_record_ids") or [])
    ]
    generic_blocker_rows = [
        str(row.get("forest_unit_id") or "")
        for row in profile_readiness.get("profile_rows") or []
        if "forest_profile_not_ready" in set(row.get("blocker_types") or [])
    ]
    return {
        "name": "forest_profile_readiness_blockers_are_source_specific",
        "passed": not missing_source_specific_blockers and not generic_blocker_rows,
        "details": {
            "missing_source_specific_blockers": missing_source_specific_blockers,
            "generic_blocker_rows": generic_blocker_rows,
        },
    }

def _forest_profile_readiness_summary_counts_align_check(
    profile_readiness: dict[str, Any],
) -> dict[str, Any]:
    configured_rows = [
        row for row in profile_readiness.get("profile_rows") or [] if row.get("configured_profile")
    ]
    tracking_only_rows = [
        row for row in profile_readiness.get("profile_rows") or [] if not row.get("configured_profile")
    ]
    expected_ready_profile_ids = sorted(
        str(row.get("forest_unit_id") or "")
        for row in configured_rows
        if row.get("profile_readiness_status") == "ready"
    )
    expected_blocked_profile_ids = sorted(
        str(row.get("forest_unit_id") or "")
        for row in configured_rows
        if row.get("profile_readiness_status") != "ready"
    )
    expected_ready_tracking_only_ids = sorted(
        str(row.get("forest_unit_id") or "")
        for row in tracking_only_rows
        if row.get("profile_readiness_status") == "ready"
    )
    expected_blocked_tracking_only_ids = sorted(
        str(row.get("forest_unit_id") or "")
        for row in tracking_only_rows
        if row.get("profile_readiness_status") != "ready"
    )
    details = {
        "expected_ready_profile_ids": expected_ready_profile_ids,
        "actual_ready_profile_ids": sorted(profile_readiness.get("ready_profile_ids") or []),
        "expected_blocked_profile_ids": expected_blocked_profile_ids,
        "actual_blocked_profile_ids": sorted(profile_readiness.get("blocked_profile_ids") or []),
        "expected_ready_tracking_only_ids": expected_ready_tracking_only_ids,
        "actual_ready_tracking_only_ids": sorted(
            profile_readiness.get("ready_tracking_only_ids") or []
        ),
        "expected_blocked_tracking_only_ids": expected_blocked_tracking_only_ids,
        "actual_blocked_tracking_only_ids": sorted(
            profile_readiness.get("blocked_tracking_only_ids") or []
        ),
    }
    passed = (
        details["expected_ready_profile_ids"] == details["actual_ready_profile_ids"]
        and details["expected_blocked_profile_ids"] == details["actual_blocked_profile_ids"]
        and details["expected_ready_tracking_only_ids"]
        == details["actual_ready_tracking_only_ids"]
        and details["expected_blocked_tracking_only_ids"]
        == details["actual_blocked_tracking_only_ids"]
    )
    return {
        "name": "forest_profile_readiness_summary_counts_align",
        "passed": passed,
        "details": details,
    }

def _required_paths_check(name: str, paths: list[Path]) -> dict[str, Any]:
    missing = [str(path) for path in paths if not path.exists()]
    return {
        "name": name,
        "passed": not missing,
        "details": {
            "required_paths": [str(path) for path in paths],
            "missing_paths": missing,
        },
    }

def _batch_capture_check(
    *,
    register: R1ForestPlanDocumentRegister,
    batch_summary: dict[str, Any],
    batch_ledger: dict[str, Any],
    source_delta_batch_run_id: str,
) -> dict[str, Any]:
    expected_ids = {source.source_record_id for source in register.source_delta_sources}
    ledger_batches = list(batch_ledger.get("batches") or [])
    ledger_ids = {
        str(source_id)
        for batch in ledger_batches
        for source_id in list(batch.get("source_record_ids") or [])
    }
    failed_batches = [
        batch.get("batch_id")
        for batch in ledger_batches
        if batch.get("status") != "passed" or batch.get("gate_passed") is False
    ]
    details = {
        "expected_run_id": source_delta_batch_run_id,
        "summary_run_id": batch_summary.get("run_id"),
        "ledger_run_id": batch_ledger.get("run_id"),
        "all_passed": bool(batch_summary.get("all_passed")),
        "expected_source_delta_count": len(expected_ids),
        "summary_planned_row_count": batch_summary.get("planned_row_count"),
        "summary_failed_batch_count": batch_summary.get("failed_batch_count"),
        "summary_needs_repair_batch_count": batch_summary.get("needs_repair_batch_count"),
        "ledger_batch_count": len(ledger_batches),
        "failed_ledger_batch_ids": failed_batches,
        "missing_ledger_source_record_ids": sorted(expected_ids - ledger_ids),
        "unexpected_ledger_source_record_ids": sorted(ledger_ids - expected_ids),
    }
    passed = (
        batch_summary.get("run_id") == source_delta_batch_run_id
        and batch_ledger.get("run_id") == source_delta_batch_run_id
        and batch_summary.get("all_passed") is True
        and batch_summary.get("planned_row_count") == len(expected_ids)
        and int(batch_summary.get("failed_batch_count") or 0) == 0
        and int(batch_summary.get("needs_repair_batch_count") or 0) == 0
        and not failed_batches
        and ledger_ids == expected_ids
    )
    return {"name": "source_delta_batch_capture_matches_register", "passed": passed, "details": details}

def _repair_queue_check(path: Path) -> dict[str, Any]:
    non_header_count = _repair_queue_non_header_row_count(path)
    return {
        "name": "source_delta_repair_queue_empty",
        "passed": path.exists() and non_header_count == 0,
        "details": {
            "path": str(path),
            "exists": path.exists(),
            "non_header_row_count": non_header_count,
        },
    }

def _catalog_validation_check(
    *,
    name: str,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    expected_batch_run_id: str | None,
) -> dict[str, Any]:
    details = {
        "manifest_source_set_id": manifest.get("source_set_id"),
        "validation_source_set_id": validation.get("source_set_id"),
        "validation_passed": bool(validation.get("passed")),
        "manifest_download_batch_run_id": manifest.get("download_batch_run_id"),
        "expected_batch_run_id": expected_batch_run_id,
    }
    passed = (
        bool(manifest)
        and bool(validation)
        and validation.get("passed") is True
        and manifest.get("source_set_id") == validation.get("source_set_id")
        and (
            expected_batch_run_id is None
            or manifest.get("download_batch_run_id") == expected_batch_run_id
        )
    )
    return {"name": name, "passed": passed, "details": details}

def _source_delta_catalog_matches_register_check(
    *,
    register: R1ForestPlanDocumentRegister,
    catalog_ids: set[str],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    source_delta_ids = {source.source_record_id for source in register.source_delta_sources}
    gap_ids = set(register.gap_source_record_ids)
    catalog_confirmed_ids = set(register.catalog_confirmed_source_record_ids)
    source_delta_input = manifest.get("source_delta_input") or {}
    details = {
        "expected_source_delta_count": len(source_delta_ids),
        "manifest_source_count": manifest.get("source_count"),
        "manifest_source_delta_count": source_delta_input.get("source_delta_count"),
        "manifest_supplemental_source_count": manifest.get("supplemental_source_count"),
        "manifest_source_record_id_filter_count": manifest.get("source_record_id_filter_count"),
        "catalog_source_record_count": len(catalog_ids),
        "missing_source_delta_ids": sorted(source_delta_ids - catalog_ids),
        "unexpected_catalog_ids": sorted(catalog_ids - source_delta_ids),
        "gap_ids_in_catalog": sorted(gap_ids & catalog_ids),
        "catalog_confirmed_ids_in_source_delta_catalog": sorted(catalog_confirmed_ids & catalog_ids),
    }
    passed = (
        manifest.get("source_count") == len(source_delta_ids)
        and source_delta_input.get("source_delta_count") == len(source_delta_ids)
        and manifest.get("supplemental_source_count") == len(source_delta_ids)
        and manifest.get("source_record_id_filter_count") == len(source_delta_ids)
        and catalog_ids == source_delta_ids
        and not (gap_ids & catalog_ids)
        and not (catalog_confirmed_ids & catalog_ids)
    )
    return {
        "name": "source_delta_catalog_gate_matches_register",
        "passed": passed,
        "details": details,
    }

def _source_delta_catalog_partition_check(
    *,
    register: R1ForestPlanDocumentRegister,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    expected_count = len(register.source_delta_sources)
    expected_primary_plan_ids = _register_primary_plan_source_record_ids(register)
    partition_counts = manifest.get("source_partition_counts") or {}
    role_counts = manifest.get("document_role_counts") or {}
    details = {
        "expected_source_delta_count": expected_count,
        "expected_primary_plan_source_record_ids": sorted(expected_primary_plan_ids),
        "expected_document_role_counts": {
            "forest_plan": len(expected_primary_plan_ids),
            "forest_plan_support": expected_count - len(expected_primary_plan_ids),
        },
        "source_partition_counts": partition_counts,
        "document_role_counts": role_counts,
        "status_counts": manifest.get("status_counts") or {},
        "artifact_count": manifest.get("artifact_count"),
    }
    passed = (
        partition_counts.get("active_review_corpus") == expected_count
        and role_counts.get("forest_plan") == len(expected_primary_plan_ids)
        and role_counts.get("forest_plan_support") == expected_count - len(expected_primary_plan_ids)
        and int(manifest.get("artifact_count") or 0) > 0
    )
    return {
        "name": "source_delta_catalog_gate_keeps_rows_active_and_support_scoped",
        "passed": passed,
        "details": details,
    }

def _register_primary_plan_source_record_ids(register: R1ForestPlanDocumentRegister) -> set[str]:
    payload = json.loads(
        DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    profile_rows = payload.get("profile_rows")
    if not isinstance(profile_rows, list):
        raise ValueError(
            "Region 1 inventory build manifest must contain a profile_rows list for "
            "source-delta readiness checks."
        )
    source_delta_ids = {source.source_record_id for source in register.source_delta_sources}
    return {
        str(row.get("primary_plan_source_record_id") or "")
        for row in profile_rows
        if isinstance(row, dict)
        and str(row.get("primary_plan_source_record_id") or "") in source_delta_ids
    }

def _merged_catalog_matches_expected_counts_check(
    *,
    register: R1ForestPlanDocumentRegister,
    manifest: dict[str, Any],
    catalog_ids: set[str],
) -> dict[str, Any]:
    source_delta_ids = {source.source_record_id for source in register.source_delta_sources}
    catalog_confirmed_ids = set(register.catalog_confirmed_source_record_ids)
    gap_ids = set(register.gap_source_record_ids)
    expected_source_count = EXPECTED_BASE_CANONICAL_SOURCE_COUNT + len(source_delta_ids)
    details = {
        "expected_source_count": expected_source_count,
        "manifest_source_count": manifest.get("source_count"),
        "expected_supplemental_source_count": len(source_delta_ids),
        "manifest_supplemental_source_count": manifest.get("supplemental_source_count"),
        "missing_source_delta_ids": sorted(source_delta_ids - catalog_ids),
        "missing_catalog_confirmed_ids": sorted(catalog_confirmed_ids - catalog_ids),
        "gap_ids_in_catalog": sorted(gap_ids & catalog_ids),
    }
    passed = (
        manifest.get("source_count") == expected_source_count
        and manifest.get("supplemental_source_count") == len(source_delta_ids)
        and source_delta_ids <= catalog_ids
        and catalog_confirmed_ids <= catalog_ids
        and not (gap_ids & catalog_ids)
    )
    return {
        "name": "merged_catalog_gate_matches_expected_source_delta_and_canonical_counts",
        "passed": passed,
        "details": details,
    }

def _extraction_readiness_covers_source_delta_rows_check(
    extraction_readiness: dict[str, Any],
) -> dict[str, Any]:
    coverage_complete = bool(extraction_readiness.get("coverage_complete"))
    reuse_inventory = extraction_readiness.get("reuse_inventory") or {}
    passed = coverage_complete and (
        reuse_inventory.get("status") in {"not_provided", "ready"}
    )
    return {
        "name": "source_delta_extraction_readiness_covers_expected_rows",
        "passed": passed,
        "details": {
            "status": extraction_readiness.get("status"),
            "coverage_complete": coverage_complete,
            "missing_source_record_ids": extraction_readiness.get("missing_source_record_ids_sample")
            or [],
            "blocked_status_counts": extraction_readiness.get("blocked_status_counts") or {},
            "reuse_inventory_status": reuse_inventory.get("status"),
            "reuse_inventory_missing_source_record_ids": reuse_inventory.get(
                "missing_source_record_ids"
            )
            or [],
        },
    }

def _canonical_catalog_validation_check(
    *,
    register: R1ForestPlanDocumentRegister,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    catalog_ids: set[str],
) -> dict[str, Any]:
    base_check = _catalog_validation_check(
        name="canonical_catalog_validation_passed",
        manifest=manifest,
        validation=validation,
        expected_batch_run_id=None,
    )
    source_delta_ids = {source.source_record_id for source in register.source_delta_sources}
    expected_source_count = EXPECTED_BASE_CANONICAL_SOURCE_COUNT + len(source_delta_ids)
    expected_source_delta_input = register.summary()
    details = {
        **base_check["details"],
        "expected_canonical_source_count": expected_source_count,
        "manifest_source_count": manifest.get("source_count"),
        "expected_source_delta_input": expected_source_delta_input,
        "source_delta_input": manifest.get("source_delta_input"),
        "expected_supplemental_source_count": len(source_delta_ids),
        "manifest_supplemental_source_count": manifest.get("supplemental_source_count"),
        "missing_source_delta_ids": sorted(source_delta_ids - catalog_ids),
    }
    passed = (
        base_check["passed"]
        and manifest.get("source_count") == expected_source_count
        and manifest.get("supplemental_source_count") == len(source_delta_ids)
        and manifest.get("source_delta_input") == expected_source_delta_input
        and source_delta_ids <= catalog_ids
    )
    return {"name": "canonical_catalog_validation_passed", "passed": passed, "details": details}

def _catalog_confirmed_sources_present_check(
    *,
    register: R1ForestPlanDocumentRegister,
    canonical_catalog_ids: set[str],
) -> dict[str, Any]:
    expected_ids = set(register.catalog_confirmed_source_record_ids)
    details = {
        "expected_catalog_confirmed_count": len(expected_ids),
        "present_catalog_confirmed_count": len(expected_ids & canonical_catalog_ids),
        "missing_catalog_confirmed_source_record_ids": sorted(expected_ids - canonical_catalog_ids),
    }
    return {
        "name": "catalog_confirmed_register_rows_present_in_canonical_catalog",
        "passed": expected_ids <= canonical_catalog_ids,
        "details": details,
    }

def _official_source_gap_evidence_check(
    *,
    register: R1ForestPlanDocumentRegister,
    evidence: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    records = _official_source_gap_evidence_records(evidence)
    expected_ids = set(register.gap_source_record_ids)
    record_ids = [str(record.get("source_record_id") or "") for record in records]
    record_id_counts = Counter(record_ids)
    duplicate_ids = sorted(source_id for source_id, count in record_id_counts.items() if count > 1)
    unexpected_ids = sorted(set(record_ids) - expected_ids)
    missing_ids = sorted(expected_ids - set(record_ids))
    records_by_id = {str(record.get("source_record_id") or ""): record for record in records}

    missing_record_fields: list[dict[str, str]] = []
    missing_candidate_fields: list[dict[str, str]] = []
    accepted_replacement_candidate_ids: list[str] = []
    non_preserved_decision_ids: list[str] = []
    records_without_candidates: list[str] = []
    for source_record_id in sorted(expected_ids):
        record = records_by_id.get(source_record_id) or {}
        for field in ("decision", "search_date", "conclusion"):
            if not str(record.get(field) or "").strip():
                missing_record_fields.append({"source_record_id": source_record_id, "field": field})
        if record.get("decision") != "preserve_official_source_gap":
            non_preserved_decision_ids.append(source_record_id)
        candidates = _official_source_gap_candidate_records(record)
        if not candidates:
            records_without_candidates.append(source_record_id)
        for index, candidate in enumerate(candidates):
            candidate_key = f"{source_record_id}#{index + 1}"
            required_fields = (
                "url",
                "access_result",
                "content_type",
                "accepted_or_rejected_reason",
                "search_date",
                "operator_notes",
            )
            for field in required_fields:
                if not str(candidate.get(field) or "").strip():
                    missing_candidate_fields.append({"candidate": candidate_key, "field": field})
            if candidate.get("accepted_as_replacement") is not False:
                accepted_replacement_candidate_ids.append(candidate_key)

    details = {
        "path": str(path),
        "exists": path.exists(),
        "schema_version": evidence.get("schema_version"),
        "expected_schema_version": OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION,
        "expected_gap_source_record_ids": sorted(expected_ids),
        "evidence_source_record_ids": sorted(record_ids),
        "missing_gap_source_record_ids": missing_ids,
        "unexpected_source_record_ids": unexpected_ids,
        "duplicate_source_record_ids": duplicate_ids,
        "missing_record_fields": missing_record_fields,
        "missing_candidate_fields": missing_candidate_fields,
        "records_without_candidates": records_without_candidates,
        "non_preserved_decision_ids": non_preserved_decision_ids,
        "accepted_replacement_candidate_ids": accepted_replacement_candidate_ids,
    }
    passed = (
        path.exists()
        and evidence.get("schema_version") == OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION
        and set(record_ids) == expected_ids
        and not duplicate_ids
        and not missing_record_fields
        and not missing_candidate_fields
        and not records_without_candidates
        and not non_preserved_decision_ids
        and not accepted_replacement_candidate_ids
    )
    return {
        "name": "official_source_gap_evidence_current_for_register",
        "passed": passed,
        "details": details,
    }
