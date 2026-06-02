from __future__ import annotations

from pathlib import Path
import re

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
    expected_inventory_path = str(component_evaluation.get("component_inventory_path") or "")
    authority_summary = _dict(authority_universe.get("summary"))
    snapshot_candidate_count = _safe_int(
        authority_summary.get("forest_plan_component_candidate_count")
    )
    context_component_count = _safe_int(component_evaluation.get("component_count"))
    expected_candidate_count = snapshot_candidate_count or context_component_count
    currentness_required = bool(
        snapshot_candidate_count or context_component_count or expected_inventory_path
    )
    component_candidates = [
        candidate
        for candidate in authority_universe.get("candidate_authorities") or []
        if isinstance(candidate, dict)
        and candidate.get("candidate_authority_type") == "forest_plan_component"
    ]
    artifact_paths = _dict(authority_universe.get("artifact_paths"))
    actual_inventory_path = str(
        artifact_paths.get("forest_plan_component_inventory_path")
        or authority_summary.get("forest_plan_component_inventory_path")
        or ""
    )
    actual_component_count = len(component_candidates)
    context_count_matches = (
        not context_component_count or actual_component_count == context_component_count
    )
    snapshot_count_matches = (
        not snapshot_candidate_count or actual_component_count == snapshot_candidate_count
    )
    forest_identity = _forest_plan_component_forest_identity(
        forest_plan_summary=forest_plan_summary or {},
        authority_universe=authority_universe,
        authority_summary=authority_summary,
        component_candidates=component_candidates,
    )
    path_matches = (
        not currentness_required
        or _path_values_match(
            output_dir=output_dir,
            actual_path=actual_inventory_path,
            expected_path=expected_inventory_path,
        )
    )
    count_matches = (
        not currentness_required
        or (snapshot_count_matches and context_count_matches)
    )
    failed_checks = []
    if not path_matches:
        failed_checks.append("forest_plan_component_inventory_path_mismatch")
    if not snapshot_count_matches:
        failed_checks.append("forest_plan_component_candidate_count_mismatch")
    if not context_count_matches:
        failed_checks.append("forest_plan_component_context_count_mismatch")
    if not forest_identity["matches"]:
        failed_checks.append("forest_plan_component_forest_unit_mismatch")
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
            "expected_forest_plan_component_count": expected_candidate_count,
            "snapshot_forest_plan_component_count": snapshot_candidate_count,
            "forest_plan_context_component_count": context_component_count,
            "forest_plan_component_candidate_count_matches_context": count_matches,
            "forest_plan_component_snapshot_count_matches": snapshot_count_matches,
            "forest_plan_component_context_count_matches": context_count_matches,
            **forest_identity["details"],
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


def _forest_plan_component_forest_identity(
    *,
    forest_plan_summary: dict,
    authority_universe: dict,
    authority_summary: dict,
    component_candidates: list[dict],
) -> dict:
    title_page = _dict(forest_plan_summary.get("title_page_project_location"))
    context_forest_name = str(title_page.get("forest_unit_name") or "").strip()
    context_scope_status = str(forest_plan_summary.get("scope_status") or "").strip()
    expected_forest_unit_ids = _expected_forest_unit_id_variants(
        authority_universe=authority_universe,
        authority_summary=authority_summary,
        scope_status=context_scope_status,
    )
    candidate_forest_unit_ids = sorted(
        {
            str(_dict(candidate.get("forest_plan")).get("forest_unit_id") or "").strip()
            for candidate in component_candidates
            if str(_dict(candidate.get("forest_plan")).get("forest_unit_id") or "").strip()
        }
    )
    candidate_forest_names = sorted(
        {
            str(name).strip()
            for candidate in component_candidates
            for name in _candidate_forest_names(candidate)
            if str(name).strip()
        }
    )
    id_matches = (
        not expected_forest_unit_ids
        or bool(candidate_forest_unit_ids)
        and set(candidate_forest_unit_ids) <= expected_forest_unit_ids
    )
    name_matches = (
        not context_forest_name
        or bool(candidate_forest_names)
        and _normalized_forest_identity_text(context_forest_name)
        in {
            _normalized_forest_identity_text(name)
            for name in candidate_forest_names
        }
    )
    identity_required = bool(
        component_candidates
        and (expected_forest_unit_ids or context_forest_name or context_scope_status)
    )
    matches = (not identity_required) or (id_matches and name_matches)
    return {
        "matches": matches,
        "details": {
            "forest_plan_context_scope_status": context_scope_status or None,
            "forest_plan_context_forest_unit_name": context_forest_name or None,
            "expected_forest_plan_forest_unit_ids": sorted(expected_forest_unit_ids),
            "authority_universe_forest_unit_id": (
                str(authority_universe.get("forest_unit_id") or "").strip() or None
            ),
            "authority_universe_summary_forest_unit_id": (
                str(authority_summary.get("forest_unit_id") or "").strip() or None
            ),
            "forest_plan_component_candidate_forest_unit_ids": candidate_forest_unit_ids,
            "forest_plan_component_candidate_forest_names": candidate_forest_names,
            "forest_plan_component_forest_unit_matches_context": matches,
        },
    }


def _expected_forest_unit_id_variants(
    *,
    authority_universe: dict,
    authority_summary: dict,
    scope_status: str,
) -> set[str]:
    variants = {
        str(authority_universe.get("forest_unit_id") or "").strip(),
        str(authority_summary.get("forest_unit_id") or "").strip(),
    }
    scoped_id = str(_dict(authority_universe.get("review_scope")).get("forest_unit_id") or "")
    summary_scoped_id = str(
        _dict(authority_summary.get("review_scope")).get("forest_unit_id") or ""
    )
    variants.update({scoped_id.strip(), summary_scoped_id.strip()})
    scope_slug = str(scope_status or "").strip().replace("_", "-")
    if scope_slug:
        variants.update({scope_slug, f"{scope_slug}-nf", f"{scope_slug}-nfs"})
    return {variant for variant in variants if variant}


def _candidate_forest_names(candidate: dict) -> list[str]:
    forest_plan = _dict(candidate.get("forest_plan"))
    names = forest_plan.get("forest_unit_names")
    if isinstance(names, list):
        return [str(name) for name in names]
    return []


def _normalized_forest_identity_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()
