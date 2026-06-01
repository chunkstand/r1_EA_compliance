from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.cli import build_parser


def test_eval_context_graph_build_parser_accepts_graph_paths() -> None:
    args = build_parser().parse_args(
        [
            "eval-context-graph-build",
            "--sqlite-path",
            "/tmp/usfs-r1-system-eval-trace.sqlite",
            "--graph-json-path",
            "/tmp/usfs-r1-eval-context-graph.json",
            "--summary-path",
            "/tmp/usfs-r1-eval-context-graph-summary.json",
            "--contract-path",
            "config/context_graph_contract_v1.json",
        ]
    )

    assert args.command == "eval-context-graph-build"
    assert args.sqlite_path == Path("/tmp/usfs-r1-system-eval-trace.sqlite")
    assert args.graph_json_path == Path("/tmp/usfs-r1-eval-context-graph.json")
    assert args.summary_path == Path("/tmp/usfs-r1-eval-context-graph-summary.json")
    assert args.contract_path == Path("config/context_graph_contract_v1.json")


def test_eval_context_graph_eval_parser_accepts_graph_paths() -> None:
    args = build_parser().parse_args(
        [
            "eval-context-graph-eval",
            "--graph-json-path",
            "/tmp/usfs-r1-eval-context-graph.json",
            "--summary-path",
            "/tmp/usfs-r1-eval-context-graph-eval-summary.json",
            "--contract-path",
            "config/context_graph_contract_v1.json",
        ]
    )

    assert args.command == "eval-context-graph-eval"
    assert args.graph_json_path == Path("/tmp/usfs-r1-eval-context-graph.json")
    assert args.summary_path == Path("/tmp/usfs-r1-eval-context-graph-eval-summary.json")
    assert args.contract_path == Path("config/context_graph_contract_v1.json")
