from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from usfs_r1_ea_sources.forest_plan_components import _component_inventory_coverage
from usfs_r1_ea_sources.forest_plan_components import build_forest_plan_component_inventory
from usfs_r1_ea_sources.forest_plan_components import load_forest_plan_component_inventory

from tests.support.forest_plan_component_fixtures import _chunk
from tests.support.forest_plan_component_fixtures import _FOREST_PLAN_TEXT
from tests.support.forest_plan_component_fixtures import _write_chunks


class ForestPlanComponentCoverageTests(unittest.TestCase):
    def test_duplicate_standard_labels_fail_build_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            _FOREST_PLAN_TEXT
                            + "\nStandards (BC-STD-CMBCA) 01 Duplicate standard text."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
                management_area_ids=["mgmt-crazy-mountains-bca"],
            )

            duplicate_id = f"{source_record_id}-BC-STD-CMBCA-01"
            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["coverage_passed"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertFalse(coverage["passed"])
            self.assertEqual(coverage["duplicate_component_ids"], [duplicate_id])
            self.assertEqual(coverage["duplicate_standard_ids"], [duplicate_id])
            failed_checks = {
                check["name"] for check in coverage["checks"] if not check["passed"]
            }
            self.assertIn("built_component_ids_are_unique", failed_checks)
            self.assertIn("detected_standard_labels_are_unique", failed_checks)
            with self.assertRaises(ValueError):
                load_forest_plan_component_inventory(
                    result.inventory_path,
                    forest_unit_id="custer-gallatin-nf",
                )

    def test_overlapping_chunk_duplicates_are_merged_before_build_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            first_chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                text=(
                    "Plan Components-Crazy Mountains Backcountry Area (CMBCA).\n"
                    "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads "
                    "shall not be allowed."
                ),
            )
            overlap_chunk = {
                **_chunk(
                    source_set_id=source_set_id,
                    source_record_id=source_record_id,
                    text=(
                        "Plan Components-Crazy Mountains Backcountry Area (CMBCA).\n"
                        "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads "
                        "shall not be allowed.\nCuster Gallatin Land Management Plan page 72."
                    ),
                ),
                "chunk_id": f"chunk:{source_record_id}:overlap",
                "chunk_index": 1,
            }
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[first_chunk, overlap_chunk],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.summary["coverage_passed"])
            self.assertTrue(result.summary["component_source_accuracy_passed"])
            self.assertEqual(result.summary["component_source_accuracy_failure_count"], 0)
            self.assertEqual(result.summary["component_count"], 1)
            self.assertEqual(result.summary["standard_count"], 1)
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["duplicate_component_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            self.assertEqual(coverage["detected_component_count"], 1)
            self.assertTrue(coverage["component_source_accuracy_passed"])
            self.assertEqual(coverage["component_source_accuracy_failure_count"], 0)
            failed_checks = [
                check["name"] for check in coverage["checks"] if not check["passed"]
            ]
            self.assertNotIn(
                "component_redetects_from_primary_source_chunk",
                failed_checks,
            )
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            self.assertEqual(len(components), 1)
            self.assertEqual(
                components[0]["source_chunk_ids"],
                [f"chunk:{source_record_id}:overlap", f"chunk:{source_record_id}"],
            )
            self.assertEqual(
                components[0]["management_area_ids"],
                ["mgmt-crazy-mountains-bca"],
            )

    def test_overlapping_chunk_duplicates_merge_despite_footer_and_ocr_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "FINAL-FLAT-001"
            first_chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                text=(
                    "Plan Components-Forestwide Direction.\n"
                    "Guidelines (FW-GDL-SOIL) 01 Ground-based equipment for vegetation "
                    "management should only operate on slopes less than 40 percent to protect "
                    "soil quality."
                ),
            )
            overlap_chunk = {
                **_chunk(
                    source_set_id=source_set_id,
                    source_record_id=source_record_id,
                    text=(
                        "Plan Components-Forestwide Direction.\n"
                        "Guidelines (FW-GDL-SOIL) 01 Ground- based equipment for vegetation "
                        "management should only operate on slopes less than 40 percent to protect "
                        "soil quality. Flathead National Forest Land Management Plan 24 "
                        "Chapter 2. Forestwide Direction"
                    ),
                ),
                "chunk_id": f"chunk:{source_record_id}:overlap-noisy",
                "chunk_index": 1,
            }
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[first_chunk, overlap_chunk],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="flathead-nf",
                plan_version="2018",
                chunks_path=chunks_path,
            )

            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(result.summary["component_count"], 1)
            self.assertEqual(coverage["duplicate_component_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            self.assertEqual(coverage["detected_component_count"], 1)
            failed_checks = {check["name"] for check in coverage["checks"] if not check["passed"]}
            self.assertNotIn("built_component_ids_are_unique", failed_checks)

    def test_failing_build_coverage_blocks_generated_inventory_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=_FOREST_PLAN_TEXT,
                    ),
                ],
            )
            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
                management_area_ids=["mgmt-crazy-mountains-bca"],
            )
            build_coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            build_coverage["passed"] = False
            build_coverage["duplicate_standard_ids"] = ["R1PLAN-custer-gallatin-nf-02-STD-01"]
            result.coverage_path.write_text(
                json.dumps(build_coverage, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )

            review_coverage = _component_inventory_coverage(
                review_id="review-test",
                source_set_id=source_set_id,
                component_inventory_path=result.inventory_path,
                components=components,
            )

            self.assertFalse(review_coverage["passed"])
            self.assertTrue(review_coverage["component_inventory_build_coverage_required"])
            self.assertFalse(review_coverage["component_inventory_build_coverage_passed"])
            check = next(
                check
                for check in review_coverage["checks"]
                if check["name"] == "component_inventory_build_coverage_passes"
            )
            self.assertFalse(check["passed"])
            self.assertTrue(check["details"]["present"])
