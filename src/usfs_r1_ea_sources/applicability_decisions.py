from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .applicability_decision_arbitration import arbitrate_trigger_matches as _arbitrate_trigger_matches
from .applicability_decision_arbitration import arbitration_summary as _arbitration_summary
from .applicability_decision_arbitration import trigger_arbitration_not_evaluated as _trigger_arbitration_not_evaluated
from .applicability_decision_arbitration import trigger_groups as _trigger_groups
from .applicability_decision_coverage import SEARCH_COVERAGE_CERTIFICATES_SCHEMA_VERSION
from .applicability_decision_coverage import coverage_boundary as _coverage_boundary
from .applicability_decision_coverage import coverage_certificate as _coverage_certificate
from .applicability_decision_coverage import records_by_candidate as _records_by_candidate
from .applicability_decision_evidence import declared_source_library_evidence as _declared_source_library_evidence
from .applicability_decision_evidence import build_trigger_search_index as _build_trigger_search_index
from .applicability_decision_forest_plan import forest_plan_component_result as _forest_plan_component_result
from .applicability_decision_evidence import package_fact_nodes as _package_fact_nodes
from .applicability_decision_evidence import present_package_values as _present_package_values
from .applicability_decision_evidence import retrieval_lineage as _retrieval_lineage
from .applicability_decision_evidence import selected_package_results as _selected_package_results
from .applicability_decision_evidence import source_evidence_available as _source_evidence_available
from .applicability_decision_evidence import source_library_evidence as _source_library_evidence
from .applicability_decision_evidence import trigger_match as _trigger_match
from .applicability_decision_outputs import decision_provenance
from .applicability_decision_outputs import decision_summary
from .applicability_decision_outputs import partition_authority_record
from .applicability_decision_outputs import write_decision_report
from .records import sha256_file


APPLICABILITY_DECISIONS_SCHEMA_VERSION = "applicability-decisions-v0"
APPLICABLE_AUTHORITIES_SCHEMA_VERSION = "applicable-authorities-v0"
NON_APPLICABLE_AUTHORITIES_SCHEMA_VERSION = "non-applicable-authorities-v0"
DETERMINISTIC_PREDICATE_VERSION = "deterministic-applicability-predicate-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ApplicabilityDecisionResult:
    review_id: str
    source_set_id: str
    applicability_dir: Path
    decisions_path: Path
    applicable_authorities_path: Path
    non_applicable_authorities_path: Path
    search_coverage_certificates_path: Path
    provenance_path: Path
    report_path: Path
    summary: dict[str, Any]


def build_applicability_decisions(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    authority_universe_path: Path | None = None,
    package_fact_graph_path: Path | None = None,
    package_applicability_context_path: Path | None = None,
    retrieval_trace_path: Path | None = None,
    graph_trace_path: Path | None = None,
) -> ApplicabilityDecisionResult:
    """Write deterministic applicability artifacts before compliance review."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    authority_universe_path = authority_universe_path or (
        applicability_dir / "authority_universe_snapshot.json"
    )
    package_fact_graph_path = package_fact_graph_path or (
        applicability_dir / "package_fact_graph.json"
    )
    package_applicability_context_path = package_applicability_context_path or (
        applicability_dir / "package_applicability_context.json"
    )
    retrieval_trace_path = retrieval_trace_path or (
        applicability_dir / "applicability_retrieval_trace.jsonl"
    )
    graph_trace_path = graph_trace_path or (
        applicability_dir / "applicability_graph_trace.jsonl"
    )

    authority_universe = _read_required_json(authority_universe_path, "authority universe")
    package_fact_graph = _read_required_json(package_fact_graph_path, "package fact graph")
    package_context = _read_required_json(
        package_applicability_context_path,
        "package applicability context",
    )
    retrieval_rows = _read_required_jsonl(retrieval_trace_path, "applicability retrieval trace")
    graph_rows = _read_required_jsonl(graph_trace_path, "applicability graph trace")
    package_chunks_path = _optional_artifact_path(package_fact_graph, "package_chunks_path")
    package_chunks = _read_jsonl_if_exists(package_chunks_path)

    if source_set_id is None:
        source_set_id = str(authority_universe.get("source_set_id") or "").strip()
    _validate_safe_segment(source_set_id, "source_set_id")
    _assert_source_set_matches(source_set_id, authority_universe, package_fact_graph, package_context)

    created_at = _utc_now()
    applicability_run_id = f"applicability-determine:{review_id}:{source_set_id}"
    authority_universe_sha256 = str(
        authority_universe.get("authority_universe_sha256")
        or sha256_file(authority_universe_path)
    )
    package_manifest_sha256 = str(
        package_context.get("package_manifest_sha256")
        or package_fact_graph.get("package_manifest_sha256")
        or ""
    )
    package_chunks_sha256 = str(
        package_context.get("package_chunks_sha256")
        or package_fact_graph.get("package_chunks_sha256")
        or ""
    )
    package_fact_graph_sha256 = str(
        package_fact_graph.get("package_fact_graph_sha256")
        or sha256_file(package_fact_graph_path)
    )
    retrieval_trace_sha256 = sha256_file(retrieval_trace_path)
    graph_trace_sha256 = sha256_file(graph_trace_path)
    catalog_sha256 = str(authority_universe.get("catalog_sha256") or "")
    freshness = {
        "authority_universe_sha256": authority_universe_sha256,
        "package_manifest_sha256": package_manifest_sha256,
        "package_chunks_sha256": package_chunks_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "search_coverage_certificates_sha256": None,
        "source_set_id": source_set_id,
        "catalog_sha256": catalog_sha256,
    }

    retrieval_by_candidate = _records_by_candidate(retrieval_rows)
    graph_by_candidate = _records_by_candidate(graph_rows)
    package_nodes = _package_fact_nodes(package_fact_graph)
    package_present_values = _present_package_values(package_nodes)
    trigger_search_index = _build_trigger_search_index(
        package_nodes=package_nodes,
        package_chunks=package_chunks,
    )
    decisions: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    for candidate in sorted(
        authority_universe.get("candidate_authorities") or [],
        key=lambda item: str(item.get("candidate_authority_id") or ""),
    ):
        candidate_id = str(candidate.get("candidate_authority_id") or "")
        candidate_retrieval_rows = retrieval_by_candidate.get(candidate_id, [])
        candidate_graph_rows = graph_by_candidate.get(candidate_id, [])
        coverage_boundary = _coverage_boundary(
            candidate=candidate,
            retrieval_rows=candidate_retrieval_rows,
            graph_rows=candidate_graph_rows,
        )
        decision = _decision_for_candidate(
            applicability_run_id=applicability_run_id,
            created_at=created_at,
            review_id=review_id,
            source_set_id=source_set_id,
            candidate=candidate,
            package_nodes=package_nodes,
            package_fact_graph=package_fact_graph,
            package_context=package_context,
            package_chunks=package_chunks,
            package_present_values=package_present_values,
            trigger_search_index=trigger_search_index,
            retrieval_rows=candidate_retrieval_rows,
            graph_rows=candidate_graph_rows,
            coverage_boundary=coverage_boundary,
            freshness=freshness,
        )
        if decision["status"] in {"not_applicable", "unresolved", "needs_adjudication"}:
            certificate = _coverage_certificate(
                applicability_run_id=applicability_run_id,
                review_id=review_id,
                source_set_id=source_set_id,
                created_at=created_at,
                candidate=candidate,
                decision=decision,
                coverage_boundary=coverage_boundary,
                authority_universe_sha256=authority_universe_sha256,
                package_fact_graph_sha256=package_fact_graph_sha256,
                retrieval_trace_sha256=retrieval_trace_sha256,
                graph_trace_sha256=graph_trace_sha256,
                retrieval_rows=candidate_retrieval_rows,
                graph_rows=candidate_graph_rows,
            )
            certificates.append(certificate)
            decision["search_coverage_certificate_ids"] = [
                certificate["coverage_certificate_id"]
            ]
        decisions.append(decision)

    certificates_payload_without_hash = {
        "schema_version": SEARCH_COVERAGE_CERTIFICATES_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "authority_universe_sha256": authority_universe_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "certificates": certificates,
    }
    search_coverage_certificates_sha256 = _stable_sha256(certificates_payload_without_hash)
    freshness["search_coverage_certificates_sha256"] = search_coverage_certificates_sha256
    for decision in decisions:
        decision["freshness"]["search_coverage_certificates_sha256"] = (
            search_coverage_certificates_sha256
        )
    certificates_payload = {
        **certificates_payload_without_hash,
        "search_coverage_certificates_sha256": search_coverage_certificates_sha256,
    }

    decisions_path = applicability_dir / "applicability_decisions.jsonl"
    search_coverage_certificates_path = applicability_dir / "search_coverage_certificates.json"
    _write_json(search_coverage_certificates_path, certificates_payload)
    decisions_sha256 = _write_jsonl_and_hash(decisions_path, decisions)

    partition_common = {
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "authority_universe_sha256": authority_universe_sha256,
        "package_manifest_sha256": package_manifest_sha256,
        "package_chunks_sha256": package_chunks_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "search_coverage_certificates_sha256": search_coverage_certificates_sha256,
        "applicability_decisions_sha256": decisions_sha256,
        "catalog_sha256": catalog_sha256,
    }
    applicable_payload = {
        "schema_version": APPLICABLE_AUTHORITIES_SCHEMA_VERSION,
        **partition_common,
        "applicable_authority_count": sum(
            1 for decision in decisions if decision["status"] == "applicable"
        ),
        "authorities": [
            partition_authority_record(decision)
            for decision in decisions
            if decision["status"] == "applicable"
        ],
    }
    non_applicable_payload = {
        "schema_version": NON_APPLICABLE_AUTHORITIES_SCHEMA_VERSION,
        **partition_common,
        "non_applicable_authority_count": sum(
            1 for decision in decisions if decision["status"] == "not_applicable"
        ),
        "authorities": [
            partition_authority_record(decision)
            for decision in decisions
            if decision["status"] == "not_applicable"
        ],
    }
    applicable_authorities_path = applicability_dir / "applicable_authorities.json"
    non_applicable_authorities_path = applicability_dir / "non_applicable_authorities.json"
    _write_json(applicable_authorities_path, applicable_payload)
    _write_json(non_applicable_authorities_path, non_applicable_payload)
    applicable_authorities_sha256 = sha256_file(applicable_authorities_path)
    non_applicable_authorities_sha256 = sha256_file(non_applicable_authorities_path)

    summary = decision_summary(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_run_id=applicability_run_id,
        decisions=decisions,
        certificates=certificates,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
    )
    provenance_path = applicability_dir / "applicability_provenance.json"
    provenance_payload = decision_provenance(
        applicability_run_id=applicability_run_id,
        review_id=review_id,
        source_set_id=source_set_id,
        created_at=created_at,
        ended_at=_utc_now(),
        authority_universe_path=authority_universe_path,
        package_fact_graph_path=package_fact_graph_path,
        package_applicability_context_path=package_applicability_context_path,
        retrieval_trace_path=retrieval_trace_path,
        graph_trace_path=graph_trace_path,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
        package_manifest_path=_optional_artifact_path(package_fact_graph, "package_manifest_path"),
        package_chunks_path=package_chunks_path,
        source_set_manifest_path=_optional_artifact_path(
            authority_universe,
            "source_set_manifest_path",
        ),
        source_catalog_path=_optional_artifact_path(authority_universe, "source_catalog_path"),
        authority_universe_sha256=authority_universe_sha256,
        source_set_manifest_sha256=str(authority_universe.get("source_set_manifest_sha256") or ""),
        package_manifest_sha256=package_manifest_sha256,
        package_chunks_sha256=package_chunks_sha256,
        package_fact_graph_sha256=package_fact_graph_sha256,
        retrieval_trace_sha256=retrieval_trace_sha256,
        graph_trace_sha256=graph_trace_sha256,
        search_coverage_certificates_sha256=search_coverage_certificates_sha256,
        decisions_sha256=decisions_sha256,
        applicable_authorities_sha256=applicable_authorities_sha256,
        non_applicable_authorities_sha256=non_applicable_authorities_sha256,
    )
    _write_json(provenance_path, provenance_payload)
    report_path = applicability_dir / "applicability_report.md"
    write_decision_report(report_path, summary, decisions)

    summary = {
        **summary,
        "provenance_path": str(provenance_path),
        "report_path": str(report_path),
        "applicability_provenance_sha256": sha256_file(provenance_path),
        "applicability_report_sha256": sha256_file(report_path),
        "applicable_authorities_sha256": applicable_authorities_sha256,
        "non_applicable_authorities_sha256": non_applicable_authorities_sha256,
        "applicability_decisions_sha256": decisions_sha256,
        "search_coverage_certificates_sha256": search_coverage_certificates_sha256,
    }
    return ApplicabilityDecisionResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
        provenance_path=provenance_path,
        report_path=report_path,
        summary=summary,
    )


def _decision_for_candidate(
    *,
    applicability_run_id: str,
    created_at: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    package_nodes: list[dict[str, Any]],
    package_fact_graph: dict[str, Any],
    package_context: dict[str, Any],
    package_chunks: list[dict[str, Any]],
    package_present_values: dict[str, set[str]],
    trigger_search_index: dict[str, Any],
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
    coverage_boundary: dict[str, Any],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    authority_family_ids = _authority_family_ids_for_candidate(candidate)
    source_record_ids = _strings(candidate.get("source_record_ids"))
    source_evidence = _source_library_evidence(retrieval_rows, source_record_ids)
    if not source_evidence:
        source_evidence = _declared_source_library_evidence(candidate, source_record_ids)
    graph_path_ids = [
        str(row.get("graph_path_id"))
        for row in graph_rows
        if row.get("selected_status") == "selected" and row.get("graph_path_id")
    ]
    selected_result_ids, rejected_result_ids, trace_ids = _retrieval_lineage(retrieval_rows)
    package_results = _selected_package_results(retrieval_rows)
    negative_groups = _trigger_groups(candidate.get("negative_trigger_groups"))
    positive_groups = _trigger_groups(candidate.get("positive_trigger_groups"))
    positive_match = _trigger_match(
        groups=positive_groups,
        package_nodes=package_nodes,
        package_chunks=package_chunks,
        package_results=package_results,
        search_index=trigger_search_index,
    )
    negative_match = _trigger_match(
        groups=negative_groups,
        package_nodes=package_nodes,
        package_chunks=package_chunks,
        package_results=package_results,
        include_negative_context=True,
        search_index=trigger_search_index,
    )
    source_available = _source_evidence_available(candidate) or bool(source_evidence)
    missing_evidence: list[str] = []
    contradiction_notes: list[str] = []
    reviewer_notes: list[str] = []
    status = "unresolved"
    basis_type = "source_set_required"
    basis: dict[str, Any] = {}
    confidence = "low"
    predicate_name = "source_set_required"
    trigger_arbitration = _trigger_arbitration_not_evaluated(
        "required source evidence has not been evaluated"
    )

    if not source_available:
        missing_evidence.append("required source evidence is unavailable")
        basis = {
            "rationale": "Required source-library evidence was not available for this authority.",
            "source_evidence_availability": candidate.get("source_evidence_availability") or {},
        }
    elif candidate.get("candidate_authority_type") == "forest_plan_component":
        if positive_groups or negative_groups:
            trigger_arbitration = _arbitrate_trigger_matches(
                candidate=candidate,
                positive_match=positive_match,
                negative_match=negative_match,
                coverage_boundary=coverage_boundary,
            )
        else:
            trigger_arbitration = _trigger_arbitration_not_evaluated(
                "Forest Plan component has no trigger groups; profile/component scope predicate decides applicability.",
                arbitration_status="component_scope_only",
            )
        component_result = _forest_plan_component_result(
            candidate=candidate,
            package_nodes=package_nodes,
            present_values=package_present_values,
            positive_match=positive_match,
            negative_match=negative_match,
            coverage_boundary=coverage_boundary,
            trigger_arbitration=trigger_arbitration,
        )
        status = component_result["status"]
        basis_type = component_result["basis_type"]
        basis = component_result["basis"]
        missing_evidence.extend(component_result["missing_evidence"])
        contradiction_notes.extend(component_result["contradiction_notes"])
        confidence = component_result["confidence"]
        predicate_name = "forest_plan_component"
    else:
        mode = str(
            (candidate.get("rule_template") or {}).get("applicability_mode")
            or (candidate.get("deterministic_applicability_test_contract") or {}).get(
                "applicability_mode"
            )
            or ""
        )
        if mode == "baseline":
            status = "applicable"
            basis_type = "mandatory_baseline"
            predicate_name = "mandatory_baseline"
            confidence = "deterministic_high"
            basis = {
                "rationale": "Baseline authorities are mandatory for this source set.",
                "baseline_required": True,
            }
            trigger_arbitration = _trigger_arbitration_not_evaluated(
                "Baseline authorities are mandatory and do not require trigger arbitration.",
                arbitration_status="mandatory_baseline",
            )
        else:
            trigger_arbitration = _arbitrate_trigger_matches(
                candidate=candidate,
                positive_match=positive_match,
                negative_match=negative_match,
                coverage_boundary=coverage_boundary,
            )

        if mode == "baseline":
            pass
        elif trigger_arbitration["arbitration_status"] == "positive_negative_conflict":
            predicate_name = "trigger_arbitration"
            status = "needs_adjudication"
            basis_type = "unresolved_evidence_conflict"
            confidence = "needs_adjudication"
            basis = {
                "rationale": trigger_arbitration["arbitration_rationale"],
                "matched_trigger_groups": positive_match["matched_groups"],
                "matched_negative_trigger_groups": negative_match["matched_groups"],
                "decisive_trigger_groups": trigger_arbitration["decisive_trigger_groups"],
                "weak_auxiliary_trigger_groups": trigger_arbitration[
                    "weak_auxiliary_trigger_groups"
                ],
            }
            contradiction_notes.extend(trigger_arbitration["arbitration_notes"])
        elif trigger_arbitration["positive_trigger_sufficient"]:
            predicate_name = "trigger_arbitration"
            status = "applicable"
            basis_type = "positive_package_trigger"
            confidence = "deterministic_high"
            basis = {
                "rationale": trigger_arbitration["arbitration_rationale"],
                "matched_trigger_groups": positive_match["matched_groups"],
                "decisive_trigger_groups": trigger_arbitration["decisive_trigger_groups"],
                "weak_auxiliary_trigger_groups": trigger_arbitration[
                    "weak_auxiliary_trigger_groups"
                ],
            }
            reviewer_notes.extend(trigger_arbitration["arbitration_notes"])
        elif negative_match["matched"]:
            predicate_name = "explicit_negative_package_evidence"
            basis_type = "negative_package_evidence"
            basis = {
                "rationale": "Package evidence matched an explicit negative applicability trigger.",
                "matched_trigger_groups": negative_match["matched_groups"],
            }
            if coverage_boundary["coverage_sufficient"]:
                status = "not_applicable"
                confidence = "deterministic_medium"
            else:
                status = "unresolved"
                confidence = "low"
                missing_evidence.append("sufficient search coverage for negative trigger")
        elif positive_match["matched"]:
            predicate_name = "positive_package_trigger"
            basis_type = "unresolved_evidence_conflict"
            basis = {
                "rationale": trigger_arbitration["arbitration_rationale"],
                "matched_trigger_groups": positive_match["matched_groups"],
                "weak_only_trigger_groups": trigger_arbitration["weak_only_trigger_groups"],
                "missing_required_trigger_groups": trigger_arbitration[
                    "missing_required_trigger_groups"
                ],
            }
            status = "needs_adjudication"
            confidence = "needs_adjudication"
            contradiction_notes.extend(trigger_arbitration["arbitration_notes"])
        elif coverage_boundary["coverage_sufficient"]:
            status = "not_applicable"
            basis_type = "absent_trigger_evidence"
            predicate_name = "absent_trigger_evidence"
            confidence = "deterministic_medium"
            basis = {
                "rationale": (
                    "Required positive package trigger groups were not found within the "
                    "recorded search boundary."
                ),
                "missing_trigger_groups": positive_groups,
            }
        else:
            status = "unresolved"
            basis_type = "absent_trigger_evidence"
            predicate_name = "search_coverage_gap"
            confidence = "low"
            missing_evidence.append("sufficient search coverage for trigger-miss decision")
            basis = {
                "rationale": (
                    "The positive trigger was not found, but search coverage was not sufficient "
                    "to make a not-applicable decision."
                ),
                "missing_trigger_groups": positive_groups,
            }

    package_evidence = (
        positive_match["evidence_spans"]
        if status in {"applicable", "needs_adjudication"}
        else []
    )
    negative_evidence = negative_match["evidence_spans"] if negative_match["matched"] else []
    trigger_miss_evidence = []
    if status in {"not_applicable", "unresolved"} and basis_type == "absent_trigger_evidence":
        trigger_miss_evidence.append(
            {
                "missing_trigger_groups": positive_groups,
                "coverage_sufficient": coverage_boundary["coverage_sufficient"],
                "executed_query_variants": coverage_boundary["executed_query_variants"],
            }
        )
    if status == "not_applicable" and basis_type == "forest_plan_component":
        trigger_miss_evidence.append(
            {
                "missing_trigger_groups": basis.get("missing_trigger_groups") or [],
                "missing_package_values": basis.get("missing_package_values") or [],
                "coverage_sufficient": coverage_boundary["coverage_sufficient"],
                "executed_query_variants": coverage_boundary["executed_query_variants"],
            }
        )
    decision_id = _stable_id(
        "applicability-decision",
        applicability_run_id,
        candidate_id,
        status,
        basis_type,
    )
    predicate_inputs = {
        "candidate_authority_id": candidate_id,
        "positive_trigger_groups": positive_groups,
        "negative_trigger_groups": negative_groups,
        "source_record_ids": source_record_ids,
        "coverage_boundary": coverage_boundary,
        "package_fact_graph_sha256": package_fact_graph.get("package_fact_graph_sha256"),
        "package_context_sha256": package_context.get("package_context_sha256"),
        "trigger_arbitration": trigger_arbitration,
    }
    arbitration_summary = _arbitration_summary(
        status=status,
        basis_type=basis_type,
        predicate_name=predicate_name,
        positive_match=positive_match,
        negative_match=negative_match,
        trigger_arbitration=trigger_arbitration,
        source_evidence=source_evidence,
        selected_retrieval_result_ids=selected_result_ids,
        retrieval_trace_ids=trace_ids,
        graph_path_ids=graph_path_ids,
    )
    return {
        "schema_version": APPLICABILITY_DECISIONS_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "decision_id": decision_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "authority_family_ids": authority_family_ids,
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "status": status,
        "basis_type": basis_type,
        "basis": basis,
        "deterministic_predicate": {
            "predicate_name": predicate_name,
            "predicate_version": DETERMINISTIC_PREDICATE_VERSION,
            "predicate_input_hash": _stable_sha256(predicate_inputs),
            "predicate_result": {
                "status": status,
                "basis_type": basis_type,
                "coverage_sufficient": coverage_boundary["coverage_sufficient"],
                "arbitration_status": trigger_arbitration["arbitration_status"],
                "decisive_trigger_groups": trigger_arbitration["decisive_trigger_groups"],
                "weak_auxiliary_trigger_groups": trigger_arbitration[
                    "weak_auxiliary_trigger_groups"
                ],
            },
        },
        "predicate_name": predicate_name,
        "predicate_version": DETERMINISTIC_PREDICATE_VERSION,
        "predicate_input_hashes": {
            "predicate_inputs_sha256": _stable_sha256(predicate_inputs),
            "package_fact_graph_sha256": package_fact_graph.get("package_fact_graph_sha256"),
            "package_context_sha256": package_context.get("package_context_sha256"),
        },
        "predicate_result": {
            "status": status,
            "basis_type": basis_type,
            "positive_trigger_matched": positive_match["matched"],
            "negative_trigger_matched": negative_match["matched"],
            "coverage_sufficient": coverage_boundary["coverage_sufficient"],
            "arbitration_status": trigger_arbitration["arbitration_status"],
            "decisive_trigger_groups": trigger_arbitration["decisive_trigger_groups"],
            "weak_auxiliary_trigger_groups": trigger_arbitration[
                "weak_auxiliary_trigger_groups"
            ],
        },
        "arbitration_summary": arbitration_summary,
        "arbitration_status": trigger_arbitration["arbitration_status"],
        "decisive_trigger_groups": trigger_arbitration["decisive_trigger_groups"],
        "weak_auxiliary_trigger_groups": trigger_arbitration[
            "weak_auxiliary_trigger_groups"
        ],
        "weak_only_trigger_groups": trigger_arbitration["weak_only_trigger_groups"],
        "arbitration_rationale": trigger_arbitration["arbitration_rationale"],
        "source_record_ids": source_record_ids,
        "authority_category": candidate.get("authority_category"),
        "authority_document_role": candidate.get("authority_document_role"),
        "rule_template": candidate.get("rule_template"),
        "forest_plan": candidate.get("forest_plan"),
        "package_evidence_spans": package_evidence,
        "source_library_evidence_spans": source_evidence,
        "retrieval_trace_ids": trace_ids,
        "selected_retrieval_result_ids": selected_result_ids,
        "rejected_retrieval_result_ids": rejected_result_ids,
        "graph_path_ids": graph_path_ids,
        "selected_graph_path_ids": graph_path_ids,
        "rejected_graph_path_ids": [
            str(row.get("graph_path_id"))
            for row in graph_rows
            if row.get("selected_status") == "rejected" and row.get("graph_path_id")
        ],
        "negative_evidence_spans": negative_evidence,
        "explicit_trigger_miss_evidence": trigger_miss_evidence,
        "search_coverage_certificate_ids": [],
        "human_adjudication_refs": [],
        "missing_evidence": missing_evidence,
        "contradiction_notes": contradiction_notes,
        "confidence_classification": confidence,
        "adjudication_state": (
            "required" if status == "needs_adjudication" else "not_required"
        ),
        "reviewer_notes": reviewer_notes,
        "freshness": dict(freshness),
    }


def _authority_family_ids_for_candidate(candidate: dict[str, Any]) -> list[str]:
    family_ids = set(_strings(candidate.get("authority_family_ids")))
    family_ids.update(_strings([candidate.get("authority_family_id")]))
    rule_template = candidate.get("rule_template")
    if isinstance(rule_template, dict):
        family_ids.update(_strings(rule_template.get("authority_family_ids")))
        family_ids.update(_strings([rule_template.get("authority_family_id")]))
    return sorted(family_ids)


def _assert_source_set_matches(
    source_set_id: str,
    authority_universe: dict[str, Any],
    package_fact_graph: dict[str, Any],
    package_context: dict[str, Any],
) -> None:
    mismatches = []
    for label, payload in (
        ("authority_universe", authority_universe),
        ("package_fact_graph", package_fact_graph),
        ("package_applicability_context", package_context),
    ):
        payload_source_set_id = str(payload.get("source_set_id") or "").strip()
        if payload_source_set_id and payload_source_set_id != source_set_id:
            mismatches.append(f"{label}={payload_source_set_id}")
    if mismatches:
        raise ValueError(
            f"Source-set mismatch for {source_set_id}: {', '.join(mismatches)}"
        )


def _validate_safe_segment(value: str | None, field_name: str) -> None:
    if not value or not SAFE_SEGMENT_RE.match(value):
        raise ValueError(f"{field_name} must be a safe path segment")


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"{label} is empty: {path}")
    return rows


def _read_jsonl_if_exists(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _optional_artifact_path(payload: dict[str, Any], key: str) -> Path | None:
    artifacts = payload.get("artifact_paths")
    if not isinstance(artifacts, dict):
        return None
    value = artifacts.get(key)
    if not value:
        return None
    return Path(str(value))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_and_hash(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return sha256_file(path)


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _stable_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(_strings(item))
        return values
    text = str(value).strip()
    return [text] if text else []
