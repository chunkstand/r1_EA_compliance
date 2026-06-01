from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3

from .records import aliased_source_record_ids
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

    display_source_record_filter_ids = _display_filter_ids(
        source_record_id=source_record_id,
        source_record_ids=source_record_ids,
    )
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
        filters["source_record_ids"] = display_source_record_filter_ids
    elif display_source_record_filter_ids:
        filters["source_record_id"] = display_source_record_filter_ids[0]
    if not query.strip() and not any(value for value in filters.values()):
        raise ValueError("retrieval query requires query text or at least one filter")
    terms = _tokenize(query)
    phrases = _query_phrases(query)
    with closing(sqlite3.connect(index_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows, retrieval_mode, fts_candidate_count = _load_candidate_rows(
            connection,
            terms=terms,
            document_role=document_role,
            support_document_role=support_document_role,
            authority_level=authority_level,
            source_record_ids=source_record_filter_ids,
            host=host,
            limit=max(limit * 50, 250),
        )
    term_weights = _query_term_weights(terms, phrases)

    scored: list[tuple[float, sqlite3.Row, list[str]]] = []
    for row in rows:
        topics = _json_list(row["review_topics_json"])
        if review_topic and not _topic_matches(review_topic, topics):
            continue
        if citation and not _citation_matches(citation, row):
            continue
        score = _score_row(
            row,
            terms=terms,
            phrases=phrases,
            query=query,
            topics=topics,
            review_topic=review_topic,
            term_weights=term_weights,
        )
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
        "retrieval_mode": retrieval_mode,
        "candidate_count": len(rows),
        "fts_candidate_count": fts_candidate_count,
        "hit_count": len(results),
        "results": results,
    }


def _load_candidate_rows(
    connection: sqlite3.Connection,
    *,
    terms: list[str],
    document_role: str | None,
    support_document_role: str | None,
    authority_level: str | None,
    source_record_ids: list[str] | None,
    host: str | None,
    limit: int,
) -> tuple[list[sqlite3.Row], str, int]:
    if terms and _fts_table_available(connection):
        rows = _load_fts_candidate_rows(
            connection,
            terms=terms,
            document_role=document_role,
            support_document_role=support_document_role,
            authority_level=authority_level,
            source_record_ids=source_record_ids,
            host=host,
            limit=limit,
        )
        if rows:
            return rows, "fts_first_stage", len(rows)
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
    rows = list(connection.execute(query, params))
    return rows, "row_scan", 0


def _load_fts_candidate_rows(
    connection: sqlite3.Connection,
    *,
    terms: list[str],
    document_role: str | None,
    support_document_role: str | None,
    authority_level: str | None,
    source_record_ids: list[str] | None,
    host: str | None,
    limit: int,
) -> list[sqlite3.Row]:
    fts_query = _fts_query(terms)
    if not fts_query:
        return []
    query = """
        SELECT c.*, bm25(chunks_fts) AS fts_bm25
        FROM chunks_fts
        JOIN chunks c ON c.rowid = chunks_fts.rowid
        WHERE chunks_fts MATCH ?
    """
    params: list[object] = [fts_query]
    if document_role:
        query += " AND c.document_role = ?"
        params.append(document_role)
    if support_document_role:
        query += " AND c.support_document_role = ?"
        params.append(support_document_role)
    if authority_level:
        query += " AND c.authority_level = ?"
        params.append(authority_level)
    if source_record_ids:
        placeholders = ", ".join("?" for _ in source_record_ids)
        query += f" AND c.source_record_id IN ({placeholders})"
        params.extend(source_record_ids)
    if host:
        query += " AND c.host = ?"
        params.append(host)
    query += " ORDER BY bm25(chunks_fts), c.source_record_id, c.chunk_index LIMIT ?"
    params.append(limit)
    try:
        return list(connection.execute(query, params))
    except sqlite3.OperationalError:
        return []


def _fts_table_available(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'chunks_fts'"
    ).fetchone()
    return row is not None


def _fts_query(terms: list[str]) -> str:
    tokens = []
    for term in dict.fromkeys(terms):
        cleaned = re.sub(r"[^A-Za-z0-9_]", "", term)
        if cleaned:
            tokens.append(f"{cleaned}*")
    return " OR ".join(tokens)


def _normalized_filter_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
) -> list[str] | None:
    normalized = _display_filter_ids(
        source_record_id=source_record_id,
        source_record_ids=source_record_ids,
    )
    if not normalized:
        return None
    return aliased_source_record_ids(normalized) or None


def _display_filter_ids(
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
        "chunk_layer": _row_value(row, "chunk_layer", "baseline_text_chunk_v1"),
        "parent_chunk_id": _row_value(row, "parent_chunk_id"),
        "parent_window_id": _row_value(row, "parent_window_id"),
        "structure_type": _row_value(row, "structure_type", "text_span"),
        "component_type": _row_value(row, "component_type"),
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
            "page_range": _json_or_none(_row_value(row, "page_range_json")),
            "section": row["section"],
            "heading": row["heading"],
            "chunk_layer": _row_value(row, "chunk_layer", "baseline_text_chunk_v1"),
            "parent_chunk_id": _row_value(row, "parent_chunk_id"),
            "parent_window_id": _row_value(row, "parent_window_id"),
            "structure_type": _row_value(row, "structure_type", "text_span"),
            "component_type": _row_value(row, "component_type"),
            "contextual_index_sha256": _row_value(row, "contextual_index_sha256"),
            "content_sha256": row["content_sha256"],
        },
    }


def _row_value(row: sqlite3.Row, key: str, default: object | None = None) -> object | None:
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def _json_or_none(value: object | None) -> object | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _evidence_span(text: str, terms: list[str], source_chunk_start: int) -> dict:
    start = _best_evidence_span_start(text, terms=terms, span_length=480)
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


def _best_evidence_span_start(text: str, *, terms: list[str], span_length: int) -> int:
    if not text or span_length <= 0:
        return 0
    normalized_terms = [str(term or "").strip().lower() for term in dict.fromkeys(terms)]
    normalized_terms = [term for term in normalized_terms if term]
    if not normalized_terms:
        return 0
    lower = text.lower()
    matches: list[tuple[int, int, str]] = []
    for term in normalized_terms:
        start = 0
        while True:
            index = lower.find(term, start)
            if index < 0:
                break
            matches.append((index, index + len(term), term))
            start = index + 1
    if not matches:
        return 0
    matches.sort(key=lambda item: (item[0], item[1], item[2]))
    best_window: tuple[int, int] | None = None
    best_score = (-1, -1, span_length + 1)
    right = 0
    active_terms: dict[str, int] = {}
    for left, (left_start, _, _) in enumerate(matches):
        while right < len(matches) and matches[right][0] < left_start + span_length:
            right_start, _, right_term = matches[right]
            if right_start >= left_start:
                active_terms[right_term] = active_terms.get(right_term, 0) + 1
            right += 1
        window = matches[left:right]
        if window:
            coverage = len(active_terms)
            density = len(window)
            occupied = window[-1][1] - window[0][0]
            score = (coverage, density, -occupied)
            if score > best_score:
                best_score = score
                best_window = (window[0][0], window[-1][1])
        left_term = matches[left][2]
        next_count = active_terms.get(left_term, 0) - 1
        if next_count <= 0:
            active_terms.pop(left_term, None)
        else:
            active_terms[left_term] = next_count
    if best_window is None:
        return 0
    window_start, window_end = best_window
    if window_end - window_start >= span_length:
        return max(0, min(window_start, max(0, len(text) - span_length)))
    center = (window_start + window_end) // 2
    start = max(0, center - (span_length // 2))
    start = min(start, max(0, len(text) - span_length))
    if start + span_length < window_end:
        start = max(0, window_end - span_length)
    return start


def _score_row(
    row: sqlite3.Row,
    *,
    terms: list[str],
    phrases: list[str],
    query: str,
    topics: list[str],
    review_topic: str | None,
    term_weights: dict[str, float] | None = None,
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
    contextual_text = str(_row_value(row, "contextual_index_text") or "")
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
    score = 0.8 * _term_hit_fraction(terms, text=metadata_text, term_weights=term_weights)
    score += 0.55 * _term_hit_fraction(terms, text=text, term_weights=term_weights)
    score += 0.55 * _term_hit_fraction(terms, text=title, term_weights=term_weights)
    score += 0.2 * _term_hit_fraction(terms, text=heading, term_weights=term_weights)
    score += 0.2 * _term_hit_fraction(terms, text=topic_text, term_weights=term_weights)
    score += 0.15 * _term_hit_fraction(
        terms,
        text=" ".join([document_role, support_document_role, authority_level]),
        term_weights=term_weights,
    )
    score += 0.2 * _term_hit_fraction(terms, text=contextual_text, term_weights=term_weights)
    score += 0.65 * _term_cluster_score(terms, text=text)
    score += 0.35 * _term_cluster_score(terms, text=title)
    score += 0.2 * _term_cluster_score(terms, text=heading)
    score += 0.45 * _phrase_hit_fraction(phrases, text=text)
    score += 0.35 * _phrase_hit_fraction(phrases, text=title)
    score += 0.2 * _phrase_hit_fraction(phrases, text=heading)
    score += 0.15 * _phrase_hit_fraction(phrases, text=metadata_text)
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
    fts_bm25 = _row_value(row, "fts_bm25")
    if isinstance(fts_bm25, (float, int)):
        score += min(0.3, 1.0 / (1.0 + abs(float(fts_bm25))))
    return score


def _term_hit_fraction(
    terms: list[str],
    *,
    text: str,
    term_weights: dict[str, float] | None = None,
) -> float:
    if not terms:
        return 0.0
    token_set = set(_tokenize(text))
    weights = term_weights or {}
    matched_weight = 0.0
    total_weight = 0.0
    for term in terms:
        weight = weights.get(term, 1.0)
        total_weight += weight
        if _contains_term(term, token_set, text):
            matched_weight += weight
    if total_weight <= 0:
        return 0.0
    return matched_weight / total_weight


def _query_term_weights(terms: list[str], phrases: list[str]) -> dict[str, float]:
    if not terms:
        return {}
    phrase_term_counts: dict[str, int] = {}
    for phrase in phrases:
        for token in set(_tokenize(phrase)):
            phrase_term_counts[token] = phrase_term_counts.get(token, 0) + 1
    weights: dict[str, float] = {}
    for term in terms:
        length_bonus = min(0.8, max(len(term) - 5, 0) * 0.08)
        phrase_bonus = min(0.25, phrase_term_counts.get(term, 0) * 0.05)
        weights[term] = 1.0 + length_bonus + phrase_bonus
    return weights


def _term_cluster_score(terms: list[str], *, text: str) -> float:
    tokens = _tokenize(text)
    if len(tokens) < 2 or not terms:
        return 0.0
    normalized_terms = list(dict.fromkeys(terms))
    positions: list[tuple[int, str]] = []
    for index, token in enumerate(tokens):
        for term in normalized_terms:
            if _token_matches_term(token, term):
                positions.append((index, term))
    if not positions:
        return 0.0
    max_span = max(4, len(normalized_terms) + 4)
    best = 0.0
    left = 0
    term_counts: dict[str, int] = {}
    for right, (right_index, term) in enumerate(positions):
        term_counts[term] = term_counts.get(term, 0) + 1
        while left <= right and right_index - positions[left][0] + 1 > max_span:
            left_term = positions[left][1]
            next_count = term_counts[left_term] - 1
            if next_count <= 0:
                term_counts.pop(left_term, None)
            else:
                term_counts[left_term] = next_count
            left += 1
        span = max(1, right_index - positions[left][0] + 1)
        coverage = len(term_counts) / len(normalized_terms)
        density = len(term_counts) / span
        best = max(best, coverage * density * max_span)
    return min(best, 1.0)


def _token_matches_term(token: str, term: str) -> bool:
    return (
        token == term
        or token.startswith(term)
        or term.startswith(token)
        or _common_prefix_length(token, term) >= 5
    )


def _title_or_topic_has_compound_match(terms: list[str], text: str) -> bool:
    matched = [term for term in terms if term in text]
    return len(matched) >= 2


def _phrase_hit_fraction(phrases: list[str], *, text: str) -> float:
    if not phrases:
        return 0.0
    lower = text.lower()
    if not lower:
        return 0.0
    match_scores = [
        min(1.0, len(_tokenize(phrase)) / 4.0)
        for phrase in phrases
        if phrase in lower
    ]
    return max(match_scores, default=0.0)


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if term in token_set:
        return True
    lower = text.lower()
    if term in lower:
        return True
    return any(
        token.startswith(term)
        or term.startswith(token)
        or _common_prefix_length(token, term) >= 5
        for token in token_set
    )


def _common_prefix_length(left: str, right: str) -> int:
    size = 0
    for left_char, right_char in zip(left, right, strict=False):
        if left_char != right_char:
            break
        size += 1
    return size


def _query_phrases(query: str) -> list[str]:
    raw_tokens = [
        token.strip("'-.")
        for token in TOKEN_RE.findall(query.lower())
        if len(token.strip("'-.") or "") >= 2
    ]
    phrases: list[str] = []
    seen = set()
    max_size = min(4, len(raw_tokens))
    for size in range(max_size, 1, -1):
        for start in range(0, len(raw_tokens) - size + 1):
            tokens = raw_tokens[start : start + size]
            if not any(token not in STOPWORDS for token in tokens):
                continue
            phrase = " ".join(tokens).strip()
            if phrase and phrase not in seen:
                seen.add(phrase)
                phrases.append(phrase)
    return phrases


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
