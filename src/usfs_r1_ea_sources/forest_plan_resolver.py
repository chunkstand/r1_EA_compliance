from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import shutil
import sqlite3

from .ea_review import _discover_package_files
from .ea_review import _extract_package_files
from .ea_review import _load_package_cache
from .ea_review import _source_set_id_from_catalog
from .ea_review import _source_set_id_from_index
from .ea_review import _utc_now
from .forest_plan_components import DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH
from .forest_plan_components import run_forest_plan_component_evaluation
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import ForestPlanProfile
from .forest_plan_profiles import ForestPlanProfileCollection
from .forest_plan_profiles import ForestPlanTermEntry
from .forest_plan_profiles import KnownForestUnit
from .forest_plan_profiles import SupportingRecordTriggerRule
from .forest_plan_profiles import load_forest_plan_profiles
from .retrieval import default_index_path
from .retrieval import query_retrieval_index


FOREST_PLAN_CONTEXT_SCHEMA_VERSION = "forest-plan-context-v0"
CUSTER_GALLATIN_FOREST_UNIT_ID = "custer-gallatin-nf"
DEFAULT_FOREST_PLAN_PROFILE_ID = CUSTER_GALLATIN_FOREST_UNIT_ID
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ForestPlanResolverResult:
    review_id: str
    review_dir: Path
    package_manifest_path: Path
    package_chunks_path: Path
    context_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict
    component_findings_path: Path | None = None
    component_markdown_path: Path | None = None
    component_reviewer_resolution_queue_path: Path | None = None
    component_inventory_coverage_path: Path | None = None
    applicable_standard_coverage_path: Path | None = None


@dataclass(frozen=True)
class GazetteerEntry:
    entry_id: str
    category: str
    name: str
    aliases: tuple[str, ...] = ()
    source_record_id: str | None = None

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


@dataclass(frozen=True)
class PlanEvidenceRoute:
    route_id: str
    category: str
    name: str
    source_record_id: str
    source_role: str
    package_terms: tuple[str, ...]
    source_query: str
    source_terms: tuple[str, ...]
    trigger_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class ForestPlanResolverProfile:
    profile: ForestPlanProfile
    known_other_forest_units: tuple[KnownForestUnit, ...]
    scope_status: str
    out_of_scope_status: str
    source_records: tuple[dict[str, str], ...]
    required_source_record_ids: tuple[str, ...]
    ranger_district_entries: tuple[GazetteerEntry, ...]
    geographic_area_entries: tuple[GazetteerEntry, ...]
    management_area_entries: tuple[GazetteerEntry, ...]
    overlay_entries: tuple[GazetteerEntry, ...]
    supporting_plan_evidence_routes: tuple[PlanEvidenceRoute, ...]


def _load_resolver_profile(
    forest_unit_id: str = DEFAULT_FOREST_PLAN_PROFILE_ID,
    profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
) -> ForestPlanResolverProfile:
    collection = load_forest_plan_profiles(Path(profiles_path))
    profile = collection.get(forest_unit_id)
    return _resolver_profile_from_profile(
        profile=profile,
        known_other_forest_units=_known_other_forest_units_for_profile(
            collection=collection,
            selected_profile=profile,
        ),
    )


def _known_other_forest_units_for_profile(
    *,
    collection: ForestPlanProfileCollection,
    selected_profile: ForestPlanProfile,
) -> tuple[KnownForestUnit, ...]:
    units_by_id = {
        unit.forest_unit_id: unit
        for unit in collection.known_other_forest_units
        if unit.forest_unit_id != selected_profile.forest_unit_id
    }
    for profile in collection.profiles:
        if profile.forest_unit_id == selected_profile.forest_unit_id:
            continue
        units_by_id.setdefault(
            profile.forest_unit_id,
            KnownForestUnit(
                forest_unit_id=profile.forest_unit_id,
                names=profile.forest_unit_names,
            ),
        )
    return tuple(units_by_id.values())


def _resolver_profile_from_profile(
    *,
    profile: ForestPlanProfile,
    known_other_forest_units: tuple[KnownForestUnit, ...],
) -> ForestPlanResolverProfile:
    return ForestPlanResolverProfile(
        profile=profile,
        known_other_forest_units=known_other_forest_units,
        scope_status=_scope_status_for_profile(profile),
        out_of_scope_status=_out_of_scope_status_for_profile(profile),
        source_records=_source_records_for_profile(profile),
        required_source_record_ids=profile.required_source_record_ids,
        ranger_district_entries=_gazetteer_entries(profile.ranger_district_terms),
        geographic_area_entries=_gazetteer_entries(profile.geographic_area_terms),
        management_area_entries=_gazetteer_entries(profile.management_area_terms),
        overlay_entries=_gazetteer_entries(profile.overlay_terms),
        supporting_plan_evidence_routes=_supporting_routes_for_profile(
            profile.supporting_record_trigger_rules
        ),
    )


def _scope_status_for_profile(profile: ForestPlanProfile) -> str:
    if profile.forest_unit_id == CUSTER_GALLATIN_FOREST_UNIT_ID:
        return "custer_gallatin"
    status = re.sub(r"[^A-Za-z0-9_.-]+", "-", profile.forest_unit_id).strip("-")
    return status.replace("-", "_") or "forest_plan_profile"


def _out_of_scope_status_for_profile(profile: ForestPlanProfile) -> str:
    if profile.forest_unit_id == CUSTER_GALLATIN_FOREST_UNIT_ID:
        return "not_custer_gallatin"
    return "not_selected_forest_unit"


def _source_records_for_profile(profile: ForestPlanProfile) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "source_record_id": record.source_record_id,
            "role": record.role,
            "required_for": record.required_for,
        }
        for record in profile.supporting_source_records
    )


def _gazetteer_entries(
    profile_terms: tuple[ForestPlanTermEntry, ...],
) -> tuple[GazetteerEntry, ...]:
    return tuple(
        GazetteerEntry(
            entry.entry_id,
            entry.category,
            entry.name,
            entry.aliases,
            entry.source_record_id,
        )
        for entry in profile_terms
    )


def _supporting_routes_for_profile(
    rules: tuple[SupportingRecordTriggerRule, ...],
) -> tuple[PlanEvidenceRoute, ...]:
    return tuple(
        PlanEvidenceRoute(
            route_id=rule.route_id,
            category=rule.category,
            name=rule.name,
            source_record_id=rule.source_record_id,
            source_role=rule.target_source_role,
            package_terms=rule.package_terms,
            source_query=rule.source_query,
            source_terms=rule.source_terms,
            trigger_terms=rule.trigger_terms,
        )
        for rule in rules
    )


_DEFAULT_RESOLVER_PROFILE = _load_resolver_profile()
CUSTER_GALLATIN_PLAN_SOURCE_ID = _DEFAULT_RESOLVER_PROFILE.profile.active_plan_source_record_id
CUSTER_GALLATIN_SOURCE_RECORDS = [
    dict(record) for record in _DEFAULT_RESOLVER_PROFILE.source_records
]
CUSTER_GALLATIN_REQUIRED_SOURCE_IDS = _DEFAULT_RESOLVER_PROFILE.required_source_record_ids
SUPPORTING_PLAN_EVIDENCE_ROUTES = _DEFAULT_RESOLVER_PROFILE.supporting_plan_evidence_routes
FOREST_UNIT_ALIASES = _DEFAULT_RESOLVER_PROFILE.profile.forest_unit_names
NON_CUSTER_FOREST_ALIASES = {
    unit.names[0]: unit.names for unit in _DEFAULT_RESOLVER_PROFILE.known_other_forest_units
}
AMBIGUOUS_FOREST_CUES = _DEFAULT_RESOLVER_PROFILE.profile.ambiguous_unit_terms
LOCATION_ENTRIES = _DEFAULT_RESOLVER_PROFILE.ranger_district_entries
GEOGRAPHIC_AREA_ENTRIES = _DEFAULT_RESOLVER_PROFILE.geographic_area_entries
MANAGEMENT_AREA_ENTRIES = _DEFAULT_RESOLVER_PROFILE.management_area_entries
OVERLAY_ENTRIES = _DEFAULT_RESOLVER_PROFILE.overlay_entries


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

    _prepare_outputs(
        package_dir=package_dir,
        context_path=context_path,
        validation_path=validation_path,
        summary_path=summary_path,
        component_findings_path=component_findings_output_path,
        component_markdown_path=component_markdown_output_path,
        component_queue_path=component_queue_output_path,
        component_inventory_coverage_path=component_inventory_coverage_output_path,
        applicable_standard_coverage_path=applicable_standard_coverage_output_path,
        preserve_package_cache=reuse_package_cache,
    )

    if reuse_package_cache:
        package_manifest, package_chunks = _load_package_cache(
            package_manifest_path=package_manifest_path,
            package_chunks_path=package_chunks_path,
        )
    else:
        for directory in (extracted_text_dir, docling_json_dir):
            directory.mkdir(parents=True, exist_ok=True)
        package_manifest, package_chunks = _extract_package_files(
            package_files=_discover_package_files(package_path),
            review_id=review_id,
            extracted_text_dir=extracted_text_dir,
            docling_json_dir=docling_json_dir,
            extracted_at=_utc_now(),
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            docling_ocr=docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
        )
        _write_jsonl(package_manifest_path, package_manifest)
        _write_jsonl(package_chunks_path, package_chunks)

    scope = _resolve_scope(package_chunks, resolver_profile=resolver_profile)
    retrieval_readiness = None
    if _is_profile_scope(scope, resolver_profile):
        if index_path is None:
            index_path = default_index_path(output_dir, source_set_id)
        index_path = Path(index_path)
        if not index_path.exists():
            raise FileNotFoundError(f"Missing source-library retrieval index: {index_path}")
        if source_set_id is None:
            source_set_id = _source_set_id_from_index(index_path) or _source_set_id_from_catalog(
                output_dir
            )
        retrieval_readiness = _retrieval_readiness_report(
            index_path=index_path,
            source_set_id=source_set_id,
            required_source_record_ids=resolver_profile.required_source_record_ids,
        )
        if not retrieval_readiness["passed"]:
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
    if _is_profile_scope(context, resolver_profile):
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

    _write_json(context_path, context)
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
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
    return DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH


def _prepare_outputs(
    *,
    package_dir: Path,
    context_path: Path,
    validation_path: Path,
    summary_path: Path,
    component_findings_path: Path | None,
    component_markdown_path: Path | None,
    component_queue_path: Path | None,
    component_inventory_coverage_path: Path | None,
    applicable_standard_coverage_path: Path | None,
    preserve_package_cache: bool,
) -> None:
    if package_dir.exists() and not preserve_package_cache:
        shutil.rmtree(package_dir)
    for path in (
        context_path,
        validation_path,
        summary_path,
        component_findings_path,
        component_markdown_path,
        component_queue_path,
        component_inventory_coverage_path,
        applicable_standard_coverage_path,
    ):
        if path is not None:
            path.unlink(missing_ok=True)


def _resolve_scope(
    package_chunks: list[dict],
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    profile_mentions = _mentions_for_aliases(
        package_chunks,
        name=resolver_profile.profile.forest_unit_names[0],
        category="forest_unit",
        aliases=resolver_profile.profile.forest_unit_names,
        limit=None,
    )
    other_forest_mentions = []
    for unit in resolver_profile.known_other_forest_units:
        other_forest_mentions.extend(
            _mentions_for_aliases(
                package_chunks,
                name=unit.names[0],
                category="forest_unit",
                aliases=unit.names,
                limit=None,
            )
        )
    profile_district_scope_mentions, profile_district_background_mentions = (
        _profile_district_location_mentions(package_chunks, resolver_profile=resolver_profile)
    )
    profile_scope_mentions = [
        mention for mention in profile_mentions if _is_scope_decisive_mention(mention)
    ]
    profile_background_mentions = [
        mention for mention in profile_mentions if not _is_scope_decisive_mention(mention)
    ]
    blocking_other_forest_mentions = [
        mention for mention in other_forest_mentions if _is_scope_decisive_mention(mention)
    ]
    other_background_mentions = [
        mention for mention in other_forest_mentions if not _is_scope_decisive_mention(mention)
    ]
    selected_profile_scope_mentions = profile_scope_mentions or profile_district_scope_mentions
    ambiguous_mentions = []
    if not selected_profile_scope_mentions:
        ambiguous_mentions = _mentions_for_aliases(
            package_chunks,
            name="ambiguous forest cue",
            category="forest_unit",
            aliases=resolver_profile.profile.ambiguous_unit_terms,
            limit=None,
        )

    if selected_profile_scope_mentions and not blocking_other_forest_mentions:
        status = resolver_profile.scope_status
        forest_unit = {
            "name": resolver_profile.profile.forest_unit_names[0],
            "resolution_basis": (
                "forest_unit_project_location"
                if profile_scope_mentions
                else "profile_district_project_location"
            ),
            "package_evidence": selected_profile_scope_mentions[:5],
        }
    elif blocking_other_forest_mentions and not selected_profile_scope_mentions:
        status = resolver_profile.out_of_scope_status
        forest_unit = {
            "name": blocking_other_forest_mentions[0]["name"],
            "resolution_basis": "other_forest_unit_project_location",
            "package_evidence": blocking_other_forest_mentions[:5],
        }
    else:
        status = "ambiguous"
        forest_unit = None

    unresolved = []
    if selected_profile_scope_mentions and blocking_other_forest_mentions:
        unresolved.extend(
            _unresolved_from_evidence(
                "multiple_forest_units_mentioned",
                blocking_other_forest_mentions,
            )
        )
    if (
        status == "ambiguous"
        and not selected_profile_scope_mentions
        and not blocking_other_forest_mentions
        and profile_background_mentions
    ):
        unresolved.extend(
            _unresolved_from_evidence(
                "profile_forest_unit_mention_not_project_location",
                profile_background_mentions[:5],
            )
        )
    if ambiguous_mentions:
        unresolved.extend(_unresolved_from_evidence("ambiguous_forest_unit", ambiguous_mentions))
    if (
        not selected_profile_scope_mentions
        and not blocking_other_forest_mentions
        and not ambiguous_mentions
        and not profile_background_mentions
        and not other_background_mentions
        and not profile_district_background_mentions
    ):
        unresolved.append(
            {
                "category": "forest_unit",
                "reason": "forest_unit_not_found",
                "name": None,
                "package_evidence": None,
            }
        )
    return {
        "scope_status": status,
        "forest_unit": forest_unit,
        "unresolved_mentions": unresolved,
        "background_location_mentions": _dedupe_evidence(
            [
                *profile_background_mentions,
                *other_background_mentions,
                *profile_district_background_mentions,
            ]
        )[:20],
    }


def _context_report(
    *,
    review_id: str,
    package_path: Path,
    output_dir: Path,
    source_set_id: str | None,
    index_path: Path | None,
    package_manifest: list[dict],
    package_chunks: list[dict],
    scope: dict,
    resolver_profile: ForestPlanResolverProfile,
    source_top_k: int,
    source_record_readiness: dict | None = None,
) -> dict:
    source_records = (
        [dict(record) for record in resolver_profile.source_records]
        if _is_profile_scope(scope, resolver_profile)
        else []
    )
    project_location_signals = _resolved_entries(
        entries=resolver_profile.ranger_district_entries,
        package_chunks=package_chunks,
        index_path=index_path,
        source_top_k=source_top_k,
        attach_plan_evidence=False,
    )
    if _is_profile_scope(scope, resolver_profile):
        geographic_areas = _resolved_entries(
            entries=resolver_profile.geographic_area_entries,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
        management_areas = _resolved_entries(
            entries=resolver_profile.management_area_entries,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
        overlays = _resolved_entries(
            entries=resolver_profile.overlay_entries,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
        supporting_plan_evidence = _supporting_plan_evidence(
            routes=resolver_profile.supporting_plan_evidence_routes,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
    else:
        geographic_areas = []
        management_areas = []
        overlays = []
        supporting_plan_evidence = []

    unresolved_mentions = list(scope["unresolved_mentions"])
    package_evidence = _flatten_package_evidence(
        [scope["forest_unit"]] if scope.get("forest_unit") else [],
        project_location_signals,
        geographic_areas,
        management_areas,
        overlays,
        supporting_plan_evidence,
    )
    plan_source_evidence = _flatten_plan_source_evidence(
        geographic_areas,
        management_areas,
        overlays,
        supporting_plan_evidence,
    )
    return {
        "schema_version": FOREST_PLAN_CONTEXT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "package_path": str(package_path),
        "output_dir": str(output_dir),
        "source_set_id": source_set_id,
        "index_path": str(index_path) if index_path else None,
        "scope_status": scope["scope_status"],
        "forest_unit": scope["forest_unit"],
        "source_records": source_records,
        "project_location_signals": project_location_signals,
        "geographic_areas": geographic_areas,
        "management_areas": management_areas,
        "overlays": overlays,
        "supporting_plan_evidence": supporting_plan_evidence,
        "source_record_readiness": source_record_readiness,
        "package_evidence": package_evidence,
        "plan_source_evidence": plan_source_evidence,
        "background_location_mentions": scope.get("background_location_mentions", []),
        "unresolved_mentions": unresolved_mentions,
        "needs_reviewer_resolution": False,
        "package_file_count": len(package_manifest),
        "package_chunk_count": len(package_chunks),
    }


def _resolved_entries(
    *,
    entries: tuple[GazetteerEntry, ...],
    package_chunks: list[dict],
    index_path: Path | None,
    source_top_k: int,
    attach_plan_evidence: bool = True,
) -> list[dict]:
    resolved = []
    for entry in entries:
        mentions = _mentions_for_entry(package_chunks, entry)
        has_negative_determination = any(_is_negative_location_context(evidence) for evidence in mentions)
        if not attach_plan_evidence and entry.category == "district":
            package_evidence = [
                evidence for evidence in mentions if _is_project_location_evidence(evidence)
            ]
        else:
            package_evidence = [
                evidence for evidence in mentions if not _is_negative_location_context(evidence)
            ]
            if has_negative_determination:
                package_evidence = [
                    evidence
                    for evidence in package_evidence
                    if _is_affirmative_location_context(evidence)
                ]
        package_evidence = package_evidence[:5]
        if not package_evidence:
            continue
        plan_evidence = []
        if attach_plan_evidence and index_path is not None:
            plan_evidence = _plan_source_evidence(
                entry=entry,
                index_path=index_path,
                limit=source_top_k,
            )
            if not plan_evidence:
                continue
        resolved.append(
            {
                "entry_id": entry.entry_id,
                "category": entry.category,
                "name": entry.name,
                "aliases": list(entry.aliases),
                "source_record_id": entry.source_record_id if attach_plan_evidence else None,
                "package_evidence": package_evidence,
                "plan_source_evidence": plan_evidence,
                "resolution_status": "resolved" if (plan_evidence or not attach_plan_evidence) else "missing_plan_source_evidence",
            }
        )
    return sorted(resolved, key=lambda item: (item["category"], item["name"]))


def _plan_source_evidence(*, entry: GazetteerEntry, index_path: Path, limit: int) -> list[dict]:
    if entry.source_record_id is None:
        return []
    query = " ".join(entry.terms)
    result = query_retrieval_index(
        index_path=index_path,
        query=query,
        limit=max(limit, 5),
        document_role="forest_plan",
        source_record_id=entry.source_record_id,
    )
    filtered = [
        row
        for row in result["results"]
        if _evidence_text_matches_entry(str(row.get("evidence_span", {}).get("text") or ""), entry)
    ]
    return filtered[:limit]


def _supporting_plan_evidence(
    *,
    routes: tuple[PlanEvidenceRoute, ...],
    package_chunks: list[dict],
    index_path: Path | None,
    source_top_k: int,
) -> list[dict]:
    routed_evidence = []
    for route in routes:
        trigger_terms = route.trigger_terms or route.package_terms
        trigger_evidence = _mentions_for_terms(
            package_chunks=package_chunks,
            terms=trigger_terms,
            name=route.name,
            category=route.category,
            entry_id=route.route_id,
        )
        if not trigger_evidence:
            continue
        package_evidence = _mentions_for_route(package_chunks, route)
        if not package_evidence:
            continue
        plan_evidence = []
        if index_path is not None:
            plan_evidence = _supporting_source_evidence(
                route=route,
                index_path=index_path,
                limit=source_top_k,
            )
        routed_evidence.append(
            {
                "entry_id": route.route_id,
                "route_id": route.route_id,
                "category": route.category,
                "name": route.name,
                "source_record_id": route.source_record_id,
                "source_role": route.source_role,
                "package_terms": list(route.package_terms),
                "trigger_terms": list(trigger_terms),
                "trigger_evidence": trigger_evidence,
                "source_query": route.source_query,
                "source_terms": list(route.source_terms),
                "package_evidence": package_evidence,
                "plan_source_evidence": plan_evidence,
                "resolution_status": (
                    "resolved" if plan_evidence else "missing_plan_source_evidence"
                ),
            }
        )
    return sorted(routed_evidence, key=lambda item: item["route_id"])


def _supporting_source_evidence(
    *, route: PlanEvidenceRoute, index_path: Path, limit: int
) -> list[dict]:
    result = query_retrieval_index(
        index_path=index_path,
        query=route.source_query,
        limit=max(limit, 5),
        source_record_id=route.source_record_id,
    )
    filtered = [
        row
        for row in result["results"]
        if _supporting_evidence_matches_route(
            str(row.get("evidence_span", {}).get("text") or ""),
            route,
        )
    ]
    return filtered[:limit]


def _supporting_evidence_matches_route(text: str, route: PlanEvidenceRoute) -> bool:
    return any(_term_found(text, term) for term in route.source_terms)


def _evidence_text_matches_entry(text: str, entry: GazetteerEntry) -> bool:
    return any(_term_found(text, term) for term in entry.terms)


def _mentions_for_entry(package_chunks: list[dict], entry: GazetteerEntry) -> list[dict]:
    mentions = []
    for alias in entry.terms:
        mentions.extend(
            _mentions_for_alias(
                package_chunks,
                name=entry.name,
                category=entry.category,
                entry_id=entry.entry_id,
                alias=alias,
            )
        )
    return _dedupe_evidence(mentions)


def _mentions_for_route(package_chunks: list[dict], route: PlanEvidenceRoute) -> list[dict]:
    return _mentions_for_terms(
        package_chunks=package_chunks,
        terms=route.package_terms,
        name=route.name,
        category=route.category,
        entry_id=route.route_id,
    )


def _mentions_for_terms(
    *,
    package_chunks: list[dict],
    terms: tuple[str, ...],
    name: str,
    category: str,
    entry_id: str,
) -> list[dict]:
    mentions = []
    for alias in terms:
        mentions.extend(
            _mentions_for_alias(
                package_chunks,
                name=name,
                category=category,
                entry_id=entry_id,
                alias=alias,
            )
        )
    return _dedupe_evidence(mentions)[:5]


def _mentions_for_aliases(
    package_chunks: list[dict],
    *,
    name: str,
    category: str,
    aliases: tuple[str, ...],
    limit: int | None = 5,
) -> list[dict]:
    mentions = []
    for alias in aliases:
        mentions.extend(
            _mentions_for_alias(
                package_chunks,
                name=name,
                category=category,
                entry_id=_evidence_id(category, name, alias),
                alias=alias,
            )
        )
    deduped = _dedupe_evidence(mentions)
    if limit is None:
        return deduped
    return deduped[:limit]


def _mentions_for_alias(
    package_chunks: list[dict],
    *,
    name: str,
    category: str,
    entry_id: str,
    alias: str,
) -> list[dict]:
    pattern, case_sensitive = _compiled_alias_pattern(alias)
    mentions = []
    for chunk in package_chunks:
        text = str(chunk.get("text") or "")
        search_text = text if case_sensitive else text.lower()
        for match in pattern.finditer(search_text):
            mentions.append(
                _package_evidence(
                    chunk=chunk,
                    text=text,
                    category=category,
                    entry_id=entry_id,
                    name=name,
                    matched_alias=alias,
                    match_start=match.start(),
                    match_end=match.end(),
                )
            )
    return mentions


def _profile_district_location_mentions(
    package_chunks: list[dict],
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> tuple[list[dict], list[dict]]:
    project_mentions = []
    background_mentions = []
    for entry in resolver_profile.ranger_district_entries:
        for evidence in _mentions_for_entry(package_chunks, entry):
            if _is_project_location_evidence(evidence):
                project_mentions.append(evidence)
            elif not _is_negative_location_context(evidence):
                background_mentions.append(evidence)
    return _dedupe_evidence(project_mentions), _dedupe_evidence(background_mentions)


def _is_scope_decisive_mention(evidence: dict) -> bool:
    return _is_project_location_evidence(evidence)


def _is_project_location_evidence(evidence: dict) -> bool:
    return _location_evidence_role(evidence) == "project_location"


def _location_evidence_role(evidence: dict) -> str:
    if _is_negative_location_context(evidence):
        return "negative_location"
    decision_text = _location_context_text(evidence)
    if _has_incidental_forest_unit_context(decision_text):
        return "background_reference"
    if _is_affirmative_location_context(evidence) or _is_header_project_location_context(evidence):
        return "project_location"
    if evidence.get("category") in {"district", "forest_unit"}:
        return "background_reference"
    return "generic_mention"


def _is_negative_location_context(evidence: dict) -> bool:
    text = _location_decision_window(evidence)
    decision_text = _plan_consistency_decision_text(evidence)
    candidate_texts = [text, decision_text]
    scope_text = _scope_decision_text(evidence)
    if (
        _is_plan_consistency_table_evidence(evidence)
        and not _has_positive_plan_consistency_determination(scope_text)
    ):
        candidate_texts.append(scope_text)
    combined_text = " ".join(candidate_texts)
    if _has_outside_entry_context(evidence, combined_text):
        return True
    if _has_negative_plan_consistency_determination(decision_text):
        return True
    negative_phrases = (
        "not part of the project area",
        "outside the project area",
        "outside of the project area",
        "project is not in this area",
        "project is not within this area",
        "is not in the project area",
        "is not within the project area",
        "not affected by the project",
        "not affected by this project",
        "does not apply to the project area",
        "project does not include",
        "project does not contain",
        "project does not affect",
        "project does not pertain to",
        "no designated wilderness in the project area",
        "no designated wilderness in the project area or affected by the project",
        "no research natural areas in the project area",
        "no research natural areas in the project area or affected by the project",
    )
    return any(
        phrase in candidate
        for phrase in negative_phrases
        for candidate in candidate_texts
    ) or bool(
        re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b(?:in\s+the\s+project\s+area|"
            r"affected\s+by\s+(?:the|this)\s+project)\b",
            combined_text,
        )
        or _has_no_entry_location_context(evidence, combined_text)
    )


def _plan_consistency_decision_text(evidence: dict) -> str:
    scope_text = _scope_decision_text(evidence)
    if "plan consistency table" not in scope_text:
        return ""
    alias = str(evidence.get("matched_alias") or "").lower()
    if not alias:
        return scope_text
    pattern, _case_sensitive = _compiled_alias_pattern(alias)
    match = pattern.search(scope_text)
    if match is None:
        return scope_text
    start = max(
        0,
        max(
            scope_text.rfind(" | | ", 0, match.start()),
            scope_text.rfind("\n\n", 0, match.start()),
        ),
    )
    end_candidates = [
        index
        for marker in (" | | ", "\n\n")
        if (index := scope_text.find(marker, match.end())) >= 0
    ]
    end = min(end_candidates) if end_candidates else min(len(scope_text), match.end() + 900)
    return scope_text[start:end]


def _has_negative_plan_consistency_determination(text: str) -> bool:
    if not text:
        return False
    has_no_determination = bool(
        re.search(r"\|\s*no\s*\|", text)
        or re.search(r"(?:^|\n)\s*no\s*(?:\n|-)", text)
    )
    if not has_no_determination:
        return False
    return bool(
        re.search(
            r"\b(?:not\s+part\s+of|outside(?:\s+of)?|not\s+in|not\s+within)\s+"
            r"(?:the\s+)?project\s+area\b",
            text,
        )
        or re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b(?:in\s+the\s+project\s+area|"
            r"affected\s+by\s+(?:the|this)\s+project)\b",
            text,
        )
        or re.search(
            r"\bproject\s+does\s+not\b.{0,180}\b(?:include|contain|affect|pertain\s+to|"
            r"involve)\b",
            text,
        )
    )


def _has_positive_plan_consistency_determination(text: str) -> bool:
    if not text:
        return False
    return bool(
        re.search(r"\|\s*yes\s*\|", text)
        or re.search(r"(?:^|\n)\s*yes\s*(?:\n|-)", text)
    )


def _has_no_entry_location_context(evidence: dict, text: str) -> bool:
    for term in _entry_text_terms(evidence):
        term_pattern = _term_pattern(term)
        if re.search(
            rf"\b(?:there\s+(?:are|is)\s+no|no)\b.{{0,240}}\b{term_pattern}\b"
            rf".{{0,160}}\b(?:in|near|within)\b.{{0,120}}\b"
            rf"(?:parcels?|lands?|project\s+area|area)\b",
            text,
        ):
            return True
    return False


def _has_outside_entry_context(evidence: dict, text: str) -> bool:
    for term in _entry_text_terms(evidence):
        if re.search(rf"\boutside(?:\s+of)?\s+{_term_pattern(term)}\b", text):
            return True
    return False


def _entry_text_terms(evidence: dict) -> list[str]:
    return _dedupe_text_terms(
        [
            str(evidence.get("matched_alias") or "").strip().lower(),
            str(evidence.get("name") or "").strip().lower(),
        ]
    )


def _dedupe_text_terms(terms: list[str]) -> list[str]:
    deduped = []
    for term in terms:
        if term and term not in deduped:
            deduped.append(term)
    return deduped


def _term_pattern(term: str) -> str:
    term_pattern = re.escape(term).replace(r"\ ", r"\s+")
    if not term.endswith("s"):
        term_pattern = f"{term_pattern}s?"
    return term_pattern


def _is_affirmative_location_context(evidence: dict) -> bool:
    if _is_negative_location_context(evidence):
        return False
    text = " ".join([_location_decision_window(evidence), _scope_decision_text(evidence)])
    return bool(
        re.search(
            r"\b(?:project\s+area|project|action|trail\s+work|parcels?|lands?|it)\b.{0,160}"
            r"\b(?:includes?|is|are|within|cross(?:es)?|located|incorporated)\b.{0,220}"
            r"\b(?:on|in|within|into|across|cross(?:es)?)\b",
            text,
        )
        or re.search(
            r"\b(?:will|would)\s+(?:also\s+)?be\s+(?:incorporated|located)\s+"
            r"(?:on|in|within|into)\b",
            text,
        )
    )


def _is_header_project_location_context(evidence: dict) -> bool:
    if evidence.get("category") not in {"district", "forest_unit"}:
        return False
    text = _location_context_text(evidence)
    if _has_incidental_forest_unit_context(text):
        return False
    has_header_marker = "##" in text or "|" in text
    has_admin_unit = "ranger district" in text or "national forest" in text
    has_document_context = bool(
        re.search(
            r"\b(?:project|proposed\s+action|environmental\s+assessment|analysis|"
            r"specialist\s+report|compliance\s+statement)\b",
            text,
        )
    )
    if has_header_marker and has_admin_unit and has_document_context:
        return True
    return bool(
        re.search(
            r"\b(?:project|analysis|environmental\s+assessment)\b.{0,240}"
            r"\b(?:ranger\s+district|national\s+forest)\b",
            text,
        )
    )


def _location_context_text(evidence: dict) -> str:
    provenance = evidence.get("provenance") or {}
    return " ".join(
        str(part)
        for part in (
            _location_decision_window(evidence),
            provenance.get("section"),
            provenance.get("heading"),
        )
        if part
    ).lower()


def _location_decision_window(evidence: dict) -> str:
    span = evidence.get("evidence_span") or {}
    text = str(span.get("text") or "").lower()
    alias = str(evidence.get("matched_alias") or "").lower()
    if not text or not alias:
        return _scope_decision_text(evidence)
    pattern, _case_sensitive = _compiled_alias_pattern(alias)
    match = pattern.search(text)
    if match is None:
        return text
    next_pipe = text.find("|", match.end())
    next_sentence_boundary = _nearest_location_boundary_after(text, match.end())
    if next_pipe >= 0 and (next_sentence_boundary is None or next_pipe < next_sentence_boundary):
        start = _location_boundary_before(text, match.start())
        end = _location_boundary_after(text, match.end())
        return text[start:end]
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    if "\n" in text and "|" in line:
        return line
    sentence_start_candidates = [
        text.rfind(boundary, 0, match.start()) for boundary in (".", ";", "\n")
    ]
    sentence_start = max(sentence_start_candidates)
    start = 0 if sentence_start < 0 else sentence_start + 1
    sentence_end_candidates = [
        index
        for boundary in (".", ";", "\n")
        if (index := text.find(boundary, match.end())) >= 0
    ]
    end = min(sentence_end_candidates) if sentence_end_candidates else len(text)
    return text[start:end]


def _nearest_location_boundary_after(text: str, start: int) -> int | None:
    candidates = [
        index for boundary in (".", ";", "\n") if (index := text.find(boundary, start)) >= 0
    ]
    return min(candidates) if candidates else None


def _location_boundary_before(text: str, start: int) -> int:
    boundary = max(text.rfind(char, 0, start) for char in (".", ";", "\n"))
    return 0 if boundary < 0 else boundary + 1


def _location_boundary_after(text: str, start: int) -> int:
    boundary = _nearest_location_boundary_after(text, start)
    return len(text) if boundary is None else boundary


def _scope_decision_text(evidence: dict) -> str:
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    parts = [
        evidence.get("title"),
        span.get("text"),
        provenance.get("section"),
        provenance.get("heading"),
        provenance.get("artifact_path"),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def _is_plan_consistency_table_evidence(evidence: dict) -> bool:
    return "plan consistency table" in _scope_decision_text(evidence)


def _has_incidental_forest_unit_context(text: str) -> bool:
    incidental_phrases = (
        "references",
        "literature cited",
        "literature/ science considered",
        "literature/science considered",
        "science considered",
        "bibliography",
        "works cited",
        "reference list",
        "forest service files",
        "coordinates stewardship",
        "for example, the",
        "other forests in the area",
        "neighboring national forests",
        "neither forest has planned projects",
        "northern portion",
        "southern portion",
        "not likely to use affected parcels",
    )
    if any(phrase in text for phrase in incidental_phrases):
        return True
    reference_like_patterns = (
        r"\b\d{4}[a-z]?\.\s+[^.]{0,180}\bnational forest\b",
        r"\busda forest service\.\s+\d{4}[a-z]?\b",
        r"\bu\.s\. department of agriculture\b[^.]{0,180}\b\d{4}[a-z]?\b",
        r"\bpublication\s+#?[a-z0-9-]+\b[^.]{0,180}\bnational forest\b",
        r"\bnational forest\b[^.]{0,140}\b\d+\s*pp\b",
    )
    return any(re.search(pattern, text) for pattern in reference_like_patterns)


def _alias_pattern(alias: str) -> re.Pattern[str]:
    pattern, _ = _compiled_alias_pattern(alias)
    return pattern


def _compiled_alias_pattern(alias: str) -> tuple[re.Pattern[str], bool]:
    case_sensitive = _is_case_sensitive_alias(alias)
    pattern_text = alias if case_sensitive else alias.lower()
    escaped = re.escape(pattern_text).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])"), case_sensitive


def _term_found(text: str, term: str) -> bool:
    pattern, case_sensitive = _compiled_alias_pattern(term)
    search_text = text if case_sensitive else text.lower()
    return bool(pattern.search(search_text))


def _is_case_sensitive_alias(alias: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9]", "", alias)
    if len(compact) < 2 or not any(char.isalpha() for char in compact):
        return False
    return compact.upper() == compact and any(char.isupper() for char in alias)


def _package_evidence(
    *,
    chunk: dict,
    text: str,
    category: str,
    entry_id: str,
    name: str,
    matched_alias: str,
    match_start: int,
    match_end: int,
) -> dict:
    span_start = max(0, match_start - 140)
    span_end = min(len(text), match_end + 900)
    span_text = text[span_start:span_end].strip()
    leading_trim = len(text[span_start:span_end]) - len(text[span_start:span_end].lstrip())
    trailing_trim = len(text[span_start:span_end].rstrip())
    chunk_span_start = span_start + leading_trim
    chunk_span_end = span_start + trailing_trim
    source_chunk_start = int(chunk.get("char_start") or 0)
    evidence = {
        "category": category,
        "entry_id": entry_id,
        "name": name,
        "matched_alias": matched_alias,
        "citation_label": chunk.get("citation_label"),
        "chunk_id": chunk.get("chunk_id"),
        "source_record_id": chunk.get("source_record_id"),
        "title": chunk.get("title"),
        "evidence_span": {
            "text": span_text,
            "chunk_char_start": chunk_span_start,
            "chunk_char_end": chunk_span_end,
            "source_char_start": source_chunk_start + chunk_span_start,
            "source_char_end": source_chunk_start + chunk_span_end,
        },
        "provenance": {
            "artifact_sha256": chunk.get("artifact_sha256"),
            "artifact_path": chunk.get("artifact_path"),
            "parser_name": chunk.get("parser_name"),
            "parser_version": chunk.get("parser_version"),
            "extracted_at": chunk.get("extracted_at"),
            "source_text_path": chunk.get("source_text_path"),
            "char_start": chunk.get("char_start"),
            "char_end": chunk.get("char_end"),
            "page": chunk.get("page"),
            "section": chunk.get("section"),
            "heading": chunk.get("heading"),
            "content_sha256": chunk.get("content_sha256"),
        },
    }
    evidence["evidence_role"] = _location_evidence_role(evidence)
    return evidence


def _dedupe_evidence(records: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for record in sorted(
        records,
        key=lambda item: (
            str(item.get("chunk_id") or ""),
            int(item.get("evidence_span", {}).get("source_char_start") or 0),
            str(item.get("matched_alias") or ""),
        ),
    ):
        key = (
            record.get("entry_id"),
            record.get("chunk_id"),
            record.get("evidence_span", {}).get("source_char_start"),
            record.get("evidence_span", {}).get("source_char_end"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def _unresolved_from_evidence(reason: str, evidence: list[dict]) -> list[dict]:
    return [
        {
            "category": item["category"],
            "reason": reason,
            "name": item["name"],
            "package_evidence": item,
        }
        for item in evidence
    ]


def _flatten_package_evidence(*groups) -> list[dict]:
    flattened = []
    for group in groups:
        for item in group:
            if not item:
                continue
            for evidence in item.get("package_evidence", []):
                flattened.append(evidence)
    return _dedupe_evidence(flattened)


def _flatten_plan_source_evidence(*groups) -> list[dict]:
    flattened = []
    seen = set()
    for group in groups:
        for item in group:
            for evidence in item.get("plan_source_evidence", []):
                key = (item.get("entry_id"), evidence.get("chunk_id"), evidence.get("rank"))
                if key in seen:
                    continue
                seen.add(key)
                flattened.append(
                    {
                        "category": item["category"],
                        "entry_id": item["entry_id"],
                        "name": item["name"],
                        **evidence,
                    }
                )
    return flattened


def _validation_report(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    checks = [
        _check_schema_fields(context),
        _check_scope_resolved(context, resolver_profile=resolver_profile),
        _check_required_custer_source_records_indexed(
            context,
            resolver_profile=resolver_profile,
        ),
        _check_custer_scope_has_resolved_area(context, resolver_profile=resolver_profile),
        _check_resolved_entries_have_plan_source_evidence(context),
        _check_triggered_supporting_plan_evidence_has_source_evidence(context),
    ]
    return {
        "schema_version": "forest-plan-context-validation-v0",
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_schema_fields(context: dict) -> dict:
    required = {
        "scope_status",
        "forest_unit",
        "source_records",
        "project_location_signals",
        "geographic_areas",
        "management_areas",
        "overlays",
        "supporting_plan_evidence",
        "source_record_readiness",
        "package_evidence",
        "plan_source_evidence",
        "unresolved_mentions",
        "needs_reviewer_resolution",
    }
    missing = sorted(required - set(context))
    return {
        "name": "context_schema_fields_present",
        "passed": not missing,
        "details": {"missing": missing},
    }


def _check_scope_resolved(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    status = context.get("scope_status")
    return {
        "name": "scope_status_resolved",
        "passed": status in {resolver_profile.scope_status, resolver_profile.out_of_scope_status},
        "details": {"scope_status": status},
    }


def _check_custer_scope_has_resolved_area(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    if not _is_profile_scope(context, resolver_profile):
        return {
            "name": "custer_scope_has_resolved_area",
            "passed": True,
            "details": {"not_applicable": True},
        }
    resolved_count = (
        len(context.get("geographic_areas", []))
        + len(context.get("management_areas", []))
        + len(context.get("overlays", []))
    )
    return {
        "name": "custer_scope_has_resolved_area",
        "passed": resolved_count > 0,
        "details": {
            "resolved_area_count": resolved_count,
            "geographic_area_count": len(context.get("geographic_areas", [])),
            "management_area_count": len(context.get("management_areas", [])),
            "overlay_count": len(context.get("overlays", [])),
        },
    }


def _check_required_custer_source_records_indexed(
    context: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    if not _is_profile_scope(context, resolver_profile):
        return {
            "name": "required_custer_source_records_indexed",
            "passed": True,
            "details": {"not_applicable": True},
        }
    readiness = context.get("source_record_readiness") or {}
    missing = list(readiness.get("missing_source_record_ids") or [])
    return {
        "name": "required_custer_source_records_indexed",
        "passed": bool(readiness.get("ready")) and not missing,
        "details": {
            "required_source_record_ids": readiness.get("required_source_record_ids", []),
            "indexed_source_record_counts": readiness.get("indexed_source_record_counts", {}),
            "missing_source_record_ids": missing,
        },
    }


def _check_resolved_entries_have_plan_source_evidence(context: dict) -> dict:
    failures = []
    for collection_name in ("geographic_areas", "management_areas", "overlays"):
        for entry in context.get(collection_name, []):
            if not entry.get("package_evidence") or not entry.get("plan_source_evidence"):
                failures.append(
                    {
                        "collection": collection_name,
                        "entry_id": entry.get("entry_id"),
                        "name": entry.get("name"),
                        "package_evidence_count": len(entry.get("package_evidence", [])),
                        "plan_source_evidence_count": len(entry.get("plan_source_evidence", [])),
                    }
                )
    return {
        "name": "resolved_entries_have_package_and_plan_source_evidence",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_triggered_supporting_plan_evidence_has_source_evidence(context: dict) -> dict:
    failures = []
    for entry in context.get("supporting_plan_evidence", []):
        if (
            not entry.get("trigger_evidence")
            or not entry.get("package_evidence")
            or not entry.get("plan_source_evidence")
        ):
            failures.append(
                {
                    "route_id": entry.get("route_id"),
                    "name": entry.get("name"),
                    "source_record_id": entry.get("source_record_id"),
                    "trigger_evidence_count": len(entry.get("trigger_evidence", [])),
                    "package_evidence_count": len(entry.get("package_evidence", [])),
                    "plan_source_evidence_count": len(entry.get("plan_source_evidence", [])),
                }
            )
    return {
        "name": "triggered_supporting_plan_evidence_has_source_evidence",
        "passed": not failures,
        "details": {
            "triggered_route_count": len(context.get("supporting_plan_evidence", [])),
            "failures": failures,
        },
    }


def _needs_reviewer_resolution(
    context: dict,
    validation: dict,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> bool:
    if context.get("scope_status") == resolver_profile.out_of_scope_status:
        return False
    if not _is_profile_scope(context, resolver_profile):
        return True
    return not validation.get("passed")


def _is_profile_scope(context: dict, resolver_profile: ForestPlanResolverProfile) -> bool:
    return context.get("scope_status") == resolver_profile.scope_status


def _summary(
    *,
    context: dict,
    validation: dict,
    package_manifest: list[dict],
    package_chunks: list[dict],
    context_path: Path,
    validation_path: Path,
    summary_path: Path,
    retrieval_readiness: dict | None,
    component_evaluation_summary: dict | None = None,
) -> dict:
    failed_package_records = [
        record for record in package_manifest if record.get("status") != "extracted"
    ]
    summary = {
        "schema_version": "forest-plan-context-summary-v0",
        "review_id": context["review_id"],
        "scope_status": context["scope_status"],
        "source_set_id": context.get("source_set_id"),
        "index_path": context.get("index_path"),
        "context_path": str(context_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "package_file_count": len(package_manifest),
        "package_failed_count": len(failed_package_records),
        "package_chunk_count": len(package_chunks),
        "project_location_signal_count": len(context["project_location_signals"]),
        "geographic_area_count": len(context["geographic_areas"]),
        "management_area_count": len(context["management_areas"]),
        "overlay_count": len(context["overlays"]),
        "supporting_plan_evidence_count": len(context["supporting_plan_evidence"]),
        "unresolved_mention_count": len(context["unresolved_mentions"]),
        "needs_reviewer_resolution": context["needs_reviewer_resolution"],
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"] and not context["needs_reviewer_resolution"],
        "retrieval_readiness": retrieval_readiness,
    }
    if component_evaluation_summary is not None:
        component_adjudication = _component_adjudication_readiness(
            review_dir=summary_path.parent,
            review_id=str(context["review_id"]),
            source_set_id=context.get("source_set_id"),
            component_evaluation_summary=component_evaluation_summary,
        )
        summary["component_evaluation"] = component_evaluation_summary
        summary["component_adjudication"] = component_adjudication
        component_gate_ready = bool(
            component_evaluation_summary.get("validation_passed")
        ) or bool(component_adjudication.get("reviewer_ready"))
        summary["reviewer_ready"] = summary["reviewer_ready"] and bool(
            component_gate_ready
        )
    return summary


def _component_adjudication_readiness(
    *,
    review_dir: Path,
    review_id: str,
    source_set_id: str | None,
    component_evaluation_summary: dict,
) -> dict:
    eval_path = review_dir / "forest_plan_component_adjudication_eval.json"
    summary = _read_json_if_exists(eval_path)
    if not isinstance(summary, dict):
        return {
            "eval_path": str(eval_path),
            "eval_exists": False,
            "reviewer_ready": False,
            "failed_checks": ["adjudication_eval_missing"],
        }
    eval_summary = (
        summary.get("summary") if isinstance(summary.get("summary"), dict) else {}
    )
    current_queue_count = int(component_evaluation_summary.get("reviewer_resolution_count") or 0)
    adjudication_queue_count = int(eval_summary.get("queue_item_count") or 0)
    resolved_count = int(eval_summary.get("resolved_adjudication_count") or 0)
    pending_count = int(eval_summary.get("pending_adjudication_count") or 0)
    system_miss_count = int(eval_summary.get("system_miss_count") or 0)
    failed_checks: list[str] = []
    if not bool(eval_summary.get("passed")):
        failed_checks.append("adjudication_eval_failed")
    if (summary.get("review_id") or eval_summary.get("review_id")) != review_id:
        failed_checks.append("review_id_mismatch")
    if (summary.get("source_set_id") or eval_summary.get("source_set_id")) != source_set_id:
        failed_checks.append("source_set_mismatch")
    if adjudication_queue_count != current_queue_count:
        failed_checks.append("queue_item_count_mismatch")
    if resolved_count != current_queue_count:
        failed_checks.append("resolved_item_count_mismatch")
    if pending_count:
        failed_checks.append("pending_adjudication")
    return {
        "eval_path": str(eval_path),
        "eval_exists": True,
        "reviewer_ready": not failed_checks,
        "failed_checks": failed_checks,
        "queue_item_count": adjudication_queue_count,
        "current_queue_item_count": current_queue_count,
        "resolved_adjudication_count": resolved_count,
        "pending_adjudication_count": pending_count,
        "real_ea_omission_count": int(eval_summary.get("real_ea_omission_count") or 0),
        "system_miss_count": system_miss_count,
        "adjudication_completion_rate": eval_summary.get("adjudication_completion_rate"),
        "adjudication_outcome_counts": eval_summary.get("adjudication_outcome_counts", {}),
        "disposition_counts": eval_summary.get("disposition_counts", {}),
        "real_ea_omission_disposition_counts": eval_summary.get(
            "real_ea_omission_disposition_counts",
            {},
        ),
        "system_miss_disposition_counts": eval_summary.get(
            "system_miss_disposition_counts",
            {},
        ),
        "failure_category_counts": eval_summary.get("failure_category_counts", {}),
    }


def _retrieval_readiness_report(
    *,
    index_path: Path,
    source_set_id: str,
    required_source_record_ids: tuple[str, ...] = (),
) -> dict:
    summary_path = index_path.parent / "summary.json"
    validation_path = index_path.parent / "retrieval_validation.json"
    summary = _read_json_if_exists(summary_path)
    validation = _read_json_if_exists(validation_path)
    indexed_source_counts = _indexed_source_record_counts(index_path, required_source_record_ids)
    missing_source_record_ids = [
        source_record_id
        for source_record_id in required_source_record_ids
        if indexed_source_counts.get(source_record_id, 0) <= 0
    ]
    required_source_records_ready = bool(required_source_record_ids) and not missing_source_record_ids
    resolver_ready = bool(
        summary
        and (
            required_source_records_ready
            if required_source_record_ids
            else summary.get("reviewer_ready")
        )
    )
    required_source_records = {
        "required_source_record_ids": list(required_source_record_ids),
        "indexed_source_record_counts": indexed_source_counts,
        "missing_source_record_ids": missing_source_record_ids,
        "ready": required_source_records_ready,
    }
    checks = [
        {
            "name": "retrieval_index_exists",
            "passed": index_path.exists(),
            "details": {"path": str(index_path)},
        },
        {
            "name": "retrieval_summary_exists",
            "passed": summary is not None,
            "details": {"path": str(summary_path)},
        },
        {
            "name": "retrieval_validation_exists",
            "passed": validation is not None,
            "details": {"path": str(validation_path)},
        },
        {
            "name": "retrieval_source_set_matches",
            "passed": bool(summary and summary.get("source_set_id") == source_set_id),
            "details": {
                "expected_source_set_id": source_set_id,
                "summary_source_set_id": (summary or {}).get("source_set_id"),
            },
        },
        {
            "name": "retrieval_validation_passed",
            "passed": bool(validation and validation.get("passed")),
            "details": {"passed": bool(validation and validation.get("passed"))},
        },
        {
            "name": "required_custer_source_records_indexed",
            "passed": not required_source_record_ids or required_source_records_ready,
            "details": required_source_records,
        },
        {
            "name": "retrieval_ready_for_forest_plan_resolver",
            "passed": resolver_ready,
            "details": {
                "summary_reviewer_ready": bool(summary and summary.get("reviewer_ready")),
                "required_source_records_ready": required_source_records_ready,
            },
        },
    ]
    return {
        "index_path": str(index_path),
        "summary_path": str(summary_path),
        "validation_path": str(validation_path),
        "required_source_records": required_source_records,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _indexed_source_record_counts(
    index_path: Path,
    required_source_record_ids: tuple[str, ...],
) -> dict[str, int]:
    if not required_source_record_ids or not index_path.exists():
        return {}
    placeholders = ",".join("?" for _ in required_source_record_ids)
    try:
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                f"""
                SELECT source_record_id, COUNT(*)
                FROM chunks
                WHERE source_record_id IN ({placeholders})
                GROUP BY source_record_id
                """,
                list(required_source_record_ids),
            ).fetchall()
    except sqlite3.Error:
        return {}
    return {str(source_record_id): int(count) for source_record_id, count in rows}


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _default_review_id(package_path: Path) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"forest-plan-context-{_safe_id(package_path.stem or package_path.name)}-{stamp}"


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return safe or hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dot, underscore, or hyphen."
        )


def _evidence_id(category: str, name: str, alias: str) -> str:
    return f"{category}-{_safe_id(name)}-{_safe_id(alias)}"
