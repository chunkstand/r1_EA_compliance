from __future__ import annotations

from pathlib import Path
import json


def _summary_check(summary: dict, name: str) -> dict:
    return next(check for check in summary["checks"] if check["name"] == name)


def _accepted_pending_policy(rule_ids: list[str]) -> dict:
    return {
        "mode": "accepted_pending_v1",
        "accepted_pending_count": len(rule_ids),
        "accepted_pending_rule_ids": sorted(rule_ids),
        "rationale": (
            "Unit contract accepts these pending conditional rows while source and "
            "section alignment remain enforced."
        ),
    }


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
            "summary": {
                "row_count": len(findings),
                "forest_plan_compliance_row_count": 1,
                "forest_plan_compliance_applicable_standard_row_count": 1,
            },
            "rows": [_matrix_row("v1-unit", finding) for finding in findings],
            "forest_plan_compliance": {
                "schema_version": "forest-plan-compliance-matrix-v0",
                "summary": {
                    "row_count": 1,
                    "applicable_standard_row_count": 1,
                    "compliance_status_counts": {"complies": 1},
                    "load_errors": [],
                },
                "rows": [
                    {
                        "row_id": (
                            "forest-plan-matrix:v1-unit:"
                            "cg-lmp-2022-cmbca-std-01"
                        ),
                        "component_id": "cg-lmp-2022-cmbca-std-01",
                        "component_type": "standard",
                        "applicability_status": "applicable",
                        "compliance_status": "complies",
                        "finding_status": "supported",
                    }
                ],
            },
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
                    "controlling": len(findings),
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
                    "search_coverage_certificate_ids": [],
                    "supporting_source_record_ids": finding[
                        "supporting_source_record_ids"
                    ],
                    "human_adjudication_refs": [],
                    "residual_risk_categories": finding["residual_risk_categories"],
                    "unresolved_issue_refs": finding["unresolved_issue_refs"],
                }
                for finding in findings
            ],
            "non_applicable_explanation_paths": [],
            "pending_resolution_paths": [],
            "adjudicated_authority_paths": [],
        },
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
                    "classification_rationale": (
                        "The package contains biological assessment evidence, so "
                        "the ESA Section 7 row is applicable in this unit fixture."
                    ),
                },
                {
                    "rule_id": "custer_gallatin_lmp_2022",
                    "expected_applicability": "applicable",
                    "expected_package_section_ids": ["forest_plan_consistency"],
                    "expected_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
                    "expected_source_document_roles": ["forest_plan"],
                    "trigger_terms": ["Custer Gallatin", "Land Management Plan"],
                    "classification_rationale": (
                        "The package resolves to the Custer Gallatin Land "
                        "Management Plan in this unit fixture."
                    ),
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


def _write_real_package_manifest(root: Path, *, review_id: str, eval_file: Path) -> Path:
    path = root / "v1_real_package_review_coverage_v1.json"
    _write_json(
        path,
        {
            "schema_version": "real-package-review-coverage-v1",
            "id": "unit-real-package-review-coverage",
            "version": "0.1.0",
            "required_coverage_class_ids": [
                "current_promotion_reviewer_ready",
            ],
            "coverage_thresholds": {
                "required_slot_count": 1,
                "required_coverage_class_count": 1,
                "distinct_forest_count_min": 1,
                "distinct_package_style_count_min": 1,
                "reviewer_ready_slot_count_min": 1,
                "typed_blocked_slot_count_min": 0,
                "missing_required_slot_count_max": 0,
                "missing_package_authority_count_max": 0,
            },
            "slots": [
                {
                    "slot_id": "v1-unit-slot",
                    "label": "V1 unit slot",
                    "review_id": review_id,
                    "package_label": "V1 unit package",
                    "coverage_class_id": "current_promotion_reviewer_ready",
                    "forest_unit_id": "custer-gallatin-nf",
                    "eval_file": str(eval_file),
                    "required": True,
                    "expected_contract_status": "reviewer_ready",
                    "package_authority": {
                        "intake_package_path": str(root / "authority-package"),
                    },
                }
            ],
        },
    )
    (root / "authority-package").mkdir(parents=True, exist_ok=True)
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
        "authority_path_classifications": ["controlling"],
        "primary_authority_path_classification": "controlling",
        "retrieval_trace_ids": [f"retrieval:{rule_id}"],
        "graph_path_ids": [f"graph:{rule_id}"],
        "supporting_source_record_ids": [],
        "residual_risk_categories": [],
        "unresolved_issue_refs": [],
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
        "primary_authority_path_classification": finding[
            "primary_authority_path_classification"
        ],
        "authority_path_classifications": finding["authority_path_classifications"],
        "retrieval_trace_ids": finding["retrieval_trace_ids"],
        "graph_path_ids": finding["graph_path_ids"],
        "supporting_source_record_ids": finding["supporting_source_record_ids"],
        "residual_risk_categories": finding["residual_risk_categories"],
        "unresolved_issue_refs": finding["unresolved_issue_refs"],
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


def _compact_evidence_for_row(evidence: dict) -> dict:
    return {
        "citation_label": evidence["citation_label"],
        "source_record_id": evidence.get("source_record_id"),
        "title": evidence.get("title"),
        "chunk_id": evidence.get("chunk_id"),
        "text": evidence["evidence_span"]["text"],
        "section": evidence["provenance"].get("section"),
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
