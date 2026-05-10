from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import sqlite3

from .records import sha256_file
from .forest_plan_profiles import load_forest_plan_profiles
from .workbook import R1ForestPlanDocumentRegister
from .workbook import load_r1_forest_plan_document_register


SOURCE_DELTA_READINESS_SCHEMA_VERSION = "r1-forest-plan-source-delta-readiness-v3"
OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION = "r1-forest-plan-official-source-gap-evidence-v0"
DEFAULT_R1_FOREST_PLAN_REGISTER_PATH = Path("config/r1_forest_plan_document_register_draft.csv")
DEFAULT_FOREST_PLAN_PROFILES_PATH = Path("config/forest_plan_profiles.json")
DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH = Path(
    "config/r1_forest_plan_official_source_gap_evidence.json"
)
DEFAULT_SOURCE_DELTA_BATCH_RUN_ID = "r1-forest-plan-source-delta-capture-20260510-batches"
EXPECTED_BASE_CANONICAL_SOURCE_COUNT = 190


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


def _extraction_readiness(
    *,
    output_dir: Path,
    source_set_id: str,
    expected_source_ids: set[str],
    reuse_inventory_path: Path | None = None,
) -> dict[str, Any]:
    derived_dir = output_dir / "derived" / source_set_id if source_set_id else output_dir / "derived"
    manifest_path = derived_dir / "diagnostics" / "extraction_manifest.jsonl"
    validation_path = derived_dir / "diagnostics" / "extraction_validation.json"
    summary_path = derived_dir / "diagnostics" / "summary.json"
    chunks_path = derived_dir / "chunks" / "chunks.jsonl"
    manifest_records = _read_jsonl_if_exists(manifest_path)
    summary = _read_json_if_exists(summary_path)
    expected_records = [
        record
        for record in manifest_records
        if str(record.get("source_record_id") or "") in expected_source_ids
    ]
    accounted_source_ids = {
        str(record.get("source_record_id") or "") for record in expected_records
    }
    missing_source_ids = sorted(expected_source_ids - accounted_source_ids)
    status_counts = Counter(str(record.get("status") or "") for record in expected_records)
    blocked_records = [
        record
        for record in expected_records
        if record.get("status") != "extracted"
        and record.get("source_status") not in {"skipped_excluded"}
    ]
    blocked_status_counts = Counter(str(record.get("status") or "") for record in blocked_records)
    blocker_error_class_counts = Counter(
        str((record.get("failure") or {}).get("error_class") or "")
        for record in blocked_records
        if (record.get("failure") or {}).get("error_class")
    )
    nonterminal_source_ids = sorted(
        record.get("source_record_id")
        for record in expected_records
        if record.get("status") not in {
            "extracted",
            "skipped_excluded",
            "no_artifact",
            "artifact_missing",
            "hash_mismatch",
            "parser_error",
            "parser_timeout",
            "empty_text",
        }
    )
    extracted_without_chunks = sorted(
        str(record.get("source_record_id") or "")
        for record in expected_records
        if record.get("status") == "extracted" and int(record.get("chunk_count") or 0) <= 0
    )
    extracted_without_text = sorted(
        str(record.get("source_record_id") or "")
        for record in expected_records
        if record.get("status") == "extracted" and int(record.get("text_char_count") or 0) <= 0
    )
    validation = _read_json_if_exists(validation_path)
    status = "not_started"
    if manifest_path.exists() or chunks_path.exists() or validation_path.exists():
        if (
            not missing_source_ids
            and not nonterminal_source_ids
            and not extracted_without_chunks
            and not extracted_without_text
        ):
            status = "ready_with_blockers" if blocked_records else "ready"
        else:
            status = "partial"
    reuse_inventory = _reuse_inventory_readiness(
        path=reuse_inventory_path,
        expected_source_ids=expected_source_ids,
        expected_source_set_id=source_set_id,
    )
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
        "extraction_summary": summary or None,
        "chunks_path": str(chunks_path),
        "chunks_exists": chunks_path.exists(),
        "manifest_record_count_for_expected_sources": len(expected_records),
        "status_counts": dict(status_counts),
        "extracted_source_record_count": status_counts.get("extracted", 0),
        "blocked_source_record_count": len(blocked_records),
        "blocked_status_counts": dict(blocked_status_counts),
        "blocker_error_class_counts": {
            key: count for key, count in blocker_error_class_counts.items() if key
        },
        "blocked_source_record_ids_sample": [
            str(record.get("source_record_id") or "") for record in blocked_records[:20]
        ],
        "expected_source_record_count": len(expected_source_ids),
        "coverage_complete": not missing_source_ids
        and not nonterminal_source_ids
        and not extracted_without_chunks
        and not extracted_without_text,
        "missing_source_record_count": len(missing_source_ids),
        "missing_source_record_ids_sample": missing_source_ids[:20],
        "nonterminal_source_record_ids": nonterminal_source_ids[:20],
        "extracted_without_chunks_source_record_ids": extracted_without_chunks[:20],
        "extracted_without_text_source_record_ids": extracted_without_text[:20],
        "reuse_inventory": reuse_inventory,
    }


def _retrieval_readiness(
    *,
    output_dir: Path,
    source_set_id: str,
    register: R1ForestPlanDocumentRegister,
    expected_source_ids: set[str],
) -> dict[str, Any]:
    derived_dir = output_dir / "derived" / source_set_id if source_set_id else output_dir / "derived"
    diagnostics_dir = derived_dir / "diagnostics"
    retrieval_dir = derived_dir / "retrieval"
    index_path = retrieval_dir / "evidence_index.sqlite"
    validation_path = retrieval_dir / "retrieval_validation.json"
    summary_path = retrieval_dir / "summary.json"
    eval_path = retrieval_dir / "retrieval_eval_results.json"
    extraction_manifest_path = diagnostics_dir / "extraction_manifest.jsonl"
    validation = _read_json_if_exists(validation_path)
    eval_results = _read_json_if_exists(eval_path)
    manifest_records = _read_jsonl_if_exists(extraction_manifest_path)
    extracted_source_ids = {
        str(record.get("source_record_id") or "")
        for record in manifest_records
        if str(record.get("source_record_id") or "") in expected_source_ids
        and str(record.get("status") or "") == "extracted"
    }
    indexed_source_ids = _retrieval_index_source_ids(index_path, expected_source_ids)
    missing_indexed_extracted_source_ids = sorted(extracted_source_ids - indexed_source_ids)
    upstream_blocked_source_ids = sorted(expected_source_ids - extracted_source_ids)
    coverage_by_unit = _retrieval_coverage_by_unit(
        register=register,
        expected_source_ids=expected_source_ids,
        extracted_source_ids=extracted_source_ids,
        indexed_source_ids=indexed_source_ids,
    )
    started = index_path.exists() or validation_path.exists() or summary_path.exists() or eval_path.exists()
    status = "not_started"
    if started:
        validation_passed = bool(validation.get("passed"))
        eval_passed = bool(eval_results.get("passed"))
        if validation_passed and eval_passed and not missing_indexed_extracted_source_ids:
            status = "ready_with_blockers" if upstream_blocked_source_ids else "ready"
        else:
            status = "partial"
    return {
        "started": started,
        "status": status,
        "source_set_id": source_set_id or None,
        "index_path": str(index_path),
        "index_exists": index_path.exists(),
        "retrieval_validation_path": str(validation_path),
        "retrieval_validation_exists": validation_path.exists(),
        "retrieval_validation_passed": bool(validation.get("passed")),
        "retrieval_summary_path": str(summary_path),
        "retrieval_summary_exists": summary_path.exists(),
        "retrieval_summary": _read_json_if_exists(summary_path) or None,
        "retrieval_eval_path": str(eval_path),
        "retrieval_eval_exists": eval_path.exists(),
        "retrieval_eval_passed": bool(eval_results.get("passed")),
        "retrieval_eval_query_count": int(eval_results.get("query_count") or 0),
        "retrieval_eval_failed_case_ids": [
            str(case.get("id") or "")
            for case in (eval_results.get("cases") or [])
            if not case.get("passed")
        ],
        "expected_source_record_count": len(expected_source_ids),
        "expected_extracted_source_record_count": len(extracted_source_ids),
        "indexed_source_record_count_for_expected_sources": len(indexed_source_ids),
        "missing_indexed_extracted_source_record_ids": missing_indexed_extracted_source_ids[:20],
        "upstream_blocked_source_record_ids": upstream_blocked_source_ids[:20],
        "document_role_counts": coverage_by_unit["document_role_counts"],
        "forest_units": coverage_by_unit["forest_units"],
    }


def _retrieval_index_source_ids(index_path: Path, expected_source_ids: set[str]) -> set[str]:
    if not index_path.exists():
        return set()
    try:
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT source_record_id FROM chunks WHERE source_record_id IS NOT NULL"
            ).fetchall()
    except sqlite3.Error:
        return set()
    return {
        str(row[0] or "")
        for row in rows
        if str(row[0] or "") in expected_source_ids
    }


def _retrieval_coverage_by_unit(
    *,
    register: R1ForestPlanDocumentRegister,
    expected_source_ids: set[str],
    extracted_source_ids: set[str],
    indexed_source_ids: set[str],
) -> dict[str, Any]:
    document_role_counts = Counter()
    extracted_role_counts = Counter()
    indexed_role_counts = Counter()
    rows_by_unit = defaultdict(list)
    for row in register.rows:
        if (
            row["draft_status"] == "source_delta_required"
            and row["proposed_source_record_id"] in expected_source_ids
        ):
            rows_by_unit[row["forest_unit_id"]].append(row)
            document_role_counts[row["document_role"]] += 1
            if row["proposed_source_record_id"] in extracted_source_ids:
                extracted_role_counts[row["document_role"]] += 1
            if row["proposed_source_record_id"] in indexed_source_ids:
                indexed_role_counts[row["document_role"]] += 1

    forest_units = []
    for forest_unit_id, rows in sorted(rows_by_unit.items()):
        forest_units.append(
            {
                "forest_unit_id": forest_unit_id,
                "expected_source_record_count": len(rows),
                "expected_extracted_source_record_count": sum(
                    1 for row in rows if row["proposed_source_record_id"] in extracted_source_ids
                ),
                "indexed_source_record_count": sum(
                    1 for row in rows if row["proposed_source_record_id"] in indexed_source_ids
                ),
                "document_role_counts": dict(Counter(row["document_role"] for row in rows)),
                "extracted_document_role_counts": dict(
                    Counter(
                        row["document_role"]
                        for row in rows
                        if row["proposed_source_record_id"] in extracted_source_ids
                    )
                ),
                "indexed_document_role_counts": dict(
                    Counter(
                        row["document_role"]
                        for row in rows
                        if row["proposed_source_record_id"] in indexed_source_ids
                    )
                ),
                "missing_indexed_extracted_source_record_ids": [
                    row["proposed_source_record_id"]
                    for row in rows
                    if row["proposed_source_record_id"] in extracted_source_ids
                    and row["proposed_source_record_id"] not in indexed_source_ids
                ][:20],
            }
        )

    return {
        "document_role_counts": {
            "expected": dict(document_role_counts),
            "extracted": dict(extracted_role_counts),
            "indexed": dict(indexed_role_counts),
        },
        "forest_units": forest_units,
    }


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


def _retrieval_eval_passed_check(retrieval_readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "source_delta_retrieval_eval_passed",
        "passed": bool(retrieval_readiness.get("retrieval_eval_passed")),
        "details": {
            "retrieval_eval_exists": bool(retrieval_readiness.get("retrieval_eval_exists")),
            "retrieval_eval_path": retrieval_readiness.get("retrieval_eval_path"),
            "retrieval_eval_query_count": retrieval_readiness.get("retrieval_eval_query_count"),
            "retrieval_eval_failed_case_ids": retrieval_readiness.get(
                "retrieval_eval_failed_case_ids"
            )
            or [],
        },
    }


def _reuse_inventory_readiness(
    *,
    path: Path | None,
    expected_source_ids: set[str],
    expected_source_set_id: str,
) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "status": "not_provided"}

    inventory_dir = path if path.is_dir() else path.parent
    inventory_path = None
    records_path = None
    summary_path = None
    if path.is_dir():
        inventory_path = path / "reuse_inventory.json"
        records_path = path / "reuse_inventory_records.jsonl"
        summary_path = path / "summary.json"
    elif path.name == "reuse_inventory.json":
        inventory_path = path
        records_path = inventory_dir / "reuse_inventory_records.jsonl"
        summary_path = inventory_dir / "summary.json"
    elif path.name == "reuse_inventory_records.jsonl":
        records_path = path
        inventory_path = inventory_dir / "reuse_inventory.json"
        summary_path = inventory_dir / "summary.json"
    elif path.name == "summary.json":
        summary_path = path
        inventory_path = inventory_dir / "reuse_inventory.json"
        records_path = inventory_dir / "reuse_inventory_records.jsonl"
    else:
        inventory_path = path
        records_path = inventory_dir / "reuse_inventory_records.jsonl"
        summary_path = inventory_dir / "summary.json"

    inventory = _read_json_if_exists(inventory_path) if inventory_path else {}
    summary = _read_json_if_exists(summary_path) if summary_path else {}
    records = _read_jsonl_if_exists(records_path) if records_path else []
    expected_records = [
        record
        for record in records
        if str(record.get("source_record_id") or "") in expected_source_ids
    ]
    record_ids = {str(record.get("source_record_id") or "") for record in expected_records}
    classification_counts = Counter(
        str(record.get("classification") or "") for record in expected_records
    )
    status = "ready"
    if not (inventory_path and inventory_path.exists()) and not (records_path and records_path.exists()):
        status = "missing"
    elif expected_source_ids - record_ids:
        status = "partial"
    return {
        "path": str(path),
        "exists": bool(path.exists()),
        "status": status,
        "inventory_path": str(inventory_path) if inventory_path else None,
        "inventory_exists": bool(inventory_path and inventory_path.exists()),
        "records_path": str(records_path) if records_path else None,
        "records_exists": bool(records_path and records_path.exists()),
        "summary_path": str(summary_path) if summary_path else None,
        "summary_exists": bool(summary_path and summary_path.exists()),
        "source_set_id": summary.get("source_set_id")
        or (inventory.get("summary") or {}).get("source_set_id"),
        "source_set_id_matches_extraction_source_set": (
            summary.get("source_set_id")
            or (inventory.get("summary") or {}).get("source_set_id")
            or expected_source_set_id
        )
        == expected_source_set_id,
        "record_count_for_expected_sources": len(expected_records),
        "missing_source_record_ids": sorted(expected_source_ids - record_ids)[:20],
        "classification_counts": {key: count for key, count in classification_counts.items() if key},
    }


def _forest_profile_readiness(
    *,
    register: R1ForestPlanDocumentRegister,
    forest_plan_profiles_path: Path,
    scoped_catalog_ids: set[str],
    merged_catalog_ids: set[str],
    canonical_catalog_ids: set[str],
    output_dir: Path,
    source_set_id: str,
) -> dict[str, Any]:
    collection = load_forest_plan_profiles(forest_plan_profiles_path)
    configured_profiles = {
        profile.forest_unit_id: profile for profile in collection.profiles
    }
    configured_profile_ids = sorted(configured_profiles)
    rows_by_unit = defaultdict(list)
    rows_by_source_id = {}
    for row in register.rows:
        rows_by_unit[row["forest_unit_id"]].append(row)
        rows_by_source_id[row["proposed_source_record_id"]] = row

    catalog_surfaces_by_source_id: dict[str, set[str]] = defaultdict(set)
    for source_id in scoped_catalog_ids:
        catalog_surfaces_by_source_id[source_id].add("scoped_source_delta_catalog")
    for source_id in merged_catalog_ids:
        catalog_surfaces_by_source_id[source_id].add("merged_source_delta_catalog")
    for source_id in canonical_catalog_ids:
        catalog_surfaces_by_source_id[source_id].add("active_canonical_catalog")

    extraction_manifest_path = (
        output_dir / "derived" / source_set_id / "diagnostics" / "extraction_manifest.jsonl"
        if source_set_id
        else output_dir / "derived" / "diagnostics" / "extraction_manifest.jsonl"
    )
    retrieval_index_path = (
        output_dir / "derived" / source_set_id / "retrieval" / "evidence_index.sqlite"
        if source_set_id
        else output_dir / "derived" / "retrieval" / "evidence_index.sqlite"
    )
    extraction_manifest_records = _read_jsonl_if_exists(extraction_manifest_path)
    extraction_records_by_source_id = {
        str(record.get("source_record_id") or ""): record for record in extraction_manifest_records
    }
    indexed_source_ids = _retrieval_index_all_source_ids(retrieval_index_path)

    tracked_forest_unit_ids = sorted(set(register.forest_unit_ids) | set(configured_profile_ids))
    profile_rows = []
    for forest_unit_id in tracked_forest_unit_ids:
        profile = configured_profiles.get(forest_unit_id)
        register_rows = sorted(
            rows_by_unit.get(forest_unit_id, []),
            key=lambda row: (row["document_role"], row["proposed_source_record_id"]),
        )
        source_requirements = []
        seen_source_ids = set()

        if profile is not None:
            for role, source_record in sorted(
                profile.supporting_source_record_ids_by_role.items(),
                key=lambda item: item[0],
            ):
                source_id = source_record.source_record_id
                source_requirements.append(
                    _forest_profile_source_requirement(
                        forest_unit_id=forest_unit_id,
                        role=role,
                        required_for=source_record.required_for,
                        source_record_id=source_id,
                        required_readiness=role in profile.required_readiness_source_roles,
                        register_row=rows_by_source_id.get(source_id),
                        catalog_surfaces=sorted(catalog_surfaces_by_source_id.get(source_id, set())),
                        extraction_record=extraction_records_by_source_id.get(source_id),
                        indexed_source_ids=indexed_source_ids,
                    )
                )
                seen_source_ids.add(source_id)

        for row in register_rows:
            source_id = row["proposed_source_record_id"]
            if source_id in seen_source_ids:
                continue
            source_requirements.append(
                _forest_profile_source_requirement(
                    forest_unit_id=forest_unit_id,
                    role=row["document_role"],
                    required_for=row["required_for"],
                    source_record_id=source_id,
                    required_readiness=False,
                    register_row=row,
                    catalog_surfaces=sorted(catalog_surfaces_by_source_id.get(source_id, set())),
                    extraction_record=extraction_records_by_source_id.get(source_id),
                    indexed_source_ids=indexed_source_ids,
                )
            )
            seen_source_ids.add(source_id)

        requirement_status_counts = Counter(
            requirement["readiness_status"] for requirement in source_requirements
        )
        blocker_types = sorted(
            {
                blocker
                for requirement in source_requirements
                for blocker in requirement["blocker_types"]
            }
        )
        blocker_source_record_ids = sorted(
            {
                requirement["source_record_id"]
                for requirement in source_requirements
                if requirement["blocker_types"] and requirement["source_record_id"]
            }
        )
        ready_required_count = sum(
            1
            for requirement in source_requirements
            if requirement["required_readiness"]
            and requirement["readiness_status"] == "retrieval_ready"
        )
        required_count = sum(
            1 for requirement in source_requirements if requirement["required_readiness"]
        )
        retrieval_ready_count = sum(
            1
            for requirement in source_requirements
            if requirement["readiness_status"] == "retrieval_ready"
        )
        profile_rows.append(
            {
                "forest_unit_id": forest_unit_id,
                "forest_unit_names": _forest_profile_unit_names(
                    forest_unit_id=forest_unit_id,
                    profile=profile,
                    register_rows=register_rows,
                ),
                "configured_profile": profile is not None,
                "profile_kind": "configured_profile" if profile is not None else "register_tracking_only",
                "profile_readiness_status": "ready" if not blocker_types else "blocked",
                "active_plan_source_record_id": (
                    profile.active_plan_source_record_id if profile is not None else None
                ),
                "required_source_record_count": required_count,
                "required_retrieval_ready_count": ready_required_count,
                "source_requirement_count": len(source_requirements),
                "retrieval_ready_source_record_count": retrieval_ready_count,
                "readiness_status_counts": dict(requirement_status_counts),
                "blocker_types": blocker_types,
                "blocker_source_record_ids": blocker_source_record_ids,
                "register_status_counts": dict(Counter(row["draft_status"] for row in register_rows)),
                "source_requirements": source_requirements,
            }
        )

    configured_rows = [row for row in profile_rows if row["configured_profile"]]
    tracking_only_rows = [row for row in profile_rows if not row["configured_profile"]]
    ready_profile_ids = sorted(
        row["forest_unit_id"]
        for row in configured_rows
        if row["profile_readiness_status"] == "ready"
    )
    blocked_profile_ids = sorted(
        row["forest_unit_id"]
        for row in configured_rows
        if row["profile_readiness_status"] != "ready"
    )
    ready_tracking_only_ids = sorted(
        row["forest_unit_id"]
        for row in tracking_only_rows
        if row["profile_readiness_status"] == "ready"
    )
    blocked_tracking_only_ids = sorted(
        row["forest_unit_id"]
        for row in tracking_only_rows
        if row["profile_readiness_status"] != "ready"
    )

    return {
        "status": "ready" if not blocked_profile_ids and not blocked_tracking_only_ids else "ready_with_blockers",
        "forest_plan_profiles_path": str(forest_plan_profiles_path),
        "source_set_id": source_set_id or None,
        "extraction_manifest_path": str(extraction_manifest_path),
        "extraction_manifest_exists": extraction_manifest_path.exists(),
        "retrieval_index_path": str(retrieval_index_path),
        "retrieval_index_exists": retrieval_index_path.exists(),
        "configured_profile_count": len(configured_profile_ids),
        "configured_profile_ids": configured_profile_ids,
        "tracked_forest_unit_count": len(tracked_forest_unit_ids),
        "tracked_forest_unit_ids": tracked_forest_unit_ids,
        "tracking_only_row_count": len(tracking_only_rows),
        "ready_profile_count": len(ready_profile_ids),
        "ready_profile_ids": ready_profile_ids,
        "blocked_profile_count": len(blocked_profile_ids),
        "blocked_profile_ids": blocked_profile_ids,
        "ready_tracking_only_count": len(ready_tracking_only_ids),
        "ready_tracking_only_ids": ready_tracking_only_ids,
        "blocked_tracking_only_count": len(blocked_tracking_only_ids),
        "blocked_tracking_only_ids": blocked_tracking_only_ids,
        "profile_rows": profile_rows,
    }


def _forest_profile_source_requirement(
    *,
    forest_unit_id: str,
    role: str,
    required_for: str,
    source_record_id: str,
    required_readiness: bool,
    register_row: dict[str, str] | None,
    catalog_surfaces: list[str],
    extraction_record: dict[str, Any] | None,
    indexed_source_ids: set[str],
) -> dict[str, Any]:
    register_status = (
        register_row.get("draft_status") if register_row is not None else "profile_source_missing_from_register"
    )
    readiness_status = "retrieval_ready"
    blocker_types: list[str] = []
    extraction_status = None
    extraction_error_class = None

    if register_status == "profile_source_missing_from_register":
        readiness_status = "profile_source_missing_from_register"
        blocker_types = ["missing_register_row"]
    elif register_status == "official_source_gap_documented":
        readiness_status = "official_source_gap"
        blocker_types = ["official_source_gap"]
    elif source_record_id in indexed_source_ids:
        readiness_status = "retrieval_ready"
    elif extraction_record is not None:
        extraction_status = str(extraction_record.get("status") or "")
        failure = extraction_record.get("failure") or {}
        extraction_error_class = str(failure.get("error_class") or "") or None
        if extraction_status == "extracted":
            readiness_status = "extracted_not_retrieval_ready"
            blocker_types = ["retrieval_gap"]
        elif extraction_status in {
            "parser_error",
            "parser_timeout",
            "empty_text",
            "artifact_missing",
            "hash_mismatch",
            "no_artifact",
        }:
            readiness_status = "extraction_blocked"
            blocker_types = ["extraction_blocked"]
        else:
            readiness_status = "extraction_pending"
            blocker_types = ["extraction_pending"]
    elif catalog_surfaces:
        readiness_status = (
            "captured_source_delta"
            if register_status == "source_delta_required"
            else "catalog_confirmed"
        )
        blocker_types = ["downstream_readiness_pending"]
    elif register_status == "source_delta_required":
        readiness_status = "source_delta_capture_missing"
        blocker_types = ["catalog_capture_missing"]
    else:
        readiness_status = "catalog_confirmed_missing_from_catalog"
        blocker_types = ["catalog_missing"]

    return {
        "forest_unit_id": forest_unit_id,
        "role": role,
        "required_for": required_for,
        "source_record_id": source_record_id,
        "required_readiness": required_readiness,
        "register_status": register_status,
        "catalog_surfaces": catalog_surfaces,
        "readiness_status": readiness_status,
        "extraction_status": extraction_status,
        "extraction_error_class": extraction_error_class,
        "retrieval_ready": source_record_id in indexed_source_ids,
        "blocker_types": blocker_types,
        "readiness_tier": register_row.get("readiness_tier") if register_row is not None else None,
        "notes": register_row.get("notes") if register_row is not None else None,
    }


def _forest_profile_unit_names(
    *,
    forest_unit_id: str,
    profile: Any,
    register_rows: list[dict[str, str]],
) -> list[str]:
    if profile is not None:
        return list(profile.forest_unit_names)
    names = []
    for row in register_rows:
        name = str(row.get("forest_unit_name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names or [forest_unit_id]


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


def _retrieval_index_all_source_ids(index_path: Path) -> set[str]:
    if not index_path.exists():
        return set()
    try:
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT source_record_id FROM chunks WHERE source_record_id IS NOT NULL"
            ).fetchall()
    except sqlite3.Error:
        return set()
    return {str(row[0] or "") for row in rows if str(row[0] or "")}


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
        f"- Official-source gap evidence: `{report['official_source_gap_evidence']['path']}`",
        f"- Scoped source-delta source set: `{report['scoped_source_delta_catalog']['source_set_id']}`",
        (
            f"- Merged source-delta source set: "
            f"`{report['merged_source_delta_catalog']['source_set_id']}`"
        )
        if report.get("merged_source_delta_catalog")
        else "- Merged source-delta source set: `not_evaluated`",
        f"- Active canonical source set: `{report['active_canonical_catalog']['source_set_id']}`",
        f"- Extraction source set: `{report['extraction_readiness']['source_set_id']}`",
        f"- Extraction readiness: `{report['extraction_readiness']['status']}`",
        f"- Retrieval readiness: `{report['retrieval_readiness']['status']}`",
        f"- Retrieval eval passed: `{str(report['retrieval_readiness']['retrieval_eval_passed']).lower()}`",
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
            "## Forest-Profile Readiness",
            "",
        ]
    )
    for unit in report["forest_profile_readiness"]["profile_rows"]:
        blockers = ", ".join(
            f"`{item}`" for item in unit["blocker_source_record_ids"]
        ) or "`none`"
        summary_lines.append(
            "- "
            + f"`{unit['forest_unit_id']}`: "
            + f"status=`{unit['profile_readiness_status']}`, "
            + f"retrieval_ready=`{unit['retrieval_ready_source_record_count']}/{unit['source_requirement_count']}`, "
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
