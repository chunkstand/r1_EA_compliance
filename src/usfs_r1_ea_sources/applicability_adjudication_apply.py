from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json

from .applicability_adjudication import APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION
from .applicability_adjudication import ApplicabilityAdjudicationApplyResult
from .applicability_adjudication import UNRESOLVED_STATUSES
from .applicability_adjudication import _adjudication_items
from .applicability_adjudication import _decision_status
from .applicability_adjudication import _read_json_if_exists
from .applicability_adjudication import _read_required_json
from .applicability_adjudication import _read_required_jsonl
from .applicability_adjudication import _utc_now
from .applicability_adjudication import _validate_safe_segment
from .applicability_adjudication import _write_json
from .applicability_adjudication import _write_jsonl_and_hash
from .applicability_adjudication import evaluate_applicability_adjudication
from .applicability_decision_outputs import partition_authority_record
from .applicability_decision_outputs import write_decision_report
from .records import sha256_file


def apply_applicability_adjudication(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    adjudication_file: Path | None = None,
    decisions_path: Path | None = None,
    applicable_authorities_path: Path | None = None,
    non_applicable_authorities_path: Path | None = None,
    provenance_path: Path | None = None,
    output_path: Path | None = None,
) -> ApplicabilityAdjudicationApplyResult:
    """Replay completed adjudication into the decision ledger and partition artifacts."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    adjudication_file = Path(adjudication_file) if adjudication_file else (
        applicability_dir / "applicability_adjudication_template.json"
    )
    decisions_path = Path(decisions_path) if decisions_path else (
        applicability_dir / "applicability_decisions.jsonl"
    )
    applicable_authorities_path = Path(applicable_authorities_path) if (
        applicable_authorities_path
    ) else applicability_dir / "applicable_authorities.json"
    non_applicable_authorities_path = Path(non_applicable_authorities_path) if (
        non_applicable_authorities_path
    ) else applicability_dir / "non_applicable_authorities.json"
    provenance_path = Path(provenance_path) if provenance_path else (
        applicability_dir / "applicability_provenance.json"
    )
    output_path = Path(output_path) if output_path else (
        applicability_dir / "applicability_adjudication_apply.json"
    )
    eval_result = evaluate_applicability_adjudication(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        adjudication_file=adjudication_file,
        decisions_path=decisions_path,
    )
    if not eval_result.summary["passed"]:
        summary = {
            "schema_version": APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION,
            "created_at": _utc_now(),
            "review_id": review_id,
            "source_set_id": eval_result.source_set_id,
            "passed": False,
            "applied": False,
            "adjudication_eval_path": str(eval_result.output_path),
            "failure_category_counts": eval_result.summary.get(
                "failure_category_counts",
                {},
            ),
        }
        _write_json(
            output_path,
            {
                "schema_version": APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION,
                "summary": summary,
            },
        )
        return ApplicabilityAdjudicationApplyResult(
            review_id=review_id,
            source_set_id=eval_result.source_set_id,
            applicability_dir=applicability_dir,
            adjudication_file=adjudication_file,
            output_path=output_path,
            summary=summary,
        )

    adjudication = _read_required_json(adjudication_file, "applicability adjudication")
    decisions = _read_required_jsonl(decisions_path, "applicability decisions")
    original_decisions_sha256 = sha256_file(decisions_path)
    items_by_decision_id = {
        str(item.get("decision_id") or ""): item
        for item in _adjudication_items(adjudication)
        if item.get("decision_id")
    }
    applied_decisions = [
        _apply_adjudication_to_decision(
            decision=decision,
            item=items_by_decision_id.get(str(decision.get("decision_id") or "")),
            adjudication=adjudication,
            adjudication_eval_path=eval_result.output_path,
        )
        for decision in decisions
    ]
    new_decisions_sha256 = _write_jsonl_and_hash(decisions_path, applied_decisions)
    common = _partition_common(
        decisions=applied_decisions,
        decisions_sha256=new_decisions_sha256,
        existing_applicable=_read_json_if_exists(applicable_authorities_path),
        existing_non_applicable=_read_json_if_exists(non_applicable_authorities_path),
    )
    applicable_payload = {
        "schema_version": "applicable-authorities-v0",
        **common,
        "applicable_authority_count": sum(
            1 for decision in applied_decisions if _decision_status(decision) == "applicable"
        ),
        "authorities": [
            partition_authority_record(decision)
            for decision in applied_decisions
            if _decision_status(decision) == "applicable"
        ],
    }
    non_applicable_payload = {
        "schema_version": "non-applicable-authorities-v0",
        **common,
        "non_applicable_authority_count": sum(
            1
            for decision in applied_decisions
            if _decision_status(decision) == "not_applicable"
        ),
        "authorities": [
            partition_authority_record(decision)
            for decision in applied_decisions
            if _decision_status(decision) == "not_applicable"
        ],
    }
    _write_json(applicable_authorities_path, applicable_payload)
    _write_json(non_applicable_authorities_path, non_applicable_payload)
    report_summary = _decision_report_summary(
        review_id=review_id,
        source_set_id=eval_result.source_set_id,
        decisions=applied_decisions,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=(
            applicability_dir / "search_coverage_certificates.json"
        ),
    )
    write_decision_report(
        applicability_dir / "applicability_report.md",
        report_summary,
        applied_decisions,
    )
    applicable_authorities_sha256 = sha256_file(applicable_authorities_path)
    non_applicable_authorities_sha256 = sha256_file(non_applicable_authorities_path)
    summary = {
        "schema_version": APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": eval_result.source_set_id,
        "passed": True,
        "applied": True,
        "adjudication_file": str(adjudication_file),
        "adjudication_eval_path": str(eval_result.output_path),
        "decisions_path": str(decisions_path),
        "original_decisions_sha256": original_decisions_sha256,
        "applied_decisions_sha256": new_decisions_sha256,
        "applied_item_count": len(items_by_decision_id),
        "remaining_unresolved_authority_count": sum(
            1
            for decision in applied_decisions
            if _decision_status(decision) in UNRESOLVED_STATUSES
        ),
        "applicable_authorities_sha256": applicable_authorities_sha256,
        "non_applicable_authorities_sha256": non_applicable_authorities_sha256,
    }
    payload = {
        "schema_version": APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "review_id": review_id,
        "source_set_id": eval_result.source_set_id,
        "summary": summary,
    }
    _write_json(output_path, payload)
    _update_provenance_for_adjudication(
        provenance_path=provenance_path,
        adjudication_file=adjudication_file,
        adjudication_eval_path=eval_result.output_path,
        adjudication_apply_path=output_path,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
    )
    return ApplicabilityAdjudicationApplyResult(
        review_id=review_id,
        source_set_id=eval_result.source_set_id,
        applicability_dir=applicability_dir,
        adjudication_file=adjudication_file,
        output_path=output_path,
        summary=summary,
    )


def _apply_adjudication_to_decision(
    *,
    decision: dict[str, Any],
    item: dict[str, Any] | None,
    adjudication: dict[str, Any],
    adjudication_eval_path: Path,
) -> dict[str, Any]:
    if item is None:
        return dict(decision)
    updated = json.loads(json.dumps(decision))
    original = {
        "status": updated.get("status"),
        "basis_type": updated.get("basis_type"),
        "basis": updated.get("basis"),
        "adjudication_state": updated.get("adjudication_state"),
    }
    final_status = str(item.get("final_status") or "")
    adjudication_ref = {
        "adjudication_id": adjudication.get("adjudication_id"),
        "item_id": item.get("item_id"),
        "decision_id": item.get("decision_id"),
        "candidate_authority_id": item.get("candidate_authority_id"),
        "adjudication_file": adjudication.get("summary", {}).get("output_path")
        or adjudication.get("decisions_path"),
        "adjudication_eval_path": str(adjudication_eval_path),
        "final_status": final_status,
        "disposition": item.get("disposition"),
        "adjudicated_at": item.get("adjudicated_at"),
        "adjudicated_by": item.get("adjudicated_by") or [],
        "source_type": item.get("source_type"),
        "rationale": item.get("rationale"),
        "supporting_citation_refs": item.get("supporting_citation_refs") or [],
        "original": original,
    }
    updated["status"] = final_status
    updated["basis_type"] = "human_adjudication"
    updated["basis"] = {
        "rationale": item.get("rationale"),
        "disposition": item.get("disposition"),
        "source_type": item.get("source_type"),
        "original_status": original["status"],
        "original_basis_type": original["basis_type"],
    }
    updated["confidence_classification"] = "human_adjudicated"
    updated["adjudication_state"] = "resolved"
    updated["human_adjudication_refs"] = [
        *(updated.get("human_adjudication_refs") or []),
        adjudication_ref,
    ]
    updated["reviewer_notes"] = [
        *(updated.get("reviewer_notes") or []),
        str(item.get("reviewer_notes") or "").strip(),
    ]
    updated["reviewer_notes"] = [note for note in updated["reviewer_notes"] if note]
    updated["predicate_result"] = {
        **(updated.get("predicate_result") or {}),
        "status": final_status,
        "basis_type": "human_adjudication",
        "human_adjudicated": True,
    }
    deterministic = updated.get("deterministic_predicate")
    if isinstance(deterministic, dict):
        deterministic["predicate_result"] = {
            **(deterministic.get("predicate_result") or {}),
            "status": final_status,
            "basis_type": "human_adjudication",
            "human_adjudicated": True,
        }
    return updated


def _partition_common(
    *,
    decisions: list[dict[str, Any]],
    decisions_sha256: str,
    existing_applicable: dict[str, Any],
    existing_non_applicable: dict[str, Any],
) -> dict[str, Any]:
    source_payload = existing_applicable or existing_non_applicable or {}
    first_decision = decisions[0] if decisions else {}
    freshness = (
        first_decision.get("freshness")
        if isinstance(first_decision.get("freshness"), dict)
        else {}
    )
    return {
        "applicability_run_id": source_payload.get("applicability_run_id")
        or first_decision.get("applicability_run_id"),
        "review_id": source_payload.get("review_id") or first_decision.get("review_id"),
        "source_set_id": source_payload.get("source_set_id")
        or first_decision.get("source_set_id"),
        "created_at": _utc_now(),
        "authority_universe_sha256": source_payload.get("authority_universe_sha256")
        or freshness.get("authority_universe_sha256"),
        "package_manifest_sha256": source_payload.get("package_manifest_sha256")
        or freshness.get("package_manifest_sha256"),
        "package_chunks_sha256": source_payload.get("package_chunks_sha256")
        or freshness.get("package_chunks_sha256"),
        "package_fact_graph_sha256": source_payload.get("package_fact_graph_sha256")
        or freshness.get("package_fact_graph_sha256"),
        "retrieval_trace_sha256": source_payload.get("retrieval_trace_sha256")
        or freshness.get("retrieval_trace_sha256"),
        "graph_trace_sha256": source_payload.get("graph_trace_sha256")
        or freshness.get("graph_trace_sha256"),
        "search_coverage_certificates_sha256": source_payload.get(
            "search_coverage_certificates_sha256"
        )
        or freshness.get("search_coverage_certificates_sha256"),
        "applicability_decisions_sha256": decisions_sha256,
        "catalog_sha256": source_payload.get("catalog_sha256")
        or freshness.get("catalog_sha256"),
    }


def _decision_report_summary(
    *,
    review_id: str,
    source_set_id: str | None,
    decisions: list[dict[str, Any]],
    decisions_path: Path,
    applicable_authorities_path: Path,
    non_applicable_authorities_path: Path,
    search_coverage_certificates_path: Path,
) -> dict[str, Any]:
    status_counts = dict(sorted(Counter(_decision_status(row) for row in decisions).items()))
    unresolved_count = sum(status_counts.get(status, 0) for status in UNRESOLVED_STATUSES)
    return {
        "schema_version": "applicability-decision-summary-v0",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "applicability_run_id": decisions[0].get("applicability_run_id") if decisions else None,
        "validation_passed": bool(decisions),
        "generated_rule_pack_ready": unresolved_count == 0,
        "candidate_authority_count": len(decisions),
        "decision_status_counts": status_counts,
        "coverage_result_counts": {},
        "applicable_authority_count": status_counts.get("applicable", 0),
        "non_applicable_authority_count": status_counts.get("not_applicable", 0),
        "unresolved_authority_count": status_counts.get("unresolved", 0),
        "needs_adjudication_authority_count": status_counts.get("needs_adjudication", 0),
        "decisions_path": str(decisions_path),
        "applicable_authorities_path": str(applicable_authorities_path),
        "non_applicable_authorities_path": str(non_applicable_authorities_path),
        "search_coverage_certificates_path": str(search_coverage_certificates_path),
    }


def _update_provenance_for_adjudication(
    *,
    provenance_path: Path,
    adjudication_file: Path,
    adjudication_eval_path: Path,
    adjudication_apply_path: Path,
    decisions_path: Path,
    applicable_authorities_path: Path,
    non_applicable_authorities_path: Path,
) -> None:
    if not provenance_path.exists():
        return
    provenance = _read_required_json(provenance_path, "applicability provenance")
    entities = provenance.setdefault("entities", [])
    entities_by_id = {
        str(entity.get("entity_id") or ""): entity
        for entity in entities
        if isinstance(entity, dict)
    }
    for entity_id, path in (
        ("applicability_adjudication", adjudication_file),
        ("applicability_adjudication_eval", adjudication_eval_path),
        ("applicability_adjudication_apply", adjudication_apply_path),
    ):
        entity = entities_by_id.get(entity_id)
        if entity is None:
            entity = {"entity_id": entity_id}
            entities.append(entity)
            entities_by_id[entity_id] = entity
        entity["path"] = str(path)
        entity["sha256"] = sha256_file(path) if path.exists() else None
        entity["exists"] = path.exists()
    provenance.setdefault("activities", []).append(
        {
            "activity_id": f"activity:{provenance.get('applicability_run_id')}:adjudication-replay",
            "activity_type": "adjudication_replay",
            "command": "applicability-adjudication-apply",
            "started_at": _utc_now(),
            "ended_at": _utc_now(),
            "used_entity_ids": [
                "decision_ledger",
                "applicability_adjudication",
                "applicability_adjudication_eval",
            ],
            "generated_entity_ids": [
                "decision_ledger",
                "applicable_authorities",
                "non_applicable_authorities",
                "applicability_adjudication_apply",
            ],
        }
    )
    provenance.setdefault("relations", []).extend(
        [
            {
                "relation_type": "wasDerivedFrom",
                "generated_entity_id": generated,
                "used_entity_id": used,
            }
            for generated in (
                "decision_ledger",
                "applicable_authorities",
                "non_applicable_authorities",
            )
            for used in ("applicability_adjudication", "applicability_adjudication_eval")
        ]
    )
    for entity_id, path in (
        ("decision_ledger", decisions_path),
        ("applicable_authorities", applicable_authorities_path),
        ("non_applicable_authorities", non_applicable_authorities_path),
    ):
        entity = entities_by_id.get(entity_id)
        if entity is None:
            entity = {"entity_id": entity_id}
            entities.append(entity)
            entities_by_id[entity_id] = entity
        entity["path"] = str(path)
        entity["sha256"] = sha256_file(path) if path.exists() else None
        entity["exists"] = path.exists()
    _write_json(provenance_path, provenance)
