from __future__ import annotations

import hashlib
import json
from pathlib import Path

from usfs_r1_ea_sources import project_sow_package as project_sow
from usfs_r1_ea_sources.project_sow_package import DEFAULT_AUTHORITY_INVENTORY_PATH
from usfs_r1_ea_sources.project_sow_package import (
    DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH,
)
from usfs_r1_ea_sources.project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from usfs_r1_ea_sources.project_sow_package import run_project_sow_eval
from usfs_r1_ea_sources.project_sow_package import run_project_sow_adjudication_apply
from usfs_r1_ea_sources.project_sow_package import run_project_sow_adjudication_eval
from usfs_r1_ea_sources.project_sow_package import run_project_sow_ea_package_handoff
from usfs_r1_ea_sources.project_sow_package import run_project_sow_intake_draft
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package
from usfs_r1_ea_sources.project_sow_package import validate_project_sow_intake
from usfs_r1_ea_sources.project_sow_package import write_project_sow_adjudication_template


REPO_ROOT = Path(__file__).resolve().parents[1]
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


def test_project_sow_package_generates_land_exchange_resource_scopes(tmp_path: Path) -> None:
    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["output_written"] is True
    assert result.package_path.exists()
    assert result.markdown_path.exists()
    assert result.pdf_path.exists()
    assert result.manifest_path.exists()
    assert result.pdf_path.read_bytes().startswith(b"%PDF-")
    assert result.summary["pdf_header_valid"] is True
    assert result.summary["output_paths"]["pdf"] == str(result.pdf_path)
    assert result.summary["output_hashes"]["project_sow_package_pdf_sha256"]

    package = json.loads(result.package_path.read_text())
    assert package["reviewer_summary"]["schema_version"] == "project-sow-reviewer-summary-v0"
    assert package["reviewer_summary"]["snapshot"]["resource_scope_count"] == 10
    assert package["reviewer_summary"]["snapshot"]["intake_evidence_graph_node_count"] == 115
    assert package["reviewer_summary"]["snapshot"]["intake_evidence_graph_edge_count"] == 134
    assert (
        package["reviewer_summary"]["snapshot"]["missing_or_uncovered_resource_area_ids"] == []
    )
    assert len(
        package["reviewer_summary"]["snapshot"]["calibration_gap_resource_area_ids"]
    ) == 7
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
    validation_checks = {check["name"]: check for check in package["validation"]["checks"]}
    assert validation_checks["project_sow_markdown_required_sections_present"]["passed"] is True
    assert validation_checks["project_sow_pdf_required_items_present"]["passed"] is True
    assert validation_checks["selected_resource_scopes_have_contract_fields"]["passed"] is True
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
    for scope in package["resource_scope_records"]:
        assert scope["acceptance_criteria"], scope["resource_scope_id"]
        assert scope["assumptions"], scope["resource_scope_id"]
        assert scope["dependencies"], scope["resource_scope_id"]
        assert scope["optional_deliverables"], scope["resource_scope_id"]
        assert scope["required_deliverables"], scope["resource_scope_id"]
        assert scope["review_timing"], scope["resource_scope_id"]
        assert scope["reviewer_role"], scope["resource_scope_id"]
        assert scope["reviewer_signoff_fields"], scope["resource_scope_id"]
    lands_scope = next(
        scope
        for scope in package["resource_scope_records"]
        if scope["resource_scope_id"] == "lands_realty_land_exchange"
    )
    assert lands_scope["reviewer_role"] == "Lands and realty specialist"
    assert "Draft exchange agreement issue list" in lands_scope["optional_deliverables"]

    markdown = result.markdown_path.read_text()
    assert "Requirements Package" in markdown
    assert "Reviewer Snapshot" in markdown
    assert "Review Checklist" in markdown
    assert "Package Boundaries" in markdown
    assert (
        "| Scope | Discipline | Covered resource areas | Required deliverables | Optional deliverables |"
        in markdown
    )
    assert "| Resource area | Coverage status | SOW scopes | Observed reports |" in markdown
    assert "Contract terms:" in markdown
    assert "Optional deliverables:" in markdown
    assert "Reviewer role: Lands and realty specialist" in markdown
    assert "Acceptance criteria:" in markdown
    assert "Lands, realty, and land exchange case requirements" in markdown
    assert "Resource Analysis Coverage" in markdown
    assert "Intake Evidence Graph" in markdown
    assert "2024 Carbon Summary.pdf" in markdown
    assert "This generated package scopes specialist work" in markdown
    pdf_text = result.pdf_path.read_bytes().decode("latin-1", errors="ignore")
    assert "Reviewer Snapshot" in pdf_text
    assert "Review Checklist" in pdf_text
    assert "Contract Terms" in pdf_text
    assert "lands_realty_land_exchange reviewer: Lands and realty specialist" in pdf_text
    assert "Resource Analysis Coverage" in pdf_text
    assert "project_sow_pdf_required_items_present: passed" in pdf_text


def test_project_sow_intake_validate_accepts_east_crazies_without_writing_outputs() -> None:
    result = validate_project_sow_intake(intake_path=INTAKE_PATH)

    assert result.summary["passed"] is True, result.summary
    assert result.summary["validation_only"] is True
    assert result.summary["output_written"] is False
    assert result.summary["resource_scope_count"] == 10
    assert result.summary["proposed_action_resource_area_count"] == 23
    assert result.summary["intake_evidence_graph_node_count"] == 115
    assert result.summary["intake_evidence_graph_edge_count"] == 134
    assert result.summary["validation_failure_count"] == 0
    assert result.summary["failed_validation_checks"] == []


def test_project_sow_intake_validate_accepts_minimal_land_exchange_template() -> None:
    result = validate_project_sow_intake(intake_path=TEMPLATE_PATH)

    assert result.summary["passed"] is True, result.summary
    assert result.summary["validation_only"] is True
    assert result.summary["output_written"] is False
    assert result.summary["resource_scope_count"] == 4
    assert result.summary["proposed_action_resource_area_count"] == 2
    assert result.summary["validation_failure_count"] == 0
    assert set(result.summary["selected_resource_scope_ids"]) == {
        "nepa_project_management",
        "lands_realty_land_exchange",
        "forest_plan_consistency",
        "public_involvement_coordination",
    }


def test_project_sow_eval_runs_three_proving_intakes(tmp_path: Path) -> None:
    result = run_project_sow_eval(
        eval_config_path=EVAL_CONFIG_PATH,
        output_dir=tmp_path / "project_sow_eval",
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary_path.exists()
    assert result.summary["case_count"] == 3
    assert result.summary["failed_cases"] == []
    assert result.summary["category_totals"] == {
        "calibration_gap_resource_area_ids": 7,
        "expected_no_observed_report_resource_area_ids": 17,
        "intake_omission_resource_area_ids": 0,
        "system_miss_resource_area_ids": 0,
    }
    cases = {case["case_id"]: case for case in result.summary["cases"]}
    assert set(cases) == {
        "east-crazies-land-exchange",
        "red-rock-ridge-land-exchange",
        "silver-creek-access-land-adjustment",
    }
    east_crazies = cases["east-crazies-land-exchange"]
    assert east_crazies["actual_metrics"]["resource_scope_count"] == 10
    assert east_crazies["actual_metrics"]["proposed_action_resource_area_count"] == 23
    assert east_crazies["actual_metrics"]["intake_evidence_graph_node_count"] == 115
    assert east_crazies["actual_metrics"]["intake_evidence_graph_edge_count"] == 134
    assert east_crazies["diagnostics"]["system_miss_resource_area_ids"] == []
    assert east_crazies["diagnostics"]["intake_omission_resource_area_ids"] == []
    assert east_crazies["diagnostics"]["calibration_gap_resource_area_ids"] == (
        east_crazies["expected_diagnostics"]["calibration_gap_resource_area_ids"]
    )
    assert cases["red-rock-ridge-land-exchange"]["diagnostics"][
        "expected_no_observed_report_resource_area_ids"
    ] == cases["red-rock-ridge-land-exchange"]["expected_diagnostics"][
        "expected_no_observed_report_resource_area_ids"
    ]
    assert cases["silver-creek-access-land-adjustment"]["actual_metrics"][
        "expected_no_observed_report_count"
    ] == 10
    for case in cases.values():
        assert case["passed"] is True, case
        assert case["actual_metrics"]["output_written"] is True
        assert case["actual_metrics"]["pdf_header_valid"] is True
        assert case["actual_metrics"]["rendering_checks_passed"] is True
        assert case["actual_metrics"]["contract_fields_passed"] is True
        assert case["actual_metrics"]["contract_ready_resource_scope_count"] == (
            case["actual_metrics"]["resource_scope_count"]
        )
        assert case["actual_metrics"]["optional_deliverable_resource_scope_count"] == (
            case["actual_metrics"]["resource_scope_count"]
        )
        assert case["actual_metrics"]["required_deliverable_resource_scope_count"] == (
            case["actual_metrics"]["resource_scope_count"]
        )
        assert Path(case["output_paths"]["package"]).exists()


def test_project_sow_eval_fails_on_expected_metric_mismatch(tmp_path: Path) -> None:
    eval_config = json.loads(EVAL_CONFIG_PATH.read_text())
    eval_config["eval_cases"][0]["expected_metrics"]["resource_scope_count"] = 99
    bad_eval_config_path = tmp_path / "bad_project_sow_eval.json"
    bad_eval_config_path.write_text(json.dumps(eval_config), encoding="utf-8")

    result = run_project_sow_eval(
        eval_config_path=bad_eval_config_path,
        output_dir=tmp_path / "project_sow_eval",
    )

    cases = {case["case_id"]: case for case in result.summary["cases"]}
    failed_checks = {
        check["name"]: check
        for check in cases["east-crazies-land-exchange"]["validation_checks"]
        if not check["passed"]
    }
    assert result.summary["passed"] is False
    assert result.summary["failed_cases"] == ["east-crazies-land-exchange"]
    assert failed_checks["expected_metrics.resource_scope_count"]["details"] == {
        "actual": 10,
        "expected": 99,
    }


def test_project_sow_eval_tracks_contract_readiness_failures(tmp_path: Path) -> None:
    resource_config = json.loads((REPO_ROOT / DEFAULT_RESOURCE_SCOPE_CONFIG_PATH).read_text())
    for scope in resource_config["resource_scopes"]:
        if scope["resource_scope_id"] == "nepa_project_management":
            del scope["reviewer_role"]
            break
    bad_config_path = tmp_path / "missing_eval_contract_fields_resource_config.json"
    bad_config_path.write_text(json.dumps(resource_config), encoding="utf-8")

    result = run_project_sow_eval(
        eval_config_path=EVAL_CONFIG_PATH,
        output_dir=tmp_path / "project_sow_eval",
        resource_scope_config_path=bad_config_path,
    )

    cases = {case["case_id"]: case for case in result.summary["cases"]}
    failed_checks = {
        check["name"]: check
        for check in cases["east-crazies-land-exchange"]["validation_checks"]
        if not check["passed"]
    }
    assert result.summary["passed"] is False
    assert result.summary["failed_cases"] == [
        "east-crazies-land-exchange",
        "red-rock-ridge-land-exchange",
        "silver-creek-access-land-adjustment",
    ]
    assert failed_checks["expected_metrics.contract_fields_passed"]["details"] == {
        "actual": False,
        "expected": True,
    }


def test_project_sow_adjudication_template_exports_reviewer_worklist(
    tmp_path: Path,
) -> None:
    result = write_project_sow_adjudication_template(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )

    template = json.loads(result.output_path.read_text())
    assert result.summary["passed"] is True
    assert result.output_path.exists()
    assert result.worklist_path.exists()
    assert template["schema_version"] == "project-sow-adjudication-v0"
    assert result.summary["item_count"] == 37
    assert result.summary["item_type_counts"] == {
        "calibration_gap": 7,
        "optional_deliverable_decision": 30,
    }
    assert template["artifact_boundaries"][1].startswith(
        "It does not create authority applicability decisions"
    )
    assert "Allowed decisions" in result.worklist_path.read_text()


def test_project_sow_adjudication_template_includes_invalid_intake_queue_items(
    tmp_path: Path,
) -> None:
    intake = json.loads(INTAKE_PATH.read_text())
    for element in intake["proposed_action_elements"]:
        if element["action_element_id"] == "climate_carbon_analysis":
            element["evidence_refs"] = []
            break
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
    intake_path = tmp_path / "adjudication_queue_intake.json"
    intake_path.write_text(json.dumps(intake), encoding="utf-8")

    result = write_project_sow_adjudication_template(
        intake_path=intake_path,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["item_type_counts"]["missing_evidence_ref"] == 1
    assert result.summary["item_type_counts"]["unknown_resource_area_id"] == 1


def test_project_sow_adjudication_eval_fails_pending_or_invalid_rows(
    tmp_path: Path,
) -> None:
    template_result = write_project_sow_adjudication_template(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    pending_eval = run_project_sow_adjudication_eval(
        intake_path=INTAKE_PATH,
        adjudication_path=template_result.output_path,
        output_path=tmp_path / "pending_adjudication_eval.json",
    )

    assert pending_eval.summary["passed"] is False
    assert pending_eval.summary["failure_category_counts"] == {
        "adjudication_pending": 37,
        "project_sow_adjudication_items_complete": 1,
        "project_sow_adjudication_reviewer_metadata_complete": 1,
    }

    adjudication = json.loads(template_result.output_path.read_text())
    adjudication["items"][0].update(
        {
            "adjudicated_at": "2026-05-07",
            "adjudicated_by": ["reviewer@example.test"],
            "decision": "approved",
            "decision_source": "fixture review",
            "rationale": "Invalid decision fixture.",
        }
    )
    invalid_path = tmp_path / "invalid_adjudication.json"
    invalid_path.write_text(json.dumps(adjudication), encoding="utf-8")

    invalid_eval = run_project_sow_adjudication_eval(
        intake_path=INTAKE_PATH,
        adjudication_path=invalid_path,
        output_path=tmp_path / "invalid_adjudication_eval.json",
    )

    assert invalid_eval.summary["passed"] is False
    assert invalid_eval.summary["failure_category_counts"][
        "adjudication_invalid_decision"
    ] == 1


def test_project_sow_adjudication_eval_fails_stale_hash_and_identity_mismatch(
    tmp_path: Path,
) -> None:
    template_result = write_project_sow_adjudication_template(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    adjudication = _completed_project_sow_adjudication(template_result.output_path)
    adjudication["input_hashes"]["intake_sha256"] = "0" * 64
    expected_resource_area_id = adjudication["items"][0]["resource_area_id"]
    adjudication["items"][0]["resource_area_id"] = "tampered_resource_area"
    adjudication_path = tmp_path / "stale_identity_mismatch_adjudication.json"
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")

    result = run_project_sow_adjudication_eval(
        intake_path=INTAKE_PATH,
        adjudication_path=adjudication_path,
        output_path=tmp_path / "stale_identity_mismatch_eval.json",
    )

    item_results = {
        item["item_id"]: item for item in result.summary["item_results"]
    }
    assert result.summary["passed"] is False
    assert result.summary["failure_category_counts"][
        "project_sow_adjudication_input_hashes_match"
    ] == 1
    assert result.summary["failure_category_counts"]["adjudication_identity_mismatch"] == 1
    assert item_results[adjudication["items"][0]["item_id"]]["identity_mismatches"] == [
        {
            "actual": "tampered_resource_area",
            "expected": expected_resource_area_id,
            "field": "resource_area_id",
        }
    ]


def test_project_sow_adjudication_eval_requires_top_level_reviewer_metadata(
    tmp_path: Path,
) -> None:
    template_result = write_project_sow_adjudication_template(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    adjudication = _completed_project_sow_adjudication(template_result.output_path)
    adjudication["reviewer_metadata"] = {
        "review_status": "pending",
        "reviewed_at": "",
        "reviewed_by": [],
        "review_source": "",
    }
    adjudication_path = tmp_path / "missing_reviewer_metadata_adjudication.json"
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")

    result = run_project_sow_adjudication_eval(
        intake_path=INTAKE_PATH,
        adjudication_path=adjudication_path,
        output_path=tmp_path / "missing_reviewer_metadata_eval.json",
    )

    failed_checks = {
        check["name"]: check for check in result.summary["failed_validation_checks"]
    }
    assert result.summary["passed"] is False
    assert set(failed_checks) == {"project_sow_adjudication_reviewer_metadata_complete"}
    assert failed_checks["project_sow_adjudication_reviewer_metadata_complete"][
        "details"
    ] == {
        "errors": [
            "reviewer_metadata.review_status must be complete",
            "reviewer_metadata.reviewed_at required",
            "reviewer_metadata.reviewed_by required",
            "reviewer_metadata.review_source required",
        ]
    }


def test_project_sow_adjudication_apply_updates_intake_for_package_status(
    tmp_path: Path,
) -> None:
    template_result = write_project_sow_adjudication_template(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    adjudication = _completed_project_sow_adjudication(template_result.output_path)
    adjudication_path = tmp_path / "completed_project_sow_adjudication.json"
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")

    apply_result = run_project_sow_adjudication_apply(
        intake_path=INTAKE_PATH,
        adjudication_path=adjudication_path,
        output_intake_path=tmp_path / "east_crazies_adjudicated_intake.json",
        output_path=tmp_path / "project_sow_adjudication_apply.json",
        eval_output_path=tmp_path / "project_sow_adjudication_eval.json",
    )

    assert apply_result.summary["passed"] is True, apply_result.summary
    assert apply_result.summary["output_written"] is True
    applied_intake = json.loads(apply_result.output_intake_path.read_text())
    assert applied_intake["project_sow_adjudication"]["status"] == "adjudicated"
    assert applied_intake["project_sow_adjudication"]["item_count"] == 37
    assert applied_intake["project_sow_adjudication"]["decision_counts"] == {
        "accepted": 7,
        "out_of_scope": 30,
    }
    assert applied_intake["project_sow_adjudication"]["reviewer_metadata"] == {
        "review_status": "complete",
        "review_source": "fixture reviewer worklist",
        "reviewed_at": "2026-05-07",
        "reviewed_by": ["reviewer@example.test"],
    }

    package_result = run_project_sow_package(
        intake_path=apply_result.output_intake_path,
        output_dir=tmp_path / "source_library_adjudicated",
    )
    package = json.loads(package_result.package_path.read_text())
    assert package_result.summary["passed"] is True, package_result.summary
    assert package_result.summary["adjudication_status"] == "adjudicated"
    assert package_result.summary["adjudication_decision_counts"] == {
        "accepted": 7,
        "out_of_scope": 30,
    }
    assert package["reviewer_summary"]["snapshot"]["adjudication_status"] == "adjudicated"
    assert package["intake_summary"]["adjudication_decision_counts"] == {
        "accepted": 7,
        "out_of_scope": 30,
    }


def test_project_sow_ea_package_handoff_derives_from_package_json(
    tmp_path: Path,
) -> None:
    package_result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )

    result = run_project_sow_ea_package_handoff(
        package_path=package_result.package_path,
        output_path=tmp_path / "project_sow_ea_package_handoff.json",
        markdown_path=tmp_path / "project_sow_ea_package_handoff.md",
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["output_written"] is True
    assert result.summary["slot_count"] == 27
    assert result.summary["slot_category_counts"] == {
        "consultation": 3,
        "decision_record_support": 2,
        "forest_plan_consistency": 1,
        "public_involvement": 1,
        "source_collection": 10,
        "specialist_report_production": 10,
    }
    assert result.output_path.exists()
    assert result.markdown_path.exists()

    handoff = json.loads(result.output_path.read_text())
    package = json.loads(package_result.package_path.read_text())
    package_hash = hashlib.sha256(package_result.package_path.read_bytes()).hexdigest()
    assert handoff["schema_version"] == "project-sow-ea-package-handoff-v0"
    assert handoff["package_identity"]["project_id"] == package["project_id"]
    assert handoff["package_identity"]["source_set_id"] == package["source_set_id"]
    assert handoff["derived_from"]["canonical_package_path"] == str(package_result.package_path)
    assert handoff["derived_from"]["source_fields"] == [
        "project_id",
        "project_name",
        "source_set_id",
        "scope_set_id",
        "resource_scope_records",
        "resource_analysis_matrix",
        "authority_requirement_matrix",
        "validation",
    ]
    assert handoff["input_hashes"]["project_sow_package_sha256"] == package_hash
    assert handoff["summary"]["slot_count"] == 27
    assert handoff["summary"]["slot_category_counts"] == result.summary[
        "slot_category_counts"
    ]
    validation_check_names = {
        check["name"] for check in handoff["validation"]["checks"]
    }
    assert {
        "ea_handoff_boundaries_complete",
        "ea_handoff_categories_complete",
        "ea_handoff_category_rules_complete",
        "ea_handoff_slots_have_future_artifacts",
        "ea_handoff_slots_present",
    }.issubset(validation_check_names)
    assert all(
        slot["future_artifact_required_now"] is False
        for slot in handoff["assembly_slots"]
    )
    assert all(
        artifact["required_now"] is False
        for slot in handoff["assembly_slots"]
        for artifact in slot["expected_future_artifacts"]
    )
    boundary_ids = {
        boundary["boundary_id"] for boundary in handoff["downstream_boundaries"]
    }
    assert {
        "future_artifacts_not_required_now",
        "no_applicability_review",
        "no_compliance_review",
        "no_generated_rule_pack",
        "no_legal_sufficiency",
    }.issubset(boundary_ids)
    contract = handoff["downstream_consumption_contract"]
    assert contract["schema_version"] == (
        "project-sow-ea-package-handoff-consumption-contract-v0"
    )
    assert {
        item["field"] for item in contract["allowed_downstream_inputs"]
    }.issuperset({"assembly_slots", "input_hashes", "package_identity"})
    assert "Expected future artifacts already exist." in contract["must_not_infer"]
    assert any(
        "actual source" in item
        for item in contract["required_preconditions_for_review_commands"]
    )
    markdown = result.markdown_path.read_text()
    assert "EA Package Assembly Handoff" in markdown
    assert "Assembly Checklist" in markdown
    assert "Downstream Consumption Contract" in markdown
    assert "no_applicability_review" in markdown
    assert "Expected future artifacts already exist." in markdown


def test_project_sow_ea_package_handoff_fails_invalid_package(
    tmp_path: Path,
) -> None:
    package_result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    package = json.loads(package_result.package_path.read_text())
    package["validation"]["passed"] = False
    invalid_package_path = tmp_path / "project_sow_package.json"
    invalid_package_path.write_text(json.dumps(package), encoding="utf-8")

    result = run_project_sow_ea_package_handoff(
        package_path=invalid_package_path,
        output_path=tmp_path / "project_sow_ea_package_handoff.json",
        markdown_path=tmp_path / "project_sow_ea_package_handoff.md",
    )

    failed_checks = {
        check["name"]: check for check in result.summary["failed_validation_checks"]
    }
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["slot_count"] == 0
    assert set(failed_checks) == {"project_sow_package_validation_passed"}
    assert not result.output_path.exists()
    assert not result.markdown_path.exists()


def test_project_sow_ea_package_handoff_fails_incomplete_rules(
    tmp_path: Path,
) -> None:
    package_result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    rules = json.loads(
        (REPO_ROOT / DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH).read_text()
    )
    rules["required_category_ids"].append("missing_category")
    rules_path = tmp_path / "project_sow_ea_handoff_rules.json"
    rules_path.write_text(json.dumps(rules), encoding="utf-8")

    result = run_project_sow_ea_package_handoff(
        package_path=package_result.package_path,
        handoff_rules_config_path=rules_path,
    )

    failed_checks = {
        check["name"]: check for check in result.summary["failed_validation_checks"]
    }
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert set(failed_checks) == {"ea_handoff_required_categories_present"}


def test_project_sow_ea_package_handoff_fails_malformed_rules(
    tmp_path: Path,
) -> None:
    package_result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )
    rules = json.loads(
        (REPO_ROOT / DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH).read_text()
    )
    rules["assembly_categories"][0]["applies_to"] = "unsupported"
    rules["assembly_categories"][1]["expected_artifact_types"] = []
    rules["category_rules"][0]["resource_area_ids"] = []
    rules["category_rules"][0]["resource_scope_ids"] = []
    rules["downstream_boundaries"][0]["statement"] = ""
    rules_path = tmp_path / "malformed_project_sow_ea_handoff_rules.json"
    rules_path.write_text(json.dumps(rules), encoding="utf-8")

    result = run_project_sow_ea_package_handoff(
        package_path=package_result.package_path,
        output_path=tmp_path / "project_sow_ea_package_handoff.json",
        markdown_path=tmp_path / "project_sow_ea_package_handoff.md",
        handoff_rules_config_path=rules_path,
    )

    failed_checks = {
        check["name"]: check for check in result.summary["failed_validation_checks"]
    }
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert {
        "ea_handoff_boundaries_complete",
        "ea_handoff_categories_complete",
        "ea_handoff_category_rules_complete",
        "ea_handoff_slots_have_future_artifacts",
    }.issubset(failed_checks)
    assert "assembly_categories[0].applies_to: unsupported" in failed_checks[
        "ea_handoff_categories_complete"
    ]["details"]["errors"]
    assert "category_rules[0].resource_scope_ids: must contain at least one item" in (
        failed_checks["ea_handoff_category_rules_complete"]["details"]["errors"]
    )
    assert "downstream_boundaries[0].statement: required" in failed_checks[
        "ea_handoff_boundaries_complete"
    ]["details"]["errors"]
    assert not result.output_path.exists()
    assert not result.markdown_path.exists()


def test_project_sow_intake_schema_declares_draft_metadata_contract() -> None:
    schema = json.loads(INTAKE_SCHEMA_PATH.read_text())
    draft_metadata = schema["properties"]["draft_metadata"]

    assert draft_metadata["properties"]["schema_version"] == {
        "const": "project-sow-intake-draft-v0"
    }
    assert "source_text_path" in draft_metadata["required"]
    assert draft_metadata["properties"]["source_text_sha256"]["pattern"] == "^[a-f0-9]{64}$"


def test_project_sow_intake_draft_writes_unreviewed_schema_valid_intake(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "red_rock_ridge_draft_intake.json"
    expected_metadata = json.loads(EXPECTED_DRAFT_METADATA_PATH.read_text())

    result = run_project_sow_intake_draft(
        proposed_action_path=PROPOSED_ACTION_FIXTURE_PATH,
        output_path=output_path,
        forest="Example National Forest",
        districts=["Example Ranger District"],
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["output_written"] is True
    assert result.summary["validation_ready"] is False
    assert output_path.exists()
    draft = json.loads(output_path.read_text())
    assert draft["schema_version"] == "project-sow-intake-v0"
    assert draft["draft_metadata"]["schema_version"] == "project-sow-intake-draft-v0"
    assert draft["draft_metadata"]["review_status"] == "unreviewed"
    assert draft["draft_metadata"]["reviewer_confirmation_required"] is True
    assert draft["draft_metadata"]["source_text_path"] == str(PROPOSED_ACTION_FIXTURE_PATH)
    assert draft["draft_metadata"]["source_text_sha256"] == hashlib.sha256(
        PROPOSED_ACTION_FIXTURE_PATH.read_bytes()
    ).hexdigest()
    assert draft["draft_metadata"]["candidate_resource_area_ids"] == (
        expected_metadata["expected_resource_area_ids"]
    )
    assert draft["draft_metadata"]["uncertainty_flags"] == (
        expected_metadata["expected_uncertainty_flags"]
    )
    assert sorted(
        action["action_type"] for action in draft["federal_land_actions"]
    ) == expected_metadata["expected_federal_land_action_types"]
    assert draft["proposed_action_elements"]
    assert all(element["evidence_refs"] for element in draft["proposed_action_elements"])
    assert any(
        ref["locator"].startswith("paragraph ")
        for element in draft["proposed_action_elements"]
        for ref in element["evidence_refs"]
    )
    assert "compliance finding" not in json.dumps(draft).lower()
    assert "legal sufficiency conclusion" not in json.dumps(draft).lower()

    validation = validate_project_sow_intake(intake_path=output_path)
    failed_checks = _failed_checks(validation)
    assert validation.summary["passed"] is False
    assert set(failed_checks) == {"draft_reviewer_confirmation_complete"}
    assert failed_checks["draft_reviewer_confirmation_complete"]["details"] == {
        "errors": [
            "draft_metadata.review_status must be reviewer_confirmed",
            "draft_metadata.reviewer_confirmation_required must be false",
            "draft_metadata.uncertainty_flags must be empty",
        ]
    }
    package_attempt = run_project_sow_package(
        intake_path=output_path,
        output_dir=tmp_path / "source_library",
    )
    assert package_attempt.summary["passed"] is False
    assert package_attempt.summary["output_written"] is False


def test_project_sow_intake_draft_marks_ambiguous_action_as_review_work(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "ambiguous_draft_intake.json"

    result = run_project_sow_intake_draft(
        proposed_action_path=AMBIGUOUS_PROPOSED_ACTION_FIXTURE_PATH,
        output_path=output_path,
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["validation_ready"] is False
    draft = json.loads(output_path.read_text())
    assert "federal_land_actions_need_review" in draft["draft_metadata"]["uncertainty_flags"]
    assert "land_exchange_action_types_uncertain" in draft["draft_metadata"]["uncertainty_flags"]
    assert draft["federal_land_actions"] == [
        {
            "action_type": "review_needed",
            "description": (
                "Reviewer must identify the federal land disposal, acquisition, "
                "reservation, or other land action before package generation."
            ),
        }
    ]
    assert "land_exchange_case" in draft["draft_metadata"]["candidate_resource_area_ids"]
    assert "wildlife_resources" in draft["draft_metadata"]["candidate_resource_area_ids"]


def test_project_sow_intake_draft_fails_on_unexpected_validation_failures(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "draft_with_bad_scope_config.json"
    bad_scope_config_path = tmp_path / "empty_resource_scopes.json"
    bad_scope_config_path.write_text(
        json.dumps({"resource_scopes": [], "schema_version": "project-sow-resource-scopes-v1"}),
        encoding="utf-8",
    )

    result = run_project_sow_intake_draft(
        proposed_action_path=PROPOSED_ACTION_FIXTURE_PATH,
        output_path=output_path,
        resource_scope_config_path=bad_scope_config_path,
    )

    failed_check_names = {
        check["name"] for check in result.summary["unexpected_failed_validation_checks"]
    }
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is True
    assert result.summary["validation_ready"] is False
    assert result.summary["unexpected_validation_failure_count"] > 0
    assert "resource_scope_config_has_scopes" in failed_check_names


def test_project_sow_intake_validate_accepts_reviewer_confirmed_draft(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "reviewed_draft_intake.json"
    run_project_sow_intake_draft(
        proposed_action_path=PROPOSED_ACTION_FIXTURE_PATH,
        output_path=output_path,
        forest="Example National Forest",
        districts=["Example Ranger District"],
    )
    draft = json.loads(output_path.read_text())
    draft["draft_metadata"]["review_status"] = "reviewer_confirmed"
    draft["draft_metadata"]["reviewer_confirmation_required"] = False
    draft["draft_metadata"]["uncertainty_flags"] = []
    output_path.write_text(json.dumps(draft), encoding="utf-8")

    validation = validate_project_sow_intake(intake_path=output_path)

    assert validation.summary["passed"] is True, validation.summary
    assert validation.summary["validation_failure_count"] == 0


def test_project_sow_intake_validate_fails_unsupported_schema_version(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["schema_version"] = "project-sow-intake-v99"

    result = _validate_with_intake(tmp_path, intake, "unsupported_schema_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 1
    assert set(failed_checks) == {"intake_schema_supported"}
    assert failed_checks["intake_schema_supported"]["details"] == {
        "schema_version": "project-sow-intake-v99"
    }


def test_project_sow_intake_validate_fails_minimal_missing_federal_land_action(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["federal_land_actions"] = []

    result = _validate_with_intake(tmp_path, intake, "missing_federal_action_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 2
    assert set(failed_checks) == {
        "land_exchange_intake_has_federal_land_actions",
        "required_intake_fields_present",
    }


def test_project_sow_intake_validate_fails_minimal_missing_evidence_refs(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["proposed_action_elements"][0]["evidence_refs"] = []

    result = _validate_with_intake(tmp_path, intake, "missing_evidence_refs_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 3
    assert set(failed_checks) == {
        "intake_schema_shape_valid",
        "intake_evidence_graph_action_elements_have_evidence_refs",
        "intake_evidence_graph_resource_area_paths_complete",
    }
    assert failed_checks["intake_schema_shape_valid"]["details"] == {
        "errors": [
            "proposed_action_elements[0].evidence_refs: must contain at least one item"
        ]
    }
    assert failed_checks["intake_evidence_graph_resource_area_paths_complete"][
        "details"
    ] == {"resource_area_ids": ["land_exchange_case", "land_management_plan_consistency"]}


def test_project_sow_intake_validate_fails_missing_action_elements(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["proposed_action_elements"] = []

    result = _validate_with_intake(tmp_path, intake, "missing_action_elements_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 2
    assert set(failed_checks) == {
        "intake_evidence_graph_resource_area_paths_complete",
        "required_intake_fields_present",
    }
    assert failed_checks["required_intake_fields_present"]["details"] == {
        "missing_fields": ["proposed_action_elements"]
    }
    assert failed_checks["intake_evidence_graph_resource_area_paths_complete"][
        "details"
    ] == {"resource_area_ids": ["land_exchange_case", "land_management_plan_consistency"]}


def test_project_sow_intake_validate_fails_incomplete_action_element_schema(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["proposed_action_elements"][0]["action_element_id"] = ""
    intake["proposed_action_elements"][0]["evidence_refs"][0].pop("source_record_id")

    result = _validate_with_intake(tmp_path, intake, "incomplete_action_element_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 1
    assert set(failed_checks) == {"intake_schema_shape_valid"}
    assert failed_checks["intake_schema_shape_valid"]["details"] == {
        "errors": [
            "proposed_action_elements[0].action_element_id: required",
            "proposed_action_elements[0].evidence_refs[0].source_record_id: required",
        ]
    }


def test_project_sow_intake_validate_fails_incomplete_observed_report_schema(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["observed_specialist_reports"] = [
        {
            "evidence_refs": [
                {
                    "evidence_ref_id": "observed-report-evidence",
                    "locator": "Observed package",
                    "source_record_id": "INTAKE-002",
                    "summary": "Observed report evidence.",
                    "title": "Observed Report.pdf",
                }
            ],
            "report_id": "observed-report",
            "resource_area_ids": [],
        }
    ]

    result = _validate_with_intake(tmp_path, intake, "incomplete_observed_report_intake.json")

    failed_checks = _failed_checks(result)
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 1
    assert set(failed_checks) == {"intake_schema_shape_valid"}
    assert failed_checks["intake_schema_shape_valid"]["details"] == {
        "errors": [
            "observed_specialist_reports[0].resource_area_ids: required",
            "observed_specialist_reports[0].title: required",
            "observed_specialist_reports[0].resource_area_ids: must contain at least one item",
        ]
    }


def test_project_sow_intake_validate_fails_minimal_unknown_resource_area(
    tmp_path: Path,
) -> None:
    intake = json.loads(TEMPLATE_PATH.read_text())
    intake["proposed_action_elements"][0]["resource_area_ids"].append("unknown_area")
    intake["resource_analysis_expectations"].append(
        {
            "proposed_action_basis": ["Intentional invalid test area."],
            "resource_area_id": "unknown_area",
            "resource_area_name": "Unknown area",
        }
    )

    result = _validate_with_intake(tmp_path, intake, "unknown_resource_area_intake.json")

    failed_checks = _failed_checks(result)
    expected_details = {"resource_area_ids": ["unknown_area"]}
    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 3
    assert set(failed_checks) == {
        "expected_resource_areas_have_sow_scope",
        "expected_resource_areas_resolve_to_scope_config",
        "intake_evidence_graph_resource_area_paths_complete",
    }
    assert failed_checks["expected_resource_areas_have_sow_scope"][
        "details"
    ] == expected_details
    assert failed_checks["expected_resource_areas_resolve_to_scope_config"][
        "details"
    ] == expected_details
    assert failed_checks["intake_evidence_graph_resource_area_paths_complete"][
        "details"
    ] == expected_details


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
        "intake_evidence_graph_action_elements_trigger_resource_areas"
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
