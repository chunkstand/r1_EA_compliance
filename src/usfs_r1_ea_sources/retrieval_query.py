from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from .retrieval_common import STOPWORDS, TOKEN_RE, _json_list


def query_retrieval_index(
    *,
    index_path: Path,
    query: str,
    limit: int = 5,
    document_role: str | None = None,
    support_document_role: str | None = None,
    authority_level: str | None = None,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
    review_topic: str | None = None,
    citation: str | None = None,
    host: str | None = None,
) -> dict:
    """Query the local evidence index and return provenance-bearing evidence spans."""

    if limit < 1:
        raise ValueError("limit must be at least 1")
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"Missing retrieval index: {index_path}")

    source_record_filter_ids = _normalized_filter_ids(
        source_record_id=source_record_id,
        source_record_ids=source_record_ids,
    )
    filters = {
        "document_role": document_role,
        "support_document_role": support_document_role,
        "authority_level": authority_level,
        "review_topic": review_topic,
        "citation": citation,
        "host": host,
    }
    if source_record_ids is not None:
        filters["source_record_ids"] = source_record_filter_ids
    elif source_record_filter_ids:
        filters["source_record_id"] = source_record_filter_ids[0]
    if not query.strip() and not any(value for value in filters.values()):
        raise ValueError("retrieval query requires query text or at least one filter")
    terms = _tokenize(query)
    with closing(sqlite3.connect(index_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = _load_candidate_rows(
            connection,
            document_role=document_role,
            support_document_role=support_document_role,
            authority_level=authority_level,
            source_record_ids=source_record_filter_ids,
            host=host,
        )

    scored: list[tuple[float, sqlite3.Row, list[str]]] = []
    for row in rows:
        topics = _json_list(row["review_topics_json"])
        if review_topic and not _topic_matches(review_topic, topics):
            continue
        if citation and not _citation_matches(citation, row):
            continue
        score = _score_row(row, terms=terms, query=query, topics=topics, review_topic=review_topic)
        if terms and score <= 0:
            continue
        scored.append((score, row, topics))

    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1]["source_record_id"] or ""),
            int(item[1]["chunk_index"] or 0),
        )
    )
    scored = _diversify_scored_rows(scored, limit=limit)
    results = [
        _result_from_row(rank=rank, score=score, row=row, topics=topics, terms=terms)
        for rank, (score, row, topics) in enumerate(scored[:limit], start=1)
    ]
    return {
        "query": query,
        "filters": {key: value for key, value in filters.items() if value is not None},
        "limit": limit,
        "hit_count": len(results),
        "results": results,
    }


def _load_candidate_rows(
    connection: sqlite3.Connection,
    *,
    document_role: str | None,
    support_document_role: str | None,
    authority_level: str | None,
    source_record_ids: list[str] | None,
    host: str | None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM chunks WHERE 1 = 1"
    params: list[object] = []
    if document_role:
        query += " AND document_role = ?"
        params.append(document_role)
    if support_document_role:
        query += " AND support_document_role = ?"
        params.append(support_document_role)
    if authority_level:
        query += " AND authority_level = ?"
        params.append(authority_level)
    if source_record_ids:
        placeholders = ", ".join("?" for _ in source_record_ids)
        query += f" AND source_record_id IN ({placeholders})"
        params.extend(source_record_ids)
    if host:
        query += " AND host = ?"
        params.append(host)
    query += " ORDER BY source_record_id, chunk_index"
    return list(connection.execute(query, params))


def _normalized_filter_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
) -> list[str] | None:
    values: list[str] = []
    if source_record_id is not None:
        values.append(str(source_record_id))
    values.extend(str(value) for value in (source_record_ids or []))
    normalized: list[str] = []
    seen = set()
    for value in values:
        candidate = str(value or "").strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized or None


def _result_from_row(
    *,
    rank: int,
    score: float,
    row: sqlite3.Row,
    topics: list[str],
    terms: list[str],
) -> dict:
    span = _evidence_span(str(row["text"] or ""), terms, int(row["char_start"]))
    return {
        "rank": rank,
        "score": round(score, 6),
        "chunk_id": row["chunk_id"],
        "source_record_id": row["source_record_id"],
        "title": row["title"],
        "document_role": row["document_role"],
        "support_document_role": _row_value(row, "support_document_role"),
        "authority_level": row["authority_level"],
        "citation_label": row["citation_label"],
        "review_topics": topics,
        "evidence_span": span,
        "provenance": {
            "source_set_id": row["source_set_id"],
            "artifact_sha256": row["artifact_sha256"],
            "artifact_path": row["artifact_path"],
            "original_url": row["original_url"],
            "effective_url": row["effective_url"],
            "final_url": row["final_url"],
            "parser_name": row["parser_name"],
            "parser_version": row["parser_version"],
            "extracted_at": row["extracted_at"],
            "source_text_path": row["source_text_path"],
            "char_start": row["char_start"],
            "char_end": row["char_end"],
            "page": row["page"],
            "section": row["section"],
            "heading": row["heading"],
            "content_sha256": row["content_sha256"],
        },
    }


def _row_value(row: sqlite3.Row, key: str, default: object | None = None) -> object | None:
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def _evidence_span(text: str, terms: list[str], source_chunk_start: int) -> dict:
    lower = text.lower()
    starts = [lower.find(term.lower()) for term in terms if lower.find(term.lower()) >= 0]
    first = min(starts) if starts else 0
    start = max(0, first - 140)
    end = min(len(text), start + 480)
    start = max(0, min(start, max(0, end - 480)))
    span_text = text[start:end].strip()
    leading_trim = len(text[start:end]) - len(text[start:end].lstrip())
    trailing_trim = len(text[start:end].rstrip())
    chunk_start = start + leading_trim
    chunk_end = start + trailing_trim
    return {
        "text": span_text,
        "chunk_char_start": chunk_start,
        "chunk_char_end": chunk_end,
        "source_char_start": source_chunk_start + chunk_start,
        "source_char_end": source_chunk_start + chunk_end,
    }


def _score_row(
    row: sqlite3.Row,
    *,
    terms: list[str],
    query: str,
    topics: list[str],
    review_topic: str | None,
) -> float:
    if not terms:
        return 0.1
    text = str(row["text"] or "")
    title = str(row["title"] or "")
    heading = str(row["heading"] or "")
    citation_label = str(row["citation_label"] or "")
    document_role = str(row["document_role"] or "").replace("_", " ")
    support_document_role = str(_row_value(row, "support_document_role") or "").replace("_", " ")
    authority_level = str(row["authority_level"] or "").replace("_", " ")
    topic_text = " ".join(topics)
    metadata_text = " ".join(
        [
            title,
            heading,
            citation_label,
            document_role,
            support_document_role,
            authority_level,
            topic_text,
        ]
    )
    score = 0.8 * _term_hit_fraction(terms, text=metadata_text)
    score += 0.55 * _term_hit_fraction(terms, text=text)
    score += 0.55 * _term_hit_fraction(terms, text=title)
    score += 0.2 * _term_hit_fraction(terms, text=heading)
    score += 0.2 * _term_hit_fraction(terms, text=topic_text)
    score += 0.15 * _term_hit_fraction(
        terms,
        text=" ".join([document_role, support_document_role, authority_level]),
    )
    lower_query = query.strip().lower()
    lower_title = title.lower()
    lower_metadata = metadata_text.lower()
    if query.strip() and query.strip().lower() in text.lower():
        score += 0.4
    if lower_query and lower_query in lower_title:
        score += 0.5
    if lower_query and lower_query in lower_metadata:
        score += 0.25
    if lower_title and _title_or_topic_has_compound_match(terms, lower_title):
        score += 0.25
    if topic_text and _title_or_topic_has_compound_match(terms, topic_text.lower()):
        score += 0.1
    if review_topic and _topic_matches(review_topic, topics):
        score += 0.2
    return score


def _term_hit_fraction(terms: list[str], *, text: str) -> float:
    if not terms:
        return 0.0
    token_set = set(_tokenize(text))
    return sum(1 for term in terms if _contains_term(term, token_set, text)) / len(terms)


def _title_or_topic_has_compound_match(terms: list[str], text: str) -> bool:
    matched = [term for term in terms if term in text]
    return len(matched) >= 2


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if term in token_set:
        return True
    lower = text.lower()
    if term in lower:
        return True
    return any(token.startswith(term) or term.startswith(token) for token in token_set)


def _tokenize(value: str) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(value.lower()):
        token = token.strip("'-.")
        if len(token) < 2 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _diversify_scored_rows(
    scored: list[tuple[float, sqlite3.Row, list[str]]],
    *,
    limit: int,
) -> list[tuple[float, sqlite3.Row, list[str]]]:
    """Prefer distinct sources before returning multiple chunks from one source."""

    source_order: list[str] = []
    scored_by_source: dict[str, list[tuple[float, sqlite3.Row, list[str]]]] = {}
    for item in scored:
        source_record_id = str(item[1]["source_record_id"] or "")
        bucket = scored_by_source.setdefault(source_record_id, [])
        if not bucket:
            source_order.append(source_record_id)
        bucket.append(item)

    diversified: list[tuple[float, sqlite3.Row, list[str]]] = []
    depth = 0
    while len(diversified) < limit:
        added = False
        for source_record_id in source_order:
            bucket = scored_by_source[source_record_id]
            if depth >= len(bucket):
                continue
            diversified.append(bucket[depth])
            added = True
            if len(diversified) >= limit:
                break
        if not added:
            break
        depth += 1
    return diversified


def _topic_matches(filter_value: str, topics: list[str]) -> bool:
    needle = filter_value.strip().lower()
    return any(needle == topic.lower() or needle in topic.lower() for topic in topics)


def _citation_matches(filter_value: str, row: sqlite3.Row) -> bool:
    needle = filter_value.strip().lower()
    haystack = " ".join(
        str(row[field] or "")
        for field in ("citation_label", "source_record_id", "title", "artifact_sha256")
    ).lower()
    return needle in haystack
