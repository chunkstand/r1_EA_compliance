from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from .workbook import load_r1_forest_plan_document_register


DEFAULT_R1_FOREST_PLAN_REGISTER_PATH = Path("config/r1_forest_plan_document_register_draft.csv")


@lru_cache(maxsize=1)
def load_support_document_role_overrides() -> dict[str, str]:
    if not DEFAULT_R1_FOREST_PLAN_REGISTER_PATH.exists():
        return {}
    register = load_r1_forest_plan_document_register(DEFAULT_R1_FOREST_PLAN_REGISTER_PATH)
    return {
        row["proposed_source_record_id"]: row["document_role"]
        for row in register.rows
    }


def resolve_support_document_role(
    row: dict,
    *,
    support_document_role_overrides: dict[str, str],
) -> str:
    return str(
        support_document_role_overrides.get(str(row.get("source_record_id") or ""))
        or row.get("metadata", {}).get("document_role")
        or row.get("document_role")
        or ""
    )


def source_derived_dir(derived_dir: Path, source_set_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", source_set_id):
        raise ValueError(f"Unsafe source_set_id for derived output path: {source_set_id!r}")
    derived_root = derived_dir.resolve()
    path = (derived_root / source_set_id).resolve()
    try:
        path.relative_to(derived_root)
    except ValueError as error:
        message = f"Unsafe derived output path for source_set_id: {source_set_id}"
        raise ValueError(message) from error
    return path
