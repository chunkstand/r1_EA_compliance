from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .project_sow_package_adjudication_eval import _project_sow_adjudication_apply_summary
from .project_sow_package_adjudication_eval import _project_sow_adjudication_eval_summary
from .project_sow_package_adjudication_eval import _project_sow_intake_adjudication
from .project_sow_package_assembly import _resource_analysis_matrix
from .project_sow_package_assembly import _scope_record
from .project_sow_package_common import _now
from .project_sow_package_common import _read_json
from .project_sow_package_common import _sha256_file
from .project_sow_package_common import _slug
from .project_sow_package_common import _source_set_id
from .project_sow_package_common import _strings
from .project_sow_package_common import _write_json
from .project_sow_package_intake_support import _list
from .project_sow_package_intake_support import _proposed_action_elements
from .project_sow_package_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package_models import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_DECISIONS
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION
from .project_sow_package_models import ProjectSowAdjudicationApplyResult
from .project_sow_package_models import ProjectSowAdjudicationEvalResult
from .project_sow_package_models import ProjectSowAdjudicationTemplateResult
from .project_sow_package_validation import _select_resource_scopes
from .project_sow_package_validation import _validate_inputs

def write_project_sow_adjudication_template(
    *,
    intake_path: Path,
    output_dir: Path = Path("source_library"),
    project_id: str | None = None,
    source_set_id: str | None = None,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    results_dir: Path | None = None,
) -> ProjectSowAdjudicationTemplateResult:
    context = _project_sow_adjudication_context(
        intake_path=intake_path,
        project_id=project_id,
        source_set_id=source_set_id,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
    )
    package_dir = (
        Path(results_dir)
        if results_dir is not None
        else Path(output_dir)
        / "projects"
        / context["project_id"]
        / "requirements_package"
    )
    output_path = package_dir / "project_sow_adjudication_template.json"
    worklist_path = package_dir / "project_sow_adjudication_worklist.md"
    template = _project_sow_adjudication_template(context=context)
    worklist = _render_project_sow_adjudication_worklist(template)
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, template)
    worklist_path.write_text(worklist, encoding="utf-8")
    summary = _project_sow_adjudication_template_summary(
        context=context,
        output_path=output_path,
        worklist_path=worklist_path,
        template=template,
    )
    return ProjectSowAdjudicationTemplateResult(
        output_path=output_path,
        worklist_path=worklist_path,
        summary=summary,
    )


def run_project_sow_adjudication_eval(
    *,
    intake_path: Path,
    adjudication_path: Path,
    output_path: Path | None = None,
    project_id: str | None = None,
    source_set_id: str | None = None,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
) -> ProjectSowAdjudicationEvalResult:
    context = _project_sow_adjudication_context(
        intake_path=intake_path,
        project_id=project_id,
        source_set_id=source_set_id,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
    )
    adjudication_path = Path(adjudication_path)
    output_path = (
        Path(output_path)
        if output_path is not None
        else adjudication_path.with_name("project_sow_adjudication_eval.json")
    )
    adjudication = _read_json(adjudication_path)
    summary = _project_sow_adjudication_eval_summary(
        context=context,
        adjudication=adjudication,
        adjudication_path=adjudication_path,
        output_path=output_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, summary)
    return ProjectSowAdjudicationEvalResult(output_path=output_path, summary=summary)


def run_project_sow_adjudication_apply(
    *,
    intake_path: Path,
    adjudication_path: Path,
    output_intake_path: Path | None = None,
    output_path: Path | None = None,
    eval_output_path: Path | None = None,
    project_id: str | None = None,
    source_set_id: str | None = None,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
) -> ProjectSowAdjudicationApplyResult:
    intake_path = Path(intake_path)
    adjudication_path = Path(adjudication_path)
    output_path = (
        Path(output_path)
        if output_path is not None
        else adjudication_path.with_name("project_sow_adjudication_apply.json")
    )
    output_intake_path = (
        Path(output_intake_path)
        if output_intake_path is not None
        else adjudication_path.with_name("project_sow_adjudicated_intake.json")
    )
    eval_output_path = (
        Path(eval_output_path)
        if eval_output_path is not None
        else adjudication_path.with_name("project_sow_adjudication_eval.json")
    )
    eval_result = run_project_sow_adjudication_eval(
        intake_path=intake_path,
        adjudication_path=adjudication_path,
        output_path=eval_output_path,
        project_id=project_id,
        source_set_id=source_set_id,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
    )
    intake = _read_json(intake_path)
    summary = _project_sow_adjudication_apply_summary(
        eval_summary=eval_result.summary,
        adjudication_path=adjudication_path,
        eval_output_path=eval_result.output_path,
        intake_path=intake_path,
        output_intake_path=output_intake_path,
        output_path=output_path,
    )
    if eval_result.summary["passed"]:
        applied_intake = dict(intake)
        applied_intake["project_sow_adjudication"] = _project_sow_intake_adjudication(
            eval_summary=eval_result.summary,
            adjudication_path=adjudication_path,
            eval_output_path=eval_result.output_path,
        )
        output_intake_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(output_intake_path, applied_intake)
        summary["output_written"] = True
        summary["output_intake_sha256"] = _sha256_file(output_intake_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, summary)
    return ProjectSowAdjudicationApplyResult(
        output_path=output_path,
        output_intake_path=output_intake_path,
        summary=summary,
    )

def _project_sow_adjudication_context(
    *,
    intake_path: Path,
    project_id: str | None,
    source_set_id: str | None,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
) -> dict[str, Any]:
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
    scope_records = [_scope_record(scope) for scope in selected_scopes]
    resource_analysis_matrix = _resource_analysis_matrix(intake, scope_records)
    queue_items = _project_sow_adjudication_queue(
        intake=intake,
        validation=validation,
        resource_analysis_matrix=resource_analysis_matrix,
        scope_records=scope_records,
    )
    return {
        "authority_inventory_path": authority_inventory_path,
        "input_hashes": _project_sow_adjudication_input_hashes(
            intake_path=intake_path,
            resource_scope_config_path=resource_scope_config_path,
            authority_inventory_path=authority_inventory_path,
        ),
        "intake": intake,
        "intake_path": intake_path,
        "project_id": selected_project_id,
        "queue_items": queue_items,
        "resource_analysis_matrix": resource_analysis_matrix,
        "resource_scope_config_path": resource_scope_config_path,
        "scope_records": scope_records,
        "selected_scopes": selected_scopes,
        "source_set_id": selected_source_set_id,
        "validation": validation,
    }


def _project_sow_adjudication_input_hashes(
    *,
    intake_path: Path,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
) -> dict[str, str]:
    return {
        "authority_inventory_sha256": _sha256_file(authority_inventory_path),
        "intake_sha256": _sha256_file(intake_path),
        "resource_scope_config_sha256": _sha256_file(resource_scope_config_path),
    }


def _project_sow_adjudication_queue(
    *,
    intake: dict[str, Any],
    validation: dict[str, Any],
    resource_analysis_matrix: list[dict[str, Any]],
    scope_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    element_by_id = {
        str(element.get("action_element_id") or ""): element
        for element in _proposed_action_elements(intake)
    }
    for area_id in _project_sow_failed_resource_area_ids(
        validation, "expected_resource_areas_resolve_to_scope_config"
    ):
        _add_project_sow_adjudication_item(
            items,
            item_type="unknown_resource_area_id",
            issue_summary=(
                "Resource area ID is present in the intake but is not configured in "
                "project_sow_resource_scopes_v1.json."
            ),
            resource_area_id=area_id,
            current_status="unknown_resource_area_id",
            source_check="expected_resource_areas_resolve_to_scope_config",
        )
    for action_element_id in _project_sow_failed_action_element_ids(
        validation, "intake_evidence_graph_action_elements_have_evidence_refs"
    ):
        element = element_by_id.get(action_element_id, {})
        _add_project_sow_adjudication_item(
            items,
            item_type="missing_evidence_ref",
            issue_summary="Action element triggers a resource area but has no evidence refs.",
            action_element_id=action_element_id,
            current_status="missing_evidence_ref",
            source_check="intake_evidence_graph_action_elements_have_evidence_refs",
            details={"description": element.get("description")},
        )
    for row in resource_analysis_matrix:
        status = str(row.get("coverage_status") or "")
        if status in {"missing_sow_scope", "observed_not_derived_from_proposed_action"}:
            _add_project_sow_adjudication_item(
                items,
                item_type="unresolved_resource_area",
                issue_summary="Resource analysis row is unresolved before package use.",
                resource_area_id=str(row.get("resource_area_id") or ""),
                current_status=status,
                selected_resource_scope_ids=_strings(row.get("selected_resource_scope_ids")),
                details={"resource_area_name": row.get("resource_area_name")},
            )
        if status == "sow_required_no_observed_report_in_calibration":
            _add_project_sow_adjudication_item(
                items,
                item_type="calibration_gap",
                issue_summary=(
                    "SOW scope is required from the proposed action, but the calibration "
                    "package has no observed specialist/supporting report for this area."
                ),
                resource_area_id=str(row.get("resource_area_id") or ""),
                current_status=status,
                selected_resource_scope_ids=_strings(row.get("selected_resource_scope_ids")),
                details={"resource_area_name": row.get("resource_area_name")},
            )
    for scope in scope_records:
        scope_id = str(scope.get("resource_scope_id") or "")
        for deliverable in _strings(scope.get("optional_deliverables")):
            _add_project_sow_adjudication_item(
                items,
                item_type="optional_deliverable_decision",
                issue_summary="Reviewer must decide whether to carry the optional deliverable.",
                resource_scope_id=scope_id,
                optional_deliverable=deliverable,
                current_status="optional_deliverable_available",
                details={"resource_name": scope.get("resource_name")},
            )
    return [items[item_id] for item_id in sorted(items)]


def _add_project_sow_adjudication_item(
    items: dict[str, dict[str, Any]],
    *,
    item_type: str,
    issue_summary: str,
    current_status: str,
    resource_area_id: str | None = None,
    action_element_id: str | None = None,
    resource_scope_id: str | None = None,
    optional_deliverable: str | None = None,
    selected_resource_scope_ids: list[str] | None = None,
    source_check: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    item_id = _project_sow_adjudication_item_id(
        item_type=item_type,
        resource_area_id=resource_area_id,
        action_element_id=action_element_id,
        resource_scope_id=resource_scope_id,
        optional_deliverable=optional_deliverable,
    )
    items[item_id] = {
        "action_element_id": action_element_id,
        "adjudicated_at": "",
        "adjudicated_by": [],
        "allowed_decisions": list(PROJECT_SOW_ADJUDICATION_DECISIONS),
        "current_status": current_status,
        "decision": "pending",
        "decision_source": "",
        "details": details or {},
        "evidence_refs": [],
        "issue_summary": issue_summary,
        "item_id": item_id,
        "item_type": item_type,
        "optional_deliverable": optional_deliverable,
        "rationale": "",
        "resource_area_id": resource_area_id,
        "resource_scope_id": resource_scope_id,
        "selected_resource_scope_ids": selected_resource_scope_ids or [],
        "source_check": source_check,
    }


def _project_sow_adjudication_item_id(
    *,
    item_type: str,
    resource_area_id: str | None = None,
    action_element_id: str | None = None,
    resource_scope_id: str | None = None,
    optional_deliverable: str | None = None,
) -> str:
    parts = [
        item_type,
        resource_area_id,
        action_element_id,
        resource_scope_id,
        optional_deliverable,
    ]
    tokens = [_slug(str(part)) for part in parts if part]
    return ":".join(tokens)


def _project_sow_failed_resource_area_ids(validation: dict[str, Any], check_name: str) -> list[str]:
    check = _validation_check(validation, check_name)
    return _strings(check.get("details", {}).get("resource_area_ids"))


def _project_sow_failed_action_element_ids(validation: dict[str, Any], check_name: str) -> list[str]:
    check = _validation_check(validation, check_name)
    return _strings(check.get("details", {}).get("action_element_ids"))


def _validation_check(validation: dict[str, Any], check_name: str) -> dict[str, Any]:
    for check in _list(validation.get("checks")):
        if isinstance(check, dict) and check.get("name") == check_name:
            return check
    return {}


def _project_sow_adjudication_template(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "adjudication_id": f"project-sow-adjudication-{context['project_id']}",
        "artifact_boundaries": [
            "Reviewer adjudication resolves project-SOW planning work only.",
            "It does not create authority applicability decisions, compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions.",
            "Apply writes an adjudicated intake copy; generated package outputs must be regenerated rather than edited by hand.",
        ],
        "created_at": _now(),
        "input_hashes": context["input_hashes"],
        "input_paths": {
            "authority_inventory": str(context["authority_inventory_path"]),
            "intake": str(context["intake_path"]),
            "resource_scope_config": str(context["resource_scope_config_path"]),
        },
        "items": context["queue_items"],
        "project_id": context["project_id"],
        "reviewer_metadata": {
            "review_status": "pending",
            "reviewed_at": "",
            "reviewed_by": [],
            "review_source": "",
        },
        "schema_version": PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION,
        "source_set_id": context["source_set_id"],
    }


def _render_project_sow_adjudication_worklist(template: dict[str, Any]) -> str:
    items = [item for item in _list(template.get("items")) if isinstance(item, dict)]
    lines = [
        "# Project SOW Adjudication Worklist",
        "",
        f"- Adjudication ID: `{template.get('adjudication_id')}`",
        f"- Project ID: `{template.get('project_id')}`",
        f"- Source set: `{template.get('source_set_id')}`",
        f"- Queue items: `{len(items)}`",
        "",
        "Allowed decisions: `accepted`, `rejected`, `needs_information`, `out_of_scope`.",
        "",
        "This worklist is planning support only. It does not create applicability decisions, compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions.",
        "",
    ]
    counts = Counter(str(item.get("item_type") or "") for item in items)
    lines.extend(["## Queue Summary", ""])
    for item_type, count in sorted(counts.items()):
        lines.append(f"- `{item_type}`: `{count}`")
    for item in items:
        lines.extend(
            [
                "",
                f"## `{item.get('item_id')}`",
                "",
                f"- Type: `{item.get('item_type')}`",
                f"- Current status: `{item.get('current_status')}`",
                f"- Issue: {item.get('issue_summary')}",
            ]
        )
        if item.get("resource_area_id"):
            lines.append(f"- Resource area: `{item.get('resource_area_id')}`")
        if item.get("action_element_id"):
            lines.append(f"- Action element: `{item.get('action_element_id')}`")
        if item.get("resource_scope_id"):
            lines.append(f"- Resource scope: `{item.get('resource_scope_id')}`")
        if item.get("optional_deliverable"):
            lines.append(f"- Optional deliverable: {item.get('optional_deliverable')}")
        if _strings(item.get("selected_resource_scope_ids")):
            lines.append(
                "- Selected scopes: "
                + ", ".join(f"`{scope_id}`" for scope_id in item["selected_resource_scope_ids"])
            )
        lines.extend(
            [
                "- Required reviewer fields: `decision`, `rationale`, `adjudicated_by`, `adjudicated_at`, `decision_source`",
            ]
        )
    return "\n".join(lines) + "\n"


def _project_sow_adjudication_template_summary(
    *,
    context: dict[str, Any],
    output_path: Path,
    worklist_path: Path,
    template: dict[str, Any],
) -> dict[str, Any]:
    items = [item for item in _list(template.get("items")) if isinstance(item, dict)]
    return {
        "item_count": len(items),
        "item_type_counts": dict(
            sorted(Counter(str(item.get("item_type") or "") for item in items).items())
        ),
        "output_path": str(output_path),
        "output_written": True,
        "passed": True,
        "project_id": context["project_id"],
        "schema_version": "project-sow-adjudication-template-summary-v0",
        "source_set_id": context["source_set_id"],
        "worklist_path": str(worklist_path),
    }
