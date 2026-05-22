from __future__ import annotations

import json
import re
from pathlib import Path

from .forest_plan_components_common import _duplicate_values, _utc_now
from .forest_plan_components_models import FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION, FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION, SAFE_ID_RE, VALID_APPLICABILITY_STATUSES, VALID_COMPLIANCE_STATUSES, VALID_FINDING_STATUSES
from .forest_plan_components_package_search import _package_evidence_review_section


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
        _check_supported_package_evidence_section_bindings(findings),
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


def _check_supported_package_evidence_section_bindings(findings: list[dict]) -> dict:
    failures = []
    for finding in findings:
        if finding.get("finding_status") not in {"supported", "partial"}:
            continue
        for evidence in finding.get("package_evidence") or []:
            section_binding = (
                evidence.get("section_binding")
                if isinstance(evidence.get("section_binding"), dict)
                else None
            )
            if section_binding and section_binding.get("matched") is True:
                continue
            if evidence.get("determination_source") == "ea_plan_consistency_table":
                continue
            failures.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "component_id": finding.get("component_id"),
                    "citation_label": evidence.get("citation_label"),
                    "review_section": evidence.get("review_section")
                    or _package_evidence_review_section(evidence),
                    "package_section_family": (
                        section_binding.get("package_section_family")
                        if section_binding
                        else None
                    ),
                    "component_section_families": (
                        section_binding.get("component_section_families")
                        if section_binding
                        else None
                    ),
                    "reason": (
                        "section_binding_mismatch"
                        if section_binding
                        else "missing_section_binding"
                    ),
                }
            )
    return {
        "name": "supported_package_evidence_section_bindings_match",
        "passed": not failures,
        "details": {"failures": failures, "failure_count": len(failures)},
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
            "component_inventory_build_coverage_required": inventory_coverage.get(
                "component_inventory_build_coverage_required"
            ),
            "component_inventory_build_coverage_passed": inventory_coverage.get(
                "component_inventory_build_coverage_passed"
            ),
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
    duplicates = _duplicate_values(values)
    if duplicates:
        raise ValueError(f"{context} contains duplicate {field} values: {duplicates}.")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object.")
            records.append(record)
    return records


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _load_component_inventory_build_coverage(component_inventory_path: Path) -> dict | None:
    coverage_path = _component_inventory_build_coverage_path(component_inventory_path)
    if not coverage_path.exists():
        return None
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {
            "schema_version": None,
            "passed": False,
            "load_error": f"Invalid JSON: {error}",
        }
    if not isinstance(coverage, dict):
        return {
            "schema_version": None,
            "passed": False,
            "load_error": "Coverage file must contain a JSON object.",
        }
    if (
        coverage.get("schema_version")
        != FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION
    ):
        coverage = dict(coverage)
        coverage["passed"] = False
        coverage["load_error"] = "Unsupported component inventory build coverage schema_version."
    return coverage


def _component_inventory_build_coverage_required(component_inventory_path: Path) -> bool:
    return (
        component_inventory_path.name == "component_inventory.json"
        and component_inventory_path.parent.name == "forest_plan_components"
    )


def _component_inventory_build_coverage_path(component_inventory_path: Path) -> Path:
    return component_inventory_path.with_name("component_inventory_build_coverage.json")
