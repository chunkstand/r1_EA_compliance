from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any


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
    eval_file: Path = DEFAULT_V1_EA_EVAL_PATH,
    output_path: Path | None = None,
) -> V1EAReviewEvalResult:
    """Evaluate a real EA compliance review against the V1 adjudication contract."""

    contract = _read_json(eval_file)
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
        section_results=section_results,
    )
    conditional_results = _evaluate_conditional_expectations(
        conditional_expectations=contract.get("conditional_source_expectations", []),
        finding_index=finding_index,
        matrix_index=matrix_index,
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
    passed = all(check["passed"] for check in checks)

    summary = {
        "schema_version": V1_EA_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "review_id": _review_identity(artifacts["compliance_review"]).get("review_id")
        or resolved_review_dir.name,
        "review_dir": str(resolved_review_dir),
        "eval_file": str(eval_file),
        "output_path": str(resolved_output_path),
        "generated_at": _utc_now(),
        "passed": passed,
        "broader_ea_passed": eval_lanes["broader_ea"]["passed"],
        "forest_plan_passed": eval_lanes["forest_plan"]["passed"],
        "forest_plan_component_adjudication_required": eval_lanes["forest_plan"][
            "component_adjudication_required"
        ],
        "checks": checks,
        "metrics": metrics,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "broader_ea_failure_category_counts": dict(
            sorted(broader_ea_failure_category_counts.items())
        ),
        "forest_plan_failure_category_counts": dict(
            sorted(forest_plan_failure_category_counts.items())
        ),
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
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return V1EAReviewEvalResult(
        eval_file=eval_file,
        review_dir=resolved_review_dir,
        output_path=resolved_output_path,
        summary=summary,
    )


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
    section_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for expectation in rule_expectations:
        rule_id = str(expectation["rule_id"])
        result = _evaluate_rule_source_section(
            expectation=expectation,
            finding=finding_index.get(rule_id),
            row=matrix_index.get(rule_id),
            section_results=section_results,
        )
        results.append(result)
    return results


def _evaluate_conditional_expectations(
    *,
    conditional_expectations: list[dict[str, Any]],
    finding_index: dict[str, dict[str, Any]],
    matrix_index: dict[str, dict[str, Any]],
    section_results: list[dict[str, Any]],
    allow_unadjudicated: bool,
) -> list[dict[str, Any]]:
    results = []
    expected_rule_ids = {str(expectation["rule_id"]) for expectation in conditional_expectations}
    for expectation in conditional_expectations:
        rule_id = str(expectation["rule_id"])
        expected = str(expectation["expected_applicability"])
        finding = finding_index.get(rule_id)
        row = matrix_index.get(rule_id)
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
    accepted_pending_rule_ids = sorted(
        str(rule_id)
        for rule_id in policy.get("accepted_pending_rule_ids", [])
        if str(rule_id).strip()
    )
    accepted_pending_count = policy.get("accepted_pending_count")
    mode = str(policy.get("mode") or "").strip()
    failure_reasons = []
    if pending_results and not policy_present:
        failure_reasons.append("missing_conditional_adjudication_policy")
    if policy_present and mode != "accepted_pending_v1":
        failure_reasons.append("unsupported_conditional_adjudication_policy_mode")
    if policy_present and not isinstance(policy.get("accepted_pending_rule_ids"), list):
        failure_reasons.append("accepted_pending_rule_ids_must_be_list")
    if policy_present and accepted_pending_count != len(actual_pending_rule_ids):
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
    queue = artifacts["forest_plan_reviewer_resolution_queue"]
    source_record_ids = _forest_source_record_ids(summary, context)
    geo_ids = _collect_values_by_key(context, {"geographic_area_id", "entry_id", "area_id"})
    management_ids = _collect_values_by_key(context, {"management_area_id", "entry_id"})
    overlay_ids = _collect_values_by_key(context, {"overlay_id", "entry_id"})
    component_ids = _collect_values_by_key(
        component_findings,
        {"component_id", "standard_id", "entry_id"},
    )
    applicable_standard_ids = _applicable_standard_ids(standard_coverage, component_findings)
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
        actual_count = _reviewer_resolution_count(queue)
        add_result(
            expectation_id="reviewer_resolution_item_count",
            expected={"max": maximum},
            actual=actual_count,
            passed=actual_count <= maximum,
            failure_category="forest_plan_reviewer_resolution_open",
        )
    if expectations.get("max_standard_reviewer_resolution_items") is not None:
        maximum = int(expectations["max_standard_reviewer_resolution_items"])
        actual_count = _reviewer_resolution_count_by_component_type(queue, "standard")
        add_result(
            expectation_id="standard_reviewer_resolution_item_count",
            expected={"max": maximum},
            actual=actual_count,
            passed=actual_count <= maximum,
            failure_category="forest_plan_standard_reviewer_resolution_open",
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
    identity = _review_identity(artifacts["compliance_review"])
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
        "reviewer_resolution_item_count": _reviewer_resolution_count(
            artifacts["forest_plan_reviewer_resolution_queue"]
        ),
        "standard_reviewer_resolution_item_count": _reviewer_resolution_count_by_component_type(
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

    reviewer_resolution_count = _reviewer_resolution_count(
        artifacts["forest_plan_reviewer_resolution_queue"]
    )
    standard_reviewer_resolution_count = _reviewer_resolution_count_by_component_type(
        artifacts["forest_plan_reviewer_resolution_queue"],
        "standard",
    )
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
            "pending_component_adjudication_count": reviewer_resolution_count,
            "pending_standard_adjudication_count": standard_reviewer_resolution_count,
            "component_adjudication_required": reviewer_resolution_count > 0,
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
        accepted_rule_ids = sorted(
            str(rule_id)
            for rule_id in policy.get("accepted_pending_rule_ids", [])
            if str(rule_id).strip()
        )
        if accepted_rule_ids != adjudicate_rule_ids:
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must match "
                "adjudicate conditional expectations"
            )
        if policy.get("accepted_pending_count") != len(adjudicate_rule_ids):
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
        _evidence_text(row.get("ea_package_evidence")),
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
    return (
        (finding or {}).get("applicability_status")
        or (row or {}).get("applicability_status")
        or ("not_applicable" if _actual_status(finding, row) == "not_applicable" else "applicable")
    )


def _is_actual_applicable(finding: dict[str, Any] | None, row: dict[str, Any] | None) -> bool:
    status = _actual_status(finding, row)
    applicability = _actual_applicability(finding, row)
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
    for key in ("source_set_id", "rule_pack_id", "rule_pack_version"):
        if contract.get(key) and contract.get(key) != identity.get(key):
            return False
    return True


def _review_identity(compliance_review: dict[str, Any]) -> dict[str, Any]:
    summary = compliance_review.get("summary") or {}
    return {
        "review_id": compliance_review.get("review_id") or summary.get("review_id"),
        "source_set_id": compliance_review.get("source_set_id") or summary.get("source_set_id"),
        "rule_pack_id": compliance_review.get("rule_pack_id") or summary.get("rule_pack_id"),
        "rule_pack_version": compliance_review.get("rule_pack_version")
        or summary.get("rule_pack_version"),
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
