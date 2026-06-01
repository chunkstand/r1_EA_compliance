from __future__ import annotations

from pathlib import Path
from typing import Any

from .phase_eval_direct_eval_context_graph import eval_context_graph_phase_status
from .phase_eval_direct_eval_knowledge_graph import knowledge_graph_query_phase_status


def graph_direct_eval_phase_status(
    *,
    producer: str,
    phase_name: str,
    coverage_class: str,
    lane_id: str,
    source_set_id: str,
    output_dir: Path,
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    if producer == "knowledge_graph_query_evaluation":
        return knowledge_graph_query_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=lane_id,
            source_set_id=source_set_id,
            output_dir=output_dir,
            results_path_value=spec.get("results_path"),
            results_filename=str(spec.get("results_filename") or ""),
            expected_contract_id=str(spec.get("expected_contract_id") or ""),
            contract_path_value=spec.get("contract_path"),
        )
    if producer == "eval_context_graph_evaluation":
        return eval_context_graph_phase_status(
            phase_name=phase_name,
            coverage_class=coverage_class,
            lane_id=lane_id,
            source_set_id=source_set_id,
            output_dir=output_dir,
            results_path_value=spec.get("results_path"),
            expected_contract_id=str(spec.get("expected_contract_id") or ""),
            contract_path_value=spec.get("contract_path"),
        )
    return None
