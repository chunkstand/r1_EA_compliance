from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile

from usfs_r1_ea_sources.phase_eval_direct_eval import load_phase_eval_direct_eval_contract
from usfs_r1_ea_sources.phase_eval_direct_eval import resolve_phase_eval_direct_eval_coverage


def test_committed_phase_eval_direct_eval_contract_tracks_required_phases() -> None:
    contract = load_phase_eval_direct_eval_contract()
    source_set_phases = {
        entry["phase_name"]: entry for entry in contract["source_set_phases"]
    }

    assert contract["schema_version"] == "phase-eval-direct-eval-v1"
    assert contract["contract_id"] == "phase-eval-direct-eval-v1"
    assert source_set_phases["catalog_capture"]["lane_id"] == "catalog"
    assert source_set_phases["extraction"]["lane_id"] == "extraction"
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
            source_set_id="source-set-test",
        )

    retrieval = summary["source_set_phase_statuses"]["retrieval"]
    graph = summary["source_set_phase_statuses"]["nepa_3d_source_set_graph"]

    assert retrieval["status"] == "direct_eval_missing"
    assert retrieval["failure_reasons"] == ["missing_required_direct_eval"]
    assert graph["status"] == "direct_eval_missing"
    assert graph["failure_reasons"] == ["missing_required_direct_eval"]


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
        source_set_id = "source-set-test"
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


def test_phase_eval_direct_eval_rejects_profile_eval_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
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
