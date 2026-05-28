from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .final_qa_certification_common import _add_check
from .final_qa_certification_common import _safe_int
from .final_qa_certification_common import _selector_value
from .final_qa_certification_common import _summary_or_self


_REVIEW_PACKET_SELF_REFERENCE_ALLOWED_CHECKS = {
    "decision_support_authority_rows_match_applicability",
    "final_qa_authority_rows_match_applicability",
    "final_qa_report_exists_and_parses",
}


def _phase_eval_counts_for_packet(phase_eval: Any) -> dict[str, int]:
    live_phase_count = _safe_int(_selector_value(phase_eval, "phase_count"))
    live_passed_phase_count = _safe_int(_selector_value(phase_eval, "passed_phase_count"))
    phases = phase_eval.get("phases", []) if isinstance(phase_eval, Mapping) else []
    final_qa_phase_present_count = int(
        any(
            isinstance(phase, Mapping)
            and phase.get("name") == "final_qa_certification_report"
            for phase in phases
        )
    )
    final_qa_phase_passed_count = int(
        any(
            isinstance(phase, Mapping)
            and phase.get("name") == "final_qa_certification_report"
            and phase.get("passed")
            for phase in phases
        )
    )
    phase_count = live_phase_count - final_qa_phase_present_count
    passed_phase_count = live_passed_phase_count - final_qa_phase_passed_count
    return {
        "phase_count": phase_count,
        "passed_phase_count": passed_phase_count,
        "live_phase_count": live_phase_count,
        "live_passed_phase_count": live_passed_phase_count,
        "final_qa_self_reference_phase_count": final_qa_phase_present_count,
    }


def _promotion_suite_counts_for_packet(promotion: Any) -> dict[str, int]:
    live_required_count = _safe_int(
        _selector_value(promotion, "required_current_result_count")
    )
    live_passed_count = _safe_int(
        _selector_value(promotion, "passed_required_current_result_count")
    )
    final_qa_counts = (
        _final_qa_current_result_counts(promotion)
        if isinstance(promotion, Mapping)
        else {"required": 0, "passed": 0}
    )
    return {
        "required_current_result_count": max(
            live_required_count - final_qa_counts["required"],
            0,
        ),
        "passed_required_current_result_count": max(
            live_passed_count - final_qa_counts["passed"],
            0,
        ),
        "live_required_current_result_count": live_required_count,
        "live_passed_required_current_result_count": live_passed_count,
        "final_qa_current_result_count": final_qa_counts["required"],
        "final_qa_current_passed_result_count": final_qa_counts["passed"],
    }


def _derive_actual_counts(
    data_by_key: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    decision = data_by_key.get("decision_support_report", {})
    compliance = data_by_key.get("compliance_review", {})
    matrix = data_by_key.get("compliance_matrix", {})
    applicability = data_by_key.get("applicability_validation", {})
    component_eval = data_by_key.get("forest_plan_component_eval_results", {})
    phase_eval = data_by_key.get("phase_eval", {})
    promotion = data_by_key.get("promotion_suite", {})
    v1_eval = data_by_key.get("v1_ea_eval", {})
    review_packet_validation = data_by_key.get("review_packet_index_validation", {})
    review_packet_inventory = data_by_key.get("review_packet_row_inventory", {})
    render_manifest = data_by_key.get("compliance_matrix_render_manifest", {})
    phase_eval_counts = _phase_eval_counts_for_packet(phase_eval)
    promotion_counts = _promotion_suite_counts_for_packet(promotion)

    compliance_summary = _summary_or_self(compliance)
    applicability_summary = _summary_or_self(applicability)
    component_eval_summary = _summary_or_self(component_eval)
    matrix_summary = matrix.get("summary", {}) if isinstance(matrix, dict) else {}
    forest_components = (
        _selector_value(matrix_summary, "forest_plan_review.component_evaluation")
        or _selector_value(compliance, "forest_plan_review.component_evaluation")
        or {}
    )
    conditional = v1_eval.get("conditional_adjudication", {}) if isinstance(v1_eval, dict) else {}
    authority_integration = (
        _selector_value(matrix_summary, "authority_integration")
        or _selector_value(compliance, "authority_integration")
        or {}
    )
    review_packet_summary = (
        _selector_value(review_packet_validation, "summary")
        or _selector_value(review_packet_inventory, "summary")
        or {}
    )
    render_manifest_summary = (
        render_manifest.get("summary", {}) if isinstance(render_manifest, Mapping) else {}
    )

    counts = {
        "package_file_count": _selector_value(
            decision,
            "record_and_artifact_inventory.package_file_count",
        ),
        "package_chunk_count": _selector_value(
            decision,
            "record_and_artifact_inventory.package_chunk_count",
        ),
        "baseline_source_record_count": _selector_value(
            compliance_summary,
            "baseline_source_record_count",
        ),
        "candidate_authority_count": applicability_summary.get("candidate_authority_count"),
        "applicable_authority_count": applicability_summary.get("applicable_authority_count"),
        "non_applicable_authority_count": applicability_summary.get("non_applicable_authority_count"),
        "unresolved_authority_count": applicability_summary.get("unresolved_authority_count"),
        "generated_rule_count": _selector_value(
            data_by_key.get("generated_rule_pack_validation", {}),
            "summary.generated_rule_count",
        ),
        "authority_finding_count": _selector_value(compliance_summary, "finding_count"),
        "authority_finding_status_counts": _selector_value(
            compliance_summary,
            "finding_status_counts",
        ),
        "rule_claim_link_count": _selector_value(compliance_summary, "rule_claim_link_count"),
        "rule_claim_gap_count": _selector_value(compliance_summary, "rule_claim_gap_count"),
        "compliance_matrix_authority_row_count": _selector_value(matrix_summary, "row_count"),
        "forest_plan_component_count": forest_components.get("component_count"),
        "forest_plan_supported_component_count": forest_components.get("supported_count"),
        "forest_plan_not_applicable_component_count": forest_components.get(
            "not_applicable_count"
        ),
        "forest_plan_gap_count": forest_components.get("gap_count"),
        "forest_plan_standard_count": forest_components.get("standard_count"),
        "applicable_standard_count": forest_components.get("applicable_standard_count"),
        "applied_standard_count": forest_components.get("applied_standard_count"),
        "forest_plan_component_eval_case_count": component_eval_summary.get("case_count"),
        "phase_eval_phase_count": phase_eval_counts["phase_count"],
        "phase_eval_passed_phase_count": phase_eval_counts["passed_phase_count"],
        "phase_eval_live_phase_count": phase_eval_counts["live_phase_count"],
        "phase_eval_live_passed_phase_count": phase_eval_counts[
            "live_passed_phase_count"
        ],
        "phase_eval_final_qa_self_reference_phase_count": phase_eval_counts[
            "final_qa_self_reference_phase_count"
        ],
        "promotion_suite_required_current_result_count": promotion_counts[
            "required_current_result_count"
        ],
        "promotion_suite_passed_required_current_result_count": promotion_counts[
            "passed_required_current_result_count"
        ],
        "promotion_suite_live_required_current_result_count": promotion_counts[
            "live_required_current_result_count"
        ],
        "promotion_suite_live_passed_required_current_result_count": promotion_counts[
            "live_passed_required_current_result_count"
        ],
        "promotion_suite_final_qa_current_result_count": promotion_counts[
            "final_qa_current_result_count"
        ],
        "promotion_suite_final_qa_current_passed_result_count": promotion_counts[
            "final_qa_current_passed_result_count"
        ],
        "accepted_v1_risk_count": conditional.get("accepted_pending_count") or 0,
        "actual_pending_applicable_count": conditional.get("actual_pending_applicable_count")
        or 0,
        "litigation_risk_legal_conclusion_count": authority_integration.get(
            "legal_conclusion_count"
        ),
        "review_packet_index_applicable_authority_count": review_packet_summary.get(
            "applicable_authority_count"
        ),
        "review_packet_index_non_applicable_authority_count": review_packet_summary.get(
            "non_applicable_authority_count"
        ),
        "review_packet_index_forest_plan_component_row_count": review_packet_summary.get(
            "forest_plan_component_row_count"
        ),
        "review_packet_index_applicable_standard_count": review_packet_summary.get(
            "applicable_standard_count"
        ),
        "review_packet_index_render_manifest_authority_row_count": render_manifest_summary.get(
            "authority_row_count"
        ),
        "review_packet_index_render_manifest_forest_plan_row_count": (
            render_manifest_summary.get("forest_plan_row_count")
        ),
        "review_packet_index_validation_failed_check_count": review_packet_summary.get(
            "failed_check_count"
        ),
    }
    missing = sorted(key for key, value in counts.items() if value is None)
    _add_check(
        checks,
        name="source_counts_derived_from_artifacts",
        passed=not missing,
        category="count_drift",
        details={"missing_count_fields": missing},
    )
    return counts


def _validate_actual_counts(
    actual_counts: Mapping[str, Any],
    config: Mapping[str, Any],
    data_by_key: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> None:
    review_packet_validation = data_by_key.get("review_packet_index_validation")
    for row in config.get("required_count_fields", []):
        field = row["field"]
        actual = _selector_value(actual_counts, field) if "." in field else actual_counts.get(field)
        self_reference_allowed = (
            field == "review_packet_index_validation_failed_check_count"
            and row["expected"] == 0
            and isinstance(actual, int)
            and actual >= 0
            and _review_packet_index_self_reference_allowed(review_packet_validation)
        )
        _add_check(
            checks,
            name=f"source_count_matches_{field}",
            passed=actual == row["expected"] or self_reference_allowed,
            category=row.get("failure_category", "count_drift"),
            details={
                "actual": actual,
                "expected": row["expected"],
                "self_reference_allowed": self_reference_allowed,
            },
        )


def _outer_gate_hash_drift_allowed(
    *,
    artifact_key: str,
    data: Mapping[str, Any] | None,
    expected: Mapping[str, Any],
) -> bool:
    if artifact_key == "phase_eval":
        return _phase_eval_self_reference_allowed(
            data,
            expected_counts=expected.get("expected_counts", {}),
        )
    if artifact_key == "promotion_suite":
        return _promotion_suite_has_only_final_qa_outer_gates(
            data,
            expected_counts=expected.get("expected_counts", {}),
        )
    return False


def _phase_eval_has_only_final_qa_outer_gate(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    phases = data.get("phases") if isinstance(data, Mapping) else None
    if not isinstance(phases, list):
        return False
    final_qa_phases = [
        phase
        for phase in phases
        if isinstance(phase, Mapping) and phase.get("name") == "final_qa_certification_report"
    ]
    if len(final_qa_phases) != 1:
        return False
    final_qa_phase = final_qa_phases[0]
    if not final_qa_phase.get("passed") or not final_qa_phase.get("reviewer_ready"):
        return False
    expected_phase_count = _safe_int(expected_counts.get("phase_eval_phase_count"))
    expected_passed_count = _safe_int(expected_counts.get("phase_eval_passed_phase_count"))
    return (
        _safe_int(data.get("phase_count")) == expected_phase_count + 1
        and _safe_int(data.get("passed_phase_count")) == expected_passed_count + 1
        and _safe_int(data.get("reviewer_ready_phase_count")) == expected_passed_count + 1
    )


def _phase_eval_pending_only_final_qa_gate(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    phases = data.get("phases") if isinstance(data, Mapping) else None
    if not isinstance(phases, list):
        return False
    final_qa_phases = [
        phase
        for phase in phases
        if isinstance(phase, Mapping) and phase.get("name") == "final_qa_certification_report"
    ]
    if len(final_qa_phases) != 1:
        return False
    final_qa_phase = final_qa_phases[0]
    if final_qa_phase.get("passed") or final_qa_phase.get("reviewer_ready"):
        return False
    non_final_qa_phases = [
        phase
        for phase in phases
        if isinstance(phase, Mapping) and phase.get("name") != "final_qa_certification_report"
    ]
    if any(not phase.get("passed") or not phase.get("reviewer_ready") for phase in non_final_qa_phases):
        return False
    expected_phase_count = _safe_int(expected_counts.get("phase_eval_phase_count"))
    expected_passed_count = _safe_int(expected_counts.get("phase_eval_passed_phase_count"))
    return (
        _safe_int(data.get("phase_count")) == expected_phase_count + 1
        and _safe_int(data.get("passed_phase_count")) == expected_passed_count
        and _safe_int(data.get("reviewer_ready_phase_count")) == expected_passed_count
    )


def _phase_eval_self_reference_allowed(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    return _phase_eval_has_only_final_qa_outer_gate(
        data,
        expected_counts=expected_counts,
    ) or _phase_eval_pending_only_final_qa_gate(
        data,
        expected_counts=expected_counts,
    )


def _promotion_suite_has_only_final_qa_outer_gates(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    if not isinstance(data, Mapping):
        return False
    expected_required = _safe_int(
        expected_counts.get("promotion_suite_required_current_result_count")
    )
    expected_passed = _safe_int(
        expected_counts.get("promotion_suite_passed_required_current_result_count")
    )
    final_qa_counts = _final_qa_current_result_counts(data)
    if final_qa_counts["required"] != 4:
        return False
    return (
        _safe_int(data.get("required_current_result_count"))
        == expected_required + final_qa_counts["required"]
        and _safe_int(data.get("passed_required_current_result_count"))
        == expected_passed + final_qa_counts["passed"]
    )


def _current_promotion_suite_self_reference_allowed(
    *,
    gate: Mapping[str, Any],
    data: Mapping[str, Any],
    expected_counts: Mapping[str, Any],
) -> bool:
    if gate.get("gate_name") == "review_packet_index_validation":
        return _review_packet_index_self_reference_allowed(data)
    if gate.get("gate_name") == "phase_eval":
        return _phase_eval_self_reference_allowed(
            data,
            expected_counts=expected_counts,
        )
    if gate.get("gate_name") != "current_promotion_suite":
        return False
    if gate.get("required_pass_selector") != "current_promotion_ready":
        return False
    if gate.get("expected_value") is not True:
        return False
    return _promotion_suite_has_only_final_qa_outer_gates(
        data,
        expected_counts=expected_counts,
    )


def _review_packet_index_self_reference_allowed(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    failed_checks = {
        str(check.get("name") or "")
        for check in data.get("checks", [])
        if isinstance(check, Mapping) and check.get("passed") is False
    }
    return bool(failed_checks) and failed_checks <= _REVIEW_PACKET_SELF_REFERENCE_ALLOWED_CHECKS


def _final_qa_current_result_counts(data: Mapping[str, Any]) -> dict[str, int]:
    counts = {"required": 0, "passed": 0}
    for case in data.get("review_cases", []):
        if not isinstance(case, Mapping) or case.get("id") != "v1-cg-ecid":
            continue
        for result in case.get("results", []):
            if not isinstance(result, Mapping):
                continue
            result_id = str(result.get("id") or "")
            if not result_id.startswith("final_qa_certification_"):
                continue
            if result.get("required_for_current_promotion"):
                counts["required"] += 1
                if result.get("passed"):
                    counts["passed"] += 1
    return counts
