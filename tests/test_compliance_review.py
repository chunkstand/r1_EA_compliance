from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.compliance_review_eval import _normalized_eval_findings_by_rule
from usfs_r1_ea_sources.compliance_review_eval import (
    _validate_compliance_review_eval_cases_against_rule_pack,
)
from usfs_r1_ea_sources.compliance_review_eval import run_compliance_review_eval
from usfs_r1_ea_sources.compliance_coverage import _load_eval_cases
from usfs_r1_ea_sources.compliance_coverage import run_compliance_coverage
from usfs_r1_ea_sources.compliance_gold_eval import _effective_cases_for_rule_pack
from usfs_r1_ea_sources.compliance_gold_eval import _gold_rule_pack_match_mode
from usfs_r1_ea_sources.compliance_gold_eval import run_compliance_gold_eval
from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.ea_review import _search_package_chunks
from usfs_r1_ea_sources.ea_review import run_ea_review
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval
from usfs_r1_ea_sources.forest_plan_components import build_forest_plan_component_inventory
from usfs_r1_ea_sources.records import sha256_file
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links
from usfs_r1_ea_sources.rule_claim_binding import default_rule_claim_links_dir
from usfs_r1_ea_sources.rule_packs import validate_rule_pack


class ComplianceReviewTests(unittest.TestCase):
    def test_v1_land_exchange_rules_are_first_class_compliance_contract(self) -> None:
        rule_pack = json.loads(
            Path("config/compliance_rule_pack_nepa_ea_v0.json").read_text(encoding="utf-8")
        )
        coverage = json.loads(
            Path("config/compliance_rule_pack_coverage_nepa_ea_v0.json").read_text(
                encoding="utf-8"
            )
        )
        eval_contract = json.loads(
            Path("config/compliance_review_eval_seed.json").read_text(
                encoding="utf-8"
            )
        )
        eval_cases = {case["id"]: case for case in eval_contract["cases"]}
        v1_contract = json.loads(
            Path("config/v1_ecid_real_ea_eval.json").read_text(encoding="utf-8")
        )

        rule = _rule_by_id(rule_pack, "flpma_section_206_land_exchange")
        self.assertEqual(rule["authority_source_record_id"], "R1EA-146")
        self.assertEqual(rule["applicability_mode"], "conditional")
        self.assertEqual(
            rule["source_filters"],
            {"document_role": "law", "source_record_id": "R1EA-146"},
        )
        self.assertIn("FLPMA", rule["applies_if_package_terms"])
        self.assertIn("cash equalization", rule["package_terms"])

        coverage_item = _coverage_item_by_rule_id(
            coverage,
            "flpma_section_206_land_exchange",
        )
        self.assertEqual(coverage_item["source_record_ids"], ["R1EA-146"])
        self.assertEqual(
            set(coverage_item["eval_case_ids"]),
            {
                "all-authorities-pass",
                "baseline-nepa-only",
                "unrelated-package-produces-baseline-gaps",
            },
        )

        self.assertEqual(
            eval_cases["all-authorities-pass"]["expected_statuses"][
                "flpma_section_206_land_exchange"
            ],
            "pass",
        )
        self.assertEqual(
            eval_cases["all-authorities-pass"]["expected_source_record_ids"][
                "flpma_section_206_land_exchange"
            ],
            ["R1EA-146"],
        )
        self.assertEqual(
            eval_cases["baseline-nepa-only"]["expected_statuses"][
                "flpma_section_206_land_exchange"
            ],
            "not_applicable",
        )
        self.assertEqual(
            eval_cases["unrelated-package-produces-baseline-gaps"]["expected_statuses"][
                "flpma_section_206_land_exchange"
            ],
            "not_applicable",
        )

        conditional_expectations = {
            expectation["rule_id"]: expectation
            for expectation in v1_contract["conditional_source_expectations"]
        }
        land_exchange_contracts = {
            "flpma_section_206_land_exchange": {
                "source_record_ids": ["R1EA-146"],
                "document_roles": ["law"],
                "family_id": "land_exchange_statutory_authorities",
                "mode": "conditional",
            },
            "land_exchange_statutory_authorities": {
                "source_record_ids": ["R1EA-137"],
                "document_roles": ["law"],
                "family_id": "land_exchange_statutory_authorities",
                "mode": "conditional",
            },
            "land_exchange_regulatory_requirements": {
                "source_record_ids": ["R1EA-124"],
                "document_roles": ["regulation"],
                "family_id": "land_exchange_regulatory_requirements",
                "mode": "conditional",
            },
            "land_exchange_fs_policy_and_project_references": {
                "source_record_ids": ["R1EA-150"],
                "document_roles": ["agency_policy"],
                "family_id": "land_exchange_fs_policy_and_project_references",
                "mode": "conditional",
            },
        }
        for rule_id, expected in land_exchange_contracts.items():
            rule = _rule_by_id(rule_pack, rule_id)
            self.assertEqual(rule["authority_source_record_id"], expected["source_record_ids"][0])
            self.assertEqual(rule["applicability_mode"], expected["mode"])
            self.assertEqual(rule["authority_family_id"], expected["family_id"])
            self.assertIn("land exchange", [term.lower() for term in rule["package_terms"]])
            generic_exchange_terms = {
                "acquisition",
                "appraisal",
                "cash equalization",
                "closing",
                "disposal",
                "easement",
                "equal value",
                "feasibility analysis",
                "mineral reservation",
                "outstanding rights",
                "public interest determination",
                "reservation",
                "reservations",
                "segregation",
                "title evidence",
            }
            singleton_trigger_groups = {
                tuple(term.lower() for term in group)
                for group in rule.get("applies_if_package_term_groups", [])
                if len(group) == 1
            }
            self.assertFalse(
                {(term,) for term in generic_exchange_terms} & singleton_trigger_groups
            )

            coverage_item = _coverage_item_by_rule_id(coverage, rule_id)
            self.assertEqual(coverage_item["source_record_ids"], expected["source_record_ids"])
            self.assertEqual(
                set(coverage_item["eval_case_ids"]),
                {
                    "all-authorities-pass",
                    "baseline-nepa-only",
                    "unrelated-package-produces-baseline-gaps",
                },
            )

            self.assertEqual(eval_cases["all-authorities-pass"]["expected_statuses"][rule_id], "pass")
            self.assertEqual(
                eval_cases["baseline-nepa-only"]["expected_statuses"][rule_id],
                "not_applicable",
            )
            self.assertEqual(
                eval_cases["unrelated-package-produces-baseline-gaps"]["expected_statuses"][rule_id],
                "not_applicable",
            )

            v1_expectation = conditional_expectations[rule_id]
            self.assertEqual(v1_expectation["expected_applicability"], "applicable")
            self.assertEqual(
                v1_expectation["expected_source_record_ids"],
                expected["source_record_ids"],
            )
            self.assertEqual(
                v1_expectation["expected_source_document_roles"],
                expected["document_roles"],
            )

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
            matrix_row = matrix["rows"][0]
            self.assertEqual(matrix_row["candidate_authority_id"], "candidate:purpose_need")
            self.assertEqual(matrix_row["applicability_decision_id"], "decision:purpose_need")
            self.assertEqual(matrix_row["authority_family_ids"], ["unit_purpose_need"])
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

    def test_phase_eval_rejects_stale_compliance_coverage_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
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
            coverage_result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=_write_coverage_matrix(Path(tmp)),
                eval_file=eval_path,
                links_path=link_result.links_path,
            )
            coverage_summary = json.loads(coverage_result.output_path.read_text(encoding="utf-8"))
            coverage_summary["source_set_id"] = "source-set-other"
            coverage_result.output_path.write_text(
                json.dumps(coverage_summary, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            coverage_phase = _phase(phase_result.summary, "compliance_coverage")
            self.assertFalse(coverage_phase["passed"])
            self.assertFalse(coverage_phase["reviewer_ready"])
            self.assertTrue(coverage_phase["details"]["coverage_passed"])
            self.assertFalse(coverage_phase["details"]["source_set_matches"])

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

    def test_review_phase_eval_prefers_review_scoped_compliance_gold_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "review-test"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            gold_path = _write_gold_eval_file(Path(tmp))
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)

            run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                gold_file=gold_path,
                results_dir=review_dir,
            )
            global_gold_dir = output_dir / "reviews" / "compliance_gold_eval"
            global_gold_dir.mkdir(parents=True, exist_ok=True)
            (global_gold_dir / "compliance_gold_eval_results.json").write_text(
                json.dumps(
                    {
                        "source_set_id": "source-set-other",
                        "passed": True,
                        "promotion_ready": True,
                        "rule_pack_id": "unit-nepa-ea",
                        "rule_pack_version": "0.4.0",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            gold_phase = _phase(phase_result.summary, "compliance_gold_eval")
            self.assertEqual(
                gold_phase["details"]["gold_eval_path"],
                str(review_dir / "compliance_gold_eval_results.json"),
            )
            self.assertTrue(gold_phase["details"]["source_set_matches"])
            self.assertEqual(gold_phase["details"]["case_count"], 3)

    def test_review_phase_eval_ignores_unrelated_global_gold_without_review_scoped_gold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "review-test"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            global_gold_dir = output_dir / "reviews" / "compliance_gold_eval"
            global_gold_dir.mkdir(parents=True, exist_ok=True)
            (global_gold_dir / "compliance_gold_eval_results.json").write_text(
                json.dumps(
                    {
                        "source_set_id": "source-set-other",
                        "passed": True,
                        "promotion_ready": True,
                        "rule_pack_id": "unit-nepa-ea",
                        "rule_pack_version": "0.4.0",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            phase_names = {phase["name"] for phase in phase_result.summary["phases"]}
            self.assertNotIn("compliance_gold_eval", phase_names)
            self.assertTrue(phase_result.summary["reviewer_ready"])

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

    def test_phase_eval_ignores_unrelated_compliance_gold_source_set_for_source_set_replay(self) -> None:
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
            _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)
            gold_summary = json.loads(result.output_path.read_text(encoding="utf-8"))
            gold_summary["source_set_id"] = "source-set-other"
            result.output_path.write_text(
                json.dumps(gold_summary, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertTrue(phase_result.summary["reviewer_ready"])
            phase_names = {phase["name"] for phase in phase_result.summary["phases"]}
            self.assertNotIn("compliance_gold_eval", phase_names)

    def test_phase_eval_can_include_compliance_review_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 17)
            self.assertEqual(result.summary["review_id"], "phase-review")
            self.assertFalse(result.summary["declared_review_contract"])
            self.assertFalse(result.summary["contract_backed_promotion_ready"])
            self.assertEqual(
                result.review_output_path,
                output_dir / "reviews" / "phase-review" / "phase_eval_results.json",
            )
            self.assertTrue(result.review_output_path.exists())
            review_phase_summary = json.loads(result.review_output_path.read_text(encoding="utf-8"))
            self.assertEqual(review_phase_summary["review_id"], "phase-review")
            self.assertTrue(review_phase_summary["reviewer_ready"])
            evaluation_coverage_phase = _phase(result.summary, "evaluation_coverage")
            self.assertTrue(evaluation_coverage_phase["passed"])
            self.assertEqual(
                evaluation_coverage_phase["details"]["review_direct_eval_status"],
                "not_required_for_ad_hoc_review",
            )
            claim_phase = _phase(result.summary, "claim_extraction")
            self.assertTrue(claim_phase["passed"])
            self.assertTrue(claim_phase["reviewer_ready"])
            rule_claim_phase = _phase(result.summary, "rule_claim_binding")
            self.assertTrue(rule_claim_phase["passed"])
            self.assertTrue(rule_claim_phase["reviewer_ready"])
            compliance_phase = _phase(result.summary, "compliance_review")
            self.assertTrue(compliance_phase["passed"])
            self.assertTrue(compliance_phase["reviewer_ready"])
            self.assertEqual(compliance_phase["details"]["rule_pack_id"], "generated-unit-nepa-ea")
            self.assertTrue(compliance_phase["details"]["matrix_exists"])
            self.assertTrue(compliance_phase["details"]["matrix_pdf_exists"])
            self.assertTrue(compliance_phase["details"]["matrix_pdf_header_valid"])
            self.assertTrue(compliance_phase["details"]["matrix_schema_matches"])
            self.assertTrue(compliance_phase["details"]["matrix_row_count_matches"])

    def test_review_phase_eval_uses_canonical_rule_claim_direct_eval_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "phase-review"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            review_result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )

            base_rule_claim_eval_path = (
                output_dir
                / "derived"
                / source_set_id
                / "rule_claim_links"
                / "nepa-ea-v0"
                / "0.4.0"
                / "rule_claim_link_eval_results.json"
            )
            base_rule_claim_eval_path.write_text(
                json.dumps(
                    _direct_eval_result_payload(
                        contract_path=Path("config/rule_claim_link_eval_seed.json"),
                        eval_id="rule-claim-direct-eval-v1",
                        source_set_id=source_set_id,
                    ),
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            selected_rule_claim_eval_path = (
                Path(review_result.summary["rule_claim_summary_path"]).parent
                / "rule_claim_link_eval_results.json"
            )
            selected_rule_claim_eval_path.write_text(
                json.dumps(
                    _direct_eval_result_payload(
                        contract_path=Path("config/rule_claim_link_eval_seed.json"),
                        eval_id="rule-claim-direct-eval-v1",
                        source_set_id="source-set-other",
                    ),
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
            )

            rule_claim_phase = _phase(phase_result.summary, "rule_claim_binding")
            self.assertTrue(rule_claim_phase["passed"])
            self.assertTrue(rule_claim_phase["reviewer_ready"])
            self.assertEqual(
                Path(rule_claim_phase["details"]["direct_eval_summary_path"]).resolve(),
                base_rule_claim_eval_path.resolve(),
            )
            self.assertEqual(
                rule_claim_phase["details"]["direct_eval_status"],
                "direct_eval_present",
            )

    def test_phase_eval_can_include_final_qa_certification_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "phase-review"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_final_qa_phase_outputs(
                output_dir / "reviews" / review_id,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 18)
            final_qa_phase = _phase(result.summary, "final_qa_certification_report")
            self.assertTrue(final_qa_phase["passed"])
            self.assertTrue(final_qa_phase["reviewer_ready"])
            self.assertTrue(final_qa_phase["details"]["validation_result_passed"])
            self.assertEqual(final_qa_phase["details"]["failed_check_count"], 0)

    def test_phase_eval_accepts_base_gold_eval_for_generated_rule_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need. Mitigation measures support a FONSI.",
            )
            base_rule_pack_path = _write_rule_pack(Path(tmp))
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            gold_path = _write_gold_eval_file(Path(tmp))
            gold_result = run_compliance_gold_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=base_rule_pack_path,
                gold_file=gold_path,
            )
            self.assertTrue(gold_result.summary["passed"])

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            gold_phase = _phase(result.summary, "compliance_gold_eval")
            self.assertTrue(gold_phase["passed"])
            self.assertTrue(gold_phase["reviewer_ready"])
            self.assertEqual(gold_phase["details"]["rule_pack_match_mode"], "generated_base")
            self.assertTrue(gold_phase["details"]["effective_promotion_ready"])
            self.assertEqual(
                gold_phase["details"]["generated_base_rule_pack_id"],
                "unit-nepa-ea",
            )

    def test_phase_eval_can_include_component_adjudication_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_adjudication_eval(
                output_dir / "reviews" / "phase-review",
                source_set_id=source_set_id,
                review_id="phase-review",
                passed=True,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 18)
            adjudication_phase = _phase(result.summary, "forest_plan_component_adjudication")
            self.assertTrue(adjudication_phase["passed"])
            self.assertTrue(adjudication_phase["reviewer_ready"])
            self.assertEqual(adjudication_phase["details"]["queue_item_count"], 2)
            self.assertEqual(
                adjudication_phase["details"]["adjudication_completion_rate"],
                1.0,
            )
            self.assertEqual(adjudication_phase["details"]["real_ea_omission_count"], 2)
            self.assertEqual(adjudication_phase["details"]["system_miss_count"], 0)
            self.assertEqual(
                adjudication_phase["details"]["adjudication_outcome_counts"],
                {"real_ea_omission": 2},
            )

    def test_phase_eval_rejects_stale_component_adjudication_queue_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="stale-adjudication-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            review_dir = output_dir / "reviews" / "stale-adjudication-review"
            _write_component_adjudication_eval(
                review_dir,
                source_set_id=source_set_id,
                review_id="stale-adjudication-review",
                passed=True,
            )
            (review_dir / "forest_plan_reviewer_resolution_queue.json").write_text(
                json.dumps(
                    {
                        "schema_version": "forest-plan-reviewer-resolution-queue-v0",
                        "review_id": "stale-adjudication-review",
                        "source_set_id": source_set_id,
                        "item_count": 0,
                        "items": [],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="stale-adjudication-review",
            )

            self.assertFalse(result.summary["reviewer_ready"])
            adjudication_phase = _phase(result.summary, "forest_plan_component_adjudication")
            self.assertFalse(adjudication_phase["passed"])
            self.assertIn(
                "queue_item_count_mismatch",
                adjudication_phase["details"]["failed_checks"],
            )
            self.assertEqual(adjudication_phase["details"]["queue_item_count"], 2)
            self.assertEqual(adjudication_phase["details"]["current_queue_item_count"], 0)

    def test_phase_eval_can_include_component_eval_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_eval(
                output_dir / "reviews" / "phase-review",
                source_set_id=source_set_id,
                review_id="phase-review",
                passed=True,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 18)
            component_eval_phase = _phase(result.summary, "forest_plan_component_eval")
            self.assertTrue(component_eval_phase["passed"])
            self.assertTrue(component_eval_phase["reviewer_ready"])
            self.assertEqual(component_eval_phase["details"]["case_count"], 3)
            self.assertEqual(
                component_eval_phase["details"]["metrics"]["applicable_standard_recall"],
                1.0,
            )

    def test_phase_eval_rejects_component_eval_schema_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="phase-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_eval(
                output_dir / "reviews" / "phase-review",
                source_set_id=source_set_id,
                review_id="phase-review",
                passed=True,
                schema_version="wrong-schema",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertFalse(result.summary["reviewer_ready"])
            component_eval_phase = _phase(result.summary, "forest_plan_component_eval")
            self.assertFalse(component_eval_phase["passed"])
            self.assertEqual(
                component_eval_phase["details"]["failed_checks"],
                ["schema_version_mismatch"],
            )

    def test_phase_eval_rejects_pending_component_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="pending-adjudication-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            _write_component_adjudication_eval(
                output_dir / "reviews" / "pending-adjudication-review",
                source_set_id=source_set_id,
                review_id="pending-adjudication-review",
                passed=False,
                pending_count=1,
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="pending-adjudication-review",
            )

            self.assertFalse(result.summary["reviewer_ready"])
            adjudication_phase = _phase(result.summary, "forest_plan_component_adjudication")
            self.assertFalse(adjudication_phase["passed"])
            self.assertFalse(adjudication_phase["reviewer_ready"])
            self.assertIn("adjudication_eval_failed", adjudication_phase["details"]["failed_checks"])
            self.assertEqual(adjudication_phase["details"]["pending_adjudication_count"], 1)
            self.assertEqual(
                adjudication_phase["details"]["failure_category_counts"],
                {"adjudication_pending": 1},
            )

    def test_phase_eval_rejects_missing_compliance_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="missing-matrix-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            result.compliance_matrix_path.unlink()

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="missing-matrix-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["matrix_exists"])
            self.assertIn(
                "matrix_exists",
                compliance_phase["details"]["failed_artifact_checks"],
            )

    def test_phase_eval_rejects_missing_compliance_matrix_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="missing-matrix-pdf-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            result.compliance_matrix_pdf_path.unlink()

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="missing-matrix-pdf-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["matrix_pdf_exists"])
            self.assertIn(
                "matrix_pdf_exists",
                compliance_phase["details"]["failed_artifact_checks"],
            )

    def test_phase_eval_rejects_stale_compliance_review_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = _run_generated_compliance_review(
                output_dir=output_dir,
                review_id="stale-review",
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=rule_pack_path,
            )
            report = json.loads(result.compliance_review_path.read_text(encoding="utf-8"))
            report["summary"]["source_set_id"] = "source-set-other"
            result.compliance_review_path.write_text(
                json.dumps(report, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="stale-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["source_set_matches"])


_CUSTER_PLAN_COMPONENT_TEXT = (
    "The 2022 Custer Gallatin Land Management Plan includes "
    "Plan Components-Crazy Mountains Backcountry Area (CMBCA). "
    "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads shall not be allowed."
)

_BEAVERHEAD_PLAN_COMPONENT_TEXT = (
    "The 2009 Beaverhead-Deerlodge Forest Plan includes the Big Hole Landscape and the West Big "
    "Hole Management Area. Inventoried Roadless Area and recommended wilderness direction apply "
    "where mapped. "
    "West Big Hole Management Area Standards Standard 1: New permanent or temporary roads "
    "shall not be allowed."
)

_FLATHEAD_PLAN_COMPONENT_TEXT = (
    "The 2018 Flathead National Forest Land Management Plan includes the Hungry Horse Geographic "
    "Area and the Jewel Basin Hiking Area. Jewel Basin Recommended Wilderness Area direction "
    "and Inventoried Roadless Area direction apply where mapped. Standard FW-STD-WTR-01 New "
    "stream diversions and associated ditches shall have screens placed on them to prevent "
    "capture of fish and other aquatic organisms. Suitability MA1b-SUIT-07 The Jewel Basin "
    "hiking area is not suitable for motorized use, mechanized transport, and stock use."
)

_CUSTER_SOURCES = (
    (
        "R1PLAN-custer-gallatin-nf-01",
        "Custer Gallatin land management plan page",
        (
            "The Custer Gallatin land management plan page lists the current plan, "
            "record of decision, final environmental impact statement volumes, "
            "biological assessment, and biological opinion."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-02",
        "2022 Custer Gallatin Land Management Plan PDF",
        _CUSTER_PLAN_COMPONENT_TEXT,
    ),
    (
        "R1PLAN-custer-gallatin-nf-03",
        "Custer Gallatin Land Management Plan Record of Decision PDF",
        "The record of decision identifies the selected alternative and plan approval.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-04",
        "Custer Gallatin Land Management Plan FEIS Volume 1 PDF",
        "The final environmental impact statement volume 1 describes effects context.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-05",
        "Custer Gallatin Land Management Plan FEIS Volume 2 PDF",
        "The final environmental impact statement volume 2 discusses plan allocations.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-06",
        "Custer Gallatin LMP Biological Assessment PDF",
        "The biological assessment analyzes species and habitat effects.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-07",
        "Custer Gallatin LMP Biological Opinion PDF",
        "The biological opinion documents ESA section 7 consultation.",
    ),
)

_BEAVERHEAD_SOURCES = (
    (
        "R1PLAN-beaverhead-deerlodge-nf-01",
        "Beaverhead-Deerlodge planning page",
        (
            "The Beaverhead-Deerlodge planning page lists the forest plan, corrected FEIS, "
            "records of decision, and biological assessment and biological opinion support records."
        ),
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-02",
        "2009 Beaverhead-Deerlodge Forest Plan PDF",
        _BEAVERHEAD_PLAN_COMPONENT_TEXT,
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-03",
        "Beaverhead-Deerlodge Corrected FEIS PDF",
        (
            "The final environmental impact statement describes travel management, recreation "
            "allocations, recommended wilderness, and roadless areas."
        ),
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-04",
        "Beaverhead-Deerlodge Record of Decision PDF",
        "The record of decision identifies the selected alternative and plan approval.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-05",
        "Beaverhead-Deerlodge Travel Management Record of Decision PDF",
        (
            "The record of decision enacts travel management direction for summer non-motorized "
            "and winter non-motorized allocations and recommended wilderness closures."
        ),
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-18",
        "Beaverhead-Deerlodge Canada Lynx Biological Assessment PDF",
        "The biological assessment evaluates Canada lynx habitat and critical habitat under ESA.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-19",
        "Beaverhead-Deerlodge Canada Lynx Biological Opinion PDF",
        "The biological opinion documents Canada lynx ESA consultation terms and conditions.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-22",
        "Beaverhead-Deerlodge Grizzly Bear Biological Assessment PDF",
        "The biological assessment evaluates grizzly bear action area effects under ESA.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-23",
        "Beaverhead-Deerlodge Grizzly Bear Biological Opinion PDF",
        "The biological opinion discusses grizzly bear ESA reinitiation and consultation terms.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-24",
        "Beaverhead-Deerlodge Supplemental Grizzly Bear Biological Assessment PDF",
        "The supplemental biological assessment describes grizzly bear action area effects.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-25",
        "Beaverhead-Deerlodge Supplemental Grizzly Bear Biological Opinion PDF",
        "The supplemental biological opinion discusses grizzly bear consultation and reinitiation.",
    ),
)

_FLATHEAD_SOURCES = (
    (
        "R1PLAN-flathead-nf-01",
        "Flathead planning page",
        (
            "The Flathead planning page lists the forest plan, FEIS volumes, record of decision, "
            "monitoring program, biennial monitoring evaluation report, administrative change, "
            "biological assessment, and biological opinions."
        ),
    ),
    (
        "R1PLAN-flathead-nf-02",
        "2018 Flathead National Forest Land Management Plan PDF",
        _FLATHEAD_PLAN_COMPONENT_TEXT,
    ),
    (
        "R1PLAN-flathead-nf-03",
        "Flathead Record of Decision PDF",
        (
            "The record of decision identifies the selected alternative, plan approval, Hungry "
            "Horse-Glacier View Ranger District, and recommended wilderness areas."
        ),
    ),
    (
        "R1PLAN-flathead-nf-04",
        "Flathead FEIS Volume 1 PDF",
        (
            "The final environmental impact statement discusses alternatives, effects, "
            "recommended wilderness, inventoried roadless areas, and wild and scenic rivers."
        ),
    ),
    (
        "R1PLAN-flathead-nf-05",
        "Flathead FEIS Appendices PDF",
        (
            "The final environmental impact statement appendices provide supporting analysis, "
            "methods, and glossary context for Flathead plan interpretation."
        ),
    ),
    (
        "R1PLAN-flathead-nf-06",
        "Flathead Biological Assessment PDF",
        (
            "The biological assessment analyzes Canada lynx critical habitat, grizzly bear, and "
            "the Northern Continental Divide Ecosystem."
        ),
    ),
    (
        "R1PLAN-flathead-nf-07",
        "Flathead Biological Opinion Bull Trout PDF",
        (
            "The biological opinion addresses bull trout incidental take and terms and "
            "conditions."
        ),
    ),
    (
        "R1PLAN-flathead-nf-08",
        "Flathead Monitoring Program PDF",
        (
            "The monitoring program includes monitoring questions and indicators under the 2012 "
            "planning rule."
        ),
    ),
    (
        "R1PLAN-flathead-nf-09",
        "Flathead Biennial Monitoring Evaluation Report PDF",
        (
            "The Biennial Monitoring Evaluation Report for the Flathead National Forest reviews "
            "visitor use and monitoring questions."
        ),
    ),
    (
        "R1PLAN-flathead-nf-10",
        "Flathead Administrative Change PDF",
        (
            "The Administrative Change updates Jewel Basin, Limestone-Dean Ridge, and "
            "Tuchuck-Whale Recommended Wilderness Areas."
        ),
    ),
    (
        "R1PLAN-flathead-nf-12",
        "Flathead FEIS Volume 2 PDF",
        (
            "The final environmental impact statement volume 2 discusses inventoried roadless "
            "areas, designated wilderness, eligible wild and scenic rivers, and recommended "
            "wilderness areas."
        ),
    ),
    (
        "R1PLAN-flathead-nf-16",
        "Flathead Biological Opinion Grizzly Bear PDF",
        (
            "The biological opinion addresses grizzly bear habitat in the Northern Continental "
            "Divide Ecosystem primary conservation area."
        ),
    ),
)


def _build_source_library(output_dir: Path, source_set_id: str) -> None:
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=["R1EA-001", "R1EA-002"],
    )
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-001",
                title="EA requirements",
                document_role="regulation",
                authority_level="federal",
                citation_label="R1EA-001 | EA requirements | artifact abc123",
                text="An environmental assessment should describe the purpose and need.",
            ),
            _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-002",
                title="FONSI mitigation",
                document_role="regulation",
                authority_level="federal",
                citation_label="R1EA-002 | FONSI mitigation | artifact def456",
                text="A finding of no significant impact should address mitigation measures.",
            ),
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            "R1EA-001": ["Purpose and need"],
            "R1EA-002": ["Mitigation"],
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)


def _build_custer_compliance_source_library(output_dir: Path, source_set_id: str) -> None:
    source_record_ids = [source_record_id for source_record_id, _title, _text in _CUSTER_SOURCES]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=source_record_ids,
    )
    chunks_path = _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label=f"{source_record_id} | {title} | artifact abc123",
                text=text,
            )
            for source_record_id, title, text in _CUSTER_SOURCES
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [title]
            for source_record_id, title, _text in _CUSTER_SOURCES
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    build_forest_plan_component_inventory(
        output_dir=output_dir,
        source_set_id=source_set_id,
        source_record_id="R1PLAN-custer-gallatin-nf-02",
        forest_unit_id="custer-gallatin-nf",
        plan_version="2022",
        chunks_path=chunks_path,
        management_area_ids=["mgmt-crazy-mountains-bca"],
    )


def _build_beaverhead_compliance_source_library(output_dir: Path, source_set_id: str) -> None:
    source_record_ids = [source_record_id for source_record_id, _title, _text in _BEAVERHEAD_SOURCES]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=source_record_ids,
    )
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label=f"{source_record_id} | {title} | artifact abc123",
                text=text,
            )
            for source_record_id, title, text in _BEAVERHEAD_SOURCES
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [title]
            for source_record_id, title, _text in _BEAVERHEAD_SOURCES
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    _write_beaverhead_component_inventory(output_dir, source_set_id)


def _build_flathead_compliance_source_library(output_dir: Path, source_set_id: str) -> None:
    source_record_ids = [source_record_id for source_record_id, _title, _text in _FLATHEAD_SOURCES]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=source_record_ids,
    )
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label=f"{source_record_id} | {title} | artifact abc123",
                text=text,
            )
            for source_record_id, title, text in _FLATHEAD_SOURCES
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [title]
            for source_record_id, title, _text in _FLATHEAD_SOURCES
        },
    )
    _write_extraction_accuracy_audit(
        output_dir,
        source_set_id,
        admitted_source_record_ids=source_record_ids,
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    _write_flathead_component_inventory(output_dir, source_set_id)


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "extraction_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": len(source_record_ids),
        "selected_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "filters": {"id": None, "parser": None, "limit": None},
    }
    (diagnostics_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "source_set_manifest.json").write_text(
        json.dumps({"source_set_id": source_set_id}, sort_keys=True),
        encoding="utf-8",
    )
    (catalog_dir / "catalog_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )


def _write_extraction_accuracy_audit(
    output_dir: Path,
    source_set_id: str,
    *,
    admitted_source_record_ids: list[str],
) -> Path:
    path = output_dir / "derived" / source_set_id / "diagnostics" / "extraction_accuracy_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_set_id": source_set_id,
        "passed": True,
        "knowledge_base_admitted_source_record_ids": admitted_source_record_ids,
        "knowledge_base_blocked_source_record_ids": [],
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        text_path = output_dir / chunk["source_text_path"]
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(chunk["text"], encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_beaverhead_component_inventory(output_dir: Path, source_set_id: str) -> None:
    components_dir = output_dir / "derived" / source_set_id / "forest_plan_components"
    inventory_path = components_dir / "component_inventory.json"
    coverage_path = components_dir / "component_inventory_build_coverage.json"
    components_dir.mkdir(parents=True, exist_ok=True)
    source_record_id = "R1PLAN-beaverhead-deerlodge-nf-02"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    content_sha256 = hashlib.sha256(_BEAVERHEAD_PLAN_COMPONENT_TEXT.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
    provenance = {
        "entity": {
            "type": "forest_plan_component",
            "source_record_id": source_record_id,
            "source_chunk_ids": source_chunk_ids,
            "artifact_sha256": artifact_sha256,
            "content_sha256": content_sha256,
        },
        "activity": {
            "type": "component_inventory_fixture",
            "created_at": "2026-05-11T00:00:00Z",
        },
        "agent": {
            "type": "deterministic_test_fixture",
            "name": "tests/test_compliance_review.py",
            "version": "forest-plan-component-inventory-v0",
        },
    }
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "beaverhead-test-components-v0",
        "forest_unit_id": "beaverhead-deerlodge-nf",
        "plan_version": "2009",
        "source_set_id": source_set_id,
        "components": [
            {
                "component_id": "bdnf-west-big-hole-std-01",
                "component_type": "standard",
                "component_text": (
                    "Standards (BD-STD-WBH) 01 New permanent or temporary roads shall not be "
                    "allowed."
                ),
                "forest_unit_id": "beaverhead-deerlodge-nf",
                "plan_version": "2009",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "section_id": "west-big-hole-standard-1",
                "section_heading": "West Big Hole Management Area Standards",
                "page": None,
                "citation_label": (
                    "R1PLAN-beaverhead-deerlodge-nf-02 | test plan | artifact abc123"
                ),
                "geographic_area_ids": ["geo-big-hole-landscape"],
                "management_area_ids": ["mgmt-west-big-hole"],
                "overlay_ids": ["overlay-inventoried-roadless-area"],
                "resource_topics": ["travel management"],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "activity_tags": ["new roads"],
                "package_evidence_terms": ["new permanent or temporary roads"],
                "provenance": provenance,
            }
        ],
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    coverage = {
        "schema_version": "forest-plan-component-inventory-build-coverage-v0",
        "created_at": "2026-05-11T00:00:00Z",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunks_path": str(output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"),
        "selected_chunk_count": 1,
        "detected_component_count": 1,
        "detected_standard_count": 1,
        "built_component_count": 1,
        "built_standard_count": 1,
        "missing_component_ids": [],
        "missing_standard_ids": [],
        "duplicate_component_ids": [],
        "duplicate_standard_ids": [],
        "validation_errors": [],
        "detected_component_labels": [
            {
                "component_id": "bdnf-west-big-hole-std-01",
                "component_type": "standard",
                "label": "Standards",
                "code": "West Big Hole Management Area",
                "number": "1",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "West Big Hole Management Area Standards",
            }
        ],
        "detected_standard_labels": [
            {
                "component_id": "bdnf-west-big-hole-std-01",
                "component_type": "standard",
                "label": "Standards",
                "code": "West Big Hole Management Area",
                "number": "1",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "West Big Hole Management Area Standards",
            }
        ],
        "passed": True,
        "checks": [
            {"name": "selected_forest_plan_chunks_present", "passed": True, "details": {}},
            {"name": "labeled_components_detected", "passed": True, "details": {}},
            {"name": "standard_components_detected", "passed": True, "details": {}},
            {"name": "all_detected_components_built", "passed": True, "details": {}},
            {"name": "all_detected_standards_built", "passed": True, "details": {}},
            {"name": "built_component_ids_are_unique", "passed": True, "details": {}},
            {"name": "detected_standard_labels_are_unique", "passed": True, "details": {}},
        ],
    }
    coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")


def _write_flathead_component_inventory(output_dir: Path, source_set_id: str) -> None:
    components_dir = output_dir / "derived" / source_set_id / "forest_plan_components"
    inventory_path = components_dir / "component_inventory.json"
    coverage_path = components_dir / "component_inventory_build_coverage.json"
    components_dir.mkdir(parents=True, exist_ok=True)
    source_record_id = "R1PLAN-flathead-nf-02"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    content_sha256 = hashlib.sha256(_FLATHEAD_PLAN_COMPONENT_TEXT.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
    provenance = {
        "entity": {
            "type": "forest_plan_component",
            "source_record_id": source_record_id,
            "source_chunk_ids": source_chunk_ids,
            "artifact_sha256": artifact_sha256,
            "content_sha256": content_sha256,
        },
        "activity": {
            "type": "component_inventory_fixture",
            "created_at": "2026-05-11T00:00:00Z",
        },
        "agent": {
            "type": "deterministic_test_fixture",
            "name": "tests/test_compliance_review.py",
            "version": "forest-plan-component-inventory-v0",
        },
    }
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "flathead-test-components-v0",
        "forest_unit_id": "flathead-nf",
        "plan_version": "2018",
        "source_set_id": source_set_id,
        "components": [
            {
                "component_id": "flathead-fw-std-wtr-01",
                "component_type": "standard",
                "component_text": (
                    "Standard (FW-STD-WTR) 01 New stream diversions and associated ditches "
                    "shall have screens placed on them to prevent capture of fish and other "
                    "aquatic organisms."
                ),
                "forest_unit_id": "flathead-nf",
                "plan_version": "2018",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "section_id": "jewel-basin-hiking-area-standard-1",
                "section_heading": "Jewel Basin Hiking Area Standards",
                "page": None,
                "citation_label": "R1PLAN-flathead-nf-02 | test plan | artifact abc123",
                "geographic_area_ids": ["geo-hungry-horse"],
                "management_area_ids": ["mgmt-jewel-basin-hiking-area"],
                "overlay_ids": [],
                "resource_topics": ["hydrology"],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "activity_tags": ["stream diversions", "screens", "aquatic organisms"],
                "package_evidence_terms": [
                    "new stream diversions",
                    "screens placed on them",
                    "aquatic organisms",
                ],
                "provenance": provenance,
            },
            {
                "component_id": "flathead-ma1b-suit-07",
                "component_type": "suitability",
                "component_text": (
                    "Suitability (MA1b-SUIT) 07 The Jewel Basin hiking area is not suitable "
                    "for motorized use, mechanized transport, and stock use."
                ),
                "forest_unit_id": "flathead-nf",
                "plan_version": "2018",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "section_id": "jewel-basin-hiking-area-suitability-7",
                "section_heading": "Jewel Basin Hiking Area Suitability",
                "page": None,
                "citation_label": "R1PLAN-flathead-nf-02 | test plan | artifact abc123",
                "geographic_area_ids": ["geo-hungry-horse"],
                "management_area_ids": ["mgmt-jewel-basin-hiking-area"],
                "overlay_ids": [],
                "resource_topics": ["recreation access"],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "activity_tags": ["motorized use", "mechanized transport", "stock use"],
                "package_evidence_terms": [
                    "motorized use",
                    "mechanized transport",
                    "stock use",
                ],
                "provenance": provenance,
            },
        ],
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    coverage = {
        "schema_version": "forest-plan-component-inventory-build-coverage-v0",
        "created_at": "2026-05-11T00:00:00Z",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunks_path": str(output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"),
        "selected_chunk_count": 1,
        "detected_component_count": 2,
        "detected_standard_count": 1,
        "built_component_count": 2,
        "built_standard_count": 1,
        "missing_component_ids": [],
        "missing_standard_ids": [],
        "duplicate_component_ids": [],
        "duplicate_standard_ids": [],
        "validation_errors": [],
        "detected_component_labels": [
            {
                "component_id": "flathead-fw-std-wtr-01",
                "component_type": "standard",
                "label": "Standard",
                "code": "FW-STD-WTR",
                "number": "01",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "Jewel Basin Hiking Area Standards",
            },
            {
                "component_id": "flathead-ma1b-suit-07",
                "component_type": "suitability",
                "label": "Suitability",
                "code": "MA1b-SUIT",
                "number": "07",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "Jewel Basin Hiking Area Suitability",
            },
        ],
        "detected_standard_labels": [
            {
                "component_id": "flathead-fw-std-wtr-01",
                "component_type": "standard",
                "label": "Standard",
                "code": "FW-STD-WTR",
                "number": "01",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "Jewel Basin Hiking Area Standards",
            }
        ],
        "passed": True,
        "checks": [
            {"name": "selected_forest_plan_chunks_present", "passed": True, "details": {}},
            {"name": "labeled_components_detected", "passed": True, "details": {}},
            {"name": "standard_components_detected", "passed": True, "details": {}},
            {"name": "all_detected_components_built", "passed": True, "details": {}},
            {"name": "all_detected_standards_built", "passed": True, "details": {}},
            {"name": "built_component_ids_are_unique", "passed": True, "details": {}},
            {"name": "detected_standard_labels_are_unique", "passed": True, "details": {}},
        ],
    }
    coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")


def _write_catalog_sqlite(output_dir: Path, topics_by_source: dict[str, list[str]]) -> None:
    path = output_dir / "catalog" / "review_sources.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE review_topics (
              topic_id TEXT PRIMARY KEY,
              label TEXT NOT NULL
            );
            CREATE TABLE source_review_topics (
              source_record_id TEXT NOT NULL,
              topic_id TEXT NOT NULL,
              PRIMARY KEY (source_record_id, topic_id)
            );
            """
        )
        for source_record_id, topics in topics_by_source.items():
            for index, topic in enumerate(topics):
                topic_id = f"topic:{source_record_id}:{index}"
                connection.execute("INSERT INTO review_topics VALUES (?, ?)", (topic_id, topic))
                connection.execute(
                    "INSERT INTO source_review_topics VALUES (?, ?)",
                    (source_record_id, topic_id),
                )
        connection.commit()


def _write_graph_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    graph_dir = output_dir / "derived" / source_set_id / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "evidence_graph_validation.json").write_text(
        json.dumps({"passed": True, "checks": []}, sort_keys=True),
        encoding="utf-8",
    )
    (graph_dir / "summary.json").write_text(
        json.dumps(
            {
                "reviewer_ready": True,
                "validation_passed": True,
                "retrieval_index_path": "index.sqlite",
                "retrieval_index_chunk_count": 2,
                "retrieval_binding_mismatch_count": 0,
                "metrics": {},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _write_upstream_evaluation_phase_outputs(output_dir)
    _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)


def _write_upstream_evaluation_phase_outputs(output_dir: Path) -> None:
    path = output_dir / "evaluations" / "upstream" / "upstream_evaluation_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "upstream-evaluation-results-v0",
                "passed": True,
                "lane_summaries": [
                    {"lane_id": "capture", "status": "direct_eval_present"},
                    {"lane_id": "catalog", "status": "direct_eval_present"},
                    {"lane_id": "extraction", "status": "direct_eval_present"},
                ],
                "failed_case_ids": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_downstream_direct_eval_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    contracts = {
        output_dir / "derived" / source_set_id / "retrieval" / "retrieval_eval_results.json": (
            Path("config/retrieval_eval_seed.json"),
            "retrieval-direct-eval-v1",
        ),
        output_dir / "derived" / source_set_id / "claims" / "claim_eval_results.json": (
            Path("config/claim_eval_seed.json"),
            "claim-direct-eval-v1",
        ),
        output_dir / "reviews" / "compliance_review_eval" / "compliance_review_eval_results.json": (
            Path("config/compliance_review_eval_seed.json"),
            "compliance-review-direct-eval-v1",
        ),
    }
    rule_claim_root = output_dir / "derived" / source_set_id / "rule_claim_links"
    candidates = sorted(rule_claim_root.glob("*/*/summary.json"))
    rule_claim_result_paths = {
        candidate.parent / "rule_claim_link_eval_results.json" for candidate in candidates
    }
    if not rule_claim_result_paths:
        rule_claim_result_paths.add(
            default_rule_claim_links_dir(
                output_dir,
                source_set_id=source_set_id,
            )
            / "rule_claim_link_eval_results.json"
        )
    for rule_claim_result_path in rule_claim_result_paths:
        contracts[rule_claim_result_path] = (
            Path("config/rule_claim_link_eval_seed.json"),
            "rule-claim-direct-eval-v1",
        )
    for result_path, (contract_path, eval_id) in contracts.items():
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _direct_eval_result_payload(
                    contract_path=contract_path,
                    eval_id=eval_id,
                    source_set_id=source_set_id,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )


def _write_final_qa_phase_outputs(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    final_qa_dir = review_dir / "final_qa"
    final_qa_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        final_qa_dir / "east_crazies_final_qa_certification.json",
        {
            "schema_version": "east-crazies-final-qa-certification-report-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "gate_replay_summary": {"machine_replay_status": "passed"},
            "finding_qa": {"authority_finding_count": 33},
            "accepted_v1_risk_ledger": {"accepted_pending_count": 14},
            "certification_statement": {"legal_conclusion": False},
        },
    )
    _write_json(
        final_qa_dir / "east_crazies_final_qa_certification_manifest.json",
        {
            "schema_version": "east-crazies-final-qa-certification-manifest-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation_status": "passed",
        },
    )
    _write_json(
        final_qa_dir / "east_crazies_final_qa_certification_validation.json",
        {
            "schema_version": "east-crazies-final-qa-certification-validation-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "machine_replay_status": "passed",
            "check_count": 157,
            "failed_check_count": 0,
            "failure_category_counts": {},
        },
    )
    (final_qa_dir / "east_crazies_final_qa_certification.pdf").write_bytes(b"%PDF-1.4\n")


def _write_component_adjudication_eval(
    review_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
    passed: bool,
    pending_count: int = 0,
    queue_item_count: int = 2,
    real_ea_omission_count: int | None = None,
    system_miss_count: int = 0,
) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    resolved_count = queue_item_count - pending_count
    real_ea_omission_count = (
        resolved_count if real_ea_omission_count is None else real_ea_omission_count
    )
    failure_counts = {"adjudication_pending": pending_count} if pending_count else {}
    outcome_counts = {}
    if real_ea_omission_count:
        outcome_counts["real_ea_omission"] = real_ea_omission_count
    if system_miss_count:
        outcome_counts["system_miss"] = system_miss_count
    (review_dir / "forest_plan_component_adjudication_eval.json").write_text(
        json.dumps(
            {
                "schema_version": "forest-plan-component-adjudication-eval-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "summary": {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "adjudication_file": str(
                        review_dir / "forest_plan_component_adjudication.json"
                    ),
                    "queue_item_count": queue_item_count,
                    "adjudication_item_count": queue_item_count,
                    "resolved_adjudication_count": resolved_count,
                    "pending_adjudication_count": pending_count,
                    "real_ea_omission_count": real_ea_omission_count,
                    "system_miss_count": system_miss_count,
                    "adjudication_completion_rate": round(resolved_count / queue_item_count, 6),
                    "real_ea_omission_rate": round(
                        real_ea_omission_count / queue_item_count,
                        6,
                    ),
                    "system_miss_rate": round(system_miss_count / queue_item_count, 6),
                    "adjudication_expectation_match_rate": 1.0,
                    "adjudication_outcome_counts": outcome_counts,
                    "disposition_counts": (
                        {"true_ea_omission": real_ea_omission_count}
                        if real_ea_omission_count
                        else {}
                    ),
                    "real_ea_omission_disposition_counts": (
                        {"true_ea_omission": real_ea_omission_count}
                        if real_ea_omission_count
                        else {}
                    ),
                    "system_miss_disposition_counts": (
                        {"retrieval_miss": system_miss_count}
                        if system_miss_count
                        else {}
                    ),
                    "failure_category_counts": failure_counts,
                    "passed": passed,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_component_eval(
    review_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
    passed: bool,
    schema_version: str = "forest-plan-component-eval-results-v0",
) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "forest_plan_component_eval_results.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "summary": {
                    "schema_version": schema_version,
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "case_count": 3,
                    "passed_case_count": 3 if passed else 2,
                    "failed_case_count": 0 if passed else 1,
                    "metrics": {
                        "component_applicability_precision": 1.0,
                        "component_applicability_recall": 1.0,
                        "applicable_standard_recall": 1.0,
                    },
                    "failure_category_counts": {} if passed else {"package_section_mismatch": 1},
                    "passed": passed,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    title: str,
    document_role: str,
    authority_level: str,
    citation_label: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "support_document_role": document_role,
        "authority_level": authority_level,
        "host": "example.test",
        "expected_parser": "html",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "citation_label": citation_label,
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-04-30T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": title,
        "content_sha256": content_sha256,
        "text": text,
    }


def _direct_eval_result_payload(
    *,
    contract_path: Path,
    eval_id: str,
    source_set_id: str,
) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    coverage_requirements = contract.get("coverage_requirements", {})
    case_count = int(
        coverage_requirements.get("case_count")
        or ((contract.get("metric_thresholds") or {}).get("case_count") or {}).get("min")
        or 1
    )
    metrics = {}
    for metric_name, threshold in (contract.get("metric_thresholds") or {}).items():
        if not isinstance(threshold, dict):
            continue
        if "min" in threshold:
            metrics[metric_name] = threshold["min"]
        elif "max" in threshold:
            metrics[metric_name] = threshold["max"]
    payload = {
        "schema_version": "unit-direct-eval-result",
        "eval_id": eval_id,
        "source_set_id": source_set_id,
        "passed": True,
        "checks": [
            {
                "name": "eval_cases_pass",
                "passed": True,
                "details": {"case_count": case_count, "failed_case_ids": []},
            },
            {
                "name": "metric_thresholds_met",
                "passed": True,
                "details": {"failures": []},
            },
        ],
        "contract": {"sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest()},
        "metrics": metrics,
    }
    for key, value in coverage_requirements.items():
        payload[key] = value
    payload.setdefault("case_count", case_count)
    payload.setdefault(
        "hard_negative_case_count",
        coverage_requirements.get("hard_negative_case_count", 0),
    )
    if eval_id == "retrieval-direct-eval-v1":
        payload["query_count"] = case_count
    return payload


def _write_package(directory: Path, text: str) -> Path:
    path = directory / "ea-package.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _write_rule_pack(directory: Path, rule_ids: list[str] | None = None) -> Path:
    rule_pack = _rule_pack()
    if rule_ids is not None:
        wanted = set(rule_ids)
        rule_pack["rules"] = [rule for rule in rule_pack["rules"] if rule["id"] in wanted]
        kept_source_record_ids = {
            rule["authority_source_record_id"]
            for rule in rule_pack["rules"]
            if rule.get("authority_source_record_id")
        }
        rule_pack["baseline_source_record_ids"] = [
            source_record_id
            for source_record_id in rule_pack.get("baseline_source_record_ids", [])
            if source_record_id in kept_source_record_ids
        ]
    path = directory / "rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_generated_review_gate(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    package_path: Path,
    base_rule_pack_path: Path,
    include_non_applicable: bool = False,
) -> Path:
    review_dir = output_dir / "reviews" / review_id
    run_ea_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        checklist_path=base_rule_pack_path,
        review_id=review_id,
        results_dir=review_dir,
    )
    applicability_dir = review_dir / "applicability"
    applicability_dir.mkdir(parents=True, exist_ok=True)
    base_rule_pack = json.loads(base_rule_pack_path.read_text(encoding="utf-8"))
    package_manifest_path = review_dir / "package" / "package_manifest.jsonl"
    package_chunks_path = review_dir / "package" / "package_chunks.jsonl"
    authority_universe_path = applicability_dir / "authority_universe_snapshot.json"
    package_fact_graph_path = applicability_dir / "package_fact_graph.json"
    package_fact_graph_validation_path = applicability_dir / "package_fact_graph_validation.json"
    retrieval_trace_path = applicability_dir / "applicability_retrieval_trace.jsonl"
    graph_trace_path = applicability_dir / "applicability_graph_trace.jsonl"
    trace_diagnostics_path = applicability_dir / "applicability_retrieval_graph_diagnostics.json"
    decisions_path = applicability_dir / "applicability_decisions.jsonl"
    applicable_path = applicability_dir / "applicable_authorities.json"
    non_applicable_path = applicability_dir / "non_applicable_authorities.json"
    coverage_path = applicability_dir / "search_coverage_certificates.json"
    provenance_path = applicability_dir / "applicability_provenance.json"
    validation_path = applicability_dir / "applicability_validation.json"
    generated_path = applicability_dir / "generated_rule_pack.json"
    generated_validation_path = applicability_dir / "generated_rule_pack_validation.json"
    applicability_run_id = f"applicability-{review_id}"
    applicable_authorities = []
    decisions = []
    candidate_authorities = []
    for rule in base_rule_pack["rules"]:
        candidate_id = f"candidate:{rule['id']}"
        decision_id = f"decision:{rule['id']}"
        authority_family_id = rule.get("authority_family_id")
        authority = {
            "candidate_authority_id": candidate_id,
            "candidate_authority_type": "rule_template",
            "decision_id": decision_id,
            "authority_family_id": authority_family_id,
            "authority_family_ids": [authority_family_id] if authority_family_id else [],
            "status": "applicable",
            "basis_type": "mandatory_baseline",
            "applicability_basis": {
                "rationale": "Unit generated gate marks baseline rule applicable.",
            },
            "rule_template": {
                "rule_id": rule["id"],
                "authority_family_id": authority_family_id,
            },
            "source_record_ids": [rule.get("authority_source_record_id")],
            "document_roles": [rule.get("authority_document_role") or "regulation"],
        }
        candidate_authorities.append(authority)
        applicable_authorities.append(authority)
        decisions.append(authority)
    non_applicable_authorities = (
        [
            {
                "candidate_authority_id": "candidate:not-applicable",
                "candidate_authority_type": "rule_template",
                "decision_id": "decision:not-applicable",
                "authority_family_id": "unit_not_applicable",
                "authority_family_ids": ["unit_not_applicable"],
                "status": "not_applicable",
                "basis_type": "absent_trigger_evidence",
                "applicability_basis": {
                    "rationale": "Unit package did not include the conditional trigger.",
                },
                "non_applicability_basis": {
                    "rationale": "Unit package did not include the conditional trigger.",
                },
                "search_coverage_certificate_ids": ["coverage:not-applicable"],
            }
        ]
        if include_non_applicable
        else []
    )
    if include_non_applicable:
        candidate_authorities.extend(non_applicable_authorities)
        decisions.extend(non_applicable_authorities)
    _write_json(
        authority_universe_path,
        {
            "schema_version": "authority-universe-snapshot-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation": {"passed": True},
            "candidate_authorities": candidate_authorities,
        },
    )
    package_fact_graph_sha256 = hashlib.sha256(
        f"{review_id}:{source_set_id}:package-facts".encode("utf-8")
    ).hexdigest()
    _write_json(
        package_fact_graph_path,
        {
            "schema_version": "package-fact-graph-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_fact_graph_sha256": package_fact_graph_sha256,
            "nodes": [{"node_id": "package-fact:purpose-need", "node_type": "package_section"}],
            "edges": [],
        },
    )
    _write_json(
        package_fact_graph_validation_path,
        {
            "schema_version": "package-fact-graph-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_fact_graph_sha256": package_fact_graph_sha256,
            "validation": {"passed": True, "checks": []},
        },
    )
    _write_jsonl(
        retrieval_trace_path,
        [
            {
                "candidate_authority_id": authority["candidate_authority_id"],
                "trace_id": f"retrieval:{authority['candidate_authority_id']}",
            }
            for authority in candidate_authorities
        ],
    )
    _write_jsonl(
        graph_trace_path,
        [
            {
                "candidate_authority_id": authority["candidate_authority_id"],
                "trace_id": f"graph:{authority['candidate_authority_id']}",
            }
            for authority in candidate_authorities
        ],
    )
    _write_json(
        trace_diagnostics_path,
        {
            "schema_version": "applicability-retrieval-graph-diagnostics-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "retrieval_trace_sha256": sha256_file(retrieval_trace_path),
            "graph_trace_sha256": sha256_file(graph_trace_path),
            "validation": {"passed": True, "checks": []},
        },
    )
    _write_jsonl(decisions_path, decisions)
    _write_json(
        applicable_path,
        {
            "schema_version": "applicable-authorities-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "authority_count": len(applicable_authorities),
            "authorities": applicable_authorities,
        },
    )
    _write_json(
        non_applicable_path,
        {
            "schema_version": "non-applicable-authorities-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "authority_count": len(non_applicable_authorities),
            "authorities": non_applicable_authorities,
        },
    )
    coverage_certificates = (
        [
            {
                "coverage_certificate_id": "coverage:not-applicable",
                "candidate_authority_id": "candidate:not-applicable",
                "covered_candidate_authority_ids": ["candidate:not-applicable"],
                "covered_decision_ids": ["decision:not-applicable"],
                "coverage_class": "non_applicable_authority",
                "coverage_result": "sufficient",
                "rationale": "Unit coverage certificate for not-applicable authority.",
            }
        ]
        if include_non_applicable
        else []
    )
    _write_json(
        coverage_path,
        {
            "schema_version": "search-coverage-certificates-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "certificates": coverage_certificates,
        },
    )
    _write_json(
        provenance_path,
        {
            "schema_version": "applicability-provenance-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "applicability_run_id": applicability_run_id,
            "entities": [],
        },
    )
    hashes = {
        "applicable_authorities_sha256": sha256_file(applicable_path),
        "authority_universe_sha256": sha256_file(authority_universe_path),
        "decisions_sha256": sha256_file(decisions_path),
        "non_applicable_authorities_sha256": sha256_file(non_applicable_path),
        "applicability_provenance_sha256": sha256_file(provenance_path),
        "package_manifest_sha256": sha256_file(package_manifest_path),
        "package_chunks_sha256": sha256_file(package_chunks_path),
        "search_coverage_certificates_sha256": sha256_file(coverage_path),
    }
    _write_json(
        validation_path,
        {
            "schema_version": "applicability-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "applicability_run_id": applicability_run_id,
            "passed": True,
            "reviewer_ready": True,
            "generated_rule_pack_ready": True,
            "artifact_paths": {
                "applicable_authorities": str(applicable_path),
                "authority_universe": str(authority_universe_path),
                "decisions": str(decisions_path),
                "non_applicable_authorities": str(non_applicable_path),
                "search_coverage_certificates": str(coverage_path),
                "provenance": str(provenance_path),
            },
            "hashes": hashes,
        },
    )
    generated_rules = []
    for rule in base_rule_pack["rules"]:
        generated_rule = dict(rule)
        generated_rule["base_rule_id"] = rule["id"]
        generated_rule["generated_rule_id"] = rule["id"]
        generated_rule["base_rule_pack_id"] = base_rule_pack["rule_pack_id"]
        generated_rule["base_rule_pack_version"] = base_rule_pack["version"]
        generated_rule["generated_from_applicability"] = True
        generated_rule["applicability_decision_id"] = f"decision:{rule['id']}"
        generated_rule["candidate_authority_id"] = f"candidate:{rule['id']}"
        generated_rule["authority_family_id"] = rule.get("authority_family_id")
        generated_rule["authority_family_ids"] = [rule.get("authority_family_id")]
        generated_rule["applicability"] = {
            "decision_id": generated_rule["applicability_decision_id"],
            "candidate_authority_id": generated_rule["candidate_authority_id"],
            "candidate_authority_type": "rule_template",
            "authority_family_id": rule.get("authority_family_id"),
            "authority_family_ids": [rule.get("authority_family_id")],
            "status": "applicable",
            "basis_type": "mandatory_baseline",
            "applicability_basis": {
                "rationale": "Unit generated gate marks baseline rule applicable.",
            },
            "source_record_ids": [rule.get("authority_source_record_id")],
            "document_roles": [rule.get("authority_document_role") or "regulation"],
        }
        generated_rules.append(generated_rule)
    generated_rule_pack = {
        **base_rule_pack,
        "schema_version": "generated-compliance-rule-pack-v0",
        "rule_pack_id": f"generated-{base_rule_pack['rule_pack_id']}",
        "version": "applicability-v0",
        "base_rule_pack_id": base_rule_pack["rule_pack_id"],
        "base_rule_pack_version": base_rule_pack["version"],
        "base_rule_pack_sha256": sha256_file(base_rule_pack_path),
        "generated_rule_pack_id": f"generated-{base_rule_pack['rule_pack_id']}",
        "generated_rule_pack_version": "applicability-v0",
        "applicability_run_id": applicability_run_id,
        "applicability_validation_sha256": sha256_file(validation_path),
        "source_set_id": source_set_id,
        "review_id": review_id,
        "non_applicable_authorities_sha256": sha256_file(non_applicable_path),
        **hashes,
        "rules": generated_rules,
    }
    _write_json(generated_path, generated_rule_pack)
    generated_sha = sha256_file(generated_path)
    _write_json(
        generated_validation_path,
        {
            "schema_version": "generated-rule-pack-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "summary": {
                "generated_rule_pack_ready": True,
                "generated_rule_pack_sha256": generated_sha,
                "expected_generated_rule_pack_sha256": generated_sha,
                "applicability_run_id": applicability_run_id,
                "source_set_id": source_set_id,
            },
        },
    )
    return generated_path


def _run_generated_compliance_review(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    package_path: Path,
    base_rule_pack_path: Path,
    include_non_applicable: bool = False,
    forest_unit_id: str = "custer-gallatin-nf",
):
    generated_rule_pack_path = _write_generated_review_gate(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        package_path=package_path,
        base_rule_pack_path=base_rule_pack_path,
        include_non_applicable=include_non_applicable,
    )
    result = run_compliance_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        rule_pack_path=generated_rule_pack_path,
        forest_unit_id=forest_unit_id,
        review_id=review_id,
        reuse_package_cache=True,
    )
    _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)
    return result


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _write_grouped_conditional_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-grouped-conditional",
        "version": "0.1.0",
        "title": "Unit Grouped Conditional Rule Pack",
        "description": "Unit test rule pack for grouped conditional applicability.",
        "rules": [
            {
                "id": "ce_adoption",
                "title": "CE adoption is reviewed",
                "authority_category": "regulation",
                "authority_source_record_id": "R1EA-002",
                "applicability_mode": "conditional",
                "question": "Does the EA package document a CE adoption path?",
                "requirement": "A CE adoption path should be documented when actually used.",
                "package_query": "adopted CE categorical exclusion path",
                "package_terms": ["adopted CE", "categorical exclusion path"],
                "source_query": "mitigation measures finding of no significant impact",
                "source_filters": {
                    "document_role": "regulation",
                    "source_record_id": "R1EA-002",
                },
                "applies_if_package_terms": [
                    "categorical exclusion",
                    "adopted CE",
                    "categorical exclusion path",
                ],
                "applies_if_package_term_groups": [
                    ["categorical exclusion", "CE"],
                    ["adopted CE", "categorical exclusion path"],
                ],
                "does_not_apply_if_package_terms": [
                    "not subject to a categorical exclusion",
                    "categorical exclusion path is not used",
                ],
                "severity": "high",
            }
        ],
    }
    path = directory / "grouped-conditional-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_custer_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-custer-gallatin-ea",
        "version": "0.1.0",
        "title": "Unit Custer Gallatin EA Rule Pack",
        "description": "Unit test Custer Gallatin forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
        "rules": [
            {
                "id": "custer_gallatin_lmp_2022",
                "title": "Custer Gallatin forest-plan standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_custer_forest_plan",
                "authority_source_record_id": "R1PLAN-custer-gallatin-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Custer Gallatin standard?",
                "requirement": (
                    "Custer Gallatin EAs in the Crazy Mountains Backcountry Area must "
                    "address the standard prohibiting new permanent or temporary roads."
                ),
                "package_query": "new permanent or temporary roads",
                "package_terms": ["new permanent or temporary roads"],
                "source_query": "new permanent or temporary roads shall not be allowed",
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "custer-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_beaverhead_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-beaverhead-ea",
        "version": "0.1.0",
        "title": "Unit Beaverhead-Deerlodge EA Rule Pack",
        "description": "Unit test Beaverhead-Deerlodge forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-beaverhead-deerlodge-nf-02"],
        "rules": [
            {
                "id": "beaverhead_west_big_hole_lmp_2009",
                "title": "Beaverhead-Deerlodge forest-plan standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_beaverhead_forest_plan",
                "authority_source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Beaverhead standard?",
                "requirement": (
                    "Beaverhead-Deerlodge EAs in the West Big Hole Management Area must "
                    "address the standard prohibiting new permanent or temporary roads."
                ),
                "package_query": "new permanent or temporary roads",
                "package_terms": ["new permanent or temporary roads"],
                "source_query": "new permanent or temporary roads shall not be allowed",
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "beaverhead-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_flathead_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-flathead-ea",
        "version": "0.1.0",
        "title": "Unit Flathead EA Rule Pack",
        "description": "Unit test Flathead forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-flathead-nf-02"],
        "rules": [
            {
                "id": "flathead_fw_std_wtr_2018",
                "title": "Flathead forest-plan stream-screen standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_flathead_forest_plan",
                "authority_source_record_id": "R1PLAN-flathead-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Flathead standard?",
                "requirement": (
                    "Flathead EAs in the Jewel Basin Hiking Area must address the stream-"
                    "screening standard for new diversions."
                ),
                "package_query": "new stream diversions screens placed on them aquatic organisms",
                "package_terms": ["new stream diversions", "screens placed on them"],
                "source_query": (
                    "new stream diversions and associated ditches shall have screens placed "
                    "on them to prevent capture of fish and other aquatic organisms"
                ),
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-flathead-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "flathead-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_compliance_eval_file(
    directory: Path,
    cases: list[dict],
    *,
    path: Path | None = None,
) -> Path:
    eval_path = path or directory / "compliance-eval.json"
    eval_path.write_text(json.dumps(cases, sort_keys=True), encoding="utf-8")
    return eval_path


def _write_coverage_matrix(directory: Path, rule_ids: list[str] | None = None) -> Path:
    items = [
        {
            "rule_id": "purpose_need",
            "obligation_area": "Purpose and need",
            "expected_package_evidence": "Purpose and need or proposed action text.",
            "source_record_ids": ["R1EA-001"],
            "source_claim_terms": ["purpose", "need"],
            "eval_case_ids": ["coverage-case"],
        },
        {
            "rule_id": "mitigation",
            "obligation_area": "Mitigation",
            "expected_package_evidence": "Mitigation or FONSI support text.",
            "source_record_ids": ["R1EA-002"],
            "source_claim_terms": ["mitigation"],
            "eval_case_ids": ["coverage-case"],
        },
    ]
    if rule_ids is not None:
        wanted = set(rule_ids)
        items = [item for item in items if item["rule_id"] in wanted]
    path = directory / "coverage-matrix.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-rule-pack-coverage-v0",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "title": "Unit coverage matrix",
                "coverage_items": items,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_gold_eval_file(directory: Path, profiles: list[str] | None = None) -> Path:
    profiles = profiles or ["positive", "mixed", "negative"]
    cases = [
        {
            "id": "gold-positive",
            "profile": profiles[0],
            "package_text": (
                "Purpose and Need. The proposed action improves trail access. "
                "Alternatives include no action. Mitigation measures support a FONSI."
            ),
            "expected_statuses": {
                "purpose_need": "pass",
                "mitigation": "pass",
            },
            "expected_finding_status_counts": {"pass": 2},
            "min_findings": 2,
        },
        {
            "id": "gold-mixed",
            "profile": profiles[1],
            "package_text": "Purpose and Need. The proposed action improves trail access.",
            "expected_statuses": {
                "purpose_need": "pass",
                "mitigation": "gap",
            },
            "expected_finding_status_counts": {"gap": 1, "pass": 1},
            "min_findings": 2,
        },
        {
            "id": "gold-negative",
            "profile": profiles[2],
            "package_text": "Routing slip. Staff contacts and a meeting date.",
            "expected_statuses": {
                "purpose_need": "gap",
                "mitigation": "gap",
            },
            "expected_finding_status_counts": {"gap": 2},
            "min_findings": 2,
        },
    ]
    for case in cases:
        case["adjudication"] = {
            "status": "adjudicated_seed",
            "source_type": "realistic_synthetic",
            "adjudicated_by": ["unit-test"],
            "adjudicated_at": "2026-04-30",
            "rationale": f"Unit adjudication for {case['id']}.",
        }
        case["expected_unsupported_finding_ids"] = []
        case["expected_source_record_ids"] = {
            "purpose_need": ["R1EA-001"],
            "mitigation": ["R1EA-002"],
        }
        case["expected_source_document_roles"] = {
            "purpose_need": ["regulation"],
            "mitigation": ["regulation"],
        }
    path = directory / "gold-eval.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-gold-eval-v0",
                "id": "unit-gold-v0.1",
                "version": "0.1.0",
                "title": "Unit Gold Eval",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "adjudication": {
                    "status": "seed_gold",
                    "method": "Unit test adjudication.",
                    "adjudicated_by": ["unit-test"],
                    "adjudicated_at": "2026-04-30",
                    "promotion_gate": True,
                },
                "cases": cases,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _rule_pack() -> dict:
    return {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "title": "Unit NEPA EA Rule Pack",
        "description": "Unit test rule pack.",
        "baseline_source_record_ids": ["R1EA-001", "R1EA-002"],
        "rules": [
            {
                "id": "purpose_need",
                "title": "Purpose and need are stated",
                "authority_category": "regulation",
                "authority_family_id": "unit_purpose_need",
                "authority_source_record_id": "R1EA-001",
                "applicability_mode": "baseline",
                "question": "Does the EA package identify the purpose and need?",
                "requirement": "Purpose and need should be identified.",
                "package_query": "purpose need proposed action",
                "package_terms": ["purpose and need", "proposed action"],
                "source_query": "environmental assessment purpose need",
                "source_filters": {"document_role": "regulation", "source_record_id": "R1EA-001"},
                "severity": "high",
            },
            {
                "id": "mitigation",
                "title": "Mitigation is addressed",
                "authority_category": "regulation",
                "authority_family_id": "unit_mitigation",
                "authority_source_record_id": "R1EA-002",
                "applicability_mode": "baseline",
                "question": "Does the EA package address mitigation?",
                "requirement": "Mitigation should be addressed when used to support a finding.",
                "package_query": "mitigation measures",
                "package_terms": ["mitigation"],
                "source_query": "mitigation measures finding of no significant impact",
                "source_filters": {"document_role": "regulation", "source_record_id": "R1EA-002"},
                "severity": "high",
            },
        ],
    }


def _rule_by_id(rule_pack: dict, rule_id: str) -> dict:
    return next(rule for rule in rule_pack["rules"] if rule["id"] == rule_id)


def _coverage_item_by_rule_id(coverage: dict, rule_id: str) -> dict:
    return next(item for item in coverage["coverage_items"] if item["rule_id"] == rule_id)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _finding(report: dict, finding_id: str) -> dict:
    return next(finding for finding in report["findings"] if finding["id"] == finding_id)


def _check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)


def _phase(summary: dict, name: str) -> dict:
    return next(phase for phase in summary["phases"] if phase["name"] == name)
