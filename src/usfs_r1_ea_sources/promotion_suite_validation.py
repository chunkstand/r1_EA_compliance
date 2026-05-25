from __future__ import annotations

from typing import Any

from .promotion_suite_support import FOREST_PLAN_PROFILE_GATE_RESULT_IDS
from .promotion_suite_support import PROMOTION_SUITE_SCHEMA_VERSION
from .promotion_suite_support import SAFE_ID_RE


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != PROMOTION_SUITE_SCHEMA_VERSION:
        raise ValueError(
            "Promotion suite manifest must use schema_version "
            f"{PROMOTION_SUITE_SCHEMA_VERSION!r}."
        )
    for key in (
        "id",
        "source_set_id",
        "rule_pack_path",
        "rule_pack_id",
        "rule_pack_version",
    ):
        if not str(manifest.get(key) or "").strip():
            raise ValueError(f"Promotion suite manifest is missing {key!r}.")
    _validate_safe_id(str(manifest["id"]), "suite id")
    full_canonical_source_set_id = str(manifest.get("full_canonical_source_set_id") or "")
    if full_canonical_source_set_id:
        _validate_safe_id(
            full_canonical_source_set_id,
            "full canonical source set id",
        )
    for case in manifest.get("review_cases", []):
        _validate_safe_id(str(case.get("id") or ""), "review case id")
        _validate_safe_id(str(case.get("review_id") or ""), "review id")
        for result in case.get("results", []):
            _validate_result_spec(result)
    for result in manifest.get("suite_results", []):
        _validate_result_spec(result)
    required_full_canonical_results = [
        result
        for result in manifest.get("suite_results", [])
        if result.get("required_for_full_canonical_corpus")
    ]
    if full_canonical_source_set_id and not required_full_canonical_results:
        raise ValueError(
            "Promotion suite manifest with full_canonical_source_set_id must define at least one "
            "suite_result required_for_full_canonical_corpus."
        )
    if required_full_canonical_results and not full_canonical_source_set_id:
        raise ValueError(
            "Promotion suite manifest with required_for_full_canonical_corpus results must define "
            "full_canonical_source_set_id."
        )
    current_promotion_contract = manifest.get("current_promotion_contract")
    if current_promotion_contract is not None:
        if not isinstance(current_promotion_contract, dict):
            raise ValueError("Promotion suite current_promotion_contract must be an object.")
        _validate_current_promotion_contract(
            current_promotion_contract,
            review_cases=manifest.get("review_cases", []),
            suite_results=manifest.get("suite_results", []),
        )
    expansion_result_ids_by_review_id = _required_expansion_result_ids_by_review_id(
        manifest
    )
    for slot in manifest.get("expansion_slots", []):
        _validate_expansion_slot_spec(
            slot,
            expansion_result_ids_by_review_id=expansion_result_ids_by_review_id,
        )


def _required_expansion_result_ids_by_review_id(
    manifest: dict[str, Any],
) -> dict[str, set[str]]:
    result_ids_by_review_id: dict[str, set[str]] = {}
    for case in manifest.get("review_cases", []):
        review_id = str(case.get("review_id") or "")
        result_ids = {
            str(result.get("id") or "")
            for result in case.get("results", [])
            if result.get("required_for_expansion")
        }
        if result_ids:
            result_ids_by_review_id[review_id] = result_ids
    return result_ids_by_review_id


def _validate_current_promotion_contract(
    contract: dict[str, Any],
    *,
    review_cases: list[dict[str, Any]],
    suite_results: list[dict[str, Any]],
) -> None:
    selector = contract.get("slot_selector")
    if not isinstance(selector, dict):
        raise ValueError("Promotion suite current_promotion_contract requires slot_selector.")
    _validate_current_promotion_selector(selector)

    quorum = contract.get("quorum")
    if not isinstance(quorum, dict):
        raise ValueError("Promotion suite current_promotion_contract requires quorum.")
    for key in ("eligible_slot_count_min", "passing_slot_count_min"):
        value = quorum.get(key)
        if not isinstance(value, int) or value < 1:
            raise ValueError(
                "Promotion suite current_promotion_contract quorum values must be "
                f"positive integers; {key!r} is invalid."
            )

    canaries = contract.get("reference_canaries")
    if not isinstance(canaries, list) or not canaries:
        raise ValueError(
            "Promotion suite current_promotion_contract requires at least one "
            "reference_canary."
        )
    review_case_ids = {str(case.get("id") or "") for case in review_cases}
    review_result_ids = {
        str(result.get("id") or "")
        for case in review_cases
        for result in case.get("results", [])
    }
    suite_result_ids = {str(result.get("id") or "") for result in suite_results}
    for canary in canaries:
        if not isinstance(canary, dict):
            raise ValueError(
                "Promotion suite current_promotion_contract reference_canaries must contain "
                "objects."
            )
        _validate_safe_id(str(canary.get("id") or ""), "reference canary id")
        review_case_id = str(canary.get("review_case_id") or "")
        _validate_safe_id(review_case_id, "reference canary review case id")
        if review_case_id not in review_case_ids:
            raise ValueError(
                "Promotion suite reference canary review_case_id must match a declared "
                f"review case; got {review_case_id!r}."
            )

    families = contract.get("artifact_families")
    if not isinstance(families, list) or not families:
        raise ValueError(
            "Promotion suite current_promotion_contract requires artifact_families."
        )
    seen_family_ids: set[str] = set()
    for family in families:
        _validate_current_promotion_family(
            family,
            review_result_ids=review_result_ids,
            suite_result_ids=suite_result_ids,
            seen_family_ids=seen_family_ids,
        )


def _validate_current_promotion_selector(selector: dict[str, Any]) -> None:
    for forbidden_key in ("review_id", "review_ids", "review_case_id", "review_case_ids"):
        if forbidden_key in selector:
            raise ValueError(
                "Promotion suite current_promotion slot_selector must resolve governed "
                f"coverage classes, not hard-coded {forbidden_key} selectors."
            )
    selector_type = str(selector.get("selector_type") or "")
    if selector_type != "governed_coverage_class":
        raise ValueError(
            "Promotion suite current_promotion slot_selector.selector_type must be "
            "'governed_coverage_class'."
        )
    for key in ("coverage_manifest_path", "coverage_results_path"):
        if not str(selector.get(key) or "").strip():
            raise ValueError(
                "Promotion suite current_promotion slot_selector is missing "
                f"{key!r}."
            )
    coverage_class_ids = selector.get("coverage_class_ids")
    if not isinstance(coverage_class_ids, list) or not coverage_class_ids:
        raise ValueError(
            "Promotion suite current_promotion slot_selector requires coverage_class_ids."
        )
    for coverage_class_id in coverage_class_ids:
        _validate_safe_id(str(coverage_class_id or ""), "coverage class id")
    allowed_contract_statuses = selector.get("allowed_contract_statuses")
    if (
        not isinstance(allowed_contract_statuses, list)
        or not allowed_contract_statuses
    ):
        raise ValueError(
            "Promotion suite current_promotion slot_selector requires "
            "allowed_contract_statuses."
        )
    for contract_status in allowed_contract_statuses:
        _validate_safe_id(str(contract_status or ""), "allowed contract status")


def _validate_current_promotion_family(
    family: dict[str, Any],
    *,
    review_result_ids: set[str],
    suite_result_ids: set[str],
    seen_family_ids: set[str],
) -> None:
    if not isinstance(family, dict):
        raise ValueError(
            "Promotion suite current_promotion artifact_families must contain objects."
        )
    family_id = str(family.get("id") or "")
    _validate_safe_id(family_id, "current promotion family id")
    if family_id in seen_family_ids:
        raise ValueError(
            f"Promotion suite current_promotion artifact_families contains duplicate id "
            f"{family_id!r}."
        )
    seen_family_ids.add(family_id)
    for forbidden_key in (
        "checks",
        "json_path",
        "equals",
        "min",
        "contains_all",
        "non_empty",
        "starts_with",
        "file_sha256_matches",
    ):
        if forbidden_key in family:
            raise ValueError(
                "Promotion suite current_promotion family "
                f"{family_id!r} embeds packet-local checks; keep packet-specific counts and "
                "assertions in focused validators instead."
            )
    family_scope = str(family.get("family_scope") or "")
    if family_scope == "suite":
        result_ids = family.get("suite_result_ids")
        if not isinstance(result_ids, list) or not result_ids:
            raise ValueError(
                f"Promotion suite current_promotion suite family {family_id!r} requires "
                "suite_result_ids."
            )
        for result_id in result_ids:
            safe_result_id = str(result_id or "")
            _validate_safe_id(safe_result_id, "suite family result id")
            if safe_result_id not in suite_result_ids:
                raise ValueError(
                    f"Promotion suite current_promotion suite family {family_id!r} "
                    f"references unknown suite_result_id {safe_result_id!r}."
                )
        return
    if family_scope != "review_slot":
        raise ValueError(
            "Promotion suite current_promotion family_scope must be 'suite' or "
            f"'review_slot'; got {family_scope!r}."
        )
    if str(family.get("slot_binding") or "") != "same_slot":
        raise ValueError(
            f"Promotion suite current_promotion review_slot family {family_id!r} must use "
            "slot_binding='same_slot' so artifacts cannot be mixed across slots."
        )
    if str(family.get("source_set_binding") or "") != "current_promotion_source_set":
        raise ValueError(
            f"Promotion suite current_promotion review_slot family {family_id!r} must use "
            "source_set_binding='current_promotion_source_set'."
        )
    passing_slot_count_min = family.get("passing_slot_count_min")
    if not isinstance(passing_slot_count_min, int) or passing_slot_count_min < 1:
        raise ValueError(
            f"Promotion suite current_promotion review_slot family {family_id!r} must define "
            "a positive passing_slot_count_min."
        )
    result_ids = family.get("review_result_ids")
    if not isinstance(result_ids, list) or not result_ids:
        raise ValueError(
            f"Promotion suite current_promotion review_slot family {family_id!r} requires "
            "review_result_ids."
        )
    for result_id in result_ids:
        safe_result_id = str(result_id or "")
        _validate_safe_id(safe_result_id, "review slot family result id")
        if safe_result_id not in review_result_ids:
            raise ValueError(
                f"Promotion suite current_promotion review_slot family {family_id!r} "
                f"references unknown review_result_id {safe_result_id!r}."
            )


def _validate_expansion_slot_spec(
    slot: dict[str, Any],
    *,
    expansion_result_ids_by_review_id: dict[str, set[str]],
) -> None:
    slot_id = str(slot.get("id") or "")
    _validate_safe_id(slot_id, "expansion slot id")
    ready = bool(slot.get("ready", False))
    status = str(slot.get("status") or "open")
    if ready and slot.get("failure_category"):
        raise ValueError(
            f"Promotion suite expansion slot {slot_id!r} is ready but still has "
            "failure_category."
        )
    has_selected_contract = status != "open" or any(
        key in slot
        for key in (
            "review_id",
            "package_path",
            "source_set_id",
            "expected_gate_artifacts",
            "project_metadata",
            "forest_plan_profile",
        )
    )
    if ready:
        has_selected_contract = True
    if not has_selected_contract:
        return
    if not ready and str(slot.get("failure_category") or "") == "package_fixture_missing":
        raise ValueError(
            f"Promotion suite selected expansion slot {slot_id!r} must use a typed "
            "failure_category other than 'package_fixture_missing'."
        )
    required_keys = ["review_id", "package_path", "source_set_id", "next_action"]
    if not ready:
        required_keys.append("failure_category")
    for key in required_keys:
        if not str(slot.get(key) or "").strip():
            raise ValueError(
                f"Promotion suite selected expansion slot {slot_id!r} is missing {key!r}."
            )
    _validate_safe_id(str(slot["review_id"]), "expansion slot review id")
    _validate_safe_id(str(slot["source_set_id"]), "expansion slot source set id")
    gate_artifacts = slot.get("expected_gate_artifacts")
    if not isinstance(gate_artifacts, list) or not gate_artifacts:
        raise ValueError(
            f"Promotion suite selected expansion slot {slot_id!r} must define "
            "expected_gate_artifacts."
        )
    for artifact in gate_artifacts:
        if not isinstance(artifact, dict):
            raise ValueError(
                f"Promotion suite selected expansion slot {slot_id!r} has an invalid "
                "expected gate artifact."
            )
        _validate_safe_id(str(artifact.get("id") or ""), "expected gate artifact id")
        if not str(artifact.get("path") or "").strip():
            raise ValueError(
                f"Promotion suite selected expansion slot {slot_id!r} has an expected "
                "gate artifact without a path."
            )
    gate_artifact_ids = {str(artifact.get("id") or "") for artifact in gate_artifacts}
    if slot.get("forest_plan_profile"):
        review_result_ids = expansion_result_ids_by_review_id.get(str(slot["review_id"]), set())
        missing_forest_gate_results = sorted(
            FOREST_PLAN_PROFILE_GATE_RESULT_IDS - review_result_ids
        )
        if missing_forest_gate_results:
            raise ValueError(
                f"Promotion suite selected expansion slot {slot_id!r} declares "
                "forest_plan_profile but is missing required expansion result ids: "
                f"{', '.join(missing_forest_gate_results)}."
            )
        missing_forest_gate_artifacts = sorted(
            FOREST_PLAN_PROFILE_GATE_RESULT_IDS - gate_artifact_ids
        )
        if missing_forest_gate_artifacts:
            raise ValueError(
                f"Promotion suite selected expansion slot {slot_id!r} declares "
                "forest_plan_profile but expected_gate_artifacts is missing: "
                f"{', '.join(missing_forest_gate_artifacts)}."
            )
    if ready:
        required_result_ids = expansion_result_ids_by_review_id.get(str(slot["review_id"]))
        if not required_result_ids:
            raise ValueError(
                f"Promotion suite ready expansion slot {slot_id!r} must have matching "
                "review-case results marked required_for_expansion."
            )
        missing_result_ids = sorted(required_result_ids - gate_artifact_ids)
        if missing_result_ids:
            raise ValueError(
                f"Promotion suite ready expansion slot {slot_id!r} expected_gate_artifacts "
                "must include required expansion result ids: "
                f"{', '.join(missing_result_ids)}."
            )


def _validate_result_spec(spec: dict[str, Any]) -> None:
    _validate_safe_id(str(spec.get("id") or ""), "result id")
    if not str(spec.get("path") or "").strip():
        raise ValueError(f"Promotion suite result {spec.get('id')!r} is missing path.")
    for check in spec.get("checks", []):
        _validate_safe_id(str(check.get("name") or ""), "check name")
        if "starts_with" in check:
            continue
        if "file_sha256_matches" in check:
            hash_spec = check["file_sha256_matches"]
            if not isinstance(hash_spec, dict):
                raise ValueError(
                    f"Promotion suite check {check.get('name')!r} has invalid "
                    "file_sha256_matches spec."
                )
            for key in ("path_json_path", "sha256_json_path"):
                if not str(hash_spec.get(key) or "").strip():
                    raise ValueError(
                        f"Promotion suite check {check.get('name')!r} is missing {key}."
                    )
            continue
        if not str(check.get("json_path") or "").strip():
            raise ValueError(
                f"Promotion suite check {check.get('name')!r} is missing json_path."
            )
        supported = {
            "equals",
            "min",
            "contains_all",
            "non_empty",
            "starts_with",
            "file_sha256_matches",
        }
        if not supported.intersection(check):
            raise ValueError(
                f"Promotion suite check {check.get('name')!r} must define one of "
                f"{sorted(supported)}."
            )


def _validate_safe_id(value: str, label: str) -> None:
    if not value or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{label} must contain only letters, numbers, dot, underscore, or hyphen."
        )
