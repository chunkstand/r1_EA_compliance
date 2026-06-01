from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.sidecar_consumer_eval import run_chunk_sidecar_consumer_eval

from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics


class ChunkSidecarConsumerEvalTests(unittest.TestCase):
    def test_sidecar_consumer_eval_scores_graph_and_claim_previews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )

            result = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["sidecar"]["graph"]["validation_passed"], True)
            self.assertEqual(result.summary["sidecar"]["claims"]["validation_passed"], True)
            self.assertEqual(result.summary["baseline"]["graph"]["validation_passed"], True)
            self.assertEqual(result.summary["baseline"]["claims"]["validation_passed"], True)
            self.assertTrue(result.output_path.exists())
            self.assertNotEqual(
                Path(result.summary["sidecar_graph_dir"]).resolve(),
                (output_dir / "derived" / source_set_id / "evidence_graph").resolve(),
            )
            self.assertNotEqual(
                Path(result.summary["sidecar_claims_dir"]).resolve(),
                (output_dir / "derived" / source_set_id / "claims").resolve(),
            )

    def test_sidecar_consumer_eval_fails_closed_on_invalid_baseline_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            graph_summary = json.loads(baseline_graph.summary_path.read_text(encoding="utf-8"))
            graph_summary["validation_passed"] = False
            baseline_graph.summary_path.write_text(
                json.dumps(graph_summary, sort_keys=True),
                encoding="utf-8",
            )

            result = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertFalse(_check(result.summary, "baseline_graph_summary_valid")["passed"])

    def test_sidecar_consumer_eval_rejects_canonical_preview_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_baseline_consumers(output_dir, source_set_id)

            with self.assertRaisesRegex(ValueError, "graph_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    graph_dir=output_dir / "derived" / source_set_id / "evidence_graph",
                )

    def test_sidecar_consumer_eval_rejects_canonical_chunk_index_and_result_dirs(self) -> None:
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
            with self.assertRaisesRegex(ValueError, "results_dir must not point"):
                run_chunk_sidecar_consumer_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    results_dir=derived_dir / "claims" / "consumer_eval",
                )


def _prepare_baseline_consumers(output_dir: Path, source_set_id: str):
    write_catalog_validation(output_dir, passed=True)
    write_catalog_source_set_manifest(output_dir, source_set_id)
    write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=["R1PLAN-001"],
    )
    write_chunks(
        output_dir,
        source_set_id,
        [
            chunk(
                source_set_id=source_set_id,
                source_record_id="R1PLAN-001",
                title="Forest Plan",
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label="R1PLAN-001 | Forest Plan | artifact abc123",
                text=(
                    "Desired condition DC-01 Watersheds are resilient. "
                    "The responsible official shall protect water quality under 42 U.S.C. 4336."
                ),
            )
        ],
    )
    write_catalog_sqlite(output_dir, {"R1PLAN-001": ["Forest plan direction"]})
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    baseline_graph = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)
    baseline_claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    return baseline_graph, baseline_claims


def _check(summary: dict, name: str) -> dict:
    for check in summary["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing check {name}")


if __name__ == "__main__":
    unittest.main()
