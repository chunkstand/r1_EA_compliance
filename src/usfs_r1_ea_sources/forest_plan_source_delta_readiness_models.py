from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any



SOURCE_DELTA_READINESS_SCHEMA_VERSION = "r1-forest-plan-source-delta-readiness-v3"
OFFICIAL_SOURCE_GAP_EVIDENCE_SCHEMA_VERSION = "r1-forest-plan-official-source-gap-evidence-v0"
DEFAULT_R1_FOREST_PLAN_REGISTER_PATH = Path("config/r1_forest_plan_document_register_draft.csv")
DEFAULT_FOREST_PLAN_PROFILES_PATH = Path("config/forest_plan_profiles.json")
DEFAULT_OFFICIAL_SOURCE_GAP_EVIDENCE_PATH = Path(
    "config/r1_forest_plan_official_source_gap_evidence.json"
)
DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH = Path(
    "config/r1_forest_plan_component_inventory_build_manifest.json"
)
DEFAULT_SOURCE_DELTA_BATCH_RUN_ID = "r1-forest-plan-source-delta-capture-20260510-batches"
EXPECTED_BASE_CANONICAL_SOURCE_COUNT = 190


@dataclass(frozen=True)
class SourceDeltaReadinessResult:
    report_path: Path
    markdown_path: Path
    summary: dict[str, Any]
