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

from .catalog_surface import catalog_source_set_id as read_catalog_source_set_id
from .catalog_surface import catalog_source_record_ids as read_catalog_source_record_ids
from .catalog_surface import resolve_catalog_dir_for_source_set
from .eval_metrics import (
    average,
    contract_snapshot,
    first_relevant_rank,
    metric_threshold_check,
    ndcg_at_k,
    read_json_payload,
    reciprocal_rank,
)
from .extraction_admission import matched_verified_extraction_contracts
from .extract import _load_support_document_role_overrides
from .extract import _resolve_support_document_role
from .extract import _source_derived_dir


INDEX_SCHEMA_VERSION = "retrieval-index-v1"
RETRIEVAL_EVAL_SCHEMA_VERSION = "retrieval-eval-v1"
RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION = "retrieval-eval-results-v1"
DEFAULT_INDEX_FILENAME = "evidence_index.sqlite"
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}")
STOPWORDS = {
    "about",
    "also",
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "not",
    "that",
    "the",
    "their",
    "this",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "with",
}
REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "source_set_id",
    "source_record_id",
    "title",
    "document_role",
    "support_document_role",
    "authority_level",
    "artifact_sha256",
    "artifact_path",
    "citation_label",
    "original_url",
    "effective_url",
    "final_url",
    "parser_name",
    "parser_version",
    "extracted_at",
    "char_start",
    "char_end",
    "content_sha256",
    "text",
}


@dataclass(frozen=True)
class RetrievalIndexBuildResult:
    source_set_id: str
    index_dir: Path
    sqlite_path: Path
    manifest_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class RetrievalEvalResult:
    index_path: Path
    eval_file: Path
    output_path: Path
    summary: dict


def build_retrieval_index(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    chunks_path: Path | None = None,
    catalog_sqlite_path: Path | None = None,
    allow_failed_extraction: bool = False,
    allow_partial_extraction: bool = False,
) -> RetrievalIndexBuildResult:
    """Build a local evidence retrieval index from extracted chunks."""

    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    index_dir = source_derived_dir / "retrieval"
    index_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_path or source_derived_dir / "chunks" / "chunks.jsonl"
    resolved_catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    catalog_sqlite_path = catalog_sqlite_path or resolved_catalog_dir / "review_sources.sqlite"
    catalog_source_set_value = read_catalog_source_set_id(catalog_sqlite_path.parent)
    catalog_source_record_ids = read_catalog_source_record_ids(catalog_sqlite_path.parent)
    extraction_validation_path = source_derived_dir / "diagnostics" / "extraction_validation.json"
    extraction_manifest_path = source_derived_dir / "diagnostics" / "extraction_manifest.jsonl"
    extraction_summary_path = source_derived_dir / "diagnostics" / "summary.json"
    extraction_accuracy_path = source_derived_dir / "diagnostics" / "extraction_accuracy_audit.json"
    sqlite_path = index_dir / DEFAULT_INDEX_FILENAME
    manifest_path = index_dir / "retrieval_manifest.json"
    validation_path = index_dir / "retrieval_validation.json"
    summary_path = index_dir / "summary.json"

    chunks = _read_jsonl(chunks_path) if chunks_path.exists() else []
    review_topics_by_source = _load_review_topics(catalog_sqlite_path)
    support_document_roles_by_source = _load_catalog_support_document_roles(catalog_sqlite_path)
    indexed_chunks = []
    for chunk in chunks:
        source_topics = review_topics_by_source.get(chunk.get("source_record_id"), [])
        indexed_chunks.append(
            _chunk_with_catalog_context(
                chunk,
                source_topics,
                support_document_roles_by_source=support_document_roles_by_source,
            )
        )
    extraction_validation = (
        _read_json(extraction_validation_path) if extraction_validation_path.exists() else None
    )
    extraction_summary = (
        _read_json(extraction_summary_path) if extraction_summary_path.exists() else None
    )
    extraction_manifest_records = (
        _read_jsonl(extraction_manifest_path) if extraction_manifest_path.exists() else []
    )
    verified_extraction_requirements = matched_verified_extraction_contracts(
        records=extraction_manifest_records
    )
    extraction_accuracy = (
        _read_json(extraction_accuracy_path) if extraction_accuracy_path.exists() else None
    )
    validation = _validation_report(
        output_dir=output_dir,
        source_set_id=source_set_id,
        chunks_path=chunks_path,
        catalog_sqlite_path=catalog_sqlite_path,
        catalog_source_set_id=catalog_source_set_value,
        catalog_source_record_ids=catalog_source_record_ids,
        extraction_validation_path=extraction_validation_path,
        extraction_validation=extraction_validation,
        extraction_manifest_path=extraction_manifest_path,
        extraction_manifest_records=extraction_manifest_records,
        extraction_summary_path=extraction_summary_path,
        extraction_summary=extraction_summary,
        extraction_accuracy_path=extraction_accuracy_path,
        extraction_accuracy=extraction_accuracy,
        verified_extraction_requirements=verified_extraction_requirements,
        chunks=indexed_chunks,
        allow_failed_extraction=allow_failed_extraction,
        allow_partial_extraction=allow_partial_extraction,
    )

    fts_enabled = False
    if validation["passed"]:
        fts_enabled = _write_sqlite_index(
            sqlite_path,
            source_set_id=source_set_id,
            chunks=indexed_chunks,
            chunks_path=chunks_path,
            catalog_sqlite_path=catalog_sqlite_path,
        )
        sqlite_checks = _sqlite_index_checks(
            sqlite_path,
            expected_chunk_count=len(indexed_chunks),
            expected_source_set_id=source_set_id,
            fts_enabled=fts_enabled,
        )
        validation = _with_additional_checks(validation, sqlite_checks)
        if not validation["passed"] and sqlite_path.exists():
            sqlite_path.unlink()
    elif sqlite_path.exists():
        sqlite_path.unlink()

    source_counts = Counter(chunk["source_record_id"] for chunk in indexed_chunks)
    extraction_complete = _extraction_summary_is_complete(extraction_summary)
    manifest = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "chunks_path": str(chunks_path),
        "catalog_dir": str(catalog_sqlite_path.parent),
        "catalog_sqlite_path": str(catalog_sqlite_path),
        "catalog_source_set_id": catalog_source_set_value,
        "extraction_validation_path": str(extraction_validation_path),
        "extraction_manifest_path": str(extraction_manifest_path),
        "extraction_summary_path": str(extraction_summary_path),
        "sqlite_path": str(sqlite_path),
        "chunk_count": len(indexed_chunks),
        "source_count": len(source_counts),
        "fts_enabled": fts_enabled,
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"] and extraction_complete,
    }
    summary = {
        **manifest,
        "index_dir": str(index_dir),
        "manifest_path": str(manifest_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "allow_failed_extraction": allow_failed_extraction,
        "allow_partial_extraction": allow_partial_extraction,
        "catalog_source_count": _int_from_summary(extraction_summary, "catalog_source_count"),
        "selected_source_count": _int_from_summary(extraction_summary, "selected_source_count"),
        "extracted_source_count": _int_from_summary(extraction_summary, "extracted_count"),
        "extraction_filters": (extraction_summary or {}).get("filters", {}),
        "extraction_complete": extraction_complete,
        "verified_extraction_required_source_count": len(
            verified_extraction_requirements["required_source_record_ids"]
        ),
        "verified_extraction_contract_ids": [
            contract.get("contract_id")
            for contract in verified_extraction_requirements["contracts"]
        ],
        "verified_extraction_admitted_source_count": len(
            (extraction_accuracy or {}).get("knowledge_base_admitted_source_record_ids", [])
        ),
        "document_role_counts": dict(
            Counter(chunk.get("document_role") for chunk in indexed_chunks)
        ),
        "support_document_role_counts": dict(
            Counter(chunk.get("support_document_role") for chunk in indexed_chunks)
        ),
        "authority_level_counts": dict(
            Counter(chunk.get("authority_level") for chunk in indexed_chunks)
        ),
        "parser_counts": dict(Counter(chunk.get("parser_name") for chunk in indexed_chunks)),
        "topic_link_count": sum(len(chunk.get("review_topics", [])) for chunk in indexed_chunks),
    }

    _write_json(manifest_path, manifest)
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
    return RetrievalIndexBuildResult(
        source_set_id=source_set_id,
        index_dir=index_dir,
        sqlite_path=sqlite_path,
        manifest_path=manifest_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
    )


def query_retrieval_index(
    *,
    index_path: Path,
    query: str,
    limit: int = 5,
    document_role: str | None = None,
    support_document_role: str | None = None,
    authority_level: str | None = None,
    source_record_id: str | None = None,
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

    filters = {
        "document_role": document_role,
        "support_document_role": support_document_role,
        "authority_level": authority_level,
        "source_record_id": source_record_id,
        "review_topic": review_topic,
        "citation": citation,
        "host": host,
    }
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
            source_record_id=source_record_id,
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


def run_retrieval_eval(
    *,
    index_path: Path,
    eval_file: Path,
    top_k: int = 5,
    output_dir: Path | None = None,
) -> RetrievalEvalResult:
    """Run a small evidence retrieval eval set against the local index."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    index_path = Path(index_path)
    eval_file = Path(eval_file)
    contract, cases, legacy_format = _load_eval_contract(eval_file)
    output_dir = output_dir or index_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "retrieval_eval_results.json"
    source_set_id = _source_set_id_from_index_path(index_path)

    case_results = []
    for case in cases:
        filters = dict(case.get("filters") or {})
        expect_no_hits = bool(case.get("expect_no_hits"))
        result = query_retrieval_index(
            index_path=index_path,
            query=str(case["query"]),
            limit=int(case.get("top_k") or top_k),
            document_role=filters.get("document_role"),
            support_document_role=filters.get("support_document_role"),
            authority_level=filters.get("authority_level"),
            source_record_id=filters.get("source_record_id"),
            review_topic=filters.get("review_topic") or filters.get("topic"),
            citation=filters.get("citation"),
            host=filters.get("host"),
        )
        hits = result["results"]
        expected_sources = _dedupe(
            str(value) for value in case.get("expected_source_record_ids", [])
        )
        expected_terms = [str(value) for value in case.get("expected_terms", [])]
        forbidden_sources = _dedupe(
            str(value) for value in case.get("forbidden_source_record_ids", [])
        )
        min_hits = 0 if expect_no_hits else int(case.get("min_hits", 1))
        zero_hits = len(hits) == 0
        matched_expected_sources = _matched_expected_source_record_ids(
            expected_sources,
            hits,
        )
        missing_expected_sources = [
            source_id for source_id in expected_sources if source_id not in matched_expected_sources
        ]
        source_hit = zero_hits if expect_no_hits else (not expected_sources or not missing_expected_sources)
        term_hit = zero_hits if expect_no_hits else (
            not expected_terms or _expected_terms_found(expected_terms, hits)
        )
        missing_expected_terms = [] if expect_no_hits else _missing_expected_terms(expected_terms, hits)
        unexpected_sources = [
            hit["source_record_id"]
            for hit in hits
            if hit["source_record_id"] in forbidden_sources
        ]
        relevance = _retrieval_relevance(hits, expected_sources)
        relevant_hits = [
            hit
            for hit, is_relevant in zip(hits, relevance, strict=False)
            if is_relevant
        ]
        first_rank = first_relevant_rank(relevance)
        top_rank_relevant = bool(relevance and relevance[0])
        top_rank_false_positive = bool(hits) if expect_no_hits else bool(hits) and not top_rank_relevant
        required_source_recall = _rate(
            len(matched_expected_sources),
            len(expected_sources),
        )
        min_hits_met = len(hits) >= min_hits
        provenance_supported = (
            zero_hits
            if expect_no_hits
            else bool(relevant_hits or hits)
            and any(_hit_has_required_provenance(hit) for hit in (relevant_hits or hits))
        )
        passed = (
            min_hits_met
            and source_hit
            and term_hit
            and provenance_supported
            and not top_rank_false_positive
            and not unexpected_sources
        )
        failure_reasons = _eval_failure_reasons(
            expect_no_hits=expect_no_hits,
            min_hits_met=min_hits_met,
            source_hit=source_hit,
            term_hit=term_hit,
            provenance_supported=provenance_supported,
            top_rank_false_positive=top_rank_false_positive,
            unexpected_sources=unexpected_sources,
        )
        case_results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "filters": filters,
                "hard_negative": bool(case.get("hard_negative") or expect_no_hits),
                "multi_source": bool(case.get("multi_source") or len(expected_sources) > 1),
                "expected_source_record_ids": expected_sources,
                "expected_terms": expected_terms,
                "forbidden_source_record_ids": forbidden_sources,
                "expect_no_hits": expect_no_hits,
                "top_k": result["limit"],
                "hit_count": len(hits),
                "top_source_record_ids": [hit["source_record_id"] for hit in hits],
                "source_hit": source_hit,
                "term_hit": term_hit,
                "matched_expected_source_record_ids": matched_expected_sources,
                "missing_expected_source_record_ids": missing_expected_sources,
                "missing_expected_terms": missing_expected_terms,
                "unexpected_source_record_ids": unexpected_sources,
                "required_source_recall": required_source_recall,
                "min_hits_met": min_hits_met,
                "provenance_supported": provenance_supported,
                "relevant_ranks": [
                    index for index, is_relevant in enumerate(relevance, start=1) if is_relevant
                ],
                "first_relevant_rank": first_rank,
                "top_rank_relevant": top_rank_relevant,
                "top_rank_false_positive": top_rank_false_positive,
                "failure_reasons": failure_reasons,
                "passed": passed,
                "top_results": hits,
            }
        )

    query_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    failed_count = query_count - passed_count
    zero_result_count = sum(1 for case in case_results if case["hit_count"] == 0)
    provenance_supported_count = sum(
        1 for case in case_results if case["provenance_supported"]
    )
    source_hit_count = sum(1 for case in case_results if case["source_hit"])
    term_hit_count = sum(1 for case in case_results if case["term_hit"])
    unsupported_answer_count = query_count - provenance_supported_count
    hard_negative_cases = [case for case in case_results if case["hard_negative"]]
    multi_source_cases = [case for case in case_results if case["multi_source"]]
    ranking_cases = [
        case
        for case in case_results
        if not case["expect_no_hits"] and case["expected_source_record_ids"]
    ]
    total_required_sources = sum(len(case["expected_source_record_ids"]) for case in ranking_cases)
    matched_required_sources = sum(
        len(case["matched_expected_source_record_ids"]) for case in ranking_cases
    )
    metrics = {
        "case_count": query_count,
        "pass_rate": _rate(passed_count, query_count),
        "source_hit_rate": _rate(source_hit_count, query_count),
        "expected_term_hit_rate": _rate(term_hit_count, query_count),
        "citation_coverage_rate": _rate(provenance_supported_count, query_count),
        "unsupported_answer_rate": _rate(unsupported_answer_count, query_count),
        "zero_result_rate": _rate(zero_result_count, query_count),
        "hard_negative_pass_rate": _rate(
            sum(1 for case in hard_negative_cases if case["hit_count"] == 0),
            len(hard_negative_cases),
        ),
        "false_positive_rate": _rate(
            sum(1 for case in case_results if case["top_rank_false_positive"]),
            query_count,
        ),
        "missing_required_source_rate": _rate(
            total_required_sources - matched_required_sources,
            total_required_sources,
        ),
        "recall_at_k": _rate(matched_required_sources, total_required_sources),
        "mrr": average(
            reciprocal_rank(
                _retrieval_relevance(
                    case["top_results"],
                    case["expected_source_record_ids"],
                )
            )
            for case in ranking_cases
        ),
        "ndcg_at_k": average(
            ndcg_at_k(
                _retrieval_relevance(
                    case["top_results"],
                    case["expected_source_record_ids"],
                ),
                relevant_count=len(case["expected_source_record_ids"]),
                k=case["top_k"],
            )
            for case in ranking_cases
        ),
    }
    checks = [
        {
            "name": "eval_cases_pass",
            "passed": failed_count == 0,
            "details": {
                "case_count": query_count,
                "failed_case_ids": [case["id"] for case in case_results if not case["passed"]],
            },
        },
        _retrieval_coverage_check(contract, case_results, legacy_format=legacy_format),
        metric_threshold_check(contract.get("metric_thresholds", {}), metrics),
    ]
    summary = {
        "schema_version": RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "source_set_id": source_set_id,
        "index_path": str(index_path),
        "eval_file": str(eval_file),
        "output_path": str(output_path),
        "created_at": _utc_now(),
        "top_k": top_k,
        "query_count": query_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "hard_negative_case_count": len(hard_negative_cases),
        "multi_source_case_count": len(multi_source_cases),
        "checks": checks,
        "metrics": metrics,
        "contract": contract_snapshot(
            contract_path=eval_file,
            contract=contract,
            case_count=len(cases),
        ),
        "cases": case_results,
    }
    summary["passed"] = all(check["passed"] for check in checks)
    _write_json(output_path, summary)
    return RetrievalEvalResult(
        index_path=index_path,
        eval_file=eval_file,
        output_path=output_path,
        summary=summary,
    )


def default_index_path(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    return source_derived_dir / "retrieval" / DEFAULT_INDEX_FILENAME


def _write_sqlite_index(
    path: Path,
    *,
    source_set_id: str,
    chunks: list[dict],
    chunks_path: Path,
    catalog_sqlite_path: Path,
) -> bool:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_index_schema(connection)
        fts_enabled = _create_fts_table(connection)
        _insert_metadata(
            connection,
            {
                "schema_version": INDEX_SCHEMA_VERSION,
                "source_set_id": source_set_id,
                "created_at": _utc_now(),
                "chunks_path": str(chunks_path),
                "catalog_sqlite_path": str(catalog_sqlite_path),
                "chunk_count": len(chunks),
                "fts_enabled": fts_enabled,
            },
        )
        for chunk in chunks:
            rowid = _insert_chunk(connection, chunk)
            if fts_enabled:
                connection.execute(
                    """
                    INSERT INTO chunks_fts(rowid, text, title, heading, citation_label)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        rowid,
                        chunk.get("text") or "",
                        chunk.get("title") or "",
                        chunk.get("heading") or "",
                        chunk.get("citation_label") or "",
                    ),
                )
        connection.commit()
    return fts_enabled


def _create_index_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE metadata (
          key TEXT PRIMARY KEY,
          value_json TEXT NOT NULL
        );

        CREATE TABLE chunks (
          chunk_id TEXT PRIMARY KEY,
          source_set_id TEXT NOT NULL,
          source_record_id TEXT NOT NULL,
          chunk_index INTEGER NOT NULL,
          title TEXT NOT NULL,
          document_role TEXT NOT NULL,
          support_document_role TEXT NOT NULL,
          authority_level TEXT NOT NULL,
          host TEXT,
          expected_parser TEXT,
          artifact_sha256 TEXT NOT NULL,
          artifact_path TEXT NOT NULL,
          citation_label TEXT NOT NULL,
          original_url TEXT NOT NULL,
          effective_url TEXT NOT NULL,
          final_url TEXT,
          parser_name TEXT NOT NULL,
          parser_version TEXT NOT NULL,
          extracted_at TEXT NOT NULL,
          source_text_path TEXT,
          char_start INTEGER NOT NULL,
          char_end INTEGER NOT NULL,
          page INTEGER,
          section TEXT,
          heading TEXT,
          content_sha256 TEXT NOT NULL,
          review_topics_json TEXT NOT NULL,
          text TEXT NOT NULL
        );

        CREATE INDEX idx_chunks_source_record_id ON chunks(source_record_id);
        CREATE INDEX idx_chunks_document_role ON chunks(document_role);
        CREATE INDEX idx_chunks_support_document_role ON chunks(support_document_role);
        CREATE INDEX idx_chunks_authority_level ON chunks(authority_level);
        CREATE INDEX idx_chunks_host ON chunks(host);
        CREATE INDEX idx_chunks_artifact_sha256 ON chunks(artifact_sha256);
        """
    )


def _create_fts_table(connection: sqlite3.Connection) -> bool:
    try:
        connection.execute(
            """
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
              text,
              title,
              heading,
              citation_label,
              content='chunks',
              content_rowid='rowid'
            )
            """
        )
    except sqlite3.OperationalError:
        return False
    return True


def _insert_metadata(connection: sqlite3.Connection, metadata: dict) -> None:
    for key, value in metadata.items():
        connection.execute(
            "INSERT INTO metadata VALUES (?, ?)",
            (key, json.dumps(value, sort_keys=True)),
        )


def _insert_chunk(connection: sqlite3.Connection, chunk: dict) -> int:
    cursor = connection.execute(
        """
        INSERT INTO chunks (
          chunk_id, source_set_id, source_record_id, chunk_index, title, document_role,
          support_document_role, authority_level, host, expected_parser, artifact_sha256, artifact_path,
          citation_label, original_url, effective_url, final_url, parser_name,
          parser_version, extracted_at, source_text_path, char_start, char_end, page,
          section, heading, content_sha256, review_topics_json, text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            chunk["chunk_id"],
            chunk["source_set_id"],
            chunk["source_record_id"],
            int(chunk.get("chunk_index") or 0),
            chunk["title"],
            chunk["document_role"],
            chunk["support_document_role"],
            chunk["authority_level"],
            chunk.get("host"),
            chunk.get("expected_parser"),
            chunk["artifact_sha256"],
            chunk["artifact_path"],
            chunk["citation_label"],
            chunk["original_url"],
            chunk["effective_url"],
            chunk.get("final_url"),
            chunk["parser_name"],
            chunk["parser_version"],
            chunk["extracted_at"],
            chunk.get("source_text_path"),
            int(chunk["char_start"]),
            int(chunk["char_end"]),
            chunk.get("page"),
            chunk.get("section"),
            chunk.get("heading"),
            chunk["content_sha256"],
            json.dumps(chunk.get("review_topics", []), sort_keys=True),
            chunk["text"],
        ),
    )
    return int(cursor.lastrowid)


def _load_candidate_rows(
    connection: sqlite3.Connection,
    *,
    document_role: str | None,
    support_document_role: str | None,
    authority_level: str | None,
    source_record_id: str | None,
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
    if source_record_id:
        query += " AND source_record_id = ?"
        params.append(source_record_id)
    if host:
        query += " AND host = ?"
        params.append(host)
    query += " ORDER BY source_record_id, chunk_index"
    return list(connection.execute(query, params))


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


def _load_catalog_support_document_roles(catalog_sqlite_path: Path) -> dict[str, str]:
    if not catalog_sqlite_path.exists():
        return {}
    query = """
        SELECT source_record_id, document_role, metadata_json
        FROM sources
        ORDER BY source_record_id
    """
    support_document_role_overrides = _load_support_document_role_overrides()
    roles: dict[str, str] = {}
    try:
        with closing(sqlite3.connect(catalog_sqlite_path)) as connection:
            connection.row_factory = sqlite3.Row
            for row in connection.execute(query):
                source_record_id = str(row["source_record_id"] or "").strip()
                if not source_record_id:
                    continue
                metadata = {}
                metadata_json = row["metadata_json"]
                if isinstance(metadata_json, str) and metadata_json.strip():
                    try:
                        payload = json.loads(metadata_json)
                    except json.JSONDecodeError:
                        payload = {}
                    if isinstance(payload, dict):
                        metadata = payload
                role = _resolve_support_document_role(
                    {
                        "source_record_id": source_record_id,
                        "document_role": row["document_role"],
                        "metadata": metadata,
                    },
                    support_document_role_overrides=support_document_role_overrides,
                )
                if role:
                    roles[source_record_id] = role
    except sqlite3.Error:
        return {}
    return roles


def _chunk_with_catalog_context(
    chunk: dict,
    review_topics: list[str],
    *,
    support_document_roles_by_source: dict[str, str],
) -> dict:
    merged = dict(chunk)
    merged["review_topics"] = sorted(set(str(topic) for topic in review_topics if str(topic)))
    if not merged.get("support_document_role"):
        merged["support_document_role"] = (
            support_document_roles_by_source.get(str(merged.get("source_record_id") or ""))
            or merged.get("document_role")
        )
    return merged


def _validation_report(
    *,
    output_dir: Path,
    source_set_id: str,
    chunks_path: Path,
    catalog_sqlite_path: Path,
    catalog_source_set_id: str | None,
    catalog_source_record_ids: set[str] | None,
    extraction_validation_path: Path,
    extraction_validation: dict | None,
    extraction_manifest_path: Path,
    extraction_manifest_records: list[dict],
    extraction_summary_path: Path,
    extraction_summary: dict | None,
    extraction_accuracy_path: Path,
    extraction_accuracy: dict | None,
    verified_extraction_requirements: dict,
    chunks: list[dict],
    allow_failed_extraction: bool,
    allow_partial_extraction: bool,
) -> dict:
    checks = [
        {
            "name": "extraction_validation_passed",
            "passed": allow_failed_extraction
            or bool(extraction_validation and extraction_validation.get("passed")),
            "details": {
                "path": str(extraction_validation_path),
                "exists": extraction_validation_path.exists(),
                "allow_failed_extraction": allow_failed_extraction,
                "passed": bool(extraction_validation and extraction_validation.get("passed")),
            },
        },
        {
            "name": "extraction_manifest_exists",
            "passed": extraction_manifest_path.exists(),
            "details": {"path": str(extraction_manifest_path)},
        },
        {
            "name": "extraction_summary_exists",
            "passed": extraction_summary_path.exists(),
            "details": {"path": str(extraction_summary_path)},
        },
        _check_verified_extraction_audit_exists(
            extraction_accuracy_path,
            verified_extraction_requirements=verified_extraction_requirements,
        ),
        _check_verified_extraction_audit_allows_knowledge_base_admission(
            source_set_id=source_set_id,
            extraction_accuracy_path=extraction_accuracy_path,
            extraction_accuracy=extraction_accuracy,
            verified_extraction_requirements=verified_extraction_requirements,
        ),
        _check_extraction_scope_is_complete(
            extraction_summary,
            allow_partial_extraction=allow_partial_extraction,
        ),
        {
            "name": "chunks_jsonl_exists",
            "passed": chunks_path.exists(),
            "details": {"path": str(chunks_path)},
        },
        {
            "name": "catalog_sqlite_exists",
            "passed": catalog_sqlite_path.exists(),
            "details": {"path": str(catalog_sqlite_path)},
        },
        _check_catalog_source_set_matches_requested_source_set(
            requested_source_set_id=source_set_id,
            catalog_sqlite_path=catalog_sqlite_path,
            catalog_source_set_id=catalog_source_set_id,
            catalog_source_record_ids=catalog_source_record_ids,
            extraction_manifest_records=extraction_manifest_records,
        ),
        _check_chunks_loaded(chunks),
        _check_source_set_ids_match(source_set_id, chunks),
        _check_chunk_ids_unique(chunks),
        _check_required_chunk_fields(chunks),
        _check_chunk_review_topics(chunks),
        _check_extracted_sources_match_chunks(extraction_manifest_records, chunks),
        _check_chunk_paths_exist(output_dir, chunks),
        _check_chunk_hashes(chunks),
        _check_chunk_offsets(chunks),
    ]
    return {
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_chunks_loaded(chunks: list[dict]) -> dict:
    return {
        "name": "chunks_loaded",
        "passed": bool(chunks),
        "details": {"chunk_count": len(chunks)},
    }


def _check_catalog_source_set_matches_requested_source_set(
    *,
    requested_source_set_id: str,
    catalog_sqlite_path: Path,
    catalog_source_set_id: str | None,
    catalog_source_record_ids: set[str] | None,
    extraction_manifest_records: list[dict],
) -> dict:
    manifest_path = catalog_sqlite_path.parent / "source_set_manifest.json"
    selected_source_record_ids = {
        str(record.get("source_record_id"))
        for record in extraction_manifest_records
        if record.get("source_record_id")
    }
    missing_source_record_ids = sorted(
        selected_source_record_ids - (catalog_source_record_ids or set())
    )
    unexpected_source_record_ids = sorted(
        (catalog_source_record_ids or set()) - selected_source_record_ids
    )
    source_record_sets_match = (
        bool(selected_source_record_ids)
        and catalog_source_record_ids is not None
        and not missing_source_record_ids
        and not unexpected_source_record_ids
    )
    exact_source_set_match = (
        not catalog_source_set_id or catalog_source_set_id == requested_source_set_id
    )
    if exact_source_set_match:
        match_mode = "exact_source_set_id"
    elif source_record_sets_match:
        match_mode = "selected_source_record_set"
    else:
        match_mode = "mismatch"
    return {
        "name": "catalog_source_set_matches_requested_source_set",
        "passed": exact_source_set_match or source_record_sets_match,
        "details": {
            "path": str(catalog_sqlite_path),
            "source_set_manifest_path": str(manifest_path),
            "source_set_manifest_exists": manifest_path.exists(),
            "requested_source_set_id": requested_source_set_id,
            "catalog_source_set_id": catalog_source_set_id,
            "match_mode": match_mode,
            "selected_source_record_count": len(selected_source_record_ids),
            "catalog_source_record_count": (
                len(catalog_source_record_ids) if catalog_source_record_ids is not None else None
            ),
            "missing_source_record_ids": missing_source_record_ids[:50],
            "unexpected_source_record_ids": unexpected_source_record_ids[:50],
        },
    }


def _check_source_set_ids_match(source_set_id: str, chunks: list[dict]) -> dict:
    mismatches = [
        chunk.get("chunk_id")
        for chunk in chunks
        if chunk.get("source_set_id") != source_set_id
    ]
    return {
        "name": "chunk_source_set_ids_match",
        "passed": not mismatches,
        "details": {"chunk_ids": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_extraction_scope_is_complete(
    extraction_summary: dict | None,
    *,
    allow_partial_extraction: bool,
) -> dict:
    complete = _extraction_summary_is_complete(extraction_summary)
    return {
        "name": "extraction_scope_is_complete",
        "passed": complete or allow_partial_extraction,
        "details": {
            "allow_partial_extraction": allow_partial_extraction,
            "catalog_source_count": _int_from_summary(extraction_summary, "catalog_source_count"),
            "selected_source_count": _int_from_summary(extraction_summary, "selected_source_count"),
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
            "complete": complete,
        },
    }


def _check_verified_extraction_audit_exists(
    extraction_accuracy_path: Path,
    *,
    verified_extraction_requirements: dict,
) -> dict:
    required_source_record_ids = list(verified_extraction_requirements["required_source_record_ids"])
    return {
        "name": "verified_extraction_accuracy_audit_exists",
        "passed": not required_source_record_ids or extraction_accuracy_path.exists(),
        "details": {
            "path": str(extraction_accuracy_path),
            "exists": extraction_accuracy_path.exists(),
            "required_source_record_ids": required_source_record_ids,
            "contract_ids": [
                contract.get("contract_id")
                for contract in verified_extraction_requirements["contracts"]
            ],
        },
    }


def _check_verified_extraction_audit_allows_knowledge_base_admission(
    *,
    source_set_id: str,
    extraction_accuracy_path: Path,
    extraction_accuracy: dict | None,
    verified_extraction_requirements: dict,
) -> dict:
    required_source_record_ids = set(verified_extraction_requirements["required_source_record_ids"])
    if not required_source_record_ids:
        return {
            "name": "required_sources_are_admitted_by_verified_extraction_audit",
            "passed": True,
            "details": {
                "path": str(extraction_accuracy_path),
                "required_source_record_ids": [],
                "admitted_source_record_ids": [],
                "blocked_source_record_ids": [],
            },
        }
    admitted_source_record_ids = set(
        str(value)
        for value in (extraction_accuracy or {}).get("knowledge_base_admitted_source_record_ids", [])
        if str(value)
    )
    blocked_source_record_ids = sorted(required_source_record_ids - admitted_source_record_ids)
    source_set_matches = bool(extraction_accuracy) and str(extraction_accuracy.get("source_set_id") or "") == source_set_id
    audit_passed = bool(extraction_accuracy and extraction_accuracy.get("passed"))
    return {
        "name": "required_sources_are_admitted_by_verified_extraction_audit",
        "passed": source_set_matches and audit_passed and not blocked_source_record_ids,
        "details": {
            "path": str(extraction_accuracy_path),
            "exists": extraction_accuracy_path.exists(),
            "audit_source_set_id": (extraction_accuracy or {}).get("source_set_id"),
            "source_set_matches": source_set_matches,
            "audit_passed": audit_passed,
            "required_source_record_ids": sorted(required_source_record_ids),
            "admitted_source_record_ids": sorted(admitted_source_record_ids),
            "blocked_source_record_ids": blocked_source_record_ids,
            "contract_ids": [
                contract.get("contract_id")
                for contract in verified_extraction_requirements["contracts"]
            ],
        },
    }


def _check_chunk_ids_unique(chunks: list[dict]) -> dict:
    counts = Counter(chunk.get("chunk_id") for chunk in chunks)
    duplicates = sorted(chunk_id for chunk_id, count in counts.items() if chunk_id and count > 1)
    return {
        "name": "chunk_ids_are_unique",
        "passed": not duplicates,
        "details": {"duplicate_chunk_ids": duplicates},
    }


def _check_required_chunk_fields(chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        missing = [
            field for field in sorted(REQUIRED_CHUNK_FIELDS) if chunk.get(field) in (None, "")
        ]
        if missing:
            failures.append({"chunk_id": chunk.get("chunk_id"), "missing_fields": missing})
    return {
        "name": "chunks_have_retrieval_provenance",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_review_topics(chunks: list[dict]) -> dict:
    failures = [
        chunk.get("chunk_id")
        for chunk in chunks
        if not chunk.get("review_topics")
    ]
    return {
        "name": "chunks_have_catalog_review_topics",
        "passed": not failures,
        "details": {"chunk_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_extracted_sources_match_chunks(
    extraction_manifest_records: list[dict],
    chunks: list[dict],
) -> dict:
    extracted_source_ids = {
        str(record.get("source_record_id"))
        for record in extraction_manifest_records
        if record.get("status") == "extracted" and record.get("source_record_id")
    }
    chunk_source_ids = {
        str(chunk.get("source_record_id"))
        for chunk in chunks
        if chunk.get("source_record_id")
    }
    missing_from_chunks = sorted(extracted_source_ids - chunk_source_ids)
    unexpected_chunk_sources = sorted(chunk_source_ids - extracted_source_ids)
    return {
        "name": "indexed_sources_match_extraction_manifest",
        "passed": not missing_from_chunks and not unexpected_chunk_sources,
        "details": {
            "extracted_source_count": len(extracted_source_ids),
            "chunk_source_count": len(chunk_source_ids),
            "missing_from_chunks": missing_from_chunks[:50],
            "unexpected_chunk_sources": unexpected_chunk_sources[:50],
        },
    }


def _check_chunk_paths_exist(output_dir: Path, chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        artifact_path = _resolve_existing_path(output_dir, chunk.get("artifact_path"))
        text_path = _resolve_existing_path(output_dir, chunk.get("source_text_path"))
        missing = []
        if artifact_path is None or not artifact_path.is_file():
            missing.append("artifact_path")
        if chunk.get("source_text_path") and (text_path is None or not text_path.is_file()):
            missing.append("source_text_path")
        if missing:
            failures.append({"chunk_id": chunk.get("chunk_id"), "missing_paths": missing})
    return {
        "name": "chunk_artifact_and_text_paths_exist",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_hashes(chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if chunk.get("content_sha256") != expected:
            failures.append(chunk.get("chunk_id"))
    return {
        "name": "chunk_content_hashes_match_text",
        "passed": not failures,
        "details": {"chunk_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_chunk_offsets(chunks: list[dict]) -> dict:
    failures = []
    for chunk in chunks:
        try:
            start = int(chunk["char_start"])
            end = int(chunk["char_end"])
        except (KeyError, TypeError, ValueError):
            failures.append(chunk.get("chunk_id"))
            continue
        if start < 0 or end <= start:
            failures.append(chunk.get("chunk_id"))
    return {
        "name": "chunk_offsets_are_valid",
        "passed": not failures,
        "details": {"chunk_ids": failures[:50], "failure_count": len(failures)},
    }


def _sqlite_index_checks(
    path: Path,
    *,
    expected_chunk_count: int,
    expected_source_set_id: str,
    fts_enabled: bool,
) -> list[dict]:
    if not path.exists():
        return [
            {
                "name": "sqlite_index_exists",
                "passed": False,
                "details": {"path": str(path)},
            }
        ]
    try:
        with closing(sqlite3.connect(path)) as connection:
            chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            source_set_values = [
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT source_set_id FROM chunks ORDER BY source_set_id"
                )
            ]
            metadata_source_set_id = _metadata_value(connection, "source_set_id")
            fts_count = None
            if fts_enabled:
                fts_count = connection.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    except sqlite3.Error as error:
        return [
            {
                "name": "sqlite_index_readable",
                "passed": False,
                "details": {"path": str(path), "error": str(error)},
            }
        ]
    return [
        {
            "name": "sqlite_index_chunk_count_matches_jsonl",
            "passed": chunk_count == expected_chunk_count,
            "details": {"expected": expected_chunk_count, "actual": chunk_count},
        },
        {
            "name": "sqlite_index_source_set_matches",
            "passed": source_set_values == [expected_source_set_id]
            and metadata_source_set_id == expected_source_set_id,
            "details": {
                "expected": expected_source_set_id,
                "chunk_source_set_ids": source_set_values,
                "metadata_source_set_id": metadata_source_set_id,
            },
        },
        {
            "name": "sqlite_fts_chunk_count_matches",
            "passed": (not fts_enabled) or fts_count == expected_chunk_count,
            "details": {
                "fts_enabled": fts_enabled,
                "expected": expected_chunk_count if fts_enabled else None,
                "actual": fts_count,
            },
        },
    ]


def _metadata_value(connection: sqlite3.Connection, key: str) -> object | None:
    row = connection.execute(
        "SELECT value_json FROM metadata WHERE key = ?",
        (key,),
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def _with_additional_checks(validation: dict, checks: list[dict]) -> dict:
    merged_checks = [*validation["checks"], *checks]
    return {
        **validation,
        "passed": all(check["passed"] for check in merged_checks),
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
    if catalog_count <= 0:
        return False
    filters = extraction_summary.get("filters") or {}
    active_filters = [value for value in filters.values() if value not in (None, "", [])]
    return (
        not active_filters
        and selected_count == catalog_count
        and selected_required_count == required_count
        and extracted_count == required_count
        and failed_count == 0
    )


def _int_from_summary(extraction_summary: dict | None, key: str) -> int:
    if not extraction_summary:
        return 0
    try:
        return int(extraction_summary.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _resolve_existing_path(output_dir: Path, value: object | None) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = (
        [path]
        if path.is_absolute()
        else [path, output_dir / path, output_dir.parent / path]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _load_eval_contract(path: Path) -> tuple[dict, list[dict], bool]:
    payload = read_json_payload(path, label="retrieval eval file")
    if isinstance(payload, list):
        cases = _validated_eval_cases(payload, legacy_format=True)
        return (
            {
                "schema_version": "legacy-retrieval-eval-list-v0",
                "eval_id": f"legacy-{path.stem}",
                "coverage_requirements": {},
                "metric_thresholds": {},
                "cases": cases,
            },
            cases,
            True,
        )
    if payload.get("schema_version") != RETRIEVAL_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported retrieval eval schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    if not str(payload.get("eval_id") or "").strip():
        raise ValueError("Retrieval eval contract missing 'eval_id'.")
    if not isinstance(payload.get("coverage_requirements"), dict):
        raise ValueError("Retrieval eval contract missing 'coverage_requirements'.")
    if not isinstance(payload.get("metric_thresholds"), dict):
        raise ValueError("Retrieval eval contract missing 'metric_thresholds'.")
    _validate_retrieval_coverage_requirements(payload["coverage_requirements"])
    cases = _validated_eval_cases(payload.get("cases"), legacy_format=False)
    return payload, cases, False


def _validated_eval_cases(payload: object, *, legacy_format: bool) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "Retrieval eval file must contain a non-empty JSON list."
            if legacy_format
            else "Retrieval eval contract must contain non-empty cases."
        )
    case_ids = []
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Retrieval eval case {index} must be an object.")
        for field in ("id", "query"):
            if not case.get(field):
                raise ValueError(f"Retrieval eval case {index} is missing {field!r}.")
        case_ids.append(str(case["id"]))
        _validate_optional_string_list(case, "expected_source_record_ids", index)
        _validate_optional_string_list(case, "expected_terms", index)
        _validate_optional_string_list(case, "forbidden_source_record_ids", index)
        _validate_optional_bool(case, "expect_no_hits", index)
        _validate_optional_bool(case, "hard_negative", index)
        _validate_optional_bool(case, "multi_source", index)
        _validate_positive_eval_int(case, "min_hits", index)
        _validate_positive_eval_int(case, "top_k", index)
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise ValueError(f"Duplicate retrieval eval case IDs: {duplicates}")
    return payload


def _validate_retrieval_coverage_requirements(requirements: dict) -> None:
    for key in (
        "case_count",
        "hard_negative_case_count",
        "multi_source_case_count",
    ):
        value = requirements.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"Retrieval eval coverage_requirements.{key} must be a non-negative integer."
            )


def _validate_optional_string_list(case: dict, field: str, index: int) -> None:
    if field not in case:
        return
    values = case.get(field)
    if not isinstance(values, list) or any(not str(value).strip() for value in values):
        raise ValueError(f"Retrieval eval case {index} {field} must be a non-empty string list.")


def _validate_optional_bool(case: dict, field: str, index: int) -> None:
    if field in case and not isinstance(case[field], bool):
        raise ValueError(f"Retrieval eval case {index} {field} must be a boolean.")


def _validate_positive_eval_int(case: dict, field: str, index: int) -> None:
    if field not in case:
        return
    value = case[field]
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Retrieval eval case {index} {field} must be a non-negative integer.")


def _source_set_id_from_index_path(index_path: Path) -> str:
    if index_path.parent.name != "retrieval":
        raise ValueError(f"Retrieval index path must live under a retrieval directory: {index_path}")
    return index_path.parent.parent.name


def _matched_expected_source_record_ids(expected_sources: list[str], hits: list[dict]) -> list[str]:
    return [
        source_id
        for source_id in expected_sources
        if source_id in {hit["source_record_id"] for hit in hits}
    ]


def _dedupe(values: object) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _retrieval_relevance(hits: list[dict], expected_sources: list[str]) -> list[bool]:
    if not expected_sources:
        return [False for _ in hits]
    remaining = set(expected_sources)
    relevance = []
    for hit in hits:
        source_record_id = str(hit.get("source_record_id") or "")
        is_relevant = source_record_id in remaining
        relevance.append(is_relevant)
        if is_relevant:
            remaining.remove(source_record_id)
    return relevance


def _retrieval_coverage_check(
    contract: dict,
    case_results: list[dict],
    *,
    legacy_format: bool,
) -> dict:
    if legacy_format:
        return {
            "name": "coverage_requirements_met",
            "passed": True,
            "details": {"enabled": False, "legacy_format": True},
        }
    requirements = contract.get("coverage_requirements", {})
    actuals = {
        "case_count": len(case_results),
        "hard_negative_case_count": sum(1 for case in case_results if case["hard_negative"]),
        "multi_source_case_count": sum(1 for case in case_results if case["multi_source"]),
    }
    failures = [
        {
            "requirement": key,
            "min": int(requirements.get(key) or 0),
            "actual": actuals[key],
        }
        for key in actuals
        if actuals[key] < int(requirements.get(key) or 0)
    ]
    return {
        "name": "coverage_requirements_met",
        "passed": not failures,
        "details": {
            "enabled": True,
            "requirements": requirements,
            "actuals": actuals,
            "failures": failures,
        },
    }


def _expected_terms_found(expected_terms: list[str], hits: list[dict]) -> bool:
    return not _missing_expected_terms(expected_terms, hits)


def _missing_expected_terms(expected_terms: list[str], hits: list[dict]) -> list[str]:
    haystack = "\n".join(
        " ".join(
            [
                hit.get("title", ""),
                hit.get("citation_label", ""),
                hit.get("evidence_span", {}).get("text", ""),
                " ".join(hit.get("review_topics", [])),
            ]
        )
        for hit in hits
    ).lower()
    return [term for term in expected_terms if term.lower() not in haystack]


def _eval_failure_reasons(
    *,
    expect_no_hits: bool,
    min_hits_met: bool,
    source_hit: bool,
    term_hit: bool,
    provenance_supported: bool,
    top_rank_false_positive: bool,
    unexpected_sources: list[str],
) -> list[str]:
    reasons = []
    if expect_no_hits:
        if not source_hit:
            reasons.append("expected_zero_hits")
        if top_rank_false_positive:
            reasons.append("unexpected_hit_returned")
        return reasons
    if not min_hits_met:
        reasons.append("min_hits_not_met")
    if not source_hit:
        reasons.append("expected_source_not_retrieved")
    if not term_hit:
        reasons.append("expected_terms_not_retrieved")
    if not provenance_supported:
        reasons.append("citation_provenance_missing")
    if top_rank_false_positive:
        reasons.append("top_rank_not_relevant")
    if unexpected_sources:
        reasons.append("forbidden_source_retrieved")
    return reasons


def _hit_has_required_provenance(hit: dict) -> bool:
    provenance = hit.get("provenance") or {}
    span = hit.get("evidence_span") or {}
    required = [
        "artifact_sha256",
        "artifact_path",
        "parser_name",
        "parser_version",
        "char_start",
        "char_end",
        "content_sha256",
    ]
    return bool(hit.get("citation_label")) and bool(span.get("text")) and all(
        provenance.get(field) not in (None, "") for field in required
    )


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    source_set_id = manifest.get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
