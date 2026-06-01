from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from usfs_r1_ea_sources import cli_derived
from usfs_r1_ea_sources.cli import build_parser


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


def test_incremental_graph_refresh_eval_parser_accepts_options() -> None:
    args = build_parser().parse_args(
        [
            "incremental-graph-refresh-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--eval-path",
            "config/custom_incremental_graph_refresh_eval.json",
            "--output-path",
            "source_library/evaluations/incremental_graph_refresh/custom_results.json",
        ]
    )

    assert args.command == "incremental-graph-refresh-eval"
    assert args.output_dir == Path("source_library")
    assert args.source_set_id == "source-set-test"
    assert args.eval_path == Path("config/custom_incremental_graph_refresh_eval.json")
    assert args.output_path == Path(
        "source_library/evaluations/incremental_graph_refresh/custom_results.json"
    )


def test_extract_build_parser_accepts_archived_catalog_dir() -> None:
    args = build_parser().parse_args(
        [
            "extract-build",
            "--output-dir",
            "source_library",
            "--catalog-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
            "--reuse-existing",
            "--merge-selected-into-existing",
        ]
    )

    assert args.command == "extract-build"
    assert args.catalog_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )
    assert args.reuse_existing is True
    assert args.merge_selected_into_existing is True


def test_source_register_proving_slice_parser_accepts_manifest_and_workbook() -> None:
    args = build_parser().parse_args(
        [
            "source-register-proving-slice",
            "--workbook",
            "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx",
            "--manifest",
            "config/source_register_proving_slice_v1.json",
            "--output-dir",
            "source_library",
        ]
    )

    assert args.command == "source-register-proving-slice"
    assert args.workbook == Path("usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx")
    assert args.manifest == Path("config/source_register_proving_slice_v1.json")
    assert args.output_dir == Path("source_library")


def test_semantic_eval_parsers_accept_phase_1_5_paths() -> None:
    ontology_args = build_parser().parse_args(
        [
            "authority-ontology-validate",
            "--output-dir",
            "source_library",
            "--ontology-path",
            "config/authority_document_ontology_v1.json",
            "--eval-path",
            "config/authority_ontology_eval_v1.json",
        ]
    )
    relationship_args = build_parser().parse_args(
        [
            "authority-relationship-eval",
            "--output-dir",
            "source_library",
            "--eval-path",
            "config/authority_relationship_eval_v1.json",
        ]
    )
    alias_args = build_parser().parse_args(
        [
            "citation-alias-eval",
            "--output-dir",
            "source_library",
        ]
    )
    graph_health_args = build_parser().parse_args(
        [
            "graph-health-eval",
            "--output-dir",
            "source_library",
            "--contract-path",
            "config/graph_health_contract_v1.json",
        ]
    )
    graph_accuracy_args = build_parser().parse_args(
        [
            "graph-accuracy-eval",
            "--output-dir",
            "source_library",
            "--eval-path",
            "config/graph_accuracy_eval_v1.json",
        ]
    )
    semantic_graph_args = build_parser().parse_args(
        [
            "semantic-graph-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-f70ea11e04ae3d53",
            "--eval-path",
            "config/semantic_graph_direct_eval_v1.json",
        ]
    )
    graph_query_args = build_parser().parse_args(
        [
            "knowledge-graph-query",
            "FED-001",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-f70ea11e04ae3d53",
            "--query-type",
            "source_record",
            "--require-hit",
        ]
    )
    graph_query_eval_args = build_parser().parse_args(
        [
            "knowledge-graph-query-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-f70ea11e04ae3d53",
            "--eval-path",
            "config/knowledge_graph_query_eval_v1.json",
        ]
    )

    assert ontology_args.command == "authority-ontology-validate"
    assert ontology_args.ontology_path == Path("config/authority_document_ontology_v1.json")
    assert ontology_args.eval_path == Path("config/authority_ontology_eval_v1.json")
    assert relationship_args.command == "authority-relationship-eval"
    assert relationship_args.eval_path == Path("config/authority_relationship_eval_v1.json")
    assert alias_args.command == "citation-alias-eval"
    assert graph_health_args.contract_path == Path("config/graph_health_contract_v1.json")
    assert graph_accuracy_args.eval_path == Path("config/graph_accuracy_eval_v1.json")
    assert semantic_graph_args.command == "semantic-graph-eval"
    assert semantic_graph_args.source_set_id == "source-set-f70ea11e04ae3d53"
    assert semantic_graph_args.eval_path == Path("config/semantic_graph_direct_eval_v1.json")
    assert graph_query_args.command == "knowledge-graph-query"
    assert graph_query_args.query == "FED-001"
    assert graph_query_args.query_type == "source_record"
    assert graph_query_args.require_hit is True
    assert graph_query_eval_args.command == "knowledge-graph-query-eval"
    assert graph_query_eval_args.eval_path == Path("config/knowledge_graph_query_eval_v1.json")


def test_extraction_accuracy_audit_parser_accepts_contract_path() -> None:
    args = build_parser().parse_args(
        [
            "extraction-accuracy-audit",
            "--output-dir",
            "source_library",
            "--contract-path",
            "config/verified_extraction_admission_contract.json",
        ]
    )

    assert args.command == "extraction-accuracy-audit"
    assert args.output_dir == Path("source_library")
    assert args.contract_path == Path("config/verified_extraction_admission_contract.json")


def test_chunk_quality_audit_parser_accepts_optional_paths() -> None:
    args = build_parser().parse_args(
        [
            "chunk-quality-audit",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-test",
            "--chunks-path",
            "/tmp/chunks.jsonl",
            "--output-path",
            "/tmp/chunk-quality-audit.json",
        ]
    )

    assert args.command == "chunk-quality-audit"
    assert args.output_dir == Path("source_library")
    assert args.source_set_id == "source-set-test"
    assert args.chunks_path == Path("/tmp/chunks.jsonl")
    assert args.output_path == Path("/tmp/chunk-quality-audit.json")


def test_retrieval_build_parser_accepts_archived_catalog_dir() -> None:
    args = build_parser().parse_args(
        [
            "retrieval-build",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-4fb59e9eb43045cb",
            "--catalog-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
        ]
    )

    assert args.command == "retrieval-build"
    assert args.catalog_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )


def test_evidence_graph_build_parser_accepts_archived_catalog_dir() -> None:
    args = build_parser().parse_args(
        [
            "evidence-graph-build",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-4fb59e9eb43045cb",
            "--catalog-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
            "--allow-partial-retrieval",
        ]
    )

    assert args.command == "evidence-graph-build"
    assert args.catalog_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )
    assert args.allow_partial_retrieval is True


def test_retrieval_query_parser_accepts_support_document_role_filter() -> None:
    args = build_parser().parse_args(
        [
            "retrieval-query",
            "flathead revised land management plan 2018",
            "--output-dir",
            "source_library",
            "--support-document-role",
            "primary_land_management_plan",
        ]
    )

    assert args.command == "retrieval-query"
    assert args.support_document_role == "primary_land_management_plan"


def test_reuse_inventory_parser_accepts_archived_catalog_dir() -> None:
    args = build_parser().parse_args(
        [
            "reuse-inventory",
            "--output-dir",
            "source_library",
            "--catalog-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
        ]
    )

    assert args.command == "reuse-inventory"
    assert args.catalog_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )


def test_rule_claim_link_parser_accepts_allow_partial_claims() -> None:
    args = build_parser().parse_args(
        [
            "rule-claim-link",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-4fb59e9eb43045cb",
            "--allow-partial-claims",
        ]
    )

    assert args.command == "rule-claim-link"
    assert args.allow_partial_claims is True


def test_forest_plan_source_delta_readiness_parser_accepts_sequence_four_inputs() -> None:
    args = build_parser().parse_args(
        [
            "forest-plan-source-delta-readiness",
            "--output-dir",
            "source_library",
            "--merged-catalog-gate-dir",
            "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate",
            "--extraction-source-set-id",
            "source-set-4fb59e9eb43045cb",
            "--reuse-inventory-path",
            "source_library/derived/source-set-4fb59e9eb43045cb/reuse_inventory/reuse_inventory.json",
        ]
    )

    assert args.command == "forest-plan-source-delta-readiness"
    assert args.merged_catalog_gate_dir == Path(
        "source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate"
    )
    assert args.extraction_source_set_id == "source-set-4fb59e9eb43045cb"
    assert args.reuse_inventory_path == Path(
        "source_library/derived/source-set-4fb59e9eb43045cb/reuse_inventory/reuse_inventory.json"
    )


def test_evidence_graph_build_handler_propagates_catalog_dir(monkeypatch) -> None:
    captured = {}

    def fake_build_evidence_graph(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"validation_passed": True})

    monkeypatch.setattr(cli_derived, "build_evidence_graph", fake_build_evidence_graph)

    parser = build_parser()
    args = parser.parse_args(
        [
            "evidence-graph-build",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-1",
            "--catalog-dir",
            "archived-catalog",
        ]
    )

    result = cli_derived.handle_derived_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("source_library")
    assert captured["source_set_id"] == "source-set-1"
    assert captured["catalog_dir"] == Path("archived-catalog")


def test_rule_claim_link_handler_propagates_allow_partial_claims(monkeypatch) -> None:
    captured = {}

    def fake_build_rule_claim_links(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"validation_passed": True})

    monkeypatch.setattr(cli_derived, "build_rule_claim_links", fake_build_rule_claim_links)

    parser = build_parser()
    args = parser.parse_args(
        [
            "rule-claim-link",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-1",
            "--allow-partial-claims",
        ]
    )

    result = cli_derived.handle_derived_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("source_library")
    assert captured["source_set_id"] == "source-set-1"
    assert captured["allow_partial_claims"] is True


def test_incremental_graph_refresh_eval_handler_propagates_options(monkeypatch) -> None:
    captured = {}

    def fake_run_incremental_graph_refresh_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_derived,
        "run_incremental_graph_refresh_eval",
        fake_run_incremental_graph_refresh_eval,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "incremental-graph-refresh-eval",
            "--output-dir",
            "library",
            "--source-set-id",
            "source-set-1",
            "--eval-path",
            "config/custom_incremental_graph_refresh_eval.json",
            "--output-path",
            "incremental-output/results.json",
        ]
    )

    result = cli_derived.handle_derived_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["source_set_id"] == "source-set-1"
    assert captured["eval_path"] == Path("config/custom_incremental_graph_refresh_eval.json")
    assert captured["output_path"] == Path("incremental-output/results.json")


def test_knowledge_graph_query_handler_propagates_contract_options(monkeypatch) -> None:
    captured = {}

    def fake_run_knowledge_graph_query(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"passed": True})

    monkeypatch.setattr(
        cli_derived,
        "run_knowledge_graph_query",
        fake_run_knowledge_graph_query,
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "knowledge-graph-query",
            "FED-001",
            "--output-dir",
            "library",
            "--source-set-id",
            "source-set-1",
            "--query-type",
            "source_record",
            "--graph-path",
            "graph.json",
            "--output-path",
            "query-output.json",
            "--limit",
            "3",
            "--require-hit",
            "--fail-on-freshness-warning",
        ]
    )

    result = cli_derived.handle_derived_command(args, parser)

    assert result == 0
    assert captured["output_dir"] == Path("library")
    assert captured["source_set_id"] == "source-set-1"
    assert captured["query"] == "FED-001"
    assert captured["query_type"] == "source_record"
    assert captured["graph_path"] == Path("graph.json")
    assert captured["output_path"] == Path("query-output.json")
    assert captured["limit"] == 3
    assert captured["require_hit"] is True
    assert captured["fail_on_freshness_warning"] is True
