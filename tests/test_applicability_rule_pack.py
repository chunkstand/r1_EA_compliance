from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.applicability_rule_pack import generate_applicability_rule_pack
from usfs_r1_ea_sources.applicability_rule_pack import validate_generated_rule_pack
from usfs_r1_ea_sources.applicability_validation import validate_applicability_run
from usfs_r1_ea_sources.cli import main

from tests.support.applicability_decision_fixtures import _authority_family_candidate
from tests.support.applicability_decision_fixtures import _build_adjudicated_applicability_dir
from tests.support.applicability_decision_fixtures import _write_decision_fixture
from tests.support.applicability_decision_fixtures import _write_generated_rule_base_pack
from tests.support.applicability_decision_support import _write_json


class ApplicabilityRulePackTests(unittest.TestCase):
    def test_generated_rule_pack_uses_only_validated_applicable_authorities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)

            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.generated_rule_pack_path.exists())
            self.assertTrue(result.generated_rule_pack_validation_path.exists())
            generated = json.loads(
                result.generated_rule_pack_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                generated["schema_version"],
                "generated-compliance-rule-pack-v0",
            )
            self.assertEqual(generated["applicable_authority_count"], 4)
            self.assertEqual(len(generated["rules"]), 4)
            rule_ids = {rule["id"] for rule in generated["rules"]}
            self.assertEqual(
                rule_ids,
                {
                    "baseline_nepa",
                    "cwa_permit",
                    "esa_consultation",
                    "forest_plan_component_STD-FP-01",
                },
            )
            self.assertNotIn("ce_fanec", rule_ids)
            self.assertNotIn("sioux_geography", rule_ids)
            for rule in generated["rules"]:
                metadata = rule["applicability"]
                self.assertEqual(metadata["status"], "applicable")
                self.assertTrue(metadata["decision_id"])
                self.assertTrue(metadata["retrieval_trace_ids"])
                self.assertTrue(metadata["source_record_ids"])
                self.assertEqual(rule["generated_rule_id"], rule["id"])
                self.assertIn("package_section_expectations", rule)
                self.assertIn("applicability_artifact_hashes", rule)
                for hash_field in {
                    "base_rule_pack_sha256",
                    "applicability_validation_sha256",
                    "authority_universe_sha256",
                    "applicable_authorities_sha256",
                    "non_applicable_authorities_sha256",
                    "package_fact_graph_sha256",
                    "selected_action_sha256",
                    "retrieval_trace_sha256",
                    "graph_trace_sha256",
                    "search_coverage_certificates_sha256",
                    "package_manifest_sha256",
                    "package_chunks_sha256",
                    "catalog_sha256",
                    "applicability_provenance_sha256",
                }:
                    self.assertTrue(rule["applicability_artifact_hashes"][hash_field])
                self.assertEqual(
                    metadata["artifact_hashes"],
                    rule["applicability_artifact_hashes"],
                )
                if rule["id"] != "forest_plan_component_STD-FP-01":
                    self.assertTrue(rule["base_rule_id"])
            applicable = json.loads(
                (applicability_dir / "applicable_authorities.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                generated["applicable_authorities_sha256"],
                result.summary["applicable_authorities_sha256"],
            )
            self.assertEqual(
                generated["applicable_authority_count"],
                applicable["applicable_authority_count"],
            )

    def test_generated_rule_pack_can_materialize_applicable_family_template(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_set_id = "source-set-unit"
            fixture = _write_decision_fixture(
                Path(tmp),
                extra_candidates=[_authority_family_candidate(source_set_id)],
            )
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)

            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertTrue(result.summary["passed"])
            generated = json.loads(
                result.generated_rule_pack_path.read_text(encoding="utf-8")
            )
            generated_by_id = {rule["id"]: rule for rule in generated["rules"]}
            family_rule = generated_by_id["clean_water_family_authority_template"]
            self.assertIsNone(family_rule["base_rule_id"])
            self.assertEqual(
                family_rule["applicability"]["candidate_authority_type"],
                "authority_family_rule_template",
            )
            self.assertEqual(
                family_rule["authority_source_record_id"],
                "R1EA-CWA",
            )
            self.assertEqual(family_rule["applies_if_package_terms"], ["wetlands"])
            self.assertFalse(family_rule["source_claim_link_requirements"]["required"])
            self.assertNotIn("ce_fanec", generated_by_id)

    def test_generated_rule_pack_requires_passing_applicability_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            validation_result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            self.assertFalse(validation_result.summary["passed"])

            with self.assertRaisesRegex(ValueError, "has not passed"):
                generate_applicability_rule_pack(
                    output_dir=fixture["output_dir"],
                    review_id=fixture["review_id"],
                    source_set_id=fixture["source_set_id"],
                    base_rule_pack_path=_write_generated_rule_base_pack(Path(tmp)),
                )

            generated_path = (
                fixture["output_dir"]
                / "reviews"
                / fixture["review_id"]
                / "applicability"
                / "generated_rule_pack.json"
            )
            self.assertFalse(generated_path.exists())

    def test_generated_rule_pack_refuses_stale_applicability_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)
            applicable_path = (
                fixture["output_dir"]
                / "reviews"
                / fixture["review_id"]
                / "applicability"
                / "applicable_authorities.json"
            )
            applicable = json.loads(applicable_path.read_text(encoding="utf-8"))
            applicable["authorities"][0]["basis_type"] = "changed-after-validation"
            _write_json(applicable_path, applicable)

            with self.assertRaisesRegex(ValueError, "stale"):
                generate_applicability_rule_pack(
                    output_dir=fixture["output_dir"],
                    review_id=fixture["review_id"],
                    source_set_id=fixture["source_set_id"],
                    base_rule_pack_path=_write_generated_rule_base_pack(Path(tmp)),
                )

            generated_path = applicable_path.parent / "generated_rule_pack.json"
            self.assertFalse(generated_path.exists())

    def test_generated_rule_pack_refuses_stale_package_context_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            context_path = applicability_dir / "package_applicability_context.json"
            context = json.loads(context_path.read_text(encoding="utf-8"))
            context["package_manifest_sha256"] = "changed-after-validation"
            _write_json(context_path, context)

            with self.assertRaisesRegex(ValueError, "stale"):
                generate_applicability_rule_pack(
                    output_dir=fixture["output_dir"],
                    review_id=fixture["review_id"],
                    source_set_id=fixture["source_set_id"],
                    base_rule_pack_path=_write_generated_rule_base_pack(Path(tmp)),
                )

            generated_path = applicability_dir / "generated_rule_pack.json"
            self.assertFalse(generated_path.exists())

    def test_generated_rule_pack_validation_rejects_manual_edit_and_stale_inputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )
            generated = json.loads(
                result.generated_rule_pack_path.read_text(encoding="utf-8")
            )
            generated["rules"][0]["title"] = "Manual edit should fail validation"
            _write_json(result.generated_rule_pack_path, generated)

            edited_validation = validate_generated_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertFalse(edited_validation.summary["passed"])
            self.assertIn(
                "generated_rule_pack_mismatch",
                edited_validation.summary["failure_category_counts"],
            )

            # Regenerate to refresh the expected generated-pack hash, then stale an input.
            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )
            applicable_path = applicability_dir / "applicable_authorities.json"
            applicable = json.loads(applicable_path.read_text(encoding="utf-8"))
            applicable["authorities"][0]["basis_type"] = "stale-after-generation"
            _write_json(applicable_path, applicable)

            stale_validation = validate_generated_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertFalse(stale_validation.summary["passed"])
            self.assertIn(
                "generated_rule_pack_stale",
                stale_validation.summary["failure_category_counts"],
            )

    def test_generated_rule_pack_validate_only_requires_recorded_generated_hash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)
            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )
            result.generated_rule_pack_validation_path.unlink()

            validation = validate_generated_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertFalse(validation.summary["passed"])
            self.assertIn(
                "generated_rule_pack_mismatch",
                validation.summary["failure_category_counts"],
            )

    def test_cli_writes_generated_rule_pack_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))

            exit_code = main(
                [
                    "applicability-generate-rule-pack",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                    "--base-rule-pack",
                    str(base_rule_pack_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            self.assertTrue((applicability_dir / "generated_rule_pack.json").exists())
            self.assertTrue(
                (applicability_dir / "generated_rule_pack_validation.json").exists()
            )
