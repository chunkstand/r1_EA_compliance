from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import argparse


@dataclass(frozen=True)
class DerivedCommandHandler:
    run: Callable[[argparse.Namespace], object]
    summary_getter: Callable[[object], dict]
    success: Callable[[dict], bool]


def dispatch_derived_command(
    args: argparse.Namespace,
    handlers: dict[str, DerivedCommandHandler],
    print_summary: Callable[[dict], None],
) -> int | None:
    handler = handlers.get(args.command)
    if handler is None:
        return None

    result = handler.run(args)
    summary = handler.summary_getter(result)
    print_summary(summary)
    return 0 if handler.success(summary) else 1
