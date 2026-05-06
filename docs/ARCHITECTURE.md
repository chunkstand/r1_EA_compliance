# Architecture

Date: 2026-05-04

This repository is a local CLI system for building an auditable USDA Forest Service Region 1 EA
source library and deterministic reviewer engine. The workbook is the source contract. The code
turns workbook rows into captured artifacts, derived evidence, validated authority applicability,
compliance findings, reports, and eval gates.

The architecture is intentionally artifact-first. Each layer reads explicit inputs, writes durable
outputs under `source_library/`, and exposes validation artifacts that later layers must respect.
Generated outputs remain ignored by git unless repository policy changes.

## System Context

```text
Workbook and config
  -> local source capture
  -> reviewer catalog
  -> extraction and retrieval
  -> evidence graph and source claims
  -> rule packs and rule-claim binding
  -> package facts and applicability
  -> EA, forest-plan, and compliance review
  -> decision support reports
  -> eval and promotion gates
  -> CLI entrypoints for operators and agents
```

Primary users are operators, reviewers, and coding agents working locally. External web pages,
downloaded documents, PDFs, and package documents are untrusted evidence inputs. They are not
instructions for agents or privileged tools.

## Containers

| Container | Role | Current Module Owners |
| --- | --- | --- |
| Workbook/config | Load workbook rows, overrides, settings, record identity, and source-partition contracts. | `workbook.py`, `records.py`, `source_partitions.py`, `config.py`, `overrides.py`, `adapters.py` |
| Capture | Dry-run, preflight, download, batch, report, and run validation. | `dry_run.py`, `preflight.py`, `download.py`, `batches.py`, `report.py`, `validate_run.py`, `pilots.py` |
| Catalog | Promote workbook rows and artifacts into reviewer-facing catalog surfaces. | `catalog.py` |
| Extraction/retrieval | Build text chunks, accuracy checks, and local evidence indexes. | `extract.py`, `extraction_accuracy.py`, `retrieval.py` |
| Review support | Build cross-source-set reuse planning artifacts that may inspect forest-plan review requirements without writing review outputs. | `reuse_inventory.py` |
| Evidence and claims | Build graph and source-claim layers used by later rule and review gates. | `evidence_graph.py`, `claim_extraction.py`, `rule_claim_binding.py` |
| NEPA 3D knowledge graph | Define and assemble source-set graph exports for visualization over audited artifacts. | `nepa_3d_graph_contract.py`, `nepa_knowledge_graph_export.py` |
| Applicability | Build package facts, retrieve/trace authority evidence, decide applicability, validate and adjudicate decisions, and generate applicability rule packs. | `package_fact_graph.py`, `applicability*.py` |
| Review | Run EA checklist review and forest-plan context/component review. | `ea_review.py`, `forest_plan_*.py` |
| Compliance | Produce citation-bearing compliance findings, matrices, finding graphs, coverage, and gold evals. | `compliance_review.py`, `compliance_inputs.py`, `compliance_outputs.py`, `compliance_coverage.py`, `compliance_gold_eval.py` |
| Decision support | Generate supervisor-facing EA consistency synthesis reports from audited review artifacts without replacing validation gates or legal judgment. | `ea_consistency_decision_support.py` |
| Eval | Score promoted review contracts, applicability quality, and manifest-driven promotion readiness. | `applicability_eval.py`, `promotion_suite.py`, `v1_ea_eval.py` |
| CLI | Stable public command surface. | `cli.py`, `__main__.py`, `cli_*.py` |

The machine-readable contract for these containers is
`docs/architecture_contract.toml`. That contract is the input to the architecture fitness test and
is the source of truth for module ownership, import boundaries, generated artifact ownership, public
command groups, and temporary exceptions.

## Component Flow

### Workbook And Capture

The workbook and config layer owns row identity, scope, URL overrides, and local downloader
configuration. Capture commands may read workbook/config helpers and produce manifests, run ledgers,
operator reports, and repair queues. Capture code must not infer reviewer behavior from raw
filenames or generated review artifacts.

### Catalog, Extraction, Retrieval

Catalog code owns reviewer catalog surfaces:

- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`
- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_graph_nodes.jsonl`
- `source_library/catalog/source_graph_edges.jsonl`

Extraction reads catalog records and raw artifacts, then writes derived text/chunk surfaces under
`source_library/derived/<source_set_id>/`. Retrieval reads extracted chunks and writes the evidence
index and validation outputs. Reuse planning is a review-support helper because it can inspect
forest-plan source-set requirements while writing only reuse inventory artifacts. Raw artifacts are
source bytes and provenance only; semantic work starts in derived layers.

Catalog records also carry `source_partition` and `source_partition_basis`. These fields distinguish
active review-corpus records from currentness/supersession archive records and candidate or blocked
records before graph-export work joins catalog, currentness, evidence, claim, applicability, and
finding artifacts.

The NEPA 3D graph contract and source-set exporter are owned separately from the document evidence
graph. They define and build the source-set visualization schema over audited artifacts; export
commands must read catalog, derived, applicability, and compliance surfaces rather than raw
filenames.

### Evidence, Claims, And Rule Packs

The evidence graph and source-claim layers convert extracted/retrieved evidence into graph and
claim artifacts. Rule-claim binding connects versioned compliance rule packs to validated source
claims before compliance findings can rely on them.

Shared rule-pack loading and validation are upstream concerns owned by `rule_packs.py`. Rule
binding, applicability, generated-rule-pack validation, compliance coverage, and compliance evals
import shared rule-pack behavior from that neutral module rather than from downstream compliance
review.

### Applicability Before Compliance

Applicability is a pre-review authority selection contract. It writes package facts, retrieval
traces, graph traces, applicability decisions, non-applicable authorities, search coverage
certificates, validation, adjudication, and generated rule-pack artifacts under
`source_library/reviews/<review_id>/applicability/`.

Compliance review must not override applicability decisions. Reviewer-ready compliance review uses
a generated applicability rule pack and retains non-applicable authorities in their own artifact
family.

### Review, Compliance, And Eval

Review layers produce package-level findings, forest-plan component findings, compliance matrices,
PDF reports, and finding graphs. Compliance findings remain evidence-backed and citation-bearing.
Eval layers check deterministic fixture contracts, phase readiness, V1 real-EA expectations,
applicability quality, and promotion-suite manifests that tell agents which artifacts support or
block a readiness claim.

Decision-support synthesis is its own layer over audited review artifacts. The
`ea-consistency-document` command reads generated applicability, compliance, Forest Plan,
non-applicable authority, risk, resolution, package, and tracked config/fixture artifacts, then
writes the local `decision_support/` JSON, Markdown, PDF, and manifest family. It must fail closed on
missing, stale, hash-mismatched, or non-reviewer-ready inputs and must not promote manual root-level
draft prose as canonical evidence.

## Public CLI Surface

`src/usfs_r1_ea_sources/cli.py` remains the public entrypoint. Command registration can be split by
workflow lane, but command names and important option names are stable unless a migration explicitly
changes them.

Current command groups are recorded in `docs/architecture_contract.toml`:

- capture and catalog;
- extraction, retrieval, graph, claims, and rule binding;
- applicability;
- review and forest-plan;
- compliance;
- decision support;
- eval and promotion.

## Architecture Fitness Gates

Architecture enforcement is deliberately small:

- parse Python imports with AST;
- fail source-level import cycles unless named as temporary exceptions in the contract;
- fail dependency-boundary violations against `docs/architecture_contract.toml`;
- keep exceptions visible with owner and removal milestone.

Relevant ADRs:

- `docs/adr/0001-architecture-fitness-gates.md`
- `docs/adr/0002-applicability-before-compliance.md`
- `docs/adr/0003-rule-pack-ownership.md`
- `docs/adr/0004-untrusted-source-content.md`
- `docs/adr/0005-architecture-gates-in-milestone-closeout.md`

## Change Rules For Agents

- Start from `AGENTS.md`, `docs/CURRENT_SYSTEM_STATE.md`, this architecture map, and the contract
  before changing module boundaries.
- Keep domain knowledge in workbook rows, catalog metadata, profiles, rule packs, eval fixtures,
  generated ledgers, and reports.
- Keep public CLI commands stable unless a milestone explicitly defines a migration.
- Do not stage ignored `source_library/` artifacts without an explicit repository policy change.
- When a temporary exception is needed, put it in the architecture contract with an owner and
  removal milestone, not in test code.
