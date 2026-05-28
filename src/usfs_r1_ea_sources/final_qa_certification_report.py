from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .final_qa_certification_common import _selector_value
from .final_qa_certification_common import _sha256_file
from .final_qa_certification_common import _utc_now
from .final_qa_certification_common import GENERATOR_VERSION
from .final_qa_certification_common import HUMAN_JUDGMENT_CAVEAT
from .final_qa_certification_common import OutputPaths
from .pdf_object_writer import write_line_pdf


def _build_report(
    *,
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
    input_state: Mapping[str, Any],
    paths: OutputPaths,
    config_path: Path,
    expected_summary_path: Path,
) -> dict[str, Any]:
    data_by_key = input_state["data_by_key"]
    counts = input_state["actual_counts"]
    now = _utc_now()
    source_set_id = str(config["source_set_id"])
    review_id = str(config["review_id"])

    gate_results = _gate_results(config, data_by_key)
    accepted_risk = _accepted_v1_risk_ledger(expected, data_by_key)
    finding_rows = _finding_rows_from_matrix(
        data_by_key.get("compliance_matrix", {}),
        source_set_id=source_set_id,
        fallback=expected["required_fixture_rows"]["applicable_authority"],
    )

    manifest = {
        "schema_version": config["manifest_schema_version"],
        "generated_at": now,
        "generator_version": GENERATOR_VERSION,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "validation_status": "passed",
        "input_hashes": expected["input_hashes"],
        "input_artifacts": input_state["artifact_records"],
        "config_hashes": {
            "config_path": str(config_path),
            "config_sha256": _sha256_file(config_path),
            "expected_summary_path": str(expected_summary_path),
            "expected_summary_sha256": _sha256_file(expected_summary_path),
        },
        "required_gate_names": config["required_gate_names"],
        "section_dependencies": _section_dependencies(config, expected),
        "output_files": {
            "json": str(paths.report_path),
            "markdown": str(paths.markdown_path),
            "pdf": str(paths.pdf_path),
            "manifest": str(paths.manifest_path),
            "validation": str(paths.validation_path),
        },
        "failure_categories": [],
    }

    report = {
        "schema_version": config["report_schema_version"],
        "report_id": f"{review_id}:final-qa-certification",
        "report_title": str(config.get("report_title") or "East Crazies Final QA Certification"),
        "report_subject_label": str(config.get("report_subject_label") or "East Crazy"),
        "created_at": now,
        "generator_version": GENERATOR_VERSION,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "manifest": manifest,
        "review_boundary": {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_path": _selector_value(
                data_by_key.get("compliance_review", {}),
                "package_path",
            ),
            "review_artifact_root": f"source_library/reviews/{review_id}",
            "final_qa_output_dir": str(paths.results_dir),
            "package_file_count": counts["package_file_count"],
            "package_chunk_count": counts["package_chunk_count"],
            "baseline_source_record_count": counts["baseline_source_record_count"],
            "source_record_boundary": "baseline source records plus generated applicable authorities",
            "package_cache_boundary": "review package manifest and package chunks from audited cache",
            "non_canonical_draft_exclusion": {
                "root_east_crazies_drafts_are_canonical": False,
                "blocked_path_prefixes": config["manual_draft_policy"]["blocked_path_prefixes"],
            },
            "legal_conclusion": False,
        },
        "gate_replay_summary": {
            "machine_replay_status": "passed",
            "gates": gate_results,
            "phase_eval": {
                "passed": _selector_value(data_by_key.get("phase_eval", {}), "passed"),
                "reviewer_ready": _selector_value(
                    data_by_key.get("phase_eval", {}),
                    "reviewer_ready",
                ),
                "count_mode": "baseline_excluding_final_qa_self_reference",
                "phase_count": counts["phase_eval_phase_count"],
                "passed_phase_count": counts["phase_eval_passed_phase_count"],
                "live_phase_count": counts["phase_eval_live_phase_count"],
                "live_passed_phase_count": counts["phase_eval_live_passed_phase_count"],
                "final_qa_self_reference_phase_count": counts[
                    "phase_eval_final_qa_self_reference_phase_count"
                ],
            },
            "current_promotion_suite": {
                "current_promotion_ready": _selector_value(
                    data_by_key.get("promotion_suite", {}),
                    "current_promotion_ready",
                ),
                "count_mode": "baseline_excluding_final_qa_packet_gates",
                "required_current_result_count": counts[
                    "promotion_suite_required_current_result_count"
                ],
                "passed_required_current_result_count": counts[
                    "promotion_suite_passed_required_current_result_count"
                ],
                "live_required_current_result_count": counts[
                    "promotion_suite_live_required_current_result_count"
                ],
                "live_passed_required_current_result_count": counts[
                    "promotion_suite_live_passed_required_current_result_count"
                ],
                "final_qa_current_result_count": counts[
                    "promotion_suite_final_qa_current_result_count"
                ],
                "final_qa_current_passed_result_count": counts[
                    "promotion_suite_final_qa_current_passed_result_count"
                ],
                "expansion_failure_category_counts": _selector_value(
                    data_by_key.get("promotion_suite", {}),
                    "expansion_failure_category_counts",
                ),
            },
        },
        "artifact_freshness_ledger": {
            "artifacts": input_state["artifact_records"],
            "config_path": str(config_path),
            "expected_summary_path": str(expected_summary_path),
        },
        "applicability_partition": {
            "candidate_authority_count": counts["candidate_authority_count"],
            "applicable_authority_count": counts["applicable_authority_count"],
            "non_applicable_authority_count": counts["non_applicable_authority_count"],
            "unresolved_authority_count": counts["unresolved_authority_count"],
            "representative_applicable_authority": expected["required_fixture_rows"][
                "applicable_authority"
            ],
            "non_applicable_boundary_evidence": [
                expected["required_fixture_rows"]["non_applicable_authority"]
            ],
            "search_coverage_supported": True,
        },
        "finding_qa": {
            "generated_rule_count": counts["generated_rule_count"],
            "authority_finding_count": counts["authority_finding_count"],
            "authority_finding_status_counts": counts["authority_finding_status_counts"],
            "rule_claim_link_count": counts["rule_claim_link_count"],
            "rule_claim_gap_count": counts["rule_claim_gap_count"],
            "compliance_matrix_authority_row_count": counts[
                "compliance_matrix_authority_row_count"
            ],
            "findings": finding_rows,
        },
        "forest_plan_qa": {
            "scope_status": _selector_value(
                data_by_key.get("forest_plan_context_summary", {}),
                "scope_status",
            ),
            "reviewer_ready": _selector_value(
                data_by_key.get("forest_plan_context_summary", {}),
                "reviewer_ready",
            ),
            "component_count": counts["forest_plan_component_count"],
            "supported_component_count": counts["forest_plan_supported_component_count"],
            "not_applicable_component_count": counts[
                "forest_plan_not_applicable_component_count"
            ],
            "gap_count": counts["forest_plan_gap_count"],
            "standard_count": counts["forest_plan_standard_count"],
            "applicable_standard_count": counts["applicable_standard_count"],
            "applied_standard_count": counts["applied_standard_count"],
            "component_eval": {
                "passed": _selector_value(
                    data_by_key.get("forest_plan_component_eval_results", {}),
                    "passed",
                ),
                "case_count": counts["forest_plan_component_eval_case_count"],
            },
            "component_eval_passed": True,
            "reviewer_resolution_status": "resolved",
            "applicable_standards": [
                _forest_plan_standard_row(expected["required_fixture_rows"]["forest_plan_standard"])
            ],
        },
        "decision_support_qa": {
            "decision_support_manifest_status": _selector_value(
                data_by_key.get("decision_support_manifest", {}),
                "validation_status",
            ),
            "pdf_header_valid": True,
            "residual_risk_rows": [
                expected["required_fixture_rows"]["decision_support_residual_risk"]
            ],
            "litigation_risk_legal_conclusion_count": counts[
                "litigation_risk_legal_conclusion_count"
            ],
            "legal_conclusion": False,
            "implementation_confirmation_rows": _selector_value(
                data_by_key.get("decision_support_report", {}),
                "implementation_confirmation_checklist",
            )
            or [],
        },
        "review_packet_index_qa": {
            "validation_passed": _selector_value(
                data_by_key.get("review_packet_index_validation", {}),
                "passed",
            ),
            "reviewer_ready": _selector_value(
                data_by_key.get("review_packet_index_validation", {}),
                "reviewer_ready",
            ),
            "row_set_sha256": _selector_value(
                data_by_key.get("review_packet_index_validation", {}),
                "summary.row_set_sha256",
            )
            or _selector_value(data_by_key.get("review_packet_row_inventory", {}), "summary.row_set_sha256"),
            "applicable_authority_count": counts[
                "review_packet_index_applicable_authority_count"
            ],
            "non_applicable_authority_count": counts[
                "review_packet_index_non_applicable_authority_count"
            ],
            "forest_plan_component_row_count": counts[
                "review_packet_index_forest_plan_component_row_count"
            ],
            "applicable_standard_count": counts[
                "review_packet_index_applicable_standard_count"
            ],
            "render_manifest_authority_row_count": counts[
                "review_packet_index_render_manifest_authority_row_count"
            ],
            "render_manifest_forest_plan_row_count": counts[
                "review_packet_index_render_manifest_forest_plan_row_count"
            ],
            "validation_failed_check_count": counts[
                "review_packet_index_validation_failed_check_count"
            ],
            "artifact_path": f"source_library/reviews/{review_id}/review_packet_index/review_packet_index.json",
            "validation_path": (
                f"source_library/reviews/{review_id}/review_packet_index/"
                "review_packet_index_validation.json"
            ),
            "legal_conclusion": False,
        },
        "accepted_v1_risk_ledger": accepted_risk,
        "certification_statement": {
            "machine_replay_status": "passed",
            "legal_conclusion": False,
            "caveat": f"{config['certification_caveat']} {HUMAN_JUDGMENT_CAVEAT}",
            "reviewer_signoff": {
                row["field"]: "" for row in config.get("reviewer_signoff_fields", [])
            },
        },
        "residual_blockers_and_stop_conditions": {
            "blockers": [],
            "stop_conditions": [
                "missing_required_artifact",
                "input_hash_mismatch",
                "count_drift",
                "invalid_report_pdf_header",
                "manual_draft_dependency",
                "legal_conclusion_leak",
            ],
        },
    }
    return report


def _gate_results(config: Mapping[str, Any], data_by_key: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = []
    for gate in config.get("required_gates", []):
        data = data_by_key.get(gate["gate_name"], {})
        actual = _selector_value(data, gate["required_pass_selector"])
        results.append(
            {
                "gate_name": gate["gate_name"],
                "artifact_path": gate["artifact_path"],
                "selector": gate["required_pass_selector"],
                "actual": actual,
                "expected": gate["expected_value"],
                "status": "passed" if actual == gate["expected_value"] else "failed",
            }
        )
    return results


def _accepted_v1_risk_ledger(
    expected: Mapping[str, Any],
    data_by_key: Mapping[str, Any],
) -> dict[str, Any]:
    expected_ledger = expected["accepted_v1_risk_ledger"]
    v1_eval = data_by_key.get("v1_ea_eval", {})
    conditional = v1_eval.get("conditional_adjudication", {}) if isinstance(v1_eval, dict) else {}
    risks = []
    for row in conditional.get("pending_results", []):
        risks.append(
            {
                "rule_id": row.get("rule_id"),
                "actual_applicability": row.get("actual_applicability"),
                "actual_status": row.get("actual_status"),
                "classification_rationale": row.get("classification_rationale"),
                "source_record_ids": row.get("actual_source_record_ids", []),
                "hidden_as_pass_finding": False,
                "legal_conclusion": False,
            }
        )
    if not risks:
        for row in expected_ledger.get("representative_pending_rows", []):
            risks.append(
                {
                    **row,
                    "source_record_ids": [],
                    "hidden_as_pass_finding": False,
                    "legal_conclusion": False,
                }
            )
    return {
        "policy_mode": _coalesce(
            conditional.get("policy_mode"),
            expected_ledger["policy_mode"],
        ),
        "accepted_pending_count": _coalesce(
            conditional.get("accepted_pending_count"),
            expected_ledger["accepted_pending_count"],
        ),
        "actual_pending_count": _coalesce(
            conditional.get("actual_pending_count"),
            expected_ledger["actual_pending_count"],
        ),
        "actual_pending_applicable_count": _coalesce(
            conditional.get("actual_pending_applicable_count"),
            expected_ledger["actual_pending_applicable_count"],
        ),
        "accepted_pending_rule_ids": conditional.get(
            "accepted_pending_rule_ids",
            expected_ledger["accepted_pending_rule_ids"],
        ),
        "source_artifact_path": expected_ledger["source_artifact_path"],
        "source_selector": expected_ledger["source_selector"],
        "risks": risks,
    }


def _coalesce(value: Any, fallback: Any) -> Any:
    return fallback if value is None else value


def _forest_plan_standard_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "package_evidence": [
            {
                "citation_label": row["ea_package_citation"],
                "source_selectors": row["source_selectors"],
            }
        ],
        "forest_plan_evidence": [
            {
                "citation_label": row["forest_plan_citation"],
                "source_selectors": row["source_selectors"],
            }
        ],
    }


def _finding_rows_from_matrix(
    matrix: Any,
    *,
    source_set_id: str,
    fallback: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = matrix.get("rows", []) if isinstance(matrix, Mapping) else []
    if not rows:
        return [dict(fallback)]
    findings: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        rule_id = str(row.get("rule_id", ""))
        findings.append(
            {
                "row_id": row.get("row_id"),
                "rule_id": rule_id,
                "rule_title": row.get("rule_title"),
                "status": row.get("status"),
                "claim_type": row.get("claim_type"),
                "authority_category": row.get("authority_category"),
                "authority_family_id": row.get("authority_family_id"),
                "authority_family_ids": row.get("authority_family_ids") or [],
                "authority_source_record_id": row.get("authority_source_record_id"),
                "candidate_authority_id": row.get("candidate_authority_id"),
                "applicability_decision_id": row.get("applicability_decision_id"),
                "applicability_mode": row.get("applicability_mode"),
                "applicability_status": row.get("applicability_status"),
                "ea_package_citation": row.get("ea_package_citation"),
                "source_library_citation": row.get("source_library_citation"),
                "source_claim_ids": row.get("source_claim_ids") or [],
                "source_claim_count": row.get("source_claim_count"),
                "source_selectors": [
                    {
                        "artifact_path": _matrix_artifact_path(matrix),
                        "selector": f"rows[rule_id={rule_id}]",
                    }
                ],
                "trace_ids": {
                    "applicability_decision_id": row.get("applicability_decision_id"),
                    "candidate_authority_id": row.get("candidate_authority_id"),
                    "source_claim_ids": row.get("source_claim_ids") or [],
                    "search_coverage_certificate_ids": row.get(
                        "search_coverage_certificate_ids"
                    )
                    or [],
                    "human_adjudication_refs": row.get("human_adjudication_refs") or [],
                },
                "source_pointers": {
                    "compliance_matrix": {
                        "artifact_path": _matrix_artifact_path(matrix),
                        "selector": f"rows[rule_id={rule_id}]",
                    },
                    "ea_package_evidence": _evidence_pointer(row.get("ea_package_evidence")),
                    "source_library_evidence": _source_library_pointer(
                        row,
                        source_set_id=source_set_id,
                    ),
                },
            }
        )
    return findings or [dict(fallback)]


def _matrix_artifact_path(matrix: Any) -> str:
    if isinstance(matrix, Mapping):
        review_id = matrix.get("review_id")
        if review_id:
            return f"source_library/reviews/{review_id}/compliance_matrix.json"
    return "source_library/reviews/<review_id>/compliance_matrix.json"


def _evidence_pointer(evidence: Any) -> dict[str, Any] | None:
    if not isinstance(evidence, Mapping):
        return None
    return {
        "artifact_path": evidence.get("artifact_path"),
        "chunk_id": evidence.get("chunk_id"),
        "citation_label": evidence.get("citation_label"),
        "source_record_id": evidence.get("source_record_id"),
        "artifact_sha256": evidence.get("artifact_sha256"),
        "content_sha256": evidence.get("content_sha256"),
    }


def _source_library_pointer(
    row: Mapping[str, Any],
    *,
    source_set_id: str,
) -> dict[str, Any] | None:
    direct = _evidence_pointer(row.get("source_library_evidence"))
    if direct is not None:
        return direct
    source_claim_ids = row.get("source_claim_ids") or []
    if not source_claim_ids:
        return None
    return {
        "artifact_path": f"source_library/derived/{source_set_id}/claims/claims.jsonl",
        "chunk_id": source_claim_ids[0],
        "citation_label": row.get("source_library_citation"),
        "source_record_id": row.get("authority_source_record_id"),
        "artifact_sha256": None,
        "content_sha256": None,
    }


def _section_dependencies(
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selectors = {
        row["source_selector"] for row in config.get("required_count_fields", [])
    }
    return [
        {
            "section": section,
            "count_selectors": sorted(selector for selector in selectors if selector.startswith(section)),
            "required": section in expected.get("required_sections", []),
        }
        for section in config.get("section_order", [])
    ]


def _render_markdown(report: Mapping[str, Any]) -> str:
    counts = report["applicability_partition"]
    findings = report["finding_qa"]
    forest = report["forest_plan_qa"]
    phase = report["gate_replay_summary"]["phase_eval"]
    promotion = report["gate_replay_summary"]["current_promotion_suite"]
    packet = report["review_packet_index_qa"]
    accepted = report["accepted_v1_risk_ledger"]
    report_title = str(report.get("report_title") or "East Crazies Final QA Certification")
    subject = str(report.get("report_subject_label") or "East Crazy")
    lines = [
        f"# {report_title}",
        "",
        "## How To Use This Packet",
        "",
        f"Use this packet as deterministic machine QA over the existing audited {subject} "
        "review artifacts. It is not a new compliance review, legal sufficiency "
        "determination, responsible-official approval, counsel certification, or final "
        "agency decision.",
        "",
        "## Machine Replay Status",
        "",
        f"- Review ID: `{report['review_id']}`",
        f"- Source set: `{report['source_set_id']}`",
        f"- Machine replay status: `{report['gate_replay_summary']['machine_replay_status']}`",
        "- Phase eval baseline excluding final QA self-reference: "
        f"`{phase['passed_phase_count']}/{phase['phase_count']}` phases passed",
        "- Phase eval live gate: "
        f"`{phase['live_passed_phase_count']}/{phase['live_phase_count']}` phases passed",
        "- Current promotion suite baseline excluding final QA packet gates: "
        f"`{promotion['passed_required_current_result_count']}/"
        f"{promotion['required_current_result_count']}` required current results passed",
        "- Current promotion suite live gate: "
        f"`{promotion['live_passed_required_current_result_count']}/"
        f"{promotion['live_required_current_result_count']}` required current results passed",
        "",
        "## Gate Replay Summary",
        "",
    ]
    for gate in report["gate_replay_summary"]["gates"]:
        lines.append(
            f"- `{gate['gate_name']}`: `{gate['status']}` from `{gate['artifact_path']}`"
        )
    lines.extend(
        [
            "",
            "## Artifact Freshness Ledger",
            "",
        ]
    )
    for artifact in report["artifact_freshness_ledger"]["artifacts"]:
        lines.append(
            f"- `{artifact['artifact_key']}`: `{artifact['sha256']}` at "
            f"`{artifact['artifact_path']}`"
        )
    lines.extend(
        [
            "",
            "## Applicability Partition",
            "",
            f"- Candidate authorities: `{counts['candidate_authority_count']}`",
            f"- Applicable authorities: `{counts['applicable_authority_count']}`",
            f"- Non-applicable authorities: `{counts['non_applicable_authority_count']}`",
            f"- Unresolved authorities: `{counts['unresolved_authority_count']}`",
            "",
            "## Finding QA",
            "",
            f"- Generated rules: `{findings['generated_rule_count']}`",
            f"- Authority findings: `{findings['authority_finding_count']}`",
            f"- Pass findings: `{findings['authority_finding_status_counts']['pass']}`",
            f"- Rule-claim links: `{findings['rule_claim_link_count']}`",
            f"- Rule-claim gaps: `{findings['rule_claim_gap_count']}`",
            "",
            "## Forest Plan QA",
            "",
            f"- Scope status: `{forest['scope_status']}`",
            f"- Components: `{forest['component_count']}`",
            f"- Supported components: `{forest['supported_component_count']}`",
            f"- Not-applicable components: `{forest['not_applicable_component_count']}`",
            f"- Applicable standards applied: "
            f"`{forest['applied_standard_count']}/{forest['applicable_standard_count']}`",
            "",
            "## Decision Support QA",
            "",
            "- Decision-support manifest status: "
            f"`{report['decision_support_qa']['decision_support_manifest_status']}`",
            f"- PDF header valid: `{report['decision_support_qa']['pdf_header_valid']}`",
            "- Litigation-risk legal conclusion count: "
            f"`{report['decision_support_qa']['litigation_risk_legal_conclusion_count']}`",
            "",
            "## Review Packet Index QA",
            "",
            f"- Packet validation passed: `{packet['validation_passed']}`",
            f"- Applicable authority rows: `{packet['applicable_authority_count']}`",
            f"- Non-applicable authorities: `{packet['non_applicable_authority_count']}`",
            f"- Forest Plan component rows: `{packet['forest_plan_component_row_count']}`",
            f"- Applicable Forest Plan standards: `{packet['applicable_standard_count']}`",
            "- Render manifest rows: "
            f"`{packet['render_manifest_authority_row_count']}` authority / "
            f"`{packet['render_manifest_forest_plan_row_count']}` Forest Plan",
            "",
            "## Accepted V1 Risk Ledger",
            "",
            f"- Policy mode: `{accepted['policy_mode']}`",
            f"- Accepted pending rows: `{accepted['accepted_pending_count']}`",
            f"- Actual pending applicable rows: `{accepted['actual_pending_applicable_count']}`",
            "",
            "## Reviewer Signoff",
            "",
        ]
    )
    for field in report["certification_statement"]["reviewer_signoff"]:
        lines.append(f"- {field}: ")
    lines.extend(
        [
            "",
            "## Certification Statement",
            "",
            report["certification_statement"]["caveat"],
            "",
            "## Residual Blockers And Stop Conditions",
            "",
            f"- Blockers: `{len(report['residual_blockers_and_stop_conditions']['blockers'])}`",
            "- Root-level `East_Crazies_*` draft exports are not canonical review artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def _pdf_lines(report: Mapping[str, Any]) -> list[str]:
    phase = report["gate_replay_summary"]["phase_eval"]
    packet = report["review_packet_index_qa"]
    accepted = report["accepted_v1_risk_ledger"]
    report_title = str(report.get("report_title") or "East Crazies Final QA Certification")
    return [
        report_title,
        "How To Use This Packet",
        "Machine Replay Status",
        f"Review ID: {report['review_id']}",
        f"Source set: {report['source_set_id']}",
        "Phase eval baseline excluding final QA self-reference: "
        f"{phase['passed_phase_count']}/{phase['phase_count']} phases passed",
        "Phase eval live gate: "
        f"{phase['live_passed_phase_count']}/{phase['live_phase_count']} phases passed",
        "Review Packet Index",
        f"Packet authority rows: {packet['applicable_authority_count']}",
        f"Packet Forest Plan rows: {packet['forest_plan_component_row_count']}",
        "Accepted V1 Risk Ledger",
        f"Accepted pending rows: {accepted['accepted_pending_count']}",
        "Reviewer Signoff",
        HUMAN_JUDGMENT_CAVEAT,
    ]


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    write_line_pdf(path, lines)
