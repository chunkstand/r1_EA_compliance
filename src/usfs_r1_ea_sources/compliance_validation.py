from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .compliance_inputs import applicability_gate_summary
from .compliance_inputs import check_applicability_generated_rule_pack_gate
from .compliance_inputs import strings
from .rule_packs import _baseline_source_record_ids


VALID_FINDING_STATUSES = {"pass", "gap", "uncertain", "not_applicable"}
CLAIM_STATUSES = {"pass", "gap"}
VALID_CLAIM_TYPES = {
    "no_compliance_claim",
    "package_evidence_gap",
    "supported_compliance_finding",
}
GRAPH_COVERAGE_CHECKS = {
    "finding_graph_evidence_edges_match_claims",
    "finding_graph_integrity",
    "finding_graph_covers_rules",
}


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
    validation: dict,
    nodes: list[dict],
    edges: list[dict],
) -> dict:
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
    }


def check_compliance_findings_have_applicability_provenance(
    findings: list[dict],
    applicability_gate: dict,
) -> dict:
    missing = []
    if not applicability_gate.get("is_generated_rule_pack"):
        return {
            "name": "compliance_findings_have_applicability_provenance",
            "passed": True,
            "details": {
                "mode": applicability_gate.get("mode"),
                "required": False,
                "missing": missing,
            },
        }
    for finding in findings:
        missing_fields = []
        if not finding.get("candidate_authority_id"):
            missing_fields.append("candidate_authority_id")
        if not finding.get("applicability_decision_id"):
            missing_fields.append("applicability_decision_id")
        if not strings(finding.get("authority_family_ids")):
            missing_fields.append("authority_family_ids")
        if missing_fields:
            missing.append(
                {
                    "rule_id": finding.get("rule_id"),
                    "finding_id": finding.get("id"),
                    "missing_fields": missing_fields,
                }
            )
    return {
        "name": "compliance_findings_have_applicability_provenance",
        "passed": not missing,
        "details": {
            "mode": applicability_gate.get("mode"),
            "required": True,
            "finding_count": len(findings),
            "missing": missing,
        },
    }


def check_non_applicable_authority_appendix(authority_integration: dict) -> dict:
    summary = authority_integration.get("summary") or {}
    if not authority_integration.get("generated_mode"):
        return {
            "name": "non_applicable_authority_appendix_ready",
            "passed": True,
            "details": {
                "generated_mode": False,
                "required": False,
                "path": authority_integration.get("non_applicable_authority_appendix_path"),
            },
        }
    missing_coverage = summary.get("non_applicable_authorities_missing_coverage") or []
    missing_rationale = summary.get("non_applicable_authorities_missing_rationale") or []
    return {
        "name": "non_applicable_authority_appendix_ready",
        "passed": not missing_coverage and not missing_rationale,
        "details": {
            "generated_mode": True,
            "required": True,
            "path": authority_integration.get("non_applicable_authority_appendix_path"),
            "markdown_path": authority_integration.get(
                "non_applicable_authority_appendix_markdown_path"
            ),
            "non_applicable_authority_count": summary.get(
                "non_applicable_authority_count",
                0,
            ),
            "missing_coverage": missing_coverage,
            "missing_rationale": missing_rationale,
        },
    }


def check_reviewer_resolution_report(authority_integration: dict) -> dict:
    summary = authority_integration.get("summary") or {}
    pending_count = int(summary.get("pending_resolution_count") or 0)
    if not authority_integration.get("generated_mode"):
        return {
            "name": "authority_reviewer_resolution_report_ready",
            "passed": True,
            "details": {
                "generated_mode": False,
                "required": False,
                "path": authority_integration.get("reviewer_resolution_report_path"),
            },
        }
    return {
        "name": "authority_reviewer_resolution_report_ready",
        "passed": pending_count == 0,
        "details": {
            "generated_mode": True,
            "required": True,
            "path": authority_integration.get("reviewer_resolution_report_path"),
            "pending_resolution_count": pending_count,
            "adjudicated_authority_count": summary.get("adjudicated_authority_count", 0),
            "pending_resolution": authority_integration.get("pending_resolution") or [],
        },
    }


def check_litigation_risk_summary(authority_integration: dict) -> dict:
    flags = authority_integration.get("risk_flags") or []
    malformed = []
    for index, flag in enumerate(flags):
        missing_fields = []
        if not flag.get("risk_category"):
            missing_fields.append("risk_category")
        if flag.get("deterministic_basis") is not True:
            missing_fields.append("deterministic_basis")
        if flag.get("legal_conclusion") is not False:
            missing_fields.append("legal_conclusion")
        if not flag.get("artifact_refs"):
            missing_fields.append("artifact_refs")
        if missing_fields:
            malformed.append(
                {
                    "index": index,
                    "risk_category": flag.get("risk_category"),
                    "missing_or_invalid_fields": missing_fields,
                }
            )
    return {
        "name": "litigation_risk_summary_deterministic",
        "passed": not malformed,
        "details": {
            "path": authority_integration.get("litigation_risk_summary_path"),
            "risk_flag_count": len(flags),
            "legal_conclusion_count": (authority_integration.get("summary") or {}).get(
                "legal_conclusion_count",
                0,
            ),
            "malformed": malformed,
        },
    }


def check_all_rules_evaluated(rule_pack: dict, findings: list[dict]) -> dict:
    expected = {str(rule["id"]) for rule in rule_pack["rules"]}
    actual = {str(finding["rule_id"]) for finding in findings}
    return {
        "name": "all_rules_evaluated",
        "passed": expected == actual,
        "details": {
            "missing_rule_ids": sorted(expected - actual),
            "unexpected_rule_ids": sorted(actual - expected),
        },
    }


def check_baseline_source_documents_evaluated(rule_pack: dict, findings: list[dict]) -> dict:
    expected = set(_baseline_source_record_ids(rule_pack))
    actual = {
        str(finding.get("authority_source_record_id"))
        for finding in findings
        if finding.get("authority_source_record_id")
    }
    missing = sorted(expected - actual)
    return {
        "name": "baseline_source_documents_evaluated",
        "passed": not missing,
        "details": {
            "baseline_source_record_count": len(expected),
            "missing_source_record_ids": missing,
        },
    }


def check_finding_statuses(findings: list[dict]) -> dict:
    invalid = [
        {"id": finding.get("id"), "status": finding.get("status")}
        for finding in findings
        if finding.get("status") not in VALID_FINDING_STATUSES
    ]
    return {
        "name": "finding_statuses_are_valid",
        "passed": not invalid and bool(findings),
        "details": {"invalid": invalid, "finding_count": len(findings)},
    }


def check_pass_findings_have_dual_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["id"]
        for finding in findings
        if finding["status"] == "pass"
        and (
            finding.get("package_evidence_status") != "found"
            or finding.get("source_library_evidence_status") != "found"
        )
    ]
    return {
        "name": "pass_findings_have_dual_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def check_gap_findings_have_source_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["id"]
        for finding in findings
        if finding["status"] == "gap"
        and finding.get("source_library_evidence_status") != "found"
    ]
    return {
        "name": "gap_findings_have_source_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def check_forest_plan_component_gate(forest_plan_summary: dict) -> dict:
    scope_status = str(forest_plan_summary.get("scope_status") or "")
    component_evaluation = forest_plan_summary.get("component_evaluation") or {}
    required = scope_status == "custer_gallatin"
    if not required:
        passed = True
    else:
        passed = bool(forest_plan_summary.get("reviewer_ready")) and bool(
            component_evaluation.get("reviewer_ready")
        )
    return {
        "name": "forest_plan_component_gate_reviewer_ready",
        "passed": passed,
        "details": {
            "required": required,
            "scope_status": scope_status,
            "forest_plan_reviewer_ready": bool(forest_plan_summary.get("reviewer_ready")),
            "validation_passed": bool(forest_plan_summary.get("validation_passed")),
            "context_path": forest_plan_summary.get("context_path"),
            "summary_path": forest_plan_summary.get("summary_path"),
            "component_evaluation_present": bool(component_evaluation),
            "component_reviewer_ready": bool(component_evaluation.get("reviewer_ready")),
            "component_validation_passed": bool(component_evaluation.get("validation_passed")),
            "component_inventory_coverage_passed": bool(
                component_evaluation.get("component_inventory_coverage_passed")
            ),
            "applicable_standard_coverage_passed": bool(
                component_evaluation.get("applicable_standard_coverage_passed")
            ),
            "reviewer_resolution_count": component_evaluation.get(
                "reviewer_resolution_count",
            ),
        },
    }


def check_claim_findings_have_source_citations(findings: list[dict]) -> dict:
    failures = [
        finding["id"]
        for finding in findings
        if finding["status"] in CLAIM_STATUSES
        and not finding.get("source_library_evidence_citation")
    ]
    return {
        "name": "claim_findings_have_source_citations",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def check_claim_findings_have_source_claim_links(findings: list[dict]) -> dict:
    failures = [
        finding["id"]
        for finding in findings
        if finding["status"] in CLAIM_STATUSES
        and not finding.get("source_claim_links")
    ]
    return {
        "name": "claim_findings_have_source_claim_links",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def check_no_unsupported_compliance_claims(findings: list[dict]) -> dict:
    unsupported = [
        finding["id"]
        for finding in findings
        if finding["status"] in CLAIM_STATUSES
        and finding.get("source_library_evidence_status") != "found"
    ]
    return {
        "name": "no_unsupported_compliance_claims",
        "passed": not unsupported,
        "details": {"finding_ids": unsupported},
    }


def check_applicable_findings_have_authority_source_records(findings: list[dict]) -> dict:
    missing = sorted(
        str(finding.get("rule_id"))
        for finding in findings
        if finding.get("applicability_status") != "not_applicable"
        and not str(finding.get("authority_source_record_id") or "").strip()
    )
    return {
        "name": "applicable_findings_have_authority_source_records",
        "passed": not missing,
        "details": {"rule_ids": missing},
    }


def check_graph_integrity(nodes: list[dict], edges: list[dict]) -> dict:
    node_ids = [node["id"] for node in nodes]
    edge_ids = [edge["id"] for edge in edges]
    node_id_set = set(node_ids)
    duplicate_node_ids = sorted(
        node_id for node_id, count in Counter(node_ids).items() if count > 1
    )
    duplicate_edge_ids = sorted(
        edge_id for edge_id, count in Counter(edge_ids).items() if count > 1
    )
    dangling = [
        edge["id"]
        for edge in edges
        if edge["source"] not in node_id_set or edge["target"] not in node_id_set
    ]
    return {
        "name": "finding_graph_integrity",
        "passed": not duplicate_node_ids and not duplicate_edge_ids and not dangling,
        "details": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "duplicate_node_ids": duplicate_node_ids,
            "duplicate_edge_ids": duplicate_edge_ids,
            "dangling_edge_ids": dangling,
        },
    }


def check_finding_graph_evidence_edges(
    review_id: str,
    findings: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_types = {node["id"]: node["type"] for node in nodes}
    edge_tuples = {(edge["source"], edge["relationship"], edge["target"]) for edge in edges}
    failures = []
    for finding in findings:
        finding_id = finding_node_id(review_id, finding["rule_id"])
        source_edge = has_edge_to_type(
            edge_tuples,
            node_types,
            finding_id,
            "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
            "SourceLibraryEvidence",
        )
        source_claim_edge = has_edge_to_type(
            edge_tuples,
            node_types,
            finding_id,
            "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
            "SourceClaim",
        )
        package_edge = has_edge_to_type(
            edge_tuples,
            node_types,
            finding_id,
            "FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE",
            "PackageEvidence",
        )
        gap_edge = has_edge_to_type(
            edge_tuples,
            node_types,
            finding_id,
            "FINDING_HAS_PACKAGE_GAP",
            "PackageEvidenceGap",
        )
        missing = []
        if finding["status"] in CLAIM_STATUSES and not source_edge:
            missing.append("source_evidence_edge")
        if finding["status"] in CLAIM_STATUSES and not source_claim_edge:
            missing.append("source_claim_edge")
        if finding["status"] == "pass" and not package_edge:
            missing.append("package_evidence_edge")
        if finding["status"] == "gap" and not gap_edge:
            missing.append("package_gap_edge")
        if missing:
            failures.append({"rule_id": finding["rule_id"], "missing": missing})
    return {
        "name": "finding_graph_evidence_edges_match_claims",
        "passed": not failures,
        "details": {"failures": failures},
    }


def has_edge_to_type(
    edge_tuples: set[tuple[str, str, str]],
    node_types: dict[str, str],
    source: str,
    relationship: str,
    target_type: str,
) -> bool:
    return any(
        edge_source == source
        and edge_relationship == relationship
        and node_types.get(edge_target) == target_type
        for edge_source, edge_relationship, edge_target in edge_tuples
    )


def check_graph_covers_findings(
    rule_pack: dict,
    findings: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_ids = {node["id"] for node in nodes}
    edge_tuples = {(edge["source"], edge["relationship"], edge["target"]) for edge in edges}
    missing = []
    rule_pack_id = rule_pack_node_id(rule_pack)
    review_node_id = next(
        (node["id"] for node in nodes if node["type"] == "ComplianceReview"),
        None,
    )
    for rule in rule_pack["rules"]:
        rule_id = rule_node_id(rule_pack, rule)
        finding = next(
            (candidate for candidate in findings if candidate["rule_id"] == rule["id"]),
            None,
        )
        finding_id = finding_node_id(
            review_node_id.split(":", 1)[1] if review_node_id else "",
            rule["id"],
        )
        missing_for_rule = []
        if rule_id not in node_ids:
            missing_for_rule.append("rule_node")
        if not finding or finding_id not in node_ids:
            missing_for_rule.append("finding_node")
        if (rule_pack_id, "RULE_PACK_HAS_RULE", rule_id) not in edge_tuples:
            missing_for_rule.append("rule_pack_edge")
        if finding and (rule_id, "RULE_PRODUCED_FINDING", finding_id) not in edge_tuples:
            missing_for_rule.append("finding_edge")
        if missing_for_rule:
            missing.append({"rule_id": rule["id"], "missing": missing_for_rule})
    return {
        "name": "finding_graph_covers_rules",
        "passed": not missing,
        "details": {"missing": missing},
    }


def validation_checks_passed(validation: dict, names: set[str]) -> bool:
    checks_by_name = {
        str(check.get("name")): bool(check.get("passed"))
        for check in validation.get("checks", [])
    }
    return all(checks_by_name.get(name) for name in names)


def rule_pack_node_id(rule_pack: dict) -> str:
    return f"rule_pack:{rule_pack['rule_pack_id']}:{rule_pack['version']}"


def rule_node_id(rule_pack: dict, rule: dict) -> str:
    return f"compliance_rule:{rule_pack['rule_pack_id']}:{rule_pack['version']}:{rule['id']}"


def finding_node_id(review_id: str, rule_id: str) -> str:
    return f"compliance_finding:{review_id}:{rule_id}"


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
