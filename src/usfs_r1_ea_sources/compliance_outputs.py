from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
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
        f"- Review ID: `{matrix['review_id']}`",
        f"- Source set: `{matrix.get('source_set_id')}`",
        f"- Rule pack: `{matrix['rule_pack']['rule_pack_id']}` "
        f"`{matrix['rule_pack']['version']}`",
        f"- Rows: `{summary['row_count']}`",
        f"- Status counts: `{summary['status_counts']}`",
        f"- Applicability counts: `{summary.get('applicability_counts', {})}`",
        f"- Reviewer ready: `{summary['reviewer_ready']}`",
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
            f"(reviewer ready: `{forest_plan_review.get('reviewer_ready')}`)"
        )
    lines.extend(
        [
            "",
            "## NEPA / Authority Compliance",
            "",
            "| Authority | Applicability | Status | EA evidence | Source evidence | Source claims | Limitations |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in matrix["rows"]:
        ea_evidence = row.get("ea_package_evidence") or {}
        source_evidence = row.get("source_library_evidence") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(
                        _authority_markdown_cell(row)
                    ),
                    _md_cell(
                        f"{row.get('applicability_status')} / "
                        f"{row.get('applicability_mode')}"
                    ),
                    _md_cell(row["status"]),
                    _md_cell(
                        _markdown_evidence_cell(
                            row.get("ea_package_citation"),
                            ea_evidence.get("title"),
                            ea_evidence.get("text"),
                        )
                    ),
                    _md_cell(
                        _markdown_evidence_cell(
                            row.get("source_library_citation"),
                            source_evidence.get("title"),
                            source_evidence.get("text"),
                        )
                    ),
                    _md_cell(", ".join(row.get("source_claim_ids", [])) or "N/A"),
                    _md_cell("; ".join(row.get("limitations", [])) or "None"),
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


def _authority_markdown_cell(row: dict) -> str:
    family_ids = ", ".join(row.get("authority_family_ids") or []) or "none"
    source = row.get("authority_source_record_id") or "none"
    candidate = row.get("candidate_authority_id") or "none"
    return (
        f"{row['rule_id']} - {row['rule_title']} "
        f"(family: {family_ids}; candidate: {candidate}; "
        f"{row.get('authority_category')}: {source})"
    )


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
        f"- Status counts: `{summary.get('compliance_status_counts', {})}`",
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
            "| Component | Type | Applicability | Compliance | EA evidence | Forest Plan evidence | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in section.get("rows", []):
        ea_evidence = row.get("ea_package_evidence") or {}
        plan_evidence = row.get("forest_plan_evidence") or {}
        determination = row.get("determination") or {}
        notes = determination.get("explanation") or row.get("rationale") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("component_id")),
                    _md_cell(row.get("component_type")),
                    _md_cell(row.get("applicability_status")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(
                        _markdown_evidence_cell(
                            row.get("ea_package_citation"),
                            ea_evidence.get("title"),
                            ea_evidence.get("text"),
                        )
                    ),
                    _md_cell(
                        _markdown_evidence_cell(
                            row.get("forest_plan_citation"),
                            plan_evidence.get("title"),
                            plan_evidence.get("text"),
                        )
                    ),
                    _md_cell(notes or "None"),
                ]
            )
            + " |"
        )
    return lines


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
        f"Rows: {summary['row_count']}",
        f"Status counts: {summary['status_counts']}",
        f"Applicability counts: {summary.get('applicability_counts', {})}",
        f"Reviewer ready: {summary['reviewer_ready']}",
    ]
    forest_plan_review = summary.get("forest_plan_review") or {}
    if forest_plan_review:
        lines.append(
            "Forest-plan review: "
            f"{forest_plan_review.get('scope_status')} "
            f"(reviewer ready: {forest_plan_review.get('reviewer_ready')})"
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
    for index, row in enumerate(matrix["rows"], start=1):
        lines.extend(_matrix_pdf_row_lines(index, row))
        lines.append("")
    forest_plan_compliance = matrix.get("forest_plan_compliance")
    if forest_plan_compliance:
        summary = forest_plan_compliance.get("summary", {})
        lines.extend(
            [
                "",
                "Forest Plan Compliance",
                f"Rows: {summary.get('row_count', 0)}",
                f"Status counts: {summary.get('compliance_status_counts', {})}",
                (
                    "Applicable standard rows: "
                    f"{summary.get('applicable_standard_row_count', 0)}"
                ),
                "",
            ]
        )
        for index, row in enumerate(forest_plan_compliance.get("rows", []), start=1):
            lines.extend(_forest_plan_pdf_row_lines(index, row))
            lines.append("")
    return _paginate_pdf_lines(lines, max_lines=45)


def _matrix_pdf_row_lines(index: int, row: dict) -> list[str]:
    ea_evidence = row.get("ea_package_evidence") or {}
    source_evidence = row.get("source_library_evidence") or {}
    lines = [
        (
            f"{index}. {row['rule_id']} - {row['rule_title']} "
            f"({row.get('authority_category')}: {row.get('authority_source_record_id')})"
        ),
        (
            f"   Applicability: {row.get('applicability_status')} / "
            f"{row.get('applicability_mode')} | Status: {row.get('status')}"
        ),
        (
            "   EA evidence: "
            + _pdf_evidence_cell(row.get("ea_package_citation"), ea_evidence)
        ),
        (
            "   Source evidence: "
            + _pdf_evidence_cell(row.get("source_library_citation"), source_evidence)
        ),
        "   Source claims: " + (", ".join(row.get("source_claim_ids", [])) or "N/A"),
        "   Limitations: " + ("; ".join(row.get("limitations", [])) or "None"),
    ]
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(_wrap_pdf_line(line))
    return wrapped


def _pdf_evidence_cell(citation: str | None, evidence: dict) -> str:
    if not evidence:
        return "N/A"
    parts = []
    if citation:
        parts.append(citation)
    if evidence.get("title"):
        parts.append(str(evidence["title"]))
    if evidence.get("text"):
        parts.append(_truncate(str(evidence["text"]), 260))
    return " - ".join(parts) if parts else "N/A"


def _forest_plan_pdf_row_lines(index: int, row: dict) -> list[str]:
    ea_evidence = row.get("ea_package_evidence") or {}
    plan_evidence = row.get("forest_plan_evidence") or {}
    determination = row.get("determination") or {}
    notes = determination.get("explanation") or row.get("rationale") or "None"
    lines = [
        (
            f"{index}. {row.get('component_id')} "
            f"({row.get('component_type')})"
        ),
        (
            f"   Applicability: {row.get('applicability_status')} | "
            f"Compliance: {row.get('compliance_status')} | "
            f"Finding: {row.get('finding_status')}"
        ),
        (
            "   EA evidence: "
            + _pdf_evidence_cell(row.get("ea_package_citation"), ea_evidence)
        ),
        (
            "   Forest Plan evidence: "
            + _pdf_evidence_cell(row.get("forest_plan_citation"), plan_evidence)
        ),
        "   Notes: " + notes,
    ]
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(_wrap_pdf_line(line))
    return wrapped


def _wrap_pdf_line(line: str, width: int = 150) -> list[str]:
    if len(line) <= width:
        return [line]
    leading_spaces = len(line) - len(line.lstrip(" "))
    indent = " " * min(leading_spaces + 4, 10)
    return textwrap.wrap(
        line,
        width=width,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


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
    objects[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
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


def _markdown_evidence_cell(citation: str | None, title: str | None, text: str | None) -> str:
    if not citation:
        return "N/A"
    parts = [citation]
    if title:
        parts.append(title)
    if text:
        parts.append(_truncate(text, 220))
    return " - ".join(parts)


def _truncate(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


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
