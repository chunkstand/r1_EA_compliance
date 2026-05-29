from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from tests.test_eval_trace_store import STORE_TABLES
from tests.test_eval_trace_store import _write_inventory
from usfs_r1_ea_sources.eval_trace_export import CANONICAL_EXPORT_SCHEMA_VERSION
from usfs_r1_ea_sources.eval_trace_export import OPENINFERENCE_EXPORT_SCHEMA_VERSION
from usfs_r1_ea_sources.eval_trace_export import run_eval_trace_export
from usfs_r1_ea_sources.eval_trace_store import run_eval_trace_store_build


def test_export_writes_canonical_and_openinference_json(tmp_path: Path) -> None:
    sqlite_path = _write_store(tmp_path)
    canonical_path = tmp_path / "system_eval_trace_export.json"
    openinference_path = tmp_path / "openinference_traces.json"

    result = run_eval_trace_export(
        sqlite_path=sqlite_path,
        canonical_json_path=canonical_path,
        openinference_json_path=openinference_path,
        repo_root=tmp_path,
    )
    summary = result.summary

    assert summary["passed"] is True
    assert summary["command_succeeded"] is True
    assert summary["row_counts"] == {table: 18 for table in STORE_TABLES}
    assert summary["trace_count"] == 18
    assert summary["openinference_span_count"] == 36

    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    openinference = json.loads(openinference_path.read_text(encoding="utf-8"))

    assert canonical["schema_version"] == CANONICAL_EXPORT_SCHEMA_VERSION
    assert canonical["export_policy"] == {
        "canonical_json_required_before_openinference": True,
        "external_export_approved": False,
        "local_source_of_record": True,
        "redaction_policy": "local_unredacted_no_external_export",
    }
    assert canonical["row_counts"] == {table: 18 for table in STORE_TABLES}
    source_catalog_run = next(
        run for run in canonical["system_eval_runs"] if run["eval_name"] == "source_catalog"
    )
    assert source_catalog_run["source_record_ids"] == ["SRC-001"]

    assert openinference["schema_version"] == OPENINFERENCE_EXPORT_SCHEMA_VERSION
    assert openinference["trace_count"] == 18
    assert all(trace["spans"][0]["parent_span_id"] is None for trace in openinference["traces"])
    retrieval_span = next(
        span
        for trace in openinference["traces"]
        for span in trace["spans"]
        if span["attributes"]["usfs.result_path"].endswith(
            "applicability_retrieval_trace.jsonl"
        )
        and span["parent_span_id"] is not None
    )
    assert retrieval_span["openinference_span_kind"] == "RETRIEVER"
    assert retrieval_span["attributes"]["openinference.span.kind"] == "RETRIEVER"
    assert retrieval_span["attributes"]["usfs.source_set_id"] == "source-set-a"
    assert retrieval_span["attributes"]["usfs.review_id"] == "review-a"
    assert retrieval_span["attributes"]["usfs.origin_artifact_ref"].endswith(
        "applicability_retrieval_trace.jsonl"
    )
    assert retrieval_span["attributes"]["usfs.artifact_sha256"]
    assert retrieval_span["attributes"]["usfs.source_ref_kind"] == "artifact"
    assert retrieval_span["attributes"]["usfs.source_ref_id"].endswith(
        "applicability_retrieval_trace.jsonl"
    )


def test_export_blocks_lossy_source_backed_openinference_span(tmp_path: Path) -> None:
    sqlite_path = _write_store(tmp_path)
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute(
            """
            UPDATE trace_spans
            SET source_ref_id = NULL
            WHERE source_ref_id LIKE '%applicability_retrieval_trace.jsonl'
            """
        )
    canonical_path = tmp_path / "system_eval_trace_export.json"
    openinference_path = tmp_path / "openinference_traces.json"

    summary = run_eval_trace_export(
        sqlite_path=sqlite_path,
        canonical_json_path=canonical_path,
        openinference_json_path=openinference_path,
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["command_succeeded"] is False
    assert summary["missing_provenance_count"] == 1
    assert not canonical_path.exists()
    assert not openinference_path.exists()


def test_export_reports_missing_store_tables_without_writing_outputs(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "empty.sqlite"
    sqlite3.connect(sqlite_path).close()
    canonical_path = tmp_path / "system_eval_trace_export.json"
    openinference_path = tmp_path / "openinference_traces.json"

    summary = run_eval_trace_export(
        sqlite_path=sqlite_path,
        canonical_json_path=canonical_path,
        openinference_json_path=openinference_path,
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["missing_table_count"] == len(STORE_TABLES)
    assert summary["row_counts"] == {table: 0 for table in STORE_TABLES}
    assert not canonical_path.exists()
    assert not openinference_path.exists()


def _write_store(tmp_path: Path) -> Path:
    inventory_path = _write_inventory(tmp_path)
    sqlite_path = tmp_path / "system_eval_trace.sqlite"
    result = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        repo_root=tmp_path,
    )
    assert result.summary["passed"] is True
    return sqlite_path
