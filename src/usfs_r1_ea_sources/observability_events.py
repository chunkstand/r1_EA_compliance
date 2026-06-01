from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import time
import uuid


OBSERVABILITY_EVENT_SCHEMA_VERSION = "usfs-r1-observability-event-v1"
DEFAULT_OBSERVABILITY_EVENT_LOG_PATH = Path(
    "source_library/evaluations/observability_events/command_events.jsonl"
)
OBSERVABILITY_EVENT_LOG_ENV = "USFS_R1_OBSERVABILITY_EVENT_LOG"
OBSERVABILITY_EVENTS_DISABLED_ENV = "USFS_R1_OBSERVABILITY_EVENTS_DISABLED"
COMMAND_CONTEXT_KEYS = {
    "case_id",
    "command",
    "contract_path",
    "eval_file",
    "event_log_path",
    "graph_json_path",
    "inventory_path",
    "output_dir",
    "results_dir",
    "review_id",
    "run_id",
    "source_set_id",
    "span_id",
    "sqlite_path",
    "summary_path",
    "trace_id",
}


@dataclass(frozen=True)
class CommandObservation:
    command: str
    command_invocation_id: str
    event_log_path: Path
    started_monotonic: float
    argv_sha256: str
    argument_keys: list[str]
    context: dict[str, Any]


def resolve_observability_event_log_path(
    *,
    repo_root: Path | None = None,
    explicit_path: Path | None = None,
    honor_disabled: bool = True,
) -> Path | None:
    if honor_disabled and _truthy(os.environ.get(OBSERVABILITY_EVENTS_DISABLED_ENV)):
        return None
    root = (repo_root or Path.cwd()).resolve()
    env_path = os.environ.get(OBSERVABILITY_EVENT_LOG_ENV)
    path = explicit_path or (Path(env_path) if env_path else DEFAULT_OBSERVABILITY_EVENT_LOG_PATH)
    return path if path.is_absolute() else root / path


def start_command_observation(
    *,
    args: Namespace,
    argv: list[str],
    repo_root: Path | None = None,
) -> CommandObservation | None:
    event_log_path = resolve_observability_event_log_path(repo_root=repo_root)
    if event_log_path is None:
        return None
    payload = vars(args)
    command = str(payload.get("command") or "unknown")
    observation = CommandObservation(
        command=command,
        command_invocation_id=str(uuid.uuid4()),
        event_log_path=event_log_path,
        started_monotonic=time.monotonic(),
        argv_sha256=_stable_hash(argv),
        argument_keys=sorted(payload),
        context=_command_context(payload),
    )
    write_observability_event(
        event_log_path,
        _command_event(observation, phase="started", exit_code=None),
    )
    return observation


def finish_command_observation(
    observation: CommandObservation | None,
    *,
    exit_code: int,
    error_type: str | None = None,
) -> None:
    if observation is None:
        return
    duration_ms = round((time.monotonic() - observation.started_monotonic) * 1000, 3)
    write_observability_event(
        observation.event_log_path,
        _command_event(
            observation,
            phase="finished",
            exit_code=exit_code,
            duration_ms=duration_ms,
            error_type=error_type,
        ),
    )


def write_observability_event(path: Path, event: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError:
        return


def _command_event(
    observation: CommandObservation,
    *,
    phase: str,
    exit_code: int | None,
    duration_ms: float | None = None,
    error_type: str | None = None,
) -> dict[str, Any]:
    event = {
        "schema_version": OBSERVABILITY_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "event_name": f"cli.command.{phase}",
        "event_timestamp": _utc_now(),
        "severity": _severity(phase=phase, exit_code=exit_code),
        "command": observation.command,
        "command_event_phase": phase,
        "command_invocation_id": observation.command_invocation_id,
        "argv_sha256": observation.argv_sha256,
        "argument_keys": observation.argument_keys,
        **observation.context,
    }
    if exit_code is not None:
        event["exit_code"] = exit_code
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    if error_type:
        event["error_type"] = error_type
    return event


def _command_context(payload: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in sorted(COMMAND_CONTEXT_KEYS):
        value = payload.get(key)
        normalized = _normalize_context_value(value)
        if normalized not in (None, "", []):
            context[key] = normalized
    return context


def _normalize_context_value(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [
            normalized
            for item in value
            if (normalized := _normalize_context_value(item)) not in (None, "", [])
        ]
    if isinstance(value, tuple):
        return [
            normalized
            for item in value
            if (normalized := _normalize_context_value(item)) not in (None, "", [])
        ]
    if isinstance(value, (str, int, float, bool)):
        return value
    return None


def _severity(*, phase: str, exit_code: int | None) -> str:
    if phase == "started" or exit_code == 0:
        return "INFO"
    return "ERROR"


def _stable_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _truthy(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes", "on"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
