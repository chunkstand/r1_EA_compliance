from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.nepa_knowledge_graph_export import build_nepa_knowledge_graph_export

from tests.support.nepa_knowledge_graph_export_fixtures import REPO_ROOT
from tests.support.nepa_knowledge_graph_export_fixtures import _read_json
from tests.support.nepa_knowledge_graph_export_fixtures import _read_jsonl
from tests.support.nepa_knowledge_graph_export_fixtures import _rewrite_catalog_as_source_register_v1
from tests.support.nepa_knowledge_graph_export_fixtures import _write_json
from tests.support.nepa_knowledge_graph_export_fixtures import _write_minimal_source_set


def test_nepa_knowledge_graph_export_builds_source_set_graph_from_audited_surfaces() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)

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

        assert result.summary["validation_passed"]
        assert result.summary["authority_family_count"] == 3
        assert result.summary["base_rule_count"] == 2
        assert result.summary["authority_family_rule_template_count"] == 1
        assert result.summary["region1_forest_plan_readiness_profile_count"] == 2
        assert result.summary["region1_forest_plan_added_profile_count"] == 1
        assert result.summary["region1_forest_plan_blocked_profile_count"] == 1
        assert result.summary["region1_forest_plan_promoted_profiles_with_eval_fixture_count"] == 1
        assert result.summary["forest_plan_component_count"] == 1
        assert result.summary["region1_field_directive_requirement_graph_node_count"] == 1
        assert result.summary["region1_overlay_requirement_graph_node_count"] == 1
        assert result.summary["catalog_graph_node_count"] == 1
        assert result.summary["catalog_graph_edge_count"] == 1

        graph = _read_json(result.graph_path)
        nodes = _read_jsonl(result.nodes_path)
        edges = _read_jsonl(result.edges_path)
        nodes_by_id = {node["node_id"]: node for node in nodes}
        node_ids = {node["node_id"] for node in nodes}
        checks = {check["name"]: check for check in graph["validation"]["checks"]}

        assert len(nodes) == graph["summary"]["node_count"]
        assert len(edges) == graph["summary"]["edge_count"]
        assert graph["validation"]["failure_category_counts"] == {}
        assert graph["summary"]["failure_category_counts"] == {}
        assert graph["summary"]["authority_category_counts"] == {
            "law": 1,
            "regulation": 1,
        }
        assert graph["summary"]["source_status_counts"] == {
            "downloaded": 4,
            "skipped_excluded": 1,
        }
        assert graph["summary"]["source_partition_counts"] == {
            "active_review_corpus": 3,
            "candidate_blocked_source": 1,
            "currentness_supersession_archive": 1,
        }
        assert graph["summary"]["source_currentness_status_counts"] == {
            "confirmed_from_catalog": 4,
            "excluded_no_artifact": 1,
        }
        assert graph["summary"]["applicability_status_counts"] == {}
        assert all(check["failure_category"].startswith("graph_") for check in checks.values())
        assert all(edge["source_node_id"] in node_ids for edge in edges)
        assert all(edge["target_node_id"] in node_ids for edge in edges)
        assert checks["nepa_3d_graph_exports_all_authority_families"]["passed"]
        assert (
            checks["nepa_3d_graph_exports_all_authority_families"]["failure_category"]
            == "graph_missing_authority_family"
        )
        assert checks["nepa_3d_graph_exports_all_catalog_source_records"]["passed"]
        assert (
            checks["nepa_3d_graph_exports_all_catalog_source_records"]["failure_category"]
            == "graph_missing_source_record"
        )
        assert checks["nepa_3d_graph_exports_candidate_families"]["passed"]
        assert checks["nepa_3d_graph_exports_superseded_families"]["passed"]
        assert checks["nepa_3d_graph_reads_catalog_graph_seeds"]["passed"]
        assert checks["nepa_3d_graph_reports_required_summary_count_fields"]["passed"]
        assert checks["nepa_3d_graph_forest_plan_inventory_owned_by_source_set"]["passed"]
        assert checks["nepa_3d_graph_nodes_have_required_provenance"]["passed"]
        assert checks["nepa_3d_graph_edges_match_declared_endpoint_types"]["passed"]
        assert checks["nepa_3d_graph_region1_readiness_prevents_overclaim"]["passed"]
        assert checks["nepa_3d_graph_exports_region1_forest_units"]["passed"]
        assert checks["nepa_3d_graph_region1_promoted_profiles_have_eval_fixtures"]["passed"]
        assert checks["nepa_3d_graph_exports_region1_field_directive_requirements"]["passed"]
        assert checks["nepa_3d_graph_exports_region1_overlay_requirements"]["passed"]
        assert checks["nepa_3d_graph_region1_requirement_sources_are_cataloged"]["passed"]
        assert checks["nepa_3d_graph_region1_requirement_sources_are_linked"]["passed"]
        assert checks["nepa_3d_graph_lens_metadata_shape"]["passed"]
        assert checks["nepa_3d_graph_lens_metadata_required_lenses_present"]["passed"]
        assert "forest_plan_component" in graph["summary"]["node_type_counts"]
        assert "source_claim" in graph["summary"]["node_type_counts"]
        assert "forest_profile_not_ready" in graph["summary"]["readiness_blocker_counts"]
        blocker_nodes = [
            node
            for node in nodes
            if node["node_type"] == "readiness_blocker"
            and node["provenance"].get("blocker_type") == "forest_profile_not_ready"
        ]
        assert blocker_nodes
        assert all(
            node["readiness_semantic_class"] == "synthetic_blocker_node"
            for node in blocker_nodes
        )
        assert (
            nodes_by_id["forest_unit:other-test-forest"]["display_status"]
            == "readiness_blocked"
        )
        assert (
            nodes_by_id["forest_unit:other-test-forest"]["readiness_semantic_class"]
            == "blocked_domain_node"
        )
        assert (
            nodes_by_id[
                "forest_plan_component:region1-field-directive:field-directives"
            ]["metadata"]["component_type"]
            == "field_directive_requirement"
        )
        assert (
            nodes_by_id[
                "forest_plan_component:region1-overlay:inventoried-roadless-area"
            ]["metadata"]["component_type"]
            == "overlay"
        )
        assert any(
            edge["edge_type"] == "HAS_READINESS_BLOCKER"
            and edge["source_node_id"] == "forest_unit:other-test-forest"
            and edge["readiness_semantic_class"] == "blocker_relationship_edge"
            for edge in edges
        )
        assert any(
            edge["edge_type"] == "HAS_FOREST_PLAN"
            and edge["source_node_id"] == "forest_unit:other-test-forest"
            and edge["target_node_id"] == "forest_plan:other-test-forest:R1PLAN-OTHER-001"
            and edge["readiness_semantic_class"] == "blocked_relationship_edge"
            for edge in edges
        )
        assert any(
            edge["edge_type"] == "HAS_FOREST_COMPONENT"
            and edge["source_node_id"] == "source_record:R1EA-002"
            and edge["target_node_id"]
            == "forest_plan_component:region1-field-directive:field-directives"
            for edge in edges
        )
        assert any(
            edge["edge_type"] == "HAS_FOREST_COMPONENT"
            and edge["source_node_id"] == "source_record:R1EA-002"
            and edge["target_node_id"]
            == "forest_plan_component:region1-overlay:inventoried-roadless-area"
            for edge in edges
        )


def test_nepa_knowledge_graph_export_builds_source_register_v1_graph_from_region1_readiness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        _rewrite_catalog_as_source_register_v1(output_dir, source_set_id=source_set_id)
        forest_profiles = _read_json(paths["forest_profiles"])
        forest_profiles["profiles"][0]["supporting_source_record_ids_by_role"][
            "stale_legacy_support"
        ] = {
            "source_record_id": "R1PLAN-LEGACY-MISSING-001",
            "required_for": "legacy regression guard",
        }
        _write_json(paths["forest_profiles"], forest_profiles)

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=paths["region1_readiness"],
        )

        graph = _read_json(result.graph_path)
        checks = {check["name"]: check for check in graph["validation"]["checks"]}

        assert result.summary["validation_passed"]
        assert result.summary["region1_forest_plan_readiness_profile_count"] == 2
        assert result.summary["region1_forest_plan_graph_ready_profile_count"] == 1
        assert result.summary["forest_plan_profile_count"] == 1
        assert result.summary["node_type_counts"]["authority_path"] >= 1
        assert result.summary["node_type_counts"]["forest_unit"] >= 2
        assert checks["nepa_3d_graph_edges_resolve_to_nodes"]["passed"]
        assert checks["nepa_3d_graph_exports_semantic_authority_paths"]["passed"]
        assert checks["nepa_3d_graph_exports_forest_units_from_semantic_relationships"]["passed"]
        assert checks["nepa_3d_graph_region1_readiness_covers_configured_profiles"]["passed"]
        assert checks["nepa_3d_graph_region1_promoted_profiles_have_inventory"]["passed"]


def test_nepa_knowledge_graph_export_accepts_stale_proving_context_id_when_manifest_matches() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-live"
        stale_source_set_id = "source-set-stale"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        _rewrite_catalog_as_source_register_v1(output_dir, source_set_id=source_set_id)
        proving_dir = output_dir / "derived" / stale_source_set_id / "source_register_proving"
        proving_dir.mkdir(parents=True, exist_ok=True)
        _write_json(proving_dir / "proving_slice_report.json", {"schema_version": "unit-proving-report"})
        _write_json(
            output_dir / "derived" / "source_register_proving" / "latest_context.json",
            {
                "schema_version": "source-register-proving-context-v1",
                "source_set_id": stale_source_set_id,
                "report_path": str((proving_dir / "proving_slice_report.json").resolve()),
                "catalog_dir": str((output_dir / "catalog").resolve()),
                "source_catalog_path": str((output_dir / "catalog" / "source_catalog.jsonl").resolve()),
                "source_set_manifest_path": str(
                    (output_dir / "catalog" / "source_set_manifest.json").resolve()
                ),
                "authority_inventory_path": str(paths["authority_inventory"].resolve()),
                "source_addition_decisions_path": str(
                    (proving_dir / "source_addition_decisions.json").resolve()
                ),
            },
        )

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=paths["region1_readiness"],
        )

        assert result.summary["validation_passed"]
        assert result.summary["authority_family_count"] == 3
        assert result.summary["forest_plan_profile_count"] == 1
