from __future__ import annotations

from collections import defaultdict
import hashlib
from typing import Any

from .applicability_contract_support import strings
from .applicability_decision_arbitration import flatten_groups
from .applicability_decision_arbitration import missing_trigger_groups


SEARCH_COVERAGE_CERTIFICATES_SCHEMA_VERSION = "search-coverage-certificates-v0"

SOURCE_QUERY_TYPES = {
    "exact_keyword",
    "bm25",
    "metadata_filter",
    "source_role",
    "authority_category",
    "citation",
}
PACKAGE_QUERY_TYPES = {"package_section", "graph_seed"}


def records_by_candidate(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_candidate[str(record.get("candidate_authority_id") or "")].append(record)
    return by_candidate


def coverage_boundary(
    *,
    candidate: dict[str, Any],
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    requirements = candidate.get("search_coverage_requirements") or []
    required_query_types = sorted(
        {
            query_type
            for requirement in requirements
            for query_type in strings(requirement.get("required_query_types"))
        }
        or set(strings((candidate.get("retrieval_contract") or {}).get("required_query_types")))
    )
    executed_query_types = sorted(
        {
            str(row.get("query_type"))
            for row in retrieval_rows
            if str(row.get("query_type") or "")
        }
    )
    missing_query_types = sorted(set(required_query_types) - set(executed_query_types))
    source_hashes = sorted(
        {
            str((row.get("searched_index") or {}).get("searched_index_hash") or "")
            for row in retrieval_rows
            if row.get("query_type") in SOURCE_QUERY_TYPES
            and (row.get("searched_index") or {}).get("searched_index_hash")
        }
    )
    package_hashes = sorted(
        {
            str((row.get("searched_index") or {}).get("graph_artifact_hash") or "")
            for row in retrieval_rows
            if row.get("query_type") in PACKAGE_QUERY_TYPES
            and (row.get("searched_index") or {}).get("graph_artifact_hash")
        }
    )
    requires_source_index_hash = any(
        bool(requirement.get("requires_searched_index_hash"))
        for requirement in requirements
    )
    source_index_hash_required = requires_source_index_hash or any(
        query_type in SOURCE_QUERY_TYPES for query_type in required_query_types
    )
    graph_required = any(
        "applicability_graph_trace" in set(strings(requirement.get("required_artifacts")))
        for requirement in requirements
    )
    coverage_sufficient = (
        bool(retrieval_rows)
        and not missing_query_types
        and (not source_index_hash_required or bool(source_hashes))
        and bool(package_hashes)
        and (not graph_required or bool(graph_rows))
    )
    return {
        "coverage_sufficient": coverage_sufficient,
        "required_query_variants": required_query_types,
        "executed_query_variants": executed_query_types,
        "missing_query_variants": missing_query_types,
        "package_sections_searched": sorted(
            {
                str(result.get("section_family"))
                for row in retrieval_rows
                for result in row.get("ranked_results") or []
                if result.get("result_kind") in {"package_fact", "package_section"}
                and result.get("section_family")
            }
        ),
        "source_indexes_searched": sorted(
            {
                str((row.get("searched_index") or {}).get("index_path") or "")
                for row in retrieval_rows
                if row.get("query_type") in SOURCE_QUERY_TYPES
                and (row.get("searched_index") or {}).get("index_path")
            }
        ),
        "metadata_filters_searched": [
            row.get("source_filters") or {}
            for row in retrieval_rows
            if row.get("query_type") in {"metadata_filter", "source_role"}
        ],
        "graph_neighborhoods_searched": sorted(
            {
                relationship
                for row in graph_rows
                for relationship in row.get("relationship_types") or []
                if relationship
            }
        ),
        "searched_artifact_hashes": sorted(set(source_hashes + package_hashes)),
        "source_index_hash_required": source_index_hash_required,
        "source_index_hash_present": bool(source_hashes),
        "package_graph_hash_present": bool(package_hashes),
        "required_artifacts": sorted(
            {
                artifact
                for requirement in requirements
                for artifact in strings(requirement.get("required_artifacts"))
            }
        ),
        "coverage_classes": sorted(
            {
                str(requirement.get("coverage_class"))
                for requirement in requirements
                if requirement.get("coverage_class")
            }
        ),
    }


def coverage_certificate(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    created_at: str,
    candidate: dict[str, Any],
    decision: dict[str, Any],
    coverage_boundary: dict[str, Any],
    authority_universe_sha256: str,
    package_fact_graph_sha256: str,
    retrieval_trace_sha256: str,
    graph_trace_sha256: str,
    retrieval_rows: list[dict[str, Any]],
    graph_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_id = decision["candidate_authority_id"]
    coverage_result = "sufficient" if coverage_boundary["coverage_sufficient"] else "insufficient"
    if decision["status"] == "needs_adjudication":
        coverage_result = "adjudication_required"
    certificate_id = _stable_id(
        "search-coverage-certificate",
        applicability_run_id,
        candidate_id,
        decision["status"],
        decision["basis_type"],
    )
    rejected_ids = [
        str(result.get("result_id"))
        for row in retrieval_rows
        for result in row.get("ranked_results") or []
        if result.get("selected_status") == "rejected" and result.get("result_id")
    ]
    return {
        "coverage_certificate_id": certificate_id,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "authority_universe_sha256": authority_universe_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "retrieval_trace_sha256": retrieval_trace_sha256,
        "graph_trace_sha256": graph_trace_sha256,
        "covered_candidate_authority_ids": [candidate_id],
        "covered_decision_ids": [decision["decision_id"]],
        "coverage_class": decision["basis_type"],
        "required_query_variants": coverage_boundary["required_query_variants"],
        "executed_query_variants": coverage_boundary["executed_query_variants"],
        "missing_query_variants": coverage_boundary["missing_query_variants"],
        "package_sections_searched": coverage_boundary["package_sections_searched"],
        "source_indexes_searched": coverage_boundary["source_indexes_searched"],
        "metadata_filters_searched": coverage_boundary["metadata_filters_searched"],
        "graph_neighborhoods_searched": coverage_boundary["graph_neighborhoods_searched"],
        "searched_artifact_hashes": coverage_boundary["searched_artifact_hashes"],
        "coverage_result": coverage_result,
        "trigger_terms_searched": flatten_groups(candidate.get("positive_trigger_groups")),
        "negative_trigger_terms_searched": flatten_groups(
            candidate.get("negative_trigger_groups")
        ),
        "missing_trigger_groups": missing_trigger_groups(decision),
        "rejected_evidence_ids": sorted(set(rejected_ids)),
        "graph_path_ids": [
            str(row.get("graph_path_id"))
            for row in graph_rows
            if row.get("graph_path_id")
        ],
        "rationale": _coverage_rationale(coverage_result),
    }


def _coverage_rationale(coverage_result: str) -> str:
    if coverage_result == "sufficient":
        return (
            "Required retrieval variants and graph neighborhoods were recorded for this "
            "authority predicate."
        )
    if coverage_result == "adjudication_required":
        return "Search coverage was recorded, but the predicate requires adjudication."
    return "Required retrieval variants or graph neighborhoods were missing."


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
