from __future__ import annotations

import re


def _compiled_alias_pattern(alias: str) -> tuple[re.Pattern[str], bool]:
    case_sensitive = _is_case_sensitive_alias(alias)
    pattern_text = alias if case_sensitive else alias.lower()
    escaped = re.escape(pattern_text).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])"), case_sensitive

def _term_found(text: str, term: str) -> bool:
    pattern, case_sensitive = _compiled_alias_pattern(term)
    search_text = text if case_sensitive else text.lower()
    return bool(pattern.search(search_text))

def _is_case_sensitive_alias(alias: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9]", "", alias)
    if len(compact) < 2 or not any(char.isalpha() for char in compact):
        return False
    return compact.upper() == compact and any(char.isupper() for char in alias)


def _location_evidence_role(evidence: dict) -> str:
    if _is_negative_location_context(evidence):
        return "negative_location"
    decision_text = _location_context_text(evidence)
    if _has_incidental_forest_unit_context(decision_text):
        return "background_reference"
    if _is_affirmative_location_context(evidence) or _is_header_project_location_context(evidence):
        return "project_location"
    if evidence.get("category") in {"district", "forest_unit"}:
        return "background_reference"
    return "generic_mention"

def _is_negative_location_context(evidence: dict) -> bool:
    text = _location_decision_window(evidence)
    decision_text = _plan_consistency_decision_text(evidence)
    candidate_texts = [text, decision_text]
    scope_text = _scope_decision_text(evidence)
    if (
        _is_plan_consistency_table_evidence(evidence)
        and not _has_positive_plan_consistency_determination(scope_text)
    ):
        candidate_texts.append(scope_text)
    combined_text = " ".join(candidate_texts)
    if _has_outside_entry_context(evidence, combined_text):
        return True
    if _has_negative_plan_consistency_determination(decision_text):
        return True
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
        "no designated wilderness in the project area or affected by the project",
        "no research natural areas in the project area",
        "no research natural areas in the project area or affected by the project",
    )
    return any(
        phrase in candidate
        for phrase in negative_phrases
        for candidate in candidate_texts
    ) or bool(
        re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b(?:in\s+the\s+project\s+area|"
            r"affected\s+by\s+(?:the|this)\s+project)\b",
            combined_text,
        )
        or _has_no_entry_location_context(evidence, combined_text)
    )

def _plan_consistency_decision_text(evidence: dict) -> str:
    scope_text = _scope_decision_text(evidence)
    if "plan consistency table" not in scope_text:
        return ""
    alias = str(evidence.get("matched_alias") or "").lower()
    if not alias:
        return scope_text
    pattern, _case_sensitive = _compiled_alias_pattern(alias)
    match = pattern.search(scope_text)
    if match is None:
        return scope_text
    start = max(
        0,
        max(
            scope_text.rfind(" | | ", 0, match.start()),
            scope_text.rfind("\n\n", 0, match.start()),
        ),
    )
    end_candidates = [
        index
        for marker in (" | | ", "\n\n")
        if (index := scope_text.find(marker, match.end())) >= 0
    ]
    end = min(end_candidates) if end_candidates else min(len(scope_text), match.end() + 900)
    return scope_text[start:end]

def _has_negative_plan_consistency_determination(text: str) -> bool:
    if not text:
        return False
    has_no_determination = bool(
        re.search(r"\|\s*no\s*\|", text)
        or re.search(r"(?:^|\n)\s*no\s*(?:\n|-)", text)
    )
    if not has_no_determination:
        return False
    return bool(
        re.search(
            r"\b(?:not\s+part\s+of|outside(?:\s+of)?|not\s+in|not\s+within)\s+"
            r"(?:the\s+)?project\s+area\b",
            text,
        )
        or re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b(?:in\s+the\s+project\s+area|"
            r"affected\s+by\s+(?:the|this)\s+project)\b",
            text,
        )
        or re.search(
            r"\bproject\s+does\s+not\b.{0,180}\b(?:include|contain|affect|pertain\s+to|"
            r"involve)\b",
            text,
        )
    )

def _has_positive_plan_consistency_determination(text: str) -> bool:
    if not text:
        return False
    return bool(
        re.search(r"\|\s*yes\s*\|", text)
        or re.search(r"(?:^|\n)\s*yes\s*(?:\n|-)", text)
    )

def _has_no_entry_location_context(evidence: dict, text: str) -> bool:
    for term in _entry_text_terms(evidence):
        term_pattern = _term_pattern(term)
        if re.search(
            rf"\b(?:there\s+(?:are|is)\s+no|no)\b.{{0,240}}\b{term_pattern}\b"
            rf".{{0,160}}\b(?:in|near|within)\b.{{0,120}}\b"
            rf"(?:parcels?|lands?|project\s+area|area)\b",
            text,
        ):
            return True
    return False

def _has_outside_entry_context(evidence: dict, text: str) -> bool:
    for term in _entry_text_terms(evidence):
        if re.search(rf"\boutside(?:\s+of)?\s+{_term_pattern(term)}\b", text):
            return True
    return False

def _entry_text_terms(evidence: dict) -> list[str]:
    return _dedupe_text_terms(
        [
            str(evidence.get("matched_alias") or "").strip().lower(),
            str(evidence.get("name") or "").strip().lower(),
        ]
    )

def _dedupe_text_terms(terms: list[str]) -> list[str]:
    deduped = []
    for term in terms:
        if term and term not in deduped:
            deduped.append(term)
    return deduped

def _term_pattern(term: str) -> str:
    term_pattern = re.escape(term).replace(r"\ ", r"\s+")
    if not term.endswith("s"):
        term_pattern = f"{term_pattern}s?"
    return term_pattern

def _is_affirmative_location_context(evidence: dict) -> bool:
    if _is_negative_location_context(evidence):
        return False
    text = " ".join([_location_decision_window(evidence), _scope_decision_text(evidence)])
    return bool(
        re.search(
            r"\b(?:project\s+area|project|action|trail\s+work|parcels?|lands?|it)\b.{0,160}"
            r"\b(?:includes?|is|are|within|cross(?:es)?|located|incorporated)\b.{0,220}"
            r"\b(?:on|in|within|into|across|cross(?:es)?)\b",
            text,
        )
        or re.search(
            r"\b(?:will|would)\s+(?:also\s+)?be\s+(?:incorporated|located)\s+"
            r"(?:on|in|within|into)\b",
            text,
        )
    )

def _is_header_project_location_context(evidence: dict) -> bool:
    if evidence.get("category") not in {"district", "forest_unit"}:
        return False
    text = _location_context_text(evidence)
    if _has_incidental_forest_unit_context(text):
        return False
    has_header_marker = "##" in text or "|" in text
    has_admin_unit = "ranger district" in text or "national forest" in text
    has_document_context = bool(
        re.search(
            r"\b(?:project|proposed\s+action|environmental\s+assessment|analysis|"
            r"specialist\s+report|compliance\s+statement)\b",
            text,
        )
    )
    if has_header_marker and has_admin_unit and has_document_context:
        return True
    return bool(
        re.search(
            r"\b(?:project|analysis|environmental\s+assessment)\b.{0,240}"
            r"\b(?:ranger\s+district|national\s+forest)\b",
            text,
        )
    )

def _location_context_text(evidence: dict) -> str:
    provenance = evidence.get("provenance") or {}
    return " ".join(
        str(part)
        for part in (
            _location_decision_window(evidence),
            provenance.get("section"),
            provenance.get("heading"),
        )
        if part
    ).lower()

def _location_decision_window(evidence: dict) -> str:
    span = evidence.get("evidence_span") or {}
    text = str(span.get("text") or "").lower()
    alias = str(evidence.get("matched_alias") or "").lower()
    if not text or not alias:
        return _scope_decision_text(evidence)
    pattern, _case_sensitive = _compiled_alias_pattern(alias)
    match = pattern.search(text)
    if match is None:
        return text
    next_pipe = text.find("|", match.end())
    next_sentence_boundary = _nearest_location_boundary_after(text, match.end())
    if next_pipe >= 0 and (next_sentence_boundary is None or next_pipe < next_sentence_boundary):
        start = _location_boundary_before(text, match.start())
        end = _location_boundary_after(text, match.end())
        return text[start:end]
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    if "\n" in text and "|" in line:
        return line
    sentence_start_candidates = [
        text.rfind(boundary, 0, match.start()) for boundary in (".", ";", "\n")
    ]
    sentence_start = max(sentence_start_candidates)
    start = 0 if sentence_start < 0 else sentence_start + 1
    sentence_end_candidates = [
        index
        for boundary in (".", ";", "\n")
        if (index := text.find(boundary, match.end())) >= 0
    ]
    end = min(sentence_end_candidates) if sentence_end_candidates else len(text)
    return text[start:end]

def _nearest_location_boundary_after(text: str, start: int) -> int | None:
    candidates = [
        index for boundary in (".", ";", "\n") if (index := text.find(boundary, start)) >= 0
    ]
    return min(candidates) if candidates else None

def _location_boundary_before(text: str, start: int) -> int:
    boundary = max(text.rfind(char, 0, start) for char in (".", ";", "\n"))
    return 0 if boundary < 0 else boundary + 1

def _location_boundary_after(text: str, start: int) -> int:
    boundary = _nearest_location_boundary_after(text, start)
    return len(text) if boundary is None else boundary

def _scope_decision_text(evidence: dict) -> str:
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    parts = [
        evidence.get("title"),
        span.get("text"),
        provenance.get("section"),
        provenance.get("heading"),
        provenance.get("artifact_path"),
    ]
    return " ".join(str(part) for part in parts if part).lower()

def _is_plan_consistency_table_evidence(evidence: dict) -> bool:
    return "plan consistency table" in _scope_decision_text(evidence)

def _has_incidental_forest_unit_context(text: str) -> bool:
    incidental_phrases = (
        "references",
        "literature cited",
        "literature/ science considered",
        "literature/science considered",
        "science considered",
        "bibliography",
        "works cited",
        "reference list",
        "forest service files",
        "coordinates stewardship",
        "for example, the",
        "other forests in the area",
        "neighboring national forests",
        "neither forest has planned projects",
        "northern portion",
        "southern portion",
        "not likely to use affected parcels",
    )
    if any(phrase in text for phrase in incidental_phrases):
        return True
    reference_like_patterns = (
        r"\b\d{4}[a-z]?\.\s+[^.]{0,180}\bnational forest\b",
        r"\busda forest service\.\s+\d{4}[a-z]?\b",
        r"\bu\.s\. department of agriculture\b[^.]{0,180}\b\d{4}[a-z]?\b",
        r"\bpublication\s+#?[a-z0-9-]+\b[^.]{0,180}\bnational forest\b",
        r"\bnational forest\b[^.]{0,140}\b\d+\s*pp\b",
    )
    return any(re.search(pattern, text) for pattern in reference_like_patterns)
