from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re


DEFAULT_REPLAY_CONTEXT_DIR = Path("config/replay_contexts")
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class ReplayContextError(ValueError):
    """Raised when tracked replay context is missing or invalid."""


class ReplayContextMismatchError(ReplayContextError):
    """Raised when explicit replay overrides conflict with tracked context."""


@dataclass(frozen=True)
class ReplayContext:
    config_path: Path
    review_id: str
    source_set_id: str
    catalog_dir: Path
    resolved_catalog_dir: Path
    package_path: Path | None = None
    resolved_package_path: Path | None = None

    @property
    def source_catalog_path(self) -> Path:
        return self.catalog_dir / "source_catalog.jsonl"

    @property
    def resolved_source_catalog_path(self) -> Path:
        return self.resolved_catalog_dir / "source_catalog.jsonl"

    @property
    def source_set_manifest_path(self) -> Path:
        return self.catalog_dir / "source_set_manifest.json"

    @property
    def resolved_source_set_manifest_path(self) -> Path:
        return self.resolved_catalog_dir / "source_set_manifest.json"

    @property
    def catalog_sqlite_path(self) -> Path:
        return self.catalog_dir / "review_sources.sqlite"

    @property
    def resolved_catalog_sqlite_path(self) -> Path:
        return self.resolved_catalog_dir / "review_sources.sqlite"


def tracked_replay_context_path(output_dir: Path, review_id: str) -> Path:
    if not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ReplayContextError(
            "review_id must contain only letters, numbers, dot, underscore, or hyphen."
        )
    output_dir = Path(output_dir)
    return output_dir.parent / DEFAULT_REPLAY_CONTEXT_DIR / f"{review_id}.json"


def load_replay_context(config_path: Path) -> ReplayContext:
    config_path = Path(config_path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    review_id = str(payload.get("review_id") or "")
    source_set_id = str(payload.get("source_set_id") or "")
    catalog_dir = payload.get("catalog_dir")
    package_path = payload.get("package_path")

    if not review_id:
        raise ReplayContextError(f"{config_path}: replay context requires non-empty review_id")
    if not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ReplayContextError(
            f"{config_path}: review_id must contain only letters, numbers, dot, underscore, or hyphen."
        )
    if not source_set_id:
        raise ReplayContextError(f"{config_path}: replay context requires non-empty source_set_id")
    if not catalog_dir:
        raise ReplayContextError(f"{config_path}: replay context requires non-empty catalog_dir")

    declared_catalog_dir = Path(str(catalog_dir))
    base_dir = _context_base_dir(config_path)
    resolved_catalog_dir = _resolve_context_path(base_dir, declared_catalog_dir)

    declared_package_path = Path(str(package_path)) if package_path else None
    resolved_package_path = (
        _resolve_context_path(base_dir, declared_package_path)
        if declared_package_path is not None
        else None
    )

    context = ReplayContext(
        config_path=config_path,
        review_id=review_id,
        source_set_id=source_set_id,
        catalog_dir=declared_catalog_dir,
        resolved_catalog_dir=resolved_catalog_dir,
        package_path=declared_package_path,
        resolved_package_path=resolved_package_path,
    )
    _validate_optional_child_path(payload, config_path, base_dir, "source_catalog_path", context.resolved_source_catalog_path)
    _validate_optional_child_path(
        payload,
        config_path,
        base_dir,
        "source_set_manifest_path",
        context.resolved_source_set_manifest_path,
    )
    _validate_optional_child_path(
        payload,
        config_path,
        base_dir,
        "catalog_sqlite_path",
        context.resolved_catalog_sqlite_path,
    )
    return context


def _context_base_dir(config_path: Path) -> Path:
    resolved = config_path.resolve()
    try:
        return resolved.parents[2]
    except IndexError:
        return resolved.parent


def _resolve_context_path(base_dir: Path, value: Path) -> Path:
    return value if value.is_absolute() else (base_dir / value).resolve()


def _validate_optional_child_path(
    payload: dict,
    config_path: Path,
    base_dir: Path,
    field_name: str,
    expected_path: Path,
) -> None:
    declared = payload.get(field_name)
    if not declared:
        return
    resolved_declared = _resolve_context_path(base_dir, Path(str(declared)))
    if resolved_declared != expected_path:
        raise ReplayContextError(
            f"{config_path}: {field_name} must match the path derived from catalog_dir"
        )
