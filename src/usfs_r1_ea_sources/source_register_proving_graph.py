from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path
import re

from .records import slugify


def _build_graph_summary(
    *,
    manifest: dict,
    selected_rows: list,
    selected_queue_rows: list[dict],
    catalog_by_source_record_id: dict[str, dict],
    relationships: list[dict],
    alias_report: dict,
    source_set_id: str,
) -> dict:
    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}
    source_set_node_id = f"source_set:{source_set_id}"
    nodes[source_set_node_id] = {
        "node_id": source_set_node_id,
        "class_id": "source_set",
        "label": source_set_id,
    }
    justification_paths = []
    authority_paths = []

    for row in selected_rows:
        catalog_row = catalog_by_source_record_id[row.source_record_id]
        source_record_node_id = f"source_record:{row.source_record_id}"
        nodes[source_record_node_id] = {
            "node_id": source_record_node_id,
            "class_id": "source_record",
            "label": row.title,
            "source_record_id": row.source_record_id,
        }
        _add_edge(edges, source_set_node_id, source_record_node_id, "IN_SOURCE_SET")
        authority_node_id = row.authority_document_id
        nodes.setdefault(
            authority_node_id,
            {
                "node_id": authority_node_id,
                "class_id": row.authority_document_class_id,
                "label": row.title,
            },
        )
        _add_edge(edges, source_record_node_id, authority_node_id, "CAPTURES_AUTHORITY")
        if row.authority_section_id:
            nodes.setdefault(
                row.authority_section_id,
                {
                    "node_id": row.authority_section_id,
                    "class_id": "authority_section",
                    "label": row.authority_section_id,
                },
            )
            _add_edge(edges, authority_node_id, row.authority_section_id, "HAS_SECTION")
        nodes.setdefault(
            row.jurisdiction_scope_id,
            {
                "node_id": row.jurisdiction_scope_id,
                "class_id": "jurisdiction_scope",
                "label": row.jurisdiction_scope_id,
            },
        )
        _add_edge(edges, authority_node_id, row.jurisdiction_scope_id, "APPLIES_WITHIN_SCOPE")
        artifact_sha256 = str(catalog_row.get("artifact_sha256") or "")
        artifact_node_id = f"source_artifact:{artifact_sha256}"
        nodes[artifact_node_id] = {
            "node_id": artifact_node_id,
            "class_id": "source_artifact",
            "label": artifact_sha256[:12],
            "artifact_sha256": artifact_sha256,
        }
        _add_edge(edges, source_record_node_id, artifact_node_id, "HAS_ARTIFACT")
        evidence_span_node_id = f"evidence_span:{row.source_record_id}:0"
        nodes[evidence_span_node_id] = {
            "node_id": evidence_span_node_id,
            "class_id": "evidence_span",
            "label": f"{row.source_record_id} proving evidence span",
            "source_record_id": row.source_record_id,
        }
        _add_edge(edges, artifact_node_id, evidence_span_node_id, "HAS_EVIDENCE_SPAN")
        if row.authority_document_class_id == "forest_plan" and row.jurisdiction_or_unit:
            forest_unit_id = _forest_unit_id(row.jurisdiction_or_unit)
            nodes.setdefault(
                forest_unit_id,
                {
                    "node_id": forest_unit_id,
                    "class_id": "forest_unit",
                    "label": row.jurisdiction_or_unit,
                },
            )
            _add_edge(edges, authority_node_id, forest_unit_id, "GOVERNS_FOREST_UNIT")

    for relationship in relationships:
        _add_edge(
            edges,
            relationship["source_id"],
            relationship["target_id"],
            relationship["relationship_type"],
        )
        authority_path_id = f"authority_path:{relationship['relationship_id']}"
        justification_path_id = f"justification_path:{relationship['relationship_id']}"
        nodes[authority_path_id] = {
            "node_id": authority_path_id,
            "class_id": "authority_path",
            "label": relationship["relationship_id"],
            "path_pattern_id": relationship["path_pattern_id"],
        }
        nodes[justification_path_id] = {
            "node_id": justification_path_id,
            "class_id": "justification_path",
            "label": relationship["relationship_id"],
        }
        _add_edge(edges, authority_path_id, relationship["source_id"], "PATH_SOURCE")
        _add_edge(edges, authority_path_id, relationship["target_id"], "PATH_TARGET")
        _add_edge(
            edges,
            justification_path_id,
            authority_path_id,
            "JUSTIFIES_AUTHORITY_PATH",
        )
        supporting_source_record_id = relationship["supporting_source_record_ids"][0]
        catalog_row = catalog_by_source_record_id[supporting_source_record_id]
        artifact_sha256 = str(catalog_row.get("artifact_sha256") or "")
        artifact_node_id = f"source_artifact:{artifact_sha256}"
        evidence_span_node_id = f"evidence_span:{supporting_source_record_id}:0"
        source_record_node_id = f"source_record:{supporting_source_record_id}"
        _add_edge(
            edges,
            justification_path_id,
            source_record_node_id,
            "HAS_SOURCE_RECORD",
        )
        _add_edge(
            edges,
            justification_path_id,
            artifact_node_id,
            "HAS_SOURCE_ARTIFACT",
        )
        _add_edge(
            edges,
            justification_path_id,
            evidence_span_node_id,
            "HAS_EVIDENCE_SPAN",
        )
        authority_paths.append(
            {
                "authority_path_id": authority_path_id,
                "relationship_id": relationship["relationship_id"],
                "path_pattern_id": relationship["path_pattern_id"],
                "source_id": relationship["source_id"],
                "target_id": relationship["target_id"],
            }
        )
        justification_paths.append(
            {
                "justification_path_id": justification_path_id,
                "authority_path_id": authority_path_id,
                "relationship_id": relationship["relationship_id"],
                "source_record_id": supporting_source_record_id,
                "artifact_sha256": artifact_sha256,
                "evidence_span_id": evidence_span_node_id,
                "conclusion": "source-register-proving-slice",
            }
        )

    orphan_node_ids = _orphan_node_ids(nodes=list(nodes.values()), edges=list(edges.values()))
    disconnected_components = _disconnected_components(
        nodes=list(nodes.values()),
        edges=list(edges.values()),
    )
    relationship_type_counts = Counter(
        relationship["relationship_type"] for relationship in relationships
    )
    lens_metadata = [
        {
            "lens_id": "source-provenance",
            "node_class_ids": ["source_record", "source_artifact", "evidence_span"],
            "edge_types": [
                "IN_SOURCE_SET",
                "HAS_ARTIFACT",
                "HAS_EVIDENCE_SPAN",
                "HAS_SOURCE_RECORD",
                "HAS_SOURCE_ARTIFACT",
            ],
        },
        {
            "lens_id": "authority-currentness",
            "node_class_ids": ["authority_document", "forest_plan", "jurisdiction_scope"],
            "edge_types": ["APPLIES_WITHIN_SCOPE", "SUPERSEDES"],
        },
        {
            "lens_id": "forest-plan-lineage",
            "node_class_ids": ["forest_plan", "forest_unit", "authority_path"],
            "edge_types": [
                "REQUIRES_CONSISTENCY_WITH",
                "GOVERNS_FOREST_UNIT",
                "PATH_SOURCE",
                "PATH_TARGET",
            ],
        },
        {
            "lens_id": "package-applicability",
            "node_class_ids": ["jurisdiction_scope", "authority_document", "forest_plan"],
            "edge_types": ["APPLIES_WITHIN_SCOPE"],
        },
        {
            "lens_id": "evidence-path",
            "node_class_ids": [
                "authority_path",
                "justification_path",
                "source_artifact",
                "evidence_span",
            ],
            "edge_types": [
                "JUSTIFIES_AUTHORITY_PATH",
                "HAS_SOURCE_RECORD",
                "HAS_SOURCE_ARTIFACT",
                "HAS_EVIDENCE_SPAN",
            ],
        },
        {
            "lens_id": "readiness-blockers",
            "queue_source_record_ids": [row["Source_ID"] for row in selected_queue_rows],
            "blocked_alias_row_ids": [
                row["source_record_id"]
                for row in alias_report["rows"]
                if row["blocked_alias_terms"]
            ],
            "edge_types": [],
            "node_class_ids": [],
        },
    ]
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "relationship_type_counts": dict(relationship_type_counts),
        "node_class_counts": dict(
            Counter(node["class_id"] for node in nodes.values())
        ),
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "authority_paths": authority_paths,
        "justification_paths": justification_paths,
        "orphan_node_ids": orphan_node_ids,
        "disconnected_components": disconnected_components,
        "lens_metadata": lens_metadata,
    }


def _validation_checks(
    *,
    manifest: dict,
    selected_rows: list,
    selected_queue_rows: list[dict],
    alias_report: dict,
    relationships: list[dict],
    graph: dict,
    preflight_result: dict,
    catalog_result: dict,
    download_manifest_path: Path,
) -> list[dict]:
    coverage_checks = []
    rows_by_id = {row.source_record_id: row for row in selected_rows}
    queue_by_id = {str(row["Source_ID"]).strip(): row for row in selected_queue_rows}
    for group in manifest.get("coverage_groups", []):
        group_id = str(group["coverage_id"])
        selected_ids = [str(source_record_id) for source_record_id in group["source_record_ids"]]
        if group.get("row_state") == "queue":
            entries = [queue_by_id[source_record_id] for source_record_id in selected_ids]
            actual_value = sorted({str(entry.get("URL_Class") or "") for entry in entries})
            expected_value = sorted(group.get("expected_url_classes", []))
            passed = set(expected_value).issubset(set(actual_value))
        else:
            entries = [rows_by_id[source_record_id] for source_record_id in selected_ids]
            expected_parser_classes = set(group.get("expected_parser_admission_classes", []))
            actual_parser_classes = {entry.parser_admission_class for entry in entries}
            expected_parsers = set(group.get("expected_expected_parsers", []))
            actual_parsers = {entry.expected_parser for entry in entries}
            expected_tiers = set(group.get("expected_authority_tiers", []))
            actual_tiers = {entry.authority_tier for entry in entries}
            passed = (
                (not expected_parser_classes or expected_parser_classes.issubset(actual_parser_classes))
                and (not expected_parsers or expected_parsers.issubset(actual_parsers))
                and (not expected_tiers or expected_tiers.issubset(actual_tiers))
            )
            actual_value = {
                "authority_tiers": sorted(actual_tiers),
                "expected_parsers": sorted(actual_parsers),
                "parser_admission_classes": sorted(actual_parser_classes),
            }
            expected_value = {
                "authority_tiers": sorted(expected_tiers),
                "expected_parsers": sorted(expected_parsers),
                "parser_admission_classes": sorted(expected_parser_classes),
            }
        coverage_checks.append(
            _check(
                f"coverage_group_{group_id}",
                passed,
                expected_value,
                actual_value,
            )
        )
    expected_alias_rows = {
        str(entry["source_record_id"]) for entry in manifest.get("alias_expectations", [])
    }
    resolved_alias_rows = {
        row["source_record_id"]
        for row in alias_report["expected_rows"]
        if row["resolved_with_context"]
    }
    return [
        _check(
            "load_ready_slice_has_expected_row_count",
            24 <= len(selected_rows) <= 40,
            "24-40",
            len(selected_rows),
        ),
        _check(
            "queue_slice_has_expected_rows",
            bool(selected_queue_rows),
            True,
            bool(selected_queue_rows),
        ),
        *coverage_checks,
        _check(
            "alias_stress_rows_resolve_with_context",
            expected_alias_rows == resolved_alias_rows,
            sorted(expected_alias_rows),
            sorted(resolved_alias_rows),
        ),
        _check(
            "identity_keys_do_not_collide",
            alias_report["identity_collision_count"] == 0,
            0,
            alias_report["identity_collision_count"],
        ),
        _check(
            "relationship_expectations_materialized",
            len(relationships) == len(manifest.get("relationship_expectations", [])),
            len(manifest.get("relationship_expectations", [])),
            len(relationships),
        ),
        _check(
            "preflight_contract_passed",
            bool(preflight_result.get("validation_passed")),
            True,
            preflight_result.get("validation_passed"),
        ),
        _check(
            "synthetic_download_manifest_written",
            download_manifest_path.exists(),
            True,
            download_manifest_path.exists(),
        ),
        _check(
            "catalog_validation_passed",
            bool(catalog_result.get("validation_passed")),
            True,
            catalog_result.get("validation_passed"),
        ),
        _check(
            "graph_has_no_orphans",
            not graph["orphan_node_ids"],
            [],
            graph["orphan_node_ids"],
        ),
        _check(
            "graph_has_single_connected_component",
            len(graph["disconnected_components"]) == 1,
            1,
            len(graph["disconnected_components"]),
        ),
    ]


def _forest_unit_id(value: str) -> str:
    return f"forest_unit:{slugify(value, max_length=96)}"


def _orphan_node_ids(*, nodes: list[dict], edges: list[dict]) -> list[str]:
    connected_node_ids = set()
    for edge in edges:
        connected_node_ids.add(str(edge["source"]))
        connected_node_ids.add(str(edge["target"]))
    return sorted(
        str(node["node_id"])
        for node in nodes
        if str(node["node_id"]) not in connected_node_ids
    )


def _disconnected_components(*, nodes: list[dict], edges: list[dict]) -> list[list[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        adjacency[str(node["node_id"])]
    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        adjacency[source].add(target)
        adjacency[target].add(source)
    visited: set[str] = set()
    components: list[list[str]] = []
    for node_id in sorted(adjacency):
        if node_id in visited:
            continue
        component = []
        queue = deque([node_id])
        visited.add(node_id)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)
        components.append(sorted(component))
    return components


def _add_edge(edges: dict[str, dict], source: str, target: str, relationship: str) -> None:
    edge_id = f"{source}|{relationship}|{target}"
    edges.setdefault(
        edge_id,
        {
            "edge_id": edge_id,
            "source": source,
            "target": target,
            "relationship": relationship,
        },
    )


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }


def _normalize_identity_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
