from __future__ import annotations

from pathlib import Path
from typing import Any

from .applicability_validation_support import first_present
from .applicability_validation_support import optional_file_sha256
from .applicability_validation_support import read_json_if_exists
from .applicability_validation_support import read_jsonl_if_exists

__all__ = [
    "artifact_hashes",
    "build_validation_artifact_paths",
    "first_present_run_id",
    "first_present_source_set_id",
    "load_validation_artifacts",
]


def build_validation_artifact_paths(
    *,
    applicability_dir: Path,
    authority_universe_path: Path | None,
    package_fact_graph_path: Path | None,
    package_applicability_context_path: Path | None,
    package_fact_graph_validation_path: Path | None,
    retrieval_trace_path: Path | None,
    graph_trace_path: Path | None,
    decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    search_coverage_certificates_path: Path | None,
    provenance_path: Path | None,
) -> dict[str, Path]:
    return {
        "authority_universe": Path(authority_universe_path)
        if authority_universe_path
        else applicability_dir / "authority_universe_snapshot.json",
        "package_fact_graph": Path(package_fact_graph_path)
        if package_fact_graph_path
        else applicability_dir / "package_fact_graph.json",
        "package_applicability_context": Path(package_applicability_context_path)
        if package_applicability_context_path
        else applicability_dir / "package_applicability_context.json",
        "package_fact_graph_validation": Path(package_fact_graph_validation_path)
        if package_fact_graph_validation_path
        else applicability_dir / "package_fact_graph_validation.json",
        "retrieval_trace": Path(retrieval_trace_path)
        if retrieval_trace_path
        else applicability_dir / "applicability_retrieval_trace.jsonl",
        "graph_trace": Path(graph_trace_path)
        if graph_trace_path
        else applicability_dir / "applicability_graph_trace.jsonl",
        "decisions": Path(decisions_path)
        if decisions_path
        else applicability_dir / "applicability_decisions.jsonl",
        "applicable_authorities": Path(applicable_authorities_path)
        if applicable_authorities_path
        else applicability_dir / "applicable_authorities.json",
        "non_applicable_authorities": Path(non_applicable_authorities_path)
        if non_applicable_authorities_path
        else applicability_dir / "non_applicable_authorities.json",
        "search_coverage_certificates": Path(search_coverage_certificates_path)
        if search_coverage_certificates_path
        else applicability_dir / "search_coverage_certificates.json",
        "provenance": Path(provenance_path)
        if provenance_path
        else applicability_dir / "applicability_provenance.json",
    }


def load_validation_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "authority_universe": read_json_if_exists(paths["authority_universe"]),
        "package_fact_graph": read_json_if_exists(paths["package_fact_graph"]),
        "package_applicability_context": read_json_if_exists(
            paths["package_applicability_context"]
        ),
        "package_fact_graph_validation": read_json_if_exists(
            paths["package_fact_graph_validation"]
        ),
        "retrieval_rows": read_jsonl_if_exists(paths["retrieval_trace"]),
        "graph_rows": read_jsonl_if_exists(paths["graph_trace"]),
        "decisions": read_jsonl_if_exists(paths["decisions"]),
        "applicable_authorities": read_json_if_exists(paths["applicable_authorities"]),
        "non_applicable_authorities": read_json_if_exists(paths["non_applicable_authorities"]),
        "search_coverage_certificates": read_json_if_exists(
            paths["search_coverage_certificates"]
        ),
        "provenance": read_json_if_exists(paths["provenance"]),
    }


def artifact_hashes(paths: dict[str, Path], artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        "authority_universe_sha256": artifacts["authority_universe"].get(
            "authority_universe_sha256"
        ),
        "package_manifest_sha256": first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks_sha256": first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
        "package_fact_graph_sha256": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_context_sha256": artifacts["package_applicability_context"].get(
            "package_context_sha256"
        ),
        "retrieval_trace_sha256": optional_file_sha256(paths["retrieval_trace"]),
        "graph_trace_sha256": optional_file_sha256(paths["graph_trace"]),
        "search_coverage_certificates_sha256": optional_file_sha256(
            paths["search_coverage_certificates"]
        ),
        "applicability_decisions_sha256": optional_file_sha256(paths["decisions"]),
        "applicable_authorities_sha256": optional_file_sha256(paths["applicable_authorities"]),
        "non_applicable_authorities_sha256": optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "applicability_provenance_sha256": optional_file_sha256(paths["provenance"]),
        "catalog_sha256": artifacts["authority_universe"].get("catalog_sha256"),
        "source_claims_sha256": artifacts["authority_universe"].get("source_claims_sha256"),
        "rule_claim_links_sha256": artifacts["authority_universe"].get(
            "rule_claim_links_sha256"
        ),
        "forest_plan_component_inventory_sha256": artifacts["authority_universe"].get(
            "forest_plan_component_inventory_sha256"
        ),
    }


def _source_set_from_decisions(decisions: list[dict[str, Any]]) -> str | None:
    for decision in decisions:
        source_set_id = str(decision.get("source_set_id") or "").strip()
        if source_set_id:
            return source_set_id
    return None


def first_present_source_set_id(artifacts: dict[str, Any]) -> str | None:
    for key in (
        "authority_universe",
        "package_fact_graph",
        "package_applicability_context",
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        value = str((artifacts.get(key) or {}).get("source_set_id") or "").strip()
        if value:
            return value
    return _source_set_from_decisions(artifacts.get("decisions") or [])


def first_present_run_id(artifacts: dict[str, Any]) -> str | None:
    for key in (
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        value = str((artifacts.get(key) or {}).get("applicability_run_id") or "").strip()
        if value:
            return value
    for decision in artifacts.get("decisions") or []:
        value = str(decision.get("applicability_run_id") or "").strip()
        if value:
            return value
    return None
