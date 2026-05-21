from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .catalog import build_review_catalog
from .config import DEFAULT_CONFIG_PATH, LEGACY_WORKBOOK_LOADER_CONTRACT
from .dry_run import run_dry_run
from .extract import build_extraction
from .extraction_accuracy import run_extraction_accuracy_audit
from .preflight import _classify_response, run_preflight
from .upstream_evaluation_fixture_support import (
    _apply_extraction_mutations,
    _default_preflight_ok,
    _preflight_result_from_spec,
    _scenario_workbook_path,
    _supplemental_sources,
    _write_batch_runs,
    _write_download_run,
)
from .upstream_evaluation_support import (
    REPO_ROOT,
    VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION,
    _check_outcome,
    _failed_check_names,
    _read_json,
    _read_jsonl,
    _resolve_path,
    _upstream_eval_config,
    _write_json,
)
from .validate_run import validate_run


def _run_case(
    *,
    case_definition: dict,
    fixture_roots: list[Path],
    fixture_cache: dict[Path, dict],
) -> dict:
    case_id = str(case_definition.get("case_id") or "")
    fixture_path = _resolve_path(case_definition.get("fixture_path"))
    scenario_id = str(case_definition.get("scenario_id") or "")
    expected_producer_passed = bool(case_definition.get("expected_producer_passed"))

    try:
        if fixture_roots and not any(_is_within_fixture_root(fixture_path, root) for root in fixture_roots):
            raise ValueError(f"Fixture path is outside tracked fixture roots: {fixture_path}")
        fixture_payload = fixture_cache.setdefault(fixture_path, _read_json(fixture_path))
        runner_name = str(fixture_payload.get("runner") or "")
        scenarios = fixture_payload.get("scenarios") or {}
        scenario = scenarios.get(scenario_id)
        if not runner_name or not isinstance(scenario, dict):
            raise ValueError(f"Fixture {fixture_path} is missing runner or scenario {scenario_id}")
        runner = _RUNNERS.get(runner_name)
        if runner is None:
            raise ValueError(f"Unsupported upstream evaluation runner: {runner_name}")
        actual_producer_passed, assertion_passed, details = runner(scenario)
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
        "lane_id": str(case_definition.get("lane_id") or ""),
        "category_id": str(case_definition.get("category_id") or ""),
        "case_type": str(case_definition.get("case_type") or ""),
        "fixture_path": str(fixture_path),
        "scenario_id": scenario_id,
        "expected_producer_passed": expected_producer_passed,
        "actual_producer_passed": actual_producer_passed,
        "assertion_passed": assertion_passed,
        "matched_expectation": matched_expectation,
        "details": details,
        "error": error,
    }


def _run_capture_response_classification(scenario: dict) -> tuple[bool, bool, dict]:
    config = _upstream_eval_config()
    response = scenario["response"]
    classification = _classify_response(
        http_status=int(response["http_status"]),
        final_url=str(response["final_url"]),
        redirect_chain=[str(value) for value in response.get("redirect_chain", [])],
        content_type=str(response["content_type"]),
        content_length=int(response["content_length"]),
        method=str(response["method"]),
        attempt_count=int(response.get("attempt_count", 1)),
        body_sample=str(response["body_sample"]).encode("utf-8"),
        validation=config.validation,
    )
    recorded_result = scenario["recorded_result"]
    actual_producer_passed = (
        classification.status == str(recorded_result["status"])
        and bool(classification.validation.get("passed"))
        == bool(recorded_result["validation_passed"])
    )
    return actual_producer_passed, True, {
        "classification_status": classification.status,
        "classification_validation_passed": bool(classification.validation.get("passed")),
        "recorded_status": recorded_result["status"],
        "recorded_validation_passed": bool(recorded_result["validation_passed"]),
    }


def _run_capture_preflight(scenario: dict) -> tuple[bool, bool, dict]:
    config = _upstream_eval_config(
        loader_contract=str(scenario.get("loader_contract") or LEGACY_WORKBOOK_LOADER_CONTRACT)
    )
    with TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        workbook_path = _scenario_workbook_path(Path(tmp), scenario)
        fetch_results = {
            url: _preflight_result_from_spec(spec)
            for url, spec in (scenario.get("fetch_results") or {}).items()
        }

        def fetcher(url, network, validation):  # noqa: ANN001
            return fetch_results.get(url, _default_preflight_ok(url))

        result = run_preflight(
            workbook_path=workbook_path,
            output_dir=output_dir,
            config=config,
            run_id=str(scenario.get("run_id") or "upstream-preflight"),
            fetcher=fetcher,
            sleep_fn=lambda _: None,
        )
        records = _read_jsonl(result.manifest_path)
        assertions = scenario["assertions"]
        actual_producer_passed = (
            result.summary.get("checked_url_count") == assertions["checked_url_count"]
            and result.summary.get("duplicate_url_count") == assertions["duplicate_url_count"]
            and result.summary.get("filtered_rows") == assertions["filtered_rows"]
            and sum(1 for record in records if record.get("status") == "duplicate_url")
            == assertions["duplicate_record_count"]
            and all(
                record.get("duplicate_of")
                for record in records
                if record.get("status") == "duplicate_url"
            )
        )
        return actual_producer_passed, True, {
            "checked_url_count": result.summary.get("checked_url_count"),
            "duplicate_url_count": result.summary.get("duplicate_url_count"),
            "filtered_rows": result.summary.get("filtered_rows"),
            "duplicate_record_count": sum(
                1 for record in records if record.get("status") == "duplicate_url"
            ),
        }


def _run_capture_dry_run(scenario: dict) -> tuple[bool, bool, dict]:
    config = _upstream_eval_config(
        loader_contract=str(scenario.get("loader_contract") or LEGACY_WORKBOOK_LOADER_CONTRACT)
    )
    with TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        workbook_path = _scenario_workbook_path(Path(tmp), scenario)
        supplemental_sources = _supplemental_sources(
            scenario.get("supplemental_sources") or []
        )
        expected_error = str(scenario.get("expected_error_contains") or "")
        try:
            result = run_dry_run(
                workbook_path=workbook_path,
                output_dir=output_dir,
                config=config,
                run_id=str(scenario.get("run_id") or "upstream-dry-run"),
                supplemental_sources=supplemental_sources or None,
                source_delta_input=scenario.get("source_delta_input"),
            )
        except Exception as exc:  # noqa: BLE001
            details = {"error_class": type(exc).__name__, "error_message": str(exc)}
            if expected_error:
                return expected_error in str(exc), True, details
            raise

        records = _read_jsonl(result.manifest_path)
        if expected_error:
            return False, True, {
                "error_class": None,
                "error_message": None,
                "filtered_rows": result.summary.get("filtered_rows"),
                "sheet_names": sorted({record.get("sheet") for record in records}),
            }

        assertions = scenario.get("assertions") or {}
        actual_producer_passed = True
        if "filtered_rows" in assertions:
            actual_producer_passed = actual_producer_passed and (
                result.summary.get("filtered_rows") == assertions["filtered_rows"]
            )
        if "unique_canonical_urls" in assertions:
            actual_producer_passed = actual_producer_passed and (
                result.summary.get("unique_canonical_urls")
                == assertions["unique_canonical_urls"]
            )
        if "required_sheet_names" in assertions:
            actual_producer_passed = actual_producer_passed and (
                sorted({record.get("sheet") for record in records})
                == sorted(assertions["required_sheet_names"])
            )
        return actual_producer_passed, True, {
            "filtered_rows": result.summary.get("filtered_rows"),
            "unique_canonical_urls": result.summary.get("unique_canonical_urls"),
            "sheet_names": sorted({record.get("sheet") for record in records}),
        }


def _run_capture_validate_run(scenario: dict) -> tuple[bool, bool, dict]:
    with TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        _write_download_run(output_dir=output_dir, scenario=scenario)
        result = validate_run(
            output_dir=output_dir,
            run_id=str(scenario.get("run_id") or "upstream-validate-run"),
        )
        required_check_outcomes = scenario.get("required_check_outcomes") or {}
        assertion_passed = all(
            _check_outcome(result.report, check_name) == bool(expected)
            for check_name, expected in required_check_outcomes.items()
        )
        return result.passed, assertion_passed, {
            "validation_passed": result.passed,
            "required_check_outcomes": {
                check_name: _check_outcome(result.report, check_name)
                for check_name in required_check_outcomes
            },
            "failed_checks": _failed_check_names(result.report),
        }


def _run_catalog_build(scenario: dict) -> tuple[bool, bool, dict]:
    config = _upstream_eval_config(
        loader_contract=str(scenario.get("loader_contract") or LEGACY_WORKBOOK_LOADER_CONTRACT)
    )
    with TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        workbook_path = _scenario_workbook_path(Path(tmp), scenario)
        supplemental_sources = _supplemental_sources(
            scenario.get("supplemental_sources") or []
        )
        _write_batch_runs(output_dir=output_dir, batch_runs=scenario.get("batch_runs") or [])
        build_kwargs = dict(
            workbook_path=workbook_path,
            output_dir=output_dir,
            config=config,
            config_path=REPO_ROOT / DEFAULT_CONFIG_PATH,
            supplemental_sources=supplemental_sources or None,
            source_delta_input=scenario.get("source_delta_input"),
        )
        if scenario.get("batch_run_id"):
            build_kwargs["batch_run_id"] = str(scenario["batch_run_id"])
        if scenario.get("batch_run_ids"):
            build_kwargs["batch_run_ids"] = [str(value) for value in scenario["batch_run_ids"]]
        result = build_review_catalog(**build_kwargs)
        validation = _read_json(result.validation_path)
        required_check_outcomes = scenario.get("required_check_outcomes") or {}
        assertion_passed = all(
            _check_outcome(validation, check_name) == bool(expected)
            for check_name, expected in required_check_outcomes.items()
        )
        return bool(result.summary.get("validation_passed")), assertion_passed, {
            "validation_passed": bool(result.summary.get("validation_passed")),
            "required_check_outcomes": {
                check_name: _check_outcome(validation, check_name)
                for check_name in required_check_outcomes
            },
            "failed_checks": _failed_check_names(validation),
        }


def _run_extraction_build(scenario: dict) -> tuple[bool, bool, dict]:
    config = _upstream_eval_config(
        loader_contract=str(scenario.get("loader_contract") or LEGACY_WORKBOOK_LOADER_CONTRACT)
    )
    with TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        workbook_path = _scenario_workbook_path(Path(tmp), scenario)
        _write_download_run(output_dir=output_dir, scenario=scenario["download_run"])
        build_review_catalog(
            workbook_path=workbook_path,
            output_dir=output_dir,
            config=config,
            config_path=REPO_ROOT / DEFAULT_CONFIG_PATH,
            run_id=str(scenario["download_run"].get("run_id") or "upstream-extraction"),
            source_record_ids={str(scenario["source_record_id"])},
        )
        extraction = build_extraction(
            output_dir=output_dir,
            id_filter=str(scenario["source_record_id"]),
        )
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
                        "contract_id": str(scenario["source_record_id"]),
                        "required_source_record_ids": [str(scenario["source_record_id"])],
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
            if record.get("source_record_id") == scenario["source_record_id"]
        )
        text = Path(manifest_record["text_path"]).read_text(encoding="utf-8")
        missing_markers = [
            marker for marker in scenario.get("required_markers", []) if marker not in text
        ]
        forbidden_markers = [
            marker for marker in scenario.get("forbidden_markers", []) if marker in text
        ]
        marker_passed = not missing_markers and not forbidden_markers
        required_check_outcomes = scenario.get("required_check_outcomes") or {}
        assertion_passed = all(
            _check_outcome(audit.summary, check_name) == bool(expected)
            for check_name, expected in required_check_outcomes.items()
        )
        actual_producer_passed = bool(audit.summary.get("passed")) and marker_passed
        return actual_producer_passed, assertion_passed, {
            "audit_passed": bool(audit.summary.get("passed")),
            "required_check_outcomes": {
                check_name: _check_outcome(audit.summary, check_name)
                for check_name in required_check_outcomes
            },
            "missing_markers": missing_markers,
            "forbidden_markers_present": forbidden_markers,
            "failed_checks": _failed_check_names(audit.summary),
        }


_RUNNERS = {
    "capture_dry_run": _run_capture_dry_run,
    "capture_preflight": _run_capture_preflight,
    "capture_response_classification": _run_capture_response_classification,
    "capture_validate_run": _run_capture_validate_run,
    "catalog_build": _run_catalog_build,
    "extraction_build": _run_extraction_build,
}


def _is_within_fixture_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
