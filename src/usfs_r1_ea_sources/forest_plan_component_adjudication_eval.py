from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .forest_plan_component_adjudication_common import _current_status
from .forest_plan_component_adjudication_common import _evidence_refs
from .forest_plan_component_adjudication_common import _key_details
from .forest_plan_component_adjudication_common import _rate
from .forest_plan_component_adjudication_common import _string_list
from .forest_plan_component_adjudication_common import _unique_ref_values
from .forest_plan_component_adjudication_common import _utc_now
from .forest_plan_component_adjudication_models import ALLOWED_DISPOSITIONS
from .forest_plan_component_adjudication_models import FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION
from .forest_plan_component_adjudication_models import PENDING_DISPOSITIONS
from .forest_plan_component_adjudication_models import REAL_EA_OMISSION_DISPOSITIONS
from .forest_plan_component_adjudication_models import REQUIRED_ADJUDICATION_FIELDS
from .forest_plan_component_adjudication_models import RESOLVED_DISPOSITIONS
from .forest_plan_component_adjudication_models import SAFE_ID_RE
from .forest_plan_component_adjudication_models import SYSTEM_MISS_DISPOSITIONS

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
        missing_trace_refs = _missing_trace_refs(
            adjudication=adjudication,
            finding=finding,
        )
        if missing_trace_refs:
            failure_categories.append("adjudication_trace_incomplete")
            details["missing_trace_refs"] = missing_trace_refs

    mismatches = _status_mismatches(current=current, expected=expected_current)
    if mismatches:
        failure_categories.append("adjudication_expectation_mismatch")
        details["status_mismatches"] = mismatches

    plan_source_evidence_refs = _evidence_refs(finding.get("plan_source_evidence") or [])
    package_evidence_refs = _evidence_refs(finding.get("package_evidence") or [])
    return {
        "item_id": queue_item.get("item_id"),
        "finding_id": queue_item.get("finding_id"),
        "component_id": queue_item.get("component_id"),
        "component_type": finding.get("component_type"),
        "queue_reason": queue_item.get("reason"),
        "disposition": disposition or None,
        "adjudication_outcome": _adjudication_outcome(disposition),
        "current": current,
        "expected_current": expected_current,
        "passed": not failure_categories,
        "failure_categories": failure_categories,
        "details": details,
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

def _missing_trace_refs(
    *,
    adjudication: dict[str, Any],
    finding: dict[str, Any],
) -> list[str]:
    missing: list[str] = []
    if not _has_source_record_ref(adjudication.get("component_source_ref")):
        missing.append("component_source_ref.source_record_id")
    if finding.get("plan_source_evidence") and not _has_source_record_ref(
        adjudication.get("plan_source_evidence_refs")
    ):
        missing.append("plan_source_evidence_refs.source_record_id")
    if finding.get("package_evidence") and not _has_source_record_ref(
        adjudication.get("package_evidence_refs")
    ):
        missing.append("package_evidence_refs.source_record_id")
    return missing

def _has_source_record_ref(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(str(value.get("source_record_id") or "").strip())
    if isinstance(value, list):
        return any(_has_source_record_ref(item) for item in value)
    return False

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

def _adjudication_outcome(disposition: str) -> str | None:
    if disposition in REAL_EA_OMISSION_DISPOSITIONS:
        return "real_ea_omission"
    if disposition in SYSTEM_MISS_DISPOSITIONS:
        return "system_miss"
    return None

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
                "adjudication_trace_incomplete",
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
    outcome_counts = Counter(
        str(result.get("adjudication_outcome") or "")
        for result in item_results
        if result.get("adjudication_outcome")
    )
    real_ea_omission_count = outcome_counts.get("real_ea_omission", 0)
    system_miss_count = outcome_counts.get("system_miss", 0)
    real_ea_omission_disposition_counts = Counter(
        str(result.get("disposition") or "")
        for result in item_results
        if result.get("adjudication_outcome") == "real_ea_omission"
    )
    system_miss_disposition_counts = Counter(
        str(result.get("disposition") or "")
        for result in item_results
        if result.get("adjudication_outcome") == "system_miss"
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
        "real_ea_omission_count": real_ea_omission_count,
        "system_miss_count": system_miss_count,
        "expectation_mismatch_count": expectation_mismatch_count,
        "adjudication_completion_rate": _rate(resolved_count, len(queue_items)),
        "real_ea_omission_rate": _rate(real_ea_omission_count, len(queue_items)),
        "system_miss_rate": _rate(system_miss_count, len(queue_items)),
        "adjudication_expectation_match_rate": _rate(
            len(queue_items) - expectation_mismatch_count,
            len(queue_items),
        ),
        "adjudication_outcome_counts": dict(sorted(outcome_counts.items())),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "real_ea_omission_disposition_counts": dict(
            sorted(real_ea_omission_disposition_counts.items())
        ),
        "system_miss_disposition_counts": dict(sorted(system_miss_disposition_counts.items())),
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "passed": passed,
        "checks": checks,
    }
