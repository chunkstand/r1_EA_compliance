from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .forest_plan_component_adjudication_common import _adjudication_items
from .forest_plan_component_adjudication_common import _component_source_ref
from .forest_plan_component_adjudication_common import _current_status
from .forest_plan_component_adjudication_common import _evidence_refs
from .forest_plan_component_adjudication_common import _queue_items
from .forest_plan_component_adjudication_common import _string_values
from .forest_plan_component_adjudication_common import _unique_ref_values
from .forest_plan_component_adjudication_common import _utc_now

def _template_item(
    *,
    item: dict[str, Any],
    finding: dict[str, Any] | None,
    component: dict[str, Any] | None,
) -> dict[str, Any]:
    finding = finding or {}
    component = component or {}
    plan_source_evidence_refs = _evidence_refs(finding.get("plan_source_evidence") or [])
    package_evidence_refs = _evidence_refs(finding.get("package_evidence") or [])
    component_source_ref = _component_source_ref(
        component=component,
        plan_source_evidence_refs=plan_source_evidence_refs,
    )
    return {
        "item_id": item.get("item_id"),
        "finding_id": item.get("finding_id"),
        "component_id": item.get("component_id"),
        "component_source_ref": component_source_ref,
        "component_type": finding.get("component_type") or component.get("component_type"),
        "queue_reason": item.get("reason"),
        "severity": item.get("severity"),
        "current": _current_status(finding=finding, item=item),
        "expected_current": _current_status(finding=finding, item=item),
        "disposition": "pending",
        "adjudicated_at": "",
        "adjudicated_by": [],
        "source_type": "",
        "rationale": "",
        "reviewer_notes": "",
        "matched_context": (finding.get("applicability_basis") or {}).get("matched_context") or {},
        "component_context": (finding.get("applicability_basis") or {}).get("component_context") or {},
        "evidence_counts": {
            "plan_source_evidence_count": len(finding.get("plan_source_evidence") or []),
            "package_evidence_count": len(finding.get("package_evidence") or []),
        },
        "plan_source_record_ids": _unique_ref_values(
            plan_source_evidence_refs,
            "source_record_id",
        ),
        "package_source_record_ids": _unique_ref_values(
            package_evidence_refs,
            "source_record_id",
        ),
        "plan_source_citations": _unique_ref_values(
            plan_source_evidence_refs,
            "citation_label",
        ),
        "package_evidence_citations": _unique_ref_values(
            package_evidence_refs,
            "citation_label",
        ),
        "plan_source_evidence_refs": plan_source_evidence_refs,
        "package_evidence_refs": package_evidence_refs,
        "component_text": component.get("component_text"),
        "package_evidence_terms": (
            (finding.get("applicability_basis") or {}).get("package_evidence_terms") or []
        ),
    }

def _template_summary(
    *,
    review_dir: Path,
    output_path: Path,
    markdown_path: Path,
    findings_report: dict[str, Any],
    queue: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    component_type_counts = Counter(str(item.get("component_type") or "") for item in items)
    reason_counts = Counter(str(item.get("queue_reason") or "") for item in items)
    summary = findings_report.get("summary") if isinstance(findings_report.get("summary"), dict) else {}
    return {
        "schema_version": "forest-plan-component-adjudication-template-summary-v0",
        "created_at": _utc_now(),
        "review_id": findings_report.get("review_id") or summary.get("review_id"),
        "source_set_id": findings_report.get("source_set_id") or summary.get("source_set_id"),
        "review_dir": str(review_dir),
        "output_path": str(output_path),
        "markdown_path": str(markdown_path),
        "component_findings_path": str(review_dir / "forest_plan_component_findings.json"),
        "reviewer_resolution_queue_path": str(
            review_dir / "forest_plan_reviewer_resolution_queue.json"
        ),
        "queue_item_count": len(_queue_items(queue)),
        "template_item_count": len(items),
        "pending_item_count": len(items),
        "component_type_counts": dict(sorted(component_type_counts.items())),
        "queue_reason_counts": dict(sorted(reason_counts.items())),
        "instructions": (
            "Replace disposition=pending with a resolved disposition, then fill adjudicated_at, "
            "adjudicated_by, source_type, and rationale before running "
            "forest-plan-component-adjudication-eval."
        ),
    }

def _template_markdown(template: dict[str, Any]) -> str:
    summary = template.get("summary") if isinstance(template.get("summary"), dict) else {}
    items = _adjudication_items(template)
    dispositions = ", ".join(str(item) for item in template.get("resolved_dispositions") or [])
    lines = [
        "# Forest Plan Component Adjudication Worklist",
        "",
        f"- Review ID: {summary.get('review_id')}",
        f"- Source set ID: {summary.get('source_set_id')}",
        f"- Queue items: {summary.get('queue_item_count', 0)}",
        f"- Pending items: {summary.get('pending_item_count', 0)}",
        f"- JSON template: {summary.get('output_path')}",
        "",
        "Resolved dispositions:",
        "",
        dispositions or "(none)",
        "",
        "For each item, replace `pending` in the JSON template with a resolved disposition and fill "
        "`adjudicated_at`, `adjudicated_by`, `source_type`, and `rationale` before running the "
        "adjudication eval.",
        "",
    ]
    for index, item in enumerate(items, start=1):
        current = item.get("current") if isinstance(item.get("current"), dict) else {}
        evidence_counts = (
            item.get("evidence_counts") if isinstance(item.get("evidence_counts"), dict) else {}
        )
        lines.extend(
            [
                f"## {index}. {item.get('component_id')}",
                "",
                f"- Item ID: {item.get('item_id')}",
                f"- Finding ID: {item.get('finding_id')}",
                f"- Component type: {item.get('component_type')}",
                f"- Queue reason: {item.get('queue_reason')}",
                "- Disposition: pending",
                f"- Finding status: {current.get('finding_status')}",
                f"- Applicability status: {current.get('applicability_status')}",
                f"- Compliance status: {current.get('compliance_status')}",
                "- Evidence counts: "
                f"plan={evidence_counts.get('plan_source_evidence_count', 0)}, "
                f"package={evidence_counts.get('package_evidence_count', 0)}",
                "",
                "Component text:",
                "",
                _markdown_blockquote(str(item.get("component_text") or "")),
                "",
                f"Package evidence terms: {', '.join(_string_values(item.get('package_evidence_terms')))}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"

def _markdown_blockquote(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return "> (missing)"
    return "\n".join(f"> {line}" for line in _wrap_words(normalized, width=100))

def _wrap_words(text: str, *, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        next_len = len(word) if not current else current_len + 1 + len(word)
        if current and next_len > width:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len
    if current:
        lines.append(" ".join(current))
    return lines
