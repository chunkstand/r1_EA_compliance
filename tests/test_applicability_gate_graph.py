from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.applicability_gate_graph import (
    DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH,
)
from usfs_r1_ea_sources.applicability_gate_graph import DEFAULT_AUTHORITY_INVENTORY_PATH
from usfs_r1_ea_sources.applicability_gate_graph import build_applicability_gate_graph
from usfs_r1_ea_sources.applicability_gate_graph import (
    load_applicability_gate_graph_contract,
)
from usfs_r1_ea_sources.applicability_gate_graph import (
    validate_applicability_gate_graph_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
NFMA_GATE_ID = "gate:authority_family:nfma_forest_planning_project_consistency"


def test_gate_graph_contract_places_every_authority_family_and_forest_plan_under_nfma() -> None:
    contract = load_applicability_gate_graph_contract(
        REPO_ROOT / DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH
    )
    inventory = _read_json(REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH)

    checks = {
        check["name"]: check
        for check in validate_applicability_gate_graph_contract(contract, inventory)
    }

    assert all(check["passed"] for check in checks.values())
    assert len(contract["authority_family_gate_placements"]) == len(
        inventory["authority_families"]
    )
    assert checks[
        "applicability_gate_graph_contract_places_forest_plan_under_nfma"
    ]["passed"]


def test_gate_graph_builds_review_overlay_and_expands_forest_plan_components_under_nfma() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "gate-graph-unit"
        applicability_dir = output_dir / "reviews" / review_id / "applicability"
        applicability_dir.mkdir(parents=True)
        authority_universe_path = applicability_dir / "authority_universe_snapshot.json"
        decisions_path = applicability_dir / "applicability_decisions.jsonl"
        component_candidate_id = "forest-plan-component:inventory-v1:STD-1"
        cwa_candidate_id = "authority-family-template:test:v1:clean_water_act_wotus_permits:cwa"
        _write_json(
            authority_universe_path,
            {
                "schema_version": "authority-universe-snapshot-v0",
                "review_id": review_id,
                "source_set_id": "source-set-gate",
                "candidate_authorities": [
                    {
                        "candidate_authority_id": component_candidate_id,
                        "candidate_authority_type": "forest_plan_component",
                        "authority_family_id": "nfma_forest_planning_project_consistency",
                        "authority_family_ids": ["nfma_forest_planning_project_consistency"],
                        "authority_category": "forest_plan",
                        "source_record_ids": ["R1PLAN-test-001"],
                        "required_package_fact_types": ["forest_unit", "management_area"],
                        "positive_trigger_groups": [["management area 1"]],
                        "forest_plan": {
                            "forest_unit_id": "test-forest",
                            "forest_unit_names": ["Test Forest"],
                            "active_plan_source_record_id": "R1PLAN-test-001",
                            "component_inventory_id": "inventory-v1",
                            "component_inventory_path": "component_inventory.json",
                            "component_inventory_sha256": "abc123",
                            "component_id": "STD-1",
                            "component_type": "standard",
                            "section_heading": "Standard 1",
                            "management_area_ids": ["mgmt-ma-1"],
                            "geographic_area_ids": [],
                            "overlay_ids": [],
                        },
                    },
                    {
                        "candidate_authority_id": cwa_candidate_id,
                        "candidate_authority_type": "authority_family_rule_template",
                        "authority_family_id": "clean_water_act_wotus_permits",
                        "authority_category": "law",
                        "source_record_ids": ["R1EA-082"],
                        "required_package_fact_types": ["permit", "resource_topic"],
                        "rule_template": {
                            "rule_id": "clean_water_act_wotus_permits_authority_template",
                            "title": "Clean Water Act permits",
                        },
                    },
                ],
            },
        )
        _write_jsonl(
            decisions_path,
            [
                {
                    "decision_id": "decision:nfma-component",
                    "candidate_authority_id": component_candidate_id,
                    "status": "applicable",
                },
                {
                    "decision_id": "decision:cwa",
                    "candidate_authority_id": cwa_candidate_id,
                    "status": "not_applicable",
                },
            ],
        )

        result = build_applicability_gate_graph(
            output_dir=output_dir,
            review_id=review_id,
            authority_universe_path=authority_universe_path,
            decisions_path=decisions_path,
            gate_graph_contract_path=REPO_ROOT / DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH,
            authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
        )

        graph = _read_json(result.gate_graph_path)
        nodes_by_id = {node["gate_id"]: node for node in graph["nodes"]}
        component_gate_id = _gate_id_for_candidate(graph, component_candidate_id)
        cwa_gate_id = _gate_id_for_candidate(graph, cwa_candidate_id)
        component_parent = nodes_by_id[component_gate_id]["parent_gate_id"]

        assert result.summary["passed"]
        assert nodes_by_id[NFMA_GATE_ID]["gate_status"] == "applicable"
        assert nodes_by_id[NFMA_GATE_ID]["activation_state"] == "open"
        assert nodes_by_id["gate:nfma_active_forest_plan"]["activation_state"] == "open"
        assert nodes_by_id[component_parent]["gate_type"] == "forest_plan_instance_gate"
        assert nodes_by_id[component_gate_id]["activation_state"] == "open"
        assert nodes_by_id[
            "gate:authority_family:clean_water_act_wotus_permits"
        ]["activation_state"] == "closed"
        assert nodes_by_id[cwa_gate_id]["activation_state"] == "closed"


def test_gate_graph_keeps_family_without_decision_pending() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "gate-graph-pending"
        applicability_dir = output_dir / "reviews" / review_id / "applicability"
        applicability_dir.mkdir(parents=True)
        authority_universe_path = applicability_dir / "authority_universe_snapshot.json"
        _write_json(
            authority_universe_path,
            {
                "schema_version": "authority-universe-snapshot-v0",
                "review_id": review_id,
                "source_set_id": "source-set-gate",
                "candidate_authorities": [],
            },
        )

        result = build_applicability_gate_graph(
            output_dir=output_dir,
            review_id=review_id,
            authority_universe_path=authority_universe_path,
            gate_graph_contract_path=REPO_ROOT / DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH,
            authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
        )

        graph = _read_json(result.gate_graph_path)
        nodes_by_id = {node["gate_id"]: node for node in graph["nodes"]}

        assert result.summary["passed"]
        assert nodes_by_id[
            "gate:authority_family:clean_water_act_wotus_permits"
        ]["activation_state"] == "pending"
        assert nodes_by_id[
            "gate:authority_family:forest_service_nepa_36cfr_220_reserved_superseded"
        ]["activation_state"] == "currentness_only"


def _gate_id_for_candidate(graph: dict, candidate_id: str) -> str:
    for node in graph["nodes"]:
        if node.get("candidate_authority_id") == candidate_id:
            return str(node["gate_id"])
    raise AssertionError(f"Missing candidate gate for {candidate_id}")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
