from __future__ import annotations

import hashlib
import json
from pathlib import Path

from usfs_r1_ea_sources.final_qa_certification import run_final_qa_certification
from usfs_r1_ea_sources.final_qa_certification import validate_final_qa_certification_report


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "east_crazies_final_qa_certification_v1.json"
EXPECTED_SUMMARY_PATH = (
    REPO_ROOT
    / "config"
    / "fixtures"
    / "final_qa"
    / "v1_ecid_final_qa_expected_summary.json"
)
MINIMAL_REPORT_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "final_qa" / "minimal_final_qa_certification_report.json"
)
OUTPUT_SCHEMAS_PATH = REPO_ROOT / "docs" / "OUTPUT_SCHEMAS.md"

REQUIRED_SECTIONS = [
    "review_boundary",
    "gate_replay_summary",
    "artifact_freshness_ledger",
    "applicability_partition",
    "finding_qa",
    "forest_plan_qa",
    "decision_support_qa",
    "accepted_v1_risk_ledger",
    "certification_statement",
    "residual_blockers_and_stop_conditions",
]

REQUIRED_GATES = {
    "applicability_validation",
    "generated_rule_pack_validation",
    "compliance_validation",
    "compliance_matrix",
    "forest_plan_context",
    "forest_plan_component_eval",
    "decision_support_validation",
    "phase_eval",
    "v1_ea_eval",
    "current_promotion_suite",
}

EXPECTED_COUNTS = {
    "package_file_count": 43,
    "package_chunk_count": 1265,
    "baseline_source_record_count": 26,
    "candidate_authority_count": 373,
    "applicable_authority_count": 33,
    "non_applicable_authority_count": 340,
    "unresolved_authority_count": 0,
    "generated_rule_count": 33,
    "authority_finding_count": 33,
    "rule_claim_link_count": 142,
    "rule_claim_gap_count": 0,
    "compliance_matrix_authority_row_count": 33,
    "forest_plan_component_count": 329,
    "forest_plan_supported_component_count": 79,
    "forest_plan_not_applicable_component_count": 250,
    "forest_plan_gap_count": 0,
    "forest_plan_standard_count": 58,
    "applicable_standard_count": 12,
    "applied_standard_count": 12,
    "forest_plan_component_eval_case_count": 35,
    "phase_eval_phase_count": 19,
    "phase_eval_passed_phase_count": 19,
    "promotion_suite_required_current_result_count": 22,
    "promotion_suite_passed_required_current_result_count": 22,
    "accepted_v1_risk_count": 14,
    "actual_pending_applicable_count": 7,
    "litigation_risk_legal_conclusion_count": 0,
}

REQUIRED_FAILURE_CATEGORIES = {
    "missing_required_artifact",
    "unparseable_required_artifact",
    "stale_artifact",
    "review_source_set_mismatch",
    "input_hash_mismatch",
    "count_drift",
    "missing_required_gate_section",
    "missing_citation_or_source_selector",
    "missing_non_applicable_boundary_evidence",
    "unresolved_reviewer_item",
    "invalid_report_pdf_header",
    "manual_draft_dependency",
    "accepted_v1_risk_hidden",
    "legal_conclusion_leak",
    "human_certification_overclaim",
}

ACCEPTED_PENDING_RULE_IDS = {
    "directives_notice_comment_36cfr_216",
    "eo_11990_wetlands",
    "eo_13186_migratory_birds",
    "esa_consultation_50cfr_402",
    "esa_section_7",
    "mbta_migratory_birds",
    "montana_shpo_review",
    "nepa_4336b_programmatic_tiering",
    "nepa_4336f_sponsor_prepared_documents",
    "nhpa_36cfr_800",
    "nhpa_section_106",
    "postdecisional_review_36cfr_214",
    "roadless_rule_36cfr_294b",
    "usda_nepa_applicant_docs_7cfr_1b10",
}


def test_sequence_1_config_owns_sections_gates_counts_and_signoff() -> None:
    config = _read_json(CONFIG_PATH)

    assert config["schema_version"] == "east-crazies-final-qa-certification-config-v1"
    assert config["review_id"] == "v1-cg-ecid-compliance-review"
    assert config["source_set_id"] == "source-set-ba8d0feae79501b8"
    assert config["section_order"] == REQUIRED_SECTIONS
    assert set(config["required_gate_names"]) == REQUIRED_GATES
    assert config["manual_draft_policy"]["root_east_crazies_drafts_are_canonical"] is False
    assert config["manual_draft_policy"]["blocked_path_prefixes"] == ["East_Crazies_"]
    assert "legal sufficiency determination" in config["certification_caveat"]

    gate_names = {gate["gate_name"] for gate in config["required_gates"]}
    assert gate_names == REQUIRED_GATES
    for gate in config["required_gates"]:
        assert gate["artifact_path"].startswith("source_library/")
        assert "East_Crazies_" not in gate["artifact_path"]
        assert gate["required_pass_selector"]
        assert gate["failure_category"] in REQUIRED_FAILURE_CATEGORIES

    count_fields = {row["field"]: row for row in config["required_count_fields"]}
    expected_count_fields = set(EXPECTED_COUNTS) - {"authority_finding_status_counts"}
    expected_count_fields.add("authority_finding_status_counts.pass")
    assert set(count_fields) == expected_count_fields
    for field, expected in EXPECTED_COUNTS.items():
        if field == "authority_finding_status_counts":
            assert count_fields["authority_finding_status_counts.pass"]["expected"] == (
                expected["pass"]
            )
        else:
            assert count_fields[field]["expected"] == expected
        assert count_fields[
            field if field != "authority_finding_status_counts" else (
                "authority_finding_status_counts.pass"
            )
        ]["source_selector"]

    signoff_fields = {row["field"] for row in config["reviewer_signoff_fields"]}
    assert {
        "reviewer_name",
        "reviewer_role",
        "reviewer_signature",
        "review_date",
        "reviewer_notes",
    } <= signoff_fields
    assert all(
        row["required_for_machine_validation"] is False
        for row in config["reviewer_signoff_fields"]
    )


def test_sequence_1_config_declares_fail_closed_acceptance_categories() -> None:
    config = _read_json(CONFIG_PATH)

    assert REQUIRED_FAILURE_CATEGORIES <= set(config["failure_categories"])
    assert "legal_conclusion_leak" in config["failure_categories"]
    assert "human_certification_overclaim" in config["failure_categories"]
    assert "accepted_v1_risk_hidden" in config["failure_categories"]
    assert "invalid_report_pdf_header" in config["failure_categories"]

    prohibited = set(config["prohibited_certification_phrases"])
    assert "legal sufficiency certified" in prohibited
    assert "responsible official approved" in prohibited
    assert config["rendering_requirements"]["pdf_header"] == "%PDF-"
    assert "Accepted V1 Risk Ledger" in config["rendering_requirements"][
        "markdown_required_text"
    ]

    expectation_categories = {
        row["required_failure_category"] for row in config["validation_expectations"]
    }
    assert {
        "missing_required_gate_section",
        "input_hash_mismatch",
        "stale_artifact",
        "count_drift",
        "missing_citation_or_source_selector",
        "missing_non_applicable_boundary_evidence",
        "unresolved_reviewer_item",
        "invalid_report_pdf_header",
        "manual_draft_dependency",
        "accepted_v1_risk_hidden",
        "legal_conclusion_leak",
        "human_certification_overclaim",
    } <= expectation_categories
    assert expectation_categories <= set(config["failure_categories"])
    for expectation in config["validation_expectations"]:
        assert expectation["expectation_id"]
        assert expectation["source_selector"]


def test_sequence_1_config_and_expected_summary_stay_aligned() -> None:
    config = _read_json(CONFIG_PATH)
    expected = _read_json(EXPECTED_SUMMARY_PATH)

    assert config["review_id"] == expected["review_id"]
    assert config["source_set_id"] == expected["source_set_id"]
    assert config["report_schema_version"] == expected["expected_report_schema_version"]
    assert config["manifest_schema_version"] == expected["expected_manifest_schema_version"]
    assert config["expected_summary_schema_version"] == expected["schema_version"]
    assert config["section_order"] == expected["required_sections"]
    assert config["required_output_files"] == expected["required_output_files"]
    assert config["failure_categories"] == expected["failure_categories"]
    assert config["manual_draft_policy"]["root_east_crazies_drafts_are_canonical"] == (
        expected["manual_draft_policy"]["root_east_crazies_drafts_are_canonical"]
    )
    assert config["rendering_requirements"]["pdf_header"] == expected["rendering_contract"][
        "pdf_header"
    ]

    config_count_fields = {row["field"]: row["expected"] for row in config["required_count_fields"]}
    for field, value in expected["expected_counts"].items():
        if field == "authority_finding_status_counts":
            assert config_count_fields["authority_finding_status_counts.pass"] == value["pass"]
        else:
            assert config_count_fields[field] == value


def test_expected_summary_locks_current_counts_hashes_and_representative_rows() -> None:
    expected = _read_json(EXPECTED_SUMMARY_PATH)

    assert expected["schema_version"] == "east-crazies-final-qa-expected-summary-v1"
    assert expected["required_sections"] == REQUIRED_SECTIONS
    for key, value in EXPECTED_COUNTS.items():
        assert expected["expected_counts"][key] == value
    assert expected["expected_counts"]["authority_finding_status_counts"]["pass"] == 33

    assert set(expected["input_hashes"]) >= {
        "decision_support_report_sha256",
        "decision_support_markdown_sha256",
        "decision_support_pdf_sha256",
        "decision_support_manifest_sha256",
        "v1_ea_eval_results_sha256",
        "phase_eval_results_sha256",
        "promotion_suite_results_sha256",
        "compliance_validation_sha256",
        "applicability_validation_sha256",
        "generated_rule_pack_validation_sha256",
        "compliance_matrix_sha256",
        "forest_plan_component_eval_results_sha256",
    }

    applicable = expected["required_fixture_rows"]["applicable_authority"]
    assert applicable["rule_id"] == "eo_11990_wetlands"
    assert applicable["status"] == "pass"
    assert applicable["applicability_status"] == "applicable"
    assert applicable["source_selectors"]

    non_applicable = expected["required_fixture_rows"]["non_applicable_authority"]
    assert non_applicable["status"] == "not_applicable"
    assert non_applicable["coverage_certificate"]["coverage_result"] == "sufficient"
    assert non_applicable["coverage_certificate"]["missing_query_variants"] == []
    assert non_applicable["source_selectors"]

    standard = expected["required_fixture_rows"]["forest_plan_standard"]
    assert standard["component_key"] == "FW-STD-RMZ-01"
    assert standard["applicability_status"] == "applicable"
    assert standard["compliance_status"] == "complies"
    assert standard["source_selectors"]

    risk = expected["required_fixture_rows"]["decision_support_residual_risk"]
    assert risk["category"] == "non_applicable_authority_boundary"
    assert risk["deterministic_basis"] is True
    assert risk["legal_conclusion"] is False
    assert risk["source_artifact_path"].endswith("litigation_risk_summary.json")


def test_expected_summary_carries_accepted_v1_risk_ledger() -> None:
    expected = _read_json(EXPECTED_SUMMARY_PATH)
    ledger = expected["accepted_v1_risk_ledger"]

    assert ledger["policy_mode"] == "accepted_pending_v1"
    assert ledger["accepted_pending_count"] == 14
    assert ledger["actual_pending_count"] == 14
    assert ledger["actual_pending_applicable_count"] == 7
    assert set(ledger["accepted_pending_rule_ids"]) == ACCEPTED_PENDING_RULE_IDS
    assert ledger["source_artifact_path"].endswith("v1_ea_eval_results.json")
    assert ledger["source_selector"] == "conditional_adjudication"
    assert any(
        row["rule_id"] == "eo_11990_wetlands"
        and row["actual_applicability"] == "applicable"
        for row in ledger["representative_pending_rows"]
    )

    assert REQUIRED_FAILURE_CATEGORIES <= set(expected["failure_categories"])
    assert expected["manual_draft_policy"]["root_east_crazies_drafts_are_canonical"] is False
    assert expected["rendering_contract"]["pin_full_rendered_body_text"] is False


def test_minimal_report_fixture_locks_schema_boundary_without_source_library() -> None:
    report = _read_json(MINIMAL_REPORT_PATH)

    assert report["schema_version"] == "east-crazies-final-qa-certification-report-v1"
    assert all(section in report for section in REQUIRED_SECTIONS)
    assert report["manifest"]["schema_version"] == (
        "east-crazies-final-qa-certification-manifest-v1"
    )
    assert report["manifest"]["validation_status"] == "passed"
    assert report["review_boundary"]["legal_conclusion"] is False
    assert report["gate_replay_summary"]["machine_replay_status"] == "passed"
    assert report["certification_statement"]["legal_conclusion"] is False
    assert "does not replace responsible official" in report["certification_statement"]["caveat"]

    assert report["applicability_partition"]["unresolved_authority_count"] == 0
    assert report["finding_qa"]["rule_claim_gap_count"] == 0
    assert report["forest_plan_qa"]["component_eval_passed"] is True
    assert report["decision_support_qa"]["pdf_header_valid"] is True
    assert report["accepted_v1_risk_ledger"]["policy_mode"] == "accepted_pending_v1"
    assert report["accepted_v1_risk_ledger"]["risks"][0]["hidden_as_pass_finding"] is False


def test_minimal_report_fixture_keeps_citations_selectors_and_risk_boundaries() -> None:
    report = _read_json(MINIMAL_REPORT_PATH)

    boundary = report["applicability_partition"]["non_applicable_boundary_evidence"][0]
    assert boundary["coverage_result"] == "sufficient"
    assert boundary["source_artifact_path"].endswith("search_coverage_certificates.json")
    assert boundary["source_selector"]

    finding = report["finding_qa"]["findings"][0]
    assert finding["ea_package_citation"]
    assert finding["source_library_citation"]
    assert finding["source_claim_ids"]
    assert finding["source_selectors"]

    standard = report["forest_plan_qa"]["applicable_standards"][0]
    assert standard["package_evidence"][0]["citation_label"]
    assert standard["forest_plan_evidence"][0]["citation_label"]

    residual_risk = report["decision_support_qa"]["residual_risk_rows"][0]
    assert residual_risk["deterministic_basis"] is True
    assert residual_risk["legal_conclusion"] is False
    assert residual_risk["source_selector"]

    signoff = report["certification_statement"]["reviewer_signoff"]
    assert set(signoff) == {
        "reviewer_name",
        "reviewer_role",
        "reviewer_signature",
        "review_date",
        "reviewer_notes",
    }


def test_output_schema_docs_record_final_qa_contract() -> None:
    docs = OUTPUT_SCHEMAS_PATH.read_text(encoding="utf-8")

    for required_text in [
        "East Crazies Final QA And Certification Outputs",
        "east-crazies-final-qa-certification-report-v1",
        "east-crazies-final-qa-certification-manifest-v1",
        "east-crazies-final-qa-certification-validation-v1",
        "east-crazies-final-qa-certification-config-v1",
        "east-crazies-final-qa-expected-summary-v1",
        "accepted_v1_risk_ledger",
        "reviewer_signoff",
        "validation_expectations",
        "human_certification_overclaim",
        "accepted_v1_risk_hidden",
        "East_Crazies_*",
    ]:
        assert required_text in docs


def test_sequence_2_generator_writes_and_validates_report_family(tmp_path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    results_dir = tmp_path / "final-qa-output"

    result = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert result.summary["passed"] is True
    assert result.summary["output_written"] is True
    assert result.report_path.exists()
    assert result.markdown_path.exists()
    assert result.pdf_path.read_bytes().startswith(b"%PDF-")
    assert result.manifest_path.exists()
    assert result.validation_path.exists()
    validation_payload = _read_json(result.validation_path)
    assert validation_payload["output_hashes"]["json_sha256"] == _sha256(result.report_path)
    assert validation_payload["output_hashes"]["markdown_sha256"] == _sha256(
        result.markdown_path
    )
    assert validation_payload["output_hashes"]["pdf_sha256"] == _sha256(result.pdf_path)
    assert validation_payload["output_hashes"]["manifest_sha256"] == _sha256(
        result.manifest_path
    )

    report = _read_json(result.report_path)
    assert report["schema_version"] == "east-crazies-final-qa-certification-report-v1"
    assert report["gate_replay_summary"]["machine_replay_status"] == "passed"
    assert report["applicability_partition"]["non_applicable_authority_count"] == 1
    assert len(report["finding_qa"]["findings"]) == 2
    assert report["finding_qa"]["authority_finding_status_counts"]["pass"] == 2
    assert all(finding["source_pointers"] for finding in report["finding_qa"]["findings"])
    assert report["accepted_v1_risk_ledger"]["accepted_pending_count"] == 2
    assert report["accepted_v1_risk_ledger"]["risks"][0]["hidden_as_pass_finding"] is False
    assert report["certification_statement"]["legal_conclusion"] is False
    assert "does not replace responsible official" in report["certification_statement"]["caveat"]

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert validation.summary["passed"] is True
    assert validation.summary["output_written"] is False


def test_sequence_2_validate_only_fails_closed_when_packet_missing(tmp_path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)

    result = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=tmp_path / "missing-final-qa-output",
    )

    assert result.summary["passed"] is False
    assert result.summary["failure_category_counts"]["missing_required_artifact"] == 5


def test_final_qa_validate_allows_only_outer_gate_self_reference(tmp_path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    results_dir = tmp_path / "final-qa-output"

    generated = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert generated.summary["passed"] is True

    review_dir = output_dir / "reviews" / "review-test"
    phase_eval = _read_json(review_dir / "phase_eval_results.json")
    phase_eval["phase_count"] = 3
    phase_eval["passed_phase_count"] = 3
    phase_eval["reviewer_ready_phase_count"] = 3
    phase_eval["phases"] = [
        {"name": "base_1", "passed": True, "reviewer_ready": True},
        {"name": "base_2", "passed": True, "reviewer_ready": True},
        {
            "name": "final_qa_certification_report",
            "passed": True,
            "reviewer_ready": True,
        },
    ]
    _write_json_file(review_dir / "phase_eval_results.json", phase_eval)

    suite_path = (
        output_dir
        / "reviews"
        / "promotion_suite"
        / "post-v1-region1-ea-promotion-suite"
        / "promotion_suite_results.json"
    )
    suite = _read_json(suite_path)
    suite["required_current_result_count"] = 6
    suite["passed_required_current_result_count"] = 6
    suite["review_cases"] = [
        {
            "id": "v1-cg-ecid",
            "results": [
                {
                    "id": result_id,
                    "required_for_current_promotion": True,
                    "passed": True,
                }
                for result_id in [
                    "final_qa_certification_report",
                    "final_qa_certification_manifest",
                    "final_qa_certification_pdf",
                    "final_qa_certification_validation",
                ]
            ],
        }
    ]
    _write_json_file(suite_path, suite)

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert validation.summary["passed"] is True
    assert validation.summary["failure_category_counts"] == {}

    regenerated = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert regenerated.summary["passed"] is True
    report = _read_json(regenerated.report_path)
    phase_summary = report["gate_replay_summary"]["phase_eval"]
    promotion_summary = report["gate_replay_summary"]["current_promotion_suite"]
    assert phase_summary["phase_count"] == 2
    assert phase_summary["passed_phase_count"] == 2
    assert phase_summary["live_phase_count"] == 3
    assert phase_summary["live_passed_phase_count"] == 3
    assert phase_summary["final_qa_self_reference_phase_count"] == 1
    assert promotion_summary["required_current_result_count"] == 2
    assert promotion_summary["passed_required_current_result_count"] == 2
    assert promotion_summary["live_required_current_result_count"] == 6
    assert promotion_summary["live_passed_required_current_result_count"] == 6
    assert promotion_summary["final_qa_current_result_count"] == 4
    markdown = regenerated.markdown_path.read_text(encoding="utf-8")
    assert "Phase eval baseline excluding final QA self-reference: `2/2`" in markdown
    assert "Phase eval live gate: `3/3`" in markdown
    assert (
        "Current promotion suite baseline excluding final QA packet gates: `2/2`"
        in markdown
    )
    assert "Current promotion suite live gate: `6/6`" in markdown


def test_final_qa_validate_fails_when_validation_sidecar_output_hash_is_stale(
    tmp_path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    results_dir = tmp_path / "final-qa-output"

    result = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert result.summary["passed"] is True
    result.report_path.write_text(
        result.report_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert validation.summary["passed"] is False
    assert validation.summary["failure_category_counts"]["stale_artifact"] == 1


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_sequence_2_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    output_dir = tmp_path / "source_library"
    review_id = "review-test"
    source_set_id = "source-set-test"
    review_dir = output_dir / "reviews" / review_id
    decision_dir = review_dir / "decision_support"
    app_dir = review_dir / "applicability"
    suite_dir = output_dir / "reviews" / "promotion_suite" / "post-v1-region1-ea-promotion-suite"
    decision_dir.mkdir(parents=True)
    app_dir.mkdir(parents=True)
    suite_dir.mkdir(parents=True)

    _write_json_file(
        decision_dir / "ea_consistency_decision_support.json",
        {
            "schema_version": "ea-consistency-decision-support-report-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "record_and_artifact_inventory": {
                "package_file_count": 2,
                "package_chunk_count": 4,
            },
            "implementation_confirmation_checklist": [
                {"confirmation_id": "synthetic", "status": "confirmed"}
            ],
        },
    )
    (decision_dir / "ea_consistency_decision_support.md").write_text(
        "# Decision Support\n",
        encoding="utf-8",
    )
    (decision_dir / "ea_consistency_decision_support.pdf").write_bytes(b"%PDF-1.4\n")
    _write_json_file(
        decision_dir / "ea_consistency_decision_support_manifest.json",
        {
            "schema_version": "ea-consistency-decision-support-manifest-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation_status": "passed",
        },
    )
    _write_json_file(
        app_dir / "applicability_validation.json",
        {
            "schema_version": "applicability-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "reviewer_ready": True,
            "generated_rule_pack_ready": True,
            "candidate_authority_count": 3,
            "applicable_authority_count": 2,
            "non_applicable_authority_count": 1,
            "unresolved_authority_count": 0,
        },
    )
    _write_json_file(
        app_dir / "generated_rule_pack_validation.json",
        {
            "schema_version": "generated-rule-pack-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "generated_rule_pack_ready": True,
            "summary": {"generated_rule_count": 2},
        },
    )
    _write_json_file(
        app_dir / "non_applicable_authorities.json",
        {
            "schema_version": "non-applicable-authorities-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "authorities": [],
        },
    )
    _write_json_file(
        review_dir / "compliance_validation.json",
        {
            "schema_version": "compliance-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
        },
    )
    _write_json_file(
        review_dir / "compliance_review.json",
        {
            "schema_version": "compliance-review-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_path": "source_library/reviews/_intake/synthetic",
            "baseline_source_record_count": 2,
            "finding_count": 2,
            "finding_status_counts": {"pass": 2},
            "rule_claim_link_count": 5,
            "rule_claim_gap_count": 0,
        },
    )
    _write_json_file(
        review_dir / "compliance_matrix.json",
        {
            "schema_version": "compliance-matrix-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "validated": True,
                "row_count": 2,
                "authority_integration": {"legal_conclusion_count": 0},
                "forest_plan_review": {
                    "component_evaluation": {
                        "component_count": 3,
                        "supported_count": 2,
                        "not_applicable_count": 1,
                        "gap_count": 0,
                        "standard_count": 1,
                        "applicable_standard_count": 1,
                        "applied_standard_count": 1,
                    }
                },
            },
            "rows": [
                _sequence_2_matrix_row(
                    rule_id="rule-a",
                    candidate_authority_id="candidate:rule-a",
                    applicability_decision_id="decision-rule-a",
                ),
                _sequence_2_matrix_row(
                    rule_id="rule-b",
                    candidate_authority_id="candidate:rule-b",
                    applicability_decision_id="decision-rule-b",
                ),
            ],
        },
    )
    (review_dir / "compliance_matrix.pdf").write_bytes(b"%PDF-1.4\n")
    _write_json_file(
        review_dir / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "reviewer_ready": True,
            "scope_status": "custer_gallatin",
        },
    )
    _write_json_file(
        review_dir / "forest_plan_component_eval_results.json",
        {
            "schema_version": "forest-plan-component-eval-results-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "case_count": 2,
        },
    )
    _write_json_file(
        review_dir / "forest_plan_applicable_standard_coverage.json",
        {
            "schema_version": "forest-plan-applicable-standard-coverage-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "standards": [],
        },
    )
    _write_json_file(
        review_dir / "litigation_risk_summary.json",
        {
            "schema_version": "litigation-risk-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {"legal_conclusion_count": 0},
        },
    )
    _write_json_file(
        review_dir / "phase_eval_results.json",
        {
            "schema_version": "phase-eval-results-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "reviewer_ready": True,
            "phase_count": 2,
            "passed_phase_count": 2,
        },
    )
    _write_json_file(
        review_dir / "v1_ea_eval_results.json",
        {
            "schema_version": "v1-ea-real-review-eval-results-v0",
            "review_id": review_id,
            "passed": True,
            "conditional_adjudication": {
                "policy_mode": "accepted_pending_v1",
                "accepted_pending_count": 2,
                "actual_pending_count": 2,
                "actual_pending_applicable_count": 1,
                "accepted_pending_rule_ids": ["rule-a", "rule-b"],
                "pending_results": [
                    {
                        "rule_id": "rule-a",
                        "actual_applicability": "applicable",
                        "actual_status": "pass",
                        "classification_rationale": "Synthetic pending risk.",
                        "actual_source_record_ids": ["R1EA-TEST"],
                    },
                    {
                        "rule_id": "rule-b",
                        "actual_applicability": "not_applicable",
                        "actual_status": "not_applicable",
                        "classification_rationale": "Synthetic pending risk.",
                        "actual_source_record_ids": ["R1EA-NON"],
                    },
                ],
            },
        },
    )
    _write_json_file(
        suite_dir / "promotion_suite_results.json",
        {
            "schema_version": "promotion-suite-results-v1",
            "source_set_id": source_set_id,
            "current_promotion_ready": True,
            "required_current_result_count": 2,
            "passed_required_current_result_count": 2,
            "expansion_failure_category_counts": {},
        },
    )

    config = _sequence_2_config(review_id, source_set_id)
    expected = _sequence_2_expected(output_dir, review_id, source_set_id)
    config_path = tmp_path / "final_qa_config.json"
    expected_path = tmp_path / "final_qa_expected.json"
    _write_json_file(config_path, config)
    _write_json_file(expected_path, expected)
    return output_dir, config_path, expected_path


def _sequence_2_config(review_id: str, source_set_id: str) -> dict:
    review_root = f"source_library/reviews/{review_id}"
    expected_counts = _sequence_2_counts()
    return {
        "schema_version": "east-crazies-final-qa-certification-config-v1",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "report_schema_version": "east-crazies-final-qa-certification-report-v1",
        "manifest_schema_version": "east-crazies-final-qa-certification-manifest-v1",
        "expected_summary_schema_version": "east-crazies-final-qa-expected-summary-v1",
        "certification_caveat": "Machine QA only.",
        "manual_draft_policy": {
            "root_east_crazies_drafts_are_canonical": False,
            "blocked_path_prefixes": ["East_Crazies_"],
        },
        "section_order": REQUIRED_SECTIONS,
        "required_output_files": [
            "east_crazies_final_qa_certification.json",
            "east_crazies_final_qa_certification.md",
            "east_crazies_final_qa_certification.pdf",
            "east_crazies_final_qa_certification_manifest.json",
            "east_crazies_final_qa_certification_validation.json",
        ],
        "required_gate_names": list(REQUIRED_GATES),
        "required_gates": [
            _gate("applicability_validation", f"{review_root}/applicability/applicability_validation.json", "passed", True),
            _gate("generated_rule_pack_validation", f"{review_root}/applicability/generated_rule_pack_validation.json", "generated_rule_pack_ready", True),
            _gate("compliance_validation", f"{review_root}/compliance_validation.json", "passed", True),
            _gate("compliance_matrix", f"{review_root}/compliance_matrix.json", "summary.validated", True),
            _gate("forest_plan_context", f"{review_root}/forest_plan_context_summary.json", "reviewer_ready", True),
            _gate("forest_plan_component_eval", f"{review_root}/forest_plan_component_eval_results.json", "passed", True),
            _gate("decision_support_validation", f"{review_root}/decision_support/ea_consistency_decision_support_manifest.json", "validation_status", "passed"),
            _gate("phase_eval", f"{review_root}/phase_eval_results.json", "reviewer_ready", True),
            _gate("v1_ea_eval", f"{review_root}/v1_ea_eval_results.json", "passed", True),
            _gate(
                "current_promotion_suite",
                "source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json",
                "current_promotion_ready",
                True,
            ),
        ],
        "required_count_fields": [
            {
                "field": field,
                "expected": value["pass"] if field == "authority_finding_status_counts.pass" else value,
                "source_selector": _sequence_2_count_selector(field),
                "failure_category": "count_drift",
            }
            for field, value in expected_counts.items()
        ],
        "reviewer_signoff_fields": [
            {"field": "reviewer_name", "required_for_machine_validation": False},
            {"field": "reviewer_role", "required_for_machine_validation": False},
            {"field": "reviewer_signature", "required_for_machine_validation": False},
            {"field": "review_date", "required_for_machine_validation": False},
            {"field": "reviewer_notes", "required_for_machine_validation": False},
        ],
        "prohibited_certification_phrases": [
            "legal sufficiency certified",
            "responsible official approved",
        ],
        "rendering_requirements": {
            "markdown_required_text": [
                "How To Use This Packet",
                "Machine Replay Status",
                "Accepted V1 Risk Ledger",
                "Reviewer Signoff",
                "does not replace responsible official, line officer, counsel, or specialist judgment",
            ],
            "pdf_required_text_markers": [
                "Machine Replay Status",
                "Accepted V1 Risk Ledger",
                "Reviewer Signoff",
            ],
            "pdf_header": "%PDF-",
        },
        "failure_categories": list(REQUIRED_FAILURE_CATEGORIES),
    }


def _sequence_2_expected(output_dir: Path, review_id: str, source_set_id: str) -> dict:
    expected = {
        "schema_version": "east-crazies-final-qa-expected-summary-v1",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "expected_report_schema_version": "east-crazies-final-qa-certification-report-v1",
        "expected_manifest_schema_version": "east-crazies-final-qa-certification-manifest-v1",
        "required_output_files": [
            "east_crazies_final_qa_certification.json",
            "east_crazies_final_qa_certification.md",
            "east_crazies_final_qa_certification.pdf",
            "east_crazies_final_qa_certification_manifest.json",
            "east_crazies_final_qa_certification_validation.json",
        ],
        "required_sections": REQUIRED_SECTIONS,
        "expected_counts": _sequence_2_counts(),
        "input_hashes": {},
        "required_fixture_rows": {
            "applicable_authority": {
                "rule_id": "rule-a",
                "status": "pass",
                "applicability_status": "applicable",
                "ea_package_citation": "EA-PACKAGE-001 (test)",
                "source_library_citation": "R1EA-TEST (test)",
                "source_claim_ids": ["claim:test"],
                "source_selectors": [
                    {
                        "artifact_path": f"source_library/reviews/{review_id}/compliance_matrix.json",
                        "selector": "rows[rule_id=rule-a]",
                    }
                ],
            },
            "non_applicable_authority": {
                "candidate_authority_id": "candidate:rule-b",
                "status": "not_applicable",
                "coverage_certificate": {
                    "coverage_result": "sufficient",
                    "missing_query_variants": [],
                },
                "source_selectors": [
                    {
                        "artifact_path": f"source_library/reviews/{review_id}/applicability/non_applicable_authorities.json",
                        "selector": "authorities[candidate_authority_id=candidate:rule-b]",
                    }
                ],
            },
            "forest_plan_standard": {
                "component_id": "component-1",
                "component_key": "FW-STD-01",
                "component_type": "standard",
                "applicability_status": "applicable",
                "compliance_status": "complies",
                "finding_status": "supported",
                "ea_package_citation": "EA-PACKAGE-002 (test)",
                "forest_plan_citation": "R1PLAN-TEST (test)",
                "source_selectors": [
                    {
                        "artifact_path": f"source_library/reviews/{review_id}/forest_plan_applicable_standard_coverage.json",
                        "selector": "standards[component_key=FW-STD-01]",
                    }
                ],
            },
            "decision_support_residual_risk": {
                "risk_id": "risk:test",
                "category": "synthetic",
                "deterministic_basis": True,
                "legal_conclusion": False,
                "source_artifact_path": f"source_library/reviews/{review_id}/litigation_risk_summary.json",
                "source_selector": "summary",
            },
        },
        "accepted_v1_risk_ledger": {
            "policy_mode": "accepted_pending_v1",
            "accepted_pending_count": 2,
            "actual_pending_count": 2,
            "actual_pending_applicable_count": 1,
            "source_artifact_path": f"source_library/reviews/{review_id}/v1_ea_eval_results.json",
            "source_selector": "conditional_adjudication",
            "accepted_pending_rule_ids": ["rule-a", "rule-b"],
            "representative_pending_rows": [],
        },
        "failure_categories": list(REQUIRED_FAILURE_CATEGORIES),
        "manual_draft_policy": {"root_east_crazies_drafts_are_canonical": False},
    }
    hash_paths = {
        "decision_support_report_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support.json",
        "decision_support_markdown_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support.md",
        "decision_support_pdf_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support.pdf",
        "decision_support_manifest_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support_manifest.json",
        "v1_ea_eval_results_sha256": output_dir / "reviews" / review_id / "v1_ea_eval_results.json",
        "phase_eval_results_sha256": output_dir / "reviews" / review_id / "phase_eval_results.json",
        "promotion_suite_results_sha256": output_dir / "reviews" / "promotion_suite" / "post-v1-region1-ea-promotion-suite" / "promotion_suite_results.json",
        "compliance_validation_sha256": output_dir / "reviews" / review_id / "compliance_validation.json",
        "applicability_validation_sha256": output_dir / "reviews" / review_id / "applicability" / "applicability_validation.json",
        "generated_rule_pack_validation_sha256": output_dir / "reviews" / review_id / "applicability" / "generated_rule_pack_validation.json",
        "compliance_matrix_sha256": output_dir / "reviews" / review_id / "compliance_matrix.json",
        "compliance_matrix_pdf_sha256": output_dir / "reviews" / review_id / "compliance_matrix.pdf",
        "compliance_review_sha256": output_dir / "reviews" / review_id / "compliance_review.json",
        "forest_plan_context_summary_sha256": output_dir / "reviews" / review_id / "forest_plan_context_summary.json",
        "forest_plan_component_eval_results_sha256": output_dir / "reviews" / review_id / "forest_plan_component_eval_results.json",
    }
    expected["input_hashes"] = {key: _sha256(path) for key, path in hash_paths.items()}
    return expected


def _sequence_2_counts() -> dict:
    return {
        "package_file_count": 2,
        "package_chunk_count": 4,
        "baseline_source_record_count": 2,
        "candidate_authority_count": 3,
        "applicable_authority_count": 2,
        "non_applicable_authority_count": 1,
        "unresolved_authority_count": 0,
        "generated_rule_count": 2,
        "authority_finding_count": 2,
        "authority_finding_status_counts.pass": {"pass": 2},
        "rule_claim_link_count": 5,
        "rule_claim_gap_count": 0,
        "compliance_matrix_authority_row_count": 2,
        "forest_plan_component_count": 3,
        "forest_plan_supported_component_count": 2,
        "forest_plan_not_applicable_component_count": 1,
        "forest_plan_gap_count": 0,
        "forest_plan_standard_count": 1,
        "applicable_standard_count": 1,
        "applied_standard_count": 1,
        "forest_plan_component_eval_case_count": 2,
        "phase_eval_phase_count": 2,
        "phase_eval_passed_phase_count": 2,
        "promotion_suite_required_current_result_count": 2,
        "promotion_suite_passed_required_current_result_count": 2,
        "accepted_v1_risk_count": 2,
        "actual_pending_applicable_count": 1,
        "litigation_risk_legal_conclusion_count": 0,
    }


def _sequence_2_count_selector(field: str) -> str:
    return {
        "package_file_count": "review_boundary.package_file_count",
        "package_chunk_count": "review_boundary.package_chunk_count",
        "baseline_source_record_count": "review_boundary.baseline_source_record_count",
        "candidate_authority_count": "applicability_partition.candidate_authority_count",
        "applicable_authority_count": "applicability_partition.applicable_authority_count",
        "non_applicable_authority_count": "applicability_partition.non_applicable_authority_count",
        "unresolved_authority_count": "applicability_partition.unresolved_authority_count",
        "generated_rule_count": "finding_qa.generated_rule_count",
        "authority_finding_count": "finding_qa.authority_finding_count",
        "authority_finding_status_counts.pass": "finding_qa.authority_finding_status_counts.pass",
        "rule_claim_link_count": "finding_qa.rule_claim_link_count",
        "rule_claim_gap_count": "finding_qa.rule_claim_gap_count",
        "compliance_matrix_authority_row_count": "finding_qa.compliance_matrix_authority_row_count",
        "forest_plan_component_count": "forest_plan_qa.component_count",
        "forest_plan_supported_component_count": "forest_plan_qa.supported_component_count",
        "forest_plan_not_applicable_component_count": "forest_plan_qa.not_applicable_component_count",
        "forest_plan_gap_count": "forest_plan_qa.gap_count",
        "forest_plan_standard_count": "forest_plan_qa.standard_count",
        "applicable_standard_count": "forest_plan_qa.applicable_standard_count",
        "applied_standard_count": "forest_plan_qa.applied_standard_count",
        "forest_plan_component_eval_case_count": "forest_plan_qa.component_eval.case_count",
        "phase_eval_phase_count": "gate_replay_summary.phase_eval.phase_count",
        "phase_eval_passed_phase_count": "gate_replay_summary.phase_eval.passed_phase_count",
        "promotion_suite_required_current_result_count": "gate_replay_summary.current_promotion_suite.required_current_result_count",
        "promotion_suite_passed_required_current_result_count": "gate_replay_summary.current_promotion_suite.passed_required_current_result_count",
        "accepted_v1_risk_count": "accepted_v1_risk_ledger.accepted_pending_count",
        "actual_pending_applicable_count": "accepted_v1_risk_ledger.actual_pending_applicable_count",
        "litigation_risk_legal_conclusion_count": "decision_support_qa.litigation_risk_legal_conclusion_count",
    }[field]


def _gate(name: str, path: str, selector: str, expected: object) -> dict:
    return {
        "gate_name": name,
        "artifact_path": path,
        "required_pass_selector": selector,
        "expected_value": expected,
        "failure_category": "stale_artifact",
    }


def _sequence_2_matrix_row(
    *,
    rule_id: str,
    candidate_authority_id: str,
    applicability_decision_id: str,
) -> dict:
    return {
        "row_id": f"matrix:review-test:{rule_id}",
        "rule_id": rule_id,
        "rule_title": f"Synthetic {rule_id}",
        "status": "pass",
        "claim_type": "supported_compliance_finding",
        "authority_category": "law",
        "authority_family_ids": ["synthetic_family"],
        "authority_source_record_id": "R1EA-TEST",
        "candidate_authority_id": candidate_authority_id,
        "applicability_decision_id": applicability_decision_id,
        "applicability_mode": "conditional",
        "applicability_status": "applicable",
        "ea_package_citation": "EA-PACKAGE-001 (test)",
        "source_library_citation": "R1EA-TEST (test)",
        "source_claim_ids": [f"claim:{rule_id}"],
        "source_claim_count": 1,
        "search_coverage_certificate_ids": [],
        "human_adjudication_refs": [],
        "ea_package_evidence": {
            "artifact_path": "source_library/reviews/_intake/synthetic/package.pdf",
            "artifact_sha256": f"sha256-package-{rule_id}",
            "chunk_id": f"chunk:package:{rule_id}",
            "citation_label": "EA-PACKAGE-001 (test)",
            "content_sha256": f"sha256-package-content-{rule_id}",
            "source_record_id": "EA-PACKAGE-001",
        },
        "source_library_evidence": {
            "artifact_path": "source_library/artifacts/raw/synthetic.html",
            "artifact_sha256": f"sha256-source-{rule_id}",
            "chunk_id": f"chunk:source:{rule_id}",
            "citation_label": "R1EA-TEST (test)",
            "content_sha256": f"sha256-source-content-{rule_id}",
            "source_record_id": "R1EA-TEST",
        },
    }


def _write_json_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
