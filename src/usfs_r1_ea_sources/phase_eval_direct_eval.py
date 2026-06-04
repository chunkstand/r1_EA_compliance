from __future__ import annotations

from pathlib import Path
from typing import Any

from .phase_eval_direct_eval_review import _ad_hoc_review_scope
from .phase_eval_direct_eval_review import resolve_review_scope_status
from .phase_eval_direct_eval_source_set import resolve_source_set_phase_statuses
from .phase_eval_direct_eval_support import DEFAULT_PHASE_EVAL_DIRECT_EVAL_CONTRACT_PATH
from .phase_eval_direct_eval_support import PHASE_EVAL_DIRECT_EVAL_SCHEMA_VERSION
from .phase_eval_direct_eval_support import REVIEW_COVERAGE_CLASSES
from .phase_eval_direct_eval_support import SOURCE_SET_COVERAGE_CLASSES
from .phase_eval_direct_eval_support import SOURCE_SET_PHASE_PRODUCERS
from .phase_eval_direct_eval_support import _dedupe_strings
from .phase_eval_direct_eval_support import _read_json
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _resolve_repo_path
from .phase_eval_direct_eval_support import _string_list


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

    source_set_phase_statuses = resolve_source_set_phase_statuses(
        contract=contract,
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=review_id,
        upstream_results_path=upstream_results_path,
        upstream_results=upstream_results,
        downstream_manifest_path=downstream_manifest_path,
        downstream_manifest=downstream_manifest,
    )
    review_scope = resolve_review_scope_status(
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
        if producer == "extraction_fidelity_evaluation" and not str(
            spec.get("results_path") or ""
        ).strip():
            raise ValueError(
                f"extraction-fidelity direct-eval phase {phase_name!r} requires results_path"
            )
        if producer == "forest_plan_component_retrieval_evaluation" and not str(
            spec.get("results_path") or ""
        ).strip():
            raise ValueError(
                "forest-plan-component-retrieval direct-eval phase "
                f"{phase_name!r} requires results_path"
            )
        if producer == "semantic_graph_direct_evaluation" and not (
            str(spec.get("results_path") or "").strip()
            or str(spec.get("results_filename") or "").strip()
        ):
            raise ValueError(
                f"semantic graph direct-eval phase {phase_name!r} requires "
                "results_path or results_filename"
            )
        if producer == "eval_context_graph_evaluation" and not str(
            spec.get("results_path") or ""
        ).strip():
            raise ValueError(
                f"context graph direct-eval phase {phase_name!r} requires results_path"
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
    declared_coverage_class = str(review_scope.get("declared_review_coverage_class") or "")
    ad_hoc_coverage_class = str(review_scope.get("ad_hoc_review_coverage_class") or "")
    if declared_coverage_class not in REVIEW_COVERAGE_CLASSES:
        raise ValueError(
            "review_scope.declared_review_coverage_class must be one of the supported "
            "review coverage classes"
        )
    if ad_hoc_coverage_class not in REVIEW_COVERAGE_CLASSES:
        raise ValueError(
            "review_scope.ad_hoc_review_coverage_class must be one of the supported "
            "review coverage classes"
        )
    if declared_coverage_class != "required_for_declared_review_contract":
        raise ValueError(
            "review_scope.declared_review_coverage_class must be "
            "'required_for_declared_review_contract'"
        )
    if ad_hoc_coverage_class != "not_required_for_ad_hoc_review":
        raise ValueError(
            "review_scope.ad_hoc_review_coverage_class must be "
            "'not_required_for_ad_hoc_review'"
        )
