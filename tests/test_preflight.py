from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import patch

from usfs_r1_ea_sources.config import (
    LEGACY_WORKBOOK_LOADER_CONTRACT,
    load_config,
)
from usfs_r1_ea_sources.preflight import PreflightFetchResult, _classify_response
from usfs_r1_ea_sources.preflight import _request_headers, fetch_url_metadata, run_preflight
from usfs_r1_ea_sources.workbook import load_r1_forest_plan_document_register


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
LEGACY_WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
R1_FOREST_PLAN_REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


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
                workbook_path=CANONICAL_WORKBOOK,
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
            self.assertEqual(len(records), 691)
            self.assertEqual(len(fetcher.calls), 691)
            self.assertEqual(result.summary["checked_url_count"], 691)
            self.assertEqual(result.summary["preflight_ok_count"], 691)
            self.assertEqual(result.summary["duplicate_url_count"], 0)
            self.assertEqual(result.summary["skipped_excluded_count"], 0)
            self.assertEqual(result.summary["failed_count"], 0)
            self.assertTrue(result.summary["validation_passed"])

            duplicate_records = [record for record in records if record["status"] == "duplicate_url"]
            self.assertEqual(len(duplicate_records), 0)
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
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-challenge",
                id_filter="FED-001",
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
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-host",
                host_filter="www.ecfr.gov",
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            self.assertEqual(result.summary["filtered_rows"], 45)
            self.assertEqual(result.summary["checked_url_count"], 45)
            self.assertEqual(result.summary["preflight_ok_count"], 45)
            self.assertEqual(result.summary["duplicate_url_count"], 0)

    def test_legacy_preflight_promotes_r1_forest_plan_source_delta_only(self) -> None:
        config = legacy_config()
        fetcher = FakeFetcher()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_delta_ids = {source.source_record_id for source in register.source_delta_sources}

        with tempfile.TemporaryDirectory() as tmp:
            result = run_preflight(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="r1-forest-plan-source-delta-preflight",
                source_record_ids=source_delta_ids,
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
                fetcher=fetcher,
                sleep_fn=lambda _: None,
            )

            records = [
                json.loads(line)
                for line in result.manifest_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(result.summary["workbook_rows"], 190)
            self.assertEqual(result.summary["canonical_rows"], 350)
            self.assertEqual(result.summary["supplemental_source_count"], 160)
            self.assertEqual(result.summary["filtered_rows"], 160)
            self.assertEqual(result.summary["checked_url_count"], 160)
            self.assertEqual(result.summary["preflight_ok_count"], 160)
            self.assertEqual(result.summary["failed_count"], 0)
            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["source_delta_input"]["gap_count"], 1)
            self.assertEqual(len(fetcher.calls), 160)
            self.assertEqual({record["source_record_id"] for record in records}, source_delta_ids)

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

    def test_preflight_accepts_supported_doc_and_image_content_types(self) -> None:
        config = load_config(CONFIG)

        for content_type in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg",
        ):
            with self.subTest(content_type=content_type):
                if content_type == "application/msword":
                    suffix = ".doc"
                elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    suffix = ".xlsx"
                else:
                    suffix = ".jpg"
                result = _classify_response(
                    http_status=200,
                    final_url=f"https://example.com/source{suffix}",
                    redirect_chain=[],
                    content_type=content_type,
                    content_length=2048,
                    method="GET",
                    attempt_count=1,
                    body_sample=b"example body bytes" + b" " * 128,
                    validation=config.validation,
                )

                self.assertEqual(result.status, "preflight_ok")
                self.assertTrue(result.validation["passed"])

    def test_host_can_use_browser_compatible_user_agent(self) -> None:
        config = load_config(CONFIG)
        headers = _request_headers("https://dahp.wa.gov/project-review", config.network)

        self.assertEqual(headers["User-Agent"], "Mozilla/5.0")
        self.assertIn("application/xhtml+xml", headers["Accept"])

    def test_preflight_can_use_verified_curl_transport_for_ecos(self) -> None:
        config = load_config(CONFIG)
        responses = [
            {
                "stdout": (
                    "CURLMETA:200\tapplication/json;charset=UTF-8\t"
                    "https://ecos.fws.gov/ecp/species/2982\t0\n"
                ),
                "stderr": "",
                "headers": "HTTP/2 200\ncontent-type: application/json;charset=UTF-8\n\n",
                "body": b"",
            },
            {
                "stdout": (
                    "CURLMETA:200\ttext/html;charset=UTF-8\t"
                    "https://ecos.fws.gov/ecp/species/2982\t256\n"
                ),
                "stderr": "",
                "headers": (
                    "HTTP/2 200\n"
                    "content-type: text/html;charset=UTF-8\n"
                    "content-length: 256\n\n"
                ),
                "body": b"<html><body>ecos species profile</body></html>" + b" " * 256,
            },
        ]
        calls: list[list[str]] = []

        def fake_run(command, capture_output, text, check):  # noqa: ANN001
            response = responses[len(calls)]
            calls.append(command)
            header_path = Path(command[command.index("--dump-header") + 1])
            body_path = Path(command[command.index("--output") + 1])
            header_path.write_text(response["headers"], encoding="utf-8")
            body_path.write_bytes(response["body"])
            return SimpleNamespace(returncode=0, stdout=response["stdout"], stderr=response["stderr"])

        with patch("usfs_r1_ea_sources.preflight.subprocess.run", side_effect=fake_run):
            result = fetch_url_metadata(
                "https://ecos.fws.gov/ecp/species/2982",
                config.network,
                config.validation,
            )

        self.assertEqual(result.status, "preflight_ok")
        self.assertEqual(result.method, "GET")
        self.assertEqual(result.validation["verified_transport"], "curl")
        self.assertEqual(len(calls), 2)
        self.assertIn("--head", calls[0])
        self.assertIn("--range", calls[1])

    def test_preflight_retries_with_get_after_head_rate_limit(self) -> None:
        config = load_config(CONFIG)
        url = "https://www.fs.usda.gov/media/44634"
        calls: list[tuple[str, int]] = []

        def fake_fetch_once(
            requested_url, method, network, validation, attempt_count, *, original_url=None
        ):  # noqa: ANN001
            calls.append((method, attempt_count))
            if method == "HEAD":
                return PreflightFetchResult(
                    status="rate_limited",
                    http_status=429,
                    final_url=requested_url,
                    redirect_chain=[],
                    content_type="text/html",
                    content_length=0,
                    method=method,
                    attempt_count=attempt_count,
                    failure={
                        "error_class": "rate_limited",
                        "error_message": "HTTP 429",
                        "attempt_count": attempt_count,
                    },
                    validation={"mode": "preflight", "passed": False, "reason": "HTTP 429"},
                )
            return PreflightFetchResult(
                status="preflight_ok",
                http_status=206,
                final_url=requested_url,
                redirect_chain=[],
                content_type="application/pdf",
                content_length=4096,
                method=method,
                attempt_count=attempt_count,
                failure=None,
                validation={"mode": "preflight", "passed": True, "reason": None},
            )

        with patch("usfs_r1_ea_sources.preflight._fetch_once", side_effect=fake_fetch_once):
            result = fetch_url_metadata(url, config.network, config.validation)

        self.assertEqual(result.status, "preflight_ok")
        self.assertEqual(result.method, "GET")
        self.assertEqual(result.http_status, 206)
        self.assertEqual(calls, [("HEAD", 1), ("GET", 1)])


if __name__ == "__main__":
    unittest.main()
