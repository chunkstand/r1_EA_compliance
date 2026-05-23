from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.forest_plan_identity_reconciliation import (
    DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    DEFAULT_FOREST_PLAN_READINESS_PATH,
    FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
    build_region1_forest_plan_identity_reconciliation_registry,
    collect_inventory_manifest_source_record_ids,
    collect_readiness_source_record_ids,
    load_region1_forest_plan_identity_reconciliation_registry,
    rebind_region1_forest_plan_inventory_build_manifest,
    rebind_region1_forest_plan_readiness,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_REGISTRY = REPO_ROOT / "config" / "r1_forest_plan_identity_reconciliation_v1.json"
COMMITTED_INVENTORY_MANIFEST = REPO_ROOT / "config" / "r1_forest_plan_component_inventory_build_manifest.json"
COMMITTED_READINESS = REPO_ROOT / "config" / "region1_forest_plan_readiness_nepa_3d_v1.json"


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
                    "proposed_source_record_id,forest_unit_id,document_role,document_title,official_link,existing_source_record_id,draft_status,required_for",
                    "R1PLAN-unit-one-01,unit-one,planning_page,Planning page,https://example.com/planning,,catalog_confirmed,Planning page",
                    "R1PLAN-unit-one-02,unit-one,primary_land_management_plan,Plan PDF,https://example.com/plan.pdf,,catalog_confirmed,Plan PDF",
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
        assert registry["governed_catalog_rebound_source_record_count"] == 0
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


def test_build_identity_reconciliation_registry_honors_governed_existing_source_record_id() -> None:
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
                    "proposed_source_record_id,forest_unit_id,document_role,document_title,official_link,existing_source_record_id,draft_status,required_for",
                    "R1PLAN-unit-one-02,unit-one,primary_land_management_plan,Plan PDF,https://legacy.example.com/plan.pdf,FOR-002,source_delta_required,Plan PDF",
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
                            "effective_url": "https://canonical.example.com/plan.pdf",
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

        assert registry["exact_url_matched_source_record_count"] == 0
        assert registry["governed_catalog_rebound_source_record_count"] == 1
        assert registry["unresolved_source_record_count"] == 0
        assert registry["governed_catalog_rebound_source_records"] == [
            {
                "legacy_source_record_id": "R1PLAN-unit-one-02",
                "canonical_source_record_id": "FOR-002",
                "forest_unit_id": "unit-one",
                "document_role": "primary_land_management_plan",
                "document_title": "Plan PDF",
                "official_link": "https://legacy.example.com/plan.pdf",
                "canonical_title": "Canonical plan PDF",
                "catalog_source_partition": "active_review_corpus",
                "binding_basis": "existing_source_record_id",
                "referenced_by": [
                    "manifest:primary_land_management_plan",
                    "primary_plan_source_record_id",
                    "readiness:active_plan_source_record_id",
                    "readiness:primary_land_management_plan",
                ],
            }
        ]


def test_committed_registry_tracks_current_identity_gap() -> None:
    registry = _read_json(COMMITTED_REGISTRY)

    assert registry["schema_version"] == FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION
    assert registry["active_source_set_id"] == "source-set-3f7d4578cafb0704"
    assert registry["referenced_legacy_source_record_count"] == 99
    assert registry["exact_url_matched_source_record_count"] == 74
    assert registry["governed_catalog_rebound_source_record_count"] == 1
    assert registry["unresolved_source_record_count"] == 24
    assert registry["unresolved_status_counts"] == {
        "catalog_confirmed": 11,
        "source_delta_required": 13,
    }

    mapping = {
        row["legacy_source_record_id"]: row["canonical_source_record_id"]
        for row in registry["exact_url_matched_source_records"]
    }
    governed_mapping = {
        row["legacy_source_record_id"]: row["canonical_source_record_id"]
        for row in registry["governed_catalog_rebound_source_records"]
    }
    assert mapping["R1PLAN-beaverhead-deerlodge-nf-02"] == "FOR-002"
    assert mapping["R1PLAN-custer-gallatin-nf-02"] == "FOR-009"
    assert mapping["R1PLAN-lolo-nf-02"] == "FPS-298"
    assert mapping["R1PLAN-nez-perce-clearwater-nfs-06"] == "FPS-347"
    assert governed_mapping["R1PLAN-flathead-nf-02"] == "FINAL-FLAT-001"

    unresolved = {
        row["legacy_source_record_id"]: row["resolution_status"]
        for row in registry["unresolved_source_records"]
    }
    assert "R1PLAN-flathead-nf-02" not in unresolved
    assert unresolved["R1PLAN-custer-gallatin-nf-01"] == "catalog_confirmed"
    assert unresolved["R1PLAN-nez-perce-clearwater-nfs-04"] == "source_delta_required"


def test_committed_registry_still_covers_every_live_manifest_and_readiness_source_record_id() -> None:
    registry = _read_json(COMMITTED_REGISTRY)
    manifest = _read_json(DEFAULT_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH)
    readiness = _read_json(DEFAULT_FOREST_PLAN_READINESS_PATH)

    referenced_ids = collect_inventory_manifest_source_record_ids(
        manifest
    ) | collect_readiness_source_record_ids(readiness)
    registry_ids = {
        row["canonical_source_record_id"] for row in registry["exact_url_matched_source_records"]
    } | {
        row["canonical_source_record_id"]
        for row in registry["governed_catalog_rebound_source_records"]
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


def test_rebind_manifest_and_readiness_preserve_only_unresolved_legacy_source_record_ids() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest_path = tmp_path / "manifest.json"
        readiness_path = tmp_path / "readiness.json"
        registry_path = tmp_path / "registry.json"

        _write_json(
            manifest_path,
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
        _write_json(registry_path, _registry_payload())

        rebound_manifest = rebind_region1_forest_plan_inventory_build_manifest(
            manifest_path=manifest_path,
            registry_path=registry_path,
        )
        rebound_readiness = rebind_region1_forest_plan_readiness(
            readiness_path=readiness_path,
            registry_path=registry_path,
        )

        assert rebound_manifest["profile_rows"][0]["primary_plan_source_record_id"] == "FOR-002"
        assert rebound_manifest["profile_rows"][0]["build_source_record_ids_by_role"] == {
            "planning_page": ["R1PLAN-unit-one-01"],
            "primary_land_management_plan": ["FOR-002"],
        }
        assert rebound_manifest["profile_rows"][0]["identity_reconciliation"] == {
            "forest_unit_id": "unit-one",
            "status": "unresolved_blockers_present",
            "remaining_unresolved_source_record_count": 1,
            "remaining_unresolved_source_record_ids": ["R1PLAN-unit-one-01"],
            "remaining_unresolved_status_counts": {"catalog_confirmed": 1},
        }
        assert rebound_manifest["identity_reconciliation"] == {
            "registry_path": str(registry_path.resolve()),
            "registry_schema_version": FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
            "registry_active_source_set_id": "source-set-test",
            "exact_url_rebound_source_record_count": 1,
            "governed_catalog_rebound_source_record_count": 0,
            "remaining_unresolved_source_record_count": 1,
            "remaining_unresolved_source_record_ids": ["R1PLAN-unit-one-01"],
            "remaining_unresolved_status_counts": {"catalog_confirmed": 1},
        }

        assert rebound_readiness["profile_rows"][0]["active_plan_source_record_id"] == "FOR-002"
        assert rebound_readiness["profile_rows"][0]["source_requirements"] == [
            {"role": "planning_page", "source_record_id": "R1PLAN-unit-one-01"},
            {"role": "primary_land_management_plan", "source_record_id": "FOR-002"},
        ]
        assert rebound_readiness["profile_rows"][0]["identity_reconciliation"] == {
            "forest_unit_id": "unit-one",
            "status": "unresolved_blockers_present",
            "remaining_unresolved_source_record_count": 1,
            "remaining_unresolved_source_record_ids": ["R1PLAN-unit-one-01"],
            "remaining_unresolved_status_counts": {"catalog_confirmed": 1},
        }
        assert rebound_readiness["identity_reconciliation"] == {
            "registry_path": str(registry_path.resolve()),
            "registry_schema_version": FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
            "registry_active_source_set_id": "source-set-test",
            "exact_url_rebound_source_record_count": 1,
            "governed_catalog_rebound_source_record_count": 0,
            "remaining_unresolved_source_record_count": 1,
            "remaining_unresolved_source_record_ids": ["R1PLAN-unit-one-01"],
            "remaining_unresolved_status_counts": {"catalog_confirmed": 1},
        }


def test_committed_manifest_and_readiness_reduce_identity_mix_to_canonical_plus_unresolved() -> None:
    registry = load_region1_forest_plan_identity_reconciliation_registry(COMMITTED_REGISTRY)
    manifest = _read_json(COMMITTED_INVENTORY_MANIFEST)
    readiness = _read_json(COMMITTED_READINESS)
    expected_source_record_ids = {
        row["canonical_source_record_id"] for row in registry["exact_url_matched_source_records"]
    } | {
        row["canonical_source_record_id"]
        for row in registry["governed_catalog_rebound_source_records"]
    } | {row["legacy_source_record_id"] for row in registry["unresolved_source_records"]}
    unresolved_source_record_ids = {
        row["legacy_source_record_id"] for row in registry["unresolved_source_records"]
    }

    manifest_source_record_ids = collect_inventory_manifest_source_record_ids(manifest)
    readiness_source_record_ids = collect_readiness_source_record_ids(readiness)

    assert manifest_source_record_ids == expected_source_record_ids
    assert readiness_source_record_ids == expected_source_record_ids
    assert manifest["identity_reconciliation"] == {
        "registry_path": "config/r1_forest_plan_identity_reconciliation_v1.json",
        "registry_schema_version": FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
        "registry_active_source_set_id": "source-set-3f7d4578cafb0704",
        "exact_url_rebound_source_record_count": 74,
        "governed_catalog_rebound_source_record_count": 1,
        "remaining_unresolved_source_record_count": 24,
        "remaining_unresolved_source_record_ids": sorted(unresolved_source_record_ids),
        "remaining_unresolved_status_counts": {
            "catalog_confirmed": 11,
            "source_delta_required": 13,
        },
    }
    assert readiness["identity_reconciliation"] == manifest["identity_reconciliation"]
    assert not sorted(
        source_record_id
        for source_record_id in manifest_source_record_ids
        if source_record_id.startswith("R1PLAN-") and source_record_id not in unresolved_source_record_ids
    )
    assert not sorted(
        source_record_id
        for source_record_id in readiness_source_record_ids
        if source_record_id.startswith("R1PLAN-") and source_record_id not in unresolved_source_record_ids
    )


def test_committed_manifest_and_readiness_share_same_per_profile_unresolved_blockers() -> None:
    manifest = _read_json(COMMITTED_INVENTORY_MANIFEST)
    readiness = _read_json(COMMITTED_READINESS)
    manifest_rows = {row["forest_unit_id"]: row for row in manifest["profile_rows"]}
    readiness_rows = {row["forest_unit_id"]: row for row in readiness["profile_rows"]}

    assert set(manifest_rows) == set(readiness_rows)
    for forest_unit_id, manifest_row in manifest_rows.items():
        assert (
            manifest_row["identity_reconciliation"]
            == readiness_rows[forest_unit_id]["identity_reconciliation"]
        )

    assert manifest_rows["flathead-nf"]["identity_reconciliation"] == {
        "forest_unit_id": "flathead-nf",
        "status": "unresolved_blockers_present",
        "remaining_unresolved_source_record_count": 9,
        "remaining_unresolved_source_record_ids": [
          "R1PLAN-flathead-nf-01",
            "R1PLAN-flathead-nf-03",
            "R1PLAN-flathead-nf-04",
            "R1PLAN-flathead-nf-05",
            "R1PLAN-flathead-nf-06",
            "R1PLAN-flathead-nf-07",
            "R1PLAN-flathead-nf-10",
            "R1PLAN-flathead-nf-12",
            "R1PLAN-flathead-nf-16",
        ],
        "remaining_unresolved_status_counts": {
            "catalog_confirmed": 1,
            "source_delta_required": 8,
        },
    }
    assert manifest_rows["custer-gallatin-nf"]["identity_reconciliation"] == {
        "forest_unit_id": "custer-gallatin-nf",
        "status": "unresolved_blockers_present",
        "remaining_unresolved_source_record_count": 1,
        "remaining_unresolved_source_record_ids": ["R1PLAN-custer-gallatin-nf-01"],
        "remaining_unresolved_status_counts": {"catalog_confirmed": 1},
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _registry_payload() -> dict:
    return {
        "schema_version": FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
        "active_source_set_id": "source-set-test",
        "exact_url_matched_source_record_count": 1,
        "governed_catalog_rebound_source_record_count": 0,
        "unresolved_source_record_count": 1,
        "unresolved_status_counts": {"catalog_confirmed": 1},
        "exact_url_matched_source_records": [
            {
                "legacy_source_record_id": "R1PLAN-unit-one-02",
                "canonical_source_record_id": "FOR-002",
            }
        ],
        "governed_catalog_rebound_source_records": [],
        "unresolved_source_records": [
            {
                "legacy_source_record_id": "R1PLAN-unit-one-01",
                "resolution_status": "catalog_confirmed",
            }
        ],
    }
