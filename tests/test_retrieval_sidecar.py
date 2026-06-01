from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.chunk_layers import build_chunk_layers
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.retrieval import query_retrieval_index

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_sqlite
from tests.support.retrieval_fixtures import _write_chunks
from tests.support.retrieval_fixtures import _write_extraction_diagnostics


class RetrievalSidecarTests(unittest.TestCase):
    def test_retrieval_query_uses_contextual_fts_over_sidecar_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_forest_plan_chunk(output_dir, source_set_id)
            layers = build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)
            result = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=layers.atomic_chunks_path,
            )

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="watersheds resilient desired condition",
            )

            self.assertEqual(query["retrieval_mode"], "fts_first_stage")
            self.assertGreater(query["fts_candidate_count"], 0)
            hit = query["results"][0]
            self.assertEqual(hit["source_record_id"], "R1PLAN-001")
            self.assertEqual(hit["chunk_layer"], "atomic_text_chunk_v2")
            self.assertEqual(hit["structure_type"], "desired_condition")
            self.assertTrue(hit["parent_window_id"])
            self.assertNotIn("source_record_id:", hit["evidence_span"]["text"])

    def test_build_retrieval_index_can_use_noncanonical_index_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_forest_plan_chunk(output_dir, source_set_id)
            index_dir = output_dir / "alt-indexes" / "retrieval_sidecar"

            result = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                index_dir=index_dir,
            )
            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="watersheds resilient",
            )

            self.assertEqual(result.index_dir, index_dir)
            self.assertEqual(result.sqlite_path, index_dir / "evidence_index.sqlite")
            self.assertEqual(query["hit_count"], 1)
            canonical_index = output_dir / "derived" / source_set_id / "retrieval" / "evidence_index.sqlite"
            self.assertFalse(canonical_index.exists())

    def test_retrieval_index_can_query_sidecar_chunk_fields_from_noncanonical_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_forest_plan_chunk(output_dir, source_set_id)
            layers = build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)
            sidecar_index_dir = output_dir / "derived" / source_set_id / "retrieval_sidecar"

            result = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=layers.atomic_chunks_path,
                index_dir=sidecar_index_dir,
            )
            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="watersheds resilient desired condition",
            )

            self.assertEqual(result.index_dir, sidecar_index_dir)
            self.assertEqual(query["hit_count"], 1)
            hit = query["results"][0]
            self.assertEqual(hit["source_record_id"], "R1PLAN-001")
            self.assertEqual(hit["chunk_layer"], "atomic_text_chunk_v2")
            self.assertEqual(hit["structure_type"], "desired_condition")
            self.assertTrue(hit["parent_window_id"])
            self.assertEqual(hit["provenance"]["chunk_layer"], "atomic_text_chunk_v2")
            self.assertNotIn("source_record_id:", hit["evidence_span"]["text"])


def _write_forest_plan_chunk(output_dir: Path, source_set_id: str) -> None:
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=["R1PLAN-001"],
    )
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
                citation_label="R1PLAN-001 | Forest Plan | artifact abc123",
                text="Desired condition DC-01 Watersheds are resilient.",
            )
        ],
    )
    _write_catalog_sqlite(output_dir, {"R1PLAN-001": ["Forest plan direction"]})
