from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import re

from .eval_metrics import metric_threshold_check, rate


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_MANIFEST_PATH = (
    REPO_ROOT / "config" / "forest_plan_component_retrieval_eval_v1.json"
)
FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_SCHEMA_VERSION = (
    "forest-plan-component-retrieval-eval-v1"
)
FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-retrieval-eval-results-v1"
)
FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION = "forest-plan-component-inventory-v0"
TOKEN_RE = re.compile(r"[a-z0-9]+")
QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "area",
    "consistency",
    "forest",
    "for",
    "in",
    "is",
    "lands",
    "management",
    "on",
    "plan",
    "site",
    "sites",
    "the",
    "to",
    "with",
}
QUERY_GENERIC_TERMS = {
    "activity",
    "activities",
    "component",
    "components",
    "direction",
    "nfs",
    "policy",
    "project",
    "projects",
    "selected",
}


@dataclass(frozen=True)
class ForestPlanComponentRetrievalEvalResult:
    summary: dict[str, Any]
    output_path: Path
    report_path: Path


@dataclass(frozen=True)
class _RetrievalCase:
    case_id: str
    case_type: str
    description: str
    query: str
    expected_forest_unit_id: str | None
    expected_component_ids: tuple[str, ...]
    expected_component_family_ids: tuple[str, ...]
    applicable_standard_case: bool


def run_forest_plan_component_retrieval_eval(
    *,
    output_dir: Path = Path("source_library"),
    manifest_path: Path = DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> ForestPlanComponentRetrievalEvalResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    results_output_dir = (
        Path(results_dir)
        if results_dir is not None
        else output_dir / "evaluations" / "forest_plan_component_retrieval"
    )
    results_output_dir.mkdir(parents=True, exist_ok=True)

    manifest = _read_json(manifest_path)
    contract_checks, cases, output_expectations = _validate_manifest_contract(
        manifest_path=manifest_path,
        manifest=manifest,
    )
    source_set_id = str(manifest.get("source_set_id") or "").strip()
    expected_active_source_set_ids = _string_tuple(manifest.get("expected_active_source_set_ids"))
    coverage_requirements = manifest.get("coverage_requirements") or {}
    top_k = _coerce_positive_int((manifest.get("search_config") or {}).get("top_k")) or 3
    component_inventory_path = _resolve_component_inventory_path(
        manifest_path=manifest_path,
        manifest=manifest,
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    component_inventory_state = _load_component_inventory(
        component_inventory_path=component_inventory_path,
        source_set_id=source_set_id,
        expected_active_source_set_ids=expected_active_source_set_ids,
    )
    contract_checks.extend(component_inventory_state["contract_checks"])

    required_forest_unit_ids = _string_tuple(coverage_requirements.get("required_forest_unit_ids"))
    positive_cases = [case for case in cases if case.case_type == "expected_pass"]
    hard_negative_cases = [case for case in cases if case.case_type == "hard_negative"]
    covered_forest_unit_ids = sorted(
        {case.expected_forest_unit_id for case in positive_cases if case.expected_forest_unit_id}
    )
    contract_checks.extend(
        [
            {
                "name": "required_case_counts_present",
                "passed": (
                    len(positive_cases)
                    >= (_coerce_non_negative_int(coverage_requirements.get("minimum_expected_pass_case_count")) or 0)
                    and len(hard_negative_cases)
                    >= (_coerce_non_negative_int(coverage_requirements.get("minimum_hard_negative_case_count")) or 0)
                ),
                "details": {
                    "expected_pass_case_count": len(positive_cases),
                    "hard_negative_case_count": len(hard_negative_cases),
                    "minimum_expected_pass_case_count": _coerce_non_negative_int(
                        coverage_requirements.get("minimum_expected_pass_case_count")
                    ),
                    "minimum_hard_negative_case_count": _coerce_non_negative_int(
                        coverage_requirements.get("minimum_hard_negative_case_count")
                    ),
                },
            },
            {
                "name": "required_forest_units_covered",
                "passed": set(required_forest_unit_ids).issubset(set(covered_forest_unit_ids)),
                "details": {
                    "required_forest_unit_ids": list(required_forest_unit_ids),
                    "covered_forest_unit_ids": covered_forest_unit_ids,
                    "missing_forest_unit_ids": sorted(
                        set(required_forest_unit_ids) - set(covered_forest_unit_ids)
                    ),
                },
            },
            {
                "name": "component_inventory_contains_required_forests",
                "passed": set(required_forest_unit_ids).issubset(
                    set(component_inventory_state["forest_unit_ids"])
                ),
                "details": {
                    "required_forest_unit_ids": list(required_forest_unit_ids),
                    "inventory_forest_unit_ids": component_inventory_state["forest_unit_ids"],
                    "missing_forest_unit_ids": sorted(
                        set(required_forest_unit_ids)
                        - set(component_inventory_state["forest_unit_ids"])
                    ),
                },
            },
        ]
    )

    case_results = [
        _evaluate_case(
            case=case,
            component_records=component_inventory_state["component_records"],
            top_k=top_k,
        )
        for case in cases
    ]

    metrics = _metrics(case_results)
    metric_check = metric_threshold_check(manifest.get("metric_thresholds"), metrics)
    contract_checks.append(metric_check)

    output_path = results_output_dir / "forest_plan_component_retrieval_eval_results.json"
    report_path = results_output_dir / "forest_plan_component_retrieval_eval_report.md"
    summary = {
        "schema_version": FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "results_dir": str(results_output_dir),
        "output_path": str(output_path),
        "report_path": str(report_path),
        "contract_id": manifest.get("contract_id"),
        "contract_version": manifest.get("version"),
        "source_set_id": source_set_id,
        "expected_active_source_set_ids": list(expected_active_source_set_ids),
        "component_inventory_path": str(component_inventory_path),
        "top_k": top_k,
        "passed": False,
        "case_count": len(case_results),
        "expected_pass_case_count": len(positive_cases),
        "hard_negative_case_count": len(hard_negative_cases),
        "covered_forest_unit_ids": covered_forest_unit_ids,
        "required_forest_unit_ids": list(required_forest_unit_ids),
        "passed_case_count": sum(1 for result in case_results if result["passed"]),
        "failed_case_count": sum(1 for result in case_results if not result["passed"]),
        "failed_case_ids": [result["case_id"] for result in case_results if not result["passed"]],
        "selected_result_count": sum(result["selected_result_count"] for result in case_results),
        "metrics": metrics,
        "failure_category_counts": dict(
            sorted(
                Counter(
                    reason
                    for result in case_results
                    for reason in result["failure_reasons"]
                ).items()
            )
        ),
        "contract_checks": contract_checks,
        "cases": case_results,
    }
    summary["contract_checks"].append(
        {
            "name": "output_schema_fields_present",
            "passed": not [
                field for field in output_expectations if field not in summary and field != "passed"
            ],
            "details": {
                "required_fields": output_expectations,
                "missing_fields": [
                    field
                    for field in output_expectations
                    if field not in summary and field != "passed"
                ],
            },
        }
    )
    summary["passed"] = all(check["passed"] for check in summary["contract_checks"]) and all(
        result["passed"] for result in case_results
    )

    _write_json(output_path, summary)
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    return ForestPlanComponentRetrievalEvalResult(
        summary=summary,
        output_path=output_path,
        report_path=report_path,
    )


def _validate_manifest_contract(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[_RetrievalCase], list[str]]:
    contract_checks: list[dict[str, Any]] = [
        {
            "name": "manifest_schema_version",
            "passed": manifest.get("schema_version")
            == FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_SCHEMA_VERSION,
            "details": {
                "path": str(manifest_path),
                "expected": FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_SCHEMA_VERSION,
                "actual": manifest.get("schema_version"),
            },
        },
        {
            "name": "manifest_contract_id_present",
            "passed": bool(str(manifest.get("contract_id") or "").strip()),
            "details": {"contract_id": manifest.get("contract_id")},
        },
        {
            "name": "manifest_source_set_id_present",
            "passed": bool(str(manifest.get("source_set_id") or "").strip()),
            "details": {"source_set_id": manifest.get("source_set_id")},
        },
        {
            "name": "expected_active_source_set_ids_present",
            "passed": bool(_string_tuple(manifest.get("expected_active_source_set_ids"))),
            "details": {
                "expected_active_source_set_ids": list(
                    _string_tuple(manifest.get("expected_active_source_set_ids"))
                ),
            },
        },
    ]

    raw_cases = manifest.get("cases")
    cases: list[_RetrievalCase] = []
    invalid_cases: list[str] = []
    duplicate_case_ids: list[str] = []
    seen_case_ids: set[str] = set()
    if not isinstance(raw_cases, list):
        invalid_cases.append("cases")
        raw_cases = []
    for index, raw_case in enumerate(raw_cases):
        context = f"cases[{index}]"
        if not isinstance(raw_case, dict):
            invalid_cases.append(context)
            continue
        case_id = str(raw_case.get("case_id") or "").strip()
        case_type = str(raw_case.get("case_type") or "").strip()
        query = str(raw_case.get("query") or "").strip()
        expected_forest_unit_id = str(raw_case.get("expected_forest_unit_id") or "").strip() or None
        expected_component_ids = _string_tuple(raw_case.get("expected_component_ids"))
        expected_component_family_ids = _string_tuple(raw_case.get("expected_component_family_ids"))
        if not case_id or case_type not in {"expected_pass", "hard_negative"} or not query:
            invalid_cases.append(context)
            continue
        if case_id in seen_case_ids:
            duplicate_case_ids.append(case_id)
            continue
        seen_case_ids.add(case_id)
        if case_type == "expected_pass" and (
            expected_forest_unit_id is None
            or (not expected_component_ids and not expected_component_family_ids)
        ):
            invalid_cases.append(context)
            continue
        cases.append(
            _RetrievalCase(
                case_id=case_id,
                case_type=case_type,
                description=str(raw_case.get("description") or "").strip(),
                query=query,
                expected_forest_unit_id=expected_forest_unit_id,
                expected_component_ids=expected_component_ids,
                expected_component_family_ids=expected_component_family_ids,
                applicable_standard_case=bool(raw_case.get("applicable_standard_case")),
            )
        )

    contract_checks.extend(
        [
            {
                "name": "case_ids_are_unique",
                "passed": not duplicate_case_ids,
                "details": {"duplicate_case_ids": sorted(duplicate_case_ids)},
            },
            {
                "name": "manifest_cases_well_formed",
                "passed": not invalid_cases and bool(cases),
                "details": {"invalid_cases": invalid_cases, "case_count": len(cases)},
            },
        ]
    )

    top_k = _coerce_positive_int((manifest.get("search_config") or {}).get("top_k"))
    contract_checks.append(
        {
            "name": "search_top_k_is_positive",
            "passed": top_k is not None,
            "details": {"top_k": (manifest.get("search_config") or {}).get("top_k")},
        }
    )

    output_expectations = [
        str(field)
        for field in _string_tuple(
            (manifest.get("output_schema") or {}).get("required_summary_fields")
        )
    ]
    return contract_checks, cases, output_expectations


def _resolve_component_inventory_path(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    output_dir: Path,
    source_set_id: str,
) -> Path:
    raw_path = manifest.get("component_inventory_path")
    if isinstance(raw_path, Path):
        path = raw_path
    elif isinstance(raw_path, str) and raw_path.strip():
        path = Path(raw_path)
    else:
        return output_dir / "derived" / source_set_id / "forest_plan_components" / "component_inventory.json"
    return path if path.is_absolute() else (manifest_path.parent / path).resolve()


def _load_component_inventory(
    *,
    component_inventory_path: Path,
    source_set_id: str,
    expected_active_source_set_ids: tuple[str, ...],
) -> dict[str, Any]:
    if not component_inventory_path.exists():
        return {
            "component_records": [],
            "forest_unit_ids": [],
            "contract_checks": [
                {
                    "name": "component_inventory_path_exists",
                    "passed": False,
                    "details": {"path": str(component_inventory_path)},
                }
            ],
        }
    payload = _read_json(component_inventory_path)
    component_records = (
        payload.get("components")
        if isinstance(payload.get("components"), list)
        else []
    )
    actual_source_set_id = str(payload.get("source_set_id") or "").strip()
    forest_unit_ids = sorted(
        {
            str(component.get("forest_unit_id") or "").strip()
            for component in component_records
            if isinstance(component, dict) and str(component.get("forest_unit_id") or "").strip()
        }
    )
    return {
        "component_records": [
            _indexed_component_record(component)
            for component in component_records
            if isinstance(component, dict)
        ],
        "forest_unit_ids": forest_unit_ids,
        "contract_checks": [
            {
                "name": "component_inventory_path_exists",
                "passed": True,
                "details": {"path": str(component_inventory_path)},
            },
            {
                "name": "component_inventory_schema_version",
                "passed": payload.get("schema_version") == FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
                "details": {
                    "expected": FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION,
                    "actual": payload.get("schema_version"),
                },
            },
            {
                "name": "component_inventory_source_set_matches_manifest",
                "passed": actual_source_set_id == source_set_id,
                "details": {
                    "expected_source_set_id": source_set_id,
                    "actual_source_set_id": actual_source_set_id,
                },
            },
            {
                "name": "component_inventory_matches_expected_active_source_set",
                "passed": actual_source_set_id in set(expected_active_source_set_ids),
                "details": {
                    "expected_active_source_set_ids": list(expected_active_source_set_ids),
                    "actual_source_set_id": actual_source_set_id,
                },
            },
            {
                "name": "component_inventory_has_components",
                "passed": bool(component_records),
                "details": {"component_count": len(component_records)},
            },
        ],
    }


def _indexed_component_record(component: dict[str, Any]) -> dict[str, Any]:
    searchable_fields = {
        "package_evidence_terms": _string_list(component.get("package_evidence_terms")),
        "component_text": _string_list([component.get("component_text")]),
        "resource_topics": _string_list(component.get("resource_topics")),
        "activity_tags": _string_list(component.get("activity_tags")),
        "section_heading": _string_list([component.get("section_heading")]),
    }
    tokens_by_field = {
        field: _token_set(" ".join(values))
        for field, values in searchable_fields.items()
    }
    return {
        "component_id": str(component.get("component_id") or "").strip(),
        "forest_unit_id": str(component.get("forest_unit_id") or "").strip(),
        "component_type": str(component.get("component_type") or "").strip(),
        "searchable_fields": searchable_fields,
        "tokens_by_field": tokens_by_field,
    }


def _evaluate_case(
    *,
    case: _RetrievalCase,
    component_records: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    selected_results = _retrieve_components(
        query=case.query,
        component_records=component_records,
        top_k=top_k,
    )
    failure_reasons: list[str] = []
    selected_component_ids = [result["component_id"] for result in selected_results]
    if case.case_type == "hard_negative":
        if selected_results:
            failure_reasons.append("hard_negative_query_returned_components")
        return {
            "case_id": case.case_id,
            "case_type": case.case_type,
            "description": case.description,
            "query": case.query,
            "expected_forest_unit_id": case.expected_forest_unit_id,
            "expected_component_ids": list(case.expected_component_ids),
            "expected_component_family_ids": list(case.expected_component_family_ids),
            "applicable_standard_case": case.applicable_standard_case,
            "selected_result_count": len(selected_results),
            "selected_component_ids": selected_component_ids,
            "selected_results": selected_results,
            "relevant_selected_count": 0,
            "matched_expected_component_ids": [],
            "matched_expected_component_family_ids": [],
            "wrong_forest_selected_count": 0,
            "case_precision": 0.0 if selected_results else 1.0,
            "case_recall": 1.0,
            "passed": not failure_reasons,
            "failure_reasons": failure_reasons,
        }

    matched_component_ids: set[str] = set()
    matched_component_family_ids: set[str] = set()
    relevant_selected_count = 0
    wrong_forest_selected_count = 0
    for result in selected_results:
        if result["forest_unit_id"] != case.expected_forest_unit_id:
            wrong_forest_selected_count += 1
            continue
        matched_id = result["component_id"] in set(case.expected_component_ids)
        matched_families = {
            family_id
            for family_id in case.expected_component_family_ids
            if family_id in result["component_id"]
        }
        if matched_id or matched_families:
            relevant_selected_count += 1
            if matched_id:
                matched_component_ids.add(result["component_id"])
            matched_component_family_ids.update(matched_families)

    expected_target_count = len(case.expected_component_ids) + len(case.expected_component_family_ids)
    matched_target_count = len(matched_component_ids) + len(matched_component_family_ids)
    case_precision = rate(relevant_selected_count, len(selected_results))
    case_recall = rate(matched_target_count, expected_target_count)
    if not selected_results:
        failure_reasons.append("no_components_selected")
    if matched_target_count < expected_target_count:
        failure_reasons.append("expected_component_not_retrieved")
    if wrong_forest_selected_count > 0:
        failure_reasons.append("wrong_forest_component_selected")
    if case_precision < 1.0:
        failure_reasons.append("component_precision_below_case_floor")
    return {
        "case_id": case.case_id,
        "case_type": case.case_type,
        "description": case.description,
        "query": case.query,
        "expected_forest_unit_id": case.expected_forest_unit_id,
        "expected_component_ids": list(case.expected_component_ids),
        "expected_component_family_ids": list(case.expected_component_family_ids),
        "applicable_standard_case": case.applicable_standard_case,
        "selected_result_count": len(selected_results),
        "selected_component_ids": selected_component_ids,
        "selected_results": selected_results,
        "relevant_selected_count": relevant_selected_count,
        "matched_expected_component_ids": sorted(matched_component_ids),
        "matched_expected_component_family_ids": sorted(matched_component_family_ids),
        "wrong_forest_selected_count": wrong_forest_selected_count,
        "case_precision": case_precision,
        "case_recall": case_recall,
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


def _retrieve_components(
    *,
    query: str,
    component_records: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    query_tokens = _query_tokens(query)
    query_lower = query.strip().lower()
    if not query_tokens:
        return []
    ranked = []
    for component in component_records:
        score = _component_score(component=component, query_lower=query_lower, query_tokens=query_tokens)
        if score <= 0:
            continue
        ranked.append(
            {
                "component_id": component["component_id"],
                "forest_unit_id": component["forest_unit_id"],
                "component_type": component["component_type"],
                "score": round(score, 6),
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["forest_unit_id"], item["component_id"]))
    return ranked[:top_k]


def _component_score(
    *,
    component: dict[str, Any],
    query_lower: str,
    query_tokens: set[str],
) -> float:
    searchable_fields = component["searchable_fields"]
    tokens_by_field = component["tokens_by_field"]
    score = 0.0

    package_terms = searchable_fields["package_evidence_terms"]
    component_text = searchable_fields["component_text"]
    if any(query_lower == value.lower() for value in package_terms):
        score += 10.0
    elif any(query_lower in value.lower() for value in package_terms):
        score += 7.0

    if any(query_lower == value.lower() for value in component_text):
        score += 8.0
    elif any(query_lower in value.lower() for value in component_text):
        score += 5.0

    score += 4.0 * _overlap_ratio(query_tokens, tokens_by_field["package_evidence_terms"])
    score += 2.0 * _overlap_ratio(query_tokens, tokens_by_field["component_text"])
    score += 1.5 * _overlap_ratio(query_tokens, tokens_by_field["resource_topics"])
    score += 1.0 * _overlap_ratio(query_tokens, tokens_by_field["activity_tags"])
    score += 0.5 * _overlap_ratio(query_tokens, tokens_by_field["section_heading"])
    return score if score >= 1.0 else 0.0


def _metrics(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    positive_results = [result for result in case_results if result["case_type"] == "expected_pass"]
    hard_negative_results = [
        result for result in case_results if result["case_type"] == "hard_negative"
    ]
    expected_target_count = sum(
        len(result["expected_component_ids"]) + len(result["expected_component_family_ids"])
        for result in positive_results
    )
    matched_target_count = sum(
        len(result["matched_expected_component_ids"])
        + len(result["matched_expected_component_family_ids"])
        for result in positive_results
    )
    applicable_standard_results = [
        result for result in positive_results if result["applicable_standard_case"]
    ]
    applicable_expected_target_count = sum(
        len(result["expected_component_ids"]) + len(result["expected_component_family_ids"])
        for result in applicable_standard_results
    )
    applicable_matched_target_count = sum(
        len(result["matched_expected_component_ids"])
        + len(result["matched_expected_component_family_ids"])
        for result in applicable_standard_results
    )
    selected_result_count = sum(result["selected_result_count"] for result in positive_results)
    relevant_selected_count = sum(result["relevant_selected_count"] for result in positive_results)
    wrong_forest_selected_count = sum(
        result["wrong_forest_selected_count"] for result in positive_results
    )
    return {
        "case_count": len(case_results),
        "expected_pass_case_count": len(positive_results),
        "hard_negative_case_count": len(hard_negative_results),
        "component_retrieval_precision": rate(relevant_selected_count, selected_result_count),
        "component_retrieval_recall": rate(matched_target_count, expected_target_count),
        "applicable_standard_component_recall": rate(
            applicable_matched_target_count,
            applicable_expected_target_count,
        ),
        "wrong_forest_component_rate": rate(
            wrong_forest_selected_count,
            selected_result_count,
        ),
        "hard_negative_zero_match_rate": rate(
            sum(1 for result in hard_negative_results if result["selected_result_count"] == 0),
            len(hard_negative_results),
        ),
    }


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Forest Plan Component Retrieval Eval Report",
        "",
        f"- passed: `{summary['passed']}`",
        f"- source_set_id: `{summary['source_set_id']}`",
        f"- case_count: `{summary['case_count']}`",
        f"- expected_pass_case_count: `{summary['expected_pass_case_count']}`",
        f"- hard_negative_case_count: `{summary['hard_negative_case_count']}`",
        f"- component_retrieval_precision: `{summary['metrics']['component_retrieval_precision']}`",
        f"- component_retrieval_recall: `{summary['metrics']['component_retrieval_recall']}`",
        (
            "- applicable_standard_component_recall: "
            f"`{summary['metrics']['applicable_standard_component_recall']}`"
        ),
        f"- wrong_forest_component_rate: `{summary['metrics']['wrong_forest_component_rate']}`",
        f"- hard_negative_zero_match_rate: `{summary['metrics']['hard_negative_zero_match_rate']}`",
        "",
        "## Cases",
        "",
    ]
    for case in summary["cases"]:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                f"- passed: `{case['passed']}`",
                f"- case_type: `{case['case_type']}`",
                f"- query: `{case['query']}`",
                f"- selected_result_count: `{case['selected_result_count']}`",
                f"- failure_reasons: `{case['failure_reasons']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _token_set(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(text.lower())
        if token and token not in QUERY_STOPWORDS and token not in QUERY_GENERIC_TERMS
    }


def _query_tokens(query: str) -> set[str]:
    return _token_set(query)


def _overlap_ratio(query_tokens: set[str], candidate_tokens: set[str]) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens)
    if overlap <= 0:
        return 0.0
    return overlap / len(query_tokens)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_string_list(item))
        return items
    text = str(value).strip()
    return [text] if text else []


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(_string_list(value))


def _coerce_non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    return None


def _coerce_positive_int(value: Any) -> int | None:
    parsed = _coerce_non_negative_int(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
