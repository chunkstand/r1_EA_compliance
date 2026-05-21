from __future__ import annotations

from urllib.parse import urlparse
import hashlib
import re


RULE_CLAIM_LINK_SCHEMA_VERSION = "rule-claim-links-v0"
RULE_CLAIM_GAP_SCHEMA_VERSION = "rule-claim-link-gaps-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "not",
    "of",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "under",
    "when",
    "where",
    "with",
}


def _build_links(
    *,
    source_set_id: str,
    rule_pack: dict,
    claims: list[dict],
    top_k: int,
    created_at: str,
) -> tuple[list[dict], list[dict]]:
    links = []
    gaps = []
    for rule in rule_pack["rules"]:
        scored = []
        query = _rule_query(rule)
        terms = _tokenize(query)
        for claim in claims:
            if not _claim_matches_rule_filters(claim, rule.get("source_filters") or {}):
                continue
            score, matched_terms = _score_rule_claim(rule, claim, terms=terms, query=query)
            if terms and score <= 0:
                continue
            scored.append((score, matched_terms, claim))
        scored.sort(
            key=lambda item: (
                -item[0],
                str(item[2]["source_record_id"]),
                int(item[2]["source_char_start"]),
                str(item[2]["claim_id"]),
            )
        )
        selected = scored[:top_k]
        if not selected:
            gaps.append(
                _gap_record(
                    source_set_id=source_set_id,
                    rule_pack=rule_pack,
                    rule=rule,
                    created_at=created_at,
                    reason="no_validated_source_claim_match",
                )
            )
            continue
        for rank, (score, matched_terms, claim) in enumerate(selected, start=1):
            links.append(
                _link_record(
                    source_set_id=source_set_id,
                    rule_pack=rule_pack,
                    rule=rule,
                    claim=claim,
                    rank=rank,
                    score=score,
                    matched_terms=matched_terms,
                    created_at=created_at,
                )
            )
    return links, gaps


def _link_record(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule: dict,
    claim: dict,
    rank: int,
    score: float,
    matched_terms: list[str],
    created_at: str,
) -> dict:
    rule_id = str(rule["id"])
    claim_id = str(claim["claim_id"])
    link_id = _link_id(
        source_set_id=source_set_id,
        rule_pack_id=str(rule_pack["rule_pack_id"]),
        rule_pack_version=str(rule_pack["version"]),
        rule_id=rule_id,
        claim_id=claim_id,
    )
    return {
        "schema_version": RULE_CLAIM_LINK_SCHEMA_VERSION,
        "link_id": link_id,
        "source_set_id": source_set_id,
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "rule_id": rule_id,
        "rule_title": rule["title"],
        "rule_query": _rule_query(rule),
        "rule_requirement": rule.get("requirement"),
        "rule_source_filters": rule.get("source_filters", {}),
        "rank": rank,
        "score": round(score, 6),
        "matched_terms": matched_terms,
        "claim_id": claim_id,
        "claim_type": claim["claim_type"],
        "claim_text": claim["claim_text"],
        "source_record_id": claim["source_record_id"],
        "chunk_id": claim["chunk_id"],
        "citation_label": claim["citation_label"],
        "authority_level": claim["authority_level"],
        "document_role": claim["document_role"],
        "review_topics": claim.get("review_topics", []),
        "title": claim.get("title"),
        "artifact_sha256": claim["artifact_sha256"],
        "artifact_path": claim["artifact_path"],
        "original_url": claim.get("original_url"),
        "effective_url": claim.get("effective_url"),
        "final_url": claim.get("final_url"),
        "parser_name": claim["parser_name"],
        "parser_version": claim["parser_version"],
        "source_text_path": claim.get("source_text_path"),
        "source_char_start": claim["source_char_start"],
        "source_char_end": claim["source_char_end"],
        "chunk_char_start": claim["chunk_char_start"],
        "chunk_char_end": claim["chunk_char_end"],
        "content_sha256": claim["content_sha256"],
        "chunk_content_sha256": claim.get("chunk_content_sha256"),
        "claim_validation_status": claim["validation_status"],
        "validation_status": "valid",
        "created_at": created_at,
    }


def _gap_record(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule: dict,
    created_at: str,
    reason: str,
) -> dict:
    return {
        "schema_version": RULE_CLAIM_GAP_SCHEMA_VERSION,
        "gap_id": _gap_id(
            source_set_id=source_set_id,
            rule_pack_id=str(rule_pack["rule_pack_id"]),
            rule_pack_version=str(rule_pack["version"]),
            rule_id=str(rule["id"]),
            reason=reason,
        ),
        "source_set_id": source_set_id,
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "rule_id": rule["id"],
        "rule_title": rule["title"],
        "rule_query": _rule_query(rule),
        "rule_requirement": rule.get("requirement"),
        "rule_source_filters": rule.get("source_filters", {}),
        "reason": reason,
        "validation_status": "explicit_no_claim_gap",
        "created_at": created_at,
    }


def _rule_query(rule: dict) -> str:
    return " ".join(
        str(value)
        for value in (
            rule.get("source_query"),
            rule.get("requirement"),
            rule.get("title"),
            " ".join(str(term) for term in rule.get("package_terms", [])),
        )
        if str(value or "").strip()
    )


def _score_rule_claim(
    rule: dict,
    claim: dict,
    *,
    terms: list[str],
    query: str,
) -> tuple[float, list[str]]:
    text = _claim_search_text(claim)
    token_set = set(_tokenize(text))
    matched_terms = [term for term in terms if _contains_term(term, token_set, text)]
    if not terms:
        return 0.1, []
    score = len(matched_terms) / len(terms)
    query_value = str(rule.get("source_query") or "").strip().lower()
    if query_value and query_value in text.lower():
        score += 0.35
    for phrase in rule.get("package_terms", []):
        phrase_value = str(phrase or "").strip().lower()
        if phrase_value and phrase_value in text.lower():
            score += 0.08
    source_filters = rule.get("source_filters") or {}
    review_topic = source_filters.get("review_topic") or source_filters.get("topic")
    if review_topic and _topic_matches(str(review_topic), claim.get("review_topics", [])):
        score += 0.15
    return score, matched_terms


def _claim_search_text(claim: dict) -> str:
    return " ".join(
        str(value)
        for value in (
            claim.get("claim_text"),
            claim.get("title"),
            claim.get("citation_label"),
            " ".join(str(topic) for topic in claim.get("review_topics", [])),
        )
        if str(value or "").strip()
    )


def _claim_matches_rule_filters(claim: dict, filters: dict) -> bool:
    source_record_filter = filters.get("source_record_id")
    for key in ("document_role", "authority_level", "source_record_id"):
        value = filters.get(key)
        if value and str(claim.get(key) or "").lower() != str(value).lower():
            return False
    review_topic = filters.get("review_topic") or filters.get("topic")
    if (
        review_topic
        and not source_record_filter
        and not _topic_matches(str(review_topic), claim.get("review_topics", []))
    ):
        return False
    citation = filters.get("citation")
    if citation and not _citation_matches(str(citation), claim):
        return False
    host = filters.get("host")
    if host and not _host_matches(str(host), claim):
        return False
    return True


def _topic_matches(filter_value: str, topics: list[str]) -> bool:
    needle = _normalized_topic_text(filter_value)
    if not needle:
        return False
    needle_tokens = set(_tokenize(needle))
    for topic in topics:
        topic_text = _normalized_topic_text(str(topic))
        if needle == topic_text or needle in topic_text:
            return True
        topic_tokens = set(_tokenize(topic_text))
        if needle_tokens and len(needle_tokens & topic_tokens) >= min(2, len(needle_tokens)):
            return True
    return False


def _normalized_topic_text(value: str) -> str:
    return " ".join(_tokenize(value.replace("_", " ").replace("-", " ")))


def _citation_matches(filter_value: str, claim: dict) -> bool:
    needle = filter_value.lower()
    return any(
        needle in str(claim.get(field) or "").lower()
        for field in ("citation_label", "source_record_id", "title", "artifact_sha256")
    )


def _host_matches(filter_value: str, claim: dict) -> bool:
    needle = filter_value.lower()
    for field in ("final_url", "effective_url", "original_url"):
        value = str(claim.get(field) or "")
        if not value:
            continue
        host = urlparse(value).netloc.lower()
        if needle == host or needle in host:
            return True
    return False


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if " " in term:
        return term.lower() in text.lower()
    return term.lower() in token_set


def _tokenize(text: str) -> list[str]:
    tokens = []
    seen = set()
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group(0).strip("._-")
        if len(token) < 3 or token in STOPWORDS or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def _safe_segment(value: str) -> str:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(
            "rule_pack_id and version must contain only letters, numbers, dot, underscore, or hyphen."
        )
    return value


def _link_id(
    *,
    source_set_id: str,
    rule_pack_id: str,
    rule_pack_version: str,
    rule_id: str,
    claim_id: str,
) -> str:
    material = "|".join([source_set_id, rule_pack_id, rule_pack_version, rule_id, claim_id])
    return f"rule_claim_link:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _gap_id(
    *,
    source_set_id: str,
    rule_pack_id: str,
    rule_pack_version: str,
    rule_id: str,
    reason: str,
) -> str:
    material = "|".join([source_set_id, rule_pack_id, rule_pack_version, rule_id, reason])
    return f"rule_claim_gap:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"
