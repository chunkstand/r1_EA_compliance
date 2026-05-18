from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .source_register_proving import default_proving_output_path
from .source_register_proving import load_proving_report


GRAPH_ACCURACY_EVAL_SCHEMA_VERSION = "graph-accuracy-eval-report-v1"
DEFAULT_GRAPH_ACCURACY_EVAL_PATH = Path("config/graph_accuracy_eval_v1.json")


@dataclass(frozen=True)
class GraphAccuracyEvalResult:
    output_path: Path
    summary: dict


def run_graph_accuracy_eval(
    *,
    output_dir: Path,
    report_path: Path | None = None,
    eval_path: Path = DEFAULT_GRAPH_ACCURACY_EVAL_PATH,
    output_path: Path | None = None,
) -> GraphAccuracyEvalResult:
    output_dir = Path(output_dir)
    report = load_proving_report(output_dir, report_path)
    eval_payload = json.loads(Path(eval_path).read_text(encoding="utf-8"))
    graph = report["graph"]
    node_classes_present = {node["class_id"] for node in graph["nodes"]}
    lens_ids_present = {entry["lens_id"] for entry in graph["lens_metadata"]}
    relationship_types_present = set(report["semantic_relationships"]["relationship_type_counts"])
    path_patterns_present = set(report["semantic_relationships"]["path_pattern_counts"])
    checks = [
        _check(
            "graph_accuracy_eval_contract_loaded",
            eval_payload.get("schema_version") == "graph-accuracy-eval-v1",
            "graph-accuracy-eval-v1",
            eval_payload.get("schema_version"),
        ),
        _check(
            "required_node_classes_present",
            set(eval_payload.get("required_node_class_ids", [])).issubset(node_classes_present),
            sorted(eval_payload.get("required_node_class_ids", [])),
            sorted(node_classes_present),
        ),
        _check(
            "required_lenses_present",
            set(eval_payload.get("required_lens_ids", [])).issubset(lens_ids_present),
            sorted(eval_payload.get("required_lens_ids", [])),
            sorted(lens_ids_present),
        ),
        _check(
            "required_relationship_types_present",
            set(eval_payload.get("required_relationship_types", [])).issubset(
                relationship_types_present
            ),
            sorted(eval_payload.get("required_relationship_types", [])),
            sorted(relationship_types_present),
        ),
        _check(
            "required_path_patterns_present",
            set(eval_payload.get("required_path_patterns", [])).issubset(path_patterns_present),
            sorted(eval_payload.get("required_path_patterns", [])),
            sorted(path_patterns_present),
        ),
        _check(
            "justification_paths_present_for_all_relationships",
            len(graph["justification_paths"]) >= report["semantic_relationships"]["relationship_count"],
            report["semantic_relationships"]["relationship_count"],
            len(graph["justification_paths"]),
        ),
    ]
    passed = all(check["passed"] for check in checks)
    output_path = output_path or default_proving_output_path(
        output_dir, "graph_accuracy_eval_report.json"
    )
    payload = {
        "schema_version": GRAPH_ACCURACY_EVAL_SCHEMA_VERSION,
        "source_set_id": report["source_set_id"],
        "checks": checks,
        "summary": {
            "passed": passed,
            "node_count": graph["node_count"],
            "relationship_type_count": len(relationship_types_present),
            "output_path": str(output_path),
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return GraphAccuracyEvalResult(output_path=output_path, summary=payload["summary"])


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
