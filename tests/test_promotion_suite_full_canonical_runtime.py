from __future__ import annotations

from pathlib import Path
import json

from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


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

    currentness_dir = output_dir / "derived" / full_source_set_id / "authority_currentness"
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
                        "path": (
                            "derived/{full_canonical_source_set_id}/authority_currentness/"
                            "authority_currentness_report.json"
                        ),
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
                        "path": (
                            "derived/{full_canonical_source_set_id}/knowledge_graph/"
                            "nepa_3d_graph_validation.json"
                        ),
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
                        "path": (
                            "derived/{full_canonical_source_set_id}/knowledge_graph/"
                            "nepa_3d_graph_summary.json"
                        ),
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
                        "path": (
                            "evaluations/extraction_fidelity/"
                            "extraction_fidelity_eval_results.json"
                        ),
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
