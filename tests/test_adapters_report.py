from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from usfs_r1_ea_sources.adapters import _ECFR_DATE_CACHE, adapt_download_url, latest_ecfr_date
from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.download import DownloadFetchResult, run_download
from usfs_r1_ea_sources.report import build_run_report, suggested_action


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
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

    def test_ecfr_latest_date_is_cached_by_title(self) -> None:
        config = load_config(CONFIG)
        _ECFR_DATE_CACHE.clear()

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
                return False

            def read(self, *_args):  # noqa: ANN002
                return (
                    b'{"titles":[{"number":7,"up_to_date_as_of":"2026-04-28",'
                    b'"latest_issue_date":"2026-04-28"}]}'
                )

        with patch("usfs_r1_ea_sources.adapters.urlopen", return_value=FakeResponse()) as mocked:
            self.assertEqual(latest_ecfr_date(7, config.network), "2026-04-28")
            self.assertEqual(latest_ecfr_date(7, config.network), "2026-04-28")

        self.assertEqual(mocked.call_count, 1)

    def test_report_resolves_manifest_path_relative_to_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            run_dir = output_dir / "runs" / "path-test"
            manifest_dir = output_dir / "manifests"
            run_dir.mkdir(parents=True)
            manifest_dir.mkdir(parents=True)
            (run_dir / "summary.json").write_text(
                json.dumps(
                    {
                        "run_id": "path-test",
                        "mode": "download",
                        "workbook_sha256": "abc",
                        "manifest_path": "manifests/download_path-test.jsonl",
                    }
                ),
                encoding="utf-8",
            )
            (manifest_dir / "download_path-test.jsonl").write_text(
                json.dumps(
                    {
                        "status": "downloaded",
                        "normalized_url": "https://example.test/source",
                        "source_record_id": "SRC-1",
                        "sheet": "Ingest_Checklist",
                        "excel_row": 5,
                        "title": "Example",
                        "original_url": "https://example.test/source",
                        "validation": {},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_run_report(output_dir=output_dir, run_id="path-test")
            self.assertTrue(report.report_path.exists())


if __name__ == "__main__":
    unittest.main()
