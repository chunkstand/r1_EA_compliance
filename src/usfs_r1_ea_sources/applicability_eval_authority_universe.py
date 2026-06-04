from __future__ import annotations

from pathlib import Path
from typing import Any

from .applicability_eval_support import _dedupe
from .applicability_eval_support import _dedupe_groups
from .applicability_eval_support import _rule_ids
from .applicability_eval_support import _stable_sha256
from .applicability_eval_support import _string_groups
from .applicability_eval_support import _strings
from .applicability_eval_support import _template_rule_ids
from .applicability_eval_support import _utc_now
from .applicability_eval_support import _write_json
from .records import sha256_file


def _write_authority_universe(
    *,
    applicability_dir: Path,
    review_id: str,
    source_set_id: str,
    case: dict[str, Any],
    base_rule_pack_path: Path,
    base_rule_pack: dict[str, Any],
    rules: list[dict[str, Any]],
    authority_family_template_set: dict[str, Any] | None,
    authority_family_templates: list[dict[str, Any]],
) -> Path:
    rule_candidates = [
        _candidate_from_rule(
            source_set_id=source_set_id,
            base_rule_pack=base_rule_pack,
            rule=rule,
        )
        for rule in rules
    ]
    authority_family_candidates = [
        _candidate_from_authority_family_template(
            source_set_id=source_set_id,
            template_set=authority_family_template_set or {},
            template=template,
        )
        for template in authority_family_templates
    ]
    explicit_candidates = _explicit_candidate_authorities(
        case=case,
        source_set_id=source_set_id,
    )
    candidates = [*rule_candidates, *authority_family_candidates, *explicit_candidates]
    without_hash = {
        "schema_version": "authority-universe-snapshot-v0",
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_pack_sha256": sha256_file(base_rule_pack_path),
        "catalog_sha256": _stable_sha256(
            {
                "source_set_id": source_set_id,
                "rules": _rule_ids(rules),
                "authority_family_rule_ids": _template_rule_ids(authority_family_templates),
                "explicit_candidate_authorities": explicit_candidates,
            }
        ),
        "source_claims_sha256": None,
        "rule_claim_links_sha256": None,
        "forest_plan_component_inventory_sha256": None,
        "artifact_paths": {
            "base_rule_pack_path": str(base_rule_pack_path),
            "authority_family_templates_path": (
                str(authority_family_template_set.get("_path"))
                if authority_family_template_set
                and authority_family_template_set.get("_path")
                else None
            ),
        },
        "validation": {"passed": True, "checks": []},
        "candidate_authorities": candidates,
    }
    authority_universe_sha256 = _stable_sha256(without_hash)
    payload = {
        **without_hash,
        "authority_universe_id": (
            f"authority-universe:{review_id}:{source_set_id}:{authority_universe_sha256[:16]}"
        ),
        "authority_universe_sha256": authority_universe_sha256,
        "summary": {
            "schema_version": "authority-universe-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "candidate_authority_count": len(candidates),
            "rule_template_candidate_count": len(rule_candidates),
            "authority_family_rule_template_candidate_count": len(
                authority_family_candidates
            ),
            "explicit_candidate_authority_count": len(explicit_candidates),
            "candidate_type_counts": _candidate_type_counts(candidates),
            "validation_passed": True,
        },
    }
    path = applicability_dir / "authority_universe_snapshot.json"
    _write_json(path, payload)
    return path


def _explicit_candidate_authorities(
    *,
    case: dict[str, Any],
    source_set_id: str,
) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in case.get("candidate_authorities") or []
        if isinstance(item, dict)
    ]
    candidates.extend(
        item
        for item in case.get("extra_candidate_authorities") or []
        if isinstance(item, dict)
    )
    explicit = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_authority_id") or "").strip()
        if not candidate_id:
            raise ValueError("Explicit applicability eval candidates need candidate_authority_id")
        normalized = {**candidate, "source_set_id": candidate.get("source_set_id") or source_set_id}
        source_record_ids = _dedupe(
            [
                *_strings(normalized.get("source_record_ids")),
                *[
                    str(record.get("source_record_id") or "")
                    for record in normalized.get("source_records") or []
                    if isinstance(record, dict)
                ],
            ]
        )
        normalized["source_record_ids"] = source_record_ids
        authority_family_ids = _dedupe(
            [
                *_strings(normalized.get("authority_family_ids")),
                *_strings([normalized.get("authority_family_id")]),
            ]
        )
        if authority_family_ids:
            normalized["authority_family_ids"] = authority_family_ids
            normalized.setdefault("authority_family_id", authority_family_ids[0])
        if source_record_ids and not normalized.get("source_records"):
            document_role = str(
                normalized.get("authority_document_role")
                or normalized.get("authority_category")
                or "source"
            )
            normalized["source_records"] = [
                {
                    "source_record_id": source_record_id,
                    "title": source_record_id,
                    "document_role": document_role,
                    "citation_label": f"{source_record_id} | {source_record_id}",
                }
                for source_record_id in source_record_ids
            ]
        if source_record_ids and not isinstance(normalized.get("source_role_filters"), dict):
            normalized["source_role_filters"] = {
                "source_record_ids": source_record_ids,
                "document_roles": _strings([normalized.get("authority_document_role")]),
                "authority_categories": _strings([normalized.get("authority_category")]),
            }
        if source_record_ids and not isinstance(normalized.get("required_source_evidence"), dict):
            normalized["required_source_evidence"] = {
                "source_record_ids": source_record_ids,
                "requires_catalog_record": True,
                "requires_artifact_sha256": True,
                "requires_source_record": True,
                "requires_source_claim_linkage": False,
            }
        if not isinstance(normalized.get("source_evidence_availability"), dict):
            normalized["source_evidence_availability"] = {
                "available": bool(source_record_ids),
                "catalog_record_present": bool(source_record_ids),
                "artifact_sha256_present": bool(source_record_ids),
                "source_claim_link_count": 0,
                "rule_claim_gap_count": 0,
            }
        explicit.append(normalized)
    explicit.sort(key=lambda item: str(item.get("candidate_authority_id") or ""))
    return explicit


def _candidate_type_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        candidate_type = str(candidate.get("candidate_authority_type") or "unknown")
        counts[candidate_type] = counts.get(candidate_type, 0) + 1
    return dict(sorted(counts.items()))


def _candidate_from_rule(
    *,
    source_set_id: str,
    base_rule_pack: dict[str, Any],
    rule: dict[str, Any],
) -> dict[str, Any]:
    rule_id = str(rule.get("id") or "")
    source_record_id = str(
        rule.get("authority_source_record_id")
        or (rule.get("source_filters") or {}).get("source_record_id")
        or ""
    )
    document_role = str(
        rule.get("authority_document_role")
        or (rule.get("source_filters") or {}).get("document_role")
        or rule.get("authority_category")
        or "source"
    )
    positive_groups = _positive_groups(rule)
    negative_terms = _strings(rule.get("does_not_apply_if_package_terms"))
    negative_groups = [[term] for term in negative_terms]
    package_terms = _strings(rule.get("package_terms")) or _strings(
        rule.get("applies_if_package_terms")
    )
    package_query = str(rule.get("package_query") or " ".join(package_terms) or rule_id)
    source_query = str(rule.get("source_query") or rule.get("title") or rule_id)
    return {
        "candidate_authority_id": (
            "rule-template:"
            f"{base_rule_pack.get('rule_pack_id')}:{base_rule_pack.get('version')}:{rule_id}"
        ),
        "candidate_authority_type": "rule_template",
        "source_set_id": source_set_id,
        "authority_category": rule.get("authority_category"),
        "authority_document_role": document_role,
        "source_record_ids": [source_record_id] if source_record_id else [],
        "source_records": (
            [
                {
                    "source_record_id": source_record_id,
                    "title": rule.get("title"),
                    "document_role": document_role,
                    "citation_label": f"{source_record_id} | {rule.get('title') or rule_id}",
                }
            ]
            if source_record_id
            else []
        ),
        "required_package_fact_types": [
            "action",
            "agency",
            "decision_posture",
            "nepa_level",
            "package_section",
            "evidence_span",
        ],
        "positive_trigger_groups": positive_groups,
        "negative_trigger_groups": negative_groups,
        "source_role_filters": {
            "source_record_ids": [source_record_id] if source_record_id else [],
            "document_roles": [document_role],
            "authority_categories": [str(rule.get("authority_category") or "")],
        },
        "package_section_filters": {
            "package_query": package_query,
            "package_terms": package_terms,
            "package_section_terms": [],
            "preferred_section_families": _strings(
                rule.get("preferred_package_sections")
            ),
        },
        "required_source_evidence": {
            "requires_source_record": bool(source_record_id),
            "requires_source_claim_linkage": False,
        },
        "retrieval_contract": {
            "contract_type": "rule_template_retrieval",
            "query_plan_id": f"retrieval-plan:{rule_id}",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "source_queries": [source_query],
            "package_queries": [package_query],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "rule_template_graph_expansion",
            "start_node_types": ["rule_template", "source_record", "authority"],
            "relationship_types": [
                "source_record",
                "authority_category",
                "source_claim",
                "rule_claim_link",
                "package_fact",
                "evidence_span",
            ],
            "max_depth": 2,
            "requires_path_trace": True,
        },
        "dependency_contract": {
            "dependency_rule_ids": [],
            "exception_rule_ids": [],
            "supersedes_rule_ids": [],
        },
        "search_coverage_requirements": [
            {
                "coverage_class": "positive_trigger_miss",
                "required_query_types": [
                    "exact_keyword",
                    "bm25",
                    "metadata_filter",
                    "package_section",
                    "source_role",
                ],
                "required_artifacts": [
                    "package_fact_graph",
                    "applicability_retrieval_trace",
                    "search_coverage_certificates",
                ],
                "requires_searched_index_hash": True,
            }
        ],
        "rule_template": {
            "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
            "base_rule_pack_version": base_rule_pack.get("version"),
            "rule_id": rule_id,
            "title": rule.get("title"),
            "question": rule.get("question"),
            "requirement": rule.get("requirement"),
            "severity": rule.get("severity"),
            "applicability_mode": rule.get("applicability_mode"),
            "trigger_arbitration": (
                rule.get("trigger_arbitration")
                if isinstance(rule.get("trigger_arbitration"), dict)
                else None
            ),
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_claim_link_count": 0,
            "rule_claim_gap_count": 0,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "rule_template",
            "applicability_mode": rule.get("applicability_mode"),
            "baseline_required": rule.get("applicability_mode") == "baseline",
            "positive_package_term_groups": positive_groups,
            "negative_package_terms": negative_terms,
            "trigger_arbitration": (
                rule.get("trigger_arbitration")
                if isinstance(rule.get("trigger_arbitration"), dict)
                else None
            ),
        },
        "source_claim_link_ids": [],
        "rule_claim_gap_ids": [],
    }


def _candidate_from_authority_family_template(
    *,
    source_set_id: str,
    template_set: dict[str, Any],
    template: dict[str, Any],
) -> dict[str, Any]:
    rule_id = str(template.get("rule_id") or template.get("template_id") or "")
    family_id = str(template.get("authority_family_id") or "")
    source_record_id = str(
        template.get("authority_source_record_id")
        or (_strings(template.get("source_record_ids"))[:1] or [""])[0]
    )
    source_record_ids = _dedupe([source_record_id, *_strings(template.get("source_record_ids"))])
    document_role = str(
        template.get("authority_document_role")
        or (template.get("source_filters") or {}).get("document_role")
        or template.get("authority_category")
        or "source"
    )
    authority_category = str(template.get("authority_category") or document_role)
    positive_groups = _authority_family_positive_trigger_groups(template)
    negative_groups = _authority_family_negative_trigger_groups(template)
    source_role_filters = {
        "source_record_ids": source_record_ids,
        "document_roles": [document_role],
        "authority_categories": [authority_category],
        "primary_source_record_id": source_record_id,
    }
    package_section_filters = {
        "package_query": str(template.get("package_query") or rule_id),
        "package_terms": _strings(template.get("package_terms")),
        "package_section_terms": _strings(template.get("package_section_terms")),
        "preferred_section_families": _strings(template.get("package_section_families")),
    }
    return {
        "candidate_authority_id": (
            "authority-family-template:"
            f"{template_set.get('template_set_id')}:{template_set.get('version')}:"
            f"{family_id}:{rule_id}"
        ),
        "candidate_authority_type": "authority_family_rule_template",
        "source_set_id": source_set_id,
        "authority_family_id": family_id,
        "authority_category": authority_category,
        "authority_document_role": document_role,
        "source_record_ids": source_record_ids,
        "source_records": [
            {
                "source_record_id": record_id,
                "title": template.get("title"),
                "document_role": document_role,
                "citation_label": f"{record_id} | {template.get('title') or rule_id}",
            }
            for record_id in source_record_ids
        ],
        "required_package_fact_types": _strings(template.get("package_fact_types")),
        "positive_trigger_groups": positive_groups,
        "negative_trigger_groups": negative_groups,
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "required_source_evidence": {
            "source_record_ids": source_record_ids,
            "primary_source_record_id": source_record_id,
            "supporting_source_record_ids": _strings(
                template.get("supporting_source_record_ids")
            ),
            "excluded_source_record_ids": _strings(
                template.get("excluded_source_record_ids")
            ),
            "document_roles": [document_role],
            "source_role_filters": source_role_filters,
            "requires_catalog_record": True,
            "requires_artifact_sha256": True,
            "requires_source_record": True,
            "requires_source_claim_linkage": False,
            "source_evidence_requirements": _strings(
                template.get("source_evidence_requirements")
            ),
        },
        "retrieval_contract": {
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
            "source_queries": _strings([template.get("source_query")]),
            "package_queries": _strings([template.get("package_query")]),
            "source_role_filters": source_role_filters,
            "package_section_filters": package_section_filters,
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "authority_family_rule_template_graph_expansion",
            "start_node_types": [
                "authority_family_rule_template",
                "source_record",
                "authority",
            ],
            "relationship_types": [
                "source_record",
                "authority_category",
                "source_claim",
                "rule_claim_link",
                "package_fact",
                "evidence_span",
            ],
            "max_depth": 2,
            "requires_path_trace": True,
            "neighbor_filters": {
                "rule_ids": [rule_id],
                "authority_family_ids": [family_id],
                "source_record_ids": source_record_ids,
                "authority_categories": [authority_category],
            },
        },
        "dependency_contract": _authority_family_dependency_contract(template),
        "search_coverage_requirements": _authority_family_search_coverage_requirements(
            template=template,
            positive_trigger_groups=positive_groups,
            negative_trigger_groups=negative_groups,
        ),
        "rule_template": {
            "base_rule_pack_id": template_set.get("base_rule_pack_id"),
            "base_rule_pack_version": template_set.get("base_rule_pack_version"),
            "authority_family_template_set_id": template_set.get("template_set_id"),
            "authority_family_template_set_version": template_set.get("version"),
            "template_id": template.get("template_id"),
            "authority_family_id": family_id,
            "rule_id": rule_id,
            "title": template.get("title"),
            "question": template.get("question"),
            "requirement": template.get("requirement"),
            "severity": template.get("severity"),
            "applicability_mode": template.get("applicability_mode"),
            "authority_source_record_id": source_record_id,
            "authority_category": authority_category,
            "package_query": template.get("package_query"),
            "package_terms": _strings(template.get("package_terms")),
            "package_section_terms": _strings(template.get("package_section_terms")),
            "applies_if_package_terms": _strings(template.get("applies_if_package_terms")),
            "applies_if_package_term_groups": _string_groups(
                template.get("applies_if_package_term_groups")
            ),
            "does_not_apply_if_package_terms": _strings(
                template.get("does_not_apply_if_package_terms")
            ),
            "source_query": template.get("source_query"),
            "source_filters": (
                template.get("source_filters")
                if isinstance(template.get("source_filters"), dict)
                else {}
            ),
            "evidence_expectation": template.get("evidence_expectation"),
            "trigger_arbitration": (
                template.get("trigger_arbitration")
                if isinstance(template.get("trigger_arbitration"), dict)
                else None
            ),
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_claim_link_count": 0,
            "rule_claim_gap_count": 0,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "rule_template",
            "candidate_authority_type": "authority_family_rule_template",
            "authority_family_id": family_id,
            "applicability_mode": template.get("applicability_mode"),
            "baseline_required": False,
            "package_query": template.get("package_query"),
            "package_terms": _strings(template.get("package_terms")),
            "positive_package_terms": _strings(template.get("applies_if_package_terms")),
            "positive_package_term_groups": _string_groups(
                template.get("applies_if_package_term_groups")
            ),
            "negative_package_terms": _strings(
                template.get("does_not_apply_if_package_terms")
            ),
            "source_query": template.get("source_query"),
            "source_filters": (
                template.get("source_filters")
                if isinstance(template.get("source_filters"), dict)
                else {}
            ),
            "evidence_expectation": template.get("evidence_expectation"),
            "trigger_arbitration": (
                template.get("trigger_arbitration")
                if isinstance(template.get("trigger_arbitration"), dict)
                else None
            ),
        },
        "source_claim_link_ids": [],
        "rule_claim_gap_ids": [],
    }


def _selected_rules(base_rule_pack: dict[str, Any], case: dict[str, Any]) -> list[dict[str, Any]]:
    if "candidate_rule_ids" in case:
        rule_ids = _strings(case.get("candidate_rule_ids"))
    elif "rule_ids" in case:
        rule_ids = _strings(case.get("rule_ids"))
    else:
        rule_ids = []
    rules = [rule for rule in base_rule_pack.get("rules") or [] if isinstance(rule, dict)]
    if "candidate_rule_ids" not in case and "rule_ids" not in case:
        return rules
    wanted = set(rule_ids)
    selected = [rule for rule in rules if str(rule.get("id") or "") in wanted]
    missing = sorted(wanted - {str(rule.get("id") or "") for rule in selected})
    if missing:
        raise ValueError(f"Applicability eval case references unknown rule IDs: {missing}")
    return selected


def _selected_authority_family_templates(
    template_set: dict[str, Any] | None,
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    rule_ids = set(_strings(case.get("candidate_authority_family_rule_ids")))
    family_ids = set(_strings(case.get("candidate_authority_family_ids")))
    template_ids = set(_strings(case.get("candidate_authority_family_template_ids")))
    if not (rule_ids or family_ids or template_ids):
        return []
    if not template_set:
        raise ValueError(
            "Applicability eval case references authority-family templates, "
            "but no template set is loaded."
        )
    templates = [item for item in template_set.get("templates") or [] if isinstance(item, dict)]
    selected = [
        template
        for template in templates
        if (
            str(template.get("rule_id") or "") in rule_ids
            or str(template.get("authority_family_id") or "") in family_ids
            or str(template.get("template_id") or "") in template_ids
        )
    ]
    selected_rule_ids = {str(template.get("rule_id") or "") for template in selected}
    selected_family_ids = {
        str(template.get("authority_family_id") or "") for template in selected
    }
    selected_template_ids = {
        str(template.get("template_id") or "") for template in selected
    }
    missing = {
        "rule_ids": sorted(rule_ids - selected_rule_ids),
        "authority_family_ids": sorted(family_ids - selected_family_ids),
        "template_ids": sorted(template_ids - selected_template_ids),
    }
    if any(missing.values()):
        raise ValueError(
            "Applicability eval case references unknown authority-family templates: "
            f"{missing}"
        )
    overrides = case.get("candidate_authority_family_template_overrides_by_rule_id")
    if isinstance(overrides, dict):
        selected = [
            _template_with_override(
                template,
                overrides.get(str(template.get("rule_id") or "")),
            )
            for template in selected
        ]
    return selected


def _template_with_override(template: dict[str, Any], override: Any) -> dict[str, Any]:
    if not isinstance(override, dict):
        return template
    merged = {**template}
    for key, value in override.items():
        merged[str(key)] = value
    return merged


def _positive_groups(rule: dict[str, Any]) -> list[list[str]]:
    groups = [
        [str(term) for term in group if str(term or "").strip()]
        for group in rule.get("applies_if_package_term_groups") or []
        if isinstance(group, list)
    ]
    if groups:
        return groups
    terms = _strings(rule.get("applies_if_package_terms"))
    return [[term] for term in terms]


def _authority_family_positive_trigger_groups(template: dict[str, Any]) -> list[list[str]]:
    groups = _string_groups(template.get("applies_if_package_term_groups"))
    terms = _strings(template.get("applies_if_package_terms"))
    if terms:
        groups.append(terms)
    if not groups:
        package_terms = _strings(template.get("package_terms"))
        if package_terms:
            groups.append(package_terms)
    return _dedupe_groups(groups)


def _authority_family_negative_trigger_groups(template: dict[str, Any]) -> list[list[str]]:
    return _dedupe_groups(
        [[term] for term in _strings(template.get("does_not_apply_if_package_terms"))]
    )


def _authority_family_dependency_contract(template: dict[str, Any]) -> dict[str, Any]:
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
        "dependency_rule_ids": _strings(dependency.get("dependency_rule_ids")),
        "dependency_family_ids": _strings(dependency.get("dependency_family_ids")),
        "exception_rule_ids": _strings(dependency.get("exception_rule_ids")),
        "exception_family_ids": _strings(dependency.get("exception_family_ids")),
        "supersedes_rule_ids": _strings(dependency.get("supersedes_rule_ids")),
        "superseded_by_rule_ids": _strings(dependency.get("superseded_by_rule_ids")),
        "superseded_by_family_ids": _strings(
            dependency.get("superseded_by_family_ids")
        ) or _strings([supersession.get("replacement_family_id")]),
        "supporting_source_record_ids": _strings(
            template.get("supporting_source_record_ids")
        ),
        "excluded_source_record_ids": _strings(template.get("excluded_source_record_ids")),
        "supersession": supersession or None,
    }


def _authority_family_search_coverage_requirements(
    *,
    template: dict[str, Any],
    positive_trigger_groups: list[list[str]],
    negative_trigger_groups: list[list[str]],
) -> list[dict[str, Any]]:
    base = {
        "required_artifacts": [
            "package_fact_graph",
            "applicability_retrieval_trace",
            "applicability_graph_trace",
            "search_coverage_certificates",
        ],
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
        ],
        "requires_searched_index_hash": True,
        "required_package_fact_types": _strings(template.get("package_fact_types")),
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
