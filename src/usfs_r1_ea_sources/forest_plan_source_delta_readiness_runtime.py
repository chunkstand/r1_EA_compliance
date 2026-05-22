from __future__ import annotations

from pathlib import Path

from .forest_plan_source_delta_readiness_checks import _batch_capture_check
from .forest_plan_source_delta_readiness_checks import _canonical_catalog_validation_check
from .forest_plan_source_delta_readiness_checks import _catalog_confirmed_sources_present_check
from .forest_plan_source_delta_readiness_checks import _catalog_validation_check
from .forest_plan_source_delta_readiness_checks import _extraction_readiness_covers_source_delta_rows_check
from .forest_plan_source_delta_readiness_checks import _forest_profile_readiness_blockers_are_source_specific_check
from .forest_plan_source_delta_readiness_checks import _forest_profile_readiness_covers_tracked_units_check
from .forest_plan_source_delta_readiness_checks import _forest_profile_readiness_summary_counts_align_check
from .forest_plan_source_delta_readiness_checks import _merged_catalog_matches_expected_counts_check
from .forest_plan_source_delta_readiness_checks import _official_source_gap_evidence_check
from .forest_plan_source_delta_readiness_checks import _repair_queue_check
from .forest_plan_source_delta_readiness_checks import _required_paths_check
from .forest_plan_source_delta_readiness_checks import _retrieval_readiness_covers_extracted_source_delta_rows_check
from .forest_plan_source_delta_readiness_checks import _source_delta_catalog_matches_register_check
from .forest_plan_source_delta_readiness_checks import _source_delta_catalog_partition_check
from .forest_plan_source_delta_readiness_io import _read_json_if_exists
from .forest_plan_source_delta_readiness_io import _read_jsonl_if_exists
from .forest_plan_source_delta_readiness_io import _render_markdown
from .forest_plan_source_delta_readiness_io import _utc_now
from .forest_plan_source_delta_readiness_io import _write_json
from .forest_plan_source_delta_readiness_models import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_source_delta_readiness_models import DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH
from .forest_plan_source_delta_readiness_models import DEFAULT_R1_FOREST_PLAN_REGISTER_PATH
from .forest_plan_source_delta_readiness_models import DEFAULT_SOURCE_DELTA_BATCH_RUN_ID
from .forest_plan_source_delta_readiness_models import SOURCE_DELTA_READINESS_SCHEMA_VERSION
from .forest_plan_source_delta_readiness_models import SourceDeltaReadinessResult
from .forest_plan_source_delta_readiness_readiness import _extraction_readiness
from .forest_plan_source_delta_readiness_readiness import _forest_profile_readiness
from .forest_plan_source_delta_readiness_readiness import _retrieval_eval_passed_check
from .forest_plan_source_delta_readiness_readiness import _retrieval_readiness
from .forest_plan_source_delta_readiness_summaries import _batch_capture_summary
from .forest_plan_source_delta_readiness_summaries import _catalog_summary
from .forest_plan_source_delta_readiness_summaries import _official_source_gap_evidence_summary
from .forest_plan_source_delta_readiness_summaries import _register_summary
from .records import sha256_file
from .workbook import load_r1_forest_plan_document_register

def build_forest_plan_source_delta_readiness_report(
    *,
    output_dir: Path,
    register_path: Path = DEFAULT_R1_FOREST_PLAN_REGISTER_PATH,
    source_delta_batch_run_id: str = DEFAULT_SOURCE_DELTA_BATCH_RUN_ID,
    scoped_catalog_gate_dir: Path | None = None,
    merged_catalog_gate_dir: Path | None = None,
    canonical_catalog_dir: Path | None = None,
    extraction_source_set_id: str | None = None,
    reuse_inventory_path: Path | None = None,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    official_source_gap_evidence_path: Path = DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH,
    results_dir: Path | None = None,
) -> SourceDeltaReadinessResult:
    """Build the readiness gate for the Region 1 forest-plan source delta."""

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
    official_source_gap_evidence_path = Path(official_source_gap_evidence_path)
    official_source_gap_evidence = _read_json_if_exists(official_source_gap_evidence_path)
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

    merged_catalog_gate_dir = Path(merged_catalog_gate_dir) if merged_catalog_gate_dir else None
    merged_manifest_path = (
        merged_catalog_gate_dir / "source_set_manifest.json" if merged_catalog_gate_dir else None
    )
    merged_validation_path = (
        merged_catalog_gate_dir / "catalog_validation.json" if merged_catalog_gate_dir else None
    )
    merged_catalog_path = (
        merged_catalog_gate_dir / "source_catalog.jsonl" if merged_catalog_gate_dir else None
    )
    merged_sqlite_path = (
        merged_catalog_gate_dir / "review_sources.sqlite" if merged_catalog_gate_dir else None
    )
    merged_manifest = _read_json_if_exists(merged_manifest_path) if merged_manifest_path else {}
    merged_validation = (
        _read_json_if_exists(merged_validation_path) if merged_validation_path else {}
    )
    merged_catalog_records = _read_jsonl_if_exists(merged_catalog_path) if merged_catalog_path else []

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
    merged_catalog_ids = {
        str(record.get("source_record_id") or "") for record in merged_catalog_records
    }
    canonical_catalog_ids = {
        str(record.get("source_record_id") or "") for record in canonical_catalog_records
    }

    scoped_source_set_id = str(scoped_manifest.get("source_set_id") or "")
    merged_source_set_id = str(merged_manifest.get("source_set_id") or "")
    effective_extraction_source_set_id = (
        str(extraction_source_set_id)
        if extraction_source_set_id
        else (merged_source_set_id or scoped_source_set_id)
    )
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
            register=register,
            manifest=canonical_manifest,
            validation=canonical_validation,
            catalog_ids=canonical_catalog_ids,
        ),
        _catalog_confirmed_sources_present_check(
            register=register,
            canonical_catalog_ids=canonical_catalog_ids,
        ),
        _official_source_gap_evidence_check(
            register=register,
            evidence=official_source_gap_evidence,
            path=official_source_gap_evidence_path,
        ),
    ]
    if merged_catalog_gate_dir:
        checks.extend(
            [
                _required_paths_check(
                    "merged_catalog_gate_artifacts_exist",
                    [
                        merged_manifest_path,
                        merged_validation_path,
                        merged_catalog_path,
                        merged_sqlite_path,
                    ],
                ),
                _catalog_validation_check(
                    name="merged_catalog_gate_validation_passed",
                    manifest=merged_manifest,
                    validation=merged_validation,
                    expected_batch_run_id=None,
                ),
                _merged_catalog_matches_expected_counts_check(
                    register=register,
                    manifest=merged_manifest,
                    catalog_ids=merged_catalog_ids,
                ),
            ]
        )

    extraction_readiness = _extraction_readiness(
        output_dir=output_dir,
        source_set_id=effective_extraction_source_set_id,
        expected_source_ids=source_delta_source_ids,
        reuse_inventory_path=Path(reuse_inventory_path) if reuse_inventory_path else None,
    )
    if merged_catalog_gate_dir or extraction_source_set_id or reuse_inventory_path:
        checks.append(_extraction_readiness_covers_source_delta_rows_check(extraction_readiness))
    retrieval_readiness = _retrieval_readiness(
        output_dir=output_dir,
        source_set_id=effective_extraction_source_set_id,
        register=register,
        expected_source_ids=source_delta_source_ids,
    )
    profile_readiness = _forest_profile_readiness(
        register=register,
        forest_plan_profiles_path=forest_plan_profiles_path,
        scoped_catalog_ids=scoped_catalog_ids,
        merged_catalog_ids=merged_catalog_ids,
        canonical_catalog_ids=canonical_catalog_ids,
        output_dir=output_dir,
        source_set_id=effective_extraction_source_set_id,
    )
    if retrieval_readiness["started"]:
        checks.extend(
            [
                _retrieval_readiness_covers_extracted_source_delta_rows_check(retrieval_readiness),
                _retrieval_eval_passed_check(retrieval_readiness),
            ]
        )
    checks.extend(
        [
            _forest_profile_readiness_covers_tracked_units_check(profile_readiness),
            _forest_profile_readiness_blockers_are_source_specific_check(profile_readiness),
            _forest_profile_readiness_summary_counts_align_check(profile_readiness),
        ]
    )
    passed = all(check["passed"] for check in checks)
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
            "merged_catalog_gate_dir": str(merged_catalog_gate_dir)
            if merged_catalog_gate_dir
            else None,
            "canonical_catalog_dir": str(canonical_catalog_dir),
            "extraction_source_set_id": effective_extraction_source_set_id or None,
            "reuse_inventory_path": str(reuse_inventory_path) if reuse_inventory_path else None,
            "forest_plan_profiles_path": str(forest_plan_profiles_path),
            "forest_plan_profiles_sha256": sha256_file(forest_plan_profiles_path)
            if forest_plan_profiles_path.exists()
            else None,
            "official_source_gap_evidence_path": str(official_source_gap_evidence_path),
            "official_source_gap_evidence_sha256": sha256_file(
                official_source_gap_evidence_path
            )
            if official_source_gap_evidence_path.exists()
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
        "merged_source_delta_catalog": _catalog_summary(
            manifest=merged_manifest,
            validation=merged_validation,
            records=merged_catalog_records,
            catalog_dir=merged_catalog_gate_dir,
        )
        if merged_catalog_gate_dir
        else None,
        "active_canonical_catalog": _catalog_summary(
            manifest=canonical_manifest,
            validation=canonical_validation,
            records=canonical_catalog_records,
            catalog_dir=canonical_catalog_dir,
        ),
        "extraction_readiness": extraction_readiness,
        "retrieval_readiness": retrieval_readiness,
        "official_source_gap_evidence": _official_source_gap_evidence_summary(
            register=register,
            evidence=official_source_gap_evidence,
            path=official_source_gap_evidence_path,
        ),
        "forest_profile_readiness": profile_readiness,
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
        "official_source_gap_evidence_path": str(official_source_gap_evidence_path),
        "scoped_source_delta_source_set_id": scoped_manifest.get("source_set_id"),
        "merged_source_delta_source_set_id": merged_manifest.get("source_set_id"),
        "extraction_source_set_id": effective_extraction_source_set_id or None,
        "canonical_catalog_source_set_id": canonical_manifest.get("source_set_id"),
        "extraction_readiness_status": extraction_readiness["status"],
        "extraction_blocker_count": extraction_readiness["blocked_source_record_count"],
        "retrieval_readiness_status": retrieval_readiness["status"],
        "retrieval_eval_passed": retrieval_readiness["retrieval_eval_passed"],
        "forest_profile_readiness_status": profile_readiness["status"],
        "forest_profile_ready_count": profile_readiness["ready_profile_count"],
        "forest_profile_blocked_count": profile_readiness["blocked_profile_count"],
        "failed_check_count": sum(1 for check in checks if not check["passed"]),
        "report_path": str(report_path),
        "markdown_path": str(markdown_path),
    }
    return SourceDeltaReadinessResult(
        report_path=report_path,
        markdown_path=markdown_path,
        summary=summary,
    )
