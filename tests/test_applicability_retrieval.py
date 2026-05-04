from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_retrieval import (
    build_applicability_retrieval_traces,
)
from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.retrieval import _write_sqlite_index


class ApplicabilityRetrievalTraceTests(unittest.TestCase):
    def test_writes_retrieval_and_bounded_graph_traces_for_each_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_trace_fixture(root)

            result = build_applicability_retrieval_traces(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                retrieval_index_path=fixture["retrieval_index_path"],
                top_k=2,
                max_graph_paths_per_candidate=25,
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.retrieval_trace_path.exists())
            self.assertTrue(result.graph_trace_path.exists())
            self.assertTrue(result.diagnostics_path.exists())
            self.assertFalse(
                (result.applicability_dir / "applicability_decisions.jsonl").exists()
            )
            self.assertFalse((result.applicability_dir / "generated_rule_pack.json").exists())

            retrieval_rows = _read_jsonl(result.retrieval_trace_path)
            graph_rows = _read_jsonl(result.graph_trace_path)
            candidate_ids = set(fixture["candidate_contracts"])
            self.assertEqual(
                {row["candidate_authority_id"] for row in retrieval_rows},
                candidate_ids,
            )
            self.assertEqual(
                {row["candidate_authority_id"] for row in graph_rows},
                candidate_ids,
            )
            query_types = {row["query_type"] for row in retrieval_rows}
            self.assertIn("bm25", query_types)
            self.assertIn("metadata_filter", query_types)
            self.assertIn("package_section", query_types)
            self.assertIn("fused", query_types)
            citation_rows = [row for row in retrieval_rows if row["query_type"] == "citation"]
            self.assertTrue(citation_rows)
            self.assertTrue(any(row["ranked_results"] for row in citation_rows))

            selected_results = [
                result_row
                for row in retrieval_rows
                for result_row in row["ranked_results"]
                if result_row["selected_status"] == "selected"
            ]
            self.assertTrue(selected_results)
            for result_row in selected_results:
                has_source = result_row["source_record_id"] and result_row["source_chunk_id"]
                has_package = result_row["package_chunk_id"] or result_row.get(
                    "package_fact_node_id"
                )
                self.assertTrue(has_source or has_package, result_row["result_id"])
                self.assertTrue(result_row["text_hash"], result_row["result_id"])

            for row in graph_rows:
                allowed = fixture["candidate_contracts"][row["candidate_authority_id"]][
                    "relationship_types"
                ]
                max_depth = fixture["candidate_contracts"][row["candidate_authority_id"]][
                    "max_depth"
                ]
                self.assertLessEqual(row["traversal_depth"], max_depth)
                self.assertTrue(set(row["relationship_types"]) <= set(allowed))

            self.assertTrue(
                any("authority_category" in row["relationship_types"] for row in graph_rows)
            )
            self.assertTrue(
                any("rule_claim_link" in row["relationship_types"] for row in graph_rows)
            )
            self.assertTrue(any("source_claim" in row["relationship_types"] for row in graph_rows))
            self.assertTrue(
                any(
                    row["evidence_references"]["rule_claim_link_ids"]
                    for row in graph_rows
                )
            )
            self.assertTrue(
                any(
                    row["evidence_references"]["authority_categories"]
                    for row in graph_rows
                )
            )
            supporting_source_ids = {
                source_record_id
                for row in graph_rows
                for source_record_id in row["evidence_references"]["source_record_ids"]
                if source_record_id.endswith("-SUPPORT") or source_record_id == "R1PLAN-CG"
            }
            self.assertTrue(supporting_source_ids)

    def test_cli_writes_trace_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_trace_fixture(root)

            exit_code = main(
                [
                    "applicability-retrieve",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                    "--retrieval-index-path",
                    str(fixture["retrieval_index_path"]),
                    "--top-k",
                    "2",
                ]
            )

            self.assertEqual(exit_code, 0)
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            self.assertTrue((applicability_dir / "applicability_retrieval_trace.jsonl").exists())
            self.assertTrue((applicability_dir / "applicability_graph_trace.jsonl").exists())

    def test_excessive_graph_fanout_is_diagnosed_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_trace_fixture(root, extra_package_fact_count=10)

            result = build_applicability_retrieval_traces(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
                retrieval_index_path=fixture["retrieval_index_path"],
                top_k=2,
                max_graph_paths_per_candidate=1,
            )

            diagnostics = json.loads(result.diagnostics_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["validation_passed"])
            self.assertIn(
                "excessive_graph_fan_out",
                {
                    item["diagnostic_type"]
                    for item in diagnostics["diagnostics"]
                },
            )
            graph_rows = _read_jsonl(result.graph_trace_path)
            row_counts = {}
            for row in graph_rows:
                row_counts[row["candidate_authority_id"]] = (
                    row_counts.get(row["candidate_authority_id"], 0) + 1
                )
            self.assertTrue(all(count <= 1 for count in row_counts.values()))


def _write_trace_fixture(root: Path, *, extra_package_fact_count: int = 0) -> dict:
    output_dir = root / "source_library"
    review_id = "trace-unit"
    source_set_id = "source-set-unit"
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    applicability_dir.mkdir(parents=True, exist_ok=True)
    retrieval_index_path = (
        output_dir / "derived" / source_set_id / "retrieval" / "evidence_index.sqlite"
    )
    retrieval_index_path.parent.mkdir(parents=True, exist_ok=True)
    chunks = _source_chunks(source_set_id)
    chunks_path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    _write_jsonl(chunks_path, chunks)
    _write_sqlite_index(
        retrieval_index_path,
        source_set_id=source_set_id,
        chunks=chunks,
        chunks_path=chunks_path,
        catalog_sqlite_path=output_dir / "catalog" / "review_sources.sqlite",
    )
    package_graph = _package_fact_graph(
        review_id=review_id,
        source_set_id=source_set_id,
        extra_package_fact_count=extra_package_fact_count,
    )
    _write_json(applicability_dir / "package_fact_graph.json", package_graph)
    claims_dir = output_dir / "derived" / source_set_id / "claims"
    rule_claim_links_path = claims_dir / "rule_claim_links.jsonl"
    claims_path = claims_dir / "claims.jsonl"
    _write_jsonl(rule_claim_links_path, _rule_claim_links())
    _write_jsonl(claims_path, _source_claims())
    candidate_contracts = _candidate_contracts()
    authority_universe = {
        "schema_version": "authority-universe-snapshot-v0",
        "authority_universe_id": "authority-universe:trace-unit",
        "authority_universe_sha256": "authority-universe-sha",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "artifact_paths": {
            "rule_claim_links_path": str(rule_claim_links_path),
            "claims_path": str(claims_path),
        },
        "candidate_authorities": list(candidate_contracts.values()),
    }
    _write_json(applicability_dir / "authority_universe_snapshot.json", authority_universe)
    return {
        "output_dir": output_dir,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "retrieval_index_path": retrieval_index_path,
        "candidate_contracts": {
            candidate_id: candidate["graph_expansion_contract"]
            for candidate_id, candidate in candidate_contracts.items()
        },
    }


def _candidate_contracts() -> dict[str, dict]:
    return {
        "rule-template:unit-pack:0.1.0:ce_fanec": _rule_candidate(
            rule_id="ce_fanec",
            title="CEQ and FANEC NEPA procedure",
            source_record_id="R1EA-CE",
            authority_category="regulation",
            source_query="CEQ FANEC NEPA environmental assessment",
            package_query="environmental assessment",
            required_package_fact_types=["action", "nepa_level"],
        ),
        "rule-template:unit-pack:0.1.0:esa_nhpa_mbta": _rule_candidate(
            rule_id="esa_nhpa_mbta",
            title="ESA NHPA MBTA consultation",
            source_record_id="R1EA-ESA",
            authority_category="law",
            source_query="Endangered Species Act NHPA MBTA consultation",
            package_query="Endangered Species Act Section 106 Migratory Bird Treaty Act",
            required_package_fact_types=["consultation"],
        ),
        "rule-template:unit-pack:0.1.0:wetlands_roadless": _rule_candidate(
            rule_id="wetlands_roadless",
            title="Wetlands floodplains and roadless",
            source_record_id="R1EA-WET",
            authority_category="policy",
            source_query="Clean Water Act wetlands floodplains roadless",
            package_query="Clean Water Act wetlands roadless",
            required_package_fact_types=["permit", "overlay"],
        ),
        "forest-plan-component:unit-inventory:STD-FP-01": _forest_plan_candidate(),
    }


def _rule_candidate(
    *,
    rule_id: str,
    title: str,
    source_record_id: str,
    authority_category: str,
    source_query: str,
    package_query: str,
    required_package_fact_types: list[str],
) -> dict:
    candidate_id = f"rule-template:unit-pack:0.1.0:{rule_id}"
    relationship_types = [
        "source_record",
        "authority_category",
        "source_claim",
        "rule_claim_link",
        "package_fact",
        "evidence_span",
        "exception",
        "dependency",
        "supersession",
    ]
    return {
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": "rule_template",
        "source_set_id": "source-set-unit",
        "authority_category": authority_category,
        "authority_document_role": authority_category,
        "source_record_ids": [source_record_id],
        "source_records": [
            {
                "source_record_id": source_record_id,
                "title": title,
                "citation_label": f"{source_record_id} | {title}",
            }
        ],
        "required_package_fact_types": required_package_fact_types,
        "positive_trigger_groups": [[package_query]],
        "negative_trigger_groups": [],
        "source_role_filters": {
            "source_record_ids": [source_record_id],
            "document_roles": [authority_category],
            "authority_categories": [authority_category],
            "source_filters": {
                "source_record_id": source_record_id,
                "document_role": authority_category,
            },
        },
        "package_section_filters": {
            "package_query": package_query,
            "package_terms": [package_query],
            "package_section_terms": [],
            "preferred_section_families": [],
        },
        "required_source_evidence": {"requires_source_record": True},
        "retrieval_contract": {
            "contract_type": "rule_template_retrieval",
            "query_plan_id": f"retrieval-plan:rule-template:{rule_id}",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "optional_query_types": ["vector"],
            "source_queries": [source_query],
            "package_queries": [package_query],
            "source_role_filters": {},
            "package_section_filters": {},
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "rule_template_graph_expansion",
            "start_node_types": ["rule_template", "source_record", "authority"],
            "relationship_types": relationship_types,
            "max_depth": 2,
            "requires_path_trace": True,
            "neighbor_filters": {"source_record_ids": [source_record_id]},
        },
        "dependency_contract": {
            "dependency_rule_ids": [],
            "exception_rule_ids": [],
            "supersedes_rule_ids": [],
            "supporting_source_record_ids": [f"{source_record_id}-SUPPORT"],
        },
        "rule_template": {
            "base_rule_pack_id": "unit-pack",
            "base_rule_pack_version": "0.1.0",
            "rule_id": rule_id,
            "title": title,
            "question": title,
            "requirement": title,
            "severity": "medium",
            "applicability_mode": "conditional",
        },
    }


def _forest_plan_candidate() -> dict:
    relationship_types = [
        "forest_plan_profile",
        "component_inventory",
        "source_record",
        "source_chunk",
        "geography",
        "management_area",
        "overlay",
        "package_fact",
        "evidence_span",
    ]
    return {
        "candidate_authority_id": "forest-plan-component:unit-inventory:STD-FP-01",
        "candidate_authority_type": "forest_plan_component",
        "source_set_id": "source-set-unit",
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
            "source_filters": {"source_record_id": "R1PLAN-CG"},
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
            "optional_query_types": ["vector"],
            "source_queries": ["Crazy Mountains Backcountry Area"],
            "package_queries": ["Crazy Mountains Backcountry Area"],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "forest_plan_component_graph_expansion",
            "start_node_types": ["forest_plan_component", "source_record", "package_fact"],
            "relationship_types": relationship_types,
            "max_depth": 3,
            "requires_path_trace": True,
            "neighbor_filters": {
                "forest_unit_id": "custer-gallatin-nf",
                "component_ids": ["STD-FP-01"],
            },
        },
        "dependency_contract": {"supporting_source_record_ids": ["R1PLAN-CG"]},
        "forest_plan": {
            "forest_unit_id": "custer-gallatin-nf",
            "component_inventory_id": "unit-inventory",
            "component_id": "STD-FP-01",
            "section_heading": "Crazy Mountains Backcountry Area standard",
            "geographic_area_ids": ["geo-bridger-bangtail-crazy"],
            "management_area_ids": ["mgmt-crazy-mountains-bca"],
            "overlay_ids": ["overlay-inventoried-roadless"],
        },
    }


def _source_chunks(source_set_id: str) -> list[dict]:
    return [
        _chunk(
            source_set_id,
            "R1EA-CE",
            "regulation",
            "regulation",
            "CEQ and FANEC NEPA environmental assessment procedure for EAs.",
        ),
        _chunk(
            source_set_id,
            "R1EA-ESA",
            "law",
            "law",
            "Endangered Species Act, NHPA Section 106, and MBTA consultation requirements.",
        ),
        _chunk(
            source_set_id,
            "R1EA-WET",
            "policy",
            "policy",
            "Clean Water Act wetlands floodplains and roadless area review.",
        ),
        _chunk(
            source_set_id,
            "R1PLAN-CG",
            "forest_plan",
            "forest_plan",
            "Crazy Mountains Backcountry Area standard in the Custer Gallatin Forest Plan.",
        ),
    ]


def _chunk(
    source_set_id: str,
    source_record_id: str,
    document_role: str,
    authority_level: str,
    text: str,
) -> dict:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"{source_record_id}-chunk-0",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": f"{source_record_id} title",
        "document_role": document_role,
        "authority_level": authority_level,
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
        "review_topics": [authority_level],
        "text": text,
    }


def _package_fact_graph(
    *,
    review_id: str,
    source_set_id: str,
    extra_package_fact_count: int,
) -> dict:
    nodes = [
        _package_fact("action", "project_action_type", "land_exchange", "land exchange"),
        _package_fact("nepa_level", "analysis_level", "environmental_assessment", "EA"),
        _package_fact("consultation", "esa", "esa", "Endangered Species Act Section 7"),
        _package_fact("consultation", "nhpa", "nhpa", "National Historic Preservation Act"),
        _package_fact("consultation", "mbta", "mbta", "Migratory Bird Treaty Act"),
        _package_fact("permit", "clean_water_act", "clean_water_act", "Clean Water Act"),
        _package_fact("permit", "wetlands_floodplains", "wetlands", "wetlands"),
        _package_fact("overlay", "overlay", "overlay-inventoried-roadless", "roadless"),
        _package_fact("geography", "geographic_area", "geo-bridger-bangtail-crazy", "geography"),
        _package_fact("management_area", "management_area", "mgmt-crazy-mountains-bca", "area"),
    ]
    for index in range(extra_package_fact_count):
        nodes.append(
            _package_fact(
                "resource_topic",
                "resource",
                f"extra-resource-{index}",
                f"extra resource {index}",
            )
        )
    return {
        "schema_version": "package-fact-graph-v0",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "package_fact_graph_id": "package-fact-graph:trace-unit",
        "package_fact_graph_sha256": "package-graph-sha",
        "nodes": nodes,
        "edges": [],
        "validation": {"passed": True, "checks": []},
    }


def _rule_claim_links() -> list[dict]:
    return [
        {
            "link_id": "link-ce",
            "rule_id": "ce_fanec",
            "claim_id": "claim-ce",
            "source_record_id": "R1EA-CE",
        },
        {
            "link_id": "link-esa",
            "rule_id": "esa_nhpa_mbta",
            "claim_id": "claim-esa",
            "source_record_id": "R1EA-ESA",
        },
        {
            "link_id": "link-wet",
            "rule_id": "wetlands_roadless",
            "claim_id": "claim-wet",
            "source_record_id": "R1EA-WET",
        },
    ]


def _source_claims() -> list[dict]:
    return [
        {"claim_id": "claim-ce", "source_record_id": "R1EA-CE"},
        {"claim_id": "claim-esa", "source_record_id": "R1EA-ESA"},
        {"claim_id": "claim-wet", "source_record_id": "R1EA-WET"},
    ]


def _package_fact(node_type: str, fact_subtype: str, normalized_value: str, raw: str) -> dict:
    node_id = f"fact-{node_type}-{normalized_value}"
    digest = hashlib.sha256(node_id.encode("utf-8")).hexdigest()
    return {
        "node_id": node_id,
        "node_type": node_type,
        "fact_subtype": fact_subtype,
        "label": raw,
        "raw_value": raw,
        "normalized_value": normalized_value,
        "confidence_class": "observed",
        "package_chunk_ids": [f"package-chunk-{normalized_value}"],
        "section_ids": ["section-1"],
        "section_family": "affected_environment",
        "citation_label": "EA-PACKAGE-001",
        "page_label": "1",
        "char_start": 10,
        "char_end": 20,
        "chunk_char_start": 10,
        "chunk_char_end": 20,
        "text_hash": digest,
        "content_sha256": digest,
        "artifact_sha256": digest,
        "context_excerpt": raw,
        "evidence_span_ids": [f"span-{node_id}"],
        "package_span_ids": [f"span-{node_id}"],
        "parser_provenance": {"parser_name": "unit-parser"},
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
