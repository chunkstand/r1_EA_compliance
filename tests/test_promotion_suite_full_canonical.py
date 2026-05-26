from __future__ import annotations

from pathlib import Path
import json

from tests.support.promotion_suite_fixtures import COMMITTED_PROMOTION_SUITE
from tests.support.promotion_suite_fixtures import FULL_CANONICAL_DOWNLOAD_RUN_ID
from tests.support.promotion_suite_fixtures import FULL_CANONICAL_SOURCE_SET_ID
from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


def test_committed_promotion_suite_tracks_full_canonical_corpus_separately() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}

    assert manifest["source_set_id"] == "source-set-f70ea11e04ae3d53"
    assert manifest["full_canonical_source_set_id"] == FULL_CANONICAL_SOURCE_SET_ID

    active_catalog = suite_results["full_canonical_catalog_manifest"]
    assert active_catalog["required_for_current_promotion"] is False
    assert active_catalog["required_for_full_canonical_corpus"] is True
    assert active_catalog["path"] == (
        "catalog/source_set_manifest.json"
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
    assert active_validation["path"] == "catalog/catalog_validation.json"
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
                    {
                        "id": "full_canonical_extraction_fidelity_eval",
                        "path": "evaluations/extraction_fidelity/extraction_fidelity_eval_results.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "failure_category": "extraction_fidelity_gap",
                        "checks": [
                            {
                                "name": "full_canonical_extraction_fidelity_eval_passed",
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
    assert result.summary["required_full_canonical_result_count"] == 3
    assert result.summary["passed_required_full_canonical_result_count"] == 1
    assert result.summary["full_canonical_failure_category_counts"] == {
        "extraction_fidelity_gap": 1,
        "stale_artifact": 1,
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
    extraction_fidelity_dir = output_dir / "evaluations" / "extraction_fidelity"
    extraction_fidelity_dir.mkdir(parents=True)
    (extraction_fidelity_dir / "extraction_fidelity_eval_results.json").write_text(
        json.dumps(
            {
                "schema_version": "extraction-fidelity-eval-results-v0",
                "passed": True,
                "required_category_count": 12,
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
                    {
                        "id": "full_canonical_extraction_fidelity_eval",
                        "path": "evaluations/extraction_fidelity/extraction_fidelity_eval_results.json",
                        "required_for_current_promotion": False,
                        "required_for_full_canonical_corpus": True,
                        "checks": [
                            {
                                "name": "full_canonical_extraction_fidelity_eval_passed",
                                "json_path": "passed",
                                "equals": True,
                            },
                            {
                                "name": "full_canonical_extraction_fidelity_eval_required_category_count",
                                "json_path": "required_category_count",
                                "equals": 12,
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
    assert result.summary["required_full_canonical_result_count"] == 7
    assert result.summary["passed_required_full_canonical_result_count"] == 7
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
    assert suite_results["full_canonical_extraction_fidelity_eval"]["path"].endswith(
        "evaluations/extraction_fidelity/extraction_fidelity_eval_results.json"
    )
