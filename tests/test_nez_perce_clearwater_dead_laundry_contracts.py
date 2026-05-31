from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-nez-perce-clearwater-dead-laundry-57827"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
EXAMPLE_ID = "npc-dead-laundry-forest-specific"

APPLICABILITY_ADJUDICATION = (
    REPO_ROOT / "config" / "applicability_adjudications" / f"{REVIEW_ID}.json"
)
COMPONENT_ADJUDICATION = (
    REPO_ROOT / "config" / "forest_plan_component_adjudications" / f"{REVIEW_ID}.json"
)
V1_EVAL = REPO_ROOT / "config" / "v1_nez_perce_clearwater_dead_laundry_real_ea_eval.json"
COMPONENT_EVAL = (
    REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
)
REAL_PACKAGE_COVERAGE = REPO_ROOT / "config" / "v1_real_package_review_coverage_v1.json"
EXAMPLE_REGISTRY = (
    REPO_ROOT / "config" / "forest_specific_example_package_registry_v1.json"
)
COMPONENT_COVERAGE = (
    REPO_ROOT / "config" / "forest_plan_component_eval_coverage_v1.json"
)


def test_dead_laundry_applicability_adjudication_is_complete() -> None:
    adjudication = _read_json(APPLICABILITY_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "applicability-adjudication-template-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 2
    assert Counter(item["disposition"] for item in items) == {"human_applicable": 2}
    assert all(item["final_status"] == "applicable" for item in items)
    assert {
        item["candidate_authority_id"].split(":")[-1]
        for item in items
    } == {
        "species_supporting_sources_and_overlays_authority_template",
        "vegetation_wildfire_forest_health_authorities_authority_template",
    }
    assert all(item["supporting_citation_refs"] for item in items)


def test_dead_laundry_component_adjudication_resolves_current_queue() -> None:
    adjudication = _read_json(COMPONENT_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "forest-plan-component-adjudication-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["adjudication"]["status"] == "completed"
    assert adjudication["adjudication"]["method"] == (
        "dead_laundry_package_scope_and_specialist_replay"
    )
    assert adjudication["summary"]["pending_item_count"] == 0
    assert adjudication["summary"]["resolved_item_count"] == 121
    assert adjudication["summary"]["disposition_counts"] == {
        "applicability_false_positive": 53,
        "evidence_linking_miss": 68,
    }
    assert adjudication["summary"]["adjudication_outcome_counts"] == {"system_miss": 121}
    assert adjudication["summary"]["queue_reason_counts"] == {
        "missing_package_evidence": 121
    }
    assert adjudication["summary"]["component_type_counts"] == {
        "desired_condition": 39,
        "goal": 17,
        "guideline": 25,
        "objective": 21,
        "standard": 16,
        "suitability": 3,
    }
    assert len(items) == 121
    assert Counter(item["disposition"] for item in items) == {
        "applicability_false_positive": 53,
        "evidence_linking_miss": 68,
    }
    assert Counter(item["queue_reason"] for item in items) == {
        "missing_package_evidence": 121
    }
    assert Counter(item["component_type"] for item in items) == {
        "desired_condition": 39,
        "goal": 17,
        "guideline": 25,
        "objective": 21,
        "standard": 16,
        "suitability": 3,
    }
    assert all(item["current"]["applicability_status"] == "applicable" for item in items)
    assert all(item["current"]["finding_status"] == "gap" for item in items)
    assert all(item["adjudicated_by"] == ["codex"] for item in items)
    assert all(item["rationale"] for item in items)

    items_by_id = {item["component_id"]: item for item in items}
    assert items_by_id["FPS-347-GA-GL-NHL-01"]["disposition"] == (
        "applicability_false_positive"
    )
    assert items_by_id["FPS-347-MA2-GL-IRA-01"]["disposition"] == (
        "evidence_linking_miss"
    )
    assert items_by_id["FPS-347-FW-DC-MWTR-01"]["disposition"] == (
        "applicability_false_positive"
    )
    assert items_by_id["FPS-347-FW-DC-CARB-01"]["disposition"] == (
        "evidence_linking_miss"
    )


def test_dead_laundry_v1_eval_contract_is_governed_and_reviewer_ready() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["eval_id"] == "nez-perce-clearwater-dead-laundry-real-ea-v1"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["forest_unit_id"] == "nez-perce-clearwater-nfs"
    assert contract["rule_pack_id"] == (
        "generated-nepa-ea-v0-region1-example-nez-perce-clearwater-dead-laundry-57827"
    )
    assert contract["rule_pack_version"] == "applicability-v0"
    assert contract["package_style_tags"] == [
        "narrowed_box_project_package",
        "nez_perce_clearwater_nfs",
        "dead_laundry",
    ]
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
        "passed": True,
    }
    assert (
        len(contract["baseline_policy"]["expected_source_record_ids"]) == 26
    )
    assert len(contract["conditional_source_expectations"]) == 27

    forest_plan = contract["forest_plan"]
    assert forest_plan["expected_scope_status"] == "nez_perce_clearwater_nfs"
    assert forest_plan["expected_overlay_ids"] == [
        "overlay-idaho-roadless-area",
        "overlay-wildland-urban-interface",
    ]
    assert forest_plan["max_reviewer_resolution_items"] == 0
    assert forest_plan["max_standard_reviewer_resolution_items"] == 0
    assert forest_plan["min_applicable_standard_count"] == 21
    assert forest_plan["require_matrix_forest_plan_compliance"] is True
    assert forest_plan["require_reviewer_ready"] is True
    assert forest_plan["required_source_record_ids"] == [
        "R1PLAN-nez-perce-clearwater-nfs-01",
        "R1PLAN-nez-perce-clearwater-nfs-02",
        "FOR-032",
        "FPS-344",
        "FOR-033",
        "FPS-347",
        "FPS-365",
        "FPS-366",
        "FOR-031",
        "FPS-368",
        "FPS-372",
        "FPS-373",
    ]


def test_dead_laundry_component_eval_contract_matches_current_surface() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["eval_id"] == (
        "region1-example-nez-perce-clearwater-dead-laundry-57827-component-eval"
    )
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["coverage_requirements"] == {
        "minimum_cases_by_applicability_status": {"applicable": 134},
        "minimum_cases_by_component_type": {
            "desired_condition": 40,
            "goal": 17,
            "guideline": 25,
            "objective": 21,
            "standard": 21,
            "suitability": 10,
        },
        "require_all_applicable_standards": True,
    }
    assert contract["metric_thresholds"] == {
        "component_applicability_precision": {"min": 1.0},
        "component_applicability_recall": {"min": 1.0},
        "expected_applicable_standard_count": {"min": 21},
        "package_evidence_citation_correctness_rate": {"min": 1.0},
        "plan_source_citation_correctness_rate": {"min": 1.0},
        "reviewer_resolution_state_match_rate": {"min": 1.0},
    }
    assert len(cases) == 134
    assert Counter(case["component_type"] for case in cases) == {
        "desired_condition": 40,
        "goal": 17,
        "guideline": 25,
        "objective": 21,
        "standard": 21,
        "suitability": 10,
    }
    assert Counter(case["applicability_status"] for case in cases) == {"applicable": 134}
    assert sum(1 for case in cases if case["applicable_standard"]) == 21


def test_dead_laundry_promotion_surfaces_are_governed_and_aligned() -> None:
    coverage = _read_json(REAL_PACKAGE_COVERAGE)
    registry = _read_json(EXAMPLE_REGISTRY)
    component_coverage = _read_json(COMPONENT_COVERAGE)

    coverage_slot = next(
        slot for slot in coverage["slots"] if slot["slot_id"] == EXAMPLE_ID
    )
    forest_row = next(
        row
        for row in registry["forest_routing"]
        if row["forest_unit_id"] == "nez-perce-clearwater-nfs"
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
        "forest_unit_id": "nez-perce-clearwater-nfs",
        "label": "Dead Laundry Nez Perce-Clearwater forest-specific reviewer-ready example",
        "package_label": "Dead Laundry Project",
        "coverage_class_id": "forest_specific_reviewer_ready",
        "expected_contract_status": "reviewer_ready",
        "required": True,
        "eval_file": "v1_nez_perce_clearwater_dead_laundry_real_ea_eval.json",
        "package_authority": {
            "replay_context_path": f"replay_contexts/{REVIEW_ID}.json",
            "official_project_page": "https://www.fs.usda.gov/r01/nezperce-clearwater/projects/57827",
            "official_documents_page": "https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225",
        },
    }
    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == EXAMPLE_ID
    assert forest_row["queue_boundary_source_ids"] == ["FOR-034"]
    assert forest_row["shared_contract_ids"] == [
        "forest_plan_profile_eval_coverage_manifest",
        "real_package_review_coverage_manifest",
        "review_packet_index_output_schema",
    ]
    assert "inspect the Dead Laundry package first" in forest_row["guidance_note"]
    assert "FOR-034" in forest_row["guidance_note"]
    assert "source-set-f70ea11e04ae3d53" in forest_row["guidance_note"]
    assert example_row["review_id"] == REVIEW_ID
    assert example_row["forest_unit_id"] == "nez-perce-clearwater-nfs"
    assert example_row["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert example_row["coverage_slot_id"] == EXAMPLE_ID
    assert example_row["expected_contract_status"] == "reviewer_ready"
    assert example_row["eval_file"] == "config/v1_nez_perce_clearwater_dead_laundry_real_ea_eval.json"
    assert example_row["package_authority"] == {
        "replay_context_path": f"config/replay_contexts/{REVIEW_ID}.json",
        "official_project_page": "https://www.fs.usda.gov/r01/nezperce-clearwater/projects/57827",
        "official_documents_page": "https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225",
    }
    assert example_row["queue_lineage_source_ids"] == ["FOR-034"]
    assert component_slot == {
        "slot_id": EXAMPLE_ID,
        "label": "Dead Laundry Nez Perce-Clearwater component eval",
        "review_id": REVIEW_ID,
        "forest_unit_id": "nez-perce-clearwater-nfs",
        "expected_source_set_id": SOURCE_SET_ID,
        "eval_file": f"forest_plan_component_evals/{REVIEW_ID}.json",
        "required": True,
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
