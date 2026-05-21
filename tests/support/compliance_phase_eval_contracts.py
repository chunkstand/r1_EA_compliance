from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

from usfs_r1_ea_sources.ea_consistency_decision_support import (
    run_ea_consistency_decision_support,
)


FINAL_QA_REQUIRED_SECTIONS = [
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
]

DECISION_SUPPORT_REQUIRED_SECTIONS = [
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

FINAL_QA_FAILURE_CATEGORIES = [
    "accepted_v1_risk_hidden",
    "count_drift",
    "human_certification_overclaim",
    "input_hash_mismatch",
    "invalid_report_pdf_header",
    "legal_conclusion_leak",
    "manual_draft_dependency",
    "missing_applicable_authority_row",
    "missing_citation_or_source_selector",
    "missing_forest_plan_row",
    "missing_matrix_render_row",
    "missing_non_applicable_boundary",
    "missing_non_applicable_boundary_evidence",
    "missing_packet_index_row",
    "missing_required_artifact",
    "missing_required_gate_section",
    "non_canonical_draft_dependency",
    "review_source_set_mismatch",
    "stale_artifact",
    "unparseable_required_artifact",
    "unresolved_reviewer_item",
]


def write_decision_support_artifacts(
    *,
    output_dir: Path,
    review_dir: Path,
    review_id: str,
    source_set_id: str,
) -> None:
    decision_dir = review_dir / "decision_support"
    decision_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir = review_dir / "package" / "extracted_text"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        review_dir / "forest_plan_component_findings.json",
        {
            "schema_version": "forest-plan-component-findings-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "finding_count": 0,
                "supported_count": 0,
                "not_applicable_count": 0,
                "gap_count": 0,
                "standard_count": 0,
                "applicable_standard_count": 0,
                "applied_standard_count": 0,
                "reviewer_ready": True,
                "validation_passed": True,
            },
            "findings": [],
        },
    )
    _write_json(
        review_dir / "forest_plan_reviewer_resolution_queue.json",
        {
            "schema_version": "forest-plan-reviewer-resolution-queue-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "items": [],
        },
    )
    _write_json(
        review_dir / "authority_reviewer_resolution_report.json",
        {
            "schema_version": "authority-reviewer-resolution-report-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {"pending_resolution_count": 0},
            "pending_resolution_items": [],
        },
    )
    _write_json(
        review_dir / "non_applicable_authority_appendix.json",
        {
            "schema_version": "appendix-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
        },
    )
    (review_dir / "non_applicable_authority_appendix.md").write_text(
        "appendix\n",
        encoding="utf-8",
    )
    (extracted_dir / "EA-PACKAGE-042_test.txt").write_text(
        "Plan Consistency Table\n",
        encoding="utf-8",
    )

    config_path = decision_dir / "decision_support_contract_config.json"
    expected_path = decision_dir / "decision_support_expected_summary.json"
    _write_json(config_path, _decision_support_config(review_id, source_set_id))
    _write_json(
        expected_path,
        _decision_support_expected(
            review_dir=review_dir,
            review_id=review_id,
            source_set_id=source_set_id,
        ),
    )

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id=review_id,
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=decision_dir,
    )
    if result.summary.get("passed") is not True:
        raise AssertionError(
            f"synthetic decision support fixture failed validation: {result.summary}"
        )


def build_final_qa_config(
    review_id: str,
    source_set_id: str,
    expected_counts: dict[str, int],
) -> dict:
    review_root = f"source_library/reviews/{review_id}"
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
        "section_order": FINAL_QA_REQUIRED_SECTIONS,
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
            _gate(
                "applicability_validation",
                f"{review_root}/applicability/applicability_validation.json",
                "passed",
                True,
            ),
            _gate(
                "generated_rule_pack_validation",
                f"{review_root}/applicability/generated_rule_pack_validation.json",
                "summary.generated_rule_pack_ready",
                True,
            ),
            _gate(
                "compliance_validation",
                f"{review_root}/compliance_validation.json",
                "passed",
                True,
            ),
            _gate(
                "compliance_matrix",
                f"{review_root}/compliance_matrix.json",
                "summary.validated",
                True,
            ),
            _gate(
                "forest_plan_context",
                f"{review_root}/forest_plan_context_summary.json",
                "reviewer_ready",
                True,
            ),
            _gate(
                "forest_plan_component_eval",
                f"{review_root}/forest_plan_component_eval_results.json",
                "passed",
                True,
            ),
            _gate(
                "decision_support_validation",
                f"{review_root}/decision_support/ea_consistency_decision_support_manifest.json",
                "validation_status",
                "passed",
            ),
            _gate(
                "review_packet_index_validation",
                f"{review_root}/review_packet_index/review_packet_index_validation.json",
                "passed",
                True,
            ),
            _gate(
                "phase_eval",
                f"{review_root}/phase_eval_results.json",
                "reviewer_ready",
                True,
            ),
            _gate(
                "v1_ea_eval",
                f"{review_root}/v1_ea_eval_results.json",
                "passed",
                True,
            ),
            _gate(
                "current_promotion_suite",
                "source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/"
                "promotion_suite_results.json",
                "current_promotion_ready",
                True,
            ),
        ],
        "required_count_fields": [
            {
                "field": field,
                "expected": expected,
                "source_selector": _count_selector(field),
                "failure_category": (
                    "accepted_v1_risk_hidden"
                    if field == "accepted_v1_risk_count"
                    else "legal_conclusion_leak"
                    if field == "litigation_risk_legal_conclusion_count"
                    else "missing_citation_or_source_selector"
                    if field == "rule_claim_gap_count"
                    else "unresolved_reviewer_item"
                    if field == "unresolved_authority_count"
                    else "count_drift"
                ),
            }
            for field, expected in expected_counts.items()
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
        "failure_categories": FINAL_QA_FAILURE_CATEGORIES,
    }


def build_final_qa_expected(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    expected_counts: dict[str, int],
) -> dict:
    review_root = output_dir / "reviews" / review_id
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
        "required_sections": FINAL_QA_REQUIRED_SECTIONS,
        "expected_counts": expected_counts,
        "input_hashes": {},
        "required_fixture_rows": {
            "applicable_authority": {
                "rule_id": "purpose_need",
                "status": "pass",
                "applicability_status": "applicable",
                "ea_package_citation": "EA-PACKAGE-001 (test)",
                "source_library_citation": "R1EA-001 (test)",
                "source_claim_ids": ["claim:test"],
                "source_selectors": [
                    {
                        "artifact_path": f"source_library/reviews/{review_id}/compliance_matrix.json",
                        "selector": "rows[rule_id=purpose_need]",
                    }
                ],
            },
            "non_applicable_authority": {
                "candidate_authority_id": "candidate:synthetic-boundary",
                "status": "not_applicable",
                "coverage_certificate": {
                    "coverage_result": "sufficient",
                    "missing_query_variants": [],
                },
                "source_selectors": [
                    {
                        "artifact_path": (
                            f"source_library/reviews/{review_id}/applicability/"
                            "non_applicable_authorities.json"
                        ),
                        "selector": "authorities",
                    }
                ],
            },
            "forest_plan_standard": {
                "component_id": "component:none",
                "component_key": "FW-STD-NONE",
                "component_type": "standard",
                "applicability_status": "not_applicable",
                "compliance_status": "not_applicable",
                "finding_status": "not_applicable",
                "ea_package_citation": "EA-PACKAGE-001 (test)",
                "forest_plan_citation": "R1PLAN-TEST (test)",
                "source_selectors": [
                    {
                        "artifact_path": (
                            f"source_library/reviews/{review_id}/"
                            "forest_plan_applicable_standard_coverage.json"
                        ),
                        "selector": "standards",
                    }
                ],
            },
            "decision_support_residual_risk": {
                "risk_id": "risk:test",
                "category": "synthetic",
                "deterministic_basis": True,
                "legal_conclusion": False,
                "source_artifact_path": (
                    f"source_library/reviews/{review_id}/litigation_risk_summary.json"
                ),
                "source_selector": "summary",
            },
        },
        "accepted_v1_risk_ledger": {
            "policy_mode": "accepted_pending_v1",
            "accepted_pending_count": 1,
            "actual_pending_count": 1,
            "actual_pending_applicable_count": 1,
            "source_artifact_path": f"source_library/reviews/{review_id}/v1_ea_eval_results.json",
            "source_selector": "conditional_adjudication",
            "accepted_pending_rule_ids": ["purpose_need"],
            "representative_pending_rows": [],
        },
        "failure_categories": FINAL_QA_FAILURE_CATEGORIES,
        "manual_draft_policy": {"root_east_crazies_drafts_are_canonical": False},
    }
    hash_paths = {
        "decision_support_report_sha256": (
            review_root / "decision_support" / "ea_consistency_decision_support.json"
        ),
        "decision_support_markdown_sha256": (
            review_root / "decision_support" / "ea_consistency_decision_support.md"
        ),
        "decision_support_pdf_sha256": (
            review_root / "decision_support" / "ea_consistency_decision_support.pdf"
        ),
        "decision_support_manifest_sha256": (
            review_root / "decision_support" / "ea_consistency_decision_support_manifest.json"
        ),
        "review_packet_row_inventory_sha256": (
            review_root / "review_packet_index" / "review_packet_row_inventory.json"
        ),
        "compliance_matrix_render_manifest_sha256": (
            review_root / "review_packet_index" / "compliance_matrix_render_manifest.json"
        ),
        "review_packet_index_sha256": (
            review_root / "review_packet_index" / "review_packet_index.json"
        ),
        "review_packet_index_validation_sha256": (
            review_root / "review_packet_index" / "review_packet_index_validation.json"
        ),
        "review_packet_index_pdf_sha256": (
            review_root / "review_packet_index" / "review_packet_index.pdf"
        ),
        "v1_ea_eval_results_sha256": review_root / "v1_ea_eval_results.json",
        "phase_eval_results_sha256": review_root / "phase_eval_results.json",
        "promotion_suite_results_sha256": (
            output_dir
            / "reviews"
            / "promotion_suite"
            / "post-v1-region1-ea-promotion-suite"
            / "promotion_suite_results.json"
        ),
        "compliance_validation_sha256": review_root / "compliance_validation.json",
        "applicability_validation_sha256": (
            review_root / "applicability" / "applicability_validation.json"
        ),
        "generated_rule_pack_validation_sha256": (
            review_root / "applicability" / "generated_rule_pack_validation.json"
        ),
        "compliance_matrix_sha256": review_root / "compliance_matrix.json",
        "compliance_matrix_pdf_sha256": review_root / "compliance_matrix.pdf",
        "compliance_review_sha256": review_root / "compliance_review.json",
        "forest_plan_context_summary_sha256": review_root / "forest_plan_context_summary.json",
        "forest_plan_component_eval_results_sha256": (
            review_root / "forest_plan_component_eval_results.json"
        ),
    }
    expected["input_hashes"] = {key: _sha256_file(path) for key, path in hash_paths.items()}
    return expected


def _decision_support_config(review_id: str, source_set_id: str) -> dict:
    return {
        "schema_version": "ea-consistency-decision-support-config-v1",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "report_schema_version": "ea-consistency-decision-support-report-v1",
        "decision_use_caveat": "Decision support only.",
        "manual_draft_policy": {
            "root_east_crazies_drafts_are_canonical": False,
            "blocked_path_prefixes": ["East_Crazies_"],
        },
        "section_order": DECISION_SUPPORT_REQUIRED_SECTIONS,
        "authority_group_order": ["regulation"],
        "residual_risk_group_order": ["reviewer_resolution"],
        "implementation_confirmations": [
            {
                "confirmation_id": "synthetic_confirmation",
                "display_order": 10,
                "label": "Synthetic confirmation",
                "group": "closing",
                "evidence_status": "evidence_linked_confirmation_required",
                "source_selectors": [
                    {
                        "artifact_path": (
                            f"source_library/reviews/{review_id}/package/package_chunks.jsonl"
                        ),
                        "selector_type": "package_chunk",
                        "selector": (
                            "source_record_id=EA-PACKAGE-001;"
                            "chunk_id=chunk:2c985edd64d4d72a094b5a8752ae6c44"
                        ),
                        "required": True,
                    },
                    {
                        "artifact_path": f"source_library/reviews/{review_id}/compliance_matrix.json",
                        "selector_type": "authority_finding",
                        "selector": "rule_id=purpose_need",
                        "required": True,
                    },
                ],
                "allowed_report_wording": "Keep this as an implementation confirmation.",
            }
        ],
        "residual_risk_rules": [],
        "report_eval_expectations": [],
    }


def _decision_support_expected(
    *,
    review_dir: Path,
    review_id: str,
    source_set_id: str,
) -> dict:
    applicability = _read_json(review_dir / "applicability" / "applicability_validation.json")
    compliance_review = _read_json(review_dir / "compliance_review.json")
    review_packet = _read_json(
        review_dir / "review_packet_index" / "review_packet_index_validation.json"
    )
    coverage = _read_json(review_dir / "applicability" / "search_coverage_certificates.json")
    forest_findings = _read_json(review_dir / "forest_plan_component_findings.json")
    standards = _read_json(review_dir / "forest_plan_applicable_standard_coverage.json")
    litigation = _read_json(review_dir / "litigation_risk_summary.json")

    return {
        "schema_version": "ea-consistency-decision-support-expected-summary-v1",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "required_sections": DECISION_SUPPORT_REQUIRED_SECTIONS,
        "expected_counts": {
            "applicable_authority_count": applicability.get("applicable_authority_count", 0),
            "non_applicable_authority_count": applicability.get("non_applicable_authority_count", 0),
            "candidate_authority_count": applicability.get("candidate_authority_count", 0),
            "authority_finding_count": _selector(compliance_review, "summary.finding_count")
            or 0,
            "authority_finding_status_counts": (
                _selector(compliance_review, "summary.finding_status_counts") or {}
            ),
            "non_applicable_search_coverage_certificate_count": len(
                coverage.get("certificates") or []
            ),
            "forest_plan_component_finding_count": _selector(
                forest_findings,
                "summary.finding_count",
            )
            or 0,
            "forest_plan_supported_component_count": _selector(
                forest_findings,
                "summary.supported_count",
            )
            or 0,
            "forest_plan_not_applicable_component_count": _selector(
                forest_findings,
                "summary.not_applicable_count",
            )
            or 0,
            "forest_plan_gap_count": _selector(forest_findings, "summary.gap_count") or 0,
            "forest_plan_standard_count": _selector(
                forest_findings,
                "summary.standard_count",
            )
            or 0,
            "forest_plan_applicable_standard_count": standards.get(
                "applicable_standard_count",
                0,
            ),
            "forest_plan_applied_standard_count": standards.get("applied_standard_count", 0),
            "authority_reviewer_resolution_pending_count": 0,
            "forest_plan_reviewer_resolution_item_count": 0,
            "litigation_risk_flag_count": _selector(litigation, "summary.risk_flag_count")
            or 0,
            "litigation_risk_legal_conclusion_count": _selector(
                litigation,
                "summary.legal_conclusion_count",
            )
            or 0,
            "review_packet_index_applicable_authority_count": _selector(
                review_packet,
                "summary.applicable_authority_count",
            )
            or 0,
            "review_packet_index_non_applicable_authority_count": _selector(
                review_packet,
                "summary.non_applicable_authority_count",
            )
            or 0,
            "review_packet_index_forest_plan_component_row_count": _selector(
                review_packet,
                "summary.forest_plan_component_row_count",
            )
            or 0,
            "review_packet_index_applicable_standard_count": _selector(
                review_packet,
                "summary.applicable_standard_count",
            )
            or 0,
            "review_packet_index_render_manifest_authority_row_count": 1,
            "review_packet_index_render_manifest_forest_plan_row_count": 0,
            "review_packet_index_validation_failed_check_count": _selector(
                review_packet,
                "summary.failed_check_count",
            )
            or 0,
            "package_file_count": 1,
            "package_chunk_count": 1,
        },
        "input_hashes": {
            "package_manifest_sha256": _sha256_file(
                review_dir / "package" / "package_manifest.jsonl"
            ),
            "package_chunks_sha256": _sha256_file(
                review_dir / "package" / "package_chunks.jsonl"
            ),
            "compliance_matrix_sha256": _sha256_file(review_dir / "compliance_matrix.json"),
            "compliance_review_sha256": _sha256_file(review_dir / "compliance_review.json"),
            "applicability_validation_sha256": _sha256_file(
                review_dir / "applicability" / "applicability_validation.json"
            ),
            "applicable_authorities_sha256": _sha256_file(
                review_dir / "applicability" / "applicable_authorities.json"
            ),
            "non_applicable_authorities_sha256": _sha256_file(
                review_dir / "applicability" / "non_applicable_authorities.json"
            ),
            "search_coverage_certificates_sha256": _sha256_file(
                review_dir / "applicability" / "search_coverage_certificates.json"
            ),
            "generated_rule_pack_sha256": _sha256_file(
                review_dir / "applicability" / "generated_rule_pack.json"
            ),
            "generated_rule_pack_validation_sha256": _sha256_file(
                review_dir / "applicability" / "generated_rule_pack_validation.json"
            ),
            "forest_plan_component_findings_sha256": _sha256_file(
                review_dir / "forest_plan_component_findings.json"
            ),
            "forest_plan_applicable_standard_coverage_sha256": _sha256_file(
                review_dir / "forest_plan_applicable_standard_coverage.json"
            ),
            "forest_plan_context_summary_sha256": _sha256_file(
                review_dir / "forest_plan_context_summary.json"
            ),
            "non_applicable_authority_appendix_sha256": _sha256_file(
                review_dir / "non_applicable_authority_appendix.json"
            ),
            "non_applicable_authority_appendix_markdown_sha256": _sha256_file(
                review_dir / "non_applicable_authority_appendix.md"
            ),
            "authority_reviewer_resolution_report_sha256": _sha256_file(
                review_dir / "authority_reviewer_resolution_report.json"
            ),
            "litigation_risk_summary_sha256": _sha256_file(
                review_dir / "litigation_risk_summary.json"
            ),
            "plan_consistency_table_text_sha256": _sha256_file(
                review_dir / "package" / "extracted_text" / "EA-PACKAGE-042_test.txt"
            ),
        },
    }


def _count_selector(field: str) -> str:
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
        "promotion_suite_required_current_result_count": (
            "gate_replay_summary.current_promotion_suite.required_current_result_count"
        ),
        "promotion_suite_passed_required_current_result_count": (
            "gate_replay_summary.current_promotion_suite.passed_required_current_result_count"
        ),
        "review_packet_index_applicable_authority_count": (
            "review_packet_index_qa.applicable_authority_count"
        ),
        "review_packet_index_non_applicable_authority_count": (
            "review_packet_index_qa.non_applicable_authority_count"
        ),
        "review_packet_index_forest_plan_component_row_count": (
            "review_packet_index_qa.forest_plan_component_row_count"
        ),
        "review_packet_index_applicable_standard_count": (
            "review_packet_index_qa.applicable_standard_count"
        ),
        "review_packet_index_render_manifest_authority_row_count": (
            "review_packet_index_qa.render_manifest_authority_row_count"
        ),
        "review_packet_index_render_manifest_forest_plan_row_count": (
            "review_packet_index_qa.render_manifest_forest_plan_row_count"
        ),
        "review_packet_index_validation_failed_check_count": (
            "review_packet_index_qa.validation_failed_check_count"
        ),
        "accepted_v1_risk_count": "accepted_v1_risk_ledger.accepted_pending_count",
        "actual_pending_applicable_count": (
            "accepted_v1_risk_ledger.actual_pending_applicable_count"
        ),
        "litigation_risk_legal_conclusion_count": (
            "decision_support_qa.litigation_risk_legal_conclusion_count"
        ),
    }[field]


def _gate(name: str, path: str, selector: str, expected: object) -> dict:
    return {
        "gate_name": name,
        "artifact_path": path,
        "required_pass_selector": selector,
        "expected_value": expected,
        "failure_category": "stale_artifact",
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _selector(payload: dict, selector: str):
    current = payload
    for part in selector.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
