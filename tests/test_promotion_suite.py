from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pytest

from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_PROMOTION_SUITE = REPO_ROOT / "config" / "promotion_suite_v1.json"


def test_committed_promotion_suite_tracks_full_canonical_corpus_separately() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}

    assert manifest["source_set_id"] == "source-set-ba8d0feae79501b8"
    assert manifest["full_canonical_source_set_id"] == "source-set-5e65d845ce77e1a0"

    active_catalog = suite_results["full_canonical_catalog_manifest"]
    assert active_catalog["required_for_current_promotion"] is False
    assert active_catalog["required_for_full_canonical_corpus"] is True
    active_catalog_checks = {check["name"]: check for check in active_catalog["checks"]}
    assert active_catalog_checks["full_canonical_source_set_matches"]["equals"] == (
        "source-set-5e65d845ce77e1a0"
    )
    assert active_catalog_checks["full_canonical_source_count"]["equals"] == 350
    assert active_catalog_checks["full_canonical_artifact_count"]["equals"] == 319
    assert active_catalog_checks["full_canonical_source_delta_count"]["equals"] == 160
    assert active_catalog_checks["full_canonical_gap_count"]["equals"] == 1

    active_validation = suite_results["full_canonical_catalog_validation"]
    assert active_validation["required_for_current_promotion"] is False
    assert active_validation["required_for_full_canonical_corpus"] is True
    active_validation_checks = {
        check["name"]: check for check in active_validation["checks"]
    }
    assert active_validation_checks["full_canonical_catalog_validation_passed"]["equals"] is True
    assert active_validation_checks["full_canonical_catalog_validation_source_set"]["equals"] == (
        "source-set-5e65d845ce77e1a0"
    )

    full_canonical_currentness = suite_results["full_canonical_authority_currentness"]
    assert full_canonical_currentness["required_for_current_promotion"] is False
    assert full_canonical_currentness["required_for_full_canonical_corpus"] is True
    assert (
        full_canonical_currentness["path"]
        == "derived/{full_canonical_source_set_id}/authority_currentness/authority_currentness_report.json"
    )
    currentness_checks = {
        check["name"]: check for check in full_canonical_currentness["checks"]
    }
    assert currentness_checks["full_canonical_authority_currentness_schema"]["equals"] == (
        "authority-currentness-report-v0"
    )
    assert currentness_checks["full_canonical_authority_currentness_source_set"]["equals"] == (
        "source-set-5e65d845ce77e1a0"
    )
    assert (
        currentness_checks["full_canonical_authority_currentness_validation_passed"][
            "equals"
        ]
        is True
    )
    assert (
        currentness_checks[
            "full_canonical_authority_currentness_active_review_corpus_count"
        ]["equals"]
        == 349
    )
    assert (
        currentness_checks["full_canonical_authority_currentness_candidate_blocked_count"][
            "equals"
        ]
        == 1
    )

    full_canonical_graph = suite_results["full_canonical_nepa_3d_source_set_graph_validation"]
    assert full_canonical_graph["required_for_current_promotion"] is False
    assert full_canonical_graph["required_for_full_canonical_corpus"] is True
    assert (
        full_canonical_graph["path"]
        == "derived/{full_canonical_source_set_id}/knowledge_graph/nepa_3d_graph_validation.json"
    )
    full_graph_checks = {check["name"]: check for check in full_canonical_graph["checks"]}
    assert full_graph_checks["full_canonical_source_set_graph_validation_passed"]["equals"] is True
    assert (
        full_graph_checks["full_canonical_source_set_graph_no_failure_categories"]["equals"]
        == {}
    )

    full_canonical_graph_summary = suite_results[
        "full_canonical_nepa_3d_source_set_graph_summary"
    ]
    assert full_canonical_graph_summary["required_for_current_promotion"] is False
    assert full_canonical_graph_summary["required_for_full_canonical_corpus"] is True
    assert (
        full_canonical_graph_summary["path"]
        == "derived/{full_canonical_source_set_id}/knowledge_graph/nepa_3d_graph_summary.json"
    )
    full_graph_summary_checks = {
        check["name"]: check for check in full_canonical_graph_summary["checks"]
    }
    assert (
        full_graph_summary_checks["full_canonical_source_set_graph_source_set_matches"][
            "equals"
        ]
        == "source-set-5e65d845ce77e1a0"
    )
    assert (
        full_graph_summary_checks[
            "full_canonical_source_set_graph_catalog_source_record_count"
        ]["equals"]
        == 350
    )
    assert (
        full_graph_summary_checks["full_canonical_source_set_graph_validation_checks"][
            "min"
        ]
        == 65
    )
    assert (
        full_graph_summary_checks[
            "full_canonical_source_set_graph_region1_ready_profiles_visible"
        ]["min"]
        == 10
    )
    assert (
        full_graph_summary_checks[
            "full_canonical_source_set_graph_region1_blocked_profiles_cleared"
        ]["equals"]
        == 0
    )

    full_canonical_profile_eval = suite_results["full_canonical_forest_plan_profile_eval"]
    assert full_canonical_profile_eval["required_for_current_promotion"] is False
    assert full_canonical_profile_eval["required_for_full_canonical_corpus"] is True
    assert (
        full_canonical_profile_eval["path"]
        == "evaluations/forest_plan_profile/forest_plan_profile_eval_results.json"
    )
    full_profile_eval_checks = {
        check["name"]: check for check in full_canonical_profile_eval["checks"]
    }
    assert (
        full_profile_eval_checks["full_canonical_forest_plan_profile_eval_passed"][
            "equals"
        ]
        is True
    )
    assert (
        full_profile_eval_checks["full_canonical_forest_plan_profile_eval_contract_id"][
            "equals"
        ]
        == "region1-forest-plan-profile-eval-coverage"
    )
    assert (
        full_profile_eval_checks[
            "full_canonical_forest_plan_profile_eval_source_set_matches"
        ]["equals"]
        == ["source-set-5e65d845ce77e1a0"]
    )
    assert (
        full_profile_eval_checks["full_canonical_forest_plan_profile_eval_covered_count"][
            "min"
        ]
        == 10
    )
    assert (
        full_profile_eval_checks[
            "full_canonical_forest_plan_profile_eval_fixture_contract_defined_count"
        ]["equals"]
        == 0
    )
    assert (
        full_profile_eval_checks["full_canonical_forest_plan_profile_eval_not_started_count"][
            "equals"
        ]
        == 0
    )
    assert (
        full_profile_eval_checks[
            "full_canonical_forest_plan_profile_eval_profile_failure_count"
        ]["equals"]
        == 0
    )

    full_component_retrieval = suite_results[
        "full_canonical_forest_plan_component_retrieval_eval"
    ]
    assert full_component_retrieval["required_for_current_promotion"] is False
    assert full_component_retrieval["required_for_full_canonical_corpus"] is True
    assert (
        full_component_retrieval["path"]
        == "evaluations/forest_plan_component_retrieval/"
        "forest_plan_component_retrieval_eval_results.json"
    )
    full_component_retrieval_checks = {
        check["name"]: check for check in full_component_retrieval["checks"]
    }
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_passed"
        ]["equals"]
        is True
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_contract_id"
        ]["equals"]
        == "region1-forest-plan-component-retrieval-eval"
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_source_set_matches"
        ]["equals"]
        == "source-set-5e65d845ce77e1a0"
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_active_source_set_matches"
        ]["equals"]
        == ["source-set-5e65d845ce77e1a0"]
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_case_count"
        ]["min"]
        == 6
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_expected_pass_case_count"
        ]["min"]
        == 4
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_hard_negative_case_count"
        ]["min"]
        == 2
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_required_forests_covered"
        ]["contains_all"]
        == [
            "beaverhead-deerlodge-nf",
            "custer-gallatin-nf",
            "flathead-nf",
        ]
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_precision"
        ]["min"]
        == 1.0
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_recall"
        ]["min"]
        == 1.0
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_wrong_forest_rate"
        ]["equals"]
        == 0.0
    )

    full_component_coverage = suite_results[
        "full_canonical_forest_plan_component_eval_coverage"
    ]
    assert full_component_coverage["required_for_current_promotion"] is False
    assert full_component_coverage["required_for_full_canonical_corpus"] is True
    assert (
        full_component_coverage["path"]
        == "evaluations/forest_plan_component_eval_coverage/"
        "forest_plan_component_eval_coverage_results.json"
    )
    full_component_coverage_checks = {
        check["name"]: check for check in full_component_coverage["checks"]
    }
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_passed"
        ]["equals"]
        is True
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_id"
        ]["equals"]
        == "region1-forest-plan-component-eval-coverage"
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_required_review_count"
        ]["equals"]
        == 3
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_covered_review_count"
        ]["equals"]
        == 3
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_required_review_ids"
        ]["contains_all"]
        == [
            "v1-cg-ecid-compliance-review",
            "v1-cg-ecid-source-delta-review",
            "west-reservoir-67436",
        ]
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_covered_review_ids"
        ]["contains_all"]
        == [
            "v1-cg-ecid-compliance-review",
            "v1-cg-ecid-source-delta-review",
            "west-reservoir-67436",
        ]
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_distinct_forest_count"
        ]["min"]
        == 2
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_missing_contract_count"
        ]["equals"]
        == 0
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_missing_result_count"
        ]["equals"]
        == 0
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_stale_identity_count"
        ]["equals"]
        == 0
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_unresolved_review_count"
        ]["equals"]
        == 0
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_blocked_typed_slot_count"
        ]["equals"]
        == 0
    )


def test_committed_promotion_suite_requires_milestone_4_applicability_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}

    compliance_gold = suite_results["compliance_gold_eval"]
    assert compliance_gold["required_for_current_promotion"] is True
    assert compliance_gold["path"] == "reviews/compliance_gold_eval/compliance_gold_eval_results.json"
    compliance_gold_checks = {check["name"]: check for check in compliance_gold["checks"]}
    assert compliance_gold_checks["compliance_gold_eval_passed"]["equals"] is True
    assert compliance_gold_checks["compliance_gold_eval_cases"]["min"] == 14
    assert compliance_gold_checks["compliance_gold_required_coverage_tags_present"]["equals"] == []
    assert (
        compliance_gold_checks["compliance_gold_required_package_style_tags_present"]["equals"]
        == []
    )
    assert compliance_gold_checks["compliance_gold_rule_pack_version"]["equals"] == "0.4.0"

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
    assert gold_checks["applicability_gold_eval_case_count"]["min"] == 12
    assert gold_checks["applicability_gold_eval_source_chunk_count"]["min"] == 12
    assert gold_checks["applicability_gold_eval_weak_only_arbitration"]["min"] == 1
    assert gold_checks["applicability_gold_eval_unresolved_profile"]["min"] == 1
    assert gold_checks["applicability_gold_eval_adjudicated_profile"]["min"] == 1
    assert gold_checks["authority_family_adjudicated_coverage"]["min"] == 7
    assert gold_checks["applicability_gold_family_group_coverage_passed"]["equals"] is True
    assert gold_checks["applicability_gold_required_family_group_count"]["equals"] == 7
    assert gold_checks["applicability_gold_positive_family_group_coverage"]["equals"] == 7
    assert gold_checks["applicability_gold_negative_family_group_coverage"]["equals"] == 7
    assert gold_checks["applicability_gold_unresolved_family_group_coverage"]["min"] == 3
    assert gold_checks["applicability_gold_adjudicated_family_group_coverage"]["equals"] == 7
    assert gold_checks["applicability_gold_unmapped_high_priority_families"]["equals"] == 0

    aggregate_gold = suite_results["gold_coverage_eval"]
    assert aggregate_gold["required_for_current_promotion"] is True
    assert aggregate_gold["path"] == "reviews/gold_coverage_eval/gold_coverage_eval_results.json"
    aggregate_gold_checks = {check["name"]: check for check in aggregate_gold["checks"]}
    assert aggregate_gold_checks["gold_coverage_eval_passed"]["equals"] is True
    assert aggregate_gold_checks["gold_coverage_eval_required_theme_count"]["equals"] == 7
    assert aggregate_gold_checks["gold_coverage_eval_passed_theme_count"]["equals"] == 7
    assert (
        aggregate_gold_checks["gold_coverage_eval_required_high_priority_family_count"]["equals"]
        == 19
    )
    assert (
        aggregate_gold_checks["gold_coverage_eval_unmapped_high_priority_family_count"][
            "equals"
        ]
        == 0
    )
    assert aggregate_gold_checks["gold_coverage_eval_applicability_case_count"]["min"] == 12
    assert aggregate_gold_checks["gold_coverage_eval_compliance_case_count"]["min"] == 14
    assert (
        aggregate_gold_checks["gold_coverage_eval_required_review_contract_count"]["equals"]
        == 3
    )
    assert aggregate_gold_checks["gold_coverage_eval_distinct_forest_count"]["min"] == 2
    assert aggregate_gold_checks["gold_coverage_eval_distinct_package_style_count"]["min"] == 3
    assert aggregate_gold_checks["gold_coverage_eval_reviewer_ready_review_count"]["min"] == 3
    assert aggregate_gold_checks["gold_coverage_eval_typed_blocked_review_count"]["min"] == 0
    assert (
        aggregate_gold_checks["gold_coverage_eval_missing_review_contract_count"]["equals"]
        == 0
    )
    assert (
        aggregate_gold_checks["gold_coverage_eval_missing_package_authority_count"]["equals"]
        == 0
    )


def test_committed_promotion_suite_requires_milestone_5_report_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}
    review_case = manifest["review_cases"][0]
    results = {result["id"]: result for result in review_case["results"]}

    phase = suite_results["phase_eval_core"]
    assert phase["path"] == "reviews/v1-cg-ecid-compliance-review/phase_eval_results.json"
    phase_checks = {check["name"]: check for check in phase["checks"]}
    assert phase_checks["core_passed_phase_count"]["min"] == 19
    assert phase_checks["core_reviewer_ready_phase_count"]["min"] == 19
    assert phase_checks["phase_eval_contract_id"]["equals"] == "phase-eval-direct-eval-v1"
    assert phase_checks["phase_eval_proxy_only_phase_count"]["equals"] == 0
    assert phase_checks["phase_eval_missing_direct_eval_phase_count"]["equals"] == 0
    assert phase_checks["phase_eval_threshold_failed_phase_count"]["equals"] == 0
    assert phase_checks["phase_eval_contract_backed_promotion_ready"]["equals"] is True
    assert phase_checks["phase_eval_required_review_eval_ids"]["contains_all"] == [
        "v1_ea_eval",
        "real_package_review_coverage",
        "forest_plan_component_eval_coverage",
    ]
    assert phase_checks["phase_eval_missing_review_eval_ids"]["equals"] == []
    assert phase_checks["phase_eval_review_direct_eval_status"]["equals"] == (
        "direct_eval_present"
    )
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
    assert decision_checks["decision_support_applicable_authorities"]["equals"] == 37
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

    final_qa = results["final_qa_certification_report"]
    assert final_qa["required_for_current_promotion"] is True
    assert (
        final_qa["path"]
        == "reviews/{review_id}/final_qa/east_crazies_final_qa_certification.json"
    )
    final_qa_checks = {check["name"]: check for check in final_qa["checks"]}
    assert final_qa_checks["final_qa_report_schema"]["equals"] == (
        "east-crazies-final-qa-certification-report-v1"
    )
    assert final_qa_checks["final_qa_machine_replay_passed"]["equals"] == "passed"
    assert final_qa_checks["final_qa_finding_count"]["equals"] == 37
    assert final_qa_checks["final_qa_accepted_v1_risk_visible"]["equals"] == 14
    assert final_qa_checks["final_qa_legal_conclusion_boundary"]["equals"] is False

    final_qa_manifest = results["final_qa_certification_manifest"]
    assert final_qa_manifest["required_for_current_promotion"] is True
    assert (
        final_qa_manifest["path"]
        == "reviews/{review_id}/final_qa/east_crazies_final_qa_certification_manifest.json"
    )
    final_qa_manifest_checks = {
        check["name"]: check for check in final_qa_manifest["checks"]
    }
    assert final_qa_manifest_checks["final_qa_manifest_schema"]["equals"] == (
        "east-crazies-final-qa-certification-manifest-v1"
    )
    assert final_qa_manifest_checks["final_qa_manifest_validation_status"]["equals"] == "passed"

    final_qa_pdf = results["final_qa_certification_pdf"]
    assert final_qa_pdf["required_for_current_promotion"] is True
    assert (
        final_qa_pdf["path"]
        == "reviews/{review_id}/final_qa/east_crazies_final_qa_certification.pdf"
    )
    final_qa_pdf_checks = {check["name"]: check for check in final_qa_pdf["checks"]}
    assert final_qa_pdf_checks["final_qa_pdf_header_valid"]["starts_with"] == "%PDF-"

    final_qa_validation = results["final_qa_certification_validation"]
    assert final_qa_validation["required_for_current_promotion"] is True
    assert (
        final_qa_validation["path"]
        == "reviews/{review_id}/final_qa/east_crazies_final_qa_certification_validation.json"
    )
    final_qa_validation_checks = {
        check["name"]: check for check in final_qa_validation["checks"]
    }
    assert final_qa_validation_checks["final_qa_validation_schema"]["equals"] == (
        "east-crazies-final-qa-certification-validation-v1"
    )
    assert final_qa_validation_checks["final_qa_validation_passed"]["equals"] is True
    assert final_qa_validation_checks["final_qa_validation_failed_check_count"]["equals"] == 0
    assert final_qa_validation_checks["final_qa_validation_check_count"]["min"] == 157
    assert "file_sha256_matches" in final_qa_validation_checks[
        "final_qa_validation_report_hash_matches_file"
    ]
    assert "file_sha256_matches" in final_qa_validation_checks[
        "final_qa_validation_markdown_hash_matches_file"
    ]
    assert "file_sha256_matches" in final_qa_validation_checks[
        "final_qa_validation_pdf_hash_matches_file"
    ]
    assert "file_sha256_matches" in final_qa_validation_checks[
        "final_qa_validation_manifest_hash_matches_file"
    ]

    provenance = results["authority_family_provenance"]
    assert provenance["required_for_current_promotion"] is True
    assert provenance["path"] == "reviews/{review_id}/authority_family_provenance.json"
    provenance_checks = {check["name"]: check for check in provenance["checks"]}
    assert provenance_checks["authority_provenance_generated_mode"]["equals"] is True
    assert provenance_checks["authority_provenance_finding_count"]["equals"] == 37
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

    source_graph = suite_results["nepa_3d_source_set_graph_validation"]
    assert source_graph["required_for_current_promotion"] is True
    assert (
        source_graph["path"]
        == "derived/{source_set_id}/knowledge_graph/nepa_3d_graph_validation.json"
    )
    assert source_graph["failure_category"] == "graph_viewer_export_invalid"
    source_graph_checks = {check["name"]: check for check in source_graph["checks"]}
    assert source_graph_checks["source_set_graph_validation_passed"]["equals"] is True
    assert source_graph_checks["source_set_graph_no_failure_categories"]["equals"] == {}

    source_graph_summary = suite_results["nepa_3d_source_set_graph_summary"]
    assert source_graph_summary["required_for_current_promotion"] is True
    assert (
        source_graph_summary["path"]
        == "derived/{source_set_id}/knowledge_graph/nepa_3d_graph_summary.json"
    )
    summary_checks = {check["name"]: check for check in source_graph_summary["checks"]}
    assert summary_checks["source_set_graph_source_set_matches"]["equals"] == (
        "source-set-ba8d0feae79501b8"
    )
    assert summary_checks["source_set_graph_node_count"]["min"] == 1
    assert summary_checks["source_set_graph_validation_checks"]["min"] == 62

    review_graph = results["nepa_3d_review_graph_validation"]
    assert review_graph["required_for_current_promotion"] is True
    assert (
        review_graph["path"]
        == "reviews/{review_id}/knowledge_graph/nepa_3d_graph_validation.json"
    )
    assert review_graph["failure_category"] == "graph_viewer_export_invalid"
    review_graph_checks = {check["name"]: check for check in review_graph["checks"]}
    assert review_graph_checks["review_graph_validation_passed"]["equals"] is True
    assert review_graph_checks["review_graph_no_failure_categories"]["equals"] == {}

    review_graph_summary = results["nepa_3d_review_graph_summary"]
    assert review_graph_summary["required_for_current_promotion"] is True
    assert (
        review_graph_summary["path"]
        == "reviews/{review_id}/knowledge_graph/nepa_3d_graph_summary.json"
    )
    review_summary_checks = {
        check["name"]: check for check in review_graph_summary["checks"]
    }
    assert review_summary_checks["review_graph_review_id_matches"]["equals"] == (
        "v1-cg-ecid-compliance-review"
    )
    assert review_summary_checks["review_graph_decision_count"]["equals"] == 377
    assert review_summary_checks["review_graph_validation_checks"]["min"] == 76


def test_run_promotion_suite_reports_full_canonical_corpus_readiness_separately(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "source_library"
    (output_dir / "catalog").mkdir(parents=True)
    (tmp_path / "config").mkdir()

    rule_pack_path = tmp_path / "config" / "rule_pack.json"
    rule_pack_path.write_text(
        json.dumps(
            {
                "rule_pack_id": "rule-pack-test",
                "version": "1.0.0",
                "rules": [{"id": "r1"}],
                "baseline_source_record_ids": ["R1EA-001"],
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "catalog" / "source_set_manifest.json").write_text(
        json.dumps(
            {
                "source_set_id": "source-set-stale",
                "download_batch_run_ids": ["run-a", "run-b"],
                "source_count": 350,
                "artifact_count": 319,
                "source_partition_counts": {"active_review_corpus": 349},
                "source_delta_input": {
                    "source_delta_count": 160,
                    "gap_count": 1,
                    "skipped_gap_source_record_ids": ["R1PLAN-kootenai-nf-18"],
                },
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "catalog" / "catalog_validation.json").write_text(
        json.dumps({"source_set_id": "source-set-full", "passed": True}),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "config" / "promotion_suite.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": PROMOTION_SUITE_SCHEMA_VERSION,
                "id": "suite-test",
                "source_set_id": "source-set-current",
                "full_canonical_source_set_id": "source-set-full",
                "rule_pack_path": "config/rule_pack.json",
                "rule_pack_id": "rule-pack-test",
                "rule_pack_version": "1.0.0",
                "expected_rule_count": 1,
                "expected_baseline_source_record_count": 1,
                "review_cases": [],
                "suite_results": [
                    {
                        "id": "full_canonical_catalog_manifest",
                        "path": "catalog/source_set_manifest.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "failure_category": "stale_artifact",
                        "checks": [
                            {
                                "name": "full_canonical_source_set_matches",
                                "json_path": "source_set_id",
                                "equals": "source-set-full",
                            }
                        ],
                    },
                    {
                        "id": "full_canonical_catalog_validation",
                        "path": "catalog/catalog_validation.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_catalog_validation_passed",
                                "json_path": "passed",
                                "equals": True,
                            }
                        ],
                    },
                ],
                "expansion_slots": [],
            }
        ),
        encoding="utf-8",
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)

    assert result.summary["source_set_id"] == "source-set-current"
    assert result.summary["current_promotion_source_set_id"] == "source-set-current"
    assert result.summary["full_canonical_source_set_id"] == "source-set-full"
    assert result.summary["current_promotion_ready"] is True
    assert result.summary["full_canonical_corpus_ready"] is False
    assert result.summary["required_full_canonical_result_count"] == 2
    assert result.summary["passed_required_full_canonical_result_count"] == 1
    assert result.summary["full_canonical_failure_category_counts"] == {
        "stale_artifact": 1
    }
    report_text = result.markdown_path.read_text(encoding="utf-8")
    assert "Full canonical source set" in report_text
    assert "Full canonical corpus ready" in report_text


def test_run_promotion_suite_supports_full_canonical_artifact_paths(tmp_path: Path) -> None:
    output_dir = tmp_path / "source_library"
    (output_dir / "catalog").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    full_source_set_id = "source-set-full"

    rule_pack_path = tmp_path / "config" / "rule_pack.json"
    rule_pack_path.write_text(
        json.dumps(
            {
                "rule_pack_id": "rule-pack-test",
                "version": "1.0.0",
                "rules": [{"id": "r1"}],
                "baseline_source_record_ids": ["R1EA-001"],
            }
        ),
        encoding="utf-8",
    )

    (output_dir / "catalog" / "source_set_manifest.json").write_text(
        json.dumps({"source_set_id": full_source_set_id}),
        encoding="utf-8",
    )
    (output_dir / "catalog" / "catalog_validation.json").write_text(
        json.dumps({"source_set_id": full_source_set_id, "passed": True}),
        encoding="utf-8",
    )

    currentness_dir = (
        output_dir
        / "derived"
        / full_source_set_id
        / "authority_currentness"
    )
    currentness_dir.mkdir(parents=True)
    (currentness_dir / "authority_currentness_report.json").write_text(
        json.dumps(
            {
                "schema_version": "authority-currentness-report-v0",
                "source_set_id": full_source_set_id,
                "summary": {
                    "validation_passed": True,
                    "catalog_source_partition_counts": {
                        "active_review_corpus": 349,
                        "candidate_blocked_source": 1,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    graph_dir = output_dir / "derived" / full_source_set_id / "knowledge_graph"
    graph_dir.mkdir(parents=True)
    (graph_dir / "nepa_3d_graph_validation.json").write_text(
        json.dumps({"passed": True, "failure_category_counts": {}}),
        encoding="utf-8",
    )
    (graph_dir / "nepa_3d_graph_summary.json").write_text(
        json.dumps(
            {
                "source_set_id": full_source_set_id,
                "validation_passed": True,
                "catalog_source_record_count": 350,
                "node_count": 10,
                "edge_count": 12,
                "validation_check_count": 65,
                "failed_validation_check_count": 0,
                "region1_forest_plan_graph_ready_profile_count": 10,
                "region1_forest_plan_blocked_profile_count": 0,
            }
        ),
        encoding="utf-8",
    )
    profile_eval_dir = output_dir / "evaluations" / "forest_plan_profile"
    profile_eval_dir.mkdir(parents=True)
    (profile_eval_dir / "forest_plan_profile_eval_results.json").write_text(
        json.dumps(
            {
                "contract_id": "region1-forest-plan-profile-eval-coverage",
                "active_source_set_ids": [full_source_set_id],
                "covered_profile_count": 10,
                "fixture_contract_defined_profile_count": 0,
                "not_started_profile_count": 0,
                "passed": True,
                "profile_failure_count": 0,
                "profiles_below_floor_ids": [],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "config" / "promotion_suite.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": PROMOTION_SUITE_SCHEMA_VERSION,
                "id": "suite-test",
                "source_set_id": "source-set-current",
                "full_canonical_source_set_id": full_source_set_id,
                "rule_pack_path": "config/rule_pack.json",
                "rule_pack_id": "rule-pack-test",
                "rule_pack_version": "1.0.0",
                "expected_rule_count": 1,
                "expected_baseline_source_record_count": 1,
                "review_cases": [],
                "suite_results": [
                    {
                        "id": "full_canonical_catalog_manifest",
                        "path": "catalog/source_set_manifest.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_source_set_matches",
                                "json_path": "source_set_id",
                                "equals": full_source_set_id,
                            }
                        ],
                    },
                    {
                        "id": "full_canonical_catalog_validation",
                        "path": "catalog/catalog_validation.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_catalog_validation_passed",
                                "json_path": "passed",
                                "equals": True,
                            }
                        ],
                    },
                    {
                        "id": "full_canonical_authority_currentness",
                        "path": "derived/{full_canonical_source_set_id}/authority_currentness/authority_currentness_report.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_authority_currentness_validation_passed",
                                "json_path": "summary.validation_passed",
                                "equals": True,
                            }
                        ],
                    },
                    {
                        "id": "full_canonical_nepa_3d_source_set_graph_validation",
                        "path": "derived/{full_canonical_source_set_id}/knowledge_graph/nepa_3d_graph_validation.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_source_set_graph_validation_passed",
                                "json_path": "passed",
                                "equals": True,
                            }
                        ],
                    },
                    {
                        "id": "full_canonical_nepa_3d_source_set_graph_summary",
                        "path": "derived/{full_canonical_source_set_id}/knowledge_graph/nepa_3d_graph_summary.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_source_set_graph_validation_passed",
                                "json_path": "validation_passed",
                                "equals": True,
                            },
                            {
                                "name": "full_canonical_source_set_graph_region1_ready_profiles_visible",
                                "json_path": "region1_forest_plan_graph_ready_profile_count",
                                "min": 10,
                            },
                            {
                                "name": "full_canonical_source_set_graph_region1_blocked_profiles_cleared",
                                "json_path": "region1_forest_plan_blocked_profile_count",
                                "equals": 0,
                            },
                        ],
                    },
                    {
                        "id": "full_canonical_forest_plan_profile_eval",
                        "path": "evaluations/forest_plan_profile/forest_plan_profile_eval_results.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_forest_plan_profile_eval_passed",
                                "json_path": "passed",
                                "equals": True,
                            },
                            {
                                "name": "full_canonical_forest_plan_profile_eval_source_set_matches",
                                "json_path": "active_source_set_ids",
                                "equals": [full_source_set_id],
                            },
                        ],
                    },
                ],
                "expansion_slots": [],
            }
        ),
        encoding="utf-8",
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)

    assert result.summary["full_canonical_corpus_ready"] is True
    assert result.summary["required_full_canonical_result_count"] == 6
    assert result.summary["passed_required_full_canonical_result_count"] == 6
    suite_results = {item["id"]: item for item in result.summary["suite_results"]}
    assert suite_results["full_canonical_authority_currentness"]["path"].endswith(
        f"derived/{full_source_set_id}/authority_currentness/authority_currentness_report.json"
    )
    assert suite_results["full_canonical_nepa_3d_source_set_graph_validation"][
        "path"
    ].endswith(
        f"derived/{full_source_set_id}/knowledge_graph/nepa_3d_graph_validation.json"
    )
    assert suite_results["full_canonical_forest_plan_profile_eval"]["path"].endswith(
        "evaluations/forest_plan_profile/forest_plan_profile_eval_results.json"
    )


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
    assert south_plateau_compliance["failure_category"] == "forest_plan_reviewer_not_ready"
    south_plateau_compliance_checks = {
        check["name"]: check for check in south_plateau_compliance["checks"]
    }
    assert south_plateau_compliance_checks["reviewer_ready"]["equals"] is True
    assert south_plateau_compliance_checks["rule_count"]["equals"] == 61
    assert south_plateau_compliance_checks["rule_claim_gap_count"]["equals"] == 0
    assert south_plateau_compliance_checks["rule_claim_link_count"]["equals"] == 280
    assert (
        south_plateau_compliance_checks[
            "forest_plan_scope_status_matches_declared_profile"
        ]["equals"]
        == "custer_gallatin"
    )
    assert (
        south_plateau_compliance_checks["forest_plan_validation_passed"][
            "failure_category"
        ]
        == "forest_plan_reviewer_not_ready"
    )
    assert (
        south_plateau_compliance_checks["forest_plan_reviewer_ready"]["equals"] is True
    )

    south_plateau_forest_context = south_plateau_results["forest_plan_context_summary"]
    forest_context_checks = {
        check["name"]: check for check in south_plateau_forest_context["checks"]
    }
    assert south_plateau_forest_context["required_for_expansion"] is True
    assert (
        forest_context_checks[
            "forest_plan_context_scope_status_matches_declared_profile"
        ]["equals"]
        == "custer_gallatin"
    )
    assert (
        forest_context_checks["forest_plan_context_validation_passed"][
            "failure_category"
        ]
        == "forest_plan_reviewer_not_ready"
    )
    assert forest_context_checks["forest_plan_context_reviewer_ready"]["equals"] is True

    south_plateau_phase = south_plateau_results["phase_eval"]
    south_plateau_phase_checks = {
        check["name"]: check for check in south_plateau_phase["checks"]
    }
    assert south_plateau_phase_checks["phase_eval_passed"]["equals"] is True
    assert south_plateau_phase_checks["phase_eval_reviewer_ready"]["equals"] is True
    assert south_plateau_phase_checks["phase_eval_passed_phase_count"]["equals"] == 19
    assert south_plateau_phase_checks["phase_eval_declared_review_contract"]["equals"] is True
    assert south_plateau_phase_checks["phase_eval_contract_backed_promotion_ready"]["equals"] is True

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
    assert third_slot["last_local_signal"]["forest_plan_scope_status"] == "custer_gallatin"
    assert third_slot["last_local_signal"]["forest_plan_context_validation_passed"] is True
    assert third_slot["last_local_signal"]["forest_plan_context_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["forest_plan_component_gate_required"] is True
    assert third_slot["last_local_signal"]["forest_plan_component_count"] == 329
    assert third_slot["last_local_signal"]["forest_plan_component_applicable_count"] == 152
    assert third_slot["last_local_signal"]["forest_plan_component_applicable_standard_count"] == 24
    assert third_slot["last_local_signal"]["forest_plan_component_applied_standard_count"] == 21
    assert third_slot["last_local_signal"]["forest_plan_component_reviewer_resolution_count"] == 31
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_eval_passed"] is True
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_pending_count"] == 0
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_resolved_count"] == 31
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_system_miss_count"] == 31
    assert third_slot["last_local_signal"]["phase_eval_passed"] is True
    assert third_slot["last_local_signal"]["phase_eval_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["phase_eval_passed_phase_count"] == 19
    assert third_slot["last_local_signal"]["phase_eval_phase_count"] == 19
    assert third_slot["last_local_signal"]["adjudication_eval_passed"] is True
    assert third_slot["last_local_signal"]["adjudication_resolved_count"] == 6
    assert third_slot["last_local_signal"]["adjudication_apply_passed"] is True
    assert third_slot["last_local_signal"]["adjudication_applied_item_count"] == 6
    assert "package_manifest" in gate_artifacts
    assert "applicability_validation" in gate_artifacts
    assert "generated_rule_pack_validation" in gate_artifacts
    assert "compliance_review" in gate_artifacts
    assert "forest_plan_context_summary" in gate_artifacts
    assert "forest_plan_component_findings" in gate_artifacts
    assert "forest_plan_reviewer_resolution_queue" in gate_artifacts
    assert "forest_plan_component_adjudication_template" in gate_artifacts
    assert "forest_plan_component_adjudication_eval" in gate_artifacts
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


def test_promotion_suite_fails_stale_validation_sidecar_file_hash(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "source_library"
    manifest_path = tmp_path / "promotion_suite.json"
    _write_json(
        tmp_path / "rule_pack.json",
        {
            "rule_pack_id": "rules-v0",
            "version": "1.0.0",
            "baseline_source_record_ids": ["R1EA-001"],
            "rules": [{"id": "rule-1"}],
        },
    )
    report_path = (
        output_dir / "reviews" / "review-1" / "final_qa" / "final_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("first version\n", encoding="utf-8")
    validation_path = report_path.parent / "validation.json"
    _write_json(
        validation_path,
        {
            "passed": True,
            "output_files": {"json": "source_library/reviews/review-1/final_qa/final_report.json"},
            "output_hashes": {"json_sha256": _sha256_bytes(b"different version\n")},
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
            "expected_rule_count": 1,
            "expected_baseline_source_record_count": 1,
            "review_cases": [
                {
                    "id": "case-1",
                    "review_id": "review-1",
                    "results": [
                        {
                            "id": "final_qa_certification_validation",
                            "path": "reviews/{review_id}/final_qa/validation.json",
                            "failure_category": "stale_artifact",
                            "checks": [
                                {
                                    "name": "final_qa_validation_passed",
                                    "json_path": "passed",
                                    "equals": True,
                                },
                                {
                                    "name": "final_qa_validation_report_hash_matches_file",
                                    "file_sha256_matches": {
                                        "path_json_path": "output_files.json",
                                        "sha256_json_path": "output_hashes.json_sha256",
                                    },
                                },
                            ],
                        }
                    ],
                }
            ],
            "suite_results": [],
            "expansion_slots": [],
        },
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)

    assert result.summary["current_promotion_ready"] is False
    failed_result = result.summary["review_cases"][0]["results"][0]
    failed_check = next(
        check
        for check in failed_result["checks"]
        if check["name"] == "final_qa_validation_report_hash_matches_file"
    )
    assert failed_check["passed"] is False
    assert failed_check["failure_category"] == "stale_artifact"


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


def test_promotion_suite_blocks_declared_forest_profile_false_pass(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].extend(
        [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "compliance_review_reviewer_ready",
                        "json_path": "summary.reviewer_ready",
                        "equals": True,
                    },
                    {
                        "name": "forest_plan_scope_status_matches_declared_profile",
                        "json_path": "summary.forest_plan_review.scope_status",
                        "equals": "custer_gallatin",
                        "failure_category": "forest_plan_reviewer_not_ready",
                    },
                ],
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_context_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "phase_eval_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
        ]
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "forest_plan_profile": "custer_gallatin",
        "expected_gate_artifacts": [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
            },
        ],
        "last_local_signal": {
            "forest_plan_scope_status": "ambiguous",
            "forest_plan_component_gate_required": False,
        },
        "next_action": "Resolve the declared forest-plan context.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": True},
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "compliance_review.json",
        {
            "summary": {
                "reviewer_ready": True,
                "forest_plan_review": {
                    "scope_status": "ambiguous",
                    "validation_passed": False,
                    "reviewer_ready": False,
                    "needs_reviewer_resolution": True,
                },
            }
        },
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "scope_status": "ambiguous",
            "validation_passed": False,
            "reviewer_ready": False,
            "needs_reviewer_resolution": True,
        },
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "phase_eval_results.json",
        {
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "passed": True,
            "reviewer_ready": True,
            "passed_phase_count": 2,
            "phase_count": 2,
            "phases": [
                {"name": "applicability_validation", "passed": True, "reviewer_ready": True},
                {"name": "compliance_review", "passed": True, "reviewer_ready": True},
            ],
        },
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
        strict_expansion=True,
    )
    slot = result.summary["expansion_slots"][0]

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert set(result.summary["failure_category_counts"]) == {
        "forest_plan_reviewer_not_ready"
    }
    assert slot["manifest_ready"] is True
    assert slot["ready"] is False
    assert slot["failure_categories"] == ["forest_plan_reviewer_not_ready"]
    profile_checks = {
        check["name"]: check for check in slot["forest_plan_profile_checks"]
    }
    assert profile_checks["forest_plan_scope_status_matches_declared_profile"][
        "actual"
    ] == "ambiguous"
    assert profile_checks["forest_plan_reviewer_ready"]["passed"] is False


def test_promotion_suite_rejects_forest_profile_slot_missing_gate_artifact(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].extend(
        [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_reviewer_ready",
                        "json_path": "summary.forest_plan_review.reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_context_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "phase_eval_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
        ]
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "blocked_forest_plan_review",
        "ready": False,
        "failure_category": "forest_plan_reviewer_not_ready",
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "forest_plan_profile": "custer_gallatin",
        "expected_gate_artifacts": [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
            },
        ],
        "next_action": "Resolve the declared forest-plan context.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="forest_plan_context_summary"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_blocks_missing_required_forest_component_phase(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].extend(
        [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_reviewer_ready",
                        "json_path": "summary.forest_plan_review.reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_context_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "phase_eval_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
        ]
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "forest_plan_profile": "custer_gallatin",
        "expected_gate_artifacts": [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
            },
        ],
        "last_local_signal": {
            "forest_plan_scope_status": "custer_gallatin",
            "forest_plan_component_gate_required": True,
        },
        "next_action": "Run Forest Plan component evaluation.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": True},
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "compliance_review.json",
        {
            "summary": {
                "reviewer_ready": True,
                "forest_plan_review": {
                    "scope_status": "custer_gallatin",
                    "validation_passed": True,
                    "reviewer_ready": True,
                },
            }
        },
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "scope_status": "custer_gallatin",
            "validation_passed": True,
            "reviewer_ready": True,
        },
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "phase_eval_results.json",
        {
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "passed": True,
            "reviewer_ready": True,
            "passed_phase_count": 2,
            "phase_count": 2,
            "phases": [
                {"name": "applicability_validation", "passed": True, "reviewer_ready": True},
                {"name": "compliance_review", "passed": True, "reviewer_ready": True},
            ],
        },
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
        strict_expansion=True,
    )
    slot = result.summary["expansion_slots"][0]
    profile_checks = {
        check["name"]: check for check in slot["forest_plan_profile_checks"]
    }

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_artifacts_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert slot["manifest_ready"] is True
    assert slot["ready"] is False
    assert profile_checks["forest_plan_component_phase_present_when_required"][
        "passed"
    ] is False
    assert profile_checks["forest_plan_component_phase_present_when_required"][
        "actual"
    ] == ["applicability_validation", "compliance_review"]


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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
