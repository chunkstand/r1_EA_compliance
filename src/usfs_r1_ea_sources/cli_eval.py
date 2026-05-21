from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from .cli_common import print_summary
from .cli_eval_dispatch import EvalCommandHandler, dispatch_eval_command
from .cli_eval_registration import (
    EvalArgumentSpec,
    EvalCommandSpec,
    register_eval_command_specs,
)


DEFAULT_OUTPUT_DIR = Path("source_library")


def _module_attr(module_name: str, attr_name: str):
    module = importlib.import_module(f".{module_name}", __package__)
    return getattr(module, attr_name)


DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH = _module_attr(
    "applicability", "DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH"
)
DEFAULT_APPLICABILITY_EVAL_PATH = _module_attr(
    "applicability_eval", "DEFAULT_APPLICABILITY_EVAL_PATH"
)
DEFAULT_APPLICABILITY_GOLD_EVAL_PATH = _module_attr(
    "applicability_eval", "DEFAULT_APPLICABILITY_GOLD_EVAL_PATH"
)
DEFAULT_RULE_PACK_PATH = _module_attr("rule_packs", "DEFAULT_RULE_PACK_PATH")
DEFAULT_DRAFT_GENERATION_CONFIG_PATH = _module_attr(
    "draft_generation", "DEFAULT_CONFIG_PATH"
)
DEFAULT_DRAFT_GENERATION_EVAL_PATH = _module_attr(
    "draft_generation_eval", "DEFAULT_EVAL_PATH"
)
DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH = _module_attr(
    "upstream_evaluation", "DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH"
)
DEFAULT_FOREST_PLAN_PROFILE_EVAL_MANIFEST_PATH = _module_attr(
    "forest_plan_profile_eval", "DEFAULT_FOREST_PLAN_PROFILE_EVAL_MANIFEST_PATH"
)
DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_MANIFEST_PATH = _module_attr(
    "forest_plan_component_retrieval_eval",
    "DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_MANIFEST_PATH",
)
DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH = _module_attr(
    "forest_plan_component_eval_coverage",
    "DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH",
)
DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH = _module_attr(
    "real_package_review_coverage_eval",
    "DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH",
)
DEFAULT_GOLD_COVERAGE_MANIFEST_PATH = _module_attr(
    "gold_coverage_eval", "DEFAULT_GOLD_COVERAGE_MANIFEST_PATH"
)
DEFAULT_PROMOTION_SUITE_PATH = _module_attr(
    "promotion_suite", "DEFAULT_PROMOTION_SUITE_PATH"
)


def run_applicability_eval(**kwargs):
    return _module_attr("applicability_eval", "run_applicability_eval")(**kwargs)


def run_applicability_gold_eval(**kwargs):
    return _module_attr("applicability_eval", "run_applicability_gold_eval")(**kwargs)


def run_draft_generation_eval(**kwargs):
    return _module_attr("draft_generation_eval", "run_draft_generation_eval")(**kwargs)


def run_upstream_evaluation(**kwargs):
    return _module_attr("upstream_evaluation", "run_upstream_evaluation")(**kwargs)


def run_forest_plan_profile_eval(**kwargs):
    return _module_attr("forest_plan_profile_eval", "run_forest_plan_profile_eval")(**kwargs)


def run_forest_plan_component_retrieval_eval(**kwargs):
    return _module_attr(
        "forest_plan_component_retrieval_eval",
        "run_forest_plan_component_retrieval_eval",
    )(**kwargs)


def run_forest_plan_component_eval_coverage(**kwargs):
    return _module_attr(
        "forest_plan_component_eval_coverage",
        "run_forest_plan_component_eval_coverage",
    )(**kwargs)


def run_phase_aligned_eval(**kwargs):
    return _module_attr("phase_eval", "run_phase_aligned_eval")(**kwargs)


def run_v1_ea_review_eval(**kwargs):
    return _module_attr("v1_ea_eval", "run_v1_ea_review_eval")(**kwargs)


def run_real_package_review_coverage_eval(**kwargs):
    return _module_attr(
        "real_package_review_coverage_eval",
        "run_real_package_review_coverage_eval",
    )(**kwargs)


def run_gold_coverage_eval(**kwargs):
    return _module_attr("gold_coverage_eval", "run_gold_coverage_eval")(**kwargs)


def run_promotion_suite(**kwargs):
    return _module_attr("promotion_suite", "run_promotion_suite")(**kwargs)


EVAL_COMMANDS = {
    "applicability-eval",
    "applicability-gold-eval",
    "draft-generation-eval",
    "forest-plan-component-eval-coverage",
    "forest-plan-component-retrieval-eval",
    "forest-plan-profile-eval",
    "upstream-eval",
    "phase-eval",
    "v1-ea-eval",
    "real-package-review-coverage-eval",
    "gold-coverage-eval",
    "promotion-suite",
}


def _arg(*flags: str, **kwargs) -> EvalArgumentSpec:
    return EvalArgumentSpec(flags=flags, kwargs=kwargs)


COMMAND_SPECS = (
    EvalCommandSpec(
        name="applicability-eval",
        help="Run deterministic applicability decision-quality eval cases.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--source-set-id"),
            _arg("--base-rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path),
            _arg("--eval-file", default=DEFAULT_APPLICABILITY_EVAL_PATH, type=Path),
            _arg(
                "--authority-family-templates-path",
                default=DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
                type=Path,
            ),
            _arg(
                "--no-authority-family-templates",
                action="store_const",
                const=None,
                dest="authority_family_templates_path",
            ),
            _arg("--results-dir", type=Path),
            _arg("--top-k", type=int, default=5),
        ),
    ),
    EvalCommandSpec(
        name="applicability-gold-eval",
        help="Run adjudicated applicability gold eval cases.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--source-set-id"),
            _arg("--base-rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path),
            _arg("--gold-file", default=DEFAULT_APPLICABILITY_GOLD_EVAL_PATH, type=Path),
            _arg(
                "--authority-family-templates-path",
                default=DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
                type=Path,
            ),
            _arg(
                "--no-authority-family-templates",
                action="store_const",
                const=None,
                dest="authority_family_templates_path",
            ),
            _arg("--results-dir", type=Path),
            _arg("--top-k", type=int, default=5),
        ),
    ),
    EvalCommandSpec(
        name="draft-generation-eval",
        help="Run fail-closed draft-generation eval fixtures and validate the live draft packet.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--review-id"),
            _arg("--eval-file", default=DEFAULT_DRAFT_GENERATION_EVAL_PATH, type=Path),
            _arg("--config", default=DEFAULT_DRAFT_GENERATION_CONFIG_PATH, type=Path),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="upstream-eval",
        help="Run deterministic upstream direct-eval coverage fixtures.",
        arguments=(
            _arg("--manifest", default=DEFAULT_UPSTREAM_EVALUATION_MANIFEST_PATH, type=Path),
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="forest-plan-profile-eval",
        help="Run the aggregate Region 1 cross-forest profile coverage gate.",
        arguments=(
            _arg(
                "--manifest",
                default=DEFAULT_FOREST_PLAN_PROFILE_EVAL_MANIFEST_PATH,
                type=Path,
            ),
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="forest-plan-component-retrieval-eval",
        help="Run the standalone source-set component retrieval coverage gate.",
        arguments=(
            _arg(
                "--manifest",
                default=DEFAULT_FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_MANIFEST_PATH,
                type=Path,
            ),
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="forest-plan-component-eval-coverage",
        help="Run the aggregate component coverage gate across retrieval and tracked review slots.",
        arguments=(
            _arg(
                "--manifest",
                default=DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
                type=Path,
            ),
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="phase-eval",
        help="Run phase-aligned readiness evals across generated artifacts.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--source-set-id"),
            _arg("--catalog-dir", type=Path),
            _arg("--review-id"),
            _arg("--review-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="v1-ea-eval",
        help="Evaluate a real EA compliance review against the V1 source/section contract.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--review-id"),
            _arg("--review-dir", type=Path),
            _arg("--eval-file", type=Path),
            _arg(
                "--manifest",
                default=DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
                type=Path,
            ),
            _arg("--output-path", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="real-package-review-coverage-eval",
        help="Run the aggregate real-package review coverage gate across tracked review slots.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg(
                "--manifest",
                default=DEFAULT_REAL_PACKAGE_REVIEW_COVERAGE_MANIFEST_PATH,
                type=Path,
            ),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="gold-coverage-eval",
        help="Run the aggregate gold coverage gate across adjudicated gold and real-review contracts.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--manifest", default=DEFAULT_GOLD_COVERAGE_MANIFEST_PATH, type=Path),
            _arg("--results-dir", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="promotion-suite",
        help="Check manifest-declared promotion evidence and write an aggregate readiness report.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--manifest", default=DEFAULT_PROMOTION_SUITE_PATH, type=Path),
            _arg("--results-dir", type=Path),
            _arg(
                "--strict-expansion",
                action="store_true",
                help="Require expansion slots to be ready before returning promotion-ready.",
            ),
        ),
    ),
)


def register_eval_commands(subparsers: argparse._SubParsersAction) -> None:
    register_eval_command_specs(subparsers, COMMAND_SPECS)


def _command_handlers() -> dict[str, EvalCommandHandler]:
    return {
        "applicability-eval": EvalCommandHandler(
            run=lambda args: run_applicability_eval(
                output_dir=args.output_dir,
                eval_file=args.eval_file,
                base_rule_pack_path=args.base_rule_pack,
                authority_family_templates_path=args.authority_family_templates_path,
                source_set_id=args.source_set_id,
                results_dir=args.results_dir,
                top_k=args.top_k,
            ),
            success_key="passed",
        ),
        "applicability-gold-eval": EvalCommandHandler(
            run=lambda args: run_applicability_gold_eval(
                output_dir=args.output_dir,
                gold_file=args.gold_file,
                base_rule_pack_path=args.base_rule_pack,
                authority_family_templates_path=args.authority_family_templates_path,
                source_set_id=args.source_set_id,
                results_dir=args.results_dir,
                top_k=args.top_k,
            ),
            success_key="passed",
        ),
        "draft-generation-eval": EvalCommandHandler(
            run=lambda args: run_draft_generation_eval(
                output_dir=args.output_dir,
                review_id=args.review_id,
                eval_path=args.eval_file,
                config_path=args.config,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "upstream-eval": EvalCommandHandler(
            run=lambda args: run_upstream_evaluation(
                manifest_path=args.manifest,
                output_dir=args.output_dir,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "forest-plan-profile-eval": EvalCommandHandler(
            run=lambda args: run_forest_plan_profile_eval(
                manifest_path=args.manifest,
                output_dir=args.output_dir,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "forest-plan-component-retrieval-eval": EvalCommandHandler(
            run=lambda args: run_forest_plan_component_retrieval_eval(
                manifest_path=args.manifest,
                output_dir=args.output_dir,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "forest-plan-component-eval-coverage": EvalCommandHandler(
            run=lambda args: run_forest_plan_component_eval_coverage(
                manifest_path=args.manifest,
                output_dir=args.output_dir,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "phase-eval": EvalCommandHandler(
            run=lambda args: run_phase_aligned_eval(
                output_dir=args.output_dir,
                source_set_id=args.source_set_id,
                catalog_dir=args.catalog_dir,
                review_id=args.review_id,
                review_dir=args.review_dir,
            ),
            success_key="reviewer_ready",
        ),
        "v1-ea-eval": EvalCommandHandler(
            run=lambda args: run_v1_ea_review_eval(
                output_dir=args.output_dir,
                review_id=args.review_id,
                review_dir=args.review_dir,
                eval_file=args.eval_file,
                manifest_path=args.manifest,
                output_path=args.output_path,
            ),
            success_key="passed",
        ),
        "real-package-review-coverage-eval": EvalCommandHandler(
            run=lambda args: run_real_package_review_coverage_eval(
                output_dir=args.output_dir,
                manifest_path=args.manifest,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "gold-coverage-eval": EvalCommandHandler(
            run=lambda args: run_gold_coverage_eval(
                output_dir=args.output_dir,
                manifest_path=args.manifest,
                results_dir=args.results_dir,
            ),
            success_key="passed",
        ),
        "promotion-suite": EvalCommandHandler(
            run=lambda args: run_promotion_suite(
                output_dir=args.output_dir,
                manifest_path=args.manifest,
                results_dir=args.results_dir,
                strict_expansion=args.strict_expansion,
            ),
            success_key="promotion_ready",
        ),
    }


def handle_eval_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
    del parser
    return dispatch_eval_command(args, _command_handlers(), print_summary)
