from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.chunk_layers import build_chunk_layers
from usfs_r1_ea_sources.chunk_quality_audit import run_chunk_quality_audit

from tests.support.retrieval_fixtures import _chunk
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


def test_chunk_quality_audit_reads_sidecar_parent_context_status() -> None:
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
        build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)

        result = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        assert result.summary["sidecar"]["present"] is True
        assert result.summary["sidecar"]["validation_passed"] is True
        assert "parent_context_missing" not in result.summary["sources"][0]["risk_buckets"]
