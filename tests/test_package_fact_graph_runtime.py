from __future__ import annotations

import hashlib

from usfs_r1_ea_sources.forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from usfs_r1_ea_sources.forest_plan_profiles import load_forest_plan_profiles
from usfs_r1_ea_sources.package_fact_graph_runtime import _build_extraction_summary
from usfs_r1_ea_sources.package_fact_graph_runtime import _extract_package_facts


def test_extract_package_facts_records_negative_location_and_weak_signal_uncertainty() -> None:
    profiles = load_forest_plan_profiles(DEFAULT_FOREST_PLAN_PROFILES_PATH)
    chunks = [
        _chunk(
            text=(
                "The project area is in the Custer Gallatin National Forest. "
                "The Sioux Geographic Area is not part of the project area. "
                "A Clean Water Act Section 404 permit may be required."
            )
        )
    ]

    extraction = _extract_package_facts(package_chunks=chunks, profiles=profiles)
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]

    assert len(extraction["section_map"]) == 1
    assert extraction["section_map"][0]["citation_label"] == "EA-PACKAGE-001"
    assert extraction["section_map"][0]["package_chunk_ids"] == ["chunk-0"]
    assert extraction["section_map"][0]["page_label"] == "1"
    assert (
        extraction["section_map"][0]["section_label"]
        == "Affected Environment / Resources and Consultation"
    )
    assert any(
        node["node_type"] == "geography"
        and node["normalized_value"] == "geo-sioux"
        and node["confidence_class"] == "negative_context"
        for node in fact_nodes
    )
    assert any(
        record["chunk_id"] == "chunk-0"
        and record["fact_subtype"] == "geographic_area"
        and record["matched_text"] == "Sioux Geographic Area"
        and record["node_type"] == "geography"
        and record["normalized_value"] == "geo-sioux"
        and record["reason"] == "negative_or_out_of_scope_location_context"
        for record in extraction["suppressed_location_facts"]
    )
    assert any(
        record["evidence_strength"]["matched_phrase"] == "not part of the project area"
        for record in extraction["suppressed_location_facts"]
        if record["normalized_value"] == "geo-sioux"
    )
    assert any(
        record["uncertainty_class"] == "weak_signal"
        and record["normalized_value"] == "clean_water_act"
        and record["matched_phrase"] == "may be required"
        for record in extraction["uncertainty_records"]
    )
    assert any(
        record["uncertainty_class"] == "missing_package_fact_type"
        and record["node_type"] == "action"
        for record in extraction["uncertainty_records"]
    )


def test_build_extraction_summary_counts_runtime_outputs() -> None:
    profiles = load_forest_plan_profiles(DEFAULT_FOREST_PLAN_PROFILES_PATH)
    chunks = [
        _chunk(
            text=(
                "The Sioux Geographic Area is not part of the project area. "
                "A Clean Water Act Section 404 permit may be required."
            )
        )
    ]
    extraction = _extract_package_facts(package_chunks=chunks, profiles=profiles)

    summary = _build_extraction_summary(
        package_manifest=[{"status": "extracted"}],
        package_chunks=chunks,
        extraction=extraction,
    )

    assert summary["package_file_count"] == 1
    assert summary["package_chunk_count"] == 1
    assert summary["package_section_count"] == 1
    assert summary["negative_location_fact_count"] >= 1
    assert summary["weak_signal_fact_count"] >= 1
    assert summary["uncertainty_record_count"] >= 1
    assert summary["missing_common_fact_type_count"] >= 1
    assert summary["fact_type_counts"]["permit"] >= 1


def _chunk(*, text: str) -> dict:
    artifact_sha256 = hashlib.sha256(b"package-fact-runtime").hexdigest()
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "artifact_path": "/tmp/east-crazy.pdf",
        "artifact_sha256": artifact_sha256,
        "authority_level": "project_record",
        "char_end": len(text),
        "char_start": 0,
        "chunk_id": "chunk-0",
        "chunk_index": 0,
        "citation_label": "EA-PACKAGE-001",
        "content_sha256": content_sha256,
        "document_role": "ea_package",
        "extracted_at": "2026-05-03T00:00:00Z",
        "heading": "Resources and Consultation",
        "page": 1,
        "parser_name": "unit-parser",
        "parser_version": "1.0",
        "section": "Affected Environment",
        "source_record_id": "EA-PACKAGE-001",
        "source_set_id": "ea-package-unit",
        "source_text_path": "/tmp/east-crazy.txt",
        "text": text,
        "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
    }
