from __future__ import annotations

from contextlib import closing
from dataclasses import replace
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.catalog import build_review_catalog
from usfs_r1_ea_sources.config import (
    LEGACY_WORKBOOK_LOADER_CONTRACT,
    load_config,
)
from usfs_r1_ea_sources.forest_plan_inventory_build_manifest import (
    load_region1_forest_plan_inventory_build_manifest,
)
from usfs_r1_ea_sources.workbook import load_canonical_sources
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


class CatalogTests(unittest.TestCase):
    def test_build_review_catalog_writes_engine_artifacts(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            result = build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=Path(tmp),
                config=config,
                config_path=CONFIG,
            )

            self.assertTrue(result.source_catalog_path.exists())
            self.assertTrue(result.source_set_manifest_path.exists())
            self.assertTrue(result.sqlite_path.exists())
            self.assertTrue(result.graph_nodes_path.exists())
            self.assertTrue(result.graph_edges_path.exists())
            records = _read_jsonl(result.source_catalog_path)
            manifest = json.loads(result.source_set_manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(len(records), 635)
            self.assertEqual(manifest["source_count"], 635)
            self.assertEqual(manifest["unique_url_count"], 635)
            self.assertEqual(manifest["status_counts"], {"planned": 635})
            self.assertIsNone(manifest["overrides_path"])
            self.assertIsNone(manifest["overrides_sha256"])
            self.assertEqual(result.summary["source_count"], 635)
            self.assertGreater(result.summary["review_topic_count"], 0)
            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.validation_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

            fed001 = next(record for record in records if record["source_record_id"] == "FED-001")
            self.assertEqual(fed001["document_role"], "law")
            self.assertEqual(fed001["authority_level"], "federal")
            self.assertEqual(fed001["source_status"], "planned")
            self.assertEqual(fed001["source_partition"], "candidate_blocked_source")
            self.assertEqual(
                fed001["source_partition_basis"],
                "blocked_or_unavailable_status:planned",
            )
            self.assertTrue(fed001["review_topics"])
            self.assertEqual(
                manifest["source_partition_counts"],
                {"candidate_blocked_source": 635},
            )
            self.assertNotIn("source_document", manifest["document_role_counts"])

            with closing(sqlite3.connect(result.sqlite_path)) as connection:
                source_count = connection.execute("SELECT count(*) FROM sources").fetchone()[0]
                topic_count = connection.execute("SELECT count(*) FROM review_topics").fetchone()[0]
                citation_count = connection.execute("SELECT count(*) FROM citations").fetchone()[0]
                partition_count = connection.execute(
                    "SELECT count(*) FROM sources WHERE source_partition = ?",
                    ("candidate_blocked_source",),
                ).fetchone()[0]
            self.assertEqual(source_count, 635)
            self.assertGreater(topic_count, 0)
            self.assertEqual(citation_count, 635)
            self.assertEqual(partition_count, 635)

    def test_build_review_catalog_rejects_legacy_source_delta_when_canonical_loader_active(self) -> None:
        config = load_config(CONFIG)
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "sole active source ledger"):
                build_review_catalog(
                    workbook_path=CANONICAL_WORKBOOK,
                    output_dir=Path(tmp),
                    config=config,
                    config_path=CONFIG,
                    supplemental_sources=register.source_delta_sources,
                    source_delta_input=register.summary(),
                )

    def test_build_review_catalog_links_download_manifest_artifact(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, "unit-download")

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            records = _read_jsonl(result.source_catalog_path)
            r1ea001 = next(record for record in records if record["source_record_id"] == "R1EA-001")
            r1ea002 = next(record for record in records if record["source_record_id"] == "R1EA-002")
            self.assertEqual(r1ea001["source_status"], "downloaded")
            self.assertEqual(r1ea001["artifact_sha256"], _artifact_sha256())
            self.assertEqual(r1ea001["expected_parser"], "html")
            self.assertEqual(r1ea001["citation_label"], f"R1EA-001 ({_artifact_sha256()[:12]})")
            self.assertEqual(r1ea001["source_partition"], "active_review_corpus")
            self.assertEqual(r1ea002["source_status"], "not_in_run")
            self.assertEqual(r1ea002["source_partition"], "candidate_blocked_source")
            self.assertTrue(result.summary["validation_passed"])

            with closing(sqlite3.connect(result.sqlite_path)) as connection:
                artifact_count = connection.execute("SELECT count(*) FROM artifacts").fetchone()[0]
                link_count = connection.execute(
                    "SELECT count(*) FROM source_artifacts"
                ).fetchone()[0]
            self.assertEqual(artifact_count, 1)
            self.assertEqual(link_count, 1)

    def test_build_review_catalog_links_batch_download_manifests(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_001 = _write_download_run(
                output_dir,
                "unit-batch-uscode-001",
                source_record_id="R1EA-001",
                artifact_body=b"<html><body>batch artifact 1</body></html>" + b" " * 128,
            )
            manifest_002 = _write_download_run(
                output_dir,
                "unit-batch-ecfr-001",
                source_record_id="R1EA-008",
                artifact_body=b"<xml><body>batch artifact 2</body></xml>" + b" " * 128,
                content_type="application/xml",
            )
            _write_batch_run(
                output_dir,
                "unit-batches",
                [
                    ("unit-batch-uscode-001", manifest_001),
                    ("unit-batch-ecfr-001", manifest_002),
                ],
            )

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_id="unit-batches",
            )

            records = _read_jsonl(result.source_catalog_path)
            manifest = json.loads(result.source_set_manifest_path.read_text(encoding="utf-8"))
            r1ea001 = next(record for record in records if record["source_record_id"] == "R1EA-001")
            r1ea008 = next(record for record in records if record["source_record_id"] == "R1EA-008")
            r1ea002 = next(record for record in records if record["source_record_id"] == "R1EA-002")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["download_batch_run_id"], "unit-batches")
            self.assertEqual(result.summary["artifact_count"], 2)
            self.assertEqual(manifest["download_batch_run_id"], "unit-batches")
            self.assertEqual(r1ea001["source_status"], "downloaded")
            self.assertEqual(r1ea001["download_run_id"], "unit-batch-uscode-001")
            self.assertEqual(r1ea001["download_batch_run_id"], "unit-batches")
            self.assertEqual(r1ea008["expected_parser"], "xml")
            self.assertEqual(r1ea002["source_status"], "not_in_run")
            self.assertIsNone(r1ea002["download_run_id"])
            self.assertEqual(r1ea002["download_batch_run_id"], "unit-batches")

            with closing(sqlite3.connect(result.sqlite_path)) as connection:
                artifact_count = connection.execute("SELECT count(*) FROM artifacts").fetchone()[0]
                batch_id = connection.execute(
                    "SELECT download_batch_run_id FROM source_sets"
                ).fetchone()[0]
            self.assertEqual(artifact_count, 2)
            self.assertEqual(batch_id, "unit-batches")

    def test_build_review_catalog_accepts_r1_forest_plan_source_delta_batch(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_id = "R1PLAN-beaverhead-deerlodge-nf-03"
        source_delta_ids = {
            source.source_record_id for source in register.source_delta_sources
        }
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_path = _write_download_run(
                output_dir,
                "unit-r1-delta-batch-001",
                source_record_id=source_id,
                artifact_body=b"%PDF-1.4 catalog artifact" + b" " * 128,
                content_type="application/pdf",
            )
            _write_batch_run(output_dir, "unit-r1-delta-batches", [("unit-r1-delta-batch-001", manifest_path)])

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_id="unit-r1-delta-batches",
                source_record_ids=source_delta_ids,
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
            )

            records = _read_jsonl(result.source_catalog_path)
            manifest = json.loads(result.source_set_manifest_path.read_text(encoding="utf-8"))
            record = next(row for row in records if row["source_record_id"] == source_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["source_count"], 160)
            self.assertEqual(result.summary["supplemental_source_count"], 160)
            self.assertEqual(result.summary["source_record_id_filter_count"], 160)
            self.assertEqual(result.summary["source_delta_input"]["source_delta_count"], 160)
            self.assertEqual(manifest["source_count"], 160)
            self.assertEqual(manifest["source_delta_input"]["source_delta_count"], 160)
            self.assertEqual(record["sheet"], "R1_Forest_Plan_Document_Register")
            self.assertEqual(record["document_role"], "forest_plan_support")
            self.assertEqual(record["authority_level"], "forest")
            self.assertEqual(record["source_status"], "downloaded")
            self.assertEqual(record["expected_parser"], "pdf")
            self.assertEqual(manifest["document_role_counts"], {"forest_plan": 5, "forest_plan_support": 155})

            for primary_source_id in _source_delta_primary_plan_source_record_ids(register):
                primary_record = next(
                    row for row in records if row["source_record_id"] == primary_source_id
                )
                self.assertEqual(primary_record["document_role"], "forest_plan")

    def test_build_review_catalog_merges_canonical_and_source_delta_batch_runs(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        source_id = "R1PLAN-beaverhead-deerlodge-nf-03"
        canonical_source_ids = [
            source.source_record_id
            for source in load_canonical_sources(LEGACY_WORKBOOK, config.workbook)
        ]
        source_delta_ids = [
            source.source_record_id for source in register.source_delta_sources
        ]
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            canonical_manifest_path = _write_download_run_records(
                output_dir,
                "unit-canonical-batch-001",
                source_record_ids=canonical_source_ids,
                content_type="text/html",
            )
            source_delta_manifest_path = _write_download_run_records(
                output_dir,
                "unit-r1-delta-batch-001",
                source_record_ids=source_delta_ids,
                content_type="application/pdf",
            )
            _write_batch_run(
                output_dir,
                "unit-canonical-batches",
                [("unit-canonical-batch-001", canonical_manifest_path)],
            )
            _write_batch_run(
                output_dir,
                "unit-r1-delta-batches",
                [("unit-r1-delta-batch-001", source_delta_manifest_path)],
            )
            archive_dir = output_dir / "runs" / "unit-merged-gate" / "catalog_gate"

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_ids=["unit-canonical-batches", "unit-r1-delta-batches"],
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
                catalog_dir=archive_dir,
            )

            records = _read_jsonl(result.source_catalog_path)
            manifest = json.loads(result.source_set_manifest_path.read_text(encoding="utf-8"))
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            r1ea001 = next(record for record in records if record["source_record_id"] == "R1EA-001")
            r1ea002 = next(record for record in records if record["source_record_id"] == "R1EA-002")
            source_delta = next(record for record in records if record["source_record_id"] == source_id)

            self.assertEqual(result.catalog_dir, archive_dir)
            self.assertFalse((output_dir / "catalog").exists())
            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["source_count"], 350)
            self.assertIsNone(result.summary["download_batch_run_id"])
            self.assertEqual(
                result.summary["download_batch_run_ids"],
                ["unit-canonical-batches", "unit-r1-delta-batches"],
            )
            self.assertEqual(manifest["source_count"], 350)
            self.assertEqual(manifest["download_batch_run_id"], None)
            self.assertEqual(
                manifest["download_batch_run_ids"],
                ["unit-canonical-batches", "unit-r1-delta-batches"],
            )
            self.assertEqual(manifest["supplemental_source_count"], 160)
            self.assertEqual(manifest["source_delta_input"]["source_delta_count"], 160)
            self.assertEqual(manifest["source_record_id_filter_count"], None)
            self.assertEqual(manifest["document_role_counts"]["forest_plan"], 33)
            self.assertEqual(manifest["document_role_counts"]["forest_plan_support"], 155)
            self.assertEqual(r1ea001["source_status"], "downloaded")
            self.assertEqual(r1ea001["download_batch_run_id"], "unit-canonical-batches")
            self.assertEqual(source_delta["source_status"], "downloaded")
            self.assertEqual(source_delta["download_batch_run_id"], "unit-r1-delta-batches")
            self.assertEqual(source_delta["document_role"], "forest_plan_support")
            self.assertEqual(r1ea002["source_status"], "downloaded")
            self.assertEqual(r1ea002["download_batch_run_id"], "unit-canonical-batches")
            self.assertTrue(_check(validation, "merged_batch_download_parent_count")["passed"])
            self.assertTrue(
                _check(
                    validation,
                    "merged_catalog_batch_runs_cover_all_catalog_records",
                )["passed"]
            )
            self.assertTrue(
                _check(
                    validation,
                    "merged_batch_download_manifest_has_no_duplicate_source_records",
                )["passed"]
            )

            with closing(sqlite3.connect(result.sqlite_path)) as connection:
                source_count = connection.execute("SELECT count(*) FROM sources").fetchone()[0]
                link_count = connection.execute(
                    "SELECT count(*) FROM source_artifacts"
                ).fetchone()[0]
            self.assertEqual(source_count, 350)
            self.assertEqual(link_count, 350)

    def test_build_review_catalog_validation_fails_for_duplicate_sources_across_batch_runs(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            first_manifest_path = _write_download_run(
                output_dir,
                "unit-canonical-batch-001",
                source_record_id="R1EA-001",
            )
            second_manifest_path = _write_download_run(
                output_dir,
                "unit-second-batch-001",
                source_record_id="R1EA-001",
            )
            _write_batch_run(
                output_dir,
                "unit-canonical-batches",
                [("unit-canonical-batch-001", first_manifest_path)],
            )
            _write_batch_run(
                output_dir,
                "unit-second-batches",
                [("unit-second-batch-001", second_manifest_path)],
            )

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_ids=["unit-canonical-batches", "unit-second-batches"],
            )

            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            check = _check(
                validation,
                "merged_batch_download_manifest_has_no_duplicate_source_records",
            )
            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(check["passed"])
            self.assertEqual(check["details"]["duplicate_source_record_ids"], ["R1EA-001"])

    def test_build_review_catalog_validation_fails_when_merged_batch_runs_leave_rows_uncovered(self) -> None:
        config = legacy_config()
        register = load_r1_forest_plan_document_register(R1_FOREST_PLAN_REGISTER)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            canonical_manifest_path = _write_download_run(
                output_dir,
                "unit-canonical-batch-001",
                source_record_id="R1EA-001",
            )
            source_delta_manifest_path = _write_download_run(
                output_dir,
                "unit-r1-delta-batch-001",
                source_record_id="R1PLAN-beaverhead-deerlodge-nf-03",
                artifact_body=b"%PDF-1.4 catalog artifact" + b" " * 128,
                content_type="application/pdf",
            )
            _write_batch_run(
                output_dir,
                "unit-canonical-batches",
                [("unit-canonical-batch-001", canonical_manifest_path)],
            )
            _write_batch_run(
                output_dir,
                "unit-r1-delta-batches",
                [("unit-r1-delta-batch-001", source_delta_manifest_path)],
            )

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_ids=["unit-canonical-batches", "unit-r1-delta-batches"],
                supplemental_sources=register.source_delta_sources,
                source_delta_input=register.summary(),
            )

            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            check = _check(
                validation,
                "merged_catalog_batch_runs_cover_all_catalog_records",
            )
            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(check["passed"])
            self.assertGreater(check["details"]["not_in_run_count"], 300)

    def test_build_review_catalog_validation_fails_for_unknown_manifest_source(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, "unit-download", source_record_id="UNKNOWN-001")

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            check = _check(validation, "download_manifest_source_records_are_in_workbook")
            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(check["passed"])
            self.assertEqual(check["details"]["unknown_source_record_ids"], ["UNKNOWN-001"])

    def test_build_review_catalog_validation_fails_for_unknown_batch_manifest_source(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_path = _write_download_run(
                output_dir,
                "unit-batch-unknown-001",
                source_record_id="UNKNOWN-001",
            )
            _write_batch_run(output_dir, "unit-batches", [("unit-batch-unknown-001", manifest_path)])

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_id="unit-batches",
            )

            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            check = _check(validation, "download_manifest_source_records_are_in_workbook")
            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(check["passed"])
            self.assertEqual(check["details"]["unknown_source_record_ids"], ["UNKNOWN-001"])

    def test_build_review_catalog_validation_fails_for_batch_ledger_row_mismatch(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_path = _write_download_run(
                output_dir,
                "unit-batch-mismatch-001",
                source_record_id="R1EA-001",
            )
            _write_batch_run(output_dir, "unit-batches", [("unit-batch-mismatch-001", manifest_path)])
            ledger_path = output_dir / "runs" / "unit-batches" / "batch_ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["batches"][0]["source_record_ids"] = ["R1EA-002"]
            ledger_path.write_text(json.dumps(ledger, sort_keys=True), encoding="utf-8")

            result = build_review_catalog(
                workbook_path=LEGACY_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                batch_run_id="unit-batches",
            )

            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            check = _check(validation, "batch_download_manifest_rows_match_ledger")
            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(check["passed"])
            self.assertEqual(check["details"]["mismatches"][0]["missing_source_record_ids"], ["R1EA-002"])
            self.assertEqual(
                check["details"]["mismatches"][0]["unexpected_source_record_ids"],
                ["R1EA-001"],
            )


def _write_download_run(
    output_dir: Path,
    run_id: str,
    *,
    source_record_id: str = "R1EA-001",
    artifact_body: bytes | None = None,
    content_type: str = "text/html",
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    body = artifact_body or _artifact_body()
    artifact = output_dir / "artifacts" / "raw" / f"{run_id}-{source_record_id}.html"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(body)
    record = {
        "run_id": run_id,
        "source_record_id": source_record_id,
        "status": "downloaded",
        "artifact_path": str(artifact),
        "artifact_sha256": _artifact_sha256(body),
        "artifact_byte_size": len(body),
        "content_type": content_type,
        "fetch_timestamp": "2026-04-30T00:00:00Z",
        "final_url": "https://example.test/final",
    }
    manifest_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": 1,
        "status_counts": {"downloaded": 1},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    return manifest_path


def _write_download_run_records(
    output_dir: Path,
    run_id: str,
    *,
    source_record_ids: list[str],
    content_type: str,
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    artifact_dir = output_dir / "artifacts" / "raw"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    extension = "pdf" if content_type == "application/pdf" else "html"
    records = []
    for source_record_id in source_record_ids:
        if extension == "pdf":
            body = f"%PDF-1.4 catalog artifact {source_record_id}".encode("utf-8") + b" " * 128
        else:
            body = (
                f"<html><body>catalog artifact {source_record_id}</body></html>".encode("utf-8")
                + b" " * 128
            )
        artifact = artifact_dir / f"{run_id}-{source_record_id}.{extension}"
        artifact.write_bytes(body)
        records.append(
            {
                "run_id": run_id,
                "source_record_id": source_record_id,
                "status": "downloaded",
                "artifact_path": str(artifact),
                "artifact_sha256": _artifact_sha256(body),
                "artifact_byte_size": len(body),
                "content_type": content_type,
                "fetch_timestamp": "2026-04-30T00:00:00Z",
                "final_url": f"https://example.test/{source_record_id}",
            }
        )
    manifest_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": len(source_record_ids),
        "status_counts": {"downloaded": len(source_record_ids)},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    return manifest_path


def _write_batch_run(output_dir: Path, batch_run_id: str, batches: list[tuple[str, Path]]) -> None:
    run_dir = output_dir / "runs" / batch_run_id
    run_dir.mkdir(parents=True)
    ledger_path = run_dir / "batch_ledger.json"
    ledger_batches = [
        {
            "batch_id": batch_id,
            "status": "passed",
            "gate_passed": True,
            "manifest_path": str(manifest_path),
            "source_record_ids": [
                record["source_record_id"] for record in _read_jsonl(manifest_path)
            ],
        }
        for batch_id, manifest_path in batches
    ]
    ledger_path.write_text(
        json.dumps({"run_id": batch_run_id, "batches": ledger_batches}, sort_keys=True),
        encoding="utf-8",
    )
    summary = {
        "run_id": batch_run_id,
        "all_passed": True,
        "batch_count": len(batches),
        "failed_batch_count": 0,
        "needs_repair_batch_count": 0,
        "ledger_path": str(ledger_path),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _artifact_body() -> bytes:
    return b"<html><body>catalog artifact</body></html>" + b" " * 128


def _artifact_sha256(body: bytes | None = None) -> str:
    return hashlib.sha256(body or _artifact_body()).hexdigest()


def _source_delta_primary_plan_source_record_ids(register) -> list[str]:
    manifest = load_region1_forest_plan_inventory_build_manifest()
    source_delta_ids = {source.source_record_id for source in register.source_delta_sources}
    return sorted(
        row.primary_plan_source_record_id
        for row in manifest.profile_rows
        if row.primary_plan_source_record_id in source_delta_ids
    )


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")


if __name__ == "__main__":
    unittest.main()
