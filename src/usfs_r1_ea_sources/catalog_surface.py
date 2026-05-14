from __future__ import annotations

from contextlib import closing
from pathlib import Path
import json
import sqlite3


ARCHIVED_CATALOG_DIR_NAMES = {"catalog_gate", "merged_catalog_gate"}


def resolve_catalog_dir_for_source_set(
    *,
    output_dir: Path,
    source_set_id: str | None,
    catalog_dir: Path | None = None,
) -> Path:
    output_dir = Path(output_dir)
    if catalog_dir is not None:
        return Path(catalog_dir)
    active_catalog_dir = output_dir / "catalog"
    if source_set_id is None:
        return active_catalog_dir
    active_source_set_id = catalog_source_set_id(active_catalog_dir)
    compatible_source_record_ids = selected_source_record_ids_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    if (
        not active_source_set_id
        or active_source_set_id == source_set_id
        or (
            compatible_source_record_ids is not None
            and catalog_source_record_ids(active_catalog_dir) == compatible_source_record_ids
        )
    ):
        return active_catalog_dir
    archived_catalog_dir = find_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
        compatible_source_record_ids=compatible_source_record_ids,
    )
    return archived_catalog_dir or active_catalog_dir


def find_catalog_dir_for_source_set(
    *,
    output_dir: Path,
    source_set_id: str,
    compatible_source_record_ids: set[str] | None = None,
) -> Path | None:
    runs_dir = Path(output_dir) / "runs"
    if not runs_dir.exists():
        return None
    exact_candidates: list[tuple[float, Path]] = []
    compatible_candidates: list[tuple[float, Path]] = []
    for manifest_path in runs_dir.rglob("source_set_manifest.json"):
        catalog_dir = manifest_path.parent
        if catalog_dir.name not in ARCHIVED_CATALOG_DIR_NAMES:
            continue
        candidate_source_set_id = catalog_source_set_id(catalog_dir)
        candidate = (manifest_path.stat().st_mtime, catalog_dir)
        if candidate_source_set_id == source_set_id:
            exact_candidates.append(candidate)
            continue
        if (
            compatible_source_record_ids is not None
            and catalog_source_record_ids(catalog_dir) == compatible_source_record_ids
        ):
            compatible_candidates.append(candidate)
    if exact_candidates:
        exact_candidates.sort(key=lambda item: (item[0], str(item[1])))
        return exact_candidates[-1][1]
    if compatible_candidates:
        compatible_candidates.sort(key=lambda item: (item[0], str(item[1])))
        return compatible_candidates[-1][1]
    return None


def catalog_source_set_id(catalog_dir: Path) -> str | None:
    catalog_dir = Path(catalog_dir)
    manifest_path = catalog_dir / "source_set_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
        source_set_id = manifest.get("source_set_id")
        if source_set_id:
            return str(source_set_id)
    sqlite_path = catalog_dir / "review_sources.sqlite"
    if not sqlite_path.exists():
        return None
    try:
        with closing(sqlite3.connect(sqlite_path)) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "source_sets" in tables:
                values = [
                    str(row[0])
                    for row in connection.execute(
                        "SELECT DISTINCT source_set_id FROM source_sets ORDER BY source_set_id"
                    )
                    if row[0]
                ]
                if len(values) == 1:
                    return values[0]
            if "sources" in tables:
                columns = {
                    str(row[1])
                    for row in connection.execute("PRAGMA table_info(sources)")
                }
                if "source_set_id" in columns:
                    values = [
                        str(row[0])
                        for row in connection.execute(
                            "SELECT DISTINCT source_set_id FROM sources ORDER BY source_set_id"
                        )
                        if row[0]
                    ]
                    if len(values) == 1:
                        return values[0]
    except sqlite3.Error:
        return None
    return None


def catalog_source_record_ids(catalog_dir: Path) -> set[str] | None:
    sqlite_path = Path(catalog_dir) / "review_sources.sqlite"
    if not sqlite_path.exists():
        return None
    try:
        with closing(sqlite3.connect(sqlite_path)) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "sources" not in tables:
                return None
            return {
                str(row[0])
                for row in connection.execute("SELECT source_record_id FROM sources")
                if row[0]
            }
    except sqlite3.Error:
        return None


def selected_source_record_ids_for_source_set(
    *,
    output_dir: Path,
    source_set_id: str,
) -> set[str] | None:
    manifest_path = (
        Path(output_dir)
        / "derived"
        / source_set_id
        / "diagnostics"
        / "extraction_manifest.jsonl"
    )
    if not manifest_path.exists():
        return None
    source_record_ids: set[str] = set()
    try:
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            source_record_id = record.get("source_record_id")
            if source_record_id:
                source_record_ids.add(str(source_record_id))
    except (OSError, json.JSONDecodeError):
        return None
    return source_record_ids or None
