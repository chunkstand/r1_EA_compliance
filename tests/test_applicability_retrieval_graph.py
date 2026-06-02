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


def test_bounded_paths_can_stop_at_trace_limit() -> None:
    adjacency = {
        "candidate:1": [
            ("package_fact", "package-fact:1"),
            ("package_fact", "package-fact:2"),
            ("package_fact", "package-fact:3"),
        ]
    }

    paths = _bounded_paths(
        start_node_id="candidate:1",
        adjacency=adjacency,
        max_depth=1,
        allowed_relationships={"package_fact"},
        max_path_count=2,
    )

    assert len(paths) == 2


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


def test_candidate_trace_graph_filters_package_facts_to_declared_scope_ids() -> None:
    candidate = {
        "candidate_authority_id": "forest-plan-component:unit",
        "candidate_authority_type": "forest_plan_component",
        "required_package_fact_types": ["management_area", "resource_topic"],
        "positive_trigger_groups": [],
        "negative_trigger_groups": [],
        "forest_plan": {"management_area_ids": ["mgmt-ma-16"]},
        "graph_expansion_contract": {
            "relationship_types": ["package_fact", "management_area", "evidence_span"],
            "neighbor_filters": {"management_area_ids": ["mgmt-ma-16"]},
        },
    }
    package_fact_graph = {
        "nodes": [
            {
                "node_id": "fact-ma-16",
                "node_type": "management_area",
                "normalized_value": "mgmt-ma-16",
                "label": "Management Area 16",
                "package_chunk_ids": ["chunk-1"],
                "evidence_span_ids": ["span-16"],
            },
            {
                "node_id": "fact-ma-24",
                "node_type": "management_area",
                "normalized_value": "mgmt-ma-24",
                "label": "Management Area 24",
                "package_chunk_ids": ["chunk-2"],
                "evidence_span_ids": ["span-24"],
            },
            {
                "node_id": "fact-resource",
                "node_type": "resource_topic",
                "normalized_value": "wildlife",
                "label": "Wildlife",
                "package_chunk_ids": ["chunk-3"],
                "evidence_span_ids": ["span-resource"],
            },
        ]
    }

    trace_graph = _candidate_trace_graph(
        candidate=candidate,
        package_fact_graph=package_fact_graph,
        graph_nodes=[],
        graph_edges=[],
        rule_claim_links=[],
        source_claims=[],
        retrieval_trace_rows=[],
        allowed_relationships={"package_fact", "management_area", "evidence_span"},
    )

    start_edges = trace_graph["adjacency"]["candidate:forest-plan-component:unit"]
    assert ("package_fact", "package-fact:fact-ma-16") in start_edges
    assert ("management_area", "package-fact:fact-ma-16") in start_edges
    assert ("package_fact", "package-fact:fact-ma-24") not in start_edges
    assert ("package_fact", "package-fact:fact-resource") not in start_edges
