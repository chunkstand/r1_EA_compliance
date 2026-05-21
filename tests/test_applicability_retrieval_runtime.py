from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.applicability_retrieval_runtime import _fused_trace_row
from usfs_r1_ea_sources.applicability_retrieval_runtime import _query_specs_for_candidate


def test_query_specs_keep_forced_trace_types_and_candidate_filters() -> None:
    candidate = {
        "candidate_authority_id": "rule-template:unit:ce_fanec",
        "authority_category": "regulation",
        "source_record_ids": ["R1EA-CE"],
        "source_role_filters": {
            "source_record_ids": ["R1EA-CE"],
            "document_roles": ["regulation"],
            "authority_categories": ["regulation"],
        },
        "package_section_filters": {
            "package_terms": ["environmental assessment"],
        },
        "positive_trigger_groups": [["environmental assessment"]],
        "negative_trigger_groups": [],
        "source_records": [
            {
                "source_record_id": "R1EA-CE",
                "citation_label": "R1EA-CE | CEQ and FANEC NEPA procedure",
            }
        ],
        "retrieval_contract": {
            "required_query_types": ["exact_keyword", "package_section"],
            "source_queries": ["CEQ FANEC environmental assessment"],
            "package_queries": ["environmental assessment"],
        },
    }

    specs = _query_specs_for_candidate(candidate)

    assert [spec["query_type"] for spec in specs] == [
        "exact_keyword",
        "authority_category",
        "citation",
        "package_section",
        "graph_seed",
    ]
    assert all(spec["source_filters"]["source_record_ids"] == ["R1EA-CE"] for spec in specs)
    assert specs[0]["query_text"] == "CEQ FANEC environmental assessment"
    assert specs[-1]["query_text"] == "environmental assessment"


def test_fused_trace_row_uses_rrf_scores_and_unique_inputs() -> None:
    candidate = {
        "candidate_authority_id": "rule-template:unit:ce_fanec",
        "candidate_authority_type": "rule_template",
        "authority_category": "regulation",
        "source_record_ids": ["R1EA-CE"],
        "source_role_filters": {
            "source_record_ids": ["R1EA-CE"],
            "authority_categories": ["regulation"],
        },
        "package_section_filters": {},
        "retrieval_contract": {"query_plan_id": "retrieval-plan:ce_fanec"},
    }
    trace_rows = [
        {
            "retrieval_trace_id": "trace:bm25",
            "query_type": "bm25",
            "ranked_results": [
                {
                    "result_id": "result:shared",
                    "result_kind": "source_chunk",
                    "rank": 1,
                    "score": 1.0,
                    "source_record_id": "R1EA-CE",
                    "source_chunk_id": "chunk-1",
                    "package_fact_node_id": None,
                    "package_chunk_id": None,
                    "claim_id": None,
                },
                {
                    "result_id": "result:package",
                    "result_kind": "package_fact",
                    "rank": 2,
                    "score": 0.4,
                    "source_record_id": None,
                    "source_chunk_id": "",
                    "package_fact_node_id": "fact-1",
                    "package_chunk_id": "package-chunk-1",
                    "claim_id": None,
                },
            ],
        },
        {
            "retrieval_trace_id": "trace:citation",
            "query_type": "citation",
            "ranked_results": [
                {
                    "result_id": "result:shared-2",
                    "result_kind": "source_chunk",
                    "rank": 1,
                    "score": 0.8,
                    "source_record_id": "R1EA-CE",
                    "source_chunk_id": "chunk-1",
                    "package_fact_node_id": None,
                    "package_chunk_id": None,
                    "claim_id": None,
                }
            ],
        },
    ]

    row = _fused_trace_row(
        applicability_run_id="applicability-retrieval:test",
        review_id="review-id",
        source_set_id="source-set-id",
        candidate=candidate,
        trace_rows=trace_rows,
        searched_index_identity={"index_path": "/tmp/index.sqlite", "index_exists": False},
        retrieval_index_path=Path("/tmp/index.sqlite"),
        top_k=1,
        created_at="2026-05-20T00:00:00Z",
        query_diagnostics=lambda **_: [],
    )

    assert row["query_type"] == "fused"
    assert row["fusion_metadata"]["fusion_strategy"] == "reciprocal_rank_fusion"
    assert [result["result_kind"] for result in row["ranked_results"]] == [
        "source_chunk",
        "package_fact",
    ]
    assert row["ranked_results"][0]["selected_status"] == "selected"
    assert row["ranked_results"][1]["selected_status"] == "rejected"
    assert row["ranked_results"][0]["input_result_ids"] == ["result:shared", "result:shared-2"]
    assert row["ranked_results"][0]["source_query_types"] == ["bm25", "citation"]
