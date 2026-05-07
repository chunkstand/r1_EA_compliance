from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources.project_sow_package import DEFAULT_AUTHORITY_INVENTORY_PATH
from usfs_r1_ea_sources.project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package


REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = REPO_ROOT / "config" / "fixtures" / "project_sow" / "east_crazies_land_exchange_intake.json"


def test_project_sow_package_generates_land_exchange_resource_scopes(tmp_path: Path) -> None:
    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["output_written"] is True
    assert result.package_path.exists()
    assert result.markdown_path.exists()
    assert result.manifest_path.exists()

    package = json.loads(result.package_path.read_text())
    scope_ids = {scope["resource_scope_id"] for scope in package["resource_scope_records"]}
    assert {
        "nepa_project_management",
        "lands_realty_land_exchange",
        "forest_plan_consistency",
        "wildlife_species_botany",
        "cultural_tribal_resources",
        "hydrology_wetlands_water_quality",
        "roads_access_recreation_designated_areas",
        "vegetation_soils_air_quality",
        "minerals_energy_hazardous_materials",
        "public_involvement_coordination",
    }.issubset(scope_ids)
    assert package["validation"]["passed"] is True
    assert package["manifest"]["input_hashes"]["intake_sha256"]

    authority_ids = {
        row["authority_family_id"] for row in package["authority_requirement_matrix"]
    }
    assert "land_exchange_statutory_authorities" in authority_ids
    assert "nfma_forest_planning_project_consistency" in authority_ids

    resource_matrix = {
        row["resource_area_id"]: row for row in package["resource_analysis_matrix"]
    }
    assert resource_matrix["aquatic_resources"]["actual_specialist_reports"][0]["title"] == (
        "2024 Aquatics Report.pdf"
    )
    assert resource_matrix["climate_carbon"]["selected_resource_scope_ids"] == [
        "vegetation_soils_air_quality"
    ]
    assert resource_matrix["climate_carbon"]["actual_specialist_reports"][0]["title"] == (
        "2024 Carbon Summary.pdf"
    )
    assert resource_matrix["roads_trails_access"]["selected_resource_scope_ids"] == [
        "roads_access_recreation_designated_areas"
    ]
    assert resource_matrix["tribal_relations"]["actual_specialist_reports"][0]["title"] == (
        "2024 Tribal Relations.pdf"
    )
    graph = package["intake_evidence_graph"]
    assert graph["schema_version"] == "project-sow-intake-evidence-graph-v0"
    assert graph["node_count"] > 0
    assert graph["edge_count"] > 0
    assert {node["node_type"] for node in graph["nodes"]}.issuperset(
        {
            "project",
            "proposed_action",
            "action_element",
            "evidence_ref",
            "resource_area",
            "sow_scope",
            "expected_deliverable",
            "observed_specialist_report",
        }
    )
    assert {edge["edge_type"] for edge in graph["edges"]}.issuperset(
        {
            "HAS_PROPOSED_ACTION",
            "HAS_ACTION_ELEMENT",
            "SUPPORTED_BY",
            "TRIGGERS_RESOURCE_AREA",
            "COVERED_BY_SOW_SCOPE",
            "REQUIRES_DELIVERABLE",
            "OBSERVED_REPORT_COVERS_RESOURCE_AREA",
        }
    )
    expected_area_ids = {
        row["resource_area_id"]
        for row in package["resource_analysis_matrix"]
        if row["expected_from_proposed_action"]
    }
    assert expected_area_ids
    assert all(_has_canonical_graph_path(graph, area_id) for area_id in expected_area_ids)
    assert _edge_exists(
        graph,
        edge_type="OBSERVED_REPORT_COVERS_RESOURCE_AREA",
        from_node_id="observed_specialist_report:ecid_carbon_summary_2024",
        to_node_id="resource_area:climate_carbon",
    )
    assert _edge_exists(
        graph,
        edge_type="COVERED_BY_SOW_SCOPE",
        from_node_id="resource_area:climate_carbon",
        to_node_id="sow_scope:vegetation_soils_air_quality",
    )
    observed_report_area_statuses = [
        row["coverage_status"]
        for row in package["resource_analysis_matrix"]
        if row["actual_specialist_reports"]
    ]
    assert "missing_sow_scope" not in observed_report_area_statuses
    assert "observed_not_derived_from_proposed_action" not in observed_report_area_statuses
    assert package["missing_resource_area_requests"] == []

    markdown = result.markdown_path.read_text()
    assert "Requirements Package" in markdown
    assert "Lands, realty, and land exchange case requirements" in markdown
    assert "Resource Analysis Coverage" in markdown
    assert "Intake Evidence Graph" in markdown
    assert "2024 Carbon Summary.pdf" in markdown
    assert "This generated package scopes specialist work" in markdown


def test_project_sow_package_fails_unknown_authority_family(tmp_path: Path) -> None:
    resource_config = json.loads((REPO_ROOT / DEFAULT_RESOURCE_SCOPE_CONFIG_PATH).read_text())
    resource_config["resource_scopes"][0]["authority_family_ids"].append("missing_authority")
    bad_config_path = tmp_path / "bad_resource_config.json"
    bad_config_path.write_text(json.dumps(resource_config), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
        resource_scope_config_path=bad_config_path,
        authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
    )

    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 1


def test_project_sow_package_fails_when_observed_report_not_derived_from_action(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    intake["resource_analysis_expectations"] = [
        row
        for row in intake["resource_analysis_expectations"]
        if row["resource_area_id"] != "climate_carbon"
    ]
    for element in intake["proposed_action_elements"]:
        element["resource_area_ids"] = [
            area_id
            for area_id in element.get("resource_area_ids", [])
            if area_id != "climate_carbon"
        ]
    intake_path = tmp_path / "missing_climate_action_intake.json"
    intake_path.write_text(json.dumps(intake), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=intake_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is False
    failed_checks = {
        check["name"]: check
        for check in result.summary["failed_validation_checks"]
        if not check["passed"]
    }
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 2
    assert set(failed_checks) == {
        "intake_evidence_graph_observed_reports_have_supported_resource_paths",
        "observed_specialist_reports_match_proposed_action_resource_areas",
    }
    assert failed_checks[
        "observed_specialist_reports_match_proposed_action_resource_areas"
    ]["details"] == {"resource_area_ids": ["climate_carbon"]}
    assert failed_checks[
        "intake_evidence_graph_observed_reports_have_supported_resource_paths"
    ]["details"] == {"report_resource_area_ids": ["ecid-carbon-summary-2024:climate_carbon"]}


def test_project_sow_package_fails_when_action_element_lacks_evidence_ref(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    for element in intake["proposed_action_elements"]:
        if element["action_element_id"] == "climate_carbon_analysis":
            element["evidence_refs"] = []
    intake_path = tmp_path / "missing_climate_evidence_intake.json"
    intake_path.write_text(json.dumps(intake), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=intake_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    failed_checks = {
        check["name"]: check
        for check in result.summary["failed_validation_checks"]
        if not check["passed"]
    }
    assert result.summary["validation_failure_count"] == 3
    assert set(failed_checks) == {
        "intake_evidence_graph_action_elements_have_evidence_refs",
        "intake_evidence_graph_observed_reports_have_supported_resource_paths",
        "intake_evidence_graph_resource_area_paths_complete",
    }
    assert failed_checks[
        "intake_evidence_graph_action_elements_have_evidence_refs"
    ]["details"] == {"action_element_ids": ["climate_carbon_analysis"]}
    assert failed_checks["intake_evidence_graph_resource_area_paths_complete"][
        "details"
    ] == {"resource_area_ids": ["climate_carbon"]}
    assert failed_checks[
        "intake_evidence_graph_observed_reports_have_supported_resource_paths"
    ]["details"] == {"report_resource_area_ids": ["ecid-carbon-summary-2024:climate_carbon"]}


def test_project_sow_package_fails_duplicate_evidence_ref_graph_id(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    duplicate_evidence_ref_id = "ecid-final-ea-section-3-11-climate-carbon"
    for element in intake["proposed_action_elements"]:
        if element["action_element_id"] == "water_rights_transfer":
            element["evidence_refs"][0]["evidence_ref_id"] = duplicate_evidence_ref_id
    intake_path = tmp_path / "duplicate_evidence_ref_id_intake.json"
    intake_path.write_text(json.dumps(intake), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=intake_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    failed_checks = {
        check["name"]: check
        for check in result.summary["failed_validation_checks"]
        if not check["passed"]
    }
    duplicate_node_id = "evidence_ref:ecid_final_ea_section_3_11_climate_carbon"
    assert result.summary["validation_failure_count"] == 1
    assert set(failed_checks) == {"intake_evidence_graph_node_ids_unique"}
    assert failed_checks["intake_evidence_graph_node_ids_unique"]["details"] == {
        "duplicate_input_node_ids": [duplicate_node_id],
        "duplicate_node_ids": [duplicate_node_id],
    }


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
