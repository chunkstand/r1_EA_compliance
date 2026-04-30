from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
    for item in data.get("overrides", []):
        source_record_id = str(item["source_record_id"]).strip()
        override_url = str(item["override_url"]).strip()
        reason = str(item.get("reason") or "").strip()
        if not source_record_id:
            raise ValueError(f"URL override in {override_path} is missing source_record_id")
        if not override_url:
            raise ValueError(f"URL override for {source_record_id} is missing override_url")
        if not reason:
            raise ValueError(f"URL override for {source_record_id} is missing reason")
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
