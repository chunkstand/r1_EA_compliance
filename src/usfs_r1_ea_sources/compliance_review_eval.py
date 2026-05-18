from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json

from .applicability import build_authority_universe_snapshot
from .applicability_decisions import build_applicability_decisions
from .applicability_retrieval import build_applicability_retrieval_traces
from .applicability_rule_pack import generate_applicability_rule_pack
from .applicability_validation import validate_applicability_run
from .eval_metrics import contract_snapshot, metric_threshold_check, read_json_payload
from .compliance_findings import claim_type
from .compliance_outputs import finding_source_document_roles
from .compliance_outputs import finding_source_record_ids
from .compliance_review import ComplianceReviewResult
from .compliance_review import run_compliance_review
from .compliance_validation import (
    CLAIM_STATUSES,
    GRAPH_COVERAGE_CHECKS,
    VALID_CLAIM_TYPES,
    VALID_FINDING_STATUSES,
)
from .compliance_validation import failed_check_names
from .compliance_validation import validation_checks_passed
from .ea_review import run_ea_review
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_resolver import DEFAULT_FOREST_PLAN_PROFILE_ID
from .package_fact_graph import build_package_fact_graph
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import SAFE_ID_RE
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION = "compliance-review-eval-v1"
COMPLIANCE_REVIEW_EVAL_RESULTS_SCHEMA_VERSION = "compliance-review-eval-results-v1"
DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH = Path("config/compliance_review_eval_seed.json")
SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS = {"claim_type", "rule_id", "status"}


@dataclass(frozen=True)
class ComplianceReviewEvalResult:
    eval_file: Path
    output_dir: Path
    output_path: Path
    summary: dict


def run_compliance_review_eval(
    *,
    output_dir: Path,
    eval_file: Path = DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    index_path: Path | None = None,
    forest_unit_id: str = DEFAULT_FOREST_PLAN_PROFILE_ID,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    results_dir: Path | None = None,
    source_top_k: int = 3,
    package_top_k: int = 3,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
) -> ComplianceReviewEvalResult:
    """Run deterministic eval cases against the final compliance-review layer."""

    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")
    if package_top_k < 1:
        raise ValueError("package_top_k must be at least 1")
    output_dir = Path(output_dir)
    eval_file = Path(eval_file)
    rule_pack_path = Path(rule_pack_path)
    if not rule_pack_path.exists():
        raise FileNotFoundError(f"Missing compliance rule pack: {rule_pack_path}")
    rule_pack = load_rule_pack(rule_pack_path)
    rule_pack_validation = validate_rule_pack(rule_pack)
    if not rule_pack_validation["passed"]:
        failed = ", ".join(
            check["name"] for check in rule_pack_validation["checks"] if not check["passed"]
        )
        raise ValueError(f"Compliance rule pack is invalid. Failed checks: {failed}")
    contract, cases, legacy_format = _load_compliance_review_eval_contract(eval_file)
    _validate_compliance_review_eval_cases_against_rule_pack(cases, rule_pack)

    eval_output_dir = (
        Path(results_dir)
        if results_dir
        else output_dir / "reviews" / "compliance_review_eval"
    )
    package_dir = eval_output_dir / "packages"
    review_root = eval_output_dir / "reviews"
    package_dir.mkdir(parents=True, exist_ok=True)
    review_root.mkdir(parents=True, exist_ok=True)
    output_path = eval_output_dir / "compliance_review_eval_results.json"

    case_results = []
    for case in cases:
        case_id = str(case["id"])
        case_source_top_k = int(case.get("source_top_k") or source_top_k)
        case_package_top_k = int(case.get("package_top_k") or package_top_k)
        package_path = _eval_package_path(
            case,
            eval_file=eval_file,
            package_dir=package_dir,
        )
        review_id = str(case.get("review_id") or f"compliance-eval-{case_id}")
        _validate_safe_id(review_id, "review_id")
        requires_generated_rule_pack = _case_requires_generated_rule_pack(case)
        review_dir = (
            output_dir / "reviews" / review_id
            if requires_generated_rule_pack
            else review_root / case_id
        )
        effective_rule_pack_path = (
            _generated_rule_pack_for_eval_case(
                output_dir=output_dir,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                source_set_id=source_set_id,
                index_path=index_path,
                review_id=review_id,
                source_top_k=case_source_top_k,
                package_top_k=case_package_top_k,
                chunk_max_chars=chunk_max_chars,
                chunk_overlap_chars=chunk_overlap_chars,
                docling_ocr=docling_ocr,
                docling_timeout_seconds=docling_timeout_seconds,
            )
            if requires_generated_rule_pack
            else rule_pack_path
        )
        result = run_compliance_review(
            package_path=package_path,
            output_dir=output_dir,
            rule_pack_path=effective_rule_pack_path,
            source_set_id=source_set_id,
            index_path=index_path,
            forest_unit_id=forest_unit_id,
            forest_plan_profiles_path=forest_plan_profiles_path,
            review_id=review_id,
            results_dir=review_dir,
            source_top_k=case_source_top_k,
            package_top_k=case_package_top_k,
            chunk_max_chars=chunk_max_chars,
            chunk_overlap_chars=chunk_overlap_chars,
            docling_ocr=docling_ocr,
            docling_timeout_seconds=docling_timeout_seconds,
            reuse_package_cache=requires_generated_rule_pack,
            allow_base_rule_pack_review=not requires_generated_rule_pack,
        )
        report = _read_json(result.compliance_review_path)
        validation = _read_json(result.compliance_validation_path)
        case_results.append(
            _compliance_review_eval_case_result(
                case=case,
                package_path=package_path,
                result=result,
                report=report,
                validation=validation,
                source_top_k=case_source_top_k,
                package_top_k=case_package_top_k,
            )
        )

    case_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    failed_count = case_count - passed_count
    source_set_ids = sorted(
        {
            str(case["source_set_id"])
            for case in case_results
            if case.get("source_set_id")
        }
    )
    hard_negative_cases = [case for case in case_results if case["hard_negative_package"]]
    conditional_subset_cases = [case for case in case_results if case["conditional_subset"]]
    all_authorities_control_cases = [
        case for case in case_results if case["all_authorities_control"]
    ]
    metrics = {
        "case_count": case_count,
        "pass_rate": _rate(passed_count, case_count),
        "validation_match_rate": _case_rate(case_results, "validation_passed_matches"),
        "reviewer_ready_match_rate": _case_rate(case_results, "reviewer_ready_matches"),
        "status_match_rate": _case_rate(case_results, "expected_statuses_match"),
        "claim_type_match_rate": _case_rate(case_results, "expected_claim_types_match"),
        "package_evidence_match_rate": _case_rate(
            case_results,
            "expected_package_evidence_match",
        ),
        "source_evidence_match_rate": _case_rate(
            case_results,
            "expected_source_evidence_match",
        ),
        "source_claim_link_match_rate": _case_rate(
            case_results,
            "expected_source_claim_links_match",
        ),
        "source_record_match_rate": _case_rate(
            case_results,
            "expected_source_record_ids_match",
        ),
        "source_document_role_match_rate": _case_rate(
            case_results,
            "expected_source_document_roles_match",
        ),
        "citation_coverage_rate": _case_rate(case_results, "citation_coverage_supported"),
        "graph_coverage_rate": _case_rate(case_results, "graph_coverage_supported"),
        "authority_explanation_artifact_rate": _case_rate(
            case_results,
            "authority_explanation_artifact_present",
        ),
        "authority_path_classification_rate": _case_rate(
            case_results,
            "authority_path_classification_supported",
        ),
        "authority_trace_coverage_rate": _case_rate(
            case_results,
            "authority_trace_coverage_supported",
        ),
        "unsupported_finding_match_rate": _case_rate(
            case_results,
            "unsupported_finding_ids_match",
        ),
        "unexpected_positive_finding_rate": _case_rate(
            case_results,
            "unexpected_positive_rules_absent",
            invert=True,
        ),
        "missing_required_source_rule_rate": _case_rate(
            case_results,
            "missing_required_source_rules_absent",
            invert=True,
        ),
        "zero_finding_rate": _rate(
            sum(1 for case in case_results if case["finding_count"] == 0),
            case_count,
        ),
    }
    checks = [
        {
            "name": "eval_cases_pass",
            "passed": failed_count == 0,
            "details": {
                "case_count": case_count,
                "failed_case_ids": [case["id"] for case in case_results if not case["passed"]],
            },
        },
        _compliance_review_eval_coverage_check(
            contract,
            case_results,
            legacy_format=legacy_format,
        ),
        metric_threshold_check(contract.get("metric_thresholds", {}), metrics),
    ]
    summary = {
        "schema_version": COMPLIANCE_REVIEW_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "eval_file": str(eval_file),
        "output_dir": str(eval_output_dir),
        "output_path": str(output_path),
        "rule_pack_path": str(rule_pack_path),
        "source_set_id": source_set_id or (source_set_ids[0] if len(source_set_ids) == 1 else None),
        "source_set_ids": source_set_ids,
        "created_at": _utc_now(),
        "source_top_k": source_top_k,
        "package_top_k": package_top_k,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "hard_negative_package_case_count": len(hard_negative_cases),
        "conditional_subset_case_count": len(conditional_subset_cases),
        "all_authorities_control_case_count": len(all_authorities_control_cases),
        "checks": checks,
        "metrics": metrics,
        "contract": contract_snapshot(
            contract_path=eval_file,
            contract=contract,
            case_count=len(cases),
        ),
        "failure_category_counts": _failure_category_counts(case_results),
        "cases": case_results,
    }
    summary["passed"] = all(check["passed"] for check in checks)
    _write_json(output_path, summary)
    return ComplianceReviewEvalResult(
        eval_file=eval_file,
        output_dir=eval_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _load_compliance_review_eval_contract(path: Path) -> tuple[dict, list[dict], bool]:
    payload = read_json_payload(path, label="compliance review eval file")
    if isinstance(payload, list):
        cases = _validated_compliance_review_eval_cases(payload, legacy_format=True)
        return (
            {
                "schema_version": "legacy-compliance-review-eval-list-v0",
                "eval_id": f"legacy-{path.stem}",
                "coverage_requirements": {},
                "metric_thresholds": {},
                "cases": cases,
            },
            cases,
            True,
        )
    if payload.get("schema_version") != COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported compliance review eval schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    if not str(payload.get("eval_id") or "").strip():
        raise ValueError("Compliance review eval contract missing 'eval_id'.")
    if not isinstance(payload.get("coverage_requirements"), dict):
        raise ValueError("Compliance review eval contract missing 'coverage_requirements'.")
    if not isinstance(payload.get("metric_thresholds"), dict):
        raise ValueError("Compliance review eval contract missing 'metric_thresholds'.")
    _validate_compliance_review_coverage_requirements(payload["coverage_requirements"])
    cases = _validated_compliance_review_eval_cases(payload.get("cases"), legacy_format=False)
    return payload, cases, False


def _case_requires_generated_rule_pack(case: dict) -> bool:
    return any(
        bool(case.get(field))
        for field in (
            "all_authorities_control",
            "conditional_subset",
            "hard_negative_package",
        )
    )


def _generated_rule_pack_for_eval_case(
    *,
    output_dir: Path,
    package_path: Path,
    base_rule_pack_path: Path,
    source_set_id: str | None,
    index_path: Path | None,
    review_id: str,
    source_top_k: int,
    package_top_k: int,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
) -> Path:
    run_ea_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=index_path,
        checklist_path=base_rule_pack_path,
        review_id=review_id,
        source_top_k=source_top_k,
        package_top_k=package_top_k,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
    )
    build_authority_universe_snapshot(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack_path=base_rule_pack_path,
    )
    build_package_fact_graph(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        package_path=package_path,
    )
    build_applicability_retrieval_traces(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        top_k=source_top_k,
    )
    build_applicability_decisions(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    validation_result = validate_applicability_run(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    if not validation_result.summary.get("passed"):
        failed_checks = [
            str(check.get("name") or "")
            for check in validation_result.summary.get("checks", [])
            if not check.get("passed")
        ]
        failed_text = ", ".join(item for item in failed_checks if item) or "unknown"
        raise ValueError(
            "Applicability validation did not pass for compliance-review eval case "
            f"{review_id}: {failed_text}"
        )
    generated_result = generate_applicability_rule_pack(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack_path=base_rule_pack_path,
    )
    return generated_result.generated_rule_pack_path


def _validated_compliance_review_eval_cases(
    payload: object,
    *,
    legacy_format: bool,
) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "Compliance review eval file must contain a non-empty JSON list."
            if legacy_format
            else "Compliance review eval contract must contain non-empty cases."
        )
    case_ids = []
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Compliance review eval case {index} must be an object.")
        case_id = str(case.get("id") or "").strip()
        if not case_id:
            raise ValueError(f"Compliance review eval case {index} is missing 'id'.")
        if not SAFE_ID_RE.fullmatch(case_id):
            raise ValueError(
                f"Compliance review eval case {index} id must contain only safe path characters."
            )
        case_ids.append(case_id)
        _validate_eval_package_fixture(index, case)
        _validate_eval_filters(index, case)
        _validate_eval_expected_statuses(index, case)
        _validate_eval_expected_claim_types(index, case)
        _validate_eval_expected_bool_map(index, case, "expected_package_evidence")
        _validate_eval_expected_bool_map(index, case, "expected_source_evidence")
        _validate_eval_expected_bool_map(index, case, "expected_source_claim_links")
        _validate_eval_expected_string_list_map(index, case, "expected_source_record_ids")
        _validate_eval_expected_string_list_map(index, case, "expected_source_document_roles")
        _validate_eval_status_counts(index, case)
        _validate_eval_string_list(index, case, "expected_unsupported_finding_ids")
        _validate_optional_bool(index, case, "expected_validation_passed")
        _validate_optional_bool(index, case, "expected_reviewer_ready")
        _validate_optional_bool(index, case, "require_graph_coverage")
        _validate_optional_bool(index, case, "hard_negative_package")
        _validate_optional_bool(index, case, "conditional_subset")
        _validate_optional_bool(index, case, "all_authorities_control")
        _validate_positive_eval_int(index, case, "min_findings")
        _validate_positive_eval_int(index, case, "source_top_k")
        _validate_positive_eval_int(index, case, "package_top_k")
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise ValueError(f"Duplicate compliance review eval case IDs: {duplicates}")
    return payload


def _validate_compliance_review_coverage_requirements(requirements: dict) -> None:
    for key in (
        "case_count",
        "hard_negative_package_case_count",
        "conditional_subset_case_count",
        "all_authorities_control_case_count",
    ):
        value = requirements.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                "Compliance review eval coverage_requirements."
                f"{key} must be a non-negative integer."
            )


def _validate_eval_package_fixture(index: int, case: dict) -> None:
    has_text = bool(str(case.get("package_text") or "").strip())
    has_path = bool(str(case.get("package_path") or "").strip())
    if has_text == has_path:
        raise ValueError(
            f"Compliance review eval case {index} must define exactly one of "
            "package_text or package_path."
        )


def _validate_compliance_review_eval_cases_against_rule_pack(
    cases: list[dict],
    rule_pack: dict,
) -> None:
    expected_rule_ids = {str(rule["id"]) for rule in rule_pack["rules"]}
    rule_count = len(expected_rule_ids)
    for index, case in enumerate(cases):
        case_id = str(case["id"])
        status_rule_ids = set(_string_map(case["expected_statuses"]))
        if status_rule_ids != expected_rule_ids:
            missing = sorted(expected_rule_ids - status_rule_ids)
            unexpected = sorted(status_rule_ids - expected_rule_ids)
            raise ValueError(
                f"Compliance review eval case {index} ({case_id}) expected_statuses must "
                f"cover every rule in the rule pack. Missing: {missing}; unexpected: {unexpected}."
            )
        for key in (
            "expected_claim_types",
            "expected_package_evidence",
            "expected_source_evidence",
            "expected_source_claim_links",
            "expected_source_record_ids",
            "expected_source_document_roles",
        ):
            _validate_eval_rule_map_keys(index, case_id, case.get(key) or {}, expected_rule_ids, key)
        unsupported_ids = set(str(value) for value in case.get("expected_unsupported_finding_ids", []))
        unexpected_unsupported = sorted(unsupported_ids - expected_rule_ids)
        if unexpected_unsupported:
            raise ValueError(
                f"Compliance review eval case {index} ({case_id}) expected_unsupported_finding_ids "
                f"contains unknown rule IDs: {unexpected_unsupported}."
            )
        filters = case.get("filters") or {}
        if "rule_id" in filters:
            rule_filter_ids = set(_filter_values(filters["rule_id"]))
            unknown_filters = sorted(rule_filter_ids - expected_rule_ids)
            if unknown_filters:
                raise ValueError(
                    f"Compliance review eval case {index} ({case_id}) rule_id filter "
                    f"contains unknown rule IDs: {unknown_filters}."
                )
        expected_counts = {
            str(status): int(count)
            for status, count in (case.get("expected_finding_status_counts") or {}).items()
        }
        if expected_counts:
            if _case_requires_generated_rule_pack(case):
                min_findings = int(case.get("min_findings") or 1)
                if sum(expected_counts.values()) < min_findings:
                    raise ValueError(
                        f"Compliance review eval case {index} ({case_id}) expected_finding_status_counts "
                        "must cover at least min_findings for generated-rule-pack cases."
                    )
            else:
                counts_from_statuses = dict(
                    Counter(str(status) for status in case["expected_statuses"].values())
                )
                normalized_expected_counts = {
                    status: count for status, count in expected_counts.items() if count
                }
                if (
                    sum(expected_counts.values()) != rule_count
                    or normalized_expected_counts != counts_from_statuses
                ):
                    raise ValueError(
                        f"Compliance review eval case {index} ({case_id}) expected_finding_status_counts "
                        "must match expected_statuses and sum to the rule count."
                    )


def _validate_eval_rule_map_keys(
    index: int,
    case_id: str,
    values: dict,
    expected_rule_ids: set[str],
    key: str,
) -> None:
    actual = set(str(rule_id) for rule_id in values)
    unexpected = sorted(actual - expected_rule_ids)
    if unexpected:
        raise ValueError(
            f"Compliance review eval case {index} ({case_id}) {key} contains unknown rule IDs: "
            f"{unexpected}."
        )


def _validate_eval_filters(index: int, case: dict) -> None:
    filters = case.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError(f"Compliance review eval case {index} filters must be an object.")
    unknown_keys = sorted(set(filters) - SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS)
    empty_values = [
        key
        for key, value in filters.items()
        if key in SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS and not _filter_values(value)
    ]
    if unknown_keys or empty_values:
        details = []
        if unknown_keys:
            details.append(f"unsupported filters: {unknown_keys}")
        if empty_values:
            details.append(f"empty filters: {empty_values}")
        raise ValueError(
            f"Compliance review eval case {index} has invalid filters; " + "; ".join(details)
        )
    if "status" in filters:
        unsupported = sorted(set(_filter_values(filters["status"])) - VALID_FINDING_STATUSES)
        if unsupported:
            raise ValueError(
                f"Compliance review eval case {index} has unsupported status filters: "
                f"{unsupported}."
            )
    if "claim_type" in filters:
        unsupported = sorted(set(_filter_values(filters["claim_type"])) - VALID_CLAIM_TYPES)
        if unsupported:
            raise ValueError(
                f"Compliance review eval case {index} has unsupported claim_type filters: "
                f"{unsupported}."
            )


def _validate_eval_expected_statuses(index: int, case: dict) -> None:
    expected = case.get("expected_statuses")
    if not isinstance(expected, dict) or not expected:
        raise ValueError(
            f"Compliance review eval case {index} expected_statuses must be a non-empty object."
        )
    invalid = sorted(
        str(status)
        for status in expected.values()
        if str(status) not in VALID_FINDING_STATUSES
    )
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} has unsupported expected_statuses: {invalid}."
        )


def _validate_eval_expected_claim_types(index: int, case: dict) -> None:
    expected = case.get("expected_claim_types") or {}
    if not isinstance(expected, dict):
        raise ValueError(
            f"Compliance review eval case {index} expected_claim_types must be an object."
        )
    invalid = sorted(
        str(claim_type)
        for claim_type in expected.values()
        if str(claim_type) not in VALID_CLAIM_TYPES
    )
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} has unsupported expected_claim_types: "
            f"{invalid}."
        )


def _validate_eval_expected_bool_map(index: int, case: dict, key: str) -> None:
    expected = case.get(key) or {}
    if not isinstance(expected, dict):
        raise ValueError(f"Compliance review eval case {index} {key} must be an object.")
    invalid = sorted(str(rule_id) for rule_id, value in expected.items() if not isinstance(value, bool))
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} {key} values must be booleans: {invalid}."
        )


def _validate_eval_expected_string_list_map(index: int, case: dict, key: str) -> None:
    expected = case.get(key) or {}
    if not isinstance(expected, dict):
        raise ValueError(f"Compliance review eval case {index} {key} must be an object.")
    invalid = []
    for rule_id, values in expected.items():
        if not isinstance(values, list) or not values:
            invalid.append(str(rule_id))
            continue
        if any(not str(value).strip() for value in values):
            invalid.append(str(rule_id))
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} {key} values must be non-empty "
            f"lists of strings: {invalid}."
        )


def _validate_eval_status_counts(index: int, case: dict) -> None:
    expected = case.get("expected_finding_status_counts") or {}
    if not isinstance(expected, dict):
        raise ValueError(
            f"Compliance review eval case {index} expected_finding_status_counts must be an object."
        )
    unsupported = sorted(set(str(status) for status in expected) - VALID_FINDING_STATUSES)
    invalid_counts = []
    for status, value in expected.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            invalid_counts.append(str(status))
            continue
        if count < 0:
            invalid_counts.append(str(status))
    if unsupported or invalid_counts:
        raise ValueError(
            f"Compliance review eval case {index} has invalid expected_finding_status_counts."
        )


def _validate_eval_string_list(index: int, case: dict, key: str) -> None:
    values = case.get(key, [])
    if not isinstance(values, list) or any(not str(value).strip() for value in values):
        raise ValueError(f"Compliance review eval case {index} {key} must be a list of strings.")


def _validate_optional_bool(index: int, case: dict, key: str) -> None:
    if key in case and not isinstance(case[key], bool):
        raise ValueError(f"Compliance review eval case {index} {key} must be a boolean.")


def _validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Compliance review eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Compliance review eval case {index} {key} must be at least 1.")


def _eval_package_path(case: dict, *, eval_file: Path, package_dir: Path) -> Path:
    if str(case.get("package_text") or "").strip():
        package_path = package_dir / f"{case['id']}.txt"
        package_path.write_text(str(case["package_text"]).rstrip() + "\n", encoding="utf-8")
        return package_path
    package_path = Path(str(case["package_path"]))
    if not package_path.is_absolute():
        package_path = eval_file.parent / package_path
    if not package_path.exists():
        raise FileNotFoundError(f"Missing compliance review eval package fixture: {package_path}")
    return package_path


def _compliance_review_eval_case_result(
    *,
    case: dict,
    package_path: Path,
    result: ComplianceReviewResult,
    report: dict,
    validation: dict,
    source_top_k: int,
    package_top_k: int,
) -> dict:
    findings = list(report.get("findings", []))
    findings_by_rule = {str(finding.get("rule_id")): finding for finding in findings}
    filters = dict(case.get("filters") or {})
    selected_findings = _filter_eval_findings(findings, filters)
    expected_statuses = _string_map(case["expected_statuses"])
    expected_claim_types = _expected_claim_type_map(case, expected_statuses)
    expected_package_evidence = _expected_bool_presence_map(
        case,
        "expected_package_evidence",
        expected_statuses,
        lambda status: status == "pass",
    )
    expected_source_evidence = _expected_bool_presence_map(
        case,
        "expected_source_evidence",
        expected_statuses,
        lambda status: status in CLAIM_STATUSES,
    )
    expected_source_claim_links = _expected_bool_presence_map(
        case,
        "expected_source_claim_links",
        expected_statuses,
        lambda status: status in CLAIM_STATUSES,
    )
    normalized_findings_by_rule = _normalized_eval_findings_by_rule(
        findings_by_rule=findings_by_rule,
        expected_statuses=expected_statuses,
        generated_rule_pack_case=_case_requires_generated_rule_pack(case),
    )
    status_mismatches = _value_mismatches(
        normalized_findings_by_rule,
        expected_statuses,
        "status",
    )
    claim_type_mismatches = _value_mismatches(
        normalized_findings_by_rule,
        expected_claim_types,
        "claim_type",
    )
    package_evidence_mismatches = _presence_mismatches(
        normalized_findings_by_rule,
        expected_package_evidence,
        _finding_has_package_evidence,
    )
    source_evidence_mismatches = _presence_mismatches(
        normalized_findings_by_rule,
        expected_source_evidence,
        _finding_has_source_evidence,
    )
    source_claim_link_mismatches = _presence_mismatches(
        normalized_findings_by_rule,
        expected_source_claim_links,
        _finding_has_source_claim_links,
    )
    expected_source_record_ids = _expected_string_list_map(case, "expected_source_record_ids")
    expected_source_document_roles = _expected_string_list_map(
        case,
        "expected_source_document_roles",
    )
    source_record_mismatches = _expected_subset_mismatches(
        normalized_findings_by_rule,
        expected_source_record_ids,
        finding_source_record_ids,
    )
    source_document_role_mismatches = _expected_subset_mismatches(
        normalized_findings_by_rule,
        expected_source_document_roles,
        finding_source_document_roles,
    )
    expected_status_counts = {
        str(status): int(count)
        for status, count in (case.get("expected_finding_status_counts") or {}).items()
    }
    actual_status_counts = dict(Counter(str(finding.get("status")) for finding in findings))
    status_counts_match = (
        not expected_status_counts or actual_status_counts == expected_status_counts
    )
    expected_unsupported = sorted(
        str(value) for value in case.get("expected_unsupported_finding_ids", [])
    )
    actual_unsupported = sorted(
        str(value)
        for value in report.get("summary", {}).get("unsupported_finding_ids", [])
    )
    unsupported_finding_ids_match = actual_unsupported == expected_unsupported
    summary = report.get("summary", {})
    applicability_gate = summary.get("applicability_gate")
    diagnostic_base_rule_pack = (
        isinstance(applicability_gate, dict)
        and applicability_gate.get("mode") == "base_rule_pack_diagnostic"
    )
    if "expected_validation_passed" in case:
        expected_validation_passed = bool(case.get("expected_validation_passed"))
    else:
        expected_validation_passed = not diagnostic_base_rule_pack
    validation_passed_matches = bool(validation.get("passed")) == expected_validation_passed
    if "expected_reviewer_ready" in case:
        expected_reviewer_ready = bool(case.get("expected_reviewer_ready"))
    else:
        expected_reviewer_ready = not diagnostic_base_rule_pack
    reviewer_ready_matches = (
        bool(summary.get("reviewer_ready")) == expected_reviewer_ready
    )
    require_graph_coverage = bool(case.get("require_graph_coverage", True))
    graph_coverage_supported = (
        not require_graph_coverage or validation_checks_passed(validation, GRAPH_COVERAGE_CHECKS)
    )
    min_findings = int(case.get("min_findings", 1))
    min_findings_met = len(selected_findings) >= min_findings
    citation_coverage_supported = bool(selected_findings) and all(
        _finding_has_required_eval_citations(finding) for finding in selected_findings
    )
    authority_explanation_path = summary.get("authority_explanation_paths_path")
    authority_explanation_artifact_present = bool(
        authority_explanation_path and Path(str(authority_explanation_path)).exists()
    )
    authority_path_classification_supported = (not selected_findings) or all(
        _finding_has_authority_path_classification(finding) for finding in selected_findings
    )
    authority_trace_coverage_supported = diagnostic_base_rule_pack or (not selected_findings) or all(
        _finding_has_graph_or_retrieval_trace(finding) for finding in selected_findings
    )
    unexpected_positive_rule_ids = sorted(
        rule_id
        for rule_id, actual_status in (
            (rule_id, finding.get("status")) for rule_id, finding in findings_by_rule.items()
        )
        if str(actual_status) == "pass" and expected_statuses.get(rule_id) != "pass"
    )
    missing_required_source_rule_ids = sorted(
        mismatch["rule_id"]
        for mismatch in source_record_mismatches
        if expected_statuses.get(str(mismatch.get("rule_id") or "")) == "pass"
    )

    result_flags = {
        "validation_passed_matches": validation_passed_matches,
        "reviewer_ready_matches": reviewer_ready_matches,
        "min_findings_met": min_findings_met,
        "expected_statuses_match": not status_mismatches,
        "expected_claim_types_match": not claim_type_mismatches,
        "expected_package_evidence_match": not package_evidence_mismatches,
        "expected_source_evidence_match": not source_evidence_mismatches,
        "expected_source_claim_links_match": not source_claim_link_mismatches,
        "expected_source_record_ids_match": not source_record_mismatches,
        "expected_source_document_roles_match": not source_document_role_mismatches,
        "status_counts_match": status_counts_match,
        "unsupported_finding_ids_match": unsupported_finding_ids_match,
        "citation_coverage_supported": citation_coverage_supported,
        "graph_coverage_supported": graph_coverage_supported,
        "authority_explanation_artifact_present": authority_explanation_artifact_present,
        "authority_path_classification_supported": authority_path_classification_supported,
        "authority_trace_coverage_supported": authority_trace_coverage_supported,
        "unexpected_positive_rules_absent": not unexpected_positive_rule_ids,
        "missing_required_source_rules_absent": not missing_required_source_rule_ids,
    }
    failure_reasons = [
        name
        for name, passed in result_flags.items()
        if not passed
    ]
    failure_taxonomy = _failure_taxonomy(
        result_flags=result_flags,
        status_mismatches=status_mismatches,
        claim_type_mismatches=claim_type_mismatches,
        package_evidence_mismatches=package_evidence_mismatches,
        source_evidence_mismatches=source_evidence_mismatches,
        source_claim_link_mismatches=source_claim_link_mismatches,
        source_record_mismatches=source_record_mismatches,
        source_document_role_mismatches=source_document_role_mismatches,
        validation_failed_checks=failed_check_names(validation),
        selected_findings=selected_findings,
    )
    return {
        "id": case["id"],
        "review_id": result.review_id,
        "source_set_id": report.get("summary", {}).get("source_set_id"),
        "rule_pack_id": report.get("summary", {}).get("rule_pack_id"),
        "rule_pack_version": report.get("summary", {}).get("rule_pack_version"),
        "package_path": str(package_path),
        "review_dir": str(result.review_dir),
        "compliance_review_path": str(result.compliance_review_path),
        "compliance_matrix_path": str(result.compliance_matrix_path),
        "compliance_matrix_markdown_path": str(result.compliance_matrix_markdown_path),
        "compliance_matrix_pdf_path": str(result.compliance_matrix_pdf_path),
        "compliance_validation_path": str(result.compliance_validation_path),
        "authority_explanation_paths_path": authority_explanation_path,
        "finding_nodes_path": str(result.finding_nodes_path),
        "finding_edges_path": str(result.finding_edges_path),
        "source_top_k": source_top_k,
        "package_top_k": package_top_k,
        "filters": filters,
        "finding_count": len(findings),
        "selected_finding_count": len(selected_findings),
        "finding_status_counts": actual_status_counts,
        "expected_statuses": expected_statuses,
        "actual_statuses": {
            rule_id: finding.get("status") for rule_id, finding in sorted(findings_by_rule.items())
        },
        "status_mismatches": status_mismatches,
        "expected_claim_types": expected_claim_types,
        "actual_claim_types": {
            rule_id: finding.get("claim_type")
            for rule_id, finding in sorted(findings_by_rule.items())
        },
        "claim_type_mismatches": claim_type_mismatches,
        "package_evidence_mismatches": package_evidence_mismatches,
        "source_evidence_mismatches": source_evidence_mismatches,
        "source_claim_link_mismatches": source_claim_link_mismatches,
        "expected_source_record_ids": expected_source_record_ids,
        "source_record_mismatches": source_record_mismatches,
        "expected_source_document_roles": expected_source_document_roles,
        "source_document_role_mismatches": source_document_role_mismatches,
        "unexpected_positive_rule_ids": unexpected_positive_rule_ids,
        "missing_required_source_rule_ids": missing_required_source_rule_ids,
        "expected_finding_status_counts": expected_status_counts,
        "expected_unsupported_finding_ids": expected_unsupported,
        "actual_unsupported_finding_ids": actual_unsupported,
        "expected_validation_passed": expected_validation_passed,
        "actual_validation_passed": bool(validation.get("passed")),
        "expected_reviewer_ready": expected_reviewer_ready,
        "actual_reviewer_ready": bool(report.get("summary", {}).get("reviewer_ready")),
        "require_graph_coverage": require_graph_coverage,
        "validation_failed_checks": failed_check_names(validation),
        "finding_results": [_eval_finding_summary(finding) for finding in selected_findings],
        "hard_negative_package": bool(case.get("hard_negative_package")),
        "conditional_subset": bool(case.get("conditional_subset")),
        "all_authorities_control": bool(case.get("all_authorities_control")),
        **result_flags,
        "failure_reasons": failure_reasons,
        "failure_taxonomy": failure_taxonomy,
        "failure_category_counts": dict(Counter(item["category"] for item in failure_taxonomy)),
        "reproduction": _case_reproduction(result, package_path),
        "passed": not failure_reasons,
    }


def _filter_eval_findings(findings: list[dict], filters: dict) -> list[dict]:
    return [
        finding
        for finding in findings
        if all(str(finding.get(key) or "") in set(_filter_values(value)) for key, value in filters.items())
    ]


def _filter_values(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _string_map(value: dict) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()}


def _expected_claim_type_map(case: dict, expected_statuses: dict[str, str]) -> dict[str, str]:
    expected = {rule_id: claim_type(status) for rule_id, status in expected_statuses.items()}
    expected.update(_string_map(case.get("expected_claim_types") or {}))
    return expected


def _expected_bool_presence_map(
    case: dict,
    key: str,
    expected_statuses: dict[str, str],
    default_for_status,
) -> dict[str, bool]:
    expected = {
        rule_id: bool(default_for_status(status))
        for rule_id, status in expected_statuses.items()
    }
    expected.update({str(rule_id): bool(value) for rule_id, value in (case.get(key) or {}).items()})
    return expected


def _expected_string_list_map(case: dict, key: str) -> dict[str, list[str]]:
    return {
        str(rule_id): sorted({str(value) for value in values if str(value).strip()})
        for rule_id, values in (case.get(key) or {}).items()
    }


def _expected_subset_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, list[str]],
    actual_values,
) -> list[dict]:
    failures = []
    for rule_id, expected_values in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = actual_values(finding) if finding else []
        missing = sorted(set(expected_values) - set(actual))
        if missing:
            failures.append(
                {
                    "rule_id": rule_id,
                    "expected": expected_values,
                    "actual": actual,
                    "missing": missing,
                }
            )
    return failures


def _normalized_eval_findings_by_rule(
    *,
    findings_by_rule: dict[str, dict],
    expected_statuses: dict[str, str],
    generated_rule_pack_case: bool,
) -> dict[str, dict]:
    if not generated_rule_pack_case:
        return findings_by_rule
    normalized = dict(findings_by_rule)
    for rule_id, expected_status in expected_statuses.items():
        if expected_status != "not_applicable" or rule_id in normalized:
            continue
        normalized[rule_id] = {
            "rule_id": rule_id,
            "status": "not_applicable",
            "claim_type": claim_type("not_applicable"),
            "package_evidence": [],
            "package_evidence_citation": None,
            "source_library_evidence": [],
            "source_library_evidence_citation": None,
            "source_claim_links": [],
            "source_claim_link_count": 0,
        }
    return normalized


def _value_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, str],
    field: str,
) -> list[dict]:
    failures = []
    for rule_id, expected_value in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = finding.get(field) if finding else None
        if actual != expected_value:
            failures.append({"rule_id": rule_id, "expected": expected_value, "actual": actual})
    return failures


def _presence_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, bool],
    predicate,
) -> list[dict]:
    failures = []
    for rule_id, expected_value in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = bool(finding and predicate(finding))
        if actual != expected_value:
            failures.append({"rule_id": rule_id, "expected": expected_value, "actual": actual})
    return failures


def _finding_has_package_evidence(finding: dict) -> bool:
    return bool(finding.get("package_evidence_citation") and finding.get("package_evidence"))


def _finding_has_source_evidence(finding: dict) -> bool:
    return bool(finding.get("source_library_evidence_citation") and finding.get("source_library_evidence"))


def _finding_has_source_claim_links(finding: dict) -> bool:
    return bool(finding.get("source_claim_link_count") and finding.get("source_claim_links"))


def _finding_has_required_eval_citations(finding: dict) -> bool:
    status = finding.get("status")
    if status not in CLAIM_STATUSES:
        return True
    if not _finding_has_source_evidence(finding) or not _finding_has_source_claim_links(finding):
        return False
    if status == "pass" and not _finding_has_package_evidence(finding):
        return False
    return True


def _finding_has_authority_path_classification(finding: dict) -> bool:
    return bool(finding.get("authority_path_classifications"))


def _finding_has_graph_or_retrieval_trace(finding: dict) -> bool:
    return bool(
        finding.get("retrieval_trace_ids")
        or finding.get("graph_path_ids")
        or finding.get("search_coverage_certificate_ids")
    )


def _eval_finding_summary(finding: dict) -> dict:
    return {
        "rule_id": finding.get("rule_id"),
        "status": finding.get("status"),
        "claim_type": finding.get("claim_type"),
        "package_evidence_citation": finding.get("package_evidence_citation"),
        "source_library_evidence_citation": finding.get("source_library_evidence_citation"),
        "source_claim_link_count": finding.get("source_claim_link_count", 0),
        "applied_source_record_ids": finding_source_record_ids(finding),
        "applied_source_document_roles": finding_source_document_roles(finding),
        "authority_path_classifications": finding.get("authority_path_classifications") or [],
        "retrieval_trace_ids": finding.get("retrieval_trace_ids") or [],
        "graph_path_ids": finding.get("graph_path_ids") or [],
        "search_coverage_certificate_ids": finding.get("search_coverage_certificate_ids") or [],
    }


def _failure_taxonomy(
    *,
    result_flags: dict[str, bool],
    status_mismatches: list[dict],
    claim_type_mismatches: list[dict],
    package_evidence_mismatches: list[dict],
    source_evidence_mismatches: list[dict],
    source_claim_link_mismatches: list[dict],
    source_record_mismatches: list[dict],
    source_document_role_mismatches: list[dict],
    validation_failed_checks: list[str],
    selected_findings: list[dict],
) -> list[dict]:
    taxonomy = []
    if not result_flags["validation_passed_matches"] or not result_flags["reviewer_ready_matches"]:
        taxonomy.append(
            _taxonomy_entry(
                "validation_gate_miss",
                validation_failed_checks,
                ["reviewer_ready", "validation_passed"],
            )
        )
    if not result_flags["min_findings_met"]:
        taxonomy.append(_taxonomy_entry("rule_wording_issue", [], ["min_findings"]))
    if status_mismatches or claim_type_mismatches:
        taxonomy.append(
            _taxonomy_entry(
                "rule_wording_issue",
                status_mismatches + claim_type_mismatches,
            )
        )
    if package_evidence_mismatches:
        taxonomy.append(
            _taxonomy_entry("package_evidence_search_miss", package_evidence_mismatches)
        )
    if source_evidence_mismatches:
        taxonomy.append(_taxonomy_entry("source_retrieval_miss", source_evidence_mismatches))
    if source_claim_link_mismatches:
        taxonomy.append(_taxonomy_entry("rule_claim_binding_miss", source_claim_link_mismatches))
    if source_record_mismatches or source_document_role_mismatches:
        taxonomy.append(
            _taxonomy_entry(
                "source_applicability_miss",
                source_record_mismatches + source_document_role_mismatches,
            )
        )
    if not result_flags["authority_explanation_artifact_present"]:
        taxonomy.append(_taxonomy_entry("authority_explanation_artifact_miss", []))
    if not result_flags["authority_path_classification_supported"]:
        taxonomy.append(_taxonomy_entry("authority_path_classification_miss", []))
    if not result_flags["authority_trace_coverage_supported"]:
        taxonomy.append(_taxonomy_entry("authority_trace_coverage_miss", []))
    if not result_flags["citation_coverage_supported"]:
        unsupported = [
            finding.get("rule_id")
            for finding in selected_findings
            if not _finding_has_required_eval_citations(finding)
        ]
        taxonomy.append(_taxonomy_entry("citation_relevance_issue", unsupported))
    if not result_flags["graph_coverage_supported"]:
        taxonomy.append(
            _taxonomy_entry(
                "finding_graph_miss",
                validation_failed_checks,
                sorted(GRAPH_COVERAGE_CHECKS),
            )
        )
    return taxonomy


def _taxonomy_entry(
    category: str,
    evidence: list,
    checks: list[str] | None = None,
) -> dict:
    rule_ids = sorted(
        {
            str(item.get("rule_id"))
            for item in evidence
            if isinstance(item, dict) and item.get("rule_id")
        }
    )
    if not rule_ids:
        rule_ids = sorted({str(item) for item in evidence if isinstance(item, str)})
    return {
        "category": category,
        "rule_ids": rule_ids,
        "checks": checks or [],
        "evidence": evidence,
    }


def _failure_category_counts(cases: list[dict]) -> dict[str, int]:
    counts = Counter()
    for case in cases:
        for item in case.get("failure_taxonomy", []):
            counts[str(item.get("category"))] += 1
    return dict(sorted(counts.items()))


def _case_reproduction(result: ComplianceReviewResult, package_path: Path) -> dict:
    return {
        "command": (
            "PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review "
            f"--package-path {package_path} --output-dir <source_library> "
            f"--review-id {result.review_id}"
        ),
        "review_dir": str(result.review_dir),
        "package_path": str(package_path),
        "compliance_review_path": str(result.compliance_review_path),
        "compliance_matrix_path": str(result.compliance_matrix_path),
        "compliance_matrix_pdf_path": str(result.compliance_matrix_pdf_path),
        "compliance_validation_path": str(result.compliance_validation_path),
    }


def _case_rate(cases: list[dict], key: str, *, invert: bool = False) -> float:
    if invert:
        return _rate(sum(1 for case in cases if not case.get(key)), len(cases))
    return _rate(sum(1 for case in cases if case.get(key)), len(cases))


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def _validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dot, underscore, or hyphen."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _compliance_review_eval_coverage_check(
    contract: dict,
    case_results: list[dict],
    *,
    legacy_format: bool,
) -> dict:
    if legacy_format:
        return {
            "name": "coverage_requirements_met",
            "passed": True,
            "details": {"enabled": False, "legacy_format": True},
        }
    requirements = contract.get("coverage_requirements", {})
    actuals = {
        "case_count": len(case_results),
        "hard_negative_package_case_count": sum(
            1 for case in case_results if case["hard_negative_package"]
        ),
        "conditional_subset_case_count": sum(
            1 for case in case_results if case["conditional_subset"]
        ),
        "all_authorities_control_case_count": sum(
            1 for case in case_results if case["all_authorities_control"]
        ),
    }
    failures = [
        {
            "requirement": key,
            "min": int(requirements.get(key) or 0),
            "actual": actuals[key],
        }
        for key in actuals
        if actuals[key] < int(requirements.get(key) or 0)
    ]
    return {
        "name": "coverage_requirements_met",
        "passed": not failures,
        "details": {
            "enabled": True,
            "requirements": requirements,
            "actuals": actuals,
            "failures": failures,
        },
    }
