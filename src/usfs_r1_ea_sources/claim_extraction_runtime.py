from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import re


CLAIM_SCHEMA_VERSION = "source-claims-v0"
CLAIM_EXTRACTOR_NAME = "deterministic_legal_claim_patterns"
CLAIM_EXTRACTOR_VERSION = "0.1.0"
SUPPORTED_CLAIM_TYPES = {
    "authorization",
    "condition",
    "definition",
    "exemption",
    "guidance",
    "obligation",
    "prohibition",
}


@dataclass(frozen=True)
class ClaimPattern:
    claim_type: str
    pattern_id: str
    regex: re.Pattern[str]
    confidence: float


CLAIM_PATTERNS = (
    ClaimPattern(
        "prohibition",
        "negative_mandate",
        re.compile(r"\b(?:shall|must|may)\s+not\b|\b(?:prohibited|forbidden)\b", re.I),
        0.92,
    ),
    ClaimPattern(
        "exemption",
        "not_required",
        re.compile(
            r"\b(?:is|are|was|were|be)?\s*not\s+required\s+to\b|"
            r"\bdoes\s+not\s+require\b|\bshall\s+not\s+require\b",
            re.I,
        ),
        0.88,
    ),
    ClaimPattern(
        "condition",
        "conditional_mandate",
        re.compile(
            r"\b(?:if|when|unless|where)\b.{0,500}\b(?:shall|must|required|may|should)\b|"
            r"\b(?:shall|must|required|may|should)\b.{0,500}\b(?:if|when|unless|where)\b",
            re.I | re.S,
        ),
        0.84,
    ),
    ClaimPattern(
        "obligation",
        "mandatory_action",
        re.compile(
            r"\b(?:shall|must|required\s+to|is\s+required\s+to|are\s+required\s+to)\b",
            re.I,
        ),
        0.9,
    ),
    ClaimPattern(
        "authorization",
        "permissive_action",
        re.compile(r"\b(?:may|authorized\s+to|is\s+authorized\s+to|are\s+authorized\s+to)\b", re.I),
        0.74,
    ),
    ClaimPattern(
        "definition",
        "definition",
        re.compile(r"\b(?:means|includes|refers\s+to|is\s+defined\s+as|are\s+defined\s+as)\b", re.I),
        0.78,
    ),
    ClaimPattern(
        "definition",
        "structural_definition",
        re.compile(
            r"\b(?:consists\s+of|comprises|is\s+composed\s+of|are\s+composed\s+of|"
            r"serves\s+as|codif(?:y|ies))\b",
            re.I,
        ),
        0.72,
    ),
    ClaimPattern(
        "guidance",
        "recommended_action",
        re.compile(r"\bshould\b", re.I),
        0.65,
    ),
)
_DUTY_STATEMENT_DOCUMENT_ROLES = {"agency_policy", "state_requirement"}
_DUTY_STATEMENT_PATTERN = ClaimPattern(
    "guidance",
    "duty_list_item",
    re.compile(
        r"^(?:Maintaining|Evaluating|Supporting|Assisting|Providing|Developing|Implementing|"
        r"Administering|Preparing|Conducting|Coordinating|Documenting|Reviewing|Preserving|"
        r"Protecting)\b",
        re.I,
    ),
    0.67,
)


def _extract_claims(*, chunks: list[dict], source_set_id: str) -> list[dict]:
    claims_by_key: dict[tuple[str, int, int, str, str], dict] = {}
    extracted_at = _utc_now()
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        for sentence_start, sentence_end, sentence_text in _sentence_spans(text):
            match = _match_claim_pattern(
                sentence_text,
                document_role=str(chunk.get("document_role") or ""),
            )
            if match is None:
                continue
            pattern, pattern_match = match
            claim_start = sentence_start
            claim_end = sentence_end
            claim_text = sentence_text
            if len(claim_text) > 1200:
                claim_start, claim_end, claim_text = _window_claim_span(
                    text,
                    sentence_start,
                    sentence_end,
                    sentence_start + pattern_match.start(),
                )
            source_char_start = int(chunk["char_start"]) + claim_start
            source_char_end = int(chunk["char_start"]) + claim_end
            normalized_text = _normalize_text(claim_text)
            dedupe_key = (
                str(chunk["source_record_id"]),
                source_char_start,
                source_char_end,
                pattern.claim_type,
                normalized_text,
            )
            if dedupe_key in claims_by_key:
                continue
            claim_id = _claim_id(
                source_set_id=source_set_id,
                chunk_id=str(chunk["chunk_id"]),
                source_char_start=source_char_start,
                source_char_end=source_char_end,
                claim_type=pattern.claim_type,
                claim_text=claim_text,
            )
            claims_by_key[dedupe_key] = {
                "schema_version": CLAIM_SCHEMA_VERSION,
                "claim_id": claim_id,
                "source_set_id": source_set_id,
                "source_record_id": str(chunk["source_record_id"]),
                "chunk_id": str(chunk["chunk_id"]),
                "chunk_index": int(chunk.get("chunk_index") or 0),
                "claim_type": pattern.claim_type,
                "claim_text": claim_text,
                "normalized_claim_text": normalized_text,
                "pattern_id": pattern.pattern_id,
                "confidence": pattern.confidence,
                "title": chunk.get("title"),
                "document_role": chunk.get("document_role"),
                "authority_level": chunk.get("authority_level"),
                "review_topics": chunk.get("review_topics", []),
                "citation_label": chunk.get("citation_label"),
                "artifact_sha256": chunk.get("artifact_sha256"),
                "artifact_path": chunk.get("artifact_path"),
                "original_url": chunk.get("original_url"),
                "effective_url": chunk.get("effective_url"),
                "final_url": chunk.get("final_url"),
                "parser_name": chunk.get("parser_name"),
                "parser_version": chunk.get("parser_version"),
                "source_text_path": chunk.get("source_text_path"),
                "page": chunk.get("page"),
                "section": chunk.get("section"),
                "heading": chunk.get("heading"),
                "chunk_char_start": claim_start,
                "chunk_char_end": claim_end,
                "source_char_start": source_char_start,
                "source_char_end": source_char_end,
                "content_sha256": _text_sha256(claim_text),
                "chunk_content_sha256": chunk.get("content_sha256"),
                "extractor_name": CLAIM_EXTRACTOR_NAME,
                "extractor_version": CLAIM_EXTRACTOR_VERSION,
                "extracted_at": extracted_at,
                "validation_status": "valid",
            }
    return sorted(
        claims_by_key.values(),
        key=lambda claim: (
            str(claim["source_record_id"]),
            int(claim["source_char_start"]),
            str(claim["claim_id"]),
        ),
    )


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    raw_start = 0
    for index, char in enumerate(text):
        if char not in ".!?;":
            continue
        if char == "." and _period_is_abbreviation(text, index):
            continue
        _append_sentence_span(spans, text, raw_start, index + 1)
        raw_start = index + 1
    _append_sentence_span(spans, text, raw_start, len(text))
    return spans


def _append_sentence_span(
    spans: list[tuple[int, int, str]],
    text: str,
    raw_start: int,
    raw_end: int,
) -> None:
    value = text[raw_start:raw_end]
    leading = len(value) - len(value.lstrip())
    trailing = len(value.rstrip())
    start = raw_start + leading
    end = raw_start + trailing
    if end <= start:
        return
    sentence = text[start:end]
    if len(sentence) < 12:
        return
    spans.append((start, end, sentence))


def _period_is_abbreviation(text: str, index: int) -> bool:
    prefix = text[max(0, index - 16) : index + 1]
    if re.search(r"(?:[A-Z]\.){1,5}$", prefix):
        return True
    if re.search(r"\b(?:No|Sec|Pt|Ch|Subsec|Para|Fig|Vol)\.$", prefix, re.I):
        return True
    if index > 0 and index + 1 < len(text) and text[index - 1].isdigit() and text[index + 1].isdigit():
        return True
    return False


def _match_claim_pattern(
    sentence: str,
    *,
    document_role: str = "",
) -> tuple[ClaimPattern, re.Match[str]] | None:
    for pattern in CLAIM_PATTERNS:
        match = pattern.regex.search(sentence)
        if match:
            return pattern, match
    if document_role in _DUTY_STATEMENT_DOCUMENT_ROLES:
        match = _DUTY_STATEMENT_PATTERN.regex.search(sentence)
        if match and len(sentence.split()) >= 5:
            return _DUTY_STATEMENT_PATTERN, match
    return None


def _window_claim_span(
    text: str,
    sentence_start: int,
    sentence_end: int,
    pattern_start: int,
    *,
    max_chars: int = 1200,
) -> tuple[int, int, str]:
    start = max(sentence_start, pattern_start - 450)
    end = min(sentence_end, start + max_chars)
    start = max(sentence_start, min(start, max(sentence_start, end - max_chars)))
    value = text[start:end]
    leading = len(value) - len(value.lstrip())
    trailing = len(value.rstrip())
    start += leading
    end = start + max(0, trailing - leading)
    return start, end, text[start:end]


def _claim_metrics(
    *,
    claims: list[dict],
    entities: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_ids = {node["id"] for node in nodes}
    dangling = sum(
        1 for edge in edges if edge.get("source") not in node_ids or edge.get("target") not in node_ids
    )
    node_type_counts = Counter(node["type"] for node in nodes)
    claim_ids = {claim["claim_id"] for claim in claims}
    evidence_claim_ids = {
        edge["source"]
        for edge in edges
        if edge.get("relationship") == "CLAIM_HAS_EVIDENCE_SPAN"
    }
    authority_claim_ids = {
        edge["source"] for edge in edges if edge.get("relationship") == "CLAIM_HAS_AUTHORITY"
    }
    topic_claim_ids = {
        edge["source"]
        for edge in edges
        if edge.get("relationship") == "CLAIM_SUPPORTS_REVIEW_TOPIC"
    }
    entity_claim_ids = {
        edge["source"] for edge in edges if edge.get("relationship") == "CLAIM_MENTIONS_ENTITY"
    }
    return {
        "claim_count": len(claims),
        "entity_count": len(entities),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "claim_node_count": node_type_counts.get("Claim", 0),
        "entity_node_count": node_type_counts.get("Entity", 0),
        "authority_node_count": node_type_counts.get("Authority", 0),
        "claim_evidence_span_count": node_type_counts.get("ClaimEvidenceSpan", 0),
        "dangling_edge_count": dangling,
        "claim_evidence_coverage_rate": _rate(len(evidence_claim_ids & claim_ids), len(claim_ids)),
        "claim_authority_coverage_rate": _rate(len(authority_claim_ids & claim_ids), len(claim_ids)),
        "claim_topic_coverage_rate": _rate(len(topic_claim_ids & claim_ids), len(claim_ids)),
        "claim_entity_coverage_rate": _rate(len(entity_claim_ids & claim_ids), len(claim_ids)),
    }


def _claim_id(
    *,
    source_set_id: str,
    chunk_id: str,
    source_char_start: int,
    source_char_end: int,
    claim_type: str,
    claim_text: str,
) -> str:
    material = "|".join(
        [
            source_set_id,
            chunk_id,
            str(source_char_start),
            str(source_char_end),
            claim_type,
            _normalize_text(claim_text),
        ]
    )
    return f"claim:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
