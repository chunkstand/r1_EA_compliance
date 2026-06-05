from __future__ import annotations

import argparse
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from usfs_r1_ea_sources import cli_capture
from usfs_r1_ea_sources import cli_compliance
from usfs_r1_ea_sources import cli_decision_support
from usfs_r1_ea_sources import cli_document_planning
from usfs_r1_ea_sources import cli_final_qa
from usfs_r1_ea_sources import cli_review_packet
from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.config import SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT


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
            "--rule-claim-links-path",
            "source_library/derived/source-set-1/rule_claim_links_sidecar/unit/0.1.0/rule_claim_links.jsonl",
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
    assert args.rule_claim_links_path == Path(
        "source_library/derived/source-set-1/rule_claim_links_sidecar/unit/0.1.0/rule_claim_links.jsonl"
    )
    assert args.rule_pack == Path("config/compliance_rule_pack_nepa_ea_v0.json")


def test_compliance_review_parser_accepts_forest_plan_profile_selection() -> None:
    args = build_parser().parse_args(
        [
            "compliance-review",
            "--package-path",
            "package",
            "--forest-unit-id",
            "beaverhead-deerlodge-nf",
            "--forest-plan-profiles-path",
            "config/forest_plan_profiles.json",
            "--forest-plan-component-inventory-path",
            "source_library/reviews/review/component_inventory.json",
        ]
    )

    assert args.command == "compliance-review"
    assert args.forest_unit_id == "beaverhead-deerlodge-nf"
    assert args.forest_plan_profiles_path == Path("config/forest_plan_profiles.json")
    assert args.forest_plan_component_inventory_path == Path(
        "source_library/reviews/review/component_inventory.json"
    )


def test_compliance_review_parser_accepts_flathead_profile_selection() -> None:
    args = build_parser().parse_args(
        [
            "compliance-review",
            "--package-path",
            "package",
            "--forest-unit-id",
            "flathead-nf",
            "--forest-plan-profiles-path",
            "config/forest_plan_profiles.json",
        ]
    )

    assert args.command == "compliance-review"
    assert args.forest_unit_id == "flathead-nf"
    assert args.forest_plan_profiles_path == Path("config/forest_plan_profiles.json")


def test_box_folder_intake_parser_accepts_selection_prefixes() -> None:
    args = build_parser().parse_args(
        [
            "box-folder-intake",
            "--root-folder-url",
            "https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225",
            "--review-id",
            "region1-example-nez-perce-clearwater-dead-laundry-57827",
            "--download",
            "--include-relative-path-prefix",
            "Analysis/Final EA 2023",
            "--include-relative-path-prefix",
            "Decision/2024 Final Decision and EA",
        ]
    )

    assert args.command == "box-folder-intake"
    assert args.root_folder_url == (
        "https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225"
    )
    assert args.review_id == "region1-example-nez-perce-clearwater-dead-laundry-57827"
    assert args.download is True
    assert args.include_relative_path_prefixes == [
        "Analysis/Final EA 2023",
        "Decision/2024 Final Decision and EA",
    ]


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


def test_capture_parser_accepts_repeated_ids_for_targeted_runs() -> None:
    args = build_parser().parse_args(
        [
            "download",
            "--workbook",
            "workbook.xlsx",
            "--id",
            "R1-SCC-NPC-004",
            "--id",
            "R1-SCC-NPC-005",
        ]
    )

    assert args.command == "download"
    assert args.id == ["R1-SCC-NPC-004", "R1-SCC-NPC-005"]


def test_source_delta_options_reject_register_under_canonical_loader(capsys) -> None:
    parser = argparse.ArgumentParser(prog="preflight")
    args = SimpleNamespace(
        r1_forest_plan_register=Path("config/r1_forest_plan_document_register_draft.csv"),
        source_delta_only=True,
    )

    with pytest.raises(SystemExit) as exc:
        cli_capture._source_delta_options(
            args,
            parser,
            SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT,
        )

    assert exc.value.code == 2
    assert "sole active source ledger" in capsys.readouterr().err


def test_source_register_validate_parser_accepts_phase_zero_contract_paths() -> None:
    args = build_parser().parse_args(
        [
            "source-register-validate",
            "--workbook",
            "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
            "--mode",
            "schema",
            "--sheet-contract",
            "config/source_register_sheet_contract_v1.json",
            "--schema-path",
            "config/source_register_schema_v1.json",
            "--vocabularies-path",
            "config/source_register_vocabularies_v1.json",
            "--row-states-path",
            "config/source_register_row_states_v1.json",
        ]
    )

    assert args.command == "source-register-validate"
    assert args.workbook == Path("usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx")
    assert args.mode == "schema"
    assert args.sheet_contract == Path("config/source_register_sheet_contract_v1.json")
    assert args.schema_path == Path("config/source_register_schema_v1.json")
    assert args.vocabularies_path == Path("config/source_register_vocabularies_v1.json")
    assert args.row_states_path == Path("config/source_register_row_states_v1.json")


def test_source_register_diff_parser_accepts_phase_zero_inputs() -> None:
    args = build_parser().parse_args(
        [
            "source-register-diff",
            "--legacy-workbook",
            "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx",
            "--legacy-register",
            "config/r1_forest_plan_document_register_draft.csv",
            "--canonical-workbook",
            "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
            "--sheet-contract",
            "config/source_register_sheet_contract_v1.json",
        ]
    )

    assert args.command == "source-register-diff"
    assert args.legacy_workbook == Path("usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx")
    assert args.legacy_register == Path("config/r1_forest_plan_document_register_draft.csv")
    assert args.canonical_workbook == Path("usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx")
    assert args.sheet_contract == Path("config/source_register_sheet_contract_v1.json")


def test_source_register_queue_audit_parser_accepts_ledger_inputs() -> None:
    args = build_parser().parse_args(
        [
            "source-register-queue-audit",
            "--workbook",
            "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
            "--ledger-path",
            "config/source_register_queue_resolution_ledger_v1.json",
            "--sheet-contract",
            "config/source_register_sheet_contract_v1.json",
        ]
    )

    assert args.command == "source-register-queue-audit"
    assert args.workbook == Path("usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx")
    assert args.ledger_path == Path("config/source_register_queue_resolution_ledger_v1.json")
    assert args.sheet_contract == Path("config/source_register_sheet_contract_v1.json")


def test_chunk_accuracy_parser_accepts_audit_and_sidecar_commands() -> None:
    audit_args = build_parser().parse_args(
        [
            "chunk-quality-audit",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--chunks-path",
            "chunks.jsonl",
        ]
    )
    layer_args = build_parser().parse_args(
        [
            "chunk-layer-build",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--atomic-max-tokens",
            "256",
        ]
    )

    assert audit_args.command == "chunk-quality-audit"
    assert audit_args.chunks_path == Path("chunks.jsonl")
    assert layer_args.command == "chunk-layer-build"
    assert layer_args.atomic_max_tokens == 256


def test_chunk_sidecar_retrieval_eval_parser_accepts_comparison_paths() -> None:
    args = build_parser().parse_args(
        [
            "chunk-sidecar-retrieval-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--chunks-v2-dir",
            "chunks_v2",
            "--sidecar-index-dir",
            "retrieval_sidecar",
            "--baseline-index-path",
            "retrieval/evidence_index.sqlite",
            "--results-dir",
            "retrieval_sidecar_eval",
            "--top-k",
            "10",
            "--rebuild-sidecar",
        ]
    )

    assert args.command == "chunk-sidecar-retrieval-eval"
    assert args.chunks_v2_dir == Path("chunks_v2")
    assert args.sidecar_index_dir == Path("retrieval_sidecar")
    assert args.baseline_index_path == Path("retrieval/evidence_index.sqlite")
    assert args.results_dir == Path("retrieval_sidecar_eval")
    assert args.top_k == 10
    assert args.rebuild_sidecar is True


def test_chunk_sidecar_consumer_eval_parser_accepts_preview_paths() -> None:
    args = build_parser().parse_args(
        [
            "chunk-sidecar-consumer-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--chunks-v2-dir",
            "chunks_v2",
            "--sidecar-index-dir",
            "retrieval_sidecar",
            "--graph-dir",
            "consumer_eval/evidence_graph_sidecar",
            "--claims-dir",
            "consumer_eval/claims_sidecar",
            "--baseline-graph-summary-path",
            "evidence_graph/summary.json",
            "--baseline-claim-summary-path",
            "claims/summary.json",
            "--results-dir",
            "consumer_sidecar_eval",
            "--rebuild-sidecar",
            "--allow-partial-extraction",
            "--allow-partial-retrieval",
        ]
    )

    assert args.command == "chunk-sidecar-consumer-eval"
    assert args.chunks_v2_dir == Path("chunks_v2")
    assert args.sidecar_index_dir == Path("retrieval_sidecar")
    assert args.graph_dir == Path("consumer_eval/evidence_graph_sidecar")
    assert args.claims_dir == Path("consumer_eval/claims_sidecar")
    assert args.baseline_graph_summary_path == Path("evidence_graph/summary.json")
    assert args.baseline_claim_summary_path == Path("claims/summary.json")
    assert args.results_dir == Path("consumer_sidecar_eval")
    assert args.rebuild_sidecar is True
    assert args.allow_partial_extraction is True
    assert args.allow_partial_retrieval is True


def test_graph_and_claim_parsers_accept_sidecar_consumer_paths() -> None:
    graph_args = build_parser().parse_args(
        [
            "evidence-graph-build",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--chunks-path",
            "chunks_v2/atomic_chunks.jsonl",
            "--retrieval-validation-path",
            "retrieval_sidecar/retrieval_validation.json",
            "--retrieval-summary-path",
            "retrieval_sidecar/summary.json",
            "--graph-dir",
            "evidence_graph_sidecar",
        ]
    )
    claim_args = build_parser().parse_args(
        [
            "claim-extract",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--chunks-path",
            "chunks_v2/atomic_chunks.jsonl",
            "--retrieval-validation-path",
            "retrieval_sidecar/retrieval_validation.json",
            "--retrieval-summary-path",
            "retrieval_sidecar/summary.json",
            "--claims-dir",
            "claims_sidecar",
        ]
    )

    assert graph_args.command == "evidence-graph-build"
    assert graph_args.chunks_path == Path("chunks_v2/atomic_chunks.jsonl")
    assert graph_args.retrieval_validation_path == Path(
        "retrieval_sidecar/retrieval_validation.json"
    )
    assert graph_args.retrieval_summary_path == Path("retrieval_sidecar/summary.json")
    assert graph_args.graph_dir == Path("evidence_graph_sidecar")
    assert claim_args.command == "claim-extract"
    assert claim_args.chunks_path == Path("chunks_v2/atomic_chunks.jsonl")
    assert claim_args.retrieval_validation_path == Path(
        "retrieval_sidecar/retrieval_validation.json"
    )
    assert claim_args.retrieval_summary_path == Path("retrieval_sidecar/summary.json")
    assert claim_args.claims_dir == Path("claims_sidecar")


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
            "--forest-plan-component-inventory-path",
            "source_library/reviews/review/component_inventory.json",
            "--rule-claim-links-path",
            "source_library/derived/source-set-1/rule_claim_links_sidecar/unit/0.1.0/rule_claim_links.jsonl",
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
    assert captured["rule_claim_links_path"] == Path(
        "source_library/derived/source-set-1/rule_claim_links_sidecar/unit/0.1.0/rule_claim_links.jsonl"
    )
    assert captured["component_inventory_path"] == Path(
        "source_library/reviews/review/component_inventory.json"
    )


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


def test_draft_generate_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_draft_generate(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_decision_support,
        "run_draft_generate",
        fake_run_draft_generate,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "draft-generate",
            "--output-dir",
            "library",
            "--review-id",
            "review-1",
            "--config",
            "config/custom_draft_generation.json",
            "--results-dir",
            "draft-output",
        ]
    )

    result = cli_decision_support.handle_decision_support_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["review_id"] == "review-1"
    assert captured["config_path"] == Path("config/custom_draft_generation.json")
    assert captured["results_dir"] == Path("draft-output")


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


def test_final_qa_direct_eval_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_final_qa_direct_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_final_qa,
        "run_final_qa_direct_eval",
        fake_run_final_qa_direct_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "final-qa-direct-eval",
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


def test_document_plan_parser_accepts_paths() -> None:
    args = build_parser().parse_args(
        [
            "document-plan",
            "--request",
            "request.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/document_plans/request-1",
            "--lane-registry",
            "config/document_lanes_v1.json",
            "--request-schema",
            "docs/schemas/document_request_v1.schema.json",
        ]
    )

    assert args.command == "document-plan"
    assert args.request == Path("request.json")
    assert args.output_dir == Path("source_library")
    assert args.results_dir == Path("source_library/document_plans/request-1")
    assert args.lane_registry == Path("config/document_lanes_v1.json")
    assert args.request_schema == Path("docs/schemas/document_request_v1.schema.json")


def test_document_plan_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_document_plan(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_document_planning,
        "run_document_plan",
        fake_run_document_plan,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "document-plan",
            "--request",
            "request.json",
            "--output-dir",
            "source_library",
            "--results-dir",
            "source_library/document_plans/request-1",
            "--lane-registry",
            "config/document_lanes_v1.json",
            "--request-schema",
            "docs/schemas/document_request_v1.schema.json",
        ]
    )

    result = cli_document_planning.handle_document_planning_command(args, parser)

    assert result == 0
    assert captured["request_path"] == Path("request.json")
    assert captured["output_dir"] == Path("source_library")
    assert captured["results_dir"] == Path("source_library/document_plans/request-1")
    assert captured["lane_registry_path"] == Path("config/document_lanes_v1.json")
    assert captured["request_schema_path"] == Path("docs/schemas/document_request_v1.schema.json")


def _registered_commands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("No subparser action found")
