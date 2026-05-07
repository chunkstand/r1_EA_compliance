from __future__ import annotations

from pathlib import Path
import argparse

from .cli_common import print_summary
from .final_qa_certification import DEFAULT_CONFIG_PATH
from .final_qa_certification import DEFAULT_EXPECTED_SUMMARY_PATH
from .final_qa_certification import run_final_qa_certification
from .final_qa_certification import validate_final_qa_certification_report


FINAL_QA_COMMANDS = {"final-qa-certification"}


def register_final_qa_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    certification = subparsers.add_parser(
        "final-qa-certification",
        help="Generate or validate the East Crazies final QA certification packet.",
    )
    certification.add_argument("--output-dir", default=Path("source_library"), type=Path)
    certification.add_argument("--review-id")
    certification.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    certification.add_argument(
        "--expected-summary",
        default=DEFAULT_EXPECTED_SUMMARY_PATH,
        type=Path,
    )
    certification.add_argument("--results-dir", type=Path)
    certification.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the existing generated final QA packet without rewriting it.",
    )


def handle_final_qa_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    del parser
    if args.command == "final-qa-certification":
        if args.validate_only:
            result = validate_final_qa_certification_report(
                output_dir=args.output_dir,
                review_id=args.review_id,
                config_path=args.config,
                expected_summary_path=args.expected_summary,
                results_dir=args.results_dir,
            )
            print_summary(result.summary)
            return 0 if result.summary["passed"] else 1
        result = run_final_qa_certification(
            output_dir=args.output_dir,
            review_id=args.review_id,
            config_path=args.config,
            expected_summary_path=args.expected_summary,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None
