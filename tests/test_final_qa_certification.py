from __future__ import annotations

import json
from pathlib import Path


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
    "forest_plan_component_count": 329,
    "forest_plan_standard_count": 58,
    "applicable_standard_count": 12,
    "applied_standard_count": 12,
    "phase_eval_phase_count": 19,
    "phase_eval_passed_phase_count": 19,
    "promotion_suite_required_current_result_count": 22,
    "promotion_suite_passed_required_current_result_count": 22,
    "accepted_v1_risk_count": 14,
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
    for field, expected in EXPECTED_COUNTS.items():
        if field in count_fields:
            assert count_fields[field]["expected"] == expected

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
        "east-crazies-final-qa-certification-config-v1",
        "east-crazies-final-qa-expected-summary-v1",
        "accepted_v1_risk_ledger",
        "reviewer_signoff",
        "human_certification_overclaim",
        "accepted_v1_risk_hidden",
        "East_Crazies_*",
    ]:
        assert required_text in docs


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
