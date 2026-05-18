from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .artifact_utils import _source_set_id_from_catalog
from .source_register_proving import default_proving_output_path
from .source_register_proving import load_proving_report


GRAPH_ACCURACY_EVAL_SCHEMA_VERSION = "graph-accuracy-eval-report-v1"
DEFAULT_GRAPH_ACCURACY_EVAL_PATH = Path("config/graph_accuracy_eval_v1.json")
DEFAULT_GRAPH_FILENAME = "nepa_3d_graph.json"
DEFAULT_GRAPH_REPORT_FILENAME = "graph_accuracy_eval_report.json"

GRAPH_NODE_TYPE_TO_CLASS_ID = {
    "authority_document": "authority_document",
    "authority_section": "authority_section",
    "jurisdiction_scope": "jurisdiction_scope",
    "forest_unit": "forest_unit",
    "forest_plan": "forest_plan",
    "forest_plan_component": "forest_plan_component",
    "source_record": "source_record",
    "artifact": "source_artifact",
    "evidence_span": "evidence_span",
    "authority_path": "authority_path",
    "justification_path": "justification_path",
}


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
    eval_payload = json.loads(Path(eval_path).read_text(encoding="utf-8"))
    source_set_id = _resolve_source_set_id(output_dir)
    graph_path = _default_graph_path(output_dir, source_set_id)
    if graph_path.exists():
        payload = _run_knowledge_graph_mode(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_path=graph_path,
            eval_payload=eval_payload,
            output_path=output_path or graph_path.parent / DEFAULT_GRAPH_REPORT_FILENAME,
        )
    else:
        report = load_proving_report(output_dir, report_path)
        payload = _run_proving_mode(
            report=report,
            eval_payload=eval_payload,
            output_path=output_path
            or default_proving_output_path(output_dir, DEFAULT_GRAPH_REPORT_FILENAME),
        )
    payload["output_path"].write_text(
        json.dumps(payload["body"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return GraphAccuracyEvalResult(
        output_path=payload["output_path"],
        summary=payload["body"]["summary"],
    )


def _run_knowledge_graph_mode(
    *,
    output_dir: Path,
    source_set_id: str,
    graph_path: Path,
    eval_payload: dict,
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
    graph_class_ids = {
        GRAPH_NODE_TYPE_TO_CLASS_ID[str(node.get("node_type") or "")]
        for node in nodes
        if str(node.get("node_type") or "") in GRAPH_NODE_TYPE_TO_CLASS_ID
    }
    lens_ids_present = {
        str(entry.get("lens_id") or "")
        for entry in graph.get("lens_metadata", [])
        if isinstance(entry, dict) and entry.get("lens_id")
    }
    authority_path_nodes = [
        node for node in nodes if str(node.get("node_type") or "") == "authority_path"
    ]
    justification_path_nodes = [
        node for node in nodes if str(node.get("node_type") or "") == "justification_path"
    ]
    relationship_types_present = {
        str(_metadata(node).get("relationship_type") or "")
        for node in authority_path_nodes
        if str(_metadata(node).get("relationship_type") or "").strip()
    }
    path_patterns_present = {
        str(_metadata(node).get("path_pattern_id") or "")
        for node in authority_path_nodes
        if str(_metadata(node).get("path_pattern_id") or "").strip()
    }
    edge_tuples = {
        (
            str(edge.get("edge_type") or ""),
            str(edge.get("source_node_id") or ""),
            str(edge.get("target_node_id") or ""),
        )
        for edge in edges
    }
    justification_edge_gaps = sorted(
        str(node.get("node_id") or "")
        for node in authority_path_nodes
        if (
            "JUSTIFIED_BY",
            str(node.get("node_id") or ""),
            f"justification_path:{str(node.get('node_id') or '').removeprefix('authority_path:')}",
        )
        not in edge_tuples
    )
    supporting_source_gaps = sorted(
        str(node.get("node_id") or "")
        for node in justification_path_nodes
        if not any(
            edge_type == "SUPPORTS_JUSTIFICATION_PATH" and target_node_id == str(node.get("node_id") or "")
            for edge_type, _, target_node_id in edge_tuples
        )
    )
    semantic_currentness_gaps = sorted(
        str(node.get("node_id") or "")
        for node in nodes
        if str(node.get("node_type") or "")
        in {
            "authority_document",
            "authority_section",
            "jurisdiction_scope",
            "forest_plan",
            "source_record",
        }
        and not isinstance(node.get("currentness_metadata"), dict)
    )
    required_node_class_ids = eval_payload.get(
        "source_set_required_node_class_ids",
        eval_payload.get("required_node_class_ids", []),
    )
    required_lens_ids = eval_payload.get(
        "knowledge_graph_required_lens_ids",
        eval_payload.get("required_lens_ids", []),
    )

    checks = [
        _check(
            "graph_accuracy_eval_contract_loaded",
            eval_payload.get("schema_version") == "graph-accuracy-eval-v1",
            "graph-accuracy-eval-v1",
            eval_payload.get("schema_version"),
        ),
        _check(
            "required_node_classes_present",
            set(required_node_class_ids).issubset(graph_class_ids),
            sorted(required_node_class_ids),
            sorted(graph_class_ids),
        ),
        _check(
            "required_lenses_present",
            set(required_lens_ids).issubset(lens_ids_present),
            sorted(required_lens_ids),
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
            "authority_paths_have_justification_paths",
            not justification_edge_gaps,
            [],
            justification_edge_gaps,
        ),
        _check(
            "justification_paths_have_supporting_source_records",
            not supporting_source_gaps,
            [],
            supporting_source_gaps,
        ),
        _check(
            "semantic_nodes_carry_currentness_metadata",
            not semantic_currentness_gaps,
            [],
            semantic_currentness_gaps,
        ),
    ]
    passed = all(check["passed"] for check in checks)
    body = {
        "schema_version": GRAPH_ACCURACY_EVAL_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "graph_path": str(graph_path),
        "checks": checks,
        "summary": {
            "passed": passed,
            "node_count": len(nodes),
            "authority_path_count": len(authority_path_nodes),
            "justification_path_count": len(justification_path_nodes),
            "relationship_type_count": len(relationship_types_present),
            "output_path": str(output_path),
        },
    }
    return {"output_path": output_path, "body": body}


def _run_proving_mode(*, report: dict, eval_payload: dict, output_path: Path) -> dict:
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
    body = {
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
    return {"output_path": output_path, "body": body}


def _resolve_source_set_id(output_dir: Path) -> str:
    try:
        return _source_set_id_from_catalog(output_dir)
    except (FileNotFoundError, ValueError):
        context = load_proving_report(output_dir)
        return str(context["source_set_id"])


def _default_graph_path(output_dir: Path, source_set_id: str) -> Path:
    return output_dir / "derived" / source_set_id / "knowledge_graph" / DEFAULT_GRAPH_FILENAME


def _metadata(node: dict) -> dict:
    value = node.get("metadata")
    return value if isinstance(value, dict) else {}


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
