from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

from .records import sha256_file
from .workbook import R1ForestPlanDocumentRegister
from .workbook import load_r1_forest_plan_document_register


SOURCE_DELTA_READINESS_SCHEMA_VERSION = "r1-forest-plan-source-delta-readiness-v0"
DEFAULT_R1_FOREST_PLAN_REGISTER_PATH = Path("config/r1_forest_plan_document_register_draft.csv")
DEFAULT_FOREST_PLAN_PROFILES_PATH = Path("config/forest_plan_profiles.json")
DEFAULT_SOURCE_DELTA_BATCH_RUN_ID = "r1-forest-plan-source-delta-capture-20260510-batches"
EXPECTED_CANONICAL_SOURCE_COUNT = 190


@dataclass(frozen=True)
class SourceDeltaReadinessResult:
    report_path: Path
    markdown_path: Path
    summary: dict[str, Any]


def build_forest_plan_source_delta_readiness_report(
    *,
    output_dir: Path,
    register_path: Path = DEFAULT_R1_FOREST_PLAN_REGISTER_PATH,
    source_delta_batch_run_id: str = DEFAULT_SOURCE_DELTA_BATCH_RUN_ID,
    scoped_catalog_gate_dir: Path | None = None,
    canonical_catalog_dir: Path | None = None,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    results_dir: Path | None = None,
) -> SourceDeltaReadinessResult:
    """Build the Sequence 0 readiness gate for the Region 1 forest-plan source delta."""

    output_dir = Path(output_dir)
    register_path = Path(register_path)
    scoped_catalog_gate_dir = (
        Path(scoped_catalog_gate_dir)
        if scoped_catalog_gate_dir
        else output_dir / "runs" / source_delta_batch_run_id / "catalog_gate"
    )
    canonical_catalog_dir = (
        Path(canonical_catalog_dir) if canonical_catalog_dir else output_dir / "catalog"
    )
    results_dir = (
        Path(results_dir)
        if results_dir
        else output_dir / "runs" / source_delta_batch_run_id / "source_delta_readiness"
    )

    register = load_r1_forest_plan_document_register(register_path)
    run_dir = output_dir / "runs" / source_delta_batch_run_id
    batch_summary_path = run_dir / "summary.json"
    batch_ledger_path = run_dir / "batch_ledger.json"
    repair_queue_path = run_dir / "repair_queue.csv"

    batch_summary = _read_json_if_exists(batch_summary_path)
    batch_ledger = _read_json_if_exists(batch_ledger_path)
    scoped_manifest_path = scoped_catalog_gate_dir / "source_set_manifest.json"
    scoped_validation_path = scoped_catalog_gate_dir / "catalog_validation.json"
    scoped_catalog_path = scoped_catalog_gate_dir / "source_catalog.jsonl"
    scoped_sqlite_path = scoped_catalog_gate_dir / "review_sources.sqlite"
    scoped_manifest = _read_json_if_exists(scoped_manifest_path)
    scoped_validation = _read_json_if_exists(scoped_validation_path)
    scoped_catalog_records = _read_jsonl_if_exists(scoped_catalog_path)

    canonical_manifest_path = canonical_catalog_dir / "source_set_manifest.json"
    canonical_validation_path = canonical_catalog_dir / "catalog_validation.json"
    canonical_catalog_path = canonical_catalog_dir / "source_catalog.jsonl"
    canonical_sqlite_path = canonical_catalog_dir / "review_sources.sqlite"
    canonical_manifest = _read_json_if_exists(canonical_manifest_path)
    canonical_validation = _read_json_if_exists(canonical_validation_path)
    canonical_catalog_records = _read_jsonl_if_exists(canonical_catalog_path)

    source_delta_source_ids = {
        source.source_record_id for source in register.source_delta_sources
    }
    scoped_catalog_ids = {
        str(record.get("source_record_id") or "") for record in scoped_catalog_records
    }
    canonical_catalog_ids = {
        str(record.get("source_record_id") or "") for record in canonical_catalog_records
    }

    scoped_source_set_id = str(scoped_manifest.get("source_set_id") or "")
    checks = [
        _required_paths_check(
            "source_delta_batch_artifacts_exist",
            [batch_summary_path, batch_ledger_path, repair_queue_path],
        ),
        _batch_capture_check(
            register=register,
            batch_summary=batch_summary,
            batch_ledger=batch_ledger,
            source_delta_batch_run_id=source_delta_batch_run_id,
        ),
        _repair_queue_check(repair_queue_path),
        _required_paths_check(
            "source_delta_catalog_gate_artifacts_exist",
            [
                scoped_manifest_path,
                scoped_validation_path,
                scoped_catalog_path,
                scoped_sqlite_path,
            ],
        ),
        _catalog_validation_check(
            name="source_delta_catalog_gate_validation_passed",
            manifest=scoped_manifest,
            validation=scoped_validation,
            expected_batch_run_id=source_delta_batch_run_id,
        ),
        _source_delta_catalog_matches_register_check(
            register=register,
            catalog_ids=scoped_catalog_ids,
            manifest=scoped_manifest,
        ),
        _source_delta_catalog_partition_check(
            register=register,
            manifest=scoped_manifest,
        ),
        _required_paths_check(
            "canonical_catalog_artifacts_exist",
            [
                canonical_manifest_path,
                canonical_validation_path,
                canonical_catalog_path,
                canonical_sqlite_path,
            ],
        ),
        _canonical_catalog_validation_check(
            manifest=canonical_manifest,
            validation=canonical_validation,
        ),
        _catalog_confirmed_sources_present_check(
            register=register,
            canonical_catalog_ids=canonical_catalog_ids,
        ),
    ]
    passed = all(check["passed"] for check in checks)

    extraction_readiness = _extraction_readiness(
        output_dir=output_dir,
        source_set_id=scoped_source_set_id,
        expected_source_ids=source_delta_source_ids,
    )
    retrieval_readiness = _retrieval_readiness(
        output_dir=output_dir,
        source_set_id=scoped_source_set_id,
    )
    profile_readiness = _profile_readiness_placeholders(
        register=register,
        forest_plan_profiles_path=forest_plan_profiles_path,
    )
    report = {
        "schema_version": SOURCE_DELTA_READINESS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "passed": passed,
        "inputs": {
            "output_dir": str(output_dir),
            "register_path": str(register_path),
            "register_sha256": sha256_file(register_path) if register_path.exists() else None,
            "source_delta_batch_run_id": source_delta_batch_run_id,
            "source_delta_batch_summary_path": str(batch_summary_path),
            "source_delta_batch_ledger_path": str(batch_ledger_path),
            "source_delta_repair_queue_path": str(repair_queue_path),
            "scoped_catalog_gate_dir": str(scoped_catalog_gate_dir),
            "canonical_catalog_dir": str(canonical_catalog_dir),
            "forest_plan_profiles_path": str(forest_plan_profiles_path),
            "forest_plan_profiles_sha256": sha256_file(forest_plan_profiles_path)
            if forest_plan_profiles_path.exists()
            else None,
        },
        "register": _register_summary(register),
        "source_delta_batch_capture": _batch_capture_summary(
            batch_summary=batch_summary,
            batch_ledger=batch_ledger,
            repair_queue_path=repair_queue_path,
        ),
        "scoped_source_delta_catalog": _catalog_summary(
            manifest=scoped_manifest,
            validation=scoped_validation,
            records=scoped_catalog_records,
            catalog_dir=scoped_catalog_gate_dir,
        ),
        "active_canonical_catalog": _catalog_summary(
            manifest=canonical_manifest,
            validation=canonical_validation,
            records=canonical_catalog_records,
            catalog_dir=canonical_catalog_dir,
        ),
        "extraction_readiness": extraction_readiness,
        "retrieval_readiness": retrieval_readiness,
        "forest_profile_readiness_placeholders": profile_readiness,
        "checks": checks,
    }

    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "r1_forest_plan_source_delta_readiness_report.json"
    markdown_path = results_dir / "r1_forest_plan_source_delta_readiness_report.md"
    _write_json(report_path, report)
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")

    summary = {
        "schema_version": SOURCE_DELTA_READINESS_SCHEMA_VERSION,
        "passed": passed,
        "source_delta_batch_run_id": source_delta_batch_run_id,
        "source_delta_source_count": len(register.source_delta_sources),
        "catalog_confirmed_count": len(register.catalog_confirmed_source_record_ids),
        "official_source_gap_count": len(register.gap_source_record_ids),
        "official_source_gap_ids": register.gap_source_record_ids,
        "scoped_source_delta_source_set_id": scoped_manifest.get("source_set_id"),
        "canonical_catalog_source_set_id": canonical_manifest.get("source_set_id"),
        "extraction_readiness_status": extraction_readiness["status"],
        "retrieval_readiness_status": retrieval_readiness["status"],
        "failed_check_count": sum(1 for check in checks if not check["passed"]),
        "report_path": str(report_path),
        "markdown_path": str(markdown_path),
    }
    return SourceDeltaReadinessResult(
        report_path=report_path,
        markdown_path=markdown_path,
        summary=summary,
    )


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
    catalog_dir: Path,
) -> dict[str, Any]:
    return {
        "catalog_dir": str(catalog_dir),
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


def _extraction_readiness(
    *,
    output_dir: Path,
    source_set_id: str,
    expected_source_ids: set[str],
) -> dict[str, Any]:
    derived_dir = output_dir / "derived" / source_set_id if source_set_id else output_dir / "derived"
    manifest_path = derived_dir / "diagnostics" / "extraction_manifest.jsonl"
    validation_path = derived_dir / "diagnostics" / "extraction_validation.json"
    summary_path = derived_dir / "diagnostics" / "summary.json"
    chunks_path = derived_dir / "chunks" / "chunks.jsonl"
    manifest_records = _read_jsonl_if_exists(manifest_path)
    extracted_source_ids = {
        str(record.get("source_record_id") or "") for record in manifest_records
    }
    missing_source_ids = sorted(expected_source_ids - extracted_source_ids)
    validation = _read_json_if_exists(validation_path)
    status = "not_started"
    if manifest_path.exists() or chunks_path.exists() or validation_path.exists():
        status = "ready" if validation.get("passed") and not missing_source_ids else "partial"
    return {
        "status": status,
        "source_set_id": source_set_id or None,
        "extraction_manifest_path": str(manifest_path),
        "extraction_manifest_exists": manifest_path.exists(),
        "extraction_validation_path": str(validation_path),
        "extraction_validation_exists": validation_path.exists(),
        "extraction_validation_passed": bool(validation.get("passed")),
        "extraction_summary_path": str(summary_path),
        "extraction_summary_exists": summary_path.exists(),
        "chunks_path": str(chunks_path),
        "chunks_exists": chunks_path.exists(),
        "extracted_source_record_count": len(extracted_source_ids),
        "expected_source_record_count": len(expected_source_ids),
        "missing_source_record_count": len(missing_source_ids),
        "missing_source_record_ids_sample": missing_source_ids[:20],
    }


def _retrieval_readiness(*, output_dir: Path, source_set_id: str) -> dict[str, Any]:
    derived_dir = output_dir / "derived" / source_set_id if source_set_id else output_dir / "derived"
    retrieval_dir = derived_dir / "retrieval"
    index_path = retrieval_dir / "evidence_index.sqlite"
    validation_path = retrieval_dir / "retrieval_validation.json"
    summary_path = retrieval_dir / "summary.json"
    validation = _read_json_if_exists(validation_path)
    status = "not_started"
    if index_path.exists() or validation_path.exists():
        status = "ready" if validation.get("passed") else "partial"
    return {
        "status": status,
        "source_set_id": source_set_id or None,
        "index_path": str(index_path),
        "index_exists": index_path.exists(),
        "retrieval_validation_path": str(validation_path),
        "retrieval_validation_exists": validation_path.exists(),
        "retrieval_validation_passed": bool(validation.get("passed")),
        "retrieval_summary_path": str(summary_path),
        "retrieval_summary_exists": summary_path.exists(),
    }


def _profile_readiness_placeholders(
    *,
    register: R1ForestPlanDocumentRegister,
    forest_plan_profiles_path: Path,
) -> dict[str, Any]:
    profiles = _read_json_if_exists(forest_plan_profiles_path)
    configured_profile_ids = [
        str(profile.get("forest_unit_id"))
        for profile in profiles.get("profiles", [])
        if profile.get("forest_unit_id")
    ]
    rows_by_unit = defaultdict(list)
    for row in register.rows:
        rows_by_unit[row["forest_unit_id"]].append(row)

    units = []
    for forest_unit_id, rows in sorted(rows_by_unit.items()):
        status_counts = Counter(row["draft_status"] for row in rows)
        gap_ids = [
            row["proposed_source_record_id"]
            for row in rows
            if row["draft_status"] == "official_source_gap_documented"
        ]
        source_delta_ids = [
            row["proposed_source_record_id"]
            for row in rows
            if row["draft_status"] == "source_delta_required"
        ]
        blocker_types = []
        if source_delta_ids:
            blocker_types.extend(
                [
                    "source_delta_extraction_pending",
                    "source_delta_retrieval_pending",
                ]
            )
        if gap_ids:
            blocker_types.append("official_source_gap")
        units.append(
            {
                "forest_unit_id": forest_unit_id,
                "configured_profile": forest_unit_id in configured_profile_ids,
                "status": "placeholder_pending_extraction_retrieval",
                "row_count": len(rows),
                "status_counts": dict(status_counts),
                "catalog_confirmed_count": status_counts.get("catalog_confirmed", 0),
                "source_delta_count": len(source_delta_ids),
                "official_source_gap_count": len(gap_ids),
                "official_source_gap_ids": gap_ids,
                "blocker_types": blocker_types,
            }
        )

    return {
        "status": "placeholder_pending_extraction_retrieval",
        "forest_plan_profiles_path": str(forest_plan_profiles_path),
        "configured_profile_count": len(configured_profile_ids),
        "configured_profile_ids": configured_profile_ids,
        "forest_unit_count": len(units),
        "forest_units": units,
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
    partition_counts = manifest.get("source_partition_counts") or {}
    role_counts = manifest.get("document_role_counts") or {}
    details = {
        "expected_source_delta_count": expected_count,
        "source_partition_counts": partition_counts,
        "document_role_counts": role_counts,
        "status_counts": manifest.get("status_counts") or {},
        "artifact_count": manifest.get("artifact_count"),
    }
    passed = (
        partition_counts.get("active_review_corpus") == expected_count
        and role_counts.get("forest_plan_support") == expected_count
        and int(manifest.get("artifact_count") or 0) > 0
    )
    return {
        "name": "source_delta_catalog_gate_keeps_rows_active_and_support_scoped",
        "passed": passed,
        "details": details,
    }


def _canonical_catalog_validation_check(
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    base_check = _catalog_validation_check(
        name="canonical_catalog_validation_passed",
        manifest=manifest,
        validation=validation,
        expected_batch_run_id=None,
    )
    details = {
        **base_check["details"],
        "expected_canonical_source_count": EXPECTED_CANONICAL_SOURCE_COUNT,
        "manifest_source_count": manifest.get("source_count"),
        "source_delta_input": manifest.get("source_delta_input"),
    }
    passed = (
        base_check["passed"]
        and manifest.get("source_count") == EXPECTED_CANONICAL_SOURCE_COUNT
        and manifest.get("source_delta_input") is None
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


def _repair_queue_non_header_row_count(path: Path) -> int:
    if not path.exists():
        return -1
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return 0
    return max(0, len(lines) - 1)


def _render_markdown(report: dict[str, Any]) -> str:
    summary_lines = [
        "# Region 1 Forest-Plan Source-Delta Readiness",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Created: `{report['created_at']}`",
        f"- Gate passed: `{str(report['passed']).lower()}`",
        f"- Source-delta rows: `{report['register']['source_delta_count']}`",
        f"- Catalog-confirmed rows: `{report['register']['catalog_confirmed_count']}`",
        f"- Official-source gaps: `{report['register']['gap_count']}`",
        "- Gap source IDs: "
        + ", ".join(f"`{source_id}`" for source_id in report["register"]["skipped_gap_source_record_ids"]),
        f"- Scoped source-delta source set: `{report['scoped_source_delta_catalog']['source_set_id']}`",
        f"- Active canonical source set: `{report['active_canonical_catalog']['source_set_id']}`",
        f"- Extraction readiness: `{report['extraction_readiness']['status']}`",
        f"- Retrieval readiness: `{report['retrieval_readiness']['status']}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        marker = "pass" if check["passed"] else "fail"
        summary_lines.append(f"- `{marker}` `{check['name']}`")
    summary_lines.extend(
        [
            "",
            "## Forest-Profile Placeholders",
            "",
        ]
    )
    for unit in report["forest_profile_readiness_placeholders"]["forest_units"]:
        blockers = ", ".join(f"`{item}`" for item in unit["blocker_types"]) or "`none`"
        summary_lines.append(
            "- "
            + f"`{unit['forest_unit_id']}`: "
            + f"source_delta=`{unit['source_delta_count']}`, "
            + f"gaps=`{unit['official_source_gap_count']}`, "
            + f"blockers={blockers}"
        )
    summary_lines.append("")
    return "\n".join(summary_lines)


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
