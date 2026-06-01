from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.records import sha256_file
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links
from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _check,
    _finding,
    _read_jsonl,
    _run_generated_compliance_review,
    _write_generated_review_gate,
    _write_package,
    _write_rule_pack,
)
from tests.support.compliance_review_eval_fixtures import _assert_v1_land_exchange_contract


class ComplianceReviewTests(unittest.TestCase):
    def test_v1_land_exchange_rules_are_first_class_compliance_contract(self) -> None:
        _assert_v1_land_exchange_contract(self)

    def test_compliance_review_refuses_base_rule_pack_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])

            with self.assertRaisesRegex(ValueError, "generated applicability rule pack"):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=rule_pack_path,
                    review_id="base-review-blocked",
                )

            review_dir = output_dir / "reviews" / "base-review-blocked"
            self.assertFalse((review_dir / "compliance_review.json").exists())

    def test_diagnostic_base_rule_pack_review_is_not_reviewer_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])

            result = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="base-diagnostic",
                allow_base_rule_pack_review=True,
            )

            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.summary["validation_passed"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            gate = _check(validation, "applicability_generated_rule_pack_gate")
            self.assertFalse(gate["passed"])
            self.assertEqual(gate["details"]["mode"], "base_rule_pack_diagnostic")

    def test_compliance_review_reuses_ready_rule_claim_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])

            first = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="base-diagnostic",
                allow_base_rule_pack_review=True,
            )

            with patch(
                "usfs_r1_ea_sources.rule_claim_binding.build_rule_claim_links",
                side_effect=AssertionError("rule-claim links should be reused"),
            ):
                second = run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=rule_pack_path,
                    review_id="base-diagnostic",
                    allow_base_rule_pack_review=True,
                )

            self.assertEqual(second.rule_claim_links_path, first.rule_claim_links_path)
            self.assertEqual(
                second.summary["rule_claim_summary_path"],
                first.summary["rule_claim_summary_path"],
            )

    def test_generated_rule_pack_diagnostic_mode_allows_non_reviewer_ready_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-diagnostic"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            (
                output_dir
                / "reviews"
                / review_id
                / "applicability"
                / "generated_rule_pack_validation.json"
            ).unlink()

            result = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=generated_rule_pack_path,
                review_id=review_id,
                reuse_package_cache=True,
                allow_generated_rule_pack_diagnostic=True,
            )

            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.summary["validation_passed"])
            self.assertEqual(
                result.summary["applicability_gate"]["mode"],
                "generated_rule_pack_diagnostic",
            )
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            gate = _check(validation, "applicability_generated_rule_pack_gate")
            self.assertFalse(gate["passed"])
            self.assertEqual(gate["details"]["mode"], "generated_rule_pack_diagnostic")

    def test_generated_rule_pack_gate_makes_review_reviewer_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-review"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )

            result = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=generated_rule_pack_path,
                review_id=review_id,
                reuse_package_cache=True,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(
                result.summary["applicability_gate"]["mode"],
                "generated_rule_pack",
            )
            self.assertTrue(result.authority_provenance_path.exists())
            self.assertTrue(result.authority_explanation_paths_path.exists())
            self.assertTrue(result.non_applicable_authority_appendix_path.exists())
            self.assertTrue(result.non_applicable_authority_appendix_markdown_path.exists())
            self.assertTrue(result.reviewer_resolution_report_path.exists())
            self.assertTrue(result.litigation_risk_summary_path.exists())
            matrix = json.loads(result.compliance_matrix_path.read_text(encoding="utf-8"))
            self.assertTrue(matrix["summary"]["non_applicable_authorities_path"])
            self.assertEqual(
                matrix["summary"]["authority_provenance_path"],
                str(result.authority_provenance_path),
            )
            self.assertEqual(
                matrix["summary"]["reviewer_resolution_report_path"],
                str(result.reviewer_resolution_report_path),
            )
            self.assertEqual(
                matrix["summary"]["authority_explanation_paths_path"],
                str(result.authority_explanation_paths_path),
            )
            matrix_row = matrix["rows"][0]
            self.assertEqual(matrix_row["candidate_authority_id"], "candidate:purpose_need")
            self.assertEqual(matrix_row["applicability_decision_id"], "decision:purpose_need")
            self.assertEqual(matrix_row["authority_family_ids"], ["unit_purpose_need"])
            self.assertEqual(
                matrix_row["primary_authority_path_classification"],
                "controlling",
            )
            self.assertTrue(matrix_row["retrieval_trace_ids"])
            self.assertTrue(matrix_row["graph_path_ids"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            self.assertTrue(
                _check(validation, "applicability_generated_rule_pack_gate")["passed"]
            )
            self.assertTrue(
                _check(
                    validation,
                    "compliance_findings_have_applicability_provenance",
                )["passed"]
            )
            self.assertTrue(
                _check(validation, "non_applicable_authority_appendix_ready")["passed"]
            )
            self.assertTrue(
                _check(validation, "authority_reviewer_resolution_report_ready")["passed"]
            )
            self.assertTrue(
                _check(validation, "litigation_risk_summary_deterministic")["passed"]
            )
            self.assertTrue(
                _check(validation, "authority_explanation_paths_ready")["passed"]
            )

    def test_compliance_review_consumes_sidecar_rule_claim_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-sidecar-review"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            sidecar_claims = build_claim_extraction(
                output_dir=output_dir,
                source_set_id=source_set_id,
                claims_dir=output_dir / "derived" / source_set_id / "claims_sidecar",
            )
            sidecar_links_dir = (
                output_dir
                / "derived"
                / source_set_id
                / "rule_claim_links_sidecar"
                / "generated-unit-nepa-ea"
                / "applicability-v0"
            )
            sidecar_links = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                claims_path=sidecar_claims.claims_path,
                links_dir=sidecar_links_dir,
                rule_pack_path=generated_rule_pack_path,
            )
            canonical_links_dir = (
                output_dir
                / "derived"
                / source_set_id
                / "rule_claim_links"
                / "generated-unit-nepa-ea"
                / "applicability-v0"
            )

            with patch(
                "usfs_r1_ea_sources.rule_claim_binding.build_rule_claim_links",
                side_effect=AssertionError("canonical rule-claim links should not be rebuilt"),
            ):
                result = run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=generated_rule_pack_path,
                    review_id=review_id,
                    reuse_package_cache=True,
                    rule_claim_links_path=sidecar_links.links_path,
                )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.rule_claim_links_path, sidecar_links.links_path)
            self.assertFalse(canonical_links_dir.exists())
            self.assertEqual(result.summary["rule_claim_links_dir"], str(sidecar_links_dir))
            self.assertFalse(result.summary["rule_claim_links_are_canonical"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            rule_claim_check = _check(validation, "rule_claim_binding_reviewer_ready")
            self.assertTrue(rule_claim_check["passed"])
            self.assertFalse(rule_claim_check["details"]["links_dir_is_canonical"])

    def test_compliance_review_emits_authority_integration_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need\n\nThe proposed action improves trail access.",
            )
            rule_pack_path = _write_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="authority-integration-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                include_non_applicable=True,
            )

            provenance = json.loads(
                result.authority_provenance_path.read_text(encoding="utf-8")
            )
            self.assertEqual(provenance["schema_version"], "authority-family-provenance-v0")
            self.assertEqual(
                provenance["summary"]["finding_authority_provenance_count"],
                2,
            )
            self.assertEqual(provenance["summary"]["findings_missing_authority_family_ids"], [])
            self.assertTrue(
                all(
                    row["candidate_authority_id"]
                    and row["applicability_decision_id"]
                    and row["authority_family_ids"]
                    for row in provenance["finding_authority_provenance"]
                )
            )

            appendix = json.loads(
                result.non_applicable_authority_appendix_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                appendix["schema_version"],
                "non-applicable-authority-appendix-v0",
            )
            self.assertEqual(appendix["summary"]["non_applicable_authority_count"], 1)
            self.assertTrue(appendix["summary"]["all_have_coverage_certificates"])
            self.assertTrue(appendix["summary"]["all_have_rationale"])
            self.assertEqual(
                appendix["authorities"][0]["authority_family_ids"],
                ["unit_not_applicable"],
            )
            self.assertEqual(
                appendix["authorities"][0]["search_coverage_certificate_ids"],
                ["coverage:not-applicable"],
            )

            explanation = json.loads(
                result.authority_explanation_paths_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                explanation["schema_version"],
                "authority-explanation-paths-v0",
            )
            self.assertTrue(explanation["summary"]["passed"])
            self.assertEqual(explanation["summary"]["finding_path_count"], 2)
            self.assertEqual(explanation["summary"]["non_applicable_path_count"], 1)
            self.assertEqual(
                explanation["finding_explanation_paths"][0][
                    "primary_authority_path_classification"
                ],
                "controlling",
            )

            resolution = json.loads(
                result.reviewer_resolution_report_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                resolution["schema_version"],
                "authority-reviewer-resolution-report-v0",
            )
            self.assertEqual(resolution["summary"]["pending_resolution_count"], 0)
            self.assertTrue(resolution["summary"]["passed"])

            risk = json.loads(result.litigation_risk_summary_path.read_text(encoding="utf-8"))
            self.assertEqual(risk["schema_version"], "litigation-risk-summary-v0")
            self.assertEqual(risk["summary"]["legal_conclusion_count"], 0)
            categories = {flag["risk_category"] for flag in risk["risk_flags"]}
            self.assertIn("package_evidence_gap", categories)
            self.assertIn("non_applicable_authority_coverage_boundary", categories)
            self.assertTrue(
                all(
                    flag["legal_conclusion"] is False
                    and flag["deterministic_basis"] is True
                    and flag["artifact_refs"]
                    for flag in risk["risk_flags"]
                )
            )

    def test_generated_rule_pack_gate_requires_non_applicable_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-missing-non-app"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            (
                output_dir
                / "reviews"
                / review_id
                / "applicability"
                / "non_applicable_authorities.json"
            ).unlink()

            with self.assertRaisesRegex(ValueError, "non_applicable_authorities_artifact_valid"):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=generated_rule_pack_path,
                    review_id=review_id,
                    reuse_package_cache=True,
                )

    def test_generated_rule_pack_gate_requires_non_applicable_search_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-missing-coverage"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
                include_non_applicable=True,
            )
            (
                output_dir
                / "reviews"
                / review_id
                / "applicability"
                / "search_coverage_certificates.json"
            ).unlink()

            with self.assertRaisesRegex(
                ValueError,
                "non_applicable_authority_search_coverage_exists",
            ):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=generated_rule_pack_path,
                    review_id=review_id,
                    reuse_package_cache=True,
                )

    def test_generated_rule_pack_gate_requires_empty_coverage_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-missing-empty-coverage"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            (
                output_dir
                / "reviews"
                / review_id
                / "applicability"
                / "search_coverage_certificates.json"
            ).unlink()

            with self.assertRaisesRegex(
                ValueError,
                "non_applicable_authority_search_coverage_exists",
            ):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=generated_rule_pack_path,
                    review_id=review_id,
                    reuse_package_cache=True,
                )

    def test_generated_rule_pack_gate_requires_explicit_generated_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-missing-ready"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            generated_validation_path = (
                output_dir
                / "reviews"
                / review_id
                / "applicability"
                / "generated_rule_pack_validation.json"
            )
            generated_validation = json.loads(
                generated_validation_path.read_text(encoding="utf-8")
            )
            generated_validation["summary"].pop("generated_rule_pack_ready")
            generated_validation_path.write_text(
                json.dumps(generated_validation, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "generated_rule_pack_validation_passed"):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=generated_rule_pack_path,
                    review_id=review_id,
                    reuse_package_cache=True,
                )

    def test_generated_rule_pack_gate_requires_package_chunks_hash_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-stale-package-chunks"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            generated_pack = json.loads(generated_rule_pack_path.read_text(encoding="utf-8"))
            generated_pack["package_chunks_sha256"] = "0" * 64
            generated_rule_pack_path.write_text(
                json.dumps(generated_pack, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            generated_sha = sha256_file(generated_rule_pack_path)
            generated_validation_path = (
                output_dir
                / "reviews"
                / review_id
                / "applicability"
                / "generated_rule_pack_validation.json"
            )
            generated_validation = json.loads(
                generated_validation_path.read_text(encoding="utf-8")
            )
            generated_validation["summary"][
                "generated_rule_pack_sha256"
            ] = generated_sha
            generated_validation["summary"][
                "expected_generated_rule_pack_sha256"
            ] = generated_sha
            generated_validation_path.write_text(
                json.dumps(generated_validation, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=generated_rule_pack_path,
                review_id=review_id,
                reuse_package_cache=True,
            )

            self.assertFalse(result.summary["reviewer_ready"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            gate = _check(validation, "applicability_generated_rule_pack_gate")
            self.assertFalse(gate["passed"])
            self.assertIn(
                "package_chunks_match_applicability_run",
                gate["details"]["failed_checks"],
            )

    def test_compliance_review_emits_rule_pack_findings_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need\n\nThe proposed action improves trail access.",
            )
            rule_pack_path = _write_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.compliance_review_path.exists())
            self.assertTrue(result.compliance_matrix_path.exists())
            self.assertTrue(result.compliance_matrix_markdown_path.exists())
            self.assertTrue(result.compliance_matrix_pdf_path.exists())
            self.assertGreater(result.compliance_matrix_pdf_path.stat().st_size, 0)
            self.assertTrue(result.compliance_matrix_pdf_path.read_bytes().startswith(b"%PDF-"))
            self.assertTrue(result.compliance_validation_path.exists())
            self.assertTrue(result.finding_nodes_path.exists())
            self.assertTrue(result.finding_edges_path.exists())
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["finding_status_counts"], {"gap": 1, "pass": 1})
            self.assertEqual(
                result.summary["compliance_matrix_path"],
                str(result.compliance_matrix_path),
            )
            self.assertEqual(
                result.summary["compliance_matrix_pdf_path"],
                str(result.compliance_matrix_pdf_path),
            )
            self.assertEqual(result.summary["baseline_source_record_count"], 2)
            self.assertEqual(
                result.summary["evaluated_baseline_source_record_ids"],
                ["R1EA-001", "R1EA-002"],
            )

            report = json.loads(result.compliance_review_path.read_text(encoding="utf-8"))
            purpose = _finding(report, "purpose_need")
            mitigation = _finding(report, "mitigation")
            self.assertEqual(purpose["status"], "pass")
            self.assertEqual(purpose["claim_type"], "supported_compliance_finding")
            self.assertTrue(purpose["source_library_evidence_citation"])
            self.assertTrue(purpose["package_evidence_citation"])
            self.assertGreaterEqual(purpose["source_claim_link_count"], 1)
            self.assertTrue(purpose["source_claim_links"][0]["claim_id"])
            self.assertEqual(mitigation["status"], "gap")
            self.assertEqual(mitigation["claim_type"], "package_evidence_gap")
            self.assertTrue(mitigation["source_library_evidence_citation"])
            self.assertIsNone(mitigation["package_evidence_citation"])
            self.assertGreaterEqual(mitigation["source_claim_link_count"], 1)

            matrix = json.loads(result.compliance_matrix_path.read_text(encoding="utf-8"))
            self.assertEqual(matrix["schema_version"], "compliance-matrix-v0")
            self.assertEqual(matrix["summary"]["row_count"], 2)
            matrix_rows = {row["rule_id"]: row for row in matrix["rows"]}
            self.assertEqual(matrix_rows["purpose_need"]["status"], "pass")
            self.assertEqual(matrix_rows["purpose_need"]["authority_category"], "regulation")
            self.assertEqual(
                matrix_rows["purpose_need"]["authority_source_record_id"],
                "R1EA-001",
            )
            self.assertEqual(matrix["summary"]["applicability_counts"], {"applicable": 2})
            self.assertEqual(matrix["summary"]["applicable_row_count"], 2)
            self.assertEqual(
                matrix["summary"]["compliance_matrix_pdf_path"],
                str(result.compliance_matrix_pdf_path),
            )
            self.assertTrue(matrix_rows["purpose_need"]["ea_package_citation"])
            self.assertTrue(matrix_rows["purpose_need"]["source_library_citation"])
            self.assertIn("R1EA-001", matrix_rows["purpose_need"]["applied_source_record_ids"])
            self.assertEqual(matrix_rows["purpose_need"]["applied_source_document_roles"], ["regulation"])
            self.assertTrue(matrix_rows["purpose_need"]["citation_requirements_met"])
            self.assertEqual(matrix_rows["mitigation"]["failure_category"], "package_evidence_gap")
            markdown = result.compliance_matrix_markdown_path.read_text(encoding="utf-8")
            self.assertIn("# Compliance Matrix", markdown)
            self.assertIn("## Responsible Official Readout", markdown)
            self.assertIn("## Accuracy Audit", markdown)
            self.assertIn(
                "| Review topic | Signer question | Decision support | EA record support | Authority basis | Trace / caveats |",
                markdown,
            )
            self.assertIn("| Review gates | Pass |", markdown)
            self.assertIn("Review gates passed and reviewer-ready support is available.", markdown)
            self.assertIn("purpose_need", markdown)
            self.assertIn("Record need:", markdown)
            self.assertIn("The proposed action improves trail access.", markdown)
            self.assertNotIn("reviewer_ready=True", markdown)
            self.assertNotIn("status counts {", markdown)

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            self.assertTrue(validation["passed"])
            self.assertTrue(
                _check(validation, "applicable_findings_have_authority_source_records")[
                    "passed"
                ]
            )
            self.assertTrue(_check(validation, "baseline_source_documents_evaluated")["passed"])
            self.assertTrue(_check(validation, "all_rules_evaluated")["passed"])
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertFalse(forest_plan_gate["details"]["required"])
            self.assertEqual(forest_plan_gate["details"]["scope_status"], "ambiguous")
            self.assertTrue(
                _check(validation, "claim_findings_have_source_citations")["passed"]
            )
            self.assertTrue(
                _check(validation, "claim_findings_have_source_claim_links")["passed"]
            )
            nodes = _read_jsonl(result.finding_nodes_path)
            edges = _read_jsonl(result.finding_edges_path)
            self.assertIn("ComplianceRulePack", {node["type"] for node in nodes})
            self.assertIn("ComplianceRule", {node["type"] for node in nodes})
            self.assertIn("ComplianceFinding", {node["type"] for node in nodes})
            self.assertIn("SourceClaim", {node["type"] for node in nodes})
            self.assertIn("PackageEvidenceGap", {node["type"] for node in nodes})
            self.assertIn(
                "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
                {edge["relationship"] for edge in edges},
            )
            self.assertIn(
                "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
                {edge["relationship"] for edge in edges},
            )
            self.assertIn("FINDING_HAS_PACKAGE_GAP", {edge["relationship"] for edge in edges})
