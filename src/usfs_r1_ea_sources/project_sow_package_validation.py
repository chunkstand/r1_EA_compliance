from __future__ import annotations

from typing import Any

from .project_sow_package_graph import _intake_evidence_graph
from .project_sow_package_graph import _intake_graph_validation_checks
from .project_sow_package_intake_support import _authority_family_ids
from .project_sow_package_intake_support import _covered_resource_area_ids
from .project_sow_package_intake_support import _draft_reviewer_confirmation_errors
from .project_sow_package_intake_support import _expected_resource_area_ids
from .project_sow_package_intake_support import _indicator_keys
from .project_sow_package_intake_support import _intake_schema_shape_errors
from .project_sow_package_intake_support import _observed_report_resource_area_ids
from .project_sow_package_intake_support import _resource_scopes
from .project_sow_package_models import CONTRACT_REQUIRED_SCOPE_FIELDS
from .project_sow_package_common import _check
from .project_sow_package_common import _duplicates
from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _normalize_token
from .project_sow_package_common import _resource_area_ids
from .project_sow_package_common import _searchable_text
from .project_sow_package_common import _strings

def _validate_inputs(
    *,
    intake: dict[str, Any],
    resource_config: dict[str, Any],
    authority_inventory: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    checks = []
    required_fields = [
        "project_id",
        "project_name",
        "forest",
        "districts",
        "project_type",
        "nepa_level",
        "proposed_action_summary",
        "federal_land_actions",
        "proposed_action_elements",
    ]
    missing_fields = [field for field in required_fields if _is_empty(intake.get(field))]
    checks.append(
        _check(
            name="required_intake_fields_present",
            passed=not missing_fields,
            details={"missing_fields": missing_fields},
        )
    )
    checks.append(
        _check(
            name="intake_schema_supported",
            passed=intake.get("schema_version") == "project-sow-intake-v0",
            details={"schema_version": intake.get("schema_version")},
        )
    )
    schema_shape_errors = _intake_schema_shape_errors(intake)
    checks.append(
        _check(
            name="intake_schema_shape_valid",
            passed=not schema_shape_errors,
            details={"errors": schema_shape_errors},
        )
    )
    draft_confirmation_errors = _draft_reviewer_confirmation_errors(intake)
    checks.append(
        _check(
            name="draft_reviewer_confirmation_complete",
            passed=not draft_confirmation_errors,
            details={"errors": draft_confirmation_errors},
        )
    )
    checks.append(
        _check(
            name="land_exchange_intake_has_federal_land_actions",
            passed=(
                _normalize_token(str(intake.get("project_type") or ""))
                != "land_exchange"
                or bool(_list(intake.get("federal_land_actions")))
            ),
            details={
                "federal_land_action_count": len(_list(intake.get("federal_land_actions"))),
                "project_type": intake.get("project_type"),
            },
        )
    )
    scopes = _resource_scopes(resource_config)
    checks.append(
        _check(
            name="resource_scope_config_has_scopes",
            passed=bool(scopes),
            details={"resource_scope_count": len(scopes)},
        )
    )
    duplicate_scope_ids = _duplicates(
        str(scope.get("resource_scope_id") or "") for scope in scopes
    )
    checks.append(
        _check(
            name="resource_scope_ids_unique",
            passed=not duplicate_scope_ids,
            details={"duplicate_scope_ids": duplicate_scope_ids},
        )
    )
    authority_family_ids = _authority_family_ids(authority_inventory)
    unknown_authorities = sorted(
        {
            authority_id
            for scope in scopes
            for authority_id in _strings(scope.get("authority_family_ids"))
            if authority_id not in authority_family_ids
        }
    )
    checks.append(
        _check(
            name="resource_scope_authorities_resolve",
            passed=not unknown_authorities,
            details={"unknown_authority_family_ids": unknown_authorities},
        )
    )
    known_covered_resource_areas = _covered_resource_area_ids(scopes)
    expected_resource_areas = _expected_resource_area_ids(intake)
    observed_resource_areas = _observed_report_resource_area_ids(intake)
    selected_resource_areas = _covered_resource_area_ids(selected_scopes)
    missing_expected_resource_areas = sorted(expected_resource_areas - selected_resource_areas)
    missing_observed_resource_areas = sorted(observed_resource_areas - selected_resource_areas)
    unknown_expected_resource_areas = sorted(
        expected_resource_areas - known_covered_resource_areas
    )
    observed_without_expected_action_trigger = sorted(
        observed_resource_areas - expected_resource_areas
    )
    checks.append(
        _check(
            name="expected_resource_areas_resolve_to_scope_config",
            passed=not unknown_expected_resource_areas,
            details={"resource_area_ids": unknown_expected_resource_areas},
        )
    )
    checks.append(
        _check(
            name="expected_resource_areas_have_sow_scope",
            passed=not missing_expected_resource_areas,
            details={"resource_area_ids": missing_expected_resource_areas},
        )
    )
    checks.append(
        _check(
            name="observed_specialist_reports_match_proposed_action_resource_areas",
            passed=not observed_without_expected_action_trigger,
            details={"resource_area_ids": observed_without_expected_action_trigger},
        )
    )
    checks.append(
        _check(
            name="observed_specialist_reports_have_sow_scope",
            passed=not missing_observed_resource_areas,
            details={"resource_area_ids": missing_observed_resource_areas},
        )
    )
    intake_graph = _intake_evidence_graph(intake, selected_scopes)
    checks.extend(_intake_graph_validation_checks(intake_graph, intake, selected_scopes))
    checks.append(
        _check(
            name="at_least_one_resource_scope_selected",
            passed=bool(selected_scopes),
            details={"selected_scope_count": len(selected_scopes)},
        )
    )
    selected_without_tasks = sorted(
        scope["resource_scope_id"]
        for scope in selected_scopes
        if not scope.get("sow_tasks") or not scope.get("required_deliverables")
    )
    checks.append(
        _check(
            name="selected_resource_scopes_have_sow_content",
            passed=not selected_without_tasks,
            details={"scope_ids": selected_without_tasks},
        )
    )
    missing_contract_fields = _selected_scope_contract_field_errors(selected_scopes)
    checks.append(
        _check(
            name="selected_resource_scopes_have_contract_fields",
            passed=not missing_contract_fields,
            details={"missing_contract_fields": missing_contract_fields},
        )
    )
    return {
        "checks": checks,
        "failure_count": sum(1 for check in checks if not check["passed"]),
        "passed": all(check["passed"] for check in checks),
        "schema_version": "project-sow-package-validation-v0",
    }


def _select_resource_scopes(
    intake: dict[str, Any],
    resource_config: dict[str, Any],
) -> list[dict[str, Any]]:
    searchable_text = _searchable_text(intake)
    indicator_keys = _indicator_keys(intake)
    expected_resource_area_ids = _expected_resource_area_ids(intake)
    project_type = _normalize_token(str(intake.get("project_type") or ""))
    selected = []
    for scope in _resource_scopes(resource_config):
        reasons: list[str] = []
        scope_resource_area_ids = _resource_area_ids(scope.get("covered_resource_area_ids"))
        matched_terms = [
            term
            for term in _strings(scope.get("trigger_terms"))
            if term.lower() in searchable_text
        ]
        matched_resource_areas = sorted(
            expected_resource_area_ids.intersection(scope_resource_area_ids)
        )
        matched_indicators = sorted(
            indicator_keys.intersection(
                _normalize_token(value) for value in _strings(scope.get("trigger_indicator_keys"))
            )
        )
        required_project_types = {
            _normalize_token(value) for value in _strings(scope.get("required_for_project_types"))
        }
        if scope.get("always_required") is True:
            reasons.append("always_required")
        if project_type and project_type in required_project_types:
            reasons.append(f"project_type:{project_type}")
        if matched_terms:
            reasons.append("trigger_terms")
        if matched_indicators:
            reasons.append("resource_indicators")
        if matched_resource_areas:
            reasons.append("proposed_action_resource_area")
        if reasons:
            item = dict(scope)
            item["selection_reasons"] = reasons
            item["matched_terms"] = matched_terms
            item["matched_indicator_keys"] = matched_indicators
            item["matched_resource_area_ids"] = matched_resource_areas
            selected.append(item)
    return selected

def _selected_scope_contract_field_errors(
    selected_scopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = []
    for scope in selected_scopes:
        missing = [
            field
            for field in CONTRACT_REQUIRED_SCOPE_FIELDS
            if _is_empty(scope.get(field))
        ]
        if missing:
            errors.append(
                {
                    "missing_fields": missing,
                    "resource_scope_id": scope.get("resource_scope_id"),
                }
            )
    return errors
