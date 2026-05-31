from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .extraction_fidelity_eval_runtime import run_extraction_fidelity_case
from .upstream_evaluation_support import (
    REPO_ROOT,
    _is_within,
    _normalized_case_definitions,
    _read_json,
    _resolve_case_path,
    _resolve_path,
    _utc_now,
    _write_json,
)


DEFAULT_EXTRACTION_FIDELITY_EVAL_MANIFEST_PATH = (
    REPO_ROOT / "config" / "extraction_fidelity_eval_v1.json"
)
EXTRACTION_FIDELITY_EVAL_RESULTS_SCHEMA_VERSION = "extraction-fidelity-eval-results-v0"


@dataclass(frozen=True)
class ExtractionFidelityEvalResult:
    summary: dict
    output_path: Path
    report_path: Path


def run_extraction_fidelity_eval(
    *,
    manifest_path: Path = DEFAULT_EXTRACTION_FIDELITY_EVAL_MANIFEST_PATH,
    output_dir: Path = Path("source_library"),
    results_dir: Path | None = None,
) -> ExtractionFidelityEvalResult:
    manifest_path = _resolve_path(manifest_path)
    output_dir = _resolve_path(output_dir)
    results_dir = _resolve_path(
        results_dir or output_dir / "evaluations" / "extraction_fidelity"
    )
    results_dir.mkdir(parents=True, exist_ok=True)

    manifest = _read_json(manifest_path)
    fixture_roots = [
        _resolve_case_path(manifest_path.parent, root) for root in manifest.get("fixture_roots", [])
    ]
    case_definitions = _normalized_case_definitions(
        manifest_dir=manifest_path.parent,
        case_definitions=sorted(manifest.get("cases", []), key=lambda item: item.get("case_id", "")),
    )
    category_definitions = {
        str(category.get("category_id") or ""): dict(category)
        for category in manifest.get("required_categories", [])
    }

    contract_checks, output_expectations = _validate_manifest_contract(
        manifest_path=manifest_path,
        manifest=manifest,
        fixture_roots=fixture_roots,
        case_definitions=case_definitions,
        category_definitions=category_definitions,
    )

    fixture_cache: dict[Path, dict] = {}
    case_results = [
        run_extraction_fidelity_case(
            case_definition=case_definition,
            category_definition=category_definitions.get(str(case_definition.get("category_id") or ""), {}),
            fixture_roots=fixture_roots,
            fixture_cache=fixture_cache,
        )
        for case_definition in case_definitions
    ]

    category_summaries = _category_summaries(
        manifest=manifest,
        case_results=case_results,
        category_definitions=category_definitions,
    )

    summary = {
        "schema_version": EXTRACTION_FIDELITY_EVAL_RESULTS_SCHEMA_VERSION,
        "manifest_path": str(manifest_path),
        "results_dir": str(results_dir),
        "generated_at": _utc_now(),
        "passed": False,
        "required_category_count": len(category_definitions),
        "case_count": len(case_results),
        "expected_pass_case_count": sum(
            1 for case_result in case_results if case_result["case_type"] == "expected_pass"
        ),
        "controlled_violation_case_count": sum(
            1
            for case_result in case_results
            if case_result["case_type"] == "controlled_violation"
        ),
        "matched_case_count": sum(
            1 for case_result in case_results if case_result["matched_expectation"]
        ),
        "failed_case_ids": [
            case_result["case_id"]
            for case_result in case_results
            if not case_result["matched_expectation"]
        ],
        "parser_route_mismatch_count": sum(
            int(case_result["details"].get("parser_route_mismatch_count", 0))
            for case_result in case_results
        ),
        "anchor_mismatch_count": sum(
            int(case_result["details"].get("anchor_mismatch_count", 0))
            for case_result in case_results
        ),
        "span_mismatch_count": sum(
            int(case_result["details"].get("span_mismatch_count", 0))
            for case_result in case_results
        ),
        "boundary_mismatch_count": sum(
            int(case_result["details"].get("boundary_mismatch_count", 0))
            for case_result in case_results
        ),
        "negative_case_pass_count": sum(
            1
            for case_result in case_results
            if case_result["case_type"] == "controlled_violation"
            and case_result["matched_expectation"]
        ),
        "negative_case_fail_count": sum(
            1
            for case_result in case_results
            if case_result["case_type"] == "controlled_violation"
            and not case_result["matched_expectation"]
        ),
        "required_check_mismatch_count": sum(
            int(case_result["details"].get("required_check_mismatch_count", 0))
            for case_result in case_results
        ),
        "contract_checks": contract_checks,
        "category_summaries": category_summaries,
        "cases": case_results,
    }

    summary["contract_checks"].append(
        _required_field_check(
            name="output_schema_fields_present",
            payload=summary,
            required_fields=output_expectations["summary_fields"],
        )
    )
    summary["contract_checks"].append(
        {
            "name": "category_summaries_match_output_schema",
            "passed": all(
                not missing
                for missing in (
                    _missing_required_fields(
                        category_summary,
                        output_expectations["category_summary_fields"],
                    )
                    for category_summary in category_summaries
                )
            ),
            "details": {
                "missing_fields": [
                    {
                        "category_id": category_summary.get("category_id"),
                        "missing_fields": missing,
                    }
                    for category_summary in category_summaries
                    if (
                        missing := _missing_required_fields(
                            category_summary,
                            output_expectations["category_summary_fields"],
                        )
                    )
                ],
            },
        }
    )
    summary["contract_checks"].append(
        {
            "name": "case_results_match_output_schema",
            "passed": all(
                not missing
                for missing in (
                    _missing_required_fields(
                        case_result,
                        output_expectations["case_fields"],
                    )
                    for case_result in case_results
                )
            ),
            "details": {
                "missing_fields": [
                    {
                        "case_id": case_result.get("case_id"),
                        "missing_fields": missing,
                    }
                    for case_result in case_results
                    if (
                        missing := _missing_required_fields(
                            case_result,
                            output_expectations["case_fields"],
                        )
                    )
                ],
            },
        }
    )

    summary["passed"] = all(check["passed"] for check in summary["contract_checks"]) and all(
        case_result["matched_expectation"] for case_result in case_results
    )

    output_path = results_dir / "extraction_fidelity_eval_results.json"
    report_path = results_dir / "extraction_fidelity_eval_report.md"
    summary["output_path"] = str(output_path)
    summary["report_path"] = str(report_path)
    _write_json(output_path, summary)
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    return ExtractionFidelityEvalResult(
        summary=summary,
        output_path=output_path,
        report_path=report_path,
    )


def _validate_manifest_contract(
    *,
    manifest_path: Path,
    manifest: dict,
    fixture_roots: list[Path],
    case_definitions: list[dict],
    category_definitions: dict[str, dict],
) -> tuple[list[dict], dict[str, list[str]]]:
    checks: list[dict] = []
    checks.append(
        {
            "name": "manifest_schema_version",
            "passed": manifest.get("schema_version") == "extraction-fidelity-eval-v1",
            "details": {
                "path": str(manifest_path),
                "actual": manifest.get("schema_version"),
                "expected": "extraction-fidelity-eval-v1",
            },
        }
    )

    category_ids = list(category_definitions)
    checks.append(
        {
            "name": "required_categories_are_unique",
            "passed": all(
                category_ids.count(category_id) == 1 for category_id in category_ids if category_id
            ),
            "details": {"category_ids": category_ids},
        }
    )

    case_ids = [str(case_definition.get("case_id") or "") for case_definition in case_definitions]
    checks.append(
        {
            "name": "case_ids_are_unique",
            "passed": len(set(case_ids)) == len(case_ids),
            "details": {"case_ids": case_ids},
        }
    )

    unknown_categories = []
    thin_categories = []
    invalid_case_shapes = []
    missing_fixtures = []
    out_of_tree_fixtures = []
    fixture_shape_errors = []
    case_count_by_category: Counter[tuple[str, str]] = Counter()

    for case_definition in case_definitions:
        case_id = str(case_definition.get("case_id") or "")
        category_id = str(case_definition.get("category_id") or "")
        case_type = str(case_definition.get("case_type") or "")
        scenario_id = str(case_definition.get("scenario_id") or "")
        expected = case_definition.get("expected_producer_passed")
        fixture_path = _resolve_path(case_definition.get("fixture_path"))

        if (
            not case_id
            or case_type not in {"expected_pass", "controlled_violation"}
            or not scenario_id
            or not isinstance(expected, bool)
        ):
            invalid_case_shapes.append(case_id or "<missing-case-id>")

        if category_id not in category_definitions:
            unknown_categories.append({"case_id": case_id, "category_id": category_id})
            continue
        case_count_by_category[(category_id, case_type)] += 1

        if not fixture_path.exists():
            missing_fixtures.append(str(fixture_path))
            continue
        if fixture_roots and not any(_is_within(fixture_path, root) for root in fixture_roots):
            out_of_tree_fixtures.append(str(fixture_path))
            continue

        fixture_shape_errors.extend(
            _validate_fixture_shape(
                fixture_path=fixture_path,
                category_definition=category_definitions[category_id],
                scenario_id=scenario_id,
                category_id=category_id,
            )
        )

    for category_id, category_definition in category_definitions.items():
        expected_pass_count = case_count_by_category[(category_id, "expected_pass")]
        controlled_violation_count = case_count_by_category[
            (category_id, "controlled_violation")
        ]
        minimum_expected = int(category_definition.get("minimum_expected_pass_cases", 1))
        minimum_controlled = int(
            category_definition.get("minimum_controlled_violation_cases", 1)
        )
        if (
            expected_pass_count < minimum_expected
            or controlled_violation_count < minimum_controlled
        ):
            thin_categories.append(
                {
                    "category_id": category_id,
                    "expected_pass_case_count": expected_pass_count,
                    "controlled_violation_case_count": controlled_violation_count,
                    "minimum_expected_pass_cases": minimum_expected,
                    "minimum_controlled_violation_cases": minimum_controlled,
                }
            )

    checks.extend(
        [
            {
                "name": "cases_reference_required_categories",
                "passed": not unknown_categories,
                "details": {"unknown_category_cases": unknown_categories},
            },
            {
                "name": "required_categories_have_expected_and_controlled_cases",
                "passed": not thin_categories,
                "details": {"thin_categories": thin_categories},
            },
            {
                "name": "fixture_paths_are_in_tracked_roots",
                "passed": not out_of_tree_fixtures,
                "details": {
                    "fixture_roots": [str(root) for root in fixture_roots],
                    "out_of_tree_fixture_paths": out_of_tree_fixtures,
                },
            },
            {
                "name": "fixture_paths_exist",
                "passed": not missing_fixtures,
                "details": {"missing_fixture_paths": missing_fixtures},
            },
            {
                "name": "case_definitions_are_well_formed",
                "passed": not invalid_case_shapes,
                "details": {"invalid_case_ids": invalid_case_shapes},
            },
            {
                "name": "fixture_scenarios_match_required_expectation_fields",
                "passed": not fixture_shape_errors,
                "details": {"shape_errors": fixture_shape_errors},
            },
        ]
    )

    output_schema = manifest.get("output_schema") or {}
    return checks, {
        "summary_fields": [
            str(field) for field in output_schema.get("required_summary_fields", [])
        ],
        "category_summary_fields": [
            str(field) for field in output_schema.get("required_category_summary_fields", [])
        ],
        "case_fields": [str(field) for field in output_schema.get("required_case_fields", [])],
    }


def _validate_fixture_shape(
    *,
    fixture_path: Path,
    category_definition: dict,
    scenario_id: str,
    category_id: str,
) -> list[dict]:
    payload = _read_json(fixture_path)
    errors = []
    if payload.get("runner") != "extraction_build":
        errors.append(
            _shape_error(
                fixture_path,
                category_id,
                scenario_id,
                reason="runner_must_be_extraction_build",
                actual=payload.get("runner"),
            )
        )
        return errors
    if payload.get("category_id") != category_id:
        errors.append(
            _shape_error(
                fixture_path,
                category_id,
                scenario_id,
                reason="fixture_category_mismatch",
                actual=payload.get("category_id"),
            )
        )

    scenario = (payload.get("scenarios") or {}).get(scenario_id)
    if not isinstance(scenario, dict):
        errors.append(_shape_error(fixture_path, category_id, scenario_id, reason="missing_scenario"))
        return errors

    if not str(scenario.get("source_record_id") or ""):
        errors.append(_shape_error(fixture_path, category_id, scenario_id, reason="missing_source_record_id"))
    if not isinstance(scenario.get("download_run"), dict):
        errors.append(_shape_error(fixture_path, category_id, scenario_id, reason="missing_download_run"))
    if scenario.get("workbook") is None and scenario.get("workbook_path") is None:
        errors.append(_shape_error(fixture_path, category_id, scenario_id, reason="missing_workbook_surface"))

    for field_name in category_definition.get("required_expectation_fields", []):
        validator = _FIELD_VALIDATORS[field_name]
        for reason in validator(scenario.get(field_name)):
            errors.append(
                _shape_error(
                    fixture_path,
                    category_id,
                    scenario_id,
                    reason=reason,
                    field_name=field_name,
                )
            )
    return errors


def _category_summaries(
    *,
    manifest: dict,
    case_results: list[dict],
    category_definitions: dict[str, dict],
) -> list[dict]:
    cases_by_category: dict[str, list[dict]] = {}
    for case_result in case_results:
        category_id = str(case_result.get("category_id") or "")
        cases_by_category.setdefault(category_id, []).append(case_result)

    summaries = []
    for category in manifest.get("required_categories", []):
        category_id = str(category.get("category_id") or "")
        category_cases = cases_by_category.get(category_id, [])
        failing_case_ids = [
            case_result["case_id"]
            for case_result in category_cases
            if not case_result["matched_expectation"]
        ]
        metric_outcomes = {}
        for metric_id in category_definitions.get(category_id, {}).get("required_metric_ids", []):
            present_metric_results = [
                case_result["details"].get("metric_results", {}).get(metric_id)
                for case_result in category_cases
            ]
            present_metric_results = [
                metric_result
                for metric_result in present_metric_results
                if isinstance(metric_result, dict)
            ]
            metric_outcomes[metric_id] = {
                "case_result_count": len(present_metric_results),
                "passed_case_count": sum(
                    1 for metric_result in present_metric_results if metric_result["passed"]
                ),
                "failed_case_count": sum(
                    1 for metric_result in present_metric_results if not metric_result["passed"]
                ),
            }
        summaries.append(
            {
                "category_id": category_id,
                "required_metric_ids": list(category.get("required_metric_ids", [])),
                "route_identity_load_bearing": bool(
                    category.get("route_identity_load_bearing", False)
                ),
                "case_count": len(category_cases),
                "expected_pass_case_count": sum(
                    1 for case_result in category_cases if case_result["case_type"] == "expected_pass"
                ),
                "controlled_violation_case_count": sum(
                    1
                    for case_result in category_cases
                    if case_result["case_type"] == "controlled_violation"
                ),
                "matched_case_count": sum(
                    1 for case_result in category_cases if case_result["matched_expectation"]
                ),
                "passed": bool(category_cases) and not failing_case_ids,
                "status": "direct_eval_present"
                if category_cases and not failing_case_ids
                else "direct_eval_missing",
                "failing_case_ids": failing_case_ids,
                "parser_route_mismatch_count": sum(
                    int(case_result["details"].get("parser_route_mismatch_count", 0))
                    for case_result in category_cases
                ),
                "anchor_mismatch_count": sum(
                    int(case_result["details"].get("anchor_mismatch_count", 0))
                    for case_result in category_cases
                ),
                "span_mismatch_count": sum(
                    int(case_result["details"].get("span_mismatch_count", 0))
                    for case_result in category_cases
                ),
                "boundary_mismatch_count": sum(
                    int(case_result["details"].get("boundary_mismatch_count", 0))
                    for case_result in category_cases
                ),
                "negative_case_pass_count": sum(
                    1
                    for case_result in category_cases
                    if case_result["case_type"] == "controlled_violation"
                    and case_result["matched_expectation"]
                ),
                "negative_case_fail_count": sum(
                    1
                    for case_result in category_cases
                    if case_result["case_type"] == "controlled_violation"
                    and not case_result["matched_expectation"]
                ),
                "metric_outcomes": metric_outcomes,
            }
        )
    return summaries


def _markdown_report(summary: dict) -> str:
    lines = [
        "# Extraction Fidelity Eval",
        "",
        f"- Passed: `{summary['passed']}`",
        f"- Manifest: `{summary['manifest_path']}`",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Required categories: `{summary['required_category_count']}`",
        f"- Cases: `{summary['case_count']}`",
        f"- Matched expectations: `{summary['matched_case_count']}`",
        f"- Parser-route mismatches: `{summary['parser_route_mismatch_count']}`",
        f"- Anchor mismatches: `{summary['anchor_mismatch_count']}`",
        f"- Span mismatches: `{summary['span_mismatch_count']}`",
        f"- Boundary mismatches: `{summary['boundary_mismatch_count']}`",
        f"- Negative-case outcomes: `{summary['negative_case_pass_count']}` pass / `{summary['negative_case_fail_count']}` fail",
        "",
        "## Categories",
        "",
        "| Category | Status | Matched | Parser | Anchor | Span | Boundary | Negative |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for category_summary in summary["category_summaries"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    category_summary["category_id"],
                    category_summary["status"],
                    f"{category_summary['matched_case_count']}/{category_summary['case_count']}",
                    str(category_summary["parser_route_mismatch_count"]),
                    str(category_summary["anchor_mismatch_count"]),
                    str(category_summary["span_mismatch_count"]),
                    str(category_summary["boundary_mismatch_count"]),
                    (
                        f"{category_summary['negative_case_pass_count']}/"
                        f"{category_summary['controlled_violation_case_count']}"
                    ),
                ]
            )
            + " |"
        )

    failed_case_ids = summary.get("failed_case_ids", [])
    lines.extend(["", "## Failed Cases", ""])
    if not failed_case_ids:
        lines.append("- None.")
    else:
        lines.extend(f"- `{case_id}`" for case_id in failed_case_ids)

    failed_contract_checks = [
        check for check in summary.get("contract_checks", []) if not check.get("passed")
    ]
    lines.extend(["", "## Contract Checks", ""])
    if not failed_contract_checks:
        lines.append("- All contract checks passed.")
    else:
        for check in failed_contract_checks:
            lines.append(f"- `{check['name']}`")
    return "\n".join(lines) + "\n"


def _required_field_check(*, name: str, payload: dict, required_fields: list[str]) -> dict:
    return {
        "name": name,
        "passed": not _missing_required_fields(payload, required_fields),
        "details": {
            "required_fields": required_fields,
            "missing_fields": _missing_required_fields(payload, required_fields),
        },
    }


def _missing_required_fields(payload: dict, required_fields: list[str]) -> list[str]:
    return [field for field in required_fields if field not in payload]


def _shape_error(
    fixture_path: Path,
    category_id: str,
    scenario_id: str,
    *,
    reason: str,
    field_name: str | None = None,
    actual: object | None = None,
) -> dict:
    payload = {
        "fixture_path": str(fixture_path),
        "category_id": category_id,
        "scenario_id": scenario_id,
        "reason": reason,
    }
    if field_name is not None:
        payload["field_name"] = field_name
    if actual is not None:
        payload["actual"] = actual
    return payload


def _validate_text_anchors(value: object) -> list[str]:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item for item in value
    ):
        return ["invalid_required_text_anchors"]
    return []


def _validate_parser_name(value: object) -> list[str]:
    if not isinstance(value, str) or not value:
        return ["invalid_expected_parser_name"]
    return []


def _validate_table_rows(value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["invalid_expected_table_rows"]
    for row in value:
        cells = row.get("cells") if isinstance(row, dict) else None
        if not isinstance(cells, list) or len(cells) < 2 or any(
            not isinstance(cell, str) or not cell for cell in cells
        ):
            return ["invalid_expected_table_rows"]
    return []


def _validate_boundary_pairs(value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["invalid_required_boundary_pairs"]
    for pair in value:
        if not isinstance(pair, dict):
            return ["invalid_required_boundary_pairs"]
        if not isinstance(pair.get("start_anchor"), str) or not pair.get("start_anchor"):
            return ["invalid_required_boundary_pairs"]
        if not isinstance(pair.get("end_anchor"), str) or not pair.get("end_anchor"):
            return ["invalid_required_boundary_pairs"]
    return []


def _validate_forbidden_anchors(value: object) -> list[str]:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item for item in value
    ):
        return ["invalid_forbidden_text_anchors"]
    return []


def _validate_source_scope(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["invalid_expected_source_scope"]
    if not isinstance(value.get("type"), str) or not value.get("type"):
        return ["invalid_expected_source_scope"]
    if not isinstance(value.get("identifier"), str) or not value.get("identifier"):
        return ["invalid_expected_source_scope"]
    return []


def _validate_check_outcomes(value: object) -> list[str]:
    if not isinstance(value, dict) or not value:
        return ["invalid_required_check_outcomes"]
    if any(not isinstance(expected, bool) for expected in value.values()):
        return ["invalid_required_check_outcomes"]
    return []


_FIELD_VALIDATORS = {
    "required_text_anchors": _validate_text_anchors,
    "expected_parser_name": _validate_parser_name,
    "expected_table_rows": _validate_table_rows,
    "required_boundary_pairs": _validate_boundary_pairs,
    "forbidden_text_anchors": _validate_forbidden_anchors,
    "expected_source_scope": _validate_source_scope,
    "required_check_outcomes": _validate_check_outcomes,
}
