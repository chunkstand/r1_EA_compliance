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
        "authority_family_ids": _strings(scope.get("authority_family_ids")),
        "covered_resource_area_ids": sorted(
            _resource_area_ids(scope.get("covered_resource_area_ids"))
        ),
        "data_needs": _strings(scope.get("data_needs")),
        "defensibility_checks": _strings(scope.get("defensibility_checks")),
        "discipline": scope.get("discipline"),
        "matched_indicator_keys": _strings(scope.get("matched_indicator_keys")),
        "matched_resource_area_ids": sorted(
            _resource_area_ids(scope.get("matched_resource_area_ids"))
        ),
        "matched_terms": _strings(scope.get("matched_terms")),
        "required_deliverables": _strings(scope.get("required_deliverables")),
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
    return {
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
            "",
            "## Resource Scopes",
            "",
            "| Scope | Discipline | Covered resource areas | Deliverables |",
            "| --- | --- | --- | --- |",
        ]
    )
    for scope in package["resource_scope_records"]:
        lines.append(
            f"| {scope['resource_name']} | `{scope['discipline']}` | "
            f"{', '.join(f'`{item}`' for item in scope['covered_resource_area_ids'])} | "
            f"{len(scope['required_deliverables'])} |"
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
        lines.append("Deliverables:")
        lines.extend(f"- {deliverable}" for deliverable in scope["required_deliverables"])
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
            f"({len(scope['required_deliverables'])} deliverables)"
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
        "## Resource Analysis Coverage",
        "## Intake Evidence Graph",
        "## Validation",
    ]
    required_pdf_items = [
        "Reviewer Snapshot",
        "Package Boundaries",
        "Review Checklist",
        "Resource Scopes",
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


def _proposed_action_elements(intake: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        element
        for element in _list(intake.get("proposed_action_elements"))
        if isinstance(element, dict)
    ]


def _observed_specialist_reports(intake: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for report in _list(intake.get("observed_specialist_reports")):
        if not isinstance(report, dict):
            continue
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
