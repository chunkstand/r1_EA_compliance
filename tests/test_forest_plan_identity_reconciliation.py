from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.forest_plan_identity_reconciliation import (
    DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    DEFAULT_FOREST_PLAN_READINESS_PATH,
    FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
    build_region1_forest_plan_identity_reconciliation_registry,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_REGISTRY = REPO_ROOT / "config" / "r1_forest_plan_identity_reconciliation_v1.json"


def test_build_identity_reconciliation_registry_with_exact_and_unresolved_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        inventory_manifest_path = tmp_path / "inventory_manifest.json"
        readiness_path = tmp_path / "readiness.json"
        legacy_register_path = tmp_path / "legacy_register.csv"
        source_catalog_path = tmp_path / "source_catalog.jsonl"
        source_set_manifest_path = tmp_path / "source_set_manifest.json"

        _write_json(
            inventory_manifest_path,
            {
                "profile_rows": [
                    {
                        "forest_unit_id": "unit-one",
                        "primary_plan_source_record_id": "R1PLAN-unit-one-02",
                        "build_source_record_ids_by_role": {
                            "planning_page": ["R1PLAN-unit-one-01"],
                            "primary_land_management_plan": ["R1PLAN-unit-one-02"],
                        },
                    }
                ]
            },
        )
        _write_json(
            readiness_path,
            {
                "profile_rows": [
                    {
                        "forest_unit_id": "unit-one",
                        "active_plan_source_record_id": "R1PLAN-unit-one-02",
                        "source_requirements": [
                            {"role": "planning_page", "source_record_id": "R1PLAN-unit-one-01"},
                            {
                                "role": "primary_land_management_plan",
                                "source_record_id": "R1PLAN-unit-one-02",
                            },
                        ],
                    }
                ]
            },
        )
        legacy_register_path.write_text(
            "\n".join(
                [
                    "proposed_source_record_id,forest_unit_id,document_role,document_title,official_link,draft_status,required_for",
                    "R1PLAN-unit-one-01,unit-one,planning_page,Planning page,https://example.com/planning,catalog_confirmed,Planning page",
                    "R1PLAN-unit-one-02,unit-one,primary_land_management_plan,Plan PDF,https://example.com/plan.pdf,catalog_confirmed,Plan PDF",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        source_catalog_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "source_record_id": "FOR-002",
                            "title": "Canonical plan PDF",
                            "source_partition": "active_review_corpus",
                            "effective_url": "https://example.com/plan.pdf",
                        }
                    )
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        _write_json(source_set_manifest_path, {"source_set_id": "source-set-test"})

        registry = build_region1_forest_plan_identity_reconciliation_registry(
            inventory_manifest_path=inventory_manifest_path,
            readiness_path=readiness_path,
            legacy_register_path=legacy_register_path,
            source_catalog_path=source_catalog_path,
            source_set_manifest_path=source_set_manifest_path,
        )

        assert registry["schema_version"] == FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION
        assert registry["active_source_set_id"] == "source-set-test"
        assert registry["referenced_legacy_source_record_count"] == 2
        assert registry["exact_url_matched_source_record_count"] == 1
        assert registry["unresolved_source_record_count"] == 1
        assert registry["exact_url_matched_source_records"] == [
            {
                "legacy_source_record_id": "R1PLAN-unit-one-02",
                "canonical_source_record_id": "FOR-002",
                "forest_unit_id": "unit-one",
                "document_role": "primary_land_management_plan",
                "document_title": "Plan PDF",
                "official_link": "https://example.com/plan.pdf",
                "canonical_title": "Canonical plan PDF",
                "catalog_source_partition": "active_review_corpus",
                "referenced_by": [
                    "manifest:primary_land_management_plan",
                    "primary_plan_source_record_id",
                    "readiness:active_plan_source_record_id",
                    "readiness:primary_land_management_plan",
                ],
            }
        ]
        assert registry["unresolved_source_records"] == [
            {
                "legacy_source_record_id": "R1PLAN-unit-one-01",
                "forest_unit_id": "unit-one",
                "document_role": "planning_page",
                "document_title": "Planning page",
                "official_link": "https://example.com/planning",
                "referenced_by": [
                    "manifest:planning_page",
                    "readiness:planning_page",
                ],
                "resolution_status": "catalog_confirmed",
                "matching_canonical_source_record_ids": [],
            }
        ]


def test_committed_registry_tracks_current_identity_gap() -> None:
    registry = _read_json(COMMITTED_REGISTRY)

    assert registry["schema_version"] == FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION
    assert registry["active_source_set_id"] == "source-set-9e7d85759951c279"
    assert registry["referenced_legacy_source_record_count"] == 99
    assert registry["exact_url_matched_source_record_count"] == 74
    assert registry["unresolved_source_record_count"] == 25
    assert registry["unresolved_status_counts"] == {
        "catalog_confirmed": 11,
        "source_delta_required": 14,
    }

    mapping = {
        row["legacy_source_record_id"]: row["canonical_source_record_id"]
        for row in registry["exact_url_matched_source_records"]
    }
    assert mapping["R1PLAN-beaverhead-deerlodge-nf-02"] == "FOR-002"
    assert mapping["R1PLAN-custer-gallatin-nf-02"] == "FOR-009"
    assert mapping["R1PLAN-lolo-nf-02"] == "FPS-298"
    assert mapping["R1PLAN-nez-perce-clearwater-nfs-06"] == "FPS-347"

    unresolved = {
        row["legacy_source_record_id"]: row["resolution_status"]
        for row in registry["unresolved_source_records"]
    }
    assert unresolved["R1PLAN-flathead-nf-02"] == "source_delta_required"
    assert unresolved["R1PLAN-custer-gallatin-nf-01"] == "catalog_confirmed"
    assert unresolved["R1PLAN-nez-perce-clearwater-nfs-04"] == "source_delta_required"


def test_committed_registry_covers_every_legacy_source_record_referenced_by_live_manifests() -> None:
    registry = _read_json(COMMITTED_REGISTRY)
    manifest = _read_json(DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH)
    readiness = _read_json(DEFAULT_FOREST_PLAN_READINESS_PATH)

    referenced_ids = set()
    for profile_row in manifest["profile_rows"]:
        referenced_ids.add(profile_row["primary_plan_source_record_id"])
        for source_record_ids in profile_row.get("build_source_record_ids_by_role", {}).values():
            referenced_ids.update(source_record_ids)
    for profile_row in readiness["profile_rows"]:
        referenced_ids.add(profile_row["active_plan_source_record_id"])
        for requirement in profile_row.get("source_requirements", []):
            source_record_id = requirement.get("source_record_id")
            if source_record_id:
                referenced_ids.add(source_record_id)
            referenced_ids.update(requirement.get("source_record_ids", []))

    registry_ids = {
        row["legacy_source_record_id"] for row in registry["exact_url_matched_source_records"]
    } | {row["legacy_source_record_id"] for row in registry["unresolved_source_records"]}

    assert registry_ids == referenced_ids
    assert registry["blocked_forest_unit_ids"] == [
        "custer-gallatin-nf",
        "beaverhead-deerlodge-nf",
        "bitterroot-nf",
        "dakota-prairie-grasslands",
        "flathead-nf",
        "helena-lewis-and-clark-nf",
        "idaho-panhandle-nfs",
        "kootenai-nf",
        "lolo-nf",
        "nez-perce-clearwater-nfs",
    ]
    assert all(
        not row["canonical_source_record_id"].startswith("R1PLAN-")
        for row in registry["exact_url_matched_source_records"]
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
