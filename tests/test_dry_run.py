from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.config import (
    LEGACY_WORKBOOK_LOADER_CONTRACT,
    load_config,
)
from usfs_r1_ea_sources.dry_run import run_dry_run
from usfs_r1_ea_sources.workbook import load_canonical_sources, load_excluded_urls
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


class DryRunTests(unittest.TestCase):
    def test_workbook_contract_counts(self) -> None:
        config = load_config(CONFIG)
        sources = load_canonical_sources(CANONICAL_WORKBOOK, config.workbook)
        excluded_urls = load_excluded_urls(CANONICAL_WORKBOOK, config.workbook)

        self.assertEqual(len(sources), 635)
        self.assertEqual(len({source.normalized_url for source in sources}), 635)
        self.assertEqual(len(excluded_urls), 0)

    def test_dry_run_writes_manifest_and_reports(self) -> None:
        config = load_config(CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(
                workbook_path=CANONICAL_WORKBOOK,
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
            self.assertEqual(len(manifest_records), 635)
            self.assertEqual(result.summary["canonical_rows"], 635)
            self.assertEqual(result.summary["unique_canonical_urls"], 635)
            self.assertEqual(result.summary["planned_count"], 635)
            self.assertEqual(result.summary["duplicate_url_count"], 0)
            self.assertEqual(result.summary["skipped_excluded_count"], 0)
            self.assertTrue(result.summary["validation_passed"])

            duplicate_records = [
                record for record in manifest_records if record["status"] == "duplicate_url"
            ]
            self.assertEqual(len(duplicate_records), 0)
            self.assertTrue(all(record["duplicate_of"] for record in duplicate_records))

            validation = json.loads(result.validation_report_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

    def test_dry_run_filter_by_host(self) -> None:
        config = load_config(CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id="test-host-filter",
                host_filter="www.ecfr.gov",
            )

            self.assertEqual(result.summary["filtered_rows"], 34)
            self.assertEqual(result.summary["status_counts"]["planned"], 34)
            self.assertNotIn("duplicate_url", result.summary["status_counts"])

    def test_dry_run_rejects_legacy_source_delta_under_canonical_loader(self) -> None:
        config = load_config(CONFIG)
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "sole active source ledger"):
                run_dry_run(
                    workbook_path=CANONICAL_WORKBOOK,
                    output_dir=Path(tmp),
                    config=config,
                    run_id="canonical-source-delta-reject",
                    supplemental_sources=register.source_delta_sources,
                    source_delta_input=register.summary(),
                )

    def test_legacy_dry_run_promotes_r1_forest_plan_source_delta_only(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_delta_ids = {source.source_record_id for source in register.source_delta_sources}

        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(
                workbook_path=LEGACY_WORKBOOK,
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
            self.assertEqual(result.summary["canonical_rows"], 350)
            self.assertEqual(result.summary["supplemental_source_count"], 160)
            self.assertEqual(result.summary["filtered_rows"], 160)
            self.assertEqual(result.summary["planned_count"], 160)
            self.assertEqual(result.summary["duplicate_url_count"], 0)
            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["source_delta_input"]["gap_count"], 1)
            self.assertEqual(
                result.summary["source_delta_input"]["skipped_gap_source_record_ids"],
                ["R1PLAN-kootenai-nf-18"],
            )
            self.assertEqual({record["source_record_id"] for record in records}, source_delta_ids)
            self.assertTrue(
                all(record["sheet"] == "R1_Forest_Plan_Document_Register" for record in records)
            )


if __name__ == "__main__":
    unittest.main()
