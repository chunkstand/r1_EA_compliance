from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


NEPA_3D_GRAPH_CONTRACT_SCHEMA_VERSION = "nepa-3d-graph-contract-v1"
NEPA_3D_GRAPH_SCHEMA_VERSION = "nepa-3d-knowledge-graph-v1"
DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH = Path("config/nepa_3d_graph_contract_v1.json")

REQUIRED_EXPORT_SCOPES = {"source_set", "review"}
REQUIRED_NODE_TYPES = {
    "source_set",
    "review",
    "authority_family",
    "source_record",
    "artifact",
    "chunk",
    "evidence_span",
    "source_claim",
    "rule_template",
    "applicability_decision",
    "generated_rule",
    "compliance_finding",
    "forest_unit",
    "forest_plan",
    "forest_plan_component",
    "readiness_blocker",
}
REQUIRED_EDGE_TYPES = {
    "CONTAINS_AUTHORITY_FAMILY",
    "HAS_SOURCE_RECORD",
    "HAS_ARTIFACT",
    "HAS_CHUNK",
    "HAS_EVIDENCE_SPAN",
    "SUPPORTS_SOURCE_CLAIM",
    "SUPPORTS_RULE_TEMPLATE",
    "PRODUCES_APPLICABILITY_DECISION",
    "GENERATES_RULE",
    "SUPPORTS_COMPLIANCE_FINDING",
    "SUPERSEDED_BY",
    "REPLACES_RESERVED_AUTHORITY",
    "HAS_CURRENTNESS_STATUS",
    "BLOCKED_BY",
    "APPLIES_TO_REVIEW",
    "NOT_APPLICABLE_TO_REVIEW",
    "NEEDS_ADJUDICATION",
    "ADJUDICATED_BY",
    "BELONGS_TO_FOREST_UNIT",
    "HAS_FOREST_PLAN",
    "HAS_FOREST_COMPONENT",
    "HAS_READINESS_BLOCKER",
    "DISPLAYED_IN_LENS",
}
REQUIRED_DISPLAY_STATUSES = {
    "active",
    "superseded",
    "reserved",
    "candidate",
    "out_of_scope",
    "applicable",
    "not_applicable",
    "unresolved",
    "adjudicated",
    "readiness_blocked",
}
REQUIRED_REVIEW_READINESS_STATUSES = {
    "reviewer_ready",
    "not_reviewer_ready",
    "not_review_specific",
    "source_currentness_only",
    "blocked",
    "needs_adjudication",
}
REQUIRED_READINESS_BLOCKER_TYPES = {
    "missing_source",
    "stale_artifact",
    "superseded_source",
    "retrieval_miss",
    "graph_trace_gap",
    "search_coverage_gap",
    "adjudication_needed",
    "package_fixture_missing",
    "forest_profile_not_ready",
    "fsh_chapter_delta_required",
}
REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "graph_id",
    "created_at",
    "export_scope",
    "inputs",
    "lens_metadata",
    "nodes",
    "edges",
    "summary",
    "validation",
}
REQUIRED_NODE_FIELDS = {
    "node_id",
    "node_type",
    "label",
    "display_status",
    "review_readiness_status",
    "provenance",
    "currentness_metadata",
    "readiness_blockers",
}
REQUIRED_EDGE_FIELDS = {
    "edge_id",
    "edge_type",
    "source_node_id",
    "target_node_id",
    "display_status",
    "review_readiness_status",
    "provenance",
}
REQUIRED_SUMMARY_FIELDS = {
    "node_count",
    "edge_count",
    "node_type_counts",
    "edge_type_counts",
    "display_status_counts",
    "review_readiness_status_counts",
    "readiness_blocker_counts",
}
REQUIRED_VALIDATION_FIELDS = {"passed", "checks"}


def load_nepa_3d_graph_contract(
    path: Path = DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH,
) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_nepa_3d_graph_contract(contract: dict[str, Any]) -> list[dict[str, Any]]:
    export_scopes = set(_strings(contract.get("export_scopes")))
    node_types = _ids(contract.get("node_types"), "node_type")
    edge_types = _ids(contract.get("edge_types"), "edge_type")
    display_statuses = set(_strings(contract.get("display_status_values")))
    review_readiness_statuses = set(_strings(contract.get("review_readiness_status_values")))
    readiness_blocker_types = set(_strings(contract.get("readiness_blocker_types")))
    graph_shape = _dict(contract.get("graph_shape"))

    return [
        _check(
            "nepa_3d_graph_contract_schema_version",
            contract.get("schema_version") == NEPA_3D_GRAPH_CONTRACT_SCHEMA_VERSION,
            NEPA_3D_GRAPH_CONTRACT_SCHEMA_VERSION,
            contract.get("schema_version"),
        ),
        _check(
            "nepa_3d_graph_schema_version_declared",
            contract.get("graph_schema_version") == NEPA_3D_GRAPH_SCHEMA_VERSION,
            NEPA_3D_GRAPH_SCHEMA_VERSION,
            contract.get("graph_schema_version"),
        ),
        _check(
            "nepa_3d_graph_supports_source_set_and_review_scopes",
            REQUIRED_EXPORT_SCOPES <= export_scopes,
            sorted(REQUIRED_EXPORT_SCOPES),
            sorted(export_scopes),
        ),
        _check(
            "nepa_3d_graph_contract_names_required_node_types",
            REQUIRED_NODE_TYPES <= node_types,
            sorted(REQUIRED_NODE_TYPES),
            sorted(REQUIRED_NODE_TYPES - node_types),
        ),
        _check(
            "nepa_3d_graph_contract_names_required_edge_types",
            REQUIRED_EDGE_TYPES <= edge_types,
            sorted(REQUIRED_EDGE_TYPES),
            sorted(REQUIRED_EDGE_TYPES - edge_types),
        ),
        _check(
            "nepa_3d_graph_contract_names_required_display_states",
            REQUIRED_DISPLAY_STATUSES <= display_statuses,
            sorted(REQUIRED_DISPLAY_STATUSES),
            sorted(REQUIRED_DISPLAY_STATUSES - display_statuses),
        ),
        _check(
            "nepa_3d_graph_contract_names_review_readiness_states",
            REQUIRED_REVIEW_READINESS_STATUSES <= review_readiness_statuses,
            sorted(REQUIRED_REVIEW_READINESS_STATUSES),
            sorted(REQUIRED_REVIEW_READINESS_STATUSES - review_readiness_statuses),
        ),
        _check(
            "nepa_3d_graph_contract_names_readiness_blockers",
            REQUIRED_READINESS_BLOCKER_TYPES <= readiness_blocker_types,
            sorted(REQUIRED_READINESS_BLOCKER_TYPES),
            sorted(REQUIRED_READINESS_BLOCKER_TYPES - readiness_blocker_types),
        ),
        _check(
            "nepa_3d_graph_contract_defines_top_level_shape",
            REQUIRED_TOP_LEVEL_FIELDS <= set(_strings(graph_shape.get("required_top_level_fields"))),
            sorted(REQUIRED_TOP_LEVEL_FIELDS),
            sorted(
                REQUIRED_TOP_LEVEL_FIELDS
                - set(_strings(graph_shape.get("required_top_level_fields")))
            ),
        ),
        _check(
            "nepa_3d_graph_contract_defines_node_shape",
            REQUIRED_NODE_FIELDS <= set(_strings(graph_shape.get("required_node_fields"))),
            sorted(REQUIRED_NODE_FIELDS),
            sorted(REQUIRED_NODE_FIELDS - set(_strings(graph_shape.get("required_node_fields")))),
        ),
        _check(
            "nepa_3d_graph_contract_defines_edge_shape",
            REQUIRED_EDGE_FIELDS <= set(_strings(graph_shape.get("required_edge_fields"))),
            sorted(REQUIRED_EDGE_FIELDS),
            sorted(REQUIRED_EDGE_FIELDS - set(_strings(graph_shape.get("required_edge_fields")))),
        ),
        _check(
            "nepa_3d_graph_contract_defines_summary_shape",
            REQUIRED_SUMMARY_FIELDS <= set(_strings(graph_shape.get("required_summary_fields"))),
            sorted(REQUIRED_SUMMARY_FIELDS),
            sorted(
                REQUIRED_SUMMARY_FIELDS - set(_strings(graph_shape.get("required_summary_fields")))
            ),
        ),
        _check(
            "nepa_3d_graph_contract_defines_validation_shape",
            REQUIRED_VALIDATION_FIELDS
            <= set(_strings(graph_shape.get("required_validation_fields"))),
            sorted(REQUIRED_VALIDATION_FIELDS),
            sorted(
                REQUIRED_VALIDATION_FIELDS
                - set(_strings(graph_shape.get("required_validation_fields")))
            ),
        ),
    ]


def validate_nepa_3d_graph(
    graph: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    contract_checks = validate_nepa_3d_graph_contract(contract)
    graph_shape = _dict(contract.get("graph_shape"))
    node_types = _ids(contract.get("node_types"), "node_type")
    edge_types = _ids(contract.get("edge_types"), "edge_type")
    display_statuses = set(_strings(contract.get("display_status_values")))
    readiness_statuses = set(_strings(contract.get("review_readiness_status_values")))
    readiness_blocker_types = set(_strings(contract.get("readiness_blocker_types")))
    export_scopes = set(_strings(contract.get("export_scopes")))

    nodes = _dict_list(graph.get("nodes"))
    edges = _dict_list(graph.get("edges"))
    node_ids = {str(node.get("node_id")) for node in nodes if node.get("node_id")}
    export_scope = _dict(graph.get("export_scope"))
    scope_type = str(export_scope.get("scope_type") or "")

    top_level_missing = _missing(graph, graph_shape.get("required_top_level_fields"))
    invalid_node_types = sorted(
        {
            str(node.get("node_type") or "")
            for node in nodes
            if str(node.get("node_type") or "") not in node_types
        }
    )
    invalid_edge_types = sorted(
        {
            str(edge.get("edge_type") or "")
            for edge in edges
            if str(edge.get("edge_type") or "") not in edge_types
        }
    )
    invalid_display_statuses = sorted(
        {
            str(record.get("display_status") or "")
            for record in nodes + edges
            if str(record.get("display_status") or "") not in display_statuses
        }
    )
    invalid_readiness_statuses = sorted(
        {
            str(record.get("review_readiness_status") or "")
            for record in nodes + edges
            if str(record.get("review_readiness_status") or "") not in readiness_statuses
        }
    )
    unresolved_edge_endpoints = sorted(
        edge.get("edge_id")
        for edge in edges
        if edge.get("source_node_id") not in node_ids or edge.get("target_node_id") not in node_ids
    )
    invalid_readiness_blockers = sorted(
        {
            blocker
            for record in nodes + edges
            for blocker in _strings(record.get("readiness_blockers"))
            if blocker not in readiness_blocker_types
        }
    )

    return contract_checks + [
        _check(
            "nepa_3d_graph_top_level_shape",
            not top_level_missing,
            graph_shape.get("required_top_level_fields", []),
            top_level_missing,
        ),
        _check(
            "nepa_3d_graph_schema_version",
            graph.get("schema_version") == contract.get("graph_schema_version"),
            contract.get("graph_schema_version"),
            graph.get("schema_version"),
        ),
        _check(
            "nepa_3d_graph_export_scope_supported",
            scope_type in export_scopes,
            sorted(export_scopes),
            scope_type,
        ),
        _check(
            "nepa_3d_graph_review_scope_has_review_id",
            scope_type != "review" or bool(export_scope.get("review_id")),
            "review scope requires review_id",
            export_scope,
        ),
        _check(
            "nepa_3d_graph_nodes_have_required_fields",
            _records_have_fields(nodes, graph_shape.get("required_node_fields")),
            graph_shape.get("required_node_fields", []),
            _records_missing_fields(nodes, graph_shape.get("required_node_fields"), "node_id"),
        ),
        _check(
            "nepa_3d_graph_edges_have_required_fields",
            _records_have_fields(edges, graph_shape.get("required_edge_fields")),
            graph_shape.get("required_edge_fields", []),
            _records_missing_fields(edges, graph_shape.get("required_edge_fields"), "edge_id"),
        ),
        _check(
            "nepa_3d_graph_uses_known_node_types",
            not invalid_node_types,
            sorted(node_types),
            invalid_node_types,
        ),
        _check(
            "nepa_3d_graph_uses_known_edge_types",
            not invalid_edge_types,
            sorted(edge_types),
            invalid_edge_types,
        ),
        _check(
            "nepa_3d_graph_uses_known_display_statuses",
            not invalid_display_statuses,
            sorted(display_statuses),
            invalid_display_statuses,
        ),
        _check(
            "nepa_3d_graph_uses_known_review_readiness_statuses",
            not invalid_readiness_statuses,
            sorted(readiness_statuses),
            invalid_readiness_statuses,
        ),
        _check(
            "nepa_3d_graph_edges_resolve_to_nodes",
            not unresolved_edge_endpoints,
            [],
            unresolved_edge_endpoints,
        ),
        _check(
            "nepa_3d_graph_uses_known_readiness_blockers",
            not invalid_readiness_blockers,
            sorted(readiness_blocker_types),
            invalid_readiness_blockers,
        ),
        _summary_check(graph, nodes=nodes, edges=edges),
        _check(
            "nepa_3d_graph_validation_block_shape",
            not _missing(_dict(graph.get("validation")), graph_shape.get("required_validation_fields")),
            graph_shape.get("required_validation_fields", []),
            _missing(_dict(graph.get("validation")), graph_shape.get("required_validation_fields")),
        ),
    ]


def _summary_check(graph: dict[str, Any], *, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    summary = _dict(graph.get("summary"))
    expected = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(Counter(str(node.get("node_type")) for node in nodes)),
        "edge_type_counts": dict(Counter(str(edge.get("edge_type")) for edge in edges)),
        "display_status_counts": dict(
            Counter(str(record.get("display_status")) for record in nodes + edges)
        ),
        "review_readiness_status_counts": dict(
            Counter(str(record.get("review_readiness_status")) for record in nodes + edges)
        ),
        "readiness_blocker_counts": dict(
            Counter(
                blocker
                for record in nodes + edges
                for blocker in _strings(record.get("readiness_blockers"))
            )
        ),
    }
    actual = {key: summary.get(key) for key in expected}
    return _check("nepa_3d_graph_summary_matches_records", actual == expected, expected, actual)


def _ids(value: object, key: str) -> set[str]:
    return {str(item.get(key)) for item in _dict_list(value) if item.get(key)}


def _missing(record: dict[str, Any], required_fields: object) -> list[str]:
    return sorted(field for field in _strings(required_fields) if field not in record)


def _records_have_fields(records: list[dict], required_fields: object) -> bool:
    required = _strings(required_fields)
    return all(all(field in record for field in required) for record in records)


def _records_missing_fields(
    records: list[dict],
    required_fields: object,
    id_field: str,
) -> list[dict[str, Any]]:
    required = _strings(required_fields)
    return [
        {"record_id": record.get(id_field), "missing": _missing(record, required)}
        for record in records
        if _missing(record, required)
    ]


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _check(name: str, passed: bool, expected: object, actual: object) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }
