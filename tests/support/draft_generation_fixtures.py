from __future__ import annotations

import json
from pathlib import Path


RULE_ROWS = [
    ("land_exchange_statutory_authorities", "law", "land_exchange_statutory_authorities", "R1EA-137"),
    ("eo_11990_wetlands", "executive_order", "wetlands_protection_eo11990", "R1EA-104"),
    ("eo_13186_migratory_birds", "executive_order", "migratory_bird_authorities", "R1EA-096"),
    ("esa_section_7", "law", "esa_section7_species_consultation", "R1EA-092"),
    ("montana_shpo_review", "state_requirement", "nhpa_section106_shpo_consultation", "R1EA-083"),
    ("roadless_rule_36cfr_294b", "regulation", "roadless_rule_authorities", "R1EA-067"),
]


def write_minimal_draft_generation_review(
    output_dir: Path,
    *,
    review_id: str = "review-test",
    source_set_id: str = "source-set-test",
) -> Path:
    review_dir = output_dir / "reviews" / review_id
    findings = [_compliance_finding(review_id, rule_id, category, family_id, source_record_id) for rule_id, category, family_id, source_record_id in RULE_ROWS]
    decision_findings = [_decision_support_finding(review_id, rule_id, category, family_id, source_record_id) for rule_id, category, family_id, source_record_id in RULE_ROWS]
    explanation_paths = [_explanation_row(rule_id, family_id, source_record_id) for rule_id, _, family_id, source_record_id in RULE_ROWS]
    packet_rows = [_packet_row(review_id, rule_id, category, family_id, source_record_id) for rule_id, category, family_id, source_record_id in RULE_ROWS]

    _write_json(review_dir / "compliance_validation.json", {"schema_version": "compliance-validation-v0", "passed": True})
    _write_json(
        review_dir / "compliance_review.json",
        {
            "schema_version": "compliance-review-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {"finding_count": len(findings)},
            "findings": findings,
        },
    )
    _write_json(
        review_dir / "authority_explanation_paths.json",
        {
            "schema_version": "authority-explanation-paths-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "validation_passed": True,
                "reviewer_ready": True,
                "finding_path_count": len(explanation_paths),
            },
            "finding_explanation_paths": explanation_paths,
            "non_applicable_explanation_paths": [],
            "pending_resolution_paths": [],
            "adjudicated_authority_paths": [],
        },
    )
    _write_json(
        review_dir / "decision_support" / "ea_consistency_decision_support.json",
        {
            "schema_version": "ea-consistency-decision-support-report-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "executive_determination": {
                "decision_support_status": "reviewer_ready",
                "decision_use_caveat": "Synthetic reviewer-ready draft support only.",
                "legal_conclusion": False,
                "review_boundary": {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                },
            },
            "authority_findings": decision_findings,
            "implementation_confirmation_checklist": [
                {
                    "confirmation_id": "wetland_protections",
                    "label": "Wetland deed restrictions",
                    "status": "requires_confirmation",
                    "config_owner": "config/draft_generation_v1.json",
                    "source_selectors": [
                        {
                            "artifact_path": str(review_dir / "package" / "package_chunks.jsonl"),
                            "selector": "source_record_id=EA-PACKAGE-001;chunk_id=chunk:package:eo_11990_wetlands",
                        }
                    ],
                    "evidence": [
                        _evidence("EA-PACKAGE-001", "EA-PACKAGE-001 (test)", "chunk:package:eo_11990_wetlands")
                    ],
                    "trace_ids": [
                        {
                            "trace_id": "trace:confirmation:wetland_protections",
                            "trace_type": "implementation_confirmation",
                            "source_artifact_path": "config/draft_generation_v1.json",
                            "source_selector": "section_profiles[output_id=unresolved_issue_statements]",
                        }
                    ],
                }
            ],
            "residual_risk_register": [
                {
                    "risk_id": "risk:non-applicable-boundary",
                    "category": "non_applicable_authority_boundary",
                    "severity": "informational",
                    "deterministic_basis": True,
                    "legal_conclusion": False,
                    "source_artifact_path": str(review_dir / "litigation_risk_summary.json"),
                    "source_selector": "risk_flags[0]",
                    "trace_ids": [
                        {
                            "trace_id": "trace:risk:non-applicable-boundary",
                            "trace_type": "residual_risk",
                            "source_artifact_path": str(review_dir / "litigation_risk_summary.json"),
                            "source_selector": "risk_flags[0]",
                        }
                    ],
                }
            ],
            "validation_and_replay": {"passed": True, "checks": [], "replay_commands": []},
        },
    )
    _write_json(
        review_dir / "review_packet_index" / "review_packet_index.json",
        {
            "schema_version": "review-packet-index-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "row_inventory_summary": {
                "applicable_authority_count": len(packet_rows),
                "non_applicable_authority_count": 2,
                "forest_plan_component_row_count": 3,
                "applicable_standard_count": 1,
            },
            "applicable_authority_rows": packet_rows,
            "land_exchange_rows": [packet_rows[0]],
            "non_applicable_authority_boundary": {
                "non_applicable_authority_count": 2,
                "coverage_certificate_count": 2,
                "appendix_path": str(review_dir / "non_applicable_authority_appendix.json"),
                "rows": [
                    {
                        "candidate_authority_id": "candidate:boundary-1",
                        "authority_family_ids": ["outside_scope_family"],
                        "source_record_ids": ["R1EA-999"],
                    }
                ],
            },
            "implementation_confirmation_checklist": [],
            "residual_risk_register": [],
        },
    )
    _write_json(
        review_dir / "non_applicable_authority_appendix.json",
        {
            "schema_version": "non-applicable-authority-appendix-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "non_applicable_authority_count": 2,
                "coverage_certificate_count": 2,
                "all_have_coverage_certificates": True,
                "all_have_rationale": True,
            },
            "authorities": [
                {
                    "candidate_authority_id": "candidate:boundary-1",
                    "authority_category": "law",
                    "authority_document_role": "law",
                    "authority_family_ids": ["outside_scope_family"],
                    "source_record_ids": ["R1EA-999"],
                    "status": "not_applicable",
                    "basis_type": "negative_package_evidence",
                    "rationale": "Synthetic non-applicable authority boundary.",
                    "search_coverage_certificate_ids": ["coverage-1"],
                    "coverage_certificates": [{"coverage_certificate_id": "coverage-1"}],
                },
                {
                    "candidate_authority_id": "candidate:boundary-2",
                    "authority_category": "regulation",
                    "authority_document_role": "regulation",
                    "authority_family_ids": ["outside_scope_family_two"],
                    "source_record_ids": ["R1EA-998"],
                    "status": "not_applicable",
                    "basis_type": "negative_package_evidence",
                    "rationale": "Synthetic non-applicable authority boundary.",
                    "search_coverage_certificate_ids": ["coverage-2"],
                    "coverage_certificates": [{"coverage_certificate_id": "coverage-2"}],
                },
            ],
        },
    )
    _write_json(
        review_dir / "litigation_risk_summary.json",
        {
            "schema_version": "litigation-risk-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "validation_passed": True,
                "legal_conclusion_count": 0,
                "risk_flag_count": 1,
                "risk_category_counts": {"non_applicable_authority_boundary": 1},
            },
            "risk_flags": [{"risk_id": "risk:non-applicable-boundary"}],
        },
    )
    _write_json(
        review_dir / "authority_reviewer_resolution_report.json",
        {
            "schema_version": "authority-reviewer-resolution-report-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "passed": True,
                "reviewer_ready_blocked": False,
                "pending_resolution_count": 0,
                "adjudicated_authority_count": 0,
            },
            "pending_resolution_items": [],
            "adjudicated_authorities": [],
        },
    )
    _write_json(
        review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
        {
            "schema_version": "east-crazies-final-qa-certification-report-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "decision_support_qa": {"legal_conclusion": False},
            "accepted_v1_risk_ledger": {
                "accepted_pending_count": 1,
                "actual_pending_count": 1,
                "actual_pending_applicable_count": 1,
                "policy_mode": "accepted_v1",
                "source_artifact_path": str(review_dir / "authority_explanation_paths.json"),
                "source_selector": "finding_explanation_paths[finding_id=eo_11990_wetlands]",
                "risks": [
                    {
                        "rule_id": "eo_11990_wetlands",
                        "actual_applicability": "applicable",
                        "actual_status": "pass",
                        "classification_rationale": "Synthetic wetlands risk remains pending reviewer review.",
                        "hidden_as_pass_finding": False,
                        "legal_conclusion": False,
                        "source_record_ids": ["R1EA-104"],
                    }
                ],
            },
            "residual_blockers_and_stop_conditions": {"blockers": [], "stop_conditions": []},
            "finding_qa": {"findings": []},
            "review_packet_index_qa": {"validation_passed": True},
        },
    )
    return review_dir


def write_minimal_draft_generation_config(
    path: Path,
    *,
    review_id: str = "review-test",
    source_set_id: str = "source-set-test",
) -> Path:
    payload = {
        "schema_version": "draft-generation-config-v1",
        "generator_version": "draft-generation-v1",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "human_review_caveat": "Synthetic human-review-only draft generation.",
        "prohibited_phrases": [
            "legal sufficiency certified",
            "responsible official approved"
        ],
        "section_order": [
            "issue_summaries",
            "compliance_narrative",
            "authority_coverage_appendix",
            "affected_environment_and_environmental_consequences",
            "unresolved_issue_statements"
        ],
        "section_profiles": [
            {
                "output_id": "issue_summaries",
                "section_type": "citation_bearing_issue_summary",
                "title": "Issue Summaries"
            },
            {
                "output_id": "compliance_narrative",
                "section_type": "compliance_narrative",
                "title": "Compliance Narrative"
            },
            {
                "output_id": "authority_coverage_appendix",
                "section_type": "authority_coverage_appendix",
                "title": "Authority Coverage Appendix"
            },
            {
                "output_id": "affected_environment_and_environmental_consequences",
                "section_type": "environmental_consequences",
                "title": "Affected Environment And Environmental Consequences",
                "minimum_findings": 5,
                "rule_ids": [
                    "eo_11990_wetlands",
                    "eo_13186_migratory_birds",
                    "esa_section_7",
                    "montana_shpo_review",
                    "roadless_rule_36cfr_294b"
                ]
            },
            {
                "output_id": "unresolved_issue_statements",
                "section_type": "unresolved_issue_statement",
                "title": "Reviewer Warnings"
            }
        ]
    }
    _write_json(path, payload)
    return path


def _compliance_finding(
    review_id: str,
    rule_id: str,
    category: str,
    family_id: str,
    source_record_id: str,
) -> dict:
    return {
        "id": rule_id,
        "rule_id": rule_id,
        "rule_title": rule_id.replace("_", " ").title(),
        "status": "pass",
        "applicability_status": "applicable",
        "authority_category": category,
        "authority_source_record_id": source_record_id,
        "authority_family_id": family_id,
        "authority_family_ids": [family_id],
        "candidate_authority_id": f"rule-template:test:{rule_id}",
        "applicability_decision_id": f"decision:{rule_id}",
        "package_evidence_citation": "EA-PACKAGE-001 (test)",
        "source_library_citation": f"{source_record_id} (test)",
    }


def _decision_support_finding(
    review_id: str,
    rule_id: str,
    category: str,
    family_id: str,
    source_record_id: str,
) -> dict:
    confirmation_ids = ["wetland_protections"] if rule_id == "eo_11990_wetlands" else []
    return {
        "rule_id": rule_id,
        "rule_title": rule_id.replace("_", " ").title(),
        "authority_category": category,
        "authority_source_record_id": source_record_id,
        "candidate_authority_id": f"rule-template:test:{rule_id}",
        "applicability_decision_id": f"decision:{rule_id}",
        "applicability_status": "applicable",
        "applicability_mode": "baseline",
        "authority_family_ids": [family_id],
        "compliance_status": "pass",
        "implementation_confirmation_ids": confirmation_ids,
        "source_claim_ids": [f"claim:{rule_id}"],
        "limitations": [],
        "rationale": f"Synthetic rationale for {rule_id}.",
        "requirement": f"Synthetic requirement for {rule_id}.",
        "ea_package_evidence": [
            _evidence("EA-PACKAGE-001", "EA-PACKAGE-001 (test)", f"chunk:package:{rule_id}")
        ],
        "source_library_evidence": [
            _evidence(source_record_id, f"{source_record_id} (test)", f"chunk:source:{rule_id}")
        ],
        "trace_ids": [
            {
                "trace_id": f"trace:authority:{rule_id}",
                "trace_type": "applicable_authority",
                "source_artifact_path": f"source_library/reviews/{review_id}/compliance_matrix.json",
                "source_selector": f"rule_id={rule_id}",
            }
        ],
        "source_selectors": [
            {
                "artifact_path": f"source_library/reviews/{review_id}/compliance_matrix.json",
                "selector": f"rule_id={rule_id}",
            }
        ],
    }


def _explanation_row(rule_id: str, family_id: str, source_record_id: str) -> dict:
    return {
        "finding_id": rule_id,
        "rule_id": rule_id,
        "applicability_status": "applicable",
        "authority_document_role": "law",
        "authority_explanation_id": f"authority-explanation:{rule_id}",
        "authority_family_ids": [family_id],
        "authority_path_classifications": ["controlling"],
        "authority_source_record_id": source_record_id,
        "candidate_authority_id": f"rule-template:test:{rule_id}",
        "candidate_authority_type": "rule_template",
        "explanation_summary": f"controlling authority path for {rule_id}",
        "graph_path_ids": [f"graph-path:{rule_id}"],
        "retrieval_trace_ids": [f"retrieval-trace:{rule_id}"],
        "primary_authority_path_classification": "controlling",
        "residual_risk_categories": [],
        "human_adjudication_refs": [],
        "package_citation": "EA-PACKAGE-001 (test)",
        "status": "pass",
        "unresolved_issue_refs": [],
    }


def _packet_row(
    review_id: str,
    rule_id: str,
    category: str,
    family_id: str,
    source_record_id: str,
) -> dict:
    return {
        "rule_id": rule_id,
        "rule_title": rule_id.replace("_", " ").title(),
        "applicability_decision_id": f"decision:{rule_id}",
        "applicability_mode": "baseline",
        "applicability_status": "applicable",
        "authority_category": category,
        "authority_family_ids": [family_id],
        "authority_source_record_id": source_record_id,
        "candidate_authority_id": f"rule-template:test:{rule_id}",
        "compliance_status": "pass",
        "ea_package_citation": "EA-PACKAGE-001 (test)",
        "render_markdown_marker": f"matrix-row:authority:{rule_id}",
        "row_class": "applicable_authority",
        "row_ledger_id": f"row-ledger:applicable-authority:{rule_id}",
        "source_claim_ids": [f"claim:{rule_id}"],
        "source_library_citation": f"{source_record_id} (test)",
        "canonical_selectors": [
            {
                "artifact_path": f"source_library/reviews/{review_id}/compliance_review.json",
                "selector": f"findings[rule_id={rule_id}]",
            },
            {
                "artifact_path": f"source_library/reviews/{review_id}/decision_support/ea_consistency_decision_support.json",
                "selector": f"authority_findings[rule_id={rule_id}]",
            },
        ],
    }


def _evidence(source_record_id: str, citation_label: str, chunk_id: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "source_record_id": source_record_id,
        "citation_label": citation_label,
        "artifact_sha256": f"artifact-sha256:{source_record_id}",
        "content_sha256": f"content-sha256:{chunk_id}",
        "text_span": {
            "char_start": 0,
            "char_end": 32,
            "excerpt": f"synthetic excerpt for {source_record_id}",
        },
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
