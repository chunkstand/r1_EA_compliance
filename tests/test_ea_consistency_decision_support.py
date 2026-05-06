from __future__ import annotations

from pathlib import Path
import hashlib
import json

from usfs_r1_ea_sources.ea_consistency_decision_support import (
    run_ea_consistency_decision_support,
)


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


def test_sequence_2_generator_writes_canonical_report_family(tmp_path: Path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is True
    assert result.summary["output_written"] is True
    assert result.report_path.exists()
    assert result.markdown_path.exists()
    assert result.pdf_path.read_bytes().startswith(b"%PDF-")
    assert result.manifest_path.exists()

    report = _read_json(result.report_path)
    assert report["schema_version"] == "ea-consistency-decision-support-report-v1"
    assert report["manifest"]["schema_version"] == "ea-consistency-decision-support-manifest-v1"
    assert report["executive_determination"]["legal_conclusion"] is False
    assert report["applicable_authority_summary"]["applicable_authority_count"] == 1
    assert len(report["authority_findings"]) == 1
    assert len(report["non_applicable_authority_boundary"]["summary_rows"]) == 1
    assert len(report["forest_plan_consistency"]["component_rows"]) == 1
    assert len(report["applicable_forest_plan_standards"]) == 1
    assert report["implementation_confirmation_checklist"][0]["status"] == (
        "requires_confirmation"
    )
    assert report["residual_risk_register"][0]["legal_conclusion"] is False

    authority = report["authority_findings"][0]
    _assert_evidence(authority["ea_package_evidence"][0])
    _assert_evidence(authority["source_library_evidence"][0])
    _assert_traceable_row(authority)

    non_applicable = report["non_applicable_authority_boundary"]["summary_rows"][0]
    assert non_applicable["status"] == "not_applicable"
    assert non_applicable["search_coverage"][0]["coverage_result"] == "sufficient"
    _assert_traceable_row(non_applicable)


def test_sequence_2_generator_fails_closed_on_missing_required_artifact(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    (
        output_dir
        / "reviews"
        / "review-test"
        / "applicability"
        / "non_applicable_authorities.json"
    ).unlink()

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is False
    assert "missing_required_artifact" in result.summary["failure_categories"]
    assert result.summary["output_written"] is False
    assert not result.report_path.exists()


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


def _write_sequence_2_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    output_dir = tmp_path / "source_library"
    review_dir = output_dir / "reviews" / "review-test"
    app_dir = review_dir / "applicability"
    package_dir = review_dir / "package"
    extracted_dir = package_dir / "extracted_text"
    app_dir.mkdir(parents=True)
    extracted_dir.mkdir(parents=True)

    package_evidence = {
        "artifact_path": "package.pdf",
        "artifact_sha256": "sha256-package-artifact",
        "chunk_id": "chunk:package",
        "citation_label": "EA-PACKAGE-001 (test)",
        "content_sha256": "sha256-package-content",
        "source_char_start": 0,
        "source_char_end": 24,
        "source_record_id": "EA-PACKAGE-001",
        "text": "synthetic package excerpt",
        "title": "Package",
    }
    source_evidence = {
        "artifact_path": "source.html",
        "artifact_sha256": "sha256-source-artifact",
        "chunk_id": "chunk:source",
        "citation_label": "R1EA-TEST (test)",
        "content_sha256": "sha256-source-content",
        "source_char_start": 0,
        "source_char_end": 23,
        "source_record_id": "R1EA-TEST",
        "text": "synthetic source excerpt",
        "title": "Source",
    }
    forest_package_evidence = {
        "chunk_id": "chunk:plan-package",
        "citation_label": "EA-PACKAGE-042 (test)",
        "component_key": "FW-STD-01",
        "evidence_span": {"source_char_start": 0, "source_char_end": 28, "text": "plan table"},
        "provenance": {
            "artifact_sha256": "sha256-plan-package-artifact",
            "content_sha256": "sha256-plan-package-content",
        },
        "source_record_id": "EA-PACKAGE-042",
    }
    forest_plan_evidence = {
        "chunk_id": "chunk:forest-plan",
        "citation_label": "R1PLAN-TEST (test)",
        "evidence_span": {"source_char_start": 0, "source_char_end": 29, "text": "plan source"},
        "provenance": {
            "artifact_sha256": "sha256-forest-plan-artifact",
            "content_sha256": "sha256-forest-plan-content",
        },
        "source_record_id": "R1PLAN-TEST",
    }

    _write_json_file(
        review_dir / "compliance_matrix.json",
        {
            "schema_version": "compliance-matrix-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {"reviewer_ready": True, "validated": True},
            "rule_pack": {"rule_pack_id": "test", "version": "1"},
            "rows": [
                {
                    "rule_id": "sample_authority",
                    "rule_title": "Sample applicable authority",
                    "authority_category": "executive_order",
                    "authority_source_record_id": "R1EA-TEST",
                    "authority_family_ids": ["sample_family"],
                    "candidate_authority_id": "candidate:sample",
                    "applicability_decision_id": "decision-applicable",
                    "applicability_status": "applicable",
                    "applicability_mode": "conditional",
                    "status": "pass",
                    "requirement": "Sample requirement",
                    "rationale": "Sample rationale",
                    "source_claim_ids": ["claim:test"],
                    "limitations": [],
                    "ea_package_evidence": package_evidence,
                    "source_library_evidence": source_evidence,
                }
            ],
        },
    )
    _write_json_file(
        review_dir / "compliance_review.json",
        {
            "schema_version": "compliance-review-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {"reviewer_ready": True},
            "findings": [],
        },
    )
    (review_dir / "compliance_matrix.pdf").write_bytes(b"%PDF-1.4\n")
    _write_json_file(
        app_dir / "applicability_validation.json",
        {
            "schema_version": "applicability-validation-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "passed": True,
            "reviewer_ready": True,
            "generated_rule_pack_ready": True,
        },
    )
    _write_json_file(
        app_dir / "applicable_authorities.json",
        {
            "schema_version": "applicable-authorities-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "authorities": [{"candidate_authority_id": "candidate:sample"}],
        },
    )
    _write_json_file(
        app_dir / "non_applicable_authorities.json",
        {
            "schema_version": "non-applicable-authorities-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "authorities": [
                {
                    "candidate_authority_id": "candidate:non-applicable",
                    "decision_id": "decision-non-applicable",
                    "authority_category": "regulation",
                    "basis_type": "absent_trigger_evidence",
                    "status": "not_applicable",
                    "source_record_ids": ["R1EA-NON"],
                    "search_coverage_certificate_ids": ["coverage:test"],
                    "applicability_basis": {"rationale": "No trigger evidence found."},
                    "rule_template": {"authority_family_id": "non_applicable_family"},
                }
            ],
        },
    )
    _write_json_file(
        app_dir / "search_coverage_certificates.json",
        {
            "schema_version": "search-coverage-certificates-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "certificates": [
                {
                    "coverage_certificate_id": "coverage:test",
                    "coverage_class": "absent_trigger_evidence",
                    "coverage_result": "sufficient",
                    "missing_query_variants": [],
                }
            ],
        },
    )
    _write_json_file(
        app_dir / "generated_rule_pack.json",
        {"schema_version": "rule-pack-v0", "review_id": "review-test", "source_set_id": "source-set-test"},
    )
    _write_json_file(
        app_dir / "generated_rule_pack_validation.json",
        {
            "schema_version": "generated-rule-pack-validation-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "passed": True,
        },
    )
    _write_json_file(
        review_dir / "forest_plan_component_findings.json",
        {
            "schema_version": "forest-plan-component-findings-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {
                "finding_count": 1,
                "supported_count": 1,
                "not_applicable_count": 0,
                "gap_count": 0,
                "standard_count": 1,
                "applicable_standard_count": 1,
                "applied_standard_count": 1,
                "reviewer_ready": True,
                "validation_passed": True,
            },
            "findings": [
                {
                    "component_id": "R1PLAN-TEST-FW-STD-01",
                    "component_type": "standard",
                    "applicability_status": "applicable",
                    "compliance_status": "complies",
                    "finding_status": "supported",
                    "rationale": "Supported.",
                    "applicability_basis": {"component_key": "FW-STD-01"},
                    "package_evidence": [forest_package_evidence],
                    "plan_source_evidence": [forest_plan_evidence],
                }
            ],
        },
    )
    _write_json_file(
        review_dir / "forest_plan_applicable_standard_coverage.json",
        {
            "schema_version": "forest-plan-applicable-standard-coverage-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "passed": True,
            "all_applicable_standards_applied": True,
            "standard_count": 1,
            "applicable_standard_count": 1,
            "applied_standard_count": 1,
            "standards": [
                {
                    "component_id": "R1PLAN-TEST-FW-STD-01",
                    "component_key": "FW-STD-01",
                    "applicability_status": "applicable",
                    "compliance_status": "complies",
                    "finding_status": "supported",
                    "standard_applied": True,
                }
            ],
        },
    )
    _write_json_file(
        review_dir / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "reviewer_ready": True,
            "validation_passed": True,
        },
    )
    _write_json_file(
        review_dir / "non_applicable_authority_appendix.json",
        {"schema_version": "appendix-v0", "review_id": "review-test", "source_set_id": "source-set-test"},
    )
    (review_dir / "non_applicable_authority_appendix.md").write_text("appendix\n")
    _write_json_file(
        review_dir / "authority_reviewer_resolution_report.json",
        {
            "schema_version": "authority-reviewer-resolution-report-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {"pending_resolution_count": 0},
            "pending_resolution_items": [],
        },
    )
    _write_json_file(
        review_dir / "litigation_risk_summary.json",
        {
            "schema_version": "litigation-risk-summary-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {
                "risk_flag_count": 1,
                "legal_conclusion_count": 0,
                "deterministic_only": True,
            },
            "risk_flags": [{"legal_conclusion": False}],
        },
    )
    _write_json_file(
        review_dir / "forest_plan_reviewer_resolution_queue.json",
        {
            "schema_version": "forest-plan-reviewer-resolution-queue-v0",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "items": [],
        },
    )
    _write_jsonl_file(
        package_dir / "package_manifest.jsonl",
        [
            {
                "source_record_id": "EA-PACKAGE-001",
                "citation_label": "EA-PACKAGE-001 (test)",
            }
        ],
    )
    _write_jsonl_file(package_dir / "package_chunks.jsonl", [package_evidence])
    (extracted_dir / "EA-PACKAGE-042_test.txt").write_text("Plan Consistency Table\n")

    config_path = tmp_path / "decision_support_config.json"
    _write_json_file(
        config_path,
        {
            "schema_version": "ea-consistency-decision-support-config-v1",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "report_schema_version": "ea-consistency-decision-support-report-v1",
            "decision_use_caveat": "Decision support only.",
            "manual_draft_policy": {
                "root_east_crazies_drafts_are_canonical": False,
                "blocked_path_prefixes": ["East_Crazies_"],
            },
            "section_order": REQUIRED_SECTIONS,
            "authority_group_order": ["executive_order", "regulation"],
            "residual_risk_group_order": ["reviewer_resolution"],
            "implementation_confirmations": [
                {
                    "confirmation_id": "sample_confirmation",
                    "display_order": 10,
                    "label": "Sample confirmation",
                    "group": "closing",
                    "evidence_status": "evidence_linked_confirmation_required",
                    "source_selectors": [
                        {
                            "artifact_path": "source_library/reviews/review-test/package/package_chunks.jsonl",
                            "selector_type": "package_chunk",
                            "selector": "source_record_id=EA-PACKAGE-001;chunk_id=chunk:package",
                            "required": True,
                        },
                        {
                            "artifact_path": "source_library/reviews/review-test/compliance_matrix.json",
                            "selector_type": "authority_finding",
                            "selector": "rule_id=sample_authority",
                            "required": True,
                        },
                    ],
                    "allowed_report_wording": "Keep this as an implementation confirmation.",
                }
            ],
            "residual_risk_rules": [
                {
                    "risk_source_id": "non_applicable_authority_boundary",
                    "legal_conclusion": False,
                }
            ],
            "report_eval_expectations": [],
        },
    )

    expected_path = tmp_path / "expected_summary.json"
    _write_json_file(
        expected_path,
        {
            "schema_version": "ea-consistency-decision-support-expected-summary-v1",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "required_sections": REQUIRED_SECTIONS,
            "expected_counts": {
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "candidate_authority_count": 2,
                "authority_finding_count": 1,
                "authority_finding_status_counts": {"pass": 1},
                "non_applicable_search_coverage_certificate_count": 1,
                "forest_plan_component_finding_count": 1,
                "forest_plan_supported_component_count": 1,
                "forest_plan_not_applicable_component_count": 0,
                "forest_plan_gap_count": 0,
                "forest_plan_standard_count": 1,
                "forest_plan_applicable_standard_count": 1,
                "forest_plan_applied_standard_count": 1,
                "authority_reviewer_resolution_pending_count": 0,
                "forest_plan_reviewer_resolution_item_count": 0,
                "litigation_risk_flag_count": 1,
                "litigation_risk_legal_conclusion_count": 0,
                "package_file_count": 1,
                "package_chunk_count": 1,
            },
            "input_hashes": {
                "package_manifest_sha256": _sha256(package_dir / "package_manifest.jsonl"),
                "package_chunks_sha256": _sha256(package_dir / "package_chunks.jsonl"),
                "compliance_matrix_sha256": _sha256(review_dir / "compliance_matrix.json"),
                "compliance_review_sha256": _sha256(review_dir / "compliance_review.json"),
                "applicability_validation_sha256": _sha256(
                    app_dir / "applicability_validation.json"
                ),
                "applicable_authorities_sha256": _sha256(
                    app_dir / "applicable_authorities.json"
                ),
                "non_applicable_authorities_sha256": _sha256(
                    app_dir / "non_applicable_authorities.json"
                ),
                "search_coverage_certificates_sha256": _sha256(
                    app_dir / "search_coverage_certificates.json"
                ),
                "generated_rule_pack_sha256": _sha256(app_dir / "generated_rule_pack.json"),
                "generated_rule_pack_validation_sha256": _sha256(
                    app_dir / "generated_rule_pack_validation.json"
                ),
                "forest_plan_component_findings_sha256": _sha256(
                    review_dir / "forest_plan_component_findings.json"
                ),
                "forest_plan_applicable_standard_coverage_sha256": _sha256(
                    review_dir / "forest_plan_applicable_standard_coverage.json"
                ),
                "forest_plan_context_summary_sha256": _sha256(
                    review_dir / "forest_plan_context_summary.json"
                ),
                "non_applicable_authority_appendix_sha256": _sha256(
                    review_dir / "non_applicable_authority_appendix.json"
                ),
                "non_applicable_authority_appendix_markdown_sha256": _sha256(
                    review_dir / "non_applicable_authority_appendix.md"
                ),
                "authority_reviewer_resolution_report_sha256": _sha256(
                    review_dir / "authority_reviewer_resolution_report.json"
                ),
                "litigation_risk_summary_sha256": _sha256(
                    review_dir / "litigation_risk_summary.json"
                ),
                "plan_consistency_table_text_sha256": _sha256(
                    extracted_dir / "EA-PACKAGE-042_test.txt"
                ),
            },
        },
    )
    return output_dir, config_path, expected_path


def _write_json_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_file(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
