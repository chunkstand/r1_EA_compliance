from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_authority_universe_builder import _load_authority_family_templates
from usfs_r1_ea_sources.applicability_authority_universe_builder import _load_source_catalog
from usfs_r1_ea_sources.applicability_authority_universe_builder import build_authority_universe_snapshot


class AuthorityUniverseBuilderTests(unittest.TestCase):
    def test_builder_reads_source_set_id_from_manifest_and_writes_snapshot(self) -> None:
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
                review_id="builder-unit",
                base_rule_pack_path=rule_pack_path,
                authority_family_templates_path=None,
                forest_plan_component_inventory_path=component_inventory_path,
            )

            self.assertEqual(result.review_id, "builder-unit")
            self.assertEqual(result.source_set_id, source_set_id)
            self.assertTrue(result.snapshot_path.exists())
            self.assertEqual(result.summary["candidate_authority_count"], 5)

            snapshot = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["review_id"], "builder-unit")
            self.assertEqual(snapshot["source_set_id"], source_set_id)
            self.assertEqual(
                snapshot["artifact_paths"]["source_set_manifest_path"],
                str(output_dir / "catalog" / "source_set_manifest.json"),
            )

    def test_load_source_catalog_falls_back_to_extraction_manifest_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            source_set_id = "source-set-legacy"
            _write_catalog(
                output_dir,
                "source-set-current",
                [_catalog_record("source-set-current", "R1EA-OTHER", "law", "law")],
            )
            _write_extraction_manifest(
                output_dir,
                source_set_id,
                [_catalog_record(source_set_id, "R1EA-BASE", "law", "law")],
            )

            catalog_records = _load_source_catalog(
                output_dir / "catalog" / "source_catalog.jsonl",
                source_set_id,
            )

            self.assertEqual(len(catalog_records), 1)
            self.assertEqual(catalog_records[0]["source_record_id"], "R1EA-BASE")
            self.assertEqual(catalog_records[0]["source_status"], "downloaded")
            self.assertEqual(catalog_records[0]["review_topics"], [])
            self.assertIsNone(catalog_records[0]["issuer"])

    def test_load_authority_family_templates_rejects_duplicate_rule_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "authority-family-templates.json"
            _write_json(
                path,
                {
                    "schema_version": "authority-family-rule-templates-v1",
                    "template_set_id": "dup-templates",
                    "version": "0.1.0",
                    "templates": [
                        _authority_family_template("dup-rule"),
                        _authority_family_template("dup-rule"),
                    ],
                },
            )

            with self.assertRaisesRegex(ValueError, "unique_rule_id"):
                _load_authority_family_templates(path)


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


def _write_extraction_manifest(output_dir: Path, source_set_id: str, records: list[dict]) -> None:
    manifest_path = (
        output_dir / "derived" / source_set_id / "diagnostics" / "extraction_manifest.jsonl"
    )
    manifest_records = []
    for record in records:
        manifest_records.append(
            {
                "source_set_id": source_set_id,
                "source_record_id": record["source_record_id"],
                "title": record["title"],
                "citation_label": record["citation_label"],
                "document_role": record["document_role"],
                "authority_level": record["authority_level"],
                "source_status": record["source_status"],
                "status": "extracted",
                "artifact_sha256": record["artifact_sha256"],
                "artifact_path": record["artifact_path"],
                "artifact_byte_size": record["artifact_byte_size"],
                "content_type": record["content_type"],
                "retrieved_at": record["retrieved_at"],
            }
        )
    _write_jsonl(manifest_path, manifest_records)


def _write_rule_pack(directory: Path) -> Path:
    path = directory / "rule-pack.json"
    _write_json(
        path,
        {
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
        },
    )
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
    _write_json(
        inventory_path,
        {
            "schema_version": "forest-plan-component-inventory-v0",
            "inventory_id": "unit-inventory",
            "source_set_id": source_set_id,
            "forest_unit_id": "custer-gallatin-nf",
            "plan_version": "2022",
            "components": [
                _component(source_set_id, "standard", "STD-01"),
                _component(source_set_id, "guideline", "GDL-01"),
            ],
        },
    )
    return inventory_path


def _component(
    source_set_id: str,
    component_type: str,
    component_code: str,
) -> dict:
    source_record_id = "R1PLAN-custer-gallatin-nf-02"
    component_id = f"{source_record_id}-{component_code}"
    return {
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
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


def _authority_family_template(rule_id: str) -> dict:
    return {
        "template_id": f"{rule_id}-template",
        "authority_family_id": "clean_water_unit",
        "rule_id": rule_id,
        "title": "Clean Water Unit applicability template",
        "authority_category": "law",
        "authority_document_role": "law",
        "authority_source_record_id": "R1EA-FAMILY",
        "source_record_ids": ["R1EA-FAMILY"],
        "supporting_source_record_ids": [],
        "excluded_source_record_ids": [],
        "applicability_mode": "conditional",
        "severity": "medium",
        "question": "Does the package trigger Clean Water Act review?",
        "requirement": "Evaluate source-backed Clean Water Act applicability.",
        "package_query": "wetlands",
        "package_terms": ["wetlands"],
        "package_fact_types": ["permit", "resource_topic"],
        "package_section_terms": ["water resources"],
        "applies_if_package_terms": ["wetlands"],
        "applies_if_package_term_groups": [["wetlands"]],
        "does_not_apply_if_package_terms": ["no wetlands"],
        "source_query": "Clean Water Act source",
        "source_filters": {
            "document_role": "law",
            "source_record_id": "R1EA-FAMILY",
        },
        "source_evidence_requirements": ["catalog-confirmed source"],
        "evidence_expectation": (
            "A supported decision requires source evidence and package wetlands evidence."
        ),
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
