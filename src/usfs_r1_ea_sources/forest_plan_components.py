from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .ea_review import _search_package_chunks
from .forest_plan_inventory_build_manifest import (
    DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH,
    load_region1_forest_plan_inventory_build_manifest,
)
from .forest_plan_profiles import load_forest_plan_profile


FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION = "forest-plan-component-inventory-v0"
FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION = "forest-plan-component-findings-v0"
FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION = (
    "forest-plan-reviewer-resolution-queue-v0"
)
FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-inventory-coverage-v0"
)
FOREST_PLAN_APPLICABLE_STANDARD_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-applicable-standard-coverage-v0"
)
FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-inventory-build-coverage-v0"
)
DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "forest_plan_component_inventory_seed.json"
)
VALID_COMPONENT_TYPES = {
    "desired_condition",
    "goal",
    "guideline",
    "monitoring",
    "objective",
    "plan_amendment",
    "standard",
    "suitability",
}
VALID_APPLICABILITY_STATUSES = {
    "applicable",
    "candidate",
    "not_applicable",
    "needs_reviewer_resolution",
}
VALID_FINDING_STATUSES = {
    "supported",
    "partial",
    "gap",
    "not_applicable",
    "needs_reviewer_resolution",
}
VALID_COMPLIANCE_STATUSES = {
    "complies",
    "potential_noncompliance",
    "insufficient_evidence",
    "not_applicable",
    "needs_reviewer_resolution",
    "not_evaluated_for_compliance",
}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
COMPONENT_LABEL_PATTERN = (
    r"Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability"
)
COMPONENT_NUMBER_RE = re.compile(r"^[0-9][A-Za-z0-9.]*$")
COMPONENT_LABEL_RE = re.compile(
    rf"\b(?P<label>{COMPONENT_LABEL_PATTERN})"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[0-9][A-Za-z0-9.]*)\s+"
    rf"(?P<text>.*?)(?=\b(?:{COMPONENT_LABEL_PATTERN})"
    r"\s*\([A-Za-z0-9-]+\)\s*[A-Za-z0-9.]+\s+|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)
COMPONENT_LABEL_CANDIDATE_RE = re.compile(
    rf"\b(?P<label>{COMPONENT_LABEL_PATTERN})"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[A-Za-z0-9.]+)\s+"
    rf"(?P<text>.*?)(?=\b(?:{COMPONENT_LABEL_PATTERN})"
    r"\s*\([A-Za-z0-9-]+\)\s*[A-Za-z0-9.]+\s+|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)
COMPONENT_CODE_ABBREVIATION_PATTERN = r"DC|GO|GDL|GL|MON|OBJ|STD|SUIT"
CODED_COMPONENT_RE = re.compile(
    rf"(?P<label>{COMPONENT_LABEL_PATTERN})\s+"
    r"(?P<code>(?:[A-Z0-9]{1,4})-(?P<abbr>"
    + COMPONENT_CODE_ABBREVIATION_PATTERN
    + r")(?:-[A-Z0-9]+)*)-(?P<number>[0-9]{1,2})[.:]\s+"
    r"(?P<text>.*?)(?=(?:(?:"
    + COMPONENT_LABEL_PATTERN
    + r")\s+)?(?:[A-Z0-9]{1,4})-(?:"
    + COMPONENT_CODE_ABBREVIATION_PATTERN
    + r")(?:-[A-Z0-9]+)*-[0-9]{1,2}[.:]\s+|\b(?:"
    + COMPONENT_LABEL_PATTERN
    + r")\s+[0-9][A-Za-z0-9.:-]*\s*:|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)
COLON_COMPONENT_RE = re.compile(
    rf"\b(?P<label>{COMPONENT_LABEL_PATTERN})\s+"
    r"(?P<number>[0-9][A-Za-z0-9.:-]*)\s*:\s+"
    r"(?P<text>.*?)(?=\b(?:"
    + COMPONENT_LABEL_PATTERN
    + r")\s+[0-9][A-Za-z0-9.:-]*\s*:|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)
SECTION_HEADING_RE = re.compile(
    r"Plan Components[-\u2013\u2014]\s*(?P<section>[^.]+)",
    re.IGNORECASE,
)
LEGACY_SECTION_HEADING_RE = re.compile(
    rf"(?P<section>[A-Z][A-Za-z/&,\-]+(?:\s+[A-Z][A-Za-z/&,\-]+){{0,6}})\s+"
    rf"(?:{COMPONENT_LABEL_PATTERN})\b",
)
LEADING_COMPONENT_LABEL_RE = re.compile(
    r"^(?:Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\([A-Za-z0-9-]+\)\s*[0-9][A-Za-z0-9.]*\s+",
    re.IGNORECASE,
)
COMPONENT_CODE_NUMBER_RE = re.compile(
    r"^(?:Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[0-9][A-Za-z0-9.]*)\b",
    re.IGNORECASE,
)
PLAN_CONSISTENCY_YES_NO = {"yes", "no"}
MODAL_BOUNDARY_RE = re.compile(
    r"\b(?:shall|must|should|may|will|would|is|are|includes?|contains?|allows?|prohibits?)\b",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"[a-z][a-z0-9-]*")
TERM_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "component",
    "components",
    "for",
    "forest",
    "forestwide",
    "from",
    "in",
    "is",
    "may",
    "must",
    "new",
    "not",
    "of",
    "or",
    "project",
    "shall",
    "should",
    "that",
    "the",
    "to",
    "will",
    "with",
}
GENERIC_COMPONENT_TERMS = {
    *TERM_STOPWORDS,
    "action",
    "actions",
    "activities",
    "activity",
    "area",
    "areas",
    "authorized",
    "custer",
    "direction",
    "gallatin",
    "management",
    "national",
    "provide",
    "provides",
    "protect",
    "related",
    "resource",
    "resources",
}
LEGACY_SECTION_STOPWORDS = {
    "chapter",
    "direction",
    "forest",
    "forestwide",
    "goals",
    "goal",
    "guidelines",
    "guideline",
    "land",
    "management",
    "monitoring",
    "national",
    "objectives",
    "objective",
    "plan",
    "standards",
    "standard",
}
SECTION_FAMILY_KEYWORDS = {
    "hydrology": {
        "aquatic",
        "aquatics",
        "floodplain",
        "floodplains",
        "hydrology",
        "riparian",
        "river",
        "rivers",
        "stream",
        "streams",
        "water",
        "watershed",
        "watersheds",
        "wetland",
        "wetlands",
    },
    "wildlife": {
        "bat",
        "bear",
        "big game",
        "carnivore",
        "elk",
        "fisheries",
        "grizzly",
        "lynx",
        "prairie dog",
        "sage-grouse",
        "species",
        "wildlife habitat",
        "wildlife",
        "wolverine",
    },
    "botany": {
        "at-risk plant",
        "botany",
        "invasive",
        "plant",
        "plants",
        "vegetation",
        "whitebark",
        "weed",
    },
    "scenery": {
        "aesthetic",
        "aesthetics",
        "landscape character",
        "natural appearing",
        "scenery",
        "scenic",
        "visual",
        "viewshed",
    },
    "sustainability": {
        "carbon",
        "climate",
        "ecosystem services",
        "resilience",
        "resilient",
        "sustainability",
        "sustainable",
    },
    "recreation_access": {
        "access",
        "backcountry",
        "bicycle",
        "event",
        "events",
        "facility",
        "facilities",
        "mechanized",
        "motorized",
        "nonmotorized",
        "recreation",
        "road",
        "roadless",
        "roads",
        "trail",
        "trails",
        "transport",
    },
    "land_exchange": {
        "acquired",
        "acquisition",
        "conveyance",
        "estate",
        "exchange",
        "federal",
        "land exchange",
        "parcel",
        "parcels",
    },
    "minerals": {
        "geologic",
        "mineral",
        "minerals",
        "palladium",
        "platinum",
        "saleable",
    },
}


@dataclass(frozen=True)
class ForestPlanComponentEvaluationResult:
    findings_path: Path
    markdown_path: Path
    reviewer_resolution_queue_path: Path
    component_inventory_coverage_path: Path
    applicable_standard_coverage_path: Path
    summary: dict


@dataclass(frozen=True)
class ForestPlanComponentInventoryBuildResult:
    inventory_path: Path
    components_jsonl_path: Path
    coverage_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class _ForestPlanInventoryProfileBuild:
    forest_unit_id: str
    plan_version: str
    primary_plan_source_record_id: str
    source_record_ids: tuple[str, ...]
    coverage: dict


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
        if manifest.source_set_reference(row.source_set_reference_id).source_set_id == source_set_id
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
        and chunk.get("document_role") == "forest_plan"
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


def _components_from_chunk(
    *,
    chunk: dict,
    forest_unit_id: str,
    plan_version: str,
    source_set_id: str,
    geographic_area_ids: list[str],
    management_area_ids: list[str],
    overlay_ids: list[str],
    profile_context: dict[str, tuple[object, ...]],
) -> list[dict]:
    text = str(chunk.get("text") or "")
    components = []
    fallback_heading = str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components")
    for match in _component_matches(text, fallback_heading=fallback_heading):
        label = match["label"]
        code = match["code"]
        number = match["number"]
        component_body = _compact(match["text"], limit=10000)
        if _suppress_component_match(match, component_body):
            continue
        component_text = _compact(f"{label} ({code}) {number} {component_body}", limit=10000)
        section_heading = match["section_heading"]
        context_text = (
            f"{section_heading} {code} "
            f"{code.replace('-', ' ')} "
            f"{_component_context_window(text=text, start=match['start'], end=match['end'])} "
            f"{component_text}"
        )
        source_chunk_ids = [str(chunk.get("chunk_id") or "").strip()]
        source_chunk_ids = [chunk_id for chunk_id in source_chunk_ids if chunk_id]
        package_evidence_terms = _package_evidence_terms_from_text(component_text)
        resource_topics = _resource_topics_from_terms(
            terms=package_evidence_terms,
            code=code,
            section_heading=section_heading,
        )
        components.append(
            {
                "component_id": _component_id(
                    source_record_id=str(chunk.get("source_record_id") or ""),
                    code=code,
                    number=number,
                ),
                "forest_unit_id": forest_unit_id,
                "plan_version": plan_version,
                "source_set_id": source_set_id,
                "source_record_id": str(chunk.get("source_record_id") or ""),
                "component_type": _component_type_from_label(label),
                "section_id": _safe_identifier(section_heading),
                "section_heading": section_heading,
                "page": chunk.get("page") if isinstance(chunk.get("page"), int) else None,
                "citation_label": str(chunk.get("citation_label") or chunk.get("title") or ""),
                "component_text": component_text,
                "geographic_area_ids": _dedupe_preserve_order(
                    [
                        *geographic_area_ids,
                        *_matching_profile_entry_ids(
                            context_text,
                            profile_context.get("geographic_area_terms", ()),
                        ),
                    ]
                ),
                "management_area_ids": _dedupe_preserve_order(
                    [
                        *management_area_ids,
                        *_matching_profile_entry_ids(
                            context_text,
                            profile_context.get("management_area_terms", ()),
                        ),
                    ]
                ),
                "overlay_ids": _dedupe_preserve_order(
                    [
                        *overlay_ids,
                        *_matching_profile_entry_ids(
                            context_text,
                            profile_context.get("overlay_terms", ()),
                        ),
                    ]
                ),
                "resource_topics": resource_topics,
                "activity_tags": package_evidence_terms,
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": str(chunk.get("artifact_sha256") or ""),
                "content_sha256": str(chunk.get("content_sha256") or ""),
                "provenance": _component_provenance(
                    chunk=chunk,
                    source_chunk_ids=source_chunk_ids,
                ),
                "package_evidence_terms": package_evidence_terms,
            }
        )
    return components


def _component_inventory_build_coverage(
    *,
    source_set_id: str,
    source_record_ids: tuple[str, ...],
    chunks_path: Path,
    chunks: list[dict],
    components: list[dict],
    validation_errors: list[dict],
    profile_builds: list[_ForestPlanInventoryProfileBuild] | None = None,
) -> dict:
    detected_labels = _merge_overlapping_detected_labels(_detected_component_labels(chunks))
    inventory_quality_issues = _component_inventory_quality_issues(chunks)
    blocking_inventory_quality_issues = [
        issue for issue in inventory_quality_issues if issue.get("severity") == "error"
    ]
    detected_standards = [
        label for label in detected_labels if label["component_type"] == "standard"
    ]
    detected_component_ids = [label["component_id"] for label in detected_labels]
    detected_standard_ids = [label["component_id"] for label in detected_standards]
    built_component_ids = [str(component.get("component_id") or "") for component in components]
    built_standard_ids = [
        str(component.get("component_id") or "")
        for component in components
        if component.get("component_type") == "standard"
    ]
    missing_component_ids = sorted(set(detected_component_ids) - set(built_component_ids))
    missing_standard_ids = sorted(set(detected_standard_ids) - set(built_standard_ids))
    duplicate_component_ids = _duplicate_values(built_component_ids)
    duplicate_standard_ids = _duplicate_values(detected_standard_ids)
    checks = [
        {
            "name": "selected_forest_plan_chunks_present",
            "passed": bool(chunks),
            "details": {"chunk_count": len(chunks), "chunks_path": str(chunks_path)},
        },
        {
            "name": "labeled_components_detected",
            "passed": bool(detected_labels),
            "details": {"detected_component_count": len(detected_labels)},
        },
        {
            "name": "standard_components_detected",
            "passed": bool(detected_standards),
            "details": {"detected_standard_count": len(detected_standards)},
        },
        {
            "name": "all_detected_components_built",
            "passed": not missing_component_ids,
            "details": {"component_ids": missing_component_ids},
        },
        {
            "name": "all_detected_standards_built",
            "passed": not missing_standard_ids,
            "details": {"component_ids": missing_standard_ids},
        },
        {
            "name": "built_component_ids_are_unique",
            "passed": not duplicate_component_ids,
            "details": {"component_ids": duplicate_component_ids},
        },
        {
            "name": "detected_standard_labels_are_unique",
            "passed": not duplicate_standard_ids,
            "details": {"component_ids": duplicate_standard_ids},
        },
        {
            "name": "built_component_records_validate",
            "passed": not validation_errors,
            "details": {"errors": validation_errors},
        },
        {
            "name": "blocking_inventory_quality_issues_absent",
            "passed": not blocking_inventory_quality_issues,
            "details": {
                "issue_count": len(blocking_inventory_quality_issues),
                "issues": blocking_inventory_quality_issues,
            },
        },
    ]
    profile_results = []
    if profile_builds:
        failed_profile_builds = []
        missing_profile_chunks = []
        for profile_build in profile_builds:
            profile_coverage = profile_build.coverage
            failed_checks = [
                check["name"]
                for check in profile_coverage["checks"]
                if not check["passed"]
            ]
            blocker_types = _component_inventory_profile_blocker_types(
                failed_checks=failed_checks,
                selected_chunk_count=profile_coverage["selected_chunk_count"],
                built_component_count=profile_coverage["built_component_count"],
                built_standard_count=profile_coverage["built_standard_count"],
                duplicate_component_ids=profile_coverage["duplicate_component_ids"],
                duplicate_standard_ids=profile_coverage["duplicate_standard_ids"],
            )
            profile_results.append(
                {
                    "forest_unit_id": profile_build.forest_unit_id,
                    "plan_version": profile_build.plan_version,
                    "primary_plan_source_record_id": (
                        profile_build.primary_plan_source_record_id
                    ),
                    "source_record_ids": list(profile_build.source_record_ids),
                    "selected_chunk_count": profile_coverage["selected_chunk_count"],
                    "detected_component_count": profile_coverage["detected_component_count"],
                    "detected_standard_count": profile_coverage["detected_standard_count"],
                    "built_component_count": profile_coverage["built_component_count"],
                    "built_standard_count": profile_coverage["built_standard_count"],
                    "missing_component_ids": profile_coverage["missing_component_ids"],
                    "missing_standard_ids": profile_coverage["missing_standard_ids"],
                    "duplicate_component_ids": profile_coverage["duplicate_component_ids"],
                    "duplicate_standard_ids": profile_coverage["duplicate_standard_ids"],
                    "inventory_quality_issue_count": profile_coverage[
                        "inventory_quality_issue_count"
                    ],
                    "blocking_inventory_quality_issue_count": profile_coverage[
                        "blocking_inventory_quality_issue_count"
                    ],
                    "validation_error_count": len(profile_coverage["validation_errors"]),
                    "failed_checks": failed_checks,
                    "blocker_types": blocker_types,
                    "passed": profile_coverage["passed"],
                }
            )
            if not profile_coverage["passed"]:
                failed_profile_builds.append(profile_build.forest_unit_id)
            if profile_coverage["selected_chunk_count"] == 0:
                missing_profile_chunks.append(profile_build.forest_unit_id)
        checks.extend(
            [
                {
                    "name": "all_profile_builds_pass",
                    "passed": not failed_profile_builds,
                    "details": {"forest_unit_ids": failed_profile_builds},
                },
                {
                    "name": "all_profile_builds_have_selected_chunks",
                    "passed": not missing_profile_chunks,
                    "details": {"forest_unit_ids": missing_profile_chunks},
                },
            ]
        )
    return {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "source_record_id": source_record_ids[0] if len(source_record_ids) == 1 else None,
        "source_record_ids": list(source_record_ids),
        "build_scope": "manifest_batch" if profile_builds else "single_forest",
        "chunks_path": str(chunks_path),
        "selected_chunk_count": len(chunks),
        "detected_component_count": len(detected_labels),
        "detected_standard_count": len(detected_standards),
        "built_component_count": len(components),
        "built_standard_count": len(built_standard_ids),
        "inventory_quality_issue_count": len(inventory_quality_issues),
        "blocking_inventory_quality_issue_count": len(blocking_inventory_quality_issues),
        "missing_component_ids": missing_component_ids,
        "missing_standard_ids": missing_standard_ids,
        "duplicate_component_ids": duplicate_component_ids,
        "duplicate_standard_ids": duplicate_standard_ids,
        "validation_errors": validation_errors,
        "inventory_quality_issues": inventory_quality_issues,
        "detected_component_labels": detected_labels,
        "detected_standard_labels": detected_standards,
        "profile_results": profile_results,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _component_inventory_profile_blocker_types(
    *,
    failed_checks: list[str],
    selected_chunk_count: int,
    built_component_count: int,
    built_standard_count: int,
    duplicate_component_ids: list[str],
    duplicate_standard_ids: list[str],
) -> list[str]:
    blockers = []
    failed = set(failed_checks)
    if selected_chunk_count == 0:
        blockers.append("no_selected_forest_plan_chunks")
    if (
        "labeled_components_detected" in failed
        and built_component_count == 0
    ):
        blockers.append("plan_component_labels_not_detected")
    if (
        "standard_components_detected" in failed
        and built_standard_count == 0
    ):
        blockers.append("plan_standard_labels_not_detected")
    if "built_component_ids_are_unique" in failed and duplicate_component_ids:
        blockers.append("duplicate_component_ids_detected")
    if "detected_standard_labels_are_unique" in failed and duplicate_standard_ids:
        blockers.append("duplicate_standard_ids_detected")
    if not blockers and failed_checks:
        blockers.extend(sorted(failed))
    return blockers


def _component_matches(text: str, *, fallback_heading: str) -> list[dict[str, object]]:
    matches = []
    for regex in (COMPONENT_LABEL_RE, CODED_COMPONENT_RE, COLON_COMPONENT_RE):
        for match in regex.finditer(text):
            normalized = _normalized_component_match(
                text=text,
                match=match,
                fallback_heading=fallback_heading,
            )
            if normalized is not None:
                matches.append(normalized)
    matches.sort(key=lambda item: (int(item["start"]), -len(str(item["text"]))))
    deduped = []
    seen = set()
    for item in matches:
        key = (item["start"], item["code"], item["number"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _normalized_component_match(
    *,
    text: str,
    match: re.Match[str],
    fallback_heading: str,
) -> dict[str, object] | None:
    groups = match.groupdict()
    start, end = match.span()
    label = str(groups.get("label") or "").strip()
    number = str(groups.get("number") or "").strip().rstrip(":.")
    component_text = str(groups.get("text") or "").strip()
    if not component_text or not number:
        return None
    if match.re is COMPONENT_LABEL_RE:
        code = str(groups.get("code") or "").strip()
    elif match.re is CODED_COMPONENT_RE:
        code = str(groups.get("code") or "").strip()
        abbr = str(groups.get("abbr") or "").strip()
        if not label:
            label = _component_label_from_code_abbreviation(abbr)
        if _looks_like_coded_component_header(component_text):
            return None
    elif match.re is COLON_COMPONENT_RE:
        if _looks_like_component_table_of_contents(component_text):
            return None
        section_heading = _legacy_section_heading_for_match(
            text=text,
            start=start,
            fallback=fallback_heading,
        )
        code = _legacy_component_code(
            section_heading=section_heading,
            label=label,
            component_body=component_text,
            text=text,
            start=start,
            fallback_heading=fallback_heading,
        )
        return {
            "label": label,
            "code": code,
            "number": number,
            "text": component_text,
            "section_heading": section_heading,
            "start": start,
            "end": end,
        }
    else:
        return None
    if not label or not code:
        return None
    return {
        "label": label,
        "code": code,
        "number": number,
        "text": component_text,
        "section_heading": _section_heading_for_match(
            text=text,
            start=start,
            fallback=fallback_heading,
        ),
        "start": start,
        "end": end,
    }


def _component_label_from_code_abbreviation(abbr: str) -> str:
    normalized = abbr.strip().upper()
    mapping = {
        "DC": "Desired Conditions",
        "GO": "Goals",
        "GL": "Guidelines",
        "GDL": "Guidelines",
        "MON": "Monitoring",
        "OBJ": "Objectives",
        "STD": "Standards",
        "SUIT": "Suitability",
    }
    return mapping.get(normalized, "Standards")


def _component_abbreviation_from_label(label: str) -> str:
    normalized = " ".join(label.lower().split())
    if normalized.startswith("desired condition"):
        return "DC"
    if normalized.startswith("goal"):
        return "GO"
    if normalized.startswith("guideline"):
        return "GL"
    if normalized.startswith("monitoring"):
        return "MON"
    if normalized.startswith("objective"):
        return "OBJ"
    if normalized.startswith("standard"):
        return "STD"
    if normalized.startswith("suitability"):
        return "SUIT"
    return "COMP"


def _legacy_component_code(
    *,
    section_heading: str,
    label: str,
    component_body: str,
    text: str,
    start: int,
    fallback_heading: str,
) -> str:
    section_code = _legacy_section_code(section_heading)
    fallback_code = _legacy_section_code(fallback_heading)
    if section_code and section_code == fallback_code:
        section_code = _legacy_body_code(component_body)
    if not section_code:
        goal_number = _legacy_parent_goal_number(text=text, start=start)
        if goal_number:
            section_code = f"GOAL-{goal_number}"
    if not section_code:
        section_code = _legacy_body_code(component_body)
    abbreviation = _component_abbreviation_from_label(label)
    if section_code:
        return _safe_identifier(f"{section_code}-{abbreviation}").upper()
    return abbreviation


def _legacy_parent_goal_number(*, text: str, start: int) -> str:
    prefix = text[max(0, start - 2000) : start]
    matches = list(re.finditer(r"\bGoal\s+(?P<number>[0-9][A-Za-z0-9.]*)\s*:", prefix, re.IGNORECASE))
    if not matches:
        return ""
    return _safe_identifier(matches[-1].group("number")).upper()


def _legacy_section_code(section_heading: str) -> str:
    parts = [
        part.upper()
        for part in TOKEN_RE.findall(section_heading.lower())
        if part not in LEGACY_SECTION_STOPWORDS
    ]
    return "-".join(parts[:4])


def _looks_like_component_table_of_contents(text: str) -> bool:
    prefix = text[:160]
    return bool(re.search(r"\.{5,}", prefix))


def _looks_like_coded_component_header(text: str) -> bool:
    normalized = " ".join(text.split())
    tokens = TOKEN_RE.findall(normalized.lower())
    return bool(
        re.search(r"\b\d+\s*$", normalized)
        and len(tokens) <= 12
        and "." not in normalized
    )


def _legacy_body_code(text: str) -> str:
    parts = [
        token.upper()
        for token in TOKEN_RE.findall(text.lower())
        if token not in TERM_STOPWORDS
    ]
    return "-".join(parts[:4])


def _suppress_component_match(match: dict[str, object], component_body: str) -> bool:
    return _suppress_tabular_component_label(
        label=str(match["label"]),
        code=str(match["code"]),
        number=str(match["number"]),
        text=component_body,
    )


def _detected_component_labels(chunks: list[dict]) -> list[dict]:
    labels = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        fallback_heading = str(
            chunk.get("heading") or chunk.get("title") or "Forest Plan Components"
        )
        for match in _component_matches(text, fallback_heading=fallback_heading):
            if _suppress_component_match(match, match["text"]):
                continue
            component_type = _component_type_from_label(match["label"])
            component_id = _component_id(
                source_record_id=str(chunk.get("source_record_id") or ""),
                code=match["code"],
                number=match["number"],
            )
            component_text = _compact(
                f"{match['label']} ({match['code']}) "
                f"{match['number']} {match['text']}",
                limit=10000,
            )
            labels.append(
                {
                    "component_id": component_id,
                    "component_type": component_type,
                    "label": match["label"],
                    "code": match["code"],
                    "number": match["number"],
                    "component_text": component_text,
                    "source_record_id": str(chunk.get("source_record_id") or ""),
                    "chunk_id": str(chunk.get("chunk_id") or ""),
                    "section_heading": match["section_heading"],
                }
            )
    return labels


def _component_inventory_quality_issues(chunks: list[dict]) -> list[dict]:
    issues = []
    seen = set()
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        for match in COMPONENT_LABEL_RE.finditer(text):
            label = match.group("label")
            code = match.group("code")
            number = match.group("number")
            component_text = match.group("text")
            if not _suppress_tabular_component_label(
                label=label,
                code=code,
                number=number,
                text=component_text,
            ):
                continue
            source_record_id = str(chunk.get("source_record_id") or "")
            candidate_component_id = _component_id(
                source_record_id=source_record_id,
                code=code,
                number=number,
            )
            chunk_id = str(chunk.get("chunk_id") or "")
            dedupe_key = ("tabular_component_label", candidate_component_id, chunk_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            section_heading = _section_heading_for_match(
                text=text,
                start=match.start(),
                fallback=str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components"),
            )
            issues.append(
                {
                    "issue_id": _safe_identifier(
                        f"{candidate_component_id}-tabular-component-label-{chunk_id or 'chunk'}"
                    ),
                    "issue_type": "tabular_component_label",
                    "severity": "warning",
                    "candidate_component_id": candidate_component_id,
                    "suggested_component_id": None,
                    "label": label,
                    "code": code,
                    "number_token": number,
                    "source_record_id": source_record_id,
                    "chunk_id": chunk_id,
                    "section_heading": section_heading,
                    "candidate_text": _compact(
                        f"{label} ({code}) {number} {component_text}",
                        limit=1200,
                    ),
                    "message": (
                        "Component-like label was suppressed because it matches a tabular "
                        "max/min statistic heading rather than a plan component."
                    ),
                }
            )
        for match in COMPONENT_LABEL_CANDIDATE_RE.finditer(text):
            number = match.group("number")
            if COMPONENT_NUMBER_RE.match(number):
                continue
            label = match.group("label")
            code = match.group("code")
            source_record_id = str(chunk.get("source_record_id") or "")
            candidate_component_id = _component_id(
                source_record_id=source_record_id,
                code=code,
                number=number,
            )
            suggested_number = _suggested_component_number(
                number_token=number,
                text=match.group("text"),
            )
            suggested_component_id = (
                _component_id(
                    source_record_id=source_record_id,
                    code=code,
                    number=suggested_number,
                )
                if suggested_number
                else None
            )
            issue_type = _component_inventory_quality_issue_type(
                number=number,
                text=match.group("text"),
            )
            chunk_id = str(chunk.get("chunk_id") or "")
            dedupe_key = (
                issue_type,
                candidate_component_id,
                suggested_component_id,
                chunk_id,
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            section_heading = _section_heading_for_match(
                text=text,
                start=match.start(),
                fallback=str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components"),
            )
            issues.append(
                {
                    "issue_id": _safe_identifier(
                        f"{candidate_component_id}-{issue_type}-{chunk_id or 'chunk'}"
                    ),
                    "issue_type": issue_type,
                    "severity": "warning",
                    "candidate_component_id": candidate_component_id,
                    "suggested_component_id": suggested_component_id,
                    "label": label,
                    "code": code,
                    "number_token": number,
                    "source_record_id": source_record_id,
                    "chunk_id": chunk_id,
                    "section_heading": section_heading,
                    "candidate_text": _compact(
                        f"{label} ({code}) {number} {match.group('text')}",
                        limit=1200,
                    ),
                    "message": (
                        "Component-like label was not built because the token after the "
                        "component code is not numeric; inspect whether this is a "
                        "cross-reference/table heading or should be normalized."
                    ),
                }
            )
    return issues


def _component_inventory_quality_issue_type(*, number: str, text: str) -> str:
    normalized_number = number.strip().lower()
    normalized_text = _normalized_component_text(text)
    if normalized_number in {"see", "table"} or normalized_text.startswith("see "):
        return "cross_reference_component_label"
    return "non_numeric_component_label"


def _suppress_tabular_component_label(
    *,
    label: str,
    code: str,
    number: str,
    text: str,
) -> bool:
    normalized_label = label.strip().lower()
    normalized_code = code.strip().lower()
    normalized_text = _normalized_component_text(text)
    if normalized_label not in {"standard", "standards"}:
        return False
    if normalized_code not in {"max", "min"}:
        return False
    if not number.isdigit():
        return False
    return normalized_text.startswith("status selected standard")


def _suggested_component_number(*, number_token: str, text: str) -> str | None:
    if number_token.strip().lower() in {"table", "figure", "appendix"}:
        return None
    match = re.search(r"(?:\A|[.!?]\s+)(?P<number>[0-9][A-Za-z0-9.]*)\s+\S", text)
    if not match:
        return None
    number = match.group("number").strip().rstrip(".")
    return number if COMPONENT_NUMBER_RE.match(number) else None


def _profile_context_terms(forest_unit_id: str) -> dict[str, tuple[object, ...]]:
    try:
        profile = load_forest_plan_profile(forest_unit_id)
    except (FileNotFoundError, KeyError, ValueError):
        return {}
    return {
        "geographic_area_terms": profile.geographic_area_terms,
        "management_area_terms": profile.management_area_terms,
        "overlay_terms": profile.overlay_terms,
    }


def _matching_profile_entry_ids(text: str, entries: tuple[object, ...]) -> list[str]:
    normalized_text = _normalized_component_text(text)
    text_tokens = set(TOKEN_RE.findall(normalized_text))
    text_tokens.update(
        part
        for token in list(text_tokens)
        for part in token.split("-")
        if part
    )
    matches = []
    for entry in entries:
        entry_id = str(getattr(entry, "entry_id", "") or "").strip()
        terms = _profile_entry_context_terms(entry)
        if not entry_id:
            continue
        for term in terms:
            normalized_term = _normalized_component_text(str(term))
            if not normalized_term:
                continue
            if " " in normalized_term and normalized_term in normalized_text:
                matches.append(entry_id)
                break
            if " " not in normalized_term and normalized_term in text_tokens:
                matches.append(entry_id)
                break
    return _dedupe_preserve_order(matches)


def _profile_entry_context_terms(entry: object) -> tuple[str, ...]:
    terms = [str(term).strip() for term in getattr(entry, "terms", ()) if str(term).strip()]
    category = str(getattr(entry, "category", "") or "").strip()
    if category == "geographic_area":
        for term in list(terms):
            shortened = re.sub(r"\s+Geographic\s+Area\Z", "", term, flags=re.IGNORECASE).strip()
            if shortened and shortened != term and len(TOKEN_RE.findall(shortened.lower())) >= 2:
                terms.append(shortened)
                singular = re.sub(r"\bMountains\b", "Mountain", shortened, flags=re.IGNORECASE)
                if singular and singular != shortened:
                    terms.append(singular)
    return tuple(_dedupe_preserve_order(terms))


def _merge_overlapping_component_records(components: list[dict]) -> list[dict]:
    merged = []
    for _component_id, group in _group_by_component_id(components):
        if len(group) == 1 or not _overlapping_duplicate_group(group):
            merged.extend(group)
            continue
        base = max(group, key=lambda component: len(str(component.get("component_text") or "")))
        combined = dict(base)
        source_chunk_ids = _dedupe_preserve_order(
            [
                chunk_id
                for component in group
                for chunk_id in component.get("source_chunk_ids", [])
                if str(chunk_id).strip()
            ]
        )
        combined["source_chunk_ids"] = source_chunk_ids
        provenance = dict(combined.get("provenance") or {})
        entity = dict(provenance.get("entity") or {})
        entity["source_chunk_ids"] = source_chunk_ids
        provenance["entity"] = entity
        combined["provenance"] = provenance
        merged.append(combined)
    return merged


def _merge_overlapping_detected_labels(labels: list[dict]) -> list[dict]:
    merged = []
    for _component_id, group in _group_by_component_id(labels):
        if len(group) == 1 or not _overlapping_duplicate_group(group):
            merged.extend(group)
            continue
        merged.append(max(group, key=lambda label: len(str(label.get("component_text") or ""))))
    return merged


def _group_by_component_id(items: list[dict]) -> list[tuple[str, list[dict]]]:
    grouped: dict[str, list[dict]] = {}
    order = []
    for item in items:
        component_id = str(item.get("component_id") or "")
        if component_id not in grouped:
            grouped[component_id] = []
            order.append(component_id)
        grouped[component_id].append(item)
    return [(component_id, grouped[component_id]) for component_id in order]


def _overlapping_duplicate_group(group: list[dict]) -> bool:
    chunk_ids = [_primary_source_chunk_id(item) for item in group]
    chunk_ids = [chunk_id for chunk_id in chunk_ids if chunk_id]
    if len(set(chunk_ids)) <= 1:
        return False
    if len({str(item.get("component_type") or "") for item in group}) > 1:
        return False
    texts = [_normalized_component_text(str(item.get("component_text") or "")) for item in group]
    if any(not text for text in texts):
        return False
    longest = max(texts, key=len)
    return all(text == longest or text in longest for text in texts)


def _primary_source_chunk_id(item: dict) -> str:
    if item.get("chunk_id"):
        return str(item["chunk_id"])
    source_chunk_ids = item.get("source_chunk_ids")
    if isinstance(source_chunk_ids, list) and source_chunk_ids:
        return str(source_chunk_ids[0])
    return ""


def _component_type_from_label(label: str) -> str:
    normalized = " ".join(label.lower().split())
    if normalized.startswith("desired condition"):
        return "desired_condition"
    if normalized.startswith("goal"):
        return "goal"
    if normalized.startswith("guideline"):
        return "guideline"
    if normalized.startswith("monitoring"):
        return "monitoring"
    if normalized.startswith("objective"):
        return "objective"
    if normalized.startswith("standard"):
        return "standard"
    if normalized.startswith("suitability"):
        return "suitability"
    raise ValueError(f"Unsupported forest-plan component label: {label!r}.")


def _section_heading_for_match(*, text: str, start: int, fallback: str) -> str:
    prefix = text[:start]
    matches = list(SECTION_HEADING_RE.finditer(prefix))
    if matches:
        section = _compact(matches[-1].group("section"), limit=240)
        return f"Plan Components-{section}"
    return _legacy_section_heading_for_match(text=text, start=start, fallback=fallback)


def _legacy_section_heading_for_match(*, text: str, start: int, fallback: str) -> str:
    prefix = text[max(0, start - 2000) : start]
    matches = list(LEGACY_SECTION_HEADING_RE.finditer(prefix))
    if matches:
        return _compact(matches[-1].group("section"), limit=240)
    return _compact(fallback, limit=240)


def _component_context_window(*, text: str, start: int, end: int) -> str:
    window_start = max(0, start - 1200)
    window_end = min(len(text), end + 400)
    return _compact(text[window_start:window_end], limit=2000)


def _component_id(*, source_record_id: str, code: str, number: str) -> str:
    return _safe_identifier(f"{source_record_id}-{code}-{number}")


def _safe_identifier(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized:
        return "unknown"
    return normalized


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _normalized_component_text(value: str) -> str:
    return " ".join(TOKEN_RE.findall(str(value).lower()))


def _package_evidence_terms_from_text(text: str) -> list[str]:
    component_body = LEADING_COMPONENT_LABEL_RE.sub("", _compact(text, limit=10000)).strip()
    first_sentence = re.split(r"(?<=[.?!])\s+", component_body, maxsplit=1)[0]
    modal_match = MODAL_BOUNDARY_RE.search(first_sentence)
    candidates = []
    if modal_match:
        candidates.append(first_sentence[: modal_match.start()])
    candidates.append(first_sentence)
    candidates.extend(_content_ngrams(first_sentence, max_terms=6))
    return _dedupe_terms(candidates)


def _content_ngrams(text: str, *, max_terms: int) -> list[str]:
    tokens = [token for token in TOKEN_RE.findall(text.lower()) if token not in TERM_STOPWORDS]
    terms = []
    for size in range(min(5, len(tokens)), 1, -1):
        for index in range(0, len(tokens) - size + 1):
            terms.append(" ".join(tokens[index : index + size]))
            if len(terms) >= max_terms:
                return terms
    return terms


def _dedupe_terms(candidates: list[str]) -> list[str]:
    terms = []
    seen = set()
    for candidate in candidates:
        term = re.sub(r"[^A-Za-z0-9 -]+", " ", candidate.lower())
        term = " ".join(term.split())
        if not term or term in seen:
            continue
        content_tokens = [
            token for token in TOKEN_RE.findall(term) if token not in TERM_STOPWORDS
        ]
        if not content_tokens:
            continue
        seen.add(term)
        terms.append(term)
    return terms


def _resource_topics_from_terms(
    *,
    terms: list[str],
    code: str,
    section_heading: str,
) -> list[str]:
    resource_topics = terms[:3]
    if not resource_topics:
        resource_topics = _content_ngrams(f"{section_heading} {code}", max_terms=3)
    if not resource_topics:
        resource_topics = [_safe_identifier(code).lower()]
    return resource_topics


def _component_provenance(*, chunk: dict, source_chunk_ids: list[str]) -> dict:
    return {
        "entity": {
            "type": "forest_plan_component",
            "source_record_id": str(chunk.get("source_record_id") or ""),
            "source_chunk_ids": source_chunk_ids,
            "artifact_sha256": str(chunk.get("artifact_sha256") or ""),
            "content_sha256": str(chunk.get("content_sha256") or ""),
        },
        "activity": {
            "type": "forest_plan_component_inventory_build",
            "created_at": _utc_now(),
            "source": str(chunk.get("source_text_path") or ""),
        },
        "agent": {
            "type": "deterministic_code",
            "name": "usfs_r1_ea_sources.forest_plan_components",
            "version": FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
        },
    }


def run_forest_plan_component_evaluation(
    *,
    review_id: str,
    review_dir: Path,
    context: dict,
    package_chunks: list[dict],
    component_inventory_path: Path,
    forest_unit_id: str,
    source_set_id: str | None,
    index_path: Path | None,
    package_top_k: int = 3,
    source_top_k: int = 3,
) -> ForestPlanComponentEvaluationResult:
    """Evaluate profile-selected forest-plan components against package evidence."""

    if package_top_k < 1:
        raise ValueError("package_top_k must be at least 1")
    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")

    review_dir = Path(review_dir)
    component_inventory_path = Path(component_inventory_path)
    findings_path = review_dir / "forest_plan_component_findings.json"
    markdown_path = review_dir / "forest_plan_component_findings.md"
    queue_path = review_dir / "forest_plan_reviewer_resolution_queue.json"
    inventory_coverage_path = review_dir / "forest_plan_component_inventory_coverage.json"
    standard_coverage_path = review_dir / "forest_plan_applicable_standard_coverage.json"
    components = load_forest_plan_component_inventory(
        component_inventory_path,
        forest_unit_id=forest_unit_id,
    )
    findings = [
        _component_finding(
            review_id=review_id,
            component=component,
            context=context,
            package_chunks=package_chunks,
            source_set_id=source_set_id,
            index_path=index_path,
            package_top_k=package_top_k,
            source_top_k=source_top_k,
        )
        for component in components
    ]
    queue = _reviewer_resolution_queue(
        review_id=review_id,
        source_set_id=source_set_id,
        findings=findings,
    )
    inventory_coverage = _component_inventory_coverage(
        review_id=review_id,
        source_set_id=source_set_id,
        component_inventory_path=component_inventory_path,
        components=components,
    )
    standard_coverage = _applicable_standard_coverage(
        review_id=review_id,
        source_set_id=source_set_id,
        components=components,
        findings=findings,
    )
    validation = _validation_report(
        source_set_id=source_set_id,
        components=components,
        findings=findings,
        queue=queue,
        inventory_coverage=inventory_coverage,
        standard_coverage=standard_coverage,
    )
    summary = _summary(
        review_id=review_id,
        source_set_id=source_set_id,
        component_inventory_path=component_inventory_path,
        findings_path=findings_path,
        markdown_path=markdown_path,
        queue_path=queue_path,
        inventory_coverage_path=inventory_coverage_path,
        standard_coverage_path=standard_coverage_path,
        components=components,
        findings=findings,
        queue=queue,
        validation=validation,
        inventory_coverage=inventory_coverage,
        standard_coverage=standard_coverage,
    )
    report = {
        "schema_version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "summary": summary,
        "validation": validation,
        "component_inventory_coverage": inventory_coverage,
        "applicable_standard_coverage": standard_coverage,
        "components": components,
        "findings": findings,
    }

    review_dir.mkdir(parents=True, exist_ok=True)
    _write_json(findings_path, report)
    _write_json(queue_path, queue)
    _write_json(inventory_coverage_path, inventory_coverage)
    _write_json(standard_coverage_path, standard_coverage)
    markdown_path.write_text(_markdown_report(report, queue), encoding="utf-8")
    return ForestPlanComponentEvaluationResult(
        findings_path=findings_path,
        markdown_path=markdown_path,
        reviewer_resolution_queue_path=queue_path,
        component_inventory_coverage_path=inventory_coverage_path,
        applicable_standard_coverage_path=standard_coverage_path,
        summary=summary,
    )


def load_forest_plan_component_inventory(
    path: Path = DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH,
    *,
    forest_unit_id: str | None = None,
) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Forest-plan component inventory must be a JSON object.")
    schema_version = _require_string(payload, "schema_version", "component inventory")
    if schema_version != FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan component inventory schema_version: "
            f"{schema_version!r}; expected {FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION!r}"
        )
    _require_safe_string(payload, "inventory_id", "component inventory")
    components = _require_list(payload, "components", "component inventory")
    parsed = []
    for index, raw_component in enumerate(components):
        component = _parse_component(raw_component, f"components[{index}]")
        if forest_unit_id is not None and component["forest_unit_id"] != forest_unit_id:
            continue
        parsed.append(component)
    if not parsed:
        raise ValueError("Forest-plan component inventory contains no selected components.")
    _reject_duplicate(
        [component["component_id"] for component in parsed],
        "component_id",
        "component inventory",
    )
    return parsed


def _parse_component(raw_component: object, context: str) -> dict:
    component = _require_object(raw_component, context)
    component_id = _require_safe_string(component, "component_id", context)
    component_type = _require_string(component, "component_type", context)
    if component_type not in VALID_COMPONENT_TYPES:
        raise ValueError(f"{context}.component_type is unsupported: {component_type!r}.")
    page = component.get("page")
    if page is not None and (not isinstance(page, int) or page < 1):
        raise ValueError(f"{context}.page must be a positive integer or null.")
    parsed = {
        "component_id": component_id,
        "forest_unit_id": _require_safe_string(component, "forest_unit_id", context),
        "plan_version": _require_string(component, "plan_version", context),
        "source_set_id": _require_safe_string(component, "source_set_id", context),
        "source_record_id": _require_safe_string(component, "source_record_id", context),
        "component_type": component_type,
        "section_id": _require_safe_string(component, "section_id", context),
        "section_heading": _require_string(component, "section_heading", context),
        "page": page,
        "citation_label": _require_string(component, "citation_label", context),
        "component_text": _require_string(component, "component_text", context),
        "geographic_area_ids": _require_string_list(
            component,
            "geographic_area_ids",
            context,
            required=False,
        ),
        "management_area_ids": _require_string_list(
            component,
            "management_area_ids",
            context,
            required=False,
        ),
        "overlay_ids": _require_string_list(component, "overlay_ids", context, required=False),
        "resource_topics": _require_string_list(
            component,
            "resource_topics",
            context,
            required=False,
        ),
        "activity_tags": _require_string_list(
            component,
            "activity_tags",
            context,
            required=False,
        ),
        "source_chunk_ids": _require_string_list(component, "source_chunk_ids", context),
        "artifact_sha256": _require_hex_string(component, "artifact_sha256", context),
        "content_sha256": _require_hex_string(component, "content_sha256", context),
        "provenance": _require_provenance(component.get("provenance"), f"{context}.provenance"),
        "package_evidence_terms": _require_string_list(
            component,
            "package_evidence_terms",
            context,
            required=False,
        ),
    }
    if not (
        parsed["geographic_area_ids"]
        or parsed["management_area_ids"]
        or parsed["overlay_ids"]
        or parsed["resource_topics"]
        or parsed["activity_tags"]
    ):
        raise ValueError(
            f"{context} must include at least one context id, resource_topic, or activity_tag."
        )
    if not parsed["source_chunk_ids"]:
        raise ValueError(f"{context}.source_chunk_ids cannot be empty.")
    return parsed


def _component_finding(
    *,
    review_id: str,
    component: dict,
    context: dict,
    package_chunks: list[dict],
    source_set_id: str | None,
    index_path: Path | None,
    package_top_k: int,
    source_top_k: int,
) -> dict:
    source_set_matches = bool(source_set_id and component["source_set_id"] == source_set_id)
    context_match = _context_matches_component(context, component)
    package_search = _component_package_search(
        component=component,
        package_chunks=package_chunks,
        limit=package_top_k,
    )
    package_determination = _component_package_determination(
        component=component,
        package_chunks=package_chunks,
    )
    if package_determination and package_determination.get("component_applies") == "no":
        package_evidence = [package_determination]
    else:
        package_evidence = _merge_package_evidence(
            [package_determination] if package_determination else [],
            package_search["results"],
            limit=package_top_k,
        )
    plan_source_evidence = []
    should_bind_plan_source = (
        context_match
        or component["component_type"] == "standard"
        or package_determination is not None
    )
    if source_set_matches and should_bind_plan_source and index_path is not None:
        plan_source_evidence = _component_plan_source_evidence(
            component=component,
            index_path=index_path,
            limit=source_top_k,
        )

    if not source_set_matches:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component inventory source set does not match the review source set."
    elif package_determination and package_determination.get("component_applies") == "no":
        applicability_status = "not_applicable"
        finding_status = "not_applicable"
        rationale = "The EA package explicitly marks this plan component not applicable."
    elif context.get("needs_reviewer_resolution"):
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The forest-plan context resolver requires reviewer resolution before component findings can be trusted."
    elif not context_match:
        applicability_status = "not_applicable"
        finding_status = "not_applicable"
        rationale = "The resolved package context does not match this component's geography, management area, or overlay."
    elif not plan_source_evidence:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component could not be verified against current source-library plan evidence."
    elif package_evidence:
        applicability_status = "applicable"
        finding_status = "supported"
        if package_determination:
            rationale = "The component is applicable and the EA package contains an explicit plan-consistency determination."
        else:
            rationale = "The component is applicable and the EA package contains matching evidence."
    else:
        applicability_status = "applicable"
        finding_status = "gap"
        rationale = "The component is applicable and source-library plan evidence exists, but matching EA package evidence was not found."

    compliance_status = _compliance_status(
        component=component,
        finding_status=finding_status,
    )
    reviewer_items = _reviewer_resolution_items_for_finding(
        review_id=review_id,
        component=component,
        finding_status=finding_status,
        applicability_status=applicability_status,
        rationale=rationale,
        source_set_id=source_set_id,
        source_set_matches=source_set_matches,
        plan_source_evidence=plan_source_evidence,
        package_evidence=package_evidence,
    )
    return {
        "finding_id": f"{component['component_id']}-finding",
        "review_id": review_id,
        "component_id": component["component_id"],
        "component_type": component["component_type"],
        "applicability_status": applicability_status,
        "finding_status": finding_status,
        "compliance_status": compliance_status,
        "applicability_basis": {
            "source_set_id": source_set_id,
            "component_source_set_id": component["source_set_id"],
            "source_set_matches": source_set_matches,
            "matched_context": _matched_context(context, component),
            "component_context": {
                "geographic_area_ids": component["geographic_area_ids"],
                "management_area_ids": component["management_area_ids"],
                "overlay_ids": component["overlay_ids"],
                "resource_topics": component["resource_topics"],
                "activity_tags": component["activity_tags"],
            },
            "package_query": package_search["query"],
            "package_evidence_terms": package_search["required_terms"],
            "component_key": _component_reference_key(component),
            "package_component_determination": (
                _package_determination_basis(package_determination)
                if package_determination
                else None
            ),
        },
        "plan_source_evidence": plan_source_evidence,
        "package_evidence": package_evidence,
        "rationale": rationale,
        "reviewer_resolution_items": reviewer_items,
        "provenance": _finding_provenance(
            review_id=review_id,
            component=component,
            source_set_id=source_set_id,
            finding_status=finding_status,
        ),
    }


def _compliance_status(*, component: dict, finding_status: str) -> str:
    if component["component_type"] != "standard":
        return "not_evaluated_for_compliance"
    if finding_status == "supported":
        return "complies"
    if finding_status == "not_applicable":
        return "not_applicable"
    if finding_status in {"gap", "partial"}:
        return "insufficient_evidence"
    return "needs_reviewer_resolution"


def _component_package_search(
    *,
    component: dict,
    package_chunks: list[dict],
    limit: int,
) -> dict:
    terms = _component_package_search_terms(component)
    section_families = _component_section_families(component)
    query = " ".join([component["section_heading"], component["component_text"], *terms])
    raw = _search_package_chunks(
        package_chunks,
        query=query,
        required_terms=list(terms),
        limit=max(limit * 10, 10),
    )
    results = []
    rejected_count = 0
    chunks_by_id = {chunk.get("chunk_id"): chunk for chunk in package_chunks}
    for result in raw["results"]:
        evidence = _annotate_component_package_evidence(
            evidence=result,
            chunk=chunks_by_id.get(result.get("chunk_id"), {}),
            component=component,
            required_terms=terms,
            core_terms=_component_core_evidence_terms(component),
            section_families=section_families,
        )
        if _package_evidence_matches_component(
            component=component,
            evidence=evidence,
            section_families=section_families,
        ):
            results.append(evidence)
        else:
            rejected_count += 1
        if len(results) >= limit:
            break
    return {
        "query": query,
        "required_terms": terms,
        "section_families": section_families,
        "raw_hit_count": raw["hit_count"],
        "rejected_count": rejected_count,
        "hit_count": len(results),
        "results": results,
    }


def _component_package_search_terms(component: dict) -> list[str]:
    candidates = [
        *component.get("package_evidence_terms", []),
        *component.get("resource_topics", []),
        *component.get("activity_tags", []),
        *_component_keyword_terms(
            " ".join(
                [
                    str(component.get("section_heading") or ""),
                    str(component.get("component_text") or ""),
                ]
            )
        ),
    ]
    component_key = _component_reference_key(component)
    if component_key:
        candidates.append(component_key)
        candidates.extend(part for part in component_key.split("-") if len(part) > 2)
    return _dedupe_terms(candidates)


def _component_core_evidence_terms(component: dict) -> list[str]:
    return [
        term
        for term in _dedupe_terms(
            [
                *component.get("package_evidence_terms", []),
                *component.get("resource_topics", []),
                *component.get("activity_tags", []),
            ]
        )
        if not _is_context_only_term(term)
    ]


def _is_context_only_term(term: str) -> bool:
    normalized = _normalized_component_text(term)
    if not normalized:
        return True
    tokens = TOKEN_RE.findall(normalized)
    if not tokens:
        return True
    context_tokens = {
        "area",
        "backcountry",
        "crazy",
        "geographic",
        "management",
        "mountain",
        "mountains",
        "plan",
    }
    return all(token in context_tokens or token in GENERIC_COMPONENT_TERMS for token in tokens)


def _component_keyword_terms(text: str) -> list[str]:
    terms = []
    for token in TOKEN_RE.findall(text.lower()):
        if len(token) < 4 or token in GENERIC_COMPONENT_TERMS or token in terms:
            continue
        terms.append(token)
        if len(terms) >= 12:
            break
    return terms


def _component_section_families(component: dict) -> list[str]:
    text = " ".join(
        [
            str(component.get("section_heading") or ""),
            str(component.get("component_text") or ""),
            " ".join(component.get("package_evidence_terms") or []),
            " ".join(component.get("resource_topics") or []),
            " ".join(component.get("activity_tags") or []),
        ]
    )
    families = _section_families_from_text(text)
    if not families:
        families.append("general_ea")
    return _dedupe_preserve_order(families)


def _annotate_component_package_evidence(
    *,
    evidence: dict,
    chunk: dict,
    component: dict,
    required_terms: list[str],
    core_terms: list[str],
    section_families: list[str],
) -> dict:
    annotated = dict(evidence)
    evidence_text = " ".join(
        [
            _package_evidence_text(evidence),
            str(chunk.get("text") or "").lower(),
        ]
    )
    matched_terms = [
        term for term in required_terms if _term_matches_text(evidence_text, term)
    ]
    matched_core_terms = [
        term for term in core_terms if _term_matches_text(evidence_text, term)
    ]
    evidence_family = _package_evidence_section_family(evidence)
    matched_substantive_core_terms = _substantive_core_terms(matched_core_terms)
    annotated["matched_component_terms"] = matched_terms
    annotated["matched_core_terms"] = matched_core_terms
    annotated["matched_substantive_core_terms"] = matched_substantive_core_terms
    section_matched = _package_section_family_matches_component(
        component=component,
        evidence=annotated,
        evidence_family=evidence_family,
        section_families=section_families,
    )
    explicit_plan_consistency_row = _package_evidence_has_affirmative_plan_consistency_row(
        component=component,
        evidence=annotated,
        context_text=evidence_text,
        family=evidence_family,
    )
    annotated["review_section"] = _package_evidence_review_section(evidence)
    annotated["section_binding"] = {
        "component_section_families": section_families,
        "package_section_family": evidence_family,
        "matched": section_matched or explicit_plan_consistency_row,
        "matched_substantive_core_terms": matched_substantive_core_terms,
        "binding_policy": (
            "explicit_plan_consistency_component_row"
            if explicit_plan_consistency_row
            else _package_section_binding_policy(component)
        ),
        "explicit_plan_consistency_component_row": explicit_plan_consistency_row,
    }
    if explicit_plan_consistency_row:
        annotated["plan_consistency_component_row"] = True
    if _package_evidence_supports_restrictive_recreation_component(
        component=component,
        evidence=evidence,
        section_families=section_families,
        context_text=evidence_text,
        family=evidence_family,
    ):
        annotated["restrictive_access_support"] = True
    return annotated


def _package_evidence_matches_component(
    *,
    component: dict,
    evidence: dict,
    section_families: list[str],
) -> bool:
    text = _package_evidence_text(evidence)
    if _is_negative_package_evidence(text):
        return False
    section_binding = (
        evidence.get("section_binding") if isinstance(evidence.get("section_binding"), dict) else {}
    )
    family = str(section_binding.get("package_section_family") or "").strip()
    if not family:
        family = _package_evidence_section_family(evidence)
    if family == "plan_consistency":
        return _package_evidence_has_affirmative_plan_consistency_row(
            component=component,
            evidence=evidence,
            context_text=text,
            family=family,
        )
    if (
        evidence.get("restrictive_access_support")
        or _package_evidence_supports_restrictive_recreation_component(
            component=component,
            evidence=evidence,
            section_families=section_families,
        )
    ):
        return True
    if not evidence.get("matched_core_terms"):
        return False
    if _is_nonstandard_component(component) and not _nonstandard_package_evidence_has_substantive_match(
        evidence
    ):
        return False
    if family in section_families:
        return True
    if family == "general_ea":
        if _is_nonstandard_component(component) and section_families != ["general_ea"]:
            return False
        return len(evidence.get("matched_component_terms") or []) >= 2
    return False


def _package_section_family_matches_component(
    *,
    component: dict,
    evidence: dict,
    evidence_family: str,
    section_families: list[str],
) -> bool:
    if evidence_family in section_families:
        if _is_nonstandard_component(component):
            return _nonstandard_package_evidence_has_substantive_match(evidence)
        return True
    if evidence_family == "plan_consistency":
        return False
    if evidence_family != "general_ea":
        return False
    if not _is_nonstandard_component(component):
        return True
    return section_families == ["general_ea"] and _nonstandard_package_evidence_has_substantive_match(
        evidence
    )


def _package_section_binding_policy(component: dict) -> str:
    if _is_nonstandard_component(component):
        return "strict_nonstandard_section_family"
    return "standard_section_family_or_general_ea"


def _package_evidence_has_affirmative_plan_consistency_row(
    *,
    component: dict,
    evidence: dict,
    context_text: str | None = None,
    family: str | None = None,
) -> bool:
    family = family or _package_evidence_section_family(evidence, context_text=context_text)
    if family != "plan_consistency":
        return False
    component_key = _component_reference_key(component)
    if not component_key:
        return False
    text = (context_text or _package_evidence_text(evidence)).lower()
    return bool(
        component_key.lower() in text
        and re.search(r"(?:\|\s*yes\s*\||(?:^|\n)\s*yes\s*(?:\n|-))", text)
    )


def _is_nonstandard_component(component: dict) -> bool:
    return component.get("component_type") != "standard"


def _nonstandard_package_evidence_has_substantive_match(evidence: dict) -> bool:
    terms = evidence.get("matched_substantive_core_terms") or []
    if not terms:
        return False
    if any(len(TOKEN_RE.findall(_normalized_component_text(term))) >= 2 for term in terms):
        return True
    return len(terms) >= 2


def _package_evidence_supports_restrictive_recreation_component(
    *,
    component: dict,
    evidence: dict,
    section_families: list[str],
    context_text: str | None = None,
    family: str | None = None,
) -> bool:
    if component.get("component_type") != "standard":
        return False
    if "recreation_access" not in section_families:
        return False
    family = family or _package_evidence_section_family(evidence, context_text=context_text)
    if family not in {"recreation_access", "general_ea"}:
        return False

    component_text = _normalized_component_text(str(component.get("component_text") or ""))
    if not re.search(
        r"\b(?:shall|should|must)\s+not\b|"
        r"\bnot\s+be\s+(?:allowed|authorized|constructed|designated|permitted)\b",
        component_text,
    ):
        return False
    if "motorized" not in set(TOKEN_RE.findall(component_text)):
        return False
    if not re.search(r"\b(?:trail|trails|road|roads|route|routes|transport|travel)\b", component_text):
        return False

    evidence_text = (context_text or _package_evidence_text(evidence)).lower()
    if _mentions_trail_access(component_text) and not re.search(
        r"\b(?:trail|trails|route|routes)\b",
        evidence_text,
    ):
        return False
    if _mentions_road_access(component_text) and not re.search(
        r"\b(?:road|roads|route|routes)\b",
        evidence_text,
    ):
        return False
    if not (_mentions_trail_access(component_text) or _mentions_road_access(component_text)):
        if not re.search(r"\b(?:route|routes|transport|travel)\b", evidence_text):
            return False
    if not re.search(
        r"\b(?:new|proposed|relocat(?:e|ed|ion)|construct(?:ed|ion)|"
        r"action\s+alternative|alternative\s+1|will|would)\b",
        evidence_text,
    ):
        return False
    return _text_supports_nonmotorized_access(evidence_text)


def _mentions_trail_access(text: str) -> bool:
    return bool(re.search(r"\btrails?\b", text))


def _mentions_road_access(text: str) -> bool:
    return bool(re.search(r"\broads?\b", text))


def _text_supports_nonmotorized_access(text: str) -> bool:
    return bool(
        re.search(r"\bnon[-\s]?motorized\b", text)
        or re.search(
            r"\b(?:not|without|free\s+of|prohibit(?:ed|s)?|"
            r"does\s+not\s+include|will\s+not\s+include)\b.{0,100}\bmotorized\b",
            text,
        )
        or re.search(r"\bno\s+(?:new\s+)?motorized\b", text)
        or re.search(
            r"\bmotorized\b.{0,100}\b(?:prohibit(?:ed|s)?|not\s+allowed|"
            r"not\s+authorized|not\s+included)\b",
            text,
        )
    )


def _section_families_from_text(text: str) -> list[str]:
    normalized_text = str(text or "").lower()
    tokens = set(TOKEN_RE.findall(normalized_text))
    families = []
    for family, keywords in SECTION_FAMILY_KEYWORDS.items():
        if any(_section_keyword_matches(normalized_text, tokens, keyword) for keyword in keywords):
            families.append(family)
    return _dedupe_preserve_order(families)


def _section_keyword_matches(text: str, tokens: set[str], keyword: str) -> bool:
    normalized_keyword = keyword.lower()
    if " " in normalized_keyword or "-" in normalized_keyword:
        return normalized_keyword in text
    return normalized_keyword in tokens


def _substantive_core_terms(terms: list[str]) -> list[str]:
    return [term for term in terms if _is_substantive_core_term(term)]


def _is_substantive_core_term(term: str) -> bool:
    tokens = TOKEN_RE.findall(_normalized_component_text(term))
    if not tokens:
        return False
    broad_tokens = {
        "access",
        "area",
        "conditions",
        "component",
        "components",
        "general",
        "habitat",
        "hydrology",
        "management",
        "plan",
        "project",
        "recreation",
        "resource",
        "resources",
        "scenery",
        "scenic",
        "section",
        "species",
        "sustainability",
        "sustainable",
        "trail",
        "trails",
        "water",
        "wildlife",
    }
    return any(token not in broad_tokens and token not in GENERIC_COMPONENT_TERMS for token in tokens)


def _package_evidence_section_family(evidence: dict, context_text: str | None = None) -> str:
    title = str(evidence.get("title") or "").lower()
    if "plan consistency table" in title:
        return "plan_consistency"
    provenance = evidence.get("provenance") if isinstance(evidence.get("provenance"), dict) else {}
    section_text = " ".join(
        str(part or "")
        for part in (
            evidence.get("title"),
            provenance.get("section"),
            provenance.get("heading"),
        )
    )
    section_families = _section_families_from_text(section_text)
    if section_families:
        return section_families[0]
    text_families = _section_families_from_text(context_text or _package_evidence_text(evidence))
    if text_families:
        return text_families[0]
    if any(
        term in title
        for term in (
            "environmental assessment",
            "decision notice",
            "fone",
            "fonsi",
            "pre-ea",
            "preea",
            "faq",
        )
    ):
        return "general_ea"
    return "general_ea"


def _package_evidence_review_section(evidence: dict) -> str:
    provenance = evidence.get("provenance") if isinstance(evidence.get("provenance"), dict) else {}
    for field in ("section", "heading"):
        value = str(provenance.get(field) or "").strip()
        if value:
            return value
    return str(evidence.get("title") or "EA package")


def _package_evidence_text(evidence: dict) -> str:
    span = evidence.get("evidence_span") if isinstance(evidence.get("evidence_span"), dict) else {}
    provenance = evidence.get("provenance") if isinstance(evidence.get("provenance"), dict) else {}
    return " ".join(
        str(part or "")
        for part in (
            evidence.get("title"),
            span.get("text"),
            provenance.get("section"),
            provenance.get("heading"),
        )
    ).lower()


def _is_negative_package_evidence(text: str) -> bool:
    if "plan consistency table" not in text:
        return False
    return bool(
        re.search(r"\|\s*no\s*\|", text)
        or re.search(r"(?:^|\n)\s*no\s*(?:\n|-)", text)
        or re.search(r"\bnot\s+part\s+of\s+(?:the\s+)?project\s+area\b", text)
        or re.search(r"\boutside(?:\s+of)?\s+(?:the\s+)?project\s+area\b", text)
        or re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b(?:in\s+the\s+project\s+area|"
            r"affected\s+by\s+(?:the|this)\s+project)\b",
            text,
        )
    )


def _term_matches_text(text: str, term: str) -> bool:
    normalized_term = _normalized_component_text(term)
    if not normalized_term:
        return False
    if " " in normalized_term:
        return normalized_term in text
    return normalized_term in set(TOKEN_RE.findall(text))


def _component_plan_source_evidence(
    *,
    component: dict,
    index_path: Path,
    limit: int,
) -> list[dict]:
    del index_path
    return _component_inventory_plan_source_evidence(component)[:limit]


def _component_inventory_plan_source_evidence(component: dict) -> list[dict]:
    source_chunk_ids = component.get("source_chunk_ids") or []
    chunk_id = str(source_chunk_ids[0]) if source_chunk_ids else component["component_id"]
    provenance = component.get("provenance") or {}
    activity = provenance.get("activity") if isinstance(provenance, dict) else {}
    entity = provenance.get("entity") if isinstance(provenance, dict) else {}
    return [
        {
            "rank": 1,
            "score": 1.0,
            "chunk_id": chunk_id,
            "source_record_id": component["source_record_id"],
            "title": component.get("section_heading") or "Forest Plan Component",
            "citation_label": component.get("citation_label"),
            "document_role": "forest_plan",
            "authority_level": "forest",
            "review_topics": [
                "Extract plan components by resource and geography",
                "check suitability/designated areas",
            ],
            "evidence_span": {
                "text": component["component_text"],
                "chunk_char_start": None,
                "chunk_char_end": None,
                "source_char_start": None,
                "source_char_end": None,
            },
            "provenance": {
                "artifact_sha256": component.get("artifact_sha256"),
                "content_sha256": component.get("content_sha256"),
                "source_chunk_ids": list(source_chunk_ids),
                "source_record_id": component["source_record_id"],
                "source_text_path": (
                    activity.get("source") if isinstance(activity, dict) else None
                ),
                "component_inventory_entity": entity if isinstance(entity, dict) else None,
                "parser_name": "forest_plan_component_inventory",
                "parser_version": FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
            },
        }
    ]


def _component_package_determination(
    *,
    component: dict,
    package_chunks: list[dict],
) -> dict | None:
    component_key = _component_reference_key(component)
    if not component_key:
        return None
    pattern = _component_key_pattern(component_key)
    candidates = []
    for index, chunk in enumerate(package_chunks):
        window_chunk = _plan_consistency_chunk_window(package_chunks, index)
        text = str(window_chunk.get("text") or "")
        for match in pattern.finditer(text):
            row = _plan_consistency_row(
                chunk=window_chunk,
                text=text,
                match_start=match.start(),
                match_end=match.end(),
                component_key=component_key,
            )
            if row is not None:
                candidates.append(row)
            row = _plan_consistency_plain_text_row(
                chunk=window_chunk,
                text=text,
                match_start=match.start(),
                match_end=match.end(),
                component=component,
                component_key=component_key,
            )
            if row is not None:
                candidates.append(row)
        if not candidates:
            row = _plan_consistency_text_row(
                chunk=window_chunk,
                text=text,
                component=component,
                component_key=component_key,
            )
            if row is not None:
                candidates.append(row)
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            str(item.get("source_record_id") or ""),
            int(item.get("provenance", {}).get("char_start") or 0),
        )
    )
    result = dict(candidates[0])
    result["rank"] = 1
    return result


def _plan_consistency_chunk_window(
    package_chunks: list[dict],
    index: int,
    *,
    lookahead: int = 4,
) -> dict:
    chunk = dict(package_chunks[index])
    title = str(chunk.get("title") or "")
    if "plan consistency table" not in title.lower():
        return chunk
    parts = [str(chunk.get("text") or "")]
    last_chunk = chunk
    for next_chunk in package_chunks[index + 1 : index + 1 + lookahead]:
        if not _same_package_document(chunk, next_chunk):
            break
        parts.append(str(next_chunk.get("text") or ""))
        last_chunk = next_chunk
    if len(parts) == 1:
        return chunk
    window = dict(chunk)
    window["text"] = "\n".join(parts)
    window["char_end"] = last_chunk.get("char_end", chunk.get("char_end"))
    window["chunk_window_ids"] = [
        str(item.get("chunk_id") or "")
        for item in package_chunks[index : index + len(parts)]
        if str(item.get("chunk_id") or "").strip()
    ]
    return window


def _same_package_document(left: dict, right: dict) -> bool:
    return all(
        str(left.get(field) or "") == str(right.get(field) or "")
        for field in ("source_record_id", "artifact_sha256", "title")
    )


def _component_reference_key(component: dict) -> str | None:
    match = COMPONENT_CODE_NUMBER_RE.search(str(component.get("component_text") or ""))
    if not match:
        return None
    return f"{match.group('code')}-{match.group('number')}"


def _component_key_pattern(component_key: str) -> re.Pattern[str]:
    prefix, separator, number = component_key.rpartition("-")
    if not separator or not prefix or not number:
        return re.compile(rf"(?<![A-Za-z0-9]){re.escape(component_key)}(?![A-Za-z0-9])")
    prefix_pattern = re.escape(prefix).replace(r"\-", r"\s*-\s*")
    number_pattern = re.escape(number)
    return re.compile(
        rf"(?<![A-Za-z0-9]){prefix_pattern}\s*-?\s*{number_pattern}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


def _plan_consistency_row(
    *,
    chunk: dict,
    text: str,
    match_start: int,
    match_end: int,
    component_key: str,
) -> dict | None:
    row_start = text.rfind("|", 0, match_start)
    if row_start < 0:
        row_start = max(0, match_start - 120)
    window = text[row_start : min(len(text), match_end + 5000)]
    cells = [cell.strip() for cell in window.split("|")]
    component_key_fingerprint = _component_key_fingerprint(component_key)
    key_index = next(
        (
            index
            for index, cell in enumerate(cells)
            if _cell_matches_component_key(cell, component_key_fingerprint)
        ),
        None,
    )
    if key_index is None:
        return None
    applies_index = next(
        (
            index
            for index in range(key_index + 1, min(len(cells), key_index + 6))
            if _yes_no_cell(cells[index]) in PLAN_CONSISTENCY_YES_NO
        ),
        None,
    )
    if applies_index is None or len(cells) <= applies_index + 1:
        return None
    applies = _yes_no_cell(cells[applies_index])
    if applies not in PLAN_CONSISTENCY_YES_NO:
        return None
    explanation = _compact(cells[applies_index + 1], limit=1200)
    component_text = _compact(
        " ".join(_component_text_cells(cells[key_index], cells[key_index + 1 : applies_index])),
        limit=1200,
    )
    row_cells = cells[key_index : applies_index + 2]
    row_text = " | ".join(cell for cell in row_cells if cell)
    row_offset = window.find(cells[key_index])
    if row_offset < 0:
        row_offset = match_start - row_start
    span_start = row_start + row_offset
    span_end = min(len(text), span_start + len(row_text))
    return _package_determination_result(
        chunk=chunk,
        component_key=component_key,
        component_applies=applies,
        component_text=component_text,
        explanation=explanation,
        span_start=span_start,
        span_end=span_end,
        row_text=row_text,
    )


def _plan_consistency_text_row(
    *,
    chunk: dict,
    text: str,
    component: dict,
    component_key: str,
) -> dict | None:
    if "plan consistency table" not in str(chunk.get("title") or "").lower():
        return None
    component_text = _component_body_text(str(component.get("component_text") or ""))
    if not component_text:
        return None
    cells = [cell.strip() for cell in text.split("|")]
    component_key_fingerprint = _component_key_fingerprint(component_key)
    component_key_prefix_fingerprint = _component_key_fingerprint(
        component_key.rpartition("-")[0]
    )
    for index in range(0, max(0, len(cells) - 3)):
        key_cell = cells[index]
        candidate_component_text = _compact(cells[index + 1], limit=1200)
        applies = _yes_no_cell(cells[index + 2])
        key_fingerprint = _component_key_fingerprint(key_cell)
        key_matches = (
            not key_cell
            or key_fingerprint == component_key_fingerprint
            or (
                bool(component_key_prefix_fingerprint)
                and key_fingerprint == component_key_prefix_fingerprint
            )
        )
        if not key_matches or applies not in PLAN_CONSISTENCY_YES_NO:
            continue
        if not _component_text_matches(candidate_component_text, component_text):
            continue
        explanation = _compact(cells[index + 3], limit=1200)
        row_cells = cells[index : index + 4]
        row_text = " | ".join(cell for cell in row_cells if cell)
        span_start = text.find(cells[index + 1])
        if span_start < 0:
            span_start = 0
        span_end = min(len(text), span_start + len(row_text))
        return _package_determination_result(
            chunk=chunk,
            component_key=component_key,
            component_applies=applies,
            component_text=candidate_component_text,
            explanation=explanation,
            span_start=span_start,
            span_end=span_end,
            row_text=row_text,
        )
    return None


def _plan_consistency_plain_text_row(
    *,
    chunk: dict,
    text: str,
    match_start: int,
    match_end: int,
    component: dict,
    component_key: str,
) -> dict | None:
    if "plan consistency table" not in str(chunk.get("title") or "").lower():
        return None
    window = text[match_start : min(len(text), match_end + 3000)]
    if "|" in window[:500]:
        return None
    applies_match = re.search(
        r"\b(?P<applies>yes|no)\b\s*(?:[-\u2013\u2014]|\b(?:this|the|no)\b)",
        window,
        re.IGNORECASE,
    )
    if not applies_match:
        return None
    applies = _yes_no_cell(applies_match.group("applies"))
    if applies not in PLAN_CONSISTENCY_YES_NO:
        return None
    component_text = _compact(window[match_end - match_start : applies_match.start()], limit=1200)
    target_text = _component_body_text(str(component.get("component_text") or ""))
    if component_text and target_text and not _component_text_matches(component_text, target_text):
        return None
    tail = window[applies_match.end() :]
    next_row = re.search(
        r"\s(?:[A-Z]{2,4}-(?:DC|GO|OBJ|STD|GDL|SUIT)-[A-Z0-9]+-?\s*[0-9]{2}|##\s+)",
        tail,
    )
    explanation_end = applies_match.end() + (next_row.start() if next_row else len(tail))
    explanation = _compact(window[applies_match.end() : explanation_end], limit=1200)
    row_text = _compact(window[:explanation_end], limit=2400)
    return _package_determination_result(
        chunk=chunk,
        component_key=component_key,
        component_applies=applies,
        component_text=component_text,
        explanation=explanation,
        span_start=match_start,
        span_end=min(len(text), match_start + len(row_text)),
        row_text=row_text,
    )


def _component_body_text(component_text: str) -> str:
    return _normalized_component_text(LEADING_COMPONENT_LABEL_RE.sub("", component_text))


def _component_text_matches(candidate: str, target: str) -> bool:
    candidate_text = _normalized_component_text(candidate)
    if not candidate_text or not target:
        return False
    candidate_tokens = candidate_text.split()
    target_tokens = target.split()
    if len(candidate_tokens) >= 6 and candidate_tokens == target_tokens[: len(candidate_tokens)]:
        return True
    if len(candidate_tokens) >= 6 and len(target_tokens) >= len(candidate_tokens):
        candidate_stem = candidate_tokens[-1].rstrip("-")
        target_token = target_tokens[len(candidate_tokens) - 1]
        if (
            candidate_tokens[:-1] == target_tokens[: len(candidate_tokens) - 1]
            and candidate_stem
            and target_token.startswith(candidate_stem)
        ):
            return True
    if len(target_tokens) >= 6 and target_tokens == candidate_tokens[: len(target_tokens)]:
        return True
    candidate_prefix = " ".join(candidate_tokens[:18])
    target_prefix = " ".join(target_tokens[:18])
    return bool(candidate_prefix and target_prefix and candidate_prefix == target_prefix)


def _component_key_fingerprint(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value).upper())


def _cell_matches_component_key(cell: str, component_key_fingerprint: str) -> bool:
    cell_fingerprint = _component_key_fingerprint(cell)
    return bool(
        cell_fingerprint
        and (
            cell_fingerprint == component_key_fingerprint
            or cell_fingerprint.startswith(component_key_fingerprint)
        )
    )


def _component_text_cells(key_cell: str, cells: list[str]) -> list[str]:
    values = []
    key_match = re.match(
        r"\s*[A-Za-z]{2,4}\s*-\s*(?:DC|GO|OBJ|STD|GDL|SUIT)\s*-\s*"
        r"[A-Za-z0-9]+\s*-?\s*[0-9]{2}\s*(?P<tail>.*)",
        key_cell,
        flags=re.IGNORECASE,
    )
    if key_match and key_match.group("tail").strip():
        values.append(key_match.group("tail").strip())
    values.extend(cell for cell in cells if cell.strip())
    return values


def _yes_no_cell(value: str) -> str | None:
    normalized = re.sub(r"[^A-Za-z]+", " ", value).strip().lower()
    if normalized in PLAN_CONSISTENCY_YES_NO:
        return normalized
    return None


def _package_determination_result(
    *,
    chunk: dict,
    component_key: str,
    component_applies: str,
    component_text: str,
    explanation: str,
    span_start: int,
    span_end: int,
    row_text: str,
) -> dict:
    source_chunk_start = int(chunk.get("char_start") or 0)
    return {
        "rank": 1,
        "score": 1.0,
        "chunk_id": chunk["chunk_id"],
        "source_record_id": chunk["source_record_id"],
        "title": chunk["title"],
        "citation_label": chunk["citation_label"],
        "matched_terms": [component_key, component_applies],
        "component_key": component_key,
        "component_applies": component_applies,
        "determination_source": "ea_plan_consistency_table",
        "determination_explanation": explanation,
        "determination_component_text": component_text,
        "review_section": _package_review_section(
            chunk=chunk,
            explanation=explanation,
        ),
        "evidence_span": {
            "text": row_text,
            "chunk_char_start": span_start,
            "chunk_char_end": span_end,
            "source_char_start": source_chunk_start + span_start,
            "source_char_end": source_chunk_start + span_end,
        },
        "provenance": {
            "artifact_sha256": chunk["artifact_sha256"],
            "artifact_path": chunk["artifact_path"],
            "parser_name": chunk["parser_name"],
            "parser_version": chunk["parser_version"],
            "extracted_at": chunk["extracted_at"],
            "source_text_path": chunk["source_text_path"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
            "chunk_window_ids": chunk.get("chunk_window_ids", [chunk.get("chunk_id")]),
            "page": chunk["page"],
            "section": chunk["section"],
            "heading": chunk["heading"],
            "content_sha256": chunk["content_sha256"],
        },
    }


def _package_review_section(*, chunk: dict, explanation: str) -> str:
    explicit_section = _explicit_ea_section(explanation)
    if explicit_section:
        return explicit_section
    for field in ("section", "heading", "title"):
        value = str(chunk.get(field) or "").strip()
        if value:
            return value
    return "EA package"


def _explicit_ea_section(text: str) -> str | None:
    match = re.search(r"\bEA(?:,)?\s+section\s+([0-9]+(?:\.[0-9]+)*)", text, re.IGNORECASE)
    if match:
        return f"EA section {match.group(1)}"
    return None


def _package_determination_basis(determination: dict | None) -> dict | None:
    if not determination:
        return None
    return {
        "component_key": determination.get("component_key"),
        "component_applies": determination.get("component_applies"),
        "determination_source": determination.get("determination_source"),
        "determination_explanation": determination.get("determination_explanation"),
        "review_section": determination.get("review_section"),
        "citation_label": determination.get("citation_label"),
        "chunk_id": determination.get("chunk_id"),
        "source_record_id": determination.get("source_record_id"),
    }


def _merge_package_evidence(
    preferred: list[dict],
    fallback: list[dict],
    *,
    limit: int,
) -> list[dict]:
    merged = []
    seen = set()
    for evidence in [*preferred, *fallback]:
        key = (
            evidence.get("chunk_id"),
            evidence.get("evidence_span", {}).get("source_char_start"),
            evidence.get("evidence_span", {}).get("source_char_end"),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(evidence)
        if len(merged) >= limit:
            break
    return merged


def _context_matches_component(context: dict, component: dict) -> bool:
    matched = _matched_context(context, component)
    return all(
        (
            not component[field]
            or bool(matched[matched_field])
        )
        for field, matched_field in (
            ("geographic_area_ids", "geographic_area_ids"),
            ("management_area_ids", "management_area_ids"),
            ("overlay_ids", "overlay_ids"),
        )
    )


def _matched_context(context: dict, component: dict) -> dict:
    geographic_area_ids = _resolved_entry_ids(context, "geographic_areas")
    management_area_ids = _resolved_entry_ids(context, "management_areas")
    overlay_ids = _resolved_entry_ids(context, "overlays")
    return {
        "geographic_area_ids": sorted(set(component["geographic_area_ids"]) & geographic_area_ids),
        "management_area_ids": sorted(set(component["management_area_ids"]) & management_area_ids),
        "overlay_ids": sorted(set(component["overlay_ids"]) & overlay_ids),
    }


def _resolved_entry_ids(context: dict, key: str) -> set[str]:
    return {str(entry.get("entry_id")) for entry in context.get(key, []) if entry.get("entry_id")}


def _reviewer_resolution_items_for_finding(
    *,
    review_id: str,
    component: dict,
    finding_status: str,
    applicability_status: str,
    rationale: str,
    source_set_id: str | None,
    source_set_matches: bool,
    plan_source_evidence: list[dict],
    package_evidence: list[dict],
) -> list[dict]:
    if finding_status in {"supported", "not_applicable"}:
        return []
    if not source_set_matches:
        reason = "component_source_set_drift"
        message = "Refresh or rebuild the component inventory for the active source set."
        severity = "high"
    elif not plan_source_evidence:
        reason = "missing_plan_source_evidence"
        message = "Verify the component against current source-library chunks before relying on it."
        severity = "high"
    elif not package_evidence:
        reason = "missing_package_evidence"
        message = "Review the EA package for evidence addressing the applicable plan component."
        severity = "medium"
    else:
        reason = "needs_reviewer_resolution"
        message = rationale
        severity = "medium"
    return [
        {
            "item_id": f"{component['component_id']}-{reason}",
            "review_id": review_id,
            "finding_id": f"{component['component_id']}-finding",
            "component_id": component["component_id"],
            "component_key": _component_reference_key(component),
            "component_type": component["component_type"],
            "component_text": component["component_text"],
            "component_context": {
                "section_heading": component.get("section_heading"),
                "geographic_area_ids": component.get("geographic_area_ids", []),
                "management_area_ids": component.get("management_area_ids", []),
                "overlay_ids": component.get("overlay_ids", []),
                "resource_topics": component.get("resource_topics", []),
                "activity_tags": component.get("activity_tags", []),
            },
            "package_evidence_terms": component.get("package_evidence_terms", []),
            "reason": reason,
            "severity": severity,
            "message": message,
            "finding_status": finding_status,
            "applicability_status": applicability_status,
            "source_set_id": source_set_id,
            "component_source_set_id": component["source_set_id"],
            "provenance": _finding_provenance(
                review_id=review_id,
                component=component,
                source_set_id=source_set_id,
                finding_status=finding_status,
            ),
        }
    ]


def _reviewer_resolution_queue(
    *,
    review_id: str,
    source_set_id: str | None,
    findings: list[dict],
) -> dict:
    items = [
        item
        for finding in findings
        for item in finding.get("reviewer_resolution_items", [])
    ]
    return {
        "schema_version": FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "item_count": len(items),
        "items": items,
    }


def _component_inventory_coverage(
    *,
    review_id: str,
    source_set_id: str | None,
    component_inventory_path: Path,
    components: list[dict],
) -> dict:
    build_coverage = _load_component_inventory_build_coverage(component_inventory_path)
    build_coverage_required = _component_inventory_build_coverage_required(
        component_inventory_path
    )
    build_coverage_path = _component_inventory_build_coverage_path(component_inventory_path)
    build_coverage_passed = (
        bool(build_coverage and build_coverage.get("passed"))
        if build_coverage_required or build_coverage is not None
        else True
    )
    component_type_counts = Counter(component["component_type"] for component in components)
    standard_component_ids = sorted(
        component["component_id"]
        for component in components
        if component["component_type"] == "standard"
    )
    source_set_mismatches = [
        {
            "component_id": component["component_id"],
            "component_source_set_id": component["source_set_id"],
            "review_source_set_id": source_set_id,
        }
        for component in components
        if component["source_set_id"] != source_set_id
    ]
    missing_source_chunks = [
        component["component_id"]
        for component in components
        if not component.get("source_chunk_ids")
    ]
    missing_provenance = [
        component["component_id"]
        for component in components
        if not _provenance_complete(component.get("provenance"))
    ]
    checks = [
        {
            "name": "component_inventory_has_components",
            "passed": bool(components),
            "details": {"component_count": len(components)},
        },
        {
            "name": "component_inventory_has_standard_records",
            "passed": bool(standard_component_ids),
            "details": {
                "standard_count": len(standard_component_ids),
                "standard_component_ids": standard_component_ids,
            },
        },
        {
            "name": "component_source_sets_match_review_source_set",
            "passed": bool(source_set_id) and not source_set_mismatches,
            "details": {"mismatches": source_set_mismatches},
        },
        {
            "name": "component_records_have_source_chunks",
            "passed": not missing_source_chunks,
            "details": {"component_ids": missing_source_chunks},
        },
        {
            "name": "component_records_have_provenance",
            "passed": not missing_provenance,
            "details": {"component_ids": missing_provenance},
        },
        {
            "name": "component_inventory_build_coverage_passes",
            "passed": build_coverage_passed,
            "details": {
                "required": build_coverage_required,
                "path": str(build_coverage_path),
                "present": build_coverage is not None,
                "schema_version": (
                    build_coverage.get("schema_version") if build_coverage else None
                ),
                "detected_standard_count": (
                    build_coverage.get("detected_standard_count") if build_coverage else None
                ),
                "built_standard_count": (
                    build_coverage.get("built_standard_count") if build_coverage else None
                ),
                "missing_standard_ids": (
                    build_coverage.get("missing_standard_ids") if build_coverage else None
                ),
                "duplicate_standard_ids": (
                    build_coverage.get("duplicate_standard_ids") if build_coverage else None
                ),
            },
        },
    ]
    return {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "component_inventory_build_coverage_path": str(build_coverage_path),
        "component_inventory_build_coverage_required": build_coverage_required,
        "component_inventory_build_coverage_passed": build_coverage_passed,
        "coverage_scope": "selected_component_inventory",
        "component_count": len(components),
        "component_type_counts": dict(component_type_counts),
        "standard_count": len(standard_component_ids),
        "standard_component_ids": standard_component_ids,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _applicable_standard_coverage(
    *,
    review_id: str,
    source_set_id: str | None,
    components: list[dict],
    findings: list[dict],
) -> dict:
    findings_by_component_id = {finding["component_id"]: finding for finding in findings}
    standard_components = [
        component for component in components if component["component_type"] == "standard"
    ]
    rows = [
        _standard_coverage_row(
            component=component,
            finding=findings_by_component_id.get(component["component_id"]),
        )
        for component in standard_components
    ]
    applicable_rows = [row for row in rows if row["applicability_status"] == "applicable"]
    missing_finding_ids = [
        row["component_id"] for row in rows if "missing_finding" in row["failure_reasons"]
    ]
    unapplied_applicable_standard_ids = [
        row["component_id"] for row in applicable_rows if not row["standard_applied"]
    ]
    invalid_status_ids = [
        row["component_id"]
        for row in rows
        if row["compliance_status"] not in VALID_COMPLIANCE_STATUSES
    ]
    standards_missing_plan_source_ids = [
        row["component_id"] for row in rows if row["plan_source_evidence_count"] == 0
    ]
    checks = [
        {
            "name": "standard_inventory_has_standards",
            "passed": bool(standard_components),
            "details": {"standard_count": len(standard_components)},
        },
        {
            "name": "standard_findings_present",
            "passed": not missing_finding_ids,
            "details": {"component_ids": missing_finding_ids},
        },
        {
            "name": "standard_compliance_statuses_are_valid",
            "passed": not invalid_status_ids,
            "details": {"component_ids": invalid_status_ids},
        },
        {
            "name": "standards_have_plan_source_evidence",
            "passed": not standards_missing_plan_source_ids,
            "details": {"component_ids": standards_missing_plan_source_ids},
        },
        {
            "name": "applicable_standards_have_package_and_plan_evidence",
            "passed": not unapplied_applicable_standard_ids,
            "details": {"component_ids": unapplied_applicable_standard_ids},
        },
    ]
    all_applicable_standards_applied = all(
        row["standard_applied"] for row in applicable_rows
    )
    return {
        "schema_version": FOREST_PLAN_APPLICABLE_STANDARD_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "standard_count": len(standard_components),
        "applicable_standard_count": len(applicable_rows),
        "applied_standard_count": sum(1 for row in applicable_rows if row["standard_applied"]),
        "all_applicable_standards_applied": all_applicable_standards_applied,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "standards": rows,
    }


def _standard_coverage_row(*, component: dict, finding: dict | None) -> dict:
    if finding is None:
        return {
            "component_id": component["component_id"],
            "component_key": _component_reference_key(component),
            "finding_id": None,
            "applicability_status": "needs_reviewer_resolution",
            "finding_status": "needs_reviewer_resolution",
            "compliance_status": "needs_reviewer_resolution",
            "plan_source_evidence_count": 0,
            "package_evidence_count": 0,
            "ea_review_section": None,
            "package_component_determination": None,
            "plan_source_citations": [],
            "package_evidence_citations": [],
            "standard_applied": False,
            "failure_reasons": ["missing_finding"],
        }
    plan_source_evidence_count = len(finding.get("plan_source_evidence") or [])
    package_evidence_count = len(finding.get("package_evidence") or [])
    compliance_status = str(finding.get("compliance_status") or "")
    failure_reasons = []
    if plan_source_evidence_count == 0:
        failure_reasons.append("missing_plan_source_evidence")
    if finding.get("applicability_status") == "applicable":
        if package_evidence_count == 0:
            failure_reasons.append("missing_package_evidence")
        if compliance_status in {"insufficient_evidence", "needs_reviewer_resolution", ""}:
            failure_reasons.append("unresolved_standard_compliance")
    elif finding.get("applicability_status") in {"candidate", "needs_reviewer_resolution"}:
        failure_reasons.append("unresolved_standard_applicability")
    if compliance_status not in VALID_COMPLIANCE_STATUSES:
        failure_reasons.append("invalid_compliance_status")
    return {
        "component_id": component["component_id"],
        "component_key": _component_reference_key(component),
        "finding_id": finding["finding_id"],
        "applicability_status": finding["applicability_status"],
        "finding_status": finding["finding_status"],
        "compliance_status": compliance_status,
        "plan_source_evidence_count": plan_source_evidence_count,
        "package_evidence_count": package_evidence_count,
        "ea_review_section": _finding_review_section(finding),
        "package_component_determination": (
            finding.get("applicability_basis", {}).get("package_component_determination")
        ),
        "plan_source_citations": _citation_labels(finding.get("plan_source_evidence") or []),
        "package_evidence_citations": _citation_labels(finding.get("package_evidence") or []),
        "standard_applied": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


def _finding_review_section(finding: dict) -> str | None:
    determination = (
        finding.get("applicability_basis", {}).get("package_component_determination")
    )
    if isinstance(determination, dict) and determination.get("review_section"):
        return str(determination["review_section"])
    for evidence in finding.get("package_evidence") or []:
        if evidence.get("review_section"):
            return str(evidence["review_section"])
        provenance = evidence.get("provenance") or {}
        for field in ("section", "heading"):
            value = str(provenance.get(field) or "").strip()
            if value:
                return value
        title = str(evidence.get("title") or "").strip()
        if title:
            return title
    return None


def _citation_labels(evidence_items: list[dict]) -> list[str]:
    return _dedupe_preserve_order(
        [
            label
            for item in evidence_items
            if (label := str(item.get("citation_label") or "").strip())
        ]
    )


def _validation_report(
    *,
    source_set_id: str | None,
    components: list[dict],
    findings: list[dict],
    queue: dict,
    inventory_coverage: dict,
    standard_coverage: dict,
) -> dict:
    checks = [
        _check_components_present(components),
        _check_component_source_sets_current(source_set_id, components),
        _check_component_provenance_complete(components),
        _check_finding_statuses(findings),
        _check_compliance_statuses(findings),
        _check_supported_findings_have_dual_evidence(findings),
        _check_supported_package_evidence_section_bindings(findings),
        _check_gap_findings_have_plan_source_evidence(findings),
        _check_finding_provenance_complete(findings),
        _check_reviewer_resolution_queue(queue, findings),
        _check_component_inventory_coverage(inventory_coverage),
        _check_applicable_standard_coverage(standard_coverage),
    ]
    return {
        "schema_version": "forest-plan-component-findings-validation-v0",
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_components_present(components: list[dict]) -> dict:
    return {
        "name": "component_inventory_has_components",
        "passed": bool(components),
        "details": {"component_count": len(components)},
    }


def _check_component_source_sets_current(
    source_set_id: str | None,
    components: list[dict],
) -> dict:
    mismatches = [
        {
            "component_id": component["component_id"],
            "component_source_set_id": component["source_set_id"],
            "review_source_set_id": source_set_id,
        }
        for component in components
        if component["source_set_id"] != source_set_id
    ]
    return {
        "name": "component_source_sets_match_review_source_set",
        "passed": not mismatches and bool(source_set_id),
        "details": {"mismatches": mismatches},
    }


def _check_component_provenance_complete(components: list[dict]) -> dict:
    failures = [
        component["component_id"]
        for component in components
        if not _provenance_complete(component.get("provenance"))
    ]
    return {
        "name": "component_provenance_complete",
        "passed": not failures,
        "details": {"component_ids": failures},
    }


def _check_finding_statuses(findings: list[dict]) -> dict:
    invalid = [
        {"finding_id": finding.get("finding_id"), "finding_status": finding.get("finding_status")}
        for finding in findings
        if finding.get("finding_status") not in VALID_FINDING_STATUSES
        or finding.get("applicability_status") not in VALID_APPLICABILITY_STATUSES
    ]
    return {
        "name": "finding_statuses_are_valid",
        "passed": bool(findings) and not invalid,
        "details": {"invalid": invalid, "finding_count": len(findings)},
    }


def _check_compliance_statuses(findings: list[dict]) -> dict:
    invalid = [
        {
            "finding_id": finding.get("finding_id"),
            "compliance_status": finding.get("compliance_status"),
        }
        for finding in findings
        if finding.get("compliance_status") not in VALID_COMPLIANCE_STATUSES
    ]
    return {
        "name": "compliance_statuses_are_valid",
        "passed": bool(findings) and not invalid,
        "details": {"invalid": invalid, "finding_count": len(findings)},
    }


def _check_supported_findings_have_dual_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["finding_id"]
        for finding in findings
        if finding.get("finding_status") in {"supported", "partial"}
        and (not finding.get("package_evidence") or not finding.get("plan_source_evidence"))
    ]
    return {
        "name": "supported_findings_have_package_and_plan_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_supported_package_evidence_section_bindings(findings: list[dict]) -> dict:
    failures = []
    for finding in findings:
        if finding.get("finding_status") not in {"supported", "partial"}:
            continue
        for evidence in finding.get("package_evidence") or []:
            section_binding = (
                evidence.get("section_binding")
                if isinstance(evidence.get("section_binding"), dict)
                else None
            )
            if section_binding and section_binding.get("matched") is True:
                continue
            if evidence.get("determination_source") == "ea_plan_consistency_table":
                continue
            failures.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "component_id": finding.get("component_id"),
                    "citation_label": evidence.get("citation_label"),
                    "review_section": evidence.get("review_section")
                    or _package_evidence_review_section(evidence),
                    "package_section_family": (
                        section_binding.get("package_section_family")
                        if section_binding
                        else None
                    ),
                    "component_section_families": (
                        section_binding.get("component_section_families")
                        if section_binding
                        else None
                    ),
                    "reason": (
                        "section_binding_mismatch"
                        if section_binding
                        else "missing_section_binding"
                    ),
                }
            )
    return {
        "name": "supported_package_evidence_section_bindings_match",
        "passed": not failures,
        "details": {"failures": failures, "failure_count": len(failures)},
    }


def _check_gap_findings_have_plan_source_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["finding_id"]
        for finding in findings
        if finding.get("finding_status") == "gap" and not finding.get("plan_source_evidence")
    ]
    return {
        "name": "gap_findings_have_plan_source_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_finding_provenance_complete(findings: list[dict]) -> dict:
    failures = [
        finding["finding_id"]
        for finding in findings
        if not _provenance_complete(finding.get("provenance"))
    ]
    return {
        "name": "finding_provenance_complete",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_reviewer_resolution_queue(queue: dict, findings: list[dict]) -> dict:
    queued_finding_ids = {item.get("finding_id") for item in queue.get("items", [])}
    expected = {
        finding["finding_id"]
        for finding in findings
        if finding.get("finding_status") in {"gap", "needs_reviewer_resolution", "partial"}
    }
    missing = sorted(expected - queued_finding_ids)
    invalid_schema = queue.get("schema_version") != FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION
    return {
        "name": "reviewer_resolution_queue_covers_unresolved_findings",
        "passed": not missing and not invalid_schema,
        "details": {
            "missing_finding_ids": missing,
            "queue_schema_version": queue.get("schema_version"),
            "item_count": len(queue.get("items", [])),
        },
    }


def _check_component_inventory_coverage(inventory_coverage: dict) -> dict:
    return {
        "name": "component_inventory_coverage_passes",
        "passed": bool(inventory_coverage.get("passed")),
        "details": {
            "schema_version": inventory_coverage.get("schema_version"),
            "component_count": inventory_coverage.get("component_count"),
            "standard_count": inventory_coverage.get("standard_count"),
            "component_inventory_build_coverage_required": inventory_coverage.get(
                "component_inventory_build_coverage_required"
            ),
            "component_inventory_build_coverage_passed": inventory_coverage.get(
                "component_inventory_build_coverage_passed"
            ),
        },
    }


def _check_applicable_standard_coverage(standard_coverage: dict) -> dict:
    return {
        "name": "all_applicable_standards_applied",
        "passed": bool(standard_coverage.get("passed"))
        and bool(standard_coverage.get("all_applicable_standards_applied")),
        "details": {
            "schema_version": standard_coverage.get("schema_version"),
            "standard_count": standard_coverage.get("standard_count"),
            "applicable_standard_count": standard_coverage.get("applicable_standard_count"),
            "applied_standard_count": standard_coverage.get("applied_standard_count"),
        },
    }


def _summary(
    *,
    review_id: str,
    source_set_id: str | None,
    component_inventory_path: Path,
    findings_path: Path,
    markdown_path: Path,
    queue_path: Path,
    inventory_coverage_path: Path,
    standard_coverage_path: Path,
    components: list[dict],
    findings: list[dict],
    queue: dict,
    validation: dict,
    inventory_coverage: dict,
    standard_coverage: dict,
) -> dict:
    status_counts = Counter(finding["finding_status"] for finding in findings)
    applicability_counts = Counter(finding["applicability_status"] for finding in findings)
    compliance_status_counts = Counter(finding["compliance_status"] for finding in findings)
    provenance_complete_count = sum(
        1 for finding in findings if _provenance_complete(finding.get("provenance"))
    )
    return {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "findings_path": str(findings_path),
        "markdown_path": str(markdown_path),
        "reviewer_resolution_queue_path": str(queue_path),
        "component_inventory_coverage_path": str(inventory_coverage_path),
        "applicable_standard_coverage_path": str(standard_coverage_path),
        "component_count": len(components),
        "finding_count": len(findings),
        "standard_count": int(standard_coverage.get("standard_count") or 0),
        "applicable_standard_count": int(
            standard_coverage.get("applicable_standard_count") or 0
        ),
        "applied_standard_count": int(standard_coverage.get("applied_standard_count") or 0),
        "all_applicable_standards_applied": bool(
            standard_coverage.get("all_applicable_standards_applied")
        ),
        "applicable_count": applicability_counts.get("applicable", 0),
        "supported_count": status_counts.get("supported", 0),
        "partial_count": status_counts.get("partial", 0),
        "gap_count": status_counts.get("gap", 0),
        "not_applicable_count": status_counts.get("not_applicable", 0),
        "needs_reviewer_resolution_count": status_counts.get("needs_reviewer_resolution", 0),
        "finding_status_counts": dict(status_counts),
        "applicability_status_counts": dict(applicability_counts),
        "compliance_status_counts": dict(compliance_status_counts),
        "reviewer_resolution_count": int(queue.get("item_count") or 0),
        "provenance_complete_count": provenance_complete_count,
        "component_inventory_coverage_passed": bool(inventory_coverage.get("passed")),
        "applicable_standard_coverage_passed": bool(standard_coverage.get("passed")),
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"],
    }


def _finding_provenance(
    *,
    review_id: str,
    component: dict,
    source_set_id: str | None,
    finding_status: str,
) -> dict:
    return {
        "entity": {
            "type": "forest_plan_component_finding",
            "review_id": review_id,
            "component_id": component["component_id"],
            "source_set_id": source_set_id,
        },
        "activity": {
            "type": "forest_plan_component_evaluation",
            "schema_version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
            "finding_status": finding_status,
            "evaluated_at": _utc_now(),
        },
        "agent": {
            "type": "deterministic_code",
            "name": "usfs_r1_ea_sources.forest_plan_components",
            "version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
        },
    }


def _markdown_report(report: dict, queue: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Forest Plan Component Findings",
        "",
        f"- Review ID: `{summary['review_id']}`",
        f"- Source set: `{summary['source_set_id']}`",
        f"- Reviewer ready: `{summary['reviewer_ready']}`",
        f"- Findings: `{summary['finding_status_counts']}`",
        f"- Reviewer-resolution items: `{summary['reviewer_resolution_count']}`",
        "",
        "## Findings",
        "",
    ]
    components_by_id = {
        component["component_id"]: component for component in report.get("components", [])
    }
    for finding in report["findings"]:
        component = components_by_id.get(finding["component_id"], {})
        lines.extend(
            [
                f"### {finding['component_id']}",
                "",
                f"- Component type: `{finding['component_type']}`",
                f"- Status: `{finding['finding_status']}`",
                f"- Applicability: `{finding['applicability_status']}`",
                f"- Source record: `{component.get('source_record_id')}`",
                f"- Rationale: {finding['rationale']}",
            ]
        )
        if finding["plan_source_evidence"]:
            evidence = finding["plan_source_evidence"][0]
            lines.extend(
                [
                    f"- Plan citation: `{evidence.get('citation_label')}`",
                    f"- Plan evidence: {_compact(evidence.get('evidence_span', {}).get('text'))}",
                ]
            )
        if finding["package_evidence"]:
            evidence = finding["package_evidence"][0]
            lines.extend(
                [
                    f"- Package citation: `{evidence.get('citation_label')}`",
                    f"- Package evidence: {_compact(evidence.get('evidence_span', {}).get('text'))}",
                ]
            )
        lines.append("")
    if queue.get("items"):
        lines.extend(["## Reviewer Resolution Queue", ""])
        for item in queue["items"]:
            lines.extend(
                [
                    f"- `{item['item_id']}`: {item['message']}",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _compact(value: object, limit: int = 360) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _provenance_complete(provenance: object) -> bool:
    if not isinstance(provenance, dict):
        return False
    return all(
        isinstance(provenance.get(key), dict) and bool(provenance[key])
        for key in ("entity", "activity", "agent")
    )


def _require_provenance(value: object, context: str) -> dict:
    if not _provenance_complete(value):
        raise ValueError(f"{context} must contain non-empty entity, activity, and agent objects.")
    return dict(value)


def _require_object(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object.")
    return value


def _require_list(value: dict, field: str, context: str) -> list:
    raw = value.get(field)
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{context}.{field} must be a non-empty list.")
    return raw


def _require_string_list(
    value: dict,
    field: str,
    context: str,
    *,
    required: bool = True,
) -> list[str]:
    raw = value.get(field)
    if raw is None and not required:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{context}.{field} must be a list.")
    strings = []
    for index, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}.{field}[{index}] must be a non-empty string.")
        strings.append(item.strip())
    if required and not strings:
        raise ValueError(f"{context}.{field} cannot be empty.")
    return strings


def _require_string(value: dict, field: str, context: str) -> str:
    raw = value.get(field)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{context}.{field} must be a non-empty string.")
    return raw.strip()


def _require_safe_string(value: dict, field: str, context: str) -> str:
    raw = _require_string(value, field, context)
    if not SAFE_ID_RE.fullmatch(raw):
        raise ValueError(
            f"{context}.{field} must contain only letters, numbers, dot, colon, underscore, or hyphen."
        )
    return raw


def _require_hex_string(value: dict, field: str, context: str) -> str:
    raw = _require_string(value, field, context)
    if not re.fullmatch(r"[0-9a-f]{64}", raw):
        raise ValueError(f"{context}.{field} must be a lowercase SHA256 hex digest.")
    return raw


def _duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if value and count > 1)


def _reject_duplicate(values: list[str], field: str, context: str) -> None:
    duplicates = _duplicate_values(values)
    if duplicates:
        raise ValueError(f"{context} contains duplicate {field} values: {duplicates}.")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object.")
            records.append(record)
    return records


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _load_component_inventory_build_coverage(component_inventory_path: Path) -> dict | None:
    coverage_path = _component_inventory_build_coverage_path(component_inventory_path)
    if not coverage_path.exists():
        return None
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {
            "schema_version": None,
            "passed": False,
            "load_error": f"Invalid JSON: {error}",
        }
    if not isinstance(coverage, dict):
        return {
            "schema_version": None,
            "passed": False,
            "load_error": "Coverage file must contain a JSON object.",
        }
    if (
        coverage.get("schema_version")
        != FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION
    ):
        coverage = dict(coverage)
        coverage["passed"] = False
        coverage["load_error"] = "Unsupported component inventory build coverage schema_version."
    return coverage


def _component_inventory_build_coverage_required(component_inventory_path: Path) -> bool:
    return (
        component_inventory_path.name == "component_inventory.json"
        and component_inventory_path.parent.name == "forest_plan_components"
    )


def _component_inventory_build_coverage_path(component_inventory_path: Path) -> Path:
    return component_inventory_path.with_name("component_inventory_build_coverage.json")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
