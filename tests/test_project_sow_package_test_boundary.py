from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE_BUDGETS = {
    "tests/test_project_sow_package.py": 450,
    "tests/test_project_sow_adjudication.py": 500,
    "tests/test_project_sow_intake.py": 500,
    "tests/test_project_sow_package_validation.py": 550,
    "tests/test_project_sow_package_test_boundary.py": 250,
    "tests/support/project_sow_package_fixtures.py": 200,
}
SPLIT_SUITES = (
    "tests/test_project_sow_package.py",
    "tests/test_project_sow_adjudication.py",
    "tests/test_project_sow_intake.py",
    "tests/test_project_sow_package_validation.py",
)
SENTINEL_OWNERS = {
    "tests/test_project_sow_package.py": {
        "test_project_sow_package_generates_land_exchange_resource_scopes",
    },
    "tests/test_project_sow_adjudication.py": {
        "test_project_sow_ea_package_handoff_derives_from_package_json",
    },
    "tests/test_project_sow_intake.py": {
        "test_project_sow_intake_draft_writes_unreviewed_schema_valid_intake",
    },
    "tests/test_project_sow_package_validation.py": {
        "test_project_sow_package_fails_unknown_authority_family",
    },
}


def test_project_sow_split_line_budgets_are_respected() -> None:
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
