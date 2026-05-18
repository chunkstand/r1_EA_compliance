from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json
import tempfile
import unittest
from urllib.parse import urlsplit

from usfs_r1_ea_sources.batches import build_batch_plan, run_batch_downloads
from usfs_r1_ea_sources.config import LEGACY_WORKBOOK_LOADER_CONTRACT, load_config
from usfs_r1_ea_sources.workbook import load_r1_forest_plan_document_register


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
R1_FOREST_PLAN_REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


@dataclass(frozen=True)
class FakeDownloadResult:
    manifest_path: Path
    summary: dict


@dataclass(frozen=True)
class FakeReportResult:
    report_path: Path
    summary: dict


@dataclass(frozen=True)
class FakeValidationResult:
    validation_path: Path
    passed: bool


class BatchTests(unittest.TestCase):
    def test_build_batch_plan_is_deterministic_by_host_and_size(self) -> None:
        config = legacy_config()
        plan = build_batch_plan(
            workbook_path=WORKBOOK,
            config=config,
            run_id_prefix="unit-batch",
            hosts=["uscode.house.gov"],
            batch_size=10,
            limit_per_host=21,
        )

        self.assertEqual([batch["row_count"] for batch in plan], [10, 10, 1])
        self.assertEqual(plan[0]["batch_id"], "unit-batch-uscode-house-gov-001")
        self.assertEqual(plan[1]["batch_id"], "unit-batch-uscode-house-gov-002")
        self.assertEqual(plan[0]["host"], "uscode.house.gov")

    def test_build_batch_plan_rejects_unknown_requested_host(self) -> None:
        config = legacy_config()

        with self.assertRaisesRegex(ValueError, "no workbook sources"):
            build_batch_plan(
                workbook_path=WORKBOOK,
                config=config,
                run_id_prefix="bad-host",
                hosts=["missing.example.test"],
                batch_size=1,
            )

    def test_build_batch_plan_can_target_r1_forest_plan_source_delta_rows(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_delta_ids = {
            source.source_record_id for source in register.source_delta_sources
        }

        plan = build_batch_plan(
            workbook_path=WORKBOOK,
            config=config,
            run_id_prefix="r1-delta",
            batch_size=100,
            source_record_ids=source_delta_ids,
            supplemental_sources=register.source_delta_sources,
        )

        planned_ids = {
            source_id
            for batch in plan
            for source_id in batch["source_record_ids"]
        }
        host_counts = {
            host: sum(batch["row_count"] for batch in plan if batch["host"] == host)
            for host in {batch["host"] for batch in plan}
        }
        self.assertEqual(planned_ids, source_delta_ids)
        self.assertEqual(sum(batch["row_count"] for batch in plan), 160)
        self.assertEqual(
            host_counts,
            {
                "federalregister.gov": 2,
                "usfs-public.app.box.com": 18,
                "www.fs.usda.gov": 140,
            },
        )

    def test_build_batch_plan_rejects_missing_source_id_filter(self) -> None:
        config = legacy_config()

        with self.assertRaisesRegex(ValueError, "no loaded sources"):
            build_batch_plan(
                workbook_path=WORKBOOK,
                config=config,
                run_id_prefix="bad-id",
                source_record_ids={"R1PLAN-missing-source"},
            )

    def test_run_batch_downloads_plan_only_writes_plan_and_ledger(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            result = run_batch_downloads(
                workbook_path=WORKBOOK,
                output_dir=tmp_path,
                config=config,
                run_id_prefix="plan-only",
                hosts=["www.ecfr.gov"],
                batch_size=2,
                limit_per_host=3,
                plan_only=True,
            )

            self.assertEqual(result.summary["batch_count"], 2)
            self.assertEqual(result.summary["planned_row_count"], 3)
            self.assertEqual(result.summary["planned_batch_count"], 2)
            self.assertTrue(result.plan_path.exists())
            self.assertTrue(result.ledger_path.exists())
            self.assertTrue(result.repair_queue_path.exists())

    def test_run_batch_downloads_plan_only_writes_source_delta_metadata(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_delta_ids = {
            source.source_record_id for source in register.source_delta_sources
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            result = run_batch_downloads(
                workbook_path=WORKBOOK,
                output_dir=tmp_path,
                config=config,
                run_id_prefix="r1-delta-plan-only",
                batch_size=200,
                plan_only=True,
                source_record_ids=source_delta_ids,
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
            )

            plan = json.loads(result.plan_path.read_text(encoding="utf-8"))
            self.assertEqual(result.summary["planned_row_count"], 160)
            self.assertEqual(result.summary["supplemental_source_count"], 160)
            self.assertEqual(result.summary["source_record_id_filter_count"], 160)
            self.assertEqual(result.summary["source_delta_input"]["source_delta_count"], 160)
            self.assertEqual(plan["supplemental_source_count"], 160)
            self.assertEqual(plan["source_record_id_filter_count"], 160)
            self.assertEqual(plan["source_delta_input"]["source_delta_count"], 160)

    def test_run_batch_downloads_passes_batches_and_forwards_source_ids(self) -> None:
        config = legacy_config()
        calls: list[set[str]] = []

        def fake_downloader(**kwargs):  # noqa: ANN003
            source_ids = kwargs["source_record_ids"]
            calls.append(source_ids)
            return FakeDownloadResult(
                manifest_path=Path("manifest.jsonl"),
                summary={
                    "filtered_rows": len(source_ids),
                    "checked_url_count": len(source_ids),
                    "downloaded_count": len(source_ids),
                    "downloaded_existing_count": 0,
                    "duplicate_content_count": 0,
                    "duplicate_url_count": 0,
                    "failed_count": 0,
                    "needs_review_count": 0,
                    "status_counts": {"downloaded": len(source_ids)},
                },
            )

        def fake_reporter(**kwargs):  # noqa: ANN003
            return FakeReportResult(
                report_path=Path("operator_report.md"),
                summary={"repair_rows": []},
            )

        def fake_validator(**kwargs):  # noqa: ANN003
            return FakeValidationResult(validation_path=Path("acceptance_gate.json"), passed=True)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_batch_downloads(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id_prefix="passing-batch",
                hosts=["uscode.house.gov"],
                batch_size=2,
                limit_per_host=3,
                downloader=fake_downloader,
                reporter=fake_reporter,
                validator=fake_validator,
            )

            self.assertTrue(result.summary["all_passed"])
            self.assertEqual(result.summary["passed_batch_count"], 2)
            self.assertEqual([len(call) for call in calls], [2, 1])

    def test_run_batch_downloads_forwards_source_delta_inputs_to_child_downloads(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_delta_ids = {
            source.source_record_id for source in register.source_delta_sources
        }
        calls: list[dict] = []

        def fake_downloader(**kwargs):  # noqa: ANN003
            calls.append(kwargs)
            source_ids = kwargs["source_record_ids"]
            return FakeDownloadResult(
                manifest_path=Path("manifest.jsonl"),
                summary={
                    "filtered_rows": len(source_ids),
                    "checked_url_count": len(source_ids),
                    "downloaded_count": len(source_ids),
                    "downloaded_existing_count": 0,
                    "duplicate_content_count": 0,
                    "duplicate_url_count": 0,
                    "failed_count": 0,
                    "needs_review_count": 0,
                    "status_counts": {"downloaded": len(source_ids)},
                },
            )

        def fake_reporter(**kwargs):  # noqa: ANN003
            return FakeReportResult(
                report_path=Path("operator_report.md"),
                summary={"repair_rows": []},
            )

        def fake_validator(**kwargs):  # noqa: ANN003
            return FakeValidationResult(validation_path=Path("acceptance_gate.json"), passed=True)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_batch_downloads(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id_prefix="r1-delta-forward",
                hosts=["federalregister.gov"],
                batch_size=2,
                source_record_ids=source_delta_ids,
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
                downloader=fake_downloader,
                reporter=fake_reporter,
                validator=fake_validator,
            )

            self.assertTrue(result.summary["all_passed"])
            self.assertEqual(result.summary["passed_batch_count"], 1)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(calls[0]["supplemental_sources"]), 160)
            self.assertEqual(calls[0]["source_delta_input"]["source_delta_count"], 160)
            self.assertEqual(calls[0]["host_filter"], "federalregister.gov")
            self.assertEqual(
                {
                    urlsplit(source.normalized_url).netloc.lower()
                    for source in register.source_delta_sources
                    if source.source_record_id in calls[0]["source_record_ids"]
                },
                {"federalregister.gov"},
            )

    def test_run_batch_downloads_summarizes_manifest_evidence(self) -> None:
        config = legacy_config()

        def fake_downloader(**kwargs):  # noqa: ANN003
            run_id = kwargs["run_id"]
            output_dir = kwargs["output_dir"]
            manifest_dir = output_dir / "manifests"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifest_dir / f"download_{run_id}.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_record_id": "R1EA-123",
                        "status": "downloaded",
                        "artifact_sha256": "a" * 64,
                        "validation": {"browser_compatible_user_agent": True},
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            return FakeDownloadResult(
                manifest_path=manifest_path,
                summary={
                    "filtered_rows": 1,
                    "checked_url_count": 1,
                    "downloaded_count": 1,
                    "downloaded_existing_count": 0,
                    "duplicate_content_count": 0,
                    "duplicate_url_count": 0,
                    "failed_count": 0,
                    "needs_review_count": 0,
                    "status_counts": {"downloaded": 1},
                },
            )

        def fake_reporter(**kwargs):  # noqa: ANN003
            return FakeReportResult(
                report_path=Path("operator_report.md"),
                summary={"repair_rows": []},
            )

        def fake_validator(**kwargs):  # noqa: ANN003
            return FakeValidationResult(validation_path=Path("acceptance_gate.json"), passed=True)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_batch_downloads(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id_prefix="manifest-evidence",
                hosts=["dahp.wa.gov"],
                batch_size=1,
                limit_per_host=1,
                downloader=fake_downloader,
                reporter=fake_reporter,
                validator=fake_validator,
            )

            self.assertEqual(result.summary["artifact_count"], 1)
            self.assertEqual(result.summary["browser_compatible_user_agent_count"], 1)
            ledger = json.loads(result.ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger["batches"][0]["artifact_count"], 1)
            self.assertEqual(ledger["batches"][0]["browser_compatible_user_agent_count"], 1)

    def test_run_batch_downloads_stops_on_failed_gate(self) -> None:
        config = legacy_config()
        calls = 0

        def fake_downloader(**kwargs):  # noqa: ANN003
            nonlocal calls
            calls += 1
            return FakeDownloadResult(
                manifest_path=Path("manifest.jsonl"),
                summary={
                    "filtered_rows": 1,
                    "checked_url_count": 1,
                    "downloaded_count": 0,
                    "downloaded_existing_count": 0,
                    "duplicate_content_count": 0,
                    "duplicate_url_count": 0,
                    "failed_count": 0,
                    "needs_review_count": 0,
                    "status_counts": {"downloaded": 1},
                },
            )

        def fake_reporter(**kwargs):  # noqa: ANN003
            return FakeReportResult(
                report_path=Path("operator_report.md"),
                summary={"repair_rows": []},
            )

        def fake_validator(**kwargs):  # noqa: ANN003
            return FakeValidationResult(validation_path=Path("acceptance_gate.json"), passed=False)

        with tempfile.TemporaryDirectory() as tmp:
            result = run_batch_downloads(
                workbook_path=WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                run_id_prefix="blocked-batch",
                hosts=["uscode.house.gov"],
                batch_size=1,
                limit_per_host=2,
                downloader=fake_downloader,
                reporter=fake_reporter,
                validator=fake_validator,
            )

            self.assertFalse(result.summary["all_passed"])
            self.assertEqual(result.summary["failed_batch_count"], 1)
            self.assertEqual(result.summary["planned_batch_count"], 1)
            self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
