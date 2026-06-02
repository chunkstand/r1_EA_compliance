from __future__ import annotations

from typing import Any

from .applicability_contract_support import string_groups
from .applicability_contract_support import strings


ARBITRATION_SUMMARY_SCHEMA_VERSION = "applicability-evidence-arbitration-v0"


def missing_trigger_groups(decision: dict[str, Any]) -> list[list[str]]:
    basis_groups = decision.get("basis", {}).get("missing_trigger_groups")
    if basis_groups:
        return basis_groups
    for evidence in decision.get("explicit_trigger_miss_evidence") or []:
        groups = evidence.get("missing_trigger_groups")
        if groups:
            return groups
    return []


def arbitrate_trigger_matches(
    *,
    candidate: dict[str, Any],
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
    coverage_boundary: dict[str, Any],
) -> dict[str, Any]:
    contract = _trigger_arbitration_contract(candidate)
    positive_results = positive_match.get("trigger_group_results") or []
    decisive_groups = [
        list(result.get("trigger_group") or [])
        for result in positive_results
        if result.get("matched") and strong_evidence_count(result) > 0
    ]
    weak_groups = [
        list(result.get("trigger_group") or [])
        for result in positive_results
        if result.get("matched") and weak_evidence_count(result) > 0
    ]
    weak_only_groups = [
        list(result.get("trigger_group") or [])
        for result in positive_results
        if result.get("matched")
        and weak_evidence_count(result) > 0
        and strong_evidence_count(result) == 0
    ]
    required_groups = contract["required_trigger_groups"]
    decisive_keys = {_trigger_group_key(group) for group in decisive_groups}
    missing_required = [
        group
        for group in required_groups
        if _trigger_group_key(group) not in decisive_keys
    ]
    minimum_strong = int(contract["minimum_strong_trigger_groups"])
    strong_sufficient = (
        bool(decisive_groups)
        and len(decisive_groups) >= minimum_strong
        and not missing_required
    )
    weak_auxiliary_groups = [
        group
        for group in weak_groups
        if _trigger_group_key(group) not in decisive_keys
    ]
    notes = sorted(set(strings(positive_match.get("adjudication_notes"))))
    arbitration_status = "not_evaluated"
    rationale = "Trigger arbitration was not evaluated."
    positive_sufficient = False
    requires_adjudication = False

    if strong_sufficient and negative_match.get("matched"):
        conflict_policy = contract["positive_negative_conflict_policy"]
        if conflict_policy == "positive_precedence":
            positive_sufficient = True
            arbitration_status = (
                "strong_positive_with_weak_auxiliary"
                if weak_auxiliary_groups
                else "strong_positive_decisive"
            )
            rationale = (
                "A rule contract gives positive trigger evidence precedence over matched "
                "negative trigger evidence."
            )
        elif conflict_policy == "negative_precedence":
            arbitration_status = "negative_precedence"
            rationale = (
                "A rule contract gives negative trigger evidence precedence over matched "
                "positive trigger evidence."
            )
        else:
            requires_adjudication = True
            arbitration_status = "positive_negative_conflict"
            rationale = (
                "Strong positive trigger evidence and explicit negative or out-of-scope "
                "trigger evidence were both found."
            )
            notes = sorted(
                set(
                    notes
                    + strings(negative_match.get("adjudication_notes"))
                    + [rationale]
                )
            )
    elif strong_sufficient:
        positive_sufficient = True
        arbitration_status = (
            "strong_positive_with_weak_auxiliary"
            if weak_auxiliary_groups
            else "strong_positive_decisive"
        )
        rationale = (
            "At least one rule-contract-sufficient positive trigger group has strong "
            "package evidence."
        )
        if weak_auxiliary_groups:
            rationale = (
                f"{rationale} Weak auxiliary trigger groups remain recorded for traceability."
            )
    elif negative_match.get("matched"):
        arbitration_status = "negative_trigger_decisive"
        rationale = (
            "Negative or out-of-scope trigger evidence was found without sufficient "
            "positive evidence."
        )
    elif positive_match.get("matched"):
        requires_adjudication = True
        arbitration_status = (
            "weak_positive_only"
            if weak_only_groups and not decisive_groups
            else "insufficient_strong_positive_trigger"
        )
        if missing_required:
            rationale = (
                "Matched positive trigger evidence does not satisfy required strong trigger "
                "groups declared by the rule contract."
            )
        elif decisive_groups:
            rationale = (
                "Matched positive trigger evidence does not meet the rule contract's minimum "
                "number of strong trigger groups."
            )
        else:
            rationale = "Only weak positive trigger evidence was found."
    elif coverage_boundary.get("coverage_sufficient"):
        arbitration_status = "positive_trigger_absent"
        rationale = "No positive trigger evidence was found within the recorded search boundary."
    else:
        arbitration_status = "coverage_gap"
        rationale = "Positive trigger evidence was not found and search coverage is insufficient."

    return {
        "arbitration_status": arbitration_status,
        "positive_trigger_sufficient": positive_sufficient,
        "requires_adjudication": requires_adjudication,
        "decisive_trigger_groups": (
            decisive_groups if positive_sufficient or requires_adjudication else []
        ),
        "weak_auxiliary_trigger_groups": weak_auxiliary_groups if positive_sufficient else [],
        "weak_only_trigger_groups": weak_only_groups,
        "missing_required_trigger_groups": missing_required,
        "minimum_strong_trigger_groups": minimum_strong,
        "strong_trigger_group_count": len(decisive_groups),
        "arbitration_rationale": rationale,
        "arbitration_notes": notes,
        "contract": contract,
    }


def trigger_arbitration_not_evaluated(
    rationale: str,
    *,
    arbitration_status: str = "not_evaluated",
) -> dict[str, Any]:
    return {
        "arbitration_status": arbitration_status,
        "positive_trigger_sufficient": False,
        "requires_adjudication": False,
        "decisive_trigger_groups": [],
        "weak_auxiliary_trigger_groups": [],
        "weak_only_trigger_groups": [],
        "missing_required_trigger_groups": [],
        "minimum_strong_trigger_groups": 0,
        "strong_trigger_group_count": 0,
        "arbitration_rationale": rationale,
        "arbitration_notes": [],
        "contract": {},
    }


def arbitration_summary(
    *,
    status: str,
    basis_type: str,
    predicate_name: str,
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
    trigger_arbitration: dict[str, Any],
    source_evidence: list[dict[str, Any]],
    selected_retrieval_result_ids: list[str],
    retrieval_trace_ids: list[str],
    graph_path_ids: list[str],
) -> dict[str, Any]:
    requires_adjudication = (
        status == "needs_adjudication"
        and bool(trigger_arbitration.get("requires_adjudication"))
    )
    notes = sorted(
        set(
            strings(trigger_arbitration.get("arbitration_notes"))
            + strings(positive_match.get("adjudication_notes"))
            + strings(negative_match.get("adjudication_notes"))
        )
    )
    return {
        "schema_version": ARBITRATION_SUMMARY_SCHEMA_VERSION,
        "diagnostic_only": False,
        "decision_effect": _arbitration_decision_effect(
            status=status,
            positive_match=positive_match,
            negative_match=negative_match,
            trigger_arbitration=trigger_arbitration,
        ),
        "status": status,
        "basis_type": basis_type,
        "predicate_name": predicate_name,
        "arbitration_status": trigger_arbitration.get("arbitration_status"),
        "decisive_trigger_groups": trigger_arbitration.get("decisive_trigger_groups") or [],
        "weak_auxiliary_trigger_groups": (
            trigger_arbitration.get("weak_auxiliary_trigger_groups") or []
        ),
        "weak_only_trigger_groups": trigger_arbitration.get("weak_only_trigger_groups") or [],
        "missing_required_trigger_groups": (
            trigger_arbitration.get("missing_required_trigger_groups") or []
        ),
        "minimum_strong_trigger_groups": trigger_arbitration.get(
            "minimum_strong_trigger_groups"
        ),
        "arbitration_rationale": trigger_arbitration.get("arbitration_rationale"),
        "positive_trigger_matched": bool(positive_match.get("matched")),
        "negative_trigger_matched": bool(negative_match.get("matched")),
        "requires_adjudication": requires_adjudication,
        "positive_trigger_groups": positive_match.get("trigger_group_results") or [],
        "negative_trigger_groups": negative_match.get("trigger_group_results") or [],
        "arbitration_notes": notes,
        "source_evidence_ids": sorted(
            str(item.get("evidence_id"))
            for item in source_evidence
            if item.get("evidence_id")
        ),
        "selected_retrieval_result_ids": selected_retrieval_result_ids,
        "retrieval_trace_ids": retrieval_trace_ids,
        "graph_path_ids": graph_path_ids,
    }


def trigger_groups(value: Any) -> list[list[str]]:
    return string_groups(value)


def flatten_groups(value: Any) -> list[str]:
    return sorted({term for group in trigger_groups(value) for term in group})


def weak_evidence_count(group_result: dict[str, Any]) -> int:
    counts = group_result.get("evidence_strength_counts") or {}
    return int(counts.get("weak_signal") or 0)


def strong_evidence_count(group_result: dict[str, Any]) -> int:
    counts = group_result.get("evidence_strength_counts") or {}
    return sum(
        int(count)
        for confidence_class, count in counts.items()
        if confidence_class not in {"weak_signal", "negative_context"}
    )


def _trigger_arbitration_contract(candidate: dict[str, Any]) -> dict[str, Any]:
    raw_contract = candidate.get("trigger_arbitration_contract")
    if not isinstance(raw_contract, dict):
        raw_contract = (candidate.get("rule_template") or {}).get("trigger_arbitration")
    if not isinstance(raw_contract, dict):
        raw_contract = (
            candidate.get("deterministic_applicability_test_contract") or {}
        ).get("trigger_arbitration")
    if not isinstance(raw_contract, dict):
        raw_contract = {}
    required_groups = trigger_groups(
        raw_contract.get("required_trigger_groups")
        or raw_contract.get("required_strong_trigger_groups")
    )
    minimum_strong = _positive_int(
        raw_contract.get("minimum_strong_trigger_groups")
        or raw_contract.get("min_strong_trigger_groups"),
        default=len(required_groups) if required_groups else 1,
    )
    policy = str(
        raw_contract.get("positive_negative_conflict_policy")
        or "needs_adjudication"
    )
    if policy not in {"needs_adjudication", "positive_precedence", "negative_precedence"}:
        policy = "needs_adjudication"
    return {
        "required_trigger_groups": required_groups,
        "minimum_strong_trigger_groups": minimum_strong,
        "positive_negative_conflict_policy": policy,
    }


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, parsed)


def _trigger_group_key(group: list[str]) -> tuple[str, ...]:
    return tuple(str(value).lower() for value in strings(group))


def _arbitration_decision_effect(
    *,
    status: str,
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
    trigger_arbitration: dict[str, Any],
) -> str:
    arbitration_status = str(trigger_arbitration.get("arbitration_status") or "")
    if status == "needs_adjudication" and arbitration_status == "positive_negative_conflict":
        return "blocked_by_positive_negative_conflict"
    if status == "needs_adjudication" and arbitration_status in {
        "weak_positive_only",
        "insufficient_strong_positive_trigger",
    }:
        return "blocked_by_weak_positive_trigger"
    if status == "needs_adjudication" and negative_match.get("requires_adjudication"):
        return "blocked_by_weak_negative_trigger"
    if (
        status == "applicable"
        and arbitration_status == "strong_positive_with_weak_auxiliary"
    ):
        return "positive_trigger_decisive_with_weak_auxiliary"
    if status == "applicable" and positive_match.get("matched"):
        return "positive_trigger_decisive"
    if status == "not_applicable" and negative_match.get("matched"):
        return "negative_trigger_decisive"
    if status == "not_applicable":
        return "trigger_absence_decisive"
    return "diagnostic_no_effect"
