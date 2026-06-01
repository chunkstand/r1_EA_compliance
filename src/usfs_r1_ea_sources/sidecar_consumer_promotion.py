from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any

from .claim_extraction import build_claim_extraction
from .evidence_graph import build_evidence_graph
from .retrieval_common import _ensure_noncanonical_sidecar_dir
from .retrieval_common import _read_json
from .retrieval_common import _source_set_id_from_catalog
from .retrieval_common import _utc_now
from .retrieval_common import _write_json
from .source_set_support import source_derived_dir


CHUNK_SIDECAR_CONSUMER_PROMOTION_SCHEMA_VERSION = (
    "chunk-sidecar-consumer-promotion-results-v1"
)
CHUNK_SIDECAR_CONSUMER_EVAL_SCHEMA_VERSION = "chunk-sidecar-consumer-eval-results-v1"
CANONICAL_CONSUMER_DIRS = ("chunks", "retrieval", "evidence_graph", "claims")


@dataclass(frozen=True)
class ChunkSidecarConsumerPromotionResult:
    source_set_id: str
    output_path: Path
    summary: dict[str, Any]


def run_chunk_sidecar_consumer_promotion(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    consumer_eval_results_path: Path | None = None,
    results_dir: Path | None = None,
    apply: bool = False,
    replace_canonical: bool = False,
) -> ChunkSidecarConsumerPromotionResult:
    """Promote sidecar graph/claim consumers into canonical dirs when fully gated."""

    output_dir = Path(output_dir)
    source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    derived_dir = source_derived_dir(output_dir / "derived", source_set_id)
    consumer_eval_results_path = (
        Path(consumer_eval_results_path)
        if consumer_eval_results_path is not None
        else derived_dir
        / "consumer_sidecar_eval"
        / "chunk_sidecar_consumer_eval_results.json"
    )
    results_dir = (
        Path(results_dir)
        if results_dir is not None
        else derived_dir / "consumer_sidecar_promotion"
    )
    for canonical_name in CANONICAL_CONSUMER_DIRS:
        _ensure_noncanonical_sidecar_dir(
            requested_dir=results_dir,
            canonical_dir=derived_dir / canonical_name,
            label="results_dir",
        )
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "chunk_sidecar_consumer_promotion_results.json"

    consumer_eval = _read_json(consumer_eval_results_path)
    sidecar_paths = _sidecar_paths(consumer_eval)
    _ensure_sidecar_input_dirs(derived_dir=derived_dir, sidecar_paths=sidecar_paths)
    canonical_graph_dir = derived_dir / "evidence_graph"
    canonical_claims_dir = derived_dir / "claims"
    sidecar_graph_summary = _read_optional_json(sidecar_paths["graph_summary"])
    sidecar_claim_summary = _read_optional_json(sidecar_paths["claims_summary"])
    checks = _preflight_checks(
        source_set_id=source_set_id,
        consumer_eval=consumer_eval,
        consumer_eval_results_path=consumer_eval_results_path,
        sidecar_paths=sidecar_paths,
        sidecar_graph_summary=sidecar_graph_summary,
        sidecar_claim_summary=sidecar_claim_summary,
        canonical_graph_dir=canonical_graph_dir,
        canonical_claims_dir=canonical_claims_dir,
        apply=apply,
        replace_canonical=replace_canonical,
    )
    promotion_ready = all(check["passed"] for check in checks)
    applied = False
    backup_dir = None
    canonical = None
    if apply and promotion_ready:
        apply_result = _apply_promotion(
            output_dir=output_dir,
            source_set_id=source_set_id,
            derived_dir=derived_dir,
            sidecar_paths=sidecar_paths,
            canonical_graph_dir=canonical_graph_dir,
            canonical_claims_dir=canonical_claims_dir,
            results_dir=results_dir,
        )
        checks.extend(apply_result["checks"])
        applied = apply_result["applied"]
        backup_dir = apply_result.get("backup_dir")
        canonical = apply_result.get("canonical")
        promotion_ready = all(check["passed"] for check in checks)

    summary = {
        "schema_version": CHUNK_SIDECAR_CONSUMER_PROMOTION_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "output_path": str(output_path),
        "consumer_eval_results_path": str(consumer_eval_results_path),
        "results_dir": str(results_dir),
        "apply": apply,
        "replace_canonical": replace_canonical,
        "promotion_ready": promotion_ready,
        "applied": applied,
        "canonical_graph_dir": str(canonical_graph_dir),
        "canonical_claims_dir": str(canonical_claims_dir),
        "sidecar": {
            "atomic_chunks_path": str(sidecar_paths["atomic_chunks"]),
            "retrieval_summary_path": str(sidecar_paths["retrieval_summary"]),
            "retrieval_validation_path": str(sidecar_paths["retrieval_validation"]),
            "graph_dir": str(sidecar_paths["graph_dir"]),
            "graph_summary_path": str(sidecar_paths["graph_summary"]),
            "claims_dir": str(sidecar_paths["claims_dir"]),
            "claims_summary_path": str(sidecar_paths["claims_summary"]),
        },
        "canonical": canonical,
        "backup_dir": backup_dir,
        "checks": checks,
    }
    summary["passed"] = promotion_ready and (not apply or applied)
    _write_json(output_path, summary)
    return ChunkSidecarConsumerPromotionResult(
        source_set_id=source_set_id,
        output_path=output_path,
        summary=summary,
    )


def _sidecar_paths(consumer_eval: dict[str, Any]) -> dict[str, Path]:
    sidecar_index_dir = Path(str(consumer_eval.get("sidecar_index_dir") or ""))
    return {
        "atomic_chunks": Path(str(consumer_eval.get("atomic_chunks_path") or "")),
        "retrieval_summary": Path(str(consumer_eval.get("sidecar_index_summary_path") or "")),
        "retrieval_validation": sidecar_index_dir / "retrieval_validation.json",
        "graph_dir": Path(str(consumer_eval.get("sidecar_graph_dir") or "")),
        "graph_summary": Path(str(consumer_eval.get("sidecar_graph_summary_path") or "")),
        "claims_dir": Path(str(consumer_eval.get("sidecar_claims_dir") or "")),
        "claims_summary": Path(str(consumer_eval.get("sidecar_claims_summary_path") or "")),
    }


def _ensure_sidecar_input_dirs(
    *,
    derived_dir: Path,
    sidecar_paths: dict[str, Path],
) -> None:
    for label, requested_dir in (
        ("chunks_v2_dir", sidecar_paths["atomic_chunks"].parent),
        ("sidecar_index_dir", sidecar_paths["retrieval_summary"].parent),
        ("sidecar_graph_dir", sidecar_paths["graph_dir"]),
        ("sidecar_claims_dir", sidecar_paths["claims_dir"]),
    ):
        for canonical_name in CANONICAL_CONSUMER_DIRS:
            _ensure_noncanonical_sidecar_dir(
                requested_dir=requested_dir,
                canonical_dir=derived_dir / canonical_name,
                label=label,
            )


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _preflight_checks(
    *,
    source_set_id: str,
    consumer_eval: dict[str, Any],
    consumer_eval_results_path: Path,
    sidecar_paths: dict[str, Path],
    sidecar_graph_summary: dict[str, Any] | None,
    sidecar_claim_summary: dict[str, Any] | None,
    canonical_graph_dir: Path,
    canonical_claims_dir: Path,
    apply: bool,
    replace_canonical: bool,
) -> list[dict[str, Any]]:
    sidecar = consumer_eval.get("sidecar") or {}
    sidecar_retrieval = sidecar.get("retrieval") or {}
    sidecar_graph = sidecar.get("graph") or {}
    sidecar_claims = sidecar.get("claims") or {}
    return [
        {
            "name": "consumer_eval_results_present",
            "passed": consumer_eval_results_path.exists(),
            "details": {"path": str(consumer_eval_results_path)},
        },
        {
            "name": "consumer_eval_schema_supported",
            "passed": consumer_eval.get("schema_version")
            == CHUNK_SIDECAR_CONSUMER_EVAL_SCHEMA_VERSION,
            "details": {"schema_version": consumer_eval.get("schema_version")},
        },
        {
            "name": "consumer_eval_source_set_matches",
            "passed": consumer_eval.get("source_set_id") == source_set_id,
            "details": {
                "expected_source_set_id": source_set_id,
                "actual_source_set_id": consumer_eval.get("source_set_id"),
            },
        },
        {
            "name": "consumer_eval_passed",
            "passed": bool(consumer_eval.get("passed")),
            "details": {"failed_checks": _failed_check_names(consumer_eval)},
        },
        {
            "name": "consumer_eval_non_partial",
            "passed": not bool(consumer_eval.get("allow_partial_extraction"))
            and not bool(consumer_eval.get("allow_partial_retrieval")),
            "details": {
                "allow_partial_extraction": bool(
                    consumer_eval.get("allow_partial_extraction")
                ),
                "allow_partial_retrieval": bool(consumer_eval.get("allow_partial_retrieval")),
            },
        },
        {
            "name": "sidecar_retrieval_reviewer_ready",
            "passed": bool(sidecar_retrieval.get("reviewer_ready")),
            "details": {
                "validation_passed": sidecar_retrieval.get("validation_passed"),
                "reviewer_ready": sidecar_retrieval.get("reviewer_ready"),
            },
        },
        {
            "name": "sidecar_graph_reviewer_ready",
            "passed": bool(sidecar_graph.get("reviewer_ready")),
            "details": {
                "validation_passed": sidecar_graph.get("validation_passed"),
                "reviewer_ready": sidecar_graph.get("reviewer_ready"),
            },
        },
        {
            "name": "sidecar_claims_reviewer_ready",
            "passed": bool(sidecar_claims.get("reviewer_ready")),
            "details": {
                "validation_passed": sidecar_claims.get("validation_passed"),
                "reviewer_ready": sidecar_claims.get("reviewer_ready"),
            },
        },
        _sidecar_summary_check(
            name="sidecar_graph_summary_valid",
            summary=sidecar_graph_summary,
            expected_source_set_id=source_set_id,
        ),
        _sidecar_summary_check(
            name="sidecar_claim_summary_valid",
            summary=sidecar_claim_summary,
            expected_source_set_id=source_set_id,
        ),
        {
            "name": "sidecar_input_paths_exist",
            "passed": all(path.exists() for path in sidecar_paths.values()),
            "details": {
                label: {"path": str(path), "exists": path.exists()}
                for label, path in sidecar_paths.items()
            },
        },
        {
            "name": "canonical_targets_are_replaceable",
            "passed": _canonical_targets_replaceable(
                canonical_graph_dir=canonical_graph_dir,
                canonical_claims_dir=canonical_claims_dir,
                apply=apply,
                replace_canonical=replace_canonical,
            ),
            "details": {
                "apply": apply,
                "replace_canonical": replace_canonical,
                "canonical_graph_dir_exists": canonical_graph_dir.exists(),
                "canonical_claims_dir_exists": canonical_claims_dir.exists(),
            },
        },
    ]


def _sidecar_summary_check(
    *,
    name: str,
    summary: dict[str, Any] | None,
    expected_source_set_id: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(
            summary
            and summary.get("source_set_id") == expected_source_set_id
            and summary.get("validation_passed")
            and summary.get("reviewer_ready")
        ),
        "details": {
            "present": summary is not None,
            "source_set_id": (summary or {}).get("source_set_id"),
            "validation_passed": (summary or {}).get("validation_passed"),
            "reviewer_ready": (summary or {}).get("reviewer_ready"),
        },
    }


def _canonical_targets_replaceable(
    *,
    canonical_graph_dir: Path,
    canonical_claims_dir: Path,
    apply: bool,
    replace_canonical: bool,
) -> bool:
    if not apply:
        return True
    if not canonical_graph_dir.exists() and not canonical_claims_dir.exists():
        return True
    return replace_canonical


def _apply_promotion(
    *,
    output_dir: Path,
    source_set_id: str,
    derived_dir: Path,
    sidecar_paths: dict[str, Path],
    canonical_graph_dir: Path,
    canonical_claims_dir: Path,
    results_dir: Path,
) -> dict[str, Any]:
    backup_dir = results_dir / "backups" / _utc_now().replace(":", "").replace("-", "")
    moved_backups = _backup_existing_dirs(
        backup_dir=backup_dir,
        graph_dir=canonical_graph_dir,
        claims_dir=canonical_claims_dir,
    )
    try:
        graph_result = build_evidence_graph(
            output_dir=output_dir,
            source_set_id=source_set_id,
            chunks_path=sidecar_paths["atomic_chunks"],
            retrieval_validation_path=sidecar_paths["retrieval_validation"],
            retrieval_summary_path=sidecar_paths["retrieval_summary"],
            graph_dir=canonical_graph_dir,
        )
        claims_result = build_claim_extraction(
            output_dir=output_dir,
            source_set_id=source_set_id,
            chunks_path=sidecar_paths["atomic_chunks"],
            retrieval_validation_path=sidecar_paths["retrieval_validation"],
            retrieval_summary_path=sidecar_paths["retrieval_summary"],
            claims_dir=canonical_claims_dir,
        )
        checks = _apply_checks(
            graph_summary=graph_result.summary,
            claim_summary=claims_result.summary,
            sidecar_paths=sidecar_paths,
        )
        if not all(check["passed"] for check in checks):
            _restore_backups(moved_backups)
            return {
                "applied": False,
                "backup_dir": str(backup_dir),
                "checks": checks,
                "canonical": None,
            }
        return {
            "applied": True,
            "backup_dir": str(backup_dir) if moved_backups else None,
            "checks": checks,
            "canonical": {
                "graph_summary_path": str(graph_result.summary_path),
                "claims_summary_path": str(claims_result.summary_path),
                "graph": _consumer_payload(graph_result.summary),
                "claims": _consumer_payload(claims_result.summary),
            },
        }
    except Exception:
        _restore_backups(moved_backups)
        raise


def _backup_existing_dirs(
    *,
    backup_dir: Path,
    graph_dir: Path,
    claims_dir: Path,
) -> dict[Path, Path]:
    moved = {}
    for path in (graph_dir, claims_dir):
        if not path.exists():
            continue
        backup_path = backup_dir / path.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.move(str(path), str(backup_path))
        moved[path] = backup_path
    return moved


def _restore_backups(moved_backups: dict[Path, Path]) -> None:
    for original_path, backup_path in moved_backups.items():
        if original_path.exists():
            shutil.rmtree(original_path)
        if backup_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(backup_path), str(original_path))


def _apply_checks(
    *,
    graph_summary: dict[str, Any],
    claim_summary: dict[str, Any],
    sidecar_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    return [
        {
            "name": "canonical_graph_reviewer_ready",
            "passed": bool(
                graph_summary.get("validation_passed") and graph_summary.get("reviewer_ready")
            ),
            "details": _consumer_payload(graph_summary),
        },
        {
            "name": "canonical_claims_reviewer_ready",
            "passed": bool(
                claim_summary.get("validation_passed") and claim_summary.get("reviewer_ready")
            ),
            "details": _consumer_payload(claim_summary),
        },
        {
            "name": "canonical_graph_uses_sidecar_inputs",
            "passed": _same_path(graph_summary.get("chunks_path"), sidecar_paths["atomic_chunks"])
            and _same_path(
                graph_summary.get("retrieval_summary_path"),
                sidecar_paths["retrieval_summary"],
            ),
            "details": {
                "chunks_path": graph_summary.get("chunks_path"),
                "retrieval_summary_path": graph_summary.get("retrieval_summary_path"),
            },
        },
        {
            "name": "canonical_claims_use_sidecar_inputs",
            "passed": _same_path(claim_summary.get("chunks_path"), sidecar_paths["atomic_chunks"])
            and _same_path(
                claim_summary.get("retrieval_summary_path"),
                sidecar_paths["retrieval_summary"],
            ),
            "details": {
                "chunks_path": claim_summary.get("chunks_path"),
                "retrieval_summary_path": claim_summary.get("retrieval_summary_path"),
            },
        },
    ]


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


def _failed_check_names(summary: dict[str, Any]) -> list[str]:
    return [
        str(check.get("name"))
        for check in summary.get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]


def _same_path(value: object, expected_path: Path) -> bool:
    if value is None:
        return False
    return Path(str(value)).resolve() == expected_path.resolve()
