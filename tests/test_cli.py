from __future__ import annotations

import argparse
import tomllib
from pathlib import Path
from types import SimpleNamespace

from usfs_r1_ea_sources import cli_compliance
from usfs_r1_ea_sources import cli_eval
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


def _registered_commands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("No subparser action found")
