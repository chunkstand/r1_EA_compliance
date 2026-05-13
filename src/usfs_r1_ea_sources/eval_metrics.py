from __future__ import annotations

from math import log2
from pathlib import Path
from typing import Any, Iterable, Sequence
import json

from .records import sha256_file


def rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 6)


def average(values: Iterable[float]) -> float:
    items = [float(value) for value in values]
    if not items:
        return 1.0
    return round(sum(items) / len(items), 6)


def first_relevant_rank(relevance: Sequence[bool]) -> int | None:
    for index, is_relevant in enumerate(relevance, start=1):
        if is_relevant:
            return index
    return None


def reciprocal_rank(relevance: Sequence[bool]) -> float:
    rank = first_relevant_rank(relevance)
    if rank is None:
        return 0.0
    return round(1.0 / rank, 6)


def dcg_at_k(relevance: Sequence[bool], *, k: int | None = None) -> float:
    if k is None:
        k = len(relevance)
    score = 0.0
    for index, is_relevant in enumerate(relevance[:k], start=1):
        if is_relevant:
            score += 1.0 / log2(index + 1)
    return score


def ndcg_at_k(
    relevance: Sequence[bool],
    *,
    relevant_count: int,
    k: int | None = None,
) -> float:
    if relevant_count <= 0:
        return 1.0
    if k is None:
        k = len(relevance)
    actual = dcg_at_k(relevance, k=k)
    ideal = sum(1.0 / log2(index + 1) for index in range(1, min(k, relevant_count) + 1))
    if ideal <= 0:
        return 1.0
    return round(actual / ideal, 6)


def metric_threshold_check(thresholds: object, metrics: dict[str, Any]) -> dict[str, Any]:
    failures = []
    threshold_map = thresholds if isinstance(thresholds, dict) else {}
    for metric_name, threshold in threshold_map.items():
        actual = metrics.get(metric_name)
        if not isinstance(actual, int | float):
            failures.append(
                {
                    "metric": metric_name,
                    "reason": "metric_missing",
                    "actual": actual,
                }
            )
            continue
        if not isinstance(threshold, dict):
            failures.append(
                {
                    "metric": metric_name,
                    "reason": "invalid_threshold",
                    "actual": actual,
                }
            )
            continue
        if "min" in threshold and actual < float(threshold["min"]):
            failures.append(
                {
                    "metric": metric_name,
                    "min": float(threshold["min"]),
                    "actual": actual,
                }
            )
        if "max" in threshold and actual > float(threshold["max"]):
            failures.append(
                {
                    "metric": metric_name,
                    "max": float(threshold["max"]),
                    "actual": actual,
                }
            )
    return {
        "name": "metric_thresholds_met",
        "passed": not failures,
        "details": {"failures": failures},
    }


def read_json_payload(path: Path, *, label: str) -> dict | list:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict | list):
        raise ValueError(f"{label} must contain a JSON object or JSON list.")
    return payload


def contract_snapshot(
    *,
    contract_path: Path,
    contract: dict[str, Any],
    case_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": contract.get("schema_version"),
        "eval_id": contract.get("eval_id"),
        "coverage_requirements": contract.get("coverage_requirements", {}),
        "metric_thresholds": contract.get("metric_thresholds", {}),
        "case_count": case_count,
        "sha256": sha256_file(contract_path),
    }
