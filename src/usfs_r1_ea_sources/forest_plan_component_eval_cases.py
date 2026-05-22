from __future__ import annotations

from collections import Counter
from typing import Any

from .forest_plan_component_eval_models import RESOLVED_COMPLIANCE_STATUSES

def _evaluate_cases(*, cases: list[dict[str, Any]], artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    findings_by_component = _findings_by_component(artifacts["component_findings"])
    components_by_id = _components_by_id(artifacts["component_findings"])
    standard_rows_by_component = _standard_rows_by_component(artifacts["standard_coverage"])
    queue_component_ids = _queue_component_ids(artifacts["reviewer_resolution_queue"])
    return [
        _case_result(
            case=case,
            finding=findings_by_component.get(str(case.get("component_id") or "")),
            component=components_by_id.get(str(case.get("component_id") or "")),
            standard_row=standard_rows_by_component.get(str(case.get("component_id") or "")),
            queue_component_ids=queue_component_ids,
        )
        for case in cases
    ]

def _case_result(
    *,
    case: dict[str, Any],
    finding: dict[str, Any] | None,
    component: dict[str, Any] | None,
    standard_row: dict[str, Any] | None,
    queue_component_ids: set[str],
) -> dict[str, Any]:
    component_id = str(case.get("component_id") or "")
    finding = finding or {}
    component = component or {}
    actual = _actual_case_values(
        component_id=component_id,
        finding=finding,
        component=component,
        standard_row=standard_row,
        queue_component_ids=queue_component_ids,
    )
    expected = _expected_case_values(case)
    failure_categories: list[str] = []
    if not finding:
        failure_categories.append("component_finding_missing")
    if "component_type" in expected and actual.get("component_type") != expected["component_type"]:
        failure_categories.append("component_type_mismatch")
    if (
        "applicability_status" in expected
        and actual.get("applicability_status") != expected["applicability_status"]
    ):
        failure_categories.append("component_applicability_mismatch")
    if (
        "applicable_standard" in expected
        and actual.get("applicable_standard") != expected["applicable_standard"]
    ):
        failure_categories.append("applicable_standard_mismatch")
    if (
        "compliance_status" in expected
        and actual.get("compliance_status") != expected["compliance_status"]
    ):
        failure_categories.append("compliance_status_mismatch")
    if "package_section" in expected and not _section_matches(
        actual.get("package_section"),
        expected["package_section"],
    ):
        failure_categories.append("package_section_mismatch")
    if "plan_source_citations" in expected and not _citations_match(
        actual.get("plan_source_citations", []),
        expected["plan_source_citations"],
    ):
        failure_categories.append("plan_source_citation_mismatch")
    if "package_evidence_citations" in expected and not _citations_match(
        actual.get("package_evidence_citations", []),
        expected["package_evidence_citations"],
    ):
        failure_categories.append("package_evidence_citation_mismatch")
    if (
        "reviewer_resolution_state" in expected
        and actual.get("reviewer_resolution_state") != expected["reviewer_resolution_state"]
    ):
        failure_categories.append("reviewer_resolution_state_mismatch")
    if (
        expected.get("component_type") == "standard"
        and standard_row is None
        and "applicable_standard" in expected
    ):
        failure_categories.append("standard_coverage_missing")
    return {
        "case_id": case["case_id"],
        "component_id": component_id,
        "description": case.get("description"),
        "actual": actual,
        "expected": expected,
        "passed": not failure_categories,
        "failure_categories": failure_categories,
    }

def _actual_case_values(
    *,
    component_id: str,
    finding: dict[str, Any],
    component: dict[str, Any],
    standard_row: dict[str, Any] | None,
    queue_component_ids: set[str],
) -> dict[str, Any]:
    component_type = finding.get("component_type") or component.get("component_type")
    applicability_status = finding.get("applicability_status")
    compliance_status = finding.get("compliance_status")
    open_resolution = bool(finding.get("reviewer_resolution_items")) or component_id in queue_component_ids
    standard_applicability = (
        standard_row.get("applicability_status") if isinstance(standard_row, dict) else None
    )
    package_section = (
        standard_row.get("ea_review_section")
        if isinstance(standard_row, dict)
        else _finding_package_section(finding)
    )
    return {
        "component_type": component_type,
        "applicability_status": applicability_status,
        "finding_status": finding.get("finding_status"),
        "compliance_status": compliance_status,
        "applicable_standard": bool(
            component_type == "standard" and standard_applicability == "applicable"
        ),
        "standard_applied": (
            bool(standard_row.get("standard_applied"))
            if isinstance(standard_row, dict)
            else None
        ),
        "package_section": package_section,
        "plan_source_citations": _actual_plan_citations(finding, standard_row),
        "package_evidence_citations": _actual_package_citations(finding, standard_row),
        "reviewer_resolution_state": "open" if open_resolution else "closed",
        "plan_source_evidence_count": len(finding.get("plan_source_evidence") or []),
        "package_evidence_count": len(finding.get("package_evidence") or []),
    }

def _expected_case_values(case: dict[str, Any]) -> dict[str, Any]:
    expected = {}
    optional_fields = (
        "component_type",
        "applicability_status",
        "applicable_standard",
        "compliance_status",
        "package_section",
        "plan_source_citations",
        "package_evidence_citations",
        "reviewer_resolution_state",
    )
    for field in optional_fields:
        if field in case:
            expected[field] = case[field]
    return expected

def _metrics(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    expected_applicable = {
        result["case_id"]: result
        for result in case_results
        if result["expected"].get("applicability_status") == "applicable"
    }
    expected_not_applicable = {
        result["case_id"]: result
        for result in case_results
        if result["expected"].get("applicability_status") == "not_applicable"
    }
    predicted_applicable = {
        result["case_id"]: result
        for result in case_results
        if result["actual"].get("applicability_status") == "applicable"
    }
    true_positive = len(set(expected_applicable) & set(predicted_applicable))
    false_positive = len(set(predicted_applicable) - set(expected_applicable))
    false_negative = len(set(expected_applicable) - set(predicted_applicable))
    true_negative = len(set(expected_not_applicable) - set(predicted_applicable))

    expected_applicable_standards = [
        result for result in case_results if result["expected"].get("applicable_standard") is True
    ]
    found_applicable_standards = [
        result
        for result in expected_applicable_standards
        if result["actual"].get("applicable_standard") is True
    ]
    section_scored = [result for result in case_results if "package_section" in result["expected"]]
    plan_citation_scored = [
        result for result in case_results if "plan_source_citations" in result["expected"]
    ]
    package_citation_scored = [
        result for result in case_results if "package_evidence_citations" in result["expected"]
    ]
    compliance_scored = [
        result for result in case_results if "compliance_status" in result["expected"]
    ]
    reviewer_scored = [
        result for result in case_results if "reviewer_resolution_state" in result["expected"]
    ]
    reviewer_closed = [
        result for result in reviewer_scored if result["actual"].get("reviewer_resolution_state") == "closed"
    ]
    return {
        "case_count": len(case_results),
        "component_applicability_true_positive_count": true_positive,
        "component_applicability_false_positive_count": false_positive,
        "component_applicability_false_negative_count": false_negative,
        "component_applicability_true_negative_count": true_negative,
        "component_applicability_precision": _rate(true_positive, true_positive + false_positive),
        "component_applicability_recall": _rate(true_positive, true_positive + false_negative),
        "applicable_standard_recall": _rate(
            len(found_applicable_standards),
            len(expected_applicable_standards),
        ),
        "expected_applicable_standard_count": len(expected_applicable_standards),
        "false_applicable_component_rate": _rate(false_positive, len(expected_not_applicable)),
        "package_section_match_rate": _case_rate(
            section_scored,
            "package_section_mismatch",
        ),
        "plan_source_citation_correctness_rate": _case_rate(
            plan_citation_scored,
            "plan_source_citation_mismatch",
        ),
        "package_evidence_citation_correctness_rate": _case_rate(
            package_citation_scored,
            "package_evidence_citation_mismatch",
        ),
        "resolved_compliance_status_rate": _rate(
            sum(
                1
                for result in compliance_scored
                if result["actual"].get("compliance_status") in RESOLVED_COMPLIANCE_STATUSES
            ),
            len(compliance_scored),
        ),
        "compliance_status_match_rate": _case_rate(
            compliance_scored,
            "compliance_status_mismatch",
        ),
        "reviewer_resolution_closure_rate": _rate(len(reviewer_closed), len(reviewer_scored)),
        "reviewer_resolution_state_match_rate": _case_rate(
            reviewer_scored,
            "reviewer_resolution_state_mismatch",
        ),
    }

def _case_rate(results: list[dict[str, Any]], failure_category: str) -> float:
    return _rate(
        sum(1 for result in results if failure_category not in result["failure_categories"]),
        len(results),
    )

def _findings_by_component(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    findings = report.get("findings")
    if not isinstance(findings, list):
        return {}
    return {
        str(finding.get("component_id")): finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("component_id")
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

def _standard_rows_by_component(coverage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    standards = coverage.get("standards")
    if not isinstance(standards, list):
        return {}
    return {
        str(row.get("component_id")): row
        for row in standards
        if isinstance(row, dict) and row.get("component_id")
    }

def _queue_component_ids(queue: dict[str, Any]) -> set[str]:
    items = queue.get("items")
    if not isinstance(items, list):
        return set()
    return {
        str(item.get("component_id"))
        for item in items
        if isinstance(item, dict) and item.get("component_id")
    }

def _actual_plan_citations(
    finding: dict[str, Any],
    standard_row: dict[str, Any] | None,
) -> list[str]:
    if isinstance(standard_row, dict) and "plan_source_citations" in standard_row:
        return _string_values(standard_row.get("plan_source_citations"))
    return _citation_labels(finding.get("plan_source_evidence") or [])

def _actual_package_citations(
    finding: dict[str, Any],
    standard_row: dict[str, Any] | None,
) -> list[str]:
    if isinstance(standard_row, dict) and "package_evidence_citations" in standard_row:
        return _string_values(standard_row.get("package_evidence_citations"))
    return _citation_labels(finding.get("package_evidence") or [])

def _finding_package_section(finding: dict[str, Any]) -> str | None:
    for evidence in finding.get("package_evidence") or []:
        if not isinstance(evidence, dict):
            continue
        if evidence.get("review_section"):
            return str(evidence["review_section"])
        provenance = evidence.get("provenance") if isinstance(evidence.get("provenance"), dict) else {}
        for field in ("section", "heading"):
            if provenance.get(field):
                return str(provenance[field])
        if evidence.get("title"):
            return str(evidence["title"])
    return None

def _citation_labels(evidence_items: object) -> list[str]:
    if not isinstance(evidence_items, list):
        return []
    return _dedupe(
        str(item.get("citation_label") or "").strip()
        for item in evidence_items
        if isinstance(item, dict)
    )

def _citations_match(actual: object, expected: object) -> bool:
    actual_values = set(_string_values(actual))
    expected_values = set(_string_values(expected))
    return actual_values == expected_values

def _section_matches(actual: object, expected: object) -> bool:
    if expected is None:
        return actual in {None, ""}
    expected_values = _string_values(expected) if isinstance(expected, list) else [str(expected)]
    return str(actual or "") in expected_values

def _string_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []

def _dedupe(values: object) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result

def _failure_category_counts(case_results: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        category
        for result in case_results
        for category in result.get("failure_categories", [])
    )
    return dict(sorted(counts.items()))

def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 6)
