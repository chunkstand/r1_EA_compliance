from __future__ import annotations

import json

from tests.support.promotion_suite_fixtures import COMMITTED_PROMOTION_SUITE


def test_committed_promotion_suite_declares_slot_driven_current_contract() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    contract = manifest["current_promotion_contract"]
    selector = contract["slot_selector"]

    assert selector["selector_type"] == "governed_coverage_class"
    assert selector["coverage_manifest_path"] == "config/v1_real_package_review_coverage_v1.json"
    assert (
        selector["coverage_results_path"]
        == "reviews/real_package_review_coverage_eval/real_package_review_coverage_eval_results.json"
    )
    assert selector["coverage_class_ids"] == ["current_promotion_reviewer_ready"]
    assert selector["allowed_contract_statuses"] == ["reviewer_ready"]
    assert contract["quorum"] == {
        "eligible_slot_count_min": 1,
        "passing_slot_count_min": 1,
    }
    family_ids = {family["id"] for family in contract["artifact_families"]}
    assert family_ids == {
        "current_suite_baseline",
        "current_review_core_artifacts",
        "current_review_packet_contract",
        "current_review_decision_support",
        "current_review_final_qa",
        "current_review_supporting_outputs",
    }
    final_qa_family = next(
        family
        for family in contract["artifact_families"]
        if family["id"] == "current_review_final_qa"
    )
    suite_family = next(
        family
        for family in contract["artifact_families"]
        if family["id"] == "current_suite_baseline"
    )
    review_packet_family = next(
        family
        for family in contract["artifact_families"]
        if family["id"] == "current_review_packet_contract"
    )
    decision_support_family = next(
        family
        for family in contract["artifact_families"]
        if family["id"] == "current_review_decision_support"
    )
    assert review_packet_family["review_result_ids"] == [
        "review_packet_row_inventory",
        "compliance_matrix_render_manifest",
        "review_packet_index",
        "review_packet_index_pdf",
        "review_packet_index_validation",
        "review_packet_direct_eval",
    ]
    assert decision_support_family["review_result_ids"] == [
        "decision_support_report",
        "decision_support_manifest",
        "decision_support_pdf",
        "decision_support_direct_eval",
    ]
    assert final_qa_family["review_result_ids"] == [
        "final_qa_certification_report",
        "final_qa_certification_manifest",
        "final_qa_certification_pdf",
        "final_qa_certification_validation",
        "final_qa_direct_eval",
    ]
    assert suite_family["suite_result_ids"] == [
        "phase_eval_core",
        "nepa_3d_source_set_graph_validation",
        "nepa_3d_source_set_graph_summary",
        "compliance_review_eval",
        "compliance_gold_eval",
        "applicability_eval_authority_family_coverage",
        "applicability_gold_eval_authority_family_adjudication",
        "gold_coverage_eval",
        "eval_trace_case_file_validation",
    ]
    reference_canary = contract["reference_canaries"][0]
    assert reference_canary["review_case_id"] == "v1-cg-ecid"
    assert reference_canary["required"] is True


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
        == 4
    )
    assert aggregate_gold_checks["gold_coverage_eval_distinct_forest_count"]["min"] == 3
    assert aggregate_gold_checks["gold_coverage_eval_distinct_package_style_count"]["min"] == 4
    assert aggregate_gold_checks["gold_coverage_eval_reviewer_ready_review_count"]["min"] == 3
    assert aggregate_gold_checks["gold_coverage_eval_typed_blocked_review_count"]["min"] == 1
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
    review_case = {case["id"]: case for case in manifest["review_cases"]}["v1-cg-ecid"]
    results = {result["id"]: result for result in review_case["results"]}

    phase = suite_results["phase_eval_core"]
    assert phase["required_for_current_promotion"] is True
    phase_checks = {check["name"]: check for check in phase["checks"]}
    assert phase_checks["phase_source_set_matches"]["equals"] == "source-set-f70ea11e04ae3d53"
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

    trace_case_file = suite_results["eval_trace_case_file_validation"]
    assert trace_case_file["required_for_current_promotion"] is True
    assert trace_case_file["path"] == (
        "evaluations/eval_trace/eval_trace_case_file_validation.json"
    )
    trace_case_checks = {check["name"]: check for check in trace_case_file["checks"]}
    assert trace_case_checks["eval_trace_case_file_validation_schema"]["equals"] == (
        "eval-trace-case-file-validation-summary-v1"
    )
    assert trace_case_checks["eval_trace_case_file_validation_passed"]["equals"] is True
    assert trace_case_checks["eval_trace_case_file_validation_case_count"]["min"] == 1
    assert trace_case_checks["eval_trace_case_file_validation_case_file"]["equals"] == (
        "config/eval_trace_cases/system_eval_trace_cases_v1.json"
    )
    assert trace_case_checks["eval_trace_case_file_validation_failures"]["equals"] == []
    assert trace_case_checks["eval_trace_case_file_validation_case_failures"]["equals"] == []

    decision_support = results["decision_support_report"]
    assert decision_support["required_for_current_promotion"] is True
    decision_checks = {check["name"]: check for check in decision_support["checks"]}
    assert decision_checks["decision_support_schema"]["equals"] == (
        "ea-consistency-decision-support-report-v1"
    )
    assert decision_checks["decision_support_status"]["equals"] == "reviewer_ready"
    assert decision_checks["decision_support_validation_passed"]["equals"] is True
    assert decision_checks["decision_support_legal_conclusion_boundary"]["equals"] is False

    decision_manifest = results["decision_support_manifest"]
    assert decision_manifest["required_for_current_promotion"] is True
    manifest_checks = {check["name"]: check for check in decision_manifest["checks"]}
    assert manifest_checks["decision_support_manifest_schema"]["equals"] == (
        "ea-consistency-decision-support-manifest-v1"
    )
    assert manifest_checks["decision_support_manifest_validation_status"]["equals"] == "passed"

    decision_pdf = results["decision_support_pdf"]
    assert decision_pdf["required_for_current_promotion"] is True
    pdf_checks = {check["name"]: check for check in decision_pdf["checks"]}
    assert pdf_checks["decision_support_pdf_header_valid"]["starts_with"] == "%PDF-"

    decision_direct_eval = results["decision_support_direct_eval"]
    assert decision_direct_eval["required_for_current_promotion"] is True
    assert decision_direct_eval["path"] == (
        "reviews/{review_id}/decision_support/"
        "ea_consistency_decision_support_direct_eval_results.json"
    )
    direct_eval_checks = {check["name"]: check for check in decision_direct_eval["checks"]}
    assert direct_eval_checks["decision_support_direct_eval_schema"]["equals"] == (
        "ea-consistency-decision-support-direct-eval-results-v1"
    )
    assert direct_eval_checks["decision_support_direct_eval_contract"]["equals"] == (
        "ea-consistency-decision-support-direct-eval-v1"
    )
    assert direct_eval_checks["decision_support_direct_eval_review_id"]["equals"] == (
        "v1-cg-ecid-compliance-review"
    )
    assert direct_eval_checks["decision_support_direct_eval_source_set"]["equals"] == (
        "source-set-f70ea11e04ae3d53"
    )
    assert direct_eval_checks["decision_support_direct_eval_present"]["equals"] is True
    assert direct_eval_checks["decision_support_direct_eval_passed"]["equals"] is True
    assert direct_eval_checks["decision_support_direct_eval_metric_group_count"]["min"] == 6
    assert direct_eval_checks["decision_support_direct_eval_required_groups_present"]["equals"] == []
    assert direct_eval_checks["decision_support_direct_eval_blocking_gaps"]["equals"] == []
    assert direct_eval_checks["decision_support_direct_eval_failure_intake_empty"]["equals"] == 0

    final_qa = results["final_qa_certification_report"]
    assert final_qa["required_for_current_promotion"] is True
    final_qa_checks = {check["name"]: check for check in final_qa["checks"]}
    assert final_qa_checks["final_qa_report_schema"]["equals"] == (
        "east-crazies-final-qa-certification-report-v1"
    )
    assert final_qa_checks["final_qa_machine_replay_passed"]["equals"] == "passed"
    assert final_qa_checks["final_qa_legal_conclusion_boundary"]["equals"] is False

    final_qa_manifest = results["final_qa_certification_manifest"]
    assert final_qa_manifest["required_for_current_promotion"] is True
    final_qa_manifest_checks = {
        check["name"]: check for check in final_qa_manifest["checks"]
    }
    assert final_qa_manifest_checks["final_qa_manifest_schema"]["equals"] == (
        "east-crazies-final-qa-certification-manifest-v1"
    )
    assert final_qa_manifest_checks["final_qa_manifest_validation_status"]["equals"] == "passed"

    final_qa_pdf = results["final_qa_certification_pdf"]
    assert final_qa_pdf["required_for_current_promotion"] is True
    final_qa_pdf_checks = {check["name"]: check for check in final_qa_pdf["checks"]}
    assert final_qa_pdf_checks["final_qa_pdf_header_valid"]["starts_with"] == "%PDF-"

    final_qa_validation = results["final_qa_certification_validation"]
    assert final_qa_validation["required_for_current_promotion"] is True
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

    final_qa_direct_eval = results["final_qa_direct_eval"]
    assert final_qa_direct_eval["required_for_current_promotion"] is True
    assert final_qa_direct_eval["path"] == (
        "reviews/{review_id}/final_qa/final_qa_direct_eval_results.json"
    )
    direct_eval_checks = {check["name"]: check for check in final_qa_direct_eval["checks"]}
    assert direct_eval_checks["final_qa_direct_eval_schema"]["equals"] == (
        "final-qa-direct-eval-results-v1"
    )
    assert direct_eval_checks["final_qa_direct_eval_contract"]["equals"] == (
        "final-qa-direct-eval-v1"
    )
    assert direct_eval_checks["final_qa_direct_eval_review_id"]["equals"] == (
        "v1-cg-ecid-compliance-review"
    )
    assert direct_eval_checks["final_qa_direct_eval_source_set"]["equals"] == (
        "source-set-f70ea11e04ae3d53"
    )
    assert direct_eval_checks["final_qa_direct_eval_present"]["equals"] is True
    assert direct_eval_checks["final_qa_direct_eval_passed"]["equals"] is True
    assert direct_eval_checks["final_qa_direct_eval_metric_group_count"]["min"] == 5
    assert direct_eval_checks["final_qa_direct_eval_required_groups_present"]["equals"] == []
    assert direct_eval_checks["final_qa_direct_eval_blocking_gaps"]["equals"] == []
    assert direct_eval_checks["final_qa_direct_eval_failure_intake_empty"]["equals"] == 0

    provenance = results["authority_family_provenance"]
    assert provenance["required_for_current_promotion"] is True
    provenance_checks = {check["name"]: check for check in provenance["checks"]}
    assert provenance_checks["authority_provenance_generated_mode"]["equals"] is True
    assert provenance_checks["authority_provenance_family_ids_present"]["equals"] == []
    assert provenance_checks["authority_provenance_candidate_ids_present"]["equals"] == []

    appendix = results["non_applicable_authority_appendix"]
    assert appendix["required_for_current_promotion"] is True
    appendix_checks = {check["name"]: check for check in appendix["checks"]}
    assert appendix_checks["non_applicable_authority_count"]["min"] == 1
    assert appendix_checks["non_applicable_authorities_have_coverage"]["equals"] is True
    assert appendix_checks["non_applicable_authorities_have_rationale"]["equals"] is True

    resolution = results["authority_reviewer_resolution_report"]
    assert resolution["required_for_current_promotion"] is True
    resolution_checks = {check["name"]: check for check in resolution["checks"]}
    assert resolution_checks["authority_resolution_pending_count"]["equals"] == 0
    assert resolution_checks["authority_resolution_report_passed"]["equals"] is True

    risk = results["litigation_risk_summary"]
    assert risk["required_for_current_promotion"] is True
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
        "source-set-f70ea11e04ae3d53"
    )
    assert summary_checks["source_set_graph_node_count"]["min"] == 1
    assert summary_checks["source_set_graph_validation_checks"]["min"] == 62
    assert summary_checks["source_set_graph_region1_ready_profile_count"]["min"] == 10
    assert summary_checks["source_set_graph_region1_blocked_profile_count_matches"]["equals"] == 0

    review_graph = results["nepa_3d_review_graph_validation"]
    assert review_graph["required_for_current_promotion"] is True
    assert review_graph["failure_category"] == "graph_viewer_export_invalid"
    review_graph_checks = {check["name"]: check for check in review_graph["checks"]}
    assert review_graph_checks["review_graph_validation_passed"]["equals"] is True
    assert review_graph_checks["review_graph_no_failure_categories"]["equals"] == {}

    review_graph_summary = results["nepa_3d_review_graph_summary"]
    assert review_graph_summary["required_for_current_promotion"] is True
    review_summary_checks = {
        check["name"]: check for check in review_graph_summary["checks"]
    }
    assert review_summary_checks["review_graph_review_id_matches"]["equals"] == (
        "v1-cg-ecid-compliance-review"
    )
    assert review_summary_checks["review_graph_validation_checks"]["min"] == 76


def test_committed_promotion_suite_defers_packet_local_counts_to_focused_owners() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}
    review_case = {case["id"]: case for case in manifest["review_cases"]}["v1-cg-ecid"]
    results = {result["id"]: result for result in review_case["results"]}

    phase_check_names = {check["name"] for check in suite_results["phase_eval_core"]["checks"]}
    assert {"core_passed_phase_count", "core_reviewer_ready_phase_count"}.isdisjoint(
        phase_check_names
    )

    decision_support_check_names = {
        check["name"] for check in results["decision_support_report"]["checks"]
    }
    assert {
        "decision_support_applicable_authorities",
        "decision_support_non_applicable_authorities",
        "decision_support_forest_plan_components",
        "decision_support_applicable_standards",
    }.isdisjoint(decision_support_check_names)

    final_qa_check_names = {
        check["name"] for check in results["final_qa_certification_report"]["checks"]
    }
    assert {
        "final_qa_finding_count",
        "final_qa_accepted_v1_risk_visible",
    }.isdisjoint(final_qa_check_names)

    review_packet_check_names = {
        check["name"] for check in results["review_packet_row_inventory"]["checks"]
    }
    assert {
        "row_inventory_applicable_authorities",
        "row_inventory_non_applicable_authorities",
        "row_inventory_forest_plan_components",
        "row_inventory_applicable_standards",
    }.isdisjoint(review_packet_check_names)

    render_manifest_check_names = {
        check["name"] for check in results["compliance_matrix_render_manifest"]["checks"]
    }
    assert {
        "render_manifest_authority_rows",
        "render_manifest_forest_plan_rows",
    }.isdisjoint(render_manifest_check_names)

    review_packet_index_check_names = {
        check["name"] for check in results["review_packet_index"]["checks"]
    }
    assert {
        "review_packet_index_applicable_authorities",
        "review_packet_index_non_applicable_authorities",
        "review_packet_index_forest_plan_components",
        "review_packet_index_applicable_standards",
    }.isdisjoint(review_packet_index_check_names)

    review_packet_validation_check_names = {
        check["name"] for check in results["review_packet_index_validation"]["checks"]
    }
    assert {
        "review_packet_index_failed_check_count",
        "review_packet_index_validation_applicable_authorities",
        "review_packet_index_validation_non_applicable_authorities",
        "review_packet_index_validation_forest_plan_components",
        "review_packet_index_validation_applicable_standards",
    }.isdisjoint(review_packet_validation_check_names)

    review_packet_direct_eval = results["review_packet_direct_eval"]
    assert review_packet_direct_eval["required_for_current_promotion"] is True
    assert review_packet_direct_eval["path"] == (
        "reviews/{review_id}/review_packet_index/review_packet_direct_eval_results.json"
    )
    direct_eval_checks = {check["name"]: check for check in review_packet_direct_eval["checks"]}
    assert direct_eval_checks["review_packet_direct_eval_schema"]["equals"] == (
        "review-packet-direct-eval-results-v1"
    )
    assert direct_eval_checks["review_packet_direct_eval_contract"]["equals"] == (
        "review-packet-direct-eval-v1"
    )
    assert direct_eval_checks["review_packet_direct_eval_review_id"]["equals"] == (
        "v1-cg-ecid-compliance-review"
    )
    assert direct_eval_checks["review_packet_direct_eval_source_set"]["equals"] == (
        "source-set-f70ea11e04ae3d53"
    )
    assert direct_eval_checks["review_packet_direct_eval_present"]["equals"] is True
    assert direct_eval_checks["review_packet_direct_eval_passed"]["equals"] is True
    assert direct_eval_checks["review_packet_direct_eval_metric_group_count"]["min"] == 6
    assert direct_eval_checks["review_packet_direct_eval_required_groups_present"]["equals"] == []
    assert direct_eval_checks["review_packet_direct_eval_blocking_gaps"]["equals"] == []
    assert direct_eval_checks["review_packet_direct_eval_failure_intake_empty"]["equals"] == 0

    provenance_check_names = {
        check["name"] for check in results["authority_family_provenance"]["checks"]
    }
    assert "authority_provenance_finding_count" not in provenance_check_names

    review_graph_check_names = {
        check["name"] for check in results["nepa_3d_review_graph_summary"]["checks"]
    }
    assert {
        "review_graph_decision_count",
        "review_graph_generated_rule_count",
        "review_graph_compliance_finding_count",
    }.isdisjoint(review_graph_check_names)

def test_committed_promotion_suite_records_ecid_expansion_artifact_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    review_cases = {case["id"]: case for case in manifest["review_cases"]}
    ecid_case = review_cases["region1-expansion-ecid-preliminary-ea"]
    ecid_results = {result["id"]: result for result in ecid_case["results"]}
    rerouted_result_ids = {
        "compliance_validation",
        "compliance_review",
        "compliance_matrix",
        "compliance_matrix_pdf",
        "authority_family_provenance",
        "non_applicable_authority_appendix",
    }
    still_required_result_ids = {
        "applicability_validation",
        "generated_rule_pack_validation",
        "forest_plan_component_adjudication_template",
        "forest_plan_component_adjudication_eval",
        "phase_eval",
    }

    assert ecid_case["required_for_current_promotion"] is False
    assert ecid_case["review_id"] == "region1-expansion-ecid-preliminary-ea"
    for result in ecid_results.values():
        assert result["required_for_current_promotion"] is False
        assert result["required_for_expansion"] is (
            result["id"] in still_required_result_ids
        )
    assert rerouted_result_ids.isdisjoint(still_required_result_ids)
    assert rerouted_result_ids | still_required_result_ids == set(ecid_results)

    generated = ecid_results["generated_rule_pack_validation"]
    generated_checks = {check["name"]: check for check in generated["checks"]}
    assert generated_checks["generated_rule_pack_validation_passed"]["equals"] is True
    assert generated_checks["generated_rule_count"]["equals"] == 46
    assert generated_checks["source_set_matches"]["equals"] == "source-set-4fb59e9eb43045cb"

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
    assert south_plateau_case["archived_as_example"] is True
    assert south_plateau_case["archive_reason"] == (
        "litigation_forest_plan_compliance_challenge"
    )
    assert south_plateau_case["usage_policy"] == "historical_evidence_only_not_example"
    for result in south_plateau_results.values():
        assert result["required_for_current_promotion"] is False
        assert result["required_for_expansion"] is False

    south_plateau_generated = south_plateau_results["generated_rule_pack_validation"]
    south_plateau_generated_checks = {
        check["name"]: check for check in south_plateau_generated["checks"]
    }
    assert south_plateau_generated_checks["generated_rule_count"]["equals"] == 64
    assert south_plateau_generated_checks["source_set_matches"]["equals"] == (
        "source-set-f70ea11e04ae3d53"
    )

    south_plateau_compliance = south_plateau_results["compliance_review"]
    assert south_plateau_compliance["failure_category"] == "forest_plan_reviewer_not_ready"
    south_plateau_compliance_checks = {
        check["name"]: check for check in south_plateau_compliance["checks"]
    }
    assert south_plateau_compliance_checks["reviewer_ready"]["equals"] is True
    assert south_plateau_compliance_checks["rule_count"]["equals"] == 64
    assert south_plateau_compliance_checks["rule_claim_gap_count"]["equals"] == 1
    assert south_plateau_compliance_checks["rule_claim_link_count"]["equals"] == 308
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
    assert south_plateau_forest_context["required_for_expansion"] is False
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
    assert south_plateau_phase_checks["phase_eval_passed_phase_count"]["equals"] == 27
    assert south_plateau_phase_checks["phase_eval_declared_review_contract"]["equals"] is True
    assert south_plateau_phase_checks["phase_eval_contract_backed_promotion_ready"]["equals"] is True

    slots = {slot["id"]: slot for slot in manifest["expansion_slots"]}
    slot = slots["region1-real-ea-slot-1"]
    ecid_gate_artifacts = {artifact["id"] for artifact in slot["expected_gate_artifacts"]}

    assert slot["status"] == "selected_not_ready"
    assert slot["ready"] is False
    assert slot["failure_category"] == "historical_source_set_split"
    assert slot["review_id"] == "region1-expansion-ecid-preliminary-ea"
    assert slot["source_set_id"] == "source-set-4fb59e9eb43045cb"
    assert "Preliminary Environmental Assessment" in slot["package_path"]
    assert set(ecid_results).issubset(ecid_gate_artifacts)
    assert slot["last_local_signal"]["package_chunk_count"] == 160
    assert slot["last_local_signal"]["candidate_authority_count"] == 392
    assert slot["last_local_signal"]["applicable_authority_count"] == 46
    assert slot["last_local_signal"]["non_applicable_authority_count"] == 346
    assert slot["last_local_signal"]["needs_adjudication_authority_count"] == 0
    assert slot["last_local_signal"]["remaining_adjudication_authority_family_ids"] == []
    assert slot["last_local_signal"]["applicability_validation_passed"] is True
    assert (
        slot["last_local_signal"]["applicability_validation_source_set_id"]
        == "source-set-ba8d0feae79501b8"
    )
    assert slot["last_local_signal"]["generated_rule_pack_ready"] is True
    assert (
        slot["last_local_signal"]["generated_rule_pack_source_set_id"]
        == "source-set-4fb59e9eb43045cb"
    )
    assert slot["last_local_signal"]["rule_claim_link_count"] == 211
    assert slot["last_local_signal"]["rule_claim_gap_count"] == 0
    assert slot["last_local_signal"]["forest_plan_component_reviewer_resolution_count"] == 158
    assert slot["last_local_signal"]["forest_plan_component_adjudication_eval_passed"] is True
    assert slot["last_local_signal"]["forest_plan_component_adjudication_resolved_count"] == 158
    assert (
        slot["last_local_signal"]["forest_plan_component_adjudication_system_miss_count"]
        == 0
    )
    assert slot["last_local_signal"]["phase_eval_source_set_id"] == (
        "source-set-ba8d0feae79501b8"
    )
    assert slot["last_local_signal"]["split_source_set_ids"] == [
        "source-set-ba8d0feae79501b8",
        "source-set-4fb59e9eb43045cb",
    ]
    assert slot["last_local_signal"]["missing_required_artifact_ids"] == [
        "compliance_validation",
        "compliance_review",
        "compliance_matrix",
        "compliance_matrix_pdf",
        "authority_family_provenance",
        "non_applicable_authority_appendix",
    ]
    assert slot["last_local_signal"]["reroute_required"] is True

    assert "region1-real-ea-slot-2" not in slots

    archived_slots = {slot["id"]: slot for slot in manifest["archived_expansion_slots"]}
    third_slot = archived_slots["region1-real-ea-slot-2"]
    gate_artifacts = {artifact["id"] for artifact in third_slot["expected_gate_artifacts"]}

    assert third_slot["status"] == "archived_litigation"
    assert third_slot["ready"] is False
    assert third_slot["failure_category"] == "litigation_forest_plan_compliance_challenge"
    assert third_slot["usage_policy"] == "historical_evidence_only_not_example"
    assert third_slot["active_expansion_slot"] is False
    assert third_slot["review_id"] == "region1-expansion-south-plateau-landscape-treatment"
    assert third_slot["source_set_id"] == "source-set-f70ea11e04ae3d53"
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
    assert third_slot["last_local_signal"]["candidate_authority_count"] == 396
    assert third_slot["last_local_signal"]["applicable_authority_count"] == 64
    assert third_slot["last_local_signal"]["non_applicable_authority_count"] == 332
    assert third_slot["last_local_signal"]["needs_adjudication_authority_count"] == 0
    assert third_slot["last_local_signal"]["unresolved_authority_count"] == 0
    assert third_slot["last_local_signal"]["remaining_adjudication_authority_family_ids"] == []
    assert third_slot["last_local_signal"]["applicability_validation_passed"] is True
    assert third_slot["last_local_signal"]["generated_rule_pack_ready"] is True
    assert third_slot["last_local_signal"]["generated_rule_pack_validation_passed"] is True
    assert third_slot["last_local_signal"]["generated_rule_count"] == 64
    assert third_slot["last_local_signal"]["compliance_validation_passed"] is True
    assert third_slot["last_local_signal"]["compliance_review_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["compliance_finding_count"] == 64
    assert third_slot["last_local_signal"]["rule_claim_link_count"] == 308
    assert third_slot["last_local_signal"]["rule_claim_gap_count"] == 1
    assert third_slot["last_local_signal"]["forest_plan_scope_status"] == "custer_gallatin"
    assert third_slot["last_local_signal"]["forest_plan_context_validation_passed"] is True
    assert third_slot["last_local_signal"]["forest_plan_context_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["forest_plan_component_gate_required"] is True
    assert third_slot["last_local_signal"]["forest_plan_component_count"] == 329
    assert third_slot["last_local_signal"]["forest_plan_component_applicable_count"] == 158
    assert third_slot["last_local_signal"]["forest_plan_component_applicable_standard_count"] == 25
    assert third_slot["last_local_signal"]["forest_plan_component_applied_standard_count"] == 22
    assert third_slot["last_local_signal"]["forest_plan_component_reviewer_resolution_count"] == 34
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_eval_passed"] is True
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_pending_count"] == 0
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_resolved_count"] == 34
    assert third_slot["last_local_signal"]["forest_plan_component_adjudication_system_miss_count"] == 34
    assert third_slot["last_local_signal"]["phase_eval_passed"] is True
    assert third_slot["last_local_signal"]["phase_eval_reviewer_ready"] is True
    assert third_slot["last_local_signal"]["phase_eval_passed_phase_count"] == 27
    assert third_slot["last_local_signal"]["phase_eval_phase_count"] == 27
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
