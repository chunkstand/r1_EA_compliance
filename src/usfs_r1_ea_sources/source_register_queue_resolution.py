from __future__ import annotations

from collections import Counter
from pathlib import Path
import json

from .records import sha256_file
from .source_register import (
    DEFAULT_SOURCE_REGISTER_SHEET_CONTRACT_PATH,
    read_source_register_tables,
)


QUEUE_RESOLUTION_LEDGER_SCHEMA_VERSION = "source-register-queue-resolution-ledger-v1"
QUEUE_DISPOSITION_AUDIT_SCHEMA_VERSION = "source-register-queue-disposition-audit-v1"
DEFAULT_SOURCE_REGISTER_QUEUE_RESOLUTION_LEDGER_PATH = Path(
    "config/source_register_queue_resolution_ledger_v1.json"
)
CURRENT_OR_PROJECT_APPLICABLE = "current_or_project_applicable"
HISTORICAL_NONCURRENT = "historical_noncurrent"
VALID_CURRENTNESS_CLASSES = {
    CURRENT_OR_PROJECT_APPLICABLE,
    HISTORICAL_NONCURRENT,
}
VALID_PLANNED_DISPOSITIONS = {
    "promote_direct_file",
    "promote_structured_export",
    "historical_scope_only",
    "explicit_exclusion",
    "named_blocker",
}
VALID_RESOLUTION_STATUSES = {"planned", "resolved", "blocked"}
EXPECTED_HISTORICAL_SOURCE_IDS = {"FPS-380", "SUP-007"}
IDENTITY_FIELDS = (
    ("excel_row", "__excel_row__"),
    ("document_title", "Document_Title"),
    ("source_url", "Source_URL"),
    ("queue_reason", "Queue_Reason"),
    ("resolution_required", "Resolution_Required"),
)


def load_source_register_queue_resolution_ledger(
    path: Path | str = DEFAULT_SOURCE_REGISTER_QUEUE_RESOLUTION_LEDGER_PATH,
) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != QUEUE_RESOLUTION_LEDGER_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported source-register queue-resolution schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return payload


def build_source_register_queue_disposition_audit(
    workbook_path: Path | str,
    *,
    ledger_path: Path | str = DEFAULT_SOURCE_REGISTER_QUEUE_RESOLUTION_LEDGER_PATH,
    sheet_contract_path: Path | str = DEFAULT_SOURCE_REGISTER_SHEET_CONTRACT_PATH,
) -> dict:
    workbook_path = Path(workbook_path)
    ledger_path = Path(ledger_path)
    ledger = load_source_register_queue_resolution_ledger(ledger_path)
    tables = read_source_register_tables(workbook_path, contract_path=sheet_contract_path)
    master_rows = list((tables.get("Document_Register_Master") or {}).get("rows", []))
    queue_rows = list((tables.get("Direct_File_Capture_Queue") or {}).get("rows", []))
    master_source_ids = {
        source_id
        for source_id in (
            _string_or_none(row.get("Source_ID"))
            for row in master_rows
        )
        if source_id
    }

    queue_source_ids = [_string_or_none(row.get("Source_ID")) for row in queue_rows]
    duplicate_queue_source_ids = _duplicates(queue_source_ids)
    queue_by_source_id = {
        source_id: row
        for row, source_id in zip(queue_rows, queue_source_ids, strict=False)
        if source_id
    }

    entries = list(ledger.get("entries", []))
    entry_source_ids = [_string_or_none(entry.get("source_id")) for entry in entries]
    duplicate_ledger_source_ids = _duplicates(entry_source_ids)
    entry_by_source_id = {
        source_id: entry
        for entry, source_id in zip(entries, entry_source_ids, strict=False)
        if source_id
    }

    missing_source_ids = sorted(set(queue_by_source_id) - set(entry_by_source_id))
    unexpected_source_ids = sorted(set(entry_by_source_id) - set(queue_by_source_id))
    drifted_rows = _drifted_rows(queue_by_source_id, entry_by_source_id)

    invalid_currentness_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) not in VALID_CURRENTNESS_CLASSES
    )
    invalid_planned_disposition_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("planned_disposition")) not in VALID_PLANNED_DISPOSITIONS
    )
    invalid_resolution_status_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("resolution_status")) not in VALID_RESOLUTION_STATUSES
    )
    current_without_planned_disposition = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) == CURRENT_OR_PROJECT_APPLICABLE
        and not _string_or_none(entry.get("planned_disposition"))
    )
    named_blocker_without_reference = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("planned_disposition")) == "named_blocker"
        and not _string_or_none(entry.get("blocker_packet_reference"))
    )
    named_blocker_with_invalid_reference = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("planned_disposition")) == "named_blocker"
        and _string_or_none(entry.get("blocker_packet_reference"))
        and not _blocker_packet_reference_exists(
            _string_or_none(entry.get("blocker_packet_reference")) or "",
            ledger_path=ledger_path,
        )
    )
    invalid_successor_reference_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _has_invalid_successor_reference_format(entry)
    )
    resolved_promotion_source_ids_without_target = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("resolution_status")) == "resolved"
        and _string_or_none(entry.get("planned_disposition"))
        in {"promote_direct_file", "promote_structured_export"}
        and not _successor_source_ids(entry)
    )
    resolved_promotion_source_ids_with_missing_master_target = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("resolution_status")) == "resolved"
        and _string_or_none(entry.get("planned_disposition"))
        in {"promote_direct_file", "promote_structured_export"}
        and any(
            target_source_id not in master_source_ids
            for target_source_id in _successor_source_ids(entry)
        )
    )
    historical_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) == HISTORICAL_NONCURRENT
    )
    historical_without_scope_only = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) == HISTORICAL_NONCURRENT
        and _string_or_none(entry.get("planned_disposition")) != "historical_scope_only"
    )
    unresolved_current_applicable_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) == CURRENT_OR_PROJECT_APPLICABLE
        and _string_or_none(entry.get("resolution_status")) == "planned"
    )
    blocked_current_applicable_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) == CURRENT_OR_PROJECT_APPLICABLE
        and _string_or_none(entry.get("resolution_status")) == "blocked"
    )
    resolved_current_applicable_source_ids = sorted(
        source_id
        for source_id, entry in entry_by_source_id.items()
        if _string_or_none(entry.get("currentness_class")) == CURRENT_OR_PROJECT_APPLICABLE
        and _string_or_none(entry.get("resolution_status")) == "resolved"
    )

    planned_disposition_counts = Counter(
        _string_or_none(entry.get("planned_disposition")) or "<blank>" for entry in entries
    )
    resolution_status_counts = Counter(
        _string_or_none(entry.get("resolution_status")) or "<blank>" for entry in entries
    )
    checks: list[dict[str, object]] = []

    _append_check(
        checks,
        name="queue_source_ids_unique",
        expected=[],
        actual=duplicate_queue_source_ids,
        passed=not duplicate_queue_source_ids,
        details="Direct_File_Capture_Queue Source_ID values must remain unique in the workbook.",
    )
    _append_check(
        checks,
        name="ledger_source_ids_unique",
        expected=[],
        actual=duplicate_ledger_source_ids,
        passed=not duplicate_ledger_source_ids,
        details="Queue-resolution ledger entries must not duplicate Source_ID values.",
    )
    _append_check(
        checks,
        name="ledger_covers_all_queue_source_ids",
        expected=[],
        actual=missing_source_ids,
        passed=not missing_source_ids,
        details="Every workbook queue row must appear exactly once in the queue-resolution ledger.",
    )
    _append_check(
        checks,
        name="ledger_has_no_unexpected_queue_source_ids",
        expected=[],
        actual=unexpected_source_ids,
        passed=not unexpected_source_ids,
        details="The queue-resolution ledger must not carry rows absent from the workbook queue.",
    )
    _append_check(
        checks,
        name="queue_identity_matches_ledger",
        expected=[],
        actual=[row["source_id"] for row in drifted_rows],
        passed=not drifted_rows,
        details="Queue identity fields must match between the workbook and the ledger snapshot.",
    )
    _append_check(
        checks,
        name="currentness_classes_are_valid",
        expected=sorted(VALID_CURRENTNESS_CLASSES),
        actual=invalid_currentness_source_ids,
        passed=not invalid_currentness_source_ids,
        details="Every ledger entry must use a governed currentness class.",
    )
    _append_check(
        checks,
        name="planned_dispositions_are_valid",
        expected=sorted(VALID_PLANNED_DISPOSITIONS),
        actual=invalid_planned_disposition_source_ids,
        passed=not invalid_planned_disposition_source_ids,
        details="Every ledger entry must use a governed planned disposition.",
    )
    _append_check(
        checks,
        name="resolution_statuses_are_valid",
        expected=sorted(VALID_RESOLUTION_STATUSES),
        actual=invalid_resolution_status_source_ids,
        passed=not invalid_resolution_status_source_ids,
        details="Every ledger entry must use a governed resolution status.",
    )
    _append_check(
        checks,
        name="current_applicable_rows_have_planned_disposition",
        expected=[],
        actual=current_without_planned_disposition,
        passed=not current_without_planned_disposition,
        details="Current or project-applicable queue rows must carry a planned disposition.",
    )
    _append_check(
        checks,
        name="named_blocker_rows_have_reference",
        expected=[],
        actual=named_blocker_without_reference,
        passed=not named_blocker_without_reference,
        details="Named blocker rows must carry a blocker reference in the ledger.",
    )
    _append_check(
        checks,
        name="named_blocker_rows_reference_existing_packet",
        expected=[],
        actual=named_blocker_with_invalid_reference,
        passed=not named_blocker_with_invalid_reference,
        details=(
            "Named blocker rows must reference an existing tracked blocker packet under docs/."
        ),
    )
    _append_check(
        checks,
        name="successor_reference_fields_are_valid",
        expected=[],
        actual=invalid_successor_reference_source_ids,
        passed=not invalid_successor_reference_source_ids,
        details=(
            "Queue-resolution ledger successor fields must use either a single target_successor_source_id "
            "or a non-empty target_successor_source_ids list."
        ),
    )
    _append_check(
        checks,
        name="resolved_promotions_reference_successor_rows",
        expected=[],
        actual=resolved_promotion_source_ids_without_target,
        passed=not resolved_promotion_source_ids_without_target,
        details=(
            "Resolved direct-file or structured-export promotions must reference their promoted "
            "Document_Register_Master successor rows."
        ),
    )
    _append_check(
        checks,
        name="resolved_promotion_successor_rows_exist_in_master",
        expected=[],
        actual=resolved_promotion_source_ids_with_missing_master_target,
        passed=not resolved_promotion_source_ids_with_missing_master_target,
        details=(
            "Resolved promotion successor rows must exist in Document_Register_Master."
        ),
    )
    _append_check(
        checks,
        name="historical_noncurrent_baseline_matches_expected_ids",
        expected=sorted(EXPECTED_HISTORICAL_SOURCE_IDS),
        actual=historical_source_ids,
        passed=set(historical_source_ids) == EXPECTED_HISTORICAL_SOURCE_IDS,
        details="The governed historical queue baseline must remain FPS-380 and SUP-007 only.",
    )
    _append_check(
        checks,
        name="historical_rows_route_to_historical_scope_only",
        expected=[],
        actual=historical_without_scope_only,
        passed=not historical_without_scope_only,
        details="Historical queue rows must not be routed as current direct-file promotions.",
    )

    validation_passed = all(check["passed"] for check in checks)
    return {
        "schema_version": QUEUE_DISPOSITION_AUDIT_SCHEMA_VERSION,
        "workbook_path": str(workbook_path),
        "workbook_sha256": sha256_file(workbook_path),
        "ledger_path": str(ledger_path),
        "ledger_sha256": sha256_file(ledger_path),
        "queue_row_count": len(queue_rows),
        "ledger_entry_count": len(entries),
        "current_or_project_applicable_count": sum(
            1
            for entry in entries
            if _string_or_none(entry.get("currentness_class")) == CURRENT_OR_PROJECT_APPLICABLE
        ),
        "historical_noncurrent_count": len(historical_source_ids),
        "historical_noncurrent_source_ids": historical_source_ids,
        "blocked_current_or_project_applicable_count": len(blocked_current_applicable_source_ids),
        "blocked_current_or_project_applicable_source_ids": blocked_current_applicable_source_ids,
        "resolved_current_or_project_applicable_count": len(resolved_current_applicable_source_ids),
        "resolved_current_or_project_applicable_source_ids": resolved_current_applicable_source_ids,
        "unresolved_current_or_project_applicable_count": len(
            unresolved_current_applicable_source_ids
        ),
        "unresolved_current_or_project_applicable_source_ids": (
            unresolved_current_applicable_source_ids
        ),
        "planned_disposition_counts": dict(planned_disposition_counts),
        "resolution_status_counts": dict(resolution_status_counts),
        "missing_source_ids": missing_source_ids,
        "unexpected_source_ids": unexpected_source_ids,
        "duplicate_ledger_source_ids": duplicate_ledger_source_ids,
        "drifted_rows": drifted_rows,
        "checks": checks,
        "validation_passed": validation_passed,
    }


def _drifted_rows(
    queue_by_source_id: dict[str, dict[str, object]],
    entry_by_source_id: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    drifted_rows: list[dict[str, object]] = []
    for source_id in sorted(set(queue_by_source_id) & set(entry_by_source_id)):
        row = queue_by_source_id[source_id]
        entry = entry_by_source_id[source_id]
        mismatches: dict[str, dict[str, object]] = {}
        for ledger_field, workbook_field in IDENTITY_FIELDS:
            ledger_value = _identity_value(entry.get(ledger_field))
            workbook_value = _identity_value(row.get(workbook_field))
            if ledger_value != workbook_value:
                mismatches[ledger_field] = {
                    "ledger": ledger_value,
                    "workbook": workbook_value,
                }
        if mismatches:
            drifted_rows.append({"source_id": source_id, "fields": mismatches})
    return drifted_rows


def _identity_value(value: object) -> int | str | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _string_or_none(value: object) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _duplicates(values: list[str | None]) -> list[str]:
    counts = Counter(value for value in values if value)
    return sorted(value for value, count in counts.items() if count > 1)


def _append_check(
    checks: list[dict[str, object]],
    *,
    name: str,
    expected: object,
    actual: object,
    passed: bool,
    details: str,
) -> None:
    checks.append(
        {
            "name": name,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "details": details,
        }
    )


def _blocker_packet_reference_exists(reference: str, *, ledger_path: Path) -> bool:
    text = reference.strip()
    if not text:
        return False
    reference_path = Path(text)
    if reference_path.suffix.lower() != ".md":
        return False
    if not str(reference_path).startswith("docs/"):
        return False
    if reference_path.is_absolute():
        return reference_path.exists()
    candidates = (
        Path.cwd() / reference_path,
        ledger_path.resolve().parent.parent / reference_path,
    )
    return any(candidate.exists() for candidate in candidates)


def _successor_source_ids(entry: dict[str, object]) -> list[str]:
    raw_multiple = entry.get("target_successor_source_ids")
    if raw_multiple is not None:
        if not isinstance(raw_multiple, list):
            return []
        return [
            source_id
            for source_id in (_string_or_none(value) for value in raw_multiple)
            if source_id
        ]
    single = _string_or_none(entry.get("target_successor_source_id"))
    return [single] if single else []


def _has_invalid_successor_reference_format(entry: dict[str, object]) -> bool:
    raw_multiple = entry.get("target_successor_source_ids")
    if raw_multiple is None:
        return False
    if not isinstance(raw_multiple, list) or not raw_multiple:
        return True
    return any(_string_or_none(value) is None for value in raw_multiple)
