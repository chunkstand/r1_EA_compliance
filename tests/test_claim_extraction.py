from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.claim_extraction import run_claim_eval
from usfs_r1_ea_sources.claim_extraction import validate_claim_outputs
from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links


class ClaimExtractionTests(unittest.TestCase):
    def test_claim_extraction_builds_claim_entity_and_graph_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Level of review",
                        document_role="law",
                        authority_level="federal",
                        citation_label="R1EA-003 | Level of review | artifact abc123",
                        text=(
                            "An agency shall prepare an environmental assessment when the "
                            "significance of effects is unknown under 42 U.S.C. 4336."
                        ),
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-014",
                        title="FONSI availability",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-014 | FONSI availability | artifact def456",
                        text="USDA shall make the FONSI available to the public.",
                    ),
                ],
            )

            result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["claim_count"], 2)
            self.assertGreaterEqual(result.summary["entity_count"], 2)
            self.assertTrue(result.claims_path.exists())
            self.assertTrue(result.entities_path.exists())
            self.assertTrue(result.nodes_path.exists())
            self.assertTrue(result.edges_path.exists())
            self.assertTrue(result.sqlite_path.exists())

            claims = _read_jsonl(result.claims_path)
            self.assertEqual({claim["claim_type"] for claim in claims}, {"condition", "obligation"})
            claim = claims[0]
            self.assertEqual(
                claim["claim_text"],
                "An agency shall prepare an environmental assessment when the "
                "significance of effects is unknown under 42 U.S.C. 4336.",
            )
            self.assertEqual(claim["source_char_start"], 0)
            self.assertEqual(claim["chunk_char_start"], 0)
            self.assertTrue(claim["citation_label"])

            nodes = _read_jsonl(result.nodes_path)
            edges = _read_jsonl(result.edges_path)
            self.assertIn("Claim", {node["type"] for node in nodes})
            self.assertIn("Entity", {node["type"] for node in nodes})
            self.assertIn("Authority", {node["type"] for node in nodes})
            self.assertIn("ClaimEvidenceSpan", {node["type"] for node in nodes})
            self.assertIn("CHUNK_HAS_CLAIM", {edge["relationship"] for edge in edges})
            self.assertIn("CLAIM_HAS_EVIDENCE_SPAN", {edge["relationship"] for edge in edges})
            self.assertIn("CLAIM_MENTIONS_ENTITY", {edge["relationship"] for edge in edges})

    def test_claim_eval_scores_expected_claims_terms_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-014",
                        title="FONSI availability",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-014 | FONSI availability | artifact def456",
                        text="USDA shall make the FONSI available to the public.",
                    )
                ],
            )
            claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "claim_eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "fonsi-public",
                            "query": "FONSI available public",
                            "expected_source_record_ids": ["R1EA-014"],
                            "expected_claim_type": "obligation",
                            "expected_terms": ["FONSI", "public"],
                            "filters": {"source_record_id": "R1EA-014"},
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_claim_eval(claims_path=claims.claims_path, eval_file=eval_file)

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["metrics"]["pass_rate"], 1.0)
            self.assertEqual(result.summary["metrics"]["citation_coverage_rate"], 1.0)
            self.assertTrue(result.output_path.exists())

    def test_claim_eval_revalidates_current_claim_artifacts_before_scoring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-014",
                        title="FONSI availability",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-014 | FONSI availability | artifact def456",
                        text="USDA shall make the FONSI available to the public.",
                    )
                ],
            )
            result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            claims = _read_jsonl(result.claims_path)
            claims[0]["claim_text"] = "Tampered claim text."
            _write_jsonl(result.claims_path, claims)
            eval_file = _write_claim_eval_file(output_dir)

            with self.assertRaisesRegex(ValueError, "Current claim artifacts failed validation"):
                run_claim_eval(claims_path=result.claims_path, eval_file=eval_file)

            self.assertFalse((result.claims_dir / "claim_eval_results.json").exists())

    def test_claim_eval_rejects_unsupported_or_empty_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-014",
                        title="FONSI availability",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-014 | FONSI availability | artifact def456",
                        text="USDA shall make the FONSI available to the public.",
                    )
                ],
            )
            result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "bad_claim_eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "bad-filter",
                            "query": "FONSI public",
                            "filters": {"source_record_ids": ["R1EA-014"], "claim_type": ""},
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unsupported filters"):
                run_claim_eval(claims_path=result.claims_path, eval_file=eval_file)

    def test_claim_validation_rejects_tampered_unsupported_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-001",
                        title="Purpose and need",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-001 | Purpose and need | artifact abc123",
                        text="The agency must identify the purpose and need.",
                    )
                ],
            )
            result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            claims = _read_jsonl(result.claims_path)
            claims[0]["claim_type"] = "model_generated_conclusion"
            claims[0]["pattern_id"] = "unsupported"
            _write_jsonl(result.claims_path, claims)

            validation = validate_claim_outputs(
                output_dir=output_dir,
                source_set_id=source_set_id,
                claims_path=result.claims_path,
                entities_path=result.entities_path,
                nodes_path=result.nodes_path,
                edges_path=result.edges_path,
                chunks_path=output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl",
            )

            self.assertFalse(validation["passed"])
            self.assertFalse(_check(validation, "claim_types_are_supported")["passed"])
            self.assertFalse(_check(validation, "no_unsupported_claims_emitted")["passed"])

    def test_claim_extraction_deduplicates_overlapping_claims_by_source_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            text = "The responsible official must document the decision."
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-020",
                        title="Decision documentation",
                        document_role="handbook",
                        authority_level="agency_guidance",
                        citation_label="R1EA-020 | Decision documentation | artifact abc123",
                        text=text,
                        chunk_id="chunk:R1EA-020:a",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-020",
                        title="Decision documentation",
                        document_role="handbook",
                        authority_level="agency_guidance",
                        citation_label="R1EA-020 | Decision documentation | artifact abc123",
                        text=text,
                        chunk_id="chunk:R1EA-020:b",
                    ),
                ],
            )

            result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["claim_count"], 1)

    def test_phase_eval_reports_claim_extraction_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _prepare_source_library(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Level of review",
                        document_role="law",
                        authority_level="federal",
                        citation_label="R1EA-003 | Level of review | artifact abc123",
                        text="An agency shall prepare an environmental assessment.",
                    )
                ],
            )
            build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)
            build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp), document_role="law")
            build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )

            result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["reviewer_ready"])
            claim_phase = _phase(result.summary, "claim_extraction")
            self.assertTrue(claim_phase["passed"])
            self.assertTrue(claim_phase["reviewer_ready"])
            self.assertEqual(claim_phase["details"]["claim_count"], 1)
            rule_claim_phase = _phase(result.summary, "rule_claim_binding")
            self.assertTrue(rule_claim_phase["passed"])
            self.assertTrue(rule_claim_phase["reviewer_ready"])


def _prepare_source_library(output_dir: Path, source_set_id: str, chunks: list[dict]) -> None:
    _write_catalog_validation(output_dir, passed=True)
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=sorted({chunk["source_record_id"] for chunk in chunks}),
    )
    _write_chunks(output_dir, source_set_id, chunks)
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [f"Topic {source_record_id}"]
            for source_record_id in sorted({chunk["source_record_id"] for chunk in chunks})
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)


def _write_catalog_validation(output_dir: Path, *, passed: bool) -> None:
    path = output_dir / "catalog" / "catalog_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"passed": passed}, sort_keys=True), encoding="utf-8")


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
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
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": len(source_record_ids),
        "selected_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "filters": {"id": None, "parser": None, "limit": None},
    }
    (diagnostics_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "source_set_manifest.json").write_text(
        json.dumps({"source_set_id": source_set_id}, sort_keys=True),
        encoding="utf-8",
    )


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text_by_path: dict[str, str] = {}
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        source_text_by_path[str(output_dir / chunk["source_text_path"])] = chunk["text"]
    for text_path, text in source_text_by_path.items():
        path_obj = Path(text_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(text, encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_claim_eval_file(output_dir: Path) -> Path:
    eval_file = output_dir / "claim_eval.json"
    eval_file.write_text(
        json.dumps(
            [
                {
                    "id": "fonsi-public",
                    "query": "FONSI available public",
                    "expected_source_record_ids": ["R1EA-014"],
                    "expected_claim_type": "obligation",
                    "expected_terms": ["FONSI", "public"],
                    "filters": {"source_record_id": "R1EA-014"},
                }
            ],
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return eval_file


def _write_rule_pack(directory: Path, *, document_role: str) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "title": "Unit NEPA EA Rule Pack",
        "description": "Unit test rule pack.",
        "rules": [
            {
                "id": "level_of_review",
                "title": "EA level of review",
                "question": "Does the source explain when an EA is prepared?",
                "requirement": "An agency shall prepare an environmental assessment.",
                "authority_category": "law",
                "authority_source_record_id": "R1EA-003",
                "authority_document_role": document_role,
                "applicability_mode": "baseline",
                "package_query": "environmental assessment",
                "package_terms": ["environmental assessment"],
                "source_query": "agency shall prepare environmental assessment",
                "source_filters": {"document_role": document_role},
                "severity": "high",
            }
        ],
    }
    path = directory / "rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
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
            CREATE TABLE sources (
              source_record_id TEXT PRIMARY KEY,
              issuer TEXT,
              scope TEXT,
              applies_to TEXT,
              trigger TEXT,
              currentness_notes TEXT
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
                (source_record_id, "Test issuer", "test scope", "test applicability", None, None),
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
    chunk_id: str | None = None,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": chunk_id or f"chunk:{source_record_id}",
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
