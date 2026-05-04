from __future__ import annotations

from pathlib import Path
import copy
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_eval import run_applicability_eval
from usfs_r1_ea_sources.applicability_eval import run_applicability_gold_eval
from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_SEED = REPO_ROOT / "config" / "applicability_eval_seed.json"
GOLD_SEED = REPO_ROOT / "config" / "applicability_gold_eval_v0.json"
RULE_PACK = REPO_ROOT / "config" / "compliance_rule_pack_nepa_ea_v0.json"


class ApplicabilityEvalTests(unittest.TestCase):
    def test_applicability_eval_scores_decisions_and_generated_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"

            result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["case_count"], 2)
            self.assertEqual(result.summary["generated_rule_pack_ready_case_count"], 2)
            mixed = _case(result.summary, "seed-mixed-applicability")
            self.assertEqual(
                mixed["actual_statuses"]["usda_nepa_ce_fanec_7cfr_1b3"],
                "not_applicable",
            )
            self.assertEqual(
                mixed["generated_rule_ids"],
                ["esa_section_7", "nepa_statute_chapter_55"],
            )
            self.assertTrue(mixed["non_applicable_coverage_supported"])

    def test_cli_runs_applicability_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exit_code = main(
                [
                    "applicability-eval",
                    "--output-dir",
                    str(Path(tmp) / "source_library"),
                    "--base-rule-pack",
                    str(RULE_PACK),
                    "--eval-file",
                    str(EVAL_SEED),
                ]
            )

            self.assertEqual(exit_code, 0)

    def test_applicability_eval_fails_on_false_negative_expectation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            eval_path = root / "bad-applicability-eval.json"
            payload = json.loads(EVAL_SEED.read_text(encoding="utf-8"))
            payload = copy.deepcopy(payload)
            payload["cases"] = [payload["cases"][1]]
            payload["cases"][0]["expected_statuses"]["esa_section_7"] = "applicable"
            eval_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=eval_path,
                base_rule_pack_path=RULE_PACK,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["failure_category_counts"],
                {"applicability_status_mismatch": 1},
            )
            failed = result.summary["cases"][0]
            self.assertEqual(
                failed["status_mismatches"],
                [
                    {
                        "rule_id": "esa_section_7",
                        "expected": "applicable",
                        "actual": "not_applicable",
                    }
                ],
            )

    def test_applicability_gold_eval_promotes_only_passing_adjudicated_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"

            result = run_applicability_gold_eval(
                output_dir=output_dir,
                gold_file=GOLD_SEED,
                base_rule_pack_path=RULE_PACK,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.summary["promotion_ready"])
            self.assertEqual(result.summary["case_count"], 3)
            self.assertEqual(
                sorted(result.summary["profile_counts"]),
                ["mixed", "negative", "positive"],
            )

    def test_phase_eval_reports_applicability_gates_and_fails_closed_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )
            case = _case(eval_result.summary, "seed-mixed-applicability")

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=case["source_set_id"],
                review_id=case["review_id"],
            )

            generated_phase = _phase(phase_result.summary, "generated_rule_pack")
            self.assertTrue(generated_phase["passed"])
            self.assertTrue(generated_phase["reviewer_ready"])
            determination_phase = _phase(phase_result.summary, "applicability_determination")
            self.assertTrue(determination_phase["passed"])
            self.assertFalse(determination_phase["details"]["non_applicable_coverage_gaps"])

            validation_path = (
                output_dir
                / "reviews"
                / case["review_id"]
                / "applicability"
                / "applicability_validation.json"
            )
            validation_path.unlink()
            failed_phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=case["source_set_id"],
                review_id=case["review_id"],
            )

            validation_phase = _phase(
                failed_phase_result.summary,
                "applicability_validation",
            )
            self.assertFalse(validation_phase["passed"])
            self.assertFalse(failed_phase_result.summary["reviewer_ready"])


def _case(summary: dict, case_id: str) -> dict:
    for case in summary["cases"]:
        if case["id"] == case_id:
            return case
    raise AssertionError(f"Missing case {case_id}")


def _phase(summary: dict, phase_name: str) -> dict:
    for phase in summary["phases"]:
        if phase["name"] == phase_name:
            return phase
    raise AssertionError(f"Missing phase {phase_name}")
