from __future__ import annotations

import json

from tests.support.promotion_suite_fixtures import COMMITTED_PROMOTION_SUITE
from tests.support.promotion_suite_fixtures import FULL_CANONICAL_DOWNLOAD_RUN_ID
from tests.support.promotion_suite_fixtures import FULL_CANONICAL_SOURCE_SET_ID


def test_committed_promotion_suite_tracks_full_canonical_corpus_separately() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}

    assert manifest["source_set_id"] == "source-set-f70ea11e04ae3d53"
    assert manifest["full_canonical_source_set_id"] == FULL_CANONICAL_SOURCE_SET_ID

    active_catalog = suite_results["full_canonical_catalog_manifest"]
    assert active_catalog["required_for_current_promotion"] is False
    assert active_catalog["required_for_full_canonical_corpus"] is True
    assert active_catalog["path"] == (
        "runs/full-canonical-4fb-catalog-archive-20260529/catalog_gate/"
        "source_set_manifest.json"
    )
    active_catalog_checks = {check["name"]: check for check in active_catalog["checks"]}
    assert active_catalog_checks["full_canonical_source_set_matches"]["equals"] == (
        FULL_CANONICAL_SOURCE_SET_ID
    )
    assert active_catalog_checks["full_canonical_download_run_id_matches"]["equals"] == (
        FULL_CANONICAL_DOWNLOAD_RUN_ID
    )
    assert active_catalog_checks["full_canonical_download_batch_run_ids"]["equals"] == []
    assert active_catalog_checks["full_canonical_source_count"]["equals"] == 647
    assert active_catalog_checks["full_canonical_artifact_count"]["equals"] == 635
    assert active_catalog_checks["full_canonical_active_review_corpus_count"]["equals"] == 594
    assert (
        active_catalog_checks["full_canonical_currentness_supersession_archive_count"]["equals"]
        == 53
    )
    assert active_catalog_checks["full_canonical_downloaded_existing_count"]["equals"] == 635
    assert active_catalog_checks["full_canonical_duplicate_content_count"]["equals"] == 12

    active_validation = suite_results["full_canonical_catalog_validation"]
    assert active_validation["required_for_current_promotion"] is False
    assert active_validation["required_for_full_canonical_corpus"] is True
    assert active_validation["path"] == (
        "runs/full-canonical-4fb-catalog-archive-20260529/catalog_gate/"
        "catalog_validation.json"
    )
    active_validation_checks = {
        check["name"]: check for check in active_validation["checks"]
    }
    assert active_validation_checks["full_canonical_catalog_validation_passed"]["equals"] is True
    assert active_validation_checks["full_canonical_catalog_validation_source_set"]["equals"] == (
        FULL_CANONICAL_SOURCE_SET_ID
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
        FULL_CANONICAL_SOURCE_SET_ID
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
        == 594
    )
    assert (
        currentness_checks[
            "full_canonical_authority_currentness_currentness_supersession_archive_count"
        ]["equals"]
        == 53
    )
    assert (
        currentness_checks["full_canonical_authority_currentness_archive_only_count"]["equals"]
        == 47
    )
    assert (
        currentness_checks["full_canonical_authority_currentness_replacement_source_count"][
            "equals"
        ]
        == 6
    )
    assert (
        currentness_checks[
            "full_canonical_authority_currentness_current_authority_source_count"
        ]["equals"]
        == 594
    )

    full_canonical_verified_admission = suite_results[
        "full_canonical_verified_admission_boundary"
    ]
    assert full_canonical_verified_admission["required_for_current_promotion"] is False
    assert full_canonical_verified_admission["required_for_full_canonical_corpus"] is True
    assert (
        full_canonical_verified_admission["path"]
        == "derived/{full_canonical_source_set_id}/retrieval/summary.json"
    )
    verified_admission_checks = {
        check["name"]: check for check in full_canonical_verified_admission["checks"]
    }
    assert (
        verified_admission_checks["full_canonical_verified_admission_boundary_source_set"][
            "equals"
        ]
        == FULL_CANONICAL_SOURCE_SET_ID
    )
    assert (
        verified_admission_checks["full_canonical_verified_admission_boundary_contract_ids"][
            "equals"
        ]
        == ["canonical-source-register-active-current-admission"]
    )
    assert (
        verified_admission_checks["full_canonical_verified_admission_required_source_count"][
            "equals"
        ]
        == 594
    )
    assert (
        verified_admission_checks["full_canonical_verified_admission_admitted_source_count"][
            "equals"
        ]
        == 594
    )
    assert (
        verified_admission_checks[
            "full_canonical_verified_admission_explicitly_non_admitted_source_count"
        ]["equals"]
        == 53
    )
    assert (
        verified_admission_checks["full_canonical_verified_admission_validation_passed"][
            "equals"
        ]
        is True
    )
    assert (
        verified_admission_checks["full_canonical_verified_admission_reviewer_ready"][
            "equals"
        ]
        is True
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
        == FULL_CANONICAL_SOURCE_SET_ID
    )
    assert (
        full_graph_summary_checks[
            "full_canonical_source_set_graph_catalog_source_record_count"
        ]["equals"]
        == 647
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
        == [FULL_CANONICAL_SOURCE_SET_ID]
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
        == FULL_CANONICAL_SOURCE_SET_ID
    )
    assert (
        full_component_retrieval_checks[
            "full_canonical_forest_plan_component_retrieval_eval_active_source_set_matches"
        ]["equals"]
        == [FULL_CANONICAL_SOURCE_SET_ID]
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
        == 4
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_covered_review_count"
        ]["equals"]
        == 4
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_required_review_ids"
        ]["contains_all"]
        == [
            "v1-cg-ecid-compliance-review",
            "v1-cg-ecid-source-delta-review",
            "west-reservoir-67436",
            "region1-example-lolo-tylers-kitchen-66344",
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
            "region1-example-lolo-tylers-kitchen-66344",
        ]
    )
    assert (
        full_component_coverage_checks[
            "full_canonical_forest_plan_component_eval_coverage_distinct_forest_count"
        ]["min"]
        == 3
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

    full_extraction_fidelity = suite_results["full_canonical_extraction_fidelity_eval"]
    assert full_extraction_fidelity["required_for_current_promotion"] is False
    assert full_extraction_fidelity["required_for_full_canonical_corpus"] is True
    assert (
        full_extraction_fidelity["path"]
        == "evaluations/extraction_fidelity/extraction_fidelity_eval_results.json"
    )
    full_extraction_fidelity_checks = {
        check["name"]: check for check in full_extraction_fidelity["checks"]
    }
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_schema"
        ]["equals"]
        == "extraction-fidelity-eval-results-v0"
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_passed"
        ]["equals"]
        is True
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_required_category_count"
        ]["equals"]
        == 12
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_case_count"
        ]["equals"]
        == 24
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_matched_case_count"
        ]["equals"]
        == 24
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_parser_route_mismatch_count"
        ]["equals"]
        == 1
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_anchor_mismatch_count"
        ]["equals"]
        == 13
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_span_mismatch_count"
        ]["equals"]
        == 10
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_boundary_mismatch_count"
        ]["equals"]
        == 4
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_negative_case_pass_count"
        ]["equals"]
        == 12
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_negative_case_fail_count"
        ]["equals"]
        == 0
    )
    assert (
        full_extraction_fidelity_checks[
            "full_canonical_extraction_fidelity_eval_required_check_mismatch_count"
        ]["equals"]
        == 0
    )
