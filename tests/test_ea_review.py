from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.ea_review import run_ea_review
from usfs_r1_ea_sources.retrieval import build_retrieval_index


class EAReviewTests(unittest.TestCase):
    def test_ea_review_emits_dual_evidence_and_gap_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
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
                        title="EA requirements",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | EA requirements | artifact abc123",
                        text="An environmental assessment should describe the purpose and need.",
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-002",
                        title="FONSI mitigation",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-002 | FONSI mitigation | artifact def456",
                        text="A finding of no significant impact should address mitigation measures.",
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-001": ["Purpose and need"],
                    "R1EA-002": ["Mitigation"],
                },
            )
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            package_path = Path(tmp) / "ea-package.txt"
            package_path.write_text(
                "Purpose and Need\n\nThe proposed action improves trail access.",
                encoding="utf-8",
            )
            checklist = Path(tmp) / "checklist.json"
            checklist.write_text(
                json.dumps(
                    [
                        {
                            "id": "purpose_need",
                            "title": "Purpose and need are stated",
                            "package_query": "purpose need proposed action",
                            "package_terms": ["purpose and need", "proposed action"],
                            "source_query": "environmental assessment purpose need",
                            "source_filters": {"document_role": "regulation"},
                            "severity": "high",
                        },
                        {
                            "id": "mitigation",
                            "title": "Mitigation is addressed",
                            "package_query": "mitigation measures",
                            "package_terms": ["mitigation"],
                            "source_query": "mitigation measures finding of no significant impact",
                            "source_filters": {"document_role": "regulation"},
                            "severity": "high",
                        },
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_ea_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                checklist_path=checklist,
                review_id="unit-review",
            )

            self.assertTrue(result.json_report_path.exists())
            self.assertTrue(result.markdown_report_path.exists())
            self.assertTrue(result.package_chunks_path.exists())
            self.assertEqual(result.summary["finding_status_counts"], {"gap": 1, "pass": 1})
            self.assertTrue(result.summary["reviewer_ready"])
            report = json.loads(result.json_report_path.read_text(encoding="utf-8"))
            purpose = _finding(report, "purpose_need")
            mitigation = _finding(report, "mitigation")
            self.assertEqual(purpose["status"], "pass")
            self.assertEqual(purpose["package_evidence_status"], "found")
            self.assertEqual(purpose["source_library_evidence_status"], "found")
            self.assertEqual(mitigation["status"], "gap")
            self.assertEqual(mitigation["package_evidence_status"], "not_found")
            self.assertEqual(mitigation["source_library_evidence_status"], "found")
            self.assertIsNone(mitigation["package_evidence"])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])
            self.assertTrue(_check(validation, "source_retrieval_is_reviewer_ready")["passed"])
            self.assertTrue(_check(validation, "gap_findings_have_source_evidence")["passed"])

    def test_ea_review_rejects_non_reviewer_ready_retrieval_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id, retrieval_result = _build_source_library(output_dir)
            summary = json.loads(retrieval_result.summary_path.read_text(encoding="utf-8"))
            summary["reviewer_ready"] = False
            retrieval_result.summary_path.write_text(
                json.dumps(summary, sort_keys=True),
                encoding="utf-8",
            )
            package_path = _write_package(Path(tmp), "Purpose and Need")
            checklist = _write_checklist(Path(tmp))

            with self.assertRaisesRegex(ValueError, "reviewer-ready"):
                run_ea_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    checklist_path=checklist,
                    review_id="not-ready",
                )

    def test_package_search_requires_configured_package_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-001"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-001",
                        title="EA alternatives",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | EA alternatives | artifact abc123",
                        text="An environmental assessment should describe alternatives.",
                    ),
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-001": ["Alternatives"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need\n\nThe proposed action improves trail access.",
            )
            checklist = Path(tmp) / "checklist.json"
            checklist.write_text(
                json.dumps(
                    [
                        {
                            "id": "alternatives",
                            "title": "Alternatives are described",
                            "package_query": "alternatives no action proposed action",
                            "package_terms": ["alternatives", "no action"],
                            "source_query": "environmental assessment alternatives",
                            "source_filters": {"document_role": "regulation"},
                            "severity": "high",
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_ea_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                checklist_path=checklist,
                review_id="required-term-review",
            )

            report = json.loads(result.json_report_path.read_text(encoding="utf-8"))
            alternatives = _finding(report, "alternatives")
            self.assertEqual(alternatives["status"], "gap")
            self.assertEqual(alternatives["package_evidence_status"], "not_found")
            self.assertEqual(alternatives["source_library_evidence_status"], "found")

    def test_package_search_does_not_match_required_term_substrings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-001"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-001",
                        title="Public involvement",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="R1EA-001 | Public involvement | artifact abc123",
                        text="An environmental assessment may include public comment.",
                    ),
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-001": ["Public involvement"]})
            build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Project notes\n\nThe administrative commentary describes routing only.",
            )
            checklist = Path(tmp) / "checklist.json"
            checklist.write_text(
                json.dumps(
                    [
                        {
                            "id": "public_involvement",
                            "title": "Public comment is described",
                            "package_query": "public involvement scoping comment",
                            "package_terms": ["comment"],
                            "source_query": "public comment environmental assessment",
                            "source_filters": {"document_role": "regulation"},
                            "severity": "medium",
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_ea_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                checklist_path=checklist,
                review_id="substring-term-review",
            )

            report = json.loads(result.json_report_path.read_text(encoding="utf-8"))
            finding = _finding(report, "public_involvement")
            self.assertEqual(finding["status"], "gap")
            self.assertEqual(finding["package_evidence_status"], "not_found")

    def test_ea_review_replaces_stale_outputs_for_fixed_review_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id, _retrieval_result = _build_source_library(output_dir)
            checklist = _write_checklist(Path(tmp))
            package_path = _write_package(Path(tmp), "Purpose and Need")
            first = run_ea_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                checklist_path=checklist,
                review_id="repeatable-review",
            )
            stale = first.review_dir / "package" / "extracted_text" / "stale.txt"
            stale.write_text("stale", encoding="utf-8")

            second = run_ea_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                checklist_path=checklist,
                review_id="repeatable-review",
            )

            self.assertEqual(first.review_dir, second.review_dir)
            self.assertFalse(stale.exists())
            self.assertTrue(second.summary["validation_passed"])

    def test_ea_review_rejects_unsafe_fixed_review_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id, _retrieval_result = _build_source_library(output_dir)
            checklist = _write_checklist(Path(tmp))
            package_path = _write_package(Path(tmp), "Purpose and Need")

            with self.assertRaisesRegex(ValueError, "review_id"):
                run_ea_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    checklist_path=checklist,
                    review_id="../bad-review",
                )

            self.assertFalse((Path(tmp) / "bad-review").exists())


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


def _build_source_library(output_dir: Path):
    source_set_id = "source-set-test"
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=["R1EA-001"],
    )
    _write_chunks(
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
            ),
        ],
    )
    _write_catalog_sqlite(output_dir, {"R1EA-001": ["Purpose and need"]})
    return source_set_id, build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)


def _write_package(directory: Path, text: str) -> Path:
    package_path = directory / "ea-package.txt"
    package_path.write_text(text, encoding="utf-8")
    return package_path


def _write_checklist(directory: Path) -> Path:
    checklist = directory / "checklist.json"
    checklist.write_text(
        json.dumps(
            [
                {
                    "id": "purpose_need",
                    "title": "Purpose and need are stated",
                    "package_query": "purpose need",
                    "package_terms": ["purpose and need"],
                    "source_query": "environmental assessment purpose need",
                    "source_filters": {"document_role": "regulation"},
                    "severity": "high",
                }
            ],
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return checklist


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


def _finding(report: dict, finding_id: str) -> dict:
    return next(finding for finding in report["findings"] if finding["id"] == finding_id)


def _check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)
