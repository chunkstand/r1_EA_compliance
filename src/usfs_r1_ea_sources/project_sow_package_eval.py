from __future__ import annotations

from pathlib import Path
from typing import Any

from .project_sow_package_assembly import _project_sow_resource_scope_records
from .project_sow_package_assembly import run_project_sow_package
from .project_sow_package_common import _check
from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _read_json
from .project_sow_package_common import _slug
from .project_sow_package_common import _strings
from .project_sow_package_common import _write_json
from .project_sow_package_graph import _has_canonical_resource_path
from .project_sow_package_models import CONTRACT_REQUIRED_SCOPE_FIELDS
from .project_sow_package_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR
from .project_sow_package_models import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package_models import ProjectSowEvalResult

def run_project_sow_eval(
    *,
    eval_config_path: Path = DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH,
    output_dir: Path = DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
) -> ProjectSowEvalResult:
    eval_config_path = Path(eval_config_path)
    output_dir = Path(output_dir)
    resource_scope_config_path = Path(resource_scope_config_path)
    authority_inventory_path = Path(authority_inventory_path)
    eval_config = _read_json(eval_config_path)
    cases = [case for case in _list(eval_config.get("eval_cases")) if isinstance(case, dict)]
    case_summaries = [
        _project_sow_eval_case_summary(
            case=case,
            output_dir=output_dir,
            resource_scope_config_path=resource_scope_config_path,
            authority_inventory_path=authority_inventory_path,
        )
        for case in cases
    ]
    top_level_checks = [
        _check(
            name="project_sow_eval_has_three_proving_intakes",
            passed=len(case_summaries) >= 3,
            details={"case_count": len(case_summaries)},
        )
    ]
    category_totals = {
        key: sum(len(_strings(case["diagnostics"].get(key))) for case in case_summaries)
        for key in [
            "system_miss_resource_area_ids",
            "intake_omission_resource_area_ids",
            "calibration_gap_resource_area_ids",
            "expected_no_observed_report_resource_area_ids",
        ]
    }
    failed_cases = [
        str(case_summary["case_id"])
        for case_summary in case_summaries
        if not case_summary["passed"]
    ]
    summary_path = output_dir / "project_sow_eval_summary.json"
    summary = {
        "authority_inventory_path": str(authority_inventory_path),
        "case_count": len(case_summaries),
        "cases": case_summaries,
        "category_totals": category_totals,
        "eval_config_path": str(eval_config_path),
        "failed_cases": failed_cases,
        "output_dir": str(output_dir),
        "passed": not failed_cases and all(check["passed"] for check in top_level_checks),
        "resource_scope_config_path": str(resource_scope_config_path),
        "schema_version": "project-sow-eval-summary-v0",
        "summary_path": str(summary_path),
        "validation_checks": top_level_checks,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(summary_path, summary)
    return ProjectSowEvalResult(
        output_dir=output_dir,
        summary_path=summary_path,
        summary=summary,
    )

def _project_sow_eval_case_summary(
    *,
    case: dict[str, Any],
    output_dir: Path,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
) -> dict[str, Any]:
    intake_path = Path(str(case.get("intake_path") or ""))
    case_id = _slug(str(case.get("case_id") or intake_path.stem or "project-sow-eval-case"))
    package_result = run_project_sow_package(
        intake_path=intake_path,
        output_dir=output_dir,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
        results_dir=output_dir / "cases" / case_id,
    )
    package = (
        _read_json(package_result.package_path)
        if package_result.summary.get("output_written") and package_result.package_path.is_file()
        else {}
    )
    diagnostics = _project_sow_eval_resource_diagnostics(package=package, case=case)
    actual_metrics = _project_sow_eval_actual_metrics(
        package=package,
        package_summary=package_result.summary,
        diagnostics=diagnostics,
    )
    metric_checks = _project_sow_eval_checks(
        actual=actual_metrics,
        expected=case.get("expected_metrics"),
        prefix="expected_metrics",
    )
    diagnostic_checks = _project_sow_eval_checks(
        actual=diagnostics,
        expected=case.get("expected_diagnostics"),
        prefix="expected_diagnostics",
    )
    checks = metric_checks + diagnostic_checks
    return {
        "actual_metrics": actual_metrics,
        "case_id": case_id,
        "description": case.get("description"),
        "diagnostics": diagnostics,
        "expected_diagnostics": case.get("expected_diagnostics") or {},
        "expected_metrics": case.get("expected_metrics") or {},
        "intake_path": str(intake_path),
        "output_paths": package_result.summary.get("output_paths") or {},
        "package_passed": package_result.summary.get("passed"),
        "passed": bool(package_result.summary.get("passed"))
        and all(check["passed"] for check in checks),
        "validation_checks": checks,
    }


def _project_sow_eval_actual_metrics(
    *,
    package: dict[str, Any],
    package_summary: dict[str, Any],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_fields_passed": _project_sow_validation_check_passed(
            package, "selected_resource_scopes_have_contract_fields"
        ),
        "contract_ready_resource_scope_count": _project_sow_contract_ready_scope_count(
            package
        ),
        "intake_evidence_graph_edge_count": package_summary.get(
            "intake_evidence_graph_edge_count"
        ),
        "intake_evidence_graph_node_count": package_summary.get(
            "intake_evidence_graph_node_count"
        ),
        "output_written": bool(package_summary.get("output_written")),
        "package_passed": bool(package_summary.get("passed")),
        "pdf_header_valid": bool(package_summary.get("pdf_header_valid")),
        "proposed_action_resource_area_count": package_summary.get(
            "proposed_action_resource_area_count"
        ),
        "optional_deliverable_resource_scope_count": _project_sow_scope_count_with_field(
            package, "optional_deliverables"
        ),
        "rendering_checks_passed": _project_sow_rendering_checks_passed(package),
        "required_deliverable_resource_scope_count": _project_sow_scope_count_with_field(
            package, "required_deliverables"
        ),
        "resource_scope_count": package_summary.get("resource_scope_count"),
        "validation_failure_count": package_summary.get("validation_failure_count"),
        "calibration_gap_count": len(
            _strings(diagnostics.get("calibration_gap_resource_area_ids"))
        ),
        "expected_no_observed_report_count": len(
            _strings(diagnostics.get("expected_no_observed_report_resource_area_ids"))
        ),
        "intake_omission_count": len(
            _strings(diagnostics.get("intake_omission_resource_area_ids"))
        ),
        "system_miss_count": len(_strings(diagnostics.get("system_miss_resource_area_ids"))),
    }

def _project_sow_contract_ready_scope_count(package: dict[str, Any]) -> int:
    return sum(
        1
        for scope in _project_sow_resource_scope_records(package)
        if not any(_is_empty(scope.get(field)) for field in CONTRACT_REQUIRED_SCOPE_FIELDS)
    )


def _project_sow_scope_count_with_field(package: dict[str, Any], field: str) -> int:
    return sum(
        1
        for scope in _project_sow_resource_scope_records(package)
        if not _is_empty(scope.get(field))
    )


def _project_sow_eval_resource_diagnostics(
    *,
    package: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    rows = [row for row in _list(package.get("resource_analysis_matrix")) if isinstance(row, dict)]
    graph = package.get("intake_evidence_graph") if isinstance(package.get("intake_evidence_graph"), dict) else {}
    expected_resource_area_ids = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("expected_from_proposed_action") and row.get("resource_area_id")
    )
    canonical_path_misses = sorted(
        area_id
        for area_id in expected_resource_area_ids
        if not _has_canonical_resource_path(graph, area_id)
    )
    missing_sow_scope = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("coverage_status") == "missing_sow_scope" and row.get("resource_area_id")
    )
    intake_omissions = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("coverage_status") == "observed_not_derived_from_proposed_action"
        and row.get("resource_area_id")
    )
    expected_without_observed_reports = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("expected_from_proposed_action")
        and row.get("resource_area_id")
        and not _list(row.get("actual_specialist_reports"))
    )
    observed_reports_available = case.get("observed_reports_available") is True
    return {
        "calibration_gap_resource_area_ids": (
            expected_without_observed_reports if observed_reports_available else []
        ),
        "expected_no_observed_report_resource_area_ids": (
            [] if observed_reports_available else expected_without_observed_reports
        ),
        "expected_resource_area_ids": expected_resource_area_ids,
        "intake_omission_resource_area_ids": intake_omissions,
        "system_miss_resource_area_ids": sorted(
            set(canonical_path_misses) | set(missing_sow_scope)
        ),
    }


def _project_sow_eval_checks(
    *,
    actual: dict[str, Any],
    expected: Any,
    prefix: str,
) -> list[dict[str, Any]]:
    if not isinstance(expected, dict):
        return []
    return [
        _check(
            name=f"{prefix}.{key}",
            passed=actual.get(key) == expected_value,
            details={"actual": actual.get(key), "expected": expected_value},
        )
        for key, expected_value in sorted(expected.items())
    ]


def _project_sow_rendering_checks_passed(package: dict[str, Any]) -> bool:
    return all(
        _project_sow_validation_check_passed(package, name)
        for name in {
            "project_sow_markdown_required_sections_present",
            "project_sow_pdf_required_items_present",
        }
    )


def _project_sow_validation_check_passed(package: dict[str, Any], check_name: str) -> bool:
    validation = package.get("validation") if isinstance(package.get("validation"), dict) else {}
    checks = {
        str(check.get("name")): check
        for check in _list(validation.get("checks"))
        if isinstance(check, dict)
    }
    return checks.get(check_name, {}).get("passed") is True
