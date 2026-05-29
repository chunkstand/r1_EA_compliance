from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"
SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"

V1_EVAL = REPO_ROOT / "config" / "v1_beaverhead_deerlodge_south_tobacco_roots_real_ea_eval.json"
COMPONENT_EVAL = REPO_ROOT / "config" / "forest_plan_component_evals" / f"{REVIEW_ID}.json"
APPLICABILITY_ADJUDICATION = (
    REPO_ROOT / "config" / "applicability_adjudications" / f"{REVIEW_ID}.json"
)
COMPONENT_ADJUDICATION = (
    REPO_ROOT / "config" / "forest_plan_component_adjudications" / f"{REVIEW_ID}.json"
)
REAL_PACKAGE_COVERAGE = REPO_ROOT / "config" / "v1_real_package_review_coverage_v1.json"
EXAMPLE_REGISTRY = REPO_ROOT / "config" / "forest_specific_example_package_registry_v1.json"
COMPONENT_COVERAGE = REPO_ROOT / "config" / "forest_plan_component_eval_coverage_v1.json"


def test_beaverhead_south_tobacco_v1_eval_contract_is_reviewer_ready_bound() -> None:
    contract = _read_json(V1_EVAL)

    assert contract["schema_version"] == "v1-ea-real-review-eval-contract-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert contract["forest_unit_id"] == "beaverhead-deerlodge-nf"
    assert contract["rule_pack_id"] == f"generated-nepa-ea-v0-{REVIEW_ID}"
    assert contract["rule_pack_version"] == "applicability-v0"
    assert contract["expected_lane_states"] == {
        "broader_ea_passed": True,
        "forest_plan_passed": True,
        "passed": True,
    }
    assert len(contract["conditional_source_expectations"]) == 26
    assert contract["forest_plan"]["require_reviewer_ready"] is True
    assert contract["forest_plan"]["max_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["max_standard_reviewer_resolution_items"] == 0
    assert contract["forest_plan"]["min_applicable_standard_count"] == 89
    assert contract["forest_plan"]["expected_scope_status"] == "beaverhead_deerlodge_nf"
    assert contract["forest_plan"]["expected_geographic_area_ids"] == [
        "geo-gravelly-landscape",
        "geo-tobacco-root-landscape",
    ]
    assert contract["forest_plan"]["expected_management_area_ids"] == [
        "mgmt-basin",
        "mgmt-middle-mountain",
        "mgmt-pintler-face",
    ]
    assert contract["forest_plan"]["expected_overlay_ids"] == [
        "overlay-inventoried-roadless-area",
        "overlay-recommended-wilderness",
    ]
    assert "R1PLAN-beaverhead-deerlodge-nf-02" in contract["forest_plan"][
        "required_source_record_ids"
    ]

    forest_plan_source = _expectation(
        contract,
        "region1_forest_plan_source_records_authority_template",
    )
    assert forest_plan_source["expected_source_record_ids"] == [
        "R1PLAN-beaverhead-deerlodge-nf-02"
    ]
    assert forest_plan_source["expected_source_document_roles"] == ["forest_plan"]


def test_beaverhead_south_tobacco_component_eval_covers_current_component_surface() -> None:
    contract = _read_json(COMPONENT_EVAL)
    cases = contract["cases"]

    assert contract["schema_version"] == "forest-plan-component-eval-v0"
    assert contract["review_id"] == REVIEW_ID
    assert contract["source_set_id"] == SOURCE_SET_ID
    assert len(cases) == 90
    assert contract["coverage_requirements"]["require_all_applicable_standards"] is True
    assert contract["metric_thresholds"]["expected_applicable_standard_count"] == {"min": 89}
    assert all(
        case["component_id"].startswith("R1PLAN-beaverhead-deerlodge-nf-02-")
        for case in cases
    )
    assert Counter(case["component_type"] for case in cases) == {
        "objective": 1,
        "standard": 89,
    }
    assert Counter(case["applicability_status"] for case in cases) == {"applicable": 90}
    assert Counter(case["reviewer_resolution_state"] for case in cases) == {
        "closed": 30,
        "open": 60,
    }
    assert sum(1 for case in cases if case.get("applicable_standard") is True) == 89


def test_beaverhead_south_tobacco_applicability_adjudication_is_complete() -> None:
    adjudication = _read_json(APPLICABILITY_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "applicability-adjudication-template-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 3
    assert Counter(item["disposition"] for item in items) == {"human_applicable": 3}
    assert all(item["final_status"] == "applicable" for item in items)
    assert {
        item["candidate_authority_id"].split(":")[-1]
        for item in items
    } == {
        "clean_air_act_conformity_air_quality_authority_template",
        "species_supporting_sources_and_overlays_authority_template",
        "vegetation_wildfire_forest_health_authorities_authority_template",
    }


def test_beaverhead_south_tobacco_component_adjudication_is_complete() -> None:
    adjudication = _read_json(COMPONENT_ADJUDICATION)
    items = adjudication["items"]

    assert adjudication["schema_version"] == "forest-plan-component-adjudication-v0"
    assert adjudication["review_id"] == REVIEW_ID
    assert adjudication["source_set_id"] == SOURCE_SET_ID
    assert adjudication["adjudication"]["status"] == "completed"
    assert adjudication["adjudication"]["method"] == "south_tobacco_roots_appendix_d_replay"
    assert adjudication["summary"]["pending_item_count"] == 0
    assert len(items) == 60
    assert Counter(item["disposition"] for item in items) == {"evidence_linking_miss": 60}
    assert Counter(item["component_type"] for item in items) == {
        "objective": 1,
        "standard": 59,
    }
    assert all(item["source_type"] == "south_tobacco_roots_appendix_d_replay" for item in items)
    assert all(item["package_evidence_refs"] for item in items)
    assert all(item["plan_source_evidence_refs"] for item in items)
    assert all(item["rationale"] for item in items)
    assert all(item["adjudicated_by"] == ["codex"] for item in items)


def test_beaverhead_south_tobacco_is_promoted_in_registry_and_coverage_manifests() -> None:
    real_package_coverage = _read_json(REAL_PACKAGE_COVERAGE)
    registry = _read_json(EXAMPLE_REGISTRY)
    component_coverage = _read_json(COMPONENT_COVERAGE)
    slot_id = "bdnf-south-tobacco-roots-forest-specific"

    real_package_slot = _by_id(real_package_coverage["slots"], "slot_id", slot_id)
    assert real_package_slot["review_id"] == REVIEW_ID
    assert real_package_slot["forest_unit_id"] == "beaverhead-deerlodge-nf"
    assert real_package_slot["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert real_package_slot["expected_contract_status"] == "reviewer_ready"
    assert real_package_slot["eval_file"] == (
        "v1_beaverhead_deerlodge_south_tobacco_roots_real_ea_eval.json"
    )
    assert real_package_slot["package_authority"] == {
        "replay_context_path": (
            f"replay_contexts/{REVIEW_ID}.json"
        ),
        "official_project_page": "https://www.fs.usda.gov/r01/beaverhead-deerlodge/projects/63754",
        "official_documents_page": "https://usfs-public.app.box.com/v/PinyonPublic/folder/199281418011",
    }

    example = _by_id(registry["review_examples"], "example_id", slot_id)
    assert example["review_id"] == REVIEW_ID
    assert example["coverage_slot_id"] == slot_id
    assert example["forest_unit_id"] == "beaverhead-deerlodge-nf"
    assert example["applicable_forest_unit_ids"] == ["beaverhead-deerlodge-nf"]
    beaverhead_route = _by_id(
        registry["forest_routing"],
        "forest_unit_id",
        "beaverhead-deerlodge-nf",
    )
    assert beaverhead_route["routing_status"] == "real_package_examples_available"
    assert beaverhead_route["primary_example_id"] == slot_id

    component_slot = _by_id(component_coverage["slots"], "slot_id", slot_id)
    assert component_slot["review_id"] == REVIEW_ID
    assert component_slot["forest_unit_id"] == "beaverhead-deerlodge-nf"
    assert component_slot["expected_source_set_id"] == SOURCE_SET_ID
    assert component_slot["eval_file"] == (
        f"forest_plan_component_evals/{REVIEW_ID}.json"
    )
    assert component_slot["required"] is True


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _expectation(contract: dict, rule_id: str) -> dict:
    return next(
        expectation
        for expectation in contract["conditional_source_expectations"]
        if expectation["rule_id"] == rule_id
    )


def _by_id(rows: list[dict], key: str, expected: str) -> dict:
    return next(row for row in rows if row[key] == expected)
