from __future__ import annotations

from collections import Counter
from collections import defaultdict
import hashlib
import re
from typing import Any

from .applicability_contract_support import strings
from .applicability_decision_arbitration import strong_evidence_count
from .applicability_decision_arbitration import weak_evidence_count
from .evidence_strength import classify_evidence_strength
from .evidence_strength import evidence_strength_for_confidence


def trigger_match(
    *,
    groups: list[list[str]],
    package_nodes: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
    package_results: list[dict[str, Any]],
    include_negative_context: bool = False,
) -> dict[str, Any]:
    if not groups:
        return {
            "matched": False,
            "matched_groups": [],
            "evidence_spans": [],
            "trigger_group_results": [],
            "requires_adjudication": False,
            "adjudication_notes": [],
        }
    searchable_nodes = [
        node
        for node in package_nodes
        if include_negative_context or node.get("confidence_class") != "negative_context"
    ]
    matched_groups = []
    evidence_by_id: dict[str, dict[str, Any]] = {}
    adjudication_notes = []
    group_results = []
    for group in groups:
        group_matched = False
        group_evidence_by_id: dict[str, dict[str, Any]] = {}
        weak_signal_reasons = []
        for node in searchable_nodes:
            node_text = _package_node_text(node)
            if not all(term_in_text(term, node_text) for term in group):
                continue
            group_matched = True
            evidence = _package_evidence_span(node)
            evidence_by_id[evidence["evidence_id"]] = evidence
            group_evidence_by_id[evidence["evidence_id"]] = evidence
            if evidence.get("confidence_class") == "weak_signal":
                note = _weak_signal_note("package fact", node.get("node_id"), evidence)
                adjudication_notes.append(note)
                weak_signal_reasons.append(note)
        for chunk in package_chunks:
            chunk_text = str(chunk.get("text") or "")
            if not all(term_in_text(term, chunk_text) for term in group):
                continue
            group_matched = True
            evidence = _package_chunk_evidence_span(chunk, group)
            evidence_by_id[evidence["evidence_id"]] = evidence
            group_evidence_by_id[evidence["evidence_id"]] = evidence
            if evidence.get("confidence_class") == "weak_signal":
                note = _weak_signal_note("package chunk", chunk.get("chunk_id"), evidence)
                adjudication_notes.append(note)
                weak_signal_reasons.append(note)
        for result in package_results:
            if not _result_matches_trigger_group(result, group):
                continue
            group_matched = True
            evidence = _package_result_span(result)
            evidence_by_id[evidence["evidence_id"]] = evidence
            group_evidence_by_id[evidence["evidence_id"]] = evidence
            if evidence.get("confidence_class") == "weak_signal":
                note = _weak_signal_note("retrieval result", result.get("result_id"), evidence)
                adjudication_notes.append(note)
                weak_signal_reasons.append(note)
        if group_matched:
            matched_groups.append(group)
        group_results.append(
            _trigger_group_diagnostic(
                group=group,
                matched=group_matched,
                evidence=list(group_evidence_by_id.values()),
                weak_signal_reasons=weak_signal_reasons,
            )
        )
    requires_adjudication = bool(adjudication_notes)
    return {
        "matched": bool(matched_groups),
        "matched_groups": matched_groups,
        "evidence_spans": sorted(evidence_by_id.values(), key=lambda item: item["evidence_id"]),
        "trigger_group_results": [
            _finalize_trigger_group_diagnostic(
                result,
                requires_adjudication=requires_adjudication,
            )
            for result in group_results
        ],
        "requires_adjudication": requires_adjudication,
        "adjudication_notes": sorted(set(adjudication_notes)),
    }


def source_library_evidence(
    retrieval_rows: list[dict[str, Any]],
    source_record_ids: list[str],
) -> list[dict[str, Any]]:
    source_record_filter = set(source_record_ids)
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in retrieval_rows:
        for result in row.get("ranked_results") or []:
            if result.get("selected_status") != "selected":
                continue
            if result.get("result_kind") != "source_chunk":
                continue
            source_record_id = str(result.get("source_record_id") or "")
            if source_record_filter and source_record_id not in source_record_filter:
                continue
            evidence_id = str(result.get("result_id") or "")
            evidence_by_id[evidence_id] = {
                "evidence_id": evidence_id,
                "retrieval_trace_id": row.get("retrieval_trace_id"),
                "retrieval_result_id": result.get("result_id"),
                "source_record_id": source_record_id,
                "source_chunk_id": result.get("source_chunk_id"),
                "citation_label": result.get("citation_label"),
                "page_label": result.get("page_label"),
                "char_start": result.get("char_start"),
                "char_end": result.get("char_end"),
                "source_claim_ids": strings([result.get("claim_id")]),
                "text_excerpt": result.get("text_excerpt"),
                "text_hash": result.get("text_hash"),
            }
    return sorted(evidence_by_id.values(), key=lambda item: item["evidence_id"])


def declared_source_library_evidence(
    candidate: dict[str, Any],
    source_record_ids: list[str],
) -> list[dict[str, Any]]:
    if not source_record_ids or not source_evidence_available(candidate):
        return []
    required = candidate.get("required_source_evidence")
    if not isinstance(required, dict):
        required = {}
    chunk_ids = strings(required.get("source_chunk_ids"))
    if not chunk_ids:
        evidence_pairs = [(source_record_id, None) for source_record_id in source_record_ids]
    elif len(source_record_ids) == 1:
        evidence_pairs = [(source_record_ids[0], chunk_id) for chunk_id in chunk_ids]
    else:
        padded_chunk_ids = [*chunk_ids]
        if len(padded_chunk_ids) < len(source_record_ids):
            padded_chunk_ids = [
                *padded_chunk_ids,
                *([None] * (len(source_record_ids) - len(padded_chunk_ids))),
            ]
        evidence_pairs = list(zip(source_record_ids, padded_chunk_ids, strict=False))
    records_by_id = {
        str(record.get("source_record_id") or ""): record
        for record in candidate.get("source_records") or []
        if isinstance(record, dict)
    }
    evidence = []
    for source_record_id, chunk_id in evidence_pairs:
        source_record = records_by_id.get(source_record_id, {})
        evidence_id = _stable_id(
            "declared-source-evidence",
            str(candidate.get("candidate_authority_id") or ""),
            source_record_id,
            str(chunk_id or ""),
        )
        evidence.append(
            {
                "evidence_id": evidence_id,
                "evidence_origin": "authority_universe",
                "retrieval_trace_id": None,
                "retrieval_result_id": None,
                "source_record_id": source_record_id,
                "source_chunk_id": chunk_id,
                "citation_label": source_record.get("citation_label"),
                "page_label": None,
                "char_start": None,
                "char_end": None,
                "source_claim_ids": [],
                "text_excerpt": source_record.get("title"),
                "text_hash": None,
            }
        )
    return evidence


def selected_package_results(retrieval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        result
        for row in retrieval_rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "selected"
        and result.get("result_kind") in {"package_fact", "package_section"}
    ]


def retrieval_lineage(
    retrieval_rows: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    trace_ids = sorted(
        {
            str(row.get("retrieval_trace_id"))
            for row in retrieval_rows
            if row.get("retrieval_trace_id")
        }
    )
    selected = sorted(
        {
            str(result.get("result_id"))
            for row in retrieval_rows
            for result in row.get("ranked_results") or []
            if result.get("selected_status") == "selected" and result.get("result_id")
        }
    )
    rejected = sorted(
        {
            str(result.get("result_id"))
            for row in retrieval_rows
            for result in row.get("ranked_results") or []
            if result.get("selected_status") == "rejected" and result.get("result_id")
        }
    )
    return selected, rejected, trace_ids


def package_fact_nodes(package_fact_graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        node
        for node in package_fact_graph.get("nodes") or []
        if isinstance(node, dict)
        and node.get("node_type") not in {"package_section", "evidence_span"}
    ]


def present_package_values(package_nodes: list[dict[str, Any]]) -> dict[str, set[str]]:
    values: dict[str, set[str]] = defaultdict(set)
    for node in package_nodes:
        if node.get("confidence_class") == "negative_context":
            continue
        node_type = str(node.get("node_type") or "")
        normalized_value = str(node.get("normalized_value") or "")
        if node_type and normalized_value:
            values[node_type].add(normalized_value)
    return values


def source_evidence_available(candidate: dict[str, Any]) -> bool:
    availability = candidate.get("source_evidence_availability")
    if isinstance(availability, dict) and availability.get("available"):
        return True
    required = candidate.get("required_source_evidence")
    if isinstance(required, dict) and not required.get("requires_source_record", True):
        return True
    return False


def term_in_text(term: str, text: str) -> bool:
    raw_term = str(term or "").strip()
    if not raw_term:
        return False
    if len(raw_term) <= 3 and raw_term.replace(".", "").isalnum():
        return bool(
            re.search(
                rf"(?<![A-Za-z0-9]){re.escape(raw_term)}(?![A-Za-z0-9])",
                text,
                flags=re.IGNORECASE,
            )
        )
    normalized_term = raw_term.lower()
    return normalized_term in text.lower()


def _trigger_group_diagnostic(
    *,
    group: list[str],
    matched: bool,
    evidence: list[dict[str, Any]],
    weak_signal_reasons: list[str],
) -> dict[str, Any]:
    evidence_ids = sorted(
        str(item.get("evidence_id") or "") for item in evidence if item.get("evidence_id")
    )
    package_chunk_ids = sorted(
        {
            chunk_id
            for item in evidence
            for chunk_id in strings(item.get("package_chunk_ids"))
        }
    )
    package_fact_node_ids = sorted(
        {
            str(item.get("package_fact_node_id"))
            for item in evidence
            if item.get("package_fact_node_id")
        }
    )
    retrieval_result_ids = sorted(
        {
            str(item.get("retrieval_result_id"))
            for item in evidence
            if item.get("retrieval_result_id")
        }
    )
    return {
        "trigger_group": list(group),
        "matched": matched,
        "diagnostic_treatment": "unmatched",
        "evidence_ids": evidence_ids,
        "package_evidence_ids": sorted(set(evidence_ids) - set(retrieval_result_ids)),
        "package_chunk_ids": package_chunk_ids,
        "package_fact_node_ids": package_fact_node_ids,
        "retrieval_result_ids": retrieval_result_ids,
        "evidence_strength_counts": _evidence_strength_counts(evidence),
        "evidence_strength_class_counts": _evidence_strength_class_counts(evidence),
        "weak_signal_reasons": sorted(set(weak_signal_reasons)),
        "weak_signal_details": _weak_signal_details(evidence),
    }


def _finalize_trigger_group_diagnostic(
    result: dict[str, Any],
    *,
    requires_adjudication: bool,
) -> dict[str, Any]:
    if not result["matched"]:
        treatment = "unmatched"
    else:
        weak_count = weak_evidence_count(result)
        strong_count = strong_evidence_count(result)
        if weak_count and strong_count:
            treatment = "conflicting"
        elif strong_count:
            treatment = "decisive"
        elif weak_count:
            treatment = "weak_only"
        elif requires_adjudication:
            treatment = "auxiliary"
        else:
            treatment = "decisive"
    return {
        **result,
        "diagnostic_treatment": treatment,
    }


def _evidence_strength_counts(evidence: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(item.get("confidence_class") or "observed") for item in evidence)
    return dict(sorted(counts.items()))


def _evidence_strength_class_counts(evidence: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        str(
            (item.get("evidence_strength") or {}).get("strength_class")
            or item.get("confidence_class")
            or "observed"
        )
        for item in evidence
    )
    return dict(sorted(counts.items()))


def _weak_signal_details(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details = []
    for item in evidence:
        if item.get("confidence_class") != "weak_signal":
            continue
        strength = item.get("evidence_strength") or evidence_strength_for_confidence(
            item.get("confidence_class"),
            section_family=item.get("section_family"),
        )
        details.append(
            {
                "evidence_id": item.get("evidence_id"),
                "strength_class": strength.get("strength_class"),
                "reason": strength.get("reason"),
                "matched_phrase": strength.get("matched_phrase"),
                "matched_text": strength.get("matched_text"),
                "evidence_window": strength.get("evidence_window"),
                "section_family": strength.get("section_family") or item.get("section_family"),
            }
        )
    return sorted(
        details,
        key=lambda item: (
            str(item.get("evidence_id") or ""),
            str(item.get("strength_class") or ""),
            str(item.get("reason") or ""),
        ),
    )


def _weak_signal_note(source: str, ref: Any, evidence: dict[str, Any]) -> str:
    strength = evidence.get("evidence_strength") or evidence_strength_for_confidence(
        evidence.get("confidence_class"),
        section_family=evidence.get("section_family"),
    )
    note = (
        f"weak {source} signal for {ref}: "
        f"{strength.get('strength_class') or 'weak_signal'}/"
        f"{strength.get('reason') or 'weak_signal'}"
    )
    if strength.get("matched_phrase"):
        note = f"{note} matched `{strength['matched_phrase']}`"
    return note


def _package_evidence_span(node: dict[str, Any]) -> dict[str, Any]:
    evidence_strength = node.get("evidence_strength") or evidence_strength_for_confidence(
        node.get("confidence_class"),
        section_family=node.get("section_family"),
    )
    return {
        "evidence_id": str(node.get("node_id") or ""),
        "package_fact_node_id": node.get("node_id"),
        "package_chunk_ids": strings(node.get("package_chunk_ids")),
        "citation_label": node.get("citation_label"),
        "section_family": node.get("section_family"),
        "page_label": node.get("page_label"),
        "char_start": node.get("char_start"),
        "char_end": node.get("char_end"),
        "matched_terms": strings([node.get("raw_value"), node.get("normalized_value")]),
        "text_snippet": node.get("raw_value") or node.get("label"),
        "confidence_class": node.get("confidence_class"),
        "evidence_strength": evidence_strength,
        "evidence_span_ids": strings(node.get("evidence_span_ids")),
        "text_hash": node.get("text_hash") or node.get("content_sha256"),
    }


def _package_result_span(result: dict[str, Any]) -> dict[str, Any]:
    provenance = result.get("provenance") or {}
    evidence_strength = provenance.get("evidence_strength") or evidence_strength_for_confidence(
        provenance.get("confidence_class"),
        section_family=result.get("section_family"),
    )
    return {
        "evidence_id": str(result.get("result_id") or ""),
        "retrieval_result_id": result.get("result_id"),
        "package_fact_node_id": result.get("package_fact_node_id"),
        "package_chunk_ids": strings([result.get("package_chunk_id")]),
        "citation_label": result.get("citation_label"),
        "section_family": result.get("section_family"),
        "page_label": result.get("page_label"),
        "char_start": result.get("char_start"),
        "char_end": result.get("char_end"),
        "matched_terms": strings(result.get("matched_terms")),
        "text_snippet": result.get("text_excerpt"),
        "confidence_class": provenance.get("confidence_class"),
        "evidence_strength": evidence_strength,
        "evidence_span_ids": strings(provenance.get("evidence_span_ids")),
        "text_hash": result.get("text_hash"),
    }


def _package_chunk_evidence_span(chunk: dict[str, Any], group: list[str]) -> dict[str, Any]:
    text = str(chunk.get("text") or "")
    first_match = _first_trigger_match(text, group)
    chunk_start = first_match[1] if first_match else 0
    chunk_end = first_match[2] if first_match else min(len(text), 200)
    section_family = _section_family_from_chunk(chunk)
    evidence_strength = classify_evidence_strength(
        text=text,
        start=chunk_start,
        end=chunk_end,
        matched_text=first_match[0] if first_match else None,
        section_family=section_family,
    )
    absolute_start = _absolute_offset(chunk.get("char_start"), chunk_start)
    absolute_end = _absolute_offset(chunk.get("char_start"), chunk_end)
    evidence_id = _stable_id(
        "package-trigger-span",
        str(chunk.get("chunk_id") or ""),
        str(chunk_start),
        str(chunk_end),
        hashlib.sha256("|".join(group).encode("utf-8")).hexdigest(),
    )
    return {
        "evidence_id": evidence_id,
        "package_fact_node_id": None,
        "package_chunk_ids": strings([chunk.get("chunk_id")]),
        "citation_label": chunk.get("citation_label"),
        "section_family": section_family,
        "page_label": _page_label(chunk),
        "char_start": absolute_start,
        "char_end": absolute_end,
        "matched_terms": group,
        "text_snippet": _context_excerpt(text, chunk_start, chunk_end),
        "confidence_class": evidence_strength["confidence_class"],
        "evidence_strength": evidence_strength,
        "evidence_span_ids": [],
        "text_hash": chunk.get("content_sha256"),
    }


def _first_trigger_match(text: str, group: list[str]) -> tuple[str, int, int] | None:
    lower_text = text.lower()
    matches = []
    for term in group:
        normalized = term.lower()
        index = lower_text.find(normalized)
        if index >= 0:
            matches.append((term, index, index + len(term)))
    if not matches:
        return None
    return sorted(matches, key=lambda item: item[1])[0]


def _package_node_text(node: dict[str, Any]) -> str:
    return " ".join(
        str(value or "")
        for value in (
            node.get("label"),
            node.get("raw_value"),
            node.get("normalized_value"),
            node.get("fact_subtype"),
            node.get("section_family"),
            node.get("context_excerpt"),
            node.get("matched_text"),
        )
    )


def _result_matches_trigger_group(result: dict[str, Any], group: list[str]) -> bool:
    matched_terms = " ".join(strings(result.get("matched_terms")))
    result_text = " ".join(
        str(value or "")
        for value in (
            matched_terms,
            result.get("text_excerpt"),
            (result.get("provenance") or {}).get("normalized_value"),
            (result.get("provenance") or {}).get("fact_subtype"),
        )
    )
    return all(term_in_text(term, result_text) for term in group)


def _context_excerpt(text: str, start: int, end: int, radius: int = 160) -> str:
    excerpt_start = max(0, start - radius)
    excerpt_end = min(len(text), end + radius)
    prefix = "..." if excerpt_start > 0 else ""
    suffix = "..." if excerpt_end < len(text) else ""
    return f"{prefix}{text[excerpt_start:excerpt_end].strip()}{suffix}"


def _absolute_offset(base: Any, offset: int) -> int:
    try:
        return int(base) + offset
    except (TypeError, ValueError):
        return offset


def _page_label(chunk: dict[str, Any]) -> str | None:
    value = chunk.get("page_label") or chunk.get("page")
    return str(value) if value is not None else None


def _section_family_from_chunk(chunk: dict[str, Any]) -> str | None:
    values = " ".join(str(chunk.get(key) or "").lower() for key in ("section", "heading"))
    if "no action" in values:
        return "no_action"
    if "cumulative" in values:
        return "cumulative_effects"
    if "purpose" in values or "need" in values:
        return "purpose_need"
    if "affected" in values or "environment" in values:
        return "affected_environment"
    if "consequence" in values or "effect" in values:
        return "environmental_consequences"
    if "alternative" in values:
        return "alternatives"
    if "public" in values or "scoping" in values:
        return "public_involvement"
    if "decision" in values or "finding" in values:
        return "finding_decision"
    return None


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
