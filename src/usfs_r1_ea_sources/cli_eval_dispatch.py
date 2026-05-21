from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import argparse


@dataclass(frozen=True)
class EvalCommandHandler:
    run: Callable[[argparse.Namespace], object]
    success_key: str


def dispatch_eval_command(
    args: argparse.Namespace,
    handlers: dict[str, EvalCommandHandler],
    print_summary: Callable[[dict], None],
) -> int | None:
    handler = handlers.get(args.command)
    if handler is None:
        return None

    result = handler.run(args)
    print_summary(result.summary)
    return 0 if result.summary[handler.success_key] else 1
