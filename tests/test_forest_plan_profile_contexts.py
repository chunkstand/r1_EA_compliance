from __future__ import annotations

import unittest

from usfs_r1_ea_sources.forest_plan_profiles import load_forest_plan_profile


class ForestPlanProfileContextTests(unittest.TestCase):
    def test_lolo_profile_uses_canonical_plan_sources_and_live_context_terms(self) -> None:
        profile = load_forest_plan_profile("lolo-nf")

        self.assertEqual(profile.active_plan_source_record_id, "FPS-298")
        self.assertEqual(
            profile.required_source_record_ids,
            (
                "R1PLAN-lolo-nf-01",
                "FPS-298",
                "FPS-300",
                "FPS-299",
                "FPS-418",
                "FPS-419",
                "FPS-342",
                "FPS-421",
            ),
        )
        self.assertIn(
            "Missoula Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertIn(
            "Inventoried Roadless Area",
            [entry.name for entry in profile.overlay_terms],
        )

    def test_dakota_prairie_profile_has_medora_context_terms(self) -> None:
        profile = load_forest_plan_profile("dakota-prairie-grasslands")

        self.assertEqual(
            profile.active_plan_source_record_id,
            "R1PLAN-dakota-prairie-grasslands-03",
        )
        self.assertIn(
            "Medora Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertEqual(
            [entry.name for entry in profile.geographic_area_terms],
            ["Badlands Geographic Area", "Rolling Prairie Geographic Area"],
        )
        self.assertEqual(
            {
                entry.source_record_id
                for entry in profile.geographic_area_terms
            },
            {"R1PLAN-dakota-prairie-grasslands-06"},
        )
        management_area_names = {entry.name for entry in profile.management_area_terms}
        self.assertTrue(
            {
                "Management Area 1.2a",
                "Management Area 3.51",
                "Management Area 3.65",
                "Management Area 6.1",
            }.issubset(management_area_names)
        )
        bighorn = next(
            entry
            for entry in profile.management_area_terms
            if entry.entry_id == "mgmt-dpg-3-51-bighorn-sheep"
        )
        self.assertIn("3.51b", bighorn.aliases)
        self.assertIn(
            "Inventoried Roadless Area",
            [entry.name for entry in profile.overlay_terms],
        )

    def test_idaho_panhandle_profile_uses_reconciled_sources_and_lacy_scope_term(self) -> None:
        profile = load_forest_plan_profile("idaho-panhandle-nfs")

        self.assertEqual(profile.active_plan_source_record_id, "FOR-021")
        self.assertEqual(
            profile.source_record_id_for_role("primary_land_management_plan"),
            "FOR-021",
        )
        self.assertEqual(profile.source_record_id_for_role("record_of_decision"), "FPS-223")
        self.assertEqual(profile.source_record_id_for_role("biological_opinion_1"), "FPS-238")
        self.assertEqual(profile.source_record_id_for_role("biological_opinion_2"), "FPS-240")
        self.assertEqual(profile.source_record_id_for_role("administrative_change_1"), "FPS-256")
        self.assertEqual(profile.source_record_id_for_role("administrative_change_2"), "FPS-257")
        self.assertEqual(
            [
                profile.source_record_id_for_role(f"biological_opinion_chapter_{index}")
                for index in range(1, 6)
            ],
            ["FPS-232", "FPS-233", "FPS-234", "FPS-235", "FPS-236"],
        )
        self.assertEqual(
            profile.source_record_id_for_role("final_environmental_impact_statement"),
            "R1PLAN-idaho-panhandle-nfs-04",
        )
        self.assertEqual(
            profile.source_record_id_for_role("final_environmental_impact_statement_appendices"),
            "R1PLAN-idaho-panhandle-nfs-05",
        )
        district = next(
            entry
            for entry in profile.ranger_district_terms
            if entry.entry_id == "district-st-joe"
        )
        self.assertEqual(district.name, "St. Joe Ranger District")
        self.assertIn("St Joe Ranger District", district.aliases)
        st_joe = next(
            entry
            for entry in profile.geographic_area_terms
            if entry.entry_id == "geo-st-joe"
        )
        self.assertEqual(st_joe.source_record_id, "FOR-021")
        self.assertIn("St Joe River drainage", st_joe.aliases)
        ma6 = next(
            entry
            for entry in profile.management_area_terms
            if entry.entry_id == "mgmt-ma6-general-forest"
        )
        self.assertEqual(ma6.name, "Management Area 6")
        self.assertIn("MA6 - General Forest", ma6.aliases)
        self.assertIn(
            "Riparian Habitat Conservation Area",
            [entry.name for entry in profile.overlay_terms],
        )
        self.assertIn("Wildland Urban Interface", [entry.name for entry in profile.overlay_terms])

    def test_kootenai_profile_uses_trojan_defense_context_terms(self) -> None:
        profile = load_forest_plan_profile("kootenai-nf")

        self.assertEqual(profile.active_plan_source_record_id, "R1PLAN-kootenai-nf-02")
        self.assertEqual(
            profile.source_record_id_for_role("primary_land_management_plan"),
            "R1PLAN-kootenai-nf-02",
        )
        self.assertIn(
            "Three Rivers Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertEqual(
            [entry.name for entry in profile.geographic_area_terms],
            ["Bull Geographic Area"],
        )
        self.assertEqual(
            {entry.entry_id for entry in profile.management_area_terms},
            {
                "mgmt-ma2-eligible-wild-scenic-rivers",
                "mgmt-ma3-special-areas",
                "mgmt-ma6-general-forest",
            },
        )
        self.assertIn(
            "Riparian Habitat Conservation Area",
            [entry.name for entry in profile.overlay_terms],
        )
        self.assertIn("Wildland Urban Interface", [entry.name for entry in profile.overlay_terms])

    def test_hlc_profile_has_bonanza_castles_context_terms(self) -> None:
        profile = load_forest_plan_profile("helena-lewis-and-clark-nf")

        self.assertEqual(
            profile.active_plan_source_record_id,
            "R1PLAN-helena-lewis-and-clark-nf-02",
        )
        self.assertIn(
            "White Sulphur Springs Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertIn(
            "Castles Geographic Area",
            [entry.name for entry in profile.geographic_area_terms],
        )
        castles = next(
            entry
            for entry in profile.geographic_area_terms
            if entry.entry_id == "geo-castles"
        )
        self.assertEqual(
            castles.source_record_id,
            "R1PLAN-helena-lewis-and-clark-nf-02",
        )
        self.assertIn("Castle Mountains", castles.aliases)

    def test_nez_perce_clearwater_profile_uses_reconciled_sources_and_dead_laundry_terms(
        self,
    ) -> None:
        profile = load_forest_plan_profile("nez-perce-clearwater-nfs")

        self.assertEqual(profile.active_plan_source_record_id, "FPS-347")
        self.assertEqual(
            profile.source_record_id_for_role("primary_land_management_plan"),
            "FPS-347",
        )
        self.assertEqual(profile.source_record_id_for_role("record_of_decision"), "FOR-032")
        self.assertEqual(
            profile.source_record_id_for_role("notice_of_plan_approval"),
            "FPS-344",
        )
        self.assertEqual(
            profile.source_record_id_for_role("administrative_changes"),
            "FOR-033",
        )
        self.assertEqual(profile.source_record_id_for_role("biological_assessment"), "FPS-365")
        self.assertEqual(
            profile.source_record_id_for_role("biological_assessment_supplement"),
            "FPS-366",
        )
        self.assertEqual(profile.source_record_id_for_role("biological_opinion_1"), "FOR-031")
        self.assertEqual(profile.source_record_id_for_role("biological_opinion_2"), "FPS-368")
        self.assertEqual(
            profile.source_record_id_for_role("final_environmental_impact_statement"),
            "FPS-372",
        )
        self.assertEqual(
            profile.source_record_id_for_role("final_environmental_impact_statement_appendices"),
            "FPS-373",
        )
        self.assertIn(
            "North Fork Ranger District",
            [entry.name for entry in profile.ranger_district_terms],
        )
        self.assertIn(
            "Deception Saddle",
            [entry.name for entry in profile.geographic_area_terms],
        )
        self.assertIn(
            "Management Area E1",
            [entry.name for entry in profile.management_area_terms],
        )
        self.assertIn(
            "Idaho Roadless Area",
            [entry.name for entry in profile.overlay_terms],
        )
        self.assertIn(
            "Riparian Habitat Conservation Area",
            [entry.name for entry in profile.overlay_terms],
        )
        self.assertEqual(
            {
                entry.entry_id: entry.source_record_id
                for entry in profile.overlay_terms
            },
            {
                "overlay-idaho-roadless-area": "FPS-347",
                "overlay-wildland-urban-interface": "FPS-347",
                "overlay-riparian-habitat-conservation-area": "FPS-347",
            },
        )


if __name__ == "__main__":
    unittest.main()
