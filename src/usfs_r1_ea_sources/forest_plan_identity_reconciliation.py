from __future__ import annotations

from collections import Counter
from collections import defaultdict
from copy import deepcopy
import csv
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH = (
    REPO_ROOT / "config" / "r1_forest_plan_component_inventory_build_manifest.json"
)
DEFAULT_FOREST_PLAN_READINESS_PATH = REPO_ROOT / "config" / "region1_forest_plan_readiness_nepa_3d_v1.json"
DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_REGISTRY_PATH = (
    REPO_ROOT / "config" / "r1_forest_plan_identity_reconciliation_v1.json"
)
DEFAULT_FOREST_PLAN_LEGACY_REGISTER_PATH = REPO_ROOT / "config" / "r1_forest_plan_document_register_draft.csv"
DEFAULT_ACTIVE_SOURCE_CATALOG_PATH = REPO_ROOT / "source_library" / "catalog" / "source_catalog.jsonl"
DEFAULT_ACTIVE_SOURCE_SET_MANIFEST_PATH = REPO_ROOT / "source_library" / "catalog" / "source_set_manifest.json"
FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION = (
    "region1-forest-plan-identity-reconciliation-registry-v1"
)


def build_region1_forest_plan_identity_reconciliation_registry(
    *,
    inventory_manifest_path: Path = DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    readiness_path: Path = DEFAULT_FOREST_PLAN_READINESS_PATH,
    legacy_register_path: Path = DEFAULT_FOREST_PLAN_LEGACY_REGISTER_PATH,
    source_catalog_path: Path = DEFAULT_ACTIVE_SOURCE_CATALOG_PATH,
    source_set_manifest_path: Path = DEFAULT_ACTIVE_SOURCE_SET_MANIFEST_PATH,
) -> dict[str, Any]:
    inventory_manifest = _read_json(inventory_manifest_path)
    readiness = _read_json(readiness_path)
    source_set_manifest = _read_json(source_set_manifest_path)
    legacy_rows = _load_legacy_register(legacy_register_path)
    catalog_by_url = _index_catalog_urls(source_catalog_path)
    catalog_by_source_record_id = _index_catalog_source_record_ids(source_catalog_path)
    referenced_by = _resolve_referenced_legacy_source_records(
        referenced_by_current_source_record_id=_collect_referenced_legacy_source_records(
            inventory_manifest,
            readiness,
        ),
        legacy_rows=legacy_rows,
        catalog_by_source_record_id=catalog_by_source_record_id,
    )

    exact_url_matched_source_records: list[dict[str, Any]] = []
    governed_catalog_rebound_source_records: list[dict[str, Any]] = []
    unresolved_source_records: list[dict[str, Any]] = []
    missing_legacy_source_record_ids: list[str] = []

    for legacy_source_record_id in sorted(referenced_by):
        legacy_row = legacy_rows.get(legacy_source_record_id)
        if legacy_row is None:
            missing_legacy_source_record_ids.append(legacy_source_record_id)
            continue
        official_link = legacy_row["official_link"]
        catalog_matches = catalog_by_url.get(official_link, [])
        base_entry = {
            "legacy_source_record_id": legacy_source_record_id,
            "forest_unit_id": legacy_row["forest_unit_id"],
            "document_role": legacy_row["document_role"],
            "document_title": legacy_row["document_title"],
            "official_link": official_link,
            "referenced_by": sorted(referenced_by[legacy_source_record_id]),
        }

        if len(catalog_matches) == 1:
            catalog_row = catalog_matches[0]
            canonical_source_record_id = str(catalog_row.get("source_record_id") or "").strip()
            if (
                canonical_source_record_id == legacy_source_record_id
                and legacy_source_record_id.startswith("R1PLAN-")
            ):
                unresolved_source_records.append(
                    {
                        **base_entry,
                        "resolution_status": legacy_row["draft_status"] or "catalog_confirmed",
                        "matching_canonical_source_record_ids": [canonical_source_record_id],
                    }
                )
                continue
            exact_url_matched_source_records.append(
                {
                    **base_entry,
                    "canonical_source_record_id": canonical_source_record_id,
                    "canonical_title": catalog_row.get("title", ""),
                    "catalog_source_partition": catalog_row.get("source_partition"),
                }
            )
            continue

        existing_source_record_id = legacy_row.get("existing_source_record_id", "").strip()
        if existing_source_record_id and not existing_source_record_id.startswith("R1PLAN-"):
            catalog_row = catalog_by_source_record_id.get(existing_source_record_id)
            if catalog_row is None:
                raise ValueError(
                    "Legacy forest-plan register existing_source_record_id is not present in the "
                    f"active catalog: {legacy_source_record_id} -> {existing_source_record_id}"
                )
            governed_catalog_rebound_source_records.append(
                {
                    **base_entry,
                    "canonical_source_record_id": existing_source_record_id,
                    "canonical_title": catalog_row.get("title", ""),
                    "catalog_source_partition": catalog_row.get("source_partition"),
                    "binding_basis": "existing_source_record_id",
                }
            )
            continue

        if len(catalog_matches) > 1:
            resolution_status = "ambiguous_exact_url_match"
            matching_canonical_source_record_ids = [
                catalog_row["source_record_id"] for catalog_row in catalog_matches
            ]
        else:
            resolution_status = legacy_row["draft_status"] or "unmatched"
            matching_canonical_source_record_ids = []

        unresolved_source_records.append(
            {
                **base_entry,
                "resolution_status": resolution_status,
                "matching_canonical_source_record_ids": matching_canonical_source_record_ids,
            }
        )

    if missing_legacy_source_record_ids:
        raise ValueError(
            "Legacy forest-plan register is missing referenced source_record_id values: "
            + ", ".join(missing_legacy_source_record_ids)
        )

    unresolved_status_counts = Counter(
        entry["resolution_status"] for entry in unresolved_source_records
    )
    unresolved_forest_unit_counts = Counter(
        entry["forest_unit_id"] for entry in unresolved_source_records
    )

    return {
        "schema_version": FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
        "contract_id": "region1-forest-plan-identity-reconciliation",
        "version": "1.0.0",
        "active_source_set_id": source_set_manifest["source_set_id"],
        "inventory_manifest_path": _repo_relative(inventory_manifest_path),
        "readiness_path": _repo_relative(readiness_path),
        "legacy_register_path": _repo_relative(legacy_register_path),
        "source_catalog_path": _repo_relative(source_catalog_path),
        "referenced_legacy_source_record_count": len(referenced_by),
        "exact_url_matched_source_record_count": len(exact_url_matched_source_records),
        "governed_catalog_rebound_source_record_count": len(governed_catalog_rebound_source_records),
        "unresolved_source_record_count": len(unresolved_source_records),
        "blocked_forest_unit_ids": [
            row["forest_unit_id"] for row in inventory_manifest["profile_rows"]
        ],
        "unresolved_status_counts": dict(sorted(unresolved_status_counts.items())),
        "unresolved_forest_unit_counts": dict(sorted(unresolved_forest_unit_counts.items())),
        "exact_url_matched_source_records": exact_url_matched_source_records,
        "governed_catalog_rebound_source_records": governed_catalog_rebound_source_records,
        "unresolved_source_records": unresolved_source_records,
    }


def write_region1_forest_plan_identity_reconciliation_registry(
    output_path: Path,
    *,
    inventory_manifest_path: Path = DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    readiness_path: Path = DEFAULT_FOREST_PLAN_READINESS_PATH,
    legacy_register_path: Path = DEFAULT_FOREST_PLAN_LEGACY_REGISTER_PATH,
    source_catalog_path: Path = DEFAULT_ACTIVE_SOURCE_CATALOG_PATH,
    source_set_manifest_path: Path = DEFAULT_ACTIVE_SOURCE_SET_MANIFEST_PATH,
) -> dict[str, Any]:
    registry = build_region1_forest_plan_identity_reconciliation_registry(
        inventory_manifest_path=inventory_manifest_path,
        readiness_path=readiness_path,
        legacy_register_path=legacy_register_path,
        source_catalog_path=source_catalog_path,
        source_set_manifest_path=source_set_manifest_path,
    )
    output_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def load_region1_forest_plan_identity_reconciliation_registry(
    path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_REGISTRY_PATH,
) -> dict[str, Any]:
    registry = _read_json(path)
    schema_version = registry.get("schema_version")
    if schema_version != FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan identity reconciliation schema_version: "
            f"{schema_version!r}; expected "
            f"{FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION!r}"
        )
    return registry


def aliased_region1_forest_plan_source_record_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
    registry_path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_REGISTRY_PATH,
) -> list[str]:
    values = _deduped_source_record_ids([source_record_id, *(source_record_ids or [])])
    if not values:
        return []
    registry = load_region1_forest_plan_identity_reconciliation_registry(registry_path)
    resolved_matches, _, canonical_source_record_ids = _registry_indexes(registry)
    legacy_by_canonical: dict[str, list[str]] = defaultdict(list)
    for legacy_source_record_id, canonical_source_record_id in resolved_matches.items():
        legacy_by_canonical[canonical_source_record_id].append(legacy_source_record_id)

    aliased_source_record_ids: list[str] = []
    for value in values:
        aliased_source_record_ids.append(value)
        if value in resolved_matches:
            aliased_source_record_ids.append(resolved_matches[value])
        if value in canonical_source_record_ids:
            aliased_source_record_ids.extend(sorted(legacy_by_canonical.get(value, ())))
    return _deduped_source_record_ids(aliased_source_record_ids)


def rebind_region1_forest_plan_inventory_build_manifest(
    *,
    manifest_path: Path = DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    registry_path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_REGISTRY_PATH,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    registry = load_region1_forest_plan_identity_reconciliation_registry(registry_path)
    exact_matches, unresolved_source_records, canonical_source_record_ids = _registry_indexes(registry)
    rebound_manifest = deepcopy(manifest)
    expected_source_record_ids = canonical_source_record_ids | set(unresolved_source_records)

    for profile_row in rebound_manifest["profile_rows"]:
        profile_row["primary_plan_source_record_id"] = _rebind_source_record_id(
            profile_row["primary_plan_source_record_id"],
            exact_matches=exact_matches,
            canonical_source_record_ids=canonical_source_record_ids,
        )
        build_source_record_ids_by_role = profile_row.get("build_source_record_ids_by_role", {})
        for role, source_record_ids in build_source_record_ids_by_role.items():
            build_source_record_ids_by_role[role] = [
                _rebind_source_record_id(
                    source_record_id,
                    exact_matches=exact_matches,
                    canonical_source_record_ids=canonical_source_record_ids,
                )
                for source_record_id in source_record_ids
            ]
        profile_row["identity_reconciliation"] = _profile_identity_reconciliation_metadata(
            forest_unit_id=profile_row["forest_unit_id"],
            source_record_ids=_collect_manifest_profile_row_source_record_ids(profile_row),
            unresolved_source_records=unresolved_source_records,
        )

    final_source_record_ids = collect_inventory_manifest_source_record_ids(rebound_manifest)
    _validate_rebound_source_record_ids(
        current_source_record_ids=final_source_record_ids,
        expected_source_record_ids=expected_source_record_ids,
        config_label="inventory build manifest",
        unresolved_source_records=unresolved_source_records,
    )
    rebound_manifest["identity_reconciliation"] = _config_identity_reconciliation_metadata(
        registry=registry,
        registry_path=registry_path,
        current_source_record_ids=final_source_record_ids,
        unresolved_source_records=unresolved_source_records,
    )
    return rebound_manifest


def rebind_region1_forest_plan_readiness(
    *,
    readiness_path: Path = DEFAULT_FOREST_PLAN_READINESS_PATH,
    registry_path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_REGISTRY_PATH,
) -> dict[str, Any]:
    readiness = _read_json(readiness_path)
    registry = load_region1_forest_plan_identity_reconciliation_registry(registry_path)
    exact_matches, unresolved_source_records, canonical_source_record_ids = _registry_indexes(registry)
    rebound_readiness = deepcopy(readiness)
    expected_source_record_ids = canonical_source_record_ids | set(unresolved_source_records)

    for profile_row in rebound_readiness["profile_rows"]:
        profile_row["active_plan_source_record_id"] = _rebind_source_record_id(
            profile_row["active_plan_source_record_id"],
            exact_matches=exact_matches,
            canonical_source_record_ids=canonical_source_record_ids,
        )
        for requirement in profile_row.get("source_requirements", []):
            source_record_id = requirement.get("source_record_id")
            if source_record_id:
                requirement["source_record_id"] = _rebind_source_record_id(
                    source_record_id,
                    exact_matches=exact_matches,
                    canonical_source_record_ids=canonical_source_record_ids,
                )
            source_record_ids = requirement.get("source_record_ids")
            if source_record_ids:
                requirement["source_record_ids"] = [
                    _rebind_source_record_id(
                        value,
                        exact_matches=exact_matches,
                        canonical_source_record_ids=canonical_source_record_ids,
                    )
                    for value in source_record_ids
                ]
        profile_row["identity_reconciliation"] = _profile_identity_reconciliation_metadata(
            forest_unit_id=profile_row["forest_unit_id"],
            source_record_ids=_collect_readiness_profile_row_source_record_ids(profile_row),
            unresolved_source_records=unresolved_source_records,
        )

    final_source_record_ids = collect_readiness_source_record_ids(rebound_readiness)
    _validate_rebound_source_record_ids(
        current_source_record_ids=final_source_record_ids,
        expected_source_record_ids=expected_source_record_ids,
        config_label="readiness matrix",
        unresolved_source_records=unresolved_source_records,
    )
    rebound_readiness["identity_reconciliation"] = _config_identity_reconciliation_metadata(
        registry=registry,
        registry_path=registry_path,
        current_source_record_ids=final_source_record_ids,
        unresolved_source_records=unresolved_source_records,
    )
    return rebound_readiness


def collect_inventory_manifest_source_record_ids(manifest: dict[str, Any]) -> set[str]:
    source_record_ids = set()
    for profile_row in manifest["profile_rows"]:
        source_record_ids.update(_collect_manifest_profile_row_source_record_ids(profile_row))
    return source_record_ids


def collect_readiness_source_record_ids(readiness: dict[str, Any]) -> set[str]:
    source_record_ids = set()
    for profile_row in readiness["profile_rows"]:
        source_record_ids.update(_collect_readiness_profile_row_source_record_ids(profile_row))
    return source_record_ids


def _collect_referenced_legacy_source_records(
    inventory_manifest: dict[str, Any], readiness: dict[str, Any]
) -> dict[str, set[str]]:
    referenced_by: dict[str, set[str]] = defaultdict(set)

    for profile_row in inventory_manifest["profile_rows"]:
        legacy_source_record_id = profile_row["primary_plan_source_record_id"]
        referenced_by[legacy_source_record_id].add("primary_plan_source_record_id")
        for role, source_record_ids in profile_row.get("build_source_record_ids_by_role", {}).items():
            for source_record_id in source_record_ids:
                referenced_by[source_record_id].add(f"manifest:{role}")

    for profile_row in readiness["profile_rows"]:
        active_plan_source_record_id = profile_row["active_plan_source_record_id"]
        referenced_by[active_plan_source_record_id].add("readiness:active_plan_source_record_id")
        for requirement in profile_row.get("source_requirements", []):
            role = requirement.get("role", "unknown")
            source_record_id = requirement.get("source_record_id")
            if source_record_id:
                referenced_by[source_record_id].add(f"readiness:{role}")
            for multi_source_record_id in requirement.get("source_record_ids", []):
                referenced_by[multi_source_record_id].add(f"readiness:{role}")

    return referenced_by


def _index_catalog_urls(source_catalog_path: Path) -> dict[str, list[dict[str, Any]]]:
    catalog_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with source_catalog_path.open(encoding="utf-8") as handle:
        for line in handle:
            catalog_row = json.loads(line)
            for url_field in ("source_url", "effective_url", "resolved_url"):
                url = catalog_row.get(url_field)
                if url:
                    catalog_by_url[url].append(catalog_row)
    return catalog_by_url


def _index_catalog_source_record_ids(source_catalog_path: Path) -> dict[str, dict[str, Any]]:
    catalog_by_source_record_id: dict[str, dict[str, Any]] = {}
    with source_catalog_path.open(encoding="utf-8") as handle:
        for line in handle:
            catalog_row = json.loads(line)
            source_record_id = str(catalog_row.get("source_record_id") or "").strip()
            if source_record_id:
                catalog_by_source_record_id[source_record_id] = catalog_row
    return catalog_by_source_record_id


def _load_legacy_register(legacy_register_path: Path) -> dict[str, dict[str, str]]:
    with legacy_register_path.open(newline="", encoding="utf-8") as handle:
        return {
            row["proposed_source_record_id"]: row
            for row in csv.DictReader(handle)
            if row.get("proposed_source_record_id")
        }


def _resolve_referenced_legacy_source_records(
    *,
    referenced_by_current_source_record_id: dict[str, set[str]],
    legacy_rows: dict[str, dict[str, str]],
    catalog_by_source_record_id: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    referenced_by: dict[str, set[str]] = defaultdict(set)
    unresolved_current_source_record_ids: list[str] = []

    for current_source_record_id, references in referenced_by_current_source_record_id.items():
        if current_source_record_id in legacy_rows:
            referenced_by[current_source_record_id].update(references)
            continue

        catalog_row = catalog_by_source_record_id.get(current_source_record_id)
        if catalog_row is None:
            unresolved_current_source_record_ids.append(current_source_record_id)
            continue

        candidate_legacy_source_record_ids = sorted(
            legacy_source_record_id
            for legacy_source_record_id, legacy_row in legacy_rows.items()
            if (
                legacy_row.get("existing_source_record_id", "").strip() == current_source_record_id
                or legacy_row.get("official_link", "").strip()
                in _catalog_row_urls(catalog_row)
            )
        )
        if not candidate_legacy_source_record_ids:
            unresolved_current_source_record_ids.append(current_source_record_id)
            continue
        if len(candidate_legacy_source_record_ids) > 1:
            referenced_roles = {
                reference.split(":", 1)[1]
                for reference in references
                if ":" in reference
            }
            role_matched_candidate_legacy_source_record_ids = [
                legacy_source_record_id
                for legacy_source_record_id in candidate_legacy_source_record_ids
                if legacy_rows[legacy_source_record_id].get("document_role", "").strip()
                in referenced_roles
            ]
            if len(role_matched_candidate_legacy_source_record_ids) == 1:
                candidate_legacy_source_record_ids = role_matched_candidate_legacy_source_record_ids
        if len(candidate_legacy_source_record_ids) > 1:
            raise ValueError(
                "Current canonical forest-plan source_record_id resolves to multiple legacy rows: "
                f"{current_source_record_id} -> {', '.join(candidate_legacy_source_record_ids)}"
            )
        referenced_by[candidate_legacy_source_record_ids[0]].update(references)

    if unresolved_current_source_record_ids:
        raise ValueError(
            "Unable to resolve current forest-plan source_record_id values back to legacy register "
            "rows: " + ", ".join(sorted(unresolved_current_source_record_ids))
        )
    return referenced_by


def _catalog_row_urls(catalog_row: dict[str, Any]) -> set[str]:
    return {
        str(catalog_row.get(field) or "").strip()
        for field in ("source_url", "effective_url", "resolved_url")
        if str(catalog_row.get(field) or "").strip()
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _deduped_source_record_ids(values: list[object]) -> list[str]:
    deduped: list[str] = []
    seen = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _registry_indexes(
    registry: dict[str, Any],
) -> tuple[dict[str, str], dict[str, dict[str, Any]], set[str]]:
    exact_matches = {
        row["legacy_source_record_id"]: row["canonical_source_record_id"]
        for row in registry["exact_url_matched_source_records"]
    }
    governed_matches = {
        row["legacy_source_record_id"]: row["canonical_source_record_id"]
        for row in registry.get("governed_catalog_rebound_source_records", [])
    }
    unresolved_source_records = {
        row["legacy_source_record_id"]: row for row in registry["unresolved_source_records"]
    }
    resolved_matches = {**exact_matches, **governed_matches}
    overlapping_ids = sorted(set(resolved_matches) & set(unresolved_source_records))
    if overlapping_ids:
        raise ValueError(
            "Identity reconciliation registry has overlapping resolved and unresolved source_record_ids: "
            + ", ".join(overlapping_ids)
        )
    canonical_source_record_ids = set(resolved_matches.values())
    if len(canonical_source_record_ids) != len(resolved_matches):
        raise ValueError(
            "Identity reconciliation registry must map each resolved legacy source_record_id to a unique "
            "canonical source_record_id."
        )
    return resolved_matches, unresolved_source_records, canonical_source_record_ids


def _rebind_source_record_id(
    source_record_id: str,
    *,
    exact_matches: dict[str, str],
    canonical_source_record_ids: set[str],
) -> str:
    if source_record_id in exact_matches:
        return exact_matches[source_record_id]
    if source_record_id in canonical_source_record_ids:
        return source_record_id
    return source_record_id


def _profile_identity_reconciliation_metadata(
    *,
    forest_unit_id: str,
    source_record_ids: set[str],
    unresolved_source_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    unresolved_rows = sorted(
        (
            unresolved_source_records[source_record_id]
            for source_record_id in source_record_ids
            if source_record_id in unresolved_source_records
        ),
        key=lambda row: row["legacy_source_record_id"],
    )
    unresolved_status_counts = Counter(row["resolution_status"] for row in unresolved_rows)
    return {
        "forest_unit_id": forest_unit_id,
        "status": (
            "unresolved_blockers_present" if unresolved_rows else "exact_url_rebound_complete"
        ),
        "remaining_unresolved_source_record_count": len(unresolved_rows),
        "remaining_unresolved_source_record_ids": [
            row["legacy_source_record_id"] for row in unresolved_rows
        ],
        "remaining_unresolved_status_counts": dict(sorted(unresolved_status_counts.items())),
    }


def _config_identity_reconciliation_metadata(
    *,
    registry: dict[str, Any],
    registry_path: Path,
    current_source_record_ids: set[str],
    unresolved_source_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    remaining_unresolved_source_record_ids = sorted(
        source_record_id
        for source_record_id in current_source_record_ids
        if source_record_id in unresolved_source_records
    )
    return {
        "registry_path": _repo_relative(registry_path),
        "registry_schema_version": registry["schema_version"],
        "registry_active_source_set_id": registry["active_source_set_id"],
        "exact_url_rebound_source_record_count": registry["exact_url_matched_source_record_count"],
        "governed_catalog_rebound_source_record_count": registry.get(
            "governed_catalog_rebound_source_record_count",
            0,
        ),
        "remaining_unresolved_source_record_count": len(remaining_unresolved_source_record_ids),
        "remaining_unresolved_source_record_ids": remaining_unresolved_source_record_ids,
        "remaining_unresolved_status_counts": dict(registry["unresolved_status_counts"]),
    }


def _validate_rebound_source_record_ids(
    *,
    current_source_record_ids: set[str],
    expected_source_record_ids: set[str],
    config_label: str,
    unresolved_source_records: dict[str, dict[str, Any]],
) -> None:
    unexpected_source_record_ids = sorted(current_source_record_ids - expected_source_record_ids)
    missing_source_record_ids = sorted(expected_source_record_ids - current_source_record_ids)
    if unexpected_source_record_ids or missing_source_record_ids:
        parts = []
        if unexpected_source_record_ids:
            parts.append("unexpected source_record_ids: " + ", ".join(unexpected_source_record_ids))
        if missing_source_record_ids:
            parts.append("missing source_record_ids: " + ", ".join(missing_source_record_ids))
        raise ValueError(f"{config_label} identity rebound mismatch: " + "; ".join(parts))
    resolved_legacy_source_record_ids = sorted(
        source_record_id
        for source_record_id in current_source_record_ids
        if source_record_id.startswith("R1PLAN-") and source_record_id not in unresolved_source_records
    )
    if resolved_legacy_source_record_ids:
        raise ValueError(
            f"{config_label} still contains reboundable legacy source_record_ids: "
            + ", ".join(resolved_legacy_source_record_ids)
        )


def _collect_manifest_profile_row_source_record_ids(profile_row: dict[str, Any]) -> set[str]:
    source_record_ids = {profile_row["primary_plan_source_record_id"]}
    for role_source_record_ids in profile_row.get("build_source_record_ids_by_role", {}).values():
        source_record_ids.update(role_source_record_ids)
    return source_record_ids


def _collect_readiness_profile_row_source_record_ids(profile_row: dict[str, Any]) -> set[str]:
    source_record_ids = {profile_row["active_plan_source_record_id"]}
    for requirement in profile_row.get("source_requirements", []):
        source_record_id = requirement.get("source_record_id")
        if source_record_id:
            source_record_ids.add(source_record_id)
        source_record_ids.update(requirement.get("source_record_ids", []))
    return source_record_ids


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)
