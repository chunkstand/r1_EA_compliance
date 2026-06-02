from __future__ import annotations

from pathlib import Path
import hashlib
import json

from tests.support.forest_plan_resolver_common import (
    _chunk,
    _write_catalog_sqlite,
    _write_chunks,
    _write_extraction_diagnostics,
)
from usfs_r1_ea_sources.retrieval import build_retrieval_index


_CUSTER_PLAN_TEXT = (
    "The Bridger, Bangtail, and Crazy Mountains Geographic Area includes "
    "several plan land allocations. Plan Components-Crazy Mountains "
    "Backcountry Area (CMBCA) contain direction for backcountry use. "
    "The Hyalite Recreation Emphasis Area (HREA) has recreation setting "
    "direction. Inventoried Roadless Area direction applies where mapped. "
    "Desired Conditions (BC-DC-CMBCA) 01 Quiet, nonmotorized recreation "
    "opportunities predominate. Standards (BC-STD-CMBCA) 01 New permanent "
    "or temporary roads shall not be allowed. Suitability (BC-SUIT-CMBCA) "
    "01 The backcountry area is not suitable for motorized transport. The "
    "backcountry area is not suitable for mechanized transport, except use "
    "of game carts."
)

_CUSTER_TEST_SOURCES = (
    (
        "R1PLAN-custer-gallatin-nf-01",
        "Custer Gallatin land management plan page",
        (
            "The Custer Gallatin land management plan page lists the current plan, "
            "record of decision, final environmental impact statement volumes, "
            "biological assessment, and biological opinion."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-02",
        "2022 Custer Gallatin Land Management Plan PDF",
        _CUSTER_PLAN_TEXT,
    ),
    (
        "R1PLAN-custer-gallatin-nf-03",
        "Custer Gallatin Land Management Plan Record of Decision PDF",
        (
            "The record of decision identifies the selected alternative, explains "
            "the decision basis, records objection resolution, and documents plan approval."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-04",
        "Custer Gallatin Land Management Plan FEIS Volume 1 PDF",
        (
            "The final environmental impact statement volume 1 describes purpose and need, "
            "alternatives, affected environment, environmental consequences, cumulative "
            "effects, and plan consistency context."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-05",
        "Custer Gallatin Land Management Plan FEIS Volume 2 PDF",
        (
            "The final environmental impact statement volume 2 discusses designated areas, "
            "plan allocations, inventoried roadless areas, backcountry areas, recreation "
            "emphasis areas, and resource effects."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-06",
        "Custer Gallatin LMP Biological Assessment PDF",
        (
            "The biological assessment analyzes threatened, endangered, proposed, and "
            "candidate species, critical habitat, conservation measures, action area, "
            "and species effects."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-07",
        "Custer Gallatin LMP Biological Opinion PDF",
        (
            "The biological opinion documents Endangered Species Act section 7 consultation, "
            "effects determinations, incidental take, reinitiation, and terms and conditions."
        ),
    ),
)

_CUSTER_TEST_REVIEW_TOPICS = {
    "R1PLAN-custer-gallatin-nf-01": "Check current Custer Gallatin plan document set",
    "R1PLAN-custer-gallatin-nf-02": "Extract plan components by resource and geography",
    "R1PLAN-custer-gallatin-nf-03": "Check selected alternative and plan approval",
    "R1PLAN-custer-gallatin-nf-04": "Use FEIS Volume 1 for alternatives and effects context",
    "R1PLAN-custer-gallatin-nf-05": "Use FEIS Volume 2 for designated areas and allocations",
    "R1PLAN-custer-gallatin-nf-06": "Check plan-level species effects analysis",
    "R1PLAN-custer-gallatin-nf-07": "Check plan-level ESA consultation terms",
}

_CUSTER_TEST_SUPPORT_DOCUMENT_ROLES = {
    "R1PLAN-custer-gallatin-nf-01": "plan_document_set_page",
    "R1PLAN-custer-gallatin-nf-02": "primary_land_management_plan",
    "R1PLAN-custer-gallatin-nf-03": "record_of_decision",
    "R1PLAN-custer-gallatin-nf-04": "final_environmental_impact_statement",
    "R1PLAN-custer-gallatin-nf-05": "final_environmental_impact_statement",
    "R1PLAN-custer-gallatin-nf-06": "biological_assessment",
    "R1PLAN-custer-gallatin-nf-07": "biological_opinion",
}

_WEAK_SOURCE_TEXT = (
    "This source chunk is intentionally generic for a negative resolver test. "
    "It has catalog provenance but no matching routed evidence terms."
)


def _build_custer_source_library(
    output_dir: Path,
    *,
    catalog_source_count: int | None = None,
    missing_source_ids: set[str] | None = None,
    weak_supporting_source_ids: set[str] | None = None,
    primary_plan_text: str | None = None,
) -> str:
    source_set_id = "source-set-test"
    missing_source_ids = missing_source_ids or set()
    weak_supporting_source_ids = weak_supporting_source_ids or set()
    chunks = [
        _chunk(
            source_set_id=source_set_id,
            source_record_id=source_record_id,
            title=title,
            document_role="forest_plan",
            support_document_role=_CUSTER_TEST_SUPPORT_DOCUMENT_ROLES[source_record_id],
            authority_level="forest",
            citation_label=f"{source_record_id} | {title} | artifact abc123",
            text=(
                _WEAK_SOURCE_TEXT
                if source_record_id in weak_supporting_source_ids
                else primary_plan_text
                if source_record_id == "R1PLAN-custer-gallatin-nf-02"
                and primary_plan_text is not None
                else text
            ),
        )
        for source_record_id, title, text in _CUSTER_TEST_SOURCES
        if source_record_id not in missing_source_ids
    ]
    source_record_ids = [chunk["source_record_id"] for chunk in chunks]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids,
        catalog_source_count=catalog_source_count,
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
            for source_record_id, topic in _CUSTER_TEST_REVIEW_TOPICS.items()
            if source_record_id in source_record_ids
        },
    )
    build_retrieval_index(
        output_dir=output_dir,
        source_set_id=source_set_id,
        allow_partial_extraction=(
            catalog_source_count is not None and catalog_source_count != len(source_record_ids)
        ),
    )
    if "R1PLAN-custer-gallatin-nf-02" in source_record_ids:
        _write_component_inventory(
            output_dir / "derived" / source_set_id / "forest_plan_components",
            source_set_id=source_set_id,
        )
    return source_set_id


def _write_component_inventory(path: Path, *, source_set_id: str) -> Path:
    inventory_path = path / "component_inventory.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    source_record_id = "R1PLAN-custer-gallatin-nf-02"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    content_sha256 = hashlib.sha256(_CUSTER_PLAN_TEXT.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
    base = {
        "forest_unit_id": "custer-gallatin-nf",
        "plan_version": "2022",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "section_id": "chapter-3-bridger-bangtail-crazy-cmbca",
        "section_heading": "Plan Components-Crazy Mountains Backcountry Area (CMBCA)",
        "page": None,
        "citation_label": "R1PLAN-custer-gallatin-nf-02 | test plan | artifact abc123",
        "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
        "management_area_ids": ["mgmt-crazy-mountains-bca"],
        "overlay_ids": [],
        "resource_topics": ["backcountry area"],
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
            "created_at": "2026-05-01T00:00:00Z",
        },
        "agent": {
            "type": "deterministic_test_fixture",
            "name": "tests/support/forest_plan_resolver_custer_fixtures.py",
            "version": "forest-plan-component-inventory-v0",
        },
    }
    components = [
        {
            **base,
            "component_id": "cg-test-cmbca-dc-01",
            "component_type": "desired_condition",
            "component_text": (
                "Desired Conditions (BC-DC-CMBCA) 01 Quiet, nonmotorized recreation "
                "opportunities predominate."
            ),
            "activity_tags": ["nonmotorized recreation"],
            "package_evidence_terms": ["nonmotorized recreation"],
            "provenance": provenance,
        },
        {
            **base,
            "component_id": "cg-test-cmbca-std-01",
            "component_type": "standard",
            "component_text": (
                "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads shall "
                "not be allowed."
            ),
            "activity_tags": ["new roads"],
            "package_evidence_terms": ["new permanent or temporary roads"],
            "provenance": provenance,
        },
        {
            **base,
            "component_id": "cg-test-cmbca-suit-01",
            "component_type": "suitability",
            "component_text": (
                "Suitability (BC-SUIT-CMBCA) 01 The backcountry area is not suitable "
                "for motorized transport. The backcountry area is not suitable for "
                "mechanized transport, except use of game carts."
            ),
            "activity_tags": ["motorized transport", "mechanized transport"],
            "package_evidence_terms": ["motorized transport", "mechanized transport"],
            "provenance": provenance,
        },
    ]
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "cg-test-components-v0",
        "forest_unit_id": "custer-gallatin-nf",
        "plan_version": "2022",
        "source_set_id": source_set_id,
        "components": components,
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    if path.name == "forest_plan_components":
        coverage = {
            "schema_version": "forest-plan-component-inventory-build-coverage-v0",
            "created_at": "2026-05-01T00:00:00Z",
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "chunks_path": "source_library/derived/source-set-test/chunks/chunks.jsonl",
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
                    "component_id": "cg-test-cmbca-std-01",
                    "component_type": "standard",
                    "label": "Standards",
                    "code": "BC-STD-CMBCA",
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
