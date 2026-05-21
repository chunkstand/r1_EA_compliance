from __future__ import annotations

from collections import Counter
from typing import Any

from .applicability_eval_support import _case_list
from .applicability_eval_support import _source_chunk_specs
from .applicability_eval_support import _strings


def _aggregate_arbitration_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    effect_counts: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    for case in case_results:
        summary = case.get("arbitration_summary")
        if not isinstance(summary, dict):
            continue
        status_counts.update(summary.get("arbitration_status_counts") or {})
        effect_counts.update(summary.get("decision_effect_counts") or {})
        for key in (
            "decision_count",
            "applicable_with_weak_auxiliary_count",
            "weak_positive_only_needs_adjudication_count",
            "insufficient_strong_positive_needs_adjudication_count",
            "positive_negative_conflict_needs_adjudication_count",
            "conservative_arbitration_needs_adjudication_count",
            "genuine_conflict_needs_adjudication_count",
        ):
            totals[key] += int(summary.get(key) or 0)
    return {
        "schema_version": "applicability-arbitration-summary-v0",
        "case_count": len(case_results),
        "decision_count": totals["decision_count"],
        "arbitration_status_counts": dict(sorted(status_counts.items())),
        "decision_effect_counts": dict(sorted(effect_counts.items())),
        "applicable_with_weak_auxiliary_count": totals[
            "applicable_with_weak_auxiliary_count"
        ],
        "weak_positive_only_needs_adjudication_count": totals[
            "weak_positive_only_needs_adjudication_count"
        ],
        "insufficient_strong_positive_needs_adjudication_count": totals[
            "insufficient_strong_positive_needs_adjudication_count"
        ],
        "positive_negative_conflict_needs_adjudication_count": totals[
            "positive_negative_conflict_needs_adjudication_count"
        ],
        "conservative_arbitration_needs_adjudication_count": totals[
            "conservative_arbitration_needs_adjudication_count"
        ],
        "genuine_conflict_needs_adjudication_count": totals[
            "genuine_conflict_needs_adjudication_count"
        ],
    }


def _failure_category_counts(case_results: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for case in case_results:
        counts.update(case.get("failure_category_counts") or {})
    return dict(sorted(counts.items()))


def _authority_family_template_coverage(
    *,
    eval_payload: dict[str, Any],
    template_set: dict[str, Any] | None,
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    templates = [
        template
        for template in (template_set or {}).get("templates", [])
        if isinstance(template, dict)
    ]
    high_priority_family_ids = _strings(
        eval_payload.get("high_priority_authority_family_ids")
    ) or sorted(
        str(template.get("authority_family_id") or "")
        for template in templates
        if template.get("authority_family_id")
    )
    family_by_rule_id = {
        str(template.get("rule_id") or ""): str(template.get("authority_family_id") or "")
        for template in templates
        if template.get("rule_id") and template.get("authority_family_id")
    }
    positive: dict[str, list[str]] = {}
    negative: dict[str, list[str]] = {}
    unresolved: dict[str, list[str]] = {}
    adjudicated: dict[str, list[str]] = {}
    coverage_tags: set[str] = set()
    for case in case_results:
        coverage_tags.update(_strings(case.get("coverage_tags")))
        for rule_id, family_id in family_by_rule_id.items():
            status = (case.get("expected_statuses") or {}).get(rule_id)
            if status == "applicable":
                positive.setdefault(family_id, []).append(str(case.get("id")))
            elif status == "not_applicable":
                negative.setdefault(family_id, []).append(str(case.get("id")))
            elif status in {"unresolved", "needs_adjudication"}:
                unresolved.setdefault(family_id, []).append(str(case.get("id")))
        for rule_id in _strings(case.get("adjudicated_rule_ids")):
            family_id = family_by_rule_id.get(rule_id)
            if family_id:
                adjudicated.setdefault(family_id, []).append(str(case.get("id")))
    required_tags = _strings(eval_payload.get("required_real_package_coverage_tags"))
    missing_positive = sorted(set(high_priority_family_ids) - set(positive))
    missing_negative = sorted(set(high_priority_family_ids) - set(negative))
    missing_tags = sorted(set(required_tags) - coverage_tags)
    return {
        "schema_version": "authority-family-template-eval-coverage-v0",
        "high_priority_family_ids": sorted(high_priority_family_ids),
        "high_priority_family_count": len(high_priority_family_ids),
        "positive_covered_family_ids": sorted(positive),
        "positive_covered_family_count": len(positive),
        "negative_covered_family_ids": sorted(negative),
        "negative_covered_family_count": len(negative),
        "unresolved_covered_family_ids": sorted(unresolved),
        "unresolved_covered_family_count": len(unresolved),
        "adjudicated_covered_family_ids": sorted(adjudicated),
        "adjudicated_covered_family_count": len(adjudicated),
        "required_real_package_coverage_tags": sorted(required_tags),
        "real_package_coverage_tags": sorted(coverage_tags),
        "missing_positive_family_ids": missing_positive,
        "missing_negative_family_ids": missing_negative,
        "missing_real_package_coverage_tags": missing_tags,
        "positive_negative_coverage_passed": (
            not missing_positive and not missing_negative
        ),
        "real_package_coverage_passed": not missing_tags,
        "passed": not missing_positive and not missing_negative and not missing_tags,
    }


def _gold_source_chunk_count(gold: dict[str, Any]) -> int:
    source_record_ids: set[str] = set()
    for spec in _source_chunk_specs(gold.get("source_chunks")):
        source_record_id = str(spec.get("source_record_id") or "").strip()
        if source_record_id:
            source_record_ids.add(source_record_id)
    for case in _case_list(gold):
        if not isinstance(case, dict):
            continue
        for spec in _source_chunk_specs(case.get("source_chunks")):
            source_record_id = str(spec.get("source_record_id") or "").strip()
            if source_record_id:
                source_record_ids.add(source_record_id)
    return len(source_record_ids)
