# First-Class Eval Trace Contract

Date: 2026-05-28

Status: Milestone 0 contract, Milestone 1 read-only inventory CLI, Milestone 2
local SQLite store, Milestone 3 canonical/OpenInference export, and Milestone 4
phase/promotion gate integration are implemented locally. Trace-to-case
promotion is still a future milestone.

Owner surfaces:

- Contract config: `config/eval_trace_inventory_contract_v1.json`
- Validation helper: `src/usfs_r1_ea_sources/eval_trace_contract.py`
- Inventory helper: `src/usfs_r1_ea_sources/eval_trace_inventory.py`
- Store helper: `src/usfs_r1_ea_sources/eval_trace_store.py`
- Export helper: `src/usfs_r1_ea_sources/eval_trace_export.py`
- Gate helper: `src/usfs_r1_ea_sources/eval_trace_gate.py`
- Contract tests: `tests/test_eval_trace_contract.py`
- Inventory tests: `tests/test_eval_trace_inventory.py`
- Store tests: `tests/test_eval_trace_store.py`
- Export tests: `tests/test_eval_trace_export.py`
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

## Scorer Contract

Deterministic checks are the default. The contract requires deterministic score
kinds for schema, retrieval, groundedness, trace integrity, safety/security, and
deterministic-code checks.

`llm_judge` remains a reserved score kind. Any future LLM judge score must store
judge model, prompt hash, rubric hash, examples hash, temperature, and output
schema before it can satisfy a gate.

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

`eval-trace-store-build` blocks failed origin artifacts, with one narrow
bootstrap allowance: a `phase_eval` artifact can still seed the store when its
only failed phase is `first_class_eval_trace` and the only reasons are
eval-trace inventory/store stale or missing-store self-reference reasons. Any
other failed phase-eval artifact still records `origin_artifact_failed` and
blocks the store summary.

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
