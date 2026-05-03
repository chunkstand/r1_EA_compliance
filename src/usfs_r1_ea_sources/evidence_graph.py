from __future__ import annotations

from collections import Counter, defaultdict, deque
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import sqlite3

from .extract import _source_derived_dir
from .forest_plan_component_eval import FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
from .rule_claim_binding import default_rule_claim_links_dir


GRAPH_SCHEMA_VERSION = "document-evidence-graph-v1"
COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"
DEFAULT_SQLITE_FILENAME = "evidence_graph.sqlite"
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
FRESHNESS_CHECK_NAMES = {
    "retrieval_index_exists_and_readable",
    "chunk_source_set_ids_match",
    "chunk_content_hashes_match_text",
    "chunks_match_retrieval_index",
    "evidence_span_content_matches_chunks",
}
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


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


@dataclass(frozen=True)
class PhaseEvalResult:
    source_set_id: str
    graph_dir: Path
    output_path: Path
    summary: dict


def build_evidence_graph(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    allow_partial_retrieval: bool = False,
) -> EvidenceGraphBuildResult:
    """Build the v1 document evidence graph from extracted chunks and retrieval metadata."""

    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    graph_dir = source_derived_dir / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = source_derived_dir / "chunks" / "chunks.jsonl"
    catalog_sqlite_path = output_dir / "catalog" / "review_sources.sqlite"
    catalog_validation_path = output_dir / "catalog" / "catalog_validation.json"
    extraction_validation_path = source_derived_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = source_derived_dir / "diagnostics" / "summary.json"
    retrieval_validation_path = source_derived_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = source_derived_dir / "retrieval" / "summary.json"

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
        source_set_id=source_set_id,
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


def run_phase_aligned_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    review_id: str | None = None,
    review_dir: Path | None = None,
) -> PhaseEvalResult:
    """Evaluate capture, extraction, retrieval, graph, and optional compliance readiness."""

    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    graph_dir = source_derived_dir / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    output_path = graph_dir / "phase_eval_results.json"

    catalog_validation_path = output_dir / "catalog" / "catalog_validation.json"
    extraction_validation_path = source_derived_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = source_derived_dir / "diagnostics" / "summary.json"
    retrieval_validation_path = source_derived_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = source_derived_dir / "retrieval" / "summary.json"
    graph_validation_path = graph_dir / "evidence_graph_validation.json"
    graph_summary_path = graph_dir / "summary.json"
    claim_dir = source_derived_dir / "claims"
    claim_validation_path = claim_dir / "claim_validation.json"
    claim_summary_path = claim_dir / "summary.json"
    try:
        rule_claim_dir = default_rule_claim_links_dir(
            output_dir,
            source_set_id=source_set_id,
        )
    except (FileNotFoundError, ValueError):
        rule_claim_dir = source_derived_dir / "rule_claim_links"
    rule_claim_validation_path = rule_claim_dir / "rule_claim_link_validation.json"
    rule_claim_summary_path = rule_claim_dir / "summary.json"
    if not rule_claim_summary_path.exists():
        candidates = sorted((source_derived_dir / "rule_claim_links").glob("*/*/summary.json"))
        if candidates:
            rule_claim_summary_path = candidates[0]
            rule_claim_validation_path = rule_claim_summary_path.parent / "rule_claim_link_validation.json"
    if review_id and not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ValueError(
            "review_id must contain only letters, numbers, dot, underscore, or hyphen."
        )
    if review_dir is None and review_id:
        review_dir = output_dir / "reviews" / review_id
    if review_dir is not None:
        review_dir = Path(review_dir)
    compliance_validation_path = (
        review_dir / "compliance_validation.json" if review_dir is not None else None
    )
    compliance_review_path = review_dir / "compliance_review.json" if review_dir is not None else None
    compliance_matrix_path = review_dir / "compliance_matrix.json" if review_dir is not None else None
    compliance_matrix_pdf_path = (
        review_dir / "compliance_matrix.pdf" if review_dir is not None else None
    )
    component_adjudication_eval_path = (
        review_dir / "forest_plan_component_adjudication_eval.json"
        if review_dir is not None
        else None
    )
    component_eval_path = (
        review_dir / "forest_plan_component_eval_results.json"
        if review_dir is not None
        else None
    )
    component_adjudication_file_path = (
        review_dir / "forest_plan_component_adjudication.json"
        if review_dir is not None
        else None
    )

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
    graph_validation = _read_json(graph_validation_path) if graph_validation_path.exists() else None
    graph_summary = _read_json(graph_summary_path) if graph_summary_path.exists() else None
    claim_validation = _read_json(claim_validation_path) if claim_validation_path.exists() else None
    claim_summary = _read_json(claim_summary_path) if claim_summary_path.exists() else None
    compliance_validation = (
        _read_json(compliance_validation_path)
        if compliance_validation_path is not None and compliance_validation_path.exists()
        else None
    )
    compliance_review = (
        _read_json(compliance_review_path)
        if compliance_review_path is not None and compliance_review_path.exists()
        else None
    )
    compliance_matrix = (
        _read_json(compliance_matrix_path)
        if compliance_matrix_path is not None and compliance_matrix_path.exists()
        else None
    )
    component_adjudication_eval = (
        _read_json(component_adjudication_eval_path)
        if component_adjudication_eval_path is not None
        and component_adjudication_eval_path.exists()
        else None
    )
    component_eval = (
        _read_json(component_eval_path)
        if component_eval_path is not None and component_eval_path.exists()
        else None
    )
    compliance_summary_for_rule_claim = (compliance_review or {}).get("summary", {})
    if compliance_summary_for_rule_claim.get("rule_claim_summary_path"):
        candidate_summary_path = Path(str(compliance_summary_for_rule_claim["rule_claim_summary_path"]))
        if candidate_summary_path.exists():
            rule_claim_summary_path = candidate_summary_path
    if compliance_summary_for_rule_claim.get("rule_claim_validation_path"):
        candidate_validation_path = Path(
            str(compliance_summary_for_rule_claim["rule_claim_validation_path"])
        )
        if candidate_validation_path.exists():
            rule_claim_validation_path = candidate_validation_path
    rule_claim_validation = (
        _read_json(rule_claim_validation_path)
        if rule_claim_validation_path.exists()
        else None
    )
    rule_claim_summary = (
        _read_json(rule_claim_summary_path) if rule_claim_summary_path.exists() else None
    )
    compliance_coverage_path = rule_claim_summary_path.parent / "compliance_coverage_results.json"
    compliance_coverage = (
        _read_json(compliance_coverage_path) if compliance_coverage_path.exists() else None
    )
    compliance_gold_eval_path = (
        output_dir / "reviews" / "compliance_gold_eval" / "compliance_gold_eval_results.json"
    )
    compliance_gold_eval = (
        _read_json(compliance_gold_eval_path) if compliance_gold_eval_path.exists() else None
    )

    phases = [
        _phase(
            "catalog_capture",
            passed=bool(catalog_validation and catalog_validation.get("passed")),
            reviewer_ready=bool(catalog_validation and catalog_validation.get("passed")),
            details={"path": str(catalog_validation_path)},
        ),
        _phase(
            "extraction",
            passed=bool(extraction_validation and extraction_validation.get("passed"))
            and _extraction_summary_is_complete(extraction_summary),
            reviewer_ready=bool(extraction_validation and extraction_validation.get("passed"))
            and _extraction_summary_is_complete(extraction_summary),
            details={
                "validation_path": str(extraction_validation_path),
                "summary_path": str(extraction_summary_path),
                "validation_passed": bool(
                    extraction_validation and extraction_validation.get("passed")
                ),
                "extraction_complete": _extraction_summary_is_complete(extraction_summary),
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
            },
        ),
        _phase(
            "retrieval",
            passed=bool(retrieval_validation and retrieval_validation.get("passed")),
            reviewer_ready=bool(retrieval_summary and retrieval_summary.get("reviewer_ready")),
            details={
                "validation_path": str(retrieval_validation_path),
                "summary_path": str(retrieval_summary_path),
                "validation_passed": bool(
                    retrieval_validation and retrieval_validation.get("passed")
                ),
                "reviewer_ready": bool(
                    retrieval_summary and retrieval_summary.get("reviewer_ready")
                ),
            },
        ),
        _phase(
            "evidence_graph",
            passed=bool(graph_validation and graph_validation.get("passed")),
            reviewer_ready=bool(graph_summary and graph_summary.get("reviewer_ready")),
            details={
                "validation_path": str(graph_validation_path),
                "summary_path": str(graph_summary_path),
                "validation_passed": bool(graph_validation and graph_validation.get("passed")),
                "reviewer_ready": bool(graph_summary and graph_summary.get("reviewer_ready")),
                "failed_validation_checks": _failed_check_names(graph_validation),
                "freshness_status": _freshness_status(graph_validation),
                "retrieval_index_path": (graph_summary or {}).get("retrieval_index_path"),
                "retrieval_index_chunk_count": (graph_summary or {}).get(
                    "retrieval_index_chunk_count",
                    0,
                ),
                "retrieval_binding_mismatch_count": (graph_summary or {}).get(
                    "retrieval_binding_mismatch_count",
                    0,
                ),
                "metrics": (graph_summary or {}).get("metrics", {}),
            },
        ),
        _phase(
            "claim_extraction",
            passed=bool(claim_validation and claim_validation.get("passed")),
            reviewer_ready=bool(claim_summary and claim_summary.get("reviewer_ready")),
            details={
                "validation_path": str(claim_validation_path),
                "summary_path": str(claim_summary_path),
                "validation_passed": bool(claim_validation and claim_validation.get("passed")),
                "reviewer_ready": bool(claim_summary and claim_summary.get("reviewer_ready")),
                "failed_validation_checks": _failed_check_names(claim_validation),
                "claims_path": (claim_summary or {}).get("claims_path"),
                "entities_path": (claim_summary or {}).get("entities_path"),
                "claim_count": (claim_summary or {}).get("claim_count", 0),
                "entity_count": (claim_summary or {}).get("entity_count", 0),
                "claim_type_counts": (claim_summary or {}).get("claim_type_counts", {}),
                "retrieval_index_path": (claim_summary or {}).get("retrieval_index_path"),
                "retrieval_binding_mismatch_count": (claim_summary or {}).get(
                    "retrieval_binding_mismatch_count",
                    0,
                ),
                "metrics": (claim_summary or {}).get("metrics", {}),
            },
        ),
        _phase(
            "rule_claim_binding",
            passed=bool(rule_claim_validation and rule_claim_validation.get("passed")),
            reviewer_ready=bool(rule_claim_summary and rule_claim_summary.get("reviewer_ready")),
            details={
                "validation_path": str(rule_claim_validation_path),
                "summary_path": str(rule_claim_summary_path),
                "validation_passed": bool(
                    rule_claim_validation and rule_claim_validation.get("passed")
                ),
                "reviewer_ready": bool(
                    rule_claim_summary and rule_claim_summary.get("reviewer_ready")
                ),
                "failed_validation_checks": _failed_check_names(rule_claim_validation),
                "links_path": (rule_claim_summary or {}).get("links_path"),
                "gaps_path": (rule_claim_summary or {}).get("gaps_path"),
                "rule_pack_id": (rule_claim_summary or {}).get("rule_pack_id"),
                "rule_pack_version": (rule_claim_summary or {}).get("rule_pack_version"),
                "rule_count": (rule_claim_summary or {}).get("rule_count", 0),
                "link_count": (rule_claim_summary or {}).get("link_count", 0),
                "gap_count": (rule_claim_summary or {}).get("gap_count", 0),
                "rules_without_links": (rule_claim_summary or {}).get(
                    "rules_without_links",
                    [],
                ),
            },
        ),
    ]
    if compliance_coverage is not None:
        coverage_source_set_id = compliance_coverage.get("source_set_id")
        coverage_source_set_matches = coverage_source_set_id == source_set_id
        rule_claim_rule_pack_id = (rule_claim_summary or {}).get("rule_pack_id")
        rule_claim_rule_pack_version = (rule_claim_summary or {}).get("rule_pack_version")
        coverage_rule_pack_matches = (
            compliance_coverage.get("rule_pack_id") == rule_claim_rule_pack_id
            and compliance_coverage.get("rule_pack_version") == rule_claim_rule_pack_version
        )
        coverage_passed = bool(compliance_coverage.get("passed"))
        coverage_phase_passed = (
            coverage_passed and coverage_source_set_matches and coverage_rule_pack_matches
        )
        phases.append(
            _phase(
                "compliance_coverage",
                passed=coverage_phase_passed,
                reviewer_ready=bool(
                    coverage_phase_passed and compliance_coverage.get("reviewer_ready")
                ),
                details={
                    "coverage_path": str(compliance_coverage_path),
                    "coverage_passed": coverage_passed,
                    "coverage_reviewer_ready": bool(compliance_coverage.get("reviewer_ready")),
                    "expected_source_set_id": source_set_id,
                    "coverage_source_set_id": coverage_source_set_id,
                    "source_set_matches": coverage_source_set_matches,
                    "expected_rule_pack_id": rule_claim_rule_pack_id,
                    "expected_rule_pack_version": rule_claim_rule_pack_version,
                    "rule_pack_id": compliance_coverage.get("rule_pack_id"),
                    "rule_pack_version": compliance_coverage.get("rule_pack_version"),
                    "rule_pack_matches": coverage_rule_pack_matches,
                    "rule_count": compliance_coverage.get("rule_count", 0),
                    "coverage_item_count": compliance_coverage.get("coverage_item_count", 0),
                    "eval_case_count": compliance_coverage.get("eval_case_count", 0),
                    "rule_claim_link_count": compliance_coverage.get("rule_claim_link_count", 0),
                    "rules_without_coverage_items": compliance_coverage.get(
                        "rules_without_coverage_items",
                        [],
                    ),
                    "rules_without_eval_cases": compliance_coverage.get(
                        "rules_without_eval_cases",
                        [],
                    ),
                    "rules_without_source_claim_links": compliance_coverage.get(
                        "rules_without_source_claim_links",
                        [],
                    ),
                    "source_record_mismatch_rule_ids": compliance_coverage.get(
                        "source_record_mismatch_rule_ids",
                        [],
                    ),
                    "source_claim_term_mismatch_rule_ids": compliance_coverage.get(
                        "source_claim_term_mismatch_rule_ids",
                        [],
                    ),
                },
            )
        )
    if compliance_gold_eval is not None:
        gold_source_set_id = compliance_gold_eval.get("source_set_id")
        gold_source_set_matches = gold_source_set_id == source_set_id
        rule_claim_rule_pack_id = (rule_claim_summary or {}).get("rule_pack_id")
        rule_claim_rule_pack_version = (rule_claim_summary or {}).get("rule_pack_version")
        gold_rule_pack_matches = (
            compliance_gold_eval.get("rule_pack_id") == rule_claim_rule_pack_id
            and compliance_gold_eval.get("rule_pack_version") == rule_claim_rule_pack_version
        )
        gold_passed = bool(compliance_gold_eval.get("passed"))
        gold_promotion_ready = bool(compliance_gold_eval.get("promotion_ready"))
        gold_phase_passed = gold_passed and gold_source_set_matches and gold_rule_pack_matches
        gold_failed_checks = []
        if not gold_passed:
            gold_failed_checks.append("gold_eval_failed")
        if not gold_promotion_ready:
            gold_failed_checks.append("gold_eval_not_promotion_ready")
        if not gold_source_set_matches:
            gold_failed_checks.append("source_set_mismatch")
        if not gold_rule_pack_matches:
            gold_failed_checks.append("rule_pack_mismatch")
        phases.append(
            _phase(
                "compliance_gold_eval",
                passed=gold_phase_passed,
                reviewer_ready=bool(gold_phase_passed and gold_promotion_ready),
                details={
                    "gold_eval_path": str(compliance_gold_eval_path),
                    "gold_eval_id": compliance_gold_eval.get("gold_eval_id"),
                    "gold_eval_version": compliance_gold_eval.get("gold_eval_version"),
                    "gold_passed": gold_passed,
                    "promotion_ready": gold_promotion_ready,
                    "failed_checks": gold_failed_checks,
                    "expected_source_set_id": source_set_id,
                    "gold_source_set_id": gold_source_set_id,
                    "source_set_matches": gold_source_set_matches,
                    "expected_rule_pack_id": rule_claim_rule_pack_id,
                    "expected_rule_pack_version": rule_claim_rule_pack_version,
                    "rule_pack_id": compliance_gold_eval.get("rule_pack_id"),
                    "rule_pack_version": compliance_gold_eval.get("rule_pack_version"),
                    "rule_pack_matches": gold_rule_pack_matches,
                    "case_count": compliance_gold_eval.get("case_count", 0),
                    "adjudicated_case_count": compliance_gold_eval.get(
                        "adjudicated_case_count",
                        0,
                    ),
                    "passed_case_count": compliance_gold_eval.get("passed_case_count", 0),
                    "failed_case_count": compliance_gold_eval.get("failed_case_count", 0),
                    "profile_counts": compliance_gold_eval.get("profile_counts", {}),
                    "required_profiles_present": compliance_gold_eval.get(
                        "required_profiles_present",
                        [],
                    ),
                    "compliance_review_eval_path": compliance_gold_eval.get(
                        "compliance_review_eval_path"
                    ),
                },
            )
        )
    if review_dir is not None:
        compliance_summary = (compliance_review or {}).get("summary", {})
        compliance_source_set_id = compliance_summary.get("source_set_id")
        source_set_matches = compliance_source_set_id == source_set_id
        review_id_matches = review_id is None or compliance_summary.get("review_id") == review_id
        compliance_review_exists = compliance_review is not None
        compliance_validation_passed = bool(
            compliance_validation and compliance_validation.get("passed")
        )
        matrix_summary = (compliance_matrix or {}).get("summary", {})
        matrix_rule_pack = (compliance_matrix or {}).get("rule_pack", {})
        compliance_matrix_exists = compliance_matrix is not None
        compliance_matrix_pdf_exists = (
            compliance_matrix_pdf_path is not None and compliance_matrix_pdf_path.exists()
        )
        compliance_matrix_pdf_valid = (
            compliance_matrix_pdf_exists
            and compliance_matrix_pdf_path.stat().st_size > 0
            and compliance_matrix_pdf_path.read_bytes().startswith(b"%PDF-")
        )
        matrix_checks = {
            "matrix_exists": compliance_matrix_exists,
            "matrix_pdf_exists": compliance_matrix_pdf_exists,
            "matrix_pdf_header_valid": compliance_matrix_pdf_valid,
            "matrix_schema_matches": (compliance_matrix or {}).get("schema_version")
            == COMPLIANCE_MATRIX_SCHEMA_VERSION,
            "matrix_review_id_matches": (compliance_matrix or {}).get("review_id")
            == compliance_summary.get("review_id"),
            "matrix_source_set_matches": (compliance_matrix or {}).get("source_set_id")
            == compliance_source_set_id,
            "matrix_rule_pack_matches": matrix_rule_pack.get("rule_pack_id")
            == compliance_summary.get("rule_pack_id")
            and matrix_rule_pack.get("version") == compliance_summary.get("rule_pack_version"),
            "matrix_row_count_matches": matrix_summary.get("row_count")
            == compliance_summary.get("finding_count"),
            "matrix_status_counts_match": matrix_summary.get("status_counts")
            == compliance_summary.get("finding_status_counts"),
        }
        compliance_matrix_passed = all(matrix_checks.values())
        compliance_phase_passed = (
            compliance_review_exists
            and compliance_validation_passed
            and source_set_matches
            and review_id_matches
            and compliance_matrix_passed
        )
        phases.append(
            _phase(
                "compliance_review",
                passed=compliance_phase_passed,
                reviewer_ready=bool(
                    compliance_phase_passed
                    and compliance_summary.get("reviewer_ready")
                ),
                details={
                    "review_dir": str(review_dir),
                    "review_id": compliance_summary.get("review_id") or review_id,
                    "validation_path": str(compliance_validation_path),
                    "review_path": str(compliance_review_path),
                    "matrix_path": str(compliance_matrix_path),
                    "matrix_pdf_path": str(compliance_matrix_pdf_path),
                    "review_exists": compliance_review_exists,
                    "matrix_exists": compliance_matrix_exists,
                    "matrix_pdf_exists": compliance_matrix_pdf_exists,
                    "matrix_pdf_header_valid": compliance_matrix_pdf_valid,
                    "validation_passed": compliance_validation_passed,
                    "reviewer_ready": bool(compliance_summary.get("reviewer_ready")),
                    "expected_source_set_id": source_set_id,
                    "review_source_set_id": compliance_source_set_id,
                    "source_set_matches": source_set_matches,
                    "review_id_matches": review_id_matches,
                    "failed_validation_checks": _failed_check_names(compliance_validation),
                    "failed_artifact_checks": sorted(
                        name for name, passed in matrix_checks.items() if not passed
                    ),
                    **matrix_checks,
                    "rule_pack_id": compliance_summary.get("rule_pack_id"),
                    "rule_pack_version": compliance_summary.get("rule_pack_version"),
                    "finding_count": compliance_summary.get("finding_count", 0),
                    "finding_status_counts": compliance_summary.get(
                        "finding_status_counts",
                        {},
                    ),
                },
            )
        )
        if component_eval is not None:
            component_eval_summary = (
                component_eval.get("summary")
                if isinstance(component_eval, dict)
                and isinstance(component_eval.get("summary"), dict)
                else {}
            )
            component_eval_schema_version = (
                component_eval.get("schema_version")
                if isinstance(component_eval, dict)
                else None
            ) or component_eval_summary.get("schema_version")
            component_eval_review_id = component_eval_summary.get("review_id")
            component_eval_source_set_id = component_eval_summary.get("source_set_id")
            expected_component_eval_review_id = review_id or compliance_summary.get("review_id")
            component_eval_passed = bool(component_eval_summary.get("passed"))
            component_eval_schema_matches = (
                component_eval_schema_version == FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
            )
            component_eval_source_set_matches = component_eval_source_set_id == source_set_id
            component_eval_review_id_matches = (
                expected_component_eval_review_id is None
                or component_eval_review_id == expected_component_eval_review_id
            )
            component_eval_failed_checks = []
            if not component_eval_schema_matches:
                component_eval_failed_checks.append("schema_version_mismatch")
            if not component_eval_passed:
                component_eval_failed_checks.append("component_eval_failed")
            if not component_eval_source_set_matches:
                component_eval_failed_checks.append("source_set_mismatch")
            if not component_eval_review_id_matches:
                component_eval_failed_checks.append("review_id_mismatch")
            component_eval_phase_passed = (
                component_eval_schema_matches
                and component_eval_passed
                and component_eval_source_set_matches
                and component_eval_review_id_matches
            )
            phases.append(
                _phase(
                    "forest_plan_component_eval",
                    passed=component_eval_phase_passed,
                    reviewer_ready=component_eval_phase_passed,
                    details={
                        "review_dir": str(review_dir),
                        "eval_path": str(component_eval_path),
                        "schema_version": component_eval_schema_version,
                        "schema_version_matches": component_eval_schema_matches,
                        "eval_passed": component_eval_passed,
                        "failed_checks": component_eval_failed_checks,
                        "expected_source_set_id": source_set_id,
                        "component_eval_source_set_id": component_eval_source_set_id,
                        "source_set_matches": component_eval_source_set_matches,
                        "expected_review_id": expected_component_eval_review_id,
                        "component_eval_review_id": component_eval_review_id,
                        "review_id_matches": component_eval_review_id_matches,
                        "case_count": component_eval_summary.get("case_count", 0),
                        "passed_case_count": component_eval_summary.get("passed_case_count", 0),
                        "failed_case_count": component_eval_summary.get("failed_case_count", 0),
                        "metrics": component_eval_summary.get("metrics", {}),
                        "failure_category_counts": component_eval_summary.get(
                            "failure_category_counts",
                            {},
                        ),
                    },
                )
            )
        should_include_component_adjudication = bool(
            component_adjudication_eval_path is not None
            and component_adjudication_eval_path.exists()
        ) or bool(
            component_adjudication_file_path is not None
            and component_adjudication_file_path.exists()
        )
        if should_include_component_adjudication:
            adjudication_summary = (
                component_adjudication_eval.get("summary")
                if isinstance(component_adjudication_eval, dict)
                and isinstance(component_adjudication_eval.get("summary"), dict)
                else {}
            )
            adjudication_review_id = (
                component_adjudication_eval or {}
            ).get("review_id") or adjudication_summary.get("review_id")
            adjudication_source_set_id = (
                component_adjudication_eval or {}
            ).get("source_set_id") or adjudication_summary.get("source_set_id")
            expected_adjudication_review_id = review_id or compliance_summary.get("review_id")
            adjudication_eval_exists = component_adjudication_eval is not None
            adjudication_eval_passed = bool(adjudication_summary.get("passed"))
            adjudication_source_set_matches = adjudication_source_set_id == source_set_id
            adjudication_review_id_matches = (
                expected_adjudication_review_id is None
                or adjudication_review_id == expected_adjudication_review_id
            )
            adjudication_failed_checks = []
            if not adjudication_eval_exists:
                adjudication_failed_checks.append("adjudication_eval_missing")
            if adjudication_eval_exists and not adjudication_eval_passed:
                adjudication_failed_checks.append("adjudication_eval_failed")
            if adjudication_eval_exists and not adjudication_source_set_matches:
                adjudication_failed_checks.append("source_set_mismatch")
            if adjudication_eval_exists and not adjudication_review_id_matches:
                adjudication_failed_checks.append("review_id_mismatch")
            adjudication_phase_passed = (
                adjudication_eval_exists
                and adjudication_eval_passed
                and adjudication_source_set_matches
                and adjudication_review_id_matches
            )
            phases.append(
                _phase(
                    "forest_plan_component_adjudication",
                    passed=adjudication_phase_passed,
                    reviewer_ready=adjudication_phase_passed,
                    details={
                        "review_dir": str(review_dir),
                        "eval_path": str(component_adjudication_eval_path),
                        "adjudication_file": (
                            adjudication_summary.get("adjudication_file")
                            or str(component_adjudication_file_path)
                        ),
                        "eval_exists": adjudication_eval_exists,
                        "eval_passed": adjudication_eval_passed,
                        "failed_checks": adjudication_failed_checks,
                        "expected_source_set_id": source_set_id,
                        "adjudication_source_set_id": adjudication_source_set_id,
                        "source_set_matches": adjudication_source_set_matches,
                        "expected_review_id": expected_adjudication_review_id,
                        "adjudication_review_id": adjudication_review_id,
                        "review_id_matches": adjudication_review_id_matches,
                        "queue_item_count": adjudication_summary.get("queue_item_count", 0),
                        "adjudication_item_count": adjudication_summary.get(
                            "adjudication_item_count",
                            0,
                        ),
                        "resolved_adjudication_count": adjudication_summary.get(
                            "resolved_adjudication_count",
                            0,
                        ),
                        "pending_adjudication_count": adjudication_summary.get(
                            "pending_adjudication_count",
                            0,
                        ),
                        "adjudication_completion_rate": adjudication_summary.get(
                            "adjudication_completion_rate",
                            0,
                        ),
                        "adjudication_expectation_match_rate": adjudication_summary.get(
                            "adjudication_expectation_match_rate",
                            0,
                        ),
                        "disposition_counts": adjudication_summary.get(
                            "disposition_counts",
                            {},
                        ),
                        "failure_category_counts": adjudication_summary.get(
                            "failure_category_counts",
                            {},
                        ),
                    },
                )
            )
    blockers = [
        {"phase": phase["name"], "reason": reason}
        for phase in phases
        for reason in phase["failure_reasons"]
    ]
    summary = {
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "passed": all(phase["passed"] for phase in phases),
        "reviewer_ready": all(phase["reviewer_ready"] for phase in phases),
        "phase_count": len(phases),
        "passed_phase_count": sum(1 for phase in phases if phase["passed"]),
        "reviewer_ready_phase_count": sum(1 for phase in phases if phase["reviewer_ready"]),
        "blockers": blockers,
        "phases": phases,
    }
    _write_json(output_path, summary)
    return PhaseEvalResult(
        source_set_id=source_set_id,
        graph_dir=graph_dir,
        output_path=output_path,
        summary=summary,
    )


def default_graph_dir(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    return _source_derived_dir(output_dir / "derived", source_set_id) / "evidence_graph"


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
    source_set_id: str,
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
    strict_blockers = {"extraction_scope_is_complete", "retrieval_is_reviewer_ready"}
    passed = all(check["passed"] for check in checks)
    if allow_partial_retrieval:
        passed = all(
            check["passed"] or check["name"] in strict_blockers
            for check in checks
        )
    return {
        "source_set_id": source_set_id,
        "passed": passed,
        "checks": checks,
        "metrics": metrics,
    }


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


def _phase(name: str, *, passed: bool, reviewer_ready: bool, details: dict) -> dict:
    failure_reasons = []
    if not passed:
        failure_reasons.append("phase_validation_failed")
    if not reviewer_ready:
        failure_reasons.append("phase_not_reviewer_ready")
    return {
        "name": name,
        "passed": passed,
        "reviewer_ready": reviewer_ready,
        "failure_reasons": failure_reasons,
        "details": details,
    }


def _failed_check_names(validation: dict | None) -> list[str]:
    if not validation:
        return []
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _freshness_status(validation: dict | None) -> str:
    if not validation:
        return "missing"
    failed = set(_failed_check_names(validation))
    return "failed" if failed & FRESHNESS_CHECK_NAMES else "passed"


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
    merged_checks = [*validation["checks"], *checks]
    ignored = {"extraction_scope_is_complete", "retrieval_is_reviewer_ready"}
    passed = all(
        check["passed"] or (allow_partial_retrieval and check["name"] in ignored)
        for check in merged_checks
    )
    return {
        **validation,
        "passed": passed,
        "checks": merged_checks,
    }


def _extraction_summary_is_complete(extraction_summary: dict | None) -> bool:
    if not extraction_summary:
        return False
    catalog_count = _int_from_summary(extraction_summary, "catalog_source_count")
    selected_count = _int_from_summary(extraction_summary, "selected_source_count")
    extracted_count = _int_from_summary(extraction_summary, "extracted_count")
    failed_count = _int_from_summary(extraction_summary, "failed_count")
    required_count = (
        _int_from_summary(extraction_summary, "required_extraction_source_count")
        or catalog_count
    )
    selected_required_count = (
        _int_from_summary(extraction_summary, "selected_required_extraction_source_count")
        or selected_count
    )
    filters = extraction_summary.get("filters") or {}
    active_filters = [value for value in filters.values() if value not in (None, "", [])]
    return (
        catalog_count > 0
        and not active_filters
        and selected_count == catalog_count
        and selected_required_count == required_count
        and extracted_count == required_count
        and failed_count == 0
    )


def _int_from_summary(summary: dict | None, key: str) -> int:
    if not summary:
        return 0
    try:
        return int(summary.get(key) or 0)
    except (TypeError, ValueError):
        return 0


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


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    source_set_id = manifest.get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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
