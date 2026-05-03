from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import re


FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION = "forest-plan-component-adjudication-v0"
FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION = (
    "forest-plan-component-adjudication-eval-v0"
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

PENDING_DISPOSITIONS = {"pending"}
RESOLVED_DISPOSITIONS = {
    "true_ea_omission",
    "retrieval_miss",
    "package_section_chunking_miss",
    "component_inventory_overreach",
    "applicability_false_positive",
    "evidence_linking_miss",
}
ALLOWED_DISPOSITIONS = PENDING_DISPOSITIONS | RESOLVED_DISPOSITIONS
REQUIRED_ADJUDICATION_FIELDS = ("adjudicated_at", "rationale", "source_type")


@dataclass(frozen=True)
class ForestPlanComponentAdjudicationTemplateResult:
    review_dir: Path
    output_path: Path
    markdown_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ForestPlanComponentAdjudicationEvalResult:
    review_dir: Path
    adjudication_file: Path
    output_path: Path
    summary: dict[str, Any]


def write_forest_plan_component_adjudication_template(
    *,
    output_dir: Path,
    review_id: str | None = None,
    review_dir: Path | None = None,
    output_path: Path | None = None,
) -> ForestPlanComponentAdjudicationTemplateResult:
    """Write a reviewer-fillable adjudication template for open component items."""

    resolved_review_dir = _resolve_review_dir(
        output_dir=output_dir,
        review_id=review_id,
        review_dir=review_dir,
    )
    artifacts = _load_review_artifacts(resolved_review_dir)
    output_path = Path(output_path) if output_path else (
        resolved_review_dir / "forest_plan_component_adjudication_template.json"
    )
    markdown_path = output_path.with_suffix(".md")
    queue_items = _queue_items(artifacts["queue"])
    findings_by_id = _findings_by_id(artifacts["findings_report"])
    components_by_id = _components_by_id(artifacts["findings_report"])
    items = [
        _template_item(
            item=queue_item,
            finding=findings_by_id.get(str(queue_item.get("finding_id") or "")),
            component=components_by_id.get(str(queue_item.get("component_id") or "")),
        )
        for queue_item in queue_items
    ]
    summary = _template_summary(
        review_dir=resolved_review_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        findings_report=artifacts["findings_report"],
        queue=artifacts["queue"],
        items=items,
    )
    template = {
        "schema_version": FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION,
        "adjudication_id": f"{summary['review_id']}-component-adjudication",
        "title": "Forest Plan Component Adjudication",
        "created_at": _utc_now(),
        "review_id": summary["review_id"],
        "source_set_id": summary["source_set_id"],
        "component_findings_path": str(resolved_review_dir / "forest_plan_component_findings.json"),
        "reviewer_resolution_queue_path": str(
            resolved_review_dir / "forest_plan_reviewer_resolution_queue.json"
        ),
        "adjudication": {
            "status": "pending",
            "method": "",
            "adjudicated_by": [],
            "adjudicated_at": "",
            "notes": "",
        },
        "allowed_dispositions": sorted(ALLOWED_DISPOSITIONS),
        "resolved_dispositions": sorted(RESOLVED_DISPOSITIONS),
        "summary": summary,
        "items": items,
    }
    _write_json(output_path, template)
    _write_text(markdown_path, _template_markdown(template))
    return ForestPlanComponentAdjudicationTemplateResult(
        review_dir=resolved_review_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        summary=summary,
    )


def run_forest_plan_component_adjudication_eval(
    *,
    output_dir: Path,
    review_id: str | None = None,
    review_dir: Path | None = None,
    adjudication_file: Path | None = None,
    output_path: Path | None = None,
) -> ForestPlanComponentAdjudicationEvalResult:
    """Evaluate completed component adjudications against current review artifacts."""

    resolved_review_dir = _resolve_review_dir(
        output_dir=output_dir,
        review_id=review_id,
        review_dir=review_dir,
    )
    artifacts = _load_review_artifacts(resolved_review_dir)
    adjudication_file = Path(adjudication_file) if adjudication_file else (
        resolved_review_dir / "forest_plan_component_adjudication.json"
    )
    output_path = Path(output_path) if output_path else (
        resolved_review_dir / "forest_plan_component_adjudication_eval.json"
    )
    adjudication = _load_adjudication(adjudication_file)
    queue_items = _queue_items(artifacts["queue"])
    findings_by_id = _findings_by_id(artifacts["findings_report"])
    adjudication_items = _adjudication_items(adjudication)
    item_results = _item_results(
        queue_items=queue_items,
        findings_by_id=findings_by_id,
        adjudication_items=adjudication_items,
    )
    checks = [
        _check_adjudication_identity(
            adjudication=adjudication,
            adjudication_file=adjudication_file,
            findings_report=artifacts["findings_report"],
        ),
        _check_adjudication_items_cover_queue(
            queue_items=queue_items,
            adjudication_items=adjudication_items,
        ),
        _check_adjudication_items_complete(item_results),
        _check_adjudication_expectations_match(item_results),
    ]
    summary = _eval_summary(
        review_dir=resolved_review_dir,
        adjudication_file=adjudication_file,
        output_path=output_path,
        findings_report=artifacts["findings_report"],
        queue_items=queue_items,
        item_results=item_results,
        checks=checks,
    )
    report = {
        "schema_version": FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": summary["review_id"],
        "source_set_id": summary["source_set_id"],
        "adjudication_file": str(adjudication_file),
        "review_dir": str(resolved_review_dir),
        "summary": summary,
        "checks": checks,
        "item_results": item_results,
    }
    _write_json(output_path, report)
    return ForestPlanComponentAdjudicationEvalResult(
        review_dir=resolved_review_dir,
        adjudication_file=adjudication_file,
        output_path=output_path,
        summary=summary,
    )


def _resolve_review_dir(
    *,
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
) -> Path:
    if review_dir is not None:
        return Path(review_dir)
    if not review_id:
        raise ValueError("Provide either review_id or review_dir.")
    if not SAFE_ID_RE.fullmatch(review_id):
        raise ValueError("review_id must contain only letters, numbers, dot, underscore, or hyphen.")
    return Path(output_dir) / "reviews" / review_id


def _load_review_artifacts(review_dir: Path) -> dict[str, Any]:
    findings_path = review_dir / "forest_plan_component_findings.json"
    queue_path = review_dir / "forest_plan_reviewer_resolution_queue.json"
    findings_report = _read_json(findings_path)
    queue = _read_json(queue_path)
    return {
        "findings_report": findings_report,
        "queue": queue,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing forest-plan component adjudication artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _load_adjudication(path: Path) -> dict[str, Any]:
    adjudication = _read_json(path)
    if adjudication.get("schema_version") != FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION:
        raise ValueError(
            "Forest-plan component adjudication file has unsupported schema_version: "
            f"{adjudication.get('schema_version')}"
        )
    return adjudication


def _queue_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    items = queue.get("items")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _findings_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    findings = report.get("findings")
    if not isinstance(findings, list):
        return {}
    return {
        str(finding.get("finding_id")): finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("finding_id")
    }


def _components_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = report.get("components")
    if not isinstance(components, list):
        return {}
    return {
        str(component.get("component_id")): component
        for component in components
        if isinstance(component, dict) and component.get("component_id")
    }


def _adjudication_items(adjudication: dict[str, Any]) -> list[dict[str, Any]]:
    items = adjudication.get("items")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _template_item(
    *,
    item: dict[str, Any],
    finding: dict[str, Any] | None,
    component: dict[str, Any] | None,
) -> dict[str, Any]:
    finding = finding or {}
    component = component or {}
    return {
        "item_id": item.get("item_id"),
        "finding_id": item.get("finding_id"),
        "component_id": item.get("component_id"),
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
        "component_text": component.get("component_text"),
        "package_evidence_terms": (
            (finding.get("applicability_basis") or {}).get("package_evidence_terms") or []
        ),
    }


def _current_status(*, finding: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "finding_status": finding.get("finding_status") or item.get("finding_status"),
        "applicability_status": finding.get("applicability_status")
        or item.get("applicability_status"),
        "compliance_status": finding.get("compliance_status"),
        "queue_reason": item.get("reason"),
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


def _item_results(
    *,
    queue_items: list[dict[str, Any]],
    findings_by_id: dict[str, dict[str, Any]],
    adjudication_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    adjudications_by_key = _adjudications_by_key(adjudication_items)
    queue_keys = {_item_key(item) for item in queue_items}
    results = []
    for queue_item in queue_items:
        key = _item_key(queue_item)
        adjudication = adjudications_by_key.get(key)
        finding = findings_by_id.get(str(queue_item.get("finding_id") or "")) or {}
        results.append(
            _item_result(
                queue_item=queue_item,
                finding=finding,
                adjudication=adjudication,
                duplicate_count=_adjudication_duplicate_count(adjudication_items, key),
            )
        )
    for adjudication in adjudication_items:
        key = _item_key(adjudication)
        if key not in queue_keys:
            results.append(
                {
                    "item_id": adjudication.get("item_id"),
                    "finding_id": adjudication.get("finding_id"),
                    "component_id": adjudication.get("component_id"),
                    "passed": False,
                    "failure_categories": ["adjudication_unexpected"],
                    "disposition": adjudication.get("disposition"),
                    "current": {},
                    "expected_current": _expected_current(adjudication),
                    "details": {"reason": "adjudication_item_not_in_current_queue"},
                }
            )
    return results


def _item_result(
    *,
    queue_item: dict[str, Any],
    finding: dict[str, Any],
    adjudication: dict[str, Any] | None,
    duplicate_count: int,
) -> dict[str, Any]:
    failure_categories = []
    details: dict[str, Any] = {}
    current = _current_status(finding=finding, item=queue_item)
    expected_current = _expected_current(adjudication or {})
    disposition = str((adjudication or {}).get("disposition") or "")
    if adjudication is None:
        failure_categories.append("adjudication_missing")
    elif duplicate_count > 1:
        failure_categories.append("adjudication_duplicate")
        details["duplicate_count"] = duplicate_count
    elif disposition not in ALLOWED_DISPOSITIONS:
        failure_categories.append("adjudication_invalid_disposition")
    elif disposition in PENDING_DISPOSITIONS:
        failure_categories.append("adjudication_pending")

    if adjudication is not None and disposition in RESOLVED_DISPOSITIONS:
        missing = _missing_adjudication_fields(adjudication)
        if missing:
            failure_categories.append("adjudication_incomplete")
            details["missing_fields"] = missing

    mismatches = _status_mismatches(current=current, expected=expected_current)
    if mismatches:
        failure_categories.append("adjudication_expectation_mismatch")
        details["status_mismatches"] = mismatches

    return {
        "item_id": queue_item.get("item_id"),
        "finding_id": queue_item.get("finding_id"),
        "component_id": queue_item.get("component_id"),
        "component_type": finding.get("component_type"),
        "queue_reason": queue_item.get("reason"),
        "disposition": disposition or None,
        "current": current,
        "expected_current": expected_current,
        "passed": not failure_categories,
        "failure_categories": failure_categories,
        "details": details,
    }


def _adjudications_by_key(items: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    by_key = {}
    for item in items:
        key = _item_key(item)
        by_key.setdefault(key, item)
    return by_key


def _adjudication_duplicate_count(
    items: list[dict[str, Any]],
    key: tuple[str, str, str],
) -> int:
    return sum(1 for item in items if _item_key(item) == key)


def _item_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(item.get("item_id") or ""),
        str(item.get("finding_id") or ""),
        str(item.get("component_id") or ""),
    )


def _expected_current(adjudication: dict[str, Any]) -> dict[str, Any]:
    value = adjudication.get("expected_current")
    if isinstance(value, dict):
        return dict(value)
    return {
        key: adjudication.get(key)
        for key in (
            "finding_status",
            "applicability_status",
            "compliance_status",
            "queue_reason",
        )
        if adjudication.get(key) is not None
    }


def _missing_adjudication_fields(adjudication: dict[str, Any]) -> list[str]:
    missing = [
        field
        for field in REQUIRED_ADJUDICATION_FIELDS
        if not str(adjudication.get(field) or "").strip()
    ]
    if not _string_list(adjudication.get("adjudicated_by")):
        missing.append("adjudicated_by")
    return sorted(missing)


def _status_mismatches(
    *,
    current: dict[str, Any],
    expected: dict[str, Any],
) -> list[dict[str, Any]]:
    mismatches = []
    for field in (
        "finding_status",
        "applicability_status",
        "compliance_status",
        "queue_reason",
    ):
        if field in expected and expected[field] is not None and expected[field] != current.get(field):
            mismatches.append(
                {
                    "field": field,
                    "expected": expected[field],
                    "actual": current.get(field),
                }
            )
    return mismatches


def _check_adjudication_identity(
    *,
    adjudication: dict[str, Any],
    adjudication_file: Path,
    findings_report: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    summary = (
        findings_report.get("summary") if isinstance(findings_report.get("summary"), dict) else {}
    )
    expected_review_id = findings_report.get("review_id") or summary.get("review_id")
    expected_source_set_id = findings_report.get("source_set_id") or summary.get("source_set_id")
    if adjudication.get("review_id") != expected_review_id:
        failures.append(
            {
                "field": "review_id",
                "expected": expected_review_id,
                "actual": adjudication.get("review_id"),
            }
        )
    if adjudication.get("source_set_id") != expected_source_set_id:
        failures.append(
            {
                "field": "source_set_id",
                "expected": expected_source_set_id,
                "actual": adjudication.get("source_set_id"),
            }
        )
    adjudication_id = str(adjudication.get("adjudication_id") or "")
    if not adjudication_id or not SAFE_ID_RE.fullmatch(adjudication_id):
        failures.append({"field": "adjudication_id", "reason": "missing_or_unsafe"})
    return {
        "name": "adjudication_identity_matches_review",
        "passed": not failures,
        "details": {"path": str(adjudication_file), "failures": failures},
    }


def _check_adjudication_items_cover_queue(
    *,
    queue_items: list[dict[str, Any]],
    adjudication_items: list[dict[str, Any]],
) -> dict[str, Any]:
    queue_keys = {_item_key(item) for item in queue_items}
    adjudication_keys = [_item_key(item) for item in adjudication_items]
    adjudication_key_set = set(adjudication_keys)
    missing = sorted(queue_keys - adjudication_key_set)
    unexpected = sorted(adjudication_key_set - queue_keys)
    duplicates = sorted(
        key for key, count in Counter(adjudication_keys).items() if count > 1
    )
    return {
        "name": "adjudication_items_cover_current_queue",
        "passed": not missing and not unexpected and not duplicates,
        "details": {
            "queue_item_count": len(queue_items),
            "adjudication_item_count": len(adjudication_items),
            "missing": [_key_details(key) for key in missing],
            "unexpected": [_key_details(key) for key in unexpected],
            "duplicates": [_key_details(key) for key in duplicates],
        },
    }


def _check_adjudication_items_complete(item_results: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [
        result
        for result in item_results
        if any(
            category
            in {
                "adjudication_missing",
                "adjudication_duplicate",
                "adjudication_invalid_disposition",
                "adjudication_pending",
                "adjudication_incomplete",
                "adjudication_unexpected",
            }
            for category in result.get("failure_categories", [])
        )
    ]
    return {
        "name": "adjudication_items_are_complete",
        "passed": not failures,
        "details": {
            "failure_count": len(failures),
            "component_ids": [result.get("component_id") for result in failures],
        },
    }


def _check_adjudication_expectations_match(item_results: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [
        result
        for result in item_results
        if "adjudication_expectation_mismatch" in result.get("failure_categories", [])
    ]
    return {
        "name": "adjudicated_expectations_match_current_findings",
        "passed": not failures,
        "details": {
            "failure_count": len(failures),
            "component_ids": [result.get("component_id") for result in failures],
        },
    }


def _eval_summary(
    *,
    review_dir: Path,
    adjudication_file: Path,
    output_path: Path,
    findings_report: dict[str, Any],
    queue_items: list[dict[str, Any]],
    item_results: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = (
        findings_report.get("summary") if isinstance(findings_report.get("summary"), dict) else {}
    )
    failure_counts = Counter(
        category
        for result in item_results
        for category in result.get("failure_categories", [])
    )
    disposition_counts = Counter(
        str(result.get("disposition") or "") for result in item_results if result.get("disposition")
    )
    resolved_count = sum(
        1 for result in item_results if result.get("disposition") in RESOLVED_DISPOSITIONS
    )
    pending_count = sum(
        1 for result in item_results if result.get("disposition") in PENDING_DISPOSITIONS
    )
    expectation_mismatch_count = failure_counts.get("adjudication_expectation_mismatch", 0)
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": findings_report.get("review_id") or summary.get("review_id"),
        "source_set_id": findings_report.get("source_set_id") or summary.get("source_set_id"),
        "review_dir": str(review_dir),
        "adjudication_file": str(adjudication_file),
        "output_path": str(output_path),
        "queue_item_count": len(queue_items),
        "adjudication_item_count": len(item_results),
        "resolved_adjudication_count": resolved_count,
        "pending_adjudication_count": pending_count,
        "expectation_mismatch_count": expectation_mismatch_count,
        "adjudication_completion_rate": _rate(resolved_count, len(queue_items)),
        "adjudication_expectation_match_rate": _rate(
            len(queue_items) - expectation_mismatch_count,
            len(queue_items),
        ),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "passed": passed,
        "checks": checks,
    }


def _key_details(key: tuple[str, str, str]) -> dict[str, str]:
    item_id, finding_id, component_id = key
    return {
        "item_id": item_id,
        "finding_id": finding_id,
        "component_id": component_id,
    }


def _string_list(value: object) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _string_values(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
