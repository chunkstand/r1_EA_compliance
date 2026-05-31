from __future__ import annotations

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
    _read_json,
    _read_jsonl,
    _resolve_path,
    _upstream_eval_config,
    _write_json,
)


_NON_LOAD_BEARING_METRIC_IDS = {
    "negative_case_match_rate",
    "required_check_match_rate",
}


def run_extraction_fidelity_case(
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
