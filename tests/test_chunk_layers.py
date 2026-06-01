from __future__ import annotations

from pathlib import Path
import json
import tempfile

import pytest

from usfs_r1_ea_sources.chunk_layers import build_chunk_layers
from usfs_r1_ea_sources.chunk_quality_audit import run_chunk_quality_audit

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_source_set_manifest
from tests.support.retrieval_fixtures import _write_chunks


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_chunk_layer_build_writes_atomic_structural_and_parent_sidecars() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        _write_chunks(
            output_dir,
            source_set_id,
            [
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="R1PLAN-001",
                    title="Forest Plan",
                    document_role="forest_plan",
                    authority_level="forest_plan",
                    citation_label="R1PLAN-001 (abc123)",
                    text=(
                        "Standard FW-STD-01 Vegetation treatments shall retain snags.\n\n"
                        "Table 1   Resource   Requirement\n"
                        "Row 1     Wildlife   Retain habitat structure."
                    ),
                ),
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="R1PLAN-001",
                    title="Forest Plan",
                    document_role="forest_plan",
                    authority_level="forest_plan",
                    citation_label="R1PLAN-001 (abc123)",
                    text="Desired condition DC-01 Watersheds are resilient.",
                )
                | {
                    "chunk_id": "chunk:R1PLAN-001:2",
                    "chunk_index": 1,
                    "char_start": 180,
                    "char_end": 228,
                },
            ],
        )

        result = build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)

        assert result.summary["validation_passed"] is True
        assert result.summary["baseline_chunk_count"] == 2
        assert result.summary["atomic_chunk_count"] >= 3
        assert result.summary["structural_chunk_count"] >= 3
        assert result.summary["parent_context_window_count"] == 1
        assert result.atomic_chunks_path.exists()
        assert result.structural_chunks_path.exists()
        assert result.parent_windows_path.exists()
        assert result.summary_path.exists()

        atomic = _read_jsonl(result.atomic_chunks_path)
        structural = _read_jsonl(result.structural_chunks_path)
        windows = _read_jsonl(result.parent_windows_path)
        window_ids = {window["window_id"] for window in windows}
        assert all(chunk["citation_label"] == "R1PLAN-001 (abc123)" for chunk in atomic)
        assert all(chunk["parent_window_id"] in window_ids for chunk in atomic)
        assert all(chunk["contextual_index_text"] for chunk in atomic)
        assert all(chunk["contextual_index_sha256"] for chunk in atomic)
        assert {chunk["structure_type"] for chunk in structural} >= {
            "forest_plan_standard",
            "table_row",
            "desired_condition",
        }


def test_chunk_layer_build_resolves_source_set_from_catalog_manifest_and_updates_audit() -> None:
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

        result = build_chunk_layers(output_dir=output_dir)
        audit = run_chunk_quality_audit(output_dir=output_dir, source_set_id=source_set_id)

        assert result.source_set_id == source_set_id
        assert result.summary["validation_passed"] is True
        assert audit.summary["sidecar"]["present"] is True
        assert audit.summary["sidecar"]["validation_passed"] is True
        assert "parent_context_missing" not in audit.summary["sources"][0]["risk_buckets"]


def test_chunk_layer_build_rejects_canonical_derived_artifact_dirs() -> None:
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
        derived_dir = output_dir / "derived" / source_set_id

        with pytest.raises(ValueError, match="canonical derived artifact directory"):
            build_chunk_layers(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_v2_dir=derived_dir / "chunks",
            )


def test_chunk_layer_build_rejects_non_positive_token_limits() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"

        with pytest.raises(ValueError, match="atomic_max_tokens must be positive"):
            build_chunk_layers(
                output_dir=output_dir,
                source_set_id=source_set_id,
                atomic_max_tokens=0,
            )
