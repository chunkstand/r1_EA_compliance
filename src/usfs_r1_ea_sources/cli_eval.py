from __future__ import annotations

from pathlib import Path
import argparse

from .applicability import DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH
from .applicability_eval import DEFAULT_APPLICABILITY_EVAL_PATH
from .applicability_eval import DEFAULT_APPLICABILITY_GOLD_EVAL_PATH
from .applicability_eval import run_applicability_eval
from .applicability_eval import run_applicability_gold_eval
from .cli_common import print_summary
from .evidence_graph import run_phase_aligned_eval
from .gold_coverage_eval import DEFAULT_GOLD_COVERAGE_MANIFEST_PATH
from .gold_coverage_eval import run_gold_coverage_eval
from .real_package_review_coverage_eval import (
    DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
)
from .real_package_review_coverage_eval import run_real_package_review_coverage_eval
from .promotion_suite import DEFAULT_PROMOTION_SUITE_PATH
from .promotion_suite import run_promotion_suite
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .upstream_evaluation import DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH
from .upstream_evaluation import run_upstream_evaluation
from .v1_ea_eval import run_v1_ea_review_eval


EVAL_COMMANDS = {
    "applicability-eval",
    "applicability-gold-eval",
    "upstream-eval",
    "phase-eval",
    "v1-ea-eval",
    "real-package-review-coverage-eval",
    "gold-coverage-eval",
    "promotion-suite",
}


def register_eval_commands(subparsers: argparse._SubParsersAction) -> None:
    applicability_eval = subparsers.add_parser(
        "applicability-eval",
        help="Run deterministic applicability decision-quality eval cases.",
    )
    applicability_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    applicability_eval.add_argument("--source-set-id")
    applicability_eval.add_argument("--base-rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    applicability_eval.add_argument("--eval-file", default=DEFAULT_APPLICABILITY_EVAL_PATH, type=Path)
    applicability_eval.add_argument(
        "--authority-family-templates-path",
        default=DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
        type=Path,
    )
    applicability_eval.add_argument(
        "--no-authority-family-templates",
        action="store_const",
        const=None,
        dest="authority_family_templates_path",
    )
    applicability_eval.add_argument("--results-dir", type=Path)
    applicability_eval.add_argument("--top-k", type=int, default=5)

    applicability_gold_eval = subparsers.add_parser(
        "applicability-gold-eval",
        help="Run adjudicated applicability gold eval cases.",
    )
    applicability_gold_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    applicability_gold_eval.add_argument("--source-set-id")
    applicability_gold_eval.add_argument("--base-rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    applicability_gold_eval.add_argument(
        "--gold-file",
        default=DEFAULT_APPLICABILITY_GOLD_EVAL_PATH,
        type=Path,
    )
    applicability_gold_eval.add_argument(
        "--authority-family-templates-path",
        default=DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
        type=Path,
    )
    applicability_gold_eval.add_argument(
        "--no-authority-family-templates",
        action="store_const",
        const=None,
        dest="authority_family_templates_path",
    )
    applicability_gold_eval.add_argument("--results-dir", type=Path)
    applicability_gold_eval.add_argument("--top-k", type=int, default=5)

    upstream_eval = subparsers.add_parser(
        "upstream-eval",
        help="Run deterministic upstream direct-eval coverage fixtures.",
    )
    upstream_eval.add_argument("--manifest", default=DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH, type=Path)
    upstream_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    upstream_eval.add_argument("--results-dir", type=Path)

    phase_eval = subparsers.add_parser(
        "phase-eval",
        help="Run phase-aligned readiness evals across generated artifacts.",
    )
    phase_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    phase_eval.add_argument("--source-set-id")
    phase_eval.add_argument("--catalog-dir", type=Path)
    phase_eval.add_argument("--review-id")
    phase_eval.add_argument("--review-dir", type=Path)

    v1_ea_eval = subparsers.add_parser(
        "v1-ea-eval",
        help="Evaluate a real EA compliance review against the V1 source/section contract.",
    )
    v1_ea_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    v1_ea_eval.add_argument("--review-id")
    v1_ea_eval.add_argument("--review-dir", type=Path)
    v1_ea_eval.add_argument("--eval-file", type=Path)
    v1_ea_eval.add_argument(
        "--manifest",
        default=DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
        type=Path,
    )
    v1_ea_eval.add_argument("--output-path", type=Path)

    real_package_review_coverage_eval = subparsers.add_parser(
        "real-package-review-coverage-eval",
        help="Run the aggregate real-package review coverage gate across tracked review slots.",
    )
    real_package_review_coverage_eval.add_argument(
        "--output-dir",
        default=Path("source_library"),
        type=Path,
    )
    real_package_review_coverage_eval.add_argument(
        "--manifest",
        default=DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
        type=Path,
    )
    real_package_review_coverage_eval.add_argument("--results-dir", type=Path)

    gold_coverage_eval = subparsers.add_parser(
        "gold-coverage-eval",
        help="Run the aggregate gold coverage gate across adjudicated gold and real-review contracts.",
    )
    gold_coverage_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    gold_coverage_eval.add_argument(
        "--manifest",
        default=DEFAULT_GOLD_COVERAGE_MANIFEST_PATH,
        type=Path,
    )
    gold_coverage_eval.add_argument("--results-dir", type=Path)

    promotion_suite = subparsers.add_parser(
        "promotion-suite",
        help="Check manifest-declared promotion evidence and write an aggregate readiness report.",
    )
    promotion_suite.add_argument("--output-dir", default=Path("source_library"), type=Path)
    promotion_suite.add_argument("--manifest", default=DEFAULT_PROMOTION_SUITE_PATH, type=Path)
    promotion_suite.add_argument("--results-dir", type=Path)
    promotion_suite.add_argument(
        "--strict-expansion",
        action="store_true",
        help="Require expansion slots to be ready before returning promotion-ready.",
    )


def handle_eval_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
    if args.command == "applicability-eval":
        result = run_applicability_eval(
            output_dir=args.output_dir,
            eval_file=args.eval_file,
            base_rule_pack_path=args.base_rule_pack,
            authority_family_templates_path=args.authority_family_templates_path,
            source_set_id=args.source_set_id,
            results_dir=args.results_dir,
            top_k=args.top_k,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "applicability-gold-eval":
        result = run_applicability_gold_eval(
            output_dir=args.output_dir,
            gold_file=args.gold_file,
            base_rule_pack_path=args.base_rule_pack,
            authority_family_templates_path=args.authority_family_templates_path,
            source_set_id=args.source_set_id,
            results_dir=args.results_dir,
            top_k=args.top_k,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "upstream-eval":
        result = run_upstream_evaluation(
            manifest_path=args.manifest,
            output_dir=args.output_dir,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "phase-eval":
        result = run_phase_aligned_eval(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            catalog_dir=args.catalog_dir,
            review_id=args.review_id,
            review_dir=args.review_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "v1-ea-eval":
        result = run_v1_ea_review_eval(
            output_dir=args.output_dir,
            review_id=args.review_id,
            review_dir=args.review_dir,
            eval_file=args.eval_file,
            manifest_path=args.manifest,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "real-package-review-coverage-eval":
        result = run_real_package_review_coverage_eval(
            output_dir=args.output_dir,
            manifest_path=args.manifest,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "gold-coverage-eval":
        result = run_gold_coverage_eval(
            output_dir=args.output_dir,
            manifest_path=args.manifest,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "promotion-suite":
        result = run_promotion_suite(
            output_dir=args.output_dir,
            manifest_path=args.manifest,
            results_dir=args.results_dir,
            strict_expansion=args.strict_expansion,
        )
        print_summary(result.summary)
        return 0 if result.summary["promotion_ready"] else 1

    return None
