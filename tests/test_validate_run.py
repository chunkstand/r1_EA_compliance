from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.validate_run import validate_run


class ValidateRunTests(unittest.TestCase):
    def test_validate_run_passes_for_matching_artifact_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            artifact = output_dir / "artifacts" / "raw" / "example" / "source_abc.html"
            body = b"<html><body>valid source content</body></html>" + b" " * 128
            _write_run(
                output_dir,
                "gate-pass",
                [
                    _record(
                        status="downloaded",
                        artifact_path=str(artifact),
                        artifact_sha256=hashlib.sha256(body).hexdigest(),
                        artifact_byte_size=len(body),
                    )
                ],
            )
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(body)

            result = validate_run(output_dir=output_dir, run_id="gate-pass")

            self.assertTrue(result.passed)
            self.assertTrue(result.validation_path.exists())

    def test_validate_run_fails_for_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            artifact = output_dir / "artifacts" / "raw" / "example" / "source_abc.html"
            body = b"<html><body>valid source content</body></html>" + b" " * 128
            _write_run(
                output_dir,
                "gate-hash-fail",
                [
                    _record(
                        status="downloaded",
                        artifact_path=str(artifact),
                        artifact_sha256="0" * 64,
                        artifact_byte_size=len(body),
                    )
                ],
            )
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(body)

            result = validate_run(output_dir=output_dir, run_id="gate-hash-fail")

            self.assertFalse(result.passed)
            artifact_check = _check(result.report, "successful_artifacts_exist_and_match_hash")
            self.assertFalse(artifact_check["passed"])

    def test_validate_run_fails_for_unknown_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            record = _record(status="custom_failure", artifact_path=None)
            _write_run(output_dir, "gate-repair-fail", [record])

            result = validate_run(output_dir=output_dir, run_id="gate-repair-fail")

            self.assertFalse(result.passed)
            self.assertFalse(_check(result.report, "known_status_values")["passed"])

    def test_validate_run_fails_for_bad_duplicate_content_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            artifact = output_dir / "artifacts" / "raw" / "example" / "source_abc.html"
            body = b"<html><body>valid source content</body></html>" + b" " * 128
            _write_run(
                output_dir,
                "gate-dup-fail",
                [
                    _record(
                        source_record_id="SRC-1",
                        status="downloaded",
                        artifact_path=str(artifact),
                        artifact_sha256=hashlib.sha256(body).hexdigest(),
                        artifact_byte_size=len(body),
                    ),
                    _record(
                        source_record_id="SRC-2",
                        status="duplicate_content",
                        artifact_path=str(artifact),
                        artifact_sha256=hashlib.sha256(body).hexdigest(),
                        artifact_byte_size=len(body),
                        duplicate_of="missing-canonical",
                    ),
                ],
            )
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(body)

            result = validate_run(output_dir=output_dir, run_id="gate-dup-fail")

            self.assertFalse(result.passed)
            duplicate_check = _check(result.report, "duplicate_content_links_to_canonical_artifact")
            self.assertFalse(duplicate_check["passed"])

    def test_validate_run_fails_for_untraceable_url_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            record = _record(status="not_found", artifact_path=None)
            record["effective_url"] = "https://example.test/repaired-source"
            _write_run(output_dir, "gate-url-provenance-fail", [record])

            result = validate_run(output_dir=output_dir, run_id="gate-url-provenance-fail")

            self.assertFalse(result.passed)
            self.assertFalse(_check(result.report, "url_provenance_is_traceable")["passed"])

    def test_validate_run_fails_for_normalized_url_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            record = _record(status="not_found", artifact_path=None)
            record["normalized_url"] = "https://example.test/different"
            _write_run(output_dir, "gate-normalized-url-fail", [record])

            result = validate_run(output_dir=output_dir, run_id="gate-normalized-url-fail")

            self.assertFalse(result.passed)
            self.assertFalse(_check(result.report, "url_provenance_is_traceable")["passed"])

    def test_validate_run_checks_filtered_override_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            record = _record(status="not_found", artifact_path=None)
            record["effective_url"] = "https://example.test/repaired-source"
            record["metadata"] = {
                "override_url": "https://example.test/repaired-source",
                "override_reason": "Unit test repair",
            }
            _write_run(
                output_dir,
                "gate-override-count-fail",
                [record],
                summary_updates={"filtered_override_count": 0},
            )

            result = validate_run(output_dir=output_dir, run_id="gate-override-count-fail")

            self.assertFalse(result.passed)
            summary_check = _check(result.report, "summary_counts_match_manifest")
            self.assertFalse(summary_check["passed"])


def _write_run(
    output_dir: Path,
    run_id: str,
    records: list[dict],
    *,
    summary_updates: dict | None = None,
) -> None:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1
    summary = {
        "run_id": run_id,
        "mode": "download",
        "filtered_rows": len(records),
        "filtered_override_count": sum(
            1 for record in records if record.get("original_url") != record.get("effective_url")
        ),
        "status_counts": status_counts,
        "manifest_path": str(manifest_path),
        "workbook_sha256": "abc",
    }
    if summary_updates:
        summary.update(summary_updates)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )


def _record(
    *,
    source_record_id: str = "SRC-1",
    status: str,
    artifact_path: str | None,
    artifact_sha256: str | None = None,
    artifact_byte_size: int | None = None,
    duplicate_of: str | None = None,
) -> dict:
    return {
        "source_record_id": source_record_id,
        "sheet": "Ingest_Checklist",
        "excel_row": 5,
        "title": "Example",
        "original_url": "https://example.test/source",
        "effective_url": "https://example.test/source",
        "normalized_url": "https://example.test/source",
        "status": status,
        "artifact_path": artifact_path,
        "artifact_sha256": artifact_sha256,
        "artifact_byte_size": artifact_byte_size,
        "http_status": None,
        "fetch_timestamp": None,
        "duplicate_of": duplicate_of,
        "validation": {"mode": "download", "passed": status != "not_found"},
        "metadata": {},
    }


def _check(report: dict, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing check {name}")


if __name__ == "__main__":
    unittest.main()
