from __future__ import annotations

from pathlib import Path
from typing import Any

from .promotion_suite_support import MISSING
from .promotion_suite_support import _check_result
from .promotion_suite_support import _equals_check
from .promotion_suite_support import _failure_category
from .promotion_suite_support import _json_path
from .promotion_suite_support import _min_check
from .promotion_suite_support import _read_json
from .promotion_suite_support import _resolve_output_path
from .promotion_suite_support import _resolve_repo_path
from .promotion_suite_support import _sha256_file


def _rule_pack_result(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    path = _resolve_repo_path(str(manifest.get("rule_pack_path") or ""), manifest_path)
    checks = []
    failure_categories: list[str] = []
    payload: dict[str, Any] | None = None
    if not path.exists():
        checks.append(
            _check_result(
                name="rule_pack_exists",
                passed=False,
                expected=True,
                actual=False,
                failure_category="missing_source",
            )
        )
        failure_categories.append("missing_source")
    else:
        payload = _read_json(path)
        for key, label in (
            ("rule_pack_id", "rule_pack_id_matches_manifest"),
            ("rule_pack_version", "rule_pack_version_matches_manifest"),
        ):
            expected = manifest.get(key)
            if expected is None:
                continue
            actual_key = "version" if key == "rule_pack_version" else key
            checks.append(
                _equals_check(
                    label,
                    actual=payload.get(actual_key),
                    expected=expected,
                    failure_category="stale_artifact",
                )
            )
        if manifest.get("expected_rule_count") is not None:
            checks.append(
                _min_check(
                    "rule_count_matches_manifest",
                    actual=len(payload.get("rules", [])),
                    expected_min=int(manifest["expected_rule_count"]),
                    failure_category="missing_source",
                )
            )
        if manifest.get("expected_baseline_source_record_count") is not None:
            baseline_ids = payload.get("baseline_source_record_ids", [])
            checks.append(
                _min_check(
                    "baseline_source_record_count_matches_manifest",
                    actual=len(baseline_ids),
                    expected_min=int(manifest["expected_baseline_source_record_count"]),
                    failure_category="missing_source",
                )
            )
    for check in checks:
        if not check["passed"]:
            failure_categories.append(check["failure_category"])
    return {
        "id": "rule_pack",
        "label": "Rule pack contract",
        "path": str(path),
        "exists": path.exists(),
        "passed": bool(checks) and all(check["passed"] for check in checks),
        "checks": checks,
        "failure_categories": sorted(set(failure_categories)),
        "rule_count": len((payload or {}).get("rules", [])),
        "baseline_source_record_count": len(
            (payload or {}).get("baseline_source_record_ids", [])
        ),
    }


def _review_case_result(
    case: dict[str, Any],
    *,
    context: dict[str, str],
    output_dir: Path,
) -> dict[str, Any]:
    case_context = dict(context)
    case_context["review_id"] = str(case["review_id"])
    results = [
        _artifact_result(spec, context=case_context, output_dir=output_dir)
        for spec in case.get("results", [])
    ]
    required_results = [
        result for result in results if result["required_for_current_promotion"]
    ]
    return {
        "id": case["id"],
        "label": case.get("label"),
        "review_id": case["review_id"],
        "package_label": case.get("package_label"),
        "required_for_current_promotion": bool(
            case.get("required_for_current_promotion", True)
        ),
        "promotion_ready": all(result["passed"] for result in required_results),
        "results": results,
        "failure_categories": sorted(
            {
                category
                for result in results
                for category in result.get("failure_categories", [])
            }
        ),
    }


def _artifact_result(
    spec: dict[str, Any],
    *,
    context: dict[str, str],
    output_dir: Path,
) -> dict[str, Any]:
    path = _resolve_output_path(str(spec["path"]).format(**context), output_dir)
    artifact_format = str(spec.get("format") or "json")
    payload = _read_json(path) if path.exists() and artifact_format == "json" else {}
    checks = []
    failure_categories: list[str] = []
    if not path.exists():
        category = _failure_category(spec, missing=True)
        checks.append(
            _check_result(
                name="artifact_exists",
                passed=False,
                expected=True,
                actual=False,
                failure_category=category,
            )
        )
        failure_categories.append(category)
    else:
        checks.append(
            _check_result(
                name="artifact_exists",
                passed=True,
                expected=True,
                actual=True,
                failure_category=_failure_category(spec, missing=False),
            )
        )
        for check_spec in spec.get("checks", []):
            check = _evaluate_artifact_check(
                path,
                payload or {},
                check_spec,
                artifact_format=artifact_format,
                default_failure_category=_failure_category(spec, missing=False),
                output_dir=output_dir,
            )
            checks.append(check)
            if not check["passed"]:
                failure_categories.append(check["failure_category"])
    return {
        "id": spec["id"],
        "label": spec.get("label"),
        "path": str(path),
        "exists": path.exists(),
        "required_for_current_promotion": bool(
            spec.get("required_for_current_promotion", True)
        ),
        "required_for_full_canonical_corpus": bool(
            spec.get("required_for_full_canonical_corpus", False)
        ),
        "required_for_expansion": bool(spec.get("required_for_expansion", False)),
        "passed": path.exists() and all(check["passed"] for check in checks),
        "checks": checks,
        "failure_categories": sorted(set(failure_categories)),
    }


def _evaluate_artifact_check(
    path: Path,
    payload: dict[str, Any],
    check_spec: dict[str, Any],
    *,
    artifact_format: str,
    default_failure_category: str,
    output_dir: Path,
) -> dict[str, Any]:
    name = str(check_spec["name"])
    failure_category = str(
        check_spec.get("failure_category") or default_failure_category
    )
    if "starts_with" in check_spec:
        expected_prefix = str(check_spec["starts_with"])
        if artifact_format == "binary":
            actual_prefix = path.read_bytes()[: len(expected_prefix)].decode(
                "latin-1",
                errors="replace",
            )
        else:
            actual_prefix = path.read_text(encoding="utf-8", errors="replace")[
                : len(expected_prefix)
            ]
        return _check_result(
            name=name,
            passed=actual_prefix == expected_prefix,
            expected=expected_prefix,
            actual=actual_prefix,
            failure_category=failure_category,
        )
    if "file_sha256_matches" in check_spec:
        hash_spec = check_spec["file_sha256_matches"]
        if not isinstance(hash_spec, dict):
            raise ValueError(f"Unsupported promotion-suite check: {check_spec}")
        path_value = _json_path(payload, str(hash_spec.get("path_json_path") or ""))
        expected_sha = _json_path(payload, str(hash_spec.get("sha256_json_path") or ""))
        if path_value is MISSING or expected_sha is MISSING:
            return _check_result(
                name=name,
                passed=False,
                expected="declared output path and sha256",
                actual=None,
                failure_category=failure_category,
            )
        target_path = _resolve_output_path(str(path_value), output_dir)
        if not target_path.exists():
            return _check_result(
                name=name,
                passed=False,
                expected=str(expected_sha),
                actual="missing",
                failure_category=failure_category,
                details={"path": str(target_path)},
            )
        actual_sha = _sha256_file(target_path)
        return _check_result(
            name=name,
            passed=actual_sha == expected_sha,
            expected=str(expected_sha),
            actual=actual_sha,
            failure_category=failure_category,
            details={"path": str(target_path)},
        )

    actual = _json_path(payload, str(check_spec["json_path"]))
    if actual is MISSING:
        return _check_result(
            name=name,
            passed=False,
            expected=check_spec.get("equals")
            if "equals" in check_spec
            else check_spec.get("min"),
            actual=None,
            failure_category=failure_category,
        )
    if "equals" in check_spec:
        return _equals_check(
            name,
            actual=actual,
            expected=check_spec["equals"],
            failure_category=failure_category,
        )
    if "min" in check_spec:
        return _min_check(
            name,
            actual=actual,
            expected_min=check_spec["min"],
            failure_category=failure_category,
        )
    if "contains_all" in check_spec:
        expected = [str(value) for value in check_spec["contains_all"]]
        actual_values = [str(value) for value in (actual or [])]
        missing_values = sorted(set(expected) - set(actual_values))
        return _check_result(
            name=name,
            passed=not missing_values,
            expected=expected,
            actual=actual_values,
            failure_category=failure_category,
            details={"missing_values": missing_values},
        )
    if check_spec.get("non_empty"):
        return _check_result(
            name=name,
            passed=bool(actual),
            expected="non_empty",
            actual=actual,
            failure_category=failure_category,
        )
    raise ValueError(f"Unsupported promotion-suite check: {check_spec}")
