from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import hashlib


DECISION_EVIDENCE_FIELDS = (
    "package_evidence_spans",
    "negative_evidence_spans",
    "explicit_trigger_miss_evidence",
    "source_library_evidence_spans",
    "search_coverage_certificate_ids",
    "selected_retrieval_result_ids",
    "selected_graph_path_ids",
    "human_adjudication_refs",
)


def score_case_trajectory(
    *,
    review_dir: Path,
    retrieval_index_path: Path,
    artifacts: dict[str, Any],
    validation_summary: dict[str, Any],
    generated_summary: dict[str, Any] | None,
    generated_error: str | None,
    expected_generated_ready: bool,
) -> dict[str, Any]:
    """Score the deterministic applicability artifact trajectory for one eval case."""

    applicability_dir = review_dir / "applicability"
    validation_passed = bool(validation_summary.get("passed"))
    generated_present = bool(artifacts.get("generated_rule_pack")) or bool(
        artifacts.get("generated_validation")
    )
    generated_required = validation_passed and expected_generated_ready
    steps = _trajectory_steps(
        applicability_dir=applicability_dir,
        retrieval_index_path=retrieval_index_path,
        generated_required=generated_required,
    )
    missing_required_step_ids = [
        str(step["step_id"])
        for step in steps
        if step["required"] and step["status"] != "completed"
    ]
    invalid_transitions = _invalid_transitions(
        artifacts=artifacts,
        validation_passed=validation_passed,
        generated_required=generated_required,
        generated_present=generated_present,
        generated_summary=generated_summary,
        generated_error=generated_error,
    )
    no_evidence_decision_gaps = _no_evidence_decision_gaps(artifacts.get("decisions") or [])
    retry_without_new_evidence = _retry_without_new_evidence(steps)
    first_bad_step_id = (
        missing_required_step_ids[0]
        if missing_required_step_ids
        else (
            str(invalid_transitions[0]["step_id"])
            if invalid_transitions
            else (
                str(no_evidence_decision_gaps[0]["step_id"])
                if no_evidence_decision_gaps
                else None
            )
        )
    )
    error_propagation_class = _error_propagation_class(
        validation_passed=validation_passed,
        expected_generated_ready=expected_generated_ready,
        generated_present=generated_present,
        generated_error=generated_error,
    )
    required_step_count = sum(1 for step in steps if step["required"])
    completed_required_step_count = sum(
        1 for step in steps if step["required"] and step["status"] == "completed"
    )
    passed = not (
        missing_required_step_ids
        or invalid_transitions
        or no_evidence_decision_gaps
        or retry_without_new_evidence
    )
    return {
        "status": "direct_eval_present",
        "passed": passed,
        "steps": steps,
        "required_step_count": required_step_count,
        "completed_required_step_count": completed_required_step_count,
        "missing_required_step_ids": missing_required_step_ids,
        "invalid_transition_count": len(invalid_transitions),
        "invalid_transitions": invalid_transitions,
        "retry_without_new_evidence_count": len(retry_without_new_evidence),
        "retry_without_new_evidence": retry_without_new_evidence,
        "no_evidence_decision_gap_count": len(no_evidence_decision_gaps),
        "no_evidence_decision_gaps": no_evidence_decision_gaps,
        "first_bad_step_id": first_bad_step_id,
        "error_propagation_class": error_propagation_class,
    }


def trajectory_process_metric_group(
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    qualities = [
        case.get("trajectory_process_quality")
        for case in case_results
        if isinstance(case.get("trajectory_process_quality"), dict)
    ]
    error_classes = Counter(
        str(quality.get("error_propagation_class") or "not_recorded")
        for quality in qualities
    )
    missing_required_step_count = sum(
        len(quality.get("missing_required_step_ids") or []) for quality in qualities
    )
    invalid_transition_count = sum(
        int(quality.get("invalid_transition_count") or 0) for quality in qualities
    )
    retry_without_new_evidence_count = sum(
        int(quality.get("retry_without_new_evidence_count") or 0)
        for quality in qualities
    )
    no_evidence_decision_gap_count = sum(
        int(quality.get("no_evidence_decision_gap_count") or 0) for quality in qualities
    )
    required_step_count = sum(
        int(quality.get("required_step_count") or 0) for quality in qualities
    )
    completed_required_step_count = sum(
        int(quality.get("completed_required_step_count") or 0) for quality in qualities
    )
    passed_case_count = sum(1 for quality in qualities if quality.get("passed"))
    failure_categories = {
        category: count
        for category, count in {
            "trajectory_required_step_missing": missing_required_step_count,
            "trajectory_invalid_transition": invalid_transition_count,
            "trajectory_retry_without_new_evidence": retry_without_new_evidence_count,
            "trajectory_no_evidence_decision": no_evidence_decision_gap_count,
        }.items()
        if count
    }
    return {
        "status": "direct_eval_present",
        "blocking": True,
        "passed": bool(case_results)
        and len(qualities) == len(case_results)
        and passed_case_count == len(case_results),
        "metrics": {
            "trajectory_case_count": len(qualities),
            "passed_case_count": passed_case_count,
            "required_step_count": required_step_count,
            "completed_required_step_count": completed_required_step_count,
            "required_step_completion_rate": (
                completed_required_step_count / required_step_count
                if required_step_count
                else 0.0
            ),
            "missing_required_step_count": missing_required_step_count,
            "invalid_transition_count": invalid_transition_count,
            "retry_without_new_evidence_count": retry_without_new_evidence_count,
            "no_evidence_decision_gap_count": no_evidence_decision_gap_count,
            "first_bad_step_case_count": sum(
                1 for quality in qualities if quality.get("first_bad_step_id")
            ),
            "error_propagation_classes": dict(sorted(error_classes.items())),
        },
        "failure_category_counts": failure_categories,
    }


def _trajectory_steps(
    *,
    applicability_dir: Path,
    retrieval_index_path: Path,
    generated_required: bool,
) -> list[dict[str, Any]]:
    specs = [
        ("source_index", [retrieval_index_path], True),
        (
            "authority_universe",
            [applicability_dir / "authority_universe_snapshot.json"],
            True,
        ),
        ("package_fact_graph", [applicability_dir / "package_fact_graph.json"], True),
        (
            "retrieval_trace",
            [applicability_dir / "applicability_retrieval_trace.jsonl"],
            True,
        ),
        (
            "graph_trace",
            [applicability_dir / "applicability_graph_trace.jsonl"],
            True,
        ),
        (
            "decision_ledger",
            [applicability_dir / "applicability_decisions.jsonl"],
            True,
        ),
        (
            "decision_partitions",
            [
                applicability_dir / "applicable_authorities.json",
                applicability_dir / "non_applicable_authorities.json",
                applicability_dir / "search_coverage_certificates.json",
            ],
            True,
        ),
        (
            "gate_graph",
            [
                applicability_dir / "applicability_gate_graph.json",
                applicability_dir / "applicability_gate_graph_summary.json",
                applicability_dir / "applicability_gate_graph_validation.json",
            ],
            True,
        ),
        (
            "applicability_validation",
            [applicability_dir / "applicability_validation.json"],
            True,
        ),
        (
            "generated_rule_pack",
            [
                applicability_dir / "generated_rule_pack.json",
                applicability_dir / "generated_rule_pack_validation.json",
            ],
            generated_required,
        ),
    ]
    return [
        _step_payload(index=index, step_id=step_id, paths=paths, required=required)
        for index, (step_id, paths, required) in enumerate(specs, start=1)
    ]


def _step_payload(
    *,
    index: int,
    step_id: str,
    paths: list[Path],
    required: bool,
) -> dict[str, Any]:
    artifact_paths = [str(path) for path in paths]
    artifact_hashes = {
        str(path): _sha256_file(path) for path in paths if path.exists() and path.is_file()
    }
    complete = all(path.exists() and path.is_file() for path in paths)
    return {
        "order": index,
        "step_id": step_id,
        "required": required,
        "status": (
            "completed"
            if complete
            else ("missing" if required else "skipped")
        ),
        "artifact_paths": artifact_paths,
        "artifact_sha256": artifact_hashes,
    }


def _invalid_transitions(
    *,
    artifacts: dict[str, Any],
    validation_passed: bool,
    generated_required: bool,
    generated_present: bool,
    generated_summary: dict[str, Any] | None,
    generated_error: str | None,
) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    decisions = artifacts.get("decisions") or []
    retrieval_rows = artifacts.get("retrieval_rows") or []
    graph_rows = artifacts.get("graph_rows") or []
    generated_validation = artifacts.get("generated_validation") or {}
    if decisions and not retrieval_rows:
        transitions.append(
            {
                "step_id": "decision_ledger",
                "reason": "decisions_without_retrieval_trace",
            }
        )
    if graph_rows and not retrieval_rows:
        transitions.append(
            {
                "step_id": "graph_trace",
                "reason": "graph_trace_without_retrieval_trace",
            }
        )
    if validation_passed and not decisions:
        transitions.append(
            {
                "step_id": "applicability_validation",
                "reason": "validation_passed_without_decisions",
            }
        )
    if generated_present and not validation_passed:
        transitions.append(
            {
                "step_id": "generated_rule_pack",
                "reason": "generated_pack_after_failed_validation",
            }
        )
    if generated_required and not generated_present:
        transitions.append(
            {
                "step_id": "generated_rule_pack",
                "reason": "generated_pack_missing_after_passed_validation",
            }
        )
    if validation_passed and generated_error:
        transitions.append(
            {
                "step_id": "generated_rule_pack",
                "reason": "generated_pack_error_after_passed_validation",
                "error": generated_error,
            }
        )
    if generated_validation and not artifacts.get("generated_rule_pack"):
        transitions.append(
            {
                "step_id": "generated_rule_pack",
                "reason": "generated_validation_without_rule_pack",
            }
        )
    if generated_summary and not generated_validation:
        transitions.append(
            {
                "step_id": "generated_rule_pack",
                "reason": "generated_summary_without_validation_artifact",
            }
        )
    return transitions


def _no_evidence_decision_gaps(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        status = str(decision.get("status") or "")
        basis_type = str(decision.get("basis_type") or "")
        if status not in {
            "applicable",
            "not_applicable",
            "needs_adjudication",
            "unresolved",
        }:
            continue
        if basis_type == "mandatory_baseline":
            continue
        if _decision_has_evidence(decision):
            continue
        gaps.append(
            {
                "step_id": "decision_ledger",
                "reason": "decision_without_evidence",
                "candidate_authority_id": decision.get("candidate_authority_id"),
                "status": status,
                "basis_type": basis_type,
            }
        )
    return gaps


def _decision_has_evidence(decision: dict[str, Any]) -> bool:
    for field in DECISION_EVIDENCE_FIELDS:
        if decision.get(field):
            return True
    summary = decision.get("arbitration_summary")
    if isinstance(summary, dict):
        for field in ("retrieval_trace_ids", "graph_path_ids"):
            if summary.get(field):
                return True
    return bool(decision.get("source_record_ids"))


def _retry_without_new_evidence(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    retries = []
    for step in steps:
        step_id = str(step.get("step_id") or "")
        if step_id not in seen:
            seen[step_id] = step
            continue
        if step.get("artifact_sha256") == seen[step_id].get("artifact_sha256"):
            retries.append(
                {
                    "step_id": step_id,
                    "reason": "retry_without_new_artifact_hash",
                }
            )
    return retries


def _error_propagation_class(
    *,
    validation_passed: bool,
    expected_generated_ready: bool,
    generated_present: bool,
    generated_error: str | None,
) -> str:
    if generated_error:
        return "generated_pack_error"
    if validation_passed and expected_generated_ready and generated_present:
        return "validation_passed_generated_pack_written"
    if validation_passed and not expected_generated_ready and generated_present:
        return "validation_passed_generated_pack_optional"
    if validation_passed and not expected_generated_ready and not generated_present:
        return "validation_passed_generation_not_expected"
    if not validation_passed and not generated_present:
        return "validation_failed_generated_pack_skipped"
    if not validation_passed and generated_present:
        return "validation_failed_generated_pack_present"
    return "not_classified"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
