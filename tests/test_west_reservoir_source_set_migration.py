from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ID = "west-reservoir-67436"
CURRENT_SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
CURRENT_CATALOG_DIR = "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"
REVIEWER_READY_SLOT_ID = "flathead-west-reservoir-forest-specific"
REVIEWER_READY_EXAMPLE_ID = "flathead-west-reservoir-forest-specific"


def test_west_reservoir_source_set_contract_surfaces_have_single_identity() -> None:
    source_sets = _west_reservoir_source_set_contracts(REPO_ROOT)

    assert source_sets == {
        "component_coverage_slot.expected_source_set_id": CURRENT_SOURCE_SET_ID,
        "component_eval_contract.source_set_id": CURRENT_SOURCE_SET_ID,
        "replay_context.source_set_id": CURRENT_SOURCE_SET_ID,
        "v1_eval_contract.source_set_id": CURRENT_SOURCE_SET_ID,
    }
    assert _source_set_mismatches(source_sets) == {}


def test_west_reservoir_source_set_contract_gate_flags_mixed_source_sets() -> None:
    source_sets = _west_reservoir_source_set_contracts(REPO_ROOT)
    source_sets["component_coverage_slot.expected_source_set_id"] = "source-set-stale"

    assert _source_set_mismatches(source_sets) == {
        "component_coverage_slot.expected_source_set_id": "source-set-stale"
    }


def test_west_reservoir_replay_context_uses_selected_catalog_surface() -> None:
    replay_context = _load_json(REPO_ROOT / "config/replay_contexts/west-reservoir-67436.json")

    assert replay_context["catalog_dir"] == CURRENT_CATALOG_DIR


def test_west_reservoir_migration_promotes_reviewer_ready_status() -> None:
    real_package_slot = _west_reservoir_real_package_slot(REPO_ROOT)
    registry_example = _west_reservoir_registry_example(REPO_ROOT)
    forest_route = _flathead_registry_route(REPO_ROOT)

    assert real_package_slot["slot_id"] == REVIEWER_READY_SLOT_ID
    assert real_package_slot["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert real_package_slot["expected_contract_status"] == "reviewer_ready"

    assert registry_example["example_id"] == REVIEWER_READY_EXAMPLE_ID
    assert registry_example["coverage_slot_id"] == REVIEWER_READY_SLOT_ID
    assert registry_example["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert registry_example["expected_contract_status"] == "reviewer_ready"

    assert forest_route["forest_unit_id"] == "flathead-nf"
    assert forest_route["routing_status"] == "real_package_examples_available"
    assert forest_route["primary_example_id"] == REVIEWER_READY_EXAMPLE_ID


def _west_reservoir_source_set_contracts(repo_root: Path) -> dict[str, str]:
    replay_context = _load_json(repo_root / "config/replay_contexts/west-reservoir-67436.json")
    v1_contract = _load_json(repo_root / "config/v1_west_reservoir_real_ea_eval.json")
    component_contract = _load_json(
        repo_root / "config/forest_plan_component_evals/west-reservoir-67436.json"
    )
    component_coverage = _load_json(repo_root / "config/forest_plan_component_eval_coverage_v1.json")
    component_slot = _slot_by_review_id(component_coverage, REVIEW_ID)

    return {
        "component_coverage_slot.expected_source_set_id": str(
            component_slot["expected_source_set_id"]
        ),
        "component_eval_contract.source_set_id": str(component_contract["source_set_id"]),
        "replay_context.source_set_id": str(replay_context["source_set_id"]),
        "v1_eval_contract.source_set_id": str(v1_contract["source_set_id"]),
    }


def _source_set_mismatches(source_sets: dict[str, str]) -> dict[str, str]:
    expected = source_sets["replay_context.source_set_id"]
    return {
        surface: source_set_id
        for surface, source_set_id in source_sets.items()
        if source_set_id != expected
    }


def _west_reservoir_real_package_slot(repo_root: Path) -> dict:
    manifest = _load_json(repo_root / "config/v1_real_package_review_coverage_v1.json")
    return _slot_by_review_id(manifest, REVIEW_ID)


def _west_reservoir_registry_example(repo_root: Path) -> dict:
    registry = _load_json(repo_root / "config/forest_specific_example_package_registry_v1.json")
    return next(example for example in registry["review_examples"] if example["review_id"] == REVIEW_ID)


def _flathead_registry_route(repo_root: Path) -> dict:
    registry = _load_json(repo_root / "config/forest_specific_example_package_registry_v1.json")
    return next(
        route for route in registry["forest_routing"] if route["forest_unit_id"] == "flathead-nf"
    )


def _slot_by_review_id(manifest: dict, review_id: str) -> dict:
    return next(slot for slot in manifest["slots"] if slot["review_id"] == review_id)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
