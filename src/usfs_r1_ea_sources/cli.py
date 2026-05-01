from __future__ import annotations

from pathlib import Path
import argparse
import json

from .batches import run_batch_downloads
from .catalog import build_review_catalog
from .claim_extraction import DEFAULT_CLAIM_EVAL_PATH
from .claim_extraction import build_claim_extraction
from .claim_extraction import default_claims_path
from .claim_extraction import run_claim_eval
from .compliance_coverage import DEFAULT_COVERAGE_MATRIX_PATH
from .compliance_coverage import run_compliance_coverage
from .compliance_gold_eval import DEFAULT_COMPLIANCE_GOLD_EVAL_PATH
from .compliance_gold_eval import run_compliance_gold_eval
from .compliance_review import DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH
from .compliance_review import DEFAULT_RULE_PACK_PATH
from .compliance_review import run_compliance_review
from .compliance_review import run_compliance_review_eval
from .config import DEFAULT_CONFIG_PATH, load_config
from .download import run_download
from .dry_run import run_dry_run
from .ea_review import DEFAULT_CHECKLIST_PATH
from .ea_review import run_ea_review
from .evidence_graph import build_evidence_graph
from .evidence_graph import run_phase_aligned_eval
from .extract import build_extraction
from .extraction_accuracy import run_extraction_accuracy_audit
from .forest_plan_resolver import run_forest_plan_resolver
from .pilots import run_host_pilots
from .preflight import run_preflight
from .report import build_run_report
from .retrieval import build_retrieval_index
from .retrieval import default_index_path
from .retrieval import query_retrieval_index
from .retrieval import run_retrieval_eval
from .rule_claim_binding import DEFAULT_RULE_CLAIM_EVAL_PATH
from .rule_claim_binding import build_rule_claim_links
from .rule_claim_binding import default_rule_claim_links_path
from .rule_claim_binding import run_rule_claim_link_eval
from .validate_run import validate_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usfs-r1-ea-sources",
        description="USFS Region 1 EA source-library tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dry_run = subparsers.add_parser(
        "dry-run",
        help="Parse workbook and write manifest/report outputs without network downloads.",
    )
    dry_run.add_argument("--workbook", required=True, type=Path)
    dry_run.add_argument("--output-dir", default=Path("source_library"), type=Path)
    dry_run.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    dry_run.add_argument("--run-id")
    dry_run.add_argument("--sheet")
    dry_run.add_argument("--id")
    dry_run.add_argument("--host")
    dry_run.add_argument("--limit", type=int)

    preflight = subparsers.add_parser(
        "preflight",
        help="Check planned source URLs and write preflight reports without saving artifacts.",
    )
    preflight.add_argument("--workbook", required=True, type=Path)
    preflight.add_argument("--output-dir", default=Path("source_library"), type=Path)
    preflight.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    preflight.add_argument("--run-id")
    preflight.add_argument("--sheet")
    preflight.add_argument("--id")
    preflight.add_argument("--host")
    preflight.add_argument("--limit", type=int)

    download = subparsers.add_parser(
        "download",
        help="Download validated source URLs, save immutable raw artifacts, and write reports.",
    )
    download.add_argument("--workbook", required=True, type=Path)
    download.add_argument("--output-dir", default=Path("source_library"), type=Path)
    download.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    download.add_argument("--run-id")
    download.add_argument("--sheet")
    download.add_argument("--id")
    download.add_argument("--host")
    download.add_argument("--limit", type=int)
    download.add_argument("--force", action="store_true")

    report = subparsers.add_parser(
        "report",
        help="Build an operator report for a previous dry-run, preflight, or download run.",
    )
    report.add_argument("--output-dir", default=Path("source_library"), type=Path)
    report.add_argument("--run-id", required=True)
    report.add_argument(
        "--json",
        action="store_true",
        help="Print report summary JSON instead of Markdown.",
    )

    validate = subparsers.add_parser(
        "validate-run",
        help="Run acceptance-gate checks for a previous run manifest and artifacts.",
    )
    validate.add_argument("--output-dir", default=Path("source_library"), type=Path)
    validate.add_argument("--run-id", required=True)

    pilots = subparsers.add_parser(
        "pilot-hosts",
        help="Run staged host pilots: download, report, and validate each selected host.",
    )
    pilots.add_argument("--workbook", required=True, type=Path)
    pilots.add_argument("--output-dir", default=Path("source_library"), type=Path)
    pilots.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    pilots.add_argument("--run-id-prefix", default="host-pilot")
    pilots.add_argument(
        "--host",
        action="append",
        help="Host to pilot. Repeat for multiple hosts. Defaults to all canonical hosts.",
    )
    pilots.add_argument("--limit-per-host", type=int)
    pilots.add_argument("--force", action="store_true")

    batches = subparsers.add_parser(
        "batch-download",
        help="Plan and run controlled download batches with a ledger and acceptance gates.",
    )
    batches.add_argument("--workbook", required=True, type=Path)
    batches.add_argument("--output-dir", default=Path("source_library"), type=Path)
    batches.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    batches.add_argument("--run-id-prefix", default="batch")
    batches.add_argument(
        "--host",
        action="append",
        help="Host to batch. Repeat for multiple hosts.",
    )
    batches.add_argument("--batch-size", type=int, default=5)
    batches.add_argument("--limit-per-host", type=int)
    batches.add_argument("--force", action="store_true")
    batches.add_argument("--plan-only", action="store_true")
    batches.add_argument("--resume", action="store_true")
    batches.add_argument("--continue-on-failure", action="store_true")

    catalog = subparsers.add_parser(
        "catalog-build",
        help="Build reviewer-engine source catalog, source-set manifest, and SQLite index.",
    )
    catalog.add_argument("--workbook", required=True, type=Path)
    catalog.add_argument("--output-dir", default=Path("source_library"), type=Path)
    catalog.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    catalog.add_argument(
        "--run-id",
        help="Optional download run ID to link artifacts into the catalog.",
    )
    catalog.add_argument(
        "--batch-run-id",
        help=(
            "Optional parent batch-download run ID to link artifacts from all passed child "
            "batches."
        ),
    )

    extract = subparsers.add_parser(
        "extract-build",
        help=(
            "Build derived extracted text, chunks, and extraction diagnostics from the reviewer "
            "catalog."
        ),
    )
    extract.add_argument("--output-dir", default=Path("source_library"), type=Path)
    extract.add_argument(
        "--id",
        action="append",
        dest="ids",
        help="Limit extraction to a source_record_id. Repeat for multiple IDs.",
    )
    extract.add_argument("--parser", help="Limit extraction to one expected_parser value.")
    extract.add_argument("--limit", type=int)
    extract.add_argument("--chunk-max-chars", type=int, default=1800)
    extract.add_argument("--chunk-overlap-chars", type=int, default=200)
    extract.add_argument(
        "--prefer-docling",
        action="store_true",
        help="Use Docling for HTML/DOCX when installed. PDF always requires Docling.",
    )
    extract.add_argument(
        "--docling-ocr",
        action="store_true",
        help="Enable Docling OCR for PDFs. Default is born-digital PDF extraction without OCR.",
    )
    extract.add_argument(
        "--docling-timeout-seconds",
        type=float,
        default=300.0,
        help="Per-document Docling timeout. Use 0 to disable the timeout.",
    )
    extract.add_argument(
        "--allow-invalid-catalog",
        action="store_true",
        help="Run even if catalog_validation.json has not passed.",
    )

    extraction_accuracy = subparsers.add_parser(
        "extraction-accuracy-audit",
        help="Run deterministic extraction accuracy checks against generated extraction outputs.",
    )
    extraction_accuracy.add_argument("--output-dir", default=Path("source_library"), type=Path)
    extraction_accuracy.add_argument("--source-set-id")
    extraction_accuracy.add_argument("--output-path", type=Path)

    retrieval_build = subparsers.add_parser(
        "retrieval-build",
        help="Build a local evidence retrieval index from extracted chunks.",
    )
    retrieval_build.add_argument("--output-dir", default=Path("source_library"), type=Path)
    retrieval_build.add_argument("--source-set-id")
    retrieval_build.add_argument("--chunks-path", type=Path)
    retrieval_build.add_argument("--catalog-sqlite-path", type=Path)
    retrieval_build.add_argument(
        "--allow-failed-extraction",
        action="store_true",
        help="Build even if extraction_validation.json has not passed.",
    )
    retrieval_build.add_argument(
        "--allow-partial-extraction",
        action="store_true",
        help="Build a diagnostic index from a filtered extraction slice.",
    )

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
    retrieval_eval.add_argument(
        "--eval-file",
        default=Path("config/retrieval_eval_seed.json"),
        type=Path,
    )
    retrieval_eval.add_argument("--top-k", type=int, default=5)
    retrieval_eval.add_argument("--results-dir", type=Path)

    evidence_graph = subparsers.add_parser(
        "evidence-graph-build",
        help="Build a document evidence graph from extracted chunks and retrieval metadata.",
    )
    evidence_graph.add_argument("--output-dir", default=Path("source_library"), type=Path)
    evidence_graph.add_argument("--source-set-id")
    evidence_graph.add_argument(
        "--allow-partial-retrieval",
        action="store_true",
        help="Build a diagnostic graph from a non-reviewer-ready retrieval index.",
    )

    claim_extract = subparsers.add_parser(
        "claim-extract",
        help="Extract deterministic source-text claims and entity graph artifacts from chunks.",
    )
    claim_extract.add_argument("--output-dir", default=Path("source_library"), type=Path)
    claim_extract.add_argument("--source-set-id")
    claim_extract.add_argument("--chunks-path", type=Path)
    claim_extract.add_argument("--catalog-sqlite-path", type=Path)
    claim_extract.add_argument(
        "--allow-partial-retrieval",
        action="store_true",
        help="Build diagnostic claims from a non-reviewer-ready retrieval index.",
    )

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
    rule_claim_eval.add_argument(
        "--eval-file",
        default=DEFAULT_RULE_CLAIM_EVAL_PATH,
        type=Path,
    )
    rule_claim_eval.add_argument("--top-k", type=int, default=5)
    rule_claim_eval.add_argument("--results-dir", type=Path)

    phase_eval = subparsers.add_parser(
        "phase-eval",
        help=(
            "Run phase-aligned readiness evals across catalog, extraction, retrieval, graph, "
            "claim extraction, rule-claim binding, and optionally one compliance review."
        ),
    )
    phase_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    phase_eval.add_argument("--source-set-id")
    phase_eval.add_argument(
        "--review-id",
        help="Optional compliance review ID to include as a phase gate.",
    )
    phase_eval.add_argument(
        "--review-dir",
        type=Path,
        help="Optional explicit compliance review directory to include as a phase gate.",
    )

    ea_review = subparsers.add_parser(
        "ea-review",
        help="Run a deterministic, evidence-backed EA package checklist review.",
    )
    ea_review.add_argument("--package-path", required=True, type=Path)
    ea_review.add_argument("--output-dir", default=Path("source_library"), type=Path)
    ea_review.add_argument("--source-set-id")
    ea_review.add_argument("--index-path", type=Path)
    ea_review.add_argument("--checklist", default=DEFAULT_CHECKLIST_PATH, type=Path)
    ea_review.add_argument("--review-id")
    ea_review.add_argument("--results-dir", type=Path)
    ea_review.add_argument("--source-top-k", type=int, default=3)
    ea_review.add_argument("--package-top-k", type=int, default=3)
    ea_review.add_argument("--chunk-max-chars", type=int, default=1800)
    ea_review.add_argument("--chunk-overlap-chars", type=int, default=200)
    ea_review.add_argument(
        "--reuse-package-cache",
        action="store_true",
        help=(
            "Reuse existing package/package_manifest.jsonl and package/package_chunks.jsonl "
            "under the review directory instead of re-extracting package files."
        ),
    )
    ea_review.add_argument(
        "--docling-ocr",
        action="store_true",
        help="Enable Docling OCR for PDF EA package files.",
    )
    ea_review.add_argument(
        "--docling-timeout-seconds",
        type=float,
        default=120.0,
        help="Per-document Docling timeout for PDF EA package files. Use 0 to disable.",
    )

    forest_plan_resolve = subparsers.add_parser(
        "forest-plan-resolve",
        help="Resolve Custer Gallatin forest-plan context from a local EA package.",
    )
    forest_plan_resolve.add_argument("--package-path", required=True, type=Path)
    forest_plan_resolve.add_argument("--output-dir", default=Path("source_library"), type=Path)
    forest_plan_resolve.add_argument("--source-set-id")
    forest_plan_resolve.add_argument("--index-path", type=Path)
    forest_plan_resolve.add_argument("--review-id")
    forest_plan_resolve.add_argument("--results-dir", type=Path)
    forest_plan_resolve.add_argument("--source-top-k", type=int, default=2)
    forest_plan_resolve.add_argument("--chunk-max-chars", type=int, default=1800)
    forest_plan_resolve.add_argument("--chunk-overlap-chars", type=int, default=200)
    forest_plan_resolve.add_argument(
        "--reuse-package-cache",
        action="store_true",
        help=(
            "Reuse existing package/package_manifest.jsonl and package/package_chunks.jsonl "
            "under the review directory instead of re-extracting package files."
        ),
    )
    forest_plan_resolve.add_argument(
        "--docling-ocr",
        action="store_true",
        help="Enable Docling OCR for PDF EA package files.",
    )
    forest_plan_resolve.add_argument(
        "--docling-timeout-seconds",
        type=float,
        default=120.0,
        help="Per-document Docling timeout for PDF EA package files. Use 0 to disable.",
    )

    compliance_review = subparsers.add_parser(
        "compliance-review",
        help="Run a versioned compliance rule pack against a local EA package.",
    )
    compliance_review.add_argument("--package-path", required=True, type=Path)
    compliance_review.add_argument("--output-dir", default=Path("source_library"), type=Path)
    compliance_review.add_argument("--source-set-id")
    compliance_review.add_argument("--index-path", type=Path)
    compliance_review.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    compliance_review.add_argument("--review-id")
    compliance_review.add_argument("--results-dir", type=Path)
    compliance_review.add_argument("--source-top-k", type=int, default=3)
    compliance_review.add_argument("--package-top-k", type=int, default=3)
    compliance_review.add_argument("--chunk-max-chars", type=int, default=1800)
    compliance_review.add_argument("--chunk-overlap-chars", type=int, default=200)
    compliance_review.add_argument(
        "--reuse-package-cache",
        action="store_true",
        help=(
            "Reuse existing package/package_manifest.jsonl and package/package_chunks.jsonl "
            "under the review directory instead of re-extracting package files."
        ),
    )
    compliance_review.add_argument(
        "--docling-ocr",
        action="store_true",
        help="Enable Docling OCR for PDF EA package files.",
    )
    compliance_review.add_argument(
        "--docling-timeout-seconds",
        type=float,
        default=120.0,
        help="Per-document Docling timeout for PDF EA package files. Use 0 to disable.",
    )

    compliance_review_eval = subparsers.add_parser(
        "compliance-review-eval",
        help="Run deterministic eval cases against compliance-review findings.",
    )
    compliance_review_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    compliance_review_eval.add_argument("--source-set-id")
    compliance_review_eval.add_argument("--index-path", type=Path)
    compliance_review_eval.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    compliance_review_eval.add_argument(
        "--eval-file",
        default=DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH,
        type=Path,
    )
    compliance_review_eval.add_argument("--results-dir", type=Path)
    compliance_review_eval.add_argument("--source-top-k", type=int, default=3)
    compliance_review_eval.add_argument("--package-top-k", type=int, default=3)
    compliance_review_eval.add_argument("--chunk-max-chars", type=int, default=1800)
    compliance_review_eval.add_argument("--chunk-overlap-chars", type=int, default=200)
    compliance_review_eval.add_argument(
        "--docling-ocr",
        action="store_true",
        help="Enable Docling OCR for PDF EA package fixtures.",
    )
    compliance_review_eval.add_argument(
        "--docling-timeout-seconds",
        type=float,
        default=120.0,
        help="Per-document Docling timeout for PDF EA package fixtures. Use 0 to disable.",
    )

    compliance_gold_eval = subparsers.add_parser(
        "compliance-gold-eval",
        help="Run adjudicated gold package fixtures through the compliance-review gate.",
    )
    compliance_gold_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    compliance_gold_eval.add_argument("--source-set-id")
    compliance_gold_eval.add_argument("--index-path", type=Path)
    compliance_gold_eval.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    compliance_gold_eval.add_argument(
        "--gold-file",
        default=DEFAULT_COMPLIANCE_GOLD_EVAL_PATH,
        type=Path,
    )
    compliance_gold_eval.add_argument("--results-dir", type=Path)
    compliance_gold_eval.add_argument("--source-top-k", type=int, default=3)
    compliance_gold_eval.add_argument("--package-top-k", type=int, default=3)
    compliance_gold_eval.add_argument("--chunk-max-chars", type=int, default=1800)
    compliance_gold_eval.add_argument("--chunk-overlap-chars", type=int, default=200)
    compliance_gold_eval.add_argument(
        "--docling-ocr",
        action="store_true",
        help="Enable Docling OCR for PDF gold package fixtures.",
    )
    compliance_gold_eval.add_argument(
        "--docling-timeout-seconds",
        type=float,
        default=120.0,
        help="Per-document Docling timeout for PDF gold package fixtures. Use 0 to disable.",
    )

    compliance_coverage = subparsers.add_parser(
        "compliance-coverage",
        help="Validate rule-pack coverage across coverage matrix, source-claim links, terms, and eval cases.",
    )
    compliance_coverage.add_argument("--output-dir", default=Path("source_library"), type=Path)
    compliance_coverage.add_argument("--source-set-id")
    compliance_coverage.add_argument("--links-path", type=Path)
    compliance_coverage.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    compliance_coverage.add_argument(
        "--coverage-matrix",
        default=DEFAULT_COVERAGE_MATRIX_PATH,
        type=Path,
    )
    compliance_coverage.add_argument(
        "--eval-file",
        default=DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH,
        type=Path,
    )
    compliance_coverage.add_argument("--results-dir", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "dry-run":
        config = load_config(args.config)
        result = run_dry_run(
            workbook_path=args.workbook,
            output_dir=args.output_dir,
            config=config,
            run_id=args.run_id,
            sheet_filter=args.sheet,
            id_filter=args.id,
            host_filter=args.host,
            limit=args.limit,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "extract-build":
        result = build_extraction(
            output_dir=args.output_dir,
            id_filters=set(args.ids or []),
            parser_filter=args.parser,
            limit=args.limit,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            prefer_docling=args.prefer_docling,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=args.docling_timeout_seconds,
            allow_invalid_catalog=args.allow_invalid_catalog,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "extraction-accuracy-audit":
        result = run_extraction_accuracy_audit(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            output_path=args.output_path,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "retrieval-build":
        result = build_retrieval_index(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            chunks_path=args.chunks_path,
            catalog_sqlite_path=args.catalog_sqlite_path,
            allow_failed_extraction=args.allow_failed_extraction,
            allow_partial_extraction=args.allow_partial_extraction,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "retrieval-query":
        index_path = args.index_path or default_index_path(args.output_dir, args.source_set_id)
        result = query_retrieval_index(
            index_path=index_path,
            query=args.query,
            limit=args.limit,
            document_role=args.document_role,
            authority_level=args.authority_level,
            source_record_id=args.source_record_id,
            review_topic=args.review_topic,
            citation=args.citation,
            host=args.host,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["hit_count"] else 1

    if args.command == "retrieval-eval":
        index_path = args.index_path or default_index_path(args.output_dir, args.source_set_id)
        result = run_retrieval_eval(
            index_path=index_path,
            eval_file=args.eval_file,
            top_k=args.top_k,
            output_dir=args.results_dir,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "evidence-graph-build":
        result = build_evidence_graph(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            allow_partial_retrieval=args.allow_partial_retrieval,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "claim-extract":
        result = build_claim_extraction(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            chunks_path=args.chunks_path,
            catalog_sqlite_path=args.catalog_sqlite_path,
            allow_partial_retrieval=args.allow_partial_retrieval,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "claim-eval":
        claims_path = args.claims_path or default_claims_path(
            args.output_dir,
            args.source_set_id,
        )
        result = run_claim_eval(
            claims_path=claims_path,
            eval_file=args.eval_file,
            top_k=args.top_k,
            output_dir=args.results_dir,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "rule-claim-link":
        result = build_rule_claim_links(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            claims_path=args.claims_path,
            rule_pack_path=args.rule_pack,
            top_k=args.top_k,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
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
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "phase-eval":
        result = run_phase_aligned_eval(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            review_id=args.review_id,
            review_dir=args.review_dir,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "ea-review":
        timeout = args.docling_timeout_seconds
        if timeout is not None and timeout <= 0:
            timeout = None
        result = run_ea_review(
            package_path=args.package_path,
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            checklist_path=args.checklist,
            review_id=args.review_id,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            package_top_k=args.package_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=timeout,
            reuse_package_cache=args.reuse_package_cache,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "forest-plan-resolve":
        timeout = args.docling_timeout_seconds
        if timeout is not None and timeout <= 0:
            timeout = None
        result = run_forest_plan_resolver(
            package_path=args.package_path,
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            review_id=args.review_id,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=timeout,
            reuse_package_cache=args.reuse_package_cache,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "compliance-review":
        timeout = args.docling_timeout_seconds
        if timeout is not None and timeout <= 0:
            timeout = None
        result = run_compliance_review(
            package_path=args.package_path,
            output_dir=args.output_dir,
            rule_pack_path=args.rule_pack,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            review_id=args.review_id,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            package_top_k=args.package_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=timeout,
            reuse_package_cache=args.reuse_package_cache,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "compliance-review-eval":
        timeout = args.docling_timeout_seconds
        if timeout is not None and timeout <= 0:
            timeout = None
        result = run_compliance_review_eval(
            output_dir=args.output_dir,
            eval_file=args.eval_file,
            rule_pack_path=args.rule_pack,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            package_top_k=args.package_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=timeout,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "compliance-gold-eval":
        timeout = args.docling_timeout_seconds
        if timeout is not None and timeout <= 0:
            timeout = None
        result = run_compliance_gold_eval(
            output_dir=args.output_dir,
            gold_file=args.gold_file,
            rule_pack_path=args.rule_pack,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            package_top_k=args.package_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=timeout,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "compliance-coverage":
        result = run_compliance_coverage(
            output_dir=args.output_dir,
            rule_pack_path=args.rule_pack,
            coverage_matrix_path=args.coverage_matrix,
            eval_file=args.eval_file,
            source_set_id=args.source_set_id,
            links_path=args.links_path,
            results_dir=args.results_dir,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["passed"] else 1

    if args.command == "preflight":
        config = load_config(args.config)
        result = run_preflight(
            workbook_path=args.workbook,
            output_dir=args.output_dir,
            config=config,
            run_id=args.run_id,
            sheet_filter=args.sheet,
            id_filter=args.id,
            host_filter=args.host,
            limit=args.limit,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0

    if args.command == "download":
        config = load_config(args.config)
        result = run_download(
            workbook_path=args.workbook,
            output_dir=args.output_dir,
            config=config,
            run_id=args.run_id,
            sheet_filter=args.sheet,
            id_filter=args.id,
            host_filter=args.host,
            limit=args.limit,
            force=args.force,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0

    if args.command == "report":
        result = build_run_report(output_dir=args.output_dir, run_id=args.run_id)
        if args.json:
            print(json.dumps(result.summary, indent=2, sort_keys=True))
        else:
            print(result.text)
        return 0

    if args.command == "validate-run":
        result = validate_run(output_dir=args.output_dir, run_id=args.run_id)
        print(json.dumps(result.report, indent=2, sort_keys=True))
        return 0 if result.passed else 1

    if args.command == "pilot-hosts":
        config = load_config(args.config)
        result = run_host_pilots(
            workbook_path=args.workbook,
            output_dir=args.output_dir,
            config=config,
            run_id_prefix=args.run_id_prefix,
            hosts=args.host,
            limit_per_host=args.limit_per_host,
            force=args.force,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["all_ready"] else 1

    if args.command == "batch-download":
        config = load_config(args.config)
        result = run_batch_downloads(
            workbook_path=args.workbook,
            output_dir=args.output_dir,
            config=config,
            run_id_prefix=args.run_id_prefix,
            hosts=args.host,
            batch_size=args.batch_size,
            limit_per_host=args.limit_per_host,
            force=args.force,
            plan_only=args.plan_only,
            resume=args.resume,
            continue_on_failure=args.continue_on_failure,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["all_passed"] or args.plan_only else 1

    if args.command == "catalog-build":
        if args.run_id and args.batch_run_id:
            parser.error("catalog-build accepts either --run-id or --batch-run-id, not both")
        config = load_config(args.config)
        result = build_review_catalog(
            workbook_path=args.workbook,
            output_dir=args.output_dir,
            config=config,
            config_path=args.config,
            run_id=args.run_id,
            batch_run_id=args.batch_run_id,
        )
        print(json.dumps(result.summary, indent=2, sort_keys=True))
        return 0 if result.summary["validation_passed"] else 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
