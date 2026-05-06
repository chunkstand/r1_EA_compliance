from __future__ import annotations

from pathlib import Path

from .compliance_inputs import first_present
from .compliance_inputs import read_json
from .compliance_inputs import strings


DEFAULT_AUTHORITY_FAMILY_INVENTORY_PATH = Path(
    "config/authority_universe_families_nepa_ea_v1.json"
)


def authority_family_index(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    payload = read_json(path)
    index: dict[str, set[str]] = {}
    for family in payload.get("authority_families") or []:
        if not isinstance(family, dict):
            continue
        family_id = str(family.get("family_id") or "").strip()
        if not family_id:
            continue
        for rule_id in strings(family.get("rule_ids")):
            index.setdefault(rule_id, set()).add(family_id)
        for rule_id in strings(family.get("rule_template_ids")):
            index.setdefault(rule_id, set()).add(family_id)
        coverage = family.get("coverage_requirements")
        if isinstance(coverage, dict):
            for rule_id in strings(coverage.get("authority_family_rule_template_ids")):
                index.setdefault(rule_id, set()).add(family_id)
            for rule_id in strings(coverage.get("coverage_matrix_rule_ids")):
                index.setdefault(rule_id, set()).add(family_id)
    return {rule_id: sorted(family_ids) for rule_id, family_ids in index.items()}


def compliance_finding(
    *,
    rule_pack: dict,
    rule: dict,
    finding: dict,
    source_claim_links: list[dict],
    authority_family_index: dict[str, list[str]],
) -> dict:
    status = str(finding["status"])
    package_evidence = finding.get("package_evidence")
    source_evidence = finding.get("source_library_evidence")
    if status == "not_applicable":
        package_evidence = None
        source_evidence = None
        source_claim_links = []
    source_claim_evidence = [_source_claim_evidence(link) for link in source_claim_links]
    source_filters = finding.get("source_filters", {})
    authority_source_record_id = str(
        rule.get("authority_source_record_id")
        or (source_filters or {}).get("source_record_id")
        or ""
    ).strip()
    authority_document_role = str(
        rule.get("authority_document_role") or (source_filters or {}).get("document_role") or ""
    ).strip()
    applicability = rule.get("applicability") if isinstance(rule.get("applicability"), dict) else {}
    authority_family_ids = _authority_family_ids_for_rule(
        rule=rule,
        applicability=applicability,
        authority_family_index=authority_family_index,
    )
    candidate_authority_id = first_present(
        rule.get("candidate_authority_id"),
        applicability.get("candidate_authority_id"),
    )
    applicability_decision_id = first_present(
        rule.get("applicability_decision_id"),
        applicability.get("decision_id"),
    )
    return {
        "id": finding["id"],
        "rule_id": rule["id"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "authority_category": rule.get("authority_category"),
        "authority_source_record_id": authority_source_record_id or None,
        "authority_document_role": authority_document_role or None,
        "candidate_authority_id": candidate_authority_id,
        "candidate_authority_type": applicability.get("candidate_authority_type"),
        "applicability_decision_id": applicability_decision_id,
        "authority_family_ids": authority_family_ids,
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "applicability_basis_type": applicability.get("basis_type"),
        "generated_from_applicability": bool(rule.get("generated_from_applicability")),
        "search_coverage_certificate_ids": strings(
            applicability.get("search_coverage_certificate_ids")
        ),
        "human_adjudication_refs": applicability.get("human_adjudication_refs") or [],
        "applicability_mode": rule.get("applicability_mode")
        or finding.get("applicability_mode"),
        "pre_review_applicability_mode": rule.get("pre_review_applicability_mode"),
        "pre_review_applicability": rule.get("pre_review_applicability"),
        "applies_if_package_terms": rule.get("applies_if_package_terms", []),
        "applies_if_package_term_groups": rule.get("applies_if_package_term_groups", []),
        "does_not_apply_if_package_terms": rule.get("does_not_apply_if_package_terms", []),
        "title": rule["title"],
        "question": rule.get("question") or rule["title"],
        "requirement": rule.get("requirement"),
        "severity": rule.get("severity", finding.get("severity", "medium")),
        "status": status,
        "claim_type": claim_type(status),
        "confidence": finding.get("confidence"),
        "rationale": finding.get("rationale"),
        "applicability_status": finding.get("applicability_status"),
        "applicability_terms": finding.get("applicability_terms", []),
        "applicability_term_groups": finding.get("applicability_term_groups", []),
        "applicability_negative_terms": finding.get("applicability_negative_terms", []),
        "applicability_rationale": finding.get("applicability_rationale"),
        "applicability_evidence": finding.get("applicability_evidence"),
        "applicability_negative_evidence": finding.get("applicability_negative_evidence"),
        "package_query": finding.get("package_query"),
        "package_terms": finding.get("package_terms", []),
        "source_query": finding.get("source_query"),
        "source_filters": source_filters,
        "package_evidence_status": finding.get("package_evidence_status"),
        "source_library_evidence_status": finding.get("source_library_evidence_status"),
        "package_evidence_citation": _citation_label(package_evidence),
        "source_library_evidence_citation": _citation_label(source_evidence),
        "source_claim_link_count": len(source_claim_evidence),
        "source_claim_ids": [link["claim_id"] for link in source_claim_evidence],
        "source_claim_evidence_citations": [
            link["citation_label"] for link in source_claim_evidence if link.get("citation_label")
        ],
        "source_claim_links": source_claim_evidence,
        "package_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "package_results": finding.get("package_results", []),
        "source_library_results": finding.get("source_library_results", []),
        "limitations": finding.get("limitations", []),
        "evidence_expectation": rule.get("evidence_expectation"),
    }


def claim_type(status: str) -> str:
    if status == "pass":
        return "supported_compliance_finding"
    if status == "gap":
        return "package_evidence_gap"
    return "no_compliance_claim"


def _authority_family_ids_for_rule(
    *,
    rule: dict,
    applicability: dict,
    authority_family_index: dict[str, list[str]],
) -> list[str]:
    family_ids = set(strings(rule.get("authority_family_ids")))
    family_ids.update(strings([rule.get("authority_family_id")]))
    family_ids.update(strings(applicability.get("authority_family_ids")))
    family_ids.update(strings([applicability.get("authority_family_id")]))
    basis = applicability.get("applicability_basis")
    if isinstance(basis, dict):
        family_ids.update(strings(basis.get("authority_family_ids")))
        family_ids.update(strings([basis.get("authority_family_id")]))
    candidate_rule_ids = [
        rule.get("id"),
        rule.get("base_rule_id"),
        rule.get("generated_rule_id"),
    ]
    rule_template = applicability.get("rule_template")
    if isinstance(rule_template, dict):
        candidate_rule_ids.extend(
            [
                rule_template.get("rule_id"),
                rule_template.get("template_id"),
                rule_template.get("source_base_rule_id"),
            ]
        )
    for rule_id in strings(candidate_rule_ids):
        family_ids.update(authority_family_index.get(rule_id, []))
    return sorted(family_ids)


def _source_claim_evidence(link: dict) -> dict:
    return {
        "link_id": link["link_id"],
        "rule_id": link["rule_id"],
        "claim_id": link["claim_id"],
        "claim_type": link["claim_type"],
        "claim_text": link["claim_text"],
        "rank": link["rank"],
        "score": link["score"],
        "matched_terms": link.get("matched_terms", []),
        "source_record_id": link["source_record_id"],
        "chunk_id": link["chunk_id"],
        "citation_label": link["citation_label"],
        "authority_level": link["authority_level"],
        "document_role": link["document_role"],
        "review_topics": link.get("review_topics", []),
        "artifact_sha256": link["artifact_sha256"],
        "artifact_path": link["artifact_path"],
        "parser_name": link["parser_name"],
        "parser_version": link["parser_version"],
        "source_text_path": link.get("source_text_path"),
        "source_char_start": link["source_char_start"],
        "source_char_end": link["source_char_end"],
        "chunk_char_start": link["chunk_char_start"],
        "chunk_char_end": link["chunk_char_end"],
        "content_sha256": link["content_sha256"],
        "validation_status": link["validation_status"],
    }


def _citation_label(evidence: dict | None) -> str | None:
    if not evidence:
        return None
    value = evidence.get("citation_label")
    return str(value) if value else None
