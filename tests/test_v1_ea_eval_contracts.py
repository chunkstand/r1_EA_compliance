from __future__ import annotations

import json
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


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_ECID_CONTRACT = REPO_ROOT / "config" / "v1_ecid_real_ea_eval.json"
COMMITTED_SOUTH_PLATEAU_CONTRACT = REPO_ROOT / "config" / "v1_south_plateau_real_ea_eval.json"
COMMITTED_WEST_RESERVOIR_CONTRACT = REPO_ROOT / "config" / "v1_west_reservoir_real_ea_eval.json"


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

    def test_committed_west_reservoir_contract_declares_typed_blocked_quarantine(self) -> None:
        contract = json.loads(COMMITTED_WEST_RESERVOIR_CONTRACT.read_text(encoding="utf-8"))

        self.assertEqual(contract["review_id"], "west-reservoir-67436")
        self.assertEqual(contract["expected_lane_states"], {
            "broader_ea_passed": False,
            "forest_plan_passed": False,
        })
        self.assertEqual(
            sorted(contract["allowed_blocker_categories"]),
            [
                "forest_plan_matrix_miss",
                "forest_plan_reviewer_not_ready",
                "forest_plan_scope_miss",
                "review_artifact_missing",
            ],
        )
        self.assertEqual(contract["package_style_tags"], ["live_external_noisy"])
        self.assertTrue(
            contract["conditional_source_expectations"],
            "expected conditional source expectations to remain present",
        )
        for entry in contract["conditional_source_expectations"]:
            self.assertIn(
                "typed-blocked replay quarantine",
                entry["classification_rationale"],
            )
            self.assertNotIn("reviewer-ready contract", entry["classification_rationale"])

    def test_committed_reviewer_ready_contracts_bind_to_scoped_alignment_source_set(self) -> None:
        ecid = json.loads(COMMITTED_ECID_CONTRACT.read_text(encoding="utf-8"))
        south = json.loads(COMMITTED_SOUTH_PLATEAU_CONTRACT.read_text(encoding="utf-8"))

        self.assertEqual(ecid["review_id"], "v1-cg-ecid-compliance-review")
        self.assertEqual(
            ecid["source_set_id"],
            "source-set-f70ea11e04ae3d53",
        )
        self.assertEqual(
            south["review_id"],
            "region1-expansion-south-plateau-landscape-treatment",
        )
        self.assertEqual(
            south["source_set_id"],
            "source-set-f70ea11e04ae3d53",
        )
