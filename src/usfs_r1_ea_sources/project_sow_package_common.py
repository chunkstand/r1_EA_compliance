from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _truncate(value: str, max_chars: int) -> str:
    text = str(value).replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _intake_adjudication_summary(intake: dict[str, Any]) -> dict[str, Any]:
    adjudication = intake.get("project_sow_adjudication")
    if not isinstance(adjudication, dict):
        return {
            "adjudication_id": None,
            "decision_counts": {},
            "item_count": 0,
            "status": "not_applied",
        }
    return {
        "adjudication_id": adjudication.get("adjudication_id"),
        "decision_counts": adjudication.get("decision_counts") or {},
        "item_count": int(adjudication.get("item_count") or 0),
        "status": adjudication.get("status") or "applied",
    }

def _source_set_id(authority_inventory: dict[str, Any]) -> str:
    return str(
        authority_inventory.get("source_set", {}).get("source_set_id")
        or authority_inventory.get("source_set_id")
        or "source-set-unspecified"
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Required JSON file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Required JSON file is invalid: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Required JSON file must contain an object: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _resource_area_ids(value: Any) -> set[str]:
    return {_normalize_token(item) for item in _strings(value)}


def _title_from_id(value: str) -> str:
    return value.replace("_", " ").title()


def _searchable_text(value: Any) -> str:
    text = " ".join(_flatten_strings(value)).lower()
    return re.sub(r"\s+", " ", text)


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_flatten_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_flatten_strings(item))
        return strings
    if value is None:
        return []
    return [str(value)]


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _slug(value: str) -> str:
    slug = _normalize_token(value).replace("_", "-")
    return slug or "project"


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"details": details, "name": name, "passed": bool(passed)}


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list | dict):
        return not value
    return False


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _duplicates(values: Any) -> list[str]:
    counts = Counter(value for value in values if value)
    return sorted(value for value, count in counts.items() if count > 1)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
