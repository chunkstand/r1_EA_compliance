from __future__ import annotations

import unittest

from usfs_r1_ea_sources.applicability_decision_evidence import declared_source_library_evidence
from usfs_r1_ea_sources.applicability_decision_evidence import package_fact_nodes
from usfs_r1_ea_sources.applicability_decision_evidence import present_package_values
from usfs_r1_ea_sources.applicability_decision_evidence import retrieval_lineage
from usfs_r1_ea_sources.applicability_decision_evidence import selected_package_results
from usfs_r1_ea_sources.applicability_decision_evidence import source_library_evidence
from usfs_r1_ea_sources.applicability_decision_evidence import term_in_text
from usfs_r1_ea_sources.applicability_decision_evidence import trigger_match


class ApplicabilityDecisionEvidenceTests(unittest.TestCase):
    def test_term_in_text_requires_acronym_boundary(self) -> None:
        self.assertFalse(
            term_in_text(
                "CE",
                "The Forest Service combined the NEPA scoping and public comment periods.",
            )
        )
        self.assertTrue(term_in_text("CE", "The agency adopted a CE for this action."))

    def test_trigger_match_collects_package_node_chunk_and_result_evidence(self) -> None:
        match = trigger_match(
            groups=[["road"], ["trail"], ["grazing"]],
            package_nodes=[
                {
                    "node_id": "node-road",
                    "label": "Road access",
                    "raw_value": "road",
                    "normalized_value": "road",
                    "fact_subtype": "action",
                    "section_family": "alternatives",
                    "context_excerpt": "The proposed action includes a road relocation.",
                    "matched_text": "road",
                    "package_chunk_ids": ["chunk-road"],
                    "citation_label": "EA-PACKAGE-001",
                    "page_label": "3",
                    "char_start": 11,
                    "char_end": 15,
                    "confidence_class": "observed",
                    "evidence_span_ids": ["span-road"],
                    "text_hash": "hash-road",
                }
            ],
            package_chunks=[
                {
                    "chunk_id": "chunk-trail",
                    "text": "Trail easements could be required if needed for final design.",
                    "section": "Alternatives",
                    "heading": "Alternatives",
                    "citation_label": "EA-PACKAGE-001",
                    "page_label": "5",
                    "char_start": 100,
                    "content_sha256": "hash-trail",
                }
            ],
            package_results=[
                {
                    "result_id": "result-grazing",
                    "result_kind": "package_section",
                    "selected_status": "selected",
                    "package_chunk_id": "chunk-grazing",
                    "package_fact_node_id": None,
                    "matched_terms": ["grazing"],
                    "text_excerpt": (
                        "Resource effects from grazing may be possible in the cumulative "
                        "effects area."
                    ),
                    "section_family": "cumulative_effects",
                    "citation_label": "EA-PACKAGE-001",
                    "page_label": "7",
                    "char_start": 220,
                    "char_end": 260,
                    "text_hash": "hash-grazing",
                    "provenance": {
                        "confidence_class": "weak_signal",
                        "normalized_value": "grazing",
                        "fact_subtype": "resource_topic",
                        "evidence_strength": {
                            "strength_class": "speculative",
                            "reason": "speculative",
                            "matched_phrase": "may be possible",
                            "matched_text": "grazing",
                            "evidence_window": (
                                "Resource effects from grazing may be possible in the cumulative "
                                "effects area."
                            ),
                            "section_family": "cumulative_effects",
                        },
                        "evidence_span_ids": ["span-grazing"],
                    },
                }
            ],
        )

        self.assertTrue(match["matched"])
        self.assertTrue(match["requires_adjudication"])
        self.assertEqual({tuple(group) for group in match["matched_groups"]}, {("road",), ("trail",), ("grazing",)})
        diagnostics = {
            tuple(group["trigger_group"]): group
            for group in match["trigger_group_results"]
        }
        self.assertEqual(diagnostics[("road",)]["diagnostic_treatment"], "decisive")
        self.assertEqual(diagnostics[("trail",)]["diagnostic_treatment"], "weak_only")
        self.assertEqual(diagnostics[("grazing",)]["diagnostic_treatment"], "weak_only")
        self.assertIn("observed", diagnostics[("road",)]["evidence_strength_counts"])
        self.assertIn("weak_signal", diagnostics[("trail",)]["evidence_strength_counts"])
        self.assertIn("speculative", diagnostics[("grazing",)]["evidence_strength_class_counts"])
        self.assertTrue(diagnostics[("trail",)]["weak_signal_reasons"])
        self.assertTrue(
            any(
                detail.get("matched_phrase") in {"could be required", "if needed"}
                for detail in diagnostics[("trail",)]["weak_signal_details"]
            )
        )
        self.assertTrue(
            any("may be possible" in note for note in diagnostics[("grazing",)]["weak_signal_reasons"])
        )

    def test_source_library_evidence_filters_selected_source_chunks(self) -> None:
        evidence = source_library_evidence(
            retrieval_rows=[
                {
                    "retrieval_trace_id": "trace-1",
                    "ranked_results": [
                        {
                            "result_id": "source-hit-1",
                            "result_kind": "source_chunk",
                            "selected_status": "selected",
                            "source_record_id": "SRC-1",
                            "source_chunk_id": "chunk-1",
                            "citation_label": "SRC-1",
                            "page_label": "2",
                            "char_start": 10,
                            "char_end": 20,
                            "claim_id": "claim-1",
                            "text_excerpt": "Selected source evidence",
                            "text_hash": "hash-1",
                        },
                        {
                            "result_id": "source-hit-2",
                            "result_kind": "source_chunk",
                            "selected_status": "rejected",
                            "source_record_id": "SRC-1",
                        },
                        {
                            "result_id": "package-hit",
                            "result_kind": "package_fact",
                            "selected_status": "selected",
                            "source_record_id": "SRC-1",
                        },
                    ],
                }
            ],
            source_record_ids=["SRC-1"],
        )

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["evidence_id"], "source-hit-1")
        self.assertEqual(evidence[0]["source_claim_ids"], ["claim-1"])

    def test_declared_source_library_evidence_uses_authority_universe_fallback(self) -> None:
        evidence = declared_source_library_evidence(
            candidate={
                "candidate_authority_id": "rule-template:unit-pack:0.1.0:test",
                "source_evidence_availability": {"available": True},
                "required_source_evidence": {"source_chunk_ids": ["chunk-A"]},
                "source_records": [
                    {
                        "source_record_id": "SRC-1",
                        "title": "Declared source record",
                        "citation_label": "SRC-1 | Declared source record",
                    }
                ],
            },
            source_record_ids=["SRC-1"],
        )

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["evidence_origin"], "authority_universe")
        self.assertEqual(evidence[0]["source_record_id"], "SRC-1")
        self.assertEqual(evidence[0]["source_chunk_id"], "chunk-A")

    def test_retrieval_lineage_and_selected_package_results_filter_status_and_kind(self) -> None:
        retrieval_rows = [
            {
                "retrieval_trace_id": "trace-1",
                "ranked_results": [
                    {
                        "result_id": "package-selected",
                        "result_kind": "package_fact",
                        "selected_status": "selected",
                    },
                    {
                        "result_id": "package-rejected",
                        "result_kind": "package_section",
                        "selected_status": "rejected",
                    },
                    {
                        "result_id": "source-selected",
                        "result_kind": "source_chunk",
                        "selected_status": "selected",
                    },
                ],
            }
        ]

        selected, rejected, traces = retrieval_lineage(retrieval_rows)
        self.assertEqual(selected, ["package-selected", "source-selected"])
        self.assertEqual(rejected, ["package-rejected"])
        self.assertEqual(traces, ["trace-1"])
        self.assertEqual(
            [result["result_id"] for result in selected_package_results(retrieval_rows)],
            ["package-selected"],
        )

    def test_package_fact_nodes_and_present_values_ignore_negative_context(self) -> None:
        nodes = package_fact_nodes(
            {
                "nodes": [
                    {"node_id": "section-1", "node_type": "package_section"},
                    {
                        "node_id": "geo-1",
                        "node_type": "geography",
                        "normalized_value": "geo-crazy",
                        "confidence_class": "observed",
                    },
                    {
                        "node_id": "geo-2",
                        "node_type": "geography",
                        "normalized_value": "geo-negative",
                        "confidence_class": "negative_context",
                    },
                ]
            }
        )

        self.assertEqual([node["node_id"] for node in nodes], ["geo-1", "geo-2"])
        present = present_package_values(nodes)
        self.assertEqual(present["geography"], {"geo-crazy"})
