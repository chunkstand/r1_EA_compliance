from __future__ import annotations

import re

from .forest_plan_components_common import _compact, _safe_identifier
from .forest_plan_components_models import MODAL_BOUNDARY_RE


LEGACY_LABEL_BY_HEADING = {
    "desired condition": "Desired Conditions",
    "desired conditions": "Desired Conditions",
    "goal": "Goal",
    "goals": "Goal",
    "guideline": "Guideline",
    "guidelines": "Guideline",
    "monitoring": "Monitoring",
    "objective": "Objective",
    "objectives": "Objective",
    "standard": "Standard",
    "standards": "Standard",
    "suitability": "Suitability",
}

LEGACY_PRACTICE_HEADING_RE = re.compile(
    r"\b(?P<heading>[A-Z][A-Za-z/& -]{2,80}?\s+Practices?|Site\s+Administration|"
    r"Management\s+Direction|Management\s+Area\s+Direction)\s*:",
)
LEGACY_COMPONENT_HEADING_RE = re.compile(
    r"\b(?P<label>Desired\s+Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|"
    r"Standards?|Suitability)\b\s*:?",
    re.IGNORECASE,
)
LEGACY_MANAGEMENT_AREA_RE = re.compile(
    r"\bMANAG[A-Za-z~]*\s+AR[A-Za-z~]*\s*[.:~\s]*(?P<identifier>[0-9]{1,3}[A-Za-z]?|[IVXLC]{1,6})\b",
    re.IGNORECASE,
)
LEGACY_MA_TOKEN_RE = re.compile(r"\bMA\s*(?P<identifier>[0-9]{1,3}[A-Za-z]?|[IVXLC]{1,6})\b")
LEGACY_NUMBERED_DIRECTIVE_RE = re.compile(
    r"(?<![A-Za-z0-9])(?P<number>[0-9]{1,3}|[IVXLC]{1,6})\s*[.):]\s+(?=[A-Z])",
)
LEGACY_STOP_HEADING_RE = re.compile(
    r"\b(?:Schedule\s+of\s+Management\s+Practices|Monitoring\s+and\s+Evaluation\s+Requirements|"
    r"Table\s+[0-9IVXLC.]+|TABLE\s+OF\s+CONTENTS)\b",
    re.IGNORECASE,
)
LEGACY_SECTION_TERMINATOR_RE = re.compile(
    r"\b(?:[A-Z]\.\s+)?(?:Schedule\s+of\s+Management\s+Practices|"
    r"Monitoring\s+and\s+Evaluation\s+Requirements)\b",
    re.IGNORECASE,
)
LEGACY_DIRECTION_CUE_RE = re.compile(
    r"\b(?:forest-wide\s+management\s+direction|management\s+standards|management\s+direction|"
    r"management\s+area\s+direction|goals,\s+management\s+standards)\b",
    re.IGNORECASE,
)
LEGACY_DIRECTIVE_MODAL_RE = re.compile(
    MODAL_BOUNDARY_RE.pattern
    + r"|\b(?:permitted|prohibited|required|classified|designed|constructed|managed|"
    r"maintained|follow|apply|applies|limited|allowed)\b",
    re.IGNORECASE,
)
LEGACY_CROSS_REFERENCE_PREFIX_RE = re.compile(
    r"\b(?:as\s+defined\s+in|defined\s+in|see|refer(?:red)?\s+to|pursuant\s+to|"
    r"consistent\s+with|identified\s+in|described\s+in)\s+(?:the\s+)?(?:forest\s+)?\Z",
    re.IGNORECASE,
)
LEGACY_CODE_PREFIX_RE = re.compile(
    r"(?:\([A-Za-z0-9-]+\)|[A-Z0-9]{1,4}-(?:DC|GO|GDL|GL|MON|OBJ|STD|SUIT)"
    r"(?:-[A-Z0-9]+)*-?)\s*\Z"
)


def ordered_legacy_chunks(chunks: list[dict]) -> list[dict]:
    return sorted(
        chunks,
        key=lambda chunk: (
            str(chunk.get("source_record_id") or ""),
            int(chunk.get("chunk_index") or 0),
            int(chunk.get("page") or 0),
            int(chunk.get("char_start") or 0),
            str(chunk.get("chunk_id") or ""),
        ),
    )


def legacy_component_matches(
    *,
    text: str,
    fallback_heading: str,
    initial_context: dict | None = None,
) -> tuple[list[dict], dict]:
    context = dict(initial_context or {})
    matches = []
    for index, directive in enumerate(list(LEGACY_NUMBERED_DIRECTIVE_RE.finditer(text))):
        start = directive.start()
        context = _context_for_prefix(
            prefix=text[:start],
            fallback_heading=fallback_heading,
            context=context,
        )
        end = _legacy_directive_end(text, directive.end(), index=index)
        body = _compact(text[directive.end() : end], limit=10000)
        number = _normalized_number(directive.group("number"))
        label = str(context.get("label") or "")
        if not label:
            label = "Standard" if _has_legacy_direction_cue(text[:start]) else ""
        if (
            not label
            or not number
            or _is_modern_component_code_number(text=text, start=start)
            or _is_explicit_singular_component_label(text=text, start=start)
            or _looks_like_legacy_table_context(text=text, start=start, body=body)
            or _is_legacy_cross_reference(text=text, start=start, label=label)
            or not _has_legacy_directive_body(label=label, body=body)
        ):
            continue
        section_heading = _legacy_section_heading(
            context=context,
            fallback_heading=fallback_heading,
        )
        matches.append(
            {
                "label": label,
                "number": number,
                "text": body,
                "section_heading": section_heading,
                "start": start,
                "end": end,
                "management_area_ids": _management_area_ids(context),
                "legacy_context": _serializable_context(context),
            }
        )
    return matches, _context_for_prefix(
        prefix=text,
        fallback_heading=fallback_heading,
        context=context,
    )


def _context_for_prefix(*, prefix: str, fallback_heading: str, context: dict) -> dict:
    current = dict(context)
    window = prefix[-1800:]
    area_match = _last_match((LEGACY_MANAGEMENT_AREA_RE, LEGACY_MA_TOKEN_RE), window)
    if area_match is not None:
        identifier = _normalized_management_area_identifier(area_match.group("identifier"))
        if identifier:
            current["management_area_identifier"] = identifier
            current["management_area_heading"] = f"Management Area {identifier}"
    heading = _last_heading(window)
    if heading:
        current.update(heading)
    elif _has_legacy_direction_cue(window):
        current.setdefault("label", "Standard")
        current.setdefault("section_heading", fallback_heading)
    if LEGACY_SECTION_TERMINATOR_RE.search(window[-240:]):
        current.pop("label", None)
        current["section_heading"] = str(current.get("management_area_heading") or fallback_heading)
    return current


def _last_heading(window: str) -> dict | None:
    candidates: list[tuple[int, dict]] = []
    for match in LEGACY_COMPONENT_HEADING_RE.finditer(window):
        if not _is_heading_case(match.group("label")):
            continue
        label = LEGACY_LABEL_BY_HEADING.get(" ".join(match.group("label").lower().split()))
        if label:
            candidates.append(
                (
                    match.start(),
                    {
                        "label": label,
                        "section_heading": _compact(match.group("label"), limit=160),
                    },
                )
            )
    for match in LEGACY_PRACTICE_HEADING_RE.finditer(window):
        candidates.append(
            (
                match.start(),
                {
                    "label": "Standard",
                    "section_heading": _compact(match.group("heading"), limit=160),
                },
            )
        )
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _is_heading_case(value: str) -> bool:
    return value[:1].isupper()


def _last_match(patterns: tuple[re.Pattern[str], ...], text: str) -> re.Match[str] | None:
    matches = [match for pattern in patterns for match in pattern.finditer(text)]
    return max(matches, key=lambda match: match.start()) if matches else None


def _legacy_directive_end(text: str, start: int, *, index: int) -> int:
    candidates = [
        match.start()
        for match in LEGACY_NUMBERED_DIRECTIVE_RE.finditer(text, start)
        if match.start() > start
    ]
    candidates.extend(match.start() for match in LEGACY_PRACTICE_HEADING_RE.finditer(text, start))
    candidates.extend(
        match.start()
        for match in LEGACY_COMPONENT_HEADING_RE.finditer(text, start)
        if _is_heading_case(match.group("label"))
    )
    candidates.extend(match.start() for match in LEGACY_MANAGEMENT_AREA_RE.finditer(text, start))
    candidates.extend(match.start() for match in LEGACY_SECTION_TERMINATOR_RE.finditer(text, start))
    if candidates:
        return min(candidates)
    return len(text)


def _legacy_section_heading(*, context: dict, fallback_heading: str) -> str:
    parts = []
    if context.get("management_area_heading"):
        parts.append(str(context["management_area_heading"]))
    section = str(context.get("section_heading") or "").strip()
    if section and section not in parts:
        parts.append(section)
    if not parts:
        parts.append(fallback_heading)
    return _compact(" ".join(parts), limit=240)


def _management_area_ids(context: dict) -> list[str]:
    identifier = str(context.get("management_area_identifier") or "").strip()
    if not identifier:
        return []
    return [f"mgmt-ma-{_safe_identifier(identifier.lower())}"]


def _serializable_context(context: dict) -> dict:
    return {
        key: str(value)
        for key, value in context.items()
        if key in {"label", "section_heading", "management_area_identifier", "management_area_heading"}
        and str(value).strip()
    }


def _normalized_management_area_identifier(identifier: str) -> str:
    text = identifier.strip().replace("?", "7")
    if text.isdigit():
        return str(int(text))
    if re.fullmatch(r"[IVXLC]+", text, flags=re.IGNORECASE):
        return str(_roman_to_int(text.upper()))
    match = re.fullmatch(r"0*([0-9]{1,3})([A-Za-z]?)", text)
    if match:
        return f"{int(match.group(1))}{match.group(2).lower()}"
    return text.lower()


def _normalized_number(number: str) -> str:
    text = number.strip()
    if text.isdigit():
        return str(int(text))
    if re.fullmatch(r"[IVXLC]+", text, flags=re.IGNORECASE):
        return str(_roman_to_int(text.upper()))
    return text


def _roman_to_int(value: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    total = 0
    previous = 0
    for char in reversed(value):
        current = values.get(char, 0)
        total += -current if current < previous else current
        previous = max(previous, current)
    return total


def _has_legacy_direction_cue(text: str) -> bool:
    return bool(LEGACY_DIRECTION_CUE_RE.search(text[-1600:]))


def _has_legacy_directive_body(*, label: str, body: str) -> bool:
    normalized_label = label.lower()
    if normalized_label.startswith(("goal", "objective", "desired condition")):
        return len(body.split()) >= 4
    return bool(LEGACY_DIRECTIVE_MODAL_RE.search(body)) and len(body.split()) >= 4


def _looks_like_legacy_table_context(*, text: str, start: int, body: str) -> bool:
    prefix = text[max(0, start - 360) : start]
    return bool(
        LEGACY_STOP_HEADING_RE.search(prefix)
        or LEGACY_STOP_HEADING_RE.match(body[:180].lstrip())
        or re.search(r"\.{5,}", body[:180])
    )


def _is_legacy_cross_reference(*, text: str, start: int, label: str) -> bool:
    if not label.lower().startswith("standard"):
        return False
    prefix = text[max(0, start - 80) : start]
    return bool(LEGACY_CROSS_REFERENCE_PREFIX_RE.search(prefix))


def _is_modern_component_code_number(*, text: str, start: int) -> bool:
    prefix = text[max(0, start - 80) : start]
    return bool(LEGACY_CODE_PREFIX_RE.search(prefix))


def _is_explicit_singular_component_label(*, text: str, start: int) -> bool:
    prefix = text[max(0, start - 80) : start]
    return bool(
        re.search(
            r"\b(?:Desired\s+Condition|Goal|Guideline|Objective|Standard)\s+\Z",
            prefix,
            re.IGNORECASE,
        )
    )
