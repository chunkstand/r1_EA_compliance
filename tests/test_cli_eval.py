from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from usfs_r1_ea_sources import cli_eval
from usfs_r1_ea_sources import cli_review
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
