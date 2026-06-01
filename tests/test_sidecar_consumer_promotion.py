from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.sidecar_consumer_eval import run_chunk_sidecar_consumer_eval
from usfs_r1_ea_sources.sidecar_consumer_promotion import (
    run_chunk_sidecar_consumer_promotion,
)

from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics


class ChunkSidecarConsumerPromotionTests(unittest.TestCase):
    def test_promote_parser_accepts_apply_options(self) -> None:
        args = build_parser().parse_args(
            [
                "chunk-sidecar-consumer-promote",
                "--output-dir",
                "source_library",
                "--source-set-id",
                "source-set-test",
                "--consumer-eval-results-path",
                "consumer_sidecar_eval/chunk_sidecar_consumer_eval_results.json",
                "--results-dir",
                "consumer_sidecar_promotion",
                "--apply",
                "--replace-canonical",
            ]
        )

        self.assertEqual(args.command, "chunk-sidecar-consumer-promote")
        self.assertEqual(
            args.consumer_eval_results_path,
            Path("consumer_sidecar_eval/chunk_sidecar_consumer_eval_results.json"),
        )
        self.assertEqual(args.results_dir, Path("consumer_sidecar_promotion"))
        self.assertTrue(args.apply)
        self.assertTrue(args.replace_canonical)

    def test_promotion_dry_run_and_apply_rebuild_canonical_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            consumer_eval = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )

            dry_run = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertTrue(dry_run.summary["passed"])
            self.assertTrue(dry_run.summary["promotion_ready"])
            self.assertFalse(dry_run.summary["applied"])
            self.assertEqual(
                Path(
                    json.loads(baseline_graph.summary_path.read_text(encoding="utf-8"))[
                        "chunks_path"
                    ]
                ).resolve(),
                (output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl").resolve(),
            )

            applied = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=consumer_eval.output_path,
                apply=True,
                replace_canonical=True,
            )

            self.assertTrue(applied.summary["passed"])
            self.assertTrue(applied.summary["applied"])
            canonical_graph = json.loads(
                baseline_graph.summary_path.read_text(encoding="utf-8")
            )
            canonical_claims = json.loads(
                baseline_claims.summary_path.read_text(encoding="utf-8")
            )
            self.assertEqual(canonical_graph["validation_passed"], True)
            self.assertEqual(canonical_claims["validation_passed"], True)
            self.assertEqual(canonical_graph["reviewer_ready"], True)
            self.assertEqual(canonical_claims["reviewer_ready"], True)
            self.assertTrue(canonical_graph["chunks_path"].endswith("chunks_v2/atomic_chunks.jsonl"))
            self.assertTrue(canonical_claims["chunks_path"].endswith("chunks_v2/atomic_chunks.jsonl"))
            self.assertIn("retrieval_sidecar", canonical_graph["retrieval_summary_path"])
            self.assertIn("retrieval_sidecar", canonical_claims["retrieval_summary_path"])

    def test_promotion_requires_replace_for_existing_canonical_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            consumer_eval = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )

            result = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=consumer_eval.output_path,
                apply=True,
            )

            self.assertFalse(result.summary["passed"])
            self.assertFalse(_check(result.summary, "canonical_targets_are_replaceable")["passed"])
            self.assertFalse(result.summary["applied"])

    def test_promotion_writes_failed_result_for_missing_consumer_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            missing_eval_path = output_dir / "missing-consumer-eval.json"

            result = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=missing_eval_path,
            )

            self.assertTrue(result.output_path.exists())
            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["promotion_ready"])
            self.assertFalse(_check(result.summary, "consumer_eval_results_present")["passed"])
            self.assertFalse(_check(result.summary, "consumer_eval_results_readable")["passed"])
            self.assertFalse(_check(result.summary, "sidecar_required_paths_declared")["passed"])
            self.assertIsNone(result.summary["sidecar"]["atomic_chunks_path"])

    def test_promotion_fails_closed_on_partial_consumer_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            consumer_eval = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )
            payload = json.loads(consumer_eval.output_path.read_text(encoding="utf-8"))
            payload["allow_partial_retrieval"] = True
            consumer_eval.output_path.write_text(
                json.dumps(payload, sort_keys=True),
                encoding="utf-8",
            )

            result = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=consumer_eval.output_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertFalse(_check(result.summary, "consumer_eval_non_partial")["passed"])

    def test_promotion_fails_closed_on_missing_sidecar_path_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            consumer_eval = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )
            payload = json.loads(consumer_eval.output_path.read_text(encoding="utf-8"))
            payload.pop("sidecar_graph_dir")
            consumer_eval.output_path.write_text(
                json.dumps(payload, sort_keys=True),
                encoding="utf-8",
            )

            result = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=consumer_eval.output_path,
            )

            path_check = _check(result.summary, "sidecar_required_paths_declared")
            self.assertFalse(result.summary["passed"])
            self.assertFalse(path_check["passed"])
            self.assertFalse(path_check["details"]["graph_dir"]["declared"])
            self.assertFalse(_check(result.summary, "sidecar_input_paths_exist")["passed"])

    def test_promotion_fails_closed_on_sidecar_path_kind_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            consumer_eval = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )
            payload = json.loads(consumer_eval.output_path.read_text(encoding="utf-8"))
            payload["sidecar_graph_dir"] = payload["sidecar_graph_summary_path"]
            consumer_eval.output_path.write_text(
                json.dumps(payload, sort_keys=True),
                encoding="utf-8",
            )

            result = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=consumer_eval.output_path,
            )

            kind_check = _check(result.summary, "sidecar_input_path_kinds_valid")
            self.assertFalse(result.summary["passed"])
            self.assertFalse(kind_check["passed"])
            self.assertFalse(kind_check["details"]["graph_dir"]["kind_valid"])

    def test_promotion_fails_closed_on_canonical_sidecar_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            baseline_graph, baseline_claims = _prepare_baseline_consumers(
                output_dir,
                source_set_id,
            )
            consumer_eval = run_chunk_sidecar_consumer_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                baseline_graph_summary_path=baseline_graph.summary_path,
                baseline_claim_summary_path=baseline_claims.summary_path,
            )
            payload = json.loads(consumer_eval.output_path.read_text(encoding="utf-8"))
            payload["sidecar_graph_dir"] = str(
                output_dir / "derived" / source_set_id / "evidence_graph"
            )
            consumer_eval.output_path.write_text(
                json.dumps(payload, sort_keys=True),
                encoding="utf-8",
            )

            result = run_chunk_sidecar_consumer_promotion(
                output_dir=output_dir,
                source_set_id=source_set_id,
                consumer_eval_results_path=consumer_eval.output_path,
            )

            noncanonical_check = _check(result.summary, "sidecar_inputs_are_noncanonical")
            self.assertFalse(result.summary["passed"])
            self.assertFalse(noncanonical_check["passed"])
            self.assertIn("sidecar_graph_dir", noncanonical_check["details"]["errors"])


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
