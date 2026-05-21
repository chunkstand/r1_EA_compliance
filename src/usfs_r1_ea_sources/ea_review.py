from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .retrieval import default_index_path
from .retrieval import query_retrieval_index
from .review_package_support import discover_package_files
from .review_package_support import extract_package_files
from .review_package_support import load_package_cache
from .review_package_support import prepare_review_outputs
from .review_package_support import retrieval_artifacts
from .review_package_support import search_package_chunks
from .review_package_support import source_set_id_from_catalog
from .review_package_support import source_set_id_from_index
from .review_package_support import utc_now
from .review_package_support import write_json
from .review_package_support import write_jsonl
from .records import reconciled_source_record_ids


DEFAULT_CHECKLIST_PATH = Path("config/ea_review_checklist_seed.json")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class EAReviewResult:
    review_id: str
    review_dir: Path
    package_manifest_path: Path
    package_chunks_path: Path
    validation_path: Path
    json_report_path: Path
    markdown_report_path: Path
    summary: dict


def run_ea_review(
    *,
    package_path: Path,
    output_dir: Path,
    source_set_id: str | None = None,
    index_path: Path | None = None,
    checklist_path: Path = DEFAULT_CHECKLIST_PATH,
    review_id: str | None = None,
    results_dir: Path | None = None,
    source_top_k: int = 3,
    package_top_k: int = 3,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
    reuse_package_cache: bool = False,
) -> EAReviewResult:
    """Run a deterministic, provenance-bearing EA package checklist review."""

    package_path = Path(package_path)
    output_dir = Path(output_dir)
    checklist_path = Path(checklist_path)
    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")
    if package_top_k < 1:
        raise ValueError("package_top_k must be at least 1")
    if not package_path.exists():
        raise FileNotFoundError(f"Missing EA package path: {package_path}")
    if not checklist_path.exists():
        raise FileNotFoundError(f"Missing EA review checklist: {checklist_path}")

    if index_path is None:
        index_path = default_index_path(output_dir, source_set_id)
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"Missing source-library retrieval index: {index_path}")
    if source_set_id is None:
        source_set_id = source_set_id_from_index(index_path) or source_set_id_from_catalog(
            output_dir
        )
    retrieval_readiness = _retrieval_readiness_report(
        index_path=index_path,
        source_set_id=source_set_id,
    )
    if not retrieval_readiness["passed"]:
        failed = ", ".join(
            check["name"] for check in retrieval_readiness["checks"] if not check["passed"]
        )
        raise ValueError(
            "EA review requires a reviewer-ready source-library retrieval index. "
            f"Failed readiness checks: {failed}"
        )

    review_id = review_id or _default_review_id(package_path)
    _validate_safe_id(review_id, "review_id")
    review_dir = Path(results_dir) if results_dir else output_dir / "reviews" / review_id
    package_dir = review_dir / "package"
    extracted_text_dir = package_dir / "extracted_text"
    docling_json_dir = package_dir / "docling_json"
    package_manifest_path = package_dir / "package_manifest.jsonl"
    package_chunks_path = package_dir / "package_chunks.jsonl"
    validation_path = review_dir / "review_validation.json"
    json_report_path = review_dir / "review_report.json"
    markdown_report_path = review_dir / "review_report.md"
    prepare_review_outputs(
        package_dir=package_dir,
        output_paths=(validation_path, json_report_path, markdown_report_path),
        preserve_package_cache=reuse_package_cache,
    )

    checklist = _load_checklist(checklist_path)
    if reuse_package_cache:
        package_manifest, package_chunks = load_package_cache(
            package_manifest_path=package_manifest_path,
            package_chunks_path=package_chunks_path,
        )
    else:
        for directory in (extracted_text_dir, docling_json_dir):
            directory.mkdir(parents=True, exist_ok=True)
        package_manifest, package_chunks = extract_package_files(
            package_files=discover_package_files(package_path),
            review_id=review_id,
            extracted_text_dir=extracted_text_dir,
            docling_json_dir=docling_json_dir,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            docling_ocr=docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
        )
        write_jsonl(package_manifest_path, package_manifest)
        write_jsonl(package_chunks_path, package_chunks)

    findings = []
    for item in checklist:
        package_search = search_package_chunks(
            package_chunks,
            query=str(item.get("package_query") or item.get("query") or item["title"]),
            required_terms=[str(term) for term in item.get("package_terms", [])],
            limit=package_top_k,
            preferred_terms=_package_term_list(item, "package_section_terms"),
            preferred_term_groups=_package_term_groups(item, "package_section_term_groups"),
        )
        source_filters = dict(item.get("source_filters") or {})
        source_record_filter_ids = reconciled_source_record_ids(
            source_record_id=source_filters.get("source_record_id")
        )
        source_query = query_retrieval_index(
            index_path=index_path,
            query=str(item.get("source_query") or item.get("query") or item["title"]),
            limit=source_top_k,
            document_role=source_filters.get("document_role"),
            authority_level=source_filters.get("authority_level"),
            source_record_id=source_filters.get("source_record_id"),
            source_record_ids=source_record_filter_ids,
            review_topic=source_filters.get("review_topic") or source_filters.get("topic"),
            citation=source_filters.get("citation"),
            host=source_filters.get("host"),
        )
        finding = _finding_for_item(
            item=item,
            package_chunks=package_chunks,
            package_search=package_search,
            source_query=source_query,
            source_filters=source_filters,
        )
        findings.append(finding)

    summary = _summary(
        review_id=review_id,
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=index_path,
        checklist_path=checklist_path,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        findings=findings,
        json_report_path=json_report_path,
        markdown_report_path=markdown_report_path,
        package_manifest_path=package_manifest_path,
        package_chunks_path=package_chunks_path,
        retrieval_readiness=retrieval_readiness,
    )
    validation = _validation_report(
        source_set_id=source_set_id,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        findings=findings,
        retrieval_readiness=retrieval_readiness,
    )
    summary["validation_passed"] = validation["passed"]
    summary["validation_path"] = str(validation_path)
    summary["reviewer_ready"] = validation["passed"]
    report = {
        "schema_version": "ea-review-v0",
        "created_at": utc_now(),
        "summary": summary,
        "validation": validation,
        "findings": findings,
    }
    review_dir.mkdir(parents=True, exist_ok=True)
    write_json(validation_path, validation)
    write_json(json_report_path, report)
    markdown_report_path.write_text(_markdown_report(report), encoding="utf-8")
    return EAReviewResult(
        review_id=review_id,
        review_dir=review_dir,
        package_manifest_path=package_manifest_path,
        package_chunks_path=package_chunks_path,
        validation_path=validation_path,
        json_report_path=json_report_path,
        markdown_report_path=markdown_report_path,
        summary=summary,
    )


def _applicability_term_groups(item: dict) -> list[list[str]]:
    return _package_term_groups(item, "applies_if_package_term_groups")


def _package_term_groups(item: dict, key: str) -> list[list[str]]:
    groups = []
    for group in item.get(key, []) or []:
        if not isinstance(group, list):
            continue
        terms = [str(term).strip() for term in group if str(term).strip()]
        if terms:
            groups.append(terms)
    return groups


def _package_term_list(item: dict, key: str) -> list[str]:
    return [
        str(term).strip()
        for term in item.get(key, []) or []
        if str(term).strip()
    ]


def _finding_for_item(
    *,
    item: dict,
    package_chunks: list[dict],
    package_search: dict,
    source_query: dict,
    source_filters: dict,
) -> dict:
    package_evidence = package_search["results"][0] if package_search["results"] else None
    source_evidence = source_query["results"][0] if source_query["results"] else None
    applicability_terms = _package_term_list(item, "applies_if_package_terms")
    applicability_term_groups = _applicability_term_groups(item)
    applicability_negative_terms = _package_term_list(
        item,
        "does_not_apply_if_package_terms",
    )
    applicability_mode = str(
        item.get("applicability_mode")
        or ("conditional" if applicability_terms or applicability_term_groups else "baseline")
    )
    applicability = True
    applicability_evidence = None
    applicability_negative_evidence = None
    explicit_negative_match = False
    if applicability_terms or applicability_term_groups:
        if applicability_negative_terms:
            negative_search = search_package_chunks(
                package_chunks,
                query=" ".join(applicability_negative_terms),
                required_terms=applicability_negative_terms,
                limit=1,
            )
            applicability_negative_evidence = (
                negative_search["results"][0] if negative_search["results"] else None
            )
        search_terms = applicability_terms or [
            term for group in applicability_term_groups for term in group
        ]
        applicability_search = search_package_chunks(
            package_chunks,
            query=" ".join(search_terms),
            required_terms=search_terms,
            required_term_groups=applicability_term_groups,
            preferred_terms=_package_term_list(item, "package_section_terms"),
            preferred_term_groups=_package_term_groups(item, "package_section_term_groups"),
            limit=1,
        )
        applicability_evidence = (
            applicability_search["results"][0] if applicability_search["results"] else None
        )
        explicit_negative_match = bool(applicability_negative_evidence) and (
            not applicability_evidence
            or applicability_negative_evidence["chunk_id"] == applicability_evidence["chunk_id"]
        )
        if explicit_negative_match:
            applicability_evidence = None
        applicability = bool(applicability_evidence) and not explicit_negative_match
    if not applicability:
        status = "not_applicable"
        confidence = 0.6
        if explicit_negative_match:
            applicability_rationale = (
                "The EA package contains explicit non-applicability evidence for this "
                "conditional authority."
            )
        else:
            applicability_rationale = "The applicability trigger terms were not found in the EA package."
        rationale = applicability_rationale
    elif package_evidence and source_evidence:
        status = "pass"
        confidence = 0.82
        applicability_rationale = "The authority was applicable to the EA package."
        rationale = "The EA package contains matching evidence and the source library provides supporting review authority."
    elif source_evidence and not package_evidence:
        status = "gap"
        confidence = 0.74
        applicability_rationale = "The authority was applicable to the EA package."
        rationale = "The source library supports this review requirement, but matching EA package evidence was not found."
    else:
        status = "uncertain"
        confidence = 0.35
        applicability_rationale = "The authority was applicable to the EA package."
        rationale = "The review item is not supported by enough package and source-library evidence for a deterministic finding."
    return {
        "id": item["id"],
        "title": item["title"],
        "question": item.get("question") or item["title"],
        "severity": item.get("severity", "medium"),
        "status": status,
        "confidence": confidence,
        "rationale": rationale,
        "package_query": package_search["query"],
        "package_terms": package_search["required_terms"],
        "source_query": source_query["query"],
        "source_filters": source_filters,
        "applicability_status": "applicable" if applicability else "not_applicable",
        "applicability_mode": applicability_mode,
        "applicability_terms": applicability_terms,
        "applicability_term_groups": applicability_term_groups,
        "applicability_negative_terms": applicability_negative_terms,
        "applicability_rationale": applicability_rationale,
        "applicability_evidence": applicability_evidence,
        "applicability_negative_evidence": applicability_negative_evidence,
        "package_evidence_status": "found" if package_evidence else "not_found",
        "source_library_evidence_status": "found" if source_evidence else "not_found",
        "package_evidence": package_evidence,
        "source_library_evidence": source_evidence,
        "package_results": package_search["results"],
        "source_library_results": source_query["results"],
        "limitations": _finding_limitations(package_evidence, source_evidence),
    }


def _finding_limitations(package_evidence: dict | None, source_evidence: dict | None) -> list[str]:
    limitations = []
    if package_evidence is None:
        limitations.append("No matching EA package evidence span was found by deterministic lexical search.")
    if source_evidence is None:
        limitations.append("No supporting source-library evidence span was found; no compliance claim is made.")
    return limitations


def _summary(
    *,
    review_id: str,
    package_path: Path,
    output_dir: Path,
    source_set_id: str,
    index_path: Path,
    checklist_path: Path,
    package_manifest: list[dict],
    package_chunks: list[dict],
    findings: list[dict],
    json_report_path: Path,
    markdown_report_path: Path,
    package_manifest_path: Path,
    package_chunks_path: Path,
    retrieval_readiness: dict,
) -> dict:
    status_counts = Counter(finding["status"] for finding in findings)
    parser_counts = Counter(
        record.get("parser_name") for record in package_manifest if record.get("parser_name")
    )
    extracted_count = sum(1 for record in package_manifest if record.get("status") == "extracted")
    failed_records = [record for record in package_manifest if record.get("status") != "extracted"]
    unsupported_findings = [
        finding["id"]
        for finding in findings
        if finding["status"] != "not_applicable"
        and finding["source_library_evidence_status"] != "found"
    ]
    return {
        "review_id": review_id,
        "package_path": str(package_path),
        "output_dir": str(output_dir),
        "source_set_id": source_set_id,
        "index_path": str(index_path),
        "checklist_path": str(checklist_path),
        "package_manifest_path": str(package_manifest_path),
        "package_chunks_path": str(package_chunks_path),
        "json_report_path": str(json_report_path),
        "markdown_report_path": str(markdown_report_path),
        "package_file_count": len(package_manifest),
        "package_extracted_count": extracted_count,
        "package_failed_count": len(failed_records),
        "package_chunk_count": len(package_chunks),
        "package_parser_counts": dict(parser_counts),
        "finding_count": len(findings),
        "finding_status_counts": dict(status_counts),
        "unsupported_finding_ids": unsupported_findings,
        "retrieval_readiness": retrieval_readiness,
        "reviewer_ready": not failed_records and not unsupported_findings,
    }


def _validation_report(
    *,
    source_set_id: str,
    package_manifest: list[dict],
    package_chunks: list[dict],
    findings: list[dict],
    retrieval_readiness: dict,
) -> dict:
    checks = [
        {
            "name": "source_retrieval_is_reviewer_ready",
            "passed": bool(retrieval_readiness.get("passed")),
            "details": retrieval_readiness,
        },
        _check_package_files_extracted(package_manifest),
        _check_package_chunks_exist(package_manifest, package_chunks),
        _check_finding_statuses_are_valid(findings),
        _check_pass_findings_have_dual_evidence(findings),
        _check_gap_findings_have_source_evidence(findings),
        _check_no_unsupported_compliance_claims(findings),
    ]
    return {
        "source_set_id": source_set_id,
        "created_at": utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_package_files_extracted(package_manifest: list[dict]) -> dict:
    failed = [
        {
            "source_record_id": record.get("source_record_id"),
            "status": record.get("status"),
            "failure": record.get("failure"),
        }
        for record in package_manifest
        if record.get("status") != "extracted"
    ]
    return {
        "name": "package_files_extracted",
        "passed": not failed and bool(package_manifest),
        "details": {
            "package_file_count": len(package_manifest),
            "failed_count": len(failed),
            "failures": failed[:50],
        },
    }


def _check_package_chunks_exist(package_manifest: list[dict], package_chunks: list[dict]) -> dict:
    missing = [
        record.get("source_record_id")
        for record in package_manifest
        if record.get("status") == "extracted" and int(record.get("chunk_count") or 0) <= 0
    ]
    return {
        "name": "package_chunks_exist",
        "passed": bool(package_chunks) and not missing,
        "details": {
            "package_chunk_count": len(package_chunks),
            "extracted_records_without_chunks": missing,
        },
    }


def _check_finding_statuses_are_valid(findings: list[dict]) -> dict:
    valid = {"pass", "gap", "uncertain", "not_applicable"}
    invalid = [
        {"id": finding.get("id"), "status": finding.get("status")}
        for finding in findings
        if finding.get("status") not in valid
    ]
    return {
        "name": "finding_statuses_are_valid",
        "passed": not invalid and bool(findings),
        "details": {"invalid": invalid, "finding_count": len(findings)},
    }


def _check_pass_findings_have_dual_evidence(findings: list[dict]) -> dict:
    failures = [
        finding.get("id")
        for finding in findings
        if finding.get("status") == "pass"
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
        finding.get("id")
        for finding in findings
        if finding.get("status") == "gap"
        and finding.get("source_library_evidence_status") != "found"
    ]
    return {
        "name": "gap_findings_have_source_evidence",
        "passed": not failures,
        "details": {"finding_ids": failures},
    }


def _check_no_unsupported_compliance_claims(findings: list[dict]) -> dict:
    unsupported = [
        finding.get("id")
        for finding in findings
        if finding.get("status") in {"pass", "gap"}
        and finding.get("source_library_evidence_status") != "found"
    ]
    return {
        "name": "no_unsupported_compliance_claims",
        "passed": not unsupported,
        "details": {"finding_ids": unsupported},
    }


def _markdown_report(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# EA Package Review",
        "",
        f"- Review ID: `{summary['review_id']}`",
        f"- Package: `{summary['package_path']}`",
        f"- Source set: `{summary['source_set_id']}`",
        f"- Reviewer ready: `{summary['reviewer_ready']}`",
        f"- Findings: `{summary['finding_status_counts']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in report["findings"]:
        lines.extend(
            [
                f"### {finding['title']}",
                "",
                f"- Status: `{finding['status']}`",
                f"- Severity: `{finding['severity']}`",
                f"- Confidence: `{finding['confidence']}`",
                f"- Rationale: {finding['rationale']}",
            ]
        )
        if finding["package_evidence"]:
            evidence = finding["package_evidence"]
            lines.extend(
                [
                    f"- EA evidence: `{evidence['citation_label']}` "
                    f"chars {evidence['evidence_span']['source_char_start']}-"
                    f"{evidence['evidence_span']['source_char_end']}",
                    f"  - {evidence['evidence_span']['text']}",
                ]
            )
        else:
            lines.append("- EA evidence: not found")
        if finding["source_library_evidence"]:
            evidence = finding["source_library_evidence"]
            lines.extend(
                [
                    f"- Source evidence: `{evidence['citation_label']}` "
                    f"chars {evidence['evidence_span']['source_char_start']}-"
                    f"{evidence['evidence_span']['source_char_end']}",
                    f"  - {evidence['evidence_span']['text']}",
                ]
            )
        else:
            lines.append("- Source evidence: not found")
        if finding["limitations"]:
            lines.append(f"- Limitations: {'; '.join(finding['limitations'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_checklist(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and isinstance(value.get("rules"), list):
        value = value["rules"]
    if not isinstance(value, list) or not value:
        raise ValueError("EA review checklist or rule pack must contain a non-empty rule array.")
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Checklist item {index} must be an object.")
        for field in ("id", "title"):
            if not item.get(field):
                raise ValueError(f"Checklist item {index} is missing {field!r}.")
    return value


def _retrieval_readiness_report(*, index_path: Path, source_set_id: str) -> dict:
    summary_path, validation_path, summary, validation = retrieval_artifacts(index_path)
    checks = [
        {
            "name": "retrieval_index_exists",
            "passed": index_path.exists(),
            "details": {"path": str(index_path)},
        },
        {
            "name": "retrieval_summary_exists",
            "passed": summary is not None,
            "details": {"path": str(summary_path)},
        },
        {
            "name": "retrieval_validation_exists",
            "passed": validation is not None,
            "details": {"path": str(validation_path)},
        },
        {
            "name": "retrieval_source_set_matches",
            "passed": bool(summary and summary.get("source_set_id") == source_set_id),
            "details": {
                "expected_source_set_id": source_set_id,
                "summary_source_set_id": (summary or {}).get("source_set_id"),
            },
        },
        {
            "name": "retrieval_validation_passed",
            "passed": bool(validation and validation.get("passed")),
            "details": {"passed": bool(validation and validation.get("passed"))},
        },
        {
            "name": "retrieval_summary_reviewer_ready",
            "passed": bool(summary and summary.get("reviewer_ready")),
            "details": {"reviewer_ready": bool(summary and summary.get("reviewer_ready"))},
        },
    ]
    return {
        "index_path": str(index_path),
        "summary_path": str(summary_path),
        "validation_path": str(validation_path),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _default_review_id(package_path: Path) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"ea-review-{_safe_id(package_path.stem or package_path.name)}-{stamp}"


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return safe or "package"


def _validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dot, underscore, or hyphen."
        )
