from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any
import json


REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION = "real-package-review-coverage-v1"
REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION = "real-package-review-coverage-results-v1"
DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH = Path(
    "config/v1_real_package_review_coverage_v1.json"
)
EXPECTED_CONTRACT_STATUSES = {"reviewer_ready", "typed_blocked"}


@dataclass(frozen=True)
class RealPackageReviewCoverageEvalResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def resolve_real_package_review_eval_file(
    *,
    review_id: str,
    manifest_path: Path = DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
) -> Path:
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    slot = _slot_by_review_id(manifest, review_id)
    return _resolve_repo_path(str(slot["eval_file"]), manifest_path)


def run_real_package_review_coverage_eval(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> RealPackageReviewCoverageEvalResult:
    run_v1_ea_review_eval = import_module(
        "usfs_r1_ea_sources.v1_ea_eval"
    ).run_v1_ea_review_eval
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)
    results_output_dir = (
        Path(results_dir)
        if results_dir
        else output_dir / "reviews" / "real_package_review_coverage_eval"
    )
    output_path = results_output_dir / "real_package_review_coverage_eval_results.json"

    slot_results = [
        _slot_result(
            slot=slot,
            manifest_path=manifest_path,
            output_dir=output_dir,
            run_v1_ea_review_eval=run_v1_ea_review_eval,
        )
        for slot in manifest.get("slots", [])
    ]
    required_slots = [slot for slot in slot_results if slot["required"]]
    required_coverage_class_ids = _string_list(manifest.get("required_coverage_class_ids"))
    covered_slots = [slot for slot in required_slots if slot["passed"]]
    covered_review_ids = sorted(slot["review_id"] for slot in covered_slots)
    covered_coverage_class_ids = sorted(slot["coverage_class_id"] for slot in covered_slots)
    reviewer_ready_slot_count = sum(
        1 for slot in required_slots if slot["actual_contract_status"] == "reviewer_ready"
    )
    typed_blocked_slot_count = sum(
        1 for slot in required_slots if slot["actual_contract_status"] == "typed_blocked"
    )
    distinct_forest_ids = sorted(
        {
            str(slot.get("forest_unit_id"))
            for slot in required_slots
            if str(slot.get("forest_unit_id") or "").strip()
        }
    )
    distinct_package_style_tags = sorted(
        {
            str(tag)
            for slot in required_slots
            for tag in slot.get("package_style_tags", [])
            if str(tag).strip()
        }
    )
    missing_package_authority_count = sum(
        1 for slot in required_slots if not slot["package_authority"]["passed"]
    )
    missing_required_slot_count = len(required_slots) - len(covered_slots)
    missing_coverage_class_ids = sorted(
        set(required_coverage_class_ids) - {slot["coverage_class_id"] for slot in covered_slots}
    )
    threshold_failures = _threshold_failures(
        thresholds=_int_dict(manifest.get("coverage_thresholds")),
        required_slot_count=len(required_slots),
        required_coverage_class_count=len(required_coverage_class_ids),
        distinct_forest_count=len(distinct_forest_ids),
        distinct_package_style_count=len(distinct_package_style_tags),
        reviewer_ready_slot_count=reviewer_ready_slot_count,
        typed_blocked_slot_count=typed_blocked_slot_count,
        missing_required_slot_count=missing_required_slot_count,
        missing_package_authority_count=missing_package_authority_count,
    )
    failure_category_counts = _failure_category_counts(
        slot_results=required_slots,
        threshold_failures=threshold_failures,
        missing_coverage_class_ids=missing_coverage_class_ids,
    )
    passed = all(slot["passed"] for slot in required_slots) and not threshold_failures
    summary = {
        "schema_version": REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "output_dir": str(results_output_dir),
        "output_path": str(output_path),
        "real_package_review_coverage_id": manifest.get("id"),
        "real_package_review_coverage_version": manifest.get("version"),
        "passed": passed,
        "required_slot_count": len(required_slots),
        "covered_slot_count": len(covered_slots),
        "covered_review_ids": covered_review_ids,
        "required_coverage_class_ids": required_coverage_class_ids,
        "covered_coverage_class_ids": covered_coverage_class_ids,
        "missing_coverage_class_ids": missing_coverage_class_ids,
        "reviewer_ready_slot_count": reviewer_ready_slot_count,
        "typed_blocked_slot_count": typed_blocked_slot_count,
        "distinct_forest_count": len(distinct_forest_ids),
        "distinct_forest_ids": distinct_forest_ids,
        "distinct_package_style_count": len(distinct_package_style_tags),
        "distinct_package_style_tags": distinct_package_style_tags,
        "missing_required_slot_count": missing_required_slot_count,
        "missing_package_authority_count": missing_package_authority_count,
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "slots": slot_results,
    }
    results_output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RealPackageReviewCoverageEvalResult(
        manifest_path=manifest_path,
        output_dir=results_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _slot_result(
    *,
    slot: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
    run_v1_ea_review_eval: Any,
) -> dict[str, Any]:
    review_id = str(slot["review_id"]).strip()
    results_path = slot.get("results_path")
    eval_file = _resolve_repo_path(str(slot["eval_file"]), manifest_path)
    summary = (
        _load_summary(_resolve_repo_path(str(results_path), manifest_path))
        if results_path
        else run_v1_ea_review_eval(
            output_dir=output_dir,
            review_id=review_id,
            eval_file=eval_file,
        ).summary
    )
    contract_expectations = summary.get("contract_expectations", {})
    package_authority = _package_authority_result(
        authority_spec=slot.get("package_authority"),
        manifest_path=manifest_path,
    )
    actual_review_id = str(summary.get("review_id") or "").strip()
    actual_contract_status = str(summary.get("contract_status") or "mismatch").strip()
    expected_contract_status = str(slot["expected_contract_status"]).strip()
    missing_contract = actual_review_id != review_id
    contract_status_match = actual_contract_status == expected_contract_status
    forest_unit_id = str(summary.get("forest_unit_id") or slot.get("forest_unit_id") or "").strip()
    package_style_tags = _string_list(
        summary.get("package_style_tags") or slot.get("package_style_tags")
    )
    expected_blocker_categories = _string_list(
        contract_expectations.get("allowed_blocker_categories")
        or summary.get("allowed_blocker_categories")
    )
    actual_blocker_categories = sorted(
        {
            *contract_expectations.get("matched_blocker_categories", []),
            *contract_expectations.get("unexpected_blocker_categories", []),
        }
    )
    unexpected_blocker_categories = _string_list(
        contract_expectations.get("unexpected_blocker_categories")
    )
    return {
        "slot_id": str(slot["slot_id"]),
        "label": str(slot["label"]),
        "review_id": review_id,
        "actual_review_id": actual_review_id,
        "package_label": str(slot["package_label"]),
        "coverage_class_id": str(slot["coverage_class_id"]),
        "required": bool(slot["required"]),
        "expected_contract_status": expected_contract_status,
        "contract_status": actual_contract_status,
        "actual_contract_status": actual_contract_status,
        "contract_status_match": contract_status_match,
        "passed": bool(summary.get("passed"))
        and not missing_contract
        and contract_status_match
        and package_authority["passed"],
        "actual_overall_passed": bool(summary.get("actual_overall_passed", summary.get("passed"))),
        "broader_ea_passed": bool(summary.get("broader_ea_passed")),
        "forest_plan_passed": bool(summary.get("forest_plan_passed")),
        "forest_unit_id": forest_unit_id,
        "package_style_tags": package_style_tags,
        "failure_category_counts": summary.get("failure_category_counts", {}),
        "forest_plan_failure_category_counts": summary.get(
            "forest_plan_failure_category_counts",
            {},
        ),
        "package_authority": package_authority,
        "missing_contract": missing_contract,
        "summary_path": str(results_path) if results_path else summary.get("output_path"),
        "eval_file": str(eval_file),
        "expected_blocker_categories": expected_blocker_categories,
        "actual_blocker_categories": actual_blocker_categories,
        "unexpected_blocker_categories": unexpected_blocker_categories,
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
            "mode": None,
        }
    replay_context = authority_spec.get("replay_context_path")
    intake_path = authority_spec.get("intake_package_path")
    details: dict[str, Any] = {}
    failure_reasons = []
    mode = None
    if replay_context:
        mode = "replay_context"
        replay_path = _resolve_repo_path(str(replay_context), manifest_path)
        details["replay_context_path"] = str(replay_path)
        details["replay_context_path_exists"] = replay_path.exists()
        if not replay_path.exists():
            failure_reasons.append("replay_context_missing")
        else:
            payload = _read_json(replay_path)
            package_path = payload.get("package_path")
            if package_path:
                resolved_package_path = _resolve_context_path(
                    replay_path,
                    Path(str(package_path)),
                )
                details["package_path"] = str(resolved_package_path)
                details["package_path_exists"] = resolved_package_path.exists()
                if not resolved_package_path.exists():
                    failure_reasons.append("package_path_missing")
            else:
                failure_reasons.append("replay_context_package_path_missing")
    elif intake_path:
        mode = "intake_path"
        resolved_intake = _resolve_repo_path(str(intake_path), manifest_path)
        details["package_path"] = str(resolved_intake)
        details["package_path_exists"] = resolved_intake.exists()
        if not resolved_intake.exists():
            failure_reasons.append("package_path_missing")
    else:
        failure_reasons.append("missing_package_authority")
    return {
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
        "mode": mode,
        **details,
    }


def _threshold_failures(
    *,
    thresholds: dict[str, int],
    required_slot_count: int,
    required_coverage_class_count: int,
    distinct_forest_count: int,
    distinct_package_style_count: int,
    reviewer_ready_slot_count: int,
    typed_blocked_slot_count: int,
    missing_required_slot_count: int,
    missing_package_authority_count: int,
) -> list[dict[str, Any]]:
    failures = []
    for metric, actual in (
        ("required_slot_count", required_slot_count),
        ("required_coverage_class_count", required_coverage_class_count),
        ("distinct_forest_count_min", distinct_forest_count),
        ("distinct_package_style_count_min", distinct_package_style_count),
        ("reviewer_ready_slot_count_min", reviewer_ready_slot_count),
        ("typed_blocked_slot_count_min", typed_blocked_slot_count),
        ("missing_required_slot_count_max", missing_required_slot_count),
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
    return failures


def _failure_category_counts(
    *,
    slot_results: list[dict[str, Any]],
    threshold_failures: list[dict[str, Any]],
    missing_coverage_class_ids: list[str],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    def bump(category: str) -> None:
        counts[category] = counts.get(category, 0) + 1

    for slot in slot_results:
        if slot["missing_contract"]:
            bump("missing_required_review_contract")
        if not slot["package_authority"]["passed"]:
            bump("missing_package_authority")
        if not slot["contract_status_match"]:
            bump("slot_contract_status_mismatch")
        if slot["expected_contract_status"] == "typed_blocked" and slot["unexpected_blocker_categories"]:
            bump("typed_blocked_blocker_mismatch")
    for failure in threshold_failures:
        metric = str(failure.get("metric") or "")
        if metric == "required_slot_count":
            bump("missing_required_slot")
        elif metric == "required_coverage_class_count":
            bump("missing_required_coverage_class")
        elif metric == "distinct_forest_count_min":
            bump("insufficient_forest_diversity")
        elif metric == "distinct_package_style_count_min":
            bump("insufficient_package_style_diversity")
        elif metric == "reviewer_ready_slot_count_min":
            bump("insufficient_reviewer_ready_slots")
        elif metric == "typed_blocked_slot_count_min":
            bump("missing_typed_blocked_slot")
        elif metric == "missing_required_slot_count_max":
            bump("missing_required_slot")
        elif metric == "missing_package_authority_count_max":
            bump("missing_package_authority")
    for _ in missing_coverage_class_ids:
        bump("missing_required_coverage_class")
    return counts


def _slot_by_review_id(manifest: dict[str, Any], review_id: str) -> dict[str, Any]:
    for slot in manifest.get("slots", []):
        if str(slot.get("review_id") or "").strip() == review_id:
            return slot
    raise ValueError(
        "review_id is not tracked by the real-package review coverage manifest: "
        f"{review_id}"
    )


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("real-package review coverage manifest must be a JSON object")
    if manifest.get("schema_version") != REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION:
        raise ValueError(
            "real-package review coverage manifest must use "
            f"schema_version={REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION!r}"
        )
    if not str(manifest.get("id") or "").strip():
        raise ValueError("real-package review coverage manifest requires id")
    if not str(manifest.get("version") or "").strip():
        raise ValueError("real-package review coverage manifest requires version")

    required_coverage_class_ids = _string_list(manifest.get("required_coverage_class_ids"))
    if not required_coverage_class_ids:
        raise ValueError(
            "real-package review coverage manifest requires required_coverage_class_ids"
        )

    slots = manifest.get("slots")
    if not isinstance(slots, list) or not slots:
        raise ValueError("real-package review coverage manifest requires slots")

    slot_ids: set[str] = set()
    review_ids: set[str] = set()
    required_class_ids: set[str] = set()
    required_slot_count = 0
    for slot in slots:
        if not isinstance(slot, dict):
            raise ValueError("real-package review coverage slots must be JSON objects")
        slot_id = str(slot.get("slot_id") or "").strip()
        review_id = str(slot.get("review_id") or "").strip()
        coverage_class_id = str(slot.get("coverage_class_id") or "").strip()
        required = bool(slot.get("required"))
        _validate_slot(slot)
        if slot_id in slot_ids:
            raise ValueError(f"duplicate real-package review slot_id: {slot_id}")
        if review_id in review_ids:
            raise ValueError(f"duplicate real-package review review_id: {review_id}")
        slot_ids.add(slot_id)
        review_ids.add(review_id)
        if required:
            required_slot_count += 1
            if coverage_class_id in required_class_ids:
                raise ValueError(
                    "required real-package review slots must not share coverage_class_id: "
                    f"{coverage_class_id}"
                )
            required_class_ids.add(coverage_class_id)

    if required_class_ids != set(required_coverage_class_ids):
        raise ValueError(
            "required_coverage_class_ids must exactly match the required slot coverage_class_id set"
        )
    thresholds = _int_dict(manifest.get("coverage_thresholds"))
    required_threshold = thresholds.get("required_slot_count")
    if required_threshold is not None and required_slot_count < required_threshold:
        raise ValueError("real-package review coverage manifest does not meet required_slot_count")


def _validate_slot(slot: dict[str, Any]) -> None:
    for field in (
        "slot_id",
        "label",
        "review_id",
        "package_label",
        "coverage_class_id",
        "forest_unit_id",
        "eval_file",
        "expected_contract_status",
    ):
        if not str(slot.get(field) or "").strip():
            raise ValueError(f"real-package review slot requires non-empty {field}")
    expected_contract_status = str(slot.get("expected_contract_status") or "").strip()
    if expected_contract_status not in EXPECTED_CONTRACT_STATUSES:
        raise ValueError(
            "real-package review slot expected_contract_status must be reviewer_ready or "
            f"typed_blocked: {expected_contract_status}"
        )
    if "required" not in slot:
        raise ValueError("real-package review slot requires required boolean")
    authority_spec = slot.get("package_authority")
    if not isinstance(authority_spec, dict):
        raise ValueError("real-package review slot requires package_authority object")
    modes = [
        field
        for field in ("replay_context_path", "intake_package_path")
        if str(authority_spec.get(field) or "").strip()
    ]
    if len(modes) != 1:
        raise ValueError(
            "real-package review slot package_authority must declare exactly one of "
            "replay_context_path or intake_package_path"
        )
    results_path = slot.get("results_path")
    if results_path is not None and not str(results_path).strip():
        raise ValueError("real-package review slot results_path must be non-empty when provided")


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
