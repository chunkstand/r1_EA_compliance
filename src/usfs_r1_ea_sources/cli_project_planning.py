from __future__ import annotations

from pathlib import Path
import argparse

from .cli_common import print_summary
from .project_sow_package import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package import DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH
from .project_sow_package import DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH
from .project_sow_package import DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH
from .project_sow_package import DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR
from .project_sow_package import DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH
from .project_sow_package import DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR
from .project_sow_package import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package import run_project_sow_adjudication_apply
from .project_sow_package import run_project_sow_adjudication_eval
from .project_sow_package import run_project_sow_ea_package_handoff
from .project_sow_package import run_project_sow_eval
from .project_sow_package import run_project_sow_intake_draft
from .project_sow_package import run_project_sow_operational_gate
from .project_sow_package import run_project_sow_package
from .project_sow_package import validate_project_sow_intake
from .project_sow_package import write_project_sow_adjudication_template


PROJECT_PLANNING_COMMANDS = {
    "project-sow-adjudication-apply",
    "project-sow-adjudication-eval",
    "project-sow-adjudication-template",
    "project-sow-ea-package-handoff",
    "project-sow-eval",
    "project-sow-intake-draft",
    "project-sow-intake-validate",
    "project-sow-operational-gate",
    "project-sow-package",
}


def register_project_planning_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    package = subparsers.add_parser(
        "project-sow-package",
        help="Generate a proposed-action NEPA resource SOW requirements package.",
    )
    package.add_argument("--intake", required=True, type=Path)
    package.add_argument("--output-dir", default=Path("source_library"), type=Path)
    package.add_argument("--project-id")
    package.add_argument("--source-set-id")
    package.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the intake without writing requirement package outputs.",
    )
    package.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    package.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )
    package.add_argument("--results-dir", type=Path)

    validate = subparsers.add_parser(
        "project-sow-intake-validate",
        help="Validate a proposed-action resource SOW intake without writing package outputs.",
    )
    validate.add_argument("--intake", required=True, type=Path)
    validate.add_argument("--project-id")
    validate.add_argument("--source-set-id")
    validate.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    validate.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )

    draft = subparsers.add_parser(
        "project-sow-intake-draft",
        help="Draft an unreviewed project SOW intake from proposed-action text.",
    )
    draft.add_argument("--proposed-action", required=True, type=Path)
    draft.add_argument("--output", required=True, type=Path)
    draft.add_argument("--project-id")
    draft.add_argument("--project-name")
    draft.add_argument("--forest")
    draft.add_argument("--district", action="append", dest="districts")
    draft.add_argument("--project-type", default="land_exchange")
    draft.add_argument("--nepa-level", default="environmental_assessment")
    draft.add_argument("--source-title")
    draft.add_argument(
        "--draft-rules",
        default=DEFAULT_INTAKE_DRAFT_RULES_CONFIG_PATH,
        type=Path,
    )
    draft.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    draft.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )

    eval_command = subparsers.add_parser(
        "project-sow-eval",
        help="Run project SOW proving-intake evaluation cases.",
    )
    eval_command.add_argument(
        "--eval-config",
        default=DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH,
        type=Path,
    )
    eval_command.add_argument(
        "--output-dir",
        default=DEFAULT_PROJECT_SOW_EVAL_OUTPUT_DIR,
        type=Path,
    )
    eval_command.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    eval_command.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )

    adjudication_template = subparsers.add_parser(
        "project-sow-adjudication-template",
        help="Write a reviewer worklist and adjudication template for project SOW review items.",
    )
    adjudication_template.add_argument("--intake", required=True, type=Path)
    adjudication_template.add_argument("--output-dir", default=Path("source_library"), type=Path)
    adjudication_template.add_argument("--project-id")
    adjudication_template.add_argument("--source-set-id")
    adjudication_template.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    adjudication_template.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )
    adjudication_template.add_argument("--results-dir", type=Path)

    adjudication_eval = subparsers.add_parser(
        "project-sow-adjudication-eval",
        help="Evaluate a completed project SOW adjudication artifact against the current intake queue.",
    )
    adjudication_eval.add_argument("--intake", required=True, type=Path)
    adjudication_eval.add_argument("--adjudication", required=True, type=Path)
    adjudication_eval.add_argument("--output", type=Path)
    adjudication_eval.add_argument("--project-id")
    adjudication_eval.add_argument("--source-set-id")
    adjudication_eval.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    adjudication_eval.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )

    adjudication_apply = subparsers.add_parser(
        "project-sow-adjudication-apply",
        help="Replay a passing project SOW adjudication artifact into an adjudicated intake copy.",
    )
    adjudication_apply.add_argument("--intake", required=True, type=Path)
    adjudication_apply.add_argument("--adjudication", required=True, type=Path)
    adjudication_apply.add_argument("--output", type=Path)
    adjudication_apply.add_argument("--output-intake", type=Path)
    adjudication_apply.add_argument("--eval-output", type=Path)
    adjudication_apply.add_argument("--project-id")
    adjudication_apply.add_argument("--source-set-id")
    adjudication_apply.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    adjudication_apply.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )

    ea_handoff = subparsers.add_parser(
        "project-sow-ea-package-handoff",
        help="Write a downstream EA package assembly checklist from project_sow_package.json.",
    )
    ea_handoff.add_argument("--package", required=True, type=Path)
    ea_handoff.add_argument("--output", type=Path)
    ea_handoff.add_argument("--markdown-output", type=Path)
    ea_handoff.add_argument(
        "--handoff-rules",
        default=DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH,
        type=Path,
    )

    operational_gate = subparsers.add_parser(
        "project-sow-operational-gate",
        help="Run the Project SOW operational readiness gate and write a report.",
    )
    operational_gate.add_argument(
        "--output-dir",
        default=DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR,
        type=Path,
    )
    operational_gate.add_argument(
        "--eval-config",
        default=DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH,
        type=Path,
    )
    operational_gate.add_argument(
        "--template-intake",
        default=DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH,
        type=Path,
    )
    operational_gate.add_argument(
        "--resource-scope-config",
        default=DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
        type=Path,
    )
    operational_gate.add_argument(
        "--authority-inventory",
        default=DEFAULT_AUTHORITY_INVENTORY_PATH,
        type=Path,
    )
    operational_gate.add_argument(
        "--handoff-rules",
        default=DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH,
        type=Path,
    )


def handle_project_planning_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    if args.command == "project-sow-package":
        if args.validate_only:
            result = validate_project_sow_intake(
                intake_path=args.intake,
                project_id=args.project_id,
                source_set_id=args.source_set_id,
                resource_scope_config_path=args.resource_scope_config,
                authority_inventory_path=args.authority_inventory,
            )
            print_summary(result.summary)
            return 0 if result.summary["passed"] else 1

        result = run_project_sow_package(
            intake_path=args.intake,
            output_dir=args.output_dir,
            project_id=args.project_id,
            source_set_id=args.source_set_id,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-intake-validate":
        result = validate_project_sow_intake(
            intake_path=args.intake,
            project_id=args.project_id,
            source_set_id=args.source_set_id,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-intake-draft":
        result = run_project_sow_intake_draft(
            proposed_action_path=args.proposed_action,
            output_path=args.output,
            project_id=args.project_id,
            project_name=args.project_name,
            forest=args.forest,
            districts=args.districts,
            project_type=args.project_type,
            nepa_level=args.nepa_level,
            source_title=args.source_title,
            draft_rules_config_path=args.draft_rules,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-eval":
        result = run_project_sow_eval(
            eval_config_path=args.eval_config,
            output_dir=args.output_dir,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-adjudication-template":
        result = write_project_sow_adjudication_template(
            intake_path=args.intake,
            output_dir=args.output_dir,
            project_id=args.project_id,
            source_set_id=args.source_set_id,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
            results_dir=args.results_dir,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-adjudication-eval":
        result = run_project_sow_adjudication_eval(
            intake_path=args.intake,
            adjudication_path=args.adjudication,
            output_path=args.output,
            project_id=args.project_id,
            source_set_id=args.source_set_id,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-adjudication-apply":
        result = run_project_sow_adjudication_apply(
            intake_path=args.intake,
            adjudication_path=args.adjudication,
            output_intake_path=args.output_intake,
            output_path=args.output,
            eval_output_path=args.eval_output,
            project_id=args.project_id,
            source_set_id=args.source_set_id,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-ea-package-handoff":
        result = run_project_sow_ea_package_handoff(
            package_path=args.package,
            output_path=args.output,
            markdown_path=args.markdown_output,
            handoff_rules_config_path=args.handoff_rules,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "project-sow-operational-gate":
        result = run_project_sow_operational_gate(
            output_dir=args.output_dir,
            eval_config_path=args.eval_config,
            template_intake_path=args.template_intake,
            resource_scope_config_path=args.resource_scope_config,
            authority_inventory_path=args.authority_inventory,
            handoff_rules_config_path=args.handoff_rules,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None
