from __future__ import annotations

from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json
import sqlite3
import subprocess

from .config import DownloaderConfig
from .records import WorkbookSource, sha256_file, slugify
from .report import _read_jsonl, _resolve_manifest_path
from .source_partitions import catalog_source_partition
from .workbook import load_canonical_sources


@dataclass(frozen=True)
class CatalogBuildResult:
    source_set_id: str
    catalog_dir: Path
    source_catalog_path: Path
    source_set_manifest_path: Path
    validation_path: Path
    sqlite_path: Path
    graph_nodes_path: Path
    graph_edges_path: Path
    summary: dict


def build_review_catalog(
    *,
    workbook_path: Path,
    output_dir: Path,
    config: DownloaderConfig,
    config_path: Path | None = None,
    run_id: str | None = None,
    batch_run_id: str | None = None,
) -> CatalogBuildResult:
    if run_id and batch_run_id:
        raise ValueError("run_id and batch_run_id are mutually exclusive")
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    source_catalog_path = catalog_dir / "source_catalog.jsonl"
    source_set_manifest_path = catalog_dir / "source_set_manifest.json"
    validation_path = catalog_dir / "catalog_validation.json"
    sqlite_path = catalog_dir / "review_sources.sqlite"
    graph_nodes_path = catalog_dir / "source_graph_nodes.jsonl"
    graph_edges_path = catalog_dir / "source_graph_edges.jsonl"

    workbook_sha256 = sha256_file(workbook_path)
    config_sha256 = sha256_file(config_path) if config_path and config_path.exists() else None
    overrides_sha256 = _optional_sha256(config.workbook.overrides_path)
    git_commit = _git_commit(workbook_path.parent)
    source_set_id = _source_set_id(
        workbook_sha256=workbook_sha256,
        config_sha256=config_sha256,
        overrides_sha256=overrides_sha256,
        run_id=run_id,
        batch_run_id=batch_run_id,
        git_commit=git_commit,
    )

    sources = load_canonical_sources(workbook_path, config.workbook)
    manifest_records, manifest_load_checks = _load_manifest_records(
        output_dir,
        run_id,
        batch_run_id,
        sources,
    )
    catalog_records = [
        _catalog_record(
            source_set_id=source_set_id,
            source=source,
            manifest_record=manifest_records.get(source.source_record_id),
            run_id=run_id,
            batch_run_id=batch_run_id,
        )
        for source in sources
    ]
    manifest = _source_set_manifest(
        source_set_id=source_set_id,
        workbook_path=workbook_path,
        workbook_sha256=workbook_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        overrides_path=config.workbook.overrides_path,
        overrides_sha256=overrides_sha256,
        git_commit=git_commit,
        run_id=run_id,
        batch_run_id=batch_run_id,
        records=catalog_records,
    )
    graph_nodes, graph_edges = _graph_records(catalog_records)
    validation_report = _validation_report(
        source_set_id=source_set_id,
        records=catalog_records,
        manifest_load_checks=manifest_load_checks,
    )

    _write_jsonl(source_catalog_path, catalog_records)
    _write_json(source_set_manifest_path, manifest)
    _write_json(validation_path, validation_report)
    _write_jsonl(graph_nodes_path, graph_nodes)
    _write_jsonl(graph_edges_path, graph_edges)
    _write_sqlite(sqlite_path, manifest, catalog_records)

    summary = {
        "source_set_id": source_set_id,
        "source_count": len(catalog_records),
        "artifact_count": _artifact_count(catalog_records),
        "unique_url_count": len({record["normalized_url"] for record in catalog_records}),
        "review_topic_count": _review_topic_count(catalog_records),
        "authority_count": _authority_count(catalog_records),
        "source_partition_counts": manifest["source_partition_counts"],
        "download_run_id": run_id,
        "download_batch_run_id": batch_run_id,
        "validation_passed": validation_report["passed"],
        "validation_path": str(validation_path),
        "source_catalog_path": str(source_catalog_path),
        "source_set_manifest_path": str(source_set_manifest_path),
        "sqlite_path": str(sqlite_path),
        "graph_nodes_path": str(graph_nodes_path),
        "graph_edges_path": str(graph_edges_path),
    }
    return CatalogBuildResult(
        source_set_id=source_set_id,
        catalog_dir=catalog_dir,
        source_catalog_path=source_catalog_path,
        source_set_manifest_path=source_set_manifest_path,
        validation_path=validation_path,
        sqlite_path=sqlite_path,
        graph_nodes_path=graph_nodes_path,
        graph_edges_path=graph_edges_path,
        summary=summary,
    )


def _catalog_record(
    *,
    source_set_id: str,
    source: WorkbookSource,
    manifest_record: dict | None,
    run_id: str | None,
    batch_run_id: str | None,
) -> dict:
    metadata = source.metadata
    host = urlsplit(source.normalized_url).netloc.lower()
    document_type = _clean(metadata.get("document_type"))
    issuer = _clean(metadata.get("issuer"))
    applies_to = _first_nonempty(metadata.get("applies_to"), metadata.get("applies_when"))
    review_engine_checks = _clean(metadata.get("review_engine_checks"))
    review_topics = _review_topics(review_engine_checks)
    artifact_sha256 = _from_manifest(manifest_record, "artifact_sha256")
    content_type = _from_manifest(manifest_record, "content_type")
    source_status = _source_status(manifest_record, bool(run_id or batch_run_id))
    artifact_run_id = _from_manifest(manifest_record, "run_id") or run_id
    record = {
        "source_set_id": source_set_id,
        "source_record_id": source.source_record_id,
        "sheet": source.sheet,
        "excel_row": source.excel_row,
        "source_id": source.source_id,
        "title": source.title,
        "document_role": _document_role(source, document_type),
        "authority_level": _authority_level(source, issuer, host),
        "issuer": issuer,
        "scope": _clean(metadata.get("scope")),
        "layer": _clean(metadata.get("layer")),
        "document_type": document_type,
        "unit_or_overlay": _clean(metadata.get("unit_or_overlay")),
        "applies_to": applies_to,
        "trigger": _clean(metadata.get("trigger")),
        "review_engine_checks": review_engine_checks,
        "review_topics": review_topics,
        "currentness_notes": _clean(metadata.get("currentness_notes")),
        "original_url": source.original_url,
        "effective_url": source.effective_url,
        "normalized_url": source.normalized_url,
        "host": host,
        "expected_parser": _expected_parser(source, content_type),
        "source_status": source_status,
        "download_run_id": artifact_run_id,
        "download_batch_run_id": batch_run_id,
        "final_url": _from_manifest(manifest_record, "final_url"),
        "artifact_sha256": artifact_sha256,
        "artifact_path": _from_manifest(manifest_record, "artifact_path"),
        "artifact_byte_size": _from_manifest(manifest_record, "artifact_byte_size"),
        "content_type": content_type,
        "retrieved_at": _from_manifest(manifest_record, "fetch_timestamp"),
        "duplicate_of": _from_manifest(manifest_record, "duplicate_of"),
        "citation_label": _citation_label(source, artifact_sha256),
        "metadata": metadata,
    }
    source_partition, source_partition_basis = catalog_source_partition(record)
    record["source_partition"] = source_partition
    record["source_partition_basis"] = source_partition_basis
    return record


def _source_set_manifest(
    *,
    source_set_id: str,
    workbook_path: Path,
    workbook_sha256: str,
    config_path: Path | None,
    config_sha256: str | None,
    overrides_path: Path | None,
    overrides_sha256: str | None,
    git_commit: str | None,
    run_id: str | None,
    batch_run_id: str | None,
    records: list[dict],
) -> dict:
    status_counts = Counter(record["source_status"] for record in records)
    role_counts = Counter(record["document_role"] for record in records)
    host_counts = Counter(record["host"] for record in records)
    parser_counts = Counter(record["expected_parser"] for record in records)
    source_partition_counts = Counter(record["source_partition"] for record in records)
    return {
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "config_path": str(config_path) if config_path else None,
        "config_sha256": config_sha256,
        "overrides_path": str(overrides_path) if overrides_path else None,
        "overrides_sha256": overrides_sha256,
        "git_commit": git_commit,
        "download_run_id": run_id,
        "download_batch_run_id": batch_run_id,
        "source_count": len(records),
        "unique_url_count": len({record["normalized_url"] for record in records}),
        "artifact_count": _artifact_count(records),
        "review_topic_count": _review_topic_count(records),
        "authority_count": len({record["issuer"] for record in records if record["issuer"]}),
        "status_counts": dict(status_counts),
        "source_partition_counts": dict(source_partition_counts),
        "document_role_counts": dict(role_counts),
        "host_counts": dict(host_counts),
        "expected_parser_counts": dict(parser_counts),
    }


def _write_sqlite(path: Path, manifest: dict, records: list[dict]) -> None:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_schema(connection)
        _insert_source_set(connection, manifest)
        for record in records:
            _insert_source(connection, record)
            _insert_artifact(connection, record)
            _insert_authority(connection, record)
            _insert_applicability(connection, record)
            _insert_review_topics(connection, record)
            _insert_citation(connection, record)
        connection.commit()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE source_sets (
          source_set_id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          workbook_sha256 TEXT NOT NULL,
          config_sha256 TEXT,
          overrides_sha256 TEXT,
          git_commit TEXT,
          download_run_id TEXT,
          download_batch_run_id TEXT,
          source_count INTEGER NOT NULL,
          unique_url_count INTEGER NOT NULL,
          artifact_count INTEGER NOT NULL
        );

        CREATE TABLE sources (
          source_record_id TEXT PRIMARY KEY,
          source_set_id TEXT NOT NULL,
          sheet TEXT NOT NULL,
          excel_row INTEGER NOT NULL,
          source_id TEXT,
          title TEXT NOT NULL,
          document_role TEXT NOT NULL,
          authority_level TEXT NOT NULL,
          issuer TEXT,
          scope TEXT,
          layer TEXT,
          document_type TEXT,
          unit_or_overlay TEXT,
          applies_to TEXT,
          trigger TEXT,
          review_engine_checks TEXT,
          currentness_notes TEXT,
          original_url TEXT NOT NULL,
          effective_url TEXT NOT NULL,
          normalized_url TEXT NOT NULL,
          host TEXT NOT NULL,
          expected_parser TEXT NOT NULL,
          source_status TEXT NOT NULL,
          source_partition TEXT NOT NULL,
          source_partition_basis TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          FOREIGN KEY (source_set_id) REFERENCES source_sets(source_set_id)
        );

        CREATE TABLE artifacts (
          artifact_sha256 TEXT PRIMARY KEY,
          artifact_path TEXT NOT NULL,
          artifact_byte_size INTEGER,
          content_type TEXT,
          retrieved_at TEXT,
          final_url TEXT
        );

        CREATE TABLE source_artifacts (
          source_record_id TEXT NOT NULL,
          artifact_sha256 TEXT NOT NULL,
          download_run_id TEXT,
          source_status TEXT NOT NULL,
          PRIMARY KEY (source_record_id, artifact_sha256),
          FOREIGN KEY (source_record_id) REFERENCES sources(source_record_id),
          FOREIGN KEY (artifact_sha256) REFERENCES artifacts(artifact_sha256)
        );

        CREATE TABLE authorities (
          authority_id TEXT PRIMARY KEY,
          authority_name TEXT NOT NULL,
          authority_level TEXT NOT NULL
        );

        CREATE TABLE source_authorities (
          source_record_id TEXT NOT NULL,
          authority_id TEXT NOT NULL,
          PRIMARY KEY (source_record_id, authority_id),
          FOREIGN KEY (source_record_id) REFERENCES sources(source_record_id),
          FOREIGN KEY (authority_id) REFERENCES authorities(authority_id)
        );

        CREATE TABLE applicability (
          applicability_id TEXT PRIMARY KEY,
          source_record_id TEXT NOT NULL,
          applies_to TEXT,
          scope TEXT,
          unit_or_overlay TEXT,
          layer TEXT,
          FOREIGN KEY (source_record_id) REFERENCES sources(source_record_id)
        );

        CREATE TABLE review_topics (
          topic_id TEXT PRIMARY KEY,
          label TEXT NOT NULL
        );

        CREATE TABLE source_review_topics (
          source_record_id TEXT NOT NULL,
          topic_id TEXT NOT NULL,
          PRIMARY KEY (source_record_id, topic_id),
          FOREIGN KEY (source_record_id) REFERENCES sources(source_record_id),
          FOREIGN KEY (topic_id) REFERENCES review_topics(topic_id)
        );

        CREATE TABLE citations (
          source_record_id TEXT PRIMARY KEY,
          citation_label TEXT NOT NULL,
          title TEXT NOT NULL,
          artifact_sha256 TEXT,
          original_url TEXT NOT NULL,
          final_url TEXT,
          retrieved_at TEXT,
          FOREIGN KEY (source_record_id) REFERENCES sources(source_record_id)
        );

        CREATE INDEX idx_sources_host ON sources(host);
        CREATE INDEX idx_sources_role ON sources(document_role);
        CREATE INDEX idx_sources_authority_level ON sources(authority_level);
        CREATE INDEX idx_sources_parser ON sources(expected_parser);
        CREATE INDEX idx_sources_status ON sources(source_status);
        CREATE INDEX idx_sources_source_partition ON sources(source_partition);
        CREATE INDEX idx_source_review_topics_topic ON source_review_topics(topic_id);
        CREATE INDEX idx_source_artifacts_artifact ON source_artifacts(artifact_sha256);
        """
    )


def _insert_source_set(connection: sqlite3.Connection, manifest: dict) -> None:
    connection.execute(
        """
        INSERT INTO source_sets (
          source_set_id, created_at, workbook_sha256, config_sha256, overrides_sha256,
          git_commit, download_run_id, download_batch_run_id, source_count, unique_url_count,
          artifact_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            manifest["source_set_id"],
            manifest["created_at"],
            manifest["workbook_sha256"],
            manifest.get("config_sha256"),
            manifest.get("overrides_sha256"),
            manifest.get("git_commit"),
            manifest.get("download_run_id"),
            manifest.get("download_batch_run_id"),
            manifest["source_count"],
            manifest["unique_url_count"],
            manifest["artifact_count"],
        ),
    )


def _insert_source(connection: sqlite3.Connection, record: dict) -> None:
    connection.execute(
        """
        INSERT INTO sources (
          source_record_id, source_set_id, sheet, excel_row, source_id, title,
          document_role, authority_level, issuer, scope, layer, document_type,
          unit_or_overlay, applies_to, trigger, review_engine_checks, currentness_notes,
          original_url, effective_url, normalized_url, host, expected_parser, source_status,
          source_partition, source_partition_basis, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["source_record_id"],
            record["source_set_id"],
            record["sheet"],
            record["excel_row"],
            record["source_id"],
            record["title"],
            record["document_role"],
            record["authority_level"],
            record["issuer"],
            record["scope"],
            record["layer"],
            record["document_type"],
            record["unit_or_overlay"],
            record["applies_to"],
            record["trigger"],
            record["review_engine_checks"],
            record["currentness_notes"],
            record["original_url"],
            record["effective_url"],
            record["normalized_url"],
            record["host"],
            record["expected_parser"],
            record["source_status"],
            record["source_partition"],
            record["source_partition_basis"],
            json.dumps(record["metadata"], sort_keys=True),
        ),
    )


def _insert_artifact(connection: sqlite3.Connection, record: dict) -> None:
    if not record["artifact_sha256"]:
        return
    connection.execute(
        """
        INSERT OR IGNORE INTO artifacts (
          artifact_sha256, artifact_path, artifact_byte_size, content_type, retrieved_at, final_url
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            record["artifact_sha256"],
            record["artifact_path"],
            record["artifact_byte_size"],
            record["content_type"],
            record["retrieved_at"],
            record["final_url"],
        ),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO source_artifacts (
          source_record_id, artifact_sha256, download_run_id, source_status
        ) VALUES (?, ?, ?, ?)
        """,
        (
            record["source_record_id"],
            record["artifact_sha256"],
            record["download_run_id"],
            record["source_status"],
        ),
    )


def _insert_authority(connection: sqlite3.Connection, record: dict) -> None:
    issuer = record["issuer"]
    if not issuer:
        return
    authority_id = f"authority:{slugify(issuer, max_length=96)}"
    connection.execute(
        "INSERT OR IGNORE INTO authorities VALUES (?, ?, ?)",
        (authority_id, issuer, record["authority_level"]),
    )
    connection.execute(
        "INSERT OR IGNORE INTO source_authorities VALUES (?, ?)",
        (record["source_record_id"], authority_id),
    )


def _insert_applicability(connection: sqlite3.Connection, record: dict) -> None:
    if not any([record["applies_to"], record["scope"], record["unit_or_overlay"], record["layer"]]):
        return
    applicability_id = f"applicability:{record['source_record_id']}"
    connection.execute(
        "INSERT OR IGNORE INTO applicability VALUES (?, ?, ?, ?, ?, ?)",
        (
            applicability_id,
            record["source_record_id"],
            record["applies_to"],
            record["scope"],
            record["unit_or_overlay"],
            record["layer"],
        ),
    )


def _insert_review_topics(connection: sqlite3.Connection, record: dict) -> None:
    for topic in record["review_topics"]:
        topic_id = f"topic:{slugify(topic, max_length=96)}"
        connection.execute("INSERT OR IGNORE INTO review_topics VALUES (?, ?)", (topic_id, topic))
        connection.execute(
            "INSERT OR IGNORE INTO source_review_topics VALUES (?, ?)",
            (record["source_record_id"], topic_id),
        )


def _insert_citation(connection: sqlite3.Connection, record: dict) -> None:
    connection.execute(
        "INSERT OR REPLACE INTO citations VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            record["source_record_id"],
            record["citation_label"],
            record["title"],
            record["artifact_sha256"],
            record["original_url"],
            record["final_url"],
            record["retrieved_at"],
        ),
    )


def _graph_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    nodes_by_id: dict[str, dict] = {}
    edges_by_id: dict[str, dict] = {}
    for record in records:
        source_node_id = f"source:{record['source_record_id']}"
        nodes_by_id[source_node_id] = {
            "id": source_node_id,
            "type": "Source",
            "source_record_id": record["source_record_id"],
            "title": record["title"],
            "document_role": record["document_role"],
            "authority_level": record["authority_level"],
            "source_partition": record["source_partition"],
        }
        if record["issuer"]:
            authority_node_id = f"authority:{slugify(record['issuer'], max_length=96)}"
            nodes_by_id.setdefault(
                authority_node_id,
                {"id": authority_node_id, "type": "Authority", "name": record["issuer"]},
            )
            edge = _edge(source_node_id, authority_node_id, "ISSUED_BY")
            edges_by_id[edge["id"]] = edge
        if record["applies_to"]:
            applies_node_id = f"applicability:{slugify(record['applies_to'], max_length=96)}"
            nodes_by_id.setdefault(
                applies_node_id,
                {"id": applies_node_id, "type": "Applicability", "label": record["applies_to"]},
            )
            edge = _edge(source_node_id, applies_node_id, "APPLIES_TO")
            edges_by_id[edge["id"]] = edge
        for topic in record["review_topics"]:
            topic_node_id = f"topic:{slugify(topic, max_length=96)}"
            nodes_by_id.setdefault(
                topic_node_id,
                {"id": topic_node_id, "type": "ReviewTopic", "label": topic},
            )
            edge = _edge(source_node_id, topic_node_id, "SUPPORTS_REVIEW_TOPIC")
            edges_by_id[edge["id"]] = edge
        if record["artifact_sha256"]:
            artifact_node_id = f"artifact:{record['artifact_sha256']}"
            nodes_by_id.setdefault(
                artifact_node_id,
                {"id": artifact_node_id, "type": "Artifact", "sha256": record["artifact_sha256"]},
            )
            edge = _edge(source_node_id, artifact_node_id, "HAS_ARTIFACT")
            edges_by_id[edge["id"]] = edge
    return list(nodes_by_id.values()), list(edges_by_id.values())


def _edge(source_id: str, target_id: str, relationship: str) -> dict:
    edge_id = f"{source_id}|{relationship}|{target_id}"
    return {"id": edge_id, "source": source_id, "target": target_id, "relationship": relationship}


def _load_manifest_records(
    output_dir: Path,
    run_id: str | None,
    batch_run_id: str | None,
    sources: list[WorkbookSource],
) -> tuple[dict[str, dict], list[dict]]:
    if not run_id and not batch_run_id:
        return {}, []
    if run_id:
        return _load_single_manifest_records(output_dir, run_id, sources)
    if not batch_run_id:
        return {}, []
    return _load_batch_manifest_records(output_dir, batch_run_id, sources)


def _load_single_manifest_records(
    output_dir: Path,
    run_id: str,
    sources: list[WorkbookSource],
) -> tuple[dict[str, dict], list[dict]]:
    source_ids = {source.source_record_id for source in sources}
    summary_path = output_dir / "runs" / run_id / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing run summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_path = _resolve_manifest_path(output_dir, summary)
    records_by_id: dict[str, dict] = {}
    duplicate_ids = []
    unknown_ids = []
    for record in _read_jsonl(manifest_path):
        source_record_id = str(record.get("source_record_id") or "")
        if source_record_id in records_by_id:
            duplicate_ids.append(source_record_id)
        if source_record_id not in source_ids:
            unknown_ids.append(source_record_id)
        records_by_id[source_record_id] = record
    checks = [
        {
            "name": "download_manifest_has_no_duplicate_source_records",
            "passed": not duplicate_ids,
            "details": {"duplicate_source_record_ids": sorted(set(duplicate_ids))},
        },
        {
            "name": "download_manifest_source_records_are_in_workbook",
            "passed": not unknown_ids,
            "details": {"unknown_source_record_ids": sorted(set(unknown_ids))},
        },
    ]
    return records_by_id, checks


def _load_batch_manifest_records(
    output_dir: Path,
    batch_run_id: str,
    sources: list[WorkbookSource],
) -> tuple[dict[str, dict], list[dict]]:
    source_ids = {source.source_record_id for source in sources}
    summary_path = output_dir / "runs" / batch_run_id / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing batch run summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    ledger_path = _resolve_existing_path(
        output_dir,
        summary.get("ledger_path"),
        output_dir / "runs" / batch_run_id / "batch_ledger.json",
    )
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    records_by_id: dict[str, dict] = {}
    duplicate_ids = []
    unknown_ids = []
    missing_manifest_batches = []
    non_passed_batches = []
    row_mismatches = []

    for batch in ledger.get("batches", []):
        batch_id = str(batch.get("batch_id") or "")
        if batch.get("status") != "passed" or batch.get("gate_passed") is not True:
            non_passed_batches.append(batch_id)
            continue
        manifest_path = _resolve_existing_path(output_dir, batch.get("manifest_path"), None)
        if not manifest_path or not manifest_path.exists():
            missing_manifest_batches.append(batch_id)
            continue
        manifest_source_ids = set()
        for record in _read_jsonl(manifest_path):
            source_record_id = str(record.get("source_record_id") or "")
            manifest_source_ids.add(source_record_id)
            if source_record_id in records_by_id:
                duplicate_ids.append(source_record_id)
            if source_record_id not in source_ids:
                unknown_ids.append(source_record_id)
            records_by_id[source_record_id] = {**record, "download_batch_run_id": batch_run_id}
        ledger_source_ids = {str(source_id) for source_id in batch.get("source_record_ids", [])}
        if ledger_source_ids and manifest_source_ids != ledger_source_ids:
            row_mismatches.append(
                {
                    "batch_id": batch_id,
                    "missing_source_record_ids": sorted(ledger_source_ids - manifest_source_ids),
                    "unexpected_source_record_ids": sorted(manifest_source_ids - ledger_source_ids),
                }
            )

    checks = [
        {
            "name": "batch_download_parent_passed",
            "passed": bool(summary.get("all_passed")) and not non_passed_batches,
            "details": {
                "batch_run_id": batch_run_id,
                "all_passed": bool(summary.get("all_passed")),
                "non_passed_batch_ids": sorted(set(non_passed_batches)),
            },
        },
        {
            "name": "batch_download_manifests_exist",
            "passed": not missing_manifest_batches,
            "details": {"missing_manifest_batch_ids": sorted(set(missing_manifest_batches))},
        },
        {
            "name": "batch_download_manifest_rows_match_ledger",
            "passed": not row_mismatches,
            "details": {"mismatches": row_mismatches},
        },
        {
            "name": "download_manifest_has_no_duplicate_source_records",
            "passed": not duplicate_ids,
            "details": {"duplicate_source_record_ids": sorted(set(duplicate_ids))},
        },
        {
            "name": "download_manifest_source_records_are_in_workbook",
            "passed": not unknown_ids,
            "details": {"unknown_source_record_ids": sorted(set(unknown_ids))},
        },
    ]
    return records_by_id, checks


def _resolve_existing_path(output_dir: Path, value: str | None, fallback: Path | None) -> Path | None:
    candidates: list[Path] = []
    if value:
        path = Path(value)
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.extend([path, output_dir / path, output_dir.parent / path])
    if fallback:
        candidates.append(fallback)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return fallback


def _validation_report(
    *,
    source_set_id: str,
    records: list[dict],
    manifest_load_checks: list[dict],
) -> dict:
    checks = [
        _check_unique_source_records(records),
        _check_required_reviewer_fields(records),
        _check_artifact_metadata(records),
        _check_review_graph_links(records),
        *manifest_load_checks,
    ]
    return {
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_unique_source_records(records: list[dict]) -> dict:
    counts = Counter(record["source_record_id"] for record in records)
    duplicates = sorted(source_id for source_id, count in counts.items() if count > 1)
    return {
        "name": "source_record_ids_are_unique",
        "passed": not duplicates,
        "details": {"duplicate_source_record_ids": duplicates},
    }


def _check_required_reviewer_fields(records: list[dict]) -> dict:
    required = [
        "source_set_id",
        "source_record_id",
        "title",
        "document_role",
        "authority_level",
        "original_url",
        "effective_url",
        "normalized_url",
        "host",
        "expected_parser",
        "source_status",
        "citation_label",
    ]
    failures = []
    for record in records:
        missing = [field for field in required if not record.get(field)]
        if missing:
            failures.append(
                {
                    "source_record_id": record.get("source_record_id"),
                    "missing_fields": missing,
                }
            )
    return {
        "name": "required_reviewer_fields_are_present",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_artifact_metadata(records: list[dict]) -> dict:
    failures = []
    success_statuses = {"downloaded", "downloaded_existing", "duplicate_content"}
    for record in records:
        if record["source_status"] not in success_statuses:
            continue
        missing = [
            field
            for field in ["artifact_sha256", "artifact_path", "artifact_byte_size", "content_type"]
            if not record.get(field)
        ]
        if missing:
            failures.append(_artifact_validation_failure(record, f"missing fields: {', '.join(missing)}"))
            continue
        path = Path(str(record["artifact_path"]))
        if not path.exists():
            failures.append(_artifact_validation_failure(record, "artifact_path does not exist"))
            continue
        if path.stat().st_size != record["artifact_byte_size"]:
            failures.append(_artifact_validation_failure(record, "artifact_byte_size mismatch"))
        digest = sha256_file(path)
        if digest != record["artifact_sha256"]:
            failures.append(_artifact_validation_failure(record, "artifact_sha256 mismatch"))
    return {
        "name": "successful_sources_have_valid_artifact_metadata",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_review_graph_links(records: list[dict]) -> dict:
    failures = []
    for record in records:
        if not record["review_topics"]:
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "reason": "missing review_topics",
                }
            )
        if record["document_role"] == "source_document":
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "reason": "unclassified document_role",
                }
            )
        if record["authority_level"] == "unknown":
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "reason": "unknown authority_level",
                }
            )
    return {
        "name": "sources_have_review_graph_links",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _artifact_validation_failure(record: dict, reason: str) -> dict:
    return {
        "source_record_id": record.get("source_record_id"),
        "source_status": record.get("source_status"),
        "artifact_path": record.get("artifact_path"),
        "reason": reason,
    }


def _source_set_id(
    *,
    workbook_sha256: str,
    config_sha256: str | None,
    overrides_sha256: str | None,
    run_id: str | None,
    batch_run_id: str | None,
    git_commit: str | None,
) -> str:
    payload = {
        "workbook_sha256": workbook_sha256,
        "config_sha256": config_sha256,
        "overrides_sha256": overrides_sha256,
        "download_run_id": run_id,
        "download_batch_run_id": batch_run_id,
        "git_commit": git_commit,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"source-set-{digest[:16]}"


def _optional_sha256(path: Path | None) -> str | None:
    if path and path.exists():
        return sha256_file(path)
    return None


def _git_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _source_status(manifest_record: dict | None, run_scope_present: bool) -> str:
    if manifest_record:
        return str(manifest_record.get("status") or "unknown")
    return "not_in_run" if run_scope_present else "planned"


def _document_role(source: WorkbookSource, document_type: str | None) -> str:
    if source.sheet == "R1_Forest_Plans":
        return "forest_plan"
    value = (document_type or "").lower()
    title = source.title.lower()
    if "executive order" in value or "executive order" in title:
        return "executive_order"
    if "federal register" in value or "final rule" in value or "final rule" in title:
        return "regulation"
    if "regulation" in value or "cfr" in title:
        return "regulation"
    if "directive" in value or "manual" in value or "supplement" in value:
        return "agency_policy"
    if "agency species page" in value or "agency page" in value:
        return "agency_policy"
    if "public law" in value:
        return "law"
    if "plan amendment" in value:
        return "agency_policy"
    if "statute" in value or "u.s.c" in title or "united states code" in title:
        return "law"
    if "state" in value:
        return "state_requirement"
    if "guidance" in value or "policy" in value or "manual" in title or "handbook" in title:
        return "agency_policy"
    if (
        "official project page" in value
        or "news release" in value
        or "repository" in value
        or "project page" in title
        or "news release" in title
        or "project documents" in title
    ):
        return "project_reference"
    if "case" in value or "court" in title:
        return "case_law"
    return "source_document"


def _authority_level(source: WorkbookSource, issuer: str | None, host: str) -> str:
    if source.sheet == "R1_Forest_Plans":
        return "forest"
    value = (issuer or "").lower()
    if "region 1" in value:
        return "regional"
    state_tokens = ["montana", "idaho", "north dakota", "south dakota", "washington"]
    if any(token in value for token in state_tokens):
        return "state"
    if host.endswith(".mt.gov") or host.endswith(".idaho.gov") or host.endswith(".nd.gov"):
        return "state"
    if host.endswith(".sd.gov") or host.endswith(".wa.gov"):
        return "state"
    federal_tokens = ["congress", "president", "usda", "epa", "u.s.", "army corps"]
    if any(token in value for token in federal_tokens):
        return "federal"
    if host.endswith(".gov"):
        return "federal"
    return "unknown"


def _expected_parser(source: WorkbookSource, content_type: str | None) -> str:
    if content_type:
        if content_type == "application/pdf":
            return "pdf"
        if content_type in {"application/xml", "text/xml"}:
            return "xml"
        if content_type in {"text/html", "application/xhtml+xml"}:
            return "html"
        docx_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if content_type == docx_content_type:
            return "docx"
    path = urlsplit(source.effective_url).path.lower()
    host = urlsplit(source.normalized_url).netloc.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith(".xml"):
        return "xml"
    if path.endswith(".docx"):
        return "docx"
    if host in {"www.ecfr.gov", "www.federalregister.gov"}:
        return "structured_web_adapter"
    return "html"


def _review_topics(value: str | None) -> list[str]:
    if not value:
        return []
    parts = []
    for segment in value.replace("\r", "\n").replace(";", "\n").split("\n"):
        segment = " ".join(segment.split())
        if segment:
            parts.append(segment)
    return parts


def _citation_label(source: WorkbookSource, artifact_sha256: str | None) -> str:
    if artifact_sha256:
        return f"{source.source_record_id} ({artifact_sha256[:12]})"
    return source.source_record_id


def _from_manifest(record: dict | None, key: str):
    return record.get(key) if record else None


def _artifact_count(records: list[dict]) -> int:
    return len({record["artifact_sha256"] for record in records if record["artifact_sha256"]})


def _review_topic_count(records: list[dict]) -> int:
    return len({topic for record in records for topic in record["review_topics"]})


def _authority_count(records: list[dict]) -> int:
    return len({record["issuer"] for record in records if record["issuer"]})


def _first_nonempty(*values: str | None) -> str | None:
    for value in values:
        cleaned = _clean(value)
        if cleaned:
            return cleaned
    return None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
