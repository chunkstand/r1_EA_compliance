from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources import project_sow_package as project_sow
from usfs_r1_ea_sources.project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from usfs_r1_ea_sources.project_sow_package import run_project_sow_eval
from usfs_r1_ea_sources.project_sow_package import run_project_sow_operational_gate
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package

from tests.support.project_sow_package_fixtures import (
    EVAL_CONFIG_PATH,
    INTAKE_PATH,
    REPO_ROOT,
    _edge_exists,
    _has_canonical_graph_path,
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


def test_project_sow_operational_gate_runs_release_checks(tmp_path: Path) -> None:
    result = run_project_sow_operational_gate(
        output_dir=tmp_path / "project_sow_operational_gate"
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["schema_version"] == "project-sow-operational-gate-summary-v0"
    assert result.summary_path.exists()
    assert result.markdown_path.exists()
    assert result.summary["intake_validation_count"] == 4
    assert result.summary["proving_eval"]["case_count"] == 3
    assert result.summary["proving_eval"]["failed_cases"] == []
    assert result.summary["proving_eval"]["category_totals"][
        "system_miss_resource_area_ids"
    ] == 0
    assert result.summary["proving_eval"]["category_totals"][
        "intake_omission_resource_area_ids"
    ] == 0
    assert result.summary["ea_handoff_smoke"]["slot_count"] == 27
    assert result.summary["ea_handoff_smoke"]["validation_failure_count"] == 0
    assert result.summary["tracked_docs_schema_checks"]["json_paths_valid"] is True
    assert result.summary["tracked_docs_schema_checks"]["docs_updated"] is True
    assert "docs/SESSION_HANDOFF.md" in result.summary["tracked_docs_schema_checks"][
        "checked_doc_paths"
    ]
    assert "docs/ARCHITECTURE.md" in result.summary["tracked_docs_schema_checks"][
        "checked_doc_paths"
    ]
    assert "docs/PROJECT_SOW_OPERATIONALIZATION_ACCEPTANCE_MATRIX.md" in result.summary[
        "tracked_docs_schema_checks"
    ]["checked_doc_paths"]
    assert result.summary["closeout_contract"]["schema_version"] == (
        "project-sow-operational-gate-closeout-contract-v0"
    )
    assert result.summary["closeout_contract"]["ci_policy"]["status"] == "local-only"
    assert "project_sow_operational_gate_closeout_contract_complete" in {
        check["name"] for check in result.summary["checks"]
    }
    assert result.summary["output_hashes"]["project_sow_eval_summary_sha256"]
    assert result.summary["output_hashes"]["project_sow_ea_package_handoff_sha256"]
    assert result.summary["output_hashes"][
        "project_sow_operational_gate_summary_content_sha256"
    ]
    assert result.summary["ci_policy"]["status"] == "local-only"
    assert all(check["passed"] for check in result.summary["checks"])
    markdown = result.markdown_path.read_text()
    assert "Project SOW Operational Readiness Report" in markdown
    assert "project-sow-operational-gate" in markdown


def test_project_sow_operational_gate_fails_on_eval_regression(tmp_path: Path) -> None:
    eval_config = json.loads(EVAL_CONFIG_PATH.read_text())
    eval_config["eval_cases"][0]["expected_metrics"]["resource_scope_count"] = 99
    bad_eval_config_path = tmp_path / "bad_project_sow_eval.json"
    bad_eval_config_path.write_text(json.dumps(eval_config), encoding="utf-8")

    result = run_project_sow_operational_gate(
        eval_config_path=bad_eval_config_path,
        output_dir=tmp_path / "project_sow_operational_gate",
    )

    failed_checks = {check["name"]: check for check in result.summary["failed_checks"]}
    assert result.summary["passed"] is False
    assert result.summary_path.exists()
    assert "project_sow_operational_gate_proving_eval_passed" in failed_checks
    assert failed_checks["project_sow_operational_gate_proving_eval_passed"][
        "details"
    ]["failed_cases"] == ["east-crazies-land-exchange"]


def test_project_sow_operational_gate_fails_missing_closeout_doc(
    monkeypatch,
    tmp_path: Path,
) -> None:
    missing_doc_path = tmp_path / "missing_closeout_doc.md"
    monkeypatch.setattr(
        project_sow,
        "PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS",
        project_sow.PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS
        + ((missing_doc_path, ("project-sow-operational-gate",)),),
    )

    result = run_project_sow_operational_gate(
        output_dir=tmp_path / "project_sow_operational_gate"
    )

    failed_checks = {check["name"]: check for check in result.summary["failed_checks"]}
    assert result.summary["passed"] is False
    assert result.summary_path.exists()
    assert "project_sow_operational_gate_docs_updated" in failed_checks
    assert failed_checks["project_sow_operational_gate_docs_updated"]["details"] == {
        "missing_doc_terms": [
            {
                "missing_terms": ["project-sow-operational-gate"],
                "path": str(missing_doc_path),
            }
        ]
    }
