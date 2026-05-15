from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_review_eval import _normalized_eval_findings_by_rule
from usfs_r1_ea_sources.compliance_review_eval import (
    _validate_compliance_review_eval_cases_against_rule_pack,
)
from usfs_r1_ea_sources.compliance_review_eval import run_compliance_review_eval

from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _rule_pack,
    _write_compliance_eval_file,
    _write_rule_pack,
)


class ComplianceReviewEvalTests(unittest.TestCase):
    def test_compliance_review_eval_scores_package_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "unit-all-pass",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access "
                            "and mitigation measures support a finding of no significant impact."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                        "expected_unsupported_finding_ids": [],
                        "expected_source_record_ids": {
                            "purpose_need": ["R1EA-001"],
                            "mitigation": ["R1EA-002"],
                        },
                        "expected_source_document_roles": {
                            "purpose_need": ["regulation"],
                            "mitigation": ["regulation"],
                        },
                        "min_findings": 2,
                    },
                    {
                        "id": "unit-package-gap",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_finding_status_counts": {"gap": 1, "pass": 1},
                        "expected_unsupported_finding_ids": [],
                        "expected_source_record_ids": {
                            "purpose_need": ["R1EA-001"],
                            "mitigation": ["R1EA-002"],
                        },
                        "min_findings": 2,
                    },
                ],
            )

            result = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=Path(tmp) / "eval-results",
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["case_count"], 2)
            self.assertEqual(result.summary["passed_count"], 2)
            self.assertEqual(result.summary["metrics"]["pass_rate"], 1.0)
            cases = {case["id"]: case for case in result.summary["cases"]}
            self.assertEqual(
                cases["unit-all-pass"]["actual_statuses"],
                {"mitigation": "pass", "purpose_need": "pass"},
            )
            self.assertEqual(
                cases["unit-package-gap"]["actual_statuses"],
                {"mitigation": "gap", "purpose_need": "pass"},
            )
            self.assertTrue(cases["unit-package-gap"]["citation_coverage_supported"])
            self.assertTrue(cases["unit-package-gap"]["graph_coverage_supported"])
            self.assertTrue(cases["unit-all-pass"]["expected_source_record_ids_match"])
            self.assertTrue(cases["unit-all-pass"]["expected_source_document_roles_match"])
            self.assertEqual(cases["unit-all-pass"]["source_record_mismatches"], [])
            self.assertTrue(Path(cases["unit-all-pass"]["compliance_matrix_path"]).exists())
            self.assertTrue(Path(cases["unit-all-pass"]["compliance_matrix_pdf_path"]).exists())
            self.assertEqual(result.summary["failure_category_counts"], {})

    def test_compliance_review_eval_rejects_bad_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "bad-filter",
                        "package_text": "Purpose and Need",
                        "filters": {"rule_ids": "purpose_need"},
                        "expected_statuses": {"purpose_need": "pass"},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "invalid filters"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_rejects_invalid_expected_source_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "bad-source-list",
                        "package_text": "Purpose and Need",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_source_record_ids": {"purpose_need": []},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "non-empty lists"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    rule_pack_path=rule_pack_path,
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_requires_full_rule_pack_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "partial-expectations",
                        "package_text": "Purpose and Need",
                        "expected_statuses": {"purpose_need": "pass"},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "cover every rule"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    rule_pack_path=rule_pack_path,
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_normalizes_missing_generated_rules_as_not_applicable(
        self,
    ) -> None:
        findings_by_rule = {
            "purpose_need": {
                "rule_id": "purpose_need",
                "status": "pass",
                "claim_type": "supported_compliance_finding",
            }
        }
        expected_statuses = {
            "purpose_need": "pass",
            "mitigation": "not_applicable",
        }

        normalized = _normalized_eval_findings_by_rule(
            findings_by_rule=findings_by_rule,
            expected_statuses=expected_statuses,
            generated_rule_pack_case=True,
        )

        self.assertEqual(normalized["purpose_need"]["status"], "pass")
        self.assertEqual(normalized["mitigation"]["status"], "not_applicable")
        self.assertEqual(normalized["mitigation"]["claim_type"], "no_compliance_claim")
        self.assertEqual(normalized["mitigation"]["source_claim_link_count"], 0)

        unchanged = _normalized_eval_findings_by_rule(
            findings_by_rule=findings_by_rule,
            expected_statuses=expected_statuses,
            generated_rule_pack_case=False,
        )
        self.assertNotIn("mitigation", unchanged)

    def test_compliance_review_eval_allows_generated_rule_pack_status_counts(self) -> None:
        case = {
            "id": "generated-case",
            "package_text": "Purpose and Need",
            "hard_negative_package": True,
            "min_findings": 1,
            "expected_statuses": {
                "purpose_need": "gap",
                "mitigation": "not_applicable",
            },
            "expected_finding_status_counts": {
                "gap": 1,
            },
        }

        _validate_compliance_review_eval_cases_against_rule_pack([case], _rule_pack())

    def test_compliance_review_eval_rejects_status_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "bad-status-count",
                        "package_text": "Purpose and Need",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "expected_finding_status_counts"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    rule_pack_path=rule_pack_path,
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_flags_false_pass_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "false-pass",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                        "expected_unsupported_finding_ids": [],
                        "min_findings": 2,
                    }
                ],
            )

            result = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=Path(tmp) / "eval-results",
            )

            self.assertFalse(result.summary["passed"])
            case = result.summary["cases"][0]
            self.assertFalse(case["expected_statuses_match"])
            self.assertFalse(case["expected_claim_types_match"])
            self.assertFalse(case["expected_package_evidence_match"])
            self.assertIn("expected_statuses_match", case["failure_reasons"])
            self.assertEqual(case["actual_statuses"]["mitigation"], "gap")
            categories = {item["category"] for item in case["failure_taxonomy"]}
            self.assertIn("rule_wording_issue", categories)
            self.assertIn("package_evidence_search_miss", categories)
            self.assertEqual(
                result.summary["failure_category_counts"]["rule_wording_issue"],
                1,
            )

    def test_compliance_review_eval_replaces_stale_case_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = Path(tmp) / "compliance-eval.json"
            results_dir = Path(tmp) / "eval-results"
            _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "stable-case",
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
                path=eval_path,
            )
            first = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=results_dir,
            )
            self.assertTrue(first.summary["passed"])
            self.assertEqual(first.summary["cases"][0]["actual_statuses"]["mitigation"], "pass")

            _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "stable-case",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_finding_status_counts": {"gap": 1, "pass": 1},
                    }
                ],
                path=eval_path,
            )

            second = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=results_dir,
            )

            self.assertTrue(second.summary["passed"])
            self.assertEqual(second.summary["cases"][0]["actual_statuses"]["mitigation"], "gap")
