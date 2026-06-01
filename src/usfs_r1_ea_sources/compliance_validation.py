from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .compliance_inputs import applicability_gate_summary
from .compliance_inputs import check_applicability_generated_rule_pack_gate
from .compliance_validation_checks import CLAIM_STATUSES
from .compliance_validation_checks import GRAPH_COVERAGE_CHECKS
from .compliance_validation_checks import VALID_CLAIM_TYPES
from .compliance_validation_checks import VALID_FINDING_STATUSES
from .compliance_validation_checks import check_all_rules_evaluated
from .compliance_validation_checks import (
    check_applicable_findings_have_authority_source_records,
)
from .compliance_validation_checks import check_authority_explanation_paths
from .compliance_validation_checks import (
    check_baseline_source_documents_evaluated,
)
from .compliance_validation_checks import (
    check_claim_findings_have_source_citations,
)
from .compliance_validation_checks import (
    check_claim_findings_have_source_claim_links,
)
from .compliance_validation_checks import (
    check_compliance_findings_have_applicability_provenance,
)
from .compliance_validation_checks import check_finding_graph_evidence_edges
from .compliance_validation_checks import check_finding_statuses
from .compliance_validation_checks import check_forest_plan_component_gate
from .compliance_validation_checks import check_gap_findings_have_source_evidence
from .compliance_validation_checks import check_graph_covers_findings
from .compliance_validation_checks import check_graph_integrity
from .compliance_validation_checks import check_litigation_risk_summary
from .compliance_validation_checks import check_no_unsupported_compliance_claims
from .compliance_validation_checks import (
    check_non_applicable_authority_appendix,
)
from .compliance_validation_checks import check_pass_findings_have_dual_evidence
from .compliance_validation_checks import check_reviewer_resolution_report
from .compliance_validation_checks import finding_node_id
from .compliance_validation_checks import rule_node_id
from .compliance_validation_checks import rule_pack_node_id
from .compliance_validation_checks import validation_checks_passed
from .rule_packs import _baseline_source_record_ids


__all__ = [
    "CLAIM_STATUSES",
    "GRAPH_COVERAGE_CHECKS",
    "VALID_CLAIM_TYPES",
    "VALID_FINDING_STATUSES",
    "compliance_summary",
    "failed_check_names",
    "finding_node_id",
    "forest_plan_summary_for_compliance",
    "rule_node_id",
    "rule_pack_node_id",
    "rule_pack_summary",
    "validation_checks_passed",
    "validation_report",
]


def validation_report(
    *,
    review_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    rule_claim_validation: dict,
    ea_validation: dict,
    forest_plan_summary: dict,
    applicability_gate: dict,
    package_manifest_path: Path,
    package_chunks_path: Path,
    authority_integration: dict,
    authority_explanation: dict,
    findings: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    checks = [
        {
            "name": "rule_pack_valid",
            "passed": bool(rule_pack_validation.get("passed")),
            "details": rule_pack_validation,
        },
        check_applicability_generated_rule_pack_gate(
            applicability_gate=applicability_gate,
            package_manifest_path=package_manifest_path,
            package_chunks_path=package_chunks_path,
        ),
        {
            "name": "rule_claim_binding_reviewer_ready",
            "passed": bool(rule_claim_validation.get("reviewer_ready")),
            "details": {
                "reviewer_ready": bool(rule_claim_validation.get("reviewer_ready")),
                "validation_passed": bool(rule_claim_validation.get("validation_passed")),
                "links_path": rule_claim_validation.get("links_path"),
                "validation_path": rule_claim_validation.get("validation_path"),
                "links_dir": rule_claim_validation.get("links_dir"),
                "canonical_links_dir": rule_claim_validation.get("canonical_links_dir"),
                "links_dir_is_canonical": rule_claim_validation.get(
                    "links_dir_is_canonical",
                    True,
                ),
                "rule_count": rule_claim_validation.get("rule_count", 0),
                "link_count": rule_claim_validation.get("link_count", 0),
                "gap_count": rule_claim_validation.get("gap_count", 0),
                "rules_without_links": rule_claim_validation.get("rules_without_links", []),
            },
        },
        {
            "name": "ea_review_validation_passed",
            "passed": bool(ea_validation.get("passed")),
            "details": {
                "passed": bool(ea_validation.get("passed")),
                "failed_checks": failed_check_names(ea_validation),
            },
        },
        check_forest_plan_component_gate(forest_plan_summary),
        check_all_rules_evaluated(rule_pack, findings),
        check_finding_statuses(findings),
        check_pass_findings_have_dual_evidence(findings),
        check_gap_findings_have_source_evidence(findings),
        check_claim_findings_have_source_citations(findings),
        check_claim_findings_have_source_claim_links(findings),
        check_no_unsupported_compliance_claims(findings),
        check_applicable_findings_have_authority_source_records(findings),
        check_compliance_findings_have_applicability_provenance(
            findings,
            applicability_gate,
        ),
        check_authority_explanation_paths(
            authority_explanation,
            applicability_gate,
        ),
        check_non_applicable_authority_appendix(authority_integration),
        check_reviewer_resolution_report(authority_integration),
        check_litigation_risk_summary(authority_integration),
        check_baseline_source_documents_evaluated(rule_pack, findings),
        check_finding_graph_evidence_edges(review_id, findings, nodes, edges),
        check_graph_integrity(nodes, edges),
        check_graph_covers_findings(rule_pack, findings, nodes, edges),
    ]
    return {
        "schema_version": "compliance-validation-v0",
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def compliance_summary(
    *,
    review_id: str,
    package_path: Path,
    output_dir: Path,
    rule_pack_path: Path,
    rule_pack: dict,
    ea_summary: dict,
    findings: list[dict],
    compliance_review_path: Path,
    compliance_matrix_path: Path,
    compliance_matrix_markdown_path: Path,
    compliance_matrix_pdf_path: Path,
    compliance_validation_path: Path,
    finding_nodes_path: Path,
    finding_edges_path: Path,
    rule_claim_result,
    ea_result,
    forest_plan_result,
    applicability_gate: dict,
    authority_integration: dict,
    authority_explanation_paths_path: Path,
    validation: dict,
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    from collections import Counter

    status_counts = Counter(finding["status"] for finding in findings)
    claim_findings = [finding for finding in findings if finding["status"] in CLAIM_STATUSES]
    applicable_findings = [
        finding for finding in findings if finding.get("applicability_status") != "not_applicable"
    ]
    not_applicable_findings = [
        finding for finding in findings if finding.get("applicability_status") == "not_applicable"
    ]
    baseline_source_record_ids = _baseline_source_record_ids(rule_pack)
    evaluated_baseline_source_record_ids = sorted(
        {
            str(finding["authority_source_record_id"])
            for finding in findings
            if finding.get("authority_source_record_id") in baseline_source_record_ids
        }
    )
    unsupported = [
        finding["id"]
        for finding in claim_findings
        if not finding.get("source_library_evidence_citation")
        or not finding.get("source_claim_links")
    ]
    return {
        "review_id": review_id,
        "package_path": str(package_path),
        "output_dir": str(output_dir),
        "source_set_id": ea_summary.get("source_set_id"),
        "index_path": ea_summary.get("index_path"),
        "rule_pack_path": str(rule_pack_path),
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "rule_count": len(rule_pack["rules"]),
        "baseline_source_record_count": len(baseline_source_record_ids),
        "baseline_source_record_ids": baseline_source_record_ids,
        "evaluated_baseline_source_record_ids": evaluated_baseline_source_record_ids,
        "finding_count": len(findings),
        "finding_status_counts": dict(status_counts),
        "authority_identification": {
            "workflow": "identify_applicable_authorities_then_evaluate_compliance",
            "authority_rule_count": len(rule_pack["rules"]),
            "applicable_authority_count": len(applicable_findings),
            "not_applicable_authority_count": len(not_applicable_findings),
            "applicable_rule_ids": sorted(finding["rule_id"] for finding in applicable_findings),
            "not_applicable_rule_ids": sorted(
                finding["rule_id"] for finding in not_applicable_findings
            ),
            "applicable_source_record_ids": sorted(
                {
                    str(finding["authority_source_record_id"])
                    for finding in applicable_findings
                    if finding.get("authority_source_record_id")
                }
            ),
        },
        "claim_finding_count": len(claim_findings),
        "unsupported_finding_ids": unsupported,
        "compliance_review_path": str(compliance_review_path),
        "compliance_matrix_path": str(compliance_matrix_path),
        "compliance_matrix_markdown_path": str(compliance_matrix_markdown_path),
        "compliance_matrix_pdf_path": str(compliance_matrix_pdf_path),
        "compliance_validation_path": str(compliance_validation_path),
        "authority_explanation_paths_path": str(authority_explanation_paths_path),
        "authority_provenance_path": authority_integration.get("authority_provenance_path"),
        "non_applicable_authority_appendix_path": authority_integration.get(
            "non_applicable_authority_appendix_path"
        ),
        "non_applicable_authority_appendix_markdown_path": authority_integration.get(
            "non_applicable_authority_appendix_markdown_path"
        ),
        "reviewer_resolution_report_path": authority_integration.get(
            "reviewer_resolution_report_path"
        ),
        "litigation_risk_summary_path": authority_integration.get(
            "litigation_risk_summary_path"
        ),
        "finding_nodes_path": str(finding_nodes_path),
        "finding_edges_path": str(finding_edges_path),
        "rule_claim_links_path": str(rule_claim_result.links_path),
        "rule_claim_validation_path": str(rule_claim_result.validation_path),
        "rule_claim_summary_path": str(rule_claim_result.summary_path),
        "rule_claim_links_dir": str(rule_claim_result.links_dir),
        "rule_claim_canonical_links_dir": rule_claim_result.summary.get("canonical_links_dir"),
        "rule_claim_links_are_canonical": bool(
            rule_claim_result.summary.get("links_dir_is_canonical", True)
        ),
        "rule_claim_link_count": rule_claim_result.summary["link_count"],
        "rule_claim_gap_count": rule_claim_result.summary["gap_count"],
        "rule_claim_rules_without_links": rule_claim_result.summary["rules_without_links"],
        "finding_node_count": len(nodes),
        "finding_edge_count": len(edges),
        "ea_review_report_path": str(ea_result.json_report_path),
        "ea_review_validation_path": str(ea_result.validation_path),
        "ea_review_reviewer_ready": bool(ea_summary.get("reviewer_ready")),
        "forest_plan_review": forest_plan_summary_for_compliance(forest_plan_result),
        "applicability_gate": applicability_gate_summary(applicability_gate),
        "authority_integration": authority_integration.get("summary", {}),
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"]
        and bool(applicability_gate.get("reviewer_ready_eligible")),
    }


def forest_plan_summary_for_compliance(forest_plan_result) -> dict:
    summary = forest_plan_result.summary
    component_evaluation = summary.get("component_evaluation") or {}
    component_adjudication = summary.get("component_adjudication") or {}
    return {
        "review_id": forest_plan_result.review_id,
        "review_dir": str(forest_plan_result.review_dir),
        "context_path": str(forest_plan_result.context_path),
        "validation_path": str(forest_plan_result.validation_path),
        "summary_path": str(forest_plan_result.summary_path),
        "scope_status": summary.get("scope_status"),
        "source_set_id": summary.get("source_set_id"),
        "index_path": summary.get("index_path"),
        "validation_passed": bool(summary.get("validation_passed")),
        "reviewer_ready": bool(summary.get("reviewer_ready")),
        "needs_reviewer_resolution": bool(summary.get("needs_reviewer_resolution")),
        "component_findings_path": (
            str(forest_plan_result.component_findings_path)
            if forest_plan_result.component_findings_path
            else None
        ),
        "component_markdown_path": (
            str(forest_plan_result.component_markdown_path)
            if forest_plan_result.component_markdown_path
            else None
        ),
        "component_reviewer_resolution_queue_path": (
            str(forest_plan_result.component_reviewer_resolution_queue_path)
            if forest_plan_result.component_reviewer_resolution_queue_path
            else None
        ),
        "component_inventory_coverage_path": (
            str(forest_plan_result.component_inventory_coverage_path)
            if forest_plan_result.component_inventory_coverage_path
            else None
        ),
        "applicable_standard_coverage_path": (
            str(forest_plan_result.applicable_standard_coverage_path)
            if forest_plan_result.applicable_standard_coverage_path
            else None
        ),
        "component_evaluation": component_evaluation,
        "component_adjudication": component_adjudication,
    }


def rule_pack_summary(rule_pack: dict) -> dict:
    return {
        "schema_version": rule_pack["schema_version"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "version": rule_pack["version"],
        "title": rule_pack["title"],
        "description": rule_pack.get("description"),
        "domain": rule_pack.get("domain"),
        "jurisdiction": rule_pack.get("jurisdiction"),
        "baseline_source_record_ids": _baseline_source_record_ids(rule_pack),
        "rule_count": len(rule_pack["rules"]),
    }


def failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
