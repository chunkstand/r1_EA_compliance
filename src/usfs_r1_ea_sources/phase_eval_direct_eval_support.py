from __future__ import annotations

from pathlib import Path
from typing import Any
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE_EVAL_DIRECT_EVAL_CONTRACT_PATH = (
    REPO_ROOT / "config" / "phase_eval_direct_eval_v1.json"
)
PHASE_EVAL_DIRECT_EVAL_SCHEMA_VERSION = "phase-eval-direct-eval-v1"
UPSTREAM_EVALUATION_RESULTS_SCHEMA_VERSION = "upstream-evaluation-results-v0"
DOWNSTREAM_DIRECT_EVAL_MANIFEST_SCHEMA_VERSION = "downstream-direct-eval-v1"
REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION = "real-package-review-coverage-v1"
REAL_PACKAGE_REVIEW_COVERAGE_RESULTS_SCHEMA_VERSION = (
    "real-package-review-coverage-results-v1"
)
V1_EA_EVAL_RESULTS_SCHEMA_VERSION = "v1-ea-real-review-eval-results-v0"
FOREST_PLAN_PROFILE_EVAL_RESULTS_SCHEMA_VERSION = (
    "region1-forest-plan-profile-eval-results-v1"
)
FOREST_PLAN_COMPONENT_EVAL_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-eval-coverage-v1"
)
FOREST_PLAN_COMPONENT_EVAL_COVERAGE_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-eval-coverage-results-v1"
)
FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION = (
    "forest-plan-component-retrieval-eval-results-v1"
)
SEMANTIC_GRAPH_EVAL_RESULTS_SCHEMA_VERSION = "semantic-graph-eval-results-v1"
KNOWLEDGE_GRAPH_QUERY_EVAL_RESULTS_SCHEMA_VERSION = (
    "knowledge-graph-query-eval-results-v1"
)
EXTRACTION_FIDELITY_EVAL_RESULTS_SCHEMA_VERSION = (
    "extraction-fidelity-eval-results-v0"
)
SOURCE_SET_COVERAGE_CLASSES = {"direct_eval_required", "validation_only_allowed"}
REVIEW_COVERAGE_CLASSES = {
    "required_for_declared_review_contract",
    "not_required_for_ad_hoc_review",
}
SOURCE_SET_PHASE_PRODUCERS = {
    "downstream_direct_evaluation",
    "eval_context_graph_evaluation",
    "extraction_fidelity_evaluation",
    "forest_plan_component_retrieval_evaluation",
    "forest_plan_profile_evaluation",
    "knowledge_graph_query_evaluation",
    "phase_eval",
    "semantic_graph_direct_evaluation",
    "upstream_evaluation",
}


def _resolve_repo_path(base_dir: Path, value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else (base_dir / path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    return _read_json(path) if Path(path).exists() else None


def _numeric(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _int_or_none(value: Any) -> int | None:
    numeric = _numeric(value)
    return int(numeric) if numeric is not None else None


def _first_numeric(*values: Any) -> int | None:
    for value in values:
        numeric = _numeric(value)
        if numeric is not None:
            return int(numeric)
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _profile_metric_sum(profiles: Any, key: str) -> int | None:
    if not isinstance(profiles, list):
        return None
    total = 0
    saw_value = False
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        numeric = _numeric(profile.get(key))
        if numeric is None:
            continue
        total += int(numeric)
        saw_value = True
    return total if saw_value else None


def _failed_contract_check_names(result: dict[str, Any]) -> list[str]:
    checks = result.get("contract_checks")
    if not isinstance(checks, list):
        return []
    return [
        str(check.get("name") or "")
        for check in checks
        if isinstance(check, dict) and not bool(check.get("passed"))
    ]


def _metric_value(result: dict[str, Any], key: str) -> int | float | None:
    metrics = result.get("metrics")
    if isinstance(metrics, dict):
        return _numeric(metrics.get(key))
    return None


def _coverage_requirement_actual(result: dict[str, Any], key: str) -> int | None:
    if key == "case_count":
        return _first_numeric(
            result.get("case_count"),
            result.get("query_count"),
            _metric_value(result, "case_count"),
        )
    return _first_numeric(result.get(key), _metric_value(result, key))


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
