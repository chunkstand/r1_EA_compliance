from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.forest_plan_profiles import (
    FOREST_PLAN_PROFILES_SCHEMA_VERSION,
    load_forest_plan_profile,
    load_forest_plan_profiles,
)
from usfs_r1_ea_sources.forest_plan_resolver import CUSTER_GALLATIN_PLAN_SOURCE_ID
from usfs_r1_ea_sources.forest_plan_resolver import CUSTER_GALLATIN_REQUIRED_SOURCE_IDS
from usfs_r1_ea_sources.forest_plan_resolver import SUPPORTING_PLAN_EVIDENCE_ROUTES


class ForestPlanProfileTests(unittest.TestCase):
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


def _write_profile_config(
    path: Path,
    *,
    required_readiness_source_roles: list[str] | None = None,
    supporting_record_trigger_rules: list[dict] | None = None,
) -> None:
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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
