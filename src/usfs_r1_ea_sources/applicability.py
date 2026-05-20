from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re

from .applicability_candidate_assembly import forest_plan_component_candidates
from .applicability_candidate_assembly import rule_template_candidates
from .applicability_authority_family_templates import authority_family_template_candidates
from .applicability_contract_support import rule_source_record_id as _rule_source_record_id
from .applicability_contract_support import string_groups as _string_groups
from .applicability_contract_support import strings as _strings
from .claim_extraction import default_claims_path
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import ForestPlanProfileCollection
from .forest_plan_profiles import load_forest_plan_profiles
from .records import sha256_file
from .rule_claim_binding import default_rule_claim_links_path
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


AUTHORITY_UNIVERSE_SCHEMA_VERSION = "authority-universe-snapshot-v0"
AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION = "authority-family-rule-templates-v1"
DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH = Path(
    "config/authority_family_rule_templates_nepa_ea_v1.json"
)
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class AuthorityUniverseSnapshotResult:
    review_id: str
    source_set_id: str
    applicability_dir: Path
    snapshot_path: Path
    summary: dict


def build_authority_universe_snapshot(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    source_catalog_path: Path | None = None,
    source_set_manifest_path: Path | None = None,
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    authority_family_templates_path: Path | None = DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
    forest_plan_component_inventory_path: Path | None = None,
    claims_path: Path | None = None,
    rule_claim_links_path: Path | None = None,
) -> AuthorityUniverseSnapshotResult:
    """Build the candidate authority universe used by applicability determination."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    catalog_dir = output_dir / "catalog"
    source_set_manifest_path = (
        Path(source_set_manifest_path)
        if source_set_manifest_path
        else catalog_dir / "source_set_manifest.json"
    )
    source_catalog_path = (
        Path(source_catalog_path)
        if source_catalog_path
        else catalog_dir / "source_catalog.jsonl"
    )
    source_set_manifest = _read_json_if_exists(source_set_manifest_path) or {}
    if source_set_id is None:
        source_set_id = _source_set_id_from_manifest(source_set_manifest_path, source_set_manifest)
    _validate_safe_segment(source_set_id, "source_set_id")
    catalog_records = _load_source_catalog(source_catalog_path, source_set_id)
    catalog_by_source_id = {
        str(record["source_record_id"]): record for record in catalog_records
    }

    base_rule_pack_path = Path(base_rule_pack_path)
    if not base_rule_pack_path.exists():
        raise FileNotFoundError(f"Missing base rule pack: {base_rule_pack_path}")
    base_rule_pack = load_rule_pack(base_rule_pack_path)
    rule_pack_validation = validate_rule_pack(base_rule_pack)
    base_rule_pack_sha256 = sha256_file(base_rule_pack_path)

    forest_plan_profiles_path = Path(forest_plan_profiles_path)
    profiles = load_forest_plan_profiles(forest_plan_profiles_path)
    profiles_sha256 = sha256_file(forest_plan_profiles_path)

    authority_family_templates_path = (
        Path(authority_family_templates_path)
        if authority_family_templates_path
        else None
    )
    authority_family_templates = (
        _load_authority_family_templates(authority_family_templates_path)
        if authority_family_templates_path
        else None
    )
    authority_family_templates_sha256 = (
        sha256_file(authority_family_templates_path)
        if authority_family_templates_path and authority_family_templates_path.exists()
        else None
    )

    claims_path = claims_path or default_claims_path(output_dir, source_set_id)
    rule_claim_links_path = rule_claim_links_path or default_rule_claim_links_path(
        output_dir,
        source_set_id=source_set_id,
        rule_pack_path=base_rule_pack_path,
    )
    rule_claim_gaps_path = rule_claim_links_path.parent / "rule_claim_link_gaps.jsonl"
    source_claim_links = _read_jsonl_if_exists(rule_claim_links_path)
    source_claim_gaps = _read_jsonl_if_exists(rule_claim_gaps_path)
    source_claim_links_by_rule = _records_by_key(source_claim_links, "rule_id")
    source_claim_gaps_by_rule = _records_by_key(source_claim_gaps, "rule_id")

    forest_plan_component_inventory_path = (
        Path(forest_plan_component_inventory_path)
        if forest_plan_component_inventory_path
        else _default_forest_plan_component_inventory_path(output_dir, source_set_id)
    )
    component_inventory = _read_json_if_exists(forest_plan_component_inventory_path)
    component_inventory_sha256 = (
        sha256_file(forest_plan_component_inventory_path)
        if forest_plan_component_inventory_path.exists()
        else None
    )

    created_at = _utc_now()
    rule_candidates = rule_template_candidates(
        source_set_id=source_set_id,
        rule_pack=base_rule_pack,
        catalog_by_source_id=catalog_by_source_id,
        source_claim_links_by_rule=source_claim_links_by_rule,
        source_claim_gaps_by_rule=source_claim_gaps_by_rule,
    )
    authority_family_candidates = authority_family_template_candidates(
        source_set_id=source_set_id,
        template_set=authority_family_templates,
        catalog_by_source_id=catalog_by_source_id,
    )
    component_candidates = forest_plan_component_candidates(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        component_inventory_path=forest_plan_component_inventory_path,
        component_inventory_sha256=component_inventory_sha256,
        catalog_by_source_id=catalog_by_source_id,
    )
    candidate_authorities = sorted(
        [*rule_candidates, *authority_family_candidates, *component_candidates],
        key=lambda candidate: str(candidate["candidate_authority_id"]),
    )
    authority_universe_sha256 = _stable_sha256(
        {
            "schema_version": AUTHORITY_UNIVERSE_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "base_rule_pack_sha256": base_rule_pack_sha256,
            "source_set_manifest_sha256": _optional_file_sha256(source_set_manifest_path),
            "catalog_sha256": _optional_file_sha256(source_catalog_path),
            "profiles_sha256": profiles_sha256,
            "authority_family_templates_sha256": authority_family_templates_sha256,
            "component_inventory_sha256": component_inventory_sha256,
            "source_claims_sha256": _optional_file_sha256(claims_path),
            "rule_claim_links_sha256": _optional_file_sha256(rule_claim_links_path),
            "rule_claim_gaps_sha256": _optional_file_sha256(rule_claim_gaps_path),
            "candidate_authorities": candidate_authorities,
        }
    )
    authority_universe_id = (
        f"authority-universe:{review_id}:{source_set_id}:{authority_universe_sha256[:16]}"
    )
    validation = _authority_universe_validation(
        source_set_id=source_set_id,
        rule_pack=base_rule_pack,
        rule_pack_validation=rule_pack_validation,
        candidate_authorities=candidate_authorities,
        profiles=profiles,
        component_inventory=component_inventory,
        authority_family_templates=authority_family_templates,
    )
    summary = _summary(
        authority_universe_id=authority_universe_id,
        authority_universe_sha256=authority_universe_sha256,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack=base_rule_pack,
        source_set_manifest_path=source_set_manifest_path,
        source_catalog_path=source_catalog_path,
        forest_plan_profiles_path=forest_plan_profiles_path,
        forest_plan_component_inventory_path=forest_plan_component_inventory_path,
        claims_path=claims_path,
        rule_claim_links_path=rule_claim_links_path,
        rule_claim_gaps_path=rule_claim_gaps_path,
        authority_family_templates_path=authority_family_templates_path,
        candidate_authorities=candidate_authorities,
        validation=validation,
    )
    snapshot = {
        "schema_version": AUTHORITY_UNIVERSE_SCHEMA_VERSION,
        "created_at": created_at,
        "authority_universe_id": authority_universe_id,
        "authority_universe_version": "0.1.0",
        "authority_universe_sha256": authority_universe_sha256,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "source_set_manifest_sha256": _optional_file_sha256(source_set_manifest_path),
        "catalog_sha256": _optional_file_sha256(source_catalog_path),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_pack_sha256": base_rule_pack_sha256,
        "forest_plan_profiles_sha256": profiles_sha256,
        "forest_plan_profile_ids": _forest_plan_profile_ids(profiles),
        "authority_family_templates_sha256": authority_family_templates_sha256,
        "authority_family_template_set_id": (
            authority_family_templates.get("template_set_id")
            if isinstance(authority_family_templates, dict)
            else None
        ),
        "forest_plan_component_inventory_id": _component_inventory_id(component_inventory),
        "forest_plan_component_inventory_sha256": component_inventory_sha256,
        "source_claims_sha256": _optional_file_sha256(claims_path),
        "rule_claim_links_sha256": _optional_file_sha256(rule_claim_links_path),
        "rule_claim_gaps_sha256": _optional_file_sha256(rule_claim_gaps_path),
        "artifact_paths": {
            "source_set_manifest_path": str(source_set_manifest_path),
            "source_catalog_path": str(source_catalog_path),
            "base_rule_pack_path": str(base_rule_pack_path),
            "forest_plan_profiles_path": str(forest_plan_profiles_path),
            "authority_family_templates_path": (
                str(authority_family_templates_path)
                if authority_family_templates_path
                else None
            ),
            "forest_plan_component_inventory_path": (
                str(forest_plan_component_inventory_path)
                if forest_plan_component_inventory_path.exists()
                else None
            ),
            "claims_path": str(claims_path) if claims_path.exists() else None,
            "rule_claim_links_path": (
                str(rule_claim_links_path) if rule_claim_links_path.exists() else None
            ),
            "rule_claim_gaps_path": (
                str(rule_claim_gaps_path) if rule_claim_gaps_path.exists() else None
            ),
        },
        "summary": summary,
        "validation": validation,
        "candidate_authorities": candidate_authorities,
    }

    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    snapshot_path = applicability_dir / "authority_universe_snapshot.json"
    _write_json(snapshot_path, snapshot)
    return AuthorityUniverseSnapshotResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        snapshot_path=snapshot_path,
        summary=summary,
    )


def _authority_universe_validation(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    candidate_authorities: list[dict],
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
    authority_family_templates: dict | None,
) -> dict:
    checks = [
        {
            "name": "rule_pack_valid",
            "passed": bool(rule_pack_validation.get("passed")),
            "details": {
                "failed_checks": [
                    check.get("name")
                    for check in rule_pack_validation.get("checks", [])
                    if not check.get("passed")
                ],
            },
        },
        _check_candidate_ids_unique(candidate_authorities),
        _check_rule_template_candidates_cover_rule_pack(rule_pack, candidate_authorities),
        _check_conditional_rule_candidates_present(rule_pack, candidate_authorities),
        _check_source_record_provenance(candidate_authorities),
        _check_candidate_authority_metadata(candidate_authorities),
        _check_source_evidence_available(candidate_authorities),
        _check_source_claim_linkage_recorded(candidate_authorities),
        _check_applicability_contracts(candidate_authorities),
        _check_candidate_pre_review_contracts(candidate_authorities),
        _check_authority_family_template_candidates(
            authority_family_templates=authority_family_templates,
            candidate_authorities=candidate_authorities,
        ),
        _check_forest_plan_component_candidates(
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            candidate_authorities=candidate_authorities,
            profiles=profiles,
            component_inventory=component_inventory,
        ),
    ]
    return {
        "schema_version": "authority-universe-validation-v0",
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_candidate_ids_unique(candidate_authorities: list[dict]) -> dict:
    counts = Counter(
        str(candidate.get("candidate_authority_id") or "")
        for candidate in candidate_authorities
    )
    duplicates = sorted(
        candidate_id
        for candidate_id, count in counts.items()
        if candidate_id and count > 1
    )
    missing = sum(1 for candidate_id in counts if not candidate_id)
    return {
        "name": "candidate_authority_ids_unique",
        "passed": not duplicates and missing == 0,
        "details": {
            "candidate_count": len(candidate_authorities),
            "duplicate_candidate_authority_ids": duplicates,
            "missing_candidate_authority_id_count": missing,
        },
    }


def _check_rule_template_candidates_cover_rule_pack(
    rule_pack: dict,
    candidate_authorities: list[dict],
) -> dict:
    expected = {str(rule.get("id") or "") for rule in rule_pack.get("rules", [])}
    actual = {
        str(candidate.get("rule_template", {}).get("rule_id") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
    }
    return {
        "name": "rule_template_candidates_cover_rule_pack",
        "passed": expected == actual and bool(expected),
        "details": {
            "expected_rule_count": len(expected),
            "actual_rule_candidate_count": len(actual),
            "missing_rule_ids": sorted(expected - actual),
            "unexpected_rule_ids": sorted(actual - expected),
        },
    }


def _check_conditional_rule_candidates_present(
    rule_pack: dict,
    candidate_authorities: list[dict],
) -> dict:
    expected = {
        str(rule.get("id") or "")
        for rule in rule_pack.get("rules", [])
        if rule.get("applicability_mode") == "conditional"
    }
    actual = {
        str(candidate.get("rule_template", {}).get("rule_id") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
        and candidate.get("rule_template", {}).get("applicability_mode") == "conditional"
    }
    return {
        "name": "conditional_rule_candidates_present",
        "passed": expected == actual,
        "details": {
            "expected_conditional_rule_count": len(expected),
            "actual_conditional_candidate_count": len(actual),
            "missing_conditional_rule_ids": sorted(expected - actual),
        },
    }


def _check_source_record_provenance(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if not candidate.get("source_record_ids")
    ]
    return {
        "name": "candidates_have_source_record_provenance",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_candidate_authority_metadata(candidate_authorities: list[dict]) -> dict:
    failures = []
    for candidate in candidate_authorities:
        missing = []
        if not str(candidate.get("authority_category") or "").strip():
            missing.append("authority_category")
        if not str(candidate.get("authority_document_role") or "").strip():
            missing.append("authority_document_role")
        if missing:
            failures.append(
                {
                    "candidate_authority_id": candidate.get("candidate_authority_id"),
                    "missing": missing,
                }
            )
    return {
        "name": "candidates_have_authority_metadata",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_source_evidence_available(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if not candidate.get("source_evidence_availability", {}).get("available")
    ]
    return {
        "name": "candidates_have_source_evidence_available",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_source_claim_linkage_recorded(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
        and not candidate.get("source_evidence_availability", {}).get(
            "source_claim_linkage_recorded"
        )
    ]
    return {
        "name": "rule_template_candidates_have_source_claim_linkage",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_applicability_contracts(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if not _has_applicability_contract(candidate)
    ]
    return {
        "name": "candidates_have_deterministic_applicability_contracts",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_candidate_pre_review_contracts(candidate_authorities: list[dict]) -> dict:
    required_fields = (
        "required_package_fact_types",
        "positive_trigger_groups",
        "negative_trigger_groups",
        "source_role_filters",
        "package_section_filters",
        "required_source_evidence",
        "retrieval_contract",
        "graph_expansion_contract",
        "dependency_contract",
        "search_coverage_requirements",
    )
    failures = []
    for candidate in candidate_authorities:
        missing = [
            field
            for field in required_fields
            if not _candidate_contract_field_present(candidate, field)
        ]
        if not _valid_retrieval_contract(candidate.get("retrieval_contract")):
            missing.append("valid_retrieval_contract")
        if not _valid_graph_expansion_contract(candidate.get("graph_expansion_contract")):
            missing.append("valid_graph_expansion_contract")
        if not _valid_search_coverage_requirements(
            candidate.get("search_coverage_requirements")
        ):
            missing.append("valid_search_coverage_requirements")
        if missing:
            failures.append(
                {
                    "candidate_authority_id": candidate.get("candidate_authority_id"),
                    "missing_or_invalid": sorted(set(missing)),
                }
            )
    return {
        "name": "candidates_have_pre_review_contracts",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_authority_family_template_candidates(
    *,
    authority_family_templates: dict | None,
    candidate_authorities: list[dict],
) -> dict:
    if not isinstance(authority_family_templates, dict):
        return {
            "name": "authority_family_template_candidates_cover_config",
            "passed": True,
            "details": {"configured": False, "expected_template_count": 0},
        }
    templates = [
        template
        for template in authority_family_templates.get("templates", [])
        if isinstance(template, dict)
    ]
    expected_rule_ids = {str(template.get("rule_id") or "") for template in templates}
    actual_rule_ids = {
        str(candidate.get("rule_template", {}).get("rule_id") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "authority_family_rule_template"
    }
    missing_predicates = [
        template.get("template_id")
        for template in templates
        if not (
            _strings(template.get("applies_if_package_terms"))
            or _string_groups(template.get("applies_if_package_term_groups"))
        )
    ]
    missing_negative_triggers = [
        template.get("template_id")
        for template in templates
        if not _strings(template.get("does_not_apply_if_package_terms"))
    ]
    candidates_without_family = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "authority_family_rule_template"
        and not candidate.get("authority_family_id")
    ]
    missing_source_records = []
    for candidate in candidate_authorities:
        if candidate.get("candidate_authority_type") != "authority_family_rule_template":
            continue
        expected_source_ids = set(_strings(candidate.get("source_record_ids")))
        actual_source_ids = {
            str(record.get("source_record_id") or "")
            for record in candidate.get("source_records") or []
            if isinstance(record, dict) and record.get("source_record_id")
        }
        missing = sorted(expected_source_ids - actual_source_ids)
        if missing:
            missing_source_records.append(
                {
                    "candidate_authority_id": candidate.get("candidate_authority_id"),
                    "source_record_ids": missing,
                }
            )
    passed = (
        expected_rule_ids == actual_rule_ids
        and bool(expected_rule_ids)
        and not missing_predicates
        and not missing_negative_triggers
        and not candidates_without_family
        and not missing_source_records
    )
    return {
        "name": "authority_family_template_candidates_cover_config",
        "passed": passed,
        "details": {
            "configured": True,
            "expected_template_count": len(expected_rule_ids),
            "actual_template_candidate_count": len(actual_rule_ids),
            "missing_rule_ids": sorted(expected_rule_ids - actual_rule_ids),
            "unexpected_rule_ids": sorted(actual_rule_ids - expected_rule_ids),
            "missing_predicate_template_ids": missing_predicates,
            "missing_negative_trigger_template_ids": missing_negative_triggers,
            "candidates_without_authority_family_id": candidates_without_family,
            "missing_source_records": missing_source_records[:50],
            "missing_source_record_count": len(missing_source_records),
        },
    }


def _check_forest_plan_component_candidates(
    *,
    source_set_id: str,
    rule_pack: dict,
    candidate_authorities: list[dict],
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
) -> dict:
    forest_plan_rule_source_ids = {
        _rule_source_record_id(rule)
        for rule in rule_pack.get("rules", [])
        if rule.get("authority_category") == "forest_plan"
    }
    profile_source_ids = {
        profile.active_plan_source_record_id
        for profile in profiles.profiles
    }
    inventory_profile_source_id = None
    inventory_forest_unit_id = ""
    if isinstance(component_inventory, dict):
        inventory_forest_unit_id = str(component_inventory.get("forest_unit_id") or "")
        if inventory_forest_unit_id:
            try:
                inventory_profile_source_id = profiles.get(
                    inventory_forest_unit_id
                ).active_plan_source_record_id
            except KeyError:
                inventory_profile_source_id = None
    required = bool(
        inventory_profile_source_id
        and inventory_profile_source_id in forest_plan_rule_source_ids
        and inventory_profile_source_id in profile_source_ids
    )
    component_candidates = [
        candidate
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "forest_plan_component"
    ]
    component_records = (
        component_inventory.get("components", [])
        if isinstance(component_inventory, dict)
        and component_inventory.get("source_set_id") == source_set_id
        and required
        and isinstance(component_inventory.get("components"), list)
        else []
    )
    passed = (not required and not component_candidates) or (
        bool(component_records) and len(component_candidates) == len(component_records)
    )
    return {
        "name": "forest_plan_component_candidates_use_profile_inventory",
        "passed": passed,
        "details": {
            "required": required,
            "forest_plan_rule_source_record_ids": sorted(
                source_id for source_id in forest_plan_rule_source_ids if source_id
            ),
            "profile_active_plan_source_record_ids": sorted(profile_source_ids),
            "inventory_forest_unit_id": inventory_forest_unit_id or None,
            "inventory_profile_source_record_id": inventory_profile_source_id,
            "component_inventory_present": bool(component_records),
            "component_inventory_count": len(component_records),
            "component_candidate_count": len(component_candidates),
        },
    }


def _has_applicability_contract(candidate: dict) -> bool:
    contract = candidate.get("deterministic_applicability_test_contract")
    if not isinstance(contract, dict):
        return False
    contract_type = contract.get("contract_type")
    if contract_type == "rule_template":
        mode = str(contract.get("applicability_mode") or "")
        if not contract.get("package_query") or not contract.get("source_query"):
            return False
        if not contract.get("source_filters"):
            return False
        if mode == "conditional":
            return bool(
                contract.get("positive_package_terms")
                or contract.get("positive_package_term_groups")
            )
        return mode == "baseline"
    if contract_type == "forest_plan_component":
        return bool(
            contract.get("component_type")
            and contract.get("source_chunk_ids")
            and (contract.get("package_evidence_terms") or contract.get("resource_topics"))
        )
    return False


def _candidate_contract_field_present(candidate: dict, field: str) -> bool:
    value = candidate.get(field)
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        if field == "negative_trigger_groups":
            return True
        return bool(value)
    return value is not None


def _valid_retrieval_contract(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return bool(
        value.get("contract_type")
        and value.get("required_query_types")
        and value.get("source_role_filters")
        and value.get("package_section_filters")
        and value.get("requires_selected_and_rejected_results") is True
        and value.get("searched_index_hash_required") is True
    )


def _valid_graph_expansion_contract(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return bool(
        value.get("contract_type")
        and value.get("start_node_types")
        and value.get("relationship_types")
        and value.get("max_depth")
        and value.get("requires_path_trace") is True
    )


def _valid_search_coverage_requirements(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for requirement in value:
        if not isinstance(requirement, dict):
            return False
        if not requirement.get("coverage_class"):
            return False
        if not requirement.get("required_query_types"):
            return False
        if not requirement.get("required_artifacts"):
            return False
    return True


def _summary(
    *,
    authority_universe_id: str,
    authority_universe_sha256: str,
    review_id: str,
    source_set_id: str,
    base_rule_pack: dict,
    source_set_manifest_path: Path,
    source_catalog_path: Path,
    forest_plan_profiles_path: Path,
    forest_plan_component_inventory_path: Path,
    claims_path: Path,
    rule_claim_links_path: Path,
    rule_claim_gaps_path: Path,
    authority_family_templates_path: Path | None,
    candidate_authorities: list[dict],
    validation: dict,
) -> dict:
    type_counts = Counter(
        str(candidate.get("candidate_authority_type") or "")
        for candidate in candidate_authorities
    )
    applicability_modes = Counter(
        str(candidate.get("rule_template", {}).get("applicability_mode") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
    )
    authority_family_template_modes = Counter(
        str(candidate.get("rule_template", {}).get("applicability_mode") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "authority_family_rule_template"
    )
    return {
        "schema_version": "authority-universe-summary-v0",
        "authority_universe_id": authority_universe_id,
        "authority_universe_sha256": authority_universe_sha256,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_count": len(base_rule_pack.get("rules", [])),
        "candidate_authority_count": len(candidate_authorities),
        "rule_template_candidate_count": type_counts.get("rule_template", 0),
        "authority_family_rule_template_candidate_count": type_counts.get(
            "authority_family_rule_template",
            0,
        ),
        "forest_plan_component_candidate_count": type_counts.get("forest_plan_component", 0),
        "candidate_type_counts": dict(type_counts),
        "rule_applicability_mode_counts": {
            key: value for key, value in dict(applicability_modes).items() if key
        },
        "authority_family_template_applicability_mode_counts": {
            key: value
            for key, value in dict(authority_family_template_modes).items()
            if key
        },
        "candidate_contract_counts": _candidate_contract_counts(candidate_authorities),
        "source_set_manifest_path": str(source_set_manifest_path),
        "source_catalog_path": str(source_catalog_path),
        "forest_plan_profiles_path": str(forest_plan_profiles_path),
        "forest_plan_component_inventory_path": (
            str(forest_plan_component_inventory_path)
            if forest_plan_component_inventory_path.exists()
            else None
        ),
        "claims_path": str(claims_path) if claims_path.exists() else None,
        "rule_claim_links_path": (
            str(rule_claim_links_path) if rule_claim_links_path.exists() else None
        ),
        "rule_claim_gaps_path": (
            str(rule_claim_gaps_path) if rule_claim_gaps_path.exists() else None
        ),
        "authority_family_templates_path": (
            str(authority_family_templates_path) if authority_family_templates_path else None
        ),
        "validation_passed": bool(validation.get("passed")),
        "passed": bool(validation.get("passed")),
    }


def _candidate_contract_counts(candidate_authorities: list[dict]) -> dict:
    return {
        "with_required_package_fact_types": sum(
            1 for candidate in candidate_authorities if candidate.get("required_package_fact_types")
        ),
        "with_retrieval_contract": sum(
            1 for candidate in candidate_authorities if candidate.get("retrieval_contract")
        ),
        "with_graph_expansion_contract": sum(
            1 for candidate in candidate_authorities if candidate.get("graph_expansion_contract")
        ),
        "with_dependency_contract": sum(
            1 for candidate in candidate_authorities if candidate.get("dependency_contract")
        ),
        "with_search_coverage_requirements": sum(
            1
            for candidate in candidate_authorities
            if candidate.get("search_coverage_requirements")
        ),
    }


def _forest_plan_profile_ids(profiles: ForestPlanProfileCollection) -> list[str]:
    return sorted(profile.forest_unit_id for profile in profiles.profiles)


def _component_inventory_id(component_inventory: dict | None) -> str | None:
    if not isinstance(component_inventory, dict):
        return None
    value = str(component_inventory.get("inventory_id") or "").strip()
    return value or None


def _load_authority_family_templates(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing authority-family templates: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Authority-family templates must be a JSON object.")
    if value.get("schema_version") != AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION:
        raise ValueError(
            "Authority-family templates schema_version must be "
            f"{AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION}."
        )
    templates = value.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ValueError("Authority-family templates must contain a non-empty templates list.")
    failures = []
    seen_rule_ids = set()
    for index, template in enumerate(templates):
        if not isinstance(template, dict):
            failures.append({"index": index, "missing": ["template_object"]})
            continue
        required = {
            "template_id",
            "authority_family_id",
            "rule_id",
            "title",
            "authority_category",
            "authority_source_record_id",
            "applicability_mode",
            "question",
            "requirement",
            "severity",
            "package_query",
            "package_terms",
            "source_query",
            "source_filters",
            "evidence_expectation",
        }
        missing = sorted(
            field for field in required if not _template_field_present(template, field)
        )
        if not (
            _strings(template.get("applies_if_package_terms"))
            or _string_groups(template.get("applies_if_package_term_groups"))
        ):
            missing.append("positive_applicability_predicate")
        if not _strings(template.get("does_not_apply_if_package_terms")):
            missing.append("does_not_apply_if_package_terms")
        if not _strings(template.get("package_fact_types")):
            missing.append("package_fact_types")
        rule_id = str(template.get("rule_id") or "")
        if rule_id in seen_rule_ids:
            missing.append("unique_rule_id")
        seen_rule_ids.add(rule_id)
        if missing:
            failures.append(
                {
                    "index": index,
                    "template_id": template.get("template_id"),
                    "missing_or_invalid": sorted(set(missing)),
                }
            )
    if failures:
        raise ValueError(
            "Authority-family templates are invalid: "
            + json.dumps(failures[:20], sort_keys=True)
        )
    return value


def _template_field_present(template: dict, field: str) -> bool:
    value = template.get(field)
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return any(str(item or "").strip() for item in value)
    return bool(str(value or "").strip())


def _load_source_catalog(path: Path, source_set_id: str) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source catalog: {path}")
    records = _read_jsonl(path)
    filtered = [
        record
        for record in records
        if str(record.get("source_set_id") or "") == source_set_id
    ]
    if filtered:
        return filtered
    fallback_records = _catalog_records_from_extraction_manifest(path, source_set_id)
    if fallback_records:
        return fallback_records
    raise ValueError(f"No source catalog records found for source set: {source_set_id}")


def _catalog_records_from_extraction_manifest(
    catalog_path: Path,
    source_set_id: str,
) -> list[dict]:
    extraction_manifest_path = (
        catalog_path.parent.parent
        / "derived"
        / source_set_id
        / "diagnostics"
        / "extraction_manifest.jsonl"
    )
    if not extraction_manifest_path.exists():
        return []
    records = _read_jsonl(extraction_manifest_path)
    filtered = [
        record
        for record in records
        if str(record.get("source_set_id") or "") == source_set_id
    ]
    if not filtered:
        return []
    catalog_by_source_record_id: dict[str, dict] = {}
    for record in filtered:
        source_record_id = str(record.get("source_record_id") or "").strip()
        if not source_record_id:
            continue
        catalog_by_source_record_id[source_record_id] = _catalog_record_from_extraction_record(
            record
        )
    return list(catalog_by_source_record_id.values())


def _catalog_record_from_extraction_record(record: dict) -> dict:
    artifact_sha256 = str(record.get("artifact_sha256") or "").strip()
    artifact_path = str(record.get("artifact_path") or "").strip()
    return {
        "source_set_id": record.get("source_set_id"),
        "source_record_id": record.get("source_record_id"),
        "title": record.get("title"),
        "citation_label": record.get("citation_label"),
        "document_role": record.get("document_role"),
        "authority_level": record.get("authority_level"),
        "issuer": None,
        "scope": None,
        "layer": None,
        "document_type": None,
        "unit_or_overlay": None,
        "applies_to": None,
        "trigger": None,
        "review_topics": [],
        "currentness_notes": None,
        "source_status": record.get("source_status") or record.get("status"),
        "artifact_sha256": artifact_sha256 or None,
        "artifact_path": artifact_path or None,
        "artifact_byte_size": record.get("artifact_byte_size"),
        "content_type": record.get("content_type"),
        "retrieved_at": record.get("retrieved_at"),
    }


def _source_set_id_from_manifest(path: Path, manifest: dict) -> str:
    value = manifest.get("source_set_id")
    if not str(value or "").strip():
        raise ValueError(f"Missing source_set_id in source-set manifest: {path}")
    return str(value).strip()


def _default_forest_plan_component_inventory_path(output_dir: Path, source_set_id: str) -> Path:
    return (
        output_dir
        / "derived"
        / source_set_id
        / "forest_plan_components"
        / "component_inventory.json"
    )


def _records_by_key(records: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        value = str(record.get(key) or "")
        if value:
            grouped[value].append(record)
    return dict(grouped)


def _validate_safe_segment(value: str, field_name: str) -> None:
    if not SAFE_SEGMENT_RE.fullmatch(str(value or "")):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _optional_file_sha256(path: Path) -> str | None:
    return sha256_file(path) if path.exists() else None


def _stable_sha256(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object lines in {path}")
        records.append(value)
    return records


def _read_jsonl_if_exists(path: Path) -> list[dict]:
    return _read_jsonl(path) if path.exists() else []


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
