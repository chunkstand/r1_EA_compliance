from __future__ import annotations

import argparse
from collections.abc import Callable

from .cli_applicability import handle_applicability_command
from .cli_applicability import register_applicability_commands
from .cli_capture import handle_capture_command
from .cli_capture import register_capture_commands
from .cli_compliance import handle_compliance_command
from .cli_compliance import register_compliance_commands
from .cli_derived import handle_derived_command
from .cli_derived import register_derived_commands
from .cli_decision_support import handle_decision_support_command
from .cli_decision_support import register_decision_support_commands
from .cli_eval import handle_eval_command
from .cli_eval import register_eval_commands
from .cli_final_qa import handle_final_qa_command
from .cli_final_qa import register_final_qa_commands
from .cli_project_planning import handle_project_planning_command
from .cli_project_planning import register_project_planning_commands
from .cli_review import handle_review_command
from .cli_review import register_review_commands
from .cli_review_packet import handle_review_packet_command
from .cli_review_packet import register_review_packet_commands


CommandHandler = Callable[[argparse.Namespace, argparse.ArgumentParser], int | None]
COMMAND_HANDLERS: tuple[CommandHandler, ...] = (
    handle_capture_command,
    handle_derived_command,
    handle_applicability_command,
    handle_eval_command,
    handle_review_command,
    handle_compliance_command,
    handle_decision_support_command,
    handle_final_qa_command,
    handle_project_planning_command,
    handle_review_packet_command,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usfs-r1-ea-sources",
        description="USFS Region 1 EA source-library tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_capture_commands(subparsers)
    register_derived_commands(subparsers)
    register_applicability_commands(subparsers)
    register_eval_commands(subparsers)
    register_review_commands(subparsers)
    register_compliance_commands(subparsers)
    register_decision_support_commands(subparsers)
    register_final_qa_commands(subparsers)
    register_project_planning_commands(subparsers)
    register_review_packet_commands(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    for handler in COMMAND_HANDLERS:
        result = handler(args, parser)
        if result is not None:
            return result

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
