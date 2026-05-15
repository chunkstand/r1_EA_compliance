from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_gold_eval import _effective_cases_for_rule_pack
from usfs_r1_ea_sources.compliance_gold_eval import _gold_rule_pack_match_mode
from usfs_r1_ea_sources.compliance_gold_eval import run_compliance_gold_eval
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval

from tests.support.compliance_phase_eval_fixtures import _write_graph_phase_outputs
from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _check,
    _phase,
    _write_gold_eval_file,
    _write_rule_pack,
)


class ComplianceGoldEvalTests(unittest.TestCase):
    def test_compliance_gold_eval_runs_adjudicated_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            self.assertFalse(result.summary["reviewer_ready_rule_pack"])
            self.assertFalse(result.summary["promotion_ready"])
            self.assertEqual(result.summary["case_count"], 3)
            self.assertEqual(result.summary["adjudicated_case_count"], 3)
            self.assertEqual(
                result.summary["profile_counts"],
                {"mixed": 1, "negative": 1, "positive": 1},
            )
            self.assertEqual(result.summary["failed_case_count"], 0)
            self.assertEqual(result.summary["metrics"]["source_record_match_rate"], 1.0)
            self.assertEqual(result.summary["metrics"]["source_document_role_match_rate"], 1.0)
            self.assertEqual(result.summary["cases"][0]["source_record_mismatches"], [])
            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )
            gold_phase = _phase(phase_result.summary, "compliance_gold_eval")
            self.assertTrue(gold_phase["passed"])
            self.assertFalse(gold_phase["reviewer_ready"])
            self.assertEqual(gold_phase["details"]["case_count"], 3)
            self.assertIn("gold_eval_not_promotion_ready", gold_phase["details"]["failed_checks"])

    def test_generated_base_gold_cases_merge_generated_status_overrides(self) -> None:
        gold = {
            "rule_pack_id": "unit-nepa-ea",
            "rule_pack_version": "0.1.0",
            "cases": [
                {
                    "id": "gold-generated",
                    "profile": "mixed",
                    "package_text": "Purpose and Need. Trail access remains under review.",
                    "expected_statuses": {
                        "purpose_need": "pass",
                        "mitigation": "pass",
                    },
                    "expected_generated_statuses": {
                        "purpose_need": "gap",
                        "trail_access_authority_template": "uncertain",
                    },
                    "adjudication": {
                        "status": "adjudicated_seed",
                        "source_type": "realistic_synthetic",
                        "adjudicated_by": ["unit-test"],
                        "adjudicated_at": "2026-05-12",
                        "rationale": "Generated-pack compatibility unit fixture.",
                    },
                }
            ],
        }
        generated_rule_pack = {
            "schema_version": "generated-compliance-rule-pack-v0",
            "rule_pack_id": "generated-unit-nepa-ea-phase-review",
            "version": "applicability-v0",
            "base_rule_pack_id": "unit-nepa-ea",
            "base_rule_pack_version": "0.1.0",
            "rules": [
                {"id": "purpose_need", "generated_from_applicability": True},
                {"id": "mitigation", "generated_from_applicability": True},
                {
                    "id": "trail_access_authority_template",
                    "generated_from_applicability": True,
                },
            ],
        }

        match_mode = _gold_rule_pack_match_mode(gold, generated_rule_pack)
        self.assertEqual(match_mode, "generated_base")

        cases = _effective_cases_for_rule_pack(
            cases=gold["cases"],
            rule_pack=generated_rule_pack,
            match_mode=match_mode,
        )

        self.assertEqual(len(cases), 1)
        self.assertEqual(
            cases[0]["expected_statuses"],
            {
                "mitigation": "pass",
                "purpose_need": "gap",
                "trail_access_authority_template": "uncertain",
            },
        )
        self.assertEqual(
            cases[0]["expected_finding_status_counts"],
            {"gap": 1, "pass": 1, "uncertain": 1},
        )
        self.assertEqual(
            cases[0]["expected_source_claim_links"]["trail_access_authority_template"],
            True,
        )

    def test_compliance_gold_eval_fails_missing_required_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp), profiles=["positive", "mixed", "mixed"])

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["promotion_ready"])
            profile_check = _check(result.summary, "gold_eval_required_profiles_present")
            self.assertFalse(profile_check["passed"])
            self.assertEqual(profile_check["details"]["missing_profiles"], ["negative"])

    def test_compliance_gold_eval_resolves_package_paths_from_gold_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(root)
            gold_path = _write_gold_eval_file(root)
            fixture_path = root / "fixtures" / "positive.txt"
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.write_text(
                "Purpose and Need. Mitigation measures support a FONSI.",
                encoding="utf-8",
            )
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            gold["cases"][0].pop("package_text")
            gold["cases"][0]["package_path"] = "fixtures/positive.txt"
            gold_path.write_text(json.dumps(gold, sort_keys=True), encoding="utf-8")

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(
                result.summary["cases"][0]["package_path"],
                str(fixture_path.resolve()),
            )

    def test_compliance_gold_eval_fails_missing_adjudication_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            gold["cases"][0]["adjudication"].pop("rationale")
            gold_path.write_text(json.dumps(gold, sort_keys=True), encoding="utf-8")

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id="source-set-test",
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["promotion_ready"])
            self.assertFalse(result.summary["compliance_review_eval_passed"])
            adjudication_check = _check(result.summary, "gold_eval_cases_have_adjudication")
            self.assertFalse(adjudication_check["passed"])
            self.assertEqual(
                adjudication_check["details"]["failures"][0]["fields"],
                ["rationale"],
            )

    def test_compliance_gold_eval_fails_duplicate_ids_and_unsafe_package_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            gold["cases"][1]["id"] = gold["cases"][0]["id"]
            gold["cases"][2].pop("package_text")
            gold["cases"][2]["package_path"] = "../outside-fixture.txt"
            gold_path.write_text(json.dumps(gold, sort_keys=True), encoding="utf-8")

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id="source-set-test",
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertFalse(result.summary["passed"])
            cases_check = _check(result.summary, "gold_eval_cases_present")
            reasons = {failure["reason"] for failure in cases_check["details"]["failures"]}
            self.assertIn("duplicate_id", reasons)
            self.assertIn("package_path_must_be_relative_child", reasons)

    def test_compliance_gold_eval_fails_resolved_package_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "gold-root"
            root.mkdir()
            outside_dir = Path(tmp) / "outside"
            outside_dir.mkdir()
            (outside_dir / "fixture.txt").write_text("Purpose and Need.", encoding="utf-8")
            try:
                (root / "fixture-link").symlink_to(outside_dir, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            output_dir = Path(tmp) / "source_library"
            rule_pack_path = _write_rule_pack(root)
            gold_path = _write_gold_eval_file(root)
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            gold["cases"][0].pop("package_text")
            gold["cases"][0]["package_path"] = "fixture-link/fixture.txt"
            gold_path.write_text(json.dumps(gold, sort_keys=True), encoding="utf-8")

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id="source-set-test",
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertFalse(result.summary["passed"])
            cases_check = _check(result.summary, "gold_eval_cases_present")
            reasons = {failure["reason"] for failure in cases_check["details"]["failures"]}
            self.assertIn("package_path_must_resolve_under_gold_file", reasons)

    def test_compliance_gold_eval_records_missing_package_fixture_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            gold["cases"][0].pop("package_text")
            gold["cases"][0]["package_path"] = "missing-fixture.txt"
            gold_path.write_text(json.dumps(gold, sort_keys=True), encoding="utf-8")

            result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id="source-set-test",
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertTrue(result.summary["adjudication_checks_passed"])
            self.assertFalse(result.summary["compliance_review_eval_passed"])
            self.assertIn("missing-fixture.txt", result.summary["compliance_review_eval_error"])
            self.assertEqual(
                result.summary["cases"][0]["failure_reasons"],
                ["compliance_review_eval_not_run"],
            )
