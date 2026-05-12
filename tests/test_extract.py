from __future__ import annotations

from pathlib import Path
import hashlib
import io
import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile

from usfs_r1_ea_sources.catalog import build_review_catalog
from usfs_r1_ea_sources.config import load_config
import usfs_r1_ea_sources.extract as extract_module
from usfs_r1_ea_sources.extract import build_extraction
from usfs_r1_ea_sources.extract import _source_derived_dir


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class ExtractionTests(unittest.TestCase):
    def test_resolve_support_document_role_prefers_r1_register_override(self) -> None:
        role = extract_module._resolve_support_document_role(
            {
                "source_record_id": "R1PLAN-custer-gallatin-nf-06",
                "document_role": "forest_plan",
                "metadata": {},
            },
            support_document_role_overrides={
                "R1PLAN-custer-gallatin-nf-06": "biological_assessment",
            },
        )

        self.assertEqual(role, "biological_assessment")

    def test_build_extraction_writes_html_text_chunks_and_manifest_provenance(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            body = _html_body()
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=body,
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["selected_source_count"], 1)
            self.assertEqual(result.summary["extracted_count"], 1)
            self.assertGreater(result.summary["chunk_count"], 0)

            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(len(manifest), 1)
            record = manifest[0]
            self.assertEqual(record["status"], "extracted")
            self.assertTrue(record["artifact_sha256_verified"])
            self.assertEqual(record["parser_name"], "python_htmlparser")
            self.assertTrue(Path(record["text_path"]).exists())
            extracted_text = Path(record["text_path"]).read_text(encoding="utf-8")
            self.assertIn("environmental impacts", extracted_text)

            chunks = _read_jsonl(result.chunks_path)
            chunk = chunks[0]
            self.assertTrue(chunk["chunk_id"].startswith("chunk:"))
            self.assertEqual(chunk["source_record_id"], "R1EA-001")
            self.assertEqual(chunk["artifact_sha256"], _artifact_sha256(body))
            self.assertTrue(chunk["citation_label"].startswith("R1EA-001"))
            self.assertEqual(chunk["support_document_role"], "law")
            self.assertEqual(chunk["char_start"], 0)
            self.assertGreater(chunk["char_end"], chunk["char_start"])
            self.assertEqual(
                chunk["content_sha256"],
                hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest(),
            )

    def test_build_extraction_uses_legal_xml_parser_for_xml_sources(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            body = _xml_body()
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-008",
                artifact_body=body,
                content_type="application/xml",
                suffix=".xml",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-008")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["parser_counts"], {"legal_xml_builtin": 1})
            chunks = _read_jsonl(result.chunks_path)
            self.assertIn("Scoping shall invite", chunks[0]["text"])
            self.assertIn("36 CFR Part 220", chunks[0]["heading"])
            self.assertTrue(chunks[0]["section"].startswith("/ECFR"))

    def test_build_extraction_scopes_ecfr_section_xml_sources(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-014",
                artifact_body=_ecfr_part_xml_body(),
                content_type="application/xml",
                suffix=".xml",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-014")

            self.assertTrue(result.summary["validation_passed"])
            text = Path(_read_jsonl(result.extraction_manifest_path)[0]["text_path"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("§ 1b.6 Finding of no significant impact", text)
            self.assertIn("FONSI content only", text)
            self.assertNotIn("§ 1b.5 Environmental assessments", text)
            self.assertNotIn("EA-only sibling content", text)
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(
                manifest[0]["parser_metadata"]["source_scope"]["identifier"],
                "1b.6",
            )
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(_check(validation, "scoped_xml_records_are_auditable")["passed"])

    def test_build_extraction_falls_back_for_xhtml_saved_as_xml(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            body = _xhtml_xml_body()
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=body,
                content_type="application/xml",
                suffix=".xml",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["parser_counts"], {"legal_xml_xhtml_fallback": 1})
            chunks = _read_jsonl(result.chunks_path)
            self.assertIn("dash entity", chunks[0]["text"])

    def test_build_extraction_uses_docx_zip_xml_parser_without_docling(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            body = _docx_body(["Decision notice", "This EA package contains mitigation measures."])
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=body,
                content_type=DOCX_CONTENT_TYPE,
                suffix=".docx",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["parser_counts"], {"python_docx_zip_xml": 1})
            text = Path(_read_jsonl(result.extraction_manifest_path)[0]["text_path"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("mitigation measures", text)

    def test_build_extraction_fails_validation_on_artifact_hash_mismatch(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            artifact_path = _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=_html_body(),
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )
            artifact_path.write_bytes(b"<html><body>changed</body></html>")

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

            self.assertFalse(result.summary["validation_passed"])
            self.assertEqual(result.summary["status_counts"], {"hash_mismatch": 1})
            self.assertEqual(_read_jsonl(result.chunks_path), [])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            hash_check = _check(validation, "no_artifact_hash_mismatches")
            self.assertFalse(hash_check["passed"])
            self.assertEqual(hash_check["details"]["source_record_ids"], ["R1EA-001"])

    def test_build_extraction_replaces_prior_derived_outputs_for_source_set(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=_html_body(),
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            first = build_extraction(output_dir=output_dir, id_filter="R1EA-001")
            stale = first.extracted_text_dir / "stale.txt"
            stale.write_text("stale", encoding="utf-8")

            second = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

            self.assertTrue(second.summary["validation_passed"])
            self.assertFalse(stale.exists())

    def test_build_extraction_can_merge_selected_refresh_into_existing_outputs(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run_records(
                output_dir,
                "unit-download",
                [
                    {
                        "source_record_id": "R1EA-001",
                        "artifact_body": _html_body(),
                        "content_type": "text/html",
                        "suffix": ".html",
                    },
                    {
                        "source_record_id": "R1EA-002",
                        "artifact_body": (
                            b"<html><body><h1>Forest Plan</h1><p>Vegetation standards apply.</p></body></html>"
                        ),
                        "content_type": "text/html",
                        "suffix": ".html",
                    },
                ],
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            first = build_extraction(
                output_dir=output_dir,
                id_filters={"R1EA-001", "R1EA-002"},
            )
            first_manifest = {
                record["source_record_id"]: record
                for record in _read_jsonl(first.extraction_manifest_path)
            }

            second = build_extraction(
                output_dir=output_dir,
                id_filter="R1EA-001",
                merge_selected_into_existing=True,
            )

            self.assertTrue(second.summary["validation_passed"])
            self.assertEqual(second.summary["selected_source_count"], 2)
            self.assertEqual(second.summary["extracted_count"], 2)
            self.assertTrue(second.summary["extraction_options"]["merge_selected_into_existing"])
            self.assertEqual(
                second.summary["extraction_options"]["refresh_source_record_ids"],
                ["R1EA-001"],
            )
            manifest = {
                record["source_record_id"]: record
                for record in _read_jsonl(second.extraction_manifest_path)
            }
            self.assertEqual(set(manifest), {"R1EA-001", "R1EA-002"})
            self.assertEqual(
                manifest["R1EA-002"]["text_sha256"],
                first_manifest["R1EA-002"]["text_sha256"],
            )
            chunks = _read_jsonl(second.chunks_path)
            self.assertEqual(
                {chunk["source_record_id"] for chunk in chunks},
                {"R1EA-001", "R1EA-002"},
            )

    def test_build_extraction_accepts_archived_catalog_dir(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=_html_body(),
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )
            archived_catalog_dir = output_dir / "runs" / "unit-archived-catalog"
            shutil.copytree(output_dir / "catalog", archived_catalog_dir)
            shutil.rmtree(output_dir / "catalog")

            result = build_extraction(
                output_dir=output_dir,
                catalog_dir=archived_catalog_dir,
                id_filter="R1EA-001",
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(
                result.summary["extraction_options"]["catalog_dir"],
                str(archived_catalog_dir),
            )
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(manifest[0]["source_record_id"], "R1EA-001")

    def test_build_extraction_reuses_existing_payload_when_requested(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=_html_body(),
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            first = build_extraction(output_dir=output_dir, id_filter="R1EA-001")
            first_manifest = _read_jsonl(first.extraction_manifest_path)
            text_path = Path(first_manifest[0]["text_path"])
            self.assertTrue(text_path.exists())

            original_extract_payload = extract_module._extract_payload

            def fail_if_called(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
                raise AssertionError("reuse_existing should not reparse unchanged artifacts")

            extract_module._extract_payload = fail_if_called
            try:
                second = build_extraction(
                    output_dir=output_dir,
                    id_filter="R1EA-001",
                    reuse_existing=True,
                )
            finally:
                extract_module._extract_payload = original_extract_payload

            self.assertTrue(second.summary["validation_passed"])
            self.assertEqual(second.summary["reused_count"], 1)
            second_manifest = _read_jsonl(second.extraction_manifest_path)
            self.assertEqual(second_manifest[0]["parser_name"], "python_htmlparser")
            self.assertTrue(second_manifest[0]["parser_metadata"]["reused_existing"])
            self.assertEqual(Path(second_manifest[0]["text_path"]), text_path)

    def test_build_extraction_reuses_prior_inventory_candidate(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            body = _html_body()
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=body,
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

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
            prior_text = "Prior extraction text keeps environmental impacts traceable."
            prior_text_path = (
                output_dir
                / "derived"
                / "source-set-prior"
                / "extracted_text"
                / "R1EA-001_prior.txt"
            )
            prior_text_path.parent.mkdir(parents=True)
            prior_text_path.write_text(prior_text + "\n", encoding="utf-8")
            text_sha256 = hashlib.sha256(prior_text.encode("utf-8")).hexdigest()
            inventory_path = output_dir / "reuse_inventory_records.jsonl"
            inventory_record = {
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
                    "parser_name": "python_htmlparser",
                    "parser_version": "test",
                    "parser_metadata": None,
                    "chunk_count": 1,
                    "text_path": str(prior_text_path),
                    "text_sha256": text_sha256,
                },
            }
            inventory_path.write_text(
                json.dumps(inventory_record, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            original_extract_payload = extract_module._extract_payload

            def fail_if_called(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
                raise AssertionError("reuse inventory should not reparse reusable artifacts")

            extract_module._extract_payload = fail_if_called
            try:
                result = build_extraction(
                    output_dir=output_dir,
                    id_filter="R1EA-001",
                    reuse_inventory_path=inventory_path,
                )
            finally:
                extract_module._extract_payload = original_extract_payload

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["reused_count"], 1)
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(manifest[0]["parser_name"], "python_htmlparser")
            self.assertEqual(
                manifest[0]["parser_metadata"]["reuse_from"],
                "inventory_prior_extraction",
            )
            self.assertEqual(
                manifest[0]["parser_metadata"]["reuse_source_set_id"],
                "source-set-prior",
            )
            self.assertIn(
                "environmental impacts",
                Path(manifest[0]["text_path"]).read_text(encoding="utf-8"),
            )

    def test_build_extraction_treats_scope_excluded_rows_as_terminal(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-160",
                status="skipped_excluded",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

            result = build_extraction(output_dir=output_dir, id_filter="R1EA-160")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["skipped_excluded_count"], 1)
            self.assertEqual(result.summary["failed_count"], 0)
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(manifest[0]["status"], "skipped_excluded")
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(_check(validation, "all_required_rows_extracted")["passed"])

    def test_reuse_inventory_prevents_loose_text_reuse_for_needs_extract_rows(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=_html_body(),
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

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
            current_text_path = (
                output_dir
                / "derived"
                / source_set_id
                / "extracted_text"
                / f"R1EA-001_{catalog_row['artifact_sha256'][:16]}.txt"
            )
            current_text_path.parent.mkdir(parents=True)
            current_text_path.write_text("Loose stale text should not be reused.\n", encoding="utf-8")
            inventory_path = output_dir / "reuse_inventory_records.jsonl"
            inventory_record = {
                "source_set_id": source_set_id,
                "source_record_id": "R1EA-001",
                "classification": "needs_extract",
                "artifact_check": {"passed": True},
                "artifact_sha256": catalog_row["artifact_sha256"],
                "expected_parser": catalog_row["expected_parser"],
                "content_type": catalog_row["content_type"],
                "reuse_candidate": None,
            }
            inventory_path.write_text(
                json.dumps(inventory_record, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = build_extraction(
                output_dir=output_dir,
                id_filter="R1EA-001",
                reuse_existing=True,
                reuse_inventory_path=inventory_path,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["reused_count"], 0)
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(manifest[0]["parser_name"], "python_htmlparser")
            self.assertIn(
                "National Environmental Policy Act",
                Path(manifest[0]["text_path"]).read_text(encoding="utf-8"),
            )

    def test_build_extraction_reports_pdf_failure_when_docling_is_unavailable(self) -> None:
        if importlib.util.find_spec("docling") is not None:
            self.skipTest("Docling is installed in this Python environment.")
        config = load_config(CONFIG)
        original_resolve_external = extract_module._resolve_external_docling_python
        original_pdf_fallback = extract_module._try_extract_pdf_text_fallback
        extract_module._resolve_external_docling_python = lambda: None
        extract_module._try_extract_pdf_text_fallback = lambda artifact_path: None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="R1EA-001",
                    artifact_body=_pdf_body(),
                    content_type="application/pdf",
                    suffix=".pdf",
                )
                build_review_catalog(
                    workbook_path=WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                )

                result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

                self.assertFalse(result.summary["validation_passed"])
                self.assertEqual(result.summary["expected_parser_counts"], {"pdf": 1})
                self.assertEqual(result.summary["failure_counts"], {"docling_unavailable": 1})
                manifest = _read_jsonl(result.extraction_manifest_path)
                self.assertEqual(manifest[0]["status"], "parser_error")
                self.assertEqual(manifest[0]["failure"]["error_class"], "docling_unavailable")
        finally:
            extract_module._resolve_external_docling_python = original_resolve_external
            extract_module._try_extract_pdf_text_fallback = original_pdf_fallback

    def test_build_extraction_falls_back_when_docling_is_unavailable(self) -> None:
        if importlib.util.find_spec("docling") is not None:
            self.skipTest("Docling is installed in this Python environment.")
        config = load_config(CONFIG)
        original_resolve_external = extract_module._resolve_external_docling_python
        original_pdf_fallback = extract_module._try_extract_pdf_text_fallback
        extract_module._resolve_external_docling_python = lambda: None
        extract_module._try_extract_pdf_text_fallback = lambda artifact_path: extract_module.ExtractionPayload(
            text="Fallback text when docling is unavailable.",
            blocks=[extract_module.TextBlock(text="Fallback text when docling is unavailable.", page=1)],
            parser_name="pypdf_text_fallback",
            parser_version="test",
            metadata={"pypdf_max_decompress_bytes": extract_module.PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES},
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="R1EA-001",
                    artifact_body=_pdf_body(),
                    content_type="application/pdf",
                    suffix=".pdf",
                )
                build_review_catalog(
                    workbook_path=WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                )

                result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

                self.assertTrue(result.summary["validation_passed"])
                self.assertEqual(result.summary["parser_counts"], {"pypdf_text_fallback": 1})
                self.assertEqual(result.summary["fallback_counts"], {"docling": 1})
                manifest = _read_jsonl(result.extraction_manifest_path)
                self.assertEqual(manifest[0]["status"], "extracted")
                self.assertEqual(manifest[0]["parser_name"], "pypdf_text_fallback")
                self.assertEqual(
                    manifest[0]["parser_metadata"]["fallback_error_class"],
                    "docling_unavailable",
                )
        finally:
            extract_module._resolve_external_docling_python = original_resolve_external
            extract_module._try_extract_pdf_text_fallback = original_pdf_fallback

    def test_build_extraction_uses_external_docling_when_active_python_lacks_docling(self) -> None:
        if importlib.util.find_spec("docling") is not None:
            self.skipTest("Docling is installed in this Python environment.")
        config = load_config(CONFIG)
        original_find_spec = extract_module.importlib.util.find_spec
        original_resolve_external = extract_module._resolve_external_docling_python
        original_try_external = extract_module._try_extract_docling_external

        def fake_find_spec(name: str):  # noqa: ANN202
            if name == "docling":
                return None
            return original_find_spec(name)

        def fake_try_external(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            text = "External Docling text."
            return extract_module.ExtractionPayload(
                text=text,
                blocks=[extract_module.TextBlock(text=text, page=1)],
                parser_name="docling",
                parser_version="test",
            )

        extract_module.importlib.util.find_spec = fake_find_spec
        extract_module._resolve_external_docling_python = lambda: Path("/tmp/fake-docling-python")
        extract_module._try_extract_docling_external = fake_try_external
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="R1EA-001",
                    artifact_body=_pdf_body(),
                    content_type="application/pdf",
                    suffix=".pdf",
                )
                build_review_catalog(
                    workbook_path=WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                )

                result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")

                self.assertTrue(result.summary["validation_passed"])
                manifest = _read_jsonl(result.extraction_manifest_path)
                self.assertEqual(manifest[0]["status"], "extracted")
                self.assertEqual(manifest[0]["parser_name"], "docling")
                self.assertEqual(
                    manifest[0]["parser_metadata"]["docling_execution"],
                    "external_python",
                )
        finally:
            extract_module.importlib.util.find_spec = original_find_spec
            extract_module._resolve_external_docling_python = original_resolve_external
            extract_module._try_extract_docling_external = original_try_external

    def test_build_extraction_accepts_reuse_inventory_bundle_path(self) -> None:
        config = load_config(CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1EA-001",
                artifact_body=_html_body(),
                content_type="text/html",
                suffix=".html",
            )
            build_review_catalog(
                workbook_path=WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
            )

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
            prior_text_dir = output_dir / "derived" / "source-set-prior" / "extracted_text"
            prior_text_dir.mkdir(parents=True, exist_ok=True)
            prior_text_path = prior_text_dir / f"R1EA-001_{catalog_row['artifact_sha256'][:16]}.txt"
            prior_text = "Prior reusable text."
            prior_text_path.write_text(prior_text, encoding="utf-8")
            inventory_path = output_dir / "derived" / source_set_id / "reuse_inventory"
            inventory_path.mkdir(parents=True, exist_ok=True)
            inventory_record = {
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
                    "chunk_count": 1,
                    "text_path": str(prior_text_path),
                    "text_sha256": hashlib.sha256(prior_text.encode("utf-8")).hexdigest(),
                    "parser_name": "unit-parser",
                    "parser_version": "1",
                    "parser_metadata": {},
                },
            }
            (inventory_path / "reuse_inventory.json").write_text(
                json.dumps({"summary": {"source_set_id": source_set_id}, "records": [inventory_record]}),
                encoding="utf-8",
            )

            result = build_extraction(
                output_dir=output_dir,
                id_filter="R1EA-001",
                reuse_inventory_path=inventory_path / "reuse_inventory.json",
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["reused_count"], 1)
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(
                manifest[0]["parser_metadata"]["reuse_from"],
                "inventory_prior_extraction",
            )

    def test_build_extraction_uses_pdf_text_fallback_after_docling_timeout(self) -> None:
        config = load_config(CONFIG)
        original_docling = extract_module._try_extract_docling
        original_fallback = extract_module._try_extract_pdf_text_fallback

        def timeout_docling(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            raise extract_module.ExtractionFailure("docling_timeout", "timeout")

        def fallback_pdf_text(artifact_path: Path):  # noqa: ANN202, ARG001
            text = "Fallback PDF text remains traceable."
            return extract_module.ExtractionPayload(
                text=text,
                blocks=[extract_module.TextBlock(text=text, page=1)],
                parser_name="pypdf_text_fallback",
                parser_version="test",
            )

        extract_module._try_extract_docling = timeout_docling
        extract_module._try_extract_pdf_text_fallback = fallback_pdf_text
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="R1EA-001",
                    artifact_body=_pdf_body(),
                    content_type="application/pdf",
                    suffix=".pdf",
                )
                build_review_catalog(
                    workbook_path=WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                )

                result = build_extraction(output_dir=output_dir, id_filter="R1EA-001")
                chunks = _read_jsonl(result.chunks_path)
                manifest = _read_jsonl(result.extraction_manifest_path)
                validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
        finally:
            extract_module._try_extract_docling = original_docling
            extract_module._try_extract_pdf_text_fallback = original_fallback

        self.assertTrue(result.summary["validation_passed"])
        self.assertEqual(result.summary["parser_counts"], {"pypdf_text_fallback": 1})
        self.assertEqual(result.summary["fallback_counts"], {"docling": 1})
        self.assertIn("Fallback PDF text", chunks[0]["text"])
        self.assertEqual(manifest[0]["parser_name"], "pypdf_text_fallback")
        self.assertEqual(manifest[0]["parser_metadata"]["fallback_from"], "docling")
        self.assertEqual(manifest[0]["parser_metadata"]["fallback_error_class"], "docling_timeout")
        self.assertTrue(_check(validation, "fallback_records_are_auditable")["passed"])

    def test_source_derived_dir_rejects_unsafe_source_set_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                _source_derived_dir(Path(tmp), "../outside")


def _write_download_run(
    output_dir: Path,
    run_id: str,
    *,
    source_record_id: str,
    artifact_body: bytes = b"",
    content_type: str = "text/html",
    suffix: str = ".html",
    status: str = "downloaded",
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    artifact = output_dir / "artifacts" / "raw" / f"{run_id}-{source_record_id}{suffix}"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if status != "skipped_excluded":
        artifact.write_bytes(artifact_body)
    record = {
        "run_id": run_id,
        "source_record_id": source_record_id,
        "status": status,
        "artifact_path": str(artifact) if status != "skipped_excluded" else None,
        "artifact_sha256": _artifact_sha256(artifact_body)
        if status != "skipped_excluded"
        else None,
        "artifact_byte_size": len(artifact_body) if status != "skipped_excluded" else None,
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
        "status_counts": {status: 1},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    return artifact


def _write_download_run_records(output_dir: Path, run_id: str, records: list[dict]) -> None:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    manifest_records = []
    for record in records:
        artifact = output_dir / "artifacts" / "raw" / f"{run_id}-{record['source_record_id']}{record['suffix']}"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(record["artifact_body"])
        manifest_records.append(
            {
                "run_id": run_id,
                "source_record_id": record["source_record_id"],
                "status": "downloaded",
                "artifact_path": str(artifact),
                "artifact_sha256": _artifact_sha256(record["artifact_body"]),
                "artifact_byte_size": len(record["artifact_body"]),
                "content_type": record["content_type"],
                "fetch_timestamp": "2026-04-30T00:00:00Z",
                "final_url": "https://example.test/final",
            }
        )
    manifest_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": len(manifest_records),
        "status_counts": {"downloaded": len(manifest_records)},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")


def _html_body() -> bytes:
    return (
        b"<html><body><h1>National Environmental Policy Act</h1>"
        b"<p>Agencies shall consider environmental impacts and alternatives.</p>"
        b"<p>Evidence must remain traceable to the administrative record.</p></body></html>"
    )


def _xml_body() -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b"<ECFR><TITLE><HEAD>36 CFR Part 220</HEAD><SECTION>"
        b"<SECTNO>Section 220.4</SECTNO>"
        b"<P>Scoping shall invite public comment and document environmental concerns.</P>"
        b"</SECTION></TITLE></ECFR>"
    )


def _ecfr_part_xml_body() -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<DIV5 N="1b" TYPE="PART">'
        b"<HEAD>PART 1b-NATIONAL ENVIRONMENT POLICY ACT</HEAD>"
        b'<DIV8 N="1b.5" TYPE="SECTION" '
        b' hierarchy_metadata="{&quot;path&quot;:&quot;/on/date/title-7/section-1b.5&quot;}">'
        b"<HEAD>&#xA7; 1b.5 Environmental assessments.</HEAD>"
        b"<P>EA-only sibling content should not leak into section 1b.6.</P>"
        b"</DIV8>"
        b'<DIV8 N="1b.6" TYPE="SECTION" '
        b' hierarchy_metadata="{&quot;path&quot;:&quot;/on/date/title-7/section-1b.6&quot;}">'
        b"<HEAD>&#xA7; 1b.6 Finding of no significant impact.</HEAD>"
        b"<P>FONSI content only.</P>"
        b"</DIV8>"
        b"</DIV5>"
    )


def _xhtml_xml_body() -> bytes:
    return (
        b"<?xml version='1.0' encoding='UTF-8' ?>"
        b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
        b'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
        b"<html><head><title>U.S. Code XHTML</title></head><body>"
        b"<h1>NEPA</h1><p>Text with dash entity &mdash; and traceability.</p>"
        b"</body></html>"
    )


def _docx_body(paragraphs: list[str]) -> bytes:
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paragraph_xml = "".join(
        f"<w:p><w:r><w:t>{_xml_escape(paragraph)}</w:t></w:r></w:p>"
        for paragraph in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{namespace}"><w:body>{paragraph_xml}</w:body></w:document>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document_xml)
    buffer.seek(0)
    return buffer.read()


def _pdf_body() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [] /Count 0 >> endobj\n"
        b"trailer << /Root 1 0 R >>\n%%EOF\n"
    )


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _artifact_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")


if __name__ == "__main__":
    unittest.main()
