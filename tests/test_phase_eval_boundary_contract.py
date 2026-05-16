from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_EVAL_PATH = REPO_ROOT / "src" / "usfs_r1_ea_sources" / "phase_eval.py"
EVIDENCE_GRAPH_PATH = REPO_ROOT / "src" / "usfs_r1_ea_sources" / "evidence_graph.py"
CLI_EVAL_PATH = REPO_ROOT / "src" / "usfs_r1_ea_sources" / "cli_eval.py"
TEST_PHASE_EVAL_PATH = REPO_ROOT / "tests" / "test_phase_eval.py"
TEST_EVIDENCE_GRAPH_PATH = REPO_ROOT / "tests" / "test_evidence_graph.py"
MAX_EVIDENCE_GRAPH_LINES = 2800
MAX_PHASE_EVAL_LINES = 1800
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
FORBIDDEN_EVIDENCE_GRAPH_HELPERS = {
    "_current_queue_item_count",
    "_dict",
    "_dict_list",
    "_extraction_summary_is_complete",
    "_int_from_summary",
    "_read_json",
    "_read_json_if_exists",
    "_read_jsonl",
    "_safe_int",
    "_selector_value",
    "_source_set_id_from_catalog",
    "_utc_now",
    "_write_json",
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
    imported_modules = _imported_modules(EVIDENCE_GRAPH_PATH)
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


def test_phase_eval_no_longer_imports_evidence_graph_helpers() -> None:
    imported_modules = _imported_modules(PHASE_EVAL_PATH)
    assert "evidence_graph" not in imported_modules


def test_evidence_graph_no_longer_defines_moved_helper_family() -> None:
    tree = _parse(EVIDENCE_GRAPH_PATH)
    defined_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }

    assert defined_names.intersection(FORBIDDEN_EVIDENCE_GRAPH_HELPERS) == set()


def test_owner_line_budgets_hold() -> None:
    evidence_graph_lines = len(EVIDENCE_GRAPH_PATH.read_text(encoding="utf-8").splitlines())
    phase_eval_lines = len(PHASE_EVAL_PATH.read_text(encoding="utf-8").splitlines())

    assert evidence_graph_lines <= MAX_EVIDENCE_GRAPH_LINES
    assert phase_eval_lines <= MAX_PHASE_EVAL_LINES


def test_phase_eval_test_owner_exists_and_imports_canonical_owner() -> None:
    assert TEST_PHASE_EVAL_PATH.exists()
    imported_modules = _imported_modules(TEST_PHASE_EVAL_PATH)
    source = TEST_PHASE_EVAL_PATH.read_text(encoding="utf-8")

    assert "phase_eval" in imported_modules
    assert "run_phase_aligned_eval" in source


def test_evidence_graph_test_owner_no_longer_exercises_phase_eval() -> None:
    imported_modules = _imported_modules(TEST_EVIDENCE_GRAPH_PATH)
    source = TEST_EVIDENCE_GRAPH_PATH.read_text(encoding="utf-8")

    assert "phase_eval" not in imported_modules
    assert "replay_context" not in imported_modules
    assert "run_phase_aligned_eval" not in source


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(path: Path) -> set[str]:
    tree = _parse(path)
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            imported_modules.add(node.module.split(".", 1)[0])
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
            and node.module.startswith("usfs_r1_ea_sources.")
        ):
            imported_modules.add(node.module.split(".", 2)[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("usfs_r1_ea_sources."):
                    imported_modules.add(alias.name.split(".", 2)[1])

    return imported_modules
