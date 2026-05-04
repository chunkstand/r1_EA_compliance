from __future__ import annotations

from pathlib import Path
import argparse

from .cli_common import normalized_timeout
from .cli_common import print_summary
from .compliance_coverage import DEFAULT_COVERAGE_MATRIX_PATH
from .compliance_coverage import run_compliance_coverage
from .compliance_gold_eval import DEFAULT_COMPLIANCE_GOLD_EVAL_PATH
from .compliance_gold_eval import run_compliance_gold_eval
from .compliance_review import DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH
from .compliance_review import run_compliance_review
from .compliance_review import run_compliance_review_eval
from .rule_packs import DEFAULT_RULE_PACK_PATH


COMPLIANCE_COMMANDS = {
    "compliance-review",
    "compliance-review-eval",
    "compliance-gold-eval",
    "compliance-coverage",
}


def register_compliance_commands(subparsers: argparse._SubParsersAction) -> None:
    review = subparsers.add_parser(
        "compliance-review",
        help="Run a versioned compliance rule pack against a local EA package.",
    )
    review.add_argument("--package-path", required=True, type=Path)
    _add_compliance_review_args(review)
    review.add_argument("--review-id")
    review.add_argument("--results-dir", type=Path)
    review.add_argument("--reuse-package-cache", action="store_true")
    review.add_argument("--allow-base-rule-pack-review", action="store_true")

    review_eval = subparsers.add_parser(
        "compliance-review-eval",
        help="Run deterministic eval cases against compliance-review findings.",
    )
    _add_compliance_review_args(review_eval)
    review_eval.add_argument("--eval-file", default=DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH, type=Path)
    review_eval.add_argument("--results-dir", type=Path)

    gold_eval = subparsers.add_parser(
        "compliance-gold-eval",
        help="Run adjudicated gold package fixtures through the compliance-review gate.",
    )
    _add_compliance_review_args(gold_eval)
    gold_eval.add_argument("--gold-file", default=DEFAULT_COMPLIANCE_GOLD_EVAL_PATH, type=Path)
    gold_eval.add_argument("--results-dir", type=Path)

    coverage = subparsers.add_parser(
        "compliance-coverage",
        help="Validate rule-pack coverage across matrix, source-claim links, terms, and eval cases.",
    )
    coverage.add_argument("--output-dir", default=Path("source_library"), type=Path)
    coverage.add_argument("--source-set-id")
    coverage.add_argument("--links-path", type=Path)
    coverage.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    coverage.add_argument("--coverage-matrix", default=DEFAULT_COVERAGE_MATRIX_PATH, type=Path)
    coverage.add_argument("--eval-file", default=DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH, type=Path)
    coverage.add_argument("--results-dir", type=Path)


def handle_compliance_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    if args.command == "compliance-review":
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
            docling_timeout_seconds=normalized_timeout(args.docling_timeout_seconds),
            reuse_package_cache=args.reuse_package_cache,
            allow_base_rule_pack_review=args.allow_base_rule_pack_review,
        )
        print_summary(result.summary)
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "compliance-review-eval":
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
            docling_timeout_seconds=normalized_timeout(args.docling_timeout_seconds),
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "compliance-gold-eval":
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
            docling_timeout_seconds=normalized_timeout(args.docling_timeout_seconds),
        )
        print_summary(result.summary)
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
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None


def _add_compliance_review_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", default=Path("source_library"), type=Path)
    parser.add_argument("--source-set-id")
    parser.add_argument("--index-path", type=Path)
    parser.add_argument("--rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    parser.add_argument("--source-top-k", type=int, default=3)
    parser.add_argument("--package-top-k", type=int, default=3)
    parser.add_argument("--chunk-max-chars", type=int, default=1800)
    parser.add_argument("--chunk-overlap-chars", type=int, default=200)
    parser.add_argument("--docling-ocr", action="store_true")
    parser.add_argument("--docling-timeout-seconds", type=float, default=120.0)
