from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE_BUDGETS = {
    "tests/test_nepa_knowledge_graph_export.py": 500,
    "tests/test_nepa_knowledge_graph_export_readiness.py": 400,
    "tests/test_nepa_knowledge_graph_export_review.py": 250,
    "tests/test_nepa_knowledge_graph_export_test_boundary.py": 250,
    "tests/support/nepa_knowledge_graph_export_fixtures.py": 700,
    "tests/support/nepa_knowledge_graph_review_fixtures.py": 450,
}
SPLIT_SUITES = (
    "tests/test_nepa_knowledge_graph_export.py",
    "tests/test_nepa_knowledge_graph_export_readiness.py",
    "tests/test_nepa_knowledge_graph_export_review.py",
)
SENTINEL_OWNERS = {
    "tests/test_nepa_knowledge_graph_export.py": {
        "test_nepa_knowledge_graph_export_builds_source_set_graph_from_audited_surfaces",
    },
    "tests/test_nepa_knowledge_graph_export_readiness.py": {
        "test_nepa_knowledge_graph_export_fails_when_promoted_tracking_profile_keeps_placeholder_eval_floor",
    },
    "tests/test_nepa_knowledge_graph_export_review.py": {
        "test_nepa_knowledge_graph_export_builds_review_specific_overlay",
    },
}


def test_nepa_knowledge_graph_export_split_line_budgets_are_respected() -> None:
    oversize = []
    missing = []

    for relative_path, max_lines in SUITE_BUDGETS.items():
        path = REPO_ROOT / relative_path
        if not path.exists():
            missing.append(relative_path)
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            oversize.append({"path": relative_path, "line_count": line_count, "max_lines": max_lines})

    assert missing == []
    assert oversize == []


def test_split_suites_do_not_redefine_top_level_helpers() -> None:
    forbidden_helpers: dict[str, list[str]] = {}

    for relative_path in SPLIT_SUITES:
        tree = _parse_module(REPO_ROOT / relative_path)
        helpers = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
                helpers.append(node.name)
        if helpers:
            forbidden_helpers[relative_path] = helpers

    assert forbidden_helpers == {}


def test_sentinel_tests_live_in_expected_owner_suites() -> None:
    missing = []
    duplicate_owners: dict[str, list[str]] = {}

    suite_tests = {
        relative_path: _test_function_names(REPO_ROOT / relative_path)
        for relative_path in SENTINEL_OWNERS
    }

    for relative_path, expected_tests in SENTINEL_OWNERS.items():
        present = suite_tests[relative_path]
        for test_name in expected_tests:
            if test_name not in present:
                missing.append({"path": relative_path, "test": test_name})
            owners = [
                owner_path
                for owner_path, test_names in suite_tests.items()
                if test_name in test_names
            ]
            if len(owners) != 1:
                duplicate_owners[test_name] = owners

    assert missing == []
    assert duplicate_owners == {}


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _test_function_names(path: Path) -> set[str]:
    tree = _parse_module(path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            names.add(node.name)
    return names
