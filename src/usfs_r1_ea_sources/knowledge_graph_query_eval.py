from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any

from .artifact_utils import _source_set_id_from_catalog
from .artifact_utils import _utc_now
from .knowledge_graph_query import _build_query_payload
from .knowledge_graph_query import _compact_dict
from .knowledge_graph_query import _dict_list
from .knowledge_graph_query import _normalize_query_type
from .knowledge_graph_query import _resolve_graph_path
from .knowledge_graph_query import _string_list
from .records import sha256_file


KNOWLEDGE_GRAPH_QUERY_EVAL_RESULTS_SCHEMA_VERSION = "knowledge-graph-query-eval-results-v1"
DEFAULT_QUERY_EVAL_PATH = Path("config/knowledge_graph_query_eval_v1.json")
DEFAULT_QUERY_EVAL_RESULTS_FILENAME = "knowledge_graph_query_eval_results.json"


@dataclass(frozen=True)
class KnowledgeGraphQueryEvalResult:
    output_path: Path
    summary: dict[str, Any]
    payload: dict[str, Any]


def run_knowledge_graph_query_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    review_id: str | None = None,
    eval_path: Path = DEFAULT_QUERY_EVAL_PATH,
    graph_path: Path | None = None,
    output_path: Path | None = None,
) -> KnowledgeGraphQueryEvalResult:
    output_dir = Path(output_dir)
    eval_path = Path(eval_path)
    contract = _load_eval_contract(eval_path)
    resolved_source_set_id = (
        source_set_id
        or str(contract.get("source_set_id") or "").strip()
        or _source_set_id_from_catalog(output_dir)
    )
    resolved_review_id = review_id or contract.get("review_id")
    if resolved_review_id is not None:
        resolved_review_id = str(resolved_review_id)
    resolved_graph_path = _resolve_graph_path(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        review_id=resolved_review_id,
        graph_path=graph_path,
    )
    case_results = []
    for case in contract["cases"]:
        query_payload = _build_query_payload(
            output_dir=output_dir,
            source_set_id=resolved_source_set_id,
            review_id=resolved_review_id,
            graph_path=resolved_graph_path,
            query=case.get("query"),
            query_type=str(case.get("query_type") or "keyword"),
            limit=int(case.get("limit") or contract.get("default_limit") or 10),
            node_type=case.get("node_type"),
            edge_type=case.get("edge_type"),
            source_record_id=case.get("source_record_id"),
            forest_unit_id=case.get("forest_unit_id"),
            citation=case.get("citation"),
            readiness_status=case.get("readiness_status"),
            require_hit=bool(case.get("require_hit", False)),
            fail_on_freshness_warning=bool(case.get("fail_on_freshness_warning", False)),
        )
        case_results.append(_evaluate_query_case(case=case, query_payload=query_payload))

    coverage = _query_eval_coverage(case_results=case_results)
    contract_checks = _query_eval_contract_checks(
        contract=contract,
        case_results=case_results,
        coverage=coverage,
        source_set_id=resolved_source_set_id,
    )
    passed = all(result["passed"] for result in case_results) and all(
        check["passed"] for check in contract_checks
    )
    hard_negative_case_count = sum(
        1 for result in case_results if result.get("case_type") == "hard_negative"
    )
    resolved_output_path = output_path or _default_query_eval_output_path(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        review_id=resolved_review_id,
    )
    payload = {
        "schema_version": KNOWLEDGE_GRAPH_QUERY_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": str(contract["contract_id"]),
        "contract_id": str(contract["contract_id"]),
        "contract_version": str(contract.get("version") or ""),
        "source_set_id": resolved_source_set_id,
        "review_id": resolved_review_id,
        "created_at": _utc_now(),
        "eval_path": str(eval_path),
        "contract": {
            "path": str(eval_path),
            "sha256": hashlib.sha256(eval_path.read_bytes()).hexdigest(),
        },
        "graph_path": str(resolved_graph_path),
        "graph_sha256": sha256_file(resolved_graph_path) if resolved_graph_path.exists() else None,
        "passed": passed,
        "case_count": len(case_results),
        "hard_negative_case_count": hard_negative_case_count,
        "query_type_count": len(coverage["query_types"]),
        "query_types": coverage["query_types"],
        "freshness_warning_case_count": sum(
            1 for result in case_results if result.get("freshness_warning_count")
        ),
        "case_results": case_results,
        "contract_checks": contract_checks,
        "checks": contract_checks,
        "summary": {
            "passed": passed,
            "source_set_id": resolved_source_set_id,
            "review_id": resolved_review_id,
            "case_count": len(case_results),
            "hard_negative_case_count": hard_negative_case_count,
            "query_type_count": len(coverage["query_types"]),
            "failed_case_ids": [
                str(result["case_id"]) for result in case_results if not result["passed"]
            ],
            "failed_contract_check_names": [
                str(check["name"]) for check in contract_checks if not check["passed"]
            ],
            "freshness_warning_case_count": sum(
                1 for result in case_results if result.get("freshness_warning_count")
            ),
            "output_path": str(resolved_output_path),
        },
    }
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return KnowledgeGraphQueryEvalResult(
        output_path=resolved_output_path,
        summary=payload["summary"],
        payload=payload,
    )


def _evaluate_query_case(*, case: dict[str, Any], query_payload: dict[str, Any]) -> dict[str, Any]:
    results = _dict_list(query_payload.get("results"))
    failures = []
    min_results = _int_or_none(case.get("expected_min_results"))
    max_results = _int_or_none(case.get("expected_max_results"))
    if min_results is not None and len(results) < min_results:
        failures.append(
            {"metric": "result_count", "expected_min": min_results, "actual": len(results)}
        )
    if max_results is not None and len(results) > max_results:
        failures.append(
            {"metric": "result_count", "expected_max": max_results, "actual": len(results)}
        )
    failures.extend(
        _missing_expected_values(
            metric="expected_node_ids",
            expected=_string_list(case.get("expected_node_ids")),
            actual=[str(result.get("node_id") or "") for result in results],
        )
    )
    failures.extend(
        _missing_expected_values(
            metric="expected_node_types",
            expected=_string_list(case.get("expected_node_types")),
            actual=[str(result.get("node_type") or "") for result in results],
        )
    )
    failures.extend(
        _missing_expected_values(
            metric="expected_edge_types",
            expected=_string_list(case.get("expected_edge_types")),
            actual=[str(result.get("edge_type") or "") for result in results],
        )
    )
    failures.extend(
        _missing_expected_values(
            metric="expected_citation_labels",
            expected=_string_list(case.get("expected_citation_labels")),
            actual=[
                str(citation.get("citation_label") or "")
                for result in results
                for citation in _dict_list(result.get("citations"))
            ],
        )
    )
    if not bool(query_payload.get("passed")):
        failures.append(
            {
                "metric": "query_payload_passed",
                "failure_reasons": query_payload.get("failure_reasons", []),
            }
        )
    return {
        "case_id": str(case["case_id"]),
        "case_type": "hard_negative" if bool(case.get("hard_negative")) else "positive",
        "query_type": query_payload["request"]["query_type"],
        "query_id": query_payload["query_id"],
        "result_count": len(results),
        "freshness_warning_count": len(query_payload.get("freshness_warnings", [])),
        "passed": not failures,
        "failures": failures,
        "expected": _compact_dict(
            {
                "expected_min_results": min_results,
                "expected_max_results": max_results,
                "expected_node_ids": _string_list(case.get("expected_node_ids")),
                "expected_node_types": _string_list(case.get("expected_node_types")),
                "expected_edge_types": _string_list(case.get("expected_edge_types")),
                "expected_citation_labels": _string_list(case.get("expected_citation_labels")),
            }
        ),
        "actual": {
            "node_ids": [result.get("node_id") for result in results if result.get("node_id")],
            "node_types": sorted(
                {str(result.get("node_type")) for result in results if result.get("node_type")}
            ),
            "edge_types": sorted(
                {str(result.get("edge_type")) for result in results if result.get("edge_type")}
            ),
            "citation_labels": sorted(
                {
                    str(citation.get("citation_label"))
                    for result in results
                    for citation in _dict_list(result.get("citations"))
                    if citation.get("citation_label")
                }
            ),
        },
    }


def _query_eval_coverage(*, case_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {"query_types": sorted({str(result["query_type"]) for result in case_results})}


def _query_eval_contract_checks(
    *,
    contract: dict[str, Any],
    case_results: list[dict[str, Any]],
    coverage: dict[str, Any],
    source_set_id: str,
) -> list[dict[str, Any]]:
    required_query_types = _string_list(contract.get("required_query_types"))
    missing_query_types = sorted(set(required_query_types) - set(coverage["query_types"]))
    hard_negative_case_count = sum(
        1 for result in case_results if result.get("case_type") == "hard_negative"
    )
    min_case_count = int(contract.get("min_case_count") or 0)
    min_hard_negative_case_count = int(contract.get("min_hard_negative_case_count") or 0)
    expected_source_set_id = str(contract.get("source_set_id") or "").strip()
    return [
        {
            "name": "knowledge_graph_query_eval_source_set_matches",
            "passed": not expected_source_set_id or expected_source_set_id == source_set_id,
            "expected": expected_source_set_id or source_set_id,
            "actual": source_set_id,
        },
        {
            "name": "knowledge_graph_query_eval_case_count",
            "passed": len(case_results) >= min_case_count,
            "expected_min": min_case_count,
            "actual": len(case_results),
        },
        {
            "name": "knowledge_graph_query_eval_hard_negative_count",
            "passed": hard_negative_case_count >= min_hard_negative_case_count,
            "expected_min": min_hard_negative_case_count,
            "actual": hard_negative_case_count,
        },
        {
            "name": "knowledge_graph_query_eval_required_query_types",
            "passed": not missing_query_types,
            "expected": required_query_types,
            "actual": coverage["query_types"],
            "missing": missing_query_types,
        },
        {
            "name": "knowledge_graph_query_eval_cases_pass",
            "passed": all(result["passed"] for result in case_results),
            "failed_case_ids": [
                str(result["case_id"]) for result in case_results if not result["passed"]
            ],
        },
    ]


def _load_eval_contract(eval_path: Path) -> dict[str, Any]:
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"knowledge graph query eval contract must be an object: {eval_path}")
    if payload.get("schema_version") != "knowledge-graph-query-eval-v1":
        raise ValueError(
            "knowledge graph query eval contract must declare "
            "schema_version='knowledge-graph-query-eval-v1'"
        )
    if not str(payload.get("contract_id") or "").strip():
        raise ValueError("knowledge graph query eval contract requires contract_id")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("knowledge graph query eval contract requires cases")
    seen_case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("knowledge graph query eval cases must be objects")
        case_id = str(case.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("knowledge graph query eval case requires case_id")
        if case_id in seen_case_ids:
            raise ValueError(f"duplicate knowledge graph query eval case_id {case_id!r}")
        seen_case_ids.add(case_id)
        _normalize_query_type(str(case.get("query_type") or "keyword"))
    return payload


def _default_query_eval_output_path(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str | None,
) -> Path:
    if review_id:
        return output_dir / "reviews" / review_id / "knowledge_graph" / DEFAULT_QUERY_EVAL_RESULTS_FILENAME
    return (
        output_dir
        / "derived"
        / source_set_id
        / "knowledge_graph"
        / DEFAULT_QUERY_EVAL_RESULTS_FILENAME
    )


def _missing_expected_values(
    *,
    metric: str,
    expected: list[str],
    actual: list[str],
) -> list[dict[str, Any]]:
    actual_set = set(actual)
    missing = [value for value in expected if value not in actual_set]
    if not missing:
        return []
    return [{"metric": metric, "missing": missing, "actual": sorted(actual_set)}]


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return int(value)
    return None
