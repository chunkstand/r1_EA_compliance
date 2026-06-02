from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from usfs_r1_ea_sources.forest_plan_components import build_forest_plan_component_inventory
from usfs_r1_ea_sources.forest_plan_components import load_forest_plan_component_inventory

from tests.support.forest_plan_component_fixtures import _chunk
from tests.support.forest_plan_component_fixtures import _FOREST_PLAN_TEXT
from tests.support.forest_plan_component_fixtures import _write_chunks


class ForestPlanComponentInventoryBuildTests(unittest.TestCase):
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

    def test_builds_inventory_from_code_style_components_without_parentheses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-nez-perce-clearwater-nfs-06"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Across the Landscape Goals FW-GL-TE-01. The forest works with "
                            "partners across jurisdictions. Desired Conditions FW-DC-TE-02. "
                            "Habitat conditions support native species. Objectives "
                            "FW-OBJ-TE-03. Restore hardwood overstory conditions. "
                            "Standards FW-STD-TE-04. Limit road density near key habitat."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="nez-perce-clearwater-nfs",
                plan_version="2025",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="nez-perce-clearwater-nfs",
            )
            component_ids = {component["component_id"] for component in components}
            self.assertIn(f"{source_record_id}-FW-GL-TE-01", component_ids)
            self.assertIn(f"{source_record_id}-FW-DC-TE-02", component_ids)
            self.assertIn(f"{source_record_id}-FW-OBJ-TE-03", component_ids)
            self.assertIn(f"{source_record_id}-FW-STD-TE-04", component_ids)

    def test_builds_inventory_from_colon_number_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-beaverhead-deerlodge-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Air Quality Standards Standard 1: Meet smoke management "
                            "requirements according to the Idaho/Montana Airshed Group "
                            "Operating Guide. Standard 2: Coordinate burns to reduce smoke "
                            "intrusions."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="beaverhead-deerlodge-nf",
                plan_version="2009",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="beaverhead-deerlodge-nf",
            )
            component_ids = {component["component_id"] for component in components}
            self.assertIn(f"{source_record_id}-AIR-QUALITY-STD-1", component_ids)
            self.assertIn(f"{source_record_id}-AIR-QUALITY-STD-2", component_ids)

    def test_builds_inventory_from_period_number_components_and_skips_standard_no_reference(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-dakota-prairie-grasslands-05"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Goal 1: Ensure sustainable ecosystems. Standard 2. Meet air "
                            "quality requirements. Guideline 7. Design stream crossings "
                            "to pass flow and sediment. Wildlife and Fish Standards "
                            "21. Wildlife features shall be protected during harvest. "
                            "Timber harvest prescriptions will be applicable as defined "
                            "in Forest Standard No. 21. Special prescriptions protect "
                            "riparian areas."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="dakota-prairie-grasslands",
                plan_version="2001",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="dakota-prairie-grasslands",
            )
            self.assertEqual(len(components), 4)
            component_ids = {component["component_id"] for component in components}
            self.assertTrue(any(component_id.endswith("-GO-1") for component_id in component_ids))
            self.assertTrue(any(component_id.endswith("-STD-2") for component_id in component_ids))
            self.assertTrue(any(component_id.endswith("-GL-7") for component_id in component_ids))
            self.assertTrue(any(component_id.endswith("-STD-21") for component_id in component_ids))
            standard_21 = next(
                component
                for component in components
                if component["component_id"].endswith("-STD-21")
            )
            self.assertIn("Wildlife features shall be protected", standard_21["component_text"])
            self.assertNotIn("Special prescriptions protect", standard_21["component_text"])

    def test_builds_legacy_management_area_numbered_direction_with_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-legacy-forest-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "III. Management Area Direction MANAGEMENT AREA 16 "
                            "C. Standards 1. Timber harvest shall maintain soil "
                            "productivity. 2. Roads will be closed after project "
                            "completion."
                        ),
                    ),
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id=source_record_id,
                            text=(
                                "Timber Practices: 3. Regeneration harvest may occur "
                                "where needed to meet management objectives. D. Schedule "
                                "of Management Practices Soil Inventory M Acres 1 0"
                            ),
                        ),
                        "chunk_id": f"chunk:{source_record_id}:1",
                        "chunk_index": 1,
                    },
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="legacy-forest-nf",
                plan_version="1986",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["standard_count"], 3)
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["detected_standard_count"], 3)
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="legacy-forest-nf",
            )
            self.assertEqual(len(components), 3)
            for component in components:
                self.assertEqual(component["component_type"], "standard")
                self.assertIn("-MA-16-", component["component_id"])
                self.assertEqual(component["management_area_ids"], ["mgmt-ma-16"])
                self.assertIn("Management Area 16", component["section_heading"])

    def test_legacy_descriptive_appendix_tables_do_not_inherit_standard_context(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-flathead-nf-01"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Management Area Direction MANAGEMENT AREA 4b B. Standards "
                            "1. Project activities shall protect recommended wilderness "
                            "characteristics. Appendix G: Factors for Wilderness "
                            "Recommendation Areas Table G-4. Jewel Basin Recommended "
                            "Wilderness Area Factors Description 2. Summarized description "
                            "of the recommended boundary Generally the western boundary "
                            "follows the Swan Crest. 3. Brief description of the general "
                            "geography, topography, and vegetation Existing vegetation "
                            "includes Douglas-fir and western larch."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="flathead-nf",
                plan_version="2018",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["standard_count"], 1)
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="flathead-nf",
            )
            self.assertEqual(len(components), 1)
            self.assertIn("protect recommended wilderness", components[0]["component_text"])
            self.assertNotIn("recommended boundary", components[0]["component_text"])

    def test_legacy_potential_management_approaches_do_not_inherit_standard_context(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-flathead-nf-01"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Management Area Direction MANAGEMENT AREA 1b B. Standards "
                            "1. Project activities shall maintain lynx habitat. "
                            "Potential Management Approaches and Possible Actions "
                            "100. Potential Management Approaches and Possible Actions "
                            "Possible strategies for vegetation management activities may "
                            "include thinning or prescribed burning."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="flathead-nf",
                plan_version="2018",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["standard_count"], 1)
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="flathead-nf",
            )
            self.assertEqual(len(components), 1)
            self.assertIn("maintain lynx habitat", components[0]["component_text"])
            self.assertNotIn("Possible strategies", components[0]["component_text"])

    def test_legacy_figure_captions_do_not_inherit_component_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-flathead-nf-01"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Management Area Direction MANAGEMENT AREA 1b B. Standards "
                            "1. Project activities shall maintain lynx habitat. "
                            "List of Figures Figure C-7. A 30 year old forest stand "
                            "that had modified precommercial thinning 20 years after "
                            "harvest, depicted about 10 years after thinning. Trees were "
                            "thinned to an average of 300 trees per acre."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="flathead-nf",
                plan_version="2018",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["standard_count"], 1)
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="flathead-nf",
            )
            self.assertEqual(len(components), 1)
            self.assertIn("maintain lynx habitat", components[0]["component_text"])
            self.assertNotIn("30 year old forest stand", components[0]["component_text"])

    def test_legacy_citation_narrative_does_not_inherit_standard_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-flathead-nf-01"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Management Area Direction MANAGEMENT AREA 1b B. Standards "
                            "1. Project activities shall maintain lynx habitat. "
                            "Examples of possible strategies associated with habitat "
                            "restoration include patch cutting. 6. Bull stated that "
                            "the highest numbers of trapped hares occurred in the patch "
                            "cuts, similar to findings of other researchers."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="flathead-nf",
                plan_version="2018",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["standard_count"], 1)
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="flathead-nf",
            )
            self.assertEqual(len(components), 1)
            self.assertIn("maintain lynx habitat", components[0]["component_text"])
            self.assertNotIn("Bull stated", components[0]["component_text"])

    def test_colon_number_table_of_contents_entries_are_suppressed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-dakota-prairie-grasslands-05"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "GOALS AND OBJECTIVES Goal 1: Ensure Sustainable Ecosystems "
                            ".................................... 1-2 Goal 2: Multiple "
                            "Benefits to People .................................... 1-4"
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="dakota-prairie-grasslands",
                plan_version="2002",
                chunks_path=chunks_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["component_count"], 0)

    def test_colon_number_components_avoid_generic_legacy_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-beaverhead-deerlodge-nf-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Chapter Three Forestwide Direction Standards Standard 1: "
                            "No impact to identified TCPs shall occur until Forest "
                            "officials consult with affected tribes."
                        ),
                    ),
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id=source_record_id,
                            text=(
                                "Chapter Three Forestwide Direction Standards Standard 1: "
                                "On lands suitable for timber production, even aged harvest "
                                "may occur only upon a finding that it is the appropriate "
                                "method."
                            ),
                        ),
                        "chunk_id": f"chunk:{source_record_id}:1",
                        "chunk_index": 1,
                    },
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id=source_record_id,
                            text=(
                                "Objectives None Standards Standard 1: Energy transmission "
                                "facilities shall be located only in designated utility "
                                "corridors."
                            ),
                        ),
                        "chunk_id": f"chunk:{source_record_id}:2",
                        "chunk_index": 2,
                    },
                    {
                        **_chunk(
                            source_set_id=source_set_id,
                            source_record_id=source_record_id,
                            text=(
                                "Objectives None Standards Standards 1: The interim standards "
                                "in Table 6 apply to livestock grazing operations."
                            ),
                        ),
                        "chunk_id": f"chunk:{source_record_id}:3",
                        "chunk_index": 3,
                    },
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="beaverhead-deerlodge-nf",
                plan_version="2009",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["duplicate_component_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            component_ids = {
                component["component_id"]
                for component in load_forest_plan_component_inventory(
                    result.inventory_path,
                    forest_unit_id="beaverhead-deerlodge-nf",
                )
            }
            self.assertNotIn(f"{source_record_id}-THREE-STD-1", component_ids)
            self.assertNotIn(f"{source_record_id}-NONE-STD-1", component_ids)
            self.assertEqual(len(component_ids), 4)

    def test_code_style_page_headers_are_suppressed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-nez-perce-clearwater-nfs-06"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Desired Conditions FW-DC-ED-01. Land Management Plan "
                            "Nez Perce-Clearwater National Forests 41"
                        ),
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "Desired Conditions FW-DC-ED-01. Interpretation and "
                            "educational opportunities enhance visitor understanding. "
                            "Standards FW-STD-ED-02. Interpretive facilities shall "
                            "protect cultural resources."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="nez-perce-clearwater-nfs",
                plan_version="2025",
                chunks_path=chunks_path,
            )

            self.assertTrue(result.summary["passed"])
            components = load_forest_plan_component_inventory(
                result.inventory_path,
                forest_unit_id="nez-perce-clearwater-nfs",
            )
            component_ids = {component["component_id"] for component in components}
            self.assertIn(f"{source_record_id}-FW-DC-ED-01", component_ids)
            self.assertIn(f"{source_record_id}-FW-STD-ED-02", component_ids)
            self.assertEqual(len(components), 2)

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

    def test_build_suppresses_tabular_max_standard_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            source_record_id = "R1PLAN-idaho-panhandle-nfs-02"
            chunks_path = _write_chunks(
                output_dir=output_dir,
                source_set_id=source_set_id,
                chunks=[
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id=source_record_id,
                        text=(
                            "2015 Idaho Panhandle Land Management Plan PDF\n"
                            "Standard (max) 2009 Status Selected Standard (min.) 1-Cedar 2 14 15."
                        ),
                    ),
                ],
            )

            result = build_forest_plan_component_inventory(
                output_dir=output_dir,
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                forest_unit_id="idaho-panhandle-nfs",
                plan_version="2015",
                chunks_path=chunks_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["component_count"], 0)
            coverage = json.loads(result.coverage_path.read_text(encoding="utf-8"))
            self.assertEqual(coverage["duplicate_component_ids"], [])
            self.assertEqual(coverage["duplicate_standard_ids"], [])
            self.assertEqual(coverage["inventory_quality_issue_count"], 1)
            self.assertEqual(
                coverage["inventory_quality_issues"][0]["issue_type"],
                "tabular_component_label",
            )
