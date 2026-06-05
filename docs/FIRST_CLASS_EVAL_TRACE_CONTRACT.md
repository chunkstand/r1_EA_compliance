# First-Class Eval Trace Contract

Date: 2026-05-28

Status: Milestone 0 contract, Milestone 1 read-only inventory CLI, Milestone 2
local SQLite store, Milestone 3 canonical/OpenInference export, Milestone 4
phase/promotion gate integration, and Milestone 5 trace-to-case promotion are
implemented locally.

Owner surfaces:

- Contract config: `config/eval_trace_inventory_contract_v1.json`
- Validation helper: `src/usfs_r1_ea_sources/eval_trace_contract.py`
- Inventory helper: `src/usfs_r1_ea_sources/eval_trace_inventory.py`
- Store helper: `src/usfs_r1_ea_sources/eval_trace_store.py`
- Export helper: `src/usfs_r1_ea_sources/eval_trace_export.py`
- Generated observability/eval context graph helper:
  `src/usfs_r1_ea_sources/eval_context_graph.py`
- Generated observability/eval context graph contract helper:
  `src/usfs_r1_ea_sources/eval_context_graph_contract.py`
- Generated observability/eval context graph event helper:
  `src/usfs_r1_ea_sources/eval_context_graph_events.py`
- Generated observability/eval context graph validation helper:
  `src/usfs_r1_ea_sources/eval_context_graph_validation.py`
- Gate helper: `src/usfs_r1_ea_sources/eval_trace_gate.py`
- Case promotion helper: `src/usfs_r1_ea_sources/eval_trace_case_promote.py`
- Default case file: `config/eval_trace_cases/system_eval_trace_cases_v1.json`
- Contract tests: `tests/test_eval_trace_contract.py`
- Inventory tests: `tests/test_eval_trace_inventory.py`
- Store tests: `tests/test_eval_trace_store.py`
- Export tests: `tests/test_eval_trace_export.py`
- Context graph tests: `tests/test_eval_context_graph.py`
- Case promotion tests: `tests/test_eval_trace_case_promote.py`
- Implementation plan:
  `docs/FIRST_CLASS_EVAL_TRACE_IMPLEMENTATION_MILESTONE_PLAN.md`

## Purpose

First-class eval and trace rows are the generic local substrate that ties
existing deterministic eval outputs, replay contexts, traces, source-set
manifests, review artifacts, and promotion gates into one queryable contract.

This contract does not replace existing domain-specific eval commands. It
defines the canonical shape that future inventory, store, export, and gate
milestones must use when reading those artifacts.

## Canonical Objects

The local generic model has six required objects:

- `system_eval_runs`
- `system_eval_cases`
- `system_eval_case_results`
- `system_eval_scores`
- `trace_runs`
- `trace_spans`

Milestone 0 validates that each object is declared with required fields in the
tracked contract config. Milestone 2 now materializes those objects in the
generated local SQLite store, `system_eval_trace.sqlite`. Future migrations must
preserve these object names unless the contract version changes.

## Enum Families

The contract validates four enum families:

- `eval_kind`
- `trace_kind`
- `span_kind`
- `score_kind`

Unsupported enum values fail contract validation. New values must be added to
`eval_trace_contract.py`, the tracked config, and the contract tests in the same
milestone slice so future inventory rows cannot silently drift into ad hoc
strings.

## Required Artifact Families

Milestone 0 requires the first inventory to reason over these artifact families:

- source-set manifest and source catalog surfaces
- replay context
- phase eval
- applicability retrieval and graph traces
- forest-plan component eval and component-coverage eval
- V1 EA eval
- real-package review coverage eval
- decision support
- final QA
- review packet index
- promotion suite

Each artifact family declares owner layer, artifact path patterns, and minimum
source-reference requirements. Future inventory/store work must check identity
and hashes from those declared surfaces rather than counting file presence.

## Required Link Checks

The first inventory/store milestones implement typed link checks for:

- source-set identity
- review identity
- source artifact hashes
- origin artifact refs
- replay context/catalog alignment
- applicability trace hashes
- phase-eval direct-eval presence
- export local provenance preservation
- explicit ratchet scope
- local source-of-record protection

Missing checks fail contract validation or inventory readiness because
linkability is the core first-class requirement. Milestone 1 now reports these
checks through `required_link_status`, plus typed `missing_cross_links`,
`stale_artifacts`, `source_set_mismatches`, `review_id_mismatches`, and
`trace_hash_mismatches` fields.

## Local Store Contract

`eval-trace-store-build` reads an inventory JSON file and rebuilds the generated
SQLite store under `source_library/evaluations/eval_trace/` or an explicit
operator path. The command owns only the six canonical store tables and does
not mutate catalog, extraction, retrieval, review, compliance, or promotion
artifacts.

Store rows preserve origin artifact refs, inventoried hashes, current hashes,
contract ID/version, source-set ID, review ID, catalog refs, replay-context
refs, source-record IDs when present, scorer-version metadata, thresholds, and
typed failure categories. Store validation fails if the input inventory failed,
an inventoried artifact was deleted or changed after inventory, a required link
is missing, a canonical table is empty, a row ID duplicates, or a child row is
orphaned.

The West Reservoir f70 seed build on 2026-05-29 passed with `18` rows in each
canonical table and `0` orphan rows, duplicate IDs, stale artifacts, source
artifact deletions, or missing required links.

## Trace-To-Case Promotion Contract

`eval-trace-case-promote` reads the local SQLite store and promotes one selected
trace or span into a versioned eval case file. The default tracked file is
`config/eval_trace_cases/system_eval_trace_cases_v1.json`, with schema version
`eval-trace-case-file-v1`.

`eval-trace-case-file-validate` validates that tracked file. By default it
requires at least one promoted case and fails closed on schema drift, missing
source artifact refs or hashes, absolute SQLite source paths, missing ownership
or lifecycle fields, missing deterministic scorer contracts, invalid human-label
status, or premature `llm_judge` enablement.

Promoted cases use schema version `eval-trace-promoted-case-v1`. Each case
must preserve the selected trace ID, optional span ID, eval run/case/result
IDs, source artifact refs, source artifact hashes, source-record IDs and
citation labels when present. The command refuses to write a case unless the
selected trace has source artifact refs and hashes and the caller supplies an
owner surface, allowed risk level, at least one tag, an assertion or expected
output contract, and review/removal lifecycle conditions. Duplicate case IDs
fail closed unless the operator passes `--replace`.

The promoted assertion contract is deterministic-first. It records contracts for
retrieval, groundedness by cited source spans, trace integrity, plus latency and
cost placeholders. Human label metadata is present without requiring a UI:
status, labeler, labels, note, and reviewed timestamp. The summary schema
version is `eval-trace-case-promote-summary-v1` and records `passed`,
`command_succeeded`, selected IDs, case count, replacement state, failure
reasons, and validation checks.

The current tracked case is
`west-reservoir-applicability-retrieval-trace-case-001`, promoted from
West Reservoir/f70 applicability retrieval trace `524a4a9ad3229869b77fc39d`
and span `24737cdb71be82ed8bc0a0d3`.

## Scorer Contract

Deterministic checks are the default. The contract requires deterministic score
kinds for schema, retrieval, groundedness, trace integrity, safety/security, and
deterministic-code checks.

`llm_judge` remains a reserved score kind. Any future LLM judge score must store
judge model, prompt hash, rubric hash, examples hash, temperature, and output
schema before it can satisfy a gate. Promoted cases explicitly record
`llm_judge.status="reserved_deferred"` and cannot use an LLM judge to satisfy a
gate until a later approved milestone adds calibration examples and
precision/recall checks against human labels.

## Export Contract

Canonical JSON export must exist before any OpenInference-shaped export can
pass. OpenInference compatibility is an interop target, not the durable source
of record. Milestone 3 implements both exports from the local SQLite store. The
default redaction policy is local, unredacted, and not approved for external
export.

Required local provenance, when available, includes:

- `source_set_id`
- `review_id`
- `source_record_id`
- artifact path
- artifact hash
- trace hash
- scorer/contract hash

`eval-trace-export` fails closed if required store tables are missing or if a
source-backed OpenInference span would lose source-set ID, review ID, source
ref, artifact path, artifact hashes, contract ID/version, local-source-of-record
truth, or redaction policy. The West Reservoir f70 seed export on 2026-05-29
passed with `18` traces, `36` OpenInference-shaped spans, `0` missing tables,
and `0` missing provenance fields.

## Generated Observability/Eval Context Graph

The first context-graph slice is implemented as a derived local graph over the
eval-trace SQLite store. `eval-context-graph-build` reads
`system_eval_runs`, `system_eval_cases`, `system_eval_case_results`,
`system_eval_scores`, `trace_runs`, and `trace_spans`, then writes a
deterministic graph JSON artifact with eval, trace, span, score, artifact,
source-set, review, and failure-class nodes. It preserves the local source of
record policy and does not create source knowledge-graph facts.

The second context-graph slice materializes event-like trace/log JSONL rows as
conditional `span_event` or `log_event` nodes and links them from the owning
span with `EMITTED` edges. Event properties keep compact provenance and payload
hashes rather than raw source text or prompt/body payloads.

The third context-graph slice accepts repeated `--event-log-path` inputs for
standalone local JSON/JSONL event logs. Each explicit file gets an
`event_source` node; rows become conditional `log_event` or `span_event` nodes
linked by `EMITTED` edges. Explicit event logs use the same payload-hash and
payload-key redaction policy as trace-derived event rows.

The fourth context-graph slice adds canonical CLI command-event capture. The
top-level CLI appends redacted start/finish rows to
`source_library/evaluations/observability_events/command_events.jsonl` by
default, and the graph builder includes that event log when it exists. Command
events carry command name, phase, invocation ID, safe context IDs/paths, argv
hashes, and exit/duration fields without storing raw argv or prompt/body text.

`eval-context-graph-eval` runs deterministic graph evals over that artifact:
required node/edge kinds, edge resolution, trace-to-result-to-score paths,
artifact provenance, event-emission integrity, event-source row materialization,
command-event graph joins, source-KG exclusion, and local export policy. This
makes graph-derived evals the next layer over the normalized store without
changing phase or promotion ratchets.

The contract and behavior are owned by
`docs/FIRST_CLASS_OBSERVABILITY_EVAL_CONTEXT_GRAPH.md` and
`config/context_graph_contract_v1.json`.

## Gate And Ratchet Contract

Milestone 0 forbids global fail-closed ratchets. The tracked config must not set
`global_fail_closed=true` or use wildcard source-set/review scopes. Milestone 4
keeps that rule and enables only one explicit review scope:
`west-reservoir-67436`.

`phase-eval` now reports `eval_trace_gate` on every run. It appends a
`first_class_eval_trace` phase only when matching eval-trace evidence exists or
when the selected review/source-set is ratcheted. Non-ratcheted scopes are
optional and non-blocking even when local eval-trace evidence is stale; ratcheted
scopes fail closed on missing inventory, missing store, stale inventory/store
hashes, missing canonical eval rows, missing trace rows, or source-set/review
identity mismatches.
The current `phase_eval_results.json` path is treated as a command
self-reference while `phase-eval` is running, so the gate does not deadlock on
the artifact it is about to rewrite.

`eval-trace-store-build` blocks failed origin artifacts, with one
self-refresh allowance: a parseable `phase_eval` artifact can still seed the
store when it contains a failed or reviewer-not-ready phase, or a blocker, so a
phase-eval run can rebuild the eval/trace substrate before rewriting its own
result file. This allowance does not bypass missing, stale-hash, missing-hash,
malformed, or unrecognized-schema checks, and any failed non-`phase_eval`
artifact still records `origin_artifact_failed` and blocks the store summary.

`promotion-suite` reads the `eval_trace_gate` object from phase-eval artifacts.
If a current-promotion phase-eval artifact reports a ratcheted eval-trace gate
failure, current promotion fails with `eval_trace_gate_failed`.

The first ratcheted seed is West Reservoir on
`source-set-f70ea11e04ae3d53`. The seed inventory, store, and export were
already green at Milestones 1-3; Milestone 4 makes the review ID fail-closed for
phase/promotion gate consumers without enabling any global or wildcard ratchet.

## Stop Conditions

Stop implementation and open a narrower compatibility packet if:

- the inventory cannot link existing result artifacts to source-set or review
  identity without broad schema changes;
- the inventory needs to mutate existing generated artifacts;
- a deterministic lane would need an uncalibrated LLM judge to pass;
- a phase or promotion gate would block unrelated active packets before a
  ratchet scope is explicit;
- a hosted platform becomes the source of record before local contract, store,
  and canonical export artifacts are complete.
