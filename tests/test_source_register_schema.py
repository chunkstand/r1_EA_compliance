from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from openpyxl import load_workbook

from usfs_r1_ea_sources.source_register import build_source_register_diff
from usfs_r1_ea_sources.source_register import validate_source_register


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
LEGACY_WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
LEGACY_REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"


class SourceRegisterSchemaTests(unittest.TestCase):
    def test_validate_source_register_passes_for_final_workbook(self) -> None:
        result = validate_source_register(CANONICAL_WORKBOOK)

        self.assertTrue(result["validation_passed"])
        self.assertEqual(result["sheet_count"], 13)
        self.assertEqual(result["load_row_count"], 635)
        self.assertEqual(result["queue_row_count"], 51)
        self.assertEqual(result["removed_row_count"], 2)
        self.assertEqual(result["stale_source_detector_count"], 5)

    def test_validate_source_register_detects_duplicate_load_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workbook_copy = Path(tmp) / CANONICAL_WORKBOOK.name
            shutil.copyfile(CANONICAL_WORKBOOK, workbook_copy)
            workbook = load_workbook(workbook_copy)
            worksheet = workbook["Document_Register_Master"]
            headers = _header_map(worksheet)
            source_url_column = headers["Source_URL"]
            worksheet.cell(row=6, column=source_url_column).value = worksheet.cell(
                row=5,
                column=source_url_column,
            ).value
            workbook.save(workbook_copy)

            result = validate_source_register(workbook_copy)

        failing_checks = {check["name"] for check in result["checks"] if not check["passed"]}
        self.assertFalse(result["validation_passed"])
        self.assertIn("master_source_url_unique", failing_checks)

    def test_validate_source_register_detects_queue_database_load_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workbook_copy = Path(tmp) / CANONICAL_WORKBOOK.name
            shutil.copyfile(CANONICAL_WORKBOOK, workbook_copy)
            workbook = load_workbook(workbook_copy)
            worksheet = workbook["Direct_File_Capture_Queue"]
            headers = _header_map(worksheet)
            worksheet.cell(row=5, column=headers["Database_Load"]).value = "Yes"
            workbook.save(workbook_copy)

            result = validate_source_register(workbook_copy)

        failing_checks = {check["name"] for check in result["checks"] if not check["passed"]}
        self.assertFalse(result["validation_passed"])
        self.assertIn("queue_database_load_values", failing_checks)

    def test_build_source_register_diff_reports_phase_zero_replacement_counts(self) -> None:
        result = build_source_register_diff(
            LEGACY_WORKBOOK,
            LEGACY_REGISTER,
            CANONICAL_WORKBOOK,
        )

        self.assertEqual(result["legacy_workbook_source_count"], 190)
        self.assertEqual(result["legacy_register_source_delta_count"], 160)
        self.assertEqual(result["legacy_register_gap_count"], 1)
        self.assertEqual(result["legacy_runtime_unique_source_count"], 350)
        self.assertEqual(result["canonical_master_row_count"], 635)
        self.assertEqual(result["canonical_queue_row_count"], 51)
        self.assertEqual(result["canonical_removed_row_count"], 2)
        self.assertEqual(result["canonical_stale_source_detector_count"], 5)
        self.assertEqual(result["canonical_shared_with_legacy_workbook_count"], 0)
        self.assertEqual(result["canonical_shared_with_source_delta_count"], 0)
        self.assertEqual(result["canonical_only_source_count"], 635)
        self.assertEqual(result["legacy_only_source_count"], 350)
        self.assertEqual(result["canonical_only_source_ids_sample"][0], "FED-001")
        self.assertEqual(result["legacy_only_source_ids_sample"][0], "R1EA-001")


def _header_map(worksheet) -> dict[str, int]:  # noqa: ANN001
    return {
        str(cell.value): index
        for index, cell in enumerate(worksheet[4], start=1)
        if cell.value not in (None, "")
    }


if __name__ == "__main__":
    unittest.main()
