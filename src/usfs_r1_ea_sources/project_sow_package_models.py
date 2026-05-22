from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PACKAGE_SCHEMA_VERSION = "project-sow-package-v0"
MANIFEST_SCHEMA_VERSION = "project-sow-package-manifest-v0"
GENERATOR_VERSION = "project-sow-package-generator-v0"
DEFAULT_RESOURCE_SCOPE_CONFIG_PATH = Path("config/project_sow_resource_scopes_v1.json")
DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH = Path("config/project_sow_intake_draft_rules_v1.json")
DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH = Path(
    "config/templates/project_sow_land_exchange_intake_template.json"
)
DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH = Path("config/project_sow_eval_proving_intakes_v1.json")
DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR = Path("source_library/project_sow_eval")
DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR = Path(
    "source_library/project_sow_operational_gate"
)
DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH = Path(
    "config/project_sow_ea_handoff_rules_v1.json"
)
PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION = "project-sow-adjudication-v0"
PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION = "project-sow-adjudication-eval-v0"
PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION = "project-sow-adjudication-apply-v0"
PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION = "project-sow-intake-adjudication-v0"
PROJECT_SOW_EA_HANDOFF_SCHEMA_VERSION = "project-sow-ea-package-handoff-v0"
PROJECT_SOW_EA_HANDOFF_SUMMARY_SCHEMA_VERSION = "project-sow-ea-package-handoff-summary-v0"
PROJECT_SOW_EA_HANDOFF_RULES_SCHEMA_VERSION = "project-sow-ea-handoff-rules-v1"
PROJECT_SOW_OPERATIONAL_GATE_SUMMARY_SCHEMA_VERSION = "project-sow-operational-gate-summary-v0"
PROJECT_SOW_EA_HANDOFF_ALLOWED_CATEGORY_APPLIES_TO = (
    "all_selected_scopes",
    "rule_matches",
)
PROJECT_SOW_EA_HANDOFF_REQUIRED_BOUNDARY_IDS = (
    "future_artifacts_not_required_now",
    "no_applicability_review",
    "no_compliance_review",
    "no_generated_rule_pack",
    "no_legal_sufficiency",
)
PROJECT_SOW_ADJUDICATION_DECISIONS = (
    "accepted",
    "rejected",
    "needs_information",
    "out_of_scope",
)
PROJECT_SOW_ADJUDICATION_ITEM_TYPES = (
    "calibration_gap",
    "missing_evidence_ref",
    "optional_deliverable_decision",
    "unknown_resource_area_id",
    "unresolved_resource_area",
)
CONTRACT_REQUIRED_SCOPE_FIELDS = [
    "acceptance_criteria",
    "assumptions",
    "dependencies",
    "optional_deliverables",
    "review_timing",
    "reviewer_role",
    "reviewer_signoff_fields",
]
PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS = (
    Path("docs/schemas/project_sow_intake_v0.schema.json"),
    Path("config/templates/project_sow_land_exchange_intake_template.json"),
    Path("config/project_sow_resource_scopes_v1.json"),
    Path("config/project_sow_ea_handoff_rules_v1.json"),
    Path("config/project_sow_eval_proving_intakes_v1.json"),
    Path("config/fixtures/project_sow/east_crazies_land_exchange_intake.json"),
)
PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS = (
    (
        Path("README.md"),
        ("project-sow-operational-gate", "operational readiness"),
    ),
    (
        Path("docs/PROJECT_SOW_OPERATIONALIZATION_MILESTONE_PLAN.md"),
        ("Sequence 7", "project-sow-operational-gate"),
    ),
    (
        Path("docs/PROJECT_SOW_PACKAGE_RUNBOOK.md"),
        ("project-sow-operational-gate", "Operational Gate"),
    ),
    (
        Path("docs/ARCHITECTURE.md"),
        ("project-sow-operational-gate",),
    ),
    (
        Path("docs/OUTPUT_SCHEMAS.md"),
        ("project_sow_operational_gate_summary.json",),
    ),
    (
        Path("docs/CURRENT_SYSTEM_STATE.md"),
        ("project-sow-operational-gate",),
    ),
    (
        Path("docs/SESSION_HANDOFF.md"),
        ("Sequence 7", "project-sow-operational-gate"),
    ),
    (
        Path("docs/architecture_contract.toml"),
        ("project-sow-operational-gate",),
    ),
    (
        Path("docs/PROJECT_SOW_OPERATIONAL_READINESS_REPORT.md"),
        ("project-sow-operational-gate", "local-only"),
    ),
    (
        Path("docs/PROJECT_SOW_OPERATIONALIZATION_ACCEPTANCE_MATRIX.md"),
        ("Sequence 1", "Sequence 7", "acceptance criteria"),
    ),
)
PROJECT_SOW_OPERATIONAL_GATE_CLOSEOUT_CONTRACT_FIELDS = (
    "artifact_boundaries",
    "ci_policy",
    "downstream_use",
    "generated_outputs",
    "must_not_infer",
    "required_green_checks",
    "tracked_doc_paths",
    "tracked_json_paths",
)


@dataclass(frozen=True)
class ProjectSowPackageResult:
    output_dir: Path
    package_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowIntakeValidationResult:
    intake_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowIntakeDraftResult:
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowEvalResult:
    output_dir: Path
    summary_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowAdjudicationTemplateResult:
    output_path: Path
    worklist_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowAdjudicationEvalResult:
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowAdjudicationApplyResult:
    output_path: Path
    output_intake_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowEaPackageHandoffResult:
    output_path: Path
    markdown_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ProjectSowOperationalGateResult:
    output_dir: Path
    summary_path: Path
    markdown_path: Path
    summary: dict[str, Any]
