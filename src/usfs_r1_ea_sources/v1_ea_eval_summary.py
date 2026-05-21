from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .v1_ea_eval_forest_plan import _forest_plan_component_adjudication_summary
from .v1_ea_eval_forest_plan import _pending_reviewer_resolution_count
from .v1_ea_eval_forest_plan import _pending_standard_reviewer_resolution_count
from .v1_ea_eval_forest_plan import _reviewer_resolution_count
from .v1_ea_eval_forest_plan import _reviewer_resolution_count_by_component_type
from .v1_ea_eval_support import FOREST_PLAN_ARTIFACTS
from .v1_ea_eval_support import FOREST_PLAN_VALIDATION_CHECKS
from .v1_ea_eval_support import _contract_identity
from .v1_ea_eval_support import _identity_matches_contract
from .v1_ea_eval_support import _normalized_expected_lane_states
from .v1_ea_eval_support import _review_identity
from .v1_ea_eval_support import _string_list


def _checks(
    *,
    contract: dict[str, Any],
    review_dir: Path,
    artifacts: dict[str, Any],
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    identity = _review_identity(
        artifacts["compliance_review"],
        artifacts.get("generated_rule_pack"),
    )
    validation = artifacts["compliance_validation"]
    return [
        {
            "name": "eval_contract_valid",
            "passed": True,
            "details": {"eval_id": contract.get("eval_id")},
        },
        {
            "name": "review_artifacts_loaded",
            "passed": not artifacts["artifact_errors"],
            "details": {"artifact_errors": artifacts["artifact_errors"]},
        },
        {
            "name": "review_identity_matches_contract",
            "passed": _identity_matches_contract(contract, identity, review_dir),
            "details": {"contract": _contract_identity(contract), "review": identity},
        },
        {
            "name": "compliance_validation_passed",
            "passed": bool(validation.get("passed", False)),
            "details": {
                "path": artifacts["artifact_paths"].get("compliance_validation"),
                "failed_checks": [
                    check.get("name")
                    for check in validation.get("checks", [])
                    if not check.get("passed")
                ],
            },
        },
        _authority_explanation_paths_check(artifacts),
        {
            "name": "required_sections_detected",
            "passed": all(result["passed"] for result in section_results),
            "details": _check_counts(section_results),
        },
        {
            "name": "baseline_source_documents_match_authority",
            "passed": all(result["passed"] for result in baseline_results),
            "details": _check_counts(baseline_results),
        },
        {
            "name": "rule_source_section_expectations_met",
            "passed": all(result["passed"] for result in rule_results),
            "details": _check_counts(rule_results),
        },
        {
            "name": "conditional_source_expectations_met",
            "passed": all(result["passed"] for result in conditional_results),
            "details": _check_counts(conditional_results),
        },
        {
            "name": "conditional_adjudication_policy_met",
            "passed": bool(conditional_adjudication.get("passed")),
            "details": {
                key: value
                for key, value in conditional_adjudication.items()
                if key != "pending_results"
            },
        },
        {
            "name": "forest_plan_expectations_met",
            "passed": all(result["passed"] for result in forest_plan_results),
            "details": _check_counts(forest_plan_results),
        },
    ]


def _authority_explanation_paths_check(artifacts: dict[str, Any]) -> dict[str, Any]:
    payload = artifacts.get("authority_explanation_paths") or {}
    summary = payload.get("summary") or {}
    finding_rows = payload.get("finding_explanation_paths") or []
    finding_rule_ids = {
        str(finding.get("rule_id") or "")
        for finding in (artifacts.get("compliance_review") or {}).get("findings", [])
        if str(finding.get("rule_id") or "").strip()
    }
    explanation_rule_ids = {
        str(row.get("rule_id") or "")
        for row in finding_rows
        if str(row.get("rule_id") or "").strip()
    }
    missing_rule_ids = sorted(finding_rule_ids - explanation_rule_ids)
    classification_gaps = sorted(
        str(row.get("rule_id") or "")
        for row in finding_rows
        if not row.get("authority_path_classifications")
    )
    trace_gaps = sorted(
        str(row.get("rule_id") or "")
        for row in finding_rows
        if str(row.get("applicability_status") or "") != "not_applicable"
        and not (row.get("retrieval_trace_ids") or row.get("graph_path_ids"))
    )
    passed = (
        bool(summary.get("passed"))
        and not missing_rule_ids
        and not classification_gaps
        and not trace_gaps
    )
    return {
        "name": "authority_explanation_paths_ready",
        "passed": passed,
        "details": {
            "path": artifacts.get("artifact_paths", {}).get("authority_explanation_paths"),
            "finding_path_count": len(finding_rows),
            "all_findings_have_path_classification": summary.get(
                "all_findings_have_path_classification"
            ),
            "all_applicable_findings_have_trace_evidence": summary.get(
                "all_applicable_findings_have_trace_evidence"
            ),
            "missing_rule_ids": missing_rule_ids,
            "classification_gaps": classification_gaps,
            "trace_gaps": trace_gaps,
        },
    }


def _metrics(
    *,
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    required_sections = [result for result in section_results if result["required"]]
    conditional_scored = [
        result for result in conditional_results if not result.get("adjudication_pending")
    ]
    conditional_applicable = [
        result for result in conditional_scored if result["expected_applicability"] == "applicable"
    ]
    conditional_actual_applicable = [
        result for result in conditional_results if result.get("actual_is_applicable")
    ]
    return {
        "required_section_count": len(required_sections),
        "detected_required_section_count": sum(
            1 for result in required_sections if result["detected"]
        ),
        "section_detection_rate": _rate(
            sum(1 for result in required_sections if result["detected"]),
            len(required_sections),
        ),
        "baseline_rule_count": len(baseline_results),
        "baseline_source_record_match_rate": _rate(
            sum(1 for result in baseline_results if result["source_record_match"]),
            len(baseline_results),
        ),
        "baseline_document_role_match_rate": _rate(
            sum(1 for result in baseline_results if result["document_role_match"]),
            len(baseline_results),
        ),
        "rule_expectation_count": len(rule_results),
        "rule_section_match_rate": _rate(
            sum(1 for result in rule_results if result["section_match"]),
            len(rule_results),
        ),
        "source_record_match_rate": _rate(
            sum(1 for result in rule_results if result["source_record_match"]),
            len(rule_results),
        ),
        "source_document_role_match_rate": _rate(
            sum(1 for result in rule_results if result["source_document_role_match"]),
            len(rule_results),
        ),
        "citation_requirement_match_rate": _rate(
            sum(1 for result in rule_results if result["citation_requirements_met"]),
            len(rule_results),
        ),
        "authority_explanation_path_count": len(
            (artifacts.get("authority_explanation_paths") or {}).get(
                "finding_explanation_paths",
                [],
            )
        ),
        "authority_explanation_path_rate": _authority_explanation_path_rate(artifacts),
        "authority_trace_coverage_rate": _authority_trace_coverage_rate(artifacts),
        "conditional_expectation_count": len(conditional_results),
        "conditional_scored_count": len(conditional_scored),
        "conditional_adjudication_pending_count": sum(
            1 for result in conditional_results if result.get("adjudication_pending")
        ),
        "conditional_adjudication_completion_rate": _rate(
            len(conditional_scored),
            len(conditional_results),
        ),
        "conditional_adjudication_accepted_pending_count": conditional_adjudication.get(
            "accepted_pending_count"
        ),
        "conditional_adjudication_unexpected_pending_count": len(
            conditional_adjudication.get("unexpected_pending_rule_ids", [])
        ),
        "conditional_adjudication_missing_pending_count": len(
            conditional_adjudication.get("missing_pending_rule_ids", [])
        ),
        "conditional_expectation_match_rate": _rate(
            sum(1 for result in conditional_scored if result["applicability_match"]),
            len(conditional_scored),
        ),
        "conditional_applicable_source_record_match_rate": _rate(
            sum(1 for result in conditional_applicable if result["source_record_match"]),
            len(conditional_applicable),
        ),
        "conditional_applicable_section_match_rate": _rate(
            sum(1 for result in conditional_applicable if result["section_match"]),
            len(conditional_applicable),
        ),
        "conditional_actual_applicable_count": len(conditional_actual_applicable),
        "conditional_actual_applicable_source_record_match_rate": _rate(
            sum(1 for result in conditional_actual_applicable if result["source_record_match"]),
            len(conditional_actual_applicable),
        ),
        "conditional_actual_applicable_section_match_rate": _rate(
            sum(1 for result in conditional_actual_applicable if result["section_match"]),
            len(conditional_actual_applicable),
        ),
        "conditional_false_positive_count": _category_count(
            conditional_results,
            "conditional_false_positive",
        ),
        "conditional_false_negative_count": _category_count(
            conditional_results,
            "conditional_false_negative",
        ),
        "conditional_expectation_missing_count": _category_count(
            conditional_results,
            "conditional_expectation_missing",
        ),
        "forest_plan_expectation_count": len(forest_plan_results),
        "forest_plan_expectation_match_rate": _rate(
            sum(1 for result in forest_plan_results if result["passed"]),
            len(forest_plan_results),
        ),
        "reviewer_resolution_item_count": _pending_reviewer_resolution_count(artifacts),
        "standard_reviewer_resolution_item_count": _pending_standard_reviewer_resolution_count(
            artifacts
        ),
        "reviewer_resolution_queue_item_count": _reviewer_resolution_count(
            artifacts["forest_plan_reviewer_resolution_queue"]
        ),
        "standard_reviewer_resolution_queue_item_count": _reviewer_resolution_count_by_component_type(
            artifacts["forest_plan_reviewer_resolution_queue"],
            "standard",
        ),
    }


def _authority_explanation_path_rate(artifacts: dict[str, Any]) -> float:
    payload = artifacts.get("authority_explanation_paths") or {}
    rows = payload.get("finding_explanation_paths") or []
    findings = (artifacts.get("compliance_review") or {}).get("findings", [])
    return _rate(len(rows), len(findings))


def _authority_trace_coverage_rate(artifacts: dict[str, Any]) -> float:
    rows = (artifacts.get("authority_explanation_paths") or {}).get(
        "finding_explanation_paths",
        [],
    )
    applicable_rows = [
        row for row in rows if str(row.get("applicability_status") or "") != "not_applicable"
    ]
    return _rate(
        sum(
            1
            for row in applicable_rows
            if row.get("retrieval_trace_ids") or row.get("graph_path_ids")
        ),
        len(applicable_rows),
    )


def _failure_category_counts(
    *,
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
    artifact_errors: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in artifact_errors:
        counts[str(error["failure_category"])] += 1
    for result in section_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    for result in baseline_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in rule_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in conditional_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    if not conditional_adjudication.get("passed"):
        category = conditional_adjudication.get("failure_category")
        if category:
            counts[str(category)] += 1
    for result in forest_plan_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    return counts


def _broader_ea_failure_category_counts(
    *,
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    artifact_errors: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in artifact_errors:
        if str(error.get("artifact") or "") in FOREST_PLAN_ARTIFACTS:
            continue
        counts[str(error["failure_category"])] += 1
    for result in section_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    for result in baseline_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in rule_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in conditional_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    if not conditional_adjudication.get("passed"):
        category = conditional_adjudication.get("failure_category")
        if category:
            counts[str(category)] += 1
    return counts


def _forest_plan_failure_category_counts(
    *,
    forest_plan_results: list[dict[str, Any]],
    artifact_errors: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in artifact_errors:
        if str(error.get("artifact") or "") in FOREST_PLAN_ARTIFACTS:
            counts[str(error["failure_category"])] += 1
    for result in forest_plan_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    return counts


def _failed_rule_expectations(
    *,
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failed: list[dict[str, Any]] = []
    for expectation_type, results in (
        ("rule_review_expectation", rule_results),
        ("conditional_source_expectation", conditional_results),
    ):
        for result in results:
            categories = [
                str(category)
                for category in result.get("failure_categories", [])
                if str(category).strip()
            ]
            if result.get("passed") and not categories:
                continue
            entry = {
                "expectation_type": expectation_type,
                "rule_id": result.get("rule_id"),
                "failure_categories": categories,
                "actual_applicability": result.get("actual_applicability"),
                "actual_status": result.get("actual_status"),
                "expected_package_section_ids": result.get(
                    "expected_package_section_ids",
                    [],
                ),
                "actual_package_section_ids": result.get("actual_package_section_ids", []),
                "expected_source_record_ids": result.get("expected_source_record_ids", []),
                "actual_source_record_ids": result.get("actual_source_record_ids", []),
            }
            if expectation_type == "conditional_source_expectation":
                entry["expected_applicability"] = result.get("expected_applicability")
                entry["actual_is_applicable"] = result.get("actual_is_applicable")
                entry["adjudication_pending"] = result.get("adjudication_pending")
            failed.append(entry)
    return failed


def _failed_rule_ids(failed_rule_expectations: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(expectation["rule_id"])
            for expectation in failed_rule_expectations
            if expectation.get("rule_id")
        }
    )


def _failed_rule_ids_by_category(
    failed_rule_expectations: list[dict[str, Any]],
) -> dict[str, list[str]]:
    category_rule_ids: dict[str, set[str]] = {}
    for expectation in failed_rule_expectations:
        rule_id = expectation.get("rule_id")
        if not rule_id:
            continue
        for category in expectation.get("failure_categories", []):
            category_rule_ids.setdefault(str(category), set()).add(str(rule_id))
    return {
        category: sorted(rule_ids)
        for category, rule_ids in sorted(category_rule_ids.items())
    }


def _eval_lanes(
    *,
    checks: list[dict[str, Any]],
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    forest_plan_results: list[dict[str, Any]],
    artifacts: dict[str, Any],
    failure_category_counts: Counter[str],
    broader_ea_failure_category_counts: Counter[str],
    forest_plan_failure_category_counts: Counter[str],
) -> dict[str, Any]:
    check_by_name = {str(check["name"]): check for check in checks}
    broader_check_names = [
        "eval_contract_valid",
        "review_artifacts_loaded",
        "review_identity_matches_contract",
        "required_sections_detected",
        "baseline_source_documents_match_authority",
        "rule_source_section_expectations_met",
        "conditional_source_expectations_met",
        "conditional_adjudication_policy_met",
        "authority_explanation_paths_ready",
    ]
    broader_failed_checks = []
    for name in broader_check_names:
        check = check_by_name.get(name)
        if not check:
            continue
        if name == "review_artifacts_loaded":
            non_forest_artifact_errors = [
                error
                for error in artifacts["artifact_errors"]
                if str(error.get("artifact") or "") not in FOREST_PLAN_ARTIFACTS
            ]
            if non_forest_artifact_errors:
                broader_failed_checks.append(name)
            continue
        if not check.get("passed"):
            broader_failed_checks.append(name)

    validation_check = check_by_name.get("compliance_validation_passed")
    validation_failed_checks = _failed_compliance_validation_check_names(validation_check)
    if validation_check and not validation_check.get("passed"):
        non_forest_validation_failures = [
            name
            for name in validation_failed_checks
            if name not in FOREST_PLAN_VALIDATION_CHECKS
        ]
        if non_forest_validation_failures or not validation_failed_checks:
            broader_failed_checks.append("compliance_validation_passed")

    forest_artifact_errors = [
        error
        for error in artifacts["artifact_errors"]
        if str(error.get("artifact") or "") in FOREST_PLAN_ARTIFACTS
    ]
    forest_failed_checks = []
    if forest_artifact_errors:
        forest_failed_checks.append("review_artifacts_loaded")
    if any(name in FOREST_PLAN_VALIDATION_CHECKS for name in validation_failed_checks):
        forest_failed_checks.append("compliance_validation_passed")
    forest_plan_check = check_by_name.get("forest_plan_expectations_met")
    if forest_plan_check and not forest_plan_check.get("passed"):
        forest_failed_checks.append("forest_plan_expectations_met")

    reviewer_resolution_queue_count = _reviewer_resolution_count(
        artifacts["forest_plan_reviewer_resolution_queue"]
    )
    standard_reviewer_resolution_queue_count = _reviewer_resolution_count_by_component_type(
        artifacts["forest_plan_reviewer_resolution_queue"],
        "standard",
    )
    pending_reviewer_resolution_count = _pending_reviewer_resolution_count(artifacts)
    pending_standard_reviewer_resolution_count = _pending_standard_reviewer_resolution_count(
        artifacts
    )
    component_adjudication_summary = _forest_plan_component_adjudication_summary(artifacts)
    overall_failed_checks = [
        str(check["name"]) for check in checks if not bool(check.get("passed"))
    ]
    return {
        "overall": {
            "passed": not overall_failed_checks,
            "failed_check_names": overall_failed_checks,
            "failure_category_counts": dict(sorted(failure_category_counts.items())),
        },
        "broader_ea": {
            "passed": not broader_failed_checks,
            "failed_check_names": broader_failed_checks,
            "failure_category_counts": dict(
                sorted(broader_ea_failure_category_counts.items())
            ),
            "section_expectation_count": len(section_results),
            "baseline_rule_count": len(baseline_results),
            "rule_expectation_count": len(rule_results),
            "conditional_expectation_count": len(conditional_results),
        },
        "forest_plan": {
            "passed": not forest_failed_checks,
            "failed_check_names": forest_failed_checks,
            "failure_category_counts": dict(
                sorted(forest_plan_failure_category_counts.items())
            ),
            "expectation_count": len(forest_plan_results),
            "passed_expectation_count": sum(
                1 for result in forest_plan_results if result.get("passed")
            ),
            "failed_expectation_count": sum(
                1 for result in forest_plan_results if not result.get("passed")
            ),
            "pending_component_adjudication_count": pending_reviewer_resolution_count,
            "pending_standard_adjudication_count": pending_standard_reviewer_resolution_count,
            "reviewer_resolution_queue_item_count": reviewer_resolution_queue_count,
            "standard_reviewer_resolution_queue_item_count": standard_reviewer_resolution_queue_count,
            "component_adjudication_required": reviewer_resolution_queue_count > 0,
            "component_adjudication_present": bool(component_adjudication_summary),
            "component_adjudication_reviewer_ready": bool(
                component_adjudication_summary.get("reviewer_ready")
            ),
        },
    }


def _failed_compliance_validation_check_names(check: dict[str, Any] | None) -> list[str]:
    if not check:
        return []
    details = check.get("details")
    if not isinstance(details, dict):
        return []
    return [
        str(name)
        for name in details.get("failed_checks") or []
        if str(name).strip()
    ]


def _evaluate_contract_lane_expectations(
    *,
    contract: dict[str, Any],
    eval_lanes: dict[str, Any],
) -> dict[str, Any]:
    expected_lane_states = _normalized_expected_lane_states(contract.get("expected_lane_states"))
    allowed_blocker_categories = set(_string_list(contract.get("allowed_blocker_categories")))
    if not expected_lane_states:
        return {
            "configured": False,
            "passed": False,
            "details": {
                "configured": False,
                "expected_lane_states": {},
                "allowed_blocker_categories": sorted(allowed_blocker_categories),
            },
        }

    actual_lane_states = {
        "passed": bool(eval_lanes["overall"]["passed"]),
        "broader_ea_passed": bool(eval_lanes["broader_ea"]["passed"]),
        "forest_plan_passed": bool(eval_lanes["forest_plan"]["passed"]),
    }
    mismatches = []
    expected_blocked_lanes = []
    blocker_categories: set[str] = set()
    unexpected_blocker_categories: set[str] = set()
    for lane_name, expected in expected_lane_states.items():
        actual = actual_lane_states[lane_name]
        if actual != expected:
            mismatches.append(
                {
                    "lane": lane_name,
                    "expected": expected,
                    "actual": actual,
                }
            )
        if expected:
            continue
        expected_blocked_lanes.append(lane_name)
        actual_categories = set(_lane_failure_categories(eval_lanes, lane_name))
        blocker_categories.update(actual_categories)
        unexpected_blocker_categories.update(actual_categories - allowed_blocker_categories)
    missing_blocker_categories = bool(expected_blocked_lanes) and not blocker_categories
    passed = not mismatches and not missing_blocker_categories and not unexpected_blocker_categories
    return {
        "configured": True,
        "passed": passed,
        "details": {
            "configured": True,
            "expected_lane_states": expected_lane_states,
            "actual_lane_states": actual_lane_states,
            "allowed_blocker_categories": sorted(allowed_blocker_categories),
            "expected_blocked_lanes": expected_blocked_lanes,
            "matched_blocker_categories": sorted(blocker_categories),
            "unexpected_blocker_categories": sorted(unexpected_blocker_categories),
            "missing_blocker_categories": missing_blocker_categories,
            "mismatches": mismatches,
        },
    }


def _contract_status(
    *,
    contract_expectations: dict[str, Any],
    eval_lanes: dict[str, Any],
    passed: bool,
) -> str:
    if not passed:
        return "mismatch"
    details = contract_expectations.get("details")
    if not isinstance(details, dict) or not contract_expectations.get("configured"):
        return "reviewer_ready" if eval_lanes["overall"]["passed"] else "matched"
    if details.get("expected_blocked_lanes"):
        return "typed_blocked"
    return "reviewer_ready"


def _lane_failure_categories(eval_lanes: dict[str, Any], lane_name: str) -> list[str]:
    if lane_name == "passed":
        lane = eval_lanes["overall"]
    elif lane_name == "broader_ea_passed":
        lane = eval_lanes["broader_ea"]
    elif lane_name == "forest_plan_passed":
        lane = eval_lanes["forest_plan"]
    else:
        return []
    failure_categories = lane.get("failure_category_counts")
    if not isinstance(failure_categories, dict):
        return []
    return [
        str(category)
        for category, count in sorted(failure_categories.items())
        if str(category).strip() and int(count or 0) > 0
    ]


def _check_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "count": len(results),
        "passed_count": sum(1 for result in results if result.get("passed")),
        "failed_count": sum(1 for result in results if not result.get("passed")),
    }


def _category_count(results: list[dict[str, Any]], category: str) -> int:
    return sum(1 for result in results if category in result.get("failure_categories", []))


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)
