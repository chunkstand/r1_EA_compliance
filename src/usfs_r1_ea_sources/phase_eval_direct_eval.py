from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .rule_claim_binding import default_rule_claim_links_dir


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE_EVAL_DIRECT_EVAL_CONTRACT_PATH = (
    REPO_ROOT / "config" / "phase_eval_direct_eval_v1.json"
)
PHASE_EVAL_DIRECT_EVAL_SCHEMA_VERSION = "phase-eval-direct-eval-v1"
UPSTREAM_EVALUATION_RESULTS_SCHEMA_VERSION = "upstream-evaluation-results-v0"
DOWNSTREAM_DIRECT_EVAL_MANIFEST_SCHEMA_VERSION = "downstream-direct-eval-v1"
REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION = "real-package-review-coverage-v1"
REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION = (
    "real-package-review-coverage-results-v1"
)
V1_EA_EVAL_RESULTS_SCHEMA_VERSION = "v1-ea-real-review-eval-results-v0"
FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION = (
    "region1-forest-plan-profile-eval-results-v1"
)
FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-eval-coverage-v1"
)
FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-eval-coverage-results-v1"
)
FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-retrieval-eval-results-v1"
)
SOURCE_SET_COVERAGE_CLASSES = {"direct_eval_required", "validation_only_allowed"}
REVIEW_COVERAGE_CLASSES = {
    "required_for_declared_review_contract",
    "not_required_for_ad_hoc_review",
}
SOURCE_SET_PHASE_PRODUCERS = {
    "downstream_direct_evaluation",
    "forest_plan_component_retrieval_evaluation",
    "forest_plan_profile_evaluation",
    "phase_eval",
    "upstream_evaluation",
}


def load_phase_eval_direct_eval_contract(
    contract_path: Path = DEFAULT_PHASE_EVAL_DIRECT_EVAL_CONTRACT_PATH,
) -> dict[str, Any]:
    contract_path = Path(contract_path)
    payload = _read_json(contract_path)
    _validate_contract(payload)
    return payload


def resolve_phase_eval_direct_eval_coverage(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str | None = None,
    review_dir: Path | None = None,
    contract_path: Path = DEFAULT_PHASE_EVAL_DIRECT_EVAL_CONTRACT_PATH,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    contract_path = Path(contract_path)
    contract = load_phase_eval_direct_eval_contract(contract_path)
    config_dir = contract_path.parent

    upstream_results_path = output_dir / str(contract["upstream_results_path"])
    upstream_results = _read_json_if_exists(upstream_results_path)
    downstream_manifest_path = _resolve_repo_path(config_dir, contract["downstream_manifest_path"])
    downstream_manifest = _read_json_if_exists(downstream_manifest_path)
    review_coverage_manifest_path = _resolve_repo_path(
        config_dir,
        contract["review_contract_manifest_path"],
    )
    review_coverage_manifest = _read_json_if_exists(review_coverage_manifest_path)
    component_review_coverage_manifest_path = _resolve_repo_path(
        config_dir,
        contract["component_review_coverage_manifest_path"],
    )
    component_review_coverage_manifest = _read_json_if_exists(
        component_review_coverage_manifest_path
    )

    source_set_phase_statuses: dict[str, dict[str, Any]] = {}
    for spec in contract.get("source_set_phases", []):
        if not _source_set_phase_applies(spec=spec, source_set_id=source_set_id):
            continue
        source_set_phase_statuses[str(spec["phase_name"])] = _source_set_phase_status(
            spec=spec,
            source_set_id=source_set_id,
            output_dir=output_dir,
            upstream_results_path=upstream_results_path,
            upstream_results=upstream_results,
            downstream_manifest_path=downstream_manifest_path,
            downstream_manifest=downstream_manifest,
        )
    review_scope = _review_scope_status(
        contract=contract,
        output_dir=output_dir,
        review_id=review_id,
        review_dir=review_dir,
        review_coverage_manifest_path=review_coverage_manifest_path,
        review_coverage_manifest=review_coverage_manifest,
        component_review_coverage_manifest_path=component_review_coverage_manifest_path,
        component_review_coverage_manifest=component_review_coverage_manifest,
    )

    return {
        "schema_version": PHASE_EVAL_DIRECT_EVAL_SCHEMA_VERSION,
        "contract_id": str(contract["contract_id"]),
        "contract_version": str(contract.get("version") or ""),
        "contract_path": str(contract_path),
        "source_set_phase_statuses": source_set_phase_statuses,
        "review_scope": review_scope,
    }


def apply_source_set_phase_direct_eval_gate(
    phase: dict[str, Any],
    *,
    direct_eval_status: dict[str, Any] | None,
) -> dict[str, Any]:
    if direct_eval_status is None:
        return phase
    details = dict(phase.get("details") or {})
    details.update(
        {
            "direct_eval_coverage_class": direct_eval_status["coverage_class"],
            "direct_eval_status": direct_eval_status["status"],
            "direct_eval_required": direct_eval_status["coverage_class"]
            == "direct_eval_required",
            "direct_eval_present": bool(direct_eval_status["direct_eval_present"]),
            "direct_eval_passed": bool(direct_eval_status["direct_eval_passed"]),
            "direct_eval_summary_present": bool(direct_eval_status["summary_present"]),
            "direct_eval_summary_path": direct_eval_status.get("summary_path"),
            "direct_eval_contract_id": direct_eval_status.get("contract_id"),
            "direct_eval_case_count": direct_eval_status.get("case_count"),
            "direct_eval_hard_negative_case_count": direct_eval_status.get(
                "hard_negative_case_count"
            ),
            "direct_eval_threshold_failures": direct_eval_status.get(
                "threshold_failures",
                [],
            ),
            "direct_eval_details": direct_eval_status.get("details", {}),
            "proxy_only": False,
        }
    )
    passed = bool(phase.get("passed"))
    reviewer_ready = bool(phase.get("reviewer_ready"))
    failure_reasons = list(direct_eval_status.get("failure_reasons", []))
    if direct_eval_status["coverage_class"] == "direct_eval_required":
        if direct_eval_status["status"] == "direct_eval_missing":
            if passed or reviewer_ready:
                details["proxy_only"] = True
                failure_reasons.append("proxy_only_coverage")
            passed = False
            reviewer_ready = False
        elif direct_eval_status["status"] in {
            "direct_eval_identity_mismatch",
            "direct_eval_schema_invalid",
            "direct_eval_failed",
        }:
            passed = False
            reviewer_ready = False
    failure_reasons = _dedupe_strings(failure_reasons)
    if not passed and "phase_validation_failed" not in failure_reasons:
        failure_reasons.insert(0, "phase_validation_failed")
    if not reviewer_ready and "phase_not_reviewer_ready" not in failure_reasons:
        failure_reasons.append("phase_not_reviewer_ready")
    return {
        "name": phase["name"],
        "passed": passed,
        "reviewer_ready": reviewer_ready,
        "failure_reasons": failure_reasons,
        "details": details,
    }


def build_evaluation_coverage_phase(
    *,
    phases: list[dict[str, Any]],
    contract_id: str,
    contract_version: str,
    contract_path: str,
    review_scope: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    critical_phases = [
        phase
        for phase in phases
        if phase.get("details", {}).get("direct_eval_coverage_class") == "direct_eval_required"
    ]
    validation_only_phases = [
        phase
        for phase in phases
        if phase.get("details", {}).get("direct_eval_coverage_class")
        == "validation_only_allowed"
    ]
    direct_eval_ready_phase_count = sum(
        1
        for phase in critical_phases
        if phase.get("details", {}).get("direct_eval_status") == "direct_eval_present"
    )
    missing_direct_eval_phase_count = sum(
        1
        for phase in critical_phases
        if phase.get("details", {}).get("direct_eval_status") == "direct_eval_missing"
    )
    proxy_only_phase_count = sum(
        1 for phase in critical_phases if phase.get("details", {}).get("proxy_only")
    )
    threshold_failed_phase_count = sum(
        1
        for phase in critical_phases
        if phase.get("details", {}).get("direct_eval_status") == "direct_eval_failed"
    )
    identity_mismatch_phase_count = sum(
        1
        for phase in critical_phases
        if phase.get("details", {}).get("direct_eval_status")
        == "direct_eval_identity_mismatch"
    )
    schema_invalid_phase_count = sum(
        1
        for phase in critical_phases
        if phase.get("details", {}).get("direct_eval_status")
        == "direct_eval_schema_invalid"
    )
    review_scope = review_scope or _ad_hoc_review_scope(review_id=None)
    failure_reasons = []
    if missing_direct_eval_phase_count:
        failure_reasons.append("missing_required_direct_eval")
    if proxy_only_phase_count:
        failure_reasons.append("proxy_only_coverage")
    if threshold_failed_phase_count:
        failure_reasons.append("direct_eval_threshold_failed")
    if identity_mismatch_phase_count:
        failure_reasons.append("direct_eval_identity_mismatch")
    if schema_invalid_phase_count:
        failure_reasons.append("direct_eval_schema_invalid")
    failure_reasons.extend(review_scope.get("failure_reasons", []))
    failure_reasons = _dedupe_strings(failure_reasons)
    passed = not failure_reasons and bool(review_scope.get("passed", True))
    reviewer_ready = passed
    phase_statuses = {
        phase["name"]: phase.get("details", {}).get("direct_eval_status")
        for phase in critical_phases + validation_only_phases
    }
    details = {
        "phase_eval_contract_id": contract_id,
        "phase_eval_contract_version": contract_version,
        "phase_eval_contract_path": contract_path,
        "critical_phase_count": len(critical_phases),
        "critical_phase_names": [phase["name"] for phase in critical_phases],
        "direct_eval_ready_phase_count": direct_eval_ready_phase_count,
        "proxy_only_phase_count": proxy_only_phase_count,
        "missing_direct_eval_phase_count": missing_direct_eval_phase_count,
        "threshold_failed_phase_count": threshold_failed_phase_count,
        "identity_mismatch_phase_count": identity_mismatch_phase_count,
        "schema_invalid_phase_count": schema_invalid_phase_count,
        "validation_only_allowed_phase_count": len(validation_only_phases),
        "validation_only_allowed_phase_names": [
            phase["name"] for phase in validation_only_phases
        ],
        "phase_statuses": phase_statuses,
        "declared_review_contract": bool(review_scope.get("declared_review_contract")),
        "review_direct_eval_status": review_scope.get("status"),
        "required_review_eval_ids": review_scope.get("required_summary_ids", []),
        "missing_review_eval_ids": review_scope.get("missing_summary_ids", []),
        "contract_backed_promotion_ready": bool(
            review_scope.get("contract_backed_promotion_ready")
        ),
        "review_scope": review_scope,
    }
    phase = {
        "name": "evaluation_coverage",
        "passed": passed,
        "reviewer_ready": reviewer_ready,
        "failure_reasons": (
            ["phase_validation_failed", *failure_reasons, "phase_not_reviewer_ready"]
            if not reviewer_ready
            else []
        ),
        "details": details,
    }
    if phase["failure_reasons"]:
        phase["failure_reasons"] = _dedupe_strings(phase["failure_reasons"])
    summary_fields = {
        "phase_eval_contract_id": contract_id,
        "phase_eval_contract_version": contract_version,
        "phase_eval_contract_path": contract_path,
        "critical_phase_count": len(critical_phases),
        "direct_eval_ready_phase_count": direct_eval_ready_phase_count,
        "proxy_only_phase_count": proxy_only_phase_count,
        "missing_direct_eval_phase_count": missing_direct_eval_phase_count,
        "threshold_failed_phase_count": threshold_failed_phase_count,
        "identity_mismatch_phase_count": identity_mismatch_phase_count,
        "schema_invalid_phase_count": schema_invalid_phase_count,
        "validation_only_allowed_phase_count": len(validation_only_phases),
        "declared_review_contract": bool(review_scope.get("declared_review_contract")),
        "contract_backed_promotion_ready": bool(
            review_scope.get("contract_backed_promotion_ready")
        ),
        "required_review_eval_ids": review_scope.get("required_summary_ids", []),
        "missing_review_eval_ids": review_scope.get("missing_summary_ids", []),
        "review_direct_eval_status": review_scope.get("status"),
    }
    return phase, summary_fields


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


def _review_scope_status(
    *,
    contract: dict[str, Any],
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
    review_coverage_manifest_path: Path,
    review_coverage_manifest: dict[str, Any] | None,
    component_review_coverage_manifest_path: Path,
    component_review_coverage_manifest: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if review_id is None:
        return None
    if review_dir is None:
        review_dir = output_dir / "reviews" / review_id
    if not isinstance(review_coverage_manifest, dict):
        return {
            **_declared_review_base(review_id),
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "summaries": [],
        }
    if (
        review_coverage_manifest.get("schema_version")
        != REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION
    ):
        return {
            **_declared_review_base(review_id),
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "summaries": [],
        }
    slot = next(
        (
            item
            for item in review_coverage_manifest.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    if slot is None:
        return _ad_hoc_review_scope(review_id=review_id)

    summaries = []
    missing_summary_ids = []
    present_summary_ids = []
    failure_reasons = []
    expected_contract_status = str(slot.get("expected_contract_status") or "")

    v1_eval_path = review_dir / str(contract["declared_review_eval_path"])
    v1_payload = _read_json_if_exists(v1_eval_path)
    v1_summary = _v1_ea_eval_summary(
        review_id=review_id,
        expected_contract_status=expected_contract_status,
        path=v1_eval_path,
        payload=v1_payload,
        expected_source_set_id=None,
    )
    summaries.append(v1_summary)

    coverage_results_path = output_dir / str(contract["review_contract_results_path"])
    coverage_results = _read_json_if_exists(coverage_results_path)
    coverage_summary = _review_coverage_summary(
        review_id=review_id,
        slot=slot,
        manifest=review_coverage_manifest,
        path=coverage_results_path,
        payload=coverage_results,
    )
    summaries.append(coverage_summary)
    component_coverage_summary = _component_review_coverage_summary_for_review(
        review_id=review_id,
        contract=contract,
        output_dir=output_dir,
        manifest_path=component_review_coverage_manifest_path,
        manifest=component_review_coverage_manifest,
    )
    if component_coverage_summary is not None:
        summaries.append(component_coverage_summary)

    for summary in summaries:
        if summary["present"]:
            present_summary_ids.append(summary["summary_id"])
        else:
            missing_summary_ids.append(summary["summary_id"])
        failure_reasons.extend(summary.get("failure_reasons", []))

    status = "direct_eval_present"
    if any(summary["status"] == "direct_eval_schema_invalid" for summary in summaries):
        status = "direct_eval_schema_invalid"
    elif any(summary["status"] == "direct_eval_identity_mismatch" for summary in summaries):
        status = "direct_eval_identity_mismatch"
    elif any(summary["status"] == "direct_eval_missing" for summary in summaries):
        status = "direct_eval_missing"
    elif any(summary["status"] == "direct_eval_failed" for summary in summaries):
        status = "direct_eval_failed"

    passed = status == "direct_eval_present"
    contract_backed_promotion_ready = bool(
        passed and expected_contract_status == "reviewer_ready"
    )
    if status == "direct_eval_missing":
        failure_reasons.append("missing_required_direct_eval")
    if status == "direct_eval_identity_mismatch":
        failure_reasons.append("direct_eval_identity_mismatch")
    if status == "direct_eval_schema_invalid":
        failure_reasons.append("direct_eval_schema_invalid")
    if status == "direct_eval_failed":
        failure_reasons.append("direct_eval_threshold_failed")
    failure_reasons = _dedupe_strings(failure_reasons)
    return {
        **_declared_review_base(review_id),
        "status": status,
        "passed": passed,
        "contract_backed_promotion_ready": contract_backed_promotion_ready,
        "required_summary_ids": [summary["summary_id"] for summary in summaries],
        "present_summary_ids": present_summary_ids,
        "missing_summary_ids": missing_summary_ids,
        "failure_reasons": failure_reasons,
        "expected_contract_status": expected_contract_status,
        "summaries": summaries,
        "review_contract_manifest_path": str(review_coverage_manifest_path),
    }


def _declared_review_base(review_id: str) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "declared_review_contract": True,
        "coverage_class": "required_for_declared_review_contract",
        "contract_backed_promotion_ready": False,
        "required_summary_ids": [],
        "present_summary_ids": [],
        "missing_summary_ids": [],
    }


def _ad_hoc_review_scope(review_id: str | None) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "declared_review_contract": False,
        "coverage_class": "not_required_for_ad_hoc_review",
        "status": "not_required_for_ad_hoc_review",
        "passed": True,
        "contract_backed_promotion_ready": False,
        "required_summary_ids": [],
        "present_summary_ids": [],
        "missing_summary_ids": [],
        "failure_reasons": [],
        "summaries": [],
    }


def _v1_ea_eval_summary(
    *,
    review_id: str,
    expected_contract_status: str,
    path: Path,
    payload: dict[str, Any] | None,
    expected_source_set_id: str | None,
) -> dict[str, Any]:
    summary = {
        "summary_id": "v1_ea_eval",
        "path": str(path),
        "present": isinstance(payload, dict),
        "status": "direct_eval_missing",
        "passed": False,
        "failure_reasons": [],
        "details": {},
    }
    if not isinstance(payload, dict):
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    nested = payload.get("summary")
    contract = payload.get("contract")
    if not isinstance(nested, dict) or not isinstance(contract, dict):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    summary["details"] = {
        "schema_version": nested.get("schema_version"),
        "actual_contract_status": nested.get("contract_status"),
        "actual_review_id": nested.get("review_id"),
        "actual_source_set_id": nested.get("source_set_id"),
        "contract": contract,
    }
    if nested.get("schema_version") != V1_EA_EVAL_RESULTS_SCHEMA_VERSION:
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if (
        str(nested.get("review_id") or "") != review_id
        or str(contract.get("review_id") or "") not in {"", review_id}
    ):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if expected_source_set_id and str(nested.get("source_set_id") or "") != expected_source_set_id:
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if str(nested.get("contract_status") or "") != expected_contract_status:
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if not bool(nested.get("passed")):
        summary["status"] = "direct_eval_failed"
        summary["failure_reasons"] = ["direct_eval_threshold_failed"]
        return summary
    summary["status"] = "direct_eval_present"
    summary["passed"] = True
    return summary


def _review_coverage_summary(
    *,
    review_id: str,
    slot: dict[str, Any],
    manifest: dict[str, Any],
    path: Path,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "summary_id": "real_package_review_coverage",
        "path": str(path),
        "present": isinstance(payload, dict),
        "status": "direct_eval_missing",
        "passed": False,
        "failure_reasons": [],
        "details": {
            "slot_id": slot.get("slot_id"),
            "expected_contract_status": slot.get("expected_contract_status"),
        },
    }
    if not isinstance(payload, dict):
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    summary["details"].update(
        {
            "schema_version": payload.get("schema_version"),
            "real_package_review_coverage_id": payload.get(
                "real_package_review_coverage_id"
            ),
        }
    )
    if (
        payload.get("schema_version")
        != REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION
    ):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if str(payload.get("real_package_review_coverage_id") or "") != str(manifest.get("id") or ""):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    slot_result = next(
        (
            item
            for item in payload.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    summary["details"]["slot_result"] = slot_result
    if not isinstance(slot_result, dict):
        summary["status"] = "direct_eval_missing"
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    if (
        str(slot_result.get("slot_id") or "") != str(slot.get("slot_id") or "")
        or str(slot_result.get("expected_contract_status") or "")
        != str(slot.get("expected_contract_status") or "")
        or str(slot_result.get("actual_review_id") or "") != review_id
    ):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if not bool(slot_result.get("passed")):
        summary["status"] = "direct_eval_failed"
        summary["failure_reasons"] = ["direct_eval_threshold_failed"]
        return summary
    summary["status"] = "direct_eval_present"
    summary["passed"] = True
    return summary


def _component_review_coverage_summary_for_review(
    *,
    review_id: str,
    contract: dict[str, Any],
    output_dir: Path,
    manifest_path: Path,
    manifest: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(manifest, dict):
        return {
            "summary_id": "forest_plan_component_eval_coverage",
            "path": str(output_dir / str(contract["component_review_coverage_results_path"])),
            "present": False,
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "details": {
                "manifest_path": str(manifest_path),
                "reason": "component_review_coverage_manifest_missing",
            },
        }
    if (
        manifest.get("schema_version")
        != FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION
    ):
        return {
            "summary_id": "forest_plan_component_eval_coverage",
            "path": str(output_dir / str(contract["component_review_coverage_results_path"])),
            "present": False,
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "details": {
                "manifest_path": str(manifest_path),
                "manifest_schema_version": manifest.get("schema_version"),
            },
        }
    slot = next(
        (
            item
            for item in manifest.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    if slot is None:
        return None
    results_path = output_dir / str(contract["component_review_coverage_results_path"])
    payload = _read_json_if_exists(results_path)
    return _component_review_coverage_summary(
        review_id=review_id,
        slot=slot,
        manifest=manifest,
        manifest_path=manifest_path,
        path=results_path,
        payload=payload,
    )


def _component_review_coverage_summary(
    *,
    review_id: str,
    slot: dict[str, Any],
    manifest: dict[str, Any],
    manifest_path: Path,
    path: Path,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "summary_id": "forest_plan_component_eval_coverage",
        "path": str(path),
        "present": isinstance(payload, dict),
        "status": "direct_eval_missing",
        "passed": False,
        "failure_reasons": [],
        "details": {
            "manifest_path": str(manifest_path),
            "expected_coverage_id": manifest.get("id"),
            "expected_review_id": review_id,
            "expected_slot_id": slot.get("slot_id"),
            "expected_forest_unit_id": slot.get("forest_unit_id"),
            "expected_source_set_id": slot.get("expected_source_set_id"),
        },
    }
    if not isinstance(payload, dict):
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    required_keys = (
        "schema_version",
        "coverage_id",
        "passed",
        "required_review_ids",
        "covered_review_ids",
        "slots",
        "review_component_eval_coverage",
        "component_retrieval_eval",
    )
    if any(key not in payload for key in required_keys):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        summary["details"]["missing_keys"] = [
            key for key in required_keys if key not in payload
        ]
        return summary
    required_review_ids = _string_list(payload.get("required_review_ids"))
    covered_review_ids = _string_list(payload.get("covered_review_ids"))
    slot_result = next(
        (
            item
            for item in payload.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    summary["details"].update(
        {
            "schema_version": payload.get("schema_version"),
            "actual_coverage_id": payload.get("coverage_id"),
            "required_review_ids": required_review_ids,
            "covered_review_ids": covered_review_ids,
            "slot_result": slot_result,
            "review_component_eval_coverage": payload.get("review_component_eval_coverage"),
            "component_retrieval_eval": payload.get("component_retrieval_eval"),
        }
    )
    if (
        payload.get("schema_version")
        != FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION
    ):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if str(payload.get("coverage_id") or "") != str(manifest.get("id") or ""):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if review_id not in _string_list(manifest.get("required_review_ids")):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if review_id not in required_review_ids:
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if not isinstance(slot_result, dict):
        summary["status"] = "direct_eval_missing"
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    if (
        str(slot_result.get("slot_id") or "") != str(slot.get("slot_id") or "")
        or str(slot_result.get("review_id") or "") != review_id
        or str(slot_result.get("forest_unit_id") or "")
        != str(slot.get("forest_unit_id") or "")
        or str(slot_result.get("expected_source_set_id") or "")
        != str(slot.get("expected_source_set_id") or "")
    ):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    review_coverage = payload.get("review_component_eval_coverage")
    if not isinstance(review_coverage, dict):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if (
        not bool(payload.get("passed"))
        or not bool(review_coverage.get("passed"))
        or not bool(slot_result.get("passed"))
        or review_id not in covered_review_ids
    ):
        summary["status"] = "direct_eval_failed"
        summary["failure_reasons"] = ["direct_eval_threshold_failed"]
        return summary
    summary["status"] = "direct_eval_present"
    summary["passed"] = True
    return summary


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
    if (
        result.get("schema_version") != FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION
    ):
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


def _downstream_threshold_failures(*, result: dict[str, Any], contract: dict[str, Any]) -> list[dict]:
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


def _coverage_requirement_actual(result: dict[str, Any], key: str) -> int | None:
    if key == "case_count":
        return _first_numeric(
            result.get("case_count"),
            result.get("query_count"),
            _metric_value(result, "case_count"),
        )
    return _first_numeric(result.get(key), _metric_value(result, key))


def _metric_value(result: dict[str, Any], key: str) -> int | float | None:
    metrics = result.get("metrics")
    if isinstance(metrics, dict):
        return _numeric(metrics.get(key))
    return None


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


def _validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != PHASE_EVAL_DIRECT_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "phase-eval direct-eval contract must declare "
            f"schema_version={PHASE_EVAL_DIRECT_EVAL_SCHEMA_VERSION!r}"
        )
    if not str(payload.get("contract_id") or "").strip():
        raise ValueError("phase-eval direct-eval contract requires contract_id")
    source_set_phases = payload.get("source_set_phases")
    if not isinstance(source_set_phases, list) or not source_set_phases:
        raise ValueError("phase-eval direct-eval contract requires source_set_phases")
    seen_phase_names: set[str] = set()
    for spec in source_set_phases:
        if not isinstance(spec, dict):
            raise ValueError("source_set_phases entries must be objects")
        phase_name = str(spec.get("phase_name") or "").strip()
        coverage_class = str(spec.get("coverage_class") or "").strip()
        producer = str(spec.get("producer") or "").strip()
        required_source_set_ids = _string_list(spec.get("required_source_set_ids"))
        if not phase_name:
            raise ValueError("source_set_phases entries require phase_name")
        if phase_name in seen_phase_names:
            raise ValueError(f"duplicate phase-eval direct-eval phase_name {phase_name!r}")
        seen_phase_names.add(phase_name)
        if coverage_class not in SOURCE_SET_COVERAGE_CLASSES:
            raise ValueError(
                f"unsupported source-set phase coverage class {coverage_class!r}"
            )
        if coverage_class == "direct_eval_required" and not str(spec.get("lane_id") or "").strip():
            raise ValueError(f"direct-eval-required phase {phase_name!r} requires lane_id")
        if not producer:
            raise ValueError(f"phase-eval direct-eval phase {phase_name!r} requires producer")
        if producer not in SOURCE_SET_PHASE_PRODUCERS:
            raise ValueError(
                f"unsupported phase-eval direct-eval producer {producer!r}"
            )
        if producer == "forest_plan_profile_evaluation" and not str(
            spec.get("results_path") or ""
        ).strip():
            raise ValueError(
                f"forest-plan-profile direct-eval phase {phase_name!r} requires results_path"
            )
        if producer == "forest_plan_component_retrieval_evaluation" and not str(
            spec.get("results_path") or ""
        ).strip():
            raise ValueError(
                "forest-plan-component-retrieval direct-eval phase "
                f"{phase_name!r} requires results_path"
            )
        if spec.get("required_source_set_ids") is not None and not required_source_set_ids:
            raise ValueError(
                f"phase-eval direct-eval phase {phase_name!r} has an empty "
                "required_source_set_ids list"
            )
    for key in (
        "upstream_results_path",
        "downstream_manifest_path",
        "review_contract_manifest_path",
        "review_contract_results_path",
        "component_review_coverage_manifest_path",
        "component_review_coverage_results_path",
        "declared_review_eval_path",
    ):
        if not str(payload.get(key) or "").strip():
            raise ValueError(f"phase-eval direct-eval contract requires {key}")
    review_scope = payload.get("review_scope")
    if not isinstance(review_scope, dict):
        raise ValueError("phase-eval direct-eval contract requires review_scope")
    if (
        str(review_scope.get("declared_review_coverage_class") or "")
        != "required_for_declared_review_contract"
    ):
        raise ValueError(
            "review_scope.declared_review_coverage_class must be "
            "'required_for_declared_review_contract'"
        )
    if (
        str(review_scope.get("ad_hoc_review_coverage_class") or "")
        != "not_required_for_ad_hoc_review"
    ):
        raise ValueError(
            "review_scope.ad_hoc_review_coverage_class must be "
            "'not_required_for_ad_hoc_review'"
        )


def _resolve_repo_path(base_dir: Path, value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else (base_dir / path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    return _read_json(path) if Path(path).exists() else None


def _numeric(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _int_or_none(value: Any) -> int | None:
    numeric = _numeric(value)
    return int(numeric) if numeric is not None else None


def _first_numeric(*values: Any) -> int | None:
    for value in values:
        numeric = _numeric(value)
        if numeric is not None:
            return int(numeric)
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _profile_metric_sum(profiles: Any, key: str) -> int | None:
    if not isinstance(profiles, list):
        return None
    total = 0
    saw_value = False
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        numeric = _numeric(profile.get(key))
        if numeric is None:
            continue
        total += int(numeric)
        saw_value = True
    return total if saw_value else None


def _failed_contract_check_names(result: dict[str, Any]) -> list[str]:
    checks = result.get("contract_checks")
    if not isinstance(checks, list):
        return []
    return [
        str(check.get("name") or "")
        for check in checks
        if isinstance(check, dict) and not bool(check.get("passed"))
    ]


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


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
