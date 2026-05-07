from __future__ import annotations

from pathlib import Path
import argparse

from .cli_common import print_summary
from .project_sow_package import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package import run_project_sow_package


PROJECT_PLANNING_COMMANDS = {"project-sow-package"}


def register_project_planning_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    package = subparsers.add_parser(
        "project-sow-package",
        help="Generate a proposed-action NEPA resource SOW requirements package.",
    )
    package.add_argument("--intake", required=True, type=Path)
    package.add_argument("--output-dir", default=Path("source_library"), type=Path)
    package.add_argument("--project-id")
    package.add_argument("--source-set-id")
    package.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    package.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )
    package.add_argument("--results-dir", type=Path)


def handle_project_planning_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    if args.command == "project-sow-package":
        result = run_project_sow_package(
            intake_path=args.intake,
            output_dir=args.output_dir,
            project_id=args.project_id,
            source_set_id=args.source_set_id,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None
