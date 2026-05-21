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
