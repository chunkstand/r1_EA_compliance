from __future__ import annotations

from pathlib import Path
from typing import Any

from .project_sow_package_common import _list
from .project_sow_package_common import _intake_adjudication_summary
from .project_sow_package_common import _now
from .project_sow_package_common import _read_json
from .project_sow_package_common import _sha256_file
from .project_sow_package_common import _resource_area_ids
from .project_sow_package_common import _slug
from .project_sow_package_common import _source_set_id
from .project_sow_package_common import _strings
from .project_sow_package_common import _title_from_id
from .project_sow_package_common import _write_json
from .project_sow_package_graph import _intake_evidence_graph
from .project_sow_package_graph import _intake_summary
from .project_sow_package_intake_support import _covered_resource_area_ids
from .project_sow_package_intake_support import _expected_resource_area_ids
from .project_sow_package_intake_support import _observed_specialist_reports
from .project_sow_package_intake_support import _proposed_action_elements
from .project_sow_package_intake_support import _resource_area_catalog
from .project_sow_package_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package_models import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package_models import GENERATOR_VERSION
from .project_sow_package_models import MANIFEST_SCHEMA_VERSION
from .project_sow_package_models import PACKAGE_SCHEMA_VERSION
from .project_sow_package_models import ProjectSowPackageResult
from .project_sow_package_rendering import _paginate_pdf_lines
from .project_sow_package_rendering import _render_markdown
from .project_sow_package_rendering import _render_pdf_lines
from .project_sow_package_rendering import _rendering_validation_checks
from .project_sow_package_rendering import _reviewer_summary
from .project_sow_package_rendering import _write_simple_pdf
from .project_sow_package_validation import _select_resource_scopes
from .project_sow_package_validation import _validate_inputs

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
    adjudication_summary = _intake_adjudication_summary(intake)
    return {
        "adjudication_decision_counts": adjudication_summary["decision_counts"],
        "adjudication_item_count": adjudication_summary["item_count"],
        "adjudication_status": adjudication_summary["status"],
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

def _project_sow_resource_scope_records(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        scope
        for scope in _list(package.get("resource_scope_records"))
        if isinstance(scope, dict)
    ]
