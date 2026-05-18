# Canonical Source Register Refoundation Milestone Plan

Date: 2026-05-18

Status: In Progress

Current checkpoint on 2026-05-18:

- Phase 0 workbook freeze artifacts are now live in the repo: the final
  workbook is staged in-repo, `source-register-validate` and
  `source-register-diff` are implemented, the sheet/schema/vocabulary/row-state
  contracts are frozen in `config/`, the direct-file-readiness and
  parser-admission contracts are explicit, and the workbook audit now lives in
  `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`.
- Phase 1 foundation loader replacement is now live: the workbook loader
  contract is explicit, the canonical source-register loader can read
  `Document_Register_Master` into normalized canonical rows with semantic
  identity and parser-routing seams, and the compatibility adapter back to
  `WorkbookSource` is in place for later runtime migration.
- Phase 1.5 proving-slice work is now live: the repo ships
  `config/source_register_proving_slice_v1.json`,
  `source-register-proving-slice`,
  `authority-relationship-eval`,
  `citation-alias-eval`,
  `graph-health-eval`, and
  `graph-accuracy-eval`, and the proving packet now exercises a governed mixed
  slice of `26` load-ready rows plus `5` queue rows before any capture/catalog
  cutover begins.
- Phase 2 capture/catalog cutover is now live: active
  `dry-run`, `preflight`, `download`, `batch-download`, and `catalog-build`
  calls resolve through `loader_contract = "source_register_v1"`, the
  canonical register is now the sole active ledger, and the first isolated
  canonical catalog gate is `source-set-ae989382c52344db`.
- Phase 3 authority-currentness, supersession, and source-partition rebase is
  now live in commit `70a5953`: bare `authority-currentness` calls can project
  canonical authority families and queue gaps from the active
  `source_register_v1` catalog plus workbook queue, supersession lineage is
  governed by `config/source_register_currentness_lineage_v1.json`, and stale
  canonical active partitions are fail-closed back into
  `currentness_supersession_archive`.
- Phase 4 extraction fidelity and verified source admission is now live: the
  extraction manifest preserves canonical planning fields, extraction planning
  is metadata-aware, governed proving-placeholder artifacts no longer surface
  as noisy parser failures, verified extraction admission can resolve against
  manifest selectors, and the upstream extraction direct-eval lane now spans
  `11` canonical category families.
- Phase 5 graph accuracy, provenance completeness, and knowledge-graph gating
  is now live: `nepa-knowledge-graph-export` now emits canonical authority
  documents, sections, scopes, authority paths, and justification paths for
  proving source set `source-set-9dcf819bc4cca486`, and the five semantic eval
  gates now pass on that exported graph. Root `phase-eval` still remains
  non-reviewer-ready because inherited Phase 4 placeholder artifacts continue
  to block extraction, retrieval, evidence-graph validation, and downstream
  reviewer lanes.
- Phase 6 applicability, rule-pack, and legally accurate review is now live in
  commit `15d117a` at the review-contract boundary: `compliance-review` writes
  `authority_explanation_paths.json`, the reviewer-facing matrix surfaces
  authority-path classifications plus retrieval/graph/search coverage and risk
  fields, `compliance-review-eval` enforces the new explanation-path artifact
  and trace/classification coverage, and `v1-ea-eval` now treats that artifact
  as a required broader-EA gate. Live green replay currently comes from the
  active reviewer-ready East Crazies lane on `source-set-ba8d0feae79501b8`
  because the canonical proving slice still carries Phase 4 placeholder
  artifacts and cannot yet prove real-direct-document review readiness.
- No full-register canonical ingestion may bypass the now-live Phase 1.5
  proving gate, and the next implementation boundary is now Phase 7: legally
  defensible draft-document generation.

Owner context: This is a fresh standalone architecture and delivery plan for
refounding the system around
`usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` as the canonical
source register. It does not append to the older
`usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx` workbook
contract or to the forest-plan-only source-delta lane except where those older
surfaces are mined for migration evidence. The current repo remains the
delivery vehicle; this plan replaces the source-contract foundation, not the
entire repository.

## Purpose

The current repo has meaningful capture, catalog, currentness, extraction,
retrieval, graph, eval, and review machinery, but it is still organized around
an older workbook contract that assumes:

- `Ingest_Checklist` is the canonical authority/load sheet;
- `R1_Forest_Plans` is the canonical forest-plan sheet; and
- supplemental forest-plan support material arrives through a special-case
  source-delta register.

The new canonical workbook is structurally different and materially better for
the long-term system. It already separates:

- one canonical load table: `Document_Register_Master`;
- non-load validation and audit sheets;
- a deferred direct-file capture queue;
- patched URL evidence;
- removed/deduped evidence; and
- workbook QA and tier-level load guidance.

This plan refounds the system around that workbook so the end state is a
register-first, evidence-backed, fail-closed NEPA platform that can:

- ingest current authoritative sources with durable provenance;
- capture only validated source documents into the corpus;
- extract source text accurately with explicit parser and quality gates;
- model agent-legible authority relationships across statutes, regulations,
  policies, directives, handbooks, forest plans, and supporting forest-plan
  documents;
- build an evidence graph with accurate nodes, edges, and provenance;
- support legally accurate, citation-bearing NEPA review; and
- generate legally defensible draft NEPA document artifacts for human legal and
  subject-matter review.

The system must not claim legal correctness by prose alone. Every material
claim must be backed by source provenance, currentness controls, extraction
accuracy evidence, graph accuracy evidence, review evals, and reviewer-visible
artifacts.

## Current Evidence

- The active capture/catalog runtime now treats
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` as the
  source-of-truth workbook because `config/downloader.toml` is now pinned to
  `loader_contract = "source_register_v1"`. The legacy workbook plus promoted
  source-delta register remain preserved replay surfaces only.
- The live legacy catalog baseline in `source_library/catalog/` remains
  `source-set-5e65d845ce77e1a0` with `350` source rows, `319` artifacts, and
  source partitions `active_review_corpus=349` and
  `candidate_blocked_source=1`.
- The legacy promotion surface is mixed today and is now baseline-locked for
  migration work. The current-promotion suite at
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  is green with `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`, `expansion_ready=true`, and
  `promotion_ready=true`, while the active full-canonical source-set artifact
  at
  `source_library/derived/source-set-5e65d845ce77e1a0/evidence_graph/phase_eval_results.json`
  currently records `reviewer_ready=false`, `passed_phase_count=9`,
  `phase_count=12`, and `threshold_failed_phase_count=1`.
- The final canonical workbook is now staged in-repo at
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`.
  Its final audit date is `2026-05-16`, and its load/certification sheets say
  that `Document_Register_Master` is the only database-load table.
- The final workbook contains `13` sheets and currently reports:
  - `635` retained load-ready source rows in `Document_Register_Master`;
  - `51` deferred rows in `Direct_File_Capture_Queue`;
  - `2` final removed-not-applicable rows in
    `Removed_Not_Applicable_Final`; and
  - `29` direct-media rows reclassified from manual-export priority to direct
    extraction.
- The final workbook QA and certification tabs currently report:
  - zero duplicate `Source_ID` values in the master load table;
  - zero duplicate `Source_URL` values in the master load table;
  - zero blank or non-HTTP(S) URLs in the master load table; and
  - `635` rows with explicit `EA_System_Applicability_Status`.
- `Land_Exchange_Additions_Log` shows the final workbook is materially broader
  than the earlier candidate: `44` master load rows, `1` queue row, and `24`
  land-exchange coverage-audit rows were added in the final pass.
- The queue is not incidental metadata. `Direct_File_Capture_Queue` is
  currently `51` rows and is dominated by folder/listing/manual-export
  placeholders plus unresolved forest-plan support file URLs. Phase `1.5` and
  Phase `2` must therefore prove queue discipline on real placeholder classes,
  not only on easy born-digital rows.
- The retained master corpus is concentrated in a few applicability families
  that the proving slice and early evals must cover explicitly:
  `238` forest/grassland plan-specific rows,
  `208` species/ESA/wildlife trigger rows,
  `50` land exchange trigger rows,
  `31` federal resource/trigger rows, and
  `5` stale-source-detector rows.
- The repo already has durable downstream controls worth preserving:
  - `authority-currentness`;
  - source-partition contracts;
  - upstream direct eval coverage;
  - downstream direct eval coverage;
  - `phase-eval`;
  - promotion-suite style aggregate gating; and
  - source-set derived artifact families under `source_library/derived/`.
- The user has clarified that the system is still under development and is not
  yet operational, so a source-contract breaking change is acceptable if it is
  explicit, well-routed, and verification-backed.

## Goal

Refound the repo around the new canonical workbook so that by the end of this
plan:

- the canonical workbook is the only human-authored source register used to
  define source rows;
- non-load workbook sheets remain first-class governance inputs but cannot leak
  into the corpus as source rows;
- every corpus-ready source row has validated source provenance, currentness
  handling, and a durable row identity;
- extraction accuracy is proven by tracked adversarial evaluation, not only by
  parser success;
- authority semantics are modeled in first-class ontology and relationship
  artifacts that distinguish source provenance objects from legal/review
  reasoning objects;
- graph accuracy is proven by tracked node/edge/provenance evaluation, not only
  by graph build success;
- legally accurate review artifacts are source-traceable, currentness-aware,
  and direct-eval-governed; and
- legally defensible draft NEPA document outputs are supported by citation
  traces, authority coverage, reviewer-visible residual-risk reporting, and
  documented human review boundaries.

For this plan, "legally accurate" and "legally defensible" do not mean
autonomous legal advice or machine final signoff. They mean the system must
fail closed unless it can show current source authority, extraction fidelity,
graph provenance, applicability/rule-pack completeness, review evidence, and
document-generation traceability in durable artifacts that a qualified human can
inspect.

## Non-Goals

- Do not preserve the old workbook contract purely for backward compatibility if
  it weakens or obscures the new canonical register boundary.
- Do not start a second greenfield repository that rebuilds downloader,
  catalog, currentness, extraction, graph, and evaluation surfaces from
  scratch.
- Do not treat deferred queue rows, listing pages, project pages, folder URLs,
  or unresolved placeholders as corpus-ready source documents.
- Do not begin bulk canonical-register ingestion before Phase `1.5`
  pre-ingestion contract proving passes.
- Do not weaken tests, evals, phase gates, or promotion gates just to achieve a
  green result.
- Do not count extraction success, graph build success, or draft generation as
  accuracy unless the relevant eval family passes.
- Do not allow superseded, reserved, repealed, stale, or blocked sources to
  silently satisfy active controlling-authority requirements.
- Do not allow generated NEPA narrative to introduce unsupported conclusions,
  hidden legal heuristics, or uncited claims.
- Do not claim production readiness until the end-state gates in this plan pass
  on real review packages and draft-generation scenarios.

## Scope

- Canonical workbook adoption and schema validation.
- Foundation-layer source-row model and workbook loader replacement.
- Capture, catalog, currentness, and source-partition refit to the new master
  register.
- Extraction fidelity and extraction-admission hardening.
- Evidence-graph and NEPA graph accuracy hardening.
- Applicability, rule-pack, compliance-review, and review-packet hardening on
  the new corpus.
- Legally defensible draft-document generation with traceability and evals.
- Aggregate phase gating, current-state docs, handoff routing, and closeout
  discipline for the new register-first system.

## Out Of Scope

- Production deployment, hosted multi-user operations, or external service
  integration beyond the local audited corpus unless explicitly added in a later
  plan.
- A broad UI redesign unrelated to source, evaluation, review, or document
  generation accuracy.
- Ad hoc import of queue rows before their direct-file readiness is resolved.
- Treating ignored `source_library/` outputs as tracked repo files unless
  repository policy explicitly changes.

## Bitter Lesson Alignment

This plan explicitly adopts the repo's interpretation of Rich Sutton's "The
Bitter Lesson" from `docs/BITTER_LESSON_ALIGNMENT.md`.

For this refoundation, the governing commitments are:

- Search, retrieval, tracing, and evaluation are first-class. Review quality
  should improve primarily through broader source coverage, stronger extraction,
  better retrieval and graph evidence, richer negative cases, and stronger
  adjudicated eval loops.
- Domain knowledge is data. NEPA authority families, source roles,
  currentness/supersession states, rule templates, forest-profile requirements,
  adjudications, and document expectations must live in the canonical workbook,
  tracked configs, eval fixtures, or reviewer-visible reports rather than in
  hidden runtime branches.
- Stable runtime code should build meta-methods: parse, normalize, capture,
  chunk, index, retrieve, trace, evaluate, and report. It should not pretend a
  fixed handcrafted branch structure can encode all legally relevant NEPA
  reasoning.
- Generated conclusions stay downstream of evidence. Retrieval, graph,
  applicability, compliance, and draft generation may summarize or assemble
  evidence, but they must not replace evidence-backed reasoning with prompt-only
  narrative.
- Quality-improvement order is controlled. When the system is weak, the default
  next move is to improve source coverage, currentness evidence, extraction
  fidelity, retrieval recall, graph coverage, eval breadth, and failure
  telemetry before adding special-case NEPA heuristics.

This plan therefore rejects two failure modes:

- hiding NEPA or Forest Service concepts inside bespoke runtime branches; and
- claiming legal accuracy from plausible output instead of scalable evidence,
  search, and evaluation loops.

## Figay And Yu Alignment

This refoundation must also satisfy two external architecture standards that
are useful as pressure tests for the repo:

- a Figay-style semantic and ontological standard: the system must model
  concepts, viewpoints, temporal lineage, normativity, and justification paths
  explicitly rather than flattening everything into source files and generic
  edges; and
- a Yu-style production GraphRAG standard: the system must sustain accurate
  retrieval, entity resolution, graph quality, graph evolution, and
  explanation under changing document corpora rather than depending on one-shot
  graph export success.

For this repo, that means:

- Do not let `source_record` stand in for every other concept. The system must
  distinguish at minimum source provenance objects, authority documents,
  authority sections/components, jurisdiction/scope objects, forest-plan
  components, and review findings.
- Do not let semantic authority relationships exist only as implicit
  string/title heuristics. They must live in versioned ontology, relationship,
  alias, or lineage artifacts with provenance and eval coverage.
- Do not let the graph become graph-only retrieval. Review and draft generation
  must keep hybrid search and trace paths across metadata, source text,
  retrieval results, graph paths, and adjudicated outputs.
- Do not treat graph quality as static. The repo must validate graph health and
  incremental refresh behavior when new laws, policies, or source revisions
  enter the canonical register.
- Do not let explanation stop at "this finding cites this source." The graph
  must support reviewer-visible justification paths that show why a source is
  controlling, interpretive, supporting, superseded, or out of scope.

## First-Class Artifacts

The end-state system must treat the following as first-class, durable,
reviewer-visible artifacts.

### Canonical Source And Governance Artifacts

- Canonical workbook:
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Workbook sheet contract and schema:
  `config/source_register_sheet_contract_v1.json`,
  `config/source_register_schema_v1.json`
- Source-register controlled vocabularies and row-state contract:
  `config/source_register_vocabularies_v1.json`,
  `config/source_register_row_states_v1.json`
- Canonical workbook audit and migration report:
  `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`
- URL override registry:
  `config/url_overrides.toml`
- Authority universe inventory:
  `config/authority_universe_families_nepa_ea_v1.json`
- Authority/source addition and non-addition decisions:
  `config/authority_source_addition_decisions_nepa_ea_v1.json`
- Source-partition contract:
  `config/source_partition_contract_nepa_3d_v1.json`
- Evaluation coverage register:
  `docs/EVALUATION_COVERAGE_REGISTER.md`

### Semantic Authority And Relationship Artifacts

- Authority ontology and node/role taxonomy:
  `config/authority_document_ontology_v1.json`
- Allowed semantic relationship vocabulary:
  `config/authority_relationship_types_v1.json`
- Canonical relationship register for explicit authority lineage:
  `config/authority_relationship_register_v1.json`
- Citation and alias normalization register:
  `config/citation_alias_register_v1.json`
- Jurisdiction, scope, and applicability-surface register:
  `config/jurisdiction_scope_register_v1.json`
- Direct-file readiness contract:
  `config/direct_file_readiness_contract_v1.json`
- Parser-routing and extraction-admission contract:
  `config/parser_admission_contract_v1.json`
- Graph health and evolution contract:
  `config/graph_health_contract_v1.json`
- Authority relationship and ontology eval manifests:
  `config/authority_relationship_eval_v1.json`,
  `config/authority_ontology_eval_v1.json`

### Capture And Corpus Artifacts

- Row-level manifests:
  `source_library/manifests/*.jsonl`
- Run summaries, validation reports, events, and failures:
  `source_library/runs/<run_id>/summary.json`,
  `validation_report.json`,
  `events.jsonl`,
  `failures.csv`
- Reviewer catalog:
  `source_library/catalog/source_catalog.jsonl`,
  `source_library/catalog/source_set_manifest.json`,
  `source_library/catalog/review_sources.sqlite`
- Corpus integrity and promotion reports for scoped or merged source sets

### Extraction And Retrieval Artifacts

- Extracted text and parser payloads:
  `source_library/derived/<source_set_id>/extracted_text/`,
  `docling_json/`
- Extraction manifest and validation:
  `source_library/derived/<source_set_id>/diagnostics/extraction_manifest.jsonl`,
  `extraction_validation.json`,
  `summary.json`
- Reuse inventory:
  `source_library/derived/<source_set_id>/reuse_inventory/reuse_inventory.json`
- Extraction accuracy audit outputs
- Retrieval index and retrieval eval outputs
- Hybrid retrieval index manifest and index-build summary
- Retrieval traces, query plans, and search coverage certificates used by
  applicability and compliance lanes
- Review explanation-path traces linking retrieval evidence to graph paths and
  final review decisions
- Hard-negative and controlled-violation eval fixtures for extraction and
  retrieval quality

### Currentness, Graph, And Review Artifacts

- Authority currentness report:
  `source_library/derived/<source_set_id>/authority_currentness/authority_currentness_report.json`
- Authority ontology validation and relationship eval results
- Citation alias resolution report and unresolved-alias ledger
- Package fact graph artifacts
- Graph nodes, graph edges, and graph validation/eval artifacts
- Graph-accuracy eval manifest, fixtures, and result summaries
- Graph health report covering orphaning, disconnected components, stale alias
  references, relationship-typing drift, and refresh-delta integrity
- Claim extraction outputs
- Rule-claim binding outputs
- Applicability decision ledgers and generated rule packs
- Applicability retrieval traces, adjudication ledgers, and search coverage
  artifacts
- Authority-path and justification-path artifacts for review-ready findings
- Compliance review outputs, including:
  `compliance_matrix.json`,
  `compliance_matrix.md`,
  `compliance_matrix.pdf`
- Review packet indexes and reviewer-facing residual-risk surfaces

### Draft Generation And Defensibility Artifacts

- Draft-generation manifest and source-citation trace for each generated NEPA
  document
- Draft-generation unsupported-evidence and refusal ledger
- Section-level evidence trace showing:
  source passages,
  authority families,
  graph paths,
  unresolved assumptions,
  and reviewer-required edits
- Draft-generation eval outputs comparing generated sections to governed review
  facts and approved exemplars
- Defensibility packet summarizing:
  controlling authorities,
  supporting evidence,
  unresolved legal or factual gaps,
  and human-review signoff requirements

## Owner Surfaces

- Foundation:
  `src/usfs_r1_ea_sources/records.py`,
  `src/usfs_r1_ea_sources/workbook.py`,
  new canonical register loader/validator modules,
  `src/usfs_r1_ea_sources/config.py`
- Semantic authority and graph identity:
  planned ontology/relationship/alias modules,
  `src/usfs_r1_ea_sources/nepa_3d_graph_contract.py`,
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`
- Capture and catalog:
  `src/usfs_r1_ea_sources/dry_run.py`,
  `preflight.py`,
  `download.py`,
  `batches.py`,
  `validate_run.py`,
  `catalog.py`
- Currentness and source partitions:
  `src/usfs_r1_ea_sources/source_partitions.py`,
  `authority_currentness.py`
- Extraction and retrieval:
  `extract.py`,
  `extraction_accuracy.py`,
  `extraction_admission.py`,
  `retrieval.py`
- Graph and downstream reasoning:
  `evidence_graph.py`,
  `claim_extraction.py`,
  `rule_claim_binding.py`,
  `nepa_knowledge_graph_export.py`
- Applicability, compliance, and review:
  `applicability*.py`,
  `compliance*.py`,
  `review_packet_index.py`,
  `ea_review.py`
- Evaluation orchestration:
  `src/usfs_r1_ea_sources/upstream_evaluation.py`,
  `cli_eval.py`,
  `phase_eval*`
- Documentation and routing:
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- The new canonical source contract must be hidden behind a narrow foundation
  interface. Do not scatter workbook-sheet assumptions across capture, catalog,
  extraction, or review modules.
- Introduce one canonical normalized source-row model for the new system.
  Preserve compatibility shims only where they reduce migration blast radius;
  do not let legacy workbook semantics remain the de facto truth.
- Introduce a separate canonical semantic model for authority reasoning. The
  system must distinguish `source_record` provenance rows from
  `authority_document`, `authority_section`, `jurisdiction_scope`,
  `forest_plan_component`, and review reasoning objects.
- The system must read `Document_Register_Master` as the only corpus-ready load
  table. Non-load tabs may be read only for validation, migration diffing,
  queue routing, or audit evidence.
- Deferred queue rows must remain explicit governance artifacts and must never
  become load-ready rows by omission or default.
- Source-partition and currentness behavior must come from explicit register
  fields plus governed contracts, not from ad hoc title heuristics.
- Keep NEPA and Forest Service domain knowledge as data in the canonical
  workbook, authority inventories, rule templates, profile configs,
  adjudications, and eval fixtures. Do not spread it through retrieval, graph,
  review, or draft-generation runtime code as hidden conditionals.
- Keep relationship semantics, citation aliases, jurisdiction/scope mappings,
  and currentness lineage in versioned config/register artifacts. Do not infer
  controlling legal relationships only from titles, URLs, or ad hoc string
  similarity inside runtime code.
- Extraction, retrieval, graph, review, and draft generation must continue to
  consume catalog or derived surfaces, not workbook cells or raw artifact
  filenames directly.
- Retrieval must remain hybrid. The graph is one reasoning surface, not the
  only retrieval interface. Metadata filters, source-role filters, source text
  search, graph expansion, and optional vector retrieval should remain
  composable and reviewer-traceable.
- Put new direct-eval contracts and fixtures under `config/` and `tests/`
  rather than relying on mutable local corpus state for the core eval truth.
- Draft-generation code and evals must live under dedicated modules and command
  groups. Do not hide document-generation logic inside compliance review or
  graph build modules.
- Draft generation must operate downstream of validated review artifacts,
  retrieval traces, graph evidence, authority lineage, and unresolved-issue
  ledgers. It must not synthesize directly from workbook prose or raw document
  bytes outside those audited surfaces.

## Weak-Point Prevention Contract

- Weak point forecast: quality improvements drift toward hidden handcrafted
  NEPA heuristics instead of broader data, search, and eval coverage.
  Owner surface: canonical register contracts, rule-template data,
  applicability/retrieval/graph interfaces, eval manifests, and
  `docs/BITTER_LESSON_ALIGNMENT.md`.
  Prevention gate: every new NEPA-specific behavior must land in a data surface,
  reviewer-visible report, or eval fixture unless the plan names a narrow
  unavoidable rule and proves why data/eval generalization is insufficient.
  Fail threshold: a milestone relies on hidden runtime branches, keyword lists,
  or bespoke output shaping to get green while corpus/eval coverage remains
  weak.
  Controlled violation: introduce a fixture-only keyword shortcut in a runtime
  module instead of in data; architecture and eval review must fail.
  Future-Codex misuse scenario: a later session improves one package by adding
  special-case branches instead of expanding source/eval coverage; this gate
  must force the improvement back into data, retrieval, graph, or eval
  surfaces.

- Weak point forecast: a later session reads audit or queue tabs as source rows
  because the workbook is rich and multi-tabbed.
  Owner surface: canonical register loader, schema validator, workbook sheet
  contract, and CLI entrypoints that accept workbook paths.
  Prevention gate: load commands must fail unless the workbook sheet contract
  says exactly one load table exists and it matches
  `Document_Register_Master`.
  Fail threshold: any non-load sheet emits corpus-ready source rows.
  Controlled violation: mutate the loader fixture so `Direct_File_Capture_Queue`
  is marked loadable; validation must fail.
  Future-Codex misuse scenario: a later session tries to "help" by loading
  queue rows directly; the sheet-contract gate must stop it.

- Weak point forecast: direct-file readiness is weakened and listing pages or
  placeholder project pages re-enter the active corpus.
  Owner surface: source-register validation, preflight classification,
  capture eval fixtures, and the deferred queue.
  Prevention gate: all load-ready forest/document rows must prove a document
  URL class allowed by the register contract or a documented exception.
  Fail threshold: queue rows or listing pages enter the active corpus without an
  explicit direct-file promotion event.
  Controlled violation: point a forest load row at a planning-page URL; the
  validator and preflight eval must fail.
  Future-Codex misuse scenario: a later session uses page URLs to get faster
  green download counts; direct-file gates must expose the regression.

- Weak point forecast: superseded or currentness-only rows count as active
  controlling authority.
  Owner surface: canonical register fields, source-partition contract,
  authority-currentness, applicability filters, graph export, and review gates.
  Prevention gate: partition/currentness checks must fail if reserved,
  repealed, superseded, blocked, or currentness-only rows derive active review
  rules.
  Fail threshold: any such row counts as active authority coverage.
  Controlled violation: move one superseded row into active review eligibility
  in a fixture; the currentness and graph evals must fail.
  Future-Codex misuse scenario: a later session promotes stale but easy-to-find
  text to satisfy coverage; currentness gates must reject it.

- Weak point forecast: extraction accuracy is inferred from parser success
  rather than from audited text fidelity.
  Owner surface: extraction pipeline, extraction-accuracy-audit, extraction
  eval fixtures, and verified extraction admission.
  Prevention gate: tracked extraction eval categories must include statutes,
  regulations, directives, appendices, chaptered forest-plan support, maps,
  OCR/scanned PDFs, table-dense PDFs, and split-page section boundaries.
  Fail threshold: extraction passes without category coverage, negative cases,
  or admission evidence.
  Controlled violation: remove one hard extraction category or mutate offsets so
  chunk coverage drifts; the extraction eval must fail.
  Future-Codex misuse scenario: a later session keeps only easy born-digital
  PDFs; the manifest/category thresholds must expose the coverage loss.

- Weak point forecast: graph accuracy is inferred from graph build success
  rather than from node/edge/provenance correctness.
  Owner surface: graph builders, graph eval contracts, node/edge gold fixtures,
  and phase-eval integration.
  Prevention gate: graph accuracy evals must verify required node classes, edge
  classes, provenance completeness, citation reachability, orphan counts, and
  controlled-negative cases.
  Fail threshold: graph build passes while edges, node typing, or provenance
  are materially wrong.
  Controlled violation: remove a required edge type or sever citation
  provenance; the graph eval must fail.
  Future-Codex misuse scenario: a later session optimizes graph generation by
  dropping provenance-rich edges; graph eval and phase-eval must stop it.

- Weak point forecast: the graph remains a provenance-only export and does not
  become agent-legible for authority reasoning.
  Owner surface: authority ontology, semantic relationship register,
  citation-alias registry, graph export contract, and relationship eval
  fixtures.
  Prevention gate: ontology and relationship evals must fail if the graph
  cannot distinguish source provenance from authority documents/sections or if
  required legal relationship types are missing.
  Fail threshold: a review-ready graph cannot answer which authority document,
  authority section, or semantic relationship governs a finding.
  Controlled violation: collapse `authority_document` and `source_record` in a
  fixture or drop `IMPLEMENTS` / `SUPERSEDES` / `IS_SUPPORTING_DOCUMENT_FOR`
  edges; ontology and relationship evals must fail.
  Future-Codex misuse scenario: a later session exports richer counts but keeps
  a semantically flat graph; the ontology and relationship gates must expose
  the gap.

- Weak point forecast: graph reasoning becomes brittle because aliases,
  citation variants, and graph refreshes drift silently as the register grows.
  Owner surface: alias registry, entity-resolution logic, graph-health
  contract, retrieval traces, and incremental refresh evals.
  Prevention gate: alias-resolution, graph-health, and refresh-delta evals must
  fail on unresolved high-priority aliases, stale semantic edges, orphan spikes,
  or refresh-induced justification drift.
  Fail threshold: adding or updating a source row can silently break authority
  paths while graph build still succeeds.
  Controlled violation: mutate a citation alias or refresh fixture so the same
  authority resolves to two node identities; graph-health and refresh evals
  must fail.
  Future-Codex misuse scenario: a later session adds new current laws or
  directives without validating graph evolution; the refresh gates must stop
  promotion.

- Weak point forecast: the system claims legal accuracy without reviewer-visible
  evidence for applicability, rule derivation, compliance findings, and draft
  text.
  Owner surface: applicability, generated rule packs, compliance review,
  draft-generation modules, direct eval contracts, and final reviewer packets.
  Prevention gate: no review-ready or draft-ready claim is valid unless the
  relevant eval families and traceability artifacts exist and pass.
  Fail threshold: a generated review or draft section is accepted without
  source citations, authority lineage, graph evidence, unresolved-issue
  reporting, and human-review boundaries.
  Controlled violation: remove source citations or unresolved issue reporting
  from a draft-generation fixture; the generation eval must fail.
  Future-Codex misuse scenario: a later session writes plausible NEPA prose from
  prompts alone; traceability and eval gates must reject it.

## Phase Sequence

### Phase 0 - Canonical Workbook Freeze And Migration Baseline

Outcome label: resolved

Purpose: adopt the new workbook as the canonical authoring artifact, freeze its
sheet contract, and produce the migration baseline before any runtime refactor
begins.

Implementation tasks:

1. Stage the canonical workbook in the repo at
   `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` and record
   its SHA256 in a tracked audit note.
2. Write a live baseline-lock note that records:
   - the legacy runtime contract still pinned to `Ingest_Checklist`,
     `R1_Forest_Plans`, and
     `config/r1_forest_plan_document_register_draft.csv`;
   - the active legacy catalog baseline on `source-set-5e65d845ce77e1a0`; and
   - the mixed inherited readiness state where the ba8d current-promotion
     suite is green but the active full-canonical `source-set-5e65d845ce77e1a0`
     `phase-eval` artifact is currently red.
   This note is the regression boundary for the refoundation and must be
   updated before any runtime refactor.
3. Add `config/source_register_sheet_contract_v1.json` describing:
   - the only load table;
   - non-load sheets and their allowed purposes;
   - required header rows;
   - required columns per sheet; and
   - allowed workbook-level QA invariants.
4. Add `config/source_register_schema_v1.json`,
   `config/source_register_vocabularies_v1.json`, and
   `config/source_register_row_states_v1.json` for the normalized master-table
   row contract.
5. Add the semantic-baseline contracts needed for agent-legible authority
   modeling:
   - `config/authority_document_ontology_v1.json`;
   - `config/authority_relationship_types_v1.json`;
   - `config/citation_alias_register_v1.json`; and
   - `config/jurisdiction_scope_register_v1.json`.
6. Add the early ingest-governance contracts needed to prevent downstream
   refactors:
   - `config/direct_file_readiness_contract_v1.json`; and
   - `config/parser_admission_contract_v1.json`.
7. Refresh `docs/BITTER_LESSON_ALIGNMENT.md` so it explicitly names the new
   canonical workbook and the anti-heuristic obligations of the refoundation.
8. Add `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md` summarizing:
   - the full sheet inventory;
   - row counts by sheet;
   - load vs non-load semantics;
   - baseline counts (`635` load rows, `51` queue rows, `2` final removed
     rows, `29` direct-media reclassifications, `44` added master rows, and
     `1` added queue row);
   - queue taxonomy and required promotion paths for the real placeholder
     classes present in `Direct_File_Capture_Queue`;
   - applicability and authority-tier distributions needed for early proving
     slices; and
   - migration implications for the current repo.
9. Build a read-only diff artifact comparing the old runtime contract to the
   new master register:
   - old workbook rows;
   - current supplemental forest-plan register rows;
   - new master load rows;
   - deferred queue rows; and
   - superseded/currentness-only rows.
10. Build an ontology-gap audit showing which authority, section, lineage,
   alias, and scope relationships are already representable from the workbook
   versus which ones require new governed adjunct artifacts.
11. Write a pre-ingestion contract packet that names the final contracts that
   must be explicit before bulk document ingestion:
   - identity;
   - ontology;
   - semantic relationship vocabulary and directionality;
   - currentness and temporal lineage;
   - jurisdiction and scope;
   - citation alias/entity resolution; and
   - direct-file readiness classes.

Required implementation artifacts:

- canonical workbook in repo
- legacy baseline-lock summary
- `config/source_register_sheet_contract_v1.json`
- `config/source_register_schema_v1.json`
- `config/source_register_vocabularies_v1.json`
- `config/source_register_row_states_v1.json`
- `config/authority_document_ontology_v1.json`
- `config/authority_relationship_types_v1.json`
- `config/citation_alias_register_v1.json`
- `config/jurisdiction_scope_register_v1.json`
- `config/direct_file_readiness_contract_v1.json`
- `config/parser_admission_contract_v1.json`
- refreshed `docs/BITTER_LESSON_ALIGNMENT.md`
- `docs/CANONICAL_SOURCE_REGISTER_WORKBOOK_AUDIT.md`
- migration diff artifact plus baseline-lock summary in
  `docs/CURRENT_SYSTEM_STATE.md`

Acceptance signals:

- The workbook sheet contract proves that `Document_Register_Master` is the
  only source-row load table.
- The legacy baseline lock distinguishes inherited green surfaces from
  inherited red surfaces before runtime migration work starts.
- The repo has a reproducible schema description for the new canonical source
  register.
- Identity, ontology, relationship, currentness, scope, alias, and
  direct-file-readiness contracts are explicit enough to drive a proving slice
  without hidden manual judgment.
- No implementation phase starts until the migration diff is documented.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --mode schema
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_cli.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The workbook contract cannot be expressed without ambiguous load-table rules.
- The live legacy baseline cannot separate inherited debt from refoundation
  regressions because the current-promotion and active full-canonical artifacts
  do not reconcile well enough to lock the starting state.
- The canonical workbook requires hidden manual knowledge not captured in the
  sheet contract or audit note.

### Phase 1 - Foundation Refactor To A Canonical Register Loader

Outcome label: resolved

Purpose: replace the old sheet-specific workbook foundation with a canonical
register loader and normalized source-row model.

Implementation tasks:

1. Introduce a canonical normalized row object that is no longer tied to the
   old workbook sheet names.
2. Introduce canonical semantic identity seams for:
   - `authority_document_id`;
   - `authority_section_id` or equivalent component identity;
   - `jurisdiction_scope_id`; and
   - source-to-authority identity linkage.
3. Freeze loader-visible routing seams for:
   - direct-file readiness class; and
   - parser-routing / extraction-admission class.
4. Implement a new canonical register loader that:
   - reads `Document_Register_Master`;
   - validates required columns and controlled vocabularies;
   - rejects queue/audit leakage;
   - preserves row identity, currentness state, and direct-file readiness
     metadata; and
   - can emit the normalized row model for downstream stages.
5. Move controlled vocabularies and row-state semantics into tracked config or
   loader-owned schema surfaces rather than scattering them through capture or
   catalog code.
6. Add loader-owned alias and identity validation so authority documents and
   source rows cannot silently fork into duplicate graph identities.
7. Preserve a narrow compatibility seam where needed so capture/catalog callers
   can migrate without a broad rewrite in one commit.
8. Add CLI validation and reporting commands for the canonical workbook.
9. Update foundation tests so the old workbook contract is explicitly legacy
   rather than implicitly canonical.

Required implementation artifacts:

- new canonical register loader and validator modules
- updated foundation model and CLI surfaces
- fixture workbook slices for positive and negative loader cases
- docs explaining canonical-vs-legacy source contract boundaries

Acceptance signals:

- The foundation layer can read the new canonical workbook without using the
  old `Ingest_Checklist` / `R1_Forest_Plans` semantics.
- Non-load workbook sheets are enforced as metadata only.
- Legacy and canonical workbook paths are explicitly separated in docs and
  tests.

Required verification gates:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_cli.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources tests
git diff --check
```

Stop conditions:

- Downstream callers require workbook-cell semantics that cannot be hidden
  behind the new foundation interface.
- The compatibility seam grows wider instead of narrower.

### Phase 1.5 - Pre-Ingestion Contract-Proving Slice

Outcome label: resolved

Purpose: prove the frozen pre-ingestion contracts on a deliberately mixed
source slice before any bulk canonical-register ingestion or active-catalog
replacement begins.

Implementation tasks:

1. Add `config/source_register_proving_slice_v1.json` that defines a
   representative mixed slice of roughly `24-40` canonical rows spanning:
   - at least one `Applicable - forest/grassland plan-specific` row;
   - at least one `Applicable - species/ESA/wildlife trigger` row;
   - at least one `Applicable - land exchange trigger` row;
   - at least one `Applicable - stale-source detector only` row;
   - statute or code chapter;
   - CFR or Federal Register source;
   - USDA or USFS directive;
   - handbook chapter;
   - forest plan;
   - supporting forest-plan appendix or report;
   - OCR or scanned PDF;
   - table-dense PDF;
   - superseded/currentness-only source;
   - deferred queue or blocked example drawn from a real
     folder/listing/manual-export or unresolved direct-file placeholder class;
     and
   - at least one citation-alias or identity-collision stress case.
2. Add a proving-slice runner or equivalent governed execution path that can
   run the mixed slice through:
   - canonical loader validation;
   - preflight and direct-file classification;
   - scoped capture and cataloging;
   - extraction admission;
   - currentness and source-partition placement;
   - authority relationship and alias evaluation;
   - graph-health evaluation; and
   - justification-path export.
3. Produce a tracked proving report that records where the frozen contracts
   held and where they still drifted:
   - identity collisions or ambiguities;
   - alias misses;
   - row-state leakage;
   - direct-file classification errors;
   - parser-routing mismatches;
   - currentness/lineage errors;
   - missing semantic relationship types; and
   - broken authority-to-finding justification paths.
4. Resolve contract gaps revealed by the slice before any full-register
   ingestion milestone can begin.
5. Write an explicit no-bulk-ingest rule into the docs and handoff: the
   canonical repo may not run full-register document ingestion until this phase
   passes.

Required implementation artifacts:

- `config/source_register_proving_slice_v1.json`
- proving-slice execution surface and fixtures
- tracked pre-ingestion contract-proving report
- docs and handoff note recording the no-bulk-ingest boundary

Acceptance signals:

- The mixed slice can be processed end to end without hidden workbook or
  reviewer-local assumptions.
- Identity, ontology, relationship, currentness, scope, alias, and
  direct-file-readiness contracts survive a representative real-document slice.
- No full-register ingestion is allowed until this proving slice is green.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-proving-slice --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --manifest config/source_register_proving_slice_v1.json --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources authority-relationship-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources citation-alias-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources graph-health-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources graph-accuracy-eval --output-dir source_library
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_proving.py tests/test_graph_accuracy_eval.py tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_preflight.py tests/test_catalog.py tests/test_extraction_accuracy.py tests/test_authority_currentness.py tests/test_cli.py tests/test_architecture_contract.py -q
git diff --check
```

Stop conditions:

- The proving slice exposes contract categories that still require ad hoc
  human interpretation to proceed.
- Slice results show identity, alias, currentness, or relationship drift that
  would force broad downstream refactors after bulk ingest.

### Phase 2 - Capture, Catalog, And Official-Source Validation On The New Register

Outcome label: resolved

Purpose: make the capture and catalog system operate on the new canonical
register while preserving provenance, queue discipline, and explicit gap
handling.

Implementation tasks:

1. Update `dry-run`, `preflight`, `download`, `batch-download`, `validate-run`,
   and `catalog-build` to consume canonical register rows.
2. Define row-state handling for:
   - load-ready corpus rows;
   - deferred direct-file queue rows;
   - removed/deduped audit rows;
   - patched URL evidence rows;
   - superseded/currentness-only rows; and
   - blocked or unresolved rows.
3. Add direct-eval coverage for:
   - queue leakage;
   - patched URL provenance drift;
   - duplicate row reintroduction;
   - direct-file readiness regression;
   - bad listing-page capture;
   - blocked/source-page misclassification; and
   - stale official-source assumptions.
4. Produce the first canonical-register-driven source-set and catalog gate
   without relying on the old workbook contract.
5. Bulk canonical-register ingestion may begin only after the Phase 1.5
   contract-proving slice has passed and its residual contract gaps are closed
   or explicitly rerouted.

Required implementation artifacts:

- canonical-register-driven manifest/report outputs
- updated catalog fields and source-set manifests
- capture and catalog eval fixtures for positive and negative cases
- current-state docs naming the new canonical corpus baseline

Acceptance signals:

- The active catalog can be rebuilt solely from the canonical register.
- Queue rows remain explicit but non-corpus-ready.
- Capture and catalog evals fail closed on row-state or provenance regressions.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources preflight --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --limit 25
PYTHONPATH=src uv run --extra dev pytest tests/test_preflight.py tests/test_validate_run.py tests/test_catalog.py tests/test_upstream_evaluation.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Queue-row leakage cannot be prevented without weakening legitimate load rows.
- Direct-file readiness requires a second hidden manual register.

### Phase 3 - Authority Currentness, Supersession, And Source-Partition Rebase

Outcome label: resolved

Purpose: rebase authority-currentness and source-partition governance onto the
new canonical register so active, superseded, and blocked sources are governed
from the new truth surface.

Implementation tasks:

1. Map canonical register rows to authority families, source partitions, and
   reviewer eligibility states.
2. Update currentness logic so canonical register fields drive:
   - active/current authority coverage;
   - superseded/currentness-only archive coverage;
   - candidate/blocked coverage; and
   - documented non-addition or explicit source gaps.
3. Add explicit temporal lineage artifacts for effective-date, supersession,
   rescission, amendment, and replacement relationships that are reviewer- and
   graph-visible.
4. Expand currentness evals for stale, repealed, reserved, superseded, and
   blocked-source scenarios.
5. Update docs and contracts so the canonical register, not the old workbook,
   is the durable authority-source ledger.

Required implementation artifacts:

- updated `authority-currentness` inputs and report logic
- governed canonical supersession-lineage contract
- projected canonical authority-inventory and source-gap decision artifacts
- updated source-partition logic for canonical historical/currentness rows
- focused currentness regression tests and live currentness report closeout

Acceptance signals:

- Current active authority coverage is proven from the canonical register and
  active catalog.
- Superseded or blocked rows are visible but cannot silently satisfy active
  rule coverage.
- Currentness evals include controlled stale-source and wrong-partition cases.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library
PYTHONPATH=src uv run --extra dev pytest tests/test_source_partitions.py tests/test_authority_currentness.py tests/test_source_register_proving.py tests/test_architecture_contract.py tests/test_nepa_knowledge_graph_export.py
git diff --check
```

Stop conditions:

- Authority-family coverage still depends on undocumented old workbook row IDs.
- Currentness state cannot be derived deterministically from the canonical
  register plus governed contracts.

### Phase 4 - Extraction Fidelity And Verified Source Admission

Outcome label: resolved

Purpose: make extraction accuracy a governed surface for the new canonical
corpus rather than a best-effort parser outcome.

Implementation tasks:

1. Update extraction planning to use canonical register metadata such as:
   document type, link class, docling instructions, currentness state, and
   extraction priority.
2. Expand extraction eval fixtures across:
   - statutes and code chapters;
   - CFR parts and Federal Register materials;
   - USDA/USFS directives and handbook/index pages;
   - forest-plan chapters, appendices, maps, and monitoring reports;
   - OCR/scanned PDFs;
   - table-dense PDFs;
   - split-page section boundaries; and
   - manual-export or queue-adjacent negative cases.
3. Harden verified extraction admission so downstream knowledge-base lanes
   fail closed if required source families lack accurate extraction.
4. Separate parser success from extraction accuracy in docs and gates.

Required implementation artifacts:

- updated extraction planner and parser-selection logic
- expanded extraction eval manifest/fixtures
- updated extraction accuracy and admission reports
- refreshed `docs/OUTPUT_SCHEMAS.md` and `docs/EVALUATION_COVERAGE_REGISTER.md`

Acceptance signals:

- Extraction accuracy is measured by governed categories and negative cases.
- Required source families can be admitted downstream only after extraction
  accuracy passes.
- Parser success alone is insufficient for reviewer-ready or draft-ready
  claims.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing
PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream
PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py tests/test_extraction_accuracy.py tests/test_upstream_evaluation.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Required source classes cannot be represented by the extraction eval
  manifest.
- Downstream gates still accept sources with parser success but failed
  extraction accuracy.

### Phase 5 - Graph Accuracy, Provenance Completeness, And Knowledge-Graph Gating

Outcome label: resolved

Purpose: turn graph correctness into a first-class evaluated contract rather
than an inferred property of a successful graph build.

Implementation status on 2026-05-18: live on
`source_library/derived/source-set-9dcf819bc4cca486/knowledge_graph/`. The
exported canonical source-set graph now passes `nepa-knowledge-graph-export`,
`authority-ontology-validate`, `authority-relationship-eval`,
`citation-alias-eval`, `graph-health-eval`, and `graph-accuracy-eval`, and
`phase-eval` records the five new semantic phases as passed. The inherited
placeholder-artifact proving slice still keeps extraction, retrieval,
evidence-graph, claim-extraction, rule-claim binding, and downstream review
lanes blocked, so this phase does not widen reviewer-ready or promotion-ready
claims beyond the semantic graph boundary.

Implementation tasks:

1. Define a tracked authority ontology and semantic relationship contract
   covering required node classes, relationship types, endpoint rules, and
   reviewer-visible justification-path semantics.
2. Define a tracked graph accuracy manifest covering:
   - required node classes;
   - required edge classes;
   - explicit authority relationship classes;
   - provenance completeness;
   - citation reachability;
   - alias-resolution correctness;
   - justification-path completeness;
   - currentness metadata carriage;
   - orphan-node and disconnected-component thresholds; and
   - controlled negative cases.
3. Add graph eval fixtures for:
   - missing provenance;
   - wrong node typing;
   - missing semantic relationship edges;
   - alias-resolution drift;
   - dropped rule-support edges;
   - broken currentness relationships; and
   - source-to-claim or claim-to-rule linkage regressions.
4. Add graph-health artifacts for orphaning, unresolved aliases,
   relationship-typing drift, and incremental refresh-delta integrity.
5. Extend phase gating so graph accuracy and ontology validation are separate
   from graph build success.
6. Update NEPA graph exports to carry reviewer-visible provenance,
   currentness metadata, semantic relationship typing, confidence, and
   justification-path evidence from the canonical source set.

Required implementation artifacts:

- authority ontology, relationship, alias, and graph-health contracts
- graph accuracy eval contract and fixtures
- focused negative semantic graph fixtures for node-loss, lens-loss, and
  justification-path regressions
- graph accuracy results and summary artifacts
- updated graph export schema docs
- phase-eval integration for graph accuracy

Acceptance signals:

- Graph build success is no longer enough for readiness.
- Node/edge correctness, semantic relationship typing, provenance completeness,
  alias resolution, and currentness carriage are governed by executable evals.
- Reviewer-visible justification paths exist from controlling or interpretive
  authority to review finding.
- Controlled graph regressions fail before promotion.

Closeout note for the active proving slice: `evidence-graph-build` and overall
root `phase-eval` may remain blocked by inherited Phase 4 placeholder-artifact
state. Phase 5 closes only when the source-set semantic graph export and the
five semantic eval families pass without weakening those downstream gates.
Focused negative coverage must also fail representative regressions in
ontology-required source-set node classes, semantic lens presence, and
authority-path justification linkage.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build --output-dir source_library
# On the active proving slice this is expected to remain non-green until real
# direct documents replace the Phase 4 placeholder artifacts. Record that
# blocked boundary; do not weaken or bypass it for Phase 5 closeout.
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources authority-ontology-validate --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources authority-relationship-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources citation-alias-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources graph-health-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources graph-accuracy-eval --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-9dcf819bc4cca486
PYTHONPATH=src uv run --extra dev pytest tests/test_evidence_graph.py tests/test_nepa_3d_graph_contract.py tests/test_graph_accuracy_eval.py tests/test_authority_ontology_starter.py tests/test_phase_eval.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Graph accuracy cannot be expressed without relying on mutable local judgment.
- Graph provenance is lost between source, chunk, claim, and rule layers.

### Phase 6 - Applicability, Rule-Pack, And Legally Accurate Review On The New Corpus

Outcome label: resolved

Purpose: prove that the canonical-register-driven system can produce legally
accurate NEPA review artifacts backed by current sources, accurate extraction,
and accurate graph evidence.

Implementation tasks:

1. Rebase applicability, rule-pack generation, and compliance review onto the
   canonical-register-driven source sets.
2. Expand direct evals and gold evals so they cover:
   - positive and negative applicability;
   - conditional authority triggers;
   - superseded/currentness-only non-applicability;
   - source-family completeness;
   - citation alias normalization;
   - retrieval traces and search coverage certificates;
   - graph-backed citation paths; and
   - reviewer-visible unresolved or adjudicated decisions.
3. Require every review output to show:
   - authority family coverage;
   - controlling vs interpretive vs supporting authority path classifications;
   - applicable vs non-applicable decisions;
   - source citations;
   - retrieval traces or search coverage certificates when they govern the
     decision path;
   - graph or retrieval evidence;
   - unresolved issues; and
   - residual legal-risk categories.
4. Refresh phase-eval and promotion gates to use the canonical-register-driven
   source truth.

Required implementation artifacts:

- updated applicability and compliance contracts
- refreshed eval seeds and gold fixtures
- review outputs and packets on canonical-register-driven source sets
- retrieval-trace and search-coverage artifacts for governed review decisions
- authority-path and explanation-path artifacts for governed review decisions
- updated coverage register and current-state docs

Acceptance signals:

- Review artifacts can be rebuilt from the canonical register without depending
  on the old workbook contract.
- Legally accurate review claims are backed by evals, currentness, and
  provenance artifacts.
- Review packets expose why an authority governs, interprets, supports, or does
  not apply, not just which source row was cited.
- Negative-path and unresolved-authority handling are reviewer-visible.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval --output-dir source_library --source-set-id <canonical_source_set_id> --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json --eval-file config/applicability_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id <canonical_source_set_id> --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id <review_id>
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py tests/test_compliance_review.py tests/test_compliance_review_eval.py tests/test_v1_ea_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Review correctness still depends on undocumented review-local artifacts.
- Review outputs can omit unresolved authority gaps while still passing.

### Phase 7 - Legally Defensible Draft-Document Generation

Outcome label: resolved

Purpose: add a governed document-generation lane that can transform reviewed,
evidence-backed NEPA findings into legally defensible draft document artifacts
without severing citation or authority traceability.

Implementation tasks:

1. Define the supported draft outputs and their evidence requirements. At
   minimum, govern:
   - citation-bearing issue summaries;
   - compliance narrative sections;
   - authority coverage appendices;
   - draft affected-environment or environmental-consequences sections where
     sufficient evidence exists; and
   - reviewer-required unresolved issue statements.
2. Add draft-generation manifests and traceability artifacts that map every
   generated paragraph or section to:
   - source passages;
   - authority families;
   - graph or retrieval paths;
   - review decisions; and
   - unresolved assumptions or missing evidence.
3. Require draft generation to consume only reviewed and traced evidence
   surfaces. It must not draft from workbook rows, raw source files, or prompt
   instructions alone when equivalent reviewed evidence artifacts exist.
4. Build draft-generation eval fixtures that test:
   - unsupported legal conclusion rejection;
   - missing-citation rejection;
   - stale-authority rejection;
   - contradictory evidence rejection; and
   - reviewer-warning insertion for unresolved issues.
5. Add a defensibility packet artifact that summarizes the evidence and residual
   risk behind each generated draft.

Required implementation artifacts:

- draft-generation module and CLI surface
- draft-generation manifest/trace schemas
- draft-generation eval fixtures and results
- unsupported-evidence and refusal artifacts for generation attempts
- defensibility packet outputs and docs

Acceptance signals:

- Draft outputs cannot be produced as "ready" without citation traces and
  residual-risk reporting.
- Unsupported or under-evidenced content fails closed.
- Human review boundaries are explicit in every governed draft output family.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources draft-generate --output-dir source_library --review-id <review_id>
PYTHONPATH=src python -m usfs_r1_ea_sources draft-generation-eval --output-dir source_library --review-id <review_id>
PYTHONPATH=src uv run --extra dev pytest tests/test_draft_generation.py tests/test_draft_generation_eval.py tests/test_review_packet_index.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Draft generation can only succeed by hiding unresolved issues or omitting
  citation provenance.
- The repo cannot express reviewer-facing traceability for generated text.

### Phase 8 - Aggregate Readiness, Real-Package Proving, And Legacy Contract Retirement

Outcome label: resolved

Purpose: close the program by proving the full canonical-register-driven system
on real package and draft-generation lanes, then retire the old workbook
contract as active truth.

Implementation tasks:

1. Extend `phase-eval` so it includes distinct fail-closed phases for:
   - source-register contract validity;
   - capture/catalog direct eval;
   - authority currentness;
   - extraction accuracy;
   - authority ontology and relationship integrity;
   - graph accuracy;
   - downstream direct eval;
   - legally accurate review;
   - draft-generation defensibility.
2. Run at least one real package replay, at least one governed draft-generation
   replay, and at least one controlled source-change refresh replay on the
   canonical-register-driven corpus.
3. Produce an explicit closeout packet against the Figay and Yu rubrics in this
   plan so semantic-legibility and GraphRAG-operability are judged by durable
   artifacts rather than by prose.
4. Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
   `docs/OUTPUT_SCHEMAS.md`, `docs/EVALUATION_COVERAGE_REGISTER.md`, and
   `docs/SESSION_HANDOFF.md` so the old workbook contract is historical only.
5. Quarantine or remove the legacy active-workbook assumptions in code and docs
   after the new path is green.

Required implementation artifacts:

- refreshed aggregate readiness reports
- real review and draft-generation proof artifacts
- source-change refresh proof artifacts
- Figay/Yu rubric closeout packet
- updated docs and handoff closing the legacy contract

Acceptance signals:

- The system can be run end to end from the canonical register without relying
  on the old workbook contract.
- Real-package review and draft-generation lanes are green under the new
  aggregate gate.
- Figay and Yu rubric criteria pass with durable artifacts and evals.
- The old workbook path is no longer documented as active source truth.

Required verification gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id <canonical_source_set_id> --review-id <review_id>
PYTHONPATH=src python -m usfs_r1_ea_sources incremental-graph-refresh-eval --output-dir source_library --source-set-id <canonical_source_set_id>
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_promotion_suite.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- Any legacy workbook assumption remains required for canonical-register-driven
  success.
- Real review or draft-generation outputs can pass without the new aggregate
  gates.

## Required Documentation And Handoff Updates

Each phase closeout must update, when affected:

- this plan
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/SESSION_HANDOFF.md`
- any new register schema, audit, or runbook docs added by the phase

The handoff must record:

- completed phase or partial stop condition;
- exact verification commands run;
- pass/fail counts;
- commit hash for the phase closeout;
- residual risks or accepted limitations; and
- the next phase or blocking issue.

## Required Verification Gates

Across the full plan, the end-state verification stack must include:

- workbook schema validation
- source-register diff or migration integrity proof
- pre-ingestion contract-proving slice
- capture direct eval
- catalog validation and integrity checks
- authority currentness and source-partition validation
- extraction accuracy eval and verified extraction admission
- authority ontology validation
- authority relationship eval
- citation alias and entity-resolution eval
- retrieval/claim/rule/applicability/compliance direct evals
- graph-health and incremental-refresh evals
- graph accuracy eval
- review gold or contract evals
- draft-generation eval
- aggregate `phase-eval`
- promotion or readiness suite
- `tests/test_architecture_contract.py`
- `git diff --check`

No phase may claim `resolved` unless its scoped gates pass and the required docs
and handoff updates land in the same atomic closeout commit.

## Repo-Facing Acceptance Rubric

### Figay Rubric

- `Figay-1: Ontological separation`. Artifact requirement:
  `config/authority_document_ontology_v1.json` and
  `docs/OUTPUT_SCHEMAS.md` must distinguish `source_record`,
  `authority_document`, `authority_section` or equivalent component,
  `jurisdiction_scope`, `forest_plan_component`, and review reasoning objects.
  Eval requirement: `authority-ontology-validate` passes, and a negative
  fixture that collapses `source_record` into `authority_document` fails.
- `Figay-2: Explicit semantic relationships`. Artifact requirement:
  `config/authority_relationship_types_v1.json` and
  `config/authority_relationship_register_v1.json` must encode governing
  relationship types such as implementation, interpretation, supersession,
  amendment, supporting-document linkage, and consistency relationships.
  Eval requirement: `authority-relationship-eval` passes, and fixtures missing
  required relationship types or directions fail.
- `Figay-3: Temporal and normative lineage`. Artifact requirement:
  currentness and lineage artifacts must show effective-date, amendment,
  supersession, rescission, and reviewer-visible status boundaries for
  controlling versus historical sources. Eval requirement:
  `authority-currentness` and `authority-relationship-eval` pass, and a
  controlled stale-lineage fixture fails.
- `Figay-4: Viewpoints and lenses`. Artifact requirement: graph lenses and
  reviewer surfaces must support at least source provenance, authority
  currentness, forest-plan lineage, package applicability, evidence path, and
  readiness blockers without flattening them into one undifferentiated graph.
  Eval requirement: `nepa-knowledge-graph-export` and `graph-accuracy-eval`
  pass with required lens metadata and endpoint rules.
- `Figay-5: Justification paths`. Artifact requirement: review-ready findings
  and governed draft sections must carry authority-path and justification-path
  artifacts that show why the cited authority governs the conclusion. Eval
  requirement: review evals and draft-generation evals fail if a finding or
  draft section lacks a valid traced path from authority to evidence to
  conclusion.

### Yu Rubric

- `Yu-1: Hybrid retrieval and explanation`. Artifact requirement: retrieval
  manifests and traces must show metadata, source-role, source-text, graph
  expansion, and optional vector/query-plan participation where supported. Eval
  requirement: retrieval/applicability evals fail if review decisions cannot be
  reconstructed from retrieval traces and selected/rejected evidence.
- `Yu-2: Entity resolution and alias stability`. Artifact requirement:
  `config/citation_alias_register_v1.json`, alias-resolution reports, and
  unresolved-alias ledgers must keep statutes, CFR parts, directives, and plan
  materials on stable identities. Eval requirement: `citation-alias-eval`
  passes, and controlled alias-collision fixtures fail.
- `Yu-3: Graph health and consistency evolution`. Artifact requirement:
  `config/graph_health_contract_v1.json` plus graph-health reports must track
  orphan rates, disconnected components, stale aliases, relationship-typing
  drift, and refresh-delta integrity. Eval requirement: `graph-health-eval`
  passes, and fixtures that introduce silent graph degradation fail.
- `Yu-4: Corpus-change resilience`. Artifact requirement: refresh-delta
  artifacts must prove the graph and review lanes can absorb new, changed, or
  superseded source rows without silent semantic drift. Eval requirement:
  `incremental-graph-refresh-eval` passes on controlled source-change fixtures.
- `Yu-5: Multi-format document robustness`. Artifact requirement: extraction
  and admission artifacts must cover born-digital PDFs, OCR PDFs, tables,
  chaptered directives, maps, appendices, and forest-plan support documents.
  Eval requirement: extraction-accuracy and upstream evaluation categories
  remain green across those source classes.
- `Yu-6: Reviewer-visible operational safety`. Artifact requirement: review and
  draft outputs must emit unsupported-evidence, unresolved-authority,
  contradiction, and refusal artifacts when evidence is weak. Eval requirement:
  compliance-review and draft-generation evals fail if the system answers with
  unsupported certainty.

## Acceptance Criteria

The full plan is complete only when all of the following are true:

- The canonical workbook is the only human-authored source register used to
  define corpus-ready source rows.
- The system can prove which workbook sheets are load vs non-load, and queue or
  audit sheets cannot leak into the active corpus.
- Identity, ontology, relationship, currentness, scope, alias, and
  direct-file-readiness contracts were frozen and validated on a representative
  proving slice before bulk document ingestion began.
- Every active source row is captured, validated, cataloged, and placed into
  the correct source-partition/currentness state, or it is explicitly carried as
  blocked, deferred, or superseded with reviewer-visible evidence.
- Extraction accuracy passes for all governed source classes required by the
  canonical corpus and the review lanes.
- Graph accuracy passes for all governed node, edge, provenance, and
  currentness-carrying requirements.
- Authority ontology, semantic relationship, alias-resolution, and
  justification-path evals pass on the canonical corpus.
- Legally accurate review artifacts pass direct eval and gold/contract eval
  gates on the canonical-register-driven corpus.
- Draft-generation outputs pass defensibility and traceability evals and
  explicitly preserve human-review boundaries.
- NEPA-specific domain rules, source states, and reviewer expectations are
  represented as data, contracts, eval fixtures, or reviewer-visible reports
  rather than as hidden runtime heuristics.
- When quality is weak, the documented next step is stronger corpus,
  extraction, retrieval, graph, currentness, or eval coverage before bespoke
  logic.
- The Figay and Yu rubric criteria pass through durable repo artifacts and
  executable evals rather than reviewer impression.
- Aggregate phase-eval and readiness/promotion gates pass on the new canonical
  source system.
- The old workbook contract is documented only as historical or migration
  context, not as active truth.

## Stop Conditions

Stop and reroute before continuing if any of the following occurs:

- the workbook contract changes again before Phase 0 closes;
- the canonical workbook cannot be versioned or checksummed reproducibly;
- the pre-ingestion contract-proving slice exposes unresolved contract drift
  that would force bulk-ingest refactors;
- the old workbook still functions as required operational truth because the
  explicit canonical cutover boundary has not yet been reached;
- queue-row promotion requires undocumented manual intervention;
- currentness or supersession cannot be represented cleanly from the canonical
  register;
- extraction or graph accuracy cannot be expressed as governed eval categories;
- draft-generation outputs cannot be made traceable to sources and review
  evidence;
- legal-accuracy claims drift into unsupported autonomous legal advice rather
  than evidence-backed reviewer support; or
- required verification fails and cannot be repaired within the scoped phase.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no phase may be marked complete, `resolved`,
  or `reduced` until the scoped verification stack passes, the required docs
  and handoff updates are written, and the local atomic closeout commit exists.
- A phase is not complete until the scoped verification stack passes, the
  required docs and handoff updates land, and the local atomic closeout commit
  exists.
- Close each phase with one local atomic commit after the scoped verification
  stack passes.
- Stage only the verified phase slice.
- Leave unrelated dirty or untracked files alone.
- Include implementation, tests, docs, contracts, generated eval outputs that
  are repository-tracked, and handoff updates in the same phase commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat a phase as incomplete until the commit exists.

## Residual Risks And Next Routing

Residual risks expected at plan creation:

- The old workbook semantics are deeply embedded in the current foundation and
  may reveal more migration coupling than the initial read-only pass shows.
- The new canonical workbook is rich enough that hidden assumptions about load
  vs audit vs queue semantics could reappear unless the sheet contract is made
  executable immediately.
- Draft-generation defensibility is the newest and most legally sensitive lane;
  it should not be treated as a thin wrapper around review outputs.
- Semantic authority modeling and graph evolution are the highest risk for
  future drift because they are easy to approximate with ad hoc heuristics.
  The ontology, alias, relationship, and graph-health gates must remain strict.

Next routing:

- Start with Phase 0.
- Do not begin source capture or loader rewrites until the workbook audit,
  sheet contract, and migration baseline are committed.
- If Phase 0 reveals that the canonical workbook still needs schema surgery,
  stop there and write a narrower workbook-normalization follow-on before
  touching runtime code.
