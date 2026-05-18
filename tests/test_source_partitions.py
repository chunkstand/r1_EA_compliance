from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources.source_partitions import ACTIVE_REVIEW_CORPUS
from usfs_r1_ea_sources.source_partitions import CANDIDATE_BLOCKED_SOURCE
from usfs_r1_ea_sources.source_partitions import CURRENTNESS_SUPERSESSION_ARCHIVE
from usfs_r1_ea_sources.source_partitions import catalog_source_partition
from usfs_r1_ea_sources.source_partitions import load_source_partition_contract
from usfs_r1_ea_sources.source_partitions import validate_source_partition_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "source_partition_contract_nepa_3d_v1.json"


def test_source_partition_contract_has_fail_closed_non_active_rules() -> None:
    contract = load_source_partition_contract(CONTRACT_PATH)

    checks = {check["name"]: check for check in validate_source_partition_contract(contract)}

    assert all(check["passed"] for check in checks.values())
    assert checks["non_active_partition_relationships_are_limited_to_currentness"]["passed"]
    assert checks["source_partition_contract_defines_workbook_source_delta_plan"]["passed"]
    assert checks["source_partition_contract_defines_fsh_1909_15_chapter_boundary"]["passed"]


def test_source_partition_contract_rejects_active_rule_edges_for_archive() -> None:
    contract = load_source_partition_contract(CONTRACT_PATH)
    contract = json.loads(json.dumps(contract))
    contract["graph_relationship_rules"][CURRENTNESS_SUPERSESSION_ARCHIVE][
        "allowed_relationships"
    ].append("RULE_DERIVES_FROM_AUTHORITY")

    checks = {check["name"]: check for check in validate_source_partition_contract(contract)}

    assert not checks["non_active_partition_relationships_are_limited_to_currentness"]["passed"]
    assert checks["non_active_partition_relationships_are_limited_to_currentness"]["actual"] == {
        CURRENTNESS_SUPERSESSION_ARCHIVE: ["RULE_DERIVES_FROM_AUTHORITY"]
    }


def test_source_partition_contract_rejects_malformed_graph_rule_shape() -> None:
    contract = load_source_partition_contract(CONTRACT_PATH)
    contract = json.loads(json.dumps(contract))
    contract["graph_relationship_rules"][CURRENTNESS_SUPERSESSION_ARCHIVE] = []
    contract["graph_relationship_rules"][CANDIDATE_BLOCKED_SOURCE]["allowed_relationships"] = (
        "HAS_CURRENTNESS_STATUS"
    )

    checks = {check["name"]: check for check in validate_source_partition_contract(contract)}

    assert not checks["source_partition_contract_graph_rules_are_objects"]["passed"]
    assert not checks["source_partition_contract_graph_relationships_are_lists"]["passed"]
    assert checks["source_partition_contract_graph_rules_are_objects"]["actual"] == [
        CURRENTNESS_SUPERSESSION_ARCHIVE
    ]
    assert checks["source_partition_contract_graph_relationships_are_lists"]["actual"] == [
        CANDIDATE_BLOCKED_SOURCE,
        CURRENTNESS_SUPERSESSION_ARCHIVE,
    ]


def test_source_partition_contract_rejects_non_active_partition_eligibility() -> None:
    contract = load_source_partition_contract(CONTRACT_PATH)
    contract = json.loads(json.dumps(contract))
    contract["source_partitions"][1]["eligible_for_active_review_rules"] = True
    contract["graph_relationship_rules"][CANDIDATE_BLOCKED_SOURCE][
        "eligible_for_active_review_rules"
    ] = True

    checks = {check["name"]: check for check in validate_source_partition_contract(contract)}

    assert not checks["source_partition_contract_partition_eligibility_matches_boundary"]["passed"]
    assert not checks["non_active_partitions_are_not_eligible_for_active_review_rules"]["passed"]
    assert checks["source_partition_contract_partition_eligibility_matches_boundary"]["actual"] == {
        CURRENTNESS_SUPERSESSION_ARCHIVE: True
    }
    assert checks["non_active_partitions_are_not_eligible_for_active_review_rules"]["actual"] == [
        CANDIDATE_BLOCKED_SOURCE
    ]


def test_source_partition_contract_rejects_missing_reserved_and_delta_boundaries() -> None:
    contract = load_source_partition_contract(CONTRACT_PATH)
    contract = json.loads(json.dumps(contract))
    contract["handbook_chapter_requirements"][0]["minimum_distinct_chapter_records_when_used"] = 1
    contract["reserved_superseded_authority_rules"] = []
    del contract["workbook_source_delta_plan"]["fsh_1909_15"]

    checks = {check["name"]: check for check in validate_source_partition_contract(contract)}

    assert not checks["source_partition_contract_defines_fsh_1909_15_chapter_boundary"]["passed"]
    assert not checks["source_partition_contract_defines_reserved_36_cfr_part_220_boundary"]["passed"]
    assert not checks["source_partition_contract_defines_workbook_source_delta_plan"]["passed"]
    assert checks["source_partition_contract_defines_workbook_source_delta_plan"]["actual"] == [
        "fsh_1909_15"
    ]


def test_catalog_source_partition_handles_reserved_authority_phrase_without_36_cfr_220() -> None:
    source_partition, basis = catalog_source_partition(
        {
            "source_status": "downloaded",
            "title": "Reserved regulation for retired agency procedure",
            "currentness_notes": "Reserved authority; currentness evidence only.",
        }
    )

    assert source_partition == CURRENTNESS_SUPERSESSION_ARCHIVE
    assert basis == "non_current_source_marker"


def test_catalog_source_partition_does_not_treat_reserved_property_rights_as_noncurrent() -> None:
    source_partition, basis = catalog_source_partition(
        {
            "source_status": "downloaded",
            "title": "Reservations and Outstanding Rights",
            "currentness_notes": "Use with reserved mineral and easement terms.",
        }
    )

    assert source_partition == ACTIVE_REVIEW_CORPUS
    assert basis == "successful_status:downloaded"


def test_catalog_source_partition_keeps_blocked_records_visible_but_not_active() -> None:
    source_partition, basis = catalog_source_partition(
        {
            "source_status": "challenge_page",
            "title": "Blocked source candidate",
        }
    )

    assert source_partition == CANDIDATE_BLOCKED_SOURCE
    assert basis == "blocked_or_unavailable_status:challenge_page"


def test_catalog_source_partition_archives_retained_historical_plan_amendments() -> None:
    source_partition, basis = catalog_source_partition(
        {
            "source_status": "downloaded_existing",
            "title": "Forest Plan Amendment 28",
            "currentness_notes": "Retained/historical plan amendment; verify applicability under current LMP",
            "metadata": {
                "loader_contract": "source_register_v1",
                "authority_tier": "Forest",
                "currentness_status": "Retained/historical plan amendment; verify applicability under current LMP",
            },
        }
    )

    assert source_partition == CURRENTNESS_SUPERSESSION_ARCHIVE
    assert basis == "non_current_source_marker"


def test_catalog_source_partition_archives_historical_transition_support_rows() -> None:
    source_partition, basis = catalog_source_partition(
        {
            "source_status": "downloaded_existing",
            "title": "Monitoring Transition Letter",
            "currentness_notes": "Historical/current transition support",
            "metadata": {
                "loader_contract": "source_register_v1",
                "authority_tier": "Forest",
                "currentness_status": "Historical/current transition support",
            },
        }
    )

    assert source_partition == CURRENTNESS_SUPERSESSION_ARCHIVE
    assert basis == "non_current_source_marker"


def test_catalog_source_partition_overrides_stale_canonical_active_partition() -> None:
    source_partition, basis = catalog_source_partition(
        {
            "source_status": "downloaded_existing",
            "source_partition": "active_review_corpus",
            "title": "Forest Plan Amendment 1",
            "currentness_notes": "Retained/historical plan amendment; verify applicability under current LMP",
            "metadata": {
                "loader_contract": "source_register_v1",
                "authority_tier": "Forest",
                "currentness_status": "Retained/historical plan amendment; verify applicability under current LMP",
            },
        }
    )

    assert source_partition == CURRENTNESS_SUPERSESSION_ARCHIVE
    assert basis == "canonical_row_currentness_override"
