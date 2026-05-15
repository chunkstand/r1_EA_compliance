from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPO_ROOT / "docs" / "TECH_DEBT_REGISTER.md"
SCAN_ROOTS = (REPO_ROOT / "src", REPO_ROOT / "tests")
COMMENT_MARKER_PATTERNS = (
    re.compile(r"\b(TODO|FIXME|HACK|XXX)\b"),
    re.compile(r"pragma:\s*no cover"),
)
CODE_MARKER_PATTERNS = (
    re.compile(r"pytest\.mark\.xfail\b"),
    re.compile(r"pytest\.xfail\b"),
    re.compile(r"pytest\.mark\.skip(?:if)?\b"),
    re.compile(r"pytest\.skip\b"),
)


def test_debt_register_entries_are_structured() -> None:
    entries = _load_register()

    assert entries != []

    incomplete = []
    stale_paths = []
    stale_tokens = []
    for entry in entries:
        required_keys = {"status", "kind", "path", "token", "owner", "remove_by", "reason"}
        missing = sorted(required_keys - set(entry))
        if missing:
            incomplete.append({"id": entry["id"], "missing": missing})
            continue

        file_path, line_number = _split_entry_path(entry["path"])
        if not file_path.exists():
            stale_paths.append(entry["id"])
            continue

        if line_number is None:
            text = file_path.read_text()
            if entry["token"] not in text:
                stale_tokens.append(entry["id"])
            continue

        lines = file_path.read_text().splitlines()
        if line_number < 1 or line_number > len(lines):
            stale_paths.append(entry["id"])
            continue

        if entry["token"] not in lines[line_number - 1]:
            stale_tokens.append(entry["id"])

    assert incomplete == []
    assert stale_paths == []
    assert stale_tokens == []


def test_source_and_test_debt_markers_are_tracked() -> None:
    registered_paths = {entry["path"] for entry in _load_register() if entry.get("status") == "active"}
    untracked = []

    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            text = path.read_text()
            lines = text.splitlines()
            relative_path = path.relative_to(REPO_ROOT)
            for token in tokenize.generate_tokens(io.StringIO(text).readline):
                if token.type != tokenize.COMMENT:
                    continue
                for pattern in COMMENT_MARKER_PATTERNS:
                    match = pattern.search(token.string)
                    if match is None:
                        continue
                    register_path = f"{relative_path}:{token.start[0]}"
                    if register_path not in registered_paths:
                        untracked.append(
                            {
                                "path": register_path,
                                "token": match.group(0),
                            }
                        )
            for line_number, line in enumerate(lines, start=1):
                for pattern in CODE_MARKER_PATTERNS:
                    match = pattern.search(line)
                    if match is None:
                        continue
                    register_path = f"{relative_path}:{line_number}"
                    if register_path not in registered_paths:
                        untracked.append(
                            {
                                "path": register_path,
                                "token": match.group(0),
                            }
                        )

    assert untracked == []


def _load_register() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw_line in REGISTER_PATH.read_text().splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            if current is not None:
                entries.append(current)
            current = {"id": line[3:].strip()}
            continue
        if current is None or not line.startswith("- "):
            continue
        key, value = line[2:].split(":", 1)
        current[key.strip()] = value.strip().strip("`")

    if current is not None:
        entries.append(current)

    return entries


def _split_entry_path(entry_path: str) -> tuple[Path, int | None]:
    raw_path, separator, raw_line = entry_path.rpartition(":")
    if separator == "" or not raw_line.isdigit():
        return REPO_ROOT / entry_path, None
    return REPO_ROOT / raw_path, int(raw_line)
