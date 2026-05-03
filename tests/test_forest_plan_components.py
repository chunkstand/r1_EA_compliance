from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.forest_plan_components import (
    _applicable_standard_coverage,
    _check_supported_package_evidence_section_bindings,
    _component_inventory_coverage,
    _component_package_determination,
    _component_package_search,
    build_forest_plan_component_inventory,
    load_forest_plan_component_inventory,
)


class ForestPlanComponentInventoryBuilderTests(unittest.TestCase):
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

    def test_builds_labeled_component_inventory_from_forest_plan_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=_FOREST_PLAN_TEXT,
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-nonplan",
                        text="Standards (OTHER-STD) 01 This should not be selected.",
                    ),
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id=source_record_id,
                            text="Standards (NONPLAN-STD) 01 This should not be selected.",
                        ),
                        "document_role": "environmental_assessment",
                    },
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
                geographic_area_ids=["geo-bridger-bangtail-crazy"],
                management_area_ids=["mgmt-crazy-mountains-bca"],
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["component_count"], 3)
            self.assertTrue(result.summary["coverage_passed"])
            self.assertEqual(result.summary["standard_count"], 1)
            self.assertEqual(
                result.summary["component_type_counts"],
                {
                    "desired_condition": 1,
                    "standard": 1,
                    "suitability": 1,
                },
            )
            self.assertTrue(result.components_jsonl_path.exists())
            self.assertTrue(result.coverage_path.exists())
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertTrue(coverage["passed"])
            self.assertEqual(coverage["detected_component_count"], 3)
            self.assertEqual(coverage["detected_standard_count"], 1)
            self.assertEqual(coverage["missing_standard_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            self.assertEqual(len(components), 3)
            standard = next(
                component for component in components if component["component_type"] == "standard"
            )
            self.assertEqual(standard["source_set_id"], source_set_id)
            self.assertEqual(standard["source_record_id"], source_record_id)
            self.assertEqual(standard["source_chunk_ids"], [f"chunk:{source_record_id}"])
            self.assertIn(
                "new permanent or temporary roads",
                standard["package_evidence_terms"],
            )
            self.assertEqual(
                standard["management_area_ids"],
                ["mgmt-crazy-mountains-bca"],
            )
            self.assertEqual(
                standard["section_heading"],
                "Plan Components-Crazy Mountains Backcountry Area (CMBCA)",
            )

    def test_build_uses_nearby_section_context_for_area_prefixed_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "The Pryor Mountains provide resilient habitat conditions for "
                            "regional endemic and peripheral plant species occurrences. "
                            "Standards (PR-STD-VEGNF) 01 Invasive species treatments in "
                            "locations of regional endemic and peripheral plant occurrences "
                            "shall use methods that are not detrimental to the long-term "
                            "persistence of the species."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
            )

            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            standard = components[0]
            self.assertEqual(standard["component_id"], f"{source_record_id}-PR-STD-VEGNF-01")
            self.assertEqual(standard["geographic_area_ids"], ["geo-pryor-mountains"])

    def test_build_skips_cross_reference_labels_and_matches_singular_area_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Guidelines (FW-GDL-VEGNF) See additional plan components "
                            "for shrubland habitats. 01 To promote habitat heterogeneity, "
                            "prescribed fire management should include a mosaic of burned "
                            "and unburned areas.\n"
                            "Desired Conditions (PR-DC-WHT) 01 Pryor Mountain Wild Horse "
                            "Territory maintains a thriving ecological balance with other "
                            "resources and activities.\n"
                            "Goals (MG-GO-ELGA) 01 The Custer Gallatin National Forest and "
                            "partners operate the visitor center complex."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
            )

            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            component_ids = {component["component_id"] for component in components}
            self.assertNotIn(f"{source_record_id}-FW-GDL-VEGNF-See", component_ids)
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["inventory_quality_issue_count"], 1)
            self.assertEqual(coverage["blocking_inventory_quality_issue_count"], 0)
            quality_issue = coverage["inventory_quality_issues"][0]
            self.assertEqual(quality_issue["issue_type"], "cross_reference_component_label")
            self.assertEqual(
                quality_issue["candidate_component_id"],
                f"{source_record_id}-FW-GDL-VEGNF-See",
            )
            self.assertEqual(
                quality_issue["suggested_component_id"],
                f"{source_record_id}-FW-GDL-VEGNF-01",
            )
            wild_horse = next(
                component
                for component in components
                if component["component_id"] == f"{source_record_id}-PR-DC-WHT-01"
            )
            earthquake_lake = next(
                component
                for component in components
                if component["component_id"] == f"{source_record_id}-MG-GO-ELGA-01"
            )
            self.assertEqual(wild_horse["geographic_area_ids"], ["geo-pryor-mountains"])
            self.assertIn("mgmt-earthquake-lake", earthquake_lake["management_area_ids"])

    def test_build_stops_component_text_before_malformed_component_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Objectives (FW-OBJ-VEGNF) 01 Complete vegetation projects "
                            "each decade. Guidelines (FW-GDL-VEGNF) See additional plan "
                            "components for shrubland habitats. 01 Prescribed fire "
                            "management should include a mosaic of burned and unburned "
                            "areas. Standards (FW-STD-VEGNF) 01 Vegetation treatment "
                            "methods shall protect rare plants."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
            )

            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            objective = next(
                component
                for component in components
                if component["component_id"] == f"{source_record_id}-FW-OBJ-VEGNF-01"
            )
            self.assertNotIn("FW-GDL-VEGNF", objective["component_text"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertTrue(coverage["passed"])
            self.assertEqual(coverage["inventory_quality_issue_count"], 1)

    def test_duplicate_standard_labels_fail_build_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            _FOREST_PLAN_TEXT
                            + "\nStandards (BC-STD-CMBCA) 01 Duplicate standard text."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
                management_area_ids=["mgmt-crazy-mountains-bca"],
            )

            duplicate_id = f"{source_record_id}-BC-STD-CMBCA-01"
            self.assertFalse(result.summary["passed"])
            self.assertFalse(result.summary["coverage_passed"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertFalse(coverage["passed"])
            self.assertEqual(coverage["duplicate_component_ids"], [duplicate_id])
            self.assertEqual(coverage["duplicate_standard_ids"], [duplicate_id])
            failed_checks = {
                check["name"] for check in coverage["checks"] if not check["passed"]
            }
            self.assertIn("built_component_ids_are_unique", failed_checks)
            self.assertIn("detected_standard_labels_are_unique", failed_checks)
            with self.assertRaises(ValueError):
                load_forest_plan_component_inventory(
                    result.inventory_path,
                    forest_unit_id="custer-gallatin-nf",
                )

    def test_overlapping_chunk_duplicates_are_merged_before_build_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            first_chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                text=(
                    "Plan Components-Crazy Mountains Backcountry Area (CMBCA).\n"
                    "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads "
                    "shall not be allowed."
                ),
            )
            overlap_chunk = {
                **_chunk(
                    source_set_id=source_set_id,
                    source_record_id=source_record_id,
                    text=(
                        "Plan Components-Crazy Mountains Backcountry Area (CMBCA).\n"
                        "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads "
                        "shall not be allowed.\nCuster Gallatin Land Management Plan page 72."
                    ),
                ),
                "chunk_id": f"chunk:{source_record_id}:overlap",
                "chunk_index": 1,
            }
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[first_chunk, overlap_chunk],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.summary["coverage_passed"])
            self.assertEqual(result.summary["component_count"], 1)
            self.assertEqual(result.summary["standard_count"], 1)
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["duplicate_component_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            self.assertEqual(coverage["detected_component_count"], 1)
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )
            self.assertEqual(len(components), 1)
            self.assertEqual(
                components[0]["source_chunk_ids"],
                [f"chunk:{source_record_id}", f"chunk:{source_record_id}:overlap"],
            )
            self.assertEqual(
                components[0]["management_area_ids"],
                ["mgmt-crazy-mountains-bca"],
            )

    def test_failing_build_coverage_blocks_generated_inventory_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-custer-gallatin-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=_FOREST_PLAN_TEXT,
                    ),
                ],
            )
            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="custer-gallatin-nf",
                plan_version="2022",
                chunks_path=chunks_path,
                management_area_ids=["mgmt-crazy-mountains-bca"],
            )
            build_coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            build_coverage["passed"] = False
            build_coverage["duplicate_standard_ids"] = ["R1PLAN-custer-gallatin-nf-02-STD-01"]
            result.coverage_path.write_text(
                json.dumps(build_coverage, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="custer-gallatin-nf",
            )

            review_coverage = _component_inventory_coverage(
                review_id="review-test",
                source_set_id=source_set_id,
                component_inventory_path=result.inventory_path,
                components=components,
            )

            self.assertFalse(review_coverage["passed"])
            self.assertTrue(review_coverage["component_inventory_build_coverage_required"])
            self.assertFalse(review_coverage["component_inventory_build_coverage_passed"])
            check = next(
                check
                for check in review_coverage["checks"]
                if check["name"] == "component_inventory_build_coverage_passes"
            )
            self.assertFalse(check["passed"])
            self.assertTrue(check["details"]["present"])

    def test_cli_parser_exposes_inventory_builder_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "forest-plan-components-build",
                "--source-set-id",
                "source-set-test",
                "--source-record-id",
                "R1PLAN-custer-gallatin-nf-02",
                "--plan-version",
                "2022",
                "--management-area-id",
                "mgmt-crazy-mountains-bca",
            ]
        )

        self.assertEqual(args.command, "forest-plan-components-build")
        self.assertEqual(args.management_area_ids, ["mgmt-crazy-mountains-bca"])


_FOREST_PLAN_TEXT = """
Plan Components-Crazy Mountains Backcountry Area (CMBCA).
Desired Conditions (BC-DC-CMBCA) 01 Quiet, nonmotorized recreation opportunities predominate.
Standards (BC-STD-CMBCA) 01 New permanent or temporary roads shall not be allowed.
Suitability (BC-SUIT-CMBCA) 01 The backcountry area is not suitable for motorized transport.
"""


def _chunk(*, source_set_id: str, source_record_id: str, text: str) -> dict:
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": "Custer Gallatin Land Management Plan",
        "document_role": "forest_plan",
        "authority_level": "forest_plan",
        "host": "example.test",
        "expected_parser": "pdf",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"artifacts/raw/{source_record_id}.pdf",
        "citation_label": f"{source_record_id} | Custer Gallatin LMP",
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-01T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": "Plan Components-Crazy Mountains Backcountry Area (CMBCA)",
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }


def _package_chunk(*, title: str, text: str) -> dict:
    source_record_id = title.replace(" ", "-")
    return {
        **_chunk(
            source_set_id="source-set-package",
            source_record_id=source_record_id,
            text=text,
        ),
        "title": title,
        "document_role": "environmental_assessment",
        "authority_level": "project",
        "citation_label": f"{source_record_id} package citation",
        "artifact_path": f"package/{source_record_id}.pdf",
        "heading": None,
    }


def _write_chunks(*, output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _check(report: dict, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing check {name!r}")


if __name__ == "__main__":
    unittest.main()
