# First-Class Eval Trace Implementation Milestone Plan

Date: 2026-05-28

Status: Resolved locally. Milestone 0 contract and baseline inventory design,
Milestone 1 read-only inventory CLI, Milestone 2 local DB-backed eval/trace
store, Milestone 3 canonical/OpenInference export, Milestone 4
phase/promotion gate integration, and Milestone 5 trace-to-case promotion are
resolved locally. Milestones 0-5 now cover contract, inventory, store, export,
phase/promotion gate integration, and local trace-to-case feedback-loop
mechanics.

Owner context: This plan implements the direction captured in
`docs/FIRST_CLASS_EVALS_AND_TRACES_RESEARCH_BRIEF.md` for this repository. The
packet was routed after West Reservoir Milestone 4 and is now closed locally.
Any hosted scoring, model-judge, or broader trace integration follow-up must be
opened as a new approved milestone before editing code.

## Purpose

This repository already has strong deterministic eval commands, replay contexts,
artifact hashes, retrieval traces, review gates, and promotion manifests. The
weakness is that those pieces are not first-class as one queryable eval/trace
substrate. A future agent or reviewer still has to know which result artifact,
trace file, replay context, catalog, source-set manifest, and promotion gate to
open for each workflow.

This milestone sequence makes evals and traces first-class by adding a
repo-owned contract, read-only inventory, local DB-backed store, export shape,
and gate integration while preserving the existing domain-specific eval
commands.

The implementation principle is local sovereignty first. Braintrust,
LangSmith, Phoenix, OTLP, and OpenInference are inspection or export targets,
not the durable system of record.

## Current Evidence

- `docs/FIRST_CLASS_EVALS_AND_TRACES_RESEARCH_BRIEF.md` concludes that the
  correct first slice is a local contract plus read-only inventory, not hosted
  observability wiring or immediate migrations.
- `docs/EVALUATION_COVERAGE_REGISTER.md` already separates structural
  validation from direct-eval coverage across upstream, retrieval, claim,
  rule-claim, compliance, forest-plan profile, forest-specific package, gold,
  V1, and promotion lanes.
- `src/usfs_r1_ea_sources/phase_eval.py` already assembles many readiness
  artifacts, including direct-eval summaries, replay-context source-set checks,
  applicability retrieval traces, graph traces, component evals, V1 evals, and
  promotion-adjacent review artifacts.
- `src/usfs_r1_ea_sources/applicability_retrieval.py` writes
  `applicability_retrieval_trace.jsonl`,
  `applicability_graph_trace.jsonl`, and diagnostics with SHA-256 hashes.
- `docs/OUTPUT_SCHEMAS.md` documents current generated eval and trace artifacts,
  including `source_library/evaluations/*`, retrieval eval outputs, claim eval
  outputs, rule-claim eval outputs, `phase_eval_results.json`, and review-scope
  applicability trace gates.
- `docs/ARCHITECTURE.md` and `docs/architecture_contract.toml` already treat
  eval and CLI command groups as explicit architecture surfaces.

## Goal

Make evals and traces first-class enough that a local command can answer, for a
source set or review:

- which eval contracts, result artifacts, scorer/threshold versions, and pass
  states exist;
- which traces, replay contexts, catalog surfaces, source rows, artifacts,
  claims, findings, reports, and promotion gates the evals used;
- which required cross-links are missing;
- which rows can be exported as canonical JSON and OpenInference-compatible
  span trees;
- which failed evals or missing traces block source-set, review, graph, report,
  memory, profile, or package promotion.

Completion means the repo has:

- a committed first-class eval/trace contract doc and schema/config contract;
- a read-only `eval-trace-inventory` CLI with focused tests;
- a local SQLite-backed eval/trace store populated from existing artifacts;
- canonical JSON and OpenInference-compatible exports;
- phase/promotion/readiness gate integration that can fail closed when the
  selected inventory or store is stale, incomplete, or below threshold;
- updated docs, handoff, output schema, architecture contract, and coverage
  register for every completed slice.

## Non-Goals

- Do not replace `phase-eval`, `v1-ea-eval`, `retrieval-eval`,
  `compliance-review-eval`, `forest-plan-component-eval`, or other
  domain-specific eval commands.
- Do not wire a hosted observability platform as the system of record.
- Do not run large downloader, extraction, review, compliance, or network
  workflows just to build the inventory.
- Do not stage generated `source_library/` artifacts unless repo policy changes
  or the user explicitly asks.
- Do not make model judges the default scorer. Use deterministic checks first.
- Do not mix this implementation with the active West Reservoir signer-facing
  packet closeout.

## Scope

- Eval/trace contract documentation.
- Read-only inventory over existing repo artifacts.
- Local generated SQLite store for generic eval/trace rows.
- Canonical JSON and OpenInference-compatible export.
- CLI registration in the eval command group.
- Focused unit tests and architecture-contract tests.
- Docs and handoff closeout for the new command, generated outputs, and gates.

## Out Of Scope

- Corpus capture, workbook source-row changes, downloader behavior, URL
  preflight semantics, or catalog regeneration.
- Rewriting retrieval, claim, rule-claim, compliance, forest-plan, V1, gold, or
  promotion eval scoring logic.
- Full tracing instrumentation for every command in one milestone.
- LLM judge implementation before deterministic inventory/store gates exist.
- Any cloud export, background online scoring service, or external API
  submission.

## Owner Surfaces

Planned docs and contracts:

- `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`
- `docs/FIRST_CLASS_EVAL_TRACE_IMPLEMENTATION_MILESTONE_PLAN.md`
- `docs/FIRST_CLASS_EVALS_AND_TRACES_RESEARCH_BRIEF.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture_contract.toml`
- `docs/SESSION_HANDOFF.md`
- `docs/CURRENT_SYSTEM_STATE.md` only when implementation changes current
  route, readiness state, command surfaces, or generated artifact truth

Planned code:

- `src/usfs_r1_ea_sources/eval_trace_contract.py`
- `src/usfs_r1_ea_sources/eval_trace_inventory.py`
- `src/usfs_r1_ea_sources/eval_trace_store.py`
- `src/usfs_r1_ea_sources/eval_trace_export.py`
- `src/usfs_r1_ea_sources/eval_trace_case_promote.py`
- `src/usfs_r1_ea_sources/cli_eval.py`
- `src/usfs_r1_ea_sources/cli_eval_registration.py`
- `src/usfs_r1_ea_sources/cli_eval_dispatch.py`
- `src/usfs_r1_ea_sources/phase_eval.py`
- `src/usfs_r1_ea_sources/promotion_suite*.py` only in the gate-integration
  milestone

Planned tests:

- `tests/test_eval_trace_contract.py`
- `tests/test_eval_trace_inventory.py`
- `tests/test_eval_trace_store.py`
- `tests/test_eval_trace_export.py`
- `tests/test_eval_trace_case_promote.py`
- `tests/test_cli_eval.py`
- `tests/test_phase_eval.py` or focused phase-eval gate tests
- `tests/test_architecture_contract.py`

Planned public commands:

- `eval-trace-inventory`
- `eval-trace-store-build`
- `eval-trace-export`
- `eval-trace-case-promote`

Generated local artifacts:

- `source_library/evaluations/eval_trace_inventory/eval_trace_inventory_results.json`
- `source_library/evaluations/eval_trace_inventory/eval_trace_inventory_report.md`
- `source_library/evaluations/eval_trace/system_eval_trace.sqlite`
- `source_library/evaluations/eval_trace/system_eval_trace_export.json`
- `source_library/evaluations/eval_trace/openinference_traces.json`

## Placement Rules

- Keep inventory and store logic in new small owner modules. Do not enlarge
  `phase_eval.py` with inventory implementation details.
- CLI registration belongs to the eval command group. Public command name:
  `eval-trace-inventory`.
- The first command must be read-only with respect to existing corpus and review
  artifacts. It may write an inventory report only to an explicit output path or
  the owned eval-trace inventory directory.
- Store rows are generated from existing artifacts. Existing eval commands remain
  the producers of domain-specific truth.
- The SQLite store is a generated local artifact under `source_library/`, not a
  committed database.
- Contract enum values must be data-visible. Do not hide eval kinds, trace
  kinds, span kinds, score kinds, source kinds, or gate kinds in ad hoc string
  branches.
- Export shape must preserve local IDs and artifact hashes. OTLP/OpenInference
  compatibility must not erase workbook row, source-record, review, source-set,
  or artifact provenance.
- Any new module must be added to `docs/architecture_contract.toml` and covered
  by `tests/test_architecture_contract.py`.

## Canonical Object Model

Use these objects as the local generic model while linking to existing
domain-specific artifacts:

- `system_eval_runs`
- `system_eval_cases`
- `system_eval_case_results`
- `system_eval_scores`
- `trace_runs`
- `trace_spans`

Required enum families:

- `eval_kind`: `capture`, `catalog`, `extraction_fidelity`, `retrieval`,
  `claim`, `rule_claim`, `applicability`, `forest_plan_component`,
  `forest_plan_profile`, `compliance_review`, `compliance_gold`, `v1_ea`,
  `real_package_review_coverage`, `gold_coverage`, `promotion_suite`,
  `phase_eval`, `decision_support`, `final_qa`, `packet_index`,
  `project_sow`, `semantic_graph`, `semantic_generation`
- `trace_kind`: `capture`, `validation`, `evaluation`, `search`, `replay`,
  `workbook_capture`, `agent_task`, `semantic_generation`,
  `technical_report`, `graph_readiness`, `semantic_memory_publication`,
  `review_package`, `applicability_retrieval`, `applicability_graph`
- `span_kind`: `workflow`, `ingest`, `parse`, `validate`, `chunk`,
  `table_extract`, `figure_extract`, `embed`, `retrieve`, `rerank`,
  `search`, `llm`, `tool`, `agent_task`, `approval`, `evaluation`, `score`,
  `artifact`, `guardrail`, `error`
- `score_kind`: `deterministic_code`, `schema`, `retrieval`,
  `groundedness`, `tool_selection`, `tool_arguments`, `trace_integrity`,
  `safety_security`, `latency`, `cost`, `human_label`, `llm_judge`

OpenInference mapping:

- `retrieve` maps to OpenTelemetry `gen_ai.operation.name=retrieval` and
  OpenInference `RETRIEVER`.
- `rerank` maps to OpenInference `RERANKER`.
- `embed` maps to OpenTelemetry embeddings and OpenInference `EMBEDDING`.
- `tool` maps to tool execution and OpenInference `TOOL`.
- `evaluation` and `score` map to OpenInference `EVALUATOR`.
- `llm` maps to OpenInference `LLM`.
- `workflow` maps to OpenInference `CHAIN` or `AGENT` depending on the
  workflow contract.

## Weak-Point Prevention Contract

### 1. Inventory Without Linkability

- Weak point forecast: the inventory lists files but does not prove that evals,
  traces, replay contexts, source-set manifests, and promotion gates actually
  link to the same review/source-set.
- Owner surface: `eval_trace_inventory.py`,
  `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`, and
  `tests/test_eval_trace_inventory.py`.
- Prevention gate: inventory tests must include a stale replay-context source
  set, a missing trace hash, and a mismatched review ID.
- Fail threshold: an inventory result reports `passed=true` while any required
  source-set, review ID, trace hash, catalog path, or result artifact is absent
  or mismatched.
- Controlled violation: fixture review has `phase_eval_results.json` for one
  source set and `v1_ea_eval_results.json` for another; inventory must fail
  with a typed `source_set_mismatch`.
- Future-Codex misuse scenario: a future session counts artifact presence only.
  The contract must require link checks, not file existence checks.

### 2. New Generic Store Replaces Domain Evals

- Weak point forecast: generic eval tables become a shadow evaluator and drift
  from existing domain-specific commands.
- Owner surface: `eval_trace_store.py`, existing eval command modules, and
  `docs/EVALUATION_COVERAGE_REGISTER.md`.
- Prevention gate: store tests must load generated rows only from existing eval
  artifacts and verify that each generic run has an `origin_artifact_ref`.
- Fail threshold: store creation can synthesize a passed eval with no
  originating eval artifact or scorer contract.
- Controlled violation: remove the underlying `retrieval_eval_results.json`;
  the generic store row must be absent or blocked, never invented.
- Future-Codex misuse scenario: a later implementation writes generic
  pass/fail decisions directly in the store. The store contract must make the
  domain artifact the owner of domain score truth.

### 3. Hosted Observability Becomes The Source Of Record

- Weak point forecast: export integration sends useful traces out of the repo
  but leaves no local durable record.
- Owner surface: `eval_trace_export.py`, local SQLite store, and
  `docs/OUTPUT_SCHEMAS.md`.
- Prevention gate: export tests must require a local store row and canonical
  JSON export before any OpenInference-shaped export can pass.
- Fail threshold: `openinference_traces.json` can be generated without
  `system_eval_trace.sqlite` and `system_eval_trace_export.json`.
- Controlled violation: delete local canonical export and run export; command
  must fail.
- Future-Codex misuse scenario: a future session adds a Braintrust/Phoenix
  client path first. The plan blocks external export until local artifacts are
  complete.

### 4. Deterministic Gates Are Replaced By LLM Judges

- Weak point forecast: model judges are used where schema, hash, source-record,
  citation, retrieval, or rule checks already exist.
- Owner surface: `eval_trace_contract.py`, scorer-kind enum, tests, and
  `docs/EVALUATION_COVERAGE_REGISTER.md`.
- Prevention gate: contract validation requires deterministic scorer kinds for
  existing deterministic lanes and requires judge metadata for any future
  `llm_judge` score.
- Fail threshold: a deterministic lane such as `retrieval`, `phase_eval`, or
  `v1_ea` can pass using only `llm_judge`.
- Controlled violation: fixture result marks `score_kind="llm_judge"` without
  judge model, prompt hash, rubric hash, temperature, examples, and output
  schema; validation must fail.
- Future-Codex misuse scenario: a future session adds a judge to get around a
  hard deterministic failure. The contract prevents that from satisfying the
  gate.

### 5. Trace Export Loses Provenance

- Weak point forecast: OpenInference-compatible spans are useful in tooling but
  drop workbook row, source record, review ID, source-set ID, artifact hash, or
  citation labels.
- Owner surface: `eval_trace_export.py` and export tests.
- Prevention gate: export tests assert required local attributes remain present
  on root traces and artifact/retrieval/evaluation spans.
- Fail threshold: any exported span that represents a source-backed operation
  lacks `source_set_id`, `source_ref_kind`, `source_ref_id`, or artifact hash
  when those values exist locally.
- Controlled violation: remove `source_record_id` from a retrieval span fixture;
  export validation must fail with `missing_source_ref`.
- Future-Codex misuse scenario: a future session optimizes for platform display
  and strips local provenance. The export contract blocks lossy export.

### 6. Gate Integration Blocks Active Work Prematurely

- Weak point forecast: phase-eval or promotion-suite starts requiring the new
  inventory before the inventory/store artifacts are stable, blocking unrelated
  active review packets.
- Owner surface: `phase_eval.py`, `promotion_suite*.py`, and routing docs.
- Prevention gate: gate integration milestone must first add optional/reporting
  mode, then ratchet fail-closed behavior only for explicitly declared source
  sets/reviews in a tracked contract.
- Fail threshold: active West Reservoir packet or unrelated review-scoped
  `phase-eval` fails only because no eval-trace store exists before the ratchet
  contract includes that review.
- Controlled violation: run a review-scoped phase-eval fixture without
  eval-trace artifacts before ratchet; it must report optional status, not fail.
- Future-Codex misuse scenario: a future session toggles global fail-closed
  behavior too early. The ratchet contract makes the enabled scope explicit.

## Blocker Contract Map

### Inventory CLI Contract

- Stable public command: `eval-trace-inventory`.
- Public options: `--output-dir`, `--source-set-id`, `--review-id`,
  `--catalog-dir`, `--results-path`, `--format json|markdown`, and
  `--fail-on-missing-required`.
- Must not mutate existing review, catalog, extraction, retrieval, or
  compliance artifacts.
- Unit tests: command registration, JSON schema, missing artifact, stale
  source-set, stale review ID, optional write path.
- Integration tests: fixture source-set inventory and fixture review inventory.

### Command Surface Contract

- Stable public commands: `eval-trace-inventory`, `eval-trace-store-build`,
  `eval-trace-export`, and `eval-trace-case-promote`.
- Command registration belongs to the eval command group and must be covered by
  `tests/test_cli_eval.py`.
- Each command must document whether it is read-only, generated-artifact-only,
  or tracked-config-writing.
- No command may silently mutate existing catalog, extraction, retrieval,
  review, compliance, or promotion artifacts.
- Tests: command registration, help text, required options, default write
  policy, and failure on unsafe implicit mutation.

### Phase Eval Contract

- Stable command: `phase-eval`.
- Existing behavior must remain unchanged until the ratchet contract explicitly
  requires eval-trace inventory.
- Review-scoped phase eval must continue to honor tracked replay contexts and
  fail closed on source-set/catalog mismatches.
- Direct tests: optional eval-trace status, ratcheted missing-inventory failure,
  stale inventory failure.

### Applicability Trace Contract

- Existing artifacts:
  `applicability_retrieval_trace.jsonl`,
  `applicability_graph_trace.jsonl`, and
  `applicability_retrieval_graph_diagnostics.json`.
- Inventory/store must preserve row IDs, hashes, candidate IDs, query types,
  source-set IDs, and review IDs.
- Tests: trace hash mismatch, missing fused retrieval row, missing graph trace
  diagnostics, and source-set mismatch.

### Generic Store Contract

- Generated SQLite path:
  `source_library/evaluations/eval_trace/system_eval_trace.sqlite`.
- Tables: `system_eval_runs`, `system_eval_cases`,
  `system_eval_case_results`, `system_eval_scores`, `trace_runs`,
  `trace_spans`.
- Store rows must include schema version, source artifact references, source
  hashes where available, status, timestamps or generated-at values, and
  typed failure categories.
- Tests: schema creation, idempotent rebuild, no duplicate rows, source artifact
  deletion, and stale-hash detection.

### Export Contract

- Commands may export canonical JSON and OpenInference-compatible JSON.
- Export must be generated from local store rows, not directly from scattered
  source artifacts.
- Tests: OpenInference span kind mapping, root/child hierarchy, preserved local
  provenance attributes, and blocked lossy export.

## Milestone Sequence

### Milestone 0: Contract And Baseline Inventory Design

Outcome label: resolved for the missing contract; reduced for first-class evals
overall because no runtime inventory exists yet.

Status: Resolved locally on 2026-05-28. The tracked contract config,
validation helper, contract doc, architecture ownership, coverage-register
entry, and focused tests are implemented. No inventory CLI, SQLite store,
export, or gate ratchet exists yet.

Implementation:

- Add `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`.
- Add `config/eval_trace_inventory_contract_v1.json` with enum values,
  required artifact families, required link checks, schema versions, and
  initial ratchet scopes.
- Add contract validation helpers in `eval_trace_contract.py`.
- Add focused tests proving unsupported enum values, missing required link
  checks, and premature global ratchets fail.

Required docs refresh:

- `docs/EVALUATION_COVERAGE_REGISTER.md` adds a queued row for first-class
  eval/trace inventory with status `direct_eval_strengthening_planned`.
- `docs/ARCHITECTURE.md` and `docs/architecture_contract.toml` add the new
  contract owner module.
- `docs/SESSION_HANDOFF.md` records this milestone only if implementation is
  active, not when the plan is merely queued.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_eval_trace_contract.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/eval_trace_contract.py tests/test_eval_trace_contract.py
PYTHONPATH=src python -m compileall src/usfs_r1_ea_sources/eval_trace_contract.py tests/test_eval_trace_contract.py
git diff --check
```

Commit closeout:

- Commit contract code, tests, config, architecture docs, coverage register,
  output schema additions if any, and handoff update if this packet is active.

### Milestone 1: Read-Only Eval Trace Inventory CLI

Outcome label: reduced. At Milestone 1 closeout the repo gained a queryable
inventory, while the generic DB-backed store remained a later slice.

Status: Resolved locally. `eval_trace_inventory.py` and the
`eval-trace-inventory` CLI now inventory source-set and review scopes without
mutating existing artifacts. The West Reservoir f70 seed run passed with `18`
required artifact rows present, `0` missing required artifacts, `0` source-set
or review-ID mismatches, `0` trace-hash mismatches, and
`export_readiness.reason="sqlite_store_not_built"`. The newer Milestone 2
section below now records the implemented local SQLite store.

Implementation:

- Add `eval_trace_inventory.py`.
- Register `eval-trace-inventory` in the eval CLI group.
- Inventory source-set and review scopes without mutating existing artifacts.
- Emit typed `coverage_status`, `required_link_status`, `missing_cross_links`,
  `stale_artifacts`, `source_set_mismatches`, `review_id_mismatches`,
  `trace_hash_mismatches`, and `export_readiness` fields.
- Support stdout JSON by default plus explicit `--results-path` writes.
- Add fixture tests for source-set-only and review-scoped inventory.
- Add negative tests for missing replay context, mismatched source-set, missing
  applicability trace, missing eval result, stale trace hash, and malformed
  result schema.

Required docs refresh:

- `docs/OUTPUT_SCHEMAS.md` documents inventory input surfaces and result JSON.
- `docs/EVALUATION_COVERAGE_REGISTER.md` updates the first-class eval/trace row
  with the implemented command and current status.
- `docs/SESSION_HANDOFF.md` records next step and residual risk if this packet
  is active.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_eval_trace_inventory.py tests/test_cli_eval.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/eval_trace_contract.py src/usfs_r1_ea_sources/eval_trace_inventory.py src/usfs_r1_ea_sources/cli_eval.py src/usfs_r1_ea_sources/cli_eval_registration.py tests/test_eval_trace_inventory.py tests/test_cli_eval.py
PYTHONPATH=src python -m compileall src/usfs_r1_ea_sources/eval_trace_contract.py src/usfs_r1_ea_sources/eval_trace_inventory.py tests/test_eval_trace_inventory.py
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-inventory --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --format json --results-path /tmp/usfs-r1-eval-trace-inventory.json
git diff --check
```

Commit closeout:

- Commit code, tests, CLI docs, output schemas, coverage register, architecture
  contract updates, and handoff update if active. Do not commit `/tmp` output
  or ignored `source_library/` generated evidence.

### Milestone 2: Local DB-Backed Eval Trace Store

Outcome label: reduced. At Milestone 2 closeout the repo gained a DB-backed
generic store, while export and promotion ratchets remained later slices.

Status: Resolved locally on 2026-05-29. `eval_trace_store.py` and the
`eval-trace-store-build` CLI now rebuild the generated local SQLite store from
inventory JSON. The West Reservoir f70 seed build passed with `18` rows in each
canonical table, `0` orphan rows, `0` duplicate IDs, `0` stale artifacts, `0`
source artifact deletions, and `0` missing required links. Canonical JSON,
OpenInference exports, phase/promotion ratchets, and trace-to-case promotion
remained future milestones at that checkpoint; the newer Milestone 3 and
Milestone 4 sections below now record local export readiness and phase/promotion
gate integration.

Implementation:

- Add `eval_trace_store.py`.
- Build `system_eval_trace.sqlite` from inventory rows and existing result
  artifacts.
- Create tables for `system_eval_runs`, `system_eval_cases`,
  `system_eval_case_results`, `system_eval_scores`, `trace_runs`, and
  `trace_spans`.
- Preserve source artifact refs, hashes, review ID, source-set ID, source
  record IDs, catalog refs, replay context refs, eval contract refs, scorer
  versions, thresholds, and failure categories.
- Add idempotent rebuild behavior. Re-running the command on unchanged inputs
  must produce the same row identities and no duplicates.
- Add store validation summary with row counts, orphan counts, stale artifact
  counts, and missing required link counts.

Required docs refresh:

- `docs/OUTPUT_SCHEMAS.md` documents the SQLite tables and generated summary.
- `docs/EVALUATION_COVERAGE_REGISTER.md` records DB-backed status and the store
  command.
- `docs/ARCHITECTURE.md` and `docs/architecture_contract.toml` add store module
  ownership.
- `docs/SESSION_HANDOFF.md` records whether store readiness is green, red, or
  scoped to fixtures if this packet is active.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_eval_trace_store.py tests/test_eval_trace_inventory.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/eval_trace_store.py tests/test_eval_trace_store.py
PYTHONPATH=src python -m compileall src/usfs_r1_ea_sources/eval_trace_store.py tests/test_eval_trace_store.py
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-inventory --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --results-path /tmp/usfs-r1-eval-trace-inventory.json
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-store-build --inventory-path /tmp/usfs-r1-eval-trace-inventory.json --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite --summary-path /tmp/usfs-r1-system-eval-trace-summary.json
git diff --check
```

Commit closeout:

- Commit code, tests, CLI registration, schemas/docs, architecture contract, and
  handoff update if active. Do not commit generated SQLite evidence unless repo
  policy changes.

### Milestone 3: Canonical JSON And OpenInference-Compatible Export

Outcome label: reduced. Export exists, but production-style online scoring and
hosted integrations remain out of scope.

Status: Resolved locally on 2026-05-29. `eval_trace_export.py` and the
`eval-trace-export` CLI now export canonical local JSON and OpenInference-shaped
span trees from the local SQLite store. The West Reservoir f70 seed export
passed with `18` traces, `36` OpenInference-shaped spans, `0` missing tables,
and `0` missing provenance fields. At that checkpoint, phase/promotion ratchets
and trace-to-case promotion remained future milestones; the newer Milestone 4
and Milestone 5 sections below now record both follow-on closeouts.

Implementation:

- Add `eval_trace_export.py`.
- Export canonical JSON from the local store with full local provenance.
- Export OpenInference-compatible trace JSON with root/child hierarchy and span
  kind mappings.
- Validate that source-backed spans preserve source-set, review ID, source
  record ID, artifact hash, result path, and citation/provenance attrs when
  present.
- Add explicit redaction-policy fields. The default export policy is local,
  unredacted only to local files; external export must require a later approval
  milestone.

Required docs refresh:

- `docs/OUTPUT_SCHEMAS.md` documents canonical JSON and OpenInference JSON
  shapes.
- `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md` documents export mapping and
  redaction policy.
- `docs/EVALUATION_COVERAGE_REGISTER.md` records export readiness.
- `docs/SESSION_HANDOFF.md` records residual risk if active.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_eval_trace_export.py tests/test_eval_trace_store.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/eval_trace_export.py tests/test_eval_trace_export.py
PYTHONPATH=src python -m compileall src/usfs_r1_ea_sources/eval_trace_export.py tests/test_eval_trace_export.py
PYTHONPATH=src python -m usfs_r1_ea_sources eval-trace-export --sqlite-path /tmp/usfs-r1-system-eval-trace.sqlite --canonical-json-path /tmp/usfs-r1-system-eval-trace-export.json --openinference-json-path /tmp/usfs-r1-openinference-traces.json
git diff --check
```

Commit closeout:

- Commit export code, tests, docs, architecture contract updates, and handoff
  update if active.

### Milestone 4: Phase Eval And Promotion Gate Integration

Outcome label: resolved for gateability of selected scopes; reduced for any
source sets or reviews not yet ratcheted into the contract.

Status: Resolved locally on 2026-05-29. `eval_trace_gate.py` now validates the
default inventory and SQLite store paths for a selected source-set/review scope,
reports optional non-blocking status for unratcheted scopes, and fails closed for
the explicitly ratcheted review `west-reservoir-67436`. `phase-eval` writes a
top-level `eval_trace_gate` object and appends `first_class_eval_trace` only for
matching evidence or ratcheted scopes. `promotion-suite` reads phase-eval gate
objects and blocks current promotion when a required current-promotion
phase-eval artifact reports a failed ratcheted eval-trace gate. No global or
source-set-wide ratchet is enabled.
The store builder now carries a phase-eval self-refresh allowance: a parseable
failed `phase_eval` artifact can seed a store rebuild before `phase-eval`
rewrites its own result file, while missing, stale-hash, malformed,
unrecognized-schema, and failed non-`phase_eval` origin artifacts still block.
The final closeout pass refreshed local final-QA and eval-trace generated
evidence, then West Reservoir `phase-eval --review-id west-reservoir-67436`
passed twice at `32/32`, `final-qa-certification --validate-only` passed
`200/200`, and `promotion-suite --manifest config/promotion_suite_v1.json`
passed current promotion `32/32` with no failed current eval-trace gates.

Implementation:

- Add optional `eval_trace_inventory` or `eval_trace_store` phase into
  `phase-eval` when an inventory/store artifact exists.
- Add contract-ratcheted fail-closed behavior only for source sets or reviews
  explicitly listed in `config/eval_trace_inventory_contract_v1.json`.
- Add promotion-suite integration only after phase-eval reports the selected
  first-class eval/trace gate.
- Ensure active review packets not listed in the ratchet contract do not fail
  solely because eval-trace artifacts are absent.
- Add tests for optional mode, required mode, stale inventory, stale store,
  missing trace rows, missing eval rows, and mismatched source-set/review.

Required docs refresh:

- `docs/EVALUATION_COVERAGE_REGISTER.md` updates first-class eval/trace status
  for ratcheted scopes.
- `docs/OUTPUT_SCHEMAS.md` documents phase/promotion fields.
- `docs/CURRENT_SYSTEM_STATE.md` records only confirmed current-state truth, not
  planned future ratchets.
- `docs/SESSION_HANDOFF.md` records the exact ratcheted scopes, verification,
  residual risk, and next route if this packet is active.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval.py tests/test_promotion_suite.py tests/test_eval_trace_inventory.py tests/test_eval_trace_store.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id west-reservoir-67436
git diff --check
```

Commit closeout:

- Commit only the verified gate slice: code, tests, contract ratchets, docs,
  handoff, and any explicitly approved generated eval-trace report artifacts.

### Milestone 5: Trace-To-Case Promotion And Feedback Loop

Status: Resolved locally on 2026-05-29. The `eval-trace-case-promote` command
now promotes selected trace/span rows from the local SQLite store into the
tracked `config/eval_trace_cases/system_eval_trace_cases_v1.json` case-file
schema. The command requires source artifact refs and hashes, owner/risk/tags,
an assertion or expected-output contract, review/removal conditions, and fails
closed on duplicate case IDs unless `--replace` is supplied. Deterministic
scorer contracts, human-label metadata, and explicit deferred `llm_judge`
metadata are present; uncalibrated model-judge scoring remains blocked and
tracked in `docs/TECH_DEBT_REGISTER.md`.

Verified closeout on 2026-05-29:

- `pytest tests/test_eval_trace_case_promote.py tests/test_eval_trace_store.py tests/test_architecture_contract.py tests/test_cli_eval.py -q`
  passed `46/46`.
- `ruff check src tests`, `python -m compileall src`, `git diff --check`, and
  `python -m usfs_r1_ea_sources --help` passed.
- A local `eval-trace-case-promote` smoke run against
  `source_library/evaluations/eval_trace/system_eval_trace.sqlite` passed.

Outcome label: resolved for local feedback-loop mechanics; reduced for any
future model-judge or hosted online-scoring integration.

Implementation:

- Add a local `eval-trace-case-promote` command or subcommand that promotes a
  trace/span into a versioned eval case file under a tracked config path.
- Require source artifact refs, hashes, expected output or assertion contract,
  owner surface, risk level, tags, and removal/review conditions.
- Add deterministic scorer support first: schema, retrieval, groundedness by
  cited source spans, trace integrity, latency, and cost placeholders.
- Add human-label metadata structure without requiring a UI.
- Reserve `llm_judge` support for a later approved milestone that includes judge
  calibration, prompt/rubric hashes, model/version/temperature, examples, and
  precision/recall checks against human labels.

Required docs refresh:

- `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md` documents trace promotion and
  versioned cases.
- `docs/EVALUATION_COVERAGE_REGISTER.md` documents new eval case owner.
- `docs/TECH_DEBT_REGISTER.md` records any accepted limitation, especially if
  model-judge support remains intentionally deferred.
- `docs/SESSION_HANDOFF.md` records next milestone routing if active.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_eval_trace_case_promote.py tests/test_eval_trace_store.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit closeout:

- Commit command, tests, docs, case fixtures, contract updates, and handoff if
  active.

## Required Implementation Artifacts

- Contract doc: `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`
- Contract config: `config/eval_trace_inventory_contract_v1.json`
- Inventory module and CLI.
- Store module and generated SQLite schema.
- Export module and canonical/OpenInference JSON contracts.
- Phase/promotion gate integration.
- Trace-to-case promotion command and deterministic case format.
- Focused tests for positive and negative paths.

## Required Documentation And Handoff Updates

Update these files in the same milestone slice when their truth changes:

- `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture_contract.toml`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `README.md` only if the public operator entrypoint or stable repo contract
  changes
- `docs/TECH_DEBT_REGISTER.md` if any shortcut, deferred ratchet, judge
  limitation, or accepted non-first-class surface remains

Update `docs/CURRENT_ROUTING.md` whenever this packet is active or closeout
truth changes. Preserve West Reservoir context as historical lineage rather
than reopening the resolved West packet.

For every active implementation milestone, re-read `docs/CURRENT_ROUTING.md`,
the top of `docs/SESSION_HANDOFF.md`, and `docs/CURRENT_SYSTEM_STATE.md` before
editing. Update `docs/SESSION_HANDOFF.md` with the completed slice, exact
verification, residual risk, and next route. Update
`docs/CURRENT_SYSTEM_STATE.md` when command surfaces, generated output truth,
gate status, source-set state, review state, or readiness claims change.

## Required Verification Gates

Minimum docs-only verification for this plan or future contract-only edits:

```bash
git diff --check
```

Minimum source verification for implementation slices:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_eval_trace_contract.py tests/test_eval_trace_inventory.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

When CLI registration changes:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_cli_eval.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources --help
```

When phase or promotion gates change:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id <ratcheted-review-id>
```

Run broader focused suites if touched surfaces expand beyond eval-trace owner
modules.

## Acceptance Criteria

- The new contract names all first-class eval/trace objects, enum values, source
  references, scorer kinds, export fields, redaction policy, and gate semantics.
- `eval-trace-inventory` can run against a fixture source set and fixture review
  and emit schema-valid JSON without mutating existing artifacts.
- Negative inventory fixtures fail on missing required artifacts, stale
  source-set IDs, stale review IDs, missing trace hashes, and malformed result
  schemas.
- The generated SQLite store contains the six canonical tables and links each
  generic row to an originating artifact, hash, and source/review/source-set
  identity when available.
- Store rebuilds are idempotent on unchanged inputs.
- Canonical JSON export and OpenInference-compatible export preserve local
  provenance attributes.
- Phase-eval and promotion-suite integration are optional until the ratchet
  contract names a source set or review; ratcheted scopes fail closed on missing
  or stale eval-trace evidence.
- Existing domain-specific eval commands still own domain score truth.
- No hosted tool or external export is required for local closeout.
- Docs, architecture contract, output schemas, coverage register, current-state
  docs, and handoff agree with the verified implementation state.
- Each milestone lands as one local atomic commit after verification.

## Stop Conditions

- The first inventory cannot link existing result artifacts to source-set or
  review identity without broad schema changes. Stop and write a narrower
  artifact-link migration plan.
- Inventory requires mutating existing `source_library/` artifacts instead of
  reading them.
- Implementation would rerun downloader, large extraction, full review, or
  network workflows to make a docs/contract gate green.
- A deterministic lane is proposed to pass using only an uncalibrated model
  judge.
- Gate integration would block active West Reservoir Milestone 4 or another
  unrelated active packet before ratchet scope is explicit.
- New modules violate architecture boundaries or require broad exceptions.
- Tests are weakened, skipped, xfailed, or narrowed to pass.

## Local Commit Closeout Policy

- Keep each milestone as a separate atomic commit.
- Stage only the verified milestone slice.
- Leave pre-existing West Reservoir decision-support/final-QA worktree changes
  untouched unless the user explicitly routes this packet through them.
- Do not push unless the user asks.
- Before each commit, run the required verification, update docs/handoff, run
  `git diff --check`, inspect `git status -sb`, and stage only intended files.

## Plan Gap-Close Pass

This plan was checked against the research brief, current routing, current
system-state docs, architecture boundaries, output-schema surfaces, and existing
eval artifact owners. The closeout pass requires these gaps to stay closed
during implementation:

- public commands and tests remain listed in owner surfaces before they are
  implemented;
- optional/reporting mode comes before fail-closed phase or promotion ratchets;
- local store and canonical JSON export exist before any hosted or
  OpenInference-only integration;
- each milestone refreshes docs and handoff artifacts before commit;
- unrelated active West Reservoir worktree changes remain outside the staged
  eval-trace slice.

## Residual Risks And Next Routing

- This plan intentionally defers hosted observability integration. After local
  export is green, a separate milestone can add optional Phoenix/Braintrust/OTLP
  export with explicit redaction and no source-of-record transfer.
- This plan intentionally defers LLM judge scoring until deterministic
  first-class eval rows exist. A later judge milestone must include human-label
  calibration and precision/recall thresholds.
- This plan intentionally defers broad runtime instrumentation. After the store
  and export path are stable, new workflows should emit trace roots/spans as
  they are touched rather than forcing a repo-wide rewrite.
- If current eval artifacts lack enough identity metadata, route a narrow
  artifact-link compatibility milestone before DB/store work.
