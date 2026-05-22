from __future__ import annotations

from collections import Counter
from pathlib import Path

from .compliance_outputs_audit import _accuracy_audit_markdown_lines
from .compliance_outputs_common import CLAIM_STATUSES
from .compliance_outputs_common import _authority_readiness_signal
from .compliance_outputs_common import _compact_evidence
from .compliance_outputs_common import _count_phrase
from .compliance_outputs_common import _display_value
from .compliance_outputs_common import _evidence_excerpt
from .compliance_outputs_common import _finding_has_required_eval_citations
from .compliance_outputs_common import _forest_plan_readiness_signal
from .compliance_outputs_common import _matrix_failure_category
from .compliance_outputs_common import _matrix_row_marker
from .compliance_outputs_common import _md_cell
from .compliance_outputs_common import _review_gate_phrase
from .compliance_outputs_common import _rule_pack_summary
from .compliance_outputs_common import _section_row_count
from .compliance_outputs_common import _section_summary_value
from .compliance_outputs_common import _strings
from .compliance_outputs_common import _truncate
from .compliance_outputs_common import _utc_now
from .compliance_outputs_common import _yes_no_sentence
from .compliance_outputs_common import finding_source_document_roles
from .compliance_outputs_common import finding_source_record_ids
from .compliance_outputs_forest_plan import _forest_plan_compliance_markdown_lines
from .compliance_outputs_forest_plan import _forest_plan_compliance_section


COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"


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
            "authority_explanation_paths_path": summary.get("authority_explanation_paths_path"),
            "compliance_matrix_pdf_path": summary.get("compliance_matrix_pdf_path"),
            "authority_provenance_path": summary.get("authority_provenance_path"),
            "non_applicable_authority_appendix_path": summary.get(
                "non_applicable_authority_appendix_path"
            ),
            "non_applicable_authority_appendix_markdown_path": summary.get(
                "non_applicable_authority_appendix_markdown_path"
            ),
            "reviewer_resolution_report_path": summary.get("reviewer_resolution_report_path"),
            "litigation_risk_summary_path": summary.get("litigation_risk_summary_path"),
            "finding_graph_nodes_path": summary.get("finding_nodes_path"),
            "finding_graph_edges_path": summary.get("finding_edges_path"),
            "forest_plan_review": summary.get("forest_plan_review"),
            "forest_plan_compliance_row_count": _section_row_count(forest_plan_compliance),
            "forest_plan_compliance_status_counts": _section_summary_value(
                forest_plan_compliance,
                "compliance_status_counts",
                {},
            ),
            "forest_plan_compliance_applicable_standard_row_count": _section_summary_value(
                forest_plan_compliance,
                "applicable_standard_row_count",
                0,
            ),
            "applicability_gate": summary.get("applicability_gate"),
            "authority_integration": summary.get("authority_integration"),
            "non_applicable_authorities_path": applicability_gate.get(
                "non_applicable_authorities_path"
            ),
            "non_applicable_authority_count": applicability_gate.get(
                "non_applicable_authority_count"
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
            "primary_authority_path_classification",
            "authority_path_classifications",
            "status",
            "applicability_status",
            "applicability_mode",
            "retrieval_trace_ids",
            "graph_path_ids",
            "search_coverage_certificate_ids",
            "supporting_source_record_ids",
            "residual_risk_categories",
            "unresolved_issue_refs",
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
        f"- Rule pack: `{matrix['rule_pack']['rule_pack_id']}` `{matrix['rule_pack']['version']}`",
        f"- Authority findings: `{summary['row_count']} rows; {_count_phrase(summary['status_counts'])}`",
        f"- Applicability: `{_count_phrase(summary.get('applicability_counts', {}))}`",
        f"- Review gates: `{_review_gate_phrase(summary)}`",
    ]
    if summary.get("non_applicable_authorities_path"):
        lines.append(
            "- Non-applicable authorities source: "
            f"`{summary.get('non_applicable_authorities_path')}` "
            f"(`{summary.get('non_applicable_authority_count', 0)}` authorities)"
        )
    if summary.get("authority_explanation_paths_path"):
        lines.append(
            "- Authority explanation paths: "
            f"`{summary.get('authority_explanation_paths_path')}`"
        )
    forest_plan_review = summary.get("forest_plan_review") or {}
    if forest_plan_review:
        lines.append(
            f"- Forest-plan review: `{forest_plan_review.get('scope_status')}` "
            f"({_yes_no_sentence(forest_plan_review.get('reviewer_ready'), 'reviewer ready')})"
        )
    lines.extend(_responsible_official_readout_markdown_lines(matrix))
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
        "primary_authority_path_classification": finding.get(
            "primary_authority_path_classification"
        ),
        "authority_path_classifications": _strings(finding.get("authority_path_classifications")),
        "retrieval_trace_ids": _strings(finding.get("retrieval_trace_ids")),
        "graph_path_ids": _strings(finding.get("graph_path_ids")),
        "search_coverage_certificate_ids": _strings(finding.get("search_coverage_certificate_ids")),
        "supporting_source_record_ids": _strings(finding.get("supporting_source_record_ids")),
        "residual_risk_categories": _strings(finding.get("residual_risk_categories")),
        "unresolved_issue_refs": _strings(finding.get("unresolved_issue_refs")),
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
            "applies_if_package_term_groups": finding.get("applies_if_package_term_groups", []),
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


def _responsible_official_readout_markdown_lines(matrix: dict) -> list[str]:
    lines = [
        "",
        "## Responsible Official Readout",
        "",
        "| Signing question | Current decision-support signal |",
        "| --- | --- |",
    ]
    for row in _responsible_official_readout_rows(matrix):
        lines.append(f"| {_md_cell(row['check'])} | {_md_cell(row['signal'])} |")
    return lines


def _responsible_official_readout_rows(matrix: dict) -> list[dict[str, str]]:
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
    return "<!-- " + _matrix_row_marker("authority", row.get("rule_id")) + " --><br>" + "<br>".join(
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
    path_classes = ", ".join(row.get("authority_path_classifications") or []) or "none"
    parts = [
        str(citation),
        _truncate(str(evidence.get("title") or "Untitled authority source"), 100),
        f"Requirement: {_truncate(str(row.get('requirement') or 'Not recorded.'), 210)}",
    ]
    excerpt = _evidence_excerpt(evidence, 180)
    if excerpt:
        parts.append(f"Authority text: {excerpt}")
    parts.append(f"Family: {_truncate(family_ids, 100)}")
    parts.append(f"Path classes: {_truncate(path_classes, 100)}")
    return "<br>".join(parts)


def _trace_caveats_cell(row: dict) -> str:
    claim_count = int(row.get("source_claim_count") or len(row.get("source_claim_ids", [])))
    citation_status = (
        "citation gate complete"
        if row.get("citation_requirements_met")
        else "citation gate needs review"
    )
    parts = [f"{claim_count} source claim{'s' if claim_count != 1 else ''}", citation_status]
    source_claims = row.get("source_claim_ids") or []
    if source_claims:
        parts.append("claims: " + _truncate(", ".join(str(value) for value in source_claims), 120))
    trace_refs = _strings(row.get("retrieval_trace_ids")) + _strings(row.get("graph_path_ids"))
    if trace_refs:
        parts.append("traces: " + _truncate(", ".join(trace_refs), 140))
    coverage_refs = _strings(row.get("search_coverage_certificate_ids"))
    if coverage_refs:
        parts.append("coverage: " + _truncate(", ".join(coverage_refs), 140))
    risk_categories = _strings(row.get("residual_risk_categories"))
    if risk_categories:
        parts.append("risk: " + _truncate(", ".join(risk_categories), 140))
    unresolved_issue_refs = _strings(row.get("unresolved_issue_refs"))
    if unresolved_issue_refs:
        parts.append("open issues: " + _truncate("; ".join(unresolved_issue_refs), 160))
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
