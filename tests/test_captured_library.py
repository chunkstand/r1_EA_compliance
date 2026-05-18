from __future__ import annotations

from pathlib import Path
from contextlib import closing
from dataclasses import replace
import csv
import hashlib
import json
import sqlite3
import tomllib
import unittest

from usfs_r1_ea_sources.config import LEGACY_WORKBOOK_LOADER_CONTRACT, load_config
from usfs_r1_ea_sources.workbook import load_r1_forest_plan_document_register
from usfs_r1_ea_sources.workbook import load_canonical_sources
from usfs_r1_ea_sources.workbook import merge_supplemental_sources


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
OVERRIDES = ROOT / "config" / "url_overrides.toml"
R1_FOREST_PLAN_REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"
SOURCE_LIBRARY = ROOT / "source_library"
FULL_BATCH_RUN_ID = "corpus-update-2026-05-01-cg-support-batches"
SOURCE_DELTA_BATCH_RUN_ID = "r1-forest-plan-source-delta-capture-20260510-refresh-batches"
ACTIVE_BATCH_RUN_IDS = [FULL_BATCH_RUN_ID, SOURCE_DELTA_BATCH_RUN_ID]
ARTIFACT_STATUSES = {"downloaded", "downloaded_existing", "duplicate_content", "duplicate_url"}
NON_ARTIFACT_SUCCESS_STATUSES = {"skipped_excluded"}
SUCCESS_STATUSES = ARTIFACT_STATUSES | NON_ARTIFACT_SUCCESS_STATUSES


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


class CapturedLibraryIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.run_dir = SOURCE_LIBRARY / "runs" / FULL_BATCH_RUN_ID
        cls.source_delta_run_dir = SOURCE_LIBRARY / "runs" / SOURCE_DELTA_BATCH_RUN_ID
        cls.catalog_dir = SOURCE_LIBRARY / "catalog"
        required_paths = [
            cls.run_dir / "summary.json",
            cls.run_dir / "batch_ledger.json",
            cls.run_dir / "repair_queue.csv",
            cls.source_delta_run_dir / "summary.json",
            cls.source_delta_run_dir / "batch_ledger.json",
            cls.source_delta_run_dir / "repair_queue.csv",
            cls.catalog_dir / "source_catalog.jsonl",
            cls.catalog_dir / "source_set_manifest.json",
            cls.catalog_dir / "catalog_validation.json",
            cls.catalog_dir / "review_sources.sqlite",
        ]
        missing = [path for path in required_paths if not path.exists()]
        if missing:
            raise unittest.SkipTest(
                "Captured source_library outputs are not present: "
                + ", ".join(str(path.relative_to(ROOT)) for path in missing)
            )

        cls.config = legacy_config()
        cls.register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        cls.canonical_sources = load_canonical_sources(WORKBOOK, cls.config.workbook)
        cls.sources = merge_supplemental_sources(
            cls.canonical_sources,
            cls.register.source_delta_sources,
        )
        cls.sources_by_id = {source.source_record_id: source for source in cls.sources}
        cls.canonical_sources_by_id = {
            source.source_record_id: source for source in cls.canonical_sources
        }
        cls.summary = _read_json(cls.run_dir / "summary.json")
        cls.ledger = _read_json(cls.run_dir / "batch_ledger.json")
        cls.source_delta_summary = _read_json(cls.source_delta_run_dir / "summary.json")
        cls.source_delta_ledger = _read_json(cls.source_delta_run_dir / "batch_ledger.json")
        cls.catalog_manifest = _read_json(cls.catalog_dir / "source_set_manifest.json")
        cls.catalog_validation = _read_json(cls.catalog_dir / "catalog_validation.json")
        cls.catalog_records = _read_jsonl(cls.catalog_dir / "source_catalog.jsonl")
        cls.catalog_by_id = {record["source_record_id"]: record for record in cls.catalog_records}
        cls.batch_records = _read_batch_records(cls.ledger)
        cls.batch_records_by_id = {
            record["source_record_id"]: record for record in cls.batch_records
        }
        cls.active_batch_records = _read_batch_records_from_ledgers(
            [cls.ledger, cls.source_delta_ledger]
        )
        cls.active_batch_records_by_id = {
            record["source_record_id"]: record for record in cls.active_batch_records
        }
        cls.override_source_ids = _override_source_ids(OVERRIDES)

    def test_full_batch_summary_matches_workbook_scope(self) -> None:
        self.assertTrue(self.summary["all_passed"])
        self.assertEqual(self.summary["run_id"], FULL_BATCH_RUN_ID)
        self.assertEqual(self.summary["planned_row_count"], len(self.canonical_sources))
        self.assertEqual(self.summary["passed_batch_count"], self.summary["batch_count"])
        self.assertEqual(self.summary["failed_batch_count"], 0)
        self.assertEqual(self.summary["needs_repair_batch_count"], 0)

        with (self.run_dir / "repair_queue.csv").open(newline="", encoding="utf-8") as handle:
            repair_rows = list(csv.DictReader(handle))
        self.assertEqual(repair_rows, [])

        batch_ids = [batch["batch_id"] for batch in self.ledger["batches"]]
        self.assertEqual(len(batch_ids), len(set(batch_ids)))
        self.assertEqual(len(batch_ids), self.summary["batch_count"])
        self.assertTrue(all(batch["status"] == "passed" for batch in self.ledger["batches"]))
        self.assertTrue(all(batch["gate_passed"] is True for batch in self.ledger["batches"]))

    def test_refresh_batch_summary_matches_source_delta_scope(self) -> None:
        self.assertTrue(self.source_delta_summary["all_passed"])
        self.assertEqual(self.source_delta_summary["run_id"], SOURCE_DELTA_BATCH_RUN_ID)
        self.assertEqual(
            self.source_delta_summary["planned_row_count"],
            len(self.register.source_delta_sources),
        )
        self.assertEqual(
            self.source_delta_summary["passed_batch_count"],
            self.source_delta_summary["batch_count"],
        )
        self.assertEqual(self.source_delta_summary["failed_batch_count"], 0)
        self.assertEqual(self.source_delta_summary["needs_repair_batch_count"], 0)
        self.assertEqual(
            self.source_delta_summary["source_delta_input"]["source_delta_count"],
            len(self.register.source_delta_sources),
        )

        with (self.source_delta_run_dir / "repair_queue.csv").open(
            newline="",
            encoding="utf-8",
        ) as handle:
            repair_rows = list(csv.DictReader(handle))
        self.assertEqual(repair_rows, [])

    def test_batch_manifests_cover_every_workbook_source_once(self) -> None:
        workbook_ids = set(self.canonical_sources_by_id)
        manifest_ids = {record["source_record_id"] for record in self.batch_records}
        self.assertEqual(manifest_ids, workbook_ids)
        self.assertEqual(len(self.batch_records), len(self.canonical_sources))

        for batch in self.ledger["batches"]:
            records = _read_jsonl(_path_from_output(batch["manifest_path"]))
            self.assertEqual(
                {record["source_record_id"] for record in records},
                set(batch["source_record_ids"]),
                msg=batch["batch_id"],
            )
            unexpected_statuses = [
                record
                for record in records
                if record["status"] not in SUCCESS_STATUSES
            ]
            self.assertEqual(unexpected_statuses, [], msg=batch["batch_id"])

        skipped_ids = sorted(
            record["source_record_id"]
            for record in self.batch_records
            if record["status"] in NON_ARTIFACT_SUCCESS_STATUSES
        )
        self.assertEqual(skipped_ids, ["R1EA-160"])

    def test_refresh_batch_manifests_cover_every_source_delta_source_once(self) -> None:
        source_delta_ids = {
            source.source_record_id for source in self.register.source_delta_sources
        }
        manifest_ids = {
            record["source_record_id"] for record in _read_batch_records(self.source_delta_ledger)
        }
        self.assertEqual(manifest_ids, source_delta_ids)

        for batch in self.source_delta_ledger["batches"]:
            records = _read_jsonl(_path_from_output(batch["manifest_path"]))
            self.assertEqual(
                {record["source_record_id"] for record in records},
                set(batch["source_record_ids"]),
                msg=batch["batch_id"],
            )
            unexpected_statuses = [
                record
                for record in records
                if record["status"] not in ARTIFACT_STATUSES
            ]
            self.assertEqual(unexpected_statuses, [], msg=batch["batch_id"])

    def test_artifact_hashes_sizes_and_duplicate_links_are_accurate(self) -> None:
        artifact_paths_by_sha: dict[str, set[str]] = {}
        for record in self.batch_records:
            self.assertIn(record["status"], SUCCESS_STATUSES)
            self.assertIsNone(record.get("failure"), msg=record["source_record_id"])
            if record["status"] in NON_ARTIFACT_SUCCESS_STATUSES:
                self.assertIsNone(record.get("artifact_sha256"), msg=record["source_record_id"])
                self.assertIsNone(record.get("artifact_path"), msg=record["source_record_id"])
                self.assertIsNone(record.get("artifact_byte_size"), msg=record["source_record_id"])
                continue

            artifact_sha = record.get("artifact_sha256")
            artifact_path_value = record.get("artifact_path")
            self.assertTrue(artifact_sha, msg=record["source_record_id"])
            self.assertTrue(artifact_path_value, msg=record["source_record_id"])
            artifact_path = _path_from_output(artifact_path_value)
            self.assertTrue(artifact_path.exists(), msg=record["source_record_id"])
            body = artifact_path.read_bytes()
            self.assertEqual(len(body), record["artifact_byte_size"], msg=record["source_record_id"])
            self.assertEqual(hashlib.sha256(body).hexdigest(), artifact_sha, msg=record["source_record_id"])
            artifact_paths_by_sha.setdefault(artifact_sha, set()).add(str(artifact_path))
            if record["status"] == "duplicate_content":
                duplicate_of = record.get("duplicate_of")
                self.assertTrue(duplicate_of, msg=record["source_record_id"])
                self.assertTrue(_path_from_output(duplicate_of).exists(), msg=record["source_record_id"])

        self.assertEqual(
            sum(int(batch.get("artifact_count") or 0) for batch in self.ledger["batches"]),
            self.summary["artifact_count"],
        )

    def test_active_catalog_artifact_count_matches_combined_batch_manifests(self) -> None:
        artifact_paths_by_sha: dict[str, set[str]] = {}
        for record in self.active_batch_records:
            if record["status"] in NON_ARTIFACT_SUCCESS_STATUSES:
                self.assertIsNone(record.get("artifact_sha256"), msg=record["source_record_id"])
                continue
            artifact_sha = record.get("artifact_sha256")
            artifact_path_value = record.get("artifact_path")
            self.assertTrue(artifact_sha, msg=record["source_record_id"])
            self.assertTrue(artifact_path_value, msg=record["source_record_id"])
            artifact_path = _path_from_output(artifact_path_value)
            self.assertTrue(artifact_path.exists(), msg=record["source_record_id"])
            artifact_paths_by_sha.setdefault(str(artifact_sha), set()).add(str(artifact_path))

        self.assertEqual(len(artifact_paths_by_sha), self.catalog_manifest["artifact_count"])

    def test_override_provenance_is_preserved_for_repaired_rows(self) -> None:
        repaired_records = [
            record for record in self.batch_records if record["original_url"] != record["effective_url"]
        ]
        self.assertEqual(
            {record["source_record_id"] for record in repaired_records},
            self.override_source_ids,
        )
        for record in repaired_records:
            metadata = record["metadata"]
            self.assertEqual(metadata.get("override_url"), record["effective_url"])
            self.assertTrue(metadata.get("override_reason"), msg=record["source_record_id"])
            self.assertEqual(record["normalized_url"], record["effective_url"])

        r1ea080 = self.batch_records_by_id["R1EA-080"]
        self.assertEqual(r1ea080["content_type"], "application/pdf")
        self.assertIn("govinfo.gov", r1ea080["effective_url"])
        self.assertEqual(r1ea080["status"], "downloaded_existing")

    def test_reviewer_catalog_matches_batch_manifests(self) -> None:
        self.assertTrue(self.catalog_validation["passed"])
        self.assertIsNone(self.catalog_manifest["download_batch_run_id"])
        self.assertEqual(
            self.catalog_manifest["download_batch_run_ids"],
            ACTIVE_BATCH_RUN_IDS,
        )
        self.assertEqual(self.catalog_manifest["source_count"], len(self.sources))
        self.assertEqual(
            self.catalog_manifest["supplemental_source_count"],
            len(self.register.source_delta_sources),
        )
        self.assertEqual(
            self.catalog_manifest["source_delta_input"]["source_delta_count"],
            len(self.register.source_delta_sources),
        )
        self.assertEqual(
            self.catalog_manifest["unique_url_count"],
            len({source.normalized_url for source in self.sources}),
        )
        self.assertEqual(set(self.catalog_by_id), set(self.active_batch_records_by_id))

        for source_id, batch_record in self.active_batch_records_by_id.items():
            catalog_record = self.catalog_by_id[source_id]
            self.assertEqual(catalog_record["source_status"], batch_record["status"], msg=source_id)
            self.assertEqual(catalog_record["artifact_sha256"], batch_record["artifact_sha256"], msg=source_id)
            self.assertEqual(catalog_record["artifact_path"], batch_record["artifact_path"], msg=source_id)
            self.assertEqual(
                catalog_record["original_url"],
                self.sources_by_id[source_id].original_url,
                msg=source_id,
            )
            self.assertEqual(catalog_record["effective_url"], batch_record["effective_url"], msg=source_id)
            self.assertEqual(catalog_record["download_run_id"], batch_record["run_id"], msg=source_id)
            expected_batch_run_id = (
                FULL_BATCH_RUN_ID
                if source_id in self.canonical_sources_by_id
                else SOURCE_DELTA_BATCH_RUN_ID
            )
            self.assertEqual(
                catalog_record["download_batch_run_id"],
                expected_batch_run_id,
                msg=source_id,
            )
            self.assertTrue(catalog_record["citation_label"], msg=source_id)
            self.assertTrue(catalog_record["review_topics"], msg=source_id)

    def test_sqlite_index_matches_catalog_outputs(self) -> None:
        sqlite_path = self.catalog_dir / "review_sources.sqlite"
        with closing(sqlite3.connect(sqlite_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT download_batch_run_id FROM source_sets").fetchone()[0],
                None,
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM sources").fetchone()[0],
                len(self.catalog_records),
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM artifacts").fetchone()[0],
                self.catalog_manifest["artifact_count"],
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM source_artifacts").fetchone()[0],
                sum(1 for record in self.catalog_records if record["artifact_sha256"]),
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM citations").fetchone()[0],
                len(self.catalog_records),
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM review_topics").fetchone()[0],
                self.catalog_manifest["review_topic_count"],
            )
            rows = connection.execute(
                "SELECT source_record_id, artifact_sha256 FROM source_artifacts"
            ).fetchall()
        sqlite_links = {source_id: sha for source_id, sha in rows}
        catalog_links = {
            record["source_record_id"]: record["artifact_sha256"]
            for record in self.catalog_records
            if record["artifact_sha256"]
        }
        self.assertEqual(sqlite_links, catalog_links)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_batch_records(ledger: dict) -> list[dict]:
    records: list[dict] = []
    for batch in ledger["batches"]:
        records.extend(_read_jsonl(_path_from_output(batch["manifest_path"])))
    return records


def _read_batch_records_from_ledgers(ledgers: list[dict]) -> list[dict]:
    records: list[dict] = []
    for ledger in ledgers:
        records.extend(_read_batch_records(ledger))
    return records


def _path_from_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def _override_source_ids(path: Path) -> set[str]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    return {override["source_record_id"] for override in payload.get("overrides", [])}


if __name__ == "__main__":
    unittest.main()
