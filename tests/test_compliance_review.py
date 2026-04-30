from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.compliance_review import run_compliance_review_eval
from usfs_r1_ea_sources.compliance_review import validate_rule_pack
from usfs_r1_ea_sources.compliance_coverage import run_compliance_coverage
from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.evidence_graph import run_phase_aligned_eval
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links


class ComplianceReviewTests(unittest.TestCase):
    def test_compliance_review_emits_rule_pack_findings_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(
                Path(tmp),
                "Purpose and Need\n\nThe proposed action improves trail access.",
            )
            rule_pack_path = _write_rule_pack(Path(tmp))

            result = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="compliance-unit",
            )

            self.assertTrue(result.compliance_review_path.exists())
            self.assertTrue(result.compliance_validation_path.exists())
            self.assertTrue(result.finding_nodes_path.exists())
            self.assertTrue(result.finding_edges_path.exists())
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["finding_status_counts"], {"gap": 1, "pass": 1})

            report = json.loads(result.compliance_review_path.read_text(encoding="utf-8"))
            purpose = _finding(report, "purpose_need")
            mitigation = _finding(report, "mitigation")
            self.assertEqual(purpose["status"], "pass")
            self.assertEqual(purpose["claim_type"], "supported_compliance_finding")
            self.assertTrue(purpose["source_library_evidence_citation"])
            self.assertTrue(purpose["package_evidence_citation"])
            self.assertGreaterEqual(purpose["source_claim_link_count"], 1)
            self.assertTrue(purpose["source_claim_links"][0]["claim_id"])
            self.assertEqual(mitigation["status"], "gap")
            self.assertEqual(mitigation["claim_type"], "package_evidence_gap")
            self.assertTrue(mitigation["source_library_evidence_citation"])
            self.assertIsNone(mitigation["package_evidence_citation"])
            self.assertGreaterEqual(mitigation["source_claim_link_count"], 1)

            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            self.assertTrue(validation["passed"])
            self.assertTrue(_check(validation, "all_rules_evaluated")["passed"])
            self.assertTrue(
                _check(validation, "claim_findings_have_source_citations")["passed"]
            )
            self.assertTrue(
                _check(validation, "claim_findings_have_source_claim_links")["passed"]
            )
            nodes = _read_jsonl(result.finding_nodes_path)
            edges = _read_jsonl(result.finding_edges_path)
            self.assertIn("ComplianceRulePack", {node["type"] for node in nodes})
            self.assertIn("ComplianceRule", {node["type"] for node in nodes})
            self.assertIn("ComplianceFinding", {node["type"] for node in nodes})
            self.assertIn("SourceClaim", {node["type"] for node in nodes})
            self.assertIn("PackageEvidenceGap", {node["type"] for node in nodes})
            self.assertIn(
                "FINDING_SUPPORTED_BY_SOURCE_EVIDENCE",
                {edge["relationship"] for edge in edges},
            )
            self.assertIn(
                "FINDING_SUPPORTED_BY_SOURCE_CLAIM",
                {edge["relationship"] for edge in edges},
            )
            self.assertIn("FINDING_HAS_PACKAGE_GAP", {edge["relationship"] for edge in edges})

    def test_compliance_review_rejects_invalid_rule_pack(self) -> None:
        rule_pack = _rule_pack()
        del rule_pack["rules"][0]["source_query"]

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        self.assertFalse(_check(validation, "required_rule_fields_present")["passed"])

    def test_rule_pack_rejects_unsupported_filters_and_unsafe_ids(self) -> None:
        rule_pack = _rule_pack()
        rule_pack["rule_pack_id"] = "../bad-pack"
        rule_pack["rules"][0]["id"] = "bad/rule"
        rule_pack["rules"][0]["source_filters"] = {
            "document_roles": "regulation",
            "host": "",
        }

        validation = validate_rule_pack(rule_pack)

        self.assertFalse(validation["passed"])
        self.assertFalse(_check(validation, "rule_pack_identity_values_are_safe")["passed"])
        self.assertFalse(_check(validation, "rule_ids_are_safe")["passed"])
        filter_check = _check(validation, "rule_source_filter_keys_are_supported")
        self.assertFalse(filter_check["passed"])
        self.assertEqual(filter_check["details"]["failures"][0]["unknown_keys"], ["document_roles"])
        self.assertEqual(filter_check["details"]["failures"][0]["empty_values"], ["host"])

    def test_compliance_review_rejects_unsafe_review_id_before_writing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])

            with self.assertRaisesRegex(ValueError, "review_id"):
                run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    rule_pack_path=rule_pack_path,
                    review_id="../bad-review",
                )

            self.assertFalse((Path(tmp) / "bad-review").exists())

    def test_compliance_review_eval_scores_package_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "unit-all-pass",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access "
                            "and mitigation measures support a finding of no significant impact."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                        "expected_unsupported_finding_ids": [],
                        "min_findings": 2,
                    },
                    {
                        "id": "unit-package-gap",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_finding_status_counts": {"gap": 1, "pass": 1},
                        "expected_unsupported_finding_ids": [],
                        "min_findings": 2,
                    },
                ],
            )

            result = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=Path(tmp) / "eval-results",
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["case_count"], 2)
            self.assertEqual(result.summary["passed_count"], 2)
            self.assertEqual(result.summary["metrics"]["pass_rate"], 1.0)
            cases = {case["id"]: case for case in result.summary["cases"]}
            self.assertEqual(
                cases["unit-all-pass"]["actual_statuses"],
                {"mitigation": "pass", "purpose_need": "pass"},
            )
            self.assertEqual(
                cases["unit-package-gap"]["actual_statuses"],
                {"mitigation": "gap", "purpose_need": "pass"},
            )
            self.assertTrue(cases["unit-package-gap"]["citation_coverage_supported"])
            self.assertTrue(cases["unit-package-gap"]["graph_coverage_supported"])

    def test_compliance_review_eval_rejects_bad_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "bad-filter",
                        "package_text": "Purpose and Need",
                        "filters": {"rule_ids": "purpose_need"},
                        "expected_statuses": {"purpose_need": "pass"},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "invalid filters"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_requires_full_rule_pack_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "partial-expectations",
                        "package_text": "Purpose and Need",
                        "expected_statuses": {"purpose_need": "pass"},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "cover every rule"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    rule_pack_path=rule_pack_path,
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_rejects_status_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "bad-status-count",
                        "package_text": "Purpose and Need",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "expected_finding_status_counts"):
                run_compliance_review_eval(
                    output_dir=Path(tmp) / "source_library",
                    rule_pack_path=rule_pack_path,
                    eval_file=eval_path,
                )

    def test_compliance_review_eval_flags_false_pass_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "false-pass",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                        "expected_unsupported_finding_ids": [],
                        "min_findings": 2,
                    }
                ],
            )

            result = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=Path(tmp) / "eval-results",
            )

            self.assertFalse(result.summary["passed"])
            case = result.summary["cases"][0]
            self.assertFalse(case["expected_statuses_match"])
            self.assertFalse(case["expected_claim_types_match"])
            self.assertFalse(case["expected_package_evidence_match"])
            self.assertIn("expected_statuses_match", case["failure_reasons"])
            self.assertEqual(case["actual_statuses"]["mitigation"], "gap")

    def test_compliance_review_eval_replaces_stale_case_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            eval_path = Path(tmp) / "compliance-eval.json"
            results_dir = Path(tmp) / "eval-results"
            _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "stable-case",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access "
                            "and mitigation measures support a finding of no significant impact."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                    }
                ],
                path=eval_path,
            )
            first = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=results_dir,
            )
            self.assertTrue(first.summary["passed"])
            self.assertEqual(first.summary["cases"][0]["actual_statuses"]["mitigation"], "pass")

            _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "stable-case",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                        "expected_finding_status_counts": {"gap": 1, "pass": 1},
                    }
                ],
                path=eval_path,
            )

            second = run_compliance_review_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                eval_file=eval_path,
                results_dir=results_dir,
            )

            self.assertTrue(second.summary["passed"])
            self.assertEqual(second.summary["cases"][0]["actual_statuses"]["mitigation"], "gap")

    def test_compliance_coverage_scores_matrix_links_and_eval_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            link_result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "coverage-case",
                        "package_text": (
                            "Purpose and Need\n\nThe proposed action improves trail access "
                            "and mitigation measures support a finding of no significant impact."
                        ),
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                        "expected_finding_status_counts": {"pass": 2},
                    }
                ],
            )
            coverage_path = _write_coverage_matrix(Path(tmp))

            result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=coverage_path,
                eval_file=eval_path,
                links_path=link_result.links_path,
                results_dir=Path(tmp) / "coverage-results",
            )

            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["rule_count"], 2)
            self.assertEqual(result.summary["coverage_item_count"], 2)
            self.assertGreaterEqual(result.summary["rule_claim_link_count"], 2)
            self.assertEqual(result.summary["rules_without_coverage_items"], [])
            self.assertEqual(result.summary["rules_without_eval_cases"], [])
            self.assertEqual(result.summary["rules_without_source_claim_links"], [])

    def test_compliance_coverage_reports_missing_rule_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            link_result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "coverage-case",
                        "package_text": "Purpose and Need",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "gap",
                        },
                    }
                ],
            )
            coverage_path = _write_coverage_matrix(Path(tmp), rule_ids=["purpose_need"])

            result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=coverage_path,
                eval_file=eval_path,
                links_path=link_result.links_path,
                results_dir=Path(tmp) / "coverage-results",
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["rules_without_coverage_items"], ["mitigation"])
            self.assertFalse(_check(result.summary, "coverage_matrix_covers_every_rule")["passed"])

    def test_phase_eval_rejects_stale_compliance_coverage_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            rule_pack_path = _write_rule_pack(Path(tmp))
            link_result = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
            )
            eval_path = _write_compliance_eval_file(
                Path(tmp),
                [
                    {
                        "id": "coverage-case",
                        "package_text": "Purpose and Need. Mitigation measures support a FONSI.",
                        "expected_statuses": {
                            "purpose_need": "pass",
                            "mitigation": "pass",
                        },
                    }
                ],
            )
            coverage_result = run_compliance_coverage(
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                coverage_matrix_path=_write_coverage_matrix(Path(tmp)),
                eval_file=eval_path,
                links_path=link_result.links_path,
            )
            coverage_summary = json.loads(coverage_result.output_path.read_text(encoding="utf-8"))
            coverage_summary["source_set_id"] = "source-set-other"
            coverage_result.output_path.write_text(
                json.dumps(coverage_summary, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            coverage_phase = _phase(phase_result.summary, "compliance_coverage")
            self.assertFalse(coverage_phase["passed"])
            self.assertFalse(coverage_phase["reviewer_ready"])
            self.assertTrue(coverage_phase["details"]["coverage_passed"])
            self.assertFalse(coverage_phase["details"]["source_set_matches"])

    def test_phase_eval_can_include_compliance_review_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="phase-review",
            )

            result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="phase-review",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.summary["phase_count"], 7)
            claim_phase = _phase(result.summary, "claim_extraction")
            self.assertTrue(claim_phase["passed"])
            self.assertTrue(claim_phase["reviewer_ready"])
            rule_claim_phase = _phase(result.summary, "rule_claim_binding")
            self.assertTrue(rule_claim_phase["passed"])
            self.assertTrue(rule_claim_phase["reviewer_ready"])
            compliance_phase = _phase(result.summary, "compliance_review")
            self.assertTrue(compliance_phase["passed"])
            self.assertTrue(compliance_phase["reviewer_ready"])
            self.assertEqual(compliance_phase["details"]["rule_pack_id"], "unit-nepa-ea")

    def test_phase_eval_rejects_stale_compliance_review_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            _build_source_library(output_dir, source_set_id)
            _write_graph_phase_outputs(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            result = run_compliance_review(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                rule_pack_path=rule_pack_path,
                review_id="stale-review",
            )
            report = json.loads(result.compliance_review_path.read_text(encoding="utf-8"))
            report["summary"]["source_set_id"] = "source-set-other"
            result.compliance_review_path.write_text(
                json.dumps(report, sort_keys=True),
                encoding="utf-8",
            )

            phase_result = run_phase_aligned_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="stale-review",
            )

            self.assertFalse(phase_result.summary["reviewer_ready"])
            compliance_phase = _phase(phase_result.summary, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertFalse(compliance_phase["reviewer_ready"])
            self.assertFalse(compliance_phase["details"]["source_set_matches"])


def _build_source_library(output_dir: Path, source_set_id: str) -> None:
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
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)


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
    (catalog_dir / "catalog_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> None:
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


def _write_catalog_sqlite(output_dir: Path, topics_by_source: dict[str, list[str]]) -> None:
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


def _write_graph_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    graph_dir = output_dir / "derived" / source_set_id / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "evidence_graph_validation.json").write_text(
        json.dumps({"passed": True, "checks": []}, sort_keys=True),
        encoding="utf-8",
    )
    (graph_dir / "summary.json").write_text(
        json.dumps(
            {
                "reviewer_ready": True,
                "validation_passed": True,
                "retrieval_index_path": "index.sqlite",
                "retrieval_index_chunk_count": 2,
                "retrieval_binding_mismatch_count": 0,
                "metrics": {},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


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


def _write_package(directory: Path, text: str) -> Path:
    path = directory / "ea-package.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _write_rule_pack(directory: Path, rule_ids: list[str] | None = None) -> Path:
    rule_pack = _rule_pack()
    if rule_ids is not None:
        rule_pack["rules"] = [rule for rule in rule_pack["rules"] if rule["id"] in set(rule_ids)]
    path = directory / "rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_compliance_eval_file(
    directory: Path,
    cases: list[dict],
    *,
    path: Path | None = None,
) -> Path:
    eval_path = path or directory / "compliance-eval.json"
    eval_path.write_text(json.dumps(cases, sort_keys=True), encoding="utf-8")
    return eval_path


def _write_coverage_matrix(directory: Path, rule_ids: list[str] | None = None) -> Path:
    items = [
        {
            "rule_id": "purpose_need",
            "obligation_area": "Purpose and need",
            "expected_package_evidence": "Purpose and need or proposed action text.",
            "source_record_ids": ["R1EA-001"],
            "source_claim_terms": ["purpose", "need"],
            "eval_case_ids": ["coverage-case"],
        },
        {
            "rule_id": "mitigation",
            "obligation_area": "Mitigation",
            "expected_package_evidence": "Mitigation or FONSI support text.",
            "source_record_ids": ["R1EA-002"],
            "source_claim_terms": ["mitigation"],
            "eval_case_ids": ["coverage-case"],
        },
    ]
    if rule_ids is not None:
        wanted = set(rule_ids)
        items = [item for item in items if item["rule_id"] in wanted]
    path = directory / "coverage-matrix.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-rule-pack-coverage-v0",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "title": "Unit coverage matrix",
                "coverage_items": items,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
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
                "requirement": "Purpose and need should be identified.",
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
                "source_filters": {"document_role": "regulation"},
                "severity": "high",
            },
        ],
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _finding(report: dict, finding_id: str) -> dict:
    return next(finding for finding in report["findings"] if finding["id"] == finding_id)


def _check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)


def _phase(summary: dict, name: str) -> dict:
    return next(phase for phase in summary["phases"] if phase["name"] == name)
