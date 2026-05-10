from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.dry_run import run_dry_run
from usfs_r1_ea_sources.workbook import load_canonical_sources, load_excluded_urls
from usfs_r1_ea_sources.workbook import load_r1_forest_plan_document_register


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
R1_FOREST_PLAN_REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"


class DryRunTests(unittest.TestCase):
    def test_workbook_contract_counts(self) -> None:
        config = load_config(CONFIG)
        sources = load_canonical_sources(WORKBOOK, config.workbook)
        excluded_urls = load_excluded_urls(WORKBOOK, config.workbook)

        self.assertEqual(len(sources), 190)
        self.assertEqual(len({source.normalized_url for source in sources}), 172)
        self.assertEqual(len(excluded_urls), 19)
        self.assertEqual(
            [source.source_record_id for source in sources if source.normalized_url in excluded_urls],
            ["R1EA-160"],
        )

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
            self.assertEqual(len(manifest_records), 190)
            self.assertEqual(result.summary["canonical_rows"], 190)
            self.assertEqual(result.summary["unique_canonical_urls"], 172)
            self.assertEqual(result.summary["planned_count"], 171)
            self.assertEqual(result.summary["duplicate_url_count"], 18)
            self.assertEqual(result.summary["skipped_excluded_count"], 1)
            self.assertTrue(result.summary["validation_passed"])

            duplicate_records = [
                record for record in manifest_records if record["status"] == "duplicate_url"
            ]
            self.assertEqual(len(duplicate_records), 18)
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

            self.assertEqual(result.summary["filtered_rows"], 61)
            self.assertEqual(result.summary["status_counts"]["planned"], 46)
            self.assertEqual(result.summary["status_counts"]["duplicate_url"], 15)

    def test_dry_run_promotes_r1_forest_plan_source_delta_only(self) -> None:
        config = load_config(CONFIG)
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_delta_ids = {source.source_record_id for source in register.source_delta_sources}

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="r1-forest-plan-source-delta-dry-run",
                source_record_ids=source_delta_ids,
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
            )

            records = [
                json.loads(line)
                for line in result.manifest_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(result.summary["workbook_rows"], 190)
            self.assertEqual(result.summary["canonical_rows"], 349)
            self.assertEqual(result.summary["supplemental_source_count"], 159)
            self.assertEqual(result.summary["filtered_rows"], 159)
            self.assertEqual(result.summary["planned_count"], 159)
            self.assertEqual(result.summary["duplicate_url_count"], 0)
            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["source_delta_input"]["gap_count"], 2)
            self.assertEqual(
                result.summary["source_delta_input"]["skipped_gap_source_record_ids"],
                ["R1PLAN-kootenai-nf-18", "R1PLAN-nez-perce-clearwater-nfs-18"],
            )
            self.assertEqual({record["source_record_id"] for record in records}, source_delta_ids)
            self.assertTrue(
                all(record["sheet"] == "R1_Forest_Plan_Document_Register" for record in records)
            )


if __name__ == "__main__":
    unittest.main()
