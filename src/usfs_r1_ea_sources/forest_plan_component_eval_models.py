from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re



DEFAULT_FOREST_PLAN_COMPONENT_EVAL_PATH = Path("config/forest_plan_component_eval_seed.json")
FOREST_PLAN_COMPONENT_EVAL_SCHEMA_VERSION = "forest-plan-component-eval-v0"
FOREST_PLAN_COMPONENT_EVAL_RESULTS_SCHEMA_VERSION = "forest-plan-component-eval-results-v0"
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
RESOLVED_COMPLIANCE_STATUSES = {
    "complies",
    "not_applicable",
    "potential_noncompliance",
}


@dataclass(frozen=True)
class ForestPlanComponentEvalResult:
    eval_file: Path
    review_dir: Path
    output_path: Path
    summary: dict[str, Any]
