from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability import build_authority_universe_snapshot
from usfs_r1_ea_sources.cli import main


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
                [["no road construction"]],
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

    def test_cli_writes_authority_universe_snapshot(self) -> None:
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

            exit_code = main(
                [
                    "applicability-authority-universe",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    "cli-unit",
                    "--source-set-id",
                    source_set_id,
                    "--base-rule-pack",
                    str(rule_pack_path),
                    "--forest-plan-component-inventory-path",
                    str(component_inventory_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            snapshot_path = (
                output_dir
                / "reviews"
                / "cli-unit"
                / "applicability"
                / "authority_universe_snapshot.json"
            )
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertTrue(snapshot["validation"]["passed"])
            self.assertEqual(snapshot["summary"]["candidate_authority_count"], 5)


def _write_catalog(output_dir: Path, source_set_id: str, records: list[dict]) -> None:
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    _write_json(catalog_dir / "source_set_manifest.json", {"source_set_id": source_set_id})
    _write_jsonl(catalog_dir / "source_catalog.jsonl", records)


def _catalog_record(
    source_set_id: str,
    source_record_id: str,
    document_role: str,
    authority_category: str,
) -> dict:
    return {
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "title": f"{source_record_id} title",
        "citation_label": f"{source_record_id} | title | artifact",
        "document_role": document_role,
        "authority_level": authority_category,
        "issuer": "Unit Test",
        "scope": "Baseline",
        "layer": "authority",
        "document_type": "source",
        "unit_or_overlay": None,
        "applies_to": "EA",
        "trigger": None,
        "review_topics": [authority_category],
        "currentness_notes": "current for unit test",
        "source_status": "downloaded",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"artifacts/raw/{source_record_id}.txt",
        "artifact_byte_size": 128,
        "content_type": "text/plain",
        "retrieved_at": "2026-05-03T00:00:00Z",
    }


def _write_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "title": "Unit NEPA EA Rule Pack",
        "rules": [
            _rule(
                rule_id="baseline_authority",
                source_record_id="R1EA-BASE",
                authority_category="law",
                document_role="law",
                applicability_mode="baseline",
            ),
            _rule(
                rule_id="conditional_authority",
                source_record_id="R1EA-COND",
                authority_category="regulation",
                document_role="regulation",
                applicability_mode="conditional",
                applies_if_package_terms=["road construction"],
                does_not_apply_if_package_terms=["no road construction"],
                package_section_terms=["transportation"],
            ),
            _rule(
                rule_id="custer_gallatin_lmp_2022",
                source_record_id="R1PLAN-custer-gallatin-nf-02",
                authority_category="forest_plan",
                document_role="forest_plan",
                applicability_mode="baseline",
            ),
        ],
    }
    path = directory / "rule-pack.json"
    _write_json(path, rule_pack)
    return path


def _rule(
    *,
    rule_id: str,
    source_record_id: str,
    authority_category: str,
    document_role: str,
    applicability_mode: str,
    applies_if_package_terms: list[str] | None = None,
    does_not_apply_if_package_terms: list[str] | None = None,
    package_section_terms: list[str] | None = None,
) -> dict:
    rule = {
        "id": rule_id,
        "title": f"{rule_id} title",
        "authority_category": authority_category,
        "authority_source_record_id": source_record_id,
        "authority_document_role": document_role,
        "applicability_mode": applicability_mode,
        "question": f"Does the package address {rule_id}?",
        "requirement": f"The package should address {rule_id}.",
        "package_query": f"{rule_id} package evidence",
        "package_terms": [rule_id.replace("_", " ")],
        "source_query": f"{rule_id} source evidence",
        "source_filters": {
            "document_role": document_role,
            "source_record_id": source_record_id,
        },
        "severity": "medium",
    }
    if applies_if_package_terms:
        rule["applies_if_package_terms"] = applies_if_package_terms
    if does_not_apply_if_package_terms:
        rule["does_not_apply_if_package_terms"] = does_not_apply_if_package_terms
    if package_section_terms:
        rule["package_section_terms"] = package_section_terms
    return rule


def _write_rule_claim_links(output_dir: Path, source_set_id: str, rule_pack_path: Path) -> None:
    rule_pack = json.loads(rule_pack_path.read_text(encoding="utf-8"))
    links_dir = (
        output_dir
        / "derived"
        / source_set_id
        / "rule_claim_links"
        / rule_pack["rule_pack_id"]
        / rule_pack["version"]
    )
    links = [
        {
            "link_id": f"link:{rule['id']}",
            "rule_id": rule["id"],
            "source_set_id": source_set_id,
        }
        for rule in rule_pack["rules"]
    ]
    _write_jsonl(links_dir / "rule_claim_links.jsonl", links)
    _write_jsonl(links_dir / "rule_claim_link_gaps.jsonl", [])


def _write_component_inventory(output_dir: Path, source_set_id: str) -> Path:
    inventory_path = (
        output_dir
        / "derived"
        / source_set_id
        / "forest_plan_components"
        / "component_inventory.json"
    )
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "unit-inventory",
        "source_set_id": source_set_id,
        "forest_unit_id": "custer-gallatin-nf",
        "plan_version": "2022",
        "components": [
            _component(source_set_id, "standard", "STD-01"),
            _component(source_set_id, "guideline", "GDL-01"),
        ],
    }
    _write_json(inventory_path, inventory)
    return inventory_path


def _component(source_set_id: str, component_type: str, component_code: str) -> dict:
    component_id = f"R1PLAN-custer-gallatin-nf-02-{component_code}"
    return {
        "source_set_id": source_set_id,
        "source_record_id": "R1PLAN-custer-gallatin-nf-02",
        "forest_unit_id": "custer-gallatin-nf",
        "plan_version": "2022",
        "component_id": component_id,
        "component_type": component_type,
        "section_id": "section",
        "section_heading": "Plan Components",
        "artifact_sha256": hashlib.sha256(component_id.encode("utf-8")).hexdigest(),
        "source_chunk_ids": [f"chunk:{component_id}"],
        "package_evidence_terms": ["road"],
        "resource_topics": ["access"],
        "activity_tags": ["construction"],
        "geographic_area_ids": [],
        "management_area_ids": ["mgmt-crazy-mountains-bca"],
        "overlay_ids": [],
    }


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check: {name}")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
