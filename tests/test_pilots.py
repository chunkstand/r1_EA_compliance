from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.pilots import discover_canonical_hosts, run_host_pilots


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


@dataclass(frozen=True)
class FakeDownloadResult:
    manifest_path: Path
    summary: dict


@dataclass(frozen=True)
class FakeReportResult:
    report_path: Path


@dataclass(frozen=True)
class FakeValidationResult:
    validation_path: Path
    passed: bool


class PilotTests(unittest.TestCase):
    def test_discover_canonical_hosts_from_workbook(self) -> None:
        config = load_config(CONFIG)
        hosts = discover_canonical_hosts(workbook_path=WORKBOOK, config=config)

        self.assertIn("www.ecfr.gov", hosts)
        self.assertIn("uscode.house.gov", hosts)
        self.assertIn("www.fs.usda.gov", hosts)

    def test_run_host_pilots_marks_all_ready_when_gates_pass_and_no_failures(self) -> None:
        config = load_config(CONFIG)
        calls: list[tuple[str, str]] = []

        def fake_downloader(**kwargs):  # noqa: ANN003
            host = kwargs["host_filter"]
            run_id = kwargs["run_id"]
            calls.append((host, run_id))
            return FakeDownloadResult(
                manifest_path=Path("manifest.jsonl"),
                summary={
                    "filtered_rows": 2,
                    "checked_url_count": 2,
                    "downloaded_count": 2,
                    "downloaded_existing_count": 0,
                    "duplicate_content_count": 0,
                    "duplicate_url_count": 0,
                    "failed_count": 0,
                    "needs_review_count": 0,
                    "status_counts": {"downloaded": 2},
                },
            )

        def fake_reporter(**kwargs):  # noqa: ANN003
            return FakeReportResult(report_path=Path("operator_report.md"))

        def fake_validator(**kwargs):  # noqa: ANN003
            return FakeValidationResult(validation_path=Path("acceptance_gate.json"), passed=True)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_host_pilots(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id_prefix="unit-pilot",
                hosts=["www.ecfr.gov", "uscode.house.gov"],
                downloader=fake_downloader,
                reporter=fake_reporter,
                validator=fake_validator,
            )

            self.assertTrue(result.summary["all_ready"])
            self.assertEqual(result.summary["ready_host_count"], 2)
            self.assertEqual(calls[0], ("www.ecfr.gov", "unit-pilot-www-ecfr-gov"))
            self.assertTrue(result.summary_path.exists())
            self.assertTrue(result.report_path.exists())

    def test_run_host_pilots_blocks_host_with_failures_even_if_gate_passes(self) -> None:
        config = load_config(CONFIG)

        def fake_downloader(**kwargs):  # noqa: ANN003
            return FakeDownloadResult(
                manifest_path=Path("manifest.jsonl"),
                summary={
                    "filtered_rows": 1,
                    "checked_url_count": 1,
                    "downloaded_count": 0,
                    "downloaded_existing_count": 0,
                    "duplicate_content_count": 0,
                    "duplicate_url_count": 0,
                    "failed_count": 1,
                    "needs_review_count": 0,
                    "status_counts": {"not_found": 1},
                },
            )

        def fake_reporter(**kwargs):  # noqa: ANN003
            return FakeReportResult(report_path=Path("operator_report.md"))

        def fake_validator(**kwargs):  # noqa: ANN003
            return FakeValidationResult(validation_path=Path("acceptance_gate.json"), passed=True)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_host_pilots(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id_prefix="blocked-pilot",
                hosts=["www.fs.usda.gov"],
                downloader=fake_downloader,
                reporter=fake_reporter,
                validator=fake_validator,
            )

            self.assertFalse(result.summary["all_ready"])
            self.assertEqual(result.summary["blocked_host_count"], 1)
            self.assertFalse(result.summary["host_results"][0]["ready_for_full_download"])


if __name__ == "__main__":
    unittest.main()
