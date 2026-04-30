from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links
from usfs_r1_ea_sources.rule_claim_binding import run_rule_claim_link_eval
from usfs_r1_ea_sources.rule_claim_binding import validate_rule_claim_links


class RuleClaimBindingTests(unittest.TestCase):
    def test_rule_claim_link_builds_links_gaps_and_sqlite(self) -> None:
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
                        title="EA requirements",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | EA requirements | artifact abc123",
                        text="An environmental assessment should describe the purpose and need.",
                    )
                ],
            )
            claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))

            result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                top_k=3,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["rule_count"], 2)
            self.assertEqual(result.summary["linked_rule_count"], 1)
            self.assertEqual(result.summary["gap_rule_count"], 1)
            self.assertEqual(result.summary["rules_without_links"], ["mitigation"])
            self.assertTrue(result.links_path.exists())
            self.assertTrue(result.gaps_path.exists())
            self.assertTrue(result.sqlite_path.exists())

            links = _read_jsonl(result.links_path)
            self.assertEqual(len(links), 1)
            self.assertEqual(links[0]["rule_id"], "purpose_need")
            self.assertEqual(links[0]["claim_id"], _read_jsonl(claims.claims_path)[0]["claim_id"])
            self.assertTrue(links[0]["matched_terms"])

            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])
            self.assertTrue(
                _check(validation, "all_rules_have_claim_link_or_explicit_gap")["passed"]
            )

    def test_rule_claim_eval_scores_expected_rule_claim_links(self) -> None:
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
                        title="EA requirements",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | EA requirements | artifact abc123",
                        text="An environmental assessment should describe the purpose and need.",
                    )
                ],
            )
            build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            links = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            eval_file = output_dir / "rule_claim_eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "purpose-need-link",
                            "rule_id": "purpose_need",
                            "expected_terms": ["purpose", "need"],
                            "expected_claim_types": ["guidance"],
                            "expected_source_record_ids": ["R1EA-001"],
                            "min_links": 1,
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_rule_claim_link_eval(links_path=links.links_path, eval_file=eval_file)

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["metrics"]["pass_rate"], 1.0)
            self.assertEqual(result.summary["metrics"]["citation_coverage_rate"], 1.0)
            self.assertTrue(result.output_path.exists())

    def test_rule_claim_eval_revalidates_links_before_scoring(self) -> None:
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
                        title="EA requirements",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | EA requirements | artifact abc123",
                        text="An environmental assessment should describe the purpose and need.",
                    )
                ],
            )
            build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            links = _read_jsonl(result.links_path)
            links[0]["claim_text"] = "Tampered link claim text."
            _write_jsonl(result.links_path, links)
            eval_file = _write_rule_claim_eval_file(output_dir)

            with self.assertRaisesRegex(
                ValueError,
                "Current rule-claim link artifacts failed validation",
            ):
                run_rule_claim_link_eval(links_path=result.links_path, eval_file=eval_file)

            self.assertFalse((result.links_dir / "rule_claim_link_eval_results.json").exists())

    def test_rule_claim_validation_rejects_unknown_rule_links(self) -> None:
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
                        title="EA requirements",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | EA requirements | artifact abc123",
                        text="An environmental assessment should describe the purpose and need.",
                    )
                ],
            )
            claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            links = _read_jsonl(result.links_path)
            links[0]["rule_id"] = "unknown_rule"
            _write_jsonl(result.links_path, links)

            validation = validate_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                claims_path=claims.claims_path,
                links_path=result.links_path,
                gaps_path=result.gaps_path,
            )

            self.assertFalse(validation["passed"])
            self.assertFalse(
                _check(validation, "all_rules_have_claim_link_or_explicit_gap")["passed"]
            )
            self.assertFalse(_check(validation, "rule_claim_links_match_rule_filters")["passed"])


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


def _write_rule_pack(directory: Path, rule_ids: list[str] | None = None) -> Path:
    rule_pack = _rule_pack()
    if rule_ids is not None:
        rule_pack["rules"] = [rule for rule in rule_pack["rules"] if rule["id"] in set(rule_ids)]
    path = directory / "rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _rule_pack() -> dict:
    return {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "title": "Unit NEPA EA Rule Pack",
        "description": "Unit test rule pack.",
        "rules": [
            {
                "id": "purpose_need",
                "title": "Purpose and need are stated",
                "question": "Does the EA package identify the purpose and need?",
                "requirement": "The EA package should identify the purpose and need.",
                "package_query": "purpose need proposed action",
                "package_terms": ["purpose and need", "proposed action"],
                "source_query": "environmental assessment purpose need",
                "source_filters": {"document_role": "regulation"},
                "severity": "high",
            },
            {
                "id": "mitigation",
                "title": "Mitigation is addressed",
                "question": "Does the EA package address mitigation?",
                "requirement": "Mitigation should be addressed when used to support a finding.",
                "package_query": "mitigation measures",
                "package_terms": ["mitigation"],
                "source_query": "mitigation measures finding of no significant impact",
                "source_filters": {"source_record_id": "R1EA-999"},
                "severity": "high",
            },
        ],
    }


def _write_rule_claim_eval_file(output_dir: Path) -> Path:
    eval_file = output_dir / "rule_claim_eval.json"
    eval_file.write_text(
        json.dumps(
            [
                {
                    "id": "purpose-need-link",
                    "rule_id": "purpose_need",
                    "expected_terms": ["purpose", "need"],
                    "expected_claim_types": ["guidance"],
                    "min_links": 1,
                }
            ],
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return eval_file


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


if __name__ == "__main__":
    unittest.main()
