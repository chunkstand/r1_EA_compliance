from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

from usfs_r1_ea_sources.nepa_3d_graph_contract import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_DISPLAY_STATUSES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_EDGE_TYPES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_NODE_TYPES
from usfs_r1_ea_sources.nepa_3d_graph_contract import REQUIRED_READINESS_BLOCKER_TYPES
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


def test_review_graph_contract_requires_review_id_for_review_scope() -> None:
    contract = load_nepa_3d_graph_contract(REPO_ROOT / DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH)
    graph = deepcopy(_read_json(FIXTURE_DIR / "minimal_review_graph.json"))
    del graph["export_scope"]["review_id"]

    checks = {check["name"]: check for check in validate_nepa_3d_graph(graph, contract)}

    assert not checks["nepa_3d_graph_review_scope_has_review_id"]["passed"]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
