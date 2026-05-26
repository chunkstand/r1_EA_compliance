from __future__ import annotations

from collections import Counter
from .forest_plan_inventory_build_manifest import DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH, load_region1_forest_plan_inventory_build_manifest
from pathlib import Path

from .forest_plan_components_common import _safe_identifier, _utc_now
from .forest_plan_components_inventory_detection import _components_from_chunk
from .forest_plan_components_inventory_quality import _component_inventory_build_coverage, _merge_overlapping_component_records, _profile_context_terms
from .forest_plan_components_models import FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION, ForestPlanComponentInventoryBuildResult, _ForestPlanInventoryProfileBuild
from .forest_plan_components_runtime import _parse_component
from .forest_plan_components_validation import _read_jsonl, _write_json, _write_jsonl


def build_forest_plan_component_inventory(
    *,
    output_dir: Path,
    source_set_id: str,
    source_record_id: str | None = None,
    forest_unit_id: str | None = None,
    plan_version: str | None = None,
    chunks_path: Path | None = None,
    geographic_area_ids: list[str] | None = None,
    management_area_ids: list[str] | None = None,
    overlay_ids: list[str] | None = None,
    manifest_path: Path | None = None,
    manifest_readiness_path: Path = DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH,
) -> ForestPlanComponentInventoryBuildResult:
    """Build a source-set forest-plan component inventory from labeled plan chunks."""

    output_dir = Path(output_dir)
    chunks_path = chunks_path or (
        output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    )
    component_dir = output_dir / "derived" / source_set_id / "forest_plan_components"
    inventory_path = component_dir / "component_inventory.json"
    components_jsonl_path = component_dir / "components.jsonl"
    coverage_path = component_dir / "component_inventory_build_coverage.json"
    summary_path = component_dir / "summary.json"
    all_chunks = _read_jsonl(chunks_path)
    manifest_path = Path(manifest_path) if manifest_path is not None else None
    if manifest_path is None:
        if not source_record_id:
            raise ValueError("source_record_id is required when manifest_path is not provided.")
        if not plan_version:
            raise ValueError("plan_version is required when manifest_path is not provided.")
        selected_forest_unit_id = forest_unit_id or "custer-gallatin-nf"
        chunks = _selected_forest_plan_chunks(
            all_chunks,
            source_set_id=source_set_id,
            source_record_ids=(source_record_id,),
        )
        components = _build_components_for_forest(
            chunks=chunks,
            forest_unit_id=selected_forest_unit_id,
            plan_version=plan_version,
            source_set_id=source_set_id,
            geographic_area_ids=geographic_area_ids,
            management_area_ids=management_area_ids,
            overlay_ids=overlay_ids,
        )
        validation_errors = _component_validation_errors(components)
        coverage = _component_inventory_build_coverage(
            source_set_id=source_set_id,
            source_record_ids=(source_record_id,),
            chunks_path=chunks_path,
            chunks=chunks,
            components=components,
            validation_errors=validation_errors,
        )
        inventory = {
            "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
            "inventory_id": _safe_identifier(f"{selected_forest_unit_id}-{plan_version}-components"),
            "forest_unit_id": selected_forest_unit_id,
            "plan_version": plan_version,
            "source_set_id": source_set_id,
            "build_scope": "single_forest",
            "components": components,
        }
        summary = _component_inventory_build_summary(
            source_set_id=source_set_id,
            chunks_path=chunks_path,
            inventory_path=inventory_path,
            components_jsonl_path=components_jsonl_path,
            coverage_path=coverage_path,
            component_count=len(components),
            component_type_counts=dict(
                Counter(component["component_type"] for component in components)
            ),
            standard_count=sum(
                1 for component in components if component["component_type"] == "standard"
            ),
            coverage=coverage,
            source_record_ids=(source_record_id,),
            forest_unit_ids=(selected_forest_unit_id,),
            build_scope="single_forest",
        )
    else:
        if source_record_id is not None or plan_version is not None:
            raise ValueError(
                "source_record_id and plan_version are not supported with manifest_path."
            )
        if geographic_area_ids or management_area_ids or overlay_ids:
            raise ValueError(
                "geographic_area_ids, management_area_ids, and overlay_ids are not supported "
                "with manifest_path."
            )
        manifest = load_region1_forest_plan_inventory_build_manifest(
            manifest_path,
            readiness_path=manifest_readiness_path,
        )
        selected_rows = _manifest_profile_rows_for_source_set(
            manifest,
            source_set_id=source_set_id,
            forest_unit_id=forest_unit_id,
        )
        profile_builds: list[_ForestPlanInventoryProfileBuild] = []
        components = []
        all_selected_chunks = []
        validation_errors = []
        for row in selected_rows:
            row_chunks = _selected_forest_plan_chunks(
                all_chunks,
                source_set_id=source_set_id,
                source_record_ids=row.component_source_record_ids,
            )
            row_components = _build_components_for_forest(
                chunks=row_chunks,
                forest_unit_id=row.forest_unit_id,
                plan_version=row.plan_version,
                source_set_id=source_set_id,
            )
            row_validation_errors = _component_validation_errors(row_components)
            row_coverage = _component_inventory_build_coverage(
                source_set_id=source_set_id,
                source_record_ids=row.source_record_ids,
                chunks_path=chunks_path,
                chunks=row_chunks,
                components=row_components,
                validation_errors=row_validation_errors,
            )
            profile_builds.append(
                _ForestPlanInventoryProfileBuild(
                    forest_unit_id=row.forest_unit_id,
                    plan_version=row.plan_version,
                    primary_plan_source_record_id=row.primary_plan_source_record_id,
                    source_record_ids=row.component_source_record_ids,
                    coverage=row_coverage,
                )
            )
            all_selected_chunks.extend(row_chunks)
            components.extend(row_components)
            validation_errors.extend(row_validation_errors)
        coverage = _component_inventory_build_coverage(
            source_set_id=source_set_id,
            source_record_ids=tuple(
                source_record_id
                for profile_build in profile_builds
                for source_record_id in profile_build.source_record_ids
            ),
            chunks_path=chunks_path,
            chunks=all_selected_chunks,
            components=components,
            validation_errors=validation_errors,
            profile_builds=profile_builds,
        )
        inventory = {
            "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
            "inventory_id": _safe_identifier(f"{source_set_id}-region1-components"),
            "source_set_id": source_set_id,
            "build_scope": "manifest_batch",
            "forest_unit_ids": [profile_build.forest_unit_id for profile_build in profile_builds],
            "profile_builds": [
                {
                    "forest_unit_id": profile_build.forest_unit_id,
                    "plan_version": profile_build.plan_version,
                    "primary_plan_source_record_id": (
                        profile_build.primary_plan_source_record_id
                    ),
                    "source_record_ids": list(profile_build.source_record_ids),
                }
                for profile_build in profile_builds
            ],
            "components": components,
        }
        summary = _component_inventory_build_summary(
            source_set_id=source_set_id,
            chunks_path=chunks_path,
            inventory_path=inventory_path,
            components_jsonl_path=components_jsonl_path,
            coverage_path=coverage_path,
            component_count=len(components),
            component_type_counts=dict(
                Counter(component["component_type"] for component in components)
            ),
            standard_count=sum(
                1 for component in components if component["component_type"] == "standard"
            ),
            coverage=coverage,
            source_record_ids=tuple(
                source_record_id
                for profile_build in profile_builds
                for source_record_id in profile_build.source_record_ids
            ),
            forest_unit_ids=tuple(
                profile_build.forest_unit_id for profile_build in profile_builds
            ),
            build_scope="manifest_batch",
            manifest_path=manifest_path,
        )
    component_dir.mkdir(parents=True, exist_ok=True)
    _write_json(inventory_path, inventory)
    _write_jsonl(components_jsonl_path, components)
    _write_json(coverage_path, coverage)
    _write_json(summary_path, summary)
    return ForestPlanComponentInventoryBuildResult(
        inventory_path=inventory_path,
        components_jsonl_path=components_jsonl_path,
        coverage_path=coverage_path,
        summary_path=summary_path,
        summary=summary,
    )


def _manifest_profile_rows_for_source_set(
    manifest,
    *,
    source_set_id: str,
    forest_unit_id: str | None,
) -> list:
    selected_rows = [
        row
        for row in manifest.profile_rows
        if manifest.source_set_reference(row.source_set_reference_id).matches_source_set(
            source_set_id
        )
    ]
    if forest_unit_id is not None:
        selected_rows = [
            row for row in selected_rows if row.forest_unit_id == forest_unit_id
        ]
        if not selected_rows:
            raise ValueError(
                "manifest_path does not define a build row for "
                f"forest_unit_id={forest_unit_id!r} and source_set_id={source_set_id!r}."
            )
    if not selected_rows:
        raise ValueError(
            "manifest_path does not define any build rows for "
            f"source_set_id={source_set_id!r}."
        )
    return selected_rows


def _selected_forest_plan_chunks(
    all_chunks: list[dict],
    *,
    source_set_id: str,
    source_record_ids: tuple[str, ...],
) -> list[dict]:
    selected_source_record_ids = set(source_record_ids)
    return [
        chunk
        for chunk in all_chunks
        if chunk.get("source_set_id") == source_set_id
        and chunk.get("source_record_id") in selected_source_record_ids
        and chunk.get("document_role") in {"forest_plan", "forest_plan_support"}
    ]


def _build_components_for_forest(
    *,
    chunks: list[dict],
    forest_unit_id: str,
    plan_version: str,
    source_set_id: str,
    geographic_area_ids: list[str] | None = None,
    management_area_ids: list[str] | None = None,
    overlay_ids: list[str] | None = None,
) -> list[dict]:
    components = []
    profile_context = _profile_context_terms(forest_unit_id)
    for chunk in chunks:
        components.extend(
            _components_from_chunk(
                chunk=chunk,
                forest_unit_id=forest_unit_id,
                plan_version=plan_version,
                source_set_id=source_set_id,
                geographic_area_ids=geographic_area_ids or [],
                management_area_ids=management_area_ids or [],
                overlay_ids=overlay_ids or [],
                profile_context=profile_context,
            )
        )
    return _merge_overlapping_component_records(components)


def _component_validation_errors(components: list[dict]) -> list[dict]:
    validation_errors = []
    for index, component in enumerate(components):
        try:
            _parse_component(component, f"built components[{index}]")
        except ValueError as error:
            validation_errors.append(
                {
                    "component_id": component.get("component_id"),
                    "index": index,
                    "error": str(error),
                }
            )
    return validation_errors


def _component_inventory_build_summary(
    *,
    source_set_id: str,
    chunks_path: Path,
    inventory_path: Path,
    components_jsonl_path: Path,
    coverage_path: Path,
    component_count: int,
    component_type_counts: dict[str, int],
    standard_count: int,
    coverage: dict,
    source_record_ids: tuple[str, ...],
    forest_unit_ids: tuple[str, ...],
    build_scope: str,
    manifest_path: Path | None = None,
) -> dict:
    summary = {
        "schema_version": "forest-plan-component-inventory-build-summary-v0",
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "source_record_ids": list(source_record_ids),
        "forest_unit_ids": list(forest_unit_ids),
        "build_scope": build_scope,
        "chunks_path": str(chunks_path),
        "inventory_path": str(inventory_path),
        "components_jsonl_path": str(components_jsonl_path),
        "coverage_path": str(coverage_path),
        "component_count": component_count,
        "component_type_counts": component_type_counts,
        "standard_count": standard_count,
        "inventory_quality_issue_count": coverage["inventory_quality_issue_count"],
        "blocking_inventory_quality_issue_count": coverage[
            "blocking_inventory_quality_issue_count"
        ],
        "component_source_accuracy_passed": coverage[
            "component_source_accuracy_passed"
        ],
        "component_source_accuracy_failure_count": coverage[
            "component_source_accuracy_failure_count"
        ],
        "coverage_passed": coverage["passed"],
        "passed": coverage["passed"],
    }
    if len(source_record_ids) == 1:
        summary["source_record_id"] = source_record_ids[0]
    if len(forest_unit_ids) == 1:
        summary["forest_unit_id"] = forest_unit_ids[0]
    if manifest_path is not None:
        summary["manifest_path"] = str(manifest_path)
    profile_results = coverage.get("profile_results", [])
    blocked_profile_results = [
        row for row in profile_results if not row.get("passed")
    ]
    if profile_results:
        summary["profile_result_count"] = len(profile_results)
        summary["blocked_forest_unit_ids"] = [
            row["forest_unit_id"] for row in blocked_profile_results
        ]
        summary["profile_blocker_types_by_forest_unit"] = {
            row["forest_unit_id"]: row.get("blocker_types", [])
            for row in blocked_profile_results
        }
    return summary
