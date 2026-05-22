from __future__ import annotations

import re
from pathlib import Path
from .review_package_support import search_package_chunks

from .forest_plan_components_common import _dedupe_preserve_order, _dedupe_terms, _normalized_component_text
from .forest_plan_components_determination import _component_reference_key
from .forest_plan_components_models import FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION, GENERIC_COMPONENT_TERMS, SECTION_FAMILY_KEYWORDS, TOKEN_RE


def _component_package_search(
    *,
    component: dict,
    package_chunks: list[dict],
    limit: int,
) -> dict:
    terms = _component_package_search_terms(component)
    section_families = _component_section_families(component)
    query = " ".join([component["section_heading"], component["component_text"], *terms])
    raw = search_package_chunks(
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
