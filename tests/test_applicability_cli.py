from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.replay_context import ReplayContextMismatchError

from tests.support.applicability_authority_universe_fixtures import (
    _catalog_record,
    _default_template_catalog_records,
    _write_catalog,
    _write_component_inventory,
    _write_region1_component_inventory,
    _write_rule_claim_links,
    _write_rule_pack,
)


class ApplicabilityAuthorityUniverseCliTests(unittest.TestCase):
    def test_cli_writes_authority_universe_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            exit_code = main(
                [
                    "applicability-authority-universe",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    "cli-unit",
                    "--source-set-id",
                    source_set_id,
                    "--base-rule-pack",
                    str(rule_pack_path),
                    "--forest-plan-component-inventory-path",
                    str(component_inventory_path),
                    "--no-authority-family-templates",
                ]
            )

            self.assertEqual(exit_code, 0)
            snapshot_path = (
                output_dir
                / "reviews"
                / "cli-unit"
                / "applicability"
                / "authority_universe_snapshot.json"
            )
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertTrue(snapshot["validation"]["passed"])
            self.assertEqual(snapshot["summary"]["candidate_authority_count"], 5)

    def test_cli_loads_default_authority_family_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            records = [
                _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                _catalog_record(
                    source_set_id,
                    "R1PLAN-custer-gallatin-nf-02",
                    "forest_plan",
                    "forest_plan",
                ),
                *_default_template_catalog_records(source_set_id),
            ]
            _write_catalog(output_dir, source_set_id, records)
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            exit_code = main(
                [
                    "applicability-authority-universe",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    "cli-default-template-unit",
                    "--source-set-id",
                    source_set_id,
                    "--base-rule-pack",
                    str(rule_pack_path),
                    "--forest-plan-component-inventory-path",
                    str(component_inventory_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            snapshot_path = (
                output_dir
                / "reviews"
                / "cli-default-template-unit"
                / "applicability"
                / "authority_universe_snapshot.json"
            )
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertTrue(snapshot["validation"]["passed"])
            self.assertEqual(
                snapshot["summary"]["authority_family_rule_template_candidate_count"],
                19,
            )
            self.assertEqual(snapshot["summary"]["candidate_authority_count"], 24)

    def test_cli_uses_tracked_replay_context_catalog_surface_for_authority_universe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-tracked"
            review_id = "tracked-review"
            rule_pack_path = _write_rule_pack(root)
            active_records = [_catalog_record("source-set-active", "ACTIVE-ONLY", "law", "law")]
            _write_catalog(output_dir, "source-set-active", active_records)
            tracked_catalog_dir = (
                output_dir / "runs" / "current-source-gap-closeout-catalog-gate" / "catalog_gate"
            )
            tracked_catalog_dir.mkdir(parents=True, exist_ok=True)
            tracked_records = [
                _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                _catalog_record(
                    source_set_id,
                    "R1PLAN-custer-gallatin-nf-02",
                    "forest_plan",
                    "forest_plan",
                ),
            ]
            (tracked_catalog_dir / "source_set_manifest.json").write_text(
                json.dumps({"source_set_id": source_set_id}, sort_keys=True),
                encoding="utf-8",
            )
            (tracked_catalog_dir / "source_catalog.jsonl").write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in tracked_records),
                encoding="utf-8",
            )
            replay_context_dir = root / "config" / "replay_contexts"
            replay_context_dir.mkdir(parents=True, exist_ok=True)
            (replay_context_dir / f"{review_id}.json").write_text(
                json.dumps(
                    {
                        "review_id": review_id,
                        "source_set_id": source_set_id,
                        "catalog_dir": (
                            "source_library/runs/current-source-gap-closeout-catalog-gate/"
                            "catalog_gate"
                        ),
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            exit_code = main(
                [
                    "applicability-authority-universe",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    review_id,
                    "--base-rule-pack",
                    str(rule_pack_path),
                    "--forest-plan-component-inventory-path",
                    str(component_inventory_path),
                    "--no-authority-family-templates",
                ]
            )

            self.assertEqual(exit_code, 0)
            snapshot_path = (
                output_dir / "reviews" / review_id / "applicability" / "authority_universe_snapshot.json"
            )
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["source_set_id"], source_set_id)
            self.assertTrue(snapshot["validation"]["passed"])
            self.assertEqual(snapshot["summary"]["candidate_authority_count"], 5)

    def test_cli_rejects_mismatched_tracked_replay_context_source_set_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            review_id = "tracked-review"
            replay_context_dir = root / "config" / "replay_contexts"
            replay_context_dir.mkdir(parents=True, exist_ok=True)
            (replay_context_dir / f"{review_id}.json").write_text(
                json.dumps(
                    {
                        "review_id": review_id,
                        "source_set_id": "source-set-tracked",
                        "catalog_dir": "source_library/catalog",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ReplayContextMismatchError):
                main(
                    [
                        "applicability-authority-universe",
                        "--output-dir",
                        str(output_dir),
                        "--review-id",
                        review_id,
                        "--source-set-id",
                        "source-set-other",
                    ]
                )

    def test_cli_applies_tracked_replay_context_forest_unit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-tracked"
            review_id = "tracked-flathead-review"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-flathead-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            replay_context_dir = root / "config" / "replay_contexts"
            replay_context_dir.mkdir(parents=True, exist_ok=True)
            (replay_context_dir / f"{review_id}.json").write_text(
                json.dumps(
                    {
                        "review_id": review_id,
                        "source_set_id": source_set_id,
                        "forest_unit_id": "flathead-nf",
                        "catalog_dir": "source_library/catalog",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_region1_component_inventory(
                output_dir,
                source_set_id,
            )

            exit_code = main(
                [
                    "applicability-authority-universe",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    review_id,
                    "--base-rule-pack",
                    str(rule_pack_path),
                    "--forest-plan-component-inventory-path",
                    str(component_inventory_path),
                    "--no-authority-family-templates",
                ]
            )

            self.assertEqual(exit_code, 0)
            snapshot_path = (
                output_dir / "reviews" / review_id / "applicability" / "authority_universe_snapshot.json"
            )
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["forest_unit_id"], "flathead-nf")
            self.assertEqual(snapshot["summary"]["rule_template_candidate_count"], 2)
            self.assertEqual(snapshot["summary"]["forest_plan_component_candidate_count"], 1)

    def test_cli_rejects_mismatched_tracked_replay_context_forest_unit_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            review_id = "tracked-review"
            replay_context_dir = root / "config" / "replay_contexts"
            replay_context_dir.mkdir(parents=True, exist_ok=True)
            (replay_context_dir / f"{review_id}.json").write_text(
                json.dumps(
                    {
                        "review_id": review_id,
                        "source_set_id": "source-set-tracked",
                        "forest_unit_id": "flathead-nf",
                        "catalog_dir": "source_library/catalog",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ReplayContextMismatchError):
                main(
                    [
                        "applicability-authority-universe",
                        "--output-dir",
                        str(output_dir),
                        "--review-id",
                        review_id,
                        "--forest-unit-id",
                        "custer-gallatin-nf",
                    ]
                )

    def test_cli_writes_applicability_gate_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            review_id = "gate-graph-cli"
            applicability_dir = output_dir / "reviews" / review_id / "applicability"
            applicability_dir.mkdir(parents=True)
            authority_universe_path = applicability_dir / "authority_universe_snapshot.json"
            authority_universe_path.write_text(
                json.dumps(
                    {
                        "schema_version": "authority-universe-snapshot-v0",
                        "review_id": review_id,
                        "source_set_id": "source-set-gate-cli",
                        "candidate_authorities": [],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "applicability-gate-graph",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    review_id,
                    "--authority-universe-path",
                    str(authority_universe_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            graph_path = applicability_dir / "applicability_gate_graph.json"
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            self.assertTrue(graph["validation"]["passed"])
            self.assertEqual(graph["root_gate_id"], "gate:nepa_ea_review")
            self.assertEqual(
                graph["summary"]["authority_family_gate_count"],
                graph["summary"]["inventory_authority_family_count"],
            )
