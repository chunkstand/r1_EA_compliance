from __future__ import annotations

from pathlib import Path
import argparse
import json

from .config import DEFAULT_CONFIG_PATH, load_config
from .dry_run import run_dry_run


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

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
