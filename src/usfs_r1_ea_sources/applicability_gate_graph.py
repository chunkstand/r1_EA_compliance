from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .records import sha256_file


APPLICABILITY_GATE_GRAPH_CONTRACT_SCHEMA_VERSION = "applicability-gate-graph-contract-v1"
APPLICABILITY_GATE_GRAPH_SCHEMA_VERSION = "applicability-gate-graph-v1"
DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH = Path(
    "config/applicability_gate_graph_nepa_ea_v1.json"
)
DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

ALLOWED_STRUCTURAL_GATE_TYPES = {
    "authority_group_gate",
    "forest_plan_component_group_gate",
    "forest_plan_component_type_gate",
    "forest_plan_gate",
    "process_gate",
    "review_output_gate",
    "review_root_gate",
    "scope_gate",
}
ALLOWED_DYNAMIC_GATE_TYPES = {
    "authority_family_gate",
    "candidate_authority_gate",
    "forest_plan_component_gate",
    "forest_plan_instance_gate",
}
ALLOWED_GATE_TYPES = ALLOWED_STRUCTURAL_GATE_TYPES | ALLOWED_DYNAMIC_GATE_TYPES
ALLOWED_ACTIVATION_RULES = {
    "always_open_for_ea_package",
    "open_when_applicable",
    "open_when_parent_applicable",
}
FINAL_DECISION_STATUSES = {
    "applicable",
    "not_applicable",
    "needs_adjudication",
    "unresolved",
}
OPEN_ACTIVATION_STATES = {"open", "currentness_only"}


@dataclass(frozen=True)
class ApplicabilityGateGraphResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    gate_graph_path: Path
    summary_path: Path
    validation_path: Path
    summary: dict[str, Any]


def build_applicability_gate_graph(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    gate_graph_contract_path: Path = DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    authority_universe_path: Path | None = None,
    decisions_path: Path | None = None,
    output_path: Path | None = None,
) -> ApplicabilityGateGraphResult:
    """Build a review-scoped NEPA applicability gate graph.

    The graph is a structural hierarchy over the authority-family inventory with optional
    review-specific candidate and decision overlays. It does not decide applicability itself.
    """

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    authority_universe_path = authority_universe_path or (
        applicability_dir / "authority_universe_snapshot.json"
    )
    decisions_path = decisions_path or (applicability_dir / "applicability_decisions.jsonl")
    gate_graph_path = output_path or (applicability_dir / "applicability_gate_graph.json")
    summary_path = gate_graph_path.with_name("applicability_gate_graph_summary.json")
    validation_path = gate_graph_path.with_name("applicability_gate_graph_validation.json")

    contract = _read_json(gate_graph_contract_path)
    inventory = _read_json(authority_inventory_path)
    authority_universe = _read_json_if_exists(authority_universe_path)
    decisions = _read_jsonl_if_exists(decisions_path)
    if source_set_id is None:
        source_set_id = str(authority_universe.get("source_set_id") or "").strip() or None
    if source_set_id is not None:
        _validate_safe_segment(source_set_id, "source_set_id")

    contract_checks = validate_applicability_gate_graph_contract(contract, inventory)
    created_at = _utc_now()
    family_by_id = _authority_family_by_id(inventory)
    family_gate_id_by_family = _family_gate_id_by_family(contract)
    family_ids_by_rule_id = _family_ids_by_rule_id(inventory)
    candidate_authorities = _dict_list(authority_universe.get("candidate_authorities"))
    decisions_by_candidate_id = {
        str(decision.get("candidate_authority_id")): decision
        for decision in decisions
        if decision.get("candidate_authority_id")
    }
    candidate_family_by_id = {
        str(candidate.get("candidate_authority_id")): _candidate_family_id(
            candidate,
            family_ids_by_rule_id=family_ids_by_rule_id,
        )
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_id")
    }
    family_decision_states = _family_decision_states(
        candidate_authorities=candidate_authorities,
        decisions_by_candidate_id=decisions_by_candidate_id,
        candidate_family_by_id=candidate_family_by_id,
        family_by_id=family_by_id,
    )

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    for structural_gate in _dict_list(contract.get("structural_gates")):
        _add_static_gate_node(
            nodes,
            contract_gate=structural_gate,
            contract=contract,
            family=None,
            family_state=None,
            review_id=review_id,
            source_set_id=source_set_id,
        )
    for placement in _dict_list(contract.get("authority_family_gate_placements")):
        family_id = str(placement.get("authority_family_id") or "")
        family = family_by_id.get(family_id, {"family_id": family_id, "name": family_id})
        gate = {
            "gate_id": _authority_family_gate_id(family_id),
            "gate_type": "authority_family_gate",
            "label": family.get("name") or family_id,
            "parent_gate_id": placement.get("parent_gate_id"),
            "activation_rule": "open_when_applicable",
            "applicability_basis": family.get("rationale")
            or "Authority-family applicability is determined by package facts and source evidence.",
            "authority_family_id": family_id,
        }
        _add_static_gate_node(
            nodes,
            contract_gate=gate,
            contract=contract,
            family=family,
            family_state=family_decision_states.get(family_id),
            review_id=review_id,
            source_set_id=source_set_id,
        )

    _add_parent_edges(nodes, edges, review_id=review_id, source_set_id=source_set_id)
    _resolve_static_activation_states(nodes)
    _add_dynamic_candidate_gates(
        nodes,
        edges,
        review_id=review_id,
        source_set_id=source_set_id,
        candidate_authorities=candidate_authorities,
        decisions_by_candidate_id=decisions_by_candidate_id,
        candidate_family_by_id=candidate_family_by_id,
        family_gate_id_by_family=family_gate_id_by_family,
        family_ids_by_rule_id=family_ids_by_rule_id,
    )
    _resolve_dynamic_parent_edges(nodes, edges, review_id=review_id, source_set_id=source_set_id)

    sorted_nodes = [nodes[node_id] for node_id in sorted(nodes)]
    sorted_edges = [edges[edge_id] for edge_id in sorted(edges)]
    graph_checks = validate_applicability_gate_graph_records(
        nodes=sorted_nodes,
        edges=sorted_edges,
        contract=contract,
        inventory=inventory,
    )
    checks = contract_checks + graph_checks
    summary = _summary(
        nodes=sorted_nodes,
        edges=sorted_edges,
        contract=contract,
        inventory=inventory,
        authority_universe=authority_universe,
        decisions=decisions,
        checks=checks,
    )
    graph = {
        "schema_version": APPLICABILITY_GATE_GRAPH_SCHEMA_VERSION,
        "graph_id": f"applicability-gate-graph:{review_id}:{source_set_id or 'unknown-source-set'}",
        "created_at": created_at,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "contract_id": contract.get("contract_id"),
        "root_gate_id": contract.get("root_gate_id"),
        "expansion_semantics": contract.get("expansion_semantics", {}),
        "inputs": _input_records(
            {
                "gate_graph_contract": gate_graph_contract_path,
                "authority_inventory": authority_inventory_path,
                "authority_universe_snapshot": authority_universe_path,
                "applicability_decisions": decisions_path,
            }
        ),
        "nodes": sorted_nodes,
        "edges": sorted_edges,
        "summary": summary,
        "validation": {
            "passed": all(check["passed"] for check in checks),
            "checks": checks,
        },
    }
    gate_graph_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(gate_graph_path, graph)
    _write_json(summary_path, summary)
    _write_json(validation_path, graph["validation"])
    return ApplicabilityGateGraphResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        gate_graph_path=gate_graph_path,
        summary_path=summary_path,
        validation_path=validation_path,
        summary=summary,
    )


def validate_applicability_gate_graph_contract(
    contract: dict[str, Any],
    inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    structural_gates = _dict_list(contract.get("structural_gates"))
    placements = _dict_list(contract.get("authority_family_gate_placements"))
    structural_gate_ids = [str(gate.get("gate_id") or "") for gate in structural_gates]
    placement_family_ids = [str(row.get("authority_family_id") or "") for row in placements]
    all_node_ids = [*structural_gate_ids, *[_authority_family_gate_id(fid) for fid in placement_family_ids]]
    node_id_set = set(all_node_ids)
    parent_ids = [
        str(gate.get("parent_gate_id") or "")
        for gate in structural_gates
        if gate.get("parent_gate_id")
    ] + [
        str(row.get("parent_gate_id") or "")
        for row in placements
        if row.get("parent_gate_id")
    ]
    inventory_family_ids = set(_authority_family_by_id(inventory))
    placement_family_id_set = set(placement_family_ids)
    duplicated_nodes = sorted(
        node_id for node_id, count in Counter(all_node_ids).items() if count > 1
    )
    duplicated_families = sorted(
        family_id
        for family_id, count in Counter(placement_family_ids).items()
        if family_id and count > 1
    )
    checks = [
        _check(
            "applicability_gate_graph_contract_schema_version",
            contract.get("schema_version") == APPLICABILITY_GATE_GRAPH_CONTRACT_SCHEMA_VERSION,
            expected=APPLICABILITY_GATE_GRAPH_CONTRACT_SCHEMA_VERSION,
            actual=contract.get("schema_version"),
        ),
        _check(
            "applicability_gate_graph_contract_root_exists",
            str(contract.get("root_gate_id") or "") in node_id_set,
            expected=contract.get("root_gate_id"),
            actual=sorted(node_id_set),
        ),
        _check(
            "applicability_gate_graph_contract_gate_ids_unique",
            not duplicated_nodes,
            expected=[],
            actual=duplicated_nodes,
        ),
        _check(
            "applicability_gate_graph_contract_parents_resolve",
            set(parent_ids) <= node_id_set,
            expected=[],
            actual=sorted(set(parent_ids) - node_id_set),
        ),
        _check(
            "applicability_gate_graph_contract_gate_types_known",
            {
                str(gate.get("gate_type") or "")
                for gate in structural_gates
            }
            <= ALLOWED_STRUCTURAL_GATE_TYPES,
            expected=sorted(ALLOWED_STRUCTURAL_GATE_TYPES),
            actual=sorted(
                {
                    str(gate.get("gate_type") or "")
                    for gate in structural_gates
                }
                - ALLOWED_STRUCTURAL_GATE_TYPES
            ),
        ),
        _check(
            "applicability_gate_graph_contract_activation_rules_known",
            {
                str(gate.get("activation_rule") or "")
                for gate in structural_gates
            }
            <= ALLOWED_ACTIVATION_RULES,
            expected=sorted(ALLOWED_ACTIVATION_RULES),
            actual=sorted(
                {
                    str(gate.get("activation_rule") or "")
                    for gate in structural_gates
                }
                - ALLOWED_ACTIVATION_RULES
            ),
        ),
        _check(
            "applicability_gate_graph_contract_covers_all_authority_families",
            inventory_family_ids <= placement_family_id_set,
            expected=sorted(inventory_family_ids),
            actual=sorted(inventory_family_ids - placement_family_id_set),
        ),
        _check(
            "applicability_gate_graph_contract_uses_known_authority_families",
            placement_family_id_set <= inventory_family_ids,
            expected=sorted(inventory_family_ids),
            actual=sorted(placement_family_id_set - inventory_family_ids),
        ),
        _check(
            "applicability_gate_graph_contract_authority_families_unique",
            not duplicated_families,
            expected=[],
            actual=duplicated_families,
        ),
        _check(
            "applicability_gate_graph_contract_places_forest_plan_under_nfma",
            _is_descendant(
                child_gate_id="gate:nfma_active_forest_plan",
                ancestor_gate_id=_authority_family_gate_id(
                    "nfma_forest_planning_project_consistency"
                ),
                parent_by_id=_contract_parent_by_id(contract),
            ),
            expected="gate:nfma_active_forest_plan descendant of NFMA authority family gate",
            actual=_ancestor_chain(
                "gate:nfma_active_forest_plan",
                _contract_parent_by_id(contract),
            ),
        ),
    ]
    return checks


def validate_applicability_gate_graph_records(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    contract: dict[str, Any],
    inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    node_ids = {str(node.get("gate_id") or "") for node in nodes}
    edge_endpoints = {
        str(edge.get("parent_gate_id") or "")
        for edge in edges
    } | {
        str(edge.get("child_gate_id") or "")
        for edge in edges
    }
    family_gate_ids = {
        str(node.get("gate_id") or "")
        for node in nodes
        if node.get("gate_type") == "authority_family_gate"
    }
    dynamic_candidate_nodes = [
        node for node in nodes if node.get("gate_type") in ALLOWED_DYNAMIC_GATE_TYPES
    ]
    child_open_under_closed_parent = []
    node_by_id = {str(node.get("gate_id") or ""): node for node in nodes}
    for edge in edges:
        child = node_by_id.get(str(edge.get("child_gate_id") or ""))
        parent = node_by_id.get(str(edge.get("parent_gate_id") or ""))
        if not child or not parent:
            continue
        if (
            child.get("activation_state") == "open"
            and parent.get("activation_state") not in OPEN_ACTIVATION_STATES
        ):
            child_open_under_closed_parent.append(
                {
                    "parent_gate_id": parent.get("gate_id"),
                    "parent_activation_state": parent.get("activation_state"),
                    "child_gate_id": child.get("gate_id"),
                    "child_activation_state": child.get("activation_state"),
                }
            )
    return [
        _check(
            "applicability_gate_graph_records_schema_nodes_present",
            bool(nodes),
            expected="non-empty nodes",
            actual=len(nodes),
        ),
        _check(
            "applicability_gate_graph_records_edges_resolve",
            edge_endpoints <= node_ids,
            expected=[],
            actual=sorted(edge_endpoints - node_ids),
        ),
        _check(
            "applicability_gate_graph_records_root_open",
            node_by_id.get(str(contract.get("root_gate_id") or ""), {}).get(
                "activation_state"
            )
            == "open",
            expected="open",
            actual=node_by_id.get(str(contract.get("root_gate_id") or ""), {}).get(
                "activation_state"
            ),
        ),
        _check(
            "applicability_gate_graph_records_all_inventory_families_have_nodes",
            {
                _authority_family_gate_id(family_id)
                for family_id in _authority_family_by_id(inventory)
            }
            <= family_gate_ids,
            expected="one gate per authority family",
            actual=sorted(
                {
                    _authority_family_gate_id(family_id)
                    for family_id in _authority_family_by_id(inventory)
                }
                - family_gate_ids
            ),
        ),
        _check(
            "applicability_gate_graph_records_no_open_child_under_closed_parent",
            not child_open_under_closed_parent,
            expected=[],
            actual=child_open_under_closed_parent,
        ),
        _check(
            "applicability_gate_graph_records_dynamic_nodes_have_gate_type",
            {str(node.get("gate_type") or "") for node in dynamic_candidate_nodes}
            <= ALLOWED_DYNAMIC_GATE_TYPES,
            expected=sorted(ALLOWED_DYNAMIC_GATE_TYPES),
            actual=sorted(
                {str(node.get("gate_type") or "") for node in dynamic_candidate_nodes}
                - ALLOWED_DYNAMIC_GATE_TYPES
            ),
        ),
    ]


def load_applicability_gate_graph_contract(
    path: Path = DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH,
) -> dict[str, Any]:
    return _read_json(path)


def _add_static_gate_node(
    nodes: dict[str, dict[str, Any]],
    *,
    contract_gate: dict[str, Any],
    contract: dict[str, Any],
    family: dict[str, Any] | None,
    family_state: dict[str, str] | None,
    review_id: str,
    source_set_id: str | None,
) -> None:
    gate_id = str(contract_gate.get("gate_id") or "")
    gate_type = str(contract_gate.get("gate_type") or "")
    activation_rule = str(contract_gate.get("activation_rule") or "")
    family_id = str(contract_gate.get("authority_family_id") or "")
    status = "candidate"
    activation_state = "pending"
    if activation_rule == "always_open_for_ea_package":
        status = "applicable"
        activation_state = "open"
    elif family_state:
        status = family_state["gate_status"]
        activation_state = family_state["activation_state"]
    elif family and family.get("status") == "superseded":
        status = "superseded"
        activation_state = "currentness_only"
    nodes[gate_id] = {
        "gate_id": gate_id,
        "gate_type": gate_type,
        "label": str(contract_gate.get("label") or gate_id),
        "parent_gate_id": contract_gate.get("parent_gate_id"),
        "gate_status": status,
        "activation_state": activation_state,
        "child_activation_rule": activation_rule,
        "applicability_basis": contract_gate.get("applicability_basis"),
        "authority_family_id": family_id or None,
        "source_status": family.get("status") if family else contract.get("status"),
        "provenance": _compact_dict(
            {
                "review_id": review_id,
                "source_set_id": source_set_id,
                "contract_id": contract.get("contract_id"),
                "authority_family_id": family_id or None,
                "source_record_ids": family.get("source_record_ids", []) if family else [],
            }
        ),
        "metadata": _compact_dict(
            {
                "required_authority_requirement_ids": (
                    family.get("required_authority_requirement_ids", []) if family else []
                ),
                "package_fact_types": family.get("package_fact_types", []) if family else [],
                "source_evidence_requirements": (
                    family.get("source_evidence_requirements", []) if family else []
                ),
            }
        ),
    }


def _resolve_static_activation_states(nodes: dict[str, dict[str, Any]]) -> None:
    changed = True
    while changed:
        changed = False
        for node in nodes.values():
            if node["activation_state"] != "pending":
                continue
            if node.get("gate_type") == "authority_family_gate":
                continue
            parent_id = node.get("parent_gate_id")
            parent = nodes.get(str(parent_id)) if parent_id else None
            if parent is None:
                continue
            parent_activation = str(parent.get("activation_state") or "")
            if parent_activation == "open":
                node["gate_status"] = "applicable"
                node["activation_state"] = "open"
                changed = True
            elif parent_activation == "currentness_only":
                node["gate_status"] = "blocked_by_parent_currentness"
                node["activation_state"] = "blocked"
                changed = True
            elif parent_activation in {"closed", "blocked"}:
                node["gate_status"] = "blocked_by_parent_not_applicable"
                node["activation_state"] = "blocked"
                changed = True


def _add_parent_edges(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    *,
    review_id: str,
    source_set_id: str | None,
) -> None:
    for node in list(nodes.values()):
        parent_gate_id = node.get("parent_gate_id")
        if not parent_gate_id:
            continue
        _add_edge(
            edges,
            parent_gate_id=str(parent_gate_id),
            child_gate_id=str(node["gate_id"]),
            edge_type="OPENS_CHILD_GATE",
            review_id=review_id,
            source_set_id=source_set_id,
            opens_when=node.get("child_activation_rule"),
        )


def _add_dynamic_candidate_gates(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    *,
    review_id: str,
    source_set_id: str | None,
    candidate_authorities: list[dict[str, Any]],
    decisions_by_candidate_id: dict[str, dict[str, Any]],
    candidate_family_by_id: dict[str, str],
    family_gate_id_by_family: dict[str, str],
    family_ids_by_rule_id: dict[str, set[str]],
) -> None:
    plan_component_group_gate_id = "gate:nfma_forest_plan_components"
    for candidate in sorted(
        candidate_authorities,
        key=lambda item: str(item.get("candidate_authority_id") or ""),
    ):
        candidate_id = str(candidate.get("candidate_authority_id") or "")
        if not candidate_id:
            continue
        family_id = candidate_family_by_id.get(candidate_id) or _candidate_family_id(
            candidate,
            family_ids_by_rule_id=family_ids_by_rule_id,
        )
        parent_gate_id = family_gate_id_by_family.get(family_id)
        candidate_gate_type = "candidate_authority_gate"
        parent_metadata: dict[str, Any] = {}
        if candidate.get("candidate_authority_type") == "forest_plan_component":
            forest_plan = _dict(candidate.get("forest_plan"))
            plan_gate_id = _ensure_forest_plan_instance_gate(
                nodes,
                edges,
                review_id=review_id,
                source_set_id=source_set_id,
                forest_plan=forest_plan,
                parent_gate_id=plan_component_group_gate_id,
            )
            parent_gate_id = plan_gate_id
            candidate_gate_type = "forest_plan_component_gate"
            parent_metadata = {
                "forest_unit_id": forest_plan.get("forest_unit_id"),
                "active_plan_source_record_id": forest_plan.get("active_plan_source_record_id"),
                "component_id": forest_plan.get("component_id"),
                "component_type": forest_plan.get("component_type"),
                "management_area_ids": forest_plan.get("management_area_ids", []),
                "geographic_area_ids": forest_plan.get("geographic_area_ids", []),
                "overlay_ids": forest_plan.get("overlay_ids", []),
            }
        if not parent_gate_id:
            parent_gate_id = "gate:nepa_other_environmental_reviews"
        decision = decisions_by_candidate_id.get(candidate_id)
        gate_status, activation_state = _candidate_gate_state(decision)
        gate_id = _candidate_gate_id(candidate_id)
        nodes[gate_id] = {
            "gate_id": gate_id,
            "gate_type": candidate_gate_type,
            "label": _candidate_label(candidate),
            "parent_gate_id": parent_gate_id,
            "gate_status": gate_status,
            "activation_state": activation_state,
            "child_activation_rule": "open_when_applicable",
            "applicability_basis": "Candidate gate status is projected from applicability decisions when available.",
            "authority_family_id": family_id or None,
            "candidate_authority_id": candidate_id,
            "source_status": "review_candidate",
            "provenance": _compact_dict(
                {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "candidate_authority_id": candidate_id,
                    "candidate_authority_type": candidate.get("candidate_authority_type"),
                    "decision_id": decision.get("decision_id") if decision else None,
                    "source_record_ids": candidate.get("source_record_ids", []),
                }
            ),
            "metadata": _compact_dict(
                {
                    "required_package_fact_types": candidate.get(
                        "required_package_fact_types", []
                    ),
                    "positive_trigger_groups": candidate.get("positive_trigger_groups", []),
                    "negative_trigger_groups": candidate.get("negative_trigger_groups", []),
                    **parent_metadata,
                }
            ),
        }


def _resolve_dynamic_parent_edges(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    *,
    review_id: str,
    source_set_id: str | None,
) -> None:
    for node in list(nodes.values()):
        if node["gate_id"] in {edge["child_gate_id"] for edge in edges.values()}:
            continue
        parent_gate_id = node.get("parent_gate_id")
        if not parent_gate_id:
            continue
        parent = nodes.get(str(parent_gate_id))
        if parent and node["activation_state"] == "open" and parent["activation_state"] != "open":
            node["gate_status"] = "needs_adjudication"
            node["activation_state"] = "blocked"
        _add_edge(
            edges,
            parent_gate_id=str(parent_gate_id),
            child_gate_id=str(node["gate_id"]),
            edge_type="OPENS_CHILD_GATE",
            review_id=review_id,
            source_set_id=source_set_id,
            opens_when=node.get("child_activation_rule"),
        )


def _ensure_forest_plan_instance_gate(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    *,
    review_id: str,
    source_set_id: str | None,
    forest_plan: dict[str, Any],
    parent_gate_id: str,
) -> str:
    source_record_id = str(forest_plan.get("active_plan_source_record_id") or "unknown-plan")
    forest_unit_id = str(forest_plan.get("forest_unit_id") or "unknown-forest")
    gate_id = f"gate:forest_plan:{_safe_id(forest_unit_id)}:{_safe_id(source_record_id)}"
    parent = nodes.get(parent_gate_id)
    parent_open = parent and parent.get("activation_state") == "open"
    if gate_id not in nodes:
        nodes[gate_id] = {
            "gate_id": gate_id,
            "gate_type": "forest_plan_instance_gate",
            "label": "Active Forest Plan",
            "parent_gate_id": parent_gate_id,
            "gate_status": "applicable" if parent_open else "blocked_by_parent_not_applicable",
            "activation_state": "open" if parent_open else "blocked",
            "child_activation_rule": "open_when_parent_applicable",
            "applicability_basis": "A selected active Forest Plan opens component candidate gates.",
            "authority_family_id": "nfma_forest_planning_project_consistency",
            "source_status": "review_candidate",
            "provenance": _compact_dict(
                {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "forest_unit_id": forest_unit_id,
                    "active_plan_source_record_id": source_record_id,
                    "component_inventory_id": forest_plan.get("component_inventory_id"),
                    "component_inventory_sha256": forest_plan.get("component_inventory_sha256"),
                }
            ),
            "metadata": _compact_dict(
                {
                    "forest_unit_names": forest_plan.get("forest_unit_names", []),
                    "plan_version": forest_plan.get("plan_version"),
                    "component_inventory_path": forest_plan.get("component_inventory_path"),
                }
            ),
        }
    return gate_id


def _family_decision_states(
    *,
    candidate_authorities: list[dict[str, Any]],
    decisions_by_candidate_id: dict[str, dict[str, Any]],
    candidate_family_by_id: dict[str, str],
    family_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str]]:
    statuses_by_family: dict[str, list[str]] = {}
    for candidate in candidate_authorities:
        candidate_id = str(candidate.get("candidate_authority_id") or "")
        family_id = candidate_family_by_id.get(candidate_id)
        if not family_id:
            continue
        decision = decisions_by_candidate_id.get(candidate_id)
        status = _decision_status(decision)
        statuses_by_family.setdefault(family_id, []).append(status)
    states: dict[str, dict[str, str]] = {}
    for family_id, family in family_by_id.items():
        statuses = [status for status in statuses_by_family.get(family_id, []) if status]
        if "applicable" in statuses:
            states[family_id] = {"gate_status": "applicable", "activation_state": "open"}
        elif "needs_adjudication" in statuses:
            states[family_id] = {
                "gate_status": "needs_adjudication",
                "activation_state": "blocked",
            }
        elif "unresolved" in statuses:
            states[family_id] = {"gate_status": "unresolved", "activation_state": "blocked"}
        elif statuses and all(status == "not_applicable" for status in statuses):
            states[family_id] = {
                "gate_status": "not_applicable",
                "activation_state": "closed",
            }
        elif family.get("status") == "superseded":
            states[family_id] = {
                "gate_status": "superseded",
                "activation_state": "currentness_only",
            }
        else:
            states[family_id] = {"gate_status": "candidate", "activation_state": "pending"}
    return states


def _candidate_gate_state(decision: dict[str, Any] | None) -> tuple[str, str]:
    status = _decision_status(decision)
    if status == "applicable":
        return "applicable", "open"
    if status == "not_applicable":
        return "not_applicable", "closed"
    if status in {"unresolved", "needs_adjudication"}:
        return status, "blocked"
    return "candidate", "pending"


def _decision_status(decision: dict[str, Any] | None) -> str:
    if not decision:
        return ""
    status = str(decision.get("status") or decision.get("applicability_status") or "").strip()
    return status if status in FINAL_DECISION_STATUSES else ""


def _candidate_family_id(
    candidate: dict[str, Any],
    *,
    family_ids_by_rule_id: dict[str, set[str]],
) -> str:
    family_id = str(candidate.get("authority_family_id") or "").strip()
    if family_id:
        return family_id
    family_ids = [str(value) for value in candidate.get("authority_family_ids", []) if value]
    if family_ids:
        return sorted(family_ids)[0]
    rule_template = _dict(candidate.get("rule_template"))
    rule_id = str(rule_template.get("rule_id") or "").strip()
    if rule_id:
        mapped = sorted(family_ids_by_rule_id.get(rule_id, set()))
        if mapped:
            return mapped[0]
    return ""


def _candidate_label(candidate: dict[str, Any]) -> str:
    forest_plan = _dict(candidate.get("forest_plan"))
    if forest_plan:
        return str(
            forest_plan.get("section_heading")
            or forest_plan.get("component_id")
            or candidate.get("candidate_authority_id")
        )
    rule_template = _dict(candidate.get("rule_template"))
    return str(
        rule_template.get("title")
        or rule_template.get("rule_id")
        or candidate.get("candidate_authority_id")
    )


def _family_ids_by_rule_id(inventory: dict[str, Any]) -> dict[str, set[str]]:
    by_rule: dict[str, set[str]] = {}
    for family in _dict_list(inventory.get("authority_families")):
        family_id = str(family.get("family_id") or "")
        for rule_id in [
            *[str(value) for value in family.get("rule_ids", []) if value],
            *[str(value) for value in family.get("rule_template_ids", []) if value],
        ]:
            by_rule.setdefault(rule_id, set()).add(family_id)
    return by_rule


def _summary(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    contract: dict[str, Any],
    inventory: dict[str, Any],
    authority_universe: dict[str, Any],
    decisions: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    family_nodes = [node for node in nodes if node.get("gate_type") == "authority_family_gate"]
    dynamic_nodes = [
        node for node in nodes if node.get("gate_type") in ALLOWED_DYNAMIC_GATE_TYPES
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "contract_id": contract.get("contract_id"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "authority_family_gate_count": len(family_nodes),
        "inventory_authority_family_count": len(_authority_family_by_id(inventory)),
        "candidate_authority_gate_count": len(
            [
                node
                for node in dynamic_nodes
                if node.get("gate_type") == "candidate_authority_gate"
            ]
        ),
        "forest_plan_component_gate_count": len(
            [
                node
                for node in dynamic_nodes
                if node.get("gate_type") == "forest_plan_component_gate"
            ]
        ),
        "forest_plan_instance_gate_count": len(
            [
                node
                for node in dynamic_nodes
                if node.get("gate_type") == "forest_plan_instance_gate"
            ]
        ),
        "authority_universe_candidate_count": len(
            _dict_list(authority_universe.get("candidate_authorities"))
        ),
        "decision_count": len(decisions),
        "gate_type_counts": dict(Counter(str(node.get("gate_type") or "") for node in nodes)),
        "gate_status_counts": dict(Counter(str(node.get("gate_status") or "") for node in nodes)),
        "activation_state_counts": dict(
            Counter(str(node.get("activation_state") or "") for node in nodes)
        ),
        "validation_check_count": len(checks),
        "failed_check_count": len([check for check in checks if not check["passed"]]),
    }


def _input_records(paths_by_name: dict[str, Path]) -> list[dict[str, Any]]:
    records = []
    for name, path in sorted(paths_by_name.items()):
        path = Path(path)
        records.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    return records


def _check(name: str, passed: bool, *, expected: Any = None, actual: Any = None) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }


def _add_edge(
    edges: dict[str, dict[str, Any]],
    *,
    parent_gate_id: str,
    child_gate_id: str,
    edge_type: str,
    review_id: str,
    source_set_id: str | None,
    opens_when: str | None,
) -> None:
    edge_id = "edge:" + _stable_digest(edge_type, parent_gate_id, child_gate_id)
    edges[edge_id] = {
        "edge_id": edge_id,
        "edge_type": edge_type,
        "parent_gate_id": parent_gate_id,
        "child_gate_id": child_gate_id,
        "opens_when": opens_when,
        "provenance": _compact_dict(
            {
                "review_id": review_id,
                "source_set_id": source_set_id,
            }
        ),
    }


def _family_gate_id_by_family(contract: dict[str, Any]) -> dict[str, str]:
    return {
        str(row.get("authority_family_id")): _authority_family_gate_id(
            str(row.get("authority_family_id"))
        )
        for row in _dict_list(contract.get("authority_family_gate_placements"))
        if row.get("authority_family_id")
    }


def _authority_family_by_id(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(family.get("family_id")): family
        for family in _dict_list(inventory.get("authority_families"))
        if family.get("family_id")
    }


def _authority_family_gate_id(family_id: str) -> str:
    return f"gate:authority_family:{family_id}"


def _candidate_gate_id(candidate_id: str) -> str:
    return f"gate:candidate:{_safe_id(candidate_id)}"


def _contract_parent_by_id(contract: dict[str, Any]) -> dict[str, str]:
    parent_by_id = {
        str(gate.get("gate_id")): str(gate.get("parent_gate_id") or "")
        for gate in _dict_list(contract.get("structural_gates"))
        if gate.get("gate_id")
    }
    for row in _dict_list(contract.get("authority_family_gate_placements")):
        family_id = str(row.get("authority_family_id") or "")
        if family_id:
            parent_by_id[_authority_family_gate_id(family_id)] = str(
                row.get("parent_gate_id") or ""
            )
    return parent_by_id


def _is_descendant(
    *,
    child_gate_id: str,
    ancestor_gate_id: str,
    parent_by_id: dict[str, str],
) -> bool:
    gate_id = child_gate_id
    seen: set[str] = set()
    while gate_id and gate_id not in seen:
        seen.add(gate_id)
        parent = parent_by_id.get(gate_id, "")
        if parent == ancestor_gate_id:
            return True
        gate_id = parent
    return False


def _ancestor_chain(gate_id: str, parent_by_id: dict[str, str]) -> list[str]:
    chain = [gate_id]
    seen: set[str] = set()
    while gate_id and gate_id not in seen:
        seen.add(gate_id)
        parent = parent_by_id.get(gate_id, "")
        if not parent:
            break
        chain.append(parent)
        gate_id = parent
    return chain


def _safe_id(value: str) -> str:
    value = value.strip()
    if SAFE_SEGMENT_RE.match(value):
        return value
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _validate_safe_segment(value: str | None, field_name: str) -> None:
    if not value or not SAFE_SEGMENT_RE.match(value):
        raise ValueError(f"{field_name} must match {SAFE_SEGMENT_RE.pattern}: {value!r}")


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, [], {}, "")}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    path = Path(path)
    return _read_json(path) if path.exists() else {}


def _read_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stable_digest(*values: object) -> str:
    return hashlib.sha256(
        "\x1f".join(str(value) for value in values).encode("utf-8")
    ).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
