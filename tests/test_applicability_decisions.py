from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.applicability_decisions import _term_in_text
from usfs_r1_ea_sources.applicability_retrieval import build_applicability_retrieval_traces
from usfs_r1_ea_sources.applicability_rule_pack import generate_applicability_rule_pack
from usfs_r1_ea_sources.applicability_rule_pack import validate_generated_rule_pack
from usfs_r1_ea_sources.applicability_validation import apply_applicability_adjudication
from usfs_r1_ea_sources.applicability_validation import evaluate_applicability_adjudication
from usfs_r1_ea_sources.applicability_validation import validate_applicability_run
from usfs_r1_ea_sources.applicability_validation import (
    write_applicability_adjudication_template,
)
from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.evidence_strength import classify_evidence_strength
from usfs_r1_ea_sources.package_fact_graph import build_package_fact_graph
from usfs_r1_ea_sources.retrieval import _write_sqlite_index


class ApplicabilityDecisionTests(unittest.TestCase):
    def test_short_acronym_trigger_requires_token_boundary(self) -> None:
        self.assertFalse(
            _term_in_text(
                "CE",
                "The Forest Service combined the NEPA scoping and public comment periods.",
            )
        )
        self.assertTrue(_term_in_text("CE", "The agency adopted a CE for this action."))

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

    def test_generated_rule_pack_uses_only_validated_applicable_authorities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)

            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.generated_rule_pack_path.exists())
            self.assertTrue(result.generated_rule_pack_validation_path.exists())
            generated = json.loads(
                result.generated_rule_pack_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                generated["schema_version"],
                "generated-compliance-rule-pack-v0",
            )
            self.assertEqual(generated["applicable_authority_count"], 4)
            self.assertEqual(len(generated["rules"]), 4)
            rule_ids = {rule["id"] for rule in generated["rules"]}
            self.assertEqual(
                rule_ids,
                {
                    "baseline_nepa",
                    "cwa_permit",
                    "esa_consultation",
                    "forest_plan_component_STD-FP-01",
                },
            )
            self.assertNotIn("ce_fanec", rule_ids)
            self.assertNotIn("sioux_geography", rule_ids)
            for rule in generated["rules"]:
                metadata = rule["applicability"]
                self.assertEqual(metadata["status"], "applicable")
                self.assertTrue(metadata["decision_id"])
                self.assertTrue(metadata["retrieval_trace_ids"])
                self.assertTrue(metadata["source_record_ids"])
                self.assertEqual(rule["generated_rule_id"], rule["id"])
                self.assertIn("package_section_expectations", rule)
                self.assertIn("applicability_artifact_hashes", rule)
                for hash_field in {
                    "base_rule_pack_sha256",
                    "applicability_validation_sha256",
                    "authority_universe_sha256",
                    "applicable_authorities_sha256",
                    "non_applicable_authorities_sha256",
                    "package_fact_graph_sha256",
                    "retrieval_trace_sha256",
                    "graph_trace_sha256",
                    "search_coverage_certificates_sha256",
                    "package_manifest_sha256",
                    "package_chunks_sha256",
                    "catalog_sha256",
                    "applicability_provenance_sha256",
                }:
                    self.assertTrue(rule["applicability_artifact_hashes"][hash_field])
                self.assertEqual(
                    metadata["artifact_hashes"],
                    rule["applicability_artifact_hashes"],
                )
                if rule["id"] != "forest_plan_component_STD-FP-01":
                    self.assertTrue(rule["base_rule_id"])
            applicable = json.loads(
                (applicability_dir / "applicable_authorities.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                generated["applicable_authorities_sha256"],
                result.summary["applicable_authorities_sha256"],
            )
            self.assertEqual(
                generated["applicable_authority_count"],
                applicable["applicable_authority_count"],
            )

    def test_generated_rule_pack_can_materialize_applicable_family_template(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_set_id = "source-set-unit"
            fixture = _write_decision_fixture(
                Path(tmp),
                extra_candidates=[_authority_family_candidate(source_set_id)],
            )
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)

            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertTrue(result.summary["passed"])
            generated = json.loads(
                result.generated_rule_pack_path.read_text(encoding="utf-8")
            )
            generated_by_id = {rule["id"]: rule for rule in generated["rules"]}
            family_rule = generated_by_id["clean_water_family_authority_template"]
            self.assertIsNone(family_rule["base_rule_id"])
            self.assertEqual(
                family_rule["applicability"]["candidate_authority_type"],
                "authority_family_rule_template",
            )
            self.assertEqual(
                family_rule["authority_source_record_id"],
                "R1EA-CWA",
            )
            self.assertEqual(family_rule["applies_if_package_terms"], ["wetlands"])
            self.assertFalse(family_rule["source_claim_link_requirements"]["required"])
            self.assertNotIn("ce_fanec", generated_by_id)

    def test_generated_rule_pack_requires_passing_applicability_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            validation_result = validate_applicability_run(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )
            self.assertFalse(validation_result.summary["passed"])

            with self.assertRaisesRegex(ValueError, "has not passed"):
                generate_applicability_rule_pack(
                    output_dir=fixture["output_dir"],
                    review_id=fixture["review_id"],
                    source_set_id=fixture["source_set_id"],
                    base_rule_pack_path=_write_generated_rule_base_pack(Path(tmp)),
                )

            generated_path = (
                fixture["output_dir"]
                / "reviews"
                / fixture["review_id"]
                / "applicability"
                / "generated_rule_pack.json"
            )
            self.assertFalse(generated_path.exists())

    def test_generated_rule_pack_refuses_stale_applicability_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)
            applicable_path = (
                fixture["output_dir"]
                / "reviews"
                / fixture["review_id"]
                / "applicability"
                / "applicable_authorities.json"
            )
            applicable = json.loads(applicable_path.read_text(encoding="utf-8"))
            applicable["authorities"][0]["basis_type"] = "changed-after-validation"
            _write_json(applicable_path, applicable)

            with self.assertRaisesRegex(ValueError, "stale"):
                generate_applicability_rule_pack(
                    output_dir=fixture["output_dir"],
                    review_id=fixture["review_id"],
                    source_set_id=fixture["source_set_id"],
                    base_rule_pack_path=_write_generated_rule_base_pack(Path(tmp)),
                )

            generated_path = applicable_path.parent / "generated_rule_pack.json"
            self.assertFalse(generated_path.exists())

    def test_generated_rule_pack_refuses_stale_package_context_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            context_path = applicability_dir / "package_applicability_context.json"
            context = json.loads(context_path.read_text(encoding="utf-8"))
            context["package_manifest_sha256"] = "changed-after-validation"
            _write_json(context_path, context)

            with self.assertRaisesRegex(ValueError, "stale"):
                generate_applicability_rule_pack(
                    output_dir=fixture["output_dir"],
                    review_id=fixture["review_id"],
                    source_set_id=fixture["source_set_id"],
                    base_rule_pack_path=_write_generated_rule_base_pack(Path(tmp)),
                )

            generated_path = applicability_dir / "generated_rule_pack.json"
            self.assertFalse(generated_path.exists())

    def test_generated_rule_pack_validation_rejects_manual_edit_and_stale_inputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            applicability_dir = _build_adjudicated_applicability_dir(fixture)
            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )
            generated = json.loads(
                result.generated_rule_pack_path.read_text(encoding="utf-8")
            )
            generated["rules"][0]["title"] = "Manual edit should fail validation"
            _write_json(result.generated_rule_pack_path, generated)

            edited_validation = validate_generated_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertFalse(edited_validation.summary["passed"])
            self.assertIn(
                "generated_rule_pack_mismatch",
                edited_validation.summary["failure_category_counts"],
            )

            # Regenerate to refresh the expected generated-pack hash, then stale an input.
            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )
            applicable_path = applicability_dir / "applicable_authorities.json"
            applicable = json.loads(applicable_path.read_text(encoding="utf-8"))
            applicable["authorities"][0]["basis_type"] = "stale-after-generation"
            _write_json(applicable_path, applicable)

            stale_validation = validate_generated_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertFalse(stale_validation.summary["passed"])
            self.assertIn(
                "generated_rule_pack_stale",
                stale_validation.summary["failure_category_counts"],
            )

    def test_generated_rule_pack_validate_only_requires_recorded_generated_hash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)
            result = generate_applicability_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )
            result.generated_rule_pack_validation_path.unlink()

            validation = validate_generated_rule_pack(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                base_rule_pack_path=base_rule_pack_path,
            )

            self.assertFalse(validation.summary["passed"])
            self.assertIn(
                "generated_rule_pack_mismatch",
                validation.summary["failure_category_counts"],
            )

    def test_cli_writes_generated_rule_pack_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))
            _build_adjudicated_applicability_dir(fixture)
            base_rule_pack_path = _write_generated_rule_base_pack(Path(tmp))

            exit_code = main(
                [
                    "applicability-generate-rule-pack",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                    "--base-rule-pack",
                    str(base_rule_pack_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            self.assertTrue((applicability_dir / "generated_rule_pack.json").exists())
            self.assertTrue(
                (applicability_dir / "generated_rule_pack_validation.json").exists()
            )

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


def _build_adjudicated_applicability_dir(fixture: dict) -> Path:
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
    item["final_status"] = "applicable"
    item["disposition"] = "human_applicable"
    item["adjudicated_at"] = "2026-05-04T00:00:00Z"
    item["adjudicated_by"] = ["unit-reviewer"]
    item["source_type"] = "test-adjudication"
    item["rationale"] = "The weak Clean Water Act signal is applicable for replay."
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
    if not eval_result.summary["passed"]:
        raise AssertionError(eval_result.summary)
    apply_result = apply_applicability_adjudication(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
        adjudication_file=template_result.output_path,
    )
    if not apply_result.summary["passed"]:
        raise AssertionError(apply_result.summary)
    validation_result = validate_applicability_run(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
    )
    if not validation_result.summary["passed"]:
        raise AssertionError(validation_result.summary)
    return fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"


def _write_generated_rule_base_pack(root: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-pack",
        "version": "0.1.0",
        "title": "Unit Applicability Rule Pack",
        "domain": "Unit NEPA",
        "jurisdiction": "Unit Test",
        "rules": [
            _generated_base_rule(
                rule_id="baseline_nepa",
                source_record_id="R1EA-BASE",
                document_role="law",
                authority_category="law",
                applicability_mode="baseline",
            ),
            _generated_base_rule(
                rule_id="esa_consultation",
                source_record_id="R1EA-ESA",
                document_role="law",
                authority_category="law",
                applicability_mode="conditional",
                applies_if_package_terms=["Endangered Species Act"],
            ),
            _generated_base_rule(
                rule_id="ce_fanec",
                source_record_id="R1EA-CE",
                document_role="regulation",
                authority_category="regulation",
                applicability_mode="conditional",
                applies_if_package_terms=["Categorical Exclusion"],
            ),
            _generated_base_rule(
                rule_id="cwa_permit",
                source_record_id="R1EA-CWA",
                document_role="law",
                authority_category="law",
                applicability_mode="conditional",
                applies_if_package_terms=["Clean Water Act"],
            ),
            _generated_base_rule(
                rule_id="sioux_geography",
                source_record_id="R1EA-SIOUX",
                document_role="forest_plan",
                authority_category="forest_plan",
                applicability_mode="conditional",
                applies_if_package_terms=["Sioux Geographic Area"],
            ),
        ],
    }
    path = root / "generated-base-rule-pack.json"
    _write_json(path, rule_pack)
    return path


def _generated_base_rule(
    *,
    rule_id: str,
    source_record_id: str,
    document_role: str,
    authority_category: str,
    applicability_mode: str,
    applies_if_package_terms: list[str] | None = None,
) -> dict:
    package_terms = applies_if_package_terms or [rule_id.replace("_", " ")]
    rule = {
        "id": rule_id,
        "title": f"{rule_id} title",
        "authority_category": authority_category,
        "authority_source_record_id": source_record_id,
        "applicability_mode": applicability_mode,
        "question": f"Does the package address {rule_id}?",
        "requirement": f"The package should address {rule_id}.",
        "severity": "medium",
        "package_query": " ".join(package_terms),
        "package_terms": package_terms,
        "source_query": f"{rule_id} source authority",
        "source_filters": {
            "document_role": document_role,
            "source_record_id": source_record_id,
        },
        "evidence_expectation": "Requires source and package evidence.",
    }
    if applicability_mode == "conditional":
        rule["applies_if_package_terms"] = package_terms
    return rule


def _write_decision_fixture(
    root: Path,
    extra_candidates: list[dict] | None = None,
) -> dict:
    output_dir = root / "source_library"
    review_id = "east-crazy-applicability"
    source_set_id = "source-set-unit"
    _write_package_cache(output_dir, review_id)
    build_package_fact_graph(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    retrieval_index_path = (
        output_dir / "derived" / source_set_id / "retrieval" / "evidence_index.sqlite"
    )
    retrieval_index_path.parent.mkdir(parents=True, exist_ok=True)
    chunks = _source_chunks(source_set_id)
    chunks_path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    _write_jsonl(chunks_path, chunks)
    _write_sqlite_index(
        retrieval_index_path,
        source_set_id=source_set_id,
        chunks=chunks,
        chunks_path=chunks_path,
        catalog_sqlite_path=output_dir / "catalog" / "review_sources.sqlite",
    )
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    authority_universe = {
        "schema_version": "authority-universe-snapshot-v0",
        "created_at": "2026-05-04T00:00:00Z",
        "authority_universe_id": "authority-universe:unit",
        "authority_universe_sha256": "authority-universe-sha",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "catalog_sha256": "catalog-sha",
        "artifact_paths": {},
        "candidate_authorities": [
            *_candidate_authorities(source_set_id),
            *(extra_candidates or []),
        ],
        "validation": {"passed": True, "checks": []},
    }
    _write_json(applicability_dir / "authority_universe_snapshot.json", authority_universe)
    build_applicability_retrieval_traces(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        retrieval_index_path=retrieval_index_path,
        top_k=3,
        max_graph_paths_per_candidate=20,
    )
    return {
        "output_dir": output_dir,
        "review_id": review_id,
        "source_set_id": source_set_id,
    }


def _candidate_authorities(source_set_id: str) -> list[dict]:
    return [
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="baseline_nepa",
            source_record_id="R1EA-BASE",
            authority_category="law",
            applicability_mode="baseline",
            source_query="NEPA environmental assessment baseline authority",
            package_query="environmental assessment",
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="esa_consultation",
            source_record_id="R1EA-ESA",
            authority_category="law",
            applicability_mode="conditional",
            source_query="Endangered Species Act consultation",
            package_query="Endangered Species Act",
            positive_trigger_groups=[["Endangered Species Act"]],
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="ce_fanec",
            source_record_id="R1EA-CE",
            authority_category="regulation",
            applicability_mode="conditional",
            source_query="categorical exclusion FANEC",
            package_query="Categorical Exclusion",
            positive_trigger_groups=[["Categorical Exclusion"]],
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="cwa_permit",
            source_record_id="R1EA-CWA",
            authority_category="law",
            applicability_mode="conditional",
            source_query="Clean Water Act permit",
            package_query="Clean Water Act",
            positive_trigger_groups=[["Clean Water Act"]],
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="sioux_geography",
            source_record_id="R1EA-SIOUX",
            authority_category="forest_plan",
            applicability_mode="conditional",
            source_query="Sioux Geographic Area forest plan direction",
            package_query="Sioux Geographic Area",
            positive_trigger_groups=[["Sioux Geographic Area"]],
            negative_trigger_groups=[["Sioux Geographic Area"]],
        ),
        _forest_plan_candidate(source_set_id),
    ]


def _authority_family_candidate(source_set_id: str) -> dict:
    candidate = _rule_candidate(
        source_set_id=source_set_id,
        rule_id="clean_water_family_authority_template",
        source_record_id="R1EA-CWA",
        authority_category="law",
        applicability_mode="conditional",
        source_query="Clean Water Act source authority",
        package_query="wetlands",
        positive_trigger_groups=[["wetlands"]],
    )
    candidate["candidate_authority_id"] = (
        "authority-family-template:unit-authority-families:0.1.0:"
        "clean_water:clean_water_family_authority_template"
    )
    candidate["candidate_authority_type"] = "authority_family_rule_template"
    candidate["authority_family_id"] = "clean_water"
    candidate["package_section_filters"]["package_section_terms"] = ["water resources"]
    candidate["rule_template"].update(
        {
            "authority_family_template_set_id": "unit-authority-families",
            "authority_family_template_set_version": "0.1.0",
            "template_id": "clean_water_template",
            "authority_family_id": "clean_water",
            "authority_source_record_id": "R1EA-CWA",
            "authority_category": "law",
            "package_query": "wetlands",
            "package_terms": ["wetlands"],
            "package_section_terms": ["water resources"],
            "applies_if_package_terms": ["wetlands"],
            "applies_if_package_term_groups": [["wetlands"]],
            "does_not_apply_if_package_terms": ["no wetlands"],
            "source_query": "Clean Water Act source authority",
            "source_filters": {
                "document_role": "law",
                "source_record_id": "R1EA-CWA",
            },
            "evidence_expectation": "Requires source and package evidence.",
        }
    )
    candidate["required_source_evidence"]["requires_source_claim_linkage"] = False
    candidate["source_claim_link_ids"] = []
    return candidate


def _roads_access_arbitration_candidate(source_set_id: str) -> dict:
    candidate = _rule_candidate(
        source_set_id=source_set_id,
        rule_id="roads_access_arbitration",
        source_record_id="R1EA-ROAD",
        authority_category="regulation",
        applicability_mode="conditional",
        source_query="National Forest roads access right-of-way special use authority",
        package_query="road trail right-of-way grazing",
        positive_trigger_groups=[
            ["road"],
            ["trail"],
            ["right-of-way"],
            ["grazing"],
        ],
    )
    candidate["trigger_arbitration_contract"] = {
        "required_trigger_groups": [["road"], ["right-of-way"]],
        "minimum_strong_trigger_groups": 2,
        "positive_negative_conflict_policy": "needs_adjudication",
    }
    candidate["rule_template"].update(
        {
            "title": "Roads and access arbitration fixture",
            "question": "Does the package trigger roads/access authorities?",
            "requirement": "Apply roads/access authority when triggered.",
        }
    )
    return candidate


def _positive_negative_conflict_candidate(source_set_id: str) -> dict:
    candidate = _rule_candidate(
        source_set_id=source_set_id,
        rule_id="positive_negative_conflict",
        source_record_id="R1EA-ROAD",
        authority_category="regulation",
        applicability_mode="conditional",
        source_query="National Forest roads access right-of-way special use authority",
        package_query="road not part of the project area",
        positive_trigger_groups=[["road"]],
        negative_trigger_groups=[["not part of the project area"]],
    )
    candidate["rule_template"].update(
        {
            "title": "Positive negative arbitration fixture",
            "question": "Does the package contain conflicting road scope evidence?",
            "requirement": "Conflict should require adjudication.",
        }
    )
    return candidate


def _rule_candidate(
    *,
    source_set_id: str,
    rule_id: str,
    source_record_id: str,
    authority_category: str,
    applicability_mode: str,
    source_query: str,
    package_query: str,
    positive_trigger_groups: list[list[str]] | None = None,
    negative_trigger_groups: list[list[str]] | None = None,
) -> dict:
    candidate_id = f"rule-template:unit-pack:0.1.0:{rule_id}"
    return {
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": "rule_template",
        "source_set_id": source_set_id,
        "authority_category": authority_category,
        "authority_document_role": authority_category,
        "source_record_ids": [source_record_id],
        "source_records": [
            {
                "source_record_id": source_record_id,
                "title": f"{rule_id} authority",
                "citation_label": f"{source_record_id} | {rule_id} authority",
            }
        ],
        "required_package_fact_types": ["action", "nepa_level", "resource_topic"],
        "positive_trigger_groups": positive_trigger_groups or [],
        "negative_trigger_groups": negative_trigger_groups or [],
        "source_role_filters": {
            "source_record_ids": [source_record_id],
            "document_roles": [authority_category],
            "authority_categories": [authority_category],
        },
        "package_section_filters": {
            "package_query": package_query,
            "package_terms": [package_query],
            "package_section_terms": [],
            "preferred_section_families": [],
        },
        "required_source_evidence": {"requires_source_record": True},
        "retrieval_contract": {
            "contract_type": "rule_template_retrieval",
            "query_plan_id": f"retrieval-plan:{rule_id}",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "source_queries": [source_query],
            "package_queries": [package_query],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "rule_template_graph_expansion",
            "start_node_types": ["rule_template", "source_record", "authority"],
            "relationship_types": [
                "source_record",
                "authority_category",
                "source_claim",
                "rule_claim_link",
                "package_fact",
                "evidence_span",
                "exception",
                "dependency",
                "supersession",
            ],
            "max_depth": 2,
            "requires_path_trace": True,
        },
        "dependency_contract": {
            "dependency_rule_ids": [],
            "exception_rule_ids": [],
            "supersedes_rule_ids": [],
        },
        "search_coverage_requirements": [
            {
                "coverage_class": "positive_trigger_miss",
                "required_query_types": [
                    "exact_keyword",
                    "bm25",
                    "metadata_filter",
                    "package_section",
                ],
                "required_artifacts": [
                    "package_fact_graph",
                    "applicability_retrieval_trace",
                    "search_coverage_certificates",
                ],
            }
        ],
        "rule_template": {
            "base_rule_pack_id": "unit-pack",
            "base_rule_pack_version": "0.1.0",
            "rule_id": rule_id,
            "title": f"{rule_id} authority",
            "question": f"Does {rule_id} apply?",
            "requirement": f"Apply {rule_id} when triggered.",
            "severity": "medium",
            "applicability_mode": applicability_mode,
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_claim_link_count": 1,
            "rule_claim_gap_count": 0,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "rule_template",
            "applicability_mode": applicability_mode,
            "baseline_required": applicability_mode == "baseline",
            "positive_package_term_groups": positive_trigger_groups or [],
            "negative_package_terms": [term for group in negative_trigger_groups or [] for term in group],
        },
    }


def _forest_plan_candidate(source_set_id: str) -> dict:
    return {
        "candidate_authority_id": "forest-plan-component:unit-inventory:STD-FP-01",
        "candidate_authority_type": "forest_plan_component",
        "source_set_id": source_set_id,
        "authority_category": "forest_plan",
        "authority_document_role": "forest_plan",
        "source_record_ids": ["R1PLAN-CG"],
        "source_records": [
            {
                "source_record_id": "R1PLAN-CG",
                "title": "Custer Gallatin Forest Plan",
                "citation_label": "R1PLAN-CG | Custer Gallatin Forest Plan",
            }
        ],
        "required_package_fact_types": ["geography", "management_area", "overlay"],
        "positive_trigger_groups": [["Crazy Mountains Backcountry Area"]],
        "negative_trigger_groups": [],
        "source_role_filters": {
            "source_record_ids": ["R1PLAN-CG"],
            "document_roles": ["forest_plan"],
            "authority_categories": ["forest_plan"],
        },
        "package_section_filters": {
            "package_evidence_terms": ["Crazy Mountains Backcountry Area"],
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
        "required_source_evidence": {"requires_source_record": True},
        "retrieval_contract": {
            "contract_type": "forest_plan_component_retrieval",
            "query_plan_id": "retrieval-plan:forest-plan-component:STD-FP-01",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "source_queries": ["Crazy Mountains Backcountry Area"],
            "package_queries": ["Crazy Mountains Backcountry Area"],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "forest_plan_component_graph_expansion",
            "start_node_types": ["forest_plan_component", "source_record", "package_fact"],
            "relationship_types": [
                "forest_plan_profile",
                "component_inventory",
                "source_record",
                "source_chunk",
                "geography",
                "management_area",
                "overlay",
                "package_fact",
                "evidence_span",
            ],
            "max_depth": 3,
            "requires_path_trace": True,
        },
        "dependency_contract": {"supporting_source_record_ids": ["R1PLAN-CG"]},
        "search_coverage_requirements": [
            {
                "coverage_class": "forest_plan_scope_miss",
                "required_query_types": [
                    "exact_keyword",
                    "bm25",
                    "metadata_filter",
                    "package_section",
                ],
                "required_artifacts": [
                    "package_fact_graph",
                    "applicability_retrieval_trace",
                    "applicability_graph_trace",
                    "search_coverage_certificates",
                ],
            }
        ],
        "forest_plan": {
            "forest_unit_id": "custer-gallatin-nf",
            "component_inventory_id": "unit-inventory",
            "component_id": "STD-FP-01",
            "component_type": "standard",
            "section_heading": "Crazy Mountains Backcountry Area standard",
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_chunk_count": 1,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "forest_plan_component",
            "component_type": "standard",
            "package_evidence_terms": ["Crazy Mountains Backcountry Area"],
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
    }


def _forest_plan_scope_miss_candidate(source_set_id: str) -> dict:
    candidate = _forest_plan_candidate(source_set_id)
    candidate["candidate_authority_id"] = (
        "forest-plan-component:unit-inventory:STD-FP-MISS"
    )
    candidate["positive_trigger_groups"] = [["Absent Forest Plan Area"]]
    candidate["package_section_filters"] = {
        "package_evidence_terms": ["Absent Forest Plan Area"],
        "geographic_area_ids": ["geo-absent"],
        "management_area_ids": ["mgmt-absent"],
        "overlay_ids": [],
    }
    candidate["retrieval_contract"]["query_plan_id"] = (
        "retrieval-plan:forest-plan-component:STD-FP-MISS"
    )
    candidate["retrieval_contract"]["source_queries"] = [
        "Crazy Mountains Backcountry Area"
    ]
    candidate["retrieval_contract"]["package_queries"] = ["Absent Forest Plan Area"]
    candidate["forest_plan"] = {
        **candidate["forest_plan"],
        "component_id": "STD-FP-MISS",
        "geographic_area_ids": ["geo-absent"],
        "management_area_ids": ["mgmt-absent"],
        "overlay_ids": [],
    }
    candidate["deterministic_applicability_test_contract"] = {
        **candidate["deterministic_applicability_test_contract"],
        "package_evidence_terms": ["Absent Forest Plan Area"],
        "geographic_area_ids": ["geo-absent"],
        "management_area_ids": ["mgmt-absent"],
        "overlay_ids": [],
    }
    return candidate


def _write_package_cache(output_dir: Path, review_id: str) -> None:
    package_dir = output_dir / "reviews" / review_id / "package"
    artifact_sha256 = hashlib.sha256(review_id.encode("utf-8")).hexdigest()
    manifest = [
        {
            "source_set_id": f"ea-package-{review_id}",
            "source_record_id": "EA-PACKAGE-001",
            "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
            "artifact_path": "/tmp/East Crazy Inspiration Divide Land Exchange EA.pdf",
            "artifact_sha256": artifact_sha256,
            "artifact_byte_size": 1000,
            "content_type": "application/pdf",
            "citation_label": "EA-PACKAGE-001",
            "extracted_at": "2026-05-04T00:00:00Z",
            "status": "extracted",
            "parser_name": "unit-parser",
            "parser_version": "1.0",
            "text_path": "/tmp/east-crazy.txt",
            "text_sha256": artifact_sha256,
            "text_char_count": 1000,
            "chunk_count": 3,
        }
    ]
    chunks = [
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=0,
            section="Purpose and Need",
            heading="Purpose and Need",
            text=(
                "The East Crazy Inspiration Divide Land Exchange Project is an "
                "environmental assessment on the Custer Gallatin National Forest."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=1,
            section="Affected Environment",
            heading="Forest Plan Consistency",
            text=(
                "The project area is in the Bridger, Bangtail, and Crazy Mountains "
                "Geographic Area and the Crazy Mountains Backcountry Area. It also "
                "intersects an Inventoried Roadless Area. The Sioux Geographic Area "
                "is not part of the project area."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=2,
            section="Environmental Consequences",
            heading="Resources and Consultation",
            text=(
                "The package identifies Endangered Species Act Section 7 consultation, "
                "wetlands, and floodplains. A Clean Water Act Section 404 permit may "
                "be required."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=3,
            section="Proposed Action",
            heading="Roads and Access",
            text=(
                "The Proposed Action reserves Right-of-Way for Big Timber Creek Road "
                "No. 197."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=4,
            section="Proposed Action",
            heading="Trail Access",
            text=(
                "Trail easements could be required if needed for final design across "
                "private land."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=5,
            section="Environmental Consequences",
            heading="Cumulative Effects",
            text=(
                "Effects from livestock grazing may be possible in the cumulative "
                "effects area."
            ),
        ),
    ]
    manifest[0]["text_char_count"] = sum(len(chunk["text"]) for chunk in chunks)
    manifest[0]["chunk_count"] = len(chunks)
    _write_jsonl(package_dir / "package_manifest.jsonl", manifest)
    _write_jsonl(package_dir / "package_chunks.jsonl", chunks)


def _package_chunk(
    *,
    review_id: str,
    artifact_sha256: str,
    index: int,
    section: str,
    heading: str,
    text: str,
) -> dict:
    return {
        "chunk_id": f"package-chunk-{index}",
        "source_set_id": f"ea-package-{review_id}",
        "source_record_id": "EA-PACKAGE-001",
        "chunk_index": index,
        "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
        "document_role": "ea_package",
        "authority_level": "project_record",
        "artifact_sha256": artifact_sha256,
        "artifact_path": "/tmp/East Crazy Inspiration Divide Land Exchange EA.pdf",
        "citation_label": "EA-PACKAGE-001",
        "parser_name": "unit-parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-04T00:00:00Z",
        "source_text_path": "/tmp/east-crazy.txt",
        "char_start": index * 1000,
        "char_end": index * 1000 + len(text),
        "page": index + 1,
        "section": section,
        "heading": heading,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }


def _source_chunks(source_set_id: str) -> list[dict]:
    return [
        _source_chunk(source_set_id, "R1EA-BASE", "law", "NEPA EA baseline authority."),
        _source_chunk(source_set_id, "R1EA-ESA", "law", "Endangered Species Act consultation."),
        _source_chunk(source_set_id, "R1EA-CE", "regulation", "FANEC categorical exclusion."),
        _source_chunk(source_set_id, "R1EA-CWA", "law", "Clean Water Act permit authority."),
        _source_chunk(
            source_set_id,
            "R1EA-SIOUX",
            "forest_plan",
            "Sioux Geographic Area forest plan direction.",
        ),
        _source_chunk(
            source_set_id,
            "R1EA-ROAD",
            "regulation",
            "National Forest roads access right-of-way special use authority.",
        ),
        _source_chunk(
            source_set_id,
            "R1PLAN-CG",
            "forest_plan",
            "Crazy Mountains Backcountry Area Forest Plan standard.",
        ),
    ]


def _source_chunk(source_set_id: str, source_record_id: str, role: str, text: str) -> dict:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"{source_record_id}-chunk-0",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": f"{source_record_id} title",
        "document_role": role,
        "authority_level": role,
        "host": "example.test",
        "expected_parser": "text",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"/tmp/{source_record_id}.txt",
        "citation_label": f"{source_record_id} citation",
        "original_url": f"https://example.test/{source_record_id}",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit-parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-04T00:00:00Z",
        "source_text_path": f"/tmp/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": 1,
        "section": "Authority Text",
        "heading": "Authority Text",
        "content_sha256": digest,
        "review_topics": [role],
        "text": text,
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
