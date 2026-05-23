from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from usfs_r1_ea_sources.config import LEGACY_WORKBOOK_LOADER_CONTRACT, load_config
from usfs_r1_ea_sources.download import (
    DownloadFetchResult,
    _classify_download_response,
    _content_type_for_suffix,
    _suffix_for_content_type,
    run_download,
)
from usfs_r1_ea_sources.records import planned_artifact_path
from usfs_r1_ea_sources.workbook import load_canonical_sources


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


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


def downloaded_pdf_result(url: str) -> DownloadFetchResult:
    body = b"%PDF-1.4 direct document bytes" + b" " * 128
    return DownloadFetchResult(
        status="downloaded",
        http_status=200,
        final_url=url,
        redirect_chain=[],
        content_type="application/pdf",
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
    def test_zip_content_type_uses_zip_suffix(self) -> None:
        self.assertEqual(_suffix_for_content_type("application/zip"), ".zip")
        self.assertEqual(_content_type_for_suffix(".zip"), "application/zip")
        self.assertEqual(_suffix_for_content_type("application/msword"), ".doc")
        self.assertEqual(_content_type_for_suffix(".doc"), "application/msword")
        self.assertEqual(
            _suffix_for_content_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ".xlsx",
        )
        self.assertEqual(
            _content_type_for_suffix(".xlsx"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(_suffix_for_content_type("image/jpeg"), ".jpg")
        self.assertEqual(_content_type_for_suffix(".jpg"), "image/jpeg")

    def test_download_writes_artifacts_hashes_and_preserves_duplicate_url_rows(self) -> None:
        config = legacy_config()
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
            self.assertEqual(len(records), 190)
            self.assertEqual(len(fetcher.calls), 171)
            self.assertEqual(result.summary["downloaded_count"], 171)
            self.assertEqual(result.summary["duplicate_url_count"], 18)
            self.assertEqual(result.summary["skipped_excluded_count"], 1)
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
            self.assertEqual(len(duplicate_rows), 18)
            self.assertTrue(all(record["duplicate_of"] for record in duplicate_rows))

            validation = json.loads(result.validation_report_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

    def test_download_reuses_existing_artifact_without_fetching_on_resume(self) -> None:
        config = legacy_config()

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

    def test_download_ignores_stale_html_artifact_when_row_now_targets_direct_pdf(self) -> None:
        config = load_config(CONFIG)
        fetcher = FakeDownloader(
            {
                "https://www.fws.gov/sites/default/files/federal_register_document/2022-27087.pdf": (
                    downloaded_pdf_result(
                        "https://www.fws.gov/sites/default/files/federal_register_document/2022-27087.pdf"
                    )
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            sources = load_canonical_sources(CANONICAL_WORKBOOK, config.workbook)
            source = next(row for row in sources if row.source_record_id == "WILD-ESA-075")
            planned_path = planned_artifact_path(output_dir, source)
            planned_path.parent.mkdir(parents=True, exist_ok=True)
            stale_html = planned_path.parent / f"{planned_path.with_suffix('').name}_stale.html"
            stale_html.write_bytes(b"<html><body>stale wrapper</body></html>" + b" " * 128)

            result = run_download(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                run_id="wild-esa-075-refresh",
                id_filter="WILD-ESA-075",
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            self.assertEqual(result.summary["downloaded_count"], 1)
            self.assertEqual(result.summary["downloaded_existing_count"], 0)
            self.assertEqual(len(fetcher.calls), 1)
            record = json.loads(result.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["status"], "downloaded")
            self.assertEqual(record["content_type"], "application/pdf")
            self.assertTrue(record["artifact_path"].endswith(".pdf"))

    def test_download_refetches_when_existing_artifact_is_invalid(self) -> None:
        config = legacy_config()

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            first_fetcher = FakeDownloader()
            first = run_download(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                run_id="seed-invalid",
                id_filter="R1EA-001",
                fetcher=first_fetcher,
                sleep_fn=lambda _: None,
            )
            first_record = json.loads(first.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            artifact = Path(first_record["artifact_path"])
            artifact.write_bytes(b"bad")

            second_fetcher = FakeDownloader()
            second = run_download(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                run_id="refetch-invalid",
                id_filter="R1EA-001",
                fetcher=second_fetcher,
                sleep_fn=lambda _: None,
            )

            self.assertEqual(len(second_fetcher.calls), 1)
            self.assertEqual(second.summary["downloaded_count"], 1)
            second_record = json.loads(second.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(second_record["status"], "downloaded")
            self.assertGreaterEqual(second_record["artifact_byte_size"], 128)

    def test_download_does_not_write_artifact_for_challenge_page(self) -> None:
        config = legacy_config()
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

    def test_download_classifies_document_not_found_body_as_not_found(self) -> None:
        config = legacy_config()

        result = _classify_download_response(
            http_status=200,
            final_url="https://uscode.house.gov/docnotfound.xhtml",
            redirect_chain=[],
            content_type="text/html",
            content_length=1024,
            body=b"<html><body>Document not found</body></html>" + b" " * 128,
            validation=config.validation,
            attempt_count=1,
        )

        self.assertEqual(result.status, "not_found")
        self.assertFalse(result.validation["passed"])

    def test_download_duplicate_content_reuses_canonical_artifact(self) -> None:
        config = legacy_config()
        same_body = b"<html><body>same captured content</body></html>" + b" " * 128

        def same_content_fetcher(url, network, validation):  # noqa: ANN001
            return DownloadFetchResult(
                status="downloaded",
                http_status=200,
                final_url=url,
                redirect_chain=[],
                content_type="text/html",
                content_length=len(same_body),
                body=same_body,
                attempt_count=1,
                failure=None,
                validation={"mode": "download", "passed": True, "reason": None},
            )

        with tempfile.TemporaryDirectory() as tmp:
            result = run_download(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="duplicate-content",
                limit=2,
                fetcher=same_content_fetcher,
                sleep_fn=lambda _: None,
            )

            records = [
                json.loads(line)
                for line in result.manifest_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(records[0]["status"], "downloaded")
            self.assertEqual(records[1]["status"], "duplicate_content")
            self.assertEqual(records[1]["artifact_path"], records[0]["artifact_path"])
            self.assertEqual(records[1]["duplicate_of"], records[0]["artifact_path"])
            artifact_files = list((Path(tmp) / "artifacts" / "raw").rglob("*"))
            artifact_files = [path for path in artifact_files if path.is_file()]
            self.assertEqual(len(artifact_files), 1)

    def test_download_can_use_verified_curl_transport_for_ecos(self) -> None:
        config = load_config(CONFIG)
        body = b"<html><body>ecos report payload</body></html>" + b" " * 256
        calls: list[list[str]] = []

        def fake_run(command, capture_output, text, check):  # noqa: ANN001
            calls.append(command)
            header_path = Path(command[command.index("--dump-header") + 1])
            body_path = Path(command[command.index("--output") + 1])
            header_path.write_text(
                "HTTP/2 200\ncontent-type: text/html;charset=UTF-8\ncontent-length: 256\n\n",
                encoding="utf-8",
            )
            body_path.write_bytes(body)
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "CURLMETA:200\ttext/html;charset=UTF-8\t"
                    "https://ecos.fws.gov/ecp/species/2982\t256\n"
                ),
                stderr="",
            )

        with tempfile.TemporaryDirectory() as tmp:
            with patch("usfs_r1_ea_sources.preflight.subprocess.run", side_effect=fake_run):
                result = run_download(
                    workbook_path=ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
                    output_dir=Path(tmp),
                    config=config,
                    run_id="ecos-curl-download",
                    id_filter="WILD-ESA-084",
                    sleep_fn=lambda _: None,
                )

            record = json.loads(result.manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["status"], "downloaded")
            self.assertEqual(record["validation"]["verified_transport"], "curl")
            self.assertEqual(len(calls), 1)
            self.assertTrue(Path(record["artifact_path"]).exists())


if __name__ == "__main__":
    unittest.main()
