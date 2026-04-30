from __future__ import annotations

from contextlib import closing
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.catalog import build_review_catalog
from usfs_r1_ea_sources.config import load_config


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_current_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


class CatalogTests(unittest.TestCase):
    def test_build_review_catalog_writes_engine_artifacts(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            result = build_review_catalog(
                workbook_path=WORKBOOK,
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

            self.assertEqual(len(records), 147)
            self.assertEqual(manifest["source_count"], 147)
            self.assertEqual(manifest["unique_url_count"], 144)
            self.assertEqual(manifest["status_counts"], {"planned": 147})
            self.assertEqual(result.summary["source_count"], 147)
            self.assertGreater(result.summary["review_topic_count"], 100)

            r1ea001 = next(record for record in records if record["source_record_id"] == "R1EA-001")
            self.assertEqual(r1ea001["document_role"], "law")
            self.assertEqual(r1ea001["authority_level"], "federal")
            self.assertEqual(r1ea001["source_status"], "planned")
            self.assertTrue(r1ea001["review_topics"])

            with closing(sqlite3.connect(result.sqlite_path)) as connection:
                source_count = connection.execute("SELECT count(*) FROM sources").fetchone()[0]
                topic_count = connection.execute("SELECT count(*) FROM review_topics").fetchone()[0]
                citation_count = connection.execute("SELECT count(*) FROM citations").fetchone()[0]
            self.assertEqual(source_count, 147)
            self.assertGreater(topic_count, 100)
            self.assertEqual(citation_count, 147)

    def test_build_review_catalog_links_download_manifest_artifact(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, "unit-download")

            result = build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            records = _read_jsonl(result.source_catalog_path)
            r1ea001 = next(record for record in records if record["source_record_id"] == "R1EA-001")
            r1ea002 = next(record for record in records if record["source_record_id"] == "R1EA-002")
            self.assertEqual(r1ea001["source_status"], "downloaded")
            self.assertEqual(r1ea001["artifact_sha256"], "a" * 64)
            self.assertEqual(r1ea001["expected_parser"], "html")
            self.assertEqual(r1ea001["citation_label"], f"R1EA-001 ({'a' * 12})")
            self.assertEqual(r1ea002["source_status"], "not_in_run")

            with closing(sqlite3.connect(result.sqlite_path)) as connection:
                artifact_count = connection.execute("SELECT count(*) FROM artifacts").fetchone()[0]
                link_count = connection.execute(
                    "SELECT count(*) FROM source_artifacts"
                ).fetchone()[0]
            self.assertEqual(artifact_count, 1)
            self.assertEqual(link_count, 1)


def _write_download_run(output_dir: Path, run_id: str) -> None:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    record = {
        "run_id": run_id,
        "source_record_id": "R1EA-001",
        "status": "downloaded",
        "artifact_path": "source_library/artifacts/raw/example.html",
        "artifact_sha256": "a" * 64,
        "artifact_byte_size": 256,
        "content_type": "text/html",
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


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


if __name__ == "__main__":
    unittest.main()
