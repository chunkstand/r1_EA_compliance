from __future__ import annotations

import json
from pathlib import Path
import tempfile

from usfs_r1_ea_sources.authority_currentness import build_authority_currentness_report
from usfs_r1_ea_sources.authority_currentness import DEFAULT_AUTHORITY_INVENTORY_PATH
from usfs_r1_ea_sources.authority_currentness import DEFAULT_SOURCE_ADDITION_DECISIONS_PATH
from usfs_r1_ea_sources.authority_ontology_validate import run_authority_ontology_validate
from usfs_r1_ea_sources.authority_relationship_eval import run_authority_relationship_eval
from usfs_r1_ea_sources.citation_alias_eval import run_citation_alias_eval
from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.graph_accuracy_eval import run_graph_accuracy_eval
from usfs_r1_ea_sources.graph_health_eval import run_graph_health_eval
from usfs_r1_ea_sources.nepa_knowledge_graph_export import build_nepa_knowledge_graph_export
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.semantic_graph_eval import run_semantic_graph_eval
from usfs_r1_ea_sources.source_register_proving import resolve_authority_currentness_inputs

from tests.test_source_register_proving import build_test_proving_slice
from tests.support.nepa_knowledge_graph_export_fixtures import _catalog_row
from tests.support.nepa_knowledge_graph_export_fixtures import _write_jsonl
from tests.support.phase_eval_fixtures import phase


def _build_canonical_knowledge_graph(output_dir: Path) -> tuple[str, dict, dict]:
    proving = build_test_proving_slice(output_dir)
    source_set_id = proving.summary["source_set_id"]

    currentness_inputs = resolve_authority_currentness_inputs(
        output_dir=output_dir,
        source_set_id=source_set_id,
        authority_inventory_path=DEFAULT_AUTHORITY_INVENTORY_PATH,
        source_addition_decisions_path=DEFAULT_SOURCE_ADDITION_DECISIONS_PATH,
        catalog_path=None,
        source_set_manifest_path=None,
    )
    currentness = build_authority_currentness_report(
        output_dir=output_dir,
        source_set_id=source_set_id,
        authority_inventory_path=currentness_inputs["authority_inventory_path"],
        source_addition_decisions_path=currentness_inputs[
            "source_addition_decisions_path"
        ],
        catalog_path=currentness_inputs["catalog_path"],
        source_set_manifest_path=currentness_inputs["source_set_manifest_path"],
    )
    graph_inputs = _write_minimal_region1_graph_inputs(output_dir, source_set_id=source_set_id)
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)
    export = build_nepa_knowledge_graph_export(
        output_dir=output_dir,
        source_set_id=source_set_id,
        authority_inventory_path=currentness_inputs["authority_inventory_path"],
        forest_plan_profiles_path=graph_inputs["forest_profiles_path"],
        region1_forest_plan_readiness_path=graph_inputs["readiness_path"],
        forest_plan_components_path=graph_inputs["component_inventory_path"],
    )
    return source_set_id, currentness.summary, export.summary


def _knowledge_graph_path(output_dir: Path, source_set_id: str) -> Path:
    return (
        output_dir
        / "derived"
        / source_set_id
        / "knowledge_graph"
        / "nepa_3d_graph.json"
    )


def _semantic_graph_eval_contract_for_source_set(tmp_dir: Path, source_set_id: str) -> Path:
    contract = json.loads(
        Path("config/semantic_graph_direct_eval_v1.json").read_text(encoding="utf-8")
    )
    contract["required_source_set_ids"] = [source_set_id]
    path = tmp_dir / "semantic_graph_direct_eval_v1.json"
    _write_json(path, contract)
    return path


def _checks_by_name(output_path: Path) -> dict[str, dict]:
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return {
        str(check["name"]): check
        for check in payload.get("checks", [])
        if isinstance(check, dict) and check.get("name")
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_minimal_region1_graph_inputs(output_dir: Path, *, source_set_id: str) -> dict[str, Path]:
    catalog_path = output_dir / "catalog" / "source_catalog.jsonl"
    catalog_rows = [
        json.loads(line)
        for line in catalog_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert catalog_rows
    plan_source_record_id = str(catalog_rows[0]["source_record_id"])
    derived_dir = output_dir / "derived" / source_set_id / "forest_plan_components"
    component_inventory_path = derived_dir / "component_inventory.json"
    forest_profiles_path = output_dir / "forest_profiles.json"
    readiness_path = output_dir / "region1_readiness.json"
    _write_json(
        component_inventory_path,
        {
            "schema_version": "forest-plan-component-inventory-v0",
            "source_set_id": source_set_id,
            "components": [
                {
                    "component_id": "test-forest:standard-1",
                    "forest_unit_id": "test-forest",
                    "source_record_id": plan_source_record_id,
                    "artifact_sha256": "sha-test-forest-plan",
                    "content_sha256": "component-sha",
                    "component_text": "Standard 01",
                    "component_type": "standard",
                    "source_chunk_ids": ["chunk:test-forest-plan"],
                }
            ],
        },
    )
    _write_json(
        forest_profiles_path,
        {
            "schema_version": "forest-plan-profiles-v0",
            "known_other_forest_units": [],
            "profiles": [
                {
                    "forest_unit_id": "test-forest",
                    "forest_unit_names": ["Test Forest"],
                    "active_plan_source_record_id": plan_source_record_id,
                    "required_readiness_source_roles": ["primary_land_management_plan"],
                    "supporting_source_record_ids_by_role": {
                        "primary_land_management_plan": {
                            "source_record_id": plan_source_record_id
                        }
                    },
                }
            ],
        },
    )
    _write_json(
        readiness_path,
        {
            "schema_version": "region1-forest-plan-readiness-v1",
            "readiness_matrix_id": "unit-region1-readiness",
            "source_set_id": source_set_id,
            "region1_completeness_claim": False,
            "field_directive_requirements": [],
            "overlay_requirements": [],
            "profile_rows": [
                {
                    "forest_unit_id": "test-forest",
                    "forest_unit_names": ["Test Forest"],
                    "profile_kind": "active_profile",
                    "active_plan_source_record_id": plan_source_record_id,
                    "graph_promotion_status": "promoted",
                    "milestone_5_added_profile": False,
                    "readiness_blockers": [],
                    "source_requirements": [
                        {
                            "role": "primary_land_management_plan",
                            "readiness_status": "catalog_confirmed",
                            "source_record_id": plan_source_record_id,
                        }
                    ],
                    "component_inventory_validation": {
                        "status": "validated",
                        "component_count": 1,
                        "standard_count": 1,
                    },
                    "applicability_eval_coverage": {
                        "status": "covered",
                        "positive_case_count": 1,
                        "hard_negative_case_count": 1,
                        "fixture_family_ids": ["selected_profile_component_eval_seed"],
                    },
                }
            ],
        },
    )
    return {
        "component_inventory_path": component_inventory_path,
        "forest_profiles_path": forest_profiles_path,
        "readiness_path": readiness_path,
    }


def test_phase_1_5_eval_commands_pass_on_proving_slice() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        build_test_proving_slice(output_dir)

        relationship_eval = run_authority_relationship_eval(output_dir=output_dir)
        alias_eval = run_citation_alias_eval(output_dir=output_dir)
        graph_health = run_graph_health_eval(output_dir=output_dir)
        graph_accuracy = run_graph_accuracy_eval(output_dir=output_dir)

        assert relationship_eval.summary["passed"] is True
        assert alias_eval.summary["passed"] is True
        assert graph_health.summary["passed"] is True
        assert graph_accuracy.summary["passed"] is True


def test_canonical_graph_eval_commands_pass_on_exported_knowledge_graph() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, currentness_summary, export_summary = _build_canonical_knowledge_graph(
            output_dir
        )

        ontology_eval = run_authority_ontology_validate(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        relationship_eval = run_authority_relationship_eval(output_dir=output_dir)
        alias_eval = run_citation_alias_eval(output_dir=output_dir)
        graph_health = run_graph_health_eval(output_dir=output_dir)
        graph_accuracy = run_graph_accuracy_eval(output_dir=output_dir)
        phase_eval = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

        assert currentness_summary["validation_passed"] is True
        assert export_summary["validation_passed"] is True
        assert ontology_eval.summary["passed"] is True
        assert relationship_eval.summary["passed"] is True
        assert alias_eval.summary["passed"] is True
        assert graph_health.summary["passed"] is True
        assert graph_accuracy.summary["passed"] is True
        assert phase(phase_eval.summary, "authority_ontology")["passed"] is True
        assert phase(phase_eval.summary, "authority_relationships")["passed"] is True
        assert phase(phase_eval.summary, "citation_aliases")["passed"] is True
        assert phase(phase_eval.summary, "graph_health")["passed"] is True
        assert phase(phase_eval.summary, "graph_accuracy")["passed"] is True


def test_semantic_graph_direct_eval_aggregate_passes_with_controlled_negatives() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, _, _ = _build_canonical_knowledge_graph(output_dir)
        eval_path = _semantic_graph_eval_contract_for_source_set(Path(tmp_dir), source_set_id)

        result = run_semantic_graph_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
            eval_path=eval_path,
        )
        payload = json.loads(result.output_path.read_text(encoding="utf-8"))

        assert result.summary["passed"] is True
        assert result.summary["case_count"] == 12
        assert result.summary["hard_negative_case_count"] == 7
        assert {
            "ontology_typing",
            "relationship_correctness",
            "relationship_provenance",
            "alias_identity_resolution",
            "currentness_metadata_carriage",
            "semantic_lens_integrity",
            "justification_path_accuracy",
            "controlled_negative",
        }.issubset(payload["coverage_categories"])
        assert all(case["passed"] for case in payload["negative_results"])


def test_semantic_graph_direct_eval_fails_when_positive_graph_report_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, _, _ = _build_canonical_knowledge_graph(output_dir)
        eval_path = _semantic_graph_eval_contract_for_source_set(Path(tmp_dir), source_set_id)
        graph_path = _knowledge_graph_path(output_dir, source_set_id)
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        graph["nodes"] = [
            node
            for node in graph["nodes"]
            if str(node.get("node_type") or "") != "authority_section"
        ]
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        result = run_semantic_graph_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
            eval_path=eval_path,
        )
        payload = json.loads(result.output_path.read_text(encoding="utf-8"))

        assert result.summary["passed"] is False
        assert "authority_ontology" in result.summary["failed_positive_case_ids"]
        assert any(
            failure["metric"] == "positive_reports_pass"
            for failure in payload["threshold_failures"]
        )


def test_canonical_graph_eval_commands_target_requested_source_set_from_archived_catalog_surface() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, _, _ = _build_canonical_knowledge_graph(output_dir)

        archived_catalog_dir = (
            output_dir / "runs" / "current-source-gap-closeout-catalog-gate" / "catalog_gate"
        )
        archived_catalog_dir.mkdir(parents=True, exist_ok=True)
        for filename in (
            "source_set_manifest.json",
            "source_catalog.jsonl",
            "source_graph_nodes.jsonl",
            "source_graph_edges.jsonl",
            "catalog_validation.json",
        ):
            (output_dir / "catalog" / filename).replace(archived_catalog_dir / filename)
        _write_json(
            output_dir / "catalog" / "source_set_manifest.json",
            {
                "source_set_id": "source-set-root",
                "created_at": "2026-05-26T00:00:00Z",
                "source_count": 1,
                "artifact_count": 1,
                "workbook_path": "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
            },
        )
        _write_jsonl(
            output_dir / "catalog" / "source_catalog.jsonl",
            [_catalog_row("source-set-root", "ROOT-001", "Root-only row", "downloaded")],
        )
        _write_jsonl(
            output_dir / "catalog" / "source_graph_nodes.jsonl",
            [{"id": "source:ROOT-001", "type": "Source", "source_record_id": "ROOT-001"}],
        )
        _write_jsonl(
            output_dir / "catalog" / "source_graph_edges.jsonl",
            [
                {
                    "id": "source:ROOT-001|SUPPORTS_REVIEW_TOPIC|topic:root",
                    "source": "source:ROOT-001",
                    "target": "topic:root",
                    "relationship": "SUPPORTS_REVIEW_TOPIC",
                }
            ],
        )
        _write_json(
            output_dir / "catalog" / "catalog_validation.json",
            {"passed": True, "source_set_id": "source-set-root"},
        )

        ontology_eval = run_authority_ontology_validate(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        relationship_eval = run_authority_relationship_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        alias_eval = run_citation_alias_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        graph_health = run_graph_health_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        graph_accuracy = run_graph_accuracy_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        phase_eval = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

        assert ontology_eval.summary["passed"] is True
        assert relationship_eval.summary["passed"] is True
        assert alias_eval.summary["passed"] is True
        assert graph_health.summary["passed"] is True
        assert graph_accuracy.summary["passed"] is True
        assert phase(phase_eval.summary, "authority_ontology")["passed"] is True
        assert phase(phase_eval.summary, "authority_relationships")["passed"] is True
        assert phase(phase_eval.summary, "citation_aliases")["passed"] is True
        assert phase(phase_eval.summary, "graph_health")["passed"] is True
        assert phase(phase_eval.summary, "graph_accuracy")["passed"] is True


def test_authority_ontology_validate_fails_when_required_source_set_node_type_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, _, _ = _build_canonical_knowledge_graph(output_dir)
        graph_path = _knowledge_graph_path(output_dir, source_set_id)
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        graph["nodes"] = [
            node
            for node in graph["nodes"]
            if str(node.get("node_type") or "") != "authority_section"
        ]
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        ontology_eval = run_authority_ontology_validate(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

        assert ontology_eval.summary["passed"] is False
        checks = _checks_by_name(ontology_eval.output_path)
        assert checks["knowledge_graph_exports_required_ontology_node_types"]["passed"] is False
        assert "authority_section" in checks["knowledge_graph_exports_required_ontology_node_types"]["actual"]


def test_graph_health_eval_fails_when_required_semantic_lens_is_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, _, _ = _build_canonical_knowledge_graph(output_dir)
        graph_path = _knowledge_graph_path(output_dir, source_set_id)
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        graph["lens_metadata"] = [
            entry
            for entry in graph["lens_metadata"]
            if str(entry.get("lens_id") or "") != "semantic_relationships"
        ]
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        health_eval = run_graph_health_eval(output_dir=output_dir)

        assert health_eval.summary["passed"] is False
        checks = _checks_by_name(health_eval.output_path)
        assert checks["required_lenses_present"]["passed"] is False
        assert "semantic_relationships" not in checks["required_lenses_present"]["actual"]


def test_graph_accuracy_eval_fails_when_authority_path_loses_justification_edge() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        source_set_id, _, _ = _build_canonical_knowledge_graph(output_dir)
        graph_path = _knowledge_graph_path(output_dir, source_set_id)
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        graph["edges"] = [
            edge
            for edge in graph["edges"]
            if not (
                str(edge.get("edge_type") or "") == "JUSTIFIED_BY"
                and str(edge.get("source_node_id") or "").startswith("authority_path:")
            )
        ]
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        accuracy_eval = run_graph_accuracy_eval(output_dir=output_dir)

        assert accuracy_eval.summary["passed"] is False
        checks = _checks_by_name(accuracy_eval.output_path)
        assert checks["authority_paths_have_justification_paths"]["passed"] is False
        assert checks["authority_paths_have_justification_paths"]["actual"]
