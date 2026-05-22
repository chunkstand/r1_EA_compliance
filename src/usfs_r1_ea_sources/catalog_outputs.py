from __future__ import annotations

from collections import Counter
from contextlib import closing
from pathlib import Path
import json
import sqlite3

from .capture_run_support import read_jsonl, resolve_manifest_path
from .records import WorkbookSource, sha256_file, slugify


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
    *,
    batch_run_ids: list[str] | None = None,
    sources: list[WorkbookSource],
) -> tuple[dict[str, dict], list[dict]]:
    active_batch_run_ids = list(batch_run_ids or ([batch_run_id] if batch_run_id else []))
    if not run_id and not active_batch_run_ids:
        return {}, []
    if run_id:
        return _load_single_manifest_records(output_dir, run_id, sources)
    if len(active_batch_run_ids) == 1:
        return _load_batch_manifest_records(output_dir, active_batch_run_ids[0], sources)
    return _load_multiple_batch_manifest_records(output_dir, active_batch_run_ids, sources)


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
    manifest_path = resolve_manifest_path(output_dir, summary)
    records_by_id: dict[str, dict] = {}
    duplicate_ids = []
    unknown_ids = []
    for record in read_jsonl(manifest_path):
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
        for record in read_jsonl(manifest_path):
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


def _load_multiple_batch_manifest_records(
    output_dir: Path,
    batch_run_ids: list[str],
    sources: list[WorkbookSource],
) -> tuple[dict[str, dict], list[dict]]:
    records_by_id: dict[str, dict] = {}
    duplicate_ids = []
    checks = [
        {
            "name": "merged_batch_download_parent_count",
            "passed": len(batch_run_ids) >= 2,
            "details": {"batch_run_ids": batch_run_ids, "batch_run_count": len(batch_run_ids)},
        }
    ]
    for batch_run_id in batch_run_ids:
        batch_records_by_id, batch_checks = _load_batch_manifest_records(
            output_dir,
            batch_run_id,
            sources,
        )
        checks.extend(batch_checks)
        for source_record_id, record in batch_records_by_id.items():
            if source_record_id in records_by_id:
                duplicate_ids.append(source_record_id)
            records_by_id[source_record_id] = record

    checks.append(
        {
            "name": "merged_batch_download_manifest_has_no_duplicate_source_records",
            "passed": not duplicate_ids,
            "details": {
                "batch_run_ids": batch_run_ids,
                "duplicate_source_record_ids": sorted(set(duplicate_ids)),
            },
        }
    )
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
    batch_run_ids: list[str],
    source_delta_input: dict | None,
    manifest_load_checks: list[dict],
) -> dict:
    checks = [
        _check_unique_source_records(records),
        _check_required_reviewer_fields(records),
        _check_artifact_metadata(records),
        _check_review_graph_links(records),
        _check_merged_catalog_has_no_not_in_run_records(
            records=records,
            batch_run_ids=batch_run_ids,
            source_delta_input=source_delta_input,
        ),
        *manifest_load_checks,
    ]
    return {
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_merged_catalog_has_no_not_in_run_records(
    *,
    records: list[dict],
    batch_run_ids: list[str],
    source_delta_input: dict | None,
) -> dict:
    not_in_run_ids = sorted(
        record["source_record_id"]
        for record in records
        if record["source_status"] == "not_in_run"
    )
    enabled = len(batch_run_ids) > 1 and source_delta_input is not None
    return {
        "name": "merged_catalog_batch_runs_cover_all_catalog_records",
        "passed": not enabled or not not_in_run_ids,
        "details": {
            "enabled": enabled,
            "batch_run_ids": batch_run_ids,
            "source_delta_count": (source_delta_input or {}).get("source_delta_count"),
            "source_count": len(records),
            "not_in_run_count": len(not_in_run_ids),
            "not_in_run_source_record_ids_sample": not_in_run_ids[:20],
        },
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
