from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .forest_plan_components import run_forest_plan_component_evaluation
from .forest_plan_components_models import DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .retrieval import default_index_path
from .review_package_support import discover_package_files
from .review_package_support import extract_package_files
from .review_package_support import load_package_cache
from .review_package_support import prepare_review_outputs
from .review_package_support import source_set_id_from_catalog
from .review_package_support import source_set_id_from_index
from .review_package_support import write_json
from .review_package_support import write_jsonl
from .forest_plan_resolver_models import DEFAULT_FOREST_PLAN_PROFILE_ID
from .forest_plan_resolver_models import ForestPlanResolverResult
from .forest_plan_resolver_models import SAFE_ID_RE
from .forest_plan_resolver_models import _load_resolver_profile
from .forest_plan_resolver_models import _is_profile_scope
from .forest_plan_resolver_models import _safe_id
from .forest_plan_resolver_scope import _context_report
from .forest_plan_resolver_scope import _resolve_scope
from .forest_plan_resolver_validation import _needs_reviewer_resolution
from .forest_plan_resolver_validation import _retrieval_readiness_report
from .forest_plan_resolver_validation import _summary
from .forest_plan_resolver_validation import _validation_report

def run_forest_plan_resolver(
    *,
    package_path: Path,
    output_dir: Path,
    forest_unit_id: str = DEFAULT_FOREST_PLAN_PROFILE_ID,
    profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    source_set_id: str | None = None,
    index_path: Path | None = None,
    review_id: str | None = None,
    results_dir: Path | None = None,
    source_top_k: int = 2,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
    reuse_package_cache: bool = False,
    component_inventory_path: Path | None = None,
) -> ForestPlanResolverResult:
    """Resolve forest-plan context from a local EA package."""

    package_path = Path(package_path)
    output_dir = Path(output_dir)
    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")
    if not package_path.exists():
        raise FileNotFoundError(f"Missing EA package path: {package_path}")
    resolver_profile = _load_resolver_profile(
        forest_unit_id=forest_unit_id,
        profiles_path=profiles_path,
    )

    review_id = review_id or _default_review_id(package_path)
    _validate_safe_id(review_id, "review_id")
    review_dir = Path(results_dir) if results_dir else output_dir / "reviews" / review_id
    package_dir = review_dir / "package"
    extracted_text_dir = package_dir / "extracted_text"
    docling_json_dir = package_dir / "docling_json"
    package_manifest_path = package_dir / "package_manifest.jsonl"
    package_chunks_path = package_dir / "package_chunks.jsonl"
    context_path = review_dir / "forest_plan_context.json"
    validation_path = review_dir / "forest_plan_context_validation.json"
    summary_path = review_dir / "forest_plan_context_summary.json"
    component_findings_output_path = review_dir / "forest_plan_component_findings.json"
    component_markdown_output_path = review_dir / "forest_plan_component_findings.md"
    component_queue_output_path = review_dir / "forest_plan_reviewer_resolution_queue.json"
    component_inventory_coverage_output_path = (
        review_dir / "forest_plan_component_inventory_coverage.json"
    )
    applicable_standard_coverage_output_path = (
        review_dir / "forest_plan_applicable_standard_coverage.json"
    )

    prepare_review_outputs(
        package_dir=package_dir,
        output_paths=(
            context_path,
            validation_path,
            summary_path,
            component_findings_output_path,
            component_markdown_output_path,
            component_queue_output_path,
            component_inventory_coverage_output_path,
            applicable_standard_coverage_output_path,
        ),
        preserve_package_cache=reuse_package_cache,
    )

    if reuse_package_cache:
        package_manifest, package_chunks = load_package_cache(
            package_manifest_path=package_manifest_path,
            package_chunks_path=package_chunks_path,
        )
    else:
        for directory in (extracted_text_dir, docling_json_dir):
            directory.mkdir(parents=True, exist_ok=True)
        package_manifest, package_chunks = extract_package_files(
            package_files=discover_package_files(package_path),
            review_id=review_id,
            extracted_text_dir=extracted_text_dir,
            docling_json_dir=docling_json_dir,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            docling_ocr=docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
        )
        write_jsonl(package_manifest_path, package_manifest)
        write_jsonl(package_chunks_path, package_chunks)

    scope = _resolve_scope(package_chunks, resolver_profile=resolver_profile)
    retrieval_readiness = None
    if _is_profile_scope(scope, resolver_profile):
        if index_path is None:
            index_path = default_index_path(output_dir, source_set_id)
        index_path = Path(index_path)
        if not index_path.exists():
            raise FileNotFoundError(f"Missing source-library retrieval index: {index_path}")
        if source_set_id is None:
            source_set_id = source_set_id_from_index(index_path) or source_set_id_from_catalog(
                output_dir
            )
        retrieval_readiness = _retrieval_readiness_report(
            index_path=index_path,
            source_set_id=source_set_id,
            required_source_record_ids=resolver_profile.required_source_record_ids,
            optional_source_record_ids=tuple(
                record.source_record_id
                for role, record in resolver_profile.profile.supporting_source_record_ids_by_role.items()
                if role == "planning_page"
            ),
        )
        if (
            not retrieval_readiness["passed"]
            and resolver_profile.profile.forest_unit_id == DEFAULT_FOREST_PLAN_PROFILE_ID
        ):
            failed = ", ".join(
                check["name"] for check in retrieval_readiness["checks"] if not check["passed"]
            )
            raise ValueError(
                "Forest-plan resolver requires a reviewer-ready source-library retrieval index. "
                f"Failed readiness checks: {failed}"
            )

    context = _context_report(
        review_id=review_id,
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=Path(index_path) if index_path else None,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        scope=scope,
        resolver_profile=resolver_profile,
        source_top_k=source_top_k,
        source_record_readiness=(
            retrieval_readiness.get("required_source_records")
            if retrieval_readiness
            else None
        ),
    )
    validation = _validation_report(context, resolver_profile=resolver_profile)
    context["validation"] = validation
    context["needs_reviewer_resolution"] = _needs_reviewer_resolution(
        context,
        validation,
        resolver_profile=resolver_profile,
    )
    component_evaluation_summary = None
    component_findings_path = None
    component_markdown_path = None
    component_queue_path = None
    component_inventory_coverage_path = None
    applicable_standard_coverage_path = None
    should_run_component_evaluation = (
        retrieval_readiness is None
        or bool(retrieval_readiness.get("passed"))
        or component_inventory_path is not None
    )
    if _is_profile_scope(context, resolver_profile) and should_run_component_evaluation:
        resolved_component_inventory_path = _resolve_component_inventory_path(
            component_inventory_path=component_inventory_path,
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        component_result = run_forest_plan_component_evaluation(
            review_id=review_id,
            review_dir=review_dir,
            context=context,
            package_chunks=package_chunks,
            component_inventory_path=resolved_component_inventory_path,
            forest_unit_id=resolver_profile.profile.forest_unit_id,
            source_set_id=source_set_id,
            index_path=Path(index_path) if index_path else None,
            package_top_k=source_top_k,
            source_top_k=source_top_k,
        )
        component_evaluation_summary = component_result.summary
        component_findings_path = component_result.findings_path
        component_markdown_path = component_result.markdown_path
        component_queue_path = component_result.reviewer_resolution_queue_path
        component_inventory_coverage_path = component_result.component_inventory_coverage_path
        applicable_standard_coverage_path = component_result.applicable_standard_coverage_path
    summary = _summary(
        context=context,
        validation=validation,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        context_path=context_path,
        validation_path=validation_path,
        summary_path=summary_path,
        retrieval_readiness=retrieval_readiness,
        component_evaluation_summary=component_evaluation_summary,
    )

    write_json(context_path, context)
    write_json(validation_path, validation)
    write_json(summary_path, summary)
    return ForestPlanResolverResult(
        review_id=review_id,
        review_dir=review_dir,
        package_manifest_path=package_manifest_path,
        package_chunks_path=package_chunks_path,
        context_path=context_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
        component_findings_path=component_findings_path,
        component_markdown_path=component_markdown_path,
        component_reviewer_resolution_queue_path=component_queue_path,
        component_inventory_coverage_path=component_inventory_coverage_path,
        applicable_standard_coverage_path=applicable_standard_coverage_path,
    )

def _resolve_component_inventory_path(
    *,
    component_inventory_path: Path | None,
    output_dir: Path,
    source_set_id: str | None,
) -> Path:
    if component_inventory_path is not None:
        return Path(component_inventory_path)
    if source_set_id:
        source_set_inventory_path = (
            output_dir
            / "derived"
            / source_set_id
            / "forest_plan_components"
            / "component_inventory.json"
        )
        if source_set_inventory_path.exists():
            return source_set_inventory_path
        raise FileNotFoundError(
            "Missing source-set forest-plan component inventory: "
            f"{source_set_inventory_path}. Run forest-plan-components-build for "
            "the active source set or pass --forest-plan-component-inventory-path."
        )
    return DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH

def _default_review_id(package_path: Path) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"forest-plan-context-{_safe_id(package_path.stem or package_path.name)}-{stamp}"

def _validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dot, underscore, or hyphen."
        )
