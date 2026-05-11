from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
