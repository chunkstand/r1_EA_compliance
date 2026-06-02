from __future__ import annotations

from pathlib import Path

from .artifact_utils import _dict
from .artifact_utils import _read_json_if_exists
from .artifact_utils import _safe_int


FOREST_PLAN_OUT_OF_SCOPE_STATUSES = {
    "ambiguous",
    "not_custer_gallatin",
    "not_in_scope",
    "not_selected_forest_unit",
}


def forest_plan_authority_universe_currentness(
    *,
    output_dir: Path,
    review_dir: Path,
    authority_universe: dict,
) -> dict:
    summary_path = review_dir / "forest_plan_context_summary.json"
    forest_plan_summary = _read_json_if_exists(summary_path)
    component_evaluation = _dict((forest_plan_summary or {}).get("component_evaluation"))
    expected_component_count = _safe_int(component_evaluation.get("component_count"))
    expected_inventory_path = str(component_evaluation.get("component_inventory_path") or "")
    currentness_required = bool(expected_component_count or expected_inventory_path)
    component_candidates = [
        candidate
        for candidate in authority_universe.get("candidate_authorities") or []
        if isinstance(candidate, dict)
        and candidate.get("candidate_authority_type") == "forest_plan_component"
    ]
    artifact_paths = _dict(authority_universe.get("artifact_paths"))
    actual_inventory_path = str(
        artifact_paths.get("forest_plan_component_inventory_path")
        or _dict(authority_universe.get("summary")).get(
            "forest_plan_component_inventory_path"
        )
        or ""
    )
    actual_component_count = len(component_candidates)
    path_matches = (
        not currentness_required
        or _path_values_match(
            output_dir=output_dir,
            actual_path=actual_inventory_path,
            expected_path=expected_inventory_path,
        )
    )
    count_matches = (
        not currentness_required or actual_component_count == expected_component_count
    )
    failed_checks = []
    if not path_matches:
        failed_checks.append("forest_plan_component_inventory_path_mismatch")
    if not count_matches:
        failed_checks.append("forest_plan_component_candidate_count_mismatch")
    return {
        "passed": not failed_checks,
        "details": {
            "forest_plan_authority_universe_currentness_required": currentness_required,
            "forest_plan_context_summary_path": str(summary_path),
            "authority_universe_forest_plan_inventory_path": actual_inventory_path or None,
            "expected_forest_plan_component_inventory_path": (
                expected_inventory_path or None
            ),
            "forest_plan_component_inventory_path_matches_context": path_matches,
            "forest_plan_component_candidate_count": actual_component_count,
            "expected_forest_plan_component_count": expected_component_count,
            "forest_plan_component_candidate_count_matches_context": count_matches,
            "failed_forest_plan_currentness_checks": failed_checks,
        },
    }


def forest_plan_matrix_required(
    *,
    forest_plan_summary: dict,
    component_evaluation: dict,
) -> bool:
    scope_status = str(forest_plan_summary.get("scope_status") or "").strip()
    if not scope_status or scope_status in FOREST_PLAN_OUT_OF_SCOPE_STATUSES:
        return False
    return bool(
        _safe_int(component_evaluation.get("component_count")) > 0
        or _safe_int(component_evaluation.get("applicable_standard_count")) > 0
        or forest_plan_summary.get("reviewer_ready")
        or component_evaluation.get("reviewer_ready")
    )


def read_forest_plan_context_summary(review_dir: Path) -> dict:
    summary_path = review_dir / "forest_plan_context_summary.json"
    summary = _read_json_if_exists(summary_path)
    return summary if isinstance(summary, dict) else {}


def _path_values_match(
    *,
    output_dir: Path,
    actual_path: str,
    expected_path: str,
) -> bool:
    if not actual_path and not expected_path:
        return True
    if not actual_path or not expected_path:
        return False
    return _resolved_path_value(output_dir, actual_path) == _resolved_path_value(
        output_dir,
        expected_path,
    )


def _resolved_path_value(output_dir: Path, value: str) -> str:
    path = Path(value)
    candidates = [path]
    if not path.is_absolute():
        candidates.extend([output_dir.parent / path, output_dir / path])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return str(path)
