from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path

from usfs_r1_ea_sources.package_fact_graph import _base_term_specs


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_PATH = REPO_ROOT / "config" / "authority_family_rule_templates_nepa_ea_v1.json"
COVERAGE_PATH = (
    REPO_ROOT / "config" / "authority_family_rule_template_coverage_nepa_ea_v1.json"
)
INVENTORY_PATH = REPO_ROOT / "config" / "authority_universe_families_nepa_ea_v1.json"
CATALOG_PATH = REPO_ROOT / "source_library" / "catalog" / "source_catalog.jsonl"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def test_authority_family_templates_have_milestone_3_contracts() -> None:
    templates = _load_json(TEMPLATES_PATH)
    inventory = _load_json(INVENTORY_PATH)
    catalog_by_id = _load_catalog_by_source_id()

    assert templates["schema_version"] == "authority-family-rule-templates-v1"
    assert templates["template_set_id"] == "nepa-ea-authority-family-rule-templates-v1"
    template_rows = templates["templates"]
    assert len(template_rows) == 19

    rule_ids = [row["rule_id"] for row in template_rows]
    assert len(rule_ids) == len(set(rule_ids))
    assert all(SAFE_ID_RE.fullmatch(rule_id) for rule_id in rule_ids)

    families_by_id = {
        family["family_id"]: family for family in inventory["authority_families"]
    }
    assert inventory["summary"]["families_requiring_milestone_3_rule_template_work"] == 0
    assert inventory["summary"]["families_confirmed_by_milestone_3_rule_templates"] == 19

    for template in template_rows:
        family = families_by_id[template["authority_family_id"]]
        primary_source = catalog_by_id[template["authority_source_record_id"]]
        assert family["status"] == "active"
        assert family["rule_template_ids"] == [template["rule_id"]]
        assert template["rule_id"] in family["coverage_requirements"][
            "authority_family_rule_template_ids"
        ]
        assert template["source_record_ids"] == family["source_record_ids"]
        assert template["package_fact_types"] == family["package_fact_types"]
        assert template["applies_if_package_terms"]
        assert template["applies_if_package_term_groups"]
        assert template["does_not_apply_if_package_terms"]
        assert template["source_evidence_requirements"]
        assert primary_source["artifact_sha256"]
        assert primary_source["source_status"] in {
            "downloaded",
            "downloaded_existing",
            "duplicate_content",
            "duplicate_url",
        }


def test_authority_family_template_coverage_maps_every_template() -> None:
    templates = _load_json(TEMPLATES_PATH)
    coverage = _load_json(COVERAGE_PATH)

    assert coverage["schema_version"] == "authority-family-rule-template-coverage-v1"
    assert coverage["template_set_id"] == templates["template_set_id"]

    template_rule_ids = {template["rule_id"] for template in templates["templates"]}
    coverage_rule_ids = {
        entry["rule_template_id"] for entry in coverage["coverage_entries"]
    }
    assert coverage_rule_ids == template_rule_ids
    assert coverage["summary"]["coverage_entry_count"] == len(template_rule_ids)

    duplicate_families = [
        family_id
        for family_id, count in Counter(
            entry["authority_family_id"] for entry in coverage["coverage_entries"]
        ).items()
        if count > 1
    ]
    assert duplicate_families == []


def test_package_fact_cues_map_to_active_authority_family_templates() -> None:
    templates = _load_json(TEMPLATES_PATH)
    inventory = _load_json(INVENTORY_PATH)
    template_by_family_id = {
        template["authority_family_id"]: template for template in templates["templates"]
    }
    family_by_id = {
        family["family_id"]: family for family in inventory["authority_families"]
    }

    expected_family_terms = {
        "clean_water_act_wotus_permits": ["Clean Water Act", "wetlands"],
        "floodplain_management_eo11988": ["floodplain"],
        "tribal_consultation_trust_sacred_sites": ["tribal consultation"],
        "wilderness_wsr_trails_designated_areas": ["wilderness", "designated area"],
        "land_exchange_regulatory_requirements": ["land exchange"],
    }
    for family_id, required_terms in expected_family_terms.items():
        family = family_by_id[family_id]
        template = template_by_family_id[family_id]
        trigger_blob = " ".join(template["applies_if_package_terms"]).lower()
        assert family["status"] == "active"
        assert all(term.lower() in trigger_blob for term in required_terms)

    package_fact_values = {
        (spec["node_type"], spec["normalized_value"]) for spec in _base_term_specs()
    }
    assert ("permit", "clean_water_act") in package_fact_values
    assert ("permit", "floodplains") in package_fact_values
    assert ("consultation", "tribal_consultation") in package_fact_values
    assert ("permit", "wilderness") in package_fact_values
    assert ("overlay", "designated_area") in package_fact_values
    assert ("action", "land_exchange") in package_fact_values


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_catalog_by_source_id() -> dict[str, dict]:
    records = {}
    for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        records[row["source_record_id"]] = row
    return records
