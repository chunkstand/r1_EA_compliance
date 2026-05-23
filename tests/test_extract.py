from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import tempfile
from types import SimpleNamespace
import unittest

from usfs_r1_ea_sources.catalog import build_review_catalog
import usfs_r1_ea_sources.extract as extract_module
from usfs_r1_ea_sources.extract import build_extraction
from usfs_r1_ea_sources.extract_common import _requires_direct_document_artifact
from usfs_r1_ea_sources.source_register import load_source_register_rows

from tests.support.extract_fixtures import CANONICAL_WORKBOOK
from tests.support.extract_fixtures import CONFIG
from tests.support.extract_fixtures import DOCX_CONTENT_TYPE
from tests.support.extract_fixtures import WORKBOOK
from tests.support.extract_fixtures import XLSX_CONTENT_TYPE
from tests.support.extract_fixtures import _artifact_sha256
from tests.support.extract_fixtures import _check
from tests.support.extract_fixtures import _docx_body
from tests.support.extract_fixtures import _ecfr_part_xml_body
from tests.support.extract_fixtures import _html_body
from tests.support.extract_fixtures import _read_jsonl
from tests.support.extract_fixtures import _write_download_run
from tests.support.extract_fixtures import _write_download_run_records
from tests.support.extract_fixtures import _xhtml_xml_body
from tests.support.extract_fixtures import _xlsx_body
from tests.support.extract_fixtures import _xml_body
from tests.support.extract_fixtures import _zip_with_metadata_body
from tests.support.extract_fixtures import canonical_config
from tests.support.extract_fixtures import legacy_config


class ExtractionBuildTests(unittest.TestCase):
    def test_generic_direct_file_instruction_only_upgrades_web_source_rows(self) -> None:
        rows = {
            row.source_record_id: row
            for row in load_source_register_rows(CANONICAL_WORKBOOK)
        }
        fps_344 = rows["FPS-344"].to_workbook_source()
        fps_180 = rows["FPS-180"].to_workbook_source()

        self.assertFalse(_requires_direct_document_artifact({"metadata": fps_344.metadata}))
        self.assertTrue(_requires_direct_document_artifact({"metadata": fps_180.metadata}))

    def test_clean_text_strips_markup_like_tokens_from_pdf_fallback_text(self) -> None:
        cleaned = extract_module._clean_text("VerDate 20<MAR>2000 alpha <i> beta")

        self.assertEqual(cleaned, "VerDate 20 2000 alpha beta")

    def test_build_extraction_writes_html_text_chunks_and_manifest_provenance(self) -> None:
        config = legacy_config()
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
        config = legacy_config()
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
        config = legacy_config()
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
        config = legacy_config()
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
        config = legacy_config()
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

    def test_build_extraction_reads_xlsx_rows_into_traceable_text_blocks(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            body = _xlsx_body(
                [
                    ["Species", "Disposition", "Rationale"],
                    ["Wolverine", "Retained", "Plan revision SCC workbook"],
                    ["Whitebark pine", "Retained", "Plant SCC workbook"],
                ]
            )
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="R1-SCC-NPC-004",
                artifact_body=body,
                content_type=XLSX_CONTENT_TYPE,
                suffix=".xlsx",
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"R1-SCC-NPC-004"},
            )

            result = build_extraction(output_dir=output_dir, id_filters={"R1-SCC-NPC-004"})

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["parser_counts"], {"openpyxl_xlsx_cells": 1})
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(manifest[0]["status"], "extracted")
            self.assertEqual(manifest[0]["parser_name"], "openpyxl_xlsx_cells")
            extracted_text = Path(manifest[0]["text_path"]).read_text(encoding="utf-8")
            self.assertIn("Wolverine", extracted_text)
            self.assertIn("Whitebark pine", extracted_text)
            chunks = _read_jsonl(result.chunks_path)
            self.assertTrue(chunks)
            self.assertEqual(chunks[0]["source_record_id"], "R1-SCC-NPC-004")
            self.assertIn("[SCC Evaluation!A1:C1]", chunks[0]["text"])

    def test_build_extraction_uses_textutil_for_doc_artifacts(self) -> None:
        config = canonical_config()
        original_run = extract_module.subprocess.run

        def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            command = args[0] if args else kwargs.get("args")
            if isinstance(command, list) and command[:2] == ["git", "rev-parse"]:
                return original_run(*args, **kwargs)
            return SimpleNamespace(
                returncode=0,
                stdout="Legacy directive body text from textutil.",
                stderr="",
            )

        extract_module.subprocess.run = fake_run
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="R1-021",
                    artifact_body=b"fake doc bytes" + b" " * 256,
                    content_type="application/msword",
                    suffix=".doc",
                )
                build_review_catalog(
                    workbook_path=CANONICAL_WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                    source_record_ids={"R1-021"},
                )

                result = build_extraction(output_dir=output_dir, id_filter="R1-021")

                self.assertTrue(result.summary["validation_passed"])
                self.assertEqual(result.summary["parser_counts"], {"macos_textutil_doc": 1})
                manifest = _read_jsonl(result.extraction_manifest_path)
                self.assertEqual(manifest[0]["parser_name"], "macos_textutil_doc")
                text = Path(manifest[0]["text_path"]).read_text(encoding="utf-8")
                self.assertIn("Legacy directive body text", text)
        finally:
            extract_module.subprocess.run = original_run

    def test_build_extraction_uses_docling_for_image_artifacts(self) -> None:
        config = canonical_config()
        original_try_docling = extract_module._try_extract_docling

        def fake_try_docling(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            text = "Vegetation and elevation zones image text."
            return extract_module.ExtractionPayload(
                text=text,
                blocks=[extract_module.TextBlock(text=text, page=1)],
                parser_name="docling",
                parser_version="test",
            )

        extract_module._try_extract_docling = fake_try_docling
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="WILD-ESA-094",
                    artifact_body=b"jpeg bytes" + b" " * 256,
                    content_type="image/jpeg",
                    suffix=".jpg",
                )
                build_review_catalog(
                    workbook_path=CANONICAL_WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                    source_record_ids={"WILD-ESA-094"},
                )

                result = build_extraction(output_dir=output_dir, id_filter="WILD-ESA-094")

                self.assertTrue(result.summary["validation_passed"])
                self.assertEqual(result.summary["parser_counts"], {"docling": 1})
                manifest = _read_jsonl(result.extraction_manifest_path)
                self.assertEqual(manifest[0]["parser_name"], "docling")
                self.assertTrue(manifest[0]["direct_document_artifact_required"])
        finally:
            extract_module._try_extract_docling = original_try_docling

    def test_build_extraction_prefers_docling_for_canonical_row_instructions(self) -> None:
        config = canonical_config()
        original_try_docling = extract_module._try_extract_docling

        def fake_try_docling(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202, ARG001
            text = "Docling appendix text with preserved page labels."
            return extract_module.ExtractionPayload(
                text=text,
                blocks=[extract_module.TextBlock(text=text, page=1)],
                parser_name="docling",
                parser_version="test",
            )

        extract_module._try_extract_docling = fake_try_docling
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output_dir = Path(tmp)
                _write_download_run(
                    output_dir,
                    "unit-download",
                    source_record_id="FPS-021",
                    artifact_body=_html_body(),
                    content_type="text/html",
                    suffix=".html",
                )
                build_review_catalog(
                    workbook_path=CANONICAL_WORKBOOK,
                    output_dir=output_dir,
                    config=config,
                    config_path=CONFIG,
                    run_id="unit-download",
                    source_record_ids={"FPS-021"},
                )

                result = build_extraction(output_dir=output_dir, id_filter="FPS-021")

                self.assertTrue(result.summary["validation_passed"])
                self.assertEqual(
                    result.summary["extraction_priority_counts"],
                    {"direct_document_verification": 1},
                )
                manifest = _read_jsonl(result.extraction_manifest_path)
                self.assertEqual(manifest[0]["parser_name"], "docling")
                self.assertEqual(manifest[0]["loader_contract"], "source_register_v1")
                self.assertTrue(manifest[0]["direct_document_artifact_required"])
                self.assertEqual(manifest[0]["parser_admission_class"], "structured_web_source")
        finally:
            extract_module._try_extract_docling = original_try_docling

    def test_build_extraction_uses_zip_metadata_parser_for_direct_file_zip_artifact(self) -> None:
        config = canonical_config()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            _write_download_run(
                output_dir,
                "unit-download",
                source_record_id="FPS-420",
                artifact_body=_zip_with_metadata_body(),
                content_type="application/zip",
                suffix=".zip",
            )
            build_review_catalog(
                workbook_path=CANONICAL_WORKBOOK,
                output_dir=output_dir,
                config=config,
                config_path=CONFIG,
                run_id="unit-download",
                source_record_ids={"FPS-420"},
            )

            result = build_extraction(output_dir=output_dir, id_filter="FPS-420")

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["parser_counts"], {"python_zip_metadata_xml": 1})
            manifest = _read_jsonl(result.extraction_manifest_path)
            self.assertEqual(manifest[0]["parser_name"], "python_zip_metadata_xml")
            self.assertTrue(manifest[0]["direct_document_artifact_required"])
            text = Path(manifest[0]["text_path"]).read_text(encoding="utf-8")
            self.assertIn("Grizzly Bear Analysis Unit Shapefile", text)
            self.assertIn("Exported GIS layer package", text)

    def test_build_extraction_fails_validation_on_artifact_hash_mismatch(self) -> None:
        config = legacy_config()
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
        config = legacy_config()
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
        config = legacy_config()
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
        config = legacy_config()
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
