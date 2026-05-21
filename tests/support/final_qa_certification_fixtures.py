from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_sequence_2_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    output_dir = tmp_path / "source_library"
    review_id = "review-test"
    source_set_id = "source-set-test"
    review_dir = output_dir / "reviews" / review_id
    decision_dir = review_dir / "decision_support"
    review_packet_dir = review_dir / "review_packet_index"
    app_dir = review_dir / "applicability"
    suite_dir = output_dir / "reviews" / "promotion_suite" / "post-v1-region1-ea-promotion-suite"
    decision_dir.mkdir(parents=True)
    review_packet_dir.mkdir(parents=True)
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
        review_packet_dir / "review_packet_row_inventory.json",
        {
            "schema_version": "review-packet-row-inventory-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "applicable_authority_count": 2,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 2,
                "applicable_standard_count": 1,
                "row_set_sha256": "synthetic-row-set",
            },
            "applicable_authority_rows": [
                {"rule_id": "rule-a"},
                {"rule_id": "rule-b"},
            ],
            "non_applicable_authority_rows": [
                {"candidate_authority_id": "candidate:rule-b"}
            ],
            "forest_plan_component_rows": [
                {"component_id": "component-1"},
                {"component_id": "component-2"},
            ],
            "applicable_forest_plan_standard_rows": [
                {"component_id": "component-1", "component_key": "FW-STD-01"}
            ],
        },
    )
    _write_json_file(
        review_packet_dir / "compliance_matrix_render_manifest.json",
        {
            "schema_version": "compliance-matrix-render-manifest-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "passed": True,
                "row_count": 4,
                "authority_row_count": 2,
                "forest_plan_row_count": 2,
                "row_set_sha256": "synthetic-render-row-set",
            },
            "rows": [
                {"row_class": "applicable_authority", "row_identity": {"rule_id": "rule-a"}},
                {"row_class": "applicable_authority", "row_identity": {"rule_id": "rule-b"}},
                {"row_class": "forest_plan_component", "row_identity": {"component_id": "component-1"}},
                {"row_class": "forest_plan_component", "row_identity": {"component_id": "component-2"}},
            ],
        },
    )
    _write_json_file(
        review_packet_dir / "review_packet_index.json",
        {
            "schema_version": "review-packet-index-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "row_inventory_summary": {
                "applicable_authority_count": 2,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 2,
                "applicable_standard_count": 1,
            },
            "render_manifest_summary": {
                "passed": True,
                "authority_row_count": 2,
                "forest_plan_row_count": 2,
            },
            "applicable_authority_rows": [
                {"rule_id": "rule-a"},
                {"rule_id": "rule-b"},
            ],
            "non_applicable_authority_boundary": {
                "non_applicable_authority_count": 1,
                "rows": [{"candidate_authority_id": "candidate:rule-b"}],
            },
            "forest_plan_component_rows": [
                {"component_id": "component-1"},
                {"component_id": "component-2"},
            ],
            "applicable_forest_plan_standard_rows": [
                {"component_id": "component-1", "component_key": "FW-STD-01"}
            ],
        },
    )
    _write_json_file(
        review_packet_dir / "review_packet_index_validation.json",
        {
            "schema_version": "review-packet-index-validation-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "reviewer_ready": True,
            "summary": {
                "failed_check_count": 0,
                "applicable_authority_count": 2,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 2,
                "applicable_standard_count": 1,
                "row_set_sha256": "synthetic-row-set",
            },
        },
    )
    (review_packet_dir / "review_packet_index.pdf").write_bytes(b"%PDF-1.4\n")
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
        "section_order": [
            "review_boundary",
            "gate_replay_summary",
            "artifact_freshness_ledger",
            "applicability_partition",
            "finding_qa",
            "forest_plan_qa",
            "decision_support_qa",
            "review_packet_index_qa",
            "accepted_v1_risk_ledger",
            "certification_statement",
            "residual_blockers_and_stop_conditions",
        ],
        "required_output_files": [
            "east_crazies_final_qa_certification.json",
            "east_crazies_final_qa_certification.md",
            "east_crazies_final_qa_certification.pdf",
            "east_crazies_final_qa_certification_manifest.json",
            "east_crazies_final_qa_certification_validation.json",
        ],
        "required_gate_names": [
            "applicability_validation",
            "generated_rule_pack_validation",
            "compliance_validation",
            "compliance_matrix",
            "forest_plan_context",
            "forest_plan_component_eval",
            "decision_support_validation",
            "review_packet_index_validation",
            "phase_eval",
            "v1_ea_eval",
            "current_promotion_suite",
        ],
        "required_gates": [
            _gate("applicability_validation", f"{review_root}/applicability/applicability_validation.json", "passed", True),
            _gate("generated_rule_pack_validation", f"{review_root}/applicability/generated_rule_pack_validation.json", "generated_rule_pack_ready", True),
            _gate("compliance_validation", f"{review_root}/compliance_validation.json", "passed", True),
            _gate("compliance_matrix", f"{review_root}/compliance_matrix.json", "summary.validated", True),
            _gate("forest_plan_context", f"{review_root}/forest_plan_context_summary.json", "reviewer_ready", True),
            _gate("forest_plan_component_eval", f"{review_root}/forest_plan_component_eval_results.json", "passed", True),
            _gate("decision_support_validation", f"{review_root}/decision_support/ea_consistency_decision_support_manifest.json", "validation_status", "passed"),
            _gate("review_packet_index_validation", f"{review_root}/review_packet_index/review_packet_index_validation.json", "passed", True),
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
        "failure_categories": [
            "missing_required_artifact",
            "unparseable_required_artifact",
            "stale_artifact",
            "review_source_set_mismatch",
            "input_hash_mismatch",
            "count_drift",
            "missing_applicable_authority_row",
            "missing_required_gate_section",
            "missing_citation_or_source_selector",
            "missing_non_applicable_boundary_evidence",
            "unresolved_reviewer_item",
            "invalid_report_pdf_header",
            "manual_draft_dependency",
            "missing_matrix_render_row",
            "missing_packet_index_row",
            "missing_forest_plan_row",
            "missing_non_applicable_boundary",
            "non_canonical_draft_dependency",
            "accepted_v1_risk_hidden",
            "legal_conclusion_leak",
            "human_certification_overclaim",
        ],
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
        "required_sections": [
            "review_boundary",
            "gate_replay_summary",
            "artifact_freshness_ledger",
            "applicability_partition",
            "finding_qa",
            "forest_plan_qa",
            "decision_support_qa",
            "review_packet_index_qa",
            "accepted_v1_risk_ledger",
            "certification_statement",
            "residual_blockers_and_stop_conditions",
        ],
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
        "failure_categories": [
            "missing_required_artifact",
            "unparseable_required_artifact",
            "stale_artifact",
            "review_source_set_mismatch",
            "input_hash_mismatch",
            "count_drift",
            "missing_applicable_authority_row",
            "missing_required_gate_section",
            "missing_citation_or_source_selector",
            "missing_non_applicable_boundary_evidence",
            "unresolved_reviewer_item",
            "invalid_report_pdf_header",
            "manual_draft_dependency",
            "missing_matrix_render_row",
            "missing_packet_index_row",
            "missing_forest_plan_row",
            "missing_non_applicable_boundary",
            "non_canonical_draft_dependency",
            "accepted_v1_risk_hidden",
            "legal_conclusion_leak",
            "human_certification_overclaim",
        ],
        "manual_draft_policy": {"root_east_crazies_drafts_are_canonical": False},
    }
    hash_paths = {
        "decision_support_report_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support.json",
        "decision_support_markdown_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support.md",
        "decision_support_pdf_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support.pdf",
        "decision_support_manifest_sha256": output_dir / "reviews" / review_id / "decision_support" / "ea_consistency_decision_support_manifest.json",
        "review_packet_row_inventory_sha256": output_dir / "reviews" / review_id / "review_packet_index" / "review_packet_row_inventory.json",
        "compliance_matrix_render_manifest_sha256": output_dir / "reviews" / review_id / "review_packet_index" / "compliance_matrix_render_manifest.json",
        "review_packet_index_sha256": output_dir / "reviews" / review_id / "review_packet_index" / "review_packet_index.json",
        "review_packet_index_validation_sha256": output_dir / "reviews" / review_id / "review_packet_index" / "review_packet_index_validation.json",
        "review_packet_index_pdf_sha256": output_dir / "reviews" / review_id / "review_packet_index" / "review_packet_index.pdf",
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
        "review_packet_index_applicable_authority_count": 2,
        "review_packet_index_non_applicable_authority_count": 1,
        "review_packet_index_forest_plan_component_row_count": 2,
        "review_packet_index_applicable_standard_count": 1,
        "review_packet_index_render_manifest_authority_row_count": 2,
        "review_packet_index_render_manifest_forest_plan_row_count": 2,
        "review_packet_index_validation_failed_check_count": 0,
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
        "review_packet_index_applicable_authority_count": "review_packet_index_qa.applicable_authority_count",
        "review_packet_index_non_applicable_authority_count": "review_packet_index_qa.non_applicable_authority_count",
        "review_packet_index_forest_plan_component_row_count": "review_packet_index_qa.forest_plan_component_row_count",
        "review_packet_index_applicable_standard_count": "review_packet_index_qa.applicable_standard_count",
        "review_packet_index_render_manifest_authority_row_count": "review_packet_index_qa.render_manifest_authority_row_count",
        "review_packet_index_render_manifest_forest_plan_row_count": "review_packet_index_qa.render_manifest_forest_plan_row_count",
        "review_packet_index_validation_failed_check_count": "review_packet_index_qa.validation_failed_check_count",
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
