from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re


PROMOTION_SUITE_SCHEMA_VERSION = "promotion-suite-v1"
PROMOTION_SUITE_RESULTS_SCHEMA_VERSION = "promotion-suite-results-v0"
DEFAULT_PROMOTION_SUITE_PATH = Path("config/promotion_suite_v1.json")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
MISSING = object()
FOREST_PLAN_PROFILE_GATE_RESULT_IDS = {
    "compliance_review",
    "forest_plan_context_summary",
    "phase_eval",
}


def _manifest_context(manifest: dict[str, Any], output_dir: Path) -> dict[str, str]:
    return {
        "output_dir": str(output_dir),
        "source_set_id": str(manifest.get("source_set_id") or ""),
        "full_canonical_source_set_id": str(
            manifest.get("full_canonical_source_set_id") or ""
        ),
        "rule_pack_id": str(manifest.get("rule_pack_id") or ""),
        "rule_pack_version": str(manifest.get("rule_pack_version") or ""),
    }


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
    if path.parts and path.parts[0] == output_dir.name:
        return output_dir.joinpath(*path.parts[1:])
    return output_dir / path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
