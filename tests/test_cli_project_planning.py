from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from usfs_r1_ea_sources import cli_project_planning
from usfs_r1_ea_sources.cli import build_parser


def test_project_sow_package_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_package(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_package",
        fake_run_project_sow_package,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-package",
            "--intake",
            "config/intake.json",
            "--output-dir",
            "library",
            "--project-id",
            "project-1",
            "--source-set-id",
            "source-set-1",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
            "--results-dir",
            "sow-output",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["intake_path"] == Path("config/intake.json")
    assert captured["output_dir"] == Path("library")
    assert captured["project_id"] == "project-1"
    assert captured["source_set_id"] == "source-set-1"
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")
    assert captured["results_dir"] == Path("sow-output")


def test_project_sow_package_handler_propagates_validate_only(monkeypatch) -> None:
    captured = {}

    def fake_validate_project_sow_intake(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "validate_project_sow_intake",
        fake_validate_project_sow_intake,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-package",
            "--intake",
            "config/intake.json",
            "--project-id",
            "project-1",
            "--source-set-id",
            "source-set-1",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
            "--validate-only",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["intake_path"] == Path("config/intake.json")
    assert captured["project_id"] == "project-1"
    assert captured["source_set_id"] == "source-set-1"
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")
    assert "output_dir" not in captured
    assert "results_dir" not in captured


def test_project_sow_intake_validate_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_validate_project_sow_intake(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "validate_project_sow_intake",
        fake_validate_project_sow_intake,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-intake-validate",
            "--intake",
            "config/intake.json",
            "--project-id",
            "project-1",
            "--source-set-id",
            "source-set-1",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["intake_path"] == Path("config/intake.json")
    assert captured["project_id"] == "project-1"
    assert captured["source_set_id"] == "source-set-1"
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")


def test_project_sow_intake_draft_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_intake_draft(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_intake_draft",
        fake_run_project_sow_intake_draft,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-intake-draft",
            "--proposed-action",
            "proposed-action.txt",
            "--output",
            "draft-intake.json",
            "--project-id",
            "project-1",
            "--project-name",
            "Project One",
            "--forest",
            "Example National Forest",
            "--district",
            "North District",
            "--district",
            "South District",
            "--project-type",
            "land_exchange",
            "--nepa-level",
            "environmental_assessment",
            "--source-title",
            "Proposed Action Narrative",
            "--draft-rules",
            "config/draft-rules.json",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["proposed_action_path"] == Path("proposed-action.txt")
    assert captured["output_path"] == Path("draft-intake.json")
    assert captured["project_id"] == "project-1"
    assert captured["project_name"] == "Project One"
    assert captured["forest"] == "Example National Forest"
    assert captured["districts"] == ["North District", "South District"]
    assert captured["project_type"] == "land_exchange"
    assert captured["nepa_level"] == "environmental_assessment"
    assert captured["source_title"] == "Proposed Action Narrative"
    assert captured["draft_rules_config_path"] == Path("config/draft-rules.json")
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")


def test_project_sow_eval_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_eval",
        fake_run_project_sow_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-eval",
            "--eval-config",
            "config/eval.json",
            "--output-dir",
            "/tmp/project-sow-eval",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["eval_config_path"] == Path("config/eval.json")
    assert captured["output_dir"] == Path("/tmp/project-sow-eval")
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")


def test_project_sow_operational_gate_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_operational_gate(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_operational_gate",
        fake_run_project_sow_operational_gate,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-operational-gate",
            "--output-dir",
            "/tmp/project-sow-operational-gate",
            "--eval-config",
            "config/eval.json",
            "--template-intake",
            "config/template.json",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
            "--handoff-rules",
            "config/handoff-rules.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("/tmp/project-sow-operational-gate")
    assert captured["eval_config_path"] == Path("config/eval.json")
    assert captured["template_intake_path"] == Path("config/template.json")
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")
    assert captured["handoff_rules_config_path"] == Path("config/handoff-rules.json")


def test_project_sow_ea_package_handoff_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_ea_package_handoff(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_ea_package_handoff",
        fake_run_project_sow_ea_package_handoff,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-ea-package-handoff",
            "--package",
            "project_sow_package.json",
            "--output",
            "project_sow_ea_package_handoff.json",
            "--markdown-output",
            "project_sow_ea_package_handoff.md",
            "--handoff-rules",
            "config/project_sow_ea_handoff_rules_v1.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["package_path"] == Path("project_sow_package.json")
    assert captured["output_path"] == Path("project_sow_ea_package_handoff.json")
    assert captured["markdown_path"] == Path("project_sow_ea_package_handoff.md")
    assert captured["handoff_rules_config_path"] == Path(
        "config/project_sow_ea_handoff_rules_v1.json"
    )


def test_project_sow_adjudication_template_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_write_project_sow_adjudication_template(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "write_project_sow_adjudication_template",
        fake_write_project_sow_adjudication_template,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-adjudication-template",
            "--intake",
            "config/intake.json",
            "--output-dir",
            "library",
            "--project-id",
            "project-1",
            "--source-set-id",
            "source-set-1",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
            "--results-dir",
            "adjudication-output",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["intake_path"] == Path("config/intake.json")
    assert captured["output_dir"] == Path("library")
    assert captured["project_id"] == "project-1"
    assert captured["source_set_id"] == "source-set-1"
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")
    assert captured["results_dir"] == Path("adjudication-output")


def test_project_sow_adjudication_eval_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_adjudication_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_adjudication_eval",
        fake_run_project_sow_adjudication_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-adjudication-eval",
            "--intake",
            "config/intake.json",
            "--adjudication",
            "adjudication.json",
            "--output",
            "adjudication-eval.json",
            "--project-id",
            "project-1",
            "--source-set-id",
            "source-set-1",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["intake_path"] == Path("config/intake.json")
    assert captured["adjudication_path"] == Path("adjudication.json")
    assert captured["output_path"] == Path("adjudication-eval.json")
    assert captured["project_id"] == "project-1"
    assert captured["source_set_id"] == "source-set-1"
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")


def test_project_sow_adjudication_apply_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_project_sow_adjudication_apply(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_project_planning,
        "run_project_sow_adjudication_apply",
        fake_run_project_sow_adjudication_apply,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "project-sow-adjudication-apply",
            "--intake",
            "config/intake.json",
            "--adjudication",
            "adjudication.json",
            "--output-intake",
            "adjudicated-intake.json",
            "--output",
            "adjudication-apply.json",
            "--eval-output",
            "adjudication-eval.json",
            "--project-id",
            "project-1",
            "--source-set-id",
            "source-set-1",
            "--resource-scope-config",
            "config/scopes.json",
            "--authority-inventory",
            "config/authorities.json",
        ]
    )

    result = cli_project_planning.handle_project_planning_command(args, parser)

    assert result == 0
    assert captured["intake_path"] == Path("config/intake.json")
    assert captured["adjudication_path"] == Path("adjudication.json")
    assert captured["output_intake_path"] == Path("adjudicated-intake.json")
    assert captured["output_path"] == Path("adjudication-apply.json")
    assert captured["eval_output_path"] == Path("adjudication-eval.json")
    assert captured["project_id"] == "project-1"
    assert captured["source_set_id"] == "source-set-1"
    assert captured["resource_scope_config_path"] == Path("config/scopes.json")
    assert captured["authority_inventory_path"] == Path("config/authorities.json")
