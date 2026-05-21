from __future__ import annotations

from collections import Counter


def _failure_category_counts(
    *,
    rule_pack_result: dict[str, object],
    review_results: list[dict[str, object]],
    suite_results: list[dict[str, object]],
    expansion_slots: list[dict[str, object]],
    strict_expansion: bool,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    counts.update(rule_pack_result.get("failure_categories", []))
    for case in review_results:
        for result in case["results"]:
            if not result["passed"] and (
                result["required_for_current_promotion"]
                or (strict_expansion and result["required_for_expansion"])
            ):
                counts.update(result.get("failure_categories", []))
    for result in suite_results:
        if not result["passed"] and (
            result["required_for_current_promotion"]
            or (strict_expansion and result["required_for_expansion"])
        ):
            counts.update(result.get("failure_categories", []))
    for slot in expansion_slots:
        if strict_expansion or slot.get("required_for_current_promotion"):
            counts.update(slot.get("failure_categories", []))
    return counts


def _expansion_failure_category_counts(
    *,
    review_results: list[dict[str, object]],
    suite_results: list[dict[str, object]],
    expansion_slots: list[dict[str, object]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for case in review_results:
        for result in case["results"]:
            if not result["passed"] and result["required_for_expansion"]:
                counts.update(result.get("failure_categories", []))
    for result in suite_results:
        if not result["passed"] and result["required_for_expansion"]:
            counts.update(result.get("failure_categories", []))
    for slot in expansion_slots:
        if not slot.get("ready"):
            counts.update(slot.get("failure_categories", []))
    return counts


def _full_canonical_failure_category_counts(
    *,
    suite_results: list[dict[str, object]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for result in suite_results:
        if not result["passed"] and result["required_for_full_canonical_corpus"]:
            counts.update(result.get("failure_categories", []))
    return counts
