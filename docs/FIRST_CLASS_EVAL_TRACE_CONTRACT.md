# First-Class Eval Trace Contract

Date: 2026-05-28

Status: Milestone 0 contract and Milestone 1 read-only inventory CLI are
implemented locally. The local SQLite store, exports, phase/promotion ratchets,
and trace-to-case promotion are still future milestones.

Owner surfaces:

- Contract config: `config/eval_trace_inventory_contract_v1.json`
- Validation helper: `src/usfs_r1_ea_sources/eval_trace_contract.py`
- Inventory helper: `src/usfs_r1_ea_sources/eval_trace_inventory.py`
- Contract tests: `tests/test_eval_trace_contract.py`
- Inventory tests: `tests/test_eval_trace_inventory.py`
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
tracked contract config. Future migrations or generated SQLite stores must
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
of record. The default redaction policy is local, unredacted, and not approved
for external export.

Required local provenance, when available, includes:

- `source_set_id`
- `review_id`
- `source_record_id`
- artifact path
- artifact hash
- trace hash
- scorer/contract hash

## Ratchet Contract

Milestone 0 forbids global fail-closed ratchets. The tracked config must not set
`global_fail_closed=true` or use wildcard source-set/review scopes.

The first seed candidate is West Reservoir on
`source-set-f70ea11e04ae3d53`; Milestone 1 now inventories that seed
successfully. It is still not a fail-closed ratchet until a later milestone
explicitly enables the scope in the tracked contract.

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
