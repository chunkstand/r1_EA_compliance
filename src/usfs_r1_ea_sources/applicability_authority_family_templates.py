from __future__ import annotations

from .applicability_contract_support import authority_document_role
from .applicability_contract_support import dedupe_groups
from .applicability_contract_support import dedupe_strings
from .applicability_contract_support import source_record_summary
from .applicability_contract_support import string_groups
from .applicability_contract_support import strings


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


def authority_family_template_candidates(
    *,
    source_set_id: str,
    template_set: dict | None,
    catalog_by_source_id: dict[str, dict],
) -> list[dict]:
    if not isinstance(template_set, dict):
        return []
    templates = template_set.get("templates")
    if not isinstance(templates, list):
        return []
    candidates = []
    template_set_id = str(template_set.get("template_set_id") or "")
    template_set_version = str(template_set.get("version") or "")
    for template in templates:
        if not isinstance(template, dict):
            continue
        template_id = str(template.get("template_id") or "")
        family_id = str(template.get("authority_family_id") or "")
        rule_id = str(template.get("rule_id") or template_id)
        source_record_id = str(template.get("authority_source_record_id") or "").strip()
        catalog_record = catalog_by_source_id.get(source_record_id)
        document_role = authority_document_role(template, catalog_record)
        authority_category = str(template.get("authority_category") or "").strip()
        source_record_ids = _template_source_record_ids(template, source_record_id)
        source_records = [
            source_record_summary(catalog_by_source_id.get(record_id))
            for record_id in source_record_ids
            if catalog_by_source_id.get(record_id)
        ]
        source_role_filters = _authority_family_source_role_filters(
            template=template,
            source_record_ids=source_record_ids,
            document_role=document_role,
            authority_category=authority_category,
        )
        package_section_filters = _authority_family_package_section_filters(template)
        positive_trigger_groups = _authority_family_positive_trigger_groups(template)
        negative_trigger_groups = _authority_family_negative_trigger_groups(template)
        required_package_fact_types = strings(template.get("package_fact_types"))
        candidates.append(
            {
                "candidate_authority_id": (
                    "authority-family-template:"
                    f"{template_set_id}:{template_set_version}:{family_id}:{rule_id}"
                ),
                "candidate_authority_type": "authority_family_rule_template",
                "source_set_id": source_set_id,
                "authority_family_id": family_id,
                "authority_category": authority_category,
                "authority_document_role": document_role,
                "source_record_ids": source_record_ids,
                "source_records": source_records,
                "required_package_fact_types": required_package_fact_types,
                "positive_trigger_groups": positive_trigger_groups,
                "negative_trigger_groups": negative_trigger_groups,
                "source_role_filters": source_role_filters,
                "package_section_filters": package_section_filters,
                "required_source_evidence": _authority_family_required_source_evidence(
                    template=template,
                    source_record_id=source_record_id,
                    document_role=document_role,
                    source_role_filters=source_role_filters,
                ),
                "retrieval_contract": _authority_family_retrieval_contract(
                    template=template,
                    rule_id=rule_id,
                    source_role_filters=source_role_filters,
                    package_section_filters=package_section_filters,
                ),
                "graph_expansion_contract": _authority_family_graph_expansion_contract(
                    template=template,
                    rule_id=rule_id,
                    source_record_id=source_record_id,
                ),
                "dependency_contract": _authority_family_dependency_contract(template),
                "search_coverage_requirements": _authority_family_search_coverage_requirements(
                    template=template,
                    positive_trigger_groups=positive_trigger_groups,
                    negative_trigger_groups=negative_trigger_groups,
                ),
                "rule_template": _authority_family_rule_template_metadata(
                    template=template,
                    template_set=template_set,
                    rule_id=rule_id,
                ),
                "source_evidence_availability": _authority_family_source_evidence_availability(
                    catalog_record=catalog_record,
                    source_records=source_records,
                ),
                "deterministic_applicability_test_contract": (
                    _authority_family_applicability_contract(template=template)
                ),
                "source_claim_link_ids": [],
                "rule_claim_gap_ids": [],
            }
        )
    return candidates


def _template_source_record_ids(template: dict, source_record_id: str) -> list[str]:
    explicit = strings(template.get("source_record_ids"))
    if explicit:
        return explicit
    return dedupe_strings(
        [
            source_record_id,
            *strings(template.get("supporting_source_record_ids")),
            *strings(template.get("excluded_source_record_ids")),
        ]
    )


def _authority_family_source_role_filters(
    *,
    template: dict,
    source_record_ids: list[str],
    document_role: str | None,
    authority_category: str | None,
) -> dict:
    source_filters = (
        template.get("source_filters")
        if isinstance(template.get("source_filters"), dict)
        else {}
    )
    supporting_source_record_ids = strings(template.get("supporting_source_record_ids"))
    return {
        "source_record_ids": source_record_ids,
        "primary_source_record_id": template.get("authority_source_record_id"),
        "supporting_source_record_ids": supporting_source_record_ids,
        "excluded_source_record_ids": strings(template.get("excluded_source_record_ids")),
        "document_roles": [document_role] if document_role else [],
        "authority_categories": strings([authority_category]),
        "source_filters": source_filters,
    }


def _authority_family_package_section_filters(template: dict) -> dict:
    return {
        "package_query": template.get("package_query"),
        "package_terms": strings(template.get("package_terms")),
        "package_section_terms": strings(template.get("package_section_terms")),
        "package_section_term_groups": string_groups(template.get("package_section_term_groups")),
        "preferred_section_families": strings(template.get("package_section_families")),
        "package_fact_types": strings(template.get("package_fact_types")),
    }


def _authority_family_positive_trigger_groups(template: dict) -> list[list[str]]:
    groups = string_groups(template.get("applies_if_package_term_groups"))
    terms = strings(template.get("applies_if_package_terms"))
    if terms:
        groups.append(terms)
    if not groups:
        package_terms = strings(template.get("package_terms"))
        if package_terms:
            groups.append(package_terms)
    return dedupe_groups(groups)


def _authority_family_negative_trigger_groups(template: dict) -> list[list[str]]:
    return dedupe_groups(
        [[term] for term in strings(template.get("does_not_apply_if_package_terms"))]
    )


def _authority_family_required_source_evidence(
    *,
    template: dict,
    source_record_id: str | None,
    document_role: str | None,
    source_role_filters: dict,
) -> dict:
    return {
        "source_record_ids": _template_source_record_ids(template, source_record_id or ""),
        "primary_source_record_id": source_record_id,
        "supporting_source_record_ids": strings(template.get("supporting_source_record_ids")),
        "excluded_source_record_ids": strings(template.get("excluded_source_record_ids")),
        "document_roles": [document_role] if document_role else [],
        "source_role_filters": source_role_filters,
        "requires_catalog_record": True,
        "requires_artifact_sha256": True,
        "requires_source_record": True,
        "requires_source_claim_linkage": False,
        "source_evidence_requirements": strings(template.get("source_evidence_requirements")),
    }


def _authority_family_retrieval_contract(
    *,
    template: dict,
    rule_id: str,
    source_role_filters: dict,
    package_section_filters: dict,
) -> dict:
    return {
        "contract_type": "authority_family_rule_template_retrieval",
        "query_plan_id": f"retrieval-plan:authority-family-template:{rule_id}",
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
            "source_role",
        ],
        "optional_query_types": ["vector"],
        "source_queries": strings([template.get("source_query")]),
        "package_queries": strings([template.get("package_query")]),
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "fused_ranking_strategy": "reciprocal_rank_fusion",
        "requires_selected_and_rejected_results": True,
        "searched_index_hash_required": True,
    }


def _authority_family_graph_expansion_contract(
    *,
    template: dict,
    rule_id: str,
    source_record_id: str | None,
) -> dict:
    dependency_contract = _authority_family_dependency_contract(template)
    return {
        "contract_type": "authority_family_rule_template_graph_expansion",
        "start_node_types": ["authority_family_rule_template", "source_record", "authority"],
        "relationship_types": list(RULE_GRAPH_RELATIONSHIP_TYPES),
        "max_depth": 2,
        "requires_path_trace": True,
        "required_graph_artifact_types": [
            "source_graph",
            "evidence_graph",
            "claim_graph",
            "authority_family_template_graph",
        ],
        "neighbor_filters": {
            "rule_ids": [rule_id] if rule_id else [],
            "authority_family_ids": strings([template.get("authority_family_id")]),
            "source_record_ids": _template_source_record_ids(template, source_record_id or ""),
            "authority_categories": strings([template.get("authority_category")]),
            "supporting_source_record_ids": dependency_contract["supporting_source_record_ids"],
            "superseded_by_family_ids": dependency_contract["superseded_by_family_ids"],
        },
    }


def _authority_family_dependency_contract(template: dict) -> dict:
    dependency = (
        template.get("dependency_contract")
        if isinstance(template.get("dependency_contract"), dict)
        else {}
    )
    supersession = (
        template.get("supersession")
        if isinstance(template.get("supersession"), dict)
        else {}
    )
    return {
        "dependency_rule_ids": strings(dependency.get("dependency_rule_ids")),
        "dependency_family_ids": strings(dependency.get("dependency_family_ids")),
        "exception_rule_ids": strings(dependency.get("exception_rule_ids")),
        "exception_family_ids": strings(dependency.get("exception_family_ids")),
        "supersedes_rule_ids": strings(dependency.get("supersedes_rule_ids")),
        "superseded_by_rule_ids": strings(dependency.get("superseded_by_rule_ids")),
        "superseded_by_family_ids": strings(dependency.get("superseded_by_family_ids"))
        or strings([supersession.get("replacement_family_id")]),
        "supporting_source_record_ids": strings(template.get("supporting_source_record_ids")),
        "excluded_source_record_ids": strings(template.get("excluded_source_record_ids")),
        "supersession": supersession or None,
    }


def _authority_family_search_coverage_requirements(
    *,
    template: dict,
    positive_trigger_groups: list[list[str]],
    negative_trigger_groups: list[list[str]],
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
        "required_package_fact_types": strings(template.get("package_fact_types")),
    }
    requirements = [
        {
            **base,
            "coverage_class": "authority_family_positive_trigger_miss",
            "required_trigger_groups": positive_trigger_groups,
        }
    ]
    if negative_trigger_groups:
        requirements.append(
            {
                **base,
                "coverage_class": "authority_family_explicit_negative_trigger",
                "required_trigger_groups": negative_trigger_groups,
            }
        )
    return requirements


def _authority_family_rule_template_metadata(
    *,
    template: dict,
    template_set: dict,
    rule_id: str,
) -> dict:
    return {
        "base_rule_pack_id": template_set.get("base_rule_pack_id"),
        "base_rule_pack_version": template_set.get("base_rule_pack_version"),
        "authority_family_template_set_id": template_set.get("template_set_id"),
        "authority_family_template_set_version": template_set.get("version"),
        "template_id": template.get("template_id"),
        "authority_family_id": template.get("authority_family_id"),
        "rule_id": rule_id,
        "title": template.get("title"),
        "question": template.get("question"),
        "requirement": template.get("requirement"),
        "severity": template.get("severity"),
        "applicability_mode": template.get("applicability_mode"),
        "authority_source_record_id": template.get("authority_source_record_id"),
        "authority_category": template.get("authority_category"),
        "package_query": template.get("package_query"),
        "package_terms": strings(template.get("package_terms")),
        "package_section_terms": strings(template.get("package_section_terms")),
        "applies_if_package_terms": strings(template.get("applies_if_package_terms")),
        "applies_if_package_term_groups": string_groups(
            template.get("applies_if_package_term_groups")
        ),
        "does_not_apply_if_package_terms": strings(
            template.get("does_not_apply_if_package_terms")
        ),
        "source_query": template.get("source_query"),
        "source_filters": (
            template.get("source_filters")
            if isinstance(template.get("source_filters"), dict)
            else {}
        ),
        "evidence_expectation": template.get("evidence_expectation"),
    }


def _authority_family_applicability_contract(*, template: dict) -> dict:
    return {
        "contract_type": "rule_template",
        "candidate_authority_type": "authority_family_rule_template",
        "authority_family_id": template.get("authority_family_id"),
        "applicability_mode": template.get("applicability_mode"),
        "baseline_required": False,
        "baseline_source_record_ids": [],
        "package_query": template.get("package_query"),
        "package_terms": strings(template.get("package_terms")),
        "package_section_terms": strings(template.get("package_section_terms")),
        "package_section_term_groups": string_groups(
            template.get("package_section_term_groups")
        ),
        "positive_package_terms": strings(template.get("applies_if_package_terms")),
        "positive_package_term_groups": string_groups(
            template.get("applies_if_package_term_groups")
        ),
        "negative_package_terms": strings(
            template.get("does_not_apply_if_package_terms")
        ),
        "source_query": template.get("source_query"),
        "source_filters": (
            template.get("source_filters")
            if isinstance(template.get("source_filters"), dict)
            else {}
        ),
        "source_evidence_requirements": strings(template.get("source_evidence_requirements")),
        "evidence_expectation": template.get("evidence_expectation"),
    }


def _authority_family_source_evidence_availability(
    *,
    catalog_record: dict | None,
    source_records: list[dict],
) -> dict:
    return {
        "available": catalog_record is not None and bool(catalog_record.get("artifact_sha256")),
        "catalog_record_present": catalog_record is not None,
        "artifact_sha256_present": bool((catalog_record or {}).get("artifact_sha256")),
        "source_record_count": len(source_records),
        "source_status": str((catalog_record or {}).get("source_status") or "") or None,
        "source_claim_linkage_recorded": False,
        "source_claim_linkage_required": False,
    }
