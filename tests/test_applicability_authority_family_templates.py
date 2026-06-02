from __future__ import annotations

import unittest

from usfs_r1_ea_sources.applicability_authority_family_templates import authority_family_template_candidates


class AuthorityFamilyTemplateCandidateTests(unittest.TestCase):
    def test_candidates_include_dependency_and_graph_contract_details(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "clean-water-template",
                        "authority_family_id": "clean_water_unit",
                        "rule_id": "clean_water_template_rule",
                        "title": "Clean Water template",
                        "question": "Does the package affect wetlands?",
                        "requirement": "Evaluate Clean Water Act applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "law",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-CWA",
                        "source_record_ids": ["R1EA-CWA"],
                        "supporting_source_record_ids": ["R1EA-CWA-GUIDE"],
                        "excluded_source_record_ids": ["R1EA-CWA-OLD"],
                        "package_query": "wetlands",
                        "package_terms": ["wetlands"],
                        "package_section_terms": ["water resources"],
                        "applies_if_package_terms": ["wetlands"],
                        "does_not_apply_if_package_terms": ["no wetlands"],
                        "package_fact_types": ["resource_topic", "permit"],
                        "source_query": "Clean Water Act source",
                        "source_filters": {
                            "document_role": "law",
                            "source_record_id": "R1EA-CWA",
                        },
                        "trigger_arbitration": {
                            "minimum_strong_trigger_groups": 1,
                            "positive_negative_conflict_policy": "positive_precedence",
                        },
                        "source_evidence_requirements": ["catalog-confirmed source"],
                        "evidence_expectation": "Source-backed wetlands evidence is required.",
                        "dependency_contract": {
                            "dependency_rule_ids": ["wetlands_screen"],
                            "superseded_by_family_ids": ["clean_water_replacement"],
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "R1EA-CWA": {
                    "source_record_id": "R1EA-CWA",
                    "title": "Clean Water Act",
                    "citation_label": "R1EA-CWA | Clean Water Act",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-cwa",
                    "artifact_path": "artifacts/raw/R1EA-CWA.pdf",
                },
                "R1EA-CWA-GUIDE": {
                    "source_record_id": "R1EA-CWA-GUIDE",
                    "title": "Clean Water guidance",
                    "citation_label": "R1EA-CWA-GUIDE | Guidance",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-guide",
                    "artifact_path": "artifacts/raw/R1EA-CWA-GUIDE.pdf",
                },
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            candidate["candidate_authority_id"],
            "authority-family-template:unit-authority-families:0.1.0:clean_water_unit:clean_water_template_rule",
        )
        self.assertEqual(candidate["source_role_filters"]["supporting_source_record_ids"], ["R1EA-CWA-GUIDE"])
        self.assertEqual(candidate["dependency_contract"]["dependency_rule_ids"], ["wetlands_screen"])
        self.assertEqual(
            candidate["graph_expansion_contract"]["neighbor_filters"]["superseded_by_family_ids"],
            ["clean_water_replacement"],
        )
        self.assertEqual(
            candidate["rule_template"]["trigger_arbitration"][
                "positive_negative_conflict_policy"
            ],
            "positive_precedence",
        )
        self.assertEqual(
            candidate["deterministic_applicability_test_contract"]["trigger_arbitration"][
                "positive_negative_conflict_policy"
            ],
            "positive_precedence",
        )
        self.assertEqual(
            {
                requirement["coverage_class"]
                for requirement in candidate["search_coverage_requirements"]
            },
            {
                "authority_family_positive_trigger_miss",
                "authority_family_explicit_negative_trigger",
            },
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_fall_back_to_package_terms_and_catalog_document_role(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "historic-template",
                        "authority_family_id": "historic_properties",
                        "rule_id": "historic_properties_rule",
                        "title": "Historic properties template",
                        "question": "Does the package affect historic properties?",
                        "requirement": "Evaluate historic properties applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "law",
                        "authority_source_record_id": "R1EA-NHPA",
                        "supporting_source_record_ids": [],
                        "excluded_source_record_ids": [],
                        "package_query": "historic properties",
                        "package_terms": ["historic properties"],
                        "package_section_terms": [],
                        "does_not_apply_if_package_terms": ["no historic properties"],
                        "package_fact_types": ["resource_topic"],
                        "source_query": "Historic Properties source",
                        "source_filters": {"source_record_id": "R1EA-NHPA"},
                        "source_evidence_requirements": [],
                        "evidence_expectation": "Historic properties evidence is required.",
                    }
                ],
            },
            catalog_by_source_id={
                "R1EA-NHPA": {
                    "source_record_id": "R1EA-NHPA",
                    "title": "NHPA",
                    "citation_label": "R1EA-NHPA | NHPA",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded_existing",
                    "artifact_sha256": "sha-nhpa",
                    "artifact_path": "artifacts/raw/R1EA-NHPA.pdf",
                }
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["authority_document_role"], "law")
        self.assertEqual(candidate["positive_trigger_groups"], [["historic properties"]])
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            ["R1EA-NHPA"],
        )
        self.assertEqual(
            candidate["retrieval_contract"]["source_role_filters"]["document_roles"],
            ["law"],
        )

    def test_candidates_use_reconciled_catalog_source_record_ids(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "land-exchange-template",
                        "authority_family_id": "land_exchange_policy",
                        "rule_id": "land_exchange_template_rule",
                        "title": "Land exchange template",
                        "question": "Does the package include a land exchange?",
                        "requirement": "Evaluate land-exchange policy applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "agency_policy",
                        "authority_document_role": "agency_policy",
                        "authority_source_record_id": "R1EA-150",
                        "source_record_ids": ["R1EA-150"],
                        "package_query": "land exchange",
                        "package_terms": ["land exchange"],
                        "applies_if_package_terms": ["land exchange"],
                        "does_not_apply_if_package_terms": ["no land exchange"],
                        "source_query": "land exchange policy source",
                        "source_filters": {
                            "document_role": "agency_policy",
                            "source_record_id": "R1EA-150",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "LEX-USFS-002": {
                    "source_record_id": "LEX-USFS-002",
                    "title": "FSM 5410 - Appraisals",
                    "citation_label": "LEX-USFS-002 | FSM 5410",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-002",
                    "artifact_path": "artifacts/raw/LEX-USFS-002.pdf",
                }
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], ["LEX-USFS-002"])
        self.assertEqual(
            candidate["source_role_filters"]["source_record_ids"],
            ["LEX-USFS-002"],
        )
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            ["LEX-USFS-002"],
        )

    def test_candidates_resolve_supporting_source_record_ids_into_catalog_rows(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "air-quality-template",
                        "authority_family_id": "clean_air_act_conformity_air_quality",
                        "rule_id": "clean_air_act_conformity_air_quality_authority_template",
                        "title": "Clean Air Act and conformity template",
                        "question": "Does the package trigger air-quality or conformity review?",
                        "requirement": "Evaluate Clean Air Act and general-conformity applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "law",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-092",
                        "source_record_ids": ["R1EA-092", "R1EA-093"],
                        "supporting_source_record_ids": ["R1EA-093"],
                        "package_query": "air quality conformity",
                        "package_terms": ["air quality", "conformity"],
                        "applies_if_package_terms": ["air quality", "conformity"],
                        "does_not_apply_if_package_terms": ["no conformity determination"],
                        "source_query": "Clean Air Act and general conformity source",
                        "source_filters": {
                            "document_role": "law",
                            "source_record_id": "R1EA-092",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "FED-023": {
                    "source_record_id": "FED-023",
                    "title": "Clean Air Act",
                    "citation_label": "FED-023 | Clean Air Act",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded_existing",
                    "artifact_sha256": "sha-fed-023",
                    "artifact_path": "artifacts/raw/FED-023.html",
                },
                "FED-044": {
                    "source_record_id": "FED-044",
                    "title": "General Conformity",
                    "citation_label": "FED-044 | General Conformity",
                    "document_role": "regulation",
                    "authority_level": "federal",
                    "source_status": "downloaded_existing",
                    "artifact_sha256": "sha-fed-044",
                    "artifact_path": "artifacts/raw/FED-044.xml",
                },
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], ["FED-023", "FED-044"])
        self.assertEqual(
            [record["source_record_id"] for record in candidate["source_records"]],
            ["FED-023", "FED-044"],
        )
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            ["FED-023", "FED-044"],
        )
        self.assertEqual(
            candidate["graph_expansion_contract"]["neighbor_filters"]["source_record_ids"],
            ["FED-023", "FED-044"],
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_use_reconciled_current_handbook_row(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "forest-plan-handbook-template",
                        "authority_family_id": "forest_service_planning_handbook_amendments",
                        "rule_id": "forest_plan_handbook_template_rule",
                        "title": "Forest planning handbook template",
                        "question": "Does the package depend on planning handbook direction?",
                        "requirement": "Evaluate planning handbook applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "agency_policy",
                        "authority_document_role": "agency_policy",
                        "authority_source_record_id": "R1EA-032",
                        "source_record_ids": ["R1EA-032"],
                        "package_query": "forest planning handbook",
                        "package_terms": ["forest planning handbook"],
                        "applies_if_package_terms": ["forest planning handbook"],
                        "does_not_apply_if_package_terms": ["no forest planning handbook"],
                        "source_query": "forest planning handbook source",
                        "source_filters": {
                            "document_role": "agency_policy",
                            "source_record_id": "R1EA-032",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "USFS-008": {
                    "source_record_id": "USFS-008",
                    "title": "Land Management Planning Handbook",
                    "citation_label": "USFS-008 | FSH 1909.12",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-usfs-008",
                    "artifact_path": "artifacts/raw/USFS-008.pdf",
                }
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], ["USFS-008"])
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            ["USFS-008"],
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_use_governed_current_source_replacements_for_remaining_template_rows(
        self,
    ) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "remaining-current-source-gap-template",
                        "authority_family_id": "remaining_current_source_gap",
                        "rule_id": "remaining_current_source_gap_rule",
                        "title": "Remaining current-source gap template",
                        "question": "Does the package depend on governed replacement rows?",
                        "requirement": "Evaluate governed current-source replacements.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "mixed",
                        "authority_document_role": "law",
                        "authority_source_record_id": "R1EA-038",
                        "source_record_ids": [
                            "R1EA-038",
                            "R1EA-043",
                            "R1EA-068",
                            "R1EA-125",
                            "R1EA-138",
                            "R1EA-143",
                            "R1EA-151",
                            "R1EA-153",
                            "R1EA-154",
                            "R1EA-156",
                        ],
                        "package_query": "governed replacement rows",
                        "package_terms": ["governed replacement rows"],
                        "applies_if_package_terms": ["governed replacement rows"],
                        "does_not_apply_if_package_terms": ["no governed replacement rows"],
                        "source_query": "governed replacement source",
                        "source_filters": {
                            "document_role": "law",
                            "source_record_id": "R1EA-038",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "LEX-FED-002": {
                    "source_record_id": "LEX-FED-002",
                    "title": "Bankhead-Jones Farm Tenant Act land exchange/disposition authority",
                    "citation_label": "LEX-FED-002 | 7 U.S.C. 1011",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-fed-002",
                    "artifact_path": "artifacts/raw/LEX-FED-002.pdf",
                },
                "FED-010": {
                    "source_record_id": "FED-010",
                    "title": "Land Uses",
                    "citation_label": "FED-010 | 36 CFR part 251",
                    "document_role": "regulation",
                    "authority_level": "regulation",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-fed-010",
                    "artifact_path": "artifacts/raw/FED-010.pdf",
                },
                "LEX-USFS-006": {
                    "source_record_id": "LEX-USFS-006",
                    "title": "FSM 5460 - Rights-of-Way Acquisition",
                    "citation_label": "LEX-USFS-006 | FSM 5460",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-006",
                    "artifact_path": "artifacts/raw/LEX-USFS-006.pdf",
                },
                "R1-003": {
                    "source_record_id": "R1-003",
                    "title": "Northern Region Species of Conservation Concern",
                    "citation_label": "R1-003 | SCC",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-r1-003",
                    "artifact_path": "artifacts/raw/R1-003.pdf",
                },
                "FED-011": {
                    "source_record_id": "FED-011",
                    "title": "Landownership Adjustments",
                    "citation_label": "FED-011 | 36 CFR part 254",
                    "document_role": "regulation",
                    "authority_level": "regulation",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-fed-011",
                    "artifact_path": "artifacts/raw/FED-011.pdf",
                },
                "R1-021": {
                    "source_record_id": "R1-021",
                    "title": "Region 1 FSM 5460 - Landownership Adjustments",
                    "citation_label": "R1-021 | Region 1 FSM 5460",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-r1-021",
                    "artifact_path": "artifacts/raw/R1-021.pdf",
                },
                "LEX-USFS-012": {
                    "source_record_id": "LEX-USFS-012",
                    "title": "FSH 5409.13 Chapter 30 - Land Exchange Sections 30-36",
                    "citation_label": "LEX-USFS-012 | FSH 5409.13 30-36",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-012",
                    "artifact_path": "artifacts/raw/LEX-USFS-012.pdf",
                },
                "LEX-USFS-013": {
                    "source_record_id": "LEX-USFS-013",
                    "title": "FSH 5409.13 Chapter 30 - Land Exchange Sections 37-39",
                    "citation_label": "LEX-USFS-013 | FSH 5409.13 37-39",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-013",
                    "artifact_path": "artifacts/raw/LEX-USFS-013.pdf",
                },
                "LEX-FED-005": {
                    "source_record_id": "LEX-FED-005",
                    "title": "Weeks Act mineral/timber/reservation exchange provisions",
                    "citation_label": "LEX-FED-005 | 16 U.S.C. 486",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-fed-005",
                    "artifact_path": "artifacts/raw/LEX-FED-005.pdf",
                },
                "LEX-FED-008": {
                    "source_record_id": "LEX-FED-008",
                    "title": "Organic Administration Act management authority",
                    "citation_label": "LEX-FED-008 | 16 U.S.C. 551",
                    "document_role": "law",
                    "authority_level": "law",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-fed-008",
                    "artifact_path": "artifacts/raw/LEX-FED-008.pdf",
                },
                "LEX-USFS-014": {
                    "source_record_id": "LEX-USFS-014",
                    "title": "FSH 5409.13 Chapter 50 - Title Evidence",
                    "citation_label": "LEX-USFS-014 | FSH 5409.13 50",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-014",
                    "artifact_path": "artifacts/raw/LEX-USFS-014.pdf",
                },
                "LEX-USFS-015": {
                    "source_record_id": "LEX-USFS-015",
                    "title": "FSH 5409.13 Chapter 60 - Reservations and Outstanding Rights",
                    "citation_label": "LEX-USFS-015 | FSH 5409.13 60",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-015",
                    "artifact_path": "artifacts/raw/LEX-USFS-015.pdf",
                },
                "LEX-USFS-002": {
                    "source_record_id": "LEX-USFS-002",
                    "title": "FSM 5410 - Appraisals",
                    "citation_label": "LEX-USFS-002 | FSM 5410",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-lex-usfs-002",
                    "artifact_path": "artifacts/raw/LEX-USFS-002.pdf",
                },
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            candidate["source_record_ids"],
            [
                "LEX-FED-002",
                "FED-010",
                "LEX-USFS-006",
                "R1-003",
                "FED-011",
                "R1-021",
                "LEX-USFS-012",
                "LEX-USFS-013",
                "LEX-FED-005",
                "LEX-FED-008",
                "LEX-USFS-014",
                "LEX-USFS-015",
                "LEX-USFS-002",
            ],
        )
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            candidate["source_record_ids"],
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])


    def test_candidates_use_forest_plan_identity_aliases_when_catalog_only_has_canonical_row(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "forest-plan-ba-template",
                        "authority_family_id": "region1_forest_plan_source_records",
                        "rule_id": "forest_plan_ba_template_rule",
                        "title": "Forest plan biological assessment template",
                        "question": "Does the package depend on the forest-plan biological assessment?",
                        "requirement": "Evaluate forest-plan biological assessment applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "forest_plan_support",
                        "authority_document_role": "forest_plan_support",
                        "authority_source_record_id": "R1PLAN-custer-gallatin-nf-06",
                        "source_record_ids": ["R1PLAN-custer-gallatin-nf-06"],
                        "package_query": "forest plan biological assessment",
                        "package_terms": ["forest plan biological assessment"],
                        "applies_if_package_terms": ["forest plan biological assessment"],
                        "does_not_apply_if_package_terms": ["no forest plan biological assessment"],
                        "source_query": "forest plan biological assessment source",
                        "source_filters": {
                            "document_role": "forest_plan_support",
                            "source_record_id": "R1PLAN-custer-gallatin-nf-06",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "FPS-074": {
                    "source_record_id": "FPS-074",
                    "title": "Biological Assessment for Custer Gallatin Land Management Plan",
                    "citation_label": "FPS-074 | Custer Gallatin biological assessment",
                    "document_role": "forest_plan_support",
                    "authority_level": "forest_plan_support",
                    "source_status": "downloaded",
                    "artifact_sha256": "sha-fps-074",
                    "artifact_path": "artifacts/raw/FPS-074.pdf",
                }
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], ["FPS-074"])
        self.assertEqual(
            candidate["required_source_evidence"]["source_record_ids"],
            ["FPS-074"],
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_candidates_keep_retired_excluded_rows_out_of_required_source_record_ids(self) -> None:
        candidates = authority_family_template_candidates(
            source_set_id="source-set-unit",
            template_set={
                "template_set_id": "unit-authority-families",
                "version": "0.1.0",
                "base_rule_pack_id": "unit-nepa-ea",
                "base_rule_pack_version": "0.1.0",
                "templates": [
                    {
                        "template_id": "land-exchange-template",
                        "authority_family_id": "land_exchange_policy",
                        "rule_id": "land_exchange_template_rule",
                        "title": "Land exchange template",
                        "question": "Does the package include a land exchange?",
                        "requirement": "Evaluate land-exchange policy applicability.",
                        "severity": "medium",
                        "applicability_mode": "conditional",
                        "authority_category": "agency_policy",
                        "authority_document_role": "agency_policy",
                        "authority_source_record_id": "R1EA-150",
                        "source_record_ids": ["R1EA-150", "R1EA-151"],
                        "supporting_source_record_ids": ["R1EA-151"],
                        "excluded_source_record_ids": ["R1EA-160", "R1EA-161", "R1EA-162"],
                        "package_query": "land exchange",
                        "package_terms": ["land exchange"],
                        "applies_if_package_terms": ["land exchange"],
                        "does_not_apply_if_package_terms": ["not a land exchange"],
                        "source_query": "land exchange policy source",
                        "source_filters": {
                            "document_role": "agency_policy",
                            "source_record_id": "R1EA-150",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "R1EA-150": {
                    "source_record_id": "R1EA-150",
                    "title": "Land exchange policy",
                    "citation_label": "R1EA-150 | Policy",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded_existing",
                    "artifact_sha256": "sha-land-policy",
                    "artifact_path": "artifacts/raw/R1EA-150.pdf",
                },
                "R1EA-151": {
                    "source_record_id": "R1EA-151",
                    "title": "Land exchange handbook support",
                    "citation_label": "R1EA-151 | Handbook",
                    "document_role": "agency_policy",
                    "authority_level": "agency_policy",
                    "source_status": "downloaded_existing",
                    "artifact_sha256": "sha-land-support",
                    "artifact_path": "artifacts/raw/R1EA-151.pdf",
                },
            },
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["source_record_ids"], ["R1EA-150", "R1EA-151"])
        self.assertEqual(
            candidate["source_role_filters"]["excluded_source_record_ids"],
            ["R1EA-160", "R1EA-161", "R1EA-162"],
        )
        self.assertEqual(
            candidate["required_source_evidence"]["excluded_source_record_ids"],
            ["R1EA-160", "R1EA-161", "R1EA-162"],
        )
        self.assertEqual(
            candidate["dependency_contract"]["excluded_source_record_ids"],
            ["R1EA-160", "R1EA-161", "R1EA-162"],
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])


if __name__ == "__main__":
    unittest.main()
