from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver

from tests.support.forest_plan_tracking_profile_fixtures import (
    TRACKING_PROFILE_IDS,
    build_tracking_profile_source_library,
    custer_hard_negative_package_text,
    expected_scope_status,
    non_selected_non_custer_hard_negative_package_text,
    scope_positive_package_text,
    scope_positive_with_ambiguous_context_text,
    tracking_profile,
)


class TrackingForestPlanProfileResolverTests(unittest.TestCase):
    def test_tracking_profiles_resolve_selected_scope_without_claiming_reviewer_ready(
        self,
    ) -> None:
        for forest_unit_id in TRACKING_PROFILE_IDS:
            with self.subTest(forest_unit_id=forest_unit_id):
                profile = tracking_profile(forest_unit_id)
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp) / "source_library"
                    source_set_id, component_inventory_path = build_tracking_profile_source_library(
                        output_dir,
                        forest_unit_id=forest_unit_id,
                    )
                    package_path = _write_package(
                        Path(tmp),
                        scope_positive_package_text(forest_unit_id),
                    )

                    result = run_forest_plan_resolver(
                        package_path=package_path,
                        output_dir=output_dir,
                        forest_unit_id=forest_unit_id,
                        source_set_id=source_set_id,
                        review_id=f"{forest_unit_id}-tracking-positive",
                        component_inventory_path=component_inventory_path,
                    )

                    context = json.loads(result.context_path.read_text(encoding="utf-8"))
                    self.assertEqual(context["scope_status"], expected_scope_status(forest_unit_id))
                    self.assertEqual(context["forest_unit"]["name"], profile.forest_unit_names[0])
                    self.assertEqual(
                        len(context["source_records"]),
                        len(profile.required_source_record_ids),
                    )
                    self.assertEqual(context["geographic_areas"], [])
                    self.assertEqual(context["management_areas"], [])
                    self.assertEqual(context["overlays"], [])
                    self.assertTrue(context["needs_reviewer_resolution"])
                    self.assertFalse(result.summary["validation_passed"])
                    self.assertFalse(result.summary["reviewer_ready"])
                    self.assertTrue(result.summary["component_evaluation"]["validation_passed"])
                    self.assertEqual(
                        result.summary["component_evaluation"]["finding_status_counts"],
                        {"needs_reviewer_resolution": 1},
                    )

    def test_tracking_profiles_keep_selected_scope_when_ambiguous_short_unit_is_present(
        self,
    ) -> None:
        for forest_unit_id in TRACKING_PROFILE_IDS:
            with self.subTest(forest_unit_id=forest_unit_id):
                profile = tracking_profile(forest_unit_id)
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp) / "source_library"
                    source_set_id, component_inventory_path = build_tracking_profile_source_library(
                        output_dir,
                        forest_unit_id=forest_unit_id,
                    )
                    package_path = _write_package(
                        Path(tmp),
                        scope_positive_with_ambiguous_context_text(forest_unit_id),
                    )

                    result = run_forest_plan_resolver(
                        package_path=package_path,
                        output_dir=output_dir,
                        forest_unit_id=forest_unit_id,
                        source_set_id=source_set_id,
                        review_id=f"{forest_unit_id}-tracking-ambiguous-positive",
                        component_inventory_path=component_inventory_path,
                    )

                    context = json.loads(result.context_path.read_text(encoding="utf-8"))
                    self.assertEqual(context["scope_status"], expected_scope_status(forest_unit_id))
                    self.assertEqual(context["forest_unit"]["name"], profile.forest_unit_names[0])
                    self.assertTrue(context["needs_reviewer_resolution"])
                    self.assertFalse(result.summary["reviewer_ready"])
                    self.assertFalse(result.summary["validation_passed"])

    def test_tracking_profiles_reject_custer_gallatin_scope_as_hard_negative(self) -> None:
        for forest_unit_id in TRACKING_PROFILE_IDS:
            with self.subTest(forest_unit_id=forest_unit_id):
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp) / "source_library"
                    source_set_id, _component_inventory_path = build_tracking_profile_source_library(
                        output_dir,
                        forest_unit_id=forest_unit_id,
                    )
                    package_path = _write_package(
                        Path(tmp),
                        custer_hard_negative_package_text(),
                    )

                    result = run_forest_plan_resolver(
                        package_path=package_path,
                        output_dir=output_dir,
                        forest_unit_id=forest_unit_id,
                        source_set_id=source_set_id,
                        review_id=f"{forest_unit_id}-tracking-custer-negative",
                    )

                    context = json.loads(result.context_path.read_text(encoding="utf-8"))
                    self.assertEqual(context["scope_status"], "not_selected_forest_unit")
                    self.assertEqual(
                        context["forest_unit"]["name"],
                        "Custer Gallatin National Forest",
                    )
                    self.assertEqual(context["source_records"], [])
                    self.assertEqual(context["supporting_plan_evidence"], [])
                    self.assertTrue(result.summary["reviewer_ready"])
                    self.assertNotIn("component_evaluation", result.summary)

    def test_tracking_profiles_reject_other_covered_profile_scope_as_hard_negative(self) -> None:
        for forest_unit_id in TRACKING_PROFILE_IDS:
            with self.subTest(forest_unit_id=forest_unit_id):
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp) / "source_library"
                    source_set_id, _component_inventory_path = build_tracking_profile_source_library(
                        output_dir,
                        forest_unit_id=forest_unit_id,
                    )
                    package_path = _write_package(
                        Path(tmp),
                        non_selected_non_custer_hard_negative_package_text(),
                    )

                    result = run_forest_plan_resolver(
                        package_path=package_path,
                        output_dir=output_dir,
                        forest_unit_id=forest_unit_id,
                        source_set_id=source_set_id,
                        review_id=f"{forest_unit_id}-tracking-beaverhead-negative",
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
                    self.assertNotIn("component_evaluation", result.summary)


def _write_package(directory: Path, text: str) -> Path:
    package_path = directory / "ea-package.txt"
    package_path.write_text(text, encoding="utf-8")
    return package_path
