from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUITE_BUDGETS = {
    "tests/test_ea_consistency_decision_support.py": 400,
    "tests/test_ea_consistency_decision_support_report.py": 250,
    "tests/test_ea_consistency_decision_support_validation.py": 350,
    "tests/test_ea_consistency_decision_support_test_boundary.py": 250,
    "tests/support/ea_consistency_decision_support_fixtures.py": 650,
}
SPLIT_SUITES = (
    "tests/test_ea_consistency_decision_support.py",
    "tests/test_ea_consistency_decision_support_report.py",
    "tests/test_ea_consistency_decision_support_validation.py",
)
SENTINEL_OWNERS = {
    "tests/test_ea_consistency_decision_support.py": {
        "test_sequence_1_config_owns_sections_confirmations_and_eval_expectations",
    },
    "tests/test_ea_consistency_decision_support_report.py": {
        "test_sequence_2_generator_writes_canonical_report_family",
    },
    "tests/test_ea_consistency_decision_support_validation.py": {
        "test_sequence_4_validation_gate_accepts_current_generated_report_family",
    },
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/ea_consistency_decision_support.py": 200,
    "src/usfs_r1_ea_sources/ea_consistency_decision_support_inputs.py": 800,
    "src/usfs_r1_ea_sources/ea_consistency_decision_support_models.py": 300,
    "src/usfs_r1_ea_sources/ea_consistency_decision_support_rendering.py": 700,
    "src/usfs_r1_ea_sources/ea_consistency_decision_support_report.py": 750,
    "src/usfs_r1_ea_sources/ea_consistency_decision_support_report_validation.py": 800,
    "src/usfs_r1_ea_sources/ea_consistency_decision_support_runtime.py": 300,
}


def test_ea_consistency_decision_support_split_line_budgets_are_respected() -> None:
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


def test_ea_consistency_decision_support_source_family_modules_stay_bounded_and_explicit() -> None:
    actual_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "src" / "usfs_r1_ea_sources").glob(
            "ea_consistency_decision_support*.py"
        )
    }

    assert actual_paths == set(SOURCE_FAMILY_BUDGETS)

    oversize = []
    for relative_path, max_lines in SOURCE_FAMILY_BUDGETS.items():
        path = REPO_ROOT / relative_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            oversize.append({"path": relative_path, "line_count": line_count, "max_lines": max_lines})

    assert oversize == []


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _test_function_names(path: Path) -> set[str]:
    tree = _parse_module(path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            names.add(node.name)
    return names
