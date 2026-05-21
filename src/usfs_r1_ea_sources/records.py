from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import hashlib
import json
import re


SOURCE_RECORD_RECONCILIATION_SCHEMA_VERSION = "compliance-source-record-reconciliation-v1"
DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH = Path(
    "config/compliance_source_record_reconciliation_v1.json"
)
SAFE_SOURCE_RECORD_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.query,
            "",
        )
    )


def slugify(value: str, max_length: int = 80) -> str:
    lowered = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return (slug or "source")[:max_length].strip("-")


def reconciled_source_record_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
    reconciliation_path: Path = DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
) -> list[str]:
    values = _normalized_source_record_ids(
        source_record_id=source_record_id,
        source_record_ids=source_record_ids,
    )
    if not values:
        return []
    reconciliation = _load_source_record_reconciliation(reconciliation_path)
    resolved: list[str] = []
    for value in values:
        resolved.append(value)
        resolved.extend(reconciliation["current_by_legacy"].get(value, ()))
    return _deduped_strings(resolved)


def aliased_source_record_ids(
    source_record_ids: list[str] | tuple[str, ...],
    *,
    reconciliation_path: Path = DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
) -> list[str]:
    values = _normalized_source_record_ids(source_record_ids=source_record_ids)
    if not values:
        return []
    reconciliation = _load_source_record_reconciliation(reconciliation_path)
    aliased: list[str] = []
    for value in values:
        aliased.append(value)
        aliased.extend(reconciliation["current_by_legacy"].get(value, ()))
        for legacy_source_record_id in reconciliation["legacy_by_current"].get(value, ()):
            aliased.append(legacy_source_record_id)
            aliased.extend(reconciliation["current_by_legacy"].get(legacy_source_record_id, ()))
    return _deduped_strings(aliased)


@dataclass(frozen=True)
class WorkbookSource:
    source_record_id: str
    sheet: str
    excel_row: int
    source_id: str | None
    title: str
    original_url: str
    effective_url: str
    normalized_url: str
    metadata: dict[str, str | None]


def planned_artifact_path(output_root: Path, source: WorkbookSource) -> Path:
    parsed = urlsplit(source.normalized_url)
    host = slugify(parsed.netloc or "unknown-host", max_length=64)
    title = slugify(source.title, max_length=72)
    short_id = slugify(source.source_id or source.source_record_id, max_length=32)
    return output_root / "artifacts" / "raw" / host / f"{short_id}_{title}.raw"


def _normalized_source_record_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    values: list[str] = []
    if source_record_id is not None:
        values.append(str(source_record_id))
    values.extend(str(value) for value in (source_record_ids or []))
    return _deduped_strings(values)


def _deduped_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


@lru_cache(maxsize=8)
def _load_source_record_reconciliation(path: Path) -> dict[str, dict[str, tuple[str, ...]]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Compliance source-record reconciliation must be a JSON object.")
    if payload.get("schema_version") != SOURCE_RECORD_RECONCILIATION_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported compliance source-record reconciliation schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Compliance source-record reconciliation entries must be a list.")
    current_by_legacy: dict[str, tuple[str, ...]] = {}
    legacy_by_current: dict[str, set[str]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(
                "Compliance source-record reconciliation entry "
                f"{index} must be a JSON object."
            )
        legacy_source_record_id = str(entry.get("legacy_source_record_id") or "").strip()
        if not legacy_source_record_id:
            raise ValueError(
                "Compliance source-record reconciliation entry "
                f"{index} is missing legacy_source_record_id."
            )
        if not SAFE_SOURCE_RECORD_ID_RE.fullmatch(legacy_source_record_id):
            raise ValueError(
                "Compliance source-record reconciliation legacy_source_record_id must be safe: "
                f"{legacy_source_record_id!r}"
            )
        replacement_ids = _deduped_strings(
            [str(value) for value in entry.get("current_source_record_ids", []) or []]
        )
        for replacement_id in replacement_ids:
            if not SAFE_SOURCE_RECORD_ID_RE.fullmatch(replacement_id):
                raise ValueError(
                    "Compliance source-record reconciliation current_source_record_id must be "
                    f"safe: {replacement_id!r}"
                )
            legacy_by_current.setdefault(replacement_id, set()).add(legacy_source_record_id)
        current_by_legacy[legacy_source_record_id] = tuple(replacement_ids)
    return {
        "current_by_legacy": current_by_legacy,
        "legacy_by_current": {
            current_source_record_id: tuple(sorted(legacy_source_record_ids))
            for current_source_record_id, legacy_source_record_ids in legacy_by_current.items()
        },
    }
