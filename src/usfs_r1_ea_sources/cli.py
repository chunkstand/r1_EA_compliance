from __future__ import annotations

from pathlib import Path
import argparse
import json

from .config import DEFAULT_CONFIG_PATH, load_config
from .download import run_download
from .dry_run import run_dry_run
from .preflight import run_preflight


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
        return 0

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

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
