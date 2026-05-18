from __future__ import annotations

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
from usfs_r1_ea_sources.source_register_proving import resolve_authority_currentness_inputs

from tests.test_source_register_proving import build_test_proving_slice
from tests.support.phase_eval_fixtures import phase


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
        build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
        build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)
        export = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
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

        assert currentness.summary["validation_passed"] is True
        assert export.summary["validation_passed"] is True
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
