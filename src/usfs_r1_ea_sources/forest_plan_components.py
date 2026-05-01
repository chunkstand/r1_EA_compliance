from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .ea_review import _search_package_chunks
from .forest_plan_profiles import load_forest_plan_profile
from .retrieval import query_retrieval_index


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
COMPONENT_LABEL_RE = re.compile(
    r"\b(?P<label>Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[A-Za-z0-9.]+)\s+"
    r"(?P<text>.*?)(?=\b(?:Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\([A-Za-z0-9-]+\)\s*[A-Za-z0-9.]+\s+|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)
SECTION_HEADING_RE = re.compile(
    r"Plan Components[-\u2013\u2014]\s*(?P<section>[^.]+)",
    re.IGNORECASE,
)
LEADING_COMPONENT_LABEL_RE = re.compile(
    r"^(?:Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\([A-Za-z0-9-]+\)\s*[A-Za-z0-9.]+\s+",
    re.IGNORECASE,
)
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
    "for",
    "from",
    "in",
    "is",
    "may",
    "must",
    "new",
    "not",
    "of",
    "or",
    "shall",
    "should",
    "that",
    "the",
    "to",
    "will",
    "with",
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


def build_forest_plan_component_inventory(
    *,
    output_dir: Path,
    source_set_id: str,
    source_record_id: str,
    forest_unit_id: str,
    plan_version: str,
    chunks_path: Path | None = None,
    geographic_area_ids: list[str] | None = None,
    management_area_ids: list[str] | None = None,
    overlay_ids: list[str] | None = None,
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
    chunks = [
        chunk
        for chunk in _read_jsonl(chunks_path)
        if chunk.get("source_set_id") == source_set_id
        and chunk.get("source_record_id") == source_record_id
        and chunk.get("document_role") == "forest_plan"
    ]
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
    components = _merge_overlapping_component_records(components)
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
    coverage = _component_inventory_build_coverage(
        source_set_id=source_set_id,
        source_record_id=source_record_id,
        chunks_path=chunks_path,
        chunks=chunks,
        components=components,
        validation_errors=validation_errors,
    )
    inventory = {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
        "inventory_id": _safe_identifier(f"{forest_unit_id}-{plan_version}-components"),
        "forest_unit_id": forest_unit_id,
        "plan_version": plan_version,
        "source_set_id": source_set_id,
        "components": components,
    }
    summary = {
        "schema_version": "forest-plan-component-inventory-build-summary-v0",
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunks_path": str(chunks_path),
        "inventory_path": str(inventory_path),
        "components_jsonl_path": str(components_jsonl_path),
        "coverage_path": str(coverage_path),
        "component_count": len(components),
        "component_type_counts": dict(
            Counter(component["component_type"] for component in components)
        ),
        "standard_count": sum(
            1 for component in components if component["component_type"] == "standard"
        ),
        "coverage_passed": coverage["passed"],
        "passed": coverage["passed"],
    }
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
    for match in COMPONENT_LABEL_RE.finditer(text):
        label = match.group("label")
        code = match.group("code")
        number = match.group("number")
        component_body = _compact(match.group("text"), limit=10000)
        component_text = _compact(f"{label} ({code}) {number} {component_body}", limit=10000)
        section_heading = _section_heading_for_match(
            text=text,
            start=match.start(),
            fallback=str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components"),
        )
        context_text = f"{section_heading} {code} {component_text}"
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
    source_record_id: str,
    chunks_path: Path,
    chunks: list[dict],
    components: list[dict],
    validation_errors: list[dict],
) -> dict:
    detected_labels = _merge_overlapping_detected_labels(_detected_component_labels(chunks))
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
    ]
    return {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunks_path": str(chunks_path),
        "selected_chunk_count": len(chunks),
        "detected_component_count": len(detected_labels),
        "detected_standard_count": len(detected_standards),
        "built_component_count": len(components),
        "built_standard_count": len(built_standard_ids),
        "missing_component_ids": missing_component_ids,
        "missing_standard_ids": missing_standard_ids,
        "duplicate_component_ids": duplicate_component_ids,
        "duplicate_standard_ids": duplicate_standard_ids,
        "validation_errors": validation_errors,
        "detected_component_labels": detected_labels,
        "detected_standard_labels": detected_standards,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _detected_component_labels(chunks: list[dict]) -> list[dict]:
    labels = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        for match in COMPONENT_LABEL_RE.finditer(text):
            component_type = _component_type_from_label(match.group("label"))
            component_id = _component_id(
                source_record_id=str(chunk.get("source_record_id") or ""),
                code=match.group("code"),
                number=match.group("number"),
            )
            component_text = _compact(
                f"{match.group('label')} ({match.group('code')}) "
                f"{match.group('number')} {match.group('text')}",
                limit=10000,
            )
            labels.append(
                {
                    "component_id": component_id,
                    "component_type": component_type,
                    "label": match.group("label"),
                    "code": match.group("code"),
                    "number": match.group("number"),
                    "component_text": component_text,
                    "source_record_id": str(chunk.get("source_record_id") or ""),
                    "chunk_id": str(chunk.get("chunk_id") or ""),
                    "section_heading": _section_heading_for_match(
                        text=text,
                        start=match.start(),
                        fallback=str(
                            chunk.get("heading") or chunk.get("title") or "Forest Plan Components"
                        ),
                    ),
                }
            )
    return labels


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
    matches = []
    for entry in entries:
        entry_id = str(getattr(entry, "entry_id", "") or "").strip()
        terms = getattr(entry, "terms", ())
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
    return _compact(fallback, limit=240)


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
    package_evidence = package_search["results"]
    plan_source_evidence = []
    if source_set_matches and context_match and index_path is not None:
        plan_source_evidence = _component_plan_source_evidence(
            component=component,
            index_path=index_path,
            limit=source_top_k,
        )

    if context.get("needs_reviewer_resolution"):
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The forest-plan context resolver requires reviewer resolution before component findings can be trusted."
    elif not source_set_matches:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component inventory source set does not match the review source set."
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
    terms = component.get("package_evidence_terms") or [
        *component.get("resource_topics", []),
        *component.get("activity_tags", []),
    ]
    query = " ".join([component["section_heading"], component["component_text"], *terms])
    return _search_package_chunks(
        package_chunks,
        query=query,
        required_terms=list(terms),
        limit=limit,
    )


def _component_plan_source_evidence(
    *,
    component: dict,
    index_path: Path,
    limit: int,
) -> list[dict]:
    result = query_retrieval_index(
        index_path=index_path,
        query=component["component_text"],
        limit=max(limit, 5),
        document_role="forest_plan",
        source_record_id=component["source_record_id"],
    )
    source_chunk_ids = set(component["source_chunk_ids"])
    filtered = [
        row
        for row in result["results"]
        if not source_chunk_ids or row.get("chunk_id") in source_chunk_ids
    ]
    return filtered[:limit]


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
            "finding_id": None,
            "applicability_status": "needs_reviewer_resolution",
            "finding_status": "needs_reviewer_resolution",
            "compliance_status": "needs_reviewer_resolution",
            "plan_source_evidence_count": 0,
            "package_evidence_count": 0,
            "standard_applied": False,
            "failure_reasons": ["missing_finding"],
        }
    plan_source_evidence_count = len(finding.get("plan_source_evidence") or [])
    package_evidence_count = len(finding.get("package_evidence") or [])
    compliance_status = str(finding.get("compliance_status") or "")
    failure_reasons = []
    if finding.get("applicability_status") == "applicable":
        if plan_source_evidence_count == 0:
            failure_reasons.append("missing_plan_source_evidence")
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
        "finding_id": finding["finding_id"],
        "applicability_status": finding["applicability_status"],
        "finding_status": finding["finding_status"],
        "compliance_status": compliance_status,
        "plan_source_evidence_count": plan_source_evidence_count,
        "package_evidence_count": package_evidence_count,
        "standard_applied": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


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
