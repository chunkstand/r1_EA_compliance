from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.knowledge_graph_query import run_knowledge_graph_query
from usfs_r1_ea_sources.knowledge_graph_query_eval import run_knowledge_graph_query_eval
from usfs_r1_ea_sources.nepa_knowledge_graph_export import build_nepa_knowledge_graph_export

from tests.support.nepa_knowledge_graph_export_fixtures import REPO_ROOT
from tests.support.nepa_knowledge_graph_export_fixtures import _write_json
from tests.support.nepa_knowledge_graph_export_fixtures import _write_minimal_source_set


def test_knowledge_graph_query_returns_citation_and_neighborhood_surface() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir, source_set_id, graph_path = _build_graph(Path(tmp))

        result = run_knowledge_graph_query(
            output_dir=output_dir,
            source_set_id=source_set_id,
            query_type="source_record",
            query="R1EA-001",
            limit=3,
            require_hit=True,
        )

        assert result.summary["passed"]
        assert result.summary["result_count"] >= 1
        assert result.output_path.exists()

        payload = json.loads(result.output_path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "knowledge-graph-query-results-v1"
        assert payload["graph_path"] == str(graph_path)
        assert payload["freshness_warnings"] == []

        first = next(
            result for result in payload["results"] if result["node_id"] == "source_record:R1EA-001"
        )
        assert first["node_id"] == "source_record:R1EA-001"
        assert first["node_type"] == "source_record"
        assert first["citations"] == [
            {
                "artifact_sha256": "sha-R1EA-001",
                "citation_label": "R1EA-001 citation",
                "source_record_id": "R1EA-001",
                "url": "https://example.test/R1EA-001",
            }
        ]
        assert first["neighborhood"]["incoming_edge_count"] >= 1
        assert first["neighborhood"]["outgoing_edge_count"] >= 1


def test_knowledge_graph_query_reports_freshness_warnings_without_hiding_results() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir, source_set_id, _graph_path = _build_graph(Path(tmp))
        catalog_path = output_dir / "catalog" / "source_catalog.jsonl"
        catalog_path.write_text(
            catalog_path.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )

        result = run_knowledge_graph_query(
            output_dir=output_dir,
            source_set_id=source_set_id,
            query_type="citation",
            query="R1EA-001",
            limit=3,
        )

        assert result.summary["passed"]
        assert result.summary["result_count"] >= 1
        warning_types = {warning["warning_type"] for warning in result.payload["freshness_warnings"]}
        assert "input_hash_mismatch" in warning_types


def test_knowledge_graph_query_eval_covers_positive_and_hard_negative_queries() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output_dir, source_set_id, _graph_path = _build_graph(tmp_path)
        eval_path = tmp_path / "knowledge_graph_query_eval.json"
        _write_json(
            eval_path,
            {
                "schema_version": "knowledge-graph-query-eval-v1",
                "contract_id": "test-knowledge-graph-query-eval",
                "version": "0.1.0",
                "default_limit": 5,
                "min_case_count": 4,
                "min_hard_negative_case_count": 1,
                "required_query_types": [
                    "edge_type",
                    "node_type",
                    "source_record",
                ],
                "cases": [
                    {
                        "case_id": "source-record-hit",
                        "query_type": "source_record",
                        "query": "R1EA-001",
                        "expected_min_results": 1,
                        "expected_node_ids": ["source_record:R1EA-001"],
                        "expected_citation_labels": ["R1EA-001 citation"],
                    },
                    {
                        "case_id": "forest-component-node-type-hit",
                        "query_type": "node_type",
                        "query": "forest_plan_component",
                        "expected_min_results": 1,
                        "expected_node_types": ["forest_plan_component"],
                    },
                    {
                        "case_id": "source-record-edge-hit",
                        "query_type": "edge_type",
                        "query": "HAS_SOURCE_RECORD",
                        "expected_min_results": 1,
                        "expected_edge_types": ["HAS_SOURCE_RECORD"],
                    },
                    {
                        "case_id": "unknown-source-record-zero-hit",
                        "query_type": "source_record",
                        "query": "NOPE-001",
                        "hard_negative": True,
                        "expected_min_results": 0,
                        "expected_max_results": 0,
                    },
                ],
            },
        )

        result = run_knowledge_graph_query_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
            eval_path=eval_path,
        )

        assert result.summary["passed"]
        assert result.summary["case_count"] == 4
        assert result.summary["hard_negative_case_count"] == 1
        assert result.summary["query_type_count"] == 3
        assert result.output_path.exists()


def _build_graph(tmp_path: Path) -> tuple[Path, str, Path]:
    output_dir = tmp_path / "source_library"
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
    return output_dir, source_set_id, result.graph_path
