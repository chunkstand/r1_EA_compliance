from __future__ import annotations

import hashlib
import re

from .forest_plan_components_common import _compact, _component_id, _component_provenance, _dedupe_preserve_order, _normalized_component_text, _package_evidence_terms_from_text, _resource_topics_from_terms, _safe_identifier
from .forest_plan_components_inventory_common import _component_context_window, _component_type_from_label, _legacy_section_heading_for_match, _matching_profile_entry_ids, _section_heading_for_match, _suppress_tabular_component_label
from .forest_plan_components_inventory_legacy import _is_legacy_cross_reference, legacy_component_matches, ordered_legacy_chunks
from .forest_plan_components_models import CODED_COMPONENT_RE, COLON_COMPONENT_RE, COMPONENT_LABEL_RE, GENERIC_LEGACY_SECTION_CODES, LEGACY_SECTION_STOPWORDS, TERM_STOPWORDS, TOKEN_RE


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
    legacy_context: dict | None = None,
) -> list[dict]:
    text = str(chunk.get("text") or "")
    components = []
    fallback_heading = str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components")
    for match in _component_matches(
        text,
        fallback_heading=fallback_heading,
        legacy_context=legacy_context,
    ):
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
                        *[
                            str(entry_id)
                            for entry_id in match.get("management_area_ids", [])
                            if str(entry_id).strip()
                        ],
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
                **(
                    {"legacy_parse_context": dict(match["legacy_context"])}
                    if isinstance(match.get("legacy_context"), dict)
                    else {}
                ),
            }
        )
    return components


def _component_matches(
    text: str,
    *,
    fallback_heading: str,
    legacy_context: dict | None = None,
) -> list[dict[str, object]]:
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
    legacy_matches, _ = legacy_component_matches(
        text=text,
        fallback_heading=fallback_heading,
        initial_context=legacy_context,
    )
    for match in legacy_matches:
        code = _legacy_component_code(
            section_heading=str(match["section_heading"]),
            label=str(match["label"]),
            component_body=str(match["text"]),
            text=text,
            start=int(match["start"]),
            fallback_heading=fallback_heading,
            prefer_body_code=False,
        )
        matches.append({**match, "code": code})
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
        if _is_legacy_cross_reference(text=text, start=start, label=label):
            return None
        if label.strip().lower() in {
            "desired conditions",
            "goals",
            "guidelines",
            "objectives",
            "standards",
        }:
            return None
        section_heading = _legacy_section_heading_for_match(
            text=text,
            start=start,
            fallback=fallback_heading,
        )
        delimiter = str(groups.get("delimiter") or "").strip()
        code = _legacy_component_code(
            section_heading=section_heading,
            label=label,
            component_body=component_text,
            text=text,
            start=start,
            fallback_heading=fallback_heading,
            prefer_body_code=delimiter == "." or bool(groups.get("number_prefix")),
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
    prefer_body_code: bool = False,
) -> str:
    section_code = _legacy_section_code(section_heading)
    fallback_code = _legacy_section_code(fallback_heading)
    body_code = _legacy_body_code(
        component_body,
        max_parts=12 if prefer_body_code else 4,
    )
    body_scoped = False
    if prefer_body_code and body_code:
        section_code = f"{body_code}-{_legacy_component_text_digest(component_body)}"
    if not prefer_body_code and body_code and section_code.startswith("MA-"):
        section_code = f"{section_code}-{body_code}-{_legacy_component_text_digest(component_body)}"
    if not prefer_body_code and section_code and (
        section_code == fallback_code
        or _legacy_section_code_is_generic(
            section_code=section_code,
            section_heading=section_heading,
        )
    ):
        section_code = body_code
        body_scoped = bool(body_code)
    if not section_code:
        goal_number = _legacy_parent_goal_number(text=text, start=start)
        if goal_number:
            section_code = f"GOAL-{goal_number}"
    if not section_code:
        section_code = body_code
        body_scoped = bool(body_code)
    if not prefer_body_code and body_scoped and section_code:
        section_code = f"{section_code}-{_legacy_component_text_digest(component_body)}"
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
    management_area_match = re.search(r"\bmanagement\s+area\s+(?P<identifier>\d{1,3}[A-Za-z]?)\b", section_heading, re.IGNORECASE)
    management_area_code = f"MA-{_safe_identifier(management_area_match.group('identifier')).upper()}" if management_area_match else ""
    parts = [
        part.upper()
        for part in TOKEN_RE.findall(section_heading.lower())
        if part not in LEGACY_SECTION_STOPWORDS and part != "area"
    ]
    if management_area_code:
        return "-".join([management_area_code, *parts[:3]])
    return "-".join(parts[:4])


def _legacy_section_code_is_generic(*, section_code: str, section_heading: str) -> bool:
    normalized_heading = " ".join(section_heading.lower().split())
    code_tokens = [token for token in section_code.split("-") if token]
    if normalized_heading.startswith("chapter "):
        return True
    if "land management plan" in normalized_heading:
        return True
    if normalized_heading in {
        "desired condition",
        "desired conditions",
        "goal",
        "goals",
        "guideline",
        "guidelines",
        "monitoring",
        "objective",
        "objectives",
        "objectives none",
        "standard",
        "standards",
        "suitability",
    }:
        return True
    return len(code_tokens) == 1 and code_tokens[0] in GENERIC_LEGACY_SECTION_CODES


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


def _legacy_body_code(text: str, *, max_parts: int = 4) -> str:
    parts = [
        token.upper()
        for token in TOKEN_RE.findall(text.lower())
        if token not in TERM_STOPWORDS
    ]
    return "-".join(parts[:max_parts])


def _legacy_component_text_digest(text: str) -> str:
    normalized = _normalized_component_text(text)
    if not normalized:
        return "text"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8].upper()


def _suppress_component_match(match: dict[str, object], component_body: str) -> bool:
    return _suppress_tabular_component_label(
        label=str(match["label"]),
        code=str(match["code"]),
        number=str(match["number"]),
        text=component_body,
    )


def _detected_component_labels(chunks: list[dict]) -> list[dict]:
    labels = []
    legacy_context_by_source_record_id: dict[str, dict] = {}
    for chunk in ordered_legacy_chunks(chunks):
        text = str(chunk.get("text") or "")
        fallback_heading = str(
            chunk.get("heading") or chunk.get("title") or "Forest Plan Components"
        )
        source_record_id = str(chunk.get("source_record_id") or "")
        legacy_context = legacy_context_by_source_record_id.get(source_record_id, {})
        for match in _component_matches(
            text,
            fallback_heading=fallback_heading,
            legacy_context=legacy_context,
        ):
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
        _, next_context = legacy_component_matches(
            text=text,
            fallback_heading=fallback_heading,
            initial_context=legacy_context,
        )
        legacy_context_by_source_record_id[source_record_id] = next_context
    return labels
