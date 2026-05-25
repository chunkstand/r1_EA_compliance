from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .promotion_suite_support import _check_result
from .promotion_suite_support import _read_json
from .promotion_suite_support import _resolve_output_path
from .promotion_suite_support import _resolve_repo_path


def _current_promotion_contract_result(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    context: dict[str, str],
    output_dir: Path,
    rule_pack_result: dict[str, Any],
    review_results: list[dict[str, Any]],
    suite_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    contract = manifest.get("current_promotion_contract")
    if not isinstance(contract, dict):
        return None

    selector = dict(contract.get("slot_selector") or {})
    coverage_manifest_path = _resolve_repo_path(
        str(selector.get("coverage_manifest_path") or ""),
        manifest_path,
    )
    coverage_results_path = _resolve_output_path(
        str(selector.get("coverage_results_path") or ""),
        output_dir,
    )
    coverage_manifest = (
        _read_json(coverage_manifest_path) if coverage_manifest_path.exists() else None
    )
    coverage_results = (
        _read_json(coverage_results_path) if coverage_results_path.exists() else None
    )
    coverage_manifest_slots = {
        str(slot.get("slot_id") or ""): slot
        for slot in (coverage_manifest or {}).get("slots", [])
        if str(slot.get("slot_id") or "").strip()
    }
    review_cases_by_id = {str(case["id"]): case for case in review_results}
    review_cases_by_review_id = {str(case["review_id"]): case for case in review_results}
    suite_results_by_id = {str(result["id"]): result for result in suite_results}

    selector_checks = [
        _check_result(
            name="coverage_manifest_exists",
            passed=coverage_manifest_path.exists(),
            expected=True,
            actual=coverage_manifest_path.exists(),
            failure_category="missing_source",
            details={"path": str(coverage_manifest_path)},
        ),
        _check_result(
            name="coverage_results_exists",
            passed=coverage_results_path.exists(),
            expected=True,
            actual=coverage_results_path.exists(),
            failure_category="missing_source",
            details={"path": str(coverage_results_path)},
        ),
    ]
    coverage_class_ids = {
        str(value)
        for value in selector.get("coverage_class_ids", [])
        if str(value).strip()
    }
    allowed_contract_statuses = {
        str(value)
        for value in selector.get("allowed_contract_statuses", [])
        if str(value).strip()
    }

    governed_slots: list[dict[str, Any]] = []
    selector_failure_categories: list[str] = []
    if coverage_manifest is None:
        selector_failure_categories.append("missing_source")
    if coverage_results is None:
        selector_failure_categories.append("missing_source")
    if coverage_results is not None:
        for slot in coverage_results.get("slots", []):
            normalized = _normalized_current_slot(
                slot=slot,
                coverage_manifest_slot=coverage_manifest_slots.get(
                    str(slot.get("slot_id") or "")
                ),
                manifest_path=manifest_path,
                output_dir=output_dir,
                current_source_set_id=str(context.get("source_set_id") or ""),
                review_cases_by_review_id=review_cases_by_review_id,
            )
            if normalized["coverage_class_id"] not in coverage_class_ids:
                continue
            if normalized["contract_status"] not in allowed_contract_statuses:
                continue
            governed_slots.append(normalized)
            if not normalized["eligible"]:
                selector_failure_categories.extend(normalized["failure_categories"])
    if not governed_slots:
        selector_failure_categories.append("unsupported_package_evidence")
    selector_passed = all(check["passed"] for check in selector_checks) and bool(governed_slots)

    suite_family_results = []
    review_slot_family_results = []
    per_slot_family_results: dict[str, list[dict[str, Any]]] = {
        slot["slot_id"]: [] for slot in governed_slots
    }
    for family in contract.get("artifact_families", []):
        family_scope = str(family.get("family_scope") or "")
        if family_scope == "suite":
            suite_family_results.append(
                _suite_family_result(
                    family=family,
                    suite_results_by_id=suite_results_by_id,
                )
            )
            continue
        family_result = _review_slot_family_result(
            family=family,
            governed_slots=governed_slots,
            review_cases_by_review_id=review_cases_by_review_id,
            current_source_set_id=str(context.get("source_set_id") or ""),
        )
        review_slot_family_results.append(family_result)
        for slot_result in family_result["slot_results"]:
            per_slot_family_results.setdefault(str(slot_result["slot_id"]), []).append(slot_result)

    passing_slots = []
    for slot in governed_slots:
        slot_family_results = per_slot_family_results.get(slot["slot_id"], [])
        contract_passed = slot["eligible"] and all(
            result["passed"] for result in slot_family_results
        )
        slot["review_family_results"] = slot_family_results
        slot["contract_passed"] = contract_passed
        if contract_passed:
            passing_slots.append(slot)

    quorum = dict(contract.get("quorum") or {})
    eligible_slot_count_min = int(quorum.get("eligible_slot_count_min") or 1)
    passing_slot_count_min = int(quorum.get("passing_slot_count_min") or 1)
    quorum_checks = [
        _check_result(
            name="eligible_slot_count",
            passed=len([slot for slot in governed_slots if slot["eligible"]])
            >= eligible_slot_count_min,
            expected={">=": eligible_slot_count_min},
            actual=len([slot for slot in governed_slots if slot["eligible"]]),
            failure_category="unsupported_package_evidence",
        ),
        _check_result(
            name="passing_slot_count",
            passed=len(passing_slots) >= passing_slot_count_min,
            expected={">=": passing_slot_count_min},
            actual=len(passing_slots),
            failure_category="unsupported_package_evidence",
        ),
    ]
    quorum_passed = all(check["passed"] for check in quorum_checks)

    reference_canaries = []
    reference_canary_failure_counts: Counter[str] = Counter()
    for canary in contract.get("reference_canaries", []):
        review_case = review_cases_by_id.get(str(canary.get("review_case_id") or ""))
        required_results = [
            result
            for result in (review_case or {}).get("results", [])
            if result.get("required_for_current_promotion")
        ]
        failure_categories = sorted(
            {
                category
                for result in required_results
                if not result["passed"]
                for category in result.get("failure_categories", [])
            }
        )
        canary_result = {
            "id": str(canary.get("id") or ""),
            "label": canary.get("label"),
            "review_case_id": str(canary.get("review_case_id") or ""),
            "review_id": review_case.get("review_id") if review_case else None,
            "required": bool(canary.get("required", True)),
            "passed": bool(review_case and review_case.get("promotion_ready")),
            "failure_categories": failure_categories,
        }
        reference_canaries.append(canary_result)
        if canary_result["required"] and not canary_result["passed"]:
            reference_canary_failure_counts.update(failure_categories or ["stale_artifact"])

    current_failure_counts: Counter[str] = Counter()
    if contract.get("require_rule_pack_result", True) and not rule_pack_result["passed"]:
        current_failure_counts.update(rule_pack_result.get("failure_categories", []))
    current_failure_counts.update(selector_failure_categories)
    for family_result in suite_family_results + review_slot_family_results:
        if not family_result["passed"]:
            current_failure_counts.update(family_result.get("failure_categories", []))
    if not quorum_passed and not current_failure_counts:
        current_failure_counts.update(["unsupported_package_evidence"])

    all_family_results = suite_family_results + review_slot_family_results
    current_promotion_ready = (
        (not contract.get("require_rule_pack_result", True) or rule_pack_result["passed"])
        and selector_passed
        and all(result["passed"] for result in all_family_results)
        and quorum_passed
    )
    return {
        "require_rule_pack_result": bool(contract.get("require_rule_pack_result", True)),
        "rule_pack_passed": bool(rule_pack_result["passed"]),
        "coverage_manifest_path": str(coverage_manifest_path),
        "coverage_results_path": str(coverage_results_path),
        "coverage_class_ids": sorted(coverage_class_ids),
        "allowed_contract_statuses": sorted(allowed_contract_statuses),
        "selector_passed": selector_passed,
        "selector_checks": selector_checks,
        "quorum_passed": quorum_passed,
        "quorum_checks": quorum_checks,
        "matched_slot_count": len(governed_slots),
        "eligible_slot_count": len([slot for slot in governed_slots if slot["eligible"]]),
        "passing_slot_count": len(passing_slots),
        "governed_slots": governed_slots,
        "family_results": all_family_results,
        "reference_canaries": reference_canaries,
        "reference_canary_ready": all(
            canary["passed"] for canary in reference_canaries if canary["required"]
        ),
        "failure_category_counts": dict(sorted(current_failure_counts.items())),
        "reference_canary_failure_category_counts": dict(
            sorted(reference_canary_failure_counts.items())
        ),
        "passed": current_promotion_ready,
    }


def _normalized_current_slot(
    *,
    slot: dict[str, Any],
    coverage_manifest_slot: dict[str, Any] | None,
    manifest_path: Path,
    output_dir: Path,
    current_source_set_id: str,
    review_cases_by_review_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    review_id = str(slot.get("review_id") or "").strip()
    source_set_id = (
        str(slot.get("source_set_id") or "").strip()
        or _slot_source_set_id(
            slot=slot,
            coverage_manifest_slot=coverage_manifest_slot,
            manifest_path=manifest_path,
            output_dir=output_dir,
        )
    )
    review_case = review_cases_by_review_id.get(review_id)
    failure_categories = {
        *slot.get("failure_category_counts", {}).keys(),
        *slot.get("forest_plan_failure_category_counts", {}).keys(),
        *slot.get("package_authority", {}).get("failure_reasons", []),
    }
    if slot.get("missing_contract"):
        failure_categories.add("stale_artifact")
    eligible = bool(slot.get("passed"))
    return {
        "slot_id": str(slot.get("slot_id") or ""),
        "label": slot.get("label"),
        "review_id": review_id,
        "review_case_id": review_case.get("id") if review_case else None,
        "package_label": slot.get("package_label"),
        "coverage_class_id": str(slot.get("coverage_class_id") or ""),
        "contract_status": str(
            slot.get("actual_contract_status") or slot.get("contract_status") or ""
        ),
        "slot_passed": bool(slot.get("passed")),
        "eligible": eligible,
        "source_set_id": source_set_id,
        "source_set_matches_current_promotion": bool(source_set_id)
        and source_set_id == current_source_set_id,
        "failure_categories": sorted(failure_categories),
    }


def _slot_source_set_id(
    *,
    slot: dict[str, Any],
    coverage_manifest_slot: dict[str, Any] | None,
    manifest_path: Path,
    output_dir: Path,
) -> str:
    summary_path_value = str(slot.get("summary_path") or "").strip()
    if summary_path_value:
        summary_path = _resolve_output_path(summary_path_value, output_dir)
        if summary_path.exists():
            summary = _read_json(summary_path)
            source_set_id = str(summary.get("source_set_id") or "").strip()
            if source_set_id:
                return source_set_id
    authority_spec = (coverage_manifest_slot or {}).get("package_authority")
    if isinstance(authority_spec, dict):
        replay_context_path = str(authority_spec.get("replay_context_path") or "").strip()
        if replay_context_path:
            resolved_path = _resolve_repo_path(replay_context_path, manifest_path)
            if resolved_path.exists():
                replay_context = _read_json(resolved_path)
                return str(replay_context.get("source_set_id") or "").strip()
    return ""


def _suite_family_result(
    *,
    family: dict[str, Any],
    suite_results_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    result_ids = [str(result_id) for result_id in family.get("suite_result_ids", [])]
    missing_result_ids = [result_id for result_id in result_ids if result_id not in suite_results_by_id]
    failed_result_ids = [
        result_id
        for result_id in result_ids
        if result_id in suite_results_by_id and not suite_results_by_id[result_id]["passed"]
    ]
    failure_categories = {
        "unsupported_package_evidence" for _ in missing_result_ids
    }
    for result_id in failed_result_ids:
        failure_categories.update(suite_results_by_id[result_id].get("failure_categories", []))
    return {
        "id": str(family.get("id") or ""),
        "family_scope": "suite",
        "suite_result_ids": result_ids,
        "missing_result_ids": missing_result_ids,
        "failed_result_ids": failed_result_ids,
        "passing_slot_count_min": None,
        "passing_slot_count": None,
        "passed": not missing_result_ids and not failed_result_ids,
        "failure_categories": sorted(failure_categories),
        "slot_results": [],
    }


def _review_slot_family_result(
    *,
    family: dict[str, Any],
    governed_slots: list[dict[str, Any]],
    review_cases_by_review_id: dict[str, dict[str, Any]],
    current_source_set_id: str,
) -> dict[str, Any]:
    result_ids = [str(result_id) for result_id in family.get("review_result_ids", [])]
    slot_results = []
    for slot in governed_slots:
        review_case = review_cases_by_review_id.get(str(slot["review_id"]))
        failure_categories = set()
        missing_review_case = review_case is None
        if missing_review_case:
            failure_categories.add("unsupported_package_evidence")
            result_map: dict[str, dict[str, Any]] = {}
        else:
            result_map = {str(result["id"]): result for result in review_case.get("results", [])}
        missing_result_ids = [result_id for result_id in result_ids if result_id not in result_map]
        if missing_result_ids:
            failure_categories.add("unsupported_package_evidence")
        failed_result_ids = [
            result_id
            for result_id in result_ids
            if result_id in result_map and not result_map[result_id]["passed"]
        ]
        for result_id in failed_result_ids:
            failure_categories.update(result_map[result_id].get("failure_categories", []))
        source_set_matches = bool(slot["source_set_id"]) and slot["source_set_id"] == current_source_set_id
        if not source_set_matches:
            failure_categories.add("stale_artifact")
        passed = (
            slot["eligible"]
            and not missing_review_case
            and not missing_result_ids
            and not failed_result_ids
            and source_set_matches
        )
        slot_results.append(
            {
                "slot_id": slot["slot_id"],
                "review_id": slot["review_id"],
                "review_case_id": slot.get("review_case_id"),
                "source_set_id": slot["source_set_id"],
                "source_set_matches_current_promotion": source_set_matches,
                "missing_review_case": missing_review_case,
                "missing_result_ids": missing_result_ids,
                "failed_result_ids": failed_result_ids,
                "passed": passed,
                "failure_categories": sorted(failure_categories),
            }
        )
    passing_slot_count = sum(1 for result in slot_results if result["passed"])
    passing_slot_count_min = int(family.get("passing_slot_count_min") or 1)
    failure_categories = {
        category
        for result in slot_results
        if not result["passed"]
        for category in result["failure_categories"]
    }
    return {
        "id": str(family.get("id") or ""),
        "family_scope": "review_slot",
        "review_result_ids": result_ids,
        "slot_binding": family.get("slot_binding"),
        "source_set_binding": family.get("source_set_binding"),
        "passing_slot_count_min": passing_slot_count_min,
        "passing_slot_count": passing_slot_count,
        "passed": passing_slot_count >= passing_slot_count_min,
        "failure_categories": sorted(failure_categories),
        "slot_results": slot_results,
    }
