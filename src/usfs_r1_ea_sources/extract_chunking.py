from __future__ import annotations

from pathlib import Path
import hashlib
import re

from .extract_common import ExtractionPayload
from .extract_common import TextBlock
from .extract_common import _clean_text
from .extract_common import _final_url

def _blocks_from_plain_text(text: str) -> tuple[str, list[TextBlock]]:
    blocks = _blocks_from_text_fragments(re.split(r"\n\s*\n", text))
    return _assemble_blocks(blocks)


def _blocks_from_text_fragments(fragments: list[str]) -> list[TextBlock]:
    return [TextBlock(text=cleaned) for fragment in fragments if (cleaned := _clean_text(fragment))]


def _assemble_blocks(blocks: list[TextBlock]) -> tuple[str, list[TextBlock]]:
    assembled_parts: list[str] = []
    offset = 0
    offset_blocks: list[TextBlock] = []
    for block in blocks:
        text = _clean_text(block.text)
        if not text:
            continue
        if assembled_parts:
            assembled_parts.append("\n\n")
            offset += 2
        start = offset
        assembled_parts.append(text)
        offset += len(text)
        offset_blocks.append(
            TextBlock(
                text=text,
                heading=block.heading,
                section=block.section,
                page=block.page,
                char_start=start,
                char_end=offset,
            )
        )
    return "".join(assembled_parts), offset_blocks


def _chunks_for_payload(
    *,
    row: dict,
    payload: ExtractionPayload,
    extracted_at: str,
    source_text_path: Path,
    max_chars: int,
    overlap_chars: int,
) -> list[dict]:
    chunks: list[dict] = []
    text_chunks = _chunk_text(payload.text, payload.blocks, max_chars, overlap_chars)
    for index, chunk in enumerate(text_chunks):
        content_sha256 = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
        chunk_id = _chunk_id(
            source_set_id=row["source_set_id"],
            source_record_id=row["source_record_id"],
            artifact_sha256=row["artifact_sha256"],
            chunk_index=index,
            char_start=chunk["char_start"],
            content_sha256=content_sha256,
        )
        chunks.append(
            {
                "chunk_id": chunk_id,
                "source_set_id": row["source_set_id"],
                "source_record_id": row["source_record_id"],
                "chunk_index": index,
                "title": row["title"],
                "document_role": row["document_role"],
                "support_document_role": row.get("support_document_role"),
                "authority_level": row["authority_level"],
                "host": row["host"],
                "expected_parser": row["expected_parser"],
                "artifact_sha256": row["artifact_sha256"],
                "artifact_path": row["artifact_path"],
                "citation_label": row["citation_label"],
                "original_url": row["original_url"],
                "effective_url": row["effective_url"],
                "final_url": _final_url(row),
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


def _chunk_text(
    text: str,
    blocks: list[TextBlock],
    max_chars: int,
    overlap_chars: int,
) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    chunks: list[dict] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        target_end = min(start + max_chars, text_len)
        end = _choose_chunk_end(text, start, target_end, max_chars)
        raw = text[start:end]
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw.rstrip())
        chunk_start = start + leading
        chunk_end = start + trailing
        chunk_text = text[chunk_start:chunk_end]
        if chunk_text:
            block = _block_for_offset(blocks, chunk_start)
            chunks.append(
                {
                    "text": chunk_text,
                    "char_start": chunk_start,
                    "char_end": chunk_end,
                    "heading": block.heading if block else None,
                    "section": block.section if block else None,
                    "page": block.page if block else None,
                }
            )
        if end >= text_len:
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def _choose_chunk_end(text: str, start: int, target_end: int, max_chars: int) -> int:
    if target_end >= len(text):
        return len(text)
    min_end = start + max(256, max_chars // 2)
    candidate = text.rfind("\n\n", start, target_end)
    if candidate >= min_end:
        return candidate
    candidate = text.rfind(". ", start, target_end)
    if candidate >= min_end:
        return candidate + 1
    candidate = text.rfind(" ", start, target_end)
    if candidate >= min_end:
        return candidate
    return target_end


def _block_for_offset(blocks: list[TextBlock], offset: int) -> TextBlock | None:
    for block in blocks:
        if block.char_start is None or block.char_end is None:
            continue
        if block.char_start <= offset < block.char_end:
            return block
    return blocks[-1] if blocks else None


def _chunk_id(
    *,
    source_set_id: str,
    source_record_id: str,
    artifact_sha256: str,
    chunk_index: int,
    char_start: int,
    content_sha256: str,
) -> str:
    material = "|".join(
        [
            source_set_id,
            source_record_id,
            artifact_sha256,
            str(chunk_index),
            str(char_start),
            content_sha256,
        ]
    )
    return f"chunk:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"
