from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from .nepa_3d_graph_contract_common import _check
from .nepa_3d_graph_contract_common import _dict
from .nepa_3d_graph_contract_common import _dict_list
from .nepa_3d_graph_contract_common import _edge_endpoint_rules
from .nepa_3d_graph_contract_common import _edge_endpoint_type_violations
from .nepa_3d_graph_contract_common import _ids
from .nepa_3d_graph_contract_common import _missing
from .nepa_3d_graph_contract_common import _node_provenance_requirements
from .nepa_3d_graph_contract_common import _readiness_semantic_gaps
from .nepa_3d_graph_contract_common import _records_have_fields
from .nepa_3d_graph_contract_common import _records_missing_fields
from .nepa_3d_graph_contract_common import _records_missing_provenance
from .nepa_3d_graph_contract_common import _strings
from .nepa_3d_graph_contract_common import _summary_check
from .nepa_3d_graph_contract_models import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH
from .nepa_3d_graph_contract_models import NEPA_3D_GRAPH_CONTRACT_SCHEMA_VERSION
from .nepa_3d_graph_contract_models import NEPA_3D_GRAPH_SCHEMA_VERSION
from .nepa_3d_graph_contract_models import REQUIRED_DISPLAY_STATUSES
from .nepa_3d_graph_contract_models import REQUIRED_EDGE_FIELDS
from .nepa_3d_graph_contract_models import REQUIRED_EDGE_TYPES
from .nepa_3d_graph_contract_models import REQUIRED_EXPORT_SCOPES
from .nepa_3d_graph_contract_models import REQUIRED_LENSES
from .nepa_3d_graph_contract_models import REQUIRED_LENS_FIELDS
from .nepa_3d_graph_contract_models import REQUIRED_NODE_FIELDS
from .nepa_3d_graph_contract_models import REQUIRED_NODE_TYPES
from .nepa_3d_graph_contract_models import REQUIRED_READINESS_BLOCKER_TYPES
from .nepa_3d_graph_contract_models import REQUIRED_READINESS_SEMANTIC_CLASSES
from .nepa_3d_graph_contract_models import REQUIRED_REVIEW_READINESS_STATUSES
from .nepa_3d_graph_contract_models import REQUIRED_SUMMARY_FIELDS
from .nepa_3d_graph_contract_models import REQUIRED_TOP_LEVEL_FIELDS
from .nepa_3d_graph_contract_models import REQUIRED_VALIDATION_FIELDS


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
    readiness_semantic_classes = set(_strings(contract.get("readiness_semantic_classes")))
    graph_shape = _dict(contract.get("graph_shape"))
    lens_contract = _dict(contract.get("lens_metadata_contract"))
    node_provenance_requirements = _node_provenance_requirements(contract)
    missing_node_provenance_requirements = sorted(
        node_type
        for node_type in REQUIRED_NODE_TYPES
        if not node_provenance_requirements.get(node_type)
    )
    edge_endpoint_rules = _edge_endpoint_rules(contract)
    missing_edge_endpoint_rules = sorted(
        edge_type
        for edge_type in REQUIRED_EDGE_TYPES
        if not edge_endpoint_rules.get(edge_type, {}).get("source_node_types")
        or not edge_endpoint_rules.get(edge_type, {}).get("target_node_types")
    )
    lens_required_fields = set(_strings(lens_contract.get("required_fields")))
    lens_required_lenses = set(_strings(lens_contract.get("required_lenses")))

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
            "nepa_3d_graph_contract_defines_node_provenance",
            not missing_node_provenance_requirements,
            sorted(REQUIRED_NODE_TYPES),
            missing_node_provenance_requirements,
        ),
        _check(
            "nepa_3d_graph_contract_names_required_edge_types",
            REQUIRED_EDGE_TYPES <= edge_types,
            sorted(REQUIRED_EDGE_TYPES),
            sorted(REQUIRED_EDGE_TYPES - edge_types),
        ),
        _check(
            "nepa_3d_graph_contract_defines_edge_endpoint_types",
            not missing_edge_endpoint_rules,
            sorted(REQUIRED_EDGE_TYPES),
            missing_edge_endpoint_rules,
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
            "nepa_3d_graph_contract_names_readiness_semantic_classes",
            REQUIRED_READINESS_SEMANTIC_CLASSES <= readiness_semantic_classes,
            sorted(REQUIRED_READINESS_SEMANTIC_CLASSES),
            sorted(REQUIRED_READINESS_SEMANTIC_CLASSES - readiness_semantic_classes),
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
        _check(
            "nepa_3d_graph_contract_defines_lens_metadata_shape",
            REQUIRED_LENS_FIELDS <= lens_required_fields,
            sorted(REQUIRED_LENS_FIELDS),
            sorted(REQUIRED_LENS_FIELDS - lens_required_fields),
        ),
        _check(
            "nepa_3d_graph_contract_defines_required_lenses",
            REQUIRED_LENSES <= lens_required_lenses,
            sorted(REQUIRED_LENSES),
            sorted(REQUIRED_LENSES - lens_required_lenses),
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
    readiness_semantic_classes = set(_strings(contract.get("readiness_semantic_classes")))
    export_scopes = set(_strings(contract.get("export_scopes")))
    node_provenance_requirements = _node_provenance_requirements(contract)
    edge_endpoint_rules = _edge_endpoint_rules(contract)
    lens_contract = _dict(contract.get("lens_metadata_contract"))

    nodes = _dict_list(graph.get("nodes"))
    edges = _dict_list(graph.get("edges"))
    node_by_id = {str(node.get("node_id")): node for node in nodes if node.get("node_id")}
    node_ids = set(node_by_id)
    export_scope = _dict(graph.get("export_scope"))
    scope_type = str(export_scope.get("scope_type") or "")
    lens_metadata = _dict_list(graph.get("lens_metadata"))

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
    invalid_readiness_semantic_classes = sorted(
        {
            str(record.get("readiness_semantic_class") or "")
            for record in nodes + edges
            if str(record.get("readiness_semantic_class") or "") not in readiness_semantic_classes
        }
    )
    node_provenance_gaps = _records_missing_provenance(nodes, node_provenance_requirements)
    edge_endpoint_type_violations = _edge_endpoint_type_violations(
        edges,
        node_by_id,
        edge_endpoint_rules,
    )
    readiness_semantic_gaps = _readiness_semantic_gaps(nodes=nodes, edges=edges, node_by_id=node_by_id)
    lens_required_fields = _strings(lens_contract.get("required_fields"))
    lens_missing_fields = _records_missing_fields(lens_metadata, lens_required_fields, "lens_id")
    required_lenses = set(_strings(lens_contract.get("required_lenses")))
    actual_lenses = {str(lens.get("lens_id")) for lens in lens_metadata if lens.get("lens_id")}
    missing_lenses = sorted(required_lenses - actual_lenses)
    invalid_lens_metadata_values = {
        "supported_node_types": sorted(
            {
                value
                for lens in lens_metadata
                for value in _strings(lens.get("supported_node_types"))
                if value not in node_types
            }
        ),
        "supported_edge_types": sorted(
            {
                value
                for lens in lens_metadata
                for value in _strings(lens.get("supported_edge_types"))
                if value not in edge_types
            }
        ),
        "display_status_values": sorted(
            {
                value
                for lens in lens_metadata
                for value in _strings(lens.get("display_status_values"))
                if value not in display_statuses
            }
        ),
    }

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
        _check(
            "nepa_3d_graph_uses_known_readiness_semantic_classes",
            not invalid_readiness_semantic_classes,
            sorted(readiness_semantic_classes),
            invalid_readiness_semantic_classes,
        ),
        _check(
            "nepa_3d_graph_nodes_have_required_provenance",
            not node_provenance_gaps,
            "node-type required_provenance_fields from contract",
            node_provenance_gaps,
        ),
        _check(
            "nepa_3d_graph_explicitly_classifies_red_semantics",
            not readiness_semantic_gaps,
            "red nodes and edges must carry the contract semantic class",
            readiness_semantic_gaps,
        ),
        _check(
            "nepa_3d_graph_edges_match_declared_endpoint_types",
            not edge_endpoint_type_violations,
            "edge-type source_node_types and target_node_types from contract",
            edge_endpoint_type_violations,
        ),
        _check(
            "nepa_3d_graph_lens_metadata_shape",
            not lens_missing_fields,
            lens_required_fields,
            lens_missing_fields,
        ),
        _check(
            "nepa_3d_graph_lens_metadata_required_lenses_present",
            not missing_lenses,
            sorted(required_lenses),
            missing_lenses,
        ),
        _check(
            "nepa_3d_graph_lens_metadata_uses_known_values",
            not any(invalid_lens_metadata_values.values()),
            "known node, edge, and display-status values from contract",
            invalid_lens_metadata_values,
        ),
        _summary_check(graph, nodes=nodes, edges=edges),
        _check(
            "nepa_3d_graph_validation_block_shape",
            not _missing(_dict(graph.get("validation")), graph_shape.get("required_validation_fields")),
            graph_shape.get("required_validation_fields", []),
            _missing(_dict(graph.get("validation")), graph_shape.get("required_validation_fields")),
        ),
    ]
