from __future__ import annotations

from pathlib import Path
import textwrap

from .compliance_outputs_audit import _accuracy_audit_rows
from .compliance_outputs_common import _count_phrase
from .compliance_outputs_common import _forest_plan_readiness_signal
from .compliance_outputs_common import _matrix_row_marker
from .compliance_outputs_common import _render_manifest_row
from .compliance_outputs_common import _review_gate_phrase
from .compliance_outputs_common import _row_set_sha256
from .compliance_outputs_common import _truncate
from .compliance_outputs_common import _utc_now
from .compliance_outputs_common import _yes_no_sentence
from .compliance_outputs_forest_plan import _forest_component_cell
from .compliance_outputs_forest_plan import _forest_decision_support_cell
from .compliance_outputs_forest_plan import _forest_direction_cell
from .compliance_outputs_forest_plan import _forest_ea_support_cell
from .compliance_outputs_forest_plan import _forest_plan_basis_cell
from .compliance_outputs_forest_plan import _forest_trace_caveats_cell
from .compliance_outputs_matrix import _authority_basis_cell
from .compliance_outputs_matrix import _evidence_support_cell
from .compliance_outputs_matrix import _nepa_decision_support_cell
from .compliance_outputs_matrix import _nepa_signer_question_cell
from .compliance_outputs_matrix import _nepa_topic_cell
from .compliance_outputs_matrix import _responsible_official_readout_rows
from .compliance_outputs_matrix import _trace_caveats_cell
from .pdf_object_writer import write_paginated_line_pdf


COMPLIANCE_MATRIX_RENDER_MANIFEST_SCHEMA_VERSION = "compliance-matrix-render-manifest-v1"


def write_compliance_matrix_pdf(path: Path, matrix: dict) -> None:
    pages = _matrix_pdf_pages(matrix)
    write_paginated_line_pdf(
        path,
        pages,
        title="Compliance Matrix",
        font_name="Courier",
        text_transform=_pdf_text,
    )


def build_compliance_matrix_render_manifest(
    *,
    matrix: dict,
    markdown: str,
    pdf_path: Path,
) -> dict:
    rows = []
    for index, row in enumerate(matrix.get("rows", []), start=1):
        rule_id = str(row.get("rule_id") or "")
        marker = _matrix_row_marker("authority", rule_id)
        rows.append(
            _render_manifest_row(
                row_class="applicable_authority",
                row=row,
                row_order=index,
                section="NEPA / Authority Compliance",
                table_id="nepa_authority_compliance",
                json_selector=f"rows[rule_id={rule_id}]",
                markdown_marker=marker,
                row_identity={"rule_id": rule_id},
            )
        )
    forest_section = matrix.get("forest_plan_compliance") or {}
    forest_rows = forest_section.get("rows") if isinstance(forest_section, dict) else []
    for index, row in enumerate(forest_rows or [], start=1):
        component_id = str(row.get("component_id") or "")
        marker = _matrix_row_marker("forest-plan", component_id)
        rows.append(
            _render_manifest_row(
                row_class="forest_plan_component",
                row=row,
                row_order=index,
                section="Forest Plan Compliance",
                table_id="forest_plan_compliance",
                json_selector=f"forest_plan_compliance.rows[component_id={component_id}]",
                markdown_marker=marker,
                row_identity={
                    "component_id": component_id,
                    "component_key": row.get("component_key"),
                    "component_type": row.get("component_type"),
                },
            )
        )
    missing_markdown_markers = [
        row["markdown_marker"] for row in rows if row["markdown_marker"] not in markdown
    ]
    pdf_header_valid = (
        pdf_path.exists()
        and pdf_path.stat().st_size > 0
        and pdf_path.read_bytes().startswith(b"%PDF-")
    )
    authority_row_count = sum(1 for row in rows if row["row_class"] == "applicable_authority")
    forest_plan_row_count = sum(1 for row in rows if row["row_class"] == "forest_plan_component")
    passed = not missing_markdown_markers and pdf_header_valid
    return {
        "schema_version": COMPLIANCE_MATRIX_RENDER_MANIFEST_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": matrix.get("review_id"),
        "source_set_id": matrix.get("source_set_id"),
        "matrix_schema_version": matrix.get("schema_version"),
        "matrix_row_count": len(matrix.get("rows", [])),
        "forest_plan_matrix_row_count": len(forest_rows or []),
        "summary": {
            "passed": passed,
            "row_count": len(rows),
            "authority_row_count": authority_row_count,
            "forest_plan_row_count": forest_plan_row_count,
            "markdown_marker_count": len(rows) - len(missing_markdown_markers),
            "missing_markdown_markers": missing_markdown_markers,
            "pdf_path": str(pdf_path),
            "pdf_header_valid": pdf_header_valid,
            "row_set_sha256": _row_set_sha256(rows),
        },
        "rows": rows,
    }


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
    lines.extend(["", "Responsible Official Readout", ""])
    lines.extend(
        _pdf_wrapped_table_lines(
            ["Signing question", "Current decision-support signal"],
            [[row["check"], row["signal"]] for row in _responsible_official_readout_rows(matrix)],
            [48, 132],
        )
    )
    lines.extend(["", "Accuracy Audit", ""])
    lines.extend(
        _pdf_wrapped_table_lines(
            ["Check", "Result", "Evidence"],
            [[row["check"], row["result"], row["evidence"]] for row in _accuracy_audit_rows(matrix)],
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
        forest_summary = forest_plan_compliance.get("summary", {})
        lines.extend(
            [
                "",
                "Forest Plan Compliance",
                f"Rows: {forest_summary.get('row_count', 0)}",
                f"Decision-support status: {_forest_plan_readiness_signal(forest_summary)}",
                (
                    "Applicable standard rows: "
                    f"{forest_summary.get('applicable_standard_row_count', 0)}"
                ),
                "",
            ]
        )
        lines.extend(
            _pdf_wrapped_table_lines(
                ["Component", "Direction", "Finding", "EA support", "Plan basis", "Trace"],
                [_forest_plan_pdf_table_row(row) for row in forest_plan_compliance.get("rows", [])],
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
