from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .source_register_proving import default_proving_output_path
from .source_register_proving import load_proving_report


GRAPH_HEALTH_EVAL_SCHEMA_VERSION = "graph-health-eval-report-v1"
DEFAULT_GRAPH_HEALTH_CONTRACT_PATH = Path("config/graph_health_contract_v1.json")


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
    report = load_proving_report(output_dir, report_path)
    contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
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
    output_path = output_path or default_proving_output_path(
        output_dir, "graph_health_eval_report.json"
    )
    payload = {
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
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return GraphHealthEvalResult(output_path=output_path, summary=payload["summary"])


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
