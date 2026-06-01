from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .source_set_support import source_derived_dir


CHUNK_LAYER_SCHEMA_VERSION = "chunk-layers-v1"
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}")
STRUCTURAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("forest_plan_standard", re.compile(r"\b(?:standard|std)\s+[A-Z0-9_.-]+", re.I)),
    ("forest_plan_guideline", re.compile(r"\bguideline[s]?\s+[A-Z0-9_.-]+", re.I)),
    ("desired_condition", re.compile(r"\bdesired condition[s]?\b", re.I)),
    ("objective", re.compile(r"\bobjective[s]?\s+[A-Z0-9_.-]+", re.I)),
    ("definition", re.compile(r"\bdefinition[s]?\b|^\s*[A-Za-z][A-Za-z -]{2,}:\s+", re.I | re.M)),
    ("legal_section", re.compile(r"\b(?:\d+\s*(?:U\.?S\.?C\.?|CFR)|§)\s*[\w.-]+", re.I)),
    ("numbered_requirement", re.compile(r"^\s*(?:\(\w+\)|\d+[.)])\s+\S+", re.M)),
    ("table_row", re.compile(r"\btable\s+\d+|\S+\s{3,}\S+\s{3,}\S+", re.I)),
)


@dataclass(frozen=True)
class ChunkLayerBuildResult:
    source_set_id: str
    output_dir: Path
    atomic_chunks_path: Path
    structural_chunks_path: Path
    parent_windows_path: Path
    summary_path: Path
    summary: dict[str, Any]


def build_chunk_layers(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    chunks_path: Path | None = None,
    chunks_v2_dir: Path | None = None,
    atomic_max_tokens: int = 600,
    parent_window_max_tokens: int = 1500,
) -> ChunkLayerBuildResult:
    """Build sidecar atomic, structural, and parent context chunk layers."""

    output_dir = Path(output_dir)
    source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    derived_dir = source_derived_dir(output_dir / "derived", source_set_id)
    chunks_path = chunks_path or derived_dir / "chunks" / "chunks.jsonl"
    chunks_v2_dir = chunks_v2_dir or derived_dir / "chunks_v2"
    atomic_chunks_path = chunks_v2_dir / "atomic_chunks.jsonl"
    structural_chunks_path = chunks_v2_dir / "structural_chunks.jsonl"
    parent_windows_path = chunks_v2_dir / "parent_context_windows.jsonl"
    summary_path = chunks_v2_dir / "summary.json"

    chunks = _read_jsonl(chunks_path)
    parent_windows = _parent_windows_for_chunks(
        chunks,
        source_set_id=source_set_id,
        max_tokens=parent_window_max_tokens,
    )
    windows_by_source = _windows_by_source(parent_windows)
    atomic_chunks = _atomic_chunks_for_chunks(
        chunks,
        parent_windows_by_source=windows_by_source,
        max_tokens=atomic_max_tokens,
    )
    structural_chunks = [
        _structural_chunk_from_atomic(chunk)
        for chunk in atomic_chunks
        if chunk.get("structure_type") != "text_span"
    ]

    chunks_v2_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(atomic_chunks_path, atomic_chunks)
    _write_jsonl(structural_chunks_path, structural_chunks)
    _write_jsonl(parent_windows_path, parent_windows)
    summary = {
        "schema_version": CHUNK_LAYER_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "baseline_chunks_path": str(chunks_path),
        "chunks_v2_dir": str(chunks_v2_dir),
        "atomic_chunks_path": str(atomic_chunks_path),
        "structural_chunks_path": str(structural_chunks_path),
        "parent_context_windows_path": str(parent_windows_path),
        "baseline_chunk_count": len(chunks),
        "atomic_chunk_count": len(atomic_chunks),
        "structural_chunk_count": len(structural_chunks),
        "parent_context_window_count": len(parent_windows),
        "atomic_chunks_with_parent_window_count": sum(
            1 for chunk in atomic_chunks if chunk.get("parent_window_id")
        ),
        "structure_type_counts": dict(
            Counter(str(chunk.get("structure_type") or "unknown") for chunk in atomic_chunks)
        ),
        "parser_counts": dict(Counter(str(chunk.get("parser_name") or "") for chunk in chunks)),
        "validation_passed": _sidecar_validation_passed(atomic_chunks, parent_windows),
    }
    _write_json(summary_path, summary)
    return ChunkLayerBuildResult(
        source_set_id=source_set_id,
        output_dir=chunks_v2_dir,
        atomic_chunks_path=atomic_chunks_path,
        structural_chunks_path=structural_chunks_path,
        parent_windows_path=parent_windows_path,
        summary_path=summary_path,
        summary=summary,
    )


def contextual_index_text(chunk: dict[str, Any]) -> str:
    prefix_parts = [
        ("source_record_id", chunk.get("source_record_id")),
        ("citation_label", chunk.get("citation_label")),
        ("title", chunk.get("title")),
        ("document_role", chunk.get("document_role")),
        ("support_document_role", chunk.get("support_document_role")),
        ("authority_level", chunk.get("authority_level")),
        ("section", chunk.get("section") or chunk.get("section_path")),
        ("heading", chunk.get("heading") or chunk.get("heading_path")),
        ("page_range", chunk.get("page_range") or chunk.get("page")),
        ("parser", chunk.get("parser_name")),
        ("structure_type", chunk.get("structure_type")),
    ]
    lines = [
        f"{name}: {str(value).strip()}"
        for name, value in prefix_parts
        if value is not None and str(value).strip()
    ]
    return "\n".join([*lines, "text:", str(chunk.get("text") or "")]).strip()


def detect_structure_type(text: str) -> str:
    for structure_type, pattern in STRUCTURAL_PATTERNS:
        if pattern.search(text):
            return structure_type
    return "text_span"


def token_count(text: str) -> int:
    return len(TOKEN_RE.findall(text or ""))


def _atomic_chunks_for_chunks(
    chunks: list[dict[str, Any]],
    *,
    parent_windows_by_source: dict[str, list[dict[str, Any]]],
    max_tokens: int,
) -> list[dict[str, Any]]:
    atomic_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        for unit_index, unit in enumerate(_text_units(text, max_tokens=max_tokens)):
            source_start = int(chunk.get("char_start") or 0) + unit["start"]
            source_end = int(chunk.get("char_start") or 0) + unit["end"]
            atomic = _base_sidecar_record(
                chunk,
                layer="atomic_text_chunk_v2",
                layer_index=unit_index,
                text=unit["text"],
                source_start=source_start,
                source_end=source_end,
            )
            atomic["parent_window_id"] = _parent_window_id_for_span(
                atomic,
                parent_windows_by_source.get(str(chunk.get("source_record_id") or ""), []),
            )
            atomic["contextual_index_text"] = contextual_index_text(atomic)
            atomic["contextual_index_sha256"] = _sha256(atomic["contextual_index_text"])
            atomic_chunks.append(atomic)
    return atomic_chunks


def _base_sidecar_record(
    chunk: dict[str, Any],
    *,
    layer: str,
    layer_index: int,
    text: str,
    source_start: int,
    source_end: int,
) -> dict[str, Any]:
    structure_type = detect_structure_type(text)
    content_sha256 = _sha256(text)
    chunk_id = _stable_id(
        layer,
        str(chunk.get("source_set_id") or ""),
        str(chunk.get("source_record_id") or ""),
        str(chunk.get("artifact_sha256") or ""),
        str(chunk.get("chunk_id") or ""),
        str(source_start),
        str(source_end),
        content_sha256,
    )
    page = chunk.get("page")
    page_range = [page, page] if page is not None else None
    return {
        "chunk_layer": layer,
        "chunk_id": chunk_id,
        "parent_chunk_id": chunk.get("chunk_id"),
        "parent_window_id": None,
        "source_set_id": chunk.get("source_set_id"),
        "source_record_id": chunk.get("source_record_id"),
        "chunk_index": layer_index,
        "title": chunk.get("title"),
        "document_role": chunk.get("document_role"),
        "support_document_role": chunk.get("support_document_role") or chunk.get("document_role"),
        "authority_level": chunk.get("authority_level"),
        "host": chunk.get("host"),
        "expected_parser": chunk.get("expected_parser"),
        "artifact_sha256": chunk.get("artifact_sha256"),
        "artifact_path": chunk.get("artifact_path"),
        "citation_label": chunk.get("citation_label"),
        "original_url": chunk.get("original_url"),
        "effective_url": chunk.get("effective_url"),
        "final_url": chunk.get("final_url"),
        "parser_name": chunk.get("parser_name"),
        "parser_version": chunk.get("parser_version"),
        "extracted_at": chunk.get("extracted_at"),
        "source_text_path": chunk.get("source_text_path"),
        "char_start": source_start,
        "char_end": source_end,
        "page": page,
        "page_range": page_range,
        "section": chunk.get("section"),
        "heading": chunk.get("heading"),
        "section_path": _path_value(chunk.get("section")),
        "heading_path": _path_value(chunk.get("heading")),
        "structure_type": structure_type,
        "component_type": _component_type(structure_type),
        "table_id": _table_id(text) if structure_type == "table_row" else None,
        "row_index": None,
        "cell_coordinates": None,
        "token_count": token_count(text),
        "content_sha256": content_sha256,
        "text": text,
    }


def _structural_chunk_from_atomic(chunk: dict[str, Any]) -> dict[str, Any]:
    structural = dict(chunk)
    structural["chunk_layer"] = "structural_evidence_chunk_v1"
    structural["chunk_id"] = _stable_id(
        "structural_evidence_chunk_v1",
        str(chunk.get("chunk_id") or ""),
        str(chunk.get("structure_type") or ""),
    )
    structural["atomic_chunk_id"] = chunk.get("chunk_id")
    structural["contextual_index_text"] = contextual_index_text(structural)
    structural["contextual_index_sha256"] = _sha256(structural["contextual_index_text"])
    return structural


def _parent_windows_for_chunks(
    chunks: list[dict[str, Any]],
    *,
    source_set_id: str,
    max_tokens: int,
) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        by_source[str(chunk.get("source_record_id") or "")].append(chunk)

    windows: list[dict[str, Any]] = []
    for source_record_id, source_chunks in sorted(by_source.items()):
        sorted_chunks = sorted(
            source_chunks,
            key=lambda c: (int(c.get("char_start") or 0), c.get("chunk_id") or ""),
        )
        current: list[dict[str, Any]] = []
        current_tokens = 0
        for chunk in sorted_chunks:
            chunk_tokens = max(1, token_count(str(chunk.get("text") or "")))
            if current and current_tokens + chunk_tokens > max_tokens:
                windows.append(_parent_window(source_set_id, source_record_id, len(windows), current))
                current = []
                current_tokens = 0
            current.append(chunk)
            current_tokens += chunk_tokens
        if current:
            windows.append(_parent_window(source_set_id, source_record_id, len(windows), current))
    return windows


def _parent_window(
    source_set_id: str,
    source_record_id: str,
    index: int,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    first = chunks[0]
    text = "\n\n".join(str(chunk.get("text") or "") for chunk in chunks if chunk.get("text"))
    char_start = min(int(chunk.get("char_start") or 0) for chunk in chunks)
    char_end = max(int(chunk.get("char_end") or 0) for chunk in chunks)
    pages = sorted(
        {
            int(chunk["page"])
            for chunk in chunks
            if chunk.get("page") is not None and str(chunk.get("page")).isdigit()
        }
    )
    content_sha256 = _sha256(text)
    return {
        "schema_version": CHUNK_LAYER_SCHEMA_VERSION,
        "window_id": _stable_id(
            "parent_context_window_v1",
            source_set_id,
            source_record_id,
            str(index),
            str(char_start),
            str(char_end),
            content_sha256,
        ),
        "chunk_layer": "parent_context_window_v1",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "window_index": index,
        "source_chunk_ids": [chunk.get("chunk_id") for chunk in chunks],
        "citation_label": first.get("citation_label"),
        "title": first.get("title"),
        "document_role": first.get("document_role"),
        "authority_level": first.get("authority_level"),
        "artifact_sha256": first.get("artifact_sha256"),
        "artifact_path": first.get("artifact_path"),
        "parser_name": first.get("parser_name"),
        "char_start": char_start,
        "char_end": char_end,
        "page_range": [pages[0], pages[-1]] if pages else None,
        "token_count": token_count(text),
        "content_sha256": content_sha256,
        "text": text,
    }


def _parent_window_id_for_span(
    chunk: dict[str, Any],
    windows: list[dict[str, Any]],
) -> str | None:
    start = int(chunk.get("char_start") or 0)
    end = int(chunk.get("char_end") or start)
    for window in windows:
        if int(window.get("char_start") or 0) <= start and end <= int(window.get("char_end") or 0):
            return str(window.get("window_id") or "")
    return str(windows[0].get("window_id") or "") if windows else None


def _text_units(text: str, *, max_tokens: int) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for match in re.finditer(r"\S(?:.*?\S)?(?=\n\s*\n|\Z)", text, flags=re.S):
        raw = match.group(0)
        stripped = raw.strip()
        if not stripped:
            continue
        leading = len(raw) - len(raw.lstrip())
        start = match.start() + leading
        units.extend(_split_large_unit(stripped, base_start=start, max_tokens=max_tokens))
    return units or [{"start": 0, "end": len(text), "text": text.strip()}]


def _split_large_unit(text: str, *, base_start: int, max_tokens: int) -> list[dict[str, Any]]:
    if token_count(text) <= max_tokens:
        return [{"start": base_start, "end": base_start + len(text), "text": text}]
    pieces: list[dict[str, Any]] = []
    start = 0
    while start < len(text):
        end = _token_window_end(text, start=start, max_tokens=max_tokens)
        piece = text[start:end].strip()
        if piece:
            leading = len(text[start:end]) - len(text[start:end].lstrip())
            piece_start = base_start + start + leading
            pieces.append({"start": piece_start, "end": piece_start + len(piece), "text": piece})
        if end >= len(text):
            break
        start = max(end, start + 1)
    return pieces


def _token_window_end(text: str, *, start: int, max_tokens: int) -> int:
    count = 0
    last_end = start
    for match in TOKEN_RE.finditer(text, pos=start):
        count += 1
        last_end = match.end()
        if count >= max_tokens:
            sentence_end = text.find(". ", last_end)
            if 0 <= sentence_end <= last_end + 240:
                return sentence_end + 1
            return last_end
    return len(text)


def _windows_by_source(windows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for window in windows:
        grouped[str(window.get("source_record_id") or "")].append(window)
    return grouped


def _sidecar_validation_passed(
    atomic_chunks: list[dict[str, Any]],
    parent_windows: list[dict[str, Any]],
) -> bool:
    if not atomic_chunks:
        return False
    chunk_ids = [str(chunk.get("chunk_id") or "") for chunk in atomic_chunks]
    if len(set(chunk_ids)) != len(chunk_ids):
        return False
    parent_ids = {window["window_id"] for window in parent_windows}
    return all(
        chunk.get("source_record_id")
        and chunk.get("citation_label")
        and chunk.get("artifact_sha256")
        and chunk.get("parent_window_id") in parent_ids
        and int(chunk.get("char_end") or 0) > int(chunk.get("char_start") or 0)
        for chunk in atomic_chunks
    )


def _component_type(structure_type: str) -> str | None:
    if structure_type.startswith("forest_plan_") or structure_type in {
        "desired_condition",
        "objective",
    }:
        return structure_type
    return None


def _table_id(text: str) -> str | None:
    match = re.search(r"\btable\s+([A-Za-z0-9_.-]+)", text, re.I)
    return f"table:{match.group(1)}" if match else None


def _path_value(value: object | None) -> list[str]:
    if value is None or not str(value).strip():
        return []
    return [part.strip() for part in str(value).split(">") if part.strip()]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing chunks JSONL: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    source_set_id = _read_json(manifest_path).get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _stable_id(*parts: str) -> str:
    return "chunk:" + hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
