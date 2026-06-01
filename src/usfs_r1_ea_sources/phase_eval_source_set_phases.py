from __future__ import annotations

from pathlib import Path

from .artifact_utils import _dict
from .artifact_utils import _extraction_summary_is_complete
from .artifact_utils import _int_from_summary
from .artifact_utils import _read_json
from .phase_eval_optional_phases import _knowledge_graph_phase
from .phase_eval_support import _failed_check_names
from .phase_eval_support import _freshness_status
from .phase_eval_support import _phase
from .phase_eval_support import _sha256_file
from .source_register import validate_source_register


KNOWLEDGE_GRAPH_SOURCE_SET_PHASE = "n" "epa_3d_source_set_graph"
REPO_ROOT = Path(__file__).resolve().parents[2]


def build_source_set_phases(
    *,
    output_dir: Path,
    source_set_id: str,
    catalog_validation: dict | None,
    catalog_validation_path: Path,
    extraction_validation: dict | None,
    extraction_validation_path: Path,
    extraction_summary: dict | None,
    extraction_summary_path: Path,
    upstream_evaluation: dict | None,
    upstream_evaluation_path: Path,
    retrieval_validation: dict | None,
    retrieval_validation_path: Path,
    retrieval_summary: dict | None,
    retrieval_summary_path: Path,
    graph_validation: dict | None,
    graph_validation_path: Path,
    graph_summary: dict | None,
    graph_summary_path: Path,
    claim_validation: dict | None,
    claim_validation_path: Path,
    claim_summary: dict | None,
    claim_summary_path: Path,
    rule_claim_validation: dict | None,
    rule_claim_validation_path: Path,
    rule_claim_summary: dict | None,
    rule_claim_summary_path: Path,
    downstream_direct_eval_manifest: dict | None,
    downstream_direct_eval_manifest_path: Path,
    downstream_lane_results: dict[str, dict[str, object]],
    source_set_manifest: dict | None,
    catalog_rows: list[dict],
    authority_currentness_report: dict | None,
    authority_currentness_path: Path,
    extraction_accuracy: dict | None,
    extraction_accuracy_path: Path,
    knowledge_graph_validation: dict | None,
    knowledge_graph_validation_path: Path,
    knowledge_graph_summary: dict | None,
    knowledge_graph_summary_path: Path,
    semantic_graph_reports: dict[str, tuple[dict | None, Path]],
    component_retrieval_direct_eval: dict | None,
    semantic_graph_direct_eval: dict | None,
    knowledge_graph_query_direct_eval: dict | None,
    eval_context_graph_direct_eval: dict | None,
) -> list[dict]:
    phases = [
        _phase(
            "catalog_capture",
            passed=bool(catalog_validation and catalog_validation.get("passed")),
            reviewer_ready=bool(catalog_validation and catalog_validation.get("passed")),
            details={"path": str(catalog_validation_path)},
        ),
        _phase(
            "extraction",
            passed=bool(extraction_validation and extraction_validation.get("passed"))
            and _extraction_summary_is_complete(extraction_summary),
            reviewer_ready=bool(extraction_validation and extraction_validation.get("passed"))
            and _extraction_summary_is_complete(extraction_summary),
            details={
                "validation_path": str(extraction_validation_path),
                "summary_path": str(extraction_summary_path),
                "validation_passed": bool(
                    extraction_validation and extraction_validation.get("passed")
                ),
                "extraction_complete": _extraction_summary_is_complete(extraction_summary),
                "catalog_source_count": _int_from_summary(
                    extraction_summary,
                    "catalog_source_count",
                ),
                "selected_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_source_count",
                ),
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
            },
        ),
        _upstream_evaluation_phase(
            upstream_evaluation=upstream_evaluation,
            upstream_evaluation_path=upstream_evaluation_path,
        ),
        _phase(
            "retrieval",
            passed=bool(retrieval_validation and retrieval_validation.get("passed")),
            reviewer_ready=bool(retrieval_summary and retrieval_summary.get("reviewer_ready")),
            details={
                "validation_path": str(retrieval_validation_path),
                "summary_path": str(retrieval_summary_path),
                "validation_passed": bool(
                    retrieval_validation and retrieval_validation.get("passed")
                ),
                "reviewer_ready": bool(
                    retrieval_summary and retrieval_summary.get("reviewer_ready")
                ),
            },
        ),
        _phase(
            "evidence_graph",
            passed=bool(graph_validation and graph_validation.get("passed")),
            reviewer_ready=bool(graph_summary and graph_summary.get("reviewer_ready")),
            details={
                "validation_path": str(graph_validation_path),
                "summary_path": str(graph_summary_path),
                "validation_passed": bool(graph_validation and graph_validation.get("passed")),
                "reviewer_ready": bool(graph_summary and graph_summary.get("reviewer_ready")),
                "failed_validation_checks": _failed_check_names(graph_validation),
                "freshness_status": _freshness_status(graph_validation),
                "retrieval_index_path": (graph_summary or {}).get("retrieval_index_path"),
                "retrieval_index_chunk_count": (graph_summary or {}).get(
                    "retrieval_index_chunk_count",
                    0,
                ),
                "retrieval_binding_mismatch_count": (graph_summary or {}).get(
                    "retrieval_binding_mismatch_count",
                    0,
                ),
                "metrics": (graph_summary or {}).get("metrics", {}),
            },
        ),
        _phase(
            "claim_extraction",
            passed=bool(claim_validation and claim_validation.get("passed")),
            reviewer_ready=bool(claim_summary and claim_summary.get("reviewer_ready")),
            details={
                "validation_path": str(claim_validation_path),
                "summary_path": str(claim_summary_path),
                "validation_passed": bool(claim_validation and claim_validation.get("passed")),
                "reviewer_ready": bool(claim_summary and claim_summary.get("reviewer_ready")),
                "failed_validation_checks": _failed_check_names(claim_validation),
                "claims_path": (claim_summary or {}).get("claims_path"),
                "entities_path": (claim_summary or {}).get("entities_path"),
                "claim_count": (claim_summary or {}).get("claim_count", 0),
                "entity_count": (claim_summary or {}).get("entity_count", 0),
                "claim_type_counts": (claim_summary or {}).get("claim_type_counts", {}),
                "retrieval_index_path": (claim_summary or {}).get("retrieval_index_path"),
                "retrieval_binding_mismatch_count": (claim_summary or {}).get(
                    "retrieval_binding_mismatch_count",
                    0,
                ),
                "metrics": (claim_summary or {}).get("metrics", {}),
            },
        ),
        _phase(
            "rule_claim_binding",
            passed=bool(rule_claim_validation and rule_claim_validation.get("passed")),
            reviewer_ready=bool(rule_claim_summary and rule_claim_summary.get("reviewer_ready")),
            details={
                "validation_path": str(rule_claim_validation_path),
                "summary_path": str(rule_claim_summary_path),
                "validation_passed": bool(
                    rule_claim_validation and rule_claim_validation.get("passed")
                ),
                "reviewer_ready": bool(
                    rule_claim_summary and rule_claim_summary.get("reviewer_ready")
                ),
                "failed_validation_checks": _failed_check_names(rule_claim_validation),
                "links_path": (rule_claim_summary or {}).get("links_path"),
                "gaps_path": (rule_claim_summary or {}).get("gaps_path"),
                "rule_pack_id": (rule_claim_summary or {}).get("rule_pack_id"),
                "rule_pack_version": (rule_claim_summary or {}).get("rule_pack_version"),
                "rule_count": (rule_claim_summary or {}).get("rule_count", 0),
                "link_count": (rule_claim_summary or {}).get("link_count", 0),
                "gap_count": (rule_claim_summary or {}).get("gap_count", 0),
                "rules_without_links": (rule_claim_summary or {}).get(
                    "rules_without_links",
                    [],
                ),
            },
        ),
        _downstream_direct_evaluation_phase(
            manifest=downstream_direct_eval_manifest,
            manifest_path=downstream_direct_eval_manifest_path,
            output_dir=output_dir,
            source_set_id=source_set_id,
            lane_results=downstream_lane_results,
        ),
    ]
    canonical_register_phase = _source_register_contract_phase(
        source_set_id=source_set_id,
        source_set_manifest=source_set_manifest,
        catalog_rows=catalog_rows,
        authority_currentness_report=authority_currentness_report,
    )
    authority_currentness_phase = _authority_currentness_phase(
        source_set_id=source_set_id,
        report=authority_currentness_report,
        report_path=authority_currentness_path,
    )
    extraction_accuracy_phase = _extraction_accuracy_phase(
        source_set_id=source_set_id,
        report=extraction_accuracy,
        report_path=extraction_accuracy_path,
    )
    if canonical_register_phase is not None:
        phases.append(canonical_register_phase)
    if authority_currentness_phase is not None:
        phases.append(authority_currentness_phase)
    if extraction_accuracy_phase is not None:
        phases.append(extraction_accuracy_phase)
    if knowledge_graph_validation is not None or knowledge_graph_summary is not None:
        phases.append(
            _knowledge_graph_phase(
                KNOWLEDGE_GRAPH_SOURCE_SET_PHASE,
                validation=knowledge_graph_validation,
                summary=knowledge_graph_summary,
                validation_path=knowledge_graph_validation_path,
                summary_path=knowledge_graph_summary_path,
                expected_source_set_id=source_set_id,
            )
        )
    if _catalog_uses_source_register_v1(catalog_rows, source_set_id):
        semantic_phase_names = {
            "authority_ontology": "authority_ontology",
            "authority_relationships": "authority_relationships",
            "citation_aliases": "citation_aliases",
            "graph_health": "graph_health",
            "graph_accuracy": "graph_accuracy",
        }
        for phase_name, report_name in semantic_phase_names.items():
            report, report_path = semantic_graph_reports[report_name]
            phases.append(
                _semantic_graph_eval_phase(
                    phase_name,
                    report=report,
                    report_path=report_path,
                    expected_source_set_id=source_set_id,
                )
            )
        if semantic_graph_direct_eval is not None:
            phases.append(
                _phase(
                    "canonical_semantic_graph",
                    passed=True,
                    reviewer_ready=True,
                    details={
                        "results_path": semantic_graph_direct_eval.get("summary_path"),
                        "expected_source_set_id": source_set_id,
                    },
                )
            )
        if knowledge_graph_query_direct_eval is not None:
            phases.append(
                _phase(
                    "knowledge_graph_query_surface",
                    passed=True,
                    reviewer_ready=True,
                    details={
                        "results_path": knowledge_graph_query_direct_eval.get("summary_path"),
                        "expected_source_set_id": source_set_id,
                    },
                )
            )
    if eval_context_graph_direct_eval is not None:
        phases.append(
            _phase(
                "observability_eval_context_graph",
                passed=True,
                reviewer_ready=True,
                details={
                    "results_path": eval_context_graph_direct_eval.get("summary_path"),
                    "expected_source_set_id": source_set_id,
                },
            )
        )
    if component_retrieval_direct_eval is not None:
        phases.append(
            _phase(
                "forest_plan_component_retrieval",
                passed=True,
                reviewer_ready=True,
                details={
                    "results_path": component_retrieval_direct_eval.get("summary_path"),
                    "expected_source_set_id": source_set_id,
                    "required_source_set_ids": (
                        component_retrieval_direct_eval.get("details", {}).get(
                            "required_source_set_ids",
                            [],
                        )
                    ),
                },
            )
        )
    return phases


def _catalog_uses_source_register_v1(catalog_rows: list[dict], source_set_id: str) -> bool:
    return any(
        str(row.get("source_set_id") or source_set_id) == source_set_id
        and str((row.get("metadata") or {}).get("loader_contract") or "") == "source_register_v1"
        for row in catalog_rows
        if isinstance(row, dict)
    )


def _resolve_repo_relative_path(value: str | None) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _is_canonical_source_register_context(
    *,
    source_set_manifest: dict | None,
    catalog_rows: list[dict],
    authority_currentness_report: dict | None,
    source_set_id: str,
) -> bool:
    if _catalog_uses_source_register_v1(catalog_rows, source_set_id):
        return True
    summary = _dict((authority_currentness_report or {}).get("summary"))
    inventory_summary = _dict(summary.get("inventory_summary"))
    if inventory_summary.get("projection_basis") == "source_register_v1_catalog_and_queue_rows":
        return True
    workbook_path = str((source_set_manifest or {}).get("workbook_path") or "")
    return workbook_path.endswith("usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx")


def _source_register_contract_phase(
    *,
    source_set_id: str,
    source_set_manifest: dict | None,
    catalog_rows: list[dict],
    authority_currentness_report: dict | None,
) -> dict | None:
    if not _is_canonical_source_register_context(
        source_set_manifest=source_set_manifest,
        catalog_rows=catalog_rows,
        authority_currentness_report=authority_currentness_report,
        source_set_id=source_set_id,
    ):
        return None
    summary = _dict((authority_currentness_report or {}).get("summary"))
    inventory_summary = _dict(summary.get("inventory_summary"))
    workbook_path = _resolve_repo_relative_path(
        str((source_set_manifest or {}).get("workbook_path") or "")
        or str(inventory_summary.get("workbook_path") or "")
    )
    workbook_path_exists = workbook_path is not None and workbook_path.exists()
    validation_report: dict | None = None
    validation_error: str | None = None
    if workbook_path_exists and workbook_path is not None:
        try:
            validation_report = validate_source_register(workbook_path)
        except (OSError, ValueError) as exc:
            validation_error = str(exc)
    manifest_workbook_sha256 = str((source_set_manifest or {}).get("workbook_sha256") or "")
    actual_workbook_sha256 = (
        _sha256_file(workbook_path) if workbook_path_exists and workbook_path is not None else None
    )
    workbook_sha_matches_manifest = (
        not manifest_workbook_sha256 or actual_workbook_sha256 == manifest_workbook_sha256
    )
    validation_passed = bool(validation_report and validation_report.get("validation_passed"))
    failed_checks = [
        check["name"]
        for check in (validation_report or {}).get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]
    passed = bool(
        workbook_path_exists
        and validation_passed
        and workbook_sha_matches_manifest
        and (validation_report or {}).get("load_sheet_name") == "Document_Register_Master"
    )
    return _phase(
        "source_register_contract",
        passed=passed,
        reviewer_ready=passed,
        details={
            "workbook_path": str(workbook_path) if workbook_path is not None else None,
            "workbook_path_exists": workbook_path_exists,
            "manifest_workbook_sha256": manifest_workbook_sha256 or None,
            "actual_workbook_sha256": actual_workbook_sha256,
            "workbook_sha_matches_manifest": workbook_sha_matches_manifest,
            "validation_passed": validation_passed,
            "validation_error": validation_error,
            "failed_checks": failed_checks,
            "sheet_count": (validation_report or {}).get("sheet_count"),
            "load_sheet_name": (validation_report or {}).get("load_sheet_name"),
            "load_row_count": (validation_report or {}).get("load_row_count"),
            "queue_row_count": (validation_report or {}).get("queue_row_count"),
            "removed_row_count": (validation_report or {}).get("removed_row_count"),
        },
    )


def _authority_currentness_phase(
    *,
    source_set_id: str,
    report: dict | None,
    report_path: Path,
) -> dict | None:
    if report is None:
        return None
    summary = _dict(report.get("summary"))
    validation = _dict(report.get("validation"))
    summary_source_set_id = str(summary.get("source_set_id") or report.get("source_set_id") or "")
    source_set_matches = summary_source_set_id == source_set_id
    validation_passed = bool(validation.get("passed"))
    summary_validation_passed = bool(summary.get("validation_passed"))
    failed_checks = [
        check["name"]
        for check in validation.get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]
    passed = bool(source_set_matches and validation_passed and summary_validation_passed)
    return _phase(
        "authority_currentness",
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "report_present": True,
            "expected_source_set_id": source_set_id,
            "summary_source_set_id": summary_source_set_id,
            "source_set_matches": source_set_matches,
            "validation_passed": validation_passed,
            "summary_validation_passed": summary_validation_passed,
            "failed_checks": failed_checks,
            "authority_family_count": summary.get("authority_family_count", 0),
            "current_authority_source_record_count": summary.get(
                "current_authority_source_record_count",
                0,
            ),
            "documented_source_gap_count": summary.get("documented_source_gap_count", 0),
            "documented_source_non_addition_count": summary.get(
                "documented_source_non_addition_count",
                0,
            ),
            "superseded_replacement_confirmed_family_count": summary.get(
                "superseded_replacement_confirmed_family_count",
                0,
            ),
            "temporal_lineage_record_count": summary.get("temporal_lineage_record_count", 0),
        },
    )


def _extraction_accuracy_phase(
    *,
    source_set_id: str,
    report: dict | None,
    report_path: Path,
) -> dict | None:
    if report is None:
        return None
    report_source_set_id = str(report.get("source_set_id") or "")
    source_set_matches = report_source_set_id == source_set_id
    passed = bool(source_set_matches and report.get("passed") is True)
    return _phase(
        "extraction_accuracy",
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "report_present": True,
            "expected_source_set_id": source_set_id,
            "report_source_set_id": report_source_set_id,
            "source_set_matches": source_set_matches,
            "passed": bool(report.get("passed")),
            "record_count": report.get("record_count", 0),
            "audited_record_count": report.get("audited_record_count", 0),
            "audited_chunk_count": report.get("audited_chunk_count", 0),
            "knowledge_base_admitted_source_record_count": len(
                report.get("knowledge_base_admitted_source_record_ids") or []
            ),
            "knowledge_base_blocked_source_record_count": len(
                report.get("knowledge_base_blocked_source_record_ids") or []
            ),
            "failed_checks": _failed_check_names(report),
        },
    )


def load_semantic_report(*, primary_path: Path, fallback_path: Path) -> dict | None:
    if primary_path.exists():
        return _read_json(primary_path)
    if fallback_path.exists():
        return _read_json(fallback_path)
    return None


def _semantic_graph_eval_phase(
    name: str,
    *,
    report: dict | None,
    report_path: Path,
    expected_source_set_id: str,
) -> dict:
    report_present = isinstance(report, dict)
    report_source_set_id = (report or {}).get("source_set_id")
    source_set_matches = report_source_set_id == expected_source_set_id
    report_passed = bool((report or {}).get("summary", {}).get("passed"))
    failed_checks = _failed_check_names(report)
    passed = report_present and source_set_matches and report_passed and not failed_checks
    return _phase(
        name,
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "report_present": report_present,
            "expected_source_set_id": expected_source_set_id,
            "source_set_id": report_source_set_id,
            "source_set_matches": source_set_matches,
            "report_passed": report_passed,
            "failed_checks": failed_checks,
        },
    )


def _downstream_direct_evaluation_phase(
    *,
    manifest: dict | None,
    manifest_path: Path,
    output_dir: Path,
    source_set_id: str,
    lane_results: dict[str, dict[str, object]],
) -> dict:
    required_lanes = manifest.get("required_lanes", []) if isinstance(manifest, dict) else []
    manifest_ok = (
        isinstance(manifest, dict)
        and manifest.get("schema_version") == "downstream-direct-eval-v1"
        and isinstance(required_lanes, list)
        and bool(required_lanes)
    )
    lane_summaries = [
        _downstream_lane_summary(
            lane=lane,
            manifest_path=manifest_path,
            output_dir=output_dir,
            source_set_id=source_set_id,
            lane_result=lane_results.get(str(lane.get("lane_id") or ""), {}),
        )
        for lane in required_lanes
        if isinstance(lane, dict)
    ]
    passed = manifest_ok and all(
        summary.get("status") == "direct_eval_present" for summary in lane_summaries
    )
    return _phase(
        "downstream_direct_evaluation",
        passed=passed,
        reviewer_ready=passed,
        details={
            "manifest_path": str(manifest_path),
            "manifest_present": manifest is not None,
            "manifest_schema_version": (manifest or {}).get("schema_version"),
            "lane_statuses": {
                str(summary.get("lane_id") or ""): str(summary.get("status") or "")
                for summary in lane_summaries
            },
            "failed_lane_ids": [
                str(summary.get("lane_id") or "")
                for summary in lane_summaries
                if summary.get("status") != "direct_eval_present"
            ],
            "lane_summaries": lane_summaries,
        },
    )


def _downstream_lane_summary(
    *,
    lane: dict,
    manifest_path: Path,
    output_dir: Path,
    source_set_id: str,
    lane_result: dict[str, object],
) -> dict:
    lane_id = str(lane.get("lane_id") or "")
    contract_path = _resolve_manifest_contract_path(manifest_path, lane.get("contract_path"))
    result = lane_result.get("result")
    result_path = (
        Path(str(lane_result.get("result_path"))) if lane_result.get("result_path") else None
    )
    present = isinstance(result, dict)
    expected_contract_sha = _sha256_file(contract_path) if contract_path.exists() else None
    actual_contract_sha = ((result or {}).get("contract") or {}).get("sha256") if present else None
    source_set_matches = (
        present and str((result or {}).get("source_set_id") or "") == source_set_id
    )
    eval_id_matches = present and str((result or {}).get("eval_id") or "") == str(
        lane.get("eval_id") or ""
    )
    contract_sha_matches = present and expected_contract_sha == actual_contract_sha
    result_passed = bool(present and (result or {}).get("passed"))
    if not present:
        status = "direct_eval_missing"
    elif not source_set_matches or not eval_id_matches or not contract_sha_matches:
        status = "direct_eval_stale"
    elif not result_passed:
        status = "direct_eval_failed"
    else:
        status = "direct_eval_present"
    return {
        "lane_id": lane_id,
        "register_rows": lane.get("register_rows", []),
        "status": status,
        "result_path": str(result_path) if result_path is not None else None,
        "present": present,
        "result_passed": result_passed,
        "expected_eval_id": lane.get("eval_id"),
        "actual_eval_id": (result or {}).get("eval_id") if present else None,
        "expected_source_set_id": source_set_id,
        "actual_source_set_id": (result or {}).get("source_set_id") if present else None,
        "source_set_matches": bool(source_set_matches),
        "contract_path": str(contract_path),
        "expected_contract_sha256": expected_contract_sha,
        "actual_contract_sha256": actual_contract_sha,
        "contract_sha_matches": bool(contract_sha_matches),
        "checks": (result or {}).get("checks", []) if present else [],
    }


def _resolve_manifest_contract_path(manifest_path: Path, value: object | None) -> Path:
    if not value:
        return manifest_path
    path = Path(str(value))
    return path if path.is_absolute() else manifest_path.parent / path


def _upstream_evaluation_phase(
    *,
    upstream_evaluation: dict | None,
    upstream_evaluation_path: Path,
) -> dict:
    lane_statuses = {
        str(lane.get("lane_id") or ""): str(lane.get("status") or "")
        for lane in (upstream_evaluation or {}).get("lane_summaries", [])
        if isinstance(lane, dict)
    }
    passed = bool(upstream_evaluation and upstream_evaluation.get("passed"))
    return _phase(
        "upstream_evaluation",
        passed=passed,
        reviewer_ready=passed,
        details={
            "path": str(upstream_evaluation_path),
            "present": upstream_evaluation is not None,
            "schema_version": (upstream_evaluation or {}).get("schema_version"),
            "lane_statuses": lane_statuses,
            "failed_case_ids": (upstream_evaluation or {}).get("failed_case_ids", []),
        },
    )
