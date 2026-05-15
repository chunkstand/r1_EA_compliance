# Graph Retrieval Starter

Date: 2026-05-15
Status: Phase 0 starter baseline

## Purpose

This artifact turns the current GraphRAG and knowledge-graph retrieval research
into a repo-specific retrieval baseline for the canonical source-register
refoundation.

The main rule is simple:

The graph must not replace retrieval. It must help route, filter, expand,
rerank, and explain retrieval.

For this repo, that means a retrieval system that can answer legal and policy
questions over auditable evidence while remaining fail-closed on currentness,
scope, provenance, and citation-bearing support.

## Starter Assumptions

- The future canonical workbook remains the governing source register.
- `source_record`, `source_artifact`, `chunk`, `evidence_span`,
  `authority_document`, `authority_expression`, `authority_fragment`,
  `forest_plan_component`, and review reasoning objects remain separate layers.
- Final review findings and draft sections must reduce to cited source evidence,
  not community summaries or graph topology alone.
- Retrieval for legal and policy work must be hybrid: exact citation and
  metadata filters are as important as semantic similarity.
- Currentness is part of retrieval, not only an after-the-fact check.
- The existing repo already has the right retrieval-direction seam:
  authority universe -> package fact graph -> retrieval traces -> bounded graph
  traces -> applicability decisions -> search coverage -> generated rules ->
  compliance findings.

## Core Modeling Rule

The repo needs a layered retrieval stack:

`query -> routed retrieval mode -> fused candidates -> bounded graph expansion -> rerank/filter -> selected evidence spans and paths -> review reasoning object`

If the system skips the routing, fusion, or bounded filtering steps, graph
retrieval becomes noisy, expensive, and legally unreliable.

## What The Graph Is For

The graph is primarily for:

- linking dissimilar but structurally relevant evidence
- expressing authority lineage and supporting-document relationships
- constraining multi-hop traversal to reviewer-visible legal paths
- surfacing justification paths from authority to evidence to finding
- enabling graph-health and path-completeness evaluation

The graph is not the only retrieval interface. It is one retrieval signal among
others.

## Retrieval Units

The repo should retrieve these units deliberately:

- `source_record`
  Use for register identity, source-role filtering, currentness, and catalog
  provenance.
- `evidence_span`
  Default final evidence unit for review findings. This is the main
  citation-bearing retrieval unit.
- `source_claim`
  Optional higher-level lexical unit when supported by extraction quality and
  claim evals.
- `authority_fragment`
  Section-aware authority retrieval surface for statutes, CFR sections, FSM/FSH
  chapters, appendices, and similar fragments.
- `forest_plan_component`
  Semantic retrieval surface for standards, guidelines, and other plan
  components.
- `authority_path`
  Reviewer-visible legal or policy lineage path.
- `justification_path`
  Reviewer-visible path from authority to evidence to review output.
- `community_summary`
  Broad corpus coverage and discovery surface only. Never enough by itself for a
  final controlling finding.

## Retrieval Modes

### `citation_exact_search`

Use for direct citations, IDs, section labels, component IDs, and known titles.

- primary signals:
  `citation`, `full_text_bm25`, `metadata_filter`
- optional signals:
  `semantic_vector`
- required filters:
  `currentness_filter`, `scope_filter` when review context exists
- final-evidence target:
  `evidence_span`

### `authority_local_hybrid_search`

Use for authority-topic questions that still require local, citation-bearing
 evidence.

- primary signals:
  `full_text_bm25`, `semantic_vector`, `metadata_filter`
- optional signals:
  `authority_graph_expansion`, `structural_similarity`
- required filters:
  `currentness_filter`, `scope_filter`, `source_role_filter`

### `forest_component_support_search`

Use for forest-plan component questions and component-supporting evidence.

- primary signals:
  `full_text_bm25`, `metadata_filter`, `source_role_filter`
- optional signals:
  `authority_graph_expansion`, `structural_similarity`
- required filters:
  `forest_unit_filter`, `support_document_role_filter`, `currentness_filter`

### `package_applicability_search`

Use for package-specific applicability discovery driven by authority candidates
and package facts.

- primary signals:
  `metadata_filter`, `full_text_bm25`, `package_fact_graph_expansion`
- optional signals:
  `semantic_vector`, `authority_graph_expansion`
- required filters:
  `currentness_filter`, `scope_filter`, `source_role_filter`
- note:
  this is the retrieval mode that most directly extends the current
  `applicability_retrieval.py` seam.

### `global_coverage_search`

Use for broad questions about themes, gaps, or whole-corpus coverage.

- primary signals:
  `community_summary`, `structural_similarity`
- optional signals:
  `semantic_vector`
- required boundary:
  any final finding must reduce from this mode back to local evidence-bearing
  units before promotion

### `drift_reasoning_search`

Use for ambiguous or multi-hop questions that need iterative broad-to-narrow
retrieval.

- primary signals:
  `community_summary`, `semantic_vector`, `authority_graph_expansion`
- optional signals:
  `full_text_bm25`, `metadata_filter`
- required boundary:
  the final answer path must record both the broad starting points and the local
  evidence chosen after refinement

## Query Routing

Routing should be explicit and replayable.

- direct citations, component IDs, source-record IDs, CFR/USC/FSM/FSH style
  queries -> `citation_exact_search`
- questions about one authority family or one document topic ->
  `authority_local_hybrid_search`
- questions about forest-plan consistency, standards, guidelines, amendments,
  appendices, or supporting documents -> `forest_component_support_search`
- package review questions driven by authority candidates and project facts ->
  `package_applicability_search`
- corpus-wide theme, coverage, or summary questions -> `global_coverage_search`
- ambiguous, multi-entity, or multi-hop questions -> `drift_reasoning_search`

The router must write its decision into the retrieval trace so the selected mode
is reviewable and evaluable.

## Hybrid Fusion

The default fusion policy should be:

- retrieve a larger candidate set from each source than the final answer needs
- fuse ranked lists with weighted reciprocal rank fusion
- use stable deterministic tie breakers
- rerank fused results with legal/reviewer-specific features

The reranker should score at least:

- citation exactness
- currentness fit
- scope fit
- source-role fit
- authority hierarchy fit
- forest-unit fit
- support-document-role fit
- path completeness
- provenance completeness

## Graph Expansion

Graph expansion must stay bounded and typed.

- allowed expansions should come from governed relationship types
- expansion depth should differ by mode
- expansion should reject currentness mismatches unless the query explicitly asks
  for historical lineage
- expansion should reject scope mismatches unless the query explicitly asks for
  cross-scope comparison
- community summaries may seed a search but must not masquerade as final legal
  evidence

For legal defensibility, graph expansion should normally happen after strong
local candidates have been identified, not as unconstrained wandering.

## Trace Requirements

Every governed retrieval run should emit replayable traces.

Required trace content:

- query text
- routed query mode
- source signals used
- filters applied
- candidate ranks by signal
- fusion contributions
- selected and rejected results
- currentness decision
- scope decision
- selected evidence spans
- graph path IDs and relationship types when graph expansion is used
- search coverage status
- unsupported or unresolved reasons when evidence is weak

Without this, the system can return text, but it cannot defend why the text was
chosen.

## Evaluation Requirements

The starter eval stack should prove these behaviors:

- exact citations beat semantically similar distractors
- current sources beat superseded sources for present-tense review queries
- historical queries may retrieve superseded sources only when explicitly asked
- forest-plan component search retrieves both the component and its governed
  supporting evidence
- package applicability retrieval can be reconstructed from traces and graph
  paths
- broad coverage answers can reduce to local evidence before becoming findings
- alias collisions remain unresolved until disambiguated
- scope mismatches are rejected
- graph traversal stays within allowed relationship types and hop limits

## Existing Repo Surfaces To Reuse

- `src/usfs_r1_ea_sources/retrieval.py`
- `src/usfs_r1_ea_sources/applicability_retrieval.py`
- `config/retrieval_eval_seed.json`
- applicability retrieval traces and graph diagnostics
- current retrieval-readiness and search-coverage artifacts

The starter should extend these seams, not replace them with a separate
GraphRAG subsystem.

## Explicit Non-Goals

- This starter does not mandate a specific graph database.
- This starter does not replace vector retrieval with graph traversal.
- This starter does not claim community summaries are legal evidence.
- This starter does not authorize hidden NEPA heuristics in runtime code.
- This starter does not turn experimental starter routes into production
  promotion gates without direct eval coverage.

## Next Implementation Use

Use this starter to drive:

1. canonical retrieval policy contracts
2. query routing and fusion policy implementation
3. graph expansion guardrails
4. retrieval trace schema hardening
5. proving-slice retrieval cases in Phase `1.5`
6. retrieval-mode and path-completeness evals before bulk canonical ingest
