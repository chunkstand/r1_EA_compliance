from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.ea_review import _search_package_chunks
from usfs_r1_ea_sources.records import sha256_file
from usfs_r1_ea_sources.rule_packs import validate_rule_pack
from tests.support.compliance_component_fixtures import (
    _build_beaverhead_compliance_source_library,
    _build_custer_compliance_source_library,
    _build_flathead_compliance_source_library,
    _write_beaverhead_rule_pack,
    _write_component_adjudication_eval,
    _write_custer_rule_pack,
    _write_flathead_rule_pack,
)
from tests.support.compliance_review_fixtures import (
    _assert_v1_land_exchange_contract,
    _build_source_library,
    _check,
    _chunk,
    _finding,
    _read_jsonl,
    _rule_pack,
    _run_generated_compliance_review,
    _write_generated_review_gate,
    _write_grouped_conditional_rule_pack,
    _write_package,
    _write_rule_pack,
)

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

    def test_custer_compliance_review_requires_generated_component_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area. No new permanent or temporary roads "
                    "are proposed."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="custer-compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "custer_gallatin")
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertTrue(forest_plan["component_evaluation"]["validation_passed"])
            self.assertTrue(forest_plan["component_evaluation"]["reviewer_ready"])
            self.assertTrue(forest_plan["component_findings_path"])
            self.assertTrue(forest_plan["component_inventory_coverage_path"])
            self.assertTrue(forest_plan["applicable_standard_coverage_path"])
            matrix = json.loads(result.compliance_matrix_path.read_text(encoding="utf-8"))
            self.assertEqual(
                matrix["summary"]["forest_plan_review"]["scope_status"],
                "custer_gallatin",
            )
            self.assertTrue(
                matrix["summary"]["forest_plan_review"]["component_findings_path"]
            )
            forest_matrix = matrix["forest_plan_compliance"]
            self.assertEqual(
                forest_matrix["schema_version"],
                "forest-plan-compliance-matrix-v0",
            )
            self.assertGreater(forest_matrix["summary"]["row_count"], 0)
            self.assertGreater(
                forest_matrix["summary"]["applicable_standard_row_count"],
                0,
            )
            forest_rows = forest_matrix["rows"]
            self.assertTrue(
                any(
                    row["component_type"] == "standard"
                    and row["compliance_status"] == "complies"
                    for row in forest_rows
                )
            )
            markdown = result.compliance_matrix_markdown_path.read_text(
                encoding="utf-8",
            )
            self.assertIn("## Forest Plan Compliance", markdown)
            self.assertIn(
                "| Component | Direction / standard | Decision support | EA consistency support | Forest Plan basis | Trace / caveats |",
                markdown,
            )
            self.assertIn("| Forest Plan citations | Pass |", markdown)
            self.assertIn("Applicable standard complies", markdown)
            self.assertIn("BC-STD-CMBCA", markdown)
            self.assertIn("all 1 applicable standards comply", markdown)
            self.assertNotIn("standard applied: True", markdown)

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertTrue(forest_plan_gate["details"]["component_reviewer_ready"])
            self.assertTrue(
                forest_plan_gate["details"]["component_inventory_coverage_passed"]
            )
            self.assertTrue(
                forest_plan_gate["details"]["applicable_standard_coverage_passed"]
            )
            nodes = _read_jsonl(result.finding_nodes_path)
            edges = _read_jsonl(result.finding_edges_path)
            self.assertIn("ForestPlanReview", {node["type"] for node in nodes})
            self.assertIn("ForestPlanComponentEvaluation", {node["type"] for node in nodes})
            self.assertIn(
                "REVIEW_INCLUDES_FOREST_PLAN_REVIEW",
                {edge["relationship"] for edge in edges},
            )
            self.assertIn(
                "FOREST_PLAN_REVIEW_HAS_COMPONENT_EVALUATION",
                {edge["relationship"] for edge in edges},
            )

    def test_beaverhead_compliance_review_requires_selected_profile_component_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_beaverhead_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Beaverhead-Deerlodge National Forest on the "
                    "Dillon Ranger District in the Big Hole Landscape and the West Big Hole "
                    "Management Area. The EA tiers to the FEIS and references the Record of "
                    "Decision. Inventoried Roadless Area direction applies. ESA consultation "
                    "includes a Biological Assessment and Biological Opinion for grizzly bear. "
                    "No new permanent or temporary roads are proposed. "
                    "| BD-STD-WBH-01 | New permanent or temporary roads shall not be allowed. "
                    "| Yes | EA section 2.2 says no new permanent or temporary roads are "
                    "proposed. |"
                ),
            )
            rule_pack_path = _write_beaverhead_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="beaverhead-compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                forest_unit_id="beaverhead-deerlodge-nf",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "beaverhead_deerlodge_nf")
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertTrue(forest_plan["component_evaluation"]["validation_passed"])
            self.assertTrue(forest_plan["component_evaluation"]["reviewer_ready"])
            context = json.loads(Path(forest_plan["context_path"]).read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["name"] for entry in context["project_location_signals"]],
                ["Dillon Ranger District"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["geographic_areas"]],
                ["Big Hole Landscape"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["management_areas"]],
                ["West Big Hole Management Area"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["overlays"]],
                ["Inventoried Roadless Area"],
            )
            self.assertEqual(
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
                {
                    "support-feis-plan-context",
                    "support-rod-travel-management",
                    "support-lynx-biological-assessment",
                    "support-lynx-biological-opinion",
                    "support-grizzly-biological-assessment",
                    "support-grizzly-biological-opinion",
                },
            )

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertEqual(
                forest_plan_gate["details"]["scope_status"],
                "beaverhead_deerlodge_nf",
            )
            self.assertTrue(forest_plan_gate["details"]["component_reviewer_ready"])

    def test_flathead_compliance_review_requires_selected_profile_component_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_flathead_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Flathead National Forest on the Hungry "
                    "Horse-Glacier View Ranger District in the Hungry Horse Geographic Area and "
                    "the Jewel Basin Hiking Area. The action is adjacent to the Jewel Basin "
                    "Recommended Wilderness Area and an Inventoried Roadless Area. The EA tiers "
                    "to the FEIS and references the Record of Decision. ESA consultation "
                    "includes a Biological Assessment and Biological Opinion for Canada lynx, "
                    "bull trout, and grizzly bear in the NCDE primary conservation area. The "
                    "monitoring program, Biennial Monitoring Evaluation Report (BMER), and 2023 "
                    "Administrative Change are incorporated by reference. No motorized use, "
                    "mechanized transport, or stock use are proposed in the Jewel Basin Hiking "
                    "Area. | FW-STD-WTR-01 | New stream diversions and associated ditches shall "
                    "have screens placed on them to prevent capture of fish and other aquatic "
                    "organisms. | Yes | EA section 2.2 says new stream diversions and associated "
                    "ditches shall have screens placed on them to prevent capture of fish and "
                    "other aquatic organisms. |"
                ),
            )
            rule_pack_path = _write_flathead_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="flathead-compliance-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
                forest_unit_id="flathead-nf",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "flathead_nf")
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertTrue(forest_plan["component_evaluation"]["validation_passed"])
            self.assertTrue(forest_plan["component_evaluation"]["reviewer_ready"])
            context = json.loads(Path(forest_plan["context_path"]).read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["name"] for entry in context["project_location_signals"]],
                ["Hungry Horse-Glacier View Ranger District"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["geographic_areas"]],
                ["Hungry Horse Geographic Area"],
            )
            self.assertEqual(
                [entry["name"] for entry in context["management_areas"]],
                ["Jewel Basin Hiking Area"],
            )
            overlay_names = [entry["name"] for entry in context["overlays"]]
            self.assertIn("Inventoried Roadless Area", overlay_names)
            self.assertIn("Jewel Basin Recommended Wilderness Area", overlay_names)
            self.assertEqual(
                {entry["route_id"] for entry in context["supporting_plan_evidence"]},
                {
                    "support-feis-plan-context",
                    "support-rod-decision-basis",
                    "support-esa-biological-assessment",
                    "support-bull-trout-biological-opinion",
                    "support-grizzly-biological-opinion",
                    "support-monitoring-program",
                    "support-bmer-currentness",
                    "support-administrative-change",
                },
            )

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertEqual(
                forest_plan_gate["details"]["scope_status"],
                "flathead_nf",
            )
            self.assertTrue(forest_plan_gate["details"]["component_reviewer_ready"])

    def test_custer_component_adjudication_resolves_real_ea_omission_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))
            review_id = "custer-adjudicated-omission-unit"

            initial = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            self.assertFalse(initial.summary["reviewer_ready"])
            review_dir = output_dir / "reviews" / review_id
            queue = json.loads(
                (review_dir / "forest_plan_reviewer_resolution_queue.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(queue["item_count"], 1)
            _write_component_adjudication_eval(
                review_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                passed=True,
                queue_item_count=1,
            )

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertTrue(forest_plan["reviewer_ready"])
            self.assertFalse(forest_plan["component_evaluation"]["reviewer_ready"])
            self.assertTrue(forest_plan["component_adjudication"]["reviewer_ready"])
            self.assertEqual(
                forest_plan["component_adjudication"]["real_ea_omission_count"],
                1,
            )
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertFalse(forest_plan_gate["details"]["component_reviewer_ready"])
            self.assertTrue(
                forest_plan_gate["details"]["component_adjudication_reviewer_ready"]
            )
            self.assertEqual(
                forest_plan_gate["details"]["component_adjudication_system_miss_count"],
                0,
            )

    def test_custer_component_adjudication_accepts_reviewed_system_miss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))
            review_id = "custer-system-miss-adjudication-unit"
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            review_dir = output_dir / "reviews" / review_id
            _write_component_adjudication_eval(
                review_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                passed=True,
                queue_item_count=1,
                real_ea_omission_count=0,
                system_miss_count=1,
            )

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertTrue(forest_plan["component_adjudication"]["reviewer_ready"])
            self.assertEqual(forest_plan["component_adjudication"]["failed_checks"], [])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertTrue(forest_plan_gate["passed"])
            self.assertTrue(
                forest_plan_gate["details"]["component_adjudication_reviewer_ready"]
            )
            self.assertEqual(
                forest_plan_gate["details"]["component_adjudication_system_miss_count"],
                1,
            )

    def test_custer_compliance_review_fails_closed_on_stale_component_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_custer_compliance_source_library(output_dir, source_set_id)
            inventory_path = (
                output_dir
                / "derived"
                / source_set_id
                / "forest_plan_components"
                / "component_inventory.json"
            )
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["source_set_id"] = "source-set-stale"
            for component in inventory["components"]:
                component["source_set_id"] = "source-set-stale"
            inventory_path.write_text(
                json.dumps(inventory, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            package_path = _write_package(
                Path(tmp),
                (
                    "The proposed action is on the Custer Gallatin National Forest in the "
                    "Crazy Mountains Backcountry Area. No new permanent or temporary roads "
                    "are proposed."
                ),
            )
            rule_pack_path = _write_custer_rule_pack(Path(tmp))

            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="custer-stale-component-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            self.assertFalse(result.summary["reviewer_ready"])
            forest_plan = result.summary["forest_plan_review"]
            self.assertEqual(forest_plan["scope_status"], "custer_gallatin")
            self.assertFalse(forest_plan["reviewer_ready"])
            self.assertFalse(forest_plan["component_evaluation"]["validation_passed"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            forest_plan_gate = _check(validation, "forest_plan_component_gate_reviewer_ready")
            self.assertFalse(forest_plan_gate["passed"])
            self.assertTrue(forest_plan_gate["details"]["required"])
            self.assertFalse(forest_plan_gate["details"]["component_reviewer_ready"])
            self.assertFalse(
                forest_plan_gate["details"]["component_inventory_coverage_passed"]
            )

    def test_compliance_review_rejects_invalid_rule_pack(self) -> None:
        rule_pack = _rule_pack()
        del rule_pack["rules"][0]["source_query"]

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        self.assertFalse(_check(validation, "required_rule_fields_present")["passed"])

    def test_rule_pack_rejects_unsupported_filters_and_unsafe_ids(self) -> None:
        rule_pack = _rule_pack()
        rule_pack["rule_pack_id"] = "../bad-pack"
        rule_pack["rules"][0]["id"] = "bad/rule"
        rule_pack["rules"][0]["source_filters"] = {
            "document_roles": "regulation",
            "host": "",
        }

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        self.assertFalse(_check(validation, "rule_pack_identity_values_are_safe")["passed"])
        self.assertFalse(_check(validation, "rule_ids_are_safe")["passed"])
        filter_check = _check(validation, "rule_source_filter_keys_are_supported")
        self.assertFalse(filter_check["passed"])
        self.assertEqual(filter_check["details"]["failures"][0]["unknown_keys"], ["document_roles"])
        self.assertEqual(filter_check["details"]["failures"][0]["empty_values"], ["host"])

    def test_rule_pack_requires_authority_metadata(self) -> None:
        rule_pack = _rule_pack()
        rule_pack["rules"][0].pop("authority_category")
        rule_pack["rules"][0].pop("authority_source_record_id")
        rule_pack["rules"][0]["source_filters"].pop("source_record_id")

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        authority_check = _check(validation, "rule_authority_metadata_present")
        self.assertFalse(authority_check["passed"])
        self.assertEqual(
            authority_check["details"]["failures"][0]["missing"],
            ["authority_category", "source_record_id"],
        )

    def test_rule_pack_requires_declared_baseline_source_record_rules(self) -> None:
        rule_pack = _rule_pack()
        rule_pack["baseline_source_record_ids"] = ["R1EA-001", "R1EA-003"]

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        baseline_check = _check(validation, "baseline_source_records_covered")
        self.assertFalse(baseline_check["passed"])
        self.assertEqual(
            baseline_check["details"]["missing_source_record_ids"],
            ["R1EA-003"],
        )

    def test_rule_pack_requires_declared_baseline_rules_to_be_baseline_mode(self) -> None:
        rule_pack = _rule_pack()
        rule_pack["rules"][1]["applicability_mode"] = "conditional"
        rule_pack["rules"][1]["applies_if_package_terms"] = ["mitigation"]

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        baseline_check = _check(validation, "baseline_source_records_covered")
        self.assertFalse(baseline_check["passed"])
        self.assertEqual(baseline_check["details"]["non_baseline_rule_ids"], ["mitigation"])

    def test_compliance_review_rejects_unsafe_review_id_before_writing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])

            with self.assertRaisesRegex(ValueError, "review_id"):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    rule_pack_path=rule_pack_path,
                    review_id="../bad-review",
                )

            self.assertFalse((Path(tmp) / "bad-review").exists())

    def test_compliance_review_can_reuse_existing_package_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need\n\nThe proposed action improves trail access.",
            )
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])

            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id="reuse-cache-unit",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            first = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=generated_rule_pack_path,
                review_id="reuse-cache-unit",
                reuse_package_cache=True,
            )
            package_path.write_text("Routing slip. No package evidence.", encoding="utf-8")
            second = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=generated_rule_pack_path,
                review_id="reuse-cache-unit",
                reuse_package_cache=True,
            )

            self.assertEqual(first.summary["finding_status_counts"], {"pass": 1})
            self.assertEqual(second.summary["finding_status_counts"], {"pass": 1})

    def test_conditional_applicability_requires_grouped_positive_trigger_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_grouped_conditional_rule_pack(Path(tmp))
            negative_dir = Path(tmp) / "negative"
            positive_dir = Path(tmp) / "positive"
            negative_dir.mkdir()
            positive_dir.mkdir()
            negative_package = _write_package(
                negative_dir,
                (
                    "Decision Notice and FONSI\n\nThe EA is not subject to a categorical "
                    "exclusion, and the categorical exclusion path is not used. "
                    "Mitigation measures support a FONSI."
                ),
            )
            positive_package = _write_package(
                positive_dir,
                (
                    "CE Screening\n\nThe agency adopted CE after categorical exclusion "
                    "path screening. Mitigation measures support a FONSI."
                ),
            )

            negative = run_compliance_review(
                package_path=negative_package,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="grouped-trigger-negative",
                allow_base_rule_pack_review=True,
            )
            positive = run_compliance_review(
                package_path=positive_package,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="grouped-trigger-positive",
                allow_base_rule_pack_review=True,
            )

            negative_report = json.loads(
                negative.compliance_review_path.read_text(encoding="utf-8")
            )
            positive_report = json.loads(
                positive.compliance_review_path.read_text(encoding="utf-8")
            )
            negative_finding = _finding(negative_report, "ce_adoption")
            positive_finding = _finding(positive_report, "ce_adoption")
            expected_groups = [
                ["categorical exclusion", "CE"],
                ["adopted CE", "categorical exclusion path"],
            ]
            self.assertEqual(negative_finding["status"], "not_applicable")
            self.assertEqual(negative_finding["applicability_status"], "not_applicable")
            self.assertEqual(negative_finding["applicability_term_groups"], expected_groups)
            self.assertEqual(
                negative_finding["applicability_negative_terms"],
                [
                    "not subject to a categorical exclusion",
                    "categorical exclusion path is not used",
                ],
            )
            self.assertIsNone(negative_finding["applicability_evidence"])
            self.assertTrue(negative_finding["applicability_negative_evidence"])
            self.assertIn("explicit non-applicability", negative_finding["rationale"])
            self.assertEqual(positive_finding["status"], "pass")
            self.assertEqual(positive_finding["applicability_status"], "applicable")
            self.assertTrue(positive_finding["applicability_evidence"])
            positive_matrix = json.loads(
                positive.compliance_matrix_path.read_text(encoding="utf-8")
            )
            positive_row = positive_matrix["rows"][0]
            self.assertEqual(
                positive_row["applicability_basis"]["applies_if_package_term_groups"],
                expected_groups,
            )
            self.assertEqual(
                positive_row["applicability_basis"]["does_not_apply_if_package_terms"],
                [
                    "not subject to a categorical exclusion",
                    "categorical exclusion path is not used",
                ],
            )

    def test_nepa_ce_rule_pack_has_explicit_non_applicability_guards(self) -> None:
        rule_pack = json.loads(
            Path("config/compliance_rule_pack_nepa_ea_v0.json").read_text(
                encoding="utf-8"
            )
        )
        validation = validate_rule_pack(rule_pack)
        rules_by_id = {rule["id"]: rule for rule in rule_pack["rules"]}
        guarded_rule_ids = [
            "nepa_4336c_ce_adoption_screen",
            "usda_nepa_ce_fanec_7cfr_1b3",
            "usda_nepa_subcomponent_ce_7cfr_1b4",
        ]

        self.assertTrue(validation["passed"])
        for rule_id in guarded_rule_ids:
            with self.subTest(rule_id=rule_id):
                rule = rules_by_id[rule_id]
                self.assertGreaterEqual(len(rule["applies_if_package_term_groups"]), 2)
                self.assertTrue(rule["does_not_apply_if_package_terms"])

    def test_nepa_statute_rule_routes_package_evidence_to_purpose_need_terms(self) -> None:
        rule_pack = json.loads(
            Path("config/compliance_rule_pack_nepa_ea_v0.json").read_text(
                encoding="utf-8"
            )
        )
        rules_by_id = {rule["id"]: rule for rule in rule_pack["rules"]}
        rule = rules_by_id["nepa_statute_chapter_55"]

        self.assertIn("purpose and need", rule["package_query"])
        self.assertEqual(
            rule["package_terms"],
            [
                "purpose and need for action",
                "purpose and need",
                "environmental assessment",
            ],
        )

    def test_programmatic_tiering_rule_declares_expected_section_context(self) -> None:
        rule_pack = json.loads(
            Path("config/compliance_rule_pack_nepa_ea_v0.json").read_text(
                encoding="utf-8"
            )
        )
        validation = validate_rule_pack(rule_pack)
        rules_by_id = {rule["id"]: rule for rule in rule_pack["rules"]}
        rule = rules_by_id["nepa_4336b_programmatic_tiering"]

        self.assertTrue(validation["passed"])
        self.assertEqual(
            rule["package_section_term_groups"],
            [
                ["alternatives", "alternative", "no action alternative"],
                [
                    "environmental consequences",
                    "environmental effects",
                    "direct and indirect effects",
                    "cumulative effects",
                ],
            ],
        )

    def test_rule_pack_rejects_invalid_package_section_preferences(self) -> None:
        rule_pack = _rule_pack()
        rule_pack["rules"][0]["package_section_terms"] = []
        rule_pack["rules"][0]["package_section_term_groups"] = [
            ["purpose and need"],
            [],
        ]

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        section_check = _check(validation, "rule_package_section_preferences_are_valid")
        self.assertFalse(section_check["passed"])
        self.assertEqual(
            section_check["details"]["failures"],
            [
                {
                    "rule_id": "purpose_need",
                    "invalid": [
                        "package_section_term_groups",
                        "package_section_terms",
                    ],
                }
            ],
        )

    def test_package_search_prefers_rule_declared_section_context(self) -> None:
        chunks = [
            _chunk(
                source_set_id="ea-package-unit",
                source_record_id="EA-PACKAGE-001",
                title="Final Environmental Assessment",
                document_role="ea_package",
                authority_level="project_record",
                citation_label="EA-PACKAGE-001 | final EA | artifact abc123",
                text=(
                    "This environmental assessment tiers to and incorporates by reference "
                    "the programmatic final environmental impact statement. Lands protect "
                    "threatened and endangered species and important cultural resources."
                ),
            ),
            _chunk(
                source_set_id="ea-package-unit",
                source_record_id="EA-PACKAGE-001",
                title="Final Environmental Assessment",
                document_role="ea_package",
                authority_level="project_record",
                citation_label="EA-PACKAGE-001 | final EA | artifact abc123",
                text=(
                    "## 3.0 Environmental Effects\n\n"
                    "This section summarizes the environmental effects of the alternative "
                    "actions, including the no action alternative. This analysis tiers to "
                    "the Final Environmental Impact Statement for the land management plan."
                ),
            )
            | {
                "chunk_id": "chunk:EA-PACKAGE-001-env-effects",
                "chunk_index": 1,
            },
        ]

        result = _search_package_chunks(
            chunks,
            query="tiers to incorporates by reference programmatic final environmental impact statement",
            required_terms=[
                "tiers to",
                "incorporates by reference",
                "programmatic",
                "final environmental impact statement",
            ],
            preferred_term_groups=[
                ["alternatives", "alternative", "no action alternative"],
                [
                    "environmental consequences",
                    "environmental effects",
                    "direct and indirect effects",
                    "cumulative effects",
                ],
            ],
            limit=2,
        )

        self.assertEqual(result["results"][0]["chunk_id"], "chunk:EA-PACKAGE-001-env-effects")
        self.assertIn(
            "Environmental Effects",
            result["results"][0]["evidence_span"]["text"],
        )
        self.assertIn(
            "alternative actions",
            result["results"][0]["evidence_span"]["text"],
        )
