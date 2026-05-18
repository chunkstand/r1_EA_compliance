from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .artifact_utils import _extraction_summary_is_complete
from .artifact_utils import _int_from_summary
from .artifact_utils import _dict
from .artifact_utils import _read_json
from .artifact_utils import _read_jsonl
from .artifact_utils import _safe_int
from .artifact_utils import _source_set_id_from_catalog
from .artifact_utils import _utc_now
from .artifact_utils import _write_json
from .catalog_surface import resolve_catalog_dir_for_source_set
from .draft_generation import MANIFEST_FILENAME as DRAFT_GENERATION_MANIFEST_FILENAME
from .draft_generation import PACKAGE_FILENAME as DRAFT_GENERATION_PACKAGE_FILENAME
from .draft_generation import VALIDATION_FILENAME as DRAFT_GENERATION_VALIDATION_FILENAME
from .draft_generation import _semantic_sha256_for_artifact
from .ea_consistency_decision_support import DEFAULT_CONFIG_PATH as DECISION_SUPPORT_CONFIG_PATH
from .ea_consistency_decision_support import (
    DEFAULT_EXPECTED_SUMMARY_PATH as DECISION_SUPPORT_EXPECTED_SUMMARY_PATH,
)
from .extract import _source_derived_dir
from .forest_plan_component_eval import FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
from .final_qa_certification import VALIDATION_FILENAME as FINAL_QA_VALIDATION_FILENAME
from .phase_eval_direct_eval import apply_source_set_phase_direct_eval_gate
from .phase_eval_direct_eval import build_evaluation_coverage_phase
from .phase_eval_direct_eval import resolve_phase_eval_direct_eval_coverage
from .phase_eval_optional_phases import _applicability_arbitration_summary
from .phase_eval_optional_phases import _applicability_phase_gates
from .phase_eval_optional_phases import _decision_support_phase
from .phase_eval_optional_phases import _final_qa_certification_phase
from .phase_eval_optional_phases import _gold_rule_pack_match_mode
from .phase_eval_optional_phases import _knowledge_graph_phase
from .phase_eval_optional_phases import _read_applicability_phase_artifacts
from .phase_eval_optional_phases import _review_packet_index_phase
from .phase_eval_support import _current_queue_item_count
from .phase_eval_support import _failed_check_names
from .phase_eval_support import _freshness_status
from .phase_eval_support import _phase
from .phase_eval_support import _sha256_file
from .replay_context import ReplayContextMismatchError
from .replay_context import load_replay_context
from .replay_context import tracked_replay_context_path
from .review_packet_index import VALIDATION_FILENAME as REVIEW_PACKET_VALIDATION_FILENAME
from .rule_claim_binding import default_rule_claim_links_dir
from .source_register import validate_source_register


DOWNSTREAM_DIRECT_EVAL_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "downstream_direct_eval_v1.json"
)
COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
KNOWLEDGE_GRAPH_FILE_PREFIX = "n" "epa_3d_graph"
KNOWLEDGE_GRAPH_SOURCE_SET_PHASE = "n" "epa_3d_source_set_graph"
KNOWLEDGE_GRAPH_REVIEW_PHASE = "n" "epa_3d_review_graph"
REPO_ROOT = Path(__file__).resolve().parents[2]
DRAFT_GENERATION_EVAL_FILENAME = "draft_generation_eval_results.json"


@dataclass(frozen=True)
class PhaseEvalResult:
    source_set_id: str
    graph_dir: Path
    output_path: Path
    review_output_path: Path | None
    summary: dict


def _should_include_decision_support_phase(
    *,
    review_id: str | None,
    decision_support_dir: Path | None,
) -> bool:
    if decision_support_dir is not None and decision_support_dir.exists():
        return True
    if not review_id:
        return False
    for path in (DECISION_SUPPORT_CONFIG_PATH, DECISION_SUPPORT_EXPECTED_SUMMARY_PATH):
        if not path.exists():
            continue
        try:
            payload = _read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if payload.get("review_id") == review_id:
            return True
    return False


def _should_include_final_qa_phase(final_qa_dir: Path) -> bool:
    return (final_qa_dir / FINAL_QA_VALIDATION_FILENAME).exists()


def _should_include_review_packet_index_phase(review_packet_index_dir: Path) -> bool:
    return (review_packet_index_dir / REVIEW_PACKET_VALIDATION_FILENAME).exists()


def _should_include_draft_generation_phase(
    *,
    review_id: str | None,
    draft_generation_dir: Path | None,
) -> bool:
    if draft_generation_dir is not None and draft_generation_dir.exists():
        return True
    if not review_id:
        return False
    config_path = REPO_ROOT / "config" / "draft_generation_v1.json"
    if not config_path.exists():
        return False
    try:
        payload = _read_json(config_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return payload.get("review_id") == review_id


def run_phase_aligned_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    catalog_dir: Path | None = None,
    review_id: str | None = None,
    review_dir: Path | None = None,
) -> PhaseEvalResult:
    """Evaluate capture, extraction, retrieval, graph, and optional compliance readiness."""

    output_dir = Path(output_dir)
    if review_id and not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ValueError(
            "review_id must contain only letters, numbers, dot, underscore, or hyphen."
        )
    if review_dir is None and review_id:
        review_dir = output_dir / "reviews" / review_id
    if review_dir is not None:
        review_dir = Path(review_dir)
    resolved_review_id = review_id or (review_dir.name if review_dir is not None else None)
    if resolved_review_id is not None:
        replay_context_path = tracked_replay_context_path(output_dir, resolved_review_id)
        if replay_context_path.exists():
            replay_context = load_replay_context(replay_context_path)
            if source_set_id is None:
                source_set_id = replay_context.source_set_id
            elif source_set_id != replay_context.source_set_id:
                raise ReplayContextMismatchError(
                    "source_set_id override does not match tracked replay context for "
                    f"{resolved_review_id}"
                )
            if catalog_dir is None:
                catalog_dir = replay_context.resolved_catalog_dir
            else:
                resolved_catalog_dir = Path(catalog_dir).resolve()
                if resolved_catalog_dir != replay_context.resolved_catalog_dir:
                    raise ReplayContextMismatchError(
                        "catalog_dir override does not match tracked replay context for "
                        f"{resolved_review_id}"
                    )
                catalog_dir = resolved_catalog_dir
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    source_derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    graph_dir = source_derived_dir / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    output_path = graph_dir / "phase_eval_results.json"
    catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_dir=catalog_dir,
    )

    catalog_validation_path = catalog_dir / "catalog_validation.json"
    catalog_source_path = catalog_dir / "source_catalog.jsonl"
    source_set_manifest_path = catalog_dir / "source_set_manifest.json"
    extraction_validation_path = source_derived_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = source_derived_dir / "diagnostics" / "summary.json"
    extraction_accuracy_path = (
        source_derived_dir / "diagnostics" / "extraction_accuracy_audit.json"
    )
    authority_currentness_path = (
        source_derived_dir / "authority_currentness" / "authority_currentness_report.json"
    )
    upstream_evaluation_path = (
        output_dir / "evaluations" / "upstream" / "upstream_evaluation_results.json"
    )
    downstream_direct_eval_manifest_path = DOWNSTREAM_DIRECT_EVAL_MANIFEST_PATH
    retrieval_eval_path = source_derived_dir / "retrieval" / "retrieval_eval_results.json"
    retrieval_validation_path = source_derived_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = source_derived_dir / "retrieval" / "summary.json"
    graph_validation_path = graph_dir / "evidence_graph_validation.json"
    graph_summary_path = graph_dir / "summary.json"
    knowledge_graph_dir = source_derived_dir / "knowledge_graph"
    knowledge_graph_validation_path = (
        knowledge_graph_dir / f"{KNOWLEDGE_GRAPH_FILE_PREFIX}_validation.json"
    )
    knowledge_graph_summary_path = (
        knowledge_graph_dir / f"{KNOWLEDGE_GRAPH_FILE_PREFIX}_summary.json"
    )
    authority_ontology_validation_path = (
        knowledge_graph_dir / "authority_ontology_validation_report.json"
    )
    authority_relationship_eval_path = (
        knowledge_graph_dir / "authority_relationship_eval_report.json"
    )
    citation_alias_eval_path = knowledge_graph_dir / "citation_alias_eval_report.json"
    graph_health_eval_path = knowledge_graph_dir / "graph_health_eval_report.json"
    graph_accuracy_eval_path = knowledge_graph_dir / "graph_accuracy_eval_report.json"
    proving_semantic_dir = source_derived_dir / "source_register_proving"
    claim_dir = source_derived_dir / "claims"
    claim_eval_path = claim_dir / "claim_eval_results.json"
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
    rule_claim_eval_path = rule_claim_dir / "rule_claim_link_eval_results.json"
    if not rule_claim_summary_path.exists():
        candidates = sorted((source_derived_dir / "rule_claim_links").glob("*/*/summary.json"))
        if candidates:
            rule_claim_summary_path = candidates[0]
            rule_claim_validation_path = rule_claim_summary_path.parent / "rule_claim_link_validation.json"
            rule_claim_eval_path = rule_claim_summary_path.parent / "rule_claim_link_eval_results.json"
    review_phase_output_path = (
        review_dir / "phase_eval_results.json" if review_dir is not None else None
    )
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
    component_queue_path = (
        review_dir / "forest_plan_reviewer_resolution_queue.json"
        if review_dir is not None
        else None
    )
    component_adjudication_file_path = (
        review_dir / "forest_plan_component_adjudication.json"
        if review_dir is not None
        else None
    )
    applicability_dir = review_dir / "applicability" if review_dir is not None else None
    authority_universe_path = (
        applicability_dir / "authority_universe_snapshot.json"
        if applicability_dir is not None
        else None
    )
    package_fact_graph_path = (
        applicability_dir / "package_fact_graph.json" if applicability_dir is not None else None
    )
    package_fact_graph_validation_path = (
        applicability_dir / "package_fact_graph_validation.json"
        if applicability_dir is not None
        else None
    )
    applicability_retrieval_trace_path = (
        applicability_dir / "applicability_retrieval_trace.jsonl"
        if applicability_dir is not None
        else None
    )
    applicability_graph_trace_path = (
        applicability_dir / "applicability_graph_trace.jsonl"
        if applicability_dir is not None
        else None
    )
    applicability_trace_diagnostics_path = (
        applicability_dir / "applicability_retrieval_graph_diagnostics.json"
        if applicability_dir is not None
        else None
    )
    applicability_decisions_path = (
        applicability_dir / "applicability_decisions.jsonl"
        if applicability_dir is not None
        else None
    )
    applicable_authorities_path = (
        applicability_dir / "applicable_authorities.json"
        if applicability_dir is not None
        else None
    )
    non_applicable_authorities_path = (
        applicability_dir / "non_applicable_authorities.json"
        if applicability_dir is not None
        else None
    )
    search_coverage_certificates_path = (
        applicability_dir / "search_coverage_certificates.json"
        if applicability_dir is not None
        else None
    )
    applicability_validation_path = (
        applicability_dir / "applicability_validation.json"
        if applicability_dir is not None
        else None
    )
    generated_rule_pack_path = (
        applicability_dir / "generated_rule_pack.json" if applicability_dir is not None else None
    )
    generated_rule_pack_validation_path = (
        applicability_dir / "generated_rule_pack_validation.json"
        if applicability_dir is not None
        else None
    )
    decision_support_dir = (
        review_dir / "decision_support" if review_dir is not None else None
    )
    draft_generation_dir = (
        review_dir / "draft_generation" if review_dir is not None else None
    )
    review_packet_index_dir = (
        review_dir / "review_packet_index" if review_dir is not None else None
    )
    final_qa_dir = review_dir / "final_qa" if review_dir is not None else None
    review_knowledge_graph_dir = (
        review_dir / "knowledge_graph" if review_dir is not None else None
    )
    review_knowledge_graph_validation_path = (
        review_knowledge_graph_dir / f"{KNOWLEDGE_GRAPH_FILE_PREFIX}_validation.json"
        if review_knowledge_graph_dir is not None
        else None
    )
    review_knowledge_graph_summary_path = (
        review_knowledge_graph_dir / f"{KNOWLEDGE_GRAPH_FILE_PREFIX}_summary.json"
        if review_knowledge_graph_dir is not None
        else None
    )

    catalog_validation = (
        _read_json(catalog_validation_path) if catalog_validation_path.exists() else None
    )
    catalog_rows = _read_jsonl(catalog_source_path) if catalog_source_path.exists() else []
    source_set_manifest = (
        _read_json(source_set_manifest_path) if source_set_manifest_path.exists() else None
    )
    extraction_validation = (
        _read_json(extraction_validation_path) if extraction_validation_path.exists() else None
    )
    extraction_summary = (
        _read_json(extraction_summary_path) if extraction_summary_path.exists() else None
    )
    extraction_accuracy = (
        _read_json(extraction_accuracy_path) if extraction_accuracy_path.exists() else None
    )
    authority_currentness_report = (
        _read_json(authority_currentness_path)
        if authority_currentness_path.exists()
        else None
    )
    upstream_evaluation = (
        _read_json(upstream_evaluation_path) if upstream_evaluation_path.exists() else None
    )
    retrieval_validation = (
        _read_json(retrieval_validation_path) if retrieval_validation_path.exists() else None
    )
    retrieval_summary = (
        _read_json(retrieval_summary_path) if retrieval_summary_path.exists() else None
    )
    graph_validation = _read_json(graph_validation_path) if graph_validation_path.exists() else None
    graph_summary = _read_json(graph_summary_path) if graph_summary_path.exists() else None
    knowledge_graph_validation = (
        _read_json(knowledge_graph_validation_path)
        if knowledge_graph_validation_path.exists()
        else None
    )
    knowledge_graph_summary = (
        _read_json(knowledge_graph_summary_path)
        if knowledge_graph_summary_path.exists()
        else None
    )
    authority_ontology_validation = (
        _read_json(authority_ontology_validation_path)
        if authority_ontology_validation_path.exists()
        else None
    )
    authority_relationship_eval = _load_semantic_report(
        primary_path=authority_relationship_eval_path,
        fallback_path=proving_semantic_dir / "authority_relationship_eval_report.json",
    )
    citation_alias_eval = _load_semantic_report(
        primary_path=citation_alias_eval_path,
        fallback_path=proving_semantic_dir / "citation_alias_eval_report.json",
    )
    graph_health_eval = _load_semantic_report(
        primary_path=graph_health_eval_path,
        fallback_path=proving_semantic_dir / "graph_health_eval_report.json",
    )
    graph_accuracy_eval = _load_semantic_report(
        primary_path=graph_accuracy_eval_path,
        fallback_path=proving_semantic_dir / "graph_accuracy_eval_report.json",
    )
    review_knowledge_graph_validation = (
        _read_json(review_knowledge_graph_validation_path)
        if review_knowledge_graph_validation_path is not None
        and review_knowledge_graph_validation_path.exists()
        else None
    )
    review_knowledge_graph_summary = (
        _read_json(review_knowledge_graph_summary_path)
        if review_knowledge_graph_summary_path is not None
        and review_knowledge_graph_summary_path.exists()
        else None
    )
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
    component_queue = (
        _read_json(component_queue_path)
        if component_queue_path is not None and component_queue_path.exists()
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
    downstream_direct_eval_manifest = (
        _read_json(downstream_direct_eval_manifest_path)
        if downstream_direct_eval_manifest_path.exists()
        else None
    )
    retrieval_eval = _read_json(retrieval_eval_path) if retrieval_eval_path.exists() else None
    claim_eval = _read_json(claim_eval_path) if claim_eval_path.exists() else None
    rule_claim_eval = _read_json(rule_claim_eval_path) if rule_claim_eval_path.exists() else None
    compliance_review_eval_path = (
        output_dir / "reviews" / "compliance_review_eval" / "compliance_review_eval_results.json"
    )
    compliance_review_eval = (
        _read_json(compliance_review_eval_path) if compliance_review_eval_path.exists() else None
    )
    review_scoped_compliance_gold_eval_path = (
        review_dir / "compliance_gold_eval_results.json" if review_dir is not None else None
    )
    default_compliance_gold_eval_path = (
        output_dir / "reviews" / "compliance_gold_eval" / "compliance_gold_eval_results.json"
    )
    has_review_scoped_compliance_gold_eval = (
        review_scoped_compliance_gold_eval_path is not None
        and review_scoped_compliance_gold_eval_path.exists()
    )
    compliance_gold_eval_path = default_compliance_gold_eval_path
    if has_review_scoped_compliance_gold_eval:
        compliance_gold_eval_path = review_scoped_compliance_gold_eval_path
    compliance_gold_eval = (
        _read_json(compliance_gold_eval_path) if compliance_gold_eval_path.exists() else None
    )
    if compliance_gold_eval is not None and review_id is None:
        gold_source_set_id = str(compliance_gold_eval.get("source_set_id") or "")
        if gold_source_set_id and gold_source_set_id != source_set_id:
            compliance_gold_eval = None
    if compliance_gold_eval is not None and review_id is not None:
        gold_source_set_id = str(compliance_gold_eval.get("source_set_id") or "")
        if (
            not has_review_scoped_compliance_gold_eval
            and gold_source_set_id
            and gold_source_set_id != source_set_id
        ):
            compliance_gold_eval = None
    applicability_artifacts = _read_applicability_phase_artifacts(
        authority_universe_path=authority_universe_path,
        package_fact_graph_path=package_fact_graph_path,
        package_fact_graph_validation_path=package_fact_graph_validation_path,
        applicability_retrieval_trace_path=applicability_retrieval_trace_path,
        applicability_graph_trace_path=applicability_graph_trace_path,
        applicability_trace_diagnostics_path=applicability_trace_diagnostics_path,
        applicability_decisions_path=applicability_decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
        applicability_validation_path=applicability_validation_path,
        generated_rule_pack_path=generated_rule_pack_path,
        generated_rule_pack_validation_path=generated_rule_pack_validation_path,
    )
    applicability_arbitration_summary = _applicability_arbitration_summary(
        applicability_artifacts.get("decisions") or []
    )
    direct_eval_coverage = resolve_phase_eval_direct_eval_coverage(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=resolved_review_id,
        review_dir=review_dir,
    )
    component_retrieval_direct_eval = direct_eval_coverage["source_set_phase_statuses"].get(
        "forest_plan_component_retrieval"
    )
    canonical_register_phase = _source_register_contract_phase(
        source_set_id=source_set_id,
        source_set_manifest=source_set_manifest,
        catalog_rows=catalog_rows,
        authority_currentness_report=authority_currentness_report,
    )
    authority_currentness_phase = _authority_currentness_phase(
        source_set_id=source_set_id,
        report=authority_currentness_report,
        report_path=authority_currentness_path,
    )
    extraction_accuracy_phase = _extraction_accuracy_phase(
        source_set_id=source_set_id,
        report=extraction_accuracy,
        report_path=extraction_accuracy_path,
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
        _upstream_evaluation_phase(
            upstream_evaluation=upstream_evaluation,
            upstream_evaluation_path=upstream_evaluation_path,
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
        _downstream_direct_evaluation_phase(
            manifest=downstream_direct_eval_manifest,
            manifest_path=downstream_direct_eval_manifest_path,
            output_dir=output_dir,
            source_set_id=source_set_id,
            lane_results={
                "retrieval_eval": {
                    "result": retrieval_eval,
                    "result_path": retrieval_eval_path,
                },
                "claim_eval": {
                    "result": claim_eval,
                    "result_path": claim_eval_path,
                },
                "rule_claim_eval": {
                    "result": rule_claim_eval,
                    "result_path": rule_claim_eval_path,
                },
                "compliance_review_eval": {
                    "result": compliance_review_eval,
                    "result_path": compliance_review_eval_path,
                },
            },
        ),
    ]
    if canonical_register_phase is not None:
        phases.append(canonical_register_phase)
    if authority_currentness_phase is not None:
        phases.append(authority_currentness_phase)
    if extraction_accuracy_phase is not None:
        phases.append(extraction_accuracy_phase)
    if knowledge_graph_validation is not None or knowledge_graph_summary is not None:
        phases.append(
            _knowledge_graph_phase(
                KNOWLEDGE_GRAPH_SOURCE_SET_PHASE,
                validation=knowledge_graph_validation,
                summary=knowledge_graph_summary,
                validation_path=knowledge_graph_validation_path,
                summary_path=knowledge_graph_summary_path,
                expected_source_set_id=source_set_id,
            )
        )
    if _catalog_uses_source_register_v1(catalog_rows, source_set_id):
        phases.extend(
            [
                _semantic_graph_eval_phase(
                    "authority_ontology",
                    report=authority_ontology_validation,
                    report_path=authority_ontology_validation_path,
                    expected_source_set_id=source_set_id,
                ),
                _semantic_graph_eval_phase(
                    "authority_relationships",
                    report=authority_relationship_eval,
                    report_path=authority_relationship_eval_path,
                    expected_source_set_id=source_set_id,
                ),
                _semantic_graph_eval_phase(
                    "citation_aliases",
                    report=citation_alias_eval,
                    report_path=citation_alias_eval_path,
                    expected_source_set_id=source_set_id,
                ),
                _semantic_graph_eval_phase(
                    "graph_health",
                    report=graph_health_eval,
                    report_path=graph_health_eval_path,
                    expected_source_set_id=source_set_id,
                ),
                _semantic_graph_eval_phase(
                    "graph_accuracy",
                    report=graph_accuracy_eval,
                    report_path=graph_accuracy_eval_path,
                    expected_source_set_id=source_set_id,
                ),
            ]
        )
    if component_retrieval_direct_eval is not None:
        phases.append(
            _phase(
                "forest_plan_component_retrieval",
                passed=True,
                reviewer_ready=True,
                details={
                    "results_path": component_retrieval_direct_eval.get("summary_path"),
                    "expected_source_set_id": source_set_id,
                    "required_source_set_ids": (
                        component_retrieval_direct_eval.get("details", {}).get(
                            "required_source_set_ids",
                            [],
                        )
                    ),
                },
            )
        )
    if review_dir is not None:
        phases.extend(
            _applicability_phase_gates(
                review_dir=review_dir,
                source_set_id=source_set_id,
                artifacts=applicability_artifacts,
                arbitration_summary=applicability_arbitration_summary,
            )
        )
        if (
            review_knowledge_graph_validation is not None
            or review_knowledge_graph_summary is not None
        ):
            phases.append(
                _knowledge_graph_phase(
                    KNOWLEDGE_GRAPH_REVIEW_PHASE,
                    validation=review_knowledge_graph_validation,
                    summary=review_knowledge_graph_summary,
                    validation_path=review_knowledge_graph_validation_path,
                    summary_path=review_knowledge_graph_summary_path,
                    expected_source_set_id=source_set_id,
                    expected_review_id=review_id,
                )
            )
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
        generated_rule_pack = applicability_artifacts.get("generated_rule_pack") or {}
        gold_rule_pack_match_mode = _gold_rule_pack_match_mode(
            gold_eval=compliance_gold_eval,
            expected_rule_pack_id=rule_claim_rule_pack_id,
            expected_rule_pack_version=rule_claim_rule_pack_version,
            generated_rule_pack=generated_rule_pack,
        )
        gold_rule_pack_matches = bool(gold_rule_pack_match_mode)
        gold_passed = bool(compliance_gold_eval.get("passed"))
        gold_promotion_ready = bool(compliance_gold_eval.get("promotion_ready"))
        gold_effective_promotion_ready = gold_promotion_ready or (
            gold_rule_pack_match_mode == "generated_base" and gold_passed
        )
        gold_phase_passed = gold_passed and gold_source_set_matches and gold_rule_pack_matches
        gold_failed_checks = []
        if not gold_passed:
            gold_failed_checks.append("gold_eval_failed")
        if not gold_effective_promotion_ready:
            gold_failed_checks.append("gold_eval_not_promotion_ready")
        if not gold_source_set_matches:
            gold_failed_checks.append("source_set_mismatch")
        if not gold_rule_pack_matches:
            gold_failed_checks.append("rule_pack_mismatch")
        phases.append(
            _phase(
                "compliance_gold_eval",
                passed=gold_phase_passed,
                reviewer_ready=bool(gold_phase_passed and gold_effective_promotion_ready),
                details={
                    "gold_eval_path": str(compliance_gold_eval_path),
                    "gold_eval_id": compliance_gold_eval.get("gold_eval_id"),
                    "gold_eval_version": compliance_gold_eval.get("gold_eval_version"),
                    "gold_passed": gold_passed,
                    "promotion_ready": gold_promotion_ready,
                    "effective_promotion_ready": gold_effective_promotion_ready,
                    "failed_checks": gold_failed_checks,
                    "expected_source_set_id": source_set_id,
                    "gold_source_set_id": gold_source_set_id,
                    "source_set_matches": gold_source_set_matches,
                    "expected_rule_pack_id": rule_claim_rule_pack_id,
                    "expected_rule_pack_version": rule_claim_rule_pack_version,
                    "rule_pack_id": compliance_gold_eval.get("rule_pack_id"),
                    "rule_pack_version": compliance_gold_eval.get("rule_pack_version"),
                    "rule_pack_matches": gold_rule_pack_matches,
                    "rule_pack_match_mode": gold_rule_pack_match_mode,
                    "generated_base_rule_pack_id": generated_rule_pack.get(
                        "base_rule_pack_id"
                    ),
                    "generated_base_rule_pack_version": generated_rule_pack.get(
                        "base_rule_pack_version"
                    ),
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
        matrix_forest_plan = (compliance_matrix or {}).get("forest_plan_compliance") or {}
        matrix_forest_plan_summary = matrix_forest_plan.get("summary", {})
        forest_plan_summary = (
            matrix_summary.get("forest_plan_review")
            or compliance_summary.get("forest_plan_review")
            or {}
        )
        forest_plan_component_evaluation = (
            forest_plan_summary.get("component_evaluation") or {}
        )
        forest_plan_matrix_required = bool(
            forest_plan_summary.get("scope_status") == "custer_gallatin"
            and (
                forest_plan_summary.get("reviewer_ready")
                or forest_plan_component_evaluation.get("reviewer_ready")
            )
        )
        forest_plan_matrix_exists = bool(matrix_forest_plan)
        forest_plan_matrix_schema_matches = (
            not forest_plan_matrix_required
            or matrix_forest_plan.get("schema_version") == "forest-plan-compliance-matrix-v0"
        )
        forest_plan_matrix_rows_visible = (
            not forest_plan_matrix_required
            or int(matrix_forest_plan_summary.get("row_count") or 0) > 0
        )
        expected_standard_count = int(
            forest_plan_component_evaluation.get("applicable_standard_count") or 0
        )
        forest_plan_matrix_standards_visible = (
            not forest_plan_matrix_required
            or expected_standard_count == 0
            or int(matrix_forest_plan_summary.get("applicable_standard_row_count") or 0)
            >= expected_standard_count
        )
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
            "forest_plan_matrix_schema_matches": forest_plan_matrix_schema_matches,
            "forest_plan_matrix_rows_visible": forest_plan_matrix_rows_visible,
            "forest_plan_matrix_standards_visible": forest_plan_matrix_standards_visible,
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
                    "forest_plan_matrix_required": forest_plan_matrix_required,
                    "forest_plan_matrix_exists": forest_plan_matrix_exists,
                    "forest_plan_matrix_row_count": matrix_forest_plan_summary.get(
                        "row_count",
                        0,
                    ),
                    "forest_plan_matrix_applicable_standard_row_count": (
                        matrix_forest_plan_summary.get("applicable_standard_row_count", 0)
                    ),
                    "forest_plan_expected_applicable_standard_count": expected_standard_count,
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
            current_queue_count = (
                _current_queue_item_count(component_queue) if component_queue is not None else None
            )
            adjudication_queue_count = _safe_int(
                adjudication_summary.get("queue_item_count"),
            )
            adjudication_queue_matches_current = (
                current_queue_count is None or adjudication_queue_count == current_queue_count
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
            if adjudication_eval_exists and not adjudication_queue_matches_current:
                adjudication_failed_checks.append("queue_item_count_mismatch")
            adjudication_phase_passed = (
                adjudication_eval_exists
                and adjudication_eval_passed
                and adjudication_source_set_matches
                and adjudication_review_id_matches
                and adjudication_queue_matches_current
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
                        "current_queue_item_count": current_queue_count,
                        "queue_item_count_matches_current": (
                            adjudication_queue_matches_current
                        ),
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
                        "real_ea_omission_count": adjudication_summary.get(
                            "real_ea_omission_count",
                            0,
                        ),
                        "system_miss_count": adjudication_summary.get(
                            "system_miss_count",
                            0,
                        ),
                        "adjudication_completion_rate": adjudication_summary.get(
                            "adjudication_completion_rate",
                            0,
                        ),
                        "real_ea_omission_rate": adjudication_summary.get(
                            "real_ea_omission_rate",
                            0,
                        ),
                        "system_miss_rate": adjudication_summary.get(
                            "system_miss_rate",
                            0,
                        ),
                        "adjudication_expectation_match_rate": adjudication_summary.get(
                            "adjudication_expectation_match_rate",
                            0,
                        ),
                        "adjudication_outcome_counts": adjudication_summary.get(
                            "adjudication_outcome_counts",
                            {},
                        ),
                        "disposition_counts": adjudication_summary.get(
                            "disposition_counts",
                            {},
                        ),
                        "real_ea_omission_disposition_counts": adjudication_summary.get(
                            "real_ea_omission_disposition_counts",
                            {},
                        ),
                        "system_miss_disposition_counts": adjudication_summary.get(
                            "system_miss_disposition_counts",
                            {},
                        ),
                        "failure_category_counts": adjudication_summary.get(
                            "failure_category_counts",
                            {},
                        ),
                    },
                )
            )
    if review_dir is not None and _should_include_decision_support_phase(
        review_id=review_id or review_dir.name,
        decision_support_dir=decision_support_dir,
    ):
        phases.append(
            _decision_support_phase(
                output_dir=output_dir,
                review_id=review_id or review_dir.name,
                decision_support_dir=decision_support_dir,
            )
        )
    if review_dir is not None and _should_include_draft_generation_phase(
        review_id=review_id or review_dir.name,
        draft_generation_dir=draft_generation_dir,
    ):
        phases.append(
            _draft_generation_phase(
                review_id=review_id or review_dir.name,
                source_set_id=source_set_id,
                draft_generation_dir=draft_generation_dir or review_dir / "draft_generation",
            )
        )
    if review_packet_index_dir is not None and _should_include_review_packet_index_phase(
        review_packet_index_dir
    ):
        phases.append(
            _review_packet_index_phase(
                review_id=review_id or review_dir.name,
                source_set_id=source_set_id,
                review_dir=review_dir,
                review_packet_index_dir=review_packet_index_dir,
            )
        )
    if final_qa_dir is not None and _should_include_final_qa_phase(final_qa_dir):
        phases.append(
            _final_qa_certification_phase(
                output_dir=output_dir,
                review_id=review_id or review_dir.name,
                source_set_id=source_set_id,
                final_qa_dir=final_qa_dir,
            )
        )
    phases = [
        apply_source_set_phase_direct_eval_gate(
            phase,
            direct_eval_status=direct_eval_coverage["source_set_phase_statuses"].get(
                phase["name"]
            ),
        )
        for phase in phases
    ]
    evaluation_coverage_phase, evaluation_coverage_summary = build_evaluation_coverage_phase(
        phases=phases,
        contract_id=direct_eval_coverage["contract_id"],
        contract_version=direct_eval_coverage["contract_version"],
        contract_path=direct_eval_coverage["contract_path"],
        review_scope=direct_eval_coverage.get("review_scope"),
    )
    phases.append(evaluation_coverage_phase)
    blockers = [
        {"phase": phase["name"], "reason": reason}
        for phase in phases
        for reason in phase["failure_reasons"]
    ]
    summary = {
        "source_set_id": source_set_id,
        "review_id": resolved_review_id,
        "review_dir": str(review_dir) if review_dir is not None else None,
        "created_at": _utc_now(),
        "catalog_dir": str(catalog_dir),
        "passed": all(phase["passed"] for phase in phases),
        "reviewer_ready": all(phase["reviewer_ready"] for phase in phases),
        "phase_count": len(phases),
        "passed_phase_count": sum(1 for phase in phases if phase["passed"]),
        "reviewer_ready_phase_count": sum(1 for phase in phases if phase["reviewer_ready"]),
        "applicability_arbitration_summary": applicability_arbitration_summary
        if review_dir is not None
        else {},
        "blockers": blockers,
        "phases": phases,
        **evaluation_coverage_summary,
    }
    _write_json(output_path, summary)
    if review_phase_output_path is not None:
        _write_json(review_phase_output_path, summary)
    return PhaseEvalResult(
        source_set_id=source_set_id,
        graph_dir=graph_dir,
        output_path=output_path,
        review_output_path=review_phase_output_path,
        summary=summary,
    )


def default_graph_dir(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    return _source_derived_dir(output_dir / "derived", source_set_id) / "evidence_graph"


def _catalog_uses_source_register_v1(catalog_rows: list[dict], source_set_id: str) -> bool:
    return any(
        str(row.get("source_set_id") or source_set_id) == source_set_id
        and str((row.get("metadata") or {}).get("loader_contract") or "") == "source_register_v1"
        for row in catalog_rows
        if isinstance(row, dict)
    )


def _resolve_repo_relative_path(value: str | None) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _is_canonical_source_register_context(
    *,
    source_set_manifest: dict | None,
    catalog_rows: list[dict],
    authority_currentness_report: dict | None,
    source_set_id: str,
) -> bool:
    if _catalog_uses_source_register_v1(catalog_rows, source_set_id):
        return True
    summary = _dict((authority_currentness_report or {}).get("summary"))
    inventory_summary = _dict(summary.get("inventory_summary"))
    if inventory_summary.get("projection_basis") == "source_register_v1_catalog_and_queue_rows":
        return True
    workbook_path = str((source_set_manifest or {}).get("workbook_path") or "")
    return workbook_path.endswith("usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx")


def _source_register_contract_phase(
    *,
    source_set_id: str,
    source_set_manifest: dict | None,
    catalog_rows: list[dict],
    authority_currentness_report: dict | None,
) -> dict | None:
    if not _is_canonical_source_register_context(
        source_set_manifest=source_set_manifest,
        catalog_rows=catalog_rows,
        authority_currentness_report=authority_currentness_report,
        source_set_id=source_set_id,
    ):
        return None
    summary = _dict((authority_currentness_report or {}).get("summary"))
    inventory_summary = _dict(summary.get("inventory_summary"))
    workbook_path = _resolve_repo_relative_path(
        str((source_set_manifest or {}).get("workbook_path") or "")
        or str(inventory_summary.get("workbook_path") or "")
    )
    workbook_path_exists = workbook_path is not None and workbook_path.exists()
    validation_report: dict | None = None
    validation_error: str | None = None
    if workbook_path_exists and workbook_path is not None:
        try:
            validation_report = validate_source_register(workbook_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            validation_error = str(exc)
    manifest_workbook_sha256 = str((source_set_manifest or {}).get("workbook_sha256") or "")
    actual_workbook_sha256 = (
        _sha256_file(workbook_path) if workbook_path_exists and workbook_path is not None else None
    )
    workbook_sha_matches_manifest = (
        not manifest_workbook_sha256 or actual_workbook_sha256 == manifest_workbook_sha256
    )
    validation_passed = bool(validation_report and validation_report.get("validation_passed"))
    failed_checks = [
        check["name"]
        for check in (validation_report or {}).get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]
    passed = bool(
        workbook_path_exists
        and validation_passed
        and workbook_sha_matches_manifest
        and (validation_report or {}).get("load_sheet_name") == "Document_Register_Master"
    )
    return _phase(
        "source_register_contract",
        passed=passed,
        reviewer_ready=passed,
        details={
            "workbook_path": str(workbook_path) if workbook_path is not None else None,
            "workbook_path_exists": workbook_path_exists,
            "manifest_workbook_sha256": manifest_workbook_sha256 or None,
            "actual_workbook_sha256": actual_workbook_sha256,
            "workbook_sha_matches_manifest": workbook_sha_matches_manifest,
            "validation_passed": validation_passed,
            "validation_error": validation_error,
            "failed_checks": failed_checks,
            "sheet_count": (validation_report or {}).get("sheet_count"),
            "load_sheet_name": (validation_report or {}).get("load_sheet_name"),
            "load_row_count": (validation_report or {}).get("load_row_count"),
            "queue_row_count": (validation_report or {}).get("queue_row_count"),
            "removed_row_count": (validation_report or {}).get("removed_row_count"),
        },
    )


def _authority_currentness_phase(
    *,
    source_set_id: str,
    report: dict | None,
    report_path: Path,
) -> dict | None:
    if report is None:
        return None
    summary = _dict(report.get("summary"))
    validation = _dict(report.get("validation"))
    summary_source_set_id = str(summary.get("source_set_id") or report.get("source_set_id") or "")
    source_set_matches = summary_source_set_id == source_set_id
    validation_passed = bool(validation.get("passed"))
    summary_validation_passed = bool(summary.get("validation_passed"))
    failed_checks = [
        check["name"]
        for check in validation.get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]
    passed = bool(source_set_matches and validation_passed and summary_validation_passed)
    return _phase(
        "authority_currentness",
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "report_present": True,
            "expected_source_set_id": source_set_id,
            "summary_source_set_id": summary_source_set_id,
            "source_set_matches": source_set_matches,
            "validation_passed": validation_passed,
            "summary_validation_passed": summary_validation_passed,
            "failed_checks": failed_checks,
            "authority_family_count": summary.get("authority_family_count", 0),
            "current_authority_source_record_count": summary.get(
                "current_authority_source_record_count",
                0,
            ),
            "documented_source_gap_count": summary.get("documented_source_gap_count", 0),
            "documented_source_non_addition_count": summary.get(
                "documented_source_non_addition_count",
                0,
            ),
            "superseded_replacement_confirmed_family_count": summary.get(
                "superseded_replacement_confirmed_family_count",
                0,
            ),
            "temporal_lineage_record_count": summary.get("temporal_lineage_record_count", 0),
        },
    )


def _extraction_accuracy_phase(
    *,
    source_set_id: str,
    report: dict | None,
    report_path: Path,
) -> dict | None:
    if report is None:
        return None
    report_source_set_id = str(report.get("source_set_id") or "")
    source_set_matches = report_source_set_id == source_set_id
    passed = bool(source_set_matches and report.get("passed") is True)
    return _phase(
        "extraction_accuracy",
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "report_present": True,
            "expected_source_set_id": source_set_id,
            "report_source_set_id": report_source_set_id,
            "source_set_matches": source_set_matches,
            "passed": bool(report.get("passed")),
            "record_count": report.get("record_count", 0),
            "audited_record_count": report.get("audited_record_count", 0),
            "audited_chunk_count": report.get("audited_chunk_count", 0),
            "knowledge_base_admitted_source_record_count": len(
                report.get("knowledge_base_admitted_source_record_ids") or []
            ),
            "knowledge_base_blocked_source_record_count": len(
                report.get("knowledge_base_blocked_source_record_ids") or []
            ),
            "failed_checks": _failed_check_names(report),
        },
    )


def _load_semantic_report(*, primary_path: Path, fallback_path: Path) -> dict | None:
    if primary_path.exists():
        return _read_json(primary_path)
    if fallback_path.exists():
        return _read_json(fallback_path)
    return None


def _semantic_graph_eval_phase(
    name: str,
    *,
    report: dict | None,
    report_path: Path,
    expected_source_set_id: str,
) -> dict:
    report_present = isinstance(report, dict)
    report_source_set_id = (report or {}).get("source_set_id")
    source_set_matches = report_source_set_id == expected_source_set_id
    report_passed = bool((report or {}).get("summary", {}).get("passed"))
    failed_checks = _failed_check_names(report)
    passed = report_present and source_set_matches and report_passed and not failed_checks
    return _phase(
        name,
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "report_present": report_present,
            "expected_source_set_id": expected_source_set_id,
            "source_set_id": report_source_set_id,
            "source_set_matches": source_set_matches,
            "report_passed": report_passed,
            "failed_checks": failed_checks,
        },
    )



def _downstream_direct_evaluation_phase(
    *,
    manifest: dict | None,
    manifest_path: Path,
    output_dir: Path,
    source_set_id: str,
    lane_results: dict[str, dict[str, object]],
) -> dict:
    required_lanes = manifest.get("required_lanes", []) if isinstance(manifest, dict) else []
    manifest_ok = (
        isinstance(manifest, dict)
        and manifest.get("schema_version") == "downstream-direct-eval-v1"
        and isinstance(required_lanes, list)
        and bool(required_lanes)
    )
    lane_summaries = [
        _downstream_lane_summary(
            lane=lane,
            manifest_path=manifest_path,
            output_dir=output_dir,
            source_set_id=source_set_id,
            lane_result=lane_results.get(str(lane.get("lane_id") or ""), {}),
        )
        for lane in required_lanes
        if isinstance(lane, dict)
    ]
    passed = manifest_ok and all(
        summary.get("status") == "direct_eval_present" for summary in lane_summaries
    )
    return _phase(
        "downstream_direct_evaluation",
        passed=passed,
        reviewer_ready=passed,
        details={
            "manifest_path": str(manifest_path),
            "manifest_present": manifest is not None,
            "manifest_schema_version": (manifest or {}).get("schema_version"),
            "lane_statuses": {
                str(summary.get("lane_id") or ""): str(summary.get("status") or "")
                for summary in lane_summaries
            },
            "failed_lane_ids": [
                str(summary.get("lane_id") or "")
                for summary in lane_summaries
                if summary.get("status") != "direct_eval_present"
            ],
            "lane_summaries": lane_summaries,
        },
    )


def _downstream_lane_summary(
    *,
    lane: dict,
    manifest_path: Path,
    output_dir: Path,
    source_set_id: str,
    lane_result: dict[str, object],
) -> dict:
    lane_id = str(lane.get("lane_id") or "")
    contract_path = _resolve_manifest_contract_path(manifest_path, lane.get("contract_path"))
    result = lane_result.get("result")
    result_path = Path(str(lane_result.get("result_path"))) if lane_result.get("result_path") else None
    present = isinstance(result, dict)
    expected_contract_sha = _sha256_file(contract_path) if contract_path.exists() else None
    actual_contract_sha = ((result or {}).get("contract") or {}).get("sha256") if present else None
    source_set_matches = (
        present and str((result or {}).get("source_set_id") or "") == source_set_id
    )
    eval_id_matches = present and str((result or {}).get("eval_id") or "") == str(lane.get("eval_id") or "")
    contract_sha_matches = present and expected_contract_sha == actual_contract_sha
    result_passed = bool(present and (result or {}).get("passed"))
    if not present:
        status = "direct_eval_missing"
    elif not source_set_matches or not eval_id_matches or not contract_sha_matches:
        status = "direct_eval_stale"
    elif not result_passed:
        status = "direct_eval_failed"
    else:
        status = "direct_eval_present"
    return {
        "lane_id": lane_id,
        "register_rows": lane.get("register_rows", []),
        "status": status,
        "result_path": str(result_path) if result_path is not None else None,
        "present": present,
        "result_passed": result_passed,
        "expected_eval_id": lane.get("eval_id"),
        "actual_eval_id": (result or {}).get("eval_id") if present else None,
        "expected_source_set_id": source_set_id,
        "actual_source_set_id": (result or {}).get("source_set_id") if present else None,
        "source_set_matches": bool(source_set_matches),
        "contract_path": str(contract_path),
        "expected_contract_sha256": expected_contract_sha,
        "actual_contract_sha256": actual_contract_sha,
        "contract_sha_matches": bool(contract_sha_matches),
        "checks": (result or {}).get("checks", []) if present else [],
    }


def _resolve_manifest_contract_path(manifest_path: Path, value: object | None) -> Path:
    if not value:
        return manifest_path
    path = Path(str(value))
    return path if path.is_absolute() else manifest_path.parent / path


def _upstream_evaluation_phase(
    *,
    upstream_evaluation: dict | None,
    upstream_evaluation_path: Path,
) -> dict:
    lane_statuses = {
        str(lane.get("lane_id") or ""): str(lane.get("status") or "")
        for lane in (upstream_evaluation or {}).get("lane_summaries", [])
        if isinstance(lane, dict)
    }
    passed = bool(upstream_evaluation and upstream_evaluation.get("passed"))
    return _phase(
        "upstream_evaluation",
        passed=passed,
        reviewer_ready=passed,
        details={
            "path": str(upstream_evaluation_path),
            "present": upstream_evaluation is not None,
            "schema_version": (upstream_evaluation or {}).get("schema_version"),
            "lane_statuses": lane_statuses,
            "failed_case_ids": (upstream_evaluation or {}).get("failed_case_ids", []),
        },
    )


def _draft_generation_phase(
    *,
    review_id: str,
    source_set_id: str,
    draft_generation_dir: Path,
) -> dict:
    validation_path = draft_generation_dir / DRAFT_GENERATION_VALIDATION_FILENAME
    eval_path = draft_generation_dir / DRAFT_GENERATION_EVAL_FILENAME
    manifest_path = draft_generation_dir / DRAFT_GENERATION_MANIFEST_FILENAME
    package_path = draft_generation_dir / DRAFT_GENERATION_PACKAGE_FILENAME
    validation = _read_json(validation_path) if validation_path.exists() else None
    evaluation = _read_json(eval_path) if eval_path.exists() else None
    manifest = _read_json(manifest_path) if manifest_path.exists() else None
    package = _read_json(package_path) if package_path.exists() else None
    validation_summary = _dict((validation or {}).get("summary"))
    eval_summary = _dict((evaluation or {}).get("summary"))
    manifest_input_artifacts = [
        artifact
        for artifact in (manifest or {}).get("input_artifacts", [])
        if isinstance(artifact, dict)
    ]
    stale_input_artifacts = []
    for artifact in manifest_input_artifacts:
        artifact_path = _resolve_repo_relative_path(str(artifact.get("artifact_path") or ""))
        expected_sha256 = str(artifact.get("sha256") or "")
        if artifact_path is None or not artifact_path.exists() or not expected_sha256:
            continue
        actual_sha256 = _sha256_file(artifact_path)
        if actual_sha256 != expected_sha256:
            semantic_sha256_matches = False
            expected_semantic_sha256 = str(artifact.get("semantic_sha256") or "")
            artifact_key = str(artifact.get("artifact_key") or "")
            if artifact_path.suffix == ".json" and expected_semantic_sha256:
                actual_payload = _read_json(artifact_path)
                actual_semantic_sha256 = _semantic_sha256_for_artifact(
                    artifact_key=artifact_key,
                    payload=actual_payload,
                )
                semantic_sha256_matches = actual_semantic_sha256 == expected_semantic_sha256
            if semantic_sha256_matches:
                continue
            stale_input_artifacts.append(
                {
                    "artifact_key": artifact_key,
                    "artifact_path": str(artifact_path),
                    "expected_sha256": expected_sha256,
                    "actual_sha256": actual_sha256,
                    "expected_semantic_sha256": expected_semantic_sha256 or None,
                }
            )
    package_summary = _dict((package or {}).get("summary"))
    checks = {
        "validation_exists": validation is not None,
        "eval_exists": evaluation is not None,
        "manifest_exists": manifest is not None,
        "package_exists": package is not None,
        "validation_schema_matches": (validation or {}).get("schema_version")
        == "draft-generation-validation-v1",
        "eval_schema_matches": (evaluation or {}).get("schema_version")
        == "draft-generation-eval-results-v1",
        "manifest_schema_matches": (manifest or {}).get("schema_version")
        == "draft-generation-manifest-v1",
        "package_schema_matches": (package or {}).get("schema_version")
        == "draft-generation-package-v1",
        "validation_review_id_matches": (validation or {}).get("review_id") == review_id,
        "eval_review_id_matches": (evaluation or {}).get("review_id") == review_id,
        "manifest_review_id_matches": (manifest or {}).get("review_id") == review_id,
        "package_review_id_matches": (package or {}).get("review_id") == review_id,
        "validation_source_set_matches": (validation or {}).get("source_set_id") == source_set_id,
        "eval_source_set_matches": (evaluation or {}).get("source_set_id") == source_set_id,
        "manifest_source_set_matches": (manifest or {}).get("source_set_id") == source_set_id,
        "package_source_set_matches": (package or {}).get("source_set_id") == source_set_id,
        "validation_passed": validation_summary.get("passed") is True,
        "eval_passed": eval_summary.get("passed") is True,
        "eval_live_validation_present": eval_summary.get("live_validation_present") is True,
        "eval_live_validation_passed": eval_summary.get("live_validation_passed") is True,
        "manifest_validation_passed": (manifest or {}).get("validation_passed") is True,
        "manifest_input_artifacts_fresh": not stale_input_artifacts,
        "ready_section_count_positive": int(package_summary.get("ready_section_count") or 0) > 0,
        "paragraph_count_positive": int(package_summary.get("paragraph_count") or 0) > 0,
    }
    passed = all(checks.values())
    return _phase(
        "draft_generation_defensibility",
        passed=passed,
        reviewer_ready=passed,
        details={
            "results_dir": str(draft_generation_dir),
            "validation_path": str(validation_path),
            "eval_path": str(eval_path),
            "manifest_path": str(manifest_path),
            "package_path": str(package_path),
            "failed_checks": sorted(name for name, ok in checks.items() if not ok),
            "stale_input_artifacts": stale_input_artifacts,
            "ready_section_count": package_summary.get("ready_section_count", 0),
            "paragraph_count": package_summary.get("paragraph_count", 0),
            "warning_section_count": package_summary.get("warning_section_count", 0),
            "refusal_count": package_summary.get("refusal_count", 0),
            "eval_case_count": eval_summary.get("case_count", 0),
            "eval_passed_case_count": eval_summary.get("passed_case_count", 0),
            **checks,
        },
    )
