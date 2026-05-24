from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_PATH = (
    REPO_ROOT / "config" / "forest_specific_example_package_registry_v1.json"
)
FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_SCHEMA_VERSION = (
    "forest-specific-example-package-registry-v1"
)
FOREST_SPECIFIC_EXAMPLE_PACKAGE_EVAL_RESULTS_SCHEMA_VERSION = (
    "forest-specific-example-package-eval-results-v1"
)
VALID_ROUTING_STATUSES = {
    "profile_eval_guidance_only",
    "real_package_examples_available",
    "typed_blocked_example_available",
}
REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION = "real-package-review-coverage-results-v1"
FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION = "region1-forest-plan-profile-eval-results-v1"


@dataclass(frozen=True)
class ForestSpecificExamplePackageEvalResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def run_forest_specific_example_package_eval(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_PATH,
    results_dir: Path | None = None,
) -> ForestSpecificExamplePackageEvalResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    results_output_dir = (
        Path(results_dir)
        if results_dir
        else output_dir / "reviews" / "forest_specific_example_package_eval"
    )
    results_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_output_dir / "forest_specific_example_package_eval_results.json"

    manifest = _read_json(manifest_path)
    contract_checks, shared_contracts, review_examples, forest_rows, output_fields = (
        _validate_manifest_contract(manifest_path=manifest_path, manifest=manifest)
    )
    review_examples_by_id = {row["example_id"]: row for row in review_examples}
    forest_row_by_id = {row["forest_unit_id"]: row for row in forest_rows}

    review_coverage_manifest_path = _resolve_shared_contract_path(
        manifest_path=manifest_path,
        shared_contracts=shared_contracts,
        contract_id="real_package_review_coverage_manifest",
    )
    profile_eval_manifest_path = _resolve_shared_contract_path(
        manifest_path=manifest_path,
        shared_contracts=shared_contracts,
        contract_id="forest_plan_profile_eval_coverage_manifest",
    )

    review_coverage_results, review_coverage_results_path = _load_or_run_real_package_results(
        output_dir=output_dir,
        manifest_path=review_coverage_manifest_path,
    )
    profile_eval_results, profile_eval_results_path = _load_or_run_profile_eval_results(
        output_dir=output_dir,
        manifest_path=profile_eval_manifest_path,
    )

    profile_rows = profile_eval_results.get("profiles")
    slot_rows = review_coverage_results.get("slots")
    profile_rows_by_forest = {
        str(row["forest_unit_id"]): row for row in profile_rows if isinstance(row, dict)
    }
    slot_rows_by_id = {str(row["slot_id"]): row for row in slot_rows if isinstance(row, dict)}

    contract_checks.extend(
        [
            {
                "name": "real_package_review_coverage_results_schema",
                "passed": review_coverage_results.get("schema_version")
                == REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION,
                "details": {
                    "results_path": str(review_coverage_results_path),
                    "expected": REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION,
                    "actual": review_coverage_results.get("schema_version"),
                },
            },
            {
                "name": "forest_plan_profile_eval_results_schema",
                "passed": profile_eval_results.get("schema_version")
                == FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION,
                "details": {
                    "results_path": str(profile_eval_results_path),
                    "expected": FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION,
                    "actual": profile_eval_results.get("schema_version"),
                },
            },
            {
                "name": "profile_eval_roster_matches_registry",
                "passed": set(profile_rows_by_forest) == set(forest_row_by_id),
                "details": {
                    "registry_forest_unit_ids": sorted(forest_row_by_id),
                    "profile_eval_forest_unit_ids": sorted(profile_rows_by_forest),
                    "missing_in_profile_eval": sorted(
                        set(forest_row_by_id) - set(profile_rows_by_forest)
                    ),
                    "unexpected_in_profile_eval": sorted(
                        set(profile_rows_by_forest) - set(forest_row_by_id)
                    ),
                },
            },
        ]
    )

    forest_results = [
        _forest_result(
            forest_row=forest_row,
            review_examples_by_id=review_examples_by_id,
            slot_rows_by_id=slot_rows_by_id,
            profile_rows_by_forest=profile_rows_by_forest,
        )
        for forest_row in forest_rows
    ]

    declared_routing_status_counts = Counter(
        str(row.get("routing_status") or "").strip() or "<blank>" for row in forest_rows
    )
    actual_routing_status_counts = Counter(
        str(row.get("actual_routing_status") or "").strip() or "<blank>" for row in forest_results
    )
    review_example_count = len(review_examples)
    reviewer_ready_example_count = sum(
        1 for row in review_examples if row.get("expected_contract_status") == "reviewer_ready"
    )
    typed_blocked_example_count = sum(
        1 for row in review_examples if row.get("expected_contract_status") == "typed_blocked"
    )
    distinct_governed_example_forest_count = len(
        {str(row["forest_unit_id"]) for row in review_examples}
    )
    profile_guidance_only_count = declared_routing_status_counts.get("profile_eval_guidance_only", 0)
    covered_forest_count = sum(1 for row in forest_results if row["passed"])
    failed_forest_count = len(forest_results) - covered_forest_count

    threshold_failures = _threshold_failures(
        thresholds=_int_dict(manifest.get("coverage_thresholds")),
        forest_unit_count=len(forest_rows),
        review_example_count=review_example_count,
        reviewer_ready_example_count=reviewer_ready_example_count,
        typed_blocked_example_count=typed_blocked_example_count,
        distinct_governed_example_forest_count=distinct_governed_example_forest_count,
        profile_guidance_only_count=profile_guidance_only_count,
        failed_forest_count=failed_forest_count,
    )
    failure_category_counts = _failure_category_counts(
        forest_results=forest_results,
        threshold_failures=threshold_failures,
    )

    summary = {
        "schema_version": FOREST_SPECIFIC_EXAMPLE_PACKAGE_EVAL_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(results_output_dir),
        "output_path": str(output_path),
        "real_package_review_coverage_manifest_path": str(review_coverage_manifest_path),
        "real_package_review_coverage_results_path": str(review_coverage_results_path),
        "forest_plan_profile_eval_manifest_path": str(profile_eval_manifest_path),
        "forest_plan_profile_eval_results_path": str(profile_eval_results_path),
        "forest_specific_example_package_id": manifest.get("contract_id"),
        "forest_specific_example_package_version": manifest.get("version"),
        "passed": False,
        "forest_unit_count": len(forest_rows),
        "covered_forest_count": covered_forest_count,
        "failed_forest_count": failed_forest_count,
        "review_example_count": review_example_count,
        "reviewer_ready_example_count": reviewer_ready_example_count,
        "typed_blocked_example_count": typed_blocked_example_count,
        "distinct_governed_example_forest_count": distinct_governed_example_forest_count,
        "profile_guidance_only_count": profile_guidance_only_count,
        "declared_routing_status_counts": dict(sorted(declared_routing_status_counts.items())),
        "actual_routing_status_counts": dict(sorted(actual_routing_status_counts.items())),
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "contract_checks": contract_checks,
        "forests": forest_results,
    }
    summary["contract_checks"].append(
        {
            "name": "output_schema_fields_present",
            "passed": not [
                field for field in output_fields if field not in summary and field != "passed"
            ],
            "details": {
                "required_fields": output_fields,
                "missing_fields": [
                    field for field in output_fields if field not in summary and field != "passed"
                ],
            },
        }
    )
    summary["passed"] = (
        all(check["passed"] for check in summary["contract_checks"])
        and not threshold_failures
        and all(row["passed"] for row in forest_results)
    )

    _write_json(output_path, summary)
    return ForestSpecificExamplePackageEvalResult(
        manifest_path=manifest_path,
        output_dir=results_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _validate_manifest_contract(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    contract_checks: list[dict[str, Any]] = [
        {
            "name": "manifest_schema_version",
            "passed": manifest.get("schema_version")
            == FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_SCHEMA_VERSION,
            "details": {
                "path": str(manifest_path),
                "expected": FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_SCHEMA_VERSION,
                "actual": manifest.get("schema_version"),
            },
        },
        {
            "name": "manifest_contract_id_present",
            "passed": bool(str(manifest.get("contract_id") or "").strip()),
            "details": {"contract_id": manifest.get("contract_id")},
        },
        {
            "name": "coverage_thresholds_present",
            "passed": isinstance(manifest.get("coverage_thresholds"), dict),
            "details": {"coverage_thresholds": manifest.get("coverage_thresholds")},
        },
    ]
    output_fields = [
        str(field)
        for field in _string_list((manifest.get("output_schema") or {}).get("required_summary_fields"))
    ]

    raw_shared_contracts = manifest.get("shared_contract_catalog")
    if not isinstance(raw_shared_contracts, list) or not raw_shared_contracts:
        contract_checks.append(
            {
                "name": "shared_contract_catalog_present",
                "passed": False,
                "details": {"shared_contract_catalog": raw_shared_contracts},
            }
        )
        shared_contracts: dict[str, dict[str, Any]] = {}
    else:
        shared_contracts = {
            str(row.get("shared_contract_id")): row
            for row in raw_shared_contracts
            if isinstance(row, dict) and str(row.get("shared_contract_id") or "").strip()
        }
        required_shared_contract_ids = {
            "real_package_review_coverage_manifest",
            "forest_plan_profile_eval_coverage_manifest",
        }
        missing_shared_contract_ids = sorted(required_shared_contract_ids - set(shared_contracts))
        missing_shared_contract_paths = sorted(
            contract_id
            for contract_id, row in shared_contracts.items()
            if not _resolve_manifest_path(manifest_path, row.get("path")).exists()
        )
        contract_checks.extend(
            [
                {
                    "name": "shared_contract_catalog_present",
                    "passed": True,
                    "details": {"shared_contract_ids": sorted(shared_contracts)},
                },
                {
                    "name": "required_shared_contract_ids_present",
                    "passed": not missing_shared_contract_ids,
                    "details": {"missing_shared_contract_ids": missing_shared_contract_ids},
                },
                {
                    "name": "shared_contract_paths_exist",
                    "passed": not missing_shared_contract_paths,
                    "details": {"missing_shared_contract_paths": missing_shared_contract_paths},
                },
            ]
        )

    raw_review_examples = manifest.get("review_examples")
    if not isinstance(raw_review_examples, list) or not raw_review_examples:
        contract_checks.append(
            {
                "name": "review_examples_present",
                "passed": False,
                "details": {"review_examples": raw_review_examples},
            }
        )
        review_examples: list[dict[str, Any]] = []
    else:
        review_examples = [row for row in raw_review_examples if isinstance(row, dict)]
        example_ids = [str(row.get("example_id") or "").strip() for row in review_examples]
        contract_checks.extend(
            [
                {
                    "name": "review_examples_present",
                    "passed": True,
                    "details": {"review_example_count": len(review_examples)},
                },
                {
                    "name": "review_example_ids_unique",
                    "passed": len(example_ids) == len(set(example_ids)) and all(example_ids),
                    "details": {"example_ids": example_ids},
                },
            ]
        )

    raw_forest_rows = manifest.get("forest_routing")
    if not isinstance(raw_forest_rows, list) or not raw_forest_rows:
        contract_checks.append(
            {
                "name": "forest_routing_present",
                "passed": False,
                "details": {"forest_routing": raw_forest_rows},
            }
        )
        forest_rows: list[dict[str, Any]] = []
    else:
        forest_rows = [row for row in raw_forest_rows if isinstance(row, dict)]
        forest_ids = [str(row.get("forest_unit_id") or "").strip() for row in forest_rows]
        invalid_routing_status_ids = sorted(
            str(row.get("forest_unit_id") or "").strip()
            for row in forest_rows
            if str(row.get("routing_status") or "").strip() not in VALID_ROUTING_STATUSES
        )
        contract_checks.extend(
            [
                {
                    "name": "forest_routing_present",
                    "passed": True,
                    "details": {"forest_unit_count": len(forest_rows)},
                },
                {
                    "name": "forest_unit_ids_unique",
                    "passed": len(forest_ids) == len(set(forest_ids)) and all(forest_ids),
                    "details": {"forest_unit_ids": forest_ids},
                },
                {
                    "name": "forest_routing_statuses_are_valid",
                    "passed": not invalid_routing_status_ids,
                    "details": {
                        "valid_routing_statuses": sorted(VALID_ROUTING_STATUSES),
                        "invalid_forest_unit_ids": invalid_routing_status_ids,
                    },
                },
            ]
        )

    actual_summary = {
        "forest_unit_count": len(forest_rows),
        "profile_guidance_only_count": sum(
            1
            for row in forest_rows
            if str(row.get("routing_status") or "").strip() == "profile_eval_guidance_only"
        ),
        "review_example_count": len(review_examples),
        "reviewer_ready_example_count": sum(
            1 for row in review_examples if row.get("expected_contract_status") == "reviewer_ready"
        ),
        "typed_blocked_example_count": sum(
            1 for row in review_examples if row.get("expected_contract_status") == "typed_blocked"
        ),
    }
    contract_checks.append(
        {
            "name": "summary_matches_declared_registry_counts",
            "passed": manifest.get("summary") == actual_summary,
            "details": {
                "declared_summary": manifest.get("summary"),
                "actual_summary": actual_summary,
            },
        }
    )
    return contract_checks, shared_contracts, review_examples, forest_rows, output_fields


def _forest_result(
    *,
    forest_row: dict[str, Any],
    review_examples_by_id: dict[str, dict[str, Any]],
    slot_rows_by_id: dict[str, dict[str, Any]],
    profile_rows_by_forest: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    forest_unit_id = str(forest_row.get("forest_unit_id") or "").strip()
    declared_routing_status = str(forest_row.get("routing_status") or "").strip()
    applicable_to_forest_unit_ids = _string_list(forest_row.get("applicable_to_forest_unit_ids"))
    primary_example_id = _string_or_none(forest_row.get("primary_example_id"))
    supplemental_example_ids = _string_list(forest_row.get("supplemental_example_ids"))
    required_fixture_family_ids = _string_list(forest_row.get("required_fixture_family_ids"))
    failure_reasons: list[str] = []

    if forest_unit_id not in applicable_to_forest_unit_ids:
        failure_reasons.append("forest_routing_applicability_mismatch")

    profile_row = profile_rows_by_forest.get(forest_unit_id)
    profile_eval_passed = bool(profile_row and profile_row.get("passed"))
    if profile_row is None:
        failure_reasons.append("profile_eval_missing")
    elif not profile_eval_passed:
        failure_reasons.append("profile_eval_failed")

    profile_fixture_ids = sorted(
        str(tag) for tag in ((profile_row or {}).get("required_fixture_family_ids") or []) if str(tag)
    )
    if profile_fixture_ids and profile_fixture_ids != sorted(required_fixture_family_ids):
        failure_reasons.append("profile_fixture_family_mismatch")

    example_ids = [example_id for example_id in [primary_example_id, *supplemental_example_ids] if example_id]
    example_results = [
        _example_result(
            forest_unit_id=forest_unit_id,
            example_id=example_id,
            review_examples_by_id=review_examples_by_id,
            slot_rows_by_id=slot_rows_by_id,
        )
        for example_id in example_ids
    ]
    failure_reasons.extend(
        reason
        for result in example_results
        for reason in result["failure_reasons"]
    )

    primary_example_result = example_results[0] if example_results else None
    if declared_routing_status == "profile_eval_guidance_only":
        if primary_example_id or supplemental_example_ids:
            failure_reasons.append("profile_only_forest_declares_review_example")
        actual_routing_status = (
            "profile_eval_guidance_only" if profile_eval_passed else "missing_or_failed"
        )
    elif declared_routing_status == "real_package_examples_available":
        if primary_example_result is None:
            failure_reasons.append("primary_example_missing")
            actual_routing_status = "missing_or_failed"
        else:
            if primary_example_result["actual_contract_status"] != "reviewer_ready":
                failure_reasons.append("primary_example_contract_status_mismatch")
            if not primary_example_result["passed"]:
                failure_reasons.append("primary_example_failed")
            actual_routing_status = (
                "real_package_examples_available"
                if primary_example_result["actual_contract_status"] == "reviewer_ready"
                else "missing_or_failed"
            )
    elif declared_routing_status == "typed_blocked_example_available":
        if primary_example_result is None:
            failure_reasons.append("primary_example_missing")
            actual_routing_status = "missing_or_failed"
        else:
            if primary_example_result["actual_contract_status"] != "typed_blocked":
                failure_reasons.append("primary_example_contract_status_mismatch")
            if not primary_example_result["passed"]:
                failure_reasons.append("primary_example_failed")
            actual_routing_status = (
                "typed_blocked_example_available"
                if primary_example_result["actual_contract_status"] == "typed_blocked"
                else "missing_or_failed"
            )
    else:
        actual_routing_status = "missing_or_failed"
        failure_reasons.append("invalid_declared_routing_status")

    if actual_routing_status != declared_routing_status:
        failure_reasons.append("routing_status_mismatch")

    return {
        "forest_unit_id": forest_unit_id,
        "forest_unit_label": str(forest_row.get("forest_unit_label") or ""),
        "declared_routing_status": declared_routing_status,
        "actual_routing_status": actual_routing_status,
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
        "applicable_to_forest_unit_ids": applicable_to_forest_unit_ids,
        "primary_example_id": primary_example_id,
        "supplemental_example_ids": supplemental_example_ids,
        "required_fixture_family_ids": required_fixture_family_ids,
        "profile_eval_present": profile_row is not None,
        "profile_eval_passed": profile_eval_passed,
        "profile_eval_status": _string_or_none((profile_row or {}).get("coverage_status")),
        "profile_eval_failure_reasons": sorted(
            str(reason)
            for reason in ((profile_row or {}).get("failure_reasons") or [])
            if str(reason).strip()
        ),
        "example_results": example_results,
        "guidance_note": str(forest_row.get("guidance_note") or ""),
    }


def _example_result(
    *,
    forest_unit_id: str,
    example_id: str,
    review_examples_by_id: dict[str, dict[str, Any]],
    slot_rows_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failure_reasons: list[str] = []
    example_row = review_examples_by_id.get(example_id)
    if example_row is None:
        return {
            "example_id": example_id,
            "passed": False,
            "failure_reasons": ["review_example_missing"],
        }

    applicable_forest_unit_ids = _string_list(example_row.get("applicable_forest_unit_ids"))
    if forest_unit_id not in applicable_forest_unit_ids:
        failure_reasons.append("review_example_not_applicable_to_forest")

    slot_id = str(example_row.get("coverage_slot_id") or "").strip()
    slot_row = slot_rows_by_id.get(slot_id)
    if slot_row is None:
        failure_reasons.append("coverage_slot_missing")
        actual_contract_status = None
        slot_passed = False
        summary_path = None
        package_authority_passed = False
    else:
        actual_contract_status = _string_or_none(slot_row.get("actual_contract_status"))
        slot_passed = bool(slot_row.get("passed"))
        summary_path = _string_or_none(slot_row.get("summary_path"))
        package_authority_passed = bool((slot_row.get("package_authority") or {}).get("passed"))
        if not slot_passed:
            failure_reasons.append("coverage_slot_failed")
        if actual_contract_status != _string_or_none(example_row.get("expected_contract_status")):
            failure_reasons.append("coverage_slot_contract_status_mismatch")

    return {
        "example_id": example_id,
        "review_id": _string_or_none(example_row.get("review_id")),
        "coverage_slot_id": slot_id,
        "expected_contract_status": _string_or_none(example_row.get("expected_contract_status")),
        "actual_contract_status": actual_contract_status,
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
        "summary_path": summary_path,
        "package_authority_passed": package_authority_passed,
    }


def _threshold_failures(
    *,
    thresholds: dict[str, int],
    forest_unit_count: int,
    review_example_count: int,
    reviewer_ready_example_count: int,
    typed_blocked_example_count: int,
    distinct_governed_example_forest_count: int,
    profile_guidance_only_count: int,
    failed_forest_count: int,
) -> list[dict[str, Any]]:
    failures = []
    for metric, actual in (
        ("required_forest_unit_count", forest_unit_count),
        ("review_example_count_min", review_example_count),
        ("reviewer_ready_example_count_min", reviewer_ready_example_count),
        ("typed_blocked_example_count_min", typed_blocked_example_count),
        ("distinct_governed_example_forest_count_min", distinct_governed_example_forest_count),
        ("profile_guidance_only_count_max", profile_guidance_only_count),
        ("failed_forest_count_max", failed_forest_count),
    ):
        expected = thresholds.get(metric)
        if expected is None:
            continue
        if metric.endswith("_max"):
            if actual > expected:
                failures.append({"metric": metric, "expected_max": expected, "actual": actual})
        elif metric.endswith("_min"):
            if actual < expected:
                failures.append({"metric": metric, "expected_min": expected, "actual": actual})
        else:
            if actual != expected:
                failures.append({"metric": metric, "expected": expected, "actual": actual})
    return failures


def _failure_category_counts(
    *,
    forest_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for result in forest_results:
        for reason in result["failure_reasons"]:
            counts[str(reason)] += 1
    for failure in threshold_failures:
        counts[f"threshold_{failure['metric']}"] += 1
    return counts


def _load_or_run_real_package_results(
    *,
    output_dir: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], Path]:
    results_path = output_dir / "reviews" / "real_package_review_coverage_eval" / (
        "real_package_review_coverage_eval_results.json"
    )
    if results_path.exists():
        return _read_json(results_path), results_path
    runner = import_module("usfs_r1_ea_sources.real_package_review_coverage_eval")
    result = runner.run_real_package_review_coverage_eval(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )
    return result.summary, result.output_path


def _load_or_run_profile_eval_results(
    *,
    output_dir: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], Path]:
    results_path = output_dir / "evaluations" / "forest_plan_profile" / (
        "forest_plan_profile_eval_results.json"
    )
    if results_path.exists():
        return _read_json(results_path), results_path
    runner = import_module("usfs_r1_ea_sources.forest_plan_profile_eval")
    result = runner.run_forest_plan_profile_eval(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )
    return result.summary, result.output_path


def _resolve_shared_contract_path(
    *,
    manifest_path: Path,
    shared_contracts: dict[str, dict[str, Any]],
    contract_id: str,
) -> Path:
    row = shared_contracts.get(contract_id, {})
    return _resolve_manifest_path(manifest_path, row.get("path"))


def _resolve_manifest_path(manifest_path: Path, path_value: Any) -> Path:
    raw_path = Path(str(path_value or ""))
    if raw_path.is_absolute():
        return raw_path
    candidate = manifest_path.parent / raw_path
    if candidate.exists():
        return candidate
    return REPO_ROOT / raw_path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _string_or_none(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _int_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): int(number)
        for key, number in value.items()
        if str(key).strip() and isinstance(number, int)
    }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
