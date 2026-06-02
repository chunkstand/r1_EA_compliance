from __future__ import annotations

from pathlib import Path
import re

from .forest_plan_resolver_location import _is_affirmative_location_context
from .forest_plan_resolver_location import _is_negative_location_context
from .forest_plan_resolver_location import _location_evidence_role
from .forest_plan_resolver_location import _term_found
from .forest_plan_resolver_mentions import _dedupe_evidence
from .forest_plan_resolver_mentions import _flatten_package_evidence
from .forest_plan_resolver_mentions import _flatten_plan_source_evidence
from .forest_plan_resolver_mentions import _mentions_for_aliases
from .forest_plan_resolver_mentions import _mentions_for_entry
from .forest_plan_resolver_mentions import _package_evidence
from .forest_plan_resolver_mentions import _plan_source_evidence
from .forest_plan_resolver_mentions import _query_plan_source_record_aliases
from .forest_plan_resolver_mentions import _supporting_plan_evidence
from .forest_plan_resolver_mentions import _unresolved_from_evidence
from .forest_plan_resolver_models import FOREST_PLAN_CONTEXT_SCHEMA_VERSION
from .forest_plan_resolver_models import GazetteerEntry
from .forest_plan_resolver_models import ForestPlanResolverProfile
from .forest_plan_resolver_models import _is_profile_scope
from .forest_plan_resolver_models import _safe_id
from .review_package_support import utc_now

def _resolve_scope(
    package_chunks: list[dict],
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict:
    title_page_project_location = _title_page_project_location(
        package_chunks,
        resolver_profile=resolver_profile,
    )
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
    title_page_forest_evidence = _title_page_selected_forest_evidence(
        title_page_project_location,
        resolver_profile=resolver_profile,
    )
    if title_page_forest_evidence:
        title_page_other_forest_names = _title_page_other_forest_names(
            title_page_project_location
        )
        profile_scope_mentions = _prioritize_title_page_evidence(
            _dedupe_evidence([*title_page_forest_evidence, *profile_scope_mentions])
        )
        other_background_mentions = _dedupe_evidence(
            [
                *other_background_mentions,
                *(
                    mention
                    for mention in blocking_other_forest_mentions
                    if mention.get("name") not in title_page_other_forest_names
                ),
            ]
        )
        blocking_other_forest_mentions = [
            mention
            for mention in blocking_other_forest_mentions
            if mention.get("name") in title_page_other_forest_names
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
        if title_page_forest_evidence:
            resolution_basis = "decision_notice_fonsi_title_page"
        elif profile_scope_mentions:
            resolution_basis = "forest_unit_project_location"
        else:
            resolution_basis = "profile_district_project_location"
        forest_unit = {
            "name": resolver_profile.profile.forest_unit_names[0],
            "resolution_basis": resolution_basis,
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
        "title_page_project_location": title_page_project_location,
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
    profile_project_location_signals = _resolved_entries(
        entries=resolver_profile.ranger_district_entries,
        package_chunks=package_chunks,
        index_path=index_path,
        source_top_k=source_top_k,
        attach_plan_evidence=False,
    )
    project_location_signals = _project_location_signals(
        profile_project_location_signals,
        title_page_project_location=scope.get("title_page_project_location"),
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
        dynamic_management_areas, unresolved_management_area_mentions = (
            _package_detected_management_areas(
                package_chunks=package_chunks,
                index_path=index_path,
                source_top_k=source_top_k,
                resolver_profile=resolver_profile,
            )
        )
        management_areas = _merge_resolved_entries(
            management_areas,
            dynamic_management_areas,
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
        unresolved_management_area_mentions = []
        overlays = []
        supporting_plan_evidence = []

    unresolved_mentions = list(scope["unresolved_mentions"])
    unresolved_mentions.extend(unresolved_management_area_mentions)
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
        "title_page_project_location": scope.get("title_page_project_location"),
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
    return sorted(resolved, key=_resolved_entry_sort_key)


def _merge_resolved_entries(*groups: list[dict]) -> list[dict]:
    merged_by_id = {}
    for group in groups:
        for entry in group:
            entry_id = entry.get("entry_id")
            if entry_id not in merged_by_id:
                merged_by_id[entry_id] = dict(entry)
                continue
            merged_by_id[entry_id]["package_evidence"] = _dedupe_evidence(
                [
                    *merged_by_id[entry_id].get("package_evidence", []),
                    *entry.get("package_evidence", []),
                ]
            )
            merged_by_id[entry_id]["plan_source_evidence"] = _dedupe_plan_evidence(
                [
                    *merged_by_id[entry_id].get("plan_source_evidence", []),
                    *entry.get("plan_source_evidence", []),
                ]
            )
    return sorted(merged_by_id.values(), key=_resolved_entry_sort_key)


def _resolved_entry_sort_key(item: dict) -> tuple[str, int, str, str]:
    if item.get("category") == "management_area":
        identifier = str(item.get("entry_id") or "").removeprefix("mgmt-ma-")
        number, suffix = _management_area_sort_key(identifier)
        if number < 9999:
            return (str(item.get("category") or ""), number, suffix, str(item.get("name") or ""))
    return (str(item.get("category") or ""), 9999, "", str(item.get("name") or ""))


def _dedupe_plan_evidence(records: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for record in records:
        span = record.get("evidence_span") if isinstance(record.get("evidence_span"), dict) else {}
        key = (
            record.get("source_record_id"),
            record.get("chunk_id"),
            span.get("source_char_start"),
            span.get("source_char_end"),
            span.get("text"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


_MANAGEMENT_AREA_REFERENCE_RE = re.compile(
    r"\b(?P<prefix>Management\s+Areas?|MA(?:['’]s|s)?)\s*"
    r"(?:\(\s*)?(?:MA\s*)?[-–—]?\s*"
    r"(?P<identifier>\d{1,3}[A-Za-z]?)\b",
    flags=re.IGNORECASE,
)

_MANAGEMENT_AREA_LIST_ITEM_RE = re.compile(
    r"(?:,\s*|\band\s+|&\s*)(?:MA\s*[-–—]?\s*)?"
    r"(?P<identifier>\d{1,3}[A-Za-z]?)\b",
    flags=re.IGNORECASE,
)


def _package_detected_management_areas(
    *,
    package_chunks: list[dict],
    index_path: Path | None,
    source_top_k: int,
    resolver_profile: ForestPlanResolverProfile,
) -> tuple[list[dict], list[dict]]:
    active_plan_source_record_id = resolver_profile.profile.active_plan_source_record_id
    if not active_plan_source_record_id:
        return [], []
    package_evidence_by_identifier = _package_management_area_evidence_by_identifier(
        package_chunks
    )
    plan_source_rows = (
        _management_area_plan_source_rows(
            index_path=index_path,
            source_record_id=active_plan_source_record_id,
        )
        if index_path is not None
        else []
    )
    resolved = []
    unresolved = []
    for identifier in sorted(package_evidence_by_identifier, key=_management_area_sort_key):
        entry = _management_area_entry(
            identifier=identifier,
            source_record_id=active_plan_source_record_id,
        )
        package_evidence = [
            evidence
            for evidence in _dedupe_evidence(package_evidence_by_identifier[identifier])
            if not _is_negative_location_context(evidence)
        ][:5]
        if not package_evidence:
            continue
        plan_evidence = _management_area_plan_evidence(
            entry=entry,
            plan_source_rows=plan_source_rows,
            limit=source_top_k,
        )
        if plan_evidence:
            resolved.append(
                {
                    "entry_id": entry.entry_id,
                    "category": entry.category,
                    "name": entry.name,
                    "aliases": list(entry.aliases),
                    "source_record_id": entry.source_record_id,
                    "package_evidence": package_evidence,
                    "plan_source_evidence": plan_evidence,
                    "resolution_status": "resolved",
                    "resolution_basis": "ea_detected_management_area_with_plan_source_evidence",
                }
            )
            continue
        unresolved.extend(
            {
                "category": "management_area",
                "reason": "management_area_missing_plan_source_evidence",
                "entry_id": entry.entry_id,
                "name": entry.name,
                "source_record_id": entry.source_record_id,
                "package_evidence": evidence,
            }
            for evidence in package_evidence
        )
    return resolved, unresolved


def _management_area_plan_source_rows(
    *,
    index_path: Path,
    source_record_id: str,
) -> list[dict]:
    return _query_plan_source_record_aliases(
        index_path=index_path,
        query="",
        limit=2000,
        source_record_id=source_record_id,
        document_role="forest_plan",
    )


def _management_area_plan_evidence(
    *,
    entry: GazetteerEntry,
    plan_source_rows: list[dict],
    limit: int,
) -> list[dict]:
    matched = [
        row
        for row in plan_source_rows
        if any(
            _term_found(str(row.get("evidence_span", {}).get("text") or ""), term)
            for term in entry.terms
        )
    ]
    return matched[:limit]


def _package_management_area_evidence_by_identifier(
    package_chunks: list[dict],
) -> dict[str, list[dict]]:
    evidence_by_identifier: dict[str, list[dict]] = {}
    for chunk in package_chunks:
        text = str(chunk.get("text") or "")
        if "management area" not in text.lower() and "ma" not in text.lower():
            continue
        for match in _MANAGEMENT_AREA_REFERENCE_RE.finditer(text):
            identifier = _normalize_management_area_identifier(match.group("identifier"))
            if identifier is None:
                continue
            evidence_by_identifier.setdefault(identifier, []).append(
                _management_area_package_evidence(
                    chunk=chunk,
                    text=text,
                    identifier=identifier,
                    match_start=match.start(),
                    match_end=match.end(),
                )
            )
            for list_identifier, list_start, list_end in _management_area_list_items(
                text,
                start=match.end(),
            ):
                evidence_by_identifier.setdefault(list_identifier, []).append(
                    _management_area_package_evidence(
                        chunk=chunk,
                        text=text,
                        identifier=list_identifier,
                        match_start=list_start,
                        match_end=list_end,
                    )
                )
    return {
        identifier: _dedupe_evidence(records)
        for identifier, records in evidence_by_identifier.items()
    }


def _management_area_list_items(
    text: str,
    *,
    start: int,
) -> list[tuple[str, int, int]]:
    end_candidates = [
        index
        for marker in (".", ";", "\n")
        if (index := text.find(marker, start)) >= 0
    ]
    end = min(end_candidates) if end_candidates else min(len(text), start + 120)
    tail = text[start:end]
    if len(tail) > 120:
        tail = tail[:120]
    items = []
    cursor = 0
    while cursor < len(tail):
        match = _MANAGEMENT_AREA_LIST_ITEM_RE.match(tail, cursor)
        if match is None:
            break
        identifier = _normalize_management_area_identifier(match.group("identifier"))
        if identifier is not None:
            items.append((identifier, start + match.start(), start + match.end()))
        cursor = match.end()
    return items


def _normalize_management_area_identifier(identifier: str) -> str | None:
    match = re.fullmatch(r"0*(\d{1,3})([A-Za-z]?)", identifier.strip())
    if match is None:
        return None
    number = int(match.group(1))
    if number <= 0:
        return None
    suffix = match.group(2).lower()
    return f"{number}{suffix}"


def _management_area_entry(*, identifier: str, source_record_id: str) -> GazetteerEntry:
    name = f"Management Area {identifier}"
    upper_identifier = identifier.upper()
    aliases = [
        f"Management Areas {identifier}",
        f"Management Area {upper_identifier}",
        f"Management Areas {upper_identifier}",
        f"MA {identifier}",
        f"MA-{identifier}",
        f"MA{identifier}",
        f"MA's {identifier}",
        f"MA’s {identifier}",
        f"MA {upper_identifier}",
        f"MA-{upper_identifier}",
        f"MA{upper_identifier}",
        f"MA's {upper_identifier}",
        f"MA’s {upper_identifier}",
    ]
    if identifier.isdigit() and (roman_identifier := _roman_numeral(int(identifier))):
        aliases.extend(
            [
                f"Management Area {roman_identifier}",
                f"Management Areas {roman_identifier}",
                f"MA {roman_identifier}",
                f"MA-{roman_identifier}",
                f"MA{roman_identifier}",
            ]
        )
    return GazetteerEntry(
        entry_id=f"mgmt-ma-{_safe_id(identifier)}",
        category="management_area",
        name=name,
        aliases=tuple(dict.fromkeys(alias for alias in aliases if alias != name)),
        source_record_id=source_record_id,
    )


def _roman_numeral(number: int) -> str | None:
    if number <= 0 or number > 399:
        return None
    values = (
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    remaining = number
    parts = []
    for value, numeral in values:
        while remaining >= value:
            parts.append(numeral)
            remaining -= value
    return "".join(parts)


def _management_area_package_evidence(
    *,
    chunk: dict,
    text: str,
    identifier: str,
    match_start: int,
    match_end: int,
) -> dict:
    entry = _management_area_entry(identifier=identifier, source_record_id="")
    return _package_evidence(
        chunk=chunk,
        text=text,
        category=entry.category,
        entry_id=entry.entry_id,
        name=entry.name,
        matched_alias=text[match_start:match_end].strip(),
        match_start=match_start,
        match_end=match_end,
    )


def _management_area_sort_key(identifier: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d{1,3})([a-z]?)", identifier)
    if match is None:
        return (9999, identifier)
    return (int(match.group(1)), match.group(2))


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


US_STATE_NAMES = (
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
)

_COUNTY_STATE_RE = re.compile(
    r"(?P<counties>"
    r"[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)*"
    r"(?:\s+(?:and|&)\s+[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)*)*"
    r")\s+Count(?:y|ies),\s+"
    rf"(?P<state>{'|'.join(re.escape(state) for state in US_STATE_NAMES)})\b"
)


def _title_page_project_location(
    package_chunks: list[dict],
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> dict | None:
    title_chunks = [
        _title_page_location_chunk(chunk)
        for chunk in package_chunks
        if _is_decision_notice_title_page_chunk(chunk)
    ]
    if not title_chunks:
        return None

    selected_forest_evidence = [
        _mark_title_page_project_location(evidence)
        for evidence in _mentions_for_aliases(
            title_chunks,
            name=resolver_profile.profile.forest_unit_names[0],
            category="forest_unit",
            aliases=resolver_profile.profile.forest_unit_names,
            limit=None,
        )
    ]
    other_forest_evidence = []
    for unit in resolver_profile.known_other_forest_units:
        other_forest_evidence.extend(
            _mark_title_page_project_location(evidence)
            for evidence in _mentions_for_aliases(
                title_chunks,
                name=unit.names[0],
                category="forest_unit",
                aliases=unit.names,
                limit=None,
            )
        )
    ranger_districts = _title_page_ranger_districts(
        title_chunks,
        forest_unit_names=resolver_profile.profile.forest_unit_names,
    )

    county_state = _title_page_county_state(
        title_chunks,
        forest_unit_names=resolver_profile.profile.forest_unit_names,
    )
    if not selected_forest_evidence and not other_forest_evidence and not ranger_districts:
        if county_state is None:
            return None

    return {
        "resolution_basis": "decision_notice_fonsi_title_page",
        "forest_unit": (
            {
                "name": resolver_profile.profile.forest_unit_names[0],
                "package_evidence": _dedupe_evidence(selected_forest_evidence),
                "resolution_status": "resolved",
            }
            if selected_forest_evidence
            else None
        ),
        "other_forest_units": [
            {
                "name": evidence["name"],
                "package_evidence": [evidence],
                "resolution_status": "resolved",
            }
            for evidence in _dedupe_evidence(other_forest_evidence)
        ],
        "ranger_districts": sorted(ranger_districts, key=lambda item: item["name"]),
        "counties": county_state["counties"] if county_state else [],
        "state": county_state["state"] if county_state else None,
        "county_state_evidence": county_state["evidence"] if county_state else None,
    }


def _title_page_selected_forest_evidence(
    title_page_project_location: dict | None,
    *,
    resolver_profile: ForestPlanResolverProfile,
) -> list[dict]:
    if not title_page_project_location:
        return []
    forest_unit = title_page_project_location.get("forest_unit")
    if not isinstance(forest_unit, dict):
        return []
    if forest_unit.get("name") != resolver_profile.profile.forest_unit_names[0]:
        return []
    return list(forest_unit.get("package_evidence") or [])


def _title_page_other_forest_names(title_page_project_location: dict | None) -> set[str]:
    if not title_page_project_location:
        return set()
    return {
        str(unit.get("name") or "")
        for unit in title_page_project_location.get("other_forest_units", [])
        if unit.get("name")
    }


def _prioritize_title_page_evidence(records: list[dict]) -> list[dict]:
    return sorted(
        records,
        key=lambda item: (
            item.get("title_page_project_location") is not True,
            str(item.get("chunk_id") or ""),
            int(item.get("evidence_span", {}).get("source_char_start") or 0),
        ),
    )


def _project_location_signals(
    profile_project_location_signals: list[dict],
    *,
    title_page_project_location: dict | None,
) -> list[dict]:
    if isinstance(title_page_project_location, dict):
        title_page_signals = list(title_page_project_location.get("ranger_districts") or [])
        if title_page_signals:
            return sorted(title_page_signals, key=lambda item: (item["category"], item["name"]))
    return sorted(
        profile_project_location_signals,
        key=lambda item: (item["category"], item["name"]),
    )


def _is_decision_notice_title_page_chunk(chunk: dict) -> bool:
    text = str(chunk.get("text") or "")
    if not text:
        return False
    title = str(chunk.get("title") or "")
    lowered = f"{title}\n{text[:1600]}".lower()
    is_first_page = int(chunk.get("page") or 1) == 1
    is_first_chunk = (
        int(chunk.get("chunk_index") or 0) == 0
        or int(chunk.get("char_start") or 0) == 0
    )
    has_decision_title = (
        "decision notice" in lowered
        and ("finding of no significant impact" in lowered or "fonsi" in lowered)
    )
    has_admin_unit = "ranger district" in lowered and "national forest" in lowered
    return is_first_page and is_first_chunk and has_decision_title and has_admin_unit


def _title_page_location_chunk(chunk: dict) -> dict:
    location_chunk = dict(chunk)
    text = str(chunk.get("text") or "")
    title_block = _title_page_location_text(text)
    location_chunk["text"] = title_block
    location_chunk["char_end"] = int(chunk.get("char_start") or 0) + len(title_block)
    return location_chunk


def _title_page_location_text(text: str) -> str:
    county_state_match = _COUNTY_STATE_RE.search(text[:900])
    if county_state_match is not None and county_state_match.end() >= 80:
        return text[: county_state_match.end()]
    for marker in ("\n\n", " Lead Agency:", "\nLead Agency:"):
        index = text.find(marker)
        if 80 <= index <= 900:
            return text[:index]
    return text[:500]


def _mark_title_page_project_location(evidence: dict) -> dict:
    marked = dict(evidence)
    marked["evidence_role"] = "project_location"
    marked["title_page_project_location"] = True
    marked["resolution_basis"] = "decision_notice_fonsi_title_page"
    return marked


def _title_page_county_state(
    title_chunks: list[dict],
    *,
    forest_unit_names: tuple[str, ...],
) -> dict | None:
    for chunk in title_chunks:
        text = str(chunk.get("text") or "")
        for forest_unit_name in forest_unit_names:
            if not _term_found(text, forest_unit_name):
                continue
            forest_match = re.search(
                re.escape(forest_unit_name).replace(r"\ ", r"\s+"),
                text,
                flags=re.IGNORECASE,
            )
            if forest_match is None:
                continue
            window_start = forest_match.end()
            window = text[window_start : window_start + 260]
            match = _COUNTY_STATE_RE.search(window)
            if match is None:
                continue
            counties = _normalize_counties(match.group("counties"))
            state = match.group("state")
            span_start = window_start + match.start()
            span_end = window_start + match.end()
            return {
                "counties": counties,
                "state": state,
                "evidence": _title_page_admin_evidence(
                    chunk=chunk,
                    span_start=span_start,
                    span_end=span_end,
                    counties=counties,
                    state=state,
                ),
            }
    return None


def _title_page_ranger_districts(
    title_chunks: list[dict],
    *,
    forest_unit_names: tuple[str, ...],
) -> list[dict]:
    districts = []
    for chunk in title_chunks:
        text = str(chunk.get("text") or "")
        for forest_unit_name in forest_unit_names:
            for match in _title_page_ranger_district_matches(
                text,
                forest_unit_name=forest_unit_name,
            ):
                name = _normalize_ranger_district_name(match.group("district"))
                span_start = match.start("district")
                span_end = match.end("district")
                name_start = match.group("district").lower().rfind(name.lower())
                if name_start >= 0:
                    span_start += name_start
                    span_end = span_start + len(name)
                evidence = _title_page_named_location_evidence(
                    chunk=chunk,
                    category="district",
                    entry_id=_title_page_entry_id("district", name),
                    name=name,
                    span_start=span_start,
                    span_end=span_end,
                )
                districts.append(
                    {
                        "entry_id": evidence["entry_id"],
                        "category": "district",
                        "name": name,
                        "aliases": [],
                        "source_record_id": None,
                        "package_evidence": [evidence],
                        "plan_source_evidence": [],
                        "resolution_status": "resolved",
                    }
                )
    deduped = {}
    for district in districts:
        key = district["name"].lower()
        if key not in deduped:
            deduped[key] = district
            continue
        deduped[key]["package_evidence"] = _dedupe_evidence(
            [
                *deduped[key].get("package_evidence", []),
                *district.get("package_evidence", []),
            ]
        )
    return sorted(deduped.values(), key=lambda item: item["name"])


def _title_page_ranger_district_matches(
    text: str,
    *,
    forest_unit_name: str,
) -> list[re.Match[str]]:
    forest_pattern = re.escape(forest_unit_name).replace(r"\ ", r"\s+")
    pattern = re.compile(
        r"(?P<district>"
        r"[A-Z][A-Za-z0-9&.'/-]*(?:\s+[A-Z][A-Za-z0-9&.'/-]*){0,6}"
        r"\s+Ranger\s+Districts?"
        r")\s+"
        rf"{forest_pattern}\b",
        flags=re.IGNORECASE,
    )
    return list(pattern.finditer(text))


def _normalize_ranger_district_name(name: str) -> str:
    normalized = " ".join(name.split()).strip(" -:;")
    for marker in (
        "finding of no significant impact",
        "fonsi",
        "decision notice",
    ):
        marker_index = normalized.lower().rfind(marker)
        if marker_index >= 0:
            normalized = normalized[marker_index + len(marker) :].strip(" -:;")
    if normalized.lower().startswith("and "):
        normalized = normalized[4:].strip(" -:;")
    return normalized


def _normalize_counties(raw_counties: str) -> list[str]:
    names = [
        name.strip(" ,")
        for name in re.split(r"\s+(?:and|&)\s+|,\s*", raw_counties)
        if name.strip(" ,")
    ]
    return [name if name.endswith(" County") else f"{name} County" for name in names]


def _title_page_admin_evidence(
    *,
    chunk: dict,
    span_start: int,
    span_end: int,
    counties: list[str],
    state: str,
) -> dict:
    text = str(chunk.get("text") or "")
    span_text = text[span_start:span_end].strip()
    source_chunk_start = int(chunk.get("char_start") or 0)
    return {
        "category": "administrative_location",
        "entry_id": "title-page-county-state",
        "name": f"{', '.join(counties)}, {state}",
        "matched_alias": span_text,
        "citation_label": chunk.get("citation_label"),
        "chunk_id": chunk.get("chunk_id"),
        "source_record_id": chunk.get("source_record_id"),
        "title": chunk.get("title"),
        "evidence_role": "project_location",
        "title_page_project_location": True,
        "resolution_basis": "decision_notice_fonsi_title_page",
        "evidence_span": {
            "text": span_text,
            "chunk_char_start": span_start,
            "chunk_char_end": span_end,
            "source_char_start": source_chunk_start + span_start,
            "source_char_end": source_chunk_start + span_end,
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


def _title_page_named_location_evidence(
    *,
    chunk: dict,
    category: str,
    entry_id: str,
    name: str,
    span_start: int,
    span_end: int,
) -> dict:
    text = str(chunk.get("text") or "")
    span_text = text[span_start:span_end].strip()
    source_chunk_start = int(chunk.get("char_start") or 0)
    return {
        "category": category,
        "entry_id": entry_id,
        "name": name,
        "matched_alias": span_text,
        "citation_label": chunk.get("citation_label"),
        "chunk_id": chunk.get("chunk_id"),
        "source_record_id": chunk.get("source_record_id"),
        "title": chunk.get("title"),
        "evidence_role": "project_location",
        "title_page_project_location": True,
        "resolution_basis": "decision_notice_fonsi_title_page",
        "evidence_span": {
            "text": span_text,
            "chunk_char_start": span_start,
            "chunk_char_end": span_end,
            "source_char_start": source_chunk_start + span_start,
            "source_char_end": source_chunk_start + span_end,
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


def _title_page_entry_id(prefix: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"title-page-{prefix}-{slug}"


def _is_scope_decisive_mention(evidence: dict) -> bool:
    return _is_project_location_evidence(evidence)


def _is_project_location_evidence(evidence: dict) -> bool:
    return _location_evidence_role(evidence) == "project_location"
