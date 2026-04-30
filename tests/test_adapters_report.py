from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from usfs_r1_ea_sources.adapters import adapt_download_url
from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.download import DownloadFetchResult, run_download
from usfs_r1_ea_sources.report import build_run_report, suggested_action


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


class AdapterAndReportTests(unittest.TestCase):
    def test_ecfr_adapter_uses_full_xml_endpoint_with_latest_available_date(self) -> None:
        config = load_config(CONFIG)
        with patch("usfs_r1_ea_sources.adapters.latest_ecfr_date", return_value="2026-04-28"):
            adapted = adapt_download_url(
                "https://www.ecfr.gov/current/title-7/subtitle-A/part-1b/section-1b.5",
                config.network,
            )

        self.assertIsNotNone(adapted)
        self.assertEqual(adapted.adapter, "ecfr_full_xml")
        self.assertEqual(
            adapted.url,
            "https://www.ecfr.gov/api/versioner/v1/full/2026-04-28/title-7.xml?part=1b",
        )
        self.assertEqual(adapted.expected_content_type, "application/xml")

    def test_federal_register_adapter_uses_full_text_xml_endpoint(self) -> None:
        config = load_config(CONFIG)
        adapted = adapt_download_url(
            "https://www.federalregister.gov/documents/2026/04/03/2026-06537/national-environmental-policy-act",
            config.network,
        )

        self.assertIsNotNone(adapted)
        self.assertEqual(adapted.adapter, "federal_register_full_text_xml")
        self.assertEqual(
            adapted.url,
            "https://www.federalregister.gov/documents/full_text/xml/2026/04/03/2026-06537.xml",
        )

    def test_report_builds_repair_queue_from_failed_manifest(self) -> None:
        config = load_config(CONFIG)

        def challenge_fetcher(url, network, validation):  # noqa: ANN001
            return DownloadFetchResult(
                status="challenge_page",
                http_status=200,
                final_url="https://unblock.federalregister.gov/",
                redirect_chain=["https://unblock.federalregister.gov/"],
                content_type="text/html",
                content_length=2048,
                body=b"",
                attempt_count=1,
                failure={
                    "error_class": "challenge_page",
                    "error_message": "Challenge URL pattern matched",
                    "attempt_count": 1,
                },
                validation={
                    "mode": "download",
                    "passed": False,
                    "reason": "Challenge URL pattern matched",
                },
            )

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            run_download(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                run_id="report-test",
                id_filter="R1EA-008",
                fetcher=challenge_fetcher,
                sleep_fn=lambda _: None,
            )
            report = build_run_report(output_dir=output_dir, run_id="report-test")

            self.assertTrue(report.report_path.exists())
            self.assertEqual(len(report.summary["repair_rows"]), 1)
            self.assertIn("R1EA-008", report.text)
            self.assertIn("official API/export adapter", report.text)

    def test_suggested_action_for_fs_404(self) -> None:
        action = suggested_action(
            {
                "normalized_url": "https://www.fs.usda.gov/r01/lolo/planning/forest-plan-revision",
                "status": "not_found",
            }
        )
        self.assertIn("Repair stale Forest Service page URL", action)


if __name__ == "__main__":
    unittest.main()
