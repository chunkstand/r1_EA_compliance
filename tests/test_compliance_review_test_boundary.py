from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_SUITE = REPO_ROOT / "tests" / "test_compliance_review.py"
SUITE_BUDGETS = {
    "tests/test_compliance_review.py": 1400,
    "tests/test_compliance_review_eval.py": 1200,
    "tests/test_compliance_coverage.py": 1200,
    "tests/test_compliance_gold_eval.py": 1200,
    "tests/test_compliance_phase_eval.py": 1200,
    "tests/support/compliance_review_fixtures.py": 1200,
    "tests/support/compliance_component_fixtures.py": 1200,
    "tests/support/compliance_phase_eval_fixtures.py": 1200,
}
FORBIDDEN_CORE_IMPORTS = {
    "run_compliance_review_eval",
    "run_compliance_coverage",
    "run_compliance_gold_eval",
    "run_phase_aligned_eval",
    "build_retrieval_index",
    "build_claim_extraction",
    "build_rule_claim_links",
    "build_forest_plan_component_inventory",
}
CORE_FORBIDDEN_HELPER_PREFIXES = ("_build_", "_write_")
CORE_FORBIDDEN_HELPERS = {"_run_generated_compliance_review"}
SENTINEL_OWNERS = {
    "tests/test_compliance_review.py": {"test_generated_rule_pack_gate_makes_review_reviewer_ready"},
    "tests/test_compliance_review_eval.py": {"test_compliance_review_eval_scores_package_fixtures"},
    "tests/test_compliance_coverage.py": {"test_compliance_coverage_scores_matrix_links_and_eval_cases"},
    "tests/test_compliance_gold_eval.py": {"test_compliance_gold_eval_runs_adjudicated_profiles"},
    "tests/test_compliance_phase_eval.py": {"test_phase_eval_can_include_compliance_review_phase"},
}


def test_compliance_suite_line_budgets_are_respected() -> None:
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


def test_core_suite_forbidden_imports_are_absent() -> None:
    forbidden = []
    tree = _parse_module(CORE_SUITE)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            imported_name = alias.asname or alias.name
            if imported_name in FORBIDDEN_CORE_IMPORTS:
                forbidden.append(imported_name)

    assert forbidden == []


def test_core_suite_no_long_builder_helpers_remain() -> None:
    tree = _parse_module(CORE_SUITE)
    forbidden_helpers = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in CORE_FORBIDDEN_HELPERS or node.name.startswith(CORE_FORBIDDEN_HELPER_PREFIXES):
            forbidden_helpers.append(node.name)

    assert forbidden_helpers == []


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
