from __future__ import annotations

from typing import Any

from .project_sow_package_common import _check
from .project_sow_package_common import _duplicates
from .project_sow_package_common import _intake_adjudication_summary
from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _normalize_token
from .project_sow_package_common import _resource_area_ids
from .project_sow_package_common import _slug
from .project_sow_package_common import _strings
from .project_sow_package_common import _title_from_id
from .project_sow_package_intake_support import _evidence_refs
from .project_sow_package_intake_support import _expected_resource_area_ids
from .project_sow_package_intake_support import _indicator_keys
from .project_sow_package_intake_support import _observed_specialist_reports
from .project_sow_package_intake_support import _proposed_action_elements
from .project_sow_package_intake_support import _resource_area_catalog
from .project_sow_package_models import CONTRACT_REQUIRED_SCOPE_FIELDS

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
