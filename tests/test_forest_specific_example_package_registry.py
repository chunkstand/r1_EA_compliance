from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "forest_specific_example_package_registry_v1.json"
QUEUE_LEDGER_PATH = ROOT / "config" / "source_register_queue_resolution_ledger_v1.json"
REAL_PACKAGE_COVERAGE_PATH = ROOT / "config" / "v1_real_package_review_coverage_v1.json"
PROFILE_COVERAGE_PATH = ROOT / "config" / "region1_forest_plan_profile_eval_coverage_v1.json"


def test_registry_covers_each_region1_forest_once_and_matches_summary() -> None:
    registry = _load_json(REGISTRY_PATH)

    forest_rows = registry["forest_routing"]
    forest_ids = [row["forest_unit_id"] for row in forest_rows]

    assert registry["schema_version"] == "forest-specific-example-package-registry-v1"
    assert len(forest_rows) == 10
    assert len(set(forest_ids)) == 10
    assert registry["summary"] == {
        "forest_unit_count": 10,
        "profile_guidance_only_count": 8,
        "review_example_count": 3,
        "reviewer_ready_example_count": 2,
        "typed_blocked_example_count": 1,
    }


def test_registry_forest_fixture_requirements_match_profile_eval_contract() -> None:
    registry = _load_json(REGISTRY_PATH)
    profile_manifest = _load_json(PROFILE_COVERAGE_PATH)

    expected_by_forest = {
        row["forest_unit_id"]: row["required_fixture_family_ids"]
        for row in profile_manifest["profiles"]
    }
    actual_by_forest = {
        row["forest_unit_id"]: row["required_fixture_family_ids"]
        for row in registry["forest_routing"]
    }

    assert actual_by_forest == expected_by_forest


def test_registry_review_examples_align_with_real_package_coverage_manifest() -> None:
    registry = _load_json(REGISTRY_PATH)
    coverage_manifest = _load_json(REAL_PACKAGE_COVERAGE_PATH)

    coverage_slots = {slot["slot_id"]: slot for slot in coverage_manifest["slots"]}
    artifact_family_ids = {
        row["artifact_family_id"] for row in registry["artifact_family_catalog"]
    }
    forest_ids = {row["forest_unit_id"] for row in registry["forest_routing"]}

    for example in registry["review_examples"]:
        slot = coverage_slots[example["coverage_slot_id"]]
        assert example["review_id"] == slot["review_id"]
        assert example["forest_unit_id"] == slot["forest_unit_id"]
        assert example["expected_contract_status"] == slot["expected_contract_status"]
        assert example["eval_file"] == f"config/{slot['eval_file']}"
        assert example["package_authority"]["replay_context_path"] == (
            f"config/{slot['package_authority']['replay_context_path']}"
        )
        assert Path(ROOT / example["package_authority"]["replay_context_path"]).exists()
        assert set(example["applicable_forest_unit_ids"]) == {example["forest_unit_id"]}
        assert set(example["agent_read_artifact_family_ids"]) <= artifact_family_ids
        assert set(example["applicable_forest_unit_ids"]) <= forest_ids


def test_registry_queue_boundary_reroutes_east_crazy_out_of_master_promotion() -> None:
    registry = _load_json(REGISTRY_PATH)
    queue_ledger = _load_json(QUEUE_LEDGER_PATH)

    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "custer-gallatin-nf"
    )
    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == "cgnf-east-crazy-current-promotion"
    )
    ledger_entries = {entry["source_id"]: entry for entry in queue_ledger["entries"]}

    assert forest_row["queue_boundary_source_ids"] == ["FOR-012", "LEX-Q-001"]
    assert example_row["queue_lineage_source_ids"] == ["FOR-012", "LEX-Q-001"]

    for source_id in ("FOR-012", "LEX-Q-001"):
        entry = ledger_entries[source_id]
        assert entry["planned_disposition"] == "named_blocker"
        assert entry["resolution_status"] == "blocked"
        assert entry["blocker_packet_reference"] == (
            "docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md"
        )


def test_registry_keeps_lolo_profile_only_while_for_029_routes_to_active_packet() -> None:
    registry = _load_json(REGISTRY_PATH)
    queue_ledger = _load_json(QUEUE_LEDGER_PATH)

    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "lolo-nf"
    )
    ledger_entries = {entry["source_id"]: entry for entry in queue_ledger["entries"]}
    for_029 = ledger_entries["FOR-029"]

    assert forest_row["routing_status"] == "profile_eval_guidance_only"
    assert forest_row["primary_example_id"] is None
    assert forest_row["queue_boundary_source_ids"] == ["FOR-029"]
    assert "inspect the Tyler's Kitchen root package first" in forest_row["guidance_note"]
    assert "inherited phase-eval blocker" in forest_row["guidance_note"]
    assert for_029["planned_disposition"] == "named_blocker"
    assert for_029["resolution_status"] == "blocked"
    assert for_029["blocker_packet_reference"] == (
        "docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md"
    )


def test_registry_contract_paths_exist_and_review_patterns_stay_parameterized() -> None:
    registry = _load_json(REGISTRY_PATH)

    for shared_contract in registry["shared_contract_catalog"]:
        assert Path(ROOT / shared_contract["path"]).exists()

    valid_path_modes = {"manifest_slot", "review_dir", "review_file"}
    for artifact in registry["artifact_family_catalog"]:
        assert artifact["path_mode"] in valid_path_modes
        if artifact["path_mode"] != "manifest_slot":
            assert "<review_id>" in artifact["path_pattern"]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
