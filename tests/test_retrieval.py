from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.retrieval import query_retrieval_index
from usfs_r1_ea_sources.retrieval_query import _contains_term
from usfs_r1_ea_sources.retrieval_query import _tokenize
from usfs_r1_ea_sources.chunk_layers import build_chunk_layers

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_sqlite
from tests.support.retrieval_fixtures import _write_chunks
from tests.support.retrieval_fixtures import _write_extraction_diagnostics


class RetrievalTests(unittest.TestCase):
    def test_build_retrieval_index_and_query_with_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-001", "R1EA-002"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-001",
                        title="NEPA regulations",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-001 | NEPA regulations | artifact abc123",
                        text="Agencies shall consider alternatives and environmental effects.",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-002",
                        title="Forest plan",
                        document_role="forest_plan",
                        authority_level="forest_plan",
                        citation_label="R1EA-002 | Forest plan | artifact def456",
                        text="This forest plan describes vegetation standards.",
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-001": ["NEPA alternatives"],
                    "R1EA-002": ["Forest plan consistency"],
                },
            )

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.sqlite_path.exists())
            self.assertEqual(result.summary["chunk_count"], 2)
            self.assertEqual(result.summary["topic_link_count"], 2)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="alternatives environmental effects",
                limit=3,
                document_role="regulation",
                authority_level="federal_regulation",
                review_topic="alternatives",
            )

            self.assertEqual(query["hit_count"], 1)
            hit = query["results"][0]
            self.assertEqual(hit["source_record_id"], "R1EA-001")
            self.assertEqual(hit["citation_label"], "R1EA-001 | NEPA regulations | artifact abc123")
            self.assertIn("NEPA alternatives", hit["review_topics"])
            self.assertEqual(hit["provenance"]["parser_name"], "unit_parser")
            self.assertEqual(hit["evidence_span"]["source_char_start"], 0)
            self.assertGreater(hit["evidence_span"]["source_char_end"], 0)

    def test_retrieval_query_supports_multiple_source_record_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["FED-001", "USDA-001"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FED-001",
                        title="National Environmental Policy Act",
                        document_role="law",
                        authority_level="federal",
                        citation_label="FED-001 | National Environmental Policy Act | artifact abc123",
                        text="The National Environmental Policy Act requires environmental review.",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="USDA-001",
                        title="USDA NEPA procedures",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="USDA-001 | USDA NEPA procedures | artifact def456",
                        text="USDA NEPA procedures govern environmental review implementation.",
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "FED-001": ["NEPA"],
                    "USDA-001": ["USDA NEPA"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="environmental review",
                source_record_ids=["R1EA-001", "FED-001"],
            )

            self.assertEqual(query["hit_count"], 1)
            self.assertEqual(query["results"][0]["source_record_id"], "FED-001")
            self.assertEqual(query["filters"]["source_record_ids"], ["R1EA-001", "FED-001"])

    def test_retrieval_query_expands_aliased_source_record_filter_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["FED-001"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FED-001",
                        title="National Environmental Policy Act",
                        document_role="law",
                        authority_level="federal",
                        citation_label="FED-001 | National Environmental Policy Act | artifact abc123",
                        text="The National Environmental Policy Act requires environmental review.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"FED-001": ["NEPA"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="environmental review",
                source_record_id="R1EA-001",
            )

            self.assertEqual(query["hit_count"], 1)
            self.assertEqual(query["results"][0]["source_record_id"], "FED-001")
            self.assertEqual(query["filters"]["source_record_id"], "R1EA-001")

    def test_retrieval_query_prefers_exact_query_phrase_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["FED-003", "FED-004"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FED-003",
                        title="National Forest System Land Management Planning",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="FED-003 | Planning rule | artifact abc123",
                        text=(
                            "The responsible official shall approve the project or activity "
                            "only after determining consistency with the applicable plan components."
                        ),
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FED-004",
                        title="National Forest System Land Management Planning",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="FED-004 | Planning record | artifact def456",
                        text=(
                            "The planning record includes approval documentation and other "
                            "documents associated with applicable components."
                        ),
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "FED-003": ["Planning rule"],
                    "FED-004": ["Planning record"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="project or activity applicable plan components",
            )

            self.assertEqual(query["results"][0]["source_record_id"], "FED-003")
            self.assertIn("project or activity", query["results"][0]["evidence_span"]["text"].lower())

    def test_retrieval_query_uses_contextual_fts_over_sidecar_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1PLAN-001"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-001",
                        title="Forest Plan",
                        document_role="forest_plan",
                        authority_level="forest_plan",
                        citation_label="R1PLAN-001 | Forest Plan | artifact abc123",
                        text="Desired condition DC-01 Watersheds are resilient.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1PLAN-001": ["Forest plan direction"]})
            layers = build_chunk_layers(output_dir=output_dir, source_set_id=source_set_id)
            result = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks_path=layers.atomic_chunks_path,
            )

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="watersheds resilient desired condition",
            )

            self.assertEqual(query["retrieval_mode"], "fts_first_stage")
            self.assertGreater(query["fts_candidate_count"], 0)
            hit = query["results"][0]
            self.assertEqual(hit["source_record_id"], "R1PLAN-001")
            self.assertEqual(hit["chunk_layer"], "atomic_text_chunk_v2")
            self.assertEqual(hit["structure_type"], "desired_condition")
            self.assertTrue(hit["parent_window_id"])
            self.assertNotIn("source_record_id:", hit["evidence_span"]["text"])

    def test_retrieval_query_weights_rare_terms_over_generic_nepa_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["USFS-001", "FPS-068"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="USFS-001",
                        title="Environmental Planning and NEPA page",
                        document_role="agency_guidance",
                        authority_level="federal",
                        citation_label="USFS-001 | NEPA page | artifact abc123",
                        text=(
                            "Environmental planning under NEPA can occur at many levels "
                            "of the Forest Service and may use several review tools."
                        ),
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FPS-068",
                        title=(
                            "Purpose and Need, Alternatives, Affected Environment and "
                            "Environmental Consequences"
                        ),
                        document_role="environmental_impact_statement",
                        authority_level="federal",
                        citation_label="FPS-068 | FEIS volume 1 | artifact def456",
                        text=(
                            "This section compares alternatives and analyzes environmental "
                            "effects and consequences for the proposed action."
                        ),
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "USFS-001": ["NEPA"],
                    "FPS-068": ["Alternatives"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="NEPA alternatives environmental effects",
            )

            self.assertEqual(query["results"][0]["source_record_id"], "FPS-068")

    def test_retrieval_query_centers_span_on_densest_query_term_cluster(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["USDA-005"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="USDA-005",
                        title="Documentation prepared by applicant or third party",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="USDA-005 | Applicant docs | artifact abc123",
                        text=(
                            "Documentation prepared by applicant or third party may be used "
                            "under agency supervision. The subcomponent will work with the "
                            "applicant to define the purpose and need and independently "
                            "evaluate the information submitted to determine whether the "
                            "documentation is sufficient."
                        ),
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"USDA-005": ["Applicant documentation"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="applicant third party independent evaluation",
                source_record_id="USDA-005",
            )

            span_text = query["results"][0]["evidence_span"]["text"].lower()
            self.assertIn("independently evaluate", span_text)
            self.assertIn("applicant", span_text)

    def test_retrieval_term_matching_treats_evaluation_and_evaluate_as_related(self) -> None:
        text = "The subcomponent shall independently evaluate the information submitted."
        self.assertTrue(
            _contains_term(
                "evaluation",
                set(_tokenize(text)),
                text,
            )
        )

    def test_retrieval_query_supports_citation_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-010"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-010",
                        title="Decision notice",
                        document_role="decision_notice",
                        authority_level="project_record",
                        citation_label="R1EA-010 | Decision notice | artifact abc123",
                        text="The decision notice includes mitigation measures.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-010": ["Mitigation"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="mitigation measures",
                citation="Decision notice",
            )

            self.assertEqual(query["hit_count"], 1)
            self.assertEqual(query["results"][0]["source_record_id"], "R1EA-010")
            self.assertIn("mitigation measures", query["results"][0]["evidence_span"]["text"])

    def test_retrieval_query_supports_support_document_role_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1PLAN-flathead-nf-02", "R1PLAN-flathead-nf-03"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-flathead-nf-02",
                        title="2018 Revised Land Management Plan",
                        document_role="forest_plan_support",
                        support_document_role="primary_land_management_plan",
                        authority_level="forest_plan",
                        citation_label="R1PLAN-flathead-nf-02 | 2018 Revised Land Management Plan | artifact abc123",
                        text="Flathead revised land management plan 2018 forest plan direction.",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1PLAN-flathead-nf-03",
                        title="Record of Decision",
                        document_role="forest_plan_support",
                        support_document_role="record_of_decision",
                        authority_level="forest_plan",
                        citation_label="R1PLAN-flathead-nf-03 | Record of Decision | artifact def456",
                        text="Flathead record of decision approving the revised forest plan.",
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1PLAN-flathead-nf-02": ["Forest-plan direction"],
                    "R1PLAN-flathead-nf-03": ["Forest-plan decision"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="flathead revised land management plan 2018",
                support_document_role="primary_land_management_plan",
            )

            self.assertEqual(query["hit_count"], 1)
            self.assertEqual(query["results"][0]["source_record_id"], "R1PLAN-flathead-nf-02")
            self.assertEqual(
                query["results"][0]["support_document_role"],
                "primary_land_management_plan",
            )

    def test_retrieval_query_diversifies_duplicate_source_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-001", "R1EA-002"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-001",
                        title="Generic authority",
                        document_role="law",
                        authority_level="federal",
                        citation_label="R1EA-001 | Generic authority | artifact abc123",
                        text="Decision notice mitigation measures are discussed in this generic source.",
                    ),
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id="R1EA-001",
                            title="Generic authority",
                            document_role="law",
                            authority_level="federal",
                            citation_label="R1EA-001 | Generic authority | artifact abc123",
                            text="Decision notice mitigation measures are discussed again in the same source.",
                        ),
                        "chunk_id": "chunk:R1EA-001:1",
                        "chunk_index": 1,
                    },
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-002",
                        title="Second source",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-002 | Second source | artifact def456",
                        text="Decision notice mitigation measures are addressed in a second source.",
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-001": ["Mitigation"],
                    "R1EA-002": ["Decision notice"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="decision notice mitigation measures",
                limit=3,
            )

            self.assertEqual(
                {query["results"][0]["source_record_id"], query["results"][1]["source_record_id"]},
                {"R1EA-001", "R1EA-002"},
            )
            self.assertEqual(query["results"][0]["source_record_id"], "R1EA-002")
            self.assertEqual(query["results"][2]["source_record_id"], "R1EA-001")

    def test_retrieval_query_boosts_title_topic_and_role_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-010", "R1EA-011", "R1EA-012"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-010",
                        title="National Environmental Policy Act",
                        document_role="law",
                        authority_level="federal",
                        citation_label="R1EA-010 | National Environmental Policy Act | artifact abc123",
                        text="This generic legal source mentions decision notice mitigation measures repeatedly.",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-011",
                        title="Notice of Decision",
                        document_role="project_record",
                        support_document_role="record_of_decision",
                        authority_level="forest",
                        citation_label="R1EA-011 | Notice of Decision | artifact def456",
                        text="The selected alternative is described in the notice of decision.",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-012",
                        title="Definitions",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-012 | Definitions | artifact ghi789",
                        text="Mitigation measures avoid, minimize, rectify, reduce, or compensate for impacts.",
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-010": ["Generic NEPA authority"],
                    "R1EA-011": ["Decision notice mitigation measures"],
                    "R1EA-012": ["Mitigation measures"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="decision notice mitigation measures",
                limit=3,
            )

            self.assertEqual(query["results"][0]["source_record_id"], "R1EA-011")
            self.assertEqual(
                {hit["source_record_id"] for hit in query["results"][:3]},
                {"R1EA-010", "R1EA-011", "R1EA-012"},
            )

    def test_retrieval_query_handles_legacy_index_without_support_document_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "evidence_index.sqlite"
            with closing(sqlite3.connect(index_path)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE chunks (
                      chunk_id TEXT PRIMARY KEY,
                      source_set_id TEXT NOT NULL,
                      source_record_id TEXT NOT NULL,
                      chunk_index INTEGER NOT NULL,
                      title TEXT NOT NULL,
                      document_role TEXT NOT NULL,
                      authority_level TEXT NOT NULL,
                      host TEXT,
                      expected_parser TEXT,
                      artifact_sha256 TEXT NOT NULL,
                      artifact_path TEXT NOT NULL,
                      citation_label TEXT NOT NULL,
                      original_url TEXT NOT NULL,
                      effective_url TEXT NOT NULL,
                      final_url TEXT,
                      parser_name TEXT NOT NULL,
                      parser_version TEXT NOT NULL,
                      extracted_at TEXT NOT NULL,
                      source_text_path TEXT,
                      char_start INTEGER NOT NULL,
                      char_end INTEGER NOT NULL,
                      page INTEGER,
                      section TEXT,
                      heading TEXT,
                      content_sha256 TEXT NOT NULL,
                      review_topics_json TEXT NOT NULL,
                      text TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    INSERT INTO chunks (
                      chunk_id, source_set_id, source_record_id, chunk_index, title, document_role,
                      authority_level, host, expected_parser, artifact_sha256, artifact_path,
                      citation_label, original_url, effective_url, final_url, parser_name,
                      parser_version, extracted_at, source_text_path, char_start, char_end, page,
                      section, heading, content_sha256, review_topics_json, text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "chunk:R1EA-001",
                        "source-set-test",
                        "R1EA-001",
                        0,
                        "Legacy source",
                        "law",
                        "federal_law",
                        "example.test",
                        "html",
                        "artifact-sha",
                        "artifacts/raw/R1EA-001.html",
                        "R1EA-001 | Legacy source | artifact-sha",
                        "https://example.test/original",
                        "https://example.test/effective",
                        "https://example.test/final",
                        "unit_parser",
                        "1.0",
                        "2026-05-13T00:00:00Z",
                        "derived/source-set-test/extracted_text/R1EA-001.txt",
                        0,
                        33,
                        None,
                        None,
                        "Legacy source",
                        hashlib.sha256(b"Legacy retrieval text").hexdigest(),
                        json.dumps(["Legacy topic"]),
                        "Legacy retrieval text",
                    ),
                )
                connection.commit()

            query = query_retrieval_index(index_path=index_path, query="legacy retrieval")

            self.assertEqual(query["hit_count"], 1)
            self.assertEqual(query["results"][0]["source_record_id"], "R1EA-001")
            self.assertIsNone(query["results"][0]["support_document_role"])

    def test_retrieval_query_requires_query_or_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-008"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-008",
                        title="Filtered source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-008 | Filtered source | artifact abc123",
                        text="Public comment is part of scoping.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-008": ["Scoping"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            with self.assertRaises(ValueError):
                query_retrieval_index(index_path=result.sqlite_path, query="   ")

            filtered = query_retrieval_index(
                index_path=result.sqlite_path,
                query="",
                source_record_id="R1EA-008",
            )
            self.assertEqual(filtered["hit_count"], 1)
