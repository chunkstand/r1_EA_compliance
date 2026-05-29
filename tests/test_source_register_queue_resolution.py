from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.source_register_queue_resolution import (
    DEFAULT_SOURCE_REGISTER_QUEUE_RESOLUTION_LEDGER_PATH,
    build_source_register_queue_disposition_audit,
    load_source_register_queue_resolution_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
LEDGER_PATH = ROOT / DEFAULT_SOURCE_REGISTER_QUEUE_RESOLUTION_LEDGER_PATH


def test_queue_disposition_audit_matches_current_queue_baseline() -> None:
    result = build_source_register_queue_disposition_audit(CANONICAL_WORKBOOK)

    assert result["validation_passed"] is True
    assert result["queue_row_count"] == 51
    assert result["ledger_entry_count"] == 51
    assert result["current_or_project_applicable_count"] == 49
    assert result["historical_noncurrent_count"] == 2
    assert result["historical_noncurrent_source_ids"] == ["FPS-380", "SUP-007"]
    assert result["blocked_current_or_project_applicable_count"] == 9
    assert result["blocked_current_or_project_applicable_source_ids"] == [
        "FINAL-Q-FLAT-001",
        "FINAL-Q-LOLO-001",
        "FINAL-Q-NPC-001",
        "FOR-012",
        "LEX-Q-001",
        "PROG-011",
        "PROG-012",
        "PROG-013",
        "WILD-ESA-Q001",
    ]
    assert result["resolved_current_or_project_applicable_count"] == 10
    assert result["unresolved_current_or_project_applicable_count"] == 30
    assert result["planned_disposition_counts"] == {
        "forest_specific_example_package": 2,
        "historical_scope_only": 2,
        "named_blocker": 9,
        "promote_direct_file": 34,
        "promote_structured_export": 4,
    }
    assert result["resolution_status_counts"] == {
        "blocked": 9,
        "planned": 32,
        "resolved": 10,
    }


def test_queue_disposition_audit_fails_when_queue_row_missing_from_ledger() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    ledger["entries"] = [
        entry for entry in ledger["entries"] if entry["source_id"] != "FOR-001"
    ]

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["ledger_covers_all_queue_source_ids"]["actual"] == ["FOR-001"]


def test_queue_disposition_audit_fails_when_queue_row_duplicated_in_ledger() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    ledger["entries"].append(dict(ledger["entries"][0]))

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["ledger_source_ids_unique"]["actual"] == ["R1-SCC-Q-CGNF-RATIONALES"]


def test_queue_disposition_audit_fails_when_current_row_lacks_planned_disposition() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    ledger["entries"][0]["planned_disposition"] = ""

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["planned_dispositions_are_valid"]["actual"] == ["R1-SCC-Q-CGNF-RATIONALES"]
    assert checks["current_applicable_rows_have_planned_disposition"]["actual"] == [
        "R1-SCC-Q-CGNF-RATIONALES"
    ]


def test_queue_disposition_audit_fails_when_named_blocker_reference_is_not_a_packet() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    for entry in ledger["entries"]:
        if entry["source_id"] == "PROG-011":
            entry["blocker_packet_reference"] = "docs/DOES_NOT_EXIST.md"
            break

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["named_blocker_rows_reference_existing_packet"]["actual"] == ["PROG-011"]


def test_queue_disposition_audit_fails_when_resolved_promotion_lacks_successor_target() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    for entry in ledger["entries"]:
        if entry["source_id"] == "FINAL-Q-HLC-001":
            entry["target_successor_source_id"] = None
            break

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["resolved_promotions_reference_successor_rows"]["actual"] == [
        "FINAL-Q-HLC-001"
    ]


def test_queue_disposition_audit_fails_when_structured_export_successor_row_is_missing() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    for entry in ledger["entries"]:
        if entry["source_id"] == "R1-SCC-Q-CGNF-RATIONALES":
            entry["target_successor_source_ids"] = ["R1-SCC-CGNF-005", "DOES-NOT-EXIST"]
            break

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["resolved_promotion_successor_rows_exist_in_master"]["actual"] == [
        "R1-SCC-Q-CGNF-RATIONALES"
    ]


def test_queue_disposition_audit_detects_identity_drift() -> None:
    ledger = load_source_register_queue_resolution_ledger(LEDGER_PATH)
    ledger["entries"][0]["source_url"] = "https://example.com/drift"

    result = _run_with_temp_ledger(ledger)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["validation_passed"] is False
    assert checks["queue_identity_matches_ledger"]["actual"] == ["R1-SCC-Q-CGNF-RATIONALES"]
    assert result["drifted_rows"][0]["source_id"] == "R1-SCC-Q-CGNF-RATIONALES"
    assert "source_url" in result["drifted_rows"][0]["fields"]


def _run_with_temp_ledger(ledger: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger_path = Path(tmp_dir) / "ledger.json"
        ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return build_source_register_queue_disposition_audit(
            CANONICAL_WORKBOOK,
            ledger_path=ledger_path,
        )
