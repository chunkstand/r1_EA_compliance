from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
import shutil

from .extract import _chunk_id
from .extract import _chunk_text
from .extract import _effective_parser
from .extract import _extract_payload
from .extract import _utc_now
from .extract import ExtractionFailure
from .retrieval import default_index_path
from .retrieval import query_retrieval_index
from .records import sha256_file


DEFAULT_CHECKLIST_PATH = Path("config/ea_review_checklist_seed.json")
SUPPORTED_PACKAGE_SUFFIXES = {".pdf", ".html", ".htm", ".xml", ".docx", ".txt", ".md"}
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
STOPWORDS = {
    "about",
    "also",
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "not",
    "that",
    "the",
    "their",
    "this",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "with",
}


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
        source_set_id = _source_set_id_from_index(index_path) or _source_set_id_from_catalog(output_dir)
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
    _prepare_review_outputs(
        package_dir=package_dir,
        validation_path=validation_path,
        json_report_path=json_report_path,
        markdown_report_path=markdown_report_path,
    )
    for directory in (extracted_text_dir, docling_json_dir):
        directory.mkdir(parents=True, exist_ok=True)

    checklist = _load_checklist(checklist_path)
    package_files = _discover_package_files(package_path)
    extracted_at = _utc_now()
    package_manifest, package_chunks = _extract_package_files(
        package_files=package_files,
        review_id=review_id,
        extracted_text_dir=extracted_text_dir,
        docling_json_dir=docling_json_dir,
        extracted_at=extracted_at,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
    )
    _write_jsonl(package_manifest_path, package_manifest)
    _write_jsonl(package_chunks_path, package_chunks)

    findings = []
    for item in checklist:
        package_search = _search_package_chunks(
            package_chunks,
            query=str(item.get("package_query") or item.get("query") or item["title"]),
            required_terms=[str(term) for term in item.get("package_terms", [])],
            limit=package_top_k,
        )
        source_filters = dict(item.get("source_filters") or {})
        source_query = query_retrieval_index(
            index_path=index_path,
            query=str(item.get("source_query") or item.get("query") or item["title"]),
            limit=source_top_k,
            document_role=source_filters.get("document_role"),
            authority_level=source_filters.get("authority_level"),
            source_record_id=source_filters.get("source_record_id"),
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
        "created_at": _utc_now(),
        "summary": summary,
        "validation": validation,
        "findings": findings,
    }
    review_dir.mkdir(parents=True, exist_ok=True)
    _write_json(validation_path, validation)
    _write_json(json_report_path, report)
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


def _prepare_review_outputs(
    *,
    package_dir: Path,
    validation_path: Path,
    json_report_path: Path,
    markdown_report_path: Path,
) -> None:
    if package_dir.exists():
        shutil.rmtree(package_dir)
    for path in (validation_path, json_report_path, markdown_report_path):
        path.unlink(missing_ok=True)


def _discover_package_files(package_path: Path) -> list[Path]:
    if package_path.is_file():
        candidates = [package_path]
    else:
        candidates = [path for path in package_path.rglob("*") if path.is_file()]
    supported = [
        path
        for path in sorted(candidates)
        if path.suffix.lower() in SUPPORTED_PACKAGE_SUFFIXES
    ]
    if not supported:
        raise ValueError(
            f"EA package has no supported files under {package_path}. "
            f"Supported suffixes: {', '.join(sorted(SUPPORTED_PACKAGE_SUFFIXES))}"
        )
    return supported


def _extract_package_files(
    *,
    package_files: list[Path],
    review_id: str,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    extracted_at: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
) -> tuple[list[dict], list[dict]]:
    manifest = []
    chunks = []
    package_source_set_id = f"ea-package-{_safe_id(review_id)}"
    for index, package_file in enumerate(package_files, start=1):
        artifact_sha256 = sha256_file(package_file)
        source_record_id = f"EA-PACKAGE-{index:03d}"
        citation_label = f"{source_record_id} ({artifact_sha256[:12]})"
        row = _package_row(
            package_file=package_file,
            source_set_id=package_source_set_id,
            source_record_id=source_record_id,
            artifact_sha256=artifact_sha256,
            citation_label=citation_label,
        )
        base_record = {
            "source_set_id": package_source_set_id,
            "source_record_id": source_record_id,
            "title": package_file.name,
            "artifact_path": str(package_file),
            "artifact_sha256": artifact_sha256,
            "artifact_byte_size": package_file.stat().st_size,
            "content_type": row["content_type"],
            "citation_label": citation_label,
            "extracted_at": extracted_at,
            "status": None,
            "failure": None,
        }
        try:
            payload = _extract_payload(
                row=row,
                artifact_path=package_file,
                prefer_docling=False,
                docling_ocr=docling_ocr,
                docling_timeout_seconds=docling_timeout_seconds,
            )
        except ExtractionFailure as error:
            manifest.append(
                {
                    **base_record,
                    "status": "parser_error",
                    "parser_name": None,
                    "parser_version": None,
                    "text_path": None,
                    "text_sha256": None,
                    "text_char_count": 0,
                    "chunk_count": 0,
                    "failure": {
                        "error_class": error.error_class,
                        "error_message": error.message,
                    },
                }
            )
            continue
        text = payload.text.strip()
        if not text:
            manifest.append(
                {
                    **base_record,
                    "status": "empty_text",
                    "parser_name": payload.parser_name,
                    "parser_version": payload.parser_version,
                    "text_path": None,
                    "text_sha256": None,
                    "text_char_count": 0,
                    "chunk_count": 0,
                    "failure": {
                        "error_class": "empty_text",
                        "error_message": "Parser produced no text.",
                    },
                }
            )
            continue
        text_path = extracted_text_dir / f"{source_record_id}_{artifact_sha256[:16]}.txt"
        text_path.write_text(text + "\n", encoding="utf-8")
        docling_json_path = None
        if payload.docling_json is not None:
            docling_json_path = docling_json_dir / f"{source_record_id}_{artifact_sha256[:16]}.json"
            _write_json(docling_json_path, payload.docling_json)
        row_chunks = _package_chunks_for_payload(
            row=row,
            payload=payload,
            extracted_at=extracted_at,
            source_text_path=text_path,
            max_chars=chunk_max_chars,
            overlap_chars=chunk_overlap_chars,
        )
        chunks.extend(row_chunks)
        manifest.append(
            {
                **base_record,
                "status": "extracted",
                "parser_name": payload.parser_name,
                "parser_version": payload.parser_version,
                "parser_metadata": payload.metadata,
                "text_path": str(text_path),
                "docling_json_path": str(docling_json_path) if docling_json_path else None,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text_char_count": len(text),
                "chunk_count": len(row_chunks),
            }
        )
    return manifest, chunks


def _package_row(
    *,
    package_file: Path,
    source_set_id: str,
    source_record_id: str,
    artifact_sha256: str,
    citation_label: str,
) -> dict:
    content_type = _content_type_for_path(package_file)
    expected_parser = _expected_parser_for_path(package_file)
    return {
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "title": package_file.name,
        "document_role": "ea_package",
        "authority_level": "project_record",
        "host": "local",
        "expected_parser": expected_parser,
        "source_status": "local_package",
        "artifact_sha256": artifact_sha256,
        "artifact_path": str(package_file),
        "artifact_byte_size": package_file.stat().st_size,
        "content_type": content_type,
        "citation_label": citation_label,
        "original_url": str(package_file),
        "effective_url": str(package_file),
        "final_url": str(package_file),
        "citation_final_url": str(package_file),
        "artifact_final_url": str(package_file),
        "metadata": {},
    }


def _package_chunks_for_payload(
    *,
    row: dict,
    payload,
    extracted_at: str,
    source_text_path: Path,
    max_chars: int,
    overlap_chars: int,
) -> list[dict]:
    chunks = []
    for index, chunk in enumerate(_chunk_text(payload.text, payload.blocks, max_chars, overlap_chars)):
        content_sha256 = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
        chunks.append(
            {
                "chunk_id": _chunk_id(
                    source_set_id=row["source_set_id"],
                    source_record_id=row["source_record_id"],
                    artifact_sha256=row["artifact_sha256"],
                    chunk_index=index,
                    char_start=chunk["char_start"],
                    content_sha256=content_sha256,
                ),
                "source_set_id": row["source_set_id"],
                "source_record_id": row["source_record_id"],
                "chunk_index": index,
                "title": row["title"],
                "document_role": row["document_role"],
                "authority_level": row["authority_level"],
                "artifact_sha256": row["artifact_sha256"],
                "artifact_path": row["artifact_path"],
                "citation_label": row["citation_label"],
                "parser_name": payload.parser_name,
                "parser_version": payload.parser_version,
                "extracted_at": extracted_at,
                "source_text_path": str(source_text_path),
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "page": chunk["page"],
                "section": chunk["section"],
                "heading": chunk["heading"],
                "content_sha256": content_sha256,
                "text": chunk["text"],
            }
        )
    return chunks


def _content_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".html", ".htm"}:
        return "text/html"
    if suffix == ".xml":
        return "application/xml"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "text/plain"


def _expected_parser_for_path(path: Path) -> str:
    row = {"expected_parser": "", "content_type": _content_type_for_path(path)}
    return _effective_parser(row, path)


def _search_package_chunks(
    chunks: list[dict],
    *,
    query: str,
    required_terms: list[str],
    limit: int,
) -> dict:
    terms = _query_terms(query, required_terms)
    evidence_terms = [term.strip().lower() for term in required_terms if term.strip()]
    scored = []
    for chunk in chunks:
        score, matched_terms = _score_package_chunk(
            chunk,
            terms,
            evidence_terms=evidence_terms,
        )
        if score <= 0:
            continue
        scored.append((score, chunk, matched_terms))
    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1]["source_record_id"]),
            int(item[1]["chunk_index"]),
        )
    )
    results = [
        _package_result(rank=rank, score=score, chunk=chunk, terms=matched_terms or terms)
        for rank, (score, chunk, matched_terms) in enumerate(scored[:limit], start=1)
    ]
    return {
        "query": query,
        "required_terms": required_terms,
        "hit_count": len(results),
        "results": results,
    }


def _query_terms(query: str, required_terms: list[str]) -> list[str]:
    terms = [term.strip().lower() for term in required_terms if term.strip()]
    terms.extend(_tokenize(query))
    return sorted(set(terms), key=lambda value: (len(value.split()), value), reverse=True)


def _score_package_chunk(
    chunk: dict,
    terms: list[str],
    *,
    evidence_terms: list[str] | None = None,
) -> tuple[float, list[str]]:
    text = " ".join([str(chunk.get("title") or ""), str(chunk.get("heading") or ""), chunk["text"]])
    lower = text.lower()
    token_set = set(_tokenize(text))
    if evidence_terms and not _matches_any_term(lower, token_set, evidence_terms):
        return 0.0, []
    matched = []
    for term in terms:
        if _matches_term(lower, token_set, term):
            matched.append(term)
    if not matched:
        return 0.0, []
    phrase_hits = sum(1 for term in matched if " " in term)
    score = len(matched) / max(1, len(terms))
    score += phrase_hits * 0.2
    return score, matched


def _matches_any_term(lower_text: str, token_set: set[str], terms: list[str]) -> bool:
    return any(_matches_term(lower_text, token_set, term) for term in terms)


def _matches_term(lower_text: str, token_set: set[str], term: str) -> bool:
    if " " in term:
        return term in lower_text
    return term in token_set


def _package_result(*, rank: int, score: float, chunk: dict, terms: list[str]) -> dict:
    span = _evidence_span(chunk["text"], terms, int(chunk["char_start"]))
    return {
        "rank": rank,
        "score": round(score, 6),
        "chunk_id": chunk["chunk_id"],
        "source_record_id": chunk["source_record_id"],
        "title": chunk["title"],
        "citation_label": chunk["citation_label"],
        "evidence_span": span,
        "provenance": {
            "artifact_sha256": chunk["artifact_sha256"],
            "artifact_path": chunk["artifact_path"],
            "parser_name": chunk["parser_name"],
            "parser_version": chunk["parser_version"],
            "extracted_at": chunk["extracted_at"],
            "source_text_path": chunk["source_text_path"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
            "page": chunk["page"],
            "section": chunk["section"],
            "heading": chunk["heading"],
            "content_sha256": chunk["content_sha256"],
        },
    }


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
    applicability_terms = [str(term) for term in item.get("applies_if_package_terms", [])]
    applicability = True
    if applicability_terms:
        applicability_search = bool(
            _search_package_chunks(
                package_chunks,
                query=" ".join(applicability_terms),
                required_terms=applicability_terms,
                limit=1,
            )["results"]
        )
        applicability = applicability_search
    if not applicability:
        status = "not_applicable"
        confidence = 0.6
        rationale = "The applicability trigger terms were not found in the EA package."
    elif package_evidence and source_evidence:
        status = "pass"
        confidence = 0.82
        rationale = "The EA package contains matching evidence and the source library provides supporting review authority."
    elif source_evidence and not package_evidence:
        status = "gap"
        confidence = 0.74
        rationale = "The source library supports this review requirement, but matching EA package evidence was not found."
    else:
        status = "uncertain"
        confidence = 0.35
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
        "created_at": _utc_now(),
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


def _evidence_span(text: str, terms: list[str], source_chunk_start: int) -> dict:
    lower = text.lower()
    starts = [lower.find(term.lower()) for term in terms if lower.find(term.lower()) >= 0]
    first = min(starts) if starts else 0
    start = max(0, first - 140)
    end = min(len(text), start + 480)
    start = max(0, min(start, max(0, end - 480)))
    span_text = text[start:end].strip()
    leading_trim = len(text[start:end]) - len(text[start:end].lstrip())
    trailing_trim = len(text[start:end].rstrip())
    chunk_start = start + leading_trim
    chunk_end = start + trailing_trim
    return {
        "text": span_text,
        "chunk_char_start": chunk_start,
        "chunk_char_end": chunk_end,
        "source_char_start": source_chunk_start + chunk_start,
        "source_char_end": source_chunk_start + chunk_end,
    }


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
    summary_path = index_path.parent / "summary.json"
    validation_path = index_path.parent / "retrieval_validation.json"
    summary = _read_json_if_exists(summary_path)
    validation = _read_json_if_exists(validation_path)
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


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        return "unknown-source-set"
    return json.loads(manifest_path.read_text(encoding="utf-8"))["source_set_id"]


def _source_set_id_from_index(index_path: Path) -> str | None:
    try:
        import sqlite3
        from contextlib import closing

        with closing(sqlite3.connect(index_path)) as connection:
            row = connection.execute(
                "SELECT value_json FROM metadata WHERE key = 'source_set_id'"
            ).fetchone()
    except sqlite3.Error:
        return None
    return json.loads(row[0]) if row else None


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


def _tokenize(value: str) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(value.lower()):
        token = token.strip("'-.")
        if len(token) < 2 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
