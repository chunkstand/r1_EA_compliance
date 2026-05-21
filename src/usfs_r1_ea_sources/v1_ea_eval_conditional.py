from __future__ import annotations

from typing import Any

from .v1_ea_eval_rule_expectations import _actual_applicability
from .v1_ea_eval_rule_expectations import _actual_document_roles
from .v1_ea_eval_rule_expectations import _actual_source_record_ids
from .v1_ea_eval_rule_expectations import _actual_status
from .v1_ea_eval_rule_expectations import _augment_with_decision_evidence
from .v1_ea_eval_rule_expectations import _decision_surrogate
from .v1_ea_eval_rule_expectations import _evaluate_rule_source_section
from .v1_ea_eval_rule_expectations import _is_actual_applicable
from .v1_ea_eval_support import _policy_rule_ids


def _evaluate_conditional_expectations(
    *,
    conditional_expectations: list[dict[str, Any]],
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    applicability_decision_index: dict[str, dict[str, Any]],
    bridge_index: dict[str, dict[str, Any]],
    section_results: list[dict[str, Any]],
    allow_unadjudicated: bool,
) -> list[dict[str, Any]]:
    results = []
    expected_rule_ids = {str(expectation["rule_id"]) for expectation in conditional_expectations}
    for expectation in conditional_expectations:
        rule_id = str(expectation["rule_id"])
        expected = str(expectation["expected_applicability"])
        decision = applicability_decision_index.get(rule_id)
        bridge = bridge_index.get(rule_id)
        finding = finding_index.get(rule_id) or bridge or _decision_surrogate(decision)
        row = matrix_index.get(rule_id) or bridge or _decision_surrogate(decision)
        finding, row = _augment_with_decision_evidence(finding, row, decision)
        source_section = _evaluate_rule_source_section(
            expectation=expectation,
            finding=finding,
            row=row,
            section_results=section_results,
        )
        actual_status = _actual_status(finding, row)
        actual_applicability = _actual_applicability(finding, row)
        actual_applicable = _is_actual_applicable(finding, row)
        failure_categories: list[str] = []
        applicability_match = True
        adjudication_pending = expected == "adjudicate"
        source_alignment_required = expected == "applicable" or (
            expected == "adjudicate" and actual_applicable
        )
        if expected == "applicable":
            applicability_match = actual_applicable
            if not actual_applicable:
                failure_categories.append("conditional_false_negative")
        elif expected == "not_applicable":
            applicability_match = not actual_applicable
            if actual_applicable:
                failure_categories.append("conditional_false_positive")
        elif expected == "needs_reviewer_resolution":
            applicability_match = actual_applicability == "needs_reviewer_resolution"
            if not applicability_match:
                failure_categories.append("conditional_resolution_miss")
        elif expected == "adjudicate":
            applicability_match = allow_unadjudicated
        if source_alignment_required:
            for category in source_section["failure_categories"]:
                if category not in failure_categories:
                    failure_categories.append(category)
            passed = applicability_match and source_section["passed"]
        else:
            passed = applicability_match
        results.append(
            {
                "rule_id": rule_id,
                "expected_applicability": expected,
                "actual_applicability": actual_applicability,
                "actual_status": actual_status,
                "actual_is_applicable": actual_applicable,
                "applicability_match": applicability_match,
                "adjudication_pending": adjudication_pending,
                "source_alignment_required": source_alignment_required,
                "trigger_terms": expectation.get("trigger_terms", []),
                "classification_rationale": expectation.get("classification_rationale"),
                "expected_package_section_ids": expectation.get("expected_package_section_ids", []),
                "actual_package_section_ids": source_section["actual_package_section_ids"],
                "section_match": source_section["section_match"],
                "expected_source_record_ids": expectation.get("expected_source_record_ids", []),
                "actual_source_record_ids": source_section["actual_source_record_ids"],
                "source_record_match": source_section["source_record_match"],
                "expected_source_document_roles": expectation.get(
                    "expected_source_document_roles",
                    [],
                ),
                "actual_source_document_roles": source_section["actual_source_document_roles"],
                "source_document_role_match": source_section["source_document_role_match"],
                "passed": passed,
                "failure_categories": failure_categories,
            }
        )
    for rule_id, finding in sorted(finding_index.items()):
        if str(finding.get("applicability_mode")) != "conditional":
            continue
        if rule_id in expected_rule_ids:
            continue
        row = matrix_index.get(rule_id)
        if not _is_actual_applicable(finding, row):
            continue
        results.append(
            {
                "rule_id": rule_id,
                "expected_applicability": "missing_contract_expectation",
                "actual_applicability": _actual_applicability(finding, row),
                "actual_status": _actual_status(finding, row),
                "actual_is_applicable": True,
                "applicability_match": False,
                "adjudication_pending": False,
                "source_alignment_required": True,
                "trigger_terms": [],
                "classification_rationale": None,
                "expected_package_section_ids": [],
                "actual_package_section_ids": [],
                "section_match": False,
                "expected_source_record_ids": [],
                "actual_source_record_ids": _actual_source_record_ids(finding, row or {}),
                "source_record_match": False,
                "expected_source_document_roles": [],
                "actual_source_document_roles": _actual_document_roles(finding, row or {}),
                "source_document_role_match": False,
                "passed": False,
                "failure_categories": ["conditional_expectation_missing"],
            }
        )
    return results


def _conditional_adjudication_report(
    *,
    contract: dict[str, Any],
    conditional_results: list[dict[str, Any]],
) -> dict[str, Any]:
    policy = contract.get("conditional_adjudication_policy")
    policy_present = isinstance(policy, dict) and bool(policy)
    policy = policy if isinstance(policy, dict) else {}
    pending_results = sorted(
        (result for result in conditional_results if result.get("adjudication_pending")),
        key=lambda result: str(result.get("rule_id") or ""),
    )
    actual_pending_rule_ids = [
        str(result["rule_id"])
        for result in pending_results
        if str(result.get("rule_id") or "").strip()
    ]
    raw_accepted_pending_rule_ids = policy.get("accepted_pending_rule_ids")
    accepted_pending_rule_ids = _policy_rule_ids(raw_accepted_pending_rule_ids)
    accepted_pending_count = policy.get("accepted_pending_count")
    mode = str(policy.get("mode") or "").strip()
    failure_reasons = []
    if pending_results and not policy_present:
        failure_reasons.append("missing_conditional_adjudication_policy")
    if policy_present and mode != "accepted_pending_v1":
        failure_reasons.append("unsupported_conditional_adjudication_policy_mode")
    if policy_present and not isinstance(raw_accepted_pending_rule_ids, list):
        failure_reasons.append("accepted_pending_rule_ids_must_be_list")
    if policy_present and (
        not isinstance(accepted_pending_count, int)
        or isinstance(accepted_pending_count, bool)
    ):
        failure_reasons.append("accepted_pending_count_must_be_integer")
    elif policy_present and accepted_pending_count != len(actual_pending_rule_ids):
        failure_reasons.append("accepted_pending_count_mismatch")
    unexpected_pending_rule_ids = sorted(
        set(actual_pending_rule_ids) - set(accepted_pending_rule_ids)
    )
    missing_pending_rule_ids = sorted(
        set(accepted_pending_rule_ids) - set(actual_pending_rule_ids)
    )
    if unexpected_pending_rule_ids:
        failure_reasons.append("unexpected_pending_rule_ids")
    if missing_pending_rule_ids:
        failure_reasons.append("missing_pending_rule_ids")
    passed = not failure_reasons
    return {
        "schema_version": "conditional-adjudication-policy-results-v0",
        "passed": passed,
        "failure_category": None
        if passed
        else "conditional_adjudication_policy_mismatch",
        "failure_reasons": failure_reasons,
        "policy_present": policy_present,
        "policy_mode": mode or None,
        "policy_rationale": policy.get("rationale") if policy_present else None,
        "accepted_pending_count": accepted_pending_count if policy_present else None,
        "accepted_pending_rule_ids": accepted_pending_rule_ids,
        "actual_pending_count": len(actual_pending_rule_ids),
        "actual_pending_rule_ids": actual_pending_rule_ids,
        "actual_pending_applicable_count": sum(
            1 for result in pending_results if result.get("actual_is_applicable")
        ),
        "unexpected_pending_rule_ids": unexpected_pending_rule_ids,
        "missing_pending_rule_ids": missing_pending_rule_ids,
        "pending_results": [
            {
                "rule_id": result.get("rule_id"),
                "expected_applicability": result.get("expected_applicability"),
                "actual_applicability": result.get("actual_applicability"),
                "actual_status": result.get("actual_status"),
                "actual_is_applicable": result.get("actual_is_applicable"),
                "classification_rationale": result.get("classification_rationale"),
                "source_alignment_required": result.get("source_alignment_required"),
                "section_match": result.get("section_match"),
                "source_record_match": result.get("source_record_match"),
                "source_document_role_match": result.get("source_document_role_match"),
                "expected_package_section_ids": result.get(
                    "expected_package_section_ids",
                    [],
                ),
                "actual_package_section_ids": result.get("actual_package_section_ids", []),
                "expected_source_record_ids": result.get("expected_source_record_ids", []),
                "actual_source_record_ids": result.get("actual_source_record_ids", []),
                "expected_source_document_roles": result.get(
                    "expected_source_document_roles",
                    [],
                ),
                "actual_source_document_roles": result.get(
                    "actual_source_document_roles",
                    [],
                ),
            }
            for result in pending_results
        ],
    }


def _conditional_adjudication_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": report.get("passed"),
        "policy_mode": report.get("policy_mode"),
        "accepted_pending_count": report.get("accepted_pending_count"),
        "actual_pending_count": report.get("actual_pending_count"),
        "actual_pending_applicable_count": report.get("actual_pending_applicable_count"),
        "accepted_pending_rule_ids": report.get("accepted_pending_rule_ids", []),
        "actual_pending_rule_ids": report.get("actual_pending_rule_ids", []),
        "unexpected_pending_rule_ids": report.get("unexpected_pending_rule_ids", []),
        "missing_pending_rule_ids": report.get("missing_pending_rule_ids", []),
        "failure_reasons": report.get("failure_reasons", []),
    }
