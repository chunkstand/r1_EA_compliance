from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any

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

SOURCE_SET_EXPORT_SCHEMA_VERSION = NEPA_3D_GRAPH_SCHEMA_VERSION
BASE_RULE_NODE_PREFIX = "rule_template:base"
AUTHORITY_TEMPLATE_NODE_PREFIX = "rule_template:authority_family"


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
            "provenance": _compact_dict(provenance),
            "readiness_blockers": sorted(set(readiness_blockers or [])),
        }
        if metadata:
            record["metadata"] = _compact_dict(metadata)
        self.edges[edge_id] = record
        return edge_id

    def sorted_nodes(self) -> list[dict[str, Any]]:
        return [self.nodes[node_id] for node_id in sorted(self.nodes)]

    def sorted_edges(self) -> list[dict[str, Any]]:
        return [self.edges[edge_id] for edge_id in sorted(self.edges)]


def build_nepa_knowledge_graph_export(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    graph_contract_path: Path = DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    authority_family_rule_templates_path: Path = DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
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
    graph_dir = derived_dir / "knowledge_graph"
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

    contract = load_nepa_3d_graph_contract(graph_contract_path)
    inventory = _read_json(authority_inventory_path)
    template_config = _read_json(authority_family_rule_templates_path)
    forest_plan_profiles = _read_json(forest_plan_profiles_path)
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
            "evidence_graph_nodes": evidence_graph_nodes_path,
            "evidence_graph_edges": evidence_graph_edges_path,
            "claims": claims_path,
            "rule_claim_links": rule_claim_links_path,
            "forest_plan_components": forest_plan_components_path,
            "graph_contract": graph_contract_path,
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
    _add_authority_family_templates(
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
        forest_components=forest_components,
    )
    _add_source_set_blockers(builder, source_set_node_id=source_set_node_id, source_set_id=source_set_id)

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
        currentness=currentness,
        inputs=inputs,
        catalog_graph_node_count=catalog_graph_node_count,
        catalog_graph_edge_count=catalog_graph_edge_count,
    )
    graph = {
        "schema_version": SOURCE_SET_EXPORT_SCHEMA_VERSION,
        "graph_id": f"nepa-3d-source-set:{source_set_id}",
        "created_at": str(manifest.get("created_at") or currentness.get("created_at") or ""),
        "export_scope": {"scope_type": "source_set", "source_set_id": source_set_id},
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
        inputs=inputs,
        catalog_graph_node_count=catalog_graph_node_count,
        catalog_graph_edge_count=catalog_graph_edge_count,
    )
    validation = {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
    graph["validation"] = validation
    summary["validation_passed"] = validation["passed"]
    summary["validation_check_count"] = len(checks)
    summary["failed_validation_check_count"] = sum(1 for check in checks if not check["passed"])
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
    forest_components: dict[str, Any],
) -> None:
    plan_node_by_unit: dict[str, str] = {}
    for profile in sorted(
        forest_plan_profiles.get("profiles", []),
        key=lambda item: str(item.get("forest_unit_id") or ""),
    ):
        forest_unit_id = str(profile.get("forest_unit_id") or "")
        if not forest_unit_id:
            continue
        unit_node_id = _forest_unit_node_id(forest_unit_id)
        builder.add_node(
            node_id=unit_node_id,
            node_type="forest_unit",
            label=str(_first(profile.get("forest_unit_names")) or forest_unit_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={"source_set_id": source_set_id, "forest_code": forest_unit_id},
            metadata={
                "forest_unit_names": profile.get("forest_unit_names", []),
                "required_readiness_source_roles": profile.get("required_readiness_source_roles", []),
            },
        )
        plan_source_record_id = str(profile.get("active_plan_source_record_id") or "")
        if plan_source_record_id:
            plan_node_id = f"forest_plan:{forest_unit_id}:{plan_source_record_id}"
            plan_node_by_unit[forest_unit_id] = plan_node_id
            builder.add_node(
                node_id=plan_node_id,
                node_type="forest_plan",
                label=f"{forest_unit_id} active forest plan",
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                metadata={
                    "supporting_source_record_ids_by_role": profile.get(
                        "supporting_source_record_ids_by_role", {}
                    )
                },
            )
            builder.add_edge(
                edge_type="HAS_FOREST_PLAN",
                source_node_id=unit_node_id,
                target_node_id=plan_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
            )
            builder.add_edge(
                edge_type="HAS_SOURCE_RECORD",
                source_node_id=plan_node_id,
                target_node_id=_source_node_id(plan_source_record_id),
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                    "source_role": "active_plan",
                },
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
                        display_status="active",
                        review_readiness_status="not_review_specific",
                        provenance={
                            "source_set_id": source_set_id,
                            "forest_code": forest_unit_id,
                            "source_record_id": supporting_source_record_id,
                            "source_role": role,
                        },
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
        "forest_plan_component_count": len(forest_components.get("components", [])),
        "currentness_validation_passed": currentness.get("validation", {}).get("passed")
        if isinstance(currentness.get("validation"), dict)
        else currentness.get("summary", {}).get("validation_passed"),
        "input_count": len(inputs),
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
    inputs: list[dict[str, Any]],
    catalog_graph_node_count: int,
    catalog_graph_edge_count: int,
) -> list[dict[str, Any]]:
    node_ids = {node["node_id"] for node in graph["nodes"]}
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
            "nepa_3d_graph_has_readiness_blocker_nodes",
            any(node_id.startswith("readiness_blocker:") for node_id in node_ids),
            "readiness blocker nodes present",
            sorted(node_id for node_id in node_ids if node_id.startswith("readiness_blocker:")),
        ),
    ]


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
        "readiness_blockers": ["source_set", "authority_family", "source_record", "readiness_blocker"],
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


def _family_node_id(family_id: str) -> str:
    return f"authority_family:{family_id}"


def _source_node_id(source_record_id: str) -> str:
    return f"source_record:{source_record_id}"


def _artifact_node_id(artifact_sha256: str) -> str:
    return f"artifact:{artifact_sha256}"


def _forest_unit_node_id(forest_unit_id: str) -> str:
    return f"forest_unit:{forest_unit_id}"


def _stable_digest(*parts: object) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "", [], {})}


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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
