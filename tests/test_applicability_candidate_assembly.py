from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from usfs_r1_ea_sources.applicability_candidate_assembly import forest_plan_component_candidates
from usfs_r1_ea_sources.applicability_candidate_assembly import rule_template_candidates
from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanProfile
from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanProfileCollection
from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanSourceRecord


class ApplicabilityCandidateAssemblyTests(unittest.TestCase):
    def test_rule_template_candidates_include_rule_and_forest_plan_contract_details(self) -> None:
        rule_pack = {
            "rule_pack_id": "unit-nepa-ea",
            "version": "0.1.0",
            "baseline_source_record_ids": ["R1EA-BASE", "R1PLAN-custer-gallatin-nf-02"],
            "rules": [
                {
                    "id": "conditional_authority",
                    "title": "Conditional authority",
                    "question": "Does the package involve new road construction?",
                    "requirement": "Evaluate transportation authority applicability.",
                    "severity": "medium",
                    "authority_category": "regulation",
                    "authority_source_record_id": "R1EA-COND",
                    "authority_document_role": "regulation",
                    "applicability_mode": "conditional",
                    "package_query": "road construction",
                    "package_terms": ["transportation"],
                    "package_section_terms": ["transportation"],
                    "applies_if_package_terms": ["road construction"],
                    "does_not_apply_if_package_terms": ["no road construction"],
                    "source_query": "transportation authority source",
                    "source_filters": {
                        "document_role": "regulation",
                        "source_record_id": "R1EA-COND",
                    },
                    "dependency_rule_ids": ["baseline_authority"],
                    "supporting_source_record_ids": ["R1EA-GUIDE"],
                    "evidence_expectation": "Requires source and package transportation evidence.",
                },
                {
                    "id": "forest_plan_authority",
                    "title": "Forest plan authority",
                    "question": "Does the package need forest-plan review?",
                    "requirement": "Evaluate forest-plan consistency.",
                    "severity": "medium",
                    "authority_category": "forest_plan",
                    "authority_source_record_id": "R1PLAN-custer-gallatin-nf-02",
                    "authority_document_role": "forest_plan",
                    "applicability_mode": "baseline",
                    "package_query": "forest plan consistency",
                    "package_terms": ["forest plan consistency"],
                    "source_query": "forest plan source",
                    "source_filters": {
                        "document_role": "forest_plan",
                        "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                    },
                },
            ],
        }
        catalog_by_source_id = {
            "R1EA-COND": _catalog_record("R1EA-COND", "regulation", "regulation"),
            "R1PLAN-custer-gallatin-nf-02": _catalog_record(
                "R1PLAN-custer-gallatin-nf-02",
                "forest_plan",
                "forest_plan",
            ),
        }

        candidates = rule_template_candidates(
            source_set_id="source-set-test",
            rule_pack=rule_pack,
            catalog_by_source_id=catalog_by_source_id,
            source_claim_links_by_rule={
                "conditional_authority": [{"link_id": "link:conditional_authority"}],
                "forest_plan_authority": [{"link_id": "link:forest_plan_authority"}],
            },
            source_claim_gaps_by_rule={
                "conditional_authority": [
                    {
                        "gap_id": "gap:conditional_authority",
                        "reason": "pending_adjudication",
                    }
                ]
            },
        )

        self.assertEqual(len(candidates), 2)
        by_id = {candidate["candidate_authority_id"]: candidate for candidate in candidates}

        conditional = by_id["rule-template:unit-nepa-ea:0.1.0:conditional_authority"]
        self.assertEqual(conditional["authority_document_role"], "regulation")
        self.assertEqual(conditional["positive_trigger_groups"], [["road construction"]])
        self.assertEqual(conditional["negative_trigger_groups"], [["no road construction"]])
        self.assertEqual(
            conditional["required_package_fact_types"],
            [
                "action",
                "agency",
                "decision_posture",
                "evidence_span",
                "nepa_level",
                "package_section",
                "resource_topic",
            ],
        )
        self.assertTrue(
            conditional["required_source_evidence"]["requires_source_claim_linkage"]
        )
        self.assertEqual(
            conditional["required_source_evidence"]["rule_claim_gap_ids"],
            ["gap:conditional_authority"],
        )
        self.assertEqual(
            conditional["dependency_contract"]["dependency_rule_ids"],
            ["baseline_authority"],
        )
        self.assertEqual(
            conditional["dependency_contract"]["supporting_source_record_ids"],
            ["R1EA-GUIDE"],
        )
        self.assertEqual(
            {
                requirement["coverage_class"]
                for requirement in conditional["search_coverage_requirements"]
            },
            {"positive_trigger_miss", "explicit_negative_trigger"},
        )
        self.assertTrue(conditional["source_evidence_availability"]["available"])
        self.assertTrue(
            conditional["source_evidence_availability"]["source_claim_linkage_recorded"]
        )
        self.assertEqual(
            conditional["deterministic_applicability_test_contract"]["baseline_required"],
            False,
        )

        forest_plan = by_id["rule-template:unit-nepa-ea:0.1.0:forest_plan_authority"]
        self.assertEqual(forest_plan["authority_document_role"], "forest_plan")
        self.assertEqual(
            forest_plan["positive_trigger_groups"],
            [["forest plan consistency"]],
        )
        self.assertEqual(forest_plan["negative_trigger_groups"], [])
        self.assertTrue(
            {
                "geography",
                "management_area",
                "overlay",
            }.issubset(set(forest_plan["required_package_fact_types"]))
        )
        self.assertEqual(
            forest_plan["retrieval_contract"]["contract_type"],
            "rule_template_retrieval",
        )
        self.assertEqual(
            forest_plan["graph_expansion_contract"]["neighbor_filters"]["source_record_ids"],
            ["R1PLAN-custer-gallatin-nf-02"],
        )
        self.assertEqual(
            forest_plan["deterministic_applicability_test_contract"]["baseline_required"],
            True,
        )

    def test_rule_template_candidates_use_reconciled_catalog_source_record_ids(self) -> None:
        candidates = rule_template_candidates(
            source_set_id="source-set-test",
            rule_pack={
                "rule_pack_id": "unit-nepa-ea",
                "version": "0.1.0",
                "baseline_source_record_ids": ["R1EA-150"],
                "rules": [
                    {
                        "id": "land_exchange_policy",
                        "title": "Land exchange policy",
                        "question": "Does the package require land-exchange policy review?",
                        "requirement": "Evaluate source-backed land-exchange policy.",
                        "severity": "medium",
                        "authority_category": "agency_policy",
                        "authority_source_record_id": "R1EA-150",
                        "authority_document_role": "agency_policy",
                        "applicability_mode": "baseline",
                        "package_query": "land exchange",
                        "package_terms": ["land exchange"],
                        "source_query": "land exchange policy source",
                        "source_filters": {
                            "document_role": "agency_policy",
                            "source_record_id": "R1EA-150",
                        },
                    }
                ],
            },
            catalog_by_source_id={
                "LEX-USFS-002": _catalog_record(
                    "LEX-USFS-002",
                    "agency_policy",
                    "agency_policy",
                )
            },
            source_claim_links_by_rule={"land_exchange_policy": [{"link_id": "link:policy"}]},
            source_claim_gaps_by_rule={},
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
        self.assertEqual(
            candidate["graph_expansion_contract"]["neighbor_filters"]["source_record_ids"],
            ["LEX-USFS-002"],
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])

    def test_rule_template_candidates_resolve_base_rule_current_source_additions(self) -> None:
        rule_pack = {
            "rule_pack_id": "unit-nepa-ea",
            "version": "0.1.0",
            "baseline_source_record_ids": [
                "R1EA-020",
                "R1EA-021",
                "R1EA-033",
                "R1EA-034",
            ],
            "rules": [
                _rule_template("seven_county_nepa_scope", "R1EA-020", "case_law", "case_law"),
                _rule_template("apa_final_agency_action", "R1EA-021", "law", "law"),
                _rule_template(
                    "directives_notice_comment_36cfr_216",
                    "R1EA-027",
                    "regulation",
                    "regulation",
                    applicability_mode="conditional",
                ),
                _rule_template(
                    "musuya_multiple_use_sustained_yield",
                    "R1EA-033",
                    "law",
                    "law",
                ),
                _rule_template("organic_act_16usc_475", "R1EA-034", "law", "law"),
            ],
        }
        catalog_by_source_id = {
            "FED-078": _catalog_record("FED-078", "case_law", "case_law"),
            "FED-079": _catalog_record("FED-079", "law", "law"),
            "FED-080": _catalog_record("FED-080", "regulation", "regulation"),
            "FED-081": _catalog_record("FED-081", "law", "law"),
            "FED-082": _catalog_record("FED-082", "law", "law"),
        }

        candidates = rule_template_candidates(
            source_set_id="source-set-test",
            rule_pack=rule_pack,
            catalog_by_source_id=catalog_by_source_id,
            source_claim_links_by_rule={
                "seven_county_nepa_scope": [{"link_id": "link:seven_county"}],
                "apa_final_agency_action": [{"link_id": "link:apa"}],
                "directives_notice_comment_36cfr_216": [{"link_id": "link:part216"}],
                "musuya_multiple_use_sustained_yield": [{"link_id": "link:musuya"}],
                "organic_act_16usc_475": [{"link_id": "link:organic475"}],
            },
            source_claim_gaps_by_rule={},
        )

        by_id = {candidate["candidate_authority_id"]: candidate for candidate in candidates}
        self.assertEqual(
            by_id["rule-template:unit-nepa-ea:0.1.0:seven_county_nepa_scope"]["source_record_ids"],
            ["FED-078"],
        )
        self.assertEqual(
            by_id["rule-template:unit-nepa-ea:0.1.0:apa_final_agency_action"]["source_record_ids"],
            ["FED-079"],
        )
        self.assertEqual(
            by_id["rule-template:unit-nepa-ea:0.1.0:directives_notice_comment_36cfr_216"]["source_record_ids"],
            ["FED-080"],
        )
        self.assertEqual(
            by_id["rule-template:unit-nepa-ea:0.1.0:musuya_multiple_use_sustained_yield"]["source_record_ids"],
            ["FED-081"],
        )
        self.assertEqual(
            by_id["rule-template:unit-nepa-ea:0.1.0:organic_act_16usc_475"]["source_record_ids"],
            ["FED-082"],
        )
        self.assertTrue(all(candidate["source_evidence_availability"]["available"] for candidate in candidates))

    def test_forest_plan_component_candidates_include_profile_and_inventory_contracts(
        self,
    ) -> None:
        source_set_id = "source-set-test"
        catalog_by_source_id = {
            "R1PLAN-custer-gallatin-nf-02": _catalog_record(
                "R1PLAN-custer-gallatin-nf-02",
                "forest_plan",
                "forest_plan",
            )
        }
        component_inventory_path = Path(
            "source_library/derived/source-set-test/forest_plan_components/component_inventory.json"
        )
        component_inventory = {
            "inventory_id": "unit-inventory",
            "source_set_id": source_set_id,
            "forest_unit_id": "custer-gallatin-nf",
            "plan_version": "2022",
            "components": [
                {
                    "component_id": "R1PLAN-custer-gallatin-nf-02-STD-01",
                    "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                    "component_type": "standard",
                    "section_id": "std-01",
                    "section_heading": "Plan Components",
                    "artifact_sha256": hashlib.sha256(b"component").hexdigest(),
                    "source_chunk_ids": ["chunk:std-01"],
                    "package_evidence_terms": ["road"],
                    "resource_topics": ["access"],
                    "activity_tags": ["construction"],
                    "geographic_area_ids": [],
                    "management_area_ids": ["mgmt-crazy-mountains-bca"],
                    "overlay_ids": [],
                }
            ],
        }

        candidates = forest_plan_component_candidates(
            source_set_id=source_set_id,
            profiles=_profile_collection(),
            component_inventory=component_inventory,
            component_inventory_path=component_inventory_path,
            component_inventory_sha256="inventory-sha256",
            catalog_by_source_id=catalog_by_source_id,
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            candidate["candidate_authority_id"],
            "forest-plan-component:unit-inventory:R1PLAN-custer-gallatin-nf-02-STD-01",
        )
        self.assertEqual(candidate["authority_family_id"], "nfma_forest_planning_project_consistency")
        self.assertEqual(
            candidate["required_package_fact_types"],
            [
                "action",
                "agency",
                "evidence_span",
                "management_area",
                "package_section",
                "resource_topic",
            ],
        )
        self.assertEqual(candidate["positive_trigger_groups"], [["road"], ["access"], ["construction"]])
        self.assertEqual(candidate["negative_trigger_groups"], [["not part of the project area"]])
        self.assertEqual(
            candidate["source_role_filters"]["source_filters"]["document_role"],
            "forest_plan",
        )
        self.assertTrue(candidate["required_source_evidence"]["requires_source_chunks"])
        self.assertEqual(
            candidate["retrieval_contract"]["contract_type"],
            "forest_plan_component_retrieval",
        )
        self.assertEqual(
            candidate["graph_expansion_contract"]["neighbor_filters"]["forest_unit_id"],
            "custer-gallatin-nf",
        )
        self.assertEqual(
            candidate["dependency_contract"]["supporting_source_record_ids"],
            ["R1PLAN-cg-biological-opinion", "R1PLAN-custer-gallatin-nf-02"],
        )
        self.assertEqual(
            candidate["forest_plan"]["profile_data_source"],
            "unit-test",
        )
        self.assertEqual(
            candidate["forest_plan"]["component_inventory_path"],
            str(component_inventory_path),
        )
        self.assertTrue(candidate["source_evidence_availability"]["available"])
        self.assertEqual(
            candidate["deterministic_applicability_test_contract"]["source_chunk_ids"],
            ["chunk:std-01"],
        )
        self.assertEqual(
            {
                requirement["coverage_class"]
                for requirement in candidate["search_coverage_requirements"]
            },
            {"forest_plan_scope_miss", "component_trigger_miss"},
        )

    def test_forest_plan_component_candidates_filter_region_inventory_to_allowed_forest(
        self,
    ) -> None:
        source_set_id = "source-set-test"
        catalog_by_source_id = {
            "R1PLAN-custer-gallatin-nf-02": _catalog_record(
                "R1PLAN-custer-gallatin-nf-02",
                "forest_plan",
                "forest_plan",
            ),
            "R1PLAN-flathead-nf-02": _catalog_record(
                "R1PLAN-flathead-nf-02",
                "forest_plan",
                "forest_plan",
            ),
        }
        candidates = forest_plan_component_candidates(
            source_set_id=source_set_id,
            profiles=_profile_collection_with_flathead(),
            component_inventory={
                "inventory_id": "region1-inventory",
                "source_set_id": source_set_id,
                "forest_unit_id": None,
                "plan_version": None,
                "components": [
                    {
                        "component_id": "R1PLAN-custer-gallatin-nf-02-STD-01",
                        "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                        "forest_unit_id": "custer-gallatin-nf",
                        "plan_version": "2022",
                        "component_type": "standard",
                        "section_id": "std-01",
                        "section_heading": "Plan Components",
                        "artifact_sha256": hashlib.sha256(b"cg-component").hexdigest(),
                        "source_chunk_ids": ["chunk:cg-std-01"],
                        "package_evidence_terms": ["road"],
                        "resource_topics": ["access"],
                        "activity_tags": ["construction"],
                        "geographic_area_ids": [],
                        "management_area_ids": ["mgmt-crazy-mountains-bca"],
                        "overlay_ids": [],
                    },
                    {
                        "component_id": "R1PLAN-flathead-nf-02-GDL-01",
                        "source_record_id": "R1PLAN-flathead-nf-02",
                        "forest_unit_id": "flathead-nf",
                        "plan_version": "2018",
                        "component_type": "guideline",
                        "section_id": "gdl-01",
                        "section_heading": "Plan Components",
                        "artifact_sha256": hashlib.sha256(b"flat-component").hexdigest(),
                        "source_chunk_ids": ["chunk:flat-gdl-01"],
                        "package_evidence_terms": ["trail"],
                        "resource_topics": ["hydrology"],
                        "activity_tags": ["maintenance"],
                        "geographic_area_ids": [],
                        "management_area_ids": ["mgmt-jewel-basin-hiking-area"],
                        "overlay_ids": [],
                    },
                ],
            },
            component_inventory_path=Path(
                "source_library/derived/source-set-test/forest_plan_components/component_inventory.json"
            ),
            component_inventory_sha256="inventory-sha256",
            catalog_by_source_id=catalog_by_source_id,
            allowed_forest_plan_source_record_ids={"R1PLAN-custer-gallatin-nf-02"},
        )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            candidate["candidate_authority_id"],
            "forest-plan-component:region1-inventory:R1PLAN-custer-gallatin-nf-02-STD-01",
        )
        self.assertEqual(candidate["forest_plan"]["forest_unit_id"], "custer-gallatin-nf")
        self.assertEqual(candidate["forest_plan"]["plan_version"], "2022")
        self.assertEqual(
            candidate["forest_plan"]["active_plan_source_record_id"],
            "R1PLAN-custer-gallatin-nf-02",
        )

    def test_forest_plan_component_candidates_ignore_inventory_outside_source_set(self) -> None:
        candidates = forest_plan_component_candidates(
            source_set_id="source-set-test",
            profiles=_profile_collection(),
            component_inventory={
                "inventory_id": "unit-inventory",
                "source_set_id": "source-set-other",
                "forest_unit_id": "custer-gallatin-nf",
                "components": [],
            },
            component_inventory_path=Path("source_library/derived/source-set-other/component_inventory.json"),
            component_inventory_sha256="inventory-sha256",
            catalog_by_source_id={},
        )

        self.assertEqual(candidates, [])


def _profile_collection() -> ForestPlanProfileCollection:
    supporting_records = {
        "forest_plan": ForestPlanSourceRecord(
            role="forest_plan",
            source_record_id="R1PLAN-custer-gallatin-nf-02",
            required_for="active plan",
        ),
        "biological_opinion": ForestPlanSourceRecord(
            role="biological_opinion",
            source_record_id="R1PLAN-cg-biological-opinion",
            required_for="supporting wildlife scope",
        ),
    }
    profile = ForestPlanProfile(
        forest_unit_id="custer-gallatin-nf",
        forest_unit_names=("Custer Gallatin National Forest",),
        ambiguous_unit_terms=(),
        active_plan_source_record_id="R1PLAN-custer-gallatin-nf-02",
        supporting_source_record_ids_by_role=supporting_records,
        required_readiness_source_roles=("forest_plan",),
        ranger_district_terms=(),
        geographic_area_terms=(),
        management_area_terms=(),
        overlay_terms=(),
        plan_component_types=("standard", "guideline"),
        supporting_record_trigger_rules=(),
        review_topics=("forest_plan",),
        profile_data_source="unit-test",
    )
    return ForestPlanProfileCollection(
        schema_version="forest-plan-profiles-v0",
        profiles=(profile,),
        known_other_forest_units=(),
    )


def _profile_collection_with_flathead() -> ForestPlanProfileCollection:
    custer = _profile_collection().profiles[0]
    flathead = ForestPlanProfile(
        forest_unit_id="flathead-nf",
        forest_unit_names=("Flathead National Forest",),
        ambiguous_unit_terms=(),
        active_plan_source_record_id="R1PLAN-flathead-nf-02",
        supporting_source_record_ids_by_role={
            "forest_plan": ForestPlanSourceRecord(
                role="forest_plan",
                source_record_id="R1PLAN-flathead-nf-02",
                required_for="active plan",
            ),
        },
        required_readiness_source_roles=("forest_plan",),
        ranger_district_terms=(),
        geographic_area_terms=(),
        management_area_terms=(),
        overlay_terms=(),
        plan_component_types=("standard", "guideline"),
        supporting_record_trigger_rules=(),
        review_topics=("forest_plan",),
        profile_data_source="unit-test",
    )
    return ForestPlanProfileCollection(
        schema_version="forest-plan-profiles-v0",
        profiles=(custer, flathead),
        known_other_forest_units=(),
    )


def _catalog_record(
    source_record_id: str,
    document_role: str,
    authority_category: str,
) -> dict:
    return {
        "source_record_id": source_record_id,
        "title": f"{source_record_id} title",
        "citation_label": f"{source_record_id} | title | artifact",
        "document_role": document_role,
        "authority_level": authority_category,
        "issuer": "Unit Test",
        "scope": "Baseline",
        "layer": "authority",
        "document_type": "source",
        "unit_or_overlay": None,
        "applies_to": "EA",
        "trigger": None,
        "review_topics": [authority_category],
        "currentness_notes": "current for unit test",
        "source_status": "downloaded",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"artifacts/raw/{source_record_id}.txt",
        "artifact_byte_size": 128,
        "content_type": "text/plain",
        "retrieved_at": "2026-05-03T00:00:00Z",
    }


def _rule_template(
    rule_id: str,
    authority_source_record_id: str,
    authority_category: str,
    authority_document_role: str,
    *,
    applicability_mode: str = "baseline",
) -> dict:
    return {
        "id": rule_id,
        "title": f"{rule_id} title",
        "question": f"{rule_id} question?",
        "requirement": f"{rule_id} requirement.",
        "severity": "medium",
        "authority_category": authority_category,
        "authority_source_record_id": authority_source_record_id,
        "authority_document_role": authority_document_role,
        "applicability_mode": applicability_mode,
        "package_query": rule_id,
        "package_terms": [rule_id],
        "source_query": f"{rule_id} source",
        "source_filters": {
            "document_role": authority_document_role,
            "source_record_id": authority_source_record_id,
        },
    }
