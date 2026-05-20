from __future__ import annotations

from pathlib import Path
import hashlib
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_decision_outputs import APPLICABILITY_PROVENANCE_SCHEMA_VERSION
from usfs_r1_ea_sources.applicability_decision_outputs import decision_provenance
from usfs_r1_ea_sources.applicability_decision_outputs import decision_summary
from usfs_r1_ea_sources.applicability_decision_outputs import partition_authority_record
from usfs_r1_ea_sources.applicability_decision_outputs import write_decision_report
from usfs_r1_ea_sources.records import sha256_file


class ApplicabilityDecisionOutputsTests(unittest.TestCase):
    def test_partition_record_and_summary_preserve_decision_output_contract(self) -> None:
        decisions = [
            _decision(
                candidate_authority_id="rule-template:unit-pack:0.1.0:baseline_nepa",
                status="applicable",
                basis_type="mandatory_baseline",
                candidate_authority_type="rule_template",
                rule_template={
                    "rule_id": "baseline_nepa",
                    "base_rule_pack_id": "unit-pack",
                    "base_rule_pack_version": "0.1.0",
                    "title": "NEPA baseline",
                    "severity": "medium",
                },
            ),
            _decision(
                candidate_authority_id="forest-plan-component:unit:STD-01",
                status="not_applicable",
                basis_type="forest_plan_component",
                candidate_authority_type="forest_plan_component",
                forest_plan={
                    "forest_unit_id": "flathead-nf",
                    "component_inventory_id": "unit-inventory",
                    "component_id": "STD-01",
                    "component_type": "standard",
                    "section_heading": "Unit standard",
                },
                authority_family_ids=["nfma_forest_planning_project_consistency"],
            ),
            _decision(
                candidate_authority_id="rule-template:unit-pack:0.1.0:cwa_permit",
                status="needs_adjudication",
                basis_type="unresolved_evidence_conflict",
                candidate_authority_type="rule_template",
                rule_template={
                    "rule_id": "cwa_permit",
                    "base_rule_pack_id": "unit-pack",
                    "base_rule_pack_version": "0.1.0",
                    "title": "Clean Water Act permit",
                    "severity": "medium",
                },
            ),
        ]
        certificates = [
            {"coverage_result": "sufficient"},
            {"coverage_result": "adjudication_required"},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = decision_summary(
                review_id="review-unit",
                source_set_id="source-set-unit",
                applicability_run_id="applicability-determine:review-unit:source-set-unit",
                decisions=decisions,
                certificates=certificates,
                decisions_path=root / "applicability_decisions.jsonl",
                applicable_authorities_path=root / "applicable_authorities.json",
                non_applicable_authorities_path=root / "non_applicable_authorities.json",
                search_coverage_certificates_path=root / "search_coverage_certificates.json",
            )

        self.assertTrue(summary["validation_passed"])
        self.assertFalse(summary["generated_rule_pack_ready"])
        self.assertEqual(summary["candidate_authority_count"], 3)
        self.assertEqual(
            summary["decision_status_counts"],
            {
                "applicable": 1,
                "needs_adjudication": 1,
                "not_applicable": 1,
            },
        )
        self.assertEqual(
            summary["coverage_result_counts"],
            {
                "adjudication_required": 1,
                "sufficient": 1,
            },
        )

        applicable = partition_authority_record(decisions[0])
        self.assertEqual(applicable["generated_rule_metadata"]["source_base_rule_id"], "baseline_nepa")
        self.assertIsNone(applicable["non_applicability_basis"])

        non_applicable = partition_authority_record(decisions[1])
        self.assertEqual(
            non_applicable["generated_rule_metadata"]["component_inventory_id"],
            "unit-inventory",
        )
        self.assertEqual(
            non_applicable["non_applicability_basis"]["rationale"],
            decisions[1]["basis"]["rationale"],
        )

    def test_write_decision_report_renders_arbitration_diagnostics(self) -> None:
        decision = _decision(
            candidate_authority_id="rule-template:unit-pack:0.1.0:roads_access",
            status="applicable",
            basis_type="positive_package_trigger",
            candidate_authority_type="rule_template",
            rule_template={"rule_id": "roads_access"},
            arbitration_summary={
                "decision_effect": "positive_trigger_decisive_with_weak_auxiliary",
                "weak_auxiliary_trigger_groups": [["trail"]],
                "arbitration_notes": ["weak package chunk signal"],
                "positive_trigger_groups": [
                    {
                        "trigger_group": ["road"],
                        "matched": True,
                        "diagnostic_treatment": "decisive",
                        "evidence_ids": ["evidence-road"],
                        "evidence_strength_counts": {"observed": 1},
                        "evidence_strength_class_counts": {"observed": 1},
                    },
                    {
                        "trigger_group": ["trail"],
                        "matched": True,
                        "diagnostic_treatment": "weak_only",
                        "evidence_ids": ["evidence-trail"],
                        "evidence_strength_counts": {"weak_signal": 1},
                        "evidence_strength_class_counts": {"conditional": 1},
                    },
                ],
            },
        )
        plain_decision = _decision(
            candidate_authority_id="rule-template:unit-pack:0.1.0:baseline_nepa",
            status="applicable",
            basis_type="mandatory_baseline",
            candidate_authority_type="rule_template",
            rule_template={"rule_id": "baseline_nepa"},
        )
        summary = {
            "review_id": "review-unit",
            "applicability_run_id": "applicability-determine:review-unit:source-set-unit",
            "source_set_id": "source-set-unit",
            "candidate_authority_count": 2,
            "decision_status_counts": {"applicable": 2},
            "generated_rule_pack_ready": True,
        }

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "applicability_report.md"
            write_decision_report(report_path, summary, [decision, plain_decision])
            report_text = report_path.read_text(encoding="utf-8")

        self.assertIn("Arbitration: `positive_trigger_decisive_with_weak_auxiliary`", report_text)
        self.assertIn("Positive trigger diagnostics:", report_text)
        self.assertIn("`trail`: `weak_only`", report_text)
        self.assertIn("Weak-signal notes: `['weak package chunk signal']`", report_text)
        self.assertIn(
            "`rule-template:unit-pack:0.1.0:baseline_nepa`: `applicable` / `mandatory_baseline`",
            report_text,
        )

    def test_decision_provenance_tracks_entities_relations_and_optional_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            authority_universe_path = _write_text(root / "authority_universe.json", "{}\n")
            package_fact_graph_path = _write_text(root / "package_fact_graph.json", "{}\n")
            package_context_path = _write_text(root / "package_context.json", "{}\n")
            retrieval_trace_path = _write_text(root / "retrieval_trace.jsonl", "{}\n")
            graph_trace_path = _write_text(root / "graph_trace.jsonl", "{}\n")
            decisions_path = _write_text(root / "decisions.jsonl", "{}\n")
            applicable_path = _write_text(root / "applicable.json", "{}\n")
            non_applicable_path = _write_text(root / "non_applicable.json", "{}\n")
            coverage_path = _write_text(root / "coverage.json", "{}\n")
            package_manifest_path = _write_text(root / "package_manifest.jsonl", "{}\n")
            package_chunks_path = _write_text(root / "package_chunks.jsonl", "{}\n")
            catalog_path = _write_text(root / "catalog.jsonl", "{}\n")
            package_context_sha256 = sha256_file(package_context_path)
            package_manifest_sha256 = sha256_file(package_manifest_path)

            provenance = decision_provenance(
                applicability_run_id="applicability-determine:review-unit:source-set-unit",
                review_id="review-unit",
                source_set_id="source-set-unit",
                created_at="2026-05-20T12:00:00Z",
                ended_at="2026-05-20T12:05:00Z",
                authority_universe_path=authority_universe_path,
                package_fact_graph_path=package_fact_graph_path,
                package_applicability_context_path=package_context_path,
                retrieval_trace_path=retrieval_trace_path,
                graph_trace_path=graph_trace_path,
                decisions_path=decisions_path,
                applicable_authorities_path=applicable_path,
                non_applicable_authorities_path=non_applicable_path,
                search_coverage_certificates_path=coverage_path,
                package_manifest_path=package_manifest_path,
                package_chunks_path=package_chunks_path,
                source_set_manifest_path=None,
                source_catalog_path=catalog_path,
                authority_universe_sha256="authority-universe-sha",
                source_set_manifest_sha256="",
                package_manifest_sha256=package_manifest_sha256,
                package_chunks_sha256=sha256_file(package_chunks_path),
                package_fact_graph_sha256=sha256_file(package_fact_graph_path),
                retrieval_trace_sha256=sha256_file(retrieval_trace_path),
                graph_trace_sha256=sha256_file(graph_trace_path),
                search_coverage_certificates_sha256=sha256_file(coverage_path),
                decisions_sha256=sha256_file(decisions_path),
                applicable_authorities_sha256=sha256_file(applicable_path),
                non_applicable_authorities_sha256=sha256_file(non_applicable_path),
            )

        self.assertEqual(
            provenance["schema_version"],
            APPLICABILITY_PROVENANCE_SCHEMA_VERSION,
        )
        self.assertEqual(
            provenance["activities"][0]["ended_at"],
            "2026-05-20T12:05:00Z",
        )
        self.assertEqual(
            provenance["agents"][0]["predicate_version"],
            "deterministic-applicability-predicate-v0",
        )
        entities = {entity["entity_id"]: entity for entity in provenance["entities"]}
        self.assertTrue(entities["package_manifest"]["exists"])
        self.assertTrue(entities["catalog"]["exists"])
        self.assertFalse(entities["source_set_manifest"]["exists"])
        self.assertIsNone(entities["source_set_manifest"]["path"])
        self.assertEqual(
            entities["package_applicability_context"]["sha256"],
            package_context_sha256,
        )
        self.assertEqual(len(provenance["relations"]), 36)
        self.assertEqual(
            provenance["freshness"]["package_manifest_sha256"],
            package_manifest_sha256,
        )


def _decision(
    *,
    candidate_authority_id: str,
    status: str,
    basis_type: str,
    candidate_authority_type: str,
    rule_template: dict | None = None,
    forest_plan: dict | None = None,
    authority_family_ids: list[str] | None = None,
    arbitration_summary: dict | None = None,
) -> dict:
    decision_id = hashlib.sha256(candidate_authority_id.encode("utf-8")).hexdigest()[:24]
    return {
        "decision_id": decision_id,
        "candidate_authority_id": candidate_authority_id,
        "candidate_authority_type": candidate_authority_type,
        "authority_family_ids": authority_family_ids or [],
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "status": status,
        "basis_type": basis_type,
        "basis": {"rationale": f"{candidate_authority_id} rationale"},
        "arbitration_status": arbitration_summary.get("decision_effect")
        if isinstance(arbitration_summary, dict)
        else None,
        "decisive_trigger_groups": [["road"]] if arbitration_summary else [],
        "weak_auxiliary_trigger_groups": arbitration_summary.get("weak_auxiliary_trigger_groups", [])
        if isinstance(arbitration_summary, dict)
        else [],
        "arbitration_rationale": "decision rationale" if arbitration_summary else None,
        "predicate_result": {"status": status, "basis_type": basis_type},
        "retrieval_trace_ids": ["trace-1"],
        "graph_path_ids": ["graph-1"],
        "source_record_ids": ["SRC-001"],
        "authority_category": "law",
        "authority_document_role": "law",
        "rule_template": rule_template,
        "forest_plan": forest_plan,
        "package_evidence_spans": [],
        "source_library_evidence_spans": [],
        "negative_evidence_spans": [],
        "explicit_trigger_miss_evidence": [],
        "search_coverage_certificate_ids": [],
        "human_adjudication_refs": [],
        "arbitration_summary": arbitration_summary,
    }


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
