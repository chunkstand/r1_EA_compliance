from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .artifact_utils import _source_set_id_from_catalog
from .nepa_3d_graph_contract import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH


AUTHORITY_ONTOLOGY_VALIDATION_SCHEMA_VERSION = "authority-ontology-validation-report-v1"
DEFAULT_AUTHORITY_ONTOLOGY_PATH = Path("config/authority_document_ontology_v1.json")
DEFAULT_AUTHORITY_ONTOLOGY_EVAL_PATH = Path("config/authority_ontology_eval_v1.json")
DEFAULT_KNOWLEDGE_GRAPH_FILENAME = "nepa_3d_graph.json"
DEFAULT_KNOWLEDGE_GRAPH_SUMMARY_FILENAME = "nepa_3d_graph_summary.json"
DEFAULT_REPORT_FILENAME = "authority_ontology_validation_report.json"

ONTOLOGY_CLASS_TO_GRAPH_NODE_TYPE = {
    "authority_document": "authority_document",
    "authority_section": "authority_section",
    "forest_unit": "forest_unit",
    "jurisdiction_scope": "jurisdiction_scope",
    "source_record": "source_record",
    "source_artifact": "artifact",
    "evidence_span": "evidence_span",
    "forest_plan": "forest_plan",
    "forest_plan_component": "forest_plan_component",
    "authority_path": "authority_path",
    "justification_path": "justification_path",
}


@dataclass(frozen=True)
class AuthorityOntologyValidateResult:
    output_path: Path
    summary: dict


def run_authority_ontology_validate(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    ontology_path: Path = DEFAULT_AUTHORITY_ONTOLOGY_PATH,
    eval_path: Path = DEFAULT_AUTHORITY_ONTOLOGY_EVAL_PATH,
    graph_contract_path: Path = DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH,
    graph_path: Path | None = None,
    output_path: Path | None = None,
) -> AuthorityOntologyValidateResult:
    output_dir = Path(output_dir)
    ontology = _load_json(ontology_path)
    eval_payload = _load_json(eval_path)
    graph_contract = _load_json(graph_contract_path)

    resolved_source_set_id = source_set_id
    if resolved_source_set_id is None:
        try:
            resolved_source_set_id = _source_set_id_from_catalog(output_dir)
        except (FileNotFoundError, ValueError):
            resolved_source_set_id = None

    if graph_path is None and resolved_source_set_id:
        graph_path = (
            output_dir
            / "derived"
            / resolved_source_set_id
            / "knowledge_graph"
            / DEFAULT_KNOWLEDGE_GRAPH_FILENAME
        )
    graph = _load_json(graph_path) if graph_path is not None and graph_path.exists() else None
    graph_node_types = {
        str(node.get("node_type") or "")
        for node in graph.get("nodes", [])
        if isinstance(node, dict)
    } if isinstance(graph, dict) else set()
    contract_node_types = {
        str(node_type.get("node_type") or "")
        for node_type in graph_contract.get("node_types", [])
        if isinstance(node_type, dict)
    }
    ontology_class_ids = {
        str(entry.get("class_id") or "")
        for entry in ontology.get("classes", [])
        if isinstance(entry, dict) and entry.get("class_id")
    }
    object_property_ids = {
        str(entry.get("property_id") or "")
        for entry in ontology.get("object_properties", [])
        if isinstance(entry, dict) and entry.get("property_id")
    }
    disjoint_set_ids = {
        str(entry.get("set_id") or "")
        for entry in ontology.get("disjoint_class_sets", [])
        if isinstance(entry, dict) and entry.get("set_id")
    }
    required_class_ids = {
        str(value)
        for value in eval_payload.get("required_class_ids", [])
        if str(value or "").strip()
    }
    required_object_property_ids = {
        str(value)
        for value in eval_payload.get("required_object_property_ids", [])
        if str(value or "").strip()
    }
    required_disjoint_set_ids = {
        str(value)
        for value in eval_payload.get("required_disjoint_set_ids", [])
        if str(value or "").strip()
    }
    source_set_required_class_ids = {
        str(value)
        for value in eval_payload.get("source_set_required_class_ids", [])
        if str(value or "").strip()
    }
    graph_scope = _graph_scope(graph_path)
    required_graph_class_ids = (
        source_set_required_class_ids
        if graph_scope == "source_set" and source_set_required_class_ids
        else required_class_ids
    )
    required_graph_node_types = {
        ONTOLOGY_CLASS_TO_GRAPH_NODE_TYPE[class_id]
        for class_id in required_graph_class_ids
        if class_id in ONTOLOGY_CLASS_TO_GRAPH_NODE_TYPE
    }

    checks = [
        _check(
            "authority_ontology_contract_loaded",
            ontology.get("schema_version") == "authority-document-ontology-v1",
            "authority-document-ontology-v1",
            ontology.get("schema_version"),
        ),
        _check(
            "authority_ontology_eval_contract_loaded",
            eval_payload.get("schema_version") == "authority-ontology-eval-v1",
            "authority-ontology-eval-v1",
            eval_payload.get("schema_version"),
        ),
        _check(
            "knowledge_graph_contract_loaded",
            graph_contract.get("schema_version") == "nepa-3d-graph-contract-v1",
            "nepa-3d-graph-contract-v1",
            graph_contract.get("schema_version"),
        ),
        _check(
            "ontology_defines_required_classes",
            required_class_ids.issubset(ontology_class_ids),
            sorted(required_class_ids),
            sorted(required_class_ids - ontology_class_ids),
        ),
        _check(
            "ontology_defines_required_object_properties",
            required_object_property_ids.issubset(object_property_ids),
            sorted(required_object_property_ids),
            sorted(required_object_property_ids - object_property_ids),
        ),
        _check(
            "ontology_defines_required_disjoint_sets",
            required_disjoint_set_ids.issubset(disjoint_set_ids),
            sorted(required_disjoint_set_ids),
            sorted(required_disjoint_set_ids - disjoint_set_ids),
        ),
        _check(
            "knowledge_graph_contract_represents_required_ontology_classes",
            required_graph_node_types.issubset(contract_node_types),
            sorted(required_graph_node_types),
            sorted(required_graph_node_types - contract_node_types),
        ),
        _check(
            "knowledge_graph_present_for_validation",
            graph is not None,
            True,
            bool(graph is not None),
        ),
        _check(
            "knowledge_graph_exports_required_ontology_node_types",
            graph is not None and required_graph_node_types.issubset(graph_node_types),
            sorted(required_graph_node_types),
            sorted(required_graph_node_types - graph_node_types)
            if graph is not None
            else [],
        ),
        _check(
            "knowledge_graph_exports_authority_and_justification_paths",
            graph is not None
            and {"authority_path", "justification_path"}.issubset(graph_node_types),
            ["authority_path", "justification_path"],
            sorted(
                {"authority_path", "justification_path"} - graph_node_types
            )
            if graph is not None
            else [],
        ),
    ]
    passed = all(check["passed"] for check in checks)
    resolved_output_path = output_path or _default_output_path(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        graph_path=graph_path,
    )
    payload = {
        "schema_version": AUTHORITY_ONTOLOGY_VALIDATION_SCHEMA_VERSION,
        "source_set_id": resolved_source_set_id,
        "graph_path": str(graph_path) if graph_path is not None else None,
        "checks": checks,
        "summary": {
            "passed": passed,
            "source_set_id": resolved_source_set_id,
            "graph_present": graph is not None,
            "graph_scope": graph_scope,
            "required_graph_node_type_count": len(required_graph_node_types),
            "output_path": str(resolved_output_path),
        },
    }
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return AuthorityOntologyValidateResult(
        output_path=resolved_output_path,
        summary=payload["summary"],
    )


def _default_output_path(
    *,
    output_dir: Path,
    source_set_id: str | None,
    graph_path: Path | None,
) -> Path:
    if graph_path is not None:
        return graph_path.parent / DEFAULT_REPORT_FILENAME
    if source_set_id:
        return output_dir / "derived" / source_set_id / "knowledge_graph" / DEFAULT_REPORT_FILENAME
    return output_dir / DEFAULT_REPORT_FILENAME


def _graph_scope(graph_path: Path | None) -> str:
    if graph_path is not None and "reviews" in Path(graph_path).parts:
        return "review"
    return "source_set"


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
