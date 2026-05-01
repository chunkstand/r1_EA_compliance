from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.reuse_inventory import build_reuse_inventory


class ReuseInventoryTests(unittest.TestCase):
    def test_inventory_classifies_current_reuse_missing_and_excluded_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            _write_catalog(
                output_dir,
                [
                    _catalog_row(
                        output_dir,
                        source_record_id="R1PLAN-custer-gallatin-nf-02",
                        body=b"current custer plan",
                        expected_parser="pdf",
                        content_type="application/pdf",
                        document_role="forest_plan",
                    ),
                    _catalog_row(
                        output_dir,
                        source_record_id="R1EA-001",
                        body=b"law one",
                    ),
                    _catalog_row(
                        output_dir,
                        source_record_id="R1EA-002",
                        body=b"law two",
                    ),
                    {
                        "source_set_id": "source-set-current",
                        "source_record_id": "R1EA-160",
                        "title": "Excluded project page",
                        "source_status": "skipped_excluded",
                        "artifact_path": None,
                        "artifact_sha256": None,
                        "artifact_byte_size": None,
                        "expected_parser": "html",
                        "content_type": None,
                        "document_role": "project_reference",
                    },
                ],
            )
            _write_extraction_manifest(
                output_dir,
                source_set_id="source-set-current",
                records=[
                    _extraction_record(
                        output_dir,
                        source_set_id="source-set-current",
                        source_record_id="R1PLAN-custer-gallatin-nf-02",
                        artifact_body=b"current custer plan",
                        text="current custer plan text",
                        expected_parser="pdf",
                        content_type="application/pdf",
                    )
                ],
            )
            _write_extraction_manifest(
                output_dir,
                source_set_id="source-set-prior",
                records=[
                    _extraction_record(
                        output_dir,
                        source_set_id="source-set-prior",
                        source_record_id="R1EA-001",
                        artifact_body=b"law one",
                        text="prior law one text",
                    )
                ],
            )

            result = build_reuse_inventory(
                output_dir=output_dir,
                previous_source_set_ids=["source-set-prior"],
            )

            self.assertEqual(
                result.summary["classification_counts"],
                {
                    "already_current_cg_slice": 1,
                    "excluded": 1,
                    "needs_extract": 1,
                    "reuse_extraction": 1,
                },
            )
            records = {
                record["source_record_id"]: record
                for record in _read_jsonl(result.records_path)
            }
            self.assertEqual(
                records["R1PLAN-custer-gallatin-nf-02"]["classification"],
                "already_current_cg_slice",
            )
            self.assertEqual(records["R1EA-001"]["classification"], "reuse_extraction")
            self.assertEqual(
                records["R1EA-001"]["reuse_candidate"]["source_set_id"],
                "source-set-prior",
            )
            self.assertEqual(records["R1EA-002"]["classification"], "needs_extract")
            self.assertEqual(records["R1EA-160"]["classification"], "excluded")
            self.assertTrue(result.inventory_path.exists())
            self.assertTrue(result.summary_path.exists())

    def test_inventory_rejects_reuse_when_prior_text_hash_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            _write_catalog(
                output_dir,
                [_catalog_row(output_dir, source_record_id="R1EA-001", body=b"law one")],
            )
            record = _extraction_record(
                output_dir,
                source_set_id="source-set-prior",
                source_record_id="R1EA-001",
                artifact_body=b"law one",
                text="prior law one text",
            )
            record["text_sha256"] = "bad-sha"
            _write_extraction_manifest(
                output_dir,
                source_set_id="source-set-prior",
                records=[record],
            )

            result = build_reuse_inventory(
                output_dir=output_dir,
                previous_source_set_ids=["source-set-prior"],
            )

            records = _read_jsonl(result.records_path)
            self.assertEqual(records[0]["classification"], "needs_extract")
            self.assertEqual(records[0]["reason"], "no_valid_prior_extraction")
            self.assertEqual(
                records[0]["candidate_failures"][0]["failures"],
                ["text_sha256_mismatch"],
            )


def _write_catalog(output_dir: Path, rows: list[dict]) -> None:
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "source_set_manifest.json").write_text(
        json.dumps({"source_set_id": "source-set-current"}, sort_keys=True),
        encoding="utf-8",
    )
    _write_jsonl(catalog_dir / "source_catalog.jsonl", rows)


def _catalog_row(
    output_dir: Path,
    *,
    source_record_id: str,
    body: bytes,
    expected_parser: str = "html",
    content_type: str = "text/html",
    document_role: str = "law",
) -> dict:
    artifact_dir = output_dir / "artifacts" / "raw"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_sha256 = hashlib.sha256(body).hexdigest()
    artifact_path = artifact_dir / f"{source_record_id}_{artifact_sha256[:12]}.txt"
    artifact_path.write_bytes(body)
    return {
        "source_set_id": "source-set-current",
        "source_record_id": source_record_id,
        "title": source_record_id,
        "source_status": "downloaded",
        "scope": "Baseline",
        "artifact_path": str(artifact_path),
        "artifact_sha256": artifact_sha256,
        "artifact_byte_size": len(body),
        "expected_parser": expected_parser,
        "content_type": content_type,
        "document_role": document_role,
        "authority_level": "federal",
    }


def _write_extraction_manifest(
    output_dir: Path,
    *,
    source_set_id: str,
    records: list[dict],
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(diagnostics_dir / "extraction_manifest.jsonl", records)


def _extraction_record(
    output_dir: Path,
    *,
    source_set_id: str,
    source_record_id: str,
    artifact_body: bytes,
    text: str,
    expected_parser: str = "html",
    content_type: str = "text/html",
) -> dict:
    text_dir = output_dir / "derived" / source_set_id / "extracted_text"
    text_dir.mkdir(parents=True, exist_ok=True)
    artifact_sha256 = hashlib.sha256(artifact_body).hexdigest()
    text_path = text_dir / f"{source_record_id}_{artifact_sha256[:12]}.txt"
    text_path.write_text(text, encoding="utf-8")
    return {
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "status": "extracted",
        "artifact_sha256": artifact_sha256,
        "expected_parser": expected_parser,
        "content_type": content_type,
        "chunk_count": 1,
        "text_path": str(text_path),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "parser_name": "unit-parser",
        "parser_version": "1",
        "parser_metadata": {"unit": True},
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
