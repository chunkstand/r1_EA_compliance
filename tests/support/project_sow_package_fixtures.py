from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources.project_sow_package import run_project_sow_package
from usfs_r1_ea_sources.project_sow_package import validate_project_sow_intake


REPO_ROOT = Path(__file__).resolve().parents[2]
INTAKE_PATH = REPO_ROOT / "config" / "fixtures" / "project_sow" / "east_crazies_land_exchange_intake.json"
TEMPLATE_PATH = REPO_ROOT / "config" / "templates" / "project_sow_land_exchange_intake_template.json"
INTAKE_SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "project_sow_intake_v0.schema.json"
EVAL_CONFIG_PATH = REPO_ROOT / "config" / "project_sow_eval_proving_intakes_v1.json"
PROPOSED_ACTION_FIXTURE_PATH = (
    REPO_ROOT
    / "config"
    / "fixtures"
    / "project_sow"
    / "proposed_action_text"
    / "red_rock_ridge_land_exchange_proposed_action.txt"
)
AMBIGUOUS_PROPOSED_ACTION_FIXTURE_PATH = (
    REPO_ROOT
    / "config"
    / "fixtures"
    / "project_sow"
    / "proposed_action_text"
    / "ambiguous_land_adjustment_proposed_action.txt"
)
EXPECTED_DRAFT_METADATA_PATH = (
    REPO_ROOT
    / "config"
    / "fixtures"
    / "project_sow"
    / "proposed_action_text"
    / "red_rock_ridge_expected_draft_metadata.json"
)


def _has_canonical_graph_path(graph: dict, area_id: str) -> bool:
    resource_node_id = f"resource_area:{area_id}"
    node_types = {node["node_id"]: node["node_type"] for node in graph["nodes"]}
    for trigger_edge in graph["edges"]:
        if trigger_edge["edge_type"] != "TRIGGERS_RESOURCE_AREA":
            continue
        if trigger_edge["to_node_id"] != resource_node_id:
            continue
        evidence_node_id = trigger_edge["from_node_id"]
        supported_edges = [
            edge
            for edge in graph["edges"]
            if edge["edge_type"] == "SUPPORTED_BY"
            and edge["to_node_id"] == evidence_node_id
            and node_types.get(edge["from_node_id"]) == "action_element"
        ]
        if not supported_edges:
            continue
        action_node_ids = {edge["from_node_id"] for edge in supported_edges}
        if not any(
            edge["edge_type"] == "HAS_ACTION_ELEMENT"
            and edge["to_node_id"] in action_node_ids
            and node_types.get(edge["from_node_id"]) == "proposed_action"
            for edge in graph["edges"]
        ):
            continue
        if _edge_exists(
            graph,
            edge_type="COVERED_BY_SOW_SCOPE",
            from_node_id=resource_node_id,
            to_node_type="sow_scope",
        ):
            return True
    return False


def _edge_exists(
    graph: dict,
    *,
    edge_type: str,
    from_node_id: str,
    to_node_id: str | None = None,
    to_node_type: str | None = None,
) -> bool:
    node_types = {node["node_id"]: node["node_type"] for node in graph["nodes"]}
    return any(
        edge["edge_type"] == edge_type
        and edge["from_node_id"] == from_node_id
        and (to_node_id is None or edge["to_node_id"] == to_node_id)
        and (to_node_type is None or node_types.get(edge["to_node_id"]) == to_node_type)
        for edge in graph["edges"]
    )


def _completed_project_sow_adjudication(template_path: Path) -> dict:
    adjudication = json.loads(template_path.read_text())
    for item in adjudication["items"]:
        item["adjudicated_at"] = "2026-05-07"
        item["adjudicated_by"] = ["reviewer@example.test"]
        item["decision_source"] = "fixture reviewer worklist"
        item["rationale"] = "Fixture reviewer decision for deterministic replay."
        item["decision"] = (
            "out_of_scope"
            if item["item_type"] == "optional_deliverable_decision"
            else "accepted"
        )
    adjudication["reviewer_metadata"] = {
        "review_status": "complete",
        "reviewed_at": "2026-05-07",
        "reviewed_by": ["reviewer@example.test"],
        "review_source": "fixture reviewer worklist",
    }
    return adjudication


def _run_with_intake(tmp_path: Path, intake: dict, filename: str):
    intake_path = tmp_path / filename
    intake_path.write_text(json.dumps(intake), encoding="utf-8")
    return run_project_sow_package(
        intake_path=intake_path,
        output_dir=tmp_path / "source_library",
    )


def _validate_with_intake(tmp_path: Path, intake: dict, filename: str):
    intake_path = tmp_path / filename
    intake_path.write_text(json.dumps(intake), encoding="utf-8")
    return validate_project_sow_intake(intake_path=intake_path)


def _failed_checks(result) -> dict:
    return {
        check["name"]: check
        for check in result.summary["failed_validation_checks"]
        if not check["passed"]
    }
