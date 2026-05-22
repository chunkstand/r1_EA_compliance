from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .project_sow_package_common import _check
from .project_sow_package_common import _duplicates
from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _now
from .project_sow_package_common import _strings
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_DECISIONS
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_ITEM_TYPES
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION

def _project_sow_adjudication_eval_summary(
    *,
    context: dict[str, Any],
    adjudication: dict[str, Any],
    adjudication_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    item_results = _project_sow_adjudication_item_results(
        expected_items=context["queue_items"],
        adjudication_items=_list(adjudication.get("items")),
    )
    decision_counts = Counter(
        str(result.get("decision"))
        for result in item_results
        if result.get("decision") in PROJECT_SOW_ADJUDICATION_DECISIONS
    )
    reviewer_metadata = _project_sow_adjudication_reviewer_metadata(adjudication)
    checks = _project_sow_adjudication_eval_checks(
        context=context,
        adjudication=adjudication,
        item_results=item_results,
    )
    failure_counts = Counter(
        category
        for result in item_results
        for category in _strings(result.get("failure_categories"))
    )
    for check in checks:
        if not check["passed"]:
            failure_counts[str(check["name"])] += 1
    passed = all(check["passed"] for check in checks) and all(
        result["passed"] for result in item_results
    )
    return {
        "adjudication_id": adjudication.get("adjudication_id"),
        "adjudication_item_count": len(_list(adjudication.get("items"))),
        "adjudication_path": str(adjudication_path),
        "adjudication_status": _project_sow_adjudication_status(
            passed=passed,
            decision_counts=decision_counts,
            item_count=len(context["queue_items"]),
        ),
        "completed_item_count": sum(1 for result in item_results if result["passed"]),
        "decision_counts": dict(sorted(decision_counts.items())),
        "failed_validation_checks": [check for check in checks if not check["passed"]],
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "input_hashes": context["input_hashes"],
        "item_results": item_results,
        "output_path": str(output_path),
        "passed": passed,
        "pending_item_count": sum(1 for result in item_results if not result["passed"]),
        "project_id": context["project_id"],
        "queue_item_count": len(context["queue_items"]),
        "reviewer_metadata": reviewer_metadata,
        "schema_version": PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "source_set_id": context["source_set_id"],
        "validation_checks": checks,
    }


def _project_sow_adjudication_eval_checks(
    *,
    context: dict[str, Any],
    adjudication: dict[str, Any],
    item_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_ids = {str(item.get("item_id")) for item in context["queue_items"]}
    adjudication_ids = [
        str(item.get("item_id") or "")
        for item in _list(adjudication.get("items"))
        if isinstance(item, dict)
    ]
    missing_item_ids = sorted(expected_ids - set(adjudication_ids))
    unexpected_item_ids = sorted(set(adjudication_ids) - expected_ids)
    duplicate_item_ids = _duplicates(adjudication_ids)
    metadata_errors = _project_sow_adjudication_reviewer_metadata_errors(adjudication)
    return [
        _check(
            name="project_sow_adjudication_schema_supported",
            passed=adjudication.get("schema_version") == PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION,
            details={"schema_version": adjudication.get("schema_version")},
        ),
        _check(
            name="project_sow_adjudication_identity_matches_intake",
            passed=(
                adjudication.get("project_id") == context["project_id"]
                and adjudication.get("source_set_id") == context["source_set_id"]
            ),
            details={
                "actual_project_id": adjudication.get("project_id"),
                "actual_source_set_id": adjudication.get("source_set_id"),
                "expected_project_id": context["project_id"],
                "expected_source_set_id": context["source_set_id"],
            },
        ),
        _check(
            name="project_sow_adjudication_input_hashes_match",
            passed=adjudication.get("input_hashes") == context["input_hashes"],
            details={
                "actual": adjudication.get("input_hashes"),
                "expected": context["input_hashes"],
            },
        ),
        _check(
            name="project_sow_adjudication_items_cover_current_queue",
            passed=not missing_item_ids and not unexpected_item_ids and not duplicate_item_ids,
            details={
                "duplicate_item_ids": duplicate_item_ids,
                "missing_item_ids": missing_item_ids,
                "unexpected_item_ids": unexpected_item_ids,
            },
        ),
        _check(
            name="project_sow_adjudication_items_complete",
            passed=all(result["passed"] for result in item_results),
            details={
                "failed_item_ids": [
                    result["item_id"] for result in item_results if not result["passed"]
                ]
            },
        ),
        _check(
            name="project_sow_adjudication_reviewer_metadata_complete",
            passed=not metadata_errors,
            details={"errors": metadata_errors},
        ),
    ]


def _project_sow_adjudication_item_results(
    *,
    expected_items: list[dict[str, Any]],
    adjudication_items: list[Any],
) -> list[dict[str, Any]]:
    expected_by_id = {str(item.get("item_id")): item for item in expected_items}
    actual_by_id = {
        str(item.get("item_id") or ""): item
        for item in adjudication_items
        if isinstance(item, dict)
    }
    duplicate_counts = Counter(
        str(item.get("item_id") or "")
        for item in adjudication_items
        if isinstance(item, dict)
    )
    results = [
        _project_sow_adjudication_item_result(
            adjudication=item,
            expected=expected_by_id.get(str(item.get("item_id") or ""))
            if isinstance(item, dict)
            else None,
            duplicate_count=duplicate_counts[str(item.get("item_id") or "")]
            if isinstance(item, dict)
            else 0,
        )
        for item in adjudication_items
    ]
    missing_ids = sorted(set(expected_by_id) - set(actual_by_id))
    for item_id in missing_ids:
        expected = expected_by_id[item_id]
        results.append(
            {
                "adjudicated_at": None,
                "adjudicated_by": [],
                "current_status": expected.get("current_status"),
                "decision": None,
                "decision_source": None,
                "failure_categories": ["adjudication_missing"],
                "issue_summary": expected.get("issue_summary"),
                "item_id": item_id,
                "item_type": expected.get("item_type"),
                "optional_deliverable": expected.get("optional_deliverable"),
                "passed": False,
                "rationale": None,
                "resource_area_id": expected.get("resource_area_id"),
                "resource_scope_id": expected.get("resource_scope_id"),
            }
        )
    return sorted(results, key=lambda result: str(result.get("item_id") or ""))


def _project_sow_adjudication_item_result(
    *,
    adjudication: Any,
    expected: dict[str, Any] | None,
    duplicate_count: int,
) -> dict[str, Any]:
    if not isinstance(adjudication, dict):
        return {
            "adjudicated_at": None,
            "adjudicated_by": [],
            "current_status": None,
            "decision": None,
            "decision_source": None,
            "failure_categories": ["adjudication_item_not_object"],
            "issue_summary": None,
            "item_id": "",
            "item_type": None,
            "optional_deliverable": None,
            "passed": False,
            "rationale": None,
            "resource_area_id": None,
            "resource_scope_id": None,
        }
    failure_categories: list[str] = []
    item_id = str(adjudication.get("item_id") or "")
    item_type = str(adjudication.get("item_type") or "")
    decision = str(adjudication.get("decision") or "")
    if expected is None:
        failure_categories.append("adjudication_unexpected")
    if duplicate_count > 1:
        failure_categories.append("adjudication_duplicate")
    if item_type not in PROJECT_SOW_ADJUDICATION_ITEM_TYPES:
        failure_categories.append("adjudication_invalid_item_type")
    identity_mismatches = (
        _project_sow_adjudication_identity_mismatches(
            adjudication=adjudication,
            expected=expected,
        )
        if expected is not None
        else []
    )
    if identity_mismatches:
        failure_categories.append("adjudication_identity_mismatch")
    if decision == "pending" or not decision:
        failure_categories.append("adjudication_pending")
    elif decision not in PROJECT_SOW_ADJUDICATION_DECISIONS:
        failure_categories.append("adjudication_invalid_decision")
    if decision in PROJECT_SOW_ADJUDICATION_DECISIONS:
        missing_fields = _missing_project_sow_adjudication_fields(adjudication)
        if missing_fields:
            failure_categories.append("adjudication_incomplete")
    return {
        "adjudicated_at": adjudication.get("adjudicated_at"),
        "adjudicated_by": _strings(adjudication.get("adjudicated_by")),
        "current_status": adjudication.get("current_status"),
        "decision": decision,
        "decision_source": adjudication.get("decision_source"),
        "failure_categories": sorted(set(failure_categories)),
        "issue_summary": adjudication.get("issue_summary"),
        "item_id": item_id,
        "item_type": item_type,
        "identity_mismatches": identity_mismatches,
        "missing_fields": _missing_project_sow_adjudication_fields(adjudication),
        "optional_deliverable": adjudication.get("optional_deliverable"),
        "passed": not failure_categories,
        "rationale": adjudication.get("rationale"),
        "resource_area_id": adjudication.get("resource_area_id"),
        "resource_scope_id": adjudication.get("resource_scope_id"),
    }


def _missing_project_sow_adjudication_fields(adjudication: dict[str, Any]) -> list[str]:
    missing = []
    for field in ("adjudicated_at", "decision_source", "rationale"):
        if _is_empty(adjudication.get(field)):
            missing.append(field)
    if not _strings(adjudication.get("adjudicated_by")):
        missing.append("adjudicated_by")
    return missing


def _project_sow_adjudication_identity_mismatches(
    *,
    adjudication: dict[str, Any],
    expected: dict[str, Any],
) -> list[dict[str, Any]]:
    fields = (
        "action_element_id",
        "current_status",
        "item_type",
        "optional_deliverable",
        "resource_area_id",
        "resource_scope_id",
        "selected_resource_scope_ids",
        "source_check",
    )
    mismatches = []
    for field in fields:
        actual = adjudication.get(field)
        expected_value = expected.get(field)
        if field == "selected_resource_scope_ids":
            actual = _strings(actual)
            expected_value = _strings(expected_value)
        if actual != expected_value:
            mismatches.append(
                {
                    "actual": actual,
                    "expected": expected_value,
                    "field": field,
                }
            )
    return mismatches


def _project_sow_adjudication_reviewer_metadata(
    adjudication: dict[str, Any],
) -> dict[str, Any]:
    metadata = adjudication.get("reviewer_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "review_status": metadata.get("review_status"),
        "reviewed_at": metadata.get("reviewed_at"),
        "reviewed_by": _strings(metadata.get("reviewed_by")),
        "review_source": metadata.get("review_source"),
    }


def _project_sow_adjudication_reviewer_metadata_errors(
    adjudication: dict[str, Any],
) -> list[str]:
    metadata = _project_sow_adjudication_reviewer_metadata(adjudication)
    errors = []
    if metadata["review_status"] != "complete":
        errors.append("reviewer_metadata.review_status must be complete")
    if _is_empty(metadata["reviewed_at"]):
        errors.append("reviewer_metadata.reviewed_at required")
    if not metadata["reviewed_by"]:
        errors.append("reviewer_metadata.reviewed_by required")
    if _is_empty(metadata["review_source"]):
        errors.append("reviewer_metadata.review_source required")
    return errors


def _project_sow_adjudication_status(
    *,
    passed: bool,
    decision_counts: Counter[str],
    item_count: int,
) -> str:
    if not passed:
        return "failed"
    if item_count == 0:
        return "not_required"
    if decision_counts.get("needs_information", 0):
        return "adjudicated_needs_information"
    return "adjudicated"


def _project_sow_adjudication_apply_summary(
    *,
    eval_summary: dict[str, Any],
    adjudication_path: Path,
    eval_output_path: Path,
    intake_path: Path,
    output_intake_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    return {
        "adjudication_path": str(adjudication_path),
        "adjudication_status": eval_summary.get("adjudication_status"),
        "decision_counts": eval_summary.get("decision_counts") or {},
        "eval_output_path": str(eval_output_path),
        "failed_validation_checks": eval_summary.get("failed_validation_checks") or [],
        "input_hashes": eval_summary.get("input_hashes") or {},
        "intake_path": str(intake_path),
        "item_count": eval_summary.get("queue_item_count"),
        "output_intake_path": str(output_intake_path),
        "output_path": str(output_path),
        "output_written": False,
        "passed": eval_summary.get("passed") is True,
        "schema_version": PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION,
    }


def _project_sow_intake_adjudication(
    *,
    eval_summary: dict[str, Any],
    adjudication_path: Path,
    eval_output_path: Path,
) -> dict[str, Any]:
    items = [
        {
            "adjudicated_at": result.get("adjudicated_at"),
            "adjudicated_by": result.get("adjudicated_by") or [],
            "current_status": result.get("current_status"),
            "decision": result.get("decision"),
            "decision_source": result.get("decision_source"),
            "issue_summary": result.get("issue_summary"),
            "item_id": result.get("item_id"),
            "item_type": result.get("item_type"),
            "optional_deliverable": result.get("optional_deliverable"),
            "rationale": result.get("rationale"),
            "resource_area_id": result.get("resource_area_id"),
            "resource_scope_id": result.get("resource_scope_id"),
        }
        for result in _list(eval_summary.get("item_results"))
        if isinstance(result, dict) and result.get("passed") is True
    ]
    return {
        "adjudication_id": eval_summary.get("adjudication_id"),
        "adjudication_path": str(adjudication_path),
        "applied_at": _now(),
        "boundaries": [
            "Project SOW adjudication is a planning overlay only.",
            "It does not create applicability decisions, compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions.",
        ],
        "decision_counts": eval_summary.get("decision_counts") or {},
        "eval_output_path": str(eval_output_path),
        "input_hashes": eval_summary.get("input_hashes") or {},
        "item_count": len(items),
        "items": items,
        "reviewer_metadata": eval_summary.get("reviewer_metadata") or {},
        "schema_version": PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION,
        "status": eval_summary.get("adjudication_status"),
    }
