from __future__ import annotations

import argparse
import tomllib
from pathlib import Path
from types import SimpleNamespace

from usfs_r1_ea_sources import cli_compliance
from usfs_r1_ea_sources import cli_decision_support
from usfs_r1_ea_sources import cli_eval
from usfs_r1_ea_sources import cli_final_qa
from usfs_r1_ea_sources import cli_project_planning
from usfs_r1_ea_sources import cli_review_packet
from usfs_r1_ea_sources.cli import build_parser


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "docs" / "architecture_contract.toml"


def test_contract_command_groups_match_registered_commands() -> None:
    parser = build_parser()
    registered = _registered_commands(parser)
    contract = tomllib.loads(CONTRACT_PATH.read_text())
    expected = {
        command
        for group in contract["command_groups"]
        for command in group.get("commands", [])
    }

    assert expected == registered


def test_compliance_review_parser_preserves_authority_gate_options() -> None:
    args = build_parser().parse_args(
        [
            "compliance-review",
            "--package-path",
            "package",
            "--allow-base-rule-pack-review",
            "--reuse-package-cache",
            "--docling-timeout-seconds",
            "0",
        ]
    )

    assert args.command == "compliance-review"
    assert args.allow_base_rule_pack_review is True
    assert args.reuse_package_cache is True
    assert args.docling_timeout_seconds == 0.0
    assert args.rule_pack == Path("config/compliance_rule_pack_nepa_ea_v0.json")


def test_capture_parser_accepts_r1_forest_plan_source_delta_register() -> None:
    args = build_parser().parse_args(
        [
            "preflight",
            "--workbook",
            "workbook.xlsx",
            "--r1-forest-plan-register",
            "config/r1_forest_plan_document_register_draft.csv",
            "--source-delta-only",
        ]
    )

    assert args.command == "preflight"
    assert args.r1_forest_plan_register == Path("config/r1_forest_plan_document_register_draft.csv")
    assert args.source_delta_only is True


def test_batch_download_parser_accepts_r1_forest_plan_source_delta_register() -> None:
    args = build_parser().parse_args(
        [
            "batch-download",
            "--workbook",
            "workbook.xlsx",
            "--r1-forest-plan-register",
            "config/r1_forest_plan_document_register_draft.csv",
            "--source-delta-only",
            "--plan-only",
        ]
    )

    assert args.command == "batch-download"
    assert args.r1_forest_plan_register == Path("config/r1_forest_plan_document_register_draft.csv")
    assert args.source_delta_only is True
    assert args.plan_only is True


def test_catalog_build_parser_accepts_r1_forest_plan_source_delta_register() -> None:
    args = build_parser().parse_args(
        [
            "catalog-build",
            "--workbook",
            "workbook.xlsx",
            "--batch-run-id",
            "canonical-batches",
            "--batch-run-id",
            "r1-delta-batches",
            "--catalog-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
            "--r1-forest-plan-register",
            "config/r1_forest_plan_document_register_draft.csv",
            "--source-delta-only",
        ]
    )

    assert args.command == "catalog-build"
    assert args.batch_run_id == ["canonical-batches", "r1-delta-batches"]
    assert args.catalog_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )
    assert args.r1_forest_plan_register == Path("config/r1_forest_plan_document_register_draft.csv")
    assert args.source_delta_only is True


def test_forest_plan_source_delta_readiness_parser_accepts_sequence_zero_inputs() -> None:
    args = build_parser().parse_args(
        [
            "forest-plan-source-delta-readiness",
            "--output-dir",
            "source_library",
            "--r1-forest-plan-register",
            "config/r1_forest_plan_document_register_draft.csv",
            "--source-delta-batch-run-id",
            "r1-delta-batches",
            "--official-source-gap-evidence",
            "config/r1_forest_plan_official_source_gap_evidence.json",
        ]
    )

    assert args.command == "forest-plan-source-delta-readiness"
    assert args.output_dir == Path("source_library")
    assert args.r1_forest_plan_register == Path("config/r1_forest_plan_document_register_draft.csv")
    assert args.source_delta_batch_run_id == "r1-delta-batches"
    assert args.official_source_gap_evidence == Path(
        "config/r1_forest_plan_official_source_gap_evidence.json"
    )


def test_compliance_review_handler_propagates_authority_gate_options(monkeypatch) -> None:
    captured = {}

    def fake_run_compliance_review(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"reviewer_ready": True})

    monkeypatch.setattr(cli_compliance, "run_compliance_review", fake_run_compliance_review)

    parser = build_parser()
    args = parser.parse_args(
        [
            "compliance-review",
            "--package-path",
            "package",
            "--allow-base-rule-pack-review",
            "--reuse-package-cache",
            "--docling-timeout-seconds",
            "0",
        ]
    )

    result = cli_compliance.handle_compliance_command(args, parser)

    assert result == 0
    assert captured["allow_base_rule_pack_review"] is True
    assert captured["reuse_package_cache"] is True
    assert captured["docling_timeout_seconds"] is None
    assert captured["package_path"] == Path("package")


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


def test_decision_support_handler_propagates_report_options(monkeypatch) -> None:
    captured = {}

    def fake_run_ea_consistency_decision_support(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_decision_support,
        "run_ea_consistency_decision_support",
        fake_run_ea_consistency_decision_support,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "ea-consistency-document",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--config",
            "config/custom_decision_support.json",
            "--expected-summary",
            "config/custom_expected_summary.json",
            "--results-dir",
            "decision-output",
        ]
    )

    result = cli_decision_support.handle_decision_support_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["config_path"] == Path("config/custom_decision_support.json")
    assert captured["expected_summary_path"] == Path("config/custom_expected_summary.json")
    assert captured["results_dir"] == Path("decision-output")


def test_decision_support_handler_propagates_validate_only(monkeypatch) -> None:
    captured = {}

    def fake_validate_ea_consistency_decision_support_report(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_decision_support,
        "validate_ea_consistency_decision_support_report",
        fake_validate_ea_consistency_decision_support_report,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "ea-consistency-document",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--config",
            "config/custom_decision_support.json",
            "--expected-summary",
            "config/custom_expected_summary.json",
            "--results-dir",
            "decision-output",
            "--validate-only",
        ]
    )

    result = cli_decision_support.handle_decision_support_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["config_path"] == Path("config/custom_decision_support.json")
    assert captured["expected_summary_path"] == Path("config/custom_expected_summary.json")
    assert captured["results_dir"] == Path("decision-output")


def test_final_qa_handler_propagates_report_options(monkeypatch) -> None:
    captured = {}

    def fake_run_final_qa_certification(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_final_qa,
        "run_final_qa_certification",
        fake_run_final_qa_certification,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "final-qa-certification",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--config",
            "config/custom_final_qa.json",
            "--expected-summary",
            "config/custom_final_qa_expected_summary.json",
            "--results-dir",
            "final-qa-output",
        ]
    )

    result = cli_final_qa.handle_final_qa_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["config_path"] == Path("config/custom_final_qa.json")
    assert captured["expected_summary_path"] == Path(
        "config/custom_final_qa_expected_summary.json"
    )
    assert captured["results_dir"] == Path("final-qa-output")


def test_final_qa_handler_propagates_validate_only(monkeypatch) -> None:
    captured = {}

    def fake_validate_final_qa_certification_report(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_final_qa,
        "validate_final_qa_certification_report",
        fake_validate_final_qa_certification_report,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "final-qa-certification",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--config",
            "config/custom_final_qa.json",
            "--expected-summary",
            "config/custom_final_qa_expected_summary.json",
            "--results-dir",
            "final-qa-output",
            "--validate-only",
        ]
    )

    result = cli_final_qa.handle_final_qa_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["config_path"] == Path("config/custom_final_qa.json")
    assert captured["expected_summary_path"] == Path(
        "config/custom_final_qa_expected_summary.json"
    )
    assert captured["results_dir"] == Path("final-qa-output")


def test_review_packet_index_handler_propagates_report_options(monkeypatch) -> None:
    captured = {}

    def fake_run_review_packet_index(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_review_packet,
        "run_review_packet_index",
        fake_run_review_packet_index,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "review-packet-index",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--results-dir",
            "review-packet-output",
        ]
    )

    result = cli_review_packet.handle_review_packet_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["results_dir"] == Path("review-packet-output")


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


def _registered_commands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("No subparser action found")
