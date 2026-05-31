from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-dakota-prairie-medora-vegetation-management-66886"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
EXAMPLE_ID = "dpg-medora-vegetation-management-forest-specific"

V1_EVAL = REPO_ROOT / "config" / "v1_dakota_prairie_medora_real_ea_eval.json"
COMPONENT_EVAL = (
    REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
)
REAL_PACKAGE_COVERAGE = REPO_ROOT / "config" / "v1_real_package_review_coverage_v1.json"
EXAMPLE_REGISTRY = (
    REPO_ROOT / "config" / "forest_specific_example_package_registry_v1.json"
)
COMPONENT_COVERAGE = REPO_ROOT / "config" / "forest_plan_component_eval_coverage_v1.json"


def test_dakota_medora_v1_eval_contract_is_governed_and_reviewer_ready() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["eval_id"] == "dakota-prairie-medora-real-ea-v1"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["forest_unit_id"] == "dakota-prairie-grasslands"
    assert contract["rule_pack_id"] == f"generated-nepa-ea-v0-{REVIEW_ID}"
    assert contract["rule_pack_version"] == "applicability-v0"
    assert contract["package_style_tags"] == [
        "narrowed_box_project_package",
        "dakota_prairie_grasslands",
        "medora_vegetation_management",
    ]
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
        "passed": True,
    }
    assert len(contract["baseline_policy"]["expected_source_record_ids"]) == 26
    assert len(contract["conditional_source_expectations"]) == 21

    forest_plan = contract["forest_plan"]
    assert forest_plan["expected_scope_status"] == "dakota_prairie_grasslands"
    assert forest_plan["expected_geographic_area_ids"] == [
        "geo-badlands",
        "geo-rolling-prairie",
    ]
    assert forest_plan["expected_management_area_ids"] == [
        "mgmt-dpg-1-2a-suitable-wilderness",
        "mgmt-dpg-1-31-nonmotorized-backcountry",
        "mgmt-dpg-2-1-special-interest",
        "mgmt-dpg-2-2-research-natural",
        "mgmt-dpg-3-51-bighorn-sheep",
        "mgmt-dpg-3-65-diverse-natural-appearing",
        "mgmt-dpg-4-22-river-travel-corridors",
        "mgmt-dpg-4-32-dispersed-recreation-high-use",
        "mgmt-dpg-6-1-broad-resource-emphasis",
    ]
    assert forest_plan["expected_overlay_ids"] == []
    assert forest_plan["max_reviewer_resolution_items"] == 0
    assert forest_plan["max_standard_reviewer_resolution_items"] == 0
    assert forest_plan["min_applicable_standard_count"] == 161
    assert forest_plan["require_matrix_forest_plan_compliance"] is True
    assert forest_plan["require_reviewer_ready"] is True
    assert forest_plan["required_source_record_ids"] == [
        "R1PLAN-dakota-prairie-grasslands-01",
        "R1PLAN-dakota-prairie-grasslands-02",
        "R1PLAN-dakota-prairie-grasslands-03",
        "R1PLAN-dakota-prairie-grasslands-04",
        "R1PLAN-dakota-prairie-grasslands-05",
        "R1PLAN-dakota-prairie-grasslands-06",
        "R1PLAN-dakota-prairie-grasslands-07",
        "R1PLAN-dakota-prairie-grasslands-10",
        "R1PLAN-dakota-prairie-grasslands-12",
        "R1PLAN-dakota-prairie-grasslands-11",
        "R1PLAN-dakota-prairie-grasslands-16",
        "R1PLAN-dakota-prairie-grasslands-15",
    ]


def test_dakota_medora_component_eval_contract_matches_current_surface() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["eval_id"] == f"{REVIEW_ID}-component-eval"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["coverage_requirements"] == {
        "minimum_cases_by_applicability_status": {"applicable": 394},
        "minimum_cases_by_component_type": {
            "goal": 9,
            "guideline": 223,
            "objective": 1,
            "standard": 161,
        },
        "require_all_applicable_standards": True,
    }
    assert contract["metric_thresholds"] == {
        "component_applicability_precision": {"min": 1.0},
        "component_applicability_recall": {"min": 1.0},
        "expected_applicable_standard_count": {"min": 161},
        "package_evidence_citation_correctness_rate": {"min": 1.0},
        "plan_source_citation_correctness_rate": {"min": 1.0},
        "reviewer_resolution_state_match_rate": {"min": 1.0},
    }
    assert len(cases) == 394
    assert Counter(case["component_type"] for case in cases) == {
        "goal": 9,
        "guideline": 223,
        "objective": 1,
        "standard": 161,
    }
    assert Counter(case["applicability_status"] for case in cases) == {
        "applicable": 394
    }
    assert Counter(case["reviewer_resolution_state"] for case in cases) == {
        "closed": 10,
        "open": 384,
    }
    assert sum(1 for case in cases if case["applicable_standard"]) == 161
    assert all(
        case["component_id"].startswith("R1PLAN-dakota-prairie-grasslands-")
        for case in cases
    )


def test_dakota_medora_promotion_surfaces_are_governed_and_aligned() -> None:
    coverage = _read_json(REAL_PACKAGE_COVERAGE)
    registry = _read_json(EXAMPLE_REGISTRY)
    component_coverage = _read_json(COMPONENT_COVERAGE)

    coverage_slot = next(
        slot for slot in coverage["slots"] if slot["slot_id"] == EXAMPLE_ID
    )
    forest_row = next(
        row
        for row in registry["forest_routing"]
        if row["forest_unit_id"] == "dakota-prairie-grasslands"
    )
    example_row = next(
        row for row in registry["review_examples"] if row["example_id"] == EXAMPLE_ID
    )
    component_slot = next(
        slot for slot in component_coverage["slots"] if slot["slot_id"] == EXAMPLE_ID
    )

    assert coverage_slot == {
        "slot_id": EXAMPLE_ID,
        "review_id": REVIEW_ID,
        "forest_unit_id": "dakota-prairie-grasslands",
        "label": (
            "Medora Vegetation Management Dakota Prairie forest-specific "
            "reviewer-ready example"
        ),
        "package_label": "Medora Vegetation Management Project",
        "coverage_class_id": "forest_specific_reviewer_ready",
        "expected_contract_status": "reviewer_ready",
        "required": True,
        "eval_file": "v1_dakota_prairie_medora_real_ea_eval.json",
        "package_authority": {
            "replay_context_path": f"replay_contexts/{REVIEW_ID}.json",
            "official_project_page": "https://www.fs.usda.gov/r01/dpg/projects/66886",
            "official_documents_page": (
                "https://usfs-public.app.box.com/v/PinyonPublic/folder/284408882208"
            ),
        },
    }
    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == EXAMPLE_ID
    assert forest_row["queue_boundary_source_ids"] == []
    assert forest_row["shared_contract_ids"] == [
        "forest_plan_profile_eval_coverage_manifest",
        "real_package_review_coverage_manifest",
        "review_packet_index_output_schema",
    ]
    assert "Use the Medora Vegetation Management package first" in (
        forest_row["guidance_note"]
    )
    assert example_row["coverage_slot_id"] == EXAMPLE_ID
    assert example_row["queue_lineage_source_ids"] == []
    assert example_row["eval_file"] == "config/v1_dakota_prairie_medora_real_ea_eval.json"
    assert component_slot == {
        "slot_id": EXAMPLE_ID,
        "label": "Medora Vegetation Management Dakota Prairie component eval",
        "review_id": REVIEW_ID,
        "forest_unit_id": "dakota-prairie-grasslands",
        "expected_source_set_id": SOURCE_SET_ID,
        "eval_file": f"forest_plan_component_evals/{REVIEW_ID}.json",
        "required": True,
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
