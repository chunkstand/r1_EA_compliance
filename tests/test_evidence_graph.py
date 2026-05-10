from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import shutil
import tempfile
import unittest

from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval
from usfs_r1_ea_sources.retrieval import build_retrieval_index


class EvidenceGraphTests(unittest.TestCase):
    def test_evidence_graph_builds_document_chunk_and_evidence_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_catalog_validation(output_dir, passed=True)
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
                        text="The forest plan describes monitoring standards.",
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

            nodes = _read_jsonl(result.nodes_path)
            edges = _read_jsonl(result.edges_path)
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
            _write_catalog_validation(output_dir, passed=True)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
                catalog_source_count=2,
                filters={"id": "R1EA-003", "parser": None, "limit": None},
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
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
            _write_catalog_sqlite(output_dir, {"R1EA-003": ["NEPA"]})
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
            retrieval_check = _check(validation, "retrieval_is_reviewer_ready")
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
            _write_catalog_validation(output_dir, passed=True)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
                skipped_source_record_ids=["R1EA-160"],
                catalog_source_count=2,
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
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
            _write_catalog_sqlite(output_dir, {"R1EA-003": ["NEPA"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(result.summary["extraction_complete"])

    def test_evidence_graph_rejects_forged_chunks_after_retrieval_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_catalog_validation(output_dir, passed=True)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-010"],
            )
            chunks_path = _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
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
            _write_catalog_sqlite(output_dir, {"R1EA-010": ["Connected actions"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            chunks = _read_jsonl(chunks_path)
            forged_text = "A forged replacement span should not bind to retrieval."
            chunks[0]["text"] = forged_text
            chunks[0]["char_end"] = len(forged_text)
            chunks[0]["content_sha256"] = hashlib.sha256(
                forged_text.encode("utf-8")
            ).hexdigest()
            _write_jsonl(chunks_path, chunks)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.nodes_path.exists())
            self.assertGreater(result.summary["retrieval_binding_mismatch_count"], 0)
            self.assertEqual(result.summary["chunk_hash_mismatch_count"], 0)
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(_check(validation, "chunks_match_retrieval_index")["passed"])
            self.assertTrue(_check(validation, "chunk_content_hashes_match_text")["passed"])
            phase_eval = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )
            graph_phase = _phase(phase_eval.summary, "evidence_graph")
            self.assertEqual(graph_phase["details"]["freshness_status"], "failed")
            self.assertIn(
                "chunks_match_retrieval_index",
                graph_phase["details"]["failed_validation_checks"],
            )

    def test_evidence_graph_rejects_chunk_source_set_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_catalog_validation(output_dir, passed=True)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-011"],
            )
            chunks_path = _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
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
            _write_catalog_sqlite(output_dir, {"R1EA-011": ["Forest plan consistency"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            chunks = _read_jsonl(chunks_path)
            chunks[0]["source_set_id"] = "source-set-other"
            _write_jsonl(chunks_path, chunks)

            result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.sqlite_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(_check(validation, "chunk_source_set_ids_match")["passed"])
            self.assertFalse(_check(validation, "chunks_match_retrieval_index")["passed"])

    def test_phase_eval_reports_partial_readiness_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_catalog_validation(output_dir, passed=True)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-004"],
                catalog_source_count=2,
                filters={"id": "R1EA-004", "parser": None, "limit": None},
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-004",
                        title="Diagnostic source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-004 | Diagnostic source | artifact abc123",
                        text="The agency considered feasible alternatives.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-004": ["Alternatives"]})
            build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_extraction=True,
            )
            build_evidence_graph(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_retrieval=True,
            )

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["reviewer_ready"])
            blocker_phases = {blocker["phase"] for blocker in result.summary["blockers"]}
            self.assertIn("extraction", blocker_phases)
            self.assertIn("retrieval", blocker_phases)
            self.assertIn("evidence_graph", blocker_phases)
            self.assertTrue(result.output_path.exists())

    def test_source_set_replay_uses_archived_catalog_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "archived_catalog"
            _write_catalog_validation(output_dir, passed=False)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-020"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
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
            active_sqlite = _write_catalog_sqlite(output_dir, {"R1EA-020": ["Replay"]})
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
            phase_eval = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                catalog_dir=archived_catalog_dir,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))
            self.assertEqual(phase_eval.summary["catalog_dir"], str(archived_catalog_dir))
            graph_phase = _phase(phase_eval.summary, "evidence_graph")
            self.assertTrue(graph_phase["passed"])
            self.assertTrue(graph_phase["reviewer_ready"])

    def test_source_set_phase_eval_ignores_unrelated_gold_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_catalog_validation(output_dir, passed=True)
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-021"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-021",
                        title="Scoped replay source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-021 | Scoped replay source | artifact abc123",
                        text="Source-set phase replay should ignore unrelated global gold evals.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-021": ["Replay"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            gold_eval_dir = output_dir / "reviews" / "compliance_gold_eval"
            gold_eval_dir.mkdir(parents=True, exist_ok=True)
            (gold_eval_dir / "compliance_gold_eval_results.json").write_text(
                json.dumps(
                    {
                        "source_set_id": "source-set-other",
                        "passed": True,
                        "promotion_ready": True,
                        "rule_pack_id": "unit-nepa-ea",
                        "rule_pack_version": "0.4.0",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            phase_names = {phase["name"] for phase in result.summary["phases"]}
            self.assertNotIn("compliance_gold_eval", phase_names)


def _write_catalog_validation(output_dir: Path, *, passed: bool) -> None:
    path = output_dir / "catalog" / "catalog_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"passed": passed}, sort_keys=True), encoding="utf-8")


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
    skipped_source_record_ids: list[str] | None = None,
    catalog_source_count: int | None = None,
    filters: dict | None = None,
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "extraction_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )
    skipped_source_record_ids = skipped_source_record_ids or []
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    manifest_records.extend(
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "skipped_excluded",
        }
        for source_record_id in skipped_source_record_ids
    )
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    selected_count = len(source_record_ids) + len(skipped_source_record_ids)
    catalog_count = catalog_source_count if catalog_source_count is not None else selected_count
    required_count = catalog_count - len(skipped_source_record_ids)
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": catalog_count,
        "artifact_bearing_source_count": required_count,
        "required_extraction_source_count": required_count,
        "selected_source_count": selected_count,
        "selected_required_extraction_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "failed_count": 0,
        "skipped_excluded_count": len(skipped_source_record_ids),
        "filters": filters or {"id": None, "parser": None, "limit": None},
    }
    (diagnostics_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        text_path = output_dir / chunk["source_text_path"]
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(chunk["text"], encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_catalog_sqlite(output_dir: Path, topics_by_source: dict[str, list[str]]) -> Path:
    path = output_dir / "catalog" / "review_sources.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE sources (
              source_record_id TEXT PRIMARY KEY,
              issuer TEXT,
              scope TEXT,
              applies_to TEXT,
              trigger TEXT,
              currentness_notes TEXT
            );
            CREATE TABLE review_topics (
              topic_id TEXT PRIMARY KEY,
              label TEXT NOT NULL
            );
            CREATE TABLE source_review_topics (
              source_record_id TEXT NOT NULL,
              topic_id TEXT NOT NULL,
              PRIMARY KEY (source_record_id, topic_id)
            );
            """
        )
        for source_record_id, topics in topics_by_source.items():
            connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?)",
                (
                    source_record_id,
                    "Test issuer",
                    "test scope",
                    "test applicability",
                    None,
                    None,
                ),
            )
            for index, topic in enumerate(topics):
                topic_id = f"topic:{source_record_id}:{index}"
                connection.execute("INSERT INTO review_topics VALUES (?, ?)", (topic_id, topic))
                connection.execute(
                    "INSERT INTO source_review_topics VALUES (?, ?)",
                    (source_record_id, topic_id),
                )
        connection.commit()
    return path


def _chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    title: str,
    document_role: str,
    authority_level: str,
    citation_label: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "support_document_role": document_role,
        "authority_level": authority_level,
        "host": "example.test",
        "expected_parser": "html",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "citation_label": citation_label,
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-04-30T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": title,
        "content_sha256": content_sha256,
        "text": text,
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")


def _phase(summary: dict, name: str) -> dict:
    for phase in summary["phases"]:
        if phase["name"] == name:
            return phase
    raise AssertionError(f"Missing phase {name}")


if __name__ == "__main__":
    unittest.main()
