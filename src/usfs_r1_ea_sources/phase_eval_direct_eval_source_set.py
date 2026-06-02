from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from .phase_eval_direct_eval_forest_plan import _forest_plan_component_retrieval_phase_status
from .phase_eval_direct_eval_forest_plan import _forest_plan_profile_phase_status
from .phase_eval_direct_eval_support import DOWNSTREAM_DIRECT_EVAL_MANIFEST_SCHEMA_VERSION
from .phase_eval_direct_eval_support import EXTRACTION_FIDELITY_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import SEMANTIC_GRAPH_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import UPSTREAM_EVALUATION_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import _coverage_requirement_actual
from .phase_eval_direct_eval_support import _failed_contract_check_names
from .phase_eval_direct_eval_support import _first_numeric
from .phase_eval_direct_eval_support import _int_or_none
from .phase_eval_direct_eval_support import _metric_value
from .phase_eval_direct_eval_support import _read_json
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _resolve_repo_path
from .phase_eval_direct_eval_support import _string_list
from .phase_eval_direct_eval_graph_producers import graph_direct_eval_phase_status
from .rule_claim_binding import default_rule_claim_links_dir


REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_source_set_phase_statuses(
    *,
    contract: dict[str, Any],
    output_dir: Path,
    source_set_id: str,
    upstream_results_path: Path,
    upstream_results: dict[str, Any] | None,
    downstream_manifest_path: Path,
    downstream_manifest: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    phase_statuses: dict[str, dict[str, Any]] = {}
    for spec in contract.get("source_set_phases", []):
        if not _source_set_phase_applies(spec=spec, source_set_id=source_set_id):
            continue
        phase_statuses[str(spec["phase_name"])] = _source_set_phase_status(
            spec=spec,
            source_set_id=source_set_id,
            output_dir=output_dir,
            upstream_results_path=upstream_results_path,
            upstream_results=upstream_results,
            downstream_manifest_path=downstream_manifest_path,
            downstream_manifest=downstream_manifest,
        )
    return phase_statuses


def _source_set_phase_applies(
    *,
    spec: dict[str, Any],
    source_set_id: str,
) -> bool:
    required_source_set_ids = _string_list(spec.get("required_source_set_ids"))
    return not required_source_set_ids or source_set_id in required_source_set_ids


def _source_set_phase_status(
    *,
    spec: dict[str, Any],
    source_set_id: str,
    output_dir: Path,
    upstream_results_path: Path,
    upstream_results: dict[str, Any] | None,
    downstream_manifest_path: Path,
    downstream_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    phase_name = str(spec["phase_name"])
    coverage_class = str(spec["coverage_class"])
    if coverage_class == "validation_only_allowed":
        return {
            "phase_name": phase_name,
            "producer": str(spec.get("producer") or "phase_eval"),
            "coverage_class": coverage_class,
            "status": "validation_only_allowed",
            "summary_present": False,
            "summary_path": None,
            "direct_eval_present": False,
            "direct_eval_passed": False,
            "case_count": None,
            "hard_negative_case_count": None,
            "threshold_failures": [],
            "failure_reasons": [],
            "contract_id": None,
            "details": {},
        }
    producer = str(spec.get("producer") or "")
    if producer == "upstream_evaluation":
        return _upstream_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=str(spec["lane_id"]),
            upstream_results_path=upstream_results_path,
            upstream_results=upstream_results,
        )
    if producer == "downstream_direct_evaluation":
        return _downstream_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=str(spec["lane_id"]),
            source_set_id=source_set_id,
            output_dir=output_dir,
            downstream_manifest_path=downstream_manifest_path,
            downstream_manifest=downstream_manifest,
        )
    if producer == "extraction_fidelity_evaluation":
        return _extraction_fidelity_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=str(spec["lane_id"]),
            output_dir=output_dir,
            results_path_value=spec.get("results_path"),
        )
    if producer == "forest_plan_profile_evaluation":
        return _forest_plan_profile_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=str(spec["lane_id"]),
            source_set_id=source_set_id,
            output_dir=output_dir,
            results_path_value=spec.get("results_path"),
            expected_contract_id=str(spec.get("expected_contract_id") or ""),
        )
    if producer == "forest_plan_component_retrieval_evaluation":
        return _forest_plan_component_retrieval_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=str(spec["lane_id"]),
            source_set_id=source_set_id,
            output_dir=output_dir,
            results_path_value=spec.get("results_path"),
            expected_contract_id=str(spec.get("expected_contract_id") or ""),
            required_source_set_ids=_string_list(spec.get("required_source_set_ids")),
        )
    if producer == "semantic_graph_direct_evaluation":
        return _semantic_graph_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=str(spec["lane_id"]),
            source_set_id=source_set_id,
            output_dir=output_dir,
            results_path_value=spec.get("results_path"),
            results_filename=str(spec.get("results_filename") or ""),
            expected_contract_id=str(spec.get("expected_contract_id") or ""),
            contract_path_value=spec.get("contract_path"),
        )
    graph_status = graph_direct_eval_phase_status(
        producer=producer,
        phase_name=phase_name,
        coverage_class=coverage_class,
        lane_id=str(spec["lane_id"]),
        source_set_id=source_set_id,
        output_dir=output_dir,
        spec=spec,
    )
    if graph_status is not None:
        return graph_status
    raise ValueError(f"Unsupported phase-eval direct-eval producer: {producer}")


def _upstream_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    upstream_results_path: Path,
    upstream_results: dict[str, Any] | None,
) -> dict[str, Any]:
    base = {
        "phase_name": phase_name,
        "producer": "upstream_evaluation",
        "coverage_class": coverage_class,
        "summary_present": isinstance(upstream_results, dict),
        "summary_path": str(upstream_results_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": [],
        "contract_id": lane_id,
        "details": {"lane_id": lane_id},
    }
    if not isinstance(upstream_results, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base
    if upstream_results.get("schema_version") != UPSTREAM_EVALUATION_RESULTS_SCHEMA_VERSION:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["schema_version"] = upstream_results.get("schema_version")
        return base
    lane_summary = next(
        (
            summary
            for summary in upstream_results.get("lane_summaries", [])
            if isinstance(summary, dict) and str(summary.get("lane_id") or "") == lane_id
        ),
        None,
    )
    if lane_summary is None:
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base
    category_summaries = [
        summary
        for summary in upstream_results.get("category_summaries", [])
        if isinstance(summary, dict) and str(summary.get("lane_id") or "") == lane_id
    ]
    base["case_count"] = sum(
        _int_or_none(summary.get("case_count")) or 0 for summary in category_summaries
    )
    base["details"].update(
        {
            "lane_status": lane_summary.get("status"),
            "category_count": lane_summary.get("category_count"),
            "direct_eval_present_category_count": lane_summary.get(
                "direct_eval_present_category_count"
            ),
            "failed_case_ids": lane_summary.get("failing_case_ids", []),
            "category_summaries": category_summaries,
        }
    )
    if str(lane_summary.get("status") or "") != "direct_eval_present" or not bool(
        upstream_results.get("passed")
    ):
        base["status"] = "direct_eval_failed"
        base["direct_eval_present"] = True
        base["failure_reasons"] = ["direct_eval_threshold_failed"]
        base["threshold_failures"] = [
            {
                "metric": "upstream_lane_status",
                "reason": str(lane_summary.get("status") or "direct_eval_failed"),
                "failed_case_ids": lane_summary.get("failing_case_ids", []),
            }
        ]
        return base
    base["status"] = "direct_eval_present"
    base["direct_eval_present"] = True
    base["direct_eval_passed"] = True
    return base


def _extraction_fidelity_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    output_dir: Path,
    results_path_value: object,
) -> dict[str, Any]:
    result_path = _resolve_repo_path(output_dir, results_path_value)
    result = _read_json_if_exists(result_path)
    base = {
        "phase_name": phase_name,
        "producer": "extraction_fidelity_evaluation",
        "coverage_class": coverage_class,
        "summary_present": isinstance(result, dict),
        "summary_path": str(result_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": [],
        "contract_id": lane_id,
        "details": {
            "lane_id": lane_id,
            "results_path": str(result_path),
        },
    }
    if not isinstance(result, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base
    if (
        result.get("schema_version")
        != EXTRACTION_FIDELITY_EVAL_RESULTS_SCHEMA_VERSION
    ):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["schema_version"] = result.get("schema_version")
        return base
    base["case_count"] = _int_or_none(result.get("case_count"))
    base["details"].update(
        {
            "required_category_count": _int_or_none(result.get("required_category_count")),
            "matched_case_count": _int_or_none(result.get("matched_case_count")),
            "failed_case_ids": list(result.get("failed_case_ids") or []),
            "failed_contract_check_names": _failed_contract_check_names(result),
        }
    )
    if not bool(result.get("passed")):
        base["status"] = "direct_eval_failed"
        base["direct_eval_present"] = True
        base["failure_reasons"] = ["direct_eval_threshold_failed"]
        base["threshold_failures"] = [
            {
                "metric": "extraction_fidelity_eval",
                "failed_case_ids": list(result.get("failed_case_ids") or []),
                "failed_contract_check_names": _failed_contract_check_names(result),
            }
        ]
        return base
    base["status"] = "direct_eval_present"
    base["direct_eval_present"] = True
    base["direct_eval_passed"] = True
    return base


def _downstream_phase_status(
    *,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    downstream_manifest_path: Path,
    downstream_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    result_path = _downstream_result_path(
        output_dir=output_dir,
        source_set_id=source_set_id,
        lane_id=lane_id,
    )
    result = _read_json_if_exists(result_path)
    base = {
        "phase_name": phase_name,
        "producer": "downstream_direct_evaluation",
        "coverage_class": coverage_class,
        "summary_present": isinstance(result, dict),
        "summary_path": str(result_path),
        "direct_eval_present": False,
        "direct_eval_passed": False,
        "case_count": None,
        "hard_negative_case_count": None,
        "threshold_failures": [],
        "failure_reasons": [],
        "contract_id": None,
        "details": {
            "lane_id": lane_id,
            "manifest_path": str(downstream_manifest_path),
        },
    }
    if not isinstance(downstream_manifest, dict):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    if (
        downstream_manifest.get("schema_version")
        != DOWNSTREAM_DIRECT_EVAL_MANIFEST_SCHEMA_VERSION
    ):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        base["details"]["manifest_schema_version"] = downstream_manifest.get(
            "schema_version"
        )
        return base
    lane = next(
        (
            item
            for item in downstream_manifest.get("required_lanes", [])
            if isinstance(item, dict) and str(item.get("lane_id") or "") == lane_id
        ),
        None,
    )
    if lane is None:
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    contract_path = _resolve_repo_path(downstream_manifest_path.parent, lane["contract_path"])
    contract = _read_json(contract_path)
    expected_contract_sha = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    base["contract_id"] = str(lane.get("eval_id") or "")
    base["details"].update(
        {
            "contract_path": str(contract_path),
            "expected_contract_sha256": expected_contract_sha,
            "expected_eval_id": lane.get("eval_id"),
        }
    )
    if not isinstance(result, dict):
        base["status"] = "direct_eval_missing"
        base["failure_reasons"] = ["missing_required_direct_eval"]
        return base
    if any(key not in result for key in ("eval_id", "source_set_id", "passed", "contract")):
        base["status"] = "direct_eval_schema_invalid"
        base["failure_reasons"] = ["direct_eval_schema_invalid"]
        return base
    actual_contract_sha = ((result.get("contract") or {}).get("sha256")) if isinstance(
        result.get("contract"),
        dict,
    ) else None
    base["case_count"] = _coverage_requirement_actual(result, "case_count")
    base["hard_negative_case_count"] = _first_numeric(
        result.get("hard_negative_case_count"),
        result.get("hard_negative_package_case_count"),
        _metric_value(result, "hard_negative_case_count"),
        _metric_value(result, "hard_negative_package_case_count"),
    )
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_eval_id": result.get("eval_id"),
            "actual_source_set_id": result.get("source_set_id"),
            "actual_contract_sha256": actual_contract_sha,
            "checks": result.get("checks", []),
        }
    )
    if (
        str(result.get("eval_id") or "") != str(lane.get("eval_id") or "")
        or str(result.get("source_set_id") or "") != source_set_id
        or actual_contract_sha != expected_contract_sha
    ):
        base["status"] = "direct_eval_identity_mismatch"
        base["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return base
    threshold_failures = _downstream_threshold_failures(result=result, contract=contract)
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


def _semantic_graph_phase_status(
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
        "producer": "semantic_graph_direct_evaluation",
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
        "coverage_categories",
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
    base["case_count"] = _first_numeric(result.get("case_count"))
    base["hard_negative_case_count"] = _first_numeric(result.get("hard_negative_case_count"))
    base["details"].update(
        {
            "schema_version": result.get("schema_version"),
            "actual_eval_id": result.get("eval_id"),
            "actual_contract_id": result.get("contract_id"),
            "actual_source_set_id": result.get("source_set_id"),
            "actual_contract_sha256": actual_contract_sha,
            "coverage_categories": result.get("coverage_categories", []),
            "positive_case_count": result.get("positive_case_count"),
            "failed_positive_case_ids": (result.get("summary") or {}).get(
                "failed_positive_case_ids",
                [],
            ),
            "failed_negative_case_ids": (result.get("summary") or {}).get(
                "failed_negative_case_ids",
                [],
            ),
            "failed_contract_checks": _failed_contract_check_names(result),
        }
    )
    if result.get("schema_version") != SEMANTIC_GRAPH_EVAL_RESULTS_SCHEMA_VERSION:
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
    threshold_failures = _semantic_graph_threshold_failures(result)
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
        / (results_filename or "semantic_graph_eval_results.json")
    )


def _downstream_threshold_failures(
    *,
    result: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict]:
    failures: list[dict] = []
    coverage_requirements = contract.get("coverage_requirements", {})
    if isinstance(coverage_requirements, dict):
        for key, expected_min in coverage_requirements.items():
            actual = _coverage_requirement_actual(result, str(key))
            if actual is None:
                failures.append(
                    {
                        "metric": str(key),
                        "reason": "actual_missing",
                        "expected_min": expected_min,
                        "actual": None,
                    }
                )
            elif actual < int(expected_min):
                failures.append(
                    {
                        "metric": str(key),
                        "reason": "below_coverage_floor",
                        "expected_min": int(expected_min),
                        "actual": actual,
                    }
                )
    threshold_check = next(
        (
            check
            for check in result.get("checks", [])
            if isinstance(check, dict) and str(check.get("name") or "") == "metric_thresholds_met"
        ),
        None,
    )
    if isinstance(threshold_check, dict) and not bool(threshold_check.get("passed")):
        failures.extend((threshold_check.get("details") or {}).get("failures", []))
    case_check = next(
        (
            check
            for check in result.get("checks", [])
            if isinstance(check, dict) and str(check.get("name") or "") == "eval_cases_pass"
        ),
        None,
    )
    if isinstance(case_check, dict) and not bool(case_check.get("passed")):
        failures.append(
            {
                "metric": "eval_cases_pass",
                "reason": "case_failures",
                "details": case_check.get("details", {}),
            }
        )
    return failures


def _downstream_result_path(
    *,
    output_dir: Path,
    source_set_id: str,
    lane_id: str,
) -> Path:
    if lane_id == "retrieval_eval":
        return output_dir / "derived" / source_set_id / "retrieval" / "retrieval_eval_results.json"
    if lane_id == "claim_eval":
        return output_dir / "derived" / source_set_id / "claims" / "claim_eval_results.json"
    if lane_id == "rule_claim_eval":
        try:
            candidate = (
                default_rule_claim_links_dir(output_dir, source_set_id=source_set_id)
                / "rule_claim_link_eval_results.json"
            )
            if candidate.exists():
                return candidate
        except (FileNotFoundError, ValueError):
            pass
        rule_claim_root = output_dir / "derived" / source_set_id / "rule_claim_links"
        candidates = sorted(rule_claim_root.glob("*/*/rule_claim_link_eval_results.json"))
        if candidates:
            return candidates[0]
        candidates = sorted(rule_claim_root.glob("*/*/summary.json"))
        if candidates:
            return candidates[0].parent / "rule_claim_link_eval_results.json"
        return rule_claim_root / "rule_claim_link_eval_results.json"
    if lane_id == "compliance_review_eval":
        return (
            output_dir
            / "reviews"
            / "compliance_review_eval"
            / "compliance_review_eval_results.json"
        )
    raise ValueError(f"Unsupported downstream direct-eval lane_id: {lane_id}")


def _semantic_graph_threshold_failures(result: dict[str, Any]) -> list[dict[str, Any]]:
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
    failed_positive_case_ids = _string_list(
        (result.get("summary") or {}).get("failed_positive_case_ids")
    )
    failed_negative_case_ids = _string_list(
        (result.get("summary") or {}).get("failed_negative_case_ids")
    )
    if failed_positive_case_ids or failed_negative_case_ids:
        failures.append(
            {
                "metric": "semantic_graph_eval_cases",
                "reason": "case_failures",
                "failed_positive_case_ids": failed_positive_case_ids,
                "failed_negative_case_ids": failed_negative_case_ids,
            }
        )
    return failures
