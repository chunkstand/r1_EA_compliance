from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json


FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION = "forest-plan-component-eval-coverage-v1"
FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-eval-coverage-results-v1"
)
FOREST_PLAN_COMPONENT_EVAL_CONTRACT_SCHEMA_VERSION = "forest-plan-component-eval-v0"
FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION = "forest-plan-component-eval-results-v0"
FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_SCHEMA_VERSION = (
    "forest-plan-component-retrieval-eval-v1"
)
FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-retrieval-eval-results-v1"
)
DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH = Path(
    "config/forest_plan_component_eval_coverage_v1.json"
)
DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_DIR = Path(
    "evaluations/forest_plan_component_eval_coverage"
)
DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_RESULTS_PATH = Path(
    "evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_results.json"
)
EXPECTED_FUTURE_FOREST_EXPANSION_POLICY = {
    "mode": "manifest_slots_only",
    "allow_untracked_non_ecid_reviews": False,
    "require_per_review_contract": True,
}


@dataclass(frozen=True)
class ForestPlanComponentEvalCoverageResult:
    manifest_path: Path
    output_dir: Path
    output_path: Path
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
    results_dir: Path | None = None,
) -> ForestPlanComponentEvalCoverageResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    results_output_dir = (
        Path(results_dir)
        if results_dir is not None
        else output_dir / DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_DIR
    )
    output_path = results_output_dir / "forest_plan_component_eval_coverage_results.json"

    manifest = _read_json(manifest_path)
    _validate_manifest(manifest)

    output_expectations = _string_list(
        (manifest.get("output_schema") or {}).get("required_summary_fields")
    )
    retrieval_state = _component_retrieval_eval_state(
        spec=manifest.get("component_retrieval_eval"),
        manifest_path=manifest_path,
        output_dir=output_dir,
    )
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
    blocked_typed_slots = _typed_blocked_slots(manifest)
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
    review_coverage_passed = all(slot["passed"] for slot in required_slots) and not threshold_failures
    future_policy_state = _future_forest_expansion_policy_state(
        manifest.get("future_forest_expansion_policy")
    )

    contract_checks = [
        {
            "name": "component_retrieval_eval_manifest_declared",
            "passed": retrieval_state["manifest_declared"],
            "details": {
                "manifest_path": retrieval_state["manifest_path"],
                "results_path": retrieval_state["results_path"],
            },
        },
        {
            "name": "typed_blocked_slots_declared",
            "passed": isinstance(manifest.get("typed_blocked_slots"), list),
            "details": {
                "typed_blocked_slot_count": len(blocked_typed_slots),
                "typed_blocked_review_ids": sorted(
                    str(slot.get("review_id") or "").strip()
                    for slot in blocked_typed_slots
                    if str(slot.get("review_id") or "").strip()
                ),
            },
        },
        {
            "name": "future_forest_expansion_policy_explicit",
            "passed": future_policy_state["explicit"],
            "details": future_policy_state["details"],
        },
        {
            "name": "future_forest_expansion_policy_enforced",
            "passed": future_policy_state["passed"],
            "details": future_policy_state["details"],
        },
    ]
    failure_category_counts = _failure_category_counts(
        slot_results=required_slots,
        threshold_failures=threshold_failures,
        retrieval_state=retrieval_state,
        future_policy_state=future_policy_state,
    )
    review_component_eval_coverage = {
        "passed": review_coverage_passed,
        "required_review_count": len(required_slots),
        "covered_review_count": len(covered_slots),
        "covered_review_ids": sorted(slot["review_id"] for slot in covered_slots),
        "distinct_forest_count": len(distinct_forest_ids),
        "distinct_forest_ids": distinct_forest_ids,
        "missing_contract_count": missing_contract_count,
        "missing_result_count": missing_result_count,
        "stale_identity_count": stale_identity_count,
        "unresolved_review_count": unresolved_review_count,
    }
    summary = {
        "schema_version": FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION,
        "manifest_schema_version": manifest.get("schema_version"),
        "created_at": _utc_now(),
        "manifest_path": str(manifest_path),
        "results_dir": str(results_output_dir),
        "output_path": str(output_path),
        "coverage_id": manifest.get("id"),
        "coverage_version": manifest.get("version"),
        "passed": False,
        "component_retrieval_eval": retrieval_state,
        "review_component_eval_coverage": review_component_eval_coverage,
        "required_review_ids": _string_list(manifest.get("required_review_ids")),
        "required_review_count": len(required_slots),
        "covered_review_count": len(covered_slots),
        "covered_review_ids": review_component_eval_coverage["covered_review_ids"],
        "distinct_forest_count": len(distinct_forest_ids),
        "distinct_forest_ids": distinct_forest_ids,
        "missing_contract_count": missing_contract_count,
        "missing_result_count": missing_result_count,
        "stale_identity_count": stale_identity_count,
        "unresolved_review_count": unresolved_review_count,
        "blocked_typed_slot_count": len(blocked_typed_slots),
        "blocked_typed_slots": blocked_typed_slots,
        "future_forest_expansion_policy": future_policy_state,
        "threshold_failures": threshold_failures,
        "failure_category_counts": dict(sorted(failure_category_counts.items())),
        "contract_checks": contract_checks,
        "slots": slot_results,
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
        retrieval_state["passed"]
        and review_coverage_passed
        and future_policy_state["passed"]
        and all(check["passed"] for check in summary["contract_checks"])
    )
    return ForestPlanComponentEvalCoverageResult(
        manifest_path=manifest_path,
        output_dir=output_dir,
        output_path=output_path,
        summary=summary,
    )


def run_forest_plan_component_eval_coverage(
    *,
    output_dir: Path,
    manifest_path: Path = DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
    results_dir: Path | None = None,
) -> ForestPlanComponentEvalCoverageResult:
    result = evaluate_forest_plan_component_eval_coverage(
        output_dir=output_dir,
        manifest_path=manifest_path,
        results_dir=results_dir,
    )
    result.output_path.parent.mkdir(parents=True, exist_ok=True)
    result.output_path.write_text(
        json.dumps(result.summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _component_retrieval_eval_state(
    *,
    spec: Any,
    manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    spec_dict = spec if isinstance(spec, dict) else {}
    retrieval_manifest_text = str(spec_dict.get("manifest_path") or "").strip()
    manifest_declared = bool(retrieval_manifest_text)
    retrieval_manifest_path = (
        _resolve_repo_path(retrieval_manifest_text, manifest_path)
        if manifest_declared
        else manifest_path.parent / "missing_component_retrieval_manifest.json"
    )
    retrieval_results_text = str(spec_dict.get("results_path") or "").strip()
    results_path = (
        _resolve_repo_path(retrieval_results_text, manifest_path)
        if retrieval_results_text
        else output_dir / DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_RESULTS_PATH
    )

    manifest_exists = manifest_declared and retrieval_manifest_path.exists()
    retrieval_manifest = _read_json(retrieval_manifest_path) if manifest_exists else {}
    results_exists = results_path.exists()
    results = _read_json(results_path) if results_exists else {}

    failure_reasons: list[str] = []
    if not manifest_declared:
        failure_reasons.append("component_retrieval_manifest_not_declared")
    elif not manifest_exists:
        failure_reasons.append("missing_component_retrieval_manifest")

    manifest_schema_version = str(retrieval_manifest.get("schema_version") or "").strip()
    manifest_valid = (
        manifest_exists
        and manifest_schema_version == FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_SCHEMA_VERSION
    )
    if manifest_exists and not manifest_valid:
        failure_reasons.append("component_retrieval_manifest_schema_mismatch")

    expected_contract_id = str(retrieval_manifest.get("contract_id") or "").strip()
    expected_source_set_id = str(retrieval_manifest.get("source_set_id") or "").strip()

    if not results_exists:
        failure_reasons.append("missing_component_retrieval_result")

    result_schema_version = str(results.get("schema_version") or "").strip()
    result_valid = (
        results_exists
        and result_schema_version == FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION
    )
    if results_exists and not result_valid:
        failure_reasons.append("component_retrieval_result_schema_mismatch")

    result_manifest_path = str(results.get("manifest_path") or "").strip()
    result_contract_id = str(results.get("contract_id") or "").strip()
    result_source_set_id = str(results.get("source_set_id") or "").strip()
    result_passed = bool(results.get("passed"))
    if (
        result_valid
        and manifest_valid
        and _resolve_result_reference_path(result_manifest_path) != retrieval_manifest_path.resolve()
    ):
        failure_reasons.append("component_retrieval_manifest_path_mismatch")
    if result_valid and manifest_valid and expected_contract_id != result_contract_id:
        failure_reasons.append("component_retrieval_contract_id_mismatch")
    if result_valid and manifest_valid and expected_source_set_id != result_source_set_id:
        failure_reasons.append("component_retrieval_source_set_id_mismatch")
    if result_valid and not result_passed:
        failure_reasons.append("component_retrieval_eval_not_passed")

    return {
        "manifest_declared": manifest_declared,
        "manifest_path": str(retrieval_manifest_path),
        "results_path": str(results_path),
        "manifest_exists": manifest_exists,
        "results_exists": results_exists,
        "manifest_schema_version": manifest_schema_version,
        "result_schema_version": result_schema_version,
        "contract_id": result_contract_id or expected_contract_id,
        "source_set_id": result_source_set_id or expected_source_set_id,
        "result_passed": result_passed,
        "missing_contract": any(
            reason in {
                "component_retrieval_manifest_not_declared",
                "missing_component_retrieval_manifest",
            }
            for reason in failure_reasons
        ),
        "missing_result": "missing_component_retrieval_result" in failure_reasons,
        "stale_identity": any(reason.endswith("_mismatch") for reason in failure_reasons),
        "passed": not failure_reasons,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def _future_forest_expansion_policy_state(policy: Any) -> dict[str, Any]:
    policy_dict = policy if isinstance(policy, dict) else {}
    details = {
        "expected": EXPECTED_FUTURE_FOREST_EXPANSION_POLICY,
        "actual": {
            "mode": policy_dict.get("mode"),
            "allow_untracked_non_ecid_reviews": policy_dict.get(
                "allow_untracked_non_ecid_reviews"
            ),
            "require_per_review_contract": policy_dict.get("require_per_review_contract"),
        },
    }
    explicit = all(key in policy_dict for key in EXPECTED_FUTURE_FOREST_EXPANSION_POLICY)
    passed = explicit and all(
        policy_dict.get(key) == value
        for key, value in EXPECTED_FUTURE_FOREST_EXPANSION_POLICY.items()
    )
    failure_reasons = []
    if not explicit:
        failure_reasons.append("future_review_contract_policy_missing")
    elif not passed:
        failure_reasons.append("future_review_contract_policy_drift")
    return {
        "explicit": explicit,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "details": details,
    }


def _typed_blocked_slots(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    slots = manifest.get("typed_blocked_slots")
    if not isinstance(slots, list):
        return []
    return [
        {
            "slot_id": str(slot.get("slot_id") or "").strip(),
            "label": str(slot.get("label") or "").strip(),
            "review_id": str(slot.get("review_id") or "").strip(),
            "forest_unit_id": str(slot.get("forest_unit_id") or "").strip(),
            "blocked_reason": str(slot.get("blocked_reason") or "").strip(),
        }
        for slot in slots
        if isinstance(slot, dict)
    ]


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
    retrieval_state: dict[str, Any],
    future_policy_state: dict[str, Any],
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

    for reason in retrieval_state.get("failure_reasons", []):
        if reason in {
            "component_retrieval_manifest_not_declared",
            "missing_component_retrieval_manifest",
        }:
            bump("missing_component_retrieval_contract")
        elif reason == "missing_component_retrieval_result":
            bump("missing_component_retrieval_result")
        elif reason in {
            "component_retrieval_manifest_schema_mismatch",
            "component_retrieval_result_schema_mismatch",
        }:
            bump("invalid_component_retrieval_eval")
        elif reason in {
            "component_retrieval_manifest_path_mismatch",
            "component_retrieval_contract_id_mismatch",
            "component_retrieval_source_set_id_mismatch",
        }:
            bump("stale_component_retrieval_identity")
        elif reason == "component_retrieval_eval_not_passed":
            bump("failed_component_retrieval_eval")

    for reason in future_policy_state.get("failure_reasons", []):
        if reason in {
            "future_review_contract_policy_missing",
            "future_review_contract_policy_drift",
        }:
            bump("future_review_contract_policy_drift")

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

    component_retrieval_eval = manifest.get("component_retrieval_eval")
    if not isinstance(component_retrieval_eval, dict):
        raise ValueError(
            "forest-plan component eval coverage manifest requires component_retrieval_eval"
        )
    if not str(component_retrieval_eval.get("manifest_path") or "").strip():
        raise ValueError(
            "forest-plan component eval coverage manifest requires component_retrieval_eval.manifest_path"
        )

    output_schema = manifest.get("output_schema")
    if not isinstance(output_schema, dict) or not _string_list(
        output_schema.get("required_summary_fields")
    ):
        raise ValueError(
            "forest-plan component eval coverage manifest requires output_schema.required_summary_fields"
        )

    future_policy = manifest.get("future_forest_expansion_policy")
    if not isinstance(future_policy, dict):
        raise ValueError(
            "forest-plan component eval coverage manifest requires future_forest_expansion_policy"
        )
    for field in EXPECTED_FUTURE_FOREST_EXPANSION_POLICY:
        if field not in future_policy:
            raise ValueError(
                "forest-plan component eval coverage manifest requires "
                f"future_forest_expansion_policy.{field}"
            )

    typed_blocked_slots = manifest.get("typed_blocked_slots")
    if not isinstance(typed_blocked_slots, list):
        raise ValueError(
            "forest-plan component eval coverage manifest requires typed_blocked_slots list"
        )
    for slot in typed_blocked_slots:
        _validate_typed_blocked_slot(slot)

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
        raise ValueError("required_review_ids must exactly match the required slot review_id set")
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


def _validate_typed_blocked_slot(slot: Any) -> None:
    if not isinstance(slot, dict):
        raise ValueError("forest-plan component eval coverage typed_blocked_slots must be objects")
    for field in ("slot_id", "label", "review_id", "forest_unit_id", "blocked_reason"):
        if not str(slot.get(field) or "").strip():
            raise ValueError(
                "forest-plan component eval coverage typed_blocked_slots require non-empty "
                f"{field}"
            )


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


def _resolve_result_reference_path(path_text: str) -> Path:
    return Path(path_text or ".").resolve()


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
