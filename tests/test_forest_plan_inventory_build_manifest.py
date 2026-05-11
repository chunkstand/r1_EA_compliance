from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile
import unittest

from usfs_r1_ea_sources.forest_plan_inventory_build_manifest import (
    DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
    REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_SCHEMA_VERSION,
    load_region1_forest_plan_inventory_build_manifest,
)


class Region1ForestPlanInventoryBuildManifestTests(unittest.TestCase):
    def test_default_manifest_path_is_repo_absolute(self) -> None:
        self.assertTrue(DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH.is_absolute())
        self.assertTrue(DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH.exists())

    def test_loads_default_manifest_from_non_repo_cwd(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                manifest = load_region1_forest_plan_inventory_build_manifest()
            finally:
                os.chdir(original_cwd)

        self.assertEqual(manifest.get("custer-gallatin-nf").plan_version, "2022")
        self.assertEqual(len(manifest.profile_rows), 10)

    def test_loads_default_manifest_as_data(self) -> None:
        manifest = load_region1_forest_plan_inventory_build_manifest()

        self.assertEqual(
            manifest.schema_version,
            REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_SCHEMA_VERSION,
        )
        self.assertEqual(
            manifest.source_set_reference("active_full_canonical").source_set_id,
            "source-set-5e65d845ce77e1a0",
        )
        dakota = manifest.get("dakota-prairie-grasslands")
        self.assertEqual(dakota.primary_plan_source_record_id, "R1PLAN-dakota-prairie-grasslands-03")
        self.assertEqual(
            dakota.build_source_record_ids_by_role["primary_land_resource_management_plan_part"],
            (
                "R1PLAN-dakota-prairie-grasslands-03",
                "R1PLAN-dakota-prairie-grasslands-04",
                "R1PLAN-dakota-prairie-grasslands-05",
                "R1PLAN-dakota-prairie-grasslands-06",
                "R1PLAN-dakota-prairie-grasslands-07",
            ),
        )
        nez_perce = manifest.get("nez-perce-clearwater-nfs")
        self.assertEqual(nez_perce.primary_plan_source_record_id, "R1PLAN-nez-perce-clearwater-nfs-06")
        self.assertIn(
            "R1PLAN-nez-perce-clearwater-nfs-02",
            nez_perce.source_record_ids,
        )

    def test_rejects_missing_readiness_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            readiness_path = Path(tmp) / "readiness.json"
            payload = _manifest_payload()
            payload["profile_rows"] = payload["profile_rows"][:1]
            _write_json(manifest_path, payload)
            _write_json(readiness_path, _readiness_payload())

            with self.assertRaisesRegex(ValueError, "missing coverage for unit-two"):
                load_region1_forest_plan_inventory_build_manifest(
                    manifest_path,
                    readiness_path=readiness_path,
                )

    def test_rejects_duplicate_forest_unit_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            readiness_path = Path(tmp) / "readiness.json"
            payload = _manifest_payload()
            payload["profile_rows"].append(dict(payload["profile_rows"][0]))
            _write_json(manifest_path, payload)
            _write_json(readiness_path, _readiness_payload())

            with self.assertRaisesRegex(ValueError, "Duplicate forest_unit_id values"):
                load_region1_forest_plan_inventory_build_manifest(
                    manifest_path,
                    readiness_path=readiness_path,
                )

    def test_rejects_unsupported_source_set_reference_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            readiness_path = Path(tmp) / "readiness.json"
            payload = _manifest_payload()
            payload["source_set_references"][0]["reference_type"] = "catalog_alias"
            _write_json(manifest_path, payload)
            _write_json(readiness_path, _readiness_payload())

            with self.assertRaisesRegex(ValueError, "reference_type must be one of"):
                load_region1_forest_plan_inventory_build_manifest(
                    manifest_path,
                    readiness_path=readiness_path,
                )

    def test_rejects_unknown_source_set_reference_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            readiness_path = Path(tmp) / "readiness.json"
            payload = _manifest_payload()
            payload["profile_rows"][0]["source_set_reference_id"] = "missing"
            _write_json(manifest_path, payload)
            _write_json(readiness_path, _readiness_payload())

            with self.assertRaisesRegex(ValueError, "references unknown source_set_reference_id"):
                load_region1_forest_plan_inventory_build_manifest(
                    manifest_path,
                    readiness_path=readiness_path,
                )

    def test_rejects_profile_missing_readiness_source_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            readiness_path = Path(tmp) / "readiness.json"
            payload = _manifest_payload()
            del payload["profile_rows"][0]["build_source_record_ids_by_role"]["planning_page"]
            _write_json(manifest_path, payload)
            _write_json(readiness_path, _readiness_payload())

            with self.assertRaisesRegex(ValueError, "must include readiness source_record_ids"):
                load_region1_forest_plan_inventory_build_manifest(
                    manifest_path,
                    readiness_path=readiness_path,
                )


def _manifest_payload() -> dict:
    return {
        "schema_version": REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_SCHEMA_VERSION,
        "manifest_id": "unit-test-manifest",
        "source_set_references": [
            {
                "reference_id": "active_full_canonical",
                "reference_type": "explicit_source_set_id",
                "source_set_id": "source-set-abc123",
                "description": "Test source set",
            }
        ],
        "profile_rows": [
            {
                "forest_unit_id": "unit-one",
                "source_set_reference_id": "active_full_canonical",
                "primary_plan_source_record_id": "PLAN-001",
                "plan_version": "2024",
                "build_source_record_ids_by_role": {
                    "planning_page": ["PAGE-001"],
                    "primary_land_management_plan": ["PLAN-001"],
                    "record_of_decision": ["ROD-001"],
                },
                "promotion_eligibility": {
                    "status": "eligible",
                    "accepted_blockers": [],
                },
            },
            {
                "forest_unit_id": "unit-two",
                "source_set_reference_id": "active_full_canonical",
                "primary_plan_source_record_id": "PLAN-002",
                "plan_version": "2019",
                "build_source_record_ids_by_role": {
                    "planning_page": ["PAGE-002"],
                    "primary_land_management_plan": ["PLAN-002"],
                },
                "promotion_eligibility": {
                    "status": "eligible_with_blockers",
                    "accepted_blockers": ["component_inventory_build_required"],
                },
            },
        ],
    }


def _readiness_payload() -> dict:
    return {
        "schema_version": "region1-forest-plan-readiness-v1",
        "profile_rows": [
            {
                "forest_unit_id": "unit-one",
                "source_requirements": [
                    {"role": "planning_page", "source_record_id": "PAGE-001"},
                    {"role": "primary_land_management_plan", "source_record_id": "PLAN-001"},
                ],
            },
            {
                "forest_unit_id": "unit-two",
                "source_requirements": [
                    {"role": "planning_page", "source_record_id": "PAGE-002"},
                    {"role": "primary_land_management_plan", "source_record_id": "PLAN-002"},
                ],
            },
        ],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
