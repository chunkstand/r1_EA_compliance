from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
SUITE_BUDGETS = {
    "tests/test_forest_plan_resolver.py": 500,
    "tests/test_forest_plan_resolver_scope.py": 800,
    "tests/test_forest_plan_resolver_profiles.py": 700,
    "tests/support/forest_plan_resolver_common.py": 300,
    "tests/support/forest_plan_resolver_custer_fixtures.py": 400,
    "tests/support/forest_plan_resolver_profile_fixtures.py": 450,
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/forest_plan_resolver.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_resolver_location.py": 400,
    "src/usfs_r1_ea_sources/forest_plan_resolver_mentions.py": 400,
    "src/usfs_r1_ea_sources/forest_plan_resolver_models.py": 280,
    "src/usfs_r1_ea_sources/forest_plan_resolver_runtime.py": 320,
    "src/usfs_r1_ea_sources/forest_plan_resolver_scope.py": 400,
    "src/usfs_r1_ea_sources/forest_plan_resolver_validation.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_checks.py": 600,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_io.py": 120,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_models.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_readiness.py": 760,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_runtime.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_summaries.py": 220,
}
SOURCE_FAMILY_PREFIXES = (
    "forest_plan_resolver",
    "forest_plan_source_delta_readiness",
)
SPLIT_SUITES = (
    "tests/test_forest_plan_resolver.py",
    "tests/test_forest_plan_resolver_scope.py",
    "tests/test_forest_plan_resolver_profiles.py",
)
FORBIDDEN_SUITE_HELPER_PREFIXES = ("_build_", "_write_")
SENTINEL_OWNERS = {
    "tests/test_forest_plan_resolver.py": {
        "test_component_inventory_path_writes_evidence_backed_findings_and_queue",
    },
    "tests/test_forest_plan_resolver_scope.py": {
        "test_resolves_custer_gallatin_geographic_and_management_areas",
    },
    "tests/test_forest_plan_resolver_profiles.py": {
        "test_flathead_profile_resolves_project_context_and_currentness_routes",
    },
}


def test_forest_plan_resolver_split_line_budgets_are_respected() -> None:
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


def test_forest_plan_resolver_source_family_roster_and_line_budgets_are_respected() -> None:
    expected_paths = set(SOURCE_FAMILY_BUDGETS)
    actual_paths = _relative_paths_for_prefixes(SOURCE_FAMILY_PREFIXES)

    assert actual_paths == expected_paths

    oversize = []
    for relative_path, max_lines in SOURCE_FAMILY_BUDGETS.items():
        path = REPO_ROOT / relative_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            oversize.append({"path": relative_path, "line_count": line_count, "max_lines": max_lines})

    assert oversize == []


def test_split_suites_do_not_redefine_fixture_builders() -> None:
    forbidden_helpers: dict[str, list[str]] = {}

    for relative_path in SPLIT_SUITES:
        tree = _parse_module(REPO_ROOT / relative_path)
        helpers = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith(
                FORBIDDEN_SUITE_HELPER_PREFIXES
            ):
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


def _relative_paths_for_prefixes(prefixes: tuple[str, ...]) -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for prefix in prefixes
        for path in SOURCE_ROOT.glob(f"{prefix}*.py")
    }
