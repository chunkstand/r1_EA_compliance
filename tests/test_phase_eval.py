from __future__ import annotations

from pathlib import Path
import hashlib
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
from tests.support.phase_eval_fixtures import direct_eval_result_payload
from tests.support.phase_eval_fixtures import phase
from tests.support.phase_eval_fixtures import read_jsonl
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest_for_dir
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_sqlite_for_dir
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_catalog_validation_for_dir
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics
from tests.support.phase_eval_fixtures import write_forest_plan_component_retrieval_eval_results
from tests.support.phase_eval_fixtures import write_forest_plan_profile_eval_results
from tests.support.phase_eval_fixtures import write_jsonl
from tests.support.phase_eval_fixtures import write_replay_context


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_WORKBOOK = REPO_ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"


class PhaseEvalTests(unittest.TestCase):
    def test_phase_eval_reports_evidence_graph_freshness_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-010"],
            )
            chunks_path = write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-010",
                        title="Clean source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-010 | Clean source | artifact abc123",
                        text="The agency must evaluate connected actions.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-010": ["Connected actions"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            chunks = read_jsonl(chunks_path)
            forged_text = "A forged replacement span should not bind to retrieval."
            chunks[0]["text"] = forged_text
            chunks[0]["char_end"] = len(forged_text)
            chunks[0]["content_sha256"] = hashlib.sha256(
                forged_text.encode("utf-8")
            ).hexdigest()
            write_jsonl(chunks_path, chunks)

            build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)
            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            graph_phase = phase(result.summary, "evidence_graph")
            self.assertEqual(graph_phase["details"]["freshness_status"], "failed")
            self.assertIn(
                "chunks_match_retrieval_index",
                graph_phase["details"]["failed_validation_checks"],
            )

    def test_phase_eval_reports_partial_readiness_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-004"],
                catalog_source_count=2,
                filters={"id": "R1EA-004", "parser": None, "limit": None},
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-004",
                        title="Diagnostic source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-004 | Diagnostic source | artifact abc123",
                        text="The agency considered feasible alternatives.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-004": ["Alternatives"]})
            build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_extraction=True,
            )
            build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_retrieval=True,
            )

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["reviewer_ready"])
            blocker_phases = {blocker["phase"] for blocker in result.summary["blockers"]}
            self.assertIn("extraction", blocker_phases)
            self.assertIn("retrieval", blocker_phases)
            self.assertIn("evidence_graph", blocker_phases)
            self.assertTrue(result.output_path.exists())

    def test_phase_eval_source_set_replay_uses_archived_catalog_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "archived_catalog"
            write_catalog_validation(output_dir, passed=False)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-020"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-020",
                        title="Archived catalog source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-020 | Archived catalog source | artifact abc123",
                        text="Archived catalog replay should stay scoped to the selected source set.",
                    )
                ],
            )
            active_sqlite = write_catalog_sqlite(output_dir, {"R1EA-020": ["Replay"]})
            archived_catalog_dir.mkdir(parents=True, exist_ok=True)
            (archived_catalog_dir / "catalog_validation.json").write_text(
                json.dumps({"passed": True}, sort_keys=True),
                encoding="utf-8",
            )
            shutil.copyfile(active_sqlite, archived_catalog_dir / "review_sources.sqlite")
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
                catalog_dir=archived_catalog_dir,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                catalog_dir=archived_catalog_dir,
            )

            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))
            graph_phase = phase(result.summary, "evidence_graph")
            self.assertTrue(graph_phase["passed"])
            self.assertTrue(graph_phase["reviewer_ready"])

    def test_phase_eval_source_set_replay_auto_resolves_compatible_archived_catalog_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "2026-05-14-replay" / "catalog_gate"
            write_catalog_validation(output_dir, passed=False)
            write_catalog_source_set_manifest(output_dir, "source-set-other")
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-023"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-023",
                        title="Archived catalog source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-023 | Archived catalog source | artifact abc123",
                        text="Source-set replay should find the matching archived catalog gate.",
                    )
                ],
            )
            write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-023": ["Replay"],
                    "R1EA-024": ["Extra row"],
                },
            )
            write_catalog_validation_for_dir(archived_catalog_dir, passed=True)
            write_catalog_source_set_manifest_for_dir(
                archived_catalog_dir,
                "source-set-compatible-archived",
            )
            write_catalog_sqlite_for_dir(
                archived_catalog_dir,
                {"R1EA-023": ["Replay"]},
            )
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))
            graph_phase = phase(result.summary, "evidence_graph")
            self.assertTrue(graph_phase["passed"])
            self.assertTrue(graph_phase["reviewer_ready"])

    def test_phase_eval_reports_upstream_evaluation_and_fails_closed_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-030"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-030",
                        title="Upstream eval phase source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-030 | Upstream eval phase source | artifact abc123",
                        text="The readiness gate should expose upstream evaluation coverage separately.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-030": ["Upstream evaluation"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            missing_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            upstream_phase = phase(missing_result.summary, "upstream_evaluation")
            self.assertFalse(upstream_phase["passed"])
            self.assertFalse(upstream_phase["reviewer_ready"])
            extraction_phase = phase(missing_result.summary, "extraction")
            self.assertIn("missing_required_direct_eval", extraction_phase["failure_reasons"])
            self.assertIn("proxy_only_coverage", extraction_phase["failure_reasons"])
            coverage_phase = phase(missing_result.summary, "evaluation_coverage")
            self.assertFalse(coverage_phase["passed"])
            self.assertGreater(
                coverage_phase["details"]["missing_direct_eval_phase_count"],
                0,
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

            ready_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            upstream_phase = phase(ready_result.summary, "upstream_evaluation")
            self.assertTrue(upstream_phase["passed"])
            self.assertTrue(upstream_phase["reviewer_ready"])
            extraction_phase = phase(ready_result.summary, "extraction")
            self.assertTrue(extraction_phase["details"]["direct_eval_present"])

    def test_phase_eval_reports_downstream_direct_evaluation_and_fails_closed_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-031"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-031",
                        title="Downstream eval phase source",
                        document_role="agency_policy",
                        authority_level="federal_guidance",
                        citation_label="R1EA-031 | Downstream eval phase source | artifact abc123",
                        text="The readiness gate should expose downstream direct eval coverage separately.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-031": ["Downstream evaluation"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            missing_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            downstream_phase = phase(missing_result.summary, "downstream_direct_evaluation")
            self.assertFalse(downstream_phase["passed"])
            self.assertFalse(downstream_phase["reviewer_ready"])
            retrieval_phase = phase(missing_result.summary, "retrieval")
            self.assertIn("missing_required_direct_eval", retrieval_phase["failure_reasons"])
            self.assertIn("proxy_only_coverage", retrieval_phase["failure_reasons"])
            coverage_phase = phase(missing_result.summary, "evaluation_coverage")
            self.assertFalse(coverage_phase["passed"])
            self.assertGreater(
                coverage_phase["details"]["proxy_only_phase_count"],
                0,
            )

            contracts = {
                "retrieval_eval": (
                    Path("config/retrieval_eval_seed.json"),
                    output_dir / "derived" / source_set_id / "retrieval" / "retrieval_eval_results.json",
                    "retrieval-direct-eval-v1",
                ),
                "claim_eval": (
                    Path("config/claim_eval_seed.json"),
                    output_dir / "derived" / source_set_id / "claims" / "claim_eval_results.json",
                    "claim-direct-eval-v1",
                ),
                "rule_claim_eval": (
                    Path("config/rule_claim_link_eval_seed.json"),
                    output_dir / "derived" / source_set_id / "rule_claim_links" / "nepa-ea-v0" / "0.4.0" / "rule_claim_link_eval_results.json",
                    "rule-claim-direct-eval-v1",
                ),
                "compliance_review_eval": (
                    Path("config/compliance_review_eval_seed.json"),
                    output_dir / "reviews" / "compliance_review_eval" / "compliance_review_eval_results.json",
                    "compliance-review-direct-eval-v1",
                ),
            }
            for contract_path, result_path, eval_id in contracts.values():
                result_path.parent.mkdir(parents=True, exist_ok=True)
                result_path.write_text(
                    json.dumps(
                        direct_eval_result_payload(
                            contract_path=contract_path,
                            eval_id=eval_id,
                            source_set_id=source_set_id,
                        ),
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )

            ready_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            downstream_phase = phase(ready_result.summary, "downstream_direct_evaluation")
            self.assertTrue(downstream_phase["passed"])
            self.assertTrue(downstream_phase["reviewer_ready"])
            retrieval_phase = phase(ready_result.summary, "retrieval")
            self.assertTrue(retrieval_phase["details"]["direct_eval_present"])
            self.assertEqual(
                ready_result.summary["phase_eval_contract_id"],
                "phase-eval-direct-eval-v1",
            )

    def test_phase_eval_requires_cross_forest_profile_eval_for_source_set_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-5e65d845ce77e1a0"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-032"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-032",
                        title="Cross-forest profile eval phase source",
                        document_role="forest_plan",
                        authority_level="forest_plan",
                        citation_label="R1EA-032 | Cross-forest profile eval phase source | artifact abc123",
                        text="The full-canonical source-set graph should require cross-forest profile eval coverage.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-032": ["Cross-forest profile eval"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            graph_dir = output_dir / "derived" / source_set_id / "knowledge_graph"
            graph_dir.mkdir(parents=True, exist_ok=True)
            (graph_dir / "nepa_3d_graph_validation.json").write_text(
                json.dumps(
                    {
                        "passed": True,
                        "checks": [],
                        "failure_category_counts": {},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (graph_dir / "nepa_3d_graph_summary.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "validation_passed": True,
                        "validation_check_count": 66,
                        "failed_validation_check_count": 0,
                        "node_count": 10,
                        "edge_count": 12,
                        "readiness_blocker_counts": {},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            missing_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            graph_phase = phase(missing_result.summary, "nepa_3d_source_set_graph")
            self.assertFalse(graph_phase["passed"])
            self.assertFalse(graph_phase["reviewer_ready"])
            self.assertEqual(graph_phase["details"]["direct_eval_status"], "direct_eval_missing")
            self.assertIn("missing_required_direct_eval", graph_phase["failure_reasons"])
            self.assertIn("proxy_only_coverage", graph_phase["failure_reasons"])

            write_forest_plan_profile_eval_results(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            ready_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            graph_phase = phase(ready_result.summary, "nepa_3d_source_set_graph")
            self.assertTrue(graph_phase["passed"])
            self.assertTrue(graph_phase["reviewer_ready"])
            self.assertEqual(graph_phase["details"]["direct_eval_status"], "direct_eval_present")
            self.assertEqual(
                graph_phase["details"]["direct_eval_details"]["covered_profile_count"],
                10,
            )
            self.assertEqual(
                graph_phase["details"]["direct_eval_details"]["profile_failure_count"],
                0,
            )

    def test_phase_eval_requires_component_retrieval_eval_for_full_canonical_component_phase(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-5e65d845ce77e1a0"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-033"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-033",
                        title="Component retrieval eval phase source",
                        document_role="forest_plan",
                        authority_level="forest_plan",
                        citation_label="R1EA-033 | Component retrieval eval phase source | artifact abc123",
                        text="The full-canonical source-set graph should require component retrieval coverage.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-033": ["Forest plan component retrieval"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            graph_dir = output_dir / "derived" / source_set_id / "knowledge_graph"
            graph_dir.mkdir(parents=True, exist_ok=True)
            (graph_dir / "nepa_3d_graph_validation.json").write_text(
                json.dumps(
                    {
                        "passed": True,
                        "checks": [],
                        "failure_category_counts": {},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (graph_dir / "nepa_3d_graph_summary.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "validation_passed": True,
                        "validation_check_count": 66,
                        "failed_validation_check_count": 0,
                        "node_count": 10,
                        "edge_count": 12,
                        "readiness_blocker_counts": {},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            missing_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            component_phase = phase(missing_result.summary, "forest_plan_component_retrieval")
            self.assertFalse(component_phase["passed"])
            self.assertFalse(component_phase["reviewer_ready"])
            self.assertEqual(
                component_phase["details"]["direct_eval_status"],
                "direct_eval_missing",
            )
            self.assertIn("missing_required_direct_eval", component_phase["failure_reasons"])
            self.assertIn("proxy_only_coverage", component_phase["failure_reasons"])

            write_forest_plan_component_retrieval_eval_results(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            ready_result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            component_phase = phase(ready_result.summary, "forest_plan_component_retrieval")
            self.assertTrue(component_phase["passed"])
            self.assertTrue(component_phase["reviewer_ready"])
            self.assertEqual(
                component_phase["details"]["direct_eval_status"],
                "direct_eval_present",
            )
            self.assertEqual(
                component_phase["details"]["direct_eval_details"]["covered_forest_unit_ids"],
                [
                    "beaverhead-deerlodge-nf",
                    "custer-gallatin-nf",
                    "flathead-nf",
                ],
            )

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

    def test_source_set_phase_eval_ignores_unrelated_gold_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-021"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-021",
                        title="Scoped replay source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-021 | Scoped replay source | artifact abc123",
                        text="Source-set phase replay should ignore unrelated global gold evals.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-021": ["Replay"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            gold_eval_dir = output_dir / "reviews" / "compliance_gold_eval"
            gold_eval_dir.mkdir(parents=True, exist_ok=True)
            (gold_eval_dir / "compliance_gold_eval_results.json").write_text(
                json.dumps(
                    {
                        "source_set_id": "source-set-other",
                        "passed": True,
                        "promotion_ready": True,
                        "rule_pack_id": "unit-nepa-ea",
                        "rule_pack_version": "0.4.0",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            phase_names = {item["name"] for item in result.summary["phases"]}
            self.assertNotIn("compliance_gold_eval", phase_names)

    def test_phase_eval_includes_canonical_contract_currentness_and_extraction_accuracy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["FOR-002"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="FOR-002",
                        title="Canonical source",
                        document_role="guidance",
                        authority_level="federal_guidance",
                        citation_label="FOR-002 | Canonical source | artifact abc123",
                        text="Canonical source register phases should appear in phase eval.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"FOR-002": ["Canonical phase"]})
            write_jsonl(
                output_dir / "catalog" / "source_catalog.jsonl",
                [
                    {
                        "source_set_id": source_set_id,
                        "source_record_id": "FOR-002",
                        "metadata": {"loader_contract": "source_register_v1"},
                    }
                ],
            )
            workbook_sha256 = hashlib.sha256(CANONICAL_WORKBOOK.read_bytes()).hexdigest()
            (output_dir / "catalog" / "source_set_manifest.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "workbook_path": "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
                        "workbook_sha256": workbook_sha256,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            currentness_dir = output_dir / "derived" / source_set_id / "authority_currentness"
            currentness_dir.mkdir(parents=True, exist_ok=True)
            (currentness_dir / "authority_currentness_report.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "summary": {
                            "source_set_id": source_set_id,
                            "validation_passed": True,
                            "authority_family_count": 1,
                            "current_authority_source_record_count": 1,
                            "documented_source_gap_count": 1,
                            "documented_source_non_addition_count": 0,
                            "superseded_replacement_confirmed_family_count": 1,
                            "temporal_lineage_record_count": 1,
                            "inventory_summary": {
                                "projection_basis": "source_register_v1_catalog_and_queue_rows",
                                "workbook_path": "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
                            },
                        },
                        "validation": {"passed": True, "checks": []},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
            (diagnostics_dir / "extraction_accuracy_audit.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "passed": True,
                        "record_count": 1,
                        "audited_record_count": 1,
                        "audited_chunk_count": 1,
                        "knowledge_base_admitted_source_record_ids": ["FOR-002"],
                        "knowledge_base_blocked_source_record_ids": [],
                        "checks": [],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(phase(result.summary, "source_register_contract")["passed"])
            self.assertTrue(phase(result.summary, "authority_currentness")["passed"])
            extraction_accuracy_phase = phase(result.summary, "extraction_accuracy")
            self.assertTrue(extraction_accuracy_phase["passed"])
            self.assertEqual(
                extraction_accuracy_phase["details"]["knowledge_base_admitted_source_record_count"],
                1,
            )

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
