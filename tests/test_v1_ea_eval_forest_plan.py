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
    def test_v1_eval_accepts_region1_alias_matched_forest_plan_component_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)

            component_findings = _read_json(review_dir / "forest_plan_component_findings.json")
            component_findings["findings"] = [
                {
                    **component_findings["findings"][0],
                    "component_id": "FOR-009-BC-DC-CMBCA-01",
                },
                {
                    **component_findings["findings"][1],
                    "component_id": "FOR-009-BC-STD-CMBCA-01",
                },
                {
                    **component_findings["findings"][2],
                    "component_id": "FOR-009-BC-SUIT-CMBCA-01",
                },
            ]
            _write_json(review_dir / "forest_plan_component_findings.json", component_findings)

            standard_coverage = _read_json(
                review_dir / "forest_plan_applicable_standard_coverage.json"
            )
            standard_coverage["standards"][0]["standard_id"] = "FOR-009-BC-STD-CMBCA-01"
            _write_json(
                review_dir / "forest_plan_applicable_standard_coverage.json",
                standard_coverage,
            )

            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["forest_unit_id"] = "custer-gallatin-nf"
            contract["forest_plan"]["expected_component_ids"] = [
                "R1PLAN-custer-gallatin-nf-02-BC-DC-CMBCA-01",
                "R1PLAN-custer-gallatin-nf-02-BC-STD-CMBCA-01",
                "R1PLAN-custer-gallatin-nf-02-BC-SUIT-CMBCA-01",
            ]
            contract["forest_plan"]["expected_applicable_standard_ids"] = [
                "R1PLAN-custer-gallatin-nf-02-BC-STD-CMBCA-01",
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.summary["forest_plan_passed"])
            self.assertEqual(result.summary["forest_plan_failure_category_counts"], {})
            self.assertEqual(
                result.summary["runtime_forest_scope"],
                {
                    "required": True,
                    "passed": True,
                    "expected_forest_unit_id": "custer-gallatin-nf",
                    "expected_scope_status": "custer_gallatin",
                    "actual_scope_status": "custer_gallatin",
                    "scope_status_expectation_present": True,
                    "scope_status_expectation_passed": True,
                    "failure_reasons": [],
                },
            )

    def test_v1_eval_counts_applicable_standard_rows_from_compliance_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            matrix = _read_json(review_dir / "compliance_matrix.json")
            matrix["forest_plan_compliance"]["summary"]["row_count"] = 2
            matrix["forest_plan_compliance"]["summary"]["applicable_standard_row_count"] = 2
            matrix["forest_plan_compliance"]["rows"].append(
                {
                    "row_id": "forest-plan-matrix:v1-unit:cg-lmp-2022-cmbca-std-02",
                    "component_id": "cg-lmp-2022-cmbca-std-02",
                    "component_type": "standard",
                    "applicability_status": "applicable",
                    "compliance_status": "insufficient_evidence",
                    "finding_status": "gap",
                }
            )
            _write_json(review_dir / "compliance_matrix.json", matrix)
            standard_coverage = _read_json(
                review_dir / "forest_plan_applicable_standard_coverage.json"
            )
            standard_coverage["standards"] = standard_coverage["standards"][:1]
            _write_json(
                review_dir / "forest_plan_applicable_standard_coverage.json",
                standard_coverage,
            )
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["forest_plan"]["min_applicable_standard_count"] = 2
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            payload = _read_json(result.output_path)
            min_standard = next(
                item
                for item in payload["forest_plan_results"]
                if item["expectation_id"] == "min_applicable_standard_count"
            )
            self.assertEqual(min_standard["actual"], 2)
            self.assertTrue(min_standard["passed"])

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

    def test_v1_eval_accepts_current_adjudication_ready_when_context_summary_is_stale(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            summary = _read_json(review_dir / "forest_plan_context_summary.json")
            summary["reviewer_ready"] = False
            summary["component_evaluation"] = {
                "reviewer_ready": False,
                "all_applicable_standards_applied": True,
            }
            summary["component_adjudication"] = {
                "reviewer_ready": False,
                "pending_adjudication_count": 0,
                "real_ea_omission_count": 0,
                "failed_checks": ["queue_item_count_mismatch"],
            }
            _write_json(review_dir / "forest_plan_context_summary.json", summary)
            _write_json(
                review_dir / "forest_plan_component_adjudication_eval.json",
                {
                    "schema_version": "forest-plan-component-adjudication-eval-v0",
                    "summary": {
                        "passed": True,
                        "pending_adjudication_count": 0,
                        "real_ea_omission_count": 0,
                        "system_miss_count": 2,
                        "failure_category_counts": {},
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
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            payload = _read_json(result.output_path)
            reviewer_ready = next(
                item
                for item in payload["forest_plan_results"]
                if item["expectation_id"] == "reviewer_ready"
            )
            self.assertTrue(reviewer_ready["passed"])
            self.assertTrue(reviewer_ready["actual"])
            self.assertTrue(
                result.summary["eval_lanes"]["forest_plan"][
                    "component_adjudication_reviewer_ready"
                ]
            )

    def test_v1_eval_rejects_current_adjudication_real_ea_omission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            summary = _read_json(review_dir / "forest_plan_context_summary.json")
            summary["reviewer_ready"] = False
            summary["component_evaluation"] = {
                "reviewer_ready": False,
                "all_applicable_standards_applied": True,
            }
            _write_json(review_dir / "forest_plan_context_summary.json", summary)
            _write_json(
                review_dir / "forest_plan_component_adjudication_eval.json",
                {
                    "schema_version": "forest-plan-component-adjudication-eval-v0",
                    "summary": {
                        "passed": True,
                        "pending_adjudication_count": 0,
                        "real_ea_omission_count": 1,
                        "system_miss_count": 0,
                        "failure_category_counts": {},
                    },
                    "item_results": [
                        {
                            "component_id": "component-standard",
                            "component_type": "standard",
                            "disposition": "project_record_omission",
                            "adjudication_outcome": "real_ea_omission",
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
            self.assertFalse(result.summary["forest_plan_passed"])
            self.assertEqual(
                result.summary["forest_plan_failure_category_counts"],
                {"forest_plan_reviewer_not_ready": 1},
            )
            payload = _read_json(result.output_path)
            reviewer_ready = next(
                item
                for item in payload["forest_plan_results"]
                if item["expectation_id"] == "reviewer_ready"
            )
            self.assertFalse(reviewer_ready["passed"])
            self.assertFalse(reviewer_ready["actual"])

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
