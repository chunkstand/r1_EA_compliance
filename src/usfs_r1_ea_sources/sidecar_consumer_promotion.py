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
SIDECAR_PATH_FIELDS = {
    "atomic_chunks": "atomic_chunks_path",
    "retrieval_summary": "sidecar_index_summary_path",
    "retrieval_validation": "sidecar_index_dir",
    "graph_dir": "sidecar_graph_dir",
    "graph_summary": "sidecar_graph_summary_path",
    "claims_dir": "sidecar_claims_dir",
    "claims_summary": "sidecar_claims_summary_path",
}
SIDECAR_PATH_KINDS = {
    "atomic_chunks": "file",
    "retrieval_summary": "file",
    "retrieval_validation": "file",
    "graph_dir": "dir",
    "graph_summary": "file",
    "claims_dir": "dir",
    "claims_summary": "file",
}


@dataclass(frozen=True)
class ChunkSidecarConsumerPromotionResult:
    source_set_id: str
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class JsonObjectReadResult:
    payload: dict[str, Any] | None
    present: bool
    error: str | None = None


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

    consumer_eval_read = _read_json_object_if_present(consumer_eval_results_path)
    consumer_eval = consumer_eval_read.payload or {}
    sidecar_paths = _sidecar_paths(consumer_eval)
    sidecar_boundary_errors = _sidecar_input_boundary_errors(
        derived_dir=derived_dir,
        sidecar_paths=sidecar_paths,
    )
    canonical_graph_dir = derived_dir / "evidence_graph"
    canonical_claims_dir = derived_dir / "claims"
    sidecar_graph_summary = _read_json_object_if_present(sidecar_paths["graph_summary"])
    sidecar_claim_summary = _read_json_object_if_present(sidecar_paths["claims_summary"])
    checks = _preflight_checks(
        source_set_id=source_set_id,
        consumer_eval=consumer_eval,
        consumer_eval_read=consumer_eval_read,
        consumer_eval_results_path=consumer_eval_results_path,
        sidecar_paths=sidecar_paths,
        sidecar_boundary_errors=sidecar_boundary_errors,
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
            sidecar_paths=_require_sidecar_paths(sidecar_paths),
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
            "atomic_chunks_path": _path_string(sidecar_paths["atomic_chunks"]),
            "retrieval_summary_path": _path_string(sidecar_paths["retrieval_summary"]),
            "retrieval_validation_path": _path_string(sidecar_paths["retrieval_validation"]),
            "graph_dir": _path_string(sidecar_paths["graph_dir"]),
            "graph_summary_path": _path_string(sidecar_paths["graph_summary"]),
            "claims_dir": _path_string(sidecar_paths["claims_dir"]),
            "claims_summary_path": _path_string(sidecar_paths["claims_summary"]),
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


def _sidecar_paths(consumer_eval: dict[str, Any]) -> dict[str, Path | None]:
    sidecar_index_dir = _optional_path(consumer_eval.get("sidecar_index_dir"))
    return {
        "atomic_chunks": _optional_path(consumer_eval.get("atomic_chunks_path")),
        "retrieval_summary": _optional_path(consumer_eval.get("sidecar_index_summary_path")),
        "retrieval_validation": (
            sidecar_index_dir / "retrieval_validation.json" if sidecar_index_dir else None
        ),
        "graph_dir": _optional_path(consumer_eval.get("sidecar_graph_dir")),
        "graph_summary": _optional_path(consumer_eval.get("sidecar_graph_summary_path")),
        "claims_dir": _optional_path(consumer_eval.get("sidecar_claims_dir")),
        "claims_summary": _optional_path(consumer_eval.get("sidecar_claims_summary_path")),
    }


def _optional_path(value: object | None) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return Path(text)


def _path_string(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _require_sidecar_paths(sidecar_paths: dict[str, Path | None]) -> dict[str, Path]:
    missing = [label for label, path in sidecar_paths.items() if path is None]
    if missing:
        raise ValueError(f"Missing sidecar input paths for promotion: {', '.join(sorted(missing))}")
    return {label: path for label, path in sidecar_paths.items() if path is not None}


def _sidecar_input_boundary_errors(
    *,
    derived_dir: Path,
    sidecar_paths: dict[str, Path | None],
) -> dict[str, str]:
    errors = {}
    for label, requested_dir in (
        ("chunks_v2_dir", _parent_dir(sidecar_paths["atomic_chunks"])),
        ("sidecar_index_dir", _parent_dir(sidecar_paths["retrieval_summary"])),
        ("sidecar_graph_dir", sidecar_paths["graph_dir"]),
        ("sidecar_claims_dir", sidecar_paths["claims_dir"]),
    ):
        if requested_dir is None:
            continue
        for canonical_name in CANONICAL_CONSUMER_DIRS:
            try:
                _ensure_noncanonical_sidecar_dir(
                    requested_dir=requested_dir,
                    canonical_dir=derived_dir / canonical_name,
                    label=label,
                )
            except ValueError as exc:
                errors[label] = str(exc)
    return errors


def _parent_dir(path: Path | None) -> Path | None:
    return path.parent if path is not None else None


def _read_json_object_if_present(path: Path | None) -> JsonObjectReadResult:
    if path is None:
        return JsonObjectReadResult(payload=None, present=False)
    if not path.exists():
        return JsonObjectReadResult(payload=None, present=False)
    if not path.is_file():
        return JsonObjectReadResult(
            payload=None,
            present=True,
            error=f"JSON path is not a file: {path}",
        )
    try:
        payload = _read_json(path)
    except (OSError, ValueError) as exc:
        return JsonObjectReadResult(
            payload=None,
            present=True,
            error=f"{type(exc).__name__}: {exc}",
        )
    if not isinstance(payload, dict):
        return JsonObjectReadResult(
            payload=None,
            present=True,
            error=f"JSON payload is not an object: {path}",
        )
    return JsonObjectReadResult(payload=payload, present=True)


def _preflight_checks(
    *,
    source_set_id: str,
    consumer_eval: dict[str, Any],
    consumer_eval_read: JsonObjectReadResult,
    consumer_eval_results_path: Path,
    sidecar_paths: dict[str, Path | None],
    sidecar_boundary_errors: dict[str, str],
    sidecar_graph_summary: JsonObjectReadResult,
    sidecar_claim_summary: JsonObjectReadResult,
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
            "passed": consumer_eval_read.present,
            "details": {"path": str(consumer_eval_results_path)},
        },
        {
            "name": "consumer_eval_results_readable",
            "passed": consumer_eval_read.present
            and consumer_eval_read.payload is not None
            and consumer_eval_read.error is None,
            "details": {
                "path": str(consumer_eval_results_path),
                "error": consumer_eval_read.error,
            },
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
            read_result=sidecar_graph_summary,
            expected_source_set_id=source_set_id,
        ),
        _sidecar_summary_check(
            name="sidecar_claim_summary_valid",
            read_result=sidecar_claim_summary,
            expected_source_set_id=source_set_id,
        ),
        {
            "name": "sidecar_required_paths_declared",
            "passed": all(path is not None for path in sidecar_paths.values()),
            "details": {
                label: {
                    "source_field": SIDECAR_PATH_FIELDS[label],
                    "path": _path_string(path),
                    "declared": path is not None,
                }
                for label, path in sidecar_paths.items()
            },
        },
        {
            "name": "sidecar_input_paths_exist",
            "passed": all(path is not None and path.exists() for path in sidecar_paths.values()),
            "details": _sidecar_path_details(sidecar_paths),
        },
        {
            "name": "sidecar_input_path_kinds_valid",
            "passed": all(_path_kind_valid(label, path) for label, path in sidecar_paths.items()),
            "details": _sidecar_path_details(sidecar_paths),
        },
        {
            "name": "sidecar_inputs_are_noncanonical",
            "passed": not sidecar_boundary_errors,
            "details": {"errors": sidecar_boundary_errors},
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
    read_result: JsonObjectReadResult,
    expected_source_set_id: str,
) -> dict[str, Any]:
    summary = read_result.payload
    return {
        "name": name,
        "passed": bool(
            summary
            and read_result.error is None
            and summary.get("source_set_id") == expected_source_set_id
            and summary.get("validation_passed")
            and summary.get("reviewer_ready")
        ),
        "details": {
            "present": read_result.present,
            "error": read_result.error,
            "source_set_id": (summary or {}).get("source_set_id"),
            "validation_passed": (summary or {}).get("validation_passed"),
            "reviewer_ready": (summary or {}).get("reviewer_ready"),
        },
    }


def _sidecar_path_details(sidecar_paths: dict[str, Path | None]) -> dict[str, dict[str, Any]]:
    return {
        label: {
            "source_field": SIDECAR_PATH_FIELDS[label],
            "path": _path_string(path),
            "expected_kind": SIDECAR_PATH_KINDS[label],
            "exists": path.exists() if path is not None else False,
            "is_file": path.is_file() if path is not None else False,
            "is_dir": path.is_dir() if path is not None else False,
            "kind_valid": _path_kind_valid(label, path),
        }
        for label, path in sidecar_paths.items()
    }


def _path_kind_valid(label: str, path: Path | None) -> bool:
    if path is None or not path.exists():
        return False
    expected_kind = SIDECAR_PATH_KINDS[label]
    if expected_kind == "file":
        return path.is_file()
    return path.is_dir()


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
