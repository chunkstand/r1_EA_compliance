from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.forest_plan_components import build_forest_plan_component_inventory
from usfs_r1_ea_sources.forest_plan_components import load_forest_plan_component_inventory

from tests.support.forest_plan_component_fixtures import _check
from tests.support.forest_plan_component_fixtures import _chunk
from tests.support.forest_plan_component_fixtures import _FOREST_PLAN_TEXT
from tests.support.forest_plan_component_fixtures import _write_chunks
from tests.support.forest_plan_component_fixtures import _write_inventory_build_contract


class ForestPlanComponentManifestTests(unittest.TestCase):
    def test_manifest_build_writes_multi_forest_inventory_and_aggregate_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            manifest_path, readiness_path = _write_inventory_build_contract(
                output_dir,
                source_set_id=source_set_id,
                rows=[
                    {
                        "forest_unit_id": "custer-gallatin-nf",
                        "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                        "plan_version": "2022",
                    },
                    {
                        "forest_unit_id": "beaverhead-deerlodge-nf",
                        "source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                        "plan_version": "2009",
                    },
                ],
            )
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-custer-gallatin-nf-02",
                        text=_FOREST_PLAN_TEXT,
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-beaverhead-deerlodge-nf-02",
                        text=(
                            "Plan Components-Beaverhead-Deerlodge Forestwide.\n"
                            "Standards (BD-STD-TRVL) 01 New road construction is not allowed."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=chunks_path,
                manifest_path=manifest_path,
                manifest_readiness_path=readiness_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["build_scope"], "manifest_batch")
            self.assertEqual(
                result.summary["forest_unit_ids"],
                ["custer-gallatin-nf", "beaverhead-deerlodge-nf"],
            )
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertTrue(coverage["passed"])
            self.assertEqual(coverage["build_scope"], "manifest_batch")
            self.assertEqual(len(coverage["profile_results"]), 2)
            self.assertTrue(_check(coverage, "all_profile_builds_pass")["passed"])
            self.assertTrue(_check(coverage, "all_profile_builds_have_selected_chunks")["passed"])
            self.assertEqual(coverage["profile_results"][0]["blocker_types"], [])
            inventory = json.loads(result.inventory_path.read_text(encoding="utf-8"))
            self.assertEqual(inventory["build_scope"], "manifest_batch")
            self.assertEqual(
                inventory["forest_unit_ids"],
                ["custer-gallatin-nf", "beaverhead-deerlodge-nf"],
            )
            self.assertEqual(len(load_forest_plan_component_inventory(result.inventory_path)), 4)
            self.assertEqual(
                len(
                    load_forest_plan_component_inventory(
                        result.inventory_path,
                        forest_unit_id="beaverhead-deerlodge-nf",
                    )
                ),
                1,
            )

    def test_manifest_build_fails_on_cross_forest_duplicate_component_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            shared_source_record_id = "R1PLAN-shared-forest-plan-02"
            manifest_path, readiness_path = _write_inventory_build_contract(
                output_dir,
                source_set_id=source_set_id,
                rows=[
                    {
                        "forest_unit_id": "custer-gallatin-nf",
                        "source_record_id": shared_source_record_id,
                        "plan_version": "2022",
                    },
                    {
                        "forest_unit_id": "beaverhead-deerlodge-nf",
                        "source_record_id": shared_source_record_id,
                        "plan_version": "2009",
                    },
                ],
            )
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=shared_source_record_id,
                        text=(
                            "Plan Components-Test Forestwide.\n"
                            "Standards (SH-STD-01) 01 Shared standard text."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=chunks_path,
                manifest_path=manifest_path,
                manifest_readiness_path=readiness_path,
            )

            self.assertFalse(result.summary["passed"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertFalse(coverage["passed"])
            self.assertEqual(
                coverage["duplicate_component_ids"],
                [f"{shared_source_record_id}-SH-STD-01-01"],
            )

    def test_manifest_build_limits_component_parsing_to_component_bearing_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            manifest_path, readiness_path = _write_inventory_build_contract(
                output_dir,
                source_set_id=source_set_id,
                rows=[
                    {
                        "forest_unit_id": "nez-perce-clearwater-nfs",
                        "source_record_id": "R1PLAN-nez-perce-clearwater-nfs-06",
                        "plan_version": "2025",
                        "build_source_record_ids_by_role": {
                            "primary_land_management_plan": [
                                "R1PLAN-nez-perce-clearwater-nfs-06"
                            ],
                            "final_environmental_impact_statement": [
                                "R1PLAN-nez-perce-clearwater-nfs-15"
                            ],
                        },
                    }
                ],
            )
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-nez-perce-clearwater-nfs-06",
                        text=(
                            "Desired Conditions FW-DC-ED-01. Interpretation and educational "
                            "opportunities enhance visitor understanding. Standards "
                            "FW-STD-ED-02. Interpretive facilities shall protect cultural "
                            "resources."
                        ),
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-nez-perce-clearwater-nfs-15",
                        text=(
                            "Desired Conditions FW-DC-ED-01. Final environmental impact "
                            "statement summary text that would collide if parsed."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=chunks_path,
                manifest_path=manifest_path,
                manifest_readiness_path=readiness_path,
            )

            self.assertTrue(result.summary["passed"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["duplicate_component_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])

    def test_manifest_build_accepts_forest_plan_support_for_component_bearing_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            manifest_path, readiness_path = _write_inventory_build_contract(
                output_dir,
                source_set_id=source_set_id,
                rows=[
                    {
                        "forest_unit_id": "dakota-prairie-grasslands",
                        "source_record_id": "R1PLAN-dakota-prairie-grasslands-03",
                        "plan_version": "2001",
                        "build_source_record_ids_by_role": {
                            "primary_land_resource_management_plan_part": [
                                "R1PLAN-dakota-prairie-grasslands-03",
                                "R1PLAN-dakota-prairie-grasslands-05",
                            ],
                        },
                    }
                ],
            )
            support_chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id="R1PLAN-dakota-prairie-grasslands-05",
                text=(
                    "Goal 1: Ensure sustainable ecosystems. Standard 2. Meet air "
                    "quality requirements."
                ),
            )
            support_chunk["document_role"] = "forest_plan_support"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[support_chunk],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=chunks_path,
                manifest_path=manifest_path,
                manifest_readiness_path=readiness_path,
            )

            self.assertTrue(result.summary["passed"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            profile = next(
                row
                for row in coverage["profile_results"]
                if row["forest_unit_id"] == "dakota-prairie-grasslands"
            )
            self.assertEqual(profile["selected_chunk_count"], 1)
            self.assertEqual(profile["built_standard_count"], 1)

    def test_cli_parser_exposes_inventory_builder_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "forest-plan-components-build",
                "--source-set-id",
                "source-set-test",
                "--source-record-id",
                "R1PLAN-custer-gallatin-nf-02",
                "--plan-version",
                "2022",
                "--management-area-id",
                "mgmt-crazy-mountains-bca",
            ]
        )

        self.assertEqual(args.command, "forest-plan-components-build")
        self.assertEqual(args.management_area_ids, ["mgmt-crazy-mountains-bca"])
        self.assertIsNone(args.manifest_path)

    def test_cli_parser_accepts_manifest_driven_inventory_build(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "forest-plan-components-build",
                "--source-set-id",
                "source-set-test",
                "--manifest-path",
            ]
        )

        self.assertEqual(args.command, "forest-plan-components-build")
        self.assertIsNotNone(args.manifest_path)
        self.assertIsNone(args.source_record_id)
        self.assertIsNone(args.plan_version)
