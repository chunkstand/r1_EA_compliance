from __future__ import annotations

import re

from .forest_plan_components_common import _compact, _finding_provenance, _normalized_component_text, _utc_now
from .forest_plan_components_models import COMPONENT_CODE_NUMBER_RE, FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION, LEADING_COMPONENT_LABEL_RE, PLAN_CONSISTENCY_YES_NO


def _component_package_determination(
    *,
    component: dict,
    package_chunks: list[dict],
) -> dict | None:
    component_key = _component_reference_key(component)
    if not component_key:
        return None
    pattern = _component_key_pattern(component_key)
    candidates = []
    for index, chunk in enumerate(package_chunks):
        window_chunk = _plan_consistency_chunk_window(package_chunks, index)
        text = str(window_chunk.get("text") or "")
        for match in pattern.finditer(text):
            row = _plan_consistency_row(
                chunk=window_chunk,
                text=text,
                match_start=match.start(),
                match_end=match.end(),
                component_key=component_key,
            )
            if row is not None:
                candidates.append(row)
            row = _plan_consistency_plain_text_row(
                chunk=window_chunk,
                text=text,
                match_start=match.start(),
                match_end=match.end(),
                component=component,
                component_key=component_key,
            )
            if row is not None:
                candidates.append(row)
        if not candidates:
            row = _plan_consistency_text_row(
                chunk=window_chunk,
                text=text,
                component=component,
                component_key=component_key,
            )
            if row is not None:
                candidates.append(row)
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            str(item.get("source_record_id") or ""),
            int(item.get("provenance", {}).get("char_start") or 0),
        )
    )
    result = dict(candidates[0])
    result["rank"] = 1
    return result


def _plan_consistency_chunk_window(
    package_chunks: list[dict],
    index: int,
    *,
    lookahead: int = 4,
) -> dict:
    chunk = dict(package_chunks[index])
    title = str(chunk.get("title") or "")
    if "plan consistency table" not in title.lower():
        return chunk
    parts = [str(chunk.get("text") or "")]
    last_chunk = chunk
    for next_chunk in package_chunks[index + 1 : index + 1 + lookahead]:
        if not _same_package_document(chunk, next_chunk):
            break
        parts.append(str(next_chunk.get("text") or ""))
        last_chunk = next_chunk
    if len(parts) == 1:
        return chunk
    window = dict(chunk)
    window["text"] = "\n".join(parts)
    window["char_end"] = last_chunk.get("char_end", chunk.get("char_end"))
    window["chunk_window_ids"] = [
        str(item.get("chunk_id") or "")
        for item in package_chunks[index : index + len(parts)]
        if str(item.get("chunk_id") or "").strip()
    ]
    return window


def _same_package_document(left: dict, right: dict) -> bool:
    return all(
        str(left.get(field) or "") == str(right.get(field) or "")
        for field in ("source_record_id", "artifact_sha256", "title")
    )


def _component_reference_key(component: dict) -> str | None:
    match = COMPONENT_CODE_NUMBER_RE.search(str(component.get("component_text") or ""))
    if not match:
        return None
    return f"{match.group('code')}-{match.group('number')}"


def _component_key_pattern(component_key: str) -> re.Pattern[str]:
    prefix, separator, number = component_key.rpartition("-")
    if not separator or not prefix or not number:
        return re.compile(rf"(?<![A-Za-z0-9]){re.escape(component_key)}(?![A-Za-z0-9])")
    prefix_pattern = re.escape(prefix).replace(r"\-", r"\s*-\s*")
    number_pattern = re.escape(number)
    return re.compile(
        rf"(?<![A-Za-z0-9]){prefix_pattern}\s*-?\s*{number_pattern}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


def _plan_consistency_row(
    *,
    chunk: dict,
    text: str,
    match_start: int,
    match_end: int,
    component_key: str,
) -> dict | None:
    row_start = text.rfind("|", 0, match_start)
    if row_start < 0:
        row_start = max(0, match_start - 120)
    window = text[row_start : min(len(text), match_end + 5000)]
    cells = [cell.strip() for cell in window.split("|")]
    component_key_fingerprint = _component_key_fingerprint(component_key)
    key_index = next(
        (
            index
            for index, cell in enumerate(cells)
            if _cell_matches_component_key(cell, component_key_fingerprint)
        ),
        None,
    )
    if key_index is None:
        return None
    applies_index = next(
        (
            index
            for index in range(key_index + 1, min(len(cells), key_index + 6))
            if _yes_no_cell(cells[index]) in PLAN_CONSISTENCY_YES_NO
        ),
        None,
    )
    if applies_index is None or len(cells) <= applies_index + 1:
        return None
    applies = _yes_no_cell(cells[applies_index])
    if applies not in PLAN_CONSISTENCY_YES_NO:
        return None
    explanation = _compact(cells[applies_index + 1], limit=1200)
    component_text = _compact(
        " ".join(_component_text_cells(cells[key_index], cells[key_index + 1 : applies_index])),
        limit=1200,
    )
    row_cells = cells[key_index : applies_index + 2]
    row_text = " | ".join(cell for cell in row_cells if cell)
    row_offset = window.find(cells[key_index])
    if row_offset < 0:
        row_offset = match_start - row_start
    span_start = row_start + row_offset
    span_end = min(len(text), span_start + len(row_text))
    return _package_determination_result(
        chunk=chunk,
        component_key=component_key,
        component_applies=applies,
        component_text=component_text,
        explanation=explanation,
        span_start=span_start,
        span_end=span_end,
        row_text=row_text,
    )


def _plan_consistency_text_row(
    *,
    chunk: dict,
    text: str,
    component: dict,
    component_key: str,
) -> dict | None:
    if "plan consistency table" not in str(chunk.get("title") or "").lower():
        return None
    component_text = _component_body_text(str(component.get("component_text") or ""))
    if not component_text:
        return None
    cells = [cell.strip() for cell in text.split("|")]
    component_key_fingerprint = _component_key_fingerprint(component_key)
    component_key_prefix_fingerprint = _component_key_fingerprint(
        component_key.rpartition("-")[0]
    )
    for index in range(0, max(0, len(cells) - 3)):
        key_cell = cells[index]
        candidate_component_text = _compact(cells[index + 1], limit=1200)
        applies = _yes_no_cell(cells[index + 2])
        key_fingerprint = _component_key_fingerprint(key_cell)
        key_matches = (
            not key_cell
            or key_fingerprint == component_key_fingerprint
            or (
                bool(component_key_prefix_fingerprint)
                and key_fingerprint == component_key_prefix_fingerprint
            )
        )
        if not key_matches or applies not in PLAN_CONSISTENCY_YES_NO:
            continue
        if not _component_text_matches(candidate_component_text, component_text):
            continue
        explanation = _compact(cells[index + 3], limit=1200)
        row_cells = cells[index : index + 4]
        row_text = " | ".join(cell for cell in row_cells if cell)
        span_start = text.find(cells[index + 1])
        if span_start < 0:
            span_start = 0
        span_end = min(len(text), span_start + len(row_text))
        return _package_determination_result(
            chunk=chunk,
            component_key=component_key,
            component_applies=applies,
            component_text=candidate_component_text,
            explanation=explanation,
            span_start=span_start,
            span_end=span_end,
            row_text=row_text,
        )
    return None


def _plan_consistency_plain_text_row(
    *,
    chunk: dict,
    text: str,
    match_start: int,
    match_end: int,
    component: dict,
    component_key: str,
) -> dict | None:
    if "plan consistency table" not in str(chunk.get("title") or "").lower():
        return None
    window = text[match_start : min(len(text), match_end + 3000)]
    if "|" in window[:500]:
        return None
    applies_match = re.search(
        r"\b(?P<applies>yes|no)\b\s*(?:[-\u2013\u2014]|\b(?:this|the|no)\b)",
        window,
        re.IGNORECASE,
    )
    if not applies_match:
        return None
    applies = _yes_no_cell(applies_match.group("applies"))
    if applies not in PLAN_CONSISTENCY_YES_NO:
        return None
    component_text = _compact(window[match_end - match_start : applies_match.start()], limit=1200)
    target_text = _component_body_text(str(component.get("component_text") or ""))
    if component_text and target_text and not _component_text_matches(component_text, target_text):
        return None
    tail = window[applies_match.end() :]
    next_row = re.search(
        r"\s(?:[A-Z]{2,4}-(?:DC|GO|OBJ|STD|GDL|SUIT)-[A-Z0-9]+-?\s*[0-9]{2}|##\s+)",
        tail,
    )
    explanation_end = applies_match.end() + (next_row.start() if next_row else len(tail))
    explanation = _compact(window[applies_match.end() : explanation_end], limit=1200)
    row_text = _compact(window[:explanation_end], limit=2400)
    return _package_determination_result(
        chunk=chunk,
        component_key=component_key,
        component_applies=applies,
        component_text=component_text,
        explanation=explanation,
        span_start=match_start,
        span_end=min(len(text), match_start + len(row_text)),
        row_text=row_text,
    )


def _component_body_text(component_text: str) -> str:
    return _normalized_component_text(LEADING_COMPONENT_LABEL_RE.sub("", component_text))


def _component_text_matches(candidate: str, target: str) -> bool:
    candidate_text = _normalized_component_text(candidate)
    if not candidate_text or not target:
        return False
    candidate_tokens = candidate_text.split()
    target_tokens = target.split()
    if len(candidate_tokens) >= 6 and candidate_tokens == target_tokens[: len(candidate_tokens)]:
        return True
    if len(candidate_tokens) >= 6 and len(target_tokens) >= len(candidate_tokens):
        candidate_stem = candidate_tokens[-1].rstrip("-")
        target_token = target_tokens[len(candidate_tokens) - 1]
        if (
            candidate_tokens[:-1] == target_tokens[: len(candidate_tokens) - 1]
            and candidate_stem
            and target_token.startswith(candidate_stem)
        ):
            return True
    if len(target_tokens) >= 6 and target_tokens == candidate_tokens[: len(target_tokens)]:
        return True
    candidate_prefix = " ".join(candidate_tokens[:18])
    target_prefix = " ".join(target_tokens[:18])
    return bool(candidate_prefix and target_prefix and candidate_prefix == target_prefix)


def _component_key_fingerprint(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value).upper())


def _cell_matches_component_key(cell: str, component_key_fingerprint: str) -> bool:
    cell_fingerprint = _component_key_fingerprint(cell)
    return bool(
        cell_fingerprint
        and (
            cell_fingerprint == component_key_fingerprint
            or cell_fingerprint.startswith(component_key_fingerprint)
        )
    )


def _component_text_cells(key_cell: str, cells: list[str]) -> list[str]:
    values = []
    key_match = re.match(
        r"\s*[A-Za-z]{2,4}\s*-\s*(?:DC|GO|OBJ|STD|GDL|SUIT)\s*-\s*"
        r"[A-Za-z0-9]+\s*-?\s*[0-9]{2}\s*(?P<tail>.*)",
        key_cell,
        flags=re.IGNORECASE,
    )
    if key_match and key_match.group("tail").strip():
        values.append(key_match.group("tail").strip())
    values.extend(cell for cell in cells if cell.strip())
    return values


def _yes_no_cell(value: str) -> str | None:
    normalized = re.sub(r"[^A-Za-z]+", " ", value).strip().lower()
    if normalized in PLAN_CONSISTENCY_YES_NO:
        return normalized
    return None


def _package_determination_result(
    *,
    chunk: dict,
    component_key: str,
    component_applies: str,
    component_text: str,
    explanation: str,
    span_start: int,
    span_end: int,
    row_text: str,
) -> dict:
    source_chunk_start = int(chunk.get("char_start") or 0)
    return {
        "rank": 1,
        "score": 1.0,
        "chunk_id": chunk["chunk_id"],
        "source_record_id": chunk["source_record_id"],
        "title": chunk["title"],
        "citation_label": chunk["citation_label"],
        "matched_terms": [component_key, component_applies],
        "component_key": component_key,
        "component_applies": component_applies,
        "determination_source": "ea_plan_consistency_table",
        "determination_explanation": explanation,
        "determination_component_text": component_text,
        "review_section": _package_review_section(
            chunk=chunk,
            explanation=explanation,
        ),
        "evidence_span": {
            "text": row_text,
            "chunk_char_start": span_start,
            "chunk_char_end": span_end,
            "source_char_start": source_chunk_start + span_start,
            "source_char_end": source_chunk_start + span_end,
        },
        "provenance": {
            "artifact_sha256": chunk["artifact_sha256"],
            "artifact_path": chunk["artifact_path"],
            "parser_name": chunk["parser_name"],
            "parser_version": chunk["parser_version"],
            "extracted_at": chunk["extracted_at"],
            "source_text_path": chunk["source_text_path"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
            "chunk_window_ids": chunk.get("chunk_window_ids", [chunk.get("chunk_id")]),
            "page": chunk["page"],
            "section": chunk["section"],
            "heading": chunk["heading"],
            "content_sha256": chunk["content_sha256"],
        },
    }


def _package_review_section(*, chunk: dict, explanation: str) -> str:
    explicit_section = _explicit_ea_section(explanation)
    if explicit_section:
        return explicit_section
    for field in ("section", "heading", "title"):
        value = str(chunk.get(field) or "").strip()
        if value:
            return value
    return "EA package"


def _explicit_ea_section(text: str) -> str | None:
    match = re.search(r"\bEA(?:,)?\s+section\s+([0-9]+(?:\.[0-9]+)*)", text, re.IGNORECASE)
    if match:
        return f"EA section {match.group(1)}"
    return None


def _package_determination_basis(determination: dict | None) -> dict | None:
    if not determination:
        return None
    return {
        "component_key": determination.get("component_key"),
        "component_applies": determination.get("component_applies"),
        "determination_source": determination.get("determination_source"),
        "determination_explanation": determination.get("determination_explanation"),
        "review_section": determination.get("review_section"),
        "citation_label": determination.get("citation_label"),
        "chunk_id": determination.get("chunk_id"),
        "source_record_id": determination.get("source_record_id"),
    }


def _merge_package_evidence(
    preferred: list[dict],
    fallback: list[dict],
    *,
    limit: int,
) -> list[dict]:
    merged = []
    seen = set()
    for evidence in [*preferred, *fallback]:
        key = (
            evidence.get("chunk_id"),
            evidence.get("evidence_span", {}).get("source_char_start"),
            evidence.get("evidence_span", {}).get("source_char_end"),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(evidence)
        if len(merged) >= limit:
            break
    return merged


def _context_matches_component(context: dict, component: dict) -> bool:
    matched = _matched_context(context, component)
    return all(
        (
            not component[field]
            or bool(matched[matched_field])
        )
        for field, matched_field in (
            ("geographic_area_ids", "geographic_area_ids"),
            ("management_area_ids", "management_area_ids"),
            ("overlay_ids", "overlay_ids"),
        )
    )


def _matched_context(context: dict, component: dict) -> dict:
    geographic_area_ids = _resolved_entry_ids(context, "geographic_areas")
    management_area_ids = _resolved_entry_ids(context, "management_areas")
    overlay_ids = _resolved_entry_ids(context, "overlays")
    return {
        "geographic_area_ids": sorted(set(component["geographic_area_ids"]) & geographic_area_ids),
        "management_area_ids": sorted(set(component["management_area_ids"]) & management_area_ids),
        "overlay_ids": sorted(set(component["overlay_ids"]) & overlay_ids),
    }


def _resolved_entry_ids(context: dict, key: str) -> set[str]:
    return {str(entry.get("entry_id")) for entry in context.get(key, []) if entry.get("entry_id")}


def _reviewer_resolution_items_for_finding(
    *,
    review_id: str,
    component: dict,
    finding_status: str,
    applicability_status: str,
    rationale: str,
    source_set_id: str | None,
    source_set_matches: bool,
    plan_source_evidence: list[dict],
    package_evidence: list[dict],
) -> list[dict]:
    if finding_status in {"supported", "not_applicable"}:
        return []
    if not source_set_matches:
        reason = "component_source_set_drift"
        message = "Refresh or rebuild the component inventory for the active source set."
        severity = "high"
    elif not plan_source_evidence:
        reason = "missing_plan_source_evidence"
        message = "Verify the component against current source-library chunks before relying on it."
        severity = "high"
    elif not package_evidence:
        reason = "missing_package_evidence"
        message = "Review the EA package for evidence addressing the applicable plan component."
        severity = "medium"
    else:
        reason = "needs_reviewer_resolution"
        message = rationale
        severity = "medium"
    return [
        {
            "item_id": f"{component['component_id']}-{reason}",
            "review_id": review_id,
            "finding_id": f"{component['component_id']}-finding",
            "component_id": component["component_id"],
            "component_key": _component_reference_key(component),
            "component_type": component["component_type"],
            "component_text": component["component_text"],
            "component_context": {
                "section_heading": component.get("section_heading"),
                "geographic_area_ids": component.get("geographic_area_ids", []),
                "management_area_ids": component.get("management_area_ids", []),
                "overlay_ids": component.get("overlay_ids", []),
                "resource_topics": component.get("resource_topics", []),
                "activity_tags": component.get("activity_tags", []),
            },
            "package_evidence_terms": component.get("package_evidence_terms", []),
            "reason": reason,
            "severity": severity,
            "message": message,
            "finding_status": finding_status,
            "applicability_status": applicability_status,
            "source_set_id": source_set_id,
            "component_source_set_id": component["source_set_id"],
            "provenance": _finding_provenance(
                review_id=review_id,
                component=component,
                source_set_id=source_set_id,
                finding_status=finding_status,
            ),
        }
    ]


def _reviewer_resolution_queue(
    *,
    review_id: str,
    source_set_id: str | None,
    findings: list[dict],
) -> dict:
    items = [
        item
        for finding in findings
        for item in finding.get("reviewer_resolution_items", [])
    ]
    return {
        "schema_version": FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "item_count": len(items),
        "items": items,
    }
