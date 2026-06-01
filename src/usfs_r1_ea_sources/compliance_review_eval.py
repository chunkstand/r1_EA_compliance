from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json

from .compliance_review import run_compliance_review
from .compliance_review_eval_contract import COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION
from .compliance_review_eval_contract import SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS
from .compliance_review_eval_contract import (
    load_compliance_review_eval_contract as _load_compliance_review_eval_contract,
)
from .compliance_review_eval_contract import (
    validate_compliance_review_eval_cases_against_rule_pack as _validate_compliance_review_eval_cases_against_rule_pack,
)
from .compliance_review_eval_generated import GENERATED_RULE_PACK_EXPECTATION_FIELDS
from .compliance_review_eval_generated import EvalRulePackResolution
from .compliance_review_eval_generated import _case_allows_generated_rule_pack_diagnostic
from .compliance_review_eval_generated import _case_requires_generated_rule_pack
from .compliance_review_eval_generated import _generated_diagnostic_rule_ids
from .compliance_review_eval_generated import _generated_rule_pack_for_eval_case
from .compliance_review_eval_scoring import case_rate as _case_rate
from .compliance_review_eval_scoring import (
    compliance_review_eval_case_result as _compliance_review_eval_case_result,
)
from .compliance_review_eval_scoring import (
    compliance_review_eval_coverage_check as _compliance_review_eval_coverage_check,
)
from .compliance_review_eval_scoring import (
    applicability_gate_is_diagnostic as _applicability_gate_is_diagnostic,
)
from .compliance_review_eval_scoring import (
    effective_eval_case_expectations as _effective_eval_case_expectations,
)
from .compliance_review_eval_scoring import (
    failure_category_counts as _failure_category_counts,
)
from .compliance_review_eval_scoring import (
    eval_package_path as _eval_package_path,
)
from .compliance_review_eval_scoring import (
    expected_subset_mismatches as _expected_subset_mismatches,
)
from .compliance_review_eval_scoring import (
    source_backed_expected_string_list_map as _source_backed_expected_string_list_map,
)
from .compliance_review_eval_scoring import (
    finding_source_record_ids_with_aliases as _finding_source_record_ids_with_aliases,
)
from .compliance_review_eval_scoring import (
    normalized_eval_findings_by_rule as _normalized_eval_findings_by_rule,
)
from .compliance_review_eval_scoring import rate as _rate
from .compliance_review_eval_scoring import read_json as _read_json
from .eval_metrics import contract_snapshot, metric_threshold_check
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_resolver import DEFAULT_FOREST_PLAN_PROFILE_ID
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import SAFE_ID_RE
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


COMPLIANCE_REVIEW_EVAL_RESULTS_SCHEMA_VERSION = "compliance-review-eval-results-v1"
DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH = Path("config/compliance_review_eval_seed.json")

__all__ = [
    "COMPLIANCE_REVIEW_EVAL_RESULTS_SCHEMA_VERSION",
    "COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION",
    "DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH",
    "GENERATED_RULE_PACK_EXPECTATION_FIELDS",
    "SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS",
    "ComplianceReviewEvalResult",
    "EvalRulePackResolution",
    "_applicability_gate_is_diagnostic",
    "_case_allows_generated_rule_pack_diagnostic",
    "_case_requires_generated_rule_pack",
    "_effective_eval_case_expectations",
    "_expected_subset_mismatches",
    "_finding_source_record_ids_with_aliases",
    "_generated_diagnostic_rule_ids",
    "_normalized_eval_findings_by_rule",
    "_source_backed_expected_string_list_map",
    "_validate_compliance_review_eval_cases_against_rule_pack",
    "run_compliance_review_eval",
]


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
    rule_claim_links_path: Path | None = None,
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
        Path(results_dir) if results_dir else output_dir / "reviews" / "compliance_review_eval"
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
        rule_pack_resolution = (
            _generated_rule_pack_for_eval_case(
                case=case,
                output_dir=output_dir,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                source_set_id=source_set_id,
                index_path=index_path,
                review_id=review_id,
                review_dir=review_dir,
                source_top_k=case_source_top_k,
                package_top_k=case_package_top_k,
                chunk_max_chars=chunk_max_chars,
                chunk_overlap_chars=chunk_overlap_chars,
                docling_ocr=docling_ocr,
                docling_timeout_seconds=docling_timeout_seconds,
            )
            if requires_generated_rule_pack
            else EvalRulePackResolution(rule_pack_path=rule_pack_path)
        )
        result = run_compliance_review(
            package_path=package_path,
            output_dir=output_dir,
            rule_pack_path=rule_pack_resolution.rule_pack_path,
            source_set_id=source_set_id,
            index_path=index_path,
            rule_claim_links_path=rule_claim_links_path,
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
            allow_generated_rule_pack_diagnostic=(
                rule_pack_resolution.allow_generated_rule_pack_diagnostic
            ),
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
        "package_evidence_match_rate": _case_rate(case_results, "expected_package_evidence_match"),
        "source_evidence_match_rate": _case_rate(case_results, "expected_source_evidence_match"),
        "source_claim_link_match_rate": _case_rate(
            case_results,
            "expected_source_claim_links_match",
        ),
        "source_record_match_rate": _case_rate(case_results, "expected_source_record_ids_match"),
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


def _validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dot, underscore, or hyphen."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
