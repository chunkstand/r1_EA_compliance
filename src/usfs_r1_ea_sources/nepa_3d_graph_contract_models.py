from __future__ import annotations

from pathlib import Path


NEPA_3D_GRAPH_CONTRACT_SCHEMA_VERSION = "nepa-3d-graph-contract-v1"
NEPA_3D_GRAPH_SCHEMA_VERSION = "nepa-3d-knowledge-graph-v1"
DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH = Path("config/nepa_3d_graph_contract_v1.json")

REQUIRED_EXPORT_SCOPES = {"source_set", "review"}
REQUIRED_NODE_TYPES = {
    "source_set",
    "review",
    "authority_family",
    "authority_document",
    "authority_section",
    "jurisdiction_scope",
    "source_record",
    "artifact",
    "chunk",
    "evidence_span",
    "source_claim",
    "rule_template",
    "applicability_decision",
    "generated_rule",
    "compliance_finding",
    "forest_unit",
    "forest_plan",
    "forest_plan_component",
    "authority_path",
    "justification_path",
    "readiness_blocker",
    "graph_lens",
}
REQUIRED_EDGE_TYPES = {
    "CONTAINS_AUTHORITY_FAMILY",
    "HAS_SOURCE_RECORD",
    "CITES_AUTHORITY_DOCUMENT",
    "HAS_AUTHORITY_SECTION",
    "HAS_JURISDICTION_SCOPE",
    "HAS_ARTIFACT",
    "HAS_CHUNK",
    "HAS_EVIDENCE_SPAN",
    "SUPPORTS_SOURCE_CLAIM",
    "SUPPORTS_RULE_TEMPLATE",
    "PRODUCES_APPLICABILITY_DECISION",
    "GENERATES_RULE",
    "SUPPORTS_COMPLIANCE_FINDING",
    "SUPERSEDED_BY",
    "REPLACES_RESERVED_AUTHORITY",
    "HAS_CURRENTNESS_STATUS",
    "BLOCKED_BY",
    "APPLIES_TO_REVIEW",
    "NOT_APPLICABLE_TO_REVIEW",
    "NEEDS_ADJUDICATION",
    "ADJUDICATED_BY",
    "BELONGS_TO_FOREST_UNIT",
    "HAS_FOREST_PLAN",
    "HAS_FOREST_COMPONENT",
    "HAS_AUTHORITY_PATH",
    "PATH_TARGETS",
    "JUSTIFIED_BY",
    "SUPPORTS_JUSTIFICATION_PATH",
    "HAS_READINESS_BLOCKER",
    "DISPLAYED_IN_LENS",
}
REQUIRED_DISPLAY_STATUSES = {
    "active",
    "superseded",
    "reserved",
    "candidate",
    "out_of_scope",
    "applicable",
    "not_applicable",
    "unresolved",
    "adjudicated",
    "readiness_blocked",
}
REQUIRED_REVIEW_READINESS_STATUSES = {
    "reviewer_ready",
    "not_reviewer_ready",
    "not_review_specific",
    "source_currentness_only",
    "blocked",
    "needs_adjudication",
}
REQUIRED_READINESS_BLOCKER_TYPES = {
    "extraction_blocked",
    "missing_source",
    "official_source_gap",
    "stale_artifact",
    "superseded_source",
    "retrieval_miss",
    "graph_trace_gap",
    "search_coverage_gap",
    "adjudication_needed",
    "package_fixture_missing",
    "forest_profile_not_ready",
    "fsh_chapter_delta_required",
    "duplicate_component_ids_detected",
    "duplicate_standard_ids_detected",
    "plan_component_labels_not_detected",
    "plan_standard_labels_not_detected",
}
REQUIRED_READINESS_SEMANTIC_CLASSES = {
    "none",
    "synthetic_blocker_node",
    "blocked_domain_node",
    "blocker_relationship_edge",
    "blocked_relationship_edge",
}
REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "graph_id",
    "created_at",
    "export_scope",
    "inputs",
    "lens_metadata",
    "nodes",
    "edges",
    "summary",
    "validation",
}
REQUIRED_NODE_FIELDS = {
    "node_id",
    "node_type",
    "label",
    "display_status",
    "review_readiness_status",
    "readiness_semantic_class",
    "provenance",
    "currentness_metadata",
    "readiness_blockers",
}
REQUIRED_EDGE_FIELDS = {
    "edge_id",
    "edge_type",
    "source_node_id",
    "target_node_id",
    "display_status",
    "review_readiness_status",
    "readiness_semantic_class",
    "provenance",
}
REQUIRED_SUMMARY_FIELDS = {
    "node_count",
    "edge_count",
    "node_type_counts",
    "edge_type_counts",
    "display_status_counts",
    "review_readiness_status_counts",
    "readiness_blocker_counts",
}
REQUIRED_VALIDATION_FIELDS = {"passed", "checks"}
REQUIRED_LENS_FIELDS = {
    "lens_id",
    "label",
    "description",
    "supported_node_types",
    "supported_edge_types",
    "display_status_values",
}
REQUIRED_LENSES = {
    "authority_currentness",
    "forest_plan",
    "package_applicability",
    "evidence_path",
    "semantic_relationships",
    "readiness_blockers",
}
DEFAULT_GRAPH_FAILURE_CATEGORY = "graph_viewer_export_invalid"
GRAPH_FAILURE_CATEGORY_BY_CHECK_NAME = {
    "nepa_3d_graph_exports_all_authority_families": "graph_missing_authority_family",
    "nepa_3d_graph_exports_candidate_families": "graph_missing_authority_family",
    "nepa_3d_graph_exports_superseded_families": "graph_superseded_as_current",
    "nepa_3d_graph_exports_all_catalog_source_records": "graph_missing_source_record",
    "nepa_3d_graph_currentness_gate_passed": "graph_missing_currentness_status",
    "nepa_3d_graph_forest_plan_inventory_owned_by_source_set": (
        "graph_forest_plan_inventory_ownership_gap"
    ),
    "nepa_3d_graph_region1_promoted_profiles_have_catalog_sources": (
        "graph_missing_source_record"
    ),
    "nepa_3d_graph_region1_promoted_profiles_have_inventory": "graph_region1_profile_gap",
    "nepa_3d_graph_region1_requirement_sources_are_cataloged": "graph_missing_source_record",
    "nepa_3d_graph_region1_readiness_prevents_overclaim": "graph_region1_profile_gap",
    "nepa_3d_graph_region1_readiness_covers_configured_profiles": "graph_region1_profile_gap",
    "nepa_3d_graph_region1_readiness_tracks_known_region1_units": "graph_region1_profile_gap",
    "nepa_3d_graph_region1_promoted_profiles_have_eval_fixtures": "graph_region1_profile_gap",
    "nepa_3d_review_graph_exports_all_candidate_authorities": (
        "graph_missing_candidate_authority"
    ),
    "nepa_3d_review_graph_maps_each_candidate_to_one_decision": (
        "graph_missing_applicability_decision"
    ),
    "nepa_3d_review_graph_decisions_map_to_candidates": (
        "graph_missing_applicability_decision"
    ),
    "nepa_3d_review_graph_links_candidates_to_decisions": (
        "graph_missing_applicability_decision"
    ),
    "nepa_3d_review_graph_non_applicable_decisions_have_support": (
        "graph_missing_applicability_decision"
    ),
    "nepa_3d_review_graph_generated_rules_from_applicable_decisions": (
        "graph_missing_applicability_decision"
    ),
    "nepa_3d_review_graph_findings_link_to_generated_rules": (
        "graph_missing_compliance_finding"
    ),
    "nepa_3d_review_graph_findings_link_to_evidence_spans": "graph_missing_evidence_span",
    "nepa_3d_review_graph_review_overlay_requires_validated_inputs": "graph_review_input_invalid",
}
