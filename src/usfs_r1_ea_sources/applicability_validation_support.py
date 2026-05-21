from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re

from .records import sha256_file


SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def candidate_ids(authority_universe: dict[str, Any]) -> set[str]:
    return candidate_ids_from_records(authority_universe.get("candidate_authorities") or [])


def candidate_ids_from_records(records: list[dict[str, Any]]) -> set[str]:
    return {
        str(record.get("candidate_authority_id") or "")
        for record in records
        if isinstance(record, dict) and record.get("candidate_authority_id")
    }


def partition_ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("candidate_authority_id") or "")
        for row in payload.get("authorities") or []
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }


def decision_status(decision: dict[str, Any]) -> str:
    return str(decision.get("status") or "")


def first_present(*values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None


def records_by_key(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    by_key = {}
    for record in records:
        value = str(record.get(key) or "")
        if value:
            by_key[value] = record
    return by_key


def check(
    name: str,
    passed: bool,
    failures: list[dict[str, Any]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_categories": sorted(
            {
                str(failure.get("failure_category") or "")
                for failure in failures
                if failure.get("failure_category")
            }
        ),
        "failures": failures,
        "details": details,
    }


def failure(
    failure_category: str,
    *,
    candidate_authority_id: str | None = None,
    artifact: str | None = None,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "failure_category": failure_category,
        "candidate_authority_id": candidate_authority_id,
        "artifact": artifact,
        "path": path,
        "details": details or {},
    }


def read_json_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return value


def read_jsonl_if_exists(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return read_jsonl_if_exists(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl_and_hash(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return sha256_file(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def optional_file_sha256(path: Path | None) -> str | None:
    return sha256_file(path) if path is not None and path.exists() else None


def stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{parts[0]}:{digest[:16]}"


def string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def validate_safe_segment(value: str | None, label: str) -> None:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only letters, numbers, dot, underscore, or hyphen.")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
