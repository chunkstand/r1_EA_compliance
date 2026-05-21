from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import main

from tests.support.applicability_authority_universe_fixtures import (
    _catalog_record,
    _default_template_catalog_records,
    _write_catalog,
    _write_component_inventory,
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
