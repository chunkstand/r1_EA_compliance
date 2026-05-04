from __future__ import annotations

from pathlib import Path
import argparse
import json

from .catalog import build_review_catalog
from .cli_common import print_summary
from .config import DEFAULT_CONFIG_PATH, load_config
from .download import run_download
from .dry_run import run_dry_run
from .batches import run_batch_downloads
from .pilots import run_host_pilots
from .preflight import run_preflight
from .report import build_run_report
from .validate_run import validate_run


CAPTURE_COMMANDS = {
    "dry-run",
    "preflight",
    "download",
    "report",
    "validate-run",
    "pilot-hosts",
    "batch-download",
    "catalog-build",
}


def register_capture_commands(subparsers: argparse._SubParsersAction) -> None:
    dry_run = subparsers.add_parser(
        "dry-run",
        help="Parse workbook and write manifest/report outputs without network downloads.",
    )
    _add_workbook_run_filters(dry_run)

    preflight = subparsers.add_parser(
        "preflight",
        help="Check planned source URLs and write preflight reports without saving artifacts.",
    )
    _add_workbook_run_filters(preflight)

    download = subparsers.add_parser(
        "download",
        help="Download validated source URLs, save immutable raw artifacts, and write reports.",
    )
    _add_workbook_run_filters(download)
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
    batches.add_argument("--host", action="append", help="Host to batch. Repeat for multiple hosts.")
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
    catalog.add_argument("--run-id", help="Optional download run ID to link artifacts.")
    catalog.add_argument(
        "--batch-run-id",
        help="Optional parent batch-download run ID to link artifacts from all passed child batches.",
    )


def handle_capture_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
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
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

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
        print_summary(result.summary)
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
        print_summary(result.summary)
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
        print_summary(result.summary)
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
        print_summary(result.summary)
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
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    return None


def _add_workbook_run_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("source_library"), type=Path)
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--sheet")
    parser.add_argument("--id")
    parser.add_argument("--host")
    parser.add_argument("--limit", type=int)
