from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from .upstream_evaluation_contracts import (
    _category_summaries,
    _lane_summaries,
    _markdown_report,
    _validate_manifest_contract,
)
from .upstream_evaluation_runners import _run_case
from .upstream_evaluation_support import (
    REPO_ROOT,
    _normalized_case_definitions,
    _read_json,
    _resolve_case_path,
    _resolve_path,
    _utc_now,
    _write_json,
)


DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH = REPO_ROOT / "config" / "upstream_evaluation_v1.json"
UPSTREAM_EVALUATION_RESULTS_SCHEMA_VERSION = "upstream-evaluation-results-v0"


@dataclass(frozen=True)
class UpstreamEvaluationResult:
    summary: dict
    output_path: Path
    report_path: Path


def run_upstream_evaluation(
    *,
    manifest_path: Path = DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH,
    output_dir: Path = Path("source_library"),
    results_dir: Path | None = None,
) -> UpstreamEvaluationResult:
    manifest_path = _resolve_path(manifest_path)
    output_dir = _resolve_path(output_dir)
    results_dir = _resolve_path(results_dir or output_dir / "evaluations" / "upstream")
    results_dir.mkdir(parents=True, exist_ok=True)

    manifest = _read_json(manifest_path)
    fixture_roots = [
        _resolve_case_path(manifest_path.parent, root) for root in manifest.get("fixture_roots", [])
    ]
    case_definitions = _normalized_case_definitions(
        manifest_dir=manifest_path.parent,
        case_definitions=sorted(
            manifest.get("cases", []),
            key=lambda item: item.get("case_id", ""),
        ),
    )

    contract_checks, output_expectations = _validate_manifest_contract(
        manifest_path=manifest_path,
        manifest=manifest,
        fixture_roots=fixture_roots,
        case_definitions=case_definitions,
    )

    fixture_cache: dict[Path, dict] = {}
    case_results = [
        _run_case(
            case_definition=case_definition,
            fixture_roots=fixture_roots,
            fixture_cache=fixture_cache,
        )
        for case_definition in case_definitions
    ]

    category_summaries = _category_summaries(
        required_lanes=manifest.get("required_lanes", []),
        case_results=case_results,
    )
    lane_summaries = _lane_summaries(
        required_lanes=manifest.get("required_lanes", []),
        category_summaries=category_summaries,
    )

    summary = {
        "schema_version": UPSTREAM_EVALUATION_RESULTS_SCHEMA_VERSION,
        "manifest_path": str(manifest_path),
        "results_dir": str(results_dir),
        "generated_at": _utc_now(),
        "passed": False,
        "required_lane_count": len(manifest.get("required_lanes", [])),
        "required_category_count": sum(
            len(lane.get("required_category_ids", []))
            for lane in manifest.get("required_lanes", [])
        ),
        "case_count": len(case_results),
        "expected_pass_case_count": sum(
            1 for case_result in case_results if case_result["case_type"] == "expected_pass"
        ),
        "controlled_violation_case_count": sum(
            1 for case_result in case_results if case_result["case_type"] == "controlled_violation"
        ),
        "matched_case_count": sum(
            1 for case_result in case_results if case_result["matched_expectation"]
        ),
        "failed_case_ids": [
            case_result["case_id"]
            for case_result in case_results
            if not case_result["matched_expectation"]
        ],
        "contract_checks": contract_checks,
        "lane_summaries": lane_summaries,
        "category_summaries": category_summaries,
        "cases": case_results,
    }

    output_field_check = {
        "name": "output_schema_fields_present",
        "passed": not [
            field for field in output_expectations if field not in summary and field != "passed"
        ],
        "details": {
            "required_fields": output_expectations,
            "missing_fields": [
                field for field in output_expectations if field not in summary and field != "passed"
            ],
        },
    }
    summary["contract_checks"].append(output_field_check)
    summary["passed"] = all(check["passed"] for check in summary["contract_checks"]) and all(
        case_result["matched_expectation"] for case_result in case_results
    )

    output_path = results_dir / "upstream_evaluation_results.json"
    report_path = results_dir / "upstream_evaluation_report.md"
    summary["output_path"] = str(output_path)
    summary["report_path"] = str(report_path)
    _write_json(output_path, summary)
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    return UpstreamEvaluationResult(summary=summary, output_path=output_path, report_path=report_path)
