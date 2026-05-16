from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_EVAL_PATH = REPO_ROOT / "src" / "usfs_r1_ea_sources" / "phase_eval.py"
EVIDENCE_GRAPH_PATH = REPO_ROOT / "src" / "usfs_r1_ea_sources" / "evidence_graph.py"
CLI_EVAL_PATH = REPO_ROOT / "src" / "usfs_r1_ea_sources" / "cli_eval.py"
FORBIDDEN_EVIDENCE_GRAPH_IMPORTS = {
    "applicability",
    "compliance",
    "ea_consistency_decision_support",
    "final_qa_certification",
    "nepa_knowledge_graph_export",
    "phase_eval_direct_eval",
    "replay_context",
    "review_packet_index",
}


def test_phase_eval_module_is_the_canonical_owner() -> None:
    tree = _parse(PHASE_EVAL_PATH)
    defined_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }

    assert "PhaseEvalResult" in defined_names
    assert "run_phase_aligned_eval" in defined_names


def test_evidence_graph_no_longer_defines_phase_eval_entrypoints() -> None:
    tree = _parse(EVIDENCE_GRAPH_PATH)
    forbidden_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name in {"PhaseEvalResult", "run_phase_aligned_eval"}
    }

    assert forbidden_names == set()


def test_evidence_graph_no_longer_imports_phase_eval_owner_dependencies() -> None:
    tree = _parse(EVIDENCE_GRAPH_PATH)
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            imported_modules.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("usfs_r1_ea_sources."):
                    imported_modules.add(alias.name.split(".", 2)[1])

    assert imported_modules.intersection(FORBIDDEN_EVIDENCE_GRAPH_IMPORTS) == set()


def test_cli_eval_imports_phase_eval_owner() -> None:
    tree = _parse(CLI_EVAL_PATH)
    imported_from_phase_eval = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level != 1 or node.module != "phase_eval":
            continue
        if any(alias.name == "run_phase_aligned_eval" for alias in node.names):
            imported_from_phase_eval = True

    assert imported_from_phase_eval


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
