from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from .cli_common import print_summary
from .cli_derived_dispatch import DerivedCommandHandler, dispatch_derived_command
from .cli_derived_registration import (
    DerivedCommandDefaults,
    build_derived_command_specs,
    register_derived_command_specs,
)


DEFAULT_OUTPUT_DIR = Path("source_library")


def _module_attr(module_name: str, attr_name: str):
    module = importlib.import_module(f".{module_name}", __package__)
    return getattr(module, attr_name)


DEFAULT_AUTHORITY_ONTOLOGY_EVAL_PATH = _module_attr(
    "authority_ontology_validate",
    "DEFAULT_AUTHORITY_ONTOLOGY_EVAL_PATH",
)
DEFAULT_AUTHORITY_ONTOLOGY_PATH = _module_attr(
    "authority_ontology_validate",
    "DEFAULT_AUTHORITY_ONTOLOGY_PATH",
)
DEFAULT_AUTHORITY_RELATIONSHIP_EVAL_PATH = _module_attr(
    "authority_relationship_eval",
    "DEFAULT_AUTHORITY_RELATIONSHIP_EVAL_PATH",
)
DEFAULT_AUTHORITY_INVENTORY_PATH = _module_attr(
    "authority_currentness",
    "DEFAULT_AUTHORITY_INVENTORY_PATH",
)
DEFAULT_SOURCE_ADDITION_DECISIONS_PATH = _module_attr(
    "authority_currentness",
    "DEFAULT_SOURCE_ADDITION_DECISIONS_PATH",
)
DEFAULT_CLAIM_EVAL_PATH = _module_attr("claim_extraction", "DEFAULT_CLAIM_EVAL_PATH")
DEFAULT_VERIFIED_EXTRACTION_ADMISSION_CONTRACT_PATH = _module_attr(
    "extraction_admission",
    "DEFAULT_VERIFIED_EXTRACTION_ADMISSION_CONTRACT_PATH",
)
DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH = _module_attr(
    "forest_plan_source_delta_readiness",
    "DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH",
)
DEFAULT_R1_FOREST_PLAN_REGISTER_PATH = _module_attr(
    "forest_plan_source_delta_readiness",
    "DEFAULT_R1_FOREST_PLAN_REGISTER_PATH",
)
DEFAULT_SOURCE_DELTA_BATCH_RUN_ID = _module_attr(
    "forest_plan_source_delta_readiness",
    "DEFAULT_SOURCE_DELTA_BATCH_RUN_ID",
)
DEFAULT_GRAPH_ACCURACY_EVAL_PATH = _module_attr(
    "graph_accuracy_eval",
    "DEFAULT_GRAPH_ACCURACY_EVAL_PATH",
)
DEFAULT_GRAPH_HEALTH_CONTRACT_PATH = _module_attr(
    "graph_health_eval",
    "DEFAULT_GRAPH_HEALTH_CONTRACT_PATH",
)
DEFAULT_INCREMENTAL_GRAPH_REFRESH_EVAL_PATH = _module_attr(
    "incremental_graph_refresh_eval",
    "DEFAULT_INCREMENTAL_GRAPH_REFRESH_EVAL_PATH",
)
DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH = _module_attr(
    "nepa_3d_graph_contract",
    "DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH",
)
DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH = _module_attr(
    "nepa_knowledge_graph_export",
    "DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH",
)
DEFAULT_FOREST_PLAN_PROFILES_PATH = _module_attr(
    "nepa_knowledge_graph_export",
    "DEFAULT_FOREST_PLAN_PROFILES_PATH",
)
DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH = _module_attr(
    "nepa_knowledge_graph_export",
    "DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH",
)
DEFAULT_RULE_CLAIM_EVAL_PATH = _module_attr(
    "rule_claim_binding",
    "DEFAULT_RULE_CLAIM_EVAL_PATH",
)
DEFAULT_CHUNK_SIDECAR_RETRIEVAL_EVAL_PATH = _module_attr(
    "sidecar_retrieval_eval",
    "DEFAULT_CHUNK_SIDECAR_RETRIEVAL_EVAL_PATH",
)
DEFAULT_RULE_PACK_PATH = _module_attr("rule_packs", "DEFAULT_RULE_PACK_PATH")
DEFAULT_SEMANTIC_GRAPH_EVAL_PATH = _module_attr(
    "semantic_graph_eval",
    "DEFAULT_SEMANTIC_GRAPH_EVAL_PATH",
)
DEFAULT_KNOWLEDGE_GRAPH_QUERY_EVAL_PATH = _module_attr(
    "knowledge_graph_query_eval",
    "DEFAULT_QUERY_EVAL_PATH",
)
DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH = _module_attr(
    "source_register_proving",
    "DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH",
)
DEFAULT_SOURCE_PARTITION_CONTRACT_PATH = _module_attr(
    "source_partitions",
    "DEFAULT_SOURCE_PARTITION_CONTRACT_PATH",
)


def run_authority_ontology_validate(**kwargs):
    return _module_attr(
        "authority_ontology_validate",
        "run_authority_ontology_validate",
    )(**kwargs)


def run_authority_relationship_eval(**kwargs):
    return _module_attr(
        "authority_relationship_eval",
        "run_authority_relationship_eval",
    )(**kwargs)


def build_authority_currentness_report(**kwargs):
    return _module_attr(
        "authority_currentness",
        "build_authority_currentness_report",
    )(**kwargs)


def run_citation_alias_eval(**kwargs):
    return _module_attr("citation_alias_eval", "run_citation_alias_eval")(**kwargs)


def build_claim_extraction(**kwargs):
    return _module_attr("claim_extraction", "build_claim_extraction")(**kwargs)


def default_claims_path(*args, **kwargs):
    return _module_attr("claim_extraction", "default_claims_path")(*args, **kwargs)


def run_claim_eval(**kwargs):
    return _module_attr("claim_extraction", "run_claim_eval")(**kwargs)


def build_evidence_graph(**kwargs):
    return _module_attr("evidence_graph", "build_evidence_graph")(**kwargs)


def build_extraction(**kwargs):
    return _module_attr("extract", "build_extraction")(**kwargs)


def run_extraction_accuracy_audit(**kwargs):
    return _module_attr(
        "extraction_accuracy",
        "run_extraction_accuracy_audit",
    )(**kwargs)


def run_chunk_quality_audit(**kwargs):
    return _module_attr("chunk_quality_audit", "run_chunk_quality_audit")(**kwargs)


def build_chunk_layers(**kwargs):
    return _module_attr("chunk_layers", "build_chunk_layers")(**kwargs)


def build_forest_plan_source_delta_readiness_report(**kwargs):
    return _module_attr(
        "forest_plan_source_delta_readiness",
        "build_forest_plan_source_delta_readiness_report",
    )(**kwargs)


def run_graph_accuracy_eval(**kwargs):
    return _module_attr("graph_accuracy_eval", "run_graph_accuracy_eval")(**kwargs)


def run_graph_health_eval(**kwargs):
    return _module_attr("graph_health_eval", "run_graph_health_eval")(**kwargs)


def run_incremental_graph_refresh_eval(**kwargs):
    return _module_attr(
        "incremental_graph_refresh_eval",
        "run_incremental_graph_refresh_eval",
    )(**kwargs)


def build_nepa_knowledge_graph_export(**kwargs):
    return _module_attr(
        "nepa_knowledge_graph_export",
        "build_nepa_knowledge_graph_export",
    )(**kwargs)


def build_retrieval_index(**kwargs):
    return _module_attr("retrieval", "build_retrieval_index")(**kwargs)


def default_index_path(*args, **kwargs):
    return _module_attr("retrieval", "default_index_path")(*args, **kwargs)


def query_retrieval_index(**kwargs):
    return _module_attr("retrieval", "query_retrieval_index")(**kwargs)


def run_retrieval_eval(**kwargs):
    return _module_attr("retrieval", "run_retrieval_eval")(**kwargs)


def run_chunk_sidecar_retrieval_eval(**kwargs):
    return _module_attr(
        "sidecar_retrieval_eval",
        "run_chunk_sidecar_retrieval_eval",
    )(**kwargs)


def build_reuse_inventory(**kwargs):
    return _module_attr("reuse_inventory", "build_reuse_inventory")(**kwargs)


def build_rule_claim_links(**kwargs):
    return _module_attr("rule_claim_binding", "build_rule_claim_links")(**kwargs)


def default_rule_claim_links_path(*args, **kwargs):
    return _module_attr(
        "rule_claim_binding",
        "default_rule_claim_links_path",
    )(*args, **kwargs)


def run_rule_claim_link_eval(**kwargs):
    return _module_attr("rule_claim_binding", "run_rule_claim_link_eval")(**kwargs)


def run_semantic_graph_eval(**kwargs):
    return _module_attr("semantic_graph_eval", "run_semantic_graph_eval")(**kwargs)


def run_knowledge_graph_query(**kwargs):
    return _module_attr("knowledge_graph_query", "run_knowledge_graph_query")(**kwargs)


def run_knowledge_graph_query_eval(**kwargs):
    return _module_attr("knowledge_graph_query_eval", "run_knowledge_graph_query_eval")(**kwargs)


def build_source_register_proving_slice(**kwargs):
    return _module_attr(
        "source_register_proving",
        "build_source_register_proving_slice",
    )(**kwargs)


def resolve_authority_currentness_inputs(**kwargs):
    return _module_attr(
        "source_register_proving",
        "resolve_authority_currentness_inputs",
    )(**kwargs)


DERIVED_COMMANDS = {
    "extract-build",
    "reuse-inventory",
    "forest-plan-source-delta-readiness",
    "extraction-accuracy-audit",
    "chunk-quality-audit",
    "chunk-layer-build",
    "chunk-sidecar-retrieval-eval",
    "chunk-sidecar-consumer-eval",
    "source-register-proving-slice",
    "authority-currentness",
    "authority-ontology-validate",
    "authority-relationship-eval",
    "citation-alias-eval",
    "graph-health-eval",
    "graph-accuracy-eval",
    "semantic-graph-eval",
    "incremental-graph-refresh-eval",
    "retrieval-build",
    "retrieval-query",
    "retrieval-eval",
    "evidence-graph-build",
    "nepa-knowledge-graph-export",
    "knowledge-graph-query",
    "knowledge-graph-query-eval",
    "claim-extract",
    "claim-eval",
    "rule-claim-link",
    "rule-claim-eval",
}

COMMAND_SPECS = build_derived_command_specs(
    DerivedCommandDefaults(
        output_dir=DEFAULT_OUTPUT_DIR,
        authority_ontology_eval_path=DEFAULT_AUTHORITY_ONTOLOGY_EVAL_PATH,
        authority_ontology_path=DEFAULT_AUTHORITY_ONTOLOGY_PATH,
        authority_relationship_eval_path=DEFAULT_AUTHORITY_RELATIONSHIP_EVAL_PATH,
        authority_inventory_path=DEFAULT_AUTHORITY_INVENTORY_PATH,
        source_addition_decisions_path=DEFAULT_SOURCE_ADDITION_DECISIONS_PATH,
        claim_eval_path=DEFAULT_CLAIM_EVAL_PATH,
        verified_extraction_admission_contract_path=(
            DEFAULT_VERIFIED_EXTRACTION_ADMISSION_CONTRACT_PATH
        ),
        official_source_gap_evidence_path=DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH,
        r1_forest_plan_register_path=DEFAULT_R1_FOREST_PLAN_REGISTER_PATH,
        source_delta_batch_run_id=DEFAULT_SOURCE_DELTA_BATCH_RUN_ID,
        graph_accuracy_eval_path=DEFAULT_GRAPH_ACCURACY_EVAL_PATH,
        graph_health_contract_path=DEFAULT_GRAPH_HEALTH_CONTRACT_PATH,
        incremental_graph_refresh_eval_path=DEFAULT_INCREMENTAL_GRAPH_REFRESH_EVAL_PATH,
        nepa_3d_graph_contract_path=DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH,
        authority_family_rule_templates_path=DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH,
        forest_plan_profiles_path=DEFAULT_FOREST_PLAN_PROFILES_PATH,
        region1_forest_plan_readiness_path=DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH,
        rule_claim_eval_path=DEFAULT_RULE_CLAIM_EVAL_PATH,
        chunk_sidecar_retrieval_eval_path=DEFAULT_CHUNK_SIDECAR_RETRIEVAL_EVAL_PATH,
        rule_pack_path=DEFAULT_RULE_PACK_PATH,
        semantic_graph_eval_path=DEFAULT_SEMANTIC_GRAPH_EVAL_PATH,
        knowledge_graph_query_eval_path=DEFAULT_KNOWLEDGE_GRAPH_QUERY_EVAL_PATH,
        source_register_proving_slice_manifest_path=(
            DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH
        ),
        source_partition_contract_path=DEFAULT_SOURCE_PARTITION_CONTRACT_PATH,
    )
)


def register_derived_commands(subparsers: argparse._SubParsersAction) -> None:
    register_derived_command_specs(subparsers, COMMAND_SPECS)


def _result_summary(result: object) -> dict:
    return result.summary


def _identity_summary(result: object) -> dict:
    return result


def _summary_key_truthy(key: str):
    def _success(summary: dict) -> bool:
        return bool(summary[key])

    return _success


def _always_true(_summary: dict) -> bool:
    return True


def _result_handler(run, success_key: str) -> DerivedCommandHandler:
    return DerivedCommandHandler(
        run=run,
        summary_getter=_result_summary,
        success=_summary_key_truthy(success_key),
    )


def _summary_handler(run, success_key: str) -> DerivedCommandHandler:
    return DerivedCommandHandler(
        run=run,
        summary_getter=_identity_summary,
        success=_summary_key_truthy(success_key),
    )


def _run_extract_build(args: argparse.Namespace):
    return build_extraction(
        output_dir=args.output_dir,
        catalog_dir=args.catalog_dir,
        id_filters=set(args.ids or []),
        parser_filter=args.parser,
        limit=args.limit,
        chunk_max_chars=args.chunk_max_chars,
        chunk_overlap_chars=args.chunk_overlap_chars,
        prefer_docling=args.prefer_docling,
        docling_ocr=args.docling_ocr,
        docling_timeout_seconds=args.docling_timeout_seconds,
        allow_invalid_catalog=args.allow_invalid_catalog,
        reuse_existing=args.reuse_existing,
        reuse_inventory_path=args.reuse_inventory_path,
        merge_selected_into_existing=args.merge_selected_into_existing,
    )


def _run_reuse_inventory(args: argparse.Namespace):
    return build_reuse_inventory(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        previous_source_set_ids=args.previous_source_set_ids,
        catalog_dir=args.catalog_dir,
        catalog_path=args.catalog_path,
        verify_artifact_hashes=not args.skip_artifact_hash_check,
    )


def _run_forest_plan_source_delta_readiness(args: argparse.Namespace):
    return build_forest_plan_source_delta_readiness_report(
        output_dir=args.output_dir,
        register_path=args.r1_forest_plan_register,
        source_delta_batch_run_id=args.source_delta_batch_run_id,
        scoped_catalog_gate_dir=args.scoped_catalog_gate_dir,
        merged_catalog_gate_dir=args.merged_catalog_gate_dir,
        canonical_catalog_dir=args.canonical_catalog_dir,
        extraction_source_set_id=args.extraction_source_set_id,
        reuse_inventory_path=args.reuse_inventory_path,
        forest_plan_profiles_path=args.forest_plan_profiles,
        official_source_gap_evidence_path=args.official_source_gap_evidence,
        results_dir=args.results_dir,
    )


def _run_extraction_accuracy_audit(args: argparse.Namespace):
    return run_extraction_accuracy_audit(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        output_path=args.output_path,
        contract_path=args.contract_path,
    )


def _run_chunk_quality_audit(args: argparse.Namespace):
    return run_chunk_quality_audit(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        chunks_path=args.chunks_path,
        output_path=args.output_path,
    )


def _run_chunk_layer_build(args: argparse.Namespace):
    return build_chunk_layers(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        chunks_path=args.chunks_path,
        chunks_v2_dir=args.chunks_v2_dir,
        atomic_max_tokens=args.atomic_max_tokens,
        parent_window_max_tokens=args.parent_window_max_tokens,
    )


def _run_source_register_proving_slice(args: argparse.Namespace):
    return build_source_register_proving_slice(
        workbook_path=args.workbook,
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        config_path=args.config,
        report_path=args.report_path,
    )


def _run_authority_currentness(args: argparse.Namespace):
    resolved_inputs = resolve_authority_currentness_inputs(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        authority_inventory_path=args.authority_inventory,
        source_addition_decisions_path=args.source_addition_decisions,
        catalog_path=args.catalog_path,
        source_set_manifest_path=args.source_set_manifest_path,
    )
    return build_authority_currentness_report(
        output_dir=args.output_dir,
        source_set_id=resolved_inputs["source_set_id"],
        authority_inventory_path=resolved_inputs["authority_inventory_path"],
        source_addition_decisions_path=resolved_inputs["source_addition_decisions_path"],
        source_partition_contract_path=args.source_partition_contract,
        catalog_path=resolved_inputs["catalog_path"],
        source_set_manifest_path=resolved_inputs["source_set_manifest_path"],
        output_path=args.output_path,
    )


def _run_authority_ontology_validate(args: argparse.Namespace):
    return run_authority_ontology_validate(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        ontology_path=args.ontology_path,
        eval_path=args.eval_path,
        graph_contract_path=args.graph_contract_path,
        graph_path=args.graph_path,
        output_path=args.output_path,
    )


def _run_authority_relationship_eval(args: argparse.Namespace):
    return run_authority_relationship_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        report_path=args.report_path,
        eval_path=args.eval_path,
        output_path=args.output_path,
    )


def _run_citation_alias_eval(args: argparse.Namespace):
    return run_citation_alias_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        report_path=args.report_path,
        output_path=args.output_path,
    )


def _run_graph_health_eval(args: argparse.Namespace):
    return run_graph_health_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        report_path=args.report_path,
        contract_path=args.contract_path,
        output_path=args.output_path,
    )


def _run_graph_accuracy_eval(args: argparse.Namespace):
    return run_graph_accuracy_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        report_path=args.report_path,
        eval_path=args.eval_path,
        output_path=args.output_path,
    )


def _run_semantic_graph_eval(args: argparse.Namespace):
    return run_semantic_graph_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        eval_path=args.eval_path,
        output_path=args.output_path,
    )


def _run_incremental_graph_refresh_eval(args: argparse.Namespace):
    return run_incremental_graph_refresh_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        eval_path=args.eval_path,
        output_path=args.output_path,
    )


def _run_retrieval_build(args: argparse.Namespace):
    catalog_sqlite_path = args.catalog_sqlite_path
    if args.catalog_dir is not None:
        catalog_sqlite_path = args.catalog_dir / "review_sources.sqlite"
    return build_retrieval_index(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        chunks_path=args.chunks_path,
        catalog_sqlite_path=catalog_sqlite_path,
        allow_failed_extraction=args.allow_failed_extraction,
        allow_partial_extraction=args.allow_partial_extraction,
    )


def _run_retrieval_query(args: argparse.Namespace):
    index_path = args.index_path or default_index_path(args.output_dir, args.source_set_id)
    return query_retrieval_index(
        index_path=index_path,
        query=args.query,
        limit=args.limit,
        document_role=args.document_role,
        support_document_role=args.support_document_role,
        authority_level=args.authority_level,
        source_record_id=args.source_record_id,
        review_topic=args.review_topic,
        citation=args.citation,
        host=args.host,
    )


def _run_retrieval_eval(args: argparse.Namespace):
    index_path = args.index_path or default_index_path(args.output_dir, args.source_set_id)
    return run_retrieval_eval(
        index_path=index_path,
        eval_file=args.eval_file,
        top_k=args.top_k,
        output_dir=args.results_dir,
    )


def _run_chunk_sidecar_retrieval_eval(args: argparse.Namespace):
    return run_chunk_sidecar_retrieval_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        eval_file=args.eval_file,
        chunks_v2_dir=args.chunks_v2_dir,
        sidecar_index_dir=args.sidecar_index_dir,
        baseline_index_path=args.baseline_index_path,
        results_dir=args.results_dir,
        top_k=args.top_k,
        rebuild_sidecar=args.rebuild_sidecar,
    )


def _run_chunk_sidecar_consumer_eval(args: argparse.Namespace):
    kwargs = {key: value for key, value in vars(args).items() if key != "command"}
    return _module_attr(
        "sidecar_consumer_eval",
        "run_chunk_sidecar_consumer_eval",
    )(**kwargs)


def _run_evidence_graph_build(args: argparse.Namespace):
    return build_evidence_graph(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        catalog_dir=args.catalog_dir,
        allow_partial_retrieval=args.allow_partial_retrieval,
    )


def _run_nepa_knowledge_graph_export(args: argparse.Namespace):
    return build_nepa_knowledge_graph_export(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        review_id=args.review_id,
        graph_contract_path=args.graph_contract,
        authority_inventory_path=args.authority_inventory,
        authority_family_rule_templates_path=args.authority_family_rule_templates,
        forest_plan_profiles_path=args.forest_plan_profiles,
        region1_forest_plan_readiness_path=args.region1_forest_plan_readiness,
        rule_pack_path=args.rule_pack,
        catalog_path=args.catalog_path,
        catalog_graph_nodes_path=args.catalog_graph_nodes_path,
        catalog_graph_edges_path=args.catalog_graph_edges_path,
        source_set_manifest_path=args.source_set_manifest_path,
        authority_currentness_path=args.authority_currentness_path,
        evidence_graph_nodes_path=args.evidence_graph_nodes_path,
        evidence_graph_edges_path=args.evidence_graph_edges_path,
        claims_path=args.claims_path,
        rule_claim_links_path=args.rule_claim_links_path,
        forest_plan_components_path=args.forest_plan_components_path,
    )


def _run_knowledge_graph_query(args: argparse.Namespace):
    return run_knowledge_graph_query(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        review_id=args.review_id,
        query=args.query,
        query_type=args.query_type,
        graph_path=args.graph_path,
        output_path=args.output_path,
        limit=args.limit,
        node_type=args.node_type,
        edge_type=args.edge_type,
        source_record_id=args.source_record_id,
        forest_unit_id=args.forest_unit_id,
        citation=args.citation,
        readiness_status=args.readiness_status,
        require_hit=args.require_hit,
        fail_on_freshness_warning=args.fail_on_freshness_warning,
    )


def _run_knowledge_graph_query_eval(args: argparse.Namespace):
    return run_knowledge_graph_query_eval(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        review_id=args.review_id,
        eval_path=args.eval_path,
        graph_path=args.graph_path,
        output_path=args.output_path,
    )


def _run_claim_extract(args: argparse.Namespace):
    return build_claim_extraction(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        chunks_path=args.chunks_path,
        catalog_sqlite_path=args.catalog_sqlite_path,
        allow_partial_retrieval=args.allow_partial_retrieval,
    )


def _run_claim_eval(args: argparse.Namespace):
    claims_path = args.claims_path or default_claims_path(args.output_dir, args.source_set_id)
    return run_claim_eval(
        claims_path=claims_path,
        eval_file=args.eval_file,
        top_k=args.top_k,
        output_dir=args.results_dir,
    )


def _run_rule_claim_link(args: argparse.Namespace):
    return build_rule_claim_links(
        output_dir=args.output_dir,
        source_set_id=args.source_set_id,
        claims_path=args.claims_path,
        rule_pack_path=args.rule_pack,
        top_k=args.top_k,
        allow_partial_claims=args.allow_partial_claims,
    )


def _run_rule_claim_eval(args: argparse.Namespace):
    links_path = args.links_path or default_rule_claim_links_path(
        args.output_dir,
        source_set_id=args.source_set_id,
        rule_pack_path=args.rule_pack,
    )
    return run_rule_claim_link_eval(
        links_path=links_path,
        eval_file=args.eval_file,
        top_k=args.top_k,
        output_dir=args.results_dir,
    )


COMMAND_HANDLERS = {
    "extract-build": _result_handler(_run_extract_build, "validation_passed"),
    "reuse-inventory": DerivedCommandHandler(
        run=_run_reuse_inventory,
        summary_getter=_result_summary,
        success=_always_true,
    ),
    "forest-plan-source-delta-readiness": _result_handler(
        _run_forest_plan_source_delta_readiness,
        "passed",
    ),
    "extraction-accuracy-audit": _result_handler(_run_extraction_accuracy_audit, "passed"),
    "chunk-quality-audit": _result_handler(_run_chunk_quality_audit, "passed"),
    "chunk-layer-build": _result_handler(_run_chunk_layer_build, "validation_passed"),
    "source-register-proving-slice": _result_handler(
        _run_source_register_proving_slice,
        "validation_passed",
    ),
    "authority-currentness": _result_handler(_run_authority_currentness, "validation_passed"),
    "authority-ontology-validate": _result_handler(
        _run_authority_ontology_validate,
        "passed",
    ),
    "authority-relationship-eval": _result_handler(
        _run_authority_relationship_eval,
        "passed",
    ),
    "citation-alias-eval": _result_handler(_run_citation_alias_eval, "passed"),
    "graph-health-eval": _result_handler(_run_graph_health_eval, "passed"),
    "graph-accuracy-eval": _result_handler(_run_graph_accuracy_eval, "passed"),
    "semantic-graph-eval": _result_handler(_run_semantic_graph_eval, "passed"),
    "incremental-graph-refresh-eval": _result_handler(
        _run_incremental_graph_refresh_eval,
        "passed",
    ),
    "retrieval-build": _result_handler(_run_retrieval_build, "validation_passed"),
    "retrieval-query": _summary_handler(_run_retrieval_query, "hit_count"),
    "retrieval-eval": _result_handler(_run_retrieval_eval, "passed"),
    "chunk-sidecar-retrieval-eval": _result_handler(
        _run_chunk_sidecar_retrieval_eval,
        "passed",
    ),
    "chunk-sidecar-consumer-eval": _result_handler(
        _run_chunk_sidecar_consumer_eval,
        "passed",
    ),
    "evidence-graph-build": _result_handler(
        _run_evidence_graph_build,
        "validation_passed",
    ),
    "nepa-knowledge-graph-export": _result_handler(
        _run_nepa_knowledge_graph_export,
        "validation_passed",
    ),
    "knowledge-graph-query": _result_handler(_run_knowledge_graph_query, "passed"),
    "knowledge-graph-query-eval": _result_handler(
        _run_knowledge_graph_query_eval,
        "passed",
    ),
    "claim-extract": _result_handler(_run_claim_extract, "validation_passed"),
    "claim-eval": _result_handler(_run_claim_eval, "passed"),
    "rule-claim-link": _result_handler(_run_rule_claim_link, "validation_passed"),
    "rule-claim-eval": _result_handler(_run_rule_claim_eval, "passed"),
}


def handle_derived_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    return dispatch_derived_command(args, COMMAND_HANDLERS, print_summary)
