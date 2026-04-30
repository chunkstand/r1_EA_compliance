from __future__ import annotations

from pathlib import Path
from contextlib import closing
import csv
import hashlib
import json
import sqlite3
import tomllib
import unittest

from usfs_r1_ea_sources.config import load_config
from usfs_r1_ea_sources.workbook import load_canonical_sources


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
OVERRIDES = ROOT / "config" / "url_overrides.toml"
SOURCE_LIBRARY = ROOT / "source_library"
FULL_BATCH_RUN_ID = "corpus-update-2026-04-30-batches"
ARTIFACT_STATUSES = {"downloaded", "downloaded_existing", "duplicate_content", "duplicate_url"}
NON_ARTIFACT_SUCCESS_STATUSES = {"skipped_excluded"}
SUCCESS_STATUSES = ARTIFACT_STATUSES | NON_ARTIFACT_SUCCESS_STATUSES


class CapturedLibraryIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.run_dir = SOURCE_LIBRARY / "runs" / FULL_BATCH_RUN_ID
        cls.catalog_dir = SOURCE_LIBRARY / "catalog"
        required_paths = [
            cls.run_dir / "summary.json",
            cls.run_dir / "batch_ledger.json",
            cls.run_dir / "repair_queue.csv",
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

        cls.config = load_config(CONFIG)
        cls.sources = load_canonical_sources(WORKBOOK, cls.config.workbook)
        cls.sources_by_id = {source.source_record_id: source for source in cls.sources}
        cls.summary = _read_json(cls.run_dir / "summary.json")
        cls.ledger = _read_json(cls.run_dir / "batch_ledger.json")
        cls.catalog_manifest = _read_json(cls.catalog_dir / "source_set_manifest.json")
        cls.catalog_validation = _read_json(cls.catalog_dir / "catalog_validation.json")
        cls.catalog_records = _read_jsonl(cls.catalog_dir / "source_catalog.jsonl")
        cls.catalog_by_id = {record["source_record_id"]: record for record in cls.catalog_records}
        cls.batch_records = _read_batch_records(cls.ledger)
        cls.batch_records_by_id = {
            record["source_record_id"]: record for record in cls.batch_records
        }
        cls.override_source_ids = _override_source_ids(OVERRIDES)

    def test_full_batch_summary_matches_workbook_scope(self) -> None:
        self.assertTrue(self.summary["all_passed"])
        self.assertEqual(self.summary["run_id"], FULL_BATCH_RUN_ID)
        self.assertEqual(self.summary["planned_row_count"], len(self.sources))
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

    def test_batch_manifests_cover_every_workbook_source_once(self) -> None:
        workbook_ids = set(self.sources_by_id)
        manifest_ids = {record["source_record_id"] for record in self.batch_records}
        self.assertEqual(manifest_ids, workbook_ids)
        self.assertEqual(len(self.batch_records), len(self.sources))

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

        unique_artifact_count = len(artifact_paths_by_sha)
        self.assertEqual(unique_artifact_count, self.catalog_manifest["artifact_count"])
        self.assertEqual(
            sum(int(batch.get("artifact_count") or 0) for batch in self.ledger["batches"]),
            self.summary["artifact_count"],
        )

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
        self.assertEqual(self.catalog_manifest["download_batch_run_id"], FULL_BATCH_RUN_ID)
        self.assertEqual(self.catalog_manifest["source_count"], len(self.sources))
        self.assertEqual(
            self.catalog_manifest["unique_url_count"],
            len({source.normalized_url for source in self.sources}),
        )
        self.assertEqual(set(self.catalog_by_id), set(self.batch_records_by_id))

        for source_id, batch_record in self.batch_records_by_id.items():
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
            self.assertEqual(catalog_record["download_batch_run_id"], FULL_BATCH_RUN_ID, msg=source_id)
            self.assertTrue(catalog_record["citation_label"], msg=source_id)
            self.assertTrue(catalog_record["review_topics"], msg=source_id)

    def test_sqlite_index_matches_catalog_outputs(self) -> None:
        sqlite_path = self.catalog_dir / "review_sources.sqlite"
        with closing(sqlite3.connect(sqlite_path)) as connection:
            self.assertEqual(
                connection.execute("SELECT download_batch_run_id FROM source_sets").fetchone()[0],
                FULL_BATCH_RUN_ID,
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
