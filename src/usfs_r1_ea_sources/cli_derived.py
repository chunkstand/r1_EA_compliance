from __future__ import annotations

from pathlib import Path
import argparse

from .authority_currentness import DEFAULT_AUTHORITY_INVENTORY_PATH
from .authority_currentness import DEFAULT_SOURCE_ADDITION_DECISIONS_PATH
from .authority_currentness import build_authority_currentness_report
from .claim_extraction import DEFAULT_CLAIM_EVAL_PATH
from .claim_extraction import build_claim_extraction
from .claim_extraction import default_claims_path
from .claim_extraction import run_claim_eval
from .cli_common import print_summary
from .evidence_graph import build_evidence_graph
from .extract import build_extraction
from .extraction_accuracy import run_extraction_accuracy_audit
from .forest_plan_source_delta_readiness import DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH
from .forest_plan_source_delta_readiness import DEFAULT_R1_FOREST_PLAN_REGISTER_PATH
from .forest_plan_source_delta_readiness import DEFAULT_SOURCE_DELTA_BATCH_RUN_ID
from .forest_plan_source_delta_readiness import build_forest_plan_source_delta_readiness_report
from .nepa_3d_graph_contract import DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH
from .nepa_knowledge_graph_export import DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH
from .nepa_knowledge_graph_export import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .nepa_knowledge_graph_export import DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH
from .nepa_knowledge_graph_export import build_nepa_knowledge_graph_export
from .retrieval import build_retrieval_index
from .retrieval import default_index_path
from .retrieval import query_retrieval_index
from .retrieval import run_retrieval_eval
from .reuse_inventory import build_reuse_inventory
from .rule_claim_binding import DEFAULT_RULE_CLAIM_EVAL_PATH
from .rule_claim_binding import build_rule_claim_links
from .rule_claim_binding import default_rule_claim_links_path
from .rule_claim_binding import run_rule_claim_link_eval
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .source_partitions import DEFAULT_SOURCE_PARTITION_CONTRACT_PATH


DERIVED_COMMANDS = {
    "extract-build",
    "reuse-inventory",
    "forest-plan-source-delta-readiness",
    "extraction-accuracy-audit",
    "authority-currentness",
    "retrieval-build",
    "retrieval-query",
    "retrieval-eval",
    "evidence-graph-build",
    "nepa-knowledge-graph-export",
    "claim-extract",
    "claim-eval",
    "rule-claim-link",
    "rule-claim-eval",
}


def register_derived_commands(subparsers: argparse._SubParsersAction) -> None:
    extract = subparsers.add_parser(
        "extract-build",
        help="Build derived extracted text, chunks, and extraction diagnostics.",
    )
    extract.add_argument("--output-dir", default=Path("source_library"), type=Path)
    extract.add_argument("--catalog-dir", type=Path)
    extract.add_argument("--id", action="append", dest="ids")
    extract.add_argument("--parser")
    extract.add_argument("--limit", type=int)
    extract.add_argument("--chunk-max-chars", type=int, default=1800)
    extract.add_argument("--chunk-overlap-chars", type=int, default=200)
    extract.add_argument("--prefer-docling", action="store_true")
    extract.add_argument("--docling-ocr", action="store_true")
    extract.add_argument("--docling-timeout-seconds", type=float, default=300.0)
    extract.add_argument("--allow-invalid-catalog", action="store_true")
    extract.add_argument("--reuse-existing", action="store_true")
    extract.add_argument("--reuse-inventory-path", type=Path)

    reuse_inventory = subparsers.add_parser(
        "reuse-inventory",
        help="Inventory reusable extraction records without running extraction or review commands.",
    )
    reuse_inventory.add_argument("--output-dir", default=Path("source_library"), type=Path)
    reuse_inventory.add_argument("--source-set-id")
    reuse_inventory.add_argument("--catalog-dir", type=Path)
    reuse_inventory.add_argument("--previous-source-set-id", action="append", dest="previous_source_set_ids")
    reuse_inventory.add_argument("--catalog-path", type=Path)
    reuse_inventory.add_argument("--skip-artifact-hash-check", action="store_true")

    source_delta_readiness = subparsers.add_parser(
        "forest-plan-source-delta-readiness",
        help="Build the Region 1 forest-plan source-delta readiness baseline report.",
    )
    source_delta_readiness.add_argument("--output-dir", default=Path("source_library"), type=Path)
    source_delta_readiness.add_argument(
        "--r1-forest-plan-register",
        default=DEFAULT_R1_FOREST_PLAN_REGISTER_PATH,
        type=Path,
    )
    source_delta_readiness.add_argument(
        "--source-delta-batch-run-id",
        default=DEFAULT_SOURCE_DELTA_BATCH_RUN_ID,
    )
    source_delta_readiness.add_argument("--scoped-catalog-gate-dir", type=Path)
    source_delta_readiness.add_argument("--merged-catalog-gate-dir", type=Path)
    source_delta_readiness.add_argument("--canonical-catalog-dir", type=Path)
    source_delta_readiness.add_argument("--extraction-source-set-id")
    source_delta_readiness.add_argument("--reuse-inventory-path", type=Path)
    source_delta_readiness.add_argument(
        "--forest-plan-profiles",
        default=DEFAULT_FOREST_PLAN_PROFILES_PATH,
        type=Path,
    )
    source_delta_readiness.add_argument(
        "--official-source-gap-evidence",
        default=DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH,
        type=Path,
    )
    source_delta_readiness.add_argument("--results-dir", type=Path)

    extraction_accuracy = subparsers.add_parser(
        "extraction-accuracy-audit",
        help="Run deterministic extraction accuracy checks against generated extraction outputs.",
    )
    extraction_accuracy.add_argument("--output-dir", default=Path("source_library"), type=Path)
    extraction_accuracy.add_argument("--source-set-id")
    extraction_accuracy.add_argument("--output-path", type=Path)

    authority_currentness = subparsers.add_parser(
        "authority-currentness",
        help="Build a source-currentness validation report for the authority-family inventory.",
    )
    authority_currentness.add_argument("--output-dir", default=Path("source_library"), type=Path)
    authority_currentness.add_argument("--source-set-id")
    authority_currentness.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )
    authority_currentness.add_argument(
        "--source-addition-decisions",
        default=DEFAULT_SOURCE_ADDITION_DECISIONS_PATH,
        type=Path,
    )
    authority_currentness.add_argument(
        "--source-partition-contract",
        default=DEFAULT_SOURCE_PARTITION_CONTRACT_PATH,
        type=Path,
    )
    authority_currentness.add_argument("--catalog-path", type=Path)
    authority_currentness.add_argument("--source-set-manifest-path", type=Path)
    authority_currentness.add_argument("--output-path", type=Path)

    retrieval_build = subparsers.add_parser(
        "retrieval-build",
        help="Build a local evidence retrieval index from extracted chunks.",
    )
    retrieval_build.add_argument("--output-dir", default=Path("source_library"), type=Path)
    retrieval_build.add_argument("--source-set-id")
    retrieval_build.add_argument("--chunks-path", type=Path)
    retrieval_build.add_argument("--catalog-dir", type=Path)
    retrieval_build.add_argument("--catalog-sqlite-path", type=Path)
    retrieval_build.add_argument("--allow-failed-extraction", action="store_true")
    retrieval_build.add_argument("--allow-partial-extraction", action="store_true")

    retrieval_query = subparsers.add_parser(
        "retrieval-query",
        help="Query the local evidence index and print provenance-bearing evidence spans.",
    )
    retrieval_query.add_argument("query")
    retrieval_query.add_argument("--output-dir", default=Path("source_library"), type=Path)
    retrieval_query.add_argument("--source-set-id")
    retrieval_query.add_argument("--index-path", type=Path)
    retrieval_query.add_argument("--limit", type=int, default=5)
    retrieval_query.add_argument("--document-role")
    retrieval_query.add_argument("--support-document-role")
    retrieval_query.add_argument("--authority-level")
    retrieval_query.add_argument("--source-record-id")
    retrieval_query.add_argument("--review-topic")
    retrieval_query.add_argument("--citation")
    retrieval_query.add_argument("--host")

    retrieval_eval = subparsers.add_parser(
        "retrieval-eval",
        help="Run the evidence retrieval eval set against a local retrieval index.",
    )
    retrieval_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    retrieval_eval.add_argument("--source-set-id")
    retrieval_eval.add_argument("--index-path", type=Path)
    retrieval_eval.add_argument("--eval-file", default=Path("config/retrieval_eval_seed.json"), type=Path)
    retrieval_eval.add_argument("--top-k", type=int, default=5)
    retrieval_eval.add_argument("--results-dir", type=Path)

    evidence_graph = subparsers.add_parser(
        "evidence-graph-build",
        help="Build a document evidence graph from extracted chunks and retrieval metadata.",
    )
    evidence_graph.add_argument("--output-dir", default=Path("source_library"), type=Path)
    evidence_graph.add_argument("--source-set-id")
    evidence_graph.add_argument("--allow-partial-retrieval", action="store_true")

    nepa_graph = subparsers.add_parser(
        "nepa-knowledge-graph-export",
        help="Build the source-set NEPA 3D knowledge graph export from audited artifacts.",
    )
    nepa_graph.add_argument("--output-dir", default=Path("source_library"), type=Path)
    nepa_graph.add_argument("--source-set-id")
    nepa_graph.add_argument("--review-id")
    nepa_graph.add_argument(
        "--graph-contract",
        default=DEFAULT_NEPA_3D_GRAPH_CONTRACT_PATH,
        type=Path,
    )
    nepa_graph.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )
    nepa_graph.add_argument(
        "--authority-family-rule-templates",
        default=DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH,
        type=Path,
    )
    nepa_graph.add_argument(
        "--forest-plan-profiles",
        default=DEFAULT_FOREST_PLAN_PROFILES_PATH,
        type=Path,
    )
    nepa_graph.add_argument(
        "--region1-forest-plan-readiness",
        default=DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH,
        type=Path,
    )
    nepa_graph.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    nepa_graph.add_argument("--catalog-path", type=Path)
    nepa_graph.add_argument("--catalog-graph-nodes-path", type=Path)
    nepa_graph.add_argument("--catalog-graph-edges-path", type=Path)
    nepa_graph.add_argument("--source-set-manifest-path", type=Path)
    nepa_graph.add_argument("--authority-currentness-path", type=Path)
    nepa_graph.add_argument("--evidence-graph-nodes-path", type=Path)
    nepa_graph.add_argument("--evidence-graph-edges-path", type=Path)
    nepa_graph.add_argument("--claims-path", type=Path)
    nepa_graph.add_argument("--rule-claim-links-path", type=Path)
    nepa_graph.add_argument("--forest-plan-components-path", type=Path)

    claim_extract = subparsers.add_parser(
        "claim-extract",
        help="Extract deterministic source-text claims and entity graph artifacts from chunks.",
    )
    claim_extract.add_argument("--output-dir", default=Path("source_library"), type=Path)
    claim_extract.add_argument("--source-set-id")
    claim_extract.add_argument("--chunks-path", type=Path)
    claim_extract.add_argument("--catalog-sqlite-path", type=Path)
    claim_extract.add_argument("--allow-partial-retrieval", action="store_true")

    claim_eval = subparsers.add_parser(
        "claim-eval",
        help="Run deterministic eval cases against extracted source claims.",
    )
    claim_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    claim_eval.add_argument("--source-set-id")
    claim_eval.add_argument("--claims-path", type=Path)
    claim_eval.add_argument("--eval-file", default=DEFAULT_CLAIM_EVAL_PATH, type=Path)
    claim_eval.add_argument("--top-k", type=int, default=5)
    claim_eval.add_argument("--results-dir", type=Path)

    rule_claim_link = subparsers.add_parser(
        "rule-claim-link",
        help="Build deterministic links from compliance rules to validated source claims.",
    )
    rule_claim_link.add_argument("--output-dir", default=Path("source_library"), type=Path)
    rule_claim_link.add_argument("--source-set-id")
    rule_claim_link.add_argument("--claims-path", type=Path)
    rule_claim_link.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    rule_claim_link.add_argument("--top-k", type=int, default=5)

    rule_claim_eval = subparsers.add_parser(
        "rule-claim-eval",
        help="Run deterministic eval cases against rule-to-source-claim links.",
    )
    rule_claim_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    rule_claim_eval.add_argument("--source-set-id")
    rule_claim_eval.add_argument("--links-path", type=Path)
    rule_claim_eval.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    rule_claim_eval.add_argument("--eval-file", default=DEFAULT_RULE_CLAIM_EVAL_PATH, type=Path)
    rule_claim_eval.add_argument("--top-k", type=int, default=5)
    rule_claim_eval.add_argument("--results-dir", type=Path)


def handle_derived_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
    if args.command == "extract-build":
        result = build_extraction(
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
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "reuse-inventory":
        result = build_reuse_inventory(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            previous_source_set_ids=args.previous_source_set_ids,
            catalog_dir=args.catalog_dir,
            catalog_path=args.catalog_path,
            verify_artifact_hashes=not args.skip_artifact_hash_check,
        )
        print_summary(result.summary)
        return 0

    if args.command == "forest-plan-source-delta-readiness":
        result = build_forest_plan_source_delta_readiness_report(
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
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "extraction-accuracy-audit":
        result = run_extraction_accuracy_audit(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "authority-currentness":
        result = build_authority_currentness_report(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            authority_inventory_path=args.authority_inventory,
            source_addition_decisions_path=args.source_addition_decisions,
            source_partition_contract_path=args.source_partition_contract,
            catalog_path=args.catalog_path,
            source_set_manifest_path=args.source_set_manifest_path,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "retrieval-build":
        catalog_sqlite_path = args.catalog_sqlite_path
        if args.catalog_dir is not None:
            catalog_sqlite_path = args.catalog_dir / "review_sources.sqlite"
        result = build_retrieval_index(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            chunks_path=args.chunks_path,
            catalog_sqlite_path=catalog_sqlite_path,
            allow_failed_extraction=args.allow_failed_extraction,
            allow_partial_extraction=args.allow_partial_extraction,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "retrieval-query":
        index_path = args.index_path or default_index_path(args.output_dir, args.source_set_id)
        result = query_retrieval_index(
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
        print_summary(result)
        return 0 if result["hit_count"] else 1

    if args.command == "retrieval-eval":
        index_path = args.index_path or default_index_path(args.output_dir, args.source_set_id)
        result = run_retrieval_eval(
            index_path=index_path,
            eval_file=args.eval_file,
            top_k=args.top_k,
            output_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "evidence-graph-build":
        result = build_evidence_graph(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            allow_partial_retrieval=args.allow_partial_retrieval,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "nepa-knowledge-graph-export":
        result = build_nepa_knowledge_graph_export(
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
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "claim-extract":
        result = build_claim_extraction(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            chunks_path=args.chunks_path,
            catalog_sqlite_path=args.catalog_sqlite_path,
            allow_partial_retrieval=args.allow_partial_retrieval,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "claim-eval":
        claims_path = args.claims_path or default_claims_path(args.output_dir, args.source_set_id)
        result = run_claim_eval(
            claims_path=claims_path,
            eval_file=args.eval_file,
            top_k=args.top_k,
            output_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "rule-claim-link":
        result = build_rule_claim_links(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            claims_path=args.claims_path,
            rule_pack_path=args.rule_pack,
            top_k=args.top_k,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "rule-claim-eval":
        links_path = args.links_path or default_rule_claim_links_path(
            args.output_dir,
            source_set_id=args.source_set_id,
            rule_pack_path=args.rule_pack,
        )
        result = run_rule_claim_link_eval(
            links_path=links_path,
            eval_file=args.eval_file,
            top_k=args.top_k,
            output_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None
