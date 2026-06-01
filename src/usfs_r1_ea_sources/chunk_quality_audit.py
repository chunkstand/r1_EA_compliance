from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from typing import Any

from .chunk_layers import CHUNK_LAYER_SCHEMA_VERSION
from .chunk_layers import detect_structure_type
from .source_set_support import source_derived_dir


CHUNK_QUALITY_AUDIT_SCHEMA_VERSION = "chunk-quality-audit-v1"
LOW_DENSITY_CHARS_PER_PAGE = 800
HEADING_MISSING_RATE_THRESHOLD = 0.75
FALLBACK_PARSERS = {"pypdf_text_fallback"}


@dataclass(frozen=True)
class ChunkQualityAuditResult:
    source_set_id: str
    output_path: Path
    summary: dict[str, Any]


def run_chunk_quality_audit(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    chunks_path: Path | None = None,
    output_path: Path | None = None,
) -> ChunkQualityAuditResult:
    """Build a read-only chunk/parser/layout risk report for a source set."""

    output_dir = Path(output_dir)
    source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    derived_dir = source_derived_dir(output_dir / "derived", source_set_id)
    chunks_path = chunks_path or derived_dir / "chunks" / "chunks.jsonl"
    output_path = output_path or derived_dir / "diagnostics" / "chunk_quality_audit.json"
    chunks = _read_jsonl(chunks_path)
    source_records = _source_records(chunks, output_dir=output_dir)
    sidecar_summary = _sidecar_summary(derived_dir)
    source_results = [
        _source_quality_record(source_record_id, records, sidecar_summary=sidecar_summary)
        for source_record_id, records in sorted(source_records.items())
    ]
    checks = _checks(chunks_path, chunks, source_results)
    risk_bucket_counts = Counter(
        bucket for source in source_results for bucket in source["risk_buckets"]
    )
    parser_counts = Counter(str(chunk.get("parser_name") or "") for chunk in chunks)
    summary = {
        "schema_version": CHUNK_QUALITY_AUDIT_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "chunks_path": str(chunks_path),
        "output_path": str(output_path),
        "chunk_count": len(chunks),
        "source_count": len(source_results),
        "parser_counts": dict(parser_counts),
        "risk_source_count": sum(1 for source in source_results if source["risk_buckets"]),
        "risk_bucket_counts": dict(sorted(risk_bucket_counts.items())),
        "sidecar": sidecar_summary,
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
        "sources": source_results,
    }
    _write_json(output_path, summary)
    return ChunkQualityAuditResult(
        source_set_id=source_set_id,
        output_path=output_path,
        summary=summary,
    )


def _source_quality_record(
    source_record_id: str,
    chunks: list[dict[str, Any]],
    *,
    sidecar_summary: dict[str, Any],
) -> dict[str, Any]:
    chunk_count = len(chunks)
    pages = _pages(chunks)
    page_count = len(pages) if pages else None
    text_char_count = _text_char_count(chunks)
    chars_per_page = round(text_char_count / page_count, 3) if page_count else None
    parser_counts = Counter(str(chunk.get("parser_name") or "") for chunk in chunks)
    heading_missing_count = sum(1 for chunk in chunks if not chunk.get("heading"))
    structural_marker_count = sum(
        _has_structural_marker(str(chunk.get("text") or "")) for chunk in chunks
    )
    table_marker_count = sum(_has_table_marker(str(chunk.get("text") or "")) for chunk in chunks)
    boundary_split_count = sum(
        _boundary_split_risk(str(chunk.get("text") or "")) for chunk in chunks
    )
    risk_buckets = _risk_buckets(
        chunks=chunks,
        page_count=page_count,
        chars_per_page=chars_per_page,
        parser_counts=parser_counts,
        heading_missing_count=heading_missing_count,
        structural_marker_count=structural_marker_count,
        table_marker_count=table_marker_count,
        boundary_split_count=boundary_split_count,
        sidecar_summary=sidecar_summary,
    )
    first = chunks[0]
    return {
        "source_record_id": source_record_id,
        "title": first.get("title"),
        "citation_label": first.get("citation_label"),
        "document_role": first.get("document_role"),
        "support_document_role": first.get("support_document_role"),
        "authority_level": first.get("authority_level"),
        "artifact_sha256": first.get("artifact_sha256"),
        "artifact_path": first.get("artifact_path"),
        "chunk_count": chunk_count,
        "page_count": page_count,
        "text_char_count": text_char_count,
        "chars_per_page": chars_per_page,
        "chunks_per_page": round(chunk_count / page_count, 3) if page_count else None,
        "parser_counts": dict(parser_counts),
        "dominant_parser": parser_counts.most_common(1)[0][0] if parser_counts else None,
        "heading_missing_count": heading_missing_count,
        "heading_missing_rate": round(heading_missing_count / chunk_count, 6) if chunk_count else 0.0,
        "structural_marker_chunk_count": structural_marker_count,
        "table_marker_chunk_count": table_marker_count,
        "boundary_split_risk_count": boundary_split_count,
        "risk_buckets": risk_buckets,
    }


def _risk_buckets(
    *,
    chunks: list[dict[str, Any]],
    page_count: int | None,
    chars_per_page: float | None,
    parser_counts: Counter[str],
    heading_missing_count: int,
    structural_marker_count: int,
    table_marker_count: int,
    boundary_split_count: int,
    sidecar_summary: dict[str, Any],
) -> list[str]:
    buckets: list[str] = []
    dominant_parser = parser_counts.most_common(1)[0][0] if parser_counts else ""
    artifact_path = str(chunks[0].get("artifact_path") or "").lower() if chunks else ""
    is_pdf_like = artifact_path.endswith(".pdf") or dominant_parser in {
        "pypdf_text_fallback",
        "apple_vision_pdf_raster",
        "rapidocr_pdf_raster",
        "docling",
    }
    if dominant_parser in FALLBACK_PARSERS:
        buckets.append("fallback_parser_dominated")
    if any("ocr" in parser or "vision" in parser for parser in parser_counts):
        buckets.append("ocr_or_scanned_source")
    if (
        is_pdf_like
        and page_count
        and chars_per_page is not None
        and chars_per_page < LOW_DENSITY_CHARS_PER_PAGE
    ):
        buckets.append("low_density_pdf")
    if chunks and heading_missing_count / len(chunks) >= HEADING_MISSING_RATE_THRESHOLD:
        buckets.append("heading_context_missing")
    if table_marker_count:
        buckets.append("table_row_unstructured")
    if structural_marker_count:
        buckets.append("structural_marker_present")
    if boundary_split_count:
        buckets.append("numbered_requirement_or_sentence_split")
    if sidecar_summary.get("validation_passed") is not True:
        buckets.append("parent_context_missing")
    return sorted(set(buckets))


def _source_records(
    chunks: list[dict[str, Any]],
    *,
    output_dir: Path,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        normalized = dict(chunk)
        normalized["_source_text_size"] = _source_text_size(chunk, output_dir=output_dir)
        grouped[str(chunk.get("source_record_id") or "")].append(normalized)
    return grouped


def _source_text_size(chunk: dict[str, Any], *, output_dir: Path) -> int | None:
    value = chunk.get("source_text_path")
    if not value:
        return None
    path = Path(str(value))
    candidates = [path] if path.is_absolute() else [path, output_dir / path, output_dir.parent / path]
    for candidate in candidates:
        if candidate.exists():
            return len(candidate.read_text(encoding="utf-8", errors="replace"))
    return None


def _text_char_count(chunks: list[dict[str, Any]]) -> int:
    source_sizes = [chunk.get("_source_text_size") for chunk in chunks if chunk.get("_source_text_size")]
    if source_sizes:
        return int(max(source_sizes))
    return max((int(chunk.get("char_end") or 0) for chunk in chunks), default=0)


def _pages(chunks: list[dict[str, Any]]) -> list[int]:
    pages = []
    for chunk in chunks:
        page = chunk.get("page")
        if page is None:
            continue
        try:
            pages.append(int(page))
        except (TypeError, ValueError):
            continue
    return sorted(set(pages))


def _has_structural_marker(text: str) -> bool:
    return detect_structure_type(text) != "text_span"


def _has_table_marker(text: str) -> bool:
    return bool(re.search(r"\btable\s+\d+|\S+\s{3,}\S+\s{3,}\S+", text, re.I))


def _boundary_split_risk(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    starts_mid_sentence = stripped[0].islower()
    ends_open = stripped[-1] not in ".;:!?)\"]}"
    return starts_mid_sentence or ends_open


def _sidecar_summary(derived_dir: Path) -> dict[str, Any]:
    summary_path = derived_dir / "chunks_v2" / "summary.json"
    if not summary_path.exists():
        return {
            "schema_version": CHUNK_LAYER_SCHEMA_VERSION,
            "present": False,
            "validation_passed": False,
        }
    summary = _read_json(summary_path)
    return {
        "schema_version": summary.get("schema_version"),
        "present": True,
        "summary_path": str(summary_path),
        "validation_passed": bool(summary.get("validation_passed")),
        "atomic_chunk_count": int(summary.get("atomic_chunk_count") or 0),
        "structural_chunk_count": int(summary.get("structural_chunk_count") or 0),
        "parent_context_window_count": int(summary.get("parent_context_window_count") or 0),
    }


def _checks(
    chunks_path: Path,
    chunks: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    required = {
        "chunk_id",
        "source_set_id",
        "source_record_id",
        "artifact_sha256",
        "citation_label",
        "char_start",
        "char_end",
        "text",
    }
    missing_required = [
        str(chunk.get("chunk_id") or f"index:{index}")
        for index, chunk in enumerate(chunks)
        if required - set(chunk)
    ]
    bad_offsets = [
        str(chunk.get("chunk_id") or f"index:{index}")
        for index, chunk in enumerate(chunks)
        if int(chunk.get("char_end") or 0) <= int(chunk.get("char_start") or 0)
    ]
    return [
        {
            "name": "chunks_jsonl_exists",
            "passed": chunks_path.exists(),
            "details": {"path": str(chunks_path)},
        },
        {
            "name": "chunks_loaded",
            "passed": bool(chunks),
            "details": {"chunk_count": len(chunks)},
        },
        {
            "name": "required_chunk_fields_present",
            "passed": not missing_required,
            "details": {"missing_required_chunk_ids": missing_required[:20]},
        },
        {
            "name": "chunk_offsets_valid",
            "passed": not bad_offsets,
            "details": {"bad_offset_chunk_ids": bad_offsets[:20]},
        },
        {
            "name": "source_identity_present",
            "passed": all(source["source_record_id"] for source in sources),
            "details": {"source_count": len(sources)},
        },
    ]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing chunks JSONL: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    source_set_id = _read_json(manifest_path).get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
