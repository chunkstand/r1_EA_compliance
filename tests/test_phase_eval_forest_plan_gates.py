from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.phase_eval_optional_phases import _applicability_phase_gates
from usfs_r1_ea_sources.phase_eval_review_phases import build_review_scoped_phases


def _phase_from_list(phases: list[dict], name: str) -> dict:
    for item in phases:
        if item["name"] == name:
            return item
    raise AssertionError(f"Missing phase {name}")


def _minimal_applicability_artifacts(authority_universe: dict) -> dict:
    return {
        "paths": {
            "authority_universe": None,
            "package_fact_graph": None,
            "package_fact_graph_validation": None,
            "applicability_retrieval_trace": None,
            "applicability_graph_trace": None,
            "applicability_trace_diagnostics": None,
            "applicability_decisions": None,
            "applicable_authorities": None,
            "non_applicable_authorities": None,
            "search_coverage_certificates": None,
            "applicability_validation": None,
            "generated_rule_pack": None,
            "generated_rule_pack_validation": None,
        },
        "authority_universe": authority_universe,
        "package_fact_graph": {},
        "package_fact_graph_validation": {},
        "retrieval_rows": [],
        "graph_rows": [],
        "trace_diagnostics": {},
        "decisions": [],
        "applicable_authorities": {},
        "non_applicable_authorities": {},
        "search_coverage_certificates": {},
        "applicability_validation": {},
        "generated_rule_pack": {},
        "generated_rule_pack_validation": {},
    }


class PhaseEvalForestPlanGateTests(unittest.TestCase):
    def test_authority_universe_fails_when_forest_plan_inventory_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "lolo-review"
            source_set_id = "source-set-test"
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)
            canonical_inventory_path = (
                output_dir
                / "derived"
                / source_set_id
                / "forest_plan_components"
                / "component_inventory.json"
            )
            stale_inventory_path = review_dir / "stale_component_inventory.json"
            canonical_inventory_path.parent.mkdir(parents=True, exist_ok=True)
            canonical_inventory_path.write_text('{"components": [{}, {}]}', encoding="utf-8")
            stale_inventory_path.write_text('{"components": [{}]}', encoding="utf-8")
            (review_dir / "forest_plan_context_summary.json").write_text(
                json.dumps(
                    {
                        "schema_version": "forest-plan-context-summary-v0",
                        "review_id": review_id,
                        "source_set_id": source_set_id,
                        "scope_status": "lolo_nf",
                        "component_evaluation": {
                            "component_count": 2,
                            "component_inventory_path": str(canonical_inventory_path),
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            authority_universe = {
                "schema_version": "authority-universe-snapshot-v0",
                "source_set_id": source_set_id,
                "validation": {"passed": True},
                "artifact_paths": {
                    "forest_plan_component_inventory_path": str(stale_inventory_path)
                },
                "candidate_authorities": [
                    {
                        "candidate_authority_id": "forest-plan-component:stale:1",
                        "candidate_authority_type": "forest_plan_component",
                    }
                ],
            }
            phases = _applicability_phase_gates(
                output_dir=output_dir,
                review_dir=review_dir,
                source_set_id=source_set_id,
                artifacts=_minimal_applicability_artifacts(authority_universe),
                arbitration_summary={},
            )

            authority_phase = _phase_from_list(phases, "authority_universe")
            self.assertFalse(authority_phase["passed"])
            self.assertFalse(authority_phase["reviewer_ready"])
            self.assertTrue(
                authority_phase["details"][
                    "forest_plan_authority_universe_currentness_required"
                ]
            )
            self.assertEqual(
                authority_phase["details"]["failed_forest_plan_currentness_checks"],
                [
                    "forest_plan_component_inventory_path_mismatch",
                    "forest_plan_component_candidate_count_mismatch",
                ],
            )

    def test_compliance_phase_requires_forest_plan_matrix_for_non_custer_forests(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "lolo-review"
            source_set_id = "source-set-test"
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = review_dir / "compliance_matrix.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n% unit fixture\n")
            forest_plan_review = {
                "scope_status": "lolo_nf",
                "reviewer_ready": False,
                "component_evaluation": {
                    "component_count": 3,
                    "applicable_standard_count": 2,
                },
            }
            compliance_review = {
                "summary": {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "rule_pack_id": "generated",
                    "rule_pack_version": "1.0",
                    "finding_count": 1,
                    "finding_status_counts": {"complies": 1},
                    "reviewer_ready": False,
                    "forest_plan_review": forest_plan_review,
                }
            }
            compliance_matrix = {
                "schema_version": "compliance-matrix-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "rule_pack": {"rule_pack_id": "generated", "version": "1.0"},
                "summary": {
                    "row_count": 1,
                    "status_counts": {"complies": 1},
                    "forest_plan_review": forest_plan_review,
                },
                "rows": [{"rule_id": "generated-rule", "status": "complies"}],
            }

            phases = _review_phases(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                review_dir=review_dir,
                compliance_validation={"passed": True, "checks": []},
                compliance_review=compliance_review,
                compliance_matrix=compliance_matrix,
                compliance_matrix_pdf_path=pdf_path,
            )

            compliance_phase = _phase_from_list(phases, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertTrue(compliance_phase["details"]["forest_plan_matrix_required"])
            self.assertFalse(
                compliance_phase["details"]["forest_plan_matrix_schema_matches"]
            )
            self.assertIn(
                "forest_plan_matrix_schema_matches",
                compliance_phase["details"]["failed_artifact_checks"],
            )

    def test_compliance_phase_requires_forest_plan_matrix_from_context_summary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            review_id = "lolo-review"
            source_set_id = "source-set-test"
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "forest_plan_context_summary.json").write_text(
                json.dumps(
                    {
                        "schema_version": "forest-plan-context-summary-v0",
                        "review_id": review_id,
                        "source_set_id": source_set_id,
                        "scope_status": "lolo_nf",
                        "component_evaluation": {
                            "component_count": 3,
                            "applicable_standard_count": 2,
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            phases = _review_phases(
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                review_dir=review_dir,
                compliance_matrix_pdf_path=review_dir / "compliance_matrix.pdf",
            )

            compliance_phase = _phase_from_list(phases, "compliance_review")
            self.assertFalse(compliance_phase["passed"])
            self.assertTrue(compliance_phase["details"]["forest_plan_matrix_required"])
            self.assertEqual(
                compliance_phase["details"]["forest_plan_expected_applicable_standard_count"],
                2,
            )
            self.assertIn(
                "forest_plan_matrix_schema_matches",
                compliance_phase["details"]["failed_artifact_checks"],
            )


def _review_phases(
    *,
    output_dir: Path,
    source_set_id: str,
    review_id: str,
    review_dir: Path,
    compliance_validation: dict | None = None,
    compliance_review: dict | None = None,
    compliance_matrix: dict | None = None,
    compliance_matrix_pdf_path: Path | None = None,
) -> list[dict]:
    return build_review_scoped_phases(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=review_id,
        review_dir=review_dir,
        authority_universe_path=None,
        package_fact_graph_path=None,
        package_fact_graph_validation_path=None,
        applicability_retrieval_trace_path=None,
        applicability_graph_trace_path=None,
        applicability_trace_diagnostics_path=None,
        applicability_decisions_path=None,
        applicable_authorities_path=None,
        non_applicable_authorities_path=None,
        search_coverage_certificates_path=None,
        applicability_validation_path=None,
        generated_rule_pack_path=None,
        generated_rule_pack_validation_path=None,
        review_knowledge_graph_validation=None,
        review_knowledge_graph_validation_path=None,
        review_knowledge_graph_summary=None,
        review_knowledge_graph_summary_path=None,
        compliance_validation=compliance_validation,
        compliance_validation_path=review_dir / "compliance_validation.json",
        compliance_review=compliance_review,
        compliance_review_path=review_dir / "compliance_review.json",
        compliance_matrix=compliance_matrix,
        compliance_matrix_path=review_dir / "compliance_matrix.json",
        compliance_matrix_pdf_path=compliance_matrix_pdf_path,
        component_adjudication_eval=None,
        component_adjudication_eval_path=None,
        component_eval=None,
        component_eval_path=None,
        component_queue=None,
        component_queue_path=None,
        component_adjudication_file_path=None,
        compliance_coverage=None,
        compliance_coverage_path=review_dir / "compliance_coverage.json",
        compliance_gold_eval=None,
        compliance_gold_eval_path=review_dir / "compliance_gold_eval.json",
        rule_claim_summary=None,
        decision_support_dir=None,
        draft_generation_dir=None,
        review_packet_index_dir=None,
        final_qa_dir=None,
    )
