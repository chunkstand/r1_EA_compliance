from __future__ import annotations

from pathlib import Path
from typing import Any

from .phase_eval_direct_eval_support import FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION
from .phase_eval_direct_eval_support import REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION
from .phase_eval_direct_eval_support import V1_EA_EVAL_RESULTS_SCHEMA_VERSION
from .phase_eval_direct_eval_support import _dedupe_strings
from .phase_eval_direct_eval_support import _read_json_if_exists
from .phase_eval_direct_eval_support import _string_list


def resolve_review_scope_status(
    *,
    contract: dict[str, Any],
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
    review_coverage_manifest_path: Path,
    review_coverage_manifest: dict[str, Any] | None,
    component_review_coverage_manifest_path: Path,
    component_review_coverage_manifest: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if review_id is None:
        return None
    if review_dir is None:
        review_dir = output_dir / "reviews" / review_id
    if not isinstance(review_coverage_manifest, dict):
        return {
            **_declared_review_base(review_id),
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "summaries": [],
        }
    if (
        review_coverage_manifest.get("schema_version")
        != REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION
    ):
        return {
            **_declared_review_base(review_id),
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "summaries": [],
        }
    slot = next(
        (
            item
            for item in review_coverage_manifest.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    if slot is None:
        return _ad_hoc_review_scope(review_id=review_id)

    summaries = []
    missing_summary_ids = []
    present_summary_ids = []
    failure_reasons = []
    expected_contract_status = str(slot.get("expected_contract_status") or "")

    v1_eval_path = review_dir / str(contract["declared_review_eval_path"])
    v1_payload = _read_json_if_exists(v1_eval_path)
    summaries.append(
        _v1_ea_eval_summary(
            review_id=review_id,
            expected_contract_status=expected_contract_status,
            path=v1_eval_path,
            payload=v1_payload,
            expected_source_set_id=None,
        )
    )

    coverage_results_path = output_dir / str(contract["review_contract_results_path"])
    coverage_results = _read_json_if_exists(coverage_results_path)
    summaries.append(
        _review_coverage_summary(
            review_id=review_id,
            slot=slot,
            manifest=review_coverage_manifest,
            path=coverage_results_path,
            payload=coverage_results,
        )
    )
    component_coverage_summary = _component_review_coverage_summary_for_review(
        review_id=review_id,
        contract=contract,
        output_dir=output_dir,
        manifest_path=component_review_coverage_manifest_path,
        manifest=component_review_coverage_manifest,
    )
    if component_coverage_summary is not None:
        summaries.append(component_coverage_summary)

    for summary in summaries:
        if summary["present"]:
            present_summary_ids.append(summary["summary_id"])
        else:
            missing_summary_ids.append(summary["summary_id"])
        failure_reasons.extend(summary.get("failure_reasons", []))

    status = "direct_eval_present"
    if any(summary["status"] == "direct_eval_schema_invalid" for summary in summaries):
        status = "direct_eval_schema_invalid"
    elif any(summary["status"] == "direct_eval_identity_mismatch" for summary in summaries):
        status = "direct_eval_identity_mismatch"
    elif any(summary["status"] == "direct_eval_missing" for summary in summaries):
        status = "direct_eval_missing"
    elif any(summary["status"] == "direct_eval_failed" for summary in summaries):
        status = "direct_eval_failed"

    passed = status == "direct_eval_present"
    contract_backed_promotion_ready = bool(
        passed and expected_contract_status == "reviewer_ready"
    )
    if status == "direct_eval_missing":
        failure_reasons.append("missing_required_direct_eval")
    if status == "direct_eval_identity_mismatch":
        failure_reasons.append("direct_eval_identity_mismatch")
    if status == "direct_eval_schema_invalid":
        failure_reasons.append("direct_eval_schema_invalid")
    if status == "direct_eval_failed":
        failure_reasons.append("direct_eval_threshold_failed")
    return {
        **_declared_review_base(review_id),
        "status": status,
        "passed": passed,
        "contract_backed_promotion_ready": contract_backed_promotion_ready,
        "required_summary_ids": [summary["summary_id"] for summary in summaries],
        "present_summary_ids": present_summary_ids,
        "missing_summary_ids": missing_summary_ids,
        "failure_reasons": _dedupe_strings(failure_reasons),
        "expected_contract_status": expected_contract_status,
        "summaries": summaries,
        "review_contract_manifest_path": str(review_coverage_manifest_path),
    }


def _declared_review_base(review_id: str) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "declared_review_contract": True,
        "coverage_class": "required_for_declared_review_contract",
        "contract_backed_promotion_ready": False,
        "required_summary_ids": [],
        "present_summary_ids": [],
        "missing_summary_ids": [],
    }


def _ad_hoc_review_scope(review_id: str | None) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "declared_review_contract": False,
        "coverage_class": "not_required_for_ad_hoc_review",
        "status": "not_required_for_ad_hoc_review",
        "passed": True,
        "contract_backed_promotion_ready": False,
        "required_summary_ids": [],
        "present_summary_ids": [],
        "missing_summary_ids": [],
        "failure_reasons": [],
        "summaries": [],
    }


def _v1_ea_eval_summary(
    *,
    review_id: str,
    expected_contract_status: str,
    path: Path,
    payload: dict[str, Any] | None,
    expected_source_set_id: str | None,
) -> dict[str, Any]:
    summary = {
        "summary_id": "v1_ea_eval",
        "path": str(path),
        "present": isinstance(payload, dict),
        "status": "direct_eval_missing",
        "passed": False,
        "failure_reasons": [],
        "details": {},
    }
    if not isinstance(payload, dict):
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    nested = payload.get("summary")
    contract = payload.get("contract")
    if not isinstance(nested, dict) or not isinstance(contract, dict):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    summary["details"] = {
        "schema_version": nested.get("schema_version"),
        "actual_contract_status": nested.get("contract_status"),
        "actual_review_id": nested.get("review_id"),
        "actual_source_set_id": nested.get("source_set_id"),
        "contract": contract,
    }
    if nested.get("schema_version") != V1_EA_EVAL_RESULTS_SCHEMA_VERSION:
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if (
        str(nested.get("review_id") or "") != review_id
        or str(contract.get("review_id") or "") not in {"", review_id}
    ):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if expected_source_set_id and str(nested.get("source_set_id") or "") != expected_source_set_id:
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if str(nested.get("contract_status") or "") != expected_contract_status:
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if not bool(nested.get("passed")):
        summary["status"] = "direct_eval_failed"
        summary["failure_reasons"] = ["direct_eval_threshold_failed"]
        return summary
    summary["status"] = "direct_eval_present"
    summary["passed"] = True
    return summary


def _review_coverage_summary(
    *,
    review_id: str,
    slot: dict[str, Any],
    manifest: dict[str, Any],
    path: Path,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "summary_id": "real_package_review_coverage",
        "path": str(path),
        "present": isinstance(payload, dict),
        "status": "direct_eval_missing",
        "passed": False,
        "failure_reasons": [],
        "details": {
            "slot_id": slot.get("slot_id"),
            "expected_contract_status": slot.get("expected_contract_status"),
        },
    }
    if not isinstance(payload, dict):
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    summary["details"].update(
        {
            "schema_version": payload.get("schema_version"),
            "real_package_review_coverage_id": payload.get(
                "real_package_review_coverage_id"
            ),
        }
    )
    if (
        payload.get("schema_version")
        != REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION
    ):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if str(payload.get("real_package_review_coverage_id") or "") != str(manifest.get("id") or ""):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    slot_result = next(
        (
            item
            for item in payload.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    summary["details"]["slot_result"] = slot_result
    if not isinstance(slot_result, dict):
        summary["status"] = "direct_eval_missing"
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    if (
        str(slot_result.get("slot_id") or "") != str(slot.get("slot_id") or "")
        or str(slot_result.get("expected_contract_status") or "")
        != str(slot.get("expected_contract_status") or "")
        or str(slot_result.get("actual_review_id") or "") != review_id
    ):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if not bool(slot_result.get("passed")):
        summary["status"] = "direct_eval_failed"
        summary["failure_reasons"] = ["direct_eval_threshold_failed"]
        return summary
    summary["status"] = "direct_eval_present"
    summary["passed"] = True
    return summary


def _component_review_coverage_summary_for_review(
    *,
    review_id: str,
    contract: dict[str, Any],
    output_dir: Path,
    manifest_path: Path,
    manifest: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(manifest, dict):
        return {
            "summary_id": "forest_plan_component_eval_coverage",
            "path": str(output_dir / str(contract["component_review_coverage_results_path"])),
            "present": False,
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "details": {
                "manifest_path": str(manifest_path),
                "reason": "component_review_coverage_manifest_missing",
            },
        }
    if (
        manifest.get("schema_version")
        != FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION
    ):
        return {
            "summary_id": "forest_plan_component_eval_coverage",
            "path": str(output_dir / str(contract["component_review_coverage_results_path"])),
            "present": False,
            "status": "direct_eval_schema_invalid",
            "passed": False,
            "failure_reasons": ["direct_eval_schema_invalid"],
            "details": {
                "manifest_path": str(manifest_path),
                "manifest_schema_version": manifest.get("schema_version"),
            },
        }
    slot = next(
        (
            item
            for item in manifest.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    if slot is None:
        return None
    results_path = output_dir / str(contract["component_review_coverage_results_path"])
    payload = _read_json_if_exists(results_path)
    return _component_review_coverage_summary(
        review_id=review_id,
        slot=slot,
        manifest=manifest,
        manifest_path=manifest_path,
        path=results_path,
        payload=payload,
    )


def _component_review_coverage_summary(
    *,
    review_id: str,
    slot: dict[str, Any],
    manifest: dict[str, Any],
    manifest_path: Path,
    path: Path,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "summary_id": "forest_plan_component_eval_coverage",
        "path": str(path),
        "present": isinstance(payload, dict),
        "status": "direct_eval_missing",
        "passed": False,
        "failure_reasons": [],
        "details": {
            "manifest_path": str(manifest_path),
            "expected_coverage_id": manifest.get("id"),
            "expected_review_id": review_id,
            "expected_slot_id": slot.get("slot_id"),
            "expected_forest_unit_id": slot.get("forest_unit_id"),
            "expected_source_set_id": slot.get("expected_source_set_id"),
        },
    }
    if not isinstance(payload, dict):
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    required_keys = (
        "schema_version",
        "coverage_id",
        "passed",
        "required_review_ids",
        "covered_review_ids",
        "slots",
        "review_component_eval_coverage",
        "component_retrieval_eval",
    )
    if any(key not in payload for key in required_keys):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        summary["details"]["missing_keys"] = [
            key for key in required_keys if key not in payload
        ]
        return summary
    required_review_ids = _string_list(payload.get("required_review_ids"))
    covered_review_ids = _string_list(payload.get("covered_review_ids"))
    slot_result = next(
        (
            item
            for item in payload.get("slots", [])
            if isinstance(item, dict) and str(item.get("review_id") or "") == review_id
        ),
        None,
    )
    summary["details"].update(
        {
            "schema_version": payload.get("schema_version"),
            "actual_coverage_id": payload.get("coverage_id"),
            "required_review_ids": required_review_ids,
            "covered_review_ids": covered_review_ids,
            "slot_result": slot_result,
            "review_component_eval_coverage": payload.get("review_component_eval_coverage"),
            "component_retrieval_eval": payload.get("component_retrieval_eval"),
        }
    )
    if (
        payload.get("schema_version")
        != FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION
    ):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if str(payload.get("coverage_id") or "") != str(manifest.get("id") or ""):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if review_id not in _string_list(manifest.get("required_review_ids")):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if review_id not in required_review_ids:
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    if not isinstance(slot_result, dict):
        summary["status"] = "direct_eval_missing"
        summary["failure_reasons"] = ["missing_required_direct_eval"]
        return summary
    if (
        str(slot_result.get("slot_id") or "") != str(slot.get("slot_id") or "")
        or str(slot_result.get("review_id") or "") != review_id
        or str(slot_result.get("forest_unit_id") or "")
        != str(slot.get("forest_unit_id") or "")
        or str(slot_result.get("expected_source_set_id") or "")
        != str(slot.get("expected_source_set_id") or "")
    ):
        summary["status"] = "direct_eval_identity_mismatch"
        summary["failure_reasons"] = ["direct_eval_identity_mismatch"]
        return summary
    review_coverage = payload.get("review_component_eval_coverage")
    if not isinstance(review_coverage, dict):
        summary["status"] = "direct_eval_schema_invalid"
        summary["failure_reasons"] = ["direct_eval_schema_invalid"]
        return summary
    if (
        not bool(payload.get("passed"))
        or not bool(review_coverage.get("passed"))
        or not bool(slot_result.get("passed"))
        or review_id not in covered_review_ids
    ):
        summary["status"] = "direct_eval_failed"
        summary["failure_reasons"] = ["direct_eval_threshold_failed"]
        return summary
    summary["status"] = "direct_eval_present"
    summary["passed"] = True
    return summary
