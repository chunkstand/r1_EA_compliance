from __future__ import annotations

from pathlib import Path
from typing import Any

from .nepa_knowledge_graph_export_models import DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH
from .nepa_knowledge_graph_export_models import REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION
from .nepa_knowledge_graph_export_models import SOURCE_DELTA_READINESS_SCHEMA_VERSION
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _dict_list
from .nepa_knowledge_graph_export_models import _read_json
from .nepa_knowledge_graph_export_models import _source_node_id
from .nepa_knowledge_graph_export_models import _strings


def _region1_profile_readiness_rows(readiness: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(readiness.get("profile_rows"))


def _load_region1_forest_plan_readiness(path: Path) -> dict[str, Any]:
    readiness = _read_json(path)
    if readiness.get("schema_version") == SOURCE_DELTA_READINESS_SCHEMA_VERSION:
        return _normalize_source_delta_region1_readiness(readiness)
    return readiness


def _normalize_source_delta_region1_readiness(report: dict[str, Any]) -> dict[str, Any]:
    baseline = _read_json(DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH)
    baseline_rows_by_unit = {
        str(row.get("forest_unit_id") or ""): row
        for row in _dict_list(baseline.get("profile_rows"))
        if row.get("forest_unit_id")
    }
    merged_source_set_id = str(
        _dict(report.get("merged_source_delta_catalog")).get("source_set_id") or ""
    )
    profile_rows = []
    for row in _dict_list(_dict(report.get("forest_profile_readiness")).get("profile_rows")):
        forest_unit_id = str(row.get("forest_unit_id") or "")
        baseline_row = _dict(baseline_rows_by_unit.get(forest_unit_id))
        configured_profile = bool(row.get("configured_profile"))
        profile_readiness_status = str(row.get("profile_readiness_status") or "")
        graph_promotion_status = _source_delta_graph_promotion_status(
            baseline_row=baseline_row,
            configured_profile=configured_profile,
            profile_readiness_status=profile_readiness_status,
        )
        profile_rows.append(
            {
                "active_plan_source_record_id": row.get("active_plan_source_record_id"),
                "applicability_eval_coverage": _dict(
                    baseline_row.get("applicability_eval_coverage")
                ),
                "component_inventory_validation": _normalized_component_inventory_validation(
                    baseline_row=_dict(baseline_row.get("component_inventory_validation")),
                    merged_source_set_id=merged_source_set_id,
                    graph_promotion_status=graph_promotion_status,
                ),
                "forest_unit_id": forest_unit_id,
                "forest_unit_names": _strings(row.get("forest_unit_names")),
                "graph_promotion_status": graph_promotion_status,
                "milestone_5_added_profile": bool(
                    baseline_row.get("milestone_5_added_profile")
                ),
                "profile_kind": row.get("profile_kind"),
                "readiness_blockers": sorted(
                    set(_strings(row.get("blocker_types")))
                    | (
                        set()
                        if graph_promotion_status == "promoted"
                        else {"forest_profile_not_ready"}
                    )
                ),
                "source_requirements": _dict_list(row.get("source_requirements")),
            }
        )
    return {
        "schema_version": REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
        "readiness_matrix_id": "region1-forest-plan-readiness-support-corpus-v1",
        "source_set_id": merged_source_set_id,
        "region1_completeness_claim": False,
        "field_directive_requirements": _dict_list(
            baseline.get("field_directive_requirements")
        ),
        "overlay_requirements": _dict_list(baseline.get("overlay_requirements")),
        "profile_rows": profile_rows,
        "support_document_corpus_summary": _source_delta_support_document_summary(report),
        "source_delta_readiness_schema_version": report.get("schema_version"),
    }


def normalize_source_register_region1_readiness(
    readiness: dict[str, Any],
    *,
    source_set_id: str,
    forest_components: dict[str, Any],
    forest_plan_components_path: Path,
) -> dict[str, Any]:
    components_by_unit: dict[str, list[dict[str, Any]]] = {}
    for component in _dict_list(forest_components.get("components")):
        forest_unit_id = str(component.get("forest_unit_id") or "")
        if not forest_unit_id:
            continue
        components_by_unit.setdefault(forest_unit_id, []).append(component)
    coverage_path = forest_plan_components_path.parent / "component_inventory_build_coverage.json"
    normalized_rows = []
    for row in _region1_profile_readiness_rows(readiness):
        normalized_row = dict(row)
        forest_unit_id = str(normalized_row.get("forest_unit_id") or "")
        components = components_by_unit.get(forest_unit_id, [])
        if components:
            component_inventory_validation = _dict(
                normalized_row.get("component_inventory_validation")
            )
            component_inventory_validation.update(
                {
                    "artifact_path": str(coverage_path),
                    "component_count": len(components),
                    "standard_count": sum(
                        1
                        for component in components
                        if str(component.get("component_type") or "") == "standard"
                    ),
                    "status": "validated",
                }
            )
            normalized_row["graph_promotion_status"] = "promoted"
            normalized_row["component_inventory_validation"] = component_inventory_validation
        else:
            normalized_row["graph_promotion_status"] = "blocked"
            normalized_row["component_inventory_validation"] = {
                "status": "component_inventory_build_required"
            }
        normalized_rows.append(normalized_row)
    return {
        **readiness,
        "source_set_id": source_set_id,
        "region1_completeness_claim": False,
        "profile_rows": normalized_rows,
    }


def _source_delta_graph_promotion_status(
    *,
    baseline_row: dict[str, Any],
    configured_profile: bool,
    profile_readiness_status: str,
) -> str:
    component_inventory_validation = _dict(baseline_row.get("component_inventory_validation"))
    component_inventory_status = str(component_inventory_validation.get("status") or "")
    component_inventory_ready = not component_inventory_status or component_inventory_status == "validated"
    if configured_profile and profile_readiness_status == "ready" and component_inventory_ready:
        return "promoted"
    if configured_profile:
        return "blocked"
    if profile_readiness_status == "ready":
        return "tracked_not_promoted"
    return "blocked"


def _normalized_component_inventory_validation(
    *,
    baseline_row: dict[str, Any],
    merged_source_set_id: str,
    graph_promotion_status: str,
) -> dict[str, Any]:
    if not baseline_row:
        return {"status": "component_inventory_build_required"}
    normalized = dict(baseline_row)
    artifact_path = str(normalized.get("artifact_path") or "")
    if artifact_path and graph_promotion_status == "promoted":
        normalized["artifact_path"] = _rewrite_support_corpus_artifact_path(
            artifact_path,
            merged_source_set_id=merged_source_set_id,
        )
    return normalized


def _rewrite_support_corpus_artifact_path(
    path: str, *, merged_source_set_id: str
) -> str:
    parts = list(Path(path).parts)
    for index, part in enumerate(parts):
        if part.startswith("source-set-"):
            parts[index] = merged_source_set_id
            break
    return str(Path(*parts))


def _source_delta_support_document_summary(report: dict[str, Any]) -> dict[str, Any]:
    merged_catalog = _dict(report.get("merged_source_delta_catalog"))
    source_delta_input = _dict(merged_catalog.get("source_delta_input"))
    extraction = _dict(report.get("extraction_readiness"))
    retrieval = _dict(report.get("retrieval_readiness"))
    profiles = _dict(report.get("forest_profile_readiness"))
    official_gaps = _dict(report.get("official_source_gap_evidence"))
    return {
        "source_set_id": merged_catalog.get("source_set_id"),
        "catalog_source_record_count": merged_catalog.get("catalog_source_record_count"),
        "catalog_confirmed_source_record_count": source_delta_input.get(
            "catalog_confirmed_count"
        ),
        "support_document_source_delta_count": source_delta_input.get("source_delta_count"),
        "official_source_gap_count": official_gaps.get("record_count"),
        "official_source_gap_source_record_ids": _strings(
            official_gaps.get("source_record_ids")
        ),
        "extracted_support_document_source_record_count": extraction.get(
            "extracted_source_record_count"
        ),
        "blocked_support_document_source_record_count": extraction.get(
            "blocked_source_record_count"
        ),
        "indexed_support_document_source_record_count": retrieval.get(
            "indexed_source_record_count_for_expected_sources"
        ),
        "configured_profile_ready_count": profiles.get("ready_profile_count"),
        "configured_profile_blocked_count": profiles.get("blocked_profile_count"),
        "tracking_only_ready_count": profiles.get("ready_tracking_only_count"),
        "tracking_only_blocked_count": profiles.get("blocked_tracking_only_count"),
    }


def _region1_profile_readiness_by_unit(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("forest_unit_id")): row
        for row in _region1_profile_readiness_rows(readiness)
        if row.get("forest_unit_id")
    }


def _region1_profile_readiness_blockers(row: dict[str, Any]) -> list[str]:
    blockers = set(_strings(row.get("readiness_blockers")))
    if row and str(row.get("graph_promotion_status") or "") != "promoted":
        blockers.add("forest_profile_not_ready")
    for requirement in _dict_list(row.get("source_requirements")):
        if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
            blockers.add("missing_source")
    return sorted(blockers)


def _region1_profile_display(row: dict[str, Any]) -> dict[str, str]:
    if row and str(row.get("graph_promotion_status") or "") != "promoted":
        return {"display_status": "readiness_blocked", "review_readiness_status": "blocked"}
    return {"display_status": "active", "review_readiness_status": "not_review_specific"}


def _region1_requirement_source_record_ids(requirement: dict[str, Any]) -> list[str]:
    source_record_ids = set(_strings(requirement.get("source_record_ids")))
    source_record_id = str(requirement.get("source_record_id") or "")
    if source_record_id:
        source_record_ids.add(source_record_id)
    return sorted(source_record_ids)


def _region1_requirement_blockers(
    requirement: dict[str, Any], source_record_ids: list[str]
) -> list[str]:
    if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
        return ["missing_source"]
    if not source_record_ids:
        return ["missing_source"]
    return []


def _region1_component_node_id(component_id: str) -> str:
    return f"forest_plan_component:{component_id}"


def _region1_field_directive_component_id(requirement: dict[str, Any]) -> str:
    return f"region1-field-directive:{requirement.get('requirement_id')}"


def _region1_overlay_component_id(requirement: dict[str, Any]) -> str:
    return f"region1-overlay:{requirement.get('overlay_id')}"


def _region1_requirement_source_gaps(
    readiness: dict[str, Any],
    *,
    catalog_source_ids: set[str],
) -> dict[str, list[str]]:
    gaps = {}
    for requirement in _dict_list(readiness.get("field_directive_requirements")):
        if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
            continue
        missing = _region1_missing_requirement_source_ids(requirement, catalog_source_ids)
        if missing:
            gaps[f"field_directive:{requirement.get('requirement_id')}"] = missing
    for requirement in _dict_list(readiness.get("overlay_requirements")):
        if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
            continue
        missing = _region1_missing_requirement_source_ids(requirement, catalog_source_ids)
        if missing:
            gaps[f"overlay:{requirement.get('overlay_id')}"] = missing
    return gaps


def _region1_missing_requirement_source_ids(
    requirement: dict[str, Any],
    catalog_source_ids: set[str],
) -> list[str]:
    source_record_ids = _region1_requirement_source_record_ids(requirement)
    if not source_record_ids:
        return ["<missing source_record_id>"]
    return sorted(source_record_id for source_record_id in source_record_ids if source_record_id not in catalog_source_ids)


def _region1_requirement_edge_gaps(
    readiness: dict[str, Any],
    *,
    edge_tuples: set[tuple[str, str, str]],
) -> dict[str, list[str]]:
    gaps = {}
    for requirement in _dict_list(readiness.get("field_directive_requirements")):
        requirement_id = str(requirement.get("requirement_id") or "")
        if not requirement_id:
            continue
        component_node_id = _region1_component_node_id(
            _region1_field_directive_component_id(requirement)
        )
        missing = _region1_missing_requirement_source_edges(
            requirement,
            component_node_id=component_node_id,
            edge_tuples=edge_tuples,
        )
        if missing:
            gaps[f"field_directive:{requirement_id}"] = missing
    for requirement in _dict_list(readiness.get("overlay_requirements")):
        overlay_id = str(requirement.get("overlay_id") or "")
        if not overlay_id:
            continue
        component_node_id = _region1_component_node_id(_region1_overlay_component_id(requirement))
        missing = _region1_missing_requirement_source_edges(
            requirement,
            component_node_id=component_node_id,
            edge_tuples=edge_tuples,
        )
        if missing:
            gaps[f"overlay:{overlay_id}"] = missing
    return gaps


def _region1_missing_requirement_source_edges(
    requirement: dict[str, Any],
    *,
    component_node_id: str,
    edge_tuples: set[tuple[str, str, str]],
) -> list[str]:
    missing = []
    for source_record_id in _region1_requirement_source_record_ids(requirement):
        if ("HAS_FOREST_COMPONENT", _source_node_id(source_record_id), component_node_id) not in edge_tuples:
            missing.append(source_record_id)
    return sorted(missing)


def _region1_readiness_summary(readiness: dict[str, Any]) -> dict[str, Any]:
    rows = _region1_profile_readiness_rows(readiness)
    added_rows = [row for row in rows if row.get("milestone_5_added_profile")]
    promoted_rows = [row for row in rows if row.get("graph_promotion_status") == "promoted"]
    blocked_rows = [row for row in rows if row.get("graph_promotion_status") != "promoted"]
    field_directive_requirements = _dict_list(readiness.get("field_directive_requirements"))
    overlay_requirements = _dict_list(readiness.get("overlay_requirements"))
    support_document_summary = _dict(readiness.get("support_document_corpus_summary"))
    return {
        "region1_forest_plan_readiness_profile_count": len(rows),
        "region1_forest_plan_graph_ready_profile_count": len(promoted_rows),
        "region1_forest_plan_blocked_profile_count": len(blocked_rows),
        "region1_forest_plan_added_profile_count": len(added_rows),
        "region1_forest_plan_added_profiles_with_eval_fixture_count": sum(
            1 for row in added_rows if _region1_profile_meets_eval_fixture_floor(row)
        ),
        "region1_forest_plan_promoted_profiles_with_eval_fixture_count": sum(
            1 for row in promoted_rows if _region1_profile_meets_eval_fixture_floor(row)
        ),
        "region1_forest_plan_completeness_claim": bool(
            readiness.get("region1_completeness_claim")
        ),
        "region1_field_directive_requirement_count": len(field_directive_requirements),
        "region1_overlay_requirement_count": len(overlay_requirements),
        "region1_field_directive_requirement_graph_node_count": sum(
            1
            for requirement in field_directive_requirements
            if requirement.get("requirement_id")
        ),
        "region1_overlay_requirement_graph_node_count": sum(
            1 for requirement in overlay_requirements if requirement.get("overlay_id")
        ),
        "region1_support_document_corpus_catalog_source_record_count": support_document_summary.get(
            "catalog_source_record_count"
        ),
        "region1_support_document_corpus_source_delta_count": support_document_summary.get(
            "support_document_source_delta_count"
        ),
        "region1_support_document_corpus_catalog_confirmed_source_record_count": support_document_summary.get(
            "catalog_confirmed_source_record_count"
        ),
        "region1_support_document_corpus_official_source_gap_count": support_document_summary.get(
            "official_source_gap_count"
        ),
        "region1_support_document_corpus_extracted_source_record_count": support_document_summary.get(
            "extracted_support_document_source_record_count"
        ),
        "region1_support_document_corpus_blocked_source_record_count": support_document_summary.get(
            "blocked_support_document_source_record_count"
        ),
        "region1_support_document_corpus_indexed_source_record_count": support_document_summary.get(
            "indexed_support_document_source_record_count"
        ),
        "region1_support_document_corpus_tracking_only_ready_count": support_document_summary.get(
            "tracking_only_ready_count"
        ),
        "region1_support_document_corpus_tracking_only_blocked_count": support_document_summary.get(
            "tracking_only_blocked_count"
        ),
    }


def _region1_profile_meets_eval_fixture_floor(row: dict[str, Any]) -> bool:
    coverage = _dict(row.get("applicability_eval_coverage"))
    fixture_family_ids = {str(value) for value in _strings(coverage.get("fixture_family_ids"))}
    if str(coverage.get("status") or "") != "covered":
        return False
    if int(coverage.get("positive_case_count") or 0) < 1:
        return False
    if int(coverage.get("hard_negative_case_count") or 0) < 1:
        return False

    profile_kind = str(row.get("profile_kind") or "")
    if profile_kind == "active_profile":
        return "selected_profile_component_eval_seed" in fixture_family_ids
    if row.get("milestone_5_added_profile"):
        return (
            int(coverage.get("selected_profile_compliance_case_count") or 0) >= 1
            and {
                "scope_positive",
                "custer_hard_negative",
                "non_selected_non_custer_hard_negative",
            }
            <= fixture_family_ids
        )
    if profile_kind == "region1_tracking_only":
        return (
            int(coverage.get("positive_case_count") or 0) >= 2
            and int(coverage.get("hard_negative_case_count") or 0) >= 2
            and {
                "scope_positive",
                "scope_positive_with_ambiguous_context",
                "custer_hard_negative",
                "non_selected_non_custer_hard_negative",
            }
            <= fixture_family_ids
        )
    return True
