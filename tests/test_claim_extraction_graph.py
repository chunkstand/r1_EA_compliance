from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction_graph import CLAIM_GRAPH_SCHEMA_VERSION
from usfs_r1_ea_sources.claim_extraction_graph import build_claim_graph_records
from usfs_r1_ea_sources.claim_extraction_graph import build_entity_records
from usfs_r1_ea_sources.claim_extraction_graph import sqlite_graph_checks
from usfs_r1_ea_sources.claim_extraction_graph import write_sqlite_graph


class ClaimExtractionGraphTests(unittest.TestCase):
    def test_build_entity_records_groups_mentions_and_provenance(self) -> None:
        claims = [
            _claim(
                claim_id="claim:1",
                source_record_id="R1EA-001",
                claim_text="Forest Service shall comply with 36 CFR 219.8.",
            ),
            _claim(
                claim_id="claim:2",
                source_record_id="R1EA-002",
                claim_text="36 CFR 219.8 applies when Forest Service acts.",
            ),
        ]

        entities = build_entity_records(
            claims,
            extractor_name="deterministic_legal_claim_patterns",
            extractor_version="0.1.0",
        )

        legal_citation = next(
            entity
            for entity in entities
            if entity["entity_type"] == "legal_citation"
            and entity["normalized_label"] == "36 cfr 219.8"
        )
        named_actor = next(
            entity
            for entity in entities
            if entity["entity_type"] == "named_actor"
            and entity["normalized_label"] == "forest service"
        )

        self.assertEqual(legal_citation["claim_ids"], ["claim:1", "claim:2"])
        self.assertEqual(legal_citation["source_record_ids"], ["R1EA-001", "R1EA-002"])
        self.assertEqual(legal_citation["mention_count"], 2)
        self.assertEqual(
            legal_citation["citation_labels"],
            [
                "R1EA-001 | Test claim 1 | artifact abc123",
                "R1EA-002 | Test claim 2 | artifact abc123",
            ],
        )
        self.assertEqual(named_actor["mention_count"], 2)
        self.assertEqual(legal_citation["extractor_name"], "deterministic_legal_claim_patterns")
        self.assertEqual(legal_citation["extractor_version"], "0.1.0")

    def test_build_claim_graph_records_emits_expected_relationships(self) -> None:
        claims = [
            _claim(
                claim_id="claim:1",
                source_record_id="R1EA-001",
                claim_text="Forest Service shall comply with 36 CFR 219.8.",
                review_topics=["Forest plan consistency"],
            )
        ]
        entities = build_entity_records(
            claims,
            extractor_name="deterministic_legal_claim_patterns",
            extractor_version="0.1.0",
        )

        nodes, edges = build_claim_graph_records(
            source_set_id="source-set-test",
            claims=claims,
            entities=entities,
        )

        node_types = {node["type"] for node in nodes}
        relationships = {edge["relationship"] for edge in edges}
        self.assertIn("SourceSet", node_types)
        self.assertIn("Claim", node_types)
        self.assertIn("ClaimEvidenceSpan", node_types)
        self.assertIn("Entity", node_types)
        self.assertIn("Authority", node_types)
        self.assertIn("ReviewTopic", node_types)
        self.assertIn("SOURCE_SET_HAS_SOURCE", relationships)
        self.assertIn("CHUNK_HAS_CLAIM", relationships)
        self.assertIn("CLAIM_HAS_EVIDENCE_SPAN", relationships)
        self.assertIn("CLAIM_HAS_AUTHORITY", relationships)
        self.assertIn("CLAIM_SUPPORTS_REVIEW_TOPIC", relationships)
        self.assertIn("CLAIM_MENTIONS_ENTITY", relationships)

    def test_sqlite_graph_round_trip_preserves_counts_and_metadata(self) -> None:
        claims = [
            _claim(
                claim_id="claim:1",
                source_record_id="R1EA-001",
                claim_text="Forest Service shall comply with 36 CFR 219.8.",
                review_topics=["Forest plan consistency"],
            )
        ]
        entities = build_entity_records(
            claims,
            extractor_name="deterministic_legal_claim_patterns",
            extractor_version="0.1.0",
        )
        nodes, edges = build_claim_graph_records(
            source_set_id="source-set-test",
            claims=claims,
            entities=entities,
        )
        metrics = {
            "claim_count": len(claims),
            "entity_count": len(entities),
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

        with tempfile.TemporaryDirectory() as tmp:
            sqlite_path = Path(tmp) / "claim_graph.sqlite"
            write_sqlite_graph(
                sqlite_path,
                source_set_id="source-set-test",
                claims=claims,
                entities=entities,
                nodes=nodes,
                edges=edges,
                metrics=metrics,
            )

            checks = sqlite_graph_checks(
                sqlite_path,
                expected_claim_count=len(claims),
                expected_entity_count=len(entities),
                expected_node_count=len(nodes),
                expected_edge_count=len(edges),
            )

            self.assertTrue(all(check["passed"] for check in checks))
            with closing(sqlite3.connect(sqlite_path)) as connection:
                metadata_rows = connection.execute(
                    "SELECT key, value_json FROM metadata"
                ).fetchall()
            metadata = {key: json.loads(value) for key, value in metadata_rows}
            self.assertEqual(metadata["schema_version"], CLAIM_GRAPH_SCHEMA_VERSION)
            self.assertEqual(metadata["source_set_id"], "source-set-test")
            self.assertEqual(metadata["claim_count"], 1)
            self.assertEqual(metadata["entity_count"], len(entities))


def _claim(
    *,
    claim_id: str,
    source_record_id: str,
    claim_text: str,
    review_topics: list[str] | None = None,
) -> dict:
    return {
        "claim_id": claim_id,
        "source_set_id": "source-set-test",
        "source_record_id": source_record_id,
        "chunk_id": f"chunk:{claim_id}",
        "chunk_index": 0,
        "claim_type": "obligation",
        "claim_text": claim_text,
        "citation_label": f"{source_record_id} | Test claim {claim_id.split(':')[-1]} | artifact abc123",
        "title": "Test title",
        "authority_level": "federal",
        "document_role": "law",
        "source_char_start": 0,
        "source_char_end": len(claim_text),
        "chunk_char_start": 0,
        "chunk_char_end": len(claim_text),
        "content_sha256": _text_sha256(claim_text),
        "chunk_content_sha256": _text_sha256(claim_text),
        "extractor_version": "0.1.0",
        "validation_status": "valid",
        "review_topics": review_topics or [],
    }


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
