from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .ea_consistency_decision_support_models import GENERATOR_VERSION
from .ea_consistency_decision_support_models import MANIFEST_SCHEMA_VERSION
from .ea_consistency_decision_support_models import REPORT_SCHEMA_VERSION
from .ea_consistency_decision_support_models import REVIEW_PACKET_ARTIFACT_KEYS
from .ea_consistency_decision_support_models import _DecisionSupportContext
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _dict_list
from .ea_consistency_decision_support_models import _list
from .ea_consistency_decision_support_models import _sha256_file
from .ea_consistency_decision_support_models import _strings
from .ea_consistency_decision_support_models import _resolved_source_library_evidence
from .ea_consistency_decision_support_models import _utc_now
from .ea_consistency_decision_support_rendering import _applicable_standard_rows
from .ea_consistency_decision_support_rendering import _authority_family_id
from .ea_consistency_decision_support_rendering import _basis_rationale
from .ea_consistency_decision_support_rendering import _confirmation_ids_by_selector
from .ea_consistency_decision_support_rendering import _coverage_summary
from .ea_consistency_decision_support_rendering import _evidence
from .ea_consistency_decision_support_rendering import _evidence_list
from .ea_consistency_decision_support_rendering import _forest_findings_by_component
from .ea_consistency_decision_support_rendering import _resolve_selector
from .ea_consistency_decision_support_rendering import _selector
from .ea_consistency_decision_support_rendering import _selector_evidence
from .ea_consistency_decision_support_rendering import _trace


def _build_report(
    context: _DecisionSupportContext,
    validation: dict[str, Any],
) -> dict[str, Any]:
    counts = validation["counts"]
    manifest = _manifest(context, validation)
    authority_rows = _authority_findings(context)
    component_rows = _forest_plan_component_rows(context)
    standard_rows = _applicable_standards(context)
    non_applicable = _non_applicable_boundary(context)
    confirmations = _implementation_confirmations(context)
    residual_risks = _residual_risks(context)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": f"ea-consistency-decision-support:{context.review_id}",
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "generator_version": GENERATOR_VERSION,
        "manifest": manifest,
        "executive_determination": {
            "decision_support_status": "reviewer_ready",
            "decision_use_caveat": context.config["decision_use_caveat"],
            "legal_conclusion": False,
            "review_boundary": {
                "review_id": context.review_id,
                "source_set_id": context.source_set_id,
                "authority_finding_count": counts["authority_finding_count"],
                "non_applicable_authority_count": counts[
                    "non_applicable_authority_count"
                ],
                "forest_plan_component_finding_count": counts[
                    "forest_plan_component_finding_count"
                ],
                "applicable_forest_plan_standard_count": counts[
                    "forest_plan_applicable_standard_count"
                ],
            },
        },
        "record_and_artifact_inventory": _record_inventory(context, validation),
        "applicable_authority_summary": _applicable_authority_summary(
            context,
            authority_rows,
        ),
        "authority_findings": authority_rows,
        "forest_plan_consistency": {
            "component_finding_count": counts["forest_plan_component_finding_count"],
            "supported_component_count": counts["forest_plan_supported_component_count"],
            "not_applicable_component_count": counts[
                "forest_plan_not_applicable_component_count"
            ],
            "gap_count": counts["forest_plan_gap_count"],
            "standard_count": counts["forest_plan_standard_count"],
            "applicable_standard_count": counts["forest_plan_applicable_standard_count"],
            "applied_standard_count": counts["forest_plan_applied_standard_count"],
            "plan_consistency_table_package_record_id": _plan_consistency_source_record_id(
                context
            ),
            "plan_consistency_table_label": _plan_consistency_label(context),
            "component_rows": component_rows,
            "source_selectors": [
                _selector(
                    context.artifacts["forest_plan_component_findings"].path,
                    "findings[*]",
                ),
                _selector(
                    context.artifacts["plan_consistency_table_text"].path,
                    f"source_record_id={_plan_consistency_source_record_id(context)}",
                ),
            ],
        },
        "applicable_forest_plan_standards": standard_rows,
        "non_applicable_authority_boundary": non_applicable,
        "implementation_confirmation_checklist": confirmations,
        "residual_risk_register": residual_risks,
        "validation_and_replay": {
            "passed": True,
            "checks": validation["checks"],
            "replay_commands": [
                (
                    "PYTHONPATH=src python -m usfs_r1_ea_sources "
                    f"ea-consistency-document --output-dir {context.output_dir} "
                    f"--review-id {context.review_id}"
                ),
                (
                    "PYTHONPATH=src python -m usfs_r1_ea_sources "
                    f"phase-eval --output-dir {context.output_dir} --review-id {context.review_id}"
                ),
            ],
        },
    }


def _record_inventory(
    context: _DecisionSupportContext,
    validation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "package_file_count": validation["counts"]["package_file_count"],
        "package_chunk_count": validation["counts"]["package_chunk_count"],
        "generated_rule_pack_ready": True,
        "source_dependencies": _source_dependencies(context),
        "source_selectors": [
            _selector(context.artifacts["package_manifest"].path, "source_record_id=*"),
            _selector(context.artifacts["package_chunks"].path, "chunk_id=*"),
        ],
    }


def _applicable_authority_summary(
    context: _DecisionSupportContext,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    category_counts = Counter(str(row.get("authority_category") or "unknown") for row in rows)
    status_counts = Counter(str(row.get("compliance_status") or "unknown") for row in rows)
    group_order = _strings(context.config.get("authority_group_order"))
    ordered_categories = {
        category: category_counts[category]
        for category in group_order
        if category in category_counts
    }
    ordered_categories.update(
        {
            category: count
            for category, count in sorted(category_counts.items())
            if category not in ordered_categories
        }
    )
    return {
        "applicable_authority_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "category_counts": ordered_categories,
    }


def _authority_findings(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    confirmation_by_rule = _confirmation_ids_by_selector(context, "authority_finding", "rule_id")
    findings_by_rule = {
        str(finding.get("rule_id")): finding
        for finding in _dict_list(context.payload("compliance_review").get("findings"))
        if finding.get("rule_id")
    }
    rows = []
    for row in sorted(
        _dict_list(context.payload("compliance_matrix").get("rows")),
        key=lambda value: str(value.get("rule_id")),
    ):
        rule_id = str(row.get("rule_id"))
        source_evidence = _resolved_source_library_evidence(
            row,
            findings_by_rule.get(rule_id),
        )
        rows.append(
            {
                "rule_id": rule_id,
                "rule_title": row.get("rule_title"),
                "authority_category": row.get("authority_category"),
                "authority_source_record_id": row.get("authority_source_record_id"),
                "authority_family_ids": _strings(row.get("authority_family_ids")),
                "candidate_authority_id": row.get("candidate_authority_id"),
                "applicability_decision_id": row.get("applicability_decision_id"),
                "applicability_status": row.get("applicability_status"),
                "applicability_mode": row.get("applicability_mode"),
                "compliance_status": row.get("status"),
                "requirement": row.get("requirement"),
                "rationale": row.get("rationale"),
                "implementation_confirmation_ids": confirmation_by_rule.get(rule_id, []),
                "source_claim_ids": _strings(row.get("source_claim_ids")),
                "limitations": _strings(row.get("limitations")),
                "ea_package_evidence": [_evidence(row.get("ea_package_evidence"))],
                "source_library_evidence": [_evidence(source_evidence)],
                "trace_ids": [
                    _trace(
                        f"trace:authority:{rule_id}",
                        "applicable_authority",
                        context.artifacts["compliance_matrix"].path,
                        f"rule_id={rule_id}",
                    )
                ],
                "source_selectors": [
                    _selector(context.artifacts["compliance_matrix"].path, f"rule_id={rule_id}"),
                    _selector(context.artifacts["compliance_review"].path, f"rule_id={rule_id}"),
                    _selector(
                        context.artifacts["applicable_authorities"].path,
                        f"candidate_authority_id={row.get('candidate_authority_id')}",
                    ),
                    _selector(
                        context.artifacts["compliance_matrix_render_manifest"].path,
                        f"rows[row_identity.rule_id={rule_id}]",
                    ),
                    _selector(
                        context.artifacts["review_packet_index"].path,
                        f"applicable_authority_rows[rule_id={rule_id}]",
                    ),
                ],
            }
        )
    return rows


def _forest_plan_component_rows(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    rows = []
    for finding in _dict_list(context.payload("forest_plan_component_findings").get("findings")):
        basis = _dict(finding.get("applicability_basis"))
        component_key = str(basis.get("component_key") or "")
        component_id = str(finding.get("component_id") or "")
        rows.append(
            {
                "component_id": component_id,
                "component_key": component_key,
                "component_type": finding.get("component_type"),
                "applicability_status": finding.get("applicability_status"),
                "compliance_status": finding.get("compliance_status"),
                "finding_status": finding.get("finding_status"),
                "rationale": finding.get("rationale"),
                "package_evidence": _evidence_list(finding.get("package_evidence")),
                "forest_plan_evidence": _evidence_list(finding.get("plan_source_evidence")),
                "trace_ids": [
                    _trace(
                        f"trace:forest-plan:{component_key or component_id}",
                        "forest_plan_component",
                        context.artifacts["forest_plan_component_findings"].path,
                        f"component_id={component_id}",
                    )
                ],
                "source_selectors": [
                    _selector(
                        context.artifacts["forest_plan_component_findings"].path,
                        f"component_id={component_id}",
                    )
                ],
            }
        )
    return sorted(rows, key=lambda row: str(row.get("component_id")))


def _applicable_standards(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    findings = _forest_findings_by_component(context)
    confirmation_by_standard = _confirmation_ids_by_selector(
        context,
        "forest_plan_standard",
        "component_key",
    )
    rows = []
    for standard in _applicable_standard_rows(context):
        component_id = str(standard.get("component_id"))
        component_key = str(standard.get("component_key") or component_id)
        finding = findings.get(component_id, {})
        rows.append(
            {
                "component_id": component_id,
                "component_key": component_key,
                "compliance_status": standard.get("compliance_status"),
                "finding_status": standard.get("finding_status"),
                "standard_applied": standard.get("standard_applied"),
                "implementation_confirmation_ids": confirmation_by_standard.get(
                    component_key,
                    [],
                ),
                "package_evidence": _evidence_list(finding.get("package_evidence")),
                "forest_plan_evidence": _evidence_list(finding.get("plan_source_evidence")),
                "trace_ids": [
                    _trace(
                        f"trace:standard:{component_key}",
                        "applicable_forest_plan_standard",
                        context.artifacts["forest_plan_applicable_standard_coverage"].path,
                        f"component_key={component_key}",
                    )
                ],
                "source_selectors": [
                    _selector(
                        context.artifacts["forest_plan_applicable_standard_coverage"].path,
                        f"component_key={component_key}",
                    ),
                    _selector(
                        context.artifacts["forest_plan_component_findings"].path,
                        f"component_id={component_id}",
                    ),
                ],
            }
        )
    return sorted(rows, key=lambda row: str(row.get("component_key")))


def _non_applicable_boundary(context: _DecisionSupportContext) -> dict[str, Any]:
    non_applicable = _dict_list(context.payload("non_applicable_authorities").get("authorities"))
    certificates = _dict_list(context.payload("search_coverage_certificates").get("certificates"))
    certificates_by_id = {
        str(certificate.get("coverage_certificate_id")): certificate
        for certificate in certificates
    }
    summary_rows = []
    category_counts = Counter()
    family_counts = Counter()
    for authority in sorted(
        non_applicable,
        key=lambda value: str(value.get("candidate_authority_id")),
    ):
        category = str(authority.get("authority_category") or "unknown")
        family = _authority_family_id(authority)
        category_counts[category] += 1
        family_counts[family] += 1
        certificate_ids = _strings(authority.get("search_coverage_certificate_ids"))
        summary_rows.append(
            {
                "candidate_authority_id": authority.get("candidate_authority_id"),
                "decision_id": authority.get("decision_id"),
                "authority_category": category,
                "authority_family_id": family,
                "basis_type": authority.get("basis_type"),
                "status": "not_applicable",
                "rationale": _basis_rationale(authority),
                "source_record_ids": _strings(authority.get("source_record_ids")),
                "search_coverage_certificate_ids": certificate_ids,
                "search_coverage": [
                    _coverage_summary(certificates_by_id[certificate_id])
                    for certificate_id in certificate_ids
                    if certificate_id in certificates_by_id
                ],
                "trace_ids": [
                    _trace(
                        f"trace:non-applicable:{authority.get('decision_id')}",
                        "non_applicable_authority",
                        context.artifacts["non_applicable_authorities"].path,
                        f"decision_id={authority.get('decision_id')}",
                    )
                ],
                "source_selectors": [
                    _selector(
                        context.artifacts["non_applicable_authorities"].path,
                        f"decision_id={authority.get('decision_id')}",
                    )
                ],
            }
        )
    return {
        "non_applicable_authority_count": len(summary_rows),
        "category_counts": dict(sorted(category_counts.items())),
        "authority_family_counts": dict(sorted(family_counts.items())),
        "summary_rows": summary_rows,
        "appendix_path": str(context.artifacts["non_applicable_authority_appendix"].path),
        "appendix_markdown_path": str(
            context.artifacts["non_applicable_authority_appendix_markdown"].path
        ),
        "coverage_certificates_path": str(
            context.artifacts["search_coverage_certificates"].path
        ),
    }


def _implementation_confirmations(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    rows = []
    for confirmation in sorted(
        _dict_list(context.config.get("implementation_confirmations")),
        key=lambda value: int(value.get("display_order") or 0),
    ):
        evidence = []
        selectors = []
        for selector in _dict_list(confirmation.get("source_selectors")):
            selectors.append(
                {
                    "artifact_path": selector.get("artifact_path"),
                    "selector": selector.get("selector"),
                    "selector_type": selector.get("selector_type"),
                }
            )
            resolved = _resolve_selector(context, selector)
            if resolved is not None:
                evidence.extend(_selector_evidence(resolved))
        rows.append(
            {
                "confirmation_id": confirmation.get("confirmation_id"),
                "label": confirmation.get("label"),
                "group": confirmation.get("group"),
                "status": "requires_confirmation",
                "evidence_status": confirmation.get("evidence_status"),
                "config_owner": str(context.config_path),
                "allowed_report_wording": confirmation.get("allowed_report_wording"),
                "source_selectors": selectors,
                "evidence": evidence,
                "trace_ids": [
                    _trace(
                        f"trace:confirmation:{confirmation.get('confirmation_id')}",
                        "implementation_confirmation",
                        context.config_path,
                        (
                            "implementation_confirmations.confirmation_id="
                            f"{confirmation.get('confirmation_id')}"
                        ),
                    )
                ],
            }
        )
    return rows


def _residual_risks(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    risk_summary = context.payload("litigation_risk_summary")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_flags = _dict_list(risk_summary.get("risk_flags"))
    forest_queue_item_count = len(forest_queue.get("items") or [])
    coverage_policy = _dict(context.config.get("forest_plan_standard_coverage_policy"))
    component_eval_controls_open_standards = (
        coverage_policy.get("require_all_applicable_standards_applied") is False
        and coverage_policy.get("accepted_basis") == "component_eval_contract_passed"
        and _dict(context.payload("forest_plan_component_eval_results")).get("passed") is True
    )
    if forest_queue_item_count:
        forest_queue_rationale = (
            "Forest Plan reviewer-resolution rows remain visible as component-eval-"
            "controlled system-miss records under the configured contract."
            if component_eval_controls_open_standards
            else "Forest Plan reviewer-resolution rows remain open."
        )
        forest_queue_severity = (
            "informational" if component_eval_controls_open_standards else "reviewer_resolution_open"
        )
    else:
        forest_queue_rationale = "No Forest Plan reviewer-resolution items are open."
        forest_queue_severity = "none"
    return [
        {
            "risk_id": "risk:non-applicable-authority-boundary",
            "category": "non_applicable_authority_boundary",
            "severity": "informational",
            "deterministic_basis": True,
            "legal_conclusion": False,
            "risk_flag_count": len(risk_flags),
            "rationale": (
                "Non-applicable authorities remain excluded from compliance findings by "
                "deterministic applicability decisions with search coverage."
            ),
            "source_artifact_path": str(context.artifacts["litigation_risk_summary"].path),
            "source_selector": "summary.risk_category_counts",
            "trace_ids": [
                _trace(
                    "trace:risk:non-applicable-authority-boundary",
                    "residual_risk",
                    context.artifacts["litigation_risk_summary"].path,
                    "summary.risk_category_counts",
                )
            ],
        },
        {
            "risk_id": "risk:authority-resolution-status",
            "category": "reviewer_resolution",
            "severity": "none",
            "deterministic_basis": True,
            "legal_conclusion": False,
            "pending_resolution_count": (
                authority_resolution.get("summary") or {}
            ).get("pending_resolution_count"),
            "rationale": "No authority reviewer-resolution items are open.",
            "source_artifact_path": str(
                context.artifacts["authority_reviewer_resolution_report"].path
            ),
            "source_selector": "summary.pending_resolution_count",
            "trace_ids": [
                _trace(
                    "trace:risk:authority-resolution-status",
                    "residual_risk",
                    context.artifacts["authority_reviewer_resolution_report"].path,
                    "summary.pending_resolution_count",
                )
            ],
        },
        {
            "risk_id": "risk:forest-plan-resolution-status",
            "category": "reviewer_resolution",
            "severity": forest_queue_severity,
            "deterministic_basis": True,
            "legal_conclusion": False,
            "pending_resolution_count": forest_queue_item_count,
            "rationale": forest_queue_rationale,
            "source_artifact_path": str(
                context.artifacts["forest_plan_reviewer_resolution_queue"].path
            ),
            "source_selector": "items",
            "trace_ids": [
                _trace(
                    "trace:risk:forest-plan-resolution-status",
                    "residual_risk",
                    context.artifacts["forest_plan_reviewer_resolution_queue"].path,
                    "items",
                )
            ],
        },
    ]


def _manifest(
    context: _DecisionSupportContext,
    validation: dict[str, Any],
) -> dict[str, Any]:
    input_hashes = {
        f"{key}_sha256": artifact.sha256
        for key, artifact in sorted(context.artifacts.items())
        if key not in REVIEW_PACKET_ARTIFACT_KEYS
        if artifact.sha256 is not None
    }
    input_hashes["decision_support_config_sha256"] = _sha256_file(context.config_path)
    input_hashes["decision_support_expected_summary_sha256"] = _sha256_file(
        context.expected_summary_path
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "generator_version": GENERATOR_VERSION,
        "generated_at": _utc_now(),
        "validation_status": "passed" if validation["passed"] else "failed",
        "input_hashes": input_hashes,
        "source_dependencies": _source_dependencies(context),
        "section_dependencies": _section_dependencies(context),
        "checks": validation["checks"],
        "failure_categories": validation["failure_categories"],
    }


def _source_dependencies(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    dependencies = [
        {
            "artifact_key": key,
            "artifact_path": str(artifact.path),
            "sha256": None if key in REVIEW_PACKET_ARTIFACT_KEYS else artifact.sha256,
            "hash_contract": "live_validated"
            if key in REVIEW_PACKET_ARTIFACT_KEYS
            else "manifest_input_hash",
        }
        for key, artifact in sorted(context.artifacts.items())
    ]
    dependencies.append(
        {
            "artifact_key": "decision_support_config",
            "artifact_path": str(context.config_path),
            "sha256": _sha256_file(context.config_path),
        }
    )
    dependencies.append(
        {
            "artifact_key": "decision_support_expected_summary",
            "artifact_path": str(context.expected_summary_path),
            "sha256": _sha256_file(context.expected_summary_path),
        }
    )
    return dependencies


def _plan_consistency_source_record_id(context: _DecisionSupportContext) -> str:
    policy = _dict(context.config.get("forest_plan_consistency_source"))
    return str(policy.get("package_source_record_id") or "EA-PACKAGE-042")


def _plan_consistency_label(context: _DecisionSupportContext) -> str:
    policy = _dict(context.config.get("forest_plan_consistency_source"))
    return str(policy.get("label") or "Plan Consistency Table")


def _section_dependencies(context: _DecisionSupportContext) -> dict[str, list[str]]:
    return {
        "executive_determination": [
            str(context.artifacts["applicability_validation"].path),
            str(context.artifacts["compliance_matrix"].path),
        ],
        "record_and_artifact_inventory": [
            str(context.artifacts["package_manifest"].path),
            str(context.artifacts["package_chunks"].path),
        ],
        "applicable_authority_summary": [str(context.artifacts["compliance_matrix"].path)],
        "authority_findings": [
            str(context.artifacts["compliance_matrix"].path),
            str(context.artifacts["applicable_authorities"].path),
            str(context.artifacts["compliance_matrix_render_manifest"].path),
            str(context.artifacts["review_packet_index"].path),
        ],
        "forest_plan_consistency": [
            str(context.artifacts["forest_plan_component_findings"].path),
            str(context.artifacts["forest_plan_context_summary"].path),
            str(context.artifacts["review_packet_row_inventory"].path),
            str(context.artifacts["compliance_matrix_render_manifest"].path),
        ],
        "applicable_forest_plan_standards": [
            str(context.artifacts["forest_plan_applicable_standard_coverage"].path),
            str(context.artifacts["forest_plan_component_findings"].path),
        ],
        "non_applicable_authority_boundary": [
            str(context.artifacts["non_applicable_authorities"].path),
            str(context.artifacts["search_coverage_certificates"].path),
            str(context.artifacts["non_applicable_authority_appendix"].path),
        ],
        "implementation_confirmation_checklist": [
            str(context.config_path),
            str(context.artifacts["package_chunks"].path),
            str(context.artifacts["compliance_matrix"].path),
            str(context.artifacts["forest_plan_applicable_standard_coverage"].path),
        ],
        "residual_risk_register": [
            str(context.artifacts["litigation_risk_summary"].path),
            str(context.artifacts["authority_reviewer_resolution_report"].path),
            str(context.artifacts["forest_plan_reviewer_resolution_queue"].path),
        ],
        "validation_and_replay": [str(context.expected_summary_path)],
        "review_packet_index": [
            str(context.artifacts["review_packet_row_inventory"].path),
            str(context.artifacts["compliance_matrix_render_manifest"].path),
            str(context.artifacts["review_packet_index"].path),
            str(context.artifacts["review_packet_index_validation"].path),
        ],
    }


def _current_counts(context: _DecisionSupportContext) -> dict[str, Any]:
    matrix_rows = _dict_list(context.payload("compliance_matrix").get("rows"))
    applicable = _dict_list(context.payload("applicable_authorities").get("authorities"))
    non_applicable = _dict_list(context.payload("non_applicable_authorities").get("authorities"))
    certificates = _dict_list(context.payload("search_coverage_certificates").get("certificates"))
    forest_summary = _dict(context.payload("forest_plan_component_findings").get("summary"))
    standard_coverage = context.payload("forest_plan_applicable_standard_coverage")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_summary = context.payload("litigation_risk_summary")
    row_inventory_summary = _dict(context.payload("review_packet_row_inventory").get("summary"))
    render_manifest_summary = _dict(
        context.payload("compliance_matrix_render_manifest").get("summary")
    )
    packet_validation_summary = _dict(
        context.payload("review_packet_index_validation").get("summary")
    )
    return {
        "applicable_authority_count": len(applicable),
        "non_applicable_authority_count": len(non_applicable),
        "candidate_authority_count": len(applicable) + len(non_applicable),
        "authority_finding_count": len(matrix_rows),
        "authority_finding_status_counts": dict(
            sorted(Counter(str(row.get("status")) for row in matrix_rows).items())
        ),
        "non_applicable_search_coverage_certificate_count": len(certificates),
        "forest_plan_component_finding_count": forest_summary.get("finding_count"),
        "forest_plan_supported_component_count": forest_summary.get("supported_count"),
        "forest_plan_not_applicable_component_count": forest_summary.get(
            "not_applicable_count"
        ),
        "forest_plan_gap_count": forest_summary.get("gap_count"),
        "forest_plan_standard_count": standard_coverage.get("standard_count"),
        "forest_plan_applicable_standard_count": standard_coverage.get(
            "applicable_standard_count"
        ),
        "forest_plan_applied_standard_count": standard_coverage.get(
            "applied_standard_count"
        ),
        "authority_reviewer_resolution_pending_count": (
            authority_resolution.get("summary") or {}
        ).get("pending_resolution_count"),
        "forest_plan_reviewer_resolution_item_count": len(forest_queue.get("items") or []),
        "litigation_risk_flag_count": (risk_summary.get("summary") or {}).get(
            "risk_flag_count"
        ),
        "litigation_risk_legal_conclusion_count": (
            risk_summary.get("summary") or {}
        ).get("legal_conclusion_count"),
        "review_packet_index_applicable_authority_count": row_inventory_summary.get(
            "applicable_authority_count"
        ),
        "review_packet_index_non_applicable_authority_count": row_inventory_summary.get(
            "non_applicable_authority_count"
        ),
        "review_packet_index_forest_plan_component_row_count": (
            row_inventory_summary.get("forest_plan_component_row_count")
        ),
        "review_packet_index_applicable_standard_count": row_inventory_summary.get(
            "applicable_standard_count"
        ),
        "review_packet_index_render_manifest_authority_row_count": (
            render_manifest_summary.get("authority_row_count")
        ),
        "review_packet_index_render_manifest_forest_plan_row_count": (
            render_manifest_summary.get("forest_plan_row_count")
        ),
        "review_packet_index_validation_failed_check_count": (
            packet_validation_summary.get("failed_check_count")
        ),
        "package_file_count": len(_list(context.payload("package_manifest"))),
        "package_chunk_count": len(_list(context.payload("package_chunks"))),
    }


def _generation_summary(
    *,
    context: _DecisionSupportContext,
    report_dir: Path,
    report_path: Path,
    markdown_path: Path,
    pdf_path: Path,
    manifest_path: Path,
    validation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "ea-consistency-decision-support-generation-summary-v1",
        "created_at": _utc_now(),
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "output_dir": str(report_dir),
        "report_path": str(report_path),
        "markdown_path": str(markdown_path),
        "pdf_path": str(pdf_path),
        "manifest_path": str(manifest_path),
        "passed": validation["passed"],
        "output_written": False,
        "failure_categories": validation["failure_categories"],
        "failure_count": len(validation["failures"]),
        "counts": validation["counts"],
    }
