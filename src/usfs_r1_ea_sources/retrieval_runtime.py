from __future__ import annotations

from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from .catalog_surface import catalog_source_record_ids as read_catalog_source_record_ids
from .catalog_surface import catalog_source_set_id as read_catalog_source_set_id
from .catalog_surface import resolve_catalog_dir_for_source_set
from .chunk_layers import contextual_index_text
from .extraction_admission import matched_verified_extraction_contracts
from .retrieval_common import (
    DEFAULT_INDEX_FILENAME,
    INDEX_SCHEMA_VERSION,
    RetrievalIndexBuildResult,
    _int_from_summary,
    _read_json,
    _read_jsonl,
    _utc_now,
    _write_json,
)
from .retrieval_validation import (
    _extraction_summary_is_complete,
    _sqlite_index_checks,
    _validation_report,
    _with_additional_checks,
)
from .source_set_support import (
    load_support_document_role_overrides,
    resolve_support_document_role,
    source_derived_dir,
)


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
        from .retrieval_common import _source_set_id_from_catalog

        source_set_id = _source_set_id_from_catalog(output_dir)
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    index_dir = derived_source_dir / "retrieval"
    index_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_path or derived_source_dir / "chunks" / "chunks.jsonl"
    resolved_catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    catalog_sqlite_path = catalog_sqlite_path or resolved_catalog_dir / "review_sources.sqlite"
    catalog_source_set_value = read_catalog_source_set_id(catalog_sqlite_path.parent)
    catalog_source_record_ids = read_catalog_source_record_ids(catalog_sqlite_path.parent)
    extraction_validation_path = derived_source_dir / "diagnostics" / "extraction_validation.json"
    extraction_manifest_path = derived_source_dir / "diagnostics" / "extraction_manifest.jsonl"
    extraction_summary_path = derived_source_dir / "diagnostics" / "summary.json"
    extraction_accuracy_path = derived_source_dir / "diagnostics" / "extraction_accuracy_audit.json"
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
        "verified_extraction_explicitly_non_admitted_source_count": len(
            verified_extraction_requirements["non_admitted_source_record_ids"]
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
                    INSERT INTO chunks_fts(
                      rowid, text, contextual_index_text, title, heading, citation_label
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rowid,
                        chunk.get("text") or "",
                        chunk.get("contextual_index_text") or "",
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
          chunk_layer TEXT,
          parent_chunk_id TEXT,
          parent_window_id TEXT,
          page_range_json TEXT NOT NULL,
          structure_type TEXT,
          component_type TEXT,
          contextual_index_text TEXT NOT NULL,
          contextual_index_sha256 TEXT,
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
              contextual_index_text,
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
    contextual_text = str(chunk.get("contextual_index_text") or contextual_index_text(chunk))
    contextual_sha256 = chunk.get("contextual_index_sha256") or _sha256(contextual_text)
    cursor = connection.execute(
        """
        INSERT INTO chunks (
          chunk_id, source_set_id, source_record_id, chunk_index, title, document_role,
          support_document_role, authority_level, host, expected_parser, artifact_sha256, artifact_path,
          citation_label, original_url, effective_url, final_url, parser_name,
          parser_version, extracted_at, source_text_path, char_start, char_end, page,
          section, heading, chunk_layer, parent_chunk_id, parent_window_id, page_range_json,
          structure_type, component_type, contextual_index_text, contextual_index_sha256,
          content_sha256, review_topics_json, text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            chunk.get("chunk_layer") or "baseline_text_chunk_v1",
            chunk.get("parent_chunk_id"),
            chunk.get("parent_window_id"),
            json.dumps(chunk.get("page_range"), sort_keys=True),
            chunk.get("structure_type") or "text_span",
            chunk.get("component_type"),
            contextual_text,
            contextual_sha256,
            chunk["content_sha256"],
            json.dumps(chunk.get("review_topics", []), sort_keys=True),
            chunk["text"],
        ),
    )
    return int(cursor.lastrowid)


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
    support_document_role_overrides = load_support_document_role_overrides()
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
                role = resolve_support_document_role(
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
    merged.setdefault("chunk_layer", "baseline_text_chunk_v1")
    merged.setdefault("structure_type", "text_span")
    merged["contextual_index_text"] = merged.get("contextual_index_text") or contextual_index_text(
        merged
    )
    merged["contextual_index_sha256"] = merged.get("contextual_index_sha256") or _sha256(
        str(merged["contextual_index_text"])
    )
    return merged


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
