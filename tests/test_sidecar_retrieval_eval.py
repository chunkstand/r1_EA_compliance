from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.chunk_layers import build_chunk_layers
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.sidecar_retrieval_eval import run_chunk_sidecar_retrieval_eval

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_sqlite
from tests.support.retrieval_fixtures import _write_chunks
from tests.support.retrieval_fixtures import _write_extraction_diagnostics


class ChunkSidecarRetrievalEvalTests(unittest.TestCase):
    def test_sidecar_retrieval_eval_compares_atomic_index_against_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
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
            baseline = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            layers = build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)
            atomic_chunk = json.loads(layers.atomic_chunks_path.read_text().splitlines()[0])
            eval_file = output_dir / "sidecar-eval.json"
            eval_file.write_text(
                json.dumps(
                    {
                        "schema_version": "retrieval-eval-v1",
                        "eval_id": "test-sidecar-eval",
                        "coverage_requirements": {
                            "case_count": 1,
                            "hard_negative_case_count": 0,
                            "multi_source_case_count": 0,
                        },
                        "metric_thresholds": {
                            "atomic_chunk_recall_at_k": {"min": 1.0},
                            "structure_hit_rate": {"min": 1.0},
                            "parent_window_coverage_rate": {"min": 1.0},
                            "citation_correctness_rate": {"min": 1.0},
                        },
                        "cases": [
                            {
                                "id": "desired-condition",
                                "query": "watersheds resilient desired condition",
                                "expected_source_record_ids": ["R1PLAN-001"],
                                "expected_chunk_ids": [atomic_chunk["chunk_id"]],
                                "expected_structure_types": ["desired_condition"],
                                "expected_citation_labels": ["R1PLAN-001"],
                                "require_parent_window": True,
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_chunk_sidecar_retrieval_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                eval_file=eval_file,
                baseline_index_path=baseline.sqlite_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["sidecar"]["eval_passed"], True)
            self.assertEqual(result.summary["baseline"]["eval_passed"], False)
            self.assertEqual(
                Path(result.summary["sidecar_index_path"]).resolve(),
                (
                    output_dir
                    / "derived"
                    / source_set_id
                    / "retrieval_sidecar"
                    / "evidence_index.sqlite"
                ).resolve(),
            )
            self.assertTrue(
                result.output_path.with_name("sidecar")
                .joinpath("retrieval_eval_results.json")
                .exists()
            )
            self.assertTrue(
                result.output_path.with_name("baseline")
                .joinpath("retrieval_eval_results.json")
                .exists()
            )

    def test_sidecar_retrieval_eval_rejects_canonical_output_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            derived_dir = output_dir / "derived" / source_set_id

            with self.assertRaisesRegex(ValueError, "chunks_v2_dir must not point"):
                run_chunk_sidecar_retrieval_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    chunks_v2_dir=derived_dir / "chunks",
                )
            with self.assertRaisesRegex(ValueError, "sidecar_index_dir must not point"):
                run_chunk_sidecar_retrieval_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    sidecar_index_dir=derived_dir / "retrieval",
                )
            with self.assertRaisesRegex(ValueError, "results_dir must not point"):
                run_chunk_sidecar_retrieval_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    results_dir=derived_dir / "chunks" / "sidecar_eval",
                )
            with self.assertRaisesRegex(ValueError, "results_dir must not point"):
                run_chunk_sidecar_retrieval_eval(
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    results_dir=derived_dir / "retrieval" / "sidecar_eval",
                )


if __name__ == "__main__":
    unittest.main()
