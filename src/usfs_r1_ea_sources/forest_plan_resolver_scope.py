from __future__ import annotations

from pathlib import Path

from .forest_plan_resolver_location import _is_affirmative_location_context
from .forest_plan_resolver_location import _is_negative_location_context
from .forest_plan_resolver_location import _location_evidence_role
from .forest_plan_resolver_mentions import _dedupe_evidence
from .forest_plan_resolver_mentions import _flatten_package_evidence
from .forest_plan_resolver_mentions import _flatten_plan_source_evidence
from .forest_plan_resolver_mentions import _mentions_for_aliases
from .forest_plan_resolver_mentions import _mentions_for_entry
from .forest_plan_resolver_mentions import _plan_source_evidence
from .forest_plan_resolver_mentions import _supporting_plan_evidence
from .forest_plan_resolver_mentions import _unresolved_from_evidence
from .forest_plan_resolver_models import FOREST_PLAN_CONTEXT_SCHEMA_VERSION
from .forest_plan_resolver_models import GazetteerEntry
from .forest_plan_resolver_models import ForestPlanResolverProfile
from .forest_plan_resolver_models import _is_profile_scope
from .review_package_support import utc_now

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
        "created_at": utc_now(),
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
