from __future__ import annotations

import hashlib
import json
from pathlib import Path

from usfs_r1_ea_sources.project_sow_package import run_project_sow_intake_draft
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package
from usfs_r1_ea_sources.project_sow_package import validate_project_sow_intake

from tests.support.project_sow_package_fixtures import (
    AMBIGUOUS_PROPOSED_ACTION_FIXTURE_PATH,
    EXPECTED_DRAFT_METADATA_PATH,
    INTAKE_PATH,
    INTAKE_SCHEMA_PATH,
    PROPOSED_ACTION_FIXTURE_PATH,
    TEMPLATE_PATH,
    _failed_checks,
    _validate_with_intake,
)


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
