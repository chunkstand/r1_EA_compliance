from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import textwrap

from .rule_packs import _baseline_source_record_ids


COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"
FOREST_PLAN_COMPLIANCE_SCHEMA_VERSION = "forest-plan-compliance-matrix-v0"
CLAIM_STATUSES = {"pass", "gap"}
VALID_FINDING_STATUSES = {"pass", "gap", "uncertain", "not_applicable"}


def build_compliance_matrix(
    *,
    review_id: str,
    package_path: Path,
    rule_pack: dict,
    findings: list[dict],
    summary: dict,
    validation: dict,
    applicability_gate: dict,
) -> dict:
    rows = [_matrix_row(review_id, finding) for finding in findings]
    forest_plan_compliance = _forest_plan_compliance_section(
        review_id=review_id,
        forest_plan_review=summary.get("forest_plan_review"),
    )
    status_counts = dict(Counter(row["status"] for row in rows))
    applicability_counts = dict(Counter(row["applicability_status"] for row in rows))
    matrix = {
        "schema_version": COMPLIANCE_MATRIX_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "package_path": str(package_path),
        "source_set_id": summary.get("source_set_id"),
        "rule_pack": _rule_pack_summary(rule_pack),
        "summary": {
            "row_count": len(rows),
            "status_counts": status_counts,
            "applicability_counts": applicability_counts,
            "applicable_row_count": sum(
                1 for row in rows if row["applicability_status"] == "applicable"
            ),
            "not_applicable_row_count": sum(
                1 for row in rows if row["applicability_status"] == "not_applicable"
            ),
            "applicable_source_record_ids": summary.get("authority_identification", {}).get(
                "applicable_source_record_ids",
                [],
            ),
            "claim_row_count": sum(1 for row in rows if row["status"] in CLAIM_STATUSES),
            "validated": bool(validation.get("passed")),
            "reviewer_ready": bool(summary.get("reviewer_ready")),
            "compliance_review_path": summary.get("compliance_review_path"),
            "compliance_validation_path": summary.get("compliance_validation_path"),
            "compliance_matrix_pdf_path": summary.get("compliance_matrix_pdf_path"),
            "authority_provenance_path": summary.get("authority_provenance_path"),
            "non_applicable_authority_appendix_path": summary.get(
                "non_applicable_authority_appendix_path"
            ),
            "non_applicable_authority_appendix_markdown_path": summary.get(
                "non_applicable_authority_appendix_markdown_path"
            ),
            "reviewer_resolution_report_path": summary.get(
                "reviewer_resolution_report_path"
            ),
            "litigation_risk_summary_path": summary.get("litigation_risk_summary_path"),
            "finding_graph_nodes_path": summary.get("finding_nodes_path"),
            "finding_graph_edges_path": summary.get("finding_edges_path"),
            "forest_plan_review": summary.get("forest_plan_review"),
            "forest_plan_compliance_row_count": _section_row_count(
                forest_plan_compliance,
            ),
            "forest_plan_compliance_status_counts": _section_summary_value(
                forest_plan_compliance,
                "compliance_status_counts",
                {},
            ),
            "forest_plan_compliance_applicable_standard_row_count": (
                _section_summary_value(
                    forest_plan_compliance,
                    "applicable_standard_row_count",
                    0,
                )
            ),
            "applicability_gate": summary.get("applicability_gate"),
            "authority_integration": summary.get("authority_integration"),
            "non_applicable_authorities_path": applicability_gate.get(
                "non_applicable_authorities_path"
            ),
            "non_applicable_authority_count": applicability_gate.get(
                "non_applicable_authority_count",
            ),
            "search_coverage_certificates_path": applicability_gate.get(
                "search_coverage_certificates_path"
            ),
        },
        "columns": [
            "rule_id",
            "rule_title",
            "authority_category",
            "authority_source_record_id",
            "authority_family_ids",
            "candidate_authority_id",
            "applicability_decision_id",
            "candidate_authority_type",
            "status",
            "applicability_status",
            "applicability_mode",
            "search_coverage_certificate_ids",
            "human_adjudication_refs",
            "requirement",
            "ea_package_citation",
            "source_library_citation",
            "source_claim_ids",
            "applied_source_record_ids",
            "limitations",
        ],
        "rows": rows,
    }
    if forest_plan_compliance is not None:
        matrix["forest_plan_compliance"] = forest_plan_compliance
    return matrix


def matrix_markdown(matrix: dict) -> str:
    summary = matrix["summary"]
    lines = [
        "# Compliance Matrix",
        "",
        (
            "This matrix is deterministic decision support from audited review artifacts. "
            "It is not legal advice, legal sufficiency certification, or a final agency decision."
        ),
        "",
        f"- Review ID: `{matrix['review_id']}`",
        f"- Source set: `{matrix.get('source_set_id')}`",
        f"- Rule pack: `{matrix['rule_pack']['rule_pack_id']}` "
        f"`{matrix['rule_pack']['version']}`",
        (
            f"- Authority findings: `{summary['row_count']} rows; "
            f"{_count_phrase(summary['status_counts'])}`"
        ),
        f"- Applicability: `{_count_phrase(summary.get('applicability_counts', {}))}`",
        f"- Review gates: `{_review_gate_phrase(summary)}`",
    ]
    if summary.get("non_applicable_authorities_path"):
        lines.append(
            "- Non-applicable authorities source: "
            f"`{summary.get('non_applicable_authorities_path')}` "
            f"(`{summary.get('non_applicable_authority_count', 0)}` authorities)"
        )
    forest_plan_review = summary.get("forest_plan_review") or {}
    if forest_plan_review:
        lines.append(
            f"- Forest-plan review: `{forest_plan_review.get('scope_status')}` "
            f"({_yes_no_sentence(forest_plan_review.get('reviewer_ready'), 'reviewer ready')})"
        )
    lines.extend(_supervisor_readout_markdown_lines(matrix))
    lines.extend(_accuracy_audit_markdown_lines(matrix))
    lines.extend(
        [
            "",
            "## NEPA / Authority Compliance",
            "",
            (
                "| Review topic | Signer question | Decision support | EA record support | "
                "Authority basis | Trace / caveats |"
            ),
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in matrix["rows"]:
        ea_evidence = row.get("ea_package_evidence") or {}
        source_evidence = row.get("source_library_evidence") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(_nepa_topic_cell(row)),
                    _md_cell(_nepa_signer_question_cell(row)),
                    _md_cell(_nepa_decision_support_cell(row)),
                    _md_cell(_evidence_support_cell(row.get("ea_package_citation"), ea_evidence)),
                    _md_cell(_authority_basis_cell(row, source_evidence)),
                    _md_cell(_trace_caveats_cell(row)),
                ]
            )
            + " |"
        )
    forest_plan_compliance = matrix.get("forest_plan_compliance")
    if forest_plan_compliance:
        lines.extend(_forest_plan_compliance_markdown_lines(forest_plan_compliance))
    return "\n".join(lines) + "\n"


def write_compliance_matrix_pdf(path: Path, matrix: dict) -> None:
    pages = _matrix_pdf_pages(matrix)
    _write_simple_pdf(path, pages, title="Compliance Matrix")


def _matrix_row(review_id: str, finding: dict) -> dict:
    source_claim_ids = [str(value) for value in finding.get("source_claim_ids", [])]
    source_claim_citations = [
        str(value) for value in finding.get("source_claim_evidence_citations", []) if value
    ]
    applied_source_record_ids = finding_source_record_ids(finding)
    applied_source_document_roles = finding_source_document_roles(finding)
    citation_requirements_met = _finding_has_required_eval_citations(finding)
    return {
        "row_id": f"matrix:{review_id}:{finding['rule_id']}",
        "rule_id": finding["rule_id"],
        "rule_title": finding["title"],
        "authority_category": finding.get("authority_category"),
        "authority_source_record_id": finding.get("authority_source_record_id"),
        "authority_document_role": finding.get("authority_document_role"),
        "authority_family_ids": _strings(finding.get("authority_family_ids")),
        "authority_family_id": finding.get("authority_family_id"),
        "candidate_authority_id": finding.get("candidate_authority_id"),
        "candidate_authority_type": finding.get("candidate_authority_type"),
        "applicability_decision_id": finding.get("applicability_decision_id"),
        "search_coverage_certificate_ids": _strings(
            finding.get("search_coverage_certificate_ids")
        ),
        "human_adjudication_refs": finding.get("human_adjudication_refs") or [],
        "question": finding.get("question"),
        "requirement": finding.get("requirement"),
        "severity": finding.get("severity"),
        "status": finding["status"],
        "claim_type": finding["claim_type"],
        "confidence": finding.get("confidence"),
        "rationale": finding.get("rationale"),
        "applicability_status": finding.get("applicability_status")
        or ("not_applicable" if finding["status"] == "not_applicable" else "applicable"),
        "applicability_mode": finding.get("applicability_mode"),
        "applicability_basis": {
            "rationale": finding.get("applicability_rationale"),
            "mode": finding.get("applicability_mode"),
            "applies_if_package_terms": finding.get("applies_if_package_terms", []),
            "applies_if_package_term_groups": finding.get(
                "applies_if_package_term_groups",
                [],
            ),
            "does_not_apply_if_package_terms": finding.get(
                "does_not_apply_if_package_terms",
                [],
            ),
            "matched_terms": finding.get("applicability_terms", []),
            "applicability_evidence": _compact_evidence(finding.get("applicability_evidence")),
            "applicability_negative_terms": finding.get("applicability_negative_terms", []),
            "applicability_negative_evidence": _compact_evidence(
                finding.get("applicability_negative_evidence")
            ),
            "source_filters": finding.get("source_filters", {}),
            "package_terms": finding.get("package_terms", []),
            "source_query": finding.get("source_query"),
            "applied_source_record_ids": applied_source_record_ids,
            "applied_source_document_roles": applied_source_document_roles,
            "candidate_authority_id": finding.get("candidate_authority_id"),
            "applicability_decision_id": finding.get("applicability_decision_id"),
            "authority_family_ids": _strings(finding.get("authority_family_ids")),
            "basis_type": finding.get("applicability_basis_type"),
        },
        "package_query": finding.get("package_query"),
        "source_query": finding.get("source_query"),
        "ea_package_citation": finding.get("package_evidence_citation"),
        "ea_package_evidence": _compact_evidence(finding.get("package_evidence")),
        "source_library_citation": finding.get("source_library_evidence_citation"),
        "source_library_evidence": _compact_evidence(finding.get("source_library_evidence")),
        "source_claim_ids": source_claim_ids,
        "source_claim_citations": sorted(set(source_claim_citations)),
        "source_claim_count": len(source_claim_ids),
        "applied_source_record_ids": applied_source_record_ids,
        "applied_source_document_roles": applied_source_document_roles,
        "citation_requirements_met": citation_requirements_met,
        "limitation_count": len(finding.get("limitations", [])),
        "limitations": finding.get("limitations", []),
        "failure_category": _matrix_failure_category(finding),
    }


def _supervisor_readout_markdown_lines(matrix: dict) -> list[str]:
    lines = [
        "",
        "## Forest Supervisor Readout",
        "",
        "| Signing question | Current decision-support signal |",
        "| --- | --- |",
    ]
    for row in _supervisor_readout_rows(matrix):
        lines.append(f"| {_md_cell(row['check'])} | {_md_cell(row['signal'])} |")
    return lines


def _supervisor_readout_rows(matrix: dict) -> list[dict[str, str]]:
    summary = matrix.get("summary") or {}
    forest_plan = matrix.get("forest_plan_compliance") or {}
    forest_summary = forest_plan.get("summary") or {}
    rows = [
        {
            "check": "Is the compliance record ready for signing review?",
            "signal": _authority_readiness_signal(summary),
        },
        {
            "check": "Are inapplicable authorities traceable rather than ignored?",
            "signal": (
                f"{summary.get('non_applicable_authority_count', 0)} authorities are "
                f"tracked in {summary.get('non_applicable_authorities_path') or 'N/A'}."
            ),
        },
    ]
    if forest_plan:
        rows.append(
            {
                "check": "Is Custer Gallatin Forest Plan consistency visible?",
                "signal": _forest_plan_readiness_signal(forest_summary),
            }
        )
    rows.append(
        {
            "check": "How should a signer use the row tables below?",
            "signal": (
                "Read any Needs review row before signing. For Pass rows, confirm the cited EA "
                "record support, authority basis, and trace/caveat cell match the decision record."
            ),
        }
    )
    return rows


def _nepa_topic_cell(row: dict) -> str:
    return "<br>".join(
        [
            _human_rule_title(row),
            f"rule: {row.get('rule_id') or 'unknown'}",
            (
                f"{_display_value(row.get('authority_category'))}: "
                f"{row.get('authority_source_record_id') or 'none'}"
            ),
        ]
    )


def _nepa_signer_question_cell(row: dict) -> str:
    question = str(row.get("question") or "No signer question recorded.")
    requirement = str(row.get("requirement") or "No record requirement recorded.")
    return "<br>".join(
        [
            _truncate(question, 190),
            f"Record need: {_truncate(requirement, 210)}",
        ]
    )


def _nepa_decision_support_cell(row: dict) -> str:
    basis = row.get("applicability_basis") or {}
    rationale = row.get("rationale") or basis.get("rationale") or ""
    parts = [
        f"Finding: {_display_value(row.get('status'))}",
        (
            f"Applies: {_display_value(row.get('applicability_status'))} "
            f"({_display_value(row.get('applicability_mode'))})"
        ),
        f"Severity: {_display_value(row.get('severity'))}; confidence: {row.get('confidence')}",
    ]
    if rationale:
        parts.append(_truncate(str(rationale), 190))
    return "<br>".join(parts)


def _evidence_support_cell(citation: str | None, evidence: dict) -> str:
    if not citation:
        return "No EA citation recorded."
    parts = [
        citation,
        _truncate(str(evidence.get("title") or "Untitled EA record"), 100),
    ]
    excerpt = _evidence_excerpt(evidence, 230)
    if excerpt:
        parts.append(f"Record says: {excerpt}")
    return "<br>".join(parts)


def _authority_basis_cell(row: dict, evidence: dict) -> str:
    family_ids = ", ".join(row.get("authority_family_ids") or []) or "none"
    citation = row.get("source_library_citation") or "No source citation recorded."
    parts = [
        str(citation),
        _truncate(str(evidence.get("title") or "Untitled authority source"), 100),
        f"Requirement: {_truncate(str(row.get('requirement') or 'Not recorded.'), 210)}",
    ]
    excerpt = _evidence_excerpt(evidence, 180)
    if excerpt:
        parts.append(f"Authority text: {excerpt}")
    parts.append(f"Family: {_truncate(family_ids, 100)}")
    return "<br>".join(parts)


def _trace_caveats_cell(row: dict) -> str:
    claim_count = int(row.get("source_claim_count") or len(row.get("source_claim_ids", [])))
    citation_status = (
        "citation gate complete"
        if row.get("citation_requirements_met")
        else "citation gate needs review"
    )
    parts = [
        f"{claim_count} source claim{'s' if claim_count != 1 else ''}",
        citation_status,
    ]
    source_claims = row.get("source_claim_ids") or []
    if source_claims:
        parts.append("claims: " + _truncate(", ".join(str(value) for value in source_claims), 120))
    limitations = row.get("limitations") or []
    if limitations:
        parts.append("limitations: " + _truncate("; ".join(str(item) for item in limitations), 160))
    elif row.get("failure_category"):
        parts.append("caveat: " + _display_value(row.get("failure_category")))
    else:
        parts.append("limitations: none recorded")
    return "<br>".join(parts)


def _human_rule_title(row: dict) -> str:
    title = str(row.get("rule_title") or "Untitled authority")
    suffixes = [
        " is reviewed",
        " is addressed",
        " is supported",
        " are addressed",
        " are met",
        " applies",
    ]
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
            break
    return _truncate(title, 115)


def _forest_plan_compliance_section(
    *,
    review_id: str,
    forest_plan_review: dict | None,
) -> dict | None:
    if not forest_plan_review:
        return None
    component_findings_path = _optional_path(
        forest_plan_review.get("component_findings_path"),
    )
    standard_coverage_path = _optional_path(
        forest_plan_review.get("applicable_standard_coverage_path"),
    )
    load_errors: list[str] = []
    component_findings = _read_json_if_exists(component_findings_path, load_errors)
    standard_coverage = _read_json_if_exists(standard_coverage_path, load_errors)
    coverage_by_component_id = _standard_coverage_by_component_id(standard_coverage)
    rows = _forest_plan_compliance_rows(
        review_id=review_id,
        component_findings=component_findings,
        coverage_by_component_id=coverage_by_component_id,
    )
    compliance_status_counts = dict(
        Counter(row["compliance_status"] for row in rows)
    )
    applicability_counts = dict(
        Counter(row["applicability_status"] for row in rows)
    )
    component_type_counts = dict(Counter(row["component_type"] for row in rows))
    applicable_standard_row_count = sum(
        1
        for row in rows
        if row["component_type"] == "standard"
        and row["applicability_status"] == "applicable"
    )
    return {
        "schema_version": FOREST_PLAN_COMPLIANCE_SCHEMA_VERSION,
        "summary": {
            "scope_status": forest_plan_review.get("scope_status"),
            "reviewer_ready": bool(forest_plan_review.get("reviewer_ready")),
            "component_findings_path": forest_plan_review.get(
                "component_findings_path",
            ),
            "applicable_standard_coverage_path": forest_plan_review.get(
                "applicable_standard_coverage_path",
            ),
            "component_evaluation": forest_plan_review.get("component_evaluation"),
            "row_filter": (
                "applicable forest-plan component findings and compliance-evaluated "
                "standards"
            ),
            "row_count": len(rows),
            "applicability_counts": applicability_counts,
            "compliance_status_counts": compliance_status_counts,
            "component_type_counts": component_type_counts,
            "applicable_standard_row_count": applicable_standard_row_count,
            "load_errors": load_errors,
        },
        "columns": [
            "component_id",
            "component_type",
            "applicability_status",
            "compliance_status",
            "finding_status",
            "ea_package_citation",
            "forest_plan_citation",
            "determination",
            "rationale",
        ],
        "rows": rows,
    }


def _forest_plan_compliance_rows(
    *,
    review_id: str,
    component_findings: dict | None,
    coverage_by_component_id: dict[str, dict],
) -> list[dict]:
    if not component_findings:
        return []
    rows = []
    for finding in component_findings.get("findings", []):
        if not _include_forest_plan_compliance_finding(finding):
            continue
        component_id = str(finding.get("component_id") or "").strip()
        if not component_id:
            continue
        package_evidence = _first_dict(finding.get("package_evidence"))
        plan_source_evidence = _first_dict(finding.get("plan_source_evidence"))
        coverage = coverage_by_component_id.get(component_id, {})
        component_type = str(finding.get("component_type") or "unknown")
        applicability_status = str(
            finding.get("applicability_status") or "unknown",
        )
        compliance_status = str(
            finding.get("compliance_status")
            or coverage.get("compliance_status")
            or "not_evaluated_for_compliance",
        )
        finding_status = str(finding.get("finding_status") or "unknown")
        rows.append(
            {
                "row_id": f"forest-plan-matrix:{review_id}:{component_id}",
                "component_id": component_id,
                "component_key": _component_key(finding, coverage),
                "component_type": component_type,
                "applicability_status": applicability_status,
                "compliance_status": compliance_status,
                "finding_status": finding_status,
                "standard_applied": _standard_applied(finding, coverage),
                "ea_package_citation": package_evidence.get("citation_label"),
                "ea_package_evidence": _compact_evidence(package_evidence),
                "forest_plan_citation": plan_source_evidence.get("citation_label"),
                "forest_plan_evidence": _compact_evidence(plan_source_evidence),
                "determination": _forest_plan_determination(finding, package_evidence),
                "rationale": finding.get("rationale"),
                "reviewer_resolution_count": len(
                    finding.get("reviewer_resolution_items", []),
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            _forest_plan_component_type_sort_key(row["component_type"]),
            row["component_id"],
        )
    )
    return rows


def _include_forest_plan_compliance_finding(finding: dict) -> bool:
    compliance_status = finding.get("compliance_status")
    return finding.get("applicability_status") == "applicable" or compliance_status in {
        "complies",
        "does_not_comply",
        "partial",
        "uncertain",
    }


def _forest_plan_determination(finding: dict, package_evidence: dict) -> dict:
    basis = finding.get("applicability_basis") or {}
    package_determination = basis.get("package_component_determination") or {}
    return {
        "component_applies": package_evidence.get("component_applies")
        or package_determination.get("component_applies"),
        "review_section": package_evidence.get("review_section")
        or package_determination.get("review_section"),
        "source": package_evidence.get("determination_source")
        or package_determination.get("determination_source"),
        "component_text": package_evidence.get("determination_component_text"),
        "explanation": package_evidence.get("determination_explanation")
        or package_determination.get("determination_explanation"),
    }


def _forest_plan_compliance_markdown_lines(section: dict) -> list[str]:
    summary = section.get("summary", {})
    lines = [
        "",
        "## Forest Plan Compliance",
        "",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Decision-support status: `{_forest_plan_readiness_signal(summary)}`",
        f"- Applicable standard rows: `{summary.get('applicable_standard_row_count', 0)}`",
        "",
    ]
    if summary.get("load_errors"):
        lines.append(
            f"- Load errors: `{summary.get('load_errors')}`",
        )
        lines.append("")
    lines.extend(
        [
            (
                "| Component | Direction / standard | Decision support | EA consistency support | "
                "Forest Plan basis | Trace / caveats |"
            ),
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in section.get("rows", []):
        ea_evidence = row.get("ea_package_evidence") or {}
        plan_evidence = row.get("forest_plan_evidence") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(_forest_component_cell(row)),
                    _md_cell(_forest_direction_cell(row, plan_evidence)),
                    _md_cell(_forest_decision_support_cell(row)),
                    _md_cell(_forest_ea_support_cell(row, ea_evidence)),
                    _md_cell(_forest_plan_basis_cell(row, plan_evidence)),
                    _md_cell(_forest_trace_caveats_cell(row)),
                ]
            )
            + " |"
        )
    return lines


def _forest_component_cell(row: dict) -> str:
    return "<br>".join(
        [
            str(row.get("component_key") or row.get("component_id") or "unknown component"),
            _truncate(str(row.get("component_id") or ""), 105),
            _display_value(row.get("component_type")),
        ]
    )


def _forest_direction_cell(row: dict, plan_evidence: dict) -> str:
    direction = _forest_component_direction(row, plan_evidence, 260)
    return "<br>".join(
        [
            f"Plan direction: {direction}",
            f"Plan source: {row.get('forest_plan_citation') or 'No Forest Plan citation'}",
        ]
    )


def _forest_decision_support_cell(row: dict) -> str:
    component_type = str(row.get("component_type") or "")
    compliance_status = str(row.get("compliance_status") or "unknown")
    if component_type == "standard":
        lead = (
            "Applicable standard complies"
            if compliance_status == "complies"
            else f"Applicable standard needs review: {_display_value(compliance_status)}"
        )
    else:
        lead = (
            f"{_display_value(component_type)} considered; "
            "plan-consistency support recorded, not counted as an applicable standard."
        )
    parts = [
        lead,
        f"Applicability: {_display_value(row.get('applicability_status'))}",
        f"Finding support: {_display_value(row.get('finding_status'))}",
    ]
    if row.get("rationale"):
        parts.append(_truncate(str(row.get("rationale")), 180))
    return "<br>".join(parts)


def _forest_ea_support_cell(row: dict, ea_evidence: dict) -> str:
    determination = row.get("determination") or {}
    explanation = determination.get("explanation")
    parts = [
        str(row.get("ea_package_citation") or "No EA citation recorded."),
        _truncate(str(ea_evidence.get("title") or "Untitled EA record"), 100),
    ]
    if explanation:
        parts.append(f"EA determination: {_truncate(str(explanation), 260)}")
    else:
        excerpt = _evidence_excerpt(ea_evidence, 240)
        if excerpt:
            parts.append(f"Record says: {excerpt}")
    if determination.get("review_section"):
        parts.append(f"Section/source: {_truncate(str(determination['review_section']), 100)}")
    return "<br>".join(parts)


def _forest_plan_basis_cell(row: dict, plan_evidence: dict) -> str:
    parts = [
        str(row.get("forest_plan_citation") or "No Forest Plan citation recorded."),
        _truncate(str(plan_evidence.get("title") or "Untitled Forest Plan source"), 100),
    ]
    excerpt = _evidence_excerpt(plan_evidence, 260)
    if excerpt:
        parts.append(f"Plan text: {excerpt}")
    return "<br>".join(parts)


def _forest_trace_caveats_cell(row: dict) -> str:
    standard_applied = row.get("standard_applied")
    if standard_applied is None:
        standard_text = "standard applied: N/A"
    else:
        standard_text = f"standard applied: {'yes' if bool(standard_applied) else 'no'}"
    return "<br>".join(
        [
            standard_text,
            f"reviewer resolutions: {row.get('reviewer_resolution_count', 0)}",
            f"row trace: {_truncate(str(row.get('row_id') or 'not recorded'), 120)}",
        ]
    )


def _forest_component_direction(row: dict, plan_evidence: dict, max_chars: int) -> str:
    determination = row.get("determination") or {}
    component_text = determination.get("component_text")
    if component_text:
        return _truncate(str(component_text), max_chars)
    excerpt = _evidence_excerpt(plan_evidence, max_chars)
    if excerpt:
        return excerpt
    return "No component text excerpt recorded."


def _accuracy_audit_markdown_lines(matrix: dict) -> list[str]:
    audit_rows = _accuracy_audit_rows(matrix)
    lines = [
        "",
        "## Accuracy Audit",
        "",
        (
            "This audit checks artifact consistency, citation coverage, and reviewer-gate status. "
            "It does not certify legal sufficiency."
        ),
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for row in audit_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row["check"]),
                    _md_cell(row["result"]),
                    _md_cell(row["evidence"]),
                ]
            )
            + " |"
        )
    return lines


def _accuracy_audit_rows(matrix: dict) -> list[dict[str, str]]:
    summary = matrix.get("summary") or {}
    rows = matrix.get("rows") or []
    claim_rows = [row for row in rows if row.get("status") in CLAIM_STATUSES]
    pass_rows = [row for row in rows if row.get("status") == "pass"]
    missing_pass_package = [
        row.get("rule_id")
        for row in pass_rows
        if not row.get("ea_package_citation") or not row.get("ea_package_evidence")
    ]
    missing_source = [
        row.get("rule_id")
        for row in claim_rows
        if not row.get("source_library_citation") or not row.get("source_library_evidence")
    ]
    missing_claims = [
        row.get("rule_id") for row in claim_rows if not row.get("source_claim_ids")
    ]
    citation_failures = [
        row.get("rule_id") for row in rows if not row.get("citation_requirements_met")
    ]
    audit_rows = [
        _audit_row(
            "Review gates",
            bool(summary.get("reviewer_ready")) and bool(summary.get("validated")),
            _review_gate_phrase(summary),
        ),
        _audit_row(
            "NEPA authority rows",
            len(rows) == int(summary.get("row_count") or 0),
            f"{len(rows)} rendered rows; {_count_phrase(summary.get('status_counts', {}))}",
        ),
        _audit_row(
            "EA package evidence",
            not missing_pass_package,
            _missing_summary(missing_pass_package, "pass rows missing EA evidence"),
        ),
        _audit_row(
            "Source-library evidence",
            not missing_source,
            _missing_summary(missing_source, "claim rows missing source evidence"),
        ),
        _audit_row(
            "Source-claim traceability",
            not missing_claims and not citation_failures,
            (
                _missing_summary(missing_claims, "claim rows missing source claims")
                + "; "
                + _missing_summary(citation_failures, "rows failing citation requirements")
            ),
        ),
        _audit_row(
            "Non-applicable authority boundary",
            bool(summary.get("non_applicable_authorities_path")),
            (
                f"{summary.get('non_applicable_authority_count', 0)} authorities tracked in "
                f"{summary.get('non_applicable_authorities_path') or 'N/A'}"
            ),
        ),
    ]
    forest_plan = matrix.get("forest_plan_compliance") or {}
    if forest_plan:
        audit_rows.extend(_forest_plan_audit_rows(forest_plan))
    return audit_rows


def _forest_plan_audit_rows(section: dict) -> list[dict[str, str]]:
    summary = section.get("summary") or {}
    rows = section.get("rows") or []
    missing_ea = [
        row.get("component_key") or row.get("component_id")
        for row in rows
        if row.get("applicability_status") == "applicable"
        and not row.get("ea_package_citation")
    ]
    missing_plan = [
        row.get("component_key") or row.get("component_id")
        for row in rows
        if row.get("applicability_status") == "applicable"
        and not row.get("forest_plan_citation")
    ]
    applicable_standards = [
        row
        for row in rows
        if row.get("component_type") == "standard"
        and row.get("applicability_status") == "applicable"
    ]
    applied_standards = [
        row
        for row in applicable_standards
        if row.get("standard_applied") and row.get("compliance_status") == "complies"
    ]
    return [
        _audit_row(
            "Forest Plan rows",
            len(rows) == int(summary.get("row_count") or 0),
            (
                f"{len(rows)} rendered rows; "
                f"{_count_phrase(summary.get('compliance_status_counts', {}))}"
            ),
        ),
        _audit_row(
            "Forest Plan citations",
            not missing_ea and not missing_plan,
            (
                _missing_summary(missing_ea, "rows missing EA citation")
                + "; "
                + _missing_summary(missing_plan, "rows missing Forest Plan citation")
            ),
        ),
        _audit_row(
            "Applicable Forest Plan standards",
            len(applied_standards)
            == int(summary.get("applicable_standard_row_count") or 0),
            (
                f"{len(applied_standards)}/"
                f"{summary.get('applicable_standard_row_count', 0)} applicable standards comply"
            ),
        ),
    ]


def _audit_row(check: str, passed: bool, evidence: str) -> dict[str, str]:
    return {
        "check": check,
        "result": "Pass" if passed else "Needs review",
        "evidence": evidence,
    }


def _authority_readiness_signal(summary: dict) -> str:
    row_count = int(summary.get("row_count") or 0)
    status_counts = summary.get("status_counts", {})
    if row_count and status_counts == {"pass": row_count}:
        finding_signal = (
            f"All {row_count} applicable authority rows pass the deterministic evidence gate."
        )
    else:
        finding_signal = f"{row_count} authority rows are rendered: {_count_phrase(status_counts)}."
    return f"{finding_signal} {_review_gate_phrase(summary)}"


def _forest_plan_readiness_signal(summary: dict) -> str:
    row_count = int(summary.get("row_count") or 0)
    standard_count = int(summary.get("applicable_standard_row_count") or 0)
    status_counts = summary.get("compliance_status_counts", {})
    complies = int(status_counts.get("complies") or 0)
    non_standard_count = max(row_count - standard_count, 0)
    if standard_count and complies == standard_count:
        standard_signal = f"all {standard_count} applicable standards comply"
    elif standard_count:
        standard_signal = (
            f"{standard_count} applicable standards are present; "
            f"status detail: {_count_phrase(status_counts)}"
        )
    else:
        standard_signal = "no applicable standards are counted for pass/fail compliance"
    if non_standard_count:
        return (
            f"{row_count} applicable Forest Plan components are visible; "
            f"{standard_signal}; {non_standard_count} goals, guidelines, desired conditions, "
            "or other non-standard components are carried as plan-consistency support."
        )
    return f"{row_count} applicable Forest Plan components are visible; {standard_signal}."


def _review_gate_phrase(summary: dict) -> str:
    reviewer_ready = bool(summary.get("reviewer_ready"))
    validated = bool(summary.get("validated"))
    if reviewer_ready and validated:
        return "Review gates passed and reviewer-ready support is available."
    if reviewer_ready:
        return "Reviewer-ready support is available, but validation needs review."
    if validated:
        return "Validation passed, but reviewer-ready support is not available."
    return "Review gates need review before relying on this matrix."


def _count_phrase(counts: dict | None) -> str:
    if not counts:
        return "no counts recorded"
    ordered_keys = [
        "pass",
        "gap",
        "uncertain",
        "not_applicable",
        "applicable",
        "complies",
        "does_not_comply",
        "partial",
        "not_evaluated_for_compliance",
    ]
    seen: set[str] = set()
    keys: list[str] = []
    for key in ordered_keys:
        if key in counts:
            keys.append(key)
            seen.add(key)
    keys.extend(sorted(key for key in counts if key not in seen))
    return "; ".join(
        f"{int(counts[key])} {_count_label(key, int(counts[key]))}" for key in keys
    )


def _count_label(key: str, count: int) -> str:
    if key == "complies":
        return "standard complies" if count == 1 else "standards comply"
    if key == "does_not_comply":
        return "standard does not comply" if count == 1 else "standards do not comply"
    return _display_value(key).lower()


def _yes_no_sentence(value: object, label: str) -> str:
    return f"{label}: {'yes' if bool(value) else 'no'}"


def _missing_summary(values: list[object], label: str) -> str:
    cleaned = [str(value) for value in values if value]
    if not cleaned:
        return f"0 {label}"
    preview = ", ".join(cleaned[:5])
    suffix = "" if len(cleaned) <= 5 else f", +{len(cleaned) - 5} more"
    return f"{len(cleaned)} {label}: {preview}{suffix}"


def _section_row_count(section: dict | None) -> int:
    if not section:
        return 0
    return int((section.get("summary") or {}).get("row_count") or 0)


def _section_summary_value(section: dict | None, key: str, default):
    if not section:
        return default
    return (section.get("summary") or {}).get(key, default)


def _optional_path(value: object) -> Path | None:
    if not value:
        return None
    return Path(str(value))


def _strings(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if str(value or "").strip():
        return [str(value).strip()]
    return []


def _read_json_if_exists(path: Path | None, load_errors: list[str]) -> dict | None:
    if path is None:
        return None
    if not path.exists():
        load_errors.append(f"missing:{path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        load_errors.append(f"unreadable:{path}:{exc}")
        return None
    if not isinstance(payload, dict):
        load_errors.append(f"invalid_json_object:{path}")
        return None
    return payload


def _standard_coverage_by_component_id(standard_coverage: dict | None) -> dict[str, dict]:
    if not standard_coverage:
        return {}
    coverage = {}
    for row in standard_coverage.get("standards", []):
        if not isinstance(row, dict):
            continue
        component_id = str(
            row.get("component_id") or row.get("standard_id") or "",
        ).strip()
        if component_id:
            coverage[component_id] = row
    return coverage


def _first_dict(values: object) -> dict:
    if isinstance(values, list):
        for value in values:
            if isinstance(value, dict):
                return value
    if isinstance(values, dict):
        return values
    return {}


def _component_key(finding: dict, coverage: dict) -> str | None:
    basis = finding.get("applicability_basis") or {}
    value = (
        finding.get("component_key")
        or coverage.get("component_key")
        or basis.get("component_key")
    )
    return str(value) if value else None


def _standard_applied(finding: dict, coverage: dict) -> bool | None:
    for key in ("standard_applied", "applied"):
        if key in finding:
            return bool(finding.get(key))
        if key in coverage:
            return bool(coverage.get(key))
    return None


def _forest_plan_component_type_sort_key(component_type: str) -> int:
    order = {
        "standard": 0,
        "guideline": 1,
        "desired_condition": 2,
        "objective": 3,
        "suitability": 4,
    }
    return order.get(component_type, 99)


def _compact_evidence(evidence: dict | None) -> dict | None:
    if not evidence:
        return None
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    return {
        "citation_label": evidence.get("citation_label"),
        "source_record_id": evidence.get("source_record_id"),
        "title": evidence.get("title"),
        "chunk_id": evidence.get("chunk_id"),
        "text": span.get("text"),
        "source_char_start": span.get("source_char_start"),
        "source_char_end": span.get("source_char_end"),
        "chunk_char_start": span.get("chunk_char_start"),
        "chunk_char_end": span.get("chunk_char_end"),
        "page": provenance.get("page"),
        "section": provenance.get("section"),
        "artifact_path": provenance.get("artifact_path"),
        "artifact_sha256": provenance.get("artifact_sha256"),
        "content_sha256": provenance.get("content_sha256"),
    }


def finding_source_record_ids(finding: dict) -> list[str]:
    source_record_ids = set()
    source_evidence = finding.get("source_library_evidence") or {}
    if source_evidence.get("source_record_id"):
        source_record_ids.add(str(source_evidence["source_record_id"]))
    for link in finding.get("source_claim_links", []):
        if link.get("source_record_id"):
            source_record_ids.add(str(link["source_record_id"]))
    return sorted(source_record_ids)


def finding_source_document_roles(finding: dict) -> list[str]:
    roles = set()
    source_evidence = finding.get("source_library_evidence") or {}
    if source_evidence.get("document_role"):
        roles.add(str(source_evidence["document_role"]))
    for link in finding.get("source_claim_links", []):
        if link.get("document_role"):
            roles.add(str(link["document_role"]))
    return sorted(roles)


def _finding_has_required_eval_citations(finding: dict) -> bool:
    status = finding.get("status")
    if status not in CLAIM_STATUSES:
        return True
    if not _finding_has_source_evidence(finding) or not _finding_has_source_claim_links(finding):
        return False
    if status == "pass" and not _finding_has_package_evidence(finding):
        return False
    return True


def _finding_has_package_evidence(finding: dict) -> bool:
    return bool(finding.get("package_evidence_citation") and finding.get("package_evidence"))


def _finding_has_source_evidence(finding: dict) -> bool:
    return bool(
        finding.get("source_library_evidence_citation")
        and finding.get("source_library_evidence")
    )


def _finding_has_source_claim_links(finding: dict) -> bool:
    return bool(finding.get("source_claim_link_count") and finding.get("source_claim_links"))


def _matrix_failure_category(finding: dict) -> str | None:
    status = finding.get("status")
    if status == "pass":
        return None
    if status == "gap":
        return "package_evidence_gap"
    if status == "not_applicable":
        return "not_applicable"
    if finding.get("source_library_evidence_status") != "found":
        return "source_retrieval_miss"
    if finding.get("package_evidence_status") != "found":
        return "package_evidence_search_miss"
    if status not in VALID_FINDING_STATUSES:
        return "unsupported_status"
    return "uncertain_finding"


def _matrix_pdf_pages(matrix: dict) -> list[list[str]]:
    summary = matrix["summary"]
    rule_pack = matrix["rule_pack"]
    lines = [
        "Compliance Matrix",
        f"Review ID: {matrix['review_id']}",
        f"Source set: {matrix.get('source_set_id')}",
        f"Rule pack: {rule_pack['rule_pack_id']} {rule_pack['version']}",
        f"Authority findings: {summary['row_count']} rows; {_count_phrase(summary['status_counts'])}",
        f"Applicability: {_count_phrase(summary.get('applicability_counts', {}))}",
        f"Review gates: {_review_gate_phrase(summary)}",
    ]
    forest_plan_review = summary.get("forest_plan_review") or {}
    if forest_plan_review:
        lines.append(
            "Forest-plan review: "
            f"{forest_plan_review.get('scope_status')} "
            f"({_yes_no_sentence(forest_plan_review.get('reviewer_ready'), 'reviewer ready')})"
        )
    lines.extend(
        [
            "",
            "Forest Supervisor Readout",
            "",
        ]
    )
    lines.extend(
        _pdf_wrapped_table_lines(
            ["Signing question", "Current decision-support signal"],
            [
                [
                    row["check"],
                    row["signal"],
                ]
                for row in _supervisor_readout_rows(matrix)
            ],
            [48, 132],
        )
    )
    lines.extend(
        [
            "",
            "Accuracy Audit",
            "",
        ]
    )
    lines.extend(
        _pdf_wrapped_table_lines(
            ["Check", "Result", "Evidence"],
            [
                [row["check"], row["result"], row["evidence"]]
                for row in _accuracy_audit_rows(matrix)
            ],
            [34, 14, 120],
        )
    )
    lines.extend(
        [
            "",
            (
                "Workflow: identify applicable authorities, evaluate the EA against each applicable "
                "authority, and cite both EA-package and source-library evidence."
            ),
            "",
            "NEPA / Authority Compliance",
            "",
        ]
    )
    lines.extend(
        _pdf_wrapped_table_lines(
            ["Topic", "Question", "Finding", "EA support", "Authority", "Trace"],
            [_matrix_pdf_table_row(row) for row in matrix["rows"]],
            [27, 36, 30, 42, 42, 20],
        )
    )
    forest_plan_compliance = matrix.get("forest_plan_compliance")
    if forest_plan_compliance:
        summary = forest_plan_compliance.get("summary", {})
        lines.extend(
            [
                "",
                "Forest Plan Compliance",
                f"Rows: {summary.get('row_count', 0)}",
                f"Decision-support status: {_forest_plan_readiness_signal(summary)}",
                (
                    "Applicable standard rows: "
                    f"{summary.get('applicable_standard_row_count', 0)}"
                ),
                "",
            ]
        )
        lines.extend(
            _pdf_wrapped_table_lines(
                [
                    "Component",
                    "Direction",
                    "Finding",
                    "EA support",
                    "Plan basis",
                    "Trace",
                ],
                [
                    _forest_plan_pdf_table_row(row)
                    for row in forest_plan_compliance.get("rows", [])
                ],
                [26, 42, 34, 42, 42, 18],
            )
        )
    return _paginate_pdf_lines(lines, max_lines=42)


def _matrix_pdf_table_row(row: dict) -> list[str]:
    ea_evidence = row.get("ea_package_evidence") or {}
    source_evidence = row.get("source_library_evidence") or {}
    return [
        _nepa_topic_cell(row),
        _nepa_signer_question_cell(row),
        _nepa_decision_support_cell(row),
        _evidence_support_cell(row.get("ea_package_citation"), ea_evidence),
        _authority_basis_cell(row, source_evidence),
        _trace_caveats_cell(row),
    ]


def _forest_plan_pdf_table_row(row: dict) -> list[str]:
    ea_evidence = row.get("ea_package_evidence") or {}
    plan_evidence = row.get("forest_plan_evidence") or {}
    return [
        _forest_component_cell(row),
        _forest_direction_cell(row, plan_evidence),
        _forest_decision_support_cell(row),
        _forest_ea_support_cell(row, ea_evidence),
        _forest_plan_basis_cell(row, plan_evidence),
        _forest_trace_caveats_cell(row),
    ]


def _pdf_table_lines(
    headers: list[str],
    rows: list[list[str]],
    widths: list[int],
) -> list[str]:
    rendered = [_pdf_table_row(headers, widths), _pdf_table_separator(widths)]
    for row in rows:
        rendered.append(_pdf_table_row(row, widths))
    return rendered


def _pdf_wrapped_table_lines(
    headers: list[str],
    rows: list[list[str]],
    widths: list[int],
) -> list[str]:
    rendered = [_pdf_table_row(headers, widths), _pdf_table_separator(widths)]
    for row in rows:
        rendered.extend(_pdf_wrapped_table_row_lines(row, widths))
        rendered.append(_pdf_table_separator(widths))
    return rendered


def _pdf_wrapped_table_row_lines(values: list[str], widths: list[int]) -> list[str]:
    wrapped_cells = [
        _wrap_pdf_cell(_pdf_text(value).replace("<br>", " / "), width)
        for value, width in zip(values, widths, strict=True)
    ]
    row_height = max(len(cell) for cell in wrapped_cells)
    lines = []
    for index in range(row_height):
        cells = [
            (cell[index] if index < len(cell) else "").ljust(width)
            for cell, width in zip(wrapped_cells, widths, strict=True)
        ]
        lines.append(" | ".join(cells))
    return lines


def _wrap_pdf_cell(value: str, width: int) -> list[str]:
    text = " ".join(str(value).split())
    if not text:
        return [""]
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def _pdf_table_row(values: list[str], widths: list[int]) -> str:
    cells = [
        _truncate(_pdf_text(value), width).ljust(width)
        for value, width in zip(values, widths, strict=True)
    ]
    return " | ".join(cells)


def _pdf_table_separator(widths: list[int]) -> str:
    return "-+-".join("-" * width for width in widths)


def _paginate_pdf_lines(lines: list[str], *, max_lines: int) -> list[list[str]]:
    pages: list[list[str]] = []
    page: list[str] = []
    for line in lines:
        if len(page) >= max_lines:
            pages.append(page)
            page = []
        page.append(line)
    if page:
        pages.append(page)
    return pages or [["Compliance Matrix"]]


def _write_simple_pdf(path: Path, pages: list[list[str]], *, title: str) -> None:
    width = 1008
    height = 612
    margin_x = 34
    start_y = 568
    leading = 12
    font_size = 8
    objects: list[bytes | None] = [None, None, None]

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    for page_number, page_lines in enumerate(pages, start=1):
        content = _pdf_page_content(
            page_lines,
            page_number=page_number,
            page_count=len(pages),
            title=title,
            margin_x=margin_x,
            start_y=start_y,
            leading=leading,
            font_size=font_size,
        )
        content_id = add_object(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects[1] = (objects[1] or b"") + f"{page_id} 0 R ".encode("ascii")

    kids = objects[1] or b""
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        b"<< /Type /Pages /Kids ["
        + kids
        + b"] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>"
    )
    objects[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"
    _write_pdf_objects(path, [obj for obj in objects if obj is not None])


def _pdf_page_content(
    lines: list[str],
    *,
    page_number: int,
    page_count: int,
    title: str,
    margin_x: int,
    start_y: int,
    leading: int,
    font_size: int,
) -> bytes:
    commands = [f"BT /F1 {font_size} Tf {leading} TL {margin_x} {start_y} Td"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj T*")
    footer_y = 24 - (start_y - len(lines) * leading)
    commands.append(
        f"0 {footer_y} Td ({_pdf_escape(f'{title} | Page {page_number} of {page_count}')}) Tj"
    )
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _pdf_escape(value: str) -> str:
    return (
        _pdf_text(value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _pdf_text(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a7": "Sec.",
        "<br>": " / ",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    offsets = []
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(payload))


def _truncate(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _evidence_excerpt(evidence: dict, max_chars: int) -> str:
    text = _clean_evidence_text(str(evidence.get("text") or ""))
    if not text:
        return ""
    return _truncate(text, max_chars)


def _clean_evidence_text(value: str) -> str:
    text = value.replace("|", " ")
    text = text.replace("#", " ")
    text = text.replace("*", " ")
    text = text.replace("\u2022", " ")
    text = " ".join(text.split())
    while "---" in text:
        text = text.replace("---", "--")
    text = text.strip(" -")
    if text and text[0].islower():
        match = re.search(r"\b[A-Z][A-Za-z0-9]", text)
        if match and match.start() < 120:
            text = text[match.start() :]
    return text


def _display_value(value: object) -> str:
    text = str(value or "unknown").replace("_", " ").strip()
    if not text:
        return "Unknown"
    return text[:1].upper() + text[1:]


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _rule_pack_summary(rule_pack: dict) -> dict:
    return {
        "schema_version": rule_pack["schema_version"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "version": rule_pack["version"],
        "title": rule_pack["title"],
        "description": rule_pack.get("description"),
        "domain": rule_pack.get("domain"),
        "jurisdiction": rule_pack.get("jurisdiction"),
        "baseline_source_record_ids": _baseline_source_record_ids(rule_pack),
        "rule_count": len(rule_pack["rules"]),
    }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
