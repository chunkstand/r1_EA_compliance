from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-idaho-panhandle-lacy-lemoosh-60853"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"

V1_EVAL = REPO_ROOT / "config" / "v1_idaho_panhandle_lacy_lemoosh_real_ea_eval.json"
COMPONENT_EVAL = REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
APPLICABILITY_ADJUDICATION = (
    REPO_ROOT / "config" / "applicability_adjudications" / f"{REVIEW_ID}.json"
)


def test_lacy_v1_eval_contract_is_reviewer_ready_bound() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["forest_unit_id"] == "idaho-panhandle-nfs"
    assert contract["rule_pack_id"] == f"generated-nepa-ea-v0-{REVIEW_ID}"
    assert contract["rule_pack_version"] == "applicability-v0"
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
        "passed": True,
    }
    assert len(contract["baseline_policy"]["expected_source_record_ids"]) == 26
    assert len(contract["conditional_source_expectations"]) == 30
    assert contract["forest_plan"]["require_reviewer_ready"] is True
    assert contract["forest_plan"]["max_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["max_standard_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["min_applicable_standard_count"] == 8
    assert contract["forest_plan"]["expected_scope_status"] == "idaho_panhandle_nfs"
    assert contract["forest_plan"]["expected_geographic_area_ids"] == ["geo-st-joe"]
    assert contract["forest_plan"]["expected_management_area_ids"] == [
        "mgmt-ma6-general-forest"
    ]
    assert contract["forest_plan"]["expected_overlay_ids"] == [
        "overlay-riparian-habitat-conservation-area",
        "overlay-wildland-urban-interface",
    ]
    assert contract["forest_plan"]["required_source_record_ids"] == [
        "R1PLAN-idaho-panhandle-nfs-01",
        "FOR-021",
        "FPS-223",
        "R1PLAN-idaho-panhandle-nfs-04",
        "R1PLAN-idaho-panhandle-nfs-05",
        "FPS-238",
        "FPS-240",
        "FPS-256",
        "FPS-257",
        "FPS-232",
        "FPS-233",
        "FPS-234",
        "FPS-235",
        "FPS-236",
    ]


def test_lacy_component_eval_covers_current_raw_component_surface() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert len(cases) == 52
    assert contract["coverage_requirements"]["require_all_applicable_standards"] is True
    assert contract["metric_thresholds"]["expected_applicable_standard_count"] == {"min": 8}
    assert all(
        case["component_id"].startswith("R1PLAN-idaho-panhandle-nfs-02-")
        for case in cases
    )
    assert Counter(case["component_type"] for case in cases) == {
        "desired_condition": 18,
        "guideline": 12,
        "objective": 14,
        "standard": 8,
    }
    assert Counter(case["applicability_status"] for case in cases) == {"applicable": 52}
    assert Counter(case["reviewer_resolution_state"] for case in cases) == {
        "closed": 16,
        "open": 36,
    }
    assert Counter(case["compliance_status"] for case in cases) == {
        "complies": 3,
        "insufficient_evidence": 5,
        "not_evaluated_for_compliance": 44,
    }
    assert sum(1 for case in cases if case.get("applicable_standard") is True) == 8


def test_lacy_applicability_adjudication_is_complete() -> None:
    adjudication = _read_json(APPLICABILITY_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "applicability-adjudication-template-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 9
    assert Counter(item["disposition"] for item in items) == {
        "human_applicable": 7,
        "human_not_applicable": 2,
    }
    assert Counter(item["final_status"] for item in items) == {
        "applicable": 7,
        "not_applicable": 2,
    }
    not_applicable_ids = {
        item["candidate_authority_id"].split(":")[-1]
        for item in items
        if item["final_status"] == "not_applicable"
    }
    assert not_applicable_ids == {
        "FOR-021-FW-GDL-WL-01",
        "minerals_energy_authorities_authority_template",
    }
    assert all(item["supporting_citation_refs"] for item in items)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
