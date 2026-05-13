from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

from .applicability_eval import DEFAULT_APPLICABILITY_GOLD_EVAL_PATH
from .applicability_eval import run_applicability_gold_eval
from .compliance_gold_eval import DEFAULT_COMPLIANCE_GOLD_EVAL_PATH
from .compliance_gold_eval import run_compliance_gold_eval
from .v1_ea_eval import DEFAULT_V1_EA_EVAL_PATH
from .v1_ea_eval import run_v1_ea_review_eval


GOLD_COVERAGE_EVAL_SCHEMA_VERSION = "gold-coverage-eval-v1"
GOLD_COVERAGE_EVAL_RESULTS_SCHEMA_VERSION = "gold-coverage-eval-results-v1"
DEFAULT_GOLD_COVERAGE_MANIFEST_PATH = Path("config/gold_coverage_v1.json")


@dataclass(frozen=True)
class GoldCoverageEvalResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def run_gold_coverage_eval(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_GOLD_COVERAGE_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> GoldCoverageEvalResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    results_output_dir = (
        Path(results_dir) if results_dir else output_dir / "reviews" / "gold_coverage_eval"
    )
    output_path = results_output_dir / "gold_coverage_eval_results.json"

    applicability_summary = _load_or_run_applicability_summary(
        manifest=manifest,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )
    compliance_summary = _load_or_run_compliance_summary(
        manifest=manifest,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )
    review_results = [
        _review_contract_result(
            spec=spec,
            manifest_path=manifest_path,
            output_dir=output_dir,
        )
        for spec in manifest.get("review_contracts", [])
    ]

    thresholds = _int_dict(manifest.get("coverage_thresholds"))
    family_group_coverage = applicability_summary.get("family_group_coverage", {})
    required_theme_ids = _string_list(
        manifest.get("required_theme_ids")
        or family_group_coverage.get("required_group_ids")
    )
    theme_results = [
        _theme_result(
            theme_id=theme_id,
            applicability_summary=applicability_summary,
            compliance_summary=compliance_summary,
        )
        for theme_id in required_theme_ids
    ]
    passed_theme_count = sum(1 for item in theme_results if item["passed"])
    theme_failure_ids = sorted(item["theme_id"] for item in theme_results if not item["passed"])

    reviewer_ready_review_count = sum(
        1 for result in review_results if result["contract_status"] == "reviewer_ready"
    )
    typed_blocked_review_count = sum(
        1 for result in review_results if result["contract_status"] == "typed_blocked"
    )
    distinct_forest_ids = sorted(
        {
            str(result.get("forest_unit_id"))
            for result in review_results
            if str(result.get("forest_unit_id") or "").strip()
        }
    )
    distinct_package_style_tags = sorted(
        {
            str(tag)
            for result in review_results
            for tag in result.get("package_style_tags", [])
            if str(tag).strip()
        }
    )
    missing_package_authority_count = sum(
        1 for result in review_results if not result["package_authority"]["passed"]
    )
    missing_required_review_contract_count = sum(
        1 for result in review_results if result["missing_contract"]
    )
    threshold_failures = _threshold_failures(
        thresholds=thresholds,
        passed_theme_count=passed_theme_count,
        family_group_coverage=family_group_coverage,
        applicability_summary=applicability_summary,
        compliance_summary=compliance_summary,
        review_results=review_results,
        distinct_forest_count=len(distinct_forest_ids),
        distinct_package_style_count=len(distinct_package_style_tags),
        reviewer_ready_review_count=reviewer_ready_review_count,
        typed_blocked_review_count=typed_blocked_review_count,
        missing_required_review_contract_count=missing_required_review_contract_count,
        missing_package_authority_count=missing_package_authority_count,
    )
    failure_category_counts = _failure_category_counts(
        applicability_summary=applicability_summary,
        compliance_summary=compliance_summary,
        theme_results=theme_results,
        review_results=review_results,
        threshold_failures=threshold_failures,
    )
    passed = (
        bool(applicability_summary.get("passed"))
        and bool(compliance_summary.get("passed"))
        and all(result["passed"] for result in review_results)
        and not theme_failure_ids
        and not threshold_failures
    )
    summary = {
        "schema_version": GOLD_COVERAGE_EVAL_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(results_output_dir),
        "output_path": str(output_path),
        "gold_coverage_eval_id": manifest.get("id"),
        "gold_coverage_eval_version": manifest.get("version"),
        "passed": passed,
        "required_theme_ids": required_theme_ids,
        "required_theme_count": len(required_theme_ids),
        "passed_theme_count": passed_theme_count,
        "theme_failure_ids": theme_failure_ids,
        "required_high_priority_family_id_count": family_group_coverage.get(
            "required_high_priority_family_id_count",
            0,
        ),
        "unmapped_high_priority_family_count": family_group_coverage.get(
            "unmapped_high_priority_family_count",
            0,
        ),
        "applicability_gold_case_count": applicability_summary.get("case_count", 0),
        "compliance_gold_case_count": compliance_summary.get("case_count", 0),
        "required_review_contract_count": len(review_results),
        "distinct_forest_count": len(distinct_forest_ids),
        "distinct_forest_ids": distinct_forest_ids,
        "distinct_package_style_count": len(distinct_package_style_tags),
        "distinct_package_style_tags": distinct_package_style_tags,
        "reviewer_ready_review_count": reviewer_ready_review_count,
        "typed_blocked_review_count": typed_blocked_review_count,
        "missing_required_review_contract_count": missing_required_review_contract_count,
        "missing_package_authority_count": missing_package_authority_count,
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "theme_results": theme_results,
        "applicability_gold": {
            "gold_file": applicability_summary.get("gold_file"),
            "passed": applicability_summary.get("passed"),
            "promotion_ready": applicability_summary.get("promotion_ready"),
            "source_chunk_count": applicability_summary.get("source_chunk_count"),
            "family_group_coverage": family_group_coverage,
        },
        "compliance_gold": {
            "gold_file": compliance_summary.get("gold_file"),
            "passed": compliance_summary.get("passed"),
            "promotion_ready": compliance_summary.get("promotion_ready"),
            "coverage_tags": compliance_summary.get("coverage_tags", []),
            "package_style_tags": compliance_summary.get("package_style_tags", []),
        },
        "review_contracts": review_results,
    }
    results_output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return GoldCoverageEvalResult(
        manifest_path=manifest_path,
        output_dir=results_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _load_or_run_applicability_summary(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    spec = manifest.get("applicability_gold")
    if not isinstance(spec, dict):
        raise ValueError("gold coverage manifest requires applicability_gold")
    results_path = spec.get("results_path")
    if results_path:
        return _load_summary(_resolve_repo_path(str(results_path), manifest_path))
    gold_file = _resolve_repo_path(
        str(spec.get("gold_file") or DEFAULT_APPLICABILITY_GOLD_EVAL_PATH),
        manifest_path,
    )
    return run_applicability_gold_eval(output_dir=output_dir, gold_file=gold_file).summary


def _load_or_run_compliance_summary(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    spec = manifest.get("compliance_gold")
    if not isinstance(spec, dict):
        raise ValueError("gold coverage manifest requires compliance_gold")
    results_path = spec.get("results_path")
    if results_path:
        return _load_summary(_resolve_repo_path(str(results_path), manifest_path))
    gold_file = _resolve_repo_path(
        str(spec.get("gold_file") or DEFAULT_COMPLIANCE_GOLD_EVAL_PATH),
        manifest_path,
    )
    return run_compliance_gold_eval(output_dir=output_dir, gold_file=gold_file).summary


def _review_contract_result(
    *,
    spec: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    review_id = str(spec.get("review_id") or "").strip()
    if not review_id:
        raise ValueError("review_contracts entries require review_id")
    results_path = spec.get("results_path")
    eval_file = _resolve_repo_path(
        str(spec.get("eval_file") or DEFAULT_V1_EA_EVAL_PATH),
        manifest_path,
    )
    summary = (
        _load_summary(_resolve_repo_path(str(results_path), manifest_path))
        if results_path
        else run_v1_ea_review_eval(
            output_dir=output_dir,
            review_id=review_id,
            eval_file=eval_file,
        ).summary
    )
    package_authority = _package_authority_result(
        authority_spec=spec.get("package_authority"),
        manifest_path=manifest_path,
    )
    forest_unit_id = str(summary.get("forest_unit_id") or spec.get("forest_unit_id") or "").strip()
    package_style_tags = _string_list(
        summary.get("package_style_tags") or spec.get("package_style_tags")
    )
    actual_review_id = str(summary.get("review_id") or "").strip()
    missing_contract = actual_review_id != review_id
    return {
        "review_id": review_id,
        "actual_review_id": actual_review_id,
        "eval_file": str(eval_file),
        "passed": bool(summary.get("passed")) and not missing_contract and package_authority["passed"],
        "contract_status": str(summary.get("contract_status") or "mismatch"),
        "forest_unit_id": forest_unit_id,
        "package_style_tags": package_style_tags,
        "actual_overall_passed": bool(summary.get("actual_overall_passed", summary.get("passed"))),
        "broader_ea_passed": bool(summary.get("broader_ea_passed")),
        "forest_plan_passed": bool(summary.get("forest_plan_passed")),
        "failure_category_counts": summary.get("failure_category_counts", {}),
        "forest_plan_failure_category_counts": summary.get(
            "forest_plan_failure_category_counts",
            {},
        ),
        "package_authority": package_authority,
        "missing_contract": missing_contract,
        "summary_path": str(results_path) if results_path else summary.get("output_path"),
    }


def _package_authority_result(
    *,
    authority_spec: Any,
    manifest_path: Path,
) -> dict[str, Any]:
    if not isinstance(authority_spec, dict):
        return {
            "passed": False,
            "failure_reasons": ["missing_package_authority"],
            "modes": [],
        }
    modes = []
    failure_reasons = []
    replay_context = authority_spec.get("replay_context_path")
    intake_path = authority_spec.get("intake_package_path")
    details: dict[str, Any] = {}
    if replay_context:
        modes.append("replay_context")
        replay_path = _resolve_repo_path(str(replay_context), manifest_path)
        details["replay_context_path"] = str(replay_path)
        if not replay_path.exists():
            failure_reasons.append("replay_context_missing")
        else:
            payload = _read_json(replay_path)
            catalog_dir = _resolve_context_path(replay_path, Path(str(payload.get("catalog_dir") or "")))
            package_path = payload.get("package_path")
            details["replay_context_catalog_dir"] = str(catalog_dir)
            details["replay_context_catalog_dir_exists"] = catalog_dir.exists()
            if not catalog_dir.exists():
                failure_reasons.append("replay_context_catalog_dir_missing")
            if package_path:
                resolved_package_path = _resolve_context_path(
                    replay_path,
                    Path(str(package_path)),
                )
                details["replay_context_package_path"] = str(resolved_package_path)
                details["replay_context_package_path_exists"] = resolved_package_path.exists()
                if not resolved_package_path.exists():
                    failure_reasons.append("replay_context_package_path_missing")
    if intake_path:
        modes.append("intake_path")
        resolved_intake = _resolve_repo_path(str(intake_path), manifest_path)
        details["intake_package_path"] = str(resolved_intake)
        details["intake_package_path_exists"] = resolved_intake.exists()
        if not resolved_intake.exists():
            failure_reasons.append("intake_package_path_missing")
    if not modes:
        failure_reasons.append("missing_package_authority")
    return {
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
        "modes": modes,
        **details,
    }


def _theme_result(
    *,
    theme_id: str,
    applicability_summary: dict[str, Any],
    compliance_summary: dict[str, Any],
) -> dict[str, Any]:
    family_group_coverage = applicability_summary.get("family_group_coverage", {})
    applicability_passed = all(
        theme_id in family_group_coverage.get(key, [])
        for key in (
            "positive_covered_group_ids",
            "negative_covered_group_ids",
            "adjudicated_covered_group_ids",
        )
    )
    compliance_passed = theme_id in compliance_summary.get("coverage_tags", [])
    return {
        "theme_id": theme_id,
        "passed": applicability_passed and compliance_passed,
        "applicability_group_present": applicability_passed,
        "compliance_group_present": compliance_passed,
    }


def _threshold_failures(
    *,
    thresholds: dict[str, int],
    passed_theme_count: int,
    family_group_coverage: dict[str, Any],
    applicability_summary: dict[str, Any],
    compliance_summary: dict[str, Any],
    review_results: list[dict[str, Any]],
    distinct_forest_count: int,
    distinct_package_style_count: int,
    reviewer_ready_review_count: int,
    typed_blocked_review_count: int,
    missing_required_review_contract_count: int,
    missing_package_authority_count: int,
) -> list[dict[str, Any]]:
    failures = []
    for metric, actual in (
        ("required_theme_count", passed_theme_count),
        (
            "required_high_priority_family_id_count",
            int(family_group_coverage.get("required_high_priority_family_id_count") or 0),
        ),
        (
            "unmapped_high_priority_family_count_max",
            int(family_group_coverage.get("unmapped_high_priority_family_count") or 0),
        ),
        ("applicability_gold_case_count_min", int(applicability_summary.get("case_count") or 0)),
        ("compliance_gold_case_count_min", int(compliance_summary.get("case_count") or 0)),
        ("required_review_contract_count", len(review_results)),
        ("distinct_forest_count_min", distinct_forest_count),
        ("distinct_package_style_count_min", distinct_package_style_count),
        ("reviewer_ready_review_count_min", reviewer_ready_review_count),
        ("typed_blocked_review_count_min", typed_blocked_review_count),
        ("missing_required_review_contract_count_max", missing_required_review_contract_count),
        ("missing_package_authority_count_max", missing_package_authority_count),
    ):
        expected = thresholds.get(metric)
        if expected is None:
            continue
        if metric.endswith("_max"):
            if actual > expected:
                failures.append({"metric": metric, "expected_max": expected, "actual": actual})
        else:
            if actual < expected:
                failures.append({"metric": metric, "expected_min": expected, "actual": actual})
    for result in review_results:
        if result["passed"]:
            continue
        failures.append(
            {
                "metric": "review_contract_passed",
                "review_id": result["review_id"],
                "contract_status": result["contract_status"],
            }
        )
    return failures


def _failure_category_counts(
    *,
    applicability_summary: dict[str, Any],
    compliance_summary: dict[str, Any],
    theme_results: list[dict[str, Any]],
    review_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    def bump(category: str) -> None:
        counts[category] = counts.get(category, 0) + 1

    if not applicability_summary.get("passed"):
        bump("applicability_gold_failed")
    if not compliance_summary.get("passed"):
        bump("compliance_gold_failed")
    for theme in theme_results:
        if not theme["passed"]:
            bump("missing_named_theme_coverage")
    for result in review_results:
        if result["missing_contract"]:
            bump("missing_required_review_contract")
        if not result["package_authority"]["passed"]:
            bump("missing_package_authority")
        if result["contract_status"] == "mismatch":
            bump("review_contract_mismatch")
    for failure in threshold_failures:
        metric = str(failure.get("metric") or "")
        if metric.endswith("distinct_package_style_count_min"):
            bump("insufficient_package_style_diversity")
        elif metric.endswith("distinct_forest_count_min"):
            bump("insufficient_forest_diversity")
        elif metric == "required_theme_count":
            bump("missing_named_theme_coverage")
        elif metric == "missing_package_authority_count_max":
            bump("missing_package_authority")
        elif metric == "missing_required_review_contract_count_max":
            bump("missing_required_review_contract")
    return counts


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("gold coverage manifest must be a JSON object")
    if manifest.get("schema_version") != GOLD_COVERAGE_EVAL_SCHEMA_VERSION:
        raise ValueError(
            f"gold coverage manifest must use schema_version={GOLD_COVERAGE_EVAL_SCHEMA_VERSION!r}"
        )
    if not str(manifest.get("id") or "").strip():
        raise ValueError("gold coverage manifest requires id")
    if not isinstance(manifest.get("review_contracts"), list) or not manifest["review_contracts"]:
        raise ValueError("gold coverage manifest requires review_contracts")


def _load_summary(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    summary = payload.get("summary") if isinstance(payload, dict) else None
    return summary if isinstance(summary, dict) else payload


def _resolve_repo_path(value: str, manifest_path: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (manifest_path.parent / path).resolve()


def _resolve_context_path(config_path: Path, value: Path) -> Path:
    base_dir = config_path.resolve().parents[2]
    return value if value.is_absolute() else (base_dir / value).resolve()


def _int_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            result[str(key)] = int(raw)
        except (TypeError, ValueError):
            continue
    return result


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(item).strip() for item in value if str(item).strip())


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
