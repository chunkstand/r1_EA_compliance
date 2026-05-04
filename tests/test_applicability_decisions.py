from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.applicability_retrieval import build_applicability_retrieval_traces
from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.package_fact_graph import build_package_fact_graph
from usfs_r1_ea_sources.retrieval import _write_sqlite_index


class ApplicabilityDecisionTests(unittest.TestCase):
    def test_writes_first_class_applicability_decision_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))

            result = build_applicability_decisions(
                output_dir=fixture["output_dir"],
                review_id=fixture["review_id"],
                source_set_id=fixture["source_set_id"],
            )

            self.assertTrue(result.summary["validation_passed"])
            self.assertFalse(result.summary["generated_rule_pack_ready"])
            self.assertTrue(result.decisions_path.exists())
            self.assertTrue(result.applicable_authorities_path.exists())
            self.assertTrue(result.non_applicable_authorities_path.exists())
            self.assertTrue(result.search_coverage_certificates_path.exists())
            self.assertTrue(result.provenance_path.exists())
            self.assertTrue(result.report_path.exists())
            self.assertFalse((result.applicability_dir / "generated_rule_pack.json").exists())
            self.assertFalse((result.applicability_dir / "compliance_matrix.json").exists())

            decisions = {
                row["candidate_authority_id"]: row for row in _read_jsonl(result.decisions_path)
            }
            self.assertEqual(len(decisions), 5)
            self.assertEqual(
                decisions["rule-template:unit-pack:0.1.0:baseline_nepa"]["status"],
                "applicable",
            )
            self.assertEqual(
                decisions["rule-template:unit-pack:0.1.0:esa_consultation"]["status"],
                "applicable",
            )
            ce_decision = decisions["rule-template:unit-pack:0.1.0:ce_fanec"]
            self.assertEqual(ce_decision["status"], "not_applicable")
            self.assertEqual(ce_decision["basis_type"], "absent_trigger_evidence")
            self.assertTrue(ce_decision["search_coverage_certificate_ids"])
            self.assertTrue(ce_decision["explicit_trigger_miss_evidence"])

            weak_decision = decisions["rule-template:unit-pack:0.1.0:cwa_permit"]
            self.assertEqual(weak_decision["status"], "needs_adjudication")
            self.assertEqual(weak_decision["basis_type"], "unresolved_evidence_conflict")
            self.assertTrue(weak_decision["contradiction_notes"])

            component_id = "forest-plan-component:unit-inventory:STD-FP-01"
            self.assertEqual(decisions[component_id]["status"], "applicable")
            self.assertEqual(decisions[component_id]["basis_type"], "forest_plan_component")

            applicable = json.loads(
                result.applicable_authorities_path.read_text(encoding="utf-8")
            )
            non_applicable = json.loads(
                result.non_applicable_authorities_path.read_text(encoding="utf-8")
            )
            coverage = json.loads(
                result.search_coverage_certificates_path.read_text(encoding="utf-8")
            )
            self.assertEqual(applicable["schema_version"], "applicable-authorities-v0")
            self.assertEqual(non_applicable["schema_version"], "non-applicable-authorities-v0")
            self.assertEqual(applicable["applicable_authority_count"], 3)
            self.assertEqual(non_applicable["non_applicable_authority_count"], 1)
            self.assertEqual(
                {row["candidate_authority_id"] for row in non_applicable["authorities"]},
                {"rule-template:unit-pack:0.1.0:ce_fanec"},
            )
            ce_certificates = [
                cert
                for cert in coverage["certificates"]
                if cert["covered_candidate_authority_ids"]
                == ["rule-template:unit-pack:0.1.0:ce_fanec"]
            ]
            self.assertEqual(len(ce_certificates), 1)
            self.assertEqual(ce_certificates[0]["coverage_result"], "sufficient")
            self.assertIn("package_section", ce_certificates[0]["executed_query_variants"])

    def test_cli_writes_decision_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_decision_fixture(Path(tmp))

            exit_code = main(
                [
                    "applicability-determine",
                    "--output-dir",
                    str(fixture["output_dir"]),
                    "--review-id",
                    fixture["review_id"],
                    "--source-set-id",
                    fixture["source_set_id"],
                ]
            )

            self.assertEqual(exit_code, 0)
            applicability_dir = (
                fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
            )
            self.assertTrue((applicability_dir / "applicability_decisions.jsonl").exists())
            self.assertTrue((applicability_dir / "applicable_authorities.json").exists())
            self.assertTrue((applicability_dir / "non_applicable_authorities.json").exists())
            self.assertTrue((applicability_dir / "search_coverage_certificates.json").exists())
            self.assertTrue((applicability_dir / "applicability_provenance.json").exists())
            self.assertTrue((applicability_dir / "applicability_report.md").exists())


def _write_decision_fixture(root: Path) -> dict:
    output_dir = root / "source_library"
    review_id = "east-crazy-applicability"
    source_set_id = "source-set-unit"
    _write_package_cache(output_dir, review_id)
    build_package_fact_graph(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
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
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    authority_universe = {
        "schema_version": "authority-universe-snapshot-v0",
        "created_at": "2026-05-04T00:00:00Z",
        "authority_universe_id": "authority-universe:unit",
        "authority_universe_sha256": "authority-universe-sha",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "catalog_sha256": "catalog-sha",
        "artifact_paths": {},
        "candidate_authorities": _candidate_authorities(source_set_id),
        "validation": {"passed": True, "checks": []},
    }
    _write_json(applicability_dir / "authority_universe_snapshot.json", authority_universe)
    build_applicability_retrieval_traces(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        retrieval_index_path=retrieval_index_path,
        top_k=3,
        max_graph_paths_per_candidate=20,
    )
    return {
        "output_dir": output_dir,
        "review_id": review_id,
        "source_set_id": source_set_id,
    }


def _candidate_authorities(source_set_id: str) -> list[dict]:
    return [
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="baseline_nepa",
            source_record_id="R1EA-BASE",
            authority_category="law",
            applicability_mode="baseline",
            source_query="NEPA environmental assessment baseline authority",
            package_query="environmental assessment",
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="esa_consultation",
            source_record_id="R1EA-ESA",
            authority_category="law",
            applicability_mode="conditional",
            source_query="Endangered Species Act consultation",
            package_query="Endangered Species Act",
            positive_trigger_groups=[["Endangered Species Act"]],
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="ce_fanec",
            source_record_id="R1EA-CE",
            authority_category="regulation",
            applicability_mode="conditional",
            source_query="categorical exclusion FANEC",
            package_query="Categorical Exclusion",
            positive_trigger_groups=[["Categorical Exclusion"]],
        ),
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="cwa_permit",
            source_record_id="R1EA-CWA",
            authority_category="law",
            applicability_mode="conditional",
            source_query="Clean Water Act permit",
            package_query="Clean Water Act",
            positive_trigger_groups=[["Clean Water Act"]],
        ),
        _forest_plan_candidate(source_set_id),
    ]


def _rule_candidate(
    *,
    source_set_id: str,
    rule_id: str,
    source_record_id: str,
    authority_category: str,
    applicability_mode: str,
    source_query: str,
    package_query: str,
    positive_trigger_groups: list[list[str]] | None = None,
) -> dict:
    candidate_id = f"rule-template:unit-pack:0.1.0:{rule_id}"
    return {
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": "rule_template",
        "source_set_id": source_set_id,
        "authority_category": authority_category,
        "authority_document_role": authority_category,
        "source_record_ids": [source_record_id],
        "source_records": [
            {
                "source_record_id": source_record_id,
                "title": f"{rule_id} authority",
                "citation_label": f"{source_record_id} | {rule_id} authority",
            }
        ],
        "required_package_fact_types": ["action", "nepa_level", "resource_topic"],
        "positive_trigger_groups": positive_trigger_groups or [],
        "negative_trigger_groups": [],
        "source_role_filters": {
            "source_record_ids": [source_record_id],
            "document_roles": [authority_category],
            "authority_categories": [authority_category],
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
            "query_plan_id": f"retrieval-plan:{rule_id}",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "source_queries": [source_query],
            "package_queries": [package_query],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "rule_template_graph_expansion",
            "start_node_types": ["rule_template", "source_record", "authority"],
            "relationship_types": [
                "source_record",
                "authority_category",
                "source_claim",
                "rule_claim_link",
                "package_fact",
                "evidence_span",
                "exception",
                "dependency",
                "supersession",
            ],
            "max_depth": 2,
            "requires_path_trace": True,
        },
        "dependency_contract": {
            "dependency_rule_ids": [],
            "exception_rule_ids": [],
            "supersedes_rule_ids": [],
        },
        "search_coverage_requirements": [
            {
                "coverage_class": "positive_trigger_miss",
                "required_query_types": [
                    "exact_keyword",
                    "bm25",
                    "metadata_filter",
                    "package_section",
                ],
                "required_artifacts": [
                    "package_fact_graph",
                    "applicability_retrieval_trace",
                    "search_coverage_certificates",
                ],
            }
        ],
        "rule_template": {
            "base_rule_pack_id": "unit-pack",
            "base_rule_pack_version": "0.1.0",
            "rule_id": rule_id,
            "title": f"{rule_id} authority",
            "question": f"Does {rule_id} apply?",
            "requirement": f"Apply {rule_id} when triggered.",
            "severity": "medium",
            "applicability_mode": applicability_mode,
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_claim_link_count": 1,
            "rule_claim_gap_count": 0,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "rule_template",
            "applicability_mode": applicability_mode,
            "baseline_required": applicability_mode == "baseline",
            "positive_package_term_groups": positive_trigger_groups or [],
            "negative_package_terms": [],
        },
    }


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
                "intersects an Inventoried Roadless Area."
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
    ]
    manifest[0]["text_char_count"] = sum(len(chunk["text"]) for chunk in chunks)
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
