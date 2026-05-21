from __future__ import annotations

from collections import Counter
from pathlib import Path

from .upstream_evaluation_support import _is_within, _resolve_path


def _validate_manifest_contract(
    *,
    manifest_path: Path,
    manifest: dict,
    fixture_roots: list[Path],
    case_definitions: list[dict],
) -> tuple[list[dict], list[str]]:
    checks: list[dict] = []
    checks.append(
        {
            "name": "manifest_schema_version",
            "passed": manifest.get("schema_version") == "upstream-evaluation-v1",
            "details": {
                "path": str(manifest_path),
                "actual": manifest.get("schema_version"),
                "expected": "upstream-evaluation-v1",
            },
        }
    )

    required_lanes = manifest.get("required_lanes", [])
    lane_ids = [str(lane.get("lane_id") or "") for lane in required_lanes]
    checks.append(
        {
            "name": "required_lanes_are_unique",
            "passed": all(lane_ids.count(lane_id) == 1 for lane_id in lane_ids if lane_id),
            "details": {"lane_ids": lane_ids},
        }
    )

    required_categories = {
        str(lane.get("lane_id")): {
            str(category_id) for category_id in lane.get("required_category_ids", [])
        }
        for lane in required_lanes
    }
    minimum_expected_cases = {
        str(lane.get("lane_id")): int(lane.get("minimum_expected_pass_cases_per_category", 1))
        for lane in required_lanes
    }
    minimum_controlled_cases = {
        str(lane.get("lane_id")): int(
            lane.get("minimum_controlled_violation_cases_per_category", 1)
        )
        for lane in required_lanes
    }

    case_keys = [
        (case.get("lane_id"), case.get("category_id"), case.get("case_id"))
        for case in case_definitions
    ]
    checks.append(
        {
            "name": "case_ids_are_unique",
            "passed": len({case_id for _, _, case_id in case_keys}) == len(case_definitions),
            "details": {"case_ids": [case.get("case_id") for case in case_definitions]},
        }
    )

    missing_categories = []
    thin_categories = []
    invalid_case_shapes = []
    out_of_tree_fixtures = []
    missing_fixtures = []
    case_count_by_category: dict[tuple[str, str, str], int] = Counter()

    for case in case_definitions:
        lane_id = str(case.get("lane_id") or "")
        category_id = str(case.get("category_id") or "")
        case_type = str(case.get("case_type") or "")
        fixture_path = _resolve_path(case.get("fixture_path"))
        case_id = str(case.get("case_id") or "")
        scenario_id = str(case.get("scenario_id") or "")
        expected = case.get("expected_producer_passed")

        if (
            not lane_id
            or not category_id
            or case_type not in {"expected_pass", "controlled_violation"}
            or not case_id
            or not scenario_id
            or not isinstance(expected, bool)
        ):
            invalid_case_shapes.append(case_id or "<missing-case-id>")

        if lane_id not in required_categories or category_id not in required_categories.get(
            lane_id, set()
        ):
            missing_categories.append(
                {
                    "lane_id": lane_id,
                    "category_id": category_id,
                    "case_id": case_id,
                }
            )

        if case_type and lane_id and category_id:
            case_count_by_category[(lane_id, category_id, case_type)] += 1

        if not fixture_path.exists():
            missing_fixtures.append(str(fixture_path))
        if fixture_roots and not any(_is_within(fixture_path, root) for root in fixture_roots):
            out_of_tree_fixtures.append(str(fixture_path))

    for lane_id, category_ids in required_categories.items():
        for category_id in sorted(category_ids):
            expected_count = case_count_by_category[(lane_id, category_id, "expected_pass")]
            controlled_count = case_count_by_category[
                (lane_id, category_id, "controlled_violation")
            ]
            if (
                expected_count < minimum_expected_cases[lane_id]
                or controlled_count < minimum_controlled_cases[lane_id]
            ):
                thin_categories.append(
                    {
                        "lane_id": lane_id,
                        "category_id": category_id,
                        "expected_pass_case_count": expected_count,
                        "controlled_violation_case_count": controlled_count,
                        "minimum_expected_pass_cases_per_category": minimum_expected_cases[lane_id],
                        "minimum_controlled_violation_cases_per_category": minimum_controlled_cases[
                            lane_id
                        ],
                    }
                )

    checks.extend(
        [
            {
                "name": "cases_reference_required_categories",
                "passed": not missing_categories,
                "details": {"invalid_case_categories": missing_categories},
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
        ]
    )

    output_expectations = [
        str(field)
        for field in (manifest.get("output_schema") or {}).get("required_summary_fields", [])
    ]
    return checks, output_expectations


def _category_summaries(*, required_lanes: list[dict], case_results: list[dict]) -> list[dict]:
    cases_by_category: dict[tuple[str, str], list[dict]] = {}
    for case_result in case_results:
        key = (case_result["lane_id"], case_result["category_id"])
        cases_by_category.setdefault(key, []).append(case_result)

    summaries = []
    for lane in required_lanes:
        lane_id = str(lane.get("lane_id") or "")
        for category_id in sorted(str(value) for value in lane.get("required_category_ids", [])):
            cases = cases_by_category.get((lane_id, category_id), [])
            failing_case_ids = [
                case_result["case_id"]
                for case_result in cases
                if not case_result["matched_expectation"]
            ]
            summaries.append(
                {
                    "lane_id": lane_id,
                    "category_id": category_id,
                    "case_count": len(cases),
                    "expected_pass_case_count": sum(
                        1 for case_result in cases if case_result["case_type"] == "expected_pass"
                    ),
                    "controlled_violation_case_count": sum(
                        1
                        for case_result in cases
                        if case_result["case_type"] == "controlled_violation"
                    ),
                    "matched_case_count": sum(
                        1 for case_result in cases if case_result["matched_expectation"]
                    ),
                    "passed": bool(cases) and not failing_case_ids,
                    "failing_case_ids": failing_case_ids,
                    "status": "direct_eval_present"
                    if cases and not failing_case_ids
                    else "direct_eval_missing",
                }
            )
    return summaries


def _lane_summaries(*, required_lanes: list[dict], category_summaries: list[dict]) -> list[dict]:
    summaries = []
    for lane in required_lanes:
        lane_id = str(lane.get("lane_id") or "")
        lane_categories = [
            summary for summary in category_summaries if summary["lane_id"] == lane_id
        ]
        failing_case_ids = sorted(
            {
                case_id
                for summary in lane_categories
                for case_id in summary.get("failing_case_ids", [])
            }
        )
        summaries.append(
            {
                "lane_id": lane_id,
                "register_rows": lane.get("register_rows", []),
                "category_count": len(lane_categories),
                "direct_eval_present_category_count": sum(
                    1 for summary in lane_categories if summary["status"] == "direct_eval_present"
                ),
                "passed": lane_categories and not failing_case_ids,
                "status": "direct_eval_present"
                if lane_categories and not failing_case_ids
                else "direct_eval_missing",
                "failing_case_ids": failing_case_ids,
            }
        )
    return summaries


def _markdown_report(summary: dict) -> str:
    lines = [
        "# Upstream Evaluation Report",
        "",
        f"- Passed: `{summary['passed']}`",
        (
            "- Contract checks passed: "
            f"`{sum(1 for check in summary['contract_checks'] if check['passed'])}/"
            f"{len(summary['contract_checks'])}`"
        ),
        f"- Cases matched expectation: `{summary['matched_case_count']}/{summary['case_count']}`",
        "",
        "## Lanes",
        "",
        "| Lane | Status | Direct Eval Categories | Failing Cases |",
        "| --- | --- | ---: | --- |",
    ]
    for lane_summary in summary["lane_summaries"]:
        failing_cases = ", ".join(lane_summary["failing_case_ids"]) or "none"
        lines.append(
            f"| `{lane_summary['lane_id']}` | `{lane_summary['status']}` | "
            f"{lane_summary['direct_eval_present_category_count']}/{lane_summary['category_count']} | "
            f"{failing_cases} |"
        )
    lines.extend(["", "## Failures", ""])
    if summary["failed_case_ids"]:
        for case_id in summary["failed_case_ids"]:
            lines.append(f"- `{case_id}`")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
