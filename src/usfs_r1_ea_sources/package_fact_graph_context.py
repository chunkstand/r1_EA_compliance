from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evidence_strength import EVIDENCE_STRENGTH_SCHEMA_VERSION
from .package_fact_graph_runtime import _add_edge
from .package_fact_graph_runtime import _build_uncertainty_records
from .package_fact_graph_runtime import _context_excerpt
from .package_fact_graph_runtime import _node_id
from .package_fact_graph_runtime import _parser_provenance
from .package_fact_graph_runtime import _section_family
from .package_fact_graph_runtime import _section_node_for_chunk


FOREST_PLAN_CONTEXT_FACT_EXTRACTION_METHOD_VERSION = (
    "forest-plan-context-package-fact-bridge-v0"
)

_CONTEXT_FACT_COLLECTIONS = {
    "geographic_areas": ("geography", "geographic_area"),
    "management_areas": ("management_area", "forest_plan_management_area"),
    "overlays": ("overlay", "forest_plan_overlay"),
}


def merge_forest_plan_context_facts(
    *,
    extraction: dict[str, Any],
    package_chunks: list[dict[str, Any]],
    forest_plan_context_path: Path,
    review_id: str,
    source_set_id: str,
) -> dict[str, Any]:
    """Merge resolver-scoped package evidence into the package fact graph."""

    summary: dict[str, Any] = {
        "context_loaded": False,
        "context_path": str(forest_plan_context_path),
        "fact_node_count": 0,
        "evidence_span_node_count": 0,
        "skipped_evidence_count": 0,
        "fact_type_counts": {},
    }
    if not forest_plan_context_path.exists():
        extraction["forest_plan_context_bridge"] = summary
        return summary

    context = json.loads(forest_plan_context_path.read_text(encoding="utf-8"))
    if not isinstance(context, dict):
        raise ValueError(f"Expected JSON object in {forest_plan_context_path}")
    _validate_context_identity(
        context=context,
        review_id=review_id,
        source_set_id=source_set_id,
        context_path=forest_plan_context_path,
    )

    nodes = extraction["nodes"]
    edges = extraction["edges"]
    seen_node_ids = {str(node.get("node_id")) for node in nodes if isinstance(node, dict)}
    seen_edge_ids = {str(edge.get("edge_id")) for edge in edges if isinstance(edge, dict)}
    chunks_by_id = {
        str(chunk.get("chunk_id") or ""): chunk
        for chunk in package_chunks
        if isinstance(chunk, dict)
    }
    added_fact_counts: dict[str, int] = {}

    for collection_key, (node_type, fact_subtype) in _CONTEXT_FACT_COLLECTIONS.items():
        for entry in _dicts(context.get(collection_key)):
            for evidence in _dicts(entry.get("package_evidence")):
                added = _add_context_fact(
                    nodes=nodes,
                    edges=edges,
                    seen_node_ids=seen_node_ids,
                    seen_edge_ids=seen_edge_ids,
                    chunks_by_id=chunks_by_id,
                    context_path=forest_plan_context_path,
                    collection_key=collection_key,
                    node_type=node_type,
                    fact_subtype=fact_subtype,
                    entry=entry,
                    evidence=evidence,
                )
                if not added:
                    summary["skipped_evidence_count"] += 1
                    continue
                summary["fact_node_count"] += 1
                added_fact_counts[node_type] = added_fact_counts.get(node_type, 0) + 1
                if added == "with_span":
                    summary["evidence_span_node_count"] += 1

    uncertainty_records, contradiction_edges = _build_uncertainty_records(nodes)
    for edge in contradiction_edges:
        edge_id = str(edge.get("edge_id") or "")
        if edge_id and edge_id not in seen_edge_ids:
            edges.append(edge)
            seen_edge_ids.add(edge_id)
    extraction["uncertainty_records"] = uncertainty_records
    extraction["edges"] = sorted(edges, key=lambda edge: str(edge["edge_id"]))
    extraction["nodes"] = sorted(nodes, key=lambda node: str(node["node_id"]))
    summary["context_loaded"] = True
    summary["context_schema_version"] = context.get("schema_version")
    summary["fact_type_counts"] = dict(sorted(added_fact_counts.items()))
    extraction["forest_plan_context_bridge"] = summary
    return summary


def _validate_context_identity(
    *,
    context: dict[str, Any],
    review_id: str,
    source_set_id: str,
    context_path: Path,
) -> None:
    context_review_id = str(context.get("review_id") or "").strip()
    context_source_set_id = str(context.get("source_set_id") or "").strip()
    if context_review_id and context_review_id != review_id:
        raise ValueError(
            f"forest_plan_context review_id mismatch in {context_path}: "
            f"{context_review_id} != {review_id}"
        )
    if context_source_set_id and context_source_set_id != source_set_id:
        raise ValueError(
            f"forest_plan_context source_set_id mismatch in {context_path}: "
            f"{context_source_set_id} != {source_set_id}"
        )


def _add_context_fact(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    seen_node_ids: set[str],
    seen_edge_ids: set[str],
    chunks_by_id: dict[str, dict[str, Any]],
    context_path: Path,
    collection_key: str,
    node_type: str,
    fact_subtype: str,
    entry: dict[str, Any],
    evidence: dict[str, Any],
) -> str | None:
    entry_id = str(entry.get("entry_id") or evidence.get("entry_id") or "").strip()
    if not entry_id:
        return None
    chunk_id = str(evidence.get("chunk_id") or "").strip()
    chunk = chunks_by_id.get(chunk_id)
    if not chunk:
        return None
    span = evidence.get("evidence_span")
    if not isinstance(span, dict):
        return None
    span_bounds = _span_bounds(span, chunk)
    if span_bounds is None:
        return None
    span_start, span_end = span_bounds
    section_node = _section_node_for_chunk(chunk)
    section_id = str(section_node["node_id"])
    if section_id not in seen_node_ids:
        nodes.append(section_node)
        seen_node_ids.add(section_id)

    label = str(entry.get("name") or evidence.get("name") or entry_id)
    matched_alias = str(evidence.get("matched_alias") or label)
    span_text = str(span.get("text") or "")
    if not span_text:
        span_text = _context_excerpt(str(chunk.get("text") or ""), span_start, span_end)
    evidence_strength = _observed_context_strength(
        matched_text=matched_alias,
        evidence_window=span_text,
        section_family=_section_family(chunk),
    )
    span_id = _node_id(
        "forest-plan-context-span",
        chunk_id,
        node_type,
        entry_id,
        str(span_start),
        str(span_end),
        str(chunk.get("content_sha256") or ""),
    )
    fact_node_id = _node_id(
        "forest-plan-context-fact",
        node_type,
        fact_subtype,
        entry_id,
        chunk_id,
        str(span_start),
        str(span_end),
    )
    span_added = False
    absolute_start = _absolute_offset(chunk.get("char_start"), span_start)
    absolute_end = _absolute_offset(chunk.get("char_start"), span_end)
    if span_id not in seen_node_ids:
        nodes.append(
            {
                "node_id": span_id,
                "node_type": "evidence_span",
                "label": f"{chunk.get('citation_label') or chunk_id} context span {span_start}-{span_end}",
                "normalized_value": span_id,
                "confidence_class": "observed",
                "evidence_strength": evidence_strength,
                "extraction_method": FOREST_PLAN_CONTEXT_FACT_EXTRACTION_METHOD_VERSION,
                "package_chunk_ids": [chunk_id],
                "section_ids": [section_id],
                "section_family": _section_family(chunk),
                "citation_label": evidence.get("citation_label") or chunk.get("citation_label"),
                "page_label": _page_label(chunk),
                "char_start": absolute_start,
                "char_end": absolute_end,
                "chunk_char_start": span_start,
                "chunk_char_end": span_end,
                "text_hash": chunk.get("content_sha256"),
                "content_sha256": chunk.get("content_sha256"),
                "artifact_sha256": chunk.get("artifact_sha256"),
                "parser_provenance": _parser_provenance(chunk),
                "matched_text": matched_alias,
                "context_excerpt": span_text,
                "evidence_span_ids": [span_id],
            }
        )
        seen_node_ids.add(span_id)
        span_added = True
    if fact_node_id in seen_node_ids:
        return "with_span" if span_added else "existing"
    nodes.append(
        {
            "node_id": fact_node_id,
            "node_type": node_type,
            "fact_subtype": fact_subtype,
            "label": label,
            "raw_value": matched_alias,
            "normalized_value": entry_id,
            "confidence_class": "observed",
            "evidence_strength": evidence_strength,
            "extraction_method": FOREST_PLAN_CONTEXT_FACT_EXTRACTION_METHOD_VERSION,
            "source_metadata": _source_metadata(
                context_path=context_path,
                collection_key=collection_key,
                entry=entry,
                evidence=evidence,
            ),
            "package_chunk_ids": [chunk_id],
            "section_ids": [section_id],
            "section_family": _section_family(chunk),
            "citation_label": evidence.get("citation_label") or chunk.get("citation_label"),
            "page_label": _page_label(chunk),
            "char_start": absolute_start,
            "char_end": absolute_end,
            "chunk_char_start": span_start,
            "chunk_char_end": span_end,
            "text_hash": chunk.get("content_sha256"),
            "content_sha256": chunk.get("content_sha256"),
            "artifact_sha256": chunk.get("artifact_sha256"),
            "parser_provenance": _parser_provenance(chunk),
            "evidence_span_ids": [span_id],
            "package_span_ids": [span_id],
            "matched_text": matched_alias,
            "context_excerpt": span_text,
        }
    )
    seen_node_ids.add(fact_node_id)
    _add_edge(
        edges=edges,
        seen_edge_ids=seen_edge_ids,
        edge_type="supports_fact",
        from_node_id=span_id,
        to_node_id=fact_node_id,
        evidence_span_ids=[span_id],
        rationale="Forest Plan resolver package evidence supports scoped package fact.",
    )
    _add_edge(
        edges=edges,
        seen_edge_ids=seen_edge_ids,
        edge_type="derived_from_section",
        from_node_id=fact_node_id,
        to_node_id=section_id,
        evidence_span_ids=[span_id],
        rationale="Forest Plan context fact was extracted from the package section containing the span.",
    )
    return "with_span" if span_added else "existing"


def _source_metadata(
    *,
    context_path: Path,
    collection_key: str,
    entry: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": "forest_plan_context",
        "context_path": str(context_path),
        "context_collection": collection_key,
        "entry_id": entry.get("entry_id") or evidence.get("entry_id"),
        "entry_category": entry.get("category") or evidence.get("category"),
        "entry_name": entry.get("name") or evidence.get("name"),
        "evidence_role": evidence.get("evidence_role"),
        "matched_alias": evidence.get("matched_alias"),
        "source_record_id": evidence.get("source_record_id"),
        "title": evidence.get("title"),
    }


def _observed_context_strength(
    *,
    matched_text: str,
    evidence_window: str,
    section_family: str,
) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_STRENGTH_SCHEMA_VERSION,
        "confidence_class": "observed",
        "strength_class": "observed",
        "reason": "forest_plan_context_package_evidence",
        "matched_phrase": None,
        "matched_text": matched_text,
        "evidence_window": evidence_window,
        "evidence_window_start": None,
        "evidence_window_end": None,
        "section_family": section_family,
    }


def _span_bounds(span: dict[str, Any], chunk: dict[str, Any]) -> tuple[int, int] | None:
    start = _int_or_none(span.get("chunk_char_start"))
    end = _int_or_none(span.get("chunk_char_end"))
    if start is None or end is None or end <= start:
        source_start = _int_or_none(span.get("source_char_start"))
        source_end = _int_or_none(span.get("source_char_end"))
        chunk_start = _int_or_none(chunk.get("char_start"))
        if source_start is not None and source_end is not None and chunk_start is not None:
            start = source_start - chunk_start
            end = source_end - chunk_start
    if start is None or end is None or end <= start:
        return None
    text_length = len(str(chunk.get("text") or ""))
    start = max(0, min(start, text_length))
    end = max(start, min(end, text_length))
    if end <= start:
        return None
    return start, end


def _page_label(chunk: dict[str, Any]) -> str | None:
    value = chunk.get("page_label") or chunk.get("page")
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _absolute_offset(base: object, offset: int) -> int:
    try:
        return int(base) + offset
    except (TypeError, ValueError):
        return offset


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
