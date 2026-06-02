from __future__ import annotations

import json
from pathlib import Path

from .artifact_utils import _dict
from .artifact_utils import _read_json
from .draft_generation import MANIFEST_FILENAME as DRAFT_GENERATION_MANIFEST_FILENAME
from .draft_generation import PACKAGE_FILENAME as DRAFT_GENERATION_PACKAGE_FILENAME
from .draft_generation import VALIDATION_FILENAME as DRAFT_GENERATION_VALIDATION_FILENAME
from .draft_generation import _semantic_sha256_for_artifact
from .ea_consistency_decision_support import DEFAULT_CONFIG_PATH as DECISION_SUPPORT_CONFIG_PATH
from .ea_consistency_decision_support import (
    DEFAULT_EXPECTED_SUMMARY_PATH as DECISION_SUPPORT_EXPECTED_SUMMARY_PATH,
)
from .final_qa_certification import VALIDATION_FILENAME as FINAL_QA_VALIDATION_FILENAME
from .forest_plan_component_eval import FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_forest_plan_gates import (
    forest_plan_matrix_required as _forest_plan_matrix_required,
)
from .phase_eval_forest_plan_gates import (
    read_forest_plan_context_summary as _read_forest_plan_context_summary,
)
from .phase_eval_optional_phases import _applicability_arbitration_summary
from .phase_eval_optional_phases import _applicability_phase_gates
from .phase_eval_optional_phases import _decision_support_phase
from .phase_eval_optional_phases import _final_qa_certification_phase
from .phase_eval_optional_phases import _gold_rule_pack_match_mode
from .phase_eval_optional_phases import _knowledge_graph_phase
from .phase_eval_optional_phases import _read_applicability_phase_artifacts
from .phase_eval_optional_phases import _review_packet_index_phase
from .phase_eval_support import _current_queue_item_count
from .phase_eval_support import _failed_check_names
from .phase_eval_support import _phase
from .phase_eval_support import _safe_int
from .phase_eval_support import _sha256_file
from .review_packet_index import VALIDATION_FILENAME as REVIEW_PACKET_VALIDATION_FILENAME


COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"
DRAFT_GENERATION_EVAL_FILENAME = "draft_generation_eval_results.json"
KNOWLEDGE_GRAPH_REVIEW_PHASE = "n" "epa_3d_review_graph"
REPO_ROOT = Path(__file__).resolve().parents[2]


def build_review_scoped_phases(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str | None,
    review_dir: Path | None,
    authority_universe_path: Path | None,
    package_fact_graph_path: Path | None,
    package_fact_graph_validation_path: Path | None,
    applicability_retrieval_trace_path: Path | None,
    applicability_graph_trace_path: Path | None,
    applicability_trace_diagnostics_path: Path | None,
    applicability_decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    search_coverage_certificates_path: Path | None,
    applicability_validation_path: Path | None,
    generated_rule_pack_path: Path | None,
    generated_rule_pack_validation_path: Path | None,
    review_knowledge_graph_validation: dict | None,
    review_knowledge_graph_validation_path: Path | None,
    review_knowledge_graph_summary: dict | None,
    review_knowledge_graph_summary_path: Path | None,
    compliance_validation: dict | None,
    compliance_validation_path: Path | None,
    compliance_review: dict | None,
    compliance_review_path: Path | None,
    compliance_matrix: dict | None,
    compliance_matrix_path: Path | None,
    compliance_matrix_pdf_path: Path | None,
    component_adjudication_eval: dict | None,
    component_adjudication_eval_path: Path | None,
    component_eval: dict | None,
    component_eval_path: Path | None,
    component_queue: dict | None,
    component_queue_path: Path | None,
    component_adjudication_file_path: Path | None,
    compliance_coverage: dict | None,
    compliance_coverage_path: Path,
    compliance_gold_eval: dict | None,
    compliance_gold_eval_path: Path,
    rule_claim_summary: dict | None,
    decision_support_dir: Path | None,
    draft_generation_dir: Path | None,
    review_packet_index_dir: Path | None,
    final_qa_dir: Path | None,
) -> list[dict]:
    if review_dir is None:
        return []
    resolved_review_id = review_id or review_dir.name
    applicability_artifacts = _read_applicability_phase_artifacts(
        authority_universe_path=authority_universe_path,
        package_fact_graph_path=package_fact_graph_path,
        package_fact_graph_validation_path=package_fact_graph_validation_path,
        applicability_retrieval_trace_path=applicability_retrieval_trace_path,
        applicability_graph_trace_path=applicability_graph_trace_path,
        applicability_trace_diagnostics_path=applicability_trace_diagnostics_path,
        applicability_decisions_path=applicability_decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
        applicability_validation_path=applicability_validation_path,
        generated_rule_pack_path=generated_rule_pack_path,
        generated_rule_pack_validation_path=generated_rule_pack_validation_path,
    )
    applicability_arbitration_summary = _applicability_arbitration_summary(
        applicability_artifacts.get("decisions") or []
    )
    phases = _applicability_phase_gates(
        output_dir=output_dir,
        review_dir=review_dir,
        source_set_id=source_set_id,
        artifacts=applicability_artifacts,
        arbitration_summary=applicability_arbitration_summary,
    )
    if review_knowledge_graph_validation is not None or review_knowledge_graph_summary is not None:
        phases.append(
            _knowledge_graph_phase(
                KNOWLEDGE_GRAPH_REVIEW_PHASE,
                validation=review_knowledge_graph_validation,
                summary=review_knowledge_graph_summary,
                validation_path=review_knowledge_graph_validation_path,
                summary_path=review_knowledge_graph_summary_path,
                expected_source_set_id=source_set_id,
                expected_review_id=review_id,
            )
        )
    compliance_summary = (compliance_review or {}).get("summary", {})
    if compliance_coverage is not None:
        coverage_source_set_id = compliance_coverage.get("source_set_id")
        coverage_source_set_matches = coverage_source_set_id == source_set_id
        rule_claim_rule_pack_id = (rule_claim_summary or {}).get("rule_pack_id")
        rule_claim_rule_pack_version = (rule_claim_summary or {}).get("rule_pack_version")
        coverage_rule_pack_matches = (
            compliance_coverage.get("rule_pack_id") == rule_claim_rule_pack_id
            and compliance_coverage.get("rule_pack_version") == rule_claim_rule_pack_version
        )
        coverage_passed = bool(compliance_coverage.get("passed"))
        coverage_phase_passed = (
            coverage_passed and coverage_source_set_matches and coverage_rule_pack_matches
        )
        phases.append(
            _phase(
                "compliance_coverage",
                passed=coverage_phase_passed,
                reviewer_ready=bool(
                    coverage_phase_passed and compliance_coverage.get("reviewer_ready")
                ),
                details={
                    "coverage_path": str(compliance_coverage_path),
                    "coverage_passed": coverage_passed,
                    "coverage_reviewer_ready": bool(compliance_coverage.get("reviewer_ready")),
                    "expected_source_set_id": source_set_id,
                    "coverage_source_set_id": coverage_source_set_id,
                    "source_set_matches": coverage_source_set_matches,
                    "expected_rule_pack_id": rule_claim_rule_pack_id,
                    "expected_rule_pack_version": rule_claim_rule_pack_version,
                    "rule_pack_id": compliance_coverage.get("rule_pack_id"),
                    "rule_pack_version": compliance_coverage.get("rule_pack_version"),
                    "rule_pack_matches": coverage_rule_pack_matches,
                    "rule_count": compliance_coverage.get("rule_count", 0),
                    "coverage_item_count": compliance_coverage.get("coverage_item_count", 0),
                    "eval_case_count": compliance_coverage.get("eval_case_count", 0),
                    "rule_claim_link_count": compliance_coverage.get("rule_claim_link_count", 0),
                    "rules_without_coverage_items": compliance_coverage.get(
                        "rules_without_coverage_items",
                        [],
                    ),
                    "rules_without_eval_cases": compliance_coverage.get(
                        "rules_without_eval_cases",
                        [],
                    ),
                    "rules_without_source_claim_links": compliance_coverage.get(
                        "rules_without_source_claim_links",
                        [],
                    ),
                    "source_record_mismatch_rule_ids": compliance_coverage.get(
                        "source_record_mismatch_rule_ids",
                        [],
                    ),
                    "source_claim_term_mismatch_rule_ids": compliance_coverage.get(
                        "source_claim_term_mismatch_rule_ids",
                        [],
                    ),
                },
            )
        )
    if compliance_gold_eval is not None:
        gold_source_set_id = compliance_gold_eval.get("source_set_id")
        gold_source_set_matches = gold_source_set_id == source_set_id
        rule_claim_rule_pack_id = (rule_claim_summary or {}).get("rule_pack_id")
        rule_claim_rule_pack_version = (rule_claim_summary or {}).get("rule_pack_version")
        generated_rule_pack = applicability_artifacts.get("generated_rule_pack") or {}
        gold_rule_pack_match_mode = _gold_rule_pack_match_mode(
            gold_eval=compliance_gold_eval,
            expected_rule_pack_id=rule_claim_rule_pack_id,
            expected_rule_pack_version=rule_claim_rule_pack_version,
            generated_rule_pack=generated_rule_pack,
        )
        gold_rule_pack_matches = bool(gold_rule_pack_match_mode)
        gold_passed = bool(compliance_gold_eval.get("passed"))
        gold_promotion_ready = bool(compliance_gold_eval.get("promotion_ready"))
        gold_effective_promotion_ready = gold_promotion_ready or (
            gold_rule_pack_match_mode == "generated_base" and gold_passed
        )
        gold_phase_passed = gold_passed and gold_source_set_matches and gold_rule_pack_matches
        gold_failed_checks = []
        if not gold_passed:
            gold_failed_checks.append("gold_eval_failed")
        if not gold_effective_promotion_ready:
            gold_failed_checks.append("gold_eval_not_promotion_ready")
        if not gold_source_set_matches:
            gold_failed_checks.append("source_set_mismatch")
        if not gold_rule_pack_matches:
            gold_failed_checks.append("rule_pack_mismatch")
        phases.append(
            _phase(
                "compliance_gold_eval",
                passed=gold_phase_passed,
                reviewer_ready=bool(gold_phase_passed and gold_effective_promotion_ready),
                details={
                    "gold_eval_path": str(compliance_gold_eval_path),
                    "gold_eval_id": compliance_gold_eval.get("gold_eval_id"),
                    "gold_eval_version": compliance_gold_eval.get("gold_eval_version"),
                    "gold_passed": gold_passed,
                    "promotion_ready": gold_promotion_ready,
                    "effective_promotion_ready": gold_effective_promotion_ready,
                    "failed_checks": gold_failed_checks,
                    "expected_source_set_id": source_set_id,
                    "gold_source_set_id": gold_source_set_id,
                    "source_set_matches": gold_source_set_matches,
                    "expected_rule_pack_id": rule_claim_rule_pack_id,
                    "expected_rule_pack_version": rule_claim_rule_pack_version,
                    "rule_pack_id": compliance_gold_eval.get("rule_pack_id"),
                    "rule_pack_version": compliance_gold_eval.get("rule_pack_version"),
                    "rule_pack_matches": gold_rule_pack_matches,
                    "rule_pack_match_mode": gold_rule_pack_match_mode,
                    "generated_base_rule_pack_id": generated_rule_pack.get("base_rule_pack_id"),
                    "generated_base_rule_pack_version": generated_rule_pack.get(
                        "base_rule_pack_version"
                    ),
                    "case_count": compliance_gold_eval.get("case_count", 0),
                    "adjudicated_case_count": compliance_gold_eval.get(
                        "adjudicated_case_count",
                        0,
                    ),
                    "passed_case_count": compliance_gold_eval.get("passed_case_count", 0),
                    "failed_case_count": compliance_gold_eval.get("failed_case_count", 0),
                    "profile_counts": compliance_gold_eval.get("profile_counts", {}),
                    "required_profiles_present": compliance_gold_eval.get(
                        "required_profiles_present",
                        [],
                    ),
                    "compliance_review_eval_path": compliance_gold_eval.get(
                        "compliance_review_eval_path"
                    ),
                },
            )
        )
    compliance_source_set_id = compliance_summary.get("source_set_id")
    source_set_matches = compliance_source_set_id == source_set_id
    review_id_matches = review_id is None or compliance_summary.get("review_id") == review_id
    compliance_review_exists = compliance_review is not None
    compliance_validation_passed = bool(compliance_validation and compliance_validation.get("passed"))
    matrix_summary = (compliance_matrix or {}).get("summary", {})
    matrix_rule_pack = (compliance_matrix or {}).get("rule_pack", {})
    matrix_forest_plan = (compliance_matrix or {}).get("forest_plan_compliance") or {}
    matrix_forest_plan_summary = matrix_forest_plan.get("summary", {})
    forest_plan_context_summary = _read_forest_plan_context_summary(review_dir)
    forest_plan_summary = (
        matrix_summary.get("forest_plan_review")
        or compliance_summary.get("forest_plan_review")
        or forest_plan_context_summary
        or {}
    )
    forest_plan_component_evaluation = forest_plan_summary.get("component_evaluation") or {}
    forest_plan_matrix_required = _forest_plan_matrix_required(
        forest_plan_summary=forest_plan_summary,
        component_evaluation=forest_plan_component_evaluation,
    )
    forest_plan_matrix_exists = bool(matrix_forest_plan)
    expected_standard_count = int(
        forest_plan_component_evaluation.get("applicable_standard_count") or 0
    )
    forest_plan_matrix_schema_matches = (
        not forest_plan_matrix_required
        or matrix_forest_plan.get("schema_version") == "forest-plan-compliance-matrix-v0"
    )
    forest_plan_matrix_rows_visible = (
        not forest_plan_matrix_required
        or (
            forest_plan_matrix_exists
            and (
                expected_standard_count == 0
                or int(matrix_forest_plan_summary.get("row_count") or 0) > 0
            )
        )
    )
    forest_plan_matrix_standards_visible = (
        not forest_plan_matrix_required
        or expected_standard_count == 0
        or int(matrix_forest_plan_summary.get("applicable_standard_row_count") or 0)
        >= expected_standard_count
    )
    compliance_matrix_exists = compliance_matrix is not None
    compliance_matrix_pdf_exists = (
        compliance_matrix_pdf_path is not None and compliance_matrix_pdf_path.exists()
    )
    compliance_matrix_pdf_valid = (
        compliance_matrix_pdf_exists
        and compliance_matrix_pdf_path.stat().st_size > 0
        and compliance_matrix_pdf_path.read_bytes().startswith(b"%PDF-")
    )
    matrix_checks = {
        "matrix_exists": compliance_matrix_exists,
        "matrix_pdf_exists": compliance_matrix_pdf_exists,
        "matrix_pdf_header_valid": compliance_matrix_pdf_valid,
        "matrix_schema_matches": (compliance_matrix or {}).get("schema_version")
        == COMPLIANCE_MATRIX_SCHEMA_VERSION,
        "matrix_review_id_matches": (compliance_matrix or {}).get("review_id")
        == compliance_summary.get("review_id"),
        "matrix_source_set_matches": (compliance_matrix or {}).get("source_set_id")
        == compliance_source_set_id,
        "matrix_rule_pack_matches": matrix_rule_pack.get("rule_pack_id")
        == compliance_summary.get("rule_pack_id")
        and matrix_rule_pack.get("version") == compliance_summary.get("rule_pack_version"),
        "matrix_row_count_matches": matrix_summary.get("row_count")
        == compliance_summary.get("finding_count"),
        "matrix_status_counts_match": matrix_summary.get("status_counts")
        == compliance_summary.get("finding_status_counts"),
        "forest_plan_matrix_schema_matches": forest_plan_matrix_schema_matches,
        "forest_plan_matrix_rows_visible": forest_plan_matrix_rows_visible,
        "forest_plan_matrix_standards_visible": forest_plan_matrix_standards_visible,
    }
    compliance_matrix_passed = all(matrix_checks.values())
    compliance_phase_passed = (
        compliance_review_exists
        and compliance_validation_passed
        and source_set_matches
        and review_id_matches
        and compliance_matrix_passed
    )
    phases.append(
        _phase(
            "compliance_review",
            passed=compliance_phase_passed,
            reviewer_ready=bool(
                compliance_phase_passed and compliance_summary.get("reviewer_ready")
            ),
            details={
                "review_dir": str(review_dir),
                "review_id": compliance_summary.get("review_id") or review_id,
                "validation_path": str(compliance_validation_path),
                "review_path": str(compliance_review_path),
                "matrix_path": str(compliance_matrix_path),
                "matrix_pdf_path": str(compliance_matrix_pdf_path),
                "review_exists": compliance_review_exists,
                "matrix_exists": compliance_matrix_exists,
                "matrix_pdf_exists": compliance_matrix_pdf_exists,
                "matrix_pdf_header_valid": compliance_matrix_pdf_valid,
                "forest_plan_matrix_required": forest_plan_matrix_required,
                "forest_plan_matrix_exists": forest_plan_matrix_exists,
                "forest_plan_matrix_row_count": matrix_forest_plan_summary.get(
                    "row_count",
                    0,
                ),
                "forest_plan_matrix_applicable_standard_row_count": matrix_forest_plan_summary.get(
                    "applicable_standard_row_count",
                    0,
                ),
                "forest_plan_expected_applicable_standard_count": expected_standard_count,
                "validation_passed": compliance_validation_passed,
                "reviewer_ready": bool(compliance_summary.get("reviewer_ready")),
                "expected_source_set_id": source_set_id,
                "review_source_set_id": compliance_source_set_id,
                "source_set_matches": source_set_matches,
                "review_id_matches": review_id_matches,
                "failed_validation_checks": _failed_check_names(compliance_validation),
                "failed_artifact_checks": sorted(
                    name for name, passed in matrix_checks.items() if not passed
                ),
                **matrix_checks,
                "rule_pack_id": compliance_summary.get("rule_pack_id"),
                "rule_pack_version": compliance_summary.get("rule_pack_version"),
                "finding_count": compliance_summary.get("finding_count", 0),
                "finding_status_counts": compliance_summary.get(
                    "finding_status_counts",
                    {},
                ),
            },
        )
    )
    if component_eval is not None:
        component_eval_summary = (
            component_eval.get("summary")
            if isinstance(component_eval, dict) and isinstance(component_eval.get("summary"), dict)
            else {}
        )
        component_eval_schema_version = (
            component_eval.get("schema_version") if isinstance(component_eval, dict) else None
        ) or component_eval_summary.get("schema_version")
        component_eval_review_id = component_eval_summary.get("review_id")
        component_eval_source_set_id = component_eval_summary.get("source_set_id")
        expected_component_eval_review_id = review_id or compliance_summary.get("review_id")
        component_eval_passed = bool(component_eval_summary.get("passed"))
        component_eval_schema_matches = (
            component_eval_schema_version == FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
        )
        component_eval_source_set_matches = component_eval_source_set_id == source_set_id
        component_eval_review_id_matches = (
            expected_component_eval_review_id is None
            or component_eval_review_id == expected_component_eval_review_id
        )
        component_eval_failed_checks = []
        if not component_eval_schema_matches:
            component_eval_failed_checks.append("schema_version_mismatch")
        if not component_eval_passed:
            component_eval_failed_checks.append("component_eval_failed")
        if not component_eval_source_set_matches:
            component_eval_failed_checks.append("source_set_mismatch")
        if not component_eval_review_id_matches:
            component_eval_failed_checks.append("review_id_mismatch")
        component_eval_phase_passed = (
            component_eval_schema_matches
            and component_eval_passed
            and component_eval_source_set_matches
            and component_eval_review_id_matches
        )
        phases.append(
            _phase(
                "forest_plan_component_eval",
                passed=component_eval_phase_passed,
                reviewer_ready=component_eval_phase_passed,
                details={
                    "review_dir": str(review_dir),
                    "eval_path": str(component_eval_path),
                    "schema_version": component_eval_schema_version,
                    "schema_version_matches": component_eval_schema_matches,
                    "eval_passed": component_eval_passed,
                    "failed_checks": component_eval_failed_checks,
                    "expected_source_set_id": source_set_id,
                    "component_eval_source_set_id": component_eval_source_set_id,
                    "source_set_matches": component_eval_source_set_matches,
                    "expected_review_id": expected_component_eval_review_id,
                    "component_eval_review_id": component_eval_review_id,
                    "review_id_matches": component_eval_review_id_matches,
                    "case_count": component_eval_summary.get("case_count", 0),
                    "passed_case_count": component_eval_summary.get("passed_case_count", 0),
                    "failed_case_count": component_eval_summary.get("failed_case_count", 0),
                    "metrics": component_eval_summary.get("metrics", {}),
                    "failure_category_counts": component_eval_summary.get(
                        "failure_category_counts",
                        {},
                    ),
                },
            )
        )
    should_include_component_adjudication = bool(
        component_adjudication_eval_path is not None and component_adjudication_eval_path.exists()
    ) or bool(
        component_adjudication_file_path is not None
        and component_adjudication_file_path.exists()
    )
    if should_include_component_adjudication:
        adjudication_summary = (
            component_adjudication_eval.get("summary")
            if isinstance(component_adjudication_eval, dict)
            and isinstance(component_adjudication_eval.get("summary"), dict)
            else {}
        )
        adjudication_review_id = (component_adjudication_eval or {}).get("review_id") or adjudication_summary.get(
            "review_id"
        )
        adjudication_source_set_id = (component_adjudication_eval or {}).get(
            "source_set_id"
        ) or adjudication_summary.get("source_set_id")
        expected_adjudication_review_id = review_id or compliance_summary.get("review_id")
        adjudication_eval_exists = component_adjudication_eval is not None
        adjudication_eval_passed = bool(adjudication_summary.get("passed"))
        adjudication_source_set_matches = adjudication_source_set_id == source_set_id
        adjudication_review_id_matches = (
            expected_adjudication_review_id is None
            or adjudication_review_id == expected_adjudication_review_id
        )
        current_queue_count = (
            _current_queue_item_count(component_queue) if component_queue is not None else None
        )
        adjudication_queue_count = _safe_int(adjudication_summary.get("queue_item_count"))
        adjudication_queue_matches_current = (
            current_queue_count is None or adjudication_queue_count == current_queue_count
        )
        adjudication_failed_checks = []
        if not adjudication_eval_exists:
            adjudication_failed_checks.append("adjudication_eval_missing")
        if adjudication_eval_exists and not adjudication_eval_passed:
            adjudication_failed_checks.append("adjudication_eval_failed")
        if adjudication_eval_exists and not adjudication_source_set_matches:
            adjudication_failed_checks.append("source_set_mismatch")
        if adjudication_eval_exists and not adjudication_review_id_matches:
            adjudication_failed_checks.append("review_id_mismatch")
        if adjudication_eval_exists and not adjudication_queue_matches_current:
            adjudication_failed_checks.append("queue_item_count_mismatch")
        adjudication_phase_passed = (
            adjudication_eval_exists
            and adjudication_eval_passed
            and adjudication_source_set_matches
            and adjudication_review_id_matches
            and adjudication_queue_matches_current
        )
        phases.append(
            _phase(
                "forest_plan_component_adjudication",
                passed=adjudication_phase_passed,
                reviewer_ready=adjudication_phase_passed,
                details={
                    "review_dir": str(review_dir),
                    "eval_path": str(component_adjudication_eval_path),
                    "adjudication_file": (
                        adjudication_summary.get("adjudication_file")
                        or str(component_adjudication_file_path)
                    ),
                    "eval_exists": adjudication_eval_exists,
                    "eval_passed": adjudication_eval_passed,
                    "failed_checks": adjudication_failed_checks,
                    "expected_source_set_id": source_set_id,
                    "adjudication_source_set_id": adjudication_source_set_id,
                    "source_set_matches": adjudication_source_set_matches,
                    "expected_review_id": expected_adjudication_review_id,
                    "adjudication_review_id": adjudication_review_id,
                    "review_id_matches": adjudication_review_id_matches,
                    "queue_item_count": adjudication_summary.get("queue_item_count", 0),
                    "current_queue_item_count": current_queue_count,
                    "queue_item_count_matches_current": adjudication_queue_matches_current,
                    "adjudication_item_count": adjudication_summary.get(
                        "adjudication_item_count",
                        0,
                    ),
                    "resolved_adjudication_count": adjudication_summary.get(
                        "resolved_adjudication_count",
                        0,
                    ),
                    "pending_adjudication_count": adjudication_summary.get(
                        "pending_adjudication_count",
                        0,
                    ),
                    "real_ea_omission_count": adjudication_summary.get(
                        "real_ea_omission_count",
                        0,
                    ),
                    "system_miss_count": adjudication_summary.get("system_miss_count", 0),
                    "adjudication_completion_rate": adjudication_summary.get(
                        "adjudication_completion_rate",
                        0,
                    ),
                    "real_ea_omission_rate": adjudication_summary.get(
                        "real_ea_omission_rate",
                        0,
                    ),
                    "system_miss_rate": adjudication_summary.get("system_miss_rate", 0),
                    "adjudication_expectation_match_rate": adjudication_summary.get(
                        "adjudication_expectation_match_rate",
                        0,
                    ),
                    "adjudication_outcome_counts": adjudication_summary.get(
                        "adjudication_outcome_counts",
                        {},
                    ),
                    "disposition_counts": adjudication_summary.get("disposition_counts", {}),
                    "real_ea_omission_disposition_counts": adjudication_summary.get(
                        "real_ea_omission_disposition_counts",
                        {},
                    ),
                    "system_miss_disposition_counts": adjudication_summary.get(
                        "system_miss_disposition_counts",
                        {},
                    ),
                    "failure_category_counts": adjudication_summary.get(
                        "failure_category_counts",
                        {},
                    ),
                },
            )
        )
    if _should_include_decision_support_phase(
        review_id=resolved_review_id,
        decision_support_dir=decision_support_dir,
    ):
        phases.append(
            _decision_support_phase(
                output_dir=output_dir,
                review_id=resolved_review_id,
                decision_support_dir=decision_support_dir,
            )
        )
    if _should_include_draft_generation_phase(
        review_id=resolved_review_id,
        draft_generation_dir=draft_generation_dir,
    ):
        phases.append(
            _draft_generation_phase(
                review_id=resolved_review_id,
                source_set_id=source_set_id,
                draft_generation_dir=draft_generation_dir or review_dir / "draft_generation",
            )
        )
    if review_packet_index_dir is not None and _should_include_review_packet_index_phase(
        review_packet_index_dir
    ):
        phases.append(
            _review_packet_index_phase(
                review_id=resolved_review_id,
                source_set_id=source_set_id,
                review_dir=review_dir,
                review_packet_index_dir=review_packet_index_dir,
            )
        )
    if final_qa_dir is not None and _should_include_final_qa_phase(final_qa_dir):
        phases.append(
            _final_qa_certification_phase(
                output_dir=output_dir,
                review_id=resolved_review_id,
                source_set_id=source_set_id,
                final_qa_dir=final_qa_dir,
            )
        )
    return phases


def _should_include_decision_support_phase(
    *,
    review_id: str | None,
    decision_support_dir: Path | None,
) -> bool:
    if decision_support_dir is not None and decision_support_dir.exists():
        return True
    if not review_id:
        return False
    for path in (DECISION_SUPPORT_CONFIG_PATH, DECISION_SUPPORT_EXPECTED_SUMMARY_PATH):
        if not path.exists():
            continue
        try:
            payload = _read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if payload.get("review_id") == review_id:
            return True
    return False


def _should_include_final_qa_phase(final_qa_dir: Path) -> bool:
    return (final_qa_dir / FINAL_QA_VALIDATION_FILENAME).exists()


def _should_include_review_packet_index_phase(review_packet_index_dir: Path) -> bool:
    return (review_packet_index_dir / REVIEW_PACKET_VALIDATION_FILENAME).exists()


def _should_include_draft_generation_phase(
    *,
    review_id: str | None,
    draft_generation_dir: Path | None,
) -> bool:
    if draft_generation_dir is not None and draft_generation_dir.exists():
        return True
    if not review_id:
        return False
    config_path = REPO_ROOT / "config" / "draft_generation_v1.json"
    if not config_path.exists():
        return False
    try:
        payload = _read_json(config_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return payload.get("review_id") == review_id


def _resolve_repo_relative_path(value: str | None) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _draft_generation_phase(
    *,
    review_id: str,
    source_set_id: str,
    draft_generation_dir: Path,
) -> dict:
    validation_path = draft_generation_dir / DRAFT_GENERATION_VALIDATION_FILENAME
    eval_path = draft_generation_dir / DRAFT_GENERATION_EVAL_FILENAME
    manifest_path = draft_generation_dir / DRAFT_GENERATION_MANIFEST_FILENAME
    package_path = draft_generation_dir / DRAFT_GENERATION_PACKAGE_FILENAME
    validation = _read_json(validation_path) if validation_path.exists() else None
    evaluation = _read_json(eval_path) if eval_path.exists() else None
    manifest = _read_json(manifest_path) if manifest_path.exists() else None
    package = _read_json(package_path) if package_path.exists() else None
    validation_summary = _dict((validation or {}).get("summary"))
    eval_summary = _dict((evaluation or {}).get("summary"))
    manifest_input_artifacts = [
        artifact
        for artifact in (manifest or {}).get("input_artifacts", [])
        if isinstance(artifact, dict)
    ]
    stale_input_artifacts = []
    for artifact in manifest_input_artifacts:
        artifact_path = _resolve_repo_relative_path(str(artifact.get("artifact_path") or ""))
        expected_sha256 = str(artifact.get("sha256") or "")
        if artifact_path is None or not artifact_path.exists() or not expected_sha256:
            continue
        actual_sha256 = _sha256_file(artifact_path)
        if actual_sha256 != expected_sha256:
            semantic_sha256_matches = False
            expected_semantic_sha256 = str(artifact.get("semantic_sha256") or "")
            artifact_key = str(artifact.get("artifact_key") or "")
            if artifact_path.suffix == ".json" and expected_semantic_sha256:
                actual_payload = _read_json(artifact_path)
                actual_semantic_sha256 = _semantic_sha256_for_artifact(
                    artifact_key=artifact_key,
                    payload=actual_payload,
                )
                semantic_sha256_matches = actual_semantic_sha256 == expected_semantic_sha256
            if semantic_sha256_matches:
                continue
            stale_input_artifacts.append(
                {
                    "artifact_key": artifact_key,
                    "artifact_path": str(artifact_path),
                    "expected_sha256": expected_sha256,
                    "actual_sha256": actual_sha256,
                    "expected_semantic_sha256": expected_semantic_sha256 or None,
                }
            )
    package_summary = _dict((package or {}).get("summary"))
    checks = {
        "validation_exists": validation is not None,
        "eval_exists": evaluation is not None,
        "manifest_exists": manifest is not None,
        "package_exists": package is not None,
        "validation_schema_matches": (validation or {}).get("schema_version")
        == "draft-generation-validation-v1",
        "eval_schema_matches": (evaluation or {}).get("schema_version")
        == "draft-generation-eval-results-v1",
        "manifest_schema_matches": (manifest or {}).get("schema_version")
        == "draft-generation-manifest-v1",
        "package_schema_matches": (package or {}).get("schema_version")
        == "draft-generation-package-v1",
        "validation_review_id_matches": (validation or {}).get("review_id") == review_id,
        "eval_review_id_matches": (evaluation or {}).get("review_id") == review_id,
        "manifest_review_id_matches": (manifest or {}).get("review_id") == review_id,
        "package_review_id_matches": (package or {}).get("review_id") == review_id,
        "validation_source_set_matches": (validation or {}).get("source_set_id") == source_set_id,
        "eval_source_set_matches": (evaluation or {}).get("source_set_id") == source_set_id,
        "manifest_source_set_matches": (manifest or {}).get("source_set_id") == source_set_id,
        "package_source_set_matches": (package or {}).get("source_set_id") == source_set_id,
        "validation_passed": validation_summary.get("passed") is True,
        "eval_passed": eval_summary.get("passed") is True,
        "eval_live_validation_present": eval_summary.get("live_validation_present") is True,
        "eval_live_validation_passed": eval_summary.get("live_validation_passed") is True,
        "manifest_validation_passed": (manifest or {}).get("validation_passed") is True,
        "manifest_input_artifacts_fresh": not stale_input_artifacts,
        "ready_section_count_positive": int(package_summary.get("ready_section_count") or 0) > 0,
        "paragraph_count_positive": int(package_summary.get("paragraph_count") or 0) > 0,
    }
    passed = all(checks.values())
    return _phase(
        "draft_generation_defensibility",
        passed=passed,
        reviewer_ready=passed,
        details={
            "results_dir": str(draft_generation_dir),
            "validation_path": str(validation_path),
            "eval_path": str(eval_path),
            "manifest_path": str(manifest_path),
            "package_path": str(package_path),
            "failed_checks": sorted(name for name, ok in checks.items() if not ok),
            "stale_input_artifacts": stale_input_artifacts,
            "ready_section_count": package_summary.get("ready_section_count", 0),
            "paragraph_count": package_summary.get("paragraph_count", 0),
            "warning_section_count": package_summary.get("warning_section_count", 0),
            "refusal_count": package_summary.get("refusal_count", 0),
            "eval_case_count": eval_summary.get("case_count", 0),
            "eval_passed_case_count": eval_summary.get("passed_case_count", 0),
            **checks,
        },
    )
