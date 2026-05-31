from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

from .real_package_review_coverage_eval import (
    DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
)
from .v1_ea_eval_conditional import _conditional_adjudication_report
from .v1_ea_eval_conditional import _conditional_adjudication_summary
from .v1_ea_eval_conditional import _evaluate_conditional_expectations
from .v1_ea_eval_forest_plan import _evaluate_forest_plan
from .v1_ea_eval_forest_plan import _forest_plan_rule_bridge_index
from .v1_ea_eval_rule_expectations import _applicability_decisions_by_rule
from .v1_ea_eval_rule_expectations import _evaluate_baseline_alignment
from .v1_ea_eval_rule_expectations import _evaluate_rule_expectations
from .v1_ea_eval_rule_expectations import _evaluate_sections
from .v1_ea_eval_summary import _broader_ea_failure_category_counts
from .v1_ea_eval_summary import _checks
from .v1_ea_eval_summary import _contract_status
from .v1_ea_eval_summary import _eval_lanes
from .v1_ea_eval_summary import _evaluate_contract_lane_expectations
from .v1_ea_eval_summary import _failed_rule_expectations
from .v1_ea_eval_summary import _failed_rule_ids
from .v1_ea_eval_summary import _failed_rule_ids_by_category
from .v1_ea_eval_summary import _failure_category_counts
from .v1_ea_eval_summary import _forest_plan_failure_category_counts
from .v1_ea_eval_summary import _metrics
from .v1_ea_eval_support import DEFAULT_V1_EA_EVAL_PATH as _DEFAULT_V1_EA_EVAL_PATH
from .v1_ea_eval_support import V1_EA_EVAL_RESULTS_SCHEMA_VERSION
from .v1_ea_eval_support import _findings_by_rule
from .v1_ea_eval_support import _load_review_artifacts
from .v1_ea_eval_support import _matrix_by_rule
from .v1_ea_eval_support import _normalized_expected_lane_states
from .v1_ea_eval_support import _preserve_generated_at_when_semantically_unchanged
from .v1_ea_eval_support import _read_json
from .v1_ea_eval_support import _resolve_eval_file
from .v1_ea_eval_support import _resolve_review_dir
from .v1_ea_eval_support import _review_identity
from .v1_ea_eval_support import _string_list
from .v1_ea_eval_support import _utc_now
from .v1_ea_eval_support import _validate_contract


DEFAULT_V1_EA_EVAL_PATH = _DEFAULT_V1_EA_EVAL_PATH


@dataclass(frozen=True)
class V1EAReviewEvalResult:
    eval_file: Path
    review_dir: Path
    output_path: Path
    summary: dict[str, Any]


def run_v1_ea_review_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    review_dir: Path | None = None,
    eval_file: Path | None = None,
    manifest_path: Path = DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
    output_path: Path | None = None,
) -> V1EAReviewEvalResult:
    """Evaluate a real EA compliance review against the V1 adjudication contract."""

    resolved_eval_file = _resolve_eval_file(
        review_id=review_id,
        review_dir=review_dir,
        eval_file=eval_file,
        manifest_path=manifest_path,
    )
    contract = _read_json(resolved_eval_file)
    _validate_contract(contract)
    resolved_review_dir = _resolve_review_dir(
        output_dir=output_dir,
        review_id=review_id or contract.get("review_id"),
        review_dir=review_dir,
    )
    resolved_output_path = output_path or resolved_review_dir / "v1_ea_eval_results.json"

    artifacts = _load_review_artifacts(resolved_review_dir, bool(contract.get("forest_plan")))
    section_results = _evaluate_sections(
        section_expectations=contract.get("section_expectations", []),
        package_chunks=artifacts["package_chunks"],
    )
    finding_index = _findings_by_rule(artifacts["compliance_review"])
    matrix_index = _matrix_by_rule(artifacts["compliance_matrix"])
    applicability_decision_index = _applicability_decisions_by_rule(
        artifacts["applicability_decisions"]
    )
    forest_plan_bridge_index = _forest_plan_rule_bridge_index(
        contract=contract,
        artifacts=artifacts,
        section_results=section_results,
    )
    baseline_policy = contract.get("baseline_policy", {})
    baseline_results = _evaluate_baseline_alignment(
        finding_index=finding_index,
        matrix_index=matrix_index,
        require_source_record_match=baseline_policy.get(
            "require_source_record_match_authority",
            True,
        ),
        require_document_role_match=baseline_policy.get(
            "require_document_role_match_authority",
            True,
        ),
        expected_source_record_ids=baseline_policy.get("expected_source_record_ids", []),
    )
    rule_results = _evaluate_rule_expectations(
        rule_expectations=contract.get("rule_review_expectations", []),
        finding_index=finding_index,
        matrix_index=matrix_index,
        applicability_decision_index=applicability_decision_index,
        bridge_index=forest_plan_bridge_index,
        section_results=section_results,
    )
    conditional_results = _evaluate_conditional_expectations(
        conditional_expectations=contract.get("conditional_source_expectations", []),
        finding_index=finding_index,
        matrix_index=matrix_index,
        applicability_decision_index=applicability_decision_index,
        bridge_index=forest_plan_bridge_index,
        section_results=section_results,
        allow_unadjudicated=bool(
            contract.get("allow_unadjudicated_conditional_expectations", True)
        ),
    )
    conditional_adjudication = _conditional_adjudication_report(
        contract=contract,
        conditional_results=conditional_results,
    )
    forest_plan_results = _evaluate_forest_plan(
        expectations=contract.get("forest_plan", {}),
        artifacts=artifacts,
    )
    runtime_forest_scope = _runtime_forest_scope(
        contract=contract,
        forest_plan_results=forest_plan_results,
    )
    checks = _checks(
        contract=contract,
        review_dir=resolved_review_dir,
        artifacts=artifacts,
        section_results=section_results,
        baseline_results=baseline_results,
        rule_results=rule_results,
        conditional_results=conditional_results,
        conditional_adjudication=conditional_adjudication,
        forest_plan_results=forest_plan_results,
    )
    metrics = _metrics(
        section_results=section_results,
        baseline_results=baseline_results,
        rule_results=rule_results,
        conditional_results=conditional_results,
        conditional_adjudication=conditional_adjudication,
        forest_plan_results=forest_plan_results,
        artifacts=artifacts,
    )
    failure_category_counts = _failure_category_counts(
        section_results=section_results,
        baseline_results=baseline_results,
        rule_results=rule_results,
        conditional_results=conditional_results,
        conditional_adjudication=conditional_adjudication,
        forest_plan_results=forest_plan_results,
        artifact_errors=artifacts["artifact_errors"],
    )
    broader_ea_failure_category_counts = _broader_ea_failure_category_counts(
        section_results=section_results,
        baseline_results=baseline_results,
        rule_results=rule_results,
        conditional_results=conditional_results,
        conditional_adjudication=conditional_adjudication,
        artifact_errors=artifacts["artifact_errors"],
    )
    forest_plan_failure_category_counts = _forest_plan_failure_category_counts(
        forest_plan_results=forest_plan_results,
        artifact_errors=artifacts["artifact_errors"],
    )
    failed_rule_expectations = _failed_rule_expectations(
        rule_results=rule_results,
        conditional_results=conditional_results,
    )
    failed_rule_ids = _failed_rule_ids(failed_rule_expectations)
    failed_rule_ids_by_category = _failed_rule_ids_by_category(failed_rule_expectations)
    eval_lanes = _eval_lanes(
        checks=checks,
        section_results=section_results,
        baseline_results=baseline_results,
        rule_results=rule_results,
        conditional_results=conditional_results,
        forest_plan_results=forest_plan_results,
        artifacts=artifacts,
        failure_category_counts=failure_category_counts,
        broader_ea_failure_category_counts=broader_ea_failure_category_counts,
        forest_plan_failure_category_counts=forest_plan_failure_category_counts,
    )
    review_identity = _review_identity(
        artifacts["compliance_review"],
        artifacts.get("generated_rule_pack"),
    )
    contract_expectations = _evaluate_contract_lane_expectations(
        contract=contract,
        eval_lanes=eval_lanes,
    )
    summary_checks = list(checks)
    if contract_expectations["configured"]:
        summary_checks.append(
            {
                "name": "expected_lane_states_matched",
                "passed": contract_expectations["passed"],
                "details": contract_expectations["details"],
            }
        )
    passed = (
        contract_expectations["passed"]
        if contract_expectations["configured"]
        else all(check["passed"] for check in checks)
    )
    contract_status = _contract_status(
        contract_expectations=contract_expectations,
        eval_lanes=eval_lanes,
        passed=passed,
    )
    summary = {
        "schema_version": V1_EA_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "review_id": review_identity.get("review_id") or resolved_review_dir.name,
        "review_dir": str(resolved_review_dir),
        "eval_file": str(resolved_eval_file),
        "output_path": str(resolved_output_path),
        "generated_at": _utc_now(),
        "source_set_id": review_identity.get("source_set_id") or contract.get("source_set_id"),
        "forest_unit_id": contract.get("forest_unit_id"),
        "package_style_tags": _string_list(contract.get("package_style_tags")),
        "expected_lane_states": _normalized_expected_lane_states(
            contract.get("expected_lane_states")
        ),
        "allowed_blocker_categories": _string_list(contract.get("allowed_blocker_categories")),
        "passed": passed,
        "actual_overall_passed": eval_lanes["overall"]["passed"],
        "contract_status": contract_status,
        "broader_ea_passed": eval_lanes["broader_ea"]["passed"],
        "forest_plan_passed": eval_lanes["forest_plan"]["passed"],
        "runtime_forest_scope": runtime_forest_scope,
        "forest_plan_component_adjudication_required": eval_lanes["forest_plan"][
            "component_adjudication_required"
        ],
        "checks": summary_checks,
        "metrics": metrics,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "broader_ea_failure_category_counts": dict(
            sorted(broader_ea_failure_category_counts.items())
        ),
        "forest_plan_failure_category_counts": dict(
            sorted(forest_plan_failure_category_counts.items())
        ),
        "contract_expectations": contract_expectations["details"],
        "failed_rule_expectation_count": len(failed_rule_expectations),
        "failed_rule_ids": failed_rule_ids,
        "failed_rule_ids_by_category": failed_rule_ids_by_category,
        "failed_rule_expectations": failed_rule_expectations,
        "conditional_adjudication": _conditional_adjudication_summary(
            conditional_adjudication
        ),
        "eval_lanes": eval_lanes,
    }
    payload = {
        "summary": summary,
        "section_results": section_results,
        "baseline_results": baseline_results,
        "rule_results": rule_results,
        "conditional_results": conditional_results,
        "conditional_adjudication": conditional_adjudication,
        "forest_plan_results": forest_plan_results,
        "artifact_paths": artifacts["artifact_paths"],
        "contract": {
            "schema_version": contract.get("schema_version"),
            "eval_id": contract.get("eval_id"),
            "review_id": contract.get("review_id"),
            "source_set_id": contract.get("source_set_id"),
            "rule_pack_id": contract.get("rule_pack_id"),
            "rule_pack_version": contract.get("rule_pack_version"),
        },
    }
    payload = _preserve_generated_at_when_semantically_unchanged(
        payload,
        resolved_output_path,
    )
    summary = payload["summary"]
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return V1EAReviewEvalResult(
        eval_file=resolved_eval_file,
        review_dir=resolved_review_dir,
        output_path=resolved_output_path,
        summary=summary,
    )


def _runtime_forest_scope(
    *,
    contract: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
) -> dict[str, Any]:
    forest_plan_expectations = contract.get("forest_plan")
    if not isinstance(forest_plan_expectations, dict):
        forest_plan_expectations = {}

    expected_forest_unit_id = _string_or_none(contract.get("forest_unit_id"))
    expected_scope_status = _string_or_none(
        forest_plan_expectations.get("expected_scope_status")
    )
    scope_result = next(
        (
            result
            for result in forest_plan_results
            if isinstance(result, dict)
            and result.get("expectation_id") == "scope_status"
        ),
        None,
    )
    actual_scope_status = (
        _string_or_none(scope_result.get("actual"))
        if isinstance(scope_result, dict)
        else None
    )
    scope_status_expectation_passed = (
        bool(scope_result.get("passed")) if isinstance(scope_result, dict) else False
    )
    required = bool(expected_forest_unit_id or expected_scope_status)
    failure_reasons: list[str] = []
    if required:
        if not expected_forest_unit_id:
            failure_reasons.append("expected_forest_unit_missing")
        if not expected_scope_status:
            failure_reasons.append("expected_scope_status_missing")
        if scope_result is None:
            failure_reasons.append("runtime_scope_status_missing")
        elif not actual_scope_status:
            failure_reasons.append("runtime_scope_status_missing")
        elif expected_scope_status and actual_scope_status != expected_scope_status:
            failure_reasons.append("runtime_scope_status_mismatch")
        if scope_result is not None and not scope_status_expectation_passed:
            failure_reasons.append("runtime_scope_status_expectation_failed")

    return {
        "required": required,
        "passed": not failure_reasons,
        "expected_forest_unit_id": expected_forest_unit_id,
        "expected_scope_status": expected_scope_status,
        "actual_scope_status": actual_scope_status,
        "scope_status_expectation_present": scope_result is not None,
        "scope_status_expectation_passed": scope_status_expectation_passed,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _string_or_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
