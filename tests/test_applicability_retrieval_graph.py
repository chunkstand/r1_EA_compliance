from __future__ import annotations

from usfs_r1_ea_sources.applicability_retrieval_graph import _bounded_paths
from usfs_r1_ea_sources.applicability_retrieval_graph import _candidate_trace_graph


def test_bounded_paths_respect_max_depth_and_avoid_cycles() -> None:
    adjacency = {
        "candidate:1": [("source_record", "source-record:R1EA-CE"), ("package_fact", "package-fact:1")],
        "source-record:R1EA-CE": [("source_chunk", "source-chunk:R1EA-CE-0")],
        "source-chunk:R1EA-CE-0": [("source_record", "source-record:R1EA-CE")],
    }

    paths = _bounded_paths(
        start_node_id="candidate:1",
        adjacency=adjacency,
        max_depth=2,
        allowed_relationships={"source_record", "source_chunk", "package_fact"},
    )

    assert paths == [
        ["candidate:1", "package_fact", "package-fact:1"],
        ["candidate:1", "source_record", "source-record:R1EA-CE"],
        [
            "candidate:1",
            "source_record",
            "source-record:R1EA-CE",
            "source_chunk",
            "source-chunk:R1EA-CE-0",
        ],
    ]


def test_candidate_trace_graph_seeds_selected_results_rule_claims_and_package_facts() -> None:
    candidate = {
        "candidate_authority_id": "rule-template:unit:ce_fanec",
        "candidate_authority_type": "rule_template",
        "authority_category": "regulation",
        "source_record_ids": ["R1EA-CE"],
        "required_package_fact_types": ["action"],
        "positive_trigger_groups": [["environmental assessment"]],
        "negative_trigger_groups": [],
        "rule_template": {"rule_id": "ce_fanec"},
        "graph_expansion_contract": {
            "relationship_types": [
                "authority_category",
                "source_record",
                "source_chunk",
                "package_fact",
                "rule_claim_link",
                "source_claim",
                "evidence_span",
            ]
        },
    }
    package_fact_graph = {
        "nodes": [
            {
                "node_id": "fact-action-1",
                "node_type": "action",
                "fact_subtype": "project_action_type",
                "normalized_value": "land_exchange",
                "label": "Land exchange",
                "package_chunk_ids": ["package-chunk-1"],
                "evidence_span_ids": ["span-1"],
            }
        ]
    }
    retrieval_trace_rows = [
        {
            "ranked_results": [
                {
                    "selected_status": "selected",
                    "source_record_id": "R1EA-CE",
                    "source_chunk_id": "chunk-1",
                    "package_fact_node_id": "fact-action-1",
                    "package_chunk_id": "package-chunk-1",
                    "result_id": "result-1",
                    "input_trace_ids": ["trace-1"],
                }
            ]
        }
    ]
    trace_graph = _candidate_trace_graph(
        candidate=candidate,
        package_fact_graph=package_fact_graph,
        graph_nodes=[],
        graph_edges=[],
        rule_claim_links=[{"link_id": "link-1", "rule_id": "ce_fanec", "claim_id": "claim-1"}],
        source_claims=[{"claim_id": "claim-1", "source_record_id": "R1EA-CE"}],
        retrieval_trace_rows=retrieval_trace_rows,
        allowed_relationships={
            "authority_category",
            "source_record",
            "source_chunk",
            "package_fact",
            "rule_claim_link",
            "source_claim",
            "evidence_span",
        },
    )

    start_edges = trace_graph["adjacency"]["candidate:rule-template:unit:ce_fanec"]
    assert ("authority_category", "authority-category:regulation") in start_edges
    assert ("source_record", "source-record:R1EA-CE") in start_edges
    assert ("package_fact", "package-fact:fact-action-1") in start_edges
    assert ("rule_claim_link", "rule-claim-link:link-1") in start_edges
    assert trace_graph["adjacency"]["source-record:R1EA-CE"] == [
        ("source_chunk", "source-chunk:chunk-1")
    ]
    assert trace_graph["adjacency"]["rule-claim-link:link-1"] == [
        ("source_claim", "source-claim:claim-1")
    ]
