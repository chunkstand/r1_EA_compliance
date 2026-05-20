from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import hashlib
import json
import re
import shutil
import sqlite3
from typing import Any

from .artifact_utils import _read_json_if_exists as read_json_if_exists
from .artifact_utils import _read_jsonl as read_jsonl
from .artifact_utils import _source_set_id_from_catalog as _source_set_id_from_catalog
from .artifact_utils import _utc_now as utc_now
from .artifact_utils import _write_json as write_json
from .extract import _chunk_id
from .extract import _chunk_text
from .extract import _effective_parser
from .extract import _extract_payload
from .extract import ExtractionFailure
from .records import sha256_file


SUPPORTED_PACKAGE_SUFFIXES = {".pdf", ".html", ".htm", ".xml", ".docx", ".txt", ".md"}
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}")
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


def source_set_id_from_catalog(output_dir: Path) -> str | None:
    return _source_set_id_from_catalog(output_dir)


def prepare_review_outputs(
    *,
    package_dir: Path,
    output_paths: Sequence[Path | None],
    preserve_package_cache: bool = False,
) -> None:
    if package_dir.exists() and not preserve_package_cache:
        shutil.rmtree(package_dir)
    for path in output_paths:
        if path is not None:
            path.unlink(missing_ok=True)


def load_package_cache(
    *,
    package_manifest_path: Path,
    package_chunks_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    missing = [
        str(path)
        for path in (package_manifest_path, package_chunks_path)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Cannot reuse EA package cache because required cache files are missing: "
            + ", ".join(missing)
        )
    package_manifest = read_jsonl(package_manifest_path)
    package_chunks = read_jsonl(package_chunks_path)
    if not package_manifest or not package_chunks:
        raise ValueError(
            "Cannot reuse EA package cache because package manifest or chunks are empty."
        )
    return package_manifest, package_chunks


def discover_package_files(package_path: Path) -> list[Path]:
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


def extract_package_files(
    *,
    package_files: list[Path],
    review_id: str,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
    extracted_at: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    extracted_at = extracted_at or utc_now()
    manifest: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    package_source_set_id = f"ea-package-{_safe_slug(review_id)}"
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
            write_json(docling_json_path, payload.docling_json)
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


def search_package_chunks(
    chunks: list[dict[str, Any]],
    *,
    query: str,
    required_terms: list[str],
    limit: int,
    required_term_groups: list[list[str]] | None = None,
    preferred_terms: list[str] | None = None,
    preferred_term_groups: list[list[str]] | None = None,
) -> dict[str, Any]:
    terms = _query_terms(query, required_terms)
    evidence_terms = [term.strip().lower() for term in required_terms if term.strip()]
    evidence_term_groups = [
        [term.strip().lower() for term in group if term.strip()]
        for group in (required_term_groups or [])
    ]
    section_terms = [term.strip().lower() for term in (preferred_terms or []) if term.strip()]
    section_term_groups = [
        [term.strip().lower() for term in group if term.strip()]
        for group in (preferred_term_groups or [])
    ]
    scored = []
    for chunk in chunks:
        score, matched_terms, preferred_matches = _score_package_chunk(
            chunk,
            terms,
            evidence_terms=evidence_terms,
            evidence_term_groups=evidence_term_groups,
            preferred_terms=section_terms,
            preferred_term_groups=section_term_groups,
        )
        if score <= 0:
            continue
        scored.append((score, chunk, matched_terms, preferred_matches))
    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1]["source_record_id"]),
            int(item[1]["chunk_index"]),
        )
    )
    results = [
        _package_result(
            rank=rank,
            score=score,
            chunk=chunk,
            terms=_span_terms(
                matched_terms=matched_terms,
                preferred_matches=preferred_matches,
                fallback_terms=terms,
            ),
        )
        for rank, (score, chunk, matched_terms, preferred_matches) in enumerate(
            scored[:limit],
            start=1,
        )
    ]
    return {
        "query": query,
        "required_terms": required_terms,
        "required_term_groups": required_term_groups or [],
        "preferred_terms": preferred_terms or [],
        "preferred_term_groups": preferred_term_groups or [],
        "hit_count": len(results),
        "results": results,
    }


def retrieval_artifacts(
    index_path: Path,
) -> tuple[Path, Path, dict[str, Any] | None, dict[str, Any] | None]:
    summary_path = index_path.parent / "summary.json"
    validation_path = index_path.parent / "retrieval_validation.json"
    return (
        summary_path,
        validation_path,
        read_json_if_exists(summary_path),
        read_json_if_exists(validation_path),
    )


def source_set_id_from_index(index_path: Path) -> str | None:
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


def indexed_source_record_counts(
    index_path: Path,
    required_source_record_ids: tuple[str, ...],
) -> dict[str, int]:
    if not required_source_record_ids or not index_path.exists():
        return {}
    placeholders = ",".join("?" for _ in required_source_record_ids)
    try:
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                f"""
                SELECT source_record_id, COUNT(*)
                FROM chunks
                WHERE source_record_id IN ({placeholders})
                GROUP BY source_record_id
                """,
                list(required_source_record_ids),
            ).fetchall()
    except sqlite3.Error:
        return {}
    return {str(source_record_id): int(count) for source_record_id, count in rows}


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _package_row(
    *,
    package_file: Path,
    source_set_id: str,
    source_record_id: str,
    artifact_sha256: str,
    citation_label: str,
) -> dict[str, Any]:
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
    row: dict[str, Any],
    payload: Any,
    extracted_at: str,
    source_text_path: Path,
    max_chars: int,
    overlap_chars: int,
) -> list[dict[str, Any]]:
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


def _query_terms(query: str, required_terms: list[str]) -> list[str]:
    terms = [term.strip().lower() for term in required_terms if term.strip()]
    terms.extend(_tokenize(query))
    return sorted(set(terms), key=lambda value: (len(value.split()), value), reverse=True)


def _score_package_chunk(
    chunk: dict[str, Any],
    terms: list[str],
    *,
    evidence_terms: list[str] | None = None,
    evidence_term_groups: list[list[str]] | None = None,
    preferred_terms: list[str] | None = None,
    preferred_term_groups: list[list[str]] | None = None,
) -> tuple[float, list[str], list[str]]:
    text = " ".join([str(chunk.get("title") or ""), str(chunk.get("heading") or ""), chunk["text"]])
    lower = text.lower()
    token_set = set(_tokenize(text))
    group_matches: list[str] = []
    if evidence_term_groups:
        for group in evidence_term_groups:
            matched_group_terms = _matched_terms(lower, token_set, group)
            if not matched_group_terms:
                return 0.0, [], []
            group_matches.extend(matched_group_terms)
    elif evidence_terms and not _matches_any_term(lower, token_set, evidence_terms):
        return 0.0, [], []
    matched = []
    for term in terms:
        if _matches_term(lower, token_set, term):
            matched.append(term)
    if not matched:
        return 0.0, [], []
    matched = sorted(set(matched) | set(group_matches))
    phrase_hits = sum(1 for term in matched if " " in term)
    score = len(matched) / max(1, len(terms))
    score += phrase_hits * 0.2
    if evidence_term_groups:
        score += len(evidence_term_groups) * 0.3
    preferred_matches = _preferred_package_matches(
        lower_text=lower,
        token_set=token_set,
        preferred_terms=preferred_terms or [],
        preferred_term_groups=preferred_term_groups or [],
    )
    if preferred_matches["matched_terms"] or preferred_matches["matched_groups"]:
        score += len(preferred_matches["matched_groups"]) * 0.55
        score += len(preferred_matches["matched_terms"]) * 0.05
    return score, matched, preferred_matches.get("matched_terms", [])


def _preferred_package_matches(
    *,
    lower_text: str,
    token_set: set[str],
    preferred_terms: list[str],
    preferred_term_groups: list[list[str]],
) -> dict[str, list[Any]]:
    matched_terms = _matched_terms(lower_text, token_set, preferred_terms)
    matched_groups: list[list[str]] = []
    for group in preferred_term_groups:
        group_matches = _matched_terms(lower_text, token_set, group)
        if group_matches:
            matched_groups.append(group_matches)
            matched_terms.extend(group_matches)
    return {
        "matched_terms": sorted(set(matched_terms), key=lambda term: (len(term.split()), term)),
        "matched_groups": matched_groups,
    }


def _span_terms(
    *,
    matched_terms: list[str],
    preferred_matches: list[str],
    fallback_terms: list[str],
) -> list[str]:
    if preferred_matches:
        return sorted(
            set(preferred_matches) | {term for term in matched_terms if " " in term},
            key=lambda term: (len(term.split()), term),
            reverse=True,
        )
    return matched_terms or fallback_terms


def _matched_terms(lower_text: str, token_set: set[str], terms: list[str]) -> list[str]:
    return [term for term in terms if _matches_term(lower_text, token_set, term)]


def _matches_any_term(lower_text: str, token_set: set[str], terms: list[str]) -> bool:
    return any(_matches_term(lower_text, token_set, term) for term in terms)


def _matches_term(lower_text: str, token_set: set[str], term: str) -> bool:
    if " " in term:
        return term in lower_text
    return term in token_set


def _package_result(
    *,
    rank: int,
    score: float,
    chunk: dict[str, Any],
    terms: list[str],
) -> dict[str, Any]:
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


def _evidence_span(text: str, terms: list[str], source_chunk_start: int) -> dict[str, Any]:
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


def _tokenize(value: str) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(value.lower()):
        token = token.strip("'-.")
        if len(token) < 2 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _safe_slug(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return safe or "package"
