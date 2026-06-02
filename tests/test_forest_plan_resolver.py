from __future__ import annotations

import hashlib
from pathlib import Path
import json
import tempfile
import unittest

from tests.support.forest_plan_resolver_common import (
    _check,
    _east_crazies_fixture_text,
    _names,
    _write_package,
)
from tests.support.forest_plan_resolver_custer_fixtures import (
    _build_custer_source_library,
    _write_component_inventory,
)
from usfs_r1_ea_sources.forest_plan_components_runtime import _component_finding
from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver


class ForestPlanResolverCoreTests(unittest.TestCase):
    def test_east_crazies_fixture_resolves_profile_driven_forest_plan_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(Path(tmp), _east_crazies_fixture_text())

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="east-crazies-profile-driven",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Custer Gallatin National Forest")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(context["source_record_readiness"]["ready"])
            self.assertEqual(context["source_record_readiness"]["missing_source_record_ids"], [])
            self.assertEqual(
                context["source_record_readiness"]["required_source_record_ids"],
                [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ],
            )
            self.assertEqual(
                _names(context["geographic_areas"]),
                ["Bridger, Bangtail, and Crazy Mountains Geographic Area"],
            )
            self.assertEqual(
                _names(context["management_areas"]),
                ["Crazy Mountains Backcountry Area"],
            )
            self.assertIsNotNone(result.component_findings_path)
            self.assertTrue(result.component_findings_path.exists())
            self.assertTrue(result.summary["component_evaluation"]["validation_passed"])

            supporting_by_route = {
                entry["route_id"]: entry for entry in context["supporting_plan_evidence"]
            }
            self.assertEqual(
                set(supporting_by_route),
                {
                    "support-biological-assessment-esa",
                    "support-biological-opinion-esa",
                    "support-feis-volume-1-context",
                    "support-feis-volume-2-designated-areas",
                },
            )
            self.assertNotIn("support-rod-decision-basis", supporting_by_route)
            for entry in supporting_by_route.values():
                self.assertEqual(entry["resolution_status"], "resolved")
                self.assertTrue(entry["trigger_evidence"])
                self.assertTrue(entry["package_evidence"])
                self.assertTrue(entry["plan_source_evidence"])

    def test_source_set_review_requires_source_set_component_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = (
                output_dir
                / "derived"
                / source_set_id
                / "forest_plan_components"
                / "component_inventory.json"
            )
            inventory_path.unlink()
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                    ]
                ),
            )

            with self.assertRaisesRegex(
                FileNotFoundError,
                "Missing source-set forest-plan component inventory",
            ):
                run_forest_plan_resolver(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    review_id="cg-missing-source-set-components",
                )

    def test_component_inventory_path_writes_evidence_backed_findings_and_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "The EA says quiet nonmotorized recreation opportunities predominate.",
                        "No new permanent or temporary roads are proposed.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-component-findings",
                component_inventory_path=inventory_path,
            )

            self.assertIsNotNone(result.component_findings_path)
            self.assertIsNotNone(result.component_markdown_path)
            self.assertIsNotNone(result.component_reviewer_resolution_queue_path)
            self.assertIsNotNone(result.component_inventory_coverage_path)
            self.assertIsNotNone(result.applicable_standard_coverage_path)
            component_summary = result.summary["component_evaluation"]
            self.assertEqual(component_summary["component_count"], 3)
            self.assertEqual(component_summary["standard_count"], 1)
            self.assertEqual(component_summary["applicable_standard_count"], 1)
            self.assertEqual(component_summary["applied_standard_count"], 1)
            self.assertEqual(component_summary["finding_status_counts"], {"supported": 2, "gap": 1})
            self.assertEqual(
                component_summary["compliance_status_counts"],
                {"not_evaluated_for_compliance": 2, "complies": 1},
            )
            self.assertEqual(component_summary["reviewer_resolution_count"], 1)
            self.assertTrue(component_summary["all_applicable_standards_applied"])
            self.assertTrue(component_summary["component_inventory_coverage_passed"])
            self.assertTrue(component_summary["applicable_standard_coverage_passed"])
            self.assertTrue(component_summary["validation_passed"])
            self.assertTrue(component_summary["reviewer_ready"])
            self.assertTrue(result.summary["reviewer_ready"])

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            supported = findings["cg-test-cmbca-std-01"]
            self.assertEqual(supported["finding_status"], "supported")
            self.assertEqual(supported["compliance_status"], "complies")
            self.assertTrue(supported["plan_source_evidence"])
            self.assertTrue(supported["package_evidence"])
            self.assertEqual(supported["reviewer_resolution_items"], [])

            gap = findings["cg-test-cmbca-suit-01"]
            self.assertEqual(gap["finding_status"], "gap")
            self.assertTrue(gap["plan_source_evidence"])
            self.assertEqual(gap["package_evidence"], [])
            self.assertEqual(gap["reviewer_resolution_items"][0]["reason"], "missing_package_evidence")

            queue = json.loads(
                result.component_reviewer_resolution_queue_path.read_text(encoding="utf-8")
            )
            self.assertEqual(queue["item_count"], 1)
            self.assertEqual(queue["items"][0]["component_id"], "cg-test-cmbca-suit-01")

            standard_coverage = json.loads(
                result.applicable_standard_coverage_path.read_text(encoding="utf-8")
            )
            self.assertTrue(standard_coverage["passed"])
            self.assertTrue(standard_coverage["all_applicable_standards_applied"])
            self.assertEqual(standard_coverage["standard_count"], 1)
            self.assertEqual(standard_coverage["standards"][0]["component_id"], "cg-test-cmbca-std-01")
            self.assertEqual(standard_coverage["standards"][0]["compliance_status"], "complies")

            inventory_coverage = json.loads(
                result.component_inventory_coverage_path.read_text(encoding="utf-8")
            )
            self.assertTrue(inventory_coverage["passed"])
            self.assertEqual(inventory_coverage["component_type_counts"]["standard"], 1)

    def test_applicable_standard_without_package_evidence_blocks_reviewer_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "The EA says quiet nonmotorized recreation opportunities predominate.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-component-standard-gap",
                component_inventory_path=inventory_path,
            )

            component_summary = result.summary["component_evaluation"]
            self.assertFalse(component_summary["validation_passed"])
            self.assertFalse(component_summary["reviewer_ready"])
            self.assertFalse(component_summary["all_applicable_standards_applied"])
            self.assertEqual(component_summary["applied_standard_count"], 0)
            self.assertFalse(result.summary["reviewer_ready"])

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            standard = findings["cg-test-cmbca-std-01"]
            self.assertEqual(standard["finding_status"], "gap")
            self.assertEqual(standard["compliance_status"], "insufficient_evidence")

            standard_coverage = json.loads(
                result.applicable_standard_coverage_path.read_text(encoding="utf-8")
            )
            self.assertFalse(standard_coverage["passed"])
            self.assertFalse(standard_coverage["all_applicable_standards_applied"])
            self.assertEqual(
                standard_coverage["standards"][0]["failure_reasons"],
                ["missing_package_evidence", "unresolved_standard_compliance"],
            )

            validation = report["validation"]
            self.assertFalse(_check(validation, "all_applicable_standards_applied")["passed"])

    def test_component_applicability_decisions_narrow_standard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            review_id = "cg-component-applicability-filter"
            _write_component_applicability_decisions(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                decisions={
                    "cg-test-cmbca-dc-01": "applicable",
                    "cg-test-cmbca-std-01": "not_applicable",
                    "cg-test-cmbca-suit-01": "not_applicable",
                },
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "The EA says quiet nonmotorized recreation opportunities predominate.",
                        "No new permanent or temporary roads are proposed.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                component_inventory_path=inventory_path,
            )

            component_summary = result.summary["component_evaluation"]
            self.assertTrue(component_summary["applicability_decision_filter"]["active"])
            self.assertEqual(
                component_summary["applicability_decision_filter"]["status_counts"],
                {"applicable": 1, "not_applicable": 2},
            )
            self.assertEqual(component_summary["applicable_standard_count"], 0)
            self.assertEqual(component_summary["applied_standard_count"], 0)
            self.assertTrue(component_summary["applicable_standard_coverage_passed"])
            self.assertTrue(component_summary["reviewer_ready"])

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            standard = findings["cg-test-cmbca-std-01"]
            self.assertEqual(standard["applicability_status"], "not_applicable")
            self.assertEqual(standard["finding_status"], "not_applicable")
            self.assertEqual(standard["compliance_status"], "not_applicable")
            self.assertEqual(
                standard["applicability_basis"]["applicability_decision"]["status"],
                "not_applicable",
            )

            standard_coverage = json.loads(
                result.applicable_standard_coverage_path.read_text(encoding="utf-8")
            )
            self.assertTrue(standard_coverage["passed"])
            self.assertEqual(standard_coverage["applicable_standard_count"], 0)
            self.assertEqual(standard_coverage["standards"][0]["plan_source_evidence_count"], 1)

    def test_applicable_component_decision_can_support_context_flagged_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_set_id = "source-set-unit"
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            component = inventory["components"][0]

            finding = _component_finding(
                review_id="component-decision-context-flag",
                component=component,
                context={"needs_reviewer_resolution": True},
                package_chunks=[],
                source_set_id=source_set_id,
                index_path=Path(tmp) / "unused.sqlite",
                package_top_k=3,
                source_top_k=3,
                component_applicability_decisions={
                    component["component_id"]: {
                        "candidate_authority_id": "forest-plan-component:test:cg-test-cmbca-dc-01",
                        "decision_id": "decision:cg-test-cmbca-dc-01",
                        "status": "applicable",
                        "basis_type": "forest_plan_component",
                        "applicability_basis": {
                            "rationale": "Current component applicability decision is applicable."
                        },
                        "package_evidence_spans": [
                            {
                                "citation_label": "EA-PACKAGE-001",
                                "source_record_id": "EA-PACKAGE-001",
                                "package_chunk_id": "chunk:package-1",
                                "text": "The EA addresses quiet nonmotorized recreation.",
                            }
                        ],
                    }
                },
            )

            self.assertEqual(finding["applicability_status"], "applicable")
            self.assertEqual(finding["finding_status"], "supported")
            self.assertEqual(finding["reviewer_resolution_items"], [])
            self.assertEqual(
                finding["package_evidence"][0]["determination_source"],
                "applicability_decision",
            )
            self.assertEqual(finding["plan_source_evidence"][0]["source_record_id"], component["source_record_id"])

    def test_partial_component_applicability_decisions_are_not_exhaustive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            review_id = "cg-partial-component-applicability"
            _write_component_applicability_decisions(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                decisions={"cg-test-cmbca-std-01": "not_applicable"},
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "The EA says quiet nonmotorized recreation opportunities predominate.",
                        "No motorized transport is proposed in the backcountry area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id=review_id,
                component_inventory_path=inventory_path,
            )

            component_summary = result.summary["component_evaluation"]
            self.assertTrue(component_summary["applicability_decision_filter"]["active"])
            self.assertEqual(
                component_summary["applicability_decision_filter"]["status_counts"],
                {"not_applicable": 1},
            )
            self.assertEqual(component_summary["needs_reviewer_resolution_count"], 0)
            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            self.assertEqual(
                findings["cg-test-cmbca-dc-01"]["applicability_status"],
                "applicable",
            )
            self.assertEqual(
                findings["cg-test-cmbca-suit-01"]["applicability_status"],
                "applicable",
            )
            self.assertEqual(
                findings["cg-test-cmbca-std-01"]["applicability_status"],
                "not_applicable",
            )

    def test_unscoped_standard_without_package_evidence_blocks_reviewer_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_unscoped_standard_inventory(
                Path(tmp),
                source_set_id=source_set_id,
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-unscoped-standard-reviewer-resolution",
                component_inventory_path=inventory_path,
            )

            component_summary = result.summary["component_evaluation"]
            self.assertFalse(component_summary["validation_passed"])
            self.assertFalse(component_summary["reviewer_ready"])
            self.assertEqual(component_summary["finding_status_counts"], {"gap": 1})
            self.assertEqual(component_summary["applicable_standard_count"], 1)
            self.assertEqual(component_summary["applied_standard_count"], 0)
            self.assertFalse(component_summary["all_applicable_standards_applied"])
            self.assertFalse(result.summary["reviewer_ready"])

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            finding = report["findings"][0]
            self.assertEqual(finding["applicability_status"], "applicable")
            self.assertEqual(finding["finding_status"], "gap")
            self.assertEqual(finding["compliance_status"], "insufficient_evidence")
            validation = report["validation"]
            self.assertFalse(_check(validation, "all_applicable_standards_applied")["passed"])

            queue = json.loads(
                result.component_reviewer_resolution_queue_path.read_text(encoding="utf-8")
            )
            self.assertEqual(queue["item_count"], 1)
            self.assertEqual(queue["items"][0]["reason"], "missing_package_evidence")

    def test_component_plan_consistency_yes_row_supplies_standard_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        (
                            "| BC-STD-CMBCA-01 | New permanent or temporary roads shall not "
                            "be allowed. | Yes | The EA section 2.2 project design shows no "
                            "new permanent or temporary roads are proposed. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-component-standard-yes-row",
                component_inventory_path=inventory_path,
            )

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            standard = findings["cg-test-cmbca-std-01"]
            self.assertEqual(standard["finding_status"], "supported")
            self.assertEqual(standard["compliance_status"], "complies")
            determination = standard["applicability_basis"]["package_component_determination"]
            self.assertEqual(determination["component_key"], "BC-STD-CMBCA-01")
            self.assertEqual(determination["component_applies"], "yes")
            self.assertEqual(determination["review_section"], "EA section 2.2")

            standard_coverage = json.loads(
                result.applicable_standard_coverage_path.read_text(encoding="utf-8")
            )
            row = standard_coverage["standards"][0]
            self.assertTrue(row["standard_applied"])
            self.assertEqual(row["ea_review_section"], "EA section 2.2")
            self.assertEqual(
                row["package_component_determination"]["component_applies"],
                "yes",
            )

    def test_component_plan_consistency_no_row_marks_standard_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        (
                            "| BC-STD-CMBCA-01 | New permanent or temporary roads shall not "
                            "be allowed. | No | This component applies to a specific "
                            "geographic area which is entirely outside the project area. |"
                        ),
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-component-standard-no-row",
                component_inventory_path=inventory_path,
            )

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            standard = findings["cg-test-cmbca-std-01"]
            self.assertEqual(standard["applicability_status"], "not_applicable")
            self.assertEqual(standard["finding_status"], "not_applicable")
            self.assertEqual(standard["compliance_status"], "not_applicable")
            determination = standard["applicability_basis"]["package_component_determination"]
            self.assertEqual(determination["component_applies"], "no")

            standard_coverage = json.loads(
                result.applicable_standard_coverage_path.read_text(encoding="utf-8")
            )
            self.assertTrue(standard_coverage["passed"])
            self.assertTrue(standard_coverage["all_applicable_standards_applied"])
            self.assertEqual(standard_coverage["applicable_standard_count"], 0)
            self.assertEqual(standard_coverage["standards"][0]["plan_source_evidence_count"], 1)

    def test_context_excluded_standard_keeps_lmp_source_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(Path(tmp), source_set_id=source_set_id)
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            standard = next(
                component
                for component in inventory["components"]
                if component["component_id"] == "cg-test-cmbca-std-01"
            )
            standard.update(
                {
                    "component_id": "cg-test-pryor-std-01",
                    "component_text": (
                        "Standards (PR-STD-VEGNF) 01 Invasive species treatments in "
                        "locations of regional endemic and peripheral plant occurrences "
                        "shall use methods that are not detrimental to long-term persistence."
                    ),
                    "section_heading": "Plan Components-Pryor Mountains Geographic Area",
                    "geographic_area_ids": ["geo-pryor-mountains"],
                    "management_area_ids": [],
                    "package_evidence_terms": [
                        "regional endemic and peripheral plant occurrences"
                    ],
                }
            )
            inventory_path.write_text(
                json.dumps(inventory, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-component-standard-context-excluded",
                component_inventory_path=inventory_path,
            )

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            findings = {finding["component_id"]: finding for finding in report["findings"]}
            standard_finding = findings["cg-test-pryor-std-01"]
            self.assertEqual(standard_finding["applicability_status"], "not_applicable")
            self.assertEqual(standard_finding["finding_status"], "not_applicable")
            self.assertEqual(standard_finding["compliance_status"], "not_applicable")
            self.assertEqual(len(standard_finding["plan_source_evidence"]), 1)

            standard_coverage = json.loads(
                result.applicable_standard_coverage_path.read_text(encoding="utf-8")
            )
            row = standard_coverage["standards"][0]
            self.assertTrue(standard_coverage["passed"])
            self.assertEqual(row["component_key"], "PR-STD-VEGNF-01")
            self.assertEqual(row["plan_source_evidence_count"], 1)
            self.assertEqual(
                row["plan_source_citations"],
                ["R1PLAN-custer-gallatin-nf-02 | test plan | artifact abc123"],
            )

    def test_component_inventory_source_set_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            inventory_path = _write_component_inventory(
                Path(tmp),
                source_set_id="source-set-stale",
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "No new permanent or temporary roads are proposed.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-component-stale",
                component_inventory_path=inventory_path,
            )

            component_summary = result.summary["component_evaluation"]
            self.assertFalse(component_summary["validation_passed"])
            self.assertEqual(
                component_summary["finding_status_counts"],
                {"needs_reviewer_resolution": 3},
            )
            self.assertEqual(component_summary["reviewer_resolution_count"], 3)

            report = json.loads(result.component_findings_path.read_text(encoding="utf-8"))
            validation = report["validation"]
            self.assertFalse(validation["passed"])
            self.assertFalse(
                _check(validation, "component_source_sets_match_review_source_set")["passed"]
            )


def _write_unscoped_standard_inventory(path: Path, *, source_set_id: str) -> Path:
    inventory_path = path / "unscoped_component_inventory.json"
    source_record_id = "R1PLAN-custer-gallatin-nf-02"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    component_text = (
        "Standards (FP-STD-UNSCOPED) 01 Special prescriptions for these areas "
        "will be developed by interdisciplinary teams that include a wildlife biologist."
    )
    content_sha256 = hashlib.sha256(component_text.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "cg-unscoped-standard-inventory",
        "source_set_id": source_set_id,
        "components": [
            {
                "component_id": "cg-unscoped-std-01",
                "forest_unit_id": "custer-gallatin-nf",
                "plan_version": "2022",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "component_type": "standard",
                "section_id": "chapter-3-unscoped-standard",
                "section_heading": "Plan Components-Unscoped Standard",
                "page": None,
                "citation_label": "R1PLAN-custer-gallatin-nf-02 | test plan | artifact abc123",
                "component_text": component_text,
                "geographic_area_ids": [],
                "management_area_ids": [],
                "overlay_ids": [],
                "resource_topics": ["special prescriptions for these areas"],
                "activity_tags": ["wildlife biologist"],
                "package_evidence_terms": [
                    "special prescriptions for these areas",
                    "interdisciplinary teams that include a wildlife biologist",
                ],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "provenance": {
                    "entity": {
                        "type": "forest_plan_component",
                        "source_record_id": source_record_id,
                        "source_chunk_ids": source_chunk_ids,
                        "artifact_sha256": artifact_sha256,
                        "content_sha256": content_sha256,
                    },
                    "activity": {
                        "type": "component_inventory_fixture",
                        "created_at": "2026-05-24T00:00:00Z",
                    },
                    "agent": {
                        "type": "deterministic_test_fixture",
                        "name": "tests/test_forest_plan_resolver.py",
                        "version": "forest-plan-component-inventory-v0",
                    },
                },
            }
        ],
    }
    inventory_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    return inventory_path


def _write_component_applicability_decisions(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    decisions: dict[str, str],
) -> Path:
    decisions_path = (
        output_dir / "reviews" / review_id / "applicability" / "applicability_decisions.jsonl"
    )
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for component_id, status in decisions.items():
        basis_key = (
            "applicability_basis" if status == "applicable" else "non_applicability_basis"
        )
        rows.append(
            {
                "schema_version": "applicability-decisions-v0",
                "source_set_id": source_set_id,
                "candidate_authority_type": "forest_plan_component",
                "candidate_authority_id": f"forest-plan-component:test:{component_id}",
                "decision_id": f"decision:{component_id}",
                "status": status,
                "basis_type": "unit_component_decision",
                basis_key: {
                    "rationale": f"Unit applicability fixture marks {component_id} {status}."
                },
                "rule_template": {"component_id": component_id},
            }
        )
    decisions_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return decisions_path
