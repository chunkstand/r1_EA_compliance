from __future__ import annotations

from dataclasses import dataclass
import argparse
from pathlib import Path


@dataclass(frozen=True)
class DerivedArgumentSpec:
    flags: tuple[str, ...]
    kwargs: dict[str, object]


@dataclass(frozen=True)
class DerivedCommandSpec:
    name: str
    help: str
    arguments: tuple[DerivedArgumentSpec, ...]


@dataclass(frozen=True)
class DerivedCommandDefaults:
    output_dir: Path
    authority_ontology_eval_path: Path
    authority_ontology_path: Path
    authority_relationship_eval_path: Path
    authority_inventory_path: Path
    source_addition_decisions_path: Path
    claim_eval_path: Path
    verified_extraction_admission_contract_path: Path
    official_source_gap_evidence_path: Path
    r1_forest_plan_register_path: Path
    source_delta_batch_run_id: str
    graph_accuracy_eval_path: Path
    graph_health_contract_path: Path
    incremental_graph_refresh_eval_path: Path
    nepa_3d_graph_contract_path: Path
    authority_family_rule_templates_path: Path
    forest_plan_profiles_path: Path
    region1_forest_plan_readiness_path: Path
    rule_claim_eval_path: Path
    rule_pack_path: Path
    semantic_graph_eval_path: Path
    knowledge_graph_query_eval_path: Path
    source_register_proving_slice_manifest_path: Path
    source_partition_contract_path: Path
    chunk_sidecar_retrieval_eval_path: Path


def build_derived_command_specs(
    defaults: DerivedCommandDefaults,
) -> tuple[DerivedCommandSpec, ...]:
    def _arg(*flags: str, **kwargs) -> DerivedArgumentSpec:
        return DerivedArgumentSpec(flags=flags, kwargs=kwargs)

    def _output_dir_arg() -> DerivedArgumentSpec:
        return _arg("--output-dir", default=defaults.output_dir, type=Path)

    return (
        DerivedCommandSpec(
            name="extract-build",
            help="Build derived extracted text, chunks, and extraction diagnostics.",
            arguments=(
                _output_dir_arg(),
                _arg("--catalog-dir", type=Path),
                _arg("--id", action="append", dest="ids"),
                _arg("--parser"),
                _arg("--limit", type=int),
                _arg("--chunk-max-chars", type=int, default=1800),
                _arg("--chunk-overlap-chars", type=int, default=200),
                _arg("--prefer-docling", action="store_true"),
                _arg("--docling-ocr", action="store_true"),
                _arg("--docling-timeout-seconds", type=float, default=300.0),
                _arg("--allow-invalid-catalog", action="store_true"),
                _arg("--reuse-existing", action="store_true"),
                _arg("--reuse-inventory-path", type=Path),
                _arg("--merge-selected-into-existing", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="reuse-inventory",
            help="Inventory reusable extraction records without running extraction or review commands.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--catalog-dir", type=Path),
                _arg(
                    "--previous-source-set-id",
                    action="append",
                    dest="previous_source_set_ids",
                ),
                _arg("--catalog-path", type=Path),
                _arg("--skip-artifact-hash-check", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="forest-plan-source-delta-readiness",
            help="Build the Region 1 forest-plan source-delta readiness baseline report.",
            arguments=(
                _output_dir_arg(),
                _arg(
                    "--r1-forest-plan-register",
                    default=defaults.r1_forest_plan_register_path,
                    type=Path,
                ),
                _arg(
                    "--source-delta-batch-run-id",
                    default=defaults.source_delta_batch_run_id,
                ),
                _arg("--scoped-catalog-gate-dir", type=Path),
                _arg("--merged-catalog-gate-dir", type=Path),
                _arg("--canonical-catalog-dir", type=Path),
                _arg("--extraction-source-set-id"),
                _arg("--reuse-inventory-path", type=Path),
                _arg(
                    "--forest-plan-profiles",
                    default=defaults.forest_plan_profiles_path,
                    type=Path,
                ),
                _arg(
                    "--official-source-gap-evidence",
                    default=defaults.official_source_gap_evidence_path,
                    type=Path,
                ),
                _arg("--results-dir", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="extraction-accuracy-audit",
            help="Run deterministic extraction accuracy checks against generated extraction outputs.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--output-path", type=Path),
                _arg(
                    "--contract-path",
                    default=defaults.verified_extraction_admission_contract_path,
                    type=Path,
                ),
            ),
        ),
        DerivedCommandSpec(
            name="chunk-quality-audit",
            help="Report chunk boundary, parser, layout, and parent-context risk by source.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--chunks-path", type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="chunk-layer-build",
            help="Build sidecar atomic, structural, and parent context chunk layers.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--chunks-path", type=Path),
                _arg("--chunks-v2-dir", type=Path),
                _arg("--atomic-max-tokens", type=int, default=600),
                _arg("--parent-window-max-tokens", type=int, default=1500),
            ),
        ),
        DerivedCommandSpec(
            name="source-register-proving-slice",
            help="Run the Phase 1.5 mixed proving slice over the canonical source register.",
            arguments=(
                _arg("--workbook", required=True, type=Path),
                _arg(
                    "--manifest",
                    default=defaults.source_register_proving_slice_manifest_path,
                    type=Path,
                ),
                _output_dir_arg(),
                _arg("--config", default=Path("config/downloader.toml"), type=Path),
                _arg("--report-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="authority-currentness",
            help="Build a source-currentness validation report for the authority-family inventory.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg(
                    "--authority-inventory",
                    default=defaults.authority_inventory_path,
                    type=Path,
                ),
                _arg(
                    "--source-addition-decisions",
                    default=defaults.source_addition_decisions_path,
                    type=Path,
                ),
                _arg(
                    "--source-partition-contract",
                    default=defaults.source_partition_contract_path,
                    type=Path,
                ),
                _arg("--catalog-path", type=Path),
                _arg("--source-set-manifest-path", type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="authority-ontology-validate",
            help="Validate authority ontology coverage and canonical knowledge-graph representation.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--ontology-path", default=defaults.authority_ontology_path, type=Path),
                _arg(
                    "--eval-path",
                    default=defaults.authority_ontology_eval_path,
                    type=Path,
                ),
                _arg(
                    "--graph-contract-path",
                    default=defaults.nepa_3d_graph_contract_path,
                    type=Path,
                ),
                _arg("--graph-path", type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="authority-relationship-eval",
            help="Validate proving-slice semantic relationship coverage and endpoint rules.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--report-path", type=Path),
                _arg(
                    "--eval-path",
                    default=defaults.authority_relationship_eval_path,
                    type=Path,
                ),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="citation-alias-eval",
            help="Validate proving-slice alias resolution and blocked-alias context handling.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--report-path", type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="graph-health-eval",
            help="Validate proving-slice graph health metrics and required lenses.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--report-path", type=Path),
                _arg(
                    "--contract-path",
                    default=defaults.graph_health_contract_path,
                    type=Path,
                ),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="graph-accuracy-eval",
            help="Validate proving-slice graph node classes, lenses, and justification paths.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--report-path", type=Path),
                _arg("--eval-path", default=defaults.graph_accuracy_eval_path, type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="semantic-graph-eval",
            help="Run aggregate direct eval for the canonical semantic knowledge graph.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--eval-path", default=defaults.semantic_graph_eval_path, type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="incremental-graph-refresh-eval",
            help="Validate controlled source-change and supersession visibility on the canonical graph lane.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg(
                    "--eval-path",
                    default=defaults.incremental_graph_refresh_eval_path,
                    type=Path,
                ),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="retrieval-build",
            help="Build a local evidence retrieval index from extracted chunks.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--chunks-path", type=Path),
                _arg("--index-dir", type=Path),
                _arg("--catalog-dir", type=Path),
                _arg("--catalog-sqlite-path", type=Path),
                _arg("--allow-failed-extraction", action="store_true"),
                _arg("--allow-partial-extraction", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="retrieval-query",
            help="Query the local evidence index and print provenance-bearing evidence spans.",
            arguments=(
                _arg("query"),
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--index-path", type=Path),
                _arg("--limit", type=int, default=5),
                _arg("--document-role"),
                _arg("--support-document-role"),
                _arg("--authority-level"),
                _arg("--source-record-id"),
                _arg("--review-topic"),
                _arg("--citation"),
                _arg("--host"),
            ),
        ),
        DerivedCommandSpec(
            name="retrieval-eval",
            help="Run the evidence retrieval eval set against a local retrieval index.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--index-path", type=Path),
                _arg("--eval-file", default=Path("config/retrieval_eval_seed.json"), type=Path),
                _arg("--top-k", type=int, default=5),
                _arg("--results-dir", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="chunk-sidecar-retrieval-eval",
            help="Compare sidecar atomic chunk retrieval against the baseline retrieval index.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg(
                    "--eval-file",
                    default=defaults.chunk_sidecar_retrieval_eval_path,
                    type=Path,
                ),
                _arg("--chunks-v2-dir", type=Path),
                _arg("--sidecar-index-dir", type=Path),
                _arg("--baseline-index-path", type=Path),
                _arg("--results-dir", type=Path),
                _arg("--top-k", type=int, default=5),
                _arg("--rebuild-sidecar", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="evidence-graph-build",
            help="Build a document evidence graph from extracted chunks and retrieval metadata.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--catalog-dir", type=Path),
                _arg("--allow-partial-retrieval", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="nepa-knowledge-graph-export",
            help="Build the source-set NEPA 3D knowledge graph export from audited artifacts.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--review-id"),
                _arg(
                    "--graph-contract",
                    default=defaults.nepa_3d_graph_contract_path,
                    type=Path,
                ),
                _arg(
                    "--authority-inventory",
                    default=defaults.authority_inventory_path,
                    type=Path,
                ),
                _arg(
                    "--authority-family-rule-templates",
                    default=defaults.authority_family_rule_templates_path,
                    type=Path,
                ),
                _arg(
                    "--forest-plan-profiles",
                    default=defaults.forest_plan_profiles_path,
                    type=Path,
                ),
                _arg(
                    "--region1-forest-plan-readiness",
                    default=defaults.region1_forest_plan_readiness_path,
                    type=Path,
                ),
                _arg("--rule-pack", default=defaults.rule_pack_path, type=Path),
                _arg("--catalog-path", type=Path),
                _arg("--catalog-graph-nodes-path", type=Path),
                _arg("--catalog-graph-edges-path", type=Path),
                _arg("--source-set-manifest-path", type=Path),
                _arg("--authority-currentness-path", type=Path),
                _arg("--evidence-graph-nodes-path", type=Path),
                _arg("--evidence-graph-edges-path", type=Path),
                _arg("--claims-path", type=Path),
                _arg("--rule-claim-links-path", type=Path),
                _arg("--forest-plan-components-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="knowledge-graph-query",
            help="Query the NEPA knowledge graph export with provenance and freshness warnings.",
            arguments=(
                _arg("query", nargs="?"),
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--review-id"),
                _arg(
                    "--query-type",
                    default="keyword",
                    choices=(
                        "keyword",
                        "node_id",
                        "node_type",
                        "edge_type",
                        "source_record",
                        "citation",
                        "forest_unit",
                        "readiness_blocker",
                    ),
                ),
                _arg("--graph-path", type=Path),
                _arg("--output-path", type=Path),
                _arg("--limit", type=int, default=10),
                _arg("--node-type"),
                _arg("--edge-type"),
                _arg("--source-record-id"),
                _arg("--forest-unit-id"),
                _arg("--citation"),
                _arg("--readiness-status"),
                _arg("--require-hit", action="store_true"),
                _arg("--fail-on-freshness-warning", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="knowledge-graph-query-eval",
            help="Run deterministic query-level evals against the NEPA knowledge graph surface.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--review-id"),
                _arg(
                    "--eval-path",
                    default=defaults.knowledge_graph_query_eval_path,
                    type=Path,
                ),
                _arg("--graph-path", type=Path),
                _arg("--output-path", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="claim-extract",
            help="Extract deterministic source-text claims and entity graph artifacts from chunks.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--chunks-path", type=Path),
                _arg("--catalog-sqlite-path", type=Path),
                _arg("--allow-partial-retrieval", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="claim-eval",
            help="Run deterministic eval cases against extracted source claims.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--claims-path", type=Path),
                _arg("--eval-file", default=defaults.claim_eval_path, type=Path),
                _arg("--top-k", type=int, default=5),
                _arg("--results-dir", type=Path),
            ),
        ),
        DerivedCommandSpec(
            name="rule-claim-link",
            help="Build deterministic links from compliance rules to validated source claims.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--claims-path", type=Path),
                _arg("--rule-pack", default=defaults.rule_pack_path, type=Path),
                _arg("--top-k", type=int, default=5),
                _arg("--allow-partial-claims", action="store_true"),
            ),
        ),
        DerivedCommandSpec(
            name="rule-claim-eval",
            help="Run deterministic eval cases against rule-to-source-claim links.",
            arguments=(
                _output_dir_arg(),
                _arg("--source-set-id"),
                _arg("--links-path", type=Path),
                _arg("--rule-pack", default=defaults.rule_pack_path, type=Path),
                _arg("--eval-file", default=defaults.rule_claim_eval_path, type=Path),
                _arg("--top-k", type=int, default=5),
                _arg("--results-dir", type=Path),
            ),
        ),
    )


def register_derived_command_specs(
    subparsers: argparse._SubParsersAction,
    command_specs: tuple[DerivedCommandSpec, ...],
) -> None:
    for command_spec in command_specs:
        parser = subparsers.add_parser(command_spec.name, help=command_spec.help)
        for argument_spec in command_spec.arguments:
            parser.add_argument(*argument_spec.flags, **argument_spec.kwargs)
