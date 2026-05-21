from __future__ import annotations

import hashlib
import json
from pathlib import Path

from usfs_r1_ea_sources.project_sow_package import DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH
from usfs_r1_ea_sources.project_sow_package import run_project_sow_adjudication_apply
from usfs_r1_ea_sources.project_sow_package import run_project_sow_adjudication_eval
from usfs_r1_ea_sources.project_sow_package import run_project_sow_ea_package_handoff
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package
from usfs_r1_ea_sources.project_sow_package import write_project_sow_adjudication_template

from tests.support.project_sow_package_fixtures import (
    INTAKE_PATH,
    REPO_ROOT,
    _completed_project_sow_adjudication,
)


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
