from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import re


PROMOTION_SUITE_SCHEMA_VERSION = "promotion-suite-v0"
PROMOTION_SUITE_RESULTS_SCHEMA_VERSION = "promotion-suite-results-v0"
DEFAULT_PROMOTION_SUITE_PATH = Path("config/promotion_suite_v1.json")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
MISSING = object()


@dataclass(frozen=True)
class PromotionSuiteResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    markdown_path: Path
    summary: dict[str, Any]


def run_promotion_suite(
    *,
    output_dir: Path = Path("source_library"),
    manifest_path: Path = DEFAULT_PROMOTION_SUITE_PATH,
    results_dir: Path | None = None,
    strict_expansion: bool = False,
) -> PromotionSuiteResult:
    """Check manifest-declared promotion evidence and write an aggregate readiness report."""

    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    suite_id = str(manifest["id"])
    suite_output_dir = (
        Path(results_dir)
        if results_dir is not None
        else output_dir / "reviews" / "promotion_suite" / suite_id
    )
    output_path = suite_output_dir / "promotion_suite_results.json"
    markdown_path = suite_output_dir / "promotion_suite_report.md"

    context = _manifest_context(manifest, output_dir)
    rule_pack_result = _rule_pack_result(manifest, manifest_path)
    review_results = [
        _review_case_result(case, context=context, output_dir=output_dir)
        for case in manifest.get("review_cases", [])
    ]
    suite_results = [
        _artifact_result(spec, context=context, output_dir=output_dir)
        for spec in manifest.get("suite_results", [])
    ]
    expansion_slots = [
        _expansion_slot_result(slot) for slot in manifest.get("expansion_slots", [])
    ]

    required_review_results = [
        result
        for case in review_results
        for result in case["results"]
        if result["required_for_current_promotion"]
    ]
    required_suite_results = [
        result for result in suite_results if result["required_for_current_promotion"]
    ]
    current_promotion_ready = (
        rule_pack_result["passed"]
        and all(result["passed"] for result in required_review_results)
        and all(result["passed"] for result in required_suite_results)
    )
    expansion_ready = all(slot["ready"] for slot in expansion_slots)
    promotion_ready = current_promotion_ready and (expansion_ready if strict_expansion else True)
    failure_category_counts = _failure_category_counts(
        rule_pack_result=rule_pack_result,
        review_results=review_results,
        suite_results=suite_results,
        expansion_slots=expansion_slots,
        strict_expansion=strict_expansion,
    )
    expansion_failure_category_counts = _expansion_failure_category_counts(
        review_results=review_results,
        suite_results=suite_results,
        expansion_slots=expansion_slots,
    )
    summary = {
        "schema_version": PROMOTION_SUITE_RESULTS_SCHEMA_VERSION,
        "suite_schema_version": manifest.get("schema_version"),
        "suite_id": suite_id,
        "suite_label": manifest.get("label"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(suite_output_dir),
        "output_path": str(output_path),
        "markdown_path": str(markdown_path),
        "source_set_id": context["source_set_id"],
        "rule_pack_path": manifest.get("rule_pack_path"),
        "rule_pack_id": manifest.get("rule_pack_id"),
        "rule_pack_version": manifest.get("rule_pack_version"),
        "strict_expansion": strict_expansion,
        "current_promotion_ready": current_promotion_ready,
        "expansion_ready": expansion_ready,
        "promotion_ready": promotion_ready,
        "review_case_count": len(review_results),
        "suite_result_count": len(suite_results),
        "expansion_slot_count": len(expansion_slots),
        "required_current_result_count": len(required_review_results)
        + len(required_suite_results)
        + 1,
        "passed_required_current_result_count": sum(
            1 for result in required_review_results + required_suite_results if result["passed"]
        )
        + int(rule_pack_result["passed"]),
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "expansion_failure_category_counts": dict(
            sorted(expansion_failure_category_counts.items())
        ),
        "open_expansion_slot_count": sum(1 for slot in expansion_slots if not slot["ready"]),
        "rule_pack_result": rule_pack_result,
        "review_cases": review_results,
        "suite_results": suite_results,
        "expansion_slots": expansion_slots,
    }
    suite_output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, summary)
    markdown_path.write_text(_markdown_report(summary), encoding="utf-8")
    return PromotionSuiteResult(
        manifest_path=manifest_path,
        output_dir=suite_output_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        summary=summary,
    )


def _manifest_context(manifest: dict[str, Any], output_dir: Path) -> dict[str, str]:
    return {
        "output_dir": str(output_dir),
        "source_set_id": str(manifest.get("source_set_id") or ""),
        "rule_pack_id": str(manifest.get("rule_pack_id") or ""),
        "rule_pack_version": str(manifest.get("rule_pack_version") or ""),
    }


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


def _equals_check(
    name: str,
    *,
    actual: Any,
    expected: Any,
    failure_category: str,
) -> dict[str, Any]:
    return _check_result(
        name=name,
        passed=actual == expected,
        expected=expected,
        actual=actual,
        failure_category=failure_category,
    )


def _min_check(
    name: str,
    *,
    actual: Any,
    expected_min: int | float,
    failure_category: str,
) -> dict[str, Any]:
    try:
        numeric_actual = float(actual)
    except (TypeError, ValueError):
        numeric_actual = None
    return _check_result(
        name=name,
        passed=numeric_actual is not None and numeric_actual >= float(expected_min),
        expected={">=": expected_min},
        actual=actual,
        failure_category=failure_category,
    )


def _check_result(
    *,
    name: str,
    passed: bool,
    expected: Any,
    actual: Any,
    failure_category: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "failure_category": failure_category,
    }
    if details:
        result["details"] = details
    return result


def _expansion_slot_result(slot: dict[str, Any]) -> dict[str, Any]:
    ready = bool(slot.get("ready", False))
    category = str(slot.get("failure_category") or "package_fixture_missing")
    return {
        "id": slot["id"],
        "label": slot.get("label"),
        "status": slot.get("status", "open"),
        "ready": ready,
        "required_for_current_promotion": bool(
            slot.get("required_for_current_promotion", False)
        ),
        "failure_categories": [] if ready else [category],
        "next_action": slot.get("next_action"),
        "acceptance_signal": slot.get("acceptance_signal"),
    }


def _failure_category_counts(
    *,
    rule_pack_result: dict[str, Any],
    review_results: list[dict[str, Any]],
    suite_results: list[dict[str, Any]],
    expansion_slots: list[dict[str, Any]],
    strict_expansion: bool,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    counts.update(rule_pack_result.get("failure_categories", []))
    for case in review_results:
        for result in case["results"]:
            if not result["passed"] and (
                result["required_for_current_promotion"]
                or (strict_expansion and result["required_for_expansion"])
            ):
                counts.update(result.get("failure_categories", []))
    for result in suite_results:
        if not result["passed"] and (
            result["required_for_current_promotion"]
            or (strict_expansion and result["required_for_expansion"])
        ):
            counts.update(result.get("failure_categories", []))
    for slot in expansion_slots:
        if strict_expansion or slot.get("required_for_current_promotion"):
            counts.update(slot.get("failure_categories", []))
    return counts


def _expansion_failure_category_counts(
    *,
    review_results: list[dict[str, Any]],
    suite_results: list[dict[str, Any]],
    expansion_slots: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for case in review_results:
        for result in case["results"]:
            if not result["passed"] and result["required_for_expansion"]:
                counts.update(result.get("failure_categories", []))
    for result in suite_results:
        if not result["passed"] and result["required_for_expansion"]:
            counts.update(result.get("failure_categories", []))
    for slot in expansion_slots:
        if not slot.get("ready"):
            counts.update(slot.get("failure_categories", []))
    return counts


def _failure_category(spec: dict[str, Any], *, missing: bool) -> str:
    if missing and spec.get("missing_failure_category"):
        return str(spec["missing_failure_category"])
    if spec.get("failure_category"):
        return str(spec["failure_category"])
    identifier = f"{spec.get('id', '')} {spec.get('path', '')}".lower()
    if "extraction" in identifier:
        return "extraction_miss"
    if "retrieval" in identifier:
        return "retrieval_miss"
    if "applicability" in identifier or "authority_universe" in identifier:
        return "applicability_miss"
    if "source" in identifier or "catalog" in identifier:
        return "missing_source"
    if "adjudication" in identifier:
        return "adjudication_needed"
    if "package" in identifier and missing:
        return "package_fixture_missing"
    if "evidence" in identifier:
        return "unsupported_package_evidence"
    return "stale_artifact"


def _json_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return MISSING
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return MISSING
            current = current[index]
        else:
            return MISSING
    return current


def _resolve_output_path(value: str, output_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return output_dir / path


def _resolve_repo_path(value: str, manifest_path: Path) -> Path:
    if not value:
        return Path("")
    path = Path(value)
    if path.is_absolute():
        return path
    for candidate in (
        path,
        manifest_path.parent / path,
        manifest_path.parent.parent / path,
    ):
        if candidate.exists():
            return candidate
    return path


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != PROMOTION_SUITE_SCHEMA_VERSION:
        raise ValueError(
            "Promotion suite manifest must use schema_version "
            f"{PROMOTION_SUITE_SCHEMA_VERSION!r}."
        )
    for key in ("id", "source_set_id", "rule_pack_path", "rule_pack_id", "rule_pack_version"):
        if not str(manifest.get(key) or "").strip():
            raise ValueError(f"Promotion suite manifest is missing {key!r}.")
    _validate_safe_id(str(manifest["id"]), "suite id")
    for case in manifest.get("review_cases", []):
        _validate_safe_id(str(case.get("id") or ""), "review case id")
        _validate_safe_id(str(case.get("review_id") or ""), "review id")
        for result in case.get("results", []):
            _validate_result_spec(result)
    for result in manifest.get("suite_results", []):
        _validate_result_spec(result)
    for slot in manifest.get("expansion_slots", []):
        _validate_safe_id(str(slot.get("id") or ""), "expansion slot id")


def _validate_result_spec(spec: dict[str, Any]) -> None:
    _validate_safe_id(str(spec.get("id") or ""), "result id")
    if not str(spec.get("path") or "").strip():
        raise ValueError(f"Promotion suite result {spec.get('id')!r} is missing path.")
    for check in spec.get("checks", []):
        _validate_safe_id(str(check.get("name") or ""), "check name")
        if "starts_with" in check:
            continue
        if not str(check.get("json_path") or "").strip():
            raise ValueError(
                f"Promotion suite check {check.get('name')!r} is missing json_path."
            )
        supported = {"equals", "min", "contains_all", "non_empty", "starts_with"}
        if not supported.intersection(check):
            raise ValueError(
                f"Promotion suite check {check.get('name')!r} must define one of "
                f"{sorted(supported)}."
            )


def _validate_safe_id(value: str, label: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only letters, numbers, dot, underscore, or hyphen.")


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Promotion Suite Report",
        "",
        f"- Suite: `{summary['suite_id']}`",
        f"- Source set: `{summary['source_set_id']}`",
        f"- Rule pack: `{summary['rule_pack_id']}` `{summary['rule_pack_version']}`",
        f"- Current promotion ready: `{summary['current_promotion_ready']}`",
        f"- Expansion ready: `{summary['expansion_ready']}`",
        f"- Promotion ready: `{summary['promotion_ready']}`",
        f"- Strict expansion: `{summary['strict_expansion']}`",
        f"- Failure categories: `{summary['failure_category_counts']}`",
        f"- Expansion failure categories: `{summary['expansion_failure_category_counts']}`",
        f"- Open expansion slots: `{summary['open_expansion_slot_count']}`",
        "",
        "## Review Cases",
        "",
        "| Case | Review ID | Ready | Failed Categories |",
        "| --- | --- | --- | --- |",
    ]
    for case in summary["review_cases"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(case["id"]),
                    _md_cell(case["review_id"]),
                    _md_cell(case["promotion_ready"]),
                    _md_cell(", ".join(case["failure_categories"]) or "None"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Suite Results",
            "",
            "| Result | Passed | Required | Failed Categories |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in summary["suite_results"]:
        lines.append(_result_markdown_row(result))
    lines.extend(
        [
            "",
            "## Expansion Slots",
            "",
            "| Slot | Status | Ready | Next Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for slot in summary["expansion_slots"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(slot["id"]),
                    _md_cell(slot.get("status")),
                    _md_cell(slot["ready"]),
                    _md_cell(slot.get("next_action") or ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _result_markdown_row(result: dict[str, Any]) -> str:
    return (
        "| "
        + " | ".join(
            [
                _md_cell(result["id"]),
                _md_cell(result["passed"]),
                _md_cell(result["required_for_current_promotion"]),
                _md_cell(", ".join(result["failure_categories"]) or "None"),
            ]
        )
        + " |"
    )


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
