from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


FOREST_PLAN_PROFILES_SCHEMA_VERSION = "forest-plan-profiles-v0"
DEFAULT_FOREST_PLAN_PROFILES_PATH = Path("config/forest_plan_profiles.json")


@dataclass(frozen=True)
class ForestPlanSourceRecord:
    role: str
    source_record_id: str
    required_for: str


@dataclass(frozen=True)
class ForestPlanTermEntry:
    entry_id: str
    category: str
    name: str
    aliases: tuple[str, ...] = ()
    source_record_id: str | None = None

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


@dataclass(frozen=True)
class SupportingRecordTriggerRule:
    route_id: str
    category: str
    name: str
    target_source_role: str
    source_record_id: str
    package_terms: tuple[str, ...]
    source_query: str
    source_terms: tuple[str, ...]
    trigger_terms: tuple[str, ...]


@dataclass(frozen=True)
class KnownForestUnit:
    forest_unit_id: str
    names: tuple[str, ...]


@dataclass(frozen=True)
class ForestPlanProfile:
    forest_unit_id: str
    forest_unit_names: tuple[str, ...]
    ambiguous_unit_terms: tuple[str, ...]
    active_plan_source_record_id: str
    supporting_source_record_ids_by_role: dict[str, ForestPlanSourceRecord]
    required_readiness_source_roles: tuple[str, ...]
    ranger_district_terms: tuple[ForestPlanTermEntry, ...]
    geographic_area_terms: tuple[ForestPlanTermEntry, ...]
    management_area_terms: tuple[ForestPlanTermEntry, ...]
    overlay_terms: tuple[ForestPlanTermEntry, ...]
    plan_component_types: tuple[str, ...]
    supporting_record_trigger_rules: tuple[SupportingRecordTriggerRule, ...]
    review_topics: tuple[str, ...]
    profile_data_source: str | None = None

    @property
    def supporting_source_records(self) -> tuple[ForestPlanSourceRecord, ...]:
        return tuple(self.supporting_source_record_ids_by_role.values())

    @property
    def required_source_record_ids(self) -> tuple[str, ...]:
        return tuple(
            self.supporting_source_record_ids_by_role[role].source_record_id
            for role in self.required_readiness_source_roles
        )

    def source_record_id_for_role(self, role: str) -> str:
        try:
            return self.supporting_source_record_ids_by_role[role].source_record_id
        except KeyError as error:
            raise KeyError(f"Unknown forest-plan source role for {self.forest_unit_id}: {role}") from error


@dataclass(frozen=True)
class ForestPlanProfileCollection:
    schema_version: str
    profiles: tuple[ForestPlanProfile, ...]
    known_other_forest_units: tuple[KnownForestUnit, ...] = ()

    def get(self, forest_unit_id: str) -> ForestPlanProfile:
        for profile in self.profiles:
            if profile.forest_unit_id == forest_unit_id:
                return profile
        raise KeyError(f"Unknown forest-plan profile: {forest_unit_id}")


def load_forest_plan_profiles(
    path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
) -> ForestPlanProfileCollection:
    payload = _read_json(path)
    schema_version = _require_string(payload, "schema_version", "profile collection")
    if schema_version != FOREST_PLAN_PROFILES_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan profile schema_version: "
            f"{schema_version!r}; expected {FOREST_PLAN_PROFILES_SCHEMA_VERSION!r}"
        )
    raw_profiles = _require_list(payload, "profiles", "profile collection")
    if not raw_profiles:
        raise ValueError("Forest-plan profile collection must contain at least one profile.")
    profiles = tuple(_parse_profile(raw_profile, index) for index, raw_profile in enumerate(raw_profiles))
    _reject_duplicate(
        [profile.forest_unit_id for profile in profiles],
        "forest_unit_id",
        "profile collection",
    )
    known_other_forest_units = tuple(
        _parse_known_forest_unit(raw_unit, index)
        for index, raw_unit in enumerate(
            _optional_list(payload, "known_other_forest_units", "profile collection")
        )
    )
    _reject_duplicate(
        [unit.forest_unit_id for unit in known_other_forest_units],
        "forest_unit_id",
        "known_other_forest_units",
    )
    return ForestPlanProfileCollection(
        schema_version=schema_version,
        profiles=profiles,
        known_other_forest_units=known_other_forest_units,
    )


def load_forest_plan_profile(
    forest_unit_id: str,
    path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
) -> ForestPlanProfile:
    return load_forest_plan_profiles(path).get(forest_unit_id)


def _parse_profile(raw_profile: object, index: int) -> ForestPlanProfile:
    context = f"profiles[{index}]"
    profile = _require_object(raw_profile, context)
    forest_unit_id = _require_string(profile, "forest_unit_id", context)
    forest_unit_names = _require_string_tuple(profile, "forest_unit_names", context)
    ambiguous_unit_terms = _require_string_tuple(profile, "ambiguous_unit_terms", context)
    active_plan_source_record_id = _require_string(profile, "active_plan_source_record_id", context)
    source_records = _parse_source_records(
        _require_object(profile.get("supporting_source_record_ids_by_role"), f"{context}.source_roles"),
        context,
    )
    if not any(
        record.source_record_id == active_plan_source_record_id for record in source_records.values()
    ):
        raise ValueError(
            f"{context}.active_plan_source_record_id must be present in "
            "supporting_source_record_ids_by_role."
        )
    required_roles = _require_string_tuple(profile, "required_readiness_source_roles", context)
    _reject_duplicate(
        list(required_roles),
        "source role",
        f"{context}.required_readiness_source_roles",
    )
    _validate_known_roles(required_roles, source_records, f"{context}.required_readiness_source_roles")
    default_plan_source_id = active_plan_source_record_id
    ranger_district_terms = _parse_term_entries(
        profile.get("ranger_district_terms", []),
        field="ranger_district_terms",
        context=context,
        default_source_record_id=None,
    )
    geographic_area_terms = _parse_term_entries(
        profile.get("geographic_area_terms", []),
        field="geographic_area_terms",
        context=context,
        default_source_record_id=default_plan_source_id,
    )
    management_area_terms = _parse_term_entries(
        profile.get("management_area_terms", []),
        field="management_area_terms",
        context=context,
        default_source_record_id=default_plan_source_id,
    )
    overlay_terms = _parse_term_entries(
        profile.get("overlay_terms", []),
        field="overlay_terms",
        context=context,
        default_source_record_id=default_plan_source_id,
    )
    supporting_record_trigger_rules = _parse_trigger_rules(
        profile.get("supporting_record_trigger_rules", []),
        source_records=source_records,
        context=context,
    )
    return ForestPlanProfile(
        forest_unit_id=forest_unit_id,
        forest_unit_names=forest_unit_names,
        ambiguous_unit_terms=ambiguous_unit_terms,
        active_plan_source_record_id=active_plan_source_record_id,
        supporting_source_record_ids_by_role=source_records,
        required_readiness_source_roles=required_roles,
        ranger_district_terms=ranger_district_terms,
        geographic_area_terms=geographic_area_terms,
        management_area_terms=management_area_terms,
        overlay_terms=overlay_terms,
        plan_component_types=_require_string_tuple(profile, "plan_component_types", context),
        supporting_record_trigger_rules=supporting_record_trigger_rules,
        review_topics=_require_string_tuple(profile, "review_topics", context),
        profile_data_source=_optional_string(profile, "profile_data_source", context),
    )


def _parse_source_records(
    raw_source_records: dict[str, object],
    context: str,
) -> dict[str, ForestPlanSourceRecord]:
    source_records = {}
    for role, raw_record in raw_source_records.items():
        if not isinstance(role, str) or not role.strip():
            raise ValueError(f"{context}.supporting_source_record_ids_by_role keys must be strings.")
        record_context = f"{context}.supporting_source_record_ids_by_role[{role!r}]"
        record = _require_object(raw_record, record_context)
        source_records[role] = ForestPlanSourceRecord(
            role=role,
            source_record_id=_require_string(record, "source_record_id", record_context),
            required_for=_require_string(record, "required_for", record_context),
        )
    if not source_records:
        raise ValueError(f"{context}.supporting_source_record_ids_by_role cannot be empty.")
    _reject_duplicate(
        [record.source_record_id for record in source_records.values()],
        "source_record_id",
        f"{context}.supporting_source_record_ids_by_role",
    )
    return source_records


def _parse_term_entries(
    raw_entries: object,
    *,
    field: str,
    context: str,
    default_source_record_id: str | None,
) -> tuple[ForestPlanTermEntry, ...]:
    entries = []
    for index, raw_entry in enumerate(_require_list({field: raw_entries}, field, context)):
        entry_context = f"{context}.{field}[{index}]"
        entry = _require_object(raw_entry, entry_context)
        entries.append(
            ForestPlanTermEntry(
                entry_id=_require_string(entry, "entry_id", entry_context),
                category=_require_string(entry, "category", entry_context),
                name=_require_string(entry, "name", entry_context),
                aliases=_optional_string_tuple(entry, "aliases", entry_context),
                source_record_id=_optional_string(
                    entry,
                    "source_record_id",
                    entry_context,
                    default=default_source_record_id,
                ),
            )
        )
    _reject_duplicate([entry.entry_id for entry in entries], "entry_id", f"{context}.{field}")
    return tuple(entries)


def _parse_trigger_rules(
    raw_rules: object,
    *,
    source_records: dict[str, ForestPlanSourceRecord],
    context: str,
) -> tuple[SupportingRecordTriggerRule, ...]:
    rules = []
    for index, raw_rule in enumerate(
        _require_list({"supporting_record_trigger_rules": raw_rules}, "supporting_record_trigger_rules", context)
    ):
        rule_context = f"{context}.supporting_record_trigger_rules[{index}]"
        rule = _require_object(raw_rule, rule_context)
        target_source_role = _require_string(rule, "target_source_role", rule_context)
        _validate_known_roles((target_source_role,), source_records, rule_context)
        package_terms = _require_string_tuple(rule, "package_terms", rule_context)
        rules.append(
            SupportingRecordTriggerRule(
                route_id=_require_string(rule, "route_id", rule_context),
                category=_require_string(rule, "category", rule_context),
                name=_require_string(rule, "name", rule_context),
                target_source_role=target_source_role,
                source_record_id=source_records[target_source_role].source_record_id,
                package_terms=package_terms,
                source_query=_require_string(rule, "source_query", rule_context),
                source_terms=_require_string_tuple(rule, "source_terms", rule_context),
                trigger_terms=_optional_string_tuple(
                    rule,
                    "trigger_terms",
                    rule_context,
                    default=package_terms,
                    allow_empty=False,
                ),
            )
        )
    _reject_duplicate(
        [rule.route_id for rule in rules],
        "route_id",
        f"{context}.supporting_record_trigger_rules",
    )
    return tuple(rules)


def _parse_known_forest_unit(raw_unit: object, index: int) -> KnownForestUnit:
    context = f"known_other_forest_units[{index}]"
    unit = _require_object(raw_unit, context)
    return KnownForestUnit(
        forest_unit_id=_require_string(unit, "forest_unit_id", context),
        names=_require_string_tuple(unit, "names", context),
    )


def _validate_known_roles(
    roles: tuple[str, ...],
    source_records: dict[str, ForestPlanSourceRecord],
    context: str,
) -> None:
    unknown_roles = [role for role in roles if role not in source_records]
    if unknown_roles:
        raise ValueError(f"{context} contains unknown source roles: {', '.join(unknown_roles)}")


def _require_object(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object.")
    return value


def _require_list(payload: dict[str, object], field: str, context: str) -> list[object]:
    value = payload.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{field} must be a list.")
    return value


def _optional_list(payload: dict[str, object], field: str, context: str) -> list[object]:
    if field not in payload:
        return []
    return _require_list(payload, field, context)


def _require_string(payload: dict[str, object], field: str, context: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field} must be a non-empty string.")
    return value


def _optional_string(
    payload: dict[str, object],
    field: str,
    context: str,
    *,
    default: str | None = None,
) -> str | None:
    value = payload.get(field, default)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field} must be a non-empty string when present.")
    return value


def _require_string_tuple(payload: dict[str, object], field: str, context: str) -> tuple[str, ...]:
    values = _require_list(payload, field, context)
    if not values:
        raise ValueError(f"{context}.{field} must not be empty.")
    return _string_tuple(values, field, context)


def _optional_string_tuple(
    payload: dict[str, object],
    field: str,
    context: str,
    *,
    default: tuple[str, ...] = (),
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if field not in payload:
        return default
    values = _require_list(payload, field, context)
    if not values and not allow_empty:
        raise ValueError(f"{context}.{field} must not be empty when present.")
    return _string_tuple(values, field, context)


def _string_tuple(values: list[object], field: str, context: str) -> tuple[str, ...]:
    invalid = [value for value in values if not isinstance(value, str) or not value.strip()]
    if invalid:
        raise ValueError(f"{context}.{field} must contain only non-empty strings.")
    return tuple(str(value) for value in values)


def _reject_duplicate(values: list[str], field: str, context: str) -> None:
    seen = set()
    duplicates = []
    for value in values:
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        raise ValueError(f"{context} contains duplicate {field} values: {', '.join(duplicates)}")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Forest-plan profile file must contain a JSON object: {path}")
    return payload
