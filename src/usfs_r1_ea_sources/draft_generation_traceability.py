from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .artifact_utils import _dict
from .artifact_utils import _dict_list
from .draft_generation_common import _missing_citation_refs
from .draft_generation_common import _string_list
from .draft_generation_common import DraftGenerationContext


def _trace_seed_from_bundles(
    *,
    context: DraftGenerationContext,
    bundles: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    source_passages = []
    authority_family_ids: list[str] = []
    graph_path_ids: list[str] = []
    retrieval_trace_ids: list[str] = []
    review_decision_refs: list[dict[str, Any]] = []
    unresolved_issue_refs: list[str] = []
    missing_evidence_refs: list[str] = []
    residual_risk_refs: list[str] = []
    rule_ids: list[str] = []
    for bundle in bundles:
        decision_row = _dict(bundle.get("decision_support"))
        explanation = _dict(bundle.get("explanation"))
        packet = _dict(bundle.get("packet"))
        rule_id = str(bundle.get("rule_id") or "")
        if rule_id:
            rule_ids.append(rule_id)
        package_evidence = _dict_list(decision_row.get("ea_package_evidence"))
        source_evidence = _dict_list(decision_row.get("source_library_evidence"))
        source_passages.extend(package_evidence)
        source_passages.extend(source_evidence)
        authority_family_ids.extend(_string_list(decision_row.get("authority_family_ids")))
        authority_family_ids.extend(_string_list(explanation.get("authority_family_ids")))
        graph_path_ids.extend(_string_list(explanation.get("graph_path_ids")))
        retrieval_trace_ids.extend(_string_list(explanation.get("retrieval_trace_ids")))
        unresolved_issue_refs.extend(_string_list(explanation.get("unresolved_issue_refs")))
        residual_risk_refs.extend(_string_list(explanation.get("residual_risk_categories")))
        missing_evidence_refs.extend(
            _missing_citation_refs(
                evidence_rows=package_evidence,
                rule_id=rule_id,
                evidence_kind="package",
            )
        )
        missing_evidence_refs.extend(
            _missing_citation_refs(
                evidence_rows=source_evidence,
                rule_id=rule_id,
                evidence_kind="source_library",
            )
        )
        review_decision_refs.extend(
            [
                {
                    "artifact_path": str(context.review_dir / "compliance_review.json"),
                    "selector": f"findings[rule_id={rule_id}]",
                },
                {
                    "artifact_path": str(context.review_dir / "authority_explanation_paths.json"),
                    "selector": f"finding_explanation_paths[finding_id={rule_id}]",
                },
                {
                    "artifact_path": str(
                        context.review_dir
                        / "decision_support"
                        / "ea_consistency_decision_support.json"
                    ),
                    "selector": f"authority_findings[rule_id={rule_id}]",
                },
            ]
        )
        review_decision_refs.extend(_dict_list(packet.get("canonical_selectors")))
    return {
        "source_passages": source_passages,
        "authority_family_ids": authority_family_ids,
        "graph_path_ids": graph_path_ids,
        "retrieval_trace_ids": retrieval_trace_ids,
        "review_decision_refs": review_decision_refs,
        "unresolved_issue_refs": unresolved_issue_refs,
        "missing_evidence_refs": missing_evidence_refs,
        "residual_risk_refs": residual_risk_refs,
        "rule_ids": rule_ids,
    }


def _trace_seed_from_confirmation(
    *,
    context: DraftGenerationContext,
    confirmation: dict[str, Any],
    bundles: list[dict[str, Any]],
) -> dict[str, Any]:
    seed = _trace_seed_from_bundles(context=context, bundles=bundles)
    evidence_rows = _dict_list(confirmation.get("evidence"))
    seed["source_passages"].extend(evidence_rows)
    seed["review_decision_refs"].extend(_dict_list(confirmation.get("source_selectors")))
    seed["review_decision_refs"].extend(
        {
            "artifact_path": str(
                context.review_dir
                / "decision_support"
                / "ea_consistency_decision_support.json"
            ),
            "selector": (
                "implementation_confirmation_checklist"
                f"[confirmation_id={confirmation.get('confirmation_id')}]"
            ),
        }
        for _ in [0]
    )
    seed["unresolved_issue_refs"].append(str(confirmation.get("confirmation_id") or ""))
    seed["missing_evidence_refs"].extend(
        _missing_citation_refs(
            evidence_rows=evidence_rows,
            rule_id=str(confirmation.get("confirmation_id") or "confirmation"),
            evidence_kind="implementation_confirmation",
        )
    )
    return seed


def _trace_seed_from_accepted_risk(
    *,
    context: DraftGenerationContext,
    risk: dict[str, Any],
    bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    seed = _trace_seed_from_bundles(context=context, bundles=[bundle] if bundle else [])
    if not bundle:
        for source_record_id in _string_list(risk.get("source_record_ids")):
            seed["source_passages"].append(
                {
                    "source_record_id": source_record_id,
                    "citation_label": source_record_id,
                }
            )
    seed["review_decision_refs"].append(
        {
            "artifact_path": str(
                context.review_dir / "final_qa" / "east_crazies_final_qa_certification.json"
            ),
            "selector": f"accepted_v1_risk_ledger.risks[rule_id={risk.get('rule_id')}]",
        }
    )
    seed["residual_risk_refs"].append(f"accepted-risk:{risk.get('rule_id')}")
    seed["unresolved_issue_refs"].append(str(risk.get("rule_id") or ""))
    return seed


def _trace_seed_from_pending_resolution(
    *,
    context: DraftGenerationContext,
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_passages": [
            {
                "source_record_id": source_record_id,
                "citation_label": source_record_id,
            }
            for source_record_id in _string_list(row.get("source_record_ids"))
        ],
        "authority_family_ids": _string_list(row.get("authority_family_ids")),
        "graph_path_ids": _string_list(row.get("graph_path_ids")),
        "retrieval_trace_ids": _string_list(row.get("retrieval_trace_ids")),
        "review_decision_refs": [
            {
                "artifact_path": str(context.review_dir / "authority_explanation_paths.json"),
                "selector": "pending_resolution_paths",
            }
        ],
        "unresolved_issue_refs": [
            str(
                row.get("decision_id")
                or row.get("authority_explanation_id")
                or "pending-resolution"
            )
        ],
        "missing_evidence_refs": [],
        "residual_risk_refs": _string_list(row.get("residual_risk_categories")),
        "rule_ids": [str(row.get("rule_id") or "")] if row.get("rule_id") else [],
    }


def _trace_seed_from_non_applicable_boundary(
    *,
    context: DraftGenerationContext,
    boundary: dict[str, Any],
    representative_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    refs = [
        {
            "artifact_path": str(
                context.review_dir / "review_packet_index" / "review_packet_index.json"
            ),
            "selector": "non_applicable_authority_boundary",
        },
        {
            "artifact_path": str(context.review_dir / "non_applicable_authority_appendix.json"),
            "selector": "authorities",
        },
    ]
    source_passages = [
        {
            "source_record_id": source_record_id,
            "citation_label": source_record_id,
        }
        for row in representative_rows
        for source_record_id in _string_list(row.get("source_record_ids"))
    ]
    return {
        "source_passages": source_passages,
        "authority_family_ids": [
            family_id
            for row in representative_rows
            for family_id in _string_list(row.get("authority_family_ids"))
        ],
        "graph_path_ids": [],
        "retrieval_trace_ids": [],
        "review_decision_refs": refs,
        "unresolved_issue_refs": [],
        "missing_evidence_refs": [],
        "residual_risk_refs": ["non_applicable_authority_boundary"]
        if boundary.get("non_applicable_authority_count")
        else [],
        "rule_ids": [],
    }


def _bundles_for_confirmation(
    *,
    confirmations: list[dict[str, Any]],
    bundles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    confirmation_ids = {
        str(row.get("confirmation_id") or "")
        for row in confirmations
        if str(row.get("confirmation_id") or "").strip()
    }
    return [
        bundle
        for bundle in bundles.values()
        if confirmation_ids.intersection(
            _string_list(_dict(bundle.get("decision_support")).get("implementation_confirmation_ids"))
        )
    ]


def _accepted_risk_for_rule(*, bundle_index: dict[str, Any], rule_id: str) -> dict[str, Any] | None:
    for row in _dict_list(bundle_index.get("accepted_risks")):
        if str(row.get("rule_id") or "") == rule_id:
            return row
    return None
