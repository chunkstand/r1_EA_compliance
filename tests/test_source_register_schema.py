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
        self.assertEqual(result["load_row_count"], 638)
        self.assertEqual(result["queue_row_count"], 51)
        self.assertEqual(result["removed_row_count"], 3)
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
        self.assertEqual(result["canonical_master_row_count"], 638)
        self.assertEqual(result["canonical_queue_row_count"], 51)
        self.assertEqual(result["canonical_removed_row_count"], 3)
        self.assertEqual(result["canonical_stale_source_detector_count"], 5)
        self.assertEqual(result["canonical_shared_with_legacy_workbook_count"], 0)
        self.assertEqual(result["canonical_shared_with_source_delta_count"], 0)
        self.assertEqual(result["canonical_only_source_count"], 638)
        self.assertEqual(result["legacy_only_source_count"], 350)
        self.assertEqual(result["canonical_only_source_ids_sample"][0], "FED-001")
        self.assertEqual(result["legacy_only_source_ids_sample"][0], "R1EA-001")

    def test_fps_005_is_removed_from_active_ingest_with_governed_reason(self) -> None:
        workbook = load_workbook(CANONICAL_WORKBOOK, read_only=True, data_only=True)
        master = workbook["Document_Register_Master"]
        removed = workbook["Removed_Not_Applicable_Final"]
        master_headers = _header_map(master)
        removed_headers = _header_map(removed)

        master_ids = {
            str(row[master_headers["Source_ID"] - 1])
            for row in master.iter_rows(min_row=5, values_only=True)
            if row[master_headers["Source_ID"] - 1]
        }
        self.assertNotIn("FPS-005", master_ids)

        removed_rows = {
            str(row[removed_headers["Source_ID"] - 1]): row
            for row in removed.iter_rows(min_row=5, values_only=True)
            if row[removed_headers["Source_ID"] - 1]
        }
        fps_005 = removed_rows["FPS-005"]
        self.assertEqual(
            fps_005[removed_headers["Source_URL"] - 1],
            "https://www.fs.usda.gov/media/228272",
        )
        self.assertEqual(
            fps_005[removed_headers["EA_System_Applicability_Status"] - 1],
            "Not applicable - removed from ingest",
        )
        self.assertIn(
            "structurally invalid",
            str(fps_005[removed_headers["Removal_Reason"] - 1]),
        )

    def test_known_blocker_repairs_use_current_official_urls(self) -> None:
        workbook = load_workbook(CANONICAL_WORKBOOK, read_only=True, data_only=True)
        worksheet = workbook["Document_Register_Master"]
        headers = _header_map(worksheet)
        source_id_column = headers["Source_ID"]
        source_url_column = headers["Source_URL"]
        expected_urls = {
            "FED-042": "https://www.archives.gov/federal-register/codification/executive-order/11988.html",
            "FED-041": "https://www.govinfo.gov/content/pkg/FR-1999-02-08/html/99-3184.htm",
            "FED-039": "https://www.govinfo.gov/content/pkg/FR-1996-05-29/html/96-13597.htm",
            "FED-043": "https://www.archives.gov/federal-register/codification/executive-order/11990.html",
            "FED-029": "https://uscode.house.gov/view.xhtml?path=/prelim@title16/chapter5A&edition=prelim",
            "FPS-117": "https://www.fs.usda.gov/sites/nfs/files/legacy-media/custergallatin/CNF%20FPAdjustment%20001.pdf",
            "FINAL-Q-HLC-001": "https://www.fs.usda.gov/sites/nfs/files/r01/helena-lewisclark/publication/V3%20Maps%20EIS%202021%20Forest%20Plan.pdf",
            "FINAL-Q-HLC-002": "https://www.fs.usda.gov/sites/nfs/files/legacy-media/helena-lewisclark/Volume%204%20-%20HLCNF%20Plan.pdf",
            "FINAL-Q-HLC-003": "https://www.fs.usda.gov/sites/nfs/files/legacy-media/helena-lewisclark/Volume%205%20-%20HLCNF%20Plan.pdf",
            "FPS-344": "https://www.federalregister.gov/d/2024-30342",
            "PROG-008": "https://www.fs.usda.gov/naturalresources/watershed/pubs/FS_National_Core_BMPs_April2012.pdf",
            "PROG-010": "https://fs-prod-nwcg.s3.us-gov-west-1.amazonaws.com/s3fs-public/publication/pms484.pdf",
            "STP-015": "https://www.deq.idaho.gov/water-quality/surface-water/total-maximum-daily-loads/",
            "STP-011": "https://idfg.idaho.gov/species/",
            "USDA-008": "https://www.fs.usda.gov/im/directives/",
            "USDA-009": "https://www.ams.usda.gov/about-ams/accessibility",
            "USDA-010": "https://securefoia.usda.gov/",
            "USDA-011": "https://www.fs.usda.gov/spf/tribalrelations/documents/policy/consultation/Final_DR.pdf",
            "USDA-012": "https://www.rma.usda.gov/about-rma/website-policies-important-links/nondiscrimination-statement",
            "USDA-013": "https://www.ers.usda.gov/about-ers/policies-and-standards/information-quality",
            "WILD-ESA-094": "https://www.fs.usda.gov/sites/nfs/files/legacy-media/r01/lynx%20mgmt%20dir%20veg%20small%20map.jpg",
        }
        actual_urls: dict[str, str] = {}

        for row in worksheet.iter_rows(min_row=5, values_only=True):
            source_id = row[source_id_column - 1]
            if source_id in expected_urls:
                actual_urls[str(source_id)] = str(row[source_url_column - 1])

        self.assertEqual(actual_urls, expected_urls)


def _header_map(worksheet) -> dict[str, int]:  # noqa: ANN001
    return {
        str(cell.value): index
        for index, cell in enumerate(worksheet[4], start=1)
        if cell.value not in (None, "")
    }


if __name__ == "__main__":
    unittest.main()
