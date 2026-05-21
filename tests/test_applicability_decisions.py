from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_decision_evidence import term_in_text
from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.evidence_strength import classify_evidence_strength

from tests.support.applicability_decision_fixtures import (
    _positive_negative_conflict_candidate,
)
from tests.support.applicability_decision_fixtures import (
    _roads_access_arbitration_candidate,
)
from tests.support.applicability_decision_fixtures import _write_decision_fixture
from tests.support.applicability_decision_support import _read_jsonl
from tests.support.applicability_decision_support import _write_json
from tests.support.applicability_decision_support import _write_jsonl


class ApplicabilityDecisionTests(unittest.TestCase):
    def test_short_acronym_trigger_requires_token_boundary(self) -> None:
        self.assertFalse(
            term_in_text(
                "CE",
                "The Forest Service combined the NEPA scoping and public comment periods.",
            )
        )
        self.assertTrue(term_in_text("CE", "The agency adopted a CE for this action."))

    def test_evidence_strength_classifies_uncertainty_contexts(self) -> None:
        conditional_text = "Trail construction may occur if needed for final design."
        conditional = classify_evidence_strength(
            text=conditional_text,
            start=conditional_text.index("Trail construction"),
            end=conditional_text.index("Trail construction") + len("Trail construction"),
            matched_text="Trail construction",
            section_family="alternatives",
        )
        self.assertEqual(conditional["confidence_class"], "weak_signal")
        self.assertEqual(conditional["strength_class"], "conditional")
        self.assertEqual(conditional["matched_phrase"], "if needed")
        self.assertIn("Trail construction", conditional["evidence_window"])

        speculative_text = "The parcel scope potentially includes reserved access."
        speculative = classify_evidence_strength(
            text=speculative_text,
            start=speculative_text.index("parcel"),
            end=speculative_text.index("parcel") + len("parcel"),
            matched_text="parcel",
        )
        self.assertEqual(speculative["confidence_class"], "weak_signal")
        self.assertEqual(speculative["strength_class"], "speculative")
        self.assertEqual(speculative["matched_phrase"], "potentially")

        resource_effects_text = (
            "Resource effects from grazing may be possible in the cumulative effects area."
        )
        resource_effects = classify_evidence_strength(
            text=resource_effects_text,
            start=resource_effects_text.index("grazing"),
            end=resource_effects_text.index("grazing") + len("grazing"),
            matched_text="grazing",
            section_family="cumulative_effects",
        )
        self.assertEqual(resource_effects["confidence_class"], "weak_signal")
        self.assertEqual(resource_effects["strength_class"], "speculative")
        self.assertEqual(resource_effects["matched_phrase"], "may be possible")

        no_action_text = (
            "Under the No Action Alternative, trail construction would not occur and "
            "access would not change."
        )
        no_action = classify_evidence_strength(
            text=no_action_text,
            start=no_action_text.index("trail construction"),
            end=no_action_text.index("trail construction") + len("trail construction"),
            matched_text="trail construction",
            section_family="no_action",
        )
        self.assertEqual(no_action["confidence_class"], "weak_signal")
        self.assertEqual(no_action["strength_class"], "background")
        self.assertEqual(no_action["matched_phrase"], "no action alternative")

        no_change_text = "Trail construction would not occur under the current proposal."
        no_change = classify_evidence_strength(
            text=no_change_text,
            start=no_change_text.index("Trail construction"),
            end=no_change_text.index("Trail construction") + len("Trail construction"),
            matched_text="Trail construction",
        )
        self.assertEqual(no_change["confidence_class"], "weak_signal")
        self.assertEqual(no_change["strength_class"], "background")
        self.assertEqual(no_change["matched_phrase"], "would not occur")

        does_not_include_text = "The project does not include trail construction."
        does_not_include = classify_evidence_strength(
            text=does_not_include_text,
            start=does_not_include_text.index("trail construction"),
            end=does_not_include_text.index("trail construction")
            + len("trail construction"),
            matched_text="trail construction",
        )
        self.assertEqual(does_not_include["confidence_class"], "weak_signal")
        self.assertEqual(does_not_include["strength_class"], "background")
        self.assertEqual(does_not_include["matched_phrase"], "does not include")

        negated_trigger_text = "The record states no road changes and no right-of-way."
        negated_trigger = classify_evidence_strength(
            text=negated_trigger_text,
            start=negated_trigger_text.index("road"),
            end=negated_trigger_text.index("road") + len("road"),
            matched_text="road",
        )
        self.assertEqual(negated_trigger["confidence_class"], "weak_signal")
        self.assertEqual(negated_trigger["strength_class"], "background")
        self.assertEqual(negated_trigger["reason"], "negated_matched_trigger")
        self.assertEqual(negated_trigger["matched_phrase"], "no road")

        not_a_land_exchange_text = "The proposal is not a land exchange."
        not_a_land_exchange = classify_evidence_strength(
            text=not_a_land_exchange_text,
            start=not_a_land_exchange_text.index("land exchange"),
            end=not_a_land_exchange_text.index("land exchange") + len("land exchange"),
            matched_text="land exchange",
        )
        self.assertEqual(not_a_land_exchange["confidence_class"], "weak_signal")
        self.assertEqual(not_a_land_exchange["strength_class"], "background")
        self.assertEqual(not_a_land_exchange["matched_phrase"], "not a land exchange")

        plural_negated_trigger_text = "The analysis finds no cultural resources."
        plural_negated_trigger = classify_evidence_strength(
            text=plural_negated_trigger_text,
            start=plural_negated_trigger_text.index("cultural resources"),
            end=plural_negated_trigger_text.index("cultural resources")
            + len("cultural resources"),
            matched_text="cultural resource",
        )
        self.assertEqual(plural_negated_trigger["confidence_class"], "weak_signal")
        self.assertEqual(plural_negated_trigger["strength_class"], "background")
        self.assertEqual(
            plural_negated_trigger["matched_phrase"],
            "no cultural resources",
        )

        decisive_text = "The Proposed Action reserves Right-of-Way for Big Timber Creek Road No. 197."
        decisive = classify_evidence_strength(
            text=decisive_text,
            start=decisive_text.index("Right-of-Way"),
            end=decisive_text.index("Right-of-Way") + len("Right-of-Way"),
            matched_text="Right-of-Way",
            section_family="alternatives",
        )
        self.assertEqual(decisive["confidence_class"], "observed")
        self.assertEqual(decisive["strength_class"], "observed")

    def test_writes_first_class_applicability_decision_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))

            result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertFalse(result.summary["generated_rule_pack_ready"])
            self.assertTrue(result.decisions_path.exists())
            self.assertTrue(result.applicable_authorities_path.exists())
            self.assertTrue(result.non_applicable_authorities_path.exists())
            self.assertTrue(result.search_coverage_certificates_path.exists())
            self.assertTrue(result.provenance_path.exists())
            self.assertTrue(result.report_path.exists())
            self.assertFalse((result.applicability_dir / "generated_rule_pack.json").exists())
            self.assertFalse((result.applicability_dir / "compliance_matrix.json").exists())

            decisions = {
                row["candidate_authority_id"]: row for row in _read_jsonl(result.decisions_path)
            }
            self.assertEqual(len(decisions), 6)
            self.assertEqual(
                decisions["rule-template:unit-pack:0.1.0:baseline_nepa"]["status"],
                "applicable",
            )
            self.assertEqual(
                decisions["rule-template:unit-pack:0.1.0:esa_consultation"]["status"],
                "applicable",
            )
            ce_decision = decisions["rule-template:unit-pack:0.1.0:ce_fanec"]
            self.assertEqual(ce_decision["status"], "not_applicable")
            self.assertEqual(ce_decision["basis_type"], "absent_trigger_evidence")
            self.assertTrue(ce_decision["search_coverage_certificate_ids"])
            self.assertTrue(ce_decision["explicit_trigger_miss_evidence"])
            self.assertTrue(ce_decision["source_library_evidence_spans"])

            sioux_decision = decisions["rule-template:unit-pack:0.1.0:sioux_geography"]
            self.assertEqual(sioux_decision["status"], "not_applicable")
            self.assertEqual(sioux_decision["basis_type"], "negative_package_evidence")
            self.assertTrue(sioux_decision["negative_evidence_spans"])
            self.assertTrue(
                any(
                    span["evidence_strength"]["strength_class"] == "negative_context"
                    for span in sioux_decision["negative_evidence_spans"]
                )
            )
            self.assertTrue(
                any(
                    span["evidence_strength"].get("matched_phrase")
                    == "not part of the project area"
                    for span in sioux_decision["negative_evidence_spans"]
                    if span["evidence_strength"]["strength_class"] == "negative_context"
                )
            )

            weak_decision = decisions["rule-template:unit-pack:0.1.0:cwa_permit"]
            self.assertEqual(weak_decision["status"], "needs_adjudication")
            self.assertEqual(weak_decision["basis_type"], "unresolved_evidence_conflict")
            self.assertTrue(weak_decision["contradiction_notes"])
            weak_arbitration = weak_decision["arbitration_summary"]
            self.assertEqual(
                weak_arbitration["schema_version"],
                "applicability-evidence-arbitration-v0",
            )
            self.assertFalse(weak_arbitration["diagnostic_only"])
            self.assertEqual(weak_decision["arbitration_status"], "weak_positive_only")
            self.assertEqual(weak_decision["decisive_trigger_groups"], [])
            self.assertTrue(weak_decision["weak_only_trigger_groups"])
            self.assertEqual(
                weak_arbitration["decision_effect"],
                "blocked_by_weak_positive_trigger",
            )
            self.assertTrue(weak_arbitration["positive_trigger_groups"])

            component_id = "forest-plan-component:unit-inventory:STD-FP-01"
            self.assertEqual(decisions[component_id]["status"], "applicable")
            self.assertEqual(decisions[component_id]["basis_type"], "forest_plan_component")
            self.assertTrue(decisions[component_id]["source_library_evidence_spans"])

            applicable = json.loads(
                result.applicable_authorities_path.read_text(encoding="utf-8")
            )
            non_applicable = json.loads(
                result.non_applicable_authorities_path.read_text(encoding="utf-8")
            )
            coverage = json.loads(
                result.search_coverage_certificates_path.read_text(encoding="utf-8")
            )
            self.assertEqual(applicable["schema_version"], "applicable-authorities-v0")
            self.assertEqual(non_applicable["schema_version"], "non-applicable-authorities-v0")
            self.assertEqual(applicable["applicable_authority_count"], 3)
            self.assertEqual(non_applicable["non_applicable_authority_count"], 2)
            self.assertEqual(
                {row["candidate_authority_id"] for row in non_applicable["authorities"]},
                {
                    "rule-template:unit-pack:0.1.0:ce_fanec",
                    "rule-template:unit-pack:0.1.0:sioux_geography",
                },
            )
            ce_certificates = [
                cert
                for cert in coverage["certificates"]
                if cert["covered_candidate_authority_ids"]
                == ["rule-template:unit-pack:0.1.0:ce_fanec"]
            ]
            self.assertEqual(len(ce_certificates), 1)
            self.assertEqual(ce_certificates[0]["coverage_result"], "sufficient")
            self.assertIn("package_section", ce_certificates[0]["executed_query_variants"])
            self.assertTrue(ce_certificates[0]["searched_artifact_hashes"])
            provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
            entity_ids = {entity["entity_id"] for entity in provenance["entities"]}
            self.assertIn("package_manifest", entity_ids)
            self.assertIn("package_chunks", entity_ids)
            self.assertIn("decision_ledger", entity_ids)

            report_text = result.report_path.read_text(encoding="utf-8")
            self.assertIn("Arbitration: `blocked_by_weak_positive_trigger`", report_text)

    def test_trigger_arbitration_accepts_strong_triggers_with_weak_auxiliary_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_set_id = "source-set-unit"
            fixture = _write_decision_fixture(
                Path(tmp),
                extra_candidates=[_roads_access_arbitration_candidate(source_set_id)],
            )

            result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            decisions = {
                row["candidate_authority_id"]: row for row in _read_jsonl(result.decisions_path)
            }
            decision = decisions["rule-template:unit-pack:0.1.0:roads_access_arbitration"]
            self.assertEqual(decision["status"], "applicable")
            self.assertEqual(decision["basis_type"], "positive_package_trigger")
            self.assertEqual(
                decision["arbitration_status"],
                "strong_positive_with_weak_auxiliary",
            )
            self.assertEqual(
                {tuple(group) for group in decision["decisive_trigger_groups"]},
                {("road",), ("right-of-way",)},
            )
            self.assertEqual(
                {tuple(group) for group in decision["weak_auxiliary_trigger_groups"]},
                {("trail",), ("grazing",)},
            )
            self.assertTrue(decision["reviewer_notes"])
            arbitration = decision["arbitration_summary"]
            self.assertEqual(
                arbitration["decision_effect"],
                "positive_trigger_decisive_with_weak_auxiliary",
            )
            self.assertFalse(arbitration["requires_adjudication"])
            groups = {
                tuple(group["trigger_group"]): group
                for group in arbitration["positive_trigger_groups"]
            }
            self.assertEqual(groups[("road",)]["diagnostic_treatment"], "decisive")
            self.assertEqual(
                groups[("right-of-way",)]["diagnostic_treatment"],
                "decisive",
            )
            self.assertEqual(groups[("trail",)]["diagnostic_treatment"], "weak_only")
            self.assertEqual(groups[("grazing",)]["diagnostic_treatment"], "weak_only")
            self.assertGreater(groups[("road",)]["evidence_strength_counts"]["observed"], 0)
            self.assertNotIn("weak_signal", groups[("road",)]["evidence_strength_counts"])
            self.assertIn(
                "observed",
                groups[("road",)]["evidence_strength_class_counts"],
            )
            self.assertIn("weak_signal", groups[("trail",)]["evidence_strength_counts"])
            self.assertIn(
                "conditional",
                groups[("trail",)]["evidence_strength_class_counts"],
            )
            self.assertIn(
                "speculative",
                groups[("grazing",)]["evidence_strength_class_counts"],
            )
            self.assertTrue(groups[("trail",)]["weak_signal_reasons"])
            self.assertTrue(groups[("grazing",)]["weak_signal_reasons"])
            self.assertTrue(
                any("matched `" in note for note in groups[("trail",)]["weak_signal_reasons"])
            )
            self.assertTrue(
                any("may be possible" in note for note in groups[("grazing",)]["weak_signal_reasons"])
            )
            trail_details = groups[("trail",)]["weak_signal_details"]
            self.assertTrue(
                {
                    detail["matched_phrase"]
                    for detail in trail_details
                    if detail.get("matched_phrase")
                }
                & {"could be required", "if needed"}
            )
            self.assertTrue(
                any("Trail easements" in detail["evidence_window"] for detail in trail_details)
            )
            grazing_details = groups[("grazing",)]["weak_signal_details"]
            self.assertTrue(
                any(
                    detail.get("matched_phrase") == "may be possible"
                    for detail in grazing_details
                )
            )
            self.assertTrue(arbitration["source_evidence_ids"])
            self.assertTrue(arbitration["selected_retrieval_result_ids"])

            report_text = result.report_path.read_text(encoding="utf-8")
            self.assertIn(
                "`rule-template:unit-pack:0.1.0:roads_access_arbitration`: "
                "`applicable` / `positive_package_trigger`",
                report_text,
            )
            self.assertIn("Positive trigger diagnostics:", report_text)
            self.assertIn(
                "Arbitration: `positive_trigger_decisive_with_weak_auxiliary`",
                report_text,
            )
            self.assertIn("`trail`: `weak_only`", report_text)

    def test_trigger_arbitration_keeps_positive_negative_conflict_adjudicated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_set_id = "source-set-unit"
            fixture = _write_decision_fixture(
                Path(tmp),
                extra_candidates=[_positive_negative_conflict_candidate(source_set_id)],
            )

            result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            decisions = {
                row["candidate_authority_id"]: row for row in _read_jsonl(result.decisions_path)
            }
            decision = decisions["rule-template:unit-pack:0.1.0:positive_negative_conflict"]
            self.assertEqual(decision["status"], "needs_adjudication")
            self.assertEqual(decision["basis_type"], "unresolved_evidence_conflict")
            self.assertEqual(decision["arbitration_status"], "positive_negative_conflict")
            self.assertEqual(decision["decisive_trigger_groups"], [["road"]])
            self.assertTrue(decision["negative_evidence_spans"])
            self.assertIn(
                "Strong positive trigger evidence and explicit negative",
                decision["arbitration_rationale"],
            )
            self.assertEqual(
                decision["arbitration_summary"]["decision_effect"],
                "blocked_by_positive_negative_conflict",
            )

    def test_uses_declared_source_evidence_when_source_retrieval_has_no_selected_hits(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            retrieval_trace_path = applicability_dir / "applicability_retrieval_trace.jsonl"
            rows = _read_jsonl(retrieval_trace_path)
            for row in rows:
                row["ranked_results"] = [
                    result
                    for result in row.get("ranked_results", [])
                    if result.get("result_kind") != "source_chunk"
                ]
            _write_jsonl(retrieval_trace_path, rows)

            result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            decisions = {
                row["candidate_authority_id"]: row for row in _read_jsonl(result.decisions_path)
            }
            baseline = decisions["rule-template:unit-pack:0.1.0:baseline_nepa"]
            self.assertTrue(baseline["source_library_evidence_spans"])
            self.assertEqual(
                baseline["source_library_evidence_spans"][0]["evidence_origin"],
                "authority_universe",
            )
            component = decisions["forest-plan-component:unit-inventory:STD-FP-01"]
            self.assertTrue(component["source_library_evidence_spans"])

    def test_forest_plan_negative_scope_evidence_overrides_component_positive(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            authority_universe_path = (
                fixture["output_dir"]
                / "reviews"
                / fixture["review_id"]
                / "applicability"
                / "authority_universe_snapshot.json"
            )
            authority_universe = json.loads(
                authority_universe_path.read_text(encoding="utf-8")
            )
            for candidate in authority_universe["candidate_authorities"]:
                if (
                    candidate["candidate_authority_id"]
                    == "forest-plan-component:unit-inventory:STD-FP-01"
                ):
                    candidate["negative_trigger_groups"] = [["not part of the project area"]]
            _write_json(authority_universe_path, authority_universe)

            result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            decisions = {
                row["candidate_authority_id"]: row for row in _read_jsonl(result.decisions_path)
            }
            component = decisions["forest-plan-component:unit-inventory:STD-FP-01"]
            self.assertEqual(component["status"], "not_applicable")
            self.assertEqual(component["basis_type"], "negative_package_evidence")
            self.assertFalse(component["package_evidence_spans"])
            self.assertTrue(component["negative_evidence_spans"])

    def test_cli_writes_decision_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))

            exit_code = main(
                [
                    "applicability-determine",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                ]
            )

            self.assertEqual(exit_code, 0)
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            self.assertTrue((applicability_dir / "applicability_decisions.jsonl").exists())
            self.assertTrue((applicability_dir / "applicable_authorities.json").exists())
            self.assertTrue((applicability_dir / "non_applicable_authorities.json").exists())
            self.assertTrue((applicability_dir / "search_coverage_certificates.json").exists())
            self.assertTrue((applicability_dir / "applicability_provenance.json").exists())
            self.assertTrue((applicability_dir / "applicability_report.md").exists())
