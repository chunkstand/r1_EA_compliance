from __future__ import annotations

from pathlib import Path

from .forest_plan_identity_reconciliation import aliased_region1_forest_plan_source_record_ids
from .forest_plan_resolver_models import _is_profile_scope
from .forest_plan_resolver_models import ForestPlanResolverProfile
from .review_package_support import indexed_source_record_counts
from .review_package_support import read_json_if_exists
from .review_package_support import retrieval_artifacts
from .review_package_support import utc_now

def _validation_report(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    checks = [
        _check_schema_fields(context),
        _check_scope_resolved(context, resolver_profile=resolver_profile),
        _check_required_custer_source_records_indexed(
            context,
            resolver_profile=resolver_profile,
        ),
        _check_custer_scope_has_resolved_area(context, resolver_profile=resolver_profile),
        _check_resolved_entries_have_plan_source_evidence(context),
        _check_triggered_supporting_plan_evidence_has_source_evidence(context),
    ]
    return {
        "schema_version": "forest-plan-context-validation-v0",
        "created_at": utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }

def _check_schema_fields(context: dict) -> dict:
    required = {
        "scope_status",
        "forest_unit",
        "source_records",
        "project_location_signals",
        "geographic_areas",
        "management_areas",
        "overlays",
        "supporting_plan_evidence",
        "source_record_readiness",
        "package_evidence",
        "plan_source_evidence",
        "unresolved_mentions",
        "needs_reviewer_resolution",
    }
    missing = sorted(required - set(context))
    return {
        "name": "context_schema_fields_present",
        "passed": not missing,
        "details": {"missing": missing},
    }

def _check_scope_resolved(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    status = context.get("scope_status")
    return {
        "name": "scope_status_resolved",
        "passed": status in {resolver_profile.scope_status, resolver_profile.out_of_scope_status},
        "details": {"scope_status": status},
    }

def _check_custer_scope_has_resolved_area(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    if not _is_profile_scope(context, resolver_profile):
        return {
            "name": "custer_scope_has_resolved_area",
            "passed": True,
            "details": {"not_applicable": True},
        }
    resolved_count = (
        len(context.get("geographic_areas", []))
        + len(context.get("management_areas", []))
        + len(context.get("overlays", []))
    )
    return {
        "name": "custer_scope_has_resolved_area",
        "passed": resolved_count > 0,
        "details": {
            "resolved_area_count": resolved_count,
            "geographic_area_count": len(context.get("geographic_areas", [])),
            "management_area_count": len(context.get("management_areas", [])),
            "overlay_count": len(context.get("overlays", [])),
        },
    }

def _check_required_custer_source_records_indexed(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    if not _is_profile_scope(context, resolver_profile):
        return {
            "name": "required_custer_source_records_indexed",
            "passed": True,
            "details": {"not_applicable": True},
        }
    readiness = context.get("source_record_readiness") or {}
    if "blocking_missing_source_record_ids" in readiness:
        missing = list(readiness.get("blocking_missing_source_record_ids") or [])
    else:
        missing = list(readiness.get("missing_source_record_ids") or [])
    return {
        "name": "required_custer_source_records_indexed",
        "passed": bool(readiness.get("ready")) and not missing,
        "details": {
            "required_source_record_ids": readiness.get("required_source_record_ids", []),
            "indexed_source_record_counts": readiness.get("indexed_source_record_counts", {}),
            "missing_source_record_ids": list(readiness.get("missing_source_record_ids") or []),
            "blocking_missing_source_record_ids": missing,
            "optional_missing_source_record_ids": list(
                readiness.get("optional_missing_source_record_ids") or []
            ),
        },
    }

def _check_resolved_entries_have_plan_source_evidence(context: dict) -> dict:
    failures = []
    for collection_name in ("geographic_areas", "management_areas", "overlays"):
        for entry in context.get(collection_name, []):
            if not entry.get("package_evidence") or not entry.get("plan_source_evidence"):
                failures.append(
                    {
                        "collection": collection_name,
                        "entry_id": entry.get("entry_id"),
                        "name": entry.get("name"),
                        "package_evidence_count": len(entry.get("package_evidence", [])),
                        "plan_source_evidence_count": len(entry.get("plan_source_evidence", [])),
                    }
                )
    return {
        "name": "resolved_entries_have_package_and_plan_source_evidence",
        "passed": not failures,
        "details": {"failures": failures},
    }

def _check_triggered_supporting_plan_evidence_has_source_evidence(context: dict) -> dict:
    failures = []
    for entry in context.get("supporting_plan_evidence", []):
        if (
            not entry.get("trigger_evidence")
            or not entry.get("package_evidence")
            or not entry.get("plan_source_evidence")
        ):
            failures.append(
                {
                    "route_id": entry.get("route_id"),
                    "name": entry.get("name"),
                    "source_record_id": entry.get("source_record_id"),
                    "trigger_evidence_count": len(entry.get("trigger_evidence", [])),
                    "package_evidence_count": len(entry.get("package_evidence", [])),
                    "plan_source_evidence_count": len(entry.get("plan_source_evidence", [])),
                }
            )
    return {
        "name": "triggered_supporting_plan_evidence_has_source_evidence",
        "passed": not failures,
        "details": {
            "triggered_route_count": len(context.get("supporting_plan_evidence", [])),
            "failures": failures,
        },
    }

def _needs_reviewer_resolution(
    context: dict,
    validation: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> bool:
    if context.get("scope_status") == resolver_profile.out_of_scope_status:
        return False
    if not _is_profile_scope(context, resolver_profile):
        return True
    return not validation.get("passed")

def _summary(
    *,
    context: dict,
    validation: dict,
    package_manifest: list[dict],
    package_chunks: list[dict],
    context_path: Path,
    validation_path: Path,
    summary_path: Path,
    retrieval_readiness: dict | None,
    component_evaluation_summary: dict | None = None,
) -> dict:
    failed_package_records = [
        record for record in package_manifest if record.get("status") != "extracted"
    ]
    summary = {
        "schema_version": "forest-plan-context-summary-v0",
        "review_id": context["review_id"],
        "scope_status": context["scope_status"],
        "source_set_id": context.get("source_set_id"),
        "index_path": context.get("index_path"),
        "context_path": str(context_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "package_file_count": len(package_manifest),
        "package_failed_count": len(failed_package_records),
        "package_chunk_count": len(package_chunks),
        "project_location_signal_count": len(context["project_location_signals"]),
        "geographic_area_count": len(context["geographic_areas"]),
        "management_area_count": len(context["management_areas"]),
        "overlay_count": len(context["overlays"]),
        "supporting_plan_evidence_count": len(context["supporting_plan_evidence"]),
        "unresolved_mention_count": len(context["unresolved_mentions"]),
        "needs_reviewer_resolution": context["needs_reviewer_resolution"],
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"] and not context["needs_reviewer_resolution"],
        "retrieval_readiness": retrieval_readiness,
    }
    if component_evaluation_summary is not None:
        component_adjudication = _component_adjudication_readiness(
            review_dir=summary_path.parent,
            review_id=str(context["review_id"]),
            source_set_id=context.get("source_set_id"),
            component_evaluation_summary=component_evaluation_summary,
        )
        summary["component_evaluation"] = component_evaluation_summary
        summary["component_adjudication"] = component_adjudication
        component_gate_ready = bool(
            component_evaluation_summary.get("validation_passed")
        ) or bool(component_adjudication.get("reviewer_ready"))
        summary["reviewer_ready"] = summary["reviewer_ready"] and bool(
            component_gate_ready
        )
    return summary

def _component_adjudication_readiness(
    *,
    review_dir: Path,
    review_id: str,
    source_set_id: str | None,
    component_evaluation_summary: dict,
) -> dict:
    eval_path = review_dir / "forest_plan_component_adjudication_eval.json"
    summary = read_json_if_exists(eval_path)
    if not isinstance(summary, dict):
        return {
            "eval_path": str(eval_path),
            "eval_exists": False,
            "reviewer_ready": False,
            "failed_checks": ["adjudication_eval_missing"],
        }
    eval_summary = (
        summary.get("summary") if isinstance(summary.get("summary"), dict) else {}
    )
    current_queue_count = int(component_evaluation_summary.get("reviewer_resolution_count") or 0)
    adjudication_queue_count = int(eval_summary.get("queue_item_count") or 0)
    resolved_count = int(eval_summary.get("resolved_adjudication_count") or 0)
    pending_count = int(eval_summary.get("pending_adjudication_count") or 0)
    system_miss_count = int(eval_summary.get("system_miss_count") or 0)
    failed_checks: list[str] = []
    if not bool(eval_summary.get("passed")):
        failed_checks.append("adjudication_eval_failed")
    if (summary.get("review_id") or eval_summary.get("review_id")) != review_id:
        failed_checks.append("review_id_mismatch")
    if (summary.get("source_set_id") or eval_summary.get("source_set_id")) != source_set_id:
        failed_checks.append("source_set_mismatch")
    if adjudication_queue_count != current_queue_count:
        failed_checks.append("queue_item_count_mismatch")
    if resolved_count != current_queue_count:
        failed_checks.append("resolved_item_count_mismatch")
    if pending_count:
        failed_checks.append("pending_adjudication")
    return {
        "eval_path": str(eval_path),
        "eval_exists": True,
        "reviewer_ready": not failed_checks,
        "failed_checks": failed_checks,
        "queue_item_count": adjudication_queue_count,
        "current_queue_item_count": current_queue_count,
        "resolved_adjudication_count": resolved_count,
        "pending_adjudication_count": pending_count,
        "real_ea_omission_count": int(eval_summary.get("real_ea_omission_count") or 0),
        "system_miss_count": system_miss_count,
        "adjudication_completion_rate": eval_summary.get("adjudication_completion_rate"),
        "adjudication_outcome_counts": eval_summary.get("adjudication_outcome_counts", {}),
        "disposition_counts": eval_summary.get("disposition_counts", {}),
        "real_ea_omission_disposition_counts": eval_summary.get(
            "real_ea_omission_disposition_counts",
            {},
        ),
        "system_miss_disposition_counts": eval_summary.get(
            "system_miss_disposition_counts",
            {},
        ),
        "failure_category_counts": eval_summary.get("failure_category_counts", {}),
    }

def _retrieval_readiness_report(
    *,
    index_path: Path,
    source_set_id: str,
    required_source_record_ids: tuple[str, ...] = (),
    optional_source_record_ids: tuple[str, ...] = (),
) -> dict:
    summary_path, validation_path, summary, validation = retrieval_artifacts(index_path)
    alias_source_record_ids_by_required_id = {
        source_record_id: tuple(
            aliased_region1_forest_plan_source_record_ids(source_record_id=source_record_id)
        )
        for source_record_id in (*required_source_record_ids, *optional_source_record_ids)
    }
    indexed_alias_source_counts = indexed_source_record_counts(
        index_path,
        tuple(
            sorted(
                {
                    aliased_source_record_id
                    for aliased_source_record_ids in alias_source_record_ids_by_required_id.values()
                    for aliased_source_record_id in aliased_source_record_ids
                }
            )
        ),
    )
    indexed_source_counts = {
        source_record_id: max(
            (
                indexed_alias_source_counts.get(aliased_source_record_id, 0)
                for aliased_source_record_id in alias_source_record_ids_by_required_id.get(
                    source_record_id,
                    (source_record_id,),
                )
            ),
            default=0,
        )
        for source_record_id in required_source_record_ids
    }
    missing_source_record_ids = [
        source_record_id
        for source_record_id in required_source_record_ids
        if indexed_source_counts.get(source_record_id, 0) <= 0
    ]
    optional_source_record_id_set = set(optional_source_record_ids)
    blocking_missing_source_record_ids = [
        source_record_id
        for source_record_id in missing_source_record_ids
        if source_record_id not in optional_source_record_id_set
    ]
    required_source_records_ready = bool(required_source_record_ids) and not blocking_missing_source_record_ids
    resolver_ready = bool(
        summary
        and (
            required_source_records_ready
            if required_source_record_ids
            else summary.get("reviewer_ready")
        )
    )
    required_source_records = {
        "required_source_record_ids": list(required_source_record_ids),
        "indexed_source_record_counts": indexed_source_counts,
        "source_record_id_aliases": {
            source_record_id: list(aliased_source_record_ids)
            for source_record_id, aliased_source_record_ids in (
                alias_source_record_ids_by_required_id.items()
            )
        },
        "indexed_alias_source_record_counts": {
            source_record_id: indexed_alias_source_counts.get(source_record_id, 0)
            for source_record_id in sorted(indexed_alias_source_counts)
        },
        "missing_source_record_ids": missing_source_record_ids,
        "blocking_missing_source_record_ids": blocking_missing_source_record_ids,
        "optional_source_record_ids": list(optional_source_record_ids),
        "optional_missing_source_record_ids": [
            source_record_id
            for source_record_id in missing_source_record_ids
            if source_record_id in optional_source_record_id_set
        ],
        "ready": required_source_records_ready,
    }
    checks = [
        {
            "name": "retrieval_index_exists",
            "passed": index_path.exists(),
            "details": {"path": str(index_path)},
        },
        {
            "name": "retrieval_summary_exists",
            "passed": summary is not None,
            "details": {"path": str(summary_path)},
        },
        {
            "name": "retrieval_validation_exists",
            "passed": validation is not None,
            "details": {"path": str(validation_path)},
        },
        {
            "name": "retrieval_source_set_matches",
            "passed": bool(summary and summary.get("source_set_id") == source_set_id),
            "details": {
                "expected_source_set_id": source_set_id,
                "summary_source_set_id": (summary or {}).get("source_set_id"),
            },
        },
        {
            "name": "retrieval_validation_passed",
            "passed": bool(validation and validation.get("passed")),
            "details": {"passed": bool(validation and validation.get("passed"))},
        },
        {
            "name": "required_custer_source_records_indexed",
            "passed": not required_source_record_ids or required_source_records_ready,
            "details": required_source_records,
        },
        {
            "name": "retrieval_ready_for_forest_plan_resolver",
            "passed": resolver_ready,
            "details": {
                "summary_reviewer_ready": bool(summary and summary.get("reviewer_ready")),
                "required_source_records_ready": required_source_records_ready,
            },
        },
    ]
    return {
        "index_path": str(index_path),
        "summary_path": str(summary_path),
        "validation_path": str(validation_path),
        "required_source_records": required_source_records,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
