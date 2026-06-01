from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from tests.support.forest_plan_resolver_common import (
    _check,
    _readiness_check,
    _write_package,
    _write_resolver_profile_config,
)
from tests.support.forest_plan_resolver_custer_fixtures import _build_custer_source_library
from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver


class ForestPlanResolverScopeReadinessTests(unittest.TestCase):
    def test_readiness_uses_profile_required_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                missing_source_ids={"R1PLAN-custer-gallatin-nf-07"},
            )
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                required_roles=[
                    "planning_page",
                    "primary_land_management_plan",
                ],
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-required-roles",
                profiles_path=profiles_path,
            )

            retrieval_readiness = result.summary["retrieval_readiness"]
            readiness = retrieval_readiness["required_source_records"]
            self.assertEqual(
                readiness["required_source_record_ids"],
                [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                ],
            )
            self.assertEqual(readiness["missing_source_record_ids"], [])
            self.assertTrue(result.summary["reviewer_ready"])
    def test_allows_partial_custer_slice_when_required_records_are_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir, catalog_source_count=190)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-partial-required",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            readiness = result.summary["retrieval_readiness"]
            self.assertTrue(readiness["passed"])
            self.assertTrue(readiness["required_source_records"]["ready"])
            self.assertTrue(
                _readiness_check(readiness, "retrieval_ready_for_forest_plan_resolver")["passed"]
            )

    def test_allows_missing_planning_page_when_plan_sources_are_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                missing_source_ids={"R1PLAN-custer-gallatin-nf-01"},
            )
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                required_roles=[
                    "planning_page",
                    "primary_land_management_plan",
                ],
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-missing-planning-page",
                profiles_path=profiles_path,
            )

            retrieval_readiness = result.summary["retrieval_readiness"]
            readiness = retrieval_readiness["required_source_records"]
            self.assertEqual(
                readiness["missing_source_record_ids"],
                ["R1PLAN-custer-gallatin-nf-01"],
            )
            self.assertEqual(readiness["blocking_missing_source_record_ids"], [])
            self.assertEqual(
                readiness["optional_missing_source_record_ids"],
                ["R1PLAN-custer-gallatin-nf-01"],
            )
            self.assertTrue(readiness["ready"])
            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(
                _readiness_check(
                    retrieval_readiness,
                    "retrieval_ready_for_forest_plan_resolver",
                )["passed"]
            )

    def test_requires_all_custer_gallatin_source_records_in_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                missing_source_ids={"R1PLAN-custer-gallatin-nf-07"},
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            with self.assertRaisesRegex(ValueError, "required_custer_source_records_indexed"):
                run_forest_plan_resolver(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    review_id="cg-missing-source",
                )

    def test_non_default_profile_missing_required_sources_writes_blocker_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                missing_source_ids={"R1PLAN-custer-gallatin-nf-07"},
            )
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                extra_profile_updates={
                    "forest_unit_id": "selected-profile-nf",
                    "forest_unit_names": ["Selected National Forest"],
                    "ambiguous_unit_terms": ["Selected"],
                },
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on Selected National Forest.",
                        (
                            "The project area is in the Bridger, Bangtail, and Crazy Mountains "
                            "Geographic Area."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                forest_unit_id="selected-profile-nf",
                source_set_id=source_set_id,
                review_id="selected-profile-missing-source",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "selected_profile_nf")
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.summary["validation_passed"])
            readiness = result.summary["retrieval_readiness"]["required_source_records"]
            self.assertEqual(
                readiness["blocking_missing_source_record_ids"],
                ["R1PLAN-custer-gallatin-nf-07"],
            )
            self.assertEqual(
                context["source_record_readiness"]["blocking_missing_source_record_ids"],
                ["R1PLAN-custer-gallatin-nf-07"],
            )

    def test_feis_tiering_and_designated_areas_trigger_feis_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA tiers to the Final Environmental Impact Statement.",
                        "The effects section discusses designated areas and plan allocations.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-feis",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_source_ids = {
                entry["source_record_id"] for entry in context["supporting_plan_evidence"]
            }
            self.assertIn("R1PLAN-custer-gallatin-nf-04", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-05", supporting_source_ids)
            for entry in context["supporting_plan_evidence"]:
                self.assertEqual(entry["resolution_status"], "resolved")
                self.assertTrue(entry["trigger_evidence"])
                self.assertTrue(entry["package_evidence"])
                self.assertTrue(entry["plan_source_evidence"])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_broad_section_labels_and_lowercase_acronyms_do_not_trigger_supporting_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA purpose and need and alternatives sections describe effects.",
                        "A fishing rod was found near the trail and ba and bo are field codes.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-no-broad-trigger",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(context["supporting_plan_evidence"], [])

    def test_project_decision_and_plan_consistency_labels_do_not_trigger_supporting_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The plan consistency table discusses the selected alternative, decision "
                        "basis, objection resolution, and plan approval for the project decision.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-generic-decision-labels",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(context["supporting_plan_evidence"], [])

    def test_uppercase_acronyms_trigger_supporting_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The ROD and FEIS are incorporated by reference.",
                        "ESA consultation includes BA and BO records.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-uppercase-triggers",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_source_ids = {
                entry["source_record_id"] for entry in context["supporting_plan_evidence"]
            }
            self.assertIn("R1PLAN-custer-gallatin-nf-03", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-04", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-06", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-07", supporting_source_ids)
            for entry in context["supporting_plan_evidence"]:
                self.assertTrue(entry["trigger_evidence"])
                self.assertTrue(entry["plan_source_evidence"])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_esa_consultation_triggers_ba_and_bo_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA discusses Endangered Species Act Section 7 consultation.",
                        "The file includes a biological assessment and biological opinion.",
                        "The analysis references critical habitat, incidental take, and reinitiation.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-esa",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_source_ids = {
                entry["source_record_id"] for entry in context["supporting_plan_evidence"]
            }
            self.assertIn("R1PLAN-custer-gallatin-nf-06", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-07", supporting_source_ids)
            self.assertTrue(result.summary["reviewer_ready"])

    def test_triggered_supporting_source_without_evidence_needs_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                weak_supporting_source_ids={
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                },
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA discusses Endangered Species Act Section 7 consultation.",
                        "The file includes a biological assessment and biological opinion.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-weak-esa",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(validation["passed"])
            self.assertFalse(
                _check(
                    validation,
                    "triggered_supporting_plan_evidence_has_source_evidence",
                )["passed"]
            )


if __name__ == "__main__":
    unittest.main()
