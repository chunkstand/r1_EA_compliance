from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import sqlite3

from .eval_context_graph_contract import DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH
from .eval_context_graph_contract import JSON_COLUMNS
from .eval_context_graph_contract import TABLE_PRIMARY_KEYS
from .eval_context_graph_contract import load_eval_context_graph_contract
from .eval_context_graph_events import context_graph_events_for_artifact
from .eval_context_graph_validation import graph_checks
from .eval_context_graph_validation import graph_file_checks
from .eval_context_graph_validation import store_checks
from .eval_trace_inventory import REPO_ROOT
from .eval_trace_store import STORE_SCHEMA_VERSION
from .records import sha256_file


CONTEXT_GRAPH_SCHEMA_VERSION = "eval-context-graph-v1"
CONTEXT_GRAPH_BUILD_SUMMARY_SCHEMA_VERSION = "eval-context-graph-build-summary-v1"
CONTEXT_GRAPH_EVAL_SUMMARY_SCHEMA_VERSION = "eval-context-graph-eval-summary-v1"
ROW_NODE_KINDS = {
    "system_eval_runs": "eval_run",
    "system_eval_cases": "eval_case",
    "system_eval_case_results": "eval_result",
    "system_eval_scores": "score",
    "trace_runs": "trace",
    "trace_spans": "span",
}


@dataclass(frozen=True)
class EvalContextGraphBuildResult:
    summary: dict[str, Any]


@dataclass(frozen=True)
class EvalContextGraphEvalResult:
    summary: dict[str, Any]


def run_eval_context_graph_build(
    *,
    sqlite_path: Path,
    graph_json_path: Path,
    summary_path: Path | None = None,
    event_log_paths: list[Path] | None = None,
    contract_path: Path = DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH,
    repo_root: Path = REPO_ROOT,
) -> EvalContextGraphBuildResult:
    repo_root = repo_root.resolve()
    sqlite_path = _resolve_path(sqlite_path, repo_root)
    graph_json_path = _resolve_path(graph_json_path, repo_root)
    summary_path = _resolve_path(summary_path, repo_root) if summary_path is not None else None
    resolved_event_log_paths = [
        _resolve_path(path, repo_root) for path in event_log_paths or []
    ]

    contract = load_eval_context_graph_contract(contract_path, repo_root=repo_root)
    store = _read_store(sqlite_path)
    graph = _build_graph(
        store,
        sqlite_path=sqlite_path,
        event_log_paths=resolved_event_log_paths,
        contract=contract,
        repo_root=repo_root,
    )
    validation_checks = store_checks(store) + graph_checks(
        graph,
        contract,
        graph_schema_version=CONTEXT_GRAPH_SCHEMA_VERSION,
    )
    passed = all(check["passed"] for check in validation_checks)

    if passed:
        _write_json(graph_json_path, graph)

    summary = {
        "schema_version": CONTEXT_GRAPH_BUILD_SUMMARY_SCHEMA_VERSION,
        "graph_schema_version": CONTEXT_GRAPH_SCHEMA_VERSION,
        "store_schema_version": STORE_SCHEMA_VERSION,
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "sqlite_path": _display_path(sqlite_path, repo_root),
        "graph_json_path": _display_path(graph_json_path, repo_root),
        "passed": passed,
        "command_succeeded": passed,
        "missing_table_count": len(store["missing_tables"]),
        "read_error_count": len(store["read_errors"]),
        "row_counts": graph["source"]["row_counts"],
        "node_counts": graph["node_counts"],
        "edge_counts": graph["edge_counts"],
        "event_log_path_count": len(resolved_event_log_paths),
        "event_source_count": len(graph.get("event_sources", [])),
        "event_node_count": _event_node_count(graph),
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "reserved_node_kinds_not_materialized": contract.get("reserved_node_kinds", []),
        "validation_checks": validation_checks,
    }
    if summary_path is not None:
        _write_json(summary_path, summary)
    return EvalContextGraphBuildResult(summary=summary)


def run_eval_context_graph_eval(
    *,
    graph_json_path: Path,
    summary_path: Path | None = None,
    contract_path: Path = DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH,
    repo_root: Path = REPO_ROOT,
) -> EvalContextGraphEvalResult:
    repo_root = repo_root.resolve()
    graph_json_path = _resolve_path(graph_json_path, repo_root)
    summary_path = _resolve_path(summary_path, repo_root) if summary_path is not None else None
    contract = load_eval_context_graph_contract(contract_path, repo_root=repo_root)
    graph = _read_graph(graph_json_path)
    validation_checks = graph_file_checks(graph_json_path, graph) + graph_checks(
        graph,
        contract,
        graph_schema_version=CONTEXT_GRAPH_SCHEMA_VERSION,
    )
    passed = all(check["passed"] for check in validation_checks)
    summary = {
        "schema_version": CONTEXT_GRAPH_EVAL_SUMMARY_SCHEMA_VERSION,
        "graph_schema_version": graph.get("schema_version"),
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "graph_json_path": _display_path(graph_json_path, repo_root),
        "passed": passed,
        "command_succeeded": passed,
        "node_counts": graph.get("node_counts", {}),
        "edge_counts": graph.get("edge_counts", {}),
        "event_source_count": len(_list_of_dicts(graph.get("event_sources"))),
        "event_node_count": _event_node_count(graph),
        "node_count": len(_list_of_dicts(graph.get("nodes"))),
        "edge_count": len(_list_of_dicts(graph.get("edges"))),
        "validation_checks": validation_checks,
    }
    if summary_path is not None:
        _write_json(summary_path, summary)
    return EvalContextGraphEvalResult(summary=summary)


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
    return {"tables": tables, "missing_tables": missing_tables, "read_errors": read_errors}


def _decode_row(table: str, row: sqlite3.Row) -> dict[str, Any]:
    decoded = dict(row)
    for column in JSON_COLUMNS.get(table, ()):
        value = decoded.pop(column, None)
        decoded[column.removesuffix("_json")] = _loads_json(value)
    return decoded


def _build_graph(
    store: dict[str, Any],
    *,
    sqlite_path: Path,
    event_log_paths: list[Path],
    contract: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    tables = store["tables"]
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    row_nodes: dict[tuple[str, str], str] = {}
    artifact_nodes: dict[str, str] = {}
    event_source_summaries: dict[str, dict[str, Any]] = {}
    target_nodes: dict[tuple[str, str], str] = {}

    def add_node(
        *,
        kind: str,
        stable_ref: str,
        properties: dict[str, Any],
        source_hash: str | None = None,
    ) -> str:
        node_id = f"context-node-{_stable_id(kind, stable_ref)}"
        existing = nodes.get(node_id)
        if existing is not None:
            existing["properties"] = _merge_properties(existing["properties"], properties)
            if not existing.get("source_hash"):
                existing["source_hash"] = source_hash
            return node_id
        nodes[node_id] = {
            "id": node_id,
            "kind": kind,
            "stable_ref": stable_ref,
            "properties": properties,
            "source_hash": source_hash,
        }
        return node_id

    def add_edge(
        *,
        kind: str,
        from_node_id: str,
        to_node_id: str,
        properties: dict[str, Any],
    ) -> None:
        edge_id = f"context-edge-{_stable_id(kind, from_node_id, to_node_id, properties)}"
        edges.setdefault(
            edge_id,
            {
                "id": edge_id,
                "kind": kind,
                "from_node_id": from_node_id,
                "to_node_id": to_node_id,
                "properties": properties,
            },
        )

    def add_artifact(ref: str | None, properties: dict[str, Any]) -> str | None:
        if not ref:
            return None
        existing = artifact_nodes.get(ref)
        node_id = add_node(
            kind="artifact",
            stable_ref=f"artifact:{ref}",
            properties={"artifact_ref": ref, **properties},
            source_hash=_stable_hash({"artifact_ref": ref, **properties}),
        )
        artifact_nodes[ref] = node_id
        return existing or node_id

    def add_target(kind: str, target_id: str | None) -> str | None:
        if not target_id:
            return None
        key = (kind, target_id)
        if key in target_nodes:
            return target_nodes[key]
        node_id = add_node(
            kind=kind,
            stable_ref=f"{kind}:{target_id}",
            properties={"target_id": target_id},
            source_hash=_stable_hash(key),
        )
        target_nodes[key] = node_id
        return node_id

    for table, kind in ROW_NODE_KINDS.items():
        primary_key = TABLE_PRIMARY_KEYS[table]
        for row in tables[table]:
            row_id = str(row[primary_key])
            node_id = add_node(
                kind=kind,
                stable_ref=f"{table}:{row_id}",
                properties=_row_node_properties(table, primary_key, row),
                source_hash=_stable_hash({"table": table, "row": row}),
            )
            row_nodes[(table, row_id)] = node_id

    for eval_run in tables["system_eval_runs"]:
        run_node = row_nodes[("system_eval_runs", eval_run["eval_run_id"])]
        for target_kind, target_id in (
            ("source_set", eval_run.get("source_set_id")),
            ("review", eval_run.get("review_id")),
        ):
            target_node = add_target(target_kind, _string(target_id))
            if target_node is not None:
                add_edge(
                    kind="TARGETS",
                    from_node_id=run_node,
                    to_node_id=target_node,
                    properties={"source_relation": "eval_run_target"},
                )
        artifact_node = add_artifact(
            _string(eval_run.get("origin_artifact_ref")),
            {
                "origin_artifact_sha256": eval_run.get("origin_artifact_sha256"),
                "current_artifact_sha256": eval_run.get("current_artifact_sha256"),
                "source_set_id": eval_run.get("source_set_id"),
                "review_id": eval_run.get("review_id"),
            },
        )
        if artifact_node is not None:
            add_edge(
                kind="PRODUCED_ARTIFACT",
                from_node_id=run_node,
                to_node_id=artifact_node,
                properties={"source_relation": "eval_run_origin_artifact"},
            )

    for eval_case in tables["system_eval_cases"]:
        case_node = row_nodes[("system_eval_cases", eval_case["eval_case_id"])]
        run_node = row_nodes.get(("system_eval_runs", eval_case["eval_run_id"]))
        if run_node is not None:
            add_edge(
                kind="CONTAINS",
                from_node_id=run_node,
                to_node_id=case_node,
                properties={"source_relation": "eval_run_contains_case"},
            )
        artifact_node = add_artifact(
            _string(eval_case.get("source_ref")),
            {"source_kind": eval_case.get("source_kind")},
        )
        if artifact_node is not None:
            add_edge(
                kind="DERIVED_FROM",
                from_node_id=case_node,
                to_node_id=artifact_node,
                properties={"source_relation": "eval_case_source_ref"},
            )

    for result in tables["system_eval_case_results"]:
        result_node = row_nodes[
            ("system_eval_case_results", result["eval_case_result_id"])
        ]
        case_node = row_nodes.get(("system_eval_cases", result["eval_case_id"]))
        if case_node is not None:
            add_edge(
                kind="EVALUATED_BY",
                from_node_id=case_node,
                to_node_id=result_node,
                properties={"source_relation": "eval_case_result"},
            )
        trace_node = row_nodes.get(("trace_runs", result["trace_id"]))
        if trace_node is not None:
            add_edge(
                kind="EVALUATED_BY",
                from_node_id=trace_node,
                to_node_id=result_node,
                properties={"source_relation": "trace_result_cross_link"},
            )
        _add_failure_edge(
            result.get("failure_reason"),
            from_node_id=result_node,
            add_node=add_node,
            add_edge=add_edge,
            source_relation="eval_result_failure",
        )

    for score in tables["system_eval_scores"]:
        score_node = row_nodes[("system_eval_scores", score["eval_score_id"])]
        result_node = row_nodes.get(
            ("system_eval_case_results", score["eval_case_result_id"])
        )
        if result_node is not None:
            add_edge(
                kind="SCORED_AS",
                from_node_id=result_node,
                to_node_id=score_node,
                properties={"source_relation": "eval_result_score"},
            )
        _add_failure_edge(
            _dict(score.get("evidence_refs")).get("failure_reason"),
            from_node_id=score_node,
            add_node=add_node,
            add_edge=add_edge,
            source_relation="score_failure",
        )

    for trace_run in tables["trace_runs"]:
        trace_node = row_nodes[("trace_runs", trace_run["trace_id"])]
        for target_kind, target_id in (
            ("source_set", trace_run.get("source_set_id")),
            ("review", trace_run.get("review_id")),
        ):
            target_node = add_target(target_kind, _string(target_id))
            if target_node is not None:
                add_edge(
                    kind="TARGETS",
                    from_node_id=trace_node,
                    to_node_id=target_node,
                    properties={"source_relation": "trace_target"},
                )
        artifact_refs = _dict(trace_run.get("artifact_refs"))
        artifact_ref = _string(artifact_refs.get("origin_artifact_ref")) or _string(
            artifact_refs.get("path")
        )
        artifact_node = add_artifact(
            artifact_ref,
            {
                "path": artifact_refs.get("path"),
                "input_hash": trace_run.get("input_hash"),
                "output_hash": trace_run.get("output_hash"),
                "source_set_id": trace_run.get("source_set_id"),
                "review_id": trace_run.get("review_id"),
            },
        )
        if artifact_node is not None:
            add_edge(
                kind="USED_ARTIFACT",
                from_node_id=trace_node,
                to_node_id=artifact_node,
                properties={"source_relation": "trace_artifact_ref"},
            )

    for span in tables["trace_spans"]:
        span_node = row_nodes[("trace_spans", span["span_id"])]
        parent_span_id = _string(span.get("parent_span_id"))
        parent_node = (
            row_nodes.get(("trace_spans", parent_span_id)) if parent_span_id else None
        )
        trace_node = row_nodes.get(("trace_runs", span["trace_id"]))
        if parent_node is not None:
            add_edge(
                kind="CONTAINS",
                from_node_id=parent_node,
                to_node_id=span_node,
                properties={"source_relation": "span_parent_child"},
            )
        elif trace_node is not None:
            add_edge(
                kind="CONTAINS",
                from_node_id=trace_node,
                to_node_id=span_node,
                properties={"source_relation": "trace_contains_span"},
            )
        if span.get("source_ref_kind") == "artifact":
            attributes = _dict(span.get("attributes"))
            artifact_node = add_artifact(
                _string(span.get("source_ref_id")),
                {
                    "artifact_sha256": attributes.get("artifact_sha256"),
                    "current_artifact_sha256": attributes.get("current_artifact_sha256"),
                    "line_count": attributes.get("line_count"),
                },
            )
            if artifact_node is not None:
                add_edge(
                    kind="USED_ARTIFACT",
                    from_node_id=span_node,
                    to_node_id=artifact_node,
                    properties={"source_relation": "span_source_ref"},
                )
            _add_event_nodes(
                artifact_ref=_string(span.get("source_ref_id")),
                emitter_node=span_node,
                source_kind="span_source_ref",
                source_relation="span_emitted_event",
                require_event_marker=True,
                add_node=add_node,
                add_edge=add_edge,
                event_source_summaries=event_source_summaries,
                repo_root=repo_root,
            )
        _add_failure_edge(
            _dict(span.get("attributes")).get("failure_reason"),
            from_node_id=span_node,
            add_node=add_node,
            add_edge=add_edge,
            source_relation="span_failure",
        )

    for event_log_path in event_log_paths:
        event_source_node = _add_event_source_node(
            path=event_log_path,
            add_node=add_node,
            repo_root=repo_root,
        )
        _add_event_nodes(
            artifact_ref=_display_path(event_log_path, repo_root),
            emitter_node=event_source_node,
            source_kind="explicit_event_log_path",
            source_relation="event_source_emitted_event",
            require_event_marker=False,
            add_node=add_node,
            add_edge=add_edge,
            event_source_summaries=event_source_summaries,
            repo_root=repo_root,
        )

    sorted_nodes = sorted(nodes.values(), key=lambda node: node["id"])
    sorted_edges = sorted(edges.values(), key=lambda edge: edge["id"])
    return {
        "schema_version": CONTEXT_GRAPH_SCHEMA_VERSION,
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "store_schema_version": STORE_SCHEMA_VERSION,
        "source": {
            "sqlite_path": _display_path(sqlite_path, repo_root),
            "sqlite_sha256": sha256_file(sqlite_path) if sqlite_path.exists() else None,
            "event_log_paths": [
                _display_path(path, repo_root) for path in event_log_paths
            ],
            "row_counts": {table: len(rows) for table, rows in tables.items()},
            "missing_tables": store["missing_tables"],
            "read_errors": store["read_errors"],
        },
        "event_sources": sorted(
            event_source_summaries.values(),
            key=lambda source: str(source.get("artifact_ref")),
        ),
        "graph_policy": contract["graph_policy"],
        "reserved_node_kinds_not_materialized": contract.get(
            "reserved_node_kinds",
            [],
        ),
        "node_counts": _kind_counts(sorted_nodes),
        "edge_counts": _kind_counts(sorted_edges),
        "nodes": sorted_nodes,
        "edges": sorted_edges,
    }


def _row_node_properties(
    table: str,
    primary_key: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    properties = {
        "source_table": table,
        "source_primary_key": primary_key,
        "source_primary_value": row[primary_key],
    }
    for key, value in row.items():
        if key.endswith("_json"):
            continue
        properties[key] = value
    return properties


def _add_failure_edge(
    failure_reason: object,
    *,
    from_node_id: str,
    add_node: Any,
    add_edge: Any,
    source_relation: str,
) -> None:
    reason = _string(failure_reason)
    if reason is None:
        return
    failure_node = add_node(
        kind="failure_class",
        stable_ref=f"failure_class:{reason}",
        properties={"failure_reason": reason},
        source_hash=_stable_hash(reason),
    )
    add_edge(
        kind="FAILED_BECAUSE",
        from_node_id=from_node_id,
        to_node_id=failure_node,
        properties={"source_relation": source_relation},
    )


def _add_event_nodes(
    *,
    artifact_ref: str | None,
    emitter_node: str,
    source_kind: str,
    source_relation: str,
    require_event_marker: bool,
    add_node: Any,
    add_edge: Any,
    event_source_summaries: dict[str, dict[str, Any]],
    repo_root: Path,
) -> None:
    batch = context_graph_events_for_artifact(
        artifact_ref,
        repo_root=repo_root,
        require_event_marker=require_event_marker,
    )
    if batch.summary is not None:
        event_source_summaries[str(batch.summary["artifact_ref"])] = {
            **batch.summary,
            "source_kind": source_kind,
        }
    for event in batch.events:
        event_node = add_node(
            kind=event["kind"],
            stable_ref=event["stable_ref"],
            properties=event["properties"],
            source_hash=event["source_hash"],
        )
        add_edge(
            kind="EMITTED",
            from_node_id=emitter_node,
            to_node_id=event_node,
            properties={
                "source_relation": source_relation,
                "artifact_ref": artifact_ref,
                "line_number": event["properties"].get("line_number"),
            },
        )


def _add_event_source_node(
    *,
    path: Path,
    add_node: Any,
    repo_root: Path,
) -> str:
    artifact_ref = _display_path(path, repo_root)
    return add_node(
        kind="event_source",
        stable_ref=f"event_source:{artifact_ref}",
        properties={
            "artifact_ref": artifact_ref,
            "path": artifact_ref,
            "source_kind": "explicit_event_log_path",
            "redaction_policy": "payload_hash_and_keys_only",
        },
        source_hash=sha256_file(path) if path.exists() else None,
    )


def _read_graph(graph_json_path: Path) -> dict[str, Any]:
    if not graph_json_path.exists():
        return {}
    try:
        graph = json.loads(graph_json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return graph if isinstance(graph, dict) else {}


def _kind_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        kind = str(row.get("kind"))
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def _event_node_count(graph: dict[str, Any]) -> int:
    node_counts = _dict(graph.get("node_counts"))
    return int(node_counts.get("log_event", 0)) + int(node_counts.get("span_event", 0))


def _merge_properties(
    current: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(current)
    for key, value in update.items():
        if value in (None, "", []):
            continue
        if key not in merged or merged[key] in (None, "", []):
            merged[key] = value
    return merged


def _loads_json(value: object) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    return json.loads(value)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _list_of_strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _stable_id(*parts: object) -> str:
    return _stable_hash(parts)[:24]


def _stable_hash(value: object) -> str:
    return hashlib.sha256(_json_dumps(value).encode("utf-8")).hexdigest()


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)
