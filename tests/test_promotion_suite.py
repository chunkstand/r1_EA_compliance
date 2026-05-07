from __future__ import annotations

from pathlib import Path
import json

import pytest

from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_PROMOTION_SUITE = REPO_ROOT / "config" / "promotion_suite_v1.json"


def test_committed_promotion_suite_requires_milestone_4_applicability_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}

    seed_gate = suite_results["applicability_eval_authority_family_coverage"]
    assert seed_gate["required_for_current_promotion"] is True
    assert seed_gate["path"] == "reviews/applicability_eval/applicability_eval_results.json"
    seed_checks = {check["name"]: check for check in seed_gate["checks"]}
    assert seed_checks["applicability_eval_passed"]["equals"] is True
    assert seed_checks["applicability_eval_case_count"]["min"] == 9
    assert seed_checks["authority_family_high_priority_count"]["equals"] == 19
    assert seed_checks["authority_family_positive_coverage"]["equals"] == 19
    assert seed_checks["authority_family_negative_coverage"]["equals"] == 19
    assert seed_checks["authority_family_unresolved_coverage"]["min"] == 1
    assert seed_checks["authority_family_real_package_tags"]["equals"] is True
    assert seed_checks["applicability_eval_weak_auxiliary_arbitration"]["min"] == 1
    assert seed_checks["applicability_eval_weak_only_arbitration"]["min"] == 1
    assert seed_checks["applicability_eval_positive_negative_arbitration"]["min"] == 1

    gold_gate = suite_results["applicability_gold_eval_authority_family_adjudication"]
    assert gold_gate["required_for_current_promotion"] is True
    assert gold_gate["path"] == "reviews/applicability_gold_eval/applicability_gold_eval_results.json"
    gold_checks = {check["name"]: check for check in gold_gate["checks"]}
    assert gold_checks["applicability_gold_eval_passed"]["equals"] is True
    assert gold_checks["applicability_gold_eval_promotion_ready"]["equals"] is True
    assert gold_checks["applicability_gold_eval_case_count"]["min"] == 5
    assert gold_checks["applicability_gold_eval_weak_only_arbitration"]["min"] == 1
    assert gold_checks["applicability_gold_eval_unresolved_profile"]["min"] == 1
    assert gold_checks["applicability_gold_eval_adjudicated_profile"]["min"] == 1
    assert gold_checks["authority_family_adjudicated_coverage"]["min"] == 1


def test_committed_promotion_suite_requires_milestone_5_report_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}
    review_case = manifest["review_cases"][0]
    results = {result["id"]: result for result in review_case["results"]}

    phase = suite_results["phase_eval_core"]
    phase_checks = {check["name"]: check for check in phase["checks"]}
    assert phase_checks["core_passed_phase_count"]["min"] == 17
    assert phase_checks["core_reviewer_ready_phase_count"]["min"] == 17
    assert phase_checks["phase_eval_arbitration_summary_schema"]["equals"] == (
        "applicability-arbitration-summary-v0"
    )
    assert phase_checks["phase_eval_arbitration_decision_count"]["min"] == 1

    decision_support = results["decision_support_report"]
    assert decision_support["required_for_current_promotion"] is True
    assert (
        decision_support["path"]
        == "reviews/{review_id}/decision_support/ea_consistency_decision_support.json"
    )
    decision_checks = {check["name"]: check for check in decision_support["checks"]}
    assert decision_checks["decision_support_schema"]["equals"] == (
        "ea-consistency-decision-support-report-v1"
    )
    assert decision_checks["decision_support_status"]["equals"] == "reviewer_ready"
    assert decision_checks["decision_support_validation_passed"]["equals"] is True
    assert decision_checks["decision_support_applicable_authorities"]["equals"] == 33
    assert decision_checks["decision_support_non_applicable_authorities"]["equals"] == 340
    assert decision_checks["decision_support_forest_plan_components"]["equals"] == 329
    assert decision_checks["decision_support_applicable_standards"]["equals"] == 12
    assert decision_checks["decision_support_legal_conclusion_boundary"]["equals"] is False

    decision_manifest = results["decision_support_manifest"]
    assert decision_manifest["required_for_current_promotion"] is True
    assert (
        decision_manifest["path"]
        == "reviews/{review_id}/decision_support/ea_consistency_decision_support_manifest.json"
    )
    manifest_checks = {check["name"]: check for check in decision_manifest["checks"]}
    assert manifest_checks["decision_support_manifest_schema"]["equals"] == (
        "ea-consistency-decision-support-manifest-v1"
    )
    assert manifest_checks["decision_support_manifest_validation_status"]["equals"] == "passed"

    decision_pdf = results["decision_support_pdf"]
    assert decision_pdf["required_for_current_promotion"] is True
    assert (
        decision_pdf["path"]
        == "reviews/{review_id}/decision_support/ea_consistency_decision_support.pdf"
    )
    pdf_checks = {check["name"]: check for check in decision_pdf["checks"]}
    assert pdf_checks["decision_support_pdf_header_valid"]["starts_with"] == "%PDF-"

    provenance = results["authority_family_provenance"]
    assert provenance["required_for_current_promotion"] is True
    assert provenance["path"] == "reviews/{review_id}/authority_family_provenance.json"
    provenance_checks = {check["name"]: check for check in provenance["checks"]}
    assert provenance_checks["authority_provenance_generated_mode"]["equals"] is True
    assert provenance_checks["authority_provenance_finding_count"]["equals"] == 33
    assert provenance_checks["authority_provenance_family_ids_present"]["equals"] == []
    assert provenance_checks["authority_provenance_candidate_ids_present"]["equals"] == []

    appendix = results["non_applicable_authority_appendix"]
    assert appendix["required_for_current_promotion"] is True
    assert appendix["path"] == "reviews/{review_id}/non_applicable_authority_appendix.json"
    appendix_checks = {check["name"]: check for check in appendix["checks"]}
    assert appendix_checks["non_applicable_authority_count"]["min"] == 1
    assert appendix_checks["non_applicable_authorities_have_coverage"]["equals"] is True
    assert appendix_checks["non_applicable_authorities_have_rationale"]["equals"] is True

    resolution = results["authority_reviewer_resolution_report"]
    assert resolution["required_for_current_promotion"] is True
    assert resolution["path"] == "reviews/{review_id}/authority_reviewer_resolution_report.json"
    resolution_checks = {check["name"]: check for check in resolution["checks"]}
    assert resolution_checks["authority_resolution_pending_count"]["equals"] == 0
    assert resolution_checks["authority_resolution_report_passed"]["equals"] is True

    risk = results["litigation_risk_summary"]
    assert risk["required_for_current_promotion"] is True
    assert risk["path"] == "reviews/{review_id}/litigation_risk_summary.json"
    risk_checks = {check["name"]: check for check in risk["checks"]}
    assert risk_checks["litigation_risk_flags_present"]["min"] == 1
    assert risk_checks["litigation_risk_no_legal_conclusions"]["equals"] == 0
    assert risk_checks["litigation_risk_deterministic_only"]["equals"] is True


def test_committed_promotion_suite_records_ecid_expansion_artifact_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    review_cases = {case["id"]: case for case in manifest["review_cases"]}
    ecid_case = review_cases["region1-expansion-ecid-preliminary-ea"]
    ecid_results = {result["id"]: result for result in ecid_case["results"]}

    assert ecid_case["required_for_current_promotion"] is False
    assert ecid_case["review_id"] == "region1-expansion-ecid-preliminary-ea"
    for result in ecid_results.values():
        assert result["required_for_current_promotion"] is False
        assert result["required_for_expansion"] is True

    generated = ecid_results["generated_rule_pack_validation"]
    generated_checks = {check["name"]: check for check in generated["checks"]}
    assert generated_checks["generated_rule_pack_validation_passed"]["equals"] is True
    assert generated_checks["generated_rule_count"]["equals"] == 46
    assert generated_checks["source_set_matches"]["equals"] == "source-set-ba8d0feae79501b8"

    compliance = ecid_results["compliance_review"]
    assert compliance["failure_category"] == "forest_plan_reviewer_not_ready"
    compliance_checks = {check["name"]: check for check in compliance["checks"]}
    assert compliance_checks["reviewer_ready"]["equals"] is True
    assert compliance_checks["rule_count"]["equals"] == 46
    assert compliance_checks["rule_claim_gap_count"]["equals"] == 0
    assert compliance_checks["rule_claim_gap_count"]["failure_category"] == "missing_source"
    assert compliance_checks["forest_plan_applicable_standard_count"]["equals"] == 29
    assert compliance_checks["forest_plan_applied_standard_count"]["equals"] == 7

    component_adjudication = ecid_results["forest_plan_component_adjudication_eval"]
    adjudication_checks = {
        check["name"]: check for check in component_adjudication["checks"]
    }
    assert adjudication_checks["component_adjudication_eval_passed"]["equals"] is True
    assert adjudication_checks["component_adjudication_eval_resolved_items"]["equals"] == 158
    assert adjudication_checks["component_adjudication_eval_true_omissions"]["equals"] == 158
    assert adjudication_checks["component_adjudication_eval_system_misses"]["equals"] == 0

    phase = ecid_results["phase_eval"]
    assert phase["path"] == "reviews/{review_id}/phase_eval_results.json"
    assert phase["failure_category"] == "forest_plan_reviewer_not_ready"

    south_plateau_case = review_cases["region1-expansion-south-plateau-landscape-treatment"]
    south_plateau_results = {
        result["id"]: result for result in south_plateau_case["results"]
    }

    assert south_plateau_case["required_for_current_promotion"] is False
    assert south_plateau_case["review_id"] == (
        "region1-expansion-south-plateau-landscape-treatment"
    )
    for result in south_plateau_results.values():
        assert result["required_for_current_promotion"] is False
        assert result["required_for_expansion"] is True

    south_plateau_generated = south_plateau_results["generated_rule_pack_validation"]
    south_plateau_generated_checks = {
        check["name"]: check for check in south_plateau_generated["checks"]
    }
    assert south_plateau_generated_checks["generated_rule_count"]["equals"] == 61
    assert south_plateau_generated_checks["source_set_matches"]["equals"] == (
        "source-set-ba8d0feae79501b8"
    )

    south_plateau_compliance = south_plateau_results["compliance_review"]
    south_plateau_compliance_checks = {
        check["name"]: check for check in south_plateau_compliance["checks"]
    }
    assert south_plateau_compliance_checks["reviewer_ready"]["equals"] is True
    assert south_plateau_compliance_checks["rule_count"]["equals"] == 61
    assert south_plateau_compliance_checks["rule_claim_gap_count"]["equals"] == 0
    assert south_plateau_compliance_checks["rule_claim_link_count"]["equals"] == 280

    south_plateau_phase = south_plateau_results["phase_eval"]
    south_plateau_phase_checks = {
        check["name"]: check for check in south_plateau_phase["checks"]
    }
    assert south_plateau_phase_checks["phase_eval_passed"]["equals"] is True
    assert south_plateau_phase_checks["phase_eval_reviewer_ready"]["equals"] is True
    assert south_plateau_phase_checks["phase_eval_passed_phase_count"]["equals"] == 15

    slots = {slot["id"]: slot for slot in manifest["expansion_slots"]}
    slot = slots["region1-real-ea-slot-1"]
    ecid_gate_artifacts = {artifact["id"] for artifact in slot["expected_gate_artifacts"]}

    assert slot["status"] == "ready"
    assert slot["ready"] is True
    assert "failure_category" not in slot
    assert slot["review_id"] == "region1-expansion-ecid-preliminary-ea"
    assert slot["source_set_id"] == "source-set-ba8d0feae79501b8"
    assert "Preliminary Environmental Assessment" in slot["package_path"]
    assert set(ecid_results).issubset(ecid_gate_artifacts)
    assert slot["last_local_signal"]["package_chunk_count"] == 160
    assert slot["last_local_signal"]["candidate_authority_count"] == 392
    assert slot["last_local_signal"]["applicable_authority_count"] == 46
    assert slot["last_local_signal"]["non_applicable_authority_count"] == 346
    assert slot["last_local_signal"]["needs_adjudication_authority_count"] == 0
    assert slot["last_local_signal"]["remaining_adjudication_authority_family_ids"] == []
    assert slot["last_local_signal"]["applicability_validation_passed"] is True
    assert slot["last_local_signal"]["generated_rule_pack_ready"] is True
    assert slot["last_local_signal"]["compliance_review_reviewer_ready"] is True
    assert slot["last_local_signal"]["rule_claim_link_count"] == 211
    assert slot["last_local_signal"]["rule_claim_gap_count"] == 0
    assert slot["last_local_signal"]["forest_plan_component_reviewer_resolution_count"] == 158
    assert slot["last_local_signal"]["forest_plan_component_adjudication_eval_passed"] is True
    assert slot["last_local_signal"]["forest_plan_component_adjudication_resolved_count"] == 158
    assert (
        slot["last_local_signal"]["forest_plan_component_adjudication_system_miss_count"]
        == 0
    )

    third_slot = slots["region1-real-ea-slot-2"]
    gate_artifacts = {artifact["id"] for artifact in third_slot["expected_gate_artifacts"]}

    assert third_slot["status"] == "ready"
    assert third_slot["ready"] is True
    assert "failure_category" not in third_slot
    assert third_slot["review_id"] == "region1-expansion-south-plateau-landscape-treatment"
    assert third_slot["source_set_id"] == "source-set-ba8d0feae79501b8"
    assert third_slot["forest_plan_profile"] == "custer_gallatin"
    assert "South Plateau" in third_slot["label"]
    assert "South Plateau" in third_slot["project_metadata"]["project_name"]
    assert third_slot["project_metadata"]["project_number"] == "57353"
    assert third_slot["project_metadata"]["expected_analysis_type"] == (
        "Environmental Assessment"
    )
    assert third_slot["last_local_signal"]["package_imported"] is True
    assert third_slot["last_local_signal"]["official_document_count"] == 26
    assert third_slot["last_local_signal"]["package_file_count"] == 26
    assert third_slot["last_local_signal"]["package_failed_count"] == 0
    assert third_slot["last_local_signal"]["package_chunk_count"] == 3671
    assert third_slot["last_local_signal"]["candidate_authority_count"] == 392
    assert third_slot["last_local_signal"]["applicable_authority_count"] == 61
    assert third_slot["last_local_signal"]["non_applicable_authority_count"] == 331
    assert third_slot["last_local_signal"]["needs_adjudication_authority_count"] == 0
    assert third_slot["last_local_signal"]["unresolved_authority_count"] == 0
    assert third_slot["last_local_signal"]["remaining_adjudication_authority_family_ids"] == []
    assert third_slot["last_local_signal"]["applicability_validation_passed"] is True
    assert third_slot["last_local_signal"]["generated_rule_pack_ready"] is True
    assert third_slot["last_local_signal"]["generated_rule_pack_validation_passed"] is True
    assert third_slot["last_local_signal"]["generated_rule_count"] == 61
    assert third_slot["last_local_signal"]["compliance_validation_passed"] is True
    assert third_slot["last_local_signal"]["compliance_review_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["compliance_finding_count"] == 61
    assert third_slot["last_local_signal"]["rule_claim_link_count"] == 280
    assert third_slot["last_local_signal"]["rule_claim_gap_count"] == 0
    assert third_slot["last_local_signal"]["phase_eval_passed"] is True
    assert third_slot["last_local_signal"]["phase_eval_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["phase_eval_passed_phase_count"] == 15
    assert third_slot["last_local_signal"]["adjudication_eval_passed"] is True
    assert third_slot["last_local_signal"]["adjudication_resolved_count"] == 6
    assert third_slot["last_local_signal"]["adjudication_apply_passed"] is True
    assert third_slot["last_local_signal"]["adjudication_applied_item_count"] == 6
    assert "package_manifest" in gate_artifacts
    assert "applicability_validation" in gate_artifacts
    assert "generated_rule_pack_validation" in gate_artifacts
    assert "compliance_review" in gate_artifacts
    assert "compliance_matrix" in gate_artifacts
    assert "compliance_matrix_pdf" in gate_artifacts
    assert "authority_family_provenance" in gate_artifacts
    assert "non_applicable_authority_appendix" in gate_artifacts
    assert "authority_reviewer_resolution_report" in gate_artifacts
    assert "litigation_risk_summary" in gate_artifacts
    assert "phase_eval" in gate_artifacts
    assert set(south_plateau_results).issubset(gate_artifacts)


def test_promotion_suite_reports_current_ready_and_expansion_gap(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is True
    assert result.summary["failure_category_counts"] == {}
    assert result.summary["expansion_failure_category_counts"] == {
        "applicability_miss": 1,
        "package_fixture_missing": 1,
    }
    assert result.summary["open_expansion_slot_count"] == 1
    assert result.output_path.exists()
    assert result.markdown_path.exists()


def test_promotion_suite_strict_expansion_blocks_promotion(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
        strict_expansion=True,
    )

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert result.summary["failure_category_counts"] == {
        "applicability_miss": 1,
        "package_fixture_missing": 1,
    }
    assert result.summary["expansion_failure_category_counts"] == {
        "applicability_miss": 1,
        "package_fixture_missing": 1,
    }


def test_promotion_suite_reports_selected_not_ready_slot_metadata(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "label": "Selected package fixture",
        "status": "selected_not_run",
        "ready": False,
        "failure_category": "applicability_miss",
        "review_id": "selected-review",
        "package_path": "source_library/reviews/_intake/selected-review",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "package_manifest",
                "path": "reviews/{review_id}/package/package_manifest.jsonl",
            }
        ],
        "next_action": "Run package context and applicability gates.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": True},
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )
    slot = result.summary["expansion_slots"][0]

    assert result.summary["expansion_failure_category_counts"] == {"applicability_miss": 1}
    assert result.summary["open_expansion_slot_count"] == 1
    assert slot["failure_categories"] == ["applicability_miss"]
    assert slot["review_id"] == "selected-review"
    assert slot["package_path"] == "source_library/reviews/_intake/selected-review"
    assert slot["source_set_id"] == "source-set-1"
    assert slot["expected_gate_artifacts"][0]["id"] == "package_manifest"
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "selected-review" in markdown
    assert "source_library/reviews/_intake/selected-review" in markdown
    assert "applicability_miss" in markdown


def test_promotion_suite_rejects_selected_slot_missing_contract_fields(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "selected_not_run",
        "ready": False,
        "failure_category": "applicability_miss",
        "review_id": "selected-review",
        "package_path": "source_library/reviews/_intake/selected-review",
        "next_action": "Run package context and applicability gates.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="source_set_id"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_rejects_selected_slot_package_fixture_missing(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "selected_not_run",
        "ready": False,
        "failure_category": "package_fixture_missing",
        "review_id": "selected-review",
        "package_path": "source_library/reviews/_intake/selected-review",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "package_manifest",
                "path": "reviews/{review_id}/package/package_manifest.jsonl",
            }
        ],
        "next_action": "Run package context and applicability gates.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="typed failure_category"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_rejects_ready_slot_with_failure_category(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0]["ready"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="ready but still has failure_category"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_rejects_ready_slot_missing_review_gate_contract(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].append(
        {
            "id": "expansion_review",
            "path": "reviews/{review_id}/expansion_review.json",
            "required_for_current_promotion": False,
            "required_for_expansion": True,
            "failure_category": "applicability_miss",
            "checks": [
                {
                    "name": "expansion_review_passed",
                    "json_path": "summary.passed",
                    "equals": True,
                }
            ],
        }
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "package_manifest",
                "path": "reviews/{review_id}/package/package_manifest.jsonl",
            }
        ],
        "next_action": "Keep the slot ready.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="expansion_review"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_expansion_requires_required_expansion_artifacts(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].append(
        {
            "id": "expansion_review",
            "path": "reviews/{review_id}/expansion_review.json",
            "required_for_current_promotion": False,
            "required_for_expansion": True,
            "failure_category": "applicability_miss",
            "checks": [
                {
                    "name": "expansion_review_passed",
                    "json_path": "summary.passed",
                    "equals": True,
                }
            ],
        }
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "expansion_review",
                "path": "reviews/{review_id}/expansion_review.json",
            }
        ],
        "next_action": "Keep the slot ready.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write_json(
        output_dir / "reviews" / "review-1" / "expansion_review.json",
        {"summary": {"passed": True}},
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["expansion_artifacts_ready"] is False
    assert result.summary["promotion_ready"] is True
    assert result.summary["failure_category_counts"] == {}
    assert result.summary["expansion_failure_category_counts"] == {
        "applicability_miss": 1,
    }
    assert result.summary["open_expansion_slot_count"] == 0
    assert result.summary["open_expansion_artifact_count"] == 1


def test_promotion_suite_fails_missing_required_artifact(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    (output_dir / "reviews" / "review-1" / "v1_ea_eval_results.json").unlink()

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert result.summary["current_promotion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert result.summary["failure_category_counts"]["stale_artifact"] == 1
    review_case = result.summary["review_cases"][0]
    missing_result = next(item for item in review_case["results"] if item["id"] == "v1_ea_eval")
    assert missing_result["checks"][0]["name"] == "artifact_exists"
    assert missing_result["checks"][0]["passed"] is False


def _write_suite_fixture(tmp_path: Path) -> tuple[Path, Path]:
    output_dir = tmp_path / "source_library"
    manifest_path = tmp_path / "promotion_suite.json"
    _write_json(
        tmp_path / "rule_pack.json",
        {
            "rule_pack_id": "rules-v0",
            "version": "1.0.0",
            "baseline_source_record_ids": ["R1EA-001", "R1EA-002"],
            "rules": [{"id": "rule-1"}, {"id": "rule-2"}],
        },
    )
    _write_json(
        manifest_path,
        {
            "schema_version": PROMOTION_SUITE_SCHEMA_VERSION,
            "id": "suite-1",
            "source_set_id": "source-set-1",
            "rule_pack_path": "rule_pack.json",
            "rule_pack_id": "rules-v0",
            "rule_pack_version": "1.0.0",
            "expected_rule_count": 2,
            "expected_baseline_source_record_count": 2,
            "review_cases": [
                {
                    "id": "case-1",
                    "review_id": "review-1",
                    "results": [
                        {
                            "id": "v1_ea_eval",
                            "path": "reviews/{review_id}/v1_ea_eval_results.json",
                            "failure_category": "stale_artifact",
                            "checks": [
                                {
                                    "name": "v1_passed",
                                    "json_path": "summary.passed",
                                    "equals": True,
                                }
                            ],
                        },
                        {
                            "id": "matrix_pdf",
                            "path": "reviews/{review_id}/compliance_matrix.pdf",
                            "format": "binary",
                            "failure_category": "stale_artifact",
                            "checks": [
                                {
                                    "name": "pdf_header",
                                    "starts_with": "%PDF-",
                                }
                            ],
                        },
                    ],
                }
            ],
            "suite_results": [
                {
                    "id": "phase_eval_core",
                    "path": "derived/{source_set_id}/evidence_graph/phase_eval_results.json",
                    "failure_category": "stale_artifact",
                    "checks": [
                        {
                            "name": "phase_count",
                            "json_path": "passed_phase_count",
                            "min": 2,
                        }
                    ],
                },
                {
                    "id": "post_v1_applicability_phase",
                    "path": "derived/{source_set_id}/evidence_graph/phase_eval_results.json",
                    "required_for_current_promotion": False,
                    "required_for_expansion": True,
                    "failure_category": "applicability_miss",
                    "checks": [
                        {
                            "name": "phase_ready_with_applicability",
                            "json_path": "reviewer_ready",
                            "equals": True,
                        }
                    ],
                },
            ],
            "expansion_slots": [
                {
                    "id": "slot-1",
                    "ready": False,
                    "failure_category": "package_fixture_missing",
                }
            ],
        },
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "v1_ea_eval_results.json",
        {"summary": {"passed": True}},
    )
    (output_dir / "reviews" / "review-1").mkdir(parents=True, exist_ok=True)
    (output_dir / "reviews" / "review-1" / "compliance_matrix.pdf").write_bytes(
        b"%PDF-1.4\n"
    )
    _write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": False},
    )
    return manifest_path, output_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
