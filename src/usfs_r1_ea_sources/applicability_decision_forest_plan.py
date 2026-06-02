from __future__ import annotations

from typing import Any

from .applicability_contract_support import strings
from .applicability_decision_arbitration import trigger_groups
from .applicability_decision_evidence import present_package_values


def forest_plan_component_result(
    *,
    candidate: dict[str, Any],
    package_nodes: list[dict[str, Any]],
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
    coverage_boundary: dict[str, Any],
    present_values: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    required_values = _required_package_values(candidate)
    if present_values is None:
        present_values = present_package_values(package_nodes)
    missing = [
        f"{fact_type}:{value}"
        for fact_type, values in required_values.items()
        for value in values
        if value not in present_values.get(fact_type, set())
    ]
    trigger_required = bool(trigger_groups(candidate.get("positive_trigger_groups")))
    trigger_matched = positive_match["matched"] if trigger_required else True

    if negative_match["requires_adjudication"]:
        return {
            "status": "needs_adjudication",
            "basis_type": "unresolved_evidence_conflict",
            "basis": {
                "rationale": "Forest Plan component negative scope evidence is weak or conflicting.",
                "matched_negative_trigger_groups": negative_match["matched_groups"],
            },
            "missing_evidence": missing,
            "contradiction_notes": negative_match["adjudication_notes"],
            "confidence": "needs_adjudication",
        }

    if negative_match["matched"]:
        basis = {
            "rationale": (
                "Package evidence matched an explicit negative Forest Plan component "
                "scope trigger."
            ),
            "matched_negative_trigger_groups": negative_match["matched_groups"],
            "matched_package_values": required_values if not missing else {},
            "matched_positive_trigger_groups": positive_match["matched_groups"],
            "missing_package_values": missing,
        }
        if coverage_boundary["coverage_sufficient"]:
            return {
                "status": "not_applicable",
                "basis_type": "negative_package_evidence",
                "basis": basis,
                "missing_evidence": [],
                "contradiction_notes": [],
                "confidence": "deterministic_high",
            }
        return {
            "status": "unresolved",
            "basis_type": "forest_plan_profile_resolution",
            "basis": basis,
            "missing_evidence": [*missing, "sufficient forest-plan search coverage"],
            "contradiction_notes": [],
            "confidence": "low",
        }

    if positive_match["requires_adjudication"]:
        return {
            "status": "needs_adjudication",
            "basis_type": "unresolved_evidence_conflict",
            "basis": {
                "rationale": "Forest Plan component trigger evidence is weak or conflicting.",
                "matched_trigger_groups": positive_match["matched_groups"],
            },
            "missing_evidence": missing,
            "contradiction_notes": positive_match["adjudication_notes"],
            "confidence": "needs_adjudication",
        }

    if not missing and trigger_matched:
        return {
            "status": "applicable",
            "basis_type": "forest_plan_component",
            "basis": {
                "rationale": "Package facts match the Forest Plan component scope.",
                "matched_package_values": required_values,
                "matched_trigger_groups": positive_match["matched_groups"],
            },
            "missing_evidence": [],
            "contradiction_notes": [],
            "confidence": "deterministic_high",
        }

    basis = {
        "rationale": "Required Forest Plan component package scope was not found.",
        "missing_package_values": missing,
        "missing_trigger_groups": [] if trigger_matched else candidate.get("positive_trigger_groups") or [],
    }
    if coverage_boundary["coverage_sufficient"]:
        return {
            "status": "not_applicable",
            "basis_type": "forest_plan_component",
            "basis": basis,
            "missing_evidence": missing,
            "contradiction_notes": [],
            "confidence": "deterministic_medium",
        }
    return {
        "status": "unresolved",
        "basis_type": "forest_plan_profile_resolution",
        "basis": basis,
        "missing_evidence": [*missing, "sufficient forest-plan search coverage"],
        "contradiction_notes": [],
        "confidence": "low",
    }


def _required_package_values(candidate: dict[str, Any]) -> dict[str, list[str]]:
    forest_plan = candidate.get("forest_plan") if isinstance(candidate.get("forest_plan"), dict) else {}
    return {
        "geography": strings(forest_plan.get("geographic_area_ids")),
        "management_area": strings(forest_plan.get("management_area_ids")),
        "overlay": strings(forest_plan.get("overlay_ids")),
    }
