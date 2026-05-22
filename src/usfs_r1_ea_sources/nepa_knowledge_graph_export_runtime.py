from __future__ import annotations

from pathlib import Path

from .nepa_3d_graph_contract import annotate_nepa_3d_graph_validation_checks
from .nepa_3d_graph_contract import build_nepa_3d_lens_metadata
from .nepa_3d_graph_contract import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH
from .nepa_3d_graph_contract import load_nepa_3d_graph_contract
from .nepa_3d_graph_contract import nepa_3d_graph_failure_category_counts
from .nepa_3d_graph_contract import validate_nepa_3d_graph
from .nepa_knowledge_graph_export_common import _is_source_register_v1_catalog
from .nepa_knowledge_graph_export_common import _source_currentness_by_id
from .nepa_knowledge_graph_export_common import _source_register_proving_context_for_source_set
from .nepa_knowledge_graph_export_common import _source_set_readiness_blockers
from .nepa_knowledge_graph_export_common import _summary
from .nepa_knowledge_graph_export_forest_plan import _add_forest_plan_nodes
from .nepa_knowledge_graph_export_forest_plan import _add_source_register_region1_semantic_paths
from .nepa_knowledge_graph_export_forest_plan import _add_source_set_blockers
from .nepa_knowledge_graph_export_models import DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH
from .nepa_knowledge_graph_export_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .nepa_knowledge_graph_export_models import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .nepa_knowledge_graph_export_models import DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH
from .nepa_knowledge_graph_export_models import NepaKnowledgeGraphExportResult
from .nepa_knowledge_graph_export_models import SOURCE_SET_EXPORT_SCHEMA_VERSION
from .nepa_knowledge_graph_export_models import _GraphBuilder
from .nepa_knowledge_graph_export_models import _input_records
from .nepa_knowledge_graph_export_models import _jsonl_count
from .nepa_knowledge_graph_export_models import _jsonl_count_if_exists
from .nepa_knowledge_graph_export_models import _read_json
from .nepa_knowledge_graph_export_models import _read_jsonl
from .nepa_knowledge_graph_export_models import _sha256_or_none
from .nepa_knowledge_graph_export_models import _source_set_node_id
from .nepa_knowledge_graph_export_models import _write_json
from .nepa_knowledge_graph_export_models import _write_jsonl
from .nepa_knowledge_graph_export_region1 import _load_region1_forest_plan_readiness
from .nepa_knowledge_graph_export_review_overlay import _add_review_overlay
from .nepa_knowledge_graph_export_review_validation import _review_overlay_validation_checks
from .nepa_knowledge_graph_export_rule_templates import _add_authority_family_templates
from .nepa_knowledge_graph_export_rule_templates import _add_base_rules
from .nepa_knowledge_graph_export_rule_templates import _add_rule_claim_paths
from .nepa_knowledge_graph_export_source_register import _add_authority_families
from .nepa_knowledge_graph_export_source_register import _add_lens_nodes
from .nepa_knowledge_graph_export_source_register import _add_source_records_and_artifacts
from .nepa_knowledge_graph_export_source_register import _add_source_register_semantics
from .nepa_knowledge_graph_export_source_set_validation import _milestone_validation_checks
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack
from .source_register import DEFAULT_JURISDICTION_SCOPE_REGISTER_PATH
from .source_register import load_jurisdiction_scope_register


from .nepa_knowledge_graph_export_models import _empty_forest_plan_profiles
from .nepa_knowledge_graph_export_models import _empty_region1_forest_plan_readiness
from .nepa_knowledge_graph_export_models import _empty_rule_pack
from .nepa_knowledge_graph_export_models import _empty_template_config
from .nepa_knowledge_graph_export_review_validation import _load_review_artifacts
from .nepa_knowledge_graph_export_review_validation import _review_artifact_paths


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
    catalog_rows = [
        row
        for row in _read_jsonl(catalog_path)
        if str(row.get("source_set_id") or source_set_id) == source_set_id
    ]
    is_source_register_v1 = _is_source_register_v1_catalog(catalog_rows)
    proving_context = (
        _source_register_proving_context_for_source_set(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )
        if is_source_register_v1
        else None
    )
    if is_source_register_v1 and authority_inventory_path == DEFAULT_AUTHORITY_INVENTORY_PATH:
        if proving_context is None:
            raise FileNotFoundError(
                "Canonical source-register graph export requires a proving context with "
                "authority inventory for the active source set."
            )
        authority_inventory_path = Path(proving_context["authority_inventory_path"])

    contract = load_nepa_3d_graph_contract(graph_contract_path)
    inventory = _read_json(authority_inventory_path)
    currentness = _read_json(authority_currentness_path)
    jurisdiction_scope_register = load_jurisdiction_scope_register(
        DEFAULT_JURISDICTION_SCOPE_REGISTER_PATH
    )

    if is_source_register_v1:
        rule_pack = _empty_rule_pack()
        template_config = _empty_template_config()
        forest_plan_profiles = (
            _read_json(forest_plan_profiles_path)
            if forest_plan_profiles_path.exists()
            else _empty_forest_plan_profiles()
        )
        region1_forest_plan_readiness = (
            _load_region1_forest_plan_readiness(region1_forest_plan_readiness_path)
            if region1_forest_plan_readiness_path.exists()
            else _empty_region1_forest_plan_readiness(source_set_id=source_set_id)
        )
        claims = _read_jsonl(claims_path) if claims_path.exists() else []
        rule_claim_links_path = rule_claim_links_path or (
            derived_dir / "rule_claim_links" / "canonical_semantic_graph" / "0.0.0" / "rule_claim_links.jsonl"
        )
        rule_claim_links = _read_jsonl(rule_claim_links_path) if rule_claim_links_path.exists() else []
        forest_plan_components_path = (
            forest_plan_components_path
            or derived_dir / "forest_plan_components" / "component_inventory.json"
        )
        forest_components = (
            _read_json(forest_plan_components_path)
            if forest_plan_components_path.exists()
            else {"schema_version": "forest-plan-component-inventory-v0", "source_set_id": source_set_id, "components": []}
        )
    else:
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
        template_config = _read_json(authority_family_rule_templates_path)
        forest_plan_profiles = _read_json(forest_plan_profiles_path)
        region1_forest_plan_readiness = _load_region1_forest_plan_readiness(
            region1_forest_plan_readiness_path
        )
        claims = _read_jsonl(claims_path)
        rule_claim_links = _read_jsonl(rule_claim_links_path)
        forest_components = _read_json(forest_plan_components_path)

    review_artifact_paths = _review_artifact_paths(review_dir) if review_dir else {}
    evidence_graph_node_count = _jsonl_count_if_exists(evidence_graph_nodes_path)
    evidence_graph_edge_count = _jsonl_count_if_exists(evidence_graph_edges_path)
    catalog_graph_node_count = _jsonl_count(catalog_graph_nodes_path)
    catalog_graph_edge_count = _jsonl_count(catalog_graph_edges_path)
    review_artifacts = (
        _load_review_artifacts(review_artifact_paths) if review_artifact_paths else {}
    )

    canonical_evidence_graph_inputs: dict[str, Path] = {}
    if not is_source_register_v1:
        canonical_evidence_graph_inputs = {
            "evidence_graph_nodes": evidence_graph_nodes_path,
            "evidence_graph_edges": evidence_graph_edges_path,
        }
    elif evidence_graph_nodes_path.exists() or evidence_graph_edges_path.exists():
        canonical_evidence_graph_inputs = {
            "evidence_graph_nodes": evidence_graph_nodes_path,
            "evidence_graph_edges": evidence_graph_edges_path,
        }

    builder = _GraphBuilder()
    inputs = _input_records(
        {
            "source_set_manifest": source_set_manifest_path,
            "source_catalog": catalog_path,
            "catalog_graph_nodes": catalog_graph_nodes_path,
            "catalog_graph_edges": catalog_graph_edges_path,
            "authority_inventory": authority_inventory_path,
            "authority_currentness": authority_currentness_path,
            **canonical_evidence_graph_inputs,
            "graph_contract": graph_contract_path,
            **(
                {
                    "forest_plan_profiles": forest_plan_profiles_path,
                    "region1_forest_plan_readiness": region1_forest_plan_readiness_path,
                    "forest_plan_components": forest_plan_components_path,
                }
                if is_source_register_v1
                else {
                    "rule_pack": rule_pack_path,
                    "authority_family_rule_templates": authority_family_rule_templates_path,
                    "forest_plan_profiles": forest_plan_profiles_path,
                    "region1_forest_plan_readiness": region1_forest_plan_readiness_path,
                    "claims": claims_path,
                    "rule_claim_links": rule_claim_links_path,
                    "forest_plan_components": forest_plan_components_path,
                }
            ),
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
    if is_source_register_v1:
        _add_source_register_semantics(
            builder,
            source_set_id=source_set_id,
            catalog_rows=catalog_rows,
            source_currentness_by_id=source_currentness_by_id,
            catalog_partition_by_id=catalog_partition_by_id,
            jurisdiction_scope_register=jurisdiction_scope_register,
            proving_context=proving_context,
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
    if is_source_register_v1:
        _add_source_register_region1_semantic_paths(
            builder,
            source_set_id=source_set_id,
            region1_forest_plan_readiness=region1_forest_plan_readiness,
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
        "lens_metadata": build_nepa_3d_lens_metadata(contract),
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
        is_source_register_v1=is_source_register_v1,
    )
    if review_id:
        checks.extend(
            _review_overlay_validation_checks(
                graph=graph,
                review_id=review_id,
                review_artifacts=review_artifacts,
            )
        )
    checks = annotate_nepa_3d_graph_validation_checks(checks)
    validation = {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "failure_category_counts": nepa_3d_graph_failure_category_counts(checks),
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
