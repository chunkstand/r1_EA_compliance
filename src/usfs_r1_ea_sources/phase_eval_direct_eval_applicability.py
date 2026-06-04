from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from .applicability_eval_support import APPLICABILITY_EVAL_CONTRACT_ID
from .applicability_eval_support import APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION
from .applicability_eval_support import APPLICABILITY_EVAL_SCORER_VERSION
from .applicability_eval_support import DEFAULT_APPLICABILITY_EVAL_PATH
from .phase_eval_direct_eval_support import _first_numeric
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _resolve_repo_path
from .phase_eval_direct_eval_support import _string_list


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APPLICABILITY_RULE_PACK_PATH = Path("config/compliance_rule_pack_nepa_ea_v0.json")
DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH = Path(
    "config/authority_family_rule_templates_nepa_ea_v1.json"
)
REQUIRED_BLOCKING_METRIC_GROUP_IDS = {
    "adjudication_failure_intake",
    "authority_universe_coverage",
    "decision_partition_fidelity",
    "forest_plan_subgate_behavior",
    "gate_graph_consistency",
    "generated_rule_pack_fidelity",
    "graph_trace_quality",
    "retrieval_trace_quality",
    "trajectory_process_quality",
}


def applicability_direct_eval_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    results_path_value: object,
    expected_contract_id: str,
    expected_scorer_version: str,
    expected_non_blocking_gap_group_ids: list[str],
) -> dict[str, Any]:
    results_path = _results_path(output_dir=output_dir, results_path_value=results_path_value)
    result = _read_json_if_exists(results_path)
    base = {
        "phase_name": phase_name,
        "producer": "applicability_direct_evaluation",
        "coverage_class": coverage_class,
        "summary_present": isinstance(result, dict),
        "summary_path": str(results_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": [],
        "contract_id": expected_contract_id or APPLICABILITY_EVAL_CONTRACT_ID,
        "details": {
            "lane_id": lane_id,
            "expected_contract_id": expected_contract_id or APPLICABILITY_EVAL_CONTRACT_ID,
            "expected_scorer_version": (
                expected_scorer_version or APPLICABILITY_EVAL_SCORER_VERSION
            ),
            "expected_source_set_id": source_set_id,
            "expected_non_blocking_gap_group_ids": expected_non_blocking_gap_group_ids,
            "results_path": str(results_path),
        },
    }
    if not isinstance(result, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base

    required_keys = (
        "schema_version",
        "contract_id",
        "scorer_version",
        "source_set_ids",
        "passed",
        "case_count",
        "metric_groups",
        "required_metric_group_ids",
        "blocking_metric_groups_passed",
        "blocking_metric_group_failures",
        "non_blocking_gap_group_ids",
        "source_artifact_hashes",
        "failure_intake_summary",
        "failure_intake_cases_path",
        "failure_intake_cases_sha256",
    )
    missing_keys = [key for key in required_keys if key not in result]
    if missing_keys:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["missing_keys"] = missing_keys
        return base

    source_set_ids = _string_list(result.get("source_set_ids"))
    metric_groups = result.get("metric_groups") if isinstance(result.get("metric_groups"), dict) else {}
    failure_intake_summary = (
        result.get("failure_intake_summary")
        if isinstance(result.get("failure_intake_summary"), dict)
        else {}
    )
    hard_negative_results = [
        item for item in result.get("hard_negative_results") or [] if isinstance(item, dict)
    ]
    base["case_count"] = _first_numeric(result.get("case_count"))
    base["hard_negative_case_count"] = len(hard_negative_results)
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_contract_id": result.get("contract_id"),
            "actual_scorer_version": result.get("scorer_version"),
            "actual_source_set_ids": source_set_ids,
            "source_set_id": result.get("source_set_id"),
            "case_count": result.get("case_count"),
            "passed_count": result.get("passed_count"),
            "failed_count": result.get("failed_count"),
            "required_metric_group_ids": result.get("required_metric_group_ids"),
            "blocking_metric_group_failures": result.get(
                "blocking_metric_group_failures",
                [],
            ),
            "non_blocking_gap_group_ids": result.get("non_blocking_gap_group_ids", []),
            "failure_intake_summary": failure_intake_summary,
            "hard_negative_case_count": len(hard_negative_results),
            "source_artifact_hash_failures": _source_artifact_hash_failures(result),
        }
    )

    if result.get("schema_version") != APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base

    if (
        str(result.get("contract_id") or "") != base["details"]["expected_contract_id"]
        or str(result.get("scorer_version") or "") != base["details"]["expected_scorer_version"]
        or source_set_ids != [source_set_id]
    ):
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base

    hash_failures = _source_artifact_hash_failures(result)
    if hash_failures:
        base["details"]["source_artifact_hash_failures"] = hash_failures
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base

    threshold_failures = _threshold_failures(
        result,
        metric_groups=metric_groups,
        failure_intake_summary=failure_intake_summary,
        expected_non_blocking_gap_group_ids=expected_non_blocking_gap_group_ids,
    )
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


def _results_path(*, output_dir: Path, results_path_value: object) -> Path:
    if str(results_path_value or "").strip():
        return output_dir / str(results_path_value)
    return output_dir / "reviews" / "applicability_eval" / "applicability_eval_results.json"


def _threshold_failures(
    result: dict[str, Any],
    *,
    metric_groups: dict[str, Any],
    failure_intake_summary: dict[str, Any],
    expected_non_blocking_gap_group_ids: list[str],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    missing_groups = sorted(REQUIRED_BLOCKING_METRIC_GROUP_IDS - set(metric_groups))
    if missing_groups:
        failures.append(
            {
                "metric": "blocking_metric_groups",
                "reason": "required_metric_groups_missing",
                "missing_group_ids": missing_groups,
            }
        )
    failed_blocking_groups = [
        group_id
        for group_id in sorted(REQUIRED_BLOCKING_METRIC_GROUP_IDS)
        if isinstance(metric_groups.get(group_id), dict)
        and not bool(metric_groups[group_id].get("passed"))
    ]
    if failed_blocking_groups:
        failures.append(
            {
                "metric": "blocking_metric_groups",
                "reason": "blocking_metric_groups_failed",
                "failed_group_ids": failed_blocking_groups,
            }
        )
    if not bool(result.get("blocking_metric_groups_passed")):
        failures.append(
            {
                "metric": "blocking_metric_groups_passed",
                "reason": "blocking_metric_groups_not_passed",
                "actual": result.get("blocking_metric_groups_passed"),
            }
        )
    if _string_list(result.get("blocking_metric_group_failures")):
        failures.append(
            {
                "metric": "blocking_metric_group_failures",
                "reason": "blocking_failures_present",
                "actual": _string_list(result.get("blocking_metric_group_failures")),
            }
        )
    actual_gap_ids = _string_list(result.get("non_blocking_gap_group_ids"))
    if actual_gap_ids != expected_non_blocking_gap_group_ids:
        failures.append(
            {
                "metric": "non_blocking_gap_group_ids",
                "reason": "unexpected_non_blocking_gap_groups",
                "expected": expected_non_blocking_gap_group_ids,
                "actual": actual_gap_ids,
            }
        )
    if not bool(failure_intake_summary.get("validation_passed")):
        failures.append(
            {
                "metric": "failure_intake_summary.validation_passed",
                "reason": "failure_intake_not_replayable",
                "actual": failure_intake_summary.get("validation_passed"),
            }
        )
    if (_first_numeric(failure_intake_summary.get("replayable_case_count")) or 0) <= 0:
        failures.append(
            {
                "metric": "failure_intake_summary.replayable_case_count",
                "reason": "failure_intake_cases_missing",
                "actual": failure_intake_summary.get("replayable_case_count"),
                "expected_minimum": 1,
            }
        )
    if not _failure_intake_hash_matches(result):
        failures.append(
            {
                "metric": "failure_intake_cases_sha256",
                "reason": "failure_intake_hash_mismatch",
            }
        )
    return failures


def _source_artifact_hash_failures(result: dict[str, Any]) -> list[dict[str, str]]:
    hashes = result.get("source_artifact_hashes")
    if not isinstance(hashes, dict):
        return [{"artifact": "source_artifact_hashes", "reason": "missing"}]
    expected_paths = {
        "eval_file": DEFAULT_APPLICABILITY_EVAL_PATH,
        "base_rule_pack_path": DEFAULT_APPLICABILITY_RULE_PACK_PATH,
        "authority_family_templates_path": DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
    }
    failures = []
    for key, path in expected_paths.items():
        expected_hash = _sha256_file(REPO_ROOT / path)
        actual_hash = str(hashes.get(key) or "")
        if actual_hash != expected_hash:
            failures.append(
                {
                    "artifact": key,
                    "reason": "hash_mismatch",
                    "expected_sha256": expected_hash,
                    "actual_sha256": actual_hash,
                }
            )
    return failures


def _failure_intake_hash_matches(result: dict[str, Any]) -> bool:
    intake_path = Path(str(result.get("failure_intake_cases_path") or ""))
    if not intake_path.is_absolute():
        intake_path = _resolve_repo_path(REPO_ROOT, intake_path)
    intake = _read_json_if_exists(intake_path)
    if not isinstance(intake, dict):
        return False
    return (
        str(intake.get("failure_intake_cases_sha256") or "")
        == str(result.get("failure_intake_cases_sha256") or "")
        == str((intake.get("summary") or {}).get("failure_intake_cases_sha256") or "")
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
