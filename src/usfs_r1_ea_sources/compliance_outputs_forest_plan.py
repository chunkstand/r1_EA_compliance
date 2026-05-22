from __future__ import annotations

from collections import Counter

from .compliance_outputs_common import _compact_evidence
from .compliance_outputs_common import _component_key
from .compliance_outputs_common import _display_value
from .compliance_outputs_common import _evidence_excerpt
from .compliance_outputs_common import _first_dict
from .compliance_outputs_common import _forest_plan_component_type_sort_key
from .compliance_outputs_common import _forest_plan_readiness_signal
from .compliance_outputs_common import _matrix_row_marker
from .compliance_outputs_common import _md_cell
from .compliance_outputs_common import _optional_path
from .compliance_outputs_common import _read_json_if_exists
from .compliance_outputs_common import _standard_applied
from .compliance_outputs_common import _standard_coverage_by_component_id
from .compliance_outputs_common import _truncate


FOREST_PLAN_COMPLIANCE_SCHEMA_VERSION = "forest-plan-compliance-matrix-v0"


def _forest_plan_compliance_section(
    *,
    review_id: str,
    forest_plan_review: dict | None,
) -> dict | None:
    if not forest_plan_review:
        return None
    component_findings_path = _optional_path(forest_plan_review.get("component_findings_path"))
    standard_coverage_path = _optional_path(
        forest_plan_review.get("applicable_standard_coverage_path")
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
    compliance_status_counts = dict(Counter(row["compliance_status"] for row in rows))
    applicability_counts = dict(Counter(row["applicability_status"] for row in rows))
    component_type_counts = dict(Counter(row["component_type"] for row in rows))
    applicable_standard_row_count = sum(
        1
        for row in rows
        if row["component_type"] == "standard" and row["applicability_status"] == "applicable"
    )
    return {
        "schema_version": FOREST_PLAN_COMPLIANCE_SCHEMA_VERSION,
        "summary": {
            "scope_status": forest_plan_review.get("scope_status"),
            "reviewer_ready": bool(forest_plan_review.get("reviewer_ready")),
            "component_findings_path": forest_plan_review.get("component_findings_path"),
            "applicable_standard_coverage_path": forest_plan_review.get(
                "applicable_standard_coverage_path"
            ),
            "component_evaluation": forest_plan_review.get("component_evaluation"),
            "row_filter": (
                "applicable forest-plan component findings and compliance-evaluated standards"
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
        applicability_status = str(finding.get("applicability_status") or "unknown")
        compliance_status = str(
            finding.get("compliance_status")
            or coverage.get("compliance_status")
            or "not_evaluated_for_compliance"
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
                "reviewer_resolution_count": len(finding.get("reviewer_resolution_items", [])),
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
        lines.append(f"- Load errors: `{summary.get('load_errors')}`")
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
                    _md_cell(
                        "<!-- "
                        + _matrix_row_marker("forest-plan", row.get("component_id"))
                        + " --><br>"
                        + _forest_component_cell(row)
                    ),
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
