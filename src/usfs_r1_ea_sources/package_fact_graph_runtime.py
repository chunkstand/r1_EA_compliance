from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import re
from typing import Any

from .evidence_strength import classify_evidence_strength
from .forest_plan_profiles import ForestPlanProfileCollection
from .package_fact_graph_terms import COMMON_PACKAGE_FACT_TYPES
from .package_fact_graph_terms import LOCATION_NODE_TYPES
from .package_fact_graph_terms import PACKAGE_FACT_EXTRACTION_METHOD_VERSION
from .package_fact_graph_terms import _base_term_specs
from .package_fact_graph_terms import _profile_term_specs


def _extract_package_facts(
    *,
    package_chunks: list[dict[str, Any]],
    profiles: ForestPlanProfileCollection,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    section_nodes: dict[str, dict[str, Any]] = {}
    suppressed_location_facts: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()
    seen_edge_ids: set[str] = set()
    term_specs = _base_term_specs()
    term_specs.extend(_profile_term_specs(profiles))

    for chunk in package_chunks:
        section_node = _section_node_for_chunk(chunk)
        section_id = str(section_node["node_id"])
        if section_id not in section_nodes:
            section_nodes[section_id] = section_node
        else:
            existing_chunk_ids = section_nodes[section_id]["package_chunk_ids"]
            chunk_id = str(chunk.get("chunk_id") or "")
            if chunk_id and chunk_id not in existing_chunk_ids:
                existing_chunk_ids.append(chunk_id)

        chunk_text = str(chunk.get("text") or "")
        for spec in term_specs:
            for term in spec["terms"]:
                for match in _find_term_matches(chunk_text, term):
                    confidence_class = str(spec.get("confidence_class") or "observed")
                    fact_subtype = str(spec.get("fact_subtype") or "")
                    evidence_strength = classify_evidence_strength(
                        text=chunk_text,
                        start=match.start(),
                        end=match.end(),
                        matched_text=match.group(0),
                        default_confidence_class=confidence_class,
                        section_family=_section_family(chunk),
                    )
                    if spec["node_type"] in LOCATION_NODE_TYPES and _is_negative_location_match(
                        chunk_text,
                        match.start(),
                        match.end(),
                    ):
                        evidence_strength = classify_evidence_strength(
                            text=chunk_text,
                            start=match.start(),
                            end=match.end(),
                            matched_text=match.group(0),
                            section_family=_section_family(chunk),
                            negative_context=True,
                            negative_reason="negative_or_out_of_scope_location_context",
                        )
                        confidence_class = str(evidence_strength["confidence_class"])
                        suppressed_location_facts.append(
                            {
                                "node_type": spec["node_type"],
                                "fact_subtype": fact_subtype,
                                "normalized_value": spec["normalized_value"],
                                "label": spec["label"],
                                "matched_text": match.group(0),
                                "chunk_id": chunk.get("chunk_id"),
                                "chunk_char_start": match.start(),
                                "chunk_char_end": match.end(),
                                "section_id": section_id,
                                "reason": "negative_or_out_of_scope_location_context",
                                "evidence_strength": evidence_strength,
                            }
                        )
                    else:
                        confidence_class = str(evidence_strength["confidence_class"])
                    _add_fact_node(
                        nodes=nodes,
                        edges=edges,
                        seen_node_ids=seen_node_ids,
                        seen_edge_ids=seen_edge_ids,
                        chunk=chunk,
                        section_id=section_id,
                        spec=spec,
                        match_start=match.start(),
                        match_end=match.end(),
                        matched_text=match.group(0),
                        confidence_class=confidence_class,
                        evidence_strength=evidence_strength,
                    )

    nodes = [*section_nodes.values(), *nodes]
    uncertainty_records, contradiction_edges = _build_uncertainty_records(nodes)
    for edge in contradiction_edges:
        if edge["edge_id"] not in seen_edge_ids:
            edges.append(edge)
            seen_edge_ids.add(edge["edge_id"])

    nodes.sort(key=lambda node: str(node["node_id"]))
    edges.sort(key=lambda edge: str(edge["edge_id"]))
    return {
        "nodes": nodes,
        "edges": edges,
        "section_map": _section_map(section_nodes),
        "uncertainty_records": uncertainty_records,
        "suppressed_location_facts": sorted(
            suppressed_location_facts,
            key=lambda item: (
                str(item["chunk_id"]),
                str(item["node_type"]),
                str(item["normalized_value"]),
            ),
        ),
    }


def _add_fact_node(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    seen_node_ids: set[str],
    seen_edge_ids: set[str],
    chunk: dict[str, Any],
    section_id: str,
    spec: dict[str, Any],
    match_start: int,
    match_end: int,
    matched_text: str,
    confidence_class: str,
    evidence_strength: dict[str, Any],
) -> None:
    chunk_id = str(chunk.get("chunk_id") or "unknown-chunk")
    absolute_start = _absolute_offset(chunk.get("char_start"), match_start)
    absolute_end = _absolute_offset(chunk.get("char_start"), match_end)
    span_id = _node_id(
        "evidence-span",
        chunk_id,
        str(match_start),
        str(match_end),
        str(chunk.get("content_sha256") or ""),
    )
    fact_node_id = _node_id(
        str(spec["node_type"]),
        str(spec["fact_subtype"]),
        str(spec["normalized_value"]),
        chunk_id,
        str(match_start),
        str(match_end),
        confidence_class,
    )
    if span_id not in seen_node_ids:
        nodes.append(
            {
                "node_id": span_id,
                "node_type": "evidence_span",
                "label": f"{chunk.get('citation_label') or chunk_id} span {match_start}-{match_end}",
                "normalized_value": span_id,
                "confidence_class": "observed",
                "evidence_strength": evidence_strength,
                "extraction_method": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
                "package_chunk_ids": [chunk_id],
                "section_ids": [section_id],
                "section_family": _section_family(chunk),
                "citation_label": chunk.get("citation_label"),
                "page_label": _page_label(chunk),
                "char_start": absolute_start,
                "char_end": absolute_end,
                "chunk_char_start": match_start,
                "chunk_char_end": match_end,
                "text_hash": chunk.get("content_sha256"),
                "content_sha256": chunk.get("content_sha256"),
                "artifact_sha256": chunk.get("artifact_sha256"),
                "parser_provenance": _parser_provenance(chunk),
                "matched_text": matched_text,
                "context_excerpt": _context_excerpt(
                    str(chunk.get("text") or ""),
                    match_start,
                    match_end,
                ),
                "evidence_span_ids": [span_id],
            }
        )
        seen_node_ids.add(span_id)
    if fact_node_id not in seen_node_ids:
        nodes.append(
            {
                "node_id": fact_node_id,
                "node_type": spec["node_type"],
                "fact_subtype": spec["fact_subtype"],
                "label": spec["label"],
                "raw_value": matched_text,
                "normalized_value": spec["normalized_value"],
                "confidence_class": confidence_class,
                "evidence_strength": evidence_strength,
                "extraction_method": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
                "source_metadata": spec["source_metadata"],
                "package_chunk_ids": [chunk_id],
                "section_ids": [section_id],
                "section_family": _section_family(chunk),
                "citation_label": chunk.get("citation_label"),
                "page_label": _page_label(chunk),
                "char_start": absolute_start,
                "char_end": absolute_end,
                "chunk_char_start": match_start,
                "chunk_char_end": match_end,
                "text_hash": chunk.get("content_sha256"),
                "content_sha256": chunk.get("content_sha256"),
                "artifact_sha256": chunk.get("artifact_sha256"),
                "parser_provenance": _parser_provenance(chunk),
                "evidence_span_ids": [span_id],
                "package_span_ids": [span_id],
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
        rationale="Matched package span supports deterministic package fact.",
    )
    _add_edge(
        edges=edges,
        seen_edge_ids=seen_edge_ids,
        edge_type="derived_from_section",
        from_node_id=fact_node_id,
        to_node_id=section_id,
        evidence_span_ids=[span_id],
        rationale="Fact was extracted from the package section containing the span.",
    )


def _add_edge(
    *,
    edges: list[dict[str, Any]],
    seen_edge_ids: set[str],
    edge_type: str,
    from_node_id: str,
    to_node_id: str,
    evidence_span_ids: list[str],
    rationale: str,
    selected_status: str = "selected",
) -> None:
    edge_id = _node_id(edge_type, from_node_id, to_node_id, *evidence_span_ids)
    if edge_id in seen_edge_ids:
        return
    edges.append(
        {
            "edge_id": edge_id,
            "edge_type": edge_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "evidence_span_ids": evidence_span_ids,
            "path_rationale": rationale,
            "selected_status": selected_status,
        }
    )
    seen_edge_ids.add(edge_id)


def _build_uncertainty_records(
    nodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fact_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        if node.get("node_type") in {"package_section", "evidence_span"}:
            continue
        key = (
            str(node.get("node_type")),
            str(node.get("fact_subtype") or ""),
            str(node.get("normalized_value") or ""),
        )
        fact_groups[key].append(node)

    uncertainty_records = []
    contradiction_edges = []
    for key, grouped_nodes in sorted(fact_groups.items()):
        positive = [
            node
            for node in grouped_nodes
            if node.get("confidence_class") != "negative_context"
        ]
        negative = [
            node
            for node in grouped_nodes
            if node.get("confidence_class") == "negative_context"
        ]
        if not positive or not negative:
            weak_nodes = [
                node
                for node in grouped_nodes
                if node.get("confidence_class") == "weak_signal"
            ]
            for weak_node in weak_nodes:
                evidence_strength = weak_node.get("evidence_strength") or {}
                uncertainty_records.append(
                    {
                        "uncertainty_id": _node_id(
                            "uncertainty",
                            "weak-signal",
                            str(weak_node["node_id"]),
                        ),
                        "uncertainty_class": "weak_signal",
                        "node_type": key[0],
                        "fact_subtype": key[1],
                        "normalized_value": key[2],
                        "weak_fact_node_ids": [str(weak_node["node_id"])],
                        "status": "requires_adjudication_before_applicability_decision",
                        "rationale": "Package fact was extracted from conditional or uncertain wording.",
                        "evidence_strength": evidence_strength,
                        "weak_signal_reason": evidence_strength.get("reason"),
                        "matched_phrase": evidence_strength.get("matched_phrase"),
                        "evidence_window": evidence_strength.get("evidence_window"),
                    }
                )
            continue
        uncertainty_records.append(
            {
                "uncertainty_id": _node_id("uncertainty", "contradiction", *key),
                "uncertainty_class": "contradictory_package_evidence",
                "node_type": key[0],
                "fact_subtype": key[1],
                "normalized_value": key[2],
                "positive_fact_node_ids": [str(node["node_id"]) for node in positive],
                "negative_fact_node_ids": [str(node["node_id"]) for node in negative],
                "status": "requires_adjudication_before_applicability_decision",
                "rationale": "Package contains both observed and negative-context facts for the same value.",
            }
        )
        for positive_node in positive:
            for negative_node in negative:
                contradiction_edges.append(
                    {
                        "edge_id": _node_id(
                            "contradicts_fact",
                            str(negative_node["node_id"]),
                            str(positive_node["node_id"]),
                        ),
                        "edge_type": "contradicts_fact",
                        "from_node_id": negative_node["node_id"],
                        "to_node_id": positive_node["node_id"],
                        "evidence_span_ids": list(negative_node.get("evidence_span_ids") or []),
                        "path_rationale": "Negative-context package fact contradicts an observed fact value.",
                        "selected_status": "selected",
                    }
                )
    present_positive = {
        str(node.get("node_type"))
        for grouped_nodes in fact_groups.values()
        for node in grouped_nodes
        if node.get("confidence_class") != "negative_context"
    }
    for fact_type in sorted(COMMON_PACKAGE_FACT_TYPES - present_positive):
        uncertainty_records.append(
            {
                "uncertainty_id": _node_id("uncertainty", "missing-fact-type", fact_type),
                "uncertainty_class": "missing_package_fact_type",
                "node_type": fact_type,
                "fact_subtype": None,
                "normalized_value": None,
                "positive_fact_node_ids": [],
                "negative_fact_node_ids": [],
                "status": "missing_package_fact_type_recorded_for_later_applicability_context",
                "rationale": (
                    "No positive package fact of this common type was extracted; later "
                    "applicability stages must treat it as missing context, not a decision."
                ),
            }
        )
    return uncertainty_records, contradiction_edges


def _build_extraction_summary(
    *,
    package_manifest: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
    extraction: dict[str, Any],
) -> dict[str, Any]:
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]
    fact_type_counts = Counter(str(node["node_type"]) for node in fact_nodes)
    fact_subtype_counts = Counter(
        f"{node.get('node_type')}:{node.get('fact_subtype')}" for node in fact_nodes
    )
    confidence_counts = Counter(str(node["confidence_class"]) for node in fact_nodes)
    evidence_strength_counts = Counter(
        str((node.get("evidence_strength") or {}).get("strength_class") or node["confidence_class"])
        for node in fact_nodes
    )
    return {
        "package_file_count": len(package_manifest),
        "package_chunk_count": len(package_chunks),
        "package_section_count": len(extraction["section_map"]),
        "fact_node_count": len(fact_nodes),
        "evidence_span_node_count": sum(
            1 for node in extraction["nodes"] if node.get("node_type") == "evidence_span"
        ),
        "edge_count": len(extraction["edges"]),
        "fact_type_counts": dict(sorted(fact_type_counts.items())),
        "fact_subtype_counts": dict(sorted(fact_subtype_counts.items())),
        "confidence_class_counts": dict(sorted(confidence_counts.items())),
        "evidence_strength_class_counts": dict(sorted(evidence_strength_counts.items())),
        "negative_location_fact_count": len(extraction["suppressed_location_facts"]),
        "uncertainty_record_count": len(extraction["uncertainty_records"]),
        "weak_signal_fact_count": confidence_counts.get("weak_signal", 0),
        "missing_common_fact_type_count": sum(
            1
            for record in extraction["uncertainty_records"]
            if record.get("uncertainty_class") == "missing_package_fact_type"
        ),
    }


def _section_node_for_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    section_label = _section_label(chunk)
    section_id = _node_id("package-section", section_label)
    chunk_id = str(chunk.get("chunk_id") or "unknown-chunk")
    return {
        "node_id": section_id,
        "node_type": "package_section",
        "label": section_label,
        "normalized_value": _safe_identifier(section_label),
        "confidence_class": "observed",
        "extraction_method": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
        "package_chunk_ids": [chunk_id],
        "section_ids": [section_id],
        "section_family": _section_family(chunk),
        "citation_label": chunk.get("citation_label"),
        "page_label": _page_label(chunk),
        "char_start": chunk.get("char_start"),
        "char_end": chunk.get("char_end"),
        "text_hash": chunk.get("content_sha256"),
        "content_sha256": chunk.get("content_sha256"),
        "artifact_sha256": chunk.get("artifact_sha256"),
        "parser_provenance": _parser_provenance(chunk),
        "evidence_span_ids": [],
    }


def _section_map(section_nodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    section_rows = []
    for node in section_nodes.values():
        section_rows.append(
            {
                "section_id": node["node_id"],
                "section_label": node["label"],
                "section_family": node["section_family"],
                "package_chunk_ids": sorted(node["package_chunk_ids"]),
                "citation_label": node["citation_label"],
                "page_label": node["page_label"],
            }
        )
    return sorted(section_rows, key=lambda row: str(row["section_id"]))


def _section_label(chunk: dict[str, Any]) -> str:
    heading = str(chunk.get("heading") or "").strip()
    section = str(chunk.get("section") or "").strip()
    title = str(chunk.get("title") or "").strip()
    if section and heading and section != heading:
        return f"{section} / {heading}"
    if section:
        return section
    if heading:
        return heading
    if title:
        return f"{title} unsectioned"
    return "unsectioned package content"


def _section_family(chunk: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(chunk.get("section") or ""),
            str(chunk.get("heading") or ""),
            str(chunk.get("text") or "")[:500],
        ]
    ).lower()
    patterns = (
        ("purpose_need", ("purpose and need", "need for action")),
        ("no_action", ("no action alternative", "no action")),
        ("alternatives", ("alternatives", "proposed action", "range of alternatives")),
        ("cumulative_effects", ("cumulative effects", "cumulative impact")),
        ("mitigation", ("mitigation", "design feature", "best management practice")),
        ("public_involvement", ("public involvement", "public comment", "scoping")),
        ("finding_decision", ("decision notice", "finding of no significant impact", "fonsi")),
        ("consultation", ("consultation", "section 7", "section 106")),
        ("affected_environment", ("affected environment", "environmental consequences")),
    )
    for family, terms in patterns:
        if any(term in text for term in terms):
            return family
    return "general"


def _find_term_matches(text: str, term: str) -> list[re.Match[str]]:
    term = " ".join(str(term or "").split())
    if not term:
        return []
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
    return list(pattern.finditer(text))


def _is_negative_location_match(text: str, start: int, end: int) -> bool:
    window = _sentence_around(text, start, end).lower()
    negative_phrases = (
        "not part of the project area",
        "outside the project area",
        "outside of the project area",
        "project is not in this area",
        "project is not within this area",
        "is not in the project area",
        "is not within the project area",
        "not affected by the project",
        "not affected by this project",
        "does not apply to the project area",
        "project does not include",
        "project does not contain",
        "project does not affect",
        "project does not pertain to",
        "no designated wilderness in the project area",
        "no research natural areas in the project area",
    )
    if any(phrase in window for phrase in negative_phrases):
        return True
    return bool(
        re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b"
            r"(?:in\s+the\s+project\s+area|affected\s+by\s+(?:the|this)\s+project)\b",
            window,
        )
    )


def _sentence_around(text: str, start: int, end: int) -> str:
    sentence_start = max(
        text.rfind(".", 0, start),
        text.rfind("\n", 0, start),
        text.rfind(";", 0, start),
    )
    sentence_end_candidates = [
        index
        for index in (
            text.find(".", end),
            text.find("\n", end),
            text.find(";", end),
        )
        if index >= 0
    ]
    sentence_start = sentence_start + 1 if sentence_start >= 0 else 0
    sentence_end = min(sentence_end_candidates) + 1 if sentence_end_candidates else len(text)
    return text[sentence_start:sentence_end]


def _absolute_offset(base: object, offset: int) -> int:
    try:
        return int(base) + offset
    except (TypeError, ValueError):
        return offset


def _page_label(chunk: dict[str, Any]) -> str | None:
    page = chunk.get("page")
    if page is None or str(page).strip() == "":
        return None
    return str(page)


def _parser_provenance(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "parser_name": chunk.get("parser_name"),
        "parser_version": chunk.get("parser_version"),
        "extracted_at": chunk.get("extracted_at"),
        "source_text_path": chunk.get("source_text_path"),
    }


def _context_excerpt(text: str, start: int, end: int, radius: int = 160) -> str:
    excerpt = text[max(0, start - radius) : min(len(text), end + radius)]
    return " ".join(excerpt.split())


def _node_id(*parts: str) -> str:
    readable = _safe_identifier("-".join(parts[:3]))
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()[:16]
    return f"{readable}-{digest}"


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()
    return safe or "item"
