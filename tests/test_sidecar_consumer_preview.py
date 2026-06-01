from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.chunk_layers import build_chunk_layers
from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_sqlite
from tests.support.retrieval_fixtures import _write_chunks
from tests.support.retrieval_fixtures import _write_extraction_diagnostics


class SidecarConsumerPreviewTests(unittest.TestCase):
    def test_claim_extraction_can_build_sidecar_preview_without_canonical_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-003",
                title="Level of review",
                document_role="law",
                authority_level="federal",
                citation_label="R1EA-003 | Level of review | artifact abc123",
                text="An agency shall prepare an environmental assessment.",
            )
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
            )
            _write_chunks(output_dir, source_set_id, [chunk])
            _write_catalog_sqlite(output_dir, {"R1EA-003": ["Level of review"]})
            layers = build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)
            sidecar_index = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=layers.atomic_chunks_path,
                index_dir=output_dir / "sidecar" / "retrieval",
            )
            claims_dir = output_dir / "sidecar" / "claims"

            result = build_claim_extraction(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=layers.atomic_chunks_path,
                retrieval_validation_path=sidecar_index.validation_path,
                retrieval_summary_path=sidecar_index.summary_path,
                claims_dir=claims_dir,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.claims_dir, claims_dir)
            self.assertEqual(result.summary["chunks_path"], str(layers.atomic_chunks_path))
            self.assertEqual(
                result.summary["retrieval_validation_path"],
                str(sidecar_index.validation_path),
            )
            self.assertEqual(
                result.summary["retrieval_summary_path"],
                str(sidecar_index.summary_path),
            )
            self.assertFalse(
                (output_dir / "derived" / source_set_id / "claims" / "claims.jsonl").exists()
            )


if __name__ == "__main__":
    unittest.main()
