from __future__ import annotations

from pathlib import Path
from typing import Any

from .promotion_suite_support import MISSING
from .promotion_suite_support import _check_result
from .promotion_suite_support import _equals_check
from .promotion_suite_support import _json_path
from .promotion_suite_support import _read_json
from .promotion_suite_support import _resolve_output_path


def _expansion_slot_result(slot: dict[str, Any], *, output_dir: Path) -> dict[str, Any]:
    manifest_ready = bool(slot.get("ready", False))
    category = str(slot.get("failure_category") or "package_fixture_missing")
    profile_checks = _forest_plan_profile_slot_checks(slot, output_dir=output_dir)
    source_set_checks = _gate_artifact_source_set_checks(
        slot,
        output_dir=output_dir,
        enabled=manifest_ready,
    )
    failed_profile_categories = [
        check["failure_category"] for check in profile_checks if not check["passed"]
    ]
    failed_source_set_categories = [
        check["failure_category"] for check in source_set_checks if not check["passed"]
    ]
    ready = (
        manifest_ready
        and not failed_profile_categories
        and not failed_source_set_categories
    )
    failure_categories = sorted(
        set(
            ([] if manifest_ready else [category])
            + failed_profile_categories
            + failed_source_set_categories
        )
    )
    result = {
        "id": slot["id"],
        "label": slot.get("label"),
        "status": slot.get("status", "open"),
        "manifest_ready": manifest_ready,
        "ready": ready,
        "required_for_current_promotion": bool(
            slot.get("required_for_current_promotion", False)
        ),
        "failure_categories": [] if ready else failure_categories,
        "next_action": slot.get("next_action"),
        "acceptance_signal": slot.get("acceptance_signal"),
    }
    if profile_checks:
        result["forest_plan_profile_checks"] = profile_checks
    if source_set_checks:
        result["gate_artifact_source_set_checks"] = source_set_checks
    for key in (
        "review_id",
        "source_set_id",
        "package_path",
        "forest_plan_profile",
        "project_metadata",
        "expected_gate_artifacts",
        "last_local_signal",
    ):
        if key in slot:
            result[key] = slot[key]
    return result


def _gate_artifact_source_set_checks(
    slot: dict[str, Any],
    *,
    output_dir: Path,
    enabled: bool,
) -> list[dict[str, Any]]:
    if not enabled:
        return []
    slot_source_set_id = str(slot.get("source_set_id") or "").strip()
    review_id = str(slot.get("review_id") or "").strip()
    if not slot_source_set_id or not review_id:
        return []

    checks: list[dict[str, Any]] = []
    for artifact in slot.get("expected_gate_artifacts", []):
        artifact_id = str(artifact.get("id") or "").strip()
        artifact_path = str(artifact.get("path") or "").strip()
        if not artifact_id or not artifact_path or not artifact_path.endswith(".json"):
            continue
        resolved_path = _resolve_output_path(
            artifact_path.format(review_id=review_id),
            output_dir,
        )
        if not resolved_path.exists():
            continue
        payload = _read_json(resolved_path)
        discovered_source_set_ids = sorted(_collect_source_set_ids(payload))
        if not discovered_source_set_ids:
            continue
        checks.append(
            _check_result(
                name=f"{artifact_id}_source_set_matches_slot",
                passed=discovered_source_set_ids == [slot_source_set_id],
                expected=[slot_source_set_id],
                actual=discovered_source_set_ids,
                failure_category="stale_artifact",
                details={"path": str(resolved_path)},
            )
        )
    return checks


def _collect_source_set_ids(payload: Any) -> set[str]:
    discovered: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "source_set_id":
                source_set_id = str(value or "").strip()
                if source_set_id:
                    discovered.add(source_set_id)
            discovered.update(_collect_source_set_ids(value))
    elif isinstance(payload, list):
        for value in payload:
            discovered.update(_collect_source_set_ids(value))
    return discovered


def _forest_plan_profile_slot_checks(
    slot: dict[str, Any], *, output_dir: Path
) -> list[dict[str, Any]]:
    declared_profile = str(slot.get("forest_plan_profile") or "")
    if not declared_profile:
        return []
    review_id = str(slot.get("review_id") or "")
    category = "forest_plan_reviewer_not_ready"
    checks: list[dict[str, Any]] = []
    compliance_path = output_dir / "reviews" / review_id / "compliance_review.json"
    if not compliance_path.exists():
        return [
            _check_result(
                name="forest_plan_compliance_review_exists",
                passed=False,
                expected=True,
                actual=False,
                failure_category=category,
                details={"path": str(compliance_path)},
            )
        ]

    compliance_payload = _read_json(compliance_path)
    forest_plan_review = _json_path(compliance_payload, "summary.forest_plan_review")
    if forest_plan_review is MISSING or not isinstance(forest_plan_review, dict):
        checks.append(
            _check_result(
                name="forest_plan_review_summary_present",
                passed=False,
                expected="summary.forest_plan_review",
                actual=None,
                failure_category=category,
                details={"path": str(compliance_path)},
            )
        )
        artifact_scope_status = None
    else:
        checks.append(
            _check_result(
                name="forest_plan_review_summary_present",
                passed=True,
                expected="summary.forest_plan_review",
                actual="present",
                failure_category=category,
                details={"path": str(compliance_path)},
            )
        )
        artifact_scope_status = forest_plan_review.get("scope_status")
        checks.append(
            _equals_check(
                "forest_plan_scope_status_matches_declared_profile",
                actual=artifact_scope_status,
                expected=declared_profile,
                failure_category=category,
            )
        )
        checks.append(
            _equals_check(
                "forest_plan_validation_passed",
                actual=forest_plan_review.get("validation_passed"),
                expected=True,
                failure_category=category,
            )
        )
        checks.append(
            _equals_check(
                "forest_plan_reviewer_ready",
                actual=forest_plan_review.get("reviewer_ready"),
                expected=True,
                failure_category=category,
            )
        )

    last_signal_scope_status = _json_path(
        slot, "last_local_signal.forest_plan_scope_status"
    )
    checks.append(
        _check_result(
            name="forest_plan_last_signal_scope_status_matches_artifact",
            passed=last_signal_scope_status is not MISSING
            and last_signal_scope_status == artifact_scope_status,
            expected=artifact_scope_status,
            actual=None if last_signal_scope_status is MISSING else last_signal_scope_status,
            failure_category=category,
        )
    )

    gate_required = (
        _json_path(slot, "last_local_signal.forest_plan_component_gate_required") is True
    )
    if gate_required:
        phase_path = output_dir / "reviews" / review_id / "phase_eval_results.json"
        phase_names: list[str] = []
        if phase_path.exists():
            phase_payload = _read_json(phase_path)
            phase_names = [
                str(phase.get("name"))
                for phase in phase_payload.get("phases", [])
                if isinstance(phase, dict)
            ]
        checks.append(
            _check_result(
                name="forest_plan_component_phase_present_when_required",
                passed=bool(
                    {"forest_plan_component_eval", "forest_plan_component_adjudication"}
                    .intersection(phase_names)
                ),
                expected=[
                    "forest_plan_component_eval",
                    "forest_plan_component_adjudication",
                ],
                actual=phase_names,
                failure_category=category,
                details={"path": str(phase_path)},
            )
        )
    else:
        checks.append(
            _check_result(
                name="forest_plan_component_phase_present_when_required",
                passed=True,
                expected="not_required",
                actual="not_required",
                failure_category=category,
            )
        )
    return checks
