from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.nepa_knowledge_graph_export import build_nepa_knowledge_graph_export

from tests.support.nepa_knowledge_graph_export_fixtures import REPO_ROOT
from tests.support.nepa_knowledge_graph_export_fixtures import _read_json
from tests.support.nepa_knowledge_graph_export_fixtures import _write_json
from tests.support.nepa_knowledge_graph_export_fixtures import _write_minimal_source_delta_readiness_report
from tests.support.nepa_knowledge_graph_export_fixtures import _write_minimal_source_set


def test_nepa_knowledge_graph_export_fails_when_promoted_tracking_profile_keeps_placeholder_eval_floor() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        readiness = _read_json(paths["region1_readiness"])
        tracking_row = next(
            row for row in readiness["profile_rows"] if row["forest_unit_id"] == "other-test-forest"
        )
        tracking_row["graph_promotion_status"] = "promoted"
        tracking_row["milestone_5_added_profile"] = False
        tracking_row["readiness_blockers"] = []
        tracking_row["component_inventory_validation"] = {
            "status": "validated",
            "component_count": 1,
            "standard_count": 1,
        }
        tracking_row["applicability_eval_coverage"] = {
            "status": "covered",
            "positive_case_count": 1,
            "hard_negative_case_count": 1,
            "fixture_family_ids": [
                "scope_positive",
                "custer_hard_negative",
            ],
        }
        _write_json(paths["region1_readiness"], readiness)

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=paths["region1_readiness"],
            rule_pack_path=paths["rule_pack"],
        )

        assert result.summary["validation_passed"] is False
        graph = _read_json(result.graph_path)
        checks = {check["name"]: check for check in graph["validation"]["checks"]}
        assert checks["nepa_3d_graph_region1_promoted_profiles_have_eval_fixtures"]["passed"] is False
        assert checks["nepa_3d_graph_region1_promoted_profiles_have_eval_fixtures"]["actual"] == {
            "other-test-forest": False,
            "test-forest": True,
        }


def test_nepa_knowledge_graph_export_accepts_source_delta_readiness_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        source_delta_readiness = _write_minimal_source_delta_readiness_report(
            output_dir,
            source_set_id=source_set_id,
        )

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=source_delta_readiness,
            rule_pack_path=paths["rule_pack"],
        )

        assert result.summary["region1_forest_plan_readiness_profile_count"] == 2
        assert result.summary["region1_support_document_corpus_source_delta_count"] == 1
        assert result.summary["region1_support_document_corpus_official_source_gap_count"] == 1
        assert result.summary["region1_support_document_corpus_tracking_only_ready_count"] == 0

        graph = _read_json(result.graph_path)
        checks = {check["name"]: check for check in graph["validation"]["checks"]}
        assert checks["nepa_3d_graph_region1_readiness_matrix_loaded"]["passed"]
        assert not result.summary["validation_passed"]
        assert (
            checks["nepa_3d_graph_region1_requirement_sources_are_cataloged"]["passed"] is False
        )


def test_source_delta_readiness_fails_inventory_gate_when_promoted_artifact_is_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        source_delta_readiness = _write_minimal_source_delta_readiness_report(
            output_dir,
            source_set_id=source_set_id,
        )
        report = _read_json(source_delta_readiness)
        other_profile = report["forest_profile_readiness"]["profile_rows"][1]
        other_profile["forest_unit_id"] = "dakota-prairie-grasslands"
        other_profile["forest_unit_names"] = ["Dakota Prairie Grasslands"]
        other_profile["configured_profile"] = True
        other_profile["profile_kind"] = "configured_profile"
        other_profile["profile_readiness_status"] = "ready"
        other_profile["active_plan_source_record_id"] = "R1PLAN-dakota-prairie-grasslands-03"
        other_profile["blocker_types"] = []
        other_profile["source_requirements"] = [
            {
                "role": "primary_land_resource_management_plan_part",
                "readiness_status": "catalog_confirmed",
                "source_record_id": "R1PLAN-dakota-prairie-grasslands-03",
            }
        ]
        report["forest_profile_readiness"]["ready_profile_count"] = 2
        report["forest_profile_readiness"]["blocked_profile_count"] = 0
        _write_json(source_delta_readiness, report)

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=source_delta_readiness,
            rule_pack_path=paths["rule_pack"],
        )

        graph = _read_json(result.graph_path)
        checks = {check["name"]: check for check in graph["validation"]["checks"]}
        assert result.summary["region1_forest_plan_graph_ready_profile_count"] == 2
        assert result.summary["region1_forest_plan_blocked_profile_count"] == 0
        assert not checks["nepa_3d_graph_region1_promoted_profiles_have_inventory"]["passed"]


def test_nepa_knowledge_graph_export_fails_when_inventory_is_borrowed_from_other_source_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        borrowed_source_set_id = "source-set-borrowed"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        _write_minimal_source_set(output_dir, source_set_id=borrowed_source_set_id)
        borrowed_inventory_path = (
            output_dir
            / "derived"
            / borrowed_source_set_id
            / "forest_plan_components"
            / "component_inventory.json"
        )

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=paths["region1_readiness"],
            rule_pack_path=paths["rule_pack"],
            forest_plan_components_path=borrowed_inventory_path,
        )

        graph = _read_json(result.graph_path)
        checks = {check["name"]: check for check in graph["validation"]["checks"]}

        assert not result.summary["validation_passed"]
        assert checks["nepa_3d_graph_region1_promoted_profiles_have_inventory"]["passed"]
        assert not checks["nepa_3d_graph_forest_plan_inventory_owned_by_source_set"]["passed"]
        assert (
            checks["nepa_3d_graph_forest_plan_inventory_owned_by_source_set"][
                "failure_category"
            ]
            == "graph_forest_plan_inventory_ownership_gap"
        )
        assert checks["nepa_3d_graph_forest_plan_inventory_owned_by_source_set"]["actual"] == {
            "source_set_id": borrowed_source_set_id,
            "artifact_path": str(borrowed_inventory_path.resolve()),
        }
        assert checks["nepa_3d_graph_forest_plan_inventory_owned_by_source_set"][
            "expected"
        ] == {
            "source_set_id": source_set_id,
            "artifact_path": str(
                (
                    output_dir
                    / "derived"
                    / source_set_id
                    / "forest_plan_components"
                    / "component_inventory.json"
                ).resolve()
            ),
        }
