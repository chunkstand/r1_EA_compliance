from __future__ import annotations

from pathlib import Path
import unittest

from tests.support.v1_ea_eval_fixtures import _accepted_pending_policy
from tests.support.v1_ea_eval_fixtures import _finding
from tests.support.v1_ea_eval_fixtures import _matrix_row
from tests.support.v1_ea_eval_fixtures import _write_json
from tests.support.v1_ea_eval_fixtures import _write_jsonl


def _assert_repair_baseline_failure_summary(
    test_case: unittest.TestCase,
    summary: dict,
) -> None:
    expected_ids_by_category = {
        "conditional_false_positive": [
            "nepa_4336c_ce_adoption_screen",
            "usda_nepa_ce_fanec_7cfr_1b3",
            "usda_nepa_subcomponent_ce_7cfr_1b4",
        ],
        "rule_section_mismatch": [
            "nepa_4336b_programmatic_tiering",
            "nepa_statute_chapter_55",
        ],
    }
    test_case.assertEqual(
        summary["failure_category_counts"],
        {"conditional_false_positive": 3, "rule_section_mismatch": 2},
    )
    test_case.assertEqual(summary["failed_rule_expectation_count"], 5)
    test_case.assertEqual(
        summary["failed_rule_ids"],
        sorted(
            rule_id
            for rule_ids in expected_ids_by_category.values()
            for rule_id in rule_ids
        ),
    )
    test_case.assertEqual(summary["failed_rule_ids_by_category"], expected_ids_by_category)
    test_case.assertEqual(
        [
            (
                failure["expectation_type"],
                failure["rule_id"],
                failure["failure_categories"],
            )
            for failure in summary["failed_rule_expectations"]
        ],
        [
            (
                "rule_review_expectation",
                "nepa_statute_chapter_55",
                ["rule_section_mismatch"],
            ),
            (
                "conditional_source_expectation",
                "nepa_4336b_programmatic_tiering",
                ["rule_section_mismatch"],
            ),
            (
                "conditional_source_expectation",
                "nepa_4336c_ce_adoption_screen",
                ["conditional_false_positive"],
            ),
            (
                "conditional_source_expectation",
                "usda_nepa_ce_fanec_7cfr_1b3",
                ["conditional_false_positive"],
            ),
            (
                "conditional_source_expectation",
                "usda_nepa_subcomponent_ce_7cfr_1b4",
                ["conditional_false_positive"],
            ),
        ],
    )


def _write_repair_baseline_failure_review(review_dir: Path) -> None:
    _write_jsonl(
        review_dir / "package" / "package_chunks.jsonl",
        [
            {
                "chunk_id": "chunk-purpose",
                "title": "EA",
                "heading": "Purpose and Need",
                "section": "Purpose and Need",
                "text": "The purpose and need section is present in the package.",
            },
            {
                "chunk_id": "chunk-alternatives",
                "title": "EA",
                "heading": "Alternatives",
                "section": "Alternatives",
                "text": "Alternatives are described for the proposed action.",
            },
            {
                "chunk_id": "chunk-effects",
                "title": "EA",
                "heading": "Environmental Consequences",
                "section": "Environmental Consequences",
                "text": "Environmental consequences are disclosed.",
            },
            {
                "chunk_id": "chunk-biology",
                "title": "EA",
                "heading": "Biological Resources",
                "section": "Biological Resources",
                "text": "Biological resources are discussed.",
            },
            {
                "chunk_id": "chunk-cultural",
                "title": "EA",
                "heading": "Cultural Resources",
                "section": "Cultural Resources",
                "text": "Cultural resources are discussed.",
            },
        ],
    )
    findings = [
        _finding(
            rule_id="nepa_statute_chapter_55",
            status="pass",
            applicability_mode="baseline",
            source_record_id="R1EA-001",
            document_role="law",
            package_text="National Environmental Policy Act chapter 55 authority applies.",
            package_section="Authority Summary",
        ),
        _finding(
            rule_id="nepa_4336b_programmatic_tiering",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-005",
            document_role="law",
            package_text=(
                "Programmatic analysis appears in biological resources and cultural resources."
            ),
            package_section="Biological Resources and Cultural Resources",
        ),
        _finding(
            rule_id="nepa_4336c_ce_adoption_screen",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-006",
            document_role="law",
            package_text="The EA mentions categorical exclusions and a FONSI.",
            package_section="Decision and FONSI",
        ),
        _finding(
            rule_id="usda_nepa_ce_fanec_7cfr_1b3",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-011",
            document_role="regulation",
            package_text="The EA mentions FANEC and extraordinary circumstances.",
            package_section="Decision and FONSI",
        ),
        _finding(
            rule_id="usda_nepa_subcomponent_ce_7cfr_1b4",
            status="pass",
            applicability_mode="conditional",
            source_record_id="R1EA-012",
            document_role="regulation",
            package_text="The EA mentions categorical exclusions and level of review.",
            package_section="Decision and FONSI",
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
                "reviewer_ready": False,
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
        review_dir / "authority_explanation_paths.json",
        {
            "schema_version": "authority-explanation-paths-v0",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "summary": {
                "passed": True,
                "finding_path_count": len(findings),
                "all_findings_have_path_classification": True,
                "all_applicable_findings_have_trace_evidence": True,
                "all_non_applicable_paths_have_boundary_evidence": True,
                "path_classification_counts": {
                    "controlling": 3,
                },
                "risk_category_counts": {},
            },
            "finding_explanation_paths": [
                {
                    "authority_explanation_id": f"authority-explanation:{finding['rule_id']}",
                    "rule_id": finding["rule_id"],
                    "status": finding["status"],
                    "applicability_status": finding["applicability_status"],
                    "authority_path_classifications": finding[
                        "authority_path_classifications"
                    ],
                    "primary_authority_path_classification": finding[
                        "primary_authority_path_classification"
                    ],
                    "retrieval_trace_ids": finding["retrieval_trace_ids"],
                    "graph_path_ids": finding["graph_path_ids"],
                }
                for finding in findings
            ],
            "non_applicable_explanation_paths": [],
            "pending_resolution_paths": [],
            "adjudicated_authority_paths": [],
        },
    )


def _write_repair_baseline_eval_contract(root: Path, *, review_id: str) -> Path:
    path = root / "v1_repair_baseline_eval.json"
    _write_json(
        path,
        {
            "schema_version": "v1-ea-real-review-eval-contract-v0",
            "eval_id": "v1-repair-baseline",
            "review_id": review_id,
            "source_set_id": "source-set-test",
            "rule_pack_id": "nepa-ea-v0",
            "rule_pack_version": "0.4.0",
            "allow_unadjudicated_conditional_expectations": True,
            "conditional_adjudication_policy": _accepted_pending_policy(
                ["nepa_4336b_programmatic_tiering"]
            ),
            "baseline_policy": {
                "require_source_record_match_authority": True,
                "expected_source_record_ids": ["R1EA-001"],
            },
            "section_expectations": [
                {
                    "section_id": "purpose_need",
                    "label": "Purpose and Need",
                    "required": True,
                    "expected_terms": ["purpose and need"],
                },
                {
                    "section_id": "alternatives",
                    "label": "Alternatives",
                    "required": True,
                    "expected_terms": ["alternatives"],
                },
                {
                    "section_id": "environmental_consequences",
                    "label": "Environmental Consequences",
                    "required": True,
                    "expected_terms": ["environmental consequences"],
                },
                {
                    "section_id": "biological_resources",
                    "label": "Biological Resources",
                    "required": True,
                    "expected_terms": ["biological resources"],
                },
                {
                    "section_id": "cultural_resources",
                    "label": "Cultural Resources",
                    "required": True,
                    "expected_terms": ["cultural resources"],
                },
            ],
            "rule_review_expectations": [
                {
                    "rule_id": "nepa_statute_chapter_55",
                    "expected_package_section_ids": ["purpose_need"],
                    "expected_source_record_ids": ["R1EA-001"],
                    "expected_source_document_roles": ["law"],
                }
            ],
            "conditional_source_expectations": [
                {
                    "rule_id": "nepa_4336b_programmatic_tiering",
                    "expected_applicability": "adjudicate",
                    "classification_rationale": (
                        "Programmatic tiering remains a reviewer judgment item in "
                        "the repair baseline."
                    ),
                    "expected_package_section_ids": [
                        "alternatives",
                        "environmental_consequences",
                    ],
                    "expected_source_record_ids": ["R1EA-005"],
                    "expected_source_document_roles": ["law"],
                },
                {
                    "rule_id": "nepa_4336c_ce_adoption_screen",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The repair baseline package is an EA context, not an "
                        "adopted categorical-exclusion path."
                    ),
                },
                {
                    "rule_id": "usda_nepa_ce_fanec_7cfr_1b3",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The repair baseline does not rely on a USDA categorical "
                        "exclusion or FANEC path."
                    ),
                },
                {
                    "rule_id": "usda_nepa_subcomponent_ce_7cfr_1b4",
                    "expected_applicability": "not_applicable",
                    "classification_rationale": (
                        "The repair baseline does not use subcomponent categorical "
                        "exclusion screening."
                    ),
                },
            ],
        },
    )
    return path
