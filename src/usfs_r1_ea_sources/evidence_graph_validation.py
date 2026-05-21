from __future__ import annotations

from collections import Counter
from contextlib import closing
from importlib import import_module
from pathlib import Path
import hashlib
import json
import sqlite3

from .artifact_utils import _extraction_summary_is_complete
from .artifact_utils import _int_from_summary
from .artifact_utils import _read_json
from .artifact_utils import _read_jsonl
from .artifact_utils import _safe_int
from .source_set_support import source_derived_dir


DEFAULT_RETRIEVAL_INDEX_FILENAME = "evidence_index.sqlite"
RETRIEVAL_BINDING_FIELDS = (
    "source_set_id",
    "source_record_id",
    "chunk_index",
    "title",
    "document_role",
    "authority_level",
    "host",
    "expected_parser",
    "artifact_sha256",
    "artifact_path",
    "citation_label",
    "original_url",
    "effective_url",
    "final_url",
    "parser_name",
    "parser_version",
    "extracted_at",
    "source_text_path",
    "char_start",
    "char_end",
    "page",
    "section",
    "heading",
    "content_sha256",
    "text",
)
INTEGER_BINDING_FIELDS = {"chunk_index", "char_start", "char_end", "page"}


_EVIDENCE_GRAPH = import_module("usfs_r1_ea_sources.evidence_graph")
_evidence_span_node_id = _EVIDENCE_GRAPH._evidence_span_node_id
_graph_metrics = _EVIDENCE_GRAPH._graph_metrics
_preview = _EVIDENCE_GRAPH._preview
_topic_node_id = _EVIDENCE_GRAPH._topic_node_id


def validate_evidence_graph_outputs(
    *,
    output_dir: Path,
    source_set_id: str,
    catalog_validation_path: Path | None = None,
    catalog_validation: dict | None = None,
    nodes_path: Path | None = None,
    edges_path: Path | None = None,
    chunks_path: Path | None = None,
    extraction_validation_path: Path | None = None,
    extraction_validation: dict | None = None,
    extraction_summary_path: Path | None = None,
    extraction_summary: dict | None = None,
    retrieval_validation_path: Path | None = None,
    retrieval_validation: dict | None = None,
    retrieval_summary_path: Path | None = None,
    retrieval_summary: dict | None = None,
    retrieval_index_path: Path | None = None,
    retrieval_index_records: dict[str, dict] | None = None,
    retrieval_index_error: str | None = None,
    chunks: list[dict] | None = None,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    metrics: dict | None = None,
    allow_partial_retrieval: bool = False,
) -> dict:
    output_dir = Path(output_dir)
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    graph_dir = derived_source_dir / "evidence_graph"
    chunks_path = chunks_path or derived_source_dir / "chunks" / "chunks.jsonl"
    nodes_path = nodes_path or graph_dir / "document_graph_nodes.jsonl"
    edges_path = edges_path or graph_dir / "document_graph_edges.jsonl"
    catalog_validation_path = catalog_validation_path or output_dir / "catalog" / "catalog_validation.json"
    extraction_validation_path = (
        extraction_validation_path
        or derived_source_dir / "diagnostics" / "extraction_validation.json"
    )
    extraction_summary_path = (
        extraction_summary_path or derived_source_dir / "diagnostics" / "summary.json"
    )
    retrieval_validation_path = (
        retrieval_validation_path or derived_source_dir / "retrieval" / "retrieval_validation.json"
    )
    retrieval_summary_path = retrieval_summary_path or derived_source_dir / "retrieval" / "summary.json"
    if catalog_validation is None and catalog_validation_path.exists():
        catalog_validation = _read_json(catalog_validation_path)
    if extraction_validation is None and extraction_validation_path.exists():
        extraction_validation = _read_json(extraction_validation_path)
    if extraction_summary is None and extraction_summary_path.exists():
        extraction_summary = _read_json(extraction_summary_path)
    if retrieval_validation is None and retrieval_validation_path.exists():
        retrieval_validation = _read_json(retrieval_validation_path)
    if retrieval_summary is None and retrieval_summary_path.exists():
        retrieval_summary = _read_json(retrieval_summary_path)
    retrieval_index_path = retrieval_index_path or _retrieval_index_path(
        derived_source_dir,
        retrieval_summary,
    )
    if retrieval_index_records is None:
        retrieval_index_records, retrieval_index_error = _load_retrieval_index_records(
            retrieval_index_path
        )
    chunks = chunks if chunks is not None else (_read_jsonl(chunks_path) if chunks_path.exists() else [])
    nodes = nodes if nodes is not None else (_read_jsonl(nodes_path) if nodes_path.exists() else [])
    edges = edges if edges is not None else (_read_jsonl(edges_path) if edges_path.exists() else [])
    metrics = metrics or _graph_metrics(nodes=nodes, edges=edges, chunks=chunks)

    checks = [
        {
            "name": "catalog_validation_passed",
            "passed": bool(catalog_validation and catalog_validation.get("passed")),
            "details": {
                "path": str(catalog_validation_path),
                "exists": catalog_validation_path.exists(),
                "passed": bool(catalog_validation and catalog_validation.get("passed")),
            },
        },
        {
            "name": "extraction_validation_passed",
            "passed": bool(extraction_validation and extraction_validation.get("passed")),
            "details": {
                "path": str(extraction_validation_path),
                "exists": extraction_validation_path.exists(),
                "passed": bool(extraction_validation and extraction_validation.get("passed")),
            },
        },
        {
            "name": "extraction_scope_is_complete",
            "passed": _extraction_summary_is_complete(extraction_summary),
            "details": {
                "path": str(extraction_summary_path),
                "exists": extraction_summary_path.exists(),
                "complete": _extraction_summary_is_complete(extraction_summary),
                "catalog_source_count": _int_from_summary(
                    extraction_summary,
                    "catalog_source_count",
                ),
                "selected_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_source_count",
                ),
                "required_extraction_source_count": _int_from_summary(
                    extraction_summary,
                    "required_extraction_source_count",
                ),
                "selected_required_extraction_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_required_extraction_source_count",
                ),
                "extracted_count": _int_from_summary(extraction_summary, "extracted_count"),
                "failed_count": _int_from_summary(extraction_summary, "failed_count"),
                "skipped_excluded_count": _int_from_summary(
                    extraction_summary,
                    "skipped_excluded_count",
                ),
                "filters": (extraction_summary or {}).get("filters", {}),
            },
        },
        {
            "name": "retrieval_validation_passed",
            "passed": bool(retrieval_validation and retrieval_validation.get("passed")),
            "details": {
                "path": str(retrieval_validation_path),
                "exists": retrieval_validation_path.exists(),
                "passed": bool(retrieval_validation and retrieval_validation.get("passed")),
            },
        },
        {
            "name": "retrieval_is_reviewer_ready",
            "passed": bool(retrieval_summary and retrieval_summary.get("reviewer_ready"))
            or allow_partial_retrieval,
            "details": {
                "path": str(retrieval_summary_path),
                "exists": retrieval_summary_path.exists(),
                "allow_partial_retrieval": allow_partial_retrieval,
                "reviewer_ready": bool(
                    retrieval_summary and retrieval_summary.get("reviewer_ready")
                ),
            },
        },
        _check_retrieval_index_readable(
            retrieval_index_path,
            retrieval_index_records,
            retrieval_index_error,
        ),
        _check_chunk_source_set_ids_match(source_set_id, chunks),
        _check_chunk_content_hashes(chunks),
        _check_chunks_match_retrieval_index(
            chunks,
            retrieval_index_records,
            retrieval_index_error,
        ),
        _check_nodes_and_edges_created(nodes, edges),
        _check_unique_ids(nodes, key="id", check_name="node_ids_are_unique"),
        _check_unique_ids(edges, key="id", check_name="edge_ids_are_unique"),
        _check_edges_resolve(nodes, edges),
        _check_chunk_nodes_exist(chunks, nodes),
        _check_chunks_have_evidence_spans(chunks, nodes, edges),
        _check_evidence_span_content_matches_chunks(chunks, nodes),
        _check_chunks_trace_to_artifacts(chunks, edges),
        _check_chunks_have_topic_edges(chunks, edges),
        _check_graph_health(metrics),
    ]
    ignored_checks = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    passed = all(check["passed"] for check in checks)
    if allow_partial_retrieval:
        passed = all(
            check["passed"] or check["name"] in ignored_checks
            for check in checks
        )
    return {
        "source_set_id": source_set_id,
        "passed": passed,
        "checks": checks,
        "metrics": metrics,
    }


def _load_retrieval_index_records(index_path: Path) -> tuple[dict[str, dict], str | None]:
    if not index_path.exists():
        return {}, f"missing retrieval index: {index_path}"
    query = """
        SELECT
          chunk_id, source_set_id, source_record_id, chunk_index, title, document_role,
          authority_level, host, expected_parser, artifact_sha256, artifact_path,
          citation_label, original_url, effective_url, final_url, parser_name,
          parser_version, extracted_at, source_text_path, char_start, char_end, page,
          section, heading, content_sha256, review_topics_json, text
        FROM chunks
        ORDER BY source_record_id, chunk_index
    """
    try:
        with closing(sqlite3.connect(index_path)) as connection:
            connection.row_factory = sqlite3.Row
            return {str(row["chunk_id"]): dict(row) for row in connection.execute(query)}, None
    except sqlite3.Error as error:
        return {}, str(error)


def _check_retrieval_index_readable(
    index_path: Path,
    retrieval_index_records: dict[str, dict],
    retrieval_index_error: str | None,
) -> dict:
    return {
        "name": "retrieval_index_exists_and_readable",
        "passed": retrieval_index_error is None and bool(retrieval_index_records),
        "details": {
            "path": str(index_path),
            "exists": index_path.exists(),
            "error": retrieval_index_error,
            "chunk_count": len(retrieval_index_records),
        },
    }


def _check_chunk_source_set_ids_match(source_set_id: str, chunks: list[dict]) -> dict:
    mismatches = [
        {
            "chunk_id": chunk.get("chunk_id"),
            "expected_source_set_id": source_set_id,
            "actual_source_set_id": chunk.get("source_set_id"),
        }
        for chunk in chunks
        if chunk.get("source_set_id") != source_set_id
    ]
    return {
        "name": "chunk_source_set_ids_match",
        "passed": bool(chunks) and not mismatches,
        "details": {
            "expected_source_set_id": source_set_id,
            "mismatches": mismatches[:50],
            "mismatch_count": len(mismatches),
        },
    }


def _check_chunk_content_hashes(chunks: list[dict]) -> dict:
    mismatches = []
    for chunk in chunks:
        expected = _text_sha256(chunk.get("text") or "")
        actual = str(chunk.get("content_sha256") or "")
        if actual != expected:
            mismatches.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "expected_content_sha256": expected,
                    "actual_content_sha256": actual,
                }
            )
    return {
        "name": "chunk_content_hashes_match_text",
        "passed": bool(chunks) and not mismatches,
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_chunks_match_retrieval_index(
    chunks: list[dict],
    retrieval_index_records: dict[str, dict],
    retrieval_index_error: str | None,
) -> dict:
    chunk_ids = {str(chunk.get("chunk_id")) for chunk in chunks if chunk.get("chunk_id")}
    index_ids = set(retrieval_index_records)
    missing_from_index = sorted(chunk_ids - index_ids)
    stale_in_index = sorted(index_ids - chunk_ids)
    mismatches = []
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "")
        index_record = retrieval_index_records.get(chunk_id)
        if not index_record:
            continue
        for field in RETRIEVAL_BINDING_FIELDS:
            chunk_value = _normalize_binding_value(chunk.get(field), field)
            index_value = _normalize_binding_value(index_record.get(field), field)
            if chunk_value != index_value:
                mismatches.append(
                    {
                        "chunk_id": chunk_id,
                        "field": field,
                        "chunk_value": _safe_detail_value(chunk.get(field)),
                        "index_value": _safe_detail_value(index_record.get(field)),
                    }
                )
        chunk_topics = _normalized_topics(chunk.get("review_topics"))
        index_topics = _normalized_topics(index_record.get("review_topics_json"))
        if chunk_topics != index_topics:
            mismatches.append(
                {
                    "chunk_id": chunk_id,
                    "field": "review_topics",
                    "chunk_value": chunk_topics,
                    "index_value": index_topics,
                }
            )
    passed = (
        retrieval_index_error is None
        and bool(chunks)
        and chunk_ids == index_ids
        and not mismatches
    )
    return {
        "name": "chunks_match_retrieval_index",
        "passed": passed,
        "details": {
            "retrieval_index_error": retrieval_index_error,
            "chunk_count": len(chunk_ids),
            "retrieval_index_chunk_count": len(index_ids),
            "missing_from_index": missing_from_index[:50],
            "missing_from_index_count": len(missing_from_index),
            "stale_in_index": stale_in_index[:50],
            "stale_in_index_count": len(stale_in_index),
            "mismatches": mismatches[:50],
            "mismatch_count": len(mismatches),
        },
    }


def _check_nodes_and_edges_created(nodes: list[dict], edges: list[dict]) -> dict:
    return {
        "name": "graph_nodes_and_edges_created",
        "passed": bool(nodes) and bool(edges),
        "details": {"node_count": len(nodes), "edge_count": len(edges)},
    }


def _check_unique_ids(records: list[dict], *, key: str, check_name: str) -> dict:
    counts = Counter(record.get(key) for record in records)
    duplicates = sorted(record_id for record_id, count in counts.items() if count > 1)
    return {
        "name": check_name,
        "passed": not duplicates,
        "details": {"duplicate_ids": duplicates[:50], "duplicate_count": len(duplicates)},
    }


def _check_edges_resolve(nodes: list[dict], edges: list[dict]) -> dict:
    node_ids = {node["id"] for node in nodes}
    dangling = [
        edge["id"]
        for edge in edges
        if edge["source"] not in node_ids or edge["target"] not in node_ids
    ]
    return {
        "name": "edges_resolve_to_existing_nodes",
        "passed": not dangling,
        "details": {"edge_ids": dangling[:50], "dangling_edge_count": len(dangling)},
    }


def _check_chunk_nodes_exist(chunks: list[dict], nodes: list[dict]) -> dict:
    node_ids = {node["id"] for node in nodes}
    missing = [chunk["chunk_id"] for chunk in chunks if chunk["chunk_id"] not in node_ids]
    return {
        "name": "every_chunk_has_graph_node",
        "passed": not missing and bool(chunks),
        "details": {"chunk_ids": missing[:50], "missing_count": len(missing)},
    }


def _check_chunks_have_evidence_spans(
    chunks: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_ids = {node["id"] for node in nodes if node["type"] == "EvidenceSpan"}
    edge_pairs = {
        (edge["source"], edge["target"])
        for edge in edges
        if edge["relationship"] == "CHUNK_HAS_EVIDENCE_SPAN"
    }
    missing = []
    for chunk in chunks:
        span_id = _evidence_span_node_id(chunk)
        if span_id not in node_ids or (chunk["chunk_id"], span_id) not in edge_pairs:
            missing.append(chunk["chunk_id"])
    return {
        "name": "every_chunk_has_evidence_span",
        "passed": not missing and bool(chunks),
        "details": {"chunk_ids": missing[:50], "missing_count": len(missing)},
    }


def _check_evidence_span_content_matches_chunks(chunks: list[dict], nodes: list[dict]) -> dict:
    spans_by_chunk_id = {
        node.get("chunk_id"): node
        for node in nodes
        if node.get("type") == "EvidenceSpan" and node.get("chunk_id")
    }
    mismatches = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        span = spans_by_chunk_id.get(chunk_id)
        if not span:
            mismatches.append({"chunk_id": chunk_id, "reason": "missing_evidence_span"})
            continue
        expected_hash = _text_sha256(chunk.get("text") or "")
        if span.get("content_sha256") != chunk.get("content_sha256"):
            mismatches.append(
                {
                    "chunk_id": chunk_id,
                    "reason": "span_hash_differs_from_chunk_hash",
                }
            )
        if span.get("content_sha256") != expected_hash:
            mismatches.append(
                {
                    "chunk_id": chunk_id,
                    "reason": "span_hash_differs_from_text_hash",
                }
            )
        if span.get("text") != chunk.get("text"):
            mismatches.append({"chunk_id": chunk_id, "reason": "span_text_differs_from_chunk"})
    return {
        "name": "evidence_span_content_matches_chunks",
        "passed": bool(chunks) and not mismatches,
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_chunks_trace_to_artifacts(chunks: list[dict], edges: list[dict]) -> dict:
    edge_pairs = {
        (edge["source"], edge["target"])
        for edge in edges
        if edge["relationship"] == "CHUNK_DERIVED_FROM_ARTIFACT"
    }
    missing = []
    for chunk in chunks:
        artifact_node_id = f"artifact:{chunk['artifact_sha256']}"
        if (chunk["chunk_id"], artifact_node_id) not in edge_pairs:
            missing.append(chunk["chunk_id"])
    return {
        "name": "every_chunk_traces_to_artifact",
        "passed": not missing and bool(chunks),
        "details": {"chunk_ids": missing[:50], "missing_count": len(missing)},
    }


def _check_chunks_have_topic_edges(chunks: list[dict], edges: list[dict]) -> dict:
    edge_pairs = {
        (edge["source"], edge["target"])
        for edge in edges
        if edge["relationship"] == "CHUNK_SUPPORTS_REVIEW_TOPIC"
    }
    missing = []
    for chunk in chunks:
        topics = chunk.get("review_topics", [])
        if not topics:
            missing.append(chunk["chunk_id"])
            continue
        if not any((chunk["chunk_id"], _topic_node_id(topic)) in edge_pairs for topic in topics):
            missing.append(chunk["chunk_id"])
    return {
        "name": "every_chunk_has_review_topic_edge",
        "passed": not missing and bool(chunks),
        "details": {"chunk_ids": missing[:50], "missing_count": len(missing)},
    }


def _check_graph_health(metrics: dict) -> dict:
    passed = (
        metrics["dangling_edge_count"] == 0
        and metrics["isolated_node_count"] == 0
        and metrics["evidence_coverage_rate"] == 1.0
        and metrics["chunk_topic_coverage_rate"] == 1.0
        and metrics["connected_component_count"] == 1
    )
    return {
        "name": "graph_health_metrics_pass",
        "passed": passed,
        "details": metrics,
    }


def _sqlite_graph_checks(
    path: Path,
    *,
    expected_node_count: int,
    expected_edge_count: int,
) -> list[dict]:
    if not path.exists():
        return [
            {
                "name": "sqlite_graph_exists",
                "passed": False,
                "details": {"path": str(path)},
            }
        ]
    try:
        with closing(sqlite3.connect(path)) as connection:
            node_count = connection.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
            edge_count = connection.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
    except sqlite3.Error as error:
        return [
            {
                "name": "sqlite_graph_readable",
                "passed": False,
                "details": {"path": str(path), "error": str(error)},
            }
        ]
    return [
        {
            "name": "sqlite_graph_node_count_matches_jsonl",
            "passed": node_count == expected_node_count,
            "details": {"expected": expected_node_count, "actual": node_count},
        },
        {
            "name": "sqlite_graph_edge_count_matches_jsonl",
            "passed": edge_count == expected_edge_count,
            "details": {"expected": expected_edge_count, "actual": edge_count},
        },
    ]


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_retrieval: bool,
) -> dict:
    merged_checks = [*validation["checks"], *checks]
    ignored = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    passed = all(
        check["passed"] or (allow_partial_retrieval and check["name"] in ignored)
        for check in merged_checks
    )
    return {
        **validation,
        "passed": passed,
        "checks": merged_checks,
    }


def _check_detail_count(validation: dict, check_name: str, detail_key: str) -> int:
    for check in validation.get("checks", []):
        if check.get("name") == check_name:
            return _safe_int((check.get("details") or {}).get(detail_key))
    return 0


def _retrieval_index_path(source_derived_dir: Path, retrieval_summary: dict | None) -> Path:
    summary_path = (retrieval_summary or {}).get("sqlite_path")
    if summary_path:
        return Path(str(summary_path))
    return source_derived_dir / "retrieval" / DEFAULT_RETRIEVAL_INDEX_FILENAME


def _normalize_binding_value(value: object, field: str) -> object:
    if field in INTEGER_BINDING_FIELDS:
        if value in (None, ""):
            return None
        return _safe_int(value)
    if value is None:
        return ""
    return str(value)


def _safe_detail_value(value: object) -> object:
    if isinstance(value, str) and len(value) > 240:
        return _preview(value)
    return value


def _normalized_topics(value: object) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = [value]
    if not isinstance(value, list):
        return []
    return sorted(str(item) for item in value if str(item))


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
