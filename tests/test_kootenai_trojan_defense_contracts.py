from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-kootenai-trojan-defense-64354"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
EXAMPLE_ID = "knf-trojan-defense-forest-specific"

V1_EVAL = REPO_ROOT / "config" / "v1_kootenai_trojan_defense_real_ea_eval.json"
COMPONENT_EVAL = REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
APPLICABILITY_ADJUDICATION = (
    REPO_ROOT / "config" / "applicability_adjudications" / f"{REVIEW_ID}.json"
)
COMPONENT_ADJUDICATION = (
    REPO_ROOT / "config" / "forest_plan_component_adjudications" / f"{REVIEW_ID}.json"
)
REPLAY_CONTEXT = REPO_ROOT / "config" / "replay_contexts" / f"{REVIEW_ID}.json"
REAL_PACKAGE_COVERAGE = REPO_ROOT / "config" / "v1_real_package_review_coverage_v1.json"
COMPONENT_COVERAGE = REPO_ROOT / "config" / "forest_plan_component_eval_coverage_v1.json"
EXAMPLE_REGISTRY = (
    REPO_ROOT / "config" / "forest_specific_example_package_registry_v1.json"
)


def test_kootenai_v1_eval_contract_is_reviewer_ready_bound() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["eval_id"] == "kootenai-trojan-defense-real-ea-v1"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["forest_unit_id"] == "kootenai-nf"
    assert contract["rule_pack_id"] == f"generated-nepa-ea-v0-{REVIEW_ID}"
    assert contract["rule_pack_version"] == "applicability-v0"
    assert contract["package_style_tags"] == [
        "narrowed_box_project_package",
        "kootenai_nf",
        "trojan_defense_hazardous_fuels",
    ]
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
        "passed": True,
    }
    assert len(contract["baseline_policy"]["expected_source_record_ids"]) == 26
    assert len(contract["conditional_source_expectations"]) == 21

    forest_plan = contract["forest_plan"]
    assert forest_plan["expected_scope_status"] == "kootenai_nf"
    assert forest_plan["expected_geographic_area_ids"] == ["geo-bull"]
    assert forest_plan["expected_management_area_ids"] == [
        "mgmt-ma2-eligible-wild-scenic-rivers",
        "mgmt-ma3-special-areas",
        "mgmt-ma6-general-forest",
    ]
    assert forest_plan["expected_overlay_ids"] == [
        "overlay-riparian-habitat-conservation-area",
        "overlay-wildland-urban-interface",
    ]
    assert forest_plan["max_reviewer_resolution_items"] == 0
    assert forest_plan["max_standard_reviewer_resolution_items"] == 0
    assert forest_plan["min_applicable_standard_count"] == 8
    assert forest_plan["require_matrix_forest_plan_compliance"] is True
    assert forest_plan["require_reviewer_ready"] is True
    assert forest_plan["required_source_record_ids"] == [
        "R1PLAN-kootenai-nf-01",
        "R1PLAN-kootenai-nf-02",
        "R1PLAN-kootenai-nf-03",
        "R1PLAN-kootenai-nf-04",
        "R1PLAN-kootenai-nf-05",
        "R1PLAN-kootenai-nf-13",
        "R1PLAN-kootenai-nf-14",
        "R1PLAN-kootenai-nf-15",
        "R1PLAN-kootenai-nf-16",
        "R1PLAN-kootenai-nf-17",
    ]


def test_kootenai_component_eval_covers_current_raw_component_surface() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["eval_id"] == f"{REVIEW_ID}-component-eval"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert len(cases) == 53
    assert contract["coverage_requirements"] == {
        "minimum_cases_by_applicability_status": {"applicable": 53},
        "minimum_cases_by_component_type": {
            "desired_condition": 18,
            "guideline": 12,
            "objective": 15,
            "standard": 8,
        },
        "require_all_applicable_standards": True,
    }
    assert contract["metric_thresholds"]["expected_applicable_standard_count"] == {"min": 8}
    assert all(
        case["component_id"].startswith("R1PLAN-kootenai-nf-02-")
        for case in cases
    )
    assert Counter(case["component_type"] for case in cases) == {
        "desired_condition": 18,
        "guideline": 12,
        "objective": 15,
        "standard": 8,
    }
    assert Counter(case["applicability_status"] for case in cases) == {"applicable": 53}
    assert Counter(case["reviewer_resolution_state"] for case in cases) == {
        "closed": 19,
        "open": 34,
    }
    assert Counter(case["compliance_status"] for case in cases) == {
        "complies": 3,
        "insufficient_evidence": 5,
        "not_evaluated_for_compliance": 45,
    }
    assert sum(1 for case in cases if case.get("applicable_standard") is True) == 8


def test_kootenai_adjudications_are_complete_and_resolve_as_system_misses() -> None:
    applicability = _read_json(APPLICABILITY_ADJUDICATION)
    component = _read_json(COMPONENT_ADJUDICATION)

    assert applicability["review_id"] == REVIEW_ID
    assert applicability["source_set_id"] == SOURCE_SET_ID
    assert applicability["summary"]["pending_item_count"] == 0
    assert len(applicability["items"]) == 6
    assert Counter(item["disposition"] for item in applicability["items"]) == {
        "human_applicable": 6,
    }
    assert Counter(item["final_status"] for item in applicability["items"]) == {
        "applicable": 6,
    }

    assert component["review_id"] == REVIEW_ID
    assert component["source_set_id"] == SOURCE_SET_ID
    assert component["summary"]["pending_item_count"] == 0
    assert len(component["items"]) == 34
    assert component["summary"]["adjudication_outcome_counts"] == {"system_miss": 34}
    assert Counter(item["disposition"] for item in component["items"]) == {
        "applicability_false_positive": 7,
        "component_inventory_overreach": 1,
        "evidence_linking_miss": 26,
    }


def test_kootenai_promotion_surfaces_are_governed_and_aligned() -> None:
    real_package = _read_json(REAL_PACKAGE_COVERAGE)
    component_coverage = _read_json(COMPONENT_COVERAGE)
    registry = _read_json(EXAMPLE_REGISTRY)
    replay_context = _read_json(REPLAY_CONTEXT)

    real_slot = next(slot for slot in real_package["slots"] if slot["slot_id"] == EXAMPLE_ID)
    component_slot = next(
        slot for slot in component_coverage["slots"] if slot["slot_id"] == EXAMPLE_ID
    )
    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "kootenai-nf"
    )
    example_row = next(
        row for row in registry["review_examples"] if row["example_id"] == EXAMPLE_ID
    )

    assert real_slot["review_id"] == REVIEW_ID
    assert real_slot["forest_unit_id"] == "kootenai-nf"
    assert real_slot["expected_contract_status"] == "reviewer_ready"
    assert real_slot["required"] is True
    assert component_slot["review_id"] == REVIEW_ID
    assert component_slot["expected_source_set_id"] == SOURCE_SET_ID
    assert component_slot["required"] is True
    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == EXAMPLE_ID
    assert forest_row["queue_boundary_source_ids"] == []
    assert example_row["queue_lineage_source_ids"] == []
    assert example_row["coverage_slot_id"] == EXAMPLE_ID
    assert replay_context == {
        "review_id": REVIEW_ID,
        "source_set_id": SOURCE_SET_ID,
        "forest_unit_id": "kootenai-nf",
        "catalog_dir": "source_library/catalog",
        "package_path": f"source_library/reviews/_intake/{REVIEW_ID}",
        "package_authority": {
            "official_project_page": "https://www.fs.usda.gov/r01/kootenai/projects/64354",
            "official_documents_page": (
                "https://usfs-public.app.box.com/v/PinyonPublic/folder/214150735755"
            ),
            "box_inventory_path": (
                f"source_library/reviews/_intake/{REVIEW_ID}/box_inventory.json"
            ),
            "box_import_manifest_path": (
                f"source_library/reviews/_intake/{REVIEW_ID}/box_import_manifest.json"
            ),
        },
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
