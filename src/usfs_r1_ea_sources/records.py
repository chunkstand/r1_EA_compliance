from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import hashlib
import re


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


@dataclass(frozen=True)
class WorkbookSource:
    source_record_id: str
    sheet: str
    excel_row: int
    source_id: str | None
    title: str
    original_url: str
    normalized_url: str
    metadata: dict[str, str | None]


def planned_artifact_path(output_root: Path, source: WorkbookSource) -> Path:
    parsed = urlsplit(source.normalized_url)
    host = slugify(parsed.netloc or "unknown-host", max_length=64)
    title = slugify(source.title, max_length=72)
    short_id = slugify(source.source_id or source.source_record_id, max_length=32)
    return output_root / "artifacts" / "raw" / host / f"{short_id}_{title}.raw"
