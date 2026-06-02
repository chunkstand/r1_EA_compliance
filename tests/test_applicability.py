from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability import build_authority_universe_snapshot
from tests.support.applicability_authority_universe_fixtures import (
    _catalog_record,
    _check,
    _write_authority_family_templates,
    _write_catalog,
    _write_component_inventory,
    _write_extraction_manifest,
    _write_json,
    _write_region1_component_inventory,
    _write_rule_claim_links,
    _write_rule_pack,
)


class AuthorityUniverseSnapshotTests(unittest.TestCase):
    def test_snapshot_includes_baseline_conditional_and_forest_plan_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="applicability-unit",
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertTrue(result.snapshot_path.exists())
            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["rule_template_candidate_count"], 3)
            self.assertEqual(result.summary["forest_plan_component_candidate_count"], 2)
            self.assertEqual(
                result.summary["rule_applicability_mode_counts"],
                {"baseline": 2, "conditional": 1},
            )

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["schema_version"], "authority-universe-snapshot-v0")
            self.assertEqual(
                snapshot["artifact_paths"]["forest_plan_component_inventory_path"],
                str(component_inventory_path),
            )
            self.assertEqual(snapshot["forest_plan_component_inventory_id"], "unit-inventory")
            self.assertIn("custer-gallatin-nf", snapshot["forest_plan_profile_ids"])
            self.assertFalse(
                (result.applicability_dir / "applicability_decisions.jsonl").exists()
            )

            candidates = {
                candidate["candidate_authority_id"]: candidate
                for candidate in snapshot["candidate_authorities"]
            }
            conditional = candidates[
                "rule-template:unit-nepa-ea:0.1.0:conditional_authority"
            ]
            self.assertEqual(
                conditional["rule_template"]["applicability_mode"],
                "conditional",
            )
            self.assertEqual(
                conditional["deterministic_applicability_test_contract"][
                    "positive_package_terms"
                ],
                ["road construction"],
            )
            self.assertIn("resource_topic", conditional["required_package_fact_types"])
            self.assertEqual(conditional["positive_trigger_groups"], [["road construction"]])
            self.assertEqual(
                conditional["negative_trigger_groups"],
                [["no road construction"], ["no new road"]],
            )
            self.assertEqual(
                conditional["source_role_filters"]["source_record_ids"],
                ["R1EA-COND"],
            )
            self.assertEqual(
                conditional["package_section_filters"]["package_section_terms"],
                ["transportation"],
            )
            self.assertTrue(
                conditional["required_source_evidence"]["requires_source_claim_linkage"]
            )
            self.assertIn(
                "metadata_filter",
                conditional["retrieval_contract"]["required_query_types"],
            )
            self.assertTrue(
                conditional["retrieval_contract"][
                    "requires_selected_and_rejected_results"
                ]
            )
            self.assertIn(
                "dependency",
                conditional["graph_expansion_contract"]["relationship_types"],
            )
            self.assertIn("dependency_rule_ids", conditional["dependency_contract"])
            self.assertEqual(
                {
                    requirement["coverage_class"]
                    for requirement in conditional["search_coverage_requirements"]
                },
                {"positive_trigger_miss", "explicit_negative_trigger"},
            )
            component_candidates = [
                candidate
                for candidate in snapshot["candidate_authorities"]
                if candidate["candidate_authority_type"] == "forest_plan_component"
            ]
            self.assertEqual(len(component_candidates), 2)
            self.assertTrue(
                all(
                    candidate["forest_plan"]["profile_data_source"]
                    for candidate in component_candidates
                )
            )
            self.assertEqual(
                {
                    candidate["forest_plan"]["active_plan_source_record_id"]
                    for candidate in component_candidates
                },
                {"R1PLAN-custer-gallatin-nf-02"},
            )
            self.assertTrue(
                all(
                    "management_area" in candidate["required_package_fact_types"]
                    for candidate in component_candidates
                )
            )
            self.assertTrue(
                all(
                    candidate["search_coverage_requirements"]
                    for candidate in component_candidates
                )
            )
            pre_review_check = _check(
                snapshot["validation"],
                "candidates_have_pre_review_contracts",
            )
            self.assertTrue(pre_review_check["passed"])
            self.assertEqual(pre_review_check["details"]["failure_count"], 0)
            self.assertEqual(
                snapshot["summary"]["candidate_contract_counts"][
                    "with_search_coverage_requirements"
                ],
                5,
            )

    def test_snapshot_accepts_catalog_override_for_noncanonical_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            merged_catalog_root = root / "merged_catalog_root"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                merged_catalog_root,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="override-unit",
                source_set_id=source_set_id,
                source_catalog_path=merged_catalog_root / "catalog" / "source_catalog.jsonl",
                source_set_manifest_path=merged_catalog_root
                / "catalog"
                / "source_set_manifest.json",
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertTrue(result.snapshot_path.exists())
            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["candidate_authority_count"], 5)

    def test_snapshot_falls_back_to_extraction_manifest_for_legacy_source_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-legacy"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                "source-set-current",
                [_catalog_record("source-set-current", "R1EA-OTHER", "law", "law")],
            )
            legacy_records = [
                _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                _catalog_record(
                    source_set_id,
                    "R1PLAN-custer-gallatin-nf-02",
                    "forest_plan",
                    "forest_plan",
                ),
            ]
            _write_extraction_manifest(output_dir, source_set_id, legacy_records)
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="legacy-source-set-unit",
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["candidate_authority_count"], 5)

    def test_snapshot_filters_region_wide_component_inventory_to_review_forest(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-flathead-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_region1_component_inventory(
                output_dir,
                source_set_id,
            )

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="region1-component-unit",
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["forest_plan_component_candidate_count"], 1)

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            component_candidates = [
                candidate
                for candidate in snapshot["candidate_authorities"]
                if candidate["candidate_authority_type"] == "forest_plan_component"
            ]
            self.assertEqual(len(component_candidates), 1)
            self.assertEqual(
                component_candidates[0]["forest_plan"]["forest_unit_id"],
                "custer-gallatin-nf",
            )
            self.assertEqual(
                component_candidates[0]["forest_plan"]["plan_version"],
                "2022",
            )
            component_check = _check(
                snapshot["validation"],
                "forest_plan_component_candidates_use_profile_inventory",
            )
            self.assertTrue(component_check["passed"])
            self.assertEqual(
                component_check["details"]["component_candidate_count"],
                1,
            )
            self.assertTrue(component_check["details"]["component_inventory_present"])
            self.assertIsNone(component_check["details"]["inventory_forest_unit_id"])
            self.assertEqual(
                component_check["details"]["selected_component_forest_unit_ids"],
                ["custer-gallatin-nf"],
            )

    def test_snapshot_scopes_region_wide_inventory_to_explicit_forest_unit(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-flathead-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_region1_component_inventory(
                output_dir,
                source_set_id,
            )

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="flathead-component-unit",
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
                forest_unit_id="flathead-nf",
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["rule_template_candidate_count"], 2)
            self.assertEqual(result.summary["forest_plan_component_candidate_count"], 1)

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["forest_unit_id"], "flathead-nf")
            self.assertEqual(
                snapshot["review_scope"]["removed_forest_plan_rule_ids"],
                ["custer_gallatin_lmp_2022"],
            )
            component_candidates = [
                candidate
                for candidate in snapshot["candidate_authorities"]
                if candidate["candidate_authority_type"] == "forest_plan_component"
            ]
            self.assertEqual(len(component_candidates), 1)
            self.assertEqual(
                component_candidates[0]["forest_plan"]["forest_unit_id"],
                "flathead-nf",
            )
            self.assertNotIn(
                "R1PLAN-custer-gallatin-nf-02",
                {
                    source_record_id
                    for candidate in snapshot["candidate_authorities"]
                    for source_record_id in candidate["source_record_ids"]
                },
            )

    def test_snapshot_scopes_region_wide_inventory_from_resolved_review_context(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            review_id = "flathead-context-unit"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-flathead-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_region1_component_inventory(
                output_dir,
                source_set_id,
            )
            review_dir = output_dir / "reviews" / review_id
            review_dir.mkdir(parents=True, exist_ok=True)
            _write_json(
                review_dir / "forest_plan_context_summary.json",
                {
                    "schema_version": "forest-plan-context-summary-v0",
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "scope_status": "flathead_nf",
                    "title_page_project_location": {
                        "forest_unit_name": "Flathead National Forest"
                    },
                    "component_evaluation": {
                        "component_count": 1,
                        "component_inventory_path": str(component_inventory_path),
                    },
                },
            )

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["forest_unit_id"], "flathead-nf")
            self.assertEqual(result.summary["rule_template_candidate_count"], 2)
            self.assertEqual(result.summary["forest_plan_component_candidate_count"], 1)

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["forest_unit_id"], "flathead-nf")
            self.assertEqual(
                snapshot["review_scope"]["removed_forest_plan_rule_ids"],
                ["custer_gallatin_lmp_2022"],
            )
            component_candidates = [
                candidate
                for candidate in snapshot["candidate_authorities"]
                if candidate["candidate_authority_type"] == "forest_plan_component"
            ]
            self.assertEqual(len(component_candidates), 1)
            self.assertEqual(
                component_candidates[0]["forest_plan"]["forest_unit_id"],
                "flathead-nf",
            )

    def test_snapshot_includes_authority_family_rule_template_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            template_path = _write_authority_family_templates(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(source_set_id, "R1EA-FAMILY", "law", "law"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            _write_rule_claim_links(output_dir, source_set_id, rule_pack_path)
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="family-template-unit",
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=template_path,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["rule_template_candidate_count"], 3)
            self.assertEqual(
                result.summary["authority_family_rule_template_candidate_count"],
                1,
            )
            self.assertEqual(result.summary["candidate_authority_count"], 6)
            self.assertEqual(
                result.summary["authority_family_template_applicability_mode_counts"],
                {"conditional": 1},
            )

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            family_candidates = [
                candidate
                for candidate in snapshot["candidate_authorities"]
                if candidate["candidate_authority_type"]
                == "authority_family_rule_template"
            ]
            self.assertEqual(len(family_candidates), 1)
            candidate = family_candidates[0]
            self.assertEqual(candidate["authority_family_id"], "clean_water_unit")
            self.assertEqual(
                candidate["rule_template"]["rule_id"],
                "clean_water_unit_authority_template",
            )
            self.assertEqual(candidate["positive_trigger_groups"], [["wetlands"]])
            self.assertEqual(candidate["negative_trigger_groups"], [["no wetlands"]])
            self.assertFalse(
                candidate["required_source_evidence"][
                    "requires_source_claim_linkage"
                ]
            )
            self.assertTrue(candidate["source_evidence_availability"]["available"])
            self.assertEqual(
                candidate["retrieval_contract"]["contract_type"],
                "authority_family_rule_template_retrieval",
            )
            self.assertEqual(
                candidate["deterministic_applicability_test_contract"][
                    "candidate_authority_type"
                ],
                "authority_family_rule_template",
            )
            template_check = _check(
                snapshot["validation"],
                "authority_family_template_candidates_cover_config",
            )
            self.assertTrue(template_check["passed"])
            self.assertEqual(
                template_check["details"]["actual_template_candidate_count"],
                1,
            )

    def test_snapshot_validation_fails_when_rule_claim_linkage_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-test"
            rule_pack_path = _write_rule_pack(root)
            _write_catalog(
                output_dir,
                source_set_id,
                [
                    _catalog_record(source_set_id, "R1EA-BASE", "law", "law"),
                    _catalog_record(source_set_id, "R1EA-COND", "regulation", "regulation"),
                    _catalog_record(
                        source_set_id,
                        "R1PLAN-custer-gallatin-nf-02",
                        "forest_plan",
                        "forest_plan",
                    ),
                ],
            )
            component_inventory_path = _write_component_inventory(output_dir, source_set_id)

            result = build_authority_universe_snapshot(
                output_dir=output_dir,
                review_id="missing-links-unit",
                source_set_id=source_set_id,
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            self.assertFalse(result.summary["validation_passed"])
            linkage_check = _check(
                snapshot["validation"],
                "rule_template_candidates_have_source_claim_linkage",
            )
            self.assertFalse(linkage_check["passed"])
            self.assertEqual(linkage_check["details"]["failure_count"], 3)
