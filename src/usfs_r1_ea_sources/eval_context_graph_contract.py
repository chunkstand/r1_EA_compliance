from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .eval_trace_inventory import REPO_ROOT
from .eval_trace_store import STORE_SCHEMA_VERSION
from .records import sha256_file


DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH = Path("config/context_graph_contract_v1.json")
TABLE_PRIMARY_KEYS = {
    "system_eval_runs": "eval_run_id",
    "system_eval_cases": "eval_case_id",
    "system_eval_case_results": "eval_case_result_id",
    "system_eval_scores": "eval_score_id",
    "trace_runs": "trace_id",
    "trace_spans": "span_id",
}
JSON_COLUMNS = {
    "system_eval_runs": (
        "source_record_ids_json",
        "scorer_versions_json",
        "thresholds_json",
        "summary_json",
    ),
    "system_eval_cases": ("input_json", "expected_json", "metadata_json"),
    "system_eval_scores": ("evidence_refs_json",),
    "trace_runs": ("artifact_refs_json",),
    "trace_spans": ("attributes_json",),
}


def load_eval_context_graph_contract(
    contract_path: Path = DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    path = _resolve_path(contract_path, repo_root)
    contract = json.loads(path.read_text(encoding="utf-8"))
    checks = validate_eval_context_graph_contract(contract)
    failed = [check["name"] for check in checks if not check["passed"]]
    if failed:
        raise ValueError(f"invalid eval context graph contract: {', '.join(failed)}")
    return contract


def context_graph_contract_summary(
    contract_path: Path = DEFAULT_CONTEXT_GRAPH_CONTRACT_PATH,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, str]:
    path = _resolve_path(contract_path, repo_root)
    return {"path": _display_path(path, repo_root), "sha256": sha256_file(path)}


def validate_eval_context_graph_contract(contract: dict[str, Any]) -> list[dict[str, Any]]:
    required_node_kinds = set(_list_of_strings(contract.get("required_node_kinds")))
    required_edge_kinds = set(_list_of_strings(contract.get("required_edge_kinds")))
    prohibited_node_kinds = set(_list_of_strings(contract.get("prohibited_node_kinds")))
    policy = _dict(contract.get("graph_policy"))
    source_store = _dict(contract.get("source_store"))
    return [
        {
            "name": "context_graph_contract_schema_version",
            "passed": contract.get("schema_version") == "eval-context-graph-contract-v1",
            "actual": contract.get("schema_version"),
        },
        {
            "name": "context_graph_contract_source_store_schema",
            "passed": source_store.get("schema_version") == STORE_SCHEMA_VERSION,
            "actual": source_store.get("schema_version"),
        },
        {
            "name": "context_graph_contract_canonical_tables",
            "passed": set(_list_of_strings(source_store.get("canonical_tables")))
            == set(TABLE_PRIMARY_KEYS),
            "actual": sorted(_list_of_strings(source_store.get("canonical_tables"))),
        },
        {
            "name": "context_graph_contract_required_node_kinds",
            "passed": {
                "artifact",
                "eval_case",
                "eval_result",
                "eval_run",
                "score",
                "span",
                "trace",
            }
            <= required_node_kinds,
            "actual": sorted(required_node_kinds),
        },
        {
            "name": "context_graph_contract_required_edge_kinds",
            "passed": {
                "CONTAINS",
                "DERIVED_FROM",
                "EVALUATED_BY",
                "SCORED_AS",
            }
            <= required_edge_kinds,
            "actual": sorted(required_edge_kinds),
        },
        {
            "name": "context_graph_contract_source_kg_excluded",
            "passed": bool(policy.get("source_knowledge_graph_excluded"))
            and bool(prohibited_node_kinds),
            "actual": {
                "source_knowledge_graph_excluded": policy.get(
                    "source_knowledge_graph_excluded"
                ),
                "prohibited_node_kinds": sorted(prohibited_node_kinds),
            },
        },
        {
            "name": "context_graph_contract_local_policy",
            "passed": bool(policy.get("local_source_of_record"))
            and not bool(policy.get("external_export_approved")),
            "actual": policy,
        },
    ]


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)
