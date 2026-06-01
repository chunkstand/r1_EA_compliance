from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .artifact_utils import _read_json
from .artifact_utils import _read_jsonl
from .artifact_utils import _source_set_id_from_catalog
from .artifact_utils import _utc_now
from .artifact_utils import _write_json
from .catalog_surface import resolve_catalog_dir_for_source_set
from .eval_trace_gate import build_eval_trace_gate_phase
from .eval_trace_inventory import REPO_ROOT as EVAL_TRACE_REPO_ROOT
from .phase_eval_direct_eval import apply_source_set_phase_direct_eval_gate
from .phase_eval_direct_eval import build_evaluation_coverage_phase
from .phase_eval_direct_eval import resolve_phase_eval_direct_eval_coverage
from .phase_eval_direct_eval_source_set import _downstream_result_path
from .phase_eval_review_phases import build_review_scoped_phases
from .phase_eval_sidecar import rule_claim_path_context as _rule_claim_path_context
from .phase_eval_sidecar import (
    with_rule_claim_direct_eval_override as _with_rule_claim_direct_eval_override,
)
from .phase_eval_source_set_phases import build_source_set_phases
from .phase_eval_source_set_phases import load_semantic_report
from .replay_context import ReplayContextMismatchError
from .replay_context import load_replay_context
from .replay_context import tracked_replay_context_path
from .rule_claim_binding import default_rule_claim_links_dir
from .source_set_support import source_derived_dir


DOWNSTREAM_DIRECT_EVAL_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "downstream_direct_eval_v1.json"
)
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
KNOWLEDGE_GRAPH_FILE_PREFIX = "n" "epa_3d_graph"


@dataclass(frozen=True)
class PhaseEvalResult:
    source_set_id: str
    graph_dir: Path
    output_path: Path
    review_output_path: Path | None
    summary: dict


def run_phase_aligned_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    catalog_dir: Path | None = None,
    review_id: str | None = None,
    review_dir: Path | None = None,
    rule_claim_links_path: Path | None = None,
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
    explicit_rule_claim_links_path = (
        Path(rule_claim_links_path) if rule_claim_links_path is not None else None
    )
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
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    graph_dir = derived_source_dir / "evidence_graph"
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
    extraction_validation_path = derived_source_dir / "diagnostics" / "extraction_validation.json"
    extraction_summary_path = derived_source_dir / "diagnostics" / "summary.json"
    extraction_accuracy_path = (
        derived_source_dir / "diagnostics" / "extraction_accuracy_audit.json"
    )
    authority_currentness_path = (
        derived_source_dir / "authority_currentness" / "authority_currentness_report.json"
    )
    upstream_evaluation_path = (
        output_dir / "evaluations" / "upstream" / "upstream_evaluation_results.json"
    )
    downstream_direct_eval_manifest_path = DOWNSTREAM_DIRECT_EVAL_MANIFEST_PATH
    retrieval_eval_path = derived_source_dir / "retrieval" / "retrieval_eval_results.json"
    retrieval_validation_path = derived_source_dir / "retrieval" / "retrieval_validation.json"
    retrieval_summary_path = derived_source_dir / "retrieval" / "summary.json"
    graph_validation_path = graph_dir / "evidence_graph_validation.json"
    graph_summary_path = graph_dir / "summary.json"
    knowledge_graph_dir = derived_source_dir / "knowledge_graph"
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
    proving_semantic_dir = derived_source_dir / "source_register_proving"
    claim_dir = derived_source_dir / "claims"
    claim_eval_path = claim_dir / "claim_eval_results.json"
    claim_validation_path = claim_dir / "claim_validation.json"
    claim_summary_path = claim_dir / "summary.json"
    try:
        rule_claim_dir = default_rule_claim_links_dir(
            output_dir,
            source_set_id=source_set_id,
        )
    except (FileNotFoundError, ValueError):
        rule_claim_dir = derived_source_dir / "rule_claim_links"
    rule_claim_validation_path = rule_claim_dir / "rule_claim_link_validation.json"
    rule_claim_summary_path = rule_claim_dir / "summary.json"
    rule_claim_eval_path = _downstream_result_path(
        output_dir=output_dir,
        source_set_id=source_set_id,
        lane_id="rule_claim_eval",
    )
    if not rule_claim_summary_path.exists():
        candidates = sorted((derived_source_dir / "rule_claim_links").glob("*/*/summary.json"))
        if candidates:
            rule_claim_summary_path = candidates[0]
            rule_claim_validation_path = (
                rule_claim_summary_path.parent / "rule_claim_link_validation.json"
            )
            rule_claim_eval_path = rule_claim_summary_path.parent / "rule_claim_link_eval_results.json"
    if explicit_rule_claim_links_path is not None:
        rule_claim_summary_path = explicit_rule_claim_links_path.parent / "summary.json"
        rule_claim_validation_path = (
            explicit_rule_claim_links_path.parent / "rule_claim_link_validation.json"
        )
        rule_claim_eval_path = (
            explicit_rule_claim_links_path.parent / "rule_claim_link_eval_results.json"
        )
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
    authority_relationship_eval = load_semantic_report(
        primary_path=authority_relationship_eval_path,
        fallback_path=proving_semantic_dir / "authority_relationship_eval_report.json",
    )
    citation_alias_eval = load_semantic_report(
        primary_path=citation_alias_eval_path,
        fallback_path=proving_semantic_dir / "citation_alias_eval_report.json",
    )
    graph_health_eval = load_semantic_report(
        primary_path=graph_health_eval_path,
        fallback_path=proving_semantic_dir / "graph_health_eval_report.json",
    )
    graph_accuracy_eval = load_semantic_report(
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
    if (
        explicit_rule_claim_links_path is None
        and compliance_summary_for_rule_claim.get("rule_claim_summary_path")
    ):
        candidate_summary_path = Path(
            str(compliance_summary_for_rule_claim["rule_claim_summary_path"])
        )
        if candidate_summary_path.exists():
            rule_claim_summary_path = candidate_summary_path
    if (
        explicit_rule_claim_links_path is None
        and compliance_summary_for_rule_claim.get("rule_claim_validation_path")
    ):
        candidate_validation_path = Path(
            str(compliance_summary_for_rule_claim["rule_claim_validation_path"])
        )
        if candidate_validation_path.exists():
            rule_claim_validation_path = candidate_validation_path
    if (
        explicit_rule_claim_links_path is None
        and compliance_summary_for_rule_claim.get("rule_claim_links_path")
        and not bool(compliance_summary_for_rule_claim.get("rule_claim_links_are_canonical", True))
    ):
        rule_claim_eval_path = (
            Path(str(compliance_summary_for_rule_claim["rule_claim_links_path"])).parent
            / "rule_claim_link_eval_results.json"
        )
    rule_claim_validation = (
        _read_json(rule_claim_validation_path) if rule_claim_validation_path.exists() else None
    )
    rule_claim_summary = (
        _read_json(rule_claim_summary_path) if rule_claim_summary_path.exists() else None
    )
    rule_claim_path_context = _rule_claim_path_context(
        explicit_links_path=explicit_rule_claim_links_path,
        selected_eval_path=rule_claim_eval_path,
        selected_summary=rule_claim_summary,
        compliance_summary=compliance_summary_for_rule_claim,
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

    rule_claim_direct_eval_override_required = bool(
        rule_claim_path_context.get("uses_sidecar_rule_claim_links")
        or explicit_rule_claim_links_path
    )
    direct_eval_coverage = resolve_phase_eval_direct_eval_coverage(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=resolved_review_id,
        review_dir=review_dir,
    )
    if rule_claim_direct_eval_override_required:
        direct_eval_coverage = _with_rule_claim_direct_eval_override(
            direct_eval_coverage=direct_eval_coverage,
            downstream_manifest=downstream_direct_eval_manifest,
            downstream_manifest_path=downstream_direct_eval_manifest_path,
            result_path=rule_claim_eval_path,
            source_set_id=source_set_id,
        )
    component_retrieval_direct_eval = direct_eval_coverage["source_set_phase_statuses"].get(
        "forest_plan_component_retrieval"
    )
    semantic_graph_direct_eval = direct_eval_coverage["source_set_phase_statuses"].get(
        "canonical_semantic_graph"
    )
    knowledge_graph_query_direct_eval = direct_eval_coverage["source_set_phase_statuses"].get(
        "knowledge_graph_query_surface"
    )
    eval_context_graph_direct_eval = direct_eval_coverage["source_set_phase_statuses"].get(
        "observability_eval_context_graph"
    )
    phases = build_source_set_phases(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_validation=catalog_validation,
        catalog_validation_path=catalog_validation_path,
        extraction_validation=extraction_validation,
        extraction_validation_path=extraction_validation_path,
        extraction_summary=extraction_summary,
        extraction_summary_path=extraction_summary_path,
        upstream_evaluation=upstream_evaluation,
        upstream_evaluation_path=upstream_evaluation_path,
        retrieval_validation=retrieval_validation,
        retrieval_validation_path=retrieval_validation_path,
        retrieval_summary=retrieval_summary,
        retrieval_summary_path=retrieval_summary_path,
        graph_validation=graph_validation,
        graph_validation_path=graph_validation_path,
        graph_summary=graph_summary,
        graph_summary_path=graph_summary_path,
        claim_validation=claim_validation,
        claim_validation_path=claim_validation_path,
        claim_summary=claim_summary,
        claim_summary_path=claim_summary_path,
        rule_claim_validation=rule_claim_validation,
        rule_claim_validation_path=rule_claim_validation_path,
        rule_claim_summary=rule_claim_summary,
        rule_claim_summary_path=rule_claim_summary_path,
        rule_claim_path_context=rule_claim_path_context,
        downstream_direct_eval_manifest=downstream_direct_eval_manifest,
        downstream_direct_eval_manifest_path=downstream_direct_eval_manifest_path,
        downstream_lane_results={
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
        source_set_manifest=source_set_manifest,
        catalog_rows=catalog_rows,
        authority_currentness_report=authority_currentness_report,
        authority_currentness_path=authority_currentness_path,
        extraction_accuracy=extraction_accuracy,
        extraction_accuracy_path=extraction_accuracy_path,
        knowledge_graph_validation=knowledge_graph_validation,
        knowledge_graph_validation_path=knowledge_graph_validation_path,
        knowledge_graph_summary=knowledge_graph_summary,
        knowledge_graph_summary_path=knowledge_graph_summary_path,
        semantic_graph_reports={
            "authority_ontology": (
                authority_ontology_validation,
                authority_ontology_validation_path,
            ),
            "authority_relationships": (
                authority_relationship_eval,
                authority_relationship_eval_path,
            ),
            "citation_aliases": (
                citation_alias_eval,
                citation_alias_eval_path,
            ),
            "graph_health": (
                graph_health_eval,
                graph_health_eval_path,
            ),
            "graph_accuracy": (
                graph_accuracy_eval,
                graph_accuracy_eval_path,
            ),
        },
        component_retrieval_direct_eval=component_retrieval_direct_eval,
        semantic_graph_direct_eval=semantic_graph_direct_eval,
        knowledge_graph_query_direct_eval=knowledge_graph_query_direct_eval,
        eval_context_graph_direct_eval=eval_context_graph_direct_eval,
    )
    phases.extend(
        build_review_scoped_phases(
            output_dir=output_dir,
            source_set_id=source_set_id,
            review_id=review_id,
            review_dir=review_dir,
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
            review_knowledge_graph_validation=review_knowledge_graph_validation,
            review_knowledge_graph_validation_path=review_knowledge_graph_validation_path,
            review_knowledge_graph_summary=review_knowledge_graph_summary,
            review_knowledge_graph_summary_path=review_knowledge_graph_summary_path,
            compliance_validation=compliance_validation,
            compliance_validation_path=compliance_validation_path,
            compliance_review=compliance_review,
            compliance_review_path=compliance_review_path,
            compliance_matrix=compliance_matrix,
            compliance_matrix_path=compliance_matrix_path,
            compliance_matrix_pdf_path=compliance_matrix_pdf_path,
            component_adjudication_eval=component_adjudication_eval,
            component_adjudication_eval_path=component_adjudication_eval_path,
            component_eval=component_eval,
            component_eval_path=component_eval_path,
            component_queue=component_queue,
            component_queue_path=component_queue_path,
            component_adjudication_file_path=component_adjudication_file_path,
            compliance_coverage=compliance_coverage,
            compliance_coverage_path=compliance_coverage_path,
            compliance_gold_eval=compliance_gold_eval,
            compliance_gold_eval_path=compliance_gold_eval_path,
            rule_claim_summary=rule_claim_summary,
            decision_support_dir=decision_support_dir,
            draft_generation_dir=draft_generation_dir,
            review_packet_index_dir=review_packet_index_dir,
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
    eval_trace_gate = build_eval_trace_gate_phase(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=resolved_review_id,
        repo_root=_eval_trace_repo_root(output_dir),
    )
    if eval_trace_gate.phase is not None:
        phases.append(eval_trace_gate.phase)
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
        "applicability_arbitration_summary": (
            next(
                (
                    phase["details"].get("arbitration_summary", {})
                    for phase in phases
                    if phase["name"] == "applicability_determination"
                ),
                {},
            )
            if review_dir is not None
            else {}
        ),
        "blockers": blockers,
        "phases": phases,
        "eval_trace_gate": eval_trace_gate.status,
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
    return source_derived_dir(output_dir / "derived", source_set_id) / "evidence_graph"


def _eval_trace_repo_root(output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    try:
        resolved.relative_to(EVAL_TRACE_REPO_ROOT)
    except ValueError:
        return resolved.parent
    return EVAL_TRACE_REPO_ROOT
