from __future__ import annotations

import re
from typing import Any


EVIDENCE_STRENGTH_SCHEMA_VERSION = "evidence-strength-v0"

WEAK_CONFIDENCE_CLASSES = {"weak_signal"}
WEAK_STRENGTH_CLASSES = {"conditional", "speculative", "background", "weak_signal"}
NEGATIVE_STRENGTH_CLASSES = {"negative_context"}
CONDITIONAL_PHRASES = (
    "may be required",
    "may require",
    "might require",
    "could be required",
    "could require",
    "if present",
    "if needed",
    "if required",
)
SPECULATIVE_PHRASES = (
    "may be possible",
    "might be possible",
    "could be possible",
    "potentially",
    "possible",
)
WEAK_SIGNAL_PHRASES = (
    "not yet determined",
    "unknown whether",
)
BACKGROUND_CONTEXT_PHRASES = (
    "no action alternative",
    "no action",
    "no change",
    "no changes",
    "would not change",
    "will not change",
    "does not change",
    "do not change",
    "would not occur",
    "will not occur",
    "does not occur",
    "do not occur",
    "would not be constructed",
    "will not be constructed",
    "would not be authorized",
    "will not be authorized",
    "does not include",
    "does not involve",
    "not proposed",
    "not part of the proposed action",
    "unchanged",
    "no new",
    "no additional",
)
NEGATIVE_CONTEXT_PHRASES = (
    "not part of the project area",
    "outside the project area",
    "outside of the project area",
    "outside the analysis area",
    "outside of the analysis area",
    "is not within the project area",
    "not affected by the project",
    "does not apply to the project area",
    "project does not include",
    "project does not contain",
    "project does not affect",
    "no designated wilderness in the project area",
    "no research natural areas in the project area",
    *BACKGROUND_CONTEXT_PHRASES,
)
BACKGROUND_SECTION_FAMILIES = {"no_action", "cumulative_effects"}


def classify_evidence_strength(
    *,
    text: str,
    start: int,
    end: int,
    matched_text: str | None = None,
    default_confidence_class: str = "observed",
    section_family: str | None = None,
    negative_context: bool = False,
    negative_reason: str | None = None,
) -> dict[str, Any]:
    """Classify matched evidence without changing existing confidence-class semantics."""

    normalized_text = str(text or "")
    window_start, window_end, window = evidence_window(normalized_text, start, end)
    window_lower = window.lower()
    section = str(section_family or "") or None
    default_class = str(default_confidence_class or "observed")

    if negative_context or default_class == "negative_context":
        return _strength_payload(
            confidence_class="negative_context",
            strength_class="negative_context",
            reason=negative_reason or "negative_context",
            matched_phrase=_first_phrase(window_lower, NEGATIVE_CONTEXT_PHRASES),
            matched_text=matched_text,
            evidence_window=window,
            evidence_window_start=window_start,
            evidence_window_end=window_end,
            section_family=section,
        )

    background_phrase = _first_phrase(window_lower, BACKGROUND_CONTEXT_PHRASES)
    if background_phrase:
        return _strength_payload(
            confidence_class="weak_signal",
            strength_class="background",
            reason="background_or_no_action_context",
            matched_phrase=background_phrase,
            matched_text=matched_text,
            evidence_window=window,
            evidence_window_start=window_start,
            evidence_window_end=window_end,
            section_family=section,
        )

    conditional_phrase = _first_phrase(window_lower, CONDITIONAL_PHRASES)
    if conditional_phrase:
        return _strength_payload(
            confidence_class="weak_signal",
            strength_class="conditional",
            reason="conditional_phrase",
            matched_phrase=conditional_phrase,
            matched_text=matched_text,
            evidence_window=window,
            evidence_window_start=window_start,
            evidence_window_end=window_end,
            section_family=section,
        )

    speculative_phrase = _first_phrase(window_lower, SPECULATIVE_PHRASES)
    if speculative_phrase:
        return _strength_payload(
            confidence_class="weak_signal",
            strength_class="speculative",
            reason="speculative_phrase",
            matched_phrase=speculative_phrase,
            matched_text=matched_text,
            evidence_window=window,
            evidence_window_start=window_start,
            evidence_window_end=window_end,
            section_family=section,
        )

    weak_phrase = _first_phrase(window_lower, WEAK_SIGNAL_PHRASES)
    if weak_phrase or default_class in WEAK_CONFIDENCE_CLASSES:
        return _strength_payload(
            confidence_class="weak_signal",
            strength_class="weak_signal",
            reason="weak_signal_phrase" if weak_phrase else "configured_weak_signal",
            matched_phrase=weak_phrase,
            matched_text=matched_text,
            evidence_window=window,
            evidence_window_start=window_start,
            evidence_window_end=window_end,
            section_family=section,
        )

    if section in BACKGROUND_SECTION_FAMILIES:
        return _strength_payload(
            confidence_class="weak_signal",
            strength_class="background",
            reason="background_section",
            matched_phrase=section,
            matched_text=matched_text,
            evidence_window=window,
            evidence_window_start=window_start,
            evidence_window_end=window_end,
            section_family=section,
        )

    return _strength_payload(
        confidence_class=default_class,
        strength_class=default_class if default_class != "observed" else "observed",
        reason="observed_match",
        matched_phrase=None,
        matched_text=matched_text,
        evidence_window=window,
        evidence_window_start=window_start,
        evidence_window_end=window_end,
        section_family=section,
    )


def evidence_strength_for_confidence(
    confidence_class: str | None,
    *,
    section_family: str | None = None,
) -> dict[str, Any]:
    confidence = str(confidence_class or "observed")
    if confidence == "negative_context":
        strength_class = "negative_context"
        reason = "negative_context"
    elif confidence == "weak_signal":
        strength_class = "weak_signal"
        reason = "legacy_weak_signal"
    else:
        strength_class = confidence
        reason = "legacy_confidence_class"
    return {
        "schema_version": EVIDENCE_STRENGTH_SCHEMA_VERSION,
        "confidence_class": confidence,
        "strength_class": strength_class,
        "reason": reason,
        "section_family": section_family,
    }


def is_weak_signal_text(
    text: str,
    start: int,
    end: int,
    *,
    section_family: str | None = None,
) -> bool:
    return (
        classify_evidence_strength(
            text=text,
            start=start,
            end=end,
            section_family=section_family,
        )["confidence_class"]
        == "weak_signal"
    )


def evidence_window(text: str, start: int, end: int) -> tuple[int, int, str]:
    safe_start = max(0, min(int(start), len(text)))
    safe_end = max(safe_start, min(int(end), len(text)))
    sentence_start = max(
        text.rfind(".", 0, safe_start),
        text.rfind("\n", 0, safe_start),
        text.rfind(";", 0, safe_start),
    )
    sentence_end_candidates = [
        index
        for index in (
            text.find(".", safe_end),
            text.find("\n", safe_end),
            text.find(";", safe_end),
        )
        if index >= 0
    ]
    window_start = sentence_start + 1
    window_end = (
        min(sentence_end_candidates) + 1
        if sentence_end_candidates
        else len(text)
    )
    return window_start, window_end, _normalize_window(text[window_start:window_end])


def _strength_payload(
    *,
    confidence_class: str,
    strength_class: str,
    reason: str,
    matched_phrase: str | None,
    matched_text: str | None,
    evidence_window: str,
    evidence_window_start: int,
    evidence_window_end: int,
    section_family: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": EVIDENCE_STRENGTH_SCHEMA_VERSION,
        "confidence_class": confidence_class,
        "strength_class": strength_class,
        "reason": reason,
        "evidence_window": evidence_window,
        "evidence_window_char_start": evidence_window_start,
        "evidence_window_char_end": evidence_window_end,
    }
    if matched_phrase:
        payload["matched_phrase"] = matched_phrase
    if matched_text:
        payload["matched_text"] = matched_text
    if section_family:
        payload["section_family"] = section_family
    return payload


def _first_phrase(text: str, phrases: tuple[str, ...]) -> str | None:
    for phrase in sorted(phrases, key=len, reverse=True):
        if _phrase_in_text(text, phrase):
            return phrase
    return None


def _phrase_in_text(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9]){re.escape(phrase)}(?![A-Za-z0-9])",
            text,
            flags=re.IGNORECASE,
        )
    )


def _normalize_window(text: str) -> str:
    return " ".join(str(text or "").split())
