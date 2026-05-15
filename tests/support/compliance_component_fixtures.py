from __future__ import annotations

from pathlib import Path
import hashlib
import json

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.forest_plan_components import build_forest_plan_component_inventory
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.compliance_review_fixtures import (
    _chunk,
    _write_catalog_sqlite,
    _write_chunks,
    _write_extraction_accuracy_audit,
    _write_extraction_diagnostics,
)


_CUSTER_PLAN_COMPONENT_TEXT = (
    "The 2022 Custer Gallatin Land Management Plan includes "
    "Plan Components-Crazy Mountains Backcountry Area (CMBCA). "
    "Standards (BC-STD-CMBCA) 01 New permanent or temporary roads shall not be allowed."
)

_BEAVERHEAD_PLAN_COMPONENT_TEXT = (
    "The 2009 Beaverhead-Deerlodge Forest Plan includes the Big Hole Landscape and the West Big "
    "Hole Management Area. Inventoried Roadless Area and recommended wilderness direction apply "
    "where mapped. "
    "West Big Hole Management Area Standards Standard 1: New permanent or temporary roads "
    "shall not be allowed."
)

_FLATHEAD_PLAN_COMPONENT_TEXT = (
    "The 2018 Flathead National Forest Land Management Plan includes the Hungry Horse Geographic "
    "Area and the Jewel Basin Hiking Area. Jewel Basin Recommended Wilderness Area direction "
    "and Inventoried Roadless Area direction apply where mapped. Standard FW-STD-WTR-01 New "
    "stream diversions and associated ditches shall have screens placed on them to prevent "
    "capture of fish and other aquatic organisms. Suitability MA1b-SUIT-07 The Jewel Basin "
    "hiking area is not suitable for motorized use, mechanized transport, and stock use."
)

_CUSTER_SOURCES = (
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
        _CUSTER_PLAN_COMPONENT_TEXT,
    ),
    (
        "R1PLAN-custer-gallatin-nf-03",
        "Custer Gallatin Land Management Plan Record of Decision PDF",
        "The record of decision identifies the selected alternative and plan approval.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-04",
        "Custer Gallatin Land Management Plan FEIS Volume 1 PDF",
        "The final environmental impact statement volume 1 describes effects context.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-05",
        "Custer Gallatin Land Management Plan FEIS Volume 2 PDF",
        "The final environmental impact statement volume 2 discusses plan allocations.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-06",
        "Custer Gallatin LMP Biological Assessment PDF",
        "The biological assessment analyzes species and habitat effects.",
    ),
    (
        "R1PLAN-custer-gallatin-nf-07",
        "Custer Gallatin LMP Biological Opinion PDF",
        "The biological opinion documents ESA section 7 consultation.",
    ),
)

_BEAVERHEAD_SOURCES = (
    (
        "R1PLAN-beaverhead-deerlodge-nf-01",
        "Beaverhead-Deerlodge planning page",
        (
            "The Beaverhead-Deerlodge planning page lists the forest plan, corrected FEIS, "
            "records of decision, and biological assessment and biological opinion support records."
        ),
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-02",
        "2009 Beaverhead-Deerlodge Forest Plan PDF",
        _BEAVERHEAD_PLAN_COMPONENT_TEXT,
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-03",
        "Beaverhead-Deerlodge Corrected FEIS PDF",
        (
            "The final environmental impact statement describes travel management, recreation "
            "allocations, recommended wilderness, and roadless areas."
        ),
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-04",
        "Beaverhead-Deerlodge Record of Decision PDF",
        "The record of decision identifies the selected alternative and plan approval.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-05",
        "Beaverhead-Deerlodge Travel Management Record of Decision PDF",
        (
            "The record of decision enacts travel management direction for summer non-motorized "
            "and winter non-motorized allocations and recommended wilderness closures."
        ),
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-18",
        "Beaverhead-Deerlodge Canada Lynx Biological Assessment PDF",
        "The biological assessment evaluates Canada lynx habitat and critical habitat under ESA.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-19",
        "Beaverhead-Deerlodge Canada Lynx Biological Opinion PDF",
        "The biological opinion documents Canada lynx ESA consultation terms and conditions.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-22",
        "Beaverhead-Deerlodge Grizzly Bear Biological Assessment PDF",
        "The biological assessment evaluates grizzly bear action area effects under ESA.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-23",
        "Beaverhead-Deerlodge Grizzly Bear Biological Opinion PDF",
        "The biological opinion discusses grizzly bear ESA reinitiation and consultation terms.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-24",
        "Beaverhead-Deerlodge Supplemental Grizzly Bear Biological Assessment PDF",
        "The supplemental biological assessment describes grizzly bear action area effects.",
    ),
    (
        "R1PLAN-beaverhead-deerlodge-nf-25",
        "Beaverhead-Deerlodge Supplemental Grizzly Bear Biological Opinion PDF",
        "The supplemental biological opinion discusses grizzly bear consultation and reinitiation.",
    ),
)

_FLATHEAD_SOURCES = (
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
        "R1PLAN-flathead-nf-02",
        "2018 Flathead National Forest Land Management Plan PDF",
        _FLATHEAD_PLAN_COMPONENT_TEXT,
    ),
    (
        "R1PLAN-flathead-nf-03",
        "Flathead Record of Decision PDF",
        (
            "The record of decision identifies the selected alternative, plan approval, Hungry "
            "Horse-Glacier View Ranger District, and recommended wilderness areas."
        ),
    ),
    (
        "R1PLAN-flathead-nf-04",
        "Flathead FEIS Volume 1 PDF",
        (
            "The final environmental impact statement discusses alternatives, effects, "
            "recommended wilderness, inventoried roadless areas, and wild and scenic rivers."
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


def _build_custer_compliance_source_library(output_dir: Path, source_set_id: str) -> None:
    source_record_ids = [source_record_id for source_record_id, _title, _text in _CUSTER_SOURCES]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=source_record_ids,
    )
    chunks_path = _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label=f"{source_record_id} | {title} | artifact abc123",
                text=text,
            )
            for source_record_id, title, text in _CUSTER_SOURCES
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [title]
            for source_record_id, title, _text in _CUSTER_SOURCES
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    build_forest_plan_component_inventory(
        output_dir=output_dir,
        source_set_id=source_set_id,
        source_record_id="R1PLAN-custer-gallatin-nf-02",
        forest_unit_id="custer-gallatin-nf",
        plan_version="2022",
        chunks_path=chunks_path,
        management_area_ids=["mgmt-crazy-mountains-bca"],
    )


def _build_beaverhead_compliance_source_library(output_dir: Path, source_set_id: str) -> None:
    source_record_ids = [source_record_id for source_record_id, _title, _text in _BEAVERHEAD_SOURCES]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=source_record_ids,
    )
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label=f"{source_record_id} | {title} | artifact abc123",
                text=text,
            )
            for source_record_id, title, text in _BEAVERHEAD_SOURCES
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [title]
            for source_record_id, title, _text in _BEAVERHEAD_SOURCES
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    _write_beaverhead_component_inventory(output_dir, source_set_id)


def _build_flathead_compliance_source_library(output_dir: Path, source_set_id: str) -> None:
    source_record_ids = [source_record_id for source_record_id, _title, _text in _FLATHEAD_SOURCES]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=source_record_ids,
    )
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role="forest_plan",
                authority_level="forest_plan",
                citation_label=f"{source_record_id} | {title} | artifact abc123",
                text=text,
            )
            for source_record_id, title, text in _FLATHEAD_SOURCES
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [title]
            for source_record_id, title, _text in _FLATHEAD_SOURCES
        },
    )
    _write_extraction_accuracy_audit(
        output_dir,
        source_set_id,
        admitted_source_record_ids=source_record_ids,
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
    _write_flathead_component_inventory(output_dir, source_set_id)


def _write_beaverhead_component_inventory(output_dir: Path, source_set_id: str) -> None:
    components_dir = output_dir / "derived" / source_set_id / "forest_plan_components"
    inventory_path = components_dir / "component_inventory.json"
    coverage_path = components_dir / "component_inventory_build_coverage.json"
    components_dir.mkdir(parents=True, exist_ok=True)
    source_record_id = "R1PLAN-beaverhead-deerlodge-nf-02"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    content_sha256 = hashlib.sha256(_BEAVERHEAD_PLAN_COMPONENT_TEXT.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
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
            "name": "tests/support/compliance_component_fixtures.py",
            "version": "forest-plan-component-inventory-v0",
        },
    }
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "beaverhead-test-components-v0",
        "forest_unit_id": "beaverhead-deerlodge-nf",
        "plan_version": "2009",
        "source_set_id": source_set_id,
        "components": [
            {
                "component_id": "bdnf-west-big-hole-std-01",
                "component_type": "standard",
                "component_text": (
                    "Standards (BD-STD-WBH) 01 New permanent or temporary roads shall not be "
                    "allowed."
                ),
                "forest_unit_id": "beaverhead-deerlodge-nf",
                "plan_version": "2009",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "section_id": "west-big-hole-standard-1",
                "section_heading": "West Big Hole Management Area Standards",
                "page": None,
                "citation_label": (
                    "R1PLAN-beaverhead-deerlodge-nf-02 | test plan | artifact abc123"
                ),
                "geographic_area_ids": ["geo-big-hole-landscape"],
                "management_area_ids": ["mgmt-west-big-hole"],
                "overlay_ids": ["overlay-inventoried-roadless-area"],
                "resource_topics": ["travel management"],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "activity_tags": ["new roads"],
                "package_evidence_terms": ["new permanent or temporary roads"],
                "provenance": provenance,
            }
        ],
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    coverage = {
        "schema_version": "forest-plan-component-inventory-build-coverage-v0",
        "created_at": "2026-05-11T00:00:00Z",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunks_path": str(output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"),
        "selected_chunk_count": 1,
        "detected_component_count": 1,
        "detected_standard_count": 1,
        "built_component_count": 1,
        "built_standard_count": 1,
        "missing_component_ids": [],
        "missing_standard_ids": [],
        "duplicate_component_ids": [],
        "duplicate_standard_ids": [],
        "validation_errors": [],
        "detected_component_labels": [
            {
                "component_id": "bdnf-west-big-hole-std-01",
                "component_type": "standard",
                "label": "Standards",
                "code": "West Big Hole Management Area",
                "number": "1",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "West Big Hole Management Area Standards",
            }
        ],
        "detected_standard_labels": [
            {
                "component_id": "bdnf-west-big-hole-std-01",
                "component_type": "standard",
                "label": "Standards",
                "code": "West Big Hole Management Area",
                "number": "1",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "West Big Hole Management Area Standards",
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
        ],
    }
    coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")


def _write_flathead_component_inventory(output_dir: Path, source_set_id: str) -> None:
    components_dir = output_dir / "derived" / source_set_id / "forest_plan_components"
    inventory_path = components_dir / "component_inventory.json"
    coverage_path = components_dir / "component_inventory_build_coverage.json"
    components_dir.mkdir(parents=True, exist_ok=True)
    source_record_id = "R1PLAN-flathead-nf-02"
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    content_sha256 = hashlib.sha256(_FLATHEAD_PLAN_COMPONENT_TEXT.encode("utf-8")).hexdigest()
    source_chunk_ids = [f"chunk:{source_record_id}"]
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
            "name": "tests/support/compliance_component_fixtures.py",
            "version": "forest-plan-component-inventory-v0",
        },
    }
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "flathead-test-components-v0",
        "forest_unit_id": "flathead-nf",
        "plan_version": "2018",
        "source_set_id": source_set_id,
        "components": [
            {
                "component_id": "flathead-fw-std-wtr-01",
                "component_type": "standard",
                "component_text": (
                    "Standard (FW-STD-WTR) 01 New stream diversions and associated ditches "
                    "shall have screens placed on them to prevent capture of fish and other "
                    "aquatic organisms."
                ),
                "forest_unit_id": "flathead-nf",
                "plan_version": "2018",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "section_id": "jewel-basin-hiking-area-standard-1",
                "section_heading": "Jewel Basin Hiking Area Standards",
                "page": None,
                "citation_label": "R1PLAN-flathead-nf-02 | test plan | artifact abc123",
                "geographic_area_ids": ["geo-hungry-horse"],
                "management_area_ids": ["mgmt-jewel-basin-hiking-area"],
                "overlay_ids": [],
                "resource_topics": ["hydrology"],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "activity_tags": ["stream diversions", "screens", "aquatic organisms"],
                "package_evidence_terms": [
                    "new stream diversions",
                    "screens placed on them",
                    "aquatic organisms",
                ],
                "provenance": provenance,
            },
            {
                "component_id": "flathead-ma1b-suit-07",
                "component_type": "suitability",
                "component_text": (
                    "Suitability (MA1b-SUIT) 07 The Jewel Basin hiking area is not suitable "
                    "for motorized use, mechanized transport, and stock use."
                ),
                "forest_unit_id": "flathead-nf",
                "plan_version": "2018",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "section_id": "jewel-basin-hiking-area-suitability-7",
                "section_heading": "Jewel Basin Hiking Area Suitability",
                "page": None,
                "citation_label": "R1PLAN-flathead-nf-02 | test plan | artifact abc123",
                "geographic_area_ids": ["geo-hungry-horse"],
                "management_area_ids": ["mgmt-jewel-basin-hiking-area"],
                "overlay_ids": [],
                "resource_topics": ["recreation access"],
                "source_chunk_ids": source_chunk_ids,
                "artifact_sha256": artifact_sha256,
                "content_sha256": content_sha256,
                "activity_tags": ["motorized use", "mechanized transport", "stock use"],
                "package_evidence_terms": [
                    "motorized use",
                    "mechanized transport",
                    "stock use",
                ],
                "provenance": provenance,
            },
        ],
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    coverage = {
        "schema_version": "forest-plan-component-inventory-build-coverage-v0",
        "created_at": "2026-05-11T00:00:00Z",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunks_path": str(output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"),
        "selected_chunk_count": 1,
        "detected_component_count": 2,
        "detected_standard_count": 1,
        "built_component_count": 2,
        "built_standard_count": 1,
        "missing_component_ids": [],
        "missing_standard_ids": [],
        "duplicate_component_ids": [],
        "duplicate_standard_ids": [],
        "validation_errors": [],
        "detected_component_labels": [
            {
                "component_id": "flathead-fw-std-wtr-01",
                "component_type": "standard",
                "label": "Standard",
                "code": "FW-STD-WTR",
                "number": "01",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "Jewel Basin Hiking Area Standards",
            },
            {
                "component_id": "flathead-ma1b-suit-07",
                "component_type": "suitability",
                "label": "Suitability",
                "code": "MA1b-SUIT",
                "number": "07",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "Jewel Basin Hiking Area Suitability",
            },
        ],
        "detected_standard_labels": [
            {
                "component_id": "flathead-fw-std-wtr-01",
                "component_type": "standard",
                "label": "Standard",
                "code": "FW-STD-WTR",
                "number": "01",
                "source_record_id": source_record_id,
                "chunk_id": source_chunk_ids[0],
                "section_heading": "Jewel Basin Hiking Area Standards",
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
        ],
    }
    coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")


def _write_component_adjudication_eval(
    review_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
    passed: bool,
    pending_count: int = 0,
    queue_item_count: int = 2,
    real_ea_omission_count: int | None = None,
    system_miss_count: int = 0,
) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    resolved_count = queue_item_count - pending_count
    real_ea_omission_count = (
        resolved_count if real_ea_omission_count is None else real_ea_omission_count
    )
    failure_counts = {"adjudication_pending": pending_count} if pending_count else {}
    outcome_counts = {}
    if real_ea_omission_count:
        outcome_counts["real_ea_omission"] = real_ea_omission_count
    if system_miss_count:
        outcome_counts["system_miss"] = system_miss_count
    (review_dir / "forest_plan_component_adjudication_eval.json").write_text(
        json.dumps(
            {
                "schema_version": "forest-plan-component-adjudication-eval-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "summary": {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "adjudication_file": str(
                        review_dir / "forest_plan_component_adjudication.json"
                    ),
                    "queue_item_count": queue_item_count,
                    "adjudication_item_count": queue_item_count,
                    "resolved_adjudication_count": resolved_count,
                    "pending_adjudication_count": pending_count,
                    "real_ea_omission_count": real_ea_omission_count,
                    "system_miss_count": system_miss_count,
                    "adjudication_completion_rate": round(resolved_count / queue_item_count, 6),
                    "real_ea_omission_rate": round(
                        real_ea_omission_count / queue_item_count,
                        6,
                    ),
                    "system_miss_rate": round(system_miss_count / queue_item_count, 6),
                    "adjudication_expectation_match_rate": 1.0,
                    "adjudication_outcome_counts": outcome_counts,
                    "disposition_counts": (
                        {"true_ea_omission": real_ea_omission_count}
                        if real_ea_omission_count
                        else {}
                    ),
                    "real_ea_omission_disposition_counts": (
                        {"true_ea_omission": real_ea_omission_count}
                        if real_ea_omission_count
                        else {}
                    ),
                    "system_miss_disposition_counts": (
                        {"retrieval_miss": system_miss_count}
                        if system_miss_count
                        else {}
                    ),
                    "failure_category_counts": failure_counts,
                    "passed": passed,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_component_eval(
    review_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
    passed: bool,
    schema_version: str = "forest-plan-component-eval-results-v0",
) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "forest_plan_component_eval_results.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "summary": {
                    "schema_version": schema_version,
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "case_count": 3,
                    "passed_case_count": 3 if passed else 2,
                    "failed_case_count": 0 if passed else 1,
                    "metrics": {
                        "component_applicability_precision": 1.0,
                        "component_applicability_recall": 1.0,
                        "applicable_standard_recall": 1.0,
                    },
                    "failure_category_counts": {} if passed else {"package_section_mismatch": 1},
                    "passed": passed,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_custer_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-custer-gallatin-ea",
        "version": "0.1.0",
        "title": "Unit Custer Gallatin EA Rule Pack",
        "description": "Unit test Custer Gallatin forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
        "rules": [
            {
                "id": "custer_gallatin_lmp_2022",
                "title": "Custer Gallatin forest-plan standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_custer_forest_plan",
                "authority_source_record_id": "R1PLAN-custer-gallatin-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Custer Gallatin standard?",
                "requirement": (
                    "Custer Gallatin EAs in the Crazy Mountains Backcountry Area must "
                    "address the standard prohibiting new permanent or temporary roads."
                ),
                "package_query": "new permanent or temporary roads",
                "package_terms": ["new permanent or temporary roads"],
                "source_query": "new permanent or temporary roads shall not be allowed",
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "custer-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_beaverhead_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-beaverhead-ea",
        "version": "0.1.0",
        "title": "Unit Beaverhead-Deerlodge EA Rule Pack",
        "description": "Unit test Beaverhead-Deerlodge forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-beaverhead-deerlodge-nf-02"],
        "rules": [
            {
                "id": "beaverhead_west_big_hole_lmp_2009",
                "title": "Beaverhead-Deerlodge forest-plan standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_beaverhead_forest_plan",
                "authority_source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Beaverhead standard?",
                "requirement": (
                    "Beaverhead-Deerlodge EAs in the West Big Hole Management Area must "
                    "address the standard prohibiting new permanent or temporary roads."
                ),
                "package_query": "new permanent or temporary roads",
                "package_terms": ["new permanent or temporary roads"],
                "source_query": "new permanent or temporary roads shall not be allowed",
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "beaverhead-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_flathead_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-flathead-ea",
        "version": "0.1.0",
        "title": "Unit Flathead EA Rule Pack",
        "description": "Unit test Flathead forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-flathead-nf-02"],
        "rules": [
            {
                "id": "flathead_fw_std_wtr_2018",
                "title": "Flathead forest-plan stream-screen standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_flathead_forest_plan",
                "authority_source_record_id": "R1PLAN-flathead-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Flathead standard?",
                "requirement": (
                    "Flathead EAs in the Jewel Basin Hiking Area must address the stream-"
                    "screening standard for new diversions."
                ),
                "package_query": "new stream diversions screens placed on them aquatic organisms",
                "package_terms": ["new stream diversions", "screens placed on them"],
                "source_query": (
                    "new stream diversions and associated ditches shall have screens placed "
                    "on them to prevent capture of fish and other aquatic organisms"
                ),
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-flathead-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "flathead-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path
