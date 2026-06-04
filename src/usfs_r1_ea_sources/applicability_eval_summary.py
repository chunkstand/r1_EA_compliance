from __future__ import annotations

from collections import Counter
from typing import Any

from .applicability_eval_trajectory import trajectory_process_metric_group
from .applicability_eval_support import _case_list
from .applicability_eval_support import _case_rate
from .applicability_eval_support import _source_chunk_specs
from .applicability_eval_support import _strings


APPLICABILITY_EVAL_METRIC_GROUP_IDS = (
    "authority_universe_coverage",
    "retrieval_trace_quality",
    "graph_trace_quality",
    "decision_partition_fidelity",
    "generated_rule_pack_fidelity",
    "gate_graph_consistency",
    "forest_plan_subgate_behavior",
    "adjudication_failure_intake",
    "trajectory_process_quality",
)


def _applicability_eval_metric_groups(
    *,
    case_results: list[dict[str, Any]],
    metrics: dict[str, Any],
    authority_family_template_coverage: dict[str, Any],
    arbitration_summary: dict[str, Any],
    failure_category_counts: dict[str, int],
    failure_intake_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    hard_negative_results = _hard_negative_results(case_results)
    gate_graph_required_results = [
        case for case in case_results if case.get("gate_graph_required")
    ]
    forest_plan_component_case_count = sum(
        1
        for case in case_results
        if int(case.get("forest_plan_component_gate_count") or 0) > 0
    )
    forest_plan_family_case_count = sum(
        1
        for case in case_results
        if "forest_plan_consistency" in _strings(case.get("coverage_tags"))
        or "region1_forest_plan_source_records_authority_template"
        in set((case.get("expected_statuses") or {}))
    )
    return {
        "authority_universe_coverage": _metric_group(
            status="direct_eval_present",
            blocking=True,
            passed=(
                bool(authority_family_template_coverage.get("passed"))
                and all(int(case.get("candidate_authority_count") or 0) > 0 for case in case_results)
            ),
            metrics={
                "case_count": len(case_results),
                "candidate_authority_count": sum(
                    int(case.get("candidate_authority_count") or 0)
                    for case in case_results
                ),
                "minimum_candidate_authority_count": min(
                    [int(case.get("candidate_authority_count") or 0) for case in case_results]
                    or [0]
                ),
                "high_priority_family_count": authority_family_template_coverage.get(
                    "high_priority_family_count"
                ),
                "positive_covered_family_count": authority_family_template_coverage.get(
                    "positive_covered_family_count"
                ),
                "negative_covered_family_count": authority_family_template_coverage.get(
                    "negative_covered_family_count"
                ),
                "unresolved_covered_family_count": authority_family_template_coverage.get(
                    "unresolved_covered_family_count"
                ),
                "missing_positive_family_count": len(
                    authority_family_template_coverage.get("missing_positive_family_ids") or []
                ),
                "missing_negative_family_count": len(
                    authority_family_template_coverage.get("missing_negative_family_ids") or []
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {"missing_applicability_artifact", "applicability_validation_mismatch"},
            ),
        ),
        "retrieval_trace_quality": _metric_group(
            status="direct_eval_present",
            blocking=True,
            passed=all(
                case.get("retrieval_trace_coverage_matches")
                and case.get("source_record_alignment_matches")
                and case.get("document_role_alignment_matches")
                for case in case_results
            ),
            metrics={
                "coverage_match_rate": _case_rate(
                    case_results,
                    "retrieval_trace_coverage_matches",
                ),
                "source_record_alignment_rate": _case_rate(
                    case_results,
                    "source_record_alignment_matches",
                ),
                "document_role_alignment_rate": _case_rate(
                    case_results,
                    "document_role_alignment_matches",
                ),
                "minimum_retrieval_trace_row_count": min(
                    [int(case.get("retrieval_trace_row_count") or 0) for case in case_results]
                    or [0]
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {
                    "retrieval_trace_gap",
                    "source_record_alignment_mismatch",
                    "document_role_alignment_mismatch",
                },
            ),
        ),
        "graph_trace_quality": _metric_group(
            status="direct_eval_present",
            blocking=True,
            passed=all(
                case.get("graph_trace_coverage_matches")
                and case.get("graph_non_path_matches")
                for case in case_results
            ),
            metrics={
                "coverage_match_rate": _case_rate(case_results, "graph_trace_coverage_matches"),
                "non_path_match_rate": _case_rate(case_results, "graph_non_path_matches"),
                "minimum_graph_trace_row_count": min(
                    [int(case.get("graph_trace_row_count") or 0) for case in case_results]
                    or [0]
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {"graph_trace_gap"},
            ),
        ),
        "decision_partition_fidelity": _metric_group(
            status="direct_eval_present",
            blocking=True,
            passed=(
                bool(metrics.get("status_match_rate") == 1.0)
                and bool(metrics.get("applicable_partition_match_rate") == 1.0)
                and bool(metrics.get("non_applicable_partition_match_rate") == 1.0)
                and all(item.get("passed") for item in hard_negative_results)
            ),
            metrics={
                "status_match_rate": metrics.get("status_match_rate"),
                "applicable_partition_match_rate": metrics.get(
                    "applicable_partition_match_rate"
                ),
                "non_applicable_partition_match_rate": metrics.get(
                    "non_applicable_partition_match_rate"
                ),
                "coverage_certificate_rate": metrics.get("coverage_certificate_rate"),
                "hard_negative_case_count": len(hard_negative_results),
                "hard_negative_passed_count": sum(
                    1 for item in hard_negative_results if item.get("passed")
                ),
                "needs_adjudication_decision_count": (
                    arbitration_summary.get("weak_positive_only_needs_adjudication_count", 0)
                    + arbitration_summary.get(
                        "insufficient_strong_positive_needs_adjudication_count",
                        0,
                    )
                    + arbitration_summary.get(
                        "positive_negative_conflict_needs_adjudication_count",
                        0,
                    )
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {
                    "applicability_status_mismatch",
                    "applicable_partition_mismatch",
                    "non_applicable_partition_mismatch",
                    "search_coverage_gap",
                    "adjudication_mismatch",
                    "arbitration_mismatch",
                },
            ),
        ),
        "generated_rule_pack_fidelity": _metric_group(
            status="direct_eval_present",
            blocking=True,
            passed=all(
                case.get("generated_rule_pack_ready_matches")
                and case.get("generated_rule_pack_matches_applicability")
                and case.get("generated_rule_pack_hash_matches_validation")
                for case in case_results
            ),
            metrics={
                "generated_rule_pack_match_rate": metrics.get(
                    "generated_rule_pack_match_rate"
                ),
                "ready_case_count": sum(
                    1 for case in case_results if case.get("generated_rule_pack_ready")
                ),
                "hash_match_rate": _case_rate(
                    case_results,
                    "generated_rule_pack_hash_matches_validation",
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {
                    "generated_rule_pack_mismatch",
                    "generated_rule_pack_not_ready",
                },
            ),
        ),
        "gate_graph_consistency": _metric_group(
            status=(
                "direct_eval_present"
                if gate_graph_required_results
                else "direct_eval_strengthening_planned"
            ),
            blocking=bool(gate_graph_required_results),
            passed=bool(gate_graph_required_results)
            and all(
                case.get("gate_graph_validation_passed")
                and case.get("gate_graph_identity_matches")
                and case.get("gate_graph_input_hashes_match")
                and case.get("gate_graph_consistency_matches")
                for case in gate_graph_required_results
            ),
            metrics={
                "gate_graph_required_case_count": len(gate_graph_required_results),
                "gate_graph_observed_case_count": sum(
                    1 for case in case_results if int(case.get("gate_graph_node_count") or 0) > 0
                ),
                "validation_pass_rate": _case_rate(
                    gate_graph_required_results,
                    "gate_graph_validation_passed",
                ),
                "identity_match_rate": _case_rate(
                    gate_graph_required_results,
                    "gate_graph_identity_matches",
                ),
                "input_hash_match_rate": _case_rate(
                    gate_graph_required_results,
                    "gate_graph_input_hashes_match",
                ),
                "decision_consistency_rate": _case_rate(
                    gate_graph_required_results,
                    "gate_graph_consistency_matches",
                ),
                "minimum_gate_graph_node_count": min(
                    [int(case.get("gate_graph_node_count") or 0) for case in case_results]
                    or [0]
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {
                    "gate_graph_consistency_mismatch",
                    "gate_graph_identity_mismatch",
                    "gate_graph_stale_artifact",
                    "gate_graph_validation_mismatch",
                },
            ),
            gap=(
                None
                if gate_graph_required_results
                else "gate graph artifacts are emitted, but no eval case declares "
                "expected_gate_graph_required yet"
            ),
        ),
        "forest_plan_subgate_behavior": _metric_group(
            status=(
                "direct_eval_present"
                if forest_plan_component_case_count
                else "direct_eval_strengthening_planned"
            ),
            blocking=bool(forest_plan_component_case_count),
            passed=not forest_plan_component_case_count
            or all(
                int(case.get("forest_plan_component_gate_count") or 0) == 0
                or case.get("gate_graph_consistency_matches")
                for case in case_results
            ),
            metrics={
                "forest_plan_authority_family_case_count": forest_plan_family_case_count,
                "forest_plan_component_case_count": forest_plan_component_case_count,
                "forest_plan_component_gate_count": sum(
                    int(case.get("forest_plan_component_gate_count") or 0)
                    for case in case_results
                ),
                "forest_plan_instance_gate_count": sum(
                    int(case.get("forest_plan_instance_gate_count") or 0)
                    for case in case_results
                ),
            },
            failure_categories=_group_failure_categories(
                failure_category_counts,
                {"forest_plan_subgate_mismatch"},
            ),
            gap="component/subgate fixture coverage remains Milestone 1 follow-on when no "
            "forest-plan component case is present",
        ),
        "adjudication_failure_intake": _metric_group(
            status="direct_eval_present",
            blocking=True,
            passed=bool(failure_intake_summary.get("validation_passed")),
            metrics={
                "failure_intake_candidate_count": failure_intake_summary.get(
                    "failure_intake_candidate_count",
                    0,
                ),
                "replayable_case_count": failure_intake_summary.get(
                    "replayable_case_count",
                    0,
                ),
                "failed_case_count": failure_intake_summary.get("failed_case_count", 0),
                "needs_adjudication_case_count": failure_intake_summary.get(
                    "needs_adjudication_case_count",
                    0,
                ),
                "adjudicated_rule_count": sum(
                    len(_strings(case.get("adjudicated_rule_ids"))) for case in case_results
                ),
                "source_artifact_ref_count": failure_intake_summary.get(
                    "source_artifact_ref_count",
                    0,
                ),
            },
            failure_categories=failure_intake_summary.get("failure_category_counts") or {},
        ),
        "trajectory_process_quality": trajectory_process_metric_group(case_results),
    }


def _metric_group(
    *,
    status: str,
    blocking: bool,
    passed: bool,
    metrics: dict[str, Any],
    failure_categories: dict[str, int],
    gap: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "blocking": bool(blocking),
        "passed": bool(passed),
        "metrics": metrics,
        "failure_category_counts": failure_categories,
    }
    if gap:
        payload["gap"] = gap
    return payload


def _metric_group_contract_summary(
    metric_groups: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    missing_group_ids = sorted(set(APPLICABILITY_EVAL_METRIC_GROUP_IDS) - set(metric_groups))
    blocking_failures = sorted(
        group_id
        for group_id, group in metric_groups.items()
        if group.get("blocking") and not group.get("passed")
    )
    non_blocking_gap_group_ids = sorted(
        group_id
        for group_id, group in metric_groups.items()
        if not group.get("blocking") and group.get("status") != "direct_eval_present"
    )
    return {
        "required_metric_group_ids": list(APPLICABILITY_EVAL_METRIC_GROUP_IDS),
        "missing_metric_group_ids": missing_group_ids,
        "metric_group_contract_passed": not missing_group_ids,
        "blocking_metric_group_ids": sorted(
            group_id
            for group_id, group in metric_groups.items()
            if group.get("blocking")
        ),
        "blocking_metric_group_failures": blocking_failures,
        "blocking_metric_groups_passed": not missing_group_ids and not blocking_failures,
        "non_blocking_gap_group_ids": non_blocking_gap_group_ids,
    }


def _hard_negative_results(case_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for case in case_results:
        tags = set(_strings(case.get("coverage_tags")))
        expected_statuses = case.get("expected_statuses") or {}
        all_expected_non_applicable = bool(expected_statuses) and all(
            status == "not_applicable" for status in expected_statuses.values()
        )
        if "negative_proof" not in tags and not all_expected_non_applicable:
            continue
        results.append(
            {
                "case_id": case.get("id"),
                "passed": bool(
                    case.get("passed")
                    and case.get("expected_non_applicable_authorities_match")
                    and not case.get("applicable_rule_ids")
                ),
                "applicable_rule_ids": case.get("applicable_rule_ids") or [],
                "non_applicable_rule_ids": case.get("non_applicable_rule_ids") or [],
                "failure_reasons": case.get("failure_reasons") or [],
            }
        )
    return results


def _group_failure_categories(
    failure_category_counts: dict[str, int],
    categories: set[str],
) -> dict[str, int]:
    return {
        category: count
        for category, count in sorted(failure_category_counts.items())
        if category in categories and count
    }


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
