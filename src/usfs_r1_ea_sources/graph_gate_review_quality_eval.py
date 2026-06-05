from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .artifact_utils import _dict, _dict_list, _read_json, _utc_now, _write_json
from .records import sha256_file


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_GATE_REVIEW_QUALITY_EVAL_SCHEMA_VERSION = "graph-gate-review-quality-eval-v1"
GRAPH_GATE_REVIEW_QUALITY_RESULTS_SCHEMA_VERSION = (
    "graph-gate-review-quality-results-v1"
)
DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH = (
    REPO_ROOT / "config" / "graph_gate_review_quality_eval_v1.json"
)
VALID_DIRECTIONS = {"higher_is_better", "lower_is_better"}


@dataclass(frozen=True)
class GraphGateReviewQualityEvalResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def run_graph_gate_review_quality_eval(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> GraphGateReviewQualityEvalResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    results_output_dir = (
        Path(results_dir)
        if results_dir
        else output_dir / "evaluations" / "graph_gate_review_quality"
    )
    output_path = results_output_dir / "graph_gate_review_quality_results.json"

    dimensions = _dimension_specs(manifest.get("quality_dimensions"))
    cases = _dict_list(manifest.get("cases"))
    contract_checks = _manifest_contract_checks(
        manifest=manifest,
        manifest_path=manifest_path,
        dimensions=dimensions,
        cases_value=manifest.get("cases"),
    )
    case_results = [
        _case_result(
            case=case,
            manifest_path=manifest_path,
            output_dir=output_dir,
            global_dimensions=dimensions,
        )
        for case in cases
    ]
    threshold_failures = _threshold_failures(
        thresholds=_dict(manifest.get("threshold_policy")),
        case_results=case_results,
    )
    failed_contract_checks = [
        check["name"] for check in contract_checks if not check["passed"]
    ]
    case_contract_failure_count = sum(
        1 for case_result in case_results if case_result["contract_failure"]
    )
    case_count = len(case_results)
    complete_case_count = sum(1 for case_result in case_results if case_result["complete"])
    review_ids = sorted(
        {
            str(case_result.get("review_id") or "").strip()
            for case_result in case_results
            if str(case_result.get("review_id") or "").strip()
        }
    )
    positive_delta_case_count = sum(
        1 for case_result in case_results if case_result["has_positive_delta"]
    )
    critical_regression_count = sum(
        int(case_result["critical_regression_count"]) for case_result in case_results
    )
    net_quality_delta = round(
        sum(float(case_result["net_quality_delta"]) for case_result in case_results), 6
    )
    experiment_blocked = (
        case_count == 0
        or bool(failed_contract_checks)
        or case_contract_failure_count > 0
    )
    hypothesis_supported = (
        not experiment_blocked
        and not threshold_failures
        and critical_regression_count == 0
        and positive_delta_case_count > 0
    )
    experiment_status = _experiment_status(
        experiment_blocked=experiment_blocked,
        hypothesis_supported=hypothesis_supported,
    )
    failure_category_counts = _failure_category_counts(
        contract_checks=contract_checks,
        case_results=case_results,
        threshold_failures=threshold_failures,
        experiment_blocked=experiment_blocked,
    )
    summary = {
        "schema_version": GRAPH_GATE_REVIEW_QUALITY_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(results_output_dir),
        "output_path": str(output_path),
        "contract_id": manifest.get("contract_id"),
        "version": manifest.get("version"),
        "intent": manifest.get("intent"),
        "stop_condition": _stop_condition(manifest),
        "hypothesis": _dict(manifest.get("hypothesis")),
        "command_succeeded": True,
        "experiment_status": experiment_status,
        "hypothesis_supported": hypothesis_supported,
        "case_count": case_count,
        "complete_case_count": complete_case_count,
        "distinct_review_count": len(review_ids),
        "review_ids": review_ids,
        "blocked_case_count": sum(
            1 for case_result in case_results if case_result["blocked"]
        ),
        "case_contract_failure_count": case_contract_failure_count,
        "positive_delta_case_count": positive_delta_case_count,
        "critical_regression_count": critical_regression_count,
        "net_quality_delta": net_quality_delta,
        "threshold_policy": _dict(manifest.get("threshold_policy")),
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "contract_checks": contract_checks,
        "quality_dimensions": list(dimensions.values()),
        "cases": case_results,
    }
    _write_json(output_path, summary)
    return GraphGateReviewQualityEvalResult(
        manifest_path=manifest_path,
        output_dir=results_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _manifest_contract_checks(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    dimensions: dict[str, dict[str, Any]],
    cases_value: Any,
) -> list[dict[str, Any]]:
    hypothesis = _dict(manifest.get("hypothesis"))
    threshold_policy = _dict(manifest.get("threshold_policy"))
    return [
        {
            "name": "manifest_schema_version",
            "passed": manifest.get("schema_version")
            == GRAPH_GATE_REVIEW_QUALITY_EVAL_SCHEMA_VERSION,
            "details": {
                "path": str(manifest_path),
                "expected": GRAPH_GATE_REVIEW_QUALITY_EVAL_SCHEMA_VERSION,
                "actual": manifest.get("schema_version"),
            },
        },
        {
            "name": "intent_declared",
            "passed": bool(str(manifest.get("intent") or "").strip()),
            "details": {"intent": manifest.get("intent")},
        },
        {
            "name": "stop_condition_declared",
            "passed": bool(_stop_condition(manifest)),
            "details": {
                "stop_condition": manifest.get("stop_condition"),
                "stop_conditions": manifest.get("stop_conditions"),
            },
        },
        {
            "name": "hypothesis_declared",
            "passed": bool(str(hypothesis.get("h1") or "").strip())
            and bool(str(hypothesis.get("h0") or "").strip()),
            "details": {"hypothesis": hypothesis},
        },
        {
            "name": "quality_dimensions_declared",
            "passed": bool(dimensions)
            and not _invalid_dimensions(manifest.get("quality_dimensions")),
            "details": {
                "metric_ids": sorted(dimensions),
                "invalid_dimensions": _invalid_dimensions(
                    manifest.get("quality_dimensions")
                ),
            },
        },
        {
            "name": "threshold_policy_declared",
            "passed": bool(threshold_policy),
            "details": {"threshold_policy": threshold_policy},
        },
        {
            "name": "case_list_declared",
            "passed": isinstance(cases_value, list),
            "details": {"case_count": len(cases_value) if isinstance(cases_value, list) else None},
        },
    ]


def _case_result(
    *,
    case: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
    global_dimensions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "").strip()
    dimensions = dict(global_dimensions)
    dimensions.update(_dimension_specs(case.get("quality_dimensions")))
    failure_reasons: list[str] = []
    if not case_id:
        failure_reasons.append("case_id_missing")
    if not dimensions:
        failure_reasons.append("quality_dimensions_missing")

    frozen_input_checks = _frozen_input_checks(
        frozen_inputs=case.get("frozen_inputs"),
        manifest_path=manifest_path,
    )
    for frozen_input_check in frozen_input_checks:
        if not frozen_input_check["passed"]:
            failure_reasons.append(str(frozen_input_check["reason"]))

    control = _observation(
        case.get("control"), manifest_path=manifest_path, output_dir=output_dir
    )
    treatment = _observation(
        case.get("treatment"), manifest_path=manifest_path, output_dir=output_dir
    )
    failure_reasons.extend(control["failure_reasons"])
    failure_reasons.extend(treatment["failure_reasons"])

    dimension_results = [
        _dimension_result(
            dimension=dimension,
            control_metrics=control["metrics"],
            treatment_metrics=treatment["metrics"],
        )
        for dimension in dimensions.values()
    ]
    for result in dimension_results:
        failure_reasons.extend(result["failure_reasons"])

    complete = not failure_reasons
    critical_regression_count = sum(
        1 for result in dimension_results if result["critical_regression"]
    )
    net_quality_delta = round(
        sum(
            float(result["quality_delta"])
            for result in dimension_results
            if result["quality_delta"] is not None
        ),
        6,
    )
    has_positive_delta = complete and any(
        float(result["quality_delta"] or 0) > 0 for result in dimension_results
    )
    return {
        "case_id": case_id,
        "review_id": case.get("review_id"),
        "source_set_id": case.get("source_set_id"),
        "case_role": case.get("case_role"),
        "complete": complete,
        "blocked": bool(failure_reasons),
        "contract_failure": bool(failure_reasons),
        "has_positive_delta": has_positive_delta,
        "critical_regression_count": critical_regression_count,
        "net_quality_delta": net_quality_delta,
        "failure_reasons": sorted(set(failure_reasons)),
        "frozen_input_checks": frozen_input_checks,
        "artifact_refs": _string_list(case.get("artifact_refs")),
        "control_observation": _compact_observation(control),
        "treatment_observation": _compact_observation(treatment),
        "dimension_results": dimension_results,
    }


def _dimension_result(
    *,
    dimension: dict[str, Any],
    control_metrics: dict[str, Any],
    treatment_metrics: dict[str, Any],
) -> dict[str, Any]:
    metric_id = str(dimension["metric_id"])
    direction = str(dimension["direction"])
    critical = bool(dimension.get("critical"))
    failure_reasons: list[str] = []
    control_value = _numeric_metric(control_metrics, metric_id)
    treatment_value = _numeric_metric(treatment_metrics, metric_id)
    if control_value is None:
        failure_reasons.append(f"control_metric_missing:{metric_id}")
    if treatment_value is None:
        failure_reasons.append(f"treatment_metric_missing:{metric_id}")

    quality_delta = None
    if control_value is not None and treatment_value is not None:
        quality_delta = (
            treatment_value - control_value
            if direction == "higher_is_better"
            else control_value - treatment_value
        )
        quality_delta = round(float(quality_delta), 6)

    return {
        "metric_id": metric_id,
        "direction": direction,
        "critical": critical,
        "control_value": control_value,
        "treatment_value": treatment_value,
        "quality_delta": quality_delta,
        "improved": quality_delta is not None and quality_delta > 0,
        "regressed": quality_delta is not None and quality_delta < 0,
        "critical_regression": critical
        and quality_delta is not None
        and quality_delta < 0,
        "failure_reasons": failure_reasons,
    }


def _observation(
    value: Any, *, manifest_path: Path, output_dir: Path
) -> dict[str, Any]:
    failures: list[str] = []
    observation = _dict(value)
    if observation.get("type") == "full_review_artifact_metrics":
        return _full_review_artifact_metrics(
            observation=observation,
            manifest_path=manifest_path,
            output_dir=output_dir,
        )
    path_value = observation.get("path")
    if path_value:
        path = _resolve_manifest_path(manifest_path=manifest_path, value=path_value)
        if not path.exists():
            return {
                "metrics": {},
                "failure_reasons": [f"observation_path_missing:{path}"],
                "evidence": {},
            }
        loaded = _read_json(path)
        observation = _dict(loaded)
        if not observation:
            failures.append(f"observation_path_not_object:{path}")

    metrics = _dict(observation.get("metrics"))
    if not metrics and observation and "metrics" not in observation:
        metrics = {
            key: item
            for key, item in observation.items()
            if isinstance(item, (int, float))
        }
    if not metrics:
        failures.append("observation_metrics_missing")
    return {"metrics": metrics, "failure_reasons": failures, "evidence": {}}


def _full_review_artifact_metrics(
    *, observation: dict[str, Any], manifest_path: Path, output_dir: Path
) -> dict[str, Any]:
    review_id = str(observation.get("review_id") or "").strip()
    source_set_id = str(observation.get("source_set_id") or "").strip()
    if not review_id:
        return {
            "metrics": {},
            "failure_reasons": ["review_id_missing"],
            "evidence": {},
        }
    review_dir = (
        _resolve_manifest_path(manifest_path=manifest_path, value=observation["review_dir"])
        if observation.get("review_dir")
        else output_dir / "reviews" / review_id
    )
    require_graph_gate = (
        bool(observation.get("require_graph_gate"))
        or observation.get("graph_gate_mode") == "gated_treatment"
    )
    artifacts = _full_review_artifacts(review_dir, require_graph_gate=require_graph_gate)
    loaded: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    evidence: dict[str, dict[str, Any]] = {}
    for artifact_id, path in artifacts.items():
        if not path.exists():
            failures.append(f"artifact_missing:{artifact_id}")
            continue
        loaded[artifact_id] = _read_json(path)
        evidence[artifact_id] = {"path": str(path), "sha256": sha256_file(path)}
    identity_mismatch_count = _identity_mismatch_count(
        loaded=loaded, review_id=review_id, source_set_id=source_set_id
    )
    if identity_mismatch_count:
        failures.append("artifact_identity_mismatch")

    phase = loaded.get("phase_eval", {})
    v1_eval = _dict(loaded.get("v1_eval", {}).get("summary"))
    compliance = _dict(loaded.get("compliance_review", {}).get("summary"))
    matrix = _dict(loaded.get("compliance_matrix", {}).get("summary"))
    app_validation = _dict(loaded.get("applicability_validation", {}).get("summary"))
    rule_pack = _dict(loaded.get("generated_rule_pack_validation", {}).get("summary"))
    gate_summary = loaded.get("gate_graph_summary", {})
    gate_validation = loaded.get("gate_graph_validation", {})
    gate_graph = loaded.get("gate_graph", {})

    graph_ready = (
        require_graph_gate
        and bool(gate_summary.get("passed"))
        and bool(gate_validation.get("passed"))
        and bool(_dict(gate_graph.get("validation")).get("passed"))
        and identity_mismatch_count == 0
    )
    ready_checks = [
        bool(phase.get("passed")) and bool(phase.get("reviewer_ready")),
        bool(v1_eval.get("passed")) or bool(v1_eval.get("actual_overall_passed")),
        bool(compliance.get("reviewer_ready")) and bool(compliance.get("validation_passed")),
        bool(matrix.get("reviewer_ready")) and bool(matrix.get("validated")),
        bool(app_validation.get("passed")) and bool(app_validation.get("reviewer_ready")),
        bool(rule_pack.get("passed")) or bool(rule_pack.get("generated_rule_pack_ready")),
        graph_ready,
    ]
    failed_phase_count = max(
        0, _int_value(phase.get("phase_count"), default=0)
        - _int_value(phase.get("passed_phase_count"), default=0)
    )
    unsupported_findings = _string_list(compliance.get("unsupported_finding_ids"))
    metrics = {
        "citation_gap_count": _int_value(compliance.get("rule_claim_gap_count"), default=0)
        + len(unsupported_findings),
        "unsupported_gate_pass_count": 0 if graph_ready else 1,
        "graph_gate_gap_count": 0 if graph_ready else 1,
        "readiness_blocker_count": len(_dict_list(phase.get("blockers"))) + failed_phase_count,
        "graph_gate_consistency_score": 1.0 if graph_ready else 0.0,
        "reviewer_traceability_score": round(sum(ready_checks) / len(ready_checks), 6),
        "full_review_artifact_count": len(evidence),
        "gate_node_count": _int_value(gate_summary.get("node_count"), default=0),
        "gate_edge_count": _int_value(gate_summary.get("edge_count"), default=0),
        "gate_validation_failed_check_count": _int_value(
            gate_summary.get("failed_check_count"), default=0
        ),
        "phase_count": _int_value(phase.get("phase_count"), default=0),
        "passed_phase_count": _int_value(phase.get("passed_phase_count"), default=0),
        "finding_count": _int_value(compliance.get("finding_count"), default=0),
        "identity_mismatch_count": identity_mismatch_count,
    }
    return {
        "metrics": metrics,
        "failure_reasons": sorted(set(failures)),
        "evidence": evidence,
        "observation_type": "full_review_artifact_metrics",
        "graph_gate_mode": observation.get("graph_gate_mode"),
    }

def _full_review_artifacts(review_dir: Path, *, require_graph_gate: bool) -> dict[str, Path]:
    artifacts = {
        "phase_eval": review_dir / "phase_eval_results.json",
        "v1_eval": review_dir / "v1_ea_eval_results.json",
        "compliance_review": review_dir / "compliance_review.json",
        "compliance_matrix": review_dir / "compliance_matrix.json",
        "compliance_validation": review_dir / "compliance_validation.json",
        "applicability_validation": review_dir / "applicability" / "applicability_validation.json",
        "generated_rule_pack_validation": review_dir
        / "applicability"
        / "generated_rule_pack_validation.json",
    }
    if require_graph_gate:
        artifacts.update(
            {
                "gate_graph": review_dir / "applicability" / "applicability_gate_graph.json",
                "gate_graph_summary": review_dir / "applicability" / "applicability_gate_graph_summary.json",
                "gate_graph_validation": review_dir / "applicability" / "applicability_gate_graph_validation.json",
            }
        )
    return artifacts


def _identity_mismatch_count(
    *, loaded: dict[str, dict[str, Any]], review_id: str, source_set_id: str
) -> int:
    mismatches = 0
    for artifact in loaded.values():
        actual_review_id = artifact.get("review_id") or _dict(artifact.get("summary")).get(
            "review_id"
        )
        actual_source_set_id = artifact.get("source_set_id") or _dict(
            artifact.get("summary")
        ).get("source_set_id")
        if actual_review_id and str(actual_review_id) != review_id:
            mismatches += 1
        if source_set_id and actual_source_set_id and str(actual_source_set_id) != source_set_id:
            mismatches += 1
    return mismatches


def _compact_observation(observation: dict[str, Any]) -> dict[str, Any]:
    return {
        "observation_type": observation.get("observation_type"),
        "graph_gate_mode": observation.get("graph_gate_mode"),
        "metrics": observation.get("metrics", {}),
        "evidence": observation.get("evidence", {}),
        "failure_reasons": observation.get("failure_reasons", []),
    }


def _frozen_input_checks(
    *, frozen_inputs: Any, manifest_path: Path
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for frozen_input in _frozen_input_rows(frozen_inputs):
        path_value = frozen_input.get("path")
        if not path_value:
            checks.append(
                {
                    "path": None,
                    "passed": False,
                    "reason": "frozen_input_path_missing",
                }
            )
            continue
        path = _resolve_manifest_path(manifest_path=manifest_path, value=path_value)
        exists = path.exists()
        expected_sha256 = str(frozen_input.get("sha256") or "").strip()
        actual_sha256 = sha256_file(path) if exists and expected_sha256 else None
        passed = exists and (
            not expected_sha256 or actual_sha256 == expected_sha256
        )
        reason = "passed"
        if not exists:
            reason = "frozen_input_missing"
        elif expected_sha256 and actual_sha256 != expected_sha256:
            reason = "frozen_input_sha256_mismatch"
        checks.append(
            {
                "path": str(path),
                "expected_sha256": expected_sha256 or None,
                "actual_sha256": actual_sha256,
                "passed": passed,
                "reason": reason,
            }
        )
    return checks


def _threshold_failures(
    *, thresholds: dict[str, Any], case_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    case_count = len(case_results)
    complete_case_count = sum(1 for case_result in case_results if case_result["complete"])
    positive_delta_case_count = sum(
        1 for case_result in case_results if case_result["has_positive_delta"]
    )
    critical_regression_count = sum(
        int(case_result["critical_regression_count"]) for case_result in case_results
    )
    case_contract_failure_count = sum(
        1 for case_result in case_results if case_result["contract_failure"]
    )
    net_quality_delta = round(
        sum(float(case_result["net_quality_delta"]) for case_result in case_results), 6
    )
    _append_min_failure(
        failures,
        thresholds,
        key="min_case_count",
        actual=case_count,
        default=1,
    )
    if "min_complete_case_count" in thresholds:
        _append_min_failure(
            failures,
            thresholds,
            key="min_complete_case_count",
            actual=complete_case_count,
            default=case_count,
        )
    if "min_distinct_review_count" in thresholds:
        distinct_review_count = len(
            {
                str(case_result.get("review_id") or "").strip()
                for case_result in case_results
                if str(case_result.get("review_id") or "").strip()
            }
        )
        _append_min_failure(
            failures,
            thresholds,
            key="min_distinct_review_count",
            actual=distinct_review_count,
            default=case_count,
        )
    _append_min_failure(
        failures,
        thresholds,
        key="min_positive_delta_case_count",
        actual=positive_delta_case_count,
        default=1,
    )
    _append_max_failure(
        failures,
        thresholds,
        key="max_critical_regression_count",
        actual=critical_regression_count,
        default=0,
    )
    _append_max_failure(
        failures,
        thresholds,
        key="max_case_contract_failure_count",
        actual=case_contract_failure_count,
        default=0,
    )
    if "min_net_quality_delta" in thresholds:
        expected = _float_value(thresholds.get("min_net_quality_delta"), default=0.0)
        if net_quality_delta < expected:
            failures.append(
                {
                    "name": "min_net_quality_delta",
                    "expected": expected,
                    "actual": net_quality_delta,
                    "category": "quality_delta",
                }
            )
    return failures


def _append_min_failure(
    failures: list[dict[str, Any]],
    thresholds: dict[str, Any],
    *,
    key: str,
    actual: int,
    default: int,
) -> None:
    expected = _int_value(thresholds.get(key), default=default)
    if actual < expected:
        failures.append(
            {
                "name": key,
                "expected": expected,
                "actual": actual,
                "category": "threshold",
            }
        )


def _append_max_failure(
    failures: list[dict[str, Any]],
    thresholds: dict[str, Any],
    *,
    key: str,
    actual: int,
    default: int,
) -> None:
    expected = _int_value(thresholds.get(key), default=default)
    if actual > expected:
        failures.append(
            {
                "name": key,
                "expected": expected,
                "actual": actual,
                "category": "threshold",
            }
        )


def _failure_category_counts(
    *,
    contract_checks: list[dict[str, Any]],
    case_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
    experiment_blocked: bool,
) -> Counter:
    counter: Counter = Counter()
    if experiment_blocked:
        counter["experiment_blocked"] += 1
    for check in contract_checks:
        if not check["passed"]:
            counter["contract_check_failed"] += 1
    for case_result in case_results:
        if case_result["contract_failure"]:
            counter["case_contract_failure"] += 1
        if int(case_result["critical_regression_count"]) > 0:
            counter["critical_regression"] += int(
                case_result["critical_regression_count"]
            )
    for failure in threshold_failures:
        counter[str(failure.get("name") or "threshold_failure")] += 1
    return counter


def _dimension_specs(value: Any) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for item in _dict_list(value):
        metric_id = str(item.get("metric_id") or item.get("id") or "").strip()
        direction = str(item.get("direction") or "").strip()
        if not metric_id or direction not in VALID_DIRECTIONS:
            continue
        specs[metric_id] = {
            "metric_id": metric_id,
            "label": item.get("label") or metric_id,
            "direction": direction,
            "critical": bool(item.get("critical")),
        }
    return specs


def _invalid_dimensions(value: Any) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for item in _dict_list(value):
        metric_id = str(item.get("metric_id") or item.get("id") or "").strip()
        direction = str(item.get("direction") or "").strip()
        if not metric_id or direction not in VALID_DIRECTIONS:
            invalid.append({"metric_id": metric_id, "direction": direction})
    return invalid


def _frozen_input_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    return _dict_list(value)


def _numeric_metric(metrics: dict[str, Any], metric_id: str) -> float | None:
    value = metrics.get(metric_id)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _stop_condition(manifest: dict[str, Any]) -> str:
    stop_condition = str(manifest.get("stop_condition") or "").strip()
    if stop_condition:
        return stop_condition
    stop_conditions = _string_list(manifest.get("stop_conditions"))
    return "; ".join(stop_conditions)


def _experiment_status(
    *, experiment_blocked: bool, hypothesis_supported: bool
) -> str:
    if experiment_blocked:
        return "experiment_blocked"
    if hypothesis_supported:
        return "hypothesis_supported"
    return "hypothesis_not_supported"


def _resolve_manifest_path(*, manifest_path: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    manifest_relative = manifest_path.parent / path
    if manifest_relative.exists():
        return manifest_relative
    return REPO_ROOT / path
