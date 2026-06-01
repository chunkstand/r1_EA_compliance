from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .chunk_layers import build_chunk_layers
from .claim_extraction import build_claim_extraction
from .evidence_graph import build_evidence_graph
from .retrieval_common import _ensure_noncanonical_sidecar_dir
from .retrieval_common import _read_json
from .retrieval_common import _source_set_id_from_catalog
from .retrieval_common import _write_json
from .retrieval_runtime import build_retrieval_index
from .source_set_support import source_derived_dir


CHUNK_SIDECAR_CONSUMER_EVAL_SCHEMA_VERSION = "chunk-sidecar-consumer-eval-results-v1"
GRAPH_RATE_METRICS = (
    "source_artifact_coverage_rate",
    "evidence_coverage_rate",
    "chunk_topic_coverage_rate",
)
CLAIM_RATE_METRICS = (
    "claim_evidence_coverage_rate",
    "claim_topic_coverage_rate",
    "claim_authority_coverage_rate",
    "claim_entity_coverage_rate",
)


@dataclass(frozen=True)
class ChunkSidecarConsumerEvalResult:
    source_set_id: str
    output_path: Path
    summary: dict[str, Any]


def run_chunk_sidecar_consumer_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    chunks_v2_dir: Path | None = None,
    sidecar_index_dir: Path | None = None,
    graph_dir: Path | None = None,
    claims_dir: Path | None = None,
    baseline_graph_summary_path: Path | None = None,
    baseline_claim_summary_path: Path | None = None,
    results_dir: Path | None = None,
    rebuild_sidecar: bool = False,
    allow_partial_extraction: bool = False,
    allow_partial_retrieval: bool = False,
) -> ChunkSidecarConsumerEvalResult:
    """Build and score sidecar graph/claim previews against canonical summaries."""

    output_dir = Path(output_dir)
    source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    derived_dir = source_derived_dir(output_dir / "derived", source_set_id)
    chunks_v2_dir = Path(chunks_v2_dir) if chunks_v2_dir is not None else derived_dir / "chunks_v2"
    sidecar_index_dir = (
        Path(sidecar_index_dir)
        if sidecar_index_dir is not None
        else derived_dir / "retrieval_sidecar"
    )
    results_dir = (
        Path(results_dir)
        if results_dir is not None
        else derived_dir / "consumer_sidecar_eval"
    )
    graph_dir = Path(graph_dir) if graph_dir is not None else results_dir / "evidence_graph_sidecar"
    claims_dir = Path(claims_dir) if claims_dir is not None else results_dir / "claims_sidecar"
    baseline_graph_summary_path = (
        Path(baseline_graph_summary_path)
        if baseline_graph_summary_path is not None
        else derived_dir / "evidence_graph" / "summary.json"
    )
    baseline_claim_summary_path = (
        Path(baseline_claim_summary_path)
        if baseline_claim_summary_path is not None
        else derived_dir / "claims" / "summary.json"
    )
    _ensure_consumer_eval_sidecar_paths(
        derived_dir=derived_dir,
        chunks_v2_dir=chunks_v2_dir,
        sidecar_index_dir=sidecar_index_dir,
        results_dir=results_dir,
        graph_dir=graph_dir,
        claims_dir=claims_dir,
    )
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "chunk_sidecar_consumer_eval_results.json"

    sidecar_summary = _ensure_sidecar_chunks(
        output_dir=output_dir,
        source_set_id=source_set_id,
        chunks_v2_dir=chunks_v2_dir,
        rebuild_sidecar=rebuild_sidecar,
    )
    atomic_chunks_path = chunks_v2_dir / "atomic_chunks.jsonl"
    sidecar_index = build_retrieval_index(
        output_dir=output_dir,
        source_set_id=source_set_id,
        chunks_path=atomic_chunks_path,
        index_dir=sidecar_index_dir,
        allow_partial_extraction=allow_partial_extraction,
    )
    sidecar_graph = build_evidence_graph(
        output_dir=output_dir,
        source_set_id=source_set_id,
        chunks_path=atomic_chunks_path,
        retrieval_validation_path=sidecar_index.validation_path,
        retrieval_summary_path=sidecar_index.summary_path,
        graph_dir=graph_dir,
        allow_partial_retrieval=allow_partial_retrieval,
    )
    sidecar_claims = build_claim_extraction(
        output_dir=output_dir,
        source_set_id=source_set_id,
        chunks_path=atomic_chunks_path,
        retrieval_validation_path=sidecar_index.validation_path,
        retrieval_summary_path=sidecar_index.summary_path,
        claims_dir=claims_dir,
        allow_partial_retrieval=allow_partial_retrieval,
    )
    baseline_graph_summary = _read_optional_json(baseline_graph_summary_path)
    baseline_claim_summary = _read_optional_json(baseline_claim_summary_path)
    graph_comparisons = _graph_metric_comparisons(
        baseline=(baseline_graph_summary or {}).get("metrics", {}),
        sidecar=sidecar_graph.summary.get("metrics", {}),
    )
    claim_comparisons = _claim_metric_comparisons(
        baseline=(baseline_claim_summary or {}).get("metrics", {}),
        sidecar=sidecar_claims.summary.get("metrics", {}),
    )
    checks = _checks(
        sidecar_summary=sidecar_summary,
        sidecar_index_summary=sidecar_index.summary,
        sidecar_graph_summary=sidecar_graph.summary,
        sidecar_claim_summary=sidecar_claims.summary,
        baseline_graph_summary=baseline_graph_summary,
        baseline_claim_summary=baseline_claim_summary,
        graph_comparisons=graph_comparisons,
        claim_comparisons=claim_comparisons,
    )
    summary = {
        "schema_version": CHUNK_SIDECAR_CONSUMER_EVAL_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "output_path": str(output_path),
        "chunks_v2_dir": str(chunks_v2_dir),
        "atomic_chunks_path": str(atomic_chunks_path),
        "sidecar_summary_path": str(chunks_v2_dir / "summary.json"),
        "sidecar_index_dir": str(sidecar_index_dir),
        "sidecar_index_path": str(sidecar_index.sqlite_path),
        "sidecar_index_summary_path": str(sidecar_index.summary_path),
        "sidecar_graph_dir": str(sidecar_graph.graph_dir),
        "sidecar_graph_summary_path": str(sidecar_graph.summary_path),
        "sidecar_claims_dir": str(sidecar_claims.claims_dir),
        "sidecar_claims_summary_path": str(sidecar_claims.summary_path),
        "baseline_graph_summary_path": str(baseline_graph_summary_path),
        "baseline_claim_summary_path": str(baseline_claim_summary_path),
        "baseline": {
            "graph": _baseline_payload(baseline_graph_summary),
            "claims": _baseline_payload(baseline_claim_summary),
        },
        "sidecar": {
            "chunks": {
                "atomic_chunk_count": sidecar_summary.get("atomic_chunk_count"),
                "structural_chunk_count": sidecar_summary.get("structural_chunk_count"),
                "parent_context_window_count": sidecar_summary.get(
                    "parent_context_window_count"
                ),
                "validation_passed": sidecar_summary.get("validation_passed"),
            },
            "retrieval": {
                "chunk_count": sidecar_index.summary.get("chunk_count"),
                "source_count": sidecar_index.summary.get("source_count"),
                "validation_passed": sidecar_index.summary.get("validation_passed"),
                "reviewer_ready": sidecar_index.summary.get("reviewer_ready"),
            },
            "graph": _consumer_payload(sidecar_graph.summary),
            "claims": _consumer_payload(sidecar_claims.summary),
        },
        "metric_comparisons": {
            "graph": graph_comparisons,
            "claims": claim_comparisons,
        },
        "allow_partial_extraction": allow_partial_extraction,
        "allow_partial_retrieval": allow_partial_retrieval,
        "checks": checks,
    }
    summary["passed"] = all(check["passed"] for check in checks)
    _write_json(output_path, summary)
    return ChunkSidecarConsumerEvalResult(
        source_set_id=source_set_id,
        output_path=output_path,
        summary=summary,
    )


def _ensure_sidecar_chunks(
    *,
    output_dir: Path,
    source_set_id: str,
    chunks_v2_dir: Path,
    rebuild_sidecar: bool,
) -> dict[str, Any]:
    summary_path = chunks_v2_dir / "summary.json"
    atomic_chunks_path = chunks_v2_dir / "atomic_chunks.jsonl"
    if rebuild_sidecar or not summary_path.exists() or not atomic_chunks_path.exists():
        return build_chunk_layers(
            output_dir=output_dir,
            source_set_id=source_set_id,
            chunks_v2_dir=chunks_v2_dir,
        ).summary
    return _read_json(summary_path)


def _ensure_consumer_eval_sidecar_paths(
    *,
    derived_dir: Path,
    chunks_v2_dir: Path,
    sidecar_index_dir: Path,
    results_dir: Path,
    graph_dir: Path,
    claims_dir: Path,
) -> None:
    _ensure_noncanonical_sidecar_dir(
        requested_dir=chunks_v2_dir,
        canonical_dir=derived_dir / "chunks",
        label="chunks_v2_dir",
    )
    _ensure_noncanonical_sidecar_dir(
        requested_dir=sidecar_index_dir,
        canonical_dir=derived_dir / "retrieval",
        label="sidecar_index_dir",
    )
    for label, requested_dir in (
        ("results_dir", results_dir),
        ("graph_dir", graph_dir),
        ("claims_dir", claims_dir),
    ):
        for canonical_name in ("chunks", "retrieval", "evidence_graph", "claims"):
            _ensure_noncanonical_sidecar_dir(
                requested_dir=requested_dir,
                canonical_dir=derived_dir / canonical_name,
                label=label,
            )


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _baseline_payload(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        "validation_passed": summary.get("validation_passed"),
        "reviewer_ready": summary.get("reviewer_ready"),
        "chunk_count": summary.get("chunk_count"),
        "claim_count": summary.get("claim_count"),
        "node_count": summary.get("node_count"),
        "edge_count": summary.get("edge_count"),
        "metrics": summary.get("metrics", {}),
    }


def _consumer_payload(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "validation_passed": summary.get("validation_passed"),
        "reviewer_ready": summary.get("reviewer_ready"),
        "chunk_count": summary.get("chunk_count"),
        "claim_count": summary.get("claim_count"),
        "node_count": summary.get("node_count"),
        "edge_count": summary.get("edge_count"),
        "metrics": summary.get("metrics", {}),
    }


def _graph_metric_comparisons(
    *,
    baseline: dict[str, Any],
    sidecar: dict[str, Any],
) -> list[dict[str, Any]]:
    comparisons = _higher_is_not_worse(baseline, sidecar, GRAPH_RATE_METRICS)
    comparisons.extend(
        _lower_is_not_worse(
            baseline,
            sidecar,
            ("dangling_edge_count", "isolated_node_count"),
        )
    )
    comparisons.extend(
        _higher_is_not_worse(
            baseline,
            sidecar,
            ("source_document_count", "raw_artifact_count"),
        )
    )
    return comparisons


def _claim_metric_comparisons(
    *,
    baseline: dict[str, Any],
    sidecar: dict[str, Any],
) -> list[dict[str, Any]]:
    comparisons = _higher_is_not_worse(baseline, sidecar, CLAIM_RATE_METRICS)
    comparisons.extend(_lower_is_not_worse(baseline, sidecar, ("dangling_edge_count",)))
    comparisons.extend(_higher_is_not_worse(baseline, sidecar, ("claim_count",)))
    return comparisons


def _higher_is_not_worse(
    baseline: dict[str, Any],
    sidecar: dict[str, Any],
    metrics: tuple[str, ...],
) -> list[dict[str, Any]]:
    comparisons = []
    for metric in metrics:
        baseline_value = _float_metric(baseline.get(metric))
        sidecar_value = _float_metric(sidecar.get(metric))
        if baseline_value is None or sidecar_value is None:
            continue
        comparisons.append(
            {
                "metric": metric,
                "baseline": baseline_value,
                "sidecar": sidecar_value,
                "delta": round(sidecar_value - baseline_value, 6),
                "sidecar_not_worse": sidecar_value >= baseline_value,
                "direction": "higher_is_better",
            }
        )
    return comparisons


def _lower_is_not_worse(
    baseline: dict[str, Any],
    sidecar: dict[str, Any],
    metrics: tuple[str, ...],
) -> list[dict[str, Any]]:
    comparisons = []
    for metric in metrics:
        baseline_value = _float_metric(baseline.get(metric))
        sidecar_value = _float_metric(sidecar.get(metric))
        if baseline_value is None or sidecar_value is None:
            continue
        comparisons.append(
            {
                "metric": metric,
                "baseline": baseline_value,
                "sidecar": sidecar_value,
                "delta": round(sidecar_value - baseline_value, 6),
                "sidecar_not_worse": sidecar_value <= baseline_value,
                "direction": "lower_is_better",
            }
        )
    return comparisons


def _checks(
    *,
    sidecar_summary: dict[str, Any],
    sidecar_index_summary: dict[str, Any],
    sidecar_graph_summary: dict[str, Any],
    sidecar_claim_summary: dict[str, Any],
    baseline_graph_summary: dict[str, Any] | None,
    baseline_claim_summary: dict[str, Any] | None,
    graph_comparisons: list[dict[str, Any]],
    claim_comparisons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "sidecar_chunks_validation_passed",
            "passed": bool(sidecar_summary.get("validation_passed")),
            "details": {
                "atomic_chunk_count": sidecar_summary.get("atomic_chunk_count"),
                "structural_chunk_count": sidecar_summary.get("structural_chunk_count"),
                "parent_context_window_count": sidecar_summary.get("parent_context_window_count"),
            },
        },
        {
            "name": "sidecar_retrieval_index_valid",
            "passed": bool(sidecar_index_summary.get("validation_passed")),
            "details": {
                "chunk_count": sidecar_index_summary.get("chunk_count"),
                "source_count": sidecar_index_summary.get("source_count"),
            },
        },
        {
            "name": "sidecar_graph_valid",
            "passed": bool(sidecar_graph_summary.get("validation_passed")),
            "details": _consumer_check_details(sidecar_graph_summary),
        },
        {
            "name": "sidecar_claims_valid",
            "passed": bool(sidecar_claim_summary.get("validation_passed")),
            "details": _consumer_check_details(sidecar_claim_summary),
        },
        {
            "name": "baseline_graph_summary_valid",
            "passed": bool(
                baseline_graph_summary and baseline_graph_summary.get("validation_passed")
            ),
            "details": {
                "validation_passed": (baseline_graph_summary or {}).get("validation_passed")
            },
        },
        {
            "name": "baseline_claim_summary_valid",
            "passed": bool(
                baseline_claim_summary and baseline_claim_summary.get("validation_passed")
            ),
            "details": {
                "validation_passed": (baseline_claim_summary or {}).get("validation_passed")
            },
        },
        {
            "name": "sidecar_graph_metrics_not_worse_than_baseline",
            "passed": bool(graph_comparisons)
            and all(comparison["sidecar_not_worse"] for comparison in graph_comparisons),
            "details": {"comparisons": graph_comparisons},
        },
        {
            "name": "sidecar_claim_metrics_not_worse_than_baseline",
            "passed": bool(claim_comparisons)
            and all(comparison["sidecar_not_worse"] for comparison in claim_comparisons),
            "details": {"comparisons": claim_comparisons},
        },
    ]


def _consumer_check_details(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_count": summary.get("chunk_count"),
        "claim_count": summary.get("claim_count"),
        "node_count": summary.get("node_count"),
        "edge_count": summary.get("edge_count"),
        "reviewer_ready": summary.get("reviewer_ready"),
    }


def _float_metric(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
