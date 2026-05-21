from __future__ import annotations

from pathlib import Path
import hashlib
import json

from tests.support.compliance_component_fixtures import (
    _build_beaverhead_compliance_source_library,
)
from tests.support.forest_plan_resolver_common import (
    _chunk,
    _write_catalog_sqlite,
    _write_chunks,
    _write_extraction_accuracy_audit,
    _write_extraction_diagnostics,
)
from usfs_r1_ea_sources.retrieval import build_retrieval_index


_FLATHEAD_PLAN_TEXT = (
    "The 2018 Flathead National Forest Land Management Plan includes the Hungry Horse Geographic "
    "Area and the Jewel Basin Hiking Area. Jewel Basin Recommended Wilderness Area direction "
    "and Inventoried Roadless Area direction apply where mapped. Standard FW-STD-WTR-01 New "
    "stream diversions and associated ditches shall have screens placed on them to prevent "
    "capture of fish and other aquatic organisms. Suitability MA1b-SUIT-07 The Jewel Basin "
    "hiking area is not suitable for motorized use, mechanized transport, and stock use."
)

_FLATHEAD_TEST_SOURCES = (
    (
        "R1PLAN-flathead-nf-01",
        "Flathead planning page",
        (
            "The Flathead planning page lists the forest plan, FEIS volumes, record of decision, "
            "monitoring program, biennial monitoring evaluation report, administrative change, "
            "biological assessment, and biological opinions."
        ),
    ),
    (
        "FINAL-FLAT-001",
        "2018 Flathead National Forest Land Management Plan PDF",
        _FLATHEAD_PLAN_TEXT,
    ),
    (
        "R1PLAN-flathead-nf-03",
        "Flathead Record of Decision PDF",
        (
            "The record of decision identifies the selected alternative, plan approval, Hungry "
            "Horse-Glacier View Ranger District, Spotted Bear Ranger District, recommended "
            "wilderness areas, and FEIS context."
        ),
    ),
    (
        "R1PLAN-flathead-nf-04",
        "Flathead FEIS Volume 1 PDF",
        (
            "The final environmental impact statement discusses alternatives, effects, plan "
            "consistency, recommended wilderness, inventoried roadless areas, and wild and scenic "
            "rivers."
        ),
    ),
    (
        "R1PLAN-flathead-nf-05",
        "Flathead FEIS Appendices PDF",
        (
            "The final environmental impact statement appendices provide supporting analysis, "
            "methods, and glossary context for Flathead plan interpretation."
        ),
    ),
    (
        "R1PLAN-flathead-nf-06",
        "Flathead Biological Assessment PDF",
        (
            "The biological assessment analyzes Canada lynx critical habitat, grizzly bear, and "
            "the Northern Continental Divide Ecosystem."
        ),
    ),
    (
        "R1PLAN-flathead-nf-07",
        "Flathead Biological Opinion Bull Trout PDF",
        (
            "The biological opinion addresses bull trout incidental take and terms and "
            "conditions."
        ),
    ),
    (
        "R1PLAN-flathead-nf-08",
        "Flathead Monitoring Program PDF",
        (
            "The monitoring program includes monitoring questions and indicators under the 2012 "
            "planning rule."
        ),
    ),
    (
        "R1PLAN-flathead-nf-09",
        "Flathead Biennial Monitoring Evaluation Report PDF",
        (
            "The Biennial Monitoring Evaluation Report for the Flathead National Forest reviews "
            "visitor use and monitoring questions."
        ),
    ),
    (
        "R1PLAN-flathead-nf-10",
        "Flathead Administrative Change PDF",
        (
            "The Administrative Change updates Jewel Basin, Limestone-Dean Ridge, and "
            "Tuchuck-Whale Recommended Wilderness Areas."
        ),
    ),
    (
        "R1PLAN-flathead-nf-12",
        "Flathead FEIS Volume 2 PDF",
        (
            "The final environmental impact statement volume 2 discusses inventoried roadless "
            "areas, designated wilderness, eligible wild and scenic rivers, and recommended "
            "wilderness areas."
        ),
    ),
    (
        "R1PLAN-flathead-nf-16",
        "Flathead Biological Opinion Grizzly Bear PDF",
        (
            "The biological opinion addresses grizzly bear habitat in the Northern Continental "
            "Divide Ecosystem primary conservation area."
        ),
    ),
)

_FLATHEAD_TEST_REVIEW_TOPICS = {
    "R1PLAN-flathead-nf-01": "Check current Flathead plan document set",
    "FINAL-FLAT-001": "Extract Flathead plan components by geography and overlay",
    "R1PLAN-flathead-nf-03": "Check selected alternative and plan approval",
    "R1PLAN-flathead-nf-04": "Use FEIS context for alternatives and designated areas",
    "R1PLAN-flathead-nf-05": "Use FEIS appendices for supporting analysis context",
    "R1PLAN-flathead-nf-06": "Check plan-level species effects analysis",
    "R1PLAN-flathead-nf-07": "Check bull trout ESA consultation terms",
    "R1PLAN-flathead-nf-08": "Check monitoring program questions and indicators",
    "R1PLAN-flathead-nf-09": "Check biennial monitoring currentness support",
    "R1PLAN-flathead-nf-10": "Check administrative change currentness support",
    "R1PLAN-flathead-nf-12": "Use FEIS volume 2 for overlays and designated areas",
    "R1PLAN-flathead-nf-16": "Check grizzly bear ESA consultation terms",
}

_FLATHEAD_TEST_SUPPORT_DOCUMENT_ROLES = {
    "R1PLAN-flathead-nf-01": "planning_page",
    "FINAL-FLAT-001": "primary_land_management_plan",
    "R1PLAN-flathead-nf-03": "record_of_decision",
    "R1PLAN-flathead-nf-04": "final_environmental_impact_statement_volume_1_part_1",
    "R1PLAN-flathead-nf-05": "final_environmental_impact_statement_appendices",
    "R1PLAN-flathead-nf-06": "biological_assessment",
    "R1PLAN-flathead-nf-07": "biological_opinion_1",
    "R1PLAN-flathead-nf-08": "forest_plan_monitoring_program",
    "R1PLAN-flathead-nf-09": "latest_biennial_monitoring_evaluation_report",
    "R1PLAN-flathead-nf-10": "administrative_change",
    "R1PLAN-flathead-nf-12": "final_environmental_impact_statement_volume_2",
    "R1PLAN-flathead-nf-16": "biological_opinion_2",
}


def _build_flathead_source_library(
    output_dir: Path,
    *,
    document_role_overrides: dict[str, str] | None = None,
    support_document_role_overrides: dict[str, str] | None = None,
) -> str:
    source_set_id = "source-set-flathead-test"
    document_role_overrides = document_role_overrides or {}
    support_document_role_overrides = support_document_role_overrides or {}
    chunks = [
        _chunk(
            source_set_id=source_set_id,
            source_record_id=source_record_id,
            title=title,
            document_role=document_role_overrides.get(source_record_id, "forest_plan"),
            support_document_role=support_document_role_overrides.get(
                source_record_id,
                _FLATHEAD_TEST_SUPPORT_DOCUMENT_ROLES[source_record_id],
            ),
            authority_level="forest",
            citation_label=f"{source_record_id} | {title} | artifact abc123",
            text=text,
        )
        for source_record_id, title, text in _FLATHEAD_TEST_SOURCES
    ]
    source_record_ids = [chunk["source_record_id"] for chunk in chunks]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids,
    )
    _write_chunks(
        output_dir,
        source_set_id,
        chunks,
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [topic]
            for source_record_id, topic in _FLATHEAD_TEST_REVIEW_TOPICS.items()
            if source_record_id in source_record_ids
        },
    )
    _write_extraction_accuracy_audit(
        output_dir,
        source_set_id,
        admitted_source_record_ids=source_record_ids,
    )
    build_retrieval_index(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    _write_flathead_component_inventory(
        output_dir / "derived" / source_set_id / "forest_plan_components",
        source_set_id=source_set_id,
    )
    return source_set_id


def _build_beaverhead_source_library(output_dir: Path) -> str:
    source_set_id = "source-set-beaverhead-test"
    _build_beaverhead_compliance_source_library(output_dir, source_set_id)
    return source_set_id


def _write_flathead_component_inventory(path: Path, *, source_set_id: str) -> Path:
    inventory_path = path / "component_inventory.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    source_record_id = "FINAL-FLAT-001"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    content_sha256 = hashlib.sha256(_FLATHEAD_PLAN_TEXT.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
    base = {
        "forest_unit_id": "flathead-nf",
        "plan_version": "2018",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "section_id": "jewel-basin-hiking-area-components",
        "section_heading": "Jewel Basin Hiking Area Components",
        "page": None,
        "citation_label": "FINAL-FLAT-001 | test plan | artifact abc123",
        "geographic_area_ids": ["geo-hungry-horse"],
        "management_area_ids": ["mgmt-jewel-basin-hiking-area"],
        "overlay_ids": [],
        "resource_topics": ["recreation access", "hydrology"],
        "source_chunk_ids": source_chunk_ids,
        "artifact_sha256": artifact_sha256,
        "content_sha256": content_sha256,
    }
    provenance = {
        "entity": {
            "type": "forest_plan_component",
            "source_record_id": source_record_id,
            "source_chunk_ids": source_chunk_ids,
            "artifact_sha256": artifact_sha256,
            "content_sha256": content_sha256,
        },
        "activity": {
            "type": "component_inventory_fixture",
            "created_at": "2026-05-11T00:00:00Z",
        },
        "agent": {
            "type": "deterministic_test_fixture",
            "name": "tests/support/forest_plan_resolver_profile_fixtures.py",
            "version": "forest-plan-component-inventory-v0",
        },
    }
    components = [
        {
            **base,
            "component_id": "flathead-test-fw-std-wtr-01",
            "component_type": "standard",
            "component_text": (
                "Standard (FW-STD-WTR) 01 New stream diversions and associated ditches "
                "shall have screens placed on them to prevent capture of fish and other "
                "aquatic organisms."
            ),
            "activity_tags": ["stream diversions", "screens", "aquatic organisms"],
            "package_evidence_terms": [
                "new stream diversions",
                "screens placed on them",
                "aquatic organisms",
            ],
            "provenance": provenance,
        },
        {
            **base,
            "component_id": "flathead-test-ma1b-suit-07",
            "component_type": "suitability",
            "component_text": (
                "Suitability (MA1b-SUIT) 07 The Jewel Basin hiking area is not suitable "
                "for motorized use, mechanized transport, and stock use."
            ),
            "activity_tags": ["motorized use", "mechanized transport", "stock use"],
            "package_evidence_terms": [
                "motorized use",
                "mechanized transport",
                "stock use",
            ],
            "provenance": provenance,
        },
    ]
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "flathead-test-components-v0",
        "forest_unit_id": "flathead-nf",
        "plan_version": "2018",
        "source_set_id": source_set_id,
        "components": components,
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    if path.name == "forest_plan_components":
        coverage = {
            "schema_version": "forest-plan-component-inventory-build-coverage-v0",
            "created_at": "2026-05-11T00:00:00Z",
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "chunks_path": f"source_library/derived/{source_set_id}/chunks/chunks.jsonl",
            "selected_chunk_count": 1,
            "detected_component_count": len(components),
            "detected_standard_count": 1,
            "built_component_count": len(components),
            "built_standard_count": 1,
            "missing_component_ids": [],
            "missing_standard_ids": [],
            "duplicate_component_ids": [],
            "duplicate_standard_ids": [],
            "validation_errors": [],
            "detected_component_labels": [
                {
                    "component_id": component["component_id"],
                    "component_type": component["component_type"],
                    "label": component["component_type"],
                    "code": component["component_id"],
                    "number": "01",
                    "source_record_id": source_record_id,
                    "chunk_id": source_chunk_ids[0],
                    "section_heading": base["section_heading"],
                }
                for component in components
            ],
            "detected_standard_labels": [
                {
                    "component_id": "flathead-test-fw-std-wtr-01",
                    "component_type": "standard",
                    "label": "Standard",
                    "code": "FW-STD-WTR",
                    "number": "01",
                    "source_record_id": source_record_id,
                    "chunk_id": source_chunk_ids[0],
                    "section_heading": base["section_heading"],
                }
            ],
            "passed": True,
            "checks": [
                {"name": "selected_forest_plan_chunks_present", "passed": True, "details": {}},
                {"name": "labeled_components_detected", "passed": True, "details": {}},
                {"name": "standard_components_detected", "passed": True, "details": {}},
                {"name": "all_detected_components_built", "passed": True, "details": {}},
                {"name": "all_detected_standards_built", "passed": True, "details": {}},
                {"name": "built_component_ids_are_unique", "passed": True, "details": {}},
                {"name": "detected_standard_labels_are_unique", "passed": True, "details": {}},
                {"name": "built_component_records_validate", "passed": True, "details": {}},
            ],
        }
        (path / "component_inventory_build_coverage.json").write_text(
            json.dumps(coverage, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return inventory_path
