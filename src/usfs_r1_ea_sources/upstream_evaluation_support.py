from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
import json

from .config import (
    DEFAULT_CONFIG_PATH,
    LEGACY_WORKBOOK_LOADER_CONTRACT,
    load_config,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIED_EXTRACTION_ADMISSION_CONTRACT_SCHEMA_VERSION = (
    "verified-extraction-admission-contract-v0"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _resolve_path(value: Path | str | None) -> Path:
    if value is None:
        raise ValueError("Expected path value")
    path = Path(value)
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def _resolve_case_path(base_dir: Path, value: Path | str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _normalized_case_definitions(*, manifest_dir: Path, case_definitions: list[dict]) -> list[dict]:
    normalized = []
    for case_definition in case_definitions:
        fixture_path = case_definition.get("fixture_path")
        if fixture_path is None:
            normalized.append(dict(case_definition))
            continue
        normalized.append(
            {
                **case_definition,
                "fixture_path": str(_resolve_case_path(manifest_dir, fixture_path)),
            }
        )
    return normalized


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _check_outcome(report: dict, name: str) -> bool | None:
    for check in report.get("checks", []):
        if check.get("name") == name:
            return bool(check.get("passed"))
    return None


def _failed_check_names(report: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in report.get("checks", [])
        if not check.get("passed")
    ]


def _upstream_eval_config(*, loader_contract: str = LEGACY_WORKBOOK_LOADER_CONTRACT):
    config = load_config(REPO_ROOT / DEFAULT_CONFIG_PATH)
    return replace(
        config,
        workbook=replace(
            config.workbook,
            loader_contract=loader_contract,
            overrides_path=None,
        ),
    )
