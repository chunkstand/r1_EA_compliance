from __future__ import annotations

import unittest

from usfs_r1_ea_sources.applicability_decision_coverage import coverage_boundary
from usfs_r1_ea_sources.applicability_decision_coverage import coverage_certificate
from usfs_r1_ea_sources.applicability_decision_coverage import records_by_candidate


class ApplicabilityDecisionCoverageTests(unittest.TestCase):
    def test_records_by_candidate_groups_rows(self) -> None:
        grouped = records_by_candidate(
            [
                {"candidate_authority_id": "candidate-1", "row_id": "row-1"},
                {"candidate_authority_id": "candidate-2", "row_id": "row-2"},
                {"candidate_authority_id": "candidate-1", "row_id": "row-3"},
            ]
        )

        self.assertEqual(
            {key: [row["row_id"] for row in rows] for key, rows in grouped.items()},
            {
                "candidate-1": ["row-1", "row-3"],
                "candidate-2": ["row-2"],
            },
        )

    def test_coverage_boundary_reports_missing_query_variants(self) -> None:
        boundary = coverage_boundary(
            candidate={
                "search_coverage_requirements": [
                    {
                        "coverage_class": "positive_trigger_miss",
                        "required_query_types": [
                            "exact_keyword",
                            "metadata_filter",
                            "package_section",
                        ],
                        "required_artifacts": [
                            "package_fact_graph",
                            "applicability_graph_trace",
                        ],
                        "requires_searched_index_hash": True,
                    }
                ]
            },
            retrieval_rows=[
                _retrieval_row(
                    "exact_keyword",
                    searched_index_hash="source-index-hash",
                    index_path="catalog/source-index.sqlite",
                ),
                _retrieval_row(
                    "package_section",
                    graph_artifact_hash="package-graph-hash",
                    section_family="alternatives",
                ),
            ],
            graph_rows=[{"relationship_types": ["package_fact"]}],
        )

        self.assertFalse(boundary["coverage_sufficient"])
        self.assertEqual(boundary["missing_query_variants"], ["metadata_filter"])
        self.assertTrue(boundary["source_index_hash_required"])
        self.assertTrue(boundary["source_index_hash_present"])
        self.assertTrue(boundary["package_graph_hash_present"])
        self.assertEqual(boundary["package_sections_searched"], ["alternatives"])
        self.assertEqual(boundary["graph_neighborhoods_searched"], ["package_fact"])

    def test_coverage_boundary_accepts_complete_search_boundary(self) -> None:
        boundary = coverage_boundary(
            candidate={
                "search_coverage_requirements": [
                    {
                        "coverage_class": "forest_plan_scope_miss",
                        "required_query_types": [
                            "exact_keyword",
                            "metadata_filter",
                            "package_section",
                        ],
                        "required_artifacts": [
                            "applicability_graph_trace",
                        ],
                    }
                ]
            },
            retrieval_rows=[
                _retrieval_row(
                    "exact_keyword",
                    searched_index_hash="source-index-hash",
                    index_path="catalog/source-index.sqlite",
                ),
                _retrieval_row(
                    "metadata_filter",
                    source_filters={"authority_categories": ["regulation"]},
                ),
                _retrieval_row(
                    "package_section",
                    graph_artifact_hash="package-graph-hash",
                    section_family="purpose_and_need",
                ),
            ],
            graph_rows=[{"relationship_types": ["package_fact", "source_record"]}],
        )

        self.assertTrue(boundary["coverage_sufficient"])
        self.assertEqual(boundary["missing_query_variants"], [])
        self.assertEqual(
            boundary["executed_query_variants"],
            ["exact_keyword", "metadata_filter", "package_section"],
        )
        self.assertEqual(
            boundary["metadata_filters_searched"],
            [{"authority_categories": ["regulation"]}],
        )
        self.assertEqual(
            boundary["graph_neighborhoods_searched"],
            ["package_fact", "source_record"],
        )

    def test_coverage_certificate_tracks_missing_trigger_groups_and_rejections(self) -> None:
        certificate = coverage_certificate(
            applicability_run_id="applicability-determine:review-1:source-set-1",
            review_id="review-1",
            source_set_id="source-set-1",
            created_at="2026-05-20T12:00:00Z",
            candidate={
                "positive_trigger_groups": [["road"], ["trail"]],
                "negative_trigger_groups": [["grazing"]],
            },
            decision={
                "candidate_authority_id": "rule-template:test:not-applicable",
                "decision_id": "decision-1",
                "status": "not_applicable",
                "basis_type": "absent_trigger_evidence",
                "basis": {"missing_trigger_groups": [["road"], ["trail"]]},
            },
            coverage_boundary={
                "coverage_sufficient": False,
                "required_query_variants": ["exact_keyword", "package_section"],
                "executed_query_variants": ["package_section"],
                "missing_query_variants": ["exact_keyword"],
                "package_sections_searched": ["alternatives"],
                "source_indexes_searched": ["catalog/source-index.sqlite"],
                "metadata_filters_searched": [{"authority_categories": ["regulation"]}],
                "graph_neighborhoods_searched": ["package_fact"],
                "searched_artifact_hashes": ["package-graph-hash"],
            },
            authority_universe_sha256="authority-hash",
            package_fact_graph_sha256="package-hash",
            retrieval_trace_sha256="retrieval-hash",
            graph_trace_sha256="graph-hash",
            retrieval_rows=[
                {
                    "ranked_results": [
                        {
                            "result_id": "selected-1",
                            "selected_status": "selected",
                        },
                        {
                            "result_id": "rejected-1",
                            "selected_status": "rejected",
                        },
                    ]
                }
            ],
            graph_rows=[
                {"graph_path_id": "graph-path-1"},
                {"graph_path_id": "graph-path-2"},
            ],
        )

        self.assertEqual(certificate["coverage_result"], "insufficient")
        self.assertEqual(certificate["missing_trigger_groups"], [["road"], ["trail"]])
        self.assertEqual(certificate["trigger_terms_searched"], ["road", "trail"])
        self.assertEqual(certificate["negative_trigger_terms_searched"], ["grazing"])
        self.assertEqual(certificate["rejected_evidence_ids"], ["rejected-1"])
        self.assertEqual(certificate["graph_path_ids"], ["graph-path-1", "graph-path-2"])
        self.assertEqual(
            certificate["rationale"],
            "Required retrieval variants or graph neighborhoods were missing.",
        )

    def test_coverage_certificate_marks_adjudication_required(self) -> None:
        certificate = coverage_certificate(
            applicability_run_id="applicability-determine:review-1:source-set-1",
            review_id="review-1",
            source_set_id="source-set-1",
            created_at="2026-05-20T12:00:00Z",
            candidate={"positive_trigger_groups": [["road"]], "negative_trigger_groups": []},
            decision={
                "candidate_authority_id": "rule-template:test:adjudication",
                "decision_id": "decision-2",
                "status": "needs_adjudication",
                "basis_type": "unresolved_evidence_conflict",
                "basis": {},
                "explicit_trigger_miss_evidence": [],
            },
            coverage_boundary={
                "coverage_sufficient": True,
                "required_query_variants": ["exact_keyword"],
                "executed_query_variants": ["exact_keyword"],
                "missing_query_variants": [],
                "package_sections_searched": [],
                "source_indexes_searched": ["catalog/source-index.sqlite"],
                "metadata_filters_searched": [],
                "graph_neighborhoods_searched": [],
                "searched_artifact_hashes": ["source-index-hash"],
            },
            authority_universe_sha256="authority-hash",
            package_fact_graph_sha256="package-hash",
            retrieval_trace_sha256="retrieval-hash",
            graph_trace_sha256="graph-hash",
            retrieval_rows=[],
            graph_rows=[],
        )

        self.assertEqual(certificate["coverage_result"], "adjudication_required")
        self.assertEqual(
            certificate["rationale"],
            "Search coverage was recorded, but the predicate requires adjudication.",
        )


def _retrieval_row(
    query_type: str,
    *,
    searched_index_hash: str | None = None,
    graph_artifact_hash: str | None = None,
    index_path: str | None = None,
    source_filters: dict | None = None,
    section_family: str | None = None,
) -> dict:
    ranked_results = []
    if section_family is not None:
        ranked_results.append(
            {
                "result_kind": "package_section",
                "section_family": section_family,
            }
        )
    return {
        "query_type": query_type,
        "searched_index": {
            "searched_index_hash": searched_index_hash,
            "graph_artifact_hash": graph_artifact_hash,
            "index_path": index_path,
        },
        "source_filters": source_filters,
        "ranked_results": ranked_results,
    }
