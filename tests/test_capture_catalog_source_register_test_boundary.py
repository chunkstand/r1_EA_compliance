from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
SUITE_BUDGETS = {
    "tests/test_catalog.py": 800,
    "tests/test_authority_currentness.py": 700,
    "tests/test_source_register_proving.py": 100,
    "tests/test_source_register_loader.py": 200,
    "tests/test_source_register_schema.py": 200,
    "tests/test_download.py": 450,
    "tests/test_preflight.py": 400,
    "tests/test_capture_catalog_source_register_test_boundary.py": 260,
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/catalog.py": 800,
    "src/usfs_r1_ea_sources/catalog_outputs.py": 750,
    "src/usfs_r1_ea_sources/authority_currentness.py": 700,
    "src/usfs_r1_ea_sources/authority_currentness_projection.py": 500,
    "src/usfs_r1_ea_sources/authority_currentness_validation.py": 450,
    "src/usfs_r1_ea_sources/source_register.py": 780,
    "src/usfs_r1_ea_sources/source_register_validation.py": 500,
    "src/usfs_r1_ea_sources/source_register_proving.py": 780,
    "src/usfs_r1_ea_sources/source_register_proving_graph.py": 500,
    "src/usfs_r1_ea_sources/download.py": 700,
    "src/usfs_r1_ea_sources/download_transport.py": 400,
    "src/usfs_r1_ea_sources/preflight.py": 450,
    "src/usfs_r1_ea_sources/preflight_transport.py": 650,
}
SOURCE_FAMILY_PATTERNS = (
    "catalog.py",
    "catalog_outputs.py",
    "authority_currentness*.py",
    "source_register.py",
    "source_register_validation.py",
    "source_register_proving*.py",
    "download*.py",
    "preflight*.py",
)
SENTINEL_OWNERS = {
    "tests/test_catalog.py": {
        "test_build_review_catalog_writes_engine_artifacts",
    },
    "tests/test_authority_currentness.py": {
        "test_canonical_source_register_projection_builds_projected_inputs_and_lineage",
    },
    "tests/test_source_register_proving.py": {
        "test_source_register_proving_slice_builds_report_and_currentness_inputs",
    },
    "tests/test_source_register_loader.py": {
        "test_source_register_loader_dispatch_returns_workbook_source_compatibility_rows",
    },
    "tests/test_source_register_schema.py": {
        "test_validate_source_register_passes_for_final_workbook",
    },
    "tests/test_download.py": {
        "test_download_writes_artifacts_hashes_and_preserves_duplicate_url_rows",
    },
    "tests/test_preflight.py": {
        "test_preflight_fetches_each_unique_url_once_and_preserves_duplicate_rows",
    },
}


def test_capture_catalog_source_register_split_line_budgets_are_respected() -> None:
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


def test_capture_catalog_source_register_source_family_roster_and_line_budgets_are_respected() -> None:
    expected_paths = set(SOURCE_FAMILY_BUDGETS)
    actual_paths = _relative_paths_for_patterns(SOURCE_FAMILY_PATTERNS)

    assert actual_paths == expected_paths

    oversize = []
    for relative_path, max_lines in SOURCE_FAMILY_BUDGETS.items():
        path = REPO_ROOT / relative_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            oversize.append({"path": relative_path, "line_count": line_count, "max_lines": max_lines})

    assert oversize == []


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


def _relative_paths_for_patterns(patterns: tuple[str, ...]) -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for pattern in patterns
        for path in SOURCE_ROOT.glob(pattern)
    }
