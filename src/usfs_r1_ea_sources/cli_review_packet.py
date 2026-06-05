from __future__ import annotations

import argparse
from pathlib import Path

from .cli_common import print_summary
from .review_packet_index import run_review_packet_direct_eval
from .review_packet_index import run_review_packet_index


REVIEW_PACKET_COMMANDS = {"review-packet-index", "review-packet-direct-eval"}


def register_review_packet_commands(subparsers: argparse._SubParsersAction) -> None:
    packet = subparsers.add_parser(
        "review-packet-index",
        help="Build the review-packet row inventory, render manifest, and signer-facing index.",
    )
    packet.add_argument("--output-dir", default=Path("source_library"), type=Path)
    packet.add_argument("--review-id", required=True)
    packet.add_argument("--results-dir", type=Path)
    direct_eval = subparsers.add_parser(
        "review-packet-direct-eval",
        help="Score generated review-packet artifacts as a deterministic direct-eval result.",
    )
    direct_eval.add_argument("--output-dir", default=Path("source_library"), type=Path)
    direct_eval.add_argument("--review-id", required=True)
    direct_eval.add_argument("--results-dir", type=Path)


def handle_review_packet_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    if args.command == "review-packet-index":
        result = run_review_packet_index(
            output_dir=args.output_dir,
            review_id=args.review_id,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1
    if args.command == "review-packet-direct-eval":
        result = run_review_packet_direct_eval(
            output_dir=args.output_dir,
            review_id=args.review_id,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1
    return None
