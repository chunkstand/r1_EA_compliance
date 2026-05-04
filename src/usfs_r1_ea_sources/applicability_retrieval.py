from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .records import sha256_file
from .retrieval import default_index_path
from .retrieval import query_retrieval_index


APPLICABILITY_RETRIEVAL_TRACE_SCHEMA_VERSION = "applicability-retrieval-trace-v0"
APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION = "applicability-graph-trace-v0"
APPLICABILITY_TRACE_DIAGNOSTICS_SCHEMA_VERSION = "applicability-trace-diagnostics-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
QUERY_TYPES_WITH_SOURCE_INDEX = {
    "exact_keyword",
    "bm25",
    "citation",
    "metadata_filter",
    "source_role",
    "authority_category",
}
PACKAGE_QUERY_TYPES = {"package_section", "graph_seed"}
RRF_K = 60


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
                package_fact_graph=package_fact_graph,
                package_graph_identity=package_graph_identity,
                top_k=top_k,
                created_at=created_at,
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
            top_k=top_k,
            created_at=created_at,
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
            package_graph_identity=package_graph_identity,
            evidence_graph_identity=evidence_graph_identity,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            rule_claim_links=rule_claim_links,
            source_claims=source_claims,
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


def _query_specs_for_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    contract = candidate.get("retrieval_contract")
    if not isinstance(contract, dict):
        contract = {}
    source_filters = _source_filters(candidate)
    package_filters = _package_filters(candidate)
    source_queries = _strings(contract.get("source_queries"))
    package_queries = _strings(contract.get("package_queries"))
    trigger_queries = _flatten_groups(candidate.get("positive_trigger_groups")) + _flatten_groups(
        candidate.get("negative_trigger_groups")
    )
    fallback_query = _candidate_fallback_query(candidate)
    source_query = _first(source_queries) or fallback_query
    package_query = _first(package_queries) or _first(trigger_queries) or fallback_query
    specs: list[dict[str, Any]] = [
        {
            "query_type": "exact_keyword",
            "query_text": source_query,
            "query_source": "retrieval_contract.source_queries",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "bm25",
            "query_text": source_query,
            "query_source": "retrieval_contract.source_queries",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "metadata_filter",
            "query_text": "",
            "query_source": "candidate.source_role_filters",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "source_role",
            "query_text": "",
            "query_source": "candidate.source_role_filters",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "authority_category",
            "query_text": str(candidate.get("authority_category") or ""),
            "query_source": "candidate.authority_category",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "citation",
            "query_text": _citation_query(candidate),
            "query_source": "candidate.source_records",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "package_section",
            "query_text": package_query,
            "query_source": "retrieval_contract.package_queries",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "graph_seed",
            "query_text": package_query,
            "query_source": "package_fact_graph",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
    ]
    allowed = set(_strings(contract.get("required_query_types"))) | {
        "citation",
        "authority_category",
        "graph_seed",
    }
    filtered = [spec for spec in specs if spec["query_type"] in allowed]
    return filtered or specs


def _execute_query_spec(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    query_spec: dict[str, Any],
    query_index: int,
    retrieval_index_path: Path,
    searched_index_identity: dict[str, Any],
    package_fact_graph: dict[str, Any],
    package_graph_identity: dict[str, Any],
    top_k: int,
    created_at: str,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    query_plan_id = str(
        (candidate.get("retrieval_contract") or {}).get("query_plan_id")
        or f"retrieval-plan:{candidate_id}"
    )
    query_type = str(query_spec["query_type"])
    query_text = str(query_spec.get("query_text") or "")
    trace_id = _stable_id(
        "retrieval-trace",
        applicability_run_id,
        candidate_id,
        query_type,
        str(query_index),
        query_text,
    )
    if query_type in PACKAGE_QUERY_TYPES:
        results = _package_results(
            trace_id=trace_id,
            query_text=query_text,
            query_type=query_type,
            candidate=candidate,
            package_fact_graph=package_fact_graph,
            top_k=top_k,
        )
        searched_identity = package_graph_identity
    else:
        results = _source_results(
            trace_id=trace_id,
            query_text=query_text,
            query_type=query_type,
            query_spec=query_spec,
            retrieval_index_path=retrieval_index_path,
            top_k=top_k,
        )
        searched_identity = searched_index_identity
    return {
        "schema_version": APPLICABILITY_RETRIEVAL_TRACE_SCHEMA_VERSION,
        "trace_kind": "query_execution",
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "retrieval_trace_id": trace_id,
        "query_plan_id": query_plan_id,
        "query_text": query_text,
        "query_type": query_type,
        "query_terms": _tokenize(query_text),
        "query_timestamp": created_at,
        "query_source": query_spec.get("query_source"),
        "source_filters": query_spec.get("source_filters") or {},
        "package_section_filters": query_spec.get("package_section_filters") or {},
        "source_record_filters": (query_spec.get("source_filters") or {}).get(
            "source_record_ids",
            [],
        ),
        "authority_category_filters": (query_spec.get("source_filters") or {}).get(
            "authority_categories",
            [],
        ),
        "forest_plan_component_filters": _forest_plan_component_filters(candidate),
        "currentness_filters": _currentness_filters(candidate),
        "searched_index": searched_identity,
        "ranked_results": results,
        "fusion_metadata": None,
        "diagnostics": _query_diagnostics(
            query_type=query_type,
            retrieval_index_path=retrieval_index_path,
            result_count=len(results),
        ),
    }


def _source_results(
    *,
    trace_id: str,
    query_text: str,
    query_type: str,
    query_spec: dict[str, Any],
    retrieval_index_path: Path,
    top_k: int,
) -> list[dict[str, Any]]:
    if not retrieval_index_path.exists():
        return []
    source_filters = query_spec.get("source_filters") or {}
    source_record_ids = _strings(source_filters.get("source_record_ids"))
    document_roles = _strings(source_filters.get("document_roles"))
    authority_categories = _strings(source_filters.get("authority_categories"))
    source_record_id = _first(source_record_ids)
    document_role = _first(document_roles)
    authority_level = _first(authority_categories)
    citation = source_record_id if query_type == "citation" else None
    query_for_index = query_text
    if query_type in {"metadata_filter", "source_role", "citation"}:
        query_for_index = ""
    result = query_retrieval_index(
        index_path=retrieval_index_path,
        query=query_for_index,
        limit=max(top_k * 2, top_k),
        document_role=document_role,
        authority_level=authority_level,
        source_record_id=source_record_id,
        citation=citation,
    )
    query_terms = _tokenize(query_text)
    return [
        _source_result_row(
            trace_id=trace_id,
            hit=hit,
            result_index=index,
            query_type=query_type,
            query_terms=query_terms,
            top_k=top_k,
        )
        for index, hit in enumerate(result["results"], start=1)
    ]


def _source_result_row(
    *,
    trace_id: str,
    hit: dict[str, Any],
    result_index: int,
    query_type: str,
    query_terms: list[str],
    top_k: int,
) -> dict[str, Any]:
    provenance = hit.get("provenance") or {}
    span = hit.get("evidence_span") or {}
    selected = result_index <= top_k
    result_id = _stable_id(
        "retrieval-result",
        trace_id,
        str(hit.get("chunk_id") or ""),
        str(result_index),
    )
    return {
        "result_id": result_id,
        "result_kind": "source_chunk",
        "rank": result_index,
        "score": hit.get("score"),
        "fused_score": None,
        "selected_status": "selected" if selected else "rejected",
        "rejection_reason": None if selected else "outside_top_k",
        "query_type": query_type,
        "source_record_id": hit.get("source_record_id"),
        "package_chunk_id": None,
        "source_chunk_id": hit.get("chunk_id"),
        "claim_id": None,
        "section_family": _section_family_from_hit(hit),
        "citation_label": hit.get("citation_label"),
        "page_label": _page_label(provenance.get("page")),
        "char_start": span.get("source_char_start"),
        "char_end": span.get("source_char_end"),
        "chunk_char_start": span.get("chunk_char_start"),
        "chunk_char_end": span.get("chunk_char_end"),
        "matched_terms": _matched_terms(query_terms, span.get("text") or ""),
        "text_hash": provenance.get("content_sha256"),
        "content_sha256": provenance.get("content_sha256"),
        "artifact_sha256": provenance.get("artifact_sha256"),
        "text_excerpt": span.get("text"),
        "provenance": provenance,
    }


def _package_results(
    *,
    trace_id: str,
    query_text: str,
    query_type: str,
    candidate: dict[str, Any],
    package_fact_graph: dict[str, Any],
    top_k: int,
) -> list[dict[str, Any]]:
    query_terms = _tokenize(query_text)
    package_filters = _package_filters(candidate)
    required_types = set(_strings(candidate.get("required_package_fact_types")))
    scored: list[tuple[float, dict[str, Any]]] = []
    for node in package_fact_graph.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("node_type") or "")
        if node_type == "evidence_span":
            continue
        score = _score_package_node(
            node=node,
            query_terms=query_terms,
            required_types=required_types,
            package_filters=package_filters,
        )
        if score <= 0:
            continue
        scored.append((score, node))
    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1].get("node_type") or ""),
            str(item[1].get("node_id") or ""),
        )
    )
    results = []
    for index, (score, node) in enumerate(scored[: max(top_k * 2, top_k)], start=1):
        selected = index <= top_k
        results.append(
            {
                "result_id": _stable_id(
                    "retrieval-result",
                    trace_id,
                    str(node.get("node_id") or ""),
                    str(index),
                ),
                "result_kind": (
                    "package_section"
                    if node.get("node_type") == "package_section"
                    else "package_fact"
                ),
                "rank": index,
                "score": round(score, 6),
                "fused_score": None,
                "selected_status": "selected" if selected else "rejected",
                "rejection_reason": None if selected else "outside_top_k",
                "query_type": query_type,
                "source_record_id": None,
                "package_chunk_id": _first(_strings(node.get("package_chunk_ids"))),
                "source_chunk_id": None,
                "claim_id": None,
                "package_fact_node_id": node.get("node_id"),
                "section_family": node.get("section_family"),
                "citation_label": node.get("citation_label"),
                "page_label": node.get("page_label"),
                "char_start": node.get("char_start"),
                "char_end": node.get("char_end"),
                "chunk_char_start": node.get("chunk_char_start"),
                "chunk_char_end": node.get("chunk_char_end"),
                "matched_terms": _matched_terms(query_terms, _package_node_text(node)),
                "text_hash": node.get("text_hash") or node.get("content_sha256"),
                "content_sha256": node.get("content_sha256"),
                "artifact_sha256": node.get("artifact_sha256"),
                "text_excerpt": node.get("context_excerpt") or node.get("raw_value"),
                "provenance": {
                    "package_span_ids": node.get("package_span_ids")
                    or node.get("evidence_span_ids")
                    or [],
                    "evidence_span_ids": node.get("evidence_span_ids") or [],
                    "parser_provenance": node.get("parser_provenance") or {},
                    "section_ids": node.get("section_ids") or [],
                    "node_type": node.get("node_type"),
                    "fact_subtype": node.get("fact_subtype"),
                    "normalized_value": node.get("normalized_value"),
                    "confidence_class": node.get("confidence_class"),
                },
            }
        )
    return results


def _fused_trace_row(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    trace_rows: list[dict[str, Any]],
    searched_index_identity: dict[str, Any],
    top_k: int,
    created_at: str,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    trace_id = _stable_id("retrieval-trace", applicability_run_id, candidate_id, "fused")
    fused: dict[str, dict[str, Any]] = {}
    input_sets = []
    for row in trace_rows:
        row_id = str(row["retrieval_trace_id"])
        result_ids = []
        for result in row.get("ranked_results") or []:
            result_key = _fusion_result_key(result)
            if result_key not in fused:
                fused[result_key] = {
                    **result,
                    "score": 0.0,
                    "fused_score": 0.0,
                    "input_result_ids": [],
                    "input_trace_ids": [],
                    "source_query_types": [],
                }
            fused[result_key]["fused_score"] += 1.0 / (RRF_K + int(result.get("rank") or 0))
            fused[result_key]["score"] = fused[result_key]["fused_score"]
            fused[result_key]["input_result_ids"].append(result["result_id"])
            fused[result_key]["input_trace_ids"].append(row_id)
            fused[result_key]["source_query_types"].append(row.get("query_type"))
            result_ids.append(result["result_id"])
        input_sets.append(
            {
                "retrieval_trace_id": row_id,
                "query_type": row.get("query_type"),
                "result_ids": result_ids,
            }
        )
    ranked = sorted(
        fused.values(),
        key=lambda item: (
            -float(item.get("fused_score") or 0),
            str(item.get("result_kind") or ""),
            str(item.get("source_record_id") or item.get("package_fact_node_id") or ""),
        ),
    )
    final_results = []
    for index, result in enumerate(ranked, start=1):
        selected = index <= top_k
        final_results.append(
            {
                **result,
                "result_id": _stable_id("retrieval-result", trace_id, _fusion_result_key(result)),
                "rank": index,
                "fused_score": round(float(result.get("fused_score") or 0), 6),
                "score": round(float(result.get("score") or 0), 6),
                "selected_status": "selected" if selected else "rejected",
                "rejection_reason": None if selected else "outside_top_k",
                "query_type": "fused",
                "input_result_ids": sorted(set(result.get("input_result_ids") or [])),
                "input_trace_ids": sorted(set(result.get("input_trace_ids") or [])),
                "source_query_types": sorted(
                    {str(value) for value in result.get("source_query_types") or []}
                ),
            }
        )
    return {
        "schema_version": APPLICABILITY_RETRIEVAL_TRACE_SCHEMA_VERSION,
        "trace_kind": "fused_result_set",
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "retrieval_trace_id": trace_id,
        "query_plan_id": str(
            (candidate.get("retrieval_contract") or {}).get("query_plan_id")
            or f"retrieval-plan:{candidate_id}"
        ),
        "query_text": "",
        "query_type": "fused",
        "query_terms": [],
        "query_timestamp": created_at,
        "query_source": "reciprocal_rank_fusion",
        "source_filters": _source_filters(candidate),
        "package_section_filters": _package_filters(candidate),
        "source_record_filters": _strings(_source_filters(candidate).get("source_record_ids")),
        "authority_category_filters": _strings(
            _source_filters(candidate).get("authority_categories")
        ),
        "forest_plan_component_filters": _forest_plan_component_filters(candidate),
        "currentness_filters": _currentness_filters(candidate),
        "searched_index": searched_index_identity,
        "ranked_results": final_results,
        "fusion_metadata": {
            "fusion_strategy": "reciprocal_rank_fusion",
            "rrf_k": RRF_K,
            "input_result_sets": input_sets,
            "final_rank_order": [result["result_id"] for result in final_results],
        },
        "diagnostics": _query_diagnostics(
            query_type="fused",
            retrieval_index_path=Path(str(searched_index_identity.get("index_path") or "")),
            result_count=len(final_results),
        ),
    }


def _graph_trace_rows_for_candidate(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    retrieval_trace_rows: list[dict[str, Any]],
    package_fact_graph: dict[str, Any],
    package_graph_identity: dict[str, Any],
    evidence_graph_identity: dict[str, Any],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    rule_claim_links: list[dict[str, Any]],
    source_claims: list[dict[str, Any]],
    max_graph_paths_per_candidate: int,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    contract = candidate.get("graph_expansion_contract")
    if not isinstance(contract, dict):
        contract = {}
    allowed_relationships = set(_strings(contract.get("relationship_types")))
    max_depth = int(contract.get("max_depth") or 1)
    trace_graph = _candidate_trace_graph(
        candidate=candidate,
        package_fact_graph=package_fact_graph,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        rule_claim_links=rule_claim_links,
        source_claims=source_claims,
        retrieval_trace_rows=retrieval_trace_rows,
        allowed_relationships=allowed_relationships,
    )
    paths = _bounded_paths(
        start_node_id=f"candidate:{candidate_id}",
        adjacency=trace_graph["adjacency"],
        max_depth=max_depth,
        allowed_relationships=allowed_relationships,
    )
    diagnostics = []
    if not paths:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "graph_dead_end",
                "severity": "warning",
                "message": "No graph paths were discovered within the declared graph contract.",
            }
        )
        return [
            _graph_dead_end_row(
                applicability_run_id=applicability_run_id,
                review_id=review_id,
                source_set_id=source_set_id,
                candidate=candidate,
                package_graph_identity=package_graph_identity,
                evidence_graph_identity=evidence_graph_identity,
                created_at=created_at,
            )
        ], diagnostics

    selected_paths = paths[:max_graph_paths_per_candidate]
    if len(paths) > max_graph_paths_per_candidate:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "excessive_graph_fan_out",
                "severity": "warning",
                "message": (
                    "Graph expansion produced more paths than the configured trace limit."
                ),
                "path_count": len(paths),
                "max_graph_paths_per_candidate": max_graph_paths_per_candidate,
            }
        )
    rows = []
    for index, path in enumerate(selected_paths, start=1):
        path_id = _stable_id("graph-path", applicability_run_id, candidate_id, str(index), *path)
        relationship_types = _path_relationship_types(path)
        rows.append(
            {
                "schema_version": APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION,
                "applicability_run_id": applicability_run_id,
                "review_id": review_id,
                "source_set_id": source_set_id,
                "candidate_authority_id": candidate_id,
                "candidate_authority_type": candidate.get("candidate_authority_type"),
                "graph_path_id": path_id,
                "query_timestamp": created_at,
                "graph_artifacts": [package_graph_identity, evidence_graph_identity],
                "graph_build_id": evidence_graph_identity.get("graph_build_id"),
                "graph_artifact_path": evidence_graph_identity.get("graph_artifact_path"),
                "graph_artifact_hash": evidence_graph_identity.get("graph_artifact_hash"),
                "start_node_id": path[0],
                "end_node_id": path[-1],
                "traversed_node_ids": _path_node_ids(path),
                "relationship_types": relationship_types,
                "traversal_depth": len(relationship_types),
                "max_depth": max_depth,
                "path_rationale": _path_rationale(path, trace_graph["nodes"]),
                "selected_status": "selected",
                "rejection_reason": None,
                "evidence_references": _path_evidence_references(path, trace_graph["nodes"]),
                "bounded_by_contract": {
                    "allowed_relationship_types": sorted(allowed_relationships),
                    "max_depth": max_depth,
                },
            }
        )
    return rows, diagnostics


def _candidate_trace_graph(
    *,
    candidate: dict[str, Any],
    package_fact_graph: dict[str, Any],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    rule_claim_links: list[dict[str, Any]],
    source_claims: list[dict[str, Any]],
    retrieval_trace_rows: list[dict[str, Any]],
    allowed_relationships: set[str],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    start_node_id = f"candidate:{candidate_id}"
    nodes: dict[str, dict[str, Any]] = {
        start_node_id: {
            "node_id": start_node_id,
            "node_type": str(candidate.get("candidate_authority_type") or "candidate"),
            "candidate_authority_id": candidate_id,
        }
    }
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add_node(node_id: str, **metadata: Any) -> None:
        nodes.setdefault(node_id, {"node_id": node_id, **metadata})

    def add_edge(source: str, relationship: str, target: str) -> None:
        if relationship in allowed_relationships:
            adjacency[source].append((relationship, target))

    authority_category = str(candidate.get("authority_category") or "").strip()
    if authority_category:
        node_id = f"authority-category:{authority_category}"
        add_node(node_id, node_type="authority_category", authority_category=authority_category)
        add_edge(start_node_id, "authority_category", node_id)

    for source_record_id in _strings(candidate.get("source_record_ids")):
        node_id = f"source-record:{source_record_id}"
        add_node(node_id, node_type="source_record", source_record_id=source_record_id)
        add_edge(start_node_id, "source_record", node_id)
        if authority_category:
            add_edge(f"authority-category:{authority_category}", "source_record", node_id)

    for result in _selected_results(retrieval_trace_rows):
        if result.get("source_chunk_id"):
            node_id = f"source-chunk:{result['source_chunk_id']}"
            add_node(
                node_id,
                node_type="source_chunk",
                source_record_id=result.get("source_record_id"),
                retrieval_result_id=result.get("result_id"),
                retrieval_trace_ids=result.get("input_trace_ids") or [],
            )
            for source_record_id in _strings([result.get("source_record_id")]):
                source_record_node = f"source-record:{source_record_id}"
                add_node(
                    source_record_node,
                    node_type="source_record",
                    source_record_id=source_record_id,
                )
                add_edge(source_record_node, "source_chunk", node_id)
        if result.get("package_fact_node_id"):
            node_id = f"package-fact:{result['package_fact_node_id']}"
            add_node(
                node_id,
                node_type="package_fact",
                package_fact_node_id=result.get("package_fact_node_id"),
                package_chunk_id=result.get("package_chunk_id"),
                retrieval_result_id=result.get("result_id"),
                retrieval_trace_ids=result.get("input_trace_ids") or [],
            )
            add_edge(start_node_id, "package_fact", node_id)

    for node in package_fact_graph.get("nodes") or []:
        if not isinstance(node, dict) or node.get("node_type") in {"evidence_span", "package_section"}:
            continue
        if not _package_node_matches_candidate(node, candidate):
            continue
        node_id = f"package-fact:{node.get('node_id')}"
        add_node(
            node_id,
            node_type="package_fact",
            package_fact_node_id=node.get("node_id"),
            package_chunk_ids=node.get("package_chunk_ids") or [],
            evidence_span_ids=node.get("evidence_span_ids") or [],
            fact_type=node.get("node_type"),
            fact_subtype=node.get("fact_subtype"),
            normalized_value=node.get("normalized_value"),
        )
        add_edge(start_node_id, "package_fact", node_id)
        relationship = str(node.get("node_type") or "")
        if relationship in {"geography", "management_area", "overlay"}:
            add_edge(start_node_id, relationship, node_id)
        for span_id in node.get("evidence_span_ids") or []:
            span_node_id = f"evidence-span:{span_id}"
            add_node(span_node_id, node_type="evidence_span", evidence_span_id=span_id)
            add_edge(node_id, "evidence_span", span_node_id)

    rule_id = ((candidate.get("rule_template") or {}).get("rule_id") or "").strip()
    claims_by_id = {str(claim.get("claim_id")): claim for claim in source_claims}
    for link in rule_claim_links:
        if rule_id and str(link.get("rule_id") or "") != rule_id:
            continue
        link_id = str(link.get("link_id") or _stable_id("rule-claim-link", json.dumps(link, sort_keys=True)))
        link_node_id = f"rule-claim-link:{link_id}"
        add_node(
            link_node_id,
            node_type="rule_claim_link",
            link_id=link_id,
            rule_id=link.get("rule_id"),
        )
        add_edge(start_node_id, "rule_claim_link", link_node_id)
        claim_id = str(link.get("claim_id") or link.get("source_claim_id") or "")
        if claim_id:
            claim = claims_by_id.get(claim_id, {})
            claim_node_id = f"source-claim:{claim_id}"
            add_node(
                claim_node_id,
                node_type="source_claim",
                claim_id=claim_id,
                source_record_id=claim.get("source_record_id") or link.get("source_record_id"),
            )
            add_edge(link_node_id, "source_claim", claim_node_id)

    forest_plan = candidate.get("forest_plan") if isinstance(candidate.get("forest_plan"), dict) else {}
    if forest_plan:
        profile_id = str(forest_plan.get("forest_unit_id") or "")
        profile_node_id = f"forest-plan-profile:{profile_id}"
        add_node(profile_node_id, node_type="forest_plan_profile", forest_unit_id=profile_id)
        add_edge(start_node_id, "forest_plan_profile", profile_node_id)
        component_id = str(forest_plan.get("component_id") or "")
        component_node_id = f"forest-plan-component:{component_id}"
        add_node(
            component_node_id,
            node_type="forest_plan_component",
            component_id=component_id,
            component_inventory_id=forest_plan.get("component_inventory_id"),
        )
        add_edge(profile_node_id, "component_inventory", component_node_id)

    dependency_contract = candidate.get("dependency_contract")
    if isinstance(dependency_contract, dict):
        for field, relationship in (
            ("dependency_rule_ids", "dependency"),
            ("exception_rule_ids", "exception"),
            ("supersedes_rule_ids", "supersession"),
        ):
            for value in _strings(dependency_contract.get(field)):
                node_id = f"{relationship}:{value}"
                add_node(node_id, node_type=relationship, rule_id=value)
                add_edge(start_node_id, relationship, node_id)
        for value in _strings(dependency_contract.get("supporting_source_record_ids")):
            node_id = f"source-record:{value}"
            add_node(
                node_id,
                node_type="source_record",
                source_record_id=value,
                source_record_relationship="supporting",
            )
            add_edge(start_node_id, "source_record", node_id)
        for record in dependency_contract.get("supporting_source_records") or []:
            if not isinstance(record, dict):
                continue
            source_record_id = str(record.get("source_record_id") or "").strip()
            if not source_record_id:
                continue
            node_id = f"source-record:{source_record_id}"
            add_node(
                node_id,
                node_type="source_record",
                source_record_id=source_record_id,
                source_record_relationship="supporting",
                source_record_role=record.get("role"),
                source_record_required_for=record.get("required_for"),
            )
            add_edge(start_node_id, "source_record", node_id)

    _merge_external_graph(
        nodes=nodes,
        adjacency=adjacency,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        allowed_relationships=allowed_relationships,
        candidate_source_record_ids=set(_strings(candidate.get("source_record_ids"))),
    )
    return {"nodes": nodes, "adjacency": adjacency}


def _merge_external_graph(
    *,
    nodes: dict[str, dict[str, Any]],
    adjacency: dict[str, list[tuple[str, str]]],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    allowed_relationships: set[str],
    candidate_source_record_ids: set[str],
) -> None:
    if not graph_nodes or not graph_edges or not candidate_source_record_ids:
        return
    allowed_node_ids = set(nodes)
    for node in graph_nodes:
        node_id = str(node.get("node_id") or "")
        node_source_ids = set(_strings(node.get("source_record_id"))) | set(
            _strings(node.get("source_record_ids"))
        )
        if node_id and node_source_ids & candidate_source_record_ids:
            allowed_node_ids.add(node_id)
            nodes.setdefault(node_id, node)
    for edge in graph_edges:
        relationship = str(edge.get("relationship_type") or edge.get("edge_type") or "")
        if relationship not in allowed_relationships:
            continue
        source = str(edge.get("from_node_id") or edge.get("source_node_id") or "")
        target = str(edge.get("to_node_id") or edge.get("target_node_id") or "")
        if source in allowed_node_ids and target:
            adjacency[source].append((relationship, target))
            nodes.setdefault(target, {"node_id": target, "node_type": "external_graph_node"})


def _bounded_paths(
    *,
    start_node_id: str,
    adjacency: dict[str, list[tuple[str, str]]],
    max_depth: int,
    allowed_relationships: set[str],
) -> list[list[str]]:
    paths: list[list[str]] = []
    queue: deque[list[str]] = deque([[start_node_id]])
    while queue:
        path = queue.popleft()
        depth = (len(path) - 1) // 2
        if depth >= max_depth:
            continue
        current = path[-1]
        for relationship, target in sorted(adjacency.get(current, [])):
            if relationship not in allowed_relationships:
                continue
            if target in _path_node_ids(path):
                continue
            next_path = [*path, relationship, target]
            paths.append(next_path)
            queue.append(next_path)
    return sorted(paths, key=lambda path: (len(path), "|".join(path)))


def _graph_dead_end_row(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    package_graph_identity: dict[str, Any],
    evidence_graph_identity: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    return {
        "schema_version": APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "graph_path_id": _stable_id("graph-path", applicability_run_id, candidate_id, "dead-end"),
        "query_timestamp": created_at,
        "graph_artifacts": [package_graph_identity, evidence_graph_identity],
        "graph_build_id": evidence_graph_identity.get("graph_build_id"),
        "graph_artifact_path": evidence_graph_identity.get("graph_artifact_path"),
        "graph_artifact_hash": evidence_graph_identity.get("graph_artifact_hash"),
        "start_node_id": f"candidate:{candidate_id}",
        "end_node_id": f"candidate:{candidate_id}",
        "traversed_node_ids": [f"candidate:{candidate_id}"],
        "relationship_types": [],
        "traversal_depth": 0,
        "max_depth": int((candidate.get("graph_expansion_contract") or {}).get("max_depth") or 0),
        "path_rationale": "No graph path found within the declared graph expansion contract.",
        "selected_status": "rejected",
        "rejection_reason": "graph_dead_end",
        "evidence_references": {
            "candidate_authority_id": candidate_id,
            "source_record_ids": _strings(candidate.get("source_record_ids")),
            "retrieval_trace_ids": [],
            "retrieval_result_ids": [],
        },
        "bounded_by_contract": {
            "allowed_relationship_types": _strings(
                (candidate.get("graph_expansion_contract") or {}).get("relationship_types")
            ),
            "max_depth": int((candidate.get("graph_expansion_contract") or {}).get("max_depth") or 0),
        },
    }


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


def _score_package_node(
    *,
    node: dict[str, Any],
    query_terms: list[str],
    required_types: set[str],
    package_filters: dict[str, Any],
) -> float:
    text = _package_node_text(node).lower()
    score = 0.0
    if node.get("node_type") in required_types:
        score += 2.0
    for term in query_terms:
        if term.lower() in text:
            score += 1.0
    section_families = set(_strings(package_filters.get("preferred_section_families")))
    if section_families and node.get("section_family") in section_families:
        score += 1.5
    filter_terms = (
        _strings(package_filters.get("package_section_terms"))
        + _strings(package_filters.get("package_terms"))
        + _strings(package_filters.get("package_evidence_terms"))
        + _strings(package_filters.get("resource_topics"))
        + _strings(package_filters.get("activity_tags"))
        + _strings(package_filters.get("geographic_area_ids"))
        + _strings(package_filters.get("management_area_ids"))
        + _strings(package_filters.get("overlay_ids"))
    )
    for term in filter_terms:
        if term.lower() in text:
            score += 1.0
    if node.get("node_type") == "package_section" and not query_terms and not filter_terms:
        score += 0.1
    return score


def _package_node_matches_candidate(node: dict[str, Any], candidate: dict[str, Any]) -> bool:
    if node.get("node_type") in set(_strings(candidate.get("required_package_fact_types"))):
        return True
    text = _package_node_text(node).lower()
    terms = (
        _strings(_package_filters(candidate).get("package_terms"))
        + _strings(_package_filters(candidate).get("package_section_terms"))
        + _strings(_package_filters(candidate).get("package_evidence_terms"))
        + _flatten_groups(candidate.get("positive_trigger_groups"))
        + _flatten_groups(candidate.get("negative_trigger_groups"))
    )
    return any(term.lower() in text for term in terms)


def _package_node_text(node: dict[str, Any]) -> str:
    values = [
        node.get("label"),
        node.get("raw_value"),
        node.get("normalized_value"),
        node.get("fact_subtype"),
        node.get("section_family"),
        node.get("context_excerpt"),
        node.get("matched_text"),
    ]
    return " ".join(str(value or "") for value in values)


def _source_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    filters = candidate.get("source_role_filters")
    if isinstance(filters, dict):
        return filters
    return {
        "source_record_ids": _strings(candidate.get("source_record_ids")),
        "document_roles": _strings([candidate.get("authority_document_role")]),
        "authority_categories": _strings([candidate.get("authority_category")]),
    }


def _package_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    filters = candidate.get("package_section_filters")
    return filters if isinstance(filters, dict) else {}


def _forest_plan_component_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    forest_plan = candidate.get("forest_plan")
    if not isinstance(forest_plan, dict):
        return {}
    return {
        "forest_unit_id": forest_plan.get("forest_unit_id"),
        "component_inventory_id": forest_plan.get("component_inventory_id"),
        "component_id": forest_plan.get("component_id"),
        "geographic_area_ids": forest_plan.get("geographic_area_ids") or [],
        "management_area_ids": forest_plan.get("management_area_ids") or [],
        "overlay_ids": forest_plan.get("overlay_ids") or [],
    }


def _currentness_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "requires_current_source": bool(
            (candidate.get("required_source_evidence") or {}).get("requires_source_record")
        ),
        "source_evidence_availability": candidate.get("source_evidence_availability") or {},
    }


def _candidate_fallback_query(candidate: dict[str, Any]) -> str:
    rule_template = candidate.get("rule_template")
    if isinstance(rule_template, dict):
        return " ".join(
            _strings(
                [
                    rule_template.get("title"),
                    rule_template.get("question"),
                    rule_template.get("requirement"),
                    rule_template.get("rule_id"),
                ]
            )
        )
    forest_plan = candidate.get("forest_plan")
    if isinstance(forest_plan, dict):
        return " ".join(
            _strings([forest_plan.get("section_heading"), forest_plan.get("component_id")])
        )
    return str(candidate.get("candidate_authority_id") or "")


def _citation_query(candidate: dict[str, Any]) -> str:
    for record in candidate.get("source_records") or []:
        if isinstance(record, dict):
            value = str(
                record.get("citation_label")
                or record.get("source_record_id")
                or record.get("title")
                or ""
            ).strip()
            if value:
                return value
    return _first(_strings(candidate.get("source_record_ids"))) or _candidate_fallback_query(candidate)


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
    return json.loads(row[0])


def _selected_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        result
        for row in rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "selected"
    ]


def _path_node_ids(path: list[str]) -> list[str]:
    return path[0::2]


def _path_relationship_types(path: list[str]) -> list[str]:
    return path[1::2]


def _path_rationale(path: list[str], nodes: dict[str, dict[str, Any]]) -> str:
    relationship_types = ", ".join(_path_relationship_types(path))
    end_node = nodes.get(path[-1], {})
    return (
        f"Bounded traversal followed {relationship_types or 'no relationships'} to "
        f"{end_node.get('node_type') or path[-1]}."
    )


def _path_evidence_references(path: list[str], nodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    refs: dict[str, set[str]] = {
        "authority_categories": set(),
        "source_record_ids": set(),
        "source_claim_ids": set(),
        "rule_claim_link_ids": set(),
        "forest_plan_component_ids": set(),
        "package_fact_node_ids": set(),
        "package_chunk_ids": set(),
        "evidence_span_ids": set(),
        "retrieval_result_ids": set(),
        "retrieval_trace_ids": set(),
    }
    for node_id in _path_node_ids(path):
        node = nodes.get(node_id, {})
        for key, ref_key in (
            ("source_record_id", "source_record_ids"),
            ("claim_id", "source_claim_ids"),
            ("link_id", "rule_claim_link_ids"),
            ("authority_category", "authority_categories"),
            ("component_id", "forest_plan_component_ids"),
            ("package_fact_node_id", "package_fact_node_ids"),
            ("package_chunk_id", "package_chunk_ids"),
            ("retrieval_result_id", "retrieval_result_ids"),
        ):
            if node.get(key):
                refs[ref_key].add(str(node[key]))
        for key, ref_key in (
            ("package_chunk_ids", "package_chunk_ids"),
            ("evidence_span_ids", "evidence_span_ids"),
            ("retrieval_trace_ids", "retrieval_trace_ids"),
        ):
            for value in _strings(node.get(key)):
                refs[ref_key].add(value)
    return {key: sorted(values) for key, values in refs.items()}


def _fusion_result_key(result: dict[str, Any]) -> str:
    return "|".join(
        [
            str(result.get("result_kind") or ""),
            str(result.get("source_chunk_id") or ""),
            str(result.get("package_fact_node_id") or ""),
            str(result.get("package_chunk_id") or ""),
            str(result.get("claim_id") or ""),
        ]
    )


def _section_family_from_hit(hit: dict[str, Any]) -> str | None:
    provenance = hit.get("provenance") or {}
    heading = str(provenance.get("heading") or "").lower()
    section = str(provenance.get("section") or "").lower()
    text = f"{section} {heading}"
    if "purpose" in text and "need" in text:
        return "purpose_need"
    if "alternative" in text:
        return "alternatives"
    if "consult" in text:
        return "consultation"
    if "decision" in text or "finding" in text:
        return "finding_decision"
    return section or heading or None


def _page_label(value: object) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _matched_terms(terms: list[str], text: str) -> list[str]:
    lower = str(text or "").lower()
    return sorted({term for term in terms if term.lower() in lower})


def _tokenize(text: str) -> list[str]:
    return [
        value.lower()
        for value in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}", text)
        if len(value) > 1
    ]


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


def _strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        return []
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for item in value:
            values.extend(_strings(item))
        return values
    text = str(value).strip()
    return [text] if text else []


def _flatten_groups(value: object) -> list[str]:
    return _strings(value)


def _first(values: list[str]) -> str | None:
    return values[0] if values else None


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    readable = re.sub(r"[^A-Za-z0-9_.-]+", "-", "-".join(parts[:2])).strip("-")
    readable = readable[:80].strip("-") or prefix
    return f"{prefix}:{readable}:{digest}"


def _validate_safe_segment(value: str, field_name: str) -> None:
    if not SAFE_SEGMENT_RE.fullmatch(str(value or "")):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
