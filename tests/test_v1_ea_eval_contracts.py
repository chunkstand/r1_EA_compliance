from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.support.v1_ea_eval_fixtures import _read_json
from tests.support.v1_ea_eval_fixtures import _write_eval_contract
from tests.support.v1_ea_eval_fixtures import _write_json
from tests.support.v1_ea_eval_fixtures import _write_positive_review
from tests.support.v1_ea_eval_fixtures import _write_real_package_manifest
from tests.support.v1_ea_eval_repair_fixtures import _assert_repair_baseline_failure_summary
from tests.support.v1_ea_eval_repair_fixtures import _write_repair_baseline_eval_contract
from tests.support.v1_ea_eval_repair_fixtures import _write_repair_baseline_failure_review
from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.v1_ea_eval import run_v1_ea_review_eval


class V1EAReviewEvalContractTests(unittest.TestCase):
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
        self.assertIsNone(args.eval_file)

    def test_v1_eval_resolves_tracked_manifest_contract_from_review_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            manifest_path = _write_real_package_manifest(
                root,
                review_id="v1-unit",
                eval_file=eval_file,
            )

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                manifest_path=manifest_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.eval_file, eval_file)

    def test_v1_eval_requires_eval_file_or_tracked_review_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)

            with self.assertRaisesRegex(
                ValueError,
                "requires --eval-file or a tracked --review-id",
            ):
                run_v1_ea_review_eval(
                    output_dir=root / "source_library",
                    review_dir=review_dir,
                )
