from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_coverage import run_compliance_coverage
from usfs_r1_ea_sources.compliance_gold_eval import run_compliance_gold_eval
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links

from tests.support.compliance_component_fixtures import (
    _write_component_adjudication_eval,
    _write_component_eval,
)
from tests.support.compliance_phase_eval_fixtures import (
    _write_final_qa_phase_outputs,
    _write_graph_phase_outputs,
)
from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _direct_eval_result_payload,
    _phase,
    _run_generated_compliance_review,
    _write_compliance_eval_file,
    _write_coverage_matrix,
    _write_downstream_direct_eval_phase_outputs,
    _write_gold_eval_file,
    _write_package,
    _write_rule_pack,
)


class CompliancePhaseEvalTests(unittest.TestCase):
    def test_phase_eval_rejects_stale_compliance_coverage_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            link_result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "coverage-case",
                        "package_text": "Purpose and Need. Mitigation measures support a FONSI.",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                    }
                ],
            )
            coverage_result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=_write_coverage_matrix(Path(tmp)),
                eval_file=eval_path,
                links_path=link_result.links_path,
            )
            coverage_summary = json.loads(coverage_result.output_path.read_text(encoding="utf-8"))
            coverage_summary["source_set_id"] = "source-set-other"
            coverage_result.output_path.write_text(
                json.dumps(coverage_summary, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            coverage_phase = _phase(phase_result.summary, "compliance_coverage")
            self.assertFalse(coverage_phase["passed"])
            self.assertFalse(coverage_phase["reviewer_ready"])
            self.assertTrue(coverage_phase["details"]["coverage_passed"])
            self.assertFalse(coverage_phase["details"]["source_set_matches"])

    def test_review_phase_eval_prefers_review_scoped_compliance_gold_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "review-test"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)

            run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
                results_dir=review_dir,
            )
            global_gold_dir = output_dir / "reviews" / "compliance_gold_eval"
            global_gold_dir.mkdir(parents=True, exist_ok=True)
            (global_gold_dir / "compliance_gold_eval_results.json").write_text(
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

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            gold_phase = _phase(phase_result.summary, "compliance_gold_eval")
            self.assertEqual(
                gold_phase["details"]["gold_eval_path"],
                str(review_dir / "compliance_gold_eval_results.json"),
            )
            self.assertTrue(gold_phase["details"]["source_set_matches"])
            self.assertEqual(gold_phase["details"]["case_count"], 3)

    def test_review_phase_eval_ignores_unrelated_global_gold_without_review_scoped_gold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "review-test"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            global_gold_dir = output_dir / "reviews" / "compliance_gold_eval"
            global_gold_dir.mkdir(parents=True, exist_ok=True)
            (global_gold_dir / "compliance_gold_eval_results.json").write_text(
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

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            phase_names = {phase["name"] for phase in phase_result.summary["phases"]}
            self.assertNotIn("compliance_gold_eval", phase_names)
            self.assertTrue(phase_result.summary["reviewer_ready"])

    def test_phase_eval_ignores_unrelated_compliance_gold_source_set_for_source_set_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))
            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )
            _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)
            gold_summary = json.loads(result.output_path.read_text(encoding="utf-8"))
            gold_summary["source_set_id"] = "source-set-other"
            result.output_path.write_text(
                json.dumps(gold_summary, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertTrue(phase_result.summary["reviewer_ready"])
            phase_names = {phase["name"] for phase in phase_result.summary["phases"]}
            self.assertNotIn("compliance_gold_eval", phase_names)

    def test_phase_eval_can_include_compliance_review_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 17)
            self.assertEqual(result.summary["review_id"], "phase-review")
            self.assertFalse(result.summary["declared_review_contract"])
            self.assertFalse(result.summary["contract_backed_promotion_ready"])
            self.assertEqual(
                result.review_output_path,
                output_dir / "reviews" / "phase-review" / "phase_eval_results.json",
            )
            self.assertTrue(result.review_output_path.exists())
            review_phase_summary = json.loads(result.review_output_path.read_text(encoding="utf-8"))
            self.assertEqual(review_phase_summary["review_id"], "phase-review")
            self.assertTrue(review_phase_summary["reviewer_ready"])
            evaluation_coverage_phase = _phase(result.summary, "evaluation_coverage")
            self.assertTrue(evaluation_coverage_phase["passed"])
            self.assertEqual(
                evaluation_coverage_phase["details"]["review_direct_eval_status"],
                "not_required_for_ad_hoc_review",
            )
            claim_phase = _phase(result.summary, "claim_extraction")
            self.assertTrue(claim_phase["passed"])
            self.assertTrue(claim_phase["reviewer_ready"])
            rule_claim_phase = _phase(result.summary, "rule_claim_binding")
            self.assertTrue(rule_claim_phase["passed"])
            self.assertTrue(rule_claim_phase["reviewer_ready"])
            compliance_phase = _phase(result.summary, "compliance_review")
            self.assertTrue(compliance_phase["passed"])
            self.assertTrue(compliance_phase["reviewer_ready"])
            self.assertEqual(compliance_phase["details"]["rule_pack_id"], "generated-unit-nepa-ea")
            self.assertTrue(compliance_phase["details"]["matrix_exists"])
            self.assertTrue(compliance_phase["details"]["matrix_pdf_exists"])
            self.assertTrue(compliance_phase["details"]["matrix_pdf_header_valid"])
            self.assertTrue(compliance_phase["details"]["matrix_schema_matches"])
            self.assertTrue(compliance_phase["details"]["matrix_row_count_matches"])

    def test_review_phase_eval_uses_canonical_rule_claim_direct_eval_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "phase-review"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            review_result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            base_rule_claim_eval_path = (
                output_dir
                / "derived"
                / source_set_id
                / "rule_claim_links"
                / "nepa-ea-v0"
                / "0.4.0"
                / "rule_claim_link_eval_results.json"
            )
            base_rule_claim_eval_path.write_text(
                json.dumps(
                    _direct_eval_result_payload(
                        contract_path=Path("config/rule_claim_link_eval_seed.json"),
                        eval_id="rule-claim-direct-eval-v1",
                        source_set_id=source_set_id,
                    ),
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            selected_rule_claim_eval_path = (
                Path(review_result.summary["rule_claim_summary_path"]).parent
                / "rule_claim_link_eval_results.json"
            )
            selected_rule_claim_eval_path.write_text(
                json.dumps(
                    _direct_eval_result_payload(
                        contract_path=Path("config/rule_claim_link_eval_seed.json"),
                        eval_id="rule-claim-direct-eval-v1",
                        source_set_id="source-set-other",
                    ),
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
            )

            rule_claim_phase = _phase(phase_result.summary, "rule_claim_binding")
            self.assertTrue(rule_claim_phase["passed"])
            self.assertTrue(rule_claim_phase["reviewer_ready"])
            self.assertEqual(
                Path(rule_claim_phase["details"]["direct_eval_summary_path"]).resolve(),
                base_rule_claim_eval_path.resolve(),
            )
            self.assertEqual(
                rule_claim_phase["details"]["direct_eval_status"],
                "direct_eval_present",
            )

    def test_phase_eval_can_include_final_qa_certification_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "phase-review"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_final_qa_phase_outputs(
                output_dir / "reviews" / review_id,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 18)
            final_qa_phase = _phase(result.summary, "final_qa_certification_report")
            self.assertTrue(final_qa_phase["passed"])
            self.assertTrue(final_qa_phase["reviewer_ready"])
            self.assertTrue(final_qa_phase["details"]["validation_result_passed"])
            self.assertEqual(final_qa_phase["details"]["failed_check_count"], 0)

    def test_phase_eval_accepts_base_gold_eval_for_generated_rule_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need. Mitigation measures support a FONSI.",
            )
            base_rule_pack_path = _write_rule_pack(Path(tmp))
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            gold_path = _write_gold_eval_file(Path(tmp))
            gold_result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=base_rule_pack_path,
                gold_file=gold_path,
            )
            self.assertTrue(gold_result.summary["passed"])

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            gold_phase = _phase(result.summary, "compliance_gold_eval")
            self.assertTrue(gold_phase["passed"])
            self.assertTrue(gold_phase["reviewer_ready"])
            self.assertEqual(gold_phase["details"]["rule_pack_match_mode"], "generated_base")
            self.assertTrue(gold_phase["details"]["effective_promotion_ready"])
            self.assertEqual(
                gold_phase["details"]["generated_base_rule_pack_id"],
                "unit-nepa-ea",
            )

    def test_phase_eval_can_include_component_adjudication_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_adjudication_eval(
                output_dir / "reviews" / "phase-review",
                source_set_id=source_set_id,
                review_id="phase-review",
                passed=True,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 18)
            adjudication_phase = _phase(result.summary, "forest_plan_component_adjudication")
            self.assertTrue(adjudication_phase["passed"])
            self.assertTrue(adjudication_phase["reviewer_ready"])
            self.assertEqual(adjudication_phase["details"]["queue_item_count"], 2)
            self.assertEqual(
                adjudication_phase["details"]["adjudication_completion_rate"],
                1.0,
            )
            self.assertEqual(adjudication_phase["details"]["real_ea_omission_count"], 2)
            self.assertEqual(adjudication_phase["details"]["system_miss_count"], 0)
            self.assertEqual(
                adjudication_phase["details"]["adjudication_outcome_counts"],
                {"real_ea_omission": 2},
            )

    def test_phase_eval_rejects_stale_component_adjudication_queue_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="stale-adjudication-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            review_dir = output_dir / "reviews" / "stale-adjudication-review"
            _write_component_adjudication_eval(
                review_dir,
                source_set_id=source_set_id,
                review_id="stale-adjudication-review",
                passed=True,
            )
            (review_dir / "forest_plan_reviewer_resolution_queue.json").write_text(
                json.dumps(
                    {
                        "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                        "review_id": "stale-adjudication-review",
                        "source_set_id": source_set_id,
                        "item_count": 0,
                        "items": [],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="stale-adjudication-review",
            )

            self.assertFalse(result.summary["reviewer_ready"])
            adjudication_phase = _phase(result.summary, "forest_plan_component_adjudication")
            self.assertFalse(adjudication_phase["passed"])
            self.assertIn(
                "queue_item_count_mismatch",
                adjudication_phase["details"]["failed_checks"],
            )
            self.assertEqual(adjudication_phase["details"]["queue_item_count"], 2)
            self.assertEqual(adjudication_phase["details"]["current_queue_item_count"], 0)

    def test_phase_eval_can_include_component_eval_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_eval(
                output_dir / "reviews" / "phase-review",
                source_set_id=source_set_id,
                review_id="phase-review",
                passed=True,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 18)
            component_eval_phase = _phase(result.summary, "forest_plan_component_eval")
            self.assertTrue(component_eval_phase["passed"])
            self.assertTrue(component_eval_phase["reviewer_ready"])
            self.assertEqual(component_eval_phase["details"]["case_count"], 3)
            self.assertEqual(
                component_eval_phase["details"]["metrics"]["applicable_standard_recall"],
                1.0,
            )

    def test_phase_eval_rejects_component_eval_schema_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_eval(
                output_dir / "reviews" / "phase-review",
                source_set_id=source_set_id,
                review_id="phase-review",
                passed=True,
                schema_version="wrong-schema",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertFalse(result.summary["reviewer_ready"])
            component_eval_phase = _phase(result.summary, "forest_plan_component_eval")
            self.assertFalse(component_eval_phase["passed"])
            self.assertEqual(
                component_eval_phase["details"]["failed_checks"],
                ["schema_version_mismatch"],
            )

    def test_phase_eval_rejects_pending_component_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="pending-adjudication-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_adjudication_eval(
                output_dir / "reviews" / "pending-adjudication-review",
                source_set_id=source_set_id,
                review_id="pending-adjudication-review",
                passed=False,
                pending_count=1,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="pending-adjudication-review",
            )

            self.assertFalse(result.summary["reviewer_ready"])
            adjudication_phase = _phase(result.summary, "forest_plan_component_adjudication")
            self.assertFalse(adjudication_phase["passed"])
            self.assertFalse(adjudication_phase["reviewer_ready"])
            self.assertIn("adjudication_eval_failed", adjudication_phase["details"]["failed_checks"])
            self.assertEqual(adjudication_phase["details"]["pending_adjudication_count"], 1)
            self.assertEqual(
                adjudication_phase["details"]["failure_category_counts"],
                {"adjudication_pending": 1},
            )

    def test_phase_eval_rejects_missing_compliance_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="missing-matrix-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            result.compliance_matrix_path.unlink()

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="missing-matrix-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["matrix_exists"])
            self.assertIn(
                "matrix_exists",
                compliance_phase["details"]["failed_artifact_checks"],
            )

    def test_phase_eval_rejects_missing_compliance_matrix_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="missing-matrix-pdf-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            result.compliance_matrix_pdf_path.unlink()

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="missing-matrix-pdf-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["matrix_pdf_exists"])
            self.assertIn(
                "matrix_pdf_exists",
                compliance_phase["details"]["failed_artifact_checks"],
            )

    def test_phase_eval_rejects_stale_compliance_review_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="stale-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            report = json.loads(result.compliance_review_path.read_text(encoding="utf-8"))
            report["summary"]["source_set_id"] = "source-set-other"
            result.compliance_review_path.write_text(
                json.dumps(report, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="stale-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["source_set_matches"])
