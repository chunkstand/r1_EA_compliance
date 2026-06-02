from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from tests.support.forest_plan_resolver_common import (
    _check,
    _names,
    _write_package,
    _write_resolver_profile_config,
)
from tests.support.forest_plan_resolver_custer_fixtures import _build_custer_source_library
from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver
from usfs_r1_ea_sources.forest_plan_resolver_location import _location_evidence_role
from usfs_r1_ea_sources.forest_plan_resolver_scope import (
    _management_area_entry,
    _management_area_plan_evidence,
    _package_management_area_evidence_by_identifier,
)


class ForestPlanResolverScopeTests(unittest.TestCase):
    def test_management_area_detection_does_not_treat_treatment_unit_rows_as_mas(
        self,
    ) -> None:
        evidence = _package_management_area_evidence_by_identifier(
            [
                {
                    "chunk_id": "chunk-table",
                    "text": (
                        "The inventoried roadless areas where treatments are proposed are "
                        "management areas 1b, 2b, 5b, 5c and 6a. Table 6. Proposed "
                        "vegetation treatments Unit Acres Prescription Treatment Method "
                        "Management Area 48 24 Seed Tree Tractor 6b 107 1 Understory "
                        "Removal Hand 7."
                    ),
                }
            ]
        )

        self.assertEqual(sorted(evidence), ["1b", "2b", "5b", "5c", "6a"])
        self.assertNotIn("48", evidence)
        self.assertNotIn("107", evidence)

    def test_management_area_plan_evidence_accepts_lettered_area_ranges(self) -> None:
        rows = [
            {
                "chunk_id": "chunk-range",
                "evidence_span": {
                    "text": (
                        "In all backcountry areas (management areas 5a through 5d), "
                        "mechanized transport is suitable."
                    )
                },
            }
        ]

        entry = _management_area_entry(
            identifier="5b",
            source_record_id="R1PLAN-test",
        )

        evidence = _management_area_plan_evidence(
            entry=entry,
            plan_source_rows=rows,
            limit=3,
        )

        self.assertEqual([row["chunk_id"] for row in evidence], ["chunk-range"])

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

    def test_decision_notice_title_page_location_does_not_require_profile_district(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Lolo National Forest"],
            )
            profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            profiles["known_other_forest_units"] = [
                unit
                for unit in profiles["known_other_forest_units"]
                if unit["forest_unit_id"] != "lolo-nf"
            ]
            profiles["profiles"] = [
                profile
                for profile in profiles["profiles"]
                if profile["forest_unit_id"] != "lolo-nf"
            ]
            profiles["profiles"][0]["ambiguous_unit_terms"] = ["Lolo"]
            profiles["profiles"][0]["ranger_district_terms"] = []
            profiles_path.write_text(
                json.dumps(profiles, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        (
                            "North Seeley Wildland Urban Interface - Highway 83 Project "
                            "Decision Notice and Finding of No Significant Impact "
                            "Seeley Lake Ranger District Lolo National Forest "
                            "Missoula and Powell County, Montana July 2025"
                        ),
                        (
                            "The project area is in the Bridger, Bangtail, and Crazy Mountains "
                            "Geographic Area."
                        ),
                        (
                            "The Forest Service did not adequately show that the Round Star "
                            "project complies with the law. The Round Star project is located "
                            "on the Flathead National Forest."
                        ),
                        (
                            "The Eastside Assessment is used on the Helena-Lewis and Clark "
                            "National Forest, not the Lolo National Forest."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="dn-title-page-profile-location",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Lolo National Forest")
            self.assertEqual(
                context["forest_unit"]["resolution_basis"],
                "decision_notice_fonsi_title_page",
            )
            self.assertNotIn(
                "multiple_forest_units_mentioned",
                [item["reason"] for item in context["unresolved_mentions"]],
            )
            self.assertEqual(
                _names(context["project_location_signals"]),
                ["Seeley Lake Ranger District"],
            )
            title_page_location = context["title_page_project_location"]
            self.assertEqual(title_page_location["forest_unit"]["name"], "Lolo National Forest")
            self.assertEqual(
                _names(title_page_location["ranger_districts"]),
                ["Seeley Lake Ranger District"],
            )
            self.assertEqual(
                title_page_location["counties"],
                ["Missoula County", "Powell County"],
            )
            self.assertEqual(title_page_location["state"], "Montana")

    def test_proposed_action_title_page_resolves_plural_districts_and_state_abbreviation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Profile National Forest"],
            )
            package_path = _write_package(
                Path(tmp),
                (
                    "West Reservoir: Proposed Action\n"
                    "The West Reservoir Project is located within the Hungry Horse "
                    "and Spotted Bear Ranger Districts of the Profile National Forest. "
                    "The project area is within Flathead County, MT."
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="proposed-action-title-page-admin-location",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            title_page_location = context["title_page_project_location"]
            self.assertEqual(title_page_location["forest_unit"]["name"], "Profile National Forest")
            self.assertEqual(
                _names(title_page_location["ranger_districts"]),
                ["Hungry Horse Ranger District", "Spotted Bear Ranger District"],
            )
            self.assertEqual(title_page_location["counties"], ["Flathead County"])
            self.assertEqual(title_page_location["state"], "Montana")

    def test_title_page_county_parser_does_not_treat_district_as_county(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Profile National Forest"],
            )
            package_path = _write_package(
                Path(tmp),
                (
                    "Environmental Assessment and Finding of No Significant Impact "
                    "Profile National Forest, Ashland Ranger District, Powder River "
                    "and Rosebud Counties, Montana"
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="title-page-county-list",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            title_page_location = context["title_page_project_location"]
            self.assertEqual(
                _names(title_page_location["ranger_districts"]),
                ["Ashland Ranger District"],
            )
            self.assertEqual(
                title_page_location["counties"],
                ["Powder River County", "Rosebud County"],
            )
            self.assertEqual(title_page_location["state"], "Montana")

    def test_title_page_forest_name_matching_accepts_hyphen_and_space_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Profile Perce-Clearwater National Forests"],
            )
            package_path = _write_package(
                Path(tmp),
                (
                    "Dead Laundry Draft Decision Notice and Finding of No Significant Impact "
                    "U.S. Forest Service Profile-Perce Clearwater National Forests: "
                    "North Fork Ranger District April 2023 Clearwater County, Idaho"
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="hyphen-variant-title-page",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            title_page_location = context["title_page_project_location"]
            self.assertEqual(
                title_page_location["forest_unit"]["name"],
                "Profile Perce-Clearwater National Forests",
            )
            self.assertEqual(
                _names(title_page_location["ranger_districts"]),
                ["North Fork Ranger District"],
            )
            self.assertEqual(title_page_location["counties"], ["Clearwater County"])
            self.assertEqual(title_page_location["state"], "Idaho")

    def test_package_detected_management_areas_resolve_against_selected_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                primary_plan_text=(
                    "The Custer Gallatin selected Forest Plan contains first-class "
                    "management area direction. MAI contains non-commercial forest "
                    "direction. Management Area 9 establishes concentrated "
                    "recreation management direction. Management Area 16 identifies suitable "
                    "timber-production lands. Management Area 21 contains old-growth forest "
                    "direction. Management Area 24 contains high visual sensitivity direction. "
                    "Management Area 25 contains partial-retention visual quality direction. "
                    "Management Area 18, Management Area 22, and Management Area 23 contain "
                    "big-game winter range direction."
                ),
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        (
                            "The EA identifies Forest Plan Management Areas in the project: "
                            "MA 1, Management Area 9 (MA-9), Management Area 16 (MA 16), "
                            "MA 21, MA 24, and MA 25."
                        ),
                        "The project area does not fall within MAs 18, 22, or 23.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="package-detected-management-areas",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(
                _names(context["management_areas"]),
                [
                    "Management Area 1",
                    "Management Area 9",
                    "Management Area 16",
                    "Management Area 21",
                    "Management Area 24",
                    "Management Area 25",
                ],
            )
            for entry in context["management_areas"]:
                self.assertEqual(
                    entry["resolution_basis"],
                    "ea_detected_management_area_with_plan_source_evidence",
                )
                self.assertTrue(entry["package_evidence"])
                self.assertTrue(entry["plan_source_evidence"])
                self.assertEqual(entry["source_record_id"], "R1PLAN-custer-gallatin-nf-02")
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])
            self.assertTrue(
                _check(validation, "detected_management_areas_found_in_selected_plan")[
                    "passed"
                ]
            )

    def test_package_detected_management_area_missing_from_selected_plan_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                primary_plan_text=(
                    "The Custer Gallatin selected Forest Plan contains Management Area 9 "
                    "direction, but not the package's unsupported management area."
                ),
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "The EA identifies project work in Management Area 99.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="missing-management-area-plan-evidence",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertEqual(context["management_areas"], [])
            unresolved = [
                item
                for item in context["unresolved_mentions"]
                if item["reason"] == "management_area_missing_plan_source_evidence"
            ]
            self.assertEqual(len(unresolved), 1)
            self.assertEqual(unresolved[0]["name"], "Management Area 99")
            self.assertEqual(unresolved[0]["source_record_id"], "R1PLAN-custer-gallatin-nf-02")
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(validation["passed"])
            self.assertFalse(
                _check(validation, "detected_management_areas_found_in_selected_plan")[
                    "passed"
                ]
            )

    def test_profile_scope_ignores_project_external_other_forest_locations(self) -> None:
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
                        "No new permanent or temporary roads are proposed.",
                        (
                            "There are no populations or individuals within the project area. "
                            "The closest location is on the Bitterroot National Forest within the "
                            "Sapphire Range."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-project-external-other-forest",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertEqual(
                [item["reason"] for item in context["unresolved_mentions"]],
                [],
            )
            background_names = {
                evidence["name"] for evidence in context["background_location_mentions"]
            }
            self.assertIn("Bitterroot National Forest", background_names)
            self.assertTrue(result.summary["reviewer_ready"])

    def test_profile_scope_ignores_cross_forest_comparison_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is on the Bozeman Ranger District.",
                        "The project area is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        (
                            "A cited report identifies habitat conditions throughout the "
                            "Bitterroot National Forest and Lolo National Forest and parts of "
                            "the Beaverhead-Deerlodge National Forest. Those comparisons provide "
                            "a foundation for cumulative effects analysis both within the project "
                            "area and considering regional connectivity."
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-cross-forest-comparison-reference",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertNotIn(
                "multiple_forest_units_mentioned",
                [item["reason"] for item in context["unresolved_mentions"]],
            )
            background_names = {
                evidence["name"] for evidence in context["background_location_mentions"]
            }
            self.assertIn("Bitterroot National Forest", background_names)
            self.assertIn("Lolo National Forest", background_names)
            self.assertIn("Beaverhead-Deerlodge National Forest", background_names)
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

    def test_literature_review_other_forest_reference_is_background(self) -> None:
        evidence = {
            "category": "forest_unit",
            "matched_alias": "Kootenai National Forest",
            "name": "Kootenai National Forest",
            "title": "LacyLemooshEALiteratureReview.pdf",
            "evidence_span": {
                "text": (
                    "USDA Forest Service, 2017c. Starry Goat Draft Environmental Impact "
                    "Statement. Three Rivers Ranger District, Kootenai National Forest, July "
                    "2017. Not used This is a NEPA document, not a research article. Does not "
                    "change the analysis of this project."
                )
            },
            "provenance": {
                "artifact_path": "Final EA/LacyLemooshEALiteratureReview.pdf",
            },
        }

        self.assertEqual(_location_evidence_role(evidence), "background_reference")
        evidence["evidence_span"]["text"] = (
            "Considered This is a field review of the Bitterroot National Forest Burned Area "
            "Recovery Project. BMPs are constantly being updated to reflect current science."
        )
        evidence["matched_alias"] = "Bitterroot National Forest"
        evidence["name"] = "Bitterroot National Forest"
        self.assertEqual(_location_evidence_role(evidence), "background_reference")

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

    def test_profile_district_scope_ignores_admin_boundary_map_forest_mentions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Selected National Forest"],
            )
            profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            profiles["profiles"][0]["ambiguous_unit_terms"] = ["Selected"]
            profiles["profiles"][0]["ranger_district_terms"] = [
                {
                    "entry_id": "district-selected",
                    "category": "district",
                    "name": "Selected Ranger District",
                    "aliases": ["Selected RD"],
                }
            ]
            profiles_path.write_text(
                json.dumps(profiles, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        (
                            "Lolo National Forest Flathead National Forest Selected Front "
                            "Project Boundary National Forest Administrative Boundary Major Roads."
                        ),
                        (
                            "Appendix map: Lolo National Forest Selected National Forest. "
                            "This map is intended to depict physical features and may not be "
                            "used to determine title, ownership, legal boundaries, legal "
                            "jurisdiction, including jurisdiction over roads or trails."
                        ),
                        (
                            "The majority of the Lolo Creek IRA is within the Lolo National "
                            "Forest, though this small portion is within Selected National "
                            "Forest."
                        ),
                        (
                            "Selected Front Project Opportunity Areas Selected RD "
                            "Selected National Forest."
                        ),
                        (
                            "The project area is in the Bridger, Bangtail, and Crazy Mountains "
                            "Geographic Area."
                        ),
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "No new permanent or temporary roads are proposed.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-admin-boundary-map",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Selected National Forest")
            self.assertEqual(
                _names(context["project_location_signals"]),
                ["Selected Ranger District"],
            )
            self.assertNotIn(
                "multiple_forest_units_mentioned",
                [item["reason"] for item in context["unresolved_mentions"]],
            )
            background_names = {
                evidence["name"] for evidence in context["background_location_mentions"]
            }
            self.assertIn("Lolo National Forest", background_names)
            self.assertIn("Flathead National Forest", background_names)


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
