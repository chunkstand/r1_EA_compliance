from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import Any

from .chunk_layers import build_chunk_layers
from .retrieval_common import DEFAULT_INDEX_FILENAME
from .retrieval_common import _ensure_noncanonical_sidecar_dir
from .retrieval_common import _read_json
from .retrieval_common import _source_set_id_from_catalog
from .retrieval_common import _write_json
from .retrieval_eval_runtime import run_retrieval_eval
from .retrieval_runtime import build_retrieval_index
from .source_set_support import source_derived_dir


CHUNK_SIDECAR_RETRIEVAL_EVAL_SCHEMA_VERSION = "chunk-sidecar-retrieval-eval-results-v1"
DEFAULT_CHUNK_SIDECAR_RETRIEVAL_EVAL_PATH = Path(
    "config/chunk_sidecar_retrieval_eval_v1.json"
)
TRACKED_COMPARISON_METRICS = (
    "pass_rate",
    "recall_at_k",
    "atomic_chunk_recall_at_k",
    "structure_hit_rate",
    "parent_window_coverage_rate",
    "citation_correctness_rate",
    "mrr",
    "ndcg_at_k",
)


@dataclass(frozen=True)
class ChunkSidecarRetrievalEvalResult:
    source_set_id: str
    output_path: Path
    summary: dict[str, Any]


def run_chunk_sidecar_retrieval_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    eval_file: Path = DEFAULT_CHUNK_SIDECAR_RETRIEVAL_EVAL_PATH,
    chunks_v2_dir: Path | None = None,
    sidecar_index_dir: Path | None = None,
    baseline_index_path: Path | None = None,
    results_dir: Path | None = None,
    top_k: int = 5,
    rebuild_sidecar: bool = False,
) -> ChunkSidecarRetrievalEvalResult:
    """Build/evaluate an opt-in sidecar retrieval index against baseline retrieval."""

    output_dir = Path(output_dir)
    source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    eval_file = Path(eval_file)
    derived_dir = source_derived_dir(output_dir / "derived", source_set_id)
    chunks_v2_dir = Path(chunks_v2_dir) if chunks_v2_dir is not None else derived_dir / "chunks_v2"
    sidecar_index_dir = (
        Path(sidecar_index_dir)
        if sidecar_index_dir is not None
        else derived_dir / "retrieval_sidecar"
    )
    baseline_index_path = (
        Path(baseline_index_path)
        if baseline_index_path is not None
        else derived_dir / "retrieval" / DEFAULT_INDEX_FILENAME
    )
    results_dir = (
        Path(results_dir)
        if results_dir is not None
        else derived_dir / "retrieval_sidecar_eval"
    )
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
    for canonical_name in ("chunks", "retrieval"):
        _ensure_noncanonical_sidecar_dir(
            requested_dir=results_dir,
            canonical_dir=derived_dir / canonical_name,
            label="results_dir",
        )
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "chunk_sidecar_retrieval_eval_results.json"

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
    )
    sidecar_eval = run_retrieval_eval(
        index_path=sidecar_index.sqlite_path,
        eval_file=eval_file,
        top_k=top_k,
        output_dir=results_dir / "sidecar",
    )
    baseline_eval_summary, baseline_error = _run_optional_baseline_eval(
        baseline_index_path=baseline_index_path,
        eval_file=eval_file,
        top_k=top_k,
        output_dir=results_dir / "baseline",
    )
    comparisons = _metric_comparisons(
        baseline_metrics=(baseline_eval_summary or {}).get("metrics", {}),
        sidecar_metrics=sidecar_eval.summary.get("metrics", {}),
    )
    checks = _checks(
        sidecar_summary=sidecar_summary,
        sidecar_index_summary=sidecar_index.summary,
        sidecar_eval_summary=sidecar_eval.summary,
        baseline_eval_summary=baseline_eval_summary,
        baseline_error=baseline_error,
        comparisons=comparisons,
    )
    summary = {
        "schema_version": CHUNK_SIDECAR_RETRIEVAL_EVAL_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "output_path": str(output_path),
        "eval_file": str(eval_file),
        "eval_file_sha256": _sha256_file(eval_file) if eval_file.exists() else None,
        "top_k": top_k,
        "chunks_v2_dir": str(chunks_v2_dir),
        "atomic_chunks_path": str(atomic_chunks_path),
        "sidecar_summary_path": str(chunks_v2_dir / "summary.json"),
        "sidecar_index_path": str(sidecar_index.sqlite_path),
        "sidecar_index_summary_path": str(sidecar_index.summary_path),
        "sidecar_eval_path": str(sidecar_eval.output_path),
        "baseline_index_path": str(baseline_index_path),
        "baseline_eval_path": (
            str(results_dir / "baseline" / "retrieval_eval_results.json")
            if baseline_eval_summary is not None
            else None
        ),
        "baseline_error": baseline_error,
        "sidecar": {
            "chunk_count": sidecar_index.summary.get("chunk_count"),
            "source_count": sidecar_index.summary.get("source_count"),
            "validation_passed": sidecar_index.summary.get("validation_passed"),
            "reviewer_ready": sidecar_index.summary.get("reviewer_ready"),
            "eval_passed": sidecar_eval.summary.get("passed"),
            "metrics": sidecar_eval.summary.get("metrics", {}),
            "atomic_chunk_case_count": sidecar_eval.summary.get("atomic_chunk_case_count"),
            "structural_case_count": sidecar_eval.summary.get("structural_case_count"),
            "parent_window_case_count": sidecar_eval.summary.get("parent_window_case_count"),
        },
        "baseline": _baseline_summary_payload(baseline_eval_summary),
        "metric_comparisons": comparisons,
        "checks": checks,
    }
    summary["passed"] = all(check["passed"] for check in checks)
    _write_json(output_path, summary)
    return ChunkSidecarRetrievalEvalResult(
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


def _run_optional_baseline_eval(
    *,
    baseline_index_path: Path,
    eval_file: Path,
    top_k: int,
    output_dir: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    if not baseline_index_path.exists():
        return None, "baseline_index_missing"
    try:
        result = run_retrieval_eval(
            index_path=baseline_index_path,
            eval_file=eval_file,
            top_k=top_k,
            output_dir=output_dir,
        )
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return result.summary, None


def _baseline_summary_payload(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        "eval_passed": summary.get("passed"),
        "metrics": summary.get("metrics", {}),
        "failed_count": summary.get("failed_count"),
        "atomic_chunk_case_count": summary.get("atomic_chunk_case_count"),
        "structural_case_count": summary.get("structural_case_count"),
        "parent_window_case_count": summary.get("parent_window_case_count"),
    }


def _metric_comparisons(
    *,
    baseline_metrics: dict[str, Any],
    sidecar_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    comparisons = []
    for metric in TRACKED_COMPARISON_METRICS:
        baseline_value = _float_metric(baseline_metrics.get(metric))
        sidecar_value = _float_metric(sidecar_metrics.get(metric))
        if baseline_value is None or sidecar_value is None:
            continue
        comparisons.append(
            {
                "metric": metric,
                "baseline": baseline_value,
                "sidecar": sidecar_value,
                "delta": round(sidecar_value - baseline_value, 6),
                "sidecar_not_worse": sidecar_value >= baseline_value,
            }
        )
    return comparisons


def _checks(
    *,
    sidecar_summary: dict[str, Any],
    sidecar_index_summary: dict[str, Any],
    sidecar_eval_summary: dict[str, Any],
    baseline_eval_summary: dict[str, Any] | None,
    baseline_error: str | None,
    comparisons: list[dict[str, Any]],
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
                "sqlite_path": sidecar_index_summary.get("sqlite_path"),
            },
        },
        {
            "name": "sidecar_retrieval_eval_passed",
            "passed": bool(sidecar_eval_summary.get("passed")),
            "details": {
                "query_count": sidecar_eval_summary.get("query_count"),
                "failed_count": sidecar_eval_summary.get("failed_count"),
            },
        },
        {
            "name": "sidecar_eval_has_atomic_structural_parent_cases",
            "passed": bool(
                int(sidecar_eval_summary.get("atomic_chunk_case_count") or 0) > 0
                and int(sidecar_eval_summary.get("structural_case_count") or 0) > 0
                and int(sidecar_eval_summary.get("parent_window_case_count") or 0) > 0
            ),
            "details": {
                "atomic_chunk_case_count": sidecar_eval_summary.get("atomic_chunk_case_count"),
                "structural_case_count": sidecar_eval_summary.get("structural_case_count"),
                "parent_window_case_count": sidecar_eval_summary.get("parent_window_case_count"),
            },
        },
        {
            "name": "baseline_eval_completed",
            "passed": baseline_eval_summary is not None,
            "details": {"baseline_error": baseline_error},
        },
        {
            "name": "sidecar_metrics_not_worse_than_baseline",
            "passed": bool(comparisons) and all(
                comparison["sidecar_not_worse"] for comparison in comparisons
            ),
            "details": {"comparisons": comparisons},
        },
    ]


def _float_metric(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
