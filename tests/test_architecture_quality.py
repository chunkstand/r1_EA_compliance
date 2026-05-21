from __future__ import annotations

import ast
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"
CODE_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
    REPO_ROOT / "viewer",
)
CODE_GLOBS = ("*.py", "*.js")
MAX_REVIEWABLE_LINES = 800
MAX_ALLOWED_OVERSIZED_FILES = 32
MAX_ALLOWED_FAN_OUT = 20
ALLOWED_HIGH_FAN_OUT_MODULES: set[str] = set()


def test_large_file_count_does_not_grow() -> None:
    oversized = [
        path.relative_to(REPO_ROOT)
        for path in _code_paths()
        if len(path.read_text(encoding="utf-8").splitlines()) > MAX_REVIEWABLE_LINES
    ]

    assert len(oversized) <= MAX_ALLOWED_OVERSIZED_FILES


def test_no_new_high_fan_out_modules() -> None:
    over_limit = {
        module: len(imports)
        for module, imports in _source_imports().items()
        if len(imports) > MAX_ALLOWED_FAN_OUT
    }

    assert set(over_limit).issubset(ALLOWED_HIGH_FAN_OUT_MODULES)


def test_architecture_doc_path_stays_canonical() -> None:
    result = subprocess.run(
        ["git", "ls-files", "docs/ARCHITECTURE.md", "docs/architecture.md"],
        check=True,
        capture_output=True,
        cwd=REPO_ROOT,
        text=True,
    )
    tracked_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    assert tracked_paths == ["docs/ARCHITECTURE.md"]
    architecture_doc = REPO_ROOT / "docs" / "ARCHITECTURE.md"
    assert architecture_doc.exists()
    assert "Canonical architecture doc path: `docs/ARCHITECTURE.md`" in architecture_doc.read_text(
        encoding="utf-8"
    )


def _code_paths() -> list[Path]:
    paths: list[Path] = []
    for root in CODE_ROOTS:
        if not root.exists():
            continue
        for pattern in CODE_GLOBS:
            paths.extend(sorted(root.rglob(pattern)))
    return paths


def _source_modules() -> set[str]:
    return {path.stem for path in SOURCE_ROOT.glob("*.py")}


def _source_imports() -> dict[str, set[str]]:
    modules = _source_modules()
    imports: dict[str, set[str]] = {module: set() for module in modules}
    for module in modules:
        path = SOURCE_ROOT / f"{module}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports[module].update(_relative_import_targets(node, modules))
            elif isinstance(node, ast.Import):
                imports[module].update(_absolute_import_targets(node, modules))
    return imports


def _relative_import_targets(node: ast.ImportFrom, modules: set[str]) -> set[str]:
    if node.level != 1:
        return set()
    if node.module:
        target = node.module.split(".", 1)[0]
        return {target} if target in modules else set()
    return {alias.name.split(".", 1)[0] for alias in node.names if alias.name in modules}


def _absolute_import_targets(node: ast.Import, modules: set[str]) -> set[str]:
    package_prefix = "usfs_r1_ea_sources."
    targets = set()
    for alias in node.names:
        if alias.name.startswith(package_prefix):
            target = alias.name[len(package_prefix) :].split(".", 1)[0]
            if target in modules:
                targets.add(target)
    return targets
