from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile

from usfs_r1_ea_sources.applicability_eval import run_applicability_eval
from usfs_r1_ea_sources.phase_eval_direct_eval import load_phase_eval_direct_eval_contract
from usfs_r1_ea_sources.phase_eval_direct_eval import resolve_phase_eval_direct_eval_coverage


FULL_CANONICAL_SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
CURRENT_PROMOTION_SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
NON_FULL_CANONICAL_SOURCE_SET_ID = "source-set-non-full-canonical"
WEST_RESERVOIR_REVIEW_ID = "west-reservoir-67436"
REPO_ROOT = Path(__file__).resolve().parents[1]
APPLICABILITY_EVAL_SEED = REPO_ROOT / "config" / "applicability_eval_seed.json"
APPLICABILITY_RULE_PACK = REPO_ROOT / "config" / "compliance_rule_pack_nepa_ea_v0.json"


def test_committed_phase_eval_direct_eval_contract_tracks_required_phases() -> None:
    contract = load_phase_eval_direct_eval_contract()
    source_set_phases = {
        entry["phase_name"]: entry for entry in contract["source_set_phases"]
    }

    assert contract["schema_version"] == "phase-eval-direct-eval-v1"
    assert contract["contract_id"] == "phase-eval-direct-eval-v1"
    assert contract["component_review_coverage_manifest_path"] == (
        "forest_plan_component_eval_coverage_v1.json"
    )
    assert contract["component_review_coverage_results_path"] == (
        "evaluations/forest_plan_component_eval_coverage/"
        "forest_plan_component_eval_coverage_results.json"
    )
    assert source_set_phases["catalog_capture"]["lane_id"] == "catalog"
    assert source_set_phases["extraction"]["lane_id"] == "extraction"
    assert source_set_phases["extraction"]["producer"] == (
        "extraction_fidelity_evaluation"
    )
    assert source_set_phases["extraction"]["results_path"] == (
        "evaluations/extraction_fidelity/extraction_fidelity_eval_results.json"
    )
    assert source_set_phases["retrieval"]["lane_id"] == "retrieval_eval"
    assert source_set_phases["nepa_3d_source_set_graph"]["lane_id"] == (
        "forest_plan_profile_eval"
    )
    assert source_set_phases["nepa_3d_source_set_graph"]["producer"] == (
        "forest_plan_profile_evaluation"
    )
    assert source_set_phases["nepa_3d_source_set_graph"]["results_path"] == (
        "evaluations/forest_plan_profile/forest_plan_profile_eval_results.json"
    )
    assert source_set_phases["nepa_3d_source_set_graph"]["required_source_set_ids"] == [
        FULL_CANONICAL_SOURCE_SET_ID
    ]
    assert source_set_phases["canonical_semantic_graph"]["lane_id"] == (
        "canonical_semantic_graph"
    )
    assert source_set_phases["canonical_semantic_graph"]["producer"] == (
        "semantic_graph_direct_evaluation"
    )
    assert source_set_phases["canonical_semantic_graph"]["contract_path"] == (
        "semantic_graph_direct_eval_v1.json"
    )
    assert source_set_phases["canonical_semantic_graph"]["results_filename"] == (
        "semantic_graph_eval_results.json"
    )
    assert source_set_phases["canonical_semantic_graph"]["required_source_set_ids"] == [
        FULL_CANONICAL_SOURCE_SET_ID
    ]
    assert source_set_phases["knowledge_graph_query_surface"]["lane_id"] == (
        "knowledge_graph_query_surface"
    )
    assert source_set_phases["knowledge_graph_query_surface"]["producer"] == (
        "knowledge_graph_query_evaluation"
    )
    assert source_set_phases["knowledge_graph_query_surface"]["contract_path"] == (
        "knowledge_graph_query_eval_v1.json"
    )
    assert source_set_phases["knowledge_graph_query_surface"]["results_filename"] == (
        "knowledge_graph_query_eval_results.json"
    )
    assert source_set_phases["knowledge_graph_query_surface"]["required_source_set_ids"] == [
        FULL_CANONICAL_SOURCE_SET_ID
    ]
    assert source_set_phases["forest_plan_component_retrieval"]["lane_id"] == (
        "forest_plan_component_retrieval_eval"
    )
    assert source_set_phases["forest_plan_component_retrieval"]["producer"] == (
        "forest_plan_component_retrieval_evaluation"
    )
    assert source_set_phases["forest_plan_component_retrieval"]["results_path"] == (
        "evaluations/forest_plan_component_retrieval/"
        "forest_plan_component_retrieval_eval_results.json"
    )
    assert source_set_phases["forest_plan_component_retrieval"]["required_source_set_ids"] == [
        FULL_CANONICAL_SOURCE_SET_ID
    ]
    assert source_set_phases["applicability_validation"]["lane_id"] == (
        "applicability_eval"
    )
    assert source_set_phases["applicability_validation"]["producer"] == (
        "applicability_direct_evaluation"
    )
    assert source_set_phases["applicability_validation"]["results_path"] == (
        "reviews/applicability_eval/applicability_eval_results.json"
    )
    assert source_set_phases["applicability_validation"]["required_source_set_ids"] == [
        FULL_CANONICAL_SOURCE_SET_ID
    ]
    assert source_set_phases["applicability_validation"]["required_review_ids"] == [
        WEST_RESERVOIR_REVIEW_ID
    ]
    assert source_set_phases["applicability_validation"]["expected_contract_id"] == (
        "applicability-direct-eval-summary-v1"
    )
    assert source_set_phases["applicability_validation"]["expected_scorer_version"] == (
        "applicability-direct-eval-scorer-v1"
    )
    assert source_set_phases["applicability_validation"][
        "expected_non_blocking_gap_group_ids"
    ] == ["trajectory_process_quality"]
    assert source_set_phases["claim_extraction"]["lane_id"] == "claim_eval"
    assert source_set_phases["rule_claim_binding"]["lane_id"] == "rule_claim_eval"
    assert source_set_phases["evidence_graph"]["coverage_class"] == "validation_only_allowed"
    assert contract["review_scope"]["declared_review_coverage_class"] == (
        "required_for_declared_review_contract"
    )
    assert contract["review_scope"]["ad_hoc_review_coverage_class"] == (
        "not_required_for_ad_hoc_review"
    )


def test_phase_eval_direct_eval_marks_missing_required_summary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    extraction = summary["source_set_phase_statuses"]["extraction"]
    retrieval = summary["source_set_phase_statuses"]["retrieval"]
    graph = summary["source_set_phase_statuses"]["nepa_3d_source_set_graph"]
    component_retrieval = summary["source_set_phase_statuses"]["forest_plan_component_retrieval"]
    semantic_graph = summary["source_set_phase_statuses"]["canonical_semantic_graph"]
    query_surface = summary["source_set_phase_statuses"]["knowledge_graph_query_surface"]

    assert "applicability_validation" not in summary["source_set_phase_statuses"]
    assert extraction["status"] == "direct_eval_missing"
    assert extraction["failure_reasons"] == ["missing_required_direct_eval"]
    assert retrieval["status"] == "direct_eval_missing"
    assert retrieval["failure_reasons"] == ["missing_required_direct_eval"]
    assert graph["status"] == "direct_eval_missing"
    assert graph["failure_reasons"] == ["missing_required_direct_eval"]
    assert semantic_graph["status"] == "direct_eval_missing"
    assert semantic_graph["failure_reasons"] == ["missing_required_direct_eval"]
    assert query_surface["status"] == "direct_eval_missing"
    assert query_surface["failure_reasons"] == ["missing_required_direct_eval"]
    assert component_retrieval["status"] == "direct_eval_missing"
    assert component_retrieval["failure_reasons"] == ["missing_required_direct_eval"]


def test_phase_eval_direct_eval_marks_missing_scoped_applicability_summary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
            review_id=WEST_RESERVOIR_REVIEW_ID,
        )

    applicability = summary["source_set_phase_statuses"]["applicability_validation"]
    assert applicability["status"] == "direct_eval_missing"
    assert applicability["failure_reasons"] == ["missing_required_direct_eval"]
    assert applicability["details"]["expected_source_set_id"] == FULL_CANONICAL_SOURCE_SET_ID


def test_phase_eval_direct_eval_skips_scoped_applicability_for_other_reviews() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
            review_id="other-review",
        )

    assert "applicability_validation" not in summary["source_set_phase_statuses"]


def test_phase_eval_direct_eval_accepts_applicability_eval_for_tracked_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_applicability_eval(output_dir, source_set_id=FULL_CANONICAL_SOURCE_SET_ID)

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
            review_id=WEST_RESERVOIR_REVIEW_ID,
        )

    applicability = summary["source_set_phase_statuses"]["applicability_validation"]
    assert applicability["status"] == "direct_eval_present"
    assert applicability["direct_eval_present"] is True
    assert applicability["direct_eval_passed"] is True
    assert applicability["case_count"] == 10
    assert applicability["hard_negative_case_count"] == 2
    assert applicability["details"]["failure_intake_summary"]["validation_passed"] is True
    assert (
        applicability["details"]["failure_intake_summary"]["replayable_case_count"]
        == 3
    )


def test_phase_eval_direct_eval_rejects_applicability_eval_source_set_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_applicability_eval(output_dir, source_set_id="source-set-other")

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
            review_id=WEST_RESERVOIR_REVIEW_ID,
        )

    applicability = summary["source_set_phase_statuses"]["applicability_validation"]
    assert applicability["status"] == "direct_eval_identity_mismatch"
    assert applicability["failure_reasons"] == ["direct_eval_identity_mismatch"]


def test_phase_eval_direct_eval_rejects_applicability_eval_stale_source_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = _write_applicability_eval(
            output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["source_artifact_hashes"]["eval_file"] = "stale-hash"
        result_path.write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
            review_id=WEST_RESERVOIR_REVIEW_ID,
        )

    applicability = summary["source_set_phase_statuses"]["applicability_validation"]
    assert applicability["status"] == "direct_eval_identity_mismatch"
    assert applicability["failure_reasons"] == ["direct_eval_identity_mismatch"]
    assert applicability["details"]["source_artifact_hash_failures"]


def test_phase_eval_direct_eval_rejects_applicability_eval_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = _write_applicability_eval(
            output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["metric_groups"]["gate_graph_consistency"]["passed"] = False
        result_path.write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
            review_id=WEST_RESERVOIR_REVIEW_ID,
        )

    applicability = summary["source_set_phase_statuses"]["applicability_validation"]
    assert applicability["status"] == "direct_eval_failed"
    assert applicability["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert applicability["threshold_failures"]


def test_phase_eval_direct_eval_rejects_identity_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        contract_path = Path("config/retrieval_eval_seed.json")
        result_path = (
            output_dir
            / "derived"
            / source_set_id
            / "retrieval"
            / "retrieval_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                {
                    "schema_version": "retrieval-eval-results-v0",
                    "eval_id": "retrieval-direct-eval-v1",
                    "source_set_id": "source-set-other",
                    "passed": True,
                    "query_count": 12,
                    "hard_negative_case_count": 3,
                    "metrics": {"case_count": 12},
                    "contract": {
                        "sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest()
                    },
                    "checks": [],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

    retrieval = summary["source_set_phase_statuses"]["retrieval"]
    assert retrieval["status"] == "direct_eval_identity_mismatch"
    assert retrieval["failure_reasons"] == ["direct_eval_identity_mismatch"]


def test_phase_eval_direct_eval_rejects_profile_eval_source_set_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = FULL_CANONICAL_SOURCE_SET_ID
        result_path = (
            output_dir
            / "evaluations"
            / "forest_plan_profile"
            / "forest_plan_profile_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _forest_plan_profile_eval_payload(source_set_id="source-set-other"),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

    graph = summary["source_set_phase_statuses"]["nepa_3d_source_set_graph"]
    assert graph["status"] == "direct_eval_identity_mismatch"
    assert graph["failure_reasons"] == ["direct_eval_identity_mismatch"]


def test_phase_eval_direct_eval_rejects_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = FULL_CANONICAL_SOURCE_SET_ID
        contract_path = Path("config/retrieval_eval_seed.json")
        result_path = (
            output_dir
            / "derived"
            / source_set_id
            / "retrieval"
            / "retrieval_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                {
                    "schema_version": "retrieval-eval-results-v0",
                    "eval_id": "retrieval-direct-eval-v1",
                    "source_set_id": source_set_id,
                    "passed": False,
                    "query_count": 2,
                    "hard_negative_case_count": 0,
                    "metrics": {
                        "case_count": 2,
                        "hard_negative_pass_rate": 0.0,
                        "false_positive_rate": 0.0,
                        "missing_required_source_rate": 0.0,
                        "recall_at_k": 0.5,
                        "mrr": 0.5,
                        "ndcg_at_k": 0.5,
                    },
                    "contract": {
                        "sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest()
                    },
                    "checks": [
                        {
                            "name": "eval_cases_pass",
                            "passed": False,
                            "details": {"case_count": 2, "failed_case_ids": ["case-1"]},
                        },
                        {
                            "name": "metric_thresholds_met",
                            "passed": False,
                            "details": {
                                "failures": [
                                    {
                                        "metric": "case_count",
                                        "min": 12.0,
                                        "actual": 2,
                                    }
                                ]
                            },
                        },
                    ],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

    retrieval = summary["source_set_phase_statuses"]["retrieval"]
    assert retrieval["status"] == "direct_eval_failed"
    assert retrieval["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert retrieval["threshold_failures"]


def test_phase_eval_direct_eval_prefers_existing_rule_claim_eval_results() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        decoy_dir = (
            output_dir
            / "derived"
            / source_set_id
            / "rule_claim_links"
            / "aaa-decoy"
            / "applicability-v0"
        )
        decoy_dir.mkdir(parents=True, exist_ok=True)
        (decoy_dir / "summary.json").write_text("{}", encoding="utf-8")
        live_dir = (
            output_dir
            / "derived"
            / source_set_id
            / "rule_claim_links"
            / "zzz-live"
            / "applicability-v0"
        )
        live_dir.mkdir(parents=True, exist_ok=True)
        (live_dir / "summary.json").write_text("{}", encoding="utf-8")
        (live_dir / "rule_claim_link_eval_results.json").write_text(
            json.dumps(
                {
                    "schema_version": "rule-claim-link-eval-results-v1",
                    "eval_id": "rule-claim-direct-eval-v1",
                    "source_set_id": source_set_id,
                    "passed": False,
                    "case_count": 10,
                    "hard_negative_case_count": 3,
                    "metrics": {
                        "case_count": 10,
                        "hard_negative_case_count": 3,
                    },
                        "contract": {
                            "sha256": hashlib.sha256(
                                (REPO_ROOT / "config" / "rule_claim_link_eval_seed.json").read_bytes()
                            ).hexdigest()
                        },
                    "checks": [
                        {
                            "name": "eval_cases_pass",
                            "passed": False,
                            "details": {"case_count": 10, "failed_case_ids": ["case-1"]},
                        },
                        {
                            "name": "metric_thresholds_met",
                            "passed": False,
                            "details": {"failures": [{"metric": "mrr", "actual": 0.5, "min": 0.9}]},
                        },
                    ],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

    rule_claim = summary["source_set_phase_statuses"]["rule_claim_binding"]
    assert rule_claim["summary_path"].endswith(
        "zzz-live/applicability-v0/rule_claim_link_eval_results.json"
    )
    assert rule_claim["status"] == "direct_eval_failed"
    assert rule_claim["failure_reasons"] == ["direct_eval_threshold_failed"]


def test_phase_eval_direct_eval_rejects_profile_eval_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = FULL_CANONICAL_SOURCE_SET_ID
        result_path = (
            output_dir
            / "evaluations"
            / "forest_plan_profile"
            / "forest_plan_profile_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _forest_plan_profile_eval_payload(
                    source_set_id=source_set_id,
                    passed=False,
                    profile_failure_count=1,
                    profiles_below_floor_ids=["lolo-nf"],
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

    graph = summary["source_set_phase_statuses"]["nepa_3d_source_set_graph"]
    assert graph["status"] == "direct_eval_failed"
    assert graph["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert graph["threshold_failures"]


def test_phase_eval_direct_eval_rejects_component_retrieval_eval_source_set_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "evaluations"
            / "forest_plan_component_retrieval"
            / "forest_plan_component_retrieval_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _forest_plan_component_retrieval_eval_payload(
                    source_set_id="source-set-other",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    component_retrieval = summary["source_set_phase_statuses"]["forest_plan_component_retrieval"]
    assert component_retrieval["status"] == "direct_eval_identity_mismatch"
    assert component_retrieval["failure_reasons"] == ["direct_eval_identity_mismatch"]


def test_phase_eval_direct_eval_rejects_component_retrieval_eval_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "evaluations"
            / "forest_plan_component_retrieval"
            / "forest_plan_component_retrieval_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _forest_plan_component_retrieval_eval_payload(
                    source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
                    passed=False,
                    failed_case_ids=["component-case-1"],
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    component_retrieval = summary["source_set_phase_statuses"]["forest_plan_component_retrieval"]
    assert component_retrieval["status"] == "direct_eval_failed"
    assert component_retrieval["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert component_retrieval["threshold_failures"]


def test_phase_eval_direct_eval_allows_ad_hoc_review_without_contract_owned_review_evals() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id="source-set-test",
            review_id="ad-hoc-review",
            review_dir=Path(tmp) / "reviews" / "ad-hoc-review",
        )

    review_scope = summary["review_scope"]

    assert review_scope["declared_review_contract"] is False
    assert review_scope["status"] == "not_required_for_ad_hoc_review"
    assert review_scope["passed"] is True
    assert review_scope["contract_backed_promotion_ready"] is False


def test_phase_eval_direct_eval_requires_component_review_coverage_for_tracked_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        review_dir = output_dir / "reviews" / "v1-cg-ecid-compliance-review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "v1_ea_eval_results.json").write_text(
            json.dumps(
                _v1_ea_eval_payload(
                    review_id="v1-cg-ecid-compliance-review",
                    source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        coverage_dir = output_dir / "reviews" / "real_package_review_coverage_eval"
        coverage_dir.mkdir(parents=True, exist_ok=True)
        (coverage_dir / "real_package_review_coverage_eval_results.json").write_text(
            json.dumps(
                _real_package_review_coverage_payload(
                    review_id="v1-cg-ecid-compliance-review",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
            review_id="v1-cg-ecid-compliance-review",
            review_dir=review_dir,
        )

    review_scope = summary["review_scope"]
    assert review_scope["status"] == "direct_eval_missing"
    assert review_scope["required_summary_ids"] == [
        "v1_ea_eval",
        "real_package_review_coverage",
        "forest_plan_component_eval_coverage",
    ]
    assert review_scope["missing_summary_ids"] == ["forest_plan_component_eval_coverage"]


def test_phase_eval_direct_eval_accepts_component_review_coverage_for_tracked_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        review_dir = output_dir / "reviews" / "v1-cg-ecid-compliance-review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "v1_ea_eval_results.json").write_text(
            json.dumps(
                _v1_ea_eval_payload(
                    review_id="v1-cg-ecid-compliance-review",
                    source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        coverage_dir = output_dir / "reviews" / "real_package_review_coverage_eval"
        coverage_dir.mkdir(parents=True, exist_ok=True)
        (coverage_dir / "real_package_review_coverage_eval_results.json").write_text(
            json.dumps(
                _real_package_review_coverage_payload(
                    review_id="v1-cg-ecid-compliance-review",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        component_eval_dir = output_dir / "evaluations" / "forest_plan_component_eval_coverage"
        component_eval_dir.mkdir(parents=True, exist_ok=True)
        (
            component_eval_dir / "forest_plan_component_eval_coverage_results.json"
        ).write_text(
            json.dumps(
                _forest_plan_component_eval_coverage_payload(
                    review_id="v1-cg-ecid-compliance-review",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
            review_id="v1-cg-ecid-compliance-review",
            review_dir=review_dir,
        )

    review_scope = summary["review_scope"]
    assert review_scope["status"] == "direct_eval_present"
    assert review_scope["passed"] is True
    assert review_scope["required_summary_ids"] == [
        "v1_ea_eval",
        "real_package_review_coverage",
        "forest_plan_component_eval_coverage",
    ]
    assert review_scope["missing_summary_ids"] == []


def test_phase_eval_direct_eval_accepts_slot_green_when_component_coverage_is_red_for_other_reviews() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        review_dir = output_dir / "reviews" / "v1-cg-ecid-compliance-review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "v1_ea_eval_results.json").write_text(
            json.dumps(
                _v1_ea_eval_payload(
                    review_id="v1-cg-ecid-compliance-review",
                    source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        coverage_dir = output_dir / "reviews" / "real_package_review_coverage_eval"
        coverage_dir.mkdir(parents=True, exist_ok=True)
        (coverage_dir / "real_package_review_coverage_eval_results.json").write_text(
            json.dumps(
                _real_package_review_coverage_payload(
                    review_id="v1-cg-ecid-compliance-review",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        component_eval_dir = output_dir / "evaluations" / "forest_plan_component_eval_coverage"
        component_eval_dir.mkdir(parents=True, exist_ok=True)
        payload = _forest_plan_component_eval_coverage_payload(
            review_id="v1-cg-ecid-compliance-review",
        )
        payload["passed"] = False
        payload["review_component_eval_coverage"]["passed"] = False
        payload["review_component_eval_coverage"]["covered_review_count"] = 1
        (
            component_eval_dir / "forest_plan_component_eval_coverage_results.json"
        ).write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
            review_id="v1-cg-ecid-compliance-review",
            review_dir=review_dir,
        )

    review_scope = summary["review_scope"]
    assert review_scope["status"] == "direct_eval_present"
    assert review_scope["passed"] is True
    component_summary = next(
        item
        for item in review_scope["summaries"]
        if item["summary_id"] == "forest_plan_component_eval_coverage"
    )
    assert component_summary["status"] == "direct_eval_present"
    assert component_summary["passed"] is True


def test_phase_eval_direct_eval_defers_self_phase_gate_failure_for_tracked_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        review_dir = output_dir / "reviews" / "v1-cg-ecid-compliance-review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "v1_ea_eval_results.json").write_text(
            json.dumps(
                _v1_ea_eval_payload(
                    review_id="v1-cg-ecid-compliance-review",
                    source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        coverage_dir = output_dir / "reviews" / "real_package_review_coverage_eval"
        coverage_dir.mkdir(parents=True, exist_ok=True)
        coverage_payload = _real_package_review_coverage_payload(
            review_id="v1-cg-ecid-compliance-review",
        )
        coverage_payload["slots"][0]["passed"] = False
        coverage_payload["slots"][0]["failure_reasons"] = [
            "phase_eval_blockers_present",
            "phase_eval_failed",
            "phase_eval_not_reviewer_ready",
        ]
        (coverage_dir / "real_package_review_coverage_eval_results.json").write_text(
            json.dumps(coverage_payload, sort_keys=True),
            encoding="utf-8",
        )
        component_eval_dir = output_dir / "evaluations" / "forest_plan_component_eval_coverage"
        component_eval_dir.mkdir(parents=True, exist_ok=True)
        (
            component_eval_dir / "forest_plan_component_eval_coverage_results.json"
        ).write_text(
            json.dumps(
                _forest_plan_component_eval_coverage_payload(
                    review_id="v1-cg-ecid-compliance-review",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
            review_id="v1-cg-ecid-compliance-review",
            review_dir=review_dir,
        )

    review_scope = summary["review_scope"]
    assert review_scope["status"] == "direct_eval_present"
    assert review_scope["passed"] is True
    real_package_summary = next(
        item
        for item in review_scope["summaries"]
        if item["summary_id"] == "real_package_review_coverage"
    )
    assert real_package_summary["status"] == "direct_eval_present"
    assert real_package_summary["passed"] is True
    assert real_package_summary["details"]["self_phase_eval_gate_deferred"] is True


def test_phase_eval_direct_eval_rejects_non_self_real_package_slot_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        review_dir = output_dir / "reviews" / "v1-cg-ecid-compliance-review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "v1_ea_eval_results.json").write_text(
            json.dumps(
                _v1_ea_eval_payload(
                    review_id="v1-cg-ecid-compliance-review",
                    source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        coverage_dir = output_dir / "reviews" / "real_package_review_coverage_eval"
        coverage_dir.mkdir(parents=True, exist_ok=True)
        coverage_payload = _real_package_review_coverage_payload(
            review_id="v1-cg-ecid-compliance-review",
        )
        coverage_payload["slots"][0]["passed"] = False
        coverage_payload["slots"][0]["failure_reasons"] = ["package_authority_missing"]
        (coverage_dir / "real_package_review_coverage_eval_results.json").write_text(
            json.dumps(coverage_payload, sort_keys=True),
            encoding="utf-8",
        )
        component_eval_dir = output_dir / "evaluations" / "forest_plan_component_eval_coverage"
        component_eval_dir.mkdir(parents=True, exist_ok=True)
        (
            component_eval_dir / "forest_plan_component_eval_coverage_results.json"
        ).write_text(
            json.dumps(
                _forest_plan_component_eval_coverage_payload(
                    review_id="v1-cg-ecid-compliance-review",
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=CURRENT_PROMOTION_SOURCE_SET_ID,
            review_id="v1-cg-ecid-compliance-review",
            review_dir=review_dir,
        )

    review_scope = summary["review_scope"]
    assert review_scope["status"] == "direct_eval_failed"
    assert review_scope["passed"] is False
    assert review_scope["failure_reasons"] == ["direct_eval_threshold_failed"]


def _write_applicability_eval(output_dir: Path, *, source_set_id: str) -> Path:
    result = run_applicability_eval(
        output_dir=output_dir,
        eval_file=APPLICABILITY_EVAL_SEED,
        base_rule_pack_path=APPLICABILITY_RULE_PACK,
        source_set_id=source_set_id,
    )
    return result.output_path


def _forest_plan_profile_eval_payload(
    *,
    source_set_id: str,
    passed: bool = True,
    profile_failure_count: int = 0,
    profiles_below_floor_ids: list[str] | None = None,
) -> dict:
    return {
        "schema_version": "region1-forest-plan-profile-eval-results-v1",
        "contract_id": "region1-forest-plan-profile-eval-coverage",
        "contract_version": "1.0.0",
        "passed": passed,
        "active_source_set_ids": [source_set_id],
        "expected_active_source_set_ids": [source_set_id],
        "required_profile_count": 10,
        "covered_profile_count": 10,
        "fixture_contract_defined_profile_count": 0,
        "not_started_profile_count": 0,
        "profile_failure_count": profile_failure_count,
        "profiles_below_floor_ids": profiles_below_floor_ids or [],
        "threshold_failures": [],
        "contract_checks": [
            {"name": "active_source_set_binding_matches_manifest", "passed": True}
        ],
        "profiles": [
            {
                "forest_unit_id": "custer-gallatin-nf",
                "hard_negative_case_count": 2,
            }
        ],
    }


def _forest_plan_component_retrieval_eval_payload(
    *,
    source_set_id: str,
    passed: bool = True,
    failed_case_ids: list[str] | None = None,
) -> dict:
    failed_case_ids = failed_case_ids or []
    return {
        "schema_version": "forest-plan-component-retrieval-eval-results-v1",
        "contract_id": "region1-forest-plan-component-retrieval-eval",
        "contract_version": "1",
        "source_set_id": source_set_id,
        "expected_active_source_set_ids": [FULL_CANONICAL_SOURCE_SET_ID],
        "passed": passed,
        "case_count": 6,
        "expected_pass_case_count": 4,
        "hard_negative_case_count": 2,
        "covered_forest_unit_ids": [
            "beaverhead-deerlodge-nf",
            "custer-gallatin-nf",
            "flathead-nf",
        ],
        "required_forest_unit_ids": [
            "beaverhead-deerlodge-nf",
            "custer-gallatin-nf",
            "flathead-nf",
        ],
        "failed_case_ids": failed_case_ids,
        "metrics": {
            "component_retrieval_precision": 1.0,
            "component_retrieval_recall": 1.0,
            "wrong_forest_component_rate": 0.0,
        },
        "contract_checks": [
            {
                "name": "metric_thresholds_met",
                "passed": passed,
            },
            {
                "name": "required_forest_units_covered",
                "passed": True,
            },
        ],
    }


def _v1_ea_eval_payload(
    *,
    review_id: str,
    source_set_id: str,
) -> dict:
    return {
        "summary": {
            "schema_version": "v1-ea-real-review-eval-results-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "contract_status": "reviewer_ready",
            "passed": True,
        },
        "contract": {
            "schema_version": "v1-ea-real-review-eval-contract-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
        },
    }


def _real_package_review_coverage_payload(
    *,
    review_id: str,
) -> dict:
    return {
        "schema_version": "real-package-review-coverage-results-v1",
        "real_package_review_coverage_id": "region1-real-package-review-coverage-v1",
        "slots": [
            {
                "slot_id": "east-crazies-current-promotion",
                "review_id": review_id,
                "actual_review_id": review_id,
                "expected_contract_status": "reviewer_ready",
                "actual_contract_status": "reviewer_ready",
                "passed": True,
            }
        ],
    }


def _forest_plan_component_eval_coverage_payload(
    *,
    review_id: str,
) -> dict:
    return {
        "schema_version": "forest-plan-component-eval-coverage-results-v1",
        "coverage_id": "region1-forest-plan-component-eval-coverage",
        "passed": True,
        "required_review_ids": [
            "v1-cg-ecid-compliance-review",
            "v1-cg-ecid-source-delta-review",
            "west-reservoir-67436",
        ],
        "covered_review_ids": [
            "v1-cg-ecid-compliance-review",
            "v1-cg-ecid-source-delta-review",
            "west-reservoir-67436",
        ],
        "component_retrieval_eval": {
            "passed": True,
            "source_set_id": FULL_CANONICAL_SOURCE_SET_ID,
        },
        "review_component_eval_coverage": {
            "passed": True,
            "required_review_count": 3,
            "covered_review_count": 3,
        },
        "slots": [
            {
                "slot_id": "ecid-current-promotion",
                "review_id": review_id,
                "forest_unit_id": "custer-gallatin-nf",
                "expected_source_set_id": CURRENT_PROMOTION_SOURCE_SET_ID,
                "passed": True,
            }
        ],
    }
