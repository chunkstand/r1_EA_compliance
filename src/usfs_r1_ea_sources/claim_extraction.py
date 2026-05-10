from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import sqlite3

from .extract import _source_derived_dir


CLAIM_SCHEMA_VERSION = "source-claims-v0"
CLAIM_GRAPH_SCHEMA_VERSION = "source-claim-graph-v0"
CLAIM_EXTRACTOR_NAME = "deterministic_legal_claim_patterns"
CLAIM_EXTRACTOR_VERSION = "0.1.0"
DEFAULT_CLAIM_EVAL_PATH = Path("config/claim_eval_seed.json")
DEFAULT_RETRIEVAL_INDEX_FILENAME = "evidence_index.sqlite"
SUPPORTED_CLAIM_TYPES = {
    "authorization",
    "condition",
    "definition",
    "exemption",
    "guidance",
    "obligation",
    "prohibition",
}
SUPPORTED_CLAIM_EVAL_FILTERS = {
    "authority_level",
    "citation_label",
    "claim_type",
    "document_role",
    "review_topic",
    "source_record_id",
    "topic",
}
REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "source_set_id",
    "source_record_id",
    "chunk_id",
    "claim_type",
    "claim_text",
    "citation_label",
    "authority_level",
    "document_role",
    "artifact_sha256",
    "artifact_path",
    "parser_name",
    "parser_version",
    "source_char_start",
    "source_char_end",
    "chunk_char_start",
    "chunk_char_end",
    "content_sha256",
    "chunk_content_sha256",
    "extractor_name",
    "extractor_version",
    "validation_status",
}


@dataclass(frozen=True)
class ClaimExtractionResult:
    source_set_id: str
    claims_dir: Path
    claims_path: Path
    entities_path: Path
    nodes_path: Path
    edges_path: Path
    sqlite_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class ClaimEvalResult:
    claims_path: Path
    eval_file: Path
    output_path: Path
    summary: dict


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

LEGAL_CITATION_RE = re.compile(
    r"\b\d+\s+(?:CFR|U\.S\.C\.|USC)\s*(?:part|section|sec\.)?\s*[\w.:-]*",
    re.I,
)
SECTION_RE = re.compile(r"(?:\u00a7|section|sec\.)\s*[\w.:-]+", re.I)
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9&]{2,}\b")
CAPITALIZED_PHRASE_RE = re.compile(
    r"\b[A-Z][a-z][A-Za-z&'-]*(?:\s+[A-Z][a-z][A-Za-z&'-]*){1,5}\b"
)
SENTENCE_RE = re.compile(r"[^.!?;]+(?:[.!?;]+|$)", re.S)


def build_claim_extraction(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    chunks_path: Path | None = None,
    catalog_sqlite_path: Path | None = None,
    allow_partial_retrieval: bool = False,
) -> ClaimExtractionResult:
    """Build deterministic source-text claim and entity artifacts from extracted chunks."""

    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    claims_dir = source_derived_dir / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_path or source_derived_dir / "chunks" / "chunks.jsonl"
    catalog_sqlite_path = catalog_sqlite_path or output_dir / "catalog" / "review_sources.sqlite"
    extraction_validation_path = source_derived_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = source_derived_dir / "diagnostics" / "summary.json"
    retrieval_validation_path = source_derived_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = source_derived_dir / "retrieval" / "summary.json"
    claims_path = claims_dir / "claims.jsonl"
    entities_path = claims_dir / "entities.jsonl"
    nodes_path = claims_dir / "claim_graph_nodes.jsonl"
    edges_path = claims_dir / "claim_graph_edges.jsonl"
    sqlite_path = claims_dir / "claim_graph.sqlite"
    validation_path = claims_dir / "claim_validation.json"
    summary_path = claims_dir / "summary.json"

    raw_chunks = _read_jsonl(chunks_path) if chunks_path.exists() else []
    review_topics_by_source = _load_review_topics(catalog_sqlite_path)
    chunks = [
        _chunk_with_review_topics(
            chunk,
            review_topics_by_source.get(str(chunk.get("source_record_id")), []),
        )
        for chunk in raw_chunks
    ]
    extraction_validation = (
        _read_json(extraction_validation_path) if extraction_validation_path.exists() else None
    )
    extraction_summary = (
        _read_json(extraction_summary_path) if extraction_summary_path.exists() else None
    )
    retrieval_validation = (
        _read_json(retrieval_validation_path) if retrieval_validation_path.exists() else None
    )
    retrieval_summary = (
        _read_json(retrieval_summary_path) if retrieval_summary_path.exists() else None
    )
    retrieval_index_path = _retrieval_index_path(source_derived_dir, retrieval_summary)
    retrieval_index_records, retrieval_index_error = _load_retrieval_index_records(
        retrieval_index_path
    )

    claims = _extract_claims(chunks=chunks, source_set_id=source_set_id)
    entities = _entity_records(claims)
    nodes, edges = _claim_graph_records(
        source_set_id=source_set_id,
        claims=claims,
        entities=entities,
    )
    metrics = _claim_metrics(claims=claims, entities=entities, nodes=nodes, edges=edges)

    _write_jsonl(claims_path, claims)
    _write_jsonl(entities_path, entities)
    _write_jsonl(nodes_path, nodes)
    _write_jsonl(edges_path, edges)

    validation = validate_claim_outputs(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_path=claims_path,
        entities_path=entities_path,
        nodes_path=nodes_path,
        edges_path=edges_path,
        chunks_path=chunks_path,
        extraction_validation_path=extraction_validation_path,
        extraction_validation=extraction_validation,
        extraction_summary_path=extraction_summary_path,
        extraction_summary=extraction_summary,
        retrieval_validation_path=retrieval_validation_path,
        retrieval_validation=retrieval_validation,
        retrieval_summary_path=retrieval_summary_path,
        retrieval_summary=retrieval_summary,
        retrieval_index_path=retrieval_index_path,
        retrieval_index_records=retrieval_index_records,
        retrieval_index_error=retrieval_index_error,
        chunks=chunks,
        claims=claims,
        entities=entities,
        nodes=nodes,
        edges=edges,
        metrics=metrics,
        allow_partial_retrieval=allow_partial_retrieval,
    )
    if validation["passed"]:
        _write_sqlite_graph(
            sqlite_path,
            source_set_id=source_set_id,
            claims=claims,
            entities=entities,
            nodes=nodes,
            edges=edges,
            metrics=metrics,
        )
        validation = _with_additional_checks(
            validation,
            _sqlite_graph_checks(
                sqlite_path,
                expected_claim_count=len(claims),
                expected_entity_count=len(entities),
                expected_node_count=len(nodes),
                expected_edge_count=len(edges),
            ),
            allow_partial_retrieval=allow_partial_retrieval,
        )
        if not validation["passed"]:
            sqlite_path.unlink(missing_ok=True)
    else:
        sqlite_path.unlink(missing_ok=True)

    retrieval_reviewer_ready = bool(retrieval_summary and retrieval_summary.get("reviewer_ready"))
    reviewer_ready = (
        validation["passed"]
        and retrieval_reviewer_ready
        and _extraction_summary_is_complete(extraction_summary)
        and bool(claims)
    )
    summary = {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "graph_schema_version": CLAIM_GRAPH_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "claims_dir": str(claims_dir),
        "claims_path": str(claims_path),
        "entities_path": str(entities_path),
        "nodes_path": str(nodes_path),
        "edges_path": str(edges_path),
        "sqlite_path": str(sqlite_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "chunks_path": str(chunks_path),
        "catalog_sqlite_path": str(catalog_sqlite_path),
        "retrieval_summary_path": str(retrieval_summary_path),
        "retrieval_validation_path": str(retrieval_validation_path),
        "retrieval_index_path": str(retrieval_index_path),
        "allow_partial_retrieval": allow_partial_retrieval,
        "extractor_name": CLAIM_EXTRACTOR_NAME,
        "extractor_version": CLAIM_EXTRACTOR_VERSION,
        "validation_passed": validation["passed"],
        "reviewer_ready": reviewer_ready,
        "retrieval_reviewer_ready": retrieval_reviewer_ready,
        "extraction_complete": _extraction_summary_is_complete(extraction_summary),
        "chunk_count": len(chunks),
        "claim_count": len(claims),
        "entity_count": len(entities),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "claim_type_counts": dict(Counter(claim["claim_type"] for claim in claims)),
        "authority_level_counts": dict(Counter(claim["authority_level"] for claim in claims)),
        "document_role_counts": dict(Counter(claim["document_role"] for claim in claims)),
        "source_record_count": len({claim["source_record_id"] for claim in claims}),
        "retrieval_index_chunk_count": len(retrieval_index_records),
        "retrieval_binding_mismatch_count": _check_detail_count(
            validation,
            "claims_match_retrieval_index",
            "mismatch_count",
        ),
        "claim_offset_mismatch_count": _check_detail_count(
            validation,
            "claim_offsets_match_chunk_text",
            "mismatch_count",
        ),
        "metrics": metrics,
    }
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
    return ClaimExtractionResult(
        source_set_id=source_set_id,
        claims_dir=claims_dir,
        claims_path=claims_path,
        entities_path=entities_path,
        nodes_path=nodes_path,
        edges_path=edges_path,
        sqlite_path=sqlite_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
    )


def run_claim_eval(
    *,
    claims_path: Path,
    eval_file: Path,
    top_k: int = 5,
    output_dir: Path | None = None,
) -> ClaimEvalResult:
    """Run deterministic eval cases against extracted source claims."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    claims_path = Path(claims_path)
    eval_file = Path(eval_file)
    claims = _load_validated_claims_for_eval(claims_path)
    cases = _load_eval_cases(eval_file)
    output_dir = output_dir or claims_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "claim_eval_results.json"

    case_results = []
    for case in cases:
        filters = dict(case.get("filters") or {})
        expected_sources = [str(value) for value in case.get("expected_source_record_ids", [])]
        expected_terms = [str(value) for value in case.get("expected_terms", [])]
        expected_claim_types = [
            str(value)
            for value in case.get(
                "expected_claim_types",
                [case["expected_claim_type"]] if case.get("expected_claim_type") else [],
            )
        ]
        min_claims = int(case.get("min_claims", 1))
        hits = _query_claims(
            claims,
            query=str(case.get("query") or ""),
            filters=filters,
            limit=int(case.get("top_k") or top_k),
        )
        source_hit = not expected_sources or any(
            hit["source_record_id"] in expected_sources for hit in hits
        )
        type_hit = not expected_claim_types or any(
            hit["claim_type"] in expected_claim_types for hit in hits
        )
        term_hit = not expected_terms or _expected_terms_found(expected_terms, hits)
        min_claims_met = len(hits) >= min_claims
        provenance_supported = bool(hits) and any(_claim_has_required_provenance(hit) for hit in hits)
        passed = min_claims_met and source_hit and type_hit and term_hit and provenance_supported
        case_results.append(
            {
                "id": case["id"],
                "query": case.get("query") or "",
                "filters": filters,
                "expected_source_record_ids": expected_sources,
                "expected_claim_types": expected_claim_types,
                "expected_terms": expected_terms,
                "top_k": int(case.get("top_k") or top_k),
                "hit_count": len(hits),
                "top_claim_ids": [hit["claim_id"] for hit in hits],
                "top_source_record_ids": [hit["source_record_id"] for hit in hits],
                "source_hit": source_hit,
                "type_hit": type_hit,
                "term_hit": term_hit,
                "min_claims_met": min_claims_met,
                "provenance_supported": provenance_supported,
                "failure_reasons": _eval_failure_reasons(
                    min_claims_met=min_claims_met,
                    source_hit=source_hit,
                    type_hit=type_hit,
                    term_hit=term_hit,
                    provenance_supported=provenance_supported,
                ),
                "passed": passed,
                "top_results": hits,
            }
        )

    case_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    source_hit_count = sum(1 for case in case_results if case["source_hit"])
    type_hit_count = sum(1 for case in case_results if case["type_hit"])
    term_hit_count = sum(1 for case in case_results if case["term_hit"])
    provenance_supported_count = sum(
        1 for case in case_results if case["provenance_supported"]
    )
    zero_result_count = sum(1 for case in case_results if case["hit_count"] == 0)
    summary = {
        "claims_path": str(claims_path),
        "eval_file": str(eval_file),
        "created_at": _utc_now(),
        "top_k": top_k,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": case_count - passed_count,
        "passed": passed_count == case_count,
        "metrics": {
            "pass_rate": _rate(passed_count, case_count),
            "source_hit_rate": _rate(source_hit_count, case_count),
            "claim_type_hit_rate": _rate(type_hit_count, case_count),
            "expected_term_hit_rate": _rate(term_hit_count, case_count),
            "citation_coverage_rate": _rate(provenance_supported_count, case_count),
            "zero_result_rate": _rate(zero_result_count, case_count),
        },
        "cases": case_results,
    }
    _write_json(output_path, summary)
    return ClaimEvalResult(
        claims_path=claims_path,
        eval_file=eval_file,
        output_path=output_path,
        summary=summary,
    )


def default_claims_path(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    return _source_derived_dir(output_dir / "derived", source_set_id) / "claims" / "claims.jsonl"


def validate_claim_outputs(
    *,
    output_dir: Path,
    source_set_id: str,
    claims_path: Path,
    entities_path: Path,
    nodes_path: Path,
    edges_path: Path,
    chunks_path: Path,
    extraction_validation_path: Path | None = None,
    extraction_validation: dict | None = None,
    extraction_summary_path: Path | None = None,
    extraction_summary: dict | None = None,
    retrieval_validation_path: Path | None = None,
    retrieval_validation: dict | None = None,
    retrieval_summary_path: Path | None = None,
    retrieval_summary: dict | None = None,
    retrieval_index_path: Path | None = None,
    retrieval_index_records: dict[str, dict] | None = None,
    retrieval_index_error: str | None = None,
    chunks: list[dict] | None = None,
    claims: list[dict] | None = None,
    entities: list[dict] | None = None,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    metrics: dict | None = None,
    allow_partial_retrieval: bool = False,
) -> dict:
    output_dir = Path(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    extraction_validation_path = (
        extraction_validation_path
        or source_derived_dir / "diagnostics" / "extraction_validation.json"
    )
    extraction_summary_path = (
        extraction_summary_path or source_derived_dir / "diagnostics" / "summary.json"
    )
    retrieval_validation_path = (
        retrieval_validation_path or source_derived_dir / "retrieval" / "retrieval_validation.json"
    )
    retrieval_summary_path = retrieval_summary_path or source_derived_dir / "retrieval" / "summary.json"
    if extraction_validation is None and extraction_validation_path.exists():
        extraction_validation = _read_json(extraction_validation_path)
    if extraction_summary is None and extraction_summary_path.exists():
        extraction_summary = _read_json(extraction_summary_path)
    if retrieval_validation is None and retrieval_validation_path.exists():
        retrieval_validation = _read_json(retrieval_validation_path)
    if retrieval_summary is None and retrieval_summary_path.exists():
        retrieval_summary = _read_json(retrieval_summary_path)
    retrieval_index_path = retrieval_index_path or _retrieval_index_path(
        source_derived_dir,
        retrieval_summary,
    )
    if retrieval_index_records is None:
        retrieval_index_records, retrieval_index_error = _load_retrieval_index_records(
            retrieval_index_path
        )
    chunks = chunks if chunks is not None else (_read_jsonl(chunks_path) if chunks_path.exists() else [])
    claims = claims if claims is not None else (_read_jsonl(claims_path) if claims_path.exists() else [])
    entities = (
        entities if entities is not None else (_read_jsonl(entities_path) if entities_path.exists() else [])
    )
    nodes = nodes if nodes is not None else (_read_jsonl(nodes_path) if nodes_path.exists() else [])
    edges = edges if edges is not None else (_read_jsonl(edges_path) if edges_path.exists() else [])
    metrics = metrics or _claim_metrics(claims=claims, entities=entities, nodes=nodes, edges=edges)

    checks = [
        {
            "name": "extraction_validation_passed",
            "passed": bool(extraction_validation and extraction_validation.get("passed")),
            "details": {
                "path": str(extraction_validation_path),
                "exists": extraction_validation_path.exists(),
                "passed": bool(extraction_validation and extraction_validation.get("passed")),
            },
        },
        {
            "name": "extraction_scope_is_complete",
            "passed": _extraction_summary_is_complete(extraction_summary)
            or allow_partial_retrieval,
            "details": {
                "path": str(extraction_summary_path),
                "exists": extraction_summary_path.exists(),
                "allow_partial_retrieval": allow_partial_retrieval,
                "complete": _extraction_summary_is_complete(extraction_summary),
                "catalog_source_count": _int_from_summary(
                    extraction_summary,
                    "catalog_source_count",
                ),
                "selected_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_source_count",
                ),
                "required_extraction_source_count": _int_from_summary(
                    extraction_summary,
                    "required_extraction_source_count",
                ),
                "selected_required_extraction_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_required_extraction_source_count",
                ),
                "extracted_count": _int_from_summary(extraction_summary, "extracted_count"),
                "failed_count": _int_from_summary(extraction_summary, "failed_count"),
                "skipped_excluded_count": _int_from_summary(
                    extraction_summary,
                    "skipped_excluded_count",
                ),
                "filters": (extraction_summary or {}).get("filters", {}),
            },
        },
        {
            "name": "retrieval_validation_passed",
            "passed": bool(retrieval_validation and retrieval_validation.get("passed")),
            "details": {
                "path": str(retrieval_validation_path),
                "exists": retrieval_validation_path.exists(),
                "passed": bool(retrieval_validation and retrieval_validation.get("passed")),
            },
        },
        {
            "name": "retrieval_is_reviewer_ready",
            "passed": bool(retrieval_summary and retrieval_summary.get("reviewer_ready"))
            or allow_partial_retrieval,
            "details": {
                "path": str(retrieval_summary_path),
                "exists": retrieval_summary_path.exists(),
                "allow_partial_retrieval": allow_partial_retrieval,
                "reviewer_ready": bool(
                    retrieval_summary and retrieval_summary.get("reviewer_ready")
                ),
            },
        },
        _check_retrieval_index_readable(
            retrieval_index_path,
            retrieval_index_records,
            retrieval_index_error,
        ),
        {
            "name": "claims_jsonl_exists",
            "passed": claims_path.exists(),
            "details": {"path": str(claims_path)},
        },
        {
            "name": "entities_jsonl_exists",
            "passed": entities_path.exists(),
            "details": {"path": str(entities_path)},
        },
        {
            "name": "claim_graph_jsonl_exists",
            "passed": nodes_path.exists() and edges_path.exists(),
            "details": {"nodes_path": str(nodes_path), "edges_path": str(edges_path)},
        },
        _check_claims_loaded(claims),
        _check_unique_ids(claims, key="claim_id", check_name="claim_ids_are_unique"),
        _check_unique_ids(entities, key="entity_id", check_name="entity_ids_are_unique"),
        _check_required_claim_fields(claims),
        _check_claim_types_supported(claims),
        _check_claim_source_set_ids_match(source_set_id, claims),
        _check_claim_chunk_ids_resolve(chunks, claims),
        _check_claim_offsets_match_chunk_text(chunks, claims),
        _check_claim_offsets_match_source_text(output_dir, chunks, claims),
        _check_claim_content_hashes(claims),
        _check_claims_match_retrieval_index(
            chunks,
            claims,
            retrieval_index_records,
            retrieval_index_error,
        ),
        _check_no_unsupported_claims(claims),
        _check_entities_resolve_to_claims(claims, entities),
        _check_graph_integrity(claims, entities, nodes, edges),
        _check_graph_health(metrics),
    ]
    strict_blockers = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    passed = all(check["passed"] for check in checks)
    if allow_partial_retrieval:
        passed = all(
            check["passed"] or check["name"] in strict_blockers
            for check in checks
        )
    return {
        "source_set_id": source_set_id,
        "passed": passed,
        "checks": checks,
        "metrics": metrics,
    }


def _extract_claims(*, chunks: list[dict], source_set_id: str) -> list[dict]:
    claims_by_key: dict[tuple[str, int, int, str, str], dict] = {}
    extracted_at = _utc_now()
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        for sentence_start, sentence_end, sentence_text in _sentence_spans(text):
            match = _match_claim_pattern(sentence_text)
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


def _match_claim_pattern(sentence: str) -> tuple[ClaimPattern, re.Match[str]] | None:
    for pattern in CLAIM_PATTERNS:
        match = pattern.regex.search(sentence)
        if match:
            return pattern, match
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


def _entity_records(claims: list[dict]) -> list[dict]:
    entities: dict[str, dict] = {}
    mention_claims: defaultdict[str, set[str]] = defaultdict(set)
    mention_sources: defaultdict[str, set[str]] = defaultdict(set)
    mention_citations: defaultdict[str, set[str]] = defaultdict(set)
    mention_counts: Counter[str] = Counter()
    for claim in claims:
        for entity_type, label in _extract_entities(str(claim["claim_text"])):
            entity_id = _entity_id(entity_type, label)
            entities.setdefault(
                entity_id,
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "label": label,
                    "normalized_label": _normalize_entity_label(label),
                },
            )
            mention_claims[entity_id].add(str(claim["claim_id"]))
            mention_sources[entity_id].add(str(claim["source_record_id"]))
            if claim.get("citation_label"):
                mention_citations[entity_id].add(str(claim["citation_label"]))
            mention_counts[entity_id] += 1
    records = []
    for entity_id, entity in entities.items():
        records.append(
            {
                **entity,
                "source_set_id": claims[0]["source_set_id"] if claims else None,
                "claim_ids": sorted(mention_claims[entity_id]),
                "source_record_ids": sorted(mention_sources[entity_id]),
                "citation_labels": sorted(mention_citations[entity_id]),
                "mention_count": mention_counts[entity_id],
                "extractor_name": CLAIM_EXTRACTOR_NAME,
                "extractor_version": CLAIM_EXTRACTOR_VERSION,
            }
        )
    return sorted(records, key=lambda entity: (entity["entity_type"], entity["label"]))


def _extract_entities(text: str) -> list[tuple[str, str]]:
    entities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entity_type, regex in (
        ("legal_citation", LEGAL_CITATION_RE),
        ("section_reference", SECTION_RE),
        ("acronym", ACRONYM_RE),
        ("named_actor", CAPITALIZED_PHRASE_RE),
    ):
        for match in regex.finditer(text):
            label = match.group(0).strip(" ,.;:()[]{}\"'")
            if len(label) < 2:
                continue
            key = (entity_type, _normalize_entity_label(label))
            if key in seen:
                continue
            seen.add(key)
            entities.append((entity_type, label))
    return entities


def _claim_graph_records(
    *,
    source_set_id: str,
    claims: list[dict],
    entities: list[dict],
) -> tuple[list[dict], list[dict]]:
    nodes_by_id: dict[str, dict] = {}
    edges_by_id: dict[str, dict] = {}
    source_set_node_id = f"source_set:{source_set_id}"
    nodes_by_id[source_set_node_id] = _node(
        source_set_node_id,
        "SourceSet",
        source_set_id=source_set_id,
    )
    entities_by_id = {entity["entity_id"]: entity for entity in entities}
    entity_ids_by_claim: defaultdict[str, list[str]] = defaultdict(list)
    for entity in entities:
        for claim_id in entity.get("claim_ids", []):
            entity_ids_by_claim[str(claim_id)].append(str(entity["entity_id"]))
            nodes_by_id.setdefault(
                str(entity["entity_id"]),
                _node(
                    str(entity["entity_id"]),
                    "Entity",
                    entity_type=entity["entity_type"],
                    label=entity["label"],
                    normalized_label=entity["normalized_label"],
                    mention_count=entity["mention_count"],
                ),
            )

    for claim in claims:
        source_node_id = f"source:{claim['source_record_id']}"
        chunk_node_id = str(claim["chunk_id"])
        claim_node_id = str(claim["claim_id"])
        authority_node_id = _authority_node_id(str(claim["authority_level"]))
        evidence_node_id = _claim_evidence_span_node_id(claim)
        nodes_by_id.setdefault(
            source_node_id,
            _node(
                source_node_id,
                "SourceDocument",
                source_set_id=source_set_id,
                source_record_id=claim["source_record_id"],
                title=claim.get("title"),
                document_role=claim.get("document_role"),
                authority_level=claim.get("authority_level"),
                citation_label=claim.get("citation_label"),
            ),
        )
        nodes_by_id.setdefault(
            chunk_node_id,
            _node(
                chunk_node_id,
                "DocumentChunk",
                chunk_id=chunk_node_id,
                source_record_id=claim["source_record_id"],
                chunk_index=claim.get("chunk_index"),
                chunk_content_sha256=claim.get("chunk_content_sha256"),
            ),
        )
        nodes_by_id.setdefault(
            authority_node_id,
            _node(
                authority_node_id,
                "Authority",
                authority_level=claim["authority_level"],
            ),
        )
        nodes_by_id[claim_node_id] = _node(
            claim_node_id,
            "Claim",
            claim_id=claim_node_id,
            source_record_id=claim["source_record_id"],
            chunk_id=chunk_node_id,
            claim_type=claim["claim_type"],
            claim_text=claim["claim_text"],
            citation_label=claim["citation_label"],
            source_char_start=claim["source_char_start"],
            source_char_end=claim["source_char_end"],
            content_sha256=claim["content_sha256"],
            extractor_version=claim["extractor_version"],
            validation_status=claim["validation_status"],
        )
        nodes_by_id[evidence_node_id] = _node(
            evidence_node_id,
            "ClaimEvidenceSpan",
            claim_id=claim_node_id,
            chunk_id=chunk_node_id,
            source_record_id=claim["source_record_id"],
            citation_label=claim["citation_label"],
            text=claim["claim_text"],
            chunk_char_start=claim["chunk_char_start"],
            chunk_char_end=claim["chunk_char_end"],
            source_char_start=claim["source_char_start"],
            source_char_end=claim["source_char_end"],
            content_sha256=claim["content_sha256"],
        )
        _put_edge(edges_by_id, source_set_node_id, source_node_id, "SOURCE_SET_HAS_SOURCE")
        _put_edge(edges_by_id, source_node_id, chunk_node_id, "SOURCE_HAS_CHUNK")
        _put_edge(edges_by_id, chunk_node_id, claim_node_id, "CHUNK_HAS_CLAIM")
        _put_edge(edges_by_id, claim_node_id, evidence_node_id, "CLAIM_HAS_EVIDENCE_SPAN")
        _put_edge(edges_by_id, evidence_node_id, chunk_node_id, "CLAIM_EVIDENCE_FROM_CHUNK")
        _put_edge(edges_by_id, claim_node_id, authority_node_id, "CLAIM_HAS_AUTHORITY")
        _put_edge(edges_by_id, source_node_id, authority_node_id, "SOURCE_HAS_AUTHORITY")
        for topic in claim.get("review_topics", []):
            topic_node_id = _topic_node_id(str(topic))
            nodes_by_id.setdefault(
                topic_node_id,
                _node(topic_node_id, "ReviewTopic", label=str(topic)),
            )
            _put_edge(edges_by_id, claim_node_id, topic_node_id, "CLAIM_SUPPORTS_REVIEW_TOPIC")
        for entity_id in entity_ids_by_claim.get(claim_node_id, []):
            if entity_id in entities_by_id:
                _put_edge(edges_by_id, claim_node_id, entity_id, "CLAIM_MENTIONS_ENTITY")
    return list(nodes_by_id.values()), list(edges_by_id.values())


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


def _check_retrieval_index_readable(
    index_path: Path,
    retrieval_index_records: dict[str, dict] | None,
    retrieval_index_error: str | None,
) -> dict:
    records = retrieval_index_records or {}
    return {
        "name": "retrieval_index_exists_and_readable",
        "passed": retrieval_index_error is None and bool(records),
        "details": {
            "path": str(index_path),
            "exists": index_path.exists(),
            "error": retrieval_index_error,
            "chunk_count": len(records),
        },
    }


def _check_claims_loaded(claims: list[dict]) -> dict:
    return {
        "name": "claims_loaded",
        "passed": bool(claims),
        "details": {"claim_count": len(claims)},
    }


def _check_unique_ids(records: list[dict], *, key: str, check_name: str) -> dict:
    counts = Counter(record.get(key) for record in records)
    duplicates = sorted(record_id for record_id, count in counts.items() if record_id and count > 1)
    return {
        "name": check_name,
        "passed": not duplicates,
        "details": {"duplicate_ids": duplicates[:50], "duplicate_count": len(duplicates)},
    }


def _check_required_claim_fields(claims: list[dict]) -> dict:
    failures = []
    for claim in claims:
        missing = [
            field for field in sorted(REQUIRED_CLAIM_FIELDS) if claim.get(field) in (None, "")
        ]
        if missing:
            failures.append({"claim_id": claim.get("claim_id"), "missing_fields": missing})
    return {
        "name": "claims_have_required_provenance",
        "passed": not failures and bool(claims),
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_claim_types_supported(claims: list[dict]) -> dict:
    failures = [
        {"claim_id": claim.get("claim_id"), "claim_type": claim.get("claim_type")}
        for claim in claims
        if claim.get("claim_type") not in SUPPORTED_CLAIM_TYPES
    ]
    return {
        "name": "claim_types_are_supported",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_claim_source_set_ids_match(source_set_id: str, claims: list[dict]) -> dict:
    mismatches = [
        {
            "claim_id": claim.get("claim_id"),
            "expected_source_set_id": source_set_id,
            "actual_source_set_id": claim.get("source_set_id"),
        }
        for claim in claims
        if claim.get("source_set_id") != source_set_id
    ]
    return {
        "name": "claim_source_set_ids_match",
        "passed": not mismatches and bool(claims),
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_claim_chunk_ids_resolve(chunks: list[dict], claims: list[dict]) -> dict:
    chunk_ids = {str(chunk.get("chunk_id")) for chunk in chunks if chunk.get("chunk_id")}
    missing = [
        {"claim_id": claim.get("claim_id"), "chunk_id": claim.get("chunk_id")}
        for claim in claims
        if str(claim.get("chunk_id")) not in chunk_ids
    ]
    return {
        "name": "claim_chunk_ids_resolve",
        "passed": bool(chunks) and not missing,
        "details": {"missing": missing[:50], "missing_count": len(missing)},
    }


def _check_claim_offsets_match_chunk_text(chunks: list[dict], claims: list[dict]) -> dict:
    chunks_by_id = {str(chunk.get("chunk_id")): chunk for chunk in chunks if chunk.get("chunk_id")}
    mismatches = []
    for claim in claims:
        chunk = chunks_by_id.get(str(claim.get("chunk_id")))
        if not chunk:
            continue
        try:
            start = int(claim["chunk_char_start"])
            end = int(claim["chunk_char_end"])
        except (KeyError, TypeError, ValueError):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "invalid_offsets"})
            continue
        text = str(chunk.get("text") or "")
        if start < 0 or end <= start or end > len(text):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "offset_out_of_range"})
            continue
        if text[start:end] != claim.get("claim_text"):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "text_mismatch"})
    return {
        "name": "claim_offsets_match_chunk_text",
        "passed": bool(claims) and not mismatches,
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_claim_offsets_match_source_text(
    output_dir: Path,
    chunks: list[dict],
    claims: list[dict],
) -> dict:
    chunks_by_id = {str(chunk.get("chunk_id")): chunk for chunk in chunks if chunk.get("chunk_id")}
    text_cache: dict[str, str | None] = {}
    mismatches = []
    for claim in claims:
        chunk = chunks_by_id.get(str(claim.get("chunk_id")))
        if not chunk:
            continue
        path_value = claim.get("source_text_path") or chunk.get("source_text_path")
        if not path_value:
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "missing_text_path"})
            continue
        path_key = str(path_value)
        if path_key not in text_cache:
            path = _resolve_path(output_dir, path_key)
            text_cache[path_key] = path.read_text(encoding="utf-8") if path.exists() else None
        source_text = text_cache[path_key]
        if source_text is None:
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "missing_text_file"})
            continue
        try:
            start = int(claim["source_char_start"])
            end = int(claim["source_char_end"])
        except (KeyError, TypeError, ValueError):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "invalid_offsets"})
            continue
        if start < 0 or end <= start or end > len(source_text):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "offset_out_of_range"})
            continue
        if source_text[start:end] != claim.get("claim_text"):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "text_mismatch"})
    return {
        "name": "claim_offsets_match_source_text",
        "passed": bool(claims) and not mismatches,
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_claim_content_hashes(claims: list[dict]) -> dict:
    failures = [
        claim.get("claim_id")
        for claim in claims
        if claim.get("content_sha256") != _text_sha256(str(claim.get("claim_text") or ""))
    ]
    return {
        "name": "claim_content_hashes_match_text",
        "passed": bool(claims) and not failures,
        "details": {"claim_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_claims_match_retrieval_index(
    chunks: list[dict],
    claims: list[dict],
    retrieval_index_records: dict[str, dict] | None,
    retrieval_index_error: str | None,
) -> dict:
    index_records = retrieval_index_records or {}
    chunks_by_id = {str(chunk.get("chunk_id")): chunk for chunk in chunks if chunk.get("chunk_id")}
    mismatches = []
    for claim in claims:
        chunk_id = str(claim.get("chunk_id") or "")
        chunk = chunks_by_id.get(chunk_id)
        index_record = index_records.get(chunk_id)
        if not index_record:
            mismatches.append(
                {"claim_id": claim.get("claim_id"), "chunk_id": chunk_id, "reason": "missing_index"}
            )
            continue
        for field in (
            "source_set_id",
            "source_record_id",
            "artifact_sha256",
            "artifact_path",
            "citation_label",
            "parser_name",
            "parser_version",
            "content_sha256",
        ):
            expected = str((chunk or claim).get(field) or "")
            actual = str(index_record.get(field) or "")
            if expected != actual:
                mismatches.append(
                    {
                        "claim_id": claim.get("claim_id"),
                        "chunk_id": chunk_id,
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                    }
                )
    return {
        "name": "claims_match_retrieval_index",
        "passed": retrieval_index_error is None and bool(claims) and not mismatches,
        "details": {
            "retrieval_index_error": retrieval_index_error,
            "mismatches": mismatches[:50],
            "mismatch_count": len(mismatches),
        },
    }


def _check_no_unsupported_claims(claims: list[dict]) -> dict:
    failures = []
    for claim in claims:
        if claim.get("validation_status") != "valid":
            failures.append({"claim_id": claim.get("claim_id"), "reason": "invalid_status"})
        if not claim.get("citation_label"):
            failures.append({"claim_id": claim.get("claim_id"), "reason": "missing_citation"})
        if claim.get("claim_type") not in SUPPORTED_CLAIM_TYPES:
            failures.append({"claim_id": claim.get("claim_id"), "reason": "unsupported_type"})
        if not any(pattern.pattern_id == claim.get("pattern_id") for pattern in CLAIM_PATTERNS):
            failures.append({"claim_id": claim.get("claim_id"), "reason": "unknown_pattern"})
    return {
        "name": "no_unsupported_claims_emitted",
        "passed": bool(claims) and not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_entities_resolve_to_claims(claims: list[dict], entities: list[dict]) -> dict:
    claim_ids = {str(claim["claim_id"]) for claim in claims}
    failures = []
    for entity in entities:
        entity_claim_ids = [str(claim_id) for claim_id in entity.get("claim_ids", [])]
        missing = sorted(set(entity_claim_ids) - claim_ids)
        if missing or not entity_claim_ids:
            failures.append({"entity_id": entity.get("entity_id"), "missing_claim_ids": missing})
    return {
        "name": "entities_resolve_to_claims",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_graph_integrity(
    claims: list[dict],
    entities: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_ids = {node.get("id") for node in nodes}
    edge_ids = [edge.get("id") for edge in edges]
    duplicate_edges = sorted(edge_id for edge_id, count in Counter(edge_ids).items() if count > 1)
    dangling = [
        edge.get("id")
        for edge in edges
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids
    ]
    claim_node_ids = {node.get("id") for node in nodes if node.get("type") == "Claim"}
    entity_node_ids = {node.get("id") for node in nodes if node.get("type") == "Entity"}
    missing_claim_nodes = sorted({claim["claim_id"] for claim in claims} - claim_node_ids)
    missing_entity_nodes = sorted({entity["entity_id"] for entity in entities} - entity_node_ids)
    failures = []
    if duplicate_edges:
        failures.append({"reason": "duplicate_edges", "ids": duplicate_edges[:50]})
    if dangling:
        failures.append({"reason": "dangling_edges", "ids": dangling[:50]})
    if missing_claim_nodes:
        failures.append({"reason": "missing_claim_nodes", "ids": missing_claim_nodes[:50]})
    if missing_entity_nodes:
        failures.append({"reason": "missing_entity_nodes", "ids": missing_entity_nodes[:50]})
    return {
        "name": "claim_graph_node_edge_integrity",
        "passed": bool(nodes) and bool(edges) and not failures,
        "details": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "failures": failures,
        },
    }


def _check_graph_health(metrics: dict) -> dict:
    passed = (
        metrics["claim_count"] > 0
        and metrics["claim_node_count"] == metrics["claim_count"]
        and metrics["dangling_edge_count"] == 0
        and metrics["claim_evidence_coverage_rate"] == 1.0
        and metrics["claim_authority_coverage_rate"] == 1.0
        and metrics["claim_topic_coverage_rate"] == 1.0
    )
    return {
        "name": "claim_graph_health_metrics_pass",
        "passed": passed,
        "details": metrics,
    }


def _write_sqlite_graph(
    path: Path,
    *,
    source_set_id: str,
    claims: list[dict],
    entities: list[dict],
    nodes: list[dict],
    edges: list[dict],
    metrics: dict,
) -> None:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL
            );

            CREATE TABLE claims (
              claim_id TEXT PRIMARY KEY,
              source_set_id TEXT NOT NULL,
              source_record_id TEXT NOT NULL,
              chunk_id TEXT NOT NULL,
              claim_type TEXT NOT NULL,
              citation_label TEXT NOT NULL,
              source_char_start INTEGER NOT NULL,
              source_char_end INTEGER NOT NULL,
              content_sha256 TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE entities (
              entity_id TEXT PRIMARY KEY,
              entity_type TEXT NOT NULL,
              label TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE graph_nodes (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE graph_edges (
              id TEXT PRIMARY KEY,
              source TEXT NOT NULL,
              target TEXT NOT NULL,
              relationship TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE INDEX idx_claims_source_record_id ON claims(source_record_id);
            CREATE INDEX idx_claims_chunk_id ON claims(chunk_id);
            CREATE INDEX idx_claims_claim_type ON claims(claim_type);
            CREATE INDEX idx_entities_entity_type ON entities(entity_type);
            CREATE INDEX idx_claim_graph_edges_source ON graph_edges(source);
            CREATE INDEX idx_claim_graph_edges_target ON graph_edges(target);
            CREATE INDEX idx_claim_graph_edges_relationship ON graph_edges(relationship);
            """
        )
        metadata = {
            "schema_version": CLAIM_GRAPH_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "created_at": _utc_now(),
            "claim_count": len(claims),
            "entity_count": len(entities),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "metrics": metrics,
        }
        for key, value in metadata.items():
            connection.execute(
                "INSERT INTO metadata VALUES (?, ?)",
                (key, json.dumps(value, sort_keys=True)),
            )
        for claim in claims:
            connection.execute(
                """
                INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim["claim_id"],
                    claim["source_set_id"],
                    claim["source_record_id"],
                    claim["chunk_id"],
                    claim["claim_type"],
                    claim["citation_label"],
                    int(claim["source_char_start"]),
                    int(claim["source_char_end"]),
                    claim["content_sha256"],
                    json.dumps(claim, sort_keys=True),
                ),
            )
        for entity in entities:
            connection.execute(
                "INSERT INTO entities VALUES (?, ?, ?, ?)",
                (
                    entity["entity_id"],
                    entity["entity_type"],
                    entity["label"],
                    json.dumps(entity, sort_keys=True),
                ),
            )
        for node in nodes:
            connection.execute(
                "INSERT INTO graph_nodes VALUES (?, ?, ?)",
                (node["id"], node["type"], json.dumps(node, sort_keys=True)),
            )
        for edge in edges:
            connection.execute(
                "INSERT INTO graph_edges VALUES (?, ?, ?, ?, ?)",
                (
                    edge["id"],
                    edge["source"],
                    edge["target"],
                    edge["relationship"],
                    json.dumps(edge, sort_keys=True),
                ),
            )
        connection.commit()


def _sqlite_graph_checks(
    path: Path,
    *,
    expected_claim_count: int,
    expected_entity_count: int,
    expected_node_count: int,
    expected_edge_count: int,
) -> list[dict]:
    if not path.exists():
        return [
            {
                "name": "claim_sqlite_graph_exists",
                "passed": False,
                "details": {"path": str(path)},
            }
        ]
    try:
        with closing(sqlite3.connect(path)) as connection:
            claim_count = connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
            entity_count = connection.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            node_count = connection.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
            edge_count = connection.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
    except sqlite3.Error as error:
        return [
            {
                "name": "claim_sqlite_graph_readable",
                "passed": False,
                "details": {"path": str(path), "error": str(error)},
            }
        ]
    return [
        {
            "name": "claim_sqlite_claim_count_matches_jsonl",
            "passed": claim_count == expected_claim_count,
            "details": {"expected": expected_claim_count, "actual": claim_count},
        },
        {
            "name": "claim_sqlite_entity_count_matches_jsonl",
            "passed": entity_count == expected_entity_count,
            "details": {"expected": expected_entity_count, "actual": entity_count},
        },
        {
            "name": "claim_sqlite_node_count_matches_jsonl",
            "passed": node_count == expected_node_count,
            "details": {"expected": expected_node_count, "actual": node_count},
        },
        {
            "name": "claim_sqlite_edge_count_matches_jsonl",
            "passed": edge_count == expected_edge_count,
            "details": {"expected": expected_edge_count, "actual": edge_count},
        },
    ]


def _query_claims(
    claims: list[dict],
    *,
    query: str,
    filters: dict,
    limit: int,
) -> list[dict]:
    terms = _tokenize(query)
    scored = []
    for claim in claims:
        if not _claim_matches_filters(claim, filters):
            continue
        score = _score_claim(claim, terms=terms, query=query)
        if terms and score <= 0:
            continue
        scored.append((score, claim))
    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1]["source_record_id"]),
            int(item[1]["source_char_start"]),
        )
    )
    return [_claim_eval_result(claim, score) for score, claim in scored[:limit]]


def _load_validated_claims_for_eval(
    claims_path: Path,
    *,
    require_reviewer_ready: bool = True,
) -> list[dict]:
    if not claims_path.exists():
        raise FileNotFoundError(f"Missing claims file: {claims_path}")
    claims_path = claims_path.resolve()
    claims_dir = claims_path.parent
    summary_path = claims_dir / "summary.json"
    validation_path = claims_dir / "claim_validation.json"
    missing = [
        str(path)
        for path in (summary_path, validation_path)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing claim readiness artifact(s): " + ", ".join(missing)
        )
    summary = _read_json(summary_path)
    validation = _read_json(validation_path)
    allowed_partial_failures = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    if not validation.get("passed"):
        failed = ", ".join(_failed_check_names(validation))
        if require_reviewer_ready or any(
            name not in allowed_partial_failures
            for name in _failed_check_names(validation)
        ):
            raise ValueError(
                f"Claim artifacts failed validation: {claims_dir}. "
                f"Resolve claim_validation.json failures before reuse. Failed checks: {failed}"
            )
    if require_reviewer_ready and not summary.get("reviewer_ready"):
        raise ValueError(
            f"Claim artifacts are not reviewer-ready: {claims_dir}. "
            "Run claim-extract and resolve claim_validation.json failures before claim-eval."
        )
    source_set_id = str(summary.get("source_set_id") or "")
    if not source_set_id:
        raise ValueError(f"Claim summary has no source_set_id: {summary_path}")
    output_dir = _output_dir_from_claims_path(claims_path, source_set_id=source_set_id)
    current_validation = validate_claim_outputs(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_path=claims_path,
        entities_path=_required_summary_path(summary, "entities_path"),
        nodes_path=_required_summary_path(summary, "nodes_path"),
        edges_path=_required_summary_path(summary, "edges_path"),
        chunks_path=_required_summary_path(summary, "chunks_path"),
    )
    if not current_validation["passed"]:
        failed = ", ".join(_failed_check_names(current_validation))
        if require_reviewer_ready or any(
            name not in allowed_partial_failures
            for name in _failed_check_names(current_validation)
        ):
            raise ValueError(
                f"Current claim artifacts failed validation before eval: {failed}"
            )
    return _read_jsonl(claims_path)


def _required_summary_path(summary: dict, key: str) -> Path:
    value = summary.get(key)
    if not value:
        raise ValueError(f"Claim summary is missing {key!r}.")
    return Path(str(value))


def _output_dir_from_claims_path(claims_path: Path, *, source_set_id: str) -> Path:
    if claims_path.name != "claims.jsonl":
        raise ValueError(f"Expected claims.jsonl path, got: {claims_path}")
    claims_dir = claims_path.parent
    source_dir = claims_dir.parent
    derived_dir = source_dir.parent
    if claims_dir.name != "claims" or source_dir.name != source_set_id or derived_dir.name != "derived":
        raise ValueError(
            "Claims path must be under source_library/derived/<source_set_id>/claims/."
        )
    return derived_dir.parent


def _claim_matches_filters(claim: dict, filters: dict) -> bool:
    for key in (
        "source_record_id",
        "claim_type",
        "document_role",
        "authority_level",
        "citation_label",
    ):
        value = filters.get(key)
        if value and str(claim.get(key) or "").lower() != str(value).lower():
            return False
    review_topic = filters.get("review_topic") or filters.get("topic")
    if review_topic:
        needle = str(review_topic).lower()
        topics = [str(topic).lower() for topic in claim.get("review_topics", [])]
        if not any(needle == topic or needle in topic for topic in topics):
            return False
    return True


def _score_claim(claim: dict, *, terms: list[str], query: str) -> float:
    if not terms:
        return 0.1
    text = " ".join(
        [
            str(claim.get("claim_text") or ""),
            str(claim.get("title") or ""),
            str(claim.get("citation_label") or ""),
            " ".join(str(topic) for topic in claim.get("review_topics", [])),
        ]
    )
    token_set = set(_tokenize(text))
    term_hits = sum(1 for term in terms if _contains_term(term, token_set, text))
    score = term_hits / len(terms)
    if query.strip() and query.strip().lower() in text.lower():
        score += 0.4
    return score


def _claim_eval_result(claim: dict, score: float) -> dict:
    return {
        "score": round(score, 6),
        "claim_id": claim["claim_id"],
        "claim_type": claim["claim_type"],
        "claim_text": claim["claim_text"],
        "source_record_id": claim["source_record_id"],
        "chunk_id": claim["chunk_id"],
        "citation_label": claim["citation_label"],
        "authority_level": claim["authority_level"],
        "document_role": claim["document_role"],
        "review_topics": claim.get("review_topics", []),
        "provenance": {
            "source_set_id": claim["source_set_id"],
            "artifact_sha256": claim["artifact_sha256"],
            "artifact_path": claim["artifact_path"],
            "parser_name": claim["parser_name"],
            "parser_version": claim["parser_version"],
            "source_text_path": claim.get("source_text_path"),
            "source_char_start": claim["source_char_start"],
            "source_char_end": claim["source_char_end"],
            "chunk_char_start": claim["chunk_char_start"],
            "chunk_char_end": claim["chunk_char_end"],
            "content_sha256": claim["content_sha256"],
        },
    }


def _expected_terms_found(expected_terms: list[str], hits: list[dict]) -> bool:
    haystack = "\n".join(
        " ".join(
            [
                hit.get("claim_text", ""),
                hit.get("citation_label", ""),
                " ".join(hit.get("review_topics", [])),
            ]
        )
        for hit in hits
    ).lower()
    return all(term.lower() in haystack for term in expected_terms)


def _claim_has_required_provenance(claim: dict) -> bool:
    provenance = claim.get("provenance", {})
    return all(
        provenance.get(field) not in (None, "")
        for field in (
            "source_set_id",
            "artifact_sha256",
            "artifact_path",
            "parser_name",
            "parser_version",
            "source_char_start",
            "source_char_end",
            "content_sha256",
        )
    ) and bool(claim.get("citation_label"))


def _eval_failure_reasons(
    *,
    min_claims_met: bool,
    source_hit: bool,
    type_hit: bool,
    term_hit: bool,
    provenance_supported: bool,
) -> list[str]:
    reasons = []
    if not min_claims_met:
        reasons.append("min_claims_not_met")
    if not source_hit:
        reasons.append("expected_source_not_extracted")
    if not type_hit:
        reasons.append("expected_claim_type_not_extracted")
    if not term_hit:
        reasons.append("expected_terms_not_extracted")
    if not provenance_supported:
        reasons.append("citation_provenance_missing")
    return reasons


def _load_eval_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing claim eval file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("Claim eval file must contain a non-empty JSON list.")
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Claim eval case {index} must be an object.")
        for field in ("id", "query"):
            if not case.get(field):
                raise ValueError(f"Claim eval case {index} is missing {field!r}.")
        _validate_eval_case_filters(index, case)
        _validate_eval_case_expectations(index, case)
        _validate_positive_eval_int(index, case, "min_claims")
        _validate_positive_eval_int(index, case, "top_k")
    return payload


def _validate_eval_case_filters(index: int, case: dict) -> None:
    filters = case.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError(f"Claim eval case {index} filters must be an object.")
    unknown = sorted(set(filters) - SUPPORTED_CLAIM_EVAL_FILTERS)
    empty = sorted(key for key, value in filters.items() if value in (None, "", []))
    claim_type = filters.get("claim_type")
    if claim_type and claim_type not in SUPPORTED_CLAIM_TYPES:
        raise ValueError(
            f"Claim eval case {index} has unsupported claim_type filter: {claim_type!r}."
        )
    if unknown or empty:
        details = []
        if unknown:
            details.append(f"unknown filters: {unknown}")
        if empty:
            details.append(f"empty filters: {empty}")
        raise ValueError(
            f"Claim eval case {index} has unsupported filters; " + "; ".join(details)
        )


def _validate_eval_case_expectations(index: int, case: dict) -> None:
    expected_claim_types = case.get("expected_claim_types")
    expected_claim_type = case.get("expected_claim_type")
    if expected_claim_types is not None:
        if not isinstance(expected_claim_types, list) or not expected_claim_types:
            raise ValueError(
                f"Claim eval case {index} expected_claim_types must be a non-empty list."
            )
        unsupported = sorted(set(str(value) for value in expected_claim_types) - SUPPORTED_CLAIM_TYPES)
        if unsupported:
            raise ValueError(
                f"Claim eval case {index} has unsupported expected_claim_types: {unsupported}."
            )
    if expected_claim_type is not None and expected_claim_type not in SUPPORTED_CLAIM_TYPES:
        raise ValueError(
            f"Claim eval case {index} has unsupported expected_claim_type: {expected_claim_type!r}."
        )
    for key in ("expected_source_record_ids", "expected_terms"):
        value = case.get(key)
        if value is not None and not isinstance(value, list):
            raise ValueError(f"Claim eval case {index} {key} must be a list.")


def _validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Claim eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Claim eval case {index} {key} must be at least 1.")


def _failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _load_review_topics(catalog_sqlite_path: Path) -> dict[str, list[str]]:
    if not catalog_sqlite_path.exists():
        return {}
    query = """
        SELECT srt.source_record_id, rt.label
        FROM source_review_topics srt
        JOIN review_topics rt ON rt.topic_id = srt.topic_id
        ORDER BY srt.source_record_id, rt.label
    """
    topics: dict[str, list[str]] = {}
    try:
        with closing(sqlite3.connect(catalog_sqlite_path)) as connection:
            for source_record_id, label in connection.execute(query):
                topics.setdefault(str(source_record_id), []).append(str(label))
    except sqlite3.Error:
        return {}
    return topics


def _load_retrieval_index_records(index_path: Path) -> tuple[dict[str, dict], str | None]:
    if not index_path.exists():
        return {}, f"missing retrieval index: {index_path}"
    query = """
        SELECT
          chunk_id, source_set_id, source_record_id, artifact_sha256, artifact_path,
          citation_label, parser_name, parser_version, content_sha256
        FROM chunks
        ORDER BY source_record_id, chunk_index
    """
    try:
        with closing(sqlite3.connect(index_path)) as connection:
            connection.row_factory = sqlite3.Row
            return {str(row["chunk_id"]): dict(row) for row in connection.execute(query)}, None
    except sqlite3.Error as error:
        return {}, str(error)


def _chunk_with_review_topics(chunk: dict, review_topics: list[str]) -> dict:
    merged = dict(chunk)
    if not merged.get("review_topics"):
        merged["review_topics"] = sorted(set(str(topic) for topic in review_topics if str(topic)))
    return merged


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_retrieval: bool,
) -> dict:
    merged_checks = [*validation["checks"], *checks]
    ignored = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    passed = all(
        check["passed"] or (allow_partial_retrieval and check["name"] in ignored)
        for check in merged_checks
    )
    return {
        **validation,
        "passed": passed,
        "checks": merged_checks,
    }


def _extraction_summary_is_complete(extraction_summary: dict | None) -> bool:
    if not extraction_summary:
        return False
    catalog_count = _int_from_summary(extraction_summary, "catalog_source_count")
    selected_count = _int_from_summary(extraction_summary, "selected_source_count")
    extracted_count = _int_from_summary(extraction_summary, "extracted_count")
    failed_count = _int_from_summary(extraction_summary, "failed_count")
    required_count = (
        _int_from_summary(extraction_summary, "required_extraction_source_count")
        or catalog_count
    )
    selected_required_count = (
        _int_from_summary(extraction_summary, "selected_required_extraction_source_count")
        or selected_count
    )
    filters = extraction_summary.get("filters") or {}
    active_filters = [value for value in filters.values() if value not in (None, "", [])]
    return (
        catalog_count > 0
        and not active_filters
        and selected_count == catalog_count
        and selected_required_count == required_count
        and extracted_count == required_count
        and failed_count == 0
    )


def _retrieval_index_path(source_derived_dir: Path, retrieval_summary: dict | None) -> Path:
    summary_path = (retrieval_summary or {}).get("sqlite_path")
    if summary_path:
        return Path(str(summary_path))
    return source_derived_dir / "retrieval" / DEFAULT_RETRIEVAL_INDEX_FILENAME


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    source_set_id = manifest.get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


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


def _entity_id(entity_type: str, label: str) -> str:
    material = f"{entity_type}|{_normalize_entity_label(label)}"
    return f"entity:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _claim_evidence_span_node_id(claim: dict) -> str:
    material = "|".join(
        [
            str(claim["claim_id"]),
            str(claim["chunk_id"]),
            str(claim["source_char_start"]),
            str(claim["source_char_end"]),
            str(claim["content_sha256"]),
        ]
    )
    return f"claim_evidence_span:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _authority_node_id(authority_level: str) -> str:
    return f"authority:{_slug(authority_level)}"


def _topic_node_id(topic: str) -> str:
    return f"review_topic:{_slug(topic)}"


def _node(node_id: str, node_type: str, **properties: object) -> dict:
    return {"id": node_id, "type": node_type, **properties}


def _edge(source: str, target: str, relationship: str) -> dict:
    return {
        "id": _edge_id(source, target, relationship),
        "source": source,
        "target": target,
        "relationship": relationship,
    }


def _put_edge(edges_by_id: dict[str, dict], source: str, target: str, relationship: str) -> None:
    edge = _edge(source, target, relationship)
    edges_by_id[edge["id"]] = edge


def _edge_id(source: str, target: str, relationship: str) -> str:
    material = f"{source}|{relationship}|{target}"
    return f"edge:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _slug(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        slug = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return slug[:max_length]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _normalize_entity_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if term in token_set:
        return True
    lower = text.lower()
    if term in lower:
        return True
    return any(token.startswith(term) or term.startswith(token) for token in token_set)


def _tokenize(value: str) -> list[str]:
    return [
        token.strip("'-.")
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}", value.lower())
        if len(token.strip("'-.") or "") >= 2
    ]


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _int_from_summary(summary: dict | None, key: str) -> int:
    if not summary:
        return 0
    try:
        return int(summary.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _check_detail_count(validation: dict, check_name: str, detail_key: str) -> int:
    for check in validation.get("checks", []):
        if check.get("name") == check_name:
            return _safe_int((check.get("details") or {}).get(detail_key))
    return 0


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)


def _resolve_path(output_dir: Path, value: str) -> Path:
    path = Path(value)
    candidates = [path] if path.is_absolute() else [path, output_dir / path, output_dir.parent / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
