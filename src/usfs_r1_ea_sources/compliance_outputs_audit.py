from __future__ import annotations

from .compliance_outputs_common import CLAIM_STATUSES
from .compliance_outputs_common import _count_phrase
from .compliance_outputs_common import _missing_summary
from .compliance_outputs_common import _md_cell
from .compliance_outputs_common import _review_gate_phrase


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
    missing_claims = [row.get("rule_id") for row in claim_rows if not row.get("source_claim_ids")]
    citation_failures = [row.get("rule_id") for row in rows if not row.get("citation_requirements_met")]
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
        if row.get("applicability_status") == "applicable" and not row.get("ea_package_citation")
    ]
    missing_plan = [
        row.get("component_key") or row.get("component_id")
        for row in rows
        if row.get("applicability_status") == "applicable" and not row.get("forest_plan_citation")
    ]
    applicable_standards = [
        row
        for row in rows
        if row.get("component_type") == "standard" and row.get("applicability_status") == "applicable"
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
            f"{len(rows)} rendered rows; {_count_phrase(summary.get('compliance_status_counts', {}))}",
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
            len(applied_standards) == int(summary.get("applicable_standard_row_count") or 0),
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
