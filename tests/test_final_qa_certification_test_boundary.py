from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
SUITE_BUDGETS = {
    "tests/test_final_qa_certification.py": 500,
    "tests/test_final_qa_certification_report.py": 300,
    "tests/test_final_qa_certification_validation.py": 250,
    "tests/test_final_qa_certification_test_boundary.py": 250,
    "tests/support/final_qa_certification_fixtures.py": 775,
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/final_qa_certification.py": 80,
    "src/usfs_r1_ea_sources/final_qa_certification_common.py": 250,
    "src/usfs_r1_ea_sources/final_qa_certification_counts.py": 450,
    "src/usfs_r1_ea_sources/final_qa_certification_report.py": 700,
    "src/usfs_r1_ea_sources/final_qa_certification_runtime.py": 600,
    "src/usfs_r1_ea_sources/final_qa_certification_validation.py": 750,
}
SPLIT_SUITES = (
    "tests/test_final_qa_certification.py",
    "tests/test_final_qa_certification_report.py",
    "tests/test_final_qa_certification_validation.py",
)
SENTINEL_OWNERS = {
    "tests/test_final_qa_certification.py": {
        "test_sequence_1_config_owns_sections_gates_counts_and_signoff",
    },
    "tests/test_final_qa_certification_report.py": {
        "test_sequence_2_generator_writes_and_validates_report_family",
    },
    "tests/test_final_qa_certification_validation.py": {
        "test_sequence_2_validate_only_fails_closed_when_packet_missing",
    },
}


def test_final_qa_certification_split_line_budgets_are_respected() -> None:
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


def test_final_qa_certification_source_family_roster_and_line_budgets_are_respected() -> None:
    actual_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in SOURCE_ROOT.glob("final_qa_certification*.py")
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
