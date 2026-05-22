from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re


FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION = "forest-plan-component-adjudication-v0"
FOREST_PLAN_COMPONENT_ADJUDICATION_EVAL_SCHEMA_VERSION = (
    "forest-plan-component-adjudication-eval-v0"
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

PENDING_DISPOSITIONS = {"pending"}
RESOLVED_DISPOSITIONS = {
    "true_ea_omission",
    "retrieval_miss",
    "package_section_chunking_miss",
    "component_inventory_overreach",
    "applicability_false_positive",
    "evidence_linking_miss",
}
ALLOWED_DISPOSITIONS = PENDING_DISPOSITIONS | RESOLVED_DISPOSITIONS
REQUIRED_ADJUDICATION_FIELDS = ("adjudicated_at", "rationale", "source_type")
REAL_EA_OMISSION_DISPOSITIONS = {"true_ea_omission"}
SYSTEM_MISS_DISPOSITIONS = RESOLVED_DISPOSITIONS - REAL_EA_OMISSION_DISPOSITIONS


@dataclass(frozen=True)
class ForestPlanComponentAdjudicationTemplateResult:
    review_dir: Path
    output_path: Path
    markdown_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ForestPlanComponentAdjudicationEvalResult:
    review_dir: Path
    adjudication_file: Path
    output_path: Path
    summary: dict[str, Any]
