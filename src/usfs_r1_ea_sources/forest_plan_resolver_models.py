from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import ForestPlanProfile
from .forest_plan_profiles import ForestPlanProfileCollection
from .forest_plan_profiles import ForestPlanTermEntry
from .forest_plan_profiles import KnownForestUnit
from .forest_plan_profiles import SupportingRecordTriggerRule
from .forest_plan_profiles import load_forest_plan_profiles


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


def _is_profile_scope(context: dict, resolver_profile: ForestPlanResolverProfile) -> bool:
    return context.get("scope_status") == resolver_profile.scope_status


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return safe or hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
