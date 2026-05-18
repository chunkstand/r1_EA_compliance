from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.catalog import build_review_catalog
from usfs_r1_ea_sources.config import LEGACY_WORKBOOK_LOADER_CONTRACT, load_config
from usfs_r1_ea_sources.extract import build_extraction
from usfs_r1_ea_sources.extraction_accuracy import run_extraction_accuracy_audit


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


class ExtractionAccuracyAuditTests(unittest.TestCase):
    def test_audit_passes_generated_html_extraction(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, artifact_body=_html_body())
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )
            build_extraction(output_dir=output_dir, id_filter="R1EA-001")

            result = run_extraction_accuracy_audit(output_dir=output_dir)

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.output_path.exists())

    def test_audit_fails_when_chunk_text_no_longer_matches_offsets(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, artifact_body=_html_body())
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )
            extraction = build_extraction(output_dir=output_dir, id_filter="R1EA-001")
            chunks = [
                json.loads(line)
                for line in extraction.chunks_path.read_text(encoding="utf-8").splitlines()
            ]
            chunks[0]["text"] = "tampered"
            extraction.chunks_path.write_text(
                "\n".join(json.dumps(chunk, sort_keys=True) for chunk in chunks) + "\n",
                encoding="utf-8",
            )

            result = run_extraction_accuracy_audit(output_dir=output_dir)

            self.assertFalse(result.summary["passed"])
            check = _check(result.summary, "chunks_match_extracted_text_offsets")
            self.assertFalse(check["passed"])

    def test_audit_blocks_reused_extraction_when_contract_requires_direct_parse(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, artifact_body=_html_body())
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )
            extraction = build_extraction(output_dir=output_dir, id_filter="R1EA-001")
            manifest = [
                json.loads(line)
                for line in extraction.extraction_manifest_path.read_text(encoding="utf-8").splitlines()
            ]
            manifest[0]["parser_metadata"] = {"reused_existing": True}
            extraction.extraction_manifest_path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in manifest) + "\n",
                encoding="utf-8",
            )
            contract_path = output_dir / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verified-extraction-admission-contract-v0",
                        "contracts": [
                            {
                                "contract_id": "direct-html",
                                "required_source_record_ids": ["R1EA-001"],
                                "require_direct_extraction": True,
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_extraction_accuracy_audit(
                output_dir=output_dir,
                contract_path=contract_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                [],
            )
            self.assertEqual(
                result.summary["knowledge_base_blocked_source_record_ids"],
                ["R1EA-001"],
            )
            check = _check(result.summary, "required_source_records_are_present_and_direct")
            self.assertFalse(check["passed"])

    def test_audit_ignores_partial_overlap_with_direct_extraction_contract(self) -> None:
        config = legacy_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(output_dir, artifact_body=_html_body())
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )
            build_extraction(output_dir=output_dir, id_filter="R1EA-001")
            contract_path = output_dir / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verified-extraction-admission-contract-v0",
                        "contracts": [
                            {
                                "contract_id": "full-set-only",
                                "required_source_record_ids": ["R1EA-001", "R1EA-999"],
                                "require_direct_extraction": True,
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_extraction_accuracy_audit(
                output_dir=output_dir,
                contract_path=contract_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["verified_extraction_admission_contracts"], [])
            self.assertEqual(result.summary["required_direct_source_record_ids"], [])
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                ["R1EA-001"],
            )


def _write_download_run(output_dir: Path, *, artifact_body: bytes) -> None:
    run_dir = output_dir / "runs" / "unit-download"
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "artifacts" / "raw" / "unit-download-R1EA-001.html"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(artifact_body)
    record = {
        "run_id": "unit-download",
        "source_record_id": "R1EA-001",
        "status": "downloaded",
        "artifact_path": str(artifact),
        "artifact_sha256": hashlib.sha256(artifact_body).hexdigest(),
        "artifact_byte_size": len(artifact_body),
        "content_type": "text/html",
        "fetch_timestamp": "2026-04-30T00:00:00Z",
        "final_url": "https://example.test/final",
    }
    (manifest_dir / "download_unit-download.jsonl").write_text(
        json.dumps(record, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "run_id": "unit-download",
        "mode": "download",
        "manifest_path": str(manifest_dir / "download_unit-download.jsonl"),
        "filtered_rows": 1,
        "status_counts": {"downloaded": 1},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")


def _html_body() -> bytes:
    return (
        b"<html><body><h1>National Environmental Policy Act</h1>"
        b"<p>Agencies shall consider environmental impacts and alternatives.</p>"
        b"<p>Evidence must remain traceable to the administrative record.</p></body></html>"
    )


def _check(summary: dict, name: str) -> dict:
    return next(check for check in summary["checks"] if check["name"] == name)
