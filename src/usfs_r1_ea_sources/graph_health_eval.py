from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
import json

from .artifact_utils import _source_set_id_from_catalog
from .source_register_proving import default_proving_output_path
from .source_register_proving import load_proving_report


GRAPH_HEALTH_EVAL_SCHEMA_VERSION = "graph-health-eval-report-v1"
DEFAULT_GRAPH_HEALTH_CONTRACT_PATH = Path("config/graph_health_contract_v1.json")
DEFAULT_GRAPH_FILENAME = "nepa_3d_graph.json"
DEFAULT_GRAPH_REPORT_FILENAME = "graph_health_eval_report.json"


@dataclass(frozen=True)
class GraphHealthEvalResult:
    output_path: Path
    summary: dict


def run_graph_health_eval(
    *,
    output_dir: Path,
    report_path: Path | None = None,
    contract_path: Path = DEFAULT_GRAPH_HEALTH_CONTRACT_PATH,
    output_path: Path | None = None,
) -> GraphHealthEvalResult:
    output_dir = Path(output_dir)
    contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    source_set_id = _resolve_source_set_id(output_dir)
    graph_path = output_dir / "derived" / source_set_id / "knowledge_graph" / DEFAULT_GRAPH_FILENAME
    if graph_path.exists():
        payload = _run_knowledge_graph_mode(
            source_set_id=source_set_id,
            graph_path=graph_path,
            contract=contract,
            output_path=output_path or graph_path.parent / DEFAULT_GRAPH_REPORT_FILENAME,
        )
    else:
        report = load_proving_report(output_dir, report_path)
        payload = _run_proving_mode(
            report=report,
            contract=contract,
            output_path=output_path
            or default_proving_output_path(output_dir, DEFAULT_GRAPH_REPORT_FILENAME),
        )
    payload["output_path"].write_text(
        json.dumps(payload["body"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return GraphHealthEvalResult(
        output_path=payload["output_path"],
        summary=payload["body"]["summary"],
    )


def _run_knowledge_graph_mode(
    *,
    source_set_id: str,
    graph_path: Path,
    contract: dict,
    output_path: Path,
) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = [
        node
        for node in graph.get("nodes", [])
        if isinstance(node, dict)
    ]
    edges = [
        edge
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
    ]
    lens_ids = {
        str(entry.get("lens_id") or "")
        for entry in graph.get("lens_metadata", [])
        if isinstance(entry, dict) and entry.get("lens_id")
    }
    orphan_node_ids, component_count = _graph_connectivity(nodes, edges)
    orphan_node_ids = [
        node_id
        for node_id in orphan_node_ids
        if not node_id.startswith("graph_lens:")
    ]
    authority_path_ids = {
        str(node.get("node_id") or "")
        for node in nodes
        if str(node.get("node_type") or "") == "authority_path"
    }
    justified_path_ids = {
        str(edge.get("source_node_id") or "")
        for edge in edges
        if str(edge.get("edge_type") or "") == "JUSTIFIED_BY"
    }
    justification_support_ids = {
        str(edge.get("target_node_id") or "")
        for edge in edges
        if str(edge.get("edge_type") or "") == "SUPPORTS_JUSTIFICATION_PATH"
    }
    required_lens_ids = contract.get(
        "knowledge_graph_required_lens_ids",
        contract.get("required_lens_ids", []),
    )
    checks = [
        _check(
            "graph_health_contract_loaded",
            contract.get("schema_version") == "graph-health-contract-v1",
            "graph-health-contract-v1",
            contract.get("schema_version"),
        ),
        _check(
            "orphan_node_count_within_limit",
            len(orphan_node_ids) <= int(contract.get("max_orphan_node_count", 0)),
            int(contract.get("max_orphan_node_count", 0)),
            len(orphan_node_ids),
        ),
        _check(
            "disconnected_component_count_within_limit",
            component_count <= int(contract.get("max_disconnected_component_count", 1)),
            int(contract.get("max_disconnected_component_count", 1)),
            component_count,
        ),
        _check(
            "required_lenses_present",
            set(required_lens_ids).issubset(lens_ids),
            sorted(required_lens_ids),
            sorted(lens_ids),
        ),
        _check(
            "authority_paths_are_justified",
            authority_path_ids <= justified_path_ids,
            sorted(authority_path_ids),
            sorted(authority_path_ids - justified_path_ids),
        ),
        _check(
            "justification_paths_are_supported",
            {
                node["node_id"]
                for node in nodes
                if str(node.get("node_type") or "") == "justification_path"
            }
            <= justification_support_ids,
            sorted(
                node["node_id"]
                for node in nodes
                if str(node.get("node_type") or "") == "justification_path"
            ),
            sorted(
                {
                    node["node_id"]
                    for node in nodes
                    if str(node.get("node_type") or "") == "justification_path"
                }
                - justification_support_ids
            ),
        ),
    ]
    passed = all(check["passed"] for check in checks)
    body = {
        "schema_version": GRAPH_HEALTH_EVAL_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "graph_path": str(graph_path),
        "checks": checks,
        "summary": {
            "passed": passed,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "orphan_node_count": len(orphan_node_ids),
            "disconnected_component_count": component_count,
            "output_path": str(output_path),
        },
    }
    return {"output_path": output_path, "body": body}


def _run_proving_mode(*, report: dict, contract: dict, output_path: Path) -> dict:
    graph = report["graph"]
    lens_ids = {entry["lens_id"] for entry in graph["lens_metadata"]}
    checks = [
        _check(
            "graph_health_contract_loaded",
            contract.get("schema_version") == "graph-health-contract-v1",
            "graph-health-contract-v1",
            contract.get("schema_version"),
        ),
        _check(
            "orphan_node_count_within_limit",
            len(graph["orphan_node_ids"]) <= int(contract.get("max_orphan_node_count", 0)),
            int(contract.get("max_orphan_node_count", 0)),
            len(graph["orphan_node_ids"]),
        ),
        _check(
            "disconnected_component_count_within_limit",
            len(graph["disconnected_components"])
            <= int(contract.get("max_disconnected_component_count", 1)),
            int(contract.get("max_disconnected_component_count", 1)),
            len(graph["disconnected_components"]),
        ),
        _check(
            "identity_collision_count_zero",
            report["alias_report"]["identity_collision_count"] == 0,
            0,
            report["alias_report"]["identity_collision_count"],
        ),
        _check(
            "required_lenses_present",
            set(contract.get("required_lens_ids", [])).issubset(lens_ids),
            sorted(contract.get("required_lens_ids", [])),
            sorted(lens_ids),
        ),
        _check(
            "justification_path_count_meets_relationship_count",
            len(graph["justification_paths"]) >= report["semantic_relationships"]["relationship_count"],
            report["semantic_relationships"]["relationship_count"],
            len(graph["justification_paths"]),
        ),
    ]
    passed = all(check["passed"] for check in checks)
    body = {
        "schema_version": GRAPH_HEALTH_EVAL_SCHEMA_VERSION,
        "source_set_id": report["source_set_id"],
        "checks": checks,
        "summary": {
            "passed": passed,
            "node_count": graph["node_count"],
            "edge_count": graph["edge_count"],
            "orphan_node_count": len(graph["orphan_node_ids"]),
            "disconnected_component_count": len(graph["disconnected_components"]),
            "output_path": str(output_path),
        },
    }
    return {"output_path": output_path, "body": body}


def _graph_connectivity(
    nodes: list[dict],
    edges: list[dict],
) -> tuple[list[str], int]:
    node_ids = [
        str(node.get("node_id") or "")
        for node in nodes
        if node.get("node_id") and str(node.get("node_type") or "") != "graph_lens"
    ]
    neighbors: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source = str(edge.get("source_node_id") or "")
        target = str(edge.get("target_node_id") or "")
        if not source or not target:
            continue
        neighbors[source].add(target)
        neighbors[target].add(source)
    orphan_node_ids = sorted(node_id for node_id in node_ids if not neighbors.get(node_id))
    visited: set[str] = set()
    component_count = 0
    for node_id in node_ids:
        if node_id in visited or node_id in orphan_node_ids:
            continue
        component_count += 1
        queue = deque([node_id])
        visited.add(node_id)
        while queue:
            current = queue.popleft()
            for neighbor in neighbors.get(current, set()):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)
    component_count += len(orphan_node_ids)
    return orphan_node_ids, component_count


def _resolve_source_set_id(output_dir: Path) -> str:
    try:
        return _source_set_id_from_catalog(output_dir)
    except (FileNotFoundError, ValueError):
        report = load_proving_report(output_dir)
        return str(report["source_set_id"])


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
