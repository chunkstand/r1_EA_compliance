from __future__ import annotations

from collections import Counter
from typing import Any

from .forest_plan_component_eval_cases import _dedupe
from .forest_plan_component_eval_models import FOREST_PLAN_COMPONENT_EVAL_SCHEMA_VERSION
from .forest_plan_components_common import normalize_forest_plan_component_identifier

def _checks(
    *,
    contract: dict[str, Any],
    artifacts: dict[str, Any],
    case_results: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "eval_contract_valid",
            "passed": True,
            "details": {"eval_id": contract.get("eval_id")},
        },
        {
            "name": "review_artifacts_loaded",
            "passed": not artifacts["artifact_errors"],
            "details": {"artifact_errors": artifacts["artifact_errors"]},
        },
        {
            "name": "review_identity_matches_contract",
            "passed": _identity_matches_contract(contract, artifacts),
            "details": {
                "contract": {
                    "review_id": contract.get("review_id"),
                    "source_set_id": contract.get("source_set_id"),
                },
                "artifacts": _artifact_identities(artifacts),
            },
        },
        {
            "name": "eval_cases_pass",
            "passed": all(result["passed"] for result in case_results),
            "details": {
                "case_count": len(case_results),
                "failed_case_ids": [
                    result["case_id"] for result in case_results if not result["passed"]
                ],
            },
        },
        _check_case_coverage_requirements(contract, artifacts, case_results),
        _check_metric_thresholds(contract.get("metric_thresholds", {}), metrics),
    ]

def _check_case_coverage_requirements(
    contract: dict[str, Any],
    artifacts: dict[str, Any],
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    requirements = contract.get("coverage_requirements")
    if not isinstance(requirements, dict):
        return {
            "name": "case_coverage_requirements_met",
            "passed": True,
            "details": {"enabled": False},
        }
    failures = []
    if requirements.get("require_all_applicable_standards"):
        actual_applicable_standards = {
            normalize_forest_plan_component_identifier(component_id)
            for component_id in _applicable_standard_component_ids(artifacts)
        }
        expected_applicable_standard_cases = {
            normalize_forest_plan_component_identifier(result["component_id"])
            for result in case_results
            if result["expected"].get("applicable_standard") is True
        }
        missing = sorted(actual_applicable_standards - expected_applicable_standard_cases)
        if missing:
            failures.append(
                {
                    "requirement": "require_all_applicable_standards",
                    "missing_component_ids": missing,
                }
            )
    for field, key in (
        ("minimum_cases_by_component_type", "component_type"),
        ("minimum_cases_by_applicability_status", "applicability_status"),
    ):
        expected_minimums = requirements.get(field)
        if not isinstance(expected_minimums, dict):
            continue
        counts = Counter(
            str(result["expected"].get(key) or "")
            for result in case_results
            if result["expected"].get(key)
        )
        for value, minimum in expected_minimums.items():
            actual = counts.get(str(value), 0)
            required = _safe_int(minimum)
            if actual < required:
                failures.append(
                    {
                        "requirement": field,
                        "value": str(value),
                        "min": required,
                        "actual": actual,
                    }
                )
    minimum_section_bound = _safe_int(requirements.get("minimum_section_bound_cases"))
    if minimum_section_bound:
        section_bound_count = sum(
            1 for result in case_results if "package_section" in result["expected"]
        )
        if section_bound_count < minimum_section_bound:
            failures.append(
                {
                    "requirement": "minimum_section_bound_cases",
                    "min": minimum_section_bound,
                    "actual": section_bound_count,
                }
            )
    minimum_not_applicable = _safe_int(requirements.get("minimum_not_applicable_cases"))
    if minimum_not_applicable:
        not_applicable_count = sum(
            1
            for result in case_results
            if result["expected"].get("applicability_status") == "not_applicable"
        )
        if not_applicable_count < minimum_not_applicable:
            failures.append(
                {
                    "requirement": "minimum_not_applicable_cases",
                    "min": minimum_not_applicable,
                    "actual": not_applicable_count,
                }
            )
    return {
        "name": "case_coverage_requirements_met",
        "passed": not failures,
        "details": {
            "enabled": True,
            "failures": failures,
        },
    }

def _applicable_standard_component_ids(artifacts: dict[str, Any]) -> list[str]:
    coverage = artifacts.get("standard_coverage")
    standards = coverage.get("standards") if isinstance(coverage, dict) else None
    if not isinstance(standards, list):
        return []
    return _dedupe(
        str(row.get("component_id") or "")
        for row in standards
        if isinstance(row, dict) and row.get("applicability_status") == "applicable"
    )

def _check_metric_thresholds(thresholds: object, metrics: dict[str, Any]) -> dict[str, Any]:
    failures = []
    threshold_map = thresholds if isinstance(thresholds, dict) else {}
    for metric_name, threshold in threshold_map.items():
        actual = metrics.get(metric_name)
        if not isinstance(actual, int | float):
            failures.append(
                {
                    "metric": metric_name,
                    "reason": "metric_missing",
                    "actual": actual,
                }
            )
            continue
        if not isinstance(threshold, dict):
            failures.append(
                {
                    "metric": metric_name,
                    "reason": "invalid_threshold",
                    "actual": actual,
                }
            )
            continue
        if "min" in threshold and actual < float(threshold["min"]):
            failures.append(
                {
                    "metric": metric_name,
                    "min": float(threshold["min"]),
                    "actual": actual,
                }
            )
        if "max" in threshold and actual > float(threshold["max"]):
            failures.append(
                {
                    "metric": metric_name,
                    "max": float(threshold["max"]),
                    "actual": actual,
                }
            )
    return {
        "name": "metric_thresholds_met",
        "passed": not failures,
        "details": {"failures": failures},
    }

def _identity_matches_contract(contract: dict[str, Any], artifacts: dict[str, Any]) -> bool:
    review_id = contract.get("review_id")
    source_set_id = contract.get("source_set_id")
    return all(
        (not review_id or identity["review_id"] == review_id)
        and (not source_set_id or identity["source_set_id"] == source_set_id)
        for identity in _artifact_identities(artifacts)
    )

def _artifact_identities(artifacts: dict[str, Any]) -> list[dict[str, str | None]]:
    identities = []
    for artifact_name in (
        "component_findings",
        "standard_coverage",
        "reviewer_resolution_queue",
    ):
        artifact = artifacts.get(artifact_name)
        summary = artifact.get("summary") if isinstance(artifact, dict) else {}
        summary = summary if isinstance(summary, dict) else {}
        identities.append(
            {
                "artifact": artifact_name,
                "review_id": _string_or_none(
                    artifact.get("review_id") if isinstance(artifact, dict) else None,
                    summary.get("review_id"),
                ),
                "source_set_id": _string_or_none(
                    artifact.get("source_set_id") if isinstance(artifact, dict) else None,
                    summary.get("source_set_id"),
                ),
            }
        )
    return identities

def _string_or_none(*values: object) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None

def _review_id(artifacts: dict[str, Any]) -> str | None:
    report = artifacts.get("component_findings") if isinstance(artifacts, dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    value = report.get("review_id") or summary.get("review_id")
    return str(value) if value else None

def _source_set_id(artifacts: dict[str, Any]) -> str | None:
    report = artifacts.get("component_findings") if isinstance(artifacts, dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    value = report.get("source_set_id") or summary.get("source_set_id")
    return str(value) if value else None

def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != FOREST_PLAN_COMPONENT_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan component eval schema_version: "
            f"{contract.get('schema_version')!r}"
        )
    for field in ("eval_id", "review_id", "source_set_id"):
        if not str(contract.get(field) or "").strip():
            raise ValueError(f"Forest-plan component eval contract missing {field!r}.")
    cases = contract.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Forest-plan component eval contract must contain non-empty cases.")
    case_ids = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"Forest-plan component eval case {index} must be an object.")
        for field in ("case_id", "component_id", "applicability_status"):
            if not str(case.get(field) or "").strip():
                raise ValueError(f"Forest-plan component eval case {index} missing {field!r}.")
        case_ids.append(str(case["case_id"]))
        _validate_optional_string_list(case, "plan_source_citations", index)
        _validate_optional_string_list(case, "package_evidence_citations", index)
    duplicates = sorted(key for key, count in Counter(case_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate forest-plan component eval case IDs: {duplicates}")

def _validate_optional_string_list(case: dict[str, Any], field: str, index: int) -> None:
    if field not in case:
        return
    if not isinstance(case[field], list) or any(not isinstance(item, str) for item in case[field]):
        raise ValueError(f"Forest-plan component eval case {index} {field} must be a string list.")

def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
