from __future__ import annotations

from pathlib import Path
from typing import Any

from .phase_eval_direct_eval_support import FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import _failed_contract_check_names
from .phase_eval_direct_eval_support import _first_numeric
from .phase_eval_direct_eval_support import _metric_value
from .phase_eval_direct_eval_support import _profile_metric_sum
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _string_list


def _forest_plan_profile_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    results_path_value: object,
    expected_contract_id: str,
) -> dict[str, Any]:
    if not str(results_path_value or "").strip():
        return {
            "phase_name": phase_name,
            "producer": "forest_plan_profile_evaluation",
            "coverage_class": coverage_class,
            "status": "direct_eval_schema_invalid",
            "summary_present": False,
            "summary_path": None,
            "direct_eval_present": False,
            "direct_eval_passed": False,
            "case_count": None,
            "hard_negative_case_count": None,
            "threshold_failures": [],
            "failure_reasons": ["direct_eval_schema_invalid"],
            "contract_id": expected_contract_id or lane_id,
            "details": {"lane_id": lane_id},
        }

    results_path = output_dir / str(results_path_value)
    result = _read_json_if_exists(results_path)
    base = {
        "phase_name": phase_name,
        "producer": "forest_plan_profile_evaluation",
        "coverage_class": coverage_class,
        "summary_present": isinstance(result, dict),
        "summary_path": str(results_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": [],
        "contract_id": expected_contract_id or lane_id,
        "details": {
            "lane_id": lane_id,
            "expected_contract_id": expected_contract_id or lane_id,
        },
    }
    if not isinstance(result, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base
    required_keys = (
        "schema_version",
        "contract_id",
        "passed",
        "active_source_set_ids",
        "covered_profile_count",
        "fixture_contract_defined_profile_count",
        "not_started_profile_count",
        "profile_failure_count",
        "profiles_below_floor_ids",
    )
    if any(key not in result for key in required_keys):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["missing_keys"] = [
            key for key in required_keys if key not in result
        ]
        return base

    active_source_set_ids = _string_list(result.get("active_source_set_ids"))
    expected_active_source_set_ids = [source_set_id]
    base["case_count"] = _first_numeric(
        result.get("required_profile_count"),
        result.get("configured_profile_count"),
        result.get("covered_profile_count"),
    )
    base["hard_negative_case_count"] = _profile_metric_sum(
        result.get("profiles"),
        "hard_negative_case_count",
    )
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_contract_id": result.get("contract_id"),
            "actual_contract_version": result.get("contract_version"),
            "active_source_set_ids": active_source_set_ids,
            "expected_active_source_set_ids": expected_active_source_set_ids,
            "covered_profile_count": result.get("covered_profile_count"),
            "fixture_contract_defined_profile_count": result.get(
                "fixture_contract_defined_profile_count"
            ),
            "not_started_profile_count": result.get("not_started_profile_count"),
            "validated_not_started_profile_count": result.get(
                "validated_not_started_profile_count"
            ),
            "profile_failure_count": result.get("profile_failure_count"),
            "profiles_below_floor_ids": result.get("profiles_below_floor_ids", []),
            "failure_category_counts": result.get("failure_category_counts", {}),
            "threshold_failures": result.get("threshold_failures", []),
            "failed_contract_checks": _failed_contract_check_names(result),
        }
    )
    if result.get("schema_version") != FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    if expected_contract_id and str(result.get("contract_id") or "") != expected_contract_id:
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base
    if active_source_set_ids != expected_active_source_set_ids:
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base

    threshold_failures = _forest_plan_profile_threshold_failures(result)
    if not bool(result.get("passed")) or threshold_failures:
        base["status"] = "direct_eval_failed"
        base["direct_eval_present"] = True
        base["failure_reasons"] = ["direct_eval_threshold_failed"]
        base["threshold_failures"] = threshold_failures or [
            {
                "metric": "producer_passed",
                "reason": "producer_failed",
                "actual": result.get("passed"),
            }
        ]
        return base

    base["status"] = "direct_eval_present"
    base["direct_eval_present"] = True
    base["direct_eval_passed"] = True
    return base


def _forest_plan_component_retrieval_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    results_path_value: object,
    expected_contract_id: str,
    required_source_set_ids: list[str],
) -> dict[str, Any]:
    if not str(results_path_value or "").strip():
        return {
            "phase_name": phase_name,
            "producer": "forest_plan_component_retrieval_evaluation",
            "coverage_class": coverage_class,
            "status": "direct_eval_schema_invalid",
            "summary_present": False,
            "summary_path": None,
            "direct_eval_present": False,
            "direct_eval_passed": False,
            "case_count": None,
            "hard_negative_case_count": None,
            "threshold_failures": [],
            "failure_reasons": ["direct_eval_schema_invalid"],
            "contract_id": expected_contract_id or lane_id,
            "details": {"lane_id": lane_id},
        }

    results_path = output_dir / str(results_path_value)
    result = _read_json_if_exists(results_path)
    base = {
        "phase_name": phase_name,
        "producer": "forest_plan_component_retrieval_evaluation",
        "coverage_class": coverage_class,
        "summary_present": isinstance(result, dict),
        "summary_path": str(results_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": [],
        "contract_id": expected_contract_id or lane_id,
        "details": {
            "lane_id": lane_id,
            "expected_contract_id": expected_contract_id or lane_id,
            "expected_source_set_id": source_set_id,
            "required_source_set_ids": required_source_set_ids,
        },
    }
    if not isinstance(result, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base
    required_keys = (
        "schema_version",
        "contract_id",
        "passed",
        "source_set_id",
        "expected_active_source_set_ids",
        "case_count",
        "expected_pass_case_count",
        "hard_negative_case_count",
        "covered_forest_unit_ids",
        "required_forest_unit_ids",
        "metrics",
    )
    if any(key not in result for key in required_keys):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["missing_keys"] = [
            key for key in required_keys if key not in result
        ]
        return base
    expected_active_source_set_ids = required_source_set_ids or [source_set_id]
    actual_expected_active_source_set_ids = _string_list(
        result.get("expected_active_source_set_ids")
    )
    base["case_count"] = _first_numeric(result.get("case_count"))
    base["hard_negative_case_count"] = _first_numeric(
        result.get("hard_negative_case_count"),
        _metric_value(result, "hard_negative_case_count"),
    )
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_contract_id": result.get("contract_id"),
            "actual_source_set_id": result.get("source_set_id"),
            "expected_active_source_set_ids": expected_active_source_set_ids,
            "actual_expected_active_source_set_ids": actual_expected_active_source_set_ids,
            "expected_pass_case_count": result.get("expected_pass_case_count"),
            "required_forest_unit_ids": result.get("required_forest_unit_ids", []),
            "covered_forest_unit_ids": result.get("covered_forest_unit_ids", []),
            "failed_case_ids": result.get("failed_case_ids", []),
            "metrics": result.get("metrics", {}),
            "failure_category_counts": result.get("failure_category_counts", {}),
            "failed_contract_checks": _failed_contract_check_names(result),
        }
    )
    if (
        result.get("schema_version")
        != FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION
    ):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    if expected_contract_id and str(result.get("contract_id") or "") != expected_contract_id:
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base
    if (
        str(result.get("source_set_id") or "") != source_set_id
        or actual_expected_active_source_set_ids != expected_active_source_set_ids
    ):
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base
    threshold_failures = _forest_plan_component_retrieval_threshold_failures(result)
    if not bool(result.get("passed")) or threshold_failures:
        base["status"] = "direct_eval_failed"
        base["direct_eval_present"] = True
        base["failure_reasons"] = ["direct_eval_threshold_failed"]
        base["threshold_failures"] = threshold_failures or [
            {
                "metric": "producer_passed",
                "reason": "producer_failed",
                "actual": result.get("passed"),
            }
        ]
        return base
    base["status"] = "direct_eval_present"
    base["direct_eval_present"] = True
    base["direct_eval_passed"] = True
    return base


def _forest_plan_profile_threshold_failures(result: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    threshold_failures = result.get("threshold_failures")
    if isinstance(threshold_failures, list):
        failures.extend(
            failure for failure in threshold_failures if isinstance(failure, dict)
        )
    failed_contract_checks = _failed_contract_check_names(result)
    if failed_contract_checks:
        failures.append(
            {
                "metric": "contract_checks",
                "reason": "contract_checks_failed",
                "failed_checks": failed_contract_checks,
            }
        )
    profile_failure_count = _first_numeric(result.get("profile_failure_count"))
    if profile_failure_count and profile_failure_count > 0:
        failures.append(
            {
                "metric": "profile_failure_count",
                "reason": "profiles_below_floor",
                "actual": profile_failure_count,
                "expected_maximum": 0,
                "profiles_below_floor_ids": _string_list(
                    result.get("profiles_below_floor_ids")
                ),
            }
        )
    return failures


def _forest_plan_component_retrieval_threshold_failures(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    failed_contract_checks = _failed_contract_check_names(result)
    if failed_contract_checks:
        failures.append(
            {
                "metric": "contract_checks",
                "reason": "contract_checks_failed",
                "failed_checks": failed_contract_checks,
            }
        )
    failed_case_ids = _string_list(result.get("failed_case_ids"))
    if failed_case_ids:
        failures.append(
            {
                "metric": "failed_case_ids",
                "reason": "case_failures",
                "actual": len(failed_case_ids),
                "failed_case_ids": failed_case_ids,
            }
        )
    return failures
