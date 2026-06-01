from __future__ import annotations

from pathlib import Path
import json

from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.observability_events import (
    OBSERVABILITY_EVENT_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.observability_events import (
    OBSERVABILITY_EVENT_LOG_ENV,
)


def test_cli_main_captures_redacted_command_lifecycle_events(
    tmp_path: Path,
    monkeypatch,
) -> None:
    event_log_path = tmp_path / "command_events.jsonl"
    monkeypatch.setenv(OBSERVABILITY_EVENT_LOG_ENV, str(event_log_path))

    result = main(
        [
            "eval-context-graph-build",
            "--sqlite-path",
            str(tmp_path / "missing.sqlite"),
            "--graph-json-path",
            str(tmp_path / "graph.json"),
            "--no-observability-event-log",
        ]
    )

    assert result == 1
    rows = _read_jsonl(event_log_path)
    assert [row["command_event_phase"] for row in rows] == ["started", "finished"]
    assert {row["schema_version"] for row in rows} == {
        OBSERVABILITY_EVENT_SCHEMA_VERSION
    }
    assert {row["command"] for row in rows} == {"eval-context-graph-build"}
    assert rows[0]["event_name"] == "cli.command.started"
    assert rows[1]["event_name"] == "cli.command.finished"
    assert rows[1]["exit_code"] == 1
    assert rows[1]["severity"] == "ERROR"
    assert rows[0]["argv_sha256"]
    assert "sqlite_path" in rows[0]["argument_keys"]
    assert rows[0]["sqlite_path"].endswith("missing.sqlite")
    assert "argv" not in rows[0]
    assert "body" not in rows[0]


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
