from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from .phase_eval_direct_eval_support import KNOWLEDGE_GRAPH_QUERY_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import _failed_contract_check_names
from .phase_eval_direct_eval_support import _first_numeric
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _resolve_repo_path
from .phase_eval_direct_eval_support import _string_list


REPO_ROOT = Path(__file__).resolve().parents[2]


def knowledge_graph_query_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    results_path_value: object,
    results_filename: str,
    expected_contract_id: str,
    contract_path_value: object,
) -> dict[str, Any]:
    results_path = _source_set_scoped_results_path(
        output_dir=output_dir,
        source_set_id=source_set_id,
        results_path_value=results_path_value,
        results_filename=results_filename,
    )
    result = _read_json_if_exists(results_path)
    contract_path = (
        _resolve_repo_path(REPO_ROOT / "config", contract_path_value)
        if str(contract_path_value or "").strip()
        else None
    )
    expected_contract_sha = (
        hashlib.sha256(contract_path.read_bytes()).hexdigest()
        if contract_path is not None and contract_path.exists()
        else None
    )
    base = {
        "phase_name": phase_name,
        "producer": "knowledge_graph_query_evaluation",
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
            "contract_path": str(contract_path) if contract_path is not None else None,
            "expected_contract_sha256": expected_contract_sha,
        },
    }
    if not isinstance(result, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base

    required_keys = (
        "schema_version",
        "eval_id",
        "contract_id",
        "source_set_id",
        "passed",
        "case_count",
        "hard_negative_case_count",
        "query_type_count",
        "query_types",
        "freshness_warning_case_count",
        "contract",
    )
    if any(key not in result for key in required_keys):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["missing_keys"] = [
            key for key in required_keys if key not in result
        ]
        return base

    actual_contract_sha = (
        (result.get("contract") or {}).get("sha256")
        if isinstance(result.get("contract"), dict)
        else None
    )
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    base["case_count"] = _first_numeric(result.get("case_count"))
    base["hard_negative_case_count"] = _first_numeric(result.get("hard_negative_case_count"))
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_eval_id": result.get("eval_id"),
            "actual_contract_id": result.get("contract_id"),
            "actual_source_set_id": result.get("source_set_id"),
            "actual_contract_sha256": actual_contract_sha,
            "query_type_count": result.get("query_type_count"),
            "query_types": result.get("query_types", []),
            "freshness_warning_case_count": result.get("freshness_warning_case_count"),
            "failed_case_ids": summary.get("failed_case_ids", []),
            "failed_contract_checks": _failed_contract_check_names(result),
        }
    )
    if result.get("schema_version") != KNOWLEDGE_GRAPH_QUERY_EVAL_RESULTS_SCHEMA_VERSION:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    if (
        (expected_contract_id and str(result.get("contract_id") or "") != expected_contract_id)
        or str(result.get("eval_id") or "") != str(result.get("contract_id") or "")
        or str(result.get("source_set_id") or "") != source_set_id
        or (
            expected_contract_sha is not None
            and actual_contract_sha != expected_contract_sha
        )
    ):
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base

    threshold_failures = _knowledge_graph_query_threshold_failures(result)
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


def _source_set_scoped_results_path(
    *,
    output_dir: Path,
    source_set_id: str,
    results_path_value: object,
    results_filename: str,
) -> Path:
    if str(results_path_value or "").strip():
        return output_dir / str(results_path_value).format(source_set_id=source_set_id)
    return (
        output_dir
        / "derived"
        / source_set_id
        / "knowledge_graph"
        / (results_filename or "knowledge_graph_query_eval_results.json")
    )


def _knowledge_graph_query_threshold_failures(result: dict[str, Any]) -> list[dict[str, Any]]:
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
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    failed_case_ids = _string_list(summary.get("failed_case_ids"))
    if failed_case_ids:
        failures.append(
            {
                "metric": "knowledge_graph_query_eval_cases",
                "reason": "case_failures",
                "failed_case_ids": failed_case_ids,
            }
        )
    freshness_warning_case_count = _first_numeric(
        result.get("freshness_warning_case_count"),
        summary.get("freshness_warning_case_count"),
    )
    if freshness_warning_case_count and freshness_warning_case_count > 0:
        failures.append(
            {
                "metric": "freshness_warning_case_count",
                "reason": "freshness_warnings_present",
                "actual": freshness_warning_case_count,
                "expected_maximum": 0,
            }
        )
    return failures
