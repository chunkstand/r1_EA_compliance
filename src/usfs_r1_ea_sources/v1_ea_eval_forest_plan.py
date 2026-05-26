from __future__ import annotations

from typing import Any

from .v1_ea_eval_support import _collect_list_values_by_key
from .v1_ea_eval_support import _collect_values_by_key
from .v1_ea_eval_support import _nested_get
from .forest_plan_components_common import normalize_forest_plan_component_identifier


def _evaluate_forest_plan(
    *,
    expectations: dict[str, Any],
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    if not expectations:
        return []
    summary = artifacts["forest_plan_context_summary"]
    context = artifacts["forest_plan_context"]
    component_findings = artifacts["forest_plan_component_findings"]
    standard_coverage = artifacts["forest_plan_applicable_standard_coverage"]
    compliance_matrix = artifacts["compliance_matrix"]
    source_record_ids = _forest_source_record_ids(summary, context)
    geo_ids = _collect_values_by_key(context, {"geographic_area_id", "entry_id", "area_id"})
    management_ids = _collect_values_by_key(context, {"management_area_id", "entry_id"})
    overlay_ids = _collect_values_by_key(context, {"overlay_id", "entry_id"})
    component_ids = {
        normalize_forest_plan_component_identifier(component_id)
        for component_id in _collect_values_by_key(
            component_findings,
            {"component_id", "standard_id", "entry_id"},
        )
    }
    applicable_standard_ids = _applicable_standard_ids(standard_coverage, component_findings)
    pending_reviewer_resolution_count = _pending_reviewer_resolution_count(artifacts)
    pending_standard_reviewer_resolution_count = _pending_standard_reviewer_resolution_count(
        artifacts
    )
    results = []

    def add_result(
        *,
        expectation_id: str,
        expected: Any,
        actual: Any,
        passed: bool,
        failure_category: str,
    ) -> None:
        results.append(
            {
                "expectation_id": expectation_id,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "failure_category": None if passed else failure_category,
            }
        )

    if expectations.get("expected_scope_status"):
        actual_scope = summary.get("scope_status") or context.get("scope_status")
        add_result(
            expectation_id="scope_status",
            expected=expectations["expected_scope_status"],
            actual=actual_scope,
            passed=actual_scope == expectations["expected_scope_status"],
            failure_category="forest_plan_scope_miss",
        )
    required_sources = {
        str(value) for value in expectations.get("required_source_record_ids", [])
    }
    if required_sources:
        add_result(
            expectation_id="required_source_record_ids",
            expected=sorted(required_sources),
            actual=sorted(source_record_ids),
            passed=required_sources.issubset(source_record_ids),
            failure_category="forest_plan_source_record_miss",
        )
    required_geo_ids = {
        str(value) for value in expectations.get("expected_geographic_area_ids", [])
    }
    if required_geo_ids:
        add_result(
            expectation_id="geographic_area_ids",
            expected=sorted(required_geo_ids),
            actual=sorted(geo_ids),
            passed=required_geo_ids.issubset(geo_ids),
            failure_category="forest_plan_component_miss",
        )
    required_management_ids = {
        str(value) for value in expectations.get("expected_management_area_ids", [])
    }
    if required_management_ids:
        add_result(
            expectation_id="management_area_ids",
            expected=sorted(required_management_ids),
            actual=sorted(management_ids),
            passed=required_management_ids.issubset(management_ids),
            failure_category="forest_plan_component_miss",
        )
    required_overlay_ids = {
        str(value) for value in expectations.get("expected_overlay_ids", [])
    }
    if required_overlay_ids:
        add_result(
            expectation_id="overlay_ids",
            expected=sorted(required_overlay_ids),
            actual=sorted(overlay_ids),
            passed=required_overlay_ids.issubset(overlay_ids),
            failure_category="forest_plan_component_miss",
        )
    expected_component_ids = {
        normalize_forest_plan_component_identifier(value)
        for value in expectations.get("expected_component_ids", [])
    }
    if expected_component_ids:
        add_result(
            expectation_id="component_ids",
            expected=sorted(expected_component_ids),
            actual=sorted(component_ids),
            passed=expected_component_ids.issubset(component_ids),
            failure_category="forest_plan_component_miss",
        )
    expected_standards = {
        normalize_forest_plan_component_identifier(value)
        for value in expectations.get("expected_applicable_standard_ids", [])
    }
    if expected_standards:
        add_result(
            expectation_id="applicable_standard_ids",
            expected=sorted(expected_standards),
            actual=sorted(applicable_standard_ids),
            passed=expected_standards.issubset(applicable_standard_ids),
            failure_category="applicable_standard_not_evaluated",
        )
    if expectations.get("min_applicable_standard_count") is not None:
        minimum = int(expectations["min_applicable_standard_count"])
        add_result(
            expectation_id="min_applicable_standard_count",
            expected=minimum,
            actual=len(applicable_standard_ids),
            passed=len(applicable_standard_ids) >= minimum,
            failure_category="applicable_standard_not_evaluated",
        )
    if expectations.get("require_all_applicable_standards_applied"):
        passed = bool(
            _nested_get(component_findings, ["summary", "all_applicable_standards_applied"])
            or _nested_get(summary, ["component_evaluation", "all_applicable_standards_applied"])
        )
        add_result(
            expectation_id="all_applicable_standards_applied",
            expected=True,
            actual=passed,
            passed=passed,
            failure_category="applicable_standard_not_evaluated",
        )
    if expectations.get("require_reviewer_ready"):
        actual_ready = bool(summary.get("reviewer_ready"))
        add_result(
            expectation_id="reviewer_ready",
            expected=True,
            actual=actual_ready,
            passed=actual_ready,
            failure_category="forest_plan_reviewer_not_ready",
        )
    if expectations.get("max_reviewer_resolution_items") is not None:
        maximum = int(expectations["max_reviewer_resolution_items"])
        actual_count = pending_reviewer_resolution_count
        add_result(
            expectation_id="reviewer_resolution_item_count",
            expected={"max": maximum},
            actual=actual_count,
            passed=actual_count <= maximum,
            failure_category="forest_plan_reviewer_resolution_open",
        )
    if expectations.get("max_standard_reviewer_resolution_items") is not None:
        maximum = int(expectations["max_standard_reviewer_resolution_items"])
        actual_count = pending_standard_reviewer_resolution_count
        add_result(
            expectation_id="standard_reviewer_resolution_item_count",
            expected={"max": maximum},
            actual=actual_count,
            passed=actual_count <= maximum,
            failure_category="forest_plan_standard_reviewer_resolution_open",
        )
    if expectations.get("require_matrix_forest_plan_compliance", True):
        matrix_details = _forest_plan_compliance_matrix_details(compliance_matrix)
        expected_standard_count = int(
            _nested_get(component_findings, ["summary", "applicable_standard_count"])
            or _nested_get(summary, ["component_evaluation", "applicable_standard_count"])
            or len(expected_standards)
        )
        matrix_visible = matrix_details["row_count"] > 0 and (
            expected_standard_count == 0
            or matrix_details["applicable_standard_row_count"] >= expected_standard_count
        )
        add_result(
            expectation_id="forest_plan_compliance_matrix",
            expected={
                "min_rows": 1,
                "applicable_standard_row_count": expected_standard_count,
            },
            actual=matrix_details,
            passed=matrix_visible,
            failure_category="forest_plan_matrix_miss",
        )
    return results


def _forest_plan_rule_bridge_index(
    *,
    contract: dict[str, Any],
    artifacts: dict[str, Any],
    section_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not contract.get("forest_plan"):
        return {}
    summary = artifacts.get("forest_plan_context_summary")
    context = artifacts.get("forest_plan_context")
    if not isinstance(summary, dict) or not isinstance(context, dict):
        return {}
    if not (
        summary.get("reviewer_ready")
        or _nested_get(summary, ["component_evaluation", "reviewer_ready"])
    ):
        return {}
    forest_source_ids = _forest_source_record_ids(summary, context)
    if not forest_source_ids:
        return {}
    bridge: dict[str, dict[str, Any]] = {}
    expectations = [
        *contract.get("rule_review_expectations", []),
        *contract.get("conditional_source_expectations", []),
    ]
    for expectation in expectations:
        rule_id = str(expectation.get("rule_id") or "").strip()
        if not rule_id or rule_id in bridge:
            continue
        expected_sources = {
            str(value)
            for value in expectation.get("expected_source_record_ids", [])
            if str(value).strip()
        }
        expected_roles = {
            str(value)
            for value in expectation.get("expected_source_document_roles", [])
            if str(value).strip()
        }
        if "forest_plan" not in expected_roles and not any(
            source_id.startswith("R1PLAN-") for source_id in expected_sources
        ):
            continue
        matched_sources = sorted(expected_sources & forest_source_ids)
        if expected_sources and not matched_sources:
            continue
        expected_sections = [
            str(section)
            for section in expectation.get("expected_package_section_ids", [])
            if str(section).strip()
        ]
        if expected_sections and not _expected_sections_detected(
            expected_sections,
            section_results,
            str(expectation.get("section_match") or "all"),
        ):
            continue
        source_ids = matched_sources or sorted(forest_source_ids)
        bridge[rule_id] = _forest_plan_bridge_row(
            rule_id=rule_id,
            source_ids=source_ids,
            expected_sections=expected_sections,
            section_results=section_results,
        )
    return bridge


def _expected_sections_detected(
    expected_sections: list[str],
    section_results: list[dict[str, Any]],
    match_mode: str,
) -> bool:
    detected = {
        str(result.get("section_id"))
        for result in section_results
        if result.get("detected")
    }
    if match_mode == "any":
        return bool(set(expected_sections) & detected)
    return set(expected_sections).issubset(detected)


def _forest_plan_bridge_row(
    *,
    rule_id: str,
    source_ids: list[str],
    expected_sections: list[str],
    section_results: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_text = _forest_plan_bridge_evidence_text(expected_sections, section_results)
    package_evidence = {
        "citation_label": "forest-plan-lane",
        "title": "Forest plan component review",
        "text": evidence_text,
        "section": "Forest Plan Consistency",
        "evidence_span": {"text": evidence_text},
        "provenance": {"section": "Forest Plan Consistency"},
    }
    source_record_id = source_ids[0] if source_ids else None
    source_evidence = {
        "citation_label": source_record_id,
        "source_record_id": source_record_id,
        "document_role": "forest_plan",
        "title": source_record_id,
        "text": "Forest plan source was validated by the forest-plan component lane.",
        "evidence_span": {
            "text": "Forest plan source was validated by the forest-plan component lane."
        },
        "provenance": {},
    }
    return {
        "rule_id": rule_id,
        "status": "pass",
        "applicability_status": "applicable",
        "applicability_mode": "conditional",
        "authority_source_record_id": source_record_id,
        "authority_document_role": "forest_plan",
        "package_evidence": package_evidence,
        "applicability_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "source_evidence": source_evidence,
        "applied_source_record_ids": source_ids,
        "applied_source_document_roles": ["forest_plan"],
        "citation_requirements_met": True,
    }


def _forest_plan_bridge_evidence_text(
    expected_sections: list[str],
    section_results: list[dict[str, Any]],
) -> str:
    chunks = []
    for result in section_results:
        if expected_sections and result.get("section_id") not in expected_sections:
            continue
        if not result.get("detected"):
            continue
        for chunk in result.get("matched_chunks", []):
            chunks.append(
                " ".join(
                    str(value)
                    for value in (
                        result.get("label"),
                        chunk.get("title"),
                        chunk.get("section"),
                        chunk.get("heading"),
                        " ".join(chunk.get("matched_terms", [])),
                    )
                    if value
                )
            )
    text = " ".join(chunk for chunk in chunks if chunk).strip()
    return text or "Forest Plan Consistency Land Management Plan"


def _forest_source_record_ids(summary: dict[str, Any], context: dict[str, Any]) -> set[str]:
    values = _collect_values_by_key(summary, {"source_record_id"}) | _collect_values_by_key(
        context,
        {"source_record_id"},
    )
    for key in (
        "required_source_record_ids",
        "present_source_record_ids",
        "missing_source_record_ids",
    ):
        values |= _collect_list_values_by_key(summary, key)
        values |= _collect_list_values_by_key(context, key)
    return values


def _applicable_standard_ids(
    standard_coverage: dict[str, Any],
    component_findings: dict[str, Any],
) -> set[str]:
    values: set[str] = set()
    rows = standard_coverage.get("standards") or standard_coverage.get("rows") or []
    for row in rows:
        if not isinstance(row, dict):
            continue
        applied = row.get("standard_applied") or row.get("applied")
        applicable = row.get("applicability_status") == "applicable" or applied
        if applicable:
            for key in ("standard_id", "component_id", "entry_id"):
                if row.get(key):
                    values.add(normalize_forest_plan_component_identifier(row[key]))
    for finding in component_findings.get("findings", []):
        if not isinstance(finding, dict):
            continue
        applicable = finding.get("applicability_status") == "applicable"
        is_standard = finding.get("component_type") == "standard" or finding.get("standard_id")
        if applicable and is_standard:
            for key in ("standard_id", "component_id", "entry_id"):
                if finding.get(key):
                    values.add(normalize_forest_plan_component_identifier(finding[key]))
    return values


def _forest_plan_compliance_matrix_details(compliance_matrix: dict[str, Any]) -> dict[str, Any]:
    section = compliance_matrix.get("forest_plan_compliance") or {}
    summary = section.get("summary") or {}
    rows = section.get("rows") or []
    applicable_standard_rows = [
        row
        for row in rows
        if row.get("component_type") == "standard"
        and row.get("applicability_status") == "applicable"
    ]
    return {
        "section_present": bool(section),
        "schema_version": section.get("schema_version"),
        "row_count": int(summary.get("row_count") or len(rows)),
        "applicable_standard_row_count": int(
            summary.get("applicable_standard_row_count")
            or len(applicable_standard_rows)
        ),
        "compliance_status_counts": summary.get("compliance_status_counts", {}),
        "load_errors": summary.get("load_errors", []),
    }


def _reviewer_resolution_count(queue: dict[str, Any]) -> int:
    summary = queue.get("summary") or {}
    for key in ("item_count", "open_item_count", "reviewer_resolution_count"):
        if summary.get(key) is not None:
            return int(summary[key])
        if queue.get(key) is not None:
            return int(queue[key])
    items = _reviewer_resolution_items(queue)
    return len(items) if isinstance(items, list) else 0


def _reviewer_resolution_count_by_component_type(queue: dict[str, Any], component_type: str) -> int:
    return sum(
        1
        for item in _reviewer_resolution_items(queue)
        if str(item.get("component_type") or "") == component_type
    )


def _reviewer_resolution_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    items = queue.get("items") or queue.get("queue") or []
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _pending_reviewer_resolution_count(artifacts: dict[str, Any]) -> int:
    item_results = _forest_plan_component_adjudication_item_results(artifacts)
    if item_results:
        return sum(
            1 for item in item_results if str(item.get("disposition") or "") == "pending"
        )
    component_adjudication = _forest_plan_component_adjudication_summary(artifacts)
    pending_count = component_adjudication.get("pending_adjudication_count")
    if pending_count is not None:
        return int(pending_count)
    if component_adjudication.get("reviewer_ready") is True:
        return 0
    return _reviewer_resolution_count(artifacts["forest_plan_reviewer_resolution_queue"])


def _pending_standard_reviewer_resolution_count(artifacts: dict[str, Any]) -> int:
    item_results = _forest_plan_component_adjudication_item_results(artifacts)
    if item_results:
        return sum(
            1
            for item in item_results
            if str(item.get("disposition") or "") == "pending"
            and str(item.get("component_type") or "") == "standard"
        )
    component_adjudication = _forest_plan_component_adjudication_summary(artifacts)
    pending_count = component_adjudication.get("pending_adjudication_count")
    if pending_count is not None and int(pending_count) == 0:
        return 0
    if component_adjudication.get("reviewer_ready") is True:
        return 0
    return _reviewer_resolution_count_by_component_type(
        artifacts["forest_plan_reviewer_resolution_queue"],
        "standard",
    )


def _forest_plan_component_adjudication_summary(artifacts: dict[str, Any]) -> dict[str, Any]:
    summary = _nested_get(artifacts["forest_plan_context_summary"], ["component_adjudication"])
    context_summary = summary if isinstance(summary, dict) else {}
    report = artifacts.get("forest_plan_component_adjudication_eval")
    if isinstance(report, dict):
        report_summary = report.get("summary")
        if isinstance(report_summary, dict):
            return {**context_summary, **report_summary}
    return context_summary


def _forest_plan_component_adjudication_item_results(
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    report = artifacts.get("forest_plan_component_adjudication_eval")
    if not isinstance(report, dict):
        return []
    items = report.get("item_results")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
