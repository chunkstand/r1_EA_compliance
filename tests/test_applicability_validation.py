from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.applicability_validation import apply_applicability_adjudication
from usfs_r1_ea_sources.applicability_validation import evaluate_applicability_adjudication
from usfs_r1_ea_sources.applicability_validation import validate_applicability_run
from usfs_r1_ea_sources.applicability_validation import (
    write_applicability_adjudication_template,
)
from usfs_r1_ea_sources.cli import main

from tests.support.applicability_decision_fixtures import _build_adjudicated_applicability_dir
from tests.support.applicability_decision_fixtures import _write_decision_fixture
from tests.support.applicability_decision_support import (
    _forest_plan_scope_miss_candidate,
)
from tests.support.applicability_decision_support import _read_jsonl
from tests.support.applicability_decision_support import _write_json
from tests.support.applicability_decision_support import _write_jsonl


class ApplicabilityValidationTests(unittest.TestCase):
    def test_validation_fails_closed_until_adjudication_resolves_open_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["generated_rule_pack_ready"])
            self.assertEqual(result.summary["needs_adjudication_authority_count"], 1)
            self.assertTrue(result.validation_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertIn(
                "unresolved_authority",
                validation["summary"]["failure_category_counts"],
            )
            self.assertIn(
                "rule-template:unit-pack:0.1.0:cwa_permit",
                {
                    failure["candidate_authority_id"]
                    for failure in validation["failures"]
                    if failure["failure_category"] == "unresolved_authority"
                },
            )

    def test_adjudication_apply_resolves_decisions_and_validation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            template_result = write_applicability_adjudication_template(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            template = json.loads(template_result.output_path.read_text(encoding="utf-8"))
            self.assertEqual(template["schema_version"], "applicability-adjudication-template-v0")
            self.assertEqual(len(template["items"]), 1)
            item = template["items"][0]
            self.assertEqual(
                item["candidate_authority_id"],
                "rule-template:unit-pack:0.1.0:cwa_permit",
            )
            item["final_status"] = "applicable"
            item["disposition"] = "human_applicable"
            item["adjudicated_at"] = "2026-05-04T00:00:00Z"
            item["adjudicated_by"] = ["unit-reviewer"]
            item["source_type"] = "test-adjudication"
            item["rationale"] = (
                "The weak Clean Water Act signal is treated as applicable for this replay."
            )
            item["supporting_citation_refs"] = sorted(
                set(item["supporting_citation_refs"] + ["EA-PACKAGE-001"])
            )
            _write_json(template_result.output_path, template)

            eval_result = evaluate_applicability_adjudication(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                adjudication_file=template_result.output_path,
            )
            self.assertTrue(eval_result.summary["passed"])

            apply_result = apply_applicability_adjudication(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                adjudication_file=template_result.output_path,
            )
            self.assertTrue(apply_result.summary["passed"])
            self.assertEqual(apply_result.summary["remaining_unresolved_authority_count"], 0)

            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            decisions = {
                row["candidate_authority_id"]: row
                for row in _read_jsonl(applicability_dir / "applicability_decisions.jsonl")
            }
            cwa_decision = decisions["rule-template:unit-pack:0.1.0:cwa_permit"]
            self.assertEqual(cwa_decision["status"], "applicable")
            self.assertEqual(cwa_decision["basis_type"], "human_adjudication")
            self.assertEqual(cwa_decision["adjudication_state"], "resolved")
            self.assertTrue(cwa_decision["human_adjudication_refs"])
            applicable = json.loads(
                (applicability_dir / "applicable_authorities.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(applicable["applicable_authority_count"], 4)

            validation_result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            self.assertTrue(validation_result.summary["passed"])
            self.assertTrue(validation_result.summary["generated_rule_pack_ready"])

    def test_validation_rejects_failed_package_fact_graph_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            validation_path = applicability_dir / "package_fact_graph_validation.json"
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            validation["validation"]["passed"] = False
            validation["summary"]["validation_passed"] = False
            _write_json(validation_path, validation)

            result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertFalse(result.summary["passed"])
            self.assertIn("package_cache_stale", result.summary["failure_category_counts"])

    def test_validation_rejects_stale_coverage_partition_and_provenance_hashes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)

            coverage_path = applicability_dir / "search_coverage_certificates.json"
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            coverage["retrieval_trace_sha256"] = "stale-retrieval-trace"
            _write_json(coverage_path, coverage)

            applicable_path = applicability_dir / "applicable_authorities.json"
            applicable = json.loads(applicable_path.read_text(encoding="utf-8"))
            applicable["package_fact_graph_sha256"] = "stale-package-graph"
            _write_json(applicable_path, applicable)

            provenance_path = applicability_dir / "applicability_provenance.json"
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            for entity in provenance["entities"]:
                if entity["entity_id"] == "decision_ledger":
                    entity["sha256"] = "stale-decision-ledger"
            _write_json(provenance_path, provenance)

            result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            categories = result.summary["failure_category_counts"]
            self.assertFalse(result.summary["passed"])
            self.assertIn("retrieval_trace_stale", categories)
            self.assertIn("package_cache_stale", categories)
            self.assertIn("provenance_gap", categories)

    def test_validation_rejects_unreplayable_human_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            eval_path = applicability_dir / "applicability_adjudication_eval.json"
            eval_payload = json.loads(eval_path.read_text(encoding="utf-8"))
            eval_payload["summary"]["passed"] = False
            _write_json(eval_path, eval_payload)

            result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertFalse(result.summary["passed"])
            self.assertIn("adjudication_missing", result.summary["failure_category_counts"])

    def test_validation_rejects_contradictory_final_decision_without_adjudication(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            decisions_path = applicability_dir / "applicability_decisions.jsonl"
            decisions = _read_jsonl(decisions_path)
            for decision in decisions:
                if (
                    decision["candidate_authority_id"]
                    == "rule-template:unit-pack:0.1.0:cwa_permit"
                ):
                    decision["human_adjudication_refs"] = []
                    decision["basis_type"] = "package_positive_trigger"
                    decision["adjudication_state"] = "not_required"
                    decision["negative_evidence_spans"] = [
                        {
                            "evidence_id": "unit-negative-span",
                            "citation_label": "EA-PACKAGE-001",
                        }
                    ]
            _write_jsonl(decisions_path, decisions)

            result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertFalse(result.summary["passed"])
            self.assertIn(
                "contradictory_package_evidence",
                result.summary["failure_category_counts"],
            )

    def test_validation_reports_candidate_basis_and_trace_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            decision_result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            decisions = _read_jsonl(decision_result.decisions_path)
            decisions = [
                decision
                for decision in decisions
                if decision["candidate_authority_id"]
                != "rule-template:unit-pack:0.1.0:esa_consultation"
            ]
            for decision in decisions:
                if (
                    decision["candidate_authority_id"]
                    == "rule-template:unit-pack:0.1.0:ce_fanec"
                ):
                    decision["explicit_trigger_miss_evidence"] = []
                    decision["negative_evidence_spans"] = []
                    decision["search_coverage_certificate_ids"] = []
                if (
                    decision["candidate_authority_id"]
                    == "forest-plan-component:unit-inventory:STD-FP-01"
                ):
                    decision["graph_path_ids"] = ["missing-graph-path"]
            _write_jsonl(decision_result.decisions_path, decisions)

            result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertFalse(result.summary["passed"])
            categories = result.summary["failure_category_counts"]
            self.assertIn("missing_candidate_decision", categories)
            self.assertIn("non_applicable_basis_gap", categories)
            self.assertIn("search_coverage_gap", categories)
            self.assertIn("graph_trace_gap", categories)

    def test_forest_plan_scope_miss_records_trigger_miss_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(
                Path(tmp),
                extra_candidates=[
                    _forest_plan_scope_miss_candidate("source-set-unit"),
                ],
            )

            decision_result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            decisions = {
                decision["candidate_authority_id"]: decision
                for decision in _read_jsonl(decision_result.decisions_path)
            }
            missed = decisions[
                "forest-plan-component:unit-inventory:STD-FP-MISS"
            ]
            self.assertEqual(missed["status"], "not_applicable")
            self.assertEqual(missed["basis_type"], "forest_plan_component")
            self.assertTrue(missed["source_library_evidence_spans"])
            self.assertEqual(len(missed["explicit_trigger_miss_evidence"]), 1)
            trigger_miss = missed["explicit_trigger_miss_evidence"][0]
            self.assertTrue(trigger_miss["coverage_sufficient"])
            self.assertEqual(
                trigger_miss["missing_package_values"],
                [
                    "geography:geo-absent",
                    "management_area:mgmt-absent",
                ],
            )
            self.assertEqual(
                trigger_miss["missing_trigger_groups"],
                [["Absent Forest Plan Area"]],
            )
            self.assertIn("bm25", trigger_miss["executed_query_variants"])
            self.assertIn("metadata_filter", trigger_miss["executed_query_variants"])

            validation = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            categories = validation.summary["failure_category_counts"]
            self.assertNotIn("forest_plan_scope_unresolved", categories)
            self.assertNotIn("non_applicable_basis_gap", categories)

    def test_cli_writes_validation_and_adjudication_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            template_exit_code = main(
                [
                    "applicability-adjudication-template",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                ]
            )
            validation_exit_code = main(
                [
                    "applicability-validate",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                ]
            )

            self.assertEqual(template_exit_code, 0)
            self.assertEqual(validation_exit_code, 1)
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            self.assertTrue(
                (applicability_dir / "applicability_adjudication_template.json").exists()
            )
            self.assertTrue(
                (applicability_dir / "applicability_adjudication_worklist.md").exists()
            )
            self.assertTrue((applicability_dir / "applicability_validation.json").exists())

    def test_apply_accepts_minimal_external_adjudication_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_decision_fixture(root)
            build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            template_result = write_applicability_adjudication_template(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            template = json.loads(template_result.output_path.read_text(encoding="utf-8"))
            item = template["items"][0]
            external_adjudication_path = root / "tracked" / "adjudication.json"
            _write_json(
                external_adjudication_path,
                {
                    "schema_version": "applicability-adjudication-template-v0",
                    "adjudication_id": template["adjudication_id"],
                    "created_at": template["created_at"],
                    "review_id": fixture["review_id"],
                    "source_set_id": fixture["source_set_id"],
                    "decisions_path": template["decisions_path"],
                    "applicability_decisions_sha256": template[
                        "applicability_decisions_sha256"
                    ],
                    "allowed_final_statuses": template["allowed_final_statuses"],
                    "allowed_dispositions": template["allowed_dispositions"],
                    "resolved_dispositions": template["resolved_dispositions"],
                    "required_adjudication_fields": template[
                        "required_adjudication_fields"
                    ],
                    "summary": {
                        **template["summary"],
                        "output_path": str(external_adjudication_path),
                        "markdown_path": str(
                            external_adjudication_path.with_suffix(".worklist.md")
                        ),
                        "pending_item_count": 0,
                    },
                    "items": [
                        {
                            "item_id": item["item_id"],
                            "decision_id": item["decision_id"],
                            "candidate_authority_id": item["candidate_authority_id"],
                            "authority_category": item["authority_category"],
                            "authority_document_role": item["authority_document_role"],
                            "current_status": item["current_status"],
                            "current_basis_type": item["current_basis_type"],
                            "expected_current": item["expected_current"],
                            "final_status": "applicable",
                            "disposition": "human_applicable",
                            "allowed_final_statuses": item["allowed_final_statuses"],
                            "allowed_dispositions": item["allowed_dispositions"],
                            "adjudicated_at": "2026-05-04T00:00:00Z",
                            "adjudicated_by": ["codex"],
                            "source_type": "codex_artifact_review",
                            "rationale": (
                                "Applicable for replay: the package contains wetlands and "
                                "possible Clean Water Act trigger evidence, and the negative "
                                "phrases are parcel-specific or no-action context."
                            ),
                            "supporting_citation_refs": [
                                "EA-PACKAGE-001",
                                "EA-PACKAGE-004",
                                "R1EA-082",
                            ],
                            "reviewer_notes": "",
                        }
                    ],
                },
            )

            eval_result = evaluate_applicability_adjudication(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                adjudication_file=external_adjudication_path,
            )
            self.assertTrue(eval_result.summary["passed"])
            self.assertEqual(
                eval_result.summary["adjudication_file"],
                str(external_adjudication_path),
            )

            apply_result = apply_applicability_adjudication(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                adjudication_file=external_adjudication_path,
            )
            self.assertTrue(apply_result.summary["passed"])
            self.assertEqual(
                apply_result.summary["adjudication_file"],
                str(external_adjudication_path),
            )

            validation_result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            self.assertTrue(validation_result.summary["passed"])
