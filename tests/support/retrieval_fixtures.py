from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3


def _write_json_file(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
    skipped_source_record_ids: list[str] | None = None,
    catalog_source_count: int | None = None,
    filters: dict | None = None,
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    _write_json_file(diagnostics_dir / "extraction_validation.json", {"passed": True})
    skipped_source_record_ids = skipped_source_record_ids or []
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    manifest_records.extend(
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "skipped_excluded",
        }
        for source_record_id in skipped_source_record_ids
    )
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    selected_count = len(source_record_ids) + len(skipped_source_record_ids)
    catalog_count = catalog_source_count if catalog_source_count is not None else selected_count
    _write_json_file(
        diagnostics_dir / "summary.json",
        {
            "source_set_id": source_set_id,
            "catalog_source_count": catalog_count,
            "artifact_bearing_source_count": catalog_count - len(skipped_source_record_ids),
            "required_extraction_source_count": catalog_count - len(skipped_source_record_ids),
            "selected_source_count": selected_count,
            "selected_required_extraction_source_count": len(source_record_ids),
            "extracted_count": len(source_record_ids),
            "failed_count": 0,
            "skipped_excluded_count": len(skipped_source_record_ids),
            "filters": filters or {"id": None, "parser": None, "limit": None},
        },
    )


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        text_path = output_dir / chunk["source_text_path"]
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(chunk["text"], encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_catalog_sqlite(
    output_dir: Path,
    topics_by_source: dict[str, list[str]],
    *,
    source_rows_by_source: dict[str, dict] | None = None,
) -> Path:
    return _write_catalog_sqlite_for_dir(
        output_dir / "catalog",
        topics_by_source,
        source_rows_by_source=source_rows_by_source,
    )


def _write_catalog_sqlite_for_dir(
    catalog_dir: Path,
    topics_by_source: dict[str, list[str]],
    *,
    source_rows_by_source: dict[str, dict] | None = None,
) -> Path:
    path = catalog_dir / "review_sources.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    source_rows_by_source = source_rows_by_source or {}
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE sources (
              source_record_id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              document_role TEXT NOT NULL,
              metadata_json TEXT NOT NULL
            );
            CREATE TABLE review_topics (
              topic_id TEXT PRIMARY KEY,
              label TEXT NOT NULL
            );
            CREATE TABLE source_review_topics (
              source_record_id TEXT NOT NULL,
              topic_id TEXT NOT NULL,
              PRIMARY KEY (source_record_id, topic_id)
            );
            """
        )
        for source_record_id in sorted(set(topics_by_source) | set(source_rows_by_source)):
            row = source_rows_by_source.get(source_record_id, {})
            metadata_json = row.get("metadata_json", {})
            if not isinstance(metadata_json, str):
                metadata_json = json.dumps(metadata_json, sort_keys=True)
            connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?)",
                (
                    source_record_id,
                    row.get("title", source_record_id),
                    row.get("document_role", "law"),
                    metadata_json,
                ),
            )
        for source_record_id, topics in topics_by_source.items():
            for index, topic in enumerate(topics):
                topic_id = f"topic:{source_record_id}:{index}"
                connection.execute("INSERT INTO review_topics VALUES (?, ?)", (topic_id, topic))
                connection.execute(
                    "INSERT INTO source_review_topics VALUES (?, ?)",
                    (source_record_id, topic_id),
                )
        connection.commit()
    return path


def _write_catalog_source_set_manifest(output_dir: Path, source_set_id: str) -> Path:
    return _write_catalog_source_set_manifest_for_dir(output_dir / "catalog", source_set_id)


def _write_catalog_source_set_manifest_for_dir(catalog_dir: Path, source_set_id: str) -> Path:
    return _write_json_file(
        catalog_dir / "source_set_manifest.json",
        {"source_set_id": source_set_id},
    )


def _write_extraction_accuracy_audit(
    output_dir: Path,
    source_set_id: str,
    *,
    admitted_source_record_ids: list[str],
) -> Path:
    return _write_json_file(
        output_dir / "derived" / source_set_id / "diagnostics" / "extraction_accuracy_audit.json",
        {
            "source_set_id": source_set_id,
            "passed": True,
            "knowledge_base_admitted_source_record_ids": admitted_source_record_ids,
            "knowledge_base_blocked_source_record_ids": [],
        },
    )


def _chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    title: str,
    document_role: str,
    support_document_role: str | None = None,
    authority_level: str,
    citation_label: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "support_document_role": support_document_role or document_role,
        "authority_level": authority_level,
        "host": "example.test",
        "expected_parser": "html",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "citation_label": citation_label,
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-04-30T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": title,
        "content_sha256": content_sha256,
        "text": text,
    }


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")
