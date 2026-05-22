from __future__ import annotations

from collections import Counter
from typing import Any

from .nepa_3d_graph_contract_common import _dict
from .nepa_3d_graph_contract_common import _strings
from .nepa_3d_graph_contract_models import DEFAULT_GRAPH_FAILURE_CATEGORY
from .nepa_3d_graph_contract_models import GRAPH_FAILURE_CATEGORY_BY_CHECK_NAME


def build_nepa_3d_lens_metadata(contract: dict[str, Any]) -> list[dict[str, Any]]:
    lens_contract = _dict(contract.get("lens_metadata_contract"))
    required_lenses = _strings(lens_contract.get("required_lenses"))
    return [
        {
            "lens_id": lens_id,
            "label": lens_id.replace("_", " ").title(),
            "description": _lens_description(lens_id),
            "supported_node_types": _lens_node_types(lens_id),
            "supported_edge_types": _lens_edge_types(lens_id),
            "display_status_values": _lens_display_statuses(lens_id),
        }
        for lens_id in required_lenses
    ]


def annotate_nepa_3d_graph_validation_checks(
    checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **check,
            "failure_category": _graph_failure_category_for_check(str(check.get("name") or "")),
        }
        for check in checks
    ]


def nepa_3d_graph_failure_category_counts(checks: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter(
        str(check.get("failure_category") or DEFAULT_GRAPH_FAILURE_CATEGORY)
        for check in checks
        if not check.get("passed")
    )
    return dict(sorted(counts.items()))


def _lens_description(lens_id: str) -> str:
    descriptions = {
        "authority_currentness": "Display active, reserved, superseded, and candidate authority source state.",
        "forest_plan": "Display Region 1 forest-plan units, plans, and component inventory.",
        "package_applicability": "Display review-specific applicability states when a review overlay is exported.",
        "evidence_path": "Display source record, artifact, chunk, evidence span, claim, and rule paths.",
        "semantic_relationships": "Display canonical authority documents, scopes, semantic paths, and justification paths.",
        "readiness_blockers": "Display missing source, stale artifact, adjudication, and readiness blockers.",
    }
    return descriptions.get(lens_id, lens_id.replace("_", " "))


def _lens_node_types(lens_id: str) -> list[str]:
    values = {
        "authority_currentness": ["authority_family", "source_record", "readiness_blocker"],
        "forest_plan": ["forest_unit", "forest_plan", "forest_plan_component", "source_record"],
        "package_applicability": ["authority_family", "rule_template", "readiness_blocker"],
        "evidence_path": [
            "source_record",
            "artifact",
            "chunk",
            "evidence_span",
            "source_claim",
            "rule_template",
        ],
        "semantic_relationships": [
            "authority_document",
            "authority_section",
            "jurisdiction_scope",
            "forest_plan",
            "forest_unit",
            "authority_path",
            "justification_path",
            "source_record",
        ],
        "readiness_blockers": [
            "source_set",
            "authority_family",
            "source_record",
            "forest_unit",
            "forest_plan",
            "forest_plan_component",
            "readiness_blocker",
        ],
    }
    return values.get(lens_id, [])


def _lens_edge_types(lens_id: str) -> list[str]:
    values = {
        "authority_currentness": [
            "CONTAINS_AUTHORITY_FAMILY",
            "HAS_SOURCE_RECORD",
            "HAS_CURRENTNESS_STATUS",
            "BLOCKED_BY",
        ],
        "forest_plan": ["HAS_FOREST_PLAN", "HAS_FOREST_COMPONENT", "BELONGS_TO_FOREST_UNIT"],
        "package_applicability": [
            "PRODUCES_APPLICABILITY_DECISION",
            "APPLIES_TO_REVIEW",
            "NOT_APPLICABLE_TO_REVIEW",
            "NEEDS_ADJUDICATION",
        ],
        "evidence_path": [
            "HAS_ARTIFACT",
            "HAS_CHUNK",
            "HAS_EVIDENCE_SPAN",
            "SUPPORTS_SOURCE_CLAIM",
            "SUPPORTS_RULE_TEMPLATE",
        ],
        "semantic_relationships": [
            "CITES_AUTHORITY_DOCUMENT",
            "HAS_AUTHORITY_SECTION",
            "HAS_JURISDICTION_SCOPE",
            "HAS_AUTHORITY_PATH",
            "PATH_TARGETS",
            "JUSTIFIED_BY",
            "SUPPORTS_JUSTIFICATION_PATH",
        ],
        "readiness_blockers": ["HAS_READINESS_BLOCKER", "BLOCKED_BY"],
    }
    return values.get(lens_id, [])


def _lens_display_statuses(lens_id: str) -> list[str]:
    values = {
        "authority_currentness": ["active", "reserved", "superseded", "candidate"],
        "forest_plan": ["active", "readiness_blocked"],
        "package_applicability": [
            "applicable",
            "not_applicable",
            "unresolved",
            "adjudicated",
            "readiness_blocked",
        ],
        "evidence_path": ["active", "readiness_blocked"],
        "semantic_relationships": ["active", "superseded", "candidate"],
        "readiness_blockers": ["readiness_blocked"],
    }
    return values.get(lens_id, [])


def _graph_failure_category_for_check(name: str) -> str:
    if name in GRAPH_FAILURE_CATEGORY_BY_CHECK_NAME:
        return GRAPH_FAILURE_CATEGORY_BY_CHECK_NAME[name]
    lowered = name.lower()
    if "dangling" in lowered or "edges_reference_existing_nodes" in lowered:
        return "graph_dangling_edge"
    if "source_partition" in lowered or "partition" in lowered:
        return "graph_missing_source_partition"
    if "currentness" in lowered:
        return "graph_missing_currentness_status"
    if "candidate_authorit" in lowered:
        return "graph_missing_candidate_authority"
    if "authority_famil" in lowered:
        return "graph_missing_authority_family"
    if "source_record" in lowered or "catalog_source" in lowered:
        return "graph_missing_source_record"
    if "applicability" in lowered or "decision" in lowered:
        return "graph_missing_applicability_decision"
    if "superseded" in lowered or "reserved" in lowered:
        return "graph_superseded_as_current"
    if "noncurrent" in lowered or "non_current" in lowered:
        return "graph_noncurrent_document_in_main_corpus"
    if "fsh" in lowered or "handbook" in lowered or "chapter" in lowered:
        return "graph_handbook_chapter_collapsed"
    if "region1" in lowered or "forest" in lowered:
        return "graph_region1_profile_gap"
    return DEFAULT_GRAPH_FAILURE_CATEGORY
