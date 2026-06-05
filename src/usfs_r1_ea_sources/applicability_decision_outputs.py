from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .records import sha256_file


APPLICABILITY_PROVENANCE_SCHEMA_VERSION = "applicability-provenance-v0"


def partition_authority_record(decision: dict[str, Any]) -> dict[str, Any]:
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
        "arbitration_status": decision.get("arbitration_status"),
        "decisive_trigger_groups": decision.get("decisive_trigger_groups") or [],
        "weak_auxiliary_trigger_groups": decision.get("weak_auxiliary_trigger_groups") or [],
        "arbitration_rationale": decision.get("arbitration_rationale"),
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


def decision_provenance(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    created_at: str,
    ended_at: str,
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
    selected_action_path: Path | None,
    source_set_manifest_path: Path | None,
    source_catalog_path: Path | None,
    authority_universe_sha256: str,
    source_set_manifest_sha256: str,
    package_manifest_sha256: str,
    package_chunks_sha256: str,
    package_fact_graph_sha256: str,
    selected_action_sha256: str,
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
        _prov_optional_entity("selected_action", selected_action_path, selected_action_sha256),
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
                "ended_at": ended_at,
                "used_entity_ids": [
                    "package_manifest",
                    "package_chunks",
                    "selected_action",
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
                "predicate_version": "deterministic-applicability-predicate-v0",
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
                "selected_action",
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
            "selected_action_sha256": selected_action_sha256,
        },
        "replay_notes": (
            "Run applicability-authority-universe, applicability-context-build, "
            "applicability-retrieve, then applicability-determine with the same inputs."
        ),
    }


def decision_summary(
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


def write_decision_report(
    path: Path,
    summary: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> None:
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
        if _should_report_arbitration(decision):
            lines.extend(_arbitration_report_lines(decision))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    return _prov_entity(
        path=path,
        entity_id=entity_id,
        sha256=sha256 or (sha256_file(path) if path.exists() else None),
    )


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


def _should_report_arbitration(decision: dict[str, Any]) -> bool:
    summary = decision.get("arbitration_summary")
    if not isinstance(summary, dict):
        return False
    if decision.get("status") == "needs_adjudication":
        return True
    return bool(
        summary.get("weak_auxiliary_trigger_groups")
        or summary.get("arbitration_notes")
    )


def _format_trigger_group(value: Any) -> str:
    return " + ".join(_strings(value))


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
