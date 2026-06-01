from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

from tests.test_eval_trace_export import _write_store
from usfs_r1_ea_sources.eval_context_graph_contract import (
    DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH,
)
from usfs_r1_ea_sources.eval_context_graph_contract import (
    load_eval_context_graph_contract,
)
from usfs_r1_ea_sources.eval_context_graph_contract import (
    validate_eval_context_graph_contract,
)
from usfs_r1_ea_sources.eval_context_graph import CONTEXT_GRAPH_SCHEMA_VERSION
from usfs_r1_ea_sources.eval_context_graph import (
    CONTEXT_GRAPH_BUILD_SUMMARY_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.eval_context_graph import (
    CONTEXT_GRAPH_EVAL_SUMMARY_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.eval_context_graph import run_eval_context_graph_build
from usfs_r1_ea_sources.eval_context_graph import run_eval_context_graph_eval


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH


def test_committed_context_graph_contract_preserves_eval_trace_boundary() -> None:
    contract = load_eval_context_graph_contract()

    assert Path(DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH).is_file()
    assert contract["schema_version"] == "eval-context-graph-contract-v1"
    assert contract["source_store"]["schema_version"] == "system-eval-trace-store-v1"
    assert "trace" in contract["required_node_kinds"]
    assert "span_event" in contract["conditional_node_kinds"]
    assert "log_event" in contract["conditional_node_kinds"]
    assert "EMITTED" in contract["conditional_edge_kinds"]
    assert "span_event" not in contract["reserved_node_kinds"]
    assert "log_event" not in contract["reserved_node_kinds"]
    assert "source_fact" in contract["prohibited_node_kinds"]
    assert contract["graph_policy"]["source_knowledge_graph_excluded"] is True
    assert contract["graph_policy"]["external_export_approved"] is False


def test_context_graph_contract_rejects_source_kg_blending() -> None:
    contract = deepcopy(load_eval_context_graph_contract())
    contract["graph_policy"]["source_knowledge_graph_excluded"] = False

    checks = _checks_by_name(validate_eval_context_graph_contract(contract))

    assert not checks["context_graph_contract_source_kg_excluded"]["passed"]


def test_context_graph_build_writes_generated_graph_from_eval_trace_store(
    tmp_path: Path,
) -> None:
    sqlite_path = _write_store(tmp_path)
    graph_path = tmp_path / "eval_context_graph.json"
    summary_path = tmp_path / "eval_context_graph_build_summary.json"

    result = run_eval_context_graph_build(
        sqlite_path=sqlite_path,
        graph_json_path=graph_path,
        summary_path=summary_path,
        contract_path=CONTRACT_PATH,
        repo_root=tmp_path,
    )
    summary = result.summary

    assert summary["schema_version"] == CONTEXT_GRAPH_BUILD_SUMMARY_SCHEMA_VERSION
    assert summary["passed"] is True
    assert summary["command_succeeded"] is True
    assert summary["row_counts"]["trace_runs"] == 18
    assert summary["row_counts"]["trace_spans"] == 18
    assert summary["node_counts"]["trace"] == 18
    assert summary["node_counts"]["span"] == 18
    assert summary["node_counts"]["eval_result"] == 18
    assert summary["node_counts"]["score"] == 18
    assert summary["node_counts"]["span_event"] == 2
    assert summary["event_node_count"] == 2
    assert summary["event_source_count"] == 2
    assert summary["node_counts"]["artifact"] > 0
    assert summary["edge_counts"]["CONTAINS"] > 0
    assert summary["edge_counts"]["EMITTED"] == 2
    assert summary["edge_counts"]["EVALUATED_BY"] > 0
    assert summary["edge_counts"]["SCORED_AS"] == 18
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert graph["schema_version"] == CONTEXT_GRAPH_SCHEMA_VERSION
    assert graph["graph_policy"]["local_source_of_record"] is True
    assert graph["graph_policy"]["source_knowledge_graph_excluded"] is True
    assert "state_checkpoint" in graph["reserved_node_kinds_not_materialized"]
    assert "span_event" not in graph["reserved_node_kinds_not_materialized"]
    assert all(
        source["row_count"] == source["materialized_event_count"]
        for source in graph["event_sources"]
    )
    assert {node["kind"] for node in graph["nodes"]}.isdisjoint(
        {"authority_fact", "claim_fact", "domain_entity", "source_fact"}
    )
    assert any(edge["kind"] == "USED_ARTIFACT" for edge in graph["edges"])


def test_context_graph_eval_passes_on_generated_graph(tmp_path: Path) -> None:
    graph_path = _write_context_graph(tmp_path)
    summary_path = tmp_path / "eval_context_graph_eval_summary.json"

    result = run_eval_context_graph_eval(
        graph_json_path=graph_path,
        summary_path=summary_path,
        contract_path=CONTRACT_PATH,
        repo_root=tmp_path,
    )
    summary = result.summary

    assert summary["schema_version"] == CONTEXT_GRAPH_EVAL_SUMMARY_SCHEMA_VERSION
    assert summary["passed"] is True
    assert summary["command_succeeded"] is True
    assert _checks_by_name(summary["validation_checks"])[
        "trace_result_score_paths_present"
    ]["passed"]
    assert _checks_by_name(summary["validation_checks"])[
        "event_nodes_emitted_by_spans"
    ]["passed"]
    assert _checks_by_name(summary["validation_checks"])[
        "event_source_rows_materialized"
    ]["passed"]
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary


def test_context_graph_eval_fails_when_result_score_edge_is_missing(
    tmp_path: Path,
) -> None:
    graph_path = _write_context_graph(tmp_path)
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["edges"] = [edge for edge in graph["edges"] if edge["kind"] != "SCORED_AS"]
    graph["edge_counts"]["SCORED_AS"] = 0
    graph_path.write_text(
        json.dumps(graph, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = run_eval_context_graph_eval(
        graph_json_path=graph_path,
        contract_path=CONTRACT_PATH,
        repo_root=tmp_path,
    ).summary

    checks = _checks_by_name(summary["validation_checks"])
    assert summary["passed"] is False
    assert not checks["required_edge_kinds_present"]["passed"]
    assert not checks["trace_result_score_paths_present"]["passed"]
    assert checks["trace_result_score_paths_present"]["failure_count"] == 18


def test_context_graph_eval_fails_when_event_emitted_edge_is_missing(
    tmp_path: Path,
) -> None:
    graph_path = _write_context_graph(tmp_path)
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["edges"] = [edge for edge in graph["edges"] if edge["kind"] != "EMITTED"]
    graph["edge_counts"]["EMITTED"] = 0
    graph_path.write_text(
        json.dumps(graph, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = run_eval_context_graph_eval(
        graph_json_path=graph_path,
        contract_path=CONTRACT_PATH,
        repo_root=tmp_path,
    ).summary

    checks = _checks_by_name(summary["validation_checks"])
    assert summary["passed"] is False
    assert not checks["event_nodes_emitted_by_spans"]["passed"]
    assert checks["event_nodes_emitted_by_spans"]["failure_count"] == 2


def test_context_graph_build_reports_missing_store_without_writing_graph(
    tmp_path: Path,
) -> None:
    graph_path = tmp_path / "eval_context_graph.json"

    summary = run_eval_context_graph_build(
        sqlite_path=tmp_path / "missing.sqlite",
        graph_json_path=graph_path,
        contract_path=CONTRACT_PATH,
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["missing_table_count"] == 6
    assert not graph_path.exists()


def _write_context_graph(tmp_path: Path) -> Path:
    sqlite_path = _write_store(tmp_path)
    graph_path = tmp_path / "eval_context_graph.json"
    result = run_eval_context_graph_build(
        sqlite_path=sqlite_path,
        graph_json_path=graph_path,
        contract_path=CONTRACT_PATH,
        repo_root=tmp_path,
    )
    assert result.summary["passed"] is True
    return graph_path


def _checks_by_name(checks: list[dict]) -> dict[str, dict]:
    return {check["name"]: check for check in checks}
