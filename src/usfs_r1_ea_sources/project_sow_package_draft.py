from __future__ import annotations

from pathlib import Path
from typing import Any

from .project_sow_package_common import _list
from .project_sow_package_common import _read_json
from .project_sow_package_common import _slug
from .project_sow_package_common import _source_set_id
from .project_sow_package_common import _strings
from .project_sow_package_common import _write_json
from .project_sow_package_graph import _intake_evidence_graph
from .project_sow_package_intake_support import _covered_resource_area_ids
from .project_sow_package_intake_support import _draft_project_sow_intake
from .project_sow_package_intake_support import _expected_resource_area_ids
from .project_sow_package_intake_support import _observed_specialist_reports
from .project_sow_package_intake_support import _proposed_action_elements
from .project_sow_package_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package_models import DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH
from .project_sow_package_models import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package_models import ProjectSowIntakeDraftResult
from .project_sow_package_models import ProjectSowIntakeValidationResult
from .project_sow_package_validation import _select_resource_scopes
from .project_sow_package_validation import _validate_inputs

def run_project_sow_intake_draft(
    *,
    proposed_action_path: Path,
    output_path: Path,
    project_id: str | None = None,
    project_name: str | None = None,
    forest: str | None = None,
    districts: list[str] | None = None,
    project_type: str = "land_exchange",
    nepa_level: str = "environmental_assessment",
    source_title: str | None = None,
    draft_rules_config_path: Path = DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
) -> ProjectSowIntakeDraftResult:
    proposed_action_path = Path(proposed_action_path)
    output_path = Path(output_path)
    draft_rules_config_path = Path(draft_rules_config_path)
    resource_scope_config_path = Path(resource_scope_config_path)
    authority_inventory_path = Path(authority_inventory_path)

    proposed_action_text = proposed_action_path.read_text(encoding="utf-8")
    draft_rules = _read_json(draft_rules_config_path)
    resource_config = _read_json(resource_scope_config_path)
    authority_inventory = _read_json(authority_inventory_path)
    draft = _draft_project_sow_intake(
        proposed_action_text=proposed_action_text,
        proposed_action_path=proposed_action_path,
        draft_rules=draft_rules,
        project_id=project_id,
        project_name=project_name,
        forest=forest,
        districts=districts,
        project_type=project_type,
        nepa_level=nepa_level,
        source_title=source_title,
    )
    selected_scopes = _select_resource_scopes(draft, resource_config)
    validation = _validate_inputs(
        intake=draft,
        resource_config=resource_config,
        authority_inventory=authority_inventory,
        selected_scopes=selected_scopes,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, draft)
    summary = _intake_draft_summary(
        draft=draft,
        output_path=output_path,
        proposed_action_path=proposed_action_path,
        draft_rules_config_path=draft_rules_config_path,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
        validation=validation,
        selected_scopes=selected_scopes,
    )
    return ProjectSowIntakeDraftResult(output_path=output_path, summary=summary)


def validate_project_sow_intake(
    *,
    intake_path: Path,
    project_id: str | None = None,
    source_set_id: str | None = None,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
) -> ProjectSowIntakeValidationResult:
    intake_path = Path(intake_path)
    resource_scope_config_path = Path(resource_scope_config_path)
    authority_inventory_path = Path(authority_inventory_path)

    intake = _read_json(intake_path)
    resource_config = _read_json(resource_scope_config_path)
    authority_inventory = _read_json(authority_inventory_path)
    selected_project_id = _slug(project_id or str(intake.get("project_id") or "project"))
    selected_source_set_id = source_set_id or _source_set_id(authority_inventory)
    selected_scopes = _select_resource_scopes(intake, resource_config)
    validation = _validate_inputs(
        intake=intake,
        resource_config=resource_config,
        authority_inventory=authority_inventory,
        selected_scopes=selected_scopes,
    )
    return ProjectSowIntakeValidationResult(
        intake_path=intake_path,
        summary=_intake_validation_summary(
            intake=intake,
            intake_path=intake_path,
            project_id=selected_project_id,
            source_set_id=selected_source_set_id,
            resource_scope_config_path=resource_scope_config_path,
            authority_inventory_path=authority_inventory_path,
            validation=validation,
            selected_scopes=selected_scopes,
        ),
    )

def _intake_draft_summary(
    *,
    draft: dict[str, Any],
    output_path: Path,
    proposed_action_path: Path,
    draft_rules_config_path: Path,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
    validation: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    draft_metadata = draft.get("draft_metadata") if isinstance(draft.get("draft_metadata"), dict) else {}
    failed_checks = [check for check in validation["checks"] if not check["passed"]]
    expected_unreviewed_failures = {"draft_reviewer_confirmation_complete"}
    unexpected_failed_checks = [
        check
        for check in failed_checks
        if str(check.get("name")) not in expected_unreviewed_failures
    ]
    return {
        "authority_inventory_path": str(authority_inventory_path),
        "candidate_federal_land_action_types": [
            str(action.get("action_type"))
            for action in _list(draft.get("federal_land_actions"))
            if isinstance(action, dict)
        ],
        "candidate_resource_area_ids": sorted(_expected_resource_area_ids(draft)),
        "draft_rules_config_path": str(draft_rules_config_path),
        "failed_validation_checks": failed_checks,
        "output_path": str(output_path),
        "output_written": True,
        "passed": not unexpected_failed_checks,
        "project_id": draft.get("project_id"),
        "proposed_action_path": str(proposed_action_path),
        "resource_scope_config_path": str(resource_scope_config_path),
        "review_status": draft_metadata.get("review_status"),
        "reviewer_confirmation_required": draft_metadata.get(
            "reviewer_confirmation_required"
        ),
        "schema_version": "project-sow-intake-draft-summary-v0",
        "selected_resource_scope_ids": [
            str(scope.get("resource_scope_id")) for scope in selected_scopes
        ],
        "unexpected_failed_validation_checks": unexpected_failed_checks,
        "unexpected_validation_failure_count": len(unexpected_failed_checks),
        "uncertainty_flags": _strings(draft_metadata.get("uncertainty_flags")),
        "validation_failure_count": validation["failure_count"],
        "validation_ready": validation["passed"],
    }


def _intake_validation_summary(
    *,
    intake: dict[str, Any],
    intake_path: Path,
    project_id: str,
    source_set_id: str,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
    validation: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    graph = _intake_evidence_graph(intake, selected_scopes)
    adjudication_summary = _intake_adjudication_summary(intake)
    return {
        "adjudication_decision_counts": adjudication_summary["decision_counts"],
        "adjudication_item_count": adjudication_summary["item_count"],
        "adjudication_status": adjudication_summary["status"],
        "authority_inventory_path": str(authority_inventory_path),
        "failed_validation_checks": [
            check for check in validation["checks"] if not check["passed"]
        ],
        "federal_land_action_count": len(_list(intake.get("federal_land_actions"))),
        "intake_path": str(intake_path),
        "intake_schema_version": intake.get("schema_version"),
        "intake_evidence_graph_edge_count": graph["edge_count"],
        "intake_evidence_graph_node_count": graph["node_count"],
        "observed_specialist_report_count": len(_observed_specialist_reports(intake)),
        "output_written": False,
        "passed": validation["passed"],
        "project_id": project_id,
        "proposed_action_element_count": len(_proposed_action_elements(intake)),
        "proposed_action_resource_area_count": len(_expected_resource_area_ids(intake)),
        "resource_scope_config_path": str(resource_scope_config_path),
        "resource_scope_count": len(selected_scopes),
        "schema_version": "project-sow-intake-validation-summary-v0",
        "selected_resource_area_ids": sorted(_covered_resource_area_ids(selected_scopes)),
        "selected_resource_scope_ids": [
            str(scope.get("resource_scope_id")) for scope in selected_scopes
        ],
        "source_set_id": source_set_id,
        "validation_check_count": len(validation["checks"]),
        "validation_checks": validation["checks"],
        "validation_failure_count": validation["failure_count"],
        "validation_only": True,
    }

def _intake_adjudication_summary(intake: dict[str, Any]) -> dict[str, Any]:
    adjudication = intake.get("project_sow_adjudication")
    if not isinstance(adjudication, dict):
        return {
            "adjudication_id": None,
            "decision_counts": {},
            "item_count": 0,
            "status": "not_applied",
        }
    return {
        "adjudication_id": adjudication.get("adjudication_id"),
        "decision_counts": adjudication.get("decision_counts") or {},
        "item_count": int(adjudication.get("item_count") or 0),
        "status": adjudication.get("status") or "applied",
    }
