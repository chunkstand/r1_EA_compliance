from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .evidence_strength import classify_evidence_strength
from .evidence_strength import evidence_strength_for_confidence
from .evidence_strength import is_weak_signal_text
from .records import sha256_file


APPLICABILITY_DECISIONS_SCHEMA_VERSION = "applicability-decisions-v0"
APPLICABLE_AUTHORITIES_SCHEMA_VERSION = "applicable-authorities-v0"
NON_APPLICABLE_AUTHORITIES_SCHEMA_VERSION = "non-applicable-authorities-v0"
SEARCH_COVERAGE_CERTIFICATES_SCHEMA_VERSION = "search-coverage-certificates-v0"
APPLICABILITY_PROVENANCE_SCHEMA_VERSION = "applicability-provenance-v0"
DETERMINISTIC_PREDICATE_VERSION = "deterministic-applicability-predicate-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
SOURCE_QUERY_TYPES = {
    "exact_keyword",
    "bm25",
    "metadata_filter",
    "source_role",
    "authority_category",
    "citation",
}
PACKAGE_QUERY_TYPES = {"package_section", "graph_seed"}


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
            _partition_authority_record(decision)
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
            _partition_authority_record(decision)
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

    summary = _summary(
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
    provenance_payload = _provenance(
        applicability_run_id=applicability_run_id,
        review_id=review_id,
        source_set_id=source_set_id,
        created_at=created_at,
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
    _write_report(report_path, summary, decisions)

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
    )
    negative_match = _trigger_match(
        groups=negative_groups,
        package_nodes=package_nodes,
        package_chunks=package_chunks,
        package_results=package_results,
        include_negative_context=True,
    )
    source_available = _source_evidence_available(candidate) or bool(source_evidence)
    missing_evidence: list[str] = []
    contradiction_notes: list[str] = []
    status = "unresolved"
    basis_type = "source_set_required"
    basis: dict[str, Any] = {}
    confidence = "low"
    predicate_name = "source_set_required"

    if not source_available:
        missing_evidence.append("required source evidence is unavailable")
        basis = {
            "rationale": "Required source-library evidence was not available for this authority.",
            "source_evidence_availability": candidate.get("source_evidence_availability") or {},
        }
    elif candidate.get("candidate_authority_type") == "forest_plan_component":
        component_result = _forest_plan_component_result(
            candidate=candidate,
            package_nodes=package_nodes,
            positive_match=positive_match,
            negative_match=negative_match,
            coverage_boundary=coverage_boundary,
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
            basis_type = "positive_package_trigger"
            basis = {
                "rationale": "Package evidence matched the authority's positive applicability trigger.",
                "matched_trigger_groups": positive_match["matched_groups"],
            }
            if positive_match["requires_adjudication"]:
                status = "needs_adjudication"
                basis_type = "unresolved_evidence_conflict"
                confidence = "needs_adjudication"
                contradiction_notes.extend(positive_match["adjudication_notes"])
            else:
                status = "applicable"
                confidence = "deterministic_high"
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
    }
    arbitration_summary = _arbitration_summary(
        status=status,
        basis_type=basis_type,
        predicate_name=predicate_name,
        positive_match=positive_match,
        negative_match=negative_match,
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
        },
        "arbitration_summary": arbitration_summary,
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
        "reviewer_notes": [],
        "freshness": dict(freshness),
    }


def _forest_plan_component_result(
    *,
    candidate: dict[str, Any],
    package_nodes: list[dict[str, Any]],
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
    coverage_boundary: dict[str, Any],
) -> dict[str, Any]:
    forest_plan = candidate.get("forest_plan") if isinstance(candidate.get("forest_plan"), dict) else {}
    required_values = {
        "geography": _strings(forest_plan.get("geographic_area_ids")),
        "management_area": _strings(forest_plan.get("management_area_ids")),
        "overlay": _strings(forest_plan.get("overlay_ids")),
    }
    present_values = _present_package_values(package_nodes)
    missing = []
    for fact_type, values in required_values.items():
        for value in values:
            if value not in present_values.get(fact_type, set()):
                missing.append(f"{fact_type}:{value}")
    trigger_required = bool(_trigger_groups(candidate.get("positive_trigger_groups")))
    trigger_matched = positive_match["matched"] if trigger_required else True
    if negative_match["requires_adjudication"]:
        return {
            "status": "needs_adjudication",
            "basis_type": "unresolved_evidence_conflict",
            "basis": {
                "rationale": "Forest Plan component negative scope evidence is weak or conflicting.",
                "matched_negative_trigger_groups": negative_match["matched_groups"],
            },
            "missing_evidence": missing,
            "contradiction_notes": negative_match["adjudication_notes"],
            "confidence": "needs_adjudication",
        }
    if negative_match["matched"]:
        basis = {
            "rationale": (
                "Package evidence matched an explicit negative Forest Plan component "
                "scope trigger."
            ),
            "matched_negative_trigger_groups": negative_match["matched_groups"],
            "matched_package_values": required_values if not missing else {},
            "matched_positive_trigger_groups": positive_match["matched_groups"],
            "missing_package_values": missing,
        }
        if coverage_boundary["coverage_sufficient"]:
            return {
                "status": "not_applicable",
                "basis_type": "negative_package_evidence",
                "basis": basis,
                "missing_evidence": [],
                "contradiction_notes": [],
                "confidence": "deterministic_high",
            }
        return {
            "status": "unresolved",
            "basis_type": "forest_plan_profile_resolution",
            "basis": basis,
            "missing_evidence": [*missing, "sufficient forest-plan search coverage"],
            "contradiction_notes": [],
            "confidence": "low",
        }
    if positive_match["requires_adjudication"]:
        return {
            "status": "needs_adjudication",
            "basis_type": "unresolved_evidence_conflict",
            "basis": {
                "rationale": "Forest Plan component trigger evidence is weak or conflicting.",
                "matched_trigger_groups": positive_match["matched_groups"],
            },
            "missing_evidence": missing,
            "contradiction_notes": positive_match["adjudication_notes"],
            "confidence": "needs_adjudication",
        }
    if not missing and trigger_matched:
        return {
            "status": "applicable",
            "basis_type": "forest_plan_component",
            "basis": {
                "rationale": "Package facts match the Forest Plan component scope.",
                "matched_package_values": required_values,
                "matched_trigger_groups": positive_match["matched_groups"],
            },
            "missing_evidence": [],
            "contradiction_notes": [],
            "confidence": "deterministic_high",
        }
    basis = {
        "rationale": "Required Forest Plan component package scope was not found.",
        "missing_package_values": missing,
        "missing_trigger_groups": [] if trigger_matched else candidate.get("positive_trigger_groups") or [],
    }
    if coverage_boundary["coverage_sufficient"]:
        return {
            "status": "not_applicable",
            "basis_type": "forest_plan_component",
            "basis": basis,
            "missing_evidence": missing,
            "contradiction_notes": [],
            "confidence": "deterministic_medium",
        }
    return {
        "status": "unresolved",
        "basis_type": "forest_plan_profile_resolution",
        "basis": basis,
        "missing_evidence": [*missing, "sufficient forest-plan search coverage"],
        "contradiction_notes": [],
        "confidence": "low",
    }


def _coverage_boundary(
    *,
    candidate: dict[str, Any],
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    requirements = candidate.get("search_coverage_requirements") or []
    required_query_types = sorted(
        {
            query_type
            for requirement in requirements
            for query_type in _strings(requirement.get("required_query_types"))
        }
        or set(
            _strings(
                (candidate.get("retrieval_contract") or {}).get("required_query_types")
            )
        )
    )
    executed_query_types = sorted(
        {
            str(row.get("query_type"))
            for row in retrieval_rows
            if str(row.get("query_type") or "")
        }
    )
    missing_query_types = sorted(set(required_query_types) - set(executed_query_types))
    source_hashes = sorted(
        {
            str((row.get("searched_index") or {}).get("searched_index_hash") or "")
            for row in retrieval_rows
            if row.get("query_type") in SOURCE_QUERY_TYPES
            and (row.get("searched_index") or {}).get("searched_index_hash")
        }
    )
    package_hashes = sorted(
        {
            str((row.get("searched_index") or {}).get("graph_artifact_hash") or "")
            for row in retrieval_rows
            if row.get("query_type") in PACKAGE_QUERY_TYPES
            and (row.get("searched_index") or {}).get("graph_artifact_hash")
        }
    )
    requires_source_index_hash = any(
        bool(requirement.get("requires_searched_index_hash"))
        for requirement in requirements
    )
    source_index_hash_required = requires_source_index_hash or any(
        query_type in SOURCE_QUERY_TYPES for query_type in required_query_types
    )
    graph_required = any(
        "applicability_graph_trace" in set(_strings(requirement.get("required_artifacts")))
        for requirement in requirements
    )
    coverage_sufficient = (
        bool(retrieval_rows)
        and not missing_query_types
        and (not source_index_hash_required or bool(source_hashes))
        and bool(package_hashes)
        and (not graph_required or bool(graph_rows))
    )
    return {
        "coverage_sufficient": coverage_sufficient,
        "required_query_variants": required_query_types,
        "executed_query_variants": executed_query_types,
        "missing_query_variants": missing_query_types,
        "package_sections_searched": sorted(
            {
                str(result.get("section_family"))
                for row in retrieval_rows
                for result in row.get("ranked_results") or []
                if result.get("result_kind") in {"package_fact", "package_section"}
                and result.get("section_family")
            }
        ),
        "source_indexes_searched": sorted(
            {
                str((row.get("searched_index") or {}).get("index_path") or "")
                for row in retrieval_rows
                if row.get("query_type") in SOURCE_QUERY_TYPES
                and (row.get("searched_index") or {}).get("index_path")
            }
        ),
        "metadata_filters_searched": [
            row.get("source_filters") or {}
            for row in retrieval_rows
            if row.get("query_type") in {"metadata_filter", "source_role"}
        ],
        "graph_neighborhoods_searched": sorted(
            {
                relationship
                for row in graph_rows
                for relationship in row.get("relationship_types") or []
                if relationship
            }
        ),
        "searched_artifact_hashes": sorted(set(source_hashes + package_hashes)),
        "source_index_hash_required": source_index_hash_required,
        "source_index_hash_present": bool(source_hashes),
        "package_graph_hash_present": bool(package_hashes),
        "required_artifacts": sorted(
            {
                artifact
                for requirement in requirements
                for artifact in _strings(requirement.get("required_artifacts"))
            }
        ),
        "coverage_classes": sorted(
            {
                str(requirement.get("coverage_class"))
                for requirement in requirements
                if requirement.get("coverage_class")
            }
        ),
    }


def _coverage_certificate(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    created_at: str,
    candidate: dict[str, Any],
    decision: dict[str, Any],
    coverage_boundary: dict[str, Any],
    authority_universe_sha256: str,
    package_fact_graph_sha256: str,
    retrieval_trace_sha256: str,
    graph_trace_sha256: str,
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_id = decision["candidate_authority_id"]
    coverage_result = "sufficient" if coverage_boundary["coverage_sufficient"] else "insufficient"
    if decision["status"] == "needs_adjudication":
        coverage_result = "adjudication_required"
    certificate_id = _stable_id(
        "search-coverage-certificate",
        applicability_run_id,
        candidate_id,
        decision["status"],
        decision["basis_type"],
    )
    rejected_ids = [
        str(result.get("result_id"))
        for row in retrieval_rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "rejected" and result.get("result_id")
    ]
    return {
        "coverage_certificate_id": certificate_id,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "authority_universe_sha256": authority_universe_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "covered_candidate_authority_ids": [candidate_id],
        "covered_decision_ids": [decision["decision_id"]],
        "coverage_class": decision["basis_type"],
        "required_query_variants": coverage_boundary["required_query_variants"],
        "executed_query_variants": coverage_boundary["executed_query_variants"],
        "missing_query_variants": coverage_boundary["missing_query_variants"],
        "package_sections_searched": coverage_boundary["package_sections_searched"],
        "source_indexes_searched": coverage_boundary["source_indexes_searched"],
        "metadata_filters_searched": coverage_boundary["metadata_filters_searched"],
        "graph_neighborhoods_searched": coverage_boundary["graph_neighborhoods_searched"],
        "searched_artifact_hashes": coverage_boundary["searched_artifact_hashes"],
        "coverage_result": coverage_result,
        "trigger_terms_searched": _flatten_groups(candidate.get("positive_trigger_groups")),
        "negative_trigger_terms_searched": _flatten_groups(
            candidate.get("negative_trigger_groups")
        ),
        "missing_trigger_groups": _missing_trigger_groups(decision),
        "rejected_evidence_ids": sorted(set(rejected_ids)),
        "graph_path_ids": [
            str(row.get("graph_path_id"))
            for row in graph_rows
            if row.get("graph_path_id")
        ],
        "rationale": _coverage_rationale(decision, coverage_result),
    }


def _coverage_rationale(decision: dict[str, Any], coverage_result: str) -> str:
    if coverage_result == "sufficient":
        return (
            "Required retrieval variants and graph neighborhoods were recorded for this "
            "authority predicate."
        )
    if coverage_result == "adjudication_required":
        return "Search coverage was recorded, but the predicate requires adjudication."
    return "Required retrieval variants or graph neighborhoods were missing."


def _missing_trigger_groups(decision: dict[str, Any]) -> list[list[str]]:
    basis_groups = decision.get("basis", {}).get("missing_trigger_groups")
    if basis_groups:
        return basis_groups
    for evidence in decision.get("explicit_trigger_miss_evidence") or []:
        groups = evidence.get("missing_trigger_groups")
        if groups:
            return groups
    return []


def _trigger_match(
    *,
    groups: list[list[str]],
    package_nodes: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
    package_results: list[dict[str, Any]],
    include_negative_context: bool = False,
) -> dict[str, Any]:
    if not groups:
        return {
            "matched": False,
            "matched_groups": [],
            "evidence_spans": [],
            "trigger_group_results": [],
            "requires_adjudication": False,
            "adjudication_notes": [],
        }
    searchable_nodes = [
        node
        for node in package_nodes
        if include_negative_context or node.get("confidence_class") != "negative_context"
    ]
    matched_groups = []
    evidence_by_id: dict[str, dict[str, Any]] = {}
    adjudication_notes = []
    group_results = []
    for group in groups:
        group_matched = False
        group_evidence_by_id: dict[str, dict[str, Any]] = {}
        weak_signal_reasons = []
        for node in searchable_nodes:
            node_text = _package_node_text(node)
            if not all(_term_in_text(term, node_text) for term in group):
                continue
            group_matched = True
            evidence = _package_evidence_span(node)
            evidence_by_id[evidence["evidence_id"]] = evidence
            group_evidence_by_id[evidence["evidence_id"]] = evidence
            if node.get("confidence_class") == "weak_signal":
                note = f"weak package signal for {node.get('node_id')}"
                adjudication_notes.append(note)
                weak_signal_reasons.append(note)
        for chunk in package_chunks:
            chunk_text = str(chunk.get("text") or "")
            if not all(_term_in_text(term, chunk_text) for term in group):
                continue
            group_matched = True
            evidence = _package_chunk_evidence_span(chunk, group)
            evidence_by_id[evidence["evidence_id"]] = evidence
            group_evidence_by_id[evidence["evidence_id"]] = evidence
            if evidence.get("confidence_class") == "weak_signal":
                note = f"weak package chunk signal for {chunk.get('chunk_id')}"
                adjudication_notes.append(note)
                weak_signal_reasons.append(note)
        for result in package_results:
            if not _result_matches_trigger_group(result, group):
                continue
            group_matched = True
            evidence = _package_result_span(result)
            evidence_by_id[evidence["evidence_id"]] = evidence
            group_evidence_by_id[evidence["evidence_id"]] = evidence
            if (result.get("provenance") or {}).get("confidence_class") == "weak_signal":
                note = f"weak retrieval result for {result.get('result_id')}"
                adjudication_notes.append(note)
                weak_signal_reasons.append(note)
        if group_matched:
            matched_groups.append(group)
        group_results.append(
            _trigger_group_diagnostic(
                group=group,
                matched=group_matched,
                evidence=list(group_evidence_by_id.values()),
                weak_signal_reasons=weak_signal_reasons,
            )
        )
    requires_adjudication = bool(adjudication_notes)
    return {
        "matched": bool(matched_groups),
        "matched_groups": matched_groups,
        "evidence_spans": sorted(evidence_by_id.values(), key=lambda item: item["evidence_id"]),
        "trigger_group_results": [
            _finalize_trigger_group_diagnostic(
                result,
                requires_adjudication=requires_adjudication,
            )
            for result in group_results
        ],
        "requires_adjudication": requires_adjudication,
        "adjudication_notes": sorted(set(adjudication_notes)),
    }


def _trigger_group_diagnostic(
    *,
    group: list[str],
    matched: bool,
    evidence: list[dict[str, Any]],
    weak_signal_reasons: list[str],
) -> dict[str, Any]:
    evidence_ids = sorted(str(item.get("evidence_id") or "") for item in evidence if item.get("evidence_id"))
    package_chunk_ids = sorted(
        {
            chunk_id
            for item in evidence
            for chunk_id in _strings(item.get("package_chunk_ids"))
        }
    )
    package_fact_node_ids = sorted(
        {
            str(item.get("package_fact_node_id"))
            for item in evidence
            if item.get("package_fact_node_id")
        }
    )
    retrieval_result_ids = sorted(
        {
            str(item.get("retrieval_result_id"))
            for item in evidence
            if item.get("retrieval_result_id")
        }
    )
    return {
        "trigger_group": list(group),
        "matched": matched,
        "diagnostic_treatment": "unmatched",
        "evidence_ids": evidence_ids,
        "package_evidence_ids": sorted(
            set(evidence_ids) - set(retrieval_result_ids)
        ),
        "package_chunk_ids": package_chunk_ids,
        "package_fact_node_ids": package_fact_node_ids,
        "retrieval_result_ids": retrieval_result_ids,
        "evidence_strength_counts": _evidence_strength_counts(evidence),
        "evidence_strength_class_counts": _evidence_strength_class_counts(evidence),
        "weak_signal_reasons": sorted(set(weak_signal_reasons)),
        "weak_signal_details": _weak_signal_details(evidence),
    }


def _finalize_trigger_group_diagnostic(
    result: dict[str, Any],
    *,
    requires_adjudication: bool,
) -> dict[str, Any]:
    if not result["matched"]:
        treatment = "unmatched"
    else:
        strength_counts = result.get("evidence_strength_counts") or {}
        weak_count = int(strength_counts.get("weak_signal") or 0)
        strong_count = sum(
            int(count)
            for strength, count in strength_counts.items()
            if strength != "weak_signal"
        )
        if weak_count and strong_count:
            treatment = "conflicting"
        elif weak_count:
            treatment = "weak_only"
        elif requires_adjudication:
            treatment = "auxiliary"
        else:
            treatment = "decisive"
    return {
        **result,
        "diagnostic_treatment": treatment,
    }


def _evidence_strength_counts(evidence: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        str(item.get("confidence_class") or "observed")
        for item in evidence
    )
    return dict(sorted(counts.items()))


def _evidence_strength_class_counts(evidence: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        str(
            (item.get("evidence_strength") or {}).get("strength_class")
            or item.get("confidence_class")
            or "observed"
        )
        for item in evidence
    )
    return dict(sorted(counts.items()))


def _weak_signal_details(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details = []
    for item in evidence:
        if item.get("confidence_class") != "weak_signal":
            continue
        strength = item.get("evidence_strength") or evidence_strength_for_confidence(
            item.get("confidence_class"),
            section_family=item.get("section_family"),
        )
        details.append(
            {
                "evidence_id": item.get("evidence_id"),
                "strength_class": strength.get("strength_class"),
                "reason": strength.get("reason"),
                "matched_phrase": strength.get("matched_phrase"),
                "matched_text": strength.get("matched_text"),
                "evidence_window": strength.get("evidence_window"),
                "section_family": strength.get("section_family") or item.get("section_family"),
            }
        )
    return sorted(
        details,
        key=lambda item: (
            str(item.get("evidence_id") or ""),
            str(item.get("strength_class") or ""),
            str(item.get("reason") or ""),
        ),
    )


def _arbitration_summary(
    *,
    status: str,
    basis_type: str,
    predicate_name: str,
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
    source_evidence: list[dict[str, Any]],
    selected_retrieval_result_ids: list[str],
    retrieval_trace_ids: list[str],
    graph_path_ids: list[str],
) -> dict[str, Any]:
    requires_adjudication = bool(
        positive_match.get("requires_adjudication")
        or negative_match.get("requires_adjudication")
    )
    notes = sorted(
        set(
            _strings(positive_match.get("adjudication_notes"))
            + _strings(negative_match.get("adjudication_notes"))
        )
    )
    return {
        "schema_version": "applicability-evidence-arbitration-v0",
        "diagnostic_only": True,
        "decision_effect": _arbitration_decision_effect(
            status=status,
            positive_match=positive_match,
            negative_match=negative_match,
        ),
        "status": status,
        "basis_type": basis_type,
        "predicate_name": predicate_name,
        "positive_trigger_matched": bool(positive_match.get("matched")),
        "negative_trigger_matched": bool(negative_match.get("matched")),
        "requires_adjudication": requires_adjudication,
        "positive_trigger_groups": positive_match.get("trigger_group_results") or [],
        "negative_trigger_groups": negative_match.get("trigger_group_results") or [],
        "arbitration_notes": notes,
        "source_evidence_ids": sorted(
            str(item.get("evidence_id"))
            for item in source_evidence
            if item.get("evidence_id")
        ),
        "selected_retrieval_result_ids": selected_retrieval_result_ids,
        "retrieval_trace_ids": retrieval_trace_ids,
        "graph_path_ids": graph_path_ids,
    }


def _arbitration_decision_effect(
    *,
    status: str,
    positive_match: dict[str, Any],
    negative_match: dict[str, Any],
) -> str:
    if status == "needs_adjudication" and positive_match.get("requires_adjudication"):
        return "blocked_by_weak_positive_trigger"
    if status == "needs_adjudication" and negative_match.get("requires_adjudication"):
        return "blocked_by_weak_negative_trigger"
    if status == "applicable" and positive_match.get("matched"):
        return "positive_trigger_decisive"
    if status == "not_applicable" and negative_match.get("matched"):
        return "negative_trigger_decisive"
    if status == "not_applicable":
        return "trigger_absence_decisive"
    return "diagnostic_no_effect"


def _source_library_evidence(
    retrieval_rows: list[dict[str, Any]],
    source_record_ids: list[str],
) -> list[dict[str, Any]]:
    source_record_filter = set(source_record_ids)
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in retrieval_rows:
        for result in row.get("ranked_results") or []:
            if result.get("selected_status") != "selected":
                continue
            if result.get("result_kind") != "source_chunk":
                continue
            source_record_id = str(result.get("source_record_id") or "")
            if source_record_filter and source_record_id not in source_record_filter:
                continue
            evidence_id = str(result.get("result_id") or "")
            evidence_by_id[evidence_id] = {
                "evidence_id": evidence_id,
                "retrieval_trace_id": row.get("retrieval_trace_id"),
                "retrieval_result_id": result.get("result_id"),
                "source_record_id": source_record_id,
                "source_chunk_id": result.get("source_chunk_id"),
                "citation_label": result.get("citation_label"),
                "page_label": result.get("page_label"),
                "char_start": result.get("char_start"),
                "char_end": result.get("char_end"),
                "source_claim_ids": _strings([result.get("claim_id")]),
                "text_excerpt": result.get("text_excerpt"),
                "text_hash": result.get("text_hash"),
            }
    return sorted(evidence_by_id.values(), key=lambda item: item["evidence_id"])


def _declared_source_library_evidence(
    candidate: dict[str, Any],
    source_record_ids: list[str],
) -> list[dict[str, Any]]:
    if not source_record_ids or not _source_evidence_available(candidate):
        return []
    required = candidate.get("required_source_evidence")
    if not isinstance(required, dict):
        required = {}
    chunk_ids = _strings(required.get("source_chunk_ids"))
    if not chunk_ids:
        evidence_pairs = [(source_record_id, None) for source_record_id in source_record_ids]
    elif len(source_record_ids) == 1:
        evidence_pairs = [
            (source_record_ids[0], chunk_id) for chunk_id in chunk_ids
        ]
    else:
        padded_chunk_ids = [*chunk_ids]
        if len(padded_chunk_ids) < len(source_record_ids):
            padded_chunk_ids = [
                *padded_chunk_ids,
                *([None] * (len(source_record_ids) - len(padded_chunk_ids))),
            ]
        evidence_pairs = list(zip(source_record_ids, padded_chunk_ids, strict=False))
    records_by_id = {
        str(record.get("source_record_id") or ""): record
        for record in candidate.get("source_records") or []
        if isinstance(record, dict)
    }
    evidence = []
    for source_record_id, chunk_id in evidence_pairs:
        source_record = records_by_id.get(source_record_id, {})
        evidence_id = _stable_id(
            "declared-source-evidence",
            str(candidate.get("candidate_authority_id") or ""),
            source_record_id,
            str(chunk_id or ""),
        )
        evidence.append(
            {
                "evidence_id": evidence_id,
                "evidence_origin": "authority_universe",
                "retrieval_trace_id": None,
                "retrieval_result_id": None,
                "source_record_id": source_record_id,
                "source_chunk_id": chunk_id,
                "citation_label": source_record.get("citation_label"),
                "page_label": None,
                "char_start": None,
                "char_end": None,
                "source_claim_ids": [],
                "text_excerpt": source_record.get("title"),
                "text_hash": None,
            }
        )
    return evidence


def _selected_package_results(retrieval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        result
        for row in retrieval_rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "selected"
        and result.get("result_kind") in {"package_fact", "package_section"}
    ]


def _retrieval_lineage(
    retrieval_rows: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    trace_ids = sorted(
        {
            str(row.get("retrieval_trace_id"))
            for row in retrieval_rows
            if row.get("retrieval_trace_id")
        }
    )
    selected = sorted(
        {
            str(result.get("result_id"))
            for row in retrieval_rows
            for result in row.get("ranked_results") or []
            if result.get("selected_status") == "selected" and result.get("result_id")
        }
    )
    rejected = sorted(
        {
            str(result.get("result_id"))
            for row in retrieval_rows
            for result in row.get("ranked_results") or []
            if result.get("selected_status") == "rejected" and result.get("result_id")
        }
    )
    return selected, rejected, trace_ids


def _package_fact_nodes(package_fact_graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        node
        for node in package_fact_graph.get("nodes") or []
        if isinstance(node, dict)
        and node.get("node_type") not in {"package_section", "evidence_span"}
    ]


def _package_evidence_span(node: dict[str, Any]) -> dict[str, Any]:
    evidence_strength = node.get("evidence_strength") or evidence_strength_for_confidence(
        node.get("confidence_class"),
        section_family=node.get("section_family"),
    )
    return {
        "evidence_id": str(node.get("node_id") or ""),
        "package_fact_node_id": node.get("node_id"),
        "package_chunk_ids": _strings(node.get("package_chunk_ids")),
        "citation_label": node.get("citation_label"),
        "section_family": node.get("section_family"),
        "page_label": node.get("page_label"),
        "char_start": node.get("char_start"),
        "char_end": node.get("char_end"),
        "matched_terms": _strings([node.get("raw_value"), node.get("normalized_value")]),
        "text_snippet": node.get("raw_value") or node.get("label"),
        "confidence_class": node.get("confidence_class"),
        "evidence_strength": evidence_strength,
        "evidence_span_ids": _strings(node.get("evidence_span_ids")),
        "text_hash": node.get("text_hash") or node.get("content_sha256"),
    }


def _package_result_span(result: dict[str, Any]) -> dict[str, Any]:
    provenance = result.get("provenance") or {}
    evidence_strength = provenance.get("evidence_strength") or evidence_strength_for_confidence(
        provenance.get("confidence_class"),
        section_family=result.get("section_family"),
    )
    return {
        "evidence_id": str(result.get("result_id") or ""),
        "retrieval_result_id": result.get("result_id"),
        "package_fact_node_id": result.get("package_fact_node_id"),
        "package_chunk_ids": _strings([result.get("package_chunk_id")]),
        "citation_label": result.get("citation_label"),
        "section_family": result.get("section_family"),
        "page_label": result.get("page_label"),
        "char_start": result.get("char_start"),
        "char_end": result.get("char_end"),
        "matched_terms": _strings(result.get("matched_terms")),
        "text_snippet": result.get("text_excerpt"),
        "confidence_class": provenance.get("confidence_class"),
        "evidence_strength": evidence_strength,
        "evidence_span_ids": _strings(provenance.get("evidence_span_ids")),
        "text_hash": result.get("text_hash"),
    }


def _package_chunk_evidence_span(chunk: dict[str, Any], group: list[str]) -> dict[str, Any]:
    text = str(chunk.get("text") or "")
    first_match = _first_trigger_match(text, group)
    chunk_start = first_match[1] if first_match else 0
    chunk_end = first_match[2] if first_match else min(len(text), 200)
    section_family = _section_family_from_chunk(chunk)
    evidence_strength = classify_evidence_strength(
        text=text,
        start=chunk_start,
        end=chunk_end,
        matched_text=first_match[0] if first_match else None,
        section_family=section_family,
    )
    absolute_start = _absolute_offset(chunk.get("char_start"), chunk_start)
    absolute_end = _absolute_offset(chunk.get("char_start"), chunk_end)
    evidence_id = _stable_id(
        "package-trigger-span",
        str(chunk.get("chunk_id") or ""),
        str(chunk_start),
        str(chunk_end),
        hashlib.sha256("|".join(group).encode("utf-8")).hexdigest(),
    )
    return {
        "evidence_id": evidence_id,
        "package_fact_node_id": None,
        "package_chunk_ids": _strings([chunk.get("chunk_id")]),
        "citation_label": chunk.get("citation_label"),
        "section_family": section_family,
        "page_label": _page_label(chunk),
        "char_start": absolute_start,
        "char_end": absolute_end,
        "matched_terms": group,
        "text_snippet": _context_excerpt(text, chunk_start, chunk_end),
        "confidence_class": evidence_strength["confidence_class"],
        "evidence_strength": evidence_strength,
        "evidence_span_ids": [],
        "text_hash": chunk.get("content_sha256"),
    }


def _first_trigger_match(text: str, group: list[str]) -> tuple[str, int, int] | None:
    lower_text = text.lower()
    matches = []
    for term in group:
        normalized = term.lower()
        index = lower_text.find(normalized)
        if index >= 0:
            matches.append((term, index, index + len(term)))
    if not matches:
        return None
    return sorted(matches, key=lambda item: item[1])[0]


def _present_package_values(package_nodes: list[dict[str, Any]]) -> dict[str, set[str]]:
    values: dict[str, set[str]] = defaultdict(set)
    for node in package_nodes:
        if node.get("confidence_class") == "negative_context":
            continue
        node_type = str(node.get("node_type") or "")
        normalized_value = str(node.get("normalized_value") or "")
        if node_type and normalized_value:
            values[node_type].add(normalized_value)
    return values


def _source_evidence_available(candidate: dict[str, Any]) -> bool:
    availability = candidate.get("source_evidence_availability")
    if isinstance(availability, dict) and availability.get("available"):
        return True
    required = candidate.get("required_source_evidence")
    if isinstance(required, dict) and not required.get("requires_source_record", True):
        return True
    return False


def _authority_family_ids_for_candidate(candidate: dict[str, Any]) -> list[str]:
    family_ids = set(_strings(candidate.get("authority_family_ids")))
    family_ids.update(_strings([candidate.get("authority_family_id")]))
    rule_template = candidate.get("rule_template")
    if isinstance(rule_template, dict):
        family_ids.update(_strings(rule_template.get("authority_family_ids")))
        family_ids.update(_strings([rule_template.get("authority_family_id")]))
    return sorted(family_ids)


def _partition_authority_record(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": decision["decision_id"],
        "candidate_authority_id": decision["candidate_authority_id"],
        "candidate_authority_type": decision.get("candidate_authority_type"),
        "authority_family_ids": decision.get("authority_family_ids") or [],
        "authority_family_id": decision.get("authority_family_id"),
        "status": decision["status"],
        "applicability_basis": decision["basis"],
        "non_applicability_basis": decision["basis"]
        if decision["status"] == "not_applicable"
        else None,
        "basis_type": decision["basis_type"],
        "generated_rule_metadata": _generated_rule_metadata(decision),
        "predicate_result": decision["predicate_result"],
        "retrieval_trace_ids": decision["retrieval_trace_ids"],
        "graph_path_ids": decision["graph_path_ids"],
        "source_record_ids": decision["source_record_ids"],
        "authority_category": decision.get("authority_category"),
        "authority_document_role": decision.get("authority_document_role"),
        "rule_template": decision.get("rule_template"),
        "forest_plan": decision.get("forest_plan"),
        "package_evidence_spans": decision["package_evidence_spans"],
        "source_library_evidence_spans": decision["source_library_evidence_spans"],
        "negative_evidence_spans": decision["negative_evidence_spans"],
        "explicit_trigger_miss_evidence": decision["explicit_trigger_miss_evidence"],
        "search_coverage_certificate_ids": decision["search_coverage_certificate_ids"],
        "human_adjudication_refs": decision["human_adjudication_refs"],
    }


def _generated_rule_metadata(decision: dict[str, Any]) -> dict[str, Any]:
    rule_template = decision.get("rule_template")
    if isinstance(rule_template, dict):
        return {
            "source_base_rule_id": rule_template.get("rule_id"),
            "authority_family_ids": decision.get("authority_family_ids") or [],
            "authority_family_id": decision.get("authority_family_id")
            or rule_template.get("authority_family_id"),
            "base_rule_pack_id": rule_template.get("base_rule_pack_id"),
            "base_rule_pack_version": rule_template.get("base_rule_pack_version"),
            "title": rule_template.get("title"),
            "severity": rule_template.get("severity"),
        }
    forest_plan = decision.get("forest_plan")
    if isinstance(forest_plan, dict):
        return {
            "forest_unit_id": forest_plan.get("forest_unit_id"),
            "component_inventory_id": forest_plan.get("component_inventory_id"),
            "component_id": forest_plan.get("component_id"),
            "component_type": forest_plan.get("component_type"),
            "section_heading": forest_plan.get("section_heading"),
        }
    return {}


def _provenance(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    created_at: str,
    authority_universe_path: Path,
    package_fact_graph_path: Path,
    package_applicability_context_path: Path,
    retrieval_trace_path: Path,
    graph_trace_path: Path,
    decisions_path: Path,
    applicable_authorities_path: Path,
    non_applicable_authorities_path: Path,
    search_coverage_certificates_path: Path,
    package_manifest_path: Path | None,
    package_chunks_path: Path | None,
    source_set_manifest_path: Path | None,
    source_catalog_path: Path | None,
    authority_universe_sha256: str,
    source_set_manifest_sha256: str,
    package_manifest_sha256: str,
    package_chunks_sha256: str,
    package_fact_graph_sha256: str,
    retrieval_trace_sha256: str,
    graph_trace_sha256: str,
    search_coverage_certificates_sha256: str,
    decisions_sha256: str,
    applicable_authorities_sha256: str,
    non_applicable_authorities_sha256: str,
) -> dict[str, Any]:
    entities = [
        _prov_optional_entity(
            "package_manifest",
            package_manifest_path,
            package_manifest_sha256,
        ),
        _prov_optional_entity("package_chunks", package_chunks_path, package_chunks_sha256),
        _prov_optional_entity(
            "source_set_manifest",
            source_set_manifest_path,
            source_set_manifest_sha256,
        ),
        _prov_optional_entity("catalog", source_catalog_path, None),
        _prov_entity("authority_universe", authority_universe_path, authority_universe_sha256),
        _prov_entity("package_fact_graph", package_fact_graph_path, package_fact_graph_sha256),
        _prov_entity(
            "package_applicability_context",
            package_applicability_context_path,
            sha256_file(package_applicability_context_path),
        ),
        _prov_entity("retrieval_trace", retrieval_trace_path, retrieval_trace_sha256),
        _prov_entity("graph_trace", graph_trace_path, graph_trace_sha256),
        _prov_entity("decision_ledger", decisions_path, decisions_sha256),
        _prov_entity(
            "search_coverage_certificates",
            search_coverage_certificates_path,
            search_coverage_certificates_sha256,
        ),
        _prov_entity(
            "applicable_authorities",
            applicable_authorities_path,
            applicable_authorities_sha256,
        ),
        _prov_entity(
            "non_applicable_authorities",
            non_applicable_authorities_path,
            non_applicable_authorities_sha256,
        ),
    ]
    return {
        "schema_version": APPLICABILITY_PROVENANCE_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "entities": entities,
        "activities": [
            {
                "activity_id": f"activity:{applicability_run_id}:deterministic-predicate-evaluation",
                "activity_type": "deterministic_predicate_evaluation",
                "command": "applicability-determine",
                "started_at": created_at,
                "ended_at": _utc_now(),
                "used_entity_ids": [
                    "package_manifest",
                    "package_chunks",
                    "source_set_manifest",
                    "catalog",
                    "authority_universe",
                    "package_fact_graph",
                    "package_applicability_context",
                    "retrieval_trace",
                    "graph_trace",
                ],
                "generated_entity_ids": [
                    "decision_ledger",
                    "search_coverage_certificates",
                    "applicable_authorities",
                    "non_applicable_authorities",
                ],
            }
        ],
        "agents": [
            {
                "agent_id": "deterministic-applicability-engine",
                "agent_type": "software",
                "predicate_version": DETERMINISTIC_PREDICATE_VERSION,
            }
        ],
        "relations": [
            {
                "relation_type": "wasDerivedFrom",
                "generated_entity_id": generated,
                "used_entity_id": used,
            }
            for generated in (
                "decision_ledger",
                "search_coverage_certificates",
                "applicable_authorities",
                "non_applicable_authorities",
            )
            for used in (
                "package_manifest",
                "package_chunks",
                "source_set_manifest",
                "catalog",
                "authority_universe",
                "package_fact_graph",
                "package_applicability_context",
                "retrieval_trace",
                "graph_trace",
            )
        ],
        "freshness": {
            "package_manifest_sha256": package_manifest_sha256,
            "package_chunks_sha256": package_chunks_sha256,
        },
        "replay_notes": (
            "Run applicability-authority-universe, applicability-context-build, "
            "applicability-retrieve, then applicability-determine with the same inputs."
        ),
    }


def _prov_entity(entity_id: str, path: Path, sha256: str | None) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "path": str(path),
        "sha256": sha256,
        "exists": path.exists(),
    }


def _prov_optional_entity(
    entity_id: str,
    path: Path | None,
    sha256: str | None,
) -> dict[str, Any]:
    if path is None:
        return {
            "entity_id": entity_id,
            "path": None,
            "sha256": sha256 or None,
            "exists": False,
        }
    return _prov_entity(entity_id, path, sha256 or (sha256_file(path) if path.exists() else None))


def _summary(
    *,
    review_id: str,
    source_set_id: str,
    applicability_run_id: str,
    decisions: list[dict[str, Any]],
    certificates: list[dict[str, Any]],
    decisions_path: Path,
    applicable_authorities_path: Path,
    non_applicable_authorities_path: Path,
    search_coverage_certificates_path: Path,
) -> dict[str, Any]:
    status_counts = dict(sorted(Counter(decision["status"] for decision in decisions).items()))
    certificate_counts = dict(
        sorted(Counter(certificate["coverage_result"] for certificate in certificates).items())
    )
    unresolved_count = status_counts.get("unresolved", 0)
    needs_adjudication_count = status_counts.get("needs_adjudication", 0)
    return {
        "schema_version": "applicability-decision-summary-v0",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "applicability_run_id": applicability_run_id,
        "validation_passed": len(decisions) > 0
        and all(decision.get("candidate_authority_id") for decision in decisions),
        "generated_rule_pack_ready": unresolved_count == 0 and needs_adjudication_count == 0,
        "candidate_authority_count": len(decisions),
        "decision_status_counts": status_counts,
        "coverage_result_counts": certificate_counts,
        "applicable_authority_count": status_counts.get("applicable", 0),
        "non_applicable_authority_count": status_counts.get("not_applicable", 0),
        "unresolved_authority_count": unresolved_count,
        "needs_adjudication_authority_count": needs_adjudication_count,
        "decisions_path": str(decisions_path),
        "applicable_authorities_path": str(applicable_authorities_path),
        "non_applicable_authorities_path": str(non_applicable_authorities_path),
        "search_coverage_certificates_path": str(search_coverage_certificates_path),
    }


def _write_report(path: Path, summary: dict[str, Any], decisions: list[dict[str, Any]]) -> None:
    lines = [
        "# Applicability Decision Report",
        "",
        f"- Review ID: `{summary['review_id']}`",
        f"- Applicability run ID: `{summary['applicability_run_id']}`",
        f"- Source set ID: `{summary['source_set_id']}`",
        f"- Candidate authorities: `{summary['candidate_authority_count']}`",
        f"- Decision counts: `{summary['decision_status_counts']}`",
        f"- Generated rule pack ready: `{summary['generated_rule_pack_ready']}`",
        "",
        "## Decisions",
        "",
    ]
    for decision in decisions:
        lines.append(
            "- "
            f"`{decision['candidate_authority_id']}`: "
            f"`{decision['status']}` / `{decision['basis_type']}`"
        )
        if decision["status"] == "needs_adjudication":
            lines.extend(_arbitration_report_lines(decision))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _arbitration_report_lines(decision: dict[str, Any]) -> list[str]:
    summary = decision.get("arbitration_summary")
    if not isinstance(summary, dict):
        return []
    lines = [
        f"  - Arbitration: `{summary.get('decision_effect')}`",
    ]
    positive_groups = summary.get("positive_trigger_groups") or []
    interesting_groups = [
        group
        for group in positive_groups
        if group.get("matched")
        and group.get("diagnostic_treatment") in {"auxiliary", "weak_only", "conflicting"}
    ]
    if interesting_groups:
        lines.append("  - Positive trigger diagnostics:")
        for group in interesting_groups:
            lines.append(
                "    - "
                f"`{_format_trigger_group(group.get('trigger_group'))}`: "
                f"`{group.get('diagnostic_treatment')}` "
                f"evidence=`{len(group.get('evidence_ids') or [])}` "
                f"strengths=`{group.get('evidence_strength_counts') or {}}` "
                f"classes=`{group.get('evidence_strength_class_counts') or {}}`"
            )
    notes = _strings(summary.get("arbitration_notes"))
    if notes:
        lines.append(f"  - Weak-signal notes: `{notes}`")
    return lines


def _format_trigger_group(value: Any) -> str:
    return " + ".join(_strings(value))


def _records_by_candidate(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_candidate[str(record.get("candidate_authority_id") or "")].append(record)
    return by_candidate


def _trigger_groups(value: Any) -> list[list[str]]:
    groups = []
    for group in value or []:
        terms = _strings(group)
        if terms:
            groups.append(terms)
    return groups


def _flatten_groups(value: Any) -> list[str]:
    return sorted({term for group in _trigger_groups(value) for term in group})


def _package_node_text(node: dict[str, Any]) -> str:
    return " ".join(
        str(value or "")
        for value in (
            node.get("label"),
            node.get("raw_value"),
            node.get("normalized_value"),
            node.get("fact_subtype"),
            node.get("section_family"),
            node.get("context_excerpt"),
            node.get("matched_text"),
        )
    )


def _result_matches_trigger_group(result: dict[str, Any], group: list[str]) -> bool:
    matched_terms = " ".join(_strings(result.get("matched_terms")))
    result_text = " ".join(
        str(value or "")
        for value in (
            matched_terms,
            result.get("text_excerpt"),
            (result.get("provenance") or {}).get("normalized_value"),
            (result.get("provenance") or {}).get("fact_subtype"),
        )
    )
    return all(_term_in_text(term, result_text) for term in group)


def _term_in_text(term: str, text: str) -> bool:
    raw_term = str(term or "").strip()
    if not raw_term:
        return False
    if len(raw_term) <= 3 and raw_term.replace(".", "").isalnum():
        return bool(
            re.search(
                rf"(?<![A-Za-z0-9]){re.escape(raw_term)}(?![A-Za-z0-9])",
                text,
                flags=re.IGNORECASE,
            )
        )
    normalized_term = raw_term.lower()
    return normalized_term in text.lower()


def _is_weak_signal_text(text: str, start: int, end: int) -> bool:
    return is_weak_signal_text(text, start, end)


def _sentence_around(text: str, start: int, end: int) -> str:
    sentence_start = max(
        text.rfind(".", 0, start),
        text.rfind("\n", 0, start),
        text.rfind(";", 0, start),
    )
    sentence_end_candidates = [
        index for index in (text.find(".", end), text.find("\n", end), text.find(";", end)) if index >= 0
    ]
    sentence_end = min(sentence_end_candidates) if sentence_end_candidates else len(text)
    return text[sentence_start + 1 : sentence_end + 1]


def _context_excerpt(text: str, start: int, end: int, radius: int = 160) -> str:
    excerpt_start = max(0, start - radius)
    excerpt_end = min(len(text), end + radius)
    prefix = "..." if excerpt_start > 0 else ""
    suffix = "..." if excerpt_end < len(text) else ""
    return f"{prefix}{text[excerpt_start:excerpt_end].strip()}{suffix}"


def _absolute_offset(base: Any, offset: int) -> int:
    try:
        return int(base) + offset
    except (TypeError, ValueError):
        return offset


def _page_label(chunk: dict[str, Any]) -> str | None:
    value = chunk.get("page_label") or chunk.get("page")
    return str(value) if value is not None else None


def _section_family_from_chunk(chunk: dict[str, Any]) -> str | None:
    values = " ".join(str(chunk.get(key) or "").lower() for key in ("section", "heading"))
    if "no action" in values:
        return "no_action"
    if "cumulative" in values:
        return "cumulative_effects"
    if "purpose" in values or "need" in values:
        return "purpose_need"
    if "affected" in values or "environment" in values:
        return "affected_environment"
    if "consequence" in values or "effect" in values:
        return "environmental_consequences"
    if "alternative" in values:
        return "alternatives"
    if "public" in values or "scoping" in values:
        return "public_involvement"
    if "decision" in values or "finding" in values:
        return "finding_decision"
    return None


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
