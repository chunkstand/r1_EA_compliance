from __future__ import annotations

from collections import Counter

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


def check_authority_explanation_paths(
    authority_explanation: dict,
    applicability_gate: dict,
) -> dict:
    summary = authority_explanation.get("summary") or {}
    path = authority_explanation.get("authority_explanation_paths_path")
    return {
        "name": "authority_explanation_paths_ready",
        "passed": bool(summary.get("passed")),
        "details": {
            "mode": applicability_gate.get("mode"),
            "generated_mode": bool(authority_explanation.get("generated_mode")),
            "path": path,
            "finding_path_count": summary.get("finding_path_count", 0),
            "non_applicable_path_count": summary.get("non_applicable_path_count", 0),
            "all_findings_have_path_classification": summary.get(
                "all_findings_have_path_classification"
            ),
            "all_applicable_findings_have_trace_evidence": summary.get(
                "all_applicable_findings_have_trace_evidence"
            ),
            "all_non_applicable_paths_have_boundary_evidence": summary.get(
                "all_non_applicable_paths_have_boundary_evidence"
            ),
            "path_classification_counts": summary.get("path_classification_counts", {}),
            "risk_category_counts": summary.get("risk_category_counts", {}),
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
        "passed": not invalid,
        "details": {"invalid": invalid},
    }


def check_pass_findings_have_dual_evidence(findings: list[dict]) -> dict:
    failures = [
        finding["id"]
        for finding in findings
        if finding["status"] == "pass"
        and (
            not finding.get("package_evidence_citation")
            or not finding.get("source_library_evidence_citation")
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
        if finding["status"] == "gap" and not finding.get("source_library_evidence_citation")
    ]
    return {
        "name": "gap_findings_have_source_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def check_forest_plan_component_gate(forest_plan_summary: dict) -> dict:
    scope_status = str(forest_plan_summary.get("scope_status") or "")
    required = _forest_plan_component_gate_required(scope_status)
    component_evaluation = forest_plan_summary.get("component_evaluation") or {}
    component_adjudication = forest_plan_summary.get("component_adjudication") or {}
    if not required:
        return {
            "name": "forest_plan_component_gate_reviewer_ready",
            "passed": True,
            "details": {
                "required": False,
                "scope_status": scope_status,
                "component_evaluation_reviewer_ready": component_evaluation.get("reviewer_ready"),
                "component_adjudication_reviewer_ready": component_adjudication.get(
                    "reviewer_ready"
                ),
            },
        }
    return {
        "name": "forest_plan_component_gate_reviewer_ready",
        "passed": bool(component_evaluation.get("reviewer_ready"))
        and bool(component_adjudication.get("reviewer_ready")),
        "details": {
            "required": True,
            "scope_status": scope_status,
            "component_evaluation_reviewer_ready": component_evaluation.get("reviewer_ready"),
            "component_adjudication_reviewer_ready": component_adjudication.get(
                "reviewer_ready"
            ),
            "component_evaluation_validation_passed": component_evaluation.get(
                "validation_passed"
            ),
            "component_adjudication_validation_passed": component_adjudication.get(
                "validation_passed"
            ),
            "component_evaluation_system_miss_count": component_evaluation.get(
                "system_miss_count",
            ),
            "component_adjudication_real_ea_omission_count": component_adjudication.get(
                "real_ea_omission_count",
            ),
        },
    }


def _forest_plan_component_gate_required(scope_status: str) -> bool:
    if not scope_status:
        return False
    return scope_status not in {"ambiguous", "not_custer_gallatin", "not_selected_forest_unit"}


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
        if finding["status"] in CLAIM_STATUSES and not finding.get("source_claim_links")
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
