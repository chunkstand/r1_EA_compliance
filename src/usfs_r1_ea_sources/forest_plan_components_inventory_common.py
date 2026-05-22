from __future__ import annotations

import re

from .forest_plan_components_common import _compact, _dedupe_preserve_order, _normalized_component_text
from .forest_plan_components_models import LEGACY_SECTION_HEADING_RE, SECTION_HEADING_RE, TOKEN_RE


def _suppress_tabular_component_label(
    *,
    label: str,
    code: str,
    number: str,
    text: str,
) -> bool:
    normalized_label = label.strip().lower()
    normalized_code = code.strip().lower()
    normalized_text = _normalized_component_text(text)
    if normalized_label not in {"standard", "standards"}:
        return False
    if normalized_code not in {"max", "min"}:
        return False
    if not number.isdigit():
        return False
    return normalized_text.startswith("status selected standard")


def _matching_profile_entry_ids(text: str, entries: tuple[object, ...]) -> list[str]:
    normalized_text = _normalized_component_text(text)
    text_tokens = set(TOKEN_RE.findall(normalized_text))
    text_tokens.update(
        part
        for token in list(text_tokens)
        for part in token.split("-")
        if part
    )
    matches = []
    for entry in entries:
        entry_id = str(getattr(entry, "entry_id", "") or "").strip()
        terms = _profile_entry_context_terms(entry)
        if not entry_id:
            continue
        for term in terms:
            normalized_term = _normalized_component_text(str(term))
            if not normalized_term:
                continue
            if " " in normalized_term and normalized_term in normalized_text:
                matches.append(entry_id)
                break
            if " " not in normalized_term and normalized_term in text_tokens:
                matches.append(entry_id)
                break
    return _dedupe_preserve_order(matches)


def _profile_entry_context_terms(entry: object) -> tuple[str, ...]:
    terms = [str(term).strip() for term in getattr(entry, "terms", ()) if str(term).strip()]
    category = str(getattr(entry, "category", "") or "").strip()
    if category == "geographic_area":
        for term in list(terms):
            shortened = re.sub(r"\s+Geographic\s+Area\Z", "", term, flags=re.IGNORECASE).strip()
            if shortened and shortened != term and len(TOKEN_RE.findall(shortened.lower())) >= 2:
                terms.append(shortened)
                singular = re.sub(r"\bMountains\b", "Mountain", shortened, flags=re.IGNORECASE)
                if singular and singular != shortened:
                    terms.append(singular)
    return tuple(_dedupe_preserve_order(terms))


def _component_type_from_label(label: str) -> str:
    normalized = " ".join(label.lower().split())
    if normalized.startswith("desired condition"):
        return "desired_condition"
    if normalized.startswith("goal"):
        return "goal"
    if normalized.startswith("guideline"):
        return "guideline"
    if normalized.startswith("monitoring"):
        return "monitoring"
    if normalized.startswith("objective"):
        return "objective"
    if normalized.startswith("standard"):
        return "standard"
    if normalized.startswith("suitability"):
        return "suitability"
    raise ValueError(f"Unsupported forest-plan component label: {label!r}.")


def _section_heading_for_match(*, text: str, start: int, fallback: str) -> str:
    prefix = text[:start]
    matches = list(SECTION_HEADING_RE.finditer(prefix))
    if matches:
        section = _compact(matches[-1].group("section"), limit=240)
        return f"Plan Components-{section}"
    return _legacy_section_heading_for_match(text=text, start=start, fallback=fallback)


def _legacy_section_heading_for_match(*, text: str, start: int, fallback: str) -> str:
    prefix = text[max(0, start - 2000) : start]
    matches = list(LEGACY_SECTION_HEADING_RE.finditer(prefix))
    if matches:
        return _compact(matches[-1].group("section"), limit=240)
    return _compact(fallback, limit=240)


def _component_context_window(*, text: str, start: int, end: int) -> str:
    window_start = max(0, start - 1200)
    window_end = min(len(text), end + 400)
    return _compact(text[window_start:window_end], limit=2000)
