from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.forest_plan_components import (
    _component_inventory_coverage,
    build_forest_plan_component_inventory,
    load_forest_plan_component_inventory,
)


class ForestPlanComponentInventoryBuilderTests(unittest.TestCase):
    def test_builds_labeled_component_inventory_from_forest_plan_chunks(self) -> None:
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
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-nonplan",
                        text="Standards (OTHER-STD) 01 This should not be selected.",
                    ),
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id=source_record_id,
                            text="Standards (NONPLAN-STD) 01 This should not be selected.",
                        ),
                        "document_role": "environmental_assessment",
                    },
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
                geographic_area_ids=["geo-bridger-bangtail-crazy"],
                management_area_ids=["mgmt-crazy-mountains-bca"],
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["component_count"], 3)
            self.assertTrue(result.summary["coverage_passed"])
            self.assertEqual(result.summary["standard_count"], 1)
            self.assertEqual(
                result.summary["component_type_counts"],
                {
                    "desired_condition": 1,
                    "standard": 1,
                    "suitability": 1,
                },
            )
            self.assertTrue(result.components_jsonl_path.exists())
            self.assertTrue(result.coverage_path.exists())
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertTrue(coverage["passed"])
            self.assertEqual(coverage["detected_component_count"], 3)
            self.assertEqual(coverage["detected_standard_count"], 1)
            self.assertEqual(coverage["missing_standard_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            self.assertEqual(len(components), 3)
            standard = next(
                component for component in components if component["component_type"] == "standard"
            )
            self.assertEqual(standard["source_set_id"], source_set_id)
            self.assertEqual(standard["source_record_id"], source_record_id)
            self.assertEqual(standard["source_chunk_ids"], [f"chunk:{source_record_id}"])
            self.assertIn(
                "new permanent or temporary roads",
                standard["package_evidence_terms"],
            )
            self.assertEqual(
                standard["management_area_ids"],
                ["mgmt-crazy-mountains-bca"],
            )
            self.assertEqual(
                standard["section_heading"],
                "Plan Components-Crazy Mountains Backcountry Area (CMBCA)",
            )

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


_FOREST_PLAN_TEXT = """
Plan Components-Crazy Mountains Backcountry Area (CMBCA).
Desired Conditions (BC-DC-CMBCA) 01 Quiet, nonmotorized recreation opportunities predominate.
Standards (BC-STD-CMBCA) 01 New permanent or temporary roads shall not be allowed.
Suitability (BC-SUIT-CMBCA) 01 The backcountry area is not suitable for motorized transport.
"""


def _chunk(*, source_set_id: str, source_record_id: str, text: str) -> dict:
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": "Custer Gallatin Land Management Plan",
        "document_role": "forest_plan",
        "authority_level": "forest_plan",
        "host": "example.test",
        "expected_parser": "pdf",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"artifacts/raw/{source_record_id}.pdf",
        "citation_label": f"{source_record_id} | Custer Gallatin LMP",
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-01T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": "Plan Components-Crazy Mountains Backcountry Area (CMBCA)",
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }


def _write_chunks(*, output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
