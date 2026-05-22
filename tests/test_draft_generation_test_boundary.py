from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
SUITE_BUDGETS = {
    "tests/test_draft_generation.py": 200,
    "tests/test_draft_generation_eval.py": 150,
    "tests/test_draft_generation_test_boundary.py": 250,
    "tests/support/draft_generation_fixtures.py": 500,
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/draft_generation.py": 80,
    "src/usfs_r1_ea_sources/draft_generation_common.py": 300,
    "src/usfs_r1_ea_sources/draft_generation_eval.py": 300,
    "src/usfs_r1_ea_sources/draft_generation_inputs.py": 450,
    "src/usfs_r1_ea_sources/draft_generation_outputs.py": 650,
    "src/usfs_r1_ea_sources/draft_generation_sections.py": 600,
    "src/usfs_r1_ea_sources/draft_generation_traceability.py": 300,
}
SPLIT_SUITES = (
    "tests/test_draft_generation.py",
    "tests/test_draft_generation_eval.py",
)
ALLOWED_TOP_LEVEL_HELPERS = {
    "tests/test_draft_generation.py": {"_read_json"},
    "tests/test_draft_generation_eval.py": {"_read_json"},
}
SENTINEL_OWNERS = {
    "tests/test_draft_generation.py": {
        "test_run_draft_generate_writes_governed_output_family",
    },
    "tests/test_draft_generation_eval.py": {
        "test_draft_generation_eval_runs_fail_closed_fixture_cases",
    },
}


def test_draft_generation_split_line_budgets_are_respected() -> None:
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


def test_draft_generation_source_family_roster_and_line_budgets_are_respected() -> None:
    actual_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in SOURCE_ROOT.glob("draft_generation*.py")
    }

    assert actual_paths == set(SOURCE_FAMILY_BUDGETS)

    oversize = []
    for relative_path, max_lines in SOURCE_FAMILY_BUDGETS.items():
        path = REPO_ROOT / relative_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            oversize.append({"path": relative_path, "line_count": line_count, "max_lines": max_lines})

    assert oversize == []


def test_split_suites_do_not_redefine_top_level_helpers() -> None:
    forbidden_helpers: dict[str, list[str]] = {}

    for relative_path in SPLIT_SUITES:
        tree = _parse_module(REPO_ROOT / relative_path)
        helpers = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
                if node.name not in ALLOWED_TOP_LEVEL_HELPERS.get(relative_path, set()):
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
