from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_coverage import _load_eval_cases
from usfs_r1_ea_sources.compliance_coverage import run_compliance_coverage
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links

from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _check,
    _write_compliance_eval_file,
    _write_coverage_matrix,
    _write_rule_pack,
)


class ComplianceCoverageTests(unittest.TestCase):
    def test_compliance_coverage_scores_matrix_links_and_eval_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
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
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access "
                            "and mitigation measures support a finding of no significant impact."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                    }
                ],
            )
            coverage_path = _write_coverage_matrix(Path(tmp))

            result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=coverage_path,
                eval_file=eval_path,
                links_path=link_result.links_path,
                results_dir=Path(tmp) / "coverage-results",
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["rule_count"], 2)
            self.assertEqual(result.summary["coverage_item_count"], 2)
            self.assertGreaterEqual(result.summary["rule_claim_link_count"], 2)
            self.assertEqual(result.summary["rules_without_coverage_items"], [])
            self.assertEqual(result.summary["rules_without_eval_cases"], [])
            self.assertEqual(result.summary["rules_without_source_claim_links"], [])
            self.assertEqual(result.summary["source_claim_term_mismatch_rule_ids"], [])

    def test_compliance_coverage_loads_contract_object_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "compliance-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "compliance-review-eval-v1",
                        "eval_id": "coverage-contract-unit",
                        "coverage_requirements": {},
                        "metric_thresholds": {},
                        "cases": [
                            {
                                "id": "coverage-case",
                                "package_text": "Purpose and Need",
                                "expected_statuses": {
                                    "purpose_need": "pass",
                                    "mitigation": "gap",
                                },
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            cases = _load_eval_cases(eval_path)

            self.assertEqual(len(cases), 1)
            self.assertEqual(cases[0]["id"], "coverage-case")
            self.assertEqual(cases[0]["expected_statuses"]["purpose_need"], "pass")

    def test_compliance_coverage_reports_missing_rule_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
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
                        "package_text": "Purpose and Need",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                    }
                ],
            )
            coverage_path = _write_coverage_matrix(Path(tmp), rule_ids=["purpose_need"])

            result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=coverage_path,
                eval_file=eval_path,
                links_path=link_result.links_path,
                results_dir=Path(tmp) / "coverage-results",
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["rules_without_coverage_items"], ["mitigation"])
            self.assertFalse(_check(result.summary, "coverage_matrix_covers_every_rule")["passed"])

    def test_compliance_coverage_reports_source_claim_term_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
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
            coverage_path = _write_coverage_matrix(Path(tmp))
            matrix = json.loads(coverage_path.read_text(encoding="utf-8"))
            for item in matrix["coverage_items"]:
                if item["rule_id"] == "mitigation":
                    item["source_claim_terms"] = ["never present term"]
            coverage_path.write_text(json.dumps(matrix, sort_keys=True), encoding="utf-8")

            result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=coverage_path,
                eval_file=eval_path,
                links_path=link_result.links_path,
                results_dir=Path(tmp) / "coverage-results",
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["source_claim_term_mismatch_rule_ids"], ["mitigation"])
            self.assertFalse(
                _check(
                    result.summary,
                    "coverage_matrix_source_claim_terms_match_rule_claim_links",
                )["passed"]
            )

    def test_compliance_coverage_reports_malformed_matrix_items_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
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
            coverage_path = _write_coverage_matrix(Path(tmp))
            matrix = json.loads(coverage_path.read_text(encoding="utf-8"))
            matrix["coverage_items"].append("not an object")
            matrix["coverage_items"][1]["source_claim_terms"] = "mitigation"
            coverage_path.write_text(json.dumps(matrix, sort_keys=True), encoding="utf-8")

            result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=coverage_path,
                eval_file=eval_path,
                links_path=link_result.links_path,
                results_dir=Path(tmp) / "coverage-results",
            )

            self.assertFalse(result.summary["passed"])
            required_fields_check = _check(
                result.summary,
                "coverage_matrix_items_have_required_fields",
            )
            self.assertFalse(required_fields_check["passed"])
            reasons = {failure["reason"] for failure in required_fields_check["details"]["failures"]}
            self.assertIn("coverage_item_must_be_object", reasons)
            self.assertIn("invalid_field_shape", reasons)
