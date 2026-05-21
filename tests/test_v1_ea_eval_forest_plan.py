from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.support.v1_ea_eval_fixtures import _read_json
from tests.support.v1_ea_eval_fixtures import _summary_check
from tests.support.v1_ea_eval_fixtures import _write_eval_contract
from tests.support.v1_ea_eval_fixtures import _write_json
from tests.support.v1_ea_eval_fixtures import _write_positive_review
from usfs_r1_ea_sources.v1_ea_eval import run_v1_ea_review_eval


class V1EAReviewEvalForestPlanTests(unittest.TestCase):
    def test_v1_eval_tracks_standard_resolution_queue_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "forest_plan_reviewer_resolution_queue.json",
                {
                    "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                    "summary": {"item_count": 2},
                    "items": [
                        {"component_id": "component-dc", "component_type": "desired_condition"},
                        {"component_id": "component-guideline", "component_type": "guideline"},
                    ],
                },
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["forest_plan"]["max_reviewer_resolution_items"] = 2
            contract["forest_plan"]["max_standard_reviewer_resolution_items"] = 0
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["reviewer_resolution_item_count"], 2)
            self.assertEqual(metrics["standard_reviewer_resolution_item_count"], 0)
            self.assertTrue(result.summary["forest_plan_passed"])
            self.assertTrue(
                result.summary["eval_lanes"]["forest_plan"][
                    "component_adjudication_required"
                ]
            )
            self.assertEqual(
                result.summary["eval_lanes"]["forest_plan"][
                    "pending_component_adjudication_count"
                ],
                2,
            )
            self.assertEqual(
                result.summary["eval_lanes"]["forest_plan"]["failed_check_names"],
                [],
            )

    def test_v1_eval_uses_component_adjudication_pending_counts_for_ready_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "forest_plan_reviewer_resolution_queue.json",
                {
                    "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                    "summary": {"item_count": 2},
                    "items": [
                        {"component_id": "component-dc", "component_type": "desired_condition"},
                        {"component_id": "component-standard", "component_type": "standard"},
                    ],
                },
            )
            _write_json(
                review_dir / "forest_plan_component_adjudication_eval.json",
                {
                    "schema_version": "forest-plan-component-adjudication-eval-v0",
                    "summary": {
                        "reviewer_ready": True,
                        "pending_adjudication_count": 0,
                        "queue_item_count": 2,
                        "resolved_adjudication_count": 2,
                        "failed_checks": [],
                        "passed": True,
                    },
                    "item_results": [
                        {
                            "component_id": "component-dc",
                            "component_type": "desired_condition",
                            "disposition": "applicability_false_positive",
                            "adjudication_outcome": "system_miss",
                        },
                        {
                            "component_id": "component-standard",
                            "component_type": "standard",
                            "disposition": "evidence_linking_miss",
                            "adjudication_outcome": "system_miss",
                        },
                    ],
                },
            )
            summary = _read_json(review_dir / "forest_plan_context_summary.json")
            summary["component_adjudication"] = {
                "reviewer_ready": True,
                "pending_adjudication_count": 0,
                "queue_item_count": 2,
                "resolved_adjudication_count": 2,
                "failed_checks": [],
            }
            _write_json(review_dir / "forest_plan_context_summary.json", summary)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["reviewer_resolution_item_count"], 0)
            self.assertEqual(metrics["standard_reviewer_resolution_item_count"], 0)
            self.assertEqual(metrics["reviewer_resolution_queue_item_count"], 2)
            self.assertEqual(metrics["standard_reviewer_resolution_queue_item_count"], 1)
            forest_lane = result.summary["eval_lanes"]["forest_plan"]
            self.assertEqual(forest_lane["pending_component_adjudication_count"], 0)
            self.assertEqual(forest_lane["pending_standard_adjudication_count"], 0)
            self.assertEqual(forest_lane["reviewer_resolution_queue_item_count"], 2)
            self.assertEqual(
                forest_lane["standard_reviewer_resolution_queue_item_count"],
                1,
            )
            self.assertTrue(forest_lane["component_adjudication_required"])
            self.assertTrue(forest_lane["component_adjudication_present"])
            self.assertTrue(forest_lane["component_adjudication_reviewer_ready"])
            self.assertEqual(forest_lane["failed_check_names"], [])

    def test_v1_eval_fails_open_standard_resolution_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "forest_plan_reviewer_resolution_queue.json",
                {
                    "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                    "summary": {"item_count": 1},
                    "items": [
                        {"component_id": "component-standard", "component_type": "standard"},
                    ],
                },
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["forest_plan"]["max_reviewer_resolution_items"] = 1
            contract["forest_plan"]["max_standard_reviewer_resolution_items"] = 0
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["forest_plan_standard_reviewer_resolution_open"], 1)
            self.assertEqual(result.summary["metrics"]["standard_reviewer_resolution_item_count"], 1)
            self.assertTrue(result.summary["broader_ea_passed"])
            self.assertFalse(result.summary["forest_plan_passed"])
            self.assertEqual(result.summary["broader_ea_failure_category_counts"], {})
            self.assertEqual(
                result.summary["forest_plan_failure_category_counts"][
                    "forest_plan_standard_reviewer_resolution_open"
                ],
                1,
            )

    def test_v1_eval_keeps_forest_plan_validation_failure_in_forest_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "compliance_validation.json",
                {
                    "schema_version": "compliance-validation-v0",
                    "passed": False,
                    "checks": [
                        {
                            "name": "forest_plan_component_gate_reviewer_ready",
                            "passed": False,
                        }
                    ],
                },
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertTrue(result.summary["broader_ea_passed"])
            self.assertFalse(result.summary["forest_plan_passed"])
            self.assertEqual(result.summary["broader_ea_failure_category_counts"], {})
            self.assertEqual(result.summary["forest_plan_failure_category_counts"], {})
            self.assertEqual(result.summary["eval_lanes"]["broader_ea"]["failed_check_names"], [])
            self.assertEqual(
                result.summary["eval_lanes"]["forest_plan"]["failed_check_names"],
                ["compliance_validation_passed"],
            )

    def test_v1_eval_keeps_component_adjudication_blocker_in_forest_plan_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "forest_plan_reviewer_resolution_queue.json",
                {
                    "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                    "summary": {"item_count": 1},
                    "items": [
                        {"component_id": "component-dc", "component_type": "desired_condition"},
                    ],
                },
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertTrue(result.summary["broader_ea_passed"])
            self.assertFalse(result.summary["forest_plan_passed"])
            self.assertEqual(result.summary["broader_ea_failure_category_counts"], {})
            self.assertEqual(
                result.summary["forest_plan_failure_category_counts"][
                    "forest_plan_reviewer_resolution_open"
                ],
                1,
            )
            forest_lane = result.summary["eval_lanes"]["forest_plan"]
            self.assertTrue(forest_lane["component_adjudication_required"])
            self.assertEqual(forest_lane["pending_component_adjudication_count"], 1)
            self.assertEqual(forest_lane["pending_standard_adjudication_count"], 0)
            self.assertEqual(forest_lane["failed_check_names"], ["forest_plan_expectations_met"])
            self.assertEqual(result.summary["eval_lanes"]["broader_ea"]["failed_check_names"], [])

    def test_v1_eval_accepts_declared_typed_blocked_forest_plan_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "forest_plan_reviewer_resolution_queue.json",
                {
                    "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                    "summary": {"item_count": 1},
                    "items": [
                        {"component_id": "component-dc", "component_type": "desired_condition"},
                    ],
                },
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["forest_unit_id"] = "custer-gallatin-nf"
            contract["package_style_tags"] = ["typed_blocked_expansion"]
            contract["expected_lane_states"] = {
                "broader_ea_passed": True,
                "forest_plan_passed": False,
            }
            contract["allowed_blocker_categories"] = [
                "forest_plan_reviewer_resolution_open",
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            self.assertFalse(result.summary["actual_overall_passed"])
            self.assertEqual(result.summary["contract_status"], "typed_blocked")
            self.assertEqual(result.summary["forest_unit_id"], "custer-gallatin-nf")
            self.assertEqual(result.summary["package_style_tags"], ["typed_blocked_expansion"])
            lane_check = _summary_check(result.summary, "expected_lane_states_matched")
            self.assertTrue(lane_check["passed"])
            self.assertEqual(
                lane_check["details"]["matched_blocker_categories"],
                ["forest_plan_reviewer_resolution_open"],
            )

    def test_v1_eval_rejects_unexpected_typed_blocked_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_json(
                review_dir / "forest_plan_reviewer_resolution_queue.json",
                {
                    "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                    "summary": {"item_count": 1},
                    "items": [
                        {"component_id": "component-dc", "component_type": "desired_condition"},
                    ],
                },
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["expected_lane_states"] = {
                "broader_ea_passed": True,
                "forest_plan_passed": False,
            }
            contract["allowed_blocker_categories"] = ["forest_plan_reviewer_not_ready"]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["contract_status"], "mismatch")
            lane_check = _summary_check(result.summary, "expected_lane_states_matched")
            self.assertFalse(lane_check["passed"])
            self.assertEqual(
                lane_check["details"]["unexpected_blocker_categories"],
                ["forest_plan_reviewer_resolution_open"],
            )
