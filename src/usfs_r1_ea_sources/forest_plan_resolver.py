from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import shutil

from .ea_review import _discover_package_files
from .ea_review import _extract_package_files
from .ea_review import _load_package_cache
from .ea_review import _source_set_id_from_catalog
from .ea_review import _source_set_id_from_index
from .ea_review import _utc_now
from .retrieval import default_index_path
from .retrieval import query_retrieval_index


FOREST_PLAN_CONTEXT_SCHEMA_VERSION = "forest-plan-context-v0"
CUSTER_GALLATIN_PLAN_SOURCE_ID = "R1PLAN-custer-gallatin-nf-02"
CUSTER_GALLATIN_SOURCE_RECORDS = [
    {
        "source_record_id": "R1PLAN-custer-gallatin-nf-01",
        "role": "planning_page",
        "required_for": "currentness and document-set resolution",
    },
    {
        "source_record_id": CUSTER_GALLATIN_PLAN_SOURCE_ID,
        "role": "primary_land_management_plan",
        "required_for": "plan component and area resolution",
    },
    {
        "source_record_id": "R1PLAN-custer-gallatin-nf-03",
        "role": "record_of_decision",
        "required_for": "plan approval and decision basis when needed",
    },
]

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


@dataclass(frozen=True)
class GazetteerEntry:
    entry_id: str
    category: str
    name: str
    aliases: tuple[str, ...] = ()
    source_record_id: str = CUSTER_GALLATIN_PLAN_SOURCE_ID

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


FOREST_UNIT_ALIASES = (
    "Custer Gallatin National Forest",
    "Custer-Gallatin National Forest",
    "Custer Gallatin",
    "Custer-Gallatin",
    "CGNF",
)

NON_CUSTER_FOREST_ALIASES = {
    "Beaverhead-Deerlodge National Forest": (
        "Beaverhead-Deerlodge National Forest",
        "Beaverhead Deerlodge National Forest",
        "BDNF",
    ),
    "Bitterroot National Forest": ("Bitterroot National Forest",),
    "Dakota Prairie Grasslands": ("Dakota Prairie Grasslands",),
    "Flathead National Forest": ("Flathead National Forest",),
    "Helena-Lewis and Clark National Forest": (
        "Helena-Lewis and Clark National Forest",
        "Helena Lewis and Clark National Forest",
    ),
    "Idaho Panhandle National Forests": ("Idaho Panhandle National Forests",),
    "Kootenai National Forest": ("Kootenai National Forest",),
    "Lolo National Forest": ("Lolo National Forest",),
    "Nez Perce-Clearwater National Forests": (
        "Nez Perce-Clearwater National Forests",
        "Nez Perce Clearwater National Forests",
    ),
}

AMBIGUOUS_FOREST_CUES = (
    "Gallatin",
    "Gallatin National Forest",
    "Custer",
)

LOCATION_ENTRIES = (
    GazetteerEntry(
        "district-ashland",
        "district",
        "Ashland Ranger District",
        ("Ashland District",),
    ),
    GazetteerEntry(
        "district-sioux",
        "district",
        "Sioux Ranger District",
        ("Sioux District",),
    ),
    GazetteerEntry("district-bozeman", "district", "Bozeman Ranger District"),
    GazetteerEntry("district-gardiner", "district", "Gardiner Ranger District"),
    GazetteerEntry("district-hebgen-lake", "district", "Hebgen Lake Ranger District"),
    GazetteerEntry("district-yellowstone", "district", "Yellowstone Ranger District"),
    GazetteerEntry("district-beartooth", "district", "Beartooth Ranger District"),
)

GEOGRAPHIC_AREA_ENTRIES = (
    GazetteerEntry("geo-sioux", "geographic_area", "Sioux Geographic Area"),
    GazetteerEntry("geo-ashland", "geographic_area", "Ashland Geographic Area"),
    GazetteerEntry("geo-pryor-mountains", "geographic_area", "Pryor Mountains Geographic Area"),
    GazetteerEntry(
        "geo-absaroka-beartooth",
        "geographic_area",
        "Absaroka Beartooth Mountains Geographic Area",
        ("Absaroka-Beartooth Mountains Geographic Area",),
    ),
    GazetteerEntry(
        "geo-bridger-bangtail-crazy",
        "geographic_area",
        "Bridger, Bangtail, and Crazy Mountains Geographic Area",
        (
            "Bridger Bangtail and Crazy Mountains Geographic Area",
            "Bridger, Bangtail and Crazy Mountains Geographic Area",
        ),
    ),
    GazetteerEntry(
        "geo-madison-henrys-gallatin",
        "geographic_area",
        "Madison, Henrys Lake, and Gallatin Mountains Geographic Area",
        (
            "Madison Henrys Lake and Gallatin Mountains Geographic Area",
            "Madison, Henrys Lake and Gallatin Mountains Geographic Area",
        ),
    ),
)

MANAGEMENT_AREA_ENTRIES = (
    GazetteerEntry("mgmt-chalk-buttes-bca", "management_area", "Chalk Buttes Backcountry Area", ("CBBCA",)),
    GazetteerEntry("mgmt-ashland-bca", "management_area", "Ashland Backcountry Areas", ("ABCA",)),
    GazetteerEntry("mgmt-cook-mountain", "management_area", "Cook Mountain Backcountry Area"),
    GazetteerEntry("mgmt-king-mountain", "management_area", "King Mountain Backcountry Area"),
    GazetteerEntry("mgmt-tongue-river-breaks", "management_area", "Tongue River Breaks Backcountry Area"),
    GazetteerEntry("mgmt-big-pryor-bca", "management_area", "Big Pryor Backcountry Area"),
    GazetteerEntry("mgmt-punch-bowl-bca", "management_area", "Punch Bowl Backcountry Area", ("PBBCA",)),
    GazetteerEntry("mgmt-stillwater-complex", "management_area", "Stillwater Complex", ("SWC",)),
    GazetteerEntry("mgmt-line-creek-rna", "management_area", "Line Creek Plateau Research Natural Area"),
    GazetteerEntry("mgmt-oto-ranch", "management_area", "OTO Ranch", ("OTO",)),
    GazetteerEntry(
        "mgmt-beartooth-scenic-byway",
        "management_area",
        "Beartooth National Forest Scenic Byway",
        ("NSB",),
    ),
    GazetteerEntry("mgmt-bad-canyon-bca", "management_area", "Bad Canyon Backcountry Area", ("BCBCA",)),
    GazetteerEntry(
        "mgmt-boulder-river-rea",
        "management_area",
        "Boulder River Recreation Emphasis Area",
        ("BRREA",),
    ),
    GazetteerEntry(
        "mgmt-cooke-city-winter-rea",
        "management_area",
        "Cooke City Winter Recreation Emphasis Area",
        ("CCREA",),
    ),
    GazetteerEntry(
        "mgmt-main-fork-rock-creek-rea",
        "management_area",
        "Main Fork Rock Creek Recreation Emphasis Area",
        ("MFRCREA",),
    ),
    GazetteerEntry("mgmt-bangtail-special-area", "management_area", "Bangtail Special Area", ("BSA",)),
    GazetteerEntry("mgmt-blacktail-peak-bca", "management_area", "Blacktail Peak Backcountry Area", ("BPBCA",)),
    GazetteerEntry("mgmt-crazy-mountains-bca", "management_area", "Crazy Mountains Backcountry Area", ("CMBCA",)),
    GazetteerEntry("mgmt-bridger-rea", "management_area", "Bridger Recreation Emphasis Area", ("BREA",)),
    GazetteerEntry(
        "mgmt-cabin-creek-recreation-wildlife",
        "management_area",
        "Cabin Creek Recreation and Wildlife Management Area",
        ("CCRW",),
    ),
    GazetteerEntry("mgmt-wilderness-study-area", "management_area", "Wilderness Study Area", ("WSA",)),
    GazetteerEntry("mgmt-black-sand-spring-sa", "management_area", "Black Sand Spring Special Area", ("BSSSA",)),
    GazetteerEntry("mgmt-cdnst", "management_area", "Continental Divide National Scenic Trail", ("CDNST",)),
    GazetteerEntry("mgmt-earthquake-lake", "management_area", "Earthquake Lake Geologic Area", ("ELGA",)),
    GazetteerEntry("mgmt-municipal-watershed", "management_area", "Municipal Watershed"),
    GazetteerEntry("mgmt-buffalo-horn-bca", "management_area", "Buffalo Horn Backcountry Area", ("BHBCA",)),
    GazetteerEntry("mgmt-lionhead-bca", "management_area", "Lionhead Backcountry Area", ("LHBCA",)),
    GazetteerEntry("mgmt-south-cottonwood-bca", "management_area", "South Cottonwood Backcountry Area", ("SCBCA",)),
    GazetteerEntry("mgmt-west-pine-bca", "management_area", "West Pine Backcountry Area", ("WPBCA",)),
    GazetteerEntry(
        "mgmt-gallatin-river-rea",
        "management_area",
        "Gallatin River Recreation Emphasis Area",
        ("GRREA",),
    ),
    GazetteerEntry(
        "mgmt-hebgen-lakeshore-rea",
        "management_area",
        "Hebgen Lakeshore Recreation Emphasis Area",
        ("HLREA",),
    ),
    GazetteerEntry(
        "mgmt-hebgen-winter-rea",
        "management_area",
        "Hebgen Winter Recreation Emphasis Area",
        ("HWREA",),
    ),
    GazetteerEntry("mgmt-hyalite-rea", "management_area", "Hyalite Recreation Emphasis Area", ("HREA",)),
    GazetteerEntry(
        "mgmt-storm-castle-rea",
        "management_area",
        "Storm Castle Recreation Emphasis Area",
        ("SCREA",),
    ),
    GazetteerEntry(
        "mgmt-yellowstone-river-rea",
        "management_area",
        "Yellowstone River Recreation Emphasis Area",
        ("YRREA",),
    ),
)

OVERLAY_ENTRIES = (
    GazetteerEntry("overlay-designated-wilderness", "overlay", "Designated Wilderness", ("DWA",)),
    GazetteerEntry("overlay-wild-scenic-river", "overlay", "Designated Wild and Scenic River", ("DWSR",)),
    GazetteerEntry("overlay-inventoried-roadless", "overlay", "Inventoried Roadless Area", ("Inventoried Roadless Areas", "IRA")),
    GazetteerEntry("overlay-research-natural-area", "overlay", "Research Natural Area", ("RNA",)),
    GazetteerEntry("overlay-special-area", "overlay", "Special Area"),
    GazetteerEntry("overlay-national-natural-landmark", "overlay", "National Natural Landmark", ("NNL",)),
    GazetteerEntry("overlay-national-recreation-trail", "overlay", "National Recreation Trail", ("NRT",)),
    GazetteerEntry(
        "overlay-eligible-wild-scenic-river",
        "overlay",
        "Eligible Wild and Scenic River",
        ("Eligible Wild and Scenic Rivers", "EWSR"),
    ),
    GazetteerEntry(
        "overlay-recommended-wilderness",
        "overlay",
        "Recommended Wilderness Area",
        ("Recommended Wilderness Areas", "RWA"),
    ),
)


def run_forest_plan_resolver(
    *,
    package_path: Path,
    output_dir: Path,
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
) -> ForestPlanResolverResult:
    """Resolve Custer Gallatin forest-plan context from a local EA package."""

    package_path = Path(package_path)
    output_dir = Path(output_dir)
    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")
    if not package_path.exists():
        raise FileNotFoundError(f"Missing EA package path: {package_path}")

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

    _prepare_outputs(
        package_dir=package_dir,
        context_path=context_path,
        validation_path=validation_path,
        summary_path=summary_path,
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

    scope = _resolve_scope(package_chunks)
    retrieval_readiness = None
    if scope["scope_status"] == "custer_gallatin":
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
        source_top_k=source_top_k,
    )
    validation = _validation_report(context)
    context["validation"] = validation
    context["needs_reviewer_resolution"] = _needs_reviewer_resolution(context, validation)
    summary = _summary(
        context=context,
        validation=validation,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        context_path=context_path,
        validation_path=validation_path,
        summary_path=summary_path,
        retrieval_readiness=retrieval_readiness,
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
    )


def _prepare_outputs(
    *,
    package_dir: Path,
    context_path: Path,
    validation_path: Path,
    summary_path: Path,
    preserve_package_cache: bool,
) -> None:
    if package_dir.exists() and not preserve_package_cache:
        shutil.rmtree(package_dir)
    for path in (context_path, validation_path, summary_path):
        path.unlink(missing_ok=True)


def _resolve_scope(package_chunks: list[dict]) -> dict:
    custer_mentions = _mentions_for_aliases(
        package_chunks,
        name="Custer Gallatin National Forest",
        category="forest_unit",
        aliases=FOREST_UNIT_ALIASES,
    )
    non_custer_mentions = []
    for name, aliases in NON_CUSTER_FOREST_ALIASES.items():
        non_custer_mentions.extend(
            _mentions_for_aliases(
                package_chunks,
                name=name,
                category="forest_unit",
                aliases=aliases,
            )
        )
    ambiguous_mentions = []
    if not custer_mentions:
        ambiguous_mentions = _mentions_for_aliases(
            package_chunks,
            name="ambiguous forest cue",
            category="forest_unit",
            aliases=AMBIGUOUS_FOREST_CUES,
        )

    if custer_mentions and not non_custer_mentions:
        status = "custer_gallatin"
        forest_unit = {
            "name": "Custer Gallatin National Forest",
            "package_evidence": custer_mentions[:5],
        }
    elif non_custer_mentions and not custer_mentions:
        status = "not_custer_gallatin"
        forest_unit = {
            "name": non_custer_mentions[0]["name"],
            "package_evidence": non_custer_mentions[:5],
        }
    else:
        status = "ambiguous"
        forest_unit = None

    unresolved = []
    if custer_mentions and non_custer_mentions:
        unresolved.extend(
            _unresolved_from_evidence("multiple_forest_units_mentioned", non_custer_mentions)
        )
    if ambiguous_mentions:
        unresolved.extend(_unresolved_from_evidence("ambiguous_forest_unit", ambiguous_mentions))
    if not custer_mentions and not non_custer_mentions and not ambiguous_mentions:
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
    source_top_k: int,
) -> dict:
    source_records = (
        list(CUSTER_GALLATIN_SOURCE_RECORDS)
        if scope["scope_status"] == "custer_gallatin"
        else []
    )
    project_location_signals = _resolved_entries(
        entries=LOCATION_ENTRIES,
        package_chunks=package_chunks,
        index_path=index_path,
        source_top_k=source_top_k,
        attach_plan_evidence=False,
    )
    if scope["scope_status"] == "custer_gallatin":
        geographic_areas = _resolved_entries(
            entries=GEOGRAPHIC_AREA_ENTRIES,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
        management_areas = _resolved_entries(
            entries=MANAGEMENT_AREA_ENTRIES,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
        overlays = _resolved_entries(
            entries=OVERLAY_ENTRIES,
            package_chunks=package_chunks,
            index_path=index_path,
            source_top_k=source_top_k,
        )
    else:
        geographic_areas = []
        management_areas = []
        overlays = []

    unresolved_mentions = list(scope["unresolved_mentions"])
    package_evidence = _flatten_package_evidence(
        [scope["forest_unit"]] if scope.get("forest_unit") else [],
        project_location_signals,
        geographic_areas,
        management_areas,
        overlays,
    )
    plan_source_evidence = _flatten_plan_source_evidence(
        geographic_areas,
        management_areas,
        overlays,
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
        "package_evidence": package_evidence,
        "plan_source_evidence": plan_source_evidence,
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
        package_evidence = _mentions_for_entry(package_chunks, entry)
        if not package_evidence:
            continue
        plan_evidence = []
        if attach_plan_evidence and index_path is not None:
            plan_evidence = _plan_source_evidence(
                entry=entry,
                index_path=index_path,
                limit=source_top_k,
            )
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


def _evidence_text_matches_entry(text: str, entry: GazetteerEntry) -> bool:
    lower = text.lower()
    return any(_alias_pattern(term).search(lower) for term in entry.terms)


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
    return _dedupe_evidence(mentions)[:5]


def _mentions_for_aliases(
    package_chunks: list[dict],
    *,
    name: str,
    category: str,
    aliases: tuple[str, ...],
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
    return _dedupe_evidence(mentions)[:5]


def _mentions_for_alias(
    package_chunks: list[dict],
    *,
    name: str,
    category: str,
    entry_id: str,
    alias: str,
) -> list[dict]:
    pattern = _alias_pattern(alias)
    mentions = []
    for chunk in package_chunks:
        text = str(chunk.get("text") or "")
        lower = text.lower()
        for match in pattern.finditer(lower):
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


def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias.lower()).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


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
    span_end = min(len(text), match_end + 340)
    span_text = text[span_start:span_end].strip()
    leading_trim = len(text[span_start:span_end]) - len(text[span_start:span_end].lstrip())
    trailing_trim = len(text[span_start:span_end].rstrip())
    chunk_span_start = span_start + leading_trim
    chunk_span_end = span_start + trailing_trim
    source_chunk_start = int(chunk.get("char_start") or 0)
    return {
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


def _validation_report(context: dict) -> dict:
    checks = [
        _check_schema_fields(context),
        _check_scope_resolved(context),
        _check_custer_scope_has_resolved_area(context),
        _check_resolved_entries_have_plan_source_evidence(context),
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


def _check_scope_resolved(context: dict) -> dict:
    status = context.get("scope_status")
    return {
        "name": "scope_status_resolved",
        "passed": status in {"custer_gallatin", "not_custer_gallatin"},
        "details": {"scope_status": status},
    }


def _check_custer_scope_has_resolved_area(context: dict) -> dict:
    if context.get("scope_status") != "custer_gallatin":
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


def _needs_reviewer_resolution(context: dict, validation: dict) -> bool:
    if context.get("scope_status") == "not_custer_gallatin":
        return False
    if context.get("scope_status") != "custer_gallatin":
        return True
    return not validation.get("passed")


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
) -> dict:
    failed_package_records = [
        record for record in package_manifest if record.get("status") != "extracted"
    ]
    return {
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
        "unresolved_mention_count": len(context["unresolved_mentions"]),
        "needs_reviewer_resolution": context["needs_reviewer_resolution"],
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"] and not context["needs_reviewer_resolution"],
        "retrieval_readiness": retrieval_readiness,
    }


def _retrieval_readiness_report(*, index_path: Path, source_set_id: str) -> dict:
    summary_path = index_path.parent / "summary.json"
    validation_path = index_path.parent / "retrieval_validation.json"
    summary = _read_json_if_exists(summary_path)
    validation = _read_json_if_exists(validation_path)
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
            "name": "retrieval_summary_reviewer_ready",
            "passed": bool(summary and summary.get("reviewer_ready")),
            "details": {"reviewer_ready": bool(summary and summary.get("reviewer_ready"))},
        },
    ]
    return {
        "index_path": str(index_path),
        "summary_path": str(summary_path),
        "validation_path": str(validation_path),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


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
