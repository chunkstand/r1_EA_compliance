from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


def _extraction_summary_is_complete(extraction_summary: dict | None) -> bool:
    if not extraction_summary:
        return False
    catalog_count = _int_from_summary(extraction_summary, "catalog_source_count")
    selected_count = _int_from_summary(extraction_summary, "selected_source_count")
    extracted_count = _int_from_summary(extraction_summary, "extracted_count")
    failed_count = _int_from_summary(extraction_summary, "failed_count")
    required_count = (
        _int_from_summary(extraction_summary, "required_extraction_source_count")
        or catalog_count
    )
    selected_required_count = (
        _int_from_summary(extraction_summary, "selected_required_extraction_source_count")
        or selected_count
    )
    filters = extraction_summary.get("filters") or {}
    active_filters = [value for value in filters.values() if value not in (None, "", [])]
    return (
        catalog_count > 0
        and not active_filters
        and selected_count == catalog_count
        and selected_required_count == required_count
        and extracted_count == required_count
        and failed_count == 0
    )


def _int_from_summary(summary: dict | None, key: str) -> int:
    if not summary:
        return 0
    try:
        return int(summary.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _selector_value(data: Any, selector: str) -> Any:
    current = data
    for part in selector.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    source_set_id = manifest.get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
