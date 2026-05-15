from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL_CONTRACT_PATH = REPO_ROOT / "config" / "graph_retrieval_contract_v1.json"
RETRIEVAL_EVAL_PATH = REPO_ROOT / "config" / "graph_retrieval_eval_v1.json"


def test_graph_retrieval_contract_defines_required_modes_and_hybrid_signals() -> None:
    contract = _load_json(RETRIEVAL_CONTRACT_PATH)

    assert contract["schema_version"] == "graph-retrieval-contract-v1"
    mode_ids = _ids(contract["query_modes"], "mode_id")
    signal_ids = _ids(contract["search_signals"], "signal_id")
    unit_ids = _ids(contract["retrieval_units"], "unit_id")

    assert {
        "citation_exact_search",
        "authority_local_hybrid_search",
        "forest_component_support_search",
        "package_applicability_search",
        "global_coverage_search",
        "drift_reasoning_search",
    }.issubset(mode_ids)
    assert {
        "citation",
        "full_text_bm25",
        "metadata_filter",
        "currentness_filter",
        "scope_filter",
        "semantic_vector",
        "structural_similarity",
        "authority_graph_expansion",
        "package_fact_graph_expansion",
        "community_summary",
    }.issubset(signal_ids)
    assert {
        "source_record",
        "evidence_span",
        "source_claim",
        "authority_fragment",
        "forest_plan_component",
        "authority_path",
        "justification_path",
        "community_summary",
    }.issubset(unit_ids)


def test_graph_retrieval_contract_keeps_graph_expansion_bounded() -> None:
    contract = _load_json(RETRIEVAL_CONTRACT_PATH)

    expansion_policies = {
        entry["policy_id"]: entry for entry in contract["graph_expansion_policies"]
    }
    assert "drift_iterative_expansion" in expansion_policies
    assert "package_applicability_expansion" in expansion_policies

    for policy in expansion_policies.values():
        assert policy["max_hops"] >= 1
        assert policy["max_hops"] <= 3
        assert policy["require_provenance"] is True

    local_policy = expansion_policies["authority_local_expansion"]
    assert "IMPLEMENTS" in local_policy["allowed_relationship_types"]
    assert "INTERPRETS" in local_policy["allowed_relationship_types"]

    forest_policy = expansion_policies["forest_component_expansion"]
    assert "SUPPORTS_FOREST_PLAN_COMPONENT" in forest_policy["allowed_relationship_types"]
    assert "GOVERNS_FOREST_UNIT" in forest_policy["allowed_relationship_types"]


def test_graph_retrieval_contract_requires_trace_and_final_evidence_boundaries() -> None:
    contract = _load_json(RETRIEVAL_CONTRACT_PATH)

    trace = contract["trace_requirements"]
    assert {
        "query_text",
        "query_mode",
        "signals_used",
        "filters_applied",
        "selected_results",
        "rejected_results",
        "search_coverage",
    }.issubset(set(trace["required_top_level_fields"]))
    assert {
        "stable_result_id",
        "source_record_id",
        "signal_ranks",
        "fusion_contributions",
        "currentness_decision",
        "scope_decision",
    }.issubset(set(trace["required_selected_result_fields"]))
    assert any(
        "Community summaries may not be used as final controlling evidence"
        in guardrail
        for guardrail in contract["guardrails"]
    )


def test_graph_retrieval_eval_manifest_stays_aligned_with_contract() -> None:
    contract = _load_json(RETRIEVAL_CONTRACT_PATH)
    eval_manifest = _load_json(RETRIEVAL_EVAL_PATH)

    mode_ids = _ids(contract["query_modes"], "mode_id")
    signal_ids = _ids(contract["search_signals"], "signal_id")
    contract_checks = {
        "mode_routing_explicit",
        "hybrid_fusion_configured",
        "graph_expansion_bounded",
        "trace_fields_complete",
        "community_summary_not_final_evidence",
    }

    assert eval_manifest["schema_version"] == "graph-retrieval-eval-v1"
    assert set(eval_manifest["required_query_modes"]).issubset(mode_ids)
    assert set(eval_manifest["required_signal_coverage"]).issubset(signal_ids)
    assert set(eval_manifest["required_contract_checks"]).issubset(contract_checks)

    positive_mode_ids = {case["mode_id"] for case in eval_manifest["starter_positive_cases"]}
    assert set(eval_manifest["required_query_modes"]) == positive_mode_ids
    assert len(eval_manifest["starter_negative_fixtures"]) >= 5


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(entries: list[dict], key: str) -> set[str]:
    return {entry[key] for entry in entries}
