from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .applicability_retrieval_graph import _external_graph_index
from .applicability_retrieval_graph import _graph_trace_rows_for_candidate
from .applicability_retrieval_runtime import PACKAGE_QUERY_TYPES
from .applicability_retrieval_runtime import QUERY_TYPES_WITH_SOURCE_INDEX
from .applicability_retrieval_runtime import _execute_query_spec
from .applicability_retrieval_runtime import _fused_trace_row
from .applicability_retrieval_runtime import _prepare_package_fact_graph_search
from .applicability_retrieval_runtime import _query_specs_for_candidate
from .applicability_retrieval_runtime import _strings
from .records import sha256_file
from .retrieval import default_index_path
from .selected_action import load_selected_action_from_artifact_path
from .selected_action import selected_action_path_from_artifact


APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION = "applicability-graph-trace-v0"
APPLICABILITY_TRACE_DIAGNOSTICS_SCHEMA_VERSION = "applicability-trace-diagnostics-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ApplicabilityRetrievalTraceResult:
    review_id: str
    source_set_id: str
    applicability_dir: Path
    retrieval_trace_path: Path
    graph_trace_path: Path
    diagnostics_path: Path
    summary: dict[str, Any]


def build_applicability_retrieval_traces(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    authority_universe_path: Path | None = None,
    package_fact_graph_path: Path | None = None,
    retrieval_index_path: Path | None = None,
    graph_nodes_path: Path | None = None,
    graph_edges_path: Path | None = None,
    top_k: int = 5,
    max_graph_paths_per_candidate: int = 25,
) -> ApplicabilityRetrievalTraceResult:
    """Run replayable candidate evidence discovery without deciding applicability."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if max_graph_paths_per_candidate < 1:
        raise ValueError("max_graph_paths_per_candidate must be at least 1")
    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    authority_universe_path = (
        Path(authority_universe_path)
        if authority_universe_path
        else applicability_dir / "authority_universe_snapshot.json"
    )
    package_fact_graph_path = (
        Path(package_fact_graph_path)
        if package_fact_graph_path
        else applicability_dir / "package_fact_graph.json"
    )
    authority_universe = _read_required_json(authority_universe_path, "authority universe")
    package_fact_graph = _read_required_json(package_fact_graph_path, "package fact graph")
    _prepare_package_fact_graph_search(package_fact_graph)
    selected_action_path = selected_action_path_from_artifact(package_fact_graph)
    selected_action = load_selected_action_from_artifact_path(selected_action_path)

    if source_set_id is None:
        source_set_id = str(authority_universe.get("source_set_id") or "").strip()
    _validate_safe_segment(source_set_id, "source_set_id")
    retrieval_index_path = (
        Path(retrieval_index_path)
        if retrieval_index_path
        else default_index_path(output_dir, source_set_id)
    )
    if graph_nodes_path is None:
        graph_nodes_path = (
            output_dir
            / "derived"
            / source_set_id
            / "evidence_graph"
            / "document_graph_nodes.jsonl"
        )
    if graph_edges_path is None:
        graph_edges_path = (
            output_dir
            / "derived"
            / source_set_id
            / "evidence_graph"
            / "document_graph_edges.jsonl"
        )
    graph_nodes_path = Path(graph_nodes_path)
    graph_edges_path = Path(graph_edges_path)
    graph_nodes = _read_jsonl_if_exists(graph_nodes_path)
    graph_edges = _read_jsonl_if_exists(graph_edges_path)
    external_graph_index = _external_graph_index(
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
    )
    rule_claim_links = _read_jsonl_if_exists(
        _optional_artifact_path(authority_universe, "rule_claim_links_path")
    )
    source_claims = _read_jsonl_if_exists(
        _optional_artifact_path(authority_universe, "claims_path")
    )

    applicability_run_id = f"applicability-retrieval:{review_id}:{source_set_id}"
    created_at = _utc_now()
    searched_index_identity = _searched_index_identity(retrieval_index_path)
    package_graph_identity = _graph_artifact_identity(
        artifact_type="package_fact_graph",
        path=package_fact_graph_path,
        payload=package_fact_graph,
    )
    evidence_graph_identity = _graph_artifact_identity(
        artifact_type="evidence_graph",
        path=graph_nodes_path,
        payload=None,
        companion_path=graph_edges_path,
    )
    candidates = list(authority_universe.get("candidate_authorities") or [])
    source_results_cache: dict[tuple, list[dict[str, Any]]] = {}
    package_results_cache: dict[tuple, list[tuple[float, dict[str, Any]]]] = {}
    package_match_cache: dict[tuple, list[dict[str, Any]]] = {}

    retrieval_rows: list[dict[str, Any]] = []
    graph_rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: str(item.get("candidate_authority_id"))):
        candidate_id = str(candidate.get("candidate_authority_id") or "")
        query_specs = _query_specs_for_candidate(candidate)
        candidate_trace_rows = []
        for index, spec in enumerate(query_specs, start=1):
            trace_row = _execute_query_spec(
                applicability_run_id=applicability_run_id,
                review_id=review_id,
                source_set_id=source_set_id,
                candidate=candidate,
                query_spec=spec,
                query_index=index,
                retrieval_index_path=retrieval_index_path,
                searched_index_identity=searched_index_identity,
                source_results_cache=source_results_cache,
                package_fact_graph=package_fact_graph,
                selected_action=selected_action,
                package_graph_identity=package_graph_identity,
                package_results_cache=package_results_cache,
                top_k=top_k,
                created_at=created_at,
                query_diagnostics=_query_diagnostics,
            )
            candidate_trace_rows.append(trace_row)
            retrieval_rows.append(trace_row)

        fused_row = _fused_trace_row(
            applicability_run_id=applicability_run_id,
            review_id=review_id,
            source_set_id=source_set_id,
            candidate=candidate,
            trace_rows=candidate_trace_rows,
            searched_index_identity=searched_index_identity,
            retrieval_index_path=retrieval_index_path,
            top_k=top_k,
            created_at=created_at,
            query_diagnostics=_query_diagnostics,
        )
        candidate_trace_rows.append(fused_row)
        retrieval_rows.append(fused_row)

        candidate_graph_rows, candidate_diagnostics = _graph_trace_rows_for_candidate(
            applicability_run_id=applicability_run_id,
            review_id=review_id,
            source_set_id=source_set_id,
            candidate=candidate,
            retrieval_trace_rows=candidate_trace_rows,
            package_fact_graph=package_fact_graph,
            selected_action=selected_action,
            package_graph_identity=package_graph_identity,
            evidence_graph_identity=evidence_graph_identity,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            external_graph_index=external_graph_index,
            rule_claim_links=rule_claim_links,
            source_claims=source_claims,
            package_match_cache=package_match_cache,
            max_graph_paths_per_candidate=max_graph_paths_per_candidate,
            created_at=created_at,
        )
        graph_rows.extend(candidate_graph_rows)
        diagnostics.extend(candidate_diagnostics)
        diagnostics.extend(
            _retrieval_diagnostics_for_candidate(
                candidate_id=candidate_id,
                trace_rows=candidate_trace_rows,
                retrieval_index_path=retrieval_index_path,
            )
        )

    retrieval_trace_path = applicability_dir / "applicability_retrieval_trace.jsonl"
    graph_trace_path = applicability_dir / "applicability_graph_trace.jsonl"
    diagnostics_path = applicability_dir / "applicability_retrieval_graph_diagnostics.json"
    validation = _validation(
        candidates=candidates,
        retrieval_rows=retrieval_rows,
        graph_rows=graph_rows,
        retrieval_index_path=retrieval_index_path,
    )
    retrieval_trace_sha256 = _write_jsonl_and_hash(retrieval_trace_path, retrieval_rows)
    graph_trace_sha256 = _write_jsonl_and_hash(graph_trace_path, graph_rows)
    diagnostics_payload = {
        "schema_version": APPLICABILITY_TRACE_DIAGNOSTICS_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "authority_universe_path": str(authority_universe_path),
        "package_fact_graph_path": str(package_fact_graph_path),
        "retrieval_trace_path": str(retrieval_trace_path),
        "graph_trace_path": str(graph_trace_path),
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "validation": validation,
        "diagnostics": sorted(
            diagnostics,
            key=lambda item: (
                str(item.get("candidate_authority_id") or ""),
                str(item.get("diagnostic_type") or ""),
            ),
        ),
        "summary": _summary(
            candidates=candidates,
            retrieval_rows=retrieval_rows,
            graph_rows=graph_rows,
            diagnostics=diagnostics,
            validation=validation,
        ),
    }
    diagnostics_sha256 = _write_json_and_hash(diagnostics_path, diagnostics_payload)
    summary = {
        **diagnostics_payload["summary"],
        "validation_passed": validation["passed"],
        "retrieval_trace_path": str(retrieval_trace_path),
        "graph_trace_path": str(graph_trace_path),
        "diagnostics_path": str(diagnostics_path),
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "diagnostics_sha256": diagnostics_sha256,
        "retrieval_index_path": str(retrieval_index_path),
        "retrieval_index_exists": retrieval_index_path.exists(),
    }
    return ApplicabilityRetrievalTraceResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        retrieval_trace_path=retrieval_trace_path,
        graph_trace_path=graph_trace_path,
        diagnostics_path=diagnostics_path,
        summary=summary,
    )


def _validation(
    *,
    candidates: list[dict[str, Any]],
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
    retrieval_index_path: Path,
) -> dict[str, Any]:
    candidate_ids = {
        str(candidate.get("candidate_authority_id") or "") for candidate in candidates
    }
    retrieval_candidate_ids = {
        str(row.get("candidate_authority_id") or "") for row in retrieval_rows
    }
    graph_candidate_ids = {
        str(row.get("candidate_authority_id") or "") for row in graph_rows
    }
    checks = [
        {
            "name": "retrieval_index_exists",
            "passed": retrieval_index_path.exists(),
            "details": {"path": str(retrieval_index_path)},
        },
        {
            "name": "each_candidate_has_retrieval_trace",
            "passed": candidate_ids <= retrieval_candidate_ids,
            "details": {
                "missing_candidate_authority_ids": sorted(candidate_ids - retrieval_candidate_ids),
                "candidate_count": len(candidate_ids),
            },
        },
        {
            "name": "each_candidate_has_graph_trace",
            "passed": candidate_ids <= graph_candidate_ids,
            "details": {
                "missing_candidate_authority_ids": sorted(candidate_ids - graph_candidate_ids),
                "candidate_count": len(candidate_ids),
            },
        },
        _check_selected_results_have_provenance(retrieval_rows),
        _check_graph_paths_are_bounded(candidates, graph_rows),
        _check_no_decision_artifacts(retrieval_rows, graph_rows),
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_selected_results_have_provenance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for row in rows:
        for result in row.get("ranked_results") or []:
            if result.get("selected_status") != "selected":
                continue
            has_source = result.get("source_record_id") and result.get("source_chunk_id")
            has_package = result.get("package_chunk_id") or result.get("package_fact_node_id")
            if not result.get("text_hash") or not (has_source or has_package):
                failures.append(result.get("result_id"))
    return {
        "name": "selected_results_have_source_or_package_provenance",
        "passed": not failures,
        "details": {
            "failure_count": len(failures),
            "result_ids": failures[:50],
        },
    }


def _check_graph_paths_are_bounded(
    candidates: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_contracts = {
        str(candidate.get("candidate_authority_id") or ""): candidate.get(
            "graph_expansion_contract"
        )
        or {}
        for candidate in candidates
    }
    failures = []
    for row in graph_rows:
        contract = candidate_contracts.get(str(row.get("candidate_authority_id") or ""), {})
        max_depth = int(contract.get("max_depth") or 0)
        allowed = set(_strings(contract.get("relationship_types")))
        relationships = set(_strings(row.get("relationship_types")))
        if int(row.get("traversal_depth") or 0) > max_depth or not relationships <= allowed:
            failures.append(row.get("graph_path_id"))
    return {
        "name": "graph_paths_respect_candidate_contracts",
        "passed": not failures,
        "details": {"failure_count": len(failures), "graph_path_ids": failures[:50]},
    }


def _check_no_decision_artifacts(
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    forbidden_statuses = {"applicable", "not_applicable", "needs_adjudication", "unresolved"}
    failures = []
    for row in [*retrieval_rows, *graph_rows]:
        if str(row.get("status") or "") in forbidden_statuses:
            failures.append(
                row.get("retrieval_trace_id") or row.get("graph_path_id") or "unknown"
            )
    return {
        "name": "trace_rows_do_not_contain_applicability_decisions",
        "passed": not failures,
        "details": {"failure_count": len(failures), "trace_ids": failures[:50]},
    }


def _summary(
    *,
    candidates: list[dict[str, Any]],
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    validation: dict[str, Any],
) -> dict[str, Any]:
    candidate_ids_with_selected_results = {
        row["candidate_authority_id"]
        for row in retrieval_rows
        if any(
            result.get("selected_status") == "selected"
            for result in row.get("ranked_results") or []
        )
    }
    return {
        "candidate_authority_count": len(candidates),
        "retrieval_trace_row_count": len(retrieval_rows),
        "graph_trace_row_count": len(graph_rows),
        "candidate_with_selected_result_count": len(candidate_ids_with_selected_results),
        "diagnostic_count": len(diagnostics),
        "diagnostic_type_counts": dict(
            sorted(Counter(str(item.get("diagnostic_type")) for item in diagnostics).items())
        ),
        "query_type_counts": dict(
            sorted(Counter(str(row.get("query_type")) for row in retrieval_rows).items())
        ),
        "graph_selected_count": sum(
            1 for row in graph_rows if row.get("selected_status") == "selected"
        ),
        "validation_passed": validation["passed"],
    }


def _retrieval_diagnostics_for_candidate(
    *,
    candidate_id: str,
    trace_rows: list[dict[str, Any]],
    retrieval_index_path: Path,
) -> list[dict[str, Any]]:
    diagnostics = []
    if not retrieval_index_path.exists():
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "retrieval_index_missing",
                "severity": "error",
                "message": "Retrieval index is missing; source-library searches are empty.",
                "path": str(retrieval_index_path),
            }
        )
    source_hit_count = sum(
        len(row.get("ranked_results") or [])
        for row in trace_rows
        if row.get("query_type") in QUERY_TYPES_WITH_SOURCE_INDEX
    )
    package_hit_count = sum(
        len(row.get("ranked_results") or [])
        for row in trace_rows
        if row.get("query_type") in PACKAGE_QUERY_TYPES
    )
    if source_hit_count == 0:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "retrieval_miss",
                "severity": "warning",
                "message": "No source-library retrieval results were found for this candidate.",
            }
        )
    if package_hit_count == 0:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "package_trace_miss",
                "severity": "warning",
                "message": "No package fact or package section results were found for this candidate.",
            }
        )
    low_confidence = [
        result
        for row in trace_rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "selected"
        and float(result.get("score") or 0) < 0.05
    ]
    if low_confidence:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "low_confidence_retrieval",
                "severity": "warning",
                "message": "One or more selected retrieval results have low deterministic score.",
                "result_count": len(low_confidence),
            }
        )
    return diagnostics


def _query_diagnostics(
    *,
    query_type: str,
    retrieval_index_path: Path,
    result_count: int,
) -> list[dict[str, Any]]:
    diagnostics = []
    if query_type in QUERY_TYPES_WITH_SOURCE_INDEX and not retrieval_index_path.exists():
        diagnostics.append({"diagnostic_type": "retrieval_index_missing", "severity": "error"})
    if result_count == 0:
        diagnostics.append({"diagnostic_type": "zero_results", "severity": "warning"})
    return diagnostics

def _searched_index_identity(path: Path) -> dict[str, Any]:
    return {
        "index_type": "sqlite_retrieval_index",
        "index_path": str(path),
        "index_exists": path.exists(),
        "index_build_id": _sqlite_metadata_value(path, "created_at") if path.exists() else None,
        "searched_index_hash": sha256_file(path) if path.exists() else None,
    }


def _graph_artifact_identity(
    *,
    artifact_type: str,
    path: Path,
    payload: dict[str, Any] | None,
    companion_path: Path | None = None,
) -> dict[str, Any]:
    hash_inputs = [sha256_file(path)] if path.exists() else []
    if companion_path and companion_path.exists():
        hash_inputs.append(sha256_file(companion_path))
    artifact_hash = (
        hashlib.sha256("|".join(hash_inputs).encode("utf-8")).hexdigest()
        if hash_inputs
        else None
    )
    graph_build_id = None
    if payload:
        graph_build_id = (
            payload.get("package_fact_graph_id")
            or payload.get("graph_id")
            or payload.get("schema_version")
        )
    return {
        "graph_artifact_type": artifact_type,
        "graph_build_id": graph_build_id,
        "graph_artifact_path": str(path),
        "graph_companion_path": str(companion_path) if companion_path else None,
        "graph_artifact_hash": artifact_hash,
        "graph_artifact_exists": path.exists(),
    }


def _sqlite_metadata_value(path: Path, key: str) -> Any:
    try:
        import sqlite3

        with sqlite3.connect(path) as connection:
            row = connection.execute(
                "SELECT value_json FROM metadata WHERE key = ?",
                (key,),
            ).fetchone()
    except sqlite3.Error:
        return None
    if not row:
        return None
def _optional_artifact_path(payload: dict[str, Any], key: str) -> Path | None:
    artifacts = payload.get("artifact_paths")
    if not isinstance(artifacts, dict):
        return None
    value = str(artifacts.get(key) or "").strip()
    return Path(value) if value else None


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return value


def _read_jsonl_if_exists(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object lines in {path}")
        records.append(value)
    return records


def _write_jsonl_and_hash(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return sha256_file(path)


def _write_json_and_hash(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256_file(path)


def _validate_safe_segment(value: str, field_name: str) -> None:
    if not SAFE_SEGMENT_RE.fullmatch(str(value or "")):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
