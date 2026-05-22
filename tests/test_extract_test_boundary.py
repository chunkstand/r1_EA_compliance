from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
SUITE_BUDGETS = {
    "tests/test_extract.py": 650,
    "tests/test_extract_reuse.py": 450,
    "tests/test_extract_pdf_fallbacks.py": 700,
    "tests/test_extract_test_boundary.py": 250,
    "tests/support/extract_fixtures.py": 250,
}
SOURCE_FAMILY_BUDGETS = {
    "src/usfs_r1_ea_sources/extract.py": 400,
    "src/usfs_r1_ea_sources/extract_chunking.py": 250,
    "src/usfs_r1_ea_sources/extract_common.py": 550,
    "src/usfs_r1_ea_sources/extract_docling_support.py": 500,
    "src/usfs_r1_ea_sources/extract_markup_support.py": 500,
    "src/usfs_r1_ea_sources/extract_pdf_support.py": 600,
    "src/usfs_r1_ea_sources/extract_runtime.py": 800,
    "src/usfs_r1_ea_sources/extract_validation.py": 500,
}
SPLIT_SUITES = (
    "tests/test_extract.py",
    "tests/test_extract_reuse.py",
    "tests/test_extract_pdf_fallbacks.py",
)
SENTINEL_OWNERS = {
    "tests/test_extract.py": {
        "test_build_extraction_writes_html_text_chunks_and_manifest_provenance",
    },
    "tests/test_extract_reuse.py": {
        "test_build_extraction_reuses_existing_payload_when_requested",
    },
    "tests/test_extract_pdf_fallbacks.py": {
        "test_build_extraction_uses_pdf_text_fallback_after_docling_timeout",
    },
}


def test_extract_split_line_budgets_are_respected() -> None:
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


def test_extract_source_family_roster_and_line_budgets_are_respected() -> None:
    actual_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for pattern in ("extract.py", "extract_*.py")
        for path in SOURCE_ROOT.glob(pattern)
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
