from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .ea_review import _search_package_chunks
from .retrieval import query_retrieval_index


FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION = "forest-plan-component-inventory-v0"
FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION = "forest-plan-component-findings-v0"
FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION = (
    "forest-plan-reviewer-resolution-queue-v0"
)
FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-inventory-coverage-v0"
)
FOREST_PLAN_APPLICABLE_STANDARD_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-applicable-standard-coverage-v0"
)
DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "forest_plan_component_inventory_seed.json"
)
VALID_COMPONENT_TYPES = {
    "desired_condition",
    "goal",
    "guideline",
    "monitoring",
    "objective",
    "plan_amendment",
    "standard",
    "suitability",
}
VALID_APPLICABILITY_STATUSES = {
    "applicable",
    "candidate",
    "not_applicable",
    "needs_reviewer_resolution",
}
VALID_FINDING_STATUSES = {
    "supported",
    "partial",
    "gap",
    "not_applicable",
    "needs_reviewer_resolution",
}
VALID_COMPLIANCE_STATUSES = {
    "complies",
    "potential_noncompliance",
    "insufficient_evidence",
    "not_applicable",
    "needs_reviewer_resolution",
    "not_evaluated_for_compliance",
}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


@dataclass(frozen=True)
class ForestPlanComponentEvaluationResult:
    findings_path: Path
    markdown_path: Path
    reviewer_resolution_queue_path: Path
    component_inventory_coverage_path: Path
    applicable_standard_coverage_path: Path
    summary: dict


def run_forest_plan_component_evaluation(
    *,
    review_id: str,
    review_dir: Path,
    context: dict,
    package_chunks: list[dict],
    component_inventory_path: Path,
    forest_unit_id: str,
    source_set_id: str | None,
    index_path: Path | None,
    package_top_k: int = 3,
    source_top_k: int = 3,
) -> ForestPlanComponentEvaluationResult:
    """Evaluate profile-selected forest-plan components against package evidence."""

    if package_top_k < 1:
        raise ValueError("package_top_k must be at least 1")
    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")

    review_dir = Path(review_dir)
    component_inventory_path = Path(component_inventory_path)
    findings_path = review_dir / "forest_plan_component_findings.json"
    markdown_path = review_dir / "forest_plan_component_findings.md"
    queue_path = review_dir / "forest_plan_reviewer_resolution_queue.json"
    inventory_coverage_path = review_dir / "forest_plan_component_inventory_coverage.json"
    standard_coverage_path = review_dir / "forest_plan_applicable_standard_coverage.json"
    components = load_forest_plan_component_inventory(
        component_inventory_path,
        forest_unit_id=forest_unit_id,
    )
    findings = [
        _component_finding(
            review_id=review_id,
            component=component,
            context=context,
            package_chunks=package_chunks,
            source_set_id=source_set_id,
            index_path=index_path,
            package_top_k=package_top_k,
            source_top_k=source_top_k,
        )
        for component in components
    ]
    queue = _reviewer_resolution_queue(
        review_id=review_id,
        source_set_id=source_set_id,
        findings=findings,
    )
    inventory_coverage = _component_inventory_coverage(
        review_id=review_id,
        source_set_id=source_set_id,
        component_inventory_path=component_inventory_path,
        components=components,
    )
    standard_coverage = _applicable_standard_coverage(
        review_id=review_id,
        source_set_id=source_set_id,
        components=components,
        findings=findings,
    )
    validation = _validation_report(
        source_set_id=source_set_id,
        components=components,
        findings=findings,
        queue=queue,
        inventory_coverage=inventory_coverage,
        standard_coverage=standard_coverage,
    )
    summary = _summary(
        review_id=review_id,
        source_set_id=source_set_id,
        component_inventory_path=component_inventory_path,
        findings_path=findings_path,
        markdown_path=markdown_path,
        queue_path=queue_path,
        inventory_coverage_path=inventory_coverage_path,
        standard_coverage_path=standard_coverage_path,
        components=components,
        findings=findings,
        queue=queue,
        validation=validation,
        inventory_coverage=inventory_coverage,
        standard_coverage=standard_coverage,
    )
    report = {
        "schema_version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "summary": summary,
        "validation": validation,
        "component_inventory_coverage": inventory_coverage,
        "applicable_standard_coverage": standard_coverage,
        "components": components,
        "findings": findings,
    }

    review_dir.mkdir(parents=True, exist_ok=True)
    _write_json(findings_path, report)
    _write_json(queue_path, queue)
    _write_json(inventory_coverage_path, inventory_coverage)
    _write_json(standard_coverage_path, standard_coverage)
    markdown_path.write_text(_markdown_report(report, queue), encoding="utf-8")
    return ForestPlanComponentEvaluationResult(
        findings_path=findings_path,
        markdown_path=markdown_path,
        reviewer_resolution_queue_path=queue_path,
        component_inventory_coverage_path=inventory_coverage_path,
        applicable_standard_coverage_path=standard_coverage_path,
        summary=summary,
    )


def load_forest_plan_component_inventory(
    path: Path = DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH,
    *,
    forest_unit_id: str | None = None,
) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Forest-plan component inventory must be a JSON object.")
    schema_version = _require_string(payload, "schema_version", "component inventory")
    if schema_version != FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan component inventory schema_version: "
            f"{schema_version!r}; expected {FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION!r}"
        )
    _require_safe_string(payload, "inventory_id", "component inventory")
    components = _require_list(payload, "components", "component inventory")
    parsed = []
    for index, raw_component in enumerate(components):
        component = _parse_component(raw_component, f"components[{index}]")
        if forest_unit_id is not None and component["forest_unit_id"] != forest_unit_id:
            continue
        parsed.append(component)
    if not parsed:
        raise ValueError("Forest-plan component inventory contains no selected components.")
    _reject_duplicate(
        [component["component_id"] for component in parsed],
        "component_id",
        "component inventory",
    )
    return parsed


def _parse_component(raw_component: object, context: str) -> dict:
    component = _require_object(raw_component, context)
    component_id = _require_safe_string(component, "component_id", context)
    component_type = _require_string(component, "component_type", context)
    if component_type not in VALID_COMPONENT_TYPES:
        raise ValueError(f"{context}.component_type is unsupported: {component_type!r}.")
    page = component.get("page")
    if page is not None and (not isinstance(page, int) or page < 1):
        raise ValueError(f"{context}.page must be a positive integer or null.")
    parsed = {
        "component_id": component_id,
        "forest_unit_id": _require_safe_string(component, "forest_unit_id", context),
        "plan_version": _require_string(component, "plan_version", context),
        "source_set_id": _require_safe_string(component, "source_set_id", context),
        "source_record_id": _require_safe_string(component, "source_record_id", context),
        "component_type": component_type,
        "section_id": _require_safe_string(component, "section_id", context),
        "section_heading": _require_string(component, "section_heading", context),
        "page": page,
        "citation_label": _require_string(component, "citation_label", context),
        "component_text": _require_string(component, "component_text", context),
        "geographic_area_ids": _require_string_list(
            component,
            "geographic_area_ids",
            context,
            required=False,
        ),
        "management_area_ids": _require_string_list(
            component,
            "management_area_ids",
            context,
            required=False,
        ),
        "overlay_ids": _require_string_list(component, "overlay_ids", context, required=False),
        "resource_topics": _require_string_list(
            component,
            "resource_topics",
            context,
            required=False,
        ),
        "activity_tags": _require_string_list(
            component,
            "activity_tags",
            context,
            required=False,
        ),
        "source_chunk_ids": _require_string_list(component, "source_chunk_ids", context),
        "artifact_sha256": _require_hex_string(component, "artifact_sha256", context),
        "content_sha256": _require_hex_string(component, "content_sha256", context),
        "provenance": _require_provenance(component.get("provenance"), f"{context}.provenance"),
        "package_evidence_terms": _require_string_list(
            component,
            "package_evidence_terms",
            context,
            required=False,
        ),
    }
    if not (
        parsed["geographic_area_ids"]
        or parsed["management_area_ids"]
        or parsed["overlay_ids"]
        or parsed["resource_topics"]
        or parsed["activity_tags"]
    ):
        raise ValueError(
            f"{context} must include at least one context id, resource_topic, or activity_tag."
        )
    if not parsed["source_chunk_ids"]:
        raise ValueError(f"{context}.source_chunk_ids cannot be empty.")
    return parsed


def _component_finding(
    *,
    review_id: str,
    component: dict,
    context: dict,
    package_chunks: list[dict],
    source_set_id: str | None,
    index_path: Path | None,
    package_top_k: int,
    source_top_k: int,
) -> dict:
    source_set_matches = bool(source_set_id and component["source_set_id"] == source_set_id)
    context_match = _context_matches_component(context, component)
    package_search = _component_package_search(
        component=component,
        package_chunks=package_chunks,
        limit=package_top_k,
    )
    package_evidence = package_search["results"]
    plan_source_evidence = []
    if source_set_matches and context_match and index_path is not None:
        plan_source_evidence = _component_plan_source_evidence(
            component=component,
            index_path=index_path,
            limit=source_top_k,
        )

    if context.get("needs_reviewer_resolution"):
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The forest-plan context resolver requires reviewer resolution before component findings can be trusted."
    elif not source_set_matches:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component inventory source set does not match the review source set."
    elif not context_match:
        applicability_status = "not_applicable"
        finding_status = "not_applicable"
        rationale = "The resolved package context does not match this component's geography, management area, or overlay."
    elif not plan_source_evidence:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component could not be verified against current source-library plan evidence."
    elif package_evidence:
        applicability_status = "applicable"
        finding_status = "supported"
        rationale = "The component is applicable and the EA package contains matching evidence."
    else:
        applicability_status = "applicable"
        finding_status = "gap"
        rationale = "The component is applicable and source-library plan evidence exists, but matching EA package evidence was not found."

    compliance_status = _compliance_status(
        component=component,
        finding_status=finding_status,
    )
    reviewer_items = _reviewer_resolution_items_for_finding(
        review_id=review_id,
        component=component,
        finding_status=finding_status,
        applicability_status=applicability_status,
        rationale=rationale,
        source_set_id=source_set_id,
        source_set_matches=source_set_matches,
        plan_source_evidence=plan_source_evidence,
        package_evidence=package_evidence,
    )
    return {
        "finding_id": f"{component['component_id']}-finding",
        "review_id": review_id,
        "component_id": component["component_id"],
        "component_type": component["component_type"],
        "applicability_status": applicability_status,
        "finding_status": finding_status,
        "compliance_status": compliance_status,
        "applicability_basis": {
            "source_set_id": source_set_id,
            "component_source_set_id": component["source_set_id"],
            "source_set_matches": source_set_matches,
            "matched_context": _matched_context(context, component),
            "component_context": {
                "geographic_area_ids": component["geographic_area_ids"],
                "management_area_ids": component["management_area_ids"],
                "overlay_ids": component["overlay_ids"],
                "resource_topics": component["resource_topics"],
                "activity_tags": component["activity_tags"],
            },
            "package_query": package_search["query"],
            "package_evidence_terms": package_search["required_terms"],
        },
        "plan_source_evidence": plan_source_evidence,
        "package_evidence": package_evidence,
        "rationale": rationale,
        "reviewer_resolution_items": reviewer_items,
        "provenance": _finding_provenance(
            review_id=review_id,
            component=component,
            source_set_id=source_set_id,
            finding_status=finding_status,
        ),
    }


def _compliance_status(*, component: dict, finding_status: str) -> str:
    if component["component_type"] != "standard":
        return "not_evaluated_for_compliance"
    if finding_status == "supported":
        return "complies"
    if finding_status == "not_applicable":
        return "not_applicable"
    if finding_status in {"gap", "partial"}:
        return "insufficient_evidence"
    return "needs_reviewer_resolution"


def _component_package_search(
    *,
    component: dict,
    package_chunks: list[dict],
    limit: int,
) -> dict:
    terms = component.get("package_evidence_terms") or [
        *component.get("resource_topics", []),
        *component.get("activity_tags", []),
    ]
    query = " ".join([component["section_heading"], component["component_text"], *terms])
    return _search_package_chunks(
        package_chunks,
        query=query,
        required_terms=list(terms),
        limit=limit,
    )


def _component_plan_source_evidence(
    *,
    component: dict,
    index_path: Path,
    limit: int,
) -> list[dict]:
    result = query_retrieval_index(
        index_path=index_path,
        query=component["component_text"],
        limit=max(limit, 5),
        document_role="forest_plan",
        source_record_id=component["source_record_id"],
    )
    source_chunk_ids = set(component["source_chunk_ids"])
    filtered = [
        row
        for row in result["results"]
        if not source_chunk_ids or row.get("chunk_id") in source_chunk_ids
    ]
    return filtered[:limit]


def _context_matches_component(context: dict, component: dict) -> bool:
    matched = _matched_context(context, component)
    return all(
        (
            not component[field]
            or bool(matched[matched_field])
        )
        for field, matched_field in (
            ("geographic_area_ids", "geographic_area_ids"),
            ("management_area_ids", "management_area_ids"),
            ("overlay_ids", "overlay_ids"),
        )
    )


def _matched_context(context: dict, component: dict) -> dict:
    geographic_area_ids = _resolved_entry_ids(context, "geographic_areas")
    management_area_ids = _resolved_entry_ids(context, "management_areas")
    overlay_ids = _resolved_entry_ids(context, "overlays")
    return {
        "geographic_area_ids": sorted(set(component["geographic_area_ids"]) & geographic_area_ids),
        "management_area_ids": sorted(set(component["management_area_ids"]) & management_area_ids),
        "overlay_ids": sorted(set(component["overlay_ids"]) & overlay_ids),
    }


def _resolved_entry_ids(context: dict, key: str) -> set[str]:
    return {str(entry.get("entry_id")) for entry in context.get(key, []) if entry.get("entry_id")}


def _reviewer_resolution_items_for_finding(
    *,
    review_id: str,
    component: dict,
    finding_status: str,
    applicability_status: str,
    rationale: str,
    source_set_id: str | None,
    source_set_matches: bool,
    plan_source_evidence: list[dict],
    package_evidence: list[dict],
) -> list[dict]:
    if finding_status in {"supported", "not_applicable"}:
        return []
    if not source_set_matches:
        reason = "component_source_set_drift"
        message = "Refresh or rebuild the component inventory for the active source set."
        severity = "high"
    elif not plan_source_evidence:
        reason = "missing_plan_source_evidence"
        message = "Verify the component against current source-library chunks before relying on it."
        severity = "high"
    elif not package_evidence:
        reason = "missing_package_evidence"
        message = "Review the EA package for evidence addressing the applicable plan component."
        severity = "medium"
    else:
        reason = "needs_reviewer_resolution"
        message = rationale
        severity = "medium"
    return [
        {
            "item_id": f"{component['component_id']}-{reason}",
            "review_id": review_id,
            "finding_id": f"{component['component_id']}-finding",
            "component_id": component["component_id"],
            "reason": reason,
            "severity": severity,
            "message": message,
            "finding_status": finding_status,
            "applicability_status": applicability_status,
            "source_set_id": source_set_id,
            "component_source_set_id": component["source_set_id"],
            "provenance": _finding_provenance(
                review_id=review_id,
                component=component,
                source_set_id=source_set_id,
                finding_status=finding_status,
            ),
        }
    ]


def _reviewer_resolution_queue(
    *,
    review_id: str,
    source_set_id: str | None,
    findings: list[dict],
) -> dict:
    items = [
        item
        for finding in findings
        for item in finding.get("reviewer_resolution_items", [])
    ]
    return {
        "schema_version": FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "item_count": len(items),
        "items": items,
    }


def _component_inventory_coverage(
    *,
    review_id: str,
    source_set_id: str | None,
    component_inventory_path: Path,
    components: list[dict],
) -> dict:
    component_type_counts = Counter(component["component_type"] for component in components)
    standard_component_ids = sorted(
        component["component_id"]
        for component in components
        if component["component_type"] == "standard"
    )
    source_set_mismatches = [
        {
            "component_id": component["component_id"],
            "component_source_set_id": component["source_set_id"],
            "review_source_set_id": source_set_id,
        }
        for component in components
        if component["source_set_id"] != source_set_id
    ]
    missing_source_chunks = [
        component["component_id"]
        for component in components
        if not component.get("source_chunk_ids")
    ]
    missing_provenance = [
        component["component_id"]
        for component in components
        if not _provenance_complete(component.get("provenance"))
    ]
    checks = [
        {
            "name": "component_inventory_has_components",
            "passed": bool(components),
            "details": {"component_count": len(components)},
        },
        {
            "name": "component_inventory_has_standard_records",
            "passed": bool(standard_component_ids),
            "details": {
                "standard_count": len(standard_component_ids),
                "standard_component_ids": standard_component_ids,
            },
        },
        {
            "name": "component_source_sets_match_review_source_set",
            "passed": bool(source_set_id) and not source_set_mismatches,
            "details": {"mismatches": source_set_mismatches},
        },
        {
            "name": "component_records_have_source_chunks",
            "passed": not missing_source_chunks,
            "details": {"component_ids": missing_source_chunks},
        },
        {
            "name": "component_records_have_provenance",
            "passed": not missing_provenance,
            "details": {"component_ids": missing_provenance},
        },
    ]
    return {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "coverage_scope": "selected_component_inventory",
        "component_count": len(components),
        "component_type_counts": dict(component_type_counts),
        "standard_count": len(standard_component_ids),
        "standard_component_ids": standard_component_ids,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _applicable_standard_coverage(
    *,
    review_id: str,
    source_set_id: str | None,
    components: list[dict],
    findings: list[dict],
) -> dict:
    findings_by_component_id = {finding["component_id"]: finding for finding in findings}
    standard_components = [
        component for component in components if component["component_type"] == "standard"
    ]
    rows = [
        _standard_coverage_row(
            component=component,
            finding=findings_by_component_id.get(component["component_id"]),
        )
        for component in standard_components
    ]
    applicable_rows = [row for row in rows if row["applicability_status"] == "applicable"]
    missing_finding_ids = [
        row["component_id"] for row in rows if "missing_finding" in row["failure_reasons"]
    ]
    unapplied_applicable_standard_ids = [
        row["component_id"] for row in applicable_rows if not row["standard_applied"]
    ]
    invalid_status_ids = [
        row["component_id"]
        for row in rows
        if row["compliance_status"] not in VALID_COMPLIANCE_STATUSES
    ]
    checks = [
        {
            "name": "standard_inventory_has_standards",
            "passed": bool(standard_components),
            "details": {"standard_count": len(standard_components)},
        },
        {
            "name": "standard_findings_present",
            "passed": not missing_finding_ids,
            "details": {"component_ids": missing_finding_ids},
        },
        {
            "name": "standard_compliance_statuses_are_valid",
            "passed": not invalid_status_ids,
            "details": {"component_ids": invalid_status_ids},
        },
        {
            "name": "applicable_standards_have_package_and_plan_evidence",
            "passed": not unapplied_applicable_standard_ids,
            "details": {"component_ids": unapplied_applicable_standard_ids},
        },
    ]
    all_applicable_standards_applied = all(
        row["standard_applied"] for row in applicable_rows
    )
    return {
        "schema_version": FOREST_PLAN_APPLICABLE_STANDARD_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "standard_count": len(standard_components),
        "applicable_standard_count": len(applicable_rows),
        "applied_standard_count": sum(1 for row in applicable_rows if row["standard_applied"]),
        "all_applicable_standards_applied": all_applicable_standards_applied,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "standards": rows,
    }


def _standard_coverage_row(*, component: dict, finding: dict | None) -> dict:
    if finding is None:
        return {
            "component_id": component["component_id"],
            "finding_id": None,
            "applicability_status": "needs_reviewer_resolution",
            "finding_status": "needs_reviewer_resolution",
            "compliance_status": "needs_reviewer_resolution",
            "plan_source_evidence_count": 0,
            "package_evidence_count": 0,
            "standard_applied": False,
            "failure_reasons": ["missing_finding"],
        }
    plan_source_evidence_count = len(finding.get("plan_source_evidence") or [])
    package_evidence_count = len(finding.get("package_evidence") or [])
    compliance_status = str(finding.get("compliance_status") or "")
    failure_reasons = []
    if finding.get("applicability_status") == "applicable":
        if plan_source_evidence_count == 0:
            failure_reasons.append("missing_plan_source_evidence")
        if package_evidence_count == 0:
            failure_reasons.append("missing_package_evidence")
        if compliance_status in {"insufficient_evidence", "needs_reviewer_resolution", ""}:
            failure_reasons.append("unresolved_standard_compliance")
    elif finding.get("applicability_status") in {"candidate", "needs_reviewer_resolution"}:
        failure_reasons.append("unresolved_standard_applicability")
    if compliance_status not in VALID_COMPLIANCE_STATUSES:
        failure_reasons.append("invalid_compliance_status")
    return {
        "component_id": component["component_id"],
        "finding_id": finding["finding_id"],
        "applicability_status": finding["applicability_status"],
        "finding_status": finding["finding_status"],
        "compliance_status": compliance_status,
        "plan_source_evidence_count": plan_source_evidence_count,
        "package_evidence_count": package_evidence_count,
        "standard_applied": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


def _validation_report(
    *,
    source_set_id: str | None,
    components: list[dict],
    findings: list[dict],
    queue: dict,
    inventory_coverage: dict,
    standard_coverage: dict,
) -> dict:
    checks = [
        _check_components_present(components),
        _check_component_source_sets_current(source_set_id, components),
        _check_component_provenance_complete(components),
        _check_finding_statuses(findings),
        _check_compliance_statuses(findings),
        _check_supported_findings_have_dual_evidence(findings),
        _check_gap_findings_have_plan_source_evidence(findings),
        _check_finding_provenance_complete(findings),
        _check_reviewer_resolution_queue(queue, findings),
        _check_component_inventory_coverage(inventory_coverage),
        _check_applicable_standard_coverage(standard_coverage),
    ]
    return {
        "schema_version": "forest-plan-component-findings-validation-v0",
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_components_present(components: list[dict]) -> dict:
    return {
        "name": "component_inventory_has_components",
        "passed": bool(components),
        "details": {"component_count": len(components)},
    }


def _check_component_source_sets_current(
    source_set_id: str | None,
    components: list[dict],
) -> dict:
    mismatches = [
        {
            "component_id": component["component_id"],
            "component_source_set_id": component["source_set_id"],
            "review_source_set_id": source_set_id,
        }
        for component in components
        if component["source_set_id"] != source_set_id
    ]
    return {
        "name": "component_source_sets_match_review_source_set",
        "passed": not mismatches and bool(source_set_id),
        "details": {"mismatches": mismatches},
    }


def _check_component_provenance_complete(components: list[dict]) -> dict:
    failures = [
        component["component_id"]
        for component in components
        if not _provenance_complete(component.get("provenance"))
    ]
    return {
        "name": "component_provenance_complete",
        "passed": not failures,
        "details": {"component_ids": failures},
    }


def _check_finding_statuses(findings: list[dict]) -> dict:
    invalid = [
        {"finding_id": finding.get("finding_id"), "finding_status": finding.get("finding_status")}
        for finding in findings
        if finding.get("finding_status") not in VALID_FINDING_STATUSES
        or finding.get("applicability_status") not in VALID_APPLICABILITY_STATUSES
    ]
    return {
        "name": "finding_statuses_are_valid",
        "passed": bool(findings) and not invalid,
        "details": {"invalid": invalid, "finding_count": len(findings)},
    }


def _check_compliance_statuses(findings: list[dict]) -> dict:
    invalid = [
        {
            "finding_id": finding.get("finding_id"),
            "compliance_status": finding.get("compliance_status"),
        }
        for finding in findings
        if finding.get("compliance_status") not in VALID_COMPLIANCE_STATUSES
    ]
    return {
        "name": "compliance_statuses_are_valid",
        "passed": bool(findings) and not invalid,
        "details": {"invalid": invalid, "finding_count": len(findings)},
    }


def _check_supported_findings_have_dual_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["finding_id"]
        for finding in findings
        if finding.get("finding_status") in {"supported", "partial"}
        and (not finding.get("package_evidence") or not finding.get("plan_source_evidence"))
    ]
    return {
        "name": "supported_findings_have_package_and_plan_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_gap_findings_have_plan_source_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["finding_id"]
        for finding in findings
        if finding.get("finding_status") == "gap" and not finding.get("plan_source_evidence")
    ]
    return {
        "name": "gap_findings_have_plan_source_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_finding_provenance_complete(findings: list[dict]) -> dict:
    failures = [
        finding["finding_id"]
        for finding in findings
        if not _provenance_complete(finding.get("provenance"))
    ]
    return {
        "name": "finding_provenance_complete",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_reviewer_resolution_queue(queue: dict, findings: list[dict]) -> dict:
    queued_finding_ids = {item.get("finding_id") for item in queue.get("items", [])}
    expected = {
        finding["finding_id"]
        for finding in findings
        if finding.get("finding_status") in {"gap", "needs_reviewer_resolution", "partial"}
    }
    missing = sorted(expected - queued_finding_ids)
    invalid_schema = queue.get("schema_version") != FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION
    return {
        "name": "reviewer_resolution_queue_covers_unresolved_findings",
        "passed": not missing and not invalid_schema,
        "details": {
            "missing_finding_ids": missing,
            "queue_schema_version": queue.get("schema_version"),
            "item_count": len(queue.get("items", [])),
        },
    }


def _check_component_inventory_coverage(inventory_coverage: dict) -> dict:
    return {
        "name": "component_inventory_coverage_passes",
        "passed": bool(inventory_coverage.get("passed")),
        "details": {
            "schema_version": inventory_coverage.get("schema_version"),
            "component_count": inventory_coverage.get("component_count"),
            "standard_count": inventory_coverage.get("standard_count"),
        },
    }


def _check_applicable_standard_coverage(standard_coverage: dict) -> dict:
    return {
        "name": "all_applicable_standards_applied",
        "passed": bool(standard_coverage.get("passed"))
        and bool(standard_coverage.get("all_applicable_standards_applied")),
        "details": {
            "schema_version": standard_coverage.get("schema_version"),
            "standard_count": standard_coverage.get("standard_count"),
            "applicable_standard_count": standard_coverage.get("applicable_standard_count"),
            "applied_standard_count": standard_coverage.get("applied_standard_count"),
        },
    }


def _summary(
    *,
    review_id: str,
    source_set_id: str | None,
    component_inventory_path: Path,
    findings_path: Path,
    markdown_path: Path,
    queue_path: Path,
    inventory_coverage_path: Path,
    standard_coverage_path: Path,
    components: list[dict],
    findings: list[dict],
    queue: dict,
    validation: dict,
    inventory_coverage: dict,
    standard_coverage: dict,
) -> dict:
    status_counts = Counter(finding["finding_status"] for finding in findings)
    applicability_counts = Counter(finding["applicability_status"] for finding in findings)
    compliance_status_counts = Counter(finding["compliance_status"] for finding in findings)
    provenance_complete_count = sum(
        1 for finding in findings if _provenance_complete(finding.get("provenance"))
    )
    return {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "findings_path": str(findings_path),
        "markdown_path": str(markdown_path),
        "reviewer_resolution_queue_path": str(queue_path),
        "component_inventory_coverage_path": str(inventory_coverage_path),
        "applicable_standard_coverage_path": str(standard_coverage_path),
        "component_count": len(components),
        "finding_count": len(findings),
        "standard_count": int(standard_coverage.get("standard_count") or 0),
        "applicable_standard_count": int(
            standard_coverage.get("applicable_standard_count") or 0
        ),
        "applied_standard_count": int(standard_coverage.get("applied_standard_count") or 0),
        "all_applicable_standards_applied": bool(
            standard_coverage.get("all_applicable_standards_applied")
        ),
        "applicable_count": applicability_counts.get("applicable", 0),
        "supported_count": status_counts.get("supported", 0),
        "partial_count": status_counts.get("partial", 0),
        "gap_count": status_counts.get("gap", 0),
        "not_applicable_count": status_counts.get("not_applicable", 0),
        "needs_reviewer_resolution_count": status_counts.get("needs_reviewer_resolution", 0),
        "finding_status_counts": dict(status_counts),
        "applicability_status_counts": dict(applicability_counts),
        "compliance_status_counts": dict(compliance_status_counts),
        "reviewer_resolution_count": int(queue.get("item_count") or 0),
        "provenance_complete_count": provenance_complete_count,
        "component_inventory_coverage_passed": bool(inventory_coverage.get("passed")),
        "applicable_standard_coverage_passed": bool(standard_coverage.get("passed")),
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"],
    }


def _finding_provenance(
    *,
    review_id: str,
    component: dict,
    source_set_id: str | None,
    finding_status: str,
) -> dict:
    return {
        "entity": {
            "type": "forest_plan_component_finding",
            "review_id": review_id,
            "component_id": component["component_id"],
            "source_set_id": source_set_id,
        },
        "activity": {
            "type": "forest_plan_component_evaluation",
            "schema_version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
            "finding_status": finding_status,
            "evaluated_at": _utc_now(),
        },
        "agent": {
            "type": "deterministic_code",
            "name": "usfs_r1_ea_sources.forest_plan_components",
            "version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
        },
    }


def _markdown_report(report: dict, queue: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Forest Plan Component Findings",
        "",
        f"- Review ID: `{summary['review_id']}`",
        f"- Source set: `{summary['source_set_id']}`",
        f"- Reviewer ready: `{summary['reviewer_ready']}`",
        f"- Findings: `{summary['finding_status_counts']}`",
        f"- Reviewer-resolution items: `{summary['reviewer_resolution_count']}`",
        "",
        "## Findings",
        "",
    ]
    components_by_id = {
        component["component_id"]: component for component in report.get("components", [])
    }
    for finding in report["findings"]:
        component = components_by_id.get(finding["component_id"], {})
        lines.extend(
            [
                f"### {finding['component_id']}",
                "",
                f"- Component type: `{finding['component_type']}`",
                f"- Status: `{finding['finding_status']}`",
                f"- Applicability: `{finding['applicability_status']}`",
                f"- Source record: `{component.get('source_record_id')}`",
                f"- Rationale: {finding['rationale']}",
            ]
        )
        if finding["plan_source_evidence"]:
            evidence = finding["plan_source_evidence"][0]
            lines.extend(
                [
                    f"- Plan citation: `{evidence.get('citation_label')}`",
                    f"- Plan evidence: {_compact(evidence.get('evidence_span', {}).get('text'))}",
                ]
            )
        if finding["package_evidence"]:
            evidence = finding["package_evidence"][0]
            lines.extend(
                [
                    f"- Package citation: `{evidence.get('citation_label')}`",
                    f"- Package evidence: {_compact(evidence.get('evidence_span', {}).get('text'))}",
                ]
            )
        lines.append("")
    if queue.get("items"):
        lines.extend(["## Reviewer Resolution Queue", ""])
        for item in queue["items"]:
            lines.extend(
                [
                    f"- `{item['item_id']}`: {item['message']}",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _compact(value: object, limit: int = 360) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _provenance_complete(provenance: object) -> bool:
    if not isinstance(provenance, dict):
        return False
    return all(
        isinstance(provenance.get(key), dict) and bool(provenance[key])
        for key in ("entity", "activity", "agent")
    )


def _require_provenance(value: object, context: str) -> dict:
    if not _provenance_complete(value):
        raise ValueError(f"{context} must contain non-empty entity, activity, and agent objects.")
    return dict(value)


def _require_object(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object.")
    return value


def _require_list(value: dict, field: str, context: str) -> list:
    raw = value.get(field)
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{context}.{field} must be a non-empty list.")
    return raw


def _require_string_list(
    value: dict,
    field: str,
    context: str,
    *,
    required: bool = True,
) -> list[str]:
    raw = value.get(field)
    if raw is None and not required:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{context}.{field} must be a list.")
    strings = []
    for index, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}.{field}[{index}] must be a non-empty string.")
        strings.append(item.strip())
    if required and not strings:
        raise ValueError(f"{context}.{field} cannot be empty.")
    return strings


def _require_string(value: dict, field: str, context: str) -> str:
    raw = value.get(field)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{context}.{field} must be a non-empty string.")
    return raw.strip()


def _require_safe_string(value: dict, field: str, context: str) -> str:
    raw = _require_string(value, field, context)
    if not SAFE_ID_RE.fullmatch(raw):
        raise ValueError(
            f"{context}.{field} must contain only letters, numbers, dot, colon, underscore, or hyphen."
        )
    return raw


def _require_hex_string(value: dict, field: str, context: str) -> str:
    raw = _require_string(value, field, context)
    if not re.fullmatch(r"[0-9a-f]{64}", raw):
        raise ValueError(f"{context}.{field} must be a lowercase SHA256 hex digest.")
    return raw


def _reject_duplicate(values: list[str], field: str, context: str) -> None:
    counts = Counter(values)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"{context} contains duplicate {field} values: {duplicates}.")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
