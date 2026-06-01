from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.chunk_quality_audit import run_chunk_quality_audit

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_source_set_manifest
from tests.support.retrieval_fixtures import _write_chunks


def test_chunk_quality_audit_reports_parser_boundary_and_structure_risk() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        risky = _chunk(
            source_set_id=source_set_id,
            source_record_id="PDF-001",
            title="Table Heavy Forest Plan",
            document_role="forest_plan",
            authority_level="forest_plan",
            citation_label="PDF-001 (abc123)",
            text="continued from previous page\n\nTable 2   Standard   Applicability",
        )
        risky.update(
            {
                "artifact_path": "artifacts/raw/PDF-001.pdf",
                "parser_name": "pypdf_text_fallback",
                "page": 1,
                "heading": None,
            }
        )
        _write_chunks(output_dir, source_set_id, [risky])

        result = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        assert result.summary["passed"] is True
        assert result.summary["chunk_count"] == 1
        assert result.summary["risk_source_count"] == 1
        buckets = result.summary["sources"][0]["risk_buckets"]
        assert "fallback_parser_dominated" in buckets
        assert "heading_context_missing" in buckets
        assert "table_row_unstructured" in buckets
        assert "parent_context_missing" in buckets


def test_chunk_quality_audit_reads_existing_sidecar_parent_context_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        _write_chunks(
            output_dir,
            source_set_id,
            [
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="DOC-001",
                    title="NEPA Section",
                    document_role="law",
                    authority_level="federal",
                    citation_label="DOC-001 (abc123)",
                    text="42 U.S.C. 4332 requires environmental effects analysis.",
                )
            ],
        )
        sidecar_summary = output_dir / "derived" / source_set_id / "chunks_v2" / "summary.json"
        sidecar_summary.parent.mkdir(parents=True, exist_ok=True)
        sidecar_summary.write_text(
            json.dumps(
                {
                    "schema_version": "chunk-layers-v1",
                    "validation_passed": True,
                    "atomic_chunk_count": 1,
                    "structural_chunk_count": 1,
                    "parent_context_window_count": 1,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        result = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        assert result.summary["sidecar"]["present"] is True
        assert result.summary["sidecar"]["validation_passed"] is True
        assert "parent_context_missing" not in result.summary["sources"][0]["risk_buckets"]


def test_chunk_quality_audit_resolves_source_set_from_catalog_manifest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        _write_catalog_source_set_manifest(output_dir, source_set_id)
        _write_chunks(
            output_dir,
            source_set_id,
            [
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="DOC-001",
                    title="NEPA Section",
                    document_role="law",
                    authority_level="federal",
                    citation_label="DOC-001 (abc123)",
                    text="42 U.S.C. 4332 requires environmental effects analysis.",
                )
            ],
        )

        result = run_chunk_quality_audit(output_dir=output_dir)

        assert result.source_set_id == source_set_id
        assert result.output_path == (
            output_dir / "derived" / source_set_id / "diagnostics" / "chunk_quality_audit.json"
        ).resolve()


def test_chunk_quality_audit_writes_failed_report_when_chunks_are_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"

        result = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        checks = {check["name"]: check for check in result.summary["checks"]}
        assert result.summary["passed"] is False
        assert checks["chunks_jsonl_exists"]["passed"] is False
        assert checks["chunks_loaded"]["passed"] is False
        assert result.output_path.exists()


def test_chunk_quality_audit_reports_invalid_offsets_without_crashing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        chunk = _chunk(
            source_set_id=source_set_id,
            source_record_id="DOC-001",
            title="NEPA Section",
            document_role="law",
            authority_level="federal",
            citation_label="DOC-001 (abc123)",
            text="42 U.S.C. 4332 requires environmental effects analysis.",
        )
        chunk["char_end"] = chunk["char_start"]
        _write_chunks(output_dir, source_set_id, [chunk])

        result = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        checks = {check["name"]: check for check in result.summary["checks"]}
        assert result.summary["passed"] is False
        assert checks["chunk_offsets_valid"]["passed"] is False
        assert checks["chunk_offsets_valid"]["details"]["bad_offset_chunk_ids"] == [
            chunk["chunk_id"]
        ]


def test_chunk_quality_audit_reads_each_source_text_path_once(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        first = _chunk(
            source_set_id=source_set_id,
            source_record_id="DOC-001",
            title="NEPA Section",
            document_role="law",
            authority_level="federal",
            citation_label="DOC-001 (abc123)",
            text="42 U.S.C. 4332 requires environmental effects analysis.",
        )
        second = dict(first)
        second.update(
            {
                "chunk_id": "chunk:DOC-001:1",
                "chunk_index": 1,
                "char_start": first["char_end"],
                "char_end": first["char_end"] + 20,
                "text": "Additional text span.",
            }
        )
        _write_chunks(output_dir, source_set_id, [first, second])
        source_text_path = output_dir / first["source_text_path"]
        original_read_text = Path.read_text
        source_text_read_count = 0

        def counting_read_text(path: Path, *args, **kwargs):
            nonlocal source_text_read_count
            if path == source_text_path:
                source_text_read_count += 1
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", counting_read_text)

        result = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        assert source_text_read_count == 1
        assert result.summary["sources"][0]["text_char_count"] == len(
            source_text_path.read_text(encoding="utf-8")
        )
