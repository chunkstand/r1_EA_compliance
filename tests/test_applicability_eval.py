from __future__ import annotations

from pathlib import Path
import copy
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_eval import run_applicability_eval
from usfs_r1_ea_sources.applicability_eval import run_applicability_gold_eval
from usfs_r1_ea_sources.applicability_eval import _read_case_artifacts
from usfs_r1_ea_sources.applicability_eval import _score_case
from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_SEED = REPO_ROOT / "config" / "applicability_eval_seed.json"
GOLD_SEED = REPO_ROOT / "config" / "applicability_gold_eval_v0.json"
RULE_PACK = REPO_ROOT / "config" / "compliance_rule_pack_nepa_ea_v0.json"
AUTHORITY_FAMILY_TEMPLATES = (
    REPO_ROOT / "config" / "authority_family_rule_templates_nepa_ea_v1.json"
)


class ApplicabilityEvalTests(unittest.TestCase):
    def test_applicability_eval_seed_covers_milestone_4_contract(self) -> None:
        seed = json.loads(EVAL_SEED.read_text(encoding="utf-8"))
        templates = json.loads(AUTHORITY_FAMILY_TEMPLATES.read_text(encoding="utf-8"))
        template_rule_ids = sorted(
            template["rule_id"] for template in templates["templates"]
        )
        template_family_ids = sorted(
            template["authority_family_id"] for template in templates["templates"]
        )

        self.assertEqual(sorted(seed["high_priority_authority_family_ids"]), template_family_ids)
        self.assertEqual(
            sorted(seed["required_real_package_coverage_tags"]),
            [
                "cultural_tribal",
                "designated_area",
                "forest_plan_consistency",
                "land_exchange",
                "water_wetlands",
                "wildlife_species",
            ],
        )

        positive = _case_payload(EVAL_SEED, "seed-expanded-authority-positive")
        negative = _case_payload(EVAL_SEED, "seed-expanded-authority-negative")
        unresolved = _case_payload(EVAL_SEED, "seed-expanded-authority-adjudication-required")
        weak_auxiliary = _case_payload(
            EVAL_SEED,
            "seed-arbitration-strong-positive-weak-auxiliary",
        )
        positive_negative = _case_payload(
            EVAL_SEED,
            "seed-arbitration-positive-negative-conflict",
        )
        no_action = _case_payload(
            EVAL_SEED,
            "seed-arbitration-no-action-background-only",
        )
        template_specific = _case_payload(
            EVAL_SEED,
            "seed-arbitration-template-specific-sufficiency",
        )
        self.assertEqual(sorted(positive["candidate_authority_family_rule_ids"]), template_rule_ids)
        self.assertEqual(sorted(negative["candidate_authority_family_rule_ids"]), template_rule_ids)
        self.assertEqual(positive["expected_status_for_candidate_authority_family_rule_ids"], "applicable")
        self.assertEqual(
            negative["expected_status_for_candidate_authority_family_rule_ids"],
            "not_applicable",
        )
        self.assertEqual(unresolved["profile"], "unresolved")
        self.assertFalse(unresolved["expected_validation_passed"])
        self.assertEqual(
            unresolved["expected_statuses"],
            {"clean_water_act_wotus_permits_authority_template": "needs_adjudication"},
        )
        self.assertEqual(
            unresolved["expected_arbitration_statuses_by_rule_id"],
            {"clean_water_act_wotus_permits_authority_template": "weak_positive_only"},
        )
        self.assertEqual(
            weak_auxiliary["expected_arbitration_statuses_by_rule_id"],
            {
                "roads_access_special_use_action_authorities_authority_template": (
                    "strong_positive_with_weak_auxiliary"
                )
            },
        )
        self.assertEqual(
            positive_negative["expected_arbitration_statuses_by_rule_id"],
            {
                "clean_water_act_wotus_permits_authority_template": (
                    "positive_negative_conflict"
                )
            },
        )
        self.assertEqual(
            no_action["expected_arbitration_decision_effects_by_rule_id"],
            {
                "roads_access_special_use_action_authorities_authority_template": (
                    "blocked_by_weak_positive_trigger"
                )
            },
        )
        self.assertEqual(
            template_specific[
                "candidate_authority_family_template_overrides_by_rule_id"
            ]["roads_access_special_use_action_authorities_authority_template"][
                "trigger_arbitration"
            ]["minimum_strong_trigger_groups"],
            2,
        )
        self.assertTrue(
            (EVAL_SEED.parent / positive["package_path"]).exists(),
            positive["package_path"],
        )

    def test_applicability_eval_scores_decisions_and_generated_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"

            result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["case_count"], 9)
            self.assertEqual(result.summary["generated_rule_pack_ready_case_count"], 2)
            arbitration = result.summary["arbitration_summary"]
            self.assertGreaterEqual(
                arbitration["applicable_with_weak_auxiliary_count"],
                1,
            )
            self.assertGreaterEqual(
                arbitration["weak_positive_only_needs_adjudication_count"],
                2,
            )
            self.assertGreaterEqual(
                arbitration["positive_negative_conflict_needs_adjudication_count"],
                1,
            )
            self.assertGreaterEqual(
                arbitration["insufficient_strong_positive_needs_adjudication_count"],
                1,
            )
            coverage = result.summary["authority_family_template_coverage"]
            self.assertTrue(coverage["passed"])
            self.assertEqual(coverage["positive_covered_family_count"], 19)
            self.assertEqual(coverage["negative_covered_family_count"], 19)
            self.assertEqual(coverage["unresolved_covered_family_count"], 2)
            unresolved = _case(result.summary, "seed-expanded-authority-adjudication-required")
            self.assertEqual(
                unresolved["actual_statuses"],
                {"clean_water_act_wotus_permits_authority_template": "needs_adjudication"},
            )
            self.assertFalse(unresolved["validation_passed"])
            self.assertFalse(unresolved["generated_rule_pack_ready"])
            self.assertEqual(
                unresolved["basis_types_by_rule_id"],
                {
                    "clean_water_act_wotus_permits_authority_template": (
                        "unresolved_evidence_conflict"
                    )
                },
            )
            self.assertEqual(
                unresolved["arbitration_statuses_by_rule_id"],
                {"clean_water_act_wotus_permits_authority_template": "weak_positive_only"},
            )
            weak_auxiliary = _case(
                result.summary,
                "seed-arbitration-strong-positive-weak-auxiliary",
            )
            self.assertEqual(
                weak_auxiliary["actual_statuses"],
                {
                    "roads_access_special_use_action_authorities_authority_template": (
                        "applicable"
                    )
                },
            )
            self.assertEqual(
                weak_auxiliary["arbitration_decision_effects_by_rule_id"],
                {
                    "roads_access_special_use_action_authorities_authority_template": (
                        "positive_trigger_decisive_with_weak_auxiliary"
                    )
                },
            )
            positive_negative = _case(
                result.summary,
                "seed-arbitration-positive-negative-conflict",
            )
            self.assertEqual(
                positive_negative["arbitration_statuses_by_rule_id"],
                {"clean_water_act_wotus_permits_authority_template": "positive_negative_conflict"},
            )
            no_action = _case(result.summary, "seed-arbitration-no-action-background-only")
            self.assertEqual(
                no_action["arbitration_statuses_by_rule_id"],
                {
                    "roads_access_special_use_action_authorities_authority_template": (
                        "weak_positive_only"
                    )
                },
            )
            template_specific = _case(
                result.summary,
                "seed-arbitration-template-specific-sufficiency",
            )
            self.assertEqual(
                template_specific["arbitration_statuses_by_rule_id"],
                {
                    "roads_access_special_use_action_authorities_authority_template": (
                        "insufficient_strong_positive_trigger"
                    )
                },
            )
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

    def test_applicability_eval_scores_source_role_and_section_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            eval_path = root / "bad-source-role-eval.json"
            payload = copy.deepcopy(json.loads(EVAL_SEED.read_text(encoding="utf-8")))
            payload["cases"] = [payload["cases"][0]]
            payload["cases"][0]["expected_source_record_ids_by_rule_id"][
                "esa_section_7"
            ] = ["R1EA-999"]
            payload["cases"][0]["expected_document_roles_by_rule_id"]["esa_section_7"] = [
                "regulation"
            ]
            payload["cases"][0]["expected_package_section_families_by_rule_id"][
                "esa_section_7"
            ] = ["effects"]
            eval_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=eval_path,
                base_rule_pack_path=RULE_PACK,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["failure_category_counts"],
                {
                    "document_role_alignment_mismatch": 1,
                    "package_section_alignment_mismatch": 1,
                    "source_record_alignment_mismatch": 1,
                },
            )

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

    def test_applicability_eval_fails_when_non_applicable_artifact_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )
            case_summary = _case(eval_result.summary, "seed-mixed-applicability")
            non_applicable_path = (
                Path(case_summary["applicability_dir"]) / "non_applicable_authorities.json"
            )
            non_applicable_path.unlink()

            rescored = _rescore_case(
                eval_file=EVAL_SEED,
                eval_summary=eval_result.summary,
                case_id="seed-mixed-applicability",
            )

            self.assertFalse(rescored["passed"])
            self.assertIn("non_applicable_authorities", rescored["required_artifact_gaps"])
            self.assertEqual(
                rescored["failure_category_counts"]["missing_applicability_artifact"],
                1,
            )

    def test_applicability_eval_fails_on_graph_trace_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )
            case_summary = _case(eval_result.summary, "seed-mixed-applicability")
            graph_trace_path = Path(case_summary["graph_trace_path"])
            retained = [
                line
                for line in graph_trace_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and "esa_section_7" not in line
            ]
            graph_trace_path.write_text("\n".join(retained) + "\n", encoding="utf-8")

            rescored = _rescore_case(
                eval_file=EVAL_SEED,
                eval_summary=eval_result.summary,
                case_id="seed-mixed-applicability",
            )

            self.assertFalse(rescored["graph_trace_coverage_matches"])
            self.assertEqual(rescored["failure_category_counts"]["graph_trace_gap"], 1)

    def test_applicability_eval_fails_on_generated_rule_pack_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )
            case_summary = _case(eval_result.summary, "seed-mixed-applicability")
            generated_path = Path(case_summary["generated_rule_pack_path"])
            generated = json.loads(generated_path.read_text(encoding="utf-8"))
            generated["manual_edit_marker"] = True
            generated_path.write_text(
                json.dumps(generated, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            rescored = _rescore_case(
                eval_file=EVAL_SEED,
                eval_summary=eval_result.summary,
                case_id="seed-mixed-applicability",
            )

            self.assertFalse(rescored["generated_rule_pack_hash_matches_validation"])
            self.assertEqual(
                rescored["failure_category_counts"]["generated_rule_pack_mismatch"],
                1,
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
            self.assertEqual(result.summary["case_count"], 5)
            self.assertTrue(
                any(
                    check["name"] == "gold_eval_cases_have_arbitration_expectations"
                    and check["passed"]
                    for check in result.summary["checks"]
                )
            )
            self.assertEqual(
                sorted(result.summary["profile_counts"]),
                ["adjudicated", "mixed", "negative", "positive", "unresolved"],
            )
            coverage = result.summary["authority_family_template_coverage"]
            self.assertEqual(coverage["unresolved_covered_family_count"], 1)
            self.assertEqual(coverage["adjudicated_covered_family_count"], 1)
            adjudicated = _case(result.summary, "gold-expanded-authority-adjudicated")
            self.assertEqual(
                adjudicated["actual_statuses"],
                {"clean_water_act_wotus_permits_authority_template": "applicable"},
            )
            self.assertEqual(
                adjudicated["basis_types_by_rule_id"],
                {"clean_water_act_wotus_permits_authority_template": "human_adjudication"},
            )
            self.assertEqual(
                adjudicated["adjudicated_rule_ids"],
                ["clean_water_act_wotus_permits_authority_template"],
            )
            self.assertTrue(adjudicated["validation_passed"])

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
            self.assertEqual(
                determination_phase["details"]["arbitration_summary"],
                phase_result.summary["applicability_arbitration_summary"],
            )
            self.assertIn(
                "arbitration_status_counts",
                determination_phase["details"]["arbitration_summary"],
            )

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

    def test_phase_eval_fails_closed_when_applicability_validation_hashes_are_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=EVAL_SEED,
                base_rule_pack_path=RULE_PACK,
            )
            case = _case(eval_result.summary, "seed-mixed-applicability")
            non_applicable_path = (
                Path(case["applicability_dir"]) / "non_applicable_authorities.json"
            )
            non_applicable = json.loads(non_applicable_path.read_text(encoding="utf-8"))
            non_applicable["manual_edit_marker"] = True
            non_applicable_path.write_text(
                json.dumps(non_applicable, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=case["source_set_id"],
                review_id=case["review_id"],
            )

            validation_phase = _phase(phase_result.summary, "applicability_validation")
            self.assertFalse(validation_phase["passed"])
            self.assertEqual(
                validation_phase["details"]["hash_gaps"][0]["artifact"],
                "non_applicable_authorities",
            )
            self.assertFalse(phase_result.summary["reviewer_ready"])


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


def _case_payload(eval_file: Path, case_id: str) -> dict:
    payload = json.loads(eval_file.read_text(encoding="utf-8"))
    for case in payload["cases"]:
        if case["id"] == case_id:
            return case
    raise AssertionError(f"Missing case payload {case_id}")


def _rescore_case(*, eval_file: Path, eval_summary: dict, case_id: str) -> dict:
    case_summary = _case(eval_summary, case_id)
    review_dir = Path(case_summary["review_dir"])
    applicability_dir = Path(case_summary["applicability_dir"])
    validation = json.loads(
        (applicability_dir / "applicability_validation.json").read_text(encoding="utf-8")
    )
    generated_validation_path = applicability_dir / "generated_rule_pack_validation.json"
    generated_validation = (
        json.loads(generated_validation_path.read_text(encoding="utf-8"))
        if generated_validation_path.exists()
        else {}
    )
    return _score_case(
        case=_case_payload(eval_file, case_id),
        case_id=case_id,
        review_id=case_summary["review_id"],
        source_set_id=case_summary["source_set_id"],
        review_dir=review_dir,
        retrieval_index_path=Path(case_summary["retrieval_index_path"]),
        validation_summary=validation,
        generated_summary=generated_validation.get("summary"),
        generated_error=None,
        artifacts=_read_case_artifacts(review_dir / "applicability"),
    )
