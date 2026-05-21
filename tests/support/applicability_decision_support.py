from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _forest_plan_candidate(source_set_id: str) -> dict:
    return {
        "candidate_authority_id": "forest-plan-component:unit-inventory:STD-FP-01",
        "candidate_authority_type": "forest_plan_component",
        "source_set_id": source_set_id,
        "authority_category": "forest_plan",
        "authority_document_role": "forest_plan",
        "source_record_ids": ["R1PLAN-CG"],
        "source_records": [
            {
                "source_record_id": "R1PLAN-CG",
                "title": "Custer Gallatin Forest Plan",
                "citation_label": "R1PLAN-CG | Custer Gallatin Forest Plan",
            }
        ],
        "required_package_fact_types": ["geography", "management_area", "overlay"],
        "positive_trigger_groups": [["Crazy Mountains Backcountry Area"]],
        "negative_trigger_groups": [],
        "source_role_filters": {
            "source_record_ids": ["R1PLAN-CG"],
            "document_roles": ["forest_plan"],
            "authority_categories": ["forest_plan"],
        },
        "package_section_filters": {
            "package_evidence_terms": ["Crazy Mountains Backcountry Area"],
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
        "required_source_evidence": {"requires_source_record": True},
        "retrieval_contract": {
            "contract_type": "forest_plan_component_retrieval",
            "query_plan_id": "retrieval-plan:forest-plan-component:STD-FP-01",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "source_queries": ["Crazy Mountains Backcountry Area"],
            "package_queries": ["Crazy Mountains Backcountry Area"],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "forest_plan_component_graph_expansion",
            "start_node_types": ["forest_plan_component", "source_record", "package_fact"],
            "relationship_types": [
                "forest_plan_profile",
                "component_inventory",
                "source_record",
                "source_chunk",
                "geography",
                "management_area",
                "overlay",
                "package_fact",
                "evidence_span",
            ],
            "max_depth": 3,
            "requires_path_trace": True,
        },
        "dependency_contract": {"supporting_source_record_ids": ["R1PLAN-CG"]},
        "search_coverage_requirements": [
            {
                "coverage_class": "forest_plan_scope_miss",
                "required_query_types": [
                    "exact_keyword",
                    "bm25",
                    "metadata_filter",
                    "package_section",
                ],
                "required_artifacts": [
                    "package_fact_graph",
                    "applicability_retrieval_trace",
                    "applicability_graph_trace",
                    "search_coverage_certificates",
                ],
            }
        ],
        "forest_plan": {
            "forest_unit_id": "custer-gallatin-nf",
            "component_inventory_id": "unit-inventory",
            "component_id": "STD-FP-01",
            "component_type": "standard",
            "section_heading": "Crazy Mountains Backcountry Area standard",
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_chunk_count": 1,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "forest_plan_component",
            "component_type": "standard",
            "package_evidence_terms": ["Crazy Mountains Backcountry Area"],
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
    }


def _forest_plan_scope_miss_candidate(source_set_id: str) -> dict:
    candidate = _forest_plan_candidate(source_set_id)
    candidate["candidate_authority_id"] = (
        "forest-plan-component:unit-inventory:STD-FP-MISS"
    )
    candidate["positive_trigger_groups"] = [["Absent Forest Plan Area"]]
    candidate["package_section_filters"] = {
        "package_evidence_terms": ["Absent Forest Plan Area"],
        "geographic_area_ids": ["geo-absent"],
        "management_area_ids": ["mgmt-absent"],
        "overlay_ids": [],
    }
    candidate["retrieval_contract"]["query_plan_id"] = (
        "retrieval-plan:forest-plan-component:STD-FP-MISS"
    )
    candidate["retrieval_contract"]["source_queries"] = [
        "Crazy Mountains Backcountry Area"
    ]
    candidate["retrieval_contract"]["package_queries"] = ["Absent Forest Plan Area"]
    candidate["forest_plan"] = {
        **candidate["forest_plan"],
        "component_id": "STD-FP-MISS",
        "geographic_area_ids": ["geo-absent"],
        "management_area_ids": ["mgmt-absent"],
        "overlay_ids": [],
    }
    candidate["deterministic_applicability_test_contract"] = {
        **candidate["deterministic_applicability_test_contract"],
        "package_evidence_terms": ["Absent Forest Plan Area"],
        "geographic_area_ids": ["geo-absent"],
        "management_area_ids": ["mgmt-absent"],
        "overlay_ids": [],
    }
    return candidate


def _write_package_cache(output_dir: Path, review_id: str) -> None:
    package_dir = output_dir / "reviews" / review_id / "package"
    artifact_sha256 = hashlib.sha256(review_id.encode("utf-8")).hexdigest()
    manifest = [
        {
            "source_set_id": f"ea-package-{review_id}",
            "source_record_id": "EA-PACKAGE-001",
            "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
            "artifact_path": "/tmp/East Crazy Inspiration Divide Land Exchange EA.pdf",
            "artifact_sha256": artifact_sha256,
            "artifact_byte_size": 1000,
            "content_type": "application/pdf",
            "citation_label": "EA-PACKAGE-001",
            "extracted_at": "2026-05-04T00:00:00Z",
            "status": "extracted",
            "parser_name": "unit-parser",
            "parser_version": "1.0",
            "text_path": "/tmp/east-crazy.txt",
            "text_sha256": artifact_sha256,
            "text_char_count": 1000,
            "chunk_count": 3,
        }
    ]
    chunks = [
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=0,
            section="Purpose and Need",
            heading="Purpose and Need",
            text=(
                "The East Crazy Inspiration Divide Land Exchange Project is an "
                "environmental assessment on the Custer Gallatin National Forest."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=1,
            section="Affected Environment",
            heading="Forest Plan Consistency",
            text=(
                "The project area is in the Bridger, Bangtail, and Crazy Mountains "
                "Geographic Area and the Crazy Mountains Backcountry Area. It also "
                "intersects an Inventoried Roadless Area. The Sioux Geographic Area "
                "is not part of the project area."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=2,
            section="Environmental Consequences",
            heading="Resources and Consultation",
            text=(
                "The package identifies Endangered Species Act Section 7 consultation, "
                "wetlands, and floodplains. A Clean Water Act Section 404 permit may "
                "be required."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=3,
            section="Proposed Action",
            heading="Roads and Access",
            text=(
                "The Proposed Action reserves Right-of-Way for Big Timber Creek Road "
                "No. 197."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=4,
            section="Proposed Action",
            heading="Trail Access",
            text=(
                "Trail easements could be required if needed for final design across "
                "private land."
            ),
        ),
        _package_chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=5,
            section="Environmental Consequences",
            heading="Cumulative Effects",
            text=(
                "Effects from livestock grazing may be possible in the cumulative "
                "effects area."
            ),
        ),
    ]
    manifest[0]["text_char_count"] = sum(len(chunk["text"]) for chunk in chunks)
    manifest[0]["chunk_count"] = len(chunks)
    _write_jsonl(package_dir / "package_manifest.jsonl", manifest)
    _write_jsonl(package_dir / "package_chunks.jsonl", chunks)


def _package_chunk(
    *,
    review_id: str,
    artifact_sha256: str,
    index: int,
    section: str,
    heading: str,
    text: str,
) -> dict:
    return {
        "chunk_id": f"package-chunk-{index}",
        "source_set_id": f"ea-package-{review_id}",
        "source_record_id": "EA-PACKAGE-001",
        "chunk_index": index,
        "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
        "document_role": "ea_package",
        "support_document_role": "ea_package",
        "authority_level": "project_record",
        "artifact_sha256": artifact_sha256,
        "artifact_path": "/tmp/East Crazy Inspiration Divide Land Exchange EA.pdf",
        "citation_label": "EA-PACKAGE-001",
        "parser_name": "unit-parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-04T00:00:00Z",
        "source_text_path": "/tmp/east-crazy.txt",
        "char_start": index * 1000,
        "char_end": index * 1000 + len(text),
        "page": index + 1,
        "section": section,
        "heading": heading,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }


def _source_chunks(source_set_id: str) -> list[dict]:
    return [
        _source_chunk(source_set_id, "R1EA-BASE", "law", "NEPA EA baseline authority."),
        _source_chunk(source_set_id, "R1EA-ESA", "law", "Endangered Species Act consultation."),
        _source_chunk(source_set_id, "R1EA-CE", "regulation", "FANEC categorical exclusion."),
        _source_chunk(source_set_id, "R1EA-CWA", "law", "Clean Water Act permit authority."),
        _source_chunk(
            source_set_id,
            "R1EA-SIOUX",
            "forest_plan",
            "Sioux Geographic Area forest plan direction.",
        ),
        _source_chunk(
            source_set_id,
            "R1EA-ROAD",
            "regulation",
            "National Forest roads access right-of-way special use authority.",
        ),
        _source_chunk(
            source_set_id,
            "R1PLAN-CG",
            "forest_plan",
            "Crazy Mountains Backcountry Area Forest Plan standard.",
        ),
    ]


def _source_chunk(source_set_id: str, source_record_id: str, role: str, text: str) -> dict:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"{source_record_id}-chunk-0",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": f"{source_record_id} title",
        "document_role": role,
        "support_document_role": role,
        "authority_level": role,
        "host": "example.test",
        "expected_parser": "text",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"/tmp/{source_record_id}.txt",
        "citation_label": f"{source_record_id} citation",
        "original_url": f"https://example.test/{source_record_id}",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit-parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-04T00:00:00Z",
        "source_text_path": f"/tmp/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": 1,
        "section": "Authority Text",
        "heading": "Authority Text",
        "content_sha256": digest,
        "review_topics": [role],
        "text": text,
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
