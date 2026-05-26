from __future__ import annotations

from typing import Any

from .records import aliased_source_record_ids
from .v1_ea_eval_support import _chunk_text
from .v1_ea_eval_support import _evidence_text
from .v1_ea_eval_support import _expectation_terms
from .v1_ea_eval_support import _first_string
from .v1_ea_eval_support import _matched_terms
from .v1_ea_eval_support import _nested_get
from .v1_ea_eval_support import _normalize
from .v1_ea_eval_support import _strings


def _evaluate_sections(
    *,
    section_expectations: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for expectation in section_expectations:
        section_id = str(expectation["section_id"])
        terms = _expectation_terms(expectation)
        matches: list[dict[str, Any]] = []
        matched_terms: set[str] = set()
        for chunk in package_chunks:
            text = _chunk_text(chunk)
            chunk_terms = _matched_terms(text, terms)
            if not chunk_terms:
                continue
            matched_terms.update(chunk_terms)
            matches.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source_record_id": chunk.get("source_record_id"),
                    "title": chunk.get("title"),
                    "section": chunk.get("section"),
                    "heading": chunk.get("heading"),
                    "matched_terms": sorted(chunk_terms),
                }
            )
        detected = bool(matches)
        required = bool(expectation.get("required", True))
        results.append(
            {
                "section_id": section_id,
                "label": expectation.get("label", section_id),
                "required": required,
                "detected": detected,
                "passed": detected or not required,
                "matched_terms": sorted(matched_terms),
                "matched_chunk_count": len(matches),
                "matched_chunks": matches[:5],
                "failure_category": None
                if detected or not required
                else "ea_section_detection_miss",
            }
        )
    return results


def _evaluate_baseline_alignment(
    *,
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    require_source_record_match: bool,
    require_document_role_match: bool,
    expected_source_record_ids: list[str],
) -> list[dict[str, Any]]:
    if not require_source_record_match and not require_document_role_match:
        return []
    results = []
    baseline_ids = sorted(
        rule_id
        for rule_id, finding in finding_index.items()
        if finding.get("applicability_mode") == "baseline"
    )
    for rule_id in baseline_ids:
        finding = finding_index[rule_id]
        row = matrix_index.get(rule_id, {})
        expected_source_id = finding.get("authority_source_record_id") or row.get(
            "authority_source_record_id"
        )
        expected_role = finding.get("authority_document_role") or row.get(
            "authority_document_role"
        )
        actual_source_ids = _actual_source_record_ids(finding, row)
        actual_roles = _actual_document_roles(finding, row)
        source_passed = (
            True
            if not require_source_record_match
            else not expected_source_id
            or _expected_source_record_ids_match(
                [str(expected_source_id)],
                actual_source_ids,
            )
        )
        role_passed = (
            True
            if not require_document_role_match
            else not expected_role or expected_role in actual_roles
        )
        failure_categories: list[str] = []
        if not source_passed:
            failure_categories.append("baseline_source_record_mismatch")
        if not role_passed:
            failure_categories.append("baseline_document_role_mismatch")
        results.append(
            {
                "rule_id": rule_id,
                "expected_source_record_id": expected_source_id,
                "actual_source_record_ids": actual_source_ids,
                "source_record_match": source_passed,
                "expected_document_role": expected_role,
                "actual_document_roles": actual_roles,
                "document_role_match": role_passed,
                "passed": source_passed and role_passed,
                "failure_categories": failure_categories,
            }
        )
    if require_source_record_match:
        actual_authority_source_ids = {
            str(result["expected_source_record_id"])
            for result in results
            if result.get("expected_source_record_id")
        }
        for expected_source_id in sorted(str(value) for value in expected_source_record_ids):
            if expected_source_id in actual_authority_source_ids:
                continue
            results.append(
                {
                    "rule_id": None,
                    "expected_source_record_id": expected_source_id,
                    "actual_source_record_ids": [],
                    "source_record_match": False,
                    "expected_document_role": None,
                    "actual_document_roles": [],
                    "document_role_match": True,
                    "passed": False,
                    "failure_categories": ["baseline_source_record_missing"],
                }
            )
    return results


def _evaluate_rule_expectations(
    *,
    rule_expectations: list[dict[str, Any]],
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    applicability_decision_index: dict[str, dict[str, Any]],
    bridge_index: dict[str, dict[str, Any]],
    section_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for expectation in rule_expectations:
        rule_id = str(expectation["rule_id"])
        decision = applicability_decision_index.get(rule_id)
        bridge = bridge_index.get(rule_id)
        finding = finding_index.get(rule_id) or bridge or _decision_surrogate(decision)
        row = matrix_index.get(rule_id) or bridge or _decision_surrogate(decision)
        finding, row = _augment_with_decision_evidence(finding, row, decision)
        results.append(
            _evaluate_rule_source_section(
                expectation=expectation,
                finding=finding,
                row=row,
                section_results=section_results,
            )
        )
    return results


def _evaluate_rule_source_section(
    *,
    expectation: dict[str, Any],
    finding: dict[str, Any] | None,
    row: dict[str, Any] | None,
    section_results: list[dict[str, Any]],
) -> dict[str, Any]:
    rule_id = str(expectation["rule_id"])
    failure_categories: list[str] = []
    if not finding and not row:
        return {
            "rule_id": rule_id,
            "present": False,
            "actual_status": None,
            "actual_applicability": None,
            "expected_package_section_ids": expectation.get("expected_package_section_ids", []),
            "actual_package_section_ids": [],
            "section_match": False,
            "expected_source_record_ids": expectation.get("expected_source_record_ids", []),
            "actual_source_record_ids": [],
            "source_record_match": False,
            "expected_source_document_roles": expectation.get(
                "expected_source_document_roles",
                [],
            ),
            "actual_source_document_roles": [],
            "source_document_role_match": False,
            "citation_requirements_met": False,
            "passed": False,
            "failure_categories": ["rule_missing"],
        }
    finding = finding or {}
    row = row or {}
    expected_sections = sorted(
        str(value) for value in expectation.get("expected_package_section_ids", [])
    )
    actual_sections = _actual_package_section_ids(finding, row, section_results)
    section_match_mode = expectation.get("section_match", "all")
    if expected_sections:
        if section_match_mode == "any":
            section_match = bool(set(expected_sections) & set(actual_sections))
        else:
            section_match = set(expected_sections).issubset(actual_sections)
    else:
        section_match = True
    if not section_match:
        failure_categories.append("rule_section_mismatch")

    expected_sources = sorted(
        str(value) for value in expectation.get("expected_source_record_ids", [])
    )
    actual_sources = _actual_source_record_ids(finding, row)
    source_match = _expected_source_record_ids_match(expected_sources, actual_sources)
    if not source_match:
        failure_categories.append("source_record_mismatch")

    expected_roles = sorted(
        str(value) for value in expectation.get("expected_source_document_roles", [])
    )
    actual_roles = _actual_document_roles(finding, row)
    role_match = not expected_roles or set(expected_roles).issubset(actual_roles)
    if not role_match:
        failure_categories.append("source_document_role_mismatch")

    citation_requirements_met = _citation_requirements_met(finding, row)
    if expectation.get("require_citations", True) and not citation_requirements_met:
        failure_categories.append("citation_requirement_miss")
    return {
        "rule_id": rule_id,
        "present": True,
        "actual_status": _actual_status(finding, row),
        "actual_applicability": _actual_applicability(finding, row),
        "expected_package_section_ids": expected_sections,
        "actual_package_section_ids": actual_sections,
        "section_match": section_match,
        "expected_source_record_ids": expected_sources,
        "actual_source_record_ids": actual_sources,
        "source_record_match": source_match,
        "expected_source_document_roles": expected_roles,
        "actual_source_document_roles": actual_roles,
        "source_document_role_match": role_match,
        "citation_requirements_met": citation_requirements_met,
        "passed": not failure_categories,
        "failure_categories": failure_categories,
    }


def _applicability_decisions_by_rule(
    decisions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        rule_id = _decision_rule_id(decision)
        if rule_id and rule_id not in indexed:
            indexed[rule_id] = decision
    return indexed


def _decision_rule_id(decision: dict[str, Any]) -> str | None:
    rule_template = decision.get("rule_template")
    if isinstance(rule_template, dict):
        for key in ("rule_id", "id"):
            value = str(rule_template.get(key) or "").strip()
            if value:
                return value
    candidate_id = str(decision.get("candidate_authority_id") or "").strip()
    if candidate_id.startswith("rule-template:"):
        parts = candidate_id.split(":")
        if len(parts) >= 4 and parts[-1]:
            return parts[-1]
    return None


def _decision_surrogate(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(decision, dict):
        return None
    rule_id = _decision_rule_id(decision)
    if not rule_id:
        return None
    status = str(decision.get("status") or "").strip()
    if status == "applicable":
        review_status = "pass"
        applicability_status = "applicable"
    elif status == "not_applicable":
        review_status = "not_applicable"
        applicability_status = "not_applicable"
    elif status in {"needs_adjudication", "unresolved"}:
        review_status = "needs_reviewer_resolution"
        applicability_status = "needs_reviewer_resolution"
    else:
        review_status = None
        applicability_status = None
    source_ids = _strings(decision.get("source_record_ids"))
    document_role = str(decision.get("authority_document_role") or "").strip() or None
    package_evidence = _decision_package_evidence(decision)
    source_evidence = _decision_source_evidence(decision, document_role)
    return {
        "rule_id": rule_id,
        "status": review_status,
        "applicability_status": applicability_status,
        "applicability_mode": "conditional",
        "authority_source_record_id": source_ids[0] if source_ids else None,
        "authority_document_role": document_role,
        "package_evidence": package_evidence,
        "applicability_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "source_evidence": source_evidence,
        "applied_source_record_ids": source_ids,
        "applied_source_document_roles": [document_role] if document_role else [],
        "citation_requirements_met": bool(
            applicability_status == "not_applicable" or (package_evidence and source_evidence)
        ),
    }


def _augment_with_decision_evidence(
    finding: dict[str, Any] | None,
    row: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    surrogate = _decision_surrogate(decision)
    if not surrogate:
        return finding, row
    package_evidence = surrogate.get("package_evidence")
    source_evidence = surrogate.get("source_library_evidence")
    applied_source_record_ids = _strings(surrogate.get("applied_source_record_ids"))
    applied_source_document_roles = _strings(surrogate.get("applied_source_document_roles"))
    if not package_evidence and not source_evidence:
        return finding, row
    if isinstance(finding, dict):
        finding = dict(finding)
        if package_evidence:
            finding["applicability_decision_evidence"] = package_evidence
        if source_evidence:
            finding["applicability_decision_source_evidence"] = source_evidence
        if applied_source_record_ids:
            finding["applied_source_record_ids"] = sorted(
                {
                    *(_strings(finding.get("applied_source_record_ids"))),
                    *applied_source_record_ids,
                }
            )
        if applied_source_document_roles:
            finding["applied_source_document_roles"] = sorted(
                {
                    *(_strings(finding.get("applied_source_document_roles"))),
                    *applied_source_document_roles,
                }
            )
    if isinstance(row, dict):
        row = dict(row)
        if package_evidence:
            row["applicability_decision_evidence"] = package_evidence
        if source_evidence:
            row["applicability_decision_source_evidence"] = source_evidence
        if applied_source_record_ids:
            row["applied_source_record_ids"] = sorted(
                {
                    *(_strings(row.get("applied_source_record_ids"))),
                    *applied_source_record_ids,
                }
            )
        if applied_source_document_roles:
            row["applied_source_document_roles"] = sorted(
                {
                    *(_strings(row.get("applied_source_document_roles"))),
                    *applied_source_document_roles,
                }
            )
    return finding, row


def _decision_package_evidence(decision: dict[str, Any]) -> dict[str, Any] | None:
    spans = decision.get("package_evidence_spans") or decision.get("negative_evidence_spans") or []
    span = next((item for item in spans if isinstance(item, dict)), None)
    if not span:
        return None
    text = str(span.get("text_snippet") or span.get("text_excerpt") or "").strip()
    section = span.get("section_family")
    return {
        "citation_label": span.get("citation_label"),
        "title": span.get("title"),
        "chunk_id": _first_string(span.get("package_chunk_ids")),
        "text": text,
        "section": section,
        "heading": span.get("heading"),
        "evidence_span": {"text": text},
        "provenance": {
            "section": section,
            "heading": span.get("heading"),
            "page": span.get("page_label"),
        },
    }


def _decision_source_evidence(
    decision: dict[str, Any],
    document_role: str | None,
) -> dict[str, Any] | None:
    spans = decision.get("source_library_evidence_spans") or []
    span = next((item for item in spans if isinstance(item, dict)), None)
    source_ids = _strings(decision.get("source_record_ids"))
    if not span and not source_ids:
        return None
    text = str((span or {}).get("text_excerpt") or "").strip()
    source_record_id = (span or {}).get("source_record_id") or (
        source_ids[0] if source_ids else None
    )
    return {
        "citation_label": (span or {}).get("citation_label"),
        "source_record_id": source_record_id,
        "document_role": document_role,
        "title": (span or {}).get("title") or source_record_id,
        "text": text,
        "evidence_span": {"text": text},
        "provenance": {"page": (span or {}).get("page_label")},
    }


def _actual_package_section_ids(
    finding: dict[str, Any],
    row: dict[str, Any],
    section_results: list[dict[str, Any]],
) -> list[str]:
    section_defs = [
        {
            "section_id": result["section_id"],
            "terms": sorted(
                set(result.get("matched_terms", []))
                | {str(result["label"]), str(result["section_id"]).replace("_", " ")}
            ),
        }
        for result in section_results
    ]
    texts = [
        _evidence_text(finding.get("package_evidence")),
        _evidence_text(finding.get("applicability_evidence")),
        _evidence_text(finding.get("applicability_decision_evidence")),
        _evidence_text(row.get("ea_package_evidence")),
        _evidence_text(row.get("applicability_decision_evidence")),
        _evidence_text(_nested_get(row, ["applicability_basis", "applicability_evidence"])),
    ]
    matches = set()
    for text in texts:
        if not text:
            continue
        normalized = _normalize(text)
        for section_def in section_defs:
            terms = [term for term in section_def["terms"] if term]
            if _matched_terms(normalized, terms):
                matches.add(section_def["section_id"])
    return sorted(matches)


def _actual_source_record_ids(finding: dict[str, Any], row: dict[str, Any]) -> list[str]:
    values = set(str(value) for value in row.get("applied_source_record_ids", []) if value)
    values.update(str(value) for value in finding.get("applied_source_record_ids", []) if value)
    for key in (
        "source_library_evidence",
        "source_evidence",
        "applicability_decision_source_evidence",
    ):
        evidence = finding.get(key) or row.get(key) or {}
        if evidence.get("source_record_id"):
            values.add(str(evidence["source_record_id"]))
    for key in ("source_claim_links", "source_claims"):
        for link in finding.get(key, []) or []:
            if link.get("source_record_id"):
                values.add(str(link["source_record_id"]))
    compact = row.get("source_library_evidence") or {}
    if compact.get("source_record_id"):
        values.add(str(compact["source_record_id"]))
    return sorted(values)


def _expected_source_record_ids_match(
    expected_source_ids: list[str],
    actual_source_ids: list[str],
) -> bool:
    if not expected_source_ids:
        return True
    if not actual_source_ids:
        return False
    actual_aliases = set(aliased_source_record_ids(actual_source_ids))
    return all(str(expected_source_id) in actual_aliases for expected_source_id in expected_source_ids)


def _actual_document_roles(finding: dict[str, Any], row: dict[str, Any]) -> list[str]:
    values = set(str(value) for value in row.get("applied_source_document_roles", []) if value)
    values.update(
        str(value) for value in finding.get("applied_source_document_roles", []) if value
    )
    for key in (
        "source_library_evidence",
        "source_evidence",
        "applicability_decision_source_evidence",
    ):
        evidence = finding.get(key) or row.get(key) or {}
        if evidence.get("document_role"):
            values.add(str(evidence["document_role"]))
    for key in ("source_claim_links", "source_claims"):
        for link in finding.get(key, []) or []:
            if link.get("document_role"):
                values.add(str(link["document_role"]))
    return sorted(values)


def _citation_requirements_met(finding: dict[str, Any], row: dict[str, Any]) -> bool:
    if row.get("citation_requirements_met") is not None:
        return bool(row["citation_requirements_met"])
    return bool(
        finding.get("package_evidence_citation")
        and finding.get("source_library_evidence_citation")
    )


def _actual_status(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> str | None:
    return (finding or {}).get("status") or (row or {}).get("status")


def _actual_applicability(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> str | None:
    explicit = (finding or {}).get("applicability_status") or (row or {}).get(
        "applicability_status"
    )
    if explicit:
        return str(explicit)
    status = _actual_status(finding, row)
    if not status:
        return None
    return "not_applicable" if status == "not_applicable" else "applicable"


def _is_actual_applicable(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> bool:
    status = _actual_status(finding, row)
    applicability = _actual_applicability(finding, row)
    if status is None and applicability is None:
        return False
    return status != "not_applicable" and applicability not in {
        "not_applicable",
        "needs_reviewer_resolution",
    }
