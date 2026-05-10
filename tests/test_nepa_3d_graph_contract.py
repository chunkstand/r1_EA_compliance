from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

from usfs_r1_ea_sources.nepa_3d_graph_contract import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_DISPLAY_STATUSES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_EDGE_TYPES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_LENSES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_LENS_FIELDS
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_NODE_TYPES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_READINESS_BLOCKER_TYPES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_READINESS_SEMANTIC_CLASSES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_REVIEW_READINESS_STATUSES
from usfs_r1_ea_sources.nepa_3d_graph_contract import load_nepa_3d_graph_contract
from usfs_r1_ea_sources.nepa_3d_graph_contract import validate_nepa_3d_graph
from usfs_r1_ea_sources.nepa_3d_graph_contract import validate_nepa_3d_graph_contract


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "nepa_3d_graph"


def test_nepa_3d_graph_contract_covers_milestone_1_required_types_and_states() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)

    checks = {check["name"]: check for check in validate_nepa_3d_graph_contract(contract)}

    assert all(check["passed"] for check in checks.values())
    assert REQUIRED_NODE_TYPES <= {entry["node_type"] for entry in contract["node_types"]}
    assert REQUIRED_EDGE_TYPES <= {entry["edge_type"] for entry in contract["edge_types"]}
    assert REQUIRED_DISPLAY_STATUSES <= set(contract["display_status_values"])
    assert REQUIRED_REVIEW_READINESS_STATUSES <= set(contract["review_readiness_status_values"])
    assert REQUIRED_READINESS_BLOCKER_TYPES <= set(contract["readiness_blocker_types"])
    assert REQUIRED_READINESS_SEMANTIC_CLASSES <= set(contract["readiness_semantic_classes"])
    assert REQUIRED_LENS_FIELDS <= set(contract["lens_metadata_contract"]["required_fields"])
    assert REQUIRED_LENSES <= set(contract["lens_metadata_contract"]["required_lenses"])
    assert {"source_set", "review"} <= set(contract["export_scopes"])


def test_minimal_source_set_graph_fixture_validates_against_contract() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = _read_json(FIXTURE_DIR / "minimal_source_set_graph.json")

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert all(check["passed"] for check in checks.values())
    assert graph["export_scope"]["scope_type"] == "source_set"
    assert "review_id" not in graph["export_scope"]


def test_minimal_review_graph_fixture_validates_against_contract() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = _read_json(FIXTURE_DIR / "minimal_review_graph.json")

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert all(check["passed"] for check in checks.values())
    assert graph["export_scope"]["scope_type"] == "review"
    assert graph["export_scope"]["review_id"] == "review-test"


def test_graph_contract_validation_fails_on_unknown_status_and_missing_edge_endpoint() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = deepcopy(_read_json(FIXTURE_DIR / "minimal_source_set_graph.json"))
    graph["nodes"][0]["display_status"] = "hidden_technical_state"
    graph["edges"][0]["target_node_id"] = "authority_family:missing"

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert not checks["nepa_3d_graph_uses_known_display_statuses"]["passed"]
    assert not checks["nepa_3d_graph_edges_resolve_to_nodes"]["passed"]
    assert not checks["nepa_3d_graph_summary_matches_records"]["passed"]
    assert checks["nepa_3d_graph_uses_known_display_statuses"]["actual"] == [
        "hidden_technical_state"
    ]


def test_graph_contract_validation_fails_on_missing_provenance_lens_and_edge_type() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = deepcopy(_read_json(FIXTURE_DIR / "minimal_source_set_graph.json"))
    source_node = next(
        node for node in graph["nodes"] if node["node_id"] == "source_record:R1EA-001"
    )
    del source_node["provenance"]["citation_label"]
    graph["edges"][1]["source_node_id"] = "source_set:source-set-test"
    del graph["lens_metadata"][0]["description"]
    graph["lens_metadata"] = [
        lens for lens in graph["lens_metadata"] if lens["lens_id"] != "readiness_blockers"
    ]

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert not checks["nepa_3d_graph_nodes_have_required_provenance"]["passed"]
    assert not checks["nepa_3d_graph_edges_match_declared_endpoint_types"]["passed"]
    assert not checks["nepa_3d_graph_lens_metadata_shape"]["passed"]
    assert not checks["nepa_3d_graph_lens_metadata_required_lenses_present"]["passed"]
    assert checks["nepa_3d_graph_nodes_have_required_provenance"]["actual"] == [
        {
            "node_id": "source_record:R1EA-001",
            "node_type": "source_record",
            "missing": ["citation_label"],
        }
    ]


def test_graph_contract_validation_fails_on_missing_red_semantic_classes() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = deepcopy(_read_json(FIXTURE_DIR / "minimal_source_set_graph.json"))
    blocker_node = next(
        node for node in graph["nodes"] if node["node_id"] == "readiness_blocker:superseded_source:R1EA-220"
    )
    blocked_edge = next(
        edge
        for edge in graph["edges"]
        if edge["edge_id"]
        == "forest_unit:other-test-forest->forest_plan:other-test-forest:R1EA-001:HAS_FOREST_PLAN"
    )
    blocker_edge = next(
        edge
        for edge in graph["edges"]
        if edge["edge_id"]
        == "source_record:R1EA-220->readiness_blocker:superseded_source:R1EA-220:BLOCKED_BY"
    )
    blocker_node["readiness_semantic_class"] = "none"
    blocked_edge["readiness_semantic_class"] = "none"
    blocker_edge["readiness_semantic_class"] = "blocked_relationship_edge"

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert not checks["nepa_3d_graph_explicitly_classifies_red_semantics"]["passed"]
    assert checks["nepa_3d_graph_explicitly_classifies_red_semantics"]["actual"] == [
        {
            "record_kind": "node",
            "record_id": "readiness_blocker:superseded_source:R1EA-220",
            "expected": "synthetic_blocker_node",
            "actual": "none",
        },
        {
            "record_kind": "edge",
            "record_id": "source_record:R1EA-220->readiness_blocker:superseded_source:R1EA-220:BLOCKED_BY",
            "expected": "blocker_relationship_edge",
            "actual": "blocked_relationship_edge",
        },
        {
            "record_kind": "edge",
            "record_id": "forest_unit:other-test-forest->forest_plan:other-test-forest:R1EA-001:HAS_FOREST_PLAN",
            "expected": "blocked_relationship_edge",
            "actual": "none",
        },
    ]


def test_contract_validation_fails_when_contract_drops_milestone_1_requirements() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    broken = deepcopy(contract)
    source_record = next(
        node_type
        for node_type in broken["node_types"]
        if node_type["node_type"] == "source_record"
    )
    source_record["required_provenance_fields"] = []
    supports_rule = next(
        edge_type
        for edge_type in broken["edge_types"]
        if edge_type["edge_type"] == "SUPPORTS_RULE_TEMPLATE"
    )
    supports_rule["source_node_types"] = []
    broken["lens_metadata_contract"]["required_fields"].remove("description")
    broken["lens_metadata_contract"]["required_lenses"].remove("readiness_blockers")
    broken["readiness_semantic_classes"].remove("blocked_relationship_edge")

    checks = {check["name"]: check for check in validate_nepa_3d_graph_contract(broken)}

    assert not checks["nepa_3d_graph_contract_defines_node_provenance"]["passed"]
    assert not checks["nepa_3d_graph_contract_defines_edge_endpoint_types"]["passed"]
    assert not checks["nepa_3d_graph_contract_defines_lens_metadata_shape"]["passed"]
    assert not checks["nepa_3d_graph_contract_defines_required_lenses"]["passed"]
    assert not checks["nepa_3d_graph_contract_names_readiness_semantic_classes"]["passed"]


def test_review_graph_contract_requires_review_id_for_review_scope() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = deepcopy(_read_json(FIXTURE_DIR / "minimal_review_graph.json"))
    del graph["export_scope"]["review_id"]

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert not checks["nepa_3d_graph_review_scope_has_review_id"]["passed"]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
