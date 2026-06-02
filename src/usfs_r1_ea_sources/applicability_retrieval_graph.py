from __future__ import annotations

from collections import defaultdict, deque
import json
from typing import Any

from .applicability_retrieval_runtime import _package_node_matches_candidate
from .applicability_retrieval_runtime import _stable_id
from .applicability_retrieval_runtime import _strings


APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION = "applicability-graph-trace-v0"


def _graph_trace_rows_for_candidate(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    retrieval_trace_rows: list[dict[str, Any]],
    package_fact_graph: dict[str, Any],
    package_graph_identity: dict[str, Any],
    evidence_graph_identity: dict[str, Any],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    external_graph_index: dict[str, Any] | None,
    rule_claim_links: list[dict[str, Any]],
    source_claims: list[dict[str, Any]],
    package_match_cache: dict[tuple, list[dict[str, Any]]],
    max_graph_paths_per_candidate: int,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    contract = candidate.get("graph_expansion_contract")
    if not isinstance(contract, dict):
        contract = {}
    allowed_relationships = set(_strings(contract.get("relationship_types")))
    max_depth = int(contract.get("max_depth") or 1)
    trace_graph = _candidate_trace_graph(
        candidate=candidate,
        package_fact_graph=package_fact_graph,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        external_graph_index=external_graph_index,
        rule_claim_links=rule_claim_links,
        source_claims=source_claims,
        retrieval_trace_rows=retrieval_trace_rows,
        package_match_cache=package_match_cache,
        allowed_relationships=allowed_relationships,
    )
    paths = _bounded_paths(
        start_node_id=f"candidate:{candidate_id}",
        adjacency=trace_graph["adjacency"],
        max_depth=max_depth,
        allowed_relationships=allowed_relationships,
        max_path_count=max_graph_paths_per_candidate + 1,
    )
    diagnostics = []
    if not paths:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "graph_dead_end",
                "severity": "warning",
                "message": "No graph paths were discovered within the declared graph contract.",
            }
        )
        return [
            _graph_dead_end_row(
                applicability_run_id=applicability_run_id,
                review_id=review_id,
                source_set_id=source_set_id,
                candidate=candidate,
                package_graph_identity=package_graph_identity,
                evidence_graph_identity=evidence_graph_identity,
                created_at=created_at,
            )
        ], diagnostics

    selected_paths = paths[:max_graph_paths_per_candidate]
    if len(paths) > max_graph_paths_per_candidate:
        diagnostics.append(
            {
                "candidate_authority_id": candidate_id,
                "diagnostic_type": "excessive_graph_fan_out",
                "severity": "warning",
                "message": (
                    "Graph expansion produced more paths than the configured trace limit."
                ),
                "path_count": len(paths),
                "path_count_is_lower_bound": True,
                "max_graph_paths_per_candidate": max_graph_paths_per_candidate,
            }
        )
    rows = []
    for index, path in enumerate(selected_paths, start=1):
        path_id = _stable_id("graph-path", applicability_run_id, candidate_id, str(index), *path)
        relationship_types = _path_relationship_types(path)
        rows.append(
            {
                "schema_version": APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION,
                "applicability_run_id": applicability_run_id,
                "review_id": review_id,
                "source_set_id": source_set_id,
                "candidate_authority_id": candidate_id,
                "candidate_authority_type": candidate.get("candidate_authority_type"),
                "graph_path_id": path_id,
                "query_timestamp": created_at,
                "graph_artifacts": [package_graph_identity, evidence_graph_identity],
                "graph_build_id": evidence_graph_identity.get("graph_build_id"),
                "graph_artifact_path": evidence_graph_identity.get("graph_artifact_path"),
                "graph_artifact_hash": evidence_graph_identity.get("graph_artifact_hash"),
                "start_node_id": path[0],
                "end_node_id": path[-1],
                "traversed_node_ids": _path_node_ids(path),
                "relationship_types": relationship_types,
                "traversal_depth": len(relationship_types),
                "max_depth": max_depth,
                "path_rationale": _path_rationale(path, trace_graph["nodes"]),
                "selected_status": "selected",
                "rejection_reason": None,
                "evidence_references": _path_evidence_references(path, trace_graph["nodes"]),
                "bounded_by_contract": {
                    "allowed_relationship_types": sorted(allowed_relationships),
                    "max_depth": max_depth,
                },
            }
        )
    return rows, diagnostics


def _candidate_trace_graph(
    *,
    candidate: dict[str, Any],
    package_fact_graph: dict[str, Any],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    rule_claim_links: list[dict[str, Any]],
    source_claims: list[dict[str, Any]],
    retrieval_trace_rows: list[dict[str, Any]],
    allowed_relationships: set[str],
    package_match_cache: dict[tuple, list[dict[str, Any]]] | None = None,
    external_graph_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    start_node_id = f"candidate:{candidate_id}"
    nodes: dict[str, dict[str, Any]] = {
        start_node_id: {
            "node_id": start_node_id,
            "node_type": str(candidate.get("candidate_authority_type") or "candidate"),
            "candidate_authority_id": candidate_id,
        }
    }
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add_node(node_id: str, **metadata: Any) -> None:
        nodes.setdefault(node_id, {"node_id": node_id, **metadata})

    def add_edge(source: str, relationship: str, target: str) -> None:
        if relationship in allowed_relationships:
            adjacency[source].append((relationship, target))

    authority_category = str(candidate.get("authority_category") or "").strip()
    if authority_category:
        node_id = f"authority-category:{authority_category}"
        add_node(node_id, node_type="authority_category", authority_category=authority_category)
        add_edge(start_node_id, "authority_category", node_id)

    for source_record_id in _strings(candidate.get("source_record_ids")):
        node_id = f"source-record:{source_record_id}"
        add_node(node_id, node_type="source_record", source_record_id=source_record_id)
        add_edge(start_node_id, "source_record", node_id)
        if authority_category:
            add_edge(f"authority-category:{authority_category}", "source_record", node_id)

    for result in _selected_results(retrieval_trace_rows):
        if result.get("source_chunk_id"):
            node_id = f"source-chunk:{result['source_chunk_id']}"
            add_node(
                node_id,
                node_type="source_chunk",
                source_record_id=result.get("source_record_id"),
                retrieval_result_id=result.get("result_id"),
                retrieval_trace_ids=result.get("input_trace_ids") or [],
            )
            for source_record_id in _strings([result.get("source_record_id")]):
                source_record_node = f"source-record:{source_record_id}"
                add_node(
                    source_record_node,
                    node_type="source_record",
                    source_record_id=source_record_id,
                )
                add_edge(source_record_node, "source_chunk", node_id)
        if result.get("package_fact_node_id"):
            node_id = f"package-fact:{result['package_fact_node_id']}"
            add_node(
                node_id,
                node_type="package_fact",
                package_fact_node_id=result.get("package_fact_node_id"),
                package_chunk_id=result.get("package_chunk_id"),
                retrieval_result_id=result.get("result_id"),
                retrieval_trace_ids=result.get("input_trace_ids") or [],
            )
            add_edge(start_node_id, "package_fact", node_id)

    for node in _matching_package_nodes(
        package_fact_graph=package_fact_graph,
        candidate=candidate,
        package_match_cache=package_match_cache if package_match_cache is not None else {},
    ):
        node_id = f"package-fact:{node.get('node_id')}"
        add_node(
            node_id,
            node_type="package_fact",
            package_fact_node_id=node.get("node_id"),
            package_chunk_ids=node.get("package_chunk_ids") or [],
            evidence_span_ids=node.get("evidence_span_ids") or [],
            fact_type=node.get("node_type"),
            fact_subtype=node.get("fact_subtype"),
            normalized_value=node.get("normalized_value"),
        )
        add_edge(start_node_id, "package_fact", node_id)
        relationship = str(node.get("node_type") or "")
        if relationship in {"geography", "management_area", "overlay"}:
            add_edge(start_node_id, relationship, node_id)
        for span_id in node.get("evidence_span_ids") or []:
            span_node_id = f"evidence-span:{span_id}"
            add_node(span_node_id, node_type="evidence_span", evidence_span_id=span_id)
            add_edge(node_id, "evidence_span", span_node_id)

    rule_id = ((candidate.get("rule_template") or {}).get("rule_id") or "").strip()
    claims_by_id = {str(claim.get("claim_id")): claim for claim in source_claims}
    for link in rule_claim_links:
        if rule_id and str(link.get("rule_id") or "") != rule_id:
            continue
        link_id = str(link.get("link_id") or _stable_id("rule-claim-link", json.dumps(link, sort_keys=True)))
        link_node_id = f"rule-claim-link:{link_id}"
        add_node(
            link_node_id,
            node_type="rule_claim_link",
            link_id=link_id,
            rule_id=link.get("rule_id"),
        )
        add_edge(start_node_id, "rule_claim_link", link_node_id)
        claim_id = str(link.get("claim_id") or link.get("source_claim_id") or "")
        if claim_id:
            claim = claims_by_id.get(claim_id, {})
            claim_node_id = f"source-claim:{claim_id}"
            add_node(
                claim_node_id,
                node_type="source_claim",
                claim_id=claim_id,
                source_record_id=claim.get("source_record_id") or link.get("source_record_id"),
            )
            add_edge(link_node_id, "source_claim", claim_node_id)

    forest_plan = candidate.get("forest_plan") if isinstance(candidate.get("forest_plan"), dict) else {}
    if forest_plan:
        profile_id = str(forest_plan.get("forest_unit_id") or "")
        profile_node_id = f"forest-plan-profile:{profile_id}"
        add_node(profile_node_id, node_type="forest_plan_profile", forest_unit_id=profile_id)
        add_edge(start_node_id, "forest_plan_profile", profile_node_id)
        component_id = str(forest_plan.get("component_id") or "")
        component_node_id = f"forest-plan-component:{component_id}"
        add_node(
            component_node_id,
            node_type="forest_plan_component",
            component_id=component_id,
            component_inventory_id=forest_plan.get("component_inventory_id"),
        )
        add_edge(profile_node_id, "component_inventory", component_node_id)

    dependency_contract = candidate.get("dependency_contract")
    if isinstance(dependency_contract, dict):
        for field, relationship in (
            ("dependency_rule_ids", "dependency"),
            ("exception_rule_ids", "exception"),
            ("supersedes_rule_ids", "supersession"),
        ):
            for value in _strings(dependency_contract.get(field)):
                node_id = f"{relationship}:{value}"
                add_node(node_id, node_type=relationship, rule_id=value)
                add_edge(start_node_id, relationship, node_id)
        for value in _strings(dependency_contract.get("supporting_source_record_ids")):
            node_id = f"source-record:{value}"
            add_node(
                node_id,
                node_type="source_record",
                source_record_id=value,
                source_record_relationship="supporting",
            )
            add_edge(start_node_id, "source_record", node_id)
        for record in dependency_contract.get("supporting_source_records") or []:
            if not isinstance(record, dict):
                continue
            source_record_id = str(record.get("source_record_id") or "").strip()
            if not source_record_id:
                continue
            node_id = f"source-record:{source_record_id}"
            add_node(
                node_id,
                node_type="source_record",
                source_record_id=source_record_id,
                source_record_relationship="supporting",
                source_record_role=record.get("role"),
                source_record_required_for=record.get("required_for"),
            )
            add_edge(start_node_id, "source_record", node_id)

    _merge_external_graph(
        nodes=nodes,
        adjacency=adjacency,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        external_graph_index=external_graph_index,
        allowed_relationships=allowed_relationships,
        candidate_source_record_ids=set(_strings(candidate.get("source_record_ids"))),
    )
    return {"nodes": nodes, "adjacency": adjacency}


def _external_graph_index(
    *,
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes_by_id: dict[str, dict[str, Any]] = {}
    node_ids_by_source_record_id: dict[str, set[str]] = defaultdict(set)
    edges_by_source_node_id: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for node in graph_nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id") or "")
        if not node_id:
            continue
        nodes_by_id[node_id] = node
        source_ids = set(_strings(node.get("source_record_id"))) | set(
            _strings(node.get("source_record_ids"))
        )
        for source_record_id in source_ids:
            node_ids_by_source_record_id[source_record_id].add(node_id)
    for edge in graph_edges:
        if not isinstance(edge, dict):
            continue
        relationship = str(edge.get("relationship_type") or edge.get("edge_type") or "")
        source = str(edge.get("from_node_id") or edge.get("source_node_id") or "")
        target = str(edge.get("to_node_id") or edge.get("target_node_id") or "")
        if source and relationship and target:
            edges_by_source_node_id[source].append((relationship, target))
    return {
        "nodes_by_id": nodes_by_id,
        "node_ids_by_source_record_id": node_ids_by_source_record_id,
        "edges_by_source_node_id": edges_by_source_node_id,
    }


def _matching_package_nodes(
    *,
    package_fact_graph: dict[str, Any],
    candidate: dict[str, Any],
    package_match_cache: dict[tuple, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    cache_key = _package_match_cache_key(candidate)
    cached = package_match_cache.get(cache_key)
    if cached is not None:
        return cached
    scoped_ids = _scoped_package_fact_ids(candidate)
    if any(scoped_ids.values()):
        matches = _scoped_package_nodes(
            package_fact_graph=package_fact_graph,
            scoped_ids=scoped_ids,
        )
    else:
        matches = [
            node
            for node in package_fact_graph.get("nodes") or []
            if isinstance(node, dict)
            and node.get("node_type") not in {"evidence_span", "package_section"}
            and _package_node_matches_graph_contract(node, candidate)
        ]
    package_match_cache[cache_key] = matches
    return matches


def _package_match_cache_key(candidate: dict[str, Any]) -> tuple:
    scoped_ids = _scoped_package_fact_ids(candidate)
    if any(scoped_ids.values()):
        return (
            "scoped",
            tuple(sorted(scoped_ids["geography"])),
            tuple(sorted(scoped_ids["management_area"])),
            tuple(sorted(scoped_ids["overlay"])),
        )
    package_filters = candidate.get("package_section_filters")
    if not isinstance(package_filters, dict):
        package_filters = {}
    terms = (
        _strings(package_filters.get("package_terms"))
        + _strings(package_filters.get("package_section_terms"))
        + _strings(package_filters.get("package_evidence_terms"))
        + _strings(package_filters.get("geographic_area_ids"))
        + _strings(package_filters.get("management_area_ids"))
        + _strings(package_filters.get("overlay_ids"))
        + _flatten_groups(candidate.get("positive_trigger_groups"))
        + _flatten_groups(candidate.get("negative_trigger_groups"))
    )
    neighbor_filters = (candidate.get("graph_expansion_contract") or {}).get(
        "neighbor_filters"
    )
    if not isinstance(neighbor_filters, dict):
        neighbor_filters = {}
    return (
        tuple(sorted(_strings(candidate.get("required_package_fact_types")))),
        tuple(term.casefold() for term in terms),
        tuple(sorted(_strings(neighbor_filters.get("geographic_area_ids")))),
        tuple(sorted(_strings(neighbor_filters.get("management_area_ids")))),
        tuple(sorted(_strings(neighbor_filters.get("overlay_ids")))),
    )


def _package_node_matches_graph_contract(node: dict[str, Any], candidate: dict[str, Any]) -> bool:
    scoped_ids = _scoped_package_fact_ids(candidate)
    node_type = str(node.get("node_type") or "")
    normalized_value = str(node.get("normalized_value") or "")
    if node_type in scoped_ids:
        expected_values = scoped_ids[node_type]
        if expected_values:
            return normalized_value in expected_values
        if any(scoped_ids.values()):
            return False
    text = str(node.get("_applicability_search_text") or "").casefold()
    if not text:
        text = " ".join(
            str(value or "")
            for value in (
                node.get("label"),
                node.get("raw_value"),
                node.get("normalized_value"),
                node.get("fact_subtype"),
                node.get("section_family"),
                node.get("context_excerpt"),
                node.get("matched_text"),
            )
        ).casefold()
    terms = _graph_package_terms(candidate)
    if terms:
        return any(term in text for term in terms)
    if any(scoped_ids.values()):
        return False
    return _package_node_matches_candidate(node, candidate)


def _scoped_package_nodes(
    *,
    package_fact_graph: dict[str, Any],
    scoped_ids: dict[str, set[str]],
) -> list[dict[str, Any]]:
    matches = []
    for node in package_fact_graph.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("node_type") or "")
        expected_values = scoped_ids.get(node_type) or set()
        if not expected_values:
            continue
        if str(node.get("normalized_value") or "") in expected_values:
            matches.append(node)
    return sorted(
        matches,
        key=lambda node: (
            str(node.get("node_type") or ""),
            str(node.get("normalized_value") or ""),
            str(node.get("node_id") or ""),
        ),
    )


def _scoped_package_fact_ids(candidate: dict[str, Any]) -> dict[str, set[str]]:
    neighbor_filters = (candidate.get("graph_expansion_contract") or {}).get(
        "neighbor_filters"
    )
    if not isinstance(neighbor_filters, dict):
        neighbor_filters = {}
    package_filters = candidate.get("package_section_filters")
    if not isinstance(package_filters, dict):
        package_filters = {}
    forest_plan = candidate.get("forest_plan")
    if not isinstance(forest_plan, dict):
        forest_plan = {}
    return {
        "geography": set(
            _strings(neighbor_filters.get("geographic_area_ids"))
            or _strings(package_filters.get("geographic_area_ids"))
            or _strings(forest_plan.get("geographic_area_ids"))
        ),
        "management_area": set(
            _strings(neighbor_filters.get("management_area_ids"))
            or _strings(package_filters.get("management_area_ids"))
            or _strings(forest_plan.get("management_area_ids"))
        ),
        "overlay": set(
            _strings(neighbor_filters.get("overlay_ids"))
            or _strings(package_filters.get("overlay_ids"))
            or _strings(forest_plan.get("overlay_ids"))
        ),
    }


def _graph_package_terms(candidate: dict[str, Any]) -> set[str]:
    package_filters = candidate.get("package_section_filters")
    if not isinstance(package_filters, dict):
        package_filters = {}
    terms = (
        _strings(package_filters.get("package_terms"))
        + _strings(package_filters.get("package_section_terms"))
        + _strings(package_filters.get("package_evidence_terms"))
        + _strings(package_filters.get("resource_topics"))
        + _strings(package_filters.get("activity_tags"))
        + _flatten_groups(candidate.get("positive_trigger_groups"))
        + _flatten_groups(candidate.get("negative_trigger_groups"))
    )
    return {term.casefold() for term in terms if term.strip()}


def _flatten_groups(value: object) -> list[str]:
    terms: list[str] = []
    if not isinstance(value, list):
        return terms
    for group in value:
        if isinstance(group, list):
            terms.extend(_strings(group))
        else:
            terms.extend(_strings(group))
    return terms


def _merge_external_graph(
    *,
    nodes: dict[str, dict[str, Any]],
    adjacency: dict[str, list[tuple[str, str]]],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    external_graph_index: dict[str, Any] | None,
    allowed_relationships: set[str],
    candidate_source_record_ids: set[str],
) -> None:
    if not graph_nodes or not graph_edges or not candidate_source_record_ids:
        return
    if external_graph_index:
        _merge_external_graph_from_index(
            nodes=nodes,
            adjacency=adjacency,
            external_graph_index=external_graph_index,
            allowed_relationships=allowed_relationships,
            candidate_source_record_ids=candidate_source_record_ids,
        )
        return
    allowed_node_ids = set(nodes)
    for node in graph_nodes:
        node_id = str(node.get("node_id") or "")
        node_source_ids = set(_strings(node.get("source_record_id"))) | set(
            _strings(node.get("source_record_ids"))
        )
        if node_id and node_source_ids & candidate_source_record_ids:
            allowed_node_ids.add(node_id)
            nodes.setdefault(node_id, node)
    for edge in graph_edges:
        relationship = str(edge.get("relationship_type") or edge.get("edge_type") or "")
        if relationship not in allowed_relationships:
            continue
        source = str(edge.get("from_node_id") or edge.get("source_node_id") or "")
        target = str(edge.get("to_node_id") or edge.get("target_node_id") or "")
        if source in allowed_node_ids and target:
            adjacency[source].append((relationship, target))
            nodes.setdefault(target, {"node_id": target, "node_type": "external_graph_node"})


def _merge_external_graph_from_index(
    *,
    nodes: dict[str, dict[str, Any]],
    adjacency: dict[str, list[tuple[str, str]]],
    external_graph_index: dict[str, Any],
    allowed_relationships: set[str],
    candidate_source_record_ids: set[str],
) -> None:
    nodes_by_id = external_graph_index.get("nodes_by_id") or {}
    node_ids_by_source_record_id = (
        external_graph_index.get("node_ids_by_source_record_id") or {}
    )
    edges_by_source_node_id = external_graph_index.get("edges_by_source_node_id") or {}
    allowed_node_ids = set(nodes)
    for source_record_id in candidate_source_record_ids:
        for node_id in node_ids_by_source_record_id.get(source_record_id, set()):
            allowed_node_ids.add(node_id)
            node = nodes_by_id.get(node_id)
            if isinstance(node, dict):
                nodes.setdefault(node_id, node)
    for source in sorted(allowed_node_ids):
        for relationship, target in edges_by_source_node_id.get(source, []):
            if relationship not in allowed_relationships:
                continue
            adjacency[source].append((relationship, target))
            if target in nodes_by_id:
                nodes.setdefault(target, nodes_by_id[target])
            else:
                nodes.setdefault(target, {"node_id": target, "node_type": "external_graph_node"})


def _bounded_paths(
    *,
    start_node_id: str,
    adjacency: dict[str, list[tuple[str, str]]],
    max_depth: int,
    allowed_relationships: set[str],
    max_path_count: int | None = None,
) -> list[list[str]]:
    if max_path_count is not None and max_path_count < 1:
        raise ValueError("max_path_count must be at least 1")
    paths: list[list[str]] = []
    queue: deque[list[str]] = deque([[start_node_id]])
    while queue:
        path = queue.popleft()
        depth = (len(path) - 1) // 2
        if depth >= max_depth:
            continue
        current = path[-1]
        for relationship, target in sorted(adjacency.get(current, [])):
            if relationship not in allowed_relationships:
                continue
            if target in _path_node_ids(path):
                continue
            next_path = [*path, relationship, target]
            paths.append(next_path)
            if max_path_count is not None and len(paths) >= max_path_count:
                return sorted(paths, key=lambda path: (len(path), "|".join(path)))
            queue.append(next_path)
    return sorted(paths, key=lambda path: (len(path), "|".join(path)))


def _graph_dead_end_row(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    package_graph_identity: dict[str, Any],
    evidence_graph_identity: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    return {
        "schema_version": APPLICABILITY_GRAPH_TRACE_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "graph_path_id": _stable_id("graph-path", applicability_run_id, candidate_id, "dead-end"),
        "query_timestamp": created_at,
        "graph_artifacts": [package_graph_identity, evidence_graph_identity],
        "graph_build_id": evidence_graph_identity.get("graph_build_id"),
        "graph_artifact_path": evidence_graph_identity.get("graph_artifact_path"),
        "graph_artifact_hash": evidence_graph_identity.get("graph_artifact_hash"),
        "start_node_id": f"candidate:{candidate_id}",
        "end_node_id": f"candidate:{candidate_id}",
        "traversed_node_ids": [f"candidate:{candidate_id}"],
        "relationship_types": [],
        "traversal_depth": 0,
        "max_depth": int((candidate.get("graph_expansion_contract") or {}).get("max_depth") or 0),
        "path_rationale": "No graph path found within the declared graph expansion contract.",
        "selected_status": "rejected",
        "rejection_reason": "graph_dead_end",
        "evidence_references": {
            "candidate_authority_id": candidate_id,
            "source_record_ids": _strings(candidate.get("source_record_ids")),
            "retrieval_trace_ids": [],
            "retrieval_result_ids": [],
        },
        "bounded_by_contract": {
            "allowed_relationship_types": _strings(
                (candidate.get("graph_expansion_contract") or {}).get("relationship_types")
            ),
            "max_depth": int((candidate.get("graph_expansion_contract") or {}).get("max_depth") or 0),
        },
    }


def _selected_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        result
        for row in rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "selected"
    ]


def _path_node_ids(path: list[str]) -> list[str]:
    return path[0::2]


def _path_relationship_types(path: list[str]) -> list[str]:
    return path[1::2]


def _path_rationale(path: list[str], nodes: dict[str, dict[str, Any]]) -> str:
    relationship_types = ", ".join(_path_relationship_types(path))
    end_node = nodes.get(path[-1], {})
    return (
        f"Bounded traversal followed {relationship_types or 'no relationships'} to "
        f"{end_node.get('node_type') or path[-1]}."
    )


def _path_evidence_references(path: list[str], nodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    refs: dict[str, set[str]] = {
        "authority_categories": set(),
        "source_record_ids": set(),
        "source_claim_ids": set(),
        "rule_claim_link_ids": set(),
        "forest_plan_component_ids": set(),
        "package_fact_node_ids": set(),
        "package_chunk_ids": set(),
        "evidence_span_ids": set(),
        "retrieval_result_ids": set(),
        "retrieval_trace_ids": set(),
    }
    for node_id in _path_node_ids(path):
        node = nodes.get(node_id, {})
        for key, ref_key in (
            ("source_record_id", "source_record_ids"),
            ("claim_id", "source_claim_ids"),
            ("link_id", "rule_claim_link_ids"),
            ("authority_category", "authority_categories"),
            ("component_id", "forest_plan_component_ids"),
            ("package_fact_node_id", "package_fact_node_ids"),
            ("package_chunk_id", "package_chunk_ids"),
            ("retrieval_result_id", "retrieval_result_ids"),
        ):
            if node.get(key):
                refs[ref_key].add(str(node[key]))
        for key, ref_key in (
            ("package_chunk_ids", "package_chunk_ids"),
            ("evidence_span_ids", "evidence_span_ids"),
            ("retrieval_trace_ids", "retrieval_trace_ids"),
        ):
            for value in _strings(node.get(key)):
                refs[ref_key].add(value)
    return {key: sorted(values) for key, values in refs.items()}
