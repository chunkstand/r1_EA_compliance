from __future__ import annotations

import hashlib
import json

from .compliance_validation import finding_node_id
from .compliance_validation import forest_plan_summary_for_compliance
from .compliance_validation import rule_node_id
from .compliance_validation import rule_pack_node_id
from .compliance_validation import rule_pack_summary


COMPLIANCE_REVIEW_SCHEMA_VERSION = "compliance-review-v0"


def finding_graph(
    *,
    review_id: str,
    rule_pack: dict,
    findings: list[dict],
) -> tuple[list[dict], list[dict]]:
    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}
    review_node_id = f"compliance_review:{review_id}"
    rule_pack_id = rule_pack_node_id(rule_pack)
    nodes[review_node_id] = _node(
        review_node_id,
        "ComplianceReview",
        review_id=review_id,
        rule_pack_id=rule_pack["rule_pack_id"],
        rule_pack_version=rule_pack["version"],
    )
    nodes[rule_pack_id] = _node(
        rule_pack_id,
        "ComplianceRulePack",
        **rule_pack_summary(rule_pack),
    )
    edges[_edge_id(rule_pack_id, "RULE_PACK_USED_BY_REVIEW", review_node_id)] = _edge(
        rule_pack_id,
        "RULE_PACK_USED_BY_REVIEW",
        review_node_id,
    )

    rules_by_id = {str(rule["id"]): rule for rule in rule_pack["rules"]}
    for finding in findings:
        rule = rules_by_id[finding["rule_id"]]
        rule_id = rule_node_id(rule_pack, rule)
        finding_id = finding_node_id(review_id, finding["rule_id"])
        nodes.setdefault(
            rule_id,
            _node(
                rule_id,
                "ComplianceRule",
                rule_pack_id=rule_pack["rule_pack_id"],
                rule_pack_version=rule_pack["version"],
                rule_id=rule["id"],
                title=rule["title"],
                severity=rule.get("severity", "medium"),
                requirement=rule.get("requirement"),
                authority_category=rule.get("authority_category"),
                authority_source_record_id=rule.get("authority_source_record_id")
                or (rule.get("source_filters") or {}).get("source_record_id"),
                authority_document_role=rule.get("authority_document_role")
                or (rule.get("source_filters") or {}).get("document_role"),
                applicability_mode=rule.get("applicability_mode"),
                applies_if_package_terms=rule.get("applies_if_package_terms", []),
                applies_if_package_term_groups=rule.get("applies_if_package_term_groups", []),
                does_not_apply_if_package_terms=rule.get(
                    "does_not_apply_if_package_terms",
                    [],
                ),
                source_query=rule.get("source_query"),
                source_filters=rule.get("source_filters", {}),
            ),
        )
        nodes[finding_id] = _node(
            finding_id,
            "ComplianceFinding",
            review_id=review_id,
            rule_id=finding["rule_id"],
            status=finding["status"],
            claim_type=finding["claim_type"],
            severity=finding["severity"],
            confidence=finding["confidence"],
            authority_category=finding.get("authority_category"),
            authority_source_record_id=finding.get("authority_source_record_id"),
            applicability_status=finding.get("applicability_status"),
            applicability_mode=finding.get("applicability_mode"),
            package_evidence_status=finding["package_evidence_status"],
            source_library_evidence_status=finding["source_library_evidence_status"],
        )
        for source, relationship, target in (
            (rule_pack_id, "RULE_PACK_HAS_RULE", rule_id),
            (review_node_id, "REVIEW_EVALUATED_RULE", rule_id),
            (rule_id, "RULE_PRODUCED_FINDING", finding_id),
        ):
            edges[_edge_id(source, relationship, target)] = _edge(source, relationship, target)

        if finding.get("source_library_evidence"):
            source_node_id = _evidence_node_id(
                review_id,
                finding["rule_id"],
                "source_library",
                finding["source_library_evidence"],
            )
            nodes[source_node_id] = _evidence_node(
                source_node_id,
                "SourceLibraryEvidence",
                finding["source_library_evidence"],
            )
            edges[
                _edge_id(
                    finding_id,
                    "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
                    source_node_id,
                )
            ] = _edge(
                finding_id,
                "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
                source_node_id,
            )

        for source_claim in finding.get("source_claim_links", []):
            source_claim_node_id = _source_claim_node_id(source_claim)
            nodes[source_claim_node_id] = _source_claim_node(source_claim_node_id, source_claim)
            edges[
                _edge_id(
                    finding_id,
                    "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
                    source_claim_node_id,
                )
            ] = _edge(
                finding_id,
                "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
                source_claim_node_id,
            )
            edges[
                _edge_id(
                    rule_id,
                    "RULE_BOUND_TO_SOURCE_CLAIM",
                    source_claim_node_id,
                )
            ] = _edge(
                rule_id,
                "RULE_BOUND_TO_SOURCE_CLAIM",
                source_claim_node_id,
            )

        if finding.get("package_evidence"):
            package_node_id = _evidence_node_id(
                review_id,
                finding["rule_id"],
                "package",
                finding["package_evidence"],
            )
            nodes[package_node_id] = _evidence_node(
                package_node_id,
                "PackageEvidence",
                finding["package_evidence"],
            )
            edges[
                _edge_id(
                    finding_id,
                    "FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE",
                    package_node_id,
                )
            ] = _edge(
                finding_id,
                "FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE",
                package_node_id,
            )
        elif finding["status"] == "gap":
            gap_node_id = f"package_gap:{review_id}:{finding['rule_id']}"
            nodes[gap_node_id] = _node(
                gap_node_id,
                "PackageEvidenceGap",
                review_id=review_id,
                rule_id=finding["rule_id"],
                package_query=finding["package_query"],
                package_terms=finding["package_terms"],
            )
            edges[_edge_id(finding_id, "FINDING_HAS_PACKAGE_GAP", gap_node_id)] = _edge(
                finding_id,
                "FINDING_HAS_PACKAGE_GAP",
                gap_node_id,
            )

    return sorted(nodes.values(), key=lambda node: node["id"]), sorted(
        edges.values(),
        key=lambda edge: edge["id"],
    )


def attach_forest_plan_graph(
    *,
    nodes: list[dict],
    edges: list[dict],
    review_id: str,
    forest_plan_result,
) -> tuple[list[dict], list[dict]]:
    node_map = {node["id"]: node for node in nodes}
    edge_map = {edge["id"]: edge for edge in edges}
    review_node_id = f"compliance_review:{review_id}"
    forest_plan_summary = forest_plan_summary_for_compliance(forest_plan_result)
    forest_plan_node_id = f"forest_plan_review:{review_id}"
    node_map[forest_plan_node_id] = _node(
        forest_plan_node_id,
        "ForestPlanReview",
        review_id=review_id,
        scope_status=forest_plan_summary.get("scope_status"),
        source_set_id=forest_plan_summary.get("source_set_id"),
        reviewer_ready=forest_plan_summary.get("reviewer_ready"),
        validation_passed=forest_plan_summary.get("validation_passed"),
        needs_reviewer_resolution=forest_plan_summary.get("needs_reviewer_resolution"),
        context_path=forest_plan_summary.get("context_path"),
        summary_path=forest_plan_summary.get("summary_path"),
        validation_path=forest_plan_summary.get("validation_path"),
    )
    edge = _edge(
        review_node_id,
        "REVIEW_INCLUDES_FOREST_PLAN_REVIEW",
        forest_plan_node_id,
    )
    edge_map[edge["id"]] = edge
    component_evaluation = forest_plan_summary.get("component_evaluation") or {}
    if component_evaluation:
        component_node_id = f"forest_plan_component_evaluation:{review_id}"
        node_map[component_node_id] = _node(
            component_node_id,
            "ForestPlanComponentEvaluation",
            review_id=review_id,
            source_set_id=component_evaluation.get("source_set_id"),
            reviewer_ready=component_evaluation.get("reviewer_ready"),
            validation_passed=component_evaluation.get("validation_passed"),
            component_count=component_evaluation.get("component_count"),
            standard_count=component_evaluation.get("standard_count"),
            applicable_standard_count=component_evaluation.get("applicable_standard_count"),
            all_applicable_standards_applied=component_evaluation.get(
                "all_applicable_standards_applied"
            ),
            reviewer_resolution_count=component_evaluation.get("reviewer_resolution_count"),
            findings_path=forest_plan_summary.get("component_findings_path"),
            markdown_path=forest_plan_summary.get("component_markdown_path"),
            reviewer_resolution_queue_path=forest_plan_summary.get(
                "component_reviewer_resolution_queue_path"
            ),
            component_inventory_coverage_path=forest_plan_summary.get(
                "component_inventory_coverage_path"
            ),
            applicable_standard_coverage_path=forest_plan_summary.get(
                "applicable_standard_coverage_path"
            ),
        )
        edge = _edge(
            forest_plan_node_id,
            "FOREST_PLAN_REVIEW_HAS_COMPONENT_EVALUATION",
            component_node_id,
        )
        edge_map[edge["id"]] = edge
    return sorted(node_map.values(), key=lambda node: node["id"]), sorted(
        edge_map.values(),
        key=lambda edge: edge["id"],
    )


def _node(node_id: str, node_type: str, **payload) -> dict:
    return {
        "id": node_id,
        "type": node_type,
        "schema_version": COMPLIANCE_REVIEW_SCHEMA_VERSION,
        **payload,
    }


def _edge(source: str, relationship: str, target: str, **payload) -> dict:
    return {
        "id": _edge_id(source, relationship, target),
        "source": source,
        "target": target,
        "relationship": relationship,
        "schema_version": COMPLIANCE_REVIEW_SCHEMA_VERSION,
        **payload,
    }


def _edge_id(source: str, relationship: str, target: str) -> str:
    digest = hashlib.sha256(f"{source}|{relationship}|{target}".encode("utf-8")).hexdigest()
    return f"edge:{digest[:24]}"


def _evidence_node(node_id: str, node_type: str, evidence: dict) -> dict:
    return _node(
        node_id,
        node_type,
        chunk_id=evidence.get("chunk_id"),
        source_record_id=evidence.get("source_record_id"),
        title=evidence.get("title"),
        citation_label=evidence.get("citation_label"),
        evidence_span=evidence.get("evidence_span"),
        provenance=evidence.get("provenance"),
    )


def _source_claim_node(node_id: str, source_claim: dict) -> dict:
    return _node(
        node_id,
        "SourceClaim",
        link_id=source_claim.get("link_id"),
        rule_id=source_claim.get("rule_id"),
        claim_id=source_claim.get("claim_id"),
        claim_type=source_claim.get("claim_type"),
        claim_text=source_claim.get("claim_text"),
        rank=source_claim.get("rank"),
        score=source_claim.get("score"),
        matched_terms=source_claim.get("matched_terms", []),
        source_record_id=source_claim.get("source_record_id"),
        chunk_id=source_claim.get("chunk_id"),
        citation_label=source_claim.get("citation_label"),
        source_char_start=source_claim.get("source_char_start"),
        source_char_end=source_claim.get("source_char_end"),
        content_sha256=source_claim.get("content_sha256"),
    )


def _source_claim_node_id(source_claim: dict) -> str:
    return f"source_claim:{source_claim['claim_id']}"


def _evidence_node_id(
    review_id: str,
    rule_id: str,
    evidence_kind: str,
    evidence: dict,
) -> str:
    key = evidence.get("chunk_id") or evidence.get("citation_label") or json.dumps(
        evidence,
        sort_keys=True,
    )
    digest = hashlib.sha256(str(key).encode("utf-8")).hexdigest()[:16]
    return f"{evidence_kind}_evidence:{review_id}:{rule_id}:{digest}"
