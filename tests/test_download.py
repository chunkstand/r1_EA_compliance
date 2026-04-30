from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.download import DownloadFetchResult, run_download


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


def downloaded_result(url: str) -> DownloadFetchResult:
    body = (f"<html><body>captured source for {url}</body></html>").encode("utf-8")
    if len(body) < 128:
        body += b" " * (128 - len(body))
    return DownloadFetchResult(
        status="downloaded",
        http_status=200,
        final_url=url,
        redirect_chain=[],
        content_type="text/html",
        content_length=len(body),
        body=body,
        attempt_count=1,
        failure=None,
        validation={"mode": "download", "passed": True, "reason": None},
    )


def challenge_result(url: str) -> DownloadFetchResult:
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


class FakeDownloader:
    def __init__(self, overrides: dict[str, DownloadFetchResult] | None = None) -> None:
        self.overrides = overrides or {}
        self.calls: list[str] = []

    def __call__(self, url, network, validation):  # noqa: ANN001
        self.calls.append(url)
        return self.overrides.get(url, downloaded_result(url))


class DownloadTests(unittest.TestCase):
    def test_download_writes_artifacts_hashes_and_preserves_duplicate_url_rows(self) -> None:
        config = load_config(CONFIG)
        fetcher = FakeDownloader()

        with tempfile.TemporaryDirectory() as tmp:
            result = run_download(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-download",
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
            self.assertEqual(result.summary["downloaded_count"], 144)
            self.assertEqual(result.summary["duplicate_url_count"], 3)
            self.assertEqual(result.summary["failed_count"], 0)

            downloaded = [record for record in records if record["status"] == "downloaded"]
            self.assertTrue(downloaded)
            for record in downloaded[:10]:
                artifact = Path(record["artifact_path"])
                self.assertTrue(artifact.exists())
                artifact_bytes = artifact.read_bytes()
                self.assertEqual(hashlib.sha256(artifact_bytes).hexdigest(), record["artifact_sha256"])
                self.assertEqual(len(artifact_bytes), record["artifact_byte_size"])
                self.assertIn(record["artifact_sha256"][:12], artifact.name)

            duplicate_rows = [record for record in records if record["status"] == "duplicate_url"]
            self.assertEqual(len(duplicate_rows), 3)
            self.assertTrue(all(record["duplicate_of"] for record in duplicate_rows))

            validation = json.loads(result.validation_report_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

    def test_download_reuses_existing_artifact_without_fetching_on_resume(self) -> None:
        config = load_config(CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            first_fetcher = FakeDownloader()
            first = run_download(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="first",
                id_filter="R1EA-001",
                fetcher=first_fetcher,
                sleep_fn=lambda _: None,
            )
            self.assertEqual(first.summary["downloaded_count"], 1)
            self.assertEqual(len(first_fetcher.calls), 1)

            second_fetcher = FakeDownloader()
            second = run_download(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="second",
                id_filter="R1EA-001",
                fetcher=second_fetcher,
                sleep_fn=lambda _: None,
            )
            self.assertEqual(second.summary["downloaded_existing_count"], 1)
            self.assertEqual(len(second_fetcher.calls), 0)

            record = json.loads(second.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["status"], "downloaded_existing")
            self.assertTrue(Path(record["artifact_path"]).exists())
            self.assertTrue(record["artifact_sha256"])

    def test_download_does_not_write_artifact_for_challenge_page(self) -> None:
        config = load_config(CONFIG)
        challenge_url = (
            "https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter55&edition=prelim"
        )
        fetcher = FakeDownloader({challenge_url: challenge_result(challenge_url)})

        with tempfile.TemporaryDirectory() as tmp:
            result = run_download(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="challenge",
                id_filter="R1EA-001",
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            record = json.loads(result.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["status"], "challenge_page")
            self.assertIsNone(record["artifact_path"])
            self.assertIsNone(record["artifact_sha256"])
            self.assertEqual(result.summary["downloaded_count"], 0)
            self.assertEqual(result.summary["failed_count"], 1)
            self.assertIn("challenge_page", result.failures_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
