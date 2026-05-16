from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import unittest

from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.phase_eval_fixtures import check
from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import read_jsonl
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest
from tests.support.phase_eval_fixtures import write_catalog_source_set_manifest_for_dir
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_sqlite_for_dir
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_catalog_validation_for_dir
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics
from tests.support.phase_eval_fixtures import write_jsonl


class EvidenceGraphTests(unittest.TestCase):
    def test_evidence_graph_builds_document_chunk_and_evidence_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-001", "R1EA-002"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-001",
                        title="NEPA regulations",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-001 | NEPA regulations | artifact abc123",
                        text="Agencies shall consider alternatives and environmental effects.",
                    ),
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-002",
                        title="Forest plan",
                        document_role="forest_plan",
                        authority_level="forest_plan",
                        citation_label="R1EA-002 | Forest plan | artifact def456",
                        text="The forest plan describes monitoring standards.",
                    ),
                ],
            )
            write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-001": ["NEPA alternatives"],
                    "R1EA-002": ["Forest plan consistency"],
                },
            )
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(result.nodes_path.exists())
            self.assertTrue(result.edges_path.exists())
            self.assertTrue(result.sqlite_path.exists())
            self.assertEqual(result.summary["metrics"]["evidence_coverage_rate"], 1.0)
            self.assertEqual(result.summary["metrics"]["chunk_topic_coverage_rate"], 1.0)
            self.assertEqual(result.summary["metrics"]["connected_component_count"], 1)

            nodes = read_jsonl(result.nodes_path)
            edges = read_jsonl(result.edges_path)
            node_types = {node["type"] for node in nodes}
            relationships = {edge["relationship"] for edge in edges}
            self.assertIn("SourceDocument", node_types)
            self.assertIn("RawArtifact", node_types)
            self.assertIn("DocumentChunk", node_types)
            self.assertIn("EvidenceSpan", node_types)
            self.assertIn("ReviewTopic", node_types)
            self.assertIn("CHUNK_HAS_EVIDENCE_SPAN", relationships)
            self.assertIn("EVIDENCE_TRACES_TO_ARTIFACT", relationships)

    def test_evidence_graph_rejects_partial_retrieval_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
                catalog_source_count=2,
                filters={"id": "R1EA-003", "parser": None, "limit": None},
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Partial source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-003 | Partial source | artifact abc123",
                        text="NEPA requires environmental review.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-003": ["NEPA"]})
            build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_extraction=True,
            )

            strict = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(strict.summary["validation_passed"])
            self.assertFalse(strict.summary["reviewer_ready"])
            self.assertFalse(strict.nodes_path.exists())
            validation = json.loads(strict.validation_path.read_text(encoding="utf-8"))
            retrieval_check = check(validation, "retrieval_is_reviewer_ready")
            self.assertFalse(retrieval_check["passed"])

            diagnostic = build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_retrieval=True,
            )
            self.assertTrue(diagnostic.summary["validation_passed"])
            self.assertFalse(diagnostic.summary["reviewer_ready"])
            self.assertTrue(diagnostic.nodes_path.exists())

    def test_evidence_graph_allows_scope_excluded_rows_in_complete_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
                skipped_source_record_ids=["R1EA-160"],
                catalog_source_count=2,
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Extracted source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-003 | Extracted source | artifact abc123",
                        text="NEPA requires environmental review.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-003": ["NEPA"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(result.summary["extraction_complete"])

    def test_evidence_graph_rejects_forged_chunks_after_retrieval_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-010"],
            )
            chunks_path = write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-010",
                        title="Clean source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-010 | Clean source | artifact abc123",
                        text="The agency must evaluate connected actions.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-010": ["Connected actions"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            chunks = read_jsonl(chunks_path)
            forged_text = "A forged replacement span should not bind to retrieval."
            chunks[0]["text"] = forged_text
            chunks[0]["char_end"] = len(forged_text)
            chunks[0]["content_sha256"] = hashlib.sha256(
                forged_text.encode("utf-8")
            ).hexdigest()
            write_jsonl(chunks_path, chunks)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.nodes_path.exists())
            self.assertGreater(result.summary["retrieval_binding_mismatch_count"], 0)
            self.assertEqual(result.summary["chunk_hash_mismatch_count"], 0)
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(check(validation, "chunks_match_retrieval_index")["passed"])
            self.assertTrue(check(validation, "chunk_content_hashes_match_text")["passed"])

    def test_evidence_graph_rejects_chunk_source_set_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            write_catalog_validation(output_dir, passed=True)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-011"],
            )
            chunks_path = write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-011",
                        title="Source set bound source",
                        document_role="forest_plan",
                        authority_level="forest_plan",
                        citation_label="R1EA-011 | Source set bound source | artifact abc123",
                        text="Forest plan standards must be checked for consistency.",
                    )
                ],
            )
            write_catalog_sqlite(output_dir, {"R1EA-011": ["Forest plan consistency"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            chunks = read_jsonl(chunks_path)
            chunks[0]["source_set_id"] = "source-set-other"
            write_jsonl(chunks_path, chunks)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.sqlite_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(check(validation, "chunk_source_set_ids_match")["passed"])
            self.assertFalse(check(validation, "chunks_match_retrieval_index")["passed"])

    def test_source_set_replay_uses_archived_catalog_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "archived_catalog"
            write_catalog_validation(output_dir, passed=False)
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-020"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-020",
                        title="Archived catalog source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-020 | Archived catalog source | artifact abc123",
                        text="Archived catalog replay should stay scoped to the selected source set.",
                    )
                ],
            )
            active_sqlite = write_catalog_sqlite(output_dir, {"R1EA-020": ["Replay"]})
            archived_catalog_dir.mkdir(parents=True, exist_ok=True)
            (archived_catalog_dir / "catalog_validation.json").write_text(
                json.dumps({"passed": True}, sort_keys=True),
                encoding="utf-8",
            )
            shutil.copyfile(active_sqlite, archived_catalog_dir / "review_sources.sqlite")
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            result = build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
                catalog_dir=archived_catalog_dir,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))

    def test_source_set_replay_auto_resolves_compatible_archived_catalog_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "2026-05-14-replay" / "catalog_gate"
            write_catalog_validation(output_dir, passed=False)
            write_catalog_source_set_manifest(output_dir, "source-set-other")
            write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-023"],
            )
            write_chunks(
                output_dir,
                source_set_id,
                [
                    chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-023",
                        title="Archived catalog source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-023 | Archived catalog source | artifact abc123",
                        text="Source-set replay should find the matching archived catalog gate.",
                    )
                ],
            )
            write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-023": ["Replay"],
                    "R1EA-024": ["Extra row"],
                },
            )
            write_catalog_validation_for_dir(archived_catalog_dir, passed=True)
            write_catalog_source_set_manifest_for_dir(
                archived_catalog_dir,
                "source-set-compatible-archived",
            )
            write_catalog_sqlite_for_dir(
                archived_catalog_dir,
                {"R1EA-023": ["Replay"]},
            )
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))


if __name__ == "__main__":
    unittest.main()
