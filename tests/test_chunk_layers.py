from __future__ import annotations

import json
from pathlib import Path
import tempfile

from usfs_r1_ea_sources.chunk_layers import build_chunk_layers

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_chunks


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


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
        assert result.summary["atomic_chunk_count"] >= 2
        assert result.summary["structural_chunk_count"] >= 2
        assert result.atomic_chunks_path.exists()
        assert result.structural_chunks_path.exists()
        assert result.parent_windows_path.exists()

        atomic = _read_jsonl(result.atomic_chunks_path)
        structural = _read_jsonl(result.structural_chunks_path)
        assert all(chunk["citation_label"] == "R1PLAN-001 (abc123)" for chunk in atomic)
        assert all(chunk["parent_window_id"] for chunk in atomic)
        assert all(chunk["contextual_index_text"] for chunk in atomic)
        assert {
            chunk["structure_type"]
            for chunk in structural
        } & {"forest_plan_standard", "table_row", "desired_condition"}
