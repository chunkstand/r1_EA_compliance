from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import tomllib

from .records import WorkbookSource, normalize_url


@dataclass(frozen=True)
class URLOverride:
    source_record_id: str
    override_url: str
    reason: str


def load_url_overrides(path: Path | str | None) -> dict[str, URLOverride]:
    if path is None:
        return {}
    override_path = Path(path)
    if not override_path.exists():
        return {}
    data = tomllib.loads(override_path.read_text(encoding="utf-8"))
    overrides: dict[str, URLOverride] = {}
    override_items = data.get("overrides", [])
    if not isinstance(override_items, list):
        raise ValueError(f"URL overrides in {override_path} must use [[overrides]] table entries")
    for item in override_items:
        source_record_id = str(item.get("source_record_id") or "").strip()
        override_url = str(item.get("override_url") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not source_record_id:
            raise ValueError(f"URL override in {override_path} is missing source_record_id")
        if not override_url:
            raise ValueError(f"URL override for {source_record_id} is missing override_url")
        if not reason:
            raise ValueError(f"URL override for {source_record_id} is missing reason")
        _validate_override_url(source_record_id, override_url)
        if source_record_id in overrides:
            raise ValueError(f"Duplicate URL override for {source_record_id}")
        overrides[source_record_id] = URLOverride(
            source_record_id=source_record_id,
            override_url=override_url,
            reason=reason,
        )
    return overrides


def apply_url_overrides(
    sources: list[WorkbookSource],
    overrides: dict[str, URLOverride],
) -> list[WorkbookSource]:
    if not overrides:
        return sources
    source_ids = {source.source_record_id for source in sources}
    unknown = sorted(set(overrides) - source_ids)
    if unknown:
        raise ValueError(f"URL overrides reference unknown source_record_id values: {unknown}")
    return [_apply_override(source, overrides.get(source.source_record_id)) for source in sources]


def validate_overrides_do_not_target_exclusions(
    sources: list[WorkbookSource],
    excluded_urls: set[str],
) -> None:
    violations = [
        source.source_record_id
        for source in sources
        if source.metadata.get("override_url") and source.normalized_url in excluded_urls
    ]
    if violations:
        raise ValueError(
            "URL overrides target excluded URLs for source_record_id values: "
            + ", ".join(sorted(violations))
        )


def _apply_override(source: WorkbookSource, override: URLOverride | None) -> WorkbookSource:
    if override is None:
        return source
    metadata = dict(source.metadata)
    metadata["workbook_url"] = source.original_url
    metadata["override_url"] = override.override_url
    metadata["override_reason"] = override.reason
    return WorkbookSource(
        source_record_id=source.source_record_id,
        sheet=source.sheet,
        excel_row=source.excel_row,
        source_id=source.source_id,
        title=source.title,
        original_url=source.original_url,
        effective_url=override.override_url,
        normalized_url=normalize_url(override.override_url),
        metadata=metadata,
    )


def _validate_override_url(source_record_id: str, override_url: str) -> None:
    parsed = urlsplit(override_url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError(
            f"URL override for {source_record_id} must use http or https: {override_url}"
        )
    if not parsed.netloc:
        raise ValueError(f"URL override for {source_record_id} is missing a host: {override_url}")
