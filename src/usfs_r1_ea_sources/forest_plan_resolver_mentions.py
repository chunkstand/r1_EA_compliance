from __future__ import annotations

from pathlib import Path

from .forest_plan_identity_reconciliation import aliased_region1_forest_plan_source_record_ids
from .forest_plan_resolver_location import _compiled_alias_pattern
from .forest_plan_resolver_location import _location_evidence_role
from .forest_plan_resolver_location import _term_found
from .forest_plan_resolver_models import GazetteerEntry
from .forest_plan_resolver_models import PlanEvidenceRoute
from .forest_plan_resolver_models import _safe_id
from .retrieval import query_retrieval_index

def _plan_source_evidence(*, entry: GazetteerEntry, index_path: Path, limit: int) -> list[dict]:
    if entry.source_record_id is None:
        return []
    query = " ".join(entry.terms)
    filtered = [
        row
        for row in _query_plan_source_record_aliases(
            index_path=index_path,
            query=query,
            limit=max(limit * 5, 25),
            source_record_id=entry.source_record_id,
            document_role="forest_plan",
        )
        if _evidence_text_matches_entry(str(row.get("evidence_span", {}).get("text") or ""), entry)
    ]
    if not filtered:
        filtered = [
            row
            for row in _query_plan_source_record_aliases(
                index_path=index_path,
                query="",
                limit=1000,
                source_record_id=entry.source_record_id,
                document_role="forest_plan",
            )
            if _evidence_text_matches_entry(str(row.get("evidence_span", {}).get("text") or ""), entry)
        ]
    return filtered[:limit]

def _supporting_plan_evidence(
    *,
    routes: tuple[PlanEvidenceRoute, ...],
    package_chunks: list[dict],
    index_path: Path | None,
    source_top_k: int,
) -> list[dict]:
    routed_evidence = []
    for route in routes:
        trigger_terms = route.trigger_terms or route.package_terms
        trigger_evidence = _mentions_for_terms(
            package_chunks=package_chunks,
            terms=trigger_terms,
            name=route.name,
            category=route.category,
            entry_id=route.route_id,
        )
        if not trigger_evidence:
            continue
        package_evidence = _mentions_for_route(package_chunks, route)
        if not package_evidence:
            continue
        plan_evidence = []
        if index_path is not None:
            plan_evidence = _supporting_source_evidence(
                route=route,
                index_path=index_path,
                limit=source_top_k,
            )
        routed_evidence.append(
            {
                "entry_id": route.route_id,
                "route_id": route.route_id,
                "category": route.category,
                "name": route.name,
                "source_record_id": route.source_record_id,
                "source_role": route.source_role,
                "package_terms": list(route.package_terms),
                "trigger_terms": list(trigger_terms),
                "trigger_evidence": trigger_evidence,
                "source_query": route.source_query,
                "source_terms": list(route.source_terms),
                "package_evidence": package_evidence,
                "plan_source_evidence": plan_evidence,
                "resolution_status": (
                    "resolved" if plan_evidence else "missing_plan_source_evidence"
                ),
            }
        )
    return sorted(routed_evidence, key=lambda item: item["route_id"])

def _supporting_source_evidence(
    *, route: PlanEvidenceRoute, index_path: Path, limit: int
) -> list[dict]:
    filtered = [
        row
        for row in _query_plan_source_record_aliases(
            index_path=index_path,
            query=route.source_query,
            limit=max(limit, 5),
            source_record_id=route.source_record_id,
        )
        if _supporting_evidence_matches_route(
            str(row.get("evidence_span", {}).get("text") or ""),
            route,
        )
    ]
    return filtered[:limit]


def _query_plan_source_record_aliases(
    *,
    index_path: Path,
    query: str,
    limit: int,
    source_record_id: str,
    document_role: str | None = None,
) -> list[dict]:
    results = []
    for aliased_source_record_id in aliased_region1_forest_plan_source_record_ids(
        source_record_id=source_record_id
    ):
        result = query_retrieval_index(
            index_path=index_path,
            query=query,
            limit=limit,
            document_role=document_role,
            source_record_id=aliased_source_record_id,
        )
        results.extend(result["results"])
    return _dedupe_retrieval_rows(results)


def _dedupe_retrieval_rows(rows: list[dict]) -> list[dict]:
    deduped_by_key: dict[tuple[object, ...], dict] = {}
    for row in rows:
        evidence_span = row.get("evidence_span") if isinstance(row.get("evidence_span"), dict) else {}
        key = (
            row.get("source_record_id"),
            row.get("chunk_id"),
            evidence_span.get("source_char_start"),
            evidence_span.get("source_char_end"),
            evidence_span.get("text"),
        )
        existing = deduped_by_key.get(key)
        if existing is None or float(row.get("score") or 0.0) > float(existing.get("score") or 0.0):
            deduped_by_key[key] = row
    return sorted(
        deduped_by_key.values(),
        key=lambda row: (
            -float(row.get("score") or 0.0),
            str(row.get("source_record_id") or ""),
            int(
                (
                    row.get("evidence_span")
                    if isinstance(row.get("evidence_span"), dict)
                    else {}
                ).get("source_char_start")
                or 0
            ),
        ),
    )

def _supporting_evidence_matches_route(text: str, route: PlanEvidenceRoute) -> bool:
    return any(_term_found(text, term) for term in route.source_terms)

def _evidence_text_matches_entry(text: str, entry: GazetteerEntry) -> bool:
    return any(_term_found(text, term) for term in entry.terms)

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
    return _dedupe_evidence(mentions)

def _mentions_for_route(package_chunks: list[dict], route: PlanEvidenceRoute) -> list[dict]:
    return _mentions_for_terms(
        package_chunks=package_chunks,
        terms=route.package_terms,
        name=route.name,
        category=route.category,
        entry_id=route.route_id,
    )

def _mentions_for_terms(
    *,
    package_chunks: list[dict],
    terms: tuple[str, ...],
    name: str,
    category: str,
    entry_id: str,
) -> list[dict]:
    mentions = []
    for alias in terms:
        mentions.extend(
            _mentions_for_alias(
                package_chunks,
                name=name,
                category=category,
                entry_id=entry_id,
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
    limit: int | None = 5,
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
    deduped = _dedupe_evidence(mentions)
    if limit is None:
        return deduped
    return deduped[:limit]

def _mentions_for_alias(
    package_chunks: list[dict],
    *,
    name: str,
    category: str,
    entry_id: str,
    alias: str,
) -> list[dict]:
    pattern, case_sensitive = _compiled_alias_pattern(alias)
    mentions = []
    for chunk in package_chunks:
        text = str(chunk.get("text") or "")
        search_text = text if case_sensitive else text.lower()
        for match in pattern.finditer(search_text):
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
    span_end = min(len(text), match_end + 900)
    span_text = text[span_start:span_end].strip()
    leading_trim = len(text[span_start:span_end]) - len(text[span_start:span_end].lstrip())
    trailing_trim = len(text[span_start:span_end].rstrip())
    chunk_span_start = span_start + leading_trim
    chunk_span_end = span_start + trailing_trim
    source_chunk_start = int(chunk.get("char_start") or 0)
    evidence = {
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
    evidence["evidence_role"] = _location_evidence_role(evidence)
    return evidence

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

def _evidence_id(category: str, name: str, alias: str) -> str:
    return f"{category}-{_safe_id(name)}-{_safe_id(alias)}"
