from __future__ import annotations

from dataclasses import dataclass
import argparse


@dataclass(frozen=True)
class EvalArgumentSpec:
    flags: tuple[str, ...]
    kwargs: dict[str, object]


@dataclass(frozen=True)
class EvalCommandSpec:
    name: str
    help: str
    arguments: tuple[EvalArgumentSpec, ...]


def register_eval_command_specs(
    subparsers: argparse._SubParsersAction,
    command_specs: tuple[EvalCommandSpec, ...],
) -> None:
    for command_spec in command_specs:
        parser = subparsers.add_parser(command_spec.name, help=command_spec.help)
        for argument_spec in command_spec.arguments:
            parser.add_argument(*argument_spec.flags, **argument_spec.kwargs)
