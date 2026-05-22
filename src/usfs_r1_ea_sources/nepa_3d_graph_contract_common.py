from __future__ import annotations

from collections import Counter
from typing import Any


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


def _node_provenance_requirements(contract: dict[str, Any]) -> dict[str, set[str]]:
    requirements: dict[str, set[str]] = {}
    for entry in _dict_list(contract.get("node_types")):
        node_type = str(entry.get("node_type") or "")
        if node_type:
            requirements[node_type] = set(_strings(entry.get("required_provenance_fields")))
    return requirements


def _edge_endpoint_rules(contract: dict[str, Any]) -> dict[str, dict[str, set[str]]]:
    rules: dict[str, dict[str, set[str]]] = {}
    for entry in _dict_list(contract.get("edge_types")):
        edge_type = str(entry.get("edge_type") or "")
        if edge_type:
            rules[edge_type] = {
                "source_node_types": set(_strings(entry.get("source_node_types"))),
                "target_node_types": set(_strings(entry.get("target_node_types"))),
            }
    return rules


def _records_missing_provenance(
    nodes: list[dict],
    requirements: dict[str, set[str]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for node in nodes:
        node_type = str(node.get("node_type") or "")
        required_fields = requirements.get(node_type, set())
        if not required_fields:
            continue
        provenance = _dict(node.get("provenance"))
        missing = sorted(
            field for field in required_fields if _is_missing_value(provenance.get(field))
        )
        if missing:
            gaps.append(
                {
                    "node_id": node.get("node_id"),
                    "node_type": node_type,
                    "missing": missing,
                }
            )
    return gaps


def _edge_endpoint_type_violations(
    edges: list[dict],
    node_by_id: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, set[str]]],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for edge in edges:
        edge_type = str(edge.get("edge_type") or "")
        rule = rules.get(edge_type)
        if not rule:
            continue
        source_node = node_by_id.get(str(edge.get("source_node_id") or ""))
        target_node = node_by_id.get(str(edge.get("target_node_id") or ""))
        if not source_node or not target_node:
            continue
        source_type = str(source_node.get("node_type") or "")
        target_type = str(target_node.get("node_type") or "")
        source_types = rule.get("source_node_types", set())
        target_types = rule.get("target_node_types", set())
        if source_type not in source_types or target_type not in target_types:
            violations.append(
                {
                    "edge_id": edge.get("edge_id"),
                    "edge_type": edge_type,
                    "source_node_type": source_type,
                    "expected_source_node_types": sorted(source_types),
                    "target_node_type": target_type,
                    "expected_target_node_types": sorted(target_types),
                }
            )
    return sorted(violations, key=lambda item: str(item.get("edge_id") or ""))


def _readiness_semantic_gaps(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for node in nodes:
        expected = _expected_node_readiness_semantic_class(node)
        actual = str(node.get("readiness_semantic_class") or "")
        if actual != expected:
            gaps.append(
                {
                    "record_kind": "node",
                    "record_id": node.get("node_id"),
                    "expected": expected,
                    "actual": actual,
                }
            )
    for edge in edges:
        target_node = node_by_id.get(str(edge.get("target_node_id") or ""))
        expected = _expected_edge_readiness_semantic_class(edge, target_node)
        actual = str(edge.get("readiness_semantic_class") or "")
        if actual != expected:
            gaps.append(
                {
                    "record_kind": "edge",
                    "record_id": edge.get("edge_id"),
                    "expected": expected,
                    "actual": actual,
                }
            )
    return gaps


def _expected_node_readiness_semantic_class(node: dict[str, Any]) -> str:
    if str(node.get("node_type") or "") == "readiness_blocker":
        return "synthetic_blocker_node"
    if str(node.get("display_status") or "") == "readiness_blocked":
        return "blocked_domain_node"
    return "none"


def _expected_edge_readiness_semantic_class(
    edge: dict[str, Any],
    target_node: dict[str, Any] | None,
) -> str:
    if str(_dict(target_node).get("node_type") or "") == "readiness_blocker":
        return "blocker_relationship_edge"
    if str(edge.get("display_status") or "") == "readiness_blocked":
        return "blocked_relationship_edge"
    return "none"


def _is_missing_value(value: object) -> bool:
    return value is None or value == "" or value == [] or value == {}


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
