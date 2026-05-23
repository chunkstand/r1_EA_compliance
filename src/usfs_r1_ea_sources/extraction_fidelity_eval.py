from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .catalog import build_review_catalog
from .config import DEFAULT_CONFIG_PATH, LEGACY_WORKBOOK_LOADER_CONTRACT
from .extract import _clean_text
from .extract import build_extraction
from .extraction_accuracy import run_extraction_accuracy_audit
from .upstream_evaluation_fixture_support import (
    _apply_extraction_mutations,
    _scenario_workbook_path,
    _write_download_run,
)
from .upstream_evaluation_support import (
    REPO_ROOT,
    VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION,
    _check_outcome,
    _failed_check_names,
    _is_within,
    _normalized_case_definitions,
    _read_json,
    _read_jsonl,
    _resolve_case_path,
    _resolve_path,
    _utc_now,
    _upstream_eval_config,
    _write_json,
)


DEFAULT_EXTRACTION_FIDELITY_EVAL_MANIFEST_PATH = (
    REPO_ROOT / "config" / "extraction_fidelity_eval_v1.json"
)
EXTRACTION_FIDELITY_EVAL_RESULTS_SCHEMA_VERSION = "extraction-fidelity-eval-results-v0"
_NON_LOAD_BEARING_METRIC_IDS = {
    "negative_case_match_rate",
    "required_check_match_rate",
}


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
        _run_case(
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


def _run_case(
    *,
    case_definition: dict,
    category_definition: dict,
    fixture_roots: list[Path],
    fixture_cache: dict[Path, dict],
) -> dict:
    case_id = str(case_definition.get("case_id") or "")
    category_id = str(case_definition.get("category_id") or "")
    case_type = str(case_definition.get("case_type") or "")
    fixture_path = _resolve_path(case_definition.get("fixture_path"))
    scenario_id = str(case_definition.get("scenario_id") or "")
    expected_producer_passed = bool(case_definition.get("expected_producer_passed"))

    try:
        if fixture_roots and not any(_is_within(fixture_path, root) for root in fixture_roots):
            raise ValueError(f"Fixture path is outside tracked fixture roots: {fixture_path}")
        fixture_payload = fixture_cache.setdefault(fixture_path, _read_json(fixture_path))
        scenario = (fixture_payload.get("scenarios") or {}).get(scenario_id)
        if not isinstance(scenario, dict):
            raise ValueError(f"Fixture {fixture_path} is missing scenario {scenario_id}")
        actual_producer_passed, assertion_passed, details = _run_extraction_case(
            scenario=scenario,
            case_type=case_type,
            category_definition=category_definition,
        )
        error = None
    except Exception as exc:  # noqa: BLE001
        actual_producer_passed = False
        assertion_passed = False
        details = {}
        error = {"error_class": type(exc).__name__, "error_message": str(exc)}

    matched_expectation = (
        actual_producer_passed == expected_producer_passed and assertion_passed and error is None
    )
    return {
        "case_id": case_id,
        "category_id": category_id,
        "case_type": case_type,
        "fixture_path": str(fixture_path),
        "scenario_id": scenario_id,
        "expected_producer_passed": expected_producer_passed,
        "actual_producer_passed": actual_producer_passed,
        "assertion_passed": assertion_passed,
        "matched_expectation": matched_expectation,
        "details": details,
        "error": error,
    }


def _run_extraction_case(
    *,
    scenario: dict,
    case_type: str,
    category_definition: dict,
) -> tuple[bool, bool, dict]:
    config = _upstream_eval_config(
        loader_contract=str(scenario.get("loader_contract") or LEGACY_WORKBOOK_LOADER_CONTRACT)
    )
    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        output_dir = tmp_dir / "source_library"
        workbook_path = _scenario_workbook_path(tmp_dir, scenario)
        source_record_id = str(scenario["source_record_id"])

        _write_download_run(output_dir=output_dir, scenario=scenario["download_run"])
        build_review_catalog(
            workbook_path=workbook_path,
            output_dir=output_dir,
            config=config,
            config_path=REPO_ROOT / DEFAULT_CONFIG_PATH,
            run_id=str(scenario["download_run"].get("run_id") or "extraction-fidelity"),
            source_record_ids={source_record_id},
        )
        extraction = build_extraction(output_dir=output_dir, id_filter=source_record_id)
        _apply_extraction_mutations(
            extraction_manifest_path=extraction.extraction_manifest_path,
            chunks_path=extraction.chunks_path,
            mutations=scenario.get("mutations") or [],
        )
        contract_path = output_dir / "verified_extraction_contract.json"
        _write_json(
            contract_path,
            {
                "schema_version": VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION,
                "contracts": [
                    {
                        "contract_id": source_record_id,
                        "required_source_record_ids": [source_record_id],
                        "require_direct_extraction": True,
                    }
                ],
            },
        )

        audit = run_extraction_accuracy_audit(
            output_dir=output_dir,
            contract_path=contract_path,
        )
        manifest_record = next(
            record
            for record in _read_jsonl(extraction.extraction_manifest_path)
            if str(record.get("source_record_id") or "") == source_record_id
        )
        chunks = [
            chunk
            for chunk in _read_jsonl(extraction.chunks_path)
            if str(chunk.get("source_record_id") or "") == source_record_id
        ]
        text = Path(manifest_record["text_path"]).read_text(encoding="utf-8").rstrip("\n")

        metric_results = _metric_results(
            scenario=scenario,
            manifest_record=manifest_record,
            text=text,
            audit_summary=audit.summary,
        )
        case_metric_results = {
            metric_id: metric_result
            for metric_id, metric_result in metric_results.items()
            if metric_id not in _NON_LOAD_BEARING_METRIC_IDS
        }
        actual_producer_passed = bool(audit.summary.get("passed")) and all(
            metric_result["passed"] for metric_result in case_metric_results.values()
        )
        if case_type == "controlled_violation":
            metric_results["negative_case_match_rate"] = {
                "passed": not actual_producer_passed,
                "actual": 1.0 if not actual_producer_passed else 0.0,
                "expected": 1.0,
            }

        required_check_result = metric_results.get("required_check_match_rate")
        assertion_passed = (
            bool(required_check_result["passed"]) if required_check_result is not None else True
        )

        details = {
            "source_record_id": source_record_id,
            "audit_passed": bool(audit.summary.get("passed")),
            "failed_checks": _failed_check_names(audit.summary),
            "actual_parser_name": str(manifest_record.get("parser_name") or ""),
            "expected_parser_name": scenario.get("expected_parser_name"),
            "text_char_count": len(text),
            "chunk_count": len(chunks),
            "actual_source_scope": _normalized_source_scope(
                (manifest_record.get("parser_metadata") or {}).get("source_scope")
            ),
            "expected_source_scope": _normalized_source_scope(
                scenario.get("expected_source_scope")
            ),
            "metric_results": metric_results,
            "parser_route_mismatch_count": int(
                not metric_results.get("parser_route_match", {"passed": True})["passed"]
            ),
            "anchor_mismatch_count": int(
                metric_results.get("anchor_match_rate", {}).get("missing_anchor_count", 0)
            )
            + int(
                metric_results.get("forbidden_anchor_absence_rate", {}).get(
                    "forbidden_anchor_present_count",
                    0,
                )
            ),
            "span_mismatch_count": _check_failure_count(
                audit.summary,
                "chunks_match_extracted_text_offsets",
            ),
            "boundary_mismatch_count": int(
                metric_results.get("boundary_pair_match_rate", {}).get(
                    "boundary_mismatch_count",
                    0,
                )
            ),
            "required_check_mismatch_count": int(
                metric_results.get("required_check_match_rate", {}).get(
                    "required_check_mismatch_count",
                    0,
                )
            ),
            "negative_case_passed": (
                not actual_producer_passed if case_type == "controlled_violation" else None
            ),
        }
        return actual_producer_passed, assertion_passed, details


def _metric_results(
    *,
    scenario: dict,
    manifest_record: dict,
    text: str,
    audit_summary: dict,
) -> dict[str, dict]:
    metric_results: dict[str, dict] = {}
    normalized_text = _clean_text(text)

    required_text_anchors = scenario.get("required_text_anchors") or []
    if required_text_anchors:
        missing_anchors = [
            anchor
            for anchor in required_text_anchors
            if _clean_text(anchor) not in normalized_text
        ]
        matched_anchor_count = len(required_text_anchors) - len(missing_anchors)
        metric_results["anchor_match_rate"] = {
            "passed": not missing_anchors,
            "actual": _rate(matched_anchor_count, len(required_text_anchors)),
            "expected": 1.0,
            "matched_anchor_count": matched_anchor_count,
            "required_anchor_count": len(required_text_anchors),
            "missing_anchor_count": len(missing_anchors),
            "missing_anchors": missing_anchors,
        }
        metric_results["missing_anchor_count"] = {
            "passed": not missing_anchors,
            "actual": len(missing_anchors),
            "expected": 0,
        }

    forbidden_text_anchors = scenario.get("forbidden_text_anchors") or []
    if forbidden_text_anchors:
        present_forbidden_anchors = [
            anchor
            for anchor in forbidden_text_anchors
            if _clean_text(anchor) in normalized_text
        ]
        absent_forbidden_anchor_count = len(forbidden_text_anchors) - len(present_forbidden_anchors)
        metric_results["forbidden_anchor_absence_rate"] = {
            "passed": not present_forbidden_anchors,
            "actual": _rate(absent_forbidden_anchor_count, len(forbidden_text_anchors)),
            "expected": 1.0,
            "forbidden_anchor_count": len(forbidden_text_anchors),
            "forbidden_anchor_present_count": len(present_forbidden_anchors),
            "present_forbidden_anchors": present_forbidden_anchors,
        }

    expected_parser_name = scenario.get("expected_parser_name")
    if expected_parser_name is not None:
        actual_parser_name = str(manifest_record.get("parser_name") or "")
        metric_results["parser_route_match"] = {
            "passed": actual_parser_name == str(expected_parser_name),
            "actual": actual_parser_name,
            "expected": str(expected_parser_name),
        }

    expected_table_rows = scenario.get("expected_table_rows") or []
    if expected_table_rows:
        missing_rows = []
        matched_row_count = 0
        for row in expected_table_rows:
            cells = [str(cell) for cell in row.get("cells", [])]
            if _table_row_present(normalized_text, cells):
                matched_row_count += 1
            else:
                missing_rows.append(cells)
        metric_results["table_row_match_rate"] = {
            "passed": not missing_rows,
            "actual": _rate(matched_row_count, len(expected_table_rows)),
            "expected": 1.0,
            "table_row_count": len(expected_table_rows),
            "matched_table_row_count": matched_row_count,
            "missing_table_row_count": len(missing_rows),
            "missing_table_rows": missing_rows,
        }
        metric_results["missing_table_row_count"] = {
            "passed": not missing_rows,
            "actual": len(missing_rows),
            "expected": 0,
        }

    required_boundary_pairs = scenario.get("required_boundary_pairs") or []
    if required_boundary_pairs:
        mismatches = []
        matched_pair_count = 0
        for pair in required_boundary_pairs:
            start_anchor = _clean_text(pair["start_anchor"])
            end_anchor = _clean_text(pair["end_anchor"])
            start_index = normalized_text.find(start_anchor)
            end_index = normalized_text.find(end_anchor)
            if start_index < 0 or end_index < 0:
                mismatches.append(
                    {
                        "start_anchor": pair["start_anchor"],
                        "end_anchor": pair["end_anchor"],
                        "reason": "missing_anchor",
                    }
                )
                continue
            if start_index >= end_index:
                mismatches.append(
                    {
                        "start_anchor": pair["start_anchor"],
                        "end_anchor": pair["end_anchor"],
                        "reason": "boundary_order_invalid",
                        "start_index": start_index,
                        "end_index": end_index,
                    }
                )
                continue
            matched_pair_count += 1
        metric_results["boundary_pair_match_rate"] = {
            "passed": not mismatches,
            "actual": _rate(matched_pair_count, len(required_boundary_pairs)),
            "expected": 1.0,
            "boundary_pair_count": len(required_boundary_pairs),
            "matched_boundary_pair_count": matched_pair_count,
            "boundary_mismatch_count": len(mismatches),
            "boundary_mismatches": mismatches,
        }
        metric_results["boundary_mismatch_count"] = {
            "passed": not mismatches,
            "actual": len(mismatches),
            "expected": 0,
        }

    expected_source_scope = scenario.get("expected_source_scope")
    if expected_source_scope is not None:
        actual_scope = _normalized_source_scope(
            (manifest_record.get("parser_metadata") or {}).get("source_scope")
        )
        normalized_expected_scope = _normalized_source_scope(expected_source_scope)
        scope_check = _check_outcome(audit_summary, "scoped_xml_text_matches_source_scope")
        metric_results["scope_match"] = {
            "passed": actual_scope == normalized_expected_scope and scope_check is True,
            "actual": actual_scope,
            "expected": normalized_expected_scope,
            "scope_audit_passed": scope_check,
        }

    required_check_outcomes = scenario.get("required_check_outcomes") or {}
    if required_check_outcomes:
        mismatches = []
        for check_name, expected_outcome in sorted(required_check_outcomes.items()):
            actual_outcome = _check_outcome(audit_summary, check_name)
            if actual_outcome != bool(expected_outcome):
                mismatches.append(
                    {
                        "check_name": check_name,
                        "actual": actual_outcome,
                        "expected": bool(expected_outcome),
                    }
                )
        matched_check_count = len(required_check_outcomes) - len(mismatches)
        metric_results["required_check_match_rate"] = {
            "passed": not mismatches,
            "actual": _rate(matched_check_count, len(required_check_outcomes)),
            "expected": 1.0,
            "required_check_count": len(required_check_outcomes),
            "matched_check_count": matched_check_count,
            "required_check_mismatch_count": len(mismatches),
            "required_check_mismatches": mismatches,
        }

    return metric_results


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


def _table_row_present(normalized_text: str, cells: list[str]) -> bool:
    normalized_cells = [_clean_text(cell) for cell in cells]
    candidates = [
        _clean_text(" | ".join(normalized_cells)),
        _clean_text(" ".join(normalized_cells)),
    ]
    if any(candidate and candidate in normalized_text for candidate in candidates):
        return True
    cursor = 0
    for cell in normalized_cells:
        index = normalized_text.find(cell, cursor)
        if index < 0:
            return False
        cursor = index + len(cell)
    return True


def _normalized_source_scope(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    scope_type = value.get("type")
    identifier = value.get("identifier")
    if not isinstance(scope_type, str) or not isinstance(identifier, str):
        return None
    return {
        "type": scope_type.lower(),
        "identifier": identifier,
    }


def _check_failure_count(summary: dict, check_name: str) -> int:
    for check in summary.get("checks", []):
        if check.get("name") != check_name:
            continue
        details = check.get("details") or {}
        failure_count = details.get("failure_count")
        if isinstance(failure_count, int):
            return failure_count
        failures = details.get("failures")
        if isinstance(failures, list):
            return len(failures)
        return 0
    return 0


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)
