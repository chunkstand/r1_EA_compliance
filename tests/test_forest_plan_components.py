from __future__ import annotations

import unittest

from usfs_r1_ea_sources.forest_plan_components import (
    _applicable_standard_coverage,
    _check_supported_package_evidence_section_bindings,
    _component_package_determination,
    _component_package_search,
)
from usfs_r1_ea_sources.forest_plan_components_runtime import (
    _requires_reviewer_resolution_without_scope_binding,
)

from tests.support.forest_plan_component_fixtures import _check
from tests.support.forest_plan_component_fixtures import _package_chunk


class ForestPlanComponentPackageTests(unittest.TestCase):
    def test_applicable_standard_coverage_requires_plan_source_for_not_applicable_standard(
        self,
    ) -> None:
        coverage = _applicable_standard_coverage(
            review_id="review-test",
            source_set_id="source-set-test",
            components=[
                {
                    "component_id": "component-std-1",
                    "component_type": "standard",
                    "component_text": "Standards (FW-STD-TEST) 01 Standard text.",
                }
            ],
            findings=[
                {
                    "finding_id": "finding-std-1",
                    "component_id": "component-std-1",
                    "applicability_status": "not_applicable",
                    "finding_status": "not_applicable",
                    "compliance_status": "not_applicable",
                    "plan_source_evidence": [],
                    "package_evidence": [],
                }
            ],
        )

        self.assertFalse(coverage["passed"])
        self.assertEqual(coverage["applicable_standard_count"], 0)
        self.assertIn(
            "component-std-1",
            _check(coverage, "standards_have_plan_source_evidence")["details"]["component_ids"],
        )
        self.assertIn("missing_plan_source_evidence", coverage["standards"][0]["failure_reasons"])

    def test_component_package_search_is_section_aware_and_filters_negative_rows(self) -> None:
        component = {
            "component_id": "component-water",
            "component_type": "desired_condition",
            "section_heading": "Plan Components-Watershed, Aquatics, and Riparian",
            "component_text": (
                "Desired Conditions (FW-DC-WTR) 01 Watershed features, including "
                "natural disturbance regimes and aquatic or riparian habitats, are well "
                "distributed, diverse, and complex."
            ),
            "package_evidence_terms": ["watershed features", "aquatic", "riparian"],
            "resource_topics": ["watershed features"],
            "activity_tags": ["aquatic", "riparian"],
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "FW-DC-WTR-01 | Watershed features are well distributed. | No | "
                    "This component is forestwide and would apply to the project area, "
                    "but there are no perennial streams in the project area or affected "
                    "by the project."
                ),
            ),
            _package_chunk(
                title="2024 Wildlife Report.pdf",
                text="Riparian habitat may provide wildlife movement corridors.",
            ),
            _package_chunk(
                title="2024 Aquatics Report.pdf",
                text=(
                    "The project protects watershed condition, aquatic habitat, and "
                    "riparian conservation measures through design features."
                ),
            ),
        ]

        result = _component_package_search(component=component, package_chunks=chunks, limit=3)

        self.assertEqual(result["hit_count"], 1)
        self.assertEqual(result["results"][0]["title"], "2024 Aquatics Report.pdf")
        self.assertEqual(result["results"][0]["review_section"], "2024 Aquatics Report.pdf")
        self.assertEqual(
            result["results"][0]["section_binding"]["package_section_family"],
            "hydrology",
        )

    def test_nonstandard_package_search_requires_matching_section_family(self) -> None:
        component = {
            "component_id": "component-wildlife-guideline",
            "component_type": "guideline",
            "section_heading": "Plan Components-Wildlife",
            "component_text": (
                "Guidelines (FW-GDL-WL) 01 To maintain secure habitat and habitat "
                "connectivity for wildlife species, new management activities should "
                "retain hiding cover and avoid displacement."
            ),
            "package_evidence_terms": ["secure habitat", "habitat connectivity"],
            "resource_topics": ["secure habitat"],
            "activity_tags": ["habitat connectivity"],
        }
        chunks = [
            _package_chunk(
                title="Final Environmental Assessment.pdf",
                text=(
                    "The proposed action mentions secure habitat, but this summary "
                    "does not bind the discussion to a resource-specific section."
                ),
            ),
            _package_chunk(
                title="Hydrology and Wetlands Report.pdf",
                text=(
                    "Riparian habitat and wetland habitat connectivity would be "
                    "maintained through hydrology design features."
                ),
            ),
            _package_chunk(
                title="Wildlife Report.pdf",
                text=(
                    "Wildlife habitat connectivity and secure habitat would be "
                    "maintained by retaining hiding cover near movement corridors."
                ),
            ),
        ]

        result = _component_package_search(component=component, package_chunks=chunks, limit=3)

        self.assertEqual(result["hit_count"], 1)
        self.assertEqual(result["results"][0]["title"], "Wildlife Report.pdf")
        self.assertEqual(
            result["results"][0]["section_binding"]["package_section_family"],
            "wildlife",
        )
        self.assertEqual(
            result["results"][0]["section_binding"]["binding_policy"],
            "strict_nonstandard_section_family",
        )

    def test_plan_consistency_yes_rows_are_valid_section_bindings(self) -> None:
        component = {
            "component_id": "component-road-goal",
            "component_type": "goal",
            "section_heading": "Plan Components-Roads and Trails",
            "component_text": (
                "Goals (FW-GO-RT) 01 The road system is part of a broader public "
                "road system that is under the jurisdiction of multiple road agencies."
            ),
            "package_evidence_terms": [
                "the road system",
                "broader public road system",
            ],
            "resource_topics": ["road system"],
            "activity_tags": ["road agencies"],
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "FW-GO-RT-01 | The road system is part of a broader public road "
                    "system that is under the jurisdiction of multiple road agencies. | "
                    "Yes | The proposed access easements and retained routes are "
                    "consistent with this plan component."
                ),
            )
        ]

        result = _component_package_search(component=component, package_chunks=chunks, limit=3)

        self.assertEqual(result["hit_count"], 1)
        evidence = result["results"][0]
        self.assertTrue(evidence["section_binding"]["matched"])
        self.assertTrue(evidence["section_binding"]["explicit_plan_consistency_component_row"])
        self.assertTrue(evidence["plan_consistency_component_row"])
        self.assertEqual(
            evidence["section_binding"]["binding_policy"],
            "explicit_plan_consistency_component_row",
        )

    def test_supported_package_evidence_validation_rejects_mismatched_sections(self) -> None:
        finding = {
            "finding_id": "component-wildlife-guideline-finding",
            "component_id": "component-wildlife-guideline",
            "finding_status": "supported",
            "package_evidence": [
                {
                    "citation_label": "PKG-001",
                    "review_section": "Hydrology Report.pdf",
                    "section_binding": {
                        "component_section_families": ["wildlife"],
                        "package_section_family": "hydrology",
                        "matched": False,
                    },
                }
            ],
        }

        check = _check_supported_package_evidence_section_bindings([finding])

        self.assertFalse(check["passed"])
        self.assertEqual(check["details"]["failure_count"], 1)
        self.assertEqual(
            check["details"]["failures"][0]["reason"],
            "section_binding_mismatch",
        )

    def test_supported_package_evidence_validation_allows_table_determinations(self) -> None:
        finding = {
            "finding_id": "component-soil-dc-finding",
            "component_id": "component-soil-dc",
            "finding_status": "supported",
            "package_evidence": [
                {
                    "citation_label": "PKG-001",
                    "review_section": "Plan Consistency Table.pdf",
                    "determination_source": "ea_plan_consistency_table",
                }
            ],
        }

        check = _check_supported_package_evidence_section_bindings([finding])

        self.assertTrue(check["passed"])

    def test_nonstandard_package_search_binds_scenery_and_sustainability_sections(self) -> None:
        scenery_component = {
            "component_id": "component-scenery-guideline",
            "component_type": "guideline",
            "section_heading": "Plan Components-Scenery",
            "component_text": (
                "Guidelines (FW-GDL-SCENERY) 01 Management activities should repeat "
                "form, line, color, and texture of the natural landscape character."
            ),
            "package_evidence_terms": ["natural landscape character", "form line color texture"],
            "resource_topics": ["natural landscape character"],
            "activity_tags": ["form line color texture"],
        }
        sustainability_component = {
            "component_id": "component-sustainability-objective",
            "component_type": "objective",
            "section_heading": "Plan Components-Sustainability",
            "component_text": (
                "Objectives (FW-OBJ-CARB) 01 Maintain carbon stocks and climate "
                "resilience while supporting sustainable ecosystem services."
            ),
            "package_evidence_terms": ["carbon stocks", "climate resilience"],
            "resource_topics": ["carbon stocks"],
            "activity_tags": ["climate resilience"],
        }
        chunks = [
            _package_chunk(
                title="Recreation and Access.pdf",
                text=(
                    "A scenic trail would provide views of the natural landscape "
                    "character, but this section addresses access management."
                ),
            ),
            _package_chunk(
                title="Scenery and Visual Resources.pdf",
                text=(
                    "Project design would repeat form, line, color, and texture and "
                    "protect natural landscape character."
                ),
            ),
            _package_chunk(
                title="Wildlife Report.pdf",
                text=(
                    "Wildlife habitat would be resilient, but the report does not "
                    "evaluate carbon stocks or climate resilience."
                ),
            ),
            _package_chunk(
                title="Sustainability and Climate.pdf",
                text=(
                    "The project would maintain carbon stocks and climate resilience "
                    "while protecting sustainable ecosystem services."
                ),
            ),
        ]

        scenery_result = _component_package_search(
            component=scenery_component,
            package_chunks=chunks,
            limit=3,
        )
        sustainability_result = _component_package_search(
            component=sustainability_component,
            package_chunks=chunks,
            limit=3,
        )

        self.assertEqual(scenery_result["hit_count"], 1)
        self.assertEqual(scenery_result["results"][0]["title"], "Scenery and Visual Resources.pdf")
        self.assertEqual(
            scenery_result["results"][0]["section_binding"]["package_section_family"],
            "scenery",
        )
        self.assertEqual(sustainability_result["hit_count"], 1)
        self.assertEqual(
            sustainability_result["results"][0]["title"],
            "Sustainability and Climate.pdf",
        )
        self.assertEqual(
            sustainability_result["results"][0]["section_binding"]["package_section_family"],
            "sustainability",
        )

    def test_component_package_search_supports_restrictive_access_standard(self) -> None:
        component = {
            "component_id": "component-ab-rcrea",
            "component_type": "standard",
            "section_heading": "Plan Components-Bridger Bangtail Crazy Mountains",
            "component_text": (
                "Standards (AB-STD-RCREA) 01 New motorized trails shall not be "
                "constructed or designated, except for reroutes of existing trails "
                "necessary for safety, resource protection or enhancement."
            ),
            "package_evidence_terms": [
                "new motorized trails",
                "motorized trails constructed designated except",
            ],
            "resource_topics": ["new motorized trails"],
            "activity_tags": ["trails constructed designated except reroutes"],
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "MG-STD-BHBCA-03 | New motorized trails shall not be constructed "
                    "or designated. | No | The geographic area to which this "
                    "component applies is not part of the project area."
                ),
            ),
            _package_chunk(
                title="2024 Roads Trails Access.pdf",
                text=(
                    "The Forest Service would reserve an easement on this existing "
                    "motorized trail as part of the proposed action."
                ),
            ),
            _package_chunk(
                title="Final Environmental Assessment.pdf",
                text=(
                    "The new trail would be called Sweet Trunk Trail No. 274. The "
                    "route would be managed consistently with the Land Management "
                    "Plan for nonmotorized, foot and horse recreation opportunities."
                ),
            ),
        ]

        result = _component_package_search(component=component, package_chunks=chunks, limit=3)

        self.assertEqual(result["hit_count"], 1)
        self.assertEqual(result["results"][0]["title"], "Final Environmental Assessment.pdf")
        self.assertEqual(
            result["results"][0]["section_binding"]["package_section_family"],
            "recreation_access",
        )

    def test_component_package_determination_matches_spaced_component_codes(self) -> None:
        component = {
            "component_text": (
                "Standards (FW-STD-FAC) 01 Extraction of saleable mineral materials "
                "shall not be allowed in administrative sites."
            )
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "FW-STD-FAC -01 | Extraction of saleable mineral materials shall "
                    "not be allowed in administrative sites. | No | No administrative "
                    "sites are included in the project."
                ),
            )
        ]

        determination = _component_package_determination(
            component=component,
            package_chunks=chunks,
        )

        self.assertIsNotNone(determination)
        self.assertEqual(determination["component_key"], "FW-STD-FAC-01")
        self.assertEqual(determination["component_applies"], "no")

    def test_component_package_determination_matches_empty_code_text_row(self) -> None:
        component = {
            "component_text": (
                "Standards (FW-STD-SCENERY) 01 Timber harvest units shall be shaped "
                "and blended with the natural terrain to the extent practicable."
            )
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "| | Timber harvest units shall be shaped and blended with the "
                    "natural terrain to the extent practicable. | No | The project "
                    "does not include timber harvest. |"
                ),
            )
        ]

        determination = _component_package_determination(
            component=component,
            package_chunks=chunks,
        )

        self.assertIsNotNone(determination)
        self.assertEqual(determination["component_key"], "FW-STD-SCENERY-01")
        self.assertEqual(determination["component_applies"], "no")

    def test_component_package_determination_reads_split_plan_consistency_rows(self) -> None:
        component = {
            "component_text": (
                "Desired Conditions (FW-DC-SOIL) 01 The inherent productivity of soil "
                "resources sustains native plant communities and wildlife populations "
                "while maintaining hydrologic function and providing for social and "
                "economic benefits."
            )
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "| FW-DC-SOIL-01 | The inherent productivity of soil resources "
                    "sustains native plant communities and wildlife populations while "
                    "maintaining hydrologic function and providing for social and "
                    "economic benefits."
                ),
            ),
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "C-SOIL-01 | The inherent productivity of soil resources sustains "
                    "native plant communities and wildlife populations while maintaining "
                    "hydrologic function and providing for social and economic benefits. "
                    "| Yes | The project does not affect the Forest's ability to attain "
                    "this desired condition. |"
                ),
            ),
        ]

        determination = _component_package_determination(
            component=component,
            package_chunks=chunks,
        )

        self.assertIsNotNone(determination)
        self.assertEqual(determination["component_key"], "FW-DC-SOIL-01")
        self.assertEqual(determination["component_applies"], "yes")
        self.assertIn(
            "chunk_window_ids",
            determination["provenance"],
        )

    def test_component_package_determination_reads_split_component_key_row(self) -> None:
        component = {
            "component_text": (
                "Objectives (FW-OBJ-ROSSPNM) 01 Eliminate five identified unauthorized "
                "motorized travel incursions per decade to maintain the semi-primitive "
                "non-motorized setting."
            )
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "| FW-OBJ-ROSSPNM- | Eliminate five identified unauthorized "
                    "motorized travel incursions per decade to maintain the semi- | "
                    "No | The project was not designed to meet this objective, but it "
                    "will not prevent the Forest from meeting it. | | 01 | primitive "
                    "non-motorized setting. |"
                ),
            )
        ]

        determination = _component_package_determination(
            component=component,
            package_chunks=chunks,
        )

        self.assertIsNotNone(determination)
        self.assertEqual(determination["component_key"], "FW-OBJ-ROSSPNM-01")
        self.assertEqual(determination["component_applies"], "no")

    def test_component_package_determination_reads_plain_text_plan_consistency_rows(self) -> None:
        component = {
            "component_text": (
                "Goals (MG-GO-ELGA) 01 The Custer Gallatin National Forest and partners "
                "operate the visitor center complex to host exhibits, films, "
                "presentations and interpretive trails focused on earthquakes, plate "
                "tectonics, and seismicity of the area and the world."
            )
        }
        chunks = [
            _package_chunk(
                title="Plan Consistency Table.pdf",
                text=(
                    "MG-GO-ELGA-01 The Custer Gallatin National Forest and partners "
                    "operate the visitor center complex to host exhibits, films, "
                    "presentations and interpretive trails focused on earthquakes, "
                    "plate tectonics, and seismicity of the area and the world. "
                    "No - The geographic area to which this component applies is not "
                    "part of the project area. MG-DC-BHBCA-01 The backcountry area "
                    "provides less developed recreation opportunities."
                ),
            )
        ]

        determination = _component_package_determination(
            component=component,
            package_chunks=chunks,
        )

        self.assertIsNotNone(determination)
        self.assertEqual(determination["component_key"], "MG-GO-ELGA-01")
        self.assertEqual(determination["component_applies"], "no")

    def test_forestwide_standard_with_topic_terms_stays_applicable_for_adjudication(
        self,
    ) -> None:
        component = {
            "component_type": "standard",
            "geographic_area_ids": [],
            "management_area_ids": [],
            "overlay_ids": [],
            "resource_topics": ["riparian management zones"],
            "activity_tags": ["activities proposed in riparian management zones"],
        }

        self.assertFalse(
            _requires_reviewer_resolution_without_scope_binding(
                component=component,
                package_determination=None,
            )
        )
