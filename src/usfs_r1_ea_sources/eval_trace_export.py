from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import sqlite3

from .eval_trace_inventory import REPO_ROOT
from .eval_trace_store import STORE_SCHEMA_VERSION
from .records import sha256_file


CANONICAL_EXPORT_SCHEMA_VERSION = "system-eval-trace-export-v1"
OPENINFERENCE_EXPORT_SCHEMA_VERSION = "openinference-traces-export-v1"
EXPORT_SUMMARY_SCHEMA_VERSION = "system-eval-trace-export-summary-v1"

TABLE_PRIMARY_KEYS = {
    "system_eval_runs": "eval_run_id",
    "system_eval_cases": "eval_case_id",
    "system_eval_case_results": "eval_case_result_id",
    "system_eval_scores": "eval_score_id",
    "trace_runs": "trace_id",
    "trace_spans": "span_id",
}
JSON_COLUMNS = {
    "system_eval_runs": (
        "source_record_ids_json",
        "scorer_versions_json",
        "thresholds_json",
        "summary_json",
    ),
    "system_eval_cases": ("input_json", "expected_json", "metadata_json"),
    "system_eval_scores": ("evidence_refs_json",),
    "trace_runs": ("artifact_refs_json",),
    "trace_spans": ("attributes_json",),
}
OPENINFERENCE_KIND_BY_SPAN_KIND = {
    "workflow": "CHAIN",
    "artifact": "CHAIN",
    "validate": "CHAIN",
    "retrieve": "RETRIEVER",
    "search": "RETRIEVER",
    "rerank": "RERANKER",
    "embed": "EMBEDDING",
    "tool": "TOOL",
    "evaluation": "EVALUATOR",
    "score": "EVALUATOR",
    "llm": "LLM",
    "agent_task": "AGENT",
    "guardrail": "GUARDRAIL",
    "error": "CHAIN",
}
OPERATION_BY_TRACE_KIND = {
    "applicability_retrieval": "retrieval",
    "applicability_graph": "retrieval",
    "evaluation": "evaluation",
    "replay": "replay",
    "validation": "validation",
}


@dataclass(frozen=True)
class EvalTraceExportResult:
    summary: dict[str, Any]


def run_eval_trace_export(
    *,
    sqlite_path: Path,
    canonical_json_path: Path,
    openinference_json_path: Path,
    repo_root: Path = REPO_ROOT,
) -> EvalTraceExportResult:
    repo_root = repo_root.resolve()
    sqlite_path = _resolve_path(sqlite_path, repo_root)
    canonical_json_path = _resolve_path(canonical_json_path, repo_root)
    openinference_json_path = _resolve_path(openinference_json_path, repo_root)

    store = _read_store(sqlite_path)
    canonical = _canonical_export(store, sqlite_path=sqlite_path, repo_root=repo_root)
    openinference = _openinference_export(
        store,
        sqlite_path=sqlite_path,
        repo_root=repo_root,
    )
    validation = _validate_exports(store, canonical, openinference)
    passed = validation["passed"]

    if passed:
        _write_json(canonical_json_path, canonical)
        _write_json(openinference_json_path, openinference)

    summary = {
        "schema_version": EXPORT_SUMMARY_SCHEMA_VERSION,
        "canonical_schema_version": CANONICAL_EXPORT_SCHEMA_VERSION,
        "openinference_schema_version": OPENINFERENCE_EXPORT_SCHEMA_VERSION,
        "store_schema_version": STORE_SCHEMA_VERSION,
        "sqlite_path": _display_path(sqlite_path, repo_root),
        "canonical_json_path": _display_path(canonical_json_path, repo_root),
        "openinference_json_path": _display_path(openinference_json_path, repo_root),
        "passed": passed,
        "command_succeeded": passed,
        "row_counts": canonical["row_counts"],
        "trace_count": openinference["trace_count"],
        "openinference_span_count": openinference["span_count"],
        "missing_table_count": len(validation["missing_tables"]),
        "missing_provenance_count": len(validation["missing_provenance"]),
        "validation_checks": validation["checks"],
    }
    return EvalTraceExportResult(summary=summary)


def _read_store(sqlite_path: Path) -> dict[str, Any]:
    if not sqlite_path.exists():
        return {
            "tables": {table: [] for table in TABLE_PRIMARY_KEYS},
            "missing_tables": list(TABLE_PRIMARY_KEYS),
            "read_errors": [{"path": str(sqlite_path), "error": "sqlite_not_found"}],
        }

    tables = {table: [] for table in TABLE_PRIMARY_KEYS}
    missing_tables: list[str] = []
    read_errors: list[dict[str, str]] = []
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        existing_tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        for table, primary_key in TABLE_PRIMARY_KEYS.items():
            if table not in existing_tables:
                missing_tables.append(table)
                continue
            try:
                rows = connection.execute(
                    f"SELECT * FROM {table} ORDER BY {primary_key}"
                ).fetchall()
            except sqlite3.Error as exc:
                read_errors.append({"table": table, "error": str(exc)})
                continue
            tables[table] = [_decode_row(table, row) for row in rows]
    return {
        "tables": tables,
        "missing_tables": missing_tables,
        "read_errors": read_errors,
    }


def _decode_row(table: str, row: sqlite3.Row) -> dict[str, Any]:
    decoded = dict(row)
    for column in JSON_COLUMNS.get(table, ()):
        value = decoded.pop(column, None)
        decoded[column.removesuffix("_json")] = _loads_json(value)
    return decoded


def _canonical_export(
    store: dict[str, Any],
    *,
    sqlite_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    tables = store["tables"]
    return {
        "schema_version": CANONICAL_EXPORT_SCHEMA_VERSION,
        "store_schema_version": STORE_SCHEMA_VERSION,
        "source": _source_metadata(sqlite_path, repo_root),
        "export_policy": _export_policy(),
        "row_counts": {table: len(rows) for table, rows in tables.items()},
        "system_eval_runs": tables["system_eval_runs"],
        "system_eval_cases": tables["system_eval_cases"],
        "system_eval_case_results": tables["system_eval_case_results"],
        "system_eval_scores": tables["system_eval_scores"],
        "trace_runs": tables["trace_runs"],
        "trace_spans": tables["trace_spans"],
    }


def _openinference_export(
    store: dict[str, Any],
    *,
    sqlite_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    tables = store["tables"]
    run_by_id = {row["eval_run_id"]: row for row in tables["system_eval_runs"]}
    case_result_by_trace_id = {
        row["trace_id"]: row for row in tables["system_eval_case_results"]
    }
    scores_by_case_result_id = _group_by(
        tables["system_eval_scores"],
        "eval_case_result_id",
    )
    spans_by_trace_id = _group_by(tables["trace_spans"], "trace_id")
    traces = []
    for trace_run in tables["trace_runs"]:
        case_result = case_result_by_trace_id.get(trace_run["trace_id"], {})
        eval_run = run_by_id.get(case_result.get("eval_run_id"), {})
        scores = scores_by_case_result_id.get(case_result.get("eval_case_result_id"), [])
        source_record_ids = _source_record_ids(eval_run, scores)
        citation_labels = _citation_labels(scores)
        root_span = _root_openinference_span(
            trace_run,
            eval_run=eval_run,
            source_record_ids=source_record_ids,
            citation_labels=citation_labels,
        )
        child_spans = [
            _child_openinference_span(
                span,
                trace_run=trace_run,
                eval_run=eval_run,
                source_record_ids=source_record_ids,
                citation_labels=citation_labels,
            )
            for span in spans_by_trace_id.get(trace_run["trace_id"], [])
        ]
        traces.append(
            {
                "trace_id": trace_run["trace_id"],
                "name": trace_run["root_ref_id"],
                "status": trace_run["status"],
                "spans": [root_span, *child_spans],
            }
        )

    span_count = sum(len(trace["spans"]) for trace in traces)
    return {
        "schema_version": OPENINFERENCE_EXPORT_SCHEMA_VERSION,
        "source": _source_metadata(sqlite_path, repo_root),
        "export_policy": _export_policy(),
        "trace_count": len(traces),
        "span_count": span_count,
        "traces": traces,
    }


def _root_openinference_span(
    trace_run: dict[str, Any],
    *,
    eval_run: dict[str, Any],
    source_record_ids: list[str],
    citation_labels: list[str],
) -> dict[str, Any]:
    artifact_refs = _dict(trace_run.get("artifact_refs"))
    span_kind = _root_span_kind(trace_run)
    return {
        "span_id": trace_run["trace_id"],
        "parent_span_id": None,
        "name": str(trace_run["root_ref_id"]),
        "status": trace_run["status"],
        "openinference_span_kind": span_kind,
        "attributes": _provenance_attributes(
            trace_run=trace_run,
            eval_run=eval_run,
            artifact_refs=artifact_refs,
            source_record_ids=source_record_ids,
            citation_labels=citation_labels,
            span_kind=span_kind,
        ),
    }


def _child_openinference_span(
    span: dict[str, Any],
    *,
    trace_run: dict[str, Any],
    eval_run: dict[str, Any],
    source_record_ids: list[str],
    citation_labels: list[str],
) -> dict[str, Any]:
    attributes = _dict(span.get("attributes"))
    artifact_refs = _dict(trace_run.get("artifact_refs"))
    span_kind = OPENINFERENCE_KIND_BY_SPAN_KIND.get(span["span_kind"], "CHAIN")
    return {
        "span_id": span["span_id"],
        "parent_span_id": span["parent_span_id"] or trace_run["trace_id"],
        "name": span["name"],
        "status": span["status"],
        "openinference_span_kind": span_kind,
        "attributes": {
            **attributes,
            **_provenance_attributes(
                trace_run=trace_run,
                eval_run=eval_run,
                artifact_refs=artifact_refs,
                source_record_ids=source_record_ids,
                citation_labels=citation_labels,
                span_kind=span_kind,
            ),
            "usfs.source_ref_kind": span.get("source_ref_kind"),
            "usfs.source_ref_id": span.get("source_ref_id"),
        },
    }


def _provenance_attributes(
    *,
    trace_run: dict[str, Any],
    eval_run: dict[str, Any],
    artifact_refs: dict[str, Any],
    source_record_ids: list[str],
    citation_labels: list[str],
    span_kind: str,
) -> dict[str, Any]:
    return {
        "openinference.span.kind": span_kind,
        "gen_ai.operation.name": OPERATION_BY_TRACE_KIND.get(
            str(trace_run.get("trace_kind")),
            str(trace_run.get("trace_kind")),
        ),
        "usfs.local_source_of_record": True,
        "usfs.redaction_policy": trace_run.get("redaction_policy"),
        "usfs.source_set_id": trace_run.get("source_set_id") or eval_run.get("source_set_id"),
        "usfs.review_id": trace_run.get("review_id") or eval_run.get("review_id"),
        "usfs.origin_artifact_ref": artifact_refs.get("origin_artifact_ref")
        or eval_run.get("origin_artifact_ref"),
        "usfs.result_path": artifact_refs.get("path") or eval_run.get("origin_artifact_ref"),
        "usfs.artifact_sha256": trace_run.get("input_hash")
        or eval_run.get("origin_artifact_sha256"),
        "usfs.current_artifact_sha256": trace_run.get("output_hash")
        or eval_run.get("current_artifact_sha256"),
        "usfs.eval_run_id": eval_run.get("eval_run_id"),
        "usfs.eval_kind": eval_run.get("eval_kind"),
        "usfs.contract_id": eval_run.get("contract_id"),
        "usfs.contract_version": eval_run.get("contract_version"),
        "usfs.source_record_ids": source_record_ids,
        "usfs.citation_labels": citation_labels,
    }


def _validate_exports(
    store: dict[str, Any],
    canonical: dict[str, Any],
    openinference: dict[str, Any],
) -> dict[str, Any]:
    missing_tables = list(store["missing_tables"])
    read_errors = list(store["read_errors"])
    row_counts = canonical["row_counts"]
    missing_provenance = _missing_provenance(openinference)
    checks = [
        {
            "name": "required_tables_present",
            "passed": not missing_tables,
            "missing_tables": missing_tables,
        },
        {
            "name": "store_rows_present",
            "passed": all(count > 0 for count in row_counts.values()),
            "row_counts": row_counts,
        },
        {
            "name": "store_readable",
            "passed": not read_errors,
            "read_errors": read_errors,
        },
        {
            "name": "canonical_local_source_of_record",
            "passed": bool(canonical["export_policy"]["local_source_of_record"]),
            "export_policy": canonical["export_policy"],
        },
        {
            "name": "openinference_provenance_preserved",
            "passed": not missing_provenance,
            "missing_provenance": missing_provenance,
        },
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "missing_tables": missing_tables,
        "read_errors": read_errors,
        "missing_provenance": missing_provenance,
        "checks": checks,
    }


def _missing_provenance(openinference: dict[str, Any]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    required_attributes = (
        "usfs.source_set_id",
        "usfs.review_id",
        "usfs.origin_artifact_ref",
        "usfs.result_path",
        "usfs.artifact_sha256",
        "usfs.current_artifact_sha256",
        "usfs.contract_id",
        "usfs.contract_version",
    )
    for trace in openinference["traces"]:
        for span in trace["spans"]:
            attrs = _dict(span.get("attributes"))
            for attribute in required_attributes:
                if _is_missing(attrs.get(attribute)):
                    missing.append(
                        {
                            "trace_id": str(trace.get("trace_id")),
                            "span_id": str(span.get("span_id")),
                            "attribute": attribute,
                        }
                    )
            if not _is_missing(attrs.get("usfs.source_ref_kind")) and _is_missing(
                attrs.get("usfs.source_ref_id")
            ):
                missing.append(
                    {
                        "trace_id": str(trace.get("trace_id")),
                        "span_id": str(span.get("span_id")),
                        "attribute": "usfs.source_ref_id",
                    }
                )
    return missing


def _root_span_kind(trace_run: dict[str, Any]) -> str:
    trace_kind = str(trace_run.get("trace_kind") or "")
    if trace_kind in {"applicability_retrieval", "applicability_graph"}:
        return "RETRIEVER"
    if trace_kind == "evaluation":
        return "EVALUATOR"
    return "CHAIN"


def _source_record_ids(eval_run: dict[str, Any], scores: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    values.extend(_string_values(eval_run.get("source_record_ids")))
    for score in scores:
        evidence_refs = _dict(score.get("evidence_refs"))
        values.extend(_string_values(evidence_refs.get("source_record_ids")))
    return sorted(set(values))


def _citation_labels(scores: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for score in scores:
        evidence_refs = _dict(score.get("evidence_refs"))
        values.extend(_string_values(evidence_refs.get("citation_labels")))
    return sorted(set(values))


def _source_metadata(sqlite_path: Path, repo_root: Path) -> dict[str, Any]:
    return {
        "sqlite_path": _display_path(sqlite_path, repo_root),
        "sqlite_sha256": sha256_file(sqlite_path) if sqlite_path.exists() else None,
    }


def _export_policy() -> dict[str, Any]:
    return {
        "local_source_of_record": True,
        "canonical_json_required_before_openinference": True,
        "redaction_policy": "local_unredacted_no_external_export",
        "external_export_approved": False,
    }


def _group_by(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row.get(key), []).append(row)
    return grouped


def _loads_json(value: object) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    return json.loads(value)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_values(value: object) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_string_values(item))
        return values
    return []


def _is_missing(value: object) -> bool:
    return value is None or value == "" or value == []


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)
