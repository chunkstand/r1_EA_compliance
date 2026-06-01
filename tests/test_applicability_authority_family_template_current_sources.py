from __future__ import annotations

import unittest

from usfs_r1_ea_sources.applicability_authority_family_templates import authority_family_template_candidates


class AuthorityFamilyTemplateCurrentSourceTests(unittest.TestCase):
    def test_candidates_resolve_clean_water_family_current_source_additions(self) -> None:
        expected_source_record_ids = [
            "FED-022",
            "FED-045",
            "FED-046",
            "FED-047",
            "FED-048",
            "FED-049",
            "FED-050",
            "FED-017",
            "FED-051",
            "FED-029",
            "STP-031",
            "STP-032",
            "STP-033",
            "STP-034",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal" if source_record_id.startswith("FED-") else "state_partner",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "clean-water-current-source-template",
                        "authority_family_id": "clean_water_act_wotus_permits",
                        "rule_id": "clean_water_current_source_template_rule",
                        "title": "Clean Water Act and WOTUS permits template",
                        "question": "Does the package trigger Clean Water Act or WOTUS permit review?",
                        "requirement": "Evaluate Clean Water Act, Corps permit, and state 401 review.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-082",
                        "source_record_ids": [
                            "R1EA-082",
                            "R1EA-083",
                            "R1EA-084",
                            "R1EA-085",
                            "R1EA-086",
                            "R1EA-087",
                            "R1EA-088",
                            "R1EA-089",
                            "R1EA-090",
                            "R1EA-091",
                            "R1EA-115",
                            "R1EA-116",
                            "R1EA-117",
                            "R1EA-118",
                        ],
                        "package_query": "clean water act permits",
                        "package_terms": ["clean water act", "wetlands", "waters of the united states"],
                        "applies_if_package_terms": ["clean water act", "wetlands"],
                        "does_not_apply_if_package_terms": ["no wetlands"],
                        "source_query": "clean water act authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-082",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_wildlife_current_source_additions(self) -> None:
        expected_source_record_ids = [
            "FED-029",
            "FED-060",
            "FED-061",
            "FED-062",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "wildlife-current-source-template",
                        "authority_family_id": "eagle_efh_and_special_wildlife_sources",
                        "rule_id": "wildlife_current_source_template_rule",
                        "title": "Eagle and EFH current source template",
                        "question": "Does the package trigger eagle or EFH review?",
                        "requirement": "Evaluate eagle and EFH review.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-097",
                        "source_record_ids": [
                            "R1EA-097",
                            "R1EA-098",
                            "R1EA-099",
                            "R1EA-100",
                        ],
                        "package_query": "eagle EFH fish habitat",
                        "package_terms": ["bald eagle", "golden eagle", "essential fish habitat"],
                        "applies_if_package_terms": ["bald eagle", "essential fish habitat"],
                        "does_not_apply_if_package_terms": ["no essential fish habitat"],
                        "source_query": "wildlife authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-097",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_hazardous_current_source_addition(self) -> None:
        expected_source_record_ids = [
            "FED-037",
            "FED-036",
            "FED-063",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "hazardous-current-source-template",
                        "authority_family_id": "hazardous_materials_site_condition",
                        "rule_id": "hazardous_current_source_template_rule",
                        "title": "Hazardous-material current source template",
                        "question": "Does the package trigger hazardous-material or site-condition review?",
                        "requirement": "Evaluate hazardous-materials, contamination, and response-action review.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-107",
                        "source_record_ids": [
                            "R1EA-107",
                            "R1EA-108",
                            "R1EA-109",
                        ],
                        "package_query": "hazardous materials contamination cleanup",
                        "package_terms": ["hazardous materials", "contamination", "spill response"],
                        "applies_if_package_terms": ["hazardous materials", "contamination"],
                        "does_not_apply_if_package_terms": ["no hazardous materials"],
                        "source_query": "hazardous materials authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-107",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_minerals_current_source_addition(self) -> None:
        expected_source_record_ids = [
            "FED-009",
            "FED-070",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "regulation" if source_record_id == "FED-009" else "law",
                "authority_level": "federal",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "minerals-current-source-template",
                        "authority_family_id": "minerals_energy_authorities",
                        "rule_id": "minerals_current_source_template_rule",
                        "title": "Minerals current source template",
                        "question": "Does the package trigger minerals or energy-development review?",
                        "requirement": "Evaluate minerals and energy-development authorities.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "regulation",
                        "authority_document_role": "regulation",
                        "authority_source_record_id": "R1EA-041",
                        "source_record_ids": [
                            "R1EA-041",
                            "R1EA-063",
                        ],
                        "package_query": "minerals mining plan of operations mineral materials energy development",
                        "package_terms": [
                            "minerals",
                            "mining",
                            "plan of operations",
                            "mineral materials",
                            "energy development",
                        ],
                        "applies_if_package_terms": [
                            "minerals",
                            "plan of operations",
                        ],
                        "does_not_apply_if_package_terms": ["no mineral activity"],
                        "source_query": "minerals authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-041",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_vegetation_fire_current_source_additions(self) -> None:
        expected_source_record_ids = [
            "FED-071",
            "FED-072",
            "FED-073",
            "FED-074",
            "FED-075",
            "FED-076",
            "FED-077",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "vegetation-current-source-template",
                        "authority_family_id": "vegetation_wildfire_forest_health_authorities",
                        "rule_id": "vegetation_current_source_template_rule",
                        "title": "Vegetation and wildfire current source template",
                        "question": "Does the package trigger vegetation, fuels, wildfire, or forest-health review?",
                        "requirement": "Evaluate vegetation, fuels, wildfire, forest-health, and emergency-action authorities.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "law",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-056",
                        "source_record_ids": [
                            "R1EA-056",
                            "R1EA-057",
                            "R1EA-058",
                            "R1EA-059",
                            "R1EA-060",
                            "R1EA-061",
                            "R1EA-062",
                        ],
                        "package_query": "vegetation fuels wildfire forest health restoration emergency action",
                        "package_terms": [
                            "vegetation management",
                            "fuels treatment",
                            "wildfire",
                            "forest health",
                            "restoration",
                            "emergency action",
                        ],
                        "applies_if_package_terms": [
                            "vegetation management",
                            "wildfire",
                        ],
                        "does_not_apply_if_package_terms": ["no vegetation treatment"],
                        "source_query": "vegetation and wildfire authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-056",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_wilderness_current_source_additions(self) -> None:
        expected_source_record_ids = [
            "FED-083",
            "FED-084",
            "FED-013",
            "FED-085",
            "FED-027",
            "FED-028",
            "FED-086",
            "FED-087",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "regulation" if source_record_id in {"FED-083", "FED-084", "FED-085"} else "law",
                "authority_level": "federal",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.pdf",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "wilderness-current-source-template",
                        "authority_family_id": "wilderness_wsr_trails_designated_areas",
                        "rule_id": "wilderness_current_source_template_rule",
                        "title": "Wilderness current source template",
                        "question": "Does the package trigger wilderness, WSR, trails, cave, paleontology, or designated-area review?",
                        "requirement": "Evaluate wilderness, WSR, trails, and designated-area authorities.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "regulation",
                        "authority_document_role": "regulation",
                        "authority_source_record_id": "R1EA-045",
                        "source_record_ids": [
                            "R1EA-045",
                            "R1EA-046",
                            "R1EA-047",
                            "R1EA-051",
                            "R1EA-052",
                            "R1EA-053",
                            "R1EA-054",
                            "R1EA-055",
                        ],
                        "package_query": "wilderness WSR trails cave paleontology designated area",
                        "package_terms": [
                            "wilderness",
                            "wild and scenic river",
                            "national trail",
                            "cave",
                            "paleontology",
                            "designated area",
                        ],
                        "applies_if_package_terms": [
                            "wilderness",
                            "wild and scenic river",
                        ],
                        "does_not_apply_if_package_terms": ["no designated areas"],
                        "source_query": "wilderness designated area authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-045",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_invasive_farmland_drinking_water_current_source_additions(
        self,
    ) -> None:
        expected_source_record_ids = [
            "R1-008",
            "FED-064",
            "FED-065",
            "FED-066",
            "FED-067",
            "FED-035",
            "FED-068",
            "FED-069",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal" if source_record_id.startswith("FED-") else "region",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "invasive-current-source-template",
                        "authority_family_id": "invasive_pesticide_soils_farmland_drinking_water",
                        "rule_id": "invasive_current_source_template_rule",
                        "title": "Invasive species and drinking-water current source template",
                        "question": "Does the package trigger invasive-species, farmland, pesticide, or drinking-water review?",
                        "requirement": "Evaluate invasive-species, farmland, pesticide, and drinking-water review.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-112",
                        "source_record_ids": [
                            "R1EA-030",
                            "R1EA-101",
                            "R1EA-102",
                            "R1EA-105",
                            "R1EA-106",
                            "R1EA-110",
                            "R1EA-111",
                            "R1EA-112",
                        ],
                        "package_query": "invasive species pesticides farmland drinking water",
                        "package_terms": ["invasive species", "pesticides", "farmland", "drinking water"],
                        "applies_if_package_terms": ["invasive species", "drinking water"],
                        "does_not_apply_if_package_terms": ["no invasive species"],
                        "source_query": "invasive species authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-112",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_cultural_and_state_shpo_current_source_additions(self) -> None:
        expected_source_record_ids = [
            "FED-052",
            "FED-025",
            "FED-053",
            "FED-026",
            "FED-054",
            "FED-055",
            "FED-056",
            "FED-057",
            "FED-039",
            "FED-058",
            "FED-059",
            "STP-027",
            "STP-028",
            "STP-029",
            "STP-035",
        ]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal" if source_record_id.startswith("FED-") else "state_partner",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "cultural-current-source-template",
                        "authority_family_id": "cultural_resource_protection_and_state_shpo_sources",
                        "rule_id": "cultural_current_source_template_rule",
                        "title": "Cultural-resource and SHPO current source template",
                        "question": "Does the package trigger cultural-resource, sacred-site, or SHPO review?",
                        "requirement": "Evaluate cultural-resource, sacred-site, and state SHPO review.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-072",
                        "source_record_ids": [
                            "R1EA-072",
                            "R1EA-073",
                            "R1EA-074",
                            "R1EA-075",
                            "R1EA-076",
                            "R1EA-077",
                            "R1EA-078",
                            "R1EA-079",
                            "R1EA-080",
                            "R1EA-113",
                            "R1EA-114",
                            "R1EA-120",
                            "R1EA-121",
                            "R1EA-122",
                            "R1EA-123",
                        ],
                        "package_query": "cultural resources sacred sites shpo",
                        "package_terms": ["historic properties", "tribal consultation", "sacred sites"],
                        "applies_if_package_terms": ["historic properties", "sacred sites"],
                        "does_not_apply_if_package_terms": ["no historic properties"],
                        "source_query": "cultural resource authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-072",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_resolve_shared_tribal_overlap_current_source_additions(self) -> None:
        expected_source_record_ids = ["FED-055", "FED-039", "FED-038"]
        catalog_by_source_id = {
            source_record_id: {
                "source_record_id": source_record_id,
                "title": source_record_id,
                "citation_label": source_record_id,
                "document_role": "law",
                "authority_level": "federal",
                "source_status": "downloaded_existing",
                "artifact_sha256": f"sha-{source_record_id.lower()}",
                "artifact_path": f"artifacts/raw/{source_record_id}.html",
            }
            for source_record_id in expected_source_record_ids
        }

        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "tribal-current-source-template",
                        "authority_family_id": "tribal_consultation_trust_sacred_sites",
                        "rule_id": "tribal_current_source_template_rule",
                        "title": "Tribal consultation current source template",
                        "question": "Does the package trigger tribal consultation or sacred-site review?",
                        "requirement": "Evaluate tribal consultation and sacred-site review.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-081",
                        "source_record_ids": ["R1EA-077", "R1EA-080", "R1EA-081"],
                        "package_query": "tribal consultation sacred sites",
                        "package_terms": ["tribal consultation", "sacred sites"],
                        "applies_if_package_terms": ["tribal consultation", "sacred sites"],
                        "does_not_apply_if_package_terms": ["no tribal consultation"],
                        "source_query": "tribal consultation authority source",
                        "source_filters": {
                            "source_record_id": "R1EA-081",
                        },
                    }
                ],
            },
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], expected_source_record_ids)
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            expected_source_record_ids,
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])


if __name__ == "__main__":
    unittest.main()
