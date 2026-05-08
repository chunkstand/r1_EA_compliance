from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .evidence_strength import classify_evidence_strength
from .evidence_strength import evidence_strength_for_confidence
from .evidence_strength import is_weak_signal_text
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import ForestPlanProfileCollection
from .forest_plan_profiles import load_forest_plan_profiles
from .records import sha256_file


PACKAGE_FACT_GRAPH_SCHEMA_VERSION = "package-fact-graph-v0"
PACKAGE_APPLICABILITY_CONTEXT_SCHEMA_VERSION = "package-applicability-context-v0"
PACKAGE_FACT_GRAPH_VALIDATION_SCHEMA_VERSION = "package-fact-graph-validation-v0"
PACKAGE_FACT_EXTRACTION_METHOD_VERSION = "deterministic-package-fact-extraction-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
LOCATION_NODE_TYPES = {"geography", "management_area", "overlay"}
COMMON_PACKAGE_FACT_TYPES = {
    "action",
    "agency",
    "nepa_level",
    "geography",
    "resource_topic",
    "consultation",
    "permit",
}
UNCERTAINTY_RECORD_STATUSES = {
    "requires_adjudication_before_applicability_decision",
    "missing_package_fact_type_recorded_for_later_applicability_context",
}


@dataclass(frozen=True)
class PackageFactGraphResult:
    review_id: str
    source_set_id: str
    applicability_dir: Path
    package_fact_graph_path: Path
    package_applicability_context_path: Path
    validation_summary_path: Path
    summary: dict[str, Any]


def build_package_fact_graph(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    package_path: Path | None = None,
    package_manifest_path: Path | None = None,
    package_chunks_path: Path | None = None,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
) -> PackageFactGraphResult:
    """Build package fact/context artifacts without deciding authority applicability."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    review_dir = output_dir / "reviews" / review_id
    package_dir = review_dir / "package"
    applicability_dir = review_dir / "applicability"
    package_manifest_path = package_manifest_path or package_dir / "package_manifest.jsonl"
    package_chunks_path = package_chunks_path or package_dir / "package_chunks.jsonl"
    package_manifest = _read_required_jsonl(package_manifest_path, "package manifest")
    package_chunks = _read_required_jsonl(package_chunks_path, "package chunks")

    if source_set_id is None:
        source_set_id = _source_set_id_from_authority_snapshot(applicability_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_package_chunks(package_chunks)
    _validate_safe_segment(source_set_id, "source_set_id")

    forest_plan_profiles_path = Path(forest_plan_profiles_path)
    profiles = load_forest_plan_profiles(forest_plan_profiles_path)
    created_at = _utc_now()
    applicability_run_id = f"applicability-context-{review_id}"
    manifest_sha256 = sha256_file(package_manifest_path)
    chunks_sha256 = sha256_file(package_chunks_path)
    profiles_sha256 = sha256_file(forest_plan_profiles_path)

    extraction = _extract_package_facts(
        package_chunks=package_chunks,
        profiles=profiles,
    )
    summary = _build_extraction_summary(
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        extraction=extraction,
    )
    validation = _validate_package_fact_graph(
        extraction=extraction,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
    )
    graph_without_hash = {
        "schema_version": PACKAGE_FACT_GRAPH_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "package_fact_graph_id": f"package-fact-graph:{review_id}",
        "package_manifest_sha256": manifest_sha256,
        "package_chunks_sha256": chunks_sha256,
        "forest_plan_profiles_sha256": profiles_sha256,
        "extraction_method_versions": {
            "package_fact_extraction": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
            "forest_plan_profiles": profiles.schema_version,
        },
        "source_package": _source_package_metadata(
            package_path=package_path,
            package_manifest=package_manifest,
        ),
        "artifact_paths": {
            "package_manifest_path": str(package_manifest_path),
            "package_chunks_path": str(package_chunks_path),
            "forest_plan_profiles_path": str(forest_plan_profiles_path),
        },
        "extraction_summary": summary,
        "nodes": extraction["nodes"],
        "edges": extraction["edges"],
        "validation": validation,
    }
    graph_sha256 = _stable_sha256(graph_without_hash)
    graph_payload = {
        **graph_without_hash,
        "package_fact_graph_sha256": graph_sha256,
    }
    context_without_hash = _build_applicability_context(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_run_id=applicability_run_id,
        package_path=package_path,
        package_manifest=package_manifest,
        package_manifest_sha256=manifest_sha256,
        package_chunks_sha256=chunks_sha256,
        package_fact_graph_sha256=graph_sha256,
        extraction=extraction,
        summary=summary,
    )
    context_sha256 = _stable_sha256(context_without_hash)
    context_payload = {
        **context_without_hash,
        "package_context_sha256": context_sha256,
    }
    validation_payload = {
        "schema_version": PACKAGE_FACT_GRAPH_VALIDATION_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "package_manifest_sha256": manifest_sha256,
        "package_chunks_sha256": chunks_sha256,
        "package_fact_graph_sha256": graph_sha256,
        "package_context_sha256": context_sha256,
        "created_at": created_at,
        "validation": validation,
        "summary": {
            **summary,
            "validation_passed": validation["passed"],
        },
    }

    package_fact_graph_path = applicability_dir / "package_fact_graph.json"
    package_applicability_context_path = (
        applicability_dir / "package_applicability_context.json"
    )
    validation_summary_path = applicability_dir / "package_fact_graph_validation.json"
    _write_json(package_fact_graph_path, graph_payload)
    _write_json(package_applicability_context_path, context_payload)
    _write_json(validation_summary_path, validation_payload)

    result_summary = {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "validation_passed": validation["passed"],
        "package_manifest_path": str(package_manifest_path),
        "package_chunks_path": str(package_chunks_path),
        "package_fact_graph_path": str(package_fact_graph_path),
        "package_applicability_context_path": str(package_applicability_context_path),
        "package_fact_graph_validation_path": str(validation_summary_path),
        "package_fact_graph_sha256": graph_sha256,
        "package_context_sha256": context_sha256,
        **summary,
    }
    return PackageFactGraphResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        package_fact_graph_path=package_fact_graph_path,
        package_applicability_context_path=package_applicability_context_path,
        validation_summary_path=validation_summary_path,
        summary=result_summary,
    )


def _extract_package_facts(
    *,
    package_chunks: list[dict[str, Any]],
    profiles: ForestPlanProfileCollection,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    section_nodes: dict[str, dict[str, Any]] = {}
    suppressed_location_facts: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()
    seen_edge_ids: set[str] = set()
    term_specs = _base_term_specs()
    term_specs.extend(_profile_term_specs(profiles))

    for chunk in package_chunks:
        section_node = _section_node_for_chunk(chunk)
        section_id = str(section_node["node_id"])
        if section_id not in section_nodes:
            section_nodes[section_id] = section_node
        else:
            existing_chunk_ids = section_nodes[section_id]["package_chunk_ids"]
            chunk_id = str(chunk.get("chunk_id") or "")
            if chunk_id and chunk_id not in existing_chunk_ids:
                existing_chunk_ids.append(chunk_id)

        chunk_text = str(chunk.get("text") or "")
        for spec in term_specs:
            for term in spec["terms"]:
                for match in _find_term_matches(chunk_text, term):
                    confidence_class = str(spec.get("confidence_class") or "observed")
                    fact_subtype = str(spec.get("fact_subtype") or "")
                    evidence_strength = classify_evidence_strength(
                        text=chunk_text,
                        start=match.start(),
                        end=match.end(),
                        matched_text=match.group(0),
                        default_confidence_class=confidence_class,
                        section_family=_section_family(chunk),
                    )
                    if spec["node_type"] in LOCATION_NODE_TYPES and _is_negative_location_match(
                        chunk_text,
                        match.start(),
                        match.end(),
                    ):
                        evidence_strength = classify_evidence_strength(
                            text=chunk_text,
                            start=match.start(),
                            end=match.end(),
                            matched_text=match.group(0),
                            section_family=_section_family(chunk),
                            negative_context=True,
                            negative_reason="negative_or_out_of_scope_location_context",
                        )
                        confidence_class = str(evidence_strength["confidence_class"])
                        suppressed_location_facts.append(
                            {
                                "node_type": spec["node_type"],
                                "fact_subtype": fact_subtype,
                                "normalized_value": spec["normalized_value"],
                                "label": spec["label"],
                                "matched_text": match.group(0),
                                "chunk_id": chunk.get("chunk_id"),
                                "chunk_char_start": match.start(),
                                "chunk_char_end": match.end(),
                                "section_id": section_id,
                                "reason": "negative_or_out_of_scope_location_context",
                                "evidence_strength": evidence_strength,
                            }
                        )
                    else:
                        confidence_class = str(evidence_strength["confidence_class"])
                    _add_fact_node(
                        nodes=nodes,
                        edges=edges,
                        seen_node_ids=seen_node_ids,
                        seen_edge_ids=seen_edge_ids,
                        chunk=chunk,
                        section_id=section_id,
                        spec=spec,
                        match_start=match.start(),
                        match_end=match.end(),
                        matched_text=match.group(0),
                        confidence_class=confidence_class,
                        evidence_strength=evidence_strength,
                    )

    nodes = [*section_nodes.values(), *nodes]
    uncertainty_records, contradiction_edges = _build_uncertainty_records(nodes)
    for edge in contradiction_edges:
        if edge["edge_id"] not in seen_edge_ids:
            edges.append(edge)
            seen_edge_ids.add(edge["edge_id"])

    nodes.sort(key=lambda node: str(node["node_id"]))
    edges.sort(key=lambda edge: str(edge["edge_id"]))
    return {
        "nodes": nodes,
        "edges": edges,
        "section_map": _section_map(section_nodes),
        "uncertainty_records": uncertainty_records,
        "suppressed_location_facts": sorted(
            suppressed_location_facts,
            key=lambda item: (
                str(item["chunk_id"]),
                str(item["node_type"]),
                str(item["normalized_value"]),
            ),
        ),
    }


def _base_term_specs() -> list[dict[str, Any]]:
    return [
        _term_spec("geography", "project_location", "project_area", "Project area", ["project area", "analysis area", "project location"]),
        _term_spec("action", "project_action_type", "land_exchange", "Land exchange", ["land exchange", "exchange of lands"]),
        _term_spec(
            "authority",
            "statutory_authority",
            "flpma_section_206_land_exchange",
            "FLPMA Section 206 land-exchange authority",
            [
                "Federal Land Policy and Management Act",
                "FLPMA",
                "FLPMA Section 206",
                "FLPMA sec. 206",
                "FLPMA \u00a7 206",
                "Section 206 of FLPMA",
                "43 U.S.C. 1716",
                "43 U.S.C. \u00a7 1716",
                "43 USC 1716",
                "43 U.S.C. section 1716",
            ],
            source_metadata={
                "authority_family_id": "land_exchange_statutory_authorities",
                "rule_id": "flpma_section_206_land_exchange",
                "source_record_id": "R1EA-146",
                "statutory_citation": "43 U.S.C. 1716",
            },
        ),
        _term_spec("action", "project_action_type", "road_action", "Road action", ["road construction", "new road", "road realignment", "road decommissioning"]),
        _term_spec("action", "project_action_type", "trail_action", "Trail action", ["trail construction", "trail relocation", "trail reroute"]),
        _term_spec("agency", "lead_agency", "usfs", "USDA Forest Service", ["USDA Forest Service", "Forest Service", "United States Forest Service"]),
        _term_spec("agency", "lead_agency", "usda", "USDA", ["U.S. Department of Agriculture", "USDA"]),
        _term_spec("agency", "cooperating_agency", "cooperating_agency", "Cooperating agency", ["cooperating agency", "cooperating agencies"]),
        _term_spec("decision_posture", "decision_document", "decision_notice", "Decision Notice", ["decision notice", "draft decision notice"]),
        _term_spec("decision_posture", "finding", "fonsi", "Finding of No Significant Impact", ["finding of no significant impact", "FONSI"]),
        _term_spec("decision_posture", "scoping", "scoping", "Scoping", ["scoping notice", "scoping period"]),
        _term_spec("nepa_level", "analysis_level", "environmental_assessment", "Environmental Assessment", ["environmental assessment"]),
        _term_spec("nepa_level", "analysis_level", "environmental_impact_statement", "Environmental Impact Statement", ["environmental impact statement", "EIS"]),
        _term_spec("nepa_level", "analysis_level", "categorical_exclusion", "Categorical Exclusion", ["categorical exclusion"]),
        _term_spec("resource_topic", "resource", "land_exchange", "Land exchange", ["land exchange"]),
        _term_spec("resource_topic", "resource", "road", "Roads", ["road", "roads", "transportation system"]),
        _term_spec("resource_topic", "resource", "recreation", "Recreation", ["recreation", "recreational access"]),
        _term_spec("resource_topic", "resource", "minerals", "Minerals", ["minerals", "mineral", "mining"]),
        _term_spec("resource_topic", "resource", "wildlife", "Wildlife", ["wildlife", "habitat", "grizzly bear", "lynx"]),
        _term_spec("resource_topic", "resource", "water", "Water", ["water quality", "watershed", "stream", "wetland", "wetlands"]),
        _term_spec("resource_topic", "resource", "heritage", "Heritage", ["heritage", "cultural resource", "historic property", "archaeological"]),
        _term_spec("resource_topic", "resource", "botany", "Botany", ["botany", "botanical", "sensitive plants", "vegetation"]),
        _term_spec("resource_topic", "resource", "fire", "Fire and fuels", ["fire", "fuels", "wildfire"]),
        _term_spec("resource_topic", "resource", "scenery", "Scenery", ["scenery", "scenic integrity", "visual quality"]),
        _term_spec("resource_topic", "resource", "grazing", "Grazing", ["grazing", "range allotment", "allotment"]),
        _term_spec("resource_topic", "resource", "soils", "Soils", ["soil", "soils", "erosion"]),
        _term_spec("consultation", "esa", "esa", "Endangered Species Act consultation", ["Endangered Species Act", "ESA", "Section 7 consultation"]),
        _term_spec("consultation", "nhpa", "nhpa", "National Historic Preservation Act consultation", ["National Historic Preservation Act", "NHPA", "Section 106"]),
        _term_spec("consultation", "mbta", "mbta", "Migratory Bird Treaty Act", ["Migratory Bird Treaty Act", "MBTA"]),
        _term_spec("consultation", "tribal", "tribal_consultation", "Tribal consultation", ["tribal consultation", "tribes", "Tribal Historic Preservation Officer"]),
        _term_spec("permit", "clean_water_act", "clean_water_act", "Clean Water Act permit cue", ["Clean Water Act", "CWA", "Section 404", "404 permit"]),
        _term_spec("permit", "wetlands_floodplains", "wetlands", "Wetlands", ["wetlands", "wetland"]),
        _term_spec("permit", "wetlands_floodplains", "floodplains", "Floodplains", ["floodplains", "floodplain"]),
        _term_spec("permit", "roadless", "roadless", "Roadless area cue", ["roadless", "inventoried roadless area"]),
        _term_spec("permit", "wilderness", "wilderness", "Wilderness cue", ["wilderness", "wilderness study area"]),
        _term_spec("permit", "permit", "permit", "Permit cue", ["permit", "permits", "authorization"]),
        _term_spec("overlay", "designated_area", "designated_area", "Designated area", ["designated area", "special area", "Wild and Scenic River", "National Trail", "recommended wilderness"]),
        _term_spec("public_involvement", "public_involvement", "public_comment", "Public comment", ["public comment", "public comments", "comment period"]),
        _term_spec("public_involvement", "public_involvement", "scoping", "Scoping", ["public scoping", "scoping"]),
        _term_spec("alternative", "alternative", "no_action", "No Action Alternative", ["no action alternative", "no action"]),
        _term_spec("alternative", "alternative", "proposed_action", "Proposed Action", ["proposed action"]),
        _term_spec("alternative", "alternative", "alternatives", "Alternatives", ["alternatives considered", "range of alternatives", "alternative 1", "alternative 2"]),
    ]


def _profile_term_specs(profiles: ForestPlanProfileCollection) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for profile in profiles.profiles:
        specs.append(
            _term_spec(
                "geography",
                "forest_unit",
                profile.forest_unit_id,
                profile.forest_unit_names[0],
                list(profile.forest_unit_names),
                source_metadata={"forest_unit_id": profile.forest_unit_id},
            )
        )
        for entry in profile.ranger_district_terms:
            specs.append(
                _term_spec(
                    "geography",
                    "ranger_district",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
        for entry in profile.geographic_area_terms:
            specs.append(
                _term_spec(
                    "geography",
                    "geographic_area",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
        for entry in profile.management_area_terms:
            specs.append(
                _term_spec(
                    "management_area",
                    "management_area",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
        for entry in profile.overlay_terms:
            specs.append(
                _term_spec(
                    "overlay",
                    "overlay",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
    for unit in profiles.known_other_forest_units:
        specs.append(
            _term_spec(
                "geography",
                "forest_unit",
                unit.forest_unit_id,
                unit.names[0],
                list(unit.names),
                source_metadata={"forest_unit_id": unit.forest_unit_id},
            )
        )
    return specs


def _term_spec(
    node_type: str,
    fact_subtype: str,
    normalized_value: str,
    label: str,
    terms: list[str],
    *,
    confidence_class: str = "observed",
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "node_type": node_type,
        "fact_subtype": fact_subtype,
        "normalized_value": normalized_value,
        "label": label,
        "terms": tuple(_dedupe_strings(terms)),
        "confidence_class": confidence_class,
        "source_metadata": source_metadata or {},
    }


def _add_fact_node(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    seen_node_ids: set[str],
    seen_edge_ids: set[str],
    chunk: dict[str, Any],
    section_id: str,
    spec: dict[str, Any],
    match_start: int,
    match_end: int,
    matched_text: str,
    confidence_class: str,
    evidence_strength: dict[str, Any],
) -> None:
    chunk_id = str(chunk.get("chunk_id") or "unknown-chunk")
    absolute_start = _absolute_offset(chunk.get("char_start"), match_start)
    absolute_end = _absolute_offset(chunk.get("char_start"), match_end)
    span_id = _node_id(
        "evidence-span",
        chunk_id,
        str(match_start),
        str(match_end),
        str(chunk.get("content_sha256") or ""),
    )
    fact_node_id = _node_id(
        str(spec["node_type"]),
        str(spec["fact_subtype"]),
        str(spec["normalized_value"]),
        chunk_id,
        str(match_start),
        str(match_end),
        confidence_class,
    )
    if span_id not in seen_node_ids:
        nodes.append(
            {
                "node_id": span_id,
                "node_type": "evidence_span",
                "label": f"{chunk.get('citation_label') or chunk_id} span {match_start}-{match_end}",
                "normalized_value": span_id,
                "confidence_class": "observed",
                "evidence_strength": evidence_strength,
                "extraction_method": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
                "package_chunk_ids": [chunk_id],
                "section_ids": [section_id],
                "section_family": _section_family(chunk),
                "citation_label": chunk.get("citation_label"),
                "page_label": _page_label(chunk),
                "char_start": absolute_start,
                "char_end": absolute_end,
                "chunk_char_start": match_start,
                "chunk_char_end": match_end,
                "text_hash": chunk.get("content_sha256"),
                "content_sha256": chunk.get("content_sha256"),
                "artifact_sha256": chunk.get("artifact_sha256"),
                "parser_provenance": _parser_provenance(chunk),
                "matched_text": matched_text,
                "context_excerpt": _context_excerpt(
                    str(chunk.get("text") or ""),
                    match_start,
                    match_end,
                ),
                "evidence_span_ids": [span_id],
            }
        )
        seen_node_ids.add(span_id)
    if fact_node_id not in seen_node_ids:
        nodes.append(
            {
                "node_id": fact_node_id,
                "node_type": spec["node_type"],
                "fact_subtype": spec["fact_subtype"],
                "label": spec["label"],
                "raw_value": matched_text,
                "normalized_value": spec["normalized_value"],
                "confidence_class": confidence_class,
                "evidence_strength": evidence_strength,
                "extraction_method": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
                "source_metadata": spec["source_metadata"],
                "package_chunk_ids": [chunk_id],
                "section_ids": [section_id],
                "section_family": _section_family(chunk),
                "citation_label": chunk.get("citation_label"),
                "page_label": _page_label(chunk),
                "char_start": absolute_start,
                "char_end": absolute_end,
                "chunk_char_start": match_start,
                "chunk_char_end": match_end,
                "text_hash": chunk.get("content_sha256"),
                "content_sha256": chunk.get("content_sha256"),
                "artifact_sha256": chunk.get("artifact_sha256"),
                "parser_provenance": _parser_provenance(chunk),
                "evidence_span_ids": [span_id],
                "package_span_ids": [span_id],
            }
        )
        seen_node_ids.add(fact_node_id)
    _add_edge(
        edges=edges,
        seen_edge_ids=seen_edge_ids,
        edge_type="supports_fact",
        from_node_id=span_id,
        to_node_id=fact_node_id,
        evidence_span_ids=[span_id],
        rationale="Matched package span supports deterministic package fact.",
    )
    _add_edge(
        edges=edges,
        seen_edge_ids=seen_edge_ids,
        edge_type="derived_from_section",
        from_node_id=fact_node_id,
        to_node_id=section_id,
        evidence_span_ids=[span_id],
        rationale="Fact was extracted from the package section containing the span.",
    )


def _add_edge(
    *,
    edges: list[dict[str, Any]],
    seen_edge_ids: set[str],
    edge_type: str,
    from_node_id: str,
    to_node_id: str,
    evidence_span_ids: list[str],
    rationale: str,
    selected_status: str = "selected",
) -> None:
    edge_id = _node_id(edge_type, from_node_id, to_node_id, *evidence_span_ids)
    if edge_id in seen_edge_ids:
        return
    edges.append(
        {
            "edge_id": edge_id,
            "edge_type": edge_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "evidence_span_ids": evidence_span_ids,
            "path_rationale": rationale,
            "selected_status": selected_status,
        }
    )
    seen_edge_ids.add(edge_id)


def _build_uncertainty_records(
    nodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fact_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        if node.get("node_type") in {"package_section", "evidence_span"}:
            continue
        key = (
            str(node.get("node_type")),
            str(node.get("fact_subtype") or ""),
            str(node.get("normalized_value") or ""),
        )
        fact_groups[key].append(node)

    uncertainty_records = []
    contradiction_edges = []
    for key, grouped_nodes in sorted(fact_groups.items()):
        positive = [
            node
            for node in grouped_nodes
            if node.get("confidence_class") != "negative_context"
        ]
        negative = [
            node
            for node in grouped_nodes
            if node.get("confidence_class") == "negative_context"
        ]
        if not positive or not negative:
            weak_nodes = [
                node
                for node in grouped_nodes
                if node.get("confidence_class") == "weak_signal"
            ]
            for weak_node in weak_nodes:
                evidence_strength = weak_node.get("evidence_strength") or {}
                uncertainty_records.append(
                    {
                        "uncertainty_id": _node_id(
                            "uncertainty",
                            "weak-signal",
                            str(weak_node["node_id"]),
                        ),
                        "uncertainty_class": "weak_signal",
                        "node_type": key[0],
                        "fact_subtype": key[1],
                        "normalized_value": key[2],
                        "weak_fact_node_ids": [str(weak_node["node_id"])],
                        "status": "requires_adjudication_before_applicability_decision",
                        "rationale": "Package fact was extracted from conditional or uncertain wording.",
                        "evidence_strength": evidence_strength,
                        "weak_signal_reason": evidence_strength.get("reason"),
                        "matched_phrase": evidence_strength.get("matched_phrase"),
                        "evidence_window": evidence_strength.get("evidence_window"),
                    }
                )
            continue
        uncertainty_records.append(
            {
                "uncertainty_id": _node_id("uncertainty", "contradiction", *key),
                "uncertainty_class": "contradictory_package_evidence",
                "node_type": key[0],
                "fact_subtype": key[1],
                "normalized_value": key[2],
                "positive_fact_node_ids": [str(node["node_id"]) for node in positive],
                "negative_fact_node_ids": [str(node["node_id"]) for node in negative],
                "status": "requires_adjudication_before_applicability_decision",
                "rationale": "Package contains both observed and negative-context facts for the same value.",
            }
        )
        for positive_node in positive:
            for negative_node in negative:
                contradiction_edges.append(
                    {
                        "edge_id": _node_id(
                            "contradicts_fact",
                            str(negative_node["node_id"]),
                            str(positive_node["node_id"]),
                        ),
                        "edge_type": "contradicts_fact",
                        "from_node_id": negative_node["node_id"],
                        "to_node_id": positive_node["node_id"],
                        "evidence_span_ids": list(negative_node.get("evidence_span_ids") or []),
                        "path_rationale": "Negative-context package fact contradicts an observed fact value.",
                        "selected_status": "selected",
                    }
                )
    present_positive = {
        str(node.get("node_type"))
        for grouped_nodes in fact_groups.values()
        for node in grouped_nodes
        if node.get("confidence_class") != "negative_context"
    }
    for fact_type in sorted(COMMON_PACKAGE_FACT_TYPES - present_positive):
        uncertainty_records.append(
            {
                "uncertainty_id": _node_id("uncertainty", "missing-fact-type", fact_type),
                "uncertainty_class": "missing_package_fact_type",
                "node_type": fact_type,
                "fact_subtype": None,
                "normalized_value": None,
                "positive_fact_node_ids": [],
                "negative_fact_node_ids": [],
                "status": "missing_package_fact_type_recorded_for_later_applicability_context",
                "rationale": (
                    "No positive package fact of this common type was extracted; later "
                    "applicability stages must treat it as missing context, not a decision."
                ),
            }
        )
    return uncertainty_records, contradiction_edges


def _build_extraction_summary(
    *,
    package_manifest: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
    extraction: dict[str, Any],
) -> dict[str, Any]:
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]
    fact_type_counts = Counter(str(node["node_type"]) for node in fact_nodes)
    fact_subtype_counts = Counter(
        f"{node.get('node_type')}:{node.get('fact_subtype')}" for node in fact_nodes
    )
    confidence_counts = Counter(str(node["confidence_class"]) for node in fact_nodes)
    evidence_strength_counts = Counter(
        str((node.get("evidence_strength") or {}).get("strength_class") or node["confidence_class"])
        for node in fact_nodes
    )
    return {
        "package_file_count": len(package_manifest),
        "package_chunk_count": len(package_chunks),
        "package_section_count": len(extraction["section_map"]),
        "fact_node_count": len(fact_nodes),
        "evidence_span_node_count": sum(
            1 for node in extraction["nodes"] if node.get("node_type") == "evidence_span"
        ),
        "edge_count": len(extraction["edges"]),
        "fact_type_counts": dict(sorted(fact_type_counts.items())),
        "fact_subtype_counts": dict(sorted(fact_subtype_counts.items())),
        "confidence_class_counts": dict(sorted(confidence_counts.items())),
        "evidence_strength_class_counts": dict(sorted(evidence_strength_counts.items())),
        "negative_location_fact_count": len(extraction["suppressed_location_facts"]),
        "uncertainty_record_count": len(extraction["uncertainty_records"]),
        "weak_signal_fact_count": confidence_counts.get("weak_signal", 0),
        "missing_common_fact_type_count": sum(
            1
            for record in extraction["uncertainty_records"]
            if record.get("uncertainty_class") == "missing_package_fact_type"
        ),
    }


def _validate_package_fact_graph(
    *,
    extraction: dict[str, Any],
    package_manifest: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]
    checks = [
        {
            "name": "package_cache_present",
            "passed": bool(package_manifest) and bool(package_chunks),
            "details": {
                "package_file_count": len(package_manifest),
                "package_chunk_count": len(package_chunks),
            },
        },
        _check_fact_nodes_have_evidence(fact_nodes),
        _check_negative_location_context(extraction, fact_nodes),
        _check_uncertainty_records(extraction),
        _check_common_fact_type_coverage(fact_nodes),
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "uncertainty_records": extraction["uncertainty_records"],
        "negative_location_facts": extraction["suppressed_location_facts"],
    }


def _check_fact_nodes_have_evidence(fact_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for node in fact_nodes:
        if (
            not node.get("package_chunk_ids")
            or not node.get("section_ids")
            or not node.get("evidence_span_ids")
            or not node.get("content_sha256")
            or not node.get("artifact_sha256")
            or not node.get("parser_provenance")
        ):
            failures.append(str(node.get("node_id")))
    return {
        "name": "fact_nodes_have_package_spans_sections_provenance_and_hashes",
        "passed": not failures,
        "details": {
            "fact_node_count": len(fact_nodes),
            "failure_count": len(failures),
            "failed_node_ids": failures[:25],
        },
    }


def _check_negative_location_context(
    extraction: dict[str, Any],
    fact_nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for negative in extraction["suppressed_location_facts"]:
        for node in fact_nodes:
            if node.get("node_type") not in LOCATION_NODE_TYPES:
                continue
            if node.get("confidence_class") == "negative_context":
                continue
            if node.get("normalized_value") != negative["normalized_value"]:
                continue
            same_chunk = negative["chunk_id"] in (node.get("package_chunk_ids") or [])
            same_span = (
                node.get("chunk_char_start") == negative.get("chunk_char_start")
                and node.get("chunk_char_end") == negative.get("chunk_char_end")
            )
            if same_chunk and same_span:
                failures.append(
                    {
                        "negative_chunk_id": negative["chunk_id"],
                        "negative_chunk_char_start": negative.get("chunk_char_start"),
                        "negative_chunk_char_end": negative.get("chunk_char_end"),
                        "positive_node_id": node["node_id"],
                        "normalized_value": negative["normalized_value"],
                    }
                )
    return {
        "name": "negative_location_statements_do_not_create_positive_location_facts",
        "passed": not failures,
        "details": {
            "negative_location_fact_count": len(extraction["suppressed_location_facts"]),
            "failure_count": len(failures),
            "failures": failures[:25],
        },
    }


def _check_uncertainty_records(extraction: dict[str, Any]) -> dict[str, Any]:
    unresolved = [
        record
        for record in extraction["uncertainty_records"]
        if record.get("status") not in UNCERTAINTY_RECORD_STATUSES
    ]
    return {
        "name": "uncertain_facts_are_recorded_without_applicability_decisions",
        "passed": not unresolved,
        "details": {
            "uncertainty_record_count": len(extraction["uncertainty_records"]),
            "invalid_record_count": len(unresolved),
            "uncertainty_classes": dict(
                sorted(
                    Counter(
                        str(record.get("uncertainty_class") or "unspecified")
                        for record in extraction["uncertainty_records"]
                    ).items()
                )
            ),
        },
    }


def _check_common_fact_type_coverage(fact_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    present = {
        str(node.get("node_type"))
        for node in fact_nodes
        if node.get("confidence_class") != "negative_context"
    }
    return {
        "name": "common_package_fact_type_coverage_recorded",
        "passed": True,
        "details": {
            "present_fact_types": sorted(present),
            "missing_common_fact_types": sorted(COMMON_PACKAGE_FACT_TYPES - present),
        },
    }


def _build_applicability_context(
    *,
    review_id: str,
    source_set_id: str,
    applicability_run_id: str,
    package_path: Path | None,
    package_manifest: list[dict[str, Any]],
    package_manifest_sha256: str,
    package_chunks_sha256: str,
    package_fact_graph_sha256: str,
    extraction: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]
    compact_facts = [_compact_fact(node) for node in fact_nodes]
    return {
        "schema_version": PACKAGE_APPLICABILITY_CONTEXT_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "package_path": str(package_path) if package_path else None,
        "source_package": _source_package_metadata(
            package_path=package_path,
            package_manifest=package_manifest,
        ),
        "package_manifest_sha256": package_manifest_sha256,
        "package_chunks_sha256": package_chunks_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "package_section_map": extraction["section_map"],
        "section_family_bindings": _section_family_bindings(extraction["section_map"]),
        "project_type": _facts_by_type(compact_facts, "action"),
        "federal_action_signals": _facts_by_types(
            compact_facts,
            {"action", "agency", "nepa_level"},
        ),
        "authority_signals": _facts_by_type(compact_facts, "authority"),
        "forest_units": _facts_by_subtype(compact_facts, "geography", "forest_unit"),
        "project_locations": _facts_by_subtype(compact_facts, "geography", "project_location"),
        "geography": _facts_by_type(compact_facts, "geography"),
        "management_areas": _facts_by_type(compact_facts, "management_area"),
        "overlays": _facts_by_type(compact_facts, "overlay"),
        "resource_topics": _facts_by_type(compact_facts, "resource_topic"),
        "consultations": _facts_by_type(compact_facts, "consultation"),
        "permits": _facts_by_type(compact_facts, "permit"),
        "public_involvement_signals": _facts_by_type(compact_facts, "public_involvement"),
        "decision_posture": _facts_by_type(compact_facts, "decision_posture"),
        "nepa_level": _facts_by_type(compact_facts, "nepa_level"),
        "alternatives": _facts_by_type(compact_facts, "alternative"),
        "supporting_document_signals": _supporting_document_signals(compact_facts),
        "uncertainty_records": extraction["uncertainty_records"],
        "negative_location_facts": extraction["suppressed_location_facts"],
        "extracted_package_facts": compact_facts,
        "summary": summary,
    }


def _compact_fact(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "fact_node_id": node["node_id"],
        "fact_type": node["node_type"],
        "fact_subtype": node.get("fact_subtype"),
        "label": node.get("label"),
        "raw_value": node.get("raw_value"),
        "normalized_value": node.get("normalized_value"),
        "confidence_class": node.get("confidence_class"),
        "evidence_strength": node.get("evidence_strength")
        or evidence_strength_for_confidence(
            node.get("confidence_class"),
            section_family=node.get("section_family"),
        ),
        "source_metadata": node.get("source_metadata") or {},
        "package_chunk_ids": node.get("package_chunk_ids") or [],
        "section_ids": node.get("section_ids") or [],
        "section_family": node.get("section_family"),
        "citation_label": node.get("citation_label"),
        "page_label": node.get("page_label"),
        "char_start": node.get("char_start"),
        "char_end": node.get("char_end"),
        "text_hash": node.get("text_hash"),
        "content_sha256": node.get("content_sha256"),
        "artifact_sha256": node.get("artifact_sha256"),
        "parser_provenance": node.get("parser_provenance"),
        "evidence_span_ids": node.get("evidence_span_ids") or [],
    }


def _facts_by_type(facts: list[dict[str, Any]], fact_type: str) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if fact["fact_type"] == fact_type
        and fact.get("confidence_class") != "negative_context"
    ]


def _facts_by_types(
    facts: list[dict[str, Any]],
    fact_types: set[str],
) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if fact["fact_type"] in fact_types
        and fact.get("confidence_class") != "negative_context"
    ]


def _facts_by_subtype(
    facts: list[dict[str, Any]],
    fact_type: str,
    fact_subtype: str,
) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if fact["fact_type"] == fact_type
        and fact.get("fact_subtype") == fact_subtype
        and fact.get("confidence_class") != "negative_context"
    ]


def _supporting_document_signals(facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "purpose_need": [
            fact for fact in facts if fact.get("section_family") == "purpose_need"
        ],
        "alternatives": [
            fact
            for fact in facts
            if fact.get("section_family") in {"alternatives", "no_action"}
        ],
        "cumulative_effects": [
            fact for fact in facts if fact.get("section_family") == "cumulative_effects"
        ],
        "mitigation": [
            fact for fact in facts if fact.get("section_family") == "mitigation"
        ],
        "public_involvement": [
            fact for fact in facts if fact.get("section_family") == "public_involvement"
        ],
        "finding_decision": [
            fact for fact in facts if fact.get("section_family") == "finding_decision"
        ],
    }


def _section_node_for_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    section_label = _section_label(chunk)
    section_id = _node_id("package-section", section_label)
    chunk_id = str(chunk.get("chunk_id") or "unknown-chunk")
    return {
        "node_id": section_id,
        "node_type": "package_section",
        "label": section_label,
        "normalized_value": _safe_identifier(section_label),
        "confidence_class": "observed",
        "extraction_method": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
        "package_chunk_ids": [chunk_id],
        "section_ids": [section_id],
        "section_family": _section_family(chunk),
        "citation_label": chunk.get("citation_label"),
        "page_label": _page_label(chunk),
        "char_start": chunk.get("char_start"),
        "char_end": chunk.get("char_end"),
        "text_hash": chunk.get("content_sha256"),
        "content_sha256": chunk.get("content_sha256"),
        "artifact_sha256": chunk.get("artifact_sha256"),
        "parser_provenance": _parser_provenance(chunk),
        "evidence_span_ids": [],
    }


def _section_map(section_nodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    section_rows = []
    for node in section_nodes.values():
        section_rows.append(
            {
                "section_id": node["node_id"],
                "section_label": node["label"],
                "section_family": node["section_family"],
                "package_chunk_ids": sorted(node["package_chunk_ids"]),
                "citation_label": node["citation_label"],
                "page_label": node["page_label"],
            }
        )
    return sorted(section_rows, key=lambda row: str(row["section_id"]))


def _section_family_bindings(section_map: list[dict[str, Any]]) -> dict[str, list[str]]:
    bindings: dict[str, list[str]] = defaultdict(list)
    for row in section_map:
        bindings[str(row["section_family"])].append(str(row["section_id"]))
    return {
        family: sorted(section_ids)
        for family, section_ids in sorted(bindings.items())
    }


def _section_label(chunk: dict[str, Any]) -> str:
    heading = str(chunk.get("heading") or "").strip()
    section = str(chunk.get("section") or "").strip()
    title = str(chunk.get("title") or "").strip()
    if section and heading and section != heading:
        return f"{section} / {heading}"
    if section:
        return section
    if heading:
        return heading
    if title:
        return f"{title} unsectioned"
    return "unsectioned package content"


def _section_family(chunk: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(chunk.get("section") or ""),
            str(chunk.get("heading") or ""),
            str(chunk.get("text") or "")[:500],
        ]
    ).lower()
    patterns = (
        ("purpose_need", ("purpose and need", "need for action")),
        ("no_action", ("no action alternative", "no action")),
        ("alternatives", ("alternatives", "proposed action", "range of alternatives")),
        ("cumulative_effects", ("cumulative effects", "cumulative impact")),
        ("mitigation", ("mitigation", "design feature", "best management practice")),
        ("public_involvement", ("public involvement", "public comment", "scoping")),
        ("finding_decision", ("decision notice", "finding of no significant impact", "fonsi")),
        ("consultation", ("consultation", "section 7", "section 106")),
        ("affected_environment", ("affected environment", "environmental consequences")),
    )
    for family, terms in patterns:
        if any(term in text for term in terms):
            return family
    return "general"


def _find_term_matches(text: str, term: str) -> list[re.Match[str]]:
    term = " ".join(str(term or "").split())
    if not term:
        return []
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
    return list(pattern.finditer(text))


def _is_negative_location_match(text: str, start: int, end: int) -> bool:
    window = _sentence_around(text, start, end).lower()
    negative_phrases = (
        "not part of the project area",
        "outside the project area",
        "outside of the project area",
        "project is not in this area",
        "project is not within this area",
        "is not in the project area",
        "is not within the project area",
        "not affected by the project",
        "not affected by this project",
        "does not apply to the project area",
        "project does not include",
        "project does not contain",
        "project does not affect",
        "project does not pertain to",
        "no designated wilderness in the project area",
        "no research natural areas in the project area",
    )
    if any(phrase in window for phrase in negative_phrases):
        return True
    return bool(
        re.search(
            r"\b(?:there\s+(?:are|is)\s+no|no)\b.{0,180}\b"
            r"(?:in\s+the\s+project\s+area|affected\s+by\s+(?:the|this)\s+project)\b",
            window,
        )
    )


def _is_weak_signal_match(text: str, start: int, end: int) -> bool:
    return is_weak_signal_text(text, start, end)


def _sentence_around(text: str, start: int, end: int) -> str:
    sentence_start = max(
        text.rfind(".", 0, start),
        text.rfind("\n", 0, start),
        text.rfind(";", 0, start),
    )
    sentence_end_candidates = [
        index
        for index in (
            text.find(".", end),
            text.find("\n", end),
            text.find(";", end),
        )
        if index >= 0
    ]
    sentence_start = sentence_start + 1 if sentence_start >= 0 else 0
    sentence_end = min(sentence_end_candidates) + 1 if sentence_end_candidates else len(text)
    return text[sentence_start:sentence_end]


def _source_package_metadata(
    *,
    package_path: Path | None,
    package_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    artifact_paths = sorted(
        str(record.get("artifact_path"))
        for record in package_manifest
        if str(record.get("artifact_path") or "").strip()
    )
    source_record_ids = sorted(
        str(record.get("source_record_id"))
        for record in package_manifest
        if str(record.get("source_record_id") or "").strip()
    )
    parsers = sorted(
        {
            str(record.get("parser_name"))
            for record in package_manifest
            if str(record.get("parser_name") or "").strip()
        }
    )
    return {
        "package_path": str(package_path) if package_path else None,
        "artifact_paths": artifact_paths,
        "source_record_ids": source_record_ids,
        "parser_names": parsers,
        "extracted_file_count": sum(
            1 for record in package_manifest if record.get("status") == "extracted"
        ),
        "failed_file_count": sum(
            1 for record in package_manifest if record.get("status") != "extracted"
        ),
    }


def _source_set_id_from_authority_snapshot(applicability_dir: Path) -> str | None:
    snapshot_path = applicability_dir / "authority_universe_snapshot.json"
    if not snapshot_path.exists():
        return None
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict):
        return None
    value = str(snapshot.get("source_set_id") or "").strip()
    return value or None


def _source_set_id_from_package_chunks(package_chunks: list[dict[str, Any]]) -> str:
    values = sorted(
        {
            str(chunk.get("source_set_id"))
            for chunk in package_chunks
            if str(chunk.get("source_set_id") or "").strip()
        }
    )
    if len(values) == 1:
        return values[0]
    if values:
        return values[0]
    return "unknown-source-set"


def _absolute_offset(base: object, offset: int) -> int:
    try:
        return int(base) + offset
    except (TypeError, ValueError):
        return offset


def _page_label(chunk: dict[str, Any]) -> str | None:
    page = chunk.get("page")
    if page is None or str(page).strip() == "":
        return None
    return str(page)


def _parser_provenance(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "parser_name": chunk.get("parser_name"),
        "parser_version": chunk.get("parser_version"),
        "extracted_at": chunk.get("extracted_at"),
        "source_text_path": chunk.get("source_text_path"),
    }


def _context_excerpt(text: str, start: int, end: int, radius: int = 160) -> str:
    excerpt = text[max(0, start - radius) : min(len(text), end + radius)]
    return " ".join(excerpt.split())


def _dedupe_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = str(value or "").strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _node_id(*parts: str) -> str:
    readable = _safe_identifier("-".join(parts[:3]))
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()[:16]
    return f"{readable}-{digest}"


def _safe_identifier(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()
    return safe or "item"


def _validate_safe_segment(value: str, field_name: str) -> None:
    if not SAFE_SEGMENT_RE.fullmatch(str(value or "")):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    records = _read_jsonl(path)
    if not records:
        raise ValueError(f"Empty {label}: {path}")
    return records


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object lines in {path}")
        records.append(value)
    return records


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stable_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
