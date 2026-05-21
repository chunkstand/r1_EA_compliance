from __future__ import annotations

from pathlib import Path
import hashlib
import json


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


def _phase(summary: dict, phase_name: str) -> dict:
    for phase in summary["phases"]:
        if phase["name"] == phase_name:
            return phase
    raise AssertionError(f"Missing phase {phase_name}")


def _failed_check(summary: dict, check_name: str) -> dict:
    for check in summary["failures"]:
        if check["name"] == check_name:
            return check
    raise AssertionError(f"Missing failed check {check_name}")


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
            "forest_plan_compliance": {
                "summary": {"row_count": 1, "applicable_standard_row_count": 1},
                "rows": [
                    {
                        "row_id": "forest-plan-matrix:review-test:R1PLAN-TEST-FW-STD-01",
                        "component_id": "R1PLAN-TEST-FW-STD-01",
                        "component_key": "FW-STD-01",
                        "component_type": "standard",
                        "applicability_status": "applicable",
                        "compliance_status": "complies",
                        "finding_status": "supported",
                        "standard_applied": True,
                    }
                ],
            },
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
    review_packet_dir = review_dir / "review_packet_index"
    _write_json_file(
        review_packet_dir / "review_packet_row_inventory.json",
        {
            "schema_version": "review-packet-row-inventory-v1",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 1,
                "applicable_standard_count": 1,
                "row_set_sha256": "packet-row-set-test",
            },
            "applicable_authority_rows": [
                {"rule_id": "sample_authority", "authority_source_record_id": "R1EA-TEST"}
            ],
            "non_applicable_authority_rows": [
                {"candidate_authority_id": "candidate:non-applicable"}
            ],
            "forest_plan_component_rows": [
                {"component_id": "R1PLAN-TEST-FW-STD-01", "component_key": "FW-STD-01"}
            ],
            "applicable_forest_plan_standard_rows": [
                {"component_id": "R1PLAN-TEST-FW-STD-01", "component_key": "FW-STD-01"}
            ],
        },
    )
    _write_json_file(
        review_packet_dir / "compliance_matrix_render_manifest.json",
        {
            "schema_version": "compliance-matrix-render-manifest-v1",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "summary": {
                "passed": True,
                "authority_row_count": 1,
                "forest_plan_row_count": 1,
                "row_count": 2,
            },
            "rows": [
                {
                    "row_class": "applicable_authority",
                    "row_identity": {"rule_id": "sample_authority"},
                },
                {
                    "row_class": "forest_plan_component",
                    "row_identity": {"component_id": "R1PLAN-TEST-FW-STD-01"},
                },
            ],
        },
    )
    _write_json_file(
        review_packet_dir / "review_packet_index.json",
        {
            "schema_version": "review-packet-index-v1",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "row_inventory_summary": {
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 1,
                "applicable_standard_count": 1,
            },
            "applicable_authority_rows": [{"rule_id": "sample_authority"}],
            "non_applicable_authority_boundary": {
                "non_applicable_authority_count": 1,
                "rows": [{"candidate_authority_id": "candidate:non-applicable"}],
            },
            "forest_plan_component_rows": [
                {"component_id": "R1PLAN-TEST-FW-STD-01", "component_key": "FW-STD-01"}
            ],
            "applicable_forest_plan_standard_rows": [
                {"component_id": "R1PLAN-TEST-FW-STD-01", "component_key": "FW-STD-01"}
            ],
        },
    )
    _write_json_file(
        review_packet_dir / "review_packet_index_validation.json",
        {
            "schema_version": "review-packet-index-validation-v1",
            "review_id": "review-test",
            "source_set_id": "source-set-test",
            "passed": True,
            "reviewer_ready": True,
            "summary": {
                "failed_check_count": 0,
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 1,
                "applicable_standard_count": 1,
            },
        },
    )
    (review_packet_dir / "review_packet_index.pdf").write_bytes(b"%PDF-1.4\n")

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
            "section_order": [
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
            ],
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
            "required_sections": [
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
            ],
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
                "review_packet_index_applicable_authority_count": 1,
                "review_packet_index_non_applicable_authority_count": 1,
                "review_packet_index_forest_plan_component_row_count": 1,
                "review_packet_index_applicable_standard_count": 1,
                "review_packet_index_render_manifest_authority_row_count": 1,
                "review_packet_index_render_manifest_forest_plan_row_count": 1,
                "review_packet_index_validation_failed_check_count": 0,
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
