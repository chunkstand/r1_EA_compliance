from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvalTraceInventoryResult:
    summary: dict[str, Any]
    report: str | None = None


@dataclass(frozen=True)
class ArtifactSpec:
    family_id: str
    path: Path
    required: bool = True
    kind: str = "json"
