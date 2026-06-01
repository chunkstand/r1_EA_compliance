from __future__ import annotations

from collections import Counter, defaultdict, deque
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re
import sqlite3

from .artifact_utils import _extraction_summary_is_complete
from .artifact_utils import _read_json
from .artifact_utils import _read_jsonl
from .artifact_utils import _source_set_id_from_catalog
from .artifact_utils import _utc_now
from .artifact_utils import _write_json
from .catalog_surface import resolve_catalog_dir_for_source_set
from .source_set_support import source_derived_dir


GRAPH_SCHEMA_VERSION = "document-evidence-graph-v1"
DEFAULT_SQLITE_FILENAME = "evidence_graph.sqlite"


@dataclass(frozen=True)
class EvidenceGraphBuildResult:
    source_set_id: str
    graph_dir: Path
    nodes_path: Path
    edges_path: Path
    sqlite_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


def build_evidence_graph(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    catalog_dir: Path | None = None,
    chunks_path: Path | None = None,
    retrieval_validation_path: Path | None = None,
    retrieval_summary_path: Path | None = None,
    graph_dir: Path | None = None,
    allow_partial_retrieval: bool = False,
) -> EvidenceGraphBuildResult:
    """Build the v1 document evidence graph from extracted chunks and retrieval metadata."""

    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    graph_dir = Path(graph_dir) if graph_dir is not None else derived_source_dir / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_dir=catalog_dir,
    )

    chunks_path = (
        Path(chunks_path)
        if chunks_path is not None
        else derived_source_dir / "chunks" / "chunks.jsonl"
    )
    catalog_sqlite_path = catalog_dir / "review_sources.sqlite"
    catalog_validation_path = catalog_dir / "catalog_validation.json"
    extraction_validation_path = derived_source_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = derived_source_dir / "diagnostics" / "summary.json"
    retrieval_validation_path = (
        Path(retrieval_validation_path)
        if retrieval_validation_path is not None
        else derived_source_dir / "retrieval" / "retrieval_validation.json"
    )
    retrieval_summary_path = (
        Path(retrieval_summary_path)
        if retrieval_summary_path is not None
        else derived_source_dir / "retrieval" / "summary.json"
    )

    nodes_path = graph_dir / "document_graph_nodes.jsonl"
    edges_path = graph_dir / "document_graph_edges.jsonl"
    sqlite_path = graph_dir / DEFAULT_SQLITE_FILENAME
    validation_path = graph_dir / "evidence_graph_validation.json"
    summary_path = graph_dir / "summary.json"

    source_metadata = _load_source_metadata(catalog_sqlite_path)
    raw_chunks = _read_jsonl(chunks_path) if chunks_path.exists() else []
    chunks = [
        _chunk_with_review_topics(
            chunk,
            source_metadata.get(str(chunk.get("source_record_id")), {}).get(
                "review_topics",
                [],
            ),
        )
        for chunk in raw_chunks
    ]
    nodes, edges = _graph_records(
        source_set_id=source_set_id,
        chunks=chunks,
        source_metadata=source_metadata,
    )
    metrics = _graph_metrics(nodes=nodes, edges=edges, chunks=chunks)
    catalog_validation = (
        _read_json(catalog_validation_path) if catalog_validation_path.exists() else None
    )
    extraction_validation = (
        _read_json(extraction_validation_path) if extraction_validation_path.exists() else None
    )
    extraction_summary = (
        _read_json(extraction_summary_path) if extraction_summary_path.exists() else None
    )
    retrieval_validation = (
        _read_json(retrieval_validation_path) if retrieval_validation_path.exists() else None
    )
    retrieval_summary = (
        _read_json(retrieval_summary_path) if retrieval_summary_path.exists() else None
    )
    retrieval_index_path = _retrieval_index_path(source_derived_dir, retrieval_summary)
    retrieval_index_records, retrieval_index_error = _load_retrieval_index_records(
        retrieval_index_path
    )

    validation = _validation_report(
        output_dir=output_dir,
        source_set_id=source_set_id,
        nodes_path=nodes_path,
        edges_path=edges_path,
        chunks_path=chunks_path,
        chunks=chunks,
        nodes=nodes,
        edges=edges,
        metrics=metrics,
        catalog_validation_path=catalog_validation_path,
        catalog_validation=catalog_validation,
        extraction_validation_path=extraction_validation_path,
        extraction_validation=extraction_validation,
        extraction_summary_path=extraction_summary_path,
        extraction_summary=extraction_summary,
        retrieval_validation_path=retrieval_validation_path,
        retrieval_validation=retrieval_validation,
        retrieval_summary_path=retrieval_summary_path,
        retrieval_summary=retrieval_summary,
        retrieval_index_path=retrieval_index_path,
        retrieval_index_records=retrieval_index_records,
        retrieval_index_error=retrieval_index_error,
        allow_partial_retrieval=allow_partial_retrieval,
    )

    if validation["passed"]:
        _write_jsonl(nodes_path, nodes)
        _write_jsonl(edges_path, edges)
        _write_sqlite_graph(
            sqlite_path,
            source_set_id=source_set_id,
            nodes=nodes,
            edges=edges,
            metrics=metrics,
        )
        validation = _with_additional_checks(
            validation,
            _sqlite_graph_checks(
                sqlite_path,
                expected_node_count=len(nodes),
                expected_edge_count=len(edges),
            ),
            allow_partial_retrieval=allow_partial_retrieval,
        )
        if not validation["passed"]:
            sqlite_path.unlink(missing_ok=True)
    else:
        for path in (nodes_path, edges_path, sqlite_path):
            path.unlink(missing_ok=True)

    retrieval_reviewer_ready = bool(retrieval_summary and retrieval_summary.get("reviewer_ready"))
    reviewer_ready = validation["passed"] and retrieval_reviewer_ready
    summary = {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "graph_dir": str(graph_dir),
        "nodes_path": str(nodes_path),
        "edges_path": str(edges_path),
        "sqlite_path": str(sqlite_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "chunks_path": str(chunks_path),
        "catalog_dir": str(catalog_dir),
        "catalog_sqlite_path": str(catalog_sqlite_path),
        "retrieval_summary_path": str(retrieval_summary_path),
        "retrieval_validation_path": str(retrieval_validation_path),
        "retrieval_index_path": str(retrieval_index_path),
        "allow_partial_retrieval": allow_partial_retrieval,
        "validation_passed": validation["passed"],
        "reviewer_ready": reviewer_ready,
        "retrieval_reviewer_ready": retrieval_reviewer_ready,
        "extraction_complete": _extraction_summary_is_complete(extraction_summary),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "chunk_count": len(chunks),
        "retrieval_index_chunk_count": len(retrieval_index_records),
        "retrieval_binding_mismatch_count": _check_detail_count(
            validation,
            "chunks_match_retrieval_index",
            "mismatch_count",
        ),
        "chunk_hash_mismatch_count": _check_detail_count(
            validation,
            "chunk_content_hashes_match_text",
            "mismatch_count",
        ),
        "metrics": metrics,
        "node_type_counts": dict(Counter(node["type"] for node in nodes)),
        "edge_relationship_counts": dict(Counter(edge["relationship"] for edge in edges)),
    }
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
    return EvidenceGraphBuildResult(
        source_set_id=source_set_id,
        graph_dir=graph_dir,
        nodes_path=nodes_path,
        edges_path=edges_path,
        sqlite_path=sqlite_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
    )



def _graph_records(
    *,
    source_set_id: str,
    chunks: list[dict],
    source_metadata: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    nodes_by_id: dict[str, dict] = {}
    edges_by_id: dict[str, dict] = {}
    source_set_node_id = f"source_set:{source_set_id}"
    nodes_by_id[source_set_node_id] = _node(
        source_set_node_id,
        "SourceSet",
        source_set_id=source_set_id,
    )

    for chunk in chunks:
        source_record_id = str(chunk["source_record_id"])
        metadata = source_metadata.get(source_record_id, {})
        source_node_id = f"source:{source_record_id}"
        artifact_node_id = f"artifact:{chunk['artifact_sha256']}"
        text_node_id = _extracted_text_node_id(chunk)
        section_node_id = _section_node_id(chunk)
        chunk_node_id = chunk["chunk_id"]
        evidence_node_id = _evidence_span_node_id(chunk)
        parser_node_id = _parser_node_id(chunk)

        nodes_by_id.setdefault(
            source_node_id,
            _node(
                source_node_id,
                "SourceDocument",
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=chunk["title"],
                document_role=chunk["document_role"],
                authority_level=chunk["authority_level"],
                host=chunk.get("host"),
                citation_label=chunk["citation_label"],
                original_url=chunk["original_url"],
                effective_url=chunk["effective_url"],
                final_url=chunk.get("final_url"),
                issuer=metadata.get("issuer"),
                scope=metadata.get("scope"),
                applies_to=metadata.get("applies_to"),
            ),
        )
        nodes_by_id.setdefault(
            artifact_node_id,
            _node(
                artifact_node_id,
                "RawArtifact",
                artifact_sha256=chunk["artifact_sha256"],
                artifact_path=chunk["artifact_path"],
                final_url=chunk.get("final_url"),
            ),
        )
        nodes_by_id.setdefault(
            text_node_id,
            _node(
                text_node_id,
                "ExtractedText",
                source_record_id=source_record_id,
                artifact_sha256=chunk["artifact_sha256"],
                source_text_path=chunk.get("source_text_path"),
                extracted_at=chunk["extracted_at"],
            ),
        )
        nodes_by_id.setdefault(
            parser_node_id,
            _node(
                parser_node_id,
                "Parser",
                parser_name=chunk["parser_name"],
                parser_version=chunk["parser_version"],
            ),
        )
        nodes_by_id.setdefault(
            section_node_id,
            _node(
                section_node_id,
                "DocumentSection",
                source_record_id=source_record_id,
                section=chunk.get("section"),
                heading=chunk.get("heading"),
                page=chunk.get("page"),
                label=_section_label(chunk),
            ),
        )
        nodes_by_id[chunk_node_id] = _node(
            chunk_node_id,
            "DocumentChunk",
            chunk_id=chunk_node_id,
            source_record_id=source_record_id,
            chunk_index=int(chunk.get("chunk_index") or 0),
            char_start=int(chunk["char_start"]),
            char_end=int(chunk["char_end"]),
            content_sha256=chunk["content_sha256"],
            text_preview=_preview(chunk.get("text") or ""),
        )
        nodes_by_id[evidence_node_id] = _node(
            evidence_node_id,
            "EvidenceSpan",
            source_record_id=source_record_id,
            chunk_id=chunk_node_id,
            citation_label=chunk["citation_label"],
            artifact_sha256=chunk["artifact_sha256"],
            parser_name=chunk["parser_name"],
            parser_version=chunk["parser_version"],
            char_start=int(chunk["char_start"]),
            char_end=int(chunk["char_end"]),
            content_sha256=chunk["content_sha256"],
            text=chunk["text"],
        )

        _put_edge(edges_by_id, source_set_node_id, source_node_id, "SOURCE_SET_HAS_SOURCE")
        _put_edge(edges_by_id, source_node_id, artifact_node_id, "SOURCE_HAS_ARTIFACT")
        _put_edge(edges_by_id, artifact_node_id, text_node_id, "ARTIFACT_PARSED_TO_TEXT")
        _put_edge(edges_by_id, text_node_id, parser_node_id, "PRODUCED_BY_PARSER")
        _put_edge(edges_by_id, source_node_id, section_node_id, "SOURCE_HAS_SECTION")
        _put_edge(edges_by_id, section_node_id, chunk_node_id, "SECTION_HAS_CHUNK")
        _put_edge(edges_by_id, source_node_id, chunk_node_id, "SOURCE_HAS_CHUNK")
        _put_edge(edges_by_id, chunk_node_id, artifact_node_id, "CHUNK_DERIVED_FROM_ARTIFACT")
        _put_edge(edges_by_id, chunk_node_id, evidence_node_id, "CHUNK_HAS_EVIDENCE_SPAN")
        _put_edge(edges_by_id, evidence_node_id, source_node_id, "EVIDENCE_SUPPORTS_SOURCE")
        _put_edge(edges_by_id, evidence_node_id, artifact_node_id, "EVIDENCE_TRACES_TO_ARTIFACT")

        for topic in chunk.get("review_topics", []):
            topic_node_id = _topic_node_id(topic)
            nodes_by_id.setdefault(
                topic_node_id,
                _node(topic_node_id, "ReviewTopic", label=topic),
            )
            _put_edge(edges_by_id, source_node_id, topic_node_id, "SOURCE_SUPPORTS_REVIEW_TOPIC")
            _put_edge(edges_by_id, chunk_node_id, topic_node_id, "CHUNK_SUPPORTS_REVIEW_TOPIC")

    return list(nodes_by_id.values()), list(edges_by_id.values())


def _load_source_metadata(catalog_sqlite_path: Path) -> dict[str, dict]:
    if not catalog_sqlite_path.exists():
        return {}
    query = """
        SELECT
          source_record_id, issuer, scope, applies_to, trigger, currentness_notes
        FROM sources
    """
    try:
        with closing(sqlite3.connect(catalog_sqlite_path)) as connection:
            connection.row_factory = sqlite3.Row
            metadata = {row["source_record_id"]: dict(row) for row in connection.execute(query)}
            for source_record_id, topic in _load_review_topics(connection):
                metadata.setdefault(source_record_id, {"source_record_id": source_record_id})
                metadata[source_record_id].setdefault("review_topics", []).append(topic)
            return metadata
    except sqlite3.Error:
        return {}


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


def _load_review_topics(connection: sqlite3.Connection) -> list[tuple[str, str]]:
    query = """
        SELECT srt.source_record_id, rt.label
        FROM source_review_topics srt
        JOIN review_topics rt ON rt.topic_id = srt.topic_id
        ORDER BY srt.source_record_id, rt.label
    """
    return [
        (str(source_record_id), str(label))
        for source_record_id, label in connection.execute(query)
    ]


def _chunk_with_review_topics(chunk: dict, review_topics: list[str]) -> dict:
    merged = dict(chunk)
    if not merged.get("review_topics"):
        merged["review_topics"] = sorted(set(str(topic) for topic in review_topics if str(topic)))
    return merged


def _validation_report(
    *,
    output_dir: Path,
    source_set_id: str,
    nodes_path: Path,
    edges_path: Path,
    chunks_path: Path,
    chunks: list[dict],
    nodes: list[dict],
    edges: list[dict],
    metrics: dict,
    catalog_validation_path: Path,
    catalog_validation: dict | None,
    extraction_validation_path: Path,
    extraction_validation: dict | None,
    extraction_summary_path: Path,
    extraction_summary: dict | None,
    retrieval_validation_path: Path,
    retrieval_validation: dict | None,
    retrieval_summary_path: Path,
    retrieval_summary: dict | None,
    retrieval_index_path: Path,
    retrieval_index_records: dict[str, dict],
    retrieval_index_error: str | None,
    allow_partial_retrieval: bool,
) -> dict:
    from .evidence_graph_validation import validate_evidence_graph_outputs as _validate

    validation = _validate(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_validation_path=catalog_validation_path,
        catalog_validation=catalog_validation,
        nodes_path=nodes_path,
        edges_path=edges_path,
        chunks_path=chunks_path,
        extraction_validation_path=extraction_validation_path,
        extraction_validation=extraction_validation,
        extraction_summary_path=extraction_summary_path,
        extraction_summary=extraction_summary,
        retrieval_validation_path=retrieval_validation_path,
        retrieval_validation=retrieval_validation,
        retrieval_summary_path=retrieval_summary_path,
        retrieval_summary=retrieval_summary,
        retrieval_index_path=retrieval_index_path,
        retrieval_index_records=retrieval_index_records,
        retrieval_index_error=retrieval_index_error,
        chunks=chunks,
        nodes=nodes,
        edges=edges,
        metrics=metrics,
        allow_partial_retrieval=allow_partial_retrieval,
    )
    return validation


def _graph_metrics(*, nodes: list[dict], edges: list[dict], chunks: list[dict]) -> dict:
    node_ids = {node["id"] for node in nodes}
    degrees: Counter[str] = Counter()
    adjacency: dict[str, set[str]] = defaultdict(set)
    dangling = 0
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source not in node_ids or target not in node_ids:
            dangling += 1
            continue
        degrees[source] += 1
        degrees[target] += 1
        adjacency[source].add(target)
        adjacency[target].add(source)

    isolated = [node_id for node_id in node_ids if degrees[node_id] == 0]
    components = _component_count(node_ids, adjacency)
    node_type_counts = Counter(node["type"] for node in nodes)
    chunk_count = len(chunks)
    evidence_span_count = node_type_counts.get("EvidenceSpan", 0)
    topic_edge_chunk_ids = {
        edge["source"]
        for edge in edges
        if edge["relationship"] == "CHUNK_SUPPORTS_REVIEW_TOPIC"
    }
    source_artifact_source_ids = {
        edge["source"]
        for edge in edges
        if edge["relationship"] == "SOURCE_HAS_ARTIFACT"
    }
    chunk_source_ids = {f"source:{chunk['source_record_id']}" for chunk in chunks}
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "chunk_count": chunk_count,
        "source_document_count": node_type_counts.get("SourceDocument", 0),
        "raw_artifact_count": node_type_counts.get("RawArtifact", 0),
        "document_section_count": node_type_counts.get("DocumentSection", 0),
        "evidence_span_count": evidence_span_count,
        "review_topic_count": node_type_counts.get("ReviewTopic", 0),
        "connected_component_count": components,
        "isolated_node_count": len(isolated),
        "dangling_edge_count": dangling,
        "evidence_coverage_rate": _rate(evidence_span_count, chunk_count),
        "chunk_topic_coverage_rate": _rate(len(topic_edge_chunk_ids), chunk_count),
        "source_artifact_coverage_rate": _rate(
            len(source_artifact_source_ids & chunk_source_ids),
            len(chunk_source_ids),
        ),
    }


def _component_count(node_ids: set[str], adjacency: dict[str, set[str]]) -> int:
    unseen = set(node_ids)
    components = 0
    while unseen:
        components += 1
        start = unseen.pop()
        queue: deque[str] = deque([start])
        while queue:
            node_id = queue.popleft()
            for neighbor in adjacency.get(node_id, set()):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
    return components


def _write_sqlite_graph(
    path: Path,
    *,
    source_set_id: str,
    nodes: list[dict],
    edges: list[dict],
    metrics: dict,
) -> None:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL
            );

            CREATE TABLE graph_nodes (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE graph_edges (
              id TEXT PRIMARY KEY,
              source TEXT NOT NULL,
              target TEXT NOT NULL,
              relationship TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE INDEX idx_graph_nodes_type ON graph_nodes(type);
            CREATE INDEX idx_graph_edges_source ON graph_edges(source);
            CREATE INDEX idx_graph_edges_target ON graph_edges(target);
            CREATE INDEX idx_graph_edges_relationship ON graph_edges(relationship);
            """
        )
        metadata = {
            "schema_version": GRAPH_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "created_at": _utc_now(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "metrics": metrics,
        }
        for key, value in metadata.items():
            connection.execute(
                "INSERT INTO metadata VALUES (?, ?)",
                (key, json.dumps(value, sort_keys=True)),
            )
        for node in nodes:
            connection.execute(
                "INSERT INTO graph_nodes VALUES (?, ?, ?)",
                (node["id"], node["type"], json.dumps(node, sort_keys=True)),
            )
        for edge in edges:
            connection.execute(
                "INSERT INTO graph_edges VALUES (?, ?, ?, ?, ?)",
                (
                    edge["id"],
                    edge["source"],
                    edge["target"],
                    edge["relationship"],
                    json.dumps(edge, sort_keys=True),
                ),
            )
        connection.commit()


def _sqlite_graph_checks(
    path: Path,
    *,
    expected_node_count: int,
    expected_edge_count: int,
) -> list[dict]:
    from .evidence_graph_validation import _sqlite_graph_checks as _checks

    return _checks(
        path,
        expected_node_count=expected_node_count,
        expected_edge_count=expected_edge_count,
    )



def _node(node_id: str, node_type: str, **properties: object) -> dict:
    return {"id": node_id, "type": node_type, **properties}


def _edge(source: str, target: str, relationship: str, **properties: object) -> dict:
    return {
        "id": _edge_id(source, target, relationship),
        "source": source,
        "target": target,
        "relationship": relationship,
        **properties,
    }


def _put_edge(edges_by_id: dict[str, dict], source: str, target: str, relationship: str) -> None:
    edge = _edge(source, target, relationship)
    edges_by_id[edge["id"]] = edge


def _edge_id(source: str, target: str, relationship: str) -> str:
    material = f"{source}|{relationship}|{target}"
    return f"edge:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _extracted_text_node_id(chunk: dict) -> str:
    material = "|".join(
        [
            str(chunk["source_record_id"]),
            str(chunk["artifact_sha256"]),
            str(chunk.get("source_text_path") or ""),
        ]
    )
    return f"extracted_text:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _section_node_id(chunk: dict) -> str:
    material = "|".join(
        [
            str(chunk["source_record_id"]),
            str(chunk.get("section") or ""),
            str(chunk.get("heading") or ""),
            str(chunk.get("page") or ""),
        ]
    )
    return f"section:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _section_label(chunk: dict) -> str:
    return (
        str(chunk.get("heading") or "")
        or str(chunk.get("section") or "")
        or (f"page {chunk['page']}" if chunk.get("page") is not None else "")
        or "unsectioned extracted text"
    )


def _evidence_span_node_id(chunk: dict) -> str:
    material = "|".join(
        [
            str(chunk["chunk_id"]),
            str(chunk["content_sha256"]),
            str(chunk["char_start"]),
            str(chunk["char_end"]),
        ]
    )
    return f"evidence_span:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _parser_node_id(chunk: dict) -> str:
    material = f"{chunk['parser_name']}|{chunk['parser_version']}"
    return f"parser:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _topic_node_id(topic: str) -> str:
    return f"review_topic:{_slug(topic)}"


def _slug(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        slug = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return slug[:max_length]


def _preview(text: str, *, max_chars: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_retrieval: bool,
) -> dict:
    from .evidence_graph_validation import _with_additional_checks as _merge

    return _merge(
        validation,
        checks,
        allow_partial_retrieval=allow_partial_retrieval,
    )


def _check_detail_count(validation: dict, check_name: str, detail_key: str) -> int:
    from .evidence_graph_validation import _check_detail_count as _count

    return _count(validation, check_name, detail_key)


def _retrieval_index_path(source_derived_dir: Path, retrieval_summary: dict | None) -> Path:
    from .evidence_graph_validation import _retrieval_index_path as _path

    return _path(source_derived_dir, retrieval_summary)


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
