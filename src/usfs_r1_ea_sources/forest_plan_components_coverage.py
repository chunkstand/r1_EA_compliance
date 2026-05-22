from __future__ import annotations

from collections import Counter
from pathlib import Path

from .forest_plan_components_common import _compact, _dedupe_preserve_order, _utc_now
from .forest_plan_components_determination import _component_reference_key
from .forest_plan_components_models import FOREST_PLAN_APPLICABLE_STANDARD_COVERAGE_SCHEMA_VERSION, FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION, VALID_COMPLIANCE_STATUSES
from .forest_plan_components_validation import _component_inventory_build_coverage_path, _component_inventory_build_coverage_required, _load_component_inventory_build_coverage, _provenance_complete


def _component_inventory_coverage(
    *,
    review_id: str,
    source_set_id: str | None,
    component_inventory_path: Path,
    components: list[dict],
) -> dict:
    build_coverage = _load_component_inventory_build_coverage(component_inventory_path)
    build_coverage_required = _component_inventory_build_coverage_required(
        component_inventory_path
    )
    build_coverage_path = _component_inventory_build_coverage_path(component_inventory_path)
    build_coverage_passed = (
        bool(build_coverage and build_coverage.get("passed"))
        if build_coverage_required or build_coverage is not None
        else True
    )
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
        {
            "name": "component_inventory_build_coverage_passes",
            "passed": build_coverage_passed,
            "details": {
                "required": build_coverage_required,
                "path": str(build_coverage_path),
                "present": build_coverage is not None,
                "schema_version": (
                    build_coverage.get("schema_version") if build_coverage else None
                ),
                "detected_standard_count": (
                    build_coverage.get("detected_standard_count") if build_coverage else None
                ),
                "built_standard_count": (
                    build_coverage.get("built_standard_count") if build_coverage else None
                ),
                "missing_standard_ids": (
                    build_coverage.get("missing_standard_ids") if build_coverage else None
                ),
                "duplicate_standard_ids": (
                    build_coverage.get("duplicate_standard_ids") if build_coverage else None
                ),
                "component_source_accuracy_passed": (
                    build_coverage.get("component_source_accuracy_passed")
                    if build_coverage
                    else None
                ),
                "component_source_accuracy_failure_count": (
                    build_coverage.get("component_source_accuracy_failure_count")
                    if build_coverage
                    else None
                ),
            },
        },
    ]
    return {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "component_inventory_build_coverage_path": str(build_coverage_path),
        "component_inventory_build_coverage_required": build_coverage_required,
        "component_inventory_build_coverage_passed": build_coverage_passed,
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
    standards_missing_plan_source_ids = [
        row["component_id"] for row in rows if row["plan_source_evidence_count"] == 0
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
            "name": "standards_have_plan_source_evidence",
            "passed": not standards_missing_plan_source_ids,
            "details": {"component_ids": standards_missing_plan_source_ids},
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
            "component_key": _component_reference_key(component),
            "finding_id": None,
            "applicability_status": "needs_reviewer_resolution",
            "finding_status": "needs_reviewer_resolution",
            "compliance_status": "needs_reviewer_resolution",
            "plan_source_evidence_count": 0,
            "package_evidence_count": 0,
            "ea_review_section": None,
            "package_component_determination": None,
            "plan_source_citations": [],
            "package_evidence_citations": [],
            "standard_applied": False,
            "failure_reasons": ["missing_finding"],
        }
    plan_source_evidence_count = len(finding.get("plan_source_evidence") or [])
    package_evidence_count = len(finding.get("package_evidence") or [])
    compliance_status = str(finding.get("compliance_status") or "")
    failure_reasons = []
    if plan_source_evidence_count == 0:
        failure_reasons.append("missing_plan_source_evidence")
    if finding.get("applicability_status") == "applicable":
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
        "component_key": _component_reference_key(component),
        "finding_id": finding["finding_id"],
        "applicability_status": finding["applicability_status"],
        "finding_status": finding["finding_status"],
        "compliance_status": compliance_status,
        "plan_source_evidence_count": plan_source_evidence_count,
        "package_evidence_count": package_evidence_count,
        "ea_review_section": _finding_review_section(finding),
        "package_component_determination": (
            finding.get("applicability_basis", {}).get("package_component_determination")
        ),
        "plan_source_citations": _citation_labels(finding.get("plan_source_evidence") or []),
        "package_evidence_citations": _citation_labels(finding.get("package_evidence") or []),
        "standard_applied": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


def _finding_review_section(finding: dict) -> str | None:
    determination = (
        finding.get("applicability_basis", {}).get("package_component_determination")
    )
    if isinstance(determination, dict) and determination.get("review_section"):
        return str(determination["review_section"])
    for evidence in finding.get("package_evidence") or []:
        if evidence.get("review_section"):
            return str(evidence["review_section"])
        provenance = evidence.get("provenance") or {}
        for field in ("section", "heading"):
            value = str(provenance.get(field) or "").strip()
            if value:
                return value
        title = str(evidence.get("title") or "").strip()
        if title:
            return title
    return None


def _citation_labels(evidence_items: list[dict]) -> list[str]:
    return _dedupe_preserve_order(
        [
            label
            for item in evidence_items
            if (label := str(item.get("citation_label") or "").strip())
        ]
    )


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
