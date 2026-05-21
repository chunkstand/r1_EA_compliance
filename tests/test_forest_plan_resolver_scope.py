from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from tests.support.forest_plan_resolver_common import (
    _check,
    _names,
    _readiness_check,
    _write_package,
    _write_resolver_profile_config,
)
from tests.support.forest_plan_resolver_custer_fixtures import _build_custer_source_library
from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver


class ForestPlanResolverScopeTests(unittest.TestCase):
    def test_other_configured_profiles_are_out_of_scope_for_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                extra_profile_updates={
                    "forest_unit_id": "profile-two-nf",
                    "forest_unit_names": ["Profile Two National Forest"],
                    "ambiguous_unit_terms": ["Profile Two"],
                },
            )
            package_path = _write_package(
                Path(tmp),
                "The proposed action is on Profile Two National Forest.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="other-configured-profile",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Profile Two National Forest")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_scope_resolution_uses_profile_unit_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Profile Forest"],
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The East Crazy project is on Profile Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-name-driven",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Profile Forest")
            self.assertTrue(result.summary["reviewer_ready"])

    def test_profile_scope_ignores_incidental_other_forest_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "The project area is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "The Land Management Plan consistency table applies to the proposed action.",
                        "Quiet nonmotorized recreation opportunities predominate.",
                        "No new permanent or temporary roads are proposed.",
                        "References: USDA Forest Service. 2016. Flathead National Forest methods paper.",
                        (
                            "The Custer Gallatin National Forest coordinates stewardship with "
                            "the Beaverhead-Deerlodge National Forest for distant wilderness areas."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-incidental-other-forests",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertEqual(
                [item["reason"] for item in context["unresolved_mentions"]],
                [],
            )
            self.assertTrue(result.summary["reviewer_ready"])

    def test_profile_scope_uses_header_location_and_excludes_reference_district(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "## South Plateau Area Landscape Treatment Project",
                        "## Hebgen Lake Ranger District, Custer Gallatin National Forest",
                        "The project area is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "Quiet nonmotorized recreation opportunities predominate.",
                        "No new permanent or temporary roads are proposed.",
                        "The backcountry area is not suitable for motorized transport or mechanized transport.",
                        (
                            "References: Final Report, Work Assignment 2-73. Forest Service "
                            "Files, Bozeman Ranger District, Bozeman, MT."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-header-location-reference-district",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertEqual(
                {
                    evidence["evidence_role"]
                    for evidence in context["forest_unit"]["package_evidence"]
                },
                {"project_location"},
            )
            self.assertEqual(
                _names(context["project_location_signals"]),
                ["Hebgen Lake Ranger District"],
            )
            background_names = {
                evidence["name"] for evidence in context["background_location_mentions"]
            }
            self.assertIn("Bozeman Ranger District", background_names)
            self.assertTrue(
                all(
                    evidence["evidence_role"] == "background_reference"
                    for evidence in context["background_location_mentions"]
                    if evidence["name"] == "Bozeman Ranger District"
                )
            )
            self.assertTrue(result.summary["reviewer_ready"])

    def test_reference_list_district_does_not_resolve_project_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = _write_package(
                Path(tmp),
                (
                    "References: Final Report, Work Assignment 2-73. Forest Service Files, "
                    "Bozeman Ranger District, Bozeman, MT. Gallatin National Forest. 1987. "
                    "Gallatin National Forest Plan."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="reference-district-not-location",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "ambiguous")
            self.assertEqual(context["project_location_signals"], [])
            background = {
                evidence["name"]: evidence["evidence_role"]
                for evidence in context["background_location_mentions"]
            }
            self.assertEqual(background["Bozeman Ranger District"], "background_reference")
            self.assertTrue(context["needs_reviewer_resolution"])

    def test_unselected_profile_district_does_not_resolve_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                extra_profile_updates={
                    "forest_unit_id": "profile-two-nf",
                    "forest_unit_names": ["Profile Two National Forest"],
                    "ambiguous_unit_terms": ["Profile Two"],
                    "ranger_district_terms": [
                        {
                            "entry_id": "district-profile-two",
                            "category": "district",
                            "name": "Profile Two Ranger District",
                            "aliases": [],
                        }
                    ],
                },
            )
            package_path = _write_package(
                Path(tmp),
                "The proposed action is on Profile Two Ranger District.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="unselected-profile-district",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "ambiguous")
            self.assertIsNone(context["forest_unit"])
            self.assertEqual(context["project_location_signals"], [])

    def test_profile_scope_stays_ambiguous_when_other_forest_is_operative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest and "
                    "the Beaverhead-Deerlodge National Forest."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="profile-operative-other-forest",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "ambiguous")
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertEqual(
                context["unresolved_mentions"][0]["reason"],
                "multiple_forest_units_mentioned",
            )

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

            readiness = result.summary["retrieval_readiness"]["required_source_records"]
            self.assertEqual(
                readiness["required_source_record_ids"],
                [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                ],
            )
            self.assertEqual(readiness["missing_source_record_ids"], [])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_resolves_custer_gallatin_geographic_and_management_areas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The East Crazy project is on the Custer Gallatin National Forest.",
                        "It is on the Bozeman Ranger District.",
                        "The EA identifies the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "Trail work also crosses the Hyalite Recreation Emphasis Area.",
                        "Mapped Inventoried Roadless Area direction is reviewed.",
                        (
                            "Recreation and access section: quiet nonmotorized recreation "
                            "opportunities predominate in the Crazy Mountains Backcountry Area."
                        ),
                        (
                            "The backcountry area is not suitable for motorized transport or "
                            "mechanized transport."
                        ),
                        "No new permanent or temporary roads are proposed.",
                        (
                            "Blacktail Peak Backcountry Area | No | The geographic area to which "
                            "this component applies is not part of the project area."
                        ),
                        "Pryor Mountains Geographic Area | No | The project is not in this area.",
                        (
                            "Research Natural Area | FW-STD-RNA-01 | No | This component is "
                            "forestwide and would apply to the project area, but there are no "
                            "research natural areas in the project area or affected by the project."
                        ),
                        (
                            "FW-DC-RNA-01 | Ecological processes that support functional and "
                            "structural patterns of research natural area ecosystems are present "
                            "and functioning to sustain the species and ecological conditions for "
                            "which the research natural area was established. "
                            + " ".join(["supporting context"] * 28)
                            + " | No | This component is forestwide and would apply to the "
                            "project area, but there are no research natural areas in the project "
                            "area or affected by the project."
                        ),
                        (
                            "FW-DC-DWSR-01 | Designated rivers retain their free-flowing "
                            "condition. | No | This component is forestwide and would apply "
                            "to the project area, but there are no designated rivers in the "
                            "project area or affected by the project."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-positive",
            )

            self.assertTrue(result.context_path.exists())
            self.assertTrue(result.validation_path.exists())
            self.assertTrue(result.summary["reviewer_ready"])
            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertEqual(
                [record["source_record_id"] for record in context["source_records"]],
                [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ],
            )
            self.assertTrue(context["source_record_readiness"]["ready"])
            self.assertEqual(
                _names(context["geographic_areas"]),
                ["Bridger, Bangtail, and Crazy Mountains Geographic Area"],
            )
            self.assertEqual(
                _names(context["management_areas"]),
                ["Crazy Mountains Backcountry Area", "Hyalite Recreation Emphasis Area"],
            )
            self.assertEqual(_names(context["overlays"]), ["Inventoried Roadless Area"])
            self.assertEqual(_names(context["project_location_signals"]), ["Bozeman Ranger District"])
            for collection in (
                context["geographic_areas"],
                context["management_areas"],
                context["overlays"],
            ):
                for entry in collection:
                    self.assertEqual(entry["resolution_status"], "resolved")
                    self.assertTrue(entry["package_evidence"])
                    self.assertTrue(entry["plan_source_evidence"])
            self.assertIn(
                "R1PLAN-custer-gallatin-nf-05",
                {entry["source_record_id"] for entry in context["supporting_plan_evidence"]},
            )
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

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

    def test_custer_scope_without_area_needs_reviewer_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "The proposed action is on the Custer Gallatin National Forest.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-no-area",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertEqual(context["geographic_areas"], [])
            self.assertEqual(context["management_areas"], [])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(validation["passed"])
            self.assertFalse(_check(validation, "custer_scope_has_resolved_area")["passed"])

    def test_ambiguous_gallatin_package_is_not_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = _write_package(
                Path(tmp),
                "The project near Gallatin includes road and trail maintenance.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="ambiguous-gallatin",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "ambiguous")
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertEqual(context["source_records"], [])
            self.assertEqual(context["geographic_areas"], [])
            self.assertEqual(context["management_areas"], [])
            self.assertEqual(context["unresolved_mentions"][0]["reason"], "ambiguous_forest_unit")

    def test_non_custer_package_is_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = _write_package(
                Path(tmp),
                "The project is on the Beaverhead-Deerlodge National Forest.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="non-custer",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_custer_gallatin")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertEqual(context["source_records"], [])
            self.assertTrue(result.summary["reviewer_ready"])
