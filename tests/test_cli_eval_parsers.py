from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.cli import build_parser


def test_phase_eval_parser_accepts_archived_catalog_dir() -> None:
    args = build_parser().parse_args(
        [
            "phase-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-4fb59e9eb43045cb",
            "--catalog-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
        ]
    )

    assert args.command == "phase-eval"
    assert args.catalog_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )


def test_source_record_identity_gate_parser_accepts_identity_inputs() -> None:
    args = build_parser().parse_args(
        [
            "source-record-identity-gate",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-f70ea11e04ae3d53",
            "--catalog-dir",
            "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate",
            "--eval-file",
            "config/v1_lolo_tylers_kitchen_real_ea_eval.json",
            "--source-record-id",
            "R1EA-001",
            "--source-record-reconciliation",
            "config/custom_source_record_reconciliation.json",
            "--forest-plan-identity-reconciliation",
            "config/custom_forest_plan_identity_reconciliation.json",
        ]
    )

    assert args.command == "source-record-identity-gate"
    assert args.output_dir == Path("source_library")
    assert args.source_set_id == "source-set-f70ea11e04ae3d53"
    assert args.catalog_dir == Path(
        "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"
    )
    assert args.eval_file == Path("config/v1_lolo_tylers_kitchen_real_ea_eval.json")
    assert args.source_record_ids == ["R1EA-001"]
    assert args.source_record_reconciliation == Path(
        "config/custom_source_record_reconciliation.json"
    )
    assert args.forest_plan_identity_reconciliation == Path(
        "config/custom_forest_plan_identity_reconciliation.json"
    )


def test_eval_trace_inventory_parser_accepts_inventory_scope_and_write_options() -> None:
    args = build_parser().parse_args(
        [
            "eval-trace-inventory",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-f70ea11e04ae3d53",
            "--review-id",
            "west-reservoir-67436",
            "--catalog-dir",
            "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate",
            "--results-path",
            "/tmp/eval-trace-inventory.md",
            "--format",
            "markdown",
            "--fail-on-missing-required",
        ]
    )

    assert args.command == "eval-trace-inventory"
    assert args.output_dir == Path("source_library")
    assert args.source_set_id == "source-set-f70ea11e04ae3d53"
    assert args.review_id == "west-reservoir-67436"
    assert args.catalog_dir == Path(
        "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"
    )
    assert args.results_path == Path("/tmp/eval-trace-inventory.md")
    assert args.format == "markdown"
    assert args.fail_on_missing_required is True


def test_eval_trace_store_build_parser_accepts_store_paths() -> None:
    args = build_parser().parse_args(
        [
            "eval-trace-store-build",
            "--inventory-path",
            "/tmp/usfs-r1-eval-trace-inventory.json",
            "--sqlite-path",
            "/tmp/usfs-r1-system-eval-trace.sqlite",
            "--summary-path",
            "/tmp/usfs-r1-system-eval-trace-summary.json",
        ]
    )

    assert args.command == "eval-trace-store-build"
    assert args.inventory_path == Path("/tmp/usfs-r1-eval-trace-inventory.json")
    assert args.sqlite_path == Path("/tmp/usfs-r1-system-eval-trace.sqlite")
    assert args.summary_path == Path("/tmp/usfs-r1-system-eval-trace-summary.json")


def test_eval_trace_export_parser_accepts_export_paths() -> None:
    args = build_parser().parse_args(
        [
            "eval-trace-export",
            "--sqlite-path",
            "/tmp/usfs-r1-system-eval-trace.sqlite",
            "--canonical-json-path",
            "/tmp/usfs-r1-system-eval-trace-export.json",
            "--openinference-json-path",
            "/tmp/usfs-r1-openinference-traces.json",
        ]
    )

    assert args.command == "eval-trace-export"
    assert args.sqlite_path == Path("/tmp/usfs-r1-system-eval-trace.sqlite")
    assert args.canonical_json_path == Path("/tmp/usfs-r1-system-eval-trace-export.json")
    assert args.openinference_json_path == Path("/tmp/usfs-r1-openinference-traces.json")


def test_eval_trace_case_promote_parser_accepts_promotion_contract() -> None:
    args = build_parser().parse_args(
        [
            "eval-trace-case-promote",
            "--sqlite-path",
            "/tmp/usfs-r1-system-eval-trace.sqlite",
            "--case-file",
            "config/eval_trace_cases/system_eval_trace_cases_v1.json",
            "--trace-id",
            "trace-123",
            "--span-id",
            "span-456",
            "--case-id",
            "west-reservoir-trace-case-001",
            "--owner",
            "eval_trace_case_promote",
            "--risk-level",
            "high",
            "--tag",
            "first-class-eval-trace",
            "--tag",
            "west-reservoir",
            "--assertion",
            "trace keeps source artifact refs",
            "--expected-output",
            "deterministic scorer contract remains replayable",
            "--review-condition",
            "review when scorer schema changes",
            "--removal-condition",
            "remove when superseded",
            "--human-label-status",
            "unlabeled",
        ]
    )

    assert args.command == "eval-trace-case-promote"
    assert args.sqlite_path == Path("/tmp/usfs-r1-system-eval-trace.sqlite")
    assert args.case_file == Path("config/eval_trace_cases/system_eval_trace_cases_v1.json")
    assert args.trace_id == "trace-123"
    assert args.span_id == "span-456"
    assert args.case_id == "west-reservoir-trace-case-001"
    assert args.owner == "eval_trace_case_promote"
    assert args.risk_level == "high"
    assert args.tags == ["first-class-eval-trace", "west-reservoir"]
    assert args.assertions == ["trace keeps source artifact refs"]
    assert args.expected_output == "deterministic scorer contract remains replayable"
    assert args.review_condition == "review when scorer schema changes"
    assert args.removal_condition == "remove when superseded"
    assert args.human_label_status == "unlabeled"


def test_eval_trace_case_file_validate_parser_accepts_case_file() -> None:
    args = build_parser().parse_args(
        [
            "eval-trace-case-file-validate",
            "--case-file",
            "config/eval_trace_cases/system_eval_trace_cases_v1.json",
            "--summary-path",
            "source_library/evaluations/eval_trace/eval_trace_case_file_validation.json",
            "--allow-empty",
        ]
    )

    assert args.command == "eval-trace-case-file-validate"
    assert args.case_file == Path("config/eval_trace_cases/system_eval_trace_cases_v1.json")
    assert args.summary_path == Path(
        "source_library/evaluations/eval_trace/eval_trace_case_file_validation.json"
    )
    assert args.require_cases is False


def test_upstream_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "upstream-eval",
            "--manifest",
            "config/upstream_evaluation_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/evaluations/upstream",
        ]
    )

    assert args.command == "upstream-eval"
    assert args.manifest == Path("config/upstream_evaluation_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/evaluations/upstream")


def test_extraction_fidelity_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "extraction-fidelity-eval",
            "--manifest",
            "config/extraction_fidelity_eval_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/evaluations/extraction_fidelity",
        ]
    )

    assert args.command == "extraction-fidelity-eval"
    assert args.manifest == Path("config/extraction_fidelity_eval_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/evaluations/extraction_fidelity")


def test_forest_plan_profile_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "forest-plan-profile-eval",
            "--manifest",
            "config/region1_forest_plan_profile_eval_coverage_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/evaluations/forest_plan_profile",
        ]
    )

    assert args.command == "forest-plan-profile-eval"
    assert args.manifest == Path("config/region1_forest_plan_profile_eval_coverage_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/evaluations/forest_plan_profile")


def test_forest_plan_component_retrieval_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "forest-plan-component-retrieval-eval",
            "--manifest",
            "config/forest_plan_component_retrieval_eval_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/evaluations/forest_plan_component_retrieval",
        ]
    )

    assert args.command == "forest-plan-component-retrieval-eval"
    assert args.manifest == Path("config/forest_plan_component_retrieval_eval_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/evaluations/forest_plan_component_retrieval")


def test_forest_plan_component_eval_coverage_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "forest-plan-component-eval-coverage",
            "--manifest",
            "config/forest_plan_component_eval_coverage_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/evaluations/forest_plan_component_eval_coverage",
        ]
    )

    assert args.command == "forest-plan-component-eval-coverage"
    assert args.manifest == Path("config/forest_plan_component_eval_coverage_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/evaluations/forest_plan_component_eval_coverage")


def test_forest_plan_component_eval_parser_accepts_manifest_without_eval_file() -> None:
    args = build_parser().parse_args(
        [
            "forest-plan-component-eval",
            "--output-dir",
            "source_library",
            "--review-id",
            "west-reservoir-67436",
            "--manifest",
            "config/forest_plan_component_eval_coverage_v1.json",
        ]
    )

    assert args.command == "forest-plan-component-eval"
    assert args.review_id == "west-reservoir-67436"
    assert args.eval_file is None
    assert args.manifest == Path("config/forest_plan_component_eval_coverage_v1.json")


def test_gold_coverage_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "gold-coverage-eval",
            "--manifest",
            "config/gold_coverage_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/reviews/gold_coverage_eval",
        ]
    )

    assert args.command == "gold-coverage-eval"
    assert args.manifest == Path("config/gold_coverage_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/reviews/gold_coverage_eval")


def test_real_package_review_coverage_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "real-package-review-coverage-eval",
            "--manifest",
            "config/v1_real_package_review_coverage_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/reviews/real_package_review_coverage_eval",
        ]
    )

    assert args.command == "real-package-review-coverage-eval"
    assert args.manifest == Path("config/v1_real_package_review_coverage_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/reviews/real_package_review_coverage_eval")


def test_forest_specific_example_package_eval_parser_accepts_manifest_and_results_dir() -> None:
    args = build_parser().parse_args(
        [
            "forest-specific-example-package-eval",
            "--manifest",
            "config/forest_specific_example_package_registry_v1.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/reviews/forest_specific_example_package_eval",
        ]
    )

    assert args.command == "forest-specific-example-package-eval"
    assert args.manifest == Path("config/forest_specific_example_package_registry_v1.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/reviews/forest_specific_example_package_eval")
