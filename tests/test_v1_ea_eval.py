from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.support.v1_ea_eval_fixtures import _accepted_pending_policy
from tests.support.v1_ea_eval_fixtures import _compact_evidence_for_row
from tests.support.v1_ea_eval_fixtures import _finding
from tests.support.v1_ea_eval_fixtures import _matrix_row
from tests.support.v1_ea_eval_fixtures import _read_json
from tests.support.v1_ea_eval_fixtures import _summary_check
from tests.support.v1_ea_eval_fixtures import _write_eval_contract
from tests.support.v1_ea_eval_fixtures import _write_json
from tests.support.v1_ea_eval_fixtures import _write_jsonl
from tests.support.v1_ea_eval_fixtures import _write_positive_review
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

    def test_v1_eval_rerun_preserves_timestamp_when_payload_is_semantically_same(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            first = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )
            payload = _read_json(first.output_path)
            payload["summary"]["generated_at"] = "2000-01-01T00:00:00Z"
            _write_json(first.output_path, payload)
            pinned_text = first.output_path.read_text(encoding="utf-8")

            second = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertEqual(second.summary["generated_at"], "2000-01-01T00:00:00Z")
            self.assertEqual(second.output_path.read_text(encoding="utf-8"), pinned_text)

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

    def test_v1_eval_fails_when_authority_explanation_paths_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            (review_dir / "authority_explanation_paths.json").unlink()
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            check = _summary_check(result.summary, "authority_explanation_paths_ready")
            self.assertFalse(check["passed"])
            self.assertIn("review_artifact_missing", result.summary["failure_category_counts"])

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

        self.assertEqual(len(contract["conditional_source_expectations"]), 22)
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
