from __future__ import annotations

from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3

from .artifact_utils import _extraction_summary_is_complete
from .catalog_surface import resolve_catalog_dir_for_source_set
from .claim_extraction_graph import CLAIM_GRAPH_SCHEMA_VERSION
from .claim_extraction_graph import build_claim_graph_records as _claim_graph_records
from .claim_extraction_graph import build_entity_records as _entity_records
from .claim_extraction_graph import sqlite_graph_checks as _sqlite_graph_checks
from .claim_extraction_graph import write_sqlite_graph as _write_sqlite_graph
from .claim_extraction_runtime import CLAIM_EXTRACTOR_NAME
from .claim_extraction_runtime import CLAIM_EXTRACTOR_VERSION
from .claim_extraction_runtime import CLAIM_SCHEMA_VERSION
from .claim_extraction_runtime import SUPPORTED_CLAIM_TYPES as _SUPPORTED_CLAIM_TYPES
from .claim_extraction_runtime import _claim_metrics
from .claim_extraction_runtime import _extract_claims
from .claim_extraction_runtime import _rate as _runtime_rate
from .claim_extraction_runtime import _utc_now
from .source_set_support import source_derived_dir


CLAIM_EVAL_SCHEMA_VERSION = "claim-eval-v1"
CLAIM_EVAL_RESULTS_SCHEMA_VERSION = "claim-eval-results-v1"
DEFAULT_CLAIM_EVAL_PATH = Path("config/claim_eval_seed.json")
SUPPORTED_CLAIM_TYPES = _SUPPORTED_CLAIM_TYPES
SUPPORTED_CLAIM_EVAL_FILTERS = {
    "authority_level",
    "citation_label",
    "claim_type",
    "document_role",
    "review_topic",
    "source_record_id",
    "topic",
}


@dataclass(frozen=True)
class ClaimExtractionResult:
    source_set_id: str
    claims_dir: Path
    claims_path: Path
    entities_path: Path
    nodes_path: Path
    edges_path: Path
    sqlite_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class ClaimEvalResult:
    claims_path: Path
    eval_file: Path
    output_path: Path
    summary: dict


def build_claim_extraction(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    chunks_path: Path | None = None,
    catalog_sqlite_path: Path | None = None,
    allow_partial_retrieval: bool = False,
) -> ClaimExtractionResult:
    """Build deterministic source-text claim and entity artifacts from extracted chunks."""

    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    claims_dir = derived_source_dir / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = chunks_path or derived_source_dir / "chunks" / "chunks.jsonl"
    resolved_catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    catalog_sqlite_path = catalog_sqlite_path or resolved_catalog_dir / "review_sources.sqlite"
    extraction_validation_path = derived_source_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = derived_source_dir / "diagnostics" / "summary.json"
    retrieval_validation_path = derived_source_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = derived_source_dir / "retrieval" / "summary.json"
    claims_path = claims_dir / "claims.jsonl"
    entities_path = claims_dir / "entities.jsonl"
    nodes_path = claims_dir / "claim_graph_nodes.jsonl"
    edges_path = claims_dir / "claim_graph_edges.jsonl"
    sqlite_path = claims_dir / "claim_graph.sqlite"
    validation_path = claims_dir / "claim_validation.json"
    summary_path = claims_dir / "summary.json"

    raw_chunks = _read_jsonl(chunks_path) if chunks_path.exists() else []
    review_topics_by_source = _load_review_topics(catalog_sqlite_path)
    chunks = [
        _chunk_with_review_topics(
            chunk,
            review_topics_by_source.get(str(chunk.get("source_record_id")), []),
        )
        for chunk in raw_chunks
    ]
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

    claims = _extract_claims(chunks=chunks, source_set_id=source_set_id)
    entities = _entity_records(
        claims,
        extractor_name=CLAIM_EXTRACTOR_NAME,
        extractor_version=CLAIM_EXTRACTOR_VERSION,
    )
    nodes, edges = _claim_graph_records(
        source_set_id=source_set_id,
        claims=claims,
        entities=entities,
    )
    metrics = _claim_metrics(claims=claims, entities=entities, nodes=nodes, edges=edges)

    _write_jsonl(claims_path, claims)
    _write_jsonl(entities_path, entities)
    _write_jsonl(nodes_path, nodes)
    _write_jsonl(edges_path, edges)

    validation = validate_claim_outputs(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_path=claims_path,
        entities_path=entities_path,
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
        claims=claims,
        entities=entities,
        nodes=nodes,
        edges=edges,
        metrics=metrics,
        allow_partial_retrieval=allow_partial_retrieval,
    )
    if validation["passed"]:
        _write_sqlite_graph(
            sqlite_path,
            source_set_id=source_set_id,
            claims=claims,
            entities=entities,
            nodes=nodes,
            edges=edges,
            metrics=metrics,
        )
        validation = _with_additional_checks(
            validation,
            _sqlite_graph_checks(
                sqlite_path,
                expected_claim_count=len(claims),
                expected_entity_count=len(entities),
                expected_node_count=len(nodes),
                expected_edge_count=len(edges),
            ),
            allow_partial_retrieval=allow_partial_retrieval,
        )
        if not validation["passed"]:
            sqlite_path.unlink(missing_ok=True)
    else:
        sqlite_path.unlink(missing_ok=True)

    retrieval_reviewer_ready = bool(retrieval_summary and retrieval_summary.get("reviewer_ready"))
    reviewer_ready = (
        validation["passed"]
        and retrieval_reviewer_ready
        and _extraction_summary_is_complete(extraction_summary)
        and bool(claims)
    )
    summary = {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "graph_schema_version": CLAIM_GRAPH_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "claims_dir": str(claims_dir),
        "claims_path": str(claims_path),
        "entities_path": str(entities_path),
        "nodes_path": str(nodes_path),
        "edges_path": str(edges_path),
        "sqlite_path": str(sqlite_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "chunks_path": str(chunks_path),
        "catalog_sqlite_path": str(catalog_sqlite_path),
        "retrieval_summary_path": str(retrieval_summary_path),
        "retrieval_validation_path": str(retrieval_validation_path),
        "retrieval_index_path": str(retrieval_index_path),
        "allow_partial_retrieval": allow_partial_retrieval,
        "extractor_name": CLAIM_EXTRACTOR_NAME,
        "extractor_version": CLAIM_EXTRACTOR_VERSION,
        "validation_passed": validation["passed"],
        "reviewer_ready": reviewer_ready,
        "retrieval_reviewer_ready": retrieval_reviewer_ready,
        "extraction_complete": _extraction_summary_is_complete(extraction_summary),
        "chunk_count": len(chunks),
        "claim_count": len(claims),
        "entity_count": len(entities),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "claim_type_counts": dict(Counter(claim["claim_type"] for claim in claims)),
        "authority_level_counts": dict(Counter(claim["authority_level"] for claim in claims)),
        "document_role_counts": dict(Counter(claim["document_role"] for claim in claims)),
        "source_record_count": len({claim["source_record_id"] for claim in claims}),
        "retrieval_index_chunk_count": len(retrieval_index_records),
        "retrieval_binding_mismatch_count": _check_detail_count(
            validation,
            "claims_match_retrieval_index",
            "mismatch_count",
        ),
        "claim_offset_mismatch_count": _check_detail_count(
            validation,
            "claim_offsets_match_chunk_text",
            "mismatch_count",
        ),
        "metrics": metrics,
    }
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
    return ClaimExtractionResult(
        source_set_id=source_set_id,
        claims_dir=claims_dir,
        claims_path=claims_path,
        entities_path=entities_path,
        nodes_path=nodes_path,
        edges_path=edges_path,
        sqlite_path=sqlite_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
    )


def run_claim_eval(
    *,
    claims_path: Path,
    eval_file: Path,
    top_k: int = 5,
    output_dir: Path | None = None,
) -> ClaimEvalResult:
    from .claim_extraction_eval import run_claim_eval as _run_claim_eval

    return _run_claim_eval(
        claims_path=claims_path,
        eval_file=eval_file,
        top_k=top_k,
        output_dir=output_dir,
    )


def _load_validated_claims_for_eval(
    claims_path: Path,
    *,
    require_reviewer_ready: bool = True,
) -> list[dict]:
    from .claim_extraction_eval import _load_validated_claims_for_eval as _load

    return _load(
        claims_path,
        require_reviewer_ready=require_reviewer_ready,
    )


def default_claims_path(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    return source_derived_dir(output_dir / "derived", source_set_id) / "claims" / "claims.jsonl"


def validate_claim_outputs(
    *,
    output_dir: Path,
    source_set_id: str,
    claims_path: Path,
    entities_path: Path,
    nodes_path: Path,
    edges_path: Path,
    chunks_path: Path,
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
    claims: list[dict] | None = None,
    entities: list[dict] | None = None,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    metrics: dict | None = None,
    allow_partial_retrieval: bool = False,
) -> dict:
    from .claim_extraction_validation import validate_claim_outputs as _validate

    return _validate(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_path=claims_path,
        entities_path=entities_path,
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
        claims=claims,
        entities=entities,
        nodes=nodes,
        edges=edges,
        metrics=metrics,
        allow_partial_retrieval=allow_partial_retrieval,
    )


def _load_review_topics(catalog_sqlite_path: Path) -> dict[str, list[str]]:
    if not catalog_sqlite_path.exists():
        return {}
    query = """
        SELECT srt.source_record_id, rt.label
        FROM source_review_topics srt
        JOIN review_topics rt ON rt.topic_id = srt.topic_id
        ORDER BY srt.source_record_id, rt.label
    """
    topics: dict[str, list[str]] = {}
    try:
        with closing(sqlite3.connect(catalog_sqlite_path)) as connection:
            for source_record_id, label in connection.execute(query):
                topics.setdefault(str(source_record_id), []).append(str(label))
    except sqlite3.Error:
        return {}
    return topics


def _load_retrieval_index_records(index_path: Path) -> tuple[dict[str, dict], str | None]:
    from .claim_extraction_validation import _load_retrieval_index_records as _load

    return _load(index_path)


def _chunk_with_review_topics(chunk: dict, review_topics: list[str]) -> dict:
    merged = dict(chunk)
    if not merged.get("review_topics"):
        merged["review_topics"] = sorted(set(str(topic) for topic in review_topics if str(topic)))
    return merged


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_retrieval: bool,
) -> dict:
    from .claim_extraction_validation import _with_additional_checks as _merge

    return _merge(
        validation,
        checks,
        allow_partial_retrieval=allow_partial_retrieval,
    )


def _retrieval_index_path(source_derived_dir: Path, retrieval_summary: dict | None) -> Path:
    from .claim_extraction_validation import _retrieval_index_path as _path

    return _path(source_derived_dir, retrieval_summary)


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    source_set_id = manifest.get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _check_detail_count(validation: dict, check_name: str, detail_key: str) -> int:
    from .claim_extraction_validation import _check_detail_count as _count

    return _count(validation, check_name, detail_key)


def _rate(count: int, total: int) -> float:
    return _runtime_rate(count, total)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
