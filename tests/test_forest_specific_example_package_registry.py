from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "forest_specific_example_package_registry_v1.json"
QUEUE_LEDGER_PATH = ROOT / "config" / "source_register_queue_resolution_ledger_v1.json"
REAL_PACKAGE_COVERAGE_PATH = ROOT / "config" / "v1_real_package_review_coverage_v1.json"
PROFILE_COVERAGE_PATH = ROOT / "config" / "region1_forest_plan_profile_eval_coverage_v1.json"
AGENT_START_HERE_PATH = ROOT / "docs" / "AGENT_START_HERE.md"
README_PATH = ROOT / "README.md"


def test_registry_covers_each_region1_forest_once_and_matches_summary() -> None:
    registry = _load_json(REGISTRY_PATH)

    forest_rows = registry["forest_routing"]
    forest_ids = [row["forest_unit_id"] for row in forest_rows]

    assert registry["schema_version"] == "forest-specific-example-package-registry-v1"
    assert len(forest_rows) == 10
    assert len(set(forest_ids)) == 10
    assert registry["summary"] == {
        "forest_unit_count": 10,
        "profile_guidance_only_count": 4,
        "review_example_count": 7,
        "reviewer_ready_example_count": 7,
        "typed_blocked_example_count": 0,
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


def test_registry_promotes_lolo_example_after_for_029_resolves_to_example_lane() -> None:
    registry = _load_json(REGISTRY_PATH)
    queue_ledger = _load_json(QUEUE_LEDGER_PATH)

    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "lolo-nf"
    )
    ledger_entries = {entry["source_id"]: entry for entry in queue_ledger["entries"]}
    for_029 = ledger_entries["FOR-029"]

    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == "lolo-tylers-kitchen-forest-specific"
    )

    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == "lolo-tylers-kitchen-forest-specific"
    assert forest_row["queue_boundary_source_ids"] == ["FOR-029"]
    assert "inspect the Tyler's Kitchen root package first" in forest_row["guidance_note"]
    assert example_row["queue_lineage_source_ids"] == ["FOR-029"]
    assert example_row["coverage_slot_id"] == "lolo-tylers-kitchen-forest-specific"
    assert for_029["planned_disposition"] == "forest_specific_example_package"
    assert for_029["resolution_status"] == "resolved"
    assert for_029["blocker_packet_reference"] == (
        "docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md"
    )


def test_registry_promotes_west_reservoir_as_flathead_primary_example() -> None:
    registry = _load_json(REGISTRY_PATH)

    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "flathead-nf"
    )
    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == "flathead-west-reservoir-forest-specific"
    )

    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == "flathead-west-reservoir-forest-specific"
    assert "Use the West Reservoir package first" in forest_row["guidance_note"]
    assert example_row["review_id"] == "west-reservoir-67436"
    assert example_row["coverage_slot_id"] == "flathead-west-reservoir-forest-specific"
    assert example_row["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert example_row["expected_contract_status"] == "reviewer_ready"


def test_registry_promotes_south_otter_as_custer_gallatin_primary_without_queue_row() -> None:
    registry = _load_json(REGISTRY_PATH)
    queue_ledger = _load_json(QUEUE_LEDGER_PATH)

    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "custer-gallatin-nf"
    )
    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == "cgnf-south-otter-forest-specific"
    )
    ledger_source_ids = {entry["source_id"] for entry in queue_ledger["entries"]}

    assert forest_row["primary_example_id"] == "cgnf-south-otter-forest-specific"
    assert forest_row["supplemental_example_ids"] == [
        "cgnf-east-crazy-current-promotion",
    ]
    assert forest_row["archived_example_ids"] == ["cgnf-south-plateau-expansion"]
    assert "Use the South Otter package first" in forest_row["guidance_note"]
    assert example_row["forest_unit_id"] == "custer-gallatin-nf"
    assert example_row["applicable_forest_unit_ids"] == ["custer-gallatin-nf"]
    assert example_row["coverage_slot_id"] == "cgnf-south-otter-forest-specific"
    assert example_row["queue_lineage_source_ids"] == []
    assert "South Otter" not in ledger_source_ids
    assert "58396" not in ledger_source_ids


def test_registry_promotes_hlc_bonanza_as_primary_example_without_queue_row() -> None:
    registry = _load_json(REGISTRY_PATH)

    forest_row = next(
        row
        for row in registry["forest_routing"]
        if row["forest_unit_id"] == "helena-lewis-and-clark-nf"
    )
    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == "hlc-bonanza-forest-specific"
    )

    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == "hlc-bonanza-forest-specific"
    assert forest_row["supplemental_example_ids"] == []
    assert "Use the Bonanza package first" in (
        forest_row["guidance_note"]
    )
    assert example_row["review_id"] == (
        "region1-example-helena-lewis-and-clark-bonanza-66532"
    )
    assert example_row["forest_unit_id"] == "helena-lewis-and-clark-nf"
    assert example_row["applicable_forest_unit_ids"] == [
        "helena-lewis-and-clark-nf"
    ]
    assert example_row["coverage_slot_id"] == "hlc-bonanza-forest-specific"
    assert example_row["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert example_row["expected_contract_status"] == "reviewer_ready"
    assert example_row["queue_lineage_source_ids"] == []


def test_registry_promotes_bitterroot_front_as_primary_example() -> None:
    registry = _load_json(REGISTRY_PATH)
    queue_ledger = _load_json(QUEUE_LEDGER_PATH)

    forest_row = next(
        row for row in registry["forest_routing"] if row["forest_unit_id"] == "bitterroot-nf"
    )
    ledger_entries = {entry["source_id"]: entry for entry in queue_ledger["entries"]}
    for_007 = ledger_entries["FOR-007"]
    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == "bitterroot-front-forest-specific"
    )

    assert forest_row["routing_status"] == "real_package_examples_available"
    assert forest_row["primary_example_id"] == "bitterroot-front-forest-specific"
    assert forest_row["supplemental_example_ids"] == []
    assert forest_row["queue_boundary_source_ids"] == ["FOR-007"]
    assert "Use the Bitterroot Front package first" in (
        forest_row["guidance_note"]
    )
    assert queue_ledger["status"] == "bitterroot_front_example_resolved"
    assert example_row["review_id"] == "region1-example-bitterroot-front-57341"
    assert example_row["forest_unit_id"] == "bitterroot-nf"
    assert example_row["applicable_forest_unit_ids"] == ["bitterroot-nf"]
    assert example_row["coverage_slot_id"] == "bitterroot-front-forest-specific"
    assert example_row["coverage_class_id"] == "forest_specific_reviewer_ready"
    assert example_row["expected_contract_status"] == "reviewer_ready"
    assert example_row["queue_lineage_source_ids"] == ["FOR-007"]
    assert for_007["planned_disposition"] == "forest_specific_example_package"
    assert for_007["resolution_status"] == "resolved"
    assert for_007["blocker_packet_reference"] == (
        "docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md"
    )


def test_registry_routes_idaho_panhandle_lacy_lemoosh_as_active_candidate_without_promotion() -> None:
    registry = _load_json(REGISTRY_PATH)
    coverage_manifest = _load_json(REAL_PACKAGE_COVERAGE_PATH)

    forest_row = next(
        row
        for row in registry["forest_routing"]
        if row["forest_unit_id"] == "idaho-panhandle-nfs"
    )
    active_example_ids = {row["example_id"] for row in registry["review_examples"]}
    coverage_slot_ids = {slot["slot_id"] for slot in coverage_manifest["slots"]}

    assert forest_row["routing_status"] == "profile_eval_guidance_only"
    assert forest_row["primary_example_id"] is None
    assert forest_row["supplemental_example_ids"] == []
    assert forest_row["queue_boundary_source_ids"] == []
    assert "Lacy Lemoosh is the selected active Idaho Panhandle" in (
        forest_row["guidance_note"]
    )
    assert "profile-eval floor" in forest_row["guidance_note"]
    assert "ipnf-lacy-lemoosh-forest-specific" not in active_example_ids
    assert "ipnf-lacy-lemoosh-forest-specific" not in coverage_slot_ids
    assert (
        ROOT
        / "docs"
        / "IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md"
    ).exists()


def test_agent_start_here_names_bitterroot_front_as_latest_resolved_example() -> None:
    registry = _load_json(REGISTRY_PATH)
    agent_start = AGENT_START_HERE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")

    forest_row = next(
        row
        for row in registry["forest_routing"]
        if row["forest_unit_id"] == "bitterroot-nf"
    )
    example_row = next(
        row
        for row in registry["review_examples"]
        if row["example_id"] == forest_row["primary_example_id"]
    )

    assert "docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md" in agent_start
    assert "latest resolved forest-specific example packet" in agent_start
    assert f'example_id="{example_row["example_id"]}"' in agent_start
    assert f'review_id="{example_row["review_id"]}"' in agent_start
    assert f'primary_example_id="{forest_row["primary_example_id"]}"' in agent_start
    assert f'forest_unit_id="{forest_row["forest_unit_id"]}"' in agent_start
    assert "Bitterroot Front as the governed primary example" in agent_start
    assert "must not be reused for non-Bitterroot forests" in agent_start
    assert f'primary_example_id="{forest_row["primary_example_id"]}"' in readme
    assert f'review_id="{example_row["review_id"]}"' in readme


def test_registry_archives_south_plateau_as_historical_only() -> None:
    registry = _load_json(REGISTRY_PATH)

    active_example_ids = {row["example_id"] for row in registry["review_examples"]}
    archived_examples = {
        row["example_id"]: row for row in registry["archived_review_examples"]
    }

    assert "cgnf-south-plateau-expansion" not in active_example_ids
    south_plateau = archived_examples["cgnf-south-plateau-expansion"]
    assert south_plateau["review_id"] == (
        "region1-expansion-south-plateau-landscape-treatment"
    )
    assert south_plateau["usage_policy"] == "historical_evidence_only_not_example"
    assert south_plateau["active_example"] is False
    assert south_plateau["archive_reason"] == (
        "litigation_forest_plan_compliance_challenge"
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
