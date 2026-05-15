from __future__ import annotations

import csv
from pathlib import Path
import json
import os
import tempfile
import unittest

from usfs_r1_ea_sources.forest_plan_profiles import (
    DEFAULT_FOREST_PLAN_PROFILES_PATH,
    FOREST_PLAN_PROFILES_SCHEMA_VERSION,
    load_forest_plan_profile,
    load_forest_plan_profiles,
)
from usfs_r1_ea_sources.forest_plan_resolver import CUSTER_GALLATIN_PLAN_SOURCE_ID
from usfs_r1_ea_sources.forest_plan_resolver import CUSTER_GALLATIN_REQUIRED_SOURCE_IDS
from usfs_r1_ea_sources.forest_plan_resolver import SUPPORTING_PLAN_EVIDENCE_ROUTES

READINESS_PATH = Path("config/region1_forest_plan_readiness_nepa_3d_v1.json")
REGISTER_PATH = Path("config/r1_forest_plan_document_register_draft.csv")


class ForestPlanProfileTests(unittest.TestCase):
    def test_default_profile_path_is_repo_absolute(self) -> None:
        self.assertTrue(DEFAULT_FOREST_PLAN_PROFILES_PATH.is_absolute())
        self.assertTrue(DEFAULT_FOREST_PLAN_PROFILES_PATH.exists())

    def test_loads_default_profiles_from_non_repo_cwd(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                profiles = load_forest_plan_profiles()
            finally:
                os.chdir(original_cwd)

        self.assertEqual(profiles.get("custer-gallatin-nf").forest_unit_id, "custer-gallatin-nf")

    def test_loads_custer_gallatin_profile_as_data(self) -> None:
        profiles = load_forest_plan_profiles()
        profile = profiles.get("custer-gallatin-nf")

        self.assertEqual(profiles.schema_version, FOREST_PLAN_PROFILES_SCHEMA_VERSION)
        self.assertIn("Custer Gallatin National Forest", profile.forest_unit_names)
        self.assertIn("Gallatin", profile.ambiguous_unit_terms)
        self.assertEqual(profile.active_plan_source_record_id, CUSTER_GALLATIN_PLAN_SOURCE_ID)
        self.assertEqual(profile.required_source_record_ids, CUSTER_GALLATIN_REQUIRED_SOURCE_IDS)
        self.assertEqual(
            profile.source_record_id_for_role("primary_land_management_plan"),
            CUSTER_GALLATIN_PLAN_SOURCE_ID,
        )
        self.assertIn(
            "Beaverhead-Deerlodge National Forest",
            profiles.known_other_forest_units[0].names,
        )

    def test_loads_beaverhead_deerlodge_milestone_5_profile_as_data(self) -> None:
        profile = load_forest_plan_profile("beaverhead-deerlodge-nf")

        self.assertIn("Beaverhead-Deerlodge National Forest", profile.forest_unit_names)
        self.assertEqual(
            profile.active_plan_source_record_id,
            "R1PLAN-beaverhead-deerlodge-nf-02",
        )
        self.assertEqual(
            profile.required_source_record_ids,
            (
                "R1PLAN-beaverhead-deerlodge-nf-01",
                "R1PLAN-beaverhead-deerlodge-nf-02",
                "R1PLAN-beaverhead-deerlodge-nf-03",
                "R1PLAN-beaverhead-deerlodge-nf-04",
                "R1PLAN-beaverhead-deerlodge-nf-05",
                "R1PLAN-beaverhead-deerlodge-nf-18",
                "R1PLAN-beaverhead-deerlodge-nf-22",
                "R1PLAN-beaverhead-deerlodge-nf-24",
                "R1PLAN-beaverhead-deerlodge-nf-19",
                "R1PLAN-beaverhead-deerlodge-nf-23",
                "R1PLAN-beaverhead-deerlodge-nf-25",
            ),
        )
        self.assertEqual(
            profile.source_record_id_for_role("primary_land_management_plan"),
            "R1PLAN-beaverhead-deerlodge-nf-02",
        )
        self.assertEqual(
            profile.source_record_id_for_role("record_of_decision_1"),
            "R1PLAN-beaverhead-deerlodge-nf-04",
        )
        self.assertEqual(
            profile.source_record_id_for_role("biological_opinion_3"),
            "R1PLAN-beaverhead-deerlodge-nf-25",
        )
        self.assertIn(
            "Dillon Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertIn(
            "Big Hole Landscape",
            [entry.name for entry in profile.geographic_area_terms],
        )
        self.assertIn(
            "West Big Hole Management Area",
            [entry.name for entry in profile.management_area_terms],
        )
        self.assertIn(
            "Inventoried Roadless Area",
            [entry.name for entry in profile.overlay_terms],
        )
        self.assertIn(
            "support-feis-plan-context",
            [rule.route_id for rule in profile.supporting_record_trigger_rules],
        )
        self.assertIn(
            "support-lynx-biological-opinion",
            [rule.route_id for rule in profile.supporting_record_trigger_rules],
        )

    def test_flathead_profile_covers_full_register_backed_support_document_contract(self) -> None:
        profile = load_forest_plan_profile("flathead-nf")
        register_rows = _forest_plan_register_rows("flathead-nf")

        self.assertEqual(len(register_rows), 17)
        self.assertEqual(
            {record.source_record_id for record in profile.supporting_source_records},
            {row["proposed_source_record_id"] for row in register_rows},
        )
        self.assertEqual(
            {
                "forest_plan_monitoring_program": "R1PLAN-flathead-nf-08",
                "latest_biennial_monitoring_evaluation_report": "R1PLAN-flathead-nf-09",
                "record_of_decision_cover_letter": "R1PLAN-flathead-nf-11",
                "final_environmental_impact_statement_volume_3": "R1PLAN-flathead-nf-13",
                "feis_map_appendix_part_1": "R1PLAN-flathead-nf-14",
                "feis_map_appendix_part_2": "R1PLAN-flathead-nf-15",
                "bmer_release_letter": "R1PLAN-flathead-nf-17",
            },
            {
                role: profile.source_record_id_for_role(role)
                for role in (
                    "forest_plan_monitoring_program",
                    "latest_biennial_monitoring_evaluation_report",
                    "record_of_decision_cover_letter",
                    "final_environmental_impact_statement_volume_3",
                    "feis_map_appendix_part_1",
                    "feis_map_appendix_part_2",
                    "bmer_release_letter",
                )
            },
        )
        self.assertEqual(
            set(profile.required_readiness_source_roles),
            {
                "planning_page",
                "primary_land_management_plan",
                "record_of_decision",
                "final_environmental_impact_statement_volume_1_part_1",
                "final_environmental_impact_statement_appendices",
                "biological_assessment",
                "biological_opinion_1",
                "biological_opinion_2",
                "administrative_change",
                "final_environmental_impact_statement_volume_2",
            },
        )
        self.assertTrue(profile.required_readiness_source_roles)
        self.assertFalse(
            {
                "forest_plan_monitoring_program",
                "latest_biennial_monitoring_evaluation_report",
                "record_of_decision_cover_letter",
                "final_environmental_impact_statement_volume_3",
                "feis_map_appendix_part_1",
                "feis_map_appendix_part_2",
                "bmer_release_letter",
            }
            & set(profile.required_readiness_source_roles)
        )

    def test_flathead_profile_has_grounded_resolver_depth_and_currentness_routes(self) -> None:
        profile = load_forest_plan_profile("flathead-nf")

        self.assertTrue(profile.ranger_district_terms)
        self.assertTrue(profile.geographic_area_terms)
        self.assertTrue(profile.management_area_terms)
        self.assertTrue(profile.overlay_terms)
        self.assertTrue(profile.supporting_record_trigger_rules)
        self.assertIn(
            "Hungry Horse-Glacier View Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertIn(
            "Spotted Bear Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertIn(
            "Hungry Horse Geographic Area",
            [entry.name for entry in profile.geographic_area_terms],
        )
        self.assertIn(
            "Swan Valley Geographic Area",
            [entry.name for entry in profile.geographic_area_terms],
        )
        self.assertIn(
            "Jewel Basin Hiking Area",
            [entry.name for entry in profile.management_area_terms],
        )
        self.assertIn(
            "Krause Basin",
            [entry.name for entry in profile.management_area_terms],
        )
        self.assertIn(
            "Inventoried Roadless Area",
            [entry.name for entry in profile.overlay_terms],
        )
        self.assertIn(
            "Jewel Basin Recommended Wilderness Area",
            [entry.name for entry in profile.overlay_terms],
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
            {rule.route_id for rule in profile.supporting_record_trigger_rules},
        )

    def test_milestone_2_added_active_profiles_are_covered_by_richer_eval_contracts(self) -> None:
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        rows = {
            row["forest_unit_id"]: row
            for row in readiness["profile_rows"]
            if row["forest_unit_id"] in {"beaverhead-deerlodge-nf", "flathead-nf"}
        }

        self.assertEqual(set(rows), {"beaverhead-deerlodge-nf", "flathead-nf"})

        expected_fixture_families = {
            "beaverhead-deerlodge-nf": {
                "scope_positive",
                "management_area_positive",
                "supporting_route_positive",
                "custer_hard_negative",
                "non_selected_non_custer_hard_negative",
                "selected_profile_compliance",
            },
            "flathead-nf": {
                "scope_positive",
                "management_area_positive",
                "supporting_route_positive",
                "currentness_positive",
                "custer_hard_negative",
                "non_selected_non_custer_hard_negative",
                "selected_profile_compliance",
            },
        }

        for forest_unit_id, row in rows.items():
            coverage = row["applicability_eval_coverage"]
            self.assertEqual(row["profile_kind"], "active_profile_added_milestone_5")
            self.assertEqual(row["graph_promotion_status"], "promoted")
            self.assertTrue(row["milestone_5_added_profile"])
            self.assertEqual(coverage["status"], "covered")
            self.assertGreaterEqual(coverage["positive_case_count"], 4)
            self.assertGreaterEqual(coverage["hard_negative_case_count"], 3)
            self.assertGreaterEqual(
                coverage["selected_profile_compliance_case_count"],
                1,
            )
            self.assertTrue(
                expected_fixture_families[forest_unit_id].issubset(
                    set(coverage["fixture_family_ids"])
                )
            )

    def test_milestone_3_tracking_only_profiles_are_promoted_to_covered_eval_contracts(self) -> None:
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        tracking_only_ids = {
            "bitterroot-nf",
            "dakota-prairie-grasslands",
            "helena-lewis-and-clark-nf",
            "idaho-panhandle-nfs",
            "kootenai-nf",
            "lolo-nf",
            "nez-perce-clearwater-nfs",
        }
        rows = {
            row["forest_unit_id"]: row
            for row in readiness["profile_rows"]
            if row["forest_unit_id"] in tracking_only_ids
        }

        self.assertEqual(set(rows), tracking_only_ids)
        expected_fixture_families = {
            "scope_positive",
            "scope_positive_with_ambiguous_context",
            "custer_hard_negative",
            "non_selected_non_custer_hard_negative",
        }

        for forest_unit_id, row in rows.items():
            coverage = row["applicability_eval_coverage"]
            self.assertEqual(row["profile_kind"], "region1_tracking_only")
            self.assertEqual(row["graph_promotion_status"], "promoted")
            self.assertEqual(coverage["status"], "covered")
            self.assertGreaterEqual(coverage["positive_case_count"], 2)
            self.assertGreaterEqual(coverage["hard_negative_case_count"], 2)
            self.assertEqual(coverage["selected_profile_compliance_case_count"], 0)
            self.assertEqual(
                set(coverage["fixture_family_ids"]),
                expected_fixture_families,
                forest_unit_id,
            )
            self.assertEqual(len(coverage["fixtures"]), 4, forest_unit_id)

    def test_profiles_cover_all_tracked_region1_readiness_units(self) -> None:
        profiles = load_forest_plan_profiles()
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))

        readiness_unit_ids = {
            row["forest_unit_id"] for row in readiness["profile_rows"]
        }
        profile_unit_ids = {profile.forest_unit_id for profile in profiles.profiles}

        self.assertEqual(profile_unit_ids, readiness_unit_ids)
        self.assertEqual(len(profiles.profiles), 10)

    def test_non_custer_profiles_flatten_readiness_source_requirements(self) -> None:
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))

        for row in readiness["profile_rows"]:
            if row["forest_unit_id"] == "custer-gallatin-nf":
                continue
            profile = load_forest_plan_profile(row["forest_unit_id"])
            expected_source_record_ids = []
            for requirement in row["source_requirements"]:
                if "source_record_id" in requirement:
                    expected_source_record_ids.append(requirement["source_record_id"])
                else:
                    expected_source_record_ids.extend(requirement["source_record_ids"])
            self.assertEqual(
                set(profile.required_source_record_ids),
                set(expected_source_record_ids),
                row["forest_unit_id"],
            )
            self.assertEqual(
                profile.active_plan_source_record_id,
                row["active_plan_source_record_id"],
                row["forest_unit_id"],
            )

    def test_custer_gallatin_profile_matches_current_supporting_routes(self) -> None:
        profile = load_forest_plan_profile("custer-gallatin-nf")

        self.assertEqual(
            [rule.route_id for rule in profile.supporting_record_trigger_rules],
            [route.route_id for route in SUPPORTING_PLAN_EVIDENCE_ROUTES],
        )
        self.assertEqual(
            [rule.source_record_id for rule in profile.supporting_record_trigger_rules],
            [route.source_record_id for route in SUPPORTING_PLAN_EVIDENCE_ROUTES],
        )
        self.assertIn(
            "Bridger, Bangtail, and Crazy Mountains Geographic Area",
            [entry.name for entry in profile.geographic_area_terms],
        )
        self.assertIn(
            "Crazy Mountains Backcountry Area",
            [entry.name for entry in profile.management_area_terms],
        )
        self.assertIn("Inventoried Roadless Area", [entry.name for entry in profile.overlay_terms])

    def test_rejects_unknown_required_readiness_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            _write_profile_config(
                path,
                required_readiness_source_roles=["primary_plan", "missing_role"],
            )

            with self.assertRaisesRegex(ValueError, "unknown source roles: missing_role"):
                load_forest_plan_profiles(path)

    def test_rejects_trigger_rule_with_unknown_target_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            _write_profile_config(
                path,
                supporting_record_trigger_rules=[
                    {
                        "route_id": "bad-route",
                        "category": "bad",
                        "name": "Bad route",
                        "target_source_role": "missing_role",
                        "package_terms": ["term"],
                        "source_query": "term",
                        "source_terms": ["term"],
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "unknown source roles: missing_role"):
                load_forest_plan_profiles(path)

    def test_rejects_non_list_known_other_forest_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            payload = _profile_config_payload()
            payload["known_other_forest_units"] = "not-a-list"
            _write_json(path, payload)

            with self.assertRaisesRegex(
                ValueError,
                "profile collection.known_other_forest_units must be a list",
            ):
                load_forest_plan_profiles(path)

    def test_rejects_non_list_term_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            _write_profile_config(
                path,
                profile_updates={
                    "geographic_area_terms": [
                        {
                            "entry_id": "geo-one",
                            "category": "geographic_area",
                            "name": "Area One",
                            "aliases": "Area 1",
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(
                ValueError,
                r"profiles\[0\]\.geographic_area_terms\[0\]\.aliases must be a list",
            ):
                load_forest_plan_profiles(path)

    def test_rejects_empty_explicit_trigger_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            _write_profile_config(
                path,
                supporting_record_trigger_rules=[
                    {
                        "route_id": "empty-trigger",
                        "category": "bad",
                        "name": "Bad trigger",
                        "target_source_role": "primary_plan",
                        "package_terms": ["term"],
                        "source_query": "term",
                        "source_terms": ["term"],
                        "trigger_terms": [],
                    }
                ],
            )

            with self.assertRaisesRegex(
                ValueError,
                r"profiles\[0\]\.supporting_record_trigger_rules\[0\]\.trigger_terms "
                "must not be empty",
            ):
                load_forest_plan_profiles(path)

    def test_defaults_trigger_terms_to_package_terms_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            _write_profile_config(
                path,
                supporting_record_trigger_rules=[
                    {
                        "route_id": "default-trigger",
                        "category": "route",
                        "name": "Default trigger route",
                        "target_source_role": "primary_plan",
                        "package_terms": ["package term"],
                        "source_query": "source term",
                        "source_terms": ["source term"],
                    }
                ],
            )

            profile = load_forest_plan_profile("unit-one", path)

            self.assertEqual(
                profile.supporting_record_trigger_rules[0].trigger_terms,
                ("package term",),
            )

    def test_rejects_non_string_profile_data_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            _write_profile_config(path, profile_updates={"profile_data_source": 123})

            with self.assertRaisesRegex(
                ValueError,
                r"profiles\[0\]\.profile_data_source must be a non-empty string",
            ):
                load_forest_plan_profiles(path)


def _write_profile_config(
    path: Path,
    *,
    required_readiness_source_roles: list[str] | None = None,
    supporting_record_trigger_rules: list[dict] | None = None,
    profile_updates: dict | None = None,
) -> None:
    payload = _profile_config_payload(
        required_readiness_source_roles=required_readiness_source_roles,
        supporting_record_trigger_rules=supporting_record_trigger_rules,
        profile_updates=profile_updates,
    )
    _write_json(path, payload)


def _profile_config_payload(
    *,
    required_readiness_source_roles: list[str] | None = None,
    supporting_record_trigger_rules: list[dict] | None = None,
    profile_updates: dict | None = None,
) -> dict:
    payload = {
        "schema_version": FOREST_PLAN_PROFILES_SCHEMA_VERSION,
        "profiles": [
            {
                "forest_unit_id": "unit-one",
                "forest_unit_names": ["Unit One National Forest"],
                "ambiguous_unit_terms": ["Unit"],
                "active_plan_source_record_id": "PLAN-001",
                "supporting_source_record_ids_by_role": {
                    "primary_plan": {
                        "source_record_id": "PLAN-001",
                        "required_for": "plan review",
                    }
                },
                "required_readiness_source_roles": required_readiness_source_roles
                or ["primary_plan"],
                "ranger_district_terms": [],
                "geographic_area_terms": [],
                "management_area_terms": [],
                "overlay_terms": [],
                "plan_component_types": ["standard"],
                "supporting_record_trigger_rules": supporting_record_trigger_rules or [],
                "review_topics": ["plan review"],
            }
        ],
    }
    if profile_updates:
        payload["profiles"][0].update(profile_updates)
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _forest_plan_register_rows(forest_unit_id: str) -> list[dict[str, str]]:
    with REGISTER_PATH.open("r", encoding="utf-8", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row["forest_unit_id"] == forest_unit_id
        ]


if __name__ == "__main__":
    unittest.main()
