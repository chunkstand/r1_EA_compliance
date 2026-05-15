from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import re

from .forest_plan_profiles import load_forest_plan_profiles


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FOREST_PLAN_PROFILE_EVAL_MANIFEST_PATH = (
    REPO_ROOT / "config" / "region1_forest_plan_profile_eval_coverage_v1.json"
)
FOREST_PLAN_PROFILE_EVAL_SCHEMA_VERSION = "region1-forest-plan-profile-eval-coverage-v1"
FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION = "region1-forest-plan-profile-eval-results-v1"
_SOURCE_SET_ID_PATTERN = re.compile(r"(source-set-[^/]+)")


@dataclass(frozen=True)
class ForestPlanProfileEvalResult:
    summary: dict[str, Any]
    output_path: Path
    report_path: Path


@dataclass(frozen=True)
class _ProfileContractSpec:
    forest_unit_id: str
    profile_kind: str
    required_coverage_status: str
    minimum_positive_case_count: int
    minimum_hard_negative_case_count: int
    minimum_selected_profile_compliance_case_count: int
    required_fixture_family_ids: tuple[str, ...]


def run_forest_plan_profile_eval(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_FOREST_PLAN_PROFILE_EVAL_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> ForestPlanProfileEvalResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    results_output_dir = (
        Path(results_dir) if results_dir else output_dir / "evaluations" / "forest_plan_profile"
    )
    results_output_dir.mkdir(parents=True, exist_ok=True)

    manifest = _read_json(manifest_path)
    contract_checks, profile_specs, output_expectations = _validate_manifest_contract(
        manifest_path=manifest_path,
        manifest=manifest,
    )
    readiness_path = _manifest_repo_path(manifest_path, manifest.get("readiness_path"))
    forest_plan_profiles_path = _manifest_repo_path(
        manifest_path,
        manifest.get("forest_plan_profiles_path"),
    )
    readiness_state = _load_readiness_state(readiness_path)
    contract_checks.extend(readiness_state["contract_checks"])
    profile_collection_state = _load_profile_collection_state(forest_plan_profiles_path)
    contract_checks.extend(profile_collection_state["contract_checks"])

    manifest_profile_ids = [spec.forest_unit_id for spec in profile_specs]
    readiness_profile_ids = sorted(readiness_state["rows_by_forest_unit_id"])
    configured_profile_ids = sorted(profile_collection_state["profiles_by_forest_unit_id"])
    contract_checks.extend(
        [
            {
                "name": "readiness_roster_matches_manifest",
                "passed": set(manifest_profile_ids) == set(readiness_profile_ids),
                "details": {
                    "manifest_profile_ids": sorted(manifest_profile_ids),
                    "readiness_profile_ids": readiness_profile_ids,
                    "missing_in_readiness": sorted(
                        set(manifest_profile_ids) - set(readiness_profile_ids)
                    ),
                    "unexpected_in_readiness": sorted(
                        set(readiness_profile_ids) - set(manifest_profile_ids)
                    ),
                },
            },
            {
                "name": "configured_profile_roster_matches_manifest",
                "passed": set(manifest_profile_ids) == set(configured_profile_ids),
                "details": {
                    "manifest_profile_ids": sorted(manifest_profile_ids),
                    "configured_profile_ids": configured_profile_ids,
                    "missing_in_profiles": sorted(
                        set(manifest_profile_ids) - set(configured_profile_ids)
                    ),
                    "unexpected_in_profiles": sorted(
                        set(configured_profile_ids) - set(manifest_profile_ids)
                    ),
                },
            },
        ]
    )

    expected_active_source_set_ids = _string_tuple(manifest.get("expected_active_source_set_ids"))
    actual_active_source_set_ids = readiness_state["active_source_set_ids"]
    contract_checks.append(
        {
            "name": "active_source_set_binding_matches_manifest",
            "passed": bool(expected_active_source_set_ids)
            and actual_active_source_set_ids == sorted(expected_active_source_set_ids),
            "details": {
                "expected_active_source_set_ids": sorted(expected_active_source_set_ids),
                "actual_active_source_set_ids": actual_active_source_set_ids,
            },
        }
    )

    profile_results = [
        _profile_result(
            spec=spec,
            readiness_row=readiness_state["rows_by_forest_unit_id"].get(spec.forest_unit_id),
            profile_collection_state=profile_collection_state,
        )
        for spec in profile_specs
    ]
    threshold_failures = _threshold_failures(
        thresholds=manifest.get("coverage_thresholds"),
        status_counts=readiness_state["status_counts"],
    )
    failure_category_counts = _failure_category_counts(
        profile_results=profile_results,
        threshold_failures=threshold_failures,
    )

    output_path = results_output_dir / "forest_plan_profile_eval_results.json"
    report_path = results_output_dir / "forest_plan_profile_eval_report.md"
    summary = {
        "schema_version": FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "results_dir": str(results_output_dir),
        "output_path": str(output_path),
        "report_path": str(report_path),
        "contract_id": manifest.get("contract_id"),
        "contract_version": manifest.get("version"),
        "readiness_path": str(readiness_path),
        "forest_plan_profiles_path": str(forest_plan_profiles_path),
        "expected_active_source_set_ids": sorted(expected_active_source_set_ids),
        "active_source_set_ids": actual_active_source_set_ids,
        "passed": False,
        "required_profile_count": len(profile_specs),
        "readiness_profile_count": len(readiness_profile_ids),
        "configured_profile_count": len(configured_profile_ids),
        "covered_profile_count": readiness_state["status_counts"].get("covered", 0),
        "fixture_contract_defined_profile_count": readiness_state["status_counts"].get(
            "fixture_contract_defined",
            0,
        ),
        "not_started_profile_count": readiness_state["status_counts"].get("not_started", 0),
        "validated_not_started_profile_count": len(readiness_state["validated_not_started_ids"]),
        "validated_not_started_profile_ids": readiness_state["validated_not_started_ids"],
        "profile_kind_counts": readiness_state["profile_kind_counts"],
        "status_counts": readiness_state["status_counts"],
        "profile_failure_count": sum(1 for result in profile_results if not result["passed"]),
        "profiles_below_floor_ids": sorted(
            result["forest_unit_id"] for result in profile_results if not result["passed"]
        ),
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "contract_checks": contract_checks,
        "profiles": profile_results,
    }
    summary["contract_checks"].append(
        {
            "name": "output_schema_fields_present",
            "passed": not [
                field for field in output_expectations if field not in summary and field != "passed"
            ],
            "details": {
                "required_fields": output_expectations,
                "missing_fields": [
                    field
                    for field in output_expectations
                    if field not in summary and field != "passed"
                ],
            },
        }
    )
    summary["passed"] = (
        all(check["passed"] for check in summary["contract_checks"])
        and not threshold_failures
        and all(profile_result["passed"] for profile_result in profile_results)
    )

    _write_json(output_path, summary)
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    return ForestPlanProfileEvalResult(
        summary=summary,
        output_path=output_path,
        report_path=report_path,
    )


def _validate_manifest_contract(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[_ProfileContractSpec], list[str]]:
    contract_checks: list[dict[str, Any]] = [
        {
            "name": "manifest_schema_version",
            "passed": manifest.get("schema_version") == FOREST_PLAN_PROFILE_EVAL_SCHEMA_VERSION,
            "details": {
                "path": str(manifest_path),
                "expected": FOREST_PLAN_PROFILE_EVAL_SCHEMA_VERSION,
                "actual": manifest.get("schema_version"),
            },
        }
    ]
    contract_id = str(manifest.get("contract_id") or "").strip()
    contract_checks.append(
        {
            "name": "manifest_contract_id_present",
            "passed": bool(contract_id),
            "details": {"contract_id": manifest.get("contract_id")},
        }
    )

    output_expectations = [
        str(field)
        for field in _string_tuple(
            (manifest.get("output_schema") or {}).get("required_summary_fields")
        )
    ]
    contract_checks.append(
        {
            "name": "expected_active_source_set_ids_present",
            "passed": bool(_string_tuple(manifest.get("expected_active_source_set_ids"))),
            "details": {
                "expected_active_source_set_ids": sorted(
                    _string_tuple(manifest.get("expected_active_source_set_ids"))
                )
            },
        }
    )
    contract_checks.append(
        {
            "name": "coverage_thresholds_present",
            "passed": isinstance(manifest.get("coverage_thresholds"), dict),
            "details": {"coverage_thresholds": manifest.get("coverage_thresholds")},
        }
    )

    raw_profiles = manifest.get("profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        contract_checks.append(
            {
                "name": "manifest_profiles_present",
                "passed": False,
                "details": {"profiles": raw_profiles},
            }
        )
        return contract_checks, [], output_expectations

    invalid_profile_contracts: list[dict[str, Any]] = []
    profile_specs: list[_ProfileContractSpec] = []
    profile_ids: list[str] = []
    for index, raw_profile in enumerate(raw_profiles):
        context = f"profiles[{index}]"
        if not isinstance(raw_profile, dict):
            invalid_profile_contracts.append({"context": context, "reason": "not_an_object"})
            continue
        forest_unit_id = str(raw_profile.get("forest_unit_id") or "").strip()
        profile_kind = str(raw_profile.get("profile_kind") or "").strip()
        required_coverage_status = str(raw_profile.get("required_coverage_status") or "").strip()
        minimum_positive_case_count = _coerce_non_negative_int(
            raw_profile.get("minimum_positive_case_count")
        )
        minimum_hard_negative_case_count = _coerce_non_negative_int(
            raw_profile.get("minimum_hard_negative_case_count")
        )
        minimum_selected_profile_compliance_case_count = _coerce_non_negative_int(
            raw_profile.get("minimum_selected_profile_compliance_case_count")
        )
        required_fixture_family_ids = _string_tuple(
            raw_profile.get("required_fixture_family_ids")
        )

        if not forest_unit_id:
            invalid_profile_contracts.append({"context": context, "reason": "missing_forest_unit_id"})
            continue
        profile_ids.append(forest_unit_id)
        if (
            not profile_kind
            or required_coverage_status != "covered"
            or minimum_positive_case_count is None
            or minimum_hard_negative_case_count is None
            or minimum_selected_profile_compliance_case_count is None
            or not required_fixture_family_ids
        ):
            invalid_profile_contracts.append(
                {
                    "context": context,
                    "forest_unit_id": forest_unit_id,
                    "profile_kind": profile_kind,
                    "required_coverage_status": required_coverage_status,
                    "minimum_positive_case_count": raw_profile.get("minimum_positive_case_count"),
                    "minimum_hard_negative_case_count": raw_profile.get(
                        "minimum_hard_negative_case_count"
                    ),
                    "minimum_selected_profile_compliance_case_count": raw_profile.get(
                        "minimum_selected_profile_compliance_case_count"
                    ),
                    "required_fixture_family_ids": raw_profile.get("required_fixture_family_ids"),
                }
            )
            continue
        profile_specs.append(
            _ProfileContractSpec(
                forest_unit_id=forest_unit_id,
                profile_kind=profile_kind,
                required_coverage_status=required_coverage_status,
                minimum_positive_case_count=minimum_positive_case_count,
                minimum_hard_negative_case_count=minimum_hard_negative_case_count,
                minimum_selected_profile_compliance_case_count=(
                    minimum_selected_profile_compliance_case_count
                ),
                required_fixture_family_ids=required_fixture_family_ids,
            )
        )

    duplicate_profile_ids = sorted(
        profile_id for profile_id in set(profile_ids) if profile_ids.count(profile_id) > 1
    )
    contract_checks.extend(
        [
            {
                "name": "manifest_profile_contracts_well_formed",
                "passed": not invalid_profile_contracts,
                "details": {"invalid_profile_contracts": invalid_profile_contracts},
            },
            {
                "name": "manifest_profile_ids_are_unique",
                "passed": not duplicate_profile_ids,
                "details": {"duplicate_profile_ids": duplicate_profile_ids},
            },
        ]
    )
    return contract_checks, profile_specs, output_expectations


def _load_readiness_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "rows_by_forest_unit_id": {},
            "status_counts": {},
            "profile_kind_counts": {},
            "validated_not_started_ids": [],
            "active_source_set_ids": [],
            "contract_checks": [
                {
                    "name": "readiness_path_exists",
                    "passed": False,
                    "details": {"path": str(path)},
                }
            ],
        }
    payload = _read_json(path)
    raw_rows = payload.get("profile_rows")
    if not isinstance(raw_rows, list):
        return {
            "rows_by_forest_unit_id": {},
            "status_counts": {},
            "profile_kind_counts": {},
            "validated_not_started_ids": [],
            "active_source_set_ids": [],
            "contract_checks": [
                {
                    "name": "readiness_path_exists",
                    "passed": True,
                    "details": {"path": str(path)},
                },
                {
                    "name": "readiness_profile_rows_present",
                    "passed": False,
                    "details": {"profile_rows": raw_rows},
                },
            ],
        }

    rows_by_forest_unit_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    invalid_rows: list[str] = []
    status_counts: dict[str, int] = {}
    profile_kind_counts: dict[str, int] = {}
    validated_not_started_ids: list[str] = []
    active_source_set_ids: set[str] = set()

    for index, raw_row in enumerate(raw_rows):
        context = f"profile_rows[{index}]"
        if not isinstance(raw_row, dict):
            invalid_rows.append(context)
            continue
        forest_unit_id = str(raw_row.get("forest_unit_id") or "").strip()
        if not forest_unit_id:
            invalid_rows.append(context)
            continue
        if forest_unit_id in rows_by_forest_unit_id:
            duplicate_ids.append(forest_unit_id)
            continue
        rows_by_forest_unit_id[forest_unit_id] = raw_row

        coverage = raw_row.get("applicability_eval_coverage") or {}
        status = str(coverage.get("status") or "missing")
        status_counts[status] = status_counts.get(status, 0) + 1

        profile_kind = str(raw_row.get("profile_kind") or "missing")
        profile_kind_counts[profile_kind] = profile_kind_counts.get(profile_kind, 0) + 1

        if (
            status == "not_started"
            and (raw_row.get("component_inventory_validation") or {}).get("status") == "validated"
        ):
            validated_not_started_ids.append(forest_unit_id)

        artifact_path = str(
            (raw_row.get("component_inventory_validation") or {}).get("artifact_path") or ""
        )
        match = _SOURCE_SET_ID_PATTERN.search(artifact_path)
        if match:
            active_source_set_ids.add(match.group(1))

    return {
        "rows_by_forest_unit_id": rows_by_forest_unit_id,
        "status_counts": dict(sorted(status_counts.items())),
        "profile_kind_counts": dict(sorted(profile_kind_counts.items())),
        "validated_not_started_ids": sorted(validated_not_started_ids),
        "active_source_set_ids": sorted(active_source_set_ids),
        "contract_checks": [
            {
                "name": "readiness_path_exists",
                "passed": True,
                "details": {"path": str(path)},
            },
            {
                "name": "readiness_profile_rows_present",
                "passed": True,
                "details": {"profile_row_count": len(raw_rows)},
            },
            {
                "name": "readiness_rows_well_formed",
                "passed": not invalid_rows,
                "details": {"invalid_rows": invalid_rows},
            },
            {
                "name": "readiness_rows_unique_by_forest_unit_id",
                "passed": not duplicate_ids,
                "details": {"duplicate_profile_ids": sorted(duplicate_ids)},
            },
        ],
    }


def _load_profile_collection_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "profiles_by_forest_unit_id": {},
            "contract_checks": [
                {
                    "name": "forest_plan_profiles_path_exists",
                    "passed": False,
                    "details": {"path": str(path)},
                }
            ],
        }
    try:
        collection = load_forest_plan_profiles(path)
    except Exception as exc:  # noqa: BLE001
        return {
            "profiles_by_forest_unit_id": {},
            "contract_checks": [
                {
                    "name": "forest_plan_profiles_path_exists",
                    "passed": True,
                    "details": {"path": str(path)},
                },
                {
                    "name": "forest_plan_profiles_loadable",
                    "passed": False,
                    "details": {"path": str(path), "error": str(exc)},
                },
            ],
        }
    return {
        "profiles_by_forest_unit_id": {
            profile.forest_unit_id: profile for profile in collection.profiles
        },
        "contract_checks": [
            {
                "name": "forest_plan_profiles_path_exists",
                "passed": True,
                "details": {"path": str(path)},
            },
            {
                "name": "forest_plan_profiles_loadable",
                "passed": True,
                "details": {
                    "path": str(path),
                    "profile_count": len(collection.profiles),
                    "schema_version": collection.schema_version,
                },
            },
        ],
    }


def _profile_result(
    *,
    spec: _ProfileContractSpec,
    readiness_row: dict[str, Any] | None,
    profile_collection_state: dict[str, Any],
) -> dict[str, Any]:
    failure_reasons: list[str] = []
    actual_profile_kind = ""
    actual_status = "missing"
    positive_case_count = 0
    hard_negative_case_count = 0
    selected_profile_compliance_case_count = 0
    actual_fixture_family_ids: tuple[str, ...] = ()
    graph_promotion_status = None
    component_inventory_status = None

    if readiness_row is None:
        failure_reasons.append("missing_readiness_row")
    else:
        actual_profile_kind = str(readiness_row.get("profile_kind") or "")
        graph_promotion_status = readiness_row.get("graph_promotion_status")
        component_inventory_status = (
            readiness_row.get("component_inventory_validation") or {}
        ).get("status")
        coverage = readiness_row.get("applicability_eval_coverage") or {}
        actual_status = str(coverage.get("status") or "missing")
        positive_case_count = _coerce_non_negative_int(coverage.get("positive_case_count")) or 0
        hard_negative_case_count = (
            _coerce_non_negative_int(coverage.get("hard_negative_case_count")) or 0
        )
        selected_profile_compliance_case_count = (
            _coerce_non_negative_int(coverage.get("selected_profile_compliance_case_count")) or 0
        )
        actual_fixture_family_ids = _string_tuple(coverage.get("fixture_family_ids"))

        if actual_profile_kind != spec.profile_kind:
            failure_reasons.append("profile_kind_mismatch")
        if actual_status != spec.required_coverage_status:
            failure_reasons.append("coverage_status_below_required_floor")
        if positive_case_count < spec.minimum_positive_case_count:
            failure_reasons.append("positive_case_floor_not_met")
        if hard_negative_case_count < spec.minimum_hard_negative_case_count:
            failure_reasons.append("hard_negative_case_floor_not_met")
        if (
            selected_profile_compliance_case_count
            < spec.minimum_selected_profile_compliance_case_count
        ):
            failure_reasons.append("selected_profile_compliance_floor_not_met")
        if set(spec.required_fixture_family_ids) - set(actual_fixture_family_ids):
            failure_reasons.append("required_fixture_families_missing")

    if spec.forest_unit_id not in profile_collection_state["profiles_by_forest_unit_id"]:
        failure_reasons.append("missing_profile_config")

    missing_fixture_family_ids = sorted(
        set(spec.required_fixture_family_ids) - set(actual_fixture_family_ids)
    )
    return {
        "forest_unit_id": spec.forest_unit_id,
        "expected_profile_kind": spec.profile_kind,
        "actual_profile_kind": actual_profile_kind,
        "expected_coverage_status": spec.required_coverage_status,
        "actual_coverage_status": actual_status,
        "minimum_positive_case_count": spec.minimum_positive_case_count,
        "positive_case_count": positive_case_count,
        "minimum_hard_negative_case_count": spec.minimum_hard_negative_case_count,
        "hard_negative_case_count": hard_negative_case_count,
        "minimum_selected_profile_compliance_case_count": (
            spec.minimum_selected_profile_compliance_case_count
        ),
        "selected_profile_compliance_case_count": selected_profile_compliance_case_count,
        "required_fixture_family_ids": list(spec.required_fixture_family_ids),
        "actual_fixture_family_ids": list(actual_fixture_family_ids),
        "missing_fixture_family_ids": missing_fixture_family_ids,
        "graph_promotion_status": graph_promotion_status,
        "component_inventory_status": component_inventory_status,
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
    }


def _threshold_failures(
    *,
    thresholds: Any,
    status_counts: dict[str, int],
) -> list[dict[str, Any]]:
    if not isinstance(thresholds, dict):
        return [{"name": "coverage_thresholds_missing", "details": {"coverage_thresholds": thresholds}}]
    failures: list[dict[str, Any]] = []
    covered_min = _coerce_non_negative_int(thresholds.get("covered_profile_count_min"))
    fixture_defined_max = _coerce_non_negative_int(
        thresholds.get("fixture_contract_defined_profile_count_max")
    )
    not_started_max = _coerce_non_negative_int(thresholds.get("not_started_profile_count_max"))

    if covered_min is None:
        failures.append(
            {
                "name": "covered_profile_count_min_missing",
                "details": {"coverage_thresholds": thresholds},
            }
        )
    elif status_counts.get("covered", 0) < covered_min:
        failures.append(
            {
                "name": "covered_profile_count_below_minimum",
                "actual": status_counts.get("covered", 0),
                "expected_minimum": covered_min,
            }
        )

    if fixture_defined_max is None:
        failures.append(
            {
                "name": "fixture_contract_defined_profile_count_max_missing",
                "details": {"coverage_thresholds": thresholds},
            }
        )
    elif status_counts.get("fixture_contract_defined", 0) > fixture_defined_max:
        failures.append(
            {
                "name": "fixture_contract_defined_profile_count_above_maximum",
                "actual": status_counts.get("fixture_contract_defined", 0),
                "expected_maximum": fixture_defined_max,
            }
        )

    if not_started_max is None:
        failures.append(
            {
                "name": "not_started_profile_count_max_missing",
                "details": {"coverage_thresholds": thresholds},
            }
        )
    elif status_counts.get("not_started", 0) > not_started_max:
        failures.append(
            {
                "name": "not_started_profile_count_above_maximum",
                "actual": status_counts.get("not_started", 0),
                "expected_maximum": not_started_max,
            }
        )

    return failures


def _failure_category_counts(
    *,
    profile_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for profile_result in profile_results:
        for reason in profile_result["failure_reasons"]:
            counts[reason] = counts.get(reason, 0) + 1
    for threshold_failure in threshold_failures:
        name = str(threshold_failure.get("name") or "threshold_failure")
        counts[name] = counts.get(name, 0) + 1
    return counts


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Cross-Forest Profile Eval Coverage",
        "",
        f"- passed: `{summary['passed']}`",
        f"- active source sets: `{', '.join(summary['active_source_set_ids']) or 'none'}`",
        f"- covered / fixture_contract_defined / not_started: "
        f"`{summary['covered_profile_count']}` / "
        f"`{summary['fixture_contract_defined_profile_count']}` / "
        f"`{summary['not_started_profile_count']}`",
        f"- validated not started: `{summary['validated_not_started_profile_count']}`",
        "",
        "## Threshold Failures",
        "",
    ]
    if summary["threshold_failures"]:
        for failure in summary["threshold_failures"]:
            actual = failure.get("actual")
            expected_minimum = failure.get("expected_minimum")
            expected_maximum = failure.get("expected_maximum")
            if expected_minimum is not None:
                detail = f"`{actual}` actual, minimum `{expected_minimum}`"
            elif expected_maximum is not None:
                detail = f"`{actual}` actual, maximum `{expected_maximum}`"
            else:
                detail = json.dumps(failure.get("details", {}), sort_keys=True)
            lines.append(f"- `{failure['name']}`: {detail}")
    else:
        lines.append("- none")

    lines.extend(["", "## Profile Results", ""])
    for profile_result in summary["profiles"]:
        lines.append(
            f"- `{profile_result['forest_unit_id']}`: "
            f"status `{profile_result['actual_coverage_status']}`, "
            f"positive `{profile_result['positive_case_count']}` / "
            f"`{profile_result['minimum_positive_case_count']}`, "
            f"hard negative `{profile_result['hard_negative_case_count']}` / "
            f"`{profile_result['minimum_hard_negative_case_count']}`, "
            f"selected compliance `{profile_result['selected_profile_compliance_case_count']}` / "
            f"`{profile_result['minimum_selected_profile_compliance_case_count']}`, "
            f"passed `{profile_result['passed']}`"
        )
        if profile_result["failure_reasons"]:
            lines.append(
                f"  failure reasons: `{', '.join(profile_result['failure_reasons'])}`"
            )
        if profile_result["missing_fixture_family_ids"]:
            lines.append(
                "  missing fixture families: "
                f"`{', '.join(profile_result['missing_fixture_family_ids'])}`"
            )

    return "\n".join(lines) + "\n"


def _manifest_repo_path(manifest_path: Path, raw_path: Any) -> Path:
    if isinstance(raw_path, Path):
        path = raw_path
    elif isinstance(raw_path, str) and raw_path.strip():
        path = Path(raw_path)
    else:
        return REPO_ROOT / "__missing_manifest_path__"
    return path if path.is_absolute() else (manifest_path.parent / path).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return tuple(sorted(set(items)))


def _coerce_non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    return None
