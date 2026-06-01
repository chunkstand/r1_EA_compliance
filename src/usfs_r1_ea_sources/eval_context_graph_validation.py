from __future__ import annotations

from pathlib import Path
from typing import Any


def store_checks(store: dict[str, Any]) -> list[dict[str, Any]]:
    row_counts = {table: len(rows) for table, rows in store["tables"].items()}
    return [
        {
            "name": "required_store_tables_present",
            "passed": not store["missing_tables"],
            "missing_tables": store["missing_tables"],
        },
        {
            "name": "store_readable",
            "passed": not store["read_errors"],
            "read_errors": store["read_errors"],
        },
        {
            "name": "store_rows_present",
            "passed": all(count > 0 for count in row_counts.values()),
            "row_counts": row_counts,
        },
    ]


def graph_checks(
    graph: dict[str, Any],
    contract: dict[str, Any],
    *,
    graph_schema_version: str,
) -> list[dict[str, Any]]:
    nodes = _list_of_dicts(graph.get("nodes"))
    edges = _list_of_dicts(graph.get("edges"))
    node_ids = {str(node.get("id")) for node in nodes}
    node_counts = _dict(graph.get("node_counts"))
    edge_counts = _dict(graph.get("edge_counts"))
    required_node_kinds = set(_list_of_strings(contract.get("required_node_kinds")))
    required_edge_kinds = set(_list_of_strings(contract.get("required_edge_kinds")))
    prohibited_node_kinds = set(_list_of_strings(contract.get("prohibited_node_kinds")))
    missing_node_kinds = sorted(
        kind for kind in required_node_kinds if int(node_counts.get(kind, 0)) == 0
    )
    missing_edge_kinds = sorted(
        kind for kind in required_edge_kinds if int(edge_counts.get(kind, 0)) == 0
    )
    unresolved_edges = [
        {
            "edge_id": str(edge.get("id")),
            "from_node_id": str(edge.get("from_node_id")),
            "to_node_id": str(edge.get("to_node_id")),
        }
        for edge in edges
        if edge.get("from_node_id") not in node_ids or edge.get("to_node_id") not in node_ids
    ]
    prohibited_nodes = [
        {"node_id": str(node.get("id")), "kind": str(node.get("kind"))}
        for node in nodes
        if node.get("kind") in prohibited_node_kinds
    ]
    path_failures = _trace_result_score_path_failures(nodes, edges)
    artifact_failures = _artifact_provenance_failures(nodes)
    event_failures = _event_emission_failures(nodes, edges)
    command_event_failures = _command_event_join_failures(graph, nodes, edges)
    graph_policy = _dict(graph.get("graph_policy"))
    return [
        {
            "name": "graph_schema_version",
            "passed": graph.get("schema_version") == graph_schema_version,
            "actual": graph.get("schema_version"),
        },
        {
            "name": "required_node_kinds_present",
            "passed": not missing_node_kinds,
            "missing_node_kinds": missing_node_kinds,
        },
        {
            "name": "required_edge_kinds_present",
            "passed": not missing_edge_kinds,
            "missing_edge_kinds": missing_edge_kinds,
        },
        {
            "name": "edges_resolve_to_nodes",
            "passed": not unresolved_edges,
            "unresolved_edges": unresolved_edges[:20],
            "unresolved_edge_count": len(unresolved_edges),
        },
        {
            "name": "trace_result_score_paths_present",
            "passed": not path_failures,
            "failure_count": len(path_failures),
            "failures": path_failures[:20],
        },
        {
            "name": "artifact_provenance_present",
            "passed": not artifact_failures,
            "failure_count": len(artifact_failures),
            "failures": artifact_failures[:20],
        },
        {
            "name": "event_nodes_have_emitted_edges",
            "passed": not event_failures,
            "failure_count": len(event_failures),
            "failures": event_failures[:20],
        },
        {
            "name": "event_source_rows_materialized",
            "passed": _event_source_rows_materialized(graph),
            "event_sources": graph.get("event_sources", []),
        },
        {
            "name": "command_event_nodes_joined",
            "passed": not command_event_failures,
            "failure_count": len(command_event_failures),
            "failures": command_event_failures[:20],
        },
        {
            "name": "source_knowledge_graph_nodes_excluded",
            "passed": not prohibited_nodes
            and bool(graph_policy.get("source_knowledge_graph_excluded")),
            "prohibited_node_count": len(prohibited_nodes),
            "prohibited_nodes": prohibited_nodes[:20],
        },
        {
            "name": "local_source_of_record_policy",
            "passed": bool(graph_policy.get("local_source_of_record"))
            and not bool(graph_policy.get("external_export_approved")),
            "graph_policy": graph_policy,
        },
    ]


def graph_file_checks(graph_json_path: Path, graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": "graph_file_exists",
            "passed": graph_json_path.exists(),
            "path": str(graph_json_path),
        },
        {
            "name": "graph_file_is_object",
            "passed": bool(graph),
        },
    ]


def target_ids(graph: dict[str, Any], kind: str) -> list[str]:
    target_ids = {
        str(_dict(node.get("properties")).get("target_id"))
        for node in _list_of_dicts(graph.get("nodes"))
        if node.get("kind") == kind and _dict(node.get("properties")).get("target_id")
    }
    return sorted(target_ids)


def _trace_result_score_path_failures(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, str]]:
    node_by_id = {str(node.get("id")): node for node in nodes}
    trace_node_by_trace_id = {
        str(_dict(node.get("properties")).get("trace_id")): str(node.get("id"))
        for node in nodes
        if node.get("kind") == "trace"
    }
    scores_by_result_node = {
        str(edge.get("from_node_id"))
        for edge in edges
        if edge.get("kind") == "SCORED_AS"
    }
    evaluated_result_by_trace_node = {
        (str(edge.get("from_node_id")), str(edge.get("to_node_id")))
        for edge in edges
        if edge.get("kind") == "EVALUATED_BY"
        and node_by_id.get(str(edge.get("from_node_id")), {}).get("kind") == "trace"
    }
    failures: list[dict[str, str]] = []
    for node in nodes:
        if node.get("kind") != "eval_result":
            continue
        properties = _dict(node.get("properties"))
        result_node_id = str(node.get("id"))
        trace_id = _string(properties.get("trace_id"))
        trace_node_id = trace_node_by_trace_id.get(trace_id or "")
        if trace_node_id is None:
            failures.append(
                {
                    "eval_result_node_id": result_node_id,
                    "reason": "missing_trace_node",
                }
            )
            continue
        if (trace_node_id, result_node_id) not in evaluated_result_by_trace_node:
            failures.append(
                {
                    "eval_result_node_id": result_node_id,
                    "reason": "missing_trace_to_result_edge",
                }
            )
        if result_node_id not in scores_by_result_node:
            failures.append(
                {
                    "eval_result_node_id": result_node_id,
                    "reason": "missing_result_to_score_edge",
                }
            )
    return failures


def _artifact_provenance_failures(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for node in nodes:
        if node.get("kind") != "artifact":
            continue
        properties = _dict(node.get("properties"))
        if not any(
            properties.get(key)
            for key in (
                "artifact_ref",
                "path",
                "origin_artifact_sha256",
                "artifact_sha256",
                "current_artifact_sha256",
                "input_hash",
                "output_hash",
            )
        ):
            failures.append(
                {
                    "node_id": str(node.get("id")),
                    "reason": "missing_artifact_ref_or_hash",
                }
            )
    return failures


def _event_emission_failures(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, str]]:
    event_node_ids = {
        str(node.get("id"))
        for node in nodes
        if node.get("kind") in {"log_event", "span_event"}
    }
    emitted_event_ids = {
        str(edge.get("to_node_id"))
        for edge in edges
        if edge.get("kind") == "EMITTED"
    }
    return [
        {"node_id": node_id, "reason": "missing_incoming_emitted_edge"}
        for node_id in sorted(event_node_ids - emitted_event_ids)
    ]


def _event_source_rows_materialized(graph: dict[str, Any]) -> bool:
    event_sources = _list_of_dicts(graph.get("event_sources"))
    return all(
        int(source.get("row_count") or 0)
        == int(source.get("materialized_event_count") or 0)
        and int(source.get("parse_error_count") or 0) == 0
        for source in event_sources
    )


def _command_event_join_failures(
    graph: dict[str, Any],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, str]]:
    emitted_event_ids = {
        str(edge.get("to_node_id"))
        for edge in edges
        if edge.get("kind") == "EMITTED"
    }
    command_event_nodes = [
        node
        for node in nodes
        if node.get("kind") in {"log_event", "span_event"}
        and _dict(node.get("properties")).get("command_event_phase")
    ]
    failures: list[dict[str, str]] = []
    for node in command_event_nodes:
        properties = _dict(node.get("properties"))
        node_id = str(node.get("id"))
        for required_property in (
            "command",
            "command_event_phase",
            "command_invocation_id",
            "payload_sha256",
        ):
            if not properties.get(required_property):
                failures.append(
                    {
                        "node_id": node_id,
                        "reason": f"missing_{required_property}",
                    }
                )
        if node_id not in emitted_event_ids:
            failures.append(
                {
                    "node_id": node_id,
                    "reason": "missing_incoming_emitted_edge",
                }
            )

    canonical_sources = [
        source
        for source in _list_of_dicts(graph.get("event_sources"))
        if source.get("source_kind") == "canonical_command_event_log"
    ]
    if canonical_sources and not command_event_nodes:
        failures.append(
            {
                "node_id": "",
                "reason": "canonical_command_event_log_without_command_events",
            }
        )
    return failures


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _list_of_strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
