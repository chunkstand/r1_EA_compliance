from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import re

from .forest_plan_component_eval_coverage import (
    DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
)
from .forest_plan_component_eval_coverage import resolve_forest_plan_component_eval_file


DEFAULT_FOREST_PLAN_COMPONENT_EVAL_PATH = Path("config/forest_plan_component_eval_seed.json")
FOREST_PLAN_COMPONENT_EVAL_SCHEMA_VERSION = "forest-plan-component-eval-v0"
FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION = "forest-plan-component-eval-results-v0"
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
RESOLVED_COMPLIANCE_STATUSES = {
    "complies",
    "not_applicable",
    "potential_noncompliance",
}


@dataclass(frozen=True)
class ForestPlanComponentEvalResult:
    eval_file: Path
    review_dir: Path
    output_path: Path
    summary: dict[str, Any]


def run_forest_plan_component_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    review_dir: Path | None = None,
    eval_file: Path | None = None,
    manifest_path: Path = DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
    output_path: Path | None = None,
) -> ForestPlanComponentEvalResult:
    """Evaluate forest-plan component findings against adjudicated component cases."""

    resolved_eval_file = _resolve_eval_file(
        review_id=review_id,
        review_dir=review_dir,
        eval_file=eval_file,
        manifest_path=manifest_path,
    )
    contract = _read_json(resolved_eval_file)
    _validate_contract(contract)
    resolved_review_dir = _resolve_review_dir(
        output_dir=Path(output_dir),
        review_id=review_id or str(contract.get("review_id") or ""),
        review_dir=review_dir,
    )
    resolved_output_path = Path(output_path) if output_path else (
        resolved_review_dir / "forest_plan_component_eval_results.json"
    )
    artifacts = _load_review_artifacts(resolved_review_dir)
    case_results = _evaluate_cases(
        cases=contract["cases"],
        artifacts=artifacts,
    )
    metrics = _metrics(case_results)
    checks = _checks(
        contract=contract,
        artifacts=artifacts,
        case_results=case_results,
        metrics=metrics,
    )
    summary = {
        "schema_version": FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "eval_id": contract.get("eval_id"),
        "review_id": _review_id(artifacts) or contract.get("review_id"),
        "source_set_id": _source_set_id(artifacts) or contract.get("source_set_id"),
        "eval_file": str(resolved_eval_file),
        "review_dir": str(resolved_review_dir),
        "output_path": str(resolved_output_path),
        "case_count": len(case_results),
        "passed_case_count": sum(1 for result in case_results if result["passed"]),
        "failed_case_count": sum(1 for result in case_results if not result["passed"]),
        "metrics": metrics,
        "failure_category_counts": _failure_category_counts(case_results),
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
    payload = {
        "schema_version": FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "eval_id": summary["eval_id"],
        "review_id": summary["review_id"],
        "source_set_id": summary["source_set_id"],
        "passed": summary["passed"],
        "summary": summary,
        "case_results": case_results,
        "artifact_paths": artifacts["artifact_paths"],
        "contract": {
            "schema_version": contract.get("schema_version"),
            "eval_id": contract.get("eval_id"),
            "review_id": contract.get("review_id"),
            "source_set_id": contract.get("source_set_id"),
            "case_count": len(contract["cases"]),
            "metric_thresholds": contract.get("metric_thresholds", {}),
            "coverage_requirements": contract.get("coverage_requirements", {}),
        },
    }
    _write_json(resolved_output_path, payload)
    return ForestPlanComponentEvalResult(
        eval_file=resolved_eval_file,
        review_dir=resolved_review_dir,
        output_path=resolved_output_path,
        summary=summary,
    )


def _resolve_eval_file(
    *,
    review_id: str | None,
    review_dir: Path | None,
    eval_file: Path | None,
    manifest_path: Path,
) -> Path:
    if eval_file is not None:
        return Path(eval_file)
    if review_id:
        return resolve_forest_plan_component_eval_file(
            review_id=review_id,
            manifest_path=manifest_path,
        )
    raise ValueError(
        "forest-plan-component-eval requires --eval-file or a tracked --review-id in the "
        "forest-plan component coverage manifest"
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
        raise ValueError("review_id is required when review_dir is not supplied.")
    if not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ValueError(f"unsafe review_id: {review_id!r}")
    return output_dir / "reviews" / review_id


def _load_review_artifacts(review_dir: Path) -> dict[str, Any]:
    specs = {
        "component_findings": ("forest_plan_component_findings.json", True, "json"),
        "standard_coverage": ("forest_plan_applicable_standard_coverage.json", True, "json"),
        "reviewer_resolution_queue": ("forest_plan_reviewer_resolution_queue.json", True, "json"),
    }
    artifacts: dict[str, Any] = {
        "artifact_errors": [],
        "artifact_paths": {},
    }
    for name, (relative_path, required, kind) in specs.items():
        path = review_dir / relative_path
        artifacts["artifact_paths"][name] = str(path)
        if not path.exists():
            artifacts[name] = [] if kind == "jsonl" else {}
            if required:
                artifacts["artifact_errors"].append(
                    {
                        "artifact": name,
                        "path": str(path),
                        "failure_category": "review_artifact_missing",
                    }
                )
            continue
        try:
            artifacts[name] = _read_json(path)
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            artifacts[name] = {}
            artifacts["artifact_errors"].append(
                {
                    "artifact": name,
                    "path": str(path),
                    "failure_category": "review_artifact_unreadable",
                    "message": str(exc),
                }
            )
    return artifacts


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
        actual_applicable_standards = set(_applicable_standard_component_ids(artifacts))
        expected_applicable_standard_cases = {
            result["component_id"]
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


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 6)


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
