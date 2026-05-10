from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any
from typing import Iterable

from .nepa_3d_graph_contract import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH
from .nepa_3d_graph_contract import NEPA_3D_GRAPH_SCHEMA_VERSION
from .nepa_3d_graph_contract import load_nepa_3d_graph_contract
from .nepa_3d_graph_contract import validate_nepa_3d_graph
from .records import sha256_file
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack


DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH = Path(
    "config/authority_family_rule_templates_nepa_ea_v1.json"
)
DEFAULT_FOREST_PLAN_PROFILES_PATH = Path("config/forest_plan_profiles.json")
DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH = Path(
    "config/region1_forest_plan_readiness_nepa_3d_v1.json"
)
REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION = "region1-forest-plan-readiness-v1"
SOURCE_DELTA_READINESS_SCHEMA_VERSION = "r1-forest-plan-source-delta-readiness-v3"

SOURCE_SET_EXPORT_SCHEMA_VERSION = NEPA_3D_GRAPH_SCHEMA_VERSION
BASE_RULE_NODE_PREFIX = "rule_template:base"
AUTHORITY_TEMPLATE_NODE_PREFIX = "rule_template:authority_family"
REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES = (
    "review_authority_universe_snapshot",
    "review_package_fact_graph",
    "review_applicability_retrieval_trace",
    "review_applicability_graph_trace",
    "review_applicability_decisions",
    "review_search_coverage_certificates",
    "review_generated_rule_pack",
    "review_compliance_matrix",
    "review_finding_graph_nodes",
    "review_finding_graph_edges",
)
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
    "nepa_3d_graph_region1_promoted_profiles_have_inventory": (
        "graph_region1_profile_gap"
    ),
    "nepa_3d_graph_region1_requirement_sources_are_cataloged": (
        "graph_missing_source_record"
    ),
    "nepa_3d_graph_region1_readiness_prevents_overclaim": "graph_region1_profile_gap",
    "nepa_3d_graph_region1_readiness_covers_configured_profiles": (
        "graph_region1_profile_gap"
    ),
    "nepa_3d_graph_region1_readiness_tracks_known_region1_units": (
        "graph_region1_profile_gap"
    ),
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
}


@dataclass(frozen=True)
class NepaKnowledgeGraphExportResult:
    source_set_id: str
    graph_dir: Path
    graph_path: Path
    nodes_path: Path
    edges_path: Path
    summary_path: Path
    validation_path: Path
    summary: dict[str, Any]


class _GraphBuilder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    def add_node(
        self,
        *,
        node_id: str,
        node_type: str,
        label: str,
        display_status: str,
        review_readiness_status: str,
        readiness_semantic_class: str | None = None,
        provenance: dict[str, Any],
        currentness_metadata: dict[str, Any] | None = None,
        readiness_blockers: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        record = {
            "node_id": node_id,
            "node_type": node_type,
            "label": label,
            "display_status": display_status,
            "review_readiness_status": review_readiness_status,
            "readiness_semantic_class": readiness_semantic_class
            or _default_node_readiness_semantic_class(
                node_type=node_type,
                display_status=display_status,
            ),
            "provenance": _compact_dict(provenance),
            "currentness_metadata": _compact_dict(currentness_metadata or {}),
            "readiness_blockers": sorted(set(readiness_blockers or [])),
        }
        if metadata:
            record["metadata"] = _compact_dict(metadata)

        existing = self.nodes.get(node_id)
        if existing is None:
            self.nodes[node_id] = record
            return node_id

        existing["provenance"] = {
            **existing.get("provenance", {}),
            **record.get("provenance", {}),
        }
        existing["currentness_metadata"] = {
            **existing.get("currentness_metadata", {}),
            **record.get("currentness_metadata", {}),
        }
        existing["readiness_blockers"] = sorted(
            set(existing.get("readiness_blockers", [])) | set(record.get("readiness_blockers", []))
        )
        existing["readiness_semantic_class"] = (
            readiness_semantic_class
            or _default_node_readiness_semantic_class(
                node_type=str(existing.get("node_type") or node_type),
                display_status=str(existing.get("display_status") or display_status),
            )
        )
        if metadata:
            existing["metadata"] = {**existing.get("metadata", {}), **record["metadata"]}
        return node_id

    def add_edge(
        self,
        *,
        edge_type: str,
        source_node_id: str,
        target_node_id: str,
        display_status: str,
        review_readiness_status: str,
        readiness_semantic_class: str | None = None,
        provenance: dict[str, Any],
        readiness_blockers: list[str] | None = None,
        edge_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        edge_id = "edge:" + _stable_digest(
            edge_key or edge_type,
            source_node_id,
            target_node_id,
            json.dumps(_compact_dict(provenance), sort_keys=True),
        )
        if edge_id in self.edges:
            return edge_id
        record = {
            "edge_id": edge_id,
            "edge_type": edge_type,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "display_status": display_status,
            "review_readiness_status": review_readiness_status,
            "readiness_semantic_class": readiness_semantic_class
            or _default_edge_readiness_semantic_class(
                display_status=display_status,
                target_node_type=str(
                    _dict(self.nodes.get(target_node_id)).get("node_type") or ""
                ),
            ),
            "provenance": _compact_dict(provenance),
            "readiness_blockers": sorted(set(readiness_blockers or [])),
        }
        if metadata:
            record["metadata"] = _compact_dict(metadata)
        self.edges[edge_id] = record
        return edge_id

    def update_node(
        self,
        node_id: str,
        *,
        display_status: str | None = None,
        review_readiness_status: str | None = None,
        readiness_semantic_class: str | None = None,
        provenance: dict[str, Any] | None = None,
        readiness_blockers: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = self.nodes.get(node_id)
        if record is None:
            return
        if display_status:
            record["display_status"] = display_status
        if review_readiness_status:
            record["review_readiness_status"] = review_readiness_status
        record["readiness_semantic_class"] = readiness_semantic_class or _default_node_readiness_semantic_class(
            node_type=str(record.get("node_type") or ""),
            display_status=str(record.get("display_status") or ""),
        )
        if provenance:
            record["provenance"] = {
                **record.get("provenance", {}),
                **_compact_dict(provenance),
            }
        if readiness_blockers:
            record["readiness_blockers"] = sorted(
                set(record.get("readiness_blockers", [])) | set(readiness_blockers)
            )
        if metadata:
            record["metadata"] = {**record.get("metadata", {}), **_compact_dict(metadata)}

    def sorted_nodes(self) -> list[dict[str, Any]]:
        return [self.nodes[node_id] for node_id in sorted(self.nodes)]

    def sorted_edges(self) -> list[dict[str, Any]]:
        return [self.edges[edge_id] for edge_id in sorted(self.edges)]


def _default_node_readiness_semantic_class(*, node_type: str, display_status: str) -> str:
    if node_type == "readiness_blocker":
        return "synthetic_blocker_node"
    if display_status == "readiness_blocked":
        return "blocked_domain_node"
    return "none"


def _default_edge_readiness_semantic_class(*, display_status: str, target_node_type: str) -> str:
    if target_node_type == "readiness_blocker":
        return "blocker_relationship_edge"
    if display_status == "readiness_blocked":
        return "blocked_relationship_edge"
    return "none"


def build_nepa_knowledge_graph_export(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    review_id: str | None = None,
    graph_contract_path: Path = DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    authority_family_rule_templates_path: Path = DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    region1_forest_plan_readiness_path: Path = DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    catalog_path: Path | None = None,
    catalog_graph_nodes_path: Path | None = None,
    catalog_graph_edges_path: Path | None = None,
    source_set_manifest_path: Path | None = None,
    authority_currentness_path: Path | None = None,
    evidence_graph_nodes_path: Path | None = None,
    evidence_graph_edges_path: Path | None = None,
    claims_path: Path | None = None,
    rule_claim_links_path: Path | None = None,
    forest_plan_components_path: Path | None = None,
) -> NepaKnowledgeGraphExportResult:
    """Build the source-set NEPA 3D graph export from audited catalog and derived artifacts."""

    output_dir = Path(output_dir)
    source_set_manifest_path = source_set_manifest_path or output_dir / "catalog" / "source_set_manifest.json"
    manifest = _read_json(source_set_manifest_path)
    source_set_id = source_set_id or str(manifest["source_set_id"])
    derived_dir = output_dir / "derived" / source_set_id
    review_dir = output_dir / "reviews" / review_id if review_id else None
    graph_dir = review_dir / "knowledge_graph" if review_dir else derived_dir / "knowledge_graph"
    graph_path = graph_dir / "nepa_3d_graph.json"
    nodes_path = graph_dir / "nepa_3d_graph_nodes.jsonl"
    edges_path = graph_dir / "nepa_3d_graph_edges.jsonl"
    summary_path = graph_dir / "nepa_3d_graph_summary.json"
    validation_path = graph_dir / "nepa_3d_graph_validation.json"

    catalog_path = catalog_path or output_dir / "catalog" / "source_catalog.jsonl"
    catalog_graph_nodes_path = catalog_graph_nodes_path or output_dir / "catalog" / "source_graph_nodes.jsonl"
    catalog_graph_edges_path = catalog_graph_edges_path or output_dir / "catalog" / "source_graph_edges.jsonl"
    authority_currentness_path = (
        authority_currentness_path
        or derived_dir / "authority_currentness" / "authority_currentness_report.json"
    )
    evidence_graph_nodes_path = (
        evidence_graph_nodes_path or derived_dir / "evidence_graph" / "document_graph_nodes.jsonl"
    )
    evidence_graph_edges_path = (
        evidence_graph_edges_path or derived_dir / "evidence_graph" / "document_graph_edges.jsonl"
    )
    claims_path = claims_path or derived_dir / "claims" / "claims.jsonl"

    rule_pack = load_rule_pack(rule_pack_path)
    rule_claim_links_path = rule_claim_links_path or (
        derived_dir
        / "rule_claim_links"
        / str(rule_pack.get("rule_pack_id"))
        / str(rule_pack.get("version"))
        / "rule_claim_links.jsonl"
    )
    forest_plan_components_path = (
        forest_plan_components_path
        or derived_dir / "forest_plan_components" / "component_inventory.json"
    )
    review_artifact_paths = _review_artifact_paths(review_dir) if review_dir else {}

    contract = load_nepa_3d_graph_contract(graph_contract_path)
    inventory = _read_json(authority_inventory_path)
    template_config = _read_json(authority_family_rule_templates_path)
    forest_plan_profiles = _read_json(forest_plan_profiles_path)
    region1_forest_plan_readiness = _load_region1_forest_plan_readiness(
        region1_forest_plan_readiness_path
    )
    currentness = _read_json(authority_currentness_path)
    catalog_rows = [
        row
        for row in _read_jsonl(catalog_path)
        if str(row.get("source_set_id") or source_set_id) == source_set_id
    ]
    claims = _read_jsonl(claims_path)
    rule_claim_links = _read_jsonl(rule_claim_links_path)
    forest_components = _read_json(forest_plan_components_path)
    evidence_graph_node_count = _jsonl_count(evidence_graph_nodes_path)
    evidence_graph_edge_count = _jsonl_count(evidence_graph_edges_path)
    catalog_graph_node_count = _jsonl_count(catalog_graph_nodes_path)
    catalog_graph_edge_count = _jsonl_count(catalog_graph_edges_path)
    review_artifacts = (
        _load_review_artifacts(review_artifact_paths) if review_artifact_paths else {}
    )

    builder = _GraphBuilder()
    inputs = _input_records(
        {
            "source_set_manifest": source_set_manifest_path,
            "source_catalog": catalog_path,
            "catalog_graph_nodes": catalog_graph_nodes_path,
            "catalog_graph_edges": catalog_graph_edges_path,
            "authority_inventory": authority_inventory_path,
            "authority_currentness": authority_currentness_path,
            "rule_pack": rule_pack_path,
            "authority_family_rule_templates": authority_family_rule_templates_path,
            "forest_plan_profiles": forest_plan_profiles_path,
            "region1_forest_plan_readiness": region1_forest_plan_readiness_path,
            "evidence_graph_nodes": evidence_graph_nodes_path,
            "evidence_graph_edges": evidence_graph_edges_path,
            "claims": claims_path,
            "rule_claim_links": rule_claim_links_path,
            "forest_plan_components": forest_plan_components_path,
            "graph_contract": graph_contract_path,
            **review_artifact_paths,
        }
    )
    family_currentness_by_id = {
        str(record.get("authority_family_id")): record
        for record in currentness.get("family_currentness", [])
        if record.get("authority_family_id")
    }
    source_currentness_by_id = _source_currentness_by_id(currentness.get("source_currentness_records", []))
    catalog_partition_by_id = {
        str(record.get("source_record_id")): record
        for record in currentness.get("catalog_source_partitions", [])
        if record.get("source_record_id")
    }
    catalog_by_id = {
        str(row.get("source_record_id")): row for row in catalog_rows if row.get("source_record_id")
    }
    claims_by_id = {str(claim.get("claim_id")): claim for claim in claims if claim.get("claim_id")}

    source_set_node_id = _source_set_node_id(source_set_id)
    builder.add_node(
        node_id=source_set_node_id,
        node_type="source_set",
        label=source_set_id,
        display_status="active",
        review_readiness_status="not_review_specific",
        provenance={
            "source_set_id": source_set_id,
            "source_set_manifest_sha256": _sha256_or_none(source_set_manifest_path),
        },
        readiness_blockers=_source_set_readiness_blockers(currentness),
        metadata={
            "manifest_source_count": manifest.get("source_count"),
            "manifest_artifact_count": manifest.get("artifact_count"),
            "catalog_graph_node_count": catalog_graph_node_count,
            "catalog_graph_edge_count": catalog_graph_edge_count,
            "evidence_graph_node_count": evidence_graph_node_count,
            "evidence_graph_edge_count": evidence_graph_edge_count,
        },
    )
    _add_lens_nodes(builder, contract=contract)
    _add_source_records_and_artifacts(
        builder,
        source_set_id=source_set_id,
        catalog_rows=catalog_rows,
        source_currentness_by_id=source_currentness_by_id,
        catalog_partition_by_id=catalog_partition_by_id,
    )
    _add_authority_families(
        builder,
        source_set_node_id=source_set_node_id,
        source_set_id=source_set_id,
        families=inventory.get("authority_families", []),
        family_currentness_by_id=family_currentness_by_id,
        source_currentness_by_id=source_currentness_by_id,
        catalog_by_id=catalog_by_id,
    )
    base_rule_node_ids = _add_base_rules(
        builder,
        source_set_id=source_set_id,
        rule_pack=rule_pack,
        families=inventory.get("authority_families", []),
    )
    template_node_ids = _add_authority_family_templates(
        builder,
        source_set_id=source_set_id,
        template_config=template_config,
    )
    _add_rule_claim_paths(
        builder,
        source_set_id=source_set_id,
        claims_by_id=claims_by_id,
        rule_claim_links=rule_claim_links,
        base_rule_node_ids=base_rule_node_ids,
    )
    _add_forest_plan_nodes(
        builder,
        source_set_id=source_set_id,
        forest_plan_profiles=forest_plan_profiles,
        region1_forest_plan_readiness=region1_forest_plan_readiness,
        forest_components=forest_components,
    )
    _add_source_set_blockers(builder, source_set_node_id=source_set_node_id, source_set_id=source_set_id)
    review_overlay_summary = {}
    if review_id:
        review_overlay_summary = _add_review_overlay(
            builder,
            source_set_id=source_set_id,
            review_id=review_id,
            review_artifacts=review_artifacts,
            inventory=inventory,
            rule_pack=rule_pack,
            base_rule_node_ids=base_rule_node_ids,
            template_node_ids=template_node_ids,
        )

    nodes = builder.sorted_nodes()
    edges = builder.sorted_edges()
    summary = _summary(
        source_set_id=source_set_id,
        nodes=nodes,
        edges=edges,
        catalog_rows=catalog_rows,
        inventory=inventory,
        rule_pack=rule_pack,
        template_config=template_config,
        rule_claim_links=rule_claim_links,
        forest_components=forest_components,
        forest_plan_profiles=forest_plan_profiles,
        region1_forest_plan_readiness=region1_forest_plan_readiness,
        currentness=currentness,
        inputs=inputs,
        catalog_graph_node_count=catalog_graph_node_count,
        catalog_graph_edge_count=catalog_graph_edge_count,
    )
    summary.update(review_overlay_summary)
    graph = {
        "schema_version": SOURCE_SET_EXPORT_SCHEMA_VERSION,
        "graph_id": f"nepa-3d-review:{review_id}:{source_set_id}"
        if review_id
        else f"nepa-3d-source-set:{source_set_id}",
        "created_at": str(manifest.get("created_at") or currentness.get("created_at") or ""),
        "export_scope": {
            **{"scope_type": "review", "source_set_id": source_set_id, "review_id": review_id}
        }
        if review_id
        else {"scope_type": "source_set", "source_set_id": source_set_id},
        "inputs": inputs,
        "lens_metadata": _lens_metadata(contract),
        "nodes": nodes,
        "edges": edges,
        "summary": summary,
        "validation": {"passed": False, "checks": []},
    }
    checks = validate_nepa_3d_graph(graph, contract) + _milestone_validation_checks(
        graph=graph,
        inventory=inventory,
        catalog_rows=catalog_rows,
        rule_pack=rule_pack,
        template_config=template_config,
        currentness=currentness,
        rule_claim_links=rule_claim_links,
        forest_components=forest_components,
        forest_plan_profiles=forest_plan_profiles,
        region1_forest_plan_readiness=region1_forest_plan_readiness,
        forest_plan_components_path=forest_plan_components_path,
        inputs=inputs,
        catalog_graph_node_count=catalog_graph_node_count,
        catalog_graph_edge_count=catalog_graph_edge_count,
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    if review_id:
        checks.extend(
            _review_overlay_validation_checks(
                graph=graph,
                review_id=review_id,
                review_artifacts=review_artifacts,
            )
        )
    checks = _annotate_graph_validation_checks(checks)
    validation = {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "failure_category_counts": _validation_failure_category_counts(checks),
    }
    graph["validation"] = validation
    summary["validation_passed"] = validation["passed"]
    summary["validation_check_count"] = len(checks)
    summary["failed_validation_check_count"] = sum(1 for check in checks if not check["passed"])
    summary["failure_category_counts"] = validation["failure_category_counts"]
    summary["graph_path"] = str(graph_path)
    summary["nodes_path"] = str(nodes_path)
    summary["edges_path"] = str(edges_path)
    summary["summary_path"] = str(summary_path)
    summary["validation_path"] = str(validation_path)

    graph_dir.mkdir(parents=True, exist_ok=True)
    _write_json(graph_path, graph)
    _write_jsonl(nodes_path, nodes)
    _write_jsonl(edges_path, edges)
    _write_json(summary_path, summary)
    _write_json(validation_path, validation)

    return NepaKnowledgeGraphExportResult(
        source_set_id=source_set_id,
        graph_dir=graph_dir,
        graph_path=graph_path,
        nodes_path=nodes_path,
        edges_path=edges_path,
        summary_path=summary_path,
        validation_path=validation_path,
        summary=summary,
    )


def _add_lens_nodes(builder: _GraphBuilder, *, contract: dict[str, Any]) -> None:
    for lens in _lens_metadata(contract):
        builder.add_node(
            node_id=f"graph_lens:{lens['lens_id']}",
            node_type="graph_lens",
            label=str(lens.get("label") or lens["lens_id"]),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={"lens_id": lens["lens_id"]},
            metadata=lens,
        )


def _add_source_records_and_artifacts(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    catalog_rows: list[dict[str, Any]],
    source_currentness_by_id: dict[str, dict[str, Any]],
    catalog_partition_by_id: dict[str, dict[str, Any]],
) -> None:
    for row in sorted(catalog_rows, key=lambda item: str(item.get("source_record_id") or "")):
        source_record_id = str(row.get("source_record_id") or "")
        currentness = source_currentness_by_id.get(source_record_id, {})
        partition = catalog_partition_by_id.get(source_record_id, {})
        status = _source_display_status(row=row, currentness=currentness, partition=partition)
        blockers = _source_readiness_blockers(row=row, currentness=currentness, partition=partition)
        source_node_id = _source_node_id(source_record_id)
        builder.add_node(
            node_id=source_node_id,
            node_type="source_record",
            label=str(row.get("title") or currentness.get("source_title") or source_record_id),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "citation_label": row.get("citation_label") or currentness.get("citation_label"),
                "artifact_sha256": row.get("artifact_sha256") or currentness.get("artifact_sha256"),
                "artifact_path": row.get("artifact_path") or currentness.get("artifact_path"),
                "url": row.get("effective_url") or row.get("original_url") or currentness.get("url"),
            },
            currentness_metadata=_currentness_metadata(currentness=currentness, partition=partition),
            readiness_blockers=blockers,
            metadata={
                "source_status": row.get("source_status"),
                "document_role": row.get("document_role"),
                "authority_level": row.get("authority_level"),
                "scope": row.get("scope"),
                "issuer": row.get("issuer"),
                "review_topics": row.get("review_topics", []),
            },
        )
        artifact_sha256 = row.get("artifact_sha256") or currentness.get("artifact_sha256")
        if artifact_sha256:
            artifact_node_id = _artifact_node_id(str(artifact_sha256))
            builder.add_node(
                node_id=artifact_node_id,
                node_type="artifact",
                label=f"Artifact {str(artifact_sha256)[:12]}",
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "artifact_sha256": artifact_sha256,
                    "artifact_path": row.get("artifact_path") or currentness.get("artifact_path"),
                    "citation_label": row.get("citation_label") or currentness.get("citation_label"),
                },
                currentness_metadata=_currentness_metadata(currentness=currentness, partition=partition),
                readiness_blockers=blockers,
            )
            builder.add_edge(
                edge_type="HAS_ARTIFACT",
                source_node_id=source_node_id,
                target_node_id=artifact_node_id,
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "artifact_sha256": artifact_sha256,
                },
                readiness_blockers=blockers,
            )


def _add_authority_families(
    builder: _GraphBuilder,
    *,
    source_set_node_id: str,
    source_set_id: str,
    families: list[dict[str, Any]],
    family_currentness_by_id: dict[str, dict[str, Any]],
    source_currentness_by_id: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
) -> None:
    for family in sorted(families, key=lambda item: str(item.get("family_id") or "")):
        family_id = str(family.get("family_id") or "")
        currentness = family_currentness_by_id.get(family_id, {})
        status = _family_display_status(family, currentness)
        blockers = _family_readiness_blockers(family, currentness)
        family_node_id = _family_node_id(family_id)
        builder.add_node(
            node_id=family_node_id,
            node_type="authority_family",
            label=str(family.get("name") or family_id),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "authority_family_id": family_id,
                "family_status": family.get("status"),
            },
            currentness_metadata={
                "family_status": family.get("status"),
                "currentness_status": currentness.get("currentness_status"),
                "current_source_record_count": currentness.get("current_source_record_count"),
                "replacement_source_record_count": currentness.get("replacement_source_record_count"),
                "source_addition_decision_status": currentness.get("source_addition_decision_status"),
            },
            readiness_blockers=blockers,
            metadata={
                "authority_category": family.get("authority_category"),
                "required_authority_requirement_ids": family.get(
                    "required_authority_requirement_ids", []
                ),
                "rule_ids": family.get("rule_ids", []),
                "open_inventory_gaps": family.get("open_inventory_gaps", []),
            },
        )
        builder.add_edge(
            edge_type="CONTAINS_AUTHORITY_FAMILY",
            source_node_id=source_set_node_id,
            target_node_id=family_node_id,
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={"source_set_id": source_set_id, "authority_family_id": family_id},
            readiness_blockers=blockers,
        )
        for source_record_id in sorted(set(_strings(family.get("source_record_ids")))):
            if source_record_id not in catalog_by_id and source_record_id not in source_currentness_by_id:
                continue
            source_record = source_currentness_by_id.get(source_record_id, {})
            source_status = _source_display_status(
                row=catalog_by_id.get(source_record_id, {}),
                currentness=source_record,
                partition={},
            )
            source_blockers = _source_readiness_blockers(
                row=catalog_by_id.get(source_record_id, {}),
                currentness=source_record,
                partition={},
            )
            builder.add_edge(
                edge_type="HAS_SOURCE_RECORD",
                source_node_id=family_node_id,
                target_node_id=_source_node_id(source_record_id),
                display_status=source_status["display_status"],
                review_readiness_status=source_status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "authority_family_id": family_id,
                    "source_record_id": source_record_id,
                    "family_status": family.get("status"),
                    "authority_family_source_role": source_record.get("authority_family_source_role"),
                },
                readiness_blockers=source_blockers,
            )
        if blockers:
            _add_blocker(builder, source_set_id=source_set_id, subject_node_id=family_node_id, blockers=blockers)


def _add_base_rules(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    rule_pack: dict[str, Any],
    families: list[dict[str, Any]],
) -> dict[str, str]:
    family_ids_by_rule_id: dict[str, set[str]] = {}
    for family in families:
        for rule_id in _strings(family.get("rule_ids")):
            family_ids_by_rule_id.setdefault(rule_id, set()).add(str(family.get("family_id")))

    rule_node_ids: dict[str, str] = {}
    for rule in sorted(rule_pack.get("rules", []), key=lambda item: str(item.get("id") or "")):
        rule_id = str(rule.get("id") or "")
        node_id = f"{BASE_RULE_NODE_PREFIX}:{rule_id}"
        rule_node_ids[rule_id] = node_id
        source_record_id = rule.get("authority_source_record_id") or _dict(rule.get("source_filters")).get(
            "source_record_id"
        )
        builder.add_node(
            node_id=node_id,
            node_type="rule_template",
            label=str(rule.get("title") or rule_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "rule_id": rule_id,
                "rule_pack_id": rule_pack.get("rule_pack_id"),
                "rule_pack_version": rule_pack.get("version"),
                "authority_source_record_id": source_record_id,
            },
            metadata={
                "rule_kind": "base_rule_pack_rule",
                "applicability_mode": rule.get("applicability_mode"),
                "authority_category": rule.get("authority_category"),
                "severity": rule.get("severity"),
                "requirement": rule.get("requirement"),
                "family_ids": sorted(family_ids_by_rule_id.get(rule_id, [])),
            },
        )
        if source_record_id:
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_source_node_id(str(source_record_id)),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "rule_id": rule_id,
                    "rule_pack_id": rule_pack.get("rule_pack_id"),
                    "rule_pack_version": rule_pack.get("version"),
                },
            )
        for family_id in sorted(family_ids_by_rule_id.get(rule_id, [])):
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_family_node_id(family_id),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "authority_family_id": family_id,
                    "rule_id": rule_id,
                },
            )
    return rule_node_ids


def _add_authority_family_templates(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    template_config: dict[str, Any],
) -> dict[str, str]:
    template_node_ids: dict[str, str] = {}
    for template in sorted(template_config.get("templates", []), key=lambda item: str(item.get("template_id") or "")):
        template_id = str(template.get("template_id") or template.get("rule_id") or "")
        rule_id = str(template.get("rule_id") or template_id)
        family_id = str(template.get("authority_family_id") or "")
        node_id = f"{AUTHORITY_TEMPLATE_NODE_PREFIX}:{template_id}"
        template_node_ids[template_id] = node_id
        builder.add_node(
            node_id=node_id,
            node_type="rule_template",
            label=str(template.get("title") or template_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "template_id": template_id,
                "rule_id": rule_id,
                "rule_pack_id": template_config.get("base_rule_pack_id"),
                "rule_pack_version": template_config.get("base_rule_pack_version"),
                "authority_family_id": family_id,
            },
            metadata={
                "rule_kind": "authority_family_template",
                "applicability_mode": template.get("applicability_mode"),
                "package_fact_types": template.get("package_fact_types", []),
                "source_record_ids": template.get("source_record_ids", []),
                "supporting_source_record_ids": template.get("supporting_source_record_ids", []),
                "requirement": template.get("requirement"),
            },
        )
        if family_id:
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_family_node_id(family_id),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "authority_family_id": family_id,
                    "template_id": template_id,
                    "rule_id": rule_id,
                },
            )
        for source_record_id in sorted(set(_strings(template.get("source_record_ids")))):
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_source_node_id(source_record_id),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "template_id": template_id,
                    "rule_id": rule_id,
                },
            )
    return template_node_ids


def _add_rule_claim_paths(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    claims_by_id: dict[str, dict[str, Any]],
    rule_claim_links: list[dict[str, Any]],
    base_rule_node_ids: dict[str, str],
) -> None:
    for link in sorted(rule_claim_links, key=lambda item: str(item.get("link_id") or "")):
        claim_id = str(link.get("claim_id") or "")
        rule_id = str(link.get("rule_id") or "")
        if not claim_id or rule_id not in base_rule_node_ids:
            continue
        claim = claims_by_id.get(claim_id, {})
        source_record_id = str(link.get("source_record_id") or claim.get("source_record_id") or "")
        artifact_sha256 = str(link.get("artifact_sha256") or claim.get("artifact_sha256") or "")
        chunk_id = str(link.get("chunk_id") or claim.get("chunk_id") or "")
        if not chunk_id:
            chunk_id = f"chunk:{source_record_id}:{link.get('chunk_index')}:{str(link.get('chunk_content_sha256') or '')[:12]}"
        chunk_node_id = f"chunk:{chunk_id.removeprefix('chunk:')}"
        evidence_node_id = f"evidence_span:{claim_id.removeprefix('claim:')}:{str(link.get('link_id') or '')[-12:]}"
        claim_node_id = f"source_claim:{claim_id.removeprefix('claim:')}"
        artifact_node_id = _artifact_node_id(artifact_sha256) if artifact_sha256 else None

        builder.add_node(
            node_id=chunk_node_id,
            node_type="chunk",
            label=f"{source_record_id} chunk {link.get('chunk_index')}",
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "chunk_index": link.get("chunk_index") or claim.get("chunk_index"),
                "content_sha256": link.get("chunk_content_sha256") or claim.get("chunk_content_sha256"),
                "artifact_sha256": artifact_sha256,
            },
            metadata={
                "citation_label": link.get("citation_label") or claim.get("citation_label"),
                "source_text_path": link.get("source_text_path") or claim.get("source_text_path"),
            },
        )
        builder.add_node(
            node_id=evidence_node_id,
            node_type="evidence_span",
            label=f"{source_record_id} evidence for {rule_id}",
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "chunk_index": link.get("chunk_index") or claim.get("chunk_index"),
                "char_start": link.get("source_char_start") or claim.get("source_char_start"),
                "char_end": link.get("source_char_end") or claim.get("source_char_end"),
                "claim_id": claim_id,
                "link_id": link.get("link_id"),
            },
            metadata={
                "citation_label": link.get("citation_label") or claim.get("citation_label"),
                "page": link.get("page") or claim.get("page"),
                "section": link.get("section") or claim.get("section"),
            },
        )
        builder.add_node(
            node_id=claim_node_id,
            node_type="source_claim",
            label=str((claim.get("claim_text") or link.get("claim_text") or claim_id))[:180],
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "claim_id": claim_id,
                "source_record_id": source_record_id,
                "content_sha256": claim.get("content_sha256") or link.get("content_sha256"),
            },
            metadata={
                "claim_type": claim.get("claim_type") or link.get("claim_type"),
                "validation_status": claim.get("validation_status")
                or link.get("claim_validation_status"),
                "confidence": claim.get("confidence"),
            },
        )
        if artifact_node_id:
            builder.add_edge(
                edge_type="HAS_CHUNK",
                source_node_id=artifact_node_id,
                target_node_id=chunk_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "artifact_sha256": artifact_sha256,
                    "chunk_id": chunk_id,
                },
            )
        builder.add_edge(
            edge_type="HAS_EVIDENCE_SPAN",
            source_node_id=chunk_node_id,
            target_node_id=evidence_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "claim_id": claim_id,
                "link_id": link.get("link_id"),
            },
        )
        builder.add_edge(
            edge_type="SUPPORTS_SOURCE_CLAIM",
            source_node_id=evidence_node_id,
            target_node_id=claim_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "claim_id": claim_id,
                "link_id": link.get("link_id"),
            },
        )
        builder.add_edge(
            edge_type="SUPPORTS_RULE_TEMPLATE",
            source_node_id=claim_node_id,
            target_node_id=base_rule_node_ids[rule_id],
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "claim_id": claim_id,
                "rule_id": rule_id,
                "link_id": link.get("link_id"),
                "score": link.get("score"),
            },
        )


def _add_forest_plan_nodes(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    forest_plan_profiles: dict[str, Any],
    region1_forest_plan_readiness: dict[str, Any],
    forest_components: dict[str, Any],
) -> None:
    plan_node_by_unit: dict[str, str] = {}
    readiness_by_unit = _region1_profile_readiness_by_unit(region1_forest_plan_readiness)
    rendered_profile_units: set[str] = set()
    for profile in sorted(
        forest_plan_profiles.get("profiles", []),
        key=lambda item: str(item.get("forest_unit_id") or ""),
    ):
        forest_unit_id = str(profile.get("forest_unit_id") or "")
        if not forest_unit_id:
            continue
        rendered_profile_units.add(forest_unit_id)
        readiness = readiness_by_unit.get(forest_unit_id, {})
        display = _region1_profile_display(readiness)
        blockers = _region1_profile_readiness_blockers(readiness)
        unit_node_id = _forest_unit_node_id(forest_unit_id)
        builder.add_node(
            node_id=unit_node_id,
            node_type="forest_unit",
            label=str(_first(profile.get("forest_unit_names")) or forest_unit_id),
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={"source_set_id": source_set_id, "forest_code": forest_unit_id},
            readiness_blockers=blockers,
            metadata={
                "forest_unit_names": profile.get("forest_unit_names", []),
                "required_readiness_source_roles": profile.get("required_readiness_source_roles", []),
                "profile_kind": readiness.get("profile_kind"),
                "graph_promotion_status": readiness.get("graph_promotion_status"),
                "source_requirements": readiness.get("source_requirements", []),
                "component_inventory_validation": readiness.get("component_inventory_validation", {}),
                "applicability_eval_coverage": readiness.get("applicability_eval_coverage", {}),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=unit_node_id,
                blockers=blockers,
            )
        plan_source_record_id = str(profile.get("active_plan_source_record_id") or "")
        if plan_source_record_id:
            plan_node_id = f"forest_plan:{forest_unit_id}:{plan_source_record_id}"
            plan_node_by_unit[forest_unit_id] = plan_node_id
            builder.add_node(
                node_id=plan_node_id,
                node_type="forest_plan",
                label=f"{forest_unit_id} active forest plan",
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
                metadata={
                    "supporting_source_record_ids_by_role": profile.get(
                        "supporting_source_record_ids_by_role", {}
                    ),
                    "component_inventory_validation": readiness.get(
                        "component_inventory_validation", {}
                    ),
                },
            )
            if blockers:
                _add_blocker(
                    builder,
                    source_set_id=source_set_id,
                    subject_node_id=plan_node_id,
                    blockers=blockers,
                )
            builder.add_edge(
                edge_type="HAS_FOREST_PLAN",
                source_node_id=unit_node_id,
                target_node_id=plan_node_id,
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
            )
            builder.add_edge(
                edge_type="HAS_SOURCE_RECORD",
                source_node_id=plan_node_id,
                target_node_id=_source_node_id(plan_source_record_id),
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                    "source_role": "active_plan",
                },
                readiness_blockers=blockers,
            )
            for role, role_record in sorted(
                _dict(profile.get("supporting_source_record_ids_by_role")).items()
            ):
                supporting_source_record_id = str(_dict(role_record).get("source_record_id") or "")
                if supporting_source_record_id:
                    builder.add_edge(
                        edge_type="HAS_SOURCE_RECORD",
                        source_node_id=plan_node_id,
                        target_node_id=_source_node_id(supporting_source_record_id),
                        display_status=display["display_status"],
                        review_readiness_status=display["review_readiness_status"],
                        provenance={
                            "source_set_id": source_set_id,
                            "forest_code": forest_unit_id,
                            "source_record_id": supporting_source_record_id,
                            "source_role": role,
                        },
                        readiness_blockers=blockers,
                    )
        _add_profile_term_nodes(
            builder,
            source_set_id=source_set_id,
            forest_unit_id=forest_unit_id,
            plan_node_id=plan_node_by_unit.get(forest_unit_id),
            profile=profile,
            display=display,
            blockers=blockers,
        )

    for readiness in _region1_profile_readiness_rows(region1_forest_plan_readiness):
        forest_unit_id = str(readiness.get("forest_unit_id") or "")
        if not forest_unit_id or forest_unit_id in rendered_profile_units:
            continue
        display = _region1_profile_display(readiness)
        blockers = _region1_profile_readiness_blockers(readiness)
        unit_node_id = _forest_unit_node_id(forest_unit_id)
        builder.add_node(
            node_id=unit_node_id,
            node_type="forest_unit",
            label=str(_first(readiness.get("forest_unit_names")) or forest_unit_id),
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={"source_set_id": source_set_id, "forest_code": forest_unit_id},
            readiness_blockers=blockers,
            metadata={
                "forest_unit_names": readiness.get("forest_unit_names", []),
                "profile_kind": readiness.get("profile_kind"),
                "graph_promotion_status": readiness.get("graph_promotion_status"),
                "source_requirements": readiness.get("source_requirements", []),
                "component_inventory_validation": readiness.get("component_inventory_validation", {}),
                "applicability_eval_coverage": readiness.get("applicability_eval_coverage", {}),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=unit_node_id,
                blockers=blockers,
            )
        plan_source_record_id = str(readiness.get("active_plan_source_record_id") or "")
        if plan_source_record_id:
            plan_node_id = f"forest_plan:{forest_unit_id}:{plan_source_record_id}"
            plan_node_by_unit[forest_unit_id] = plan_node_id
            builder.add_node(
                node_id=plan_node_id,
                node_type="forest_plan",
                label=f"{forest_unit_id} tracked forest plan",
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
                metadata={
                    "source_requirements": readiness.get("source_requirements", []),
                    "component_inventory_validation": readiness.get(
                        "component_inventory_validation", {}
                    ),
                },
            )
            if blockers:
                _add_blocker(
                    builder,
                    source_set_id=source_set_id,
                    subject_node_id=plan_node_id,
                    blockers=blockers,
                )
            builder.add_edge(
                edge_type="HAS_FOREST_PLAN",
                source_node_id=unit_node_id,
                target_node_id=plan_node_id,
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
            )
            for requirement in _dict_list(readiness.get("source_requirements")):
                source_record_id = str(requirement.get("source_record_id") or "")
                if not source_record_id:
                    continue
                builder.add_edge(
                    edge_type="HAS_SOURCE_RECORD",
                    source_node_id=plan_node_id,
                    target_node_id=_source_node_id(source_record_id),
                    display_status=display["display_status"],
                    review_readiness_status=display["review_readiness_status"],
                    provenance={
                        "source_set_id": source_set_id,
                        "forest_code": forest_unit_id,
                        "source_record_id": source_record_id,
                        "source_role": requirement.get("role"),
                    },
                    readiness_blockers=blockers,
                )

    _add_region1_requirement_nodes(
        builder,
        source_set_id=source_set_id,
        region1_forest_plan_readiness=region1_forest_plan_readiness,
    )

    for component in sorted(
        forest_components.get("components", []),
        key=lambda item: str(item.get("component_id") or ""),
    ):
        component_id = str(component.get("component_id") or "")
        forest_unit_id = str(component.get("forest_unit_id") or "")
        if not component_id or not forest_unit_id:
            continue
        component_node_id = f"forest_plan_component:{component_id}"
        source_record_id = str(component.get("source_record_id") or "")
        builder.add_node(
            node_id=component_node_id,
            node_type="forest_plan_component",
            label=component_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": forest_unit_id,
                "source_record_id": source_record_id,
                "artifact_sha256": component.get("artifact_sha256"),
                "content_sha256": component.get("content_sha256"),
            },
            metadata={
                "component_type": component.get("component_type"),
                "plan_version": component.get("plan_version"),
                "section_id": component.get("section_id"),
                "source_chunk_ids": component.get("source_chunk_ids", []),
                "text_excerpt": str(component.get("component_text") or "")[:240],
            },
        )
        plan_node_id = plan_node_by_unit.get(forest_unit_id)
        if plan_node_id:
            builder.add_edge(
                edge_type="HAS_FOREST_COMPONENT",
                source_node_id=plan_node_id,
                target_node_id=component_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "component_id": component_id,
                },
            )
        builder.add_edge(
            edge_type="BELONGS_TO_FOREST_UNIT",
            source_node_id=component_node_id,
            target_node_id=_forest_unit_node_id(forest_unit_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "forest_code": forest_unit_id,
                "component_id": component_id,
            },
        )
        if source_record_id:
            builder.add_edge(
                edge_type="HAS_FOREST_COMPONENT",
                source_node_id=_source_node_id(source_record_id),
                target_node_id=component_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "component_id": component_id,
                },
            )


def _add_region1_requirement_nodes(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    region1_forest_plan_readiness: dict[str, Any],
) -> None:
    for requirement in _dict_list(region1_forest_plan_readiness.get("field_directive_requirements")):
        requirement_id = str(requirement.get("requirement_id") or "")
        if not requirement_id:
            continue
        source_record_ids = _region1_requirement_source_record_ids(requirement)
        blockers = _region1_requirement_blockers(requirement, source_record_ids)
        component_id = _region1_field_directive_component_id(requirement)
        component_node_id = _region1_component_node_id(component_id)
        builder.add_node(
            node_id=component_node_id,
            node_type="forest_plan_component",
            label=f"Region 1 field directive: {requirement_id}",
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": "region1",
                "requirement_id": requirement_id,
                "source_record_ids": source_record_ids,
            },
            readiness_blockers=blockers,
            metadata={
                "component_type": "field_directive_requirement",
                "term_source": "region1_forest_plan_readiness",
                "requirement_type": requirement.get("requirement_type"),
                "readiness_status": requirement.get("readiness_status"),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=component_node_id,
                blockers=blockers,
            )
        _add_region1_requirement_source_edges(
            builder,
            source_set_id=source_set_id,
            component_node_id=component_node_id,
            source_record_ids=source_record_ids,
            requirement_kind="field_directive_requirement",
            requirement_id=requirement_id,
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            blockers=blockers,
        )

    for requirement in _dict_list(region1_forest_plan_readiness.get("overlay_requirements")):
        overlay_id = str(requirement.get("overlay_id") or "")
        if not overlay_id:
            continue
        source_record_ids = _region1_requirement_source_record_ids(requirement)
        blockers = _region1_requirement_blockers(requirement, source_record_ids)
        component_id = _region1_overlay_component_id(requirement)
        component_node_id = _region1_component_node_id(component_id)
        builder.add_node(
            node_id=component_node_id,
            node_type="forest_plan_component",
            label=f"Region 1 overlay: {overlay_id}",
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": "region1",
                "overlay_id": overlay_id,
                "source_record_ids": source_record_ids,
            },
            readiness_blockers=blockers,
            metadata={
                "component_type": "overlay",
                "term_source": "region1_forest_plan_readiness",
                "readiness_status": requirement.get("readiness_status"),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=component_node_id,
                blockers=blockers,
            )
        _add_region1_requirement_source_edges(
            builder,
            source_set_id=source_set_id,
            component_node_id=component_node_id,
            source_record_ids=source_record_ids,
            requirement_kind="overlay_requirement",
            requirement_id=overlay_id,
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            blockers=blockers,
        )


def _add_region1_requirement_source_edges(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    component_node_id: str,
    source_record_ids: list[str],
    requirement_kind: str,
    requirement_id: str,
    display_status: str,
    review_readiness_status: str,
    blockers: list[str],
) -> None:
    for source_record_id in source_record_ids:
        builder.add_edge(
            edge_type="HAS_FOREST_COMPONENT",
            source_node_id=_source_node_id(source_record_id),
            target_node_id=component_node_id,
            display_status=display_status,
            review_readiness_status=review_readiness_status,
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "requirement_kind": requirement_kind,
                "requirement_id": requirement_id,
            },
            readiness_blockers=blockers,
        )


def _add_profile_term_nodes(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    forest_unit_id: str,
    plan_node_id: str | None,
    profile: dict[str, Any],
    display: dict[str, str],
    blockers: list[str],
) -> None:
    term_fields = (
        ("geographic_area_terms", "geographic_area"),
        ("management_area_terms", "management_area"),
        ("overlay_terms", "overlay"),
    )
    active_plan_source_record_id = str(profile.get("active_plan_source_record_id") or "")
    for field, term_kind in term_fields:
        for term in _dict_list(profile.get(field)):
            entry_id = str(term.get("entry_id") or "")
            if not entry_id:
                continue
            component_id = f"profile-term:{forest_unit_id}:{term_kind}:{entry_id}"
            component_node_id = f"forest_plan_component:{component_id}"
            source_record_id = str(term.get("source_record_id") or active_plan_source_record_id)
            builder.add_node(
                node_id=component_node_id,
                node_type="forest_plan_component",
                label=str(term.get("name") or entry_id),
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "component_id": component_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": source_record_id,
                },
                readiness_blockers=blockers,
                metadata={
                    "component_type": term_kind,
                    "profile_term_field": field,
                    "entry_id": entry_id,
                    "aliases": term.get("aliases", []),
                    "term_source": "forest_plan_profile",
                },
            )
            if blockers:
                _add_blocker(
                    builder,
                    source_set_id=source_set_id,
                    subject_node_id=component_node_id,
                    blockers=blockers,
                )
            if plan_node_id:
                builder.add_edge(
                    edge_type="HAS_FOREST_COMPONENT",
                    source_node_id=plan_node_id,
                    target_node_id=component_node_id,
                    display_status=display["display_status"],
                    review_readiness_status=display["review_readiness_status"],
                    provenance={
                        "source_set_id": source_set_id,
                        "forest_code": forest_unit_id,
                        "component_id": component_id,
                    },
                    readiness_blockers=blockers,
                )
            builder.add_edge(
                edge_type="BELONGS_TO_FOREST_UNIT",
                source_node_id=component_node_id,
                target_node_id=_forest_unit_node_id(forest_unit_id),
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "component_id": component_id,
                },
                readiness_blockers=blockers,
            )


def _add_source_set_blockers(
    builder: _GraphBuilder,
    *,
    source_set_node_id: str,
    source_set_id: str,
) -> None:
    _add_blocker(
        builder,
        source_set_id=source_set_id,
        subject_node_id=source_set_node_id,
        blockers=["fsh_chapter_delta_required"],
    )


def _add_review_overlay(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    review_id: str,
    review_artifacts: dict[str, Any],
    inventory: dict[str, Any],
    rule_pack: dict[str, Any],
    base_rule_node_ids: dict[str, str],
    template_node_ids: dict[str, str],
) -> dict[str, Any]:
    authority_universe = _dict(review_artifacts.get("authority_universe_snapshot"))
    candidate_authorities = _dict_list(authority_universe.get("candidate_authorities"))
    decisions = _dict_list(review_artifacts.get("applicability_decisions"))
    search_coverage = _dict(review_artifacts.get("search_coverage_certificates"))
    generated_rule_pack = _dict(review_artifacts.get("generated_rule_pack"))
    compliance_matrix = _dict(review_artifacts.get("compliance_matrix"))
    applicability_validation = _dict(review_artifacts.get("applicability_validation"))
    generated_rule_pack_validation = _dict(review_artifacts.get("generated_rule_pack_validation"))
    compliance_validation = _dict(review_artifacts.get("compliance_validation"))

    family_ids_by_rule_id = _family_ids_by_rule_id(inventory)
    family_id_by_decision_id: dict[str, str] = {}
    review_node_id = _review_node_id(review_id)
    builder.add_node(
        node_id=review_node_id,
        node_type="review",
        label=review_id,
        display_status="active",
        review_readiness_status="reviewer_ready"
        if _review_validation_ready(applicability_validation, generated_rule_pack_validation)
        else "not_reviewer_ready",
        provenance={"review_id": review_id, "source_set_id": source_set_id},
        readiness_blockers=[]
        if _review_validation_ready(applicability_validation, generated_rule_pack_validation)
        else ["package_fixture_missing"],
        metadata={
            "applicability_validation_passed": applicability_validation.get("passed"),
            "generated_rule_pack_validation_passed": generated_rule_pack_validation.get("passed"),
            "compliance_validation_passed": compliance_validation.get("passed"),
            "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
            "generated_rule_pack_id": generated_rule_pack.get("generated_rule_pack_id"),
            "review_artifact_counts": _review_artifact_counts(review_artifacts),
        },
    )

    candidate_by_id = {
        str(candidate.get("candidate_authority_id")): candidate
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_id")
    }
    for candidate in sorted(candidate_authorities, key=lambda item: str(item.get("candidate_authority_id") or "")):
        _add_candidate_authority_overlay_node(
            builder,
            source_set_id=source_set_id,
            candidate=candidate,
            rule_pack=rule_pack,
            base_rule_node_ids=base_rule_node_ids,
            template_node_ids=template_node_ids,
        )

    for decision in sorted(decisions, key=lambda item: str(item.get("decision_id") or "")):
        candidate_id = str(decision.get("candidate_authority_id") or "")
        candidate = candidate_by_id.get(candidate_id, {})
        candidate_node_id = _candidate_authority_node_id(
            candidate or decision,
            base_rule_node_ids=base_rule_node_ids,
            template_node_ids=template_node_ids,
        )
        authority_family_id = _authority_family_id_for_decision(
            decision=decision,
            candidate=candidate,
            family_ids_by_rule_id=family_ids_by_rule_id,
        )
        family_id_by_decision_id[str(decision.get("decision_id") or "")] = authority_family_id
        status = _decision_status(decision)
        blockers = _decision_readiness_blockers(decision)
        decision_node_id = _decision_node_id(review_id, decision)
        builder.add_node(
            node_id=decision_node_id,
            node_type="applicability_decision",
            label=f"{candidate_id} {status}",
            display_status=_decision_display_status(decision),
            review_readiness_status=_decision_review_readiness(decision),
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "authority_family_id": authority_family_id,
                "decision_id": decision.get("decision_id"),
                "candidate_authority_id": candidate_id,
                "candidate_authority_type": decision.get("candidate_authority_type"),
            },
            currentness_metadata={
                "adjudication_state": decision.get("adjudication_state"),
                "basis_type": decision.get("basis_type"),
                "confidence_classification": decision.get("confidence_classification"),
            },
            readiness_blockers=blockers,
            metadata={
                "status": status,
                "applicability_status": status,
                "search_coverage_certificate_ids": decision.get(
                    "search_coverage_certificate_ids", []
                ),
                "human_adjudication_refs": decision.get("human_adjudication_refs", []),
                "retrieval_trace_ids": decision.get("retrieval_trace_ids", []),
                "selected_graph_path_ids": decision.get("selected_graph_path_ids", []),
            },
        )
        builder.update_node(
            candidate_node_id,
            display_status=_decision_display_status(decision),
            review_readiness_status=_decision_review_readiness(decision),
            readiness_blockers=blockers,
            metadata={
                "review_overlay": {
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "status": status,
                    "candidate_authority_id": candidate_id,
                }
            },
        )
        builder.add_edge(
            edge_type="PRODUCES_APPLICABILITY_DECISION",
            source_node_id=candidate_node_id,
            target_node_id=decision_node_id,
            display_status=_decision_display_status(decision),
            review_readiness_status=_decision_review_readiness(decision),
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "decision_id": decision.get("decision_id"),
                "candidate_authority_id": candidate_id,
            },
            readiness_blockers=blockers,
        )
        if status == "applicable":
            builder.add_edge(
                edge_type="APPLIES_TO_REVIEW",
                source_node_id=decision_node_id,
                target_node_id=review_node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "candidate_authority_id": candidate_id,
                },
            )
        elif status == "not_applicable":
            builder.add_edge(
                edge_type="NOT_APPLICABLE_TO_REVIEW",
                source_node_id=decision_node_id,
                target_node_id=review_node_id,
                display_status="not_applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "candidate_authority_id": candidate_id,
                    "search_coverage_certificate_ids": decision.get(
                        "search_coverage_certificate_ids", []
                    ),
                    "human_adjudication_refs": decision.get("human_adjudication_refs", []),
                },
            )
        else:
            blocker_node_id = _review_blocker_node_id(review_id, "adjudication_needed", decision)
            builder.add_node(
                node_id=blocker_node_id,
                node_type="readiness_blocker",
                label="Applicability adjudication needed",
                display_status="readiness_blocked",
                review_readiness_status="needs_adjudication",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "blocker_type": "adjudication_needed",
                    "decision_id": decision.get("decision_id"),
                },
                readiness_blockers=["adjudication_needed"],
            )
            builder.add_edge(
                edge_type="NEEDS_ADJUDICATION",
                source_node_id=decision_node_id,
                target_node_id=blocker_node_id,
                display_status="readiness_blocked",
                review_readiness_status="needs_adjudication",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "candidate_authority_id": candidate_id,
                },
                readiness_blockers=["adjudication_needed"],
            )
        if decision.get("human_adjudication_refs"):
            builder.add_edge(
                edge_type="ADJUDICATED_BY",
                source_node_id=decision_node_id,
                target_node_id=review_node_id,
                display_status="adjudicated",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision.get("decision_id"),
                    "human_adjudication_refs": decision.get("human_adjudication_refs", []),
                },
            )

    generated_rule_node_ids = _add_generated_rules_overlay(
        builder,
        source_set_id=source_set_id,
        review_id=review_id,
        generated_rules=_dict_list(generated_rule_pack.get("rules")),
        decisions_by_id={str(decision.get("decision_id")): decision for decision in decisions},
        family_id_by_decision_id=family_id_by_decision_id,
        family_ids_by_rule_id=family_ids_by_rule_id,
    )
    _add_compliance_finding_overlay(
        builder,
        source_set_id=source_set_id,
        review_id=review_id,
        compliance_rows=_dict_list(compliance_matrix.get("rows")),
        generated_rule_node_ids=generated_rule_node_ids,
    )
    return _review_overlay_summary(
        review_id=review_id,
        candidate_authorities=candidate_authorities,
        decisions=decisions,
        generated_rules=_dict_list(generated_rule_pack.get("rules")),
        compliance_rows=_dict_list(compliance_matrix.get("rows")),
        search_coverage=search_coverage,
        review_artifacts=review_artifacts,
    )


def _add_candidate_authority_overlay_node(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    candidate: dict[str, Any],
    rule_pack: dict[str, Any],
    base_rule_node_ids: dict[str, str],
    template_node_ids: dict[str, str],
) -> None:
    node_id = _candidate_authority_node_id(
        candidate,
        base_rule_node_ids=base_rule_node_ids,
        template_node_ids=template_node_ids,
    )
    candidate_type = str(candidate.get("candidate_authority_type") or "")
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    if candidate_type == "forest_plan_component":
        forest_plan = _dict(candidate.get("forest_plan"))
        component_id = str(forest_plan.get("component_id") or candidate_id.rsplit(":", 1)[-1])
        forest_code = str(forest_plan.get("forest_unit_id") or "unknown_forest_unit")
        builder.add_node(
            node_id=node_id,
            node_type="forest_plan_component",
            label=str(forest_plan.get("section_heading") or component_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": forest_code,
                "candidate_authority_id": candidate_id,
            },
            metadata={
                "candidate_authority_type": candidate_type,
                "authority_category": candidate.get("authority_category"),
            },
        )
        return
    rule_id = _candidate_rule_id(candidate)
    builder.add_node(
        node_id=node_id,
        node_type="rule_template",
        label=rule_id,
        display_status="active",
        review_readiness_status="not_review_specific",
        provenance={
            "source_set_id": source_set_id,
            "rule_id": rule_id,
            "rule_pack_id": rule_pack.get("rule_pack_id"),
            "rule_pack_version": rule_pack.get("version"),
            "candidate_authority_id": candidate_id,
        },
        metadata={
            "candidate_authority_type": candidate_type,
            "authority_category": candidate.get("authority_category"),
            "required_package_fact_types": candidate.get("required_package_fact_types", []),
        },
    )


def _add_generated_rules_overlay(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    review_id: str,
    generated_rules: list[dict[str, Any]],
    decisions_by_id: dict[str, dict[str, Any]],
    family_id_by_decision_id: dict[str, str],
    family_ids_by_rule_id: dict[str, set[str]],
) -> dict[str, str]:
    generated_rule_node_ids: dict[str, str] = {}
    for rule in sorted(generated_rules, key=lambda item: str(item.get("generated_rule_id") or item.get("id") or "")):
        generated_rule_id = str(rule.get("generated_rule_id") or rule.get("id") or "")
        decision_id = str(rule.get("applicability_decision_id") or "")
        decision = decisions_by_id.get(decision_id, {})
        rule_id = str(rule.get("base_rule_id") or rule.get("id") or generated_rule_id)
        authority_family_id = (
            family_id_by_decision_id.get(decision_id)
            or _first_sorted(family_ids_by_rule_id.get(rule_id, set()))
            or "unknown_authority_family"
        )
        node_id = _generated_rule_node_id(review_id, generated_rule_id)
        generated_rule_node_ids[generated_rule_id] = node_id
        generated_rule_node_ids[rule_id] = node_id
        builder.add_node(
            node_id=node_id,
            node_type="generated_rule",
            label=str(rule.get("title") or generated_rule_id),
            display_status="applicable",
            review_readiness_status="reviewer_ready",
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "generated_rule_id": generated_rule_id,
                "authority_family_id": authority_family_id,
                "applicability_decision_id": decision_id,
                "candidate_authority_id": rule.get("candidate_authority_id"),
            },
            metadata={
                "rule_id": rule_id,
                "authority_category": rule.get("authority_category"),
                "authority_source_record_id": rule.get("authority_source_record_id"),
                "severity": rule.get("severity"),
                "applicability_mode": rule.get("applicability_mode"),
            },
        )
        if decision:
            builder.add_edge(
                edge_type="GENERATES_RULE",
                source_node_id=_decision_node_id(review_id, decision),
                target_node_id=node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "decision_id": decision_id,
                    "generated_rule_id": generated_rule_id,
                },
            )
    return generated_rule_node_ids


def _add_compliance_finding_overlay(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    review_id: str,
    compliance_rows: list[dict[str, Any]],
    generated_rule_node_ids: dict[str, str],
) -> None:
    for row in sorted(compliance_rows, key=lambda item: str(item.get("rule_id") or item.get("row_id") or "")):
        finding_id = str(row.get("row_id") or row.get("rule_id") or "")
        if not finding_id:
            continue
        rule_id = str(row.get("rule_id") or finding_id)
        finding_node_id = _compliance_finding_node_id(review_id, finding_id)
        builder.add_node(
            node_id=finding_node_id,
            node_type="compliance_finding",
            label=str(row.get("rule_title") or rule_id),
            display_status="applicable",
            review_readiness_status="reviewer_ready",
            provenance={
                "source_set_id": source_set_id,
                "review_id": review_id,
                "finding_id": finding_id,
                "rule_id": rule_id,
            },
            metadata={
                "status": row.get("status"),
                "applicability_status": row.get("applicability_status"),
                "authority_category": row.get("authority_category"),
                "source_claim_ids": row.get("source_claim_ids", []),
                "candidate_authority_id": row.get("candidate_authority_id"),
            },
        )
        generated_rule_node_id = generated_rule_node_ids.get(rule_id)
        if generated_rule_node_id:
            builder.add_edge(
                edge_type="SUPPORTS_COMPLIANCE_FINDING",
                source_node_id=generated_rule_node_id,
                target_node_id=finding_node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "rule_id": rule_id,
                    "finding_id": finding_id,
                },
            )
        for evidence_kind in ("source_library_evidence", "ea_package_evidence"):
            evidence = _dict(row.get(evidence_kind))
            if not evidence:
                continue
            evidence_node_id = _review_evidence_node_id(review_id, finding_id, evidence_kind, evidence)
            builder.add_node(
                node_id=evidence_node_id,
                node_type="evidence_span",
                label=str(evidence.get("citation_label") or f"{finding_id} {evidence_kind}"),
                display_status="active",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "source_record_id": evidence.get("source_record_id"),
                    "chunk_index": evidence.get("chunk_index") or evidence.get("chunk_id") or 0,
                    "char_start": evidence.get("source_char_start")
                    if evidence.get("source_char_start") is not None
                    else evidence.get("chunk_char_start", 0),
                    "char_end": evidence.get("source_char_end")
                    if evidence.get("source_char_end") is not None
                    else evidence.get("chunk_char_end", 0),
                    "finding_id": finding_id,
                    "evidence_kind": evidence_kind,
                },
                metadata={
                    "artifact_sha256": evidence.get("artifact_sha256"),
                    "content_sha256": evidence.get("content_sha256"),
                    "citation_label": evidence.get("citation_label"),
                    "section": evidence.get("section"),
                    "page": evidence.get("page"),
                },
            )
            builder.add_edge(
                edge_type="SUPPORTS_COMPLIANCE_FINDING",
                source_node_id=evidence_node_id,
                target_node_id=finding_node_id,
                display_status="applicable",
                review_readiness_status="reviewer_ready",
                provenance={
                    "source_set_id": source_set_id,
                    "review_id": review_id,
                    "finding_id": finding_id,
                    "evidence_kind": evidence_kind,
                    "source_record_id": evidence.get("source_record_id"),
                },
            )


def _add_blocker(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    subject_node_id: str,
    blockers: list[str],
) -> None:
    for blocker in sorted(set(blockers)):
        blocker_node_id = f"readiness_blocker:{blocker}:{_stable_digest(subject_node_id)[:16]}"
        builder.add_node(
            node_id=blocker_node_id,
            node_type="readiness_blocker",
            label=blocker.replace("_", " "),
            display_status="readiness_blocked",
            review_readiness_status="blocked",
            provenance={
                "source_set_id": source_set_id,
                "blocker_type": blocker,
                "subject_node_id": subject_node_id,
            },
        )
        builder.add_edge(
            edge_type="HAS_READINESS_BLOCKER",
            source_node_id=subject_node_id,
            target_node_id=blocker_node_id,
            display_status="readiness_blocked",
            review_readiness_status="blocked",
            provenance={
                "source_set_id": source_set_id,
                "blocker_type": blocker,
                "subject_node_id": subject_node_id,
            },
            readiness_blockers=[blocker],
        )


def _region1_profile_readiness_rows(readiness: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(readiness.get("profile_rows"))


def _load_region1_forest_plan_readiness(path: Path) -> dict[str, Any]:
    readiness = _read_json(path)
    if readiness.get("schema_version") == SOURCE_DELTA_READINESS_SCHEMA_VERSION:
        return _normalize_source_delta_region1_readiness(readiness)
    return readiness


def _normalize_source_delta_region1_readiness(report: dict[str, Any]) -> dict[str, Any]:
    baseline = _read_json(DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH)
    baseline_rows_by_unit = {
        str(row.get("forest_unit_id") or ""): row
        for row in _dict_list(baseline.get("profile_rows"))
        if row.get("forest_unit_id")
    }
    merged_source_set_id = str(
        _dict(report.get("merged_source_delta_catalog")).get("source_set_id") or ""
    )
    profile_rows = []
    for row in _dict_list(_dict(report.get("forest_profile_readiness")).get("profile_rows")):
        forest_unit_id = str(row.get("forest_unit_id") or "")
        baseline_row = _dict(baseline_rows_by_unit.get(forest_unit_id))
        configured_profile = bool(row.get("configured_profile"))
        profile_readiness_status = str(row.get("profile_readiness_status") or "")
        graph_promotion_status = _source_delta_graph_promotion_status(
            baseline_row=baseline_row,
            configured_profile=configured_profile,
            profile_readiness_status=profile_readiness_status,
        )
        profile_rows.append(
            {
                "active_plan_source_record_id": row.get("active_plan_source_record_id"),
                "applicability_eval_coverage": _dict(
                    baseline_row.get("applicability_eval_coverage")
                ),
                "component_inventory_validation": _normalized_component_inventory_validation(
                    baseline_row=_dict(baseline_row.get("component_inventory_validation")),
                    merged_source_set_id=merged_source_set_id,
                    graph_promotion_status=graph_promotion_status,
                ),
                "forest_unit_id": forest_unit_id,
                "forest_unit_names": _strings(row.get("forest_unit_names")),
                "graph_promotion_status": graph_promotion_status,
                "milestone_5_added_profile": bool(
                    baseline_row.get("milestone_5_added_profile")
                ),
                "profile_kind": row.get("profile_kind"),
                "readiness_blockers": sorted(
                    set(_strings(row.get("blocker_types")))
                    | (
                        set()
                        if graph_promotion_status == "promoted"
                        else {"forest_profile_not_ready"}
                    )
                ),
                "source_requirements": _dict_list(row.get("source_requirements")),
            }
        )
    return {
        "schema_version": REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
        "readiness_matrix_id": "region1-forest-plan-readiness-support-corpus-v1",
        "source_set_id": merged_source_set_id,
        "region1_completeness_claim": False,
        "field_directive_requirements": _dict_list(
            baseline.get("field_directive_requirements")
        ),
        "overlay_requirements": _dict_list(baseline.get("overlay_requirements")),
        "profile_rows": profile_rows,
        "support_document_corpus_summary": _source_delta_support_document_summary(report),
        "source_delta_readiness_schema_version": report.get("schema_version"),
    }


def _source_delta_graph_promotion_status(
    *,
    baseline_row: dict[str, Any],
    configured_profile: bool,
    profile_readiness_status: str,
) -> str:
    component_inventory_validation = _dict(baseline_row.get("component_inventory_validation"))
    component_inventory_status = str(component_inventory_validation.get("status") or "")
    component_inventory_ready = not component_inventory_status or component_inventory_status == "validated"
    if configured_profile and profile_readiness_status == "ready" and component_inventory_ready:
        return "promoted"
    if configured_profile:
        return "blocked"
    if profile_readiness_status == "ready":
        return "tracked_not_promoted"
    return "blocked"


def _normalized_component_inventory_validation(
    *,
    baseline_row: dict[str, Any],
    merged_source_set_id: str,
    graph_promotion_status: str,
) -> dict[str, Any]:
    if not baseline_row:
        return {"status": "component_inventory_build_required"}
    normalized = dict(baseline_row)
    artifact_path = str(normalized.get("artifact_path") or "")
    if artifact_path and graph_promotion_status == "promoted":
        normalized["artifact_path"] = _rewrite_support_corpus_artifact_path(
            artifact_path,
            merged_source_set_id=merged_source_set_id,
        )
    return normalized


def _rewrite_support_corpus_artifact_path(
    path: str, *, merged_source_set_id: str
) -> str:
    parts = list(Path(path).parts)
    for index, part in enumerate(parts):
        if part.startswith("source-set-"):
            parts[index] = merged_source_set_id
            break
    return str(Path(*parts))


def _source_delta_support_document_summary(report: dict[str, Any]) -> dict[str, Any]:
    merged_catalog = _dict(report.get("merged_source_delta_catalog"))
    source_delta_input = _dict(merged_catalog.get("source_delta_input"))
    extraction = _dict(report.get("extraction_readiness"))
    retrieval = _dict(report.get("retrieval_readiness"))
    profiles = _dict(report.get("forest_profile_readiness"))
    official_gaps = _dict(report.get("official_source_gap_evidence"))
    return {
        "source_set_id": merged_catalog.get("source_set_id"),
        "catalog_source_record_count": merged_catalog.get("catalog_source_record_count"),
        "catalog_confirmed_source_record_count": source_delta_input.get(
            "catalog_confirmed_count"
        ),
        "support_document_source_delta_count": source_delta_input.get("source_delta_count"),
        "official_source_gap_count": official_gaps.get("record_count"),
        "official_source_gap_source_record_ids": _strings(
            official_gaps.get("source_record_ids")
        ),
        "extracted_support_document_source_record_count": extraction.get(
            "extracted_source_record_count"
        ),
        "blocked_support_document_source_record_count": extraction.get(
            "blocked_source_record_count"
        ),
        "indexed_support_document_source_record_count": retrieval.get(
            "indexed_source_record_count_for_expected_sources"
        ),
        "configured_profile_ready_count": profiles.get("ready_profile_count"),
        "configured_profile_blocked_count": profiles.get("blocked_profile_count"),
        "tracking_only_ready_count": profiles.get("ready_tracking_only_count"),
        "tracking_only_blocked_count": profiles.get("blocked_tracking_only_count"),
    }


def _region1_profile_readiness_by_unit(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("forest_unit_id")): row
        for row in _region1_profile_readiness_rows(readiness)
        if row.get("forest_unit_id")
    }


def _region1_profile_readiness_blockers(row: dict[str, Any]) -> list[str]:
    blockers = set(_strings(row.get("readiness_blockers")))
    if row and str(row.get("graph_promotion_status") or "") != "promoted":
        blockers.add("forest_profile_not_ready")
    for requirement in _dict_list(row.get("source_requirements")):
        if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
            blockers.add("missing_source")
    return sorted(blockers)


def _region1_profile_display(row: dict[str, Any]) -> dict[str, str]:
    if row and str(row.get("graph_promotion_status") or "") != "promoted":
        return {"display_status": "readiness_blocked", "review_readiness_status": "blocked"}
    return {"display_status": "active", "review_readiness_status": "not_review_specific"}


def _region1_requirement_source_record_ids(requirement: dict[str, Any]) -> list[str]:
    source_record_ids = set(_strings(requirement.get("source_record_ids")))
    source_record_id = str(requirement.get("source_record_id") or "")
    if source_record_id:
        source_record_ids.add(source_record_id)
    return sorted(source_record_ids)


def _region1_requirement_blockers(
    requirement: dict[str, Any], source_record_ids: list[str]
) -> list[str]:
    if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
        return ["missing_source"]
    if not source_record_ids:
        return ["missing_source"]
    return []


def _region1_component_node_id(component_id: str) -> str:
    return f"forest_plan_component:{component_id}"


def _region1_field_directive_component_id(requirement: dict[str, Any]) -> str:
    return f"region1-field-directive:{requirement.get('requirement_id')}"


def _region1_overlay_component_id(requirement: dict[str, Any]) -> str:
    return f"region1-overlay:{requirement.get('overlay_id')}"


def _region1_requirement_source_gaps(
    readiness: dict[str, Any],
    *,
    catalog_source_ids: set[str],
) -> dict[str, list[str]]:
    gaps = {}
    for requirement in _dict_list(readiness.get("field_directive_requirements")):
        if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
            continue
        missing = _region1_missing_requirement_source_ids(requirement, catalog_source_ids)
        if missing:
            gaps[f"field_directive:{requirement.get('requirement_id')}"] = missing
    for requirement in _dict_list(readiness.get("overlay_requirements")):
        if str(requirement.get("readiness_status") or "") != "catalog_confirmed":
            continue
        missing = _region1_missing_requirement_source_ids(requirement, catalog_source_ids)
        if missing:
            gaps[f"overlay:{requirement.get('overlay_id')}"] = missing
    return gaps


def _region1_missing_requirement_source_ids(
    requirement: dict[str, Any],
    catalog_source_ids: set[str],
) -> list[str]:
    source_record_ids = _region1_requirement_source_record_ids(requirement)
    if not source_record_ids:
        return ["<missing source_record_id>"]
    return sorted(source_record_id for source_record_id in source_record_ids if source_record_id not in catalog_source_ids)


def _region1_requirement_edge_gaps(
    readiness: dict[str, Any],
    *,
    edge_tuples: set[tuple[str, str, str]],
) -> dict[str, list[str]]:
    gaps = {}
    for requirement in _dict_list(readiness.get("field_directive_requirements")):
        requirement_id = str(requirement.get("requirement_id") or "")
        if not requirement_id:
            continue
        component_node_id = _region1_component_node_id(
            _region1_field_directive_component_id(requirement)
        )
        missing = _region1_missing_requirement_source_edges(
            requirement,
            component_node_id=component_node_id,
            edge_tuples=edge_tuples,
        )
        if missing:
            gaps[f"field_directive:{requirement_id}"] = missing
    for requirement in _dict_list(readiness.get("overlay_requirements")):
        overlay_id = str(requirement.get("overlay_id") or "")
        if not overlay_id:
            continue
        component_node_id = _region1_component_node_id(_region1_overlay_component_id(requirement))
        missing = _region1_missing_requirement_source_edges(
            requirement,
            component_node_id=component_node_id,
            edge_tuples=edge_tuples,
        )
        if missing:
            gaps[f"overlay:{overlay_id}"] = missing
    return gaps


def _region1_missing_requirement_source_edges(
    requirement: dict[str, Any],
    *,
    component_node_id: str,
    edge_tuples: set[tuple[str, str, str]],
) -> list[str]:
    missing = []
    for source_record_id in _region1_requirement_source_record_ids(requirement):
        if ("HAS_FOREST_COMPONENT", _source_node_id(source_record_id), component_node_id) not in edge_tuples:
            missing.append(source_record_id)
    return sorted(missing)


def _region1_readiness_summary(readiness: dict[str, Any]) -> dict[str, Any]:
    rows = _region1_profile_readiness_rows(readiness)
    added_rows = [row for row in rows if row.get("milestone_5_added_profile")]
    promoted_rows = [row for row in rows if row.get("graph_promotion_status") == "promoted"]
    blocked_rows = [row for row in rows if row.get("graph_promotion_status") != "promoted"]
    field_directive_requirements = _dict_list(readiness.get("field_directive_requirements"))
    overlay_requirements = _dict_list(readiness.get("overlay_requirements"))
    support_document_summary = _dict(readiness.get("support_document_corpus_summary"))
    return {
        "region1_forest_plan_readiness_profile_count": len(rows),
        "region1_forest_plan_graph_ready_profile_count": len(promoted_rows),
        "region1_forest_plan_blocked_profile_count": len(blocked_rows),
        "region1_forest_plan_added_profile_count": len(added_rows),
        "region1_forest_plan_added_profiles_with_eval_fixture_count": sum(
            1 for row in added_rows if _region1_profile_has_positive_and_negative_fixtures(row)
        ),
        "region1_forest_plan_completeness_claim": bool(
            readiness.get("region1_completeness_claim")
        ),
        "region1_field_directive_requirement_count": len(field_directive_requirements),
        "region1_overlay_requirement_count": len(overlay_requirements),
        "region1_field_directive_requirement_graph_node_count": sum(
            1
            for requirement in field_directive_requirements
            if requirement.get("requirement_id")
        ),
        "region1_overlay_requirement_graph_node_count": sum(
            1 for requirement in overlay_requirements if requirement.get("overlay_id")
        ),
        "region1_support_document_corpus_catalog_source_record_count": support_document_summary.get(
            "catalog_source_record_count"
        ),
        "region1_support_document_corpus_source_delta_count": support_document_summary.get(
            "support_document_source_delta_count"
        ),
        "region1_support_document_corpus_catalog_confirmed_source_record_count": support_document_summary.get(
            "catalog_confirmed_source_record_count"
        ),
        "region1_support_document_corpus_official_source_gap_count": support_document_summary.get(
            "official_source_gap_count"
        ),
        "region1_support_document_corpus_extracted_source_record_count": support_document_summary.get(
            "extracted_support_document_source_record_count"
        ),
        "region1_support_document_corpus_blocked_source_record_count": support_document_summary.get(
            "blocked_support_document_source_record_count"
        ),
        "region1_support_document_corpus_indexed_source_record_count": support_document_summary.get(
            "indexed_support_document_source_record_count"
        ),
        "region1_support_document_corpus_tracking_only_ready_count": support_document_summary.get(
            "tracking_only_ready_count"
        ),
        "region1_support_document_corpus_tracking_only_blocked_count": support_document_summary.get(
            "tracking_only_blocked_count"
        ),
    }


def _region1_profile_has_positive_and_negative_fixtures(row: dict[str, Any]) -> bool:
    coverage = _dict(row.get("applicability_eval_coverage"))
    fixtures = _dict_list(coverage.get("fixtures"))
    fixture_types = {str(fixture.get("fixture_type") or "") for fixture in fixtures}
    return (
        "positive" in fixture_types
        and "hard_negative" in fixture_types
        and int(coverage.get("positive_case_count") or 0) >= 1
        and int(coverage.get("hard_negative_case_count") or 0) >= 1
    )


def _source_display_status(
    *,
    row: dict[str, Any],
    currentness: dict[str, Any],
    partition: dict[str, Any],
) -> dict[str, str]:
    source_partition = partition.get("source_partition") or currentness.get("source_partition")
    source_status = row.get("source_status") or currentness.get("source_status")
    supersession_status = currentness.get("supersession_status")
    if source_status == "skipped_excluded":
        return {"display_status": "out_of_scope", "review_readiness_status": "blocked"}
    if source_partition == "candidate_blocked_source":
        return {"display_status": "candidate", "review_readiness_status": "blocked"}
    if source_partition == "currentness_supersession_archive":
        display_status = "reserved" if "reserved" in str(row.get("title") or "").lower() else "superseded"
        return {
            "display_status": display_status,
            "review_readiness_status": "source_currentness_only",
        }
    if supersession_status == "superseded_replacement_source":
        return {"display_status": "superseded", "review_readiness_status": "source_currentness_only"}
    return {"display_status": "active", "review_readiness_status": "reviewer_ready"}


def _source_readiness_blockers(
    *,
    row: dict[str, Any],
    currentness: dict[str, Any],
    partition: dict[str, Any],
) -> list[str]:
    source_partition = partition.get("source_partition") or currentness.get("source_partition")
    source_status = row.get("source_status") or currentness.get("source_status")
    supersession_status = currentness.get("supersession_status")
    if source_status == "skipped_excluded":
        return ["missing_source"]
    if source_partition == "candidate_blocked_source":
        return ["missing_source"]
    if source_partition == "currentness_supersession_archive" or supersession_status == "superseded_replacement_source":
        return ["superseded_source"]
    return []


def _family_display_status(family: dict[str, Any], currentness: dict[str, Any]) -> dict[str, str]:
    status = str(family.get("status") or currentness.get("family_status") or "")
    currentness_status = str(currentness.get("currentness_status") or "")
    if status == "candidate":
        return {"display_status": "candidate", "review_readiness_status": "blocked"}
    if status == "superseded":
        return {"display_status": "superseded", "review_readiness_status": "source_currentness_only"}
    if currentness_status in {"missing_source_addition_decision", "source_currentness_failed"}:
        return {"display_status": "readiness_blocked", "review_readiness_status": "blocked"}
    return {"display_status": "active", "review_readiness_status": "reviewer_ready"}


def _family_readiness_blockers(family: dict[str, Any], currentness: dict[str, Any]) -> list[str]:
    status = str(family.get("status") or currentness.get("family_status") or "")
    if status == "candidate":
        return ["missing_source"]
    if status == "superseded":
        return ["superseded_source"]
    if currentness.get("failed_source_record_count"):
        return ["missing_source"]
    return []


def _currentness_metadata(
    *,
    currentness: dict[str, Any],
    partition: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_partition": partition.get("source_partition") or currentness.get("source_partition"),
        "source_partition_basis": partition.get("source_partition_basis")
        or currentness.get("source_partition_basis"),
        "supersession_status": currentness.get("supersession_status"),
        "currentness_status": currentness.get("currentness_status"),
        "counts_as_current_authority": currentness.get("counts_as_current_authority"),
        "capture_date": currentness.get("capture_date"),
        "effective_date": currentness.get("effective_date"),
    }


def _source_set_readiness_blockers(currentness: dict[str, Any]) -> list[str]:
    contract = _dict(currentness.get("source_partition_contract"))
    delta_plan = _dict(contract.get("workbook_source_delta_plan"))
    return ["fsh_chapter_delta_required"] if delta_plan.get("fsh_1909_15") else []


def _source_currentness_by_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        source_record_id = str(record.get("source_record_id") or "")
        if not source_record_id:
            continue
        existing = by_id.get(source_record_id)
        if existing is None or record.get("counts_as_current_authority"):
            by_id[source_record_id] = record
    return by_id


def _node_metadata_counts(
    nodes: list[dict[str, Any]],
    key: str,
    *,
    node_type: str | None = None,
) -> dict[str, int]:
    return _sorted_counts(
        _dict(node.get("metadata")).get(key)
        for node in nodes
        if node_type is None or node.get("node_type") == node_type
    )


def _node_currentness_counts(
    nodes: list[dict[str, Any]],
    key: str,
    *,
    node_type: str | None = None,
) -> dict[str, int]:
    return _sorted_counts(
        _dict(node.get("currentness_metadata")).get(key)
        for node in nodes
        if node_type is None or node.get("node_type") == node_type
    )


def _sorted_counts(values: Iterable[Any]) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                str(value)
                for value in values
                if value is not None and not isinstance(value, (list, dict, tuple, set))
            ).items()
        )
    )


def _missing_summary_count_fields(graph: dict[str, Any]) -> list[str]:
    summary = _dict(graph.get("summary"))
    required_fields = [
        "node_type_counts",
        "edge_type_counts",
        "authority_category_counts",
        "source_status_counts",
        "source_partition_counts",
        "applicability_status_counts",
        "readiness_blocker_counts",
    ]
    return [
        field
        for field in required_fields
        if not isinstance(summary.get(field), dict)
    ]


def _summary(
    *,
    source_set_id: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    catalog_rows: list[dict[str, Any]],
    inventory: dict[str, Any],
    rule_pack: dict[str, Any],
    template_config: dict[str, Any],
    rule_claim_links: list[dict[str, Any]],
    forest_components: dict[str, Any],
    forest_plan_profiles: dict[str, Any],
    region1_forest_plan_readiness: dict[str, Any],
    currentness: dict[str, Any],
    inputs: list[dict[str, Any]],
    catalog_graph_node_count: int,
    catalog_graph_edge_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": "nepa-3d-knowledge-graph-summary-v1",
        "source_set_id": source_set_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(Counter(str(node.get("node_type")) for node in nodes)),
        "edge_type_counts": dict(Counter(str(edge.get("edge_type")) for edge in edges)),
        "display_status_counts": dict(
            Counter(str(record.get("display_status")) for record in nodes + edges)
        ),
        "review_readiness_status_counts": dict(
            Counter(str(record.get("review_readiness_status")) for record in nodes + edges)
        ),
        "authority_category_counts": _node_metadata_counts(nodes, "authority_category"),
        "source_status_counts": _node_metadata_counts(
            nodes,
            "source_status",
            node_type="source_record",
        ),
        "source_partition_counts": _node_currentness_counts(
            nodes,
            "source_partition",
            node_type="source_record",
        ),
        "source_currentness_status_counts": _node_currentness_counts(
            nodes,
            "currentness_status",
            node_type="source_record",
        ),
        "applicability_status_counts": _node_metadata_counts(nodes, "applicability_status"),
        "readiness_blocker_counts": dict(
            Counter(
                blocker
                for record in nodes + edges
                for blocker in _strings(record.get("readiness_blockers"))
            )
        ),
        "catalog_source_record_count": len(catalog_rows),
        "catalog_graph_node_count": catalog_graph_node_count,
        "catalog_graph_edge_count": catalog_graph_edge_count,
        "authority_family_count": len(inventory.get("authority_families", [])),
        "base_rule_count": len(rule_pack.get("rules", [])),
        "authority_family_rule_template_count": len(template_config.get("templates", [])),
        "rule_claim_link_count": len(rule_claim_links),
        "forest_plan_profile_count": len(forest_plan_profiles.get("profiles", [])),
        "forest_plan_component_count": len(forest_components.get("components", [])),
        "currentness_validation_passed": currentness.get("validation", {}).get("passed")
        if isinstance(currentness.get("validation"), dict)
        else currentness.get("summary", {}).get("validation_passed"),
        "input_count": len(inputs),
        **_region1_readiness_summary(region1_forest_plan_readiness),
    }


def _milestone_validation_checks(
    *,
    graph: dict[str, Any],
    inventory: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    rule_pack: dict[str, Any],
    template_config: dict[str, Any],
    currentness: dict[str, Any],
    rule_claim_links: list[dict[str, Any]],
    forest_components: dict[str, Any],
    forest_plan_profiles: dict[str, Any],
    region1_forest_plan_readiness: dict[str, Any],
    forest_plan_components_path: Path,
    inputs: list[dict[str, Any]],
    catalog_graph_node_count: int,
    catalog_graph_edge_count: int,
    output_dir: Path,
    source_set_id: str,
) -> list[dict[str, Any]]:
    node_ids = {node["node_id"] for node in graph["nodes"]}
    edge_tuples = {
        (
            str(edge.get("edge_type") or ""),
            str(edge.get("source_node_id") or ""),
            str(edge.get("target_node_id") or ""),
        )
        for edge in _dict_list(graph.get("edges"))
    }
    display_status_by_node_id = {node["node_id"]: node["display_status"] for node in graph["nodes"]}
    family_ids = {str(family.get("family_id")) for family in inventory.get("authority_families", [])}
    source_record_ids = {str(row.get("source_record_id")) for row in catalog_rows}
    rule_ids = {str(rule.get("id")) for rule in rule_pack.get("rules", [])}
    template_ids = {str(template.get("template_id")) for template in template_config.get("templates", [])}
    exported_family_ids = {
        node["provenance"].get("authority_family_id")
        for node in graph["nodes"]
        if node["node_type"] == "authority_family"
    }
    exported_source_record_ids = {
        node["provenance"].get("source_record_id")
        for node in graph["nodes"]
        if node["node_type"] == "source_record"
    }
    exported_rule_ids = {
        node["provenance"].get("rule_id")
        for node in graph["nodes"]
        if node["node_type"] == "rule_template"
        and node.get("metadata", {}).get("rule_kind") == "base_rule_pack_rule"
    }
    exported_template_ids = {
        node["provenance"].get("template_id")
        for node in graph["nodes"]
        if node["node_type"] == "rule_template"
        and node.get("metadata", {}).get("rule_kind") == "authority_family_template"
    }
    exported_forest_unit_ids = {
        node["provenance"].get("forest_code")
        for node in graph["nodes"]
        if node["node_type"] == "forest_unit"
    }
    active_profile_ids = {
        str(profile.get("forest_unit_id") or "")
        for profile in _dict_list(forest_plan_profiles.get("profiles"))
        if profile.get("forest_unit_id")
    }
    known_region1_unit_ids = {
        str(unit.get("forest_unit_id") or "")
        for unit in _dict_list(forest_plan_profiles.get("known_other_forest_units"))
        if unit.get("forest_unit_id")
    }
    readiness_rows = _region1_profile_readiness_rows(region1_forest_plan_readiness)
    readiness_ids = {
        str(row.get("forest_unit_id") or "") for row in readiness_rows if row.get("forest_unit_id")
    }
    added_profile_rows = [row for row in readiness_rows if row.get("milestone_5_added_profile")]
    blocked_profile_ids_without_blockers = sorted(
        str(row.get("forest_unit_id") or "")
        for row in readiness_rows
        if row.get("graph_promotion_status") != "promoted"
        and not _region1_profile_readiness_blockers(row)
    )
    promoted_rows = [
        row for row in readiness_rows if row.get("graph_promotion_status") == "promoted"
    ]
    catalog_source_ids = {str(row.get("source_record_id") or "") for row in catalog_rows}
    promoted_missing_sources = {
        str(row.get("forest_unit_id") or ""): sorted(
            source_record_id
            for source_record_id in (
                str(requirement.get("source_record_id") or "")
                for requirement in _dict_list(row.get("source_requirements"))
                if requirement.get("readiness_status") == "catalog_confirmed"
            )
            if source_record_id and source_record_id not in catalog_source_ids
        )
        for row in promoted_rows
    }
    promoted_missing_sources = {
        forest_unit_id: missing
        for forest_unit_id, missing in promoted_missing_sources.items()
        if missing
    }
    component_forest_unit_ids = {
        str(component.get("forest_unit_id") or "")
        for component in _dict_list(forest_components.get("components"))
        if component.get("forest_unit_id")
    }
    promoted_without_inventory = sorted(
        str(row.get("forest_unit_id") or "")
        for row in promoted_rows
        if str(row.get("forest_unit_id") or "") not in component_forest_unit_ids
    )
    overclaim = bool(region1_forest_plan_readiness.get("region1_completeness_claim"))
    non_promoted_readiness_ids = {
        str(row.get("forest_unit_id") or "")
        for row in readiness_rows
        if row.get("graph_promotion_status") != "promoted"
    }
    candidate_family_ids = {
        str(family.get("family_id"))
        for family in inventory.get("authority_families", [])
        if family.get("status") == "candidate"
    }
    superseded_family_ids = {
        str(family.get("family_id"))
        for family in inventory.get("authority_families", [])
        if family.get("status") == "superseded"
    }
    input_failures = [
        input_record["name"] for input_record in inputs if not input_record.get("exists")
    ]
    field_directive_requirement_node_ids = {
        _region1_component_node_id(_region1_field_directive_component_id(requirement))
        for requirement in _dict_list(
            region1_forest_plan_readiness.get("field_directive_requirements")
        )
        if requirement.get("requirement_id")
    }
    overlay_requirement_node_ids = {
        _region1_component_node_id(_region1_overlay_component_id(requirement))
        for requirement in _dict_list(region1_forest_plan_readiness.get("overlay_requirements"))
        if requirement.get("overlay_id")
    }
    region1_requirement_source_gaps = _region1_requirement_source_gaps(
        region1_forest_plan_readiness,
        catalog_source_ids=catalog_source_ids,
    )
    region1_requirement_edge_gaps = _region1_requirement_edge_gaps(
        region1_forest_plan_readiness,
        edge_tuples=edge_tuples,
    )
    inventory_ownership = _forest_plan_inventory_ownership(
        forest_components=forest_components,
        forest_plan_components_path=forest_plan_components_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    return [
        _check("nepa_3d_graph_inputs_exist", not input_failures, [], input_failures),
        _check(
            "nepa_3d_graph_reads_catalog_graph_seeds",
            catalog_graph_node_count > 0 and catalog_graph_edge_count > 0,
            {"catalog_graph_node_count": "> 0", "catalog_graph_edge_count": "> 0"},
            {
                "catalog_graph_node_count": catalog_graph_node_count,
                "catalog_graph_edge_count": catalog_graph_edge_count,
            },
        ),
        _check(
            "nepa_3d_graph_reports_required_summary_count_fields",
            not _missing_summary_count_fields(graph),
            [
                "node_type_counts",
                "edge_type_counts",
                "authority_category_counts",
                "source_status_counts",
                "source_partition_counts",
                "applicability_status_counts",
                "readiness_blocker_counts",
            ],
            _missing_summary_count_fields(graph),
        ),
        _check(
            "nepa_3d_graph_currentness_gate_passed",
            bool(
                _dict(currentness.get("validation")).get("passed")
                or _dict(currentness.get("summary")).get("validation_passed")
            ),
            True,
            {
                "validation": _dict(currentness.get("validation")).get("passed"),
                "summary": _dict(currentness.get("summary")).get("validation_passed"),
            },
        ),
        _check(
            "nepa_3d_graph_exports_all_authority_families",
            family_ids <= exported_family_ids,
            sorted(family_ids),
            sorted(family_ids - exported_family_ids),
        ),
        _check(
            "nepa_3d_graph_exports_all_catalog_source_records",
            source_record_ids <= exported_source_record_ids,
            sorted(source_record_ids),
            sorted(source_record_ids - exported_source_record_ids),
        ),
        _check(
            "nepa_3d_graph_exports_all_base_rules",
            rule_ids <= exported_rule_ids,
            sorted(rule_ids),
            sorted(rule_ids - exported_rule_ids),
        ),
        _check(
            "nepa_3d_graph_exports_all_authority_family_templates",
            template_ids <= exported_template_ids,
            sorted(template_ids),
            sorted(template_ids - exported_template_ids),
        ),
        _check(
            "nepa_3d_graph_exports_candidate_families",
            all(display_status_by_node_id.get(_family_node_id(family_id)) == "candidate" for family_id in candidate_family_ids),
            sorted(candidate_family_ids),
            {
                family_id: display_status_by_node_id.get(_family_node_id(family_id))
                for family_id in sorted(candidate_family_ids)
            },
        ),
        _check(
            "nepa_3d_graph_exports_superseded_families",
            all(display_status_by_node_id.get(_family_node_id(family_id)) == "superseded" for family_id in superseded_family_ids),
            sorted(superseded_family_ids),
            {
                family_id: display_status_by_node_id.get(_family_node_id(family_id))
                for family_id in sorted(superseded_family_ids)
            },
        ),
        _check(
            "nepa_3d_graph_uses_rule_claim_links",
            bool(rule_claim_links),
            "at least one rule claim link",
            len(rule_claim_links),
        ),
        _check(
            "nepa_3d_graph_exports_forest_plan_components",
            bool(forest_components.get("components")),
            "at least one forest plan component",
            len(forest_components.get("components", [])),
        ),
        _check(
            "nepa_3d_graph_forest_plan_inventory_owned_by_source_set",
            inventory_ownership["passed"],
            inventory_ownership["expected"],
            inventory_ownership["actual"],
        ),
        _check(
            "nepa_3d_graph_region1_readiness_matrix_loaded",
            region1_forest_plan_readiness.get("schema_version")
            == REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
            REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
            region1_forest_plan_readiness.get("schema_version"),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_covers_configured_profiles",
            active_profile_ids <= readiness_ids,
            sorted(active_profile_ids),
            sorted(active_profile_ids - readiness_ids),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_tracks_known_region1_units",
            known_region1_unit_ids <= readiness_ids,
            sorted(known_region1_unit_ids),
            sorted(known_region1_unit_ids - readiness_ids),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_prevents_overclaim",
            not overclaim or not non_promoted_readiness_ids,
            "region1_completeness_claim is false until every tracked profile is promoted",
            {
                "region1_completeness_claim": overclaim,
                "non_promoted_profile_ids": sorted(non_promoted_readiness_ids),
            },
        ),
        _check(
            "nepa_3d_graph_exports_region1_forest_units",
            readiness_ids <= exported_forest_unit_ids,
            sorted(readiness_ids),
            sorted(readiness_ids - exported_forest_unit_ids),
        ),
        _check(
            "nepa_3d_graph_region1_added_profiles_have_eval_fixtures",
            bool(added_profile_rows)
            and all(_region1_profile_has_positive_and_negative_fixtures(row) for row in added_profile_rows),
            "positive and hard-negative fixture contract for each Milestone 5 added profile",
            {
                str(row.get("forest_unit_id") or ""): _region1_profile_has_positive_and_negative_fixtures(row)
                for row in added_profile_rows
            },
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_inventory",
            not promoted_without_inventory,
            "component inventory for each graph-promoted profile",
            promoted_without_inventory,
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_catalog_sources",
            not promoted_missing_sources,
            "catalog-confirmed source records exist for each graph-promoted profile",
            promoted_missing_sources,
        ),
        _check(
            "nepa_3d_graph_exports_region1_field_directive_requirements",
            field_directive_requirement_node_ids <= node_ids,
            sorted(field_directive_requirement_node_ids),
            sorted(field_directive_requirement_node_ids - node_ids),
        ),
        _check(
            "nepa_3d_graph_exports_region1_overlay_requirements",
            overlay_requirement_node_ids <= node_ids,
            sorted(overlay_requirement_node_ids),
            sorted(overlay_requirement_node_ids - node_ids),
        ),
        _check(
            "nepa_3d_graph_region1_requirement_sources_are_cataloged",
            not region1_requirement_source_gaps,
            "catalog-confirmed field directive and overlay source records exist",
            region1_requirement_source_gaps,
        ),
        _check(
            "nepa_3d_graph_region1_requirement_sources_are_linked",
            not region1_requirement_edge_gaps,
            "HAS_FOREST_COMPONENT edges from source records to field directive and overlay nodes",
            region1_requirement_edge_gaps,
        ),
        _check(
            "nepa_3d_graph_region1_blocked_profiles_have_blockers",
            not blocked_profile_ids_without_blockers,
            "readiness blockers for each non-promoted profile",
            blocked_profile_ids_without_blockers,
        ),
        _check(
            "nepa_3d_graph_has_readiness_blocker_nodes",
            any(node_id.startswith("readiness_blocker:") for node_id in node_ids),
            "readiness blocker nodes present",
            sorted(node_id for node_id in node_ids if node_id.startswith("readiness_blocker:")),
        ),
    ]


def _review_overlay_validation_checks(
    *,
    graph: dict[str, Any],
    review_id: str,
    review_artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    authority_universe = _dict(review_artifacts.get("authority_universe_snapshot"))
    candidate_authorities = _dict_list(authority_universe.get("candidate_authorities"))
    decisions = _dict_list(review_artifacts.get("applicability_decisions"))
    search_coverage = _dict(review_artifacts.get("search_coverage_certificates"))
    generated_rule_pack = _dict(review_artifacts.get("generated_rule_pack"))
    compliance_matrix = _dict(review_artifacts.get("compliance_matrix"))
    applicability_validation = _dict(review_artifacts.get("applicability_validation"))
    generated_rule_pack_validation = _dict(review_artifacts.get("generated_rule_pack_validation"))
    compliance_validation = _dict(review_artifacts.get("compliance_validation"))
    review_input_gaps = _review_required_input_gaps(graph)
    coverage_reference_gaps = _search_coverage_reference_gaps(
        decisions,
        certificates_by_id={
            str(certificate.get("coverage_certificate_id")): certificate
            for certificate in _dict_list(search_coverage.get("certificates"))
            if certificate.get("coverage_certificate_id")
        },
    )
    retrieval_trace_reference_gaps = _trace_reference_gaps(
        decisions,
        trace_field="retrieval_trace_ids",
        available_ids={
            str(record.get("retrieval_trace_id"))
            for record in _dict_list(review_artifacts.get("applicability_retrieval_trace"))
            if record.get("retrieval_trace_id")
        },
    )
    graph_trace_reference_gaps = _graph_trace_reference_gaps(
        decisions,
        available_ids={
            str(record.get("graph_path_id"))
            for record in _dict_list(review_artifacts.get("applicability_graph_trace"))
            if record.get("graph_path_id")
        },
    )

    node_ids = {str(node.get("node_id")) for node in _dict_list(graph.get("nodes"))}
    edges = _dict_list(graph.get("edges"))
    edge_tuples = {
        (
            str(edge.get("edge_type") or ""),
            str(edge.get("source_node_id") or ""),
            str(edge.get("target_node_id") or ""),
        )
        for edge in edges
    }
    decision_by_candidate_id: dict[str, list[dict[str, Any]]] = {}
    decisions_by_id: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        decision_by_candidate_id.setdefault(str(decision.get("candidate_authority_id") or ""), []).append(
            decision
        )
        decisions_by_id[str(decision.get("decision_id") or "")] = decision
    candidate_node_gaps = sorted(
        str(candidate.get("candidate_authority_id") or "")
        for candidate in candidate_authorities
        if _candidate_authority_node_id(candidate, base_rule_node_ids={}, template_node_ids={})
        not in node_ids
    )
    decision_cardinality_gaps = {
        str(candidate.get("candidate_authority_id") or ""): len(
            decision_by_candidate_id.get(str(candidate.get("candidate_authority_id") or ""), [])
        )
        for candidate in candidate_authorities
        if len(decision_by_candidate_id.get(str(candidate.get("candidate_authority_id") or ""), []))
        != 1
    }
    decision_mapping_gaps = sorted(
        str(decision.get("decision_id") or "")
        for decision in decisions
        if str(decision.get("candidate_authority_id") or "")
        not in {
            str(candidate.get("candidate_authority_id") or "")
            for candidate in candidate_authorities
        }
    )
    decision_edge_gaps = sorted(
        str(decision.get("decision_id") or "")
        for decision in decisions
        if (
            "PRODUCES_APPLICABILITY_DECISION",
            _candidate_authority_node_id(
                decision,
                base_rule_node_ids={},
                template_node_ids={},
            ),
            _decision_node_id(review_id, decision),
        )
        not in edge_tuples
    )
    unsupported_non_applicable = sorted(
        str(decision.get("decision_id") or "")
        for decision in decisions
        if _decision_status(decision) == "not_applicable"
        and not decision.get("search_coverage_certificate_ids")
        and not decision.get("human_adjudication_refs")
    )
    invalid_generated_rules = sorted(
        str(rule.get("generated_rule_id") or rule.get("id") or "")
        for rule in _dict_list(generated_rule_pack.get("rules"))
        if _decision_status(decisions_by_id.get(str(rule.get("applicability_decision_id") or ""), {}))
        != "applicable"
    )
    generated_rule_edge_gaps = sorted(
        str(rule.get("generated_rule_id") or rule.get("id") or "")
        for rule in _dict_list(generated_rule_pack.get("rules"))
        if (
            "GENERATES_RULE",
            _decision_node_id(
                review_id,
                decisions_by_id.get(str(rule.get("applicability_decision_id") or ""), {}),
            ),
            _generated_rule_node_id(
                review_id,
                str(rule.get("generated_rule_id") or rule.get("id") or ""),
            ),
        )
        not in edge_tuples
    )
    compliance_finding_edge_gaps = sorted(
        str(row.get("row_id") or row.get("rule_id") or "")
        for row in _dict_list(compliance_matrix.get("rows"))
        if (
            "SUPPORTS_COMPLIANCE_FINDING",
            _generated_rule_node_id(review_id, str(row.get("rule_id") or "")),
            _compliance_finding_node_id(review_id, str(row.get("row_id") or row.get("rule_id") or "")),
        )
        not in edge_tuples
    )
    finding_evidence_edge_gaps = []
    for row in _dict_list(compliance_matrix.get("rows")):
        finding_id = str(row.get("row_id") or row.get("rule_id") or "")
        finding_node_id = _compliance_finding_node_id(review_id, finding_id)
        evidence_edge_count = sum(
            1
            for edge_type, source_node_id, target_node_id in edge_tuples
            if edge_type == "SUPPORTS_COMPLIANCE_FINDING"
            and target_node_id == finding_node_id
            and source_node_id.startswith("evidence_span:review:")
        )
        if evidence_edge_count == 0:
            finding_evidence_edge_gaps.append(finding_id)
    return [
        _check(
            "nepa_3d_review_graph_links_required_review_artifacts",
            not review_input_gaps,
            "required review artifact inputs exist and are hashed",
            review_input_gaps,
        ),
        _check(
            "nepa_3d_review_graph_inputs_are_validated",
            bool(
                applicability_validation.get("passed")
                and generated_rule_pack_validation.get("passed")
                and compliance_validation.get("passed")
            ),
            {
                "applicability_validation": True,
                "generated_rule_pack_validation": True,
                "compliance_validation": True,
            },
            {
                "applicability_validation": applicability_validation.get("passed"),
                "generated_rule_pack_validation": generated_rule_pack_validation.get("passed"),
                "compliance_validation": compliance_validation.get("passed"),
            },
        ),
        _check(
            "nepa_3d_review_graph_exports_all_candidate_authorities",
            not candidate_node_gaps,
            len(candidate_authorities),
            candidate_node_gaps,
        ),
        _check(
            "nepa_3d_review_graph_maps_each_candidate_to_one_decision",
            not decision_cardinality_gaps,
            "exactly one decision per candidate authority",
            decision_cardinality_gaps,
        ),
        _check(
            "nepa_3d_review_graph_decisions_map_to_candidates",
            not decision_mapping_gaps,
            "all decisions reference candidate_authority_id values in authority_universe_snapshot",
            decision_mapping_gaps,
        ),
        _check(
            "nepa_3d_review_graph_links_candidates_to_decisions",
            not decision_edge_gaps,
            "PRODUCES_APPLICABILITY_DECISION edge for each decision",
            decision_edge_gaps,
        ),
        _check(
            "nepa_3d_review_graph_non_applicable_decisions_have_support",
            not unsupported_non_applicable,
            "search coverage certificate or adjudication reference",
            unsupported_non_applicable,
        ),
        _check(
            "nepa_3d_review_graph_search_coverage_references_resolve",
            not coverage_reference_gaps,
            "decision search coverage certificate IDs resolve and cover the decision",
            coverage_reference_gaps,
        ),
        _check(
            "nepa_3d_review_graph_retrieval_trace_references_resolve",
            not retrieval_trace_reference_gaps,
            "decision retrieval_trace_ids resolve to applicability retrieval trace records",
            retrieval_trace_reference_gaps,
        ),
        _check(
            "nepa_3d_review_graph_graph_trace_references_resolve",
            not graph_trace_reference_gaps,
            "decision graph path IDs resolve to applicability graph trace records",
            graph_trace_reference_gaps,
        ),
        _check(
            "nepa_3d_review_graph_generated_rules_from_applicable_decisions",
            not invalid_generated_rules,
            "generated rules derive only from applicable decisions",
            invalid_generated_rules,
        ),
        _check(
            "nepa_3d_review_graph_links_generated_rules_to_decisions",
            not generated_rule_edge_gaps,
            "GENERATES_RULE edge for each generated rule",
            generated_rule_edge_gaps,
        ),
        _check(
            "nepa_3d_review_graph_links_findings_to_generated_rules",
            not compliance_finding_edge_gaps,
            "SUPPORTS_COMPLIANCE_FINDING edge from generated rule to finding",
            compliance_finding_edge_gaps,
        ),
        _check(
            "nepa_3d_review_graph_links_findings_to_evidence",
            not finding_evidence_edge_gaps,
            "SUPPORTS_COMPLIANCE_FINDING evidence edge for each compliance finding",
            finding_evidence_edge_gaps,
        ),
    ]


def _forest_plan_inventory_ownership(
    *,
    forest_components: dict[str, Any],
    forest_plan_components_path: Path,
    output_dir: Path,
    source_set_id: str,
) -> dict[str, Any]:
    expected_path = (
        output_dir
        / "derived"
        / source_set_id
        / "forest_plan_components"
        / "component_inventory.json"
    ).resolve()
    actual_path = Path(forest_plan_components_path).resolve()
    inventory_source_set_id = str(forest_components.get("source_set_id") or "")
    return {
        "passed": actual_path == expected_path and inventory_source_set_id == source_set_id,
        "expected": {
            "source_set_id": source_set_id,
            "artifact_path": str(expected_path),
        },
        "actual": {
            "source_set_id": inventory_source_set_id or None,
            "artifact_path": str(actual_path),
        },
    }


def _review_required_input_gaps(graph: dict[str, Any]) -> dict[str, str]:
    inputs_by_name = {
        str(input_record.get("name") or ""): input_record
        for input_record in _dict_list(graph.get("inputs"))
    }
    gaps = {}
    for input_name in REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES:
        input_record = inputs_by_name.get(input_name)
        if not input_record:
            gaps[input_name] = "missing_input_record"
        elif not input_record.get("exists"):
            gaps[input_name] = "missing_file"
        elif not input_record.get("sha256"):
            gaps[input_name] = "missing_hash"
    return gaps


def _search_coverage_reference_gaps(
    decisions: list[dict[str, Any]],
    *,
    certificates_by_id: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    gaps = {}
    for decision in decisions:
        decision_id = str(decision.get("decision_id") or "")
        candidate_id = str(decision.get("candidate_authority_id") or "")
        decision_gaps = []
        for certificate_id in _strings(decision.get("search_coverage_certificate_ids")):
            certificate = certificates_by_id.get(certificate_id)
            if not certificate:
                decision_gaps.append(f"{certificate_id}:missing_certificate")
                continue
            covered_decision_ids = set(_strings(certificate.get("covered_decision_ids")))
            covered_candidate_ids = set(
                _strings(certificate.get("covered_candidate_authority_ids"))
            )
            if decision_id and decision_id not in covered_decision_ids:
                decision_gaps.append(f"{certificate_id}:decision_not_covered")
            if candidate_id and candidate_id not in covered_candidate_ids:
                decision_gaps.append(f"{certificate_id}:candidate_not_covered")
            if str(certificate.get("coverage_result") or "") != "sufficient":
                decision_gaps.append(f"{certificate_id}:coverage_not_sufficient")
        if decision_gaps:
            gaps[decision_id] = sorted(decision_gaps)
    return gaps


def _trace_reference_gaps(
    decisions: list[dict[str, Any]],
    *,
    trace_field: str,
    available_ids: set[str],
) -> dict[str, list[str]]:
    gaps = {}
    for decision in decisions:
        missing = sorted(
            trace_id
            for trace_id in _strings(decision.get(trace_field))
            if trace_id not in available_ids
        )
        if missing:
            gaps[str(decision.get("decision_id") or "")] = missing
    return gaps


def _graph_trace_reference_gaps(
    decisions: list[dict[str, Any]],
    *,
    available_ids: set[str],
) -> dict[str, list[str]]:
    gaps = {}
    for decision in decisions:
        decision_graph_path_ids = set(_strings(decision.get("selected_graph_path_ids")))
        decision_graph_path_ids.update(_strings(decision.get("graph_path_ids")))
        missing = sorted(
            graph_path_id
            for graph_path_id in decision_graph_path_ids
            if graph_path_id not in available_ids
        )
        if missing:
            gaps[str(decision.get("decision_id") or "")] = missing
    return gaps


def _review_overlay_summary(
    *,
    review_id: str,
    candidate_authorities: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    generated_rules: list[dict[str, Any]],
    compliance_rows: list[dict[str, Any]],
    search_coverage: dict[str, Any],
    review_artifacts: dict[str, Any],
) -> dict[str, Any]:
    decision_status_counts = Counter(_decision_status(decision) for decision in decisions)
    artifact_counts = _review_artifact_counts(review_artifacts)
    return {
        "review_id": review_id,
        "review_candidate_authority_count": len(candidate_authorities),
        "review_candidate_authority_type_counts": dict(
            Counter(str(candidate.get("candidate_authority_type")) for candidate in candidate_authorities)
        ),
        "review_decision_count": len(decisions),
        "review_decision_status_counts": dict(decision_status_counts),
        "applicable_decision_count": decision_status_counts.get("applicable", 0),
        "non_applicable_decision_count": decision_status_counts.get("not_applicable", 0),
        "needs_adjudication_decision_count": decision_status_counts.get("needs_adjudication", 0),
        "unresolved_decision_count": decision_status_counts.get("unresolved", 0),
        "generated_rule_count": len(generated_rules),
        "compliance_finding_count": len(compliance_rows),
        "search_coverage_certificate_count": len(_dict_list(search_coverage.get("certificates"))),
        "review_blocker_count": sum(
            1 for decision in decisions if _decision_readiness_blockers(decision)
        ),
        "review_required_artifact_count": len(REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES),
        **artifact_counts,
    }


def _review_artifact_counts(review_artifacts: dict[str, Any]) -> dict[str, int]:
    package_fact_graph = _dict(review_artifacts.get("package_fact_graph"))
    search_coverage = _dict(review_artifacts.get("search_coverage_certificates"))
    return {
        "review_package_fact_node_count": len(_dict_list(package_fact_graph.get("nodes"))),
        "review_package_fact_edge_count": len(_dict_list(package_fact_graph.get("edges"))),
        "review_retrieval_trace_count": len(
            _dict_list(review_artifacts.get("applicability_retrieval_trace"))
        ),
        "review_graph_trace_count": len(
            _dict_list(review_artifacts.get("applicability_graph_trace"))
        ),
        "review_search_coverage_certificate_count": len(
            _dict_list(search_coverage.get("certificates"))
        ),
        "review_finding_graph_node_count": len(
            _dict_list(review_artifacts.get("finding_graph_nodes"))
        ),
        "review_finding_graph_edge_count": len(
            _dict_list(review_artifacts.get("finding_graph_edges"))
        ),
    }


def _review_artifact_paths(review_dir: Path | None) -> dict[str, Path]:
    if review_dir is None:
        return {}
    applicability_dir = review_dir / "applicability"
    return {
        "review_authority_universe_snapshot": applicability_dir / "authority_universe_snapshot.json",
        "review_package_fact_graph": applicability_dir / "package_fact_graph.json",
        "review_applicability_retrieval_trace": applicability_dir / "applicability_retrieval_trace.jsonl",
        "review_applicability_graph_trace": applicability_dir / "applicability_graph_trace.jsonl",
        "review_applicability_decisions": applicability_dir / "applicability_decisions.jsonl",
        "review_search_coverage_certificates": applicability_dir / "search_coverage_certificates.json",
        "review_applicability_validation": applicability_dir / "applicability_validation.json",
        "review_generated_rule_pack": applicability_dir / "generated_rule_pack.json",
        "review_generated_rule_pack_validation": applicability_dir
        / "generated_rule_pack_validation.json",
        "review_compliance_matrix": review_dir / "compliance_matrix.json",
        "review_compliance_validation": review_dir / "compliance_validation.json",
        "review_finding_graph_nodes": review_dir / "finding_graph_nodes.jsonl",
        "review_finding_graph_edges": review_dir / "finding_graph_edges.jsonl",
    }


def _load_review_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "authority_universe_snapshot": _read_json(paths["review_authority_universe_snapshot"]),
        "package_fact_graph": _read_json(paths["review_package_fact_graph"]),
        "applicability_retrieval_trace": _read_jsonl(
            paths["review_applicability_retrieval_trace"]
        ),
        "applicability_graph_trace": _read_jsonl(paths["review_applicability_graph_trace"]),
        "applicability_decisions": _read_jsonl(paths["review_applicability_decisions"]),
        "search_coverage_certificates": _read_json(
            paths["review_search_coverage_certificates"]
        ),
        "applicability_validation": _read_json(paths["review_applicability_validation"]),
        "generated_rule_pack": _read_json(paths["review_generated_rule_pack"]),
        "generated_rule_pack_validation": _read_json(
            paths["review_generated_rule_pack_validation"]
        ),
        "compliance_matrix": _read_json(paths["review_compliance_matrix"]),
        "compliance_validation": _read_json(paths["review_compliance_validation"]),
        "finding_graph_nodes": _read_jsonl(paths["review_finding_graph_nodes"]),
        "finding_graph_edges": _read_jsonl(paths["review_finding_graph_edges"]),
    }


def _input_records(paths_by_name: dict[str, Path]) -> list[dict[str, Any]]:
    records = []
    for name, path in sorted(paths_by_name.items()):
        path = Path(path)
        records.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "sha256": _sha256_or_none(path),
            }
        )
    return records


def _lens_metadata(contract: dict[str, Any]) -> list[dict[str, Any]]:
    lens_contract = _dict(contract.get("lens_metadata_contract"))
    required_lenses = _strings(lens_contract.get("required_lenses"))
    return [
        {
            "lens_id": lens_id,
            "label": lens_id.replace("_", " ").title(),
            "description": _lens_description(lens_id),
            "supported_node_types": _lens_node_types(lens_id),
            "supported_edge_types": _lens_edge_types(lens_id),
            "display_status_values": _lens_display_statuses(lens_id),
        }
        for lens_id in required_lenses
    ]


def _lens_description(lens_id: str) -> str:
    descriptions = {
        "authority_currentness": "Display active, reserved, superseded, and candidate authority source state.",
        "forest_plan": "Display Region 1 forest-plan units, plans, and component inventory.",
        "package_applicability": "Display review-specific applicability states when a review overlay is exported.",
        "evidence_path": "Display source record, artifact, chunk, evidence span, claim, and rule paths.",
        "readiness_blockers": "Display missing source, stale artifact, adjudication, and readiness blockers.",
    }
    return descriptions.get(lens_id, lens_id.replace("_", " "))


def _lens_node_types(lens_id: str) -> list[str]:
    values = {
        "authority_currentness": ["authority_family", "source_record", "readiness_blocker"],
        "forest_plan": ["forest_unit", "forest_plan", "forest_plan_component", "source_record"],
        "package_applicability": ["authority_family", "rule_template", "readiness_blocker"],
        "evidence_path": [
            "source_record",
            "artifact",
            "chunk",
            "evidence_span",
            "source_claim",
            "rule_template",
        ],
        "readiness_blockers": [
            "source_set",
            "authority_family",
            "source_record",
            "forest_unit",
            "forest_plan",
            "forest_plan_component",
            "readiness_blocker",
        ],
    }
    return values.get(lens_id, [])


def _lens_edge_types(lens_id: str) -> list[str]:
    values = {
        "authority_currentness": [
            "CONTAINS_AUTHORITY_FAMILY",
            "HAS_SOURCE_RECORD",
            "HAS_CURRENTNESS_STATUS",
            "BLOCKED_BY",
        ],
        "forest_plan": ["HAS_FOREST_PLAN", "HAS_FOREST_COMPONENT", "BELONGS_TO_FOREST_UNIT"],
        "package_applicability": [
            "PRODUCES_APPLICABILITY_DECISION",
            "APPLIES_TO_REVIEW",
            "NOT_APPLICABLE_TO_REVIEW",
            "NEEDS_ADJUDICATION",
        ],
        "evidence_path": [
            "HAS_ARTIFACT",
            "HAS_CHUNK",
            "HAS_EVIDENCE_SPAN",
            "SUPPORTS_SOURCE_CLAIM",
            "SUPPORTS_RULE_TEMPLATE",
        ],
        "readiness_blockers": ["HAS_READINESS_BLOCKER", "BLOCKED_BY"],
    }
    return values.get(lens_id, [])


def _lens_display_statuses(lens_id: str) -> list[str]:
    values = {
        "authority_currentness": ["active", "reserved", "superseded", "candidate"],
        "forest_plan": ["active", "readiness_blocked"],
        "package_applicability": [
            "applicable",
            "not_applicable",
            "unresolved",
            "adjudicated",
            "readiness_blocked",
        ],
        "evidence_path": ["active", "readiness_blocked"],
        "readiness_blockers": ["readiness_blocked"],
    }
    return values.get(lens_id, [])


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _jsonl_count(path: Path) -> int:
    with Path(path).open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _sha256_or_none(path: Path) -> str | None:
    return sha256_file(path) if Path(path).exists() else None


def _source_set_node_id(source_set_id: str) -> str:
    return f"source_set:{source_set_id}"


def _review_node_id(review_id: str) -> str:
    return f"review:{review_id}"


def _family_node_id(family_id: str) -> str:
    return f"authority_family:{family_id}"


def _source_node_id(source_record_id: str) -> str:
    return f"source_record:{source_record_id}"


def _artifact_node_id(artifact_sha256: str) -> str:
    return f"artifact:{artifact_sha256}"


def _forest_unit_node_id(forest_unit_id: str) -> str:
    return f"forest_unit:{forest_unit_id}"


def _decision_node_id(review_id: str, decision: dict[str, Any]) -> str:
    decision_id = str(decision.get("decision_id") or "")
    if decision_id:
        return f"applicability_decision:{review_id}:{decision_id}"
    return f"applicability_decision:{review_id}:{_stable_digest(decision)}"


def _generated_rule_node_id(review_id: str, generated_rule_id: str) -> str:
    return f"generated_rule:{review_id}:{generated_rule_id}"


def _compliance_finding_node_id(review_id: str, finding_id: str) -> str:
    return f"compliance_finding:{review_id}:{finding_id}"


def _review_blocker_node_id(review_id: str, blocker_type: str, decision: dict[str, Any]) -> str:
    return f"readiness_blocker:{review_id}:{blocker_type}:{_stable_digest(decision)}"


def _review_evidence_node_id(
    review_id: str,
    finding_id: str,
    evidence_kind: str,
    evidence: dict[str, Any],
) -> str:
    return f"evidence_span:review:{review_id}:{finding_id}:{evidence_kind}:{_stable_digest(evidence)}"


def _candidate_authority_node_id(
    candidate: dict[str, Any],
    *,
    base_rule_node_ids: dict[str, str],
    template_node_ids: dict[str, str],
) -> str:
    candidate_type = str(candidate.get("candidate_authority_type") or "")
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    if candidate_type == "forest_plan_component":
        forest_plan = _dict(candidate.get("forest_plan"))
        component_id = str(forest_plan.get("component_id") or candidate_id.rsplit(":", 1)[-1])
        return f"forest_plan_component:{component_id}"
    rule_id = _candidate_rule_id(candidate)
    return (
        base_rule_node_ids.get(rule_id)
        or template_node_ids.get(rule_id)
        or f"{BASE_RULE_NODE_PREFIX}:{rule_id}"
    )


def _candidate_rule_id(candidate: dict[str, Any]) -> str:
    return str(
        _dict(candidate.get("rule_template")).get("rule_id")
        or _dict(candidate.get("deterministic_applicability_test_contract")).get("rule_id")
        or candidate.get("rule_id")
        or str(candidate.get("candidate_authority_id") or "").rsplit(":", 1)[-1]
    )


def _family_ids_by_rule_id(inventory: dict[str, Any]) -> dict[str, set[str]]:
    by_rule: dict[str, set[str]] = {}
    for family in inventory.get("authority_families", []):
        family_id = str(family.get("family_id") or "")
        for rule_id in _strings(family.get("rule_ids")):
            by_rule.setdefault(rule_id, set()).add(family_id)
    return by_rule


def _authority_family_id_for_decision(
    *,
    decision: dict[str, Any],
    candidate: dict[str, Any],
    family_ids_by_rule_id: dict[str, set[str]],
) -> str:
    explicit = (
        decision.get("authority_family_id")
        or _dict(decision.get("rule_template")).get("authority_family_id")
        or candidate.get("authority_family_id")
    )
    if explicit:
        return str(explicit)
    if str(decision.get("candidate_authority_type") or "") == "forest_plan_component":
        return "nfma_forest_planning_project_consistency"
    rule_id = _candidate_rule_id(decision or candidate)
    return _first_sorted(family_ids_by_rule_id.get(rule_id, set())) or "unknown_authority_family"


def _decision_status(decision: dict[str, Any]) -> str:
    return str(decision.get("status") or decision.get("applicability_status") or "")


def _decision_display_status(decision: dict[str, Any]) -> str:
    if decision.get("human_adjudication_refs"):
        return "adjudicated"
    status = _decision_status(decision)
    if status in {"applicable", "not_applicable", "unresolved"}:
        return status
    if status == "needs_adjudication":
        return "unresolved"
    return "readiness_blocked"


def _decision_review_readiness(decision: dict[str, Any]) -> str:
    status = _decision_status(decision)
    if status in {"applicable", "not_applicable"}:
        return "reviewer_ready"
    if status == "needs_adjudication":
        return "needs_adjudication"
    return "blocked"


def _decision_readiness_blockers(decision: dict[str, Any]) -> list[str]:
    status = _decision_status(decision)
    return ["adjudication_needed"] if status in {"needs_adjudication", "unresolved"} else []


def _review_validation_ready(
    applicability_validation: dict[str, Any],
    generated_rule_pack_validation: dict[str, Any],
) -> bool:
    return bool(
        applicability_validation.get("passed")
        and generated_rule_pack_validation.get("passed")
        and (
            applicability_validation.get("reviewer_ready") is not False
            and applicability_validation.get("generated_rule_pack_ready") is not False
        )
    )


def _first_sorted(values: set[str] | list[str] | tuple[str, ...] | None) -> str | None:
    if not values:
        return None
    return sorted(str(value) for value in values if str(value))[0]


def _stable_digest(*parts: object) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "", [], {})}


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _first(value: object) -> object | None:
    if isinstance(value, list) and value:
        return value[0]
    return None


def _check(name: str, passed: bool, expected: object, actual: object) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }


def _annotate_graph_validation_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **check,
            "failure_category": _graph_failure_category_for_check(str(check.get("name") or "")),
        }
        for check in checks
    ]


def _graph_failure_category_for_check(name: str) -> str:
    if name in GRAPH_FAILURE_CATEGORY_BY_CHECK_NAME:
        return GRAPH_FAILURE_CATEGORY_BY_CHECK_NAME[name]
    lowered = name.lower()
    if "dangling" in lowered or "edges_reference_existing_nodes" in lowered:
        return "graph_dangling_edge"
    if "source_partition" in lowered or "partition" in lowered:
        return "graph_missing_source_partition"
    if "currentness" in lowered:
        return "graph_missing_currentness_status"
    if "candidate_authorit" in lowered:
        return "graph_missing_candidate_authority"
    if "authority_famil" in lowered:
        return "graph_missing_authority_family"
    if "source_record" in lowered or "catalog_source" in lowered:
        return "graph_missing_source_record"
    if "applicability" in lowered or "decision" in lowered:
        return "graph_missing_applicability_decision"
    if "superseded" in lowered or "reserved" in lowered:
        return "graph_superseded_as_current"
    if "noncurrent" in lowered or "non_current" in lowered:
        return "graph_noncurrent_document_in_main_corpus"
    if "fsh" in lowered or "handbook" in lowered or "chapter" in lowered:
        return "graph_handbook_chapter_collapsed"
    if "region1" in lowered or "forest" in lowered:
        return "graph_region1_profile_gap"
    return DEFAULT_GRAPH_FAILURE_CATEGORY


def _validation_failure_category_counts(checks: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter(
        str(check.get("failure_category") or DEFAULT_GRAPH_FAILURE_CATEGORY)
        for check in checks
        if not check.get("passed")
    )
    return dict(sorted(counts.items()))
