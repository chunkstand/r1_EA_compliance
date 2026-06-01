from __future__ import annotations

from typing import Any

from .ea_consistency_decision_support_models import _DecisionSupportContext
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _dict_list
from .ea_consistency_decision_support_models import _record_check
from .ea_consistency_decision_support_models import _resolved_source_library_evidence
from .ea_consistency_decision_support_models import _strings
from .ea_consistency_decision_support_report_validation import (
    _validate_required_applicable_authority_rows,
)
from .ea_consistency_decision_support_rendering import _applicable_standard_rows
from .ea_consistency_decision_support_rendering import _forest_findings_by_component
from .ea_consistency_decision_support_rendering import _resolve_selector


_REVIEW_PACKET_BOOTSTRAP_ALLOWED_CHECKS = {
    "decision_support_authority_rows_match_applicability",
    "decision_support_report_exists_and_parses",
    "final_qa_authority_rows_match_applicability",
    "final_qa_report_exists_and_parses",
}


def _validate_hashes(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    hash_map = {
        "package_manifest_sha256": "package_manifest",
        "package_chunks_sha256": "package_chunks",
        "compliance_matrix_sha256": "compliance_matrix",
        "compliance_review_sha256": "compliance_review",
        "applicability_validation_sha256": "applicability_validation",
        "applicable_authorities_sha256": "applicable_authorities",
        "non_applicable_authorities_sha256": "non_applicable_authorities",
        "search_coverage_certificates_sha256": "search_coverage_certificates",
        "generated_rule_pack_sha256": "generated_rule_pack",
        "generated_rule_pack_validation_sha256": "generated_rule_pack_validation",
        "forest_plan_component_findings_sha256": "forest_plan_component_findings",
        "forest_plan_applicable_standard_coverage_sha256": (
            "forest_plan_applicable_standard_coverage"
        ),
        "forest_plan_component_eval_results_sha256": "forest_plan_component_eval_results",
        "forest_plan_context_summary_sha256": "forest_plan_context_summary",
        "non_applicable_authority_appendix_sha256": "non_applicable_authority_appendix",
        "non_applicable_authority_appendix_markdown_sha256": (
            "non_applicable_authority_appendix_markdown"
        ),
        "authority_reviewer_resolution_report_sha256": (
            "authority_reviewer_resolution_report"
        ),
        "litigation_risk_summary_sha256": "litigation_risk_summary",
        "plan_consistency_table_text_sha256": "plan_consistency_table_text",
    }
    expected_hashes = _dict(context.expected.get("input_hashes"))
    for hash_key, artifact_key in hash_map.items():
        if hash_key not in expected_hashes:
            continue
        actual = context.artifacts[artifact_key].sha256
        _record_check(
            checks,
            failures,
            name=f"{hash_key}_matches_expected",
            passed=actual == expected_hashes[hash_key],
            failure_category="input_hash_mismatch",
            source_selector=f"input_hashes.{hash_key}",
            expected=expected_hashes[hash_key],
            actual=actual,
        )


def _validate_review_source_set(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    for key, artifact in context.artifacts.items():
        if not isinstance(artifact.payload, dict):
            continue
        review_id = artifact.payload.get("review_id")
        source_set_id = artifact.payload.get("source_set_id")
        if review_id is not None:
            _record_check(
                checks,
                failures,
                name=f"{key}_review_id_matches",
                passed=review_id == context.review_id,
                failure_category="review_source_set_mismatch",
                source_selector=f"{key}.review_id",
                expected=context.review_id,
                actual=review_id,
            )
        if source_set_id is not None:
            _record_check(
                checks,
                failures,
                name=f"{key}_source_set_id_matches",
                passed=source_set_id == context.source_set_id,
                failure_category="review_source_set_mismatch",
                source_selector=f"{key}.source_set_id",
                expected=context.source_set_id,
                actual=source_set_id,
            )


def _validate_readiness(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    matrix = context.payload("compliance_matrix")
    app_validation = context.payload("applicability_validation")
    generated_validation = context.payload("generated_rule_pack_validation")
    forest_findings = context.payload("forest_plan_component_findings")
    standard_coverage = context.payload("forest_plan_applicable_standard_coverage")
    component_eval = _dict(context.payload("forest_plan_component_eval_results"))
    forest_context = context.payload("forest_plan_context_summary")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_summary = context.payload("litigation_risk_summary")
    coverage_policy = _dict(context.config.get("forest_plan_standard_coverage_policy"))
    require_all_standards_applied = coverage_policy.get(
        "require_all_applicable_standards_applied",
        True,
    )
    component_eval_controls_open_standards = (
        require_all_standards_applied is False
        and coverage_policy.get("accepted_basis") == "component_eval_contract_passed"
        and component_eval.get("passed") is True
    )
    readiness_checks = {
        "compliance_matrix_reviewer_ready": (matrix.get("summary") or {}).get(
            "reviewer_ready"
        ),
        "compliance_matrix_validated": (matrix.get("summary") or {}).get("validated"),
        "applicability_validation_passed": app_validation.get("passed"),
        "applicability_reviewer_ready": app_validation.get("reviewer_ready"),
        "generated_rule_pack_ready": app_validation.get("generated_rule_pack_ready"),
        "generated_rule_pack_validation_passed": generated_validation.get("passed"),
        "forest_plan_findings_reviewer_ready": (forest_findings.get("summary") or {}).get(
            "reviewer_ready"
        )
        is True
        or component_eval_controls_open_standards,
        "forest_plan_findings_validation_passed": (forest_findings.get("summary") or {}).get(
            "validation_passed"
        )
        is True
        or component_eval_controls_open_standards,
        "forest_plan_context_reviewer_ready": forest_context.get("reviewer_ready"),
        "forest_plan_context_validation_passed": forest_context.get("validation_passed"),
        "applicable_standards_applied": (
            standard_coverage.get("all_applicable_standards_applied") is True
            or component_eval_controls_open_standards
        ),
        "applicable_standard_coverage_passed": (
            standard_coverage.get("passed") is True or component_eval_controls_open_standards
        ),
        "authority_resolution_clear": (
            authority_resolution.get("summary") or {}
        ).get("pending_resolution_count")
        == 0,
        "forest_plan_resolution_clear": len(forest_queue.get("items") or []) == 0
        or component_eval_controls_open_standards,
        "risk_summary_deterministic_only": (risk_summary.get("summary") or {}).get(
            "deterministic_only"
        ),
        "risk_summary_has_no_legal_conclusions": (
            risk_summary.get("summary") or {}
        ).get("legal_conclusion_count")
        == 0,
    }
    for name, actual in readiness_checks.items():
        _record_check(
            checks,
            failures,
            name=name,
            passed=actual is True,
            failure_category=(
                "reviewer_resolution_open"
                if name.endswith("_clear")
                else "residual_risk_legal_conclusion"
                if name.endswith("legal_conclusions")
                else "stale_artifact"
            ),
            source_selector=name,
            expected=True,
            actual=actual,
        )


def _validate_authority_rows(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    rows = _dict_list(context.payload("compliance_matrix").get("rows"))
    findings_by_rule = {
        str(finding.get("rule_id")): finding
        for finding in _dict_list(context.payload("compliance_review").get("findings"))
        if finding.get("rule_id")
    }
    evidence_policy = _dict(context.config.get("authority_evidence_policy"))
    allowed_single_evidence_statuses = {
        str(status)
        for status in _strings(evidence_policy.get("allow_single_evidence_statuses"))
    }
    seen: set[str] = set()
    duplicates: list[str] = []
    missing_evidence: list[str] = []
    for row in rows:
        rule_id = str(row.get("rule_id") or "")
        if rule_id in seen:
            duplicates.append(rule_id)
        seen.add(rule_id)
        missing_dual_evidence_allowed = (
            str(row.get("status") or "") in allowed_single_evidence_statuses
        )
        if (
            not row.get("ea_package_evidence")
            or not _resolved_source_library_evidence(row, findings_by_rule.get(rule_id))
        ) and not missing_dual_evidence_allowed:
            missing_evidence.append(rule_id)
    _record_check(
        checks,
        failures,
        name="applicable_authority_rows_unique",
        passed=not duplicates,
        failure_category="duplicate_applicable_authority_row",
        source_selector="compliance_matrix.rows.rule_id",
        expected=[],
        actual=duplicates,
    )
    _record_check(
        checks,
        failures,
        name="applicable_authority_rows_have_dual_evidence",
        passed=not missing_evidence,
        failure_category="applicable_authority_missing_dual_evidence",
        source_selector="compliance_matrix.rows.evidence",
        expected=[],
        actual=missing_evidence,
    )
    _validate_required_applicable_authority_rows(
        rows=rows,
        expected=context.expected,
        checks=checks,
        failures=failures,
        source_selector="compliance_matrix.rows",
    )


def _validate_review_packet_index(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    matrix = context.payload("compliance_matrix")
    inventory = context.payload("review_packet_row_inventory")
    render_manifest = context.payload("compliance_matrix_render_manifest")
    packet_index = context.payload("review_packet_index")
    validation = context.payload("review_packet_index_validation")
    matrix_rows = _dict_list(matrix.get("rows"))
    expected_authority_ids = {str(row.get("rule_id")) for row in matrix_rows if row.get("rule_id")}
    inventory_authority_ids = {
        str(row.get("rule_id"))
        for row in _dict_list(inventory.get("applicable_authority_rows"))
        if row.get("rule_id")
    }
    packet_authority_ids = {
        str(row.get("rule_id"))
        for row in _dict_list(packet_index.get("applicable_authority_rows"))
        if row.get("rule_id")
    }
    render_authority_ids = {
        str(_dict(row.get("row_identity")).get("rule_id"))
        for row in _dict_list(render_manifest.get("rows"))
        if row.get("row_class") == "applicable_authority"
        and _dict(row.get("row_identity")).get("rule_id")
    }
    forest_matrix_ids = {
        str(row.get("component_id"))
        for row in _dict_list(_dict(matrix.get("forest_plan_compliance")).get("rows"))
        if row.get("component_id")
    }
    inventory_forest_ids = {
        str(row.get("component_id"))
        for row in _dict_list(inventory.get("forest_plan_component_rows"))
        if row.get("component_id")
    }
    packet_forest_ids = {
        str(row.get("component_id"))
        for row in _dict_list(packet_index.get("forest_plan_component_rows"))
        if row.get("component_id")
    }
    render_forest_ids = {
        str(_dict(row.get("row_identity")).get("component_id"))
        for row in _dict_list(render_manifest.get("rows"))
        if row.get("row_class") == "forest_plan_component"
        and _dict(row.get("row_identity")).get("component_id")
    }
    packet_summary = _dict(packet_index.get("row_inventory_summary"))
    validation_summary = _dict(validation.get("summary"))
    bootstrap_allowed = _review_packet_bootstrap_allowed(validation)
    readiness_checks = {
        "review_packet_index_validation_passed": (
            validation.get("passed") is True or bootstrap_allowed
        ),
        "review_packet_index_validation_reviewer_ready": (
            validation.get("reviewer_ready") is True or bootstrap_allowed
        ),
        "review_packet_index_validation_no_failed_checks": (
            validation_summary.get("failed_check_count") == 0 or bootstrap_allowed
        ),
        "review_packet_index_schema_matches": (
            packet_index.get("schema_version") == "review-packet-index-v1"
        ),
        "review_packet_row_inventory_schema_matches": (
            inventory.get("schema_version") == "review-packet-row-inventory-v1"
        ),
        "compliance_matrix_render_manifest_schema_matches": (
            render_manifest.get("schema_version") == "compliance-matrix-render-manifest-v1"
        ),
        "compliance_matrix_render_manifest_passed": (
            _dict(render_manifest.get("summary")).get("passed") is True
        ),
    }
    for name, passed in readiness_checks.items():
        _record_check(
            checks,
            failures,
            name=name,
            passed=passed,
            failure_category="missing_packet_index_row"
            if name.startswith("review_packet")
            else "missing_matrix_render_row",
            source_selector=f"review_packet_index.{name}",
            expected=True,
            actual=passed,
        )
    row_sets = {
        "inventory": inventory_authority_ids,
        "render_manifest": render_authority_ids,
        "packet_index": packet_authority_ids,
    }
    for name, row_ids in row_sets.items():
        _record_check(
            checks,
            failures,
            name=f"{name}_authority_rows_match_compliance_matrix",
            passed=row_ids == expected_authority_ids,
            failure_category=(
                "missing_matrix_render_row"
                if name == "render_manifest"
                else "missing_packet_index_row"
            ),
            source_selector=f"review_packet_index.{name}.authority_rows",
            expected=sorted(expected_authority_ids),
            actual={
                "missing": sorted(expected_authority_ids - row_ids),
                "extra": sorted(row_ids - expected_authority_ids),
            },
        )
    forest_sets = {
        "inventory": inventory_forest_ids,
        "render_manifest": render_forest_ids,
        "packet_index": packet_forest_ids,
    }
    for name, row_ids in forest_sets.items():
        _record_check(
            checks,
            failures,
            name=f"{name}_forest_plan_rows_match_compliance_matrix",
            passed=row_ids == forest_matrix_ids,
            failure_category=(
                "missing_matrix_render_row"
                if name == "render_manifest"
                else "missing_forest_plan_row"
            ),
            source_selector=f"review_packet_index.{name}.forest_plan_rows",
            expected=sorted(forest_matrix_ids),
            actual={
                "missing": sorted(forest_matrix_ids - row_ids),
                "extra": sorted(row_ids - forest_matrix_ids),
            },
        )
    _record_check(
        checks,
        failures,
        name="review_packet_non_applicable_boundary_present",
        passed=packet_summary.get("non_applicable_authority_count", 0) > 0,
        failure_category="missing_non_applicable_boundary",
        source_selector="review_packet_index.non_applicable_authority_boundary",
        expected="non-applicable boundary rows",
        actual=packet_summary.get("non_applicable_authority_count"),
    )


def _review_packet_bootstrap_allowed(validation: dict[str, Any]) -> bool:
    failed_checks = {
        str(check.get("name") or "")
        for check in _dict_list(validation.get("checks"))
        if check.get("passed") is False
    }
    return bool(failed_checks) and failed_checks <= _REVIEW_PACKET_BOOTSTRAP_ALLOWED_CHECKS


def _review_packet_count_bootstrap_allowed(
    *,
    key: str,
    actual_value: Any,
    expected_value: Any,
    validation: dict[str, Any],
) -> bool:
    return (
        key == "review_packet_index_validation_failed_check_count"
        and expected_value == 0
        and isinstance(actual_value, int)
        and actual_value >= 0
        and _review_packet_bootstrap_allowed(validation)
    )


def _validate_non_applicable_boundary(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    non_applicable = _dict_list(context.payload("non_applicable_authorities").get("authorities"))
    certificates = _dict_list(context.payload("search_coverage_certificates").get("certificates"))
    certificates_by_id = {
        str(certificate.get("coverage_certificate_id")): certificate
        for certificate in certificates
    }
    missing_coverage: list[str] = []
    for authority in non_applicable:
        certificate_ids = _strings(authority.get("search_coverage_certificate_ids"))
        if not certificate_ids or any(cid not in certificates_by_id for cid in certificate_ids):
            missing_coverage.append(str(authority.get("candidate_authority_id")))
    _record_check(
        checks,
        failures,
        name="non_applicable_authorities_have_search_coverage",
        passed=not missing_coverage,
        failure_category="non_applicable_missing_search_coverage",
        source_selector="non_applicable_authorities.authorities",
        expected=[],
        actual=missing_coverage,
    )


def _validate_forest_plan_standards(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    coverage_policy = _dict(context.config.get("forest_plan_standard_coverage_policy"))
    require_all_standards_applied = coverage_policy.get(
        "require_all_applicable_standards_applied",
        True,
    )
    findings_by_component = _forest_findings_by_component(context)
    missing: list[str] = []
    for standard in _applicable_standard_rows(context):
        component_id = str(standard.get("component_id"))
        finding = findings_by_component.get(component_id, {})
        if not finding.get("package_evidence") or not finding.get("plan_source_evidence"):
            missing.append(str(standard.get("component_key") or component_id))
    _record_check(
        checks,
        failures,
        name="applicable_standards_have_package_and_plan_evidence",
        passed=not missing or require_all_standards_applied is False,
        failure_category="applicable_standard_missing_evidence",
        source_selector="forest_plan_applicable_standard_coverage.standards",
        expected=[],
        actual=missing,
    )


def _validate_confirmation_selectors(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    unresolved: list[str] = []
    for confirmation in _dict_list(context.config.get("implementation_confirmations")):
        for selector in _dict_list(confirmation.get("source_selectors")):
            if selector.get("required") is not True:
                continue
            if not _resolve_selector(context, selector):
                unresolved.append(
                    f"{confirmation.get('confirmation_id')}:{selector.get('selector')}"
                )
    _record_check(
        checks,
        failures,
        name="implementation_confirmation_selectors_resolve",
        passed=not unresolved,
        failure_category="implementation_confirmation_selector_unresolved",
        source_selector="config.implementation_confirmations.source_selectors",
        expected=[],
        actual=unresolved,
    )


def _validate_residual_risks(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    invalid = [
        str(rule.get("risk_source_id"))
        for rule in _dict_list(context.config.get("residual_risk_rules"))
        if rule.get("legal_conclusion") is not False
    ]
    _record_check(
        checks,
        failures,
        name="residual_risk_rules_are_not_legal_conclusions",
        passed=not invalid,
        failure_category="residual_risk_legal_conclusion",
        source_selector="config.residual_risk_rules",
        expected=[],
        actual=invalid,
    )
