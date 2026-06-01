from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from .eval_context_graph import CONTEXT_GRAPH_EVAL_SUMMARY_SCHEMA_VERSION
from .eval_context_graph import CONTEXT_GRAPH_SCHEMA_VERSION
from .phase_eval_direct_eval_support import _first_numeric
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _resolve_repo_path
from .phase_eval_direct_eval_support import _string_list


REPO_ROOT = Path(__file__).resolve().parents[2]


def eval_context_graph_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    results_path_value: object,
    expected_contract_id: str,
    contract_path_value: object,
) -> dict[str, Any]:
    results_path = _context_graph_results_path(
        output_dir=output_dir,
        results_path_value=results_path_value,
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
        "producer": "eval_context_graph_evaluation",
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
        "graph_schema_version",
        "contract_id",
        "contract_version",
        "contract",
        "graph_json_path",
        "passed",
        "command_succeeded",
        "node_counts",
        "edge_counts",
        "event_source_count",
        "event_node_count",
        "node_count",
        "edge_count",
        "source_set_ids",
        "validation_checks",
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
    source_set_ids = _string_list(result.get("source_set_ids"))
    failed_check_names = _failed_graph_check_names(result)
    base["case_count"] = len(_graph_checks(result))
    base["hard_negative_case_count"] = 0
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "graph_schema_version": result.get("graph_schema_version"),
            "actual_contract_id": result.get("contract_id"),
            "actual_contract_sha256": actual_contract_sha,
            "graph_json_path": result.get("graph_json_path"),
            "source_set_ids": source_set_ids,
            "review_ids": _string_list(result.get("review_ids")),
            "node_count": _first_numeric(result.get("node_count")),
            "edge_count": _first_numeric(result.get("edge_count")),
            "event_source_count": _first_numeric(result.get("event_source_count")),
            "event_node_count": _first_numeric(result.get("event_node_count")),
            "failed_graph_check_names": failed_check_names,
        }
    )
    if (
        result.get("schema_version") != CONTEXT_GRAPH_EVAL_SUMMARY_SCHEMA_VERSION
        or result.get("graph_schema_version") != CONTEXT_GRAPH_SCHEMA_VERSION
    ):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base

    if (
        (expected_contract_id and str(result.get("contract_id") or "") != expected_contract_id)
        or source_set_id not in source_set_ids
        or (
            expected_contract_sha is not None
            and actual_contract_sha != expected_contract_sha
        )
    ):
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base

    threshold_failures = _context_graph_threshold_failures(result)
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


def _context_graph_results_path(
    *,
    output_dir: Path,
    results_path_value: object,
) -> Path:
    if str(results_path_value or "").strip():
        return output_dir / str(results_path_value)
    return (
        output_dir
        / "evaluations"
        / "eval_context_graph"
        / "eval_context_graph_eval_summary.json"
    )


def _context_graph_threshold_failures(result: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    failed_check_names = _failed_graph_check_names(result)
    if failed_check_names:
        failures.append(
            {
                "metric": "graph_eval_checks",
                "reason": "graph_eval_checks_failed",
                "failed_checks": failed_check_names,
            }
        )
    if not bool(result.get("command_succeeded")):
        failures.append(
            {
                "metric": "command_succeeded",
                "reason": "producer_command_failed",
                "actual": result.get("command_succeeded"),
            }
        )
    event_node_count = _first_numeric(result.get("event_node_count")) or 0
    if event_node_count <= 0:
        failures.append(
            {
                "metric": "event_node_count",
                "reason": "event_nodes_missing",
                "actual": event_node_count,
                "expected_minimum": 1,
            }
        )
    return failures


def _failed_graph_check_names(result: dict[str, Any]) -> list[str]:
    return [
        str(check.get("name") or "")
        for check in _graph_checks(result)
        if not bool(check.get("passed"))
    ]


def _graph_checks(result: dict[str, Any]) -> list[dict[str, Any]]:
    checks = result.get("validation_checks")
    return [check for check in checks if isinstance(check, dict)] if isinstance(checks, list) else []
