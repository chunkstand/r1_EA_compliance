from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-bitterroot-front-57341"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"

V1_EVAL = REPO_ROOT / "config" / "v1_bitterroot_front_real_ea_eval.json"
COMPONENT_EVAL = REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
APPLICABILITY_ADJUDICATION = (
    REPO_ROOT / "config" / "applicability_adjudications" / f"{REVIEW_ID}.json"
)
COMPONENT_ADJUDICATION = (
    REPO_ROOT / "config" / "forest_plan_component_adjudications" / f"{REVIEW_ID}.json"
)


def test_bitterroot_v1_eval_contract_is_reviewer_ready_bound() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["forest_unit_id"] == "bitterroot-nf"
    assert contract["rule_pack_id"] == f"generated-nepa-ea-v0-{REVIEW_ID}"
    assert contract["rule_pack_version"] == "applicability-v0"
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
        "passed": True,
    }
    assert len(contract["conditional_source_expectations"]) == 28
    assert contract["forest_plan"]["require_reviewer_ready"] is True
    assert contract["forest_plan"]["max_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["max_standard_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["min_applicable_standard_count"] == 3
    assert contract["forest_plan"]["required_source_record_ids"] == [
        "R1PLAN-bitterroot-nf-01",
        "R1PLAN-bitterroot-nf-02",
        "R1PLAN-bitterroot-nf-03",
        "R1PLAN-bitterroot-nf-04",
        "R1PLAN-bitterroot-nf-05",
        "R1PLAN-bitterroot-nf-06",
        "R1PLAN-bitterroot-nf-12",
        "R1PLAN-bitterroot-nf-13",
    ]


def test_bitterroot_component_eval_covers_current_raw_component_surface() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert len(cases) == 23
    assert contract["coverage_requirements"]["require_all_applicable_standards"] is True
    assert contract["metric_thresholds"]["expected_applicable_standard_count"] == {"min": 3}
    assert all(
        case["component_id"].startswith("R1PLAN-bitterroot-nf-") for case in cases
    )
    assert Counter(case["component_type"] for case in cases) == {
        "desired_condition": 4,
        "goal": 6,
        "guideline": 4,
        "objective": 6,
        "standard": 3,
    }
    assert Counter(case["applicability_status"] for case in cases) == {"applicable": 23}
    assert Counter(case["reviewer_resolution_state"] for case in cases) == {
        "closed": 3,
        "open": 20,
    }
    assert sum(1 for case in cases if case.get("applicable_standard") is True) == 3


def test_bitterroot_applicability_adjudication_is_complete() -> None:
    adjudication = _read_json(APPLICABILITY_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "applicability-adjudication-template-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 6
    assert Counter(item["disposition"] for item in items) == {
        "human_applicable": 5,
        "human_not_applicable": 1,
    }
    assert all(item["final_status"] in {"applicable", "not_applicable"} for item in items)


def test_bitterroot_component_adjudication_is_complete() -> None:
    adjudication = _read_json(COMPONENT_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "forest-plan-component-adjudication-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["adjudication"]["status"] == "completed"
    assert adjudication["adjudication"]["method"] == "bitterroot_front_forest_plan_consistency_replay"
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 20
    assert Counter(item["disposition"] for item in items) == {
        "applicability_false_positive": 12,
        "evidence_linking_miss": 8,
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
