from __future__ import annotations

from collections import Counter
from pathlib import Path

from .applicability_candidate_assembly import selected_forest_plan_inventory_components
from .applicability_contract_support import rule_source_record_id
from .applicability_contract_support import string_groups
from .applicability_contract_support import strings
from .forest_plan_profiles import ForestPlanProfileCollection


def authority_universe_validation(
    *,
    created_at: str,
    source_set_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    candidate_authorities: list[dict],
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
    authority_family_templates: dict | None,
    forest_plan_required_source_record_ids: set[str] | None = None,
    forest_plan_required_forest_unit_id: str | None = None,
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
            forest_plan_required_source_record_ids=forest_plan_required_source_record_ids,
            forest_plan_required_forest_unit_id=forest_plan_required_forest_unit_id,
        ),
    ]
    return {
        "schema_version": "authority-universe-validation-v0",
        "created_at": created_at,
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def authority_universe_summary(
    *,
    authority_universe_id: str,
    authority_universe_sha256: str,
    review_id: str,
    source_set_id: str,
    forest_unit_id: str | None,
    review_scope: dict | None,
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
        "forest_unit_id": forest_unit_id,
        "review_scope": review_scope or {},
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


def forest_plan_profile_ids(profiles: ForestPlanProfileCollection) -> list[str]:
    return sorted(profile.forest_unit_id for profile in profiles.profiles)


def component_inventory_id(component_inventory: dict | None) -> str | None:
    if not isinstance(component_inventory, dict):
        return None
    value = str(component_inventory.get("inventory_id") or "").strip()
    return value or None


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
            strings(template.get("applies_if_package_terms"))
            or string_groups(template.get("applies_if_package_term_groups"))
        )
    ]
    missing_negative_triggers = [
        template.get("template_id")
        for template in templates
        if not strings(template.get("does_not_apply_if_package_terms"))
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
        expected_source_ids = set(strings(candidate.get("source_record_ids")))
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
    forest_plan_required_source_record_ids: set[str] | None = None,
    forest_plan_required_forest_unit_id: str | None = None,
) -> dict:
    forest_plan_required_forest_unit_id = str(
        forest_plan_required_forest_unit_id or ""
    ).strip()
    forest_plan_rule_source_ids = forest_plan_required_source_record_ids or {
        rule_source_record_id(rule)
        for rule in rule_pack.get("rules", [])
        if rule.get("authority_category") == "forest_plan"
    }
    profile_source_ids = {
        profile.active_plan_source_record_id
        for profile in profiles.profiles
    }
    required_profile_source_ids = sorted(
        source_id
        for source_id in forest_plan_rule_source_ids
        if source_id and source_id in profile_source_ids
    )
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
    required = bool(required_profile_source_ids)
    selected_component_records = selected_forest_plan_inventory_components(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        allowed_forest_plan_source_record_ids=required_profile_source_ids,
        selected_forest_unit_id=forest_plan_required_forest_unit_id,
    )
    component_candidates = [
        candidate
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "forest_plan_component"
    ]
    required = bool(forest_plan_required_forest_unit_id or required_profile_source_ids)
    passed = (not required and not component_candidates) or (
        bool(selected_component_records)
        and len(component_candidates) == len(selected_component_records)
    )
    return {
        "name": "forest_plan_component_candidates_use_profile_inventory",
        "passed": passed,
        "details": {
            "required": required,
            "required_forest_unit_id": forest_plan_required_forest_unit_id or None,
            "forest_plan_rule_source_record_ids": sorted(
                source_id for source_id in forest_plan_rule_source_ids if source_id
            ),
            "profile_active_plan_source_record_ids": sorted(profile_source_ids),
            "required_profile_source_record_ids": required_profile_source_ids,
            "inventory_forest_unit_id": inventory_forest_unit_id or None,
            "inventory_profile_source_record_id": inventory_profile_source_id,
            "component_inventory_present": bool(selected_component_records),
            "component_inventory_count": len(selected_component_records),
            "component_candidate_count": len(component_candidates),
            "selected_component_forest_unit_ids": sorted(
                {
                    profile.forest_unit_id
                    for profile, _component in selected_component_records
                }
            ),
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
