from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime

from .forest_plan_components_models import FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION, FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION, LEADING_COMPONENT_LABEL_RE, MODAL_BOUNDARY_RE, TERM_STOPWORDS, TOKEN_RE


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


def _compact(value: object, limit: int = 360) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if value and count > 1)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
