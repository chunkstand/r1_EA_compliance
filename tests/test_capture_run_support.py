from __future__ import annotations

from pathlib import Path
import csv
import tempfile
import unittest

from usfs_r1_ea_sources.capture_run_support import (
    build_capture_manifest_record,
    read_jsonl,
    resolve_manifest_path,
    write_failures_csv,
    write_jsonl,
)
from usfs_r1_ea_sources.records import WorkbookSource


def _source() -> WorkbookSource:
    return WorkbookSource(
        source_record_id="SRC-001",
        sheet="Document_Register_Master",
        excel_row=12,
        source_id="DOC-001",
        title="Example Source",
        original_url="https://example.test/source",
        effective_url="https://example.test/source",
        normalized_url="https://example.test/source",
        metadata={"issuer": "Test Issuer"},
    )


class CaptureRunSupportTests(unittest.TestCase):
    def test_build_capture_manifest_record_preserves_common_fields_and_extras(self) -> None:
        source = _source()
        artifact_path = Path("/tmp/example.pdf")

        record = build_capture_manifest_record(
            run_id="unit-run",
            workbook_path=Path("/tmp/workbook.xlsx"),
            workbook_sha256="abc123",
            source=source,
            status="downloaded",
            final_url=source.effective_url,
            redirect_chain=[],
            content_type="application/pdf",
            content_length=512,
            http_status=200,
            attempt_count=1,
            fetch_timestamp="2026-05-20T00:00:00Z",
            validation={"mode": "download", "passed": True, "reason": None},
            duplicate_of=None,
            failure=None,
            artifact_path=artifact_path,
            artifact_sha256="deadbeef",
            artifact_byte_size=512,
            extra_fields={"planned_artifact_path": "/tmp/planned.raw"},
        )

        self.assertEqual(record["run_id"], "unit-run")
        self.assertEqual(record["source_record_id"], source.source_record_id)
        self.assertEqual(record["artifact_path"], str(artifact_path))
        self.assertEqual(record["artifact_sha256"], "deadbeef")
        self.assertEqual(record["planned_artifact_path"], "/tmp/planned.raw")
        self.assertEqual(record["metadata"], source.metadata)

    def test_write_jsonl_and_read_jsonl_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            records = [{"source_record_id": "SRC-001"}, {"source_record_id": "SRC-002"}]

            write_jsonl(path, records)

            self.assertEqual(read_jsonl(path), records)

    def test_write_failures_csv_excludes_non_failure_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "failures.csv"
            records = [
                {
                    "source_record_id": "SRC-001",
                    "sheet": "Sheet1",
                    "excel_row": 1,
                    "source_id": "DOC-001",
                    "title": "Downloaded",
                    "original_url": "https://example.test/downloaded",
                    "status": "downloaded",
                    "attempt_count": 1,
                    "failure": None,
                },
                {
                    "source_record_id": "SRC-002",
                    "sheet": "Sheet1",
                    "excel_row": 2,
                    "source_id": "DOC-002",
                    "title": "Failed",
                    "original_url": "https://example.test/failed",
                    "status": "failed",
                    "attempt_count": 3,
                    "failure": {
                        "error_class": "TimeoutError",
                        "error_message": "timed out",
                    },
                },
            ]

            write_failures_csv(path, records)

            rows = list(csv.DictReader(path.open(encoding="utf-8")))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_record_id"], "SRC-002")
            self.assertEqual(rows[0]["status"], "failed")
            self.assertEqual(rows[0]["attempt_count"], "3")

    def test_resolve_manifest_path_falls_back_to_default_manifest_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            manifest_path = output_dir / "manifests" / "download_unit-run.jsonl"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text("", encoding="utf-8")

            resolved = resolve_manifest_path(
                output_dir,
                {"run_id": "unit-run", "mode": "download", "manifest_path": "missing.jsonl"},
            )

            self.assertEqual(resolved, manifest_path)
