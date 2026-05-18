from __future__ import annotations

from pathlib import Path
import argparse

from .cli_common import print_summary
from .draft_generation import DEFAULT_CONFIG_PATH as DEFAULT_DRAFT_GENERATION_CONFIG_PATH
from .draft_generation import run_draft_generate
from .ea_consistency_decision_support import DEFAULT_CONFIG_PATH
from .ea_consistency_decision_support import DEFAULT_EXPECTED_SUMMARY_PATH
from .ea_consistency_decision_support import run_ea_consistency_decision_support
from .ea_consistency_decision_support import validate_ea_consistency_decision_support_report


DECISION_SUPPORT_COMMANDS = {"draft-generate", "ea-consistency-document"}


def register_decision_support_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    document = subparsers.add_parser(
        "ea-consistency-document",
        help="Generate an EA consistency decision-support report from audited review artifacts.",
    )
    document.add_argument("--output-dir", default=Path("source_library"), type=Path)
    document.add_argument("--review-id")
    document.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    document.add_argument(
        "--expected-summary",
        default=DEFAULT_EXPECTED_SUMMARY_PATH,
        type=Path,
    )
    document.add_argument("--results-dir", type=Path)
    document.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the existing generated report family without rewriting it.",
    )

    draft_generate = subparsers.add_parser(
        "draft-generate",
        help="Generate an evidence-backed draft-document packet from reviewed artifacts.",
    )
    draft_generate.add_argument("--output-dir", default=Path("source_library"), type=Path)
    draft_generate.add_argument("--review-id")
    draft_generate.add_argument("--config", default=DEFAULT_DRAFT_GENERATION_CONFIG_PATH, type=Path)
    draft_generate.add_argument("--results-dir", type=Path)


def handle_decision_support_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    if args.command == "ea-consistency-document":
        if args.validate_only:
            result = validate_ea_consistency_decision_support_report(
                output_dir=args.output_dir,
                review_id=args.review_id,
                config_path=args.config,
                expected_summary_path=args.expected_summary,
                results_dir=args.results_dir,
            )
            print_summary(result.summary)
            return 0 if result.summary["passed"] else 1
        result = run_ea_consistency_decision_support(
            output_dir=args.output_dir,
            review_id=args.review_id,
            config_path=args.config,
            expected_summary_path=args.expected_summary,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "draft-generate":
        result = run_draft_generate(
            output_dir=args.output_dir,
            review_id=args.review_id,
            config_path=args.config,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None
