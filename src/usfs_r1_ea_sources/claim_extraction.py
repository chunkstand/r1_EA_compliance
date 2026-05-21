from __future__ import annotations

from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import sqlite3

from .catalog_surface import resolve_catalog_dir_for_source_set
from .claim_extraction_graph import CLAIM_GRAPH_SCHEMA_VERSION
from .claim_extraction_graph import build_claim_graph_records as _claim_graph_records
from .claim_extraction_graph import build_entity_records as _entity_records
from .claim_extraction_graph import sqlite_graph_checks as _sqlite_graph_checks
from .claim_extraction_graph import write_sqlite_graph as _write_sqlite_graph
from .source_set_support import source_derived_dir


CLAIM_SCHEMA_VERSION = "source-claims-v0"
CLAIM_EXTRACTOR_NAME = "deterministic_legal_claim_patterns"
CLAIM_EXTRACTOR_VERSION = "0.1.0"
CLAIM_EVAL_SCHEMA_VERSION = "claim-eval-v1"
CLAIM_EVAL_RESULTS_SCHEMA_VERSION = "claim-eval-results-v1"
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
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    claims_dir = derived_source_dir / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_path or derived_source_dir / "chunks" / "chunks.jsonl"
    resolved_catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    catalog_sqlite_path = catalog_sqlite_path or resolved_catalog_dir / "review_sources.sqlite"
    extraction_validation_path = derived_source_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = derived_source_dir / "diagnostics" / "summary.json"
    retrieval_validation_path = derived_source_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = derived_source_dir / "retrieval" / "summary.json"
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
    entities = _entity_records(
        claims,
        extractor_name=CLAIM_EXTRACTOR_NAME,
        extractor_version=CLAIM_EXTRACTOR_VERSION,
    )
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
    from .claim_extraction_eval import run_claim_eval as _run_claim_eval

    return _run_claim_eval(
        claims_path=claims_path,
        eval_file=eval_file,
        top_k=top_k,
        output_dir=output_dir,
    )


def _load_validated_claims_for_eval(
    claims_path: Path,
    *,
    require_reviewer_ready: bool = True,
) -> list[dict]:
    from .claim_extraction_eval import _load_validated_claims_for_eval as _load

    return _load(
        claims_path,
        require_reviewer_ready=require_reviewer_ready,
    )


def default_claims_path(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    return source_derived_dir(output_dir / "derived", source_set_id) / "claims" / "claims.jsonl"


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
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    extraction_validation_path = (
        extraction_validation_path
        or derived_source_dir / "diagnostics" / "extraction_validation.json"
    )
    extraction_summary_path = (
        extraction_summary_path or derived_source_dir / "diagnostics" / "summary.json"
    )
    retrieval_validation_path = (
        retrieval_validation_path or derived_source_dir / "retrieval" / "retrieval_validation.json"
    )
    retrieval_summary_path = retrieval_summary_path or derived_source_dir / "retrieval" / "summary.json"
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


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


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
