from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any


REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_SCHEMA_VERSION = (
    "region1-forest-plan-component-inventory-build-manifest-v0"
)
DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "r1_forest_plan_component_inventory_build_manifest.json"
)
DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "region1_forest_plan_readiness_nepa_3d_v1.json"
)
SUPPORTED_SOURCE_SET_REFERENCE_TYPES = {"explicit_source_set_id"}
SUPPORTED_PROMOTION_ELIGIBILITY_STATUSES = {"eligible", "eligible_with_blockers"}
SUPPORTED_ACCEPTED_BLOCKERS = {
    "component_inventory_build_required",
    "official_source_gap_documented",
}
SOURCE_SET_ID_RE = re.compile(r"^source-set-[A-Za-z0-9]+$")


@dataclass(frozen=True)
class SourceSetReference:
    reference_id: str
    reference_type: str
    source_set_id: str
    description: str


@dataclass(frozen=True)
class PromotionEligibility:
    status: str
    accepted_blockers: tuple[str, ...]


@dataclass(frozen=True)
class InventoryBuildProfile:
    forest_unit_id: str
    source_set_reference_id: str
    primary_plan_source_record_id: str
    plan_version: str
    build_source_record_ids_by_role: dict[str, tuple[str, ...]]
    promotion_eligibility: PromotionEligibility

    @property
    def source_record_ids(self) -> tuple[str, ...]:
        return tuple(
            source_record_id
            for source_record_ids in self.build_source_record_ids_by_role.values()
            for source_record_id in source_record_ids
        )


@dataclass(frozen=True)
class Region1ForestPlanInventoryBuildManifest:
    schema_version: str
    manifest_id: str
    source_set_references: tuple[SourceSetReference, ...]
    profile_rows: tuple[InventoryBuildProfile, ...]

    def get(self, forest_unit_id: str) -> InventoryBuildProfile:
        for row in self.profile_rows:
            if row.forest_unit_id == forest_unit_id:
                return row
        raise KeyError(f"Unknown inventory build profile: {forest_unit_id}")

    def source_set_reference(self, reference_id: str) -> SourceSetReference:
        for reference in self.source_set_references:
            if reference.reference_id == reference_id:
                return reference
        raise KeyError(f"Unknown source-set reference: {reference_id}")


def load_region1_forest_plan_inventory_build_manifest(
    path: Path = DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    *,
    readiness_path: Path = DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH,
) -> Region1ForestPlanInventoryBuildManifest:
    payload = _read_json(path)
    schema_version = _require_string(payload, "schema_version", "inventory build manifest")
    if schema_version != REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported Region 1 inventory build manifest schema_version: "
            f"{schema_version!r}; expected "
            f"{REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_SCHEMA_VERSION!r}"
        )
    manifest_id = _require_string(payload, "manifest_id", "inventory build manifest")
    raw_references = _require_list(payload, "source_set_references", "inventory build manifest")
    if not raw_references:
        raise ValueError("inventory build manifest.source_set_references cannot be empty.")
    source_set_references = tuple(
        _parse_source_set_reference(raw_reference, index)
        for index, raw_reference in enumerate(raw_references)
    )
    _reject_duplicate(
        [reference.reference_id for reference in source_set_references],
        "reference_id",
        "inventory build manifest.source_set_references",
    )
    raw_profiles = _require_list(payload, "profile_rows", "inventory build manifest")
    if not raw_profiles:
        raise ValueError("inventory build manifest.profile_rows cannot be empty.")
    profile_rows = tuple(
        _parse_profile_row(raw_profile, index)
        for index, raw_profile in enumerate(raw_profiles)
    )
    _reject_duplicate(
        [row.forest_unit_id for row in profile_rows],
        "forest_unit_id",
        "inventory build manifest.profile_rows",
    )
    references_by_id = {reference.reference_id for reference in source_set_references}
    for row in profile_rows:
        if row.source_set_reference_id not in references_by_id:
            raise ValueError(
                f"inventory build manifest.profile_rows[{row.forest_unit_id!r}] references unknown "
                f"source_set_reference_id {row.source_set_reference_id!r}"
            )
    readiness_rows = _load_readiness_rows(readiness_path)
    readiness_units = {
        forest_unit_id
        for forest_unit_id in (
            _require_string(row, "forest_unit_id", f"readiness.profile_rows[{index}]")
            for index, row in enumerate(readiness_rows)
        )
    }
    manifest_units = {row.forest_unit_id for row in profile_rows}
    missing_units = sorted(readiness_units - manifest_units)
    extra_units = sorted(manifest_units - readiness_units)
    if missing_units or extra_units:
        parts = []
        if missing_units:
            parts.append(f"missing coverage for {', '.join(missing_units)}")
        if extra_units:
            parts.append(f"unexpected profiles {', '.join(extra_units)}")
        raise ValueError(
            "inventory build manifest.profile_rows must match readiness profile_rows: "
            + "; ".join(parts)
        )
    readiness_rows_by_unit = {
        _require_string(row, "forest_unit_id", f"readiness.profile_rows[{index}]"): row
        for index, row in enumerate(readiness_rows)
    }
    for row in profile_rows:
        readiness_row = _require_object(
            readiness_rows_by_unit[row.forest_unit_id],
            f"readiness.profile_rows[{row.forest_unit_id!r}]",
        )
        readiness_source_record_ids = {
            source_record_id
            for index, source_requirement in enumerate(
                _require_list(
                    readiness_row,
                    "source_requirements",
                    f"readiness.profile_rows[{row.forest_unit_id!r}]",
                )
            )
            if (
                source_record_id := _optional_string(
                    _require_object(
                        source_requirement,
                        f"readiness.profile_rows[{row.forest_unit_id!r}].source_requirements[{index}]",
                    ),
                    "source_record_id",
                    f"readiness.profile_rows[{row.forest_unit_id!r}].source_requirements[{index}]",
                )
            )
        }
        missing_readiness_sources = sorted(readiness_source_record_ids - set(row.source_record_ids))
        if missing_readiness_sources:
            raise ValueError(
                "inventory build manifest.profile_rows"
                f"[{row.forest_unit_id!r}] must include readiness source_record_ids: "
                + ", ".join(missing_readiness_sources)
            )
    return Region1ForestPlanInventoryBuildManifest(
        schema_version=schema_version,
        manifest_id=manifest_id,
        source_set_references=source_set_references,
        profile_rows=profile_rows,
    )


def _parse_source_set_reference(raw_reference: object, index: int) -> SourceSetReference:
    context = f"inventory build manifest.source_set_references[{index}]"
    reference = _require_object(raw_reference, context)
    reference_type = _require_string(reference, "reference_type", context)
    if reference_type not in SUPPORTED_SOURCE_SET_REFERENCE_TYPES:
        supported_types = ", ".join(sorted(SUPPORTED_SOURCE_SET_REFERENCE_TYPES))
        raise ValueError(
            f"{context}.reference_type must be one of {supported_types}; got {reference_type!r}"
        )
    source_set_id = _require_string(reference, "source_set_id", context)
    if not SOURCE_SET_ID_RE.match(source_set_id):
        raise ValueError(f"{context}.source_set_id must look like a source-set id.")
    return SourceSetReference(
        reference_id=_require_string(reference, "reference_id", context),
        reference_type=reference_type,
        source_set_id=source_set_id,
        description=_require_string(reference, "description", context),
    )


def _parse_profile_row(raw_profile: object, index: int) -> InventoryBuildProfile:
    context = f"inventory build manifest.profile_rows[{index}]"
    profile = _require_object(raw_profile, context)
    build_source_record_ids_by_role = _parse_build_source_record_ids_by_role(
        _require_object(profile.get("build_source_record_ids_by_role"), context),
        context,
    )
    primary_plan_source_record_id = _require_string(profile, "primary_plan_source_record_id", context)
    if primary_plan_source_record_id not in {
        source_record_id
        for source_record_ids in build_source_record_ids_by_role.values()
        for source_record_id in source_record_ids
    }:
        raise ValueError(
            f"{context}.primary_plan_source_record_id must be present in build_source_record_ids_by_role."
        )
    return InventoryBuildProfile(
        forest_unit_id=_require_string(profile, "forest_unit_id", context),
        source_set_reference_id=_require_string(profile, "source_set_reference_id", context),
        primary_plan_source_record_id=primary_plan_source_record_id,
        plan_version=_require_string(profile, "plan_version", context),
        build_source_record_ids_by_role=build_source_record_ids_by_role,
        promotion_eligibility=_parse_promotion_eligibility(
            _require_object(profile.get("promotion_eligibility"), context),
            context,
        ),
    )


def _parse_build_source_record_ids_by_role(
    raw_source_records: dict[str, object],
    context: str,
) -> dict[str, tuple[str, ...]]:
    if not raw_source_records:
        raise ValueError(f"{context}.build_source_record_ids_by_role cannot be empty.")
    source_record_ids_by_role: dict[str, tuple[str, ...]] = {}
    for role, raw_source_record_ids in raw_source_records.items():
        if not isinstance(role, str) or not role.strip():
            raise ValueError(f"{context}.build_source_record_ids_by_role keys must be strings.")
        role_context = f"{context}.build_source_record_ids_by_role[{role!r}]"
        source_record_ids = _require_string_tuple(
            {"source_record_ids": raw_source_record_ids},
            "source_record_ids",
            role_context,
        )
        _reject_duplicate(list(source_record_ids), "source_record_id", role_context)
        source_record_ids_by_role[role] = source_record_ids
    _reject_duplicate(
        [
            source_record_id
            for source_record_ids in source_record_ids_by_role.values()
            for source_record_id in source_record_ids
        ],
        "source_record_id",
        f"{context}.build_source_record_ids_by_role",
    )
    return source_record_ids_by_role


def _parse_promotion_eligibility(
    raw_promotion_eligibility: dict[str, object],
    context: str,
) -> PromotionEligibility:
    promotion_context = f"{context}.promotion_eligibility"
    status = _require_string(raw_promotion_eligibility, "status", promotion_context)
    if status not in SUPPORTED_PROMOTION_ELIGIBILITY_STATUSES:
        supported_statuses = ", ".join(sorted(SUPPORTED_PROMOTION_ELIGIBILITY_STATUSES))
        raise ValueError(
            f"{promotion_context}.status must be one of {supported_statuses}; got {status!r}"
        )
    accepted_blockers = _optional_string_tuple_allow_empty(
        raw_promotion_eligibility,
        "accepted_blockers",
        promotion_context,
    )
    _reject_duplicate(list(accepted_blockers), "accepted_blocker", promotion_context)
    unsupported_blockers = sorted(set(accepted_blockers) - SUPPORTED_ACCEPTED_BLOCKERS)
    if unsupported_blockers:
        raise ValueError(
            f"{promotion_context}.accepted_blockers contains unsupported values: "
            + ", ".join(unsupported_blockers)
        )
    if status == "eligible" and accepted_blockers:
        raise ValueError(f"{promotion_context}.accepted_blockers must be empty when status='eligible'.")
    if status == "eligible_with_blockers" and not accepted_blockers:
        raise ValueError(
            f"{promotion_context}.accepted_blockers cannot be empty when status='eligible_with_blockers'."
        )
    return PromotionEligibility(status=status, accepted_blockers=accepted_blockers)


def _load_readiness_rows(path: Path) -> list[dict[str, Any]]:
    readiness = _read_json(path)
    return _require_list(readiness, "profile_rows", "readiness")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object at the top level.")
    return payload


def _require_object(raw_value: object, context: str) -> dict[str, object]:
    if not isinstance(raw_value, dict):
        raise ValueError(f"{context} must be an object.")
    return raw_value


def _require_string(payload: dict[str, object], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string.")
    return value


def _optional_string(payload: dict[str, object], key: str, context: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string when provided.")
    return value


def _require_list(payload: dict[str, object], key: str, context: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be a list.")
    return value


def _require_string_tuple(payload: dict[str, object], key: str, context: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be a list.")
    strings = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}.{key}[{index}] must be a non-empty string.")
        strings.append(item)
    if not strings:
        raise ValueError(f"{context}.{key} cannot be empty.")
    return tuple(strings)


def _optional_string_tuple(payload: dict[str, object], key: str, context: str) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    return _require_string_tuple(payload, key, context)


def _optional_string_tuple_allow_empty(
    payload: dict[str, object],
    key: str,
    context: str,
) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be a list.")
    strings = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}.{key}[{index}] must be a non-empty string.")
        strings.append(item)
    return tuple(strings)


def _reject_duplicate(values: list[str], label: str, context: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        duplicates_text = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate {label} values in {context}: {duplicates_text}")
