from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.review_package_support import search_package_chunks
from usfs_r1_ea_sources.rule_packs import validate_rule_pack
from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _check,
    _chunk,
    _finding,
    _rule_pack,
    _write_generated_review_gate,
    _write_grouped_conditional_rule_pack,
    _write_package,
    _write_rule_pack,
)


class ComplianceReviewContractTests(unittest.TestCase):
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

        result = search_package_chunks(
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
