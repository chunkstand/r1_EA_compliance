from __future__ import annotations

from pathlib import Path
from typing import Any

from .pdf_object_writer import write_paginated_line_pdf
from .project_sow_package_common import _check
from .project_sow_package_common import _intake_adjudication_summary
from .project_sow_package_common import _strings
from .project_sow_package_common import _truncate
from .project_sow_package_graph import _has_canonical_resource_path
from .project_sow_package_intake_support import _expected_resource_area_ids

def _render_markdown(package: dict[str, Any]) -> str:
    lines = [
        f"# {package['project_name']} Requirements Package",
        "",
        "This generated package scopes specialist work needed to prepare a defensible NEPA EA package. It is planning support, not legal advice or a final compliance determination.",
        "",
        "## Reviewer Snapshot",
        "",
    ]
    reviewer_summary = package["reviewer_summary"]
    snapshot = reviewer_summary["snapshot"]
    lines.extend(
        [
            "| Field | Value |",
            "| --- | --- |",
            f"| Project ID | `{package['project_id']}` |",
            f"| Forest | {snapshot['forest']} |",
            f"| Districts | {', '.join(snapshot['districts'])} |",
            f"| Project type | `{snapshot['project_type']}` |",
            f"| NEPA level | `{snapshot['nepa_level']}` |",
            f"| SOW scopes | `{snapshot['resource_scope_count']}` |",
            f"| Proposed-action resource areas | `{snapshot['proposed_action_resource_area_count']}` |",
            f"| Observed reports in calibration set | `{snapshot['observed_specialist_report_count']}` |",
            f"| Unresolved resource areas | `{len(snapshot['missing_or_uncovered_resource_area_ids'])}` |",
            f"| Calibration gaps | `{len(snapshot['calibration_gap_resource_area_ids'])}` |",
            f"| Adjudication status | `{snapshot['adjudication_status']}` |",
            "| Intake evidence graph | "
            f"`{snapshot['intake_evidence_graph_node_count']}` nodes / "
            f"`{snapshot['intake_evidence_graph_edge_count']}` edges |",
            "",
            "### Review Checklist",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in reviewer_summary["review_checklist"])
    lines.extend(
        [
            "",
            "### Package Boundaries",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in reviewer_summary["package_boundaries"])
    lines.extend(
        [
            "",
            "## Intake",
        ]
    )
    intake = package["intake_summary"]
    lines.extend(
        [
            f"- Project ID: `{package['project_id']}`",
            f"- Source set: `{package['source_set_id']}`",
            f"- Forest: {intake.get('forest')}",
            f"- Districts: {', '.join(intake.get('districts') or [])}",
            f"- Project type: `{intake.get('project_type')}`",
            f"- NEPA level: `{intake.get('nepa_level')}`",
            f"- Federal land action count: `{intake.get('federal_land_action_count')}`",
            f"- Proposed action resource areas: `{len(intake.get('proposed_action_resource_area_ids') or [])}`",
            f"- Observed specialist/supporting reports: `{intake.get('observed_specialist_report_count')}`",
            f"- Adjudication status: `{intake.get('adjudication_status')}`",
            "",
            "## Resource Scopes",
            "",
            "| Scope | Discipline | Covered resource areas | Required deliverables | Optional deliverables |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for scope in package["resource_scope_records"]:
        lines.append(
            f"| {scope['resource_name']} | `{scope['discipline']}` | "
            f"{', '.join(f'`{item}`' for item in scope['covered_resource_area_ids'])} | "
            f"{len(scope['required_deliverables'])} | {len(scope['optional_deliverables'])} |"
        )
    for scope in package["resource_scope_records"]:
        lines.extend(
            [
                "",
                f"### {scope['resource_name']}",
                "",
                f"- Scope ID: `{scope['resource_scope_id']}`",
                f"- Discipline: `{scope['discipline']}`",
                f"- Selection reasons: {', '.join(scope['selection_reasons'])}",
                f"- Covered resource areas: {', '.join(f'`{item}`' for item in scope['covered_resource_area_ids'])}",
                f"- Authority families: {', '.join(f'`{item}`' for item in scope['authority_family_ids'])}",
                "",
                "Tasks:",
            ]
        )
        lines.extend(f"- {task}" for task in scope["sow_tasks"])
        lines.append("")
        lines.append("Required deliverables:")
        lines.extend(f"- {deliverable}" for deliverable in scope["required_deliverables"])
        lines.append("")
        lines.append("Optional deliverables:")
        lines.extend(f"- {deliverable}" for deliverable in scope["optional_deliverables"])
        lines.append("")
        lines.append("Contract terms:")
        lines.extend(
            [
                f"- Reviewer role: {scope['reviewer_role']}",
                f"- Review timing: {scope['review_timing']}",
                "- Assumptions:",
            ]
        )
        lines.extend(f"  - {item}" for item in scope["assumptions"])
        lines.append("- Dependencies:")
        lines.extend(f"  - {item}" for item in scope["dependencies"])
        lines.append("- Acceptance criteria:")
        lines.extend(f"  - {item}" for item in scope["acceptance_criteria"])
        lines.append("- Reviewer signoff fields:")
        lines.extend(f"  - `{item}`" for item in scope["reviewer_signoff_fields"])
        lines.append("")
        lines.append("Defensibility checks:")
        lines.extend(f"- {check}" for check in scope["defensibility_checks"])
    lines.extend(["", "## Authority Requirement Matrix"])
    for row in package["authority_requirement_matrix"]:
        lines.append(
            f"- `{row['authority_family_id']}`: {', '.join(f'`{scope_id}`' for scope_id in row['resource_scope_ids'])}"
        )
    lines.extend(
        [
            "",
            "## Resource Analysis Coverage",
            "",
            "| Resource area | Coverage status | SOW scopes | Observed reports |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in package["resource_analysis_matrix"]:
        report_titles = [
            str(report["title"]) for report in row["actual_specialist_reports"]
        ]
        lines.append(
            f"| `{row['resource_area_id']}` | `{row['coverage_status']}` | "
            f"{', '.join(f'`{scope_id}`' for scope_id in row['selected_resource_scope_ids']) or 'none'} | "
            f"{', '.join(report_titles) or 'none observed'} |"
        )
    graph = package["intake_evidence_graph"]
    lines.extend(
        [
            "",
            "## Intake Evidence Graph",
            f"- Nodes: `{graph['node_count']}`",
            f"- Edges: `{graph['edge_count']}`",
            "- Required path: `proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope`",
        ]
    )
    for row in package["resource_analysis_matrix"]:
        if row["expected_from_proposed_action"]:
            status = (
                "present"
                if _has_canonical_resource_path(graph, row["resource_area_id"])
                else "missing"
            )
            lines.append(f"- `{row['resource_area_id']}` path: `{status}`")
    lines.extend(["", "## Validation"])
    for check in package["validation"]["checks"]:
        status = "passed" if check["passed"] else "failed"
        lines.append(f"- `{check['name']}`: `{status}`")
    return "\n".join(lines) + "\n"


def _reviewer_summary(
    *,
    intake: dict[str, Any],
    project_id: str,
    source_set_id: str,
    scope_records: list[dict[str, Any]],
    resource_analysis_matrix: list[dict[str, Any]],
    observed_specialist_reports: list[dict[str, Any]],
    intake_evidence_graph: dict[str, Any],
) -> dict[str, Any]:
    adjudication_summary = _intake_adjudication_summary(intake)
    unresolved_statuses = {
        "missing_sow_scope",
        "observed_not_derived_from_proposed_action",
    }
    missing_or_uncovered = [
        row["resource_area_id"]
        for row in resource_analysis_matrix
        if row["coverage_status"] in unresolved_statuses
    ]
    calibration_gap_resource_area_ids = [
        row["resource_area_id"]
        for row in resource_analysis_matrix
        if row["coverage_status"] == "sow_required_no_observed_report_in_calibration"
    ]
    return {
        "package_boundaries": [
            "Planning support only; not legal advice or a final agency decision.",
            "JSON is canonical; Markdown and PDF are renderings from the same package JSON.",
            "SOW scope selection is not an applicability decision or compliance finding.",
            "Ignored source_library outputs remain local generated artifacts unless policy changes.",
        ],
        "review_checklist": [
            "Confirm the proposed action and federal land actions are complete.",
            "Assign a responsible specialist for each required resource scope.",
            "Confirm each proposed-action resource area has an evidence-backed graph path.",
            "Resolve any missing resource-area requests before using the package for contracting.",
            "Use observed East Crazies reports only as calibration evidence, not as legal precedent.",
        ],
        "schema_version": "project-sow-reviewer-summary-v0",
        "snapshot": {
            "adjudication_decision_counts": adjudication_summary["decision_counts"],
            "adjudication_item_count": adjudication_summary["item_count"],
            "adjudication_status": adjudication_summary["status"],
            "districts": _strings(intake.get("districts")),
            "forest": intake.get("forest"),
            "intake_evidence_graph_edge_count": int(intake_evidence_graph.get("edge_count") or 0),
            "intake_evidence_graph_node_count": int(intake_evidence_graph.get("node_count") or 0),
            "calibration_gap_resource_area_ids": calibration_gap_resource_area_ids,
            "missing_or_uncovered_resource_area_ids": missing_or_uncovered,
            "nepa_level": intake.get("nepa_level"),
            "observed_specialist_report_count": len(observed_specialist_reports),
            "project_id": project_id,
            "project_name": intake.get("project_name"),
            "project_type": intake.get("project_type"),
            "proposed_action_resource_area_count": len(_expected_resource_area_ids(intake)),
            "resource_scope_count": len(scope_records),
            "source_set_id": source_set_id,
        },
    }


def _render_pdf_lines(package: dict[str, Any]) -> list[str]:
    reviewer_summary = package["reviewer_summary"]
    snapshot = reviewer_summary["snapshot"]
    lines = [
        f"{package['project_name']} Requirements Package",
        "Reviewer Snapshot",
        f"Project ID: {package['project_id']}",
        f"Forest: {snapshot['forest']}",
        f"Districts: {', '.join(snapshot['districts'])}",
        f"Project type: {snapshot['project_type']}",
        f"NEPA level: {snapshot['nepa_level']}",
        f"Resource Scope Count: {snapshot['resource_scope_count']}",
        f"Proposed-action resource areas: {snapshot['proposed_action_resource_area_count']}",
        f"Observed reports in calibration set: {snapshot['observed_specialist_report_count']}",
        f"Unresolved resource areas: {len(snapshot['missing_or_uncovered_resource_area_ids'])}",
        f"Calibration gaps: {len(snapshot['calibration_gap_resource_area_ids'])}",
        f"Adjudication status: {snapshot['adjudication_status']}",
        (
            "Intake evidence graph: "
            f"{snapshot['intake_evidence_graph_node_count']} nodes / "
            f"{snapshot['intake_evidence_graph_edge_count']} edges"
        ),
        "",
        "Package Boundaries",
    ]
    lines.extend(f"- {item}" for item in reviewer_summary["package_boundaries"])
    lines.extend(["", "Review Checklist"])
    lines.extend(f"- {item}" for item in reviewer_summary["review_checklist"])
    lines.extend(["", "Resource Scopes"])
    for scope in package["resource_scope_records"]:
        lines.append(
            f"- {scope['resource_scope_id']}: {scope['resource_name']} "
            f"({len(scope['required_deliverables'])} required, "
            f"{len(scope['optional_deliverables'])} optional deliverables)"
        )
    lines.extend(["", "Contract Terms"])
    for scope in package["resource_scope_records"]:
        lines.append(f"- {scope['resource_scope_id']} reviewer: {scope['reviewer_role']}")
        lines.append(f"  timing: {scope['review_timing']}")
        lines.append(
            f"  acceptance criteria: {len(scope['acceptance_criteria'])}; "
            f"assumptions: {len(scope['assumptions'])}; "
            f"dependencies: {len(scope['dependencies'])}"
        )
        lines.append(
            "  signoff fields: " + ", ".join(scope["reviewer_signoff_fields"])
        )
    lines.extend(["", "Resource Analysis Coverage"])
    for row in package["resource_analysis_matrix"]:
        reports = ", ".join(
            str(report["title"]) for report in row["actual_specialist_reports"]
        )
        lines.append(
            f"- {row['resource_area_id']}: {row['coverage_status']}; "
            f"SOW scopes {', '.join(row['selected_resource_scope_ids']) or 'none'}; "
            f"reports {reports or 'none observed'}"
        )
    lines.extend(
        [
            "",
            "Intake Evidence Graph",
            "Required path: proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope",
            "",
            "Validation",
        ]
    )
    for check in package["validation"]["checks"]:
        status = "passed" if check["passed"] else "failed"
        lines.append(f"- {check['name']}: {status}")
    return [_truncate(line, 150) for line in lines]


def _rendering_validation_checks(markdown: str, pdf_lines: list[str]) -> list[dict[str, Any]]:
    required_markdown_sections = [
        "# ",
        "## Reviewer Snapshot",
        "## Intake",
        "## Resource Scopes",
        "Contract terms:",
        "## Resource Analysis Coverage",
        "## Intake Evidence Graph",
        "## Validation",
    ]
    required_pdf_items = [
        "Reviewer Snapshot",
        "Package Boundaries",
        "Review Checklist",
        "Resource Scopes",
        "Contract Terms",
        "Resource Analysis Coverage",
        "Intake Evidence Graph",
        "Validation",
    ]
    pdf_text = "\n".join(pdf_lines)
    missing_markdown_sections = [
        section for section in required_markdown_sections if section not in markdown
    ]
    missing_pdf_items = [item for item in required_pdf_items if item not in pdf_text]
    return [
        _check(
            name="project_sow_markdown_required_sections_present",
            passed=not missing_markdown_sections,
            details={"missing_sections": missing_markdown_sections},
        ),
        _check(
            name="project_sow_pdf_required_items_present",
            passed=not missing_pdf_items,
            details={"missing_items": missing_pdf_items},
        ),
    ]


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
    return pages or [["Project SOW Requirements Package"]]


def _write_simple_pdf(path: Path, pages: list[list[str]], *, title: str) -> None:
    write_paginated_line_pdf(
        path,
        pages,
        title=title,
        text_transform=_pdf_text,
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
