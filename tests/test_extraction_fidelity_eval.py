from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.extraction_fidelity_eval import run_extraction_fidelity_eval


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "extraction_fidelity_eval_v1.json"
MISSING_CATEGORY_MANIFEST = (
    ROOT / "tests" / "fixtures" / "extraction_fidelity_eval" / "missing_category_manifest.json"
)
OUT_OF_TREE_MANIFEST = (
    ROOT / "tests" / "fixtures" / "extraction_fidelity_eval" / "out_of_tree_fixture_manifest.json"
)


def test_extraction_fidelity_contract_rejects_missing_category_coverage() -> None:
    summary = _manifest_contract_summary(MISSING_CATEGORY_MANIFEST)

    assert summary["passed"] is False
    check = _check(summary, "required_categories_have_expected_and_controlled_cases")
    assert check["passed"] is False
    assert check["details"]["thin_categories"]


def test_extraction_fidelity_contract_rejects_out_of_tree_fixtures() -> None:
    summary = _manifest_contract_summary(OUT_OF_TREE_MANIFEST)

    assert summary["passed"] is False
    check = _check(summary, "fixture_paths_are_in_tracked_roots")
    assert check["passed"] is False
    assert check["details"]["out_of_tree_fixture_paths"]


def test_extraction_fidelity_real_manifest_covers_required_categories_and_fixture_shapes() -> None:
    summary = _manifest_contract_summary(MANIFEST)

    assert summary["passed"] is True
    assert summary["required_category_count"] == 12
    assert summary["case_count"] == 24
    assert summary["matched_case_count"] == 24
    assert all(check["passed"] for check in summary["contract_checks"])


def test_extraction_fidelity_eval_runs_real_manifest_and_writes_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_extraction_fidelity_eval(
            manifest_path=MANIFEST,
            results_dir=Path(tmp) / "extraction-fidelity",
        )

        assert result.summary["passed"] is True
        assert result.output_path.exists()
        assert result.report_path.exists()
        assert result.summary["required_category_count"] == 12
        assert result.summary["case_count"] == 24
        assert result.summary["matched_case_count"] == 24
        assert result.summary["parser_route_mismatch_count"] == 1
        assert result.summary["negative_case_pass_count"] == 12
        assert result.summary["negative_case_fail_count"] == 0
        assert all(check["passed"] for check in result.summary["contract_checks"])


def test_extraction_fidelity_eval_records_controlled_violation_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_extraction_fidelity_eval(
            manifest_path=MANIFEST,
            results_dir=Path(tmp) / "extraction-fidelity",
        )

    ocr_case = _case(result.summary, "ocr-anchor-controlled-violation")
    assert ocr_case["actual_producer_passed"] is False
    assert (
        ocr_case["details"]["metric_results"]["anchor_match_rate"]["missing_anchor_count"] > 0
    )

    boundary_case = _case(result.summary, "section-boundary-controlled-violation")
    assert boundary_case["actual_producer_passed"] is False
    assert (
        boundary_case["details"]["metric_results"]["boundary_pair_match_rate"][
            "boundary_mismatch_count"
        ]
        > 0
    )

    parser_case = _case(result.summary, "parser-route-identity-controlled-violation")
    assert parser_case["actual_producer_passed"] is False
    assert parser_case["details"]["metric_results"]["parser_route_match"]["passed"] is False

    scope_case = _case(result.summary, "statute-scope-controlled-violation")
    assert scope_case["actual_producer_passed"] is False
    assert scope_case["details"]["metric_results"]["scope_match"]["passed"] is False
    assert (
        scope_case["details"]["metric_results"]["forbidden_anchor_absence_rate"][
            "forbidden_anchor_present_count"
        ]
        > 0
    )

    wrapper_case = _case(result.summary, "direct-document-wrapper-controlled-violation")
    assert wrapper_case["actual_producer_passed"] is False
    assert (
        wrapper_case["details"]["metric_results"]["required_check_match_rate"]["passed"] is True
    )
    assert wrapper_case["details"]["negative_case_passed"] is True


def _manifest_contract_summary(manifest_path: Path) -> dict:
    manifest = _read_json(manifest_path)
    fixture_roots = [
        _resolve_case_path(manifest_path.parent, root)
        for root in manifest.get("fixture_roots", [])
    ]
    cases = manifest.get("cases") or []
    required_categories = manifest.get("required_categories") or []
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

    category_ids = [str(category.get("category_id") or "") for category in required_categories]
    checks.append(
        {
            "name": "required_categories_are_unique",
            "passed": all(category_ids.count(category_id) == 1 for category_id in category_ids if category_id),
            "details": {"category_ids": category_ids},
        }
    )

    case_ids = [str(case.get("case_id") or "") for case in cases]
    checks.append(
        {
            "name": "case_ids_are_unique",
            "passed": len(set(case_ids)) == len(case_ids),
            "details": {"case_ids": case_ids},
        }
    )

    required_fields = set(
        (manifest.get("output_schema") or {}).get("required_summary_fields", [])
    )
    checks.append(
        {
            "name": "output_schema_declares_contract_summary_fields",
            "passed": {
                "schema_version",
                "passed",
                "contract_checks",
                "category_summaries",
                "cases",
            }.issubset(required_fields),
            "details": {"required_summary_fields": sorted(required_fields)},
        }
    )

    category_defs = {
        str(category.get("category_id")): category for category in required_categories
    }
    case_count_by_category: Counter[tuple[str, str]] = Counter()
    invalid_cases = []
    out_of_tree_fixtures = []
    missing_fixtures = []
    unknown_categories = []
    fixture_shape_errors = []

    for case in cases:
        category_id = str(case.get("category_id") or "")
        case_type = str(case.get("case_type") or "")
        fixture_path = _resolve_case_path(manifest_path.parent, case.get("fixture_path"))
        scenario_id = str(case.get("scenario_id") or "")
        expected = case.get("expected_producer_passed")

        if (
            not str(case.get("case_id") or "")
            or case_type not in {"expected_pass", "controlled_violation"}
            or not scenario_id
            or not isinstance(expected, bool)
        ):
            invalid_cases.append(str(case.get("case_id") or "<missing-case-id>"))
        if category_id not in category_defs:
            unknown_categories.append(
                {
                    "category_id": category_id,
                    "case_id": str(case.get("case_id") or ""),
                }
            )
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
                category=category_defs[category_id],
                scenario_id=scenario_id,
                category_id=category_id,
            )
        )

    thin_categories = []
    for category_id, category in category_defs.items():
        expected_pass_count = case_count_by_category[(category_id, "expected_pass")]
        controlled_count = case_count_by_category[(category_id, "controlled_violation")]
        minimum_expected = int(category.get("minimum_expected_pass_cases", 1))
        minimum_controlled = int(category.get("minimum_controlled_violation_cases", 1))
        if expected_pass_count < minimum_expected or controlled_count < minimum_controlled:
            thin_categories.append(
                {
                    "category_id": category_id,
                    "expected_pass_case_count": expected_pass_count,
                    "controlled_violation_case_count": controlled_count,
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
                "passed": not invalid_cases,
                "details": {"invalid_case_ids": invalid_cases},
            },
            {
                "name": "fixture_scenarios_match_required_expectation_fields",
                "passed": not fixture_shape_errors,
                "details": {"shape_errors": fixture_shape_errors},
            },
        ]
    )

    return {
        "schema_version": manifest.get("schema_version"),
        "required_category_count": len(required_categories),
        "case_count": len(cases),
        "matched_case_count": len(cases)
        - len(thin_categories)
        - len(out_of_tree_fixtures)
        - len(missing_fixtures)
        - len(invalid_cases)
        - len(unknown_categories)
        - len(fixture_shape_errors),
        "contract_checks": checks,
        "category_summaries": [
            {
                "category_id": category_id,
                "required_metric_ids": list(category.get("required_metric_ids", [])),
                "case_count": case_count_by_category[(category_id, "expected_pass")]
                + case_count_by_category[(category_id, "controlled_violation")],
                "expected_pass_case_count": case_count_by_category[(category_id, "expected_pass")],
                "controlled_violation_case_count": case_count_by_category[
                    (category_id, "controlled_violation")
                ],
                "matched_case_count": case_count_by_category[(category_id, "expected_pass")]
                + case_count_by_category[(category_id, "controlled_violation")],
                "passed": category_id not in {entry["category_id"] for entry in thin_categories},
                "status": "direct_eval_contract_present"
                if category_id not in {entry["category_id"] for entry in thin_categories}
                else "direct_eval_contract_missing",
            }
            for category_id, category in category_defs.items()
        ],
        "cases": cases,
        "passed": all(check["passed"] for check in checks),
    }


def _validate_fixture_shape(
    *,
    fixture_path: Path,
    category: dict,
    scenario_id: str,
    category_id: str,
) -> list[dict]:
    payload = _read_json(fixture_path)
    errors = []
    if payload.get("runner") != "extraction_build":
        errors.append(
            {
                "fixture_path": str(fixture_path),
                "category_id": category_id,
                "scenario_id": scenario_id,
                "reason": "runner_must_be_extraction_build",
                "actual": payload.get("runner"),
            }
        )
        return errors
    if payload.get("category_id") != category_id:
        errors.append(
            {
                "fixture_path": str(fixture_path),
                "category_id": category_id,
                "scenario_id": scenario_id,
                "reason": "fixture_category_mismatch",
                "actual": payload.get("category_id"),
            }
        )

    scenario = (payload.get("scenarios") or {}).get(scenario_id)
    if not isinstance(scenario, dict):
        errors.append(
            {
                "fixture_path": str(fixture_path),
                "category_id": category_id,
                "scenario_id": scenario_id,
                "reason": "missing_scenario",
            }
        )
        return errors

    if not str(scenario.get("source_record_id") or ""):
        errors.append(_shape_error(fixture_path, category_id, scenario_id, "missing_source_record_id"))
    if not isinstance(scenario.get("download_run"), dict):
        errors.append(_shape_error(fixture_path, category_id, scenario_id, "missing_download_run"))
    if scenario.get("workbook") is None and scenario.get("workbook_path") is None:
        errors.append(_shape_error(fixture_path, category_id, scenario_id, "missing_workbook_surface"))

    for field_name in category.get("required_expectation_fields", []):
        validator = _FIELD_VALIDATORS[field_name]
        field_errors = validator(scenario.get(field_name))
        for reason in field_errors:
            errors.append(_shape_error(fixture_path, category_id, scenario_id, reason, field_name))

    return errors


def _validate_text_anchors(value: object) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
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
        if not isinstance(cells, list) or len(cells) < 2 or any(not isinstance(cell, str) or not cell for cell in cells):
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
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
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


def _shape_error(
    fixture_path: Path,
    category_id: str,
    scenario_id: str,
    reason: str,
    field_name: str | None = None,
) -> dict:
    payload = {
        "fixture_path": str(fixture_path),
        "category_id": category_id,
        "scenario_id": scenario_id,
        "reason": reason,
    }
    if field_name is not None:
        payload["field_name"] = field_name
    return payload


def _check(summary: dict, name: str) -> dict:
    return next(check for check in summary["contract_checks"] if check["name"] == name)


def _case(summary: dict, case_id: str) -> dict:
    return next(case for case in summary["cases"] if case["case_id"] == case_id)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_case_path(base_dir: Path, relative_path: object) -> Path:
    return (base_dir / str(relative_path)).resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
