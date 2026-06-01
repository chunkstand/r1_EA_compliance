from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json


EVENT_SCHEMA_VERSION = "eval-context-graph-event-source-v1"
EVENT_FILENAME_MARKERS = ("event", "events", "log", "logs", "trace")
EVENT_ID_FIELDS = (
    "event_id",
    "span_event_id",
    "log_event_id",
    "retrieval_trace_id",
    "graph_path_id",
    "trace_id",
)
TIMESTAMP_FIELDS = ("timestamp", "event_timestamp", "query_timestamp", "created_at")
SEVERITY_FIELDS = ("severity_text", "severity", "level", "log_level")


@dataclass(frozen=True)
class ContextGraphEventBatch:
    events: list[dict[str, Any]]
    summary: dict[str, Any] | None


def context_graph_events_for_artifact(
    artifact_ref: str | None,
    *,
    repo_root: Path,
) -> ContextGraphEventBatch:
    path = _artifact_path(artifact_ref, repo_root)
    if path is None or not _looks_like_event_artifact(path):
        return ContextGraphEventBatch(events=[], summary=None)
    rows, parse_error_count = _read_event_rows(path)
    events = [
        _event_from_row(row=row, artifact_ref=str(artifact_ref), line_number=index)
        for index, row in enumerate(rows, start=1)
    ]
    return ContextGraphEventBatch(
        events=events,
        summary={
            "schema_version": EVENT_SCHEMA_VERSION,
            "artifact_ref": str(artifact_ref),
            "path": _display_path(path, repo_root),
            "row_count": len(rows),
            "materialized_event_count": len(events),
            "parse_error_count": parse_error_count,
            "event_kinds": sorted({event["kind"] for event in events}),
        },
    )


def _event_from_row(
    *,
    row: dict[str, Any],
    artifact_ref: str,
    line_number: int,
) -> dict[str, Any]:
    payload_hash = _stable_hash(row)
    event_kind = _event_kind(row)
    event_id = _first_string(row, EVENT_ID_FIELDS) or payload_hash[:24]
    return {
        "kind": event_kind,
        "stable_ref": f"{event_kind}:{artifact_ref}:{line_number}:{event_id}",
        "source_hash": payload_hash,
        "properties": {
            "schema_version": row.get("schema_version"),
            "artifact_ref": artifact_ref,
            "line_number": line_number,
            "event_id": event_id,
            "event_name": _event_name(row),
            "event_timestamp": _first_string(row, TIMESTAMP_FIELDS),
            "severity": _first_string(row, SEVERITY_FIELDS),
            "payload_sha256": payload_hash,
            "payload_keys": sorted(row),
            "trace_kind": row.get("trace_kind"),
            "trace_id": row.get("trace_id"),
            "span_id": row.get("span_id"),
            "retrieval_trace_id": row.get("retrieval_trace_id"),
            "graph_path_id": row.get("graph_path_id"),
            "review_id": row.get("review_id"),
            "source_set_id": row.get("source_set_id"),
            "candidate_authority_id": row.get("candidate_authority_id"),
            "query_type": row.get("query_type"),
            "selected_status": row.get("selected_status"),
            "diagnostic_count": len(_list_of_dicts(row.get("diagnostics"))),
            "ranked_result_count": len(_list_of_dicts(row.get("ranked_results"))),
        },
    }


def _read_event_rows(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    parse_error_count = 0
    if path.suffix == ".jsonl":
        try:
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        parse_error_count += 1
                        continue
                    if isinstance(payload, dict):
                        rows.append(payload)
        except (OSError, UnicodeDecodeError):
            parse_error_count += 1
        return rows, parse_error_count
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return [], 1
    if isinstance(payload, dict):
        rows.extend(_list_of_dicts(payload.get("events")))
    elif isinstance(payload, list):
        rows.extend(_list_of_dicts(payload))
    return rows, parse_error_count


def _event_kind(row: dict[str, Any]) -> str:
    if any(row.get(field) for field in SEVERITY_FIELDS) or row.get("body") is not None:
        return "log_event"
    return "span_event"


def _event_name(row: dict[str, Any]) -> str:
    if isinstance(row.get("event_name"), str) and row["event_name"]:
        return row["event_name"]
    if isinstance(row.get("name"), str) and row["name"]:
        return row["name"]
    if isinstance(row.get("query_type"), str) and row["query_type"]:
        return f"query:{row['query_type']}"
    if isinstance(row.get("trace_kind"), str) and row["trace_kind"]:
        return row["trace_kind"]
    return "structured_event"


def _artifact_path(artifact_ref: str | None, repo_root: Path) -> Path | None:
    if not artifact_ref:
        return None
    path = Path(artifact_ref)
    return path if path.is_absolute() else repo_root / path


def _looks_like_event_artifact(path: Path) -> bool:
    if path.suffix not in {".json", ".jsonl"}:
        return False
    tokens = {
        token
        for token in path.stem.lower().replace("-", "_").split("_")
        if token
    }
    return bool(tokens.intersection(EVENT_FILENAME_MARKERS))


def _first_string(row: dict[str, Any], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        value = row.get(field)
        if isinstance(value, str) and value:
            return value
    return None


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _stable_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)
