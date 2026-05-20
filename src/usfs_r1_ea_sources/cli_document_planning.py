from __future__ import annotations

import argparse
from pathlib import Path

from .cli_common import print_summary
from .document_plan import DEFAULT_LANE_REGISTRY_PATH
from .document_plan import DEFAULT_REQUEST_SCHEMA_PATH
from .document_plan import run_document_plan


DOCUMENT_PLANNING_COMMANDS = {"document-plan"}


def register_document_planning_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    planner = subparsers.add_parser(
        "document-plan",
        help="Dry-run a normalized document request into an existing supported document lane or fail closed.",
    )
    planner.add_argument("--request", required=True, type=Path)
    planner.add_argument("--output-dir", default=Path("source_library"), type=Path)
    planner.add_argument("--results-dir", type=Path)
    planner.add_argument("--lane-registry", default=DEFAULT_LANE_REGISTRY_PATH, type=Path)
    planner.add_argument("--request-schema", default=DEFAULT_REQUEST_SCHEMA_PATH, type=Path)


def handle_document_planning_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    del parser
    if args.command == "document-plan":
        result = run_document_plan(
            request_path=args.request,
            output_dir=args.output_dir,
            lane_registry_path=args.lane_registry,
            request_schema_path=args.request_schema,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None
