from __future__ import annotations

from collections import Counter
from collections import defaultdict
import csv
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH = (
    REPO_ROOT / "config" / "r1_forest_plan_component_inventory_build_manifest.json"
)
DEFAULT_FOREST_PLAN_READINESS_PATH = REPO_ROOT / "config" / "region1_forest_plan_readiness_nepa_3d_v1.json"
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
    referenced_by = _collect_referenced_legacy_source_records(inventory_manifest, readiness)
    legacy_rows = _load_legacy_register(legacy_register_path)
    catalog_by_url = _index_catalog_urls(source_catalog_path)

    exact_url_matched_source_records: list[dict[str, Any]] = []
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
            exact_url_matched_source_records.append(
                {
                    **base_entry,
                    "canonical_source_record_id": catalog_row["source_record_id"],
                    "canonical_title": catalog_row.get("title", ""),
                    "catalog_source_partition": catalog_row.get("source_partition"),
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
        "unresolved_source_record_count": len(unresolved_source_records),
        "blocked_forest_unit_ids": [
            row["forest_unit_id"] for row in inventory_manifest["profile_rows"]
        ],
        "unresolved_status_counts": dict(sorted(unresolved_status_counts.items())),
        "unresolved_forest_unit_counts": dict(sorted(unresolved_forest_unit_counts.items())),
        "exact_url_matched_source_records": exact_url_matched_source_records,
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


def _load_legacy_register(legacy_register_path: Path) -> dict[str, dict[str, str]]:
    with legacy_register_path.open(newline="", encoding="utf-8") as handle:
        return {
            row["proposed_source_record_id"]: row
            for row in csv.DictReader(handle)
            if row.get("proposed_source_record_id")
        }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)
