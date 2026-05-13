from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any

from .real_package_review_coverage_eval import (
    DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
)
from .real_package_review_coverage_eval import resolve_real_package_review_eval_file


DEFAULT_V1_EA_EVAL_PATH = Path("config/v1_ecid_real_ea_eval.json")
V1_EA_EVAL_RESULTS_SCHEMA_VERSION = "v1-ea-real-review-eval-results-v0"
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
EXPECTED_APPLICABILITY_VALUES = {
    "applicable",
    "not_applicable",
    "needs_reviewer_resolution",
    "adjudicate",
}
FOREST_PLAN_ARTIFACTS = {
    "forest_plan_context_summary",
    "forest_plan_context",
    "forest_plan_component_findings",
    "forest_plan_applicable_standard_coverage",
    "forest_plan_reviewer_resolution_queue",
}
FOREST_PLAN_VALIDATION_CHECKS = {
    "forest_plan_component_gate_reviewer_ready",
}


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


def _resolve_eval_file(
    *,
    review_id: str | None,
    review_dir: Path | None,
    eval_file: Path | None,
    manifest_path: Path,
) -> Path:
    if eval_file is not None:
        return Path(eval_file)
    if review_id:
        return resolve_real_package_review_eval_file(
            review_id=review_id,
            manifest_path=manifest_path,
        )
    raise ValueError(
        "v1-ea-eval requires --eval-file or a tracked --review-id in the real-package "
        "review coverage manifest"
    )


def _preserve_generated_at_when_semantically_unchanged(
    payload: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    if not output_path.exists():
        return payload
    try:
        existing = _read_json(output_path)
    except (OSError, json.JSONDecodeError):
        return payload
    existing_summary = existing.get("summary") if isinstance(existing, dict) else None
    existing_generated_at = (
        existing_summary.get("generated_at")
        if isinstance(existing_summary, dict)
        else None
    )
    if not isinstance(existing_generated_at, str) or not existing_generated_at:
        return payload
    candidate = json.loads(json.dumps(payload))
    candidate["summary"]["generated_at"] = existing_generated_at
    if _without_summary_generated_at(candidate) == _without_summary_generated_at(existing):
        return candidate
    return payload


def _without_summary_generated_at(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(payload))
    summary = normalized.get("summary")
    if isinstance(summary, dict):
        summary.pop("generated_at", None)
    return normalized


def _resolve_review_dir(
    *,
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
) -> Path:
    if review_dir is not None:
        return review_dir
    if not review_id:
        raise ValueError("review_id is required when review_dir is not supplied")
    if not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ValueError(f"unsafe review_id: {review_id!r}")
    return output_dir / "reviews" / review_id


def _load_review_artifacts(review_dir: Path, require_forest_plan: bool) -> dict[str, Any]:
    specs = {
        "compliance_review": ("compliance_review.json", True, "json"),
        "compliance_matrix": ("compliance_matrix.json", True, "json"),
        "compliance_validation": ("compliance_validation.json", True, "json"),
        "package_chunks": ("package/package_chunks.jsonl", True, "jsonl"),
        "applicability_decisions": (
            "applicability/applicability_decisions.jsonl",
            False,
            "jsonl",
        ),
        "generated_rule_pack": ("applicability/generated_rule_pack.json", False, "json"),
        "forest_plan_context_summary": ("forest_plan_context_summary.json", require_forest_plan, "json"),
        "forest_plan_context": ("forest_plan_context.json", require_forest_plan, "json"),
        "forest_plan_component_findings": (
            "forest_plan_component_findings.json",
            require_forest_plan,
            "json",
        ),
        "forest_plan_applicable_standard_coverage": (
            "forest_plan_applicable_standard_coverage.json",
            require_forest_plan,
            "json",
        ),
        "forest_plan_component_adjudication_eval": (
            "forest_plan_component_adjudication_eval.json",
            False,
            "json",
        ),
        "forest_plan_reviewer_resolution_queue": (
            "forest_plan_reviewer_resolution_queue.json",
            False,
            "json",
        ),
    }
    artifacts: dict[str, Any] = {
        "artifact_errors": [],
        "artifact_paths": {},
    }
    for name, (relative, required, kind) in specs.items():
        path = review_dir / relative
        artifacts["artifact_paths"][name] = str(path)
        if not path.exists():
            artifacts[name] = [] if kind == "jsonl" else {}
            if required:
                artifacts["artifact_errors"].append(
                    {
                        "artifact": name,
                        "path": str(path),
                        "failure_category": "review_artifact_missing",
                        "message": "Required review artifact is missing.",
                    }
                )
            continue
        try:
            artifacts[name] = _read_jsonl(path) if kind == "jsonl" else _read_json(path)
        except (json.JSONDecodeError, OSError) as exc:
            artifacts[name] = [] if kind == "jsonl" else {}
            artifacts["artifact_errors"].append(
                {
                    "artifact": name,
                    "path": str(path),
                    "failure_category": "review_artifact_unreadable",
                    "message": str(exc),
                }
            )
    return artifacts


def _evaluate_sections(
    *,
    section_expectations: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for expectation in section_expectations:
        section_id = str(expectation["section_id"])
        terms = _expectation_terms(expectation)
        matches: list[dict[str, Any]] = []
        matched_terms: set[str] = set()
        for chunk in package_chunks:
            text = _chunk_text(chunk)
            chunk_terms = _matched_terms(text, terms)
            if not chunk_terms:
                continue
            matched_terms.update(chunk_terms)
            matches.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source_record_id": chunk.get("source_record_id"),
                    "title": chunk.get("title"),
                    "section": chunk.get("section"),
                    "heading": chunk.get("heading"),
                    "matched_terms": sorted(chunk_terms),
                }
            )
        detected = bool(matches)
        required = bool(expectation.get("required", True))
        result = {
            "section_id": section_id,
            "label": expectation.get("label", section_id),
            "required": required,
            "detected": detected,
            "passed": detected or not required,
            "matched_terms": sorted(matched_terms),
            "matched_chunk_count": len(matches),
            "matched_chunks": matches[:5],
            "failure_category": None if detected or not required else "ea_section_detection_miss",
        }
        results.append(result)
    return results


def _evaluate_baseline_alignment(
    *,
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    require_source_record_match: bool,
    require_document_role_match: bool,
    expected_source_record_ids: list[str],
) -> list[dict[str, Any]]:
    if not require_source_record_match and not require_document_role_match:
        return []
    results = []
    baseline_ids = sorted(
        rule_id
        for rule_id, finding in finding_index.items()
        if finding.get("applicability_mode") == "baseline"
    )
    for rule_id in baseline_ids:
        finding = finding_index[rule_id]
        row = matrix_index.get(rule_id, {})
        expected_source_id = finding.get("authority_source_record_id") or row.get(
            "authority_source_record_id"
        )
        expected_role = finding.get("authority_document_role") or row.get("authority_document_role")
        actual_source_ids = _actual_source_record_ids(finding, row)
        actual_roles = _actual_document_roles(finding, row)
        source_passed = (
            True
            if not require_source_record_match
            else not expected_source_id or expected_source_id in actual_source_ids
        )
        role_passed = (
            True
            if not require_document_role_match
            else not expected_role or expected_role in actual_roles
        )
        failure_categories: list[str] = []
        if not source_passed:
            failure_categories.append("baseline_source_record_mismatch")
        if not role_passed:
            failure_categories.append("baseline_document_role_mismatch")
        results.append(
            {
                "rule_id": rule_id,
                "expected_source_record_id": expected_source_id,
                "actual_source_record_ids": actual_source_ids,
                "source_record_match": source_passed,
                "expected_document_role": expected_role,
                "actual_document_roles": actual_roles,
                "document_role_match": role_passed,
                "passed": source_passed and role_passed,
                "failure_categories": failure_categories,
            }
        )
    if require_source_record_match:
        actual_authority_source_ids = {
            str(result["expected_source_record_id"])
            for result in results
            if result.get("expected_source_record_id")
        }
        for expected_source_id in sorted(str(value) for value in expected_source_record_ids):
            if expected_source_id in actual_authority_source_ids:
                continue
            results.append(
                {
                    "rule_id": None,
                    "expected_source_record_id": expected_source_id,
                    "actual_source_record_ids": [],
                    "source_record_match": False,
                    "expected_document_role": None,
                    "actual_document_roles": [],
                    "document_role_match": True,
                    "passed": False,
                    "failure_categories": ["baseline_source_record_missing"],
                }
            )
    return results


def _evaluate_rule_expectations(
    *,
    rule_expectations: list[dict[str, Any]],
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    applicability_decision_index: dict[str, dict[str, Any]],
    bridge_index: dict[str, dict[str, Any]],
    section_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for expectation in rule_expectations:
        rule_id = str(expectation["rule_id"])
        decision = applicability_decision_index.get(rule_id)
        bridge = bridge_index.get(rule_id)
        finding = finding_index.get(rule_id) or bridge or _decision_surrogate(decision)
        row = matrix_index.get(rule_id) or bridge or _decision_surrogate(decision)
        finding, row = _augment_with_decision_evidence(finding, row, decision)
        result = _evaluate_rule_source_section(
            expectation=expectation,
            finding=finding,
            row=row,
            section_results=section_results,
        )
        results.append(result)
    return results


def _evaluate_conditional_expectations(
    *,
    conditional_expectations: list[dict[str, Any]],
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    applicability_decision_index: dict[str, dict[str, Any]],
    bridge_index: dict[str, dict[str, Any]],
    section_results: list[dict[str, Any]],
    allow_unadjudicated: bool,
) -> list[dict[str, Any]]:
    results = []
    expected_rule_ids = {str(expectation["rule_id"]) for expectation in conditional_expectations}
    for expectation in conditional_expectations:
        rule_id = str(expectation["rule_id"])
        expected = str(expectation["expected_applicability"])
        decision = applicability_decision_index.get(rule_id)
        bridge = bridge_index.get(rule_id)
        finding = finding_index.get(rule_id) or bridge or _decision_surrogate(decision)
        row = matrix_index.get(rule_id) or bridge or _decision_surrogate(decision)
        finding, row = _augment_with_decision_evidence(finding, row, decision)
        source_section = _evaluate_rule_source_section(
            expectation=expectation,
            finding=finding,
            row=row,
            section_results=section_results,
        )
        actual_status = _actual_status(finding, row)
        actual_applicability = _actual_applicability(finding, row)
        actual_applicable = _is_actual_applicable(finding, row)
        failure_categories: list[str] = []
        applicability_match = True
        adjudication_pending = expected == "adjudicate"
        source_alignment_required = expected == "applicable" or (
            expected == "adjudicate" and actual_applicable
        )
        if expected == "applicable":
            applicability_match = actual_applicable
            if not actual_applicable:
                failure_categories.append("conditional_false_negative")
        elif expected == "not_applicable":
            applicability_match = not actual_applicable
            if actual_applicable:
                failure_categories.append("conditional_false_positive")
        elif expected == "needs_reviewer_resolution":
            applicability_match = actual_applicability == "needs_reviewer_resolution"
            if not applicability_match:
                failure_categories.append("conditional_resolution_miss")
        elif expected == "adjudicate":
            applicability_match = allow_unadjudicated
        if source_alignment_required:
            for category in source_section["failure_categories"]:
                if category not in failure_categories:
                    failure_categories.append(category)
            passed = applicability_match and source_section["passed"]
        else:
            passed = applicability_match
        results.append(
            {
                "rule_id": rule_id,
                "expected_applicability": expected,
                "actual_applicability": actual_applicability,
                "actual_status": actual_status,
                "actual_is_applicable": actual_applicable,
                "applicability_match": applicability_match,
                "adjudication_pending": adjudication_pending,
                "source_alignment_required": source_alignment_required,
                "trigger_terms": expectation.get("trigger_terms", []),
                "classification_rationale": expectation.get("classification_rationale"),
                "expected_package_section_ids": expectation.get("expected_package_section_ids", []),
                "actual_package_section_ids": source_section["actual_package_section_ids"],
                "section_match": source_section["section_match"],
                "expected_source_record_ids": expectation.get("expected_source_record_ids", []),
                "actual_source_record_ids": source_section["actual_source_record_ids"],
                "source_record_match": source_section["source_record_match"],
                "expected_source_document_roles": expectation.get(
                    "expected_source_document_roles",
                    [],
                ),
                "actual_source_document_roles": source_section["actual_source_document_roles"],
                "source_document_role_match": source_section["source_document_role_match"],
                "passed": passed,
                "failure_categories": failure_categories,
            }
        )
    for rule_id, finding in sorted(finding_index.items()):
        if str(finding.get("applicability_mode")) != "conditional":
            continue
        if rule_id in expected_rule_ids:
            continue
        row = matrix_index.get(rule_id)
        if not _is_actual_applicable(finding, row):
            continue
        results.append(
            {
                "rule_id": rule_id,
                "expected_applicability": "missing_contract_expectation",
                "actual_applicability": _actual_applicability(finding, row),
                "actual_status": _actual_status(finding, row),
                "actual_is_applicable": True,
                "applicability_match": False,
                "adjudication_pending": False,
                "source_alignment_required": True,
                "trigger_terms": [],
                "classification_rationale": None,
                "expected_package_section_ids": [],
                "actual_package_section_ids": [],
                "section_match": False,
                "expected_source_record_ids": [],
                "actual_source_record_ids": _actual_source_record_ids(finding, row or {}),
                "source_record_match": False,
                "expected_source_document_roles": [],
                "actual_source_document_roles": _actual_document_roles(finding, row or {}),
                "source_document_role_match": False,
                "passed": False,
                "failure_categories": ["conditional_expectation_missing"],
            }
        )
    return results


def _conditional_adjudication_report(
    *,
    contract: dict[str, Any],
    conditional_results: list[dict[str, Any]],
) -> dict[str, Any]:
    policy = contract.get("conditional_adjudication_policy")
    policy_present = isinstance(policy, dict) and bool(policy)
    policy = policy if isinstance(policy, dict) else {}
    pending_results = sorted(
        (
            result
            for result in conditional_results
            if result.get("adjudication_pending")
        ),
        key=lambda result: str(result.get("rule_id") or ""),
    )
    actual_pending_rule_ids = [
        str(result["rule_id"])
        for result in pending_results
        if str(result.get("rule_id") or "").strip()
    ]
    raw_accepted_pending_rule_ids = policy.get("accepted_pending_rule_ids")
    accepted_pending_rule_ids = _policy_rule_ids(raw_accepted_pending_rule_ids)
    accepted_pending_count = policy.get("accepted_pending_count")
    mode = str(policy.get("mode") or "").strip()
    failure_reasons = []
    if pending_results and not policy_present:
        failure_reasons.append("missing_conditional_adjudication_policy")
    if policy_present and mode != "accepted_pending_v1":
        failure_reasons.append("unsupported_conditional_adjudication_policy_mode")
    if policy_present and not isinstance(raw_accepted_pending_rule_ids, list):
        failure_reasons.append("accepted_pending_rule_ids_must_be_list")
    if policy_present and (
        not isinstance(accepted_pending_count, int)
        or isinstance(accepted_pending_count, bool)
    ):
        failure_reasons.append("accepted_pending_count_must_be_integer")
    elif policy_present and accepted_pending_count != len(actual_pending_rule_ids):
        failure_reasons.append("accepted_pending_count_mismatch")
    unexpected_pending_rule_ids = sorted(
        set(actual_pending_rule_ids) - set(accepted_pending_rule_ids)
    )
    missing_pending_rule_ids = sorted(
        set(accepted_pending_rule_ids) - set(actual_pending_rule_ids)
    )
    if unexpected_pending_rule_ids:
        failure_reasons.append("unexpected_pending_rule_ids")
    if missing_pending_rule_ids:
        failure_reasons.append("missing_pending_rule_ids")
    passed = not failure_reasons
    return {
        "schema_version": "conditional-adjudication-policy-results-v0",
        "passed": passed,
        "failure_category": None
        if passed
        else "conditional_adjudication_policy_mismatch",
        "failure_reasons": failure_reasons,
        "policy_present": policy_present,
        "policy_mode": mode or None,
        "policy_rationale": policy.get("rationale") if policy_present else None,
        "accepted_pending_count": accepted_pending_count if policy_present else None,
        "accepted_pending_rule_ids": accepted_pending_rule_ids,
        "actual_pending_count": len(actual_pending_rule_ids),
        "actual_pending_rule_ids": actual_pending_rule_ids,
        "actual_pending_applicable_count": sum(
            1 for result in pending_results if result.get("actual_is_applicable")
        ),
        "unexpected_pending_rule_ids": unexpected_pending_rule_ids,
        "missing_pending_rule_ids": missing_pending_rule_ids,
        "pending_results": [
            {
                "rule_id": result.get("rule_id"),
                "expected_applicability": result.get("expected_applicability"),
                "actual_applicability": result.get("actual_applicability"),
                "actual_status": result.get("actual_status"),
                "actual_is_applicable": result.get("actual_is_applicable"),
                "classification_rationale": result.get("classification_rationale"),
                "source_alignment_required": result.get("source_alignment_required"),
                "section_match": result.get("section_match"),
                "source_record_match": result.get("source_record_match"),
                "source_document_role_match": result.get("source_document_role_match"),
                "expected_package_section_ids": result.get(
                    "expected_package_section_ids",
                    [],
                ),
                "actual_package_section_ids": result.get("actual_package_section_ids", []),
                "expected_source_record_ids": result.get("expected_source_record_ids", []),
                "actual_source_record_ids": result.get("actual_source_record_ids", []),
                "expected_source_document_roles": result.get(
                    "expected_source_document_roles",
                    [],
                ),
                "actual_source_document_roles": result.get(
                    "actual_source_document_roles",
                    [],
                ),
            }
            for result in pending_results
        ],
    }


def _conditional_adjudication_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": report.get("passed"),
        "policy_mode": report.get("policy_mode"),
        "accepted_pending_count": report.get("accepted_pending_count"),
        "actual_pending_count": report.get("actual_pending_count"),
        "actual_pending_applicable_count": report.get("actual_pending_applicable_count"),
        "accepted_pending_rule_ids": report.get("accepted_pending_rule_ids", []),
        "actual_pending_rule_ids": report.get("actual_pending_rule_ids", []),
        "unexpected_pending_rule_ids": report.get("unexpected_pending_rule_ids", []),
        "missing_pending_rule_ids": report.get("missing_pending_rule_ids", []),
        "failure_reasons": report.get("failure_reasons", []),
    }


def _policy_rule_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(rule_id).strip() for rule_id in value if str(rule_id).strip())


def _evaluate_rule_source_section(
    *,
    expectation: dict[str, Any],
    finding: dict[str, Any] | None,
    row: dict[str, Any] | None,
    section_results: list[dict[str, Any]],
) -> dict[str, Any]:
    rule_id = str(expectation["rule_id"])
    failure_categories: list[str] = []
    if not finding and not row:
        return {
            "rule_id": rule_id,
            "present": False,
            "actual_status": None,
            "actual_applicability": None,
            "expected_package_section_ids": expectation.get("expected_package_section_ids", []),
            "actual_package_section_ids": [],
            "section_match": False,
            "expected_source_record_ids": expectation.get("expected_source_record_ids", []),
            "actual_source_record_ids": [],
            "source_record_match": False,
            "expected_source_document_roles": expectation.get(
                "expected_source_document_roles",
                [],
            ),
            "actual_source_document_roles": [],
            "source_document_role_match": False,
            "citation_requirements_met": False,
            "passed": False,
            "failure_categories": ["rule_missing"],
        }
    finding = finding or {}
    row = row or {}
    expected_sections = sorted(str(value) for value in expectation.get("expected_package_section_ids", []))
    actual_sections = _actual_package_section_ids(finding, row, section_results)
    section_match_mode = expectation.get("section_match", "all")
    if expected_sections:
        if section_match_mode == "any":
            section_match = bool(set(expected_sections) & set(actual_sections))
        else:
            section_match = set(expected_sections).issubset(actual_sections)
    else:
        section_match = True
    if not section_match:
        failure_categories.append("rule_section_mismatch")

    expected_sources = sorted(str(value) for value in expectation.get("expected_source_record_ids", []))
    actual_sources = _actual_source_record_ids(finding, row)
    source_match = not expected_sources or set(expected_sources).issubset(actual_sources)
    if not source_match:
        failure_categories.append("source_record_mismatch")

    expected_roles = sorted(
        str(value) for value in expectation.get("expected_source_document_roles", [])
    )
    actual_roles = _actual_document_roles(finding, row)
    role_match = not expected_roles or set(expected_roles).issubset(actual_roles)
    if not role_match:
        failure_categories.append("source_document_role_mismatch")

    citation_requirements_met = _citation_requirements_met(finding, row)
    if expectation.get("require_citations", True) and not citation_requirements_met:
        failure_categories.append("citation_requirement_miss")
    return {
        "rule_id": rule_id,
        "present": True,
        "actual_status": _actual_status(finding, row),
        "actual_applicability": _actual_applicability(finding, row),
        "expected_package_section_ids": expected_sections,
        "actual_package_section_ids": actual_sections,
        "section_match": section_match,
        "expected_source_record_ids": expected_sources,
        "actual_source_record_ids": actual_sources,
        "source_record_match": source_match,
        "expected_source_document_roles": expected_roles,
        "actual_source_document_roles": actual_roles,
        "source_document_role_match": role_match,
        "citation_requirements_met": citation_requirements_met,
        "passed": not failure_categories,
        "failure_categories": failure_categories,
    }


def _evaluate_forest_plan(
    *,
    expectations: dict[str, Any],
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    if not expectations:
        return []
    summary = artifacts["forest_plan_context_summary"]
    context = artifacts["forest_plan_context"]
    component_findings = artifacts["forest_plan_component_findings"]
    standard_coverage = artifacts["forest_plan_applicable_standard_coverage"]
    compliance_matrix = artifacts["compliance_matrix"]
    source_record_ids = _forest_source_record_ids(summary, context)
    geo_ids = _collect_values_by_key(context, {"geographic_area_id", "entry_id", "area_id"})
    management_ids = _collect_values_by_key(context, {"management_area_id", "entry_id"})
    overlay_ids = _collect_values_by_key(context, {"overlay_id", "entry_id"})
    component_ids = _collect_values_by_key(
        component_findings,
        {"component_id", "standard_id", "entry_id"},
    )
    applicable_standard_ids = _applicable_standard_ids(standard_coverage, component_findings)
    pending_reviewer_resolution_count = _pending_reviewer_resolution_count(artifacts)
    pending_standard_reviewer_resolution_count = _pending_standard_reviewer_resolution_count(
        artifacts
    )
    results = []

    def add_result(
        *,
        expectation_id: str,
        expected: Any,
        actual: Any,
        passed: bool,
        failure_category: str,
    ) -> None:
        results.append(
            {
                "expectation_id": expectation_id,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "failure_category": None if passed else failure_category,
            }
        )

    if expectations.get("expected_scope_status"):
        actual_scope = summary.get("scope_status") or context.get("scope_status")
        add_result(
            expectation_id="scope_status",
            expected=expectations["expected_scope_status"],
            actual=actual_scope,
            passed=actual_scope == expectations["expected_scope_status"],
            failure_category="forest_plan_scope_miss",
        )
    required_sources = set(str(value) for value in expectations.get("required_source_record_ids", []))
    if required_sources:
        add_result(
            expectation_id="required_source_record_ids",
            expected=sorted(required_sources),
            actual=sorted(source_record_ids),
            passed=required_sources.issubset(source_record_ids),
            failure_category="forest_plan_source_record_miss",
        )
    required_geo_ids = set(str(value) for value in expectations.get("expected_geographic_area_ids", []))
    if required_geo_ids:
        add_result(
            expectation_id="geographic_area_ids",
            expected=sorted(required_geo_ids),
            actual=sorted(geo_ids),
            passed=required_geo_ids.issubset(geo_ids),
            failure_category="forest_plan_component_miss",
        )
    required_management_ids = set(
        str(value) for value in expectations.get("expected_management_area_ids", [])
    )
    if required_management_ids:
        add_result(
            expectation_id="management_area_ids",
            expected=sorted(required_management_ids),
            actual=sorted(management_ids),
            passed=required_management_ids.issubset(management_ids),
            failure_category="forest_plan_component_miss",
        )
    required_overlay_ids = set(str(value) for value in expectations.get("expected_overlay_ids", []))
    if required_overlay_ids:
        add_result(
            expectation_id="overlay_ids",
            expected=sorted(required_overlay_ids),
            actual=sorted(overlay_ids),
            passed=required_overlay_ids.issubset(overlay_ids),
            failure_category="forest_plan_component_miss",
        )
    expected_component_ids = set(str(value) for value in expectations.get("expected_component_ids", []))
    if expected_component_ids:
        add_result(
            expectation_id="component_ids",
            expected=sorted(expected_component_ids),
            actual=sorted(component_ids),
            passed=expected_component_ids.issubset(component_ids),
            failure_category="forest_plan_component_miss",
        )
    expected_standards = set(
        str(value) for value in expectations.get("expected_applicable_standard_ids", [])
    )
    if expected_standards:
        add_result(
            expectation_id="applicable_standard_ids",
            expected=sorted(expected_standards),
            actual=sorted(applicable_standard_ids),
            passed=expected_standards.issubset(applicable_standard_ids),
            failure_category="applicable_standard_not_evaluated",
        )
    if expectations.get("min_applicable_standard_count") is not None:
        minimum = int(expectations["min_applicable_standard_count"])
        add_result(
            expectation_id="min_applicable_standard_count",
            expected=minimum,
            actual=len(applicable_standard_ids),
            passed=len(applicable_standard_ids) >= minimum,
            failure_category="applicable_standard_not_evaluated",
        )
    if expectations.get("require_all_applicable_standards_applied"):
        passed = bool(
            _nested_get(component_findings, ["summary", "all_applicable_standards_applied"])
            or _nested_get(summary, ["component_evaluation", "all_applicable_standards_applied"])
        )
        add_result(
            expectation_id="all_applicable_standards_applied",
            expected=True,
            actual=passed,
            passed=passed,
            failure_category="applicable_standard_not_evaluated",
        )
    if expectations.get("require_reviewer_ready"):
        actual_ready = bool(summary.get("reviewer_ready"))
        add_result(
            expectation_id="reviewer_ready",
            expected=True,
            actual=actual_ready,
            passed=actual_ready,
            failure_category="forest_plan_reviewer_not_ready",
        )
    if expectations.get("max_reviewer_resolution_items") is not None:
        maximum = int(expectations["max_reviewer_resolution_items"])
        actual_count = pending_reviewer_resolution_count
        add_result(
            expectation_id="reviewer_resolution_item_count",
            expected={"max": maximum},
            actual=actual_count,
            passed=actual_count <= maximum,
            failure_category="forest_plan_reviewer_resolution_open",
        )
    if expectations.get("max_standard_reviewer_resolution_items") is not None:
        maximum = int(expectations["max_standard_reviewer_resolution_items"])
        actual_count = pending_standard_reviewer_resolution_count
        add_result(
            expectation_id="standard_reviewer_resolution_item_count",
            expected={"max": maximum},
            actual=actual_count,
            passed=actual_count <= maximum,
            failure_category="forest_plan_standard_reviewer_resolution_open",
        )
    if expectations.get("require_matrix_forest_plan_compliance", True):
        matrix_details = _forest_plan_compliance_matrix_details(compliance_matrix)
        expected_standard_count = int(
            _nested_get(component_findings, ["summary", "applicable_standard_count"])
            or _nested_get(summary, ["component_evaluation", "applicable_standard_count"])
            or len(expected_standards)
        )
        matrix_visible = matrix_details["row_count"] > 0 and (
            expected_standard_count == 0
            or matrix_details["applicable_standard_row_count"] >= expected_standard_count
        )
        add_result(
            expectation_id="forest_plan_compliance_matrix",
            expected={
                "min_rows": 1,
                "applicable_standard_row_count": expected_standard_count,
            },
            actual=matrix_details,
            passed=matrix_visible,
            failure_category="forest_plan_matrix_miss",
        )
    return results


def _checks(
    *,
    contract: dict[str, Any],
    review_dir: Path,
    artifacts: dict[str, Any],
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    identity = _review_identity(
        artifacts["compliance_review"],
        artifacts.get("generated_rule_pack"),
    )
    validation = artifacts["compliance_validation"]
    return [
        {
            "name": "eval_contract_valid",
            "passed": True,
            "details": {"eval_id": contract.get("eval_id")},
        },
        {
            "name": "review_artifacts_loaded",
            "passed": not artifacts["artifact_errors"],
            "details": {"artifact_errors": artifacts["artifact_errors"]},
        },
        {
            "name": "review_identity_matches_contract",
            "passed": _identity_matches_contract(contract, identity, review_dir),
            "details": {"contract": _contract_identity(contract), "review": identity},
        },
        {
            "name": "compliance_validation_passed",
            "passed": bool(validation.get("passed", False)),
            "details": {
                "path": artifacts["artifact_paths"].get("compliance_validation"),
                "failed_checks": [
                    check.get("name")
                    for check in validation.get("checks", [])
                    if not check.get("passed")
                ],
            },
        },
        {
            "name": "required_sections_detected",
            "passed": all(result["passed"] for result in section_results),
            "details": _check_counts(section_results),
        },
        {
            "name": "baseline_source_documents_match_authority",
            "passed": all(result["passed"] for result in baseline_results),
            "details": _check_counts(baseline_results),
        },
        {
            "name": "rule_source_section_expectations_met",
            "passed": all(result["passed"] for result in rule_results),
            "details": _check_counts(rule_results),
        },
        {
            "name": "conditional_source_expectations_met",
            "passed": all(result["passed"] for result in conditional_results),
            "details": _check_counts(conditional_results),
        },
        {
            "name": "conditional_adjudication_policy_met",
            "passed": bool(conditional_adjudication.get("passed")),
            "details": {
                key: value
                for key, value in conditional_adjudication.items()
                if key != "pending_results"
            },
        },
        {
            "name": "forest_plan_expectations_met",
            "passed": all(result["passed"] for result in forest_plan_results),
            "details": _check_counts(forest_plan_results),
        },
    ]


def _metrics(
    *,
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    required_sections = [result for result in section_results if result["required"]]
    conditional_scored = [
        result for result in conditional_results if not result.get("adjudication_pending")
    ]
    conditional_applicable = [
        result for result in conditional_scored if result["expected_applicability"] == "applicable"
    ]
    conditional_actual_applicable = [
        result for result in conditional_results if result.get("actual_is_applicable")
    ]
    return {
        "required_section_count": len(required_sections),
        "detected_required_section_count": sum(1 for result in required_sections if result["detected"]),
        "section_detection_rate": _rate(
            sum(1 for result in required_sections if result["detected"]),
            len(required_sections),
        ),
        "baseline_rule_count": len(baseline_results),
        "baseline_source_record_match_rate": _rate(
            sum(1 for result in baseline_results if result["source_record_match"]),
            len(baseline_results),
        ),
        "baseline_document_role_match_rate": _rate(
            sum(1 for result in baseline_results if result["document_role_match"]),
            len(baseline_results),
        ),
        "rule_expectation_count": len(rule_results),
        "rule_section_match_rate": _rate(
            sum(1 for result in rule_results if result["section_match"]),
            len(rule_results),
        ),
        "source_record_match_rate": _rate(
            sum(1 for result in rule_results if result["source_record_match"]),
            len(rule_results),
        ),
        "source_document_role_match_rate": _rate(
            sum(1 for result in rule_results if result["source_document_role_match"]),
            len(rule_results),
        ),
        "citation_requirement_match_rate": _rate(
            sum(1 for result in rule_results if result["citation_requirements_met"]),
            len(rule_results),
        ),
        "conditional_expectation_count": len(conditional_results),
        "conditional_scored_count": len(conditional_scored),
        "conditional_adjudication_pending_count": sum(
            1 for result in conditional_results if result.get("adjudication_pending")
        ),
        "conditional_adjudication_completion_rate": _rate(
            len(conditional_scored),
            len(conditional_results),
        ),
        "conditional_adjudication_accepted_pending_count": conditional_adjudication.get(
            "accepted_pending_count"
        ),
        "conditional_adjudication_unexpected_pending_count": len(
            conditional_adjudication.get("unexpected_pending_rule_ids", [])
        ),
        "conditional_adjudication_missing_pending_count": len(
            conditional_adjudication.get("missing_pending_rule_ids", [])
        ),
        "conditional_expectation_match_rate": _rate(
            sum(1 for result in conditional_scored if result["applicability_match"]),
            len(conditional_scored),
        ),
        "conditional_applicable_source_record_match_rate": _rate(
            sum(1 for result in conditional_applicable if result["source_record_match"]),
            len(conditional_applicable),
        ),
        "conditional_applicable_section_match_rate": _rate(
            sum(1 for result in conditional_applicable if result["section_match"]),
            len(conditional_applicable),
        ),
        "conditional_actual_applicable_count": len(conditional_actual_applicable),
        "conditional_actual_applicable_source_record_match_rate": _rate(
            sum(1 for result in conditional_actual_applicable if result["source_record_match"]),
            len(conditional_actual_applicable),
        ),
        "conditional_actual_applicable_section_match_rate": _rate(
            sum(1 for result in conditional_actual_applicable if result["section_match"]),
            len(conditional_actual_applicable),
        ),
        "conditional_false_positive_count": _category_count(
            conditional_results,
            "conditional_false_positive",
        ),
        "conditional_false_negative_count": _category_count(
            conditional_results,
            "conditional_false_negative",
        ),
        "conditional_expectation_missing_count": _category_count(
            conditional_results,
            "conditional_expectation_missing",
        ),
        "forest_plan_expectation_count": len(forest_plan_results),
        "forest_plan_expectation_match_rate": _rate(
            sum(1 for result in forest_plan_results if result["passed"]),
            len(forest_plan_results),
        ),
        "reviewer_resolution_item_count": _pending_reviewer_resolution_count(artifacts),
        "standard_reviewer_resolution_item_count": _pending_standard_reviewer_resolution_count(
            artifacts
        ),
        "reviewer_resolution_queue_item_count": _reviewer_resolution_count(
            artifacts["forest_plan_reviewer_resolution_queue"]
        ),
        "standard_reviewer_resolution_queue_item_count": _reviewer_resolution_count_by_component_type(
            artifacts["forest_plan_reviewer_resolution_queue"],
            "standard",
        ),
    }


def _failure_category_counts(
    *,
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    forest_plan_results: list[dict[str, Any]],
    artifact_errors: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in artifact_errors:
        counts[str(error["failure_category"])] += 1
    for result in section_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    for result in baseline_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in rule_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in conditional_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    if not conditional_adjudication.get("passed"):
        category = conditional_adjudication.get("failure_category")
        if category:
            counts[str(category)] += 1
    for result in forest_plan_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    return counts


def _broader_ea_failure_category_counts(
    *,
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    conditional_adjudication: dict[str, Any],
    artifact_errors: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in artifact_errors:
        if str(error.get("artifact") or "") in FOREST_PLAN_ARTIFACTS:
            continue
        counts[str(error["failure_category"])] += 1
    for result in section_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    for result in baseline_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in rule_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    for result in conditional_results:
        for category in result.get("failure_categories", []):
            counts[str(category)] += 1
    if not conditional_adjudication.get("passed"):
        category = conditional_adjudication.get("failure_category")
        if category:
            counts[str(category)] += 1
    return counts


def _forest_plan_failure_category_counts(
    *,
    forest_plan_results: list[dict[str, Any]],
    artifact_errors: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for error in artifact_errors:
        if str(error.get("artifact") or "") in FOREST_PLAN_ARTIFACTS:
            counts[str(error["failure_category"])] += 1
    for result in forest_plan_results:
        if result.get("failure_category"):
            counts[str(result["failure_category"])] += 1
    return counts


def _failed_rule_expectations(
    *,
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failed: list[dict[str, Any]] = []
    for expectation_type, results in (
        ("rule_review_expectation", rule_results),
        ("conditional_source_expectation", conditional_results),
    ):
        for result in results:
            categories = [
                str(category)
                for category in result.get("failure_categories", [])
                if str(category).strip()
            ]
            if result.get("passed") and not categories:
                continue
            entry = {
                "expectation_type": expectation_type,
                "rule_id": result.get("rule_id"),
                "failure_categories": categories,
                "actual_applicability": result.get("actual_applicability"),
                "actual_status": result.get("actual_status"),
                "expected_package_section_ids": result.get("expected_package_section_ids", []),
                "actual_package_section_ids": result.get("actual_package_section_ids", []),
                "expected_source_record_ids": result.get("expected_source_record_ids", []),
                "actual_source_record_ids": result.get("actual_source_record_ids", []),
            }
            if expectation_type == "conditional_source_expectation":
                entry["expected_applicability"] = result.get("expected_applicability")
                entry["actual_is_applicable"] = result.get("actual_is_applicable")
                entry["adjudication_pending"] = result.get("adjudication_pending")
            failed.append(entry)
    return failed


def _failed_rule_ids(failed_rule_expectations: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(expectation["rule_id"])
            for expectation in failed_rule_expectations
            if expectation.get("rule_id")
        }
    )


def _failed_rule_ids_by_category(
    failed_rule_expectations: list[dict[str, Any]],
) -> dict[str, list[str]]:
    category_rule_ids: dict[str, set[str]] = {}
    for expectation in failed_rule_expectations:
        rule_id = expectation.get("rule_id")
        if not rule_id:
            continue
        for category in expectation.get("failure_categories", []):
            category_rule_ids.setdefault(str(category), set()).add(str(rule_id))
    return {
        category: sorted(rule_ids)
        for category, rule_ids in sorted(category_rule_ids.items())
    }


def _eval_lanes(
    *,
    checks: list[dict[str, Any]],
    section_results: list[dict[str, Any]],
    baseline_results: list[dict[str, Any]],
    rule_results: list[dict[str, Any]],
    conditional_results: list[dict[str, Any]],
    forest_plan_results: list[dict[str, Any]],
    artifacts: dict[str, Any],
    failure_category_counts: Counter[str],
    broader_ea_failure_category_counts: Counter[str],
    forest_plan_failure_category_counts: Counter[str],
) -> dict[str, Any]:
    check_by_name = {str(check["name"]): check for check in checks}
    broader_check_names = [
        "eval_contract_valid",
        "review_artifacts_loaded",
        "review_identity_matches_contract",
        "required_sections_detected",
        "baseline_source_documents_match_authority",
        "rule_source_section_expectations_met",
        "conditional_source_expectations_met",
        "conditional_adjudication_policy_met",
    ]
    broader_failed_checks = []
    for name in broader_check_names:
        check = check_by_name.get(name)
        if not check:
            continue
        if name == "review_artifacts_loaded":
            non_forest_artifact_errors = [
                error
                for error in artifacts["artifact_errors"]
                if str(error.get("artifact") or "") not in FOREST_PLAN_ARTIFACTS
            ]
            if non_forest_artifact_errors:
                broader_failed_checks.append(name)
            continue
        if not check.get("passed"):
            broader_failed_checks.append(name)

    validation_check = check_by_name.get("compliance_validation_passed")
    validation_failed_checks = _failed_compliance_validation_check_names(validation_check)
    if validation_check and not validation_check.get("passed"):
        non_forest_validation_failures = [
            name
            for name in validation_failed_checks
            if name not in FOREST_PLAN_VALIDATION_CHECKS
        ]
        if non_forest_validation_failures or not validation_failed_checks:
            broader_failed_checks.append("compliance_validation_passed")

    forest_artifact_errors = [
        error
        for error in artifacts["artifact_errors"]
        if str(error.get("artifact") or "") in FOREST_PLAN_ARTIFACTS
    ]
    forest_failed_checks = []
    if forest_artifact_errors:
        forest_failed_checks.append("review_artifacts_loaded")
    if any(name in FOREST_PLAN_VALIDATION_CHECKS for name in validation_failed_checks):
        forest_failed_checks.append("compliance_validation_passed")
    forest_plan_check = check_by_name.get("forest_plan_expectations_met")
    if forest_plan_check and not forest_plan_check.get("passed"):
        forest_failed_checks.append("forest_plan_expectations_met")

    reviewer_resolution_queue_count = _reviewer_resolution_count(
        artifacts["forest_plan_reviewer_resolution_queue"]
    )
    standard_reviewer_resolution_queue_count = _reviewer_resolution_count_by_component_type(
        artifacts["forest_plan_reviewer_resolution_queue"],
        "standard",
    )
    pending_reviewer_resolution_count = _pending_reviewer_resolution_count(artifacts)
    pending_standard_reviewer_resolution_count = _pending_standard_reviewer_resolution_count(
        artifacts
    )
    component_adjudication_summary = _forest_plan_component_adjudication_summary(artifacts)
    overall_failed_checks = [
        str(check["name"]) for check in checks if not bool(check.get("passed"))
    ]
    return {
        "overall": {
            "passed": not overall_failed_checks,
            "failed_check_names": overall_failed_checks,
            "failure_category_counts": dict(sorted(failure_category_counts.items())),
        },
        "broader_ea": {
            "passed": not broader_failed_checks,
            "failed_check_names": broader_failed_checks,
            "failure_category_counts": dict(
                sorted(broader_ea_failure_category_counts.items())
            ),
            "section_expectation_count": len(section_results),
            "baseline_rule_count": len(baseline_results),
            "rule_expectation_count": len(rule_results),
            "conditional_expectation_count": len(conditional_results),
        },
        "forest_plan": {
            "passed": not forest_failed_checks,
            "failed_check_names": forest_failed_checks,
            "failure_category_counts": dict(
                sorted(forest_plan_failure_category_counts.items())
            ),
            "expectation_count": len(forest_plan_results),
            "passed_expectation_count": sum(
                1 for result in forest_plan_results if result.get("passed")
            ),
            "failed_expectation_count": sum(
                1 for result in forest_plan_results if not result.get("passed")
            ),
            "pending_component_adjudication_count": pending_reviewer_resolution_count,
            "pending_standard_adjudication_count": pending_standard_reviewer_resolution_count,
            "reviewer_resolution_queue_item_count": reviewer_resolution_queue_count,
            "standard_reviewer_resolution_queue_item_count": standard_reviewer_resolution_queue_count,
            "component_adjudication_required": reviewer_resolution_queue_count > 0,
            "component_adjudication_present": bool(component_adjudication_summary),
            "component_adjudication_reviewer_ready": bool(
                component_adjudication_summary.get("reviewer_ready")
            ),
        },
    }


def _failed_compliance_validation_check_names(check: dict[str, Any] | None) -> list[str]:
    if not check:
        return []
    details = check.get("details")
    if not isinstance(details, dict):
        return []
    return [
        str(name)
        for name in details.get("failed_checks") or []
        if str(name).strip()
    ]


def _evaluate_contract_lane_expectations(
    *,
    contract: dict[str, Any],
    eval_lanes: dict[str, Any],
) -> dict[str, Any]:
    expected_lane_states = _normalized_expected_lane_states(
        contract.get("expected_lane_states")
    )
    allowed_blocker_categories = set(_string_list(contract.get("allowed_blocker_categories")))
    if not expected_lane_states:
        return {
            "configured": False,
            "passed": False,
            "details": {
                "configured": False,
                "expected_lane_states": {},
                "allowed_blocker_categories": sorted(allowed_blocker_categories),
            },
        }

    actual_lane_states = {
        "passed": bool(eval_lanes["overall"]["passed"]),
        "broader_ea_passed": bool(eval_lanes["broader_ea"]["passed"]),
        "forest_plan_passed": bool(eval_lanes["forest_plan"]["passed"]),
    }
    mismatches = []
    expected_blocked_lanes = []
    blocker_categories: set[str] = set()
    unexpected_blocker_categories: set[str] = set()
    for lane_name, expected in expected_lane_states.items():
        actual = actual_lane_states[lane_name]
        if actual != expected:
            mismatches.append(
                {
                    "lane": lane_name,
                    "expected": expected,
                    "actual": actual,
                }
            )
        if expected:
            continue
        expected_blocked_lanes.append(lane_name)
        actual_categories = set(_lane_failure_categories(eval_lanes, lane_name))
        blocker_categories.update(actual_categories)
        unexpected_blocker_categories.update(actual_categories - allowed_blocker_categories)
    missing_blocker_categories = bool(expected_blocked_lanes) and not blocker_categories
    passed = not mismatches and not missing_blocker_categories and not unexpected_blocker_categories
    return {
        "configured": True,
        "passed": passed,
        "details": {
            "configured": True,
            "expected_lane_states": expected_lane_states,
            "actual_lane_states": actual_lane_states,
            "allowed_blocker_categories": sorted(allowed_blocker_categories),
            "expected_blocked_lanes": expected_blocked_lanes,
            "matched_blocker_categories": sorted(blocker_categories),
            "unexpected_blocker_categories": sorted(unexpected_blocker_categories),
            "missing_blocker_categories": missing_blocker_categories,
            "mismatches": mismatches,
        },
    }


def _contract_status(
    *,
    contract_expectations: dict[str, Any],
    eval_lanes: dict[str, Any],
    passed: bool,
) -> str:
    if not passed:
        return "mismatch"
    details = contract_expectations.get("details")
    if not isinstance(details, dict) or not contract_expectations.get("configured"):
        return "reviewer_ready" if eval_lanes["overall"]["passed"] else "matched"
    if details.get("expected_blocked_lanes"):
        return "typed_blocked"
    return "reviewer_ready"


def _normalized_expected_lane_states(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, bool] = {}
    key_aliases = {
        "passed": "passed",
        "overall_passed": "passed",
        "broader_ea_passed": "broader_ea_passed",
        "forest_plan_passed": "forest_plan_passed",
    }
    for raw_key, expected in value.items():
        key = key_aliases.get(str(raw_key))
        if key is None or not isinstance(expected, bool):
            continue
        normalized[key] = expected
    return normalized


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _lane_failure_categories(eval_lanes: dict[str, Any], lane_name: str) -> list[str]:
    if lane_name == "passed":
        lane = eval_lanes["overall"]
    elif lane_name == "broader_ea_passed":
        lane = eval_lanes["broader_ea"]
    elif lane_name == "forest_plan_passed":
        lane = eval_lanes["forest_plan"]
    else:
        return []
    failure_categories = lane.get("failure_category_counts")
    if not isinstance(failure_categories, dict):
        return []
    return [
        str(category)
        for category, count in sorted(failure_categories.items())
        if str(category).strip() and int(count or 0) > 0
    ]


def _validate_contract(contract: dict[str, Any]) -> None:
    if not isinstance(contract, dict):
        raise ValueError("V1 EA eval contract must be a JSON object")
    if not contract.get("eval_id"):
        raise ValueError("V1 EA eval contract requires eval_id")
    for index, expectation in enumerate(contract.get("section_expectations", []), start=1):
        if not expectation.get("section_id"):
            raise ValueError(f"section_expectations[{index}] requires section_id")
        if not _expectation_terms(expectation):
            raise ValueError(f"section_expectations[{index}] requires expected_terms or aliases")
    forest_unit_id = contract.get("forest_unit_id")
    if forest_unit_id is not None and not str(forest_unit_id).strip():
        raise ValueError("forest_unit_id must be a non-empty string when provided")
    package_style_tags = contract.get("package_style_tags")
    if package_style_tags is not None and (
        not isinstance(package_style_tags, list)
        or not all(isinstance(tag, str) and tag.strip() for tag in package_style_tags)
    ):
        raise ValueError("package_style_tags must contain only non-empty strings")
    expected_lane_states = contract.get("expected_lane_states")
    normalized_lane_states = _normalized_expected_lane_states(expected_lane_states)
    if expected_lane_states is not None:
        if not isinstance(expected_lane_states, dict):
            raise ValueError("expected_lane_states must be a JSON object when provided")
        if len(normalized_lane_states) != len(expected_lane_states):
            raise ValueError(
                "expected_lane_states may only contain boolean passed/overall_passed/"
                "broader_ea_passed/forest_plan_passed fields"
            )
    allowed_blocker_categories = contract.get("allowed_blocker_categories")
    if allowed_blocker_categories is not None and (
        not isinstance(allowed_blocker_categories, list)
        or not all(
            isinstance(category, str) and category.strip()
            for category in allowed_blocker_categories
        )
    ):
        raise ValueError("allowed_blocker_categories must contain only non-empty strings")
    if any(expected is False for expected in normalized_lane_states.values()):
        if not _string_list(allowed_blocker_categories):
            raise ValueError(
                "allowed_blocker_categories is required when expected_lane_states includes "
                "a false lane state"
            )
    for name in ("rule_review_expectations", "conditional_source_expectations"):
        for index, expectation in enumerate(contract.get(name, []), start=1):
            if not expectation.get("rule_id"):
                raise ValueError(f"{name}[{index}] requires rule_id")
            if name == "conditional_source_expectations":
                value = expectation.get("expected_applicability")
                if value not in EXPECTED_APPLICABILITY_VALUES:
                    raise ValueError(
                        f"{name}[{index}] has invalid expected_applicability: {value!r}"
                    )
                if not str(expectation.get("classification_rationale") or "").strip():
                    raise ValueError(f"{name}[{index}] requires classification_rationale")
    adjudicate_rule_ids = sorted(
        str(expectation["rule_id"])
        for expectation in contract.get("conditional_source_expectations", [])
        if expectation.get("expected_applicability") == "adjudicate"
        and str(expectation.get("rule_id") or "").strip()
    )
    if adjudicate_rule_ids:
        policy = contract.get("conditional_adjudication_policy")
        if not isinstance(policy, dict):
            raise ValueError(
                "conditional_adjudication_policy is required when conditional "
                "expectations use expected_applicability=adjudicate"
            )
        if policy.get("mode") != "accepted_pending_v1":
            raise ValueError("conditional_adjudication_policy.mode must be accepted_pending_v1")
        raw_accepted_rule_ids = policy.get("accepted_pending_rule_ids")
        if not isinstance(raw_accepted_rule_ids, list):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must be a list"
            )
        if not all(
            isinstance(rule_id, str) and rule_id.strip()
            for rule_id in raw_accepted_rule_ids
        ):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must contain "
                "non-empty strings"
            )
        accepted_rule_ids = _policy_rule_ids(raw_accepted_rule_ids)
        if accepted_rule_ids != adjudicate_rule_ids:
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must match "
                "adjudicate conditional expectations"
            )
        accepted_pending_count = policy.get("accepted_pending_count")
        if not isinstance(accepted_pending_count, int) or isinstance(
            accepted_pending_count,
            bool,
        ):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_count must be an integer"
            )
        if accepted_pending_count != len(adjudicate_rule_ids):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_count must match "
                "adjudicate conditional expectation count"
            )
        if not str(policy.get("rationale") or "").strip():
            raise ValueError("conditional_adjudication_policy requires rationale")


def _findings_by_rule(compliance_review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(finding["rule_id"]): finding
        for finding in compliance_review.get("findings", [])
        if finding.get("rule_id")
    }


def _matrix_by_rule(compliance_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["rule_id"]): row
        for row in compliance_matrix.get("rows", [])
        if row.get("rule_id")
    }


def _applicability_decisions_by_rule(
    decisions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        rule_id = _decision_rule_id(decision)
        if rule_id and rule_id not in indexed:
            indexed[rule_id] = decision
    return indexed


def _decision_rule_id(decision: dict[str, Any]) -> str | None:
    rule_template = decision.get("rule_template")
    if isinstance(rule_template, dict):
        for key in ("rule_id", "id"):
            value = str(rule_template.get(key) or "").strip()
            if value:
                return value
    candidate_id = str(decision.get("candidate_authority_id") or "").strip()
    if candidate_id.startswith("rule-template:"):
        parts = candidate_id.split(":")
        if len(parts) >= 4 and parts[-1]:
            return parts[-1]
    return None


def _decision_surrogate(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(decision, dict):
        return None
    rule_id = _decision_rule_id(decision)
    if not rule_id:
        return None
    status = str(decision.get("status") or "").strip()
    if status == "applicable":
        review_status = "pass"
        applicability_status = "applicable"
    elif status == "not_applicable":
        review_status = "not_applicable"
        applicability_status = "not_applicable"
    elif status in {"needs_adjudication", "unresolved"}:
        review_status = "needs_reviewer_resolution"
        applicability_status = "needs_reviewer_resolution"
    else:
        review_status = None
        applicability_status = None
    source_ids = _strings(decision.get("source_record_ids"))
    document_role = str(decision.get("authority_document_role") or "").strip() or None
    package_evidence = _decision_package_evidence(decision)
    source_evidence = _decision_source_evidence(decision, document_role)
    return {
        "rule_id": rule_id,
        "status": review_status,
        "applicability_status": applicability_status,
        "applicability_mode": "conditional",
        "authority_source_record_id": source_ids[0] if source_ids else None,
        "authority_document_role": document_role,
        "package_evidence": package_evidence,
        "applicability_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "source_evidence": source_evidence,
        "applied_source_record_ids": source_ids,
        "applied_source_document_roles": [document_role] if document_role else [],
        "citation_requirements_met": bool(
            applicability_status == "not_applicable" or (package_evidence and source_evidence)
        ),
    }


def _augment_with_decision_evidence(
    finding: dict[str, Any] | None,
    row: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    surrogate = _decision_surrogate(decision)
    if not surrogate:
        return finding, row
    package_evidence = surrogate.get("package_evidence")
    source_evidence = surrogate.get("source_library_evidence")
    if not package_evidence and not source_evidence:
        return finding, row
    if isinstance(finding, dict):
        finding = dict(finding)
        if package_evidence:
            finding["applicability_decision_evidence"] = package_evidence
        if source_evidence:
            finding["applicability_decision_source_evidence"] = source_evidence
    if isinstance(row, dict):
        row = dict(row)
        if package_evidence:
            row["applicability_decision_evidence"] = package_evidence
        if source_evidence:
            row["applicability_decision_source_evidence"] = source_evidence
    return finding, row


def _decision_package_evidence(decision: dict[str, Any]) -> dict[str, Any] | None:
    spans = decision.get("package_evidence_spans") or decision.get("negative_evidence_spans") or []
    span = next((item for item in spans if isinstance(item, dict)), None)
    if not span:
        return None
    text = str(span.get("text_snippet") or span.get("text_excerpt") or "").strip()
    section = span.get("section_family")
    return {
        "citation_label": span.get("citation_label"),
        "title": span.get("title"),
        "chunk_id": _first_string(span.get("package_chunk_ids")),
        "text": text,
        "section": section,
        "heading": span.get("heading"),
        "evidence_span": {"text": text},
        "provenance": {
            "section": section,
            "heading": span.get("heading"),
            "page": span.get("page_label"),
        },
    }


def _decision_source_evidence(
    decision: dict[str, Any],
    document_role: str | None,
) -> dict[str, Any] | None:
    spans = decision.get("source_library_evidence_spans") or []
    span = next((item for item in spans if isinstance(item, dict)), None)
    source_ids = _strings(decision.get("source_record_ids"))
    if not span and not source_ids:
        return None
    text = str((span or {}).get("text_excerpt") or "").strip()
    source_record_id = (span or {}).get("source_record_id") or (source_ids[0] if source_ids else None)
    return {
        "citation_label": (span or {}).get("citation_label"),
        "source_record_id": source_record_id,
        "document_role": document_role,
        "title": (span or {}).get("title") or source_record_id,
        "text": text,
        "evidence_span": {"text": text},
        "provenance": {"page": (span or {}).get("page_label")},
    }


def _forest_plan_rule_bridge_index(
    *,
    contract: dict[str, Any],
    artifacts: dict[str, Any],
    section_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not contract.get("forest_plan"):
        return {}
    summary = artifacts.get("forest_plan_context_summary")
    context = artifacts.get("forest_plan_context")
    if not isinstance(summary, dict) or not isinstance(context, dict):
        return {}
    if not (
        summary.get("reviewer_ready")
        or _nested_get(summary, ["component_evaluation", "reviewer_ready"])
    ):
        return {}
    forest_source_ids = _forest_source_record_ids(summary, context)
    if not forest_source_ids:
        return {}
    bridge: dict[str, dict[str, Any]] = {}
    expectations = [
        *contract.get("rule_review_expectations", []),
        *contract.get("conditional_source_expectations", []),
    ]
    for expectation in expectations:
        rule_id = str(expectation.get("rule_id") or "").strip()
        if not rule_id or rule_id in bridge:
            continue
        expected_sources = {
            str(value)
            for value in expectation.get("expected_source_record_ids", [])
            if str(value).strip()
        }
        expected_roles = {
            str(value)
            for value in expectation.get("expected_source_document_roles", [])
            if str(value).strip()
        }
        if "forest_plan" not in expected_roles and not any(
            source_id.startswith("R1PLAN-") for source_id in expected_sources
        ):
            continue
        matched_sources = sorted(expected_sources & forest_source_ids)
        if expected_sources and not matched_sources:
            continue
        expected_sections = [
            str(section)
            for section in expectation.get("expected_package_section_ids", [])
            if str(section).strip()
        ]
        if expected_sections and not _expected_sections_detected(
            expected_sections,
            section_results,
            str(expectation.get("section_match") or "all"),
        ):
            continue
        source_ids = matched_sources or sorted(forest_source_ids)
        bridge[rule_id] = _forest_plan_bridge_row(
            rule_id=rule_id,
            source_ids=source_ids,
            expected_sections=expected_sections,
            section_results=section_results,
        )
    return bridge


def _expected_sections_detected(
    expected_sections: list[str],
    section_results: list[dict[str, Any]],
    match_mode: str,
) -> bool:
    detected = {
        str(result.get("section_id"))
        for result in section_results
        if result.get("detected")
    }
    if match_mode == "any":
        return bool(set(expected_sections) & detected)
    return set(expected_sections).issubset(detected)


def _forest_plan_bridge_row(
    *,
    rule_id: str,
    source_ids: list[str],
    expected_sections: list[str],
    section_results: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_text = _forest_plan_bridge_evidence_text(expected_sections, section_results)
    package_evidence = {
        "citation_label": "forest-plan-lane",
        "title": "Forest plan component review",
        "text": evidence_text,
        "section": "Forest Plan Consistency",
        "evidence_span": {"text": evidence_text},
        "provenance": {"section": "Forest Plan Consistency"},
    }
    source_record_id = source_ids[0] if source_ids else None
    source_evidence = {
        "citation_label": source_record_id,
        "source_record_id": source_record_id,
        "document_role": "forest_plan",
        "title": source_record_id,
        "text": "Forest plan source was validated by the forest-plan component lane.",
        "evidence_span": {
            "text": "Forest plan source was validated by the forest-plan component lane."
        },
        "provenance": {},
    }
    return {
        "rule_id": rule_id,
        "status": "pass",
        "applicability_status": "applicable",
        "applicability_mode": "conditional",
        "authority_source_record_id": source_record_id,
        "authority_document_role": "forest_plan",
        "package_evidence": package_evidence,
        "applicability_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "source_evidence": source_evidence,
        "applied_source_record_ids": source_ids,
        "applied_source_document_roles": ["forest_plan"],
        "citation_requirements_met": True,
    }


def _forest_plan_bridge_evidence_text(
    expected_sections: list[str],
    section_results: list[dict[str, Any]],
) -> str:
    chunks = []
    for result in section_results:
        if expected_sections and result.get("section_id") not in expected_sections:
            continue
        if not result.get("detected"):
            continue
        for chunk in result.get("matched_chunks", []):
            chunks.append(
                " ".join(
                    str(value)
                    for value in (
                        result.get("label"),
                        chunk.get("title"),
                        chunk.get("section"),
                        chunk.get("heading"),
                        " ".join(chunk.get("matched_terms", [])),
                    )
                    if value
                )
            )
    text = " ".join(chunk for chunk in chunks if chunk).strip()
    return text or "Forest Plan Consistency Land Management Plan"


def _actual_package_section_ids(
    finding: dict[str, Any],
    row: dict[str, Any],
    section_results: list[dict[str, Any]],
) -> list[str]:
    section_defs = [
        {
            "section_id": result["section_id"],
            "terms": sorted(
                set(result.get("matched_terms", []))
                | {str(result["label"]), str(result["section_id"]).replace("_", " ")}
            ),
        }
        for result in section_results
    ]
    texts = [
        _evidence_text(finding.get("package_evidence")),
        _evidence_text(finding.get("applicability_evidence")),
        _evidence_text(finding.get("applicability_decision_evidence")),
        _evidence_text(row.get("ea_package_evidence")),
        _evidence_text(row.get("applicability_decision_evidence")),
        _evidence_text(_nested_get(row, ["applicability_basis", "applicability_evidence"])),
    ]
    matches = set()
    for text in texts:
        if not text:
            continue
        normalized = _normalize(text)
        for section_def in section_defs:
            terms = [term for term in section_def["terms"] if term]
            if _matched_terms(normalized, terms):
                matches.add(section_def["section_id"])
    return sorted(matches)


def _actual_source_record_ids(finding: dict[str, Any], row: dict[str, Any]) -> list[str]:
    values = set(str(value) for value in row.get("applied_source_record_ids", []) if value)
    for key in ("source_library_evidence", "source_evidence"):
        evidence = finding.get(key) or row.get(key) or {}
        if evidence.get("source_record_id"):
            values.add(str(evidence["source_record_id"]))
    for key in ("source_claim_links", "source_claims"):
        for link in finding.get(key, []) or []:
            if link.get("source_record_id"):
                values.add(str(link["source_record_id"]))
    compact = row.get("source_library_evidence") or {}
    if compact.get("source_record_id"):
        values.add(str(compact["source_record_id"]))
    return sorted(values)


def _actual_document_roles(finding: dict[str, Any], row: dict[str, Any]) -> list[str]:
    values = set(str(value) for value in row.get("applied_source_document_roles", []) if value)
    for key in ("source_library_evidence", "source_evidence"):
        evidence = finding.get(key) or row.get(key) or {}
        if evidence.get("document_role"):
            values.add(str(evidence["document_role"]))
    for key in ("source_claim_links", "source_claims"):
        for link in finding.get(key, []) or []:
            if link.get("document_role"):
                values.add(str(link["document_role"]))
    return sorted(values)


def _citation_requirements_met(finding: dict[str, Any], row: dict[str, Any]) -> bool:
    if row.get("citation_requirements_met") is not None:
        return bool(row["citation_requirements_met"])
    return bool(
        finding.get("package_evidence_citation")
        and finding.get("source_library_evidence_citation")
    )


def _actual_status(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> str | None:
    return (finding or {}).get("status") or (row or {}).get("status")


def _actual_applicability(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> str | None:
    explicit = (finding or {}).get("applicability_status") or (row or {}).get(
        "applicability_status"
    )
    if explicit:
        return str(explicit)
    status = _actual_status(finding, row)
    if not status:
        return None
    return "not_applicable" if status == "not_applicable" else "applicable"


def _is_actual_applicable(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> bool:
    status = _actual_status(finding, row)
    applicability = _actual_applicability(finding, row)
    if status is None and applicability is None:
        return False
    return status != "not_applicable" and applicability not in {
        "not_applicable",
        "needs_reviewer_resolution",
    }


def _identity_matches_contract(
    contract: dict[str, Any],
    identity: dict[str, Any],
    review_dir: Path,
) -> bool:
    if contract.get("review_id") and contract["review_id"] != identity.get("review_id", review_dir.name):
        return False
    if contract.get("source_set_id") and contract.get("source_set_id") != identity.get(
        "source_set_id"
    ):
        return False
    return _rule_pack_identity_matches(contract, identity)


def _rule_pack_identity_matches(contract: dict[str, Any], identity: dict[str, Any]) -> bool:
    contract_id = contract.get("rule_pack_id")
    contract_version = contract.get("rule_pack_version")
    if not contract_id and not contract_version:
        return True
    review_pairs = {
        (
            identity.get("rule_pack_id"),
            identity.get("rule_pack_version"),
        ),
        (
            identity.get("base_rule_pack_id"),
            identity.get("base_rule_pack_version"),
        ),
    }
    review_pairs = {(pack_id, version) for pack_id, version in review_pairs if pack_id or version}
    if contract_id and contract_version:
        return (contract_id, contract_version) in review_pairs
    if contract_id:
        return any(contract_id == pack_id for pack_id, _version in review_pairs)
    if contract_version:
        return any(contract_version == version for _pack_id, version in review_pairs)
    return True


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _first_string(value: Any) -> str | None:
    values = _strings(value)
    return values[0] if values else None


def _review_identity(
    compliance_review: dict[str, Any],
    generated_rule_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = compliance_review.get("summary") or {}
    rule_pack = compliance_review.get("rule_pack") or {}
    generated_rule_pack = generated_rule_pack or {}
    return {
        "review_id": compliance_review.get("review_id") or summary.get("review_id"),
        "source_set_id": compliance_review.get("source_set_id") or summary.get("source_set_id"),
        "rule_pack_id": compliance_review.get("rule_pack_id")
        or summary.get("rule_pack_id")
        or rule_pack.get("rule_pack_id")
        or generated_rule_pack.get("rule_pack_id"),
        "rule_pack_version": compliance_review.get("rule_pack_version")
        or summary.get("rule_pack_version")
        or rule_pack.get("version")
        or generated_rule_pack.get("version"),
        "base_rule_pack_id": compliance_review.get("base_rule_pack_id")
        or summary.get("base_rule_pack_id")
        or rule_pack.get("base_rule_pack_id")
        or generated_rule_pack.get("base_rule_pack_id"),
        "base_rule_pack_version": compliance_review.get("base_rule_pack_version")
        or summary.get("base_rule_pack_version")
        or rule_pack.get("base_rule_pack_version")
        or generated_rule_pack.get("base_rule_pack_version"),
    }


def _contract_identity(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        key: contract.get(key)
        for key in ("review_id", "source_set_id", "rule_pack_id", "rule_pack_version")
        if contract.get(key)
    }


def _expectation_terms(expectation: dict[str, Any]) -> list[str]:
    terms = []
    for key in ("expected_terms", "aliases", "trigger_terms"):
        terms.extend(str(value) for value in expectation.get(key, []) if value)
    return sorted(set(terms))


def _chunk_text(chunk: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in (
            chunk.get("title"),
            chunk.get("section"),
            chunk.get("heading"),
            chunk.get("text"),
        )
        if value
    )


def _evidence_text(evidence: Any) -> str:
    if not isinstance(evidence, dict):
        return ""
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    return " ".join(
        str(value)
        for value in (
            evidence.get("citation_label"),
            evidence.get("title"),
            evidence.get("section"),
            evidence.get("heading"),
            evidence.get("text"),
            span.get("text"),
            provenance.get("section"),
            provenance.get("heading"),
            provenance.get("title"),
        )
        if value
    )


def _matched_terms(text: str, terms: list[str]) -> set[str]:
    normalized = _normalize(text)
    return {term for term in terms if _normalize(term) in normalized}


def _normalize(value: str) -> str:
    return " ".join(str(value).lower().replace("_", " ").replace("-", " ").split())


def _collect_values_by_key(value: Any, keys: set[str]) -> set[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys and isinstance(child, (str, int)):
                values.add(str(child))
            values |= _collect_values_by_key(child, keys)
    elif isinstance(value, list):
        for child in value:
            values |= _collect_values_by_key(child, keys)
    return values


def _forest_source_record_ids(summary: dict[str, Any], context: dict[str, Any]) -> set[str]:
    values = _collect_values_by_key(summary, {"source_record_id"}) | _collect_values_by_key(
        context,
        {"source_record_id"},
    )
    for key in (
        "required_source_record_ids",
        "present_source_record_ids",
        "missing_source_record_ids",
    ):
        values |= _collect_list_values_by_key(summary, key)
        values |= _collect_list_values_by_key(context, key)
    return values


def _collect_list_values_by_key(value: Any, key_name: str) -> set[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == key_name and isinstance(child, list):
                values.update(str(item) for item in child if isinstance(item, (str, int)))
            else:
                values |= _collect_list_values_by_key(child, key_name)
    elif isinstance(value, list):
        for child in value:
            values |= _collect_list_values_by_key(child, key_name)
    return values


def _applicable_standard_ids(
    standard_coverage: dict[str, Any],
    component_findings: dict[str, Any],
) -> set[str]:
    values: set[str] = set()
    rows = standard_coverage.get("standards") or standard_coverage.get("rows") or []
    for row in rows:
        if not isinstance(row, dict):
            continue
        applied = row.get("standard_applied") or row.get("applied")
        applicable = row.get("applicability_status") == "applicable" or applied
        if applicable:
            for key in ("standard_id", "component_id", "entry_id"):
                if row.get(key):
                    values.add(str(row[key]))
    for finding in component_findings.get("findings", []):
        if not isinstance(finding, dict):
            continue
        applicable = finding.get("applicability_status") == "applicable"
        is_standard = finding.get("component_type") == "standard" or finding.get("standard_id")
        if applicable and is_standard:
            for key in ("standard_id", "component_id", "entry_id"):
                if finding.get(key):
                    values.add(str(finding[key]))
    return values


def _forest_plan_compliance_matrix_details(compliance_matrix: dict[str, Any]) -> dict[str, Any]:
    section = compliance_matrix.get("forest_plan_compliance") or {}
    summary = section.get("summary") or {}
    rows = section.get("rows") or []
    applicable_standard_rows = [
        row
        for row in rows
        if row.get("component_type") == "standard"
        and row.get("applicability_status") == "applicable"
    ]
    return {
        "section_present": bool(section),
        "schema_version": section.get("schema_version"),
        "row_count": int(summary.get("row_count") or len(rows)),
        "applicable_standard_row_count": int(
            summary.get("applicable_standard_row_count")
            or len(applicable_standard_rows)
        ),
        "compliance_status_counts": summary.get("compliance_status_counts", {}),
        "load_errors": summary.get("load_errors", []),
    }


def _reviewer_resolution_count(queue: dict[str, Any]) -> int:
    summary = queue.get("summary") or {}
    for key in ("item_count", "open_item_count", "reviewer_resolution_count"):
        if summary.get(key) is not None:
            return int(summary[key])
        if queue.get(key) is not None:
            return int(queue[key])
    items = _reviewer_resolution_items(queue)
    return len(items) if isinstance(items, list) else 0


def _reviewer_resolution_count_by_component_type(queue: dict[str, Any], component_type: str) -> int:
    return sum(
        1
        for item in _reviewer_resolution_items(queue)
        if str(item.get("component_type") or "") == component_type
    )


def _reviewer_resolution_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    items = queue.get("items") or queue.get("queue") or []
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _pending_reviewer_resolution_count(artifacts: dict[str, Any]) -> int:
    item_results = _forest_plan_component_adjudication_item_results(artifacts)
    if item_results:
        return sum(
            1 for item in item_results if str(item.get("disposition") or "") == "pending"
        )
    component_adjudication = _forest_plan_component_adjudication_summary(artifacts)
    pending_count = component_adjudication.get("pending_adjudication_count")
    if pending_count is not None:
        return int(pending_count)
    if component_adjudication.get("reviewer_ready") is True:
        return 0
    return _reviewer_resolution_count(artifacts["forest_plan_reviewer_resolution_queue"])


def _pending_standard_reviewer_resolution_count(artifacts: dict[str, Any]) -> int:
    item_results = _forest_plan_component_adjudication_item_results(artifacts)
    if item_results:
        return sum(
            1
            for item in item_results
            if str(item.get("disposition") or "") == "pending"
            and str(item.get("component_type") or "") == "standard"
        )
    component_adjudication = _forest_plan_component_adjudication_summary(artifacts)
    pending_count = component_adjudication.get("pending_adjudication_count")
    if pending_count is not None and int(pending_count) == 0:
        return 0
    if component_adjudication.get("reviewer_ready") is True:
        return 0
    return _reviewer_resolution_count_by_component_type(
        artifacts["forest_plan_reviewer_resolution_queue"],
        "standard",
    )


def _forest_plan_component_adjudication_summary(artifacts: dict[str, Any]) -> dict[str, Any]:
    summary = _nested_get(artifacts["forest_plan_context_summary"], ["component_adjudication"])
    context_summary = summary if isinstance(summary, dict) else {}
    report = artifacts.get("forest_plan_component_adjudication_eval")
    if isinstance(report, dict):
        report_summary = report.get("summary")
        if isinstance(report_summary, dict):
            return {**context_summary, **report_summary}
    return context_summary


def _forest_plan_component_adjudication_item_results(
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    report = artifacts.get("forest_plan_component_adjudication_eval")
    if not isinstance(report, dict):
        return []
    items = report.get("item_results")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _nested_get(value: dict[str, Any], path: list[str]) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _check_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "count": len(results),
        "passed_count": sum(1 for result in results if result.get("passed")),
        "failed_count": sum(1 for result in results if not result.get("passed")),
    }


def _category_count(results: list[dict[str, Any]], category: str) -> int:
    return sum(1 for result in results if category in result.get("failure_categories", []))


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
