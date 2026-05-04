from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.v1_ea_eval import run_v1_ea_review_eval


class V1EAReviewEvalTests(unittest.TestCase):
    def test_v1_eval_scores_sections_sources_conditionals_and_forest_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["section_detection_rate"], 1.0)
            self.assertEqual(metrics["source_record_match_rate"], 1.0)
            self.assertEqual(metrics["conditional_false_negative_count"], 0)
            self.assertEqual(metrics["forest_plan_expectation_match_rate"], 1.0)
            self.assertTrue(result.summary["broader_ea_passed"])
            self.assertTrue(result.summary["forest_plan_passed"])
            self.assertFalse(result.summary["forest_plan_component_adjudication_required"])
            self.assertTrue(result.summary["eval_lanes"]["overall"]["passed"])
            self.assertTrue(result.summary["eval_lanes"]["broader_ea"]["passed"])
            self.assertTrue(result.summary["eval_lanes"]["forest_plan"]["passed"])
            self.assertEqual(result.summary["failed_rule_expectation_count"], 0)
            self.assertEqual(result.summary["failed_rule_ids"], [])
            self.assertEqual(result.summary["failed_rule_ids_by_category"], {})
            self.assertEqual(result.summary["failed_rule_expectations"], [])

    def test_v1_eval_accepts_generated_rule_pack_base_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            report = _read_json(review_dir / "compliance_review.json")
            generated_identity = {
                "rule_pack_id": "generated-nepa-ea-v0-v1-unit",
                "version": "applicability-v0",
                "base_rule_pack_id": "nepa-ea-v0",
                "base_rule_pack_version": "0.4.0",
            }
            report["rule_pack_id"] = generated_identity["rule_pack_id"]
            report["rule_pack_version"] = generated_identity["version"]
            report["base_rule_pack_id"] = generated_identity["base_rule_pack_id"]
            report["base_rule_pack_version"] = generated_identity["base_rule_pack_version"]
            report["rule_pack"] = generated_identity
            report["summary"]["rule_pack_id"] = generated_identity["rule_pack_id"]
            report["summary"]["rule_pack_version"] = generated_identity["version"]
            report["summary"]["base_rule_pack_id"] = generated_identity["base_rule_pack_id"]
            report["summary"]["base_rule_pack_version"] = generated_identity[
                "base_rule_pack_version"
            ]
            _write_json(review_dir / "compliance_review.json", report)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            identity_check = _summary_check(result.summary, "review_identity_matches_contract")
            self.assertTrue(identity_check["passed"])
            self.assertEqual(
                identity_check["details"]["review"]["base_rule_pack_id"],
                "nepa-ea-v0",
            )

    def test_v1_eval_uses_applicability_decision_for_missing_not_applicable_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"].append(
                {
                    "rule_id": "nepa_4336c_ce_adoption_screen",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The package is an EA, so the categorical-exclusion adoption row "
                        "should remain explicitly not applicable."
                    ),
                }
            )
            _write_json(eval_file, contract)
            _write_jsonl(
                review_dir / "applicability" / "applicability_decisions.jsonl",
                [
                    {
                        "schema_version": "applicability-decisions-v0",
                        "candidate_authority_id": (
                            "rule-template:nepa-ea-v0:0.4.0:"
                            "nepa_4336c_ce_adoption_screen"
                        ),
                        "rule_template": {"rule_id": "nepa_4336c_ce_adoption_screen"},
                        "status": "not_applicable",
                        "source_record_ids": ["R1EA-006"],
                        "authority_document_role": "law",
                        "negative_evidence_spans": [
                            {
                                "citation_label": "EA-PACKAGE-001",
                                "text_snippet": (
                                    "The proposal is not using a categorical exclusion."
                                ),
                            }
                        ],
                        "source_library_evidence_spans": [
                            {
                                "citation_label": "R1EA-006",
                                "source_record_id": "R1EA-006",
                                "text_excerpt": "42 U.S.C. 4336c",
                            }
                        ],
                    }
                ],
            )

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            output = _read_json(result.output_path)
            ce_result = next(
                item
                for item in output["conditional_results"]
                if item["rule_id"] == "nepa_4336c_ce_adoption_screen"
            )
            self.assertEqual(ce_result["actual_status"], "not_applicable")
            self.assertEqual(ce_result["actual_applicability"], "not_applicable")

    def test_v1_eval_bridges_missing_forest_plan_authority_row_from_component_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            report = _read_json(review_dir / "compliance_review.json")
            report["findings"] = [
                finding
                for finding in report["findings"]
                if finding["rule_id"] != "custer_gallatin_lmp_2022"
            ]
            _write_json(review_dir / "compliance_review.json", report)
            matrix = _read_json(review_dir / "compliance_matrix.json")
            matrix["rows"] = [
                row for row in matrix["rows"] if row["rule_id"] != "custer_gallatin_lmp_2022"
            ]
            matrix["summary"]["row_count"] = len(matrix["rows"])
            _write_json(review_dir / "compliance_matrix.json", matrix)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            output = _read_json(result.output_path)
            custer_rule = next(
                item
                for item in output["rule_results"]
                if item["rule_id"] == "custer_gallatin_lmp_2022"
            )
            self.assertTrue(custer_rule["present"])
            self.assertEqual(
                custer_rule["actual_source_record_ids"],
                ["R1PLAN-custer-gallatin-nf-02"],
            )

    def test_v1_eval_flags_conditional_false_negative_and_section_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_jsonl(
                review_dir / "package" / "package_chunks.jsonl",
                [
                    {
                        "chunk_id": "chunk-purpose",
                        "title": "EA",
                        "heading": "Purpose and Need",
                        "section": "Purpose and Need",
                        "text": "The purpose and need is documented.",
                    }
                ],
            )
            report = _read_json(review_dir / "compliance_review.json")
            report["findings"][1]["status"] = "not_applicable"
            report["findings"][1]["applicability_status"] = "not_applicable"
            report["findings"][1]["package_evidence"] = None
            report["findings"][1]["package_evidence_citation"] = None
            _write_json(review_dir / "compliance_review.json", report)
            matrix = _read_json(review_dir / "compliance_matrix.json")
            matrix["rows"][1]["status"] = "not_applicable"
            matrix["rows"][1]["applicability_status"] = "not_applicable"
            matrix["rows"][1]["ea_package_evidence"] = None
            matrix["rows"][1]["ea_package_citation"] = None
            matrix["rows"][1]["citation_requirements_met"] = False
            _write_json(review_dir / "compliance_matrix.json", matrix)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["conditional_false_negative"], 1)
            self.assertGreaterEqual(failures["ea_section_detection_miss"], 1)
            self.assertFalse(result.summary["broader_ea_passed"])
            self.assertTrue(result.summary["forest_plan_passed"])
            self.assertFalse(
                result.summary["eval_lanes"]["forest_plan"][
                    "component_adjudication_required"
                ]
            )
            self.assertEqual(result.summary["forest_plan_failure_category_counts"], {})
            self.assertIn(
                "conditional_false_negative",
                result.summary["broader_ea_failure_category_counts"],
            )
            self.assertEqual(result.summary["eval_lanes"]["forest_plan"]["failed_check_names"], [])
            self.assertIn(
                "conditional_source_expectations_met",
                result.summary["eval_lanes"]["broader_ea"]["failed_check_names"],
            )

    def test_v1_eval_enforces_source_alignment_for_adjudicate_when_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"][0]["expected_applicability"] = "adjudicate"
            contract["conditional_source_expectations"][0]["expected_source_record_ids"] = [
                "R1EA-does-not-match"
            ]
            contract["conditional_adjudication_policy"] = _accepted_pending_policy(
                ["esa_section_7"]
            )
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["source_record_mismatch"], 1)
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["conditional_actual_applicable_count"], 2)
            self.assertLess(metrics["conditional_actual_applicable_source_record_match_rate"], 1.0)

    def test_v1_eval_enforces_section_alignment_for_adjudicate_when_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["section_expectations"].extend(
                [
                    {
                        "section_id": "alternatives",
                        "label": "Alternatives",
                        "required": False,
                        "expected_terms": ["alternatives", "alternative"],
                    },
                    {
                        "section_id": "environmental_consequences",
                        "label": "Environmental Consequences",
                        "required": False,
                        "expected_terms": [
                            "environmental consequences",
                            "environmental effects",
                        ],
                    },
                    {
                        "section_id": "cultural_resources",
                        "label": "Cultural Resources",
                        "required": False,
                        "expected_terms": ["cultural resources"],
                    },
                ]
            )
            contract["conditional_source_expectations"].append(
                {
                    "rule_id": "nepa_4336b_programmatic_tiering",
                    "expected_applicability": "adjudicate",
                    "classification_rationale": (
                        "Programmatic tiering requires reviewer judgment while V1 "
                        "enforces source and section alignment."
                    ),
                    "expected_package_section_ids": [
                        "alternatives",
                        "environmental_consequences",
                    ],
                    "expected_source_record_ids": ["R1EA-005"],
                    "expected_source_document_roles": ["law"],
                }
            )
            contract["conditional_adjudication_policy"] = _accepted_pending_policy(
                ["nepa_4336b_programmatic_tiering"]
            )
            _write_json(eval_file, contract)
            report = _read_json(review_dir / "compliance_review.json")
            matrix = _read_json(review_dir / "compliance_matrix.json")
            bad_evidence = {
                "citation_label": "EA-PACKAGE-001 (abc123)",
                "source_record_id": "EA-PACKAGE-001",
                "title": "EA",
                "chunk_id": "chunk-biology",
                "evidence_span": {
                    "text": (
                        "Biological resources and cultural resources discuss "
                        "programmatic tiering."
                    ),
                },
                "provenance": {"section": "Biological Resources"},
            }
            finding = _finding(
                rule_id="nepa_4336b_programmatic_tiering",
                status="pass",
                applicability_mode="conditional",
                source_record_id="R1EA-005",
                document_role="law",
                package_text=bad_evidence["evidence_span"]["text"],
                package_section="Biological Resources",
            )
            finding["package_evidence"] = bad_evidence
            finding["applicability_evidence"] = bad_evidence
            report["findings"].append(finding)
            row = _matrix_row("v1-unit", finding)
            row["ea_package_evidence"] = _compact_evidence_for_row(bad_evidence)
            matrix["rows"].append(row)
            _write_json(review_dir / "compliance_review.json", report)
            _write_json(review_dir / "compliance_matrix.json", matrix)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["failure_category_counts"], {"rule_section_mismatch": 1})
            self.assertEqual(
                result.summary["failed_rule_ids_by_category"],
                {"rule_section_mismatch": ["nepa_4336b_programmatic_tiering"]},
            )
            output = _read_json(result.output_path)
            conditional_result = next(
                item
                for item in output["conditional_results"]
                if item["rule_id"] == "nepa_4336b_programmatic_tiering"
            )
            self.assertEqual(
                conditional_result["actual_package_section_ids"],
                ["biological_resources", "cultural_resources"],
            )

    def test_v1_eval_requires_pending_conditional_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"][0][
                "expected_applicability"
            ] = "adjudicate"
            _write_json(eval_file, contract)

            with self.assertRaisesRegex(ValueError, "conditional_adjudication_policy"):
                run_v1_ea_review_eval(
                    output_dir=root / "source_library",
                    review_id="v1-unit",
                    eval_file=eval_file,
                )

    def test_v1_eval_rejects_malformed_pending_conditional_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"][0][
                "expected_applicability"
            ] = "adjudicate"
            contract["conditional_adjudication_policy"] = _accepted_pending_policy(
                ["esa_section_7"]
            )
            contract["conditional_adjudication_policy"]["accepted_pending_rule_ids"] = None
            _write_json(eval_file, contract)

            with self.assertRaisesRegex(ValueError, "accepted_pending_rule_ids"):
                run_v1_ea_review_eval(
                    output_dir=root / "source_library",
                    review_id="v1-unit",
                    eval_file=eval_file,
                )

    def test_v1_eval_outputs_explicit_pending_conditional_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"][0][
                "expected_applicability"
            ] = "adjudicate"
            contract["conditional_adjudication_policy"] = _accepted_pending_policy(
                ["esa_section_7"]
            )
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            policy_summary = result.summary["conditional_adjudication"]
            self.assertTrue(policy_summary["passed"])
            self.assertEqual(policy_summary["policy_mode"], "accepted_pending_v1")
            self.assertEqual(policy_summary["actual_pending_count"], 1)
            self.assertEqual(policy_summary["actual_pending_rule_ids"], ["esa_section_7"])
            self.assertEqual(
                result.summary["metrics"]["conditional_adjudication_accepted_pending_count"],
                1,
            )
            policy_check = _summary_check(result.summary, "conditional_adjudication_policy_met")
            self.assertTrue(policy_check["passed"])
            output = _read_json(result.output_path)
            self.assertEqual(
                output["conditional_adjudication"]["pending_results"][0]["rule_id"],
                "esa_section_7",
            )
            self.assertTrue(
                output["conditional_adjudication"]["pending_results"][0][
                    "classification_rationale"
                ]
            )

    def test_v1_eval_flags_applicable_conditional_missing_from_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"] = [
                expectation
                for expectation in contract["conditional_source_expectations"]
                if expectation["rule_id"] != "esa_section_7"
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["conditional_expectation_missing"], 1)
            self.assertEqual(result.summary["metrics"]["conditional_expectation_missing_count"], 1)

    def test_real_v1_contract_declares_conditional_adjudication_policy(self) -> None:
        contract = _read_json(Path("config/v1_ecid_real_ea_eval.json"))
        adjudicate_rule_ids = sorted(
            expectation["rule_id"]
            for expectation in contract["conditional_source_expectations"]
            if expectation["expected_applicability"] == "adjudicate"
        )
        policy = contract["conditional_adjudication_policy"]

        self.assertEqual(len(contract["conditional_source_expectations"]), 18)
        self.assertEqual(len(adjudicate_rule_ids), 14)
        self.assertEqual(policy["mode"], "accepted_pending_v1")
        self.assertEqual(policy["accepted_pending_count"], 14)
        self.assertEqual(policy["accepted_pending_rule_ids"], adjudicate_rule_ids)
        self.assertTrue(policy["rationale"])
        self.assertTrue(
            all(
                expectation.get("classification_rationale")
                for expectation in contract["conditional_source_expectations"]
            )
        )

    def test_v1_eval_flags_missing_expected_baseline_source_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["baseline_policy"]["expected_source_record_ids"] = [
                "R1EA-013",
                "R1EA-baseline-missing",
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["baseline_source_record_missing"], 1)
            self.assertLess(result.summary["metrics"]["baseline_source_record_match_rate"], 1.0)

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

    def test_v1_eval_output_names_current_repair_baseline_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_repair_baseline_failure_review(review_dir)
            eval_file = _write_repair_baseline_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            _assert_repair_baseline_failure_summary(self, result.summary)

    def test_v1_eval_recovers_baseline_section_from_evidence_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_repair_baseline_failure_review(review_dir)
            purpose_text = (
                "Purpose and Need for Action\n\nThe environmental assessment explains "
                "the purpose and need for the proposed action."
            )
            report = _read_json(review_dir / "compliance_review.json")
            baseline_finding = next(
                finding
                for finding in report["findings"]
                if finding["rule_id"] == "nepa_statute_chapter_55"
            )
            baseline_finding["package_evidence"]["evidence_span"]["text"] = purpose_text
            baseline_finding["package_evidence"]["provenance"]["section"] = "Authority Summary"
            _write_json(review_dir / "compliance_review.json", report)
            matrix = _read_json(review_dir / "compliance_matrix.json")
            baseline_row = next(
                row
                for row in matrix["rows"]
                if row["rule_id"] == "nepa_statute_chapter_55"
            )
            baseline_row["ea_package_evidence"]["text"] = purpose_text
            baseline_row["ea_package_evidence"]["section"] = "Authority Summary"
            _write_json(review_dir / "compliance_matrix.json", matrix)
            eval_file = _write_repair_baseline_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            output = _read_json(result.output_path)
            baseline_result = next(
                rule_result
                for rule_result in output["rule_results"]
                if rule_result["rule_id"] == "nepa_statute_chapter_55"
            )
            self.assertTrue(baseline_result["section_match"])
            self.assertEqual(baseline_result["actual_package_section_ids"], ["purpose_need"])
            self.assertNotIn(
                "nepa_statute_chapter_55",
                result.summary["failed_rule_ids_by_category"].get(
                    "rule_section_mismatch",
                    [],
                ),
            )

    def test_cli_accepts_v1_ea_eval_command(self) -> None:
        args = build_parser().parse_args(
            [
                "v1-ea-eval",
                "--output-dir",
                "source_library",
                "--review-id",
                "v1-unit",
            ]
        )

        self.assertEqual(args.command, "v1-ea-eval")
        self.assertEqual(args.review_id, "v1-unit")


def _assert_repair_baseline_failure_summary(
    test_case: unittest.TestCase,
    summary: dict,
) -> None:
    expected_ids_by_category = {
        "conditional_false_positive": [
            "nepa_4336c_ce_adoption_screen",
            "usda_nepa_ce_fanec_7cfr_1b3",
            "usda_nepa_subcomponent_ce_7cfr_1b4",
        ],
        "rule_section_mismatch": [
            "nepa_4336b_programmatic_tiering",
            "nepa_statute_chapter_55",
        ],
    }
    test_case.assertEqual(
        summary["failure_category_counts"],
        {"conditional_false_positive": 3, "rule_section_mismatch": 2},
    )
    test_case.assertEqual(summary["failed_rule_expectation_count"], 5)
    test_case.assertEqual(
        summary["failed_rule_ids"],
        sorted(
            rule_id
            for rule_ids in expected_ids_by_category.values()
            for rule_id in rule_ids
        ),
    )
    test_case.assertEqual(summary["failed_rule_ids_by_category"], expected_ids_by_category)
    test_case.assertEqual(
        [
            (
                failure["expectation_type"],
                failure["rule_id"],
                failure["failure_categories"],
            )
            for failure in summary["failed_rule_expectations"]
        ],
        [
            (
                "rule_review_expectation",
                "nepa_statute_chapter_55",
                ["rule_section_mismatch"],
            ),
            (
                "conditional_source_expectation",
                "nepa_4336b_programmatic_tiering",
                ["rule_section_mismatch"],
            ),
            (
                "conditional_source_expectation",
                "nepa_4336c_ce_adoption_screen",
                ["conditional_false_positive"],
            ),
            (
                "conditional_source_expectation",
                "usda_nepa_ce_fanec_7cfr_1b3",
                ["conditional_false_positive"],
            ),
            (
                "conditional_source_expectation",
                "usda_nepa_subcomponent_ce_7cfr_1b4",
                ["conditional_false_positive"],
            ),
        ],
    )


def _summary_check(summary: dict, name: str) -> dict:
    return next(check for check in summary["checks"] if check["name"] == name)


def _accepted_pending_policy(rule_ids: list[str]) -> dict:
    return {
        "mode": "accepted_pending_v1",
        "accepted_pending_count": len(rule_ids),
        "accepted_pending_rule_ids": sorted(rule_ids),
        "rationale": (
            "Unit contract accepts these pending conditional rows while source and "
            "section alignment remain enforced."
        ),
    }


def _write_repair_baseline_failure_review(review_dir: Path) -> None:
    _write_jsonl(
        review_dir / "package" / "package_chunks.jsonl",
        [
            {
                "chunk_id": "chunk-purpose",
                "title": "EA",
                "heading": "Purpose and Need",
                "section": "Purpose and Need",
                "text": "The purpose and need section is present in the package.",
            },
            {
                "chunk_id": "chunk-alternatives",
                "title": "EA",
                "heading": "Alternatives",
                "section": "Alternatives",
                "text": "Alternatives are described for the proposed action.",
            },
            {
                "chunk_id": "chunk-effects",
                "title": "EA",
                "heading": "Environmental Consequences",
                "section": "Environmental Consequences",
                "text": "Environmental consequences are disclosed.",
            },
            {
                "chunk_id": "chunk-biology",
                "title": "EA",
                "heading": "Biological Resources",
                "section": "Biological Resources",
                "text": "Biological resources are discussed.",
            },
            {
                "chunk_id": "chunk-cultural",
                "title": "EA",
                "heading": "Cultural Resources",
                "section": "Cultural Resources",
                "text": "Cultural resources are discussed.",
            },
        ],
    )
    findings = [
        _finding(
            rule_id="nepa_statute_chapter_55",
            status="pass",
            applicability_mode="baseline",
            source_record_id="R1EA-001",
            document_role="law",
            package_text="National Environmental Policy Act chapter 55 authority applies.",
            package_section="Authority Summary",
        ),
        _finding(
            rule_id="nepa_4336b_programmatic_tiering",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-005",
            document_role="law",
            package_text=(
                "Programmatic analysis appears in biological resources and cultural resources."
            ),
            package_section="Biological Resources and Cultural Resources",
        ),
        _finding(
            rule_id="nepa_4336c_ce_adoption_screen",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-006",
            document_role="law",
            package_text="The EA mentions categorical exclusions and a FONSI.",
            package_section="Decision and FONSI",
        ),
        _finding(
            rule_id="usda_nepa_ce_fanec_7cfr_1b3",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-011",
            document_role="regulation",
            package_text="The EA mentions FANEC and extraordinary circumstances.",
            package_section="Decision and FONSI",
        ),
        _finding(
            rule_id="usda_nepa_subcomponent_ce_7cfr_1b4",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-012",
            document_role="regulation",
            package_text="The EA mentions categorical exclusions and level of review.",
            package_section="Decision and FONSI",
        ),
    ]
    _write_json(
        review_dir / "compliance_review.json",
        {
            "schema_version": "compliance-review-v0",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "summary": {
                "review_id": "v1-unit",
                "source_set_id": "source-set-test",
                "rule_pack_id": "nepa-ea-v0",
                "rule_pack_version": "0.4.0",
                "reviewer_ready": False,
            },
            "findings": findings,
        },
    )
    _write_json(
        review_dir / "compliance_matrix.json",
        {
            "schema_version": "compliance-matrix-v0",
            "summary": {"row_count": len(findings)},
            "rows": [_matrix_row("v1-unit", finding) for finding in findings],
        },
    )
    _write_json(
        review_dir / "compliance_validation.json",
        {"schema_version": "compliance-validation-v0", "passed": True, "checks": []},
    )


def _write_repair_baseline_eval_contract(root: Path, *, review_id: str) -> Path:
    path = root / "v1_repair_baseline_eval.json"
    _write_json(
        path,
        {
            "schema_version": "v1-ea-real-review-eval-contract-v0",
            "eval_id": "v1-repair-baseline",
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "allow_unadjudicated_conditional_expectations": True,
            "conditional_adjudication_policy": _accepted_pending_policy(
                ["nepa_4336b_programmatic_tiering"]
            ),
            "baseline_policy": {
                "require_source_record_match_authority": True,
                "expected_source_record_ids": ["R1EA-001"],
            },
            "section_expectations": [
                {
                    "section_id": "purpose_need",
                    "label": "Purpose and Need",
                    "required": True,
                    "expected_terms": ["purpose and need"],
                },
                {
                    "section_id": "alternatives",
                    "label": "Alternatives",
                    "required": True,
                    "expected_terms": ["alternatives"],
                },
                {
                    "section_id": "environmental_consequences",
                    "label": "Environmental Consequences",
                    "required": True,
                    "expected_terms": ["environmental consequences"],
                },
                {
                    "section_id": "biological_resources",
                    "label": "Biological Resources",
                    "required": True,
                    "expected_terms": ["biological resources"],
                },
                {
                    "section_id": "cultural_resources",
                    "label": "Cultural Resources",
                    "required": True,
                    "expected_terms": ["cultural resources"],
                },
            ],
            "rule_review_expectations": [
                {
                    "rule_id": "nepa_statute_chapter_55",
                    "expected_package_section_ids": ["purpose_need"],
                    "expected_source_record_ids": ["R1EA-001"],
                    "expected_source_document_roles": ["law"],
                }
            ],
            "conditional_source_expectations": [
                {
                    "rule_id": "nepa_4336b_programmatic_tiering",
                    "expected_applicability": "adjudicate",
                    "classification_rationale": (
                        "Programmatic tiering remains a reviewer judgment item in "
                        "the repair baseline."
                    ),
                    "expected_package_section_ids": [
                        "alternatives",
                        "environmental_consequences",
                    ],
                    "expected_source_record_ids": ["R1EA-005"],
                    "expected_source_document_roles": ["law"],
                },
                {
                    "rule_id": "nepa_4336c_ce_adoption_screen",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The repair baseline package is an EA context, not an "
                        "adopted categorical-exclusion path."
                    ),
                },
                {
                    "rule_id": "usda_nepa_ce_fanec_7cfr_1b3",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The repair baseline does not rely on a USDA categorical "
                        "exclusion or FANEC path."
                    ),
                },
                {
                    "rule_id": "usda_nepa_subcomponent_ce_7cfr_1b4",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The repair baseline does not use subcomponent categorical "
                        "exclusion screening."
                    ),
                },
            ],
        },
    )
    return path


def _write_positive_review(review_dir: Path) -> None:
    _write_jsonl(
        review_dir / "package" / "package_chunks.jsonl",
        [
            {
                "chunk_id": "chunk-purpose",
                "title": "EA",
                "heading": "Purpose and Need",
                "section": "Purpose and Need",
                "text": "The purpose and need explains the proposed action.",
            },
            {
                "chunk_id": "chunk-forest-plan",
                "title": "EA",
                "heading": "Forest Plan Consistency",
                "section": "Forest Plan Consistency",
                "text": (
                    "The Custer Gallatin National Forest 2022 Land Management Plan applies "
                    "in the Crazy Mountains Backcountry Area."
                ),
            },
            {
                "chunk_id": "chunk-biology",
                "title": "EA",
                "heading": "Biological Resources",
                "section": "Biological Resources",
                "text": (
                    "Endangered Species Act Section 7 consultation and a biological "
                    "assessment are discussed."
                ),
            },
        ],
    )
    findings = [
        _finding(
            rule_id="usda_nepa_ea_7cfr_1b5",
            status="pass",
            applicability_mode="baseline",
            source_record_id="R1EA-013",
            document_role="regulation",
            package_text="The purpose and need explains the proposed action.",
            package_section="Purpose and Need",
        ),
        _finding(
            rule_id="esa_section_7",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-065",
            document_role="law",
            package_text=(
                "Endangered Species Act Section 7 consultation and a biological assessment "
                "are discussed."
            ),
            package_section="Biological Resources",
        ),
        _finding(
            rule_id="custer_gallatin_lmp_2022",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1PLAN-custer-gallatin-nf-02",
            document_role="forest_plan",
            package_text=(
                "The Custer Gallatin National Forest 2022 Land Management Plan applies "
                "in the Crazy Mountains Backcountry Area."
            ),
            package_section="Forest Plan Consistency",
        ),
    ]
    _write_json(
        review_dir / "compliance_review.json",
        {
            "schema_version": "compliance-review-v0",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "summary": {
                "review_id": "v1-unit",
                "source_set_id": "source-set-test",
                "rule_pack_id": "nepa-ea-v0",
                "rule_pack_version": "0.4.0",
                "reviewer_ready": True,
            },
            "findings": findings,
        },
    )
    _write_json(
        review_dir / "compliance_matrix.json",
        {
            "schema_version": "compliance-matrix-v0",
            "summary": {
                "row_count": len(findings),
                "forest_plan_compliance_row_count": 1,
                "forest_plan_compliance_applicable_standard_row_count": 1,
            },
            "rows": [_matrix_row("v1-unit", finding) for finding in findings],
            "forest_plan_compliance": {
                "schema_version": "forest-plan-compliance-matrix-v0",
                "summary": {
                    "row_count": 1,
                    "applicable_standard_row_count": 1,
                    "compliance_status_counts": {"complies": 1},
                    "load_errors": [],
                },
                "rows": [
                    {
                        "row_id": (
                            "forest-plan-matrix:v1-unit:"
                            "cg-lmp-2022-cmbca-std-01"
                        ),
                        "component_id": "cg-lmp-2022-cmbca-std-01",
                        "component_type": "standard",
                        "applicability_status": "applicable",
                        "compliance_status": "complies",
                        "finding_status": "supported",
                    }
                ],
            },
        },
    )
    _write_json(
        review_dir / "compliance_validation.json",
        {"schema_version": "compliance-validation-v0", "passed": True, "checks": []},
    )
    _write_json(
        review_dir / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "scope_status": "custer_gallatin",
            "reviewer_ready": True,
            "component_evaluation": {"all_applicable_standards_applied": True},
        },
    )
    _write_json(
        review_dir / "forest_plan_context.json",
        {
            "schema_version": "forest-plan-context-v0",
            "scope_status": "custer_gallatin",
            "source_record_readiness": {
                "required_source_record_ids": [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ]
            },
            "geographic_areas": [{"entry_id": "geo-bridger-bangtail-crazy"}],
            "management_areas": [{"entry_id": "mgmt-crazy-mountains-bca"}],
        },
    )
    _write_json(
        review_dir / "forest_plan_component_findings.json",
        {
            "schema_version": "forest-plan-component-findings-v0",
            "summary": {"all_applicable_standards_applied": True},
            "findings": [
                {"component_id": "cg-lmp-2022-cmbca-dc-01", "component_type": "desired_condition"},
                {
                    "component_id": "cg-lmp-2022-cmbca-std-01",
                    "component_type": "standard",
                    "applicability_status": "applicable",
                },
                {"component_id": "cg-lmp-2022-cmbca-suit-01", "component_type": "suitability"},
            ],
        },
    )
    _write_json(
        review_dir / "forest_plan_applicable_standard_coverage.json",
        {
            "schema_version": "forest-plan-applicable-standard-coverage-v0",
            "standards": [
                {
                    "standard_id": "cg-lmp-2022-cmbca-std-01",
                    "applicability_status": "applicable",
                    "standard_applied": True,
                }
            ],
        },
    )
    _write_json(
        review_dir / "forest_plan_reviewer_resolution_queue.json",
        {"schema_version": "forest-plan-reviewer-resolution-queue-v0", "summary": {"item_count": 0}},
    )


def _write_eval_contract(root: Path, *, review_id: str) -> Path:
    path = root / "v1_eval.json"
    _write_json(
        path,
        {
            "schema_version": "v1-ea-real-review-eval-contract-v0",
            "eval_id": "v1-unit-eval",
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "allow_unadjudicated_conditional_expectations": True,
            "baseline_policy": {
                "require_source_record_match_authority": True,
                "expected_source_record_ids": ["R1EA-013"],
            },
            "section_expectations": [
                {
                    "section_id": "purpose_need",
                    "label": "Purpose and Need",
                    "required": True,
                    "expected_terms": ["purpose and need"],
                },
                {
                    "section_id": "forest_plan_consistency",
                    "label": "Forest Plan Consistency",
                    "required": True,
                    "expected_terms": ["Land Management Plan", "Crazy Mountains Backcountry Area"],
                },
                {
                    "section_id": "biological_resources",
                    "label": "Biological Resources",
                    "required": True,
                    "expected_terms": ["Endangered Species Act", "biological assessment"],
                },
            ],
            "rule_review_expectations": [
                {
                    "rule_id": "usda_nepa_ea_7cfr_1b5",
                    "expected_package_section_ids": ["purpose_need"],
                    "expected_source_record_ids": ["R1EA-013"],
                    "expected_source_document_roles": ["regulation"],
                },
                {
                    "rule_id": "esa_section_7",
                    "expected_package_section_ids": ["biological_resources"],
                    "expected_source_record_ids": ["R1EA-065"],
                    "expected_source_document_roles": ["law"],
                },
                {
                    "rule_id": "custer_gallatin_lmp_2022",
                    "expected_package_section_ids": ["forest_plan_consistency"],
                    "expected_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
                    "expected_source_document_roles": ["forest_plan"],
                },
            ],
            "conditional_source_expectations": [
                {
                    "rule_id": "esa_section_7",
                    "expected_applicability": "applicable",
                    "expected_package_section_ids": ["biological_resources"],
                    "expected_source_record_ids": ["R1EA-065"],
                    "expected_source_document_roles": ["law"],
                    "trigger_terms": ["Endangered Species Act", "biological assessment"],
                    "classification_rationale": (
                        "The package contains biological assessment evidence, so "
                        "the ESA Section 7 row is applicable in this unit fixture."
                    ),
                },
                {
                    "rule_id": "custer_gallatin_lmp_2022",
                    "expected_applicability": "applicable",
                    "expected_package_section_ids": ["forest_plan_consistency"],
                    "expected_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
                    "expected_source_document_roles": ["forest_plan"],
                    "trigger_terms": ["Custer Gallatin", "Land Management Plan"],
                    "classification_rationale": (
                        "The package resolves to the Custer Gallatin Land "
                        "Management Plan in this unit fixture."
                    ),
                },
            ],
            "forest_plan": {
                "expected_scope_status": "custer_gallatin",
                "required_source_record_ids": [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ],
                "expected_geographic_area_ids": ["geo-bridger-bangtail-crazy"],
                "expected_management_area_ids": ["mgmt-crazy-mountains-bca"],
                "expected_component_ids": [
                    "cg-lmp-2022-cmbca-dc-01",
                    "cg-lmp-2022-cmbca-std-01",
                    "cg-lmp-2022-cmbca-suit-01",
                ],
                "expected_applicable_standard_ids": ["cg-lmp-2022-cmbca-std-01"],
                "min_applicable_standard_count": 1,
                "require_all_applicable_standards_applied": True,
                "require_reviewer_ready": True,
                "max_reviewer_resolution_items": 0,
            },
        },
    )
    return path


def _finding(
    *,
    rule_id: str,
    status: str,
    applicability_mode: str,
    source_record_id: str,
    document_role: str,
    package_text: str,
    package_section: str,
) -> dict:
    return {
        "rule_id": rule_id,
        "title": rule_id,
        "status": status,
        "claim_type": "supported_compliance_finding",
        "applicability_status": "applicable" if status != "not_applicable" else "not_applicable",
        "applicability_mode": applicability_mode,
        "authority_source_record_id": source_record_id,
        "authority_document_role": document_role,
        "package_evidence_citation": f"package:{rule_id}",
        "source_library_evidence_citation": f"source:{source_record_id}",
        "package_evidence": {
            "citation_label": f"package:{rule_id}",
            "title": "EA",
            "evidence_span": {"text": package_text},
            "provenance": {"section": package_section},
        },
        "source_library_evidence": {
            "citation_label": f"source:{source_record_id}",
            "source_record_id": source_record_id,
            "document_role": document_role,
            "title": source_record_id,
            "evidence_span": {"text": rule_id},
            "provenance": {"section": "Authority"},
        },
        "source_claim_links": [
            {
                "claim_id": f"claim:{rule_id}",
                "source_record_id": source_record_id,
                "document_role": document_role,
            }
        ],
    }


def _matrix_row(review_id: str, finding: dict) -> dict:
    return {
        "row_id": f"matrix:{review_id}:{finding['rule_id']}",
        "rule_id": finding["rule_id"],
        "status": finding["status"],
        "applicability_status": finding["applicability_status"],
        "applicability_mode": finding["applicability_mode"],
        "authority_source_record_id": finding["authority_source_record_id"],
        "authority_document_role": finding["authority_document_role"],
        "ea_package_citation": finding["package_evidence_citation"],
        "ea_package_evidence": {
            "citation_label": finding["package_evidence_citation"],
            "text": finding["package_evidence"]["evidence_span"]["text"],
            "section": finding["package_evidence"]["provenance"]["section"],
        },
        "source_library_citation": finding["source_library_evidence_citation"],
        "source_library_evidence": {
            "citation_label": finding["source_library_evidence_citation"],
            "source_record_id": finding["authority_source_record_id"],
            "title": finding["authority_source_record_id"],
            "text": finding["rule_id"],
        },
        "applied_source_record_ids": [finding["authority_source_record_id"]],
        "applied_source_document_roles": [finding["authority_document_role"]],
        "citation_requirements_met": True,
    }


def _compact_evidence_for_row(evidence: dict) -> dict:
    return {
        "citation_label": evidence["citation_label"],
        "source_record_id": evidence.get("source_record_id"),
        "title": evidence.get("title"),
        "chunk_id": evidence.get("chunk_id"),
        "text": evidence["evidence_span"]["text"],
        "section": evidence["provenance"].get("section"),
    }


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
