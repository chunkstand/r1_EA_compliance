from __future__ import annotations

from pathlib import Path
import json
import shutil
import tempfile
import unittest

from usfs_r1_ea_sources.draft_generation import run_draft_generate
from usfs_r1_ea_sources.draft_generation_eval import run_draft_generation_eval
from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval
from usfs_r1_ea_sources.replay_context import ReplayContextMismatchError
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.draft_generation_fixtures import write_minimal_draft_generation_config
from tests.support.draft_generation_fixtures import write_minimal_draft_generation_review
from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import phase
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics
from tests.support.phase_eval_fixtures import write_replay_context


class PhaseEvalReviewTests(unittest.TestCase):
    def test_review_phase_eval_auto_resolves_tracked_replay_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            output_dir = repo_root / "source_library"
            source_set_id = "source-set-test"
            review_id = "tracked-replay-review"
            archived_catalog_dir = output_dir / "runs" / "archived_catalog"
            write_catalog_validation(output_dir, passed=False)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-022"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-022",
                        title="Tracked replay source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-022 | Tracked replay source | artifact abc123",
                        text="Tracked replay context should resolve archived catalog state.",
                    )
                ],
            )
            active_sqlite = write_catalog_sqlite(output_dir, {"R1EA-022": ["Replay"]})
            archived_catalog_dir.mkdir(parents=True, exist_ok=True)
            (archived_catalog_dir / "catalog_validation.json").write_text(
                json.dumps({"passed": True}, sort_keys=True),
                encoding="utf-8",
            )
            shutil.copyfile(active_sqlite, archived_catalog_dir / "review_sources.sqlite")
            write_replay_context(
                repo_root,
                review_id=review_id,
                source_set_id=source_set_id,
                catalog_dir=Path("source_library/runs/archived_catalog"),
            )
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
                catalog_dir=archived_catalog_dir,
            )
            upstream_results_path = (
                output_dir / "evaluations" / "upstream" / "upstream_evaluation_results.json"
            )
            upstream_results_path.parent.mkdir(parents=True, exist_ok=True)
            upstream_results_path.write_text(
                json.dumps(
                    {
                        "schema_version": "upstream-evaluation-results-v0",
                        "passed": True,
                        "lane_summaries": [
                            {"lane_id": "capture", "status": "direct_eval_present"},
                            {"lane_id": "catalog", "status": "direct_eval_present"},
                            {"lane_id": "extraction", "status": "direct_eval_present"},
                        ],
                        "failed_case_ids": [],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            phase_eval = run_phase_aligned_eval(
                output_dir=output_dir,
                review_id=review_id,
            )

            self.assertEqual(phase_eval.summary["review_id"], review_id)
            self.assertEqual(phase_eval.summary["source_set_id"], source_set_id)
            self.assertEqual(
                Path(phase_eval.summary["catalog_dir"]),
                archived_catalog_dir.resolve(),
            )
            self.assertTrue(phase_eval.review_output_path.exists())
            catalog_phase = phase(phase_eval.summary, "catalog_capture")
            self.assertTrue(catalog_phase["passed"])

    def test_review_phase_eval_rejects_mismatched_tracked_catalog_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            output_dir = repo_root / "source_library"
            review_id = "tracked-replay-review"
            write_replay_context(
                repo_root,
                review_id=review_id,
                source_set_id="source-set-test",
                catalog_dir=Path("source_library/runs/archived_catalog"),
            )

            with self.assertRaises(ReplayContextMismatchError):
                run_phase_aligned_eval(
                    output_dir=output_dir,
                    review_id=review_id,
                    catalog_dir=output_dir / "catalog",
                )

    def test_review_phase_eval_overwrites_stale_review_result_with_tracked_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            output_dir = repo_root / "source_library"
            review_id = "tracked-replay-review"
            current_source_set_id = "source-set-current"
            stale_source_set_id = "source-set-stale"
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)
            stale_result_path = review_dir / "phase_eval_results.json"
            stale_result_path.write_text(
                json.dumps(
                    {
                        "passed": True,
                        "review_id": review_id,
                        "source_set_id": stale_source_set_id,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            write_replay_context(
                repo_root,
                review_id=review_id,
                source_set_id=current_source_set_id,
                catalog_dir=Path("source_library/runs/current_catalog"),
            )

            phase_eval = run_phase_aligned_eval(
                output_dir=output_dir,
                review_id=review_id,
            )

            persisted_result = json.loads(stale_result_path.read_text(encoding="utf-8"))
            self.assertEqual(phase_eval.summary["source_set_id"], current_source_set_id)
            self.assertEqual(persisted_result["source_set_id"], current_source_set_id)
            self.assertFalse(persisted_result["passed"])

    def test_review_phase_eval_marks_stale_draft_generation_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "review-test"
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_catalog_source_set_manifest(output_dir, source_set_id)
            review_dir = write_minimal_draft_generation_review(
                output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )
            config_path = write_minimal_draft_generation_config(
                Path(tmp) / "draft_generation_config.json",
                review_id=review_id,
                source_set_id=source_set_id,
            )
            run_draft_generate(
                output_dir=output_dir,
                review_id=review_id,
                config_path=config_path,
            )
            run_draft_generation_eval(
                output_dir=output_dir,
                review_id=review_id,
                config_path=config_path,
            )
            decision_support_path = (
                review_dir / "decision_support" / "ea_consistency_decision_support.json"
            )
            decision_support = json.loads(decision_support_path.read_text(encoding="utf-8"))
            decision_support["validation_and_replay"]["replay_commands"] = [
                "stale input mutation for phase eval"
            ]
            decision_support_path.write_text(
                json.dumps(decision_support, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
            )

            draft_phase = phase(result.summary, "draft_generation_defensibility")
            self.assertFalse(draft_phase["passed"])
            self.assertFalse(draft_phase["reviewer_ready"])
            self.assertIn(
                "manifest_input_artifacts_fresh",
                draft_phase["details"]["failed_checks"],
            )
            self.assertEqual(
                draft_phase["details"]["stale_input_artifacts"][0]["artifact_key"],
                "decision_support",
            )

    def test_review_phase_eval_allows_semantically_stable_final_qa_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "review-test"
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_catalog_source_set_manifest(output_dir, source_set_id)
            review_dir = write_minimal_draft_generation_review(
                output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )
            config_path = write_minimal_draft_generation_config(
                Path(tmp) / "draft_generation_config.json",
                review_id=review_id,
                source_set_id=source_set_id,
            )
            run_draft_generate(
                output_dir=output_dir,
                review_id=review_id,
                config_path=config_path,
            )
            run_draft_generation_eval(
                output_dir=output_dir,
                review_id=review_id,
                config_path=config_path,
            )
            final_qa_path = (
                review_dir / "final_qa" / "east_crazies_final_qa_certification.json"
            )
            final_qa = json.loads(final_qa_path.read_text(encoding="utf-8"))
            final_qa["gate_replay_summary"] = {
                "phase_eval": {"phase_count": 99, "passed_phase_count": 98}
            }
            final_qa_path.write_text(
                json.dumps(final_qa, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
            )

            draft_phase = phase(result.summary, "draft_generation_defensibility")
            self.assertTrue(draft_phase["passed"])
            self.assertTrue(draft_phase["reviewer_ready"])
            self.assertEqual(
                draft_phase["details"]["stale_input_artifacts"],
                [],
            )


if __name__ == "__main__":
    unittest.main()
