from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any
import json


REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION = "real-package-review-coverage-v1"
REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION = "real-package-review-coverage-results-v1"
DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH = Path(
    "config/v1_real_package_review_coverage_v1.json"
)
EXPECTED_CONTRACT_STATUSES = {"reviewer_ready", "typed_blocked"}
RUNTIME_FOREST_SCOPE_REQUIRED_COVERAGE_CLASS_IDS = {
    "current_promotion_reviewer_ready",
    "forest_specific_reviewer_ready",
}
PHASE_EVAL_REQUIRED_CONTRACT_STATUSES = {"reviewer_ready"}
PHASE_EVAL_SELF_REFERENCE_PHASE_NAMES = {
    "evaluation_coverage",
    "final_qa_certification_report",
    "first_class_eval_trace",
}
DECISION_DOCUMENT_IDENTITY_REQUIRED_CONTRACT_STATUSES = {"reviewer_ready"}


@dataclass(frozen=True)
class RealPackageReviewCoverageEvalResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def resolve_real_package_review_eval_file(
    *,
    review_id: str,
    manifest_path: Path = DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
) -> Path:
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    slot = _slot_by_review_id(manifest, review_id)
    return _resolve_repo_path(str(slot["eval_file"]), manifest_path)


def run_real_package_review_coverage_eval(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> RealPackageReviewCoverageEvalResult:
    run_v1_ea_review_eval = import_module(
        "usfs_r1_ea_sources.v1_ea_eval"
    ).run_v1_ea_review_eval
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    results_output_dir = (
        Path(results_dir)
        if results_dir
        else output_dir / "reviews" / "real_package_review_coverage_eval"
    )
    output_path = results_output_dir / "real_package_review_coverage_eval_results.json"

    slot_results = [
        _slot_result(
            slot=slot,
            manifest_path=manifest_path,
            output_dir=output_dir,
            decision_document_identity_policy=manifest.get(
                "decision_document_identity_policy",
                {},
            ),
            run_v1_ea_review_eval=run_v1_ea_review_eval,
        )
        for slot in manifest.get("slots", [])
    ]
    required_slots = [slot for slot in slot_results if slot["required"]]
    required_coverage_class_ids = _string_list(manifest.get("required_coverage_class_ids"))
    covered_slots = [slot for slot in required_slots if slot["passed"]]
    covered_review_ids = sorted(slot["review_id"] for slot in covered_slots)
    covered_coverage_class_ids = sorted(slot["coverage_class_id"] for slot in covered_slots)
    reviewer_ready_slot_count = sum(
        1 for slot in required_slots if slot["actual_contract_status"] == "reviewer_ready"
    )
    typed_blocked_slot_count = sum(
        1 for slot in required_slots if slot["actual_contract_status"] == "typed_blocked"
    )
    distinct_forest_ids = sorted(
        {
            str(slot.get("forest_unit_id"))
            for slot in required_slots
            if str(slot.get("forest_unit_id") or "").strip()
        }
    )
    distinct_package_style_tags = sorted(
        {
            str(tag)
            for slot in required_slots
            for tag in slot.get("package_style_tags", [])
            if str(tag).strip()
        }
    )
    missing_package_authority_count = sum(
        1 for slot in required_slots if not slot["package_authority"]["passed"]
    )
    phase_eval_required_slot_count = sum(
        1 for slot in required_slots if slot["phase_eval_gate"]["required"]
    )
    phase_eval_ready_slot_count = sum(
        1
        for slot in required_slots
        if slot["phase_eval_gate"]["required"] and slot["phase_eval_gate"]["passed"]
    )
    missing_phase_eval_count = sum(
        1
        for slot in required_slots
        if "phase_eval_missing" in slot["phase_eval_gate"]["failure_reasons"]
    )
    failed_phase_eval_count = phase_eval_required_slot_count - phase_eval_ready_slot_count
    decision_identity_required_slot_count = sum(
        1 for slot in required_slots if slot["decision_document_identity_gate"]["required"]
    )
    decision_identity_ready_slot_count = sum(
        1
        for slot in required_slots
        if slot["decision_document_identity_gate"]["required"]
        and slot["decision_document_identity_gate"]["passed"]
    )
    missing_decision_identity_count = sum(
        1
        for slot in required_slots
        if "decision_document_identity_missing"
        in slot["decision_document_identity_gate"]["failure_reasons"]
    )
    failed_decision_identity_count = (
        decision_identity_required_slot_count - decision_identity_ready_slot_count
    )
    missing_required_slot_count = len(required_slots) - len(covered_slots)
    missing_coverage_class_ids = sorted(
        set(required_coverage_class_ids) - {slot["coverage_class_id"] for slot in covered_slots}
    )
    threshold_failures = _threshold_failures(
        thresholds=_int_dict(manifest.get("coverage_thresholds")),
        required_slot_count=len(required_slots),
        required_coverage_class_count=len(required_coverage_class_ids),
        distinct_forest_count=len(distinct_forest_ids),
        distinct_package_style_count=len(distinct_package_style_tags),
        reviewer_ready_slot_count=reviewer_ready_slot_count,
        typed_blocked_slot_count=typed_blocked_slot_count,
        missing_required_slot_count=missing_required_slot_count,
        missing_package_authority_count=missing_package_authority_count,
    )
    failure_category_counts = _failure_category_counts(
        slot_results=required_slots,
        threshold_failures=threshold_failures,
        missing_coverage_class_ids=missing_coverage_class_ids,
    )
    passed = all(slot["passed"] for slot in required_slots) and not threshold_failures
    summary = {
        "schema_version": REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(results_output_dir),
        "output_path": str(output_path),
        "real_package_review_coverage_id": manifest.get("id"),
        "real_package_review_coverage_version": manifest.get("version"),
        "phase_eval_policy": manifest.get("phase_eval_policy", {}),
        "decision_document_identity_policy": manifest.get(
            "decision_document_identity_policy",
            {},
        ),
        "passed": passed,
        "required_slot_count": len(required_slots),
        "covered_slot_count": len(covered_slots),
        "covered_review_ids": covered_review_ids,
        "required_coverage_class_ids": required_coverage_class_ids,
        "covered_coverage_class_ids": covered_coverage_class_ids,
        "missing_coverage_class_ids": missing_coverage_class_ids,
        "reviewer_ready_slot_count": reviewer_ready_slot_count,
        "typed_blocked_slot_count": typed_blocked_slot_count,
        "distinct_forest_count": len(distinct_forest_ids),
        "distinct_forest_ids": distinct_forest_ids,
        "distinct_package_style_count": len(distinct_package_style_tags),
        "distinct_package_style_tags": distinct_package_style_tags,
        "missing_required_slot_count": missing_required_slot_count,
        "missing_package_authority_count": missing_package_authority_count,
        "phase_eval_required_slot_count": phase_eval_required_slot_count,
        "phase_eval_ready_slot_count": phase_eval_ready_slot_count,
        "missing_phase_eval_count": missing_phase_eval_count,
        "failed_phase_eval_count": failed_phase_eval_count,
        "decision_document_identity_required_slot_count": (
            decision_identity_required_slot_count
        ),
        "decision_document_identity_ready_slot_count": decision_identity_ready_slot_count,
        "missing_decision_document_identity_count": missing_decision_identity_count,
        "failed_decision_document_identity_count": failed_decision_identity_count,
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "slots": slot_results,
    }
    results_output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RealPackageReviewCoverageEvalResult(
        manifest_path=manifest_path,
        output_dir=results_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _slot_result(
    *,
    slot: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
    decision_document_identity_policy: Any,
    run_v1_ea_review_eval: Any,
) -> dict[str, Any]:
    review_id = str(slot["review_id"]).strip()
    results_path = slot.get("results_path")
    eval_file = _resolve_repo_path(str(slot["eval_file"]), manifest_path)
    summary = (
        _load_summary(_resolve_repo_path(str(results_path), manifest_path))
        if results_path
        else run_v1_ea_review_eval(
            output_dir=output_dir,
            review_id=review_id,
            eval_file=eval_file,
        ).summary
    )
    contract_expectations = summary.get("contract_expectations", {})
    package_authority = _package_authority_result(
        authority_spec=slot.get("package_authority"),
        manifest_path=manifest_path,
    )
    actual_review_id = str(summary.get("review_id") or "").strip()
    actual_contract_status = str(summary.get("contract_status") or "mismatch").strip()
    expected_contract_status = str(slot["expected_contract_status"]).strip()
    coverage_class_id = str(slot["coverage_class_id"])
    missing_contract = actual_review_id != review_id
    contract_status_match = actual_contract_status == expected_contract_status
    forest_unit_id = str(summary.get("forest_unit_id") or slot.get("forest_unit_id") or "").strip()
    expected_forest_unit_id = str(slot.get("forest_unit_id") or "").strip()
    runtime_forest_scope_gate = _runtime_forest_scope_gate(
        coverage_class_id=coverage_class_id,
        expected_forest_unit_id=expected_forest_unit_id,
        summary=summary,
    )
    package_style_tags = _string_list(
        summary.get("package_style_tags") or slot.get("package_style_tags")
    )
    phase_eval_gate = _phase_eval_gate(
        slot=slot,
        manifest_path=manifest_path,
        output_dir=output_dir,
        review_id=review_id,
        expected_contract_status=expected_contract_status,
        summary=summary,
    )
    decision_document_identity_gate = _decision_document_identity_gate(
        slot=slot,
        manifest_path=manifest_path,
        output_dir=output_dir,
        review_id=review_id,
        coverage_class_id=coverage_class_id,
        expected_contract_status=expected_contract_status,
        expected_forest_unit_id=expected_forest_unit_id,
        expected_source_set_id=str(summary.get("source_set_id") or "").strip(),
        policy=decision_document_identity_policy,
    )
    expected_blocker_categories = _string_list(
        contract_expectations.get("allowed_blocker_categories")
        or summary.get("allowed_blocker_categories")
    )
    actual_blocker_categories = sorted(
        {
            *contract_expectations.get("matched_blocker_categories", []),
            *contract_expectations.get("unexpected_blocker_categories", []),
        }
    )
    unexpected_blocker_categories = _string_list(
        contract_expectations.get("unexpected_blocker_categories")
    )
    failure_reasons: list[str] = []
    if not bool(summary.get("passed")):
        failure_reasons.append("review_eval_failed")
    if missing_contract:
        failure_reasons.append("missing_required_review_contract")
    if not contract_status_match:
        failure_reasons.append("slot_contract_status_mismatch")
    if not package_authority["passed"]:
        failure_reasons.append("missing_package_authority")
    failure_reasons.extend(runtime_forest_scope_gate["failure_reasons"])
    failure_reasons.extend(phase_eval_gate["failure_reasons"])
    failure_reasons.extend(decision_document_identity_gate["failure_reasons"])
    return {
        "slot_id": str(slot["slot_id"]),
        "label": str(slot["label"]),
        "review_id": review_id,
        "actual_review_id": actual_review_id,
        "package_label": str(slot["package_label"]),
        "coverage_class_id": coverage_class_id,
        "required": bool(slot["required"]),
        "expected_contract_status": expected_contract_status,
        "contract_status": actual_contract_status,
        "actual_contract_status": actual_contract_status,
        "contract_status_match": contract_status_match,
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
        "actual_overall_passed": bool(summary.get("actual_overall_passed", summary.get("passed"))),
        "broader_ea_passed": bool(summary.get("broader_ea_passed")),
        "forest_plan_passed": bool(summary.get("forest_plan_passed")),
        "forest_unit_id": forest_unit_id,
        "expected_forest_unit_id": expected_forest_unit_id,
        "runtime_forest_scope_gate": runtime_forest_scope_gate,
        "phase_eval_gate": phase_eval_gate,
        "decision_document_identity_gate": decision_document_identity_gate,
        "package_style_tags": package_style_tags,
        "failure_category_counts": summary.get("failure_category_counts", {}),
        "forest_plan_failure_category_counts": summary.get(
            "forest_plan_failure_category_counts",
            {},
        ),
        "package_authority": package_authority,
        "missing_contract": missing_contract,
        "summary_path": str(results_path) if results_path else summary.get("output_path"),
        "eval_file": str(eval_file),
        "expected_blocker_categories": expected_blocker_categories,
        "actual_blocker_categories": actual_blocker_categories,
        "unexpected_blocker_categories": unexpected_blocker_categories,
    }


def _phase_eval_gate(
    *,
    slot: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
    review_id: str,
    expected_contract_status: str,
    summary: dict[str, Any],
) -> dict[str, Any]:
    required = expected_contract_status in PHASE_EVAL_REQUIRED_CONTRACT_STATUSES
    path_value = slot.get("phase_eval_results_path")
    phase_eval_path = (
        _resolve_repo_path(str(path_value), manifest_path)
        if path_value
        else output_dir / "reviews" / review_id / "phase_eval_results.json"
    )
    failure_reasons: list[str] = []
    payload: dict[str, Any] = {}
    path_exists = phase_eval_path.exists()

    if path_exists:
        try:
            loaded = _read_json(phase_eval_path)
            if isinstance(loaded, dict):
                payload = loaded
            else:
                failure_reasons.append("phase_eval_invalid_json")
        except (OSError, json.JSONDecodeError):
            failure_reasons.append("phase_eval_invalid_json")
    elif required:
        failure_reasons.append("phase_eval_missing")

    actual_review_id = str(payload.get("review_id") or "").strip()
    actual_source_set_id = str(payload.get("source_set_id") or "").strip()
    expected_source_set_id = str(summary.get("source_set_id") or "").strip()
    phase_blockers = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
    passed = bool(payload.get("passed"))
    reviewer_ready = bool(payload.get("reviewer_ready"))
    phase_count = _optional_int(payload.get("phase_count"))
    passed_phase_count = _optional_int(payload.get("passed_phase_count"))
    reviewer_ready_phase_count = _optional_int(payload.get("reviewer_ready_phase_count"))
    self_reference_allowed = _phase_eval_self_reference_allowed(payload)

    if required and payload:
        if actual_review_id != review_id:
            failure_reasons.append("phase_eval_review_id_mismatch")
        if expected_source_set_id and actual_source_set_id != expected_source_set_id:
            failure_reasons.append("phase_eval_source_set_mismatch")
        if not passed and not self_reference_allowed:
            failure_reasons.append("phase_eval_failed")
        if not reviewer_ready and not self_reference_allowed:
            failure_reasons.append("phase_eval_not_reviewer_ready")
        if phase_blockers and not self_reference_allowed:
            failure_reasons.append("phase_eval_blockers_present")
        if phase_count is not None:
            if phase_count <= 0:
                failure_reasons.append("phase_eval_phase_count_missing")
            if passed_phase_count != phase_count and not self_reference_allowed:
                failure_reasons.append("phase_eval_phase_count_mismatch")
            if reviewer_ready_phase_count != phase_count and not self_reference_allowed:
                failure_reasons.append("phase_eval_reviewer_ready_phase_count_mismatch")

    return {
        "required": required,
        "passed": not failure_reasons,
        "path": str(phase_eval_path),
        "path_exists": path_exists,
        "review_id": actual_review_id or None,
        "expected_review_id": review_id,
        "review_id_matches": (not required or actual_review_id == review_id),
        "source_set_id": actual_source_set_id or None,
        "expected_source_set_id": expected_source_set_id or None,
        "source_set_matches": (
            not required
            or not expected_source_set_id
            or actual_source_set_id == expected_source_set_id
        ),
        "phase_eval_passed": passed,
        "reviewer_ready": reviewer_ready,
        "phase_count": phase_count,
        "passed_phase_count": passed_phase_count,
        "reviewer_ready_phase_count": reviewer_ready_phase_count,
        "blocker_count": len(phase_blockers),
        "self_reference_allowed": self_reference_allowed,
        "self_reference_phase_names": _phase_eval_failed_phase_names(payload)
        if self_reference_allowed
        else [],
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _phase_eval_self_reference_allowed(payload: dict[str, Any]) -> bool:
    phases = payload.get("phases")
    if not isinstance(phases, list):
        return False
    failed_phase_names = _phase_eval_failed_phase_names(payload)
    if not failed_phase_names:
        return False
    if not set(failed_phase_names) <= PHASE_EVAL_SELF_REFERENCE_PHASE_NAMES:
        return False
    phase_count = _optional_int(payload.get("phase_count"))
    passed_phase_count = _optional_int(payload.get("passed_phase_count"))
    reviewer_ready_phase_count = _optional_int(payload.get("reviewer_ready_phase_count"))
    if phase_count is None or passed_phase_count is None or reviewer_ready_phase_count is None:
        return False
    expected_ready_count = phase_count - len(failed_phase_names)
    return passed_phase_count == expected_ready_count and reviewer_ready_phase_count == expected_ready_count


def _phase_eval_failed_phase_names(payload: dict[str, Any]) -> list[str]:
    phases = payload.get("phases")
    if not isinstance(phases, list):
        return []
    return sorted(
        str(phase.get("name"))
        for phase in phases
        if isinstance(phase, dict)
        and str(phase.get("name") or "").strip()
        and (not phase.get("passed") or not phase.get("reviewer_ready"))
    )


def _decision_document_identity_gate(
    *,
    slot: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
    review_id: str,
    coverage_class_id: str,
    expected_contract_status: str,
    expected_forest_unit_id: str,
    expected_source_set_id: str,
    policy: Any,
) -> dict[str, Any]:
    if not isinstance(policy, dict):
        policy = {}
    mode = str(policy.get("mode") or "").strip()
    applies_to_statuses = set(
        _string_list(policy.get("applies_to_expected_contract_statuses"))
        or sorted(DECISION_DOCUMENT_IDENTITY_REQUIRED_CONTRACT_STATUSES)
    )
    applies_to_coverage_class_ids = set(
        _string_list(policy.get("applies_to_coverage_class_ids"))
    )
    required = (
        mode == "fail_closed"
        and expected_contract_status in applies_to_statuses
        and (
            not applies_to_coverage_class_ids
            or coverage_class_id in applies_to_coverage_class_ids
        )
    )
    path_value = slot.get("forest_plan_context_summary_path")
    summary_path = (
        _resolve_manifest_repo_path(str(path_value), manifest_path)
        if path_value
        else output_dir / "reviews" / review_id / "forest_plan_context_summary.json"
    )
    failure_reasons: list[str] = []
    payload: dict[str, Any] = {}
    path_exists = summary_path.exists()

    if path_exists:
        try:
            loaded = _read_json(summary_path)
            if isinstance(loaded, dict):
                payload = loaded
            else:
                failure_reasons.append("decision_document_identity_invalid_json")
        except (OSError, json.JSONDecodeError):
            failure_reasons.append("decision_document_identity_invalid_json")
    elif required:
        failure_reasons.append("decision_document_identity_missing")

    actual_review_id = str(payload.get("review_id") or "").strip()
    actual_source_set_id = str(payload.get("source_set_id") or "").strip()
    location = (
        payload.get("title_page_project_location")
        if isinstance(payload.get("title_page_project_location"), dict)
        else {}
    )
    evidence_refs = (
        location.get("evidence_refs") if isinstance(location.get("evidence_refs"), list) else []
    )
    forest_unit_name = str(location.get("forest_unit_name") or "").strip()
    ranger_district_count = _optional_int(location.get("ranger_district_count")) or 0
    county_count = _optional_int(location.get("county_count")) or 0
    state = str(location.get("state") or "").strip()
    other_forest_unit_count = _optional_int(location.get("other_forest_unit_count")) or 0

    if required and payload:
        if actual_review_id != review_id:
            failure_reasons.append("decision_document_context_review_id_mismatch")
        if expected_source_set_id and actual_source_set_id != expected_source_set_id:
            failure_reasons.append("decision_document_context_source_set_mismatch")
        if not bool(location.get("present")):
            failure_reasons.append("decision_document_identity_missing")
        if not forest_unit_name or not bool(location.get("forest_unit_resolved")):
            failure_reasons.append("decision_document_forest_unit_missing")
        if ranger_district_count <= 0:
            failure_reasons.append("decision_document_ranger_district_missing")
        if county_count <= 0:
            failure_reasons.append("decision_document_county_missing")
        if not state:
            failure_reasons.append("decision_document_state_missing")
        if other_forest_unit_count > 0:
            failure_reasons.append("decision_document_other_forest_unit_present")
        if not evidence_refs:
            failure_reasons.append("decision_document_identity_evidence_missing")

    return {
        "required": required,
        "passed": not failure_reasons,
        "path": str(summary_path),
        "path_exists": path_exists,
        "review_id": actual_review_id or None,
        "expected_review_id": review_id,
        "review_id_matches": (not required or actual_review_id == review_id),
        "source_set_id": actual_source_set_id or None,
        "expected_source_set_id": expected_source_set_id or None,
        "source_set_matches": (
            not required
            or not expected_source_set_id
            or actual_source_set_id == expected_source_set_id
        ),
        "expected_forest_unit_id": expected_forest_unit_id or None,
        "forest_unit_name": forest_unit_name or None,
        "ranger_district_names": _string_list(location.get("ranger_district_names")),
        "ranger_district_count": ranger_district_count,
        "counties": _string_list(location.get("counties")),
        "county_count": county_count,
        "state": state or None,
        "other_forest_unit_names": _string_list(location.get("other_forest_unit_names")),
        "other_forest_unit_count": other_forest_unit_count,
        "evidence_ref_count": len(evidence_refs),
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _package_authority_result(
    *,
    authority_spec: Any,
    manifest_path: Path,
) -> dict[str, Any]:
    if not isinstance(authority_spec, dict):
        return {
            "passed": False,
            "failure_reasons": ["missing_package_authority"],
            "mode": None,
        }
    replay_context = authority_spec.get("replay_context_path")
    intake_path = authority_spec.get("intake_package_path")
    details: dict[str, Any] = {}
    failure_reasons = []
    mode = None
    if replay_context:
        mode = "replay_context"
        replay_path = _resolve_repo_path(str(replay_context), manifest_path)
        details["replay_context_path"] = str(replay_path)
        details["replay_context_path_exists"] = replay_path.exists()
        if not replay_path.exists():
            failure_reasons.append("replay_context_missing")
        else:
            payload = _read_json(replay_path)
            package_path = payload.get("package_path")
            if package_path:
                resolved_package_path = _resolve_context_path(
                    replay_path,
                    Path(str(package_path)),
                )
                details["package_path"] = str(resolved_package_path)
                details["package_path_exists"] = resolved_package_path.exists()
                if not resolved_package_path.exists():
                    failure_reasons.append("package_path_missing")
            else:
                failure_reasons.append("replay_context_package_path_missing")
    elif intake_path:
        mode = "intake_path"
        resolved_intake = _resolve_repo_path(str(intake_path), manifest_path)
        details["package_path"] = str(resolved_intake)
        details["package_path_exists"] = resolved_intake.exists()
        if not resolved_intake.exists():
            failure_reasons.append("package_path_missing")
    else:
        failure_reasons.append("missing_package_authority")
    return {
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
        "mode": mode,
        **details,
    }


def _threshold_failures(
    *,
    thresholds: dict[str, int],
    required_slot_count: int,
    required_coverage_class_count: int,
    distinct_forest_count: int,
    distinct_package_style_count: int,
    reviewer_ready_slot_count: int,
    typed_blocked_slot_count: int,
    missing_required_slot_count: int,
    missing_package_authority_count: int,
) -> list[dict[str, Any]]:
    failures = []
    for metric, actual in (
        ("required_slot_count", required_slot_count),
        ("required_coverage_class_count", required_coverage_class_count),
        ("distinct_forest_count_min", distinct_forest_count),
        ("distinct_package_style_count_min", distinct_package_style_count),
        ("reviewer_ready_slot_count_min", reviewer_ready_slot_count),
        ("typed_blocked_slot_count_min", typed_blocked_slot_count),
        ("missing_required_slot_count_max", missing_required_slot_count),
        ("missing_package_authority_count_max", missing_package_authority_count),
    ):
        expected = thresholds.get(metric)
        if expected is None:
            continue
        if metric.endswith("_max"):
            if actual > expected:
                failures.append({"metric": metric, "expected_max": expected, "actual": actual})
        else:
            if actual < expected:
                failures.append({"metric": metric, "expected_min": expected, "actual": actual})
    return failures


def _failure_category_counts(
    *,
    slot_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
    missing_coverage_class_ids: list[str],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    def bump(category: str) -> None:
        counts[category] = counts.get(category, 0) + 1

    for slot in slot_results:
        for reason in slot.get("failure_reasons", []):
            bump(str(reason))
        if slot["expected_contract_status"] == "typed_blocked" and slot["unexpected_blocker_categories"]:
            bump("typed_blocked_blocker_mismatch")
    for failure in threshold_failures:
        metric = str(failure.get("metric") or "")
        if metric == "required_slot_count":
            bump("missing_required_slot")
        elif metric == "required_coverage_class_count":
            bump("missing_required_coverage_class")
        elif metric == "distinct_forest_count_min":
            bump("insufficient_forest_diversity")
        elif metric == "distinct_package_style_count_min":
            bump("insufficient_package_style_diversity")
        elif metric == "reviewer_ready_slot_count_min":
            bump("insufficient_reviewer_ready_slots")
        elif metric == "typed_blocked_slot_count_min":
            bump("missing_typed_blocked_slot")
        elif metric == "missing_required_slot_count_max":
            bump("missing_required_slot")
        elif metric == "missing_package_authority_count_max":
            bump("missing_package_authority")
    for _ in missing_coverage_class_ids:
        bump("missing_required_coverage_class")
    return counts


def _runtime_forest_scope_gate(
    *,
    coverage_class_id: str,
    expected_forest_unit_id: str,
    summary: dict[str, Any],
) -> dict[str, Any]:
    required = coverage_class_id in RUNTIME_FOREST_SCOPE_REQUIRED_COVERAGE_CLASS_IDS
    runtime_scope = summary.get("runtime_forest_scope")
    contract_forest_unit_id = str(summary.get("forest_unit_id") or "").strip()
    failure_reasons: list[str] = []

    if not required:
        return {
            "required": False,
            "passed": True,
            "expected_forest_unit_id": expected_forest_unit_id or None,
            "contract_forest_unit_id": contract_forest_unit_id or None,
            "runtime_expected_forest_unit_id": None,
            "expected_scope_status": None,
            "actual_scope_status": None,
            "scope_status_expectation_present": False,
            "scope_status_expectation_passed": False,
            "failure_reasons": [],
        }

    if not expected_forest_unit_id:
        failure_reasons.append("expected_forest_unit_missing")
    if contract_forest_unit_id != expected_forest_unit_id:
        failure_reasons.append("contract_forest_unit_mismatch")
    if not isinstance(runtime_scope, dict):
        runtime_scope = {}
        failure_reasons.append("runtime_forest_scope_missing")

    runtime_expected_forest_unit_id = str(
        runtime_scope.get("expected_forest_unit_id") or ""
    ).strip()
    expected_scope_status = str(runtime_scope.get("expected_scope_status") or "").strip()
    actual_scope_status = str(runtime_scope.get("actual_scope_status") or "").strip()
    scope_status_expectation_present = bool(
        runtime_scope.get("scope_status_expectation_present")
    )
    scope_status_expectation_passed = bool(
        runtime_scope.get("scope_status_expectation_passed")
    )

    if runtime_expected_forest_unit_id != expected_forest_unit_id:
        failure_reasons.append("runtime_expected_forest_unit_mismatch")
    if not expected_scope_status:
        failure_reasons.append("runtime_expected_scope_status_missing")
    if not actual_scope_status:
        failure_reasons.append("runtime_scope_status_missing")
    if not scope_status_expectation_present:
        failure_reasons.append("runtime_scope_status_missing")
    if not bool(runtime_scope.get("passed")):
        failure_reasons.append("runtime_forest_scope_mismatch")
    if not scope_status_expectation_passed:
        failure_reasons.append("runtime_scope_status_expectation_failed")

    return {
        "required": True,
        "passed": not failure_reasons,
        "expected_forest_unit_id": expected_forest_unit_id or None,
        "contract_forest_unit_id": contract_forest_unit_id or None,
        "runtime_expected_forest_unit_id": runtime_expected_forest_unit_id or None,
        "expected_scope_status": expected_scope_status or None,
        "actual_scope_status": actual_scope_status or None,
        "scope_status_expectation_present": scope_status_expectation_present,
        "scope_status_expectation_passed": scope_status_expectation_passed,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _slot_by_review_id(manifest: dict[str, Any], review_id: str) -> dict[str, Any]:
    for slot in manifest.get("slots", []):
        if str(slot.get("review_id") or "").strip() == review_id:
            return slot
    raise ValueError(
        "review_id is not tracked by the real-package review coverage manifest: "
        f"{review_id}"
    )


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("real-package review coverage manifest must be a JSON object")
    if manifest.get("schema_version") != REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION:
        raise ValueError(
            "real-package review coverage manifest must use "
            f"schema_version={REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION!r}"
        )
    if not str(manifest.get("id") or "").strip():
        raise ValueError("real-package review coverage manifest requires id")
    if not str(manifest.get("version") or "").strip():
        raise ValueError("real-package review coverage manifest requires version")

    required_coverage_class_ids = _string_list(manifest.get("required_coverage_class_ids"))
    if not required_coverage_class_ids:
        raise ValueError(
            "real-package review coverage manifest requires required_coverage_class_ids"
        )

    slots = manifest.get("slots")
    if not isinstance(slots, list) or not slots:
        raise ValueError("real-package review coverage manifest requires slots")

    slot_ids: set[str] = set()
    review_ids: set[str] = set()
    required_class_ids: set[str] = set()
    required_slot_count = 0
    for slot in slots:
        if not isinstance(slot, dict):
            raise ValueError("real-package review coverage slots must be JSON objects")
        slot_id = str(slot.get("slot_id") or "").strip()
        review_id = str(slot.get("review_id") or "").strip()
        coverage_class_id = str(slot.get("coverage_class_id") or "").strip()
        required = bool(slot.get("required"))
        _validate_slot(slot)
        if slot_id in slot_ids:
            raise ValueError(f"duplicate real-package review slot_id: {slot_id}")
        if review_id in review_ids:
            raise ValueError(f"duplicate real-package review review_id: {review_id}")
        slot_ids.add(slot_id)
        review_ids.add(review_id)
        if required:
            required_slot_count += 1
            required_class_ids.add(coverage_class_id)

    if required_class_ids != set(required_coverage_class_ids):
        raise ValueError(
            "required_coverage_class_ids must exactly match the required slot coverage_class_id set"
        )
    thresholds = _int_dict(manifest.get("coverage_thresholds"))
    required_threshold = thresholds.get("required_slot_count")
    if required_threshold is not None and required_slot_count < required_threshold:
        raise ValueError("real-package review coverage manifest does not meet required_slot_count")


def _validate_slot(slot: dict[str, Any]) -> None:
    for field in (
        "slot_id",
        "label",
        "review_id",
        "package_label",
        "coverage_class_id",
        "forest_unit_id",
        "eval_file",
        "expected_contract_status",
    ):
        if not str(slot.get(field) or "").strip():
            raise ValueError(f"real-package review slot requires non-empty {field}")
    expected_contract_status = str(slot.get("expected_contract_status") or "").strip()
    if expected_contract_status not in EXPECTED_CONTRACT_STATUSES:
        raise ValueError(
            "real-package review slot expected_contract_status must be reviewer_ready or "
            f"typed_blocked: {expected_contract_status}"
        )
    if "required" not in slot:
        raise ValueError("real-package review slot requires required boolean")
    authority_spec = slot.get("package_authority")
    if not isinstance(authority_spec, dict):
        raise ValueError("real-package review slot requires package_authority object")
    modes = [
        field
        for field in ("replay_context_path", "intake_package_path")
        if str(authority_spec.get(field) or "").strip()
    ]
    if len(modes) != 1:
        raise ValueError(
            "real-package review slot package_authority must declare exactly one of "
            "replay_context_path or intake_package_path"
        )
    results_path = slot.get("results_path")
    if results_path is not None and not str(results_path).strip():
        raise ValueError("real-package review slot results_path must be non-empty when provided")


def _load_summary(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    summary = payload.get("summary") if isinstance(payload, dict) else None
    return summary if isinstance(summary, dict) else payload


def _resolve_repo_path(value: str, manifest_path: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (manifest_path.parent / path).resolve()


def _resolve_manifest_repo_path(value: str, manifest_path: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    manifest_dir = manifest_path.resolve().parent
    repo_root = manifest_dir.parent if manifest_dir.name == "config" else manifest_dir
    return (repo_root / path).resolve()


def _resolve_context_path(config_path: Path, value: Path) -> Path:
    base_dir = config_path.resolve().parents[2]
    return value if value.is_absolute() else (base_dir / value).resolve()


def _int_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            result[str(key)] = int(raw)
        except (TypeError, ValueError):
            continue
    return result


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(item).strip() for item in value if str(item).strip())


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
