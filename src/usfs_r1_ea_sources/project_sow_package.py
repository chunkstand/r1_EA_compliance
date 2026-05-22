from __future__ import annotations

from pathlib import Path

from .project_sow_package_adjudication import run_project_sow_adjudication_apply
from .project_sow_package_adjudication import run_project_sow_adjudication_eval
from .project_sow_package_adjudication import write_project_sow_adjudication_template
from .project_sow_package_assembly import run_project_sow_package
from .project_sow_package_draft import run_project_sow_intake_draft
from .project_sow_package_draft import validate_project_sow_intake
from .project_sow_package_ea_handoff import run_project_sow_ea_package_handoff
from .project_sow_package_graph import _intake_graph_validation_checks
from .project_sow_package_models import CONTRACT_REQUIRED_SCOPE_FIELDS
from .project_sow_package_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package_models import DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR
from .project_sow_package_models import DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR
from .project_sow_package_models import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package_models import GENERATOR_VERSION
from .project_sow_package_models import MANIFEST_SCHEMA_VERSION
from .project_sow_package_models import PACKAGE_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_DECISIONS
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_ITEM_TYPES
from .project_sow_package_models import PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_ALLOWED_CATEGORY_APPLIES_TO
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_REQUIRED_BOUNDARY_IDS
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_RULES_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_SUMMARY_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_CLOSEOUT_CONTRACT_FIELDS
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_SUMMARY_SCHEMA_VERSION
from .project_sow_package_models import ProjectSowAdjudicationApplyResult
from .project_sow_package_models import ProjectSowAdjudicationEvalResult
from .project_sow_package_models import ProjectSowAdjudicationTemplateResult
from .project_sow_package_models import ProjectSowEaPackageHandoffResult
from .project_sow_package_models import ProjectSowEvalResult
from .project_sow_package_models import ProjectSowIntakeDraftResult
from .project_sow_package_models import ProjectSowIntakeValidationResult
from .project_sow_package_models import ProjectSowOperationalGateResult
from .project_sow_package_models import ProjectSowPackageResult
from .project_sow_package_operational_gate import run_project_sow_operational_gate as _run_project_sow_operational_gate
from .project_sow_package_rendering import _rendering_validation_checks
from .project_sow_package_eval import run_project_sow_eval


def run_project_sow_operational_gate(
    *,
    output_dir: Path = DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR,
    eval_config_path: Path = DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH,
    template_intake_path: Path = DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    handoff_rules_config_path: Path = DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH,
) -> ProjectSowOperationalGateResult:
    return _run_project_sow_operational_gate(
        output_dir=output_dir,
        eval_config_path=eval_config_path,
        template_intake_path=template_intake_path,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
        handoff_rules_config_path=handoff_rules_config_path,
        doc_requirements=PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS,
    )


__all__ = [
    "CONTRACT_REQUIRED_SCOPE_FIELDS",
    "DEFAULT_AUTHORITY_INVENTORY_PATH",
    "DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH",
    "DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH",
    "DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH",
    "DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR",
    "DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH",
    "DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR",
    "DEFAULT_RESOURCE_SCOPE_CONFIG_PATH",
    "GENERATOR_VERSION",
    "MANIFEST_SCHEMA_VERSION",
    "PACKAGE_SCHEMA_VERSION",
    "PROJECT_SOW_ADJUDICATION_APPLY_SCHEMA_VERSION",
    "PROJECT_SOW_ADJUDICATION_DECISIONS",
    "PROJECT_SOW_ADJUDICATION_EVAL_SCHEMA_VERSION",
    "PROJECT_SOW_ADJUDICATION_ITEM_TYPES",
    "PROJECT_SOW_ADJUDICATION_SCHEMA_VERSION",
    "PROJECT_SOW_EA_HANDOFF_ALLOWED_CATEGORY_APPLIES_TO",
    "PROJECT_SOW_EA_HANDOFF_REQUIRED_BOUNDARY_IDS",
    "PROJECT_SOW_EA_HANDOFF_RULES_SCHEMA_VERSION",
    "PROJECT_SOW_EA_HANDOFF_SCHEMA_VERSION",
    "PROJECT_SOW_EA_HANDOFF_SUMMARY_SCHEMA_VERSION",
    "PROJECT_SOW_INTAKE_ADJUDICATION_SCHEMA_VERSION",
    "PROJECT_SOW_OPERATIONAL_GATE_CLOSEOUT_CONTRACT_FIELDS",
    "PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS",
    "PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS",
    "PROJECT_SOW_OPERATIONAL_GATE_SUMMARY_SCHEMA_VERSION",
    "ProjectSowAdjudicationApplyResult",
    "ProjectSowAdjudicationEvalResult",
    "ProjectSowAdjudicationTemplateResult",
    "ProjectSowEaPackageHandoffResult",
    "ProjectSowEvalResult",
    "ProjectSowIntakeDraftResult",
    "ProjectSowIntakeValidationResult",
    "ProjectSowOperationalGateResult",
    "ProjectSowPackageResult",
    "_intake_graph_validation_checks",
    "_rendering_validation_checks",
    "run_project_sow_adjudication_apply",
    "run_project_sow_adjudication_eval",
    "run_project_sow_ea_package_handoff",
    "run_project_sow_eval",
    "run_project_sow_intake_draft",
    "run_project_sow_operational_gate",
    "run_project_sow_package",
    "validate_project_sow_intake",
    "write_project_sow_adjudication_template",
]
