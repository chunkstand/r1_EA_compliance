from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from usfs_r1_ea_sources import cli_eval
from usfs_r1_ea_sources import cli_review
from usfs_r1_ea_sources.cli import build_parser


def test_phase_eval_handler_propagates_catalog_dir(monkeypatch) -> None:
    captured = {}

    def fake_run_phase_aligned_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"reviewer_ready": True})

    monkeypatch.setattr(cli_eval, "run_phase_aligned_eval", fake_run_phase_aligned_eval)

    parser = build_parser()
    args = parser.parse_args(
        [
            "phase-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-1",
            "--catalog-dir",
            "archived-catalog",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("source_library")
    assert captured["source_set_id"] == "source-set-1"
    assert captured["catalog_dir"] == Path("archived-catalog")


def test_phase_eval_handler_propagates_review_id_only(monkeypatch) -> None:
    captured = {}

    def fake_run_phase_aligned_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"reviewer_ready": False})

    monkeypatch.setattr(cli_eval, "run_phase_aligned_eval", fake_run_phase_aligned_eval)

    parser = build_parser()
    args = parser.parse_args(
        [
            "phase-eval",
            "--output-dir",
            "source_library",
            "--review-id",
            "tracked-replay-review",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 1
    assert captured["output_dir"] == Path("source_library")
    assert captured["review_id"] == "tracked-replay-review"
    assert captured["source_set_id"] is None
    assert captured["catalog_dir"] is None


def test_eval_trace_inventory_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_eval_trace_inventory(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"command_succeeded": True})

    monkeypatch.setattr(cli_eval, "run_eval_trace_inventory", fake_run_eval_trace_inventory)

    parser = build_parser()
    args = parser.parse_args(
        [
            "eval-trace-inventory",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-f70ea11e04ae3d53",
            "--review-id",
            "west-reservoir-67436",
            "--catalog-dir",
            "catalog-gate",
            "--results-path",
            "inventory.json",
            "--format",
            "json",
            "--fail-on-missing-required",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured == {
        "output_dir": Path("source_library"),
        "source_set_id": "source-set-f70ea11e04ae3d53",
        "review_id": "west-reservoir-67436",
        "catalog_dir": Path("catalog-gate"),
        "results_path": Path("inventory.json"),
        "format": "json",
        "fail_on_missing_required": True,
    }


def test_eval_trace_store_build_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_eval_trace_store_build(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"command_succeeded": True})

    monkeypatch.setattr(
        cli_eval,
        "run_eval_trace_store_build",
        fake_run_eval_trace_store_build,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "eval-trace-store-build",
            "--inventory-path",
            "inventory.json",
            "--sqlite-path",
            "system_eval_trace.sqlite",
            "--summary-path",
            "summary.json",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured == {
        "inventory_path": Path("inventory.json"),
        "sqlite_path": Path("system_eval_trace.sqlite"),
        "summary_path": Path("summary.json"),
    }


def test_eval_trace_export_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_eval_trace_export(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"command_succeeded": True})

    monkeypatch.setattr(
        cli_eval,
        "run_eval_trace_export",
        fake_run_eval_trace_export,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "eval-trace-export",
            "--sqlite-path",
            "system_eval_trace.sqlite",
            "--canonical-json-path",
            "system_eval_trace_export.json",
            "--openinference-json-path",
            "openinference_traces.json",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured == {
        "sqlite_path": Path("system_eval_trace.sqlite"),
        "canonical_json_path": Path("system_eval_trace_export.json"),
        "openinference_json_path": Path("openinference_traces.json"),
    }


def test_source_record_identity_gate_handler_propagates_identity_options(monkeypatch) -> None:
    captured = {}

    def fake_run_source_record_identity_gate(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": False})

    monkeypatch.setattr(
        cli_eval,
        "run_source_record_identity_gate",
        fake_run_source_record_identity_gate,
    )

    parser = build_parser()
    args = parser.parse_args(
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

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 1
    assert captured["output_dir"] == Path("source_library")
    assert captured["source_set_id"] == "source-set-f70ea11e04ae3d53"
    assert captured["catalog_dir"] == Path(
        "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"
    )
    assert captured["eval_file"] == Path("config/v1_lolo_tylers_kitchen_real_ea_eval.json")
    assert captured["source_record_ids"] == ["R1EA-001"]
    assert captured["source_record_reconciliation_path"] == Path(
        "config/custom_source_record_reconciliation.json"
    )
    assert captured["forest_plan_identity_reconciliation_path"] == Path(
        "config/custom_forest_plan_identity_reconciliation.json"
    )


def test_promotion_suite_handler_propagates_manifest_and_strict_mode(monkeypatch) -> None:
    captured = {}

    def fake_run_promotion_suite(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"promotion_ready": True})

    monkeypatch.setattr(cli_eval, "run_promotion_suite", fake_run_promotion_suite)

    parser = build_parser()
    args = parser.parse_args(
        [
            "promotion-suite",
            "--output-dir",
            "library",
            "--manifest",
            "config/custom_suite.json",
            "--results-dir",
            "suite-results",
            "--strict-expansion",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["manifest_path"] == Path("config/custom_suite.json")
    assert captured["results_dir"] == Path("suite-results")
    assert captured["strict_expansion"] is True


def test_upstream_eval_handler_propagates_manifest_and_results_dir(monkeypatch) -> None:
    captured = {}

    def fake_run_upstream_evaluation(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(cli_eval, "run_upstream_evaluation", fake_run_upstream_evaluation)

    parser = build_parser()
    args = parser.parse_args(
        [
            "upstream-eval",
            "--manifest",
            "config/upstream_evaluation_v1.json",
            "--output-dir",
            "library",
            "--results-dir",
            "library/evaluations/upstream",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["manifest_path"] == Path("config/upstream_evaluation_v1.json")
    assert captured["output_dir"] == Path("library")
    assert captured["results_dir"] == Path("library/evaluations/upstream")


def test_extraction_fidelity_eval_handler_propagates_manifest_and_results_dir(
    monkeypatch,
) -> None:
    captured = {}

    def fake_run_extraction_fidelity_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_eval,
        "run_extraction_fidelity_eval",
        fake_run_extraction_fidelity_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "extraction-fidelity-eval",
            "--manifest",
            "config/extraction_fidelity_eval_v1.json",
            "--output-dir",
            "library",
            "--results-dir",
            "library/evaluations/extraction_fidelity",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["manifest_path"] == Path("config/extraction_fidelity_eval_v1.json")
    assert captured["output_dir"] == Path("library")
    assert captured["results_dir"] == Path("library/evaluations/extraction_fidelity")


def test_forest_plan_profile_eval_handler_propagates_manifest_and_results_dir(monkeypatch) -> None:
    captured = {}

    def fake_run_forest_plan_profile_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": False})

    monkeypatch.setattr(
        cli_eval,
        "run_forest_plan_profile_eval",
        fake_run_forest_plan_profile_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "forest-plan-profile-eval",
            "--manifest",
            "config/region1_forest_plan_profile_eval_coverage_v1.json",
            "--output-dir",
            "library",
            "--results-dir",
            "library/evaluations/forest_plan_profile",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 1
    assert captured["manifest_path"] == Path(
        "config/region1_forest_plan_profile_eval_coverage_v1.json"
    )
    assert captured["output_dir"] == Path("library")
    assert captured["results_dir"] == Path("library/evaluations/forest_plan_profile")


def test_forest_plan_component_retrieval_eval_handler_propagates_manifest_and_results_dir(
    monkeypatch,
) -> None:
    captured = {}

    def fake_run_forest_plan_component_retrieval_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_eval,
        "run_forest_plan_component_retrieval_eval",
        fake_run_forest_plan_component_retrieval_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "forest-plan-component-retrieval-eval",
            "--manifest",
            "config/forest_plan_component_retrieval_eval_v1.json",
            "--output-dir",
            "library",
            "--results-dir",
            "library/evaluations/forest_plan_component_retrieval",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["manifest_path"] == Path("config/forest_plan_component_retrieval_eval_v1.json")
    assert captured["output_dir"] == Path("library")
    assert captured["results_dir"] == Path(
        "library/evaluations/forest_plan_component_retrieval"
    )


def test_forest_plan_component_eval_handler_propagates_manifest(monkeypatch) -> None:
    captured = {}

    def fake_run_forest_plan_component_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_review,
        "run_forest_plan_component_eval",
        fake_run_forest_plan_component_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "forest-plan-component-eval",
            "--output-dir",
            "library",
            "--review-id",
            "west-reservoir-67436",
            "--manifest",
            "config/forest_plan_component_eval_coverage_v1.json",
        ]
    )

    result = cli_review.handle_review_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "west-reservoir-67436"
    assert captured["eval_file"] is None
    assert captured["manifest_path"] == Path("config/forest_plan_component_eval_coverage_v1.json")


def test_forest_plan_component_eval_coverage_handler_propagates_manifest_and_results_dir(
    monkeypatch,
) -> None:
    captured = {}

    def fake_run_forest_plan_component_eval_coverage(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_eval,
        "run_forest_plan_component_eval_coverage",
        fake_run_forest_plan_component_eval_coverage,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "forest-plan-component-eval-coverage",
            "--manifest",
            "config/forest_plan_component_eval_coverage_v1.json",
            "--output-dir",
            "library",
            "--results-dir",
            "library/evaluations/forest_plan_component_eval_coverage",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["manifest_path"] == Path("config/forest_plan_component_eval_coverage_v1.json")
    assert captured["output_dir"] == Path("library")
    assert captured["results_dir"] == Path("library/evaluations/forest_plan_component_eval_coverage")


def test_gold_coverage_eval_handler_propagates_manifest_and_results_dir(monkeypatch) -> None:
    captured = {}

    def fake_run_gold_coverage_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(cli_eval, "run_gold_coverage_eval", fake_run_gold_coverage_eval)

    parser = build_parser()
    args = parser.parse_args(
        [
            "gold-coverage-eval",
            "--manifest",
            "config/gold_coverage_v1.json",
            "--output-dir",
            "library",
            "--results-dir",
            "library/reviews/gold_coverage_eval",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["manifest_path"] == Path("config/gold_coverage_v1.json")
    assert captured["output_dir"] == Path("library")
    assert captured["results_dir"] == Path("library/reviews/gold_coverage_eval")


def test_forest_specific_example_package_eval_handler_propagates_manifest_and_results_dir(
    monkeypatch,
) -> None:
    captured = {}

    def fake_run_forest_specific_example_package_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_eval,
        "run_forest_specific_example_package_eval",
        fake_run_forest_specific_example_package_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "forest-specific-example-package-eval",
            "--output-dir",
            "library",
            "--manifest",
            "config/forest_specific_example_package_registry_v1.json",
            "--results-dir",
            "library/reviews/forest_specific_example_package_eval",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["manifest_path"] == Path(
        "config/forest_specific_example_package_registry_v1.json"
    )
    assert captured["results_dir"] == Path("library/reviews/forest_specific_example_package_eval")


def test_draft_generation_eval_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_draft_generation_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_eval,
        "run_draft_generation_eval",
        fake_run_draft_generation_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "draft-generation-eval",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--eval-file",
            "config/custom_draft_generation_eval.json",
            "--config",
            "config/custom_draft_generation.json",
            "--results-dir",
            "draft-eval-output",
        ]
    )

    result = cli_eval.handle_eval_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["eval_path"] == Path("config/custom_draft_generation_eval.json")
    assert captured["config_path"] == Path("config/custom_draft_generation.json")
    assert captured["results_dir"] == Path("draft-eval-output")
