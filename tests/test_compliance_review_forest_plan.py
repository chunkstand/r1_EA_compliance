from pathlib import Path
import json
import tempfile
import unittest

from tests.support.compliance_component_fixtures import (
    _build_beaverhead_compliance_source_library,
    _build_custer_compliance_source_library,
    _build_flathead_compliance_source_library,
)
from tests.support.compliance_component_review_fixtures import (
    _write_beaverhead_rule_pack,
    _write_component_adjudication_eval,
    _write_custer_rule_pack,
    _write_flathead_rule_pack,
)
from tests.support.compliance_review_fixtures import (
    _check,
    _read_jsonl,
    _run_generated_compliance_review,
    _write_package,
)


class ComplianceReviewForestPlanTests(unittest.TestCase):
    def test_custer_compliance_review_requires_generated_component_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area. No new permanent or temporary roads "
                    "are proposed."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="custer-compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "custer_gallatin")
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertTrue(forest_plan["component_evaluation"]["validation_passed"])
            self.assertTrue(forest_plan["component_evaluation"]["reviewer_ready"])
            self.assertTrue(forest_plan["component_findings_path"])
            self.assertTrue(forest_plan["component_inventory_coverage_path"])
            self.assertTrue(forest_plan["applicable_standard_coverage_path"])
            matrix = json.loads(result.compliance_matrix_path.read_text(encoding="utf-8"))
            self.assertEqual(
                matrix["summary"]["forest_plan_review"]["scope_status"],
                "custer_gallatin",
            )
            self.assertTrue(
                matrix["summary"]["forest_plan_review"]["component_findings_path"]
            )
            forest_matrix = matrix["forest_plan_compliance"]
            self.assertEqual(
                forest_matrix["schema_version"],
                "forest-plan-compliance-matrix-v0",
            )
            self.assertGreater(forest_matrix["summary"]["row_count"], 0)
            self.assertGreater(
                forest_matrix["summary"]["applicable_standard_row_count"],
                0,
            )
            forest_rows = forest_matrix["rows"]
            self.assertTrue(
                any(
                    row["component_type"] == "standard"
                    and row["compliance_status"] == "complies"
                    for row in forest_rows
                )
            )
            markdown = result.compliance_matrix_markdown_path.read_text(
                encoding="utf-8",
            )
            self.assertIn("## Forest Plan Compliance", markdown)
            self.assertIn(
                "| Component | Direction / standard | Decision support | EA consistency support | Forest Plan basis | Trace / caveats |",
                markdown,
            )
            self.assertIn("| Forest Plan citations | Pass |", markdown)
            self.assertIn("Applicable standard complies", markdown)
            self.assertIn("BC-STD-CMBCA", markdown)
            self.assertIn("all 1 applicable standards comply", markdown)
            self.assertNotIn("standard applied: True", markdown)

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertTrue(forest_plan_gate["details"]["component_reviewer_ready"])
            self.assertTrue(
                forest_plan_gate["details"]["component_inventory_coverage_passed"]
            )
            self.assertTrue(
                forest_plan_gate["details"]["applicable_standard_coverage_passed"]
            )
            nodes = _read_jsonl(result.finding_nodes_path)
            edges = _read_jsonl(result.finding_edges_path)
            self.assertIn("ForestPlanReview", {node["type"] for node in nodes})
            self.assertIn("ForestPlanComponentEvaluation", {node["type"] for node in nodes})
            self.assertIn(
                "REVIEW_INCLUDES_FOREST_PLAN_REVIEW",
                {edge["relationship"] for edge in edges},
            )
            self.assertIn(
                "FOREST_PLAN_REVIEW_HAS_COMPONENT_EVALUATION",
                {edge["relationship"] for edge in edges},
            )

    def test_beaverhead_compliance_review_requires_selected_profile_component_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_beaverhead_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Beaverhead-Deerlodge National Forest on the "
                    "Dillon Ranger District in the Big Hole Landscape and the West Big Hole "
                    "Management Area. The EA tiers to the FEIS and references the Record of "
                    "Decision. Inventoried Roadless Area direction applies. ESA consultation "
                    "includes a Biological Assessment and Biological Opinion for grizzly bear. "
                    "No new permanent or temporary roads are proposed. "
                    "| BD-STD-WBH-01 | New permanent or temporary roads shall not be allowed. "
                    "| Yes | EA section 2.2 says no new permanent or temporary roads are "
                    "proposed. |"
                ),
            )
            rule_pack_path = _write_beaverhead_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="beaverhead-compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                forest_unit_id="beaverhead-deerlodge-nf",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "beaverhead_deerlodge_nf")
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertTrue(forest_plan["component_evaluation"]["validation_passed"])
            self.assertTrue(forest_plan["component_evaluation"]["reviewer_ready"])
            context = json.loads(Path(forest_plan["context_path"]).read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["name"] for entry in context["project_location_signals"]],
                ["Dillon Ranger District"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["geographic_areas"]],
                ["Big Hole Landscape"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["management_areas"]],
                ["West Big Hole Management Area"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["overlays"]],
                ["Inventoried Roadless Area"],
            )
            self.assertEqual(
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
                {
                    "support-feis-plan-context",
                    "support-rod-travel-management",
                    "support-lynx-biological-assessment",
                    "support-lynx-biological-opinion",
                    "support-grizzly-biological-assessment",
                    "support-grizzly-biological-opinion",
                },
            )

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertEqual(
                forest_plan_gate["details"]["scope_status"],
                "beaverhead_deerlodge_nf",
            )
            self.assertTrue(forest_plan_gate["details"]["component_reviewer_ready"])

    def test_flathead_compliance_review_requires_selected_profile_component_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_flathead_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Flathead National Forest on the Hungry "
                    "Horse-Glacier View Ranger District in the Hungry Horse Geographic Area and "
                    "the Jewel Basin Hiking Area. The action is adjacent to the Jewel Basin "
                    "Recommended Wilderness Area and an Inventoried Roadless Area. The EA tiers "
                    "to the FEIS and references the Record of Decision. ESA consultation "
                    "includes a Biological Assessment and Biological Opinion for Canada lynx, "
                    "bull trout, and grizzly bear in the NCDE primary conservation area. The "
                    "monitoring program, Biennial Monitoring Evaluation Report (BMER), and 2023 "
                    "Administrative Change are incorporated by reference. No motorized use, "
                    "mechanized transport, or stock use are proposed in the Jewel Basin Hiking "
                    "Area. | FW-STD-WTR-01 | New stream diversions and associated ditches shall "
                    "have screens placed on them to prevent capture of fish and other aquatic "
                    "organisms. | Yes | EA section 2.2 says new stream diversions and associated "
                    "ditches shall have screens placed on them to prevent capture of fish and "
                    "other aquatic organisms. |"
                ),
            )
            rule_pack_path = _write_flathead_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="flathead-compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                forest_unit_id="flathead-nf",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "flathead_nf")
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertTrue(forest_plan["component_evaluation"]["validation_passed"])
            self.assertTrue(forest_plan["component_evaluation"]["reviewer_ready"])
            context = json.loads(Path(forest_plan["context_path"]).read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["name"] for entry in context["project_location_signals"]],
                ["Hungry Horse-Glacier View Ranger District"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["geographic_areas"]],
                ["Hungry Horse Geographic Area"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["management_areas"]],
                ["Jewel Basin Hiking Area"],
            )
            overlay_names = [entry["name"] for entry in context["overlays"]]
            self.assertIn("Inventoried Roadless Area", overlay_names)
            self.assertIn("Jewel Basin Recommended Wilderness Area", overlay_names)
            self.assertEqual(
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
                {
                    "support-feis-plan-context",
                    "support-rod-decision-basis",
                    "support-esa-biological-assessment",
                    "support-bull-trout-biological-opinion",
                    "support-grizzly-biological-opinion",
                    "support-monitoring-program",
                    "support-bmer-currentness",
                    "support-administrative-change",
                },
            )

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertEqual(
                forest_plan_gate["details"]["scope_status"],
                "flathead_nf",
            )
            self.assertTrue(forest_plan_gate["details"]["component_reviewer_ready"])

    def test_custer_component_adjudication_resolves_real_ea_omission_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))
            review_id = "custer-adjudicated-omission-unit"

            initial = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            self.assertFalse(initial.summary["reviewer_ready"])
            review_dir = output_dir / "reviews" / review_id
            queue = json.loads(
                (review_dir / "forest_plan_reviewer_resolution_queue.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(queue["item_count"], 1)
            _write_component_adjudication_eval(
                review_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                passed=True,
                queue_item_count=1,
            )

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertFalse(forest_plan["component_evaluation"]["reviewer_ready"])
            self.assertTrue(forest_plan["component_adjudication"]["reviewer_ready"])
            self.assertEqual(
                forest_plan["component_adjudication"]["real_ea_omission_count"],
                1,
            )
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertFalse(forest_plan_gate["details"]["component_reviewer_ready"])
            self.assertTrue(
                forest_plan_gate["details"]["component_adjudication_reviewer_ready"]
            )
            self.assertEqual(
                forest_plan_gate["details"]["component_adjudication_system_miss_count"],
                0,
            )

    def test_custer_component_adjudication_accepts_reviewed_system_miss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))
            review_id = "custer-system-miss-adjudication-unit"
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            review_dir = output_dir / "reviews" / review_id
            _write_component_adjudication_eval(
                review_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                passed=True,
                queue_item_count=1,
                real_ea_omission_count=0,
                system_miss_count=1,
            )

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertTrue(forest_plan["component_adjudication"]["reviewer_ready"])
            self.assertEqual(forest_plan["component_adjudication"]["failed_checks"], [])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(
                forest_plan_gate["details"]["component_adjudication_reviewer_ready"]
            )
            self.assertEqual(
                forest_plan_gate["details"]["component_adjudication_system_miss_count"],
                1,
            )

    def test_custer_compliance_review_fails_closed_on_stale_component_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            inventory_path = (
                output_dir
                / "derived"
                / source_set_id
                / "forest_plan_components"
                / "component_inventory.json"
            )
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["source_set_id"] = "source-set-stale"
            for component in inventory["components"]:
                component["source_set_id"] = "source-set-stale"
            inventory_path.write_text(
                json.dumps(inventory, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area. No new permanent or temporary roads "
                    "are proposed."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="custer-stale-component-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertFalse(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "custer_gallatin")
            self.assertFalse(forest_plan["reviewer_ready"])
            self.assertFalse(forest_plan["component_evaluation"]["validation_passed"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertFalse(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertFalse(forest_plan_gate["details"]["component_reviewer_ready"])
            self.assertFalse(
                forest_plan_gate["details"]["component_inventory_coverage_passed"]
            )
