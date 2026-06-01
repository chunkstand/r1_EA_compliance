from __future__ import annotations

from typing import Any
import sqlite3


def _reset_schema(connection: sqlite3.Connection) -> None:
    for table in (
        "system_eval_scores",
        "system_eval_case_results",
        "system_eval_cases",
        "system_eval_runs",
        "trace_spans",
        "trace_runs",
    ):
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    _create_schema(connection)


def _replace_rows(connection: sqlite3.Connection, rows: dict[str, list[dict[str, Any]]]) -> None:
    table_order = (
        "system_eval_runs",
        "system_eval_cases",
        "trace_runs",
        "system_eval_case_results",
        "system_eval_scores",
        "trace_spans",
    )
    for table in table_order:
        table_rows = rows[table]
        if not table_rows:
            continue
        columns = tuple(table_rows[0])
        placeholders = ", ".join("?" for _ in columns)
        column_list = ", ".join(columns)
        connection.executemany(
            f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})",
            [[row[column] for column in columns] for row in table_rows],
        )


def _row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    tables = (
        "system_eval_runs",
        "system_eval_cases",
        "system_eval_case_results",
        "system_eval_scores",
        "trace_runs",
        "trace_spans",
    )
    return {
        table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in tables
    }


def _orphan_counts(connection: sqlite3.Connection) -> dict[str, int]:
    queries = {
        "system_eval_cases_without_run": """
            SELECT COUNT(*) FROM system_eval_cases c
            LEFT JOIN system_eval_runs r ON c.eval_run_id = r.eval_run_id
            WHERE r.eval_run_id IS NULL
        """,
        "system_eval_case_results_without_case": """
            SELECT COUNT(*) FROM system_eval_case_results r
            LEFT JOIN system_eval_cases c ON r.eval_case_id = c.eval_case_id
            WHERE c.eval_case_id IS NULL
        """,
        "system_eval_scores_without_case_result": """
            SELECT COUNT(*) FROM system_eval_scores s
            LEFT JOIN system_eval_case_results r
              ON s.eval_case_result_id = r.eval_case_result_id
            WHERE r.eval_case_result_id IS NULL
        """,
        "trace_spans_without_trace_run": """
            SELECT COUNT(*) FROM trace_spans s
            LEFT JOIN trace_runs r ON s.trace_id = r.trace_id
            WHERE r.trace_id IS NULL
        """,
    }
    return {
        name: int(connection.execute(query).fetchone()[0])
        for name, query in queries.items()
    }


def _duplicate_id_counts(connection: sqlite3.Connection) -> dict[str, int]:
    primary_keys = {
        "system_eval_runs": "eval_run_id",
        "system_eval_cases": "eval_case_id",
        "system_eval_case_results": "eval_case_result_id",
        "system_eval_scores": "eval_score_id",
        "trace_runs": "trace_id",
        "trace_spans": "span_id",
    }
    counts = {}
    for table, key in primary_keys.items():
        query = f"""
            SELECT COUNT(*) FROM (
                SELECT {key} FROM {table}
                GROUP BY {key}
                HAVING COUNT(*) > 1
            )
        """
        counts[table] = int(connection.execute(query).fetchone()[0])
    return counts


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS system_eval_runs (
            eval_run_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            contract_id TEXT,
            contract_version TEXT,
            eval_name TEXT NOT NULL,
            eval_kind TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT,
            dataset_name TEXT NOT NULL,
            dataset_version TEXT NOT NULL,
            scorer_set_name TEXT NOT NULL,
            scorer_set_version TEXT NOT NULL,
            workflow_version TEXT NOT NULL,
            status TEXT NOT NULL,
            passed INTEGER NOT NULL,
            source_set_id TEXT,
            review_id TEXT,
            origin_artifact_ref TEXT NOT NULL,
            origin_artifact_sha256 TEXT,
            current_artifact_sha256 TEXT,
            catalog_ref TEXT,
            replay_context_ref TEXT,
            source_record_ids_json TEXT NOT NULL,
            scorer_versions_json TEXT NOT NULL,
            thresholds_json TEXT NOT NULL,
            failure_reason TEXT,
            summary_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS system_eval_cases (
            eval_case_id TEXT PRIMARY KEY,
            eval_run_id TEXT NOT NULL,
            case_key TEXT NOT NULL,
            case_version TEXT NOT NULL,
            case_hash TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            input_json TEXT NOT NULL,
            expected_json TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            FOREIGN KEY(eval_run_id) REFERENCES system_eval_runs(eval_run_id)
        );
        CREATE TABLE IF NOT EXISTS system_eval_case_results (
            eval_case_result_id TEXT PRIMARY KEY,
            eval_run_id TEXT NOT NULL,
            eval_case_id TEXT NOT NULL,
            trace_id TEXT NOT NULL,
            status TEXT NOT NULL,
            passed INTEGER NOT NULL,
            score REAL NOT NULL,
            failure_reason TEXT,
            FOREIGN KEY(eval_run_id) REFERENCES system_eval_runs(eval_run_id),
            FOREIGN KEY(eval_case_id) REFERENCES system_eval_cases(eval_case_id)
        );
        CREATE TABLE IF NOT EXISTS system_eval_scores (
            eval_score_id TEXT PRIMARY KEY,
            eval_case_result_id TEXT NOT NULL,
            score_name TEXT NOT NULL,
            score_kind TEXT NOT NULL,
            score_version TEXT NOT NULL,
            score REAL NOT NULL,
            passed INTEGER NOT NULL,
            threshold REAL NOT NULL,
            evidence_refs_json TEXT NOT NULL,
            FOREIGN KEY(eval_case_result_id) REFERENCES system_eval_case_results(eval_case_result_id)
        );
        CREATE TABLE IF NOT EXISTS trace_runs (
            trace_id TEXT PRIMARY KEY,
            trace_kind TEXT NOT NULL,
            root_ref_kind TEXT NOT NULL,
            root_ref_id TEXT NOT NULL,
            status TEXT NOT NULL,
            input_hash TEXT,
            output_hash TEXT,
            artifact_refs_json TEXT NOT NULL,
            redaction_policy TEXT NOT NULL,
            source_set_id TEXT,
            review_id TEXT
        );
        CREATE TABLE IF NOT EXISTS trace_spans (
            span_id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            parent_span_id TEXT,
            span_kind TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            attributes_json TEXT NOT NULL,
            source_ref_kind TEXT,
            source_ref_id TEXT,
            FOREIGN KEY(trace_id) REFERENCES trace_runs(trace_id)
        );
        """
    )
