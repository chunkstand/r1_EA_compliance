from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .compliance_authority_integration import (
    authority_integration_context as _authority_integration_context,
    write_authority_integration_artifacts as _write_authority_integration_artifacts,
)
from .compliance_finding_graph import attach_forest_plan_graph as _attach_forest_plan_graph
from .compliance_finding_graph import finding_graph as _finding_graph
from .compliance_findings import DEFAULT_AUTHORITY_FAMILY_INVENTORY_PATH
from .compliance_findings import authority_family_index as _authority_family_index
from .compliance_findings import compliance_finding as _compliance_finding
from .compliance_inputs import applicability_gate_context as _applicability_gate_context
from .compliance_inputs import first_present as _first_present
from .compliance_inputs import write_evaluation_rule_pack as _write_evaluation_rule_pack
from .compliance_outputs import build_compliance_matrix
from .compliance_outputs import build_compliance_matrix_render_manifest
from .compliance_outputs import matrix_markdown
from .compliance_outputs import write_compliance_matrix_pdf
from .compliance_validation import compliance_summary as _summary
from .compliance_validation import rule_pack_summary as _rule_pack_summary
from .compliance_validation import validation_report as _validation_report
from .ea_review import run_ea_review
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_resolver import DEFAULT_FOREST_PLAN_PROFILE_ID
from .forest_plan_resolver import run_forest_plan_resolver
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import SAFE_ID_RE
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


COMPLIANCE_REVIEW_SCHEMA_VERSION = "compliance-review-v0"
COMPLIANCE_MATRIX_SCHEMA_VERSION = "compliance-matrix-v0"


@dataclass(frozen=True)
class ComplianceReviewResult:
    review_id: str
    review_dir: Path
    compliance_review_path: Path
    compliance_matrix_path: Path
    compliance_matrix_markdown_path: Path
    compliance_matrix_pdf_path: Path
    compliance_matrix_render_manifest_path: Path
    compliance_validation_path: Path
    authority_provenance_path: Path
    non_applicable_authority_appendix_path: Path
    non_applicable_authority_appendix_markdown_path: Path
    reviewer_resolution_report_path: Path
    litigation_risk_summary_path: Path
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
    forest_unit_id: str = DEFAULT_FOREST_PLAN_PROFILE_ID,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    review_id: str | None = None,
    results_dir: Path | None = None,
    source_top_k: int = 3,
    package_top_k: int = 3,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
    reuse_package_cache: bool = False,
    allow_base_rule_pack_review: bool = False,
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

    if source_set_id is None:
        source_set_id = _first_present(rule_pack.get("source_set_id"))
    review_id = review_id or _first_present(rule_pack.get("review_id")) or _default_review_id(
        package_path,
        rule_pack,
    )
    _validate_safe_id(review_id, "review_id")
    if source_set_id:
        _validate_safe_id(source_set_id, "source_set_id")
    review_dir = Path(results_dir) if results_dir else output_dir / "reviews" / review_id
    compliance_review_path = review_dir / "compliance_review.json"
    compliance_matrix_path = review_dir / "compliance_matrix.json"
    compliance_matrix_markdown_path = review_dir / "compliance_matrix.md"
    compliance_matrix_pdf_path = review_dir / "compliance_matrix.pdf"
    review_packet_index_dir = review_dir / "review_packet_index"
    compliance_matrix_render_manifest_path = (
        review_packet_index_dir / "compliance_matrix_render_manifest.json"
    )
    compliance_validation_path = review_dir / "compliance_validation.json"
    authority_provenance_path = review_dir / "authority_family_provenance.json"
    non_applicable_authority_appendix_path = review_dir / "non_applicable_authority_appendix.json"
    non_applicable_authority_appendix_markdown_path = (
        review_dir / "non_applicable_authority_appendix.md"
    )
    reviewer_resolution_report_path = review_dir / "authority_reviewer_resolution_report.json"
    litigation_risk_summary_path = review_dir / "litigation_risk_summary.json"
    finding_nodes_path = review_dir / "finding_graph_nodes.jsonl"
    finding_edges_path = review_dir / "finding_graph_edges.jsonl"
    _prepare_outputs(
        compliance_review_path=compliance_review_path,
        compliance_matrix_path=compliance_matrix_path,
        compliance_matrix_markdown_path=compliance_matrix_markdown_path,
        compliance_matrix_pdf_path=compliance_matrix_pdf_path,
        compliance_matrix_render_manifest_path=compliance_matrix_render_manifest_path,
        compliance_validation_path=compliance_validation_path,
        authority_provenance_path=authority_provenance_path,
        non_applicable_authority_appendix_path=non_applicable_authority_appendix_path,
        non_applicable_authority_appendix_markdown_path=non_applicable_authority_appendix_markdown_path,
        reviewer_resolution_report_path=reviewer_resolution_report_path,
        litigation_risk_summary_path=litigation_risk_summary_path,
        finding_nodes_path=finding_nodes_path,
        finding_edges_path=finding_edges_path,
    )
    applicability_gate = _applicability_gate_context(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
        rule_pack=rule_pack,
        allow_base_rule_pack_review=allow_base_rule_pack_review,
    )
    evaluation_rule_pack_path = _write_evaluation_rule_pack(
        review_dir=review_dir,
        rule_pack_path=rule_pack_path,
        rule_pack=rule_pack,
        applicability_gate=applicability_gate,
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
    authority_family_index = _authority_family_index(DEFAULT_AUTHORITY_FAMILY_INVENTORY_PATH)

    ea_result = run_ea_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=index_path,
        checklist_path=evaluation_rule_pack_path,
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
        forest_unit_id=forest_unit_id,
        profiles_path=forest_plan_profiles_path,
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
            authority_family_index=authority_family_index,
        )
        for finding in ea_report["findings"]
    ]
    authority_integration = _authority_integration_context(
        review_id=review_id,
        source_set_id=source_set_id or str(ea_report["summary"].get("source_set_id") or ""),
        rule_pack=rule_pack,
        findings=findings,
        applicability_gate=applicability_gate,
        authority_provenance_path=authority_provenance_path,
        non_applicable_authority_appendix_path=non_applicable_authority_appendix_path,
        non_applicable_authority_appendix_markdown_path=non_applicable_authority_appendix_markdown_path,
        reviewer_resolution_report_path=reviewer_resolution_report_path,
        litigation_risk_summary_path=litigation_risk_summary_path,
    )
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
        applicability_gate=applicability_gate,
        package_manifest_path=ea_result.package_manifest_path,
        package_chunks_path=ea_result.package_chunks_path,
        authority_integration=authority_integration,
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
        applicability_gate=applicability_gate,
        authority_integration=authority_integration,
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
    matrix = build_compliance_matrix(
        review_id=review_id,
        package_path=package_path,
        rule_pack=rule_pack,
        findings=findings,
        summary=summary,
        validation=validation,
        applicability_gate=applicability_gate,
    )
    matrix["summary"]["compliance_matrix_render_manifest_path"] = str(
        compliance_matrix_render_manifest_path
    )
    _write_authority_integration_artifacts(
        context=authority_integration,
        summary=summary,
        validation=validation,
    )
    _write_jsonl(finding_nodes_path, nodes)
    _write_jsonl(finding_edges_path, edges)
    _write_json(compliance_matrix_path, matrix)
    compliance_matrix_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_markdown_text = matrix_markdown(matrix)
    compliance_matrix_markdown_path.write_text(
        matrix_markdown_text,
        encoding="utf-8",
    )
    write_compliance_matrix_pdf(compliance_matrix_pdf_path, matrix)
    render_manifest = build_compliance_matrix_render_manifest(
        matrix=matrix,
        markdown=matrix_markdown_text,
        pdf_path=compliance_matrix_pdf_path,
    )
    _write_json(compliance_matrix_render_manifest_path, render_manifest)
    _write_json(compliance_validation_path, validation)
    _write_json(compliance_review_path, report)
    return ComplianceReviewResult(
        review_id=review_id,
        review_dir=review_dir,
        compliance_review_path=compliance_review_path,
        compliance_matrix_path=compliance_matrix_path,
        compliance_matrix_markdown_path=compliance_matrix_markdown_path,
        compliance_matrix_pdf_path=compliance_matrix_pdf_path,
        compliance_matrix_render_manifest_path=compliance_matrix_render_manifest_path,
        compliance_validation_path=compliance_validation_path,
        authority_provenance_path=authority_provenance_path,
        non_applicable_authority_appendix_path=non_applicable_authority_appendix_path,
        non_applicable_authority_appendix_markdown_path=non_applicable_authority_appendix_markdown_path,
        reviewer_resolution_report_path=reviewer_resolution_report_path,
        litigation_risk_summary_path=litigation_risk_summary_path,
        finding_nodes_path=finding_nodes_path,
        finding_edges_path=finding_edges_path,
        rule_claim_links_path=rule_claim_result.links_path,
        rule_claim_validation_path=rule_claim_result.validation_path,
        ea_review_report_path=ea_result.json_report_path,
        ea_review_validation_path=ea_result.validation_path,
        summary=summary,
    )


def _prepare_outputs(
    *,
    compliance_review_path: Path,
    compliance_matrix_path: Path,
    compliance_matrix_markdown_path: Path,
    compliance_matrix_pdf_path: Path,
    compliance_matrix_render_manifest_path: Path,
    compliance_validation_path: Path,
    authority_provenance_path: Path,
    non_applicable_authority_appendix_path: Path,
    non_applicable_authority_appendix_markdown_path: Path,
    reviewer_resolution_report_path: Path,
    litigation_risk_summary_path: Path,
    finding_nodes_path: Path,
    finding_edges_path: Path,
) -> None:
    for path in (
        compliance_review_path,
        compliance_matrix_path,
        compliance_matrix_markdown_path,
        compliance_matrix_pdf_path,
        compliance_matrix_render_manifest_path,
        compliance_validation_path,
        authority_provenance_path,
        non_applicable_authority_appendix_path,
        non_applicable_authority_appendix_markdown_path,
        reviewer_resolution_report_path,
        litigation_risk_summary_path,
        finding_nodes_path,
        finding_edges_path,
    ):
        path.unlink(missing_ok=True)


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
