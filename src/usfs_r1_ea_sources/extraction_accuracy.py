from __future__ import annotations

from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from .extraction_admission import matched_verified_extraction_contracts
from .extract import _clean_text
from .extract import _find_xml_scope_element
from .extract import _normalize_xml_scope_identifier
from .extract import _raise_pypdf_decompression_limit
from .extract import _read_json
from .extract import _source_derived_dir
from .extract import _write_json
from .extract import _xml_local_name
from .extract import _xml_scope_for_row
from .records import sha256_file


@dataclass(frozen=True)
class ExtractionAccuracyAuditResult:
    summary: dict
    output_path: Path


def run_extraction_accuracy_audit(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    output_path: Path | None = None,
    contract_path: Path | None = None,
) -> ExtractionAccuracyAuditResult:
    """Run deterministic extraction-accuracy checks against generated extraction artifacts."""

    source_set_id = source_set_id or _read_json(
        output_dir / "catalog" / "source_set_manifest.json"
    )["source_set_id"]
    derived_dir = _source_derived_dir(output_dir / "derived", source_set_id)
    manifest_path = derived_dir / "diagnostics" / "extraction_manifest.jsonl"
    chunks_path = derived_dir / "chunks" / "chunks.jsonl"
    validation_path = derived_dir / "diagnostics" / "extraction_validation.json"
    output_path = output_path or derived_dir / "diagnostics" / "extraction_accuracy_audit.json"

    records = _read_jsonl(manifest_path)
    chunks = _read_jsonl(chunks_path)
    extraction_validation = _read_json(validation_path)
    admission_requirements = matched_verified_extraction_contracts(
        records=records,
        contract_path=contract_path,
    )
    audited_source_record_ids = admission_requirements["required_source_record_ids"] or [
        str(record.get("source_record_id") or "")
        for record in records
        if record.get("status") == "extracted"
    ]
    scoped_records = [
        record
        for record in records
        if str(record.get("source_record_id") or "") in set(audited_source_record_ids)
    ]
    scoped_chunks = [
        chunk
        for chunk in chunks
        if str(chunk.get("source_record_id") or "") in set(audited_source_record_ids)
    ]
    text_by_record = _load_extracted_text(scoped_records)

    checks = [
        _check_extraction_validation_passed(extraction_validation),
        _check_required_source_records_present_and_direct(
            scoped_records,
            required_source_record_ids=admission_requirements["required_source_record_ids"],
            require_direct_extraction=bool(admission_requirements["require_direct_extraction"]),
        ),
        _check_direct_document_required_records_use_document_artifacts(scoped_records),
        _check_text_files_match_manifest(scoped_records, text_by_record),
        _check_raw_artifact_hashes_match(scoped_records, output_dir),
        _check_chunks_match_text(scoped_records, scoped_chunks, text_by_record),
        _check_chunk_coverage(scoped_records, scoped_chunks, text_by_record),
        _check_scoped_xml_accuracy(scoped_records, text_by_record, output_dir),
        _check_markup_leakage(scoped_records, text_by_record),
        _check_pdf_text_crosscheck(scoped_records, text_by_record, output_dir),
    ]
    per_source_failures = _per_source_failure_map(
        checks,
        relevant_source_record_ids=audited_source_record_ids,
    )
    extracted_scoped_ids = {
        str(record.get("source_record_id") or "")
        for record in scoped_records
        if record.get("status") == "extracted"
    }
    admitted_source_record_ids = sorted(
        source_record_id
        for source_record_id in audited_source_record_ids
        if source_record_id in extracted_scoped_ids and source_record_id not in per_source_failures
    )
    blocked_source_record_ids = sorted(set(audited_source_record_ids) - set(admitted_source_record_ids))

    summary = {
        "source_set_id": source_set_id,
        "manifest_path": str(manifest_path),
        "chunks_path": str(chunks_path),
        "record_count": len(records),
        "extracted_record_count": sum(1 for record in records if record.get("status") == "extracted"),
        "chunk_count": len(chunks),
        "audited_record_count": len(scoped_records),
        "audited_chunk_count": len(scoped_chunks),
        "verified_extraction_admission_contract_path": admission_requirements["contract_path"],
        "verified_extraction_admission_contracts": admission_requirements["contracts"],
        "audited_source_record_ids": sorted(audited_source_record_ids),
        "required_direct_source_record_ids": sorted(audited_source_record_ids)
        if admission_requirements["require_direct_extraction"]
        else [],
        "knowledge_base_admitted_source_record_ids": admitted_source_record_ids,
        "knowledge_base_blocked_source_record_ids": blocked_source_record_ids,
        "per_source_failures": {
            source_record_id: reasons
            for source_record_id, reasons in sorted(per_source_failures.items())
        },
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, summary)
    return ExtractionAccuracyAuditResult(summary=summary, output_path=output_path)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _load_extracted_text(records: list[dict]) -> dict[str, str]:
    text_by_record = {}
    for record in records:
        if record.get("status") != "extracted" or not record.get("text_path"):
            continue
        path = Path(record["text_path"])
        text_by_record[record["source_record_id"]] = path.read_text(encoding="utf-8").rstrip("\n")
    return text_by_record


def _check_extraction_validation_passed(extraction_validation: dict) -> dict:
    return {
        "name": "extraction_validation_passed",
        "passed": bool(extraction_validation.get("passed")),
        "details": {
            "failed_checks": [
                check.get("name")
                for check in extraction_validation.get("checks", [])
                if not check.get("passed")
            ],
        },
    }


def _check_required_source_records_present_and_direct(
    records: list[dict],
    *,
    required_source_record_ids: list[str],
    require_direct_extraction: bool,
) -> dict:
    if not required_source_record_ids:
        return {
            "name": "required_source_records_are_present_and_direct",
            "passed": True,
            "details": {
                "required_source_record_ids": [],
                "require_direct_extraction": False,
                "failure_count": 0,
                "failures": [],
            },
        }
    records_by_source = {
        str(record.get("source_record_id") or ""): record
        for record in records
    }
    failures = []
    for source_record_id in required_source_record_ids:
        record = records_by_source.get(source_record_id)
        if record is None:
            failures.append(
                {
                    "source_record_id": source_record_id,
                    "reason": "missing_from_extraction_manifest",
                }
            )
            continue
        if record.get("status") != "extracted":
            failures.append(
                {
                    "source_record_id": source_record_id,
                    "reason": "not_extracted",
                    "status": record.get("status"),
                }
            )
            continue
        if require_direct_extraction and (record.get("parser_metadata") or {}).get("reused_existing"):
            failures.append(
                {
                    "source_record_id": source_record_id,
                    "reason": "reused_existing_extraction_not_admissible",
                }
            )
    return {
        "name": "required_source_records_are_present_and_direct",
        "passed": not failures,
        "details": {
            "required_source_record_ids": required_source_record_ids,
            "require_direct_extraction": require_direct_extraction,
            "failure_count": len(failures),
            "failures": failures[:50],
        },
    }


def _check_direct_document_required_records_use_document_artifacts(records: list[dict]) -> dict:
    failures = []
    for record in records:
        if not record.get("direct_document_artifact_required"):
            continue
        if record.get("status") != "extracted":
            continue
        if _record_uses_direct_document_artifact(record):
            continue
        failures.append(
            {
                "source_record_id": record.get("source_record_id"),
                "content_type": record.get("content_type"),
                "artifact_path": record.get("artifact_path"),
                "parser_name": record.get("parser_name"),
                "url_class": record.get("url_class"),
                "reason": "wrapper_page_not_admissible_for_direct_document_requirement",
            }
        )
    return {
        "name": "direct_document_required_records_use_document_artifacts",
        "passed": not failures,
        "details": {"failure_count": len(failures), "failures": failures[:50]},
    }


def _check_text_files_match_manifest(records: list[dict], text_by_record: dict[str, str]) -> dict:
    failures = []
    for record in records:
        if record.get("status") != "extracted":
            continue
        text = text_by_record.get(record["source_record_id"], "")
        actual_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if actual_hash != record.get("text_sha256") or len(text) != record.get("text_char_count"):
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "expected_text_sha256": record.get("text_sha256"),
                    "actual_text_sha256": actual_hash,
                    "expected_text_char_count": record.get("text_char_count"),
                    "actual_text_char_count": len(text),
                }
            )
    return {
        "name": "text_files_match_manifest_hashes",
        "passed": not failures,
        "details": {"failure_count": len(failures), "failures": failures[:50]},
    }


def _check_raw_artifact_hashes_match(records: list[dict], output_dir: Path) -> dict:
    failures = []
    for record in records:
        if record.get("status") != "extracted":
            continue
        artifact_path = _resolve_artifact_path(output_dir, record.get("artifact_path"))
        if not artifact_path or not artifact_path.exists():
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "artifact_path": record.get("artifact_path"),
                    "reason": "missing_artifact",
                }
            )
            continue
        actual_hash = sha256_file(artifact_path)
        if actual_hash != record.get("artifact_sha256"):
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "expected_artifact_sha256": record.get("artifact_sha256"),
                    "actual_artifact_sha256": actual_hash,
                }
            )
    return {
        "name": "raw_artifact_hashes_match_manifest",
        "passed": not failures,
        "details": {"failure_count": len(failures), "failures": failures[:50]},
    }


def _check_chunks_match_text(
    records: list[dict],
    chunks: list[dict],
    text_by_record: dict[str, str],
) -> dict:
    text_paths = {
        record["source_record_id"]: record.get("text_path")
        for record in records
        if record.get("status") == "extracted"
    }
    failures = []
    for chunk in chunks:
        source_id = chunk.get("source_record_id")
        text = text_by_record.get(source_id, "")
        start = chunk.get("char_start")
        end = chunk.get("char_end")
        chunk_text = chunk.get("text") or ""
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or end > len(text)
        ):
            failures.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source_record_id": source_id,
                    "reason": "invalid_offsets",
                    "char_start": start,
                    "char_end": end,
                    "text_char_count": len(text),
                }
            )
            continue
        actual_text = text[start:end]
        actual_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
        if (
            actual_text != chunk_text
            or actual_hash != chunk.get("content_sha256")
            or chunk.get("source_text_path") != text_paths.get(source_id)
        ):
            failures.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "source_record_id": source_id,
                    "reason": "chunk_text_or_provenance_mismatch",
                }
            )
    return {
        "name": "chunks_match_extracted_text_offsets",
        "passed": not failures,
        "details": {"failure_count": len(failures), "failures": failures[:50]},
    }


def _check_chunk_coverage(
    records: list[dict],
    chunks: list[dict],
    text_by_record: dict[str, str],
) -> dict:
    chunks_by_record: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        chunks_by_record[chunk["source_record_id"]].append(chunk)
    failures = []
    for record in records:
        if record.get("status") != "extracted":
            continue
        source_id = record["source_record_id"]
        text = text_by_record.get(source_id, "")
        source_chunks = sorted(chunks_by_record.get(source_id, []), key=lambda item: item["char_start"])
        if not source_chunks:
            failures.append({"source_record_id": source_id, "reason": "missing_chunks"})
            continue
        if source_chunks[0]["char_start"] != 0:
            failures.append(
                {
                    "source_record_id": source_id,
                    "reason": "first_chunk_does_not_start_at_zero",
                    "first_char_start": source_chunks[0]["char_start"],
                }
            )
        if source_chunks[-1]["char_end"] != len(text):
            failures.append(
                {
                    "source_record_id": source_id,
                    "reason": "last_chunk_does_not_end_at_text_end",
                    "last_char_end": source_chunks[-1]["char_end"],
                    "text_char_count": len(text),
                }
            )
        previous_end = source_chunks[0]["char_end"]
        for chunk in source_chunks[1:]:
            if chunk["char_start"] > previous_end:
                failures.append(
                    {
                        "source_record_id": source_id,
                        "reason": "chunk_gap",
                        "gap_start": previous_end,
                        "gap_end": chunk["char_start"],
                    }
                )
                break
            previous_end = max(previous_end, chunk["char_end"])
    return {
        "name": "chunk_coverage_has_no_gaps",
        "passed": not failures,
        "details": {"failure_count": len(failures), "failures": failures[:50]},
    }


def _check_scoped_xml_accuracy(
    records: list[dict],
    text_by_record: dict[str, str],
    output_dir: Path,
) -> dict:
    failures = []
    checked = 0
    for record in records:
        if record.get("status") != "extracted" or record.get("parser_name") != "legal_xml_builtin":
            continue
        scope = _xml_scope_for_row(record)
        if scope is None:
            continue
        checked += 1
        text = text_by_record.get(record["source_record_id"], "")
        metadata = record.get("parser_metadata") or {}
        actual_scope = metadata.get("source_scope") if isinstance(metadata, dict) else None
        if not _scope_matches(scope, actual_scope):
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "reason": "missing_or_wrong_scope_metadata",
                    "expected_scope": scope,
                    "actual_scope": actual_scope,
                }
            )
            continue
        artifact_path = _resolve_artifact_path(output_dir, record.get("artifact_path"))
        if not artifact_path:
            continue
        target_markers, sibling_markers = _xml_scope_markers(artifact_path, scope)
        missing_targets = [marker for marker in target_markers if marker not in text]
        leaked_siblings = [marker for marker in sibling_markers if marker in text]
        if missing_targets or leaked_siblings:
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "reason": "scoped_text_marker_mismatch",
                    "missing_target_markers": missing_targets,
                    "leaked_sibling_markers": leaked_siblings[:20],
                }
            )
    return {
        "name": "scoped_xml_text_matches_source_scope",
        "passed": not failures,
        "details": {
            "checked_record_count": checked,
            "failure_count": len(failures),
            "failures": failures[:50],
        },
    }


def _scope_matches(expected: dict, actual: dict | None) -> bool:
    if not isinstance(actual, dict):
        return False
    return (
        _normalize_xml_scope_identifier(expected["type"])
        == _normalize_xml_scope_identifier(actual.get("type"))
        and _normalize_xml_scope_identifier(expected["identifier"])
        == _normalize_xml_scope_identifier(actual.get("identifier"))
    )


def _xml_scope_markers(artifact_path: Path, scope: dict) -> tuple[list[str], list[str]]:
    try:
        root = ET.parse(artifact_path).getroot()
    except ET.ParseError:
        return [], []
    target = _find_xml_scope_element(root, scope)
    if target is None:
        return [], []
    target_markers = _markers_for_scope_element(target)
    parent_map = {child: parent for parent in root.iter() for child in list(parent)}
    parent = parent_map.get(target)
    sibling_markers = []
    if parent is not None:
        expected_type = _normalize_xml_scope_identifier(scope["type"])
        for sibling in list(parent):
            if sibling is target:
                continue
            if _normalize_xml_scope_identifier(sibling.attrib.get("TYPE")) != expected_type:
                continue
            heading = _first_child_text(sibling, "HEAD")
            if heading:
                sibling_markers.append(heading)
    return target_markers, sibling_markers


def _markers_for_scope_element(element: ET.Element) -> list[str]:
    scope_type = _normalize_xml_scope_identifier(element.attrib.get("TYPE"))
    identifier = str(element.attrib.get("N") or "").strip()
    heading = _first_child_text(element, "HEAD")
    markers = []
    if heading:
        markers.append(heading)
    if scope_type == "section" and identifier:
        markers.append(f"§ {identifier}")
    if scope_type == "subpart" and identifier:
        markers.append(f"Subpart {identifier}")
    return [marker for marker in dict.fromkeys(markers) if marker]


def _first_child_text(element: ET.Element, tag_name: str) -> str | None:
    expected = tag_name.upper()
    for child in list(element):
        if _xml_local_name(child.tag) == expected:
            return _clean_text(" ".join(child.itertext()))
    return None


def _check_markup_leakage(records: list[dict], text_by_record: dict[str, str]) -> dict:
    failures = []
    tag_pattern = re.compile(r"</?[A-Za-z][A-Za-z0-9:_-]*(?:\\s[^<>]{0,160})?>")
    entity_pattern = re.compile(r"&(?:amp|lt|gt|quot|apos|nbsp);")
    for record in records:
        if record.get("status") != "extracted":
            continue
        text = text_by_record.get(record["source_record_id"], "")
        tag_hits = tag_pattern.findall(text[:200_000])
        entity_hits = entity_pattern.findall(text[:200_000])
        if tag_hits or entity_hits:
            failures.append(
                {
                    "source_record_id": record["source_record_id"],
                    "tag_examples": tag_hits[:5],
                    "entity_examples": entity_hits[:5],
                }
            )
    return {
        "name": "extracted_text_has_no_markup_leakage",
        "passed": not failures,
        "details": {"failure_count": len(failures), "failures": failures[:50]},
    }


def _check_pdf_text_crosscheck(
    records: list[dict],
    text_by_record: dict[str, str],
    output_dir: Path,
) -> dict:
    with suppress(ImportError):
        from pypdf import PdfReader

        _raise_pypdf_decompression_limit()
        failures = []
        metrics = []
        skipped = []
        for record in records:
            if record.get("status") != "extracted":
                continue
            if (record.get("content_type") or "").lower() != "application/pdf" and not str(
                record.get("artifact_path") or ""
            ).lower().endswith(".pdf"):
                continue
            artifact_path = _resolve_artifact_path(output_dir, record.get("artifact_path"))
            if not artifact_path or not artifact_path.exists():
                skipped.append({"source_record_id": record["source_record_id"], "reason": "missing_pdf"})
                continue
            try:
                reference = _extract_pypdf_reference_text(PdfReader(str(artifact_path)))
            except Exception as error:  # noqa: BLE001
                failures.append(
                    {
                        "source_record_id": record["source_record_id"],
                        "parser_name": record.get("parser_name"),
                        "reason": "pypdf_crosscheck_failed",
                        "error_class": type(error).__name__,
                        "error_message": str(error),
                    }
                )
                continue
            reference_tokens = _tokens(reference)
            extracted_tokens = _tokens(text_by_record.get(record["source_record_id"], ""))
            if not reference_tokens:
                skipped.append({"source_record_id": record["source_record_id"], "reason": "no_pdf_text"})
                continue
            overlap = reference_tokens & extracted_tokens
            recall = len(overlap) / len(reference_tokens)
            precision = len(overlap) / len(extracted_tokens) if extracted_tokens else 0.0
            threshold = 0.95 if record.get("parser_name") == "pypdf_text_fallback" else 0.55
            metric = {
                "source_record_id": record["source_record_id"],
                "parser_name": record.get("parser_name"),
                "reference_token_count": len(reference_tokens),
                "extracted_token_count": len(extracted_tokens),
                "token_recall": round(recall, 4),
                "token_precision": round(precision, 4),
                "threshold": threshold,
            }
            metrics.append(metric)
            if recall < threshold:
                failures.append(metric)
        return {
            "name": "pdf_text_crosscheck_against_pypdf",
            "passed": not failures,
            "details": {
                "checked_record_count": len(metrics),
                "skipped_record_count": len(skipped),
                "failure_count": len(failures),
                "failures": failures[:50],
                "metrics": metrics,
                "skipped": skipped[:50],
            },
        }
    return {
        "name": "pdf_text_crosscheck_against_pypdf",
        "passed": True,
        "details": {"checked_record_count": 0, "skipped_reason": "pypdf_unavailable"},
    }


def _extract_pypdf_reference_text(reader) -> str:  # noqa: ANN001
    parts = []
    for page in reader.pages:
        text = _clean_text(page.extract_text() or "")
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", text)
        if not token.isdigit()
    }


def _resolve_artifact_path(output_dir: Path, value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute() or path.exists():
        return path
    output_relative = output_dir / path
    if output_relative.exists():
        return output_relative
    return path


def _record_uses_direct_document_artifact(record: dict) -> bool:
    content_type = str(record.get("content_type") or "").lower()
    artifact_path = str(record.get("artifact_path") or "").lower()
    parser_name = str(record.get("parser_name") or "").lower()
    if content_type in {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        return True
    if artifact_path.endswith((".pdf", ".doc", ".docx")):
        return True
    return parser_name in {"docling", "python_docx_zip_xml", "pypdf_text_fallback"}


def _per_source_failure_map(
    checks: list[dict],
    *,
    relevant_source_record_ids: list[str],
) -> dict[str, list[str]]:
    failures_by_source: dict[str, list[str]] = {}
    relevant_source_record_id_set = set(relevant_source_record_ids)
    for check in checks:
        if check.get("passed"):
            continue
        failed_source_ids = _source_record_ids_from_check(check, relevant_source_record_id_set)
        if not failed_source_ids and relevant_source_record_id_set:
            failed_source_ids = sorted(relevant_source_record_id_set)
        for source_record_id in failed_source_ids:
            failures_by_source.setdefault(source_record_id, []).append(str(check.get("name") or ""))
    return failures_by_source


def _source_record_ids_from_check(
    check: dict,
    relevant_source_record_ids: set[str],
) -> list[str]:
    details = check.get("details") or {}
    if not isinstance(details, dict):
        return []
    discovered = set()
    for key in (
        "source_record_ids",
        "missing_source_record_ids",
        "failed_source_record_ids",
        "required_source_record_ids",
    ):
        values = details.get(key)
        if isinstance(values, list):
            discovered.update(str(value) for value in values if str(value) in relevant_source_record_ids)
    for key in ("failures", "metrics"):
        values = details.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, dict):
                continue
            source_record_id = str(value.get("source_record_id") or "")
            if source_record_id in relevant_source_record_ids:
                discovered.add(source_record_id)
    return sorted(discovered)
