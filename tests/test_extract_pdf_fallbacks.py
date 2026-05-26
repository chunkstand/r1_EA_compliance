from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from usfs_r1_ea_sources.catalog import build_review_catalog
import usfs_r1_ea_sources.extract as extract_module
from usfs_r1_ea_sources.extract import build_extraction

from tests.support.extract_fixtures import CONFIG
from tests.support.extract_fixtures import WORKBOOK
from tests.support.extract_fixtures import _check
from tests.support.extract_fixtures import _pdf_body
from tests.support.extract_fixtures import _read_jsonl
from tests.support.extract_fixtures import _write_download_run
from tests.support.extract_fixtures import legacy_config


class ExtractionPdfFallbackTests(unittest.TestCase):
    def test_docling_wrapper_helpers_accept_injected_facade_module(self) -> None:
        original_try_external = extract_module.extract_docling_support._try_extract_docling_external
        original_try_isolated = extract_module.extract_docling_support._try_extract_docling_isolated
        captured: dict[str, object] = {}

        def fake_try_external(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            captured["external_facade_module"] = kwargs["facade_module"]
            return None

        def fake_try_isolated(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            captured["isolated_facade_module"] = kwargs["facade_module"]
            return None

        extract_module.extract_docling_support._try_extract_docling_external = fake_try_external
        extract_module.extract_docling_support._try_extract_docling_isolated = fake_try_isolated
        sentinel = object()
        try:
            self.assertIsNone(
                extract_module._try_extract_docling_external(
                    Path("/tmp/docling.pdf"),
                    ocr_enabled=False,
                    timeout_seconds=1.0,
                    python_path=Path("/tmp/docling-python"),
                    facade_module=sentinel,
                )
            )
            self.assertIsNone(
                extract_module._try_extract_docling_isolated(
                    Path("/tmp/docling.pdf"),
                    ocr_enabled=False,
                    timeout_seconds=1.0,
                    facade_module=sentinel,
                )
            )
        finally:
            extract_module.extract_docling_support._try_extract_docling_external = original_try_external
            extract_module.extract_docling_support._try_extract_docling_isolated = original_try_isolated

        self.assertIs(captured["external_facade_module"], sentinel)
        self.assertIs(captured["isolated_facade_module"], sentinel)

    def test_build_extraction_reports_pdf_failure_when_docling_is_unavailable(self) -> None:
        if importlib.util.find_spec("docling") is not None:
            self.skipTest("Docling is installed in this Python environment.")
        config = legacy_config()
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
        config = legacy_config()
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
        config = legacy_config()
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

    def test_build_extraction_uses_pdf_text_fallback_after_docling_timeout(self) -> None:
        config = legacy_config()
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

    def test_build_extraction_uses_chunked_docling_after_pdf_text_empty(self) -> None:
        config = legacy_config()
        original_docling = extract_module._try_extract_docling
        original_fallback = extract_module._try_extract_pdf_text_fallback
        original_raster = extract_module._try_extract_pdf_raster_ocr
        original_chunked = extract_module._try_extract_chunked_docling_pdf

        def timeout_docling(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            raise extract_module.ExtractionFailure("docling_timeout", "timeout")

        def empty_pdf_text(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            raise extract_module.ExtractionFailure(
                "pdf_text_fallback_empty",
                "PDF text fallback produced no text.",
            )

        def chunked_docling(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            text = "Chunked Docling OCR recovered scanned appendix text."
            return extract_module.ExtractionPayload(
                text=text,
                blocks=[extract_module.TextBlock(text=text, page=12)],
                parser_name="docling",
                parser_version="test",
                metadata={
                    "fallback_from": "docling_chunked_pdf",
                    "fallback_error_class": "pdf_text_fallback_empty",
                    "chunked_pdf_chunk_count": 2,
                    "chunked_pdf_page_chunk_size": 10,
                    "chunked_pdf_page_count": 20,
                },
            )

        extract_module._try_extract_docling = timeout_docling
        extract_module._try_extract_pdf_text_fallback = empty_pdf_text
        extract_module._try_extract_pdf_raster_ocr = lambda *args, **kwargs: None
        extract_module._try_extract_chunked_docling_pdf = chunked_docling
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
            extract_module._try_extract_pdf_raster_ocr = original_raster
            extract_module._try_extract_chunked_docling_pdf = original_chunked

        self.assertTrue(result.summary["validation_passed"])
        self.assertEqual(result.summary["parser_counts"], {"docling": 1})
        self.assertEqual(result.summary["fallback_counts"], {"docling_chunked_pdf": 1})
        self.assertIn("Chunked Docling OCR", chunks[0]["text"])
        self.assertEqual(manifest[0]["parser_name"], "docling")
        self.assertEqual(manifest[0]["parser_metadata"]["fallback_from"], "docling_chunked_pdf")
        self.assertEqual(
            manifest[0]["parser_metadata"]["fallback_error_class"],
            "pdf_text_fallback_empty",
        )
        self.assertTrue(_check(validation, "fallback_records_are_auditable")["passed"])

    def test_build_extraction_uses_pdf_raster_ocr_after_pdf_text_empty(self) -> None:
        config = legacy_config()
        original_docling = extract_module._try_extract_docling
        original_fallback = extract_module._try_extract_pdf_text_fallback
        original_raster = extract_module._try_extract_pdf_raster_ocr
        original_chunked = extract_module._try_extract_chunked_docling_pdf

        def timeout_docling(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            raise extract_module.ExtractionFailure("docling_timeout", "timeout")

        def empty_pdf_text(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            raise extract_module.ExtractionFailure(
                "pdf_text_fallback_empty",
                "PDF text fallback produced no text.",
            )

        def raster_ocr(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
            text = "Raster OCR recovered scanned appendix text."
            return extract_module.ExtractionPayload(
                text=text,
                blocks=[extract_module.TextBlock(text=text, page=7)],
                parser_name="rapidocr_pdf_raster",
                parser_version="torch",
                metadata={
                    "fallback_from": "pdf_raster_ocr",
                    "fallback_error_class": "pdf_text_fallback_empty",
                    "pdf_raster_ocr_dpi": extract_module.PDF_RASTER_OCR_DPI,
                    "pdf_raster_ocr_page_count": 12,
                },
            )

        extract_module._try_extract_docling = timeout_docling
        extract_module._try_extract_pdf_text_fallback = empty_pdf_text
        extract_module._try_extract_pdf_raster_ocr = raster_ocr
        extract_module._try_extract_chunked_docling_pdf = lambda *args, **kwargs: None
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
            extract_module._try_extract_pdf_raster_ocr = original_raster
            extract_module._try_extract_chunked_docling_pdf = original_chunked

        self.assertTrue(result.summary["validation_passed"])
        self.assertEqual(result.summary["parser_counts"], {"rapidocr_pdf_raster": 1})
        self.assertEqual(result.summary["fallback_counts"], {"pdf_raster_ocr": 1})
        self.assertIn("Raster OCR recovered", chunks[0]["text"])
        self.assertEqual(manifest[0]["parser_name"], "rapidocr_pdf_raster")
        self.assertEqual(manifest[0]["parser_metadata"]["fallback_from"], "pdf_raster_ocr")
        self.assertEqual(
            manifest[0]["parser_metadata"]["fallback_error_class"],
            "pdf_text_fallback_empty",
        )
        self.assertTrue(_check(validation, "fallback_records_are_auditable")["passed"])

    def test_pdf_raster_ocr_worker_count_caps_large_documents(self) -> None:
        with mock.patch.object(extract_module.multiprocessing, "cpu_count", return_value=8):
            self.assertEqual(extract_module._pdf_raster_ocr_worker_count(4), 1)
            self.assertEqual(
                extract_module._pdf_raster_ocr_worker_count(
                    extract_module.PDF_RASTER_OCR_PARALLEL_MIN_PAGES
                ),
                extract_module.PDF_RASTER_OCR_MAX_WORKERS,
            )

    def test_collect_pdf_raster_ocr_blocks_falls_back_to_sequential_when_pool_fails(self) -> None:
        image_paths = [Path("/tmp/page-2.png"), Path("/tmp/page-3.png")]
        broken_context = mock.Mock()
        broken_context.Pool.side_effect = RuntimeError("pool failed")

        with (
            mock.patch.object(extract_module, "_pdf_raster_ocr_worker_count", return_value=2),
            mock.patch.object(
                extract_module.multiprocessing,
                "get_context",
                return_value=broken_context,
            ),
            mock.patch.object(
                extract_module,
                "_ocr_pdf_raster_page",
                side_effect=[(2, "Recovered page two text."), (3, None)],
            ) as ocr_page,
        ):
            blocks = extract_module._collect_pdf_raster_ocr_blocks(image_paths)

        self.assertEqual([block.page for block in blocks], [2])
        self.assertEqual([block.text for block in blocks], ["Recovered page two text."])
        self.assertEqual(ocr_page.call_count, 2)

    def test_ocr_pdf_raster_page_uses_no_classifier_mode(self) -> None:
        fake_ocr = mock.Mock(return_value=SimpleNamespace(txts=["  Alpha  ", "", "Beta"]))

        with mock.patch.object(extract_module, "_rapidocr_torch", return_value=fake_ocr) as rapidocr:
            page_number, text = extract_module._ocr_pdf_raster_page("/tmp/page-7.png")

        rapidocr.assert_called_once_with(use_cls=False)
        fake_ocr.assert_called_once_with("/tmp/page-7.png")
        self.assertEqual(page_number, 7)
        self.assertEqual(text, "Alpha\nBeta")

    def test_ocr_pdf_raster_page_propagates_ocr_setup_errors(self) -> None:
        with mock.patch.object(
            extract_module,
            "_rapidocr_torch",
            side_effect=RuntimeError("rapidocr unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "rapidocr unavailable"):
                extract_module._ocr_pdf_raster_page("/tmp/page-7.png")

    def test_try_extract_pdf_raster_ocr_returns_none_when_parallel_ocr_errors(self) -> None:
        artifact = Path("/tmp/fake.pdf")
        fake_completed = SimpleNamespace(returncode=0)
        image_paths = [Path("/tmp/page-1.png")]

        with (
            mock.patch.object(extract_module.shutil, "which", return_value="/opt/homebrew/bin/pdftoppm"),
            mock.patch.object(extract_module.importlib.util, "find_spec", return_value=object()),
            mock.patch.object(extract_module.tempfile, "TemporaryDirectory") as tempdir,
            mock.patch.object(extract_module.subprocess, "run", return_value=fake_completed),
            mock.patch.object(extract_module.Path, "glob", return_value=image_paths),
            mock.patch.object(extract_module, "_apple_vision_ocr_available", return_value=False),
            mock.patch.object(
                extract_module,
                "_collect_pdf_raster_ocr_blocks",
                side_effect=RuntimeError("ocr worker failed"),
            ),
        ):
            tempdir.return_value.__enter__.return_value = "/tmp"
            tempdir.return_value.__exit__.return_value = None
            self.assertIsNone(
                extract_module._try_extract_pdf_raster_ocr(
                    artifact,
                    fallback_error_class="pdf_text_fallback_empty",
                    fallback_error_message="empty",
                )
            )

    def test_try_extract_pdf_raster_ocr_uses_apple_vision_when_rapidocr_stalls(self) -> None:
        artifact = Path("/tmp/fake.pdf")
        fake_completed = SimpleNamespace(returncode=0)
        image_paths = [Path("/tmp/page-2.png"), Path("/tmp/page-3.png")]

        with (
            mock.patch.object(extract_module.shutil, "which", return_value="/opt/homebrew/bin/pdftoppm"),
            mock.patch.object(
                extract_module.importlib.util,
                "find_spec",
                side_effect=lambda name: object() if name == "rapidocr" else None,
            ),
            mock.patch.object(extract_module.tempfile, "TemporaryDirectory") as tempdir,
            mock.patch.object(extract_module.subprocess, "run", return_value=fake_completed),
            mock.patch.object(extract_module.Path, "glob", return_value=image_paths),
            mock.patch.object(
                extract_module,
                "_collect_pdf_raster_ocr_blocks",
                side_effect=RuntimeError("rapidocr pool stalled"),
            ),
            mock.patch.object(extract_module, "_apple_vision_ocr_available", return_value=True),
            mock.patch.object(
                extract_module,
                "_collect_pdf_raster_apple_vision_blocks",
                return_value=[
                    extract_module.TextBlock(text="Recovered page two text.", page=2),
                    extract_module.TextBlock(text="Recovered page three text.", page=3),
                ],
            ),
        ):
            tempdir.return_value.__enter__.return_value = "/tmp"
            tempdir.return_value.__exit__.return_value = None
            payload = extract_module._try_extract_pdf_raster_ocr(
                artifact,
                fallback_error_class="pdf_text_fallback_empty",
                fallback_error_message="empty",
            )

        assert payload is not None
        self.assertEqual(payload.parser_name, "apple_vision_pdf_raster")
        self.assertEqual(payload.parser_version, "vision_swift")
        self.assertEqual(payload.metadata["fallback_from"], "pdf_raster_ocr")
        self.assertEqual(payload.metadata["pdf_raster_ocr_backend"], "apple_vision_swift")
        self.assertEqual(payload.metadata["pdf_raster_ocr_page_count"], 2)
        self.assertIn("Recovered page two text.", payload.text)

    def test_try_extract_pdf_raster_ocr_prefers_apple_vision_for_large_documents(self) -> None:
        artifact = Path("/tmp/fake.pdf")
        fake_completed = SimpleNamespace(returncode=0)
        image_paths = [
            Path(f"/tmp/page-{index}.png")
            for index in range(1, extract_module.PDF_RASTER_OCR_PARALLEL_MIN_PAGES + 1)
        ]

        with (
            mock.patch.object(extract_module.shutil, "which", return_value="/opt/homebrew/bin/pdftoppm"),
            mock.patch.object(
                extract_module.importlib.util,
                "find_spec",
                side_effect=lambda name: object() if name == "rapidocr" else None,
            ),
            mock.patch.object(extract_module.tempfile, "TemporaryDirectory") as tempdir,
            mock.patch.object(extract_module.subprocess, "run", return_value=fake_completed),
            mock.patch.object(extract_module.Path, "glob", return_value=image_paths),
            mock.patch.object(extract_module, "_apple_vision_ocr_available", return_value=True),
            mock.patch.object(
                extract_module,
                "_collect_pdf_raster_apple_vision_blocks",
                return_value=[extract_module.TextBlock(text="Recovered first page.", page=1)],
            ),
            mock.patch.object(extract_module, "_collect_pdf_raster_ocr_blocks") as rapidocr_blocks,
        ):
            tempdir.return_value.__enter__.return_value = "/tmp"
            tempdir.return_value.__exit__.return_value = None
            payload = extract_module._try_extract_pdf_raster_ocr(
                artifact,
                fallback_error_class="pdf_text_fallback_empty",
                fallback_error_message="empty",
            )

        assert payload is not None
        self.assertEqual(payload.parser_name, "apple_vision_pdf_raster")
        rapidocr_blocks.assert_not_called()

    def test_collect_pdf_raster_apple_vision_blocks_parses_json_output(self) -> None:
        completed = SimpleNamespace(
            returncode=0,
            stdout='{"page":10,"text":"  Ten  "}\n{"page":2,"text":"Two"}\n{"page":7,"text":"   "}\n',
            stderr="",
        )

        with mock.patch.object(extract_module.subprocess, "run", return_value=completed):
            blocks = extract_module._collect_pdf_raster_apple_vision_blocks(
                [Path("/tmp/page-10.png"), Path("/tmp/page-2.png"), Path("/tmp/page-7.png")]
            )

        self.assertEqual([block.page for block in blocks], [2, 10])
        self.assertEqual([block.text for block in blocks], ["Two", "Ten"])
