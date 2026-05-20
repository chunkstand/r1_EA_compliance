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


if __name__ == "__main__":
    unittest.main()
