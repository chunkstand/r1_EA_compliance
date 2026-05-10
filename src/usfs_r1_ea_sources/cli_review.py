from __future__ import annotations

from pathlib import Path
import argparse

from .cli_common import normalized_timeout
from .cli_common import print_summary
from .ea_review import DEFAULT_CHECKLIST_PATH
from .ea_review import run_ea_review
from .forest_plan_component_adjudication import (
    run_forest_plan_component_adjudication_eval,
    write_forest_plan_component_adjudication_template,
)
from .forest_plan_component_eval import DEFAULT_FOREST_PLAN_COMPONENT_EVAL_PATH
from .forest_plan_component_eval import run_forest_plan_component_eval
from .forest_plan_components import build_forest_plan_component_inventory
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_inventory_build_manifest import (
    DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
)
from .forest_plan_resolver import DEFAULT_FOREST_PLAN_PROFILE_ID
from .forest_plan_resolver import run_forest_plan_resolver


REVIEW_COMMANDS = {
    "ea-review",
    "forest-plan-components-build",
    "forest-plan-component-adjudication-template",
    "forest-plan-component-adjudication-eval",
    "forest-plan-component-eval",
    "forest-plan-resolve",
}


def register_review_commands(subparsers: argparse._SubParsersAction) -> None:
    ea_review = subparsers.add_parser(
        "ea-review",
        help="Run a deterministic, evidence-backed EA package checklist review.",
    )
    ea_review.add_argument("--package-path", required=True, type=Path)
    _add_review_output_args(ea_review)
    ea_review.add_argument("--index-path", type=Path)
    ea_review.add_argument("--checklist", default=DEFAULT_CHECKLIST_PATH, type=Path)
    ea_review.add_argument("--source-top-k", type=int, default=3)
    ea_review.add_argument("--package-top-k", type=int, default=3)
    ea_review.add_argument("--chunk-max-chars", type=int, default=1800)
    ea_review.add_argument("--chunk-overlap-chars", type=int, default=200)
    ea_review.add_argument("--reuse-package-cache", action="store_true")
    ea_review.add_argument("--docling-ocr", action="store_true")
    ea_review.add_argument("--docling-timeout-seconds", type=float, default=120.0)

    components = subparsers.add_parser(
        "forest-plan-components-build",
        help="Build a source-traced forest-plan component inventory from extracted plan chunks.",
    )
    components.add_argument("--output-dir", default=Path("source_library"), type=Path)
    components.add_argument("--source-set-id", required=True)
    components.add_argument("--source-record-id")
    components.add_argument("--forest-unit-id")
    components.add_argument("--plan-version")
    components.add_argument("--chunks-path", type=Path)
    components.add_argument("--geographic-area-id", action="append", dest="geographic_area_ids")
    components.add_argument("--management-area-id", action="append", dest="management_area_ids")
    components.add_argument("--overlay-id", action="append", dest="overlay_ids")
    components.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        const=DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH,
        nargs="?",
        help=(
            "Build from the tracked Region 1 inventory manifest. Omit the value to use the "
            "default manifest path."
        ),
    )

    adjudication_template = subparsers.add_parser(
        "forest-plan-component-adjudication-template",
        help="Export a reviewer-fillable forest-plan component adjudication template.",
    )
    _add_review_lookup_args(adjudication_template)
    adjudication_template.add_argument("--output-path", type=Path)

    adjudication_eval = subparsers.add_parser(
        "forest-plan-component-adjudication-eval",
        help="Evaluate completed forest-plan component adjudications against current artifacts.",
    )
    _add_review_lookup_args(adjudication_eval)
    adjudication_eval.add_argument("--adjudication-file", type=Path)
    adjudication_eval.add_argument("--output-path", type=Path)

    component_eval = subparsers.add_parser(
        "forest-plan-component-eval",
        help="Evaluate forest-plan component findings against adjudicated component cases.",
    )
    _add_review_lookup_args(component_eval)
    component_eval.add_argument(
        "--eval-file",
        default=DEFAULT_FOREST_PLAN_COMPONENT_EVAL_PATH,
        type=Path,
    )
    component_eval.add_argument("--output-path", type=Path)

    resolver = subparsers.add_parser(
        "forest-plan-resolve",
        help="Resolve profile-driven forest-plan context from a local EA package.",
    )
    resolver.add_argument("--package-path", required=True, type=Path)
    _add_review_output_args(resolver)
    resolver.add_argument("--forest-unit-id", default=DEFAULT_FOREST_PLAN_PROFILE_ID)
    resolver.add_argument(
        "--forest-plan-profiles-path",
        default=DEFAULT_FOREST_PLAN_PROFILES_PATH,
        type=Path,
    )
    resolver.add_argument("--index-path", type=Path)
    resolver.add_argument("--source-top-k", type=int, default=2)
    resolver.add_argument("--chunk-max-chars", type=int, default=1800)
    resolver.add_argument("--chunk-overlap-chars", type=int, default=200)
    resolver.add_argument("--forest-plan-component-inventory-path", type=Path)
    resolver.add_argument("--reuse-package-cache", action="store_true")
    resolver.add_argument("--docling-ocr", action="store_true")
    resolver.add_argument("--docling-timeout-seconds", type=float, default=120.0)


def handle_review_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int | None:
    if args.command == "ea-review":
        result = run_ea_review(
            package_path=args.package_path,
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            checklist_path=args.checklist,
            review_id=args.review_id,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            package_top_k=args.package_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=normalized_timeout(args.docling_timeout_seconds),
            reuse_package_cache=args.reuse_package_cache,
        )
        print_summary(result.summary)
        return 0 if result.summary["reviewer_ready"] else 1

    if args.command == "forest-plan-components-build":
        if args.manifest_path is None:
            if not args.source_record_id or not args.plan_version:
                parser.error(
                    "forest-plan-components-build requires --source-record-id and "
                    "--plan-version unless --manifest-path is provided."
                )
        else:
            if args.source_record_id or args.plan_version:
                parser.error(
                    "forest-plan-components-build does not accept --source-record-id or "
                    "--plan-version when --manifest-path is provided."
                )
            if args.geographic_area_ids or args.management_area_ids or args.overlay_ids:
                parser.error(
                    "forest-plan-components-build does not accept geographic or overlay id "
                    "overrides when --manifest-path is provided."
                )
        result = build_forest_plan_component_inventory(
            output_dir=args.output_dir,
            source_set_id=args.source_set_id,
            source_record_id=args.source_record_id,
            forest_unit_id=(
                args.forest_unit_id
                if args.manifest_path is not None
                else (args.forest_unit_id or DEFAULT_FOREST_PLAN_PROFILE_ID)
            ),
            plan_version=args.plan_version,
            chunks_path=args.chunks_path,
            geographic_area_ids=args.geographic_area_ids,
            management_area_ids=args.management_area_ids,
            overlay_ids=args.overlay_ids,
            manifest_path=args.manifest_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "forest-plan-component-adjudication-template":
        result = write_forest_plan_component_adjudication_template(
            output_dir=args.output_dir,
            review_id=args.review_id,
            review_dir=args.review_dir,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0

    if args.command == "forest-plan-component-adjudication-eval":
        result = run_forest_plan_component_adjudication_eval(
            output_dir=args.output_dir,
            review_id=args.review_id,
            review_dir=args.review_dir,
            adjudication_file=args.adjudication_file,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "forest-plan-component-eval":
        result = run_forest_plan_component_eval(
            output_dir=args.output_dir,
            review_id=args.review_id,
            review_dir=args.review_dir,
            eval_file=args.eval_file,
            output_path=args.output_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["passed"] else 1

    if args.command == "forest-plan-resolve":
        result = run_forest_plan_resolver(
            package_path=args.package_path,
            output_dir=args.output_dir,
            forest_unit_id=args.forest_unit_id,
            profiles_path=args.forest_plan_profiles_path,
            source_set_id=args.source_set_id,
            index_path=args.index_path,
            review_id=args.review_id,
            results_dir=args.results_dir,
            source_top_k=args.source_top_k,
            chunk_max_chars=args.chunk_max_chars,
            chunk_overlap_chars=args.chunk_overlap_chars,
            docling_ocr=args.docling_ocr,
            docling_timeout_seconds=normalized_timeout(args.docling_timeout_seconds),
            reuse_package_cache=args.reuse_package_cache,
            component_inventory_path=args.forest_plan_component_inventory_path,
        )
        print_summary(result.summary)
        return 0 if result.summary["reviewer_ready"] else 1

    return None


def _add_review_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", default=Path("source_library"), type=Path)
    parser.add_argument("--source-set-id")
    parser.add_argument("--review-id")
    parser.add_argument("--results-dir", type=Path)


def _add_review_lookup_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", default=Path("source_library"), type=Path)
    parser.add_argument("--review-id")
    parser.add_argument("--review-dir", type=Path)
