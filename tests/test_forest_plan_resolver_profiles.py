from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from tests.support.forest_plan_resolver_common import _names, _write_package
from tests.support.forest_plan_resolver_profile_fixtures import (
    _build_beaverhead_source_library,
    _build_flathead_source_library,
)
from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver


class ForestPlanResolverProfileTests(unittest.TestCase):
    def test_beaverhead_profile_resolves_project_context_and_supporting_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Beaverhead-Deerlodge National Forest.",
                        "It is on the Dillon Ranger District.",
                        "The project area is in the Big Hole Landscape and the West Big Hole Management Area.",
                        "The action overlaps an Inventoried Roadless Area.",
                        (
                            "The EA tiers to the FEIS and references the travel management "
                            "Record of Decision."
                        ),
                        (
                            "ESA consultation includes Biological Assessments and Biological "
                            "Opinions for Canada lynx and grizzly bear."
                        ),
                        "No new permanent or temporary roads are proposed.",
                        (
                            "| BD-STD-WBH-01 | New permanent or temporary roads shall not be "
                            "allowed. | Yes | EA section 2.2 says no new permanent or temporary "
                            "roads are proposed. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-positive",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "beaverhead_deerlodge_nf")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(result.summary["component_evaluation"]["validation_passed"])
            self.assertEqual(_names(context["project_location_signals"]), ["Dillon Ranger District"])
            self.assertEqual(_names(context["geographic_areas"]), ["Big Hole Landscape"])
            self.assertEqual(_names(context["management_areas"]), ["West Big Hole Management Area"])
            self.assertEqual(_names(context["overlays"]), ["Inventoried Roadless Area"])
            self.assertEqual(
                {
                    "support-feis-plan-context",
                    "support-rod-travel-management",
                    "support-lynx-biological-assessment",
                    "support-lynx-biological-opinion",
                    "support-grizzly-biological-assessment",
                    "support-grizzly-biological-opinion",
                },
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
            )

    def test_beaverhead_management_area_and_overlay_resolve_without_supporting_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Beaverhead-Deerlodge National Forest.",
                        "It is on the Dillon Ranger District.",
                        "The project area is in the Big Hole Landscape and the West Big Hole Management Area.",
                        "The action overlaps an Inventoried Roadless Area.",
                        "No new permanent or temporary roads are proposed.",
                        (
                            "| BD-STD-WBH-01 | New permanent or temporary roads shall not be "
                            "allowed. | Yes | EA section 2.2 says no new permanent or temporary "
                            "roads are proposed. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-management-area-positive",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(context["scope_status"], "beaverhead_deerlodge_nf")
            self.assertEqual(_names(context["geographic_areas"]), ["Big Hole Landscape"])
            self.assertEqual(_names(context["management_areas"]), ["West Big Hole Management Area"])
            self.assertEqual(_names(context["overlays"]), ["Inventoried Roadless Area"])
            self.assertEqual(context["supporting_plan_evidence"], [])

    def test_beaverhead_supporting_routes_resolve_from_explicit_consultation_cues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Beaverhead-Deerlodge National Forest.",
                        "It is on the Dillon Ranger District in the Big Hole Landscape.",
                        (
                            "The EA tiers to the FEIS and references the travel management "
                            "Record of Decision."
                        ),
                        (
                            "ESA consultation includes Biological Assessments and Biological "
                            "Opinions for Canada lynx and grizzly bear."
                        ),
                        "No new permanent or temporary roads are proposed.",
                        (
                            "| BD-STD-WBH-01 | New permanent or temporary roads shall not be "
                            "allowed. | Yes | EA section 2.2 says no new permanent or temporary "
                            "roads are proposed. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-supporting-routes-positive",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(
                {
                    "support-feis-plan-context",
                    "support-rod-travel-management",
                    "support-lynx-biological-assessment",
                    "support-lynx-biological-opinion",
                    "support-grizzly-biological-assessment",
                    "support-grizzly-biological-opinion",
                },
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
            )

    def test_beaverhead_south_tobacco_scope_ignores_external_forest_comparison(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        (
                            "The South Tobacco Roots project area is on the Madison Ranger "
                            "District of the Beaverhead-Deerlodge National Forest."
                        ),
                        (
                            "The project area is in the South Tobacco Roots portion of the "
                            "Tobacco Root Landscape."
                        ),
                        (
                            "The Helena-Lewis and Clark National Forest has implemented "
                            "cut-pile-burn treatments that are discussed as comparison evidence "
                            "in the project record."
                        ),
                        "No new permanent or temporary roads are proposed.",
                        (
                            "| BD-STD-WBH-01 | New permanent or temporary roads shall not be "
                            "allowed. | Yes | EA section 2.2 says no new permanent or temporary "
                            "roads are proposed. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-south-tobacco-external-comparison",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "beaverhead_deerlodge_nf")
            self.assertEqual(
                _names(context["project_location_signals"]),
                ["Madison Ranger District"],
            )
            self.assertEqual(_names(context["geographic_areas"]), ["Tobacco Root Landscape"])
            self.assertNotIn(
                "multiple_forest_units_mentioned",
                [item["reason"] for item in context["unresolved_mentions"]],
            )

    def test_beaverhead_custer_package_does_not_match_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-custer-hard-negative",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_selected_forest_unit")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertEqual(context["source_records"], [])
            self.assertEqual(context["supporting_plan_evidence"], [])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_beaverhead_flathead_package_does_not_match_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Flathead National Forest in the Hungry Horse "
                    "Geographic Area and the Jewel Basin Hiking Area."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-flathead-hard-negative",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_selected_forest_unit")
            self.assertEqual(context["forest_unit"]["name"], "Flathead National Forest")
            self.assertEqual(context["source_records"], [])
            self.assertEqual(context["supporting_plan_evidence"], [])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_beaverhead_generic_decision_labels_and_lowercase_acronyms_do_not_trigger_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_beaverhead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Beaverhead-Deerlodge National Forest.",
                        "It is on the Dillon Ranger District.",
                        "The project area is in the Big Hole Landscape and the West Big Hole Management Area.",
                        "The action overlaps an Inventoried Roadless Area.",
                        (
                            "The plan consistency table discusses the selected alternative and "
                            "decision basis for the project decision."
                        ),
                        "Field notes say ba and bo are shorthand tags, and travel management continues.",
                        "No new permanent or temporary roads are proposed.",
                        (
                            "| BD-STD-WBH-01 | New permanent or temporary roads shall not be "
                            "allowed. | Yes | EA section 2.2 says no new permanent or temporary "
                            "roads are proposed. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="beaverhead-deerlodge-nf",
                source_set_id=source_set_id,
                review_id="beaverhead-no-broad-trigger",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(context["supporting_plan_evidence"], [])

    def test_flathead_profile_resolves_project_context_and_currentness_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Flathead National Forest.",
                        "It is on the Hungry Horse-Glacier View Ranger District.",
                        "The project area is in the Hungry Horse Geographic Area and the Jewel Basin Hiking Area.",
                        (
                            "The action is adjacent to the Jewel Basin Recommended Wilderness "
                            "Area and an Inventoried Roadless Area."
                        ),
                        (
                            "The EA tiers to the FEIS and references the Record of Decision and "
                            "selected alternative."
                        ),
                        (
                            "ESA consultation includes a Biological Assessment and Biological "
                            "Opinion for Canada lynx, bull trout, and grizzly bear in the NCDE "
                            "primary conservation area."
                        ),
                        (
                            "The plan monitoring program, Biennial Monitoring Evaluation Report "
                            "(BMER), and 2023 Administrative Change are incorporated by reference."
                        ),
                        (
                            "No motorized use, mechanized transport, or stock use are proposed "
                            "in the Jewel Basin Hiking Area."
                        ),
                        (
                            "New stream diversions and associated ditches shall have screens "
                            "placed on them to prevent capture of fish and other aquatic organisms."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-positive",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "flathead_nf")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(result.summary["component_evaluation"]["validation_passed"])
            self.assertEqual(
                _names(context["project_location_signals"]),
                ["Hungry Horse-Glacier View Ranger District"],
            )
            self.assertEqual(
                _names(context["geographic_areas"]),
                ["Hungry Horse Geographic Area"],
            )
            self.assertEqual(
                _names(context["management_areas"]),
                ["Jewel Basin Hiking Area"],
            )
            self.assertIn("Inventoried Roadless Area", _names(context["overlays"]))
            self.assertIn(
                "Jewel Basin Recommended Wilderness Area",
                _names(context["overlays"]),
            )
            self.assertEqual(
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
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
            )

    def test_flathead_supporting_routes_resolve_live_like_support_document_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(
                output_dir,
                document_role_overrides={
                    "R1PLAN-flathead-nf-03": "forest_plan_support",
                    "R1PLAN-flathead-nf-04": "forest_plan_support",
                    "R1PLAN-flathead-nf-06": "forest_plan_support",
                    "R1PLAN-flathead-nf-07": "forest_plan_support",
                    "R1PLAN-flathead-nf-08": "forest_plan_support",
                    "R1PLAN-flathead-nf-16": "forest_plan_support",
                },
                support_document_role_overrides={
                    "R1PLAN-flathead-nf-07": "biological_opinion",
                    "R1PLAN-flathead-nf-16": "biological_opinion",
                },
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Flathead National Forest.",
                        "It is on the Hungry Horse-Glacier View Ranger District.",
                        (
                            "The project area is in the Hungry Horse Geographic Area and the "
                            "Jewel Basin Hiking Area."
                        ),
                        (
                            "The action is adjacent to the Jewel Basin Recommended Wilderness "
                            "Area and an Inventoried Roadless Area."
                        ),
                        (
                            "The EA tiers to the FEIS and references the Record of Decision."
                        ),
                        (
                            "ESA consultation includes a Biological Assessment and Biological "
                            "Opinion for Canada lynx, bull trout, and grizzly bear in the NCDE "
                            "primary conservation area."
                        ),
                        (
                            "The plan monitoring program, Biennial Monitoring Evaluation Report "
                            "(BMER), and 2023 Administrative Change are incorporated by reference."
                        ),
                        (
                            "No motorized use, mechanized transport, or stock use are proposed "
                            "in the Jewel Basin Hiking Area."
                        ),
                        (
                            "New stream diversions and associated ditches shall have screens "
                            "placed on them to prevent capture of fish and other aquatic organisms."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-live-like-support-roles",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_by_route = {
                entry["route_id"]: entry for entry in context["supporting_plan_evidence"]
            }
            self.assertTrue(result.summary["validation_passed"])
            self.assertFalse(context["needs_reviewer_resolution"])
            for route_id in (
                "support-feis-plan-context",
                "support-rod-decision-basis",
                "support-esa-biological-assessment",
                "support-bull-trout-biological-opinion",
                "support-grizzly-biological-opinion",
                "support-monitoring-program",
            ):
                self.assertGreater(len(supporting_by_route[route_id]["plan_source_evidence"]), 0)

    def test_flathead_generic_decision_labels_and_lowercase_acronyms_do_not_trigger_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Flathead National Forest.",
                        "It is on the Hungry Horse-Glacier View Ranger District.",
                        "The project area is in the Hungry Horse Geographic Area and the Jewel Basin Hiking Area.",
                        "The action overlaps an Inventoried Roadless Area.",
                        (
                            "The plan consistency table discusses the selected alternative and "
                            "decision basis for the project decision."
                        ),
                        "Field notes say ba and bo are shorthand tags, and monitoring continues.",
                        (
                            "No motorized use, mechanized transport, or stock use are proposed "
                            "in the Jewel Basin Hiking Area."
                        ),
                        (
                            "New stream diversions and associated ditches shall have screens "
                            "placed on them to prevent capture of fish and other aquatic organisms."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-no-broad-trigger",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(context["supporting_plan_evidence"], [])

    def test_flathead_currentness_routes_resolve_from_explicit_monitoring_cues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Flathead National Forest.",
                        "It is on the Hungry Horse-Glacier View Ranger District.",
                        "The project area is in the Hungry Horse Geographic Area and the Jewel Basin Hiking Area.",
                        (
                            "The monitoring program, Biennial Monitoring Evaluation Report "
                            "(BMER), and 2023 Administrative Change are incorporated by reference."
                        ),
                        (
                            "No motorized use, mechanized transport, or stock use are proposed "
                            "in the Jewel Basin Hiking Area."
                        ),
                        (
                            "New stream diversions and associated ditches shall have screens "
                            "placed on them to prevent capture of fish and other aquatic organisms."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-currentness-positive",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(
                {
                    "support-monitoring-program",
                    "support-bmer-currentness",
                    "support-administrative-change",
                },
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
            )

    def test_flathead_generic_monitoring_text_does_not_trigger_currentness_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Flathead National Forest.",
                        "It is on the Hungry Horse-Glacier View Ranger District.",
                        "The project area is in the Hungry Horse Geographic Area and the Jewel Basin Hiking Area.",
                        (
                            "The action is adjacent to the Jewel Basin Recommended Wilderness "
                            "Area and an Inventoried Roadless Area."
                        ),
                        (
                            "No motorized use, mechanized transport, or stock use are proposed "
                            "in the Jewel Basin Hiking Area."
                        ),
                        (
                            "New stream diversions and associated ditches shall have screens "
                            "placed on them to prevent capture of fish and other aquatic organisms."
                        ),
                        "The EA tiers to the FEIS and references the Record of Decision.",
                        (
                            "ESA consultation includes a Biological Assessment and Biological "
                            "Opinion for Canada lynx, bull trout, and grizzly bear."
                        ),
                        "The monitoring section discusses seasonal data and visitor monitoring.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-no-currentness-trigger",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(
                {
                    "support-feis-plan-context",
                    "support-rod-decision-basis",
                    "support-esa-biological-assessment",
                    "support-bull-trout-biological-opinion",
                    "support-grizzly-biological-opinion",
                },
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
            )

    def test_flathead_custer_package_does_not_match_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-custer-hard-negative",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_selected_forest_unit")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertEqual(context["source_records"], [])
            self.assertEqual(context["supporting_plan_evidence"], [])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_flathead_beaverhead_package_does_not_match_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_flathead_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Beaverhead-Deerlodge National Forest in the "
                    "Big Hole Landscape and the West Big Hole Management Area."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="flathead-nf",
                source_set_id=source_set_id,
                review_id="flathead-beaverhead-hard-negative",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_selected_forest_unit")
            self.assertEqual(
                context["forest_unit"]["name"],
                "Beaverhead-Deerlodge National Forest",
            )
            self.assertEqual(context["source_records"], [])
            self.assertEqual(context["supporting_plan_evidence"], [])
            self.assertTrue(result.summary["reviewer_ready"])
