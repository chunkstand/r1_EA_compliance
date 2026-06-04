from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import re

from .applicability_eval_support import _source_chunk_specs
from .applicability_eval_support import _strings
from .applicability_eval_support import _utc_now
from .applicability_eval_support import _write_jsonl
from .retrieval import _write_sqlite_index


def _write_package_cache(
    *,
    review_dir: Path,
    review_id: str,
    source_set_id: str,
    case: dict[str, Any],
    eval_file: Path,
) -> None:
    package_dir = review_dir / "package"
    package_path = _case_package_path(case, eval_file)
    text = _case_package_text(case, eval_file)
    artifact_sha256 = hashlib.sha256(f"{review_id}:{text}".encode("utf-8")).hexdigest()
    chunks = []
    for index, chunk_text in enumerate(_split_case_text(text), start=1):
        content_sha256 = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
        chunks.append(
            {
                "chunk_id": f"{review_id}-package-chunk-{index}",
                "source_set_id": f"ea-package-{review_id}",
                "source_record_id": "EA-PACKAGE-001",
                "chunk_index": index - 1,
                "title": str(case.get("package_title") or f"{case.get('id')} package"),
                "document_role": "ea_package",
                "authority_level": "project_record",
                "artifact_sha256": artifact_sha256,
                "artifact_path": str(package_path) if package_path else str(eval_file),
                "citation_label": f"EA-PACKAGE-{index:03d}",
                "parser_name": "applicability-eval-fixture",
                "parser_version": "0.1.0",
                "extracted_at": _utc_now(),
                "source_text_path": str(package_path) if package_path else str(eval_file),
                "char_start": 0,
                "char_end": len(chunk_text),
                "page": index,
                "section": _section_for_chunk(index),
                "heading": _section_for_chunk(index),
                "content_sha256": content_sha256,
                "text": chunk_text,
            }
        )
    manifest = [
        {
            "source_set_id": f"ea-package-{review_id}",
            "source_record_id": "EA-PACKAGE-001",
            "title": str(case.get("package_title") or f"{case.get('id')} package"),
            "artifact_path": str(package_path) if package_path else str(eval_file),
            "artifact_sha256": artifact_sha256,
            "artifact_byte_size": len(text.encode("utf-8")),
            "content_type": "text/plain",
            "citation_label": "EA-PACKAGE-001",
            "extracted_at": _utc_now(),
            "status": "extracted",
            "parser_name": "applicability-eval-fixture",
            "parser_version": "0.1.0",
            "text_path": str(package_path) if package_path else str(eval_file),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text_char_count": len(text),
            "chunk_count": len(chunks),
        }
    ]
    _write_jsonl(package_dir / "package_manifest.jsonl", manifest)
    _write_jsonl(package_dir / "package_chunks.jsonl", chunks)


def _write_source_index(
    *,
    output_dir: Path,
    eval_output_dir: Path,
    case_id: str,
    source_set_id: str,
    chunks: list[dict[str, Any]],
) -> Path:
    source_dir = eval_output_dir / "source_indexes" / case_id
    chunks_path = source_dir / "chunks.jsonl"
    sqlite_path = source_dir / "evidence_index.sqlite"
    _write_jsonl(chunks_path, chunks)
    _write_sqlite_index(
        sqlite_path,
        source_set_id=source_set_id,
        chunks=chunks,
        chunks_path=chunks_path,
        catalog_sqlite_path=output_dir / "catalog" / "review_sources.sqlite",
    )
    return sqlite_path


def _case_source_chunks(
    *,
    case: dict[str, Any],
    inherited_source_chunks: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    authority_family_templates: list[dict[str, Any]],
    source_set_id: str,
) -> list[dict[str, Any]]:
    explicit = _source_chunk_specs(case.get("source_chunks"))
    specs = explicit or inherited_source_chunks
    by_source = {str(spec.get("source_record_id")): spec for spec in specs}
    chunks = []
    emitted_source_record_ids: set[str] = set()
    for rule in rules:
        source_record_id = str(
            rule.get("authority_source_record_id")
            or (rule.get("source_filters") or {}).get("source_record_id")
            or ""
        )
        if not source_record_id or source_record_id in emitted_source_record_ids:
            continue
        emitted_source_record_ids.add(source_record_id)
        spec = by_source.get(source_record_id, {})
        text = str(
            spec.get("text")
            or rule.get("source_query")
            or rule.get("requirement")
            or rule.get("title")
            or source_record_id
        )
        role = str(
            spec.get("document_role")
            or rule.get("authority_document_role")
            or (rule.get("source_filters") or {}).get("document_role")
            or rule.get("authority_category")
            or "source"
        )
        chunks.append(
            _source_chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                document_role=role,
                title=str(spec.get("title") or rule.get("title") or source_record_id),
                text=text,
            )
        )
    for template in authority_family_templates:
        source_record_id = str(
            template.get("authority_source_record_id")
            or (_strings(template.get("source_record_ids"))[:1] or [""])[0]
        )
        if not source_record_id or source_record_id in emitted_source_record_ids:
            continue
        emitted_source_record_ids.add(source_record_id)
        spec = by_source.get(source_record_id, {})
        source_filters = (
            template.get("source_filters")
            if isinstance(template.get("source_filters"), dict)
            else {}
        )
        role = str(
            spec.get("document_role")
            or template.get("authority_document_role")
            or source_filters.get("document_role")
            or template.get("authority_category")
            or "source"
        )
        text = str(
            spec.get("text")
            or template.get("source_query")
            or template.get("requirement")
            or template.get("title")
            or source_record_id
        )
        chunks.append(
            _source_chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                document_role=role,
                title=str(spec.get("title") or template.get("title") or source_record_id),
                text=text,
            )
        )
    for candidate in _explicit_candidate_authorities(case):
        for source_record_id in _candidate_source_record_ids(candidate):
            if source_record_id in emitted_source_record_ids:
                continue
            emitted_source_record_ids.add(source_record_id)
            spec = by_source.get(source_record_id, {})
            source_record = _candidate_source_record(candidate, source_record_id)
            role = str(
                spec.get("document_role")
                or source_record.get("document_role")
                or candidate.get("authority_document_role")
                or candidate.get("authority_category")
                or "source"
            )
            title = str(
                spec.get("title")
                or source_record.get("title")
                or candidate.get("title")
                or source_record_id
            )
            text = str(
                spec.get("text")
                or source_record.get("text")
                or _candidate_source_query(candidate)
                or candidate.get("requirement")
                or title
            )
            chunks.append(
                _source_chunk(
                    source_set_id=source_set_id,
                    source_record_id=source_record_id,
                    document_role=role,
                    title=title,
                    text=text,
                )
            )
    return chunks


def _explicit_candidate_authorities(case: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in case.get("candidate_authorities") or []
        if isinstance(item, dict)
    ]
    candidates.extend(
        item
        for item in case.get("extra_candidate_authorities") or []
        if isinstance(item, dict)
    )
    return candidates


def _candidate_source_query(candidate: dict[str, Any]) -> str:
    value = candidate.get("source_query")
    if value:
        return str(value)
    contract = candidate.get("retrieval_contract")
    if not isinstance(contract, dict):
        return ""
    return (_strings(contract.get("source_queries")) or [""])[0]


def _candidate_source_record(
    candidate: dict[str, Any],
    source_record_id: str,
) -> dict[str, Any]:
    for record in candidate.get("source_records") or []:
        if (
            isinstance(record, dict)
            and str(record.get("source_record_id") or "") == source_record_id
        ):
            return record
    return {}


def _candidate_source_record_ids(candidate: dict[str, Any]) -> list[str]:
    values = [*_strings(candidate.get("source_record_ids"))]
    values.extend(
        str(record.get("source_record_id") or "")
        for record in candidate.get("source_records") or []
        if isinstance(record, dict)
    )
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _source_chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    document_role: str,
    title: str,
    text: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"{source_record_id}-applicability-eval-chunk-0",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "support_document_role": document_role,
        "authority_level": document_role,
        "host": "applicability-eval.local",
        "expected_parser": "text",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"/applicability-eval/{source_record_id}.txt",
        "citation_label": f"{source_record_id} | {title}",
        "original_url": f"https://applicability-eval.local/{source_record_id}",
        "effective_url": f"https://applicability-eval.local/{source_record_id}",
        "final_url": f"https://applicability-eval.local/{source_record_id}",
        "parser_name": "applicability-eval-fixture",
        "parser_version": "0.1.0",
        "extracted_at": _utc_now(),
        "source_text_path": f"/applicability-eval/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": 1,
        "section": "Authority Text",
        "heading": "Authority Text",
        "content_sha256": digest,
        "review_topics": [document_role],
        "text": text,
    }


def _case_package_text(case: dict[str, Any], eval_file: Path) -> str:
    if case.get("package_text"):
        return str(case["package_text"])
    path = _case_package_path(case, eval_file)
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Applicability eval case {case.get('id')} has no package_text/path"
    )


def _case_package_path(case: dict[str, Any], eval_file: Path) -> Path | None:
    package_path = str(case.get("package_path") or "").strip()
    if not package_path:
        return None
    path = Path(package_path)
    if not path.is_absolute():
        path = (eval_file.parent / path).resolve()
    return path


def _split_case_text(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    return chunks or [text]


def _section_for_chunk(index: int) -> str:
    sections = {
        1: "Purpose and Need",
        2: "Affected Environment",
        3: "Environmental Consequences",
    }
    return sections.get(index, "Appendix")
