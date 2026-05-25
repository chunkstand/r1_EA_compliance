from __future__ import annotations

from collections.abc import Collection
from pathlib import Path

from .applicability_contract_support import authority_document_role
from .applicability_contract_support import baseline_source_record_ids
from .applicability_contract_support import catalog_resolved_source_record_ids
from .applicability_contract_support import rule_source_record_id
from .applicability_contract_support import source_record_summary
from .applicability_contract_support import string_groups
from .applicability_contract_support import strings
from .forest_plan_profiles import ForestPlanProfile
from .forest_plan_profiles import ForestPlanProfileCollection


FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID = "nfma_forest_planning_project_consistency"
BASE_RULE_PACKAGE_FACT_TYPES = (
    "action",
    "agency",
    "decision_posture",
    "nepa_level",
    "package_section",
    "evidence_span",
)
FOREST_PLAN_PACKAGE_FACT_TYPES = (
    "action",
    "agency",
    "geography",
    "management_area",
    "overlay",
    "resource_topic",
    "package_section",
    "evidence_span",
)
RULE_GRAPH_RELATIONSHIP_TYPES = (
    "source_record",
    "authority_category",
    "source_claim",
    "rule_claim_link",
    "package_fact",
    "evidence_span",
    "exception",
    "dependency",
    "supersession",
)
FOREST_PLAN_GRAPH_RELATIONSHIP_TYPES = (
    "forest_plan_profile",
    "component_inventory",
    "source_record",
    "source_chunk",
    "geography",
    "management_area",
    "overlay",
    "package_fact",
    "evidence_span",
)


def rule_template_candidates(
    *,
    source_set_id: str,
    rule_pack: dict,
    catalog_by_source_id: dict[str, dict],
    source_claim_links_by_rule: dict[str, list[dict]],
    source_claim_gaps_by_rule: dict[str, list[dict]],
) -> list[dict]:
    baseline_source_ids = baseline_source_record_ids(rule_pack)
    candidates = []
    for rule in rule_pack.get("rules", []):
        rule_id = str(rule.get("id") or "")
        declared_source_record_id = rule_source_record_id(rule)
        source_record_ids = catalog_resolved_source_record_ids(
            [declared_source_record_id] if declared_source_record_id else [],
            catalog_by_source_id=catalog_by_source_id,
        )
        source_record_id = (
            source_record_ids[0] if source_record_ids else declared_source_record_id
        )
        catalog_record = catalog_by_source_id.get(source_record_id or "")
        source_claim_links = source_claim_links_by_rule.get(rule_id, [])
        source_claim_gaps = source_claim_gaps_by_rule.get(rule_id, [])
        document_role = authority_document_role(rule, catalog_record)
        source_role_filters = _rule_source_role_filters(
            rule=rule,
            source_record_id=source_record_id,
            source_record_ids=source_record_ids,
            document_role=document_role,
        )
        package_section_filters = _rule_package_section_filters(rule)
        positive_trigger_groups = _rule_positive_trigger_groups(rule)
        negative_trigger_groups = _rule_negative_trigger_groups(rule)
        required_package_fact_types = _rule_required_package_fact_types(rule)
        candidates.append(
            {
                "candidate_authority_id": (
                    "rule-template:"
                    f"{rule_pack.get('rule_pack_id')}:{rule_pack.get('version')}:{rule_id}"
                ),
                "candidate_authority_type": "rule_template",
                "source_set_id": source_set_id,
                "authority_category": rule.get("authority_category"),
                "authority_document_role": document_role,
                "source_record_ids": source_record_ids,
                "source_records": [
                    source_record_summary(catalog_by_source_id.get(candidate_source_record_id))
                    for candidate_source_record_id in source_record_ids
                    if catalog_by_source_id.get(candidate_source_record_id)
                ],
                "required_package_fact_types": required_package_fact_types,
                "positive_trigger_groups": positive_trigger_groups,
                "negative_trigger_groups": negative_trigger_groups,
                "source_role_filters": source_role_filters,
                "package_section_filters": package_section_filters,
                "required_source_evidence": _rule_required_source_evidence(
                    source_record_id=source_record_id,
                    source_record_ids=source_record_ids,
                    document_role=document_role,
                    source_role_filters=source_role_filters,
                    source_claim_links=source_claim_links,
                    source_claim_gaps=source_claim_gaps,
                ),
                "retrieval_contract": _rule_retrieval_contract(
                    rule=rule,
                    rule_id=rule_id,
                    source_role_filters=source_role_filters,
                    package_section_filters=package_section_filters,
                ),
                "graph_expansion_contract": _rule_graph_expansion_contract(
                    rule=rule,
                    rule_id=rule_id,
                    source_record_ids=source_record_ids,
                ),
                "dependency_contract": _rule_dependency_contract(rule),
                "search_coverage_requirements": _rule_search_coverage_requirements(
                    rule=rule,
                    positive_trigger_groups=positive_trigger_groups,
                    negative_trigger_groups=negative_trigger_groups,
                ),
                "rule_template": {
                    "base_rule_pack_id": rule_pack.get("rule_pack_id"),
                    "base_rule_pack_version": rule_pack.get("version"),
                    "rule_id": rule_id,
                    "title": rule.get("title"),
                    "question": rule.get("question"),
                    "requirement": rule.get("requirement"),
                    "severity": rule.get("severity"),
                    "applicability_mode": rule.get("applicability_mode"),
                },
                "source_evidence_availability": _rule_source_evidence_availability(
                    catalog_record=catalog_record,
                    source_claim_links=source_claim_links,
                    source_claim_gaps=source_claim_gaps,
                ),
                "deterministic_applicability_test_contract": _rule_applicability_contract(
                    rule=rule,
                    baseline_source_record_ids=baseline_source_ids,
                ),
                "source_claim_link_ids": [
                    str(link.get("link_id"))
                    for link in source_claim_links
                    if link.get("link_id")
                ],
                "rule_claim_gap_ids": [
                    str(gap.get("gap_id")) for gap in source_claim_gaps if gap.get("gap_id")
                ],
            }
        )
    return candidates


def forest_plan_component_candidates(
    *,
    source_set_id: str,
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
    component_inventory_path: Path,
    component_inventory_sha256: str | None,
    catalog_by_source_id: dict[str, dict],
    allowed_forest_plan_source_record_ids: Collection[str] | None = None,
) -> list[dict]:
    inventory_id = str(component_inventory.get("inventory_id") or "")
    candidates = []
    for profile, component in selected_forest_plan_inventory_components(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        allowed_forest_plan_source_record_ids=allowed_forest_plan_source_record_ids,
    ):
        component_id = str(component.get("component_id") or "")
        source_record_id = str(
            component.get("source_record_id") or profile.active_plan_source_record_id
        )
        catalog_record = catalog_by_source_id.get(source_record_id)
        source_role_filters = _component_source_role_filters(
            source_record_id=source_record_id,
        )
        package_section_filters = _component_package_section_filters(component)
        positive_trigger_groups = _component_positive_trigger_groups(component)
        negative_trigger_groups = _component_negative_trigger_groups()
        required_package_fact_types = _component_required_package_fact_types(component)
        candidates.append(
            {
                "candidate_authority_id": (
                    f"forest-plan-component:{inventory_id}:{component_id}"
                ),
                "candidate_authority_type": "forest_plan_component",
                "source_set_id": source_set_id,
                "authority_category": "forest_plan",
                "authority_family_id": FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID,
                "authority_family_ids": [FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID],
                "authority_document_role": "forest_plan",
                "source_record_ids": [source_record_id] if source_record_id else [],
                "source_records": [source_record_summary(catalog_record)]
                if catalog_record
                else [],
                "required_package_fact_types": required_package_fact_types,
                "positive_trigger_groups": positive_trigger_groups,
                "negative_trigger_groups": negative_trigger_groups,
                "source_role_filters": source_role_filters,
                "package_section_filters": package_section_filters,
                "required_source_evidence": _component_required_source_evidence(
                    source_record_id=source_record_id,
                    source_role_filters=source_role_filters,
                    component=component,
                ),
                "retrieval_contract": _component_retrieval_contract(
                    component=component,
                    component_id=component_id,
                    source_role_filters=source_role_filters,
                    package_section_filters=package_section_filters,
                ),
                "graph_expansion_contract": _component_graph_expansion_contract(
                    component=component,
                    component_id=component_id,
                    profile=profile,
                    inventory_id=inventory_id,
                ),
                "dependency_contract": _component_dependency_contract(profile),
                "search_coverage_requirements": _component_search_coverage_requirements(
                    component=component,
                    positive_trigger_groups=positive_trigger_groups,
                ),
                "forest_plan": {
                    "forest_unit_id": profile.forest_unit_id,
                    "forest_unit_names": list(profile.forest_unit_names),
                    "active_plan_source_record_id": profile.active_plan_source_record_id,
                    "profile_data_source": profile.profile_data_source,
                    "component_inventory_id": inventory_id,
                    "component_inventory_path": str(component_inventory_path),
                    "component_inventory_sha256": component_inventory_sha256,
                    "plan_version": component.get("plan_version")
                    or component_inventory.get("plan_version"),
                    "component_id": component_id,
                    "component_type": component.get("component_type"),
                    "section_id": component.get("section_id"),
                    "section_heading": component.get("section_heading"),
                    "geographic_area_ids": component.get("geographic_area_ids", []),
                    "management_area_ids": component.get("management_area_ids", []),
                    "overlay_ids": component.get("overlay_ids", []),
                },
                "source_evidence_availability": _component_source_evidence_availability(
                    catalog_record=catalog_record,
                    component=component,
                ),
                "deterministic_applicability_test_contract": {
                    "contract_type": "forest_plan_component",
                    "component_type": component.get("component_type"),
                    "source_chunk_ids": component.get("source_chunk_ids", []),
                    "package_evidence_terms": component.get("package_evidence_terms", []),
                    "resource_topics": component.get("resource_topics", []),
                    "activity_tags": component.get("activity_tags", []),
                    "geographic_area_ids": component.get("geographic_area_ids", []),
                    "management_area_ids": component.get("management_area_ids", []),
                    "overlay_ids": component.get("overlay_ids", []),
                },
            }
        )
    return candidates


def selected_forest_plan_inventory_components(
    *,
    source_set_id: str,
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
    allowed_forest_plan_source_record_ids: Collection[str] | None = None,
) -> list[tuple[ForestPlanProfile, dict]]:
    if not isinstance(component_inventory, dict):
        return []
    if str(component_inventory.get("source_set_id") or "") != source_set_id:
        return []
    components = component_inventory.get("components")
    if not isinstance(components, list):
        return []
    allowed_source_ids = {
        str(source_record_id).strip()
        for source_record_id in allowed_forest_plan_source_record_ids or ()
        if str(source_record_id).strip()
    }
    inventory_profile = _inventory_profile(profiles, component_inventory)
    if inventory_profile is not None:
        if (
            allowed_source_ids
            and inventory_profile.active_plan_source_record_id not in allowed_source_ids
        ):
            return []
        return [
            (inventory_profile, component)
            for component in components
            if isinstance(component, dict)
        ]
    if not allowed_source_ids:
        return []
    selected: list[tuple[ForestPlanProfile, dict]] = []
    for component in components:
        if not isinstance(component, dict):
            continue
        profile = _component_profile(profiles, component)
        if profile is None:
            continue
        source_record_id = str(
            component.get("source_record_id") or profile.active_plan_source_record_id
        ).strip()
        if (
            source_record_id not in allowed_source_ids
            and profile.active_plan_source_record_id not in allowed_source_ids
        ):
            continue
        selected.append((profile, component))
    return selected


def _inventory_profile(
    profiles: ForestPlanProfileCollection,
    component_inventory: dict,
) -> ForestPlanProfile | None:
    forest_unit_id = str(component_inventory.get("forest_unit_id") or "").strip()
    if not forest_unit_id:
        return None
    try:
        return profiles.get(forest_unit_id)
    except KeyError:
        return None


def _component_profile(
    profiles: ForestPlanProfileCollection,
    component: dict,
) -> ForestPlanProfile | None:
    forest_unit_id = str(component.get("forest_unit_id") or "").strip()
    if forest_unit_id:
        try:
            return profiles.get(forest_unit_id)
        except KeyError:
            return None
    source_record_id = str(component.get("source_record_id") or "").strip()
    if not source_record_id:
        return None
    for profile in profiles.profiles:
        if profile.active_plan_source_record_id == source_record_id:
            return profile
    return None


def _rule_source_evidence_availability(
    *,
    catalog_record: dict | None,
    source_claim_links: list[dict],
    source_claim_gaps: list[dict],
) -> dict:
    artifact_sha256 = str((catalog_record or {}).get("artifact_sha256") or "")
    source_status = str((catalog_record or {}).get("source_status") or "")
    catalog_present = catalog_record is not None
    return {
        "available": catalog_present and bool(artifact_sha256),
        "catalog_record_present": catalog_present,
        "artifact_sha256_present": bool(artifact_sha256),
        "source_status": source_status or None,
        "source_claim_link_count": len(source_claim_links),
        "rule_claim_gap_count": len(source_claim_gaps),
        "source_claim_linkage_recorded": bool(source_claim_links or source_claim_gaps),
        "rule_claim_gap_reasons": sorted(
            {
                str(gap.get("reason"))
                for gap in source_claim_gaps
                if gap.get("reason")
            }
        ),
    }


def _component_source_evidence_availability(
    *,
    catalog_record: dict | None,
    component: dict,
) -> dict:
    source_chunk_ids = [
        str(chunk_id)
        for chunk_id in component.get("source_chunk_ids", [])
        if str(chunk_id or "").strip()
    ]
    artifact_sha256 = str(component.get("artifact_sha256") or "")
    return {
        "available": catalog_record is not None and bool(source_chunk_ids) and bool(artifact_sha256),
        "catalog_record_present": catalog_record is not None,
        "artifact_sha256_present": bool(artifact_sha256),
        "source_chunk_count": len(source_chunk_ids),
        "source_status": str((catalog_record or {}).get("source_status") or "") or None,
    }


def _rule_required_package_fact_types(rule: dict) -> list[str]:
    fact_types = set(BASE_RULE_PACKAGE_FACT_TYPES)
    if rule.get("applicability_mode") == "conditional":
        fact_types.add("resource_topic")
    if rule.get("authority_category") == "forest_plan":
        fact_types.update({"geography", "management_area", "overlay"})
    return sorted(fact_types)


def _component_required_package_fact_types(component: dict) -> list[str]:
    fact_types = set(FOREST_PLAN_PACKAGE_FACT_TYPES)
    if not component.get("geographic_area_ids"):
        fact_types.discard("geography")
    if not component.get("management_area_ids"):
        fact_types.discard("management_area")
    if not component.get("overlay_ids"):
        fact_types.discard("overlay")
    return sorted(fact_types)


def _rule_applicability_contract(
    *,
    rule: dict,
    baseline_source_record_ids: list[str],
) -> dict:
    source_record_id = rule_source_record_id(rule)
    return {
        "contract_type": "rule_template",
        "applicability_mode": rule.get("applicability_mode"),
        "baseline_required": source_record_id in baseline_source_record_ids,
        "baseline_source_record_ids": baseline_source_record_ids,
        "package_query": rule.get("package_query"),
        "package_terms": rule.get("package_terms", []),
        "package_section_terms": rule.get("package_section_terms", []),
        "package_section_term_groups": rule.get("package_section_term_groups", []),
        "positive_package_terms": rule.get("applies_if_package_terms", []),
        "positive_package_term_groups": rule.get("applies_if_package_term_groups", []),
        "negative_package_terms": rule.get("does_not_apply_if_package_terms", []),
        "source_query": rule.get("source_query"),
        "source_filters": rule.get("source_filters", {}),
        "evidence_expectation": rule.get("evidence_expectation"),
    }


def _rule_positive_trigger_groups(rule: dict) -> list[list[str]]:
    groups = string_groups(rule.get("applies_if_package_term_groups"))
    explicit_terms = strings(rule.get("applies_if_package_terms"))
    if explicit_terms:
        groups.append(explicit_terms)
    if not groups:
        package_terms = strings(rule.get("package_terms"))
        if package_terms:
            groups.append(package_terms)
    if not groups:
        package_query = str(rule.get("package_query") or "").strip()
        if package_query:
            groups.append([package_query])
    return groups


def _rule_negative_trigger_groups(rule: dict) -> list[list[str]]:
    terms = strings(rule.get("does_not_apply_if_package_terms"))
    return [[term] for term in terms]


def _component_positive_trigger_groups(component: dict) -> list[list[str]]:
    groups = []
    package_terms = strings(component.get("package_evidence_terms"))
    if package_terms:
        groups.append(package_terms)
    resource_topics = strings(component.get("resource_topics"))
    if resource_topics:
        groups.append(resource_topics)
    activity_tags = strings(component.get("activity_tags"))
    if activity_tags:
        groups.append(activity_tags)
    component_type = str(component.get("component_type") or "").strip()
    if not groups and component_type:
        groups.append([component_type])
    return groups


def _component_negative_trigger_groups() -> list[list[str]]:
    return [["not part of the project area"]]


def _rule_source_role_filters(
    *,
    rule: dict,
    source_record_id: str | None,
    source_record_ids: list[str],
    document_role: str | None,
) -> dict:
    source_filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    return {
        "source_record_ids": source_record_ids,
        "document_roles": [document_role] if document_role else [],
        "authority_categories": strings([rule.get("authority_category")]),
        "source_filters": source_filters,
    }


def _component_source_role_filters(*, source_record_id: str | None) -> dict:
    return {
        "source_record_ids": [source_record_id] if source_record_id else [],
        "document_roles": ["forest_plan"],
        "authority_categories": ["forest_plan"],
        "source_filters": {
            "document_role": "forest_plan",
            "source_record_id": source_record_id,
        },
    }


def _rule_package_section_filters(rule: dict) -> dict:
    return {
        "package_query": rule.get("package_query"),
        "package_terms": strings(rule.get("package_terms")),
        "package_section_terms": strings(rule.get("package_section_terms")),
        "package_section_term_groups": string_groups(rule.get("package_section_term_groups")),
        "preferred_section_families": strings(rule.get("package_section_families")),
    }


def _component_package_section_filters(component: dict) -> dict:
    return {
        "component_section_id": component.get("section_id"),
        "component_section_heading": component.get("section_heading"),
        "package_evidence_terms": strings(component.get("package_evidence_terms")),
        "resource_topics": strings(component.get("resource_topics")),
        "activity_tags": strings(component.get("activity_tags")),
        "geographic_area_ids": strings(component.get("geographic_area_ids")),
        "management_area_ids": strings(component.get("management_area_ids")),
        "overlay_ids": strings(component.get("overlay_ids")),
    }


def _rule_required_source_evidence(
    *,
    source_record_id: str | None,
    source_record_ids: list[str],
    document_role: str | None,
    source_role_filters: dict,
    source_claim_links: list[dict],
    source_claim_gaps: list[dict],
) -> dict:
    return {
        "source_record_ids": source_record_ids,
        "document_roles": [document_role] if document_role else [],
        "source_role_filters": source_role_filters,
        "requires_catalog_record": True,
        "requires_artifact_sha256": True,
        "requires_source_claim_linkage": True,
        "source_claim_link_ids": [
            str(link.get("link_id"))
            for link in source_claim_links
            if str(link.get("link_id") or "").strip()
        ],
        "rule_claim_gap_ids": [
            str(gap.get("gap_id"))
            for gap in source_claim_gaps
            if str(gap.get("gap_id") or "").strip()
        ],
    }


def _component_required_source_evidence(
    *,
    source_record_id: str | None,
    source_role_filters: dict,
    component: dict,
) -> dict:
    return {
        "source_record_ids": [source_record_id] if source_record_id else [],
        "document_roles": ["forest_plan"],
        "source_role_filters": source_role_filters,
        "requires_catalog_record": True,
        "requires_artifact_sha256": True,
        "requires_source_chunks": True,
        "source_chunk_ids": strings(component.get("source_chunk_ids")),
    }


def _rule_retrieval_contract(
    *,
    rule: dict,
    rule_id: str,
    source_role_filters: dict,
    package_section_filters: dict,
) -> dict:
    return {
        "contract_type": "rule_template_retrieval",
        "query_plan_id": f"retrieval-plan:rule-template:{rule_id}",
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
            "source_role",
        ],
        "optional_query_types": ["vector"],
        "source_queries": strings([rule.get("source_query")]),
        "package_queries": strings([rule.get("package_query")]),
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "fused_ranking_strategy": "reciprocal_rank_fusion",
        "requires_selected_and_rejected_results": True,
        "searched_index_hash_required": True,
    }


def _component_retrieval_contract(
    *,
    component: dict,
    component_id: str,
    source_role_filters: dict,
    package_section_filters: dict,
) -> dict:
    query_terms = strings(component.get("package_evidence_terms")) or strings(
        [component.get("section_heading")]
    )
    return {
        "contract_type": "forest_plan_component_retrieval",
        "query_plan_id": f"retrieval-plan:forest-plan-component:{component_id}",
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
            "source_role",
        ],
        "optional_query_types": ["vector"],
        "source_queries": strings([component.get("section_heading")]),
        "package_queries": query_terms,
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "fused_ranking_strategy": "reciprocal_rank_fusion",
        "requires_selected_and_rejected_results": True,
        "searched_index_hash_required": True,
    }


def _rule_graph_expansion_contract(
    *,
    rule: dict,
    rule_id: str,
    source_record_ids: list[str],
) -> dict:
    return {
        "contract_type": "rule_template_graph_expansion",
        "start_node_types": ["rule_template", "source_record", "authority"],
        "relationship_types": list(RULE_GRAPH_RELATIONSHIP_TYPES),
        "max_depth": 2,
        "requires_path_trace": True,
        "required_graph_artifact_types": [
            "source_graph",
            "evidence_graph",
            "claim_graph",
            "rule_claim_graph",
        ],
        "neighbor_filters": {
            "rule_ids": [rule_id] if rule_id else [],
            "source_record_ids": source_record_ids,
            "authority_categories": strings([rule.get("authority_category")]),
        },
    }


def _component_graph_expansion_contract(
    *,
    component: dict,
    component_id: str,
    profile: ForestPlanProfile,
    inventory_id: str,
) -> dict:
    return {
        "contract_type": "forest_plan_component_graph_expansion",
        "start_node_types": ["forest_plan_component", "source_record", "package_fact"],
        "relationship_types": list(FOREST_PLAN_GRAPH_RELATIONSHIP_TYPES),
        "max_depth": 3,
        "requires_path_trace": True,
        "required_graph_artifact_types": [
            "source_graph",
            "evidence_graph",
            "forest_plan_component_inventory",
        ],
        "neighbor_filters": {
            "forest_unit_id": profile.forest_unit_id,
            "component_inventory_id": inventory_id,
            "component_ids": [component_id] if component_id else [],
            "geographic_area_ids": strings(component.get("geographic_area_ids")),
            "management_area_ids": strings(component.get("management_area_ids")),
            "overlay_ids": strings(component.get("overlay_ids")),
        },
    }


def _rule_dependency_contract(rule: dict) -> dict:
    return {
        "dependency_rule_ids": strings(
            rule.get("dependency_rule_ids")
            or rule.get("depends_on_rule_ids")
            or rule.get("dependencies")
        ),
        "exception_rule_ids": strings(
            rule.get("exception_rule_ids") or rule.get("exceptions")
        ),
        "supersedes_rule_ids": strings(rule.get("supersedes_rule_ids")),
        "superseded_by_rule_ids": strings(rule.get("superseded_by_rule_ids")),
        "supporting_source_record_ids": strings(rule.get("supporting_source_record_ids")),
    }


def _component_dependency_contract(profile: ForestPlanProfile) -> dict:
    supporting_records = [
        {
            "role": record.role,
            "source_record_id": record.source_record_id,
            "required_for": record.required_for,
        }
        for record in profile.supporting_source_records
    ]
    return {
        "dependency_rule_ids": [],
        "exception_rule_ids": [],
        "supersedes_rule_ids": [],
        "superseded_by_rule_ids": [],
        "supporting_source_record_ids": sorted(
            {record["source_record_id"] for record in supporting_records}
        ),
        "supporting_source_records": supporting_records,
    }


def _rule_search_coverage_requirements(
    *,
    rule: dict,
    positive_trigger_groups: list[list[str]],
    negative_trigger_groups: list[list[str]],
) -> list[dict]:
    base = {
        "required_artifacts": [
            "package_fact_graph",
            "applicability_retrieval_trace",
            "search_coverage_certificates",
        ],
        "required_query_types": ["exact_keyword", "bm25", "metadata_filter", "package_section"],
        "requires_searched_index_hash": True,
    }
    if rule.get("applicability_mode") == "conditional":
        requirements = [
            {
                **base,
                "coverage_class": "positive_trigger_miss",
                "required_trigger_groups": positive_trigger_groups,
            }
        ]
        if negative_trigger_groups:
            requirements.append(
                {
                    **base,
                    "coverage_class": "explicit_negative_trigger",
                    "required_trigger_groups": negative_trigger_groups,
                }
            )
        return requirements
    return [
        {
            **base,
            "coverage_class": "baseline_exclusion_requires_adjudication",
            "requires_adjudication_for_not_applicable": True,
        }
    ]


def _component_search_coverage_requirements(
    *,
    component: dict,
    positive_trigger_groups: list[list[str]],
) -> list[dict]:
    base = {
        "required_artifacts": [
            "package_fact_graph",
            "applicability_retrieval_trace",
            "applicability_graph_trace",
            "search_coverage_certificates",
        ],
        "required_query_types": ["exact_keyword", "bm25", "metadata_filter", "package_section"],
        "requires_searched_index_hash": True,
    }
    return [
        {
            **base,
            "coverage_class": "forest_plan_scope_miss",
            "required_package_fact_types": _component_required_package_fact_types(component),
        },
        {
            **base,
            "coverage_class": "component_trigger_miss",
            "required_trigger_groups": positive_trigger_groups,
        },
    ]
