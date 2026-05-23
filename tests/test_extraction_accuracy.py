from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import hashlib
import io
import json
import tempfile
import unittest
import zipfile

from openpyxl import Workbook

from usfs_r1_ea_sources.catalog import build_review_catalog
from usfs_r1_ea_sources.config import LEGACY_WORKBOOK_LOADER_CONTRACT, load_config
from usfs_r1_ea_sources.extract import build_extraction
import usfs_r1_ea_sources.extraction_accuracy as extraction_accuracy_module
from usfs_r1_ea_sources.extraction_accuracy import run_extraction_accuracy_audit


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
VERIFIED_ADMISSION_CONTRACT = ROOT / "config" / "verified_extraction_admission_contract.json"


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


def canonical_config():
    config = load_config(CONFIG)
    return replace(config, workbook=replace(config.workbook, overrides_path=None))


class ExtractionAccuracyAuditTests(unittest.TestCase):
    def test_per_source_failure_map_ignores_non_failure_metric_rows(self) -> None:
        failures = extraction_accuracy_module._per_source_failure_map(
            [
                {
                    "name": "pdf_text_crosscheck_against_pypdf",
                    "passed": False,
                    "details": {
                        "failures": [{"source_record_id": "R1EA-001"}],
                        "metrics": [
                            {"source_record_id": "R1EA-001"},
                            {"source_record_id": "R1EA-002"},
                        ],
                    },
                }
            ],
            relevant_source_record_ids=["R1EA-001", "R1EA-002"],
        )

        self.assertEqual(
            failures,
            {"R1EA-001": ["pdf_text_crosscheck_against_pypdf"]},
        )

    def test_pdf_crosscheck_skips_self_reference_for_pypdf_fallback_records(self) -> None:
        result = extraction_accuracy_module._check_pdf_text_crosscheck(
            [
                {
                    "source_record_id": "R1EA-PDF-001",
                    "status": "extracted",
                    "content_type": "application/pdf",
                    "artifact_path": "missing.pdf",
                    "parser_name": "pypdf_text_fallback",
                }
            ],
            {},
            ROOT,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["details"]["checked_record_count"], 0)
        self.assertEqual(result["details"]["skipped_record_count"], 1)
        self.assertEqual(
            result["details"]["skipped"],
            [
                {
                    "source_record_id": "R1EA-PDF-001",
                    "reason": "self_reference_pypdf_fallback",
                }
            ],
        )

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

    def test_audit_accepts_verified_inventory_reuse_when_payload_cache_matches(self) -> None:
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
            initial = build_extraction(output_dir=output_dir, id_filter="R1EA-001")
            catalog_row = next(
                row
                for row in _read_jsonl(output_dir / "catalog" / "source_catalog.jsonl")
                if row["source_record_id"] == "R1EA-001"
            )
            source_set_id = json.loads(
                (output_dir / "catalog" / "source_set_manifest.json").read_text(
                    encoding="utf-8"
                )
            )["source_set_id"]
            initial_manifest = _read_jsonl(initial.extraction_manifest_path)
            prior_text_path = (
                output_dir
                / "derived"
                / "source-set-prior"
                / "extracted_text"
                / f"R1EA-001_{catalog_row['artifact_sha256'][:16]}.txt"
            )
            prior_text_path.parent.mkdir(parents=True, exist_ok=True)
            prior_text = Path(initial_manifest[0]["text_path"]).read_text(encoding="utf-8").strip()
            prior_text_path.write_text(prior_text + "\n", encoding="utf-8")
            prior_payload_cache_path = (
                output_dir
                / "derived"
                / "source-set-prior"
                / "diagnostics"
                / "payload_cache"
                / f"R1EA-001_{catalog_row['artifact_sha256'][:16]}.json"
            )
            prior_payload_cache_path.parent.mkdir(parents=True, exist_ok=True)
            current_payload_cache_path = (
                output_dir
                / "derived"
                / source_set_id
                / "diagnostics"
                / "payload_cache"
                / f"R1EA-001_{catalog_row['artifact_sha256'][:16]}.json"
            )
            prior_payload_cache_path.write_text(
                current_payload_cache_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            inventory_path = output_dir / "reuse_inventory_records.jsonl"
            inventory_path.write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "source_record_id": "R1EA-001",
                        "classification": "reuse_extraction",
                        "artifact_check": {"passed": True},
                        "artifact_sha256": catalog_row["artifact_sha256"],
                        "expected_parser": catalog_row["expected_parser"],
                        "content_type": catalog_row["content_type"],
                        "reuse_candidate": {
                            "source_set_id": "source-set-prior",
                            "source_record_id": "R1EA-001",
                            "status": "extracted",
                            "artifact_sha256": catalog_row["artifact_sha256"],
                            "expected_parser": catalog_row["expected_parser"],
                            "content_type": catalog_row["content_type"],
                            "parser_name": initial_manifest[0]["parser_name"],
                            "parser_version": initial_manifest[0]["parser_version"],
                            "parser_metadata": initial_manifest[0]["parser_metadata"],
                            "chunk_count": initial_manifest[0]["chunk_count"],
                            "text_path": str(prior_text_path),
                            "text_sha256": initial_manifest[0]["text_sha256"],
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            extraction = build_extraction(
                output_dir=output_dir,
                id_filter="R1EA-001",
                reuse_inventory_path=inventory_path,
            )
            manifest = _read_jsonl(extraction.extraction_manifest_path)
            self.assertEqual(
                manifest[0]["parser_metadata"]["reuse_from"],
                "inventory_prior_extraction",
            )
            self.assertTrue(manifest[0]["parser_metadata"]["verified_reuse_admissible"])
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

            self.assertTrue(result.summary["passed"])
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                ["R1EA-001"],
            )
            self.assertEqual(result.summary["knowledge_base_blocked_source_record_ids"], [])

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

    def test_audit_blocks_wrapper_page_when_direct_document_artifact_is_required(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                source_record_id="FOR-002",
                artifact_body=(
                    b"<html><body><h1>Forest Plan Landing Page</h1>"
                    b"<p>Download the direct file from this wrapper page.</p></body></html>"
                ),
                suffix=".html",
                content_type="text/html",
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"FOR-002"},
            )
            build_extraction(output_dir=output_dir, id_filter="FOR-002")
            contract_path = output_dir / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verified-extraction-admission-contract-v0",
                        "contracts": [
                            {
                                "contract_id": "wrapper-direct-file",
                                "required_source_record_ids": ["FOR-002"],
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
            self.assertEqual(result.summary["knowledge_base_admitted_source_record_ids"], [])
            self.assertEqual(
                result.summary["knowledge_base_blocked_source_record_ids"],
                ["FOR-002"],
            )
            check = _check(result.summary, "direct_document_required_records_use_document_artifacts")
            self.assertFalse(check["passed"])

    def test_committed_verified_admission_contract_audits_active_review_blockers(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run_records(
                output_dir,
                records=[
                    {
                        "source_record_id": "FED-001",
                        "artifact_body": _html_body(),
                        "suffix": ".html",
                        "content_type": "text/html",
                    },
                    {
                        "source_record_id": "FOR-002",
                        "artifact_body": (
                            b"<html><body><h1>Forest Plan Landing Page</h1>"
                            b"<p>Download the direct file from this wrapper page.</p></body></html>"
                        ),
                        "suffix": ".html",
                        "content_type": "text/html",
                    },
                ],
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"FED-001", "FOR-002"},
            )
            build_extraction(output_dir=output_dir, id_filters={"FED-001", "FOR-002"})

            result = run_extraction_accuracy_audit(
                output_dir=output_dir,
                contract_path=VERIFIED_ADMISSION_CONTRACT,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["verified_extraction_admission_contracts"][0]["contract_id"],
                "canonical-source-register-active-current-admission",
            )
            self.assertEqual(
                result.summary["audited_source_record_ids"],
                ["FED-001", "FOR-002"],
            )
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                ["FED-001"],
            )
            self.assertEqual(
                result.summary["knowledge_base_blocked_source_record_ids"],
                ["FOR-002"],
            )

    def test_committed_verified_admission_contract_reports_explicit_archive_boundary(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run_records(
                output_dir,
                records=[
                    {
                        "source_record_id": "FED-001",
                        "artifact_body": _html_body(),
                        "suffix": ".html",
                        "content_type": "text/html",
                    },
                    {
                        "source_record_id": "SUP-004",
                        "artifact_body": _html_body(),
                        "suffix": ".html",
                        "content_type": "text/html",
                    },
                ],
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"FED-001", "SUP-004"},
            )
            build_extraction(output_dir=output_dir, id_filters={"FED-001", "SUP-004"})

            result = run_extraction_accuracy_audit(
                output_dir=output_dir,
                contract_path=VERIFIED_ADMISSION_CONTRACT,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(
                result.summary["verified_extraction_admission_contracts"][0]["contract_id"],
                "canonical-source-register-active-current-admission",
            )
            self.assertEqual(result.summary["audited_source_record_ids"], ["FED-001"])
            self.assertEqual(
                result.summary["explicitly_non_admitted_source_record_ids"],
                ["SUP-004"],
            )
            self.assertEqual(
                result.summary["verified_extraction_admission_contracts"][0][
                    "non_admitted_source_record_ids"
                ],
                ["SUP-004"],
            )

    def test_audit_accepts_zip_metadata_parser_for_direct_file_zip_artifact(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                source_record_id="FPS-420",
                artifact_body=_zip_with_metadata_body(),
                suffix=".zip",
                content_type="application/zip",
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"FPS-420"},
            )
            build_extraction(output_dir=output_dir, id_filter="FPS-420")
            contract_path = output_dir / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verified-extraction-admission-contract-v0",
                        "contracts": [
                            {
                                "contract_id": "zip-direct-file",
                                "required_source_record_ids": ["FPS-420"],
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
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                ["FPS-420"],
            )
            self.assertEqual(result.summary["knowledge_base_blocked_source_record_ids"], [])

    def test_audit_accepts_xlsx_parser_for_direct_file_workbook_artifact(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                source_record_id="R1-SCC-CGNF-005",
                artifact_body=_xlsx_body(),
                suffix=".xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"R1-SCC-CGNF-005"},
            )
            build_extraction(output_dir=output_dir, id_filter="R1-SCC-CGNF-005")
            contract_path = output_dir / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verified-extraction-admission-contract-v0",
                        "contracts": [
                            {
                                "contract_id": "xlsx-direct-file",
                                "required_source_record_ids": ["R1-SCC-CGNF-005"],
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
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                ["R1-SCC-CGNF-005"],
            )
            self.assertEqual(result.summary["knowledge_base_blocked_source_record_ids"], [])

    def test_audit_selector_contracts_resolve_canonical_active_review_rows(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run_records(
                output_dir,
                records=[
                    {
                        "source_record_id": "FED-001",
                        "artifact_body": _html_body(),
                        "suffix": ".html",
                        "content_type": "text/html",
                    },
                    {
                        "source_record_id": "SUP-004",
                        "artifact_body": _html_body(),
                        "suffix": ".html",
                        "content_type": "text/html",
                    },
                ],
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"FED-001", "SUP-004"},
            )
            build_extraction(output_dir=output_dir, id_filters={"FED-001", "SUP-004"})
            contract_path = output_dir / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": "verified-extraction-admission-contract-v0",
                        "contracts": [
                            {
                                "contract_id": "canonical-active-review-only",
                                "required_record_selectors": [
                                    {
                                        "loader_contracts": ["source_register_v1"],
                                        "source_partitions": ["active_review_corpus"],
                                        "currentness_status_not_contains": ["Superseded"]
                                    }
                                ],
                                "non_admitted_record_selectors": [
                                    {
                                        "loader_contracts": ["source_register_v1"],
                                        "source_partitions": [
                                            "currentness_supersession_archive"
                                        ]
                                    }
                                ],
                                "require_direct_extraction": True
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
            self.assertEqual(
                result.summary["audited_source_record_ids"],
                ["FED-001"],
            )
            self.assertEqual(
                result.summary["knowledge_base_admitted_source_record_ids"],
                ["FED-001"],
            )
            self.assertEqual(result.summary["knowledge_base_blocked_source_record_ids"], [])
            self.assertEqual(
                result.summary["explicitly_non_admitted_source_record_ids"],
                ["SUP-004"],
            )
            self.assertEqual(
                result.summary["verified_extraction_admission_contracts"][0][
                    "non_admitted_source_record_ids"
                ],
                ["SUP-004"],
            )


def _write_download_run(
    output_dir: Path,
    *,
    artifact_body: bytes,
    source_record_id: str = "R1EA-001",
    suffix: str = ".html",
    content_type: str = "text/html",
) -> None:
    run_dir = output_dir / "runs" / "unit-download"
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "artifacts" / "raw" / f"unit-download-{source_record_id}{suffix}"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(artifact_body)
    record = {
        "run_id": "unit-download",
        "source_record_id": source_record_id,
        "status": "downloaded",
        "artifact_path": str(artifact),
        "artifact_sha256": hashlib.sha256(artifact_body).hexdigest(),
        "artifact_byte_size": len(artifact_body),
        "content_type": content_type,
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


def _write_download_run_records(output_dir: Path, *, records: list[dict]) -> None:
    run_dir = output_dir / "runs" / "unit-download"
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "download_unit-download.jsonl"
    serialized = []
    for definition in records:
        source_record_id = str(definition["source_record_id"])
        suffix = str(definition.get("suffix") or ".html")
        artifact = output_dir / "artifacts" / "raw" / f"unit-download-{source_record_id}{suffix}"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact_body = definition["artifact_body"]
        artifact.write_bytes(artifact_body)
        serialized.append(
            {
                "run_id": "unit-download",
                "source_record_id": source_record_id,
                "status": "downloaded",
                "artifact_path": str(artifact),
                "artifact_sha256": hashlib.sha256(artifact_body).hexdigest(),
                "artifact_byte_size": len(artifact_body),
                "content_type": str(definition.get("content_type") or "text/html"),
                "fetch_timestamp": "2026-04-30T00:00:00Z",
                "final_url": "https://example.test/final",
            }
        )
    manifest_path.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in serialized) + "\n",
        encoding="utf-8",
    )
    summary = {
        "run_id": "unit-download",
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": len(serialized),
        "status_counts": {"downloaded": len(serialized)},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")


def _html_body() -> bytes:
    return (
        b"<html><body><h1>National Environmental Policy Act</h1>"
        b"<p>Agencies shall consider environmental impacts and alternatives.</p>"
        b"<p>Evidence must remain traceable to the administrative record.</p></body></html>"
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _zip_with_metadata_body() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("GrizAnalysisUnits_LNF_10302023.shp", b"placeholder shapefile bytes")
        archive.writestr(
            "GrizAnalysisUnits_LNF_10302023.shp.xml",
            (
                "<metadata><idinfo><citation><citeinfo><title>Grizzly Bear Analysis Units"
                "</title></citeinfo></citation></idinfo><dataqual><lineage><procstep>"
                "<procdesc>Metadata describes the Flathead analysis unit coverage.</procdesc>"
                "</procstep></lineage></dataqual></metadata>"
            ),
        )
    return buffer.getvalue()


def _xlsx_body() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Species"
    sheet["A1"] = "Common Name"
    sheet["B1"] = "Status"
    sheet["A2"] = "Canada lynx"
    sheet["B2"] = "Present"
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _check(summary: dict, name: str) -> dict:
    return next(check for check in summary["checks"] if check["name"] == name)
