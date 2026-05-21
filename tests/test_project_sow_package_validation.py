from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources import project_sow_package as project_sow
from usfs_r1_ea_sources.project_sow_package import DEFAULT_AUTHORITY_INVENTORY_PATH
from usfs_r1_ea_sources.project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package

from tests.support.project_sow_package_fixtures import (
    INTAKE_PATH,
    REPO_ROOT,
    _failed_checks,
    _run_with_intake,
)


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
    intake["proposed_action_elements"] = [
        element
        for element in intake["proposed_action_elements"]
        if element.get("resource_area_ids")
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
    assert result.summary["validation_failure_count"] == 4
    assert set(failed_checks) == {
        "intake_schema_shape_valid",
        "intake_evidence_graph_action_elements_have_evidence_refs",
        "intake_evidence_graph_observed_reports_have_supported_resource_paths",
        "intake_evidence_graph_resource_area_paths_complete",
    }
    assert failed_checks["intake_schema_shape_valid"]["details"] == {
        "errors": [
            "proposed_action_elements[14].evidence_refs: must contain at least one item"
        ]
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


def test_project_sow_package_fails_unconfigured_resource_area_path(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    intake["proposed_action_elements"].append(
        {
            "action_element_id": "unconfigured_resource_probe",
            "description": "Probe a resource area that has no configured SOW scope.",
            "evidence_refs": [
                {
                    "evidence_ref_id": "unconfigured-resource-probe-evidence",
                    "locator": "Test fixture",
                    "source_record_id": "TEST-PACKAGE-001",
                    "summary": "Evidence for an intentionally unconfigured resource area.",
                    "title": "Unconfigured Resource Probe.pdf",
                }
            ],
            "resource_area_ids": ["unconfigured_resource_area"],
            "resource_indicator_keys": [],
        }
    )

    result = _run_with_intake(tmp_path, intake, "unconfigured_resource_area_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 3
    assert set(failed_checks) == {
        "expected_resource_areas_have_sow_scope",
        "expected_resource_areas_resolve_to_scope_config",
        "intake_evidence_graph_resource_area_paths_complete",
    }
    expected_details = {"resource_area_ids": ["unconfigured_resource_area"]}
    assert failed_checks["expected_resource_areas_have_sow_scope"]["details"] == expected_details
    assert failed_checks["expected_resource_areas_resolve_to_scope_config"][
        "details"
    ] == expected_details
    assert failed_checks["intake_evidence_graph_resource_area_paths_complete"][
        "details"
    ] == expected_details


def test_project_sow_package_fails_action_element_with_evidence_but_no_resource_area(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    intake["proposed_action_elements"].append(
        {
            "action_element_id": "context_without_resource_area",
            "description": "Evidence-bearing context that does not trigger a resource area.",
            "evidence_refs": [
                {
                    "evidence_ref_id": "context-without-resource-area-evidence",
                    "locator": "Test fixture",
                    "source_record_id": "TEST-PACKAGE-002",
                    "summary": "Evidence that should not stand alone without a triggered resource area.",
                    "title": "Context Without Resource Area.pdf",
                }
            ],
            "resource_area_ids": [],
            "resource_indicator_keys": [],
        }
    )

    result = _run_with_intake(tmp_path, intake, "context_without_resource_area_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 2
    assert set(failed_checks) == {
        "intake_schema_shape_valid",
        "intake_evidence_graph_action_elements_trigger_resource_areas",
    }
    assert failed_checks["intake_schema_shape_valid"]["details"] == {
        "errors": [
            "proposed_action_elements[16].resource_area_ids: must contain at least one item"
        ]
    }
    assert failed_checks[
        "intake_evidence_graph_action_elements_trigger_resource_areas"
    ]["details"] == {"action_element_ids": ["context_without_resource_area"]}


def test_project_sow_package_fails_duplicate_observed_report_graph_id(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    intake["observed_specialist_reports"][1]["report_id"] = intake[
        "observed_specialist_reports"
    ][0]["report_id"]

    result = _run_with_intake(tmp_path, intake, "duplicate_observed_report_id_intake.json")

    failed_checks = _failed_checks(result)
    duplicate_node_id = "observed_specialist_report:ecid_mineral_potential_report_2023"
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 1
    assert set(failed_checks) == {"intake_evidence_graph_node_ids_unique"}
    assert failed_checks["intake_evidence_graph_node_ids_unique"]["details"] == {
        "duplicate_input_node_ids": [duplicate_node_id],
        "duplicate_node_ids": [duplicate_node_id],
    }


def test_project_sow_package_fails_duplicate_deliverable_graph_id(
    tmp_path: Path,
) -> None:
    resource_config = json.loads((REPO_ROOT / DEFAULT_RESOURCE_SCOPE_CONFIG_PATH).read_text())
    for scope in resource_config["resource_scopes"]:
        if scope["resource_scope_id"] == "nepa_project_management":
            scope["required_deliverables"].append(scope["required_deliverables"][0])
            break
    bad_config_path = tmp_path / "duplicate_deliverable_resource_config.json"
    bad_config_path.write_text(json.dumps(resource_config), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
        resource_scope_config_path=bad_config_path,
        authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
    )

    failed_checks = _failed_checks(result)
    duplicate_node_id = (
        "expected_deliverable:nepa_project_management:project-initiation-checklist"
    )
    duplicate_edge_id = (
        "REQUIRES_DELIVERABLE:sow_scope:nepa_project_management->"
        "expected_deliverable:nepa_project_management:project-initiation-checklist"
    )
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 2
    assert set(failed_checks) == {
        "intake_evidence_graph_edge_ids_unique",
        "intake_evidence_graph_node_ids_unique",
    }
    assert failed_checks["intake_evidence_graph_node_ids_unique"]["details"] == {
        "duplicate_input_node_ids": [duplicate_node_id],
        "duplicate_node_ids": [duplicate_node_id],
    }
    assert failed_checks["intake_evidence_graph_edge_ids_unique"]["details"] == {
        "duplicate_edge_ids": [duplicate_edge_id],
        "duplicate_input_edge_ids": [duplicate_edge_id],
    }


def test_project_sow_graph_validation_reports_dangling_edge(tmp_path: Path) -> None:
    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    package = json.loads(result.package_path.read_text())
    graph = json.loads(json.dumps(package["intake_evidence_graph"]))
    dangling_edge = {
        "edge_id": "BROKEN:missing_node->resource_area:climate_carbon",
        "edge_type": "BROKEN",
        "from_node_id": "missing_node",
        "to_node_id": "resource_area:climate_carbon",
    }
    graph["edges"].append(dangling_edge)
    graph["edge_count"] += 1
    intake = json.loads(INTAKE_PATH.read_text())

    validation_checks = project_sow._intake_graph_validation_checks(graph, intake, [])
    failed_checks = {
        check["name"]: check for check in validation_checks if not check["passed"]
    }

    assert set(failed_checks) == {"intake_evidence_graph_edges_resolve"}
    assert failed_checks["intake_evidence_graph_edges_resolve"]["details"] == {
        "dangling_edge_ids": [dangling_edge["edge_id"]]
    }


def test_project_sow_package_fails_land_exchange_without_federal_land_action(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    intake["federal_land_actions"] = []

    result = _run_with_intake(tmp_path, intake, "no_federal_land_action_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 2
    assert set(failed_checks) == {
        "land_exchange_intake_has_federal_land_actions",
        "required_intake_fields_present",
    }
    assert failed_checks["required_intake_fields_present"]["details"] == {
        "missing_fields": ["federal_land_actions"]
    }
    assert failed_checks["land_exchange_intake_has_federal_land_actions"]["details"] == {
        "federal_land_action_count": 0,
        "project_type": "land_exchange",
    }


def test_project_sow_package_fails_selected_scope_missing_contract_fields(
    tmp_path: Path,
) -> None:
    resource_config = json.loads((REPO_ROOT / DEFAULT_RESOURCE_SCOPE_CONFIG_PATH).read_text())
    for scope in resource_config["resource_scopes"]:
        if scope["resource_scope_id"] == "nepa_project_management":
            del scope["acceptance_criteria"]
            break
    bad_config_path = tmp_path / "missing_contract_fields_resource_config.json"
    bad_config_path.write_text(json.dumps(resource_config), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
        resource_scope_config_path=bad_config_path,
        authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
    )

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert set(failed_checks) == {"selected_resource_scopes_have_contract_fields"}
    assert failed_checks["selected_resource_scopes_have_contract_fields"]["details"] == {
        "missing_contract_fields": [
            {
                "missing_fields": ["acceptance_criteria"],
                "resource_scope_id": "nepa_project_management",
            }
        ]
    }


def test_project_sow_package_optional_deliverables_do_not_satisfy_required_gate(
    tmp_path: Path,
) -> None:
    resource_config = json.loads((REPO_ROOT / DEFAULT_RESOURCE_SCOPE_CONFIG_PATH).read_text())
    for scope in resource_config["resource_scopes"]:
        if scope["resource_scope_id"] == "nepa_project_management":
            scope["required_deliverables"] = []
            scope["optional_deliverables"] = ["Optional scoping support memo"]
            break
    bad_config_path = tmp_path / "optional_only_resource_config.json"
    bad_config_path.write_text(json.dumps(resource_config), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
        resource_scope_config_path=bad_config_path,
        authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
    )

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert set(failed_checks) == {"selected_resource_scopes_have_sow_content"}
    assert failed_checks["selected_resource_scopes_have_sow_content"]["details"] == {
        "scope_ids": ["nepa_project_management"]
    }


def test_project_sow_rendering_validation_fails_missing_sections() -> None:
    checks = project_sow._rendering_validation_checks(
        markdown="# Incomplete Package\n\n## Intake\n",
        pdf_lines=["Incomplete Package", "Resource Scopes"],
    )

    failed_checks = {check["name"]: check for check in checks if not check["passed"]}
    assert set(failed_checks) == {
        "project_sow_markdown_required_sections_present",
        "project_sow_pdf_required_items_present",
    }
    assert "## Reviewer Snapshot" in failed_checks[
        "project_sow_markdown_required_sections_present"
    ]["details"]["missing_sections"]
    assert "Review Checklist" in failed_checks[
        "project_sow_pdf_required_items_present"
    ]["details"]["missing_items"]
    assert "Contract Terms" in failed_checks[
        "project_sow_pdf_required_items_present"
    ]["details"]["missing_items"]
