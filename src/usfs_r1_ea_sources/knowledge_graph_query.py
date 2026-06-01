from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any

from .artifact_utils import _source_set_id_from_catalog
from .artifact_utils import _utc_now
from .nepa_3d_graph_contract import NEPA_3D_GRAPH_SCHEMA_VERSION
from .records import sha256_file


KNOWLEDGE_GRAPH_QUERY_RESULTS_SCHEMA_VERSION = "knowledge-graph-query-results-v1"
DEFAULT_GRAPH_FILENAME = "nepa_3d_graph.json"
DEFAULT_QUERY_RESULTS_FILENAME = "knowledge_graph_query_results.json"
SUPPORTED_QUERY_TYPES = {
    "keyword",
    "node_id",
    "node_type",
    "edge_type",
    "source_record",
    "citation",
    "forest_unit",
    "readiness_blocker",
}


@dataclass(frozen=True)
class KnowledgeGraphQueryResult:
    output_path: Path
    summary: dict[str, Any]
    payload: dict[str, Any]


def run_knowledge_graph_query(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    review_id: str | None = None,
    query: str | None = None,
    query_type: str = "keyword",
    graph_path: Path | None = None,
    output_path: Path | None = None,
    limit: int = 10,
    node_type: str | None = None,
    edge_type: str | None = None,
    source_record_id: str | None = None,
    forest_unit_id: str | None = None,
    citation: str | None = None,
    readiness_status: str | None = None,
    require_hit: bool = False,
    fail_on_freshness_warning: bool = False,
) -> KnowledgeGraphQueryResult:
    output_dir = Path(output_dir)
    resolved_source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    resolved_graph_path = _resolve_graph_path(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        review_id=review_id,
        graph_path=graph_path,
    )
    payload = _build_query_payload(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        review_id=review_id,
        graph_path=resolved_graph_path,
        query=query,
        query_type=query_type,
        limit=limit,
        node_type=node_type,
        edge_type=edge_type,
        source_record_id=source_record_id,
        forest_unit_id=forest_unit_id,
        citation=citation,
        readiness_status=readiness_status,
        require_hit=require_hit,
        fail_on_freshness_warning=fail_on_freshness_warning,
    )
    resolved_output_path = output_path or _default_query_output_path(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        review_id=review_id,
        query_id=str(payload["query_id"]),
    )
    payload["summary"]["output_path"] = str(resolved_output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return KnowledgeGraphQueryResult(
        output_path=resolved_output_path,
        summary=payload["summary"],
        payload=payload,
    )


def _build_query_payload(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str | None,
    graph_path: Path,
    query: str | None,
    query_type: str,
    limit: int,
    node_type: str | None,
    edge_type: str | None,
    source_record_id: str | None,
    forest_unit_id: str | None,
    citation: str | None,
    readiness_status: str | None,
    require_hit: bool,
    fail_on_freshness_warning: bool,
) -> dict[str, Any]:
    query_type = _normalize_query_type(query_type)
    normalized_limit = max(0, int(limit))
    request = {
        "query_type": query_type,
        "query": _strip_or_none(query),
        "filters": _compact_dict(
            {
                "node_type": _strip_or_none(node_type),
                "edge_type": _strip_or_none(edge_type),
                "source_record_id": _strip_or_none(source_record_id),
                "forest_unit_id": _strip_or_none(forest_unit_id),
                "citation": _strip_or_none(citation),
                "readiness_status": _strip_or_none(readiness_status),
            }
        ),
        "limit": normalized_limit,
        "require_hit": require_hit,
        "fail_on_freshness_warning": fail_on_freshness_warning,
    }
    query_text = _query_text_from_request(request)
    graph = _read_graph(graph_path)
    nodes = _dict_list(graph.get("nodes"))
    edges = _dict_list(graph.get("edges"))
    node_by_id = {str(node.get("node_id")): node for node in nodes}
    incoming_edges, outgoing_edges = _edge_indexes(edges)
    freshness_warnings = _freshness_warnings(
        output_dir=output_dir,
        graph_path=graph_path,
        graph=graph,
    )
    results = _query_graph(
        nodes=nodes,
        edges=edges,
        node_by_id=node_by_id,
        incoming_edges=incoming_edges,
        outgoing_edges=outgoing_edges,
        request=request,
        query_text=query_text,
        limit=normalized_limit,
    )
    graph_schema_matches = graph.get("schema_version") == NEPA_3D_GRAPH_SCHEMA_VERSION
    graph_validation_passed = bool(_dict(graph.get("validation")).get("passed"))
    result_count = len(results)
    passed = (
        graph_schema_matches
        and graph_validation_passed
        and (not require_hit or result_count > 0)
        and (not fail_on_freshness_warning or not freshness_warnings)
    )
    failure_reasons = []
    if not graph_schema_matches:
        failure_reasons.append("graph_schema_mismatch")
    if not graph_validation_passed:
        failure_reasons.append("graph_validation_failed")
    if require_hit and result_count == 0:
        failure_reasons.append("required_query_hit_missing")
    if fail_on_freshness_warning and freshness_warnings:
        failure_reasons.append("freshness_warning_present")

    query_id = _stable_query_id(
        source_set_id=source_set_id,
        review_id=review_id,
        request=request,
    )
    return {
        "schema_version": KNOWLEDGE_GRAPH_QUERY_RESULTS_SCHEMA_VERSION,
        "query_id": query_id,
        "source_set_id": source_set_id,
        "review_id": review_id,
        "created_at": _utc_now(),
        "graph_path": str(graph_path),
        "graph_sha256": sha256_file(graph_path) if graph_path.exists() else None,
        "graph_schema_version": graph.get("schema_version"),
        "graph_validation_passed": graph_validation_passed,
        "request": request,
        "freshness_warnings": freshness_warnings,
        "result_count": result_count,
        "results": results,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "summary": {
            "passed": passed,
            "source_set_id": source_set_id,
            "review_id": review_id,
            "query_id": query_id,
            "query_type": query_type,
            "result_count": result_count,
            "freshness_warning_count": len(freshness_warnings),
            "failure_reasons": failure_reasons,
        },
    }


def _query_graph(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
    incoming_edges: dict[str, list[dict[str, Any]]],
    outgoing_edges: dict[str, list[dict[str, Any]]],
    request: dict[str, Any],
    query_text: str,
    limit: int,
) -> list[dict[str, Any]]:
    query_type = str(request["query_type"])
    filters = _dict(request.get("filters"))
    candidates: list[tuple[int, str, dict[str, Any], list[str]]] = []

    if query_type == "edge_type":
        for edge in edges:
            score, reasons = _edge_score(edge=edge, query_text=query_text, filters=filters)
            if score <= 0:
                continue
            candidates.append((score, str(edge.get("edge_id") or ""), edge, reasons))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        return [
            _edge_result(
                edge=edge,
                score=score,
                match_reasons=reasons,
                node_by_id=node_by_id,
            )
            for score, _, edge, reasons in candidates[:limit]
        ]

    for node in nodes:
        score, reasons = _node_score(node=node, query_text=query_text, query_type=query_type, filters=filters)
        if score <= 0:
            continue
        candidates.append((score, str(node.get("node_id") or ""), node, reasons))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [
        _node_result(
            node=node,
            score=score,
            match_reasons=reasons,
            incoming_edges=incoming_edges.get(str(node.get("node_id") or ""), []),
            outgoing_edges=outgoing_edges.get(str(node.get("node_id") or ""), []),
            node_by_id=node_by_id,
        )
        for score, _, node, reasons in candidates[:limit]
    ]


def _node_score(
    *,
    node: dict[str, Any],
    query_text: str,
    query_type: str,
    filters: dict[str, Any],
) -> tuple[int, list[str]]:
    reasons: list[str] = []
    if not _node_matches_filters(node=node, filters=filters):
        return 0, reasons

    lowered_query = query_text.casefold()
    if query_type == "node_id":
        if str(node.get("node_id") or "") == query_text:
            return 100, ["node_id_exact"]
        return 0, reasons
    if query_type == "node_type":
        expected = filters.get("node_type") or query_text
        if str(node.get("node_type") or "") == str(expected):
            return 90, ["node_type_exact"]
        return 0, reasons
    if query_type == "source_record":
        source_record_id = filters.get("source_record_id") or query_text
        if _node_source_record_id(node) == str(source_record_id):
            score = 100 if node.get("node_type") == "source_record" else 80
            return score, ["source_record_id_exact"]
        return 0, reasons
    if query_type == "citation":
        citation = filters.get("citation") or query_text
        citation_label = str(_dict(node.get("provenance")).get("citation_label") or "")
        if str(citation).casefold() in citation_label.casefold():
            score = 95 if node.get("node_type") == "source_record" else 75
            return score, ["citation_label_contains"]
        return 0, reasons
    if query_type == "forest_unit":
        forest_unit_id = str(filters.get("forest_unit_id") or query_text)
        if forest_unit_id and _forest_unit_matches(node=node, forest_unit_id=forest_unit_id):
            return 95, ["forest_unit_match"]
        return 0, reasons
    if query_type == "readiness_blocker":
        blocker = str(query_text)
        if blocker and _readiness_blocker_matches(node=node, blocker=blocker):
            score = 95 if node.get("node_type") == "readiness_blocker" else 75
            return score, ["readiness_blocker_match"]
        return 0, reasons

    if not lowered_query:
        return 50, ["filter_match"]
    haystack = _record_haystack(node)
    if lowered_query in haystack:
        reasons.append("keyword_contains")
        exact_label = str(node.get("label") or "").casefold() == lowered_query
        return (85 if exact_label else 60), reasons
    return 0, reasons


def _edge_score(
    *,
    edge: dict[str, Any],
    query_text: str,
    filters: dict[str, Any],
) -> tuple[int, list[str]]:
    expected_edge_type = str(filters.get("edge_type") or query_text)
    if expected_edge_type and str(edge.get("edge_type") or "") != expected_edge_type:
        return 0, []
    return 90, ["edge_type_exact"]


def _node_matches_filters(*, node: dict[str, Any], filters: dict[str, Any]) -> bool:
    if filters.get("node_type") and node.get("node_type") != filters["node_type"]:
        return False
    if filters.get("source_record_id") and _node_source_record_id(node) != filters["source_record_id"]:
        return False
    if filters.get("forest_unit_id") and not _forest_unit_matches(
        node=node,
        forest_unit_id=str(filters["forest_unit_id"]),
    ):
        return False
    if filters.get("citation"):
        citation_label = str(_dict(node.get("provenance")).get("citation_label") or "")
        if str(filters["citation"]).casefold() not in citation_label.casefold():
            return False
    if filters.get("readiness_status"):
        status = str(filters["readiness_status"])
        if status not in {
            str(node.get("display_status") or ""),
            str(node.get("review_readiness_status") or ""),
        } and status not in _string_list(node.get("readiness_blockers")):
            return False
    return True


def _node_result(
    *,
    node: dict[str, Any],
    score: int,
    match_reasons: list[str],
    incoming_edges: list[dict[str, Any]],
    outgoing_edges: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    node_id = str(node.get("node_id") or "")
    return {
        "result_type": "node",
        "score": score,
        "match_reasons": match_reasons,
        "node_id": node_id,
        "node_type": node.get("node_type"),
        "label": node.get("label"),
        "display_status": node.get("display_status"),
        "review_readiness_status": node.get("review_readiness_status"),
        "readiness_semantic_class": node.get("readiness_semantic_class"),
        "readiness_blockers": _string_list(node.get("readiness_blockers")),
        "provenance": _dict(node.get("provenance")),
        "currentness_metadata": _dict(node.get("currentness_metadata")),
        "metadata": _dict(node.get("metadata")),
        "citations": _citation_refs(node),
        "neighborhood": {
            "incoming_edge_count": len(incoming_edges),
            "outgoing_edge_count": len(outgoing_edges),
            "incoming_edges": [
                _compact_edge(edge=edge, node_by_id=node_by_id) for edge in incoming_edges[:5]
            ],
            "outgoing_edges": [
                _compact_edge(edge=edge, node_by_id=node_by_id) for edge in outgoing_edges[:5]
            ],
        },
    }


def _edge_result(
    *,
    edge: dict[str, Any],
    score: int,
    match_reasons: list[str],
    node_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "result_type": "edge",
        "score": score,
        "match_reasons": match_reasons,
        "edge_id": edge.get("edge_id"),
        "edge_type": edge.get("edge_type"),
        "source_node_id": edge.get("source_node_id"),
        "target_node_id": edge.get("target_node_id"),
        "source_node": _compact_node(node_by_id.get(str(edge.get("source_node_id") or ""))),
        "target_node": _compact_node(node_by_id.get(str(edge.get("target_node_id") or ""))),
        "display_status": edge.get("display_status"),
        "review_readiness_status": edge.get("review_readiness_status"),
        "readiness_semantic_class": edge.get("readiness_semantic_class"),
        "readiness_blockers": _string_list(edge.get("readiness_blockers")),
        "provenance": _dict(edge.get("provenance")),
        "metadata": _dict(edge.get("metadata")),
        "citations": _citation_refs(edge),
    }


def _freshness_warnings(
    *,
    output_dir: Path,
    graph_path: Path,
    graph: dict[str, Any],
) -> list[dict[str, Any]]:
    warnings = []
    if graph.get("schema_version") != NEPA_3D_GRAPH_SCHEMA_VERSION:
        warnings.append(
            {
                "warning_type": "graph_schema_mismatch",
                "expected": NEPA_3D_GRAPH_SCHEMA_VERSION,
                "actual": graph.get("schema_version"),
            }
        )
    if not bool(_dict(graph.get("validation")).get("passed")):
        warnings.append({"warning_type": "graph_validation_not_passed"})
    if not bool(_dict(graph.get("summary")).get("validation_passed")):
        warnings.append({"warning_type": "graph_summary_validation_not_passed"})

    for input_record in _dict_list(graph.get("inputs")):
        declared_path = _strip_or_none(input_record.get("path"))
        if not declared_path:
            continue
        input_path = _resolve_input_path(
            declared_path=declared_path,
            output_dir=output_dir,
            graph_path=graph_path,
        )
        declared_sha = _strip_or_none(input_record.get("sha256"))
        declared_exists = bool(input_record.get("exists"))
        exists_now = input_path.exists()
        if declared_exists and not exists_now:
            warnings.append(
                {
                    "warning_type": "input_missing",
                    "input_name": input_record.get("name"),
                    "path": declared_path,
                }
            )
            continue
        if declared_sha and exists_now:
            actual_sha = sha256_file(input_path)
            if actual_sha != declared_sha:
                warnings.append(
                    {
                        "warning_type": "input_hash_mismatch",
                        "input_name": input_record.get("name"),
                        "path": declared_path,
                        "expected_sha256": declared_sha,
                        "actual_sha256": actual_sha,
                    }
                )
    return warnings


def _resolve_graph_path(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str | None,
    graph_path: Path | None,
) -> Path:
    if graph_path is not None:
        return Path(graph_path)
    if review_id:
        return output_dir / "reviews" / review_id / "knowledge_graph" / DEFAULT_GRAPH_FILENAME
    return output_dir / "derived" / source_set_id / "knowledge_graph" / DEFAULT_GRAPH_FILENAME


def _default_query_output_path(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str | None,
    query_id: str,
) -> Path:
    if review_id:
        graph_dir = output_dir / "reviews" / review_id / "knowledge_graph"
    else:
        graph_dir = output_dir / "derived" / source_set_id / "knowledge_graph"
    return graph_dir / "query_results" / f"{query_id}.json"


def _read_graph(graph_path: Path) -> dict[str, Any]:
    if not graph_path.exists():
        raise FileNotFoundError(f"knowledge graph export not found: {graph_path}")
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"knowledge graph export must be a JSON object: {graph_path}")
    return payload


def _normalize_query_type(query_type: str) -> str:
    normalized = str(query_type or "keyword").strip()
    if normalized not in SUPPORTED_QUERY_TYPES:
        raise ValueError(
            f"unsupported knowledge graph query_type {normalized!r}; "
            f"expected one of {sorted(SUPPORTED_QUERY_TYPES)}"
        )
    return normalized


def _query_text_from_request(request: dict[str, Any]) -> str:
    query_type = str(request["query_type"])
    filters = _dict(request.get("filters"))
    query = str(request.get("query") or "")
    fallback_by_type = {
        "node_id": query,
        "node_type": str(filters.get("node_type") or query),
        "edge_type": str(filters.get("edge_type") or query),
        "source_record": str(filters.get("source_record_id") or query),
        "citation": str(filters.get("citation") or query),
        "forest_unit": str(filters.get("forest_unit_id") or query),
        "readiness_blocker": str(filters.get("readiness_status") or query),
        "keyword": query,
    }
    resolved = fallback_by_type[query_type].strip()
    if query_type != "keyword" and not resolved:
        raise ValueError(f"knowledge graph query_type {query_type!r} requires a query or matching filter")
    if query_type == "keyword" and not resolved and not filters:
        raise ValueError("knowledge graph keyword query requires query text or at least one filter")
    return resolved


def _edge_indexes(
    edges: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    incoming: dict[str, list[dict[str, Any]]] = {}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        source = str(edge.get("source_node_id") or "")
        target = str(edge.get("target_node_id") or "")
        if source:
            outgoing.setdefault(source, []).append(edge)
        if target:
            incoming.setdefault(target, []).append(edge)
    return incoming, outgoing


def _record_haystack(record: dict[str, Any]) -> str:
    values = [
        record.get("node_id"),
        record.get("edge_id"),
        record.get("node_type"),
        record.get("edge_type"),
        record.get("label"),
        record.get("display_status"),
        record.get("review_readiness_status"),
        record.get("readiness_semantic_class"),
        json.dumps(record.get("provenance", {}), sort_keys=True),
        json.dumps(record.get("currentness_metadata", {}), sort_keys=True),
        json.dumps(record.get("metadata", {}), sort_keys=True),
        " ".join(_string_list(record.get("readiness_blockers"))),
    ]
    return " ".join(str(value) for value in values if value is not None).casefold()


def _citation_refs(record: dict[str, Any]) -> list[dict[str, Any]]:
    provenance = _dict(record.get("provenance"))
    citation_label = _strip_or_none(provenance.get("citation_label"))
    source_record_id = _strip_or_none(provenance.get("source_record_id"))
    artifact_sha256 = _strip_or_none(provenance.get("artifact_sha256"))
    url = _strip_or_none(provenance.get("url"))
    if not any((citation_label, source_record_id, artifact_sha256, url)):
        return []
    return [
        _compact_dict(
            {
                "citation_label": citation_label,
                "source_record_id": source_record_id,
                "artifact_sha256": artifact_sha256,
                "url": url,
            }
        )
    ]


def _compact_node(node: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(node, dict):
        return {}
    return _compact_dict(
        {
            "node_id": node.get("node_id"),
            "node_type": node.get("node_type"),
            "label": node.get("label"),
            "display_status": node.get("display_status"),
            "review_readiness_status": node.get("review_readiness_status"),
            "provenance": _dict(node.get("provenance")),
        }
    )


def _compact_edge(*, edge: dict[str, Any], node_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _compact_dict(
        {
            "edge_id": edge.get("edge_id"),
            "edge_type": edge.get("edge_type"),
            "source_node_id": edge.get("source_node_id"),
            "target_node_id": edge.get("target_node_id"),
            "source_node": _compact_node(node_by_id.get(str(edge.get("source_node_id") or ""))),
            "target_node": _compact_node(node_by_id.get(str(edge.get("target_node_id") or ""))),
        }
    )


def _forest_unit_matches(*, node: dict[str, Any], forest_unit_id: str) -> bool:
    provenance = _dict(node.get("provenance"))
    metadata = _dict(node.get("metadata"))
    values = {
        str(node.get("node_id") or ""),
        str(provenance.get("forest_unit_id") or ""),
        str(metadata.get("forest_unit_id") or ""),
    }
    return forest_unit_id in values or f"forest_unit:{forest_unit_id}" in values


def _readiness_blocker_matches(*, node: dict[str, Any], blocker: str) -> bool:
    provenance = _dict(node.get("provenance"))
    blockers = set(_string_list(node.get("readiness_blockers")))
    blockers.add(str(provenance.get("blocker_type") or ""))
    return blocker in blockers or blocker.casefold() in _record_haystack(node)


def _node_source_record_id(node: dict[str, Any]) -> str:
    provenance = _dict(node.get("provenance"))
    return str(provenance.get("source_record_id") or "").strip()


def _resolve_input_path(*, declared_path: str, output_dir: Path, graph_path: Path) -> Path:
    path = Path(declared_path)
    if path.is_absolute():
        return path
    candidates = [
        Path.cwd() / path,
        output_dir / path,
        graph_path.parent / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _stable_query_id(*, source_set_id: str, review_id: str | None, request: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "source_set_id": source_set_id,
            "review_id": review_id,
            "request": request,
        },
        sort_keys=True,
    )
    return "kg-query-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _strip_or_none(value: Any) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "", [], {})}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
