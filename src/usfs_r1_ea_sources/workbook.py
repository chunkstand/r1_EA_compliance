from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import load_workbook

from .config import WorkbookConfig
from .overrides import apply_url_overrides, load_url_overrides
from .records import WorkbookSource, normalize_url, slugify


INGEST_LINK_COLUMN = "Official_Link"
FOREST_PLAN_LINK_COLUMN = "Official_Link"
EXCLUSION_LINK_COLUMN = "Link"


def _headers_by_name(sheet, header_row: int) -> dict[str, int]:
    headers: dict[str, int] = {}
    for column in range(1, sheet.max_column + 1):
        value = sheet.cell(header_row, column).value
        if value not in (None, ""):
            headers[str(value)] = column
    return headers


def _row_has_data(sheet, row: int) -> bool:
    return any(sheet.cell(row, column).value not in (None, "") for column in range(1, sheet.max_column + 1))


def _cell(sheet, row: int, headers: dict[str, int], name: str) -> str | None:
    column = headers.get(name)
    if column is None:
        return None
    value = sheet.cell(row, column).value
    if value in (None, ""):
        return None
    return str(value).strip()


def load_excluded_urls(workbook_path: Path, config: WorkbookConfig) -> set[str]:
    workbook = load_workbook(workbook_path, read_only=False, data_only=True)
    if config.exclusion_sheet not in workbook.sheetnames:
        return set()

    sheet = workbook[config.exclusion_sheet]
    headers = _headers_by_name(sheet, config.header_row)
    link_column = headers.get(EXCLUSION_LINK_COLUMN)
    if link_column is None:
        return set()

    urls: set[str] = set()
    for row in range(config.header_row + 1, sheet.max_row + 1):
        value = sheet.cell(row, link_column).value
        if value not in (None, ""):
            urls.add(normalize_url(str(value)))
    return urls


def load_canonical_sources(workbook_path: Path, config: WorkbookConfig) -> list[WorkbookSource]:
    workbook = load_workbook(workbook_path, read_only=False, data_only=True)
    sources: list[WorkbookSource] = []

    for sheet_name in config.canonical_sheets:
        sheet = workbook[sheet_name]
        headers = _headers_by_name(sheet, config.header_row)
        if sheet_name == "Ingest_Checklist":
            sources.extend(_load_ingest_checklist(sheet, headers, config.header_row))
        elif sheet_name == "R1_Forest_Plans":
            sources.extend(_load_forest_plans(sheet, headers, config.header_row))
        else:
            raise ValueError(f"Unsupported canonical sheet: {sheet_name}")

    overrides = load_url_overrides(config.overrides_path)
    return apply_url_overrides(sources, overrides)


def _load_ingest_checklist(sheet, headers: dict[str, int], header_row: int) -> Iterable[WorkbookSource]:
    required = ["ID", "Document / Source", INGEST_LINK_COLUMN]
    missing = [name for name in required if name not in headers]
    if missing:
        raise ValueError(f"Missing required Ingest_Checklist headers: {missing}")

    for row in range(header_row + 1, sheet.max_row + 1):
        if not _row_has_data(sheet, row):
            continue
        source_id = _cell(sheet, row, headers, "ID")
        title = _cell(sheet, row, headers, "Document / Source")
        original_url = _cell(sheet, row, headers, INGEST_LINK_COLUMN)
        if not source_id or not title or not original_url:
            raise ValueError(f"Ingest_Checklist row {row} is missing ID, title, or URL")
        yield WorkbookSource(
            source_record_id=source_id,
            sheet=sheet.title,
            excel_row=row,
            source_id=source_id,
            title=title,
            original_url=original_url,
            effective_url=original_url,
            normalized_url=normalize_url(original_url),
            metadata={
                "ingest_status": _cell(sheet, row, headers, "Ingest_Status"),
                "scope": _cell(sheet, row, headers, "Scope"),
                "layer": _cell(sheet, row, headers, "Layer"),
                "issuer": _cell(sheet, row, headers, "Issuer"),
                "document_type": _cell(sheet, row, headers, "Document_Type"),
                "applies_to": _cell(sheet, row, headers, "Applies_To"),
                "trigger": _cell(sheet, row, headers, "Trigger / When to Apply"),
                "review_engine_checks": _cell(sheet, row, headers, "Review_Engine_Checks"),
                "currentness_notes": _cell(sheet, row, headers, "Currentness / Notes"),
            },
        )


def _load_forest_plans(sheet, headers: dict[str, int], header_row: int) -> Iterable[WorkbookSource]:
    required = ["Unit / Overlay", "Current Document or Source", FOREST_PLAN_LINK_COLUMN]
    missing = [name for name in required if name not in headers]
    if missing:
        raise ValueError(f"Missing required R1_Forest_Plans headers: {missing}")

    seen_unit_rows: dict[str, int] = {}
    for row in range(header_row + 1, sheet.max_row + 1):
        if not _row_has_data(sheet, row):
            continue
        unit = _cell(sheet, row, headers, "Unit / Overlay")
        title = _cell(sheet, row, headers, "Current Document or Source")
        original_url = _cell(sheet, row, headers, FOREST_PLAN_LINK_COLUMN)
        if not unit or not title or not original_url:
            raise ValueError(f"R1_Forest_Plans row {row} is missing unit, title, or URL")
        unit_slug = slugify(unit, max_length=28)
        seen_unit_rows[unit_slug] = seen_unit_rows.get(unit_slug, 0) + 1
        source_id = f"R1PLAN-{unit_slug}-{seen_unit_rows[unit_slug]:02d}"
        yield WorkbookSource(
            source_record_id=source_id,
            sheet=sheet.title,
            excel_row=row,
            source_id=source_id,
            title=title,
            original_url=original_url,
            effective_url=original_url,
            normalized_url=normalize_url(original_url),
            metadata={
                "unit_or_overlay": unit,
                "status_in_apr_2026": _cell(sheet, row, headers, "Status in Apr 2026"),
                "applies_when": _cell(sheet, row, headers, "Applies_When"),
                "review_engine_checks": _cell(sheet, row, headers, "Review_Engine_Checks"),
                "currentness_notes": _cell(sheet, row, headers, "Notes"),
            },
        )
