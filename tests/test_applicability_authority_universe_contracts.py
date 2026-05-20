from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_authority_family_templates import authority_family_template_candidates
from usfs_r1_ea_sources.applicability_authority_universe_contracts import authority_universe_summary
from usfs_r1_ea_sources.applicability_authority_universe_contracts import authority_universe_validation
from usfs_r1_ea_sources.applicability_candidate_assembly import forest_plan_component_candidates
from usfs_r1_ea_sources.applicability_candidate_assembly import rule_template_candidates
from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanProfile
from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanProfileCollection
from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanSourceRecord
from usfs_r1_ea_sources.rule_packs import validate_rule_pack


class AuthorityUniverseContractsTests(unittest.TestCase):
    def test_validation_passes_for_complete_candidate_universe(self) -> None:
        source_set_id = "source-set-test"
        rule_pack = _rule_pack()
        profiles = _profile_collection()
        template_set = _template_set()
        component_inventory = _component_inventory(source_set_id)
        catalog_by_source_id = _catalog_by_source_id(source_set_id)
        candidate_authorities = _candidate_authorities(
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            profiles=profiles,
            template_set=template_set,
            component_inventory=component_inventory,
            catalog_by_source_id=catalog_by_source_id,
            source_claim_links_by_rule=_source_claim_links_by_rule(),
            source_claim_gaps_by_rule={},
        )

        validation = authority_universe_validation(
            created_at="2026-05-20T12:00:00Z",
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            rule_pack_validation=validate_rule_pack(rule_pack),
            candidate_authorities=candidate_authorities,
            profiles=profiles,
            component_inventory=component_inventory,
            authority_family_templates=template_set,
        )

        self.assertTrue(validation["passed"])
        self.assertEqual(validation["source_set_id"], source_set_id)
        checks = {check["name"]: check for check in validation["checks"]}
        self.assertTrue(checks["rule_pack_valid"]["passed"])
        self.assertTrue(checks["rule_template_candidates_cover_rule_pack"]["passed"])
        self.assertTrue(checks["conditional_rule_candidates_present"]["passed"])
        self.assertTrue(checks["authority_family_template_candidates_cover_config"]["passed"])
        self.assertTrue(checks["forest_plan_component_candidates_use_profile_inventory"]["passed"])
        self.assertEqual(
            checks["forest_plan_component_candidates_use_profile_inventory"]["details"][
                "component_candidate_count"
            ],
            1,
        )

    def test_validation_failure_and_summary_counts_are_reported_directly(self) -> None:
        source_set_id = "source-set-test"
        rule_pack = _rule_pack()
        profiles = _profile_collection()
        template_set = _template_set()
        component_inventory = _component_inventory(source_set_id)
        catalog_by_source_id = _catalog_by_source_id(source_set_id)
        candidate_authorities = _candidate_authorities(
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            profiles=profiles,
            template_set=template_set,
            component_inventory=component_inventory,
            catalog_by_source_id=catalog_by_source_id,
            source_claim_links_by_rule={},
            source_claim_gaps_by_rule={},
        )
        validation = authority_universe_validation(
            created_at="2026-05-20T12:00:00Z",
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            rule_pack_validation=validate_rule_pack(rule_pack),
            candidate_authorities=candidate_authorities,
            profiles=profiles,
            component_inventory=component_inventory,
            authority_family_templates=template_set,
        )

        self.assertFalse(validation["passed"])
        checks = {check["name"]: check for check in validation["checks"]}
        self.assertFalse(checks["rule_template_candidates_have_source_claim_linkage"]["passed"])
        self.assertEqual(
            checks["rule_template_candidates_have_source_claim_linkage"]["details"][
                "failure_count"
            ],
            3,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_set_manifest_path = _touch(root / "catalog" / "source_set_manifest.json")
            source_catalog_path = _touch(root / "catalog" / "source_catalog.jsonl")
            forest_plan_profiles_path = _touch(root / "config" / "forest_plan_profiles.json")
            component_inventory_path = _touch(
                root / "derived" / source_set_id / "forest_plan_components" / "component_inventory.json"
            )
            claims_path = _touch(root / "derived" / source_set_id / "claims" / "source_claims.jsonl")
            rule_claim_links_path = _touch(
                root / "derived" / source_set_id / "rule_claim_links" / "rule_claim_links.jsonl"
            )
            rule_claim_gaps_path = _touch(
                root / "derived" / source_set_id / "rule_claim_links" / "rule_claim_link_gaps.jsonl"
            )
            authority_family_templates_path = _touch(root / "config" / "authority_family_templates.json")

            summary = authority_universe_summary(
                authority_universe_id="authority-universe:test",
                authority_universe_sha256="summary-sha256",
                review_id="review-unit",
                source_set_id=source_set_id,
                base_rule_pack=rule_pack,
                source_set_manifest_path=source_set_manifest_path,
                source_catalog_path=source_catalog_path,
                forest_plan_profiles_path=forest_plan_profiles_path,
                forest_plan_component_inventory_path=component_inventory_path,
                claims_path=claims_path,
                rule_claim_links_path=rule_claim_links_path,
                rule_claim_gaps_path=rule_claim_gaps_path,
                authority_family_templates_path=authority_family_templates_path,
                candidate_authorities=candidate_authorities,
                validation=validation,
            )

        self.assertEqual(summary["candidate_authority_count"], 5)
        self.assertEqual(summary["rule_template_candidate_count"], 3)
        self.assertEqual(summary["authority_family_rule_template_candidate_count"], 1)
        self.assertEqual(summary["forest_plan_component_candidate_count"], 1)
        self.assertEqual(
            summary["rule_applicability_mode_counts"],
            {"baseline": 2, "conditional": 1},
        )
        self.assertEqual(
            summary["authority_family_template_applicability_mode_counts"],
            {"conditional": 1},
        )
        self.assertEqual(
            summary["candidate_contract_counts"]["with_search_coverage_requirements"],
            5,
        )
        self.assertFalse(summary["validation_passed"])
        self.assertEqual(summary["forest_plan_component_inventory_path"], str(component_inventory_path))
        self.assertEqual(summary["authority_family_templates_path"], str(authority_family_templates_path))


def _candidate_authorities(
    *,
    source_set_id: str,
    rule_pack: dict,
    profiles: ForestPlanProfileCollection,
    template_set: dict,
    component_inventory: dict,
    catalog_by_source_id: dict[str, dict],
    source_claim_links_by_rule: dict[str, list[dict]],
    source_claim_gaps_by_rule: dict[str, list[dict]],
) -> list[dict]:
    rule_candidates = rule_template_candidates(
        source_set_id=source_set_id,
        rule_pack=rule_pack,
        catalog_by_source_id=catalog_by_source_id,
        source_claim_links_by_rule=source_claim_links_by_rule,
        source_claim_gaps_by_rule=source_claim_gaps_by_rule,
    )
    family_candidates = authority_family_template_candidates(
        source_set_id=source_set_id,
        template_set=template_set,
        catalog_by_source_id=catalog_by_source_id,
    )
    component_candidates = forest_plan_component_candidates(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        component_inventory_path=Path("source_library/derived/source-set-test/forest_plan_components/component_inventory.json"),
        component_inventory_sha256="inventory-sha256",
        catalog_by_source_id=catalog_by_source_id,
    )
    return [*rule_candidates, *family_candidates, *component_candidates]


def _rule_pack() -> dict:
    return {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "title": "Unit NEPA EA Rule Pack",
        "baseline_source_record_ids": ["R1EA-BASE", "R1PLAN-custer-gallatin-nf-02"],
        "rules": [
            _rule(
                rule_id="baseline_authority",
                source_record_id="R1EA-BASE",
                authority_category="law",
                document_role="law",
                applicability_mode="baseline",
            ),
            _rule(
                rule_id="conditional_authority",
                source_record_id="R1EA-COND",
                authority_category="regulation",
                document_role="regulation",
                applicability_mode="conditional",
                applies_if_package_terms=["road construction"],
                does_not_apply_if_package_terms=["no road construction"],
                package_section_terms=["transportation"],
            ),
            _rule(
                rule_id="custer_gallatin_lmp_2022",
                source_record_id="R1PLAN-custer-gallatin-nf-02",
                authority_category="forest_plan",
                document_role="forest_plan",
                applicability_mode="baseline",
            ),
        ],
    }


def _rule(
    *,
    rule_id: str,
    source_record_id: str,
    authority_category: str,
    document_role: str,
    applicability_mode: str,
    applies_if_package_terms: list[str] | None = None,
    does_not_apply_if_package_terms: list[str] | None = None,
    package_section_terms: list[str] | None = None,
) -> dict:
    rule = {
        "id": rule_id,
        "title": f"{rule_id} title",
        "authority_category": authority_category,
        "authority_source_record_id": source_record_id,
        "authority_document_role": document_role,
        "applicability_mode": applicability_mode,
        "question": f"Does the package address {rule_id}?",
        "requirement": f"The package should address {rule_id}.",
        "package_query": f"{rule_id} package evidence",
        "package_terms": [rule_id.replace("_", " ")],
        "source_query": f"{rule_id} source evidence",
        "source_filters": {
            "document_role": document_role,
            "source_record_id": source_record_id,
        },
        "severity": "medium",
    }
    if applies_if_package_terms:
        rule["applies_if_package_terms"] = applies_if_package_terms
    if does_not_apply_if_package_terms:
        rule["does_not_apply_if_package_terms"] = does_not_apply_if_package_terms
    if package_section_terms:
        rule["package_section_terms"] = package_section_terms
    return rule


def _template_set() -> dict:
    return {
        "schema_version": "authority-family-rule-templates-v1",
        "template_set_id": "unit-authority-family-templates",
        "version": "0.1.0",
        "templates": [
            {
                "template_id": "clean_water_unit_template",
                "authority_family_id": "clean_water_unit",
                "rule_id": "clean_water_unit_authority_template",
                "title": "Clean Water Unit applicability template",
                "authority_category": "law",
                "authority_document_role": "law",
                "authority_source_record_id": "R1EA-FAMILY",
                "source_record_ids": ["R1EA-FAMILY"],
                "supporting_source_record_ids": [],
                "excluded_source_record_ids": [],
                "applicability_mode": "conditional",
                "severity": "medium",
                "question": "Does the package trigger Clean Water Act review?",
                "requirement": "Evaluate source-backed Clean Water Act applicability.",
                "package_query": "wetlands",
                "package_terms": ["wetlands"],
                "package_fact_types": ["permit", "resource_topic"],
                "package_section_terms": ["water resources"],
                "applies_if_package_terms": ["wetlands"],
                "applies_if_package_term_groups": [["wetlands"]],
                "does_not_apply_if_package_terms": ["no wetlands"],
                "source_query": "Clean Water Act source",
                "source_filters": {
                    "document_role": "law",
                    "source_record_id": "R1EA-FAMILY",
                },
                "source_evidence_requirements": ["catalog-confirmed source"],
                "evidence_expectation": "A supported decision requires source evidence and wetlands evidence.",
            }
        ],
    }


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


def _component_inventory(source_set_id: str) -> dict:
    component_id = "R1PLAN-custer-gallatin-nf-02-STD-01"
    return {
        "inventory_id": "unit-inventory",
        "source_set_id": source_set_id,
        "forest_unit_id": "custer-gallatin-nf",
        "plan_version": "2022",
        "components": [
            {
                "component_id": component_id,
                "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                "component_type": "standard",
                "section_id": "std-01",
                "section_heading": "Plan Components",
                "artifact_sha256": hashlib.sha256(component_id.encode("utf-8")).hexdigest(),
                "source_chunk_ids": [f"chunk:{component_id}"],
                "package_evidence_terms": ["road"],
                "resource_topics": ["access"],
                "activity_tags": ["construction"],
                "geographic_area_ids": [],
                "management_area_ids": ["mgmt-crazy-mountains-bca"],
                "overlay_ids": [],
            }
        ],
    }


def _catalog_by_source_id(source_set_id: str) -> dict[str, dict]:
    records = [
        _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
        _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
        _catalog_record(source_set_id, "R1EA-FAMILY", "law", "law"),
        _catalog_record(
            source_set_id,
            "R1PLAN-custer-gallatin-nf-02",
            "forest_plan",
            "forest_plan",
        ),
    ]
    return {record["source_record_id"]: record for record in records}


def _catalog_record(
    source_set_id: str,
    source_record_id: str,
    document_role: str,
    authority_category: str,
) -> dict:
    return {
        "source_set_id": source_set_id,
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


def _source_claim_links_by_rule() -> dict[str, list[dict]]:
    return {
        "baseline_authority": [{"link_id": "link:baseline_authority"}],
        "conditional_authority": [{"link_id": "link:conditional_authority"}],
        "custer_gallatin_lmp_2022": [{"link_id": "link:custer_gallatin_lmp_2022"}],
    }


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return path
