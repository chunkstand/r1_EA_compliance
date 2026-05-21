from __future__ import annotations

from pathlib import Path

from tests.support.nepa_knowledge_graph_export_fixtures import _write_json
from tests.support.nepa_knowledge_graph_export_fixtures import _write_jsonl


def _write_minimal_review_overlay(
    output_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
) -> None:
    review_dir = output_dir / "reviews" / review_id
    applicability_dir = review_dir / "applicability"
    authority_universe_sha256 = "authority-universe-sha"
    _write_json(
        applicability_dir / "authority_universe_snapshot.json",
        {
            "schema_version": "applicability-authority-universe-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "authority_universe_sha256": authority_universe_sha256,
            "candidate_authorities": [
                {
                    "candidate_authority_id": "rule-template:nepa-ea-v0:0.1.0:nepa_rule",
                    "candidate_authority_type": "rule_template",
                    "authority_category": "law",
                    "source_record_ids": ["R1EA-001"],
                    "deterministic_applicability_test_contract": {
                        "rule_id": "nepa_rule",
                        "applicability_mode": "baseline",
                    },
                },
                {
                    "candidate_authority_id": (
                        "forest-plan-component:test-inventory:R1PLAN-001-FW-STD-01"
                    ),
                    "candidate_authority_type": "forest_plan_component",
                    "authority_category": "forest_plan",
                    "source_record_ids": ["R1PLAN-001"],
                    "forest_plan": {
                        "component_id": "R1PLAN-001-FW-STD-01",
                        "component_inventory_id": "test-inventory",
                        "forest_unit_id": "test-forest",
                        "component_type": "standard",
                    },
                },
            ],
            "validation": {"passed": True, "checks": []},
        },
    )
    _write_jsonl(
        applicability_dir / "applicability_decisions.jsonl",
        [
            {
                "schema_version": "applicability-decision-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "decision_id": "decision-applicable",
                "candidate_authority_id": "rule-template:nepa-ea-v0:0.1.0:nepa_rule",
                "candidate_authority_type": "rule_template",
                "status": "applicable",
                "basis_type": "baseline",
                "adjudication_state": "not_required",
                "rule_template": {"rule_id": "nepa_rule"},
                "search_coverage_certificate_ids": [],
                "retrieval_trace_ids": ["retrieval-trace-applicable"],
                "selected_graph_path_ids": ["graph-path-applicable"],
                "human_adjudication_refs": [],
            },
            {
                "schema_version": "applicability-decision-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "decision_id": "decision-not-applicable",
                "candidate_authority_id": (
                    "forest-plan-component:test-inventory:R1PLAN-001-FW-STD-01"
                ),
                "candidate_authority_type": "forest_plan_component",
                "status": "not_applicable",
                "basis_type": "negative_package_evidence",
                "adjudication_state": "not_required",
                "forest_plan": {
                    "component_id": "R1PLAN-001-FW-STD-01",
                    "forest_unit_id": "test-forest",
                },
                "search_coverage_certificate_ids": ["coverage-not-applicable"],
                "retrieval_trace_ids": ["retrieval-trace-not-applicable"],
                "selected_graph_path_ids": ["graph-path-not-applicable"],
                "human_adjudication_refs": [],
            },
        ],
    )
    _write_json(
        applicability_dir / "search_coverage_certificates.json",
        {
            "schema_version": "search-coverage-certificates-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "certificates": [
                {
                    "coverage_certificate_id": "coverage-not-applicable",
                    "covered_candidate_authority_ids": [
                        "forest-plan-component:test-inventory:R1PLAN-001-FW-STD-01"
                    ],
                    "covered_decision_ids": ["decision-not-applicable"],
                    "coverage_result": "sufficient",
                }
            ],
        },
    )
    _write_json(
        applicability_dir / "generated_rule_pack.json",
        {
            "schema_version": "generated-rule-pack-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "generated_rule_pack_id": "generated-review-test",
            "rules": [
                {
                    "id": "nepa_rule",
                    "generated_rule_id": "nepa_rule",
                    "applicability_decision_id": "decision-applicable",
                    "candidate_authority_id": "rule-template:nepa-ea-v0:0.1.0:nepa_rule",
                    "authority_category": "law",
                    "authority_source_record_id": "R1EA-001",
                    "title": "NEPA applies",
                    "severity": "high",
                    "applicability_mode": "baseline",
                }
            ],
        },
    )
    _write_json(
        applicability_dir / "applicability_validation.json",
        {
            "schema_version": "applicability-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "reviewer_ready": True,
            "generated_rule_pack_ready": True,
            "checks": [],
        },
    )
    _write_json(
        applicability_dir / "generated_rule_pack_validation.json",
        {
            "schema_version": "generated-rule-pack-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "checks": [],
        },
    )
    _write_json(
        applicability_dir / "package_fact_graph.json",
        {
            "schema_version": "package-fact-graph-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "nodes": [
                {
                    "node_id": "package-fact:test-action",
                    "node_type": "package_fact",
                    "fact_type": "action",
                }
            ],
            "edges": [
                {
                    "edge_id": "package-fact:test-action:source",
                    "source_node_id": "package-fact:test-action",
                    "target_node_id": "chunk:EA-PACKAGE-001",
                }
            ],
        },
    )
    _write_jsonl(
        applicability_dir / "applicability_retrieval_trace.jsonl",
        [
            {
                "schema_version": "applicability-retrieval-trace-v0",
                "retrieval_trace_id": "retrieval-trace-applicable",
                "candidate_authority_id": "rule-template:nepa-ea-v0:0.1.0:nepa_rule",
            },
            {
                "schema_version": "applicability-retrieval-trace-v0",
                "retrieval_trace_id": "retrieval-trace-not-applicable",
                "candidate_authority_id": (
                    "forest-plan-component:test-inventory:R1PLAN-001-FW-STD-01"
                ),
            },
        ],
    )
    _write_jsonl(
        applicability_dir / "applicability_graph_trace.jsonl",
        [
            {
                "schema_version": "applicability-graph-trace-v0",
                "graph_path_id": "graph-path-applicable",
                "candidate_authority_id": "rule-template:nepa-ea-v0:0.1.0:nepa_rule",
            },
            {
                "schema_version": "applicability-graph-trace-v0",
                "graph_path_id": "graph-path-not-applicable",
                "candidate_authority_id": (
                    "forest-plan-component:test-inventory:R1PLAN-001-FW-STD-01"
                ),
            },
        ],
    )
    _write_json(
        review_dir / "compliance_matrix.json",
        {
            "schema_version": "compliance-matrix-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "rows": [
                {
                    "row_id": "nepa_rule",
                    "rule_id": "nepa_rule",
                    "rule_title": "NEPA applies",
                    "status": "pass",
                    "applicability_status": "applicable",
                    "applicability_decision_id": "decision-applicable",
                    "candidate_authority_id": "rule-template:nepa-ea-v0:0.1.0:nepa_rule",
                    "candidate_authority_type": "rule_template",
                    "authority_family_id": "active_family",
                    "authority_category": "law",
                    "source_claim_ids": ["claim:001"],
                    "source_library_evidence": _evidence(
                        source_set_id,
                        source_record_id="R1EA-001",
                        citation_label="R1EA-001 citation",
                    ),
                    "ea_package_evidence": _evidence(
                        source_set_id,
                        source_record_id="EA-PACKAGE-001",
                        citation_label="EA package citation",
                    ),
                }
            ],
        },
    )
    _write_json(
        review_dir / "compliance_validation.json",
        {
            "schema_version": "compliance-validation-v0",
            "passed": True,
            "checks": [],
        },
    )
    _write_jsonl(
        review_dir / "finding_graph_nodes.jsonl",
        [{"id": "compliance_finding:review-test:nepa_rule", "type": "ComplianceFinding"}],
    )
    _write_jsonl(
        review_dir / "finding_graph_edges.jsonl",
        [{"id": "edge:review-test:nepa_rule", "relationship": "RULE_PRODUCED_FINDING"}],
    )


def _evidence(source_set_id: str, *, source_record_id: str, citation_label: str) -> dict:
    return {
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "citation_label": citation_label,
        "artifact_sha256": f"sha-{source_record_id}",
        "chunk_id": f"chunk:{source_record_id}",
        "content_sha256": f"content-{source_record_id}",
        "source_char_start": 0,
        "source_char_end": 64,
        "chunk_char_start": 0,
        "chunk_char_end": 64,
    }


def _phase(summary: dict, name: str) -> dict:
    return next(phase for phase in summary["phases"] if phase["name"] == name)
