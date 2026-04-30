from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re

from .ea_review import run_ea_review


RULE_PACK_SCHEMA_VERSION = "compliance-rule-pack-v0"
COMPLIANCE_REVIEW_SCHEMA_VERSION = "compliance-review-v0"
DEFAULT_RULE_PACK_PATH = Path("config/compliance_rule_pack_nepa_ea_v0.json")
VALID_FINDING_STATUSES = {"pass", "gap", "uncertain", "not_applicable"}
CLAIM_STATUSES = {"pass", "gap"}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
ALLOWED_SOURCE_FILTER_KEYS = {
    "authority_level",
    "citation",
    "document_role",
    "host",
    "review_topic",
    "source_record_id",
    "topic",
}


@dataclass(frozen=True)
class ComplianceReviewResult:
    review_id: str
    review_dir: Path
    compliance_review_path: Path
    compliance_validation_path: Path
    finding_nodes_path: Path
    finding_edges_path: Path
    rule_claim_links_path: Path
    rule_claim_validation_path: Path
    ea_review_report_path: Path
    ea_review_validation_path: Path
    summary: dict


def run_compliance_review(
    *,
    package_path: Path,
    output_dir: Path,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    index_path: Path | None = None,
    review_id: str | None = None,
    results_dir: Path | None = None,
    source_top_k: int = 3,
    package_top_k: int = 3,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
) -> ComplianceReviewResult:
    """Run a versioned compliance rule pack against a local EA package."""

    package_path = Path(package_path)
    output_dir = Path(output_dir)
    rule_pack_path = Path(rule_pack_path)
    if not rule_pack_path.exists():
        raise FileNotFoundError(f"Missing compliance rule pack: {rule_pack_path}")

    rule_pack = load_rule_pack(rule_pack_path)
    rule_pack_validation = validate_rule_pack(rule_pack)
    if not rule_pack_validation["passed"]:
        failed = ", ".join(
            check["name"] for check in rule_pack_validation["checks"] if not check["passed"]
        )
        raise ValueError(f"Compliance rule pack is invalid. Failed checks: {failed}")

    review_id = review_id or _default_review_id(package_path, rule_pack)
    _validate_safe_id(review_id, "review_id")
    review_dir = Path(results_dir) if results_dir else output_dir / "reviews" / review_id
    compliance_review_path = review_dir / "compliance_review.json"
    compliance_validation_path = review_dir / "compliance_validation.json"
    finding_nodes_path = review_dir / "finding_graph_nodes.jsonl"
    finding_edges_path = review_dir / "finding_graph_edges.jsonl"
    _prepare_outputs(
        compliance_review_path=compliance_review_path,
        compliance_validation_path=compliance_validation_path,
        finding_nodes_path=finding_nodes_path,
        finding_edges_path=finding_edges_path,
    )
    from .rule_claim_binding import build_rule_claim_links
    from .rule_claim_binding import links_by_rule

    rule_claim_result = build_rule_claim_links(
        output_dir=output_dir,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
    )
    rule_claim_links = _read_jsonl(rule_claim_result.links_path)
    rule_claim_links_by_rule = links_by_rule(rule_claim_links, limit=source_top_k)

    ea_result = run_ea_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=index_path,
        checklist_path=rule_pack_path,
        review_id=review_id,
        results_dir=review_dir,
        source_top_k=source_top_k,
        package_top_k=package_top_k,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
    )
    ea_report = _read_json(ea_result.json_report_path)
    ea_validation = _read_json(ea_result.validation_path)
    rules_by_id = {str(rule["id"]): rule for rule in rule_pack["rules"]}
    findings = [
        _compliance_finding(
            rule_pack=rule_pack,
            rule=rules_by_id[str(finding["id"])],
            finding=finding,
            source_claim_links=rule_claim_links_by_rule.get(str(finding["id"]), []),
        )
        for finding in ea_report["findings"]
    ]
    nodes, edges = _finding_graph(
        review_id=review_id,
        rule_pack=rule_pack,
        findings=findings,
    )
    validation = _validation_report(
        review_id=review_id,
        rule_pack=rule_pack,
        rule_pack_validation=rule_pack_validation,
        rule_claim_validation=rule_claim_result.summary,
        ea_validation=ea_validation,
        findings=findings,
        nodes=nodes,
        edges=edges,
    )
    summary = _summary(
        review_id=review_id,
        package_path=package_path,
        output_dir=output_dir,
        rule_pack_path=rule_pack_path,
        rule_pack=rule_pack,
        ea_summary=ea_report["summary"],
        findings=findings,
        compliance_review_path=compliance_review_path,
        compliance_validation_path=compliance_validation_path,
        finding_nodes_path=finding_nodes_path,
        finding_edges_path=finding_edges_path,
        rule_claim_result=rule_claim_result,
        ea_result=ea_result,
        validation=validation,
        nodes=nodes,
        edges=edges,
    )
    report = {
        "schema_version": COMPLIANCE_REVIEW_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "summary": summary,
        "rule_pack": _rule_pack_summary(rule_pack),
        "validation": validation,
        "findings": findings,
    }
    _write_jsonl(finding_nodes_path, nodes)
    _write_jsonl(finding_edges_path, edges)
    _write_json(compliance_validation_path, validation)
    _write_json(compliance_review_path, report)
    return ComplianceReviewResult(
        review_id=review_id,
        review_dir=review_dir,
        compliance_review_path=compliance_review_path,
        compliance_validation_path=compliance_validation_path,
        finding_nodes_path=finding_nodes_path,
        finding_edges_path=finding_edges_path,
        rule_claim_links_path=rule_claim_result.links_path,
        rule_claim_validation_path=rule_claim_result.validation_path,
        ea_review_report_path=ea_result.json_report_path,
        ea_review_validation_path=ea_result.validation_path,
        summary=summary,
    )


def load_rule_pack(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Compliance rule pack must be a JSON object.")
    return value


def validate_rule_pack(rule_pack: dict) -> dict:
    checks = [
        _check_rule_pack_schema(rule_pack),
        _check_rule_pack_identity(rule_pack),
        _check_rule_pack_identity_safe(rule_pack),
        _check_rules_present(rule_pack),
        _check_rule_ids_unique(rule_pack),
        _check_rule_ids_safe(rule_pack),
        _check_required_rule_fields(rule_pack),
        _check_rule_queries_and_terms(rule_pack),
        _check_rule_source_filters(rule_pack),
        _check_rule_source_filter_keys(rule_pack),
    ]
    return {
        "schema_version": "compliance-rule-pack-validation-v0",
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _prepare_outputs(
    *,
    compliance_review_path: Path,
    compliance_validation_path: Path,
    finding_nodes_path: Path,
    finding_edges_path: Path,
) -> None:
    for path in (
        compliance_review_path,
        compliance_validation_path,
        finding_nodes_path,
        finding_edges_path,
    ):
        path.unlink(missing_ok=True)


def _compliance_finding(
    *,
    rule_pack: dict,
    rule: dict,
    finding: dict,
    source_claim_links: list[dict],
) -> dict:
    status = str(finding["status"])
    package_evidence = finding.get("package_evidence")
    source_evidence = finding.get("source_library_evidence")
    source_claim_evidence = [_source_claim_evidence(link) for link in source_claim_links]
    return {
        "id": finding["id"],
        "rule_id": rule["id"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "title": rule["title"],
        "question": rule.get("question") or rule["title"],
        "requirement": rule.get("requirement"),
        "severity": rule.get("severity", finding.get("severity", "medium")),
        "status": status,
        "claim_type": _claim_type(status),
        "confidence": finding.get("confidence"),
        "rationale": finding.get("rationale"),
        "package_query": finding.get("package_query"),
        "package_terms": finding.get("package_terms", []),
        "source_query": finding.get("source_query"),
        "source_filters": finding.get("source_filters", {}),
        "package_evidence_status": finding.get("package_evidence_status"),
        "source_library_evidence_status": finding.get("source_library_evidence_status"),
        "package_evidence_citation": _citation_label(package_evidence),
        "source_library_evidence_citation": _citation_label(source_evidence),
        "source_claim_link_count": len(source_claim_evidence),
        "source_claim_ids": [link["claim_id"] for link in source_claim_evidence],
        "source_claim_evidence_citations": [
            link["citation_label"] for link in source_claim_evidence if link.get("citation_label")
        ],
        "source_claim_links": source_claim_evidence,
        "package_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "package_results": finding.get("package_results", []),
        "source_library_results": finding.get("source_library_results", []),
        "limitations": finding.get("limitations", []),
        "evidence_expectation": rule.get("evidence_expectation"),
    }


def _claim_type(status: str) -> str:
    if status == "pass":
        return "supported_compliance_finding"
    if status == "gap":
        return "package_evidence_gap"
    return "no_compliance_claim"


def _finding_graph(
    *,
    review_id: str,
    rule_pack: dict,
    findings: list[dict],
) -> tuple[list[dict], list[dict]]:
    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}
    review_node_id = f"compliance_review:{review_id}"
    rule_pack_node_id = _rule_pack_node_id(rule_pack)
    nodes[review_node_id] = _node(
        review_node_id,
        "ComplianceReview",
        review_id=review_id,
        rule_pack_id=rule_pack["rule_pack_id"],
        rule_pack_version=rule_pack["version"],
    )
    nodes[rule_pack_node_id] = _node(
        rule_pack_node_id,
        "ComplianceRulePack",
        **_rule_pack_summary(rule_pack),
    )
    edges[_edge_id(rule_pack_node_id, "RULE_PACK_USED_BY_REVIEW", review_node_id)] = _edge(
        rule_pack_node_id,
        "RULE_PACK_USED_BY_REVIEW",
        review_node_id,
    )

    rules_by_id = {str(rule["id"]): rule for rule in rule_pack["rules"]}
    for finding in findings:
        rule = rules_by_id[finding["rule_id"]]
        rule_node_id = _rule_node_id(rule_pack, rule)
        finding_node_id = _finding_node_id(review_id, finding["rule_id"])
        nodes.setdefault(
            rule_node_id,
            _node(
                rule_node_id,
                "ComplianceRule",
                rule_pack_id=rule_pack["rule_pack_id"],
                rule_pack_version=rule_pack["version"],
                rule_id=rule["id"],
                title=rule["title"],
                severity=rule.get("severity", "medium"),
                requirement=rule.get("requirement"),
                source_query=rule.get("source_query"),
                source_filters=rule.get("source_filters", {}),
            ),
        )
        nodes[finding_node_id] = _node(
            finding_node_id,
            "ComplianceFinding",
            review_id=review_id,
            rule_id=finding["rule_id"],
            status=finding["status"],
            claim_type=finding["claim_type"],
            severity=finding["severity"],
            confidence=finding["confidence"],
            package_evidence_status=finding["package_evidence_status"],
            source_library_evidence_status=finding["source_library_evidence_status"],
        )
        for source, relationship, target in (
            (rule_pack_node_id, "RULE_PACK_HAS_RULE", rule_node_id),
            (review_node_id, "REVIEW_EVALUATED_RULE", rule_node_id),
            (rule_node_id, "RULE_PRODUCED_FINDING", finding_node_id),
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
                    finding_node_id,
                    "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
                    source_node_id,
                )
            ] = _edge(
                finding_node_id,
                "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
                source_node_id,
            )

        for source_claim in finding.get("source_claim_links", []):
            source_claim_node_id = _source_claim_node_id(source_claim)
            nodes[source_claim_node_id] = _source_claim_node(source_claim_node_id, source_claim)
            edges[
                _edge_id(
                    finding_node_id,
                    "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
                    source_claim_node_id,
                )
            ] = _edge(
                finding_node_id,
                "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
                source_claim_node_id,
            )
            edges[
                _edge_id(
                    rule_node_id,
                    "RULE_BOUND_TO_SOURCE_CLAIM",
                    source_claim_node_id,
                )
            ] = _edge(
                rule_node_id,
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
                    finding_node_id,
                    "FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE",
                    package_node_id,
                )
            ] = _edge(
                finding_node_id,
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
            edges[_edge_id(finding_node_id, "FINDING_HAS_PACKAGE_GAP", gap_node_id)] = _edge(
                finding_node_id,
                "FINDING_HAS_PACKAGE_GAP",
                gap_node_id,
            )

    return sorted(nodes.values(), key=lambda node: node["id"]), sorted(
        edges.values(),
        key=lambda edge: edge["id"],
    )


def _validation_report(
    *,
    review_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    rule_claim_validation: dict,
    ea_validation: dict,
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
                "failed_checks": _failed_check_names(ea_validation),
            },
        },
        _check_all_rules_evaluated(rule_pack, findings),
        _check_finding_statuses(findings),
        _check_pass_findings_have_dual_evidence(findings),
        _check_gap_findings_have_source_evidence(findings),
        _check_claim_findings_have_source_citations(findings),
        _check_claim_findings_have_source_claim_links(findings),
        _check_no_unsupported_compliance_claims(findings),
        _check_finding_graph_evidence_edges(review_id, findings, nodes, edges),
        _check_graph_integrity(nodes, edges),
        _check_graph_covers_findings(rule_pack, findings, nodes, edges),
    ]
    return {
        "schema_version": "compliance-validation-v0",
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _summary(
    *,
    review_id: str,
    package_path: Path,
    output_dir: Path,
    rule_pack_path: Path,
    rule_pack: dict,
    ea_summary: dict,
    findings: list[dict],
    compliance_review_path: Path,
    compliance_validation_path: Path,
    finding_nodes_path: Path,
    finding_edges_path: Path,
    rule_claim_result,
    ea_result,
    validation: dict,
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    status_counts = Counter(finding["status"] for finding in findings)
    claim_findings = [finding for finding in findings if finding["status"] in CLAIM_STATUSES]
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
        "finding_count": len(findings),
        "finding_status_counts": dict(status_counts),
        "claim_finding_count": len(claim_findings),
        "unsupported_finding_ids": unsupported,
        "compliance_review_path": str(compliance_review_path),
        "compliance_validation_path": str(compliance_validation_path),
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
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"],
    }


def _check_rule_pack_schema(rule_pack: dict) -> dict:
    actual = rule_pack.get("schema_version")
    return {
        "name": "rule_pack_schema_version",
        "passed": actual == RULE_PACK_SCHEMA_VERSION,
        "details": {"expected": RULE_PACK_SCHEMA_VERSION, "actual": actual},
    }


def _check_rule_pack_identity(rule_pack: dict) -> dict:
    missing = [
        field
        for field in ("rule_pack_id", "version", "title")
        if not str(rule_pack.get(field) or "").strip()
    ]
    return {
        "name": "rule_pack_identity_present",
        "passed": not missing,
        "details": {"missing": missing},
    }


def _check_rule_pack_identity_safe(rule_pack: dict) -> dict:
    unsafe = [
        field
        for field in ("rule_pack_id", "version")
        if str(rule_pack.get(field) or "").strip()
        and not SAFE_ID_RE.fullmatch(str(rule_pack.get(field)))
    ]
    return {
        "name": "rule_pack_identity_values_are_safe",
        "passed": not unsafe,
        "details": {"unsafe_fields": unsafe},
    }


def _check_rules_present(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules")
    return {
        "name": "rules_present",
        "passed": isinstance(rules, list) and bool(rules),
        "details": {"rule_count": len(rules) if isinstance(rules, list) else 0},
    }


def _check_rule_ids_unique(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    ids = [str(rule.get("id") or "") for rule in rules if isinstance(rule, dict)]
    counts = Counter(ids)
    duplicates = sorted(rule_id for rule_id, count in counts.items() if rule_id and count > 1)
    missing = sum(1 for rule_id in ids if not rule_id)
    return {
        "name": "rule_ids_unique",
        "passed": not duplicates and missing == 0 and len(ids) == len(rules),
        "details": {"duplicate_ids": duplicates, "missing_id_count": missing},
    }


def _check_rule_ids_safe(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    unsafe = [
        rule.get("id")
        for rule in rules
        if isinstance(rule, dict)
        and str(rule.get("id") or "").strip()
        and not SAFE_ID_RE.fullmatch(str(rule.get("id")))
    ]
    return {
        "name": "rule_ids_are_safe",
        "passed": not unsafe,
        "details": {"rule_ids": unsafe},
    }


def _check_required_rule_fields(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    required = {
        "id",
        "title",
        "question",
        "requirement",
        "severity",
        "package_query",
        "source_query",
    }
    missing = []
    for rule in rules:
        if not isinstance(rule, dict):
            missing.append({"rule_id": None, "missing": sorted(required)})
            continue
        rule_missing = sorted(
            field for field in required if not str(rule.get(field) or "").strip()
        )
        if rule_missing:
            missing.append({"rule_id": rule.get("id"), "missing": rule_missing})
    return {
        "name": "required_rule_fields_present",
        "passed": not missing,
        "details": {"missing": missing},
    }


def _check_rule_queries_and_terms(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        terms = rule.get("package_terms")
        if not isinstance(terms, list) or not any(str(term).strip() for term in terms):
            failures.append(rule.get("id"))
    return {
        "name": "rule_package_terms_present",
        "passed": not failures,
        "details": {"rule_ids": failures},
    }


def _check_rule_source_filters(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        filters = rule.get("source_filters")
        if not isinstance(filters, dict) or not filters:
            failures.append(rule.get("id"))
    return {
        "name": "rule_source_filters_present",
        "passed": not failures,
        "details": {"rule_ids": failures},
    }


def _check_rule_source_filter_keys(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        filters = rule.get("source_filters")
        if not isinstance(filters, dict):
            continue
        unknown_keys = sorted(set(filters) - ALLOWED_SOURCE_FILTER_KEYS)
        empty_values = sorted(
            key
            for key, value in filters.items()
            if key in ALLOWED_SOURCE_FILTER_KEYS and not str(value or "").strip()
        )
        if unknown_keys or empty_values:
            failures.append(
                {
                    "rule_id": rule.get("id"),
                    "unknown_keys": unknown_keys,
                    "empty_values": empty_values,
                }
            )
    return {
        "name": "rule_source_filter_keys_are_supported",
        "passed": not failures,
        "details": {
            "allowed_keys": sorted(ALLOWED_SOURCE_FILTER_KEYS),
            "failures": failures,
        },
    }


def _check_all_rules_evaluated(rule_pack: dict, findings: list[dict]) -> dict:
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


def _check_finding_statuses(findings: list[dict]) -> dict:
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


def _check_pass_findings_have_dual_evidence(findings: list[dict]) -> dict:
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


def _check_gap_findings_have_source_evidence(findings: list[dict]) -> dict:
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


def _check_claim_findings_have_source_citations(findings: list[dict]) -> dict:
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


def _check_claim_findings_have_source_claim_links(findings: list[dict]) -> dict:
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


def _check_no_unsupported_compliance_claims(findings: list[dict]) -> dict:
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


def _check_graph_integrity(nodes: list[dict], edges: list[dict]) -> dict:
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


def _check_finding_graph_evidence_edges(
    review_id: str,
    findings: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_types = {node["id"]: node["type"] for node in nodes}
    edge_tuples = {(edge["source"], edge["relationship"], edge["target"]) for edge in edges}
    failures = []
    for finding in findings:
        finding_node_id = _finding_node_id(review_id, finding["rule_id"])
        source_edge = _has_edge_to_type(
            edge_tuples,
            node_types,
            finding_node_id,
            "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
            "SourceLibraryEvidence",
        )
        source_claim_edge = _has_edge_to_type(
            edge_tuples,
            node_types,
            finding_node_id,
            "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
            "SourceClaim",
        )
        package_edge = _has_edge_to_type(
            edge_tuples,
            node_types,
            finding_node_id,
            "FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE",
            "PackageEvidence",
        )
        gap_edge = _has_edge_to_type(
            edge_tuples,
            node_types,
            finding_node_id,
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


def _has_edge_to_type(
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


def _check_graph_covers_findings(
    rule_pack: dict,
    findings: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_ids = {node["id"] for node in nodes}
    edge_tuples = {(edge["source"], edge["relationship"], edge["target"]) for edge in edges}
    missing = []
    rule_pack_node_id = _rule_pack_node_id(rule_pack)
    review_node_id = next(
        (node["id"] for node in nodes if node["type"] == "ComplianceReview"),
        None,
    )
    for rule in rule_pack["rules"]:
        rule_node_id = _rule_node_id(rule_pack, rule)
        finding = next(
            (candidate for candidate in findings if candidate["rule_id"] == rule["id"]),
            None,
        )
        finding_node_id = _finding_node_id(
            review_node_id.split(":", 1)[1] if review_node_id else "",
            rule["id"],
        )
        missing_for_rule = []
        if rule_node_id not in node_ids:
            missing_for_rule.append("rule_node")
        if not finding or finding_node_id not in node_ids:
            missing_for_rule.append("finding_node")
        if (rule_pack_node_id, "RULE_PACK_HAS_RULE", rule_node_id) not in edge_tuples:
            missing_for_rule.append("rule_pack_edge")
        if finding and (rule_node_id, "RULE_PRODUCED_FINDING", finding_node_id) not in edge_tuples:
            missing_for_rule.append("finding_edge")
        if missing_for_rule:
            missing.append({"rule_id": rule["id"], "missing": missing_for_rule})
    return {
        "name": "finding_graph_covers_rules",
        "passed": not missing,
        "details": {"missing": missing},
    }


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


def _source_claim_evidence(link: dict) -> dict:
    return {
        "link_id": link["link_id"],
        "rule_id": link["rule_id"],
        "claim_id": link["claim_id"],
        "claim_type": link["claim_type"],
        "claim_text": link["claim_text"],
        "rank": link["rank"],
        "score": link["score"],
        "matched_terms": link.get("matched_terms", []),
        "source_record_id": link["source_record_id"],
        "chunk_id": link["chunk_id"],
        "citation_label": link["citation_label"],
        "authority_level": link["authority_level"],
        "document_role": link["document_role"],
        "review_topics": link.get("review_topics", []),
        "artifact_sha256": link["artifact_sha256"],
        "artifact_path": link["artifact_path"],
        "parser_name": link["parser_name"],
        "parser_version": link["parser_version"],
        "source_text_path": link.get("source_text_path"),
        "source_char_start": link["source_char_start"],
        "source_char_end": link["source_char_end"],
        "chunk_char_start": link["chunk_char_start"],
        "chunk_char_end": link["chunk_char_end"],
        "content_sha256": link["content_sha256"],
        "validation_status": link["validation_status"],
    }


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


def _rule_pack_node_id(rule_pack: dict) -> str:
    return f"rule_pack:{rule_pack['rule_pack_id']}:{rule_pack['version']}"


def _rule_node_id(rule_pack: dict, rule: dict) -> str:
    return f"compliance_rule:{rule_pack['rule_pack_id']}:{rule_pack['version']}:{rule['id']}"


def _finding_node_id(review_id: str, rule_id: str) -> str:
    return f"compliance_finding:{review_id}:{rule_id}"


def _rule_pack_summary(rule_pack: dict) -> dict:
    return {
        "schema_version": rule_pack["schema_version"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "version": rule_pack["version"],
        "title": rule_pack["title"],
        "description": rule_pack.get("description"),
        "domain": rule_pack.get("domain"),
        "jurisdiction": rule_pack.get("jurisdiction"),
        "rule_count": len(rule_pack["rules"]),
    }


def _citation_label(evidence: dict | None) -> str | None:
    if not evidence:
        return None
    value = evidence.get("citation_label")
    return str(value) if value else None


def _failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _default_review_id(package_path: Path, rule_pack: dict) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return (
        f"compliance-review-{_safe_id(rule_pack['rule_pack_id'])}-"
        f"{_safe_id(package_path.stem or package_path.name)}-{stamp}"
    )


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return safe or "review"


def _validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dot, underscore, or hyphen."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
