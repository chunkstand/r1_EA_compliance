from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.preflight import PreflightFetchResult, _classify_response
from usfs_r1_ea_sources.preflight import _request_headers, run_preflight


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


def ok_result(url: str) -> PreflightFetchResult:
    return PreflightFetchResult(
        status="preflight_ok",
        http_status=200,
        final_url=url,
        redirect_chain=[],
        content_type="text/html",
        content_length=1024,
        method="HEAD",
        failure=None,
        validation={"mode": "preflight", "passed": True, "reason": None},
    )


class FakeFetcher:
    def __init__(self, overrides: dict[str, PreflightFetchResult] | None = None) -> None:
        self.overrides = overrides or {}
        self.calls: list[str] = []

    def __call__(self, url, network, validation):  # noqa: ANN001
        self.calls.append(url)
        return self.overrides.get(url, ok_result(url))


class PreflightTests(unittest.TestCase):
    def test_preflight_fetches_each_unique_url_once_and_preserves_duplicate_rows(self) -> None:
        config = load_config(CONFIG)
        fetcher = FakeFetcher()

        with tempfile.TemporaryDirectory() as tmp:
            result = run_preflight(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-preflight",
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            records = [
                json.loads(line)
                for line in result.manifest_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(records), 147)
            self.assertEqual(len(fetcher.calls), 144)
            self.assertEqual(result.summary["checked_url_count"], 144)
            self.assertEqual(result.summary["preflight_ok_count"], 144)
            self.assertEqual(result.summary["duplicate_url_count"], 3)
            self.assertEqual(result.summary["failed_count"], 0)

            duplicate_records = [record for record in records if record["status"] == "duplicate_url"]
            self.assertEqual(len(duplicate_records), 3)
            self.assertTrue(all(record["duplicate_of"] for record in duplicate_records))

            validation = json.loads(result.validation_report_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

    def test_preflight_records_challenge_page_as_failure_not_success(self) -> None:
        config = load_config(CONFIG)
        challenge_url = (
            "https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter55&edition=prelim"
        )
        fetcher = FakeFetcher(
            {
                challenge_url: PreflightFetchResult(
                    status="challenge_page",
                    http_status=200,
                    final_url="https://unblock.federalregister.gov/",
                    redirect_chain=["https://unblock.federalregister.gov/"],
                    content_type="text/html",
                    content_length=4096,
                    method="HEAD",
                    failure={
                        "error_class": "challenge_page",
                        "error_message": "Challenge URL pattern matched",
                    },
                    validation={
                        "mode": "preflight",
                        "passed": False,
                        "reason": "Challenge URL pattern matched",
                    },
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = run_preflight(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-challenge",
                id_filter="R1EA-001",
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            record = json.loads(result.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["status"], "challenge_page")
            self.assertEqual(record["http_status"], 200)
            self.assertFalse(record["validation"]["passed"])
            self.assertEqual(result.summary["preflight_ok_count"], 0)
            self.assertEqual(result.summary["failed_count"], 1)

            failures = result.failures_path.read_text(encoding="utf-8")
            self.assertIn("challenge_page", failures)

    def test_preflight_filter_by_host_limits_checked_urls(self) -> None:
        config = load_config(CONFIG)
        fetcher = FakeFetcher()

        with tempfile.TemporaryDirectory() as tmp:
            result = run_preflight(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-host",
                host_filter="www.ecfr.gov",
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            self.assertEqual(result.summary["filtered_rows"], 45)
            self.assertEqual(result.summary["checked_url_count"], 44)
            self.assertEqual(result.summary["preflight_ok_count"], 44)
            self.assertEqual(result.summary["duplicate_url_count"], 1)

    def test_preflight_classifies_document_not_found_body_as_not_found(self) -> None:
        config = load_config(CONFIG)
        result = _classify_response(
            http_status=200,
            final_url="https://uscode.house.gov/view.xhtml?bad=1",
            redirect_chain=[],
            content_type="text/html",
            content_length=1024,
            method="GET",
            attempt_count=1,
            body_sample=b"<html><body>Document not found</body></html>" + b" " * 128,
            validation=config.validation,
        )

        self.assertEqual(result.status, "not_found")
        self.assertFalse(result.validation["passed"])

    def test_host_can_use_browser_compatible_user_agent(self) -> None:
        config = load_config(CONFIG)
        headers = _request_headers("https://dahp.wa.gov/project-review", config.network)

        self.assertEqual(headers["User-Agent"], "Mozilla/5.0")
        self.assertIn("application/xhtml+xml", headers["Accept"])


if __name__ == "__main__":
    unittest.main()
