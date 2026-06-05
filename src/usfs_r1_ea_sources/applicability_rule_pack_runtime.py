from __future__ import annotations

from pathlib import Path
from typing import Any
import copy

from .applicability_rule_pack_support import _authority_ids
from .applicability_rule_pack_support import _evidence_refs
from .applicability_rule_pack_support import _first_present
from .applicability_rule_pack_support import _optional_file_sha256
from .applicability_rule_pack_support import _safe_id
from .applicability_rule_pack_support import _strings
from .records import sha256_file
from .rule_packs import GENERATED_RULE_PACK_SCHEMA_VERSION


def _generated_rule_pack(
    *,
    review_id: str,
    source_set_id: str | None,
    base_rule_pack_path: Path,
    base_rule_pack: dict[str, Any],
    authority_universe: dict[str, Any],
    applicability_validation: dict[str, Any],
    applicable_authorities: dict[str, Any],
    non_applicable_authorities: dict[str, Any],
    decisions: list[dict[str, Any]],
    paths: dict[str, Path],
) -> dict[str, Any]:
    candidates_by_id = {
        str(candidate.get("candidate_authority_id") or ""): candidate
        for candidate in authority_universe.get("candidate_authorities") or []
        if isinstance(candidate, dict)
    }
    decisions_by_candidate = {
        str(decision.get("candidate_authority_id") or ""): decision
        for decision in decisions
        if isinstance(decision, dict)
    }
    base_rules_by_id = {
        str(rule.get("id") or ""): rule
        for rule in base_rule_pack.get("rules") or []
        if isinstance(rule, dict)
    }
    validation_hashes = applicability_validation.get("hashes") or {}
    artifact_hashes = _generated_artifact_hashes(
        validation_hashes=validation_hashes,
        authority_universe=authority_universe,
        paths=paths,
        base_rule_pack_path=base_rule_pack_path,
    )
    rules = []
    for authority in applicable_authorities.get("authorities") or []:
        if not isinstance(authority, dict):
            continue
        candidate_id = str(authority.get("candidate_authority_id") or "")
        candidate = candidates_by_id.get(candidate_id, {})
        decision = decisions_by_candidate.get(candidate_id, {})
        if authority.get("candidate_authority_type") == "forest_plan_component":
            rule = _forest_plan_component_rule(authority=authority, candidate=candidate)
            base_rule_id = None
        elif authority.get("candidate_authority_type") == "authority_family_rule_template":
            rule = _authority_family_template_rule(authority=authority, candidate=candidate)
            base_rule_id = None
        else:
            rule_id = str((authority.get("rule_template") or {}).get("rule_id") or "")
            base_rule = base_rules_by_id.get(rule_id)
            if not base_rule:
                raise ValueError(f"Missing base rule for applicable authority: {rule_id}")
            rule = copy.deepcopy(base_rule)
            base_rule_id = rule_id
        rule["applicability"] = _rule_applicability_metadata(
            authority=authority,
            candidate=candidate,
            decision=decision,
            artifact_hashes=artifact_hashes,
        )
        rule["source_claim_link_requirements"] = _source_claim_link_requirements(candidate)
        rule["package_section_expectations"] = candidate.get("package_section_filters") or {}
        rule["base_rule_id"] = base_rule_id
        rule["generated_rule_id"] = rule.get("id")
        rule["base_rule_pack_id"] = base_rule_pack.get("rule_pack_id")
        rule["base_rule_pack_version"] = base_rule_pack.get("version")
        rule["applicability_decision_id"] = authority.get("decision_id")
        rule["candidate_authority_id"] = candidate_id
        authority_family_ids = _authority_family_ids_for_authority(
            authority=authority,
            candidate=candidate,
            decision=decision,
        )
        rule["authority_family_ids"] = authority_family_ids
        rule["authority_family_id"] = authority_family_ids[0] if authority_family_ids else None
        rule["applicability_artifact_hashes"] = dict(artifact_hashes)
        rule["generated_from_applicability"] = True
        rules.append(rule)
    rules.sort(key=lambda rule: str(rule.get("id") or ""))
    validation_hash = sha256_file(paths["applicability_validation"])
    applicable_hash = sha256_file(paths["applicable_authorities"])
    non_applicable_hash = sha256_file(paths["non_applicable_authorities"])
    generated_rule_pack_id = _safe_id(
        f"generated-{base_rule_pack.get('rule_pack_id')}-{review_id}"
    )
    generated_version = "applicability-v0"
    baseline_source_record_ids = sorted(
        {
            str(rule.get("authority_source_record_id") or "")
            for rule in rules
            if rule.get("applicability_mode") == "baseline"
            and str(rule.get("authority_source_record_id") or "").strip()
        }
    )
    payload = {
        "schema_version": GENERATED_RULE_PACK_SCHEMA_VERSION,
        "rule_pack_id": generated_rule_pack_id,
        "version": generated_version,
        "title": f"Generated Applicability Rule Pack for {review_id}",
        "description": (
            "Generated from validated applicable-authorities artifacts. "
            "Non-applicable authorities remain in non_applicable_authorities.json."
        ),
        "domain": base_rule_pack.get("domain"),
        "jurisdiction": base_rule_pack.get("jurisdiction"),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_pack_sha256": sha256_file(base_rule_pack_path),
        "generated_rule_pack_id": generated_rule_pack_id,
        "generated_rule_pack_version": generated_version,
        "applicability_run_id": applicability_validation.get("applicability_run_id"),
        "applicability_validation_sha256": validation_hash,
        "authority_universe_sha256": validation_hashes.get("authority_universe_sha256"),
        "applicable_authorities_sha256": applicable_hash,
        "non_applicable_authorities_sha256": non_applicable_hash,
        "applicability_provenance_sha256": validation_hashes.get(
            "applicability_provenance_sha256"
        ),
        "package_fact_graph_sha256": validation_hashes.get("package_fact_graph_sha256"),
        "selected_action_sha256": validation_hashes.get("selected_action_sha256"),
        "retrieval_trace_sha256": validation_hashes.get("retrieval_trace_sha256"),
        "graph_trace_sha256": validation_hashes.get("graph_trace_sha256"),
        "search_coverage_certificates_sha256": validation_hashes.get(
            "search_coverage_certificates_sha256"
        ),
        "package_manifest_sha256": validation_hashes.get("package_manifest_sha256"),
        "package_chunks_sha256": validation_hashes.get("package_chunks_sha256"),
        "catalog_sha256": validation_hashes.get("catalog_sha256"),
        "source_set_id": source_set_id,
        "review_id": review_id,
        "applicable_authority_count": len(_authority_ids(applicable_authorities)),
        "non_applicable_authority_count": len(_authority_ids(non_applicable_authorities)),
        "artifact_hashes": artifact_hashes,
        "rules": rules,
    }
    if baseline_source_record_ids:
        payload["baseline_source_record_ids"] = baseline_source_record_ids
    return payload


def _rule_applicability_metadata(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    decision: dict[str, Any],
    artifact_hashes: dict[str, Any],
) -> dict[str, Any]:
    authority_family_ids = _authority_family_ids_for_authority(
        authority=authority,
        candidate=candidate,
        decision=decision,
    )
    return {
        "decision_id": authority.get("decision_id"),
        "candidate_authority_id": authority.get("candidate_authority_id"),
        "candidate_authority_type": authority.get("candidate_authority_type"),
        "authority_family_ids": authority_family_ids,
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "status": authority.get("status"),
        "basis_type": authority.get("basis_type"),
        "applicability_basis": authority.get("applicability_basis"),
        "retrieval_trace_ids": _strings(authority.get("retrieval_trace_ids")),
        "graph_path_ids": _strings(authority.get("graph_path_ids")),
        "source_record_ids": _strings(authority.get("source_record_ids")),
        "document_roles": _strings([authority.get("authority_document_role")]),
        "package_evidence_refs": _evidence_refs(authority.get("package_evidence_spans")),
        "source_evidence_refs": _evidence_refs(authority.get("source_library_evidence_spans")),
        "search_coverage_certificate_ids": _strings(
            authority.get("search_coverage_certificate_ids")
        ),
        "human_adjudication_refs": authority.get("human_adjudication_refs") or [],
        "source_claim_link_requirements": _source_claim_link_requirements(candidate),
        "package_section_expectations": candidate.get("package_section_filters") or {},
        "forest_plan": authority.get("forest_plan") or None,
        "freshness": decision.get("freshness") if isinstance(decision, dict) else {},
        "artifact_hashes": dict(artifact_hashes),
    }


def _forest_plan_component_rule(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    forest_plan = (
        authority.get("forest_plan") if isinstance(authority.get("forest_plan"), dict) else {}
    )
    filters = candidate.get("package_section_filters") or {}
    terms = _strings(filters.get("package_evidence_terms")) or _strings(
        [
            forest_plan.get("section_heading"),
            *(_strings(forest_plan.get("geographic_area_ids"))),
            *(_strings(forest_plan.get("management_area_ids"))),
            *(_strings(forest_plan.get("overlay_ids"))),
        ]
    )
    component_id = str(forest_plan.get("component_id") or authority.get("candidate_authority_id"))
    source_record_id = _first_present(_strings(authority.get("source_record_ids")))
    section_heading = str(forest_plan.get("section_heading") or component_id)
    rule_id = _safe_id(f"forest_plan_component_{component_id}")
    return {
        "id": rule_id,
        "title": f"Forest Plan component applies: {section_heading}",
        "authority_category": "forest_plan",
        "authority_source_record_id": source_record_id,
        "applicability_mode": "conditional",
        "question": f"Does the EA package address Forest Plan component {component_id}?",
        "requirement": (
            f"The EA package should address the applicable Forest Plan component: {section_heading}."
        ),
        "severity": "medium",
        "package_query": " ".join(terms) if terms else section_heading,
        "package_terms": terms or [section_heading],
        "applies_if_package_terms": terms or [section_heading],
        "source_query": f"{section_heading} Forest Plan component",
        "source_filters": {
            "document_role": "forest_plan",
            "source_record_id": source_record_id,
        },
        "evidence_expectation": (
            "A supported finding requires one source-library Forest Plan span and one package span."
        ),
    }


def _authority_family_template_rule(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    rule_template = (
        authority.get("rule_template")
        if isinstance(authority.get("rule_template"), dict)
        else {}
    )
    source_record_id = (
        str(rule_template.get("authority_source_record_id") or "").strip()
        or _first_present(_strings(authority.get("source_record_ids")))
    )
    package_filters = (
        candidate.get("package_section_filters")
        if isinstance(candidate.get("package_section_filters"), dict)
        else {}
    )
    source_filters = (
        rule_template.get("source_filters")
        if isinstance(rule_template.get("source_filters"), dict)
        else {}
    )
    if source_record_id and "source_record_id" not in source_filters:
        source_filters = {**source_filters, "source_record_id": source_record_id}
    return {
        "id": _safe_id(str(rule_template.get("rule_id") or authority["candidate_authority_id"])),
        "title": rule_template.get("title"),
        "authority_category": rule_template.get("authority_category")
        or authority.get("authority_category"),
        "authority_source_record_id": source_record_id,
        "applicability_mode": rule_template.get("applicability_mode") or "conditional",
        "question": rule_template.get("question"),
        "requirement": rule_template.get("requirement"),
        "severity": rule_template.get("severity") or "medium",
        "package_query": rule_template.get("package_query")
        or package_filters.get("package_query")
        or rule_template.get("title"),
        "package_terms": _strings(rule_template.get("package_terms"))
        or _strings(package_filters.get("package_terms")),
        "package_section_terms": _strings(rule_template.get("package_section_terms"))
        or _strings(package_filters.get("package_section_terms")),
        "applies_if_package_terms": _strings(rule_template.get("applies_if_package_terms")),
        "applies_if_package_term_groups": rule_template.get(
            "applies_if_package_term_groups",
            [],
        ),
        "does_not_apply_if_package_terms": _strings(
            rule_template.get("does_not_apply_if_package_terms")
        ),
        "source_query": rule_template.get("source_query") or rule_template.get("title"),
        "source_filters": source_filters,
        "supporting_source_record_ids": _strings(
            (candidate.get("dependency_contract") or {}).get("supporting_source_record_ids")
        ),
        "evidence_expectation": rule_template.get("evidence_expectation"),
    }


def _authority_family_ids_for_authority(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    decision: dict[str, Any],
) -> list[str]:
    family_ids: set[str] = set()
    for payload in (authority, candidate, decision):
        family_ids.update(_strings(payload.get("authority_family_ids")))
        family_ids.update(_strings([payload.get("authority_family_id")]))
        rule_template = payload.get("rule_template")
        if isinstance(rule_template, dict):
            family_ids.update(_strings(rule_template.get("authority_family_ids")))
            family_ids.update(_strings([rule_template.get("authority_family_id")]))
    return sorted(family_ids)


def _source_claim_link_requirements(candidate: dict[str, Any]) -> dict[str, Any]:
    required = (
        candidate.get("required_source_evidence")
        if isinstance(candidate.get("required_source_evidence"), dict)
        else {}
    )
    return {
        "required": bool(required.get("requires_source_claim_linkage")),
        "source_claim_link_ids": _strings(required.get("source_claim_link_ids"))
        or _strings(candidate.get("source_claim_link_ids")),
        "rule_claim_gap_ids": _strings(required.get("rule_claim_gap_ids"))
        or _strings(candidate.get("rule_claim_gap_ids")),
    }


def _generated_artifact_hashes(
    *,
    validation_hashes: dict[str, Any],
    authority_universe: dict[str, Any],
    paths: dict[str, Path],
    base_rule_pack_path: Path,
) -> dict[str, Any]:
    return {
        "base_rule_pack_sha256": _optional_file_sha256(base_rule_pack_path),
        "applicability_validation_sha256": _optional_file_sha256(
            paths["applicability_validation"]
        ),
        "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
        "applicable_authorities_sha256": _optional_file_sha256(
            paths["applicable_authorities"]
        ),
        "non_applicable_authorities_sha256": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "package_fact_graph_sha256": validation_hashes.get("package_fact_graph_sha256"),
        "selected_action_sha256": validation_hashes.get("selected_action_sha256"),
        "retrieval_trace_sha256": validation_hashes.get("retrieval_trace_sha256"),
        "graph_trace_sha256": validation_hashes.get("graph_trace_sha256"),
        "search_coverage_certificates_sha256": validation_hashes.get(
            "search_coverage_certificates_sha256"
        ),
        "package_manifest_sha256": validation_hashes.get("package_manifest_sha256"),
        "package_chunks_sha256": validation_hashes.get("package_chunks_sha256"),
        "catalog_sha256": validation_hashes.get("catalog_sha256"),
        "applicability_provenance_sha256": validation_hashes.get(
            "applicability_provenance_sha256"
        ),
    }
