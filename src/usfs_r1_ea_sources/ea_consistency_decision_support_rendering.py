from __future__ import annotations

from pathlib import Path
from typing import Any

from .ea_consistency_decision_support_models import _DecisionSupportContext
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _dict_list
from .ea_consistency_decision_support_models import _int
from .ea_consistency_decision_support_models import _list
from .ea_consistency_decision_support_models import _md_cell
from .ea_consistency_decision_support_models import _paginate_pdf_lines
from .ea_consistency_decision_support_models import _strings
from .ea_consistency_decision_support_models import _truncate
from .ea_consistency_decision_support_models import _wrap_pdf_line


def _resolve_selector(
    context: _DecisionSupportContext,
    selector: dict[str, Any],
) -> dict[str, Any] | None:
    selector_type = str(selector.get("selector_type") or "")
    criteria = _parse_selector(str(selector.get("selector") or ""))
    if selector_type == "package_chunk":
        return _find_by_criteria(_list(context.payload("package_chunks")), criteria)
    if selector_type == "package_record":
        return _find_by_criteria(_list(context.payload("package_manifest")), criteria)
    if selector_type == "authority_finding":
        return _find_by_criteria(
            _dict_list(context.payload("compliance_matrix").get("rows")),
            criteria,
        )
    if selector_type == "forest_plan_standard":
        return _find_by_criteria(
            _dict_list(
                context.payload("forest_plan_applicable_standard_coverage").get("standards")
            ),
            criteria,
        )
    return None


def _selector_evidence(resolved: dict[str, Any]) -> list[dict[str, Any]]:
    if resolved.get("ea_package_evidence") or resolved.get("source_library_evidence"):
        evidence = []
        if resolved.get("ea_package_evidence"):
            evidence.append(_evidence(resolved["ea_package_evidence"]))
        if resolved.get("source_library_evidence"):
            evidence.append(_evidence(resolved["source_library_evidence"]))
        return evidence
    if "text" in resolved and "chunk_id" in resolved:
        return [_evidence(resolved)]
    if resolved.get("package_component_determination"):
        determination = resolved["package_component_determination"]
        return [
            {
                "chunk_id": determination.get("chunk_id") or "unknown",
                "source_record_id": determination.get("source_record_id") or "unknown",
                "citation_label": determination.get("citation_label") or "N/A",
                "artifact_sha256": "selector:forest_plan_standard",
                "content_sha256": "selector:forest_plan_standard",
                "text_span": {
                    "char_start": 0,
                    "char_end": len(str(determination.get("determination_explanation") or "")),
                    "excerpt": str(determination.get("determination_explanation") or ""),
                },
            }
        ]
    if resolved.get("citation_label") and resolved.get("source_record_id"):
        return [_evidence(resolved)]
    return []


def _find_by_criteria(rows: list[Any], criteria: dict[str, str]) -> dict[str, Any] | None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        if all(str(row.get(key) or "") == value for key, value in criteria.items()):
            return row
    return None


def _parse_selector(selector: str) -> dict[str, str]:
    criteria = {}
    for item in selector.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        criteria[key.strip()] = value.strip()
    return criteria


def _confirmation_ids_by_selector(
    context: _DecisionSupportContext,
    selector_type: str,
    selector_key: str,
) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for confirmation in _dict_list(context.config.get("implementation_confirmations")):
        confirmation_id = str(confirmation.get("confirmation_id") or "")
        for selector in _dict_list(confirmation.get("source_selectors")):
            if selector.get("selector_type") != selector_type:
                continue
            value = _parse_selector(str(selector.get("selector") or "")).get(selector_key)
            if value:
                mapping.setdefault(value, []).append(confirmation_id)
    return {key: sorted(values) for key, values in mapping.items()}


def _forest_findings_by_component(context: _DecisionSupportContext) -> dict[str, dict[str, Any]]:
    return {
        str(finding.get("component_id")): finding
        for finding in _dict_list(context.payload("forest_plan_component_findings").get("findings"))
    }


def _applicable_standard_rows(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    return [
        standard
        for standard in _dict_list(
            context.payload("forest_plan_applicable_standard_coverage").get("standards")
        )
        if standard.get("applicability_status") == "applicable"
    ]


def _coverage_summary(certificate: dict[str, Any]) -> dict[str, Any]:
    return {
        "coverage_certificate_id": certificate.get("coverage_certificate_id"),
        "coverage_class": certificate.get("coverage_class"),
        "coverage_result": certificate.get("coverage_result"),
        "missing_query_variants": certificate.get("missing_query_variants") or [],
    }


def _basis_rationale(authority: dict[str, Any]) -> str:
    basis = _dict(authority.get("applicability_basis"))
    non_applicability = _dict(authority.get("non_applicability_basis"))
    return str(
        basis.get("rationale")
        or non_applicability.get("rationale")
        or "The authority was determined not applicable within the recorded search boundary."
    )


def _authority_family_id(authority: dict[str, Any]) -> str:
    rule_template = _dict(authority.get("rule_template"))
    forest_plan = _dict(authority.get("forest_plan"))
    if rule_template.get("authority_family_id"):
        return str(rule_template["authority_family_id"])
    if forest_plan.get("component_id"):
        return "nfma_forest_planning_project_consistency"
    ids = _strings(authority.get("authority_family_ids"))
    return ids[0] if ids else "unknown"


def _evidence_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [_evidence(item) for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [_evidence(value)]
    return []


def _evidence(value: Any) -> dict[str, Any]:
    evidence = _dict(value)
    span = _dict(evidence.get("evidence_span"))
    provenance = _dict(evidence.get("provenance"))
    text = str(evidence.get("text") or span.get("text") or evidence.get("text_snippet") or "")
    char_start = _int(
        evidence.get("source_char_start"),
        evidence.get("char_start"),
        span.get("source_char_start"),
        span.get("char_start"),
        evidence.get("chunk_char_start"),
        span.get("chunk_char_start"),
        0,
    )
    char_end = _int(
        evidence.get("source_char_end"),
        evidence.get("char_end"),
        span.get("source_char_end"),
        span.get("char_end"),
        evidence.get("chunk_char_end"),
        span.get("chunk_char_end"),
        char_start + len(text),
    )
    if char_end < char_start:
        char_end = char_start
    return {
        "chunk_id": str(evidence.get("chunk_id") or "unknown"),
        "source_record_id": str(
            evidence.get("source_record_id")
            or provenance.get("source_record_id")
            or "unknown"
        ),
        "citation_label": str(evidence.get("citation_label") or "N/A"),
        "artifact_sha256": str(
            evidence.get("artifact_sha256")
            or provenance.get("artifact_sha256")
            or "unknown"
        ),
        "content_sha256": str(
            evidence.get("content_sha256")
            or provenance.get("content_sha256")
            or "unknown"
        ),
        "text_span": {
            "char_start": char_start,
            "char_end": char_end,
            "excerpt": _truncate(text, 500) or "N/A",
        },
    }


def _report_markdown(report: dict[str, Any]) -> str:
    executive = report["executive_determination"]
    inventory = report["record_and_artifact_inventory"]
    authority_summary = report["applicable_authority_summary"]
    forest = report["forest_plan_consistency"]
    non_applicable = report["non_applicable_authority_boundary"]
    confirmation_count = len(report["implementation_confirmation_checklist"])
    residual_risk_count = len(report["residual_risk_register"])
    legal_risk_count = _legal_conclusion_risk_count(report)
    lines = [
        "# EA Consistency Decision Support",
        "",
        f"- Review ID: `{report['review_id']}`",
        f"- Source set: `{report['source_set_id']}`",
        f"- Status: `{executive['decision_support_status']}`",
        f"- Caveat: {executive['decision_use_caveat']}",
        "",
        "## How To Use This Document",
        "",
        _decision_support_use_note(),
        "",
        "## Review Snapshot",
        "",
    ]
    lines.extend(f"- {item}" for item in _review_snapshot_items(report))
    lines.extend(
        [
            "",
            "## Record and Artifact Inventory",
            "",
            (
                "This inventory identifies the generated review package and validation-owned "
                "artifacts used to build the decision-support rendering."
            ),
            "",
            f"- Package files: `{inventory['package_file_count']}`",
            f"- Package chunks: `{inventory['package_chunk_count']}`",
            f"- Generated rule pack ready: `{inventory['generated_rule_pack_ready']}`",
            "",
            "## Applicable Authority Summary",
            "",
            (
                "The authority summary groups generated applicable findings before the full "
                "evidence table. The table is ordered by rule ID and keeps EA package evidence "
                "separate from source-library evidence."
            ),
            "",
            f"- Applicable authorities: `{authority_summary['applicable_authority_count']}`",
            f"- Status counts: `{_format_counts(authority_summary['status_counts'])}`",
            f"- Category counts: `{_format_counts(authority_summary['category_counts'])}`",
            "",
            "## Authority Findings",
            "",
            (
                "Summary: generated applicable authority findings with package and source "
                "citations; implementation-confirmation IDs identify follow-up checks without "
                "creating additional compliance findings."
            ),
            "",
            "| Rule | Category | Status | EA evidence | Source evidence | Implementation confirmations |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["authority_findings"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row["rule_id"]),
                    _md_cell(row.get("authority_category")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(_evidence_cell(row.get("ea_package_evidence", []))),
                    _md_cell(_evidence_cell(row.get("source_library_evidence", []))),
                    _md_cell(", ".join(row.get("implementation_confirmation_ids", [])) or "None"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Forest Plan Consistency",
            "",
            f"- Component findings: `{forest['component_finding_count']}`",
            f"- Supported/applicable components: `{forest['supported_component_count']}`",
            f"- Not-applicable components: `{forest['not_applicable_component_count']}`",
            f"- Gap count: `{forest['gap_count']}`",
            f"- Applicable standards: `{forest['applicable_standard_count']}`",
            f"- Applied standards: `{forest['applied_standard_count']}`",
            f"- Plan Consistency Table source: `{forest['plan_consistency_table_package_record_id']}`",
            "",
            "## Applicable Forest Plan Standards",
            "",
            (
                "Summary: generated applicable Forest Plan standards with package evidence "
                "and Forest Plan source evidence; standards remain separate from broader "
                "not-applicable component rows."
            ),
            "",
            "| Standard | Compliance | Package evidence | Forest Plan evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["applicable_forest_plan_standards"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("component_key")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(_evidence_cell(row.get("package_evidence", []))),
                    _md_cell(_evidence_cell(row.get("forest_plan_evidence", []))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Non-Applicable Authority Boundary",
            "",
            (
                "Summary: non-applicable authorities stay out of compliance findings and remain "
                "available through the generated appendix and search-coverage certificates."
            ),
            "",
            f"- Non-applicable authorities: `{non_applicable['non_applicable_authority_count']}`",
            f"- Category counts: `{_format_counts(non_applicable['category_counts'])}`",
            f"- Full appendix: `{non_applicable['appendix_path']}`",
            f"- Coverage certificates: `{non_applicable['coverage_certificates_path']}`",
            "",
            "## Implementation Confirmation Checklist",
            "",
            (
                f"Summary: `{confirmation_count}` evidence-linked implementation confirmations "
                "require reviewer confirmation. These rows are not compliance findings and do "
                "not prove final implementation completion."
            ),
            "",
            "| Confirmation | Status | Decision-support wording | Evidence selectors |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["implementation_confirmation_checklist"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("label")),
                    _md_cell(row.get("status")),
                    _md_cell(row.get("allowed_report_wording")),
                    _md_cell(_selector_cell(row.get("source_selectors", []))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Residual Risk Register",
            "",
            (
                f"Summary: `{residual_risk_count}` deterministic decision-support risk notes; "
                f"legal-conclusion flags: `{legal_risk_count}`. Risk notes preserve source "
                "artifact pointers and do not replace responsible official or counsel judgment."
            ),
            "",
        ]
    )
    for risk in report["residual_risk_register"]:
        lines.append(
            f"- `{risk['risk_id']}`: `{risk['category']}` / `{risk['severity']}` - "
            f"{risk['rationale']} Source: `{risk['source_artifact_path']}` selector "
            f"`{risk['source_selector']}`."
        )
    lines.extend(
        [
            "",
            "## Validation and Replay",
            "",
            "Summary: replay commands regenerate or re-evaluate this report from audited artifacts.",
            "",
            f"- Passed: `{report['validation_and_replay']['passed']}`",
            f"- Manifest: `{report['manifest']['schema_version']}`",
        ]
    )
    for command in report["validation_and_replay"]["replay_commands"]:
        lines.append(f"- `{command}`")
    return "\n".join(lines) + "\n"


def _report_pdf_pages(report: dict[str, Any]) -> list[list[str]]:
    forest = report["forest_plan_consistency"]
    authority_summary = report["applicable_authority_summary"]
    non_applicable = report["non_applicable_authority_boundary"]
    lines = [
        "EA Consistency Decision Support",
        f"Review ID: {report['review_id']}",
        f"Source set: {report['source_set_id']}",
        (
            "Bottom-line determination: "
            f"{report['executive_determination']['decision_support_status']} "
            "decision support from generated artifacts."
        ),
        "Caveat: " + report["executive_determination"]["decision_use_caveat"],
        "",
        "How To Use This Document",
    ]
    lines.extend(_wrap_pdf_line(_decision_support_use_note()))
    lines.extend(["", "Review Snapshot"])
    for item in _review_snapshot_items(report):
        lines.extend(_wrap_pdf_line("- " + item))
    lines.extend(
        [
            "",
            "Table Summaries",
            (
                "Authority Findings: "
                f"{authority_summary['applicable_authority_count']} generated applicable "
                f"findings, categories {_format_counts(authority_summary['category_counts'])}."
            ),
            (
                "Forest Plan Standards: "
                f"{forest['applied_standard_count']} of {forest['applicable_standard_count']} "
                "applicable standards applied with package and plan evidence."
            ),
            (
                "Non-Applicable Authority Boundary: "
                f"{non_applicable['non_applicable_authority_count']} authorities; appendix "
                f"{non_applicable['appendix_path']}."
            ),
            (
                "Implementation Confirmations: "
                f"{len(report['implementation_confirmation_checklist'])} evidence-linked rows "
                "requiring reviewer confirmation."
            ),
            (
                "Residual Risks: "
                f"{len(report['residual_risk_register'])} decision-support notes; "
                f"{_legal_conclusion_risk_count(report)} legal-conclusion flags."
            ),
        ]
    )
    lines.extend(
        [
            "",
            "Record and Artifact Inventory",
            f"Package files: {report['record_and_artifact_inventory']['package_file_count']}",
            f"Package chunks: {report['record_and_artifact_inventory']['package_chunk_count']}",
            (
                "Generated rule pack ready: "
                f"{report['record_and_artifact_inventory']['generated_rule_pack_ready']}"
            ),
        ]
    )
    lines.extend(
        [
            "",
            "Applicable Authority Findings (ordered by rule ID)",
        ]
    )
    for index, row in enumerate(report["authority_findings"], start=1):
        lines.extend(
            _wrap_pdf_line(
                f"{index}. {row['rule_id']} ({row.get('authority_category')}) - "
                f"{row.get('compliance_status')} - EA: "
                f"{_evidence_cell(row.get('ea_package_evidence', []))} - Source: "
                f"{_evidence_cell(row.get('source_library_evidence', []))} - Confirmations: "
                f"{', '.join(row.get('implementation_confirmation_ids', [])) or 'None'}"
            )
        )
    lines.extend(
        [
            "",
            "Applicable Forest Plan Standards",
            (
                "Summary: standards shown here are the applicable subset from generated "
                "Forest Plan coverage."
            ),
        ]
    )
    for index, row in enumerate(report["applicable_forest_plan_standards"], start=1):
        lines.extend(
            _wrap_pdf_line(
                f"{index}. {row.get('component_key')} - {row.get('compliance_status')} - "
                f"Package: {_evidence_cell(row.get('package_evidence', []))} - "
                f"Plan: {_evidence_cell(row.get('forest_plan_evidence', []))}"
            )
        )
    lines.extend(
        [
            "",
            "Non-Applicable Authority Boundary",
            (
                "Summary: non-applicable authorities are excluded from compliance findings; "
                f"full appendix {non_applicable['appendix_path']} and coverage certificates "
                f"{non_applicable['coverage_certificates_path']}."
            ),
            "",
            "Implementation Confirmations",
            "Summary: confirmation rows require reviewer confirmation and are not findings.",
        ]
    )
    for index, row in enumerate(report["implementation_confirmation_checklist"], start=1):
        lines.extend(
            _wrap_pdf_line(
                f"{index}. {row.get('label')} - {row.get('status')} - "
                f"{row.get('allowed_report_wording')}"
            )
        )
    lines.extend(
        [
            "",
            "Residual Risks",
            (
                "Summary: deterministic decision-support risk notes with source artifact "
                "pointers, not legal conclusions."
            ),
        ]
    )
    for row in report["residual_risk_register"]:
        lines.extend(
            _wrap_pdf_line(
                f"{row['risk_id']} - {row['rationale']} Source: "
                f"{row['source_artifact_path']} selector {row['source_selector']}."
            )
        )
    return _paginate_pdf_lines(lines, max_lines=44)


def _decision_support_use_note() -> str:
    return (
        "Use this document to inspect generated authority, Forest Plan, implementation "
        "confirmation, residual-risk, and validation evidence for the review. It supports "
        "review and does not replace responsible official, line officer, counsel, or "
        "specialist judgment."
    )


def _review_snapshot_items(report: dict[str, Any]) -> list[str]:
    executive = report["executive_determination"]
    authority_summary = report["applicable_authority_summary"]
    forest = report["forest_plan_consistency"]
    non_applicable = report["non_applicable_authority_boundary"]
    confirmations = report["implementation_confirmation_checklist"]
    residual_risks = report["residual_risk_register"]
    return [
        (
            "Bottom-line determination: "
            f"{executive['decision_support_status']} decision-support status from generated "
            "artifacts; not a legal sufficiency determination or final agency decision."
        ),
        (
            "Authority categories: "
            f"{_format_counts(authority_summary['category_counts'])}; applicable authority "
            f"findings: {authority_summary['applicable_authority_count']}; status counts: "
            f"{_format_counts(authority_summary['status_counts'])}."
        ),
        (
            "Forest Plan basis: "
            f"{forest['plan_consistency_table_package_record_id']} "
            f"{forest.get('plan_consistency_table_label', 'Plan Consistency Table')} plus "
            f"{forest['component_finding_count']} generated component rows "
            f"({forest['supported_component_count']} supported/applicable, "
            f"{forest['not_applicable_component_count']} not applicable, "
            f"{forest['gap_count']} gaps)."
        ),
        (
            "Applicable standards: "
            f"{forest['applied_standard_count']} of {forest['applicable_standard_count']} "
            "applicable Forest Plan standards are applied with package and plan evidence."
        ),
        (
            "Non-applicable boundary: "
            f"{non_applicable['non_applicable_authority_count']} authorities remain "
            "non-applicable with search coverage and appendix pointers."
        ),
        (
            "Implementation confirmations: "
            f"{len(confirmations)} evidence-linked checklist rows require confirmation and "
            "are not additional compliance findings."
        ),
        (
            "Residual risks: "
            f"{len(residual_risks)} deterministic decision-support notes; "
            f"{_legal_conclusion_risk_count(report)} legal-conclusion flags."
        ),
        (
            "Validation: "
            f"report validation passed={report['validation_and_replay']['passed']}; "
            f"manifest schema {report['manifest']['schema_version']}."
        ),
    ]


def _legal_conclusion_risk_count(report: dict[str, Any]) -> int:
    return sum(
        1
        for risk in report["residual_risk_register"]
        if risk.get("legal_conclusion") is True
    )


def _format_counts(counts: Any) -> str:
    rows = _dict(counts)
    if not rows:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in rows.items())


def _selector_cell(selectors: Any) -> str:
    parts = []
    for selector in _dict_list(selectors):
        artifact_path = str(selector.get("artifact_path") or "").strip()
        selector_text = str(selector.get("selector") or "").strip()
        if artifact_path and selector_text:
            parts.append(f"{artifact_path} :: {selector_text}")
        elif artifact_path:
            parts.append(artifact_path)
        elif selector_text:
            parts.append(selector_text)
    return "; ".join(parts) or "N/A"


def _evidence_cell(evidence_rows: list[dict[str, Any]]) -> str:
    if not evidence_rows:
        return "N/A"
    evidence = evidence_rows[0]
    return (
        f"{evidence.get('citation_label')} - "
        f"{_truncate((evidence.get('text_span') or {}).get('excerpt', ''), 180)}"
    )


def _trace(
    trace_id: str,
    trace_type: str,
    source_artifact_path: Path,
    source_selector: str,
) -> dict[str, str]:
    return {
        "trace_id": trace_id,
        "trace_type": trace_type,
        "source_artifact_path": str(source_artifact_path),
        "source_selector": source_selector,
    }


def _selector(path: Path, selector: str) -> dict[str, str]:
    return {"artifact_path": str(path), "selector": selector}
