from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.v1_ea_eval import run_v1_ea_review_eval


class V1EAReviewEvalTests(unittest.TestCase):
    def test_v1_eval_scores_sections_sources_conditionals_and_forest_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["section_detection_rate"], 1.0)
            self.assertEqual(metrics["source_record_match_rate"], 1.0)
            self.assertEqual(metrics["conditional_false_negative_count"], 0)
            self.assertEqual(metrics["forest_plan_expectation_match_rate"], 1.0)

    def test_v1_eval_flags_conditional_false_negative_and_section_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            _write_jsonl(
                review_dir / "package" / "package_chunks.jsonl",
                [
                    {
                        "chunk_id": "chunk-purpose",
                        "title": "EA",
                        "heading": "Purpose and Need",
                        "section": "Purpose and Need",
                        "text": "The purpose and need is documented.",
                    }
                ],
            )
            report = _read_json(review_dir / "compliance_review.json")
            report["findings"][1]["status"] = "not_applicable"
            report["findings"][1]["applicability_status"] = "not_applicable"
            report["findings"][1]["package_evidence"] = None
            report["findings"][1]["package_evidence_citation"] = None
            _write_json(review_dir / "compliance_review.json", report)
            matrix = _read_json(review_dir / "compliance_matrix.json")
            matrix["rows"][1]["status"] = "not_applicable"
            matrix["rows"][1]["applicability_status"] = "not_applicable"
            matrix["rows"][1]["ea_package_evidence"] = None
            matrix["rows"][1]["ea_package_citation"] = None
            matrix["rows"][1]["citation_requirements_met"] = False
            _write_json(review_dir / "compliance_matrix.json", matrix)
            eval_file = _write_eval_contract(root, review_id="v1-unit")

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["conditional_false_negative"], 1)
            self.assertGreaterEqual(failures["ea_section_detection_miss"], 1)

    def test_v1_eval_enforces_source_alignment_for_adjudicate_when_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"][0]["expected_applicability"] = "adjudicate"
            contract["conditional_source_expectations"][0]["expected_source_record_ids"] = [
                "R1EA-does-not-match"
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["source_record_mismatch"], 1)
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["conditional_actual_applicable_count"], 2)
            self.assertLess(metrics["conditional_actual_applicable_source_record_match_rate"], 1.0)

    def test_v1_eval_flags_applicable_conditional_missing_from_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["conditional_source_expectations"] = [
                expectation
                for expectation in contract["conditional_source_expectations"]
                if expectation["rule_id"] != "esa_section_7"
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["conditional_expectation_missing"], 1)
            self.assertEqual(result.summary["metrics"]["conditional_expectation_missing_count"], 1)

    def test_v1_eval_flags_missing_expected_baseline_source_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "v1-unit"
            _write_positive_review(review_dir)
            eval_file = _write_eval_contract(root, review_id="v1-unit")
            contract = _read_json(eval_file)
            contract["baseline_policy"]["expected_source_record_ids"] = [
                "R1EA-013",
                "R1EA-baseline-missing",
            ]
            _write_json(eval_file, contract)

            result = run_v1_ea_review_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["baseline_source_record_missing"], 1)
            self.assertLess(result.summary["metrics"]["baseline_source_record_match_rate"], 1.0)

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


def _write_positive_review(review_dir: Path) -> None:
    _write_jsonl(
        review_dir / "package" / "package_chunks.jsonl",
        [
            {
                "chunk_id": "chunk-purpose",
                "title": "EA",
                "heading": "Purpose and Need",
                "section": "Purpose and Need",
                "text": "The purpose and need explains the proposed action.",
            },
            {
                "chunk_id": "chunk-forest-plan",
                "title": "EA",
                "heading": "Forest Plan Consistency",
                "section": "Forest Plan Consistency",
                "text": (
                    "The Custer Gallatin National Forest 2022 Land Management Plan applies "
                    "in the Crazy Mountains Backcountry Area."
                ),
            },
            {
                "chunk_id": "chunk-biology",
                "title": "EA",
                "heading": "Biological Resources",
                "section": "Biological Resources",
                "text": (
                    "Endangered Species Act Section 7 consultation and a biological "
                    "assessment are discussed."
                ),
            },
        ],
    )
    findings = [
        _finding(
            rule_id="usda_nepa_ea_7cfr_1b5",
            status="pass",
            applicability_mode="baseline",
            source_record_id="R1EA-013",
            document_role="regulation",
            package_text="The purpose and need explains the proposed action.",
            package_section="Purpose and Need",
        ),
        _finding(
            rule_id="esa_section_7",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-065",
            document_role="law",
            package_text=(
                "Endangered Species Act Section 7 consultation and a biological assessment "
                "are discussed."
            ),
            package_section="Biological Resources",
        ),
        _finding(
            rule_id="custer_gallatin_lmp_2022",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1PLAN-custer-gallatin-nf-02",
            document_role="forest_plan",
            package_text=(
                "The Custer Gallatin National Forest 2022 Land Management Plan applies "
                "in the Crazy Mountains Backcountry Area."
            ),
            package_section="Forest Plan Consistency",
        ),
    ]
    _write_json(
        review_dir / "compliance_review.json",
        {
            "schema_version": "compliance-review-v0",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "summary": {
                "review_id": "v1-unit",
                "source_set_id": "source-set-test",
                "rule_pack_id": "nepa-ea-v0",
                "rule_pack_version": "0.4.0",
                "reviewer_ready": True,
            },
            "findings": findings,
        },
    )
    _write_json(
        review_dir / "compliance_matrix.json",
        {
            "schema_version": "compliance-matrix-v0",
            "summary": {"row_count": len(findings)},
            "rows": [_matrix_row("v1-unit", finding) for finding in findings],
        },
    )
    _write_json(
        review_dir / "compliance_validation.json",
        {"schema_version": "compliance-validation-v0", "passed": True, "checks": []},
    )
    _write_json(
        review_dir / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "scope_status": "custer_gallatin",
            "reviewer_ready": True,
            "component_evaluation": {"all_applicable_standards_applied": True},
        },
    )
    _write_json(
        review_dir / "forest_plan_context.json",
        {
            "schema_version": "forest-plan-context-v0",
            "scope_status": "custer_gallatin",
            "source_record_readiness": {
                "required_source_record_ids": [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ]
            },
            "geographic_areas": [{"entry_id": "geo-bridger-bangtail-crazy"}],
            "management_areas": [{"entry_id": "mgmt-crazy-mountains-bca"}],
        },
    )
    _write_json(
        review_dir / "forest_plan_component_findings.json",
        {
            "schema_version": "forest-plan-component-findings-v0",
            "summary": {"all_applicable_standards_applied": True},
            "findings": [
                {"component_id": "cg-lmp-2022-cmbca-dc-01", "component_type": "desired_condition"},
                {
                    "component_id": "cg-lmp-2022-cmbca-std-01",
                    "component_type": "standard",
                    "applicability_status": "applicable",
                },
                {"component_id": "cg-lmp-2022-cmbca-suit-01", "component_type": "suitability"},
            ],
        },
    )
    _write_json(
        review_dir / "forest_plan_applicable_standard_coverage.json",
        {
            "schema_version": "forest-plan-applicable-standard-coverage-v0",
            "standards": [
                {
                    "standard_id": "cg-lmp-2022-cmbca-std-01",
                    "applicability_status": "applicable",
                    "standard_applied": True,
                }
            ],
        },
    )
    _write_json(
        review_dir / "forest_plan_reviewer_resolution_queue.json",
        {"schema_version": "forest-plan-reviewer-resolution-queue-v0", "summary": {"item_count": 0}},
    )


def _write_eval_contract(root: Path, *, review_id: str) -> Path:
    path = root / "v1_eval.json"
    _write_json(
        path,
        {
            "schema_version": "v1-ea-real-review-eval-contract-v0",
            "eval_id": "v1-unit-eval",
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "allow_unadjudicated_conditional_expectations": True,
            "baseline_policy": {
                "require_source_record_match_authority": True,
                "expected_source_record_ids": ["R1EA-013"],
            },
            "section_expectations": [
                {
                    "section_id": "purpose_need",
                    "label": "Purpose and Need",
                    "required": True,
                    "expected_terms": ["purpose and need"],
                },
                {
                    "section_id": "forest_plan_consistency",
                    "label": "Forest Plan Consistency",
                    "required": True,
                    "expected_terms": ["Land Management Plan", "Crazy Mountains Backcountry Area"],
                },
                {
                    "section_id": "biological_resources",
                    "label": "Biological Resources",
                    "required": True,
                    "expected_terms": ["Endangered Species Act", "biological assessment"],
                },
            ],
            "rule_review_expectations": [
                {
                    "rule_id": "usda_nepa_ea_7cfr_1b5",
                    "expected_package_section_ids": ["purpose_need"],
                    "expected_source_record_ids": ["R1EA-013"],
                    "expected_source_document_roles": ["regulation"],
                },
                {
                    "rule_id": "esa_section_7",
                    "expected_package_section_ids": ["biological_resources"],
                    "expected_source_record_ids": ["R1EA-065"],
                    "expected_source_document_roles": ["law"],
                },
                {
                    "rule_id": "custer_gallatin_lmp_2022",
                    "expected_package_section_ids": ["forest_plan_consistency"],
                    "expected_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
                    "expected_source_document_roles": ["forest_plan"],
                },
            ],
            "conditional_source_expectations": [
                {
                    "rule_id": "esa_section_7",
                    "expected_applicability": "applicable",
                    "expected_package_section_ids": ["biological_resources"],
                    "expected_source_record_ids": ["R1EA-065"],
                    "expected_source_document_roles": ["law"],
                    "trigger_terms": ["Endangered Species Act", "biological assessment"],
                },
                {
                    "rule_id": "custer_gallatin_lmp_2022",
                    "expected_applicability": "applicable",
                    "expected_package_section_ids": ["forest_plan_consistency"],
                    "expected_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
                    "expected_source_document_roles": ["forest_plan"],
                    "trigger_terms": ["Custer Gallatin", "Land Management Plan"],
                },
            ],
            "forest_plan": {
                "expected_scope_status": "custer_gallatin",
                "required_source_record_ids": [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ],
                "expected_geographic_area_ids": ["geo-bridger-bangtail-crazy"],
                "expected_management_area_ids": ["mgmt-crazy-mountains-bca"],
                "expected_component_ids": [
                    "cg-lmp-2022-cmbca-dc-01",
                    "cg-lmp-2022-cmbca-std-01",
                    "cg-lmp-2022-cmbca-suit-01",
                ],
                "expected_applicable_standard_ids": ["cg-lmp-2022-cmbca-std-01"],
                "min_applicable_standard_count": 1,
                "require_all_applicable_standards_applied": True,
                "require_reviewer_ready": True,
                "max_reviewer_resolution_items": 0,
            },
        },
    )
    return path


def _finding(
    *,
    rule_id: str,
    status: str,
    applicability_mode: str,
    source_record_id: str,
    document_role: str,
    package_text: str,
    package_section: str,
) -> dict:
    return {
        "rule_id": rule_id,
        "title": rule_id,
        "status": status,
        "claim_type": "supported_compliance_finding",
        "applicability_status": "applicable" if status != "not_applicable" else "not_applicable",
        "applicability_mode": applicability_mode,
        "authority_source_record_id": source_record_id,
        "authority_document_role": document_role,
        "package_evidence_citation": f"package:{rule_id}",
        "source_library_evidence_citation": f"source:{source_record_id}",
        "package_evidence": {
            "citation_label": f"package:{rule_id}",
            "title": "EA",
            "evidence_span": {"text": package_text},
            "provenance": {"section": package_section},
        },
        "source_library_evidence": {
            "citation_label": f"source:{source_record_id}",
            "source_record_id": source_record_id,
            "document_role": document_role,
            "title": source_record_id,
            "evidence_span": {"text": rule_id},
            "provenance": {"section": "Authority"},
        },
        "source_claim_links": [
            {
                "claim_id": f"claim:{rule_id}",
                "source_record_id": source_record_id,
                "document_role": document_role,
            }
        ],
    }


def _matrix_row(review_id: str, finding: dict) -> dict:
    return {
        "row_id": f"matrix:{review_id}:{finding['rule_id']}",
        "rule_id": finding["rule_id"],
        "status": finding["status"],
        "applicability_status": finding["applicability_status"],
        "applicability_mode": finding["applicability_mode"],
        "authority_source_record_id": finding["authority_source_record_id"],
        "authority_document_role": finding["authority_document_role"],
        "ea_package_citation": finding["package_evidence_citation"],
        "ea_package_evidence": {
            "citation_label": finding["package_evidence_citation"],
            "text": finding["package_evidence"]["evidence_span"]["text"],
            "section": finding["package_evidence"]["provenance"]["section"],
        },
        "source_library_citation": finding["source_library_evidence_citation"],
        "source_library_evidence": {
            "citation_label": finding["source_library_evidence_citation"],
            "source_record_id": finding["authority_source_record_id"],
            "title": finding["authority_source_record_id"],
            "text": finding["rule_id"],
        },
        "applied_source_record_ids": [finding["authority_source_record_id"]],
        "applied_source_document_roles": [finding["authority_document_role"]],
        "citation_requirements_met": True,
    }


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
