from __future__ import annotations

from typing import Any

from .nepa_knowledge_graph_export_models import _GraphBuilder
from .nepa_knowledge_graph_export_models import _authority_family_id_for_decision
from .nepa_knowledge_graph_export_models import _candidate_authority_node_id
from .nepa_knowledge_graph_export_models import _candidate_rule_id
from .nepa_knowledge_graph_export_models import _compliance_finding_node_id
from .nepa_knowledge_graph_export_models import _decision_display_status
from .nepa_knowledge_graph_export_models import _decision_node_id
from .nepa_knowledge_graph_export_models import _decision_readiness_blockers
from .nepa_knowledge_graph_export_models import _decision_review_readiness
from .nepa_knowledge_graph_export_models import _decision_status
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _dict_list
from .nepa_knowledge_graph_export_models import _family_ids_by_rule_id
from .nepa_knowledge_graph_export_models import _first_sorted
from .nepa_knowledge_graph_export_models import _generated_rule_node_id
from .nepa_knowledge_graph_export_models import _review_blocker_node_id
from .nepa_knowledge_graph_export_models import _review_evidence_node_id
from .nepa_knowledge_graph_export_models import _review_node_id
from .nepa_knowledge_graph_export_models import _review_validation_ready
from .nepa_knowledge_graph_export_models import _stable_digest
from .nepa_knowledge_graph_export_review_validation import _review_artifact_counts
from .nepa_knowledge_graph_export_review_validation import _review_overlay_summary


def _add_review_overlay(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    review_id: str,
    review_artifacts: dict[str, Any],
    inventory: dict[str, Any],
    rule_pack: dict[str, Any],
    base_rule_node_ids: dict[str, str],
    template_node_ids: dict[str, str],
) -> dict[str, Any]:
    authority_universe = _dict(review_artifacts.get("authority_universe_snapshot"))
    candidate_authorities = _dict_list(authority_universe.get("candidate_authorities"))
    decisions = _dict_list(review_artifacts.get("applicability_decisions"))
    search_coverage = _dict(review_artifacts.get("search_coverage_certificates"))
    generated_rule_pack = _dict(review_artifacts.get("generated_rule_pack"))
    compliance_matrix = _dict(review_artifacts.get("compliance_matrix"))
    applicability_validation = _dict(review_artifacts.get("applicability_validation"))
    generated_rule_pack_validation = _dict(review_artifacts.get("generated_rule_pack_validation"))
    compliance_validation = _dict(review_artifacts.get("compliance_validation"))

    family_ids_by_rule_id = _family_ids_by_rule_id(inventory)
    family_id_by_decision_id: dict[str, str] = {}
    review_node_id = _review_node_id(review_id)
    builder.add_node(
        node_id=review_node_id,
        node_type="review",
        label=review_id,
        display_status="active",
        review_readiness_status="reviewer_ready"
        if _review_validation_ready(applicability_validation, generated_rule_pack_validation)
        else "not_reviewer_ready",
        provenance={"review_id": review_id, "source_set_id": source_set_id},
        readiness_blockers=[]
        if _review_validation_ready(applicability_validation, generated_rule_pack_validation)
        else ["package_fixture_missing"],
        metadata={
            "applicability_validation_passed": applicability_validation.get("passed"),
            "generated_rule_pack_validation_passed": generated_rule_pack_validation.get("passed"),
            "compliance_validation_passed": compliance_validation.get("passed"),
            "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
            "generated_rule_pack_id": generated_rule_pack.get("generated_rule_pack_id"),
            "review_artifact_counts": _review_artifact_counts(review_artifacts),
        },
    )

    candidate_by_id = {
        str(candidate.get("candidate_authority_id")): candidate
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_id")
    }
    for candidate in sorted(candidate_authorities, key=lambda item: str(item.get("candidate_authority_id") or "")):
        _add_candidate_authority_overlay_node(
            builder,
            source_set_id=source_set_id,
            candidate=candidate,
            rule_pack=rule_pack,
            base_rule_node_ids=base_rule_node_ids,
            template_node_ids=template_node_ids,
        )

    for decision in sorted(decisions, key=lambda item: str(item.get("decision_id") or "")):
        candidate_id = str(decision.get("candidate_authority_id") or "")
        candidate = candidate_by_id.get(candidate_id, {})
        candidate_node_id = _candidate_authority_node_id(
            candidate or decision,
            base_rule_node_ids=base_rule_node_ids,
            template_node_ids=template_node_ids,
        )
        authority_family_id = _authority_family_id_for_decision(
            decision=decision,
            candidate=candidate,
            family_ids_by_rule_id=family_ids_by_rule_id,
        )
        family_id_by_decision_id[str(decision.get("decision_id") or "")] = authority_family_id
        status = _decision_status(decision)
        blockers = _decision_readiness_blockers(decision)
        decision_node_id = _decision_node_id(review_id, decision)
        builder.add_node(
            node_id=decision_node_id,
            node_type="applicability_decision",
            label=f"{candidate_id} {status}",
            display_status=_decision_display_status(decision),
            review_readiness_status=_decision_review_readiness(decision),
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "authority_family_id": authority_family_id,
                "decision_id": decision.get("decision_id"),
                "candidate_authority_id": candidate_id,
                "candidate_authority_type": decision.get("candidate_authority_type"),
            },
            currentness_metadata={
                "adjudication_state": decision.get("adjudication_state"),
                "basis_type": decision.get("basis_type"),
                "confidence_classification": decision.get("confidence_classification"),
            },
            readiness_blockers=blockers,
            metadata={
                "status": status,
                "applicability_status": status,
                "search_coverage_certificate_ids": decision.get(
                    "search_coverage_certificate_ids", []
                ),
                "human_adjudication_refs": decision.get("human_adjudication_refs", []),
                "retrieval_trace_ids": decision.get("retrieval_trace_ids", []),
                "selected_graph_path_ids": decision.get("selected_graph_path_ids", []),
            },
        )
        builder.update_node(
            candidate_node_id,
            display_status=_decision_display_status(decision),
            review_readiness_status=_decision_review_readiness(decision),
            readiness_blockers=blockers,
            metadata={
                "review_overlay": {
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "status": status,
                    "candidate_authority_id": candidate_id,
                }
            },
        )
        builder.add_edge(
            edge_type="PRODUCES_APPLICABILITY_DECISION",
            source_node_id=candidate_node_id,
            target_node_id=decision_node_id,
            display_status=_decision_display_status(decision),
            review_readiness_status=_decision_review_readiness(decision),
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "decision_id": decision.get("decision_id"),
                "candidate_authority_id": candidate_id,
            },
            readiness_blockers=blockers,
        )
        if status == "applicable":
            builder.add_edge(
                edge_type="APPLIES_TO_REVIEW",
                source_node_id=decision_node_id,
                target_node_id=review_node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "candidate_authority_id": candidate_id,
                },
            )
        elif status == "not_applicable":
            builder.add_edge(
                edge_type="NOT_APPLICABLE_TO_REVIEW",
                source_node_id=decision_node_id,
                target_node_id=review_node_id,
                display_status="not_applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "candidate_authority_id": candidate_id,
                    "search_coverage_certificate_ids": decision.get(
                        "search_coverage_certificate_ids", []
                    ),
                    "human_adjudication_refs": decision.get("human_adjudication_refs", []),
                },
            )
        else:
            blocker_node_id = _review_blocker_node_id(review_id, "adjudication_needed", decision)
            builder.add_node(
                node_id=blocker_node_id,
                node_type="readiness_blocker",
                label="Applicability adjudication needed",
                display_status="readiness_blocked",
                review_readiness_status="needs_adjudication",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "blocker_type": "adjudication_needed",
                    "decision_id": decision.get("decision_id"),
                },
                readiness_blockers=["adjudication_needed"],
            )
            builder.add_edge(
                edge_type="NEEDS_ADJUDICATION",
                source_node_id=decision_node_id,
                target_node_id=blocker_node_id,
                display_status="readiness_blocked",
                review_readiness_status="needs_adjudication",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "candidate_authority_id": candidate_id,
                },
                readiness_blockers=["adjudication_needed"],
            )
        if decision.get("human_adjudication_refs"):
            builder.add_edge(
                edge_type="ADJUDICATED_BY",
                source_node_id=decision_node_id,
                target_node_id=review_node_id,
                display_status="adjudicated",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "human_adjudication_refs": decision.get("human_adjudication_refs", []),
                },
            )

    generated_rule_node_ids = _add_generated_rules_overlay(
        builder,
        source_set_id=source_set_id,
        review_id=review_id,
        generated_rules=_dict_list(generated_rule_pack.get("rules")),
        decisions_by_id={str(decision.get("decision_id")): decision for decision in decisions},
        family_id_by_decision_id=family_id_by_decision_id,
        family_ids_by_rule_id=family_ids_by_rule_id,
    )
    _add_compliance_finding_overlay(
        builder,
        source_set_id=source_set_id,
        review_id=review_id,
        compliance_rows=_dict_list(compliance_matrix.get("rows")),
        generated_rule_node_ids=generated_rule_node_ids,
    )
    return _review_overlay_summary(
        review_id=review_id,
        candidate_authorities=candidate_authorities,
        decisions=decisions,
        generated_rules=_dict_list(generated_rule_pack.get("rules")),
        compliance_rows=_dict_list(compliance_matrix.get("rows")),
        search_coverage=search_coverage,
        review_artifacts=review_artifacts,
    )


def _add_candidate_authority_overlay_node(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    candidate: dict[str, Any],
    rule_pack: dict[str, Any],
    base_rule_node_ids: dict[str, str],
    template_node_ids: dict[str, str],
) -> None:
    node_id = _candidate_authority_node_id(
        candidate,
        base_rule_node_ids=base_rule_node_ids,
        template_node_ids=template_node_ids,
    )
    candidate_type = str(candidate.get("candidate_authority_type") or "")
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    if candidate_type == "forest_plan_component":
        forest_plan = _dict(candidate.get("forest_plan"))
        component_id = str(forest_plan.get("component_id") or candidate_id.rsplit(":", 1)[-1])
        forest_code = str(forest_plan.get("forest_unit_id") or "unknown_forest_unit")
        builder.add_node(
            node_id=node_id,
            node_type="forest_plan_component",
            label=str(forest_plan.get("section_heading") or component_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": forest_code,
                "candidate_authority_id": candidate_id,
            },
            metadata={
                "candidate_authority_type": candidate_type,
                "authority_category": candidate.get("authority_category"),
            },
        )
        return
    rule_id = _candidate_rule_id(candidate)
    builder.add_node(
        node_id=node_id,
        node_type="rule_template",
        label=rule_id,
        display_status="active",
        review_readiness_status="not_review_specific",
        provenance={
            "source_set_id": source_set_id,
            "rule_id": rule_id,
            "rule_pack_id": rule_pack.get("rule_pack_id"),
            "rule_pack_version": rule_pack.get("version"),
            "candidate_authority_id": candidate_id,
        },
        metadata={
            "candidate_authority_type": candidate_type,
            "authority_category": candidate.get("authority_category"),
            "required_package_fact_types": candidate.get("required_package_fact_types", []),
        },
    )


def _add_generated_rules_overlay(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    review_id: str,
    generated_rules: list[dict[str, Any]],
    decisions_by_id: dict[str, dict[str, Any]],
    family_id_by_decision_id: dict[str, str],
    family_ids_by_rule_id: dict[str, set[str]],
) -> dict[str, str]:
    generated_rule_node_ids: dict[str, str] = {}
    for rule in sorted(generated_rules, key=lambda item: str(item.get("generated_rule_id") or item.get("id") or "")):
        generated_rule_id = str(rule.get("generated_rule_id") or rule.get("id") or "")
        decision_id = str(rule.get("applicability_decision_id") or "")
        decision = decisions_by_id.get(decision_id, {})
        rule_id = str(rule.get("base_rule_id") or rule.get("id") or generated_rule_id)
        authority_family_id = (
            family_id_by_decision_id.get(decision_id)
            or _first_sorted(family_ids_by_rule_id.get(rule_id, set()))
            or "unknown_authority_family"
        )
        node_id = _generated_rule_node_id(review_id, generated_rule_id)
        generated_rule_node_ids[generated_rule_id] = node_id
        generated_rule_node_ids[rule_id] = node_id
        builder.add_node(
            node_id=node_id,
            node_type="generated_rule",
            label=str(rule.get("title") or generated_rule_id),
            display_status="applicable",
            review_readiness_status="reviewer_ready",
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "generated_rule_id": generated_rule_id,
                "authority_family_id": authority_family_id,
                "applicability_decision_id": decision_id,
                "candidate_authority_id": rule.get("candidate_authority_id"),
            },
            metadata={
                "rule_id": rule_id,
                "authority_category": rule.get("authority_category"),
                "authority_source_record_id": rule.get("authority_source_record_id"),
                "severity": rule.get("severity"),
                "applicability_mode": rule.get("applicability_mode"),
            },
        )
        if decision:
            builder.add_edge(
                edge_type="GENERATES_RULE",
                source_node_id=_decision_node_id(review_id, decision),
                target_node_id=node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision_id,
                    "generated_rule_id": generated_rule_id,
                },
            )
    return generated_rule_node_ids


def _add_compliance_finding_overlay(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    review_id: str,
    compliance_rows: list[dict[str, Any]],
    generated_rule_node_ids: dict[str, str],
) -> None:
    for row in sorted(compliance_rows, key=lambda item: str(item.get("rule_id") or item.get("row_id") or "")):
        finding_id = str(row.get("row_id") or row.get("rule_id") or "")
        if not finding_id:
            continue
        rule_id = str(row.get("rule_id") or finding_id)
        finding_node_id = _compliance_finding_node_id(review_id, finding_id)
        builder.add_node(
            node_id=finding_node_id,
            node_type="compliance_finding",
            label=str(row.get("rule_title") or rule_id),
            display_status="applicable",
            review_readiness_status="reviewer_ready",
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "finding_id": finding_id,
                "rule_id": rule_id,
            },
            metadata={
                "status": row.get("status"),
                "applicability_status": row.get("applicability_status"),
                "authority_category": row.get("authority_category"),
                "source_claim_ids": row.get("source_claim_ids", []),
                "candidate_authority_id": row.get("candidate_authority_id"),
            },
        )
        generated_rule_node_id = generated_rule_node_ids.get(rule_id)
        if generated_rule_node_id:
            builder.add_edge(
                edge_type="SUPPORTS_COMPLIANCE_FINDING",
                source_node_id=generated_rule_node_id,
                target_node_id=finding_node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "finding_id": finding_id,
                },
            )
        for evidence_kind in ("source_library_evidence", "ea_package_evidence"):
            evidence = _dict(row.get(evidence_kind))
            if not evidence:
                continue
            evidence_node_id = _review_evidence_node_id(review_id, finding_id, evidence_kind, evidence)
            builder.add_node(
                node_id=evidence_node_id,
                node_type="evidence_span",
                label=str(evidence.get("citation_label") or f"{finding_id} {evidence_kind}"),
                display_status="active",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "source_record_id": evidence.get("source_record_id"),
                    "chunk_index": evidence.get("chunk_index") or evidence.get("chunk_id") or 0,
                    "char_start": evidence.get("source_char_start")
                    if evidence.get("source_char_start") is not None
                    else evidence.get("chunk_char_start", 0),
                    "char_end": evidence.get("source_char_end")
                    if evidence.get("source_char_end") is not None
                    else evidence.get("chunk_char_end", 0),
                    "finding_id": finding_id,
                    "evidence_kind": evidence_kind,
                },
                metadata={
                    "artifact_sha256": evidence.get("artifact_sha256"),
                    "content_sha256": evidence.get("content_sha256"),
                    "citation_label": evidence.get("citation_label"),
                    "section": evidence.get("section"),
                    "page": evidence.get("page"),
                },
            )
            builder.add_edge(
                edge_type="SUPPORTS_COMPLIANCE_FINDING",
                source_node_id=evidence_node_id,
                target_node_id=finding_node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "finding_id": finding_id,
                    "evidence_kind": evidence_kind,
                    "source_record_id": evidence.get("source_record_id"),
                },
            )


def _add_blocker(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    subject_node_id: str,
    blockers: list[str],
) -> None:
    for blocker in sorted(set(blockers)):
        blocker_node_id = f"readiness_blocker:{blocker}:{_stable_digest(subject_node_id)[:16]}"
        builder.add_node(
            node_id=blocker_node_id,
            node_type="readiness_blocker",
            label=blocker.replace("_", " "),
            display_status="readiness_blocked",
            review_readiness_status="blocked",
            provenance={
                "source_set_id": source_set_id,
                "blocker_type": blocker,
                "subject_node_id": subject_node_id,
            },
        )
        builder.add_edge(
            edge_type="HAS_READINESS_BLOCKER",
            source_node_id=subject_node_id,
            target_node_id=blocker_node_id,
            display_status="readiness_blocked",
            review_readiness_status="blocked",
            provenance={
                "source_set_id": source_set_id,
                "blocker_type": blocker,
                "subject_node_id": subject_node_id,
            },
            readiness_blockers=[blocker],
        )
