from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.workbook import load_canonical_sources


REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "config" / "authority_universe_families_nepa_ea_v1.json"
RULE_PACK_PATH = REPO_ROOT / "config" / "compliance_rule_pack_nepa_ea_v0.json"
WORKBOOK_PATH = REPO_ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
DOWNLOADER_CONFIG_PATH = REPO_ROOT / "config" / "downloader.toml"
VALID_STATUSES = {"active", "source_only", "candidate", "out_of_scope", "superseded"}


def test_authority_inventory_has_valid_family_contract() -> None:
    inventory = _load_json(INVENTORY_PATH)

    assert inventory["schema_version"] == "authority-universe-families-v1"
    families = inventory["authority_families"]
    family_ids = [family["family_id"] for family in families]
    assert len(family_ids) == len(set(family_ids))
    assert inventory["summary"]["authority_family_count"] == len(families)

    for family in families:
        assert family["status"] in VALID_STATUSES
        assert family["rationale"]
        assert family["coverage_requirements"]["source_record_ids"] == family["source_record_ids"]
        assert family["applicability_predicates"]
        assert family["source_record_mapping"]["mapped_source_record_ids"] == family["source_record_ids"]
        assert family["source_record_mapping"]["catalog_source_record_ids"] == family["source_record_ids"]
        assert family["status"] == "candidate" or family["source_record_ids"]
        if family["status"] == "active":
            assert family["rule_ids"]
            assert family["coverage_requirements"]["coverage_matrix_rule_ids"]
            assert family["coverage_requirements"]["eval_case_ids"]
        if family["status"] == "source_only":
            assert family["source_record_ids"]
            assert family["open_inventory_gaps"]
            assert family["rule_ids"] == []
            assert family["source_record_mapping"]["mapping_status"] == "mapped_source_only_family"
        if family["status"] == "candidate":
            assert family["open_inventory_gaps"]
            assert family["source_record_mapping"]["missing_source_record_requirements"]
            assert family["source_record_mapping"]["mapping_status"] == "candidate_source_records_needed"
        if family["status"] == "superseded":
            supersession = family["supersession"]
            assert supersession
            assert supersession["replacement_family_id"] in family_ids
            assert supersession["current_source_record_ids"]
            assert family["open_inventory_gaps"]

    for requirement in inventory["required_authority_family_coverage"]:
        assert requirement["requirement_id"]
        assert requirement["family_ids"]
        assert set(requirement["family_ids"]).issubset(family_ids)


def test_authority_inventory_maps_every_rule_pack_rule_once() -> None:
    inventory = _load_json(INVENTORY_PATH)
    rule_pack = _load_json(RULE_PACK_PATH)
    family_by_id = {family["family_id"]: family for family in inventory["authority_families"]}
    rule_to_family: dict[str, str] = {}
    duplicated_rules: list[str] = []

    for family in inventory["authority_families"]:
        for rule_id in family["rule_ids"]:
            if rule_id in rule_to_family:
                duplicated_rules.append(rule_id)
            rule_to_family[rule_id] = family["family_id"]

    expected_rule_ids = {rule["id"] for rule in rule_pack["rules"]}
    assert sorted(rule_to_family) == sorted(expected_rule_ids)
    assert duplicated_rules == []
    assert inventory["summary"]["orphan_rule_ids"] == []
    assert inventory["summary"]["duplicate_rule_ids"] == []
    assert inventory["summary"]["rule_count"] == len(expected_rule_ids)
    assert inventory["summary"]["mapped_rule_count"] == len(rule_to_family)

    for rule in rule_pack["rules"]:
        family = family_by_id[rule_to_family[rule["id"]]]
        assert rule["authority_source_record_id"] in family["source_record_ids"]
        assert rule["id"] in family["coverage_requirements"]["coverage_matrix_rule_ids"]


def test_authority_inventory_maps_every_workbook_source_record() -> None:
    inventory = _load_json(INVENTORY_PATH)
    config = load_config(DOWNLOADER_CONFIG_PATH)
    sources = load_canonical_sources(WORKBOOK_PATH, config.workbook)
    workbook_ids = {source.source_record_id for source in sources}
    family_ids = {family["family_id"] for family in inventory["authority_families"]}
    family_source_ids = {
        source_record_id
        for family in inventory["authority_families"]
        for source_record_id in family["source_record_ids"]
    }
    crosswalk = inventory["source_record_crosswalk"]

    assert {row["source_record_id"] for row in crosswalk} == workbook_ids
    assert workbook_ids.issubset(family_source_ids)
    assert family_source_ids.issubset(workbook_ids)
    assert inventory["summary"]["orphan_source_record_ids"] == []
    assert inventory["summary"]["source_record_crosswalk_count"] == len(sources)
    assert inventory["summary"]["workbook_source_record_count"] == len(sources)
    assert inventory["summary"]["mapped_source_record_count"] == len(workbook_ids)

    duplicate_crosswalk_ids = [
        source_record_id
        for source_record_id, count in Counter(row["source_record_id"] for row in crosswalk).items()
        if count > 1
    ]
    assert duplicate_crosswalk_ids == []

    for row in crosswalk:
        assert row["primary_family_id"] in family_ids
        assert set(row["related_family_ids"]).issubset(family_ids)

    excluded_project_reference = next(row for row in crosswalk if row["source_record_id"] == "R1EA-160")
    assert excluded_project_reference["mapping_status"] == "mapped_source_url_excluded"
    assert excluded_project_reference["primary_family_id"] == "land_exchange_fs_policy_and_project_references"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
