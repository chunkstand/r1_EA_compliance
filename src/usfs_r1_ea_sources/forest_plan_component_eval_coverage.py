from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json


FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION = "forest-plan-component-eval-coverage-v1"
FOREST_PLAN_COMPONENT_EVAL_CONTRACT_SCHEMA_VERSION = "forest-plan-component-eval-v0"
FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION = "forest-plan-component-eval-results-v0"
DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH = Path(
    "config/forest_plan_component_eval_coverage_v1.json"
)


@dataclass(frozen=True)
class ForestPlanComponentEvalCoverageResult:
    manifest_path: Path
    output_dir: Path
    summary: dict[str, Any]


def resolve_forest_plan_component_eval_file(
    *,
    review_id: str,
    manifest_path: Path = DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
) -> Path:
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    slot = _slot_by_review_id(manifest, review_id)
    return _resolve_repo_path(str(slot["eval_file"]), manifest_path)


def evaluate_forest_plan_component_eval_coverage(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
) -> ForestPlanComponentEvalCoverageResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)

    slot_results = [
        _slot_result(
            slot=slot,
            output_dir=output_dir,
            manifest_path=manifest_path,
        )
        for slot in manifest.get("slots", [])
    ]
    required_slots = [slot for slot in slot_results if slot["required"]]
    covered_slots = [slot for slot in required_slots if slot["passed"]]
    distinct_forest_ids = sorted(
        {
            str(slot.get("forest_unit_id") or "")
            for slot in required_slots
            if str(slot.get("forest_unit_id") or "").strip()
        }
    )
    missing_contract_count = sum(1 for slot in required_slots if slot["missing_contract"])
    missing_result_count = sum(1 for slot in required_slots if slot["missing_result"])
    stale_identity_count = sum(1 for slot in required_slots if slot["stale_identity"])
    unresolved_review_count = sum(1 for slot in required_slots if slot["unresolved_review"])
    threshold_failures = _threshold_failures(
        thresholds=_int_dict(manifest.get("coverage_thresholds")),
        required_review_count=len(required_slots),
        distinct_forest_count=len(distinct_forest_ids),
        missing_contract_count=missing_contract_count,
        missing_result_count=missing_result_count,
        stale_identity_count=stale_identity_count,
        unresolved_review_count=unresolved_review_count,
    )
    failure_category_counts = _failure_category_counts(
        slot_results=required_slots,
        threshold_failures=threshold_failures,
    )
    summary = {
        "schema_version": FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "coverage_id": manifest.get("id"),
        "coverage_version": manifest.get("version"),
        "passed": all(slot["passed"] for slot in required_slots) and not threshold_failures,
        "required_review_ids": _string_list(manifest.get("required_review_ids")),
        "required_review_count": len(required_slots),
        "covered_review_count": len(covered_slots),
        "covered_review_ids": sorted(slot["review_id"] for slot in covered_slots),
        "distinct_forest_count": len(distinct_forest_ids),
        "distinct_forest_ids": distinct_forest_ids,
        "missing_contract_count": missing_contract_count,
        "missing_result_count": missing_result_count,
        "stale_identity_count": stale_identity_count,
        "unresolved_review_count": unresolved_review_count,
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "slots": slot_results,
    }
    return ForestPlanComponentEvalCoverageResult(
        manifest_path=manifest_path,
        output_dir=output_dir,
        summary=summary,
    )


def _slot_result(
    *,
    slot: dict[str, Any],
    output_dir: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    review_id = str(slot["review_id"]).strip()
    eval_file = _resolve_repo_path(str(slot["eval_file"]), manifest_path)
    results_path = (
        _resolve_repo_path(str(slot["results_path"]), manifest_path)
        if slot.get("results_path")
        else output_dir / "reviews" / review_id / "forest_plan_component_eval_results.json"
    )

    contract_exists = eval_file.exists()
    result_exists = results_path.exists()
    contract = _read_json(eval_file) if contract_exists else {}
    result = _read_json(results_path) if result_exists else {}

    failure_reasons: list[str] = []
    expected_source_set_id = str(slot.get("expected_source_set_id") or "").strip()
    contract_review_id = str(contract.get("review_id") or "").strip()
    contract_source_set_id = str(contract.get("source_set_id") or "").strip()
    contract_schema_version = str(contract.get("schema_version") or "").strip()
    contract_valid = (
        contract_exists
        and contract_schema_version == FOREST_PLAN_COMPONENT_EVAL_CONTRACT_SCHEMA_VERSION
    )
    if not contract_exists:
        failure_reasons.append("missing_contract")
    elif not contract_valid:
        failure_reasons.append("contract_schema_mismatch")
    if contract_valid and contract_review_id != review_id:
        failure_reasons.append("contract_review_id_mismatch")
    if contract_valid and expected_source_set_id and contract_source_set_id != expected_source_set_id:
        failure_reasons.append("contract_source_set_id_mismatch")

    result_summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    result_review_id = str(result.get("review_id") or result_summary.get("review_id") or "").strip()
    result_source_set_id = str(
        result.get("source_set_id") or result_summary.get("source_set_id") or ""
    ).strip()
    result_eval_file = str(
        result.get("eval_file") or result_summary.get("eval_file") or ""
    ).strip()
    result_schema_version = str(result.get("schema_version") or "").strip()
    result_passed = bool(result.get("passed", result_summary.get("passed")))
    result_valid = (
        result_exists
        and result_schema_version == FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION
    )
    if not result_exists:
        failure_reasons.append("missing_result")
    elif not result_valid:
        failure_reasons.append("result_schema_mismatch")
    if result_valid and result_review_id != review_id:
        failure_reasons.append("result_review_id_mismatch")
    if result_valid and expected_source_set_id and result_source_set_id != expected_source_set_id:
        failure_reasons.append("result_source_set_id_mismatch")
    if (
        result_valid
        and contract_valid
        and Path(result_eval_file or ".").resolve() != eval_file.resolve()
    ):
        failure_reasons.append("result_eval_file_mismatch")
    if result_valid and not result_passed:
        failure_reasons.append("result_not_passed")

    return {
        "slot_id": str(slot["slot_id"]),
        "label": str(slot["label"]),
        "review_id": review_id,
        "forest_unit_id": str(slot["forest_unit_id"]),
        "expected_source_set_id": expected_source_set_id,
        "required": bool(slot["required"]),
        "eval_file": str(eval_file),
        "results_path": str(results_path),
        "contract_exists": contract_exists,
        "contract_review_id": contract_review_id,
        "contract_source_set_id": contract_source_set_id,
        "result_exists": result_exists,
        "result_review_id": result_review_id,
        "result_source_set_id": result_source_set_id,
        "result_eval_file": result_eval_file,
        "result_passed": result_passed,
        "missing_contract": "missing_contract" in failure_reasons,
        "missing_result": "missing_result" in failure_reasons,
        "stale_identity": any(reason.endswith("_mismatch") for reason in failure_reasons),
        "unresolved_review": (
            "missing_result" in failure_reasons
            or "result_schema_mismatch" in failure_reasons
            or "result_not_passed" in failure_reasons
        ),
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _threshold_failures(
    *,
    thresholds: dict[str, int],
    required_review_count: int,
    distinct_forest_count: int,
    missing_contract_count: int,
    missing_result_count: int,
    stale_identity_count: int,
    unresolved_review_count: int,
) -> list[dict[str, Any]]:
    failures = []
    for metric, actual in (
        ("required_review_count", required_review_count),
        ("distinct_forest_count_min", distinct_forest_count),
        ("missing_contract_count_max", missing_contract_count),
        ("missing_result_count_max", missing_result_count),
        ("stale_identity_count_max", stale_identity_count),
        ("unresolved_review_count_max", unresolved_review_count),
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
    return failures


def _failure_category_counts(
    *,
    slot_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    def bump(category: str) -> None:
        counts[category] = counts.get(category, 0) + 1

    for slot in slot_results:
        for reason in slot["failure_reasons"]:
            if reason == "missing_contract":
                bump("missing_required_review_contract")
            elif reason == "missing_result":
                bump("missing_required_review_result")
            elif reason in {
                "contract_review_id_mismatch",
                "contract_source_set_id_mismatch",
                "result_review_id_mismatch",
                "result_source_set_id_mismatch",
                "result_eval_file_mismatch",
            }:
                bump("stale_review_identity")
            elif reason == "result_not_passed":
                bump("unresolved_review_eval")
            elif reason == "contract_schema_mismatch":
                bump("invalid_review_contract")
            elif reason == "result_schema_mismatch":
                bump("invalid_review_result")
    for failure in threshold_failures:
        metric = str(failure.get("metric") or "")
        if metric == "required_review_count":
            bump("missing_required_review_slot")
        elif metric == "distinct_forest_count_min":
            bump("insufficient_forest_diversity")
        elif metric == "missing_contract_count_max":
            bump("missing_required_review_contract")
        elif metric == "missing_result_count_max":
            bump("missing_required_review_result")
        elif metric == "stale_identity_count_max":
            bump("stale_review_identity")
        elif metric == "unresolved_review_count_max":
            bump("unresolved_review_eval")
    return counts


def _slot_by_review_id(manifest: dict[str, Any], review_id: str) -> dict[str, Any]:
    for slot in manifest.get("slots", []):
        if str(slot.get("review_id") or "").strip() == review_id:
            return slot
    raise ValueError(
        "review_id is not tracked by the forest-plan component eval coverage manifest: "
        f"{review_id}"
    )


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("forest-plan component eval coverage manifest must be a JSON object")
    if manifest.get("schema_version") != FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION:
        raise ValueError(
            "forest-plan component eval coverage manifest must use "
            f"schema_version={FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION!r}"
        )
    if not str(manifest.get("id") or "").strip():
        raise ValueError("forest-plan component eval coverage manifest requires id")
    if not str(manifest.get("version") or "").strip():
        raise ValueError("forest-plan component eval coverage manifest requires version")

    required_review_ids = _string_list(manifest.get("required_review_ids"))
    if not required_review_ids:
        raise ValueError("forest-plan component eval coverage manifest requires required_review_ids")

    slots = manifest.get("slots")
    if not isinstance(slots, list) or not slots:
        raise ValueError("forest-plan component eval coverage manifest requires slots")

    slot_ids: set[str] = set()
    review_ids: set[str] = set()
    required_slot_review_ids: set[str] = set()
    required_slot_count = 0
    for slot in slots:
        if not isinstance(slot, dict):
            raise ValueError("forest-plan component eval coverage slots must be JSON objects")
        slot_id = str(slot.get("slot_id") or "").strip()
        review_id = str(slot.get("review_id") or "").strip()
        _validate_slot(slot)
        if slot_id in slot_ids:
            raise ValueError(f"duplicate forest-plan component eval coverage slot_id: {slot_id}")
        if review_id in review_ids:
            raise ValueError(f"duplicate forest-plan component eval coverage review_id: {review_id}")
        slot_ids.add(slot_id)
        review_ids.add(review_id)
        if bool(slot.get("required")):
            required_slot_count += 1
            required_slot_review_ids.add(review_id)

    if required_slot_review_ids != set(required_review_ids):
        raise ValueError(
            "required_review_ids must exactly match the required slot review_id set"
        )
    thresholds = _int_dict(manifest.get("coverage_thresholds"))
    required_threshold = thresholds.get("required_review_count")
    if required_threshold is not None and required_slot_count < required_threshold:
        raise ValueError(
            "forest-plan component eval coverage manifest does not meet required_review_count"
        )


def _validate_slot(slot: dict[str, Any]) -> None:
    for field in (
        "slot_id",
        "label",
        "review_id",
        "forest_unit_id",
        "expected_source_set_id",
        "eval_file",
    ):
        if not str(slot.get(field) or "").strip():
            raise ValueError(
                f"forest-plan component eval coverage slot requires non-empty {field}"
            )
    if "required" not in slot:
        raise ValueError("forest-plan component eval coverage slot requires required boolean")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}.")
    return value


def _resolve_repo_path(path_text: str, manifest_path: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (manifest_path.parent / path).resolve()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        try:
            result[str(key)] = int(item)
        except (TypeError, ValueError):
            continue
    return result


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
