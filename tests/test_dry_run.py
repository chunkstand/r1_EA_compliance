from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.dry_run import run_dry_run
from usfs_r1_ea_sources.workbook import load_canonical_sources, load_excluded_urls


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


class DryRunTests(unittest.TestCase):
    def test_workbook_contract_counts(self) -> None:
        config = load_config(CONFIG)
        sources = load_canonical_sources(WORKBOOK, config.workbook)
        excluded_urls = load_excluded_urls(WORKBOOK, config.workbook)

        self.assertEqual(len(sources), 147)
        self.assertEqual(len({source.normalized_url for source in sources}), 144)
        self.assertEqual(len(excluded_urls), 17)
        self.assertFalse({source.normalized_url for source in sources} & excluded_urls)

    def test_dry_run_writes_manifest_and_reports(self) -> None:
        config = load_config(CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-run",
            )

            self.assertTrue(result.manifest_path.exists())
            self.assertTrue(result.summary_path.exists())
            self.assertTrue(result.validation_report_path.exists())
            self.assertTrue(result.failures_path.exists())

            manifest_records = [
                json.loads(line)
                for line in result.manifest_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(manifest_records), 147)
            self.assertEqual(result.summary["canonical_rows"], 147)
            self.assertEqual(result.summary["unique_canonical_urls"], 144)
            self.assertEqual(result.summary["planned_count"], 144)
            self.assertEqual(result.summary["duplicate_url_count"], 3)
            self.assertEqual(result.summary["skipped_excluded_count"], 0)

            duplicate_records = [
                record for record in manifest_records if record["status"] == "duplicate_url"
            ]
            self.assertEqual(len(duplicate_records), 3)
            self.assertTrue(all(record["duplicate_of"] for record in duplicate_records))

            validation = json.loads(result.validation_report_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

    def test_dry_run_filter_by_host(self) -> None:
        config = load_config(CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-host-filter",
                host_filter="www.ecfr.gov",
            )

            self.assertEqual(result.summary["filtered_rows"], 45)
            self.assertEqual(result.summary["status_counts"]["planned"], 44)
            self.assertEqual(result.summary["status_counts"]["duplicate_url"], 1)


if __name__ == "__main__":
    unittest.main()
