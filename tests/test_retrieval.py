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
from usfs_r1_ea_sources.retrieval import run_retrieval_eval


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

    def test_retrieval_eval_scores_expected_sources_terms_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Scoping rule",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-003 | Scoping rule | artifact abc123",
                        text="Scoping shall invite public comment about environmental concerns.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-003": ["Scoping"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "scoping",
                            "query": "scoping public comment",
                            "expected_source_record_ids": ["R1EA-003"],
                            "expected_terms": ["scoping", "public comment"],
                            "filters": {"review_topic": "Scoping"},
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            eval_result = run_retrieval_eval(index_path=result.sqlite_path, eval_file=eval_file)

            self.assertTrue(eval_result.summary["passed"])
            self.assertEqual(eval_result.summary["metrics"]["pass_rate"], 1.0)
            self.assertEqual(eval_result.summary["metrics"]["unsupported_answer_rate"], 0.0)
            self.assertTrue(eval_result.output_path.exists())

    def test_retrieval_build_fails_validation_on_bad_chunk_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-004"],
            )
            chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-004",
                title="Bad hash source",
                document_role="regulation",
                authority_level="federal_regulation",
                citation_label="R1EA-004 | Bad hash source | artifact abc123",
                text="This chunk hash has been corrupted.",
            )
            chunk["content_sha256"] = "0" * 64
            _write_chunks(output_dir, source_set_id, [chunk])
            _write_catalog_sqlite(output_dir, {"R1EA-004": ["Integrity"]})

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.sqlite_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            hash_check = _check(validation, "chunk_content_hashes_match_text")
            self.assertFalse(hash_check["passed"])
            self.assertEqual(hash_check["details"]["failure_count"], 1)

    def test_retrieval_build_rejects_partial_extraction_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-005"],
                catalog_source_count=2,
                filters={"id": "R1EA-005", "parser": None, "limit": None},
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-005",
                        title="Partial source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-005 | Partial source | artifact abc123",
                        text="NEPA requires environmental review.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-005": ["NEPA"]})

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.sqlite_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            scope_check = _check(validation, "extraction_scope_is_complete")
            self.assertFalse(scope_check["passed"])
            self.assertEqual(scope_check["details"]["catalog_source_count"], 2)

            diagnostic = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_extraction=True,
            )
            self.assertTrue(diagnostic.summary["validation_passed"])
            self.assertFalse(diagnostic.summary["reviewer_ready"])
            self.assertTrue(diagnostic.sqlite_path.exists())

    def test_retrieval_build_fails_when_extracted_source_has_no_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-006", "R1EA-007"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-006",
                        title="One source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-006 | One source | artifact abc123",
                        text="Alternatives must be considered.",
                    )
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-006": ["Alternatives"],
                    "R1EA-007": ["Scoping"],
                },
            )

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            manifest_check = _check(validation, "indexed_sources_match_extraction_manifest")
            self.assertFalse(manifest_check["passed"])
            self.assertEqual(manifest_check["details"]["missing_from_chunks"], ["R1EA-007"])

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


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
    catalog_source_count: int | None = None,
    filters: dict | None = None,
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "extraction_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    catalog_count = (
        catalog_source_count if catalog_source_count is not None else len(source_record_ids)
    )
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": catalog_count,
        "selected_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
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


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")


if __name__ == "__main__":
    unittest.main()
