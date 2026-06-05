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
DEFAULT_EXTRACTION_FIDELITY_EVAL_MANIFEST_PATH = _module_attr(
    "extraction_fidelity_eval", "DEFAULT_EXTRACTION_FIDELITY_EVAL_MANIFEST_PATH"
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
DEFAULT_FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_PATH = _module_attr(
    "forest_specific_example_package_eval",
    "DEFAULT_FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_PATH",
)
DEFAULT_GOLD_COVERAGE_MANIFEST_PATH = _module_attr(
    "gold_coverage_eval", "DEFAULT_GOLD_COVERAGE_MANIFEST_PATH"
)
DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH = _module_attr(
    "graph_gate_review_quality_eval",
    "DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH",
)
DEFAULT_PROMOTION_SUITE_PATH = _module_attr(
    "promotion_suite", "DEFAULT_PROMOTION_SUITE_PATH"
)
DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH = _module_attr(
    "records", "DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH"
)
DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH = _module_attr(
    "records", "DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH"
)
DEFAULT_EVAL_TRACE_CASE_FILE_PATH = _module_attr(
    "eval_trace_case_promote", "DEFAULT_EVAL_TRACE_CASE_FILE_PATH"
)


def run_applicability_eval(**kwargs):
    return _module_attr("applicability_eval", "run_applicability_eval")(**kwargs)


def run_applicability_gold_eval(**kwargs):
    return _module_attr("applicability_eval", "run_applicability_gold_eval")(**kwargs)


def run_draft_generation_eval(**kwargs):
    return _module_attr("draft_generation_eval", "run_draft_generation_eval")(**kwargs)


def run_eval_trace_inventory(**kwargs):
    return _module_attr("eval_trace_inventory", "run_eval_trace_inventory")(**kwargs)


def run_eval_trace_export(**kwargs):
    return _module_attr("eval_trace_export", "run_eval_trace_export")(**kwargs)


def run_eval_trace_store_build(**kwargs):
    return _module_attr("eval_trace_store", "run_eval_trace_store_build")(**kwargs)


def run_eval_trace_case_promote(**kwargs):
    return _module_attr("eval_trace_case_promote", "run_eval_trace_case_promote")(
        **kwargs
    )


def validate_eval_trace_case_file(**kwargs):
    return _module_attr("eval_trace_case_promote", "validate_eval_trace_case_file")(
        **kwargs
    )


def run_eval_context_graph_build(**kwargs):
    return _module_attr("eval_context_graph", "run_eval_context_graph_build")(**kwargs)


def run_eval_context_graph_eval(**kwargs):
    return _module_attr("eval_context_graph", "run_eval_context_graph_eval")(**kwargs)


def run_extraction_fidelity_eval(**kwargs):
    return _module_attr("extraction_fidelity_eval", "run_extraction_fidelity_eval")(**kwargs)


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


def run_source_record_identity_gate(**kwargs):
    return _module_attr("records", "run_source_record_identity_gate")(**kwargs)


def run_real_package_review_coverage_eval(**kwargs):
    return _module_attr(
        "real_package_review_coverage_eval",
        "run_real_package_review_coverage_eval",
    )(**kwargs)


def run_forest_specific_example_package_eval(**kwargs):
    return _module_attr(
        "forest_specific_example_package_eval",
        "run_forest_specific_example_package_eval",
    )(**kwargs)


def run_gold_coverage_eval(**kwargs):
    return _module_attr("gold_coverage_eval", "run_gold_coverage_eval")(**kwargs)


def run_graph_gate_review_quality_eval(**kwargs):
    return _module_attr(
        "graph_gate_review_quality_eval",
        "run_graph_gate_review_quality_eval",
    )(**kwargs)


def run_promotion_suite(**kwargs):
    return _module_attr("promotion_suite", "run_promotion_suite")(**kwargs)


EVAL_COMMANDS = {
    "applicability-eval",
    "applicability-gold-eval",
    "draft-generation-eval",
    "eval-context-graph-build",
    "eval-context-graph-eval",
    "eval-trace-case-promote",
    "eval-trace-export",
    "eval-trace-inventory",
    "eval-trace-store-build",
    "extraction-fidelity-eval",
    "forest-plan-component-eval-coverage",
    "forest-plan-component-retrieval-eval",
    "forest-plan-profile-eval",
    "upstream-eval",
    "phase-eval",
    "source-record-identity-gate",
    "v1-ea-eval",
    "real-package-review-coverage-eval",
    "forest-specific-example-package-eval",
    "gold-coverage-eval",
    "graph-gate-review-quality-eval",
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
        name="eval-context-graph-build",
        help=(
            "Build a generated observability/eval context graph from the local "
            "eval-trace store and optional event logs."
        ),
        arguments=(
            _arg("--sqlite-path", required=True, type=Path),
            _arg("--graph-json-path", required=True, type=Path),
            _arg("--summary-path", type=Path),
            _arg("--event-log-path", action="append", default=[], type=Path),
            _arg("--observability-event-log-path", type=Path),
            _arg(
                "--no-observability-event-log",
                action="store_false",
                dest="include_observability_event_log",
                default=True,
            ),
            _arg(
                "--contract-path",
                default=Path("config/context_graph_contract_v1.json"),
                type=Path,
            ),
        ),
    ),
    EvalCommandSpec(
        name="eval-context-graph-eval",
        help="Run deterministic graph evals over a generated observability/eval context graph.",
        arguments=(
            _arg("--graph-json-path", required=True, type=Path),
            _arg("--summary-path", type=Path),
            _arg(
                "--contract-path",
                default=Path("config/context_graph_contract_v1.json"),
                type=Path,
            ),
        ),
    ),
    EvalCommandSpec(
        name="eval-trace-inventory",
        help="Inventory first-class eval and trace artifact links without mutating source artifacts.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--source-set-id"),
            _arg("--review-id"),
            _arg("--catalog-dir", type=Path),
            _arg("--results-path", type=Path),
            _arg("--format", choices=("json", "markdown"), default="json"),
            _arg("--fail-on-missing-required", action="store_true"),
        ),
    ),
    EvalCommandSpec(
        name="eval-trace-export",
        help="Export local eval/trace store rows as canonical JSON and OpenInference-shaped spans.",
        arguments=(
            _arg("--sqlite-path", required=True, type=Path),
            _arg("--canonical-json-path", required=True, type=Path),
            _arg("--openinference-json-path", required=True, type=Path),
        ),
    ),
    EvalCommandSpec(
        name="eval-trace-store-build",
        help="Build the local SQLite first-class eval/trace store from an inventory JSON file.",
        arguments=(
            _arg("--inventory-path", required=True, type=Path),
            _arg("--sqlite-path", required=True, type=Path),
            _arg("--summary-path", type=Path),
        ),
    ),
    EvalCommandSpec(
        name="eval-trace-case-promote",
        help="Promote a stored first-class eval trace/span into a versioned eval case file.",
        arguments=(
            _arg("--sqlite-path", required=True, type=Path),
            _arg("--case-file", default=DEFAULT_EVAL_TRACE_CASE_FILE_PATH, type=Path),
            _arg("--trace-id"),
            _arg("--span-id"),
            _arg("--case-id"),
            _arg("--owner", required=True),
            _arg(
                "--risk-level",
                required=True,
                choices=("low", "medium", "high", "critical"),
            ),
            _arg("--tag", action="append", dest="tags"),
            _arg("--assertion", action="append", dest="assertions"),
            _arg("--expected-output"),
            _arg("--review-condition", required=True),
            _arg("--removal-condition", required=True),
            _arg("--replace", action="store_true"),
            _arg(
                "--human-label-status",
                default="unlabeled",
                choices=("unlabeled", "labeled", "reviewed", "rejected"),
            ),
            _arg("--human-labeler"),
            _arg("--human-label-note"),
        ),
    ),
    EvalCommandSpec(
        name="eval-trace-case-file-validate",
        help="Validate the tracked first-class eval trace case file.",
        arguments=(
            _arg("--case-file", default=DEFAULT_EVAL_TRACE_CASE_FILE_PATH, type=Path),
            _arg("--summary-path", type=Path),
            _arg(
                "--allow-empty",
                action="store_false",
                dest="require_cases",
                help="Allow a valid case-file schema with zero promoted cases.",
            ),
        ),
    ),
    EvalCommandSpec(
        name="extraction-fidelity-eval",
        help="Run dedicated extraction-fidelity direct-eval fixtures.",
        arguments=(
            _arg(
                "--manifest",
                default=DEFAULT_EXTRACTION_FIDELITY_EVAL_MANIFEST_PATH,
                type=Path,
            ),
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
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
            _arg("--rule-claim-links-path", type=Path),
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
        name="source-record-identity-gate",
        help="Validate expected source-record IDs against a target catalog identity surface.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg("--source-set-id"),
            _arg("--catalog-dir", type=Path),
            _arg("--eval-file", type=Path),
            _arg("--source-record-id", action="append", dest="source_record_ids"),
            _arg(
                "--source-record-reconciliation",
                default=DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
                type=Path,
            ),
            _arg(
                "--forest-plan-identity-reconciliation",
                default=DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH,
                type=Path,
            ),
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
        name="forest-specific-example-package-eval",
        help="Run the aggregate per-forest example-package coverage gate.",
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg(
                "--manifest",
                default=DEFAULT_FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_PATH,
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
        name="graph-gate-review-quality-eval",
        help=(
            "Run the manifest-owned graph-gate review-quality hypothesis test "
            "without adopting graph gates into runtime review."
        ),
        arguments=(
            _arg("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path),
            _arg(
                "--manifest",
                default=DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH,
                type=Path,
            ),
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
        "eval-context-graph-build": EvalCommandHandler(
            run=lambda args: run_eval_context_graph_build(
                sqlite_path=args.sqlite_path,
                graph_json_path=args.graph_json_path,
                summary_path=args.summary_path,
                event_log_paths=args.event_log_path,
                include_observability_event_log=args.include_observability_event_log,
                observability_event_log_path=args.observability_event_log_path,
                contract_path=args.contract_path,
            ),
            success_key="command_succeeded",
        ),
        "eval-context-graph-eval": EvalCommandHandler(
            run=lambda args: run_eval_context_graph_eval(
                graph_json_path=args.graph_json_path,
                summary_path=args.summary_path,
                contract_path=args.contract_path,
            ),
            success_key="command_succeeded",
        ),
        "eval-trace-inventory": EvalCommandHandler(
            run=lambda args: run_eval_trace_inventory(
                output_dir=args.output_dir,
                source_set_id=args.source_set_id,
                review_id=args.review_id,
                catalog_dir=args.catalog_dir,
                results_path=args.results_path,
                format=args.format,
                fail_on_missing_required=args.fail_on_missing_required,
            ),
            success_key="command_succeeded",
        ),
        "eval-trace-export": EvalCommandHandler(
            run=lambda args: run_eval_trace_export(
                sqlite_path=args.sqlite_path,
                canonical_json_path=args.canonical_json_path,
                openinference_json_path=args.openinference_json_path,
            ),
            success_key="command_succeeded",
        ),
        "eval-trace-store-build": EvalCommandHandler(
            run=lambda args: run_eval_trace_store_build(
                inventory_path=args.inventory_path,
                sqlite_path=args.sqlite_path,
                summary_path=args.summary_path,
            ),
            success_key="command_succeeded",
        ),
        "eval-trace-case-promote": EvalCommandHandler(
            run=lambda args: run_eval_trace_case_promote(
                sqlite_path=args.sqlite_path,
                case_file=args.case_file,
                trace_id=args.trace_id,
                span_id=args.span_id,
                case_id=args.case_id,
                owner=args.owner,
                risk_level=args.risk_level,
                tags=args.tags,
                assertions=args.assertions,
                expected_output=args.expected_output,
                review_condition=args.review_condition,
                removal_condition=args.removal_condition,
                replace=args.replace,
                human_label_status=args.human_label_status,
                human_labeler=args.human_labeler,
                human_label_note=args.human_label_note,
            ),
            success_key="command_succeeded",
        ),
        "eval-trace-case-file-validate": EvalCommandHandler(
            run=lambda args: validate_eval_trace_case_file(
                case_file=args.case_file,
                summary_path=args.summary_path,
                require_cases=args.require_cases,
            ),
            success_key="command_succeeded",
        ),
        "extraction-fidelity-eval": EvalCommandHandler(
            run=lambda args: run_extraction_fidelity_eval(
                manifest_path=args.manifest,
                output_dir=args.output_dir,
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
                rule_claim_links_path=args.rule_claim_links_path,
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
        "source-record-identity-gate": EvalCommandHandler(
            run=lambda args: run_source_record_identity_gate(
                output_dir=args.output_dir,
                source_set_id=args.source_set_id,
                catalog_dir=args.catalog_dir,
                eval_file=args.eval_file,
                source_record_ids=args.source_record_ids,
                source_record_reconciliation_path=args.source_record_reconciliation,
                forest_plan_identity_reconciliation_path=(
                    args.forest_plan_identity_reconciliation
                ),
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
        "forest-specific-example-package-eval": EvalCommandHandler(
            run=lambda args: run_forest_specific_example_package_eval(
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
        "graph-gate-review-quality-eval": EvalCommandHandler(
            run=lambda args: run_graph_gate_review_quality_eval(
                output_dir=args.output_dir,
                manifest_path=args.manifest,
                results_dir=args.results_dir,
            ),
            success_key="command_succeeded",
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
