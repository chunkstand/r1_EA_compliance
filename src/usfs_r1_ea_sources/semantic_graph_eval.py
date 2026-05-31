from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import tempfile
from typing import Any

from .artifact_utils import _source_set_id_from_catalog
from .artifact_utils import _utc_now
from .authority_ontology_validate import AUTHORITY_ONTOLOGY_VALIDATION_SCHEMA_VERSION
from .authority_ontology_validate import run_authority_ontology_validate
from .authority_relationship_eval import AUTHORITY_RELATIONSHIP_EVAL_SCHEMA_VERSION
from .authority_relationship_eval import run_authority_relationship_eval
from .citation_alias_eval import CITATION_ALIAS_EVAL_SCHEMA_VERSION
from .citation_alias_eval import run_citation_alias_eval
from .graph_accuracy_eval import GRAPH_ACCURACY_EVAL_SCHEMA_VERSION
from .graph_accuracy_eval import run_graph_accuracy_eval
from .graph_health_eval import GRAPH_HEALTH_EVAL_SCHEMA_VERSION
from .graph_health_eval import run_graph_health_eval


SEMANTIC_GRAPH_EVAL_SCHEMA_VERSION = "semantic-graph-eval-results-v1"
DEFAULT_SEMANTIC_GRAPH_EVAL_PATH = Path("config/semantic_graph_direct_eval_v1.json")
DEFAULT_RESULTS_FILENAME = "semantic_graph_eval_results.json"
DEFAULT_GRAPH_FILENAME = "nepa_3d_graph.json"
DEFAULT_PROVING_REPORT_FILENAME = "proving_slice_report.json"


@dataclass(frozen=True)
class SemanticGraphEvalResult:
    output_path: Path
    summary: dict[str, Any]


def run_semantic_graph_eval(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    eval_path: Path = DEFAULT_SEMANTIC_GRAPH_EVAL_PATH,
    output_path: Path | None = None,
) -> SemanticGraphEvalResult:
    output_dir = Path(output_dir)
    eval_path = Path(eval_path)
    contract = _load_contract(eval_path)
    resolved_source_set_id = source_set_id or _source_set_id_from_catalog(output_dir)
    knowledge_graph_dir = output_dir / "derived" / resolved_source_set_id / "knowledge_graph"
    resolved_output_path = output_path or knowledge_graph_dir / DEFAULT_RESULTS_FILENAME

    _refresh_positive_reports(
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
    )
    positive_results = _positive_report_results(
        contract=contract,
        knowledge_graph_dir=knowledge_graph_dir,
        source_set_id=resolved_source_set_id,
    )
    negative_results = _negative_case_results(
        contract=contract,
        output_dir=output_dir,
        source_set_id=resolved_source_set_id,
        knowledge_graph_dir=knowledge_graph_dir,
    )
    coverage_categories = sorted(
        {
            category
            for result in [*positive_results, *negative_results]
            for category in result.get("coverage_categories", [])
        }
    )
    case_count = len(positive_results) + len(negative_results)
    hard_negative_case_count = len(negative_results)
    threshold_failures = _threshold_failures(
        contract=contract,
        positive_results=positive_results,
        negative_results=negative_results,
        coverage_categories=coverage_categories,
        case_count=case_count,
        hard_negative_case_count=hard_negative_case_count,
        source_set_id=resolved_source_set_id,
    )
    contract_checks = _contract_checks(
        contract=contract,
        threshold_failures=threshold_failures,
        coverage_categories=coverage_categories,
        case_count=case_count,
        hard_negative_case_count=hard_negative_case_count,
        source_set_id=resolved_source_set_id,
    )
    passed = not threshold_failures and all(check["passed"] for check in contract_checks)
    payload = {
        "schema_version": SEMANTIC_GRAPH_EVAL_SCHEMA_VERSION,
        "eval_id": str(contract["contract_id"]),
        "contract_id": str(contract["contract_id"]),
        "contract_version": str(contract.get("version") or ""),
        "source_set_id": resolved_source_set_id,
        "created_at": _utc_now(),
        "eval_path": str(eval_path),
        "contract": {
            "path": str(eval_path),
            "sha256": hashlib.sha256(eval_path.read_bytes()).hexdigest(),
        },
        "passed": passed,
        "case_count": case_count,
        "positive_case_count": len(positive_results),
        "hard_negative_case_count": hard_negative_case_count,
        "coverage_categories": coverage_categories,
        "positive_results": positive_results,
        "negative_results": negative_results,
        "threshold_failures": threshold_failures,
        "contract_checks": contract_checks,
        "checks": contract_checks,
        "summary": {
            "passed": passed,
            "source_set_id": resolved_source_set_id,
            "case_count": case_count,
            "positive_case_count": len(positive_results),
            "hard_negative_case_count": hard_negative_case_count,
            "coverage_category_count": len(coverage_categories),
            "failed_positive_case_ids": [
                str(result["case_id"])
                for result in positive_results
                if not bool(result.get("passed"))
            ],
            "failed_negative_case_ids": [
                str(result["case_id"])
                for result in negative_results
                if not bool(result.get("passed"))
            ],
            "output_path": str(resolved_output_path),
        },
    }
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return SemanticGraphEvalResult(
        output_path=resolved_output_path,
        summary=payload["summary"],
    )


def _load_contract(eval_path: Path) -> dict[str, Any]:
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "semantic-graph-direct-eval-v1":
        raise ValueError(
            "semantic graph direct-eval contract must declare "
            "schema_version='semantic-graph-direct-eval-v1'"
        )
    if not str(payload.get("contract_id") or "").strip():
        raise ValueError("semantic graph direct-eval contract requires contract_id")
    if not isinstance(payload.get("positive_reports"), list) or not payload["positive_reports"]:
        raise ValueError("semantic graph direct-eval contract requires positive_reports")
    if not isinstance(payload.get("negative_cases"), list) or not payload["negative_cases"]:
        raise ValueError("semantic graph direct-eval contract requires negative_cases")
    return payload


def _refresh_positive_reports(*, output_dir: Path, source_set_id: str) -> None:
    run_authority_ontology_validate(output_dir=output_dir, source_set_id=source_set_id)
    run_authority_relationship_eval(output_dir=output_dir, source_set_id=source_set_id)
    run_citation_alias_eval(output_dir=output_dir, source_set_id=source_set_id)
    run_graph_health_eval(output_dir=output_dir, source_set_id=source_set_id)
    run_graph_accuracy_eval(output_dir=output_dir, source_set_id=source_set_id)


def _positive_report_results(
    *,
    contract: dict[str, Any],
    knowledge_graph_dir: Path,
    source_set_id: str,
) -> list[dict[str, Any]]:
    results = []
    for spec in contract.get("positive_reports", []):
        report_path = knowledge_graph_dir / str(spec["report_path"])
        report = _read_json_if_exists(report_path)
        failed_check_names = _failed_check_names(report)
        source_set_matches = (report or {}).get("source_set_id") == source_set_id
        schema_matches = (report or {}).get("schema_version") == spec.get("schema_version")
        report_passed = _report_passed(report)
        results.append(
            {
                "case_id": str(spec["report_id"]),
                "case_type": "positive_report",
                "coverage_categories": _string_list(spec.get("coverage_categories")),
                "report_path": str(report_path),
                "report_present": isinstance(report, dict),
                "expected_schema_version": spec.get("schema_version"),
                "actual_schema_version": (report or {}).get("schema_version"),
                "source_set_matches": source_set_matches,
                "report_passed": report_passed,
                "failed_check_names": failed_check_names,
                "passed": bool(
                    isinstance(report, dict)
                    and schema_matches
                    and source_set_matches
                    and report_passed
                    and not failed_check_names
                ),
            }
        )
    return results


def _negative_case_results(
    *,
    contract: dict[str, Any],
    output_dir: Path,
    source_set_id: str,
    knowledge_graph_dir: Path,
) -> list[dict[str, Any]]:
    graph_path = knowledge_graph_dir / DEFAULT_GRAPH_FILENAME
    proving_report_path = (
        output_dir
        / "derived"
        / source_set_id
        / "source_register_proving"
        / DEFAULT_PROVING_REPORT_FILENAME
    )
    graph = _read_json_if_exists(graph_path)
    proving_report = _read_json_if_exists(proving_report_path)
    results = []
    for spec in contract.get("negative_cases", []):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            try:
                result = _run_negative_case(
                    spec=spec,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    graph=graph,
                    proving_report=proving_report,
                    temp_root=temp_root,
                )
            except Exception as exc:  # pragma: no cover - defensive artifact detail
                result = {
                    "case_id": str(spec.get("case_id") or ""),
                    "case_type": "controlled_negative",
                    "coverage_categories": _string_list(spec.get("coverage_categories")),
                    "mutation": spec.get("mutation"),
                    "evaluator": spec.get("evaluator"),
                    "passed": False,
                    "error": str(exc),
                }
        results.append(result)
    return results


def _run_negative_case(
    *,
    spec: dict[str, Any],
    output_dir: Path,
    source_set_id: str,
    graph: dict[str, Any] | None,
    proving_report: dict[str, Any] | None,
    temp_root: Path,
) -> dict[str, Any]:
    evaluator = str(spec["evaluator"])
    mutation = str(spec["mutation"])
    expected_failed_check_names = set(_string_list(spec.get("expected_failed_check_names")))
    temp_output_dir = temp_root / "source_library"
    temp_kg_dir = temp_output_dir / "derived" / source_set_id / "knowledge_graph"
    temp_kg_dir.mkdir(parents=True, exist_ok=True)
    report_output_path = temp_root / f"{spec['case_id']}_report.json"

    if evaluator in {"authority_ontology", "graph_health", "graph_accuracy"}:
        if not isinstance(graph, dict):
            return _missing_base_artifact_result(spec, "knowledge_graph")
        mutated_graph = _mutated_graph(graph, spec)
        graph_path = temp_kg_dir / DEFAULT_GRAPH_FILENAME
        _write_json(graph_path, mutated_graph)
        if evaluator == "authority_ontology":
            eval_result = run_authority_ontology_validate(
                output_dir=output_dir,
                source_set_id=source_set_id,
                graph_path=graph_path,
                output_path=report_output_path,
            )
        elif evaluator == "graph_health":
            eval_result = run_graph_health_eval(
                output_dir=temp_output_dir,
                source_set_id=source_set_id,
                output_path=report_output_path,
            )
        else:
            eval_result = run_graph_accuracy_eval(
                output_dir=temp_output_dir,
                source_set_id=source_set_id,
                output_path=report_output_path,
            )
    else:
        if not isinstance(proving_report, dict):
            return _missing_base_artifact_result(spec, "proving_report")
        mutated_report = _mutated_proving_report(proving_report, spec)
        proving_report_path = temp_root / "proving_slice_report.json"
        _write_json(proving_report_path, mutated_report)
        if evaluator == "authority_relationships":
            eval_result = run_authority_relationship_eval(
                output_dir=output_dir,
                report_path=proving_report_path,
                output_path=report_output_path,
            )
        elif evaluator == "citation_aliases":
            eval_result = run_citation_alias_eval(
                output_dir=output_dir,
                report_path=proving_report_path,
                output_path=report_output_path,
            )
        else:
            raise ValueError(f"Unsupported semantic graph negative evaluator: {evaluator}")

    report = json.loads(eval_result.output_path.read_text(encoding="utf-8"))
    failed_check_names = set(_failed_check_names(report))
    evaluator_passed = _report_passed(report)
    expected_failure_observed = expected_failed_check_names <= failed_check_names
    return {
        "case_id": str(spec["case_id"]),
        "case_type": "controlled_negative",
        "coverage_categories": _string_list(spec.get("coverage_categories")),
        "mutation": mutation,
        "evaluator": evaluator,
        "expected_failed_check_names": sorted(expected_failed_check_names),
        "actual_failed_check_names": sorted(failed_check_names),
        "evaluator_passed": evaluator_passed,
        "passed": bool(not evaluator_passed and expected_failure_observed),
        "report_path": str(eval_result.output_path),
    }


def _mutated_graph(graph: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    mutated = deepcopy(graph)
    mutation = str(spec["mutation"])
    if mutation == "remove_required_node_type":
        node_type = str(spec["node_type"])
        mutated["nodes"] = [
            node
            for node in mutated.get("nodes", [])
            if str(node.get("node_type") or "") != node_type
        ]
        return mutated
    if mutation == "remove_semantic_lens":
        lens_id = str(spec.get("lens_id") or "semantic_relationships")
        mutated["lens_metadata"] = [
            entry
            for entry in mutated.get("lens_metadata", [])
            if str(entry.get("lens_id") or "") != lens_id
        ]
        return mutated
    if mutation == "remove_authority_path_justification_edges":
        mutated["edges"] = [
            edge
            for edge in mutated.get("edges", [])
            if not (
                str(edge.get("edge_type") or "") == "JUSTIFIED_BY"
                and str(edge.get("source_node_id") or "").startswith("authority_path:")
            )
        ]
        return mutated
    if mutation == "remove_currentness_metadata":
        node_type = str(spec.get("node_type") or "authority_document")
        for node in mutated.get("nodes", []):
            if str(node.get("node_type") or "") == node_type:
                node.pop("currentness_metadata", None)
                break
        return mutated
    raise ValueError(f"Unsupported semantic graph mutation: {mutation}")


def _mutated_proving_report(report: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    mutated = deepcopy(report)
    mutation = str(spec["mutation"])
    if mutation == "set_unknown_relationship_type":
        relationships = mutated["semantic_relationships"]["relationships"]
        relationships[0]["relationship_type"] = "UNKNOWN_RELATIONSHIP"
        mutated["semantic_relationships"]["relationship_type_counts"] = {
            "UNKNOWN_RELATIONSHIP": 1
        }
        return mutated
    if mutation == "remove_relationship_supporting_sources":
        relationships = mutated["semantic_relationships"]["relationships"]
        relationships[0]["supporting_source_record_ids"] = []
        return mutated
    if mutation == "add_alias_identity_collision":
        alias_report = mutated["alias_report"]
        alias_report["identity_collision_count"] = 1
        alias_report["identity_collisions"] = [
            {
                "identity_key": "controlled-negative-collision",
                "authority_document_ids": [
                    "authority_document:controlled-negative-a",
                    "authority_document:controlled-negative-b",
                ],
            }
        ]
        return mutated
    raise ValueError(f"Unsupported semantic graph proving-report mutation: {mutation}")


def _threshold_failures(
    *,
    contract: dict[str, Any],
    positive_results: list[dict[str, Any]],
    negative_results: list[dict[str, Any]],
    coverage_categories: list[str],
    case_count: int,
    hard_negative_case_count: int,
    source_set_id: str,
) -> list[dict[str, Any]]:
    failures = []
    required_source_set_ids = _string_list(contract.get("required_source_set_ids"))
    if required_source_set_ids and source_set_id not in required_source_set_ids:
        failures.append(
            {
                "metric": "source_set_id",
                "expected": required_source_set_ids,
                "actual": source_set_id,
            }
        )
    missing_categories = sorted(
        set(_string_list(contract.get("required_coverage_categories")))
        - set(coverage_categories)
    )
    if missing_categories:
        failures.append(
            {
                "metric": "coverage_categories",
                "expected_missing": [],
                "actual_missing": missing_categories,
            }
        )
    minimum_case_count = int(contract.get("minimum_case_count", 0))
    if case_count < minimum_case_count:
        failures.append(
            {
                "metric": "case_count",
                "min": minimum_case_count,
                "actual": case_count,
            }
        )
    minimum_hard_negative_case_count = int(contract.get("minimum_hard_negative_case_count", 0))
    if hard_negative_case_count < minimum_hard_negative_case_count:
        failures.append(
            {
                "metric": "hard_negative_case_count",
                "min": minimum_hard_negative_case_count,
                "actual": hard_negative_case_count,
            }
        )
    failed_positive_case_ids = [
        str(result["case_id"])
        for result in positive_results
        if not bool(result.get("passed"))
    ]
    if failed_positive_case_ids:
        failures.append(
            {
                "metric": "positive_reports_pass",
                "failed_case_ids": failed_positive_case_ids,
            }
        )
    failed_negative_case_ids = [
        str(result["case_id"])
        for result in negative_results
        if not bool(result.get("passed"))
    ]
    if failed_negative_case_ids:
        failures.append(
            {
                "metric": "controlled_negative_cases",
                "failed_case_ids": failed_negative_case_ids,
            }
        )
    return failures


def _contract_checks(
    *,
    contract: dict[str, Any],
    threshold_failures: list[dict[str, Any]],
    coverage_categories: list[str],
    case_count: int,
    hard_negative_case_count: int,
    source_set_id: str,
) -> list[dict[str, Any]]:
    required_source_set_ids = _string_list(contract.get("required_source_set_ids"))
    required_categories = _string_list(contract.get("required_coverage_categories"))
    return [
        _check(
            "semantic_graph_direct_eval_contract_loaded",
            contract.get("schema_version") == "semantic-graph-direct-eval-v1",
            "semantic-graph-direct-eval-v1",
            contract.get("schema_version"),
        ),
        _check(
            "source_set_id_allowed",
            not required_source_set_ids or source_set_id in required_source_set_ids,
            required_source_set_ids,
            source_set_id,
        ),
        _check(
            "required_coverage_categories_present",
            set(required_categories).issubset(coverage_categories),
            sorted(required_categories),
            coverage_categories,
        ),
        _check(
            "case_count_floor_met",
            case_count >= int(contract.get("minimum_case_count", 0)),
            int(contract.get("minimum_case_count", 0)),
            case_count,
        ),
        _check(
            "hard_negative_case_count_floor_met",
            hard_negative_case_count
            >= int(contract.get("minimum_hard_negative_case_count", 0)),
            int(contract.get("minimum_hard_negative_case_count", 0)),
            hard_negative_case_count,
        ),
        _check(
            "semantic_graph_eval_thresholds_met",
            not threshold_failures,
            [],
            threshold_failures,
        ),
    ]


def _missing_base_artifact_result(spec: dict[str, Any], artifact_name: str) -> dict[str, Any]:
    return {
        "case_id": str(spec.get("case_id") or ""),
        "case_type": "controlled_negative",
        "coverage_categories": _string_list(spec.get("coverage_categories")),
        "mutation": spec.get("mutation"),
        "evaluator": spec.get("evaluator"),
        "passed": False,
        "error": f"missing_base_{artifact_name}",
    }


def _report_passed(report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict):
        return False
    summary = report.get("summary")
    if isinstance(summary, dict) and "passed" in summary:
        return bool(summary.get("passed"))
    if "passed" in report:
        return bool(report.get("passed"))
    return False


def _failed_check_names(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return []
    return [
        str(check.get("name") or "")
        for check in report.get("checks", [])
        if isinstance(check, dict) and not bool(check.get("passed"))
    ]


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _check(name: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }


REPORT_SCHEMA_VERSIONS = {
    "authority_ontology": AUTHORITY_ONTOLOGY_VALIDATION_SCHEMA_VERSION,
    "authority_relationships": AUTHORITY_RELATIONSHIP_EVAL_SCHEMA_VERSION,
    "citation_aliases": CITATION_ALIAS_EVAL_SCHEMA_VERSION,
    "graph_health": GRAPH_HEALTH_EVAL_SCHEMA_VERSION,
    "graph_accuracy": GRAPH_ACCURACY_EVAL_SCHEMA_VERSION,
}
