from __future__ import annotations

from pathlib import Path
import json

from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.applicability_retrieval import build_applicability_retrieval_traces
from usfs_r1_ea_sources.applicability_validation import apply_applicability_adjudication
from usfs_r1_ea_sources.applicability_validation import evaluate_applicability_adjudication
from usfs_r1_ea_sources.applicability_validation import validate_applicability_run
from usfs_r1_ea_sources.applicability_validation import (
    write_applicability_adjudication_template,
)
from usfs_r1_ea_sources.package_fact_graph import build_package_fact_graph
from usfs_r1_ea_sources.retrieval import _write_sqlite_index

from tests.support.applicability_decision_support import _forest_plan_candidate
from tests.support.applicability_decision_support import _source_chunks
from tests.support.applicability_decision_support import _write_json
from tests.support.applicability_decision_support import _write_jsonl
from tests.support.applicability_decision_support import _write_package_cache


def _build_adjudicated_applicability_dir(fixture: dict) -> Path:
    build_applicability_decisions(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
    )
    template_result = write_applicability_adjudication_template(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
    )
    template = json.loads(template_result.output_path.read_text(encoding="utf-8"))
    item = template["items"][0]
    item["final_status"] = "applicable"
    item["disposition"] = "human_applicable"
    item["adjudicated_at"] = "2026-05-04T00:00:00Z"
    item["adjudicated_by"] = ["unit-reviewer"]
    item["source_type"] = "test-adjudication"
    item["rationale"] = "The weak Clean Water Act signal is applicable for replay."
    item["supporting_citation_refs"] = sorted(
        set(item["supporting_citation_refs"] + ["EA-PACKAGE-001"])
    )
    _write_json(template_result.output_path, template)
    eval_result = evaluate_applicability_adjudication(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
        adjudication_file=template_result.output_path,
    )
    if not eval_result.summary["passed"]:
        raise AssertionError(eval_result.summary)
    apply_result = apply_applicability_adjudication(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
        adjudication_file=template_result.output_path,
    )
    if not apply_result.summary["passed"]:
        raise AssertionError(apply_result.summary)
    validation_result = validate_applicability_run(
        output_dir=fixture["output_dir"],
        review_id=fixture["review_id"],
        source_set_id=fixture["source_set_id"],
    )
    if not validation_result.summary["passed"]:
        raise AssertionError(validation_result.summary)
    return fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"


def _write_generated_rule_base_pack(root: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-pack",
        "version": "0.1.0",
        "title": "Unit Applicability Rule Pack",
        "domain": "Unit NEPA",
        "jurisdiction": "Unit Test",
        "rules": [
            _generated_base_rule(
                rule_id="baseline_nepa",
                source_record_id="R1EA-BASE",
                document_role="law",
                authority_category="law",
                applicability_mode="baseline",
            ),
            _generated_base_rule(
                rule_id="esa_consultation",
                source_record_id="R1EA-ESA",
                document_role="law",
                authority_category="law",
                applicability_mode="conditional",
                applies_if_package_terms=["Endangered Species Act"],
            ),
            _generated_base_rule(
                rule_id="ce_fanec",
                source_record_id="R1EA-CE",
                document_role="regulation",
                authority_category="regulation",
                applicability_mode="conditional",
                applies_if_package_terms=["Categorical Exclusion"],
            ),
            _generated_base_rule(
                rule_id="cwa_permit",
                source_record_id="R1EA-CWA",
                document_role="law",
                authority_category="law",
                applicability_mode="conditional",
                applies_if_package_terms=["Clean Water Act"],
            ),
            _generated_base_rule(
                rule_id="sioux_geography",
                source_record_id="R1EA-SIOUX",
                document_role="forest_plan",
                authority_category="forest_plan",
                applicability_mode="conditional",
                applies_if_package_terms=["Sioux Geographic Area"],
            ),
        ],
    }
    path = root / "generated-base-rule-pack.json"
    _write_json(path, rule_pack)
    return path


def _generated_base_rule(
    *,
    rule_id: str,
    source_record_id: str,
    document_role: str,
    authority_category: str,
    applicability_mode: str,
    applies_if_package_terms: list[str] | None = None,
) -> dict:
    package_terms = applies_if_package_terms or [rule_id.replace("_", " ")]
    rule = {
        "id": rule_id,
        "title": f"{rule_id} title",
        "authority_category": authority_category,
        "authority_source_record_id": source_record_id,
        "applicability_mode": applicability_mode,
        "question": f"Does the package address {rule_id}?",
        "requirement": f"The package should address {rule_id}.",
        "severity": "medium",
        "package_query": " ".join(package_terms),
        "package_terms": package_terms,
        "source_query": f"{rule_id} source authority",
        "source_filters": {
            "document_role": document_role,
            "source_record_id": source_record_id,
        },
        "evidence_expectation": "Requires source and package evidence.",
    }
    if applicability_mode == "conditional":
        rule["applies_if_package_terms"] = package_terms
    return rule


def _write_decision_fixture(
    root: Path,
    extra_candidates: list[dict] | None = None,
) -> dict:
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
        "candidate_authorities": [
            *_candidate_authorities(source_set_id),
            *(extra_candidates or []),
        ],
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
        _rule_candidate(
            source_set_id=source_set_id,
            rule_id="sioux_geography",
            source_record_id="R1EA-SIOUX",
            authority_category="forest_plan",
            applicability_mode="conditional",
            source_query="Sioux Geographic Area forest plan direction",
            package_query="Sioux Geographic Area",
            positive_trigger_groups=[["Sioux Geographic Area"]],
            negative_trigger_groups=[["Sioux Geographic Area"]],
        ),
        _forest_plan_candidate(source_set_id),
    ]


def _authority_family_candidate(source_set_id: str) -> dict:
    candidate = _rule_candidate(
        source_set_id=source_set_id,
        rule_id="clean_water_family_authority_template",
        source_record_id="R1EA-CWA",
        authority_category="law",
        applicability_mode="conditional",
        source_query="Clean Water Act source authority",
        package_query="wetlands",
        positive_trigger_groups=[["wetlands"]],
    )
    candidate["candidate_authority_id"] = (
        "authority-family-template:unit-authority-families:0.1.0:"
        "clean_water:clean_water_family_authority_template"
    )
    candidate["candidate_authority_type"] = "authority_family_rule_template"
    candidate["authority_family_id"] = "clean_water"
    candidate["package_section_filters"]["package_section_terms"] = ["water resources"]
    candidate["rule_template"].update(
        {
            "authority_family_template_set_id": "unit-authority-families",
            "authority_family_template_set_version": "0.1.0",
            "template_id": "clean_water_template",
            "authority_family_id": "clean_water",
            "authority_source_record_id": "R1EA-CWA",
            "authority_category": "law",
            "package_query": "wetlands",
            "package_terms": ["wetlands"],
            "package_section_terms": ["water resources"],
            "applies_if_package_terms": ["wetlands"],
            "applies_if_package_term_groups": [["wetlands"]],
            "does_not_apply_if_package_terms": ["no wetlands"],
            "source_query": "Clean Water Act source authority",
            "source_filters": {
                "document_role": "law",
                "source_record_id": "R1EA-CWA",
            },
            "evidence_expectation": "Requires source and package evidence.",
        }
    )
    candidate["required_source_evidence"]["requires_source_claim_linkage"] = False
    candidate["source_claim_link_ids"] = []
    return candidate


def _roads_access_arbitration_candidate(source_set_id: str) -> dict:
    candidate = _rule_candidate(
        source_set_id=source_set_id,
        rule_id="roads_access_arbitration",
        source_record_id="R1EA-ROAD",
        authority_category="regulation",
        applicability_mode="conditional",
        source_query="National Forest roads access right-of-way special use authority",
        package_query="road trail right-of-way grazing",
        positive_trigger_groups=[
            ["road"],
            ["trail"],
            ["right-of-way"],
            ["grazing"],
        ],
    )
    candidate["trigger_arbitration_contract"] = {
        "required_trigger_groups": [["road"], ["right-of-way"]],
        "minimum_strong_trigger_groups": 2,
        "positive_negative_conflict_policy": "needs_adjudication",
    }
    candidate["rule_template"].update(
        {
            "title": "Roads and access arbitration fixture",
            "question": "Does the package trigger roads/access authorities?",
            "requirement": "Apply roads/access authority when triggered.",
        }
    )
    return candidate


def _positive_negative_conflict_candidate(source_set_id: str) -> dict:
    candidate = _rule_candidate(
        source_set_id=source_set_id,
        rule_id="positive_negative_conflict",
        source_record_id="R1EA-ROAD",
        authority_category="regulation",
        applicability_mode="conditional",
        source_query="National Forest roads access right-of-way special use authority",
        package_query="road not part of the project area",
        positive_trigger_groups=[["road"]],
        negative_trigger_groups=[["not part of the project area"]],
    )
    candidate["rule_template"].update(
        {
            "title": "Positive negative arbitration fixture",
            "question": "Does the package contain conflicting road scope evidence?",
            "requirement": "Conflict should require adjudication.",
        }
    )
    return candidate


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
    negative_trigger_groups: list[list[str]] | None = None,
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
        "negative_trigger_groups": negative_trigger_groups or [],
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
            "negative_package_terms": [term for group in negative_trigger_groups or [] for term in group],
        },
    }
