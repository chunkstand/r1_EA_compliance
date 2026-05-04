from __future__ import annotations

from pathlib import Path
import argparse

from .applicability import DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH
from .applicability import build_authority_universe_snapshot
from .applicability_decisions import build_applicability_decisions
from .applicability_retrieval import build_applicability_retrieval_traces
from .applicability_rule_pack import generate_applicability_rule_pack
from .applicability_rule_pack import validate_generated_rule_pack
from .applicability_validation import apply_applicability_adjudication
from .applicability_validation import evaluate_applicability_adjudication
from .applicability_validation import validate_applicability_run
from .applicability_validation import write_applicability_adjudication_template
from .cli_common import print_summary
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .rule_packs import DEFAULT_RULE_PACK_PATH


APPLICABILITY_COMMANDS = {
    "applicability-authority-universe",
    "applicability-context-build",
    "applicability-retrieve",
    "applicability-determine",
    "applicability-validate",
    "applicability-adjudication-template",
    "applicability-adjudication-eval",
    "applicability-adjudication-apply",
    "applicability-generate-rule-pack",
}


def register_applicability_commands(subparsers: argparse._SubParsersAction) -> None:
    authority_universe = subparsers.add_parser(
        "applicability-authority-universe",
        help="Build the pre-review authority-universe snapshot without deciding applicability.",
    )
    _add_review_source_args(authority_universe)
    authority_universe.add_argument("--base-rule-pack", default=DEFAULT_RULE_PACK_PATH, type=Path)
    authority_universe.add_argument(
        "--authority-family-templates-path",
        default=DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
        type=Path,
        help=(
            "Milestone 3 authority-family rule-template config. "
            f"Defaults to {DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH}."
        ),
    )
    authority_universe.add_argument(
        "--no-authority-family-templates",
        action="store_const",
        const=None,
        dest="authority_family_templates_path",
        help="Disable Milestone 3 authority-family templates for narrow legacy or unit runs.",
    )
    authority_universe.add_argument(
        "--forest-plan-profiles-path",
        default=DEFAULT_FOREST_PLAN_PROFILES_PATH,
        type=Path,
    )
    authority_universe.add_argument("--forest-plan-component-inventory-path", type=Path)
    authority_universe.add_argument("--claims-path", type=Path)
    authority_universe.add_argument("--rule-claim-links-path", type=Path)

    context = subparsers.add_parser(
        "applicability-context-build",
        help="Build package fact graph and applicability context artifacts from package cache.",
    )
    _add_review_source_args(context)
    context.add_argument("--package-path", type=Path)
    context.add_argument("--package-manifest-path", type=Path)
    context.add_argument("--package-chunks-path", type=Path)
    context.add_argument(
        "--forest-plan-profiles-path",
        default=DEFAULT_FOREST_PLAN_PROFILES_PATH,
        type=Path,
    )

    retrieve = subparsers.add_parser(
        "applicability-retrieve",
        help="Write per-authority applicability retrieval and bounded graph traces.",
    )
    _add_review_source_args(retrieve)
    retrieve.add_argument("--authority-universe-path", type=Path)
    retrieve.add_argument("--package-fact-graph-path", type=Path)
    retrieve.add_argument("--retrieval-index-path", type=Path)
    retrieve.add_argument("--graph-nodes-path", type=Path)
    retrieve.add_argument("--graph-edges-path", type=Path)
    retrieve.add_argument("--top-k", type=int, default=5)
    retrieve.add_argument("--max-graph-paths-per-candidate", type=int, default=25)

    determine = subparsers.add_parser(
        "applicability-determine",
        help="Write deterministic applicability decisions and authority artifacts.",
    )
    _add_review_source_args(determine)
    determine.add_argument("--authority-universe-path", type=Path)
    determine.add_argument("--package-fact-graph-path", type=Path)
    determine.add_argument("--package-applicability-context-path", type=Path)
    determine.add_argument("--retrieval-trace-path", type=Path)
    determine.add_argument("--graph-trace-path", type=Path)

    validate = subparsers.add_parser(
        "applicability-validate",
        help="Validate applicability decisions, coverage, provenance, and adjudication readiness.",
    )
    _add_review_source_args(validate)
    validate.add_argument("--authority-universe-path", type=Path)
    validate.add_argument("--package-fact-graph-path", type=Path)
    validate.add_argument("--package-applicability-context-path", type=Path)
    validate.add_argument("--package-fact-graph-validation-path", type=Path)
    validate.add_argument("--retrieval-trace-path", type=Path)
    validate.add_argument("--graph-trace-path", type=Path)
    validate.add_argument("--decisions-path", type=Path)
    validate.add_argument("--applicable-authorities-path", type=Path)
    validate.add_argument("--non-applicable-authorities-path", type=Path)
    validate.add_argument("--search-coverage-certificates-path", type=Path)
    validate.add_argument("--provenance-path", type=Path)
    validate.add_argument("--validation-path", type=Path)

    template = subparsers.add_parser(
        "applicability-adjudication-template",
        help="Write a reviewer-fillable adjudication template for applicability decisions.",
    )
    _add_review_source_args(template)
    template.add_argument("--decisions-path", type=Path)
    template.add_argument("--output-path", type=Path)

    adjudication_eval = subparsers.add_parser(
        "applicability-adjudication-eval",
        help="Evaluate a completed applicability adjudication file against current decisions.",
    )
    _add_review_source_args(adjudication_eval)
    adjudication_eval.add_argument("--adjudication-file", type=Path)
    adjudication_eval.add_argument("--decisions-path", type=Path)
    adjudication_eval.add_argument("--output-path", type=Path)

    adjudication_apply = subparsers.add_parser(
        "applicability-adjudication-apply",
        help="Replay a completed applicability adjudication into partition artifacts.",
    )
    _add_review_source_args(adjudication_apply)
    adjudication_apply.add_argument("--adjudication-file", type=Path)
    adjudication_apply.add_argument("--decisions-path", type=Path)
    adjudication_apply.add_argument("--applicable-authorities-path", type=Path)
    adjudication_apply.add_argument("--non-applicable-authorities-path", type=Path)
    adjudication_apply.add_argument("--provenance-path", type=Path)
    adjudication_apply.add_argument("--output-path", type=Path)

    generated = subparsers.add_parser(
        "applicability-generate-rule-pack",
        help="Generate or validate a compliance rule pack from passing applicability validation.",
    )
    _add_review_source_args(generated)
    generated.add_argument("--base-rule-pack", type=Path)
    generated.add_argument("--authority-universe-path", type=Path)
    generated.add_argument("--decisions-path", type=Path)
    generated.add_argument("--applicable-authorities-path", type=Path)
    generated.add_argument("--non-applicable-authorities-path", type=Path)
    generated.add_argument("--applicability-validation-path", type=Path)
    generated.add_argument("--output-path", type=Path)
    generated.add_argument("--validation-output-path", type=Path)
    generated.add_argument("--validate-only", action="store_true")


def handle_applicability_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int | None:
    if args.command == "applicability-authority-universe":
        result = build_authority_universe_snapshot(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            base_rule_pack_path=args.base_rule_pack,
            authority_family_templates_path=args.authority_family_templates_path,
            forest_plan_profiles_path=args.forest_plan_profiles_path,
            forest_plan_component_inventory_path=args.forest_plan_component_inventory_path,
            claims_path=args.claims_path,
            rule_claim_links_path=args.rule_claim_links_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "applicability-context-build":
        from .package_fact_graph import build_package_fact_graph

        result = build_package_fact_graph(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            package_path=args.package_path,
            package_manifest_path=args.package_manifest_path,
            package_chunks_path=args.package_chunks_path,
            forest_plan_profiles_path=args.forest_plan_profiles_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "applicability-retrieve":
        result = build_applicability_retrieval_traces(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            authority_universe_path=args.authority_universe_path,
            package_fact_graph_path=args.package_fact_graph_path,
            retrieval_index_path=args.retrieval_index_path,
            graph_nodes_path=args.graph_nodes_path,
            graph_edges_path=args.graph_edges_path,
            top_k=args.top_k,
            max_graph_paths_per_candidate=args.max_graph_paths_per_candidate,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "applicability-determine":
        result = build_applicability_decisions(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            authority_universe_path=args.authority_universe_path,
            package_fact_graph_path=args.package_fact_graph_path,
            package_applicability_context_path=args.package_applicability_context_path,
            retrieval_trace_path=args.retrieval_trace_path,
            graph_trace_path=args.graph_trace_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["validation_passed"] else 1

    if args.command == "applicability-validate":
        result = validate_applicability_run(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            authority_universe_path=args.authority_universe_path,
            package_fact_graph_path=args.package_fact_graph_path,
            package_applicability_context_path=args.package_applicability_context_path,
            package_fact_graph_validation_path=args.package_fact_graph_validation_path,
            retrieval_trace_path=args.retrieval_trace_path,
            graph_trace_path=args.graph_trace_path,
            decisions_path=args.decisions_path,
            applicable_authorities_path=args.applicable_authorities_path,
            non_applicable_authorities_path=args.non_applicable_authorities_path,
            search_coverage_certificates_path=args.search_coverage_certificates_path,
            provenance_path=args.provenance_path,
            validation_path=args.validation_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "applicability-adjudication-template":
        result = write_applicability_adjudication_template(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            decisions_path=args.decisions_path,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0

    if args.command == "applicability-adjudication-eval":
        result = evaluate_applicability_adjudication(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            adjudication_file=args.adjudication_file,
            decisions_path=args.decisions_path,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "applicability-adjudication-apply":
        result = apply_applicability_adjudication(
            output_dir=args.output_dir,
            review_id=args.review_id,
            source_set_id=args.source_set_id,
            adjudication_file=args.adjudication_file,
            decisions_path=args.decisions_path,
            applicable_authorities_path=args.applicable_authorities_path,
            non_applicable_authorities_path=args.non_applicable_authorities_path,
            provenance_path=args.provenance_path,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "applicability-generate-rule-pack":
        if args.validate_only:
            result = validate_generated_rule_pack(
                output_dir=args.output_dir,
                review_id=args.review_id,
                source_set_id=args.source_set_id,
                base_rule_pack_path=args.base_rule_pack,
                authority_universe_path=args.authority_universe_path,
                applicable_authorities_path=args.applicable_authorities_path,
                non_applicable_authorities_path=args.non_applicable_authorities_path,
                applicability_validation_path=args.applicability_validation_path,
                generated_rule_pack_path=args.output_path,
                validation_output_path=args.validation_output_path,
            )
        else:
            result = generate_applicability_rule_pack(
                output_dir=args.output_dir,
                review_id=args.review_id,
                source_set_id=args.source_set_id,
                base_rule_pack_path=args.base_rule_pack,
                authority_universe_path=args.authority_universe_path,
                decisions_path=args.decisions_path,
                applicable_authorities_path=args.applicable_authorities_path,
                non_applicable_authorities_path=args.non_applicable_authorities_path,
                applicability_validation_path=args.applicability_validation_path,
                output_path=args.output_path,
                validation_output_path=args.validation_output_path,
            )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    return None


def _add_review_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", default=Path("source_library"), type=Path)
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--source-set-id")
