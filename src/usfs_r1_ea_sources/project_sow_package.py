from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re


PACKAGE_SCHEMA_VERSION = "project-sow-package-v0"
MANIFEST_SCHEMA_VERSION = "project-sow-package-manifest-v0"
GENERATOR_VERSION = "project-sow-package-generator-v0"
DEFAULT_RESOURCE_SCOPE_CONFIG_PATH = Path("config/project_sow_resource_scopes_v1.json")
DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH = Path("config/project_sow_intake_draft_rules_v1.json")
DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH = Path("config/project_sow_eval_proving_intakes_v1.json")
DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR = Path("source_library/project_sow_eval")
PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION = "project-sow-adjudication-v0"
PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION = "project-sow-adjudication-eval-v0"
PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION = "project-sow-adjudication-apply-v0"
PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION = "project-sow-intake-adjudication-v0"
PROJECT_SOW_ADJUDICATION_DECISIONS = (
    "accepted",
    "rejected",
    "needs_information",
    "out_of_scope",
)
PROJECT_SOW_ADJUDICATION_ITEM_TYPES = (
    "calibration_gap",
    "missing_evidence_ref",
    "optional_deliverable_decision",
    "unknown_resource_area_id",
    "unresolved_resource_area",
)
CONTRACT_REQUIRED_SCOPE_FIELDS = [
    "acceptance_criteria",
    "assumptions",
    "dependencies",
    "optional_deliverables",
    "review_timing",
    "reviewer_role",
    "reviewer_signoff_fields",
]


@dataclass(frozen=True)
class ProjectSowPackageResult:
    output_dir: Path
    package_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowIntakeValidationResult:
    intake_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowIntakeDraftResult:
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowEvalResult:
    output_dir: Path
    summary_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowAdjudicationTemplateResult:
    output_path: Path
    worklist_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowAdjudicationEvalResult:
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowAdjudicationApplyResult:
    output_path: Path
    output_intake_path: Path
    summary: dict[str, Any]


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


def run_project_sow_package(
    *,
    intake_path: Path,
    output_dir: Path = Path("source_library"),
    project_id: str | None = None,
    source_set_id: str | None = None,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    results_dir: Path | None = None,
) -> ProjectSowPackageResult:
    output_dir = Path(output_dir)
    intake_path = Path(intake_path)
    resource_scope_config_path = Path(resource_scope_config_path)
    authority_inventory_path = Path(authority_inventory_path)

    intake = _read_json(intake_path)
    resource_config = _read_json(resource_scope_config_path)
    authority_inventory = _read_json(authority_inventory_path)
    selected_project_id = _slug(project_id or str(intake.get("project_id") or "project"))
    selected_source_set_id = source_set_id or _source_set_id(authority_inventory)
    package_dir = (
        Path(results_dir)
        if results_dir is not None
        else output_dir / "projects" / selected_project_id / "requirements_package"
    )
    package_path = package_dir / "project_sow_package.json"
    markdown_path = package_dir / "project_sow_package.md"
    pdf_path = package_dir / "project_sow_package.pdf"
    manifest_path = package_dir / "project_sow_package_manifest.json"

    selected_scopes = _select_resource_scopes(intake, resource_config)
    validation = _validate_inputs(
        intake=intake,
        resource_config=resource_config,
        authority_inventory=authority_inventory,
        selected_scopes=selected_scopes,
    )
    summary = _summary(
        intake=intake,
        project_id=selected_project_id,
        source_set_id=selected_source_set_id,
        package_dir=package_dir,
        package_path=package_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        validation=validation,
        selected_scopes=selected_scopes,
    )
    if not validation["passed"]:
        return ProjectSowPackageResult(
            output_dir=package_dir,
            package_path=package_path,
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
            summary=summary,
        )

    package = _build_package(
        intake=intake,
        project_id=selected_project_id,
        source_set_id=selected_source_set_id,
        resource_config=resource_config,
        selected_scopes=selected_scopes,
        validation=validation,
        intake_path=intake_path,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
    )
    markdown = _render_markdown(package)
    pdf_lines = _render_pdf_lines(package)
    rendering_checks = _rendering_validation_checks(markdown=markdown, pdf_lines=pdf_lines)
    package["validation"]["checks"].extend(rendering_checks)
    package["validation"]["failure_count"] = sum(
        1 for check in package["validation"]["checks"] if not check["passed"]
    )
    package["validation"]["passed"] = all(
        check["passed"] for check in package["validation"]["checks"]
    )
    summary = _summary(
        intake=intake,
        project_id=selected_project_id,
        source_set_id=selected_source_set_id,
        package_dir=package_dir,
        package_path=package_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        validation=package["validation"],
        selected_scopes=selected_scopes,
    )
    if not package["validation"]["passed"]:
        return ProjectSowPackageResult(
            output_dir=package_dir,
            package_path=package_path,
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
            summary=summary,
        )
    markdown = _render_markdown(package)
    pdf_lines = _render_pdf_lines(package)
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(package_path, package)
    markdown_path.write_text(markdown, encoding="utf-8")
    _write_simple_pdf(
        pdf_path,
        _paginate_pdf_lines(pdf_lines, max_lines=42),
        title="Project SOW Requirements Package",
    )
    _write_json(manifest_path, package["manifest"])
    summary["output_written"] = True
    summary["output_hashes"] = {
        "project_sow_package_sha256": _sha256_file(package_path),
        "project_sow_package_markdown_sha256": _sha256_file(markdown_path),
        "project_sow_package_pdf_sha256": _sha256_file(pdf_path),
        "project_sow_package_manifest_sha256": _sha256_file(manifest_path),
    }
    summary["pdf_header_valid"] = pdf_path.read_bytes().startswith(b"%PDF-")
    return ProjectSowPackageResult(
        output_dir=package_dir,
        package_path=package_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        summary=summary,
    )


def run_project_sow_eval(
    *,
    eval_config_path: Path = DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH,
    output_dir: Path = DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
) -> ProjectSowEvalResult:
    eval_config_path = Path(eval_config_path)
    output_dir = Path(output_dir)
    resource_scope_config_path = Path(resource_scope_config_path)
    authority_inventory_path = Path(authority_inventory_path)
    eval_config = _read_json(eval_config_path)
    cases = [case for case in _list(eval_config.get("eval_cases")) if isinstance(case, dict)]
    case_summaries = [
        _project_sow_eval_case_summary(
            case=case,
            output_dir=output_dir,
            resource_scope_config_path=resource_scope_config_path,
            authority_inventory_path=authority_inventory_path,
        )
        for case in cases
    ]
    top_level_checks = [
        _check(
            name="project_sow_eval_has_three_proving_intakes",
            passed=len(case_summaries) >= 3,
            details={"case_count": len(case_summaries)},
        )
    ]
    category_totals = {
        key: sum(len(_strings(case["diagnostics"].get(key))) for case in case_summaries)
        for key in [
            "system_miss_resource_area_ids",
            "intake_omission_resource_area_ids",
            "calibration_gap_resource_area_ids",
            "expected_no_observed_report_resource_area_ids",
        ]
    }
    failed_cases = [
        str(case_summary["case_id"])
        for case_summary in case_summaries
        if not case_summary["passed"]
    ]
    summary_path = output_dir / "project_sow_eval_summary.json"
    summary = {
        "authority_inventory_path": str(authority_inventory_path),
        "case_count": len(case_summaries),
        "cases": case_summaries,
        "category_totals": category_totals,
        "eval_config_path": str(eval_config_path),
        "failed_cases": failed_cases,
        "output_dir": str(output_dir),
        "passed": not failed_cases and all(check["passed"] for check in top_level_checks),
        "resource_scope_config_path": str(resource_scope_config_path),
        "schema_version": "project-sow-eval-summary-v0",
        "summary_path": str(summary_path),
        "validation_checks": top_level_checks,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(summary_path, summary)
    return ProjectSowEvalResult(
        output_dir=output_dir,
        summary_path=summary_path,
        summary=summary,
    )


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


def _build_package(
    *,
    intake: dict[str, Any],
    project_id: str,
    source_set_id: str,
    resource_config: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
    validation: dict[str, Any],
    intake_path: Path,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
) -> dict[str, Any]:
    created_at = _now()
    scope_records = [_scope_record(scope) for scope in selected_scopes]
    authority_matrix = _authority_matrix(scope_records)
    resource_analysis_matrix = _resource_analysis_matrix(intake, scope_records)
    observed_specialist_reports = _observed_specialist_reports(intake)
    intake_evidence_graph = _intake_evidence_graph(intake, selected_scopes)
    manifest = {
        "artifact_paths": {
            "authority_inventory": str(authority_inventory_path),
            "intake": str(intake_path),
            "resource_scope_config": str(resource_scope_config_path),
        },
        "created_at": created_at,
        "generator_version": GENERATOR_VERSION,
        "input_hashes": {
            "authority_inventory_sha256": _sha256_file(authority_inventory_path),
            "intake_sha256": _sha256_file(intake_path),
            "resource_scope_config_sha256": _sha256_file(resource_scope_config_path),
        },
        "project_id": project_id,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "validation_status": "passed" if validation["passed"] else "failed",
    }
    return {
        "authority_requirement_matrix": authority_matrix,
        "created_at": created_at,
        "generator_version": GENERATOR_VERSION,
        "intake_summary": _intake_summary(intake),
        "intake_evidence_graph": intake_evidence_graph,
        "manifest": manifest,
        "missing_resource_area_requests": _missing_resource_area_requests(
            resource_analysis_matrix
        ),
        "observed_specialist_reports": observed_specialist_reports,
        "project_id": project_id,
        "project_name": intake.get("project_name"),
        "reviewer_summary": _reviewer_summary(
            intake=intake,
            project_id=project_id,
            source_set_id=source_set_id,
            scope_records=scope_records,
            resource_analysis_matrix=resource_analysis_matrix,
            observed_specialist_reports=observed_specialist_reports,
            intake_evidence_graph=intake_evidence_graph,
        ),
        "resource_analysis_matrix": resource_analysis_matrix,
        "resource_analysis_matrix_count": len(resource_analysis_matrix),
        "resource_scope_count": len(scope_records),
        "resource_scope_records": scope_records,
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "scope_set_id": resource_config.get("scope_set_id"),
        "source_set_id": source_set_id,
        "validation": validation,
    }


def _scope_record(scope: dict[str, Any]) -> dict[str, Any]:
    return {
        "acceptance_criteria": _strings(scope.get("acceptance_criteria")),
        "assumptions": _strings(scope.get("assumptions")),
        "authority_family_ids": _strings(scope.get("authority_family_ids")),
        "covered_resource_area_ids": sorted(
            _resource_area_ids(scope.get("covered_resource_area_ids"))
        ),
        "data_needs": _strings(scope.get("data_needs")),
        "defensibility_checks": _strings(scope.get("defensibility_checks")),
        "dependencies": _strings(scope.get("dependencies")),
        "discipline": scope.get("discipline"),
        "matched_indicator_keys": _strings(scope.get("matched_indicator_keys")),
        "matched_resource_area_ids": sorted(
            _resource_area_ids(scope.get("matched_resource_area_ids"))
        ),
        "matched_terms": _strings(scope.get("matched_terms")),
        "optional_deliverables": _strings(scope.get("optional_deliverables")),
        "required_deliverables": _strings(scope.get("required_deliverables")),
        "review_timing": scope.get("review_timing"),
        "reviewer_role": scope.get("reviewer_role"),
        "reviewer_signoff_fields": _strings(scope.get("reviewer_signoff_fields")),
        "resource_name": scope.get("resource_name"),
        "resource_scope_id": scope.get("resource_scope_id"),
        "selection_reasons": _strings(scope.get("selection_reasons")),
        "sow_tasks": _strings(scope.get("sow_tasks")),
        "status": "required",
    }


def _authority_matrix(scope_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, set[str]] = {}
    for scope in scope_records:
        for authority_id in scope["authority_family_ids"]:
            rows.setdefault(authority_id, set()).add(str(scope["resource_scope_id"]))
    return [
        {
            "authority_family_id": authority_id,
            "resource_scope_ids": sorted(scope_ids),
            "status": "planning_requirement",
        }
        for authority_id, scope_ids in sorted(rows.items())
    ]


def _resource_analysis_matrix(
    intake: dict[str, Any],
    scope_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_area_ids = _expected_resource_area_ids(intake)
    observed_reports = _observed_specialist_reports(intake)
    catalog = _resource_area_catalog(intake)
    scope_ids_by_area: dict[str, list[str]] = {}
    for scope in scope_records:
        for area_id in scope["covered_resource_area_ids"]:
            scope_ids_by_area.setdefault(area_id, []).append(str(scope["resource_scope_id"]))
    reports_by_area: dict[str, list[dict[str, Any]]] = {}
    for report in observed_reports:
        for area_id in _resource_area_ids(report.get("resource_area_ids")):
            reports_by_area.setdefault(area_id, []).append(
                {
                    "document_role": report.get("document_role"),
                    "report_id": report.get("report_id"),
                    "source_record_id": report.get("source_record_id"),
                    "title": report.get("title"),
                }
            )
    action_elements_by_area: dict[str, list[dict[str, str]]] = {}
    for element in _proposed_action_elements(intake):
        for area_id in _resource_area_ids(element.get("resource_area_ids")):
            action_elements_by_area.setdefault(area_id, []).append(
                {
                    "action_element_id": str(element.get("action_element_id") or ""),
                    "description": str(element.get("description") or ""),
                }
            )
    resource_area_ids = sorted(
        set(expected_area_ids) | set(reports_by_area) | set(scope_ids_by_area)
    )
    records = []
    for area_id in resource_area_ids:
        scope_ids = sorted(set(scope_ids_by_area.get(area_id, [])))
        reports = sorted(
            reports_by_area.get(area_id, []),
            key=lambda item: str(item.get("report_id") or item.get("title") or ""),
        )
        expected = area_id in expected_area_ids
        status = "covered"
        if expected and not scope_ids:
            status = "missing_sow_scope"
        elif reports and not expected:
            status = "observed_not_derived_from_proposed_action"
        elif expected and not reports:
            status = "sow_required_no_observed_report_in_calibration"
        area = catalog.get(area_id, {})
        records.append(
            {
                "actual_specialist_reports": reports,
                "coverage_status": status,
                "expected_from_proposed_action": expected,
                "proposed_action_elements": action_elements_by_area.get(area_id, []),
                "proposed_action_basis": _strings(area.get("proposed_action_basis")),
                "resource_area_id": area_id,
                "resource_area_name": area.get("resource_area_name")
                or _title_from_id(area_id),
                "selected_resource_scope_ids": scope_ids,
            }
        )
    return records


def _missing_resource_area_requests(
    resource_analysis_matrix: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    requests = []
    for record in resource_analysis_matrix:
        if record["coverage_status"] == "missing_sow_scope":
            requests.append(
                {
                    "request": "Confirm required specialist product or record location.",
                    "resource_area_id": record["resource_area_id"],
                    "resource_area_name": record["resource_area_name"],
                    "status": record["coverage_status"],
                }
            )
    return requests


def _intake_evidence_graph(
    intake: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    project_id = _slug(str(intake.get("project_id") or "project"))
    project_node_id = f"project:{project_id}"
    proposed_action_node_id = f"proposed_action:{project_id}"
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    _add_node(
        nodes,
        node_id=project_node_id,
        node_type="project",
        label=str(intake.get("project_name") or project_id),
        metadata={
            "forest": intake.get("forest"),
            "project_type": intake.get("project_type"),
        },
    )
    _add_node(
        nodes,
        node_id=proposed_action_node_id,
        node_type="proposed_action",
        label="Proposed action",
        metadata={"summary": intake.get("proposed_action_summary")},
    )
    _add_edge(
        edges,
        edge_type="HAS_PROPOSED_ACTION",
        from_node_id=project_node_id,
        to_node_id=proposed_action_node_id,
    )

    for element in _proposed_action_elements(intake):
        element_node_id = _action_element_node_id(element)
        if not element_node_id:
            continue
        _add_node(
            nodes,
            node_id=element_node_id,
            node_type="action_element",
            label=str(element.get("action_element_id") or element_node_id),
            metadata={"description": element.get("description")},
        )
        _add_edge(
            edges,
            edge_type="HAS_ACTION_ELEMENT",
            from_node_id=proposed_action_node_id,
            to_node_id=element_node_id,
        )
        for evidence_ref in _evidence_refs(element):
            evidence_node_id = _evidence_ref_node_id(evidence_ref)
            if not evidence_node_id:
                continue
            _add_node(
                nodes,
                node_id=evidence_node_id,
                node_type="evidence_ref",
                label=str(evidence_ref.get("title") or evidence_node_id),
                metadata={
                    "citation_label": evidence_ref.get("citation_label"),
                    "locator": evidence_ref.get("locator"),
                    "source_record_id": evidence_ref.get("source_record_id"),
                    "summary": evidence_ref.get("summary"),
                },
            )
            _add_edge(
                edges,
                edge_type="SUPPORTED_BY",
                from_node_id=element_node_id,
                to_node_id=evidence_node_id,
            )
            for area_id in sorted(_resource_area_ids(element.get("resource_area_ids"))):
                resource_node_id = _resource_area_node_id(area_id)
                _add_resource_area_node(nodes, intake, area_id)
                _add_edge(
                    edges,
                    edge_type="TRIGGERS_RESOURCE_AREA",
                    from_node_id=evidence_node_id,
                    to_node_id=resource_node_id,
                )

    for area_id in sorted(_expected_resource_area_ids(intake)):
        _add_resource_area_node(nodes, intake, area_id)

    for scope in selected_scopes:
        scope_node_id = _scope_node_id(scope)
        if not scope_node_id:
            continue
        scope_id = str(scope.get("resource_scope_id") or "")
        _add_node(
            nodes,
            node_id=scope_node_id,
            node_type="sow_scope",
            label=str(scope.get("resource_name") or scope_id),
            metadata={"discipline": scope.get("discipline")},
        )
        for area_id in sorted(_resource_area_ids(scope.get("covered_resource_area_ids"))):
            resource_node_id = _resource_area_node_id(area_id)
            _add_resource_area_node(nodes, intake, area_id)
            _add_edge(
                edges,
                edge_type="COVERED_BY_SOW_SCOPE",
                from_node_id=resource_node_id,
                to_node_id=scope_node_id,
            )
        for deliverable in _strings(scope.get("required_deliverables")):
            deliverable_node_id = _deliverable_node_id(scope, deliverable)
            _add_node(
                nodes,
                node_id=deliverable_node_id,
                node_type="expected_deliverable",
                label=deliverable,
                metadata={"resource_scope_id": scope_id},
            )
            _add_edge(
                edges,
                edge_type="REQUIRES_DELIVERABLE",
                from_node_id=scope_node_id,
                to_node_id=deliverable_node_id,
            )

    for report in _observed_specialist_reports(intake):
        report_node_id = _observed_report_node_id(report)
        if not report_node_id:
            continue
        _add_node(
            nodes,
            node_id=report_node_id,
            node_type="observed_specialist_report",
            label=str(report.get("title") or report_node_id),
            metadata={
                "document_role": report.get("document_role"),
                "evidence_refs": report.get("evidence_refs") or [],
                "source_record_id": report.get("source_record_id"),
            },
        )
        for area_id in _resource_area_ids(report.get("resource_area_ids")):
            resource_node_id = _resource_area_node_id(area_id)
            _add_resource_area_node(nodes, intake, area_id)
            _add_edge(
                edges,
                edge_type="OBSERVED_REPORT_COVERS_RESOURCE_AREA",
                from_node_id=report_node_id,
                to_node_id=resource_node_id,
            )

    return {
        "edge_count": len(edges),
        "edges": sorted(edges, key=lambda edge: edge["edge_id"]),
        "node_count": len(nodes),
        "nodes": sorted(nodes.values(), key=lambda node: node["node_id"]),
        "schema_version": "project-sow-intake-evidence-graph-v0",
    }


def _intake_graph_validation_checks(
    graph: dict[str, Any],
    intake: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    nodes = {node["node_id"]: node for node in _list(graph.get("nodes")) if isinstance(node, dict)}
    edges = [edge for edge in _list(graph.get("edges")) if isinstance(edge, dict)]
    raw_id_diagnostics = _intake_graph_raw_id_diagnostics(intake, selected_scopes)
    node_ids = [str(node_id) for node_id in nodes]
    duplicate_node_ids = sorted(
        set(_duplicates(node_ids))
        | set(raw_id_diagnostics["duplicate_node_ids"])
    )
    edge_ids = [str(edge.get("edge_id") or "") for edge in edges]
    duplicate_edge_ids = sorted(
        set(_duplicates(edge_ids))
        | set(raw_id_diagnostics["duplicate_edge_ids"])
    )
    dangling_edges = sorted(
        edge.get("edge_id")
        for edge in edges
        if edge.get("from_node_id") not in nodes or edge.get("to_node_id") not in nodes
    )
    missing_evidence_action_elements = sorted(
        str(element.get("action_element_id") or "")
        for element in _proposed_action_elements(intake)
        if _resource_area_ids(element.get("resource_area_ids"))
        and not _evidence_ref_node_ids(element)
    )
    evidence_without_resource_area_action_elements = sorted(
        str(element.get("action_element_id") or "")
        for element in _proposed_action_elements(intake)
        if _evidence_ref_node_ids(element)
        and not _resource_area_ids(element.get("resource_area_ids"))
    )
    missing_resource_paths = sorted(
        area_id
        for area_id in _expected_resource_area_ids(intake)
        if not _has_canonical_resource_path(graph, area_id)
    )
    missing_observed_report_paths = sorted(
        f"{report.get('report_id') or report.get('title')}:{area_id}"
        for report in _observed_specialist_reports(intake)
        for area_id in _resource_area_ids(report.get("resource_area_ids"))
        if not _has_canonical_resource_path(graph, area_id)
    )
    return [
        _check(
            name="intake_evidence_graph_node_ids_unique",
            passed=not duplicate_node_ids,
            details={
                "duplicate_input_node_ids": raw_id_diagnostics["duplicate_node_ids"],
                "duplicate_node_ids": duplicate_node_ids,
            },
        ),
        _check(
            name="intake_evidence_graph_edge_ids_unique",
            passed=not duplicate_edge_ids,
            details={
                "duplicate_edge_ids": duplicate_edge_ids,
                "duplicate_input_edge_ids": raw_id_diagnostics["duplicate_edge_ids"],
            },
        ),
        _check(
            name="intake_evidence_graph_edges_resolve",
            passed=not dangling_edges,
            details={"dangling_edge_ids": dangling_edges},
        ),
        _check(
            name="intake_evidence_graph_action_elements_have_evidence_refs",
            passed=not missing_evidence_action_elements,
            details={"action_element_ids": missing_evidence_action_elements},
        ),
        _check(
            name="intake_evidence_graph_action_elements_trigger_resource_areas",
            passed=not evidence_without_resource_area_action_elements,
            details={
                "action_element_ids": evidence_without_resource_area_action_elements,
            },
        ),
        _check(
            name="intake_evidence_graph_resource_area_paths_complete",
            passed=not missing_resource_paths,
            details={"resource_area_ids": missing_resource_paths},
        ),
        _check(
            name="intake_evidence_graph_observed_reports_have_supported_resource_paths",
            passed=not missing_observed_report_paths,
            details={"report_resource_area_ids": missing_observed_report_paths},
        ),
    ]


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


def _intake_graph_raw_id_diagnostics(
    intake: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> dict[str, list[str]]:
    project_id = _slug(str(intake.get("project_id") or "project"))
    proposed_action_node_id = f"proposed_action:{project_id}"
    node_ids: list[str] = [
        f"project:{project_id}",
        proposed_action_node_id,
    ]
    edge_ids: list[str] = [
        _graph_edge_id(
            edge_type="HAS_PROPOSED_ACTION",
            from_node_id=f"project:{project_id}",
            to_node_id=proposed_action_node_id,
        )
    ]

    for element in _proposed_action_elements(intake):
        element_node_id = _action_element_node_id(element)
        if not element_node_id:
            continue
        node_ids.append(element_node_id)
        edge_ids.append(
            _graph_edge_id(
                edge_type="HAS_ACTION_ELEMENT",
                from_node_id=proposed_action_node_id,
                to_node_id=element_node_id,
            )
        )
        for evidence_node_id in _evidence_ref_node_ids(element):
            node_ids.append(evidence_node_id)
            edge_ids.append(
                _graph_edge_id(
                    edge_type="SUPPORTED_BY",
                    from_node_id=element_node_id,
                    to_node_id=evidence_node_id,
                )
            )
            for area_id in sorted(_resource_area_ids(element.get("resource_area_ids"))):
                edge_ids.append(
                    _graph_edge_id(
                        edge_type="TRIGGERS_RESOURCE_AREA",
                        from_node_id=evidence_node_id,
                        to_node_id=_resource_area_node_id(area_id),
                    )
                )

    for area_id in sorted(_resource_area_catalog(intake)):
        node_ids.append(_resource_area_node_id(area_id))

    for scope in selected_scopes:
        scope_node_id = _scope_node_id(scope)
        if not scope_node_id:
            continue
        node_ids.append(scope_node_id)
        for area_id in sorted(_resource_area_ids(scope.get("covered_resource_area_ids"))):
            edge_ids.append(
                _graph_edge_id(
                    edge_type="COVERED_BY_SOW_SCOPE",
                    from_node_id=_resource_area_node_id(area_id),
                    to_node_id=scope_node_id,
                )
            )
        for deliverable in _strings(scope.get("required_deliverables")):
            deliverable_node_id = _deliverable_node_id(scope, deliverable)
            node_ids.append(deliverable_node_id)
            edge_ids.append(
                _graph_edge_id(
                    edge_type="REQUIRES_DELIVERABLE",
                    from_node_id=scope_node_id,
                    to_node_id=deliverable_node_id,
                )
            )

    for report in _observed_specialist_reports(intake):
        report_node_id = _observed_report_node_id(report)
        if not report_node_id:
            continue
        node_ids.append(report_node_id)
        for area_id in _resource_area_ids(report.get("resource_area_ids")):
            edge_ids.append(
                _graph_edge_id(
                    edge_type="OBSERVED_REPORT_COVERS_RESOURCE_AREA",
                    from_node_id=report_node_id,
                    to_node_id=_resource_area_node_id(area_id),
                )
            )
    return {
        "duplicate_edge_ids": _duplicates(edge_ids),
        "duplicate_node_ids": _duplicates(node_ids),
    }


def _add_resource_area_node(
    nodes: dict[str, dict[str, Any]],
    intake: dict[str, Any],
    area_id: str,
) -> None:
    area = _resource_area_catalog(intake).get(area_id, {})
    _add_node(
        nodes,
        node_id=_resource_area_node_id(area_id),
        node_type="resource_area",
        label=str(area.get("resource_area_name") or _title_from_id(area_id)),
        metadata={"proposed_action_basis": _strings(area.get("proposed_action_basis"))},
    )


def _add_node(
    nodes: dict[str, dict[str, Any]],
    *,
    node_id: str,
    node_type: str,
    label: str,
    metadata: dict[str, Any],
) -> None:
    nodes.setdefault(
        node_id,
        {
            "label": label,
            "metadata": metadata,
            "node_id": node_id,
            "node_type": node_type,
        },
    )


def _add_edge(
    edges: list[dict[str, Any]],
    *,
    edge_type: str,
    from_node_id: str,
    to_node_id: str,
) -> None:
    edge_id = _graph_edge_id(
        edge_type=edge_type,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
    )
    edge = {
        "edge_id": edge_id,
        "edge_type": edge_type,
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
    }
    if edge not in edges:
        edges.append(edge)


def _graph_edge_id(*, edge_type: str, from_node_id: str, to_node_id: str) -> str:
    return f"{edge_type}:{from_node_id}->{to_node_id}"


def _has_canonical_resource_path(graph: dict[str, Any], area_id: str) -> bool:
    resource_node_id = _resource_area_node_id(area_id)
    return any(
        edge.get("edge_type") == "TRIGGERS_RESOURCE_AREA"
        and edge.get("to_node_id") == resource_node_id
        and _has_incoming_edge(
            graph,
            from_node_type="action_element",
            edge_type="SUPPORTED_BY",
            to_node_id=str(edge.get("from_node_id")),
        )
        and _has_incoming_edge(
            graph,
            from_node_type="proposed_action",
            edge_type="HAS_ACTION_ELEMENT",
            to_node_id=_incoming_edge_from(graph, str(edge.get("from_node_id"))),
        )
        and _has_outgoing_edge(
            graph,
            from_node_id=resource_node_id,
            edge_type="COVERED_BY_SOW_SCOPE",
            to_node_type="sow_scope",
        )
        for edge in _list(graph.get("edges"))
        if isinstance(edge, dict)
    )


def _incoming_edge_from(graph: dict[str, Any], to_node_id: str) -> str:
    for edge in _list(graph.get("edges")):
        if (
            isinstance(edge, dict)
            and edge.get("edge_type") == "SUPPORTED_BY"
            and edge.get("to_node_id") == to_node_id
        ):
            return str(edge.get("from_node_id") or "")
    return ""


def _has_incoming_edge(
    graph: dict[str, Any],
    *,
    from_node_type: str,
    edge_type: str,
    to_node_id: str,
) -> bool:
    node_types = {
        str(node.get("node_id")): node.get("node_type")
        for node in _list(graph.get("nodes"))
        if isinstance(node, dict)
    }
    return any(
        edge.get("edge_type") == edge_type
        and edge.get("to_node_id") == to_node_id
        and node_types.get(str(edge.get("from_node_id"))) == from_node_type
        for edge in _list(graph.get("edges"))
        if isinstance(edge, dict)
    )


def _has_outgoing_edge(
    graph: dict[str, Any],
    *,
    from_node_id: str,
    edge_type: str,
    to_node_type: str,
) -> bool:
    node_types = {
        str(node.get("node_id")): node.get("node_type")
        for node in _list(graph.get("nodes"))
        if isinstance(node, dict)
    }
    return any(
        edge.get("edge_type") == edge_type
        and edge.get("from_node_id") == from_node_id
        and node_types.get(str(edge.get("to_node_id"))) == to_node_type
        for edge in _list(graph.get("edges"))
        if isinstance(edge, dict)
    )


def _resource_area_node_id(area_id: str) -> str:
    return f"resource_area:{area_id}"


def _action_element_node_id(element: dict[str, Any]) -> str:
    element_id = _normalize_token(str(element.get("action_element_id") or "element"))
    return f"action_element:{element_id}" if element_id else ""


def _evidence_ref_node_ids(record: dict[str, Any]) -> list[str]:
    return [
        node_id
        for node_id in (_evidence_ref_node_id(evidence_ref) for evidence_ref in _evidence_refs(record))
        if node_id
    ]


def _evidence_ref_node_id(evidence_ref: dict[str, Any]) -> str:
    evidence_ref_id = _normalize_token(
        str(evidence_ref.get("evidence_ref_id") or evidence_ref.get("title") or "")
    )
    return f"evidence_ref:{evidence_ref_id}" if evidence_ref_id else ""


def _scope_node_id(scope: dict[str, Any]) -> str:
    scope_id = str(scope.get("resource_scope_id") or "")
    return f"sow_scope:{scope_id}" if scope_id else ""


def _deliverable_node_id(scope: dict[str, Any], deliverable: str) -> str:
    scope_id = str(scope.get("resource_scope_id") or "")
    return f"expected_deliverable:{scope_id}:{_slug(deliverable)}"


def _observed_report_node_id(report: dict[str, Any]) -> str:
    report_id = _normalize_token(str(report.get("report_id") or report.get("title") or ""))
    return f"observed_specialist_report:{report_id}" if report_id else ""


def _intake_summary(intake: dict[str, Any]) -> dict[str, Any]:
    adjudication_summary = _intake_adjudication_summary(intake)
    return {
        "adjudication_decision_counts": adjudication_summary["decision_counts"],
        "adjudication_item_count": adjudication_summary["item_count"],
        "adjudication_status": adjudication_summary["status"],
        "districts": _strings(intake.get("districts")),
        "federal_land_action_count": len(_list(intake.get("federal_land_actions"))),
        "forest": intake.get("forest"),
        "forest_plan_profile": intake.get("forest_plan_profile"),
        "geography": _strings(intake.get("geography")),
        "nepa_level": intake.get("nepa_level"),
        "observed_specialist_report_count": len(_observed_specialist_reports(intake)),
        "project_name": intake.get("project_name"),
        "proposed_action_element_count": len(_proposed_action_elements(intake)),
        "project_type": intake.get("project_type"),
        "proposed_action_resource_area_ids": sorted(
            _expected_resource_area_ids(intake)
        ),
        "resource_indicator_keys": sorted(_indicator_keys(intake)),
    }


def _render_markdown(package: dict[str, Any]) -> str:
    lines = [
        f"# {package['project_name']} Requirements Package",
        "",
        "This generated package scopes specialist work needed to prepare a defensible NEPA EA package. It is planning support, not legal advice or a final compliance determination.",
        "",
        "## Reviewer Snapshot",
        "",
    ]
    reviewer_summary = package["reviewer_summary"]
    snapshot = reviewer_summary["snapshot"]
    lines.extend(
        [
            "| Field | Value |",
            "| --- | --- |",
            f"| Project ID | `{package['project_id']}` |",
            f"| Forest | {snapshot['forest']} |",
            f"| Districts | {', '.join(snapshot['districts'])} |",
            f"| Project type | `{snapshot['project_type']}` |",
            f"| NEPA level | `{snapshot['nepa_level']}` |",
            f"| SOW scopes | `{snapshot['resource_scope_count']}` |",
            f"| Proposed-action resource areas | `{snapshot['proposed_action_resource_area_count']}` |",
            f"| Observed reports in calibration set | `{snapshot['observed_specialist_report_count']}` |",
            f"| Unresolved resource areas | `{len(snapshot['missing_or_uncovered_resource_area_ids'])}` |",
            f"| Calibration gaps | `{len(snapshot['calibration_gap_resource_area_ids'])}` |",
            f"| Adjudication status | `{snapshot['adjudication_status']}` |",
            "| Intake evidence graph | "
            f"`{snapshot['intake_evidence_graph_node_count']}` nodes / "
            f"`{snapshot['intake_evidence_graph_edge_count']}` edges |",
            "",
            "### Review Checklist",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in reviewer_summary["review_checklist"])
    lines.extend(
        [
            "",
            "### Package Boundaries",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in reviewer_summary["package_boundaries"])
    lines.extend(
        [
            "",
            "## Intake",
        ]
    )
    intake = package["intake_summary"]
    lines.extend(
        [
            f"- Project ID: `{package['project_id']}`",
            f"- Source set: `{package['source_set_id']}`",
            f"- Forest: {intake.get('forest')}",
            f"- Districts: {', '.join(intake.get('districts') or [])}",
            f"- Project type: `{intake.get('project_type')}`",
            f"- NEPA level: `{intake.get('nepa_level')}`",
            f"- Federal land action count: `{intake.get('federal_land_action_count')}`",
            f"- Proposed action resource areas: `{len(intake.get('proposed_action_resource_area_ids') or [])}`",
            f"- Observed specialist/supporting reports: `{intake.get('observed_specialist_report_count')}`",
            f"- Adjudication status: `{intake.get('adjudication_status')}`",
            "",
            "## Resource Scopes",
            "",
            "| Scope | Discipline | Covered resource areas | Required deliverables | Optional deliverables |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for scope in package["resource_scope_records"]:
        lines.append(
            f"| {scope['resource_name']} | `{scope['discipline']}` | "
            f"{', '.join(f'`{item}`' for item in scope['covered_resource_area_ids'])} | "
            f"{len(scope['required_deliverables'])} | {len(scope['optional_deliverables'])} |"
        )
    for scope in package["resource_scope_records"]:
        lines.extend(
            [
                "",
                f"### {scope['resource_name']}",
                "",
                f"- Scope ID: `{scope['resource_scope_id']}`",
                f"- Discipline: `{scope['discipline']}`",
                f"- Selection reasons: {', '.join(scope['selection_reasons'])}",
                f"- Covered resource areas: {', '.join(f'`{item}`' for item in scope['covered_resource_area_ids'])}",
                f"- Authority families: {', '.join(f'`{item}`' for item in scope['authority_family_ids'])}",
                "",
                "Tasks:",
            ]
        )
        lines.extend(f"- {task}" for task in scope["sow_tasks"])
        lines.append("")
        lines.append("Required deliverables:")
        lines.extend(f"- {deliverable}" for deliverable in scope["required_deliverables"])
        lines.append("")
        lines.append("Optional deliverables:")
        lines.extend(f"- {deliverable}" for deliverable in scope["optional_deliverables"])
        lines.append("")
        lines.append("Contract terms:")
        lines.extend(
            [
                f"- Reviewer role: {scope['reviewer_role']}",
                f"- Review timing: {scope['review_timing']}",
                "- Assumptions:",
            ]
        )
        lines.extend(f"  - {item}" for item in scope["assumptions"])
        lines.append("- Dependencies:")
        lines.extend(f"  - {item}" for item in scope["dependencies"])
        lines.append("- Acceptance criteria:")
        lines.extend(f"  - {item}" for item in scope["acceptance_criteria"])
        lines.append("- Reviewer signoff fields:")
        lines.extend(f"  - `{item}`" for item in scope["reviewer_signoff_fields"])
        lines.append("")
        lines.append("Defensibility checks:")
        lines.extend(f"- {check}" for check in scope["defensibility_checks"])
    lines.extend(["", "## Authority Requirement Matrix"])
    for row in package["authority_requirement_matrix"]:
        lines.append(
            f"- `{row['authority_family_id']}`: {', '.join(f'`{scope_id}`' for scope_id in row['resource_scope_ids'])}"
        )
    lines.extend(
        [
            "",
            "## Resource Analysis Coverage",
            "",
            "| Resource area | Coverage status | SOW scopes | Observed reports |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in package["resource_analysis_matrix"]:
        report_titles = [
            str(report["title"]) for report in row["actual_specialist_reports"]
        ]
        lines.append(
            f"| `{row['resource_area_id']}` | `{row['coverage_status']}` | "
            f"{', '.join(f'`{scope_id}`' for scope_id in row['selected_resource_scope_ids']) or 'none'} | "
            f"{', '.join(report_titles) or 'none observed'} |"
        )
    graph = package["intake_evidence_graph"]
    lines.extend(
        [
            "",
            "## Intake Evidence Graph",
            f"- Nodes: `{graph['node_count']}`",
            f"- Edges: `{graph['edge_count']}`",
            "- Required path: `proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope`",
        ]
    )
    for row in package["resource_analysis_matrix"]:
        if row["expected_from_proposed_action"]:
            status = (
                "present"
                if _has_canonical_resource_path(graph, row["resource_area_id"])
                else "missing"
            )
            lines.append(f"- `{row['resource_area_id']}` path: `{status}`")
    lines.extend(["", "## Validation"])
    for check in package["validation"]["checks"]:
        status = "passed" if check["passed"] else "failed"
        lines.append(f"- `{check['name']}`: `{status}`")
    return "\n".join(lines) + "\n"


def _reviewer_summary(
    *,
    intake: dict[str, Any],
    project_id: str,
    source_set_id: str,
    scope_records: list[dict[str, Any]],
    resource_analysis_matrix: list[dict[str, Any]],
    observed_specialist_reports: list[dict[str, Any]],
    intake_evidence_graph: dict[str, Any],
) -> dict[str, Any]:
    adjudication_summary = _intake_adjudication_summary(intake)
    unresolved_statuses = {
        "missing_sow_scope",
        "observed_not_derived_from_proposed_action",
    }
    missing_or_uncovered = [
        row["resource_area_id"]
        for row in resource_analysis_matrix
        if row["coverage_status"] in unresolved_statuses
    ]
    calibration_gap_resource_area_ids = [
        row["resource_area_id"]
        for row in resource_analysis_matrix
        if row["coverage_status"] == "sow_required_no_observed_report_in_calibration"
    ]
    return {
        "package_boundaries": [
            "Planning support only; not legal advice or a final agency decision.",
            "JSON is canonical; Markdown and PDF are renderings from the same package JSON.",
            "SOW scope selection is not an applicability decision or compliance finding.",
            "Ignored source_library outputs remain local generated artifacts unless policy changes.",
        ],
        "review_checklist": [
            "Confirm the proposed action and federal land actions are complete.",
            "Assign a responsible specialist for each required resource scope.",
            "Confirm each proposed-action resource area has an evidence-backed graph path.",
            "Resolve any missing resource-area requests before using the package for contracting.",
            "Use observed East Crazies reports only as calibration evidence, not as legal precedent.",
        ],
        "schema_version": "project-sow-reviewer-summary-v0",
        "snapshot": {
            "adjudication_decision_counts": adjudication_summary["decision_counts"],
            "adjudication_item_count": adjudication_summary["item_count"],
            "adjudication_status": adjudication_summary["status"],
            "districts": _strings(intake.get("districts")),
            "forest": intake.get("forest"),
            "intake_evidence_graph_edge_count": int(intake_evidence_graph.get("edge_count") or 0),
            "intake_evidence_graph_node_count": int(intake_evidence_graph.get("node_count") or 0),
            "calibration_gap_resource_area_ids": calibration_gap_resource_area_ids,
            "missing_or_uncovered_resource_area_ids": missing_or_uncovered,
            "nepa_level": intake.get("nepa_level"),
            "observed_specialist_report_count": len(observed_specialist_reports),
            "project_id": project_id,
            "project_name": intake.get("project_name"),
            "project_type": intake.get("project_type"),
            "proposed_action_resource_area_count": len(_expected_resource_area_ids(intake)),
            "resource_scope_count": len(scope_records),
            "source_set_id": source_set_id,
        },
    }


def _render_pdf_lines(package: dict[str, Any]) -> list[str]:
    reviewer_summary = package["reviewer_summary"]
    snapshot = reviewer_summary["snapshot"]
    lines = [
        f"{package['project_name']} Requirements Package",
        "Reviewer Snapshot",
        f"Project ID: {package['project_id']}",
        f"Forest: {snapshot['forest']}",
        f"Districts: {', '.join(snapshot['districts'])}",
        f"Project type: {snapshot['project_type']}",
        f"NEPA level: {snapshot['nepa_level']}",
        f"Resource Scope Count: {snapshot['resource_scope_count']}",
        f"Proposed-action resource areas: {snapshot['proposed_action_resource_area_count']}",
        f"Observed reports in calibration set: {snapshot['observed_specialist_report_count']}",
        f"Unresolved resource areas: {len(snapshot['missing_or_uncovered_resource_area_ids'])}",
        f"Calibration gaps: {len(snapshot['calibration_gap_resource_area_ids'])}",
        f"Adjudication status: {snapshot['adjudication_status']}",
        (
            "Intake evidence graph: "
            f"{snapshot['intake_evidence_graph_node_count']} nodes / "
            f"{snapshot['intake_evidence_graph_edge_count']} edges"
        ),
        "",
        "Package Boundaries",
    ]
    lines.extend(f"- {item}" for item in reviewer_summary["package_boundaries"])
    lines.extend(["", "Review Checklist"])
    lines.extend(f"- {item}" for item in reviewer_summary["review_checklist"])
    lines.extend(["", "Resource Scopes"])
    for scope in package["resource_scope_records"]:
        lines.append(
            f"- {scope['resource_scope_id']}: {scope['resource_name']} "
            f"({len(scope['required_deliverables'])} required, "
            f"{len(scope['optional_deliverables'])} optional deliverables)"
        )
    lines.extend(["", "Contract Terms"])
    for scope in package["resource_scope_records"]:
        lines.append(f"- {scope['resource_scope_id']} reviewer: {scope['reviewer_role']}")
        lines.append(f"  timing: {scope['review_timing']}")
        lines.append(
            f"  acceptance criteria: {len(scope['acceptance_criteria'])}; "
            f"assumptions: {len(scope['assumptions'])}; "
            f"dependencies: {len(scope['dependencies'])}"
        )
        lines.append(
            "  signoff fields: " + ", ".join(scope["reviewer_signoff_fields"])
        )
    lines.extend(["", "Resource Analysis Coverage"])
    for row in package["resource_analysis_matrix"]:
        reports = ", ".join(
            str(report["title"]) for report in row["actual_specialist_reports"]
        )
        lines.append(
            f"- {row['resource_area_id']}: {row['coverage_status']}; "
            f"SOW scopes {', '.join(row['selected_resource_scope_ids']) or 'none'}; "
            f"reports {reports or 'none observed'}"
        )
    lines.extend(
        [
            "",
            "Intake Evidence Graph",
            "Required path: proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope",
            "",
            "Validation",
        ]
    )
    for check in package["validation"]["checks"]:
        status = "passed" if check["passed"] else "failed"
        lines.append(f"- {check['name']}: {status}")
    return [_truncate(line, 150) for line in lines]


def _rendering_validation_checks(markdown: str, pdf_lines: list[str]) -> list[dict[str, Any]]:
    required_markdown_sections = [
        "# ",
        "## Reviewer Snapshot",
        "## Intake",
        "## Resource Scopes",
        "Contract terms:",
        "## Resource Analysis Coverage",
        "## Intake Evidence Graph",
        "## Validation",
    ]
    required_pdf_items = [
        "Reviewer Snapshot",
        "Package Boundaries",
        "Review Checklist",
        "Resource Scopes",
        "Contract Terms",
        "Resource Analysis Coverage",
        "Intake Evidence Graph",
        "Validation",
    ]
    pdf_text = "\n".join(pdf_lines)
    missing_markdown_sections = [
        section for section in required_markdown_sections if section not in markdown
    ]
    missing_pdf_items = [item for item in required_pdf_items if item not in pdf_text]
    return [
        _check(
            name="project_sow_markdown_required_sections_present",
            passed=not missing_markdown_sections,
            details={"missing_sections": missing_markdown_sections},
        ),
        _check(
            name="project_sow_pdf_required_items_present",
            passed=not missing_pdf_items,
            details={"missing_items": missing_pdf_items},
        ),
    ]


def _paginate_pdf_lines(lines: list[str], *, max_lines: int) -> list[list[str]]:
    pages: list[list[str]] = []
    page: list[str] = []
    for line in lines:
        if len(page) >= max_lines:
            pages.append(page)
            page = []
        page.append(line)
    if page:
        pages.append(page)
    return pages or [["Project SOW Requirements Package"]]


def _write_simple_pdf(path: Path, pages: list[list[str]], *, title: str) -> None:
    width = 1008
    height = 612
    margin_x = 34
    start_y = 568
    leading = 12
    font_size = 8
    objects: list[bytes | None] = [None, None, None]

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    for page_number, page_lines in enumerate(pages, start=1):
        content = _pdf_page_content(
            page_lines,
            page_number=page_number,
            page_count=len(pages),
            title=title,
            margin_x=margin_x,
            start_y=start_y,
            leading=leading,
            font_size=font_size,
        )
        content_id = add_object(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects[1] = (objects[1] or b"") + f"{page_id} 0 R ".encode("ascii")

    kids = objects[1] or b""
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        b"<< /Type /Pages /Kids ["
        + kids
        + b"] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>"
    )
    objects[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    _write_pdf_objects(path, [obj for obj in objects if obj is not None])


def _pdf_page_content(
    lines: list[str],
    *,
    page_number: int,
    page_count: int,
    title: str,
    margin_x: int,
    start_y: int,
    leading: int,
    font_size: int,
) -> bytes:
    commands = [f"BT /F1 {font_size} Tf {leading} TL {margin_x} {start_y} Td"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj T*")
    footer_y = 24 - (start_y - len(lines) * leading)
    commands.append(
        f"0 {footer_y} Td ({_pdf_escape(f'{title} | Page {page_number} of {page_count}')}) Tj"
    )
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _pdf_escape(value: str) -> str:
    return (
        _pdf_text(value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _pdf_text(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a7": "Sec.",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    offsets = []
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(payload))


def _truncate(value: str, max_chars: int) -> str:
    text = str(value).replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _summary(
    *,
    intake: dict[str, Any],
    project_id: str,
    source_set_id: str,
    package_dir: Path,
    package_path: Path,
    markdown_path: Path,
    pdf_path: Path,
    manifest_path: Path,
    validation: dict[str, Any],
    selected_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "output_dir": str(package_dir),
        "output_paths": {
            "manifest": str(manifest_path),
            "markdown": str(markdown_path),
            "package": str(package_path),
            "pdf": str(pdf_path),
        },
        "output_written": False,
        "passed": validation["passed"],
        "failed_validation_checks": [
            check for check in validation["checks"] if not check["passed"]
        ],
        "intake_evidence_graph_edge_count": _intake_evidence_graph(
            intake, selected_scopes
        )["edge_count"],
        "intake_evidence_graph_node_count": _intake_evidence_graph(
            intake, selected_scopes
        )["node_count"],
        "project_id": project_id,
        "proposed_action_resource_area_count": len(_expected_resource_area_ids(intake)),
        "resource_scope_count": len(selected_scopes),
        "schema_version": "project-sow-package-summary-v0",
        "selected_resource_scope_ids": [
            str(scope.get("resource_scope_id")) for scope in selected_scopes
        ],
        "selected_resource_area_ids": sorted(_covered_resource_area_ids(selected_scopes)),
        "source_set_id": source_set_id,
        "validation_failure_count": validation["failure_count"],
    }


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
    return {
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


def _project_sow_eval_case_summary(
    *,
    case: dict[str, Any],
    output_dir: Path,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
) -> dict[str, Any]:
    intake_path = Path(str(case.get("intake_path") or ""))
    case_id = _slug(str(case.get("case_id") or intake_path.stem or "project-sow-eval-case"))
    package_result = run_project_sow_package(
        intake_path=intake_path,
        output_dir=output_dir,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
        results_dir=output_dir / "cases" / case_id,
    )
    package = (
        _read_json(package_result.package_path)
        if package_result.summary.get("output_written") and package_result.package_path.is_file()
        else {}
    )
    diagnostics = _project_sow_eval_resource_diagnostics(package=package, case=case)
    actual_metrics = _project_sow_eval_actual_metrics(
        package=package,
        package_summary=package_result.summary,
        diagnostics=diagnostics,
    )
    metric_checks = _project_sow_eval_checks(
        actual=actual_metrics,
        expected=case.get("expected_metrics"),
        prefix="expected_metrics",
    )
    diagnostic_checks = _project_sow_eval_checks(
        actual=diagnostics,
        expected=case.get("expected_diagnostics"),
        prefix="expected_diagnostics",
    )
    checks = metric_checks + diagnostic_checks
    return {
        "actual_metrics": actual_metrics,
        "case_id": case_id,
        "description": case.get("description"),
        "diagnostics": diagnostics,
        "expected_diagnostics": case.get("expected_diagnostics") or {},
        "expected_metrics": case.get("expected_metrics") or {},
        "intake_path": str(intake_path),
        "output_paths": package_result.summary.get("output_paths") or {},
        "package_passed": package_result.summary.get("passed"),
        "passed": bool(package_result.summary.get("passed"))
        and all(check["passed"] for check in checks),
        "validation_checks": checks,
    }


def _project_sow_eval_actual_metrics(
    *,
    package: dict[str, Any],
    package_summary: dict[str, Any],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_fields_passed": _project_sow_validation_check_passed(
            package, "selected_resource_scopes_have_contract_fields"
        ),
        "contract_ready_resource_scope_count": _project_sow_contract_ready_scope_count(
            package
        ),
        "intake_evidence_graph_edge_count": package_summary.get(
            "intake_evidence_graph_edge_count"
        ),
        "intake_evidence_graph_node_count": package_summary.get(
            "intake_evidence_graph_node_count"
        ),
        "output_written": bool(package_summary.get("output_written")),
        "package_passed": bool(package_summary.get("passed")),
        "pdf_header_valid": bool(package_summary.get("pdf_header_valid")),
        "proposed_action_resource_area_count": package_summary.get(
            "proposed_action_resource_area_count"
        ),
        "optional_deliverable_resource_scope_count": _project_sow_scope_count_with_field(
            package, "optional_deliverables"
        ),
        "rendering_checks_passed": _project_sow_rendering_checks_passed(package),
        "required_deliverable_resource_scope_count": _project_sow_scope_count_with_field(
            package, "required_deliverables"
        ),
        "resource_scope_count": package_summary.get("resource_scope_count"),
        "validation_failure_count": package_summary.get("validation_failure_count"),
        "calibration_gap_count": len(
            _strings(diagnostics.get("calibration_gap_resource_area_ids"))
        ),
        "expected_no_observed_report_count": len(
            _strings(diagnostics.get("expected_no_observed_report_resource_area_ids"))
        ),
        "intake_omission_count": len(
            _strings(diagnostics.get("intake_omission_resource_area_ids"))
        ),
        "system_miss_count": len(_strings(diagnostics.get("system_miss_resource_area_ids"))),
    }


def _project_sow_resource_scope_records(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        scope
        for scope in _list(package.get("resource_scope_records"))
        if isinstance(scope, dict)
    ]


def _project_sow_contract_ready_scope_count(package: dict[str, Any]) -> int:
    return sum(
        1
        for scope in _project_sow_resource_scope_records(package)
        if not any(_is_empty(scope.get(field)) for field in CONTRACT_REQUIRED_SCOPE_FIELDS)
    )


def _project_sow_scope_count_with_field(package: dict[str, Any], field: str) -> int:
    return sum(
        1
        for scope in _project_sow_resource_scope_records(package)
        if not _is_empty(scope.get(field))
    )


def _project_sow_eval_resource_diagnostics(
    *,
    package: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    rows = [row for row in _list(package.get("resource_analysis_matrix")) if isinstance(row, dict)]
    graph = package.get("intake_evidence_graph") if isinstance(package.get("intake_evidence_graph"), dict) else {}
    expected_resource_area_ids = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("expected_from_proposed_action") and row.get("resource_area_id")
    )
    canonical_path_misses = sorted(
        area_id
        for area_id in expected_resource_area_ids
        if not _has_canonical_resource_path(graph, area_id)
    )
    missing_sow_scope = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("coverage_status") == "missing_sow_scope" and row.get("resource_area_id")
    )
    intake_omissions = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("coverage_status") == "observed_not_derived_from_proposed_action"
        and row.get("resource_area_id")
    )
    expected_without_observed_reports = sorted(
        str(row.get("resource_area_id"))
        for row in rows
        if row.get("expected_from_proposed_action")
        and row.get("resource_area_id")
        and not _list(row.get("actual_specialist_reports"))
    )
    observed_reports_available = case.get("observed_reports_available") is True
    return {
        "calibration_gap_resource_area_ids": (
            expected_without_observed_reports if observed_reports_available else []
        ),
        "expected_no_observed_report_resource_area_ids": (
            [] if observed_reports_available else expected_without_observed_reports
        ),
        "expected_resource_area_ids": expected_resource_area_ids,
        "intake_omission_resource_area_ids": intake_omissions,
        "system_miss_resource_area_ids": sorted(
            set(canonical_path_misses) | set(missing_sow_scope)
        ),
    }


def _project_sow_eval_checks(
    *,
    actual: dict[str, Any],
    expected: Any,
    prefix: str,
) -> list[dict[str, Any]]:
    if not isinstance(expected, dict):
        return []
    return [
        _check(
            name=f"{prefix}.{key}",
            passed=actual.get(key) == expected_value,
            details={"actual": actual.get(key), "expected": expected_value},
        )
        for key, expected_value in sorted(expected.items())
    ]


def _project_sow_rendering_checks_passed(package: dict[str, Any]) -> bool:
    return all(
        _project_sow_validation_check_passed(package, name)
        for name in {
            "project_sow_markdown_required_sections_present",
            "project_sow_pdf_required_items_present",
        }
    )


def _project_sow_validation_check_passed(package: dict[str, Any], check_name: str) -> bool:
    validation = package.get("validation") if isinstance(package.get("validation"), dict) else {}
    checks = {
        str(check.get("name")): check
        for check in _list(validation.get("checks"))
        if isinstance(check, dict)
    }
    return checks.get(check_name, {}).get("passed") is True


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


def _project_sow_adjudication_eval_summary(
    *,
    context: dict[str, Any],
    adjudication: dict[str, Any],
    adjudication_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    item_results = _project_sow_adjudication_item_results(
        expected_items=context["queue_items"],
        adjudication_items=_list(adjudication.get("items")),
    )
    decision_counts = Counter(
        str(result.get("decision"))
        for result in item_results
        if result.get("decision") in PROJECT_SOW_ADJUDICATION_DECISIONS
    )
    checks = _project_sow_adjudication_eval_checks(
        context=context,
        adjudication=adjudication,
        item_results=item_results,
    )
    failure_counts = Counter(
        category
        for result in item_results
        for category in _strings(result.get("failure_categories"))
    )
    for check in checks:
        if not check["passed"]:
            failure_counts[str(check["name"])] += 1
    passed = all(check["passed"] for check in checks) and all(
        result["passed"] for result in item_results
    )
    return {
        "adjudication_id": adjudication.get("adjudication_id"),
        "adjudication_item_count": len(_list(adjudication.get("items"))),
        "adjudication_path": str(adjudication_path),
        "adjudication_status": _project_sow_adjudication_status(
            passed=passed,
            decision_counts=decision_counts,
            item_count=len(context["queue_items"]),
        ),
        "completed_item_count": sum(1 for result in item_results if result["passed"]),
        "decision_counts": dict(sorted(decision_counts.items())),
        "failed_validation_checks": [check for check in checks if not check["passed"]],
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "input_hashes": context["input_hashes"],
        "item_results": item_results,
        "output_path": str(output_path),
        "passed": passed,
        "pending_item_count": sum(1 for result in item_results if not result["passed"]),
        "project_id": context["project_id"],
        "queue_item_count": len(context["queue_items"]),
        "schema_version": PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "source_set_id": context["source_set_id"],
        "validation_checks": checks,
    }


def _project_sow_adjudication_eval_checks(
    *,
    context: dict[str, Any],
    adjudication: dict[str, Any],
    item_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expected_ids = {str(item.get("item_id")) for item in context["queue_items"]}
    adjudication_ids = [
        str(item.get("item_id") or "")
        for item in _list(adjudication.get("items"))
        if isinstance(item, dict)
    ]
    missing_item_ids = sorted(expected_ids - set(adjudication_ids))
    unexpected_item_ids = sorted(set(adjudication_ids) - expected_ids)
    duplicate_item_ids = _duplicates(adjudication_ids)
    return [
        _check(
            name="project_sow_adjudication_schema_supported",
            passed=adjudication.get("schema_version") == PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION,
            details={"schema_version": adjudication.get("schema_version")},
        ),
        _check(
            name="project_sow_adjudication_identity_matches_intake",
            passed=(
                adjudication.get("project_id") == context["project_id"]
                and adjudication.get("source_set_id") == context["source_set_id"]
            ),
            details={
                "actual_project_id": adjudication.get("project_id"),
                "actual_source_set_id": adjudication.get("source_set_id"),
                "expected_project_id": context["project_id"],
                "expected_source_set_id": context["source_set_id"],
            },
        ),
        _check(
            name="project_sow_adjudication_input_hashes_match",
            passed=adjudication.get("input_hashes") == context["input_hashes"],
            details={
                "actual": adjudication.get("input_hashes"),
                "expected": context["input_hashes"],
            },
        ),
        _check(
            name="project_sow_adjudication_items_cover_current_queue",
            passed=not missing_item_ids and not unexpected_item_ids and not duplicate_item_ids,
            details={
                "duplicate_item_ids": duplicate_item_ids,
                "missing_item_ids": missing_item_ids,
                "unexpected_item_ids": unexpected_item_ids,
            },
        ),
        _check(
            name="project_sow_adjudication_items_complete",
            passed=all(result["passed"] for result in item_results),
            details={
                "failed_item_ids": [
                    result["item_id"] for result in item_results if not result["passed"]
                ]
            },
        ),
    ]


def _project_sow_adjudication_item_results(
    *,
    expected_items: list[dict[str, Any]],
    adjudication_items: list[Any],
) -> list[dict[str, Any]]:
    expected_by_id = {str(item.get("item_id")): item for item in expected_items}
    actual_by_id = {
        str(item.get("item_id") or ""): item
        for item in adjudication_items
        if isinstance(item, dict)
    }
    duplicate_counts = Counter(
        str(item.get("item_id") or "")
        for item in adjudication_items
        if isinstance(item, dict)
    )
    results = [
        _project_sow_adjudication_item_result(
            adjudication=item,
            expected=expected_by_id.get(str(item.get("item_id") or ""))
            if isinstance(item, dict)
            else None,
            duplicate_count=duplicate_counts[str(item.get("item_id") or "")]
            if isinstance(item, dict)
            else 0,
        )
        for item in adjudication_items
    ]
    missing_ids = sorted(set(expected_by_id) - set(actual_by_id))
    for item_id in missing_ids:
        expected = expected_by_id[item_id]
        results.append(
            {
                "adjudicated_at": None,
                "adjudicated_by": [],
                "current_status": expected.get("current_status"),
                "decision": None,
                "decision_source": None,
                "failure_categories": ["adjudication_missing"],
                "issue_summary": expected.get("issue_summary"),
                "item_id": item_id,
                "item_type": expected.get("item_type"),
                "optional_deliverable": expected.get("optional_deliverable"),
                "passed": False,
                "rationale": None,
                "resource_area_id": expected.get("resource_area_id"),
                "resource_scope_id": expected.get("resource_scope_id"),
            }
        )
    return sorted(results, key=lambda result: str(result.get("item_id") or ""))


def _project_sow_adjudication_item_result(
    *,
    adjudication: Any,
    expected: dict[str, Any] | None,
    duplicate_count: int,
) -> dict[str, Any]:
    if not isinstance(adjudication, dict):
        return {
            "adjudicated_at": None,
            "adjudicated_by": [],
            "current_status": None,
            "decision": None,
            "decision_source": None,
            "failure_categories": ["adjudication_item_not_object"],
            "issue_summary": None,
            "item_id": "",
            "item_type": None,
            "optional_deliverable": None,
            "passed": False,
            "rationale": None,
            "resource_area_id": None,
            "resource_scope_id": None,
        }
    failure_categories: list[str] = []
    item_id = str(adjudication.get("item_id") or "")
    item_type = str(adjudication.get("item_type") or "")
    decision = str(adjudication.get("decision") or "")
    if expected is None:
        failure_categories.append("adjudication_unexpected")
    if duplicate_count > 1:
        failure_categories.append("adjudication_duplicate")
    if item_type not in PROJECT_SOW_ADJUDICATION_ITEM_TYPES:
        failure_categories.append("adjudication_invalid_item_type")
    if expected is not None and item_type != expected.get("item_type"):
        failure_categories.append("adjudication_identity_mismatch")
    if decision == "pending" or not decision:
        failure_categories.append("adjudication_pending")
    elif decision not in PROJECT_SOW_ADJUDICATION_DECISIONS:
        failure_categories.append("adjudication_invalid_decision")
    if decision in PROJECT_SOW_ADJUDICATION_DECISIONS:
        missing_fields = _missing_project_sow_adjudication_fields(adjudication)
        if missing_fields:
            failure_categories.append("adjudication_incomplete")
    return {
        "adjudicated_at": adjudication.get("adjudicated_at"),
        "adjudicated_by": _strings(adjudication.get("adjudicated_by")),
        "current_status": adjudication.get("current_status"),
        "decision": decision,
        "decision_source": adjudication.get("decision_source"),
        "failure_categories": sorted(set(failure_categories)),
        "issue_summary": adjudication.get("issue_summary"),
        "item_id": item_id,
        "item_type": item_type,
        "missing_fields": _missing_project_sow_adjudication_fields(adjudication),
        "optional_deliverable": adjudication.get("optional_deliverable"),
        "passed": not failure_categories,
        "rationale": adjudication.get("rationale"),
        "resource_area_id": adjudication.get("resource_area_id"),
        "resource_scope_id": adjudication.get("resource_scope_id"),
    }


def _missing_project_sow_adjudication_fields(adjudication: dict[str, Any]) -> list[str]:
    missing = []
    for field in ("adjudicated_at", "decision_source", "rationale"):
        if _is_empty(adjudication.get(field)):
            missing.append(field)
    if not _strings(adjudication.get("adjudicated_by")):
        missing.append("adjudicated_by")
    return missing


def _project_sow_adjudication_status(
    *,
    passed: bool,
    decision_counts: Counter[str],
    item_count: int,
) -> str:
    if not passed:
        return "failed"
    if item_count == 0:
        return "not_required"
    if decision_counts.get("needs_information", 0):
        return "adjudicated_needs_information"
    return "adjudicated"


def _project_sow_adjudication_apply_summary(
    *,
    eval_summary: dict[str, Any],
    adjudication_path: Path,
    eval_output_path: Path,
    intake_path: Path,
    output_intake_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    return {
        "adjudication_path": str(adjudication_path),
        "adjudication_status": eval_summary.get("adjudication_status"),
        "decision_counts": eval_summary.get("decision_counts") or {},
        "eval_output_path": str(eval_output_path),
        "failed_validation_checks": eval_summary.get("failed_validation_checks") or [],
        "input_hashes": eval_summary.get("input_hashes") or {},
        "intake_path": str(intake_path),
        "item_count": eval_summary.get("queue_item_count"),
        "output_intake_path": str(output_intake_path),
        "output_path": str(output_path),
        "output_written": False,
        "passed": eval_summary.get("passed") is True,
        "schema_version": PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION,
    }


def _project_sow_intake_adjudication(
    *,
    eval_summary: dict[str, Any],
    adjudication_path: Path,
    eval_output_path: Path,
) -> dict[str, Any]:
    items = [
        {
            "adjudicated_at": result.get("adjudicated_at"),
            "adjudicated_by": result.get("adjudicated_by") or [],
            "current_status": result.get("current_status"),
            "decision": result.get("decision"),
            "decision_source": result.get("decision_source"),
            "issue_summary": result.get("issue_summary"),
            "item_id": result.get("item_id"),
            "item_type": result.get("item_type"),
            "optional_deliverable": result.get("optional_deliverable"),
            "rationale": result.get("rationale"),
            "resource_area_id": result.get("resource_area_id"),
            "resource_scope_id": result.get("resource_scope_id"),
        }
        for result in _list(eval_summary.get("item_results"))
        if isinstance(result, dict) and result.get("passed") is True
    ]
    return {
        "adjudication_id": eval_summary.get("adjudication_id"),
        "adjudication_path": str(adjudication_path),
        "applied_at": _now(),
        "boundaries": [
            "Project SOW adjudication is a planning overlay only.",
            "It does not create applicability decisions, compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions.",
        ],
        "decision_counts": eval_summary.get("decision_counts") or {},
        "eval_output_path": str(eval_output_path),
        "input_hashes": eval_summary.get("input_hashes") or {},
        "item_count": len(items),
        "items": items,
        "schema_version": PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION,
        "status": eval_summary.get("adjudication_status"),
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


def _source_set_id(authority_inventory: dict[str, Any]) -> str:
    return str(
        authority_inventory.get("source_set", {}).get("source_set_id")
        or authority_inventory.get("source_set_id")
        or "source-set-unspecified"
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Required JSON file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Required JSON file is invalid: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Required JSON file must contain an object: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _resource_scopes(resource_config: dict[str, Any]) -> list[dict[str, Any]]:
    scopes = resource_config.get("resource_scopes")
    if not isinstance(scopes, list):
        return []
    return [scope for scope in scopes if isinstance(scope, dict)]


def _authority_family_ids(authority_inventory: dict[str, Any]) -> set[str]:
    family_ids = {
        str(family.get("family_id"))
        for family in _list(authority_inventory.get("authority_families"))
        if isinstance(family, dict) and family.get("family_id")
    }
    for family in _list(authority_inventory.get("authority_families")):
        if isinstance(family, dict) and family.get("authority_family_id"):
            family_ids.add(str(family["authority_family_id"]))
    return family_ids


def _indicator_keys(intake: dict[str, Any]) -> set[str]:
    indicators = intake.get("resource_indicators")
    keys = set()
    if isinstance(indicators, dict):
        keys.update(_normalize_token(str(key)) for key in indicators)
    for element in _proposed_action_elements(intake):
        keys.update(
            _normalize_token(value)
            for value in _strings(element.get("resource_indicator_keys"))
        )
    return keys


def _resource_area_catalog(intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for area in _list(intake.get("resource_analysis_expectations")):
        if isinstance(area, dict) and area.get("resource_area_id"):
            area_id = _normalize_token(str(area["resource_area_id"]))
            catalog[area_id] = {**area, "resource_area_id": area_id}
    for element in _proposed_action_elements(intake):
        for area_id in _resource_area_ids(element.get("resource_area_ids")):
            catalog.setdefault(
                area_id,
                {
                    "resource_area_id": area_id,
                    "resource_area_name": _title_from_id(area_id),
                },
            )
    return catalog


def _expected_resource_area_ids(intake: dict[str, Any]) -> set[str]:
    area_ids = _resource_area_ids(intake.get("expected_resource_area_ids"))
    area_ids.update(_resource_area_catalog(intake))
    for element in _proposed_action_elements(intake):
        area_ids.update(_resource_area_ids(element.get("resource_area_ids")))
    return area_ids


def _covered_resource_area_ids(scopes: list[dict[str, Any]]) -> set[str]:
    return {
        area_id
        for scope in scopes
        for area_id in _resource_area_ids(scope.get("covered_resource_area_ids"))
    }


def _observed_report_resource_area_ids(intake: dict[str, Any]) -> set[str]:
    return {
        area_id
        for report in _observed_specialist_reports(intake)
        for area_id in _resource_area_ids(report.get("resource_area_ids"))
    }


def _draft_project_sow_intake(
    *,
    proposed_action_text: str,
    proposed_action_path: Path,
    draft_rules: dict[str, Any],
    project_id: str | None,
    project_name: str | None,
    forest: str | None,
    districts: list[str] | None,
    project_type: str,
    nepa_level: str,
    source_title: str | None,
) -> dict[str, Any]:
    source_title = source_title or proposed_action_path.name
    inferred_project_name = project_name or _infer_project_name(proposed_action_text)
    selected_project_id = _slug(project_id or inferred_project_name)
    selected_project_type = _normalize_token(project_type or "land_exchange") or "land_exchange"
    selected_districts = [district for district in districts or [] if district.strip()]
    if not selected_districts:
        selected_districts = ["review_needed"]

    federal_actions, federal_action_flags = _draft_federal_land_actions(
        proposed_action_text=proposed_action_text,
        draft_rules=draft_rules,
        project_type=selected_project_type,
    )
    action_elements, resource_candidates, element_flags = _draft_action_elements(
        proposed_action_text=proposed_action_text,
        source_title=source_title,
        draft_rules=draft_rules,
        project_type=selected_project_type,
    )
    resource_expectations = _draft_resource_expectations(resource_candidates)
    resource_indicators = _draft_resource_indicators(resource_candidates)
    uncertainty_flags = sorted(
        {
            "draft_requires_reviewer_confirmation",
            "resource_area_candidates_require_review",
            *federal_action_flags,
            *element_flags,
        }
    )
    return {
        "consultation_indicators": _draft_consultation_indicators(resource_candidates),
        "districts": selected_districts,
        "draft_metadata": {
            "candidate_federal_land_action_types": [
                str(action.get("action_type")) for action in federal_actions
            ],
            "candidate_resource_area_ids": sorted(resource_candidates),
            "draft_notice": (
                "Deterministic draft for reviewer intake authoring. It does not decide "
                "authority applicability, compliance, or final agency action."
            ),
            "review_status": "unreviewed",
            "reviewer_confirmation_required": True,
            "schema_version": "project-sow-intake-draft-v0",
            "source_text_sha256": hashlib.sha256(
                proposed_action_text.encode("utf-8")
            ).hexdigest(),
            "source_text_path": str(proposed_action_path),
            "uncertainty_flags": uncertainty_flags,
        },
        "federal_land_actions": federal_actions,
        "forest": forest or "review_needed",
        "forest_plan_profile": "review_needed",
        "geography": [],
        "management_context": [],
        "nepa_level": nepa_level or "environmental_assessment",
        "observed_specialist_reports": [],
        "project_id": selected_project_id,
        "project_name": inferred_project_name,
        "project_type": selected_project_type,
        "proponent": "review_needed",
        "proposed_action_elements": action_elements,
        "proposed_action_summary": _proposed_action_summary_from_text(proposed_action_text),
        "resource_analysis_expectations": resource_expectations,
        "resource_indicators": resource_indicators,
        "schema_version": "project-sow-intake-v0",
    }


def _draft_federal_land_actions(
    *,
    proposed_action_text: str,
    draft_rules: dict[str, Any],
    project_type: str,
) -> tuple[list[dict[str, str]], list[str]]:
    text = _searchable_text(proposed_action_text)
    actions: list[dict[str, str]] = []
    flags: list[str] = []
    for rule in _list(draft_rules.get("federal_land_action_rules")):
        if not isinstance(rule, dict):
            continue
        terms = _strings(rule.get("trigger_terms"))
        matched_terms = _matched_terms(text, terms)
        if not matched_terms:
            continue
        action_type = str(rule.get("action_type") or "review_needed")
        actions.append(
            {
                "action_type": action_type,
                "description": (
                    f"Draft candidate {action_type} action matched from proposed-action "
                    f"text terms: {', '.join(matched_terms)}. Reviewer must confirm."
                ),
            }
        )
    if not actions:
        flags.append("federal_land_actions_need_review")
        actions.append(
            {
                "action_type": "review_needed",
                "description": (
                    "Reviewer must identify the federal land disposal, acquisition, "
                    "reservation, or other land action before package generation."
                ),
            }
        )
    if project_type == "land_exchange" and not {
        str(action.get("action_type")) for action in actions
    }.intersection({"dispose", "acquire"}):
        flags.append("land_exchange_action_types_uncertain")
    return actions, flags


def _draft_action_elements(
    *,
    proposed_action_text: str,
    source_title: str,
    draft_rules: dict[str, Any],
    project_type: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    passages = _candidate_action_passages(proposed_action_text)
    resource_candidates: dict[str, dict[str, Any]] = {}
    elements: list[dict[str, Any]] = []
    flags: list[str] = []
    for index, passage in enumerate(passages, start=1):
        matched_resources = _draft_resource_candidates(
            text=passage,
            draft_rules=draft_rules,
            project_type=project_type,
        )
        if not matched_resources:
            continue
        for area_id, candidate in matched_resources.items():
            existing = resource_candidates.setdefault(area_id, candidate)
            existing.setdefault("matched_terms", [])
            existing["matched_terms"] = sorted(
                set(_strings(existing.get("matched_terms")) + _strings(candidate.get("matched_terms")))
            )
        element_id = f"draft_action_element_{index:02d}"
        elements.append(
            {
                "action_element_id": element_id,
                "description": _truncate(passage, 300),
                "draft_status": "candidate_reviewer_confirmation_required",
                "evidence_refs": [
                    {
                        "citation_label": f"Draft proposed action paragraph {index}",
                        "evidence_ref_id": f"draft-proposed-action-paragraph-{index:02d}",
                        "locator": f"paragraph {index}",
                        "source_record_id": "DRAFT-PROPOSED-ACTION",
                        "summary": _truncate(passage, 240),
                        "title": source_title,
                    }
                ],
                "resource_area_ids": sorted(matched_resources),
                "resource_indicator_keys": sorted(
                    {
                        str(candidate.get("indicator_key"))
                        for candidate in matched_resources.values()
                        if candidate.get("indicator_key")
                    }
                ),
            }
        )
    if not elements:
        flags.append("resource_area_candidates_need_review")
        fallback_resources = _draft_resource_candidates(
            text="land exchange",
            draft_rules=draft_rules,
            project_type=project_type,
        )
        resource_candidates.update(fallback_resources)
        elements.append(
            {
                "action_element_id": "draft_action_element_01",
                "description": (
                    "Reviewer must identify proposed-action elements and resource areas "
                    "from the source narrative."
                ),
                "draft_status": "candidate_reviewer_confirmation_required",
                "evidence_refs": [
                    {
                        "citation_label": "Draft proposed action narrative",
                        "evidence_ref_id": "draft-proposed-action-narrative",
                        "locator": "full proposed action text",
                        "source_record_id": "DRAFT-PROPOSED-ACTION",
                        "summary": _truncate(proposed_action_text, 240),
                        "title": source_title,
                    }
                ],
                "resource_area_ids": sorted(fallback_resources) or ["land_exchange_case"],
                "resource_indicator_keys": ["lands_realty"],
            }
        )
    return elements, resource_candidates, flags


def _draft_resource_candidates(
    *,
    text: str,
    draft_rules: dict[str, Any],
    project_type: str,
) -> dict[str, dict[str, Any]]:
    searchable_text = _searchable_text(text)
    candidates: dict[str, dict[str, Any]] = {}
    for rule in _list(draft_rules.get("resource_area_rules")):
        if not isinstance(rule, dict):
            continue
        area_id = _normalize_token(str(rule.get("resource_area_id") or ""))
        if not area_id:
            continue
        matched_terms = _matched_terms(searchable_text, _strings(rule.get("trigger_terms")))
        always_project_types = {
            _normalize_token(value) for value in _strings(rule.get("always_for_project_types"))
        }
        if not matched_terms and project_type not in always_project_types:
            continue
        candidates[area_id] = {
            "indicator_key": rule.get("indicator_key"),
            "matched_terms": matched_terms or [f"project_type:{project_type}"],
            "resource_area_id": area_id,
            "resource_area_name": rule.get("resource_area_name") or _title_from_id(area_id),
        }
    return candidates


def _draft_resource_expectations(
    resource_candidates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "draft_status": "candidate_reviewer_confirmation_required",
            "proposed_action_basis": [
                "Draft candidate from proposed-action source text; reviewer must confirm.",
                "Matched terms: " + ", ".join(_strings(candidate.get("matched_terms"))),
            ],
            "resource_area_id": area_id,
            "resource_area_name": str(candidate.get("resource_area_name") or _title_from_id(area_id)),
        }
        for area_id, candidate in sorted(resource_candidates.items())
    ]


def _draft_resource_indicators(
    resource_candidates: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    indicators: dict[str, set[str]] = {}
    for candidate in resource_candidates.values():
        indicator_key = str(candidate.get("indicator_key") or "").strip()
        if not indicator_key:
            continue
        indicators.setdefault(indicator_key, set()).update(
            _strings(candidate.get("matched_terms"))
        )
    return {key: sorted(values) for key, values in sorted(indicators.items())}


def _draft_consultation_indicators(
    resource_candidates: dict[str, dict[str, Any]],
) -> list[str]:
    indicators = []
    if "species_consultation" in resource_candidates:
        indicators.append("ESA Section 7 review needed")
    if "cultural_resources" in resource_candidates or "tribal_relations" in resource_candidates:
        indicators.append("NHPA/tribal consultation review needed")
    return indicators


def _candidate_action_passages(text: str) -> list[str]:
    passages = []
    for raw in re.split(r"\n\s*\n", text):
        passage = re.sub(r"^\s*[-*]\s*", "", raw.strip())
        passage = re.sub(r"\s+", " ", passage)
        if passage:
            passages.append(passage)
    return passages or [text.strip()]


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    return sorted({term for term in terms if term.lower() in text})


def _infer_project_name(text: str) -> str:
    for line in text.splitlines():
        value = line.strip(" #\t")
        if value:
            return _truncate(value, 90)
    return "Draft Project SOW Intake"


def _proposed_action_summary_from_text(text: str) -> str:
    for passage in _candidate_action_passages(text):
        if passage:
            return _truncate(passage, 700)
    return "Draft proposed action summary requires reviewer completion."


def _draft_reviewer_confirmation_errors(intake: dict[str, Any]) -> list[str]:
    draft_metadata = intake.get("draft_metadata")
    if not isinstance(draft_metadata, dict):
        return []
    errors = []
    if draft_metadata.get("review_status") != "reviewer_confirmed":
        errors.append("draft_metadata.review_status must be reviewer_confirmed")
    if draft_metadata.get("reviewer_confirmation_required") is not False:
        errors.append("draft_metadata.reviewer_confirmation_required must be false")
    if _strings(draft_metadata.get("uncertainty_flags")):
        errors.append("draft_metadata.uncertainty_flags must be empty")
    return errors


def _intake_schema_shape_errors(intake: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _required_object_field_errors(
            _list(intake.get("federal_land_actions")),
            path="federal_land_actions",
            required_fields=("action_type", "description"),
        )
    )
    for element_index, element in enumerate(_proposed_action_elements(intake)):
        element_path = f"proposed_action_elements[{element_index}]"
        errors.extend(
            _required_fields_for_record(
                element,
                path=element_path,
                required_fields=("action_element_id", "description"),
            )
        )
        if not _resource_area_ids(element.get("resource_area_ids")):
            errors.append(f"{element_path}.resource_area_ids: must contain at least one item")
        evidence_refs = _list(element.get("evidence_refs"))
        if not evidence_refs:
            errors.append(f"{element_path}.evidence_refs: must contain at least one item")
        errors.extend(_evidence_ref_shape_errors(evidence_refs, path=f"{element_path}.evidence_refs"))

    errors.extend(
        _required_object_field_errors(
            _list(intake.get("resource_analysis_expectations")),
            path="resource_analysis_expectations",
            required_fields=("resource_area_id", "resource_area_name"),
        )
    )
    for report_index, report in enumerate(_observed_specialist_reports_raw(intake)):
        report_path = f"observed_specialist_reports[{report_index}]"
        errors.extend(
            _required_fields_for_record(
                report,
                path=report_path,
                required_fields=("report_id", "resource_area_ids", "title"),
            )
        )
        if not _resource_area_ids(report.get("resource_area_ids")):
            errors.append(f"{report_path}.resource_area_ids: must contain at least one item")
        errors.extend(
            _evidence_ref_shape_errors(
                _list(report.get("evidence_refs")),
                path=f"{report_path}.evidence_refs",
            )
        )
    return errors


def _required_object_field_errors(
    records: list[Any],
    *,
    path: str,
    required_fields: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}[{index}]: must be an object")
            continue
        errors.extend(
            _required_fields_for_record(
                record,
                path=f"{path}[{index}]",
                required_fields=required_fields,
            )
        )
    return errors


def _evidence_ref_shape_errors(records: list[Any], *, path: str) -> list[str]:
    return _required_object_field_errors(
        records,
        path=path,
        required_fields=("evidence_ref_id", "locator", "source_record_id", "summary", "title"),
    )


def _required_fields_for_record(
    record: dict[str, Any],
    *,
    path: str,
    required_fields: tuple[str, ...],
) -> list[str]:
    return [
        f"{path}.{field}: required"
        for field in required_fields
        if _is_empty(record.get(field))
    ]


def _proposed_action_elements(intake: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        element
        for element in _list(intake.get("proposed_action_elements"))
        if isinstance(element, dict)
    ]


def _observed_specialist_reports_raw(intake: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report
        for report in _list(intake.get("observed_specialist_reports"))
        if isinstance(report, dict)
    ]


def _observed_specialist_reports(intake: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for report in _observed_specialist_reports_raw(intake):
        records.append(
            {
                "document_role": report.get("document_role") or "specialist_report",
                "evidence_refs": _evidence_refs(report),
                "report_id": report.get("report_id"),
                "resource_area_ids": sorted(
                    _resource_area_ids(report.get("resource_area_ids"))
                ),
                "source_record_id": report.get("source_record_id"),
                "title": report.get("title"),
            }
        )
    return records


def _evidence_refs(record: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for evidence_ref in _list(record.get("evidence_refs")):
        if not isinstance(evidence_ref, dict):
            continue
        refs.append(
            {
                "citation_label": evidence_ref.get("citation_label"),
                "evidence_ref_id": evidence_ref.get("evidence_ref_id"),
                "locator": evidence_ref.get("locator"),
                "source_record_id": evidence_ref.get("source_record_id"),
                "summary": evidence_ref.get("summary"),
                "title": evidence_ref.get("title"),
            }
        )
    return refs


def _resource_area_ids(value: Any) -> set[str]:
    return {_normalize_token(item) for item in _strings(value)}


def _title_from_id(value: str) -> str:
    return value.replace("_", " ").title()


def _searchable_text(value: Any) -> str:
    text = " ".join(_flatten_strings(value)).lower()
    return re.sub(r"\s+", " ", text)


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_flatten_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_flatten_strings(item))
        return strings
    if value is None:
        return []
    return [str(value)]


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _slug(value: str) -> str:
    slug = _normalize_token(value).replace("_", "-")
    return slug or "project"


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"details": details, "name": name, "passed": bool(passed)}


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list | dict):
        return not value
    return False


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _duplicates(values: Any) -> list[str]:
    counts = Counter(value for value in values if value)
    return sorted(value for value, count in counts.items() if count > 1)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
