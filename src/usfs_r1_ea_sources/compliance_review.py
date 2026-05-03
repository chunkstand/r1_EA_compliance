from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import textwrap

from .ea_review import run_ea_review
from .forest_plan_resolver import run_forest_plan_resolver


RULE_PACK_SCHEMA_VERSION = "compliance-rule-pack-v0"
COMPLIANCE_REVIEW_SCHEMA_VERSION = "compliance-review-v0"
COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"
COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION = "compliance-review-eval-v0"
DEFAULT_RULE_PACK_PATH = Path("config/compliance_rule_pack_nepa_ea_v0.json")
DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH = Path("config/compliance_review_eval_seed.json")
VALID_FINDING_STATUSES = {"pass", "gap", "uncertain", "not_applicable"}
CLAIM_STATUSES = {"pass", "gap"}
VALID_CLAIM_TYPES = {
    "no_compliance_claim",
    "package_evidence_gap",
    "supported_compliance_finding",
}
AUTHORITY_CATEGORIES = {
    "agency_policy",
    "case_law",
    "executive_order",
    "forest_plan",
    "law",
    "regulation",
    "state_requirement",
}
APPLICABILITY_MODES = {"baseline", "conditional"}
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
SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS = {"claim_type", "rule_id", "status"}
GRAPH_COVERAGE_CHECKS = {
    "finding_graph_evidence_edges_match_claims",
    "finding_graph_integrity",
    "finding_graph_covers_rules",
}


@dataclass(frozen=True)
class ComplianceReviewResult:
    review_id: str
    review_dir: Path
    compliance_review_path: Path
    compliance_matrix_path: Path
    compliance_matrix_markdown_path: Path
    compliance_matrix_pdf_path: Path
    compliance_validation_path: Path
    finding_nodes_path: Path
    finding_edges_path: Path
    rule_claim_links_path: Path
    rule_claim_validation_path: Path
    ea_review_report_path: Path
    ea_review_validation_path: Path
    summary: dict


@dataclass(frozen=True)
class ComplianceReviewEvalResult:
    eval_file: Path
    output_dir: Path
    output_path: Path
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
    reuse_package_cache: bool = False,
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
    compliance_matrix_path = review_dir / "compliance_matrix.json"
    compliance_matrix_markdown_path = review_dir / "compliance_matrix.md"
    compliance_matrix_pdf_path = review_dir / "compliance_matrix.pdf"
    compliance_validation_path = review_dir / "compliance_validation.json"
    finding_nodes_path = review_dir / "finding_graph_nodes.jsonl"
    finding_edges_path = review_dir / "finding_graph_edges.jsonl"
    _prepare_outputs(
        compliance_review_path=compliance_review_path,
        compliance_matrix_path=compliance_matrix_path,
        compliance_matrix_markdown_path=compliance_matrix_markdown_path,
        compliance_matrix_pdf_path=compliance_matrix_pdf_path,
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
        reuse_package_cache=reuse_package_cache,
    )
    ea_report = _read_json(ea_result.json_report_path)
    ea_validation = _read_json(ea_result.validation_path)
    forest_plan_result = run_forest_plan_resolver(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=index_path,
        review_id=review_id,
        results_dir=review_dir,
        source_top_k=source_top_k,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
        reuse_package_cache=True,
    )
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
    nodes, edges = _attach_forest_plan_graph(
        nodes=nodes,
        edges=edges,
        review_id=review_id,
        forest_plan_result=forest_plan_result,
    )
    validation = _validation_report(
        review_id=review_id,
        rule_pack=rule_pack,
        rule_pack_validation=rule_pack_validation,
        rule_claim_validation=rule_claim_result.summary,
        ea_validation=ea_validation,
        forest_plan_summary=forest_plan_result.summary,
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
        compliance_matrix_path=compliance_matrix_path,
        compliance_matrix_markdown_path=compliance_matrix_markdown_path,
        compliance_matrix_pdf_path=compliance_matrix_pdf_path,
        compliance_validation_path=compliance_validation_path,
        finding_nodes_path=finding_nodes_path,
        finding_edges_path=finding_edges_path,
        rule_claim_result=rule_claim_result,
        ea_result=ea_result,
        forest_plan_result=forest_plan_result,
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
    matrix = _compliance_matrix(
        review_id=review_id,
        package_path=package_path,
        rule_pack=rule_pack,
        findings=findings,
        summary=summary,
        validation=validation,
    )
    _write_jsonl(finding_nodes_path, nodes)
    _write_jsonl(finding_edges_path, edges)
    _write_json(compliance_matrix_path, matrix)
    compliance_matrix_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    compliance_matrix_markdown_path.write_text(
        _matrix_markdown(matrix),
        encoding="utf-8",
    )
    _write_compliance_matrix_pdf(compliance_matrix_pdf_path, matrix)
    _write_json(compliance_validation_path, validation)
    _write_json(compliance_review_path, report)
    return ComplianceReviewResult(
        review_id=review_id,
        review_dir=review_dir,
        compliance_review_path=compliance_review_path,
        compliance_matrix_path=compliance_matrix_path,
        compliance_matrix_markdown_path=compliance_matrix_markdown_path,
        compliance_matrix_pdf_path=compliance_matrix_pdf_path,
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
        _check_rule_package_section_preferences(rule_pack),
        _check_rule_source_filters(rule_pack),
        _check_rule_source_filter_keys(rule_pack),
        _check_rule_authority_metadata(rule_pack),
        _check_rule_pack_baseline_source_records(rule_pack),
    ]
    return {
        "schema_version": "compliance-rule-pack-validation-v0",
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def run_compliance_review_eval(
    *,
    output_dir: Path,
    eval_file: Path = DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    index_path: Path | None = None,
    results_dir: Path | None = None,
    source_top_k: int = 3,
    package_top_k: int = 3,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
) -> ComplianceReviewEvalResult:
    """Run deterministic eval cases against the final compliance-review layer."""

    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")
    if package_top_k < 1:
        raise ValueError("package_top_k must be at least 1")
    output_dir = Path(output_dir)
    eval_file = Path(eval_file)
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
    cases = _load_compliance_review_eval_cases(eval_file)
    _validate_compliance_review_eval_cases_against_rule_pack(cases, rule_pack)

    eval_output_dir = Path(results_dir) if results_dir else output_dir / "reviews" / "compliance_review_eval"
    package_dir = eval_output_dir / "packages"
    review_root = eval_output_dir / "reviews"
    package_dir.mkdir(parents=True, exist_ok=True)
    review_root.mkdir(parents=True, exist_ok=True)
    output_path = eval_output_dir / "compliance_review_eval_results.json"

    case_results = []
    for case in cases:
        case_id = str(case["id"])
        case_source_top_k = int(case.get("source_top_k") or source_top_k)
        case_package_top_k = int(case.get("package_top_k") or package_top_k)
        package_path = _eval_package_path(
            case,
            eval_file=eval_file,
            package_dir=package_dir,
        )
        review_id = str(case.get("review_id") or f"compliance-eval-{case_id}")
        _validate_safe_id(review_id, "review_id")
        review_dir = review_root / case_id
        result = run_compliance_review(
            package_path=package_path,
            output_dir=output_dir,
            rule_pack_path=rule_pack_path,
            source_set_id=source_set_id,
            index_path=index_path,
            review_id=review_id,
            results_dir=review_dir,
            source_top_k=case_source_top_k,
            package_top_k=case_package_top_k,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            docling_ocr=docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
        )
        report = _read_json(result.compliance_review_path)
        validation = _read_json(result.compliance_validation_path)
        case_results.append(
            _compliance_review_eval_case_result(
                case=case,
                package_path=package_path,
                result=result,
                report=report,
                validation=validation,
                source_top_k=case_source_top_k,
                package_top_k=case_package_top_k,
            )
        )

    case_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    source_set_ids = sorted(
        {
            str(case["source_set_id"])
            for case in case_results
            if case.get("source_set_id")
        }
    )
    summary = {
        "schema_version": COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION,
        "eval_file": str(eval_file),
        "output_dir": str(eval_output_dir),
        "output_path": str(output_path),
        "rule_pack_path": str(rule_pack_path),
        "source_set_id": source_set_id or (source_set_ids[0] if len(source_set_ids) == 1 else None),
        "source_set_ids": source_set_ids,
        "created_at": _utc_now(),
        "source_top_k": source_top_k,
        "package_top_k": package_top_k,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": case_count - passed_count,
        "passed": passed_count == case_count,
        "metrics": {
            "pass_rate": _rate(passed_count, case_count),
            "validation_match_rate": _case_rate(case_results, "validation_passed_matches"),
            "reviewer_ready_match_rate": _case_rate(case_results, "reviewer_ready_matches"),
            "status_match_rate": _case_rate(case_results, "expected_statuses_match"),
            "claim_type_match_rate": _case_rate(case_results, "expected_claim_types_match"),
            "package_evidence_match_rate": _case_rate(
                case_results,
                "expected_package_evidence_match",
            ),
            "source_evidence_match_rate": _case_rate(
                case_results,
                "expected_source_evidence_match",
            ),
            "source_claim_link_match_rate": _case_rate(
                case_results,
                "expected_source_claim_links_match",
            ),
            "source_record_match_rate": _case_rate(
                case_results,
                "expected_source_record_ids_match",
            ),
            "source_document_role_match_rate": _case_rate(
                case_results,
                "expected_source_document_roles_match",
            ),
            "citation_coverage_rate": _case_rate(case_results, "citation_coverage_supported"),
            "graph_coverage_rate": _case_rate(case_results, "graph_coverage_supported"),
            "unsupported_finding_match_rate": _case_rate(
                case_results,
                "unsupported_finding_ids_match",
            ),
            "zero_finding_rate": _rate(
                sum(1 for case in case_results if case["finding_count"] == 0),
                case_count,
            ),
        },
        "failure_category_counts": _failure_category_counts(case_results),
        "cases": case_results,
    }
    _write_json(output_path, summary)
    return ComplianceReviewEvalResult(
        eval_file=eval_file,
        output_dir=eval_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _prepare_outputs(
    *,
    compliance_review_path: Path,
    compliance_matrix_path: Path,
    compliance_matrix_markdown_path: Path,
    compliance_matrix_pdf_path: Path,
    compliance_validation_path: Path,
    finding_nodes_path: Path,
    finding_edges_path: Path,
) -> None:
    for path in (
        compliance_review_path,
        compliance_matrix_path,
        compliance_matrix_markdown_path,
        compliance_matrix_pdf_path,
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
    if status == "not_applicable":
        package_evidence = None
        source_evidence = None
        source_claim_links = []
    source_claim_evidence = [_source_claim_evidence(link) for link in source_claim_links]
    source_filters = finding.get("source_filters", {})
    authority_source_record_id = str(
        rule.get("authority_source_record_id")
        or (source_filters or {}).get("source_record_id")
        or ""
    ).strip()
    authority_document_role = str(
        rule.get("authority_document_role") or (source_filters or {}).get("document_role") or ""
    ).strip()
    return {
        "id": finding["id"],
        "rule_id": rule["id"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "authority_category": rule.get("authority_category"),
        "authority_source_record_id": authority_source_record_id or None,
        "authority_document_role": authority_document_role or None,
        "applicability_mode": rule.get("applicability_mode")
        or finding.get("applicability_mode"),
        "applies_if_package_terms": rule.get("applies_if_package_terms", []),
        "applies_if_package_term_groups": rule.get("applies_if_package_term_groups", []),
        "does_not_apply_if_package_terms": rule.get("does_not_apply_if_package_terms", []),
        "title": rule["title"],
        "question": rule.get("question") or rule["title"],
        "requirement": rule.get("requirement"),
        "severity": rule.get("severity", finding.get("severity", "medium")),
        "status": status,
        "claim_type": _claim_type(status),
        "confidence": finding.get("confidence"),
        "rationale": finding.get("rationale"),
        "applicability_status": finding.get("applicability_status"),
        "applicability_terms": finding.get("applicability_terms", []),
        "applicability_term_groups": finding.get("applicability_term_groups", []),
        "applicability_negative_terms": finding.get("applicability_negative_terms", []),
        "applicability_rationale": finding.get("applicability_rationale"),
        "applicability_evidence": finding.get("applicability_evidence"),
        "applicability_negative_evidence": finding.get("applicability_negative_evidence"),
        "package_query": finding.get("package_query"),
        "package_terms": finding.get("package_terms", []),
        "source_query": finding.get("source_query"),
        "source_filters": source_filters,
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
        nodes[finding_node_id] = _node(
            finding_node_id,
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


def _attach_forest_plan_graph(
    *,
    nodes: list[dict],
    edges: list[dict],
    review_id: str,
    forest_plan_result,
) -> tuple[list[dict], list[dict]]:
    node_map = {node["id"]: node for node in nodes}
    edge_map = {edge["id"]: edge for edge in edges}
    review_node_id = f"compliance_review:{review_id}"
    forest_plan_summary = _forest_plan_summary_for_compliance(forest_plan_result)
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


def _validation_report(
    *,
    review_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    rule_claim_validation: dict,
    ea_validation: dict,
    forest_plan_summary: dict,
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
        _check_forest_plan_component_gate(forest_plan_summary),
        _check_all_rules_evaluated(rule_pack, findings),
        _check_finding_statuses(findings),
        _check_pass_findings_have_dual_evidence(findings),
        _check_gap_findings_have_source_evidence(findings),
        _check_claim_findings_have_source_citations(findings),
        _check_claim_findings_have_source_claim_links(findings),
        _check_no_unsupported_compliance_claims(findings),
        _check_applicable_findings_have_authority_source_records(findings),
        _check_baseline_source_documents_evaluated(rule_pack, findings),
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
    compliance_matrix_path: Path,
    compliance_matrix_markdown_path: Path,
    compliance_matrix_pdf_path: Path,
    compliance_validation_path: Path,
    finding_nodes_path: Path,
    finding_edges_path: Path,
    rule_claim_result,
    ea_result,
    forest_plan_result,
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
        "forest_plan_review": _forest_plan_summary_for_compliance(forest_plan_result),
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"],
    }


def _forest_plan_summary_for_compliance(forest_plan_result) -> dict:
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


def _compliance_matrix(
    *,
    review_id: str,
    package_path: Path,
    rule_pack: dict,
    findings: list[dict],
    summary: dict,
    validation: dict,
) -> dict:
    rows = [_matrix_row(review_id, finding) for finding in findings]
    status_counts = dict(Counter(row["status"] for row in rows))
    applicability_counts = dict(Counter(row["applicability_status"] for row in rows))
    return {
        "schema_version": COMPLIANCE_MATRIX_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "package_path": str(package_path),
        "source_set_id": summary.get("source_set_id"),
        "rule_pack": _rule_pack_summary(rule_pack),
        "summary": {
            "row_count": len(rows),
            "status_counts": status_counts,
            "applicability_counts": applicability_counts,
            "applicable_row_count": sum(
                1 for row in rows if row["applicability_status"] == "applicable"
            ),
            "not_applicable_row_count": sum(
                1 for row in rows if row["applicability_status"] == "not_applicable"
            ),
            "applicable_source_record_ids": summary.get("authority_identification", {}).get(
                "applicable_source_record_ids",
                [],
            ),
            "claim_row_count": sum(1 for row in rows if row["status"] in CLAIM_STATUSES),
            "validated": bool(validation.get("passed")),
            "reviewer_ready": bool(summary.get("reviewer_ready")),
            "compliance_review_path": summary.get("compliance_review_path"),
            "compliance_validation_path": summary.get("compliance_validation_path"),
            "compliance_matrix_pdf_path": summary.get("compliance_matrix_pdf_path"),
            "finding_graph_nodes_path": summary.get("finding_nodes_path"),
            "finding_graph_edges_path": summary.get("finding_edges_path"),
            "forest_plan_review": summary.get("forest_plan_review"),
        },
        "columns": [
            "rule_id",
            "rule_title",
            "authority_category",
            "authority_source_record_id",
            "status",
            "applicability_status",
            "applicability_mode",
            "requirement",
            "ea_package_citation",
            "source_library_citation",
            "source_claim_ids",
            "applied_source_record_ids",
            "limitations",
        ],
        "rows": rows,
    }


def _matrix_row(review_id: str, finding: dict) -> dict:
    source_claim_ids = [str(value) for value in finding.get("source_claim_ids", [])]
    source_claim_citations = [
        str(value) for value in finding.get("source_claim_evidence_citations", []) if value
    ]
    applied_source_record_ids = _finding_source_record_ids(finding)
    applied_source_document_roles = _finding_source_document_roles(finding)
    citation_requirements_met = _finding_has_required_eval_citations(finding)
    return {
        "row_id": f"matrix:{review_id}:{finding['rule_id']}",
        "rule_id": finding["rule_id"],
        "rule_title": finding["title"],
        "authority_category": finding.get("authority_category"),
        "authority_source_record_id": finding.get("authority_source_record_id"),
        "authority_document_role": finding.get("authority_document_role"),
        "question": finding.get("question"),
        "requirement": finding.get("requirement"),
        "severity": finding.get("severity"),
        "status": finding["status"],
        "claim_type": finding["claim_type"],
        "confidence": finding.get("confidence"),
        "rationale": finding.get("rationale"),
        "applicability_status": finding.get("applicability_status")
        or ("not_applicable" if finding["status"] == "not_applicable" else "applicable"),
        "applicability_mode": finding.get("applicability_mode"),
        "applicability_basis": {
            "rationale": finding.get("applicability_rationale"),
            "mode": finding.get("applicability_mode"),
            "applies_if_package_terms": finding.get("applies_if_package_terms", []),
            "applies_if_package_term_groups": finding.get(
                "applies_if_package_term_groups",
                [],
            ),
            "does_not_apply_if_package_terms": finding.get(
                "does_not_apply_if_package_terms",
                [],
            ),
            "matched_terms": finding.get("applicability_terms", []),
            "applicability_evidence": _compact_evidence(finding.get("applicability_evidence")),
            "applicability_negative_terms": finding.get("applicability_negative_terms", []),
            "applicability_negative_evidence": _compact_evidence(
                finding.get("applicability_negative_evidence")
            ),
            "source_filters": finding.get("source_filters", {}),
            "package_terms": finding.get("package_terms", []),
            "source_query": finding.get("source_query"),
            "applied_source_record_ids": applied_source_record_ids,
            "applied_source_document_roles": applied_source_document_roles,
        },
        "package_query": finding.get("package_query"),
        "source_query": finding.get("source_query"),
        "ea_package_citation": finding.get("package_evidence_citation"),
        "ea_package_evidence": _compact_evidence(finding.get("package_evidence")),
        "source_library_citation": finding.get("source_library_evidence_citation"),
        "source_library_evidence": _compact_evidence(finding.get("source_library_evidence")),
        "source_claim_ids": source_claim_ids,
        "source_claim_citations": sorted(set(source_claim_citations)),
        "source_claim_count": len(source_claim_ids),
        "applied_source_record_ids": applied_source_record_ids,
        "applied_source_document_roles": applied_source_document_roles,
        "citation_requirements_met": citation_requirements_met,
        "limitation_count": len(finding.get("limitations", [])),
        "limitations": finding.get("limitations", []),
        "failure_category": _matrix_failure_category(finding),
    }


def _compact_evidence(evidence: dict | None) -> dict | None:
    if not evidence:
        return None
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    return {
        "citation_label": evidence.get("citation_label"),
        "source_record_id": evidence.get("source_record_id"),
        "title": evidence.get("title"),
        "chunk_id": evidence.get("chunk_id"),
        "text": span.get("text"),
        "source_char_start": span.get("source_char_start"),
        "source_char_end": span.get("source_char_end"),
        "chunk_char_start": span.get("chunk_char_start"),
        "chunk_char_end": span.get("chunk_char_end"),
        "page": provenance.get("page"),
        "section": provenance.get("section"),
        "artifact_path": provenance.get("artifact_path"),
        "artifact_sha256": provenance.get("artifact_sha256"),
        "content_sha256": provenance.get("content_sha256"),
    }


def _finding_source_record_ids(finding: dict) -> list[str]:
    source_record_ids = set()
    source_evidence = finding.get("source_library_evidence") or {}
    if source_evidence.get("source_record_id"):
        source_record_ids.add(str(source_evidence["source_record_id"]))
    for link in finding.get("source_claim_links", []):
        if link.get("source_record_id"):
            source_record_ids.add(str(link["source_record_id"]))
    return sorted(source_record_ids)


def _finding_source_document_roles(finding: dict) -> list[str]:
    roles = set()
    source_evidence = finding.get("source_library_evidence") or {}
    if source_evidence.get("document_role"):
        roles.add(str(source_evidence["document_role"]))
    for link in finding.get("source_claim_links", []):
        if link.get("document_role"):
            roles.add(str(link["document_role"]))
    return sorted(roles)


def _matrix_failure_category(finding: dict) -> str | None:
    status = finding.get("status")
    if status == "pass":
        return None
    if status == "gap":
        return "package_evidence_gap"
    if status == "not_applicable":
        return "not_applicable"
    if finding.get("source_library_evidence_status") != "found":
        return "source_retrieval_miss"
    if finding.get("package_evidence_status") != "found":
        return "package_evidence_search_miss"
    if status not in VALID_FINDING_STATUSES:
        return "unsupported_status"
    return "uncertain_finding"


def _matrix_markdown(matrix: dict) -> str:
    summary = matrix["summary"]
    lines = [
        "# Compliance Matrix",
        "",
        f"- Review ID: `{matrix['review_id']}`",
        f"- Source set: `{matrix.get('source_set_id')}`",
        f"- Rule pack: `{matrix['rule_pack']['rule_pack_id']}` "
        f"`{matrix['rule_pack']['version']}`",
        f"- Rows: `{summary['row_count']}`",
        f"- Status counts: `{summary['status_counts']}`",
        f"- Applicability counts: `{summary.get('applicability_counts', {})}`",
        f"- Reviewer ready: `{summary['reviewer_ready']}`",
    ]
    forest_plan_review = summary.get("forest_plan_review") or {}
    if forest_plan_review:
        lines.append(
            f"- Forest-plan review: `{forest_plan_review.get('scope_status')}` "
            f"(reviewer ready: `{forest_plan_review.get('reviewer_ready')}`)"
        )
    lines.extend(
        [
            "",
            "| Authority | Applicability | Status | EA evidence | Source evidence | Source claims | Limitations |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in matrix["rows"]:
        ea_evidence = row.get("ea_package_evidence") or {}
        source_evidence = row.get("source_library_evidence") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(
                        f"{row['rule_id']} - {row['rule_title']} "
                        f"({row.get('authority_category')}: "
                        f"{row.get('authority_source_record_id')})"
                    ),
                    _md_cell(
                        f"{row.get('applicability_status')} / "
                        f"{row.get('applicability_mode')}"
                    ),
                    _md_cell(row["status"]),
                    _md_cell(
                        _markdown_evidence_cell(
                            row.get("ea_package_citation"),
                            ea_evidence.get("title"),
                            ea_evidence.get("text"),
                        )
                    ),
                    _md_cell(
                        _markdown_evidence_cell(
                            row.get("source_library_citation"),
                            source_evidence.get("title"),
                            source_evidence.get("text"),
                        )
                    ),
                    _md_cell(", ".join(row.get("source_claim_ids", [])) or "N/A"),
                    _md_cell("; ".join(row.get("limitations", [])) or "None"),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _write_compliance_matrix_pdf(path: Path, matrix: dict) -> None:
    pages = _matrix_pdf_pages(matrix)
    _write_simple_pdf(path, pages, title="Compliance Matrix")


def _matrix_pdf_pages(matrix: dict) -> list[list[str]]:
    summary = matrix["summary"]
    rule_pack = matrix["rule_pack"]
    lines = [
        "Compliance Matrix",
        f"Review ID: {matrix['review_id']}",
        f"Source set: {matrix.get('source_set_id')}",
        f"Rule pack: {rule_pack['rule_pack_id']} {rule_pack['version']}",
        f"Rows: {summary['row_count']}",
        f"Status counts: {summary['status_counts']}",
        f"Applicability counts: {summary.get('applicability_counts', {})}",
        f"Reviewer ready: {summary['reviewer_ready']}",
    ]
    forest_plan_review = summary.get("forest_plan_review") or {}
    if forest_plan_review:
        lines.append(
            "Forest-plan review: "
            f"{forest_plan_review.get('scope_status')} "
            f"(reviewer ready: {forest_plan_review.get('reviewer_ready')})"
        )
    lines.extend(
        [
            "",
            (
                "Workflow: identify applicable authorities, evaluate the EA against each applicable "
                "authority, and cite both EA-package and source-library evidence."
            ),
            "",
        ]
    )
    for index, row in enumerate(matrix["rows"], start=1):
        lines.extend(_matrix_pdf_row_lines(index, row))
        lines.append("")
    return _paginate_pdf_lines(lines, max_lines=45)


def _matrix_pdf_row_lines(index: int, row: dict) -> list[str]:
    ea_evidence = row.get("ea_package_evidence") or {}
    source_evidence = row.get("source_library_evidence") or {}
    lines = [
        (
            f"{index}. {row['rule_id']} - {row['rule_title']} "
            f"({row.get('authority_category')}: {row.get('authority_source_record_id')})"
        ),
        (
            f"   Applicability: {row.get('applicability_status')} / "
            f"{row.get('applicability_mode')} | Status: {row.get('status')}"
        ),
        (
            "   EA evidence: "
            + _pdf_evidence_cell(row.get("ea_package_citation"), ea_evidence)
        ),
        (
            "   Source evidence: "
            + _pdf_evidence_cell(row.get("source_library_citation"), source_evidence)
        ),
        "   Source claims: " + (", ".join(row.get("source_claim_ids", [])) or "N/A"),
        "   Limitations: " + ("; ".join(row.get("limitations", [])) or "None"),
    ]
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(_wrap_pdf_line(line))
    return wrapped


def _pdf_evidence_cell(citation: str | None, evidence: dict) -> str:
    if not evidence:
        return "N/A"
    parts = []
    if citation:
        parts.append(citation)
    if evidence.get("title"):
        parts.append(str(evidence["title"]))
    if evidence.get("text"):
        parts.append(_truncate(str(evidence["text"]), 260))
    return " - ".join(parts) if parts else "N/A"


def _wrap_pdf_line(line: str, width: int = 150) -> list[str]:
    if len(line) <= width:
        return [line]
    leading_spaces = len(line) - len(line.lstrip(" "))
    indent = " " * min(leading_spaces + 4, 10)
    return textwrap.wrap(
        line,
        width=width,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _paginate_pdf_lines(lines: list[str], *, max_lines: int) -> list[list[str]]:
    pages: list[list[str]] = []
    page: list[str] = []
    for line in lines:
        if len(page) >= max_lines:
            pages.append(page)
            page = []
        page.append(line)
    if page:
        pages.append(page)
    return pages or [["Compliance Matrix"]]


def _write_simple_pdf(path: Path, pages: list[list[str]], *, title: str) -> None:
    width = 1008
    height = 612
    margin_x = 34
    start_y = 568
    leading = 12
    font_size = 8
    objects: list[bytes | None] = [None, None, None]

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    for page_number, page_lines in enumerate(pages, start=1):
        content = _pdf_page_content(
            page_lines,
            page_number=page_number,
            page_count=len(pages),
            title=title,
            margin_x=margin_x,
            start_y=start_y,
            leading=leading,
            font_size=font_size,
        )
        content_id = add_object(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects[1] = (objects[1] or b"") + f"{page_id} 0 R ".encode("ascii")

    kids = objects[1] or b""
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        b"<< /Type /Pages /Kids ["
        + kids
        + b"] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>"
    )
    objects[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    _write_pdf_objects(path, [obj for obj in objects if obj is not None])


def _pdf_page_content(
    lines: list[str],
    *,
    page_number: int,
    page_count: int,
    title: str,
    margin_x: int,
    start_y: int,
    leading: int,
    font_size: int,
) -> bytes:
    commands = [f"BT /F1 {font_size} Tf {leading} TL {margin_x} {start_y} Td"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj T*")
    footer_y = 24 - (start_y - len(lines) * leading)
    commands.append(
        f"0 {footer_y} Td ({_pdf_escape(f'{title} | Page {page_number} of {page_count}')}) Tj"
    )
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _pdf_escape(value: str) -> str:
    return (
        _pdf_text(value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _pdf_text(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a7": "Sec.",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    offsets = []
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(payload))


def _markdown_evidence_cell(citation: str | None, title: str | None, text: str | None) -> str:
    if not citation:
        return "N/A"
    parts = [citation]
    if title:
        parts.append(title)
    if text:
        parts.append(_truncate(text, 220))
    return " - ".join(parts)


def _truncate(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _load_compliance_review_eval_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing compliance review eval file: {path}")
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("Compliance review eval file must contain a non-empty JSON list.")
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"Compliance review eval case {index} must be an object.")
        case_id = str(case.get("id") or "").strip()
        if not case_id:
            raise ValueError(f"Compliance review eval case {index} is missing 'id'.")
        if not SAFE_ID_RE.fullmatch(case_id):
            raise ValueError(
                f"Compliance review eval case {index} id must contain only safe path characters."
            )
        _validate_eval_package_fixture(index, case)
        _validate_eval_filters(index, case)
        _validate_eval_expected_statuses(index, case)
        _validate_eval_expected_claim_types(index, case)
        _validate_eval_expected_bool_map(index, case, "expected_package_evidence")
        _validate_eval_expected_bool_map(index, case, "expected_source_evidence")
        _validate_eval_expected_bool_map(index, case, "expected_source_claim_links")
        _validate_eval_expected_string_list_map(index, case, "expected_source_record_ids")
        _validate_eval_expected_string_list_map(index, case, "expected_source_document_roles")
        _validate_eval_status_counts(index, case)
        _validate_eval_string_list(index, case, "expected_unsupported_finding_ids")
        _validate_optional_bool(index, case, "expected_validation_passed")
        _validate_optional_bool(index, case, "expected_reviewer_ready")
        _validate_optional_bool(index, case, "require_graph_coverage")
        _validate_positive_eval_int(index, case, "min_findings")
        _validate_positive_eval_int(index, case, "source_top_k")
        _validate_positive_eval_int(index, case, "package_top_k")
    return cases


def _validate_eval_package_fixture(index: int, case: dict) -> None:
    has_text = bool(str(case.get("package_text") or "").strip())
    has_path = bool(str(case.get("package_path") or "").strip())
    if has_text == has_path:
        raise ValueError(
            f"Compliance review eval case {index} must define exactly one of "
            "package_text or package_path."
        )


def _validate_compliance_review_eval_cases_against_rule_pack(
    cases: list[dict],
    rule_pack: dict,
) -> None:
    expected_rule_ids = {str(rule["id"]) for rule in rule_pack["rules"]}
    rule_count = len(expected_rule_ids)
    for index, case in enumerate(cases):
        case_id = str(case["id"])
        status_rule_ids = set(_string_map(case["expected_statuses"]))
        if status_rule_ids != expected_rule_ids:
            missing = sorted(expected_rule_ids - status_rule_ids)
            unexpected = sorted(status_rule_ids - expected_rule_ids)
            raise ValueError(
                f"Compliance review eval case {index} ({case_id}) expected_statuses must "
                f"cover every rule in the rule pack. Missing: {missing}; unexpected: {unexpected}."
            )
        for key in (
            "expected_claim_types",
            "expected_package_evidence",
            "expected_source_evidence",
            "expected_source_claim_links",
            "expected_source_record_ids",
            "expected_source_document_roles",
        ):
            _validate_eval_rule_map_keys(index, case_id, case.get(key) or {}, expected_rule_ids, key)
        unsupported_ids = set(str(value) for value in case.get("expected_unsupported_finding_ids", []))
        unexpected_unsupported = sorted(unsupported_ids - expected_rule_ids)
        if unexpected_unsupported:
            raise ValueError(
                f"Compliance review eval case {index} ({case_id}) expected_unsupported_finding_ids "
                f"contains unknown rule IDs: {unexpected_unsupported}."
            )
        filters = case.get("filters") or {}
        if "rule_id" in filters:
            rule_filter_ids = set(_filter_values(filters["rule_id"]))
            unknown_filters = sorted(rule_filter_ids - expected_rule_ids)
            if unknown_filters:
                raise ValueError(
                    f"Compliance review eval case {index} ({case_id}) rule_id filter "
                    f"contains unknown rule IDs: {unknown_filters}."
                )
        expected_counts = {
            str(status): int(count)
            for status, count in (case.get("expected_finding_status_counts") or {}).items()
        }
        if expected_counts:
            counts_from_statuses = dict(Counter(str(status) for status in case["expected_statuses"].values()))
            normalized_expected_counts = {
                status: count for status, count in expected_counts.items() if count
            }
            if sum(expected_counts.values()) != rule_count or normalized_expected_counts != counts_from_statuses:
                raise ValueError(
                    f"Compliance review eval case {index} ({case_id}) expected_finding_status_counts "
                    "must match expected_statuses and sum to the rule count."
                )


def _validate_eval_rule_map_keys(
    index: int,
    case_id: str,
    values: dict,
    expected_rule_ids: set[str],
    key: str,
) -> None:
    actual = set(str(rule_id) for rule_id in values)
    unexpected = sorted(actual - expected_rule_ids)
    if unexpected:
        raise ValueError(
            f"Compliance review eval case {index} ({case_id}) {key} contains unknown rule IDs: "
            f"{unexpected}."
        )


def _validate_eval_filters(index: int, case: dict) -> None:
    filters = case.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError(f"Compliance review eval case {index} filters must be an object.")
    unknown_keys = sorted(set(filters) - SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS)
    empty_values = [
        key
        for key, value in filters.items()
        if key in SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS and not _filter_values(value)
    ]
    if unknown_keys or empty_values:
        details = []
        if unknown_keys:
            details.append(f"unsupported filters: {unknown_keys}")
        if empty_values:
            details.append(f"empty filters: {empty_values}")
        raise ValueError(
            f"Compliance review eval case {index} has invalid filters; " + "; ".join(details)
        )
    if "status" in filters:
        unsupported = sorted(set(_filter_values(filters["status"])) - VALID_FINDING_STATUSES)
        if unsupported:
            raise ValueError(
                f"Compliance review eval case {index} has unsupported status filters: "
                f"{unsupported}."
            )
    if "claim_type" in filters:
        unsupported = sorted(set(_filter_values(filters["claim_type"])) - VALID_CLAIM_TYPES)
        if unsupported:
            raise ValueError(
                f"Compliance review eval case {index} has unsupported claim_type filters: "
                f"{unsupported}."
            )


def _validate_eval_expected_statuses(index: int, case: dict) -> None:
    expected = case.get("expected_statuses")
    if not isinstance(expected, dict) or not expected:
        raise ValueError(
            f"Compliance review eval case {index} expected_statuses must be a non-empty object."
        )
    invalid = sorted(
        str(status)
        for status in expected.values()
        if str(status) not in VALID_FINDING_STATUSES
    )
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} has unsupported expected_statuses: {invalid}."
        )


def _validate_eval_expected_claim_types(index: int, case: dict) -> None:
    expected = case.get("expected_claim_types") or {}
    if not isinstance(expected, dict):
        raise ValueError(
            f"Compliance review eval case {index} expected_claim_types must be an object."
        )
    invalid = sorted(
        str(claim_type)
        for claim_type in expected.values()
        if str(claim_type) not in VALID_CLAIM_TYPES
    )
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} has unsupported expected_claim_types: "
            f"{invalid}."
        )


def _validate_eval_expected_bool_map(index: int, case: dict, key: str) -> None:
    expected = case.get(key) or {}
    if not isinstance(expected, dict):
        raise ValueError(f"Compliance review eval case {index} {key} must be an object.")
    invalid = sorted(str(rule_id) for rule_id, value in expected.items() if not isinstance(value, bool))
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} {key} values must be booleans: {invalid}."
        )


def _validate_eval_expected_string_list_map(index: int, case: dict, key: str) -> None:
    expected = case.get(key) or {}
    if not isinstance(expected, dict):
        raise ValueError(f"Compliance review eval case {index} {key} must be an object.")
    invalid = []
    for rule_id, values in expected.items():
        if not isinstance(values, list) or not values:
            invalid.append(str(rule_id))
            continue
        if any(not str(value).strip() for value in values):
            invalid.append(str(rule_id))
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} {key} values must be non-empty "
            f"lists of strings: {invalid}."
        )


def _validate_eval_status_counts(index: int, case: dict) -> None:
    expected = case.get("expected_finding_status_counts") or {}
    if not isinstance(expected, dict):
        raise ValueError(
            f"Compliance review eval case {index} expected_finding_status_counts must be an object."
        )
    unsupported = sorted(set(str(status) for status in expected) - VALID_FINDING_STATUSES)
    invalid_counts = []
    for status, value in expected.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            invalid_counts.append(str(status))
            continue
        if count < 0:
            invalid_counts.append(str(status))
    if unsupported or invalid_counts:
        raise ValueError(
            f"Compliance review eval case {index} has invalid expected_finding_status_counts."
        )


def _validate_eval_string_list(index: int, case: dict, key: str) -> None:
    values = case.get(key, [])
    if not isinstance(values, list) or any(not str(value).strip() for value in values):
        raise ValueError(f"Compliance review eval case {index} {key} must be a list of strings.")


def _validate_optional_bool(index: int, case: dict, key: str) -> None:
    if key in case and not isinstance(case[key], bool):
        raise ValueError(f"Compliance review eval case {index} {key} must be a boolean.")


def _validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Compliance review eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Compliance review eval case {index} {key} must be at least 1.")


def _eval_package_path(case: dict, *, eval_file: Path, package_dir: Path) -> Path:
    if str(case.get("package_text") or "").strip():
        package_path = package_dir / f"{case['id']}.txt"
        package_path.write_text(str(case["package_text"]).rstrip() + "\n", encoding="utf-8")
        return package_path
    package_path = Path(str(case["package_path"]))
    if not package_path.is_absolute():
        package_path = eval_file.parent / package_path
    if not package_path.exists():
        raise FileNotFoundError(f"Missing compliance review eval package fixture: {package_path}")
    return package_path


def _compliance_review_eval_case_result(
    *,
    case: dict,
    package_path: Path,
    result: ComplianceReviewResult,
    report: dict,
    validation: dict,
    source_top_k: int,
    package_top_k: int,
) -> dict:
    findings = list(report.get("findings", []))
    findings_by_rule = {str(finding.get("rule_id")): finding for finding in findings}
    filters = dict(case.get("filters") or {})
    selected_findings = _filter_eval_findings(findings, filters)
    expected_statuses = _string_map(case["expected_statuses"])
    expected_claim_types = _expected_claim_type_map(case, expected_statuses)
    expected_package_evidence = _expected_bool_presence_map(
        case,
        "expected_package_evidence",
        expected_statuses,
        lambda status: status == "pass",
    )
    expected_source_evidence = _expected_bool_presence_map(
        case,
        "expected_source_evidence",
        expected_statuses,
        lambda status: status in CLAIM_STATUSES,
    )
    expected_source_claim_links = _expected_bool_presence_map(
        case,
        "expected_source_claim_links",
        expected_statuses,
        lambda status: status in CLAIM_STATUSES,
    )
    status_mismatches = _value_mismatches(findings_by_rule, expected_statuses, "status")
    claim_type_mismatches = _value_mismatches(
        findings_by_rule,
        expected_claim_types,
        "claim_type",
    )
    package_evidence_mismatches = _presence_mismatches(
        findings_by_rule,
        expected_package_evidence,
        _finding_has_package_evidence,
    )
    source_evidence_mismatches = _presence_mismatches(
        findings_by_rule,
        expected_source_evidence,
        _finding_has_source_evidence,
    )
    source_claim_link_mismatches = _presence_mismatches(
        findings_by_rule,
        expected_source_claim_links,
        _finding_has_source_claim_links,
    )
    expected_source_record_ids = _expected_string_list_map(case, "expected_source_record_ids")
    expected_source_document_roles = _expected_string_list_map(
        case,
        "expected_source_document_roles",
    )
    source_record_mismatches = _expected_subset_mismatches(
        findings_by_rule,
        expected_source_record_ids,
        _finding_source_record_ids,
    )
    source_document_role_mismatches = _expected_subset_mismatches(
        findings_by_rule,
        expected_source_document_roles,
        _finding_source_document_roles,
    )
    expected_status_counts = {
        str(status): int(count)
        for status, count in (case.get("expected_finding_status_counts") or {}).items()
    }
    actual_status_counts = dict(Counter(str(finding.get("status")) for finding in findings))
    status_counts_match = (
        not expected_status_counts or actual_status_counts == expected_status_counts
    )
    expected_unsupported = sorted(
        str(value) for value in case.get("expected_unsupported_finding_ids", [])
    )
    actual_unsupported = sorted(
        str(value)
        for value in report.get("summary", {}).get("unsupported_finding_ids", [])
    )
    unsupported_finding_ids_match = actual_unsupported == expected_unsupported
    expected_validation_passed = bool(case.get("expected_validation_passed", True))
    validation_passed_matches = bool(validation.get("passed")) == expected_validation_passed
    expected_reviewer_ready = bool(case.get("expected_reviewer_ready", True))
    reviewer_ready_matches = (
        bool(report.get("summary", {}).get("reviewer_ready")) == expected_reviewer_ready
    )
    require_graph_coverage = bool(case.get("require_graph_coverage", True))
    graph_coverage_supported = (
        not require_graph_coverage or _validation_checks_passed(validation, GRAPH_COVERAGE_CHECKS)
    )
    min_findings = int(case.get("min_findings", 1))
    min_findings_met = len(selected_findings) >= min_findings
    citation_coverage_supported = bool(selected_findings) and all(
        _finding_has_required_eval_citations(finding) for finding in selected_findings
    )

    result_flags = {
        "validation_passed_matches": validation_passed_matches,
        "reviewer_ready_matches": reviewer_ready_matches,
        "min_findings_met": min_findings_met,
        "expected_statuses_match": not status_mismatches,
        "expected_claim_types_match": not claim_type_mismatches,
        "expected_package_evidence_match": not package_evidence_mismatches,
        "expected_source_evidence_match": not source_evidence_mismatches,
        "expected_source_claim_links_match": not source_claim_link_mismatches,
        "expected_source_record_ids_match": not source_record_mismatches,
        "expected_source_document_roles_match": not source_document_role_mismatches,
        "status_counts_match": status_counts_match,
        "unsupported_finding_ids_match": unsupported_finding_ids_match,
        "citation_coverage_supported": citation_coverage_supported,
        "graph_coverage_supported": graph_coverage_supported,
    }
    failure_reasons = [
        name
        for name, passed in result_flags.items()
        if not passed
    ]
    failure_taxonomy = _failure_taxonomy(
        result_flags=result_flags,
        status_mismatches=status_mismatches,
        claim_type_mismatches=claim_type_mismatches,
        package_evidence_mismatches=package_evidence_mismatches,
        source_evidence_mismatches=source_evidence_mismatches,
        source_claim_link_mismatches=source_claim_link_mismatches,
        source_record_mismatches=source_record_mismatches,
        source_document_role_mismatches=source_document_role_mismatches,
        validation_failed_checks=_failed_check_names(validation),
        selected_findings=selected_findings,
    )
    return {
        "id": case["id"],
        "review_id": result.review_id,
        "source_set_id": report.get("summary", {}).get("source_set_id"),
        "rule_pack_id": report.get("summary", {}).get("rule_pack_id"),
        "rule_pack_version": report.get("summary", {}).get("rule_pack_version"),
        "package_path": str(package_path),
        "review_dir": str(result.review_dir),
        "compliance_review_path": str(result.compliance_review_path),
        "compliance_matrix_path": str(result.compliance_matrix_path),
        "compliance_matrix_markdown_path": str(result.compliance_matrix_markdown_path),
        "compliance_matrix_pdf_path": str(result.compliance_matrix_pdf_path),
        "compliance_validation_path": str(result.compliance_validation_path),
        "finding_nodes_path": str(result.finding_nodes_path),
        "finding_edges_path": str(result.finding_edges_path),
        "source_top_k": source_top_k,
        "package_top_k": package_top_k,
        "filters": filters,
        "finding_count": len(findings),
        "selected_finding_count": len(selected_findings),
        "finding_status_counts": actual_status_counts,
        "expected_statuses": expected_statuses,
        "actual_statuses": {
            rule_id: finding.get("status") for rule_id, finding in sorted(findings_by_rule.items())
        },
        "status_mismatches": status_mismatches,
        "expected_claim_types": expected_claim_types,
        "actual_claim_types": {
            rule_id: finding.get("claim_type")
            for rule_id, finding in sorted(findings_by_rule.items())
        },
        "claim_type_mismatches": claim_type_mismatches,
        "package_evidence_mismatches": package_evidence_mismatches,
        "source_evidence_mismatches": source_evidence_mismatches,
        "source_claim_link_mismatches": source_claim_link_mismatches,
        "expected_source_record_ids": expected_source_record_ids,
        "source_record_mismatches": source_record_mismatches,
        "expected_source_document_roles": expected_source_document_roles,
        "source_document_role_mismatches": source_document_role_mismatches,
        "expected_finding_status_counts": expected_status_counts,
        "expected_unsupported_finding_ids": expected_unsupported,
        "actual_unsupported_finding_ids": actual_unsupported,
        "expected_validation_passed": expected_validation_passed,
        "actual_validation_passed": bool(validation.get("passed")),
        "expected_reviewer_ready": expected_reviewer_ready,
        "actual_reviewer_ready": bool(report.get("summary", {}).get("reviewer_ready")),
        "require_graph_coverage": require_graph_coverage,
        "validation_failed_checks": _failed_check_names(validation),
        "finding_results": [_eval_finding_summary(finding) for finding in selected_findings],
        **result_flags,
        "failure_reasons": failure_reasons,
        "failure_taxonomy": failure_taxonomy,
        "failure_category_counts": dict(Counter(item["category"] for item in failure_taxonomy)),
        "reproduction": _case_reproduction(result, package_path),
        "passed": not failure_reasons,
    }


def _filter_eval_findings(findings: list[dict], filters: dict) -> list[dict]:
    return [
        finding
        for finding in findings
        if all(str(finding.get(key) or "") in set(_filter_values(value)) for key, value in filters.items())
    ]


def _filter_values(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _string_map(value: dict) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()}


def _expected_claim_type_map(case: dict, expected_statuses: dict[str, str]) -> dict[str, str]:
    expected = {rule_id: _claim_type(status) for rule_id, status in expected_statuses.items()}
    expected.update(_string_map(case.get("expected_claim_types") or {}))
    return expected


def _expected_bool_presence_map(
    case: dict,
    key: str,
    expected_statuses: dict[str, str],
    default_for_status,
) -> dict[str, bool]:
    expected = {
        rule_id: bool(default_for_status(status))
        for rule_id, status in expected_statuses.items()
    }
    expected.update({str(rule_id): bool(value) for rule_id, value in (case.get(key) or {}).items()})
    return expected


def _expected_string_list_map(case: dict, key: str) -> dict[str, list[str]]:
    return {
        str(rule_id): sorted({str(value) for value in values if str(value).strip()})
        for rule_id, values in (case.get(key) or {}).items()
    }


def _expected_subset_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, list[str]],
    actual_values,
) -> list[dict]:
    failures = []
    for rule_id, expected_values in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = actual_values(finding) if finding else []
        missing = sorted(set(expected_values) - set(actual))
        if missing:
            failures.append(
                {
                    "rule_id": rule_id,
                    "expected": expected_values,
                    "actual": actual,
                    "missing": missing,
                }
            )
    return failures


def _value_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, str],
    field: str,
) -> list[dict]:
    failures = []
    for rule_id, expected_value in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = finding.get(field) if finding else None
        if actual != expected_value:
            failures.append({"rule_id": rule_id, "expected": expected_value, "actual": actual})
    return failures


def _presence_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, bool],
    predicate,
) -> list[dict]:
    failures = []
    for rule_id, expected_value in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = bool(finding and predicate(finding))
        if actual != expected_value:
            failures.append({"rule_id": rule_id, "expected": expected_value, "actual": actual})
    return failures


def _finding_has_package_evidence(finding: dict) -> bool:
    return bool(finding.get("package_evidence_citation") and finding.get("package_evidence"))


def _finding_has_source_evidence(finding: dict) -> bool:
    return bool(finding.get("source_library_evidence_citation") and finding.get("source_library_evidence"))


def _finding_has_source_claim_links(finding: dict) -> bool:
    return bool(finding.get("source_claim_link_count") and finding.get("source_claim_links"))


def _finding_has_required_eval_citations(finding: dict) -> bool:
    status = finding.get("status")
    if status not in CLAIM_STATUSES:
        return True
    if not _finding_has_source_evidence(finding) or not _finding_has_source_claim_links(finding):
        return False
    if status == "pass" and not _finding_has_package_evidence(finding):
        return False
    return True


def _validation_checks_passed(validation: dict, names: set[str]) -> bool:
    checks_by_name = {str(check.get("name")): bool(check.get("passed")) for check in validation.get("checks", [])}
    return all(checks_by_name.get(name) for name in names)


def _eval_finding_summary(finding: dict) -> dict:
    return {
        "rule_id": finding.get("rule_id"),
        "status": finding.get("status"),
        "claim_type": finding.get("claim_type"),
        "package_evidence_citation": finding.get("package_evidence_citation"),
        "source_library_evidence_citation": finding.get("source_library_evidence_citation"),
        "source_claim_link_count": finding.get("source_claim_link_count", 0),
        "applied_source_record_ids": _finding_source_record_ids(finding),
        "applied_source_document_roles": _finding_source_document_roles(finding),
    }


def _failure_taxonomy(
    *,
    result_flags: dict[str, bool],
    status_mismatches: list[dict],
    claim_type_mismatches: list[dict],
    package_evidence_mismatches: list[dict],
    source_evidence_mismatches: list[dict],
    source_claim_link_mismatches: list[dict],
    source_record_mismatches: list[dict],
    source_document_role_mismatches: list[dict],
    validation_failed_checks: list[str],
    selected_findings: list[dict],
) -> list[dict]:
    taxonomy = []
    if not result_flags["validation_passed_matches"] or not result_flags["reviewer_ready_matches"]:
        taxonomy.append(
            _taxonomy_entry(
                "validation_gate_miss",
                validation_failed_checks,
                ["reviewer_ready", "validation_passed"],
            )
        )
    if not result_flags["min_findings_met"]:
        taxonomy.append(_taxonomy_entry("rule_wording_issue", [], ["min_findings"]))
    if status_mismatches or claim_type_mismatches:
        taxonomy.append(
            _taxonomy_entry(
                "rule_wording_issue",
                status_mismatches + claim_type_mismatches,
            )
        )
    if package_evidence_mismatches:
        taxonomy.append(
            _taxonomy_entry("package_evidence_search_miss", package_evidence_mismatches)
        )
    if source_evidence_mismatches:
        taxonomy.append(_taxonomy_entry("source_retrieval_miss", source_evidence_mismatches))
    if source_claim_link_mismatches:
        taxonomy.append(_taxonomy_entry("rule_claim_binding_miss", source_claim_link_mismatches))
    if source_record_mismatches or source_document_role_mismatches:
        taxonomy.append(
            _taxonomy_entry(
                "source_applicability_miss",
                source_record_mismatches + source_document_role_mismatches,
            )
        )
    if not result_flags["citation_coverage_supported"]:
        unsupported = [
            finding.get("rule_id")
            for finding in selected_findings
            if not _finding_has_required_eval_citations(finding)
        ]
        taxonomy.append(_taxonomy_entry("citation_relevance_issue", unsupported))
    if not result_flags["graph_coverage_supported"]:
        taxonomy.append(
            _taxonomy_entry(
                "finding_graph_miss",
                validation_failed_checks,
                sorted(GRAPH_COVERAGE_CHECKS),
            )
        )
    return taxonomy


def _taxonomy_entry(
    category: str,
    evidence: list,
    checks: list[str] | None = None,
) -> dict:
    rule_ids = sorted(
        {
            str(item.get("rule_id"))
            for item in evidence
            if isinstance(item, dict) and item.get("rule_id")
        }
    )
    if not rule_ids:
        rule_ids = sorted({str(item) for item in evidence if isinstance(item, str)})
    return {
        "category": category,
        "rule_ids": rule_ids,
        "checks": checks or [],
        "evidence": evidence,
    }


def _failure_category_counts(cases: list[dict]) -> dict[str, int]:
    counts = Counter()
    for case in cases:
        for item in case.get("failure_taxonomy", []):
            counts[str(item.get("category"))] += 1
    return dict(sorted(counts.items()))


def _case_reproduction(result: ComplianceReviewResult, package_path: Path) -> dict:
    return {
        "command": (
            "PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review "
            f"--package-path {package_path} --output-dir <source_library> "
            f"--review-id {result.review_id}"
        ),
        "review_dir": str(result.review_dir),
        "package_path": str(package_path),
        "compliance_review_path": str(result.compliance_review_path),
        "compliance_matrix_path": str(result.compliance_matrix_path),
        "compliance_matrix_pdf_path": str(result.compliance_matrix_pdf_path),
        "compliance_validation_path": str(result.compliance_validation_path),
    }


def _case_rate(cases: list[dict], key: str) -> float:
    return _rate(sum(1 for case in cases if case.get(key)), len(cases))


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


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


def _check_rule_package_section_preferences(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        invalid = []
        section_terms = rule.get("package_section_terms")
        section_term_groups = rule.get("package_section_term_groups")
        if section_terms is not None and not _valid_nonempty_term_list(section_terms):
            invalid.append("package_section_terms")
        if section_term_groups is not None and not _valid_nonempty_term_groups(
            section_term_groups
        ):
            invalid.append("package_section_term_groups")
        if invalid:
            failures.append(
                {
                    "rule_id": rule.get("id"),
                    "invalid": sorted(invalid),
                }
            )
    return {
        "name": "rule_package_section_preferences_are_valid",
        "passed": not failures,
        "details": {"failures": failures},
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


def _check_rule_authority_metadata(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
        authority_category = str(rule.get("authority_category") or "").strip()
        applicability_mode = str(rule.get("applicability_mode") or "").strip()
        source_record_id = str(
            rule.get("authority_source_record_id") or filters.get("source_record_id") or ""
        ).strip()
        missing = []
        invalid = []
        if not authority_category:
            missing.append("authority_category")
        elif authority_category not in AUTHORITY_CATEGORIES:
            invalid.append("authority_category")
        if not applicability_mode:
            missing.append("applicability_mode")
        elif applicability_mode not in APPLICABILITY_MODES:
            invalid.append("applicability_mode")
        if not source_record_id:
            missing.append("source_record_id")
        if applicability_mode == "conditional":
            terms = rule.get("applies_if_package_terms")
            term_groups = rule.get("applies_if_package_term_groups")
            negative_terms = rule.get("does_not_apply_if_package_terms")
            has_terms = isinstance(terms, list) and any(str(term).strip() for term in terms)
            has_term_groups = _valid_nonempty_term_groups(term_groups)
            if not has_terms and not has_term_groups:
                missing.append("applies_if_package_terms")
            if term_groups is not None and not has_term_groups:
                invalid.append("applies_if_package_term_groups")
            if negative_terms is not None and not _valid_nonempty_term_list(negative_terms):
                invalid.append("does_not_apply_if_package_terms")
        if missing or invalid:
            failures.append(
                {
                    "rule_id": rule.get("id"),
                    "missing": sorted(missing),
                    "invalid": sorted(invalid),
                }
            )
    return {
        "name": "rule_authority_metadata_present",
        "passed": not failures,
        "details": {
            "allowed_authority_categories": sorted(AUTHORITY_CATEGORIES),
            "allowed_applicability_modes": sorted(APPLICABILITY_MODES),
            "failures": failures,
        },
    }


def _valid_nonempty_term_groups(value) -> bool:
    return isinstance(value, list) and all(
        isinstance(group, list) and any(str(term).strip() for term in group)
        for group in value
    ) and bool(value)


def _valid_nonempty_term_list(value) -> bool:
    return isinstance(value, list) and all(str(term).strip() for term in value) and bool(value)


def _check_rule_pack_baseline_source_records(rule_pack: dict) -> dict:
    expected = _baseline_source_record_ids(rule_pack)
    raw_expected = rule_pack.get("baseline_source_record_ids")
    if raw_expected is None:
        return {
            "name": "baseline_source_records_covered",
            "passed": True,
            "details": {
                "enforced": False,
                "baseline_source_record_count": 0,
                "missing_source_record_ids": [],
                "non_baseline_rule_ids": [],
            },
        }
    invalid_shape = (
        not isinstance(raw_expected, list)
        or not expected
        or len(expected) != len(raw_expected)
    )
    duplicate_ids = sorted(
        source_record_id
        for source_record_id, count in Counter(expected).items()
        if count > 1
    )
    unsafe_ids = sorted(
        source_record_id
        for source_record_id in expected
        if not SAFE_ID_RE.fullmatch(source_record_id)
    )
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    rules_by_source_record_id = defaultdict(list)
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        source_record_id = _rule_source_record_id(rule)
        if source_record_id:
            rules_by_source_record_id[source_record_id].append(rule)
    missing = sorted(
        source_record_id
        for source_record_id in expected
        if source_record_id not in rules_by_source_record_id
    )
    non_baseline = sorted(
        str(rule.get("id"))
        for source_record_id in expected
        for rule in rules_by_source_record_id.get(source_record_id, [])
        if str(rule.get("applicability_mode") or "") != "baseline"
    )
    return {
        "name": "baseline_source_records_covered",
        "passed": not invalid_shape and not duplicate_ids and not unsafe_ids and not missing and not non_baseline,
        "details": {
            "enforced": True,
            "baseline_source_record_count": len(expected),
            "missing_source_record_ids": missing,
            "duplicate_source_record_ids": duplicate_ids,
            "unsafe_source_record_ids": unsafe_ids,
            "non_baseline_rule_ids": non_baseline,
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


def _check_baseline_source_documents_evaluated(rule_pack: dict, findings: list[dict]) -> dict:
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


def _check_forest_plan_component_gate(forest_plan_summary: dict) -> dict:
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


def _check_applicable_findings_have_authority_source_records(findings: list[dict]) -> dict:
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
        "baseline_source_record_ids": _baseline_source_record_ids(rule_pack),
        "rule_count": len(rule_pack["rules"]),
    }


def _baseline_source_record_ids(rule_pack: dict) -> list[str]:
    raw = rule_pack.get("baseline_source_record_ids")
    if not isinstance(raw, list):
        return []
    return [str(value).strip() for value in raw if str(value or "").strip()]


def _rule_source_record_id(rule: dict) -> str | None:
    filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    value = rule.get("authority_source_record_id") or filters.get("source_record_id")
    if not str(value or "").strip():
        return None
    return str(value).strip()


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
