from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.catalog import build_review_catalog
import usfs_r1_ea_sources.extract as extract_module
from usfs_r1_ea_sources.extract import build_extraction

from tests.support.extract_fixtures import CONFIG
from tests.support.extract_fixtures import WORKBOOK
from tests.support.extract_fixtures import _check
from tests.support.extract_fixtures import _html_body
from tests.support.extract_fixtures import _read_jsonl
from tests.support.extract_fixtures import _write_download_run
from tests.support.extract_fixtures import legacy_config


class ExtractionReuseTests(unittest.TestCase):
    def test_build_extraction_reuses_existing_payload_when_requested(self) -> None:
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
        config = legacy_config()
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

    def test_build_extraction_accepts_reuse_inventory_bundle_path(self) -> None:
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
