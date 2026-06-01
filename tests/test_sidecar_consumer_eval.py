from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.sidecar_consumer_eval import run_chunk_sidecar_consumer_eval

from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics


class ChunkSidecarConsumerEvalTests(unittest.TestCase):
    def test_consumer_eval_builds_sidecar_graph_and_claims_without_canonical_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-014"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-014",
                        title="FONSI availability",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-014 | FONSI availability | artifact def456",
                        text="USDA shall make the FONSI available to the public.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-014": ["FONSI availability"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            baseline_graph = build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )
            baseline_claims = build_claim_extraction(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )
            baseline_graph_summary = baseline_graph.summary_path.read_text(encoding="utf-8")
            baseline_claim_summary = baseline_claims.summary_path.read_text(encoding="utf-8")

            result = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["sidecar"]["graph"]["validation_passed"], True)
            self.assertEqual(result.summary["sidecar"]["claims"]["validation_passed"], True)
            self.assertEqual(
                Path(result.summary["sidecar_graph_dir"]).resolve(),
                (
                    output_dir
                    / "derived"
                    / source_set_id
                    / "consumer_sidecar_eval"
                    / "evidence_graph_sidecar"
                ).resolve(),
            )
            self.assertEqual(
                Path(result.summary["sidecar_claims_dir"]).resolve(),
                (
                    output_dir
                    / "derived"
                    / source_set_id
                    / "consumer_sidecar_eval"
                    / "claims_sidecar"
                ).resolve(),
            )
            self.assertTrue(result.output_path.exists())
            self.assertEqual(
                baseline_graph.summary_path.read_text(encoding="utf-8"),
                baseline_graph_summary,
            )
            self.assertEqual(
                baseline_claims.summary_path.read_text(encoding="utf-8"),
                baseline_claim_summary,
            )

    def test_consumer_eval_rejects_canonical_output_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            derived_dir = output_dir / "derived" / source_set_id

            with self.assertRaisesRegex(ValueError, "chunks_v2_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    chunks_v2_dir=derived_dir / "chunks",
                )
            with self.assertRaisesRegex(ValueError, "sidecar_index_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    sidecar_index_dir=derived_dir / "retrieval",
                )
            with self.assertRaisesRegex(ValueError, "graph_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    graph_dir=derived_dir / "evidence_graph",
                )
            with self.assertRaisesRegex(ValueError, "claims_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    claims_dir=derived_dir / "claims",
                )
            with self.assertRaisesRegex(ValueError, "results_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    results_dir=derived_dir / "claims" / "sidecar_eval",
                )


if __name__ == "__main__":
    unittest.main()
