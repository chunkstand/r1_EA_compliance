from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.nepa_knowledge_graph_export import build_nepa_knowledge_graph_export
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval

from tests.support.nepa_knowledge_graph_export_fixtures import REPO_ROOT
from tests.support.nepa_knowledge_graph_export_fixtures import _read_json
from tests.support.nepa_knowledge_graph_export_fixtures import _read_jsonl
from tests.support.nepa_knowledge_graph_export_fixtures import _write_minimal_source_set
from tests.support.nepa_knowledge_graph_review_fixtures import _phase
from tests.support.nepa_knowledge_graph_review_fixtures import _write_minimal_review_overlay


def test_nepa_knowledge_graph_export_builds_review_specific_overlay() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        review_id = "review-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)
        _write_minimal_review_overlay(output_dir, source_set_id=source_set_id, review_id=review_id)

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            review_id=review_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            region1_forest_plan_readiness_path=paths["region1_readiness"],
            rule_pack_path=paths["rule_pack"],
        )

        graph = _read_json(result.graph_path)
        checks = {check["name"]: check for check in graph["validation"]["checks"]}
        nodes = {node["node_id"]: node for node in _read_jsonl(result.nodes_path)}
        edges = _read_jsonl(result.edges_path)

        assert result.graph_dir == output_dir / "reviews" / review_id / "knowledge_graph"
        assert result.summary["validation_passed"]
        assert graph["validation"]["failure_category_counts"] == {}
        assert graph["summary"]["authority_category_counts"] == {
            "forest_plan": 1,
            "law": 3,
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
        assert graph["summary"]["applicability_status_counts"] == {
            "applicable": 2,
            "not_applicable": 1,
        }
        assert all(check["failure_category"].startswith("graph_") for check in checks.values())
        assert graph["export_scope"] == {
            "scope_type": "review",
            "source_set_id": source_set_id,
            "review_id": review_id,
        }
        assert result.summary["review_candidate_authority_count"] == 2
        assert result.summary["applicable_decision_count"] == 1
        assert result.summary["non_applicable_decision_count"] == 1
        assert result.summary["generated_rule_count"] == 1
        assert result.summary["compliance_finding_count"] == 1
        assert result.summary["review_required_artifact_count"] == 10
        assert result.summary["review_package_fact_node_count"] == 1
        assert result.summary["review_retrieval_trace_count"] == 2
        assert result.summary["review_graph_trace_count"] == 2
        assert checks["nepa_3d_review_graph_exports_all_candidate_authorities"]["passed"]
        assert checks["nepa_3d_graph_reports_required_summary_count_fields"]["passed"]
        assert (
            checks["nepa_3d_review_graph_exports_all_candidate_authorities"][
                "failure_category"
            ]
            == "graph_missing_candidate_authority"
        )
        assert checks["nepa_3d_review_graph_maps_each_candidate_to_one_decision"]["passed"]
        assert (
            checks["nepa_3d_review_graph_maps_each_candidate_to_one_decision"][
                "failure_category"
            ]
            == "graph_missing_applicability_decision"
        )
        assert checks["nepa_3d_review_graph_links_required_review_artifacts"]["passed"]
        assert checks["nepa_3d_review_graph_search_coverage_references_resolve"]["passed"]
        assert checks["nepa_3d_review_graph_retrieval_trace_references_resolve"]["passed"]
        assert checks["nepa_3d_review_graph_graph_trace_references_resolve"]["passed"]
        assert checks["nepa_3d_review_graph_generated_rules_from_applicable_decisions"]["passed"]
        assert checks["nepa_3d_review_graph_links_findings_to_evidence"]["passed"]
        inputs = {input_record["name"]: input_record for input_record in graph["inputs"]}
        for input_name in [
            "review_authority_universe_snapshot",
            "review_package_fact_graph",
            "review_applicability_retrieval_trace",
            "review_applicability_graph_trace",
            "review_applicability_decisions",
            "review_search_coverage_certificates",
            "review_generated_rule_pack",
            "review_compliance_matrix",
            "review_finding_graph_nodes",
            "review_finding_graph_edges",
        ]:
            assert inputs[input_name]["exists"]
            assert inputs[input_name]["sha256"]
        assert nodes["rule_template:base:nepa_rule"]["display_status"] == "applicable"
        assert (
            nodes["forest_plan_component:R1PLAN-001-FW-STD-01"]["display_status"]
            == "not_applicable"
        )
        assert any(edge["edge_type"] == "GENERATES_RULE" for edge in edges)
        assert any(
            edge["edge_type"] == "SUPPORTS_COMPLIANCE_FINDING"
            and edge["source_node_id"].startswith("evidence_span:review:")
            for edge in edges
        )

        phase_eval = run_phase_aligned_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
            review_id=review_id,
        )
        nepa_phase = _phase(phase_eval.summary, "nepa_3d_review_graph")
        assert nepa_phase["passed"]
        assert nepa_phase["reviewer_ready"]
        assert nepa_phase["details"]["review_id"] == review_id
        assert nepa_phase["details"]["validation_check_count"] == 80
        assert nepa_phase["details"]["failure_category_counts"] == {}
