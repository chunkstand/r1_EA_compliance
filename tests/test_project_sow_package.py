from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources.project_sow_package import DEFAULT_AUTHORITY_INVENTORY_PATH
from usfs_r1_ea_sources.project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from usfs_r1_ea_sources.project_sow_package import run_project_sow_package


REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = REPO_ROOT / "config" / "fixtures" / "project_sow" / "east_crazies_land_exchange_intake.json"


def test_project_sow_package_generates_land_exchange_resource_scopes(tmp_path: Path) -> None:
    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
    )

    assert result.summary["passed"] is True, result.summary
    assert result.summary["output_written"] is True
    assert result.package_path.exists()
    assert result.markdown_path.exists()
    assert result.manifest_path.exists()

    package = json.loads(result.package_path.read_text())
    scope_ids = {scope["resource_scope_id"] for scope in package["resource_scope_records"]}
    assert {
        "nepa_project_management",
        "lands_realty_land_exchange",
        "forest_plan_consistency",
        "wildlife_species_botany",
        "cultural_tribal_resources",
        "hydrology_wetlands_water_quality",
        "roads_access_recreation_designated_areas",
        "minerals_energy_hazardous_materials",
        "public_involvement_coordination",
    }.issubset(scope_ids)
    assert package["validation"]["passed"] is True
    assert package["manifest"]["input_hashes"]["intake_sha256"]

    authority_ids = {
        row["authority_family_id"] for row in package["authority_requirement_matrix"]
    }
    assert "land_exchange_statutory_authorities" in authority_ids
    assert "nfma_forest_planning_project_consistency" in authority_ids

    markdown = result.markdown_path.read_text()
    assert "Requirements Package" in markdown
    assert "Lands, realty, and land exchange case requirements" in markdown
    assert "This generated package scopes specialist work" in markdown


def test_project_sow_package_fails_unknown_authority_family(tmp_path: Path) -> None:
    resource_config = json.loads((REPO_ROOT / DEFAULT_RESOURCE_SCOPE_CONFIG_PATH).read_text())
    resource_config["resource_scopes"][0]["authority_family_ids"].append("missing_authority")
    bad_config_path = tmp_path / "bad_resource_config.json"
    bad_config_path.write_text(json.dumps(resource_config), encoding="utf-8")

    result = run_project_sow_package(
        intake_path=INTAKE_PATH,
        output_dir=tmp_path / "source_library",
        resource_scope_config_path=bad_config_path,
        authority_inventory_path=REPO_ROOT / DEFAULT_AUTHORITY_INVENTORY_PATH,
    )

    assert result.summary["passed"] is False
    assert result.summary["output_written"] is False
    assert result.summary["validation_failure_count"] == 1
