from __future__ import annotations

import ast
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "docs" / "architecture_contract.toml"
SOURCE_ROOT = REPO_ROOT / "src" / "usfs_r1_ea_sources"


def test_architecture_contract_covers_source_modules() -> None:
    contract = _load_contract()
    layer_by_module = _layer_by_module(contract)
    source_modules = _source_modules()

    missing = sorted(source_modules - set(layer_by_module))
    extra = sorted(set(layer_by_module) - source_modules)

    assert missing == []
    assert extra == []


def test_architecture_contract_uses_valid_layer_names() -> None:
    contract = _load_contract()
    layer_names = {layer["name"] for layer in contract["layers"]}

    unknown_allowed_layers = sorted(
        {
            allowed
            for layer in contract["layers"]
            for allowed in layer.get("allowed_import_layers", [])
            if allowed not in layer_names
        }
    )
    unknown_artifact_layers = sorted(
        {
            artifact["owner_layer"]
            for artifact in contract.get("artifacts", [])
            if artifact["owner_layer"] not in layer_names
        }
    )

    assert unknown_allowed_layers == []
    assert unknown_artifact_layers == []


def test_temporary_exceptions_are_owned_and_scheduled() -> None:
    contract = _load_contract()

    incomplete = [
        exception.get("id", "<missing-id>")
        for exception in contract.get("temporary_exceptions", [])
        if not exception.get("owner") or not exception.get("remove_by") or not exception.get("reason")
    ]

    assert incomplete == []


def test_source_imports_follow_architecture_contract() -> None:
    contract = _load_contract()
    imports = _source_imports()
    layer_by_module = _layer_by_module(contract)
    allowed_layers_by_layer = {
        layer["name"]: set(layer.get("allowed_import_layers", [])) for layer in contract["layers"]
    }
    dependency_exceptions = {
        (exception["from_module"], exception["to_module"])
        for exception in contract.get("temporary_exceptions", [])
        if exception.get("kind") == "dependency"
    }

    violations = []
    for importer, imported_modules in sorted(imports.items()):
        importer_layer = layer_by_module[importer]
        allowed_layers = allowed_layers_by_layer[importer_layer]
        for imported in sorted(imported_modules):
            imported_layer = layer_by_module[imported]
            if imported_layer in allowed_layers:
                continue
            if (importer, imported) in dependency_exceptions:
                continue
            violations.append(
                {
                    "importer": importer,
                    "importer_layer": importer_layer,
                    "imported": imported,
                    "imported_layer": imported_layer,
                }
            )

    assert violations == []


def test_source_import_cycles_are_explicit_contract_exceptions() -> None:
    contract = _load_contract()
    imports = _source_imports()
    cycle_exceptions = {
        frozenset(exception["modules"])
        for exception in contract.get("temporary_exceptions", [])
        if exception.get("kind") == "cycle"
    }
    cycles = _find_cycles(imports)

    unexpected_cycles = [
        cycle for cycle in cycles if frozenset(cycle[:-1]) not in cycle_exceptions
    ]
    stale_cycle_exceptions = sorted(
        sorted(exception)
        for exception in cycle_exceptions
        if all(frozenset(cycle[:-1]) != exception for cycle in cycles)
    )

    assert unexpected_cycles == []
    assert stale_cycle_exceptions == []


def _load_contract() -> dict:
    return tomllib.loads(CONTRACT_PATH.read_text())


def _source_modules() -> set[str]:
    return {path.stem for path in SOURCE_ROOT.glob("*.py")}


def _layer_by_module(contract: dict) -> dict[str, str]:
    layer_by_module: dict[str, str] = {}
    duplicate_modules = []
    for layer in contract["layers"]:
        for module in layer.get("modules", []):
            if module in layer_by_module:
                duplicate_modules.append(module)
            layer_by_module[module] = layer["name"]

    assert duplicate_modules == []
    return layer_by_module


def _source_imports() -> dict[str, set[str]]:
    modules = _source_modules()
    imports: dict[str, set[str]] = {module: set() for module in modules}
    for module in modules:
        path = SOURCE_ROOT / f"{module}.py"
        tree = ast.parse(path.read_text(), filename=str(path))
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


def _find_cycles(imports: dict[str, set[str]]) -> list[list[str]]:
    cycles: set[tuple[str, ...]] = set()
    path: list[str] = []
    in_stack: set[str] = set()

    def visit(module: str) -> None:
        path.append(module)
        in_stack.add(module)
        for imported in sorted(imports[module]):
            if imported in in_stack:
                start = path.index(imported)
                cycle = path[start:] + [imported]
                cycles.add(_canonical_cycle(cycle))
            else:
                visit(imported)
        in_stack.remove(module)
        path.pop()

    for module in sorted(imports):
        visit(module)

    return [list(cycle) for cycle in sorted(cycles)]


def _canonical_cycle(cycle: list[str]) -> tuple[str, ...]:
    cycle_without_repeat = cycle[:-1]
    rotations = []
    for index, module in enumerate(cycle_without_repeat):
        rotated = cycle_without_repeat[index:] + cycle_without_repeat[:index] + [module]
        rotations.append(tuple(rotated))
    return min(rotations)
