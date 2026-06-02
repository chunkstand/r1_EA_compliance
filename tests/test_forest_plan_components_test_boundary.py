from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
SUITE_BUDGETS = {
    "tests/test_forest_plan_components.py": 550,
    "tests/test_forest_plan_components_inventory.py": 700,
    "tests/test_forest_plan_components_coverage.py": 350,
    "tests/test_forest_plan_components_manifest.py": 450,
    "tests/test_forest_plan_components_test_boundary.py": 275,
    "tests/support/forest_plan_component_fixtures.py": 200,
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/forest_plan_components.py": 120,
    "src/usfs_r1_ea_sources/forest_plan_components_common.py": 225,
    "src/usfs_r1_ea_sources/forest_plan_components_coverage.py": 500,
    "src/usfs_r1_ea_sources/forest_plan_components_determination.py": 650,
    "src/usfs_r1_ea_sources/forest_plan_components_inventory_build.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_components_inventory_common.py": 180,
    "src/usfs_r1_ea_sources/forest_plan_components_inventory_detection.py": 460,
    "src/usfs_r1_ea_sources/forest_plan_components_inventory_legacy.py": 320,
    "src/usfs_r1_ea_sources/forest_plan_components_inventory_quality.py": 750,
    "src/usfs_r1_ea_sources/forest_plan_components_models.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_components_package_search.py": 650,
    "src/usfs_r1_ea_sources/forest_plan_components_runtime.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_components_validation.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_component_adjudication.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_component_adjudication_common.py": 260,
    "src/usfs_r1_ea_sources/forest_plan_component_adjudication_eval.py": 500,
    "src/usfs_r1_ea_sources/forest_plan_component_adjudication_models.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_component_adjudication_runtime.py": 240,
    "src/usfs_r1_ea_sources/forest_plan_component_adjudication_template.py": 240,
    "src/usfs_r1_ea_sources/forest_plan_component_eval.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_component_eval_cases.py": 450,
    "src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py": 800,
    "src/usfs_r1_ea_sources/forest_plan_component_eval_models.py": 80,
    "src/usfs_r1_ea_sources/forest_plan_component_eval_runtime.py": 260,
    "src/usfs_r1_ea_sources/forest_plan_component_eval_validation.py": 360,
}
SOURCE_FAMILY_PREFIXES = (
    "forest_plan_components",
    "forest_plan_component_adjudication",
    "forest_plan_component_eval",
)
SPLIT_SUITES = (
    "tests/test_forest_plan_components.py",
    "tests/test_forest_plan_components_inventory.py",
    "tests/test_forest_plan_components_coverage.py",
    "tests/test_forest_plan_components_manifest.py",
)
SENTINEL_OWNERS = {
    "tests/test_forest_plan_components.py": {
        "test_component_package_search_is_section_aware_and_filters_negative_rows",
    },
    "tests/test_forest_plan_components_inventory.py": {
        "test_builds_labeled_component_inventory_from_forest_plan_chunks",
    },
    "tests/test_forest_plan_components_coverage.py": {
        "test_duplicate_standard_labels_fail_build_coverage",
    },
    "tests/test_forest_plan_components_manifest.py": {
        "test_manifest_build_writes_multi_forest_inventory_and_aggregate_coverage",
    },
}


def test_forest_plan_component_split_line_budgets_are_respected() -> None:
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


def test_forest_plan_component_source_family_roster_and_line_budgets_are_respected() -> None:
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


def _relative_paths_for_prefixes(prefixes: tuple[str, ...]) -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for prefix in prefixes
        for path in SOURCE_ROOT.glob(f"{prefix}*.py")
    }
