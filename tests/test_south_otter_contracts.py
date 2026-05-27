from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-custer-gallatin-south-otter-58396"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"

V1_EVAL = REPO_ROOT / "config" / "v1_custer_gallatin_south_otter_real_ea_eval.json"
COMPONENT_EVAL = (
    REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
)
APPLICABILITY_ADJUDICATION = (
    REPO_ROOT / "config" / "applicability_adjudications" / f"{REVIEW_ID}.json"
)
COMPONENT_ADJUDICATION = (
    REPO_ROOT / "config" / "forest_plan_component_adjudications" / f"{REVIEW_ID}.json"
)


def test_south_otter_v1_eval_contract_is_reviewer_ready_bound() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert (
        contract["rule_pack_id"]
        == "generated-nepa-ea-v0-region1-example-custer-gallatin-south-otter-58396"
    )
    assert contract["forest_unit_id"] == "custer-gallatin-nf"
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
    }
    assert len(contract["conditional_source_expectations"]) == 35
    planning_handbook = _expectation(
        contract,
        "forest_service_planning_handbook_amendments_authority_template",
    )
    assert planning_handbook["expected_source_record_ids"] == ["USFS-008"]
    assert planning_handbook["expected_source_document_roles"] == ["agency_policy"]
    assert contract["forest_plan"]["require_reviewer_ready"] is True
    assert contract["forest_plan"]["max_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["max_standard_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["required_source_record_ids"] == [
        "R1PLAN-custer-gallatin-nf-01",
        "R1PLAN-custer-gallatin-nf-02",
        "R1PLAN-custer-gallatin-nf-03",
        "R1PLAN-custer-gallatin-nf-04",
        "R1PLAN-custer-gallatin-nf-05",
        "R1PLAN-custer-gallatin-nf-06",
        "R1PLAN-custer-gallatin-nf-07",
    ]


def test_south_otter_component_eval_covers_raw_queue_and_standards() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert len(cases) == 56
    assert contract["coverage_requirements"]["require_all_applicable_standards"] is True
    assert contract["metric_thresholds"]["expected_applicable_standard_count"] == {"min": 43}
    assert all(
        case["component_id"].startswith("R1PLAN-custer-gallatin-nf-02-")
        for case in cases
    )
    assert sum(1 for case in cases if case.get("applicable_standard") is True) == 43
    assert Counter(case["applicability_status"] for case in cases) == {
        "applicable": 48,
        "needs_reviewer_resolution": 5,
        "not_applicable": 3,
    }
    assert {
        case["component_id"]
        for case in cases
        if case["applicability_status"] == "needs_reviewer_resolution"
    } == {
        "R1PLAN-custer-gallatin-nf-02-FW-STD-AIRFIELDS-01",
        "R1PLAN-custer-gallatin-nf-02-FW-STD-SOIL-01",
        "R1PLAN-custer-gallatin-nf-02-FW-STD-WLBAT-01",
        "R1PLAN-custer-gallatin-nf-02-FW-STD-WLGB-01",
        "R1PLAN-custer-gallatin-nf-02-FW-STD-WLPD-01",
    }


def test_south_otter_applicability_adjudication_is_complete() -> None:
    adjudication = _read_json(APPLICABILITY_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "applicability-adjudication-template-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 8
    assert Counter(item["disposition"] for item in items) == {
        "human_applicable": 6,
        "human_not_applicable": 2,
    }
    assert all(item["final_status"] in {"applicable", "not_applicable"} for item in items)


def test_south_otter_component_adjudication_is_complete() -> None:
    adjudication = _read_json(COMPONENT_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "forest-plan-component-adjudication-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["adjudication"]["status"] == "completed"
    assert adjudication["adjudication"]["method"] == "forest_plan_consistency_checklist_replay"
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 169
    assert Counter(item["disposition"] for item in items) == {
        "applicability_false_positive": 132,
        "evidence_linking_miss": 37,
    }
    assert all(item["source_type"] == "forest_plan_consistency_checklist_replay" for item in items)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _expectation(contract: dict, rule_id: str) -> dict:
    return next(
        expectation
        for expectation in contract["conditional_source_expectations"]
        if expectation["rule_id"] == rule_id
    )
