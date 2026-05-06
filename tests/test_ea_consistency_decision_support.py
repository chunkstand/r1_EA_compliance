from __future__ import annotations

from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "ea_consistency_decision_support_v1.json"
EXPECTED_SUMMARY_PATH = (
    REPO_ROOT
    / "config"
    / "fixtures"
    / "decision_support"
    / "v1_ecid_decision_support_expected_summary.json"
)
MINIMAL_REPORT_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "decision_support" / "minimal_decision_support_report.json"
)
OUTPUT_SCHEMAS_PATH = REPO_ROOT / "docs" / "OUTPUT_SCHEMAS.md"

REQUIRED_SECTIONS = [
    "executive_determination",
    "record_and_artifact_inventory",
    "applicable_authority_summary",
    "authority_findings",
    "forest_plan_consistency",
    "applicable_forest_plan_standards",
    "non_applicable_authority_boundary",
    "implementation_confirmation_checklist",
    "residual_risk_register",
    "validation_and_replay",
]

EXPECTED_COUNTS = {
    "applicable_authority_count": 33,
    "non_applicable_authority_count": 340,
    "candidate_authority_count": 373,
    "authority_finding_count": 33,
    "non_applicable_search_coverage_certificate_count": 340,
    "forest_plan_component_finding_count": 329,
    "forest_plan_supported_component_count": 79,
    "forest_plan_not_applicable_component_count": 250,
    "forest_plan_gap_count": 0,
    "forest_plan_standard_count": 58,
    "forest_plan_applicable_standard_count": 12,
    "forest_plan_applied_standard_count": 12,
    "authority_reviewer_resolution_pending_count": 0,
    "forest_plan_reviewer_resolution_item_count": 0,
    "litigation_risk_flag_count": 340,
    "litigation_risk_legal_conclusion_count": 0,
    "package_file_count": 43,
    "package_chunk_count": 1265,
}

EXPECTED_FAILURE_CATEGORIES = {
    "missing_required_artifact",
    "unparseable_required_artifact",
    "review_source_set_mismatch",
    "input_hash_mismatch",
    "count_drift",
    "missing_applicable_authority_row",
    "duplicate_applicable_authority_row",
    "applicable_authority_missing_dual_evidence",
    "non_applicable_summary_missing",
    "non_applicable_missing_search_coverage",
    "non_applicable_promoted_to_finding",
    "forest_plan_component_summary_missing",
    "applicable_standard_missing",
    "applicable_standard_missing_evidence",
    "reviewer_resolution_open",
    "implementation_confirmation_selector_unresolved",
    "residual_risk_legal_conclusion",
    "manual_draft_dependency",
    "missing_report_pdf",
    "invalid_report_pdf_header",
    "false_positive_synthesis_claim",
    "false_negative_synthesis_omission",
}

EXPECTED_CONFIRMATION_IDS = {
    "closing_instruments",
    "deed_restrictions",
    "easements",
    "appraisal_equalization_title",
    "nhpa_moa_mitigation",
    "wetland_protections",
    "esa_botany_whitebark_trail_controls",
    "access_terms",
    "construction_phase_commitments",
}

EXPECTED_STANDARD_KEYS = {
    "FW-STD-RMZ-01",
    "FW-STD-PRISK-01",
    "FW-STD-WL-01",
    "FW-STD-WLBAT-01",
    "FW-STD-WLGB-01",
    "FW-STD-TRIBAL-01",
    "FW-STD-ROS-01",
    "FW-STD-IRA-01",
    "FW-STD-RWA-01",
    "FW-STD-BCA-01",
    "AB-STD-RCREA-01",
    "BC-STD-CMBCA-01",
}


def test_sequence_1_config_owns_sections_confirmations_and_eval_expectations() -> None:
    config = _read_json(CONFIG_PATH)

    assert config["schema_version"] == "ea-consistency-decision-support-config-v1"
    assert config["review_id"] == "v1-cg-ecid-compliance-review"
    assert config["source_set_id"] == "source-set-ba8d0feae79501b8"
    assert config["section_order"] == REQUIRED_SECTIONS
    assert config["manual_draft_policy"]["root_east_crazies_drafts_are_canonical"] is False

    confirmations = {
        row["confirmation_id"]: row for row in config["implementation_confirmations"]
    }
    assert set(confirmations) == EXPECTED_CONFIRMATION_IDS
    assert [row["display_order"] for row in config["implementation_confirmations"]] == sorted(
        row["display_order"] for row in config["implementation_confirmations"]
    )

    for confirmation in confirmations.values():
        assert confirmation["label"]
        assert confirmation["evidence_status"] == "evidence_linked_confirmation_required"
        assert confirmation["allowed_report_wording"]
        assert confirmation["source_selectors"]
        for selector in confirmation["source_selectors"]:
            assert selector["artifact_path"].startswith("source_library/reviews/")
            assert "East_Crazies_" not in selector["artifact_path"]
            assert selector["selector"]
            assert selector["required"] is True

    eval_failure_categories = {
        expectation["failure_category"] for expectation in config["report_eval_expectations"]
    }
    assert {"false_positive_synthesis_claim", "false_negative_synthesis_omission"} <= (
        eval_failure_categories
    )


def test_expected_summary_locks_pass_8_counts_hashes_samples_and_failures() -> None:
    expected = _read_json(EXPECTED_SUMMARY_PATH)

    assert expected["schema_version"] == "ea-consistency-decision-support-expected-summary-v1"
    assert expected["required_sections"] == REQUIRED_SECTIONS
    for key, value in EXPECTED_COUNTS.items():
        assert expected["expected_counts"][key] == value
    assert expected["expected_counts"]["authority_finding_status_counts"]["pass"] == 33

    assert len(expected["input_hashes"]) >= 18
    assert set(expected["input_hashes"]) >= {
        "package_manifest_sha256",
        "package_chunks_sha256",
        "compliance_matrix_sha256",
        "applicability_validation_sha256",
        "generated_rule_pack_validation_sha256",
        "forest_plan_component_findings_sha256",
        "forest_plan_applicable_standard_coverage_sha256",
        "non_applicable_authority_appendix_sha256",
        "litigation_risk_summary_sha256",
        "plan_consistency_table_text_sha256",
    }

    applicable = expected["required_fixture_rows"]["applicable_authority"]
    assert applicable["rule_id"] == "eo_11990_wetlands"
    assert applicable["applicability_status"] == "applicable"
    assert applicable["status"] == "pass"
    assert applicable["limitations"] == []

    non_applicable = expected["required_fixture_rows"]["non_applicable_authority"]
    assert non_applicable["status"] == "not_applicable"
    assert non_applicable["coverage_certificate"]["coverage_result"] == "sufficient"
    assert non_applicable["coverage_certificate"]["missing_query_variants"] == []

    forest_plan = expected["required_fixture_rows"]["forest_plan_component"]
    assert forest_plan["component_key"] == "FW-STD-RMZ-01"
    assert forest_plan["applicability_status"] == "applicable"
    assert forest_plan["compliance_status"] == "complies"

    standards = expected["applicable_standards"]
    assert {standard["component_key"] for standard in standards} == EXPECTED_STANDARD_KEYS
    assert len(standards) == 12
    assert all(standard["compliance_status"] == "complies" for standard in standards)
    assert all(standard["finding_status"] == "supported" for standard in standards)

    assert EXPECTED_FAILURE_CATEGORIES <= set(expected["failure_categories"])
    assert expected["manual_draft_policy"]["root_east_crazies_drafts_are_canonical"] is False
    assert {"trace_ids", "source_selectors"} <= set(
        expected["row_trace_contract"]["required_row_fields"]
    )


def test_minimal_report_fixture_has_required_sections_manifest_and_distinct_statuses() -> None:
    report = _read_json(MINIMAL_REPORT_PATH)

    assert report["schema_version"] == "ea-consistency-decision-support-report-v1"
    assert all(section in report for section in REQUIRED_SECTIONS)
    assert report["manifest"]["schema_version"] == "ea-consistency-decision-support-manifest-v1"
    assert report["manifest"]["validation_status"] == "passed"
    assert report["validation_and_replay"]["passed"] is True

    input_hashes = report["manifest"]["input_hashes"]
    assert {
        "package_manifest_sha256",
        "compliance_matrix_sha256",
        "applicability_validation_sha256",
        "forest_plan_component_findings_sha256",
        "decision_support_config_sha256",
    } <= set(input_hashes)

    authority = report["authority_findings"][0]
    confirmation = report["implementation_confirmation_checklist"][0]
    risk = report["residual_risk_register"][0]

    assert authority["applicability_status"] == "applicable"
    assert authority["compliance_status"] == "pass"
    assert confirmation["status"] == "requires_confirmation"
    assert risk["category"] == "non_applicable_authority_boundary"
    assert risk["deterministic_basis"] is True
    assert risk["legal_conclusion"] is False
    assert report["executive_determination"]["legal_conclusion"] is False


def test_minimal_report_fixture_rows_have_required_trace_ids_and_evidence() -> None:
    report = _read_json(MINIMAL_REPORT_PATH)

    authority = report["authority_findings"][0]
    _assert_evidence(authority["ea_package_evidence"][0])
    _assert_evidence(authority["source_library_evidence"][0])
    _assert_traceable_row(authority)

    non_applicable = report["non_applicable_authority_boundary"]["summary_rows"][0]
    assert non_applicable["status"] == "not_applicable"
    assert non_applicable["search_coverage"][0]["coverage_result"] == "sufficient"
    _assert_traceable_row(non_applicable)

    component = report["forest_plan_consistency"]["component_rows"][0]
    _assert_evidence(component["package_evidence"][0])
    _assert_evidence(component["forest_plan_evidence"][0])
    _assert_traceable_row(component)

    standard = report["applicable_forest_plan_standards"][0]
    _assert_evidence(standard["package_evidence"][0])
    _assert_evidence(standard["forest_plan_evidence"][0])
    _assert_traceable_row(standard)

    confirmation = report["implementation_confirmation_checklist"][0]
    _assert_evidence(confirmation["evidence"][0])
    assert confirmation["source_selectors"]
    assert confirmation["trace_ids"]

    risk = report["residual_risk_register"][0]
    assert risk["source_artifact_path"].endswith("litigation_risk_summary.json")
    assert risk["source_selector"]
    assert risk["trace_ids"]


def test_output_schema_docs_record_decision_support_contract() -> None:
    docs = OUTPUT_SCHEMAS_PATH.read_text(encoding="utf-8")

    for required_text in [
        "EA Consistency Decision-Support Outputs",
        "ea-consistency-decision-support-report-v1",
        "ea-consistency-decision-support-config-v1",
        "ea-consistency-decision-support-expected-summary-v1",
        "trace_ids[]",
        "source_selectors[]",
        "false_positive_synthesis_claim",
        "false_negative_synthesis_omission",
        "East_Crazies_*",
    ]:
        assert required_text in docs


def _assert_traceable_row(row: dict) -> None:
    assert row["trace_ids"]
    for trace in row["trace_ids"]:
        assert trace["trace_id"]
        assert trace["trace_type"]
        assert trace["source_artifact_path"]
        assert trace["source_selector"]
    assert row["source_selectors"]
    for selector in row["source_selectors"]:
        assert selector["artifact_path"]
        assert selector["selector"]


def _assert_evidence(evidence: dict) -> None:
    assert evidence["chunk_id"]
    assert evidence["source_record_id"]
    assert evidence["citation_label"]
    assert evidence["artifact_sha256"]
    assert evidence["content_sha256"]
    text_span = evidence["text_span"]
    assert isinstance(text_span["char_start"], int)
    assert isinstance(text_span["char_end"], int)
    assert text_span["char_end"] >= text_span["char_start"]
    assert text_span["excerpt"]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
