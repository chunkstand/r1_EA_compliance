# Phase Eval Orchestration Boundary Milestone Plan

Date: 2026-05-13

Status: Proposed 2026-05-16 (Sequence 0 reduced through local commit `a983bdc`; Sequence 1 is
reduced; Sequence 2 is now the next executable slice)

Sequence 0 closeout summary on 2026-05-16:

- The Sequence 0 closeout checkpoint is local commit `a983bdc`
  (`docs: close phase eval boundary sequence 0`).
- The predecessor direct-eval seam is no longer an open dirty overlap. The direct-eval lane in
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` is resolved on `2026-05-15`, and the
  later cross-forest/component-coverage follow-ons that consume that seam are also now resolved.
- The live baseline for this packet is refreshed:
  `src/usfs_r1_ea_sources/evidence_graph.py` is `3565` lines,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` is `1675` lines, and
  `tests/test_evidence_graph.py` is `1317` lines.
- The repo-local `run_phase_aligned_eval` caller baseline is now explicit:
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_compliance_gold_eval.py`,
  `tests/test_compliance_phase_eval.py`,
  `tests/test_ea_consistency_decision_support.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_nepa_knowledge_graph_export.py`,
  and the `phase-eval` CLI doubles in `tests/test_cli.py`.
- The fresh architecture probe on `2026-05-16` now reports
  `50` code files above `800` lines,
  `evidence_graph.py` at `32` revisions with hotspot score `114080`,
  and no import cycles.
- The overlap gate for this packet is currently green: `git status -sb` is clean, so no predecessor
  or unrelated dirty work needs to be parked before Sequence 1 begins.
- The next executable slice in this packet is Sequence 1: create `src/usfs_r1_ea_sources/phase_eval.py`
  as the canonical owner and add the first boundary gate.

Sequence 1 closeout summary on 2026-05-16:

- Sequence 1 is reduced in the local closeout commit for this slice.
- `src/usfs_r1_ea_sources/phase_eval.py` now exists as the canonical owner for
  `PhaseEvalResult` and `run_phase_aligned_eval(...)`, and the stable `phase-eval` CLI now imports
  that owner from `src/usfs_r1_ea_sources/cli_eval.py`.
- `docs/architecture_contract.toml` now defines a dedicated `phase_eval` layer for
  `phase_eval`, `phase_eval_direct_eval`, and `replay_context`, and phase-eval result artifacts now
  belong to that owner boundary instead of the generic eval layer.
- `src/usfs_r1_ea_sources/evidence_graph.py` no longer defines the phase-eval entrypoints or
  imports decision-support, final-QA, review-packet, replay-context, or direct-eval owner modules.
  The graph owner is now `1317` lines; the new canonical owner is `2277` lines.
- `tests/test_phase_eval_boundary_contract.py` now fail-closes canonical owner presence, stale
  entrypoint definitions in `evidence_graph.py`, stale phase-eval owner imports inside
  `evidence_graph.py`, and CLI import drift.
- The post-move architecture probe still reports no import cycles, but the hotspot picture has
  changed: `51` code files now exceed `800` lines, `evidence_graph.py` is no longer the top
  hotspot, and `phase_eval.py` is the new over-budget owner that Sequence 2 must split.
- The next executable slice in this packet is Sequence 2: finish the owner cleanup by removing the
  remaining non-graph helper dependency on `evidence_graph.py` and splitting the oversized
  `phase_eval.py` owner below the line-budget cap.

Owner context: This is a fresh standalone milestone plan for the P1 architecture finding that the
`evidence_graph` boundary is collapsed. It does not reopen the now-resolved
`docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` implementation slice. Sequence 0 of this
plan exists to refresh the landed helper names, file-size baseline, caller roster, and routing
truth before the owner extraction starts. Completion means the `phase-eval` command still works,
but its orchestration no longer lives in `src/usfs_r1_ea_sources/evidence_graph.py`.

## Purpose

Resolve the architectural collapse where `src/usfs_r1_ea_sources/evidence_graph.py` owns both:

- document evidence graph build and validation; and
- `phase-eval` readiness orchestration across replay context, direct-eval coverage, applicability,
  compliance, knowledge-graph, decision-support, review-packet, and final-QA artifacts.

The goal is not a broad rewrite. The goal is to give `phase-eval` an explicit owner boundary so the
graph builder can stay a deep module for graph concerns only, while readiness orchestration can
evolve without continuing to enlarge the graph layer.

This milestone is complete only after the new owner surface, architecture contract, focused tests,
docs, handoff updates, and one local atomic commit all land together. A verified but uncommitted
slice is only ready-to-close.

## Current Evidence

- `docs/architecture_contract.toml` currently describes the `evidence_graph` layer as
  "Document evidence graph build and validation", but it still owns
  `evidence_graph`, `phase_eval_direct_eval`, and `replay_context`.
- `docs/ARCHITECTURE.md` separates NEPA 3D graph ownership from document evidence graph ownership,
  but it still presents `evidence_graph.py` as part of the evidence-and-claims lane while the live
  `phase-eval` command is implemented inside that file.
- `src/usfs_r1_ea_sources/evidence_graph.py` is currently `3565` lines and defines both
  `build_evidence_graph(...)` and `run_phase_aligned_eval(...)`.
- `src/usfs_r1_ea_sources/evidence_graph.py` imports decision-support, final-QA, review-packet,
  direct-eval, replay-context, and rule-claim surfaces that are not graph-build concerns.
- The direct-eval predecessor lane is now committed, and its helper owner remains live at
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` (`1675` lines). Sequence 0 started from a
  clean worktree, so this packet no longer overlaps unresolved dirty predecessor edits.
- `tests/test_evidence_graph.py` is currently `1317` lines and still mixes graph-build tests with
  `phase-eval` orchestration coverage.
- Several other test modules still import `run_phase_aligned_eval` from `evidence_graph.py`,
  including `tests/test_claim_extraction.py`, `tests/test_applicability_eval.py`,
  `tests/test_compliance_gold_eval.py`, `tests/test_compliance_phase_eval.py`,
  `tests/test_ea_consistency_decision_support.py`, and `tests/test_nepa_knowledge_graph_export.py`.
- The fresh architecture probe on 2026-05-16 reported:
  - `evidence_graph.py`: `3565` lines, `32` revisions, hotspot score `114080`
  - `50` code files above `800` lines
  - no import cycles, which means the main remaining issue here is boundary ownership rather than
    cycle cleanup

## Goal

Resolve the scoped evidence-graph boundary problem by moving `phase-eval` orchestration into a
dedicated owner module and tightening the architecture contract so the graph-build layer no longer
owns multi-lane readiness assembly.

Completion means all of the following are true:

- `phase-eval` has one canonical code owner separate from `evidence_graph.py`.
- `evidence_graph.py` owns graph build, graph validation, graph persistence, and graph metrics only.
- `phase-eval` orchestration, replay-context routing, optional readiness-phase assembly, and
  direct-eval contract consumption are owned outside the graph-build module.
- repo-local callers and tests no longer import `run_phase_aligned_eval` from `evidence_graph.py`.
- the architecture contract and architecture docs describe the new boundary accurately.
- the boundary has an executable prevention gate so a later Codex session cannot quietly move phase
  logic back into `evidence_graph.py`.

## Non-Goals

- Do not rewrite retrieval, applicability, compliance, knowledge-graph, decision-support, or final
  QA behavior just to make the split easier.
- Do not weaken `phase-eval`, direct-eval, promotion-suite, or cross-lane tests to compensate for
  moving code.
- Do not change public CLI command names, key options, or output artifact locations unless a
  migration is explicitly required and documented.
- Do not reopen the resolved compliance-review test-boundary lane in the same commit unless a
  narrowly scoped import or owner-surface adjustment is required for this split.
- Do not reopen the current direct-eval lane by inventing a second threshold contract or a second
  `phase-eval` manifest.
- Do not use dynamic imports or hidden fallback logic to preserve the old boundary in disguise.

## Scope

- canonical owner for `phase-eval`
- architecture-contract layer ownership for `phase-eval`, `phase_eval_direct_eval`, and
  `replay_context`
- `cli_eval.py` wiring for the stable `phase-eval` CLI command
- repo-local callers that import `run_phase_aligned_eval`
- separation of graph-build tests from phase-eval tests
- architecture docs, schema docs, current-state notes, and handoff updates required to describe the
  new owner boundary

## Out Of Scope

- direct-eval threshold redesign
- new eval cases except focused negative or boundary cases needed to prove the split
- new source-library runs or network workflows
- large review-package replays as a substitute for focused boundary verification
- project-SOW, downloader, catalog, or forest-profile routing unrelated to the `phase-eval` owner
  split

## Owner Surfaces

- canonical phase-eval owner:
  `src/usfs_r1_ea_sources/phase_eval.py`
- direct-eval helper and replay-context owner after the split:
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `src/usfs_r1_ea_sources/replay_context.py`
- graph-build owner after the split:
  `src/usfs_r1_ea_sources/evidence_graph.py`
- CLI owner:
  `src/usfs_r1_ea_sources/cli_eval.py`
- boundary and regression tests:
  `tests/test_phase_eval.py`,
  `tests/test_phase_eval_boundary_contract.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_cli.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_nepa_knowledge_graph_export.py`,
  `tests/test_compliance_phase_eval.py`,
  `tests/test_architecture_contract.py`
- durable docs and routing artifacts:
  `docs/ARCHITECTURE.md`,
  `docs/architecture_contract.toml`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this milestone plan

## Placement Rules

- `src/usfs_r1_ea_sources/evidence_graph.py` may own only graph-build concerns after closeout:
  graph record assembly, graph validation, graph metrics, graph SQLite writes, and graph-specific
  JSON or JSONL helpers that are used only by `build_evidence_graph(...)`.
- `src/usfs_r1_ea_sources/phase_eval.py` must own `run_phase_aligned_eval(...)`,
  `PhaseEvalResult`, source-set and review-scoped phase assembly, and the final
  `phase_eval_results.json` shaping logic.
- `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` remains the owner of direct-eval contract
  parsing and normalized summary resolution. Do not duplicate threshold, summary-resolution, or
  contract-reading logic in `phase_eval.py`.
- `src/usfs_r1_ea_sources/replay_context.py` must be owned by the phase-eval boundary, not by the
  evidence-graph boundary. After closeout, `evidence_graph.py` must not import it.
- Repo-local Python callers should import `run_phase_aligned_eval` from `phase_eval.py` after the
  split. Internal import compatibility from `evidence_graph.py` is not a required public contract.
- Keep the public CLI stable: the `phase-eval` command name, key flags, and output path stay the
  same.
- Move `phase-eval`-specific tests out of `tests/test_evidence_graph.py`. That file should remain
  the graph-build and graph-validation test owner.
- Tighten the architecture contract rather than adding an exception. The intended closeout state is
  no `evidence_graph -> decision_support|applicability|compliance|knowledge_graph|phase_eval`
  dependency at the source-module level.
- If `phase_eval.py` would exceed `1800` lines at closeout, split optional phase helpers into a
  small sibling owner such as `phase_eval_optional_phases.py` before committing. Do not replace one
  hotspot with another unnamed hotspot.

## Weak-Point Prevention Contract

- Weak point forecast: `run_phase_aligned_eval(...)` moves, but `evidence_graph.py` still quietly
  owns replay-context or readiness assembly helpers.
  Owner surface: `src/usfs_r1_ea_sources/evidence_graph.py`,
  `tests/test_phase_eval_boundary_contract.py`,
  `docs/architecture_contract.toml`
  Prevention gate: boundary tests and the architecture contract must require that
  `evidence_graph.py` no longer defines `run_phase_aligned_eval`, `PhaseEvalResult`, or the
  optional phase-assembly helper family.
  Fail threshold: `evidence_graph.py` still defines or imports phase-eval orchestration concerns
  after closeout.
  Controlled violation: reintroduce `run_phase_aligned_eval(...)` or a
  `decision_support` import into `evidence_graph.py`; the boundary test must fail.
  Future-Codex misuse scenario: a later session adds a new readiness phase directly into
  `evidence_graph.py`; the boundary gate must fail before commit.

- Weak point forecast: the new phase-eval owner duplicates direct-eval contract logic instead of
  reusing the existing helper seam.
  Owner surface: `src/usfs_r1_ea_sources/phase_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`
  Prevention gate: direct-eval contract loading must remain centralized in
  `phase_eval_direct_eval.py`, with `phase_eval.py` consuming normalized results rather than
  re-parsing contracts or re-stating thresholds.
  Fail threshold: the split creates a second threshold table, a second result-resolution path, or a
  code-only fallback that bypasses `phase_eval_direct_eval.py`.
  Controlled violation: remove the helper usage and re-inline a threshold dictionary in
  `phase_eval.py`; the contract tests must fail.
  Future-Codex misuse scenario: a later session updates the new phase-eval owner only and leaves
  the governed direct-eval contract stale; the contract tests must fail.

- Weak point forecast: the move lowers coverage by deleting or shrinking phase-eval tests instead
  of relocating them.
  Owner surface: `tests/test_phase_eval.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_compliance_phase_eval.py`
  Prevention gate: every source-set and review-scoped phase-eval behavior currently covered in
  `tests/test_evidence_graph.py` must have an equivalent or broader assertion in the new
  `tests/test_phase_eval.py`, and existing cross-lane consumers must stay green.
  Fail threshold: `phase-eval` behavior is removed from tests, or negative-path coverage becomes
  narrower after the move.
  Controlled violation: delete the replay-context mismatch or missing-direct-eval assertions while
  keeping happy-path tests green; the focused phase-eval suite must fail.
  Future-Codex misuse scenario: a later session "simplifies" the move by deleting the moved tests;
  the focused suite and parity review must fail.

- Weak point forecast: the split resolves `evidence_graph.py` but creates a second oversized
  orchestration hotspot with no explicit budget.
  Owner surface: `src/usfs_r1_ea_sources/phase_eval.py`,
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`,
  the post-closeout `wc -l` baseline recorded in the handoff
  Prevention gate: Sequence 0 records the baseline, and closeout must prove
  `evidence_graph.py` dropped by at least `700` lines from that baseline and is no larger than
  `2800` lines; `phase_eval.py` must be no larger than `1800` lines.
  Fail threshold: the code move lands without materially shrinking the graph owner, or the new
  owner immediately exceeds the line budget.
  Controlled violation: move only the public entrypoint and leave the helper tree in
  `evidence_graph.py`; the budget gate must fail.
  Future-Codex misuse scenario: a later session keeps adding optional phases to `phase_eval.py`
  without another split; the size budget forces a new owner milestone before that lands.

- Weak point forecast: CLI or schema behavior drifts because internal imports change.
  Owner surface: `src/usfs_r1_ea_sources/cli_eval.py`,
  `docs/OUTPUT_SCHEMAS.md`,
  `tests/test_cli.py`
  Prevention gate: the `phase-eval` CLI command and output schema remain stable and are revalidated
  with focused CLI and schema-facing tests.
  Fail threshold: command name, key flags, or output schema change without an explicit migration and
  docs update.
  Controlled violation: change the CLI import without updating the parser or output expectations;
  the CLI tests must fail.
  Future-Codex misuse scenario: a later session treats the internal module rename as permission to
  rename the CLI surface; the CLI tests and docs checks must fail.

- Weak point forecast: architecture docs stay stale, so future sessions keep treating
  `evidence_graph.py` as the phase-eval owner.
  Owner surface: `docs/ARCHITECTURE.md`,
  `docs/architecture_contract.toml`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
  Prevention gate: closeout requires the architecture map, contract, current-state notes, and
  handoff to all point to the new canonical owner.
  Fail threshold: code lands while durable docs still name `evidence_graph.py` as the
  `phase-eval` owner.
  Controlled violation: move the code without updating the architecture map or handoff; the docs
  verification pass must fail.
  Future-Codex misuse scenario: a later session reads old docs and adds more readiness logic to the
  graph module; the closeout docs make that routing obviously wrong.

## Milestone Sequence

### Sequence 0 - Predecessor Refresh And Baseline Lock

Outcome label: reduced

Purpose: start this lane only after the current direct-eval `phase-eval` work is actually routed and
the live file-size baseline is refreshed.

Implementation tasks:

1. Confirm the predecessor lane is closed or explicitly parked:
   - `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`
   - `docs/SESSION_HANDOFF.md`
   - `docs/architecture_contract.toml`
   - any landed `phase_eval_direct_eval.py` or replay-context owner names
2. Record the live baseline:
   - `wc -l src/usfs_r1_ea_sources/evidence_graph.py`
   - `wc -l src/usfs_r1_ea_sources/phase_eval_direct_eval.py`
   - `wc -l tests/test_evidence_graph.py`
   - `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown`
3. Search repo-local callers of `run_phase_aligned_eval` and lock the import-migration list before
   moving code.
4. If overlapping dirty work from the predecessor still touches `evidence_graph.py`,
   `architecture_contract.toml`, `phase_eval_direct_eval.py`, or `SESSION_HANDOFF.md`, stop and
   either finish that lane first or park it outside this milestone.

Acceptance signals:

- the new plan is routed against the actual landed direct-eval helper names
- the file-size and caller baseline is fresh
- the split does not begin on top of unresolved overlapping dirty work

Required verification:

```bash
git status -sb
wc -l src/usfs_r1_ea_sources/evidence_graph.py src/usfs_r1_ea_sources/phase_eval_direct_eval.py tests/test_evidence_graph.py
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown
rg -n "run_phase_aligned_eval" src tests
git diff --check
```

Stop conditions:

- the predecessor direct-eval lane is not actually closed or safely parkable
- the baseline overlaps unrelated dirty work that cannot be separated
- the live helper names differ materially from this plan and require a routing refresh first

### Sequence 1 - Create The Canonical Phase-Eval Owner And Gate

Outcome label: reduced

Purpose: establish the explicit owner boundary and the first executable guard before the large move.

Implementation tasks:

1. Add `src/usfs_r1_ea_sources/phase_eval.py` as the canonical owner for:
   - `PhaseEvalResult`
   - `run_phase_aligned_eval(...)`
   - top-level source-set and review-scoped orchestration entrypoints
2. Update `src/usfs_r1_ea_sources/cli_eval.py` so the stable `phase-eval` CLI command imports the
   canonical owner from `phase_eval.py`.
3. Update `docs/architecture_contract.toml` to create a dedicated `phase_eval` layer that owns:
   - `phase_eval`
   - `phase_eval_direct_eval`
   - `replay_context`
4. Tighten the `evidence_graph` layer summary so it describes graph build and validation only.
5. Add `tests/test_phase_eval_boundary_contract.py` to lock:
   - canonical owner module presence
   - no `run_phase_aligned_eval(...)` definition in `evidence_graph.py`
   - no `PhaseEvalResult` definition in `evidence_graph.py`
   - no direct import of `decision_support`, `compliance`, `applicability`, `knowledge_graph`,
     `replay_context`, or `phase_eval_direct_eval` from `evidence_graph.py` after the move

Acceptance signals:

- `phase_eval.py` exists as the canonical entrypoint owner
- the CLI surface is unchanged
- the architecture contract names the new layer explicitly
- the first boundary gate exists before the full helper migration

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_boundary_contract.py tests/test_cli.py tests/test_architecture_contract.py -q
git diff --check
```

Stop conditions:

- the new owner can be created only by changing the CLI surface
- the architecture contract requires a hidden exception instead of the intended boundary
- the boundary gate cannot be expressed without dynamic-import fallback logic

### Sequence 2 - Move Replay And Phase Assembly Out Of The Graph Owner

Outcome label: reduced

Purpose: finish the owner extraction that Sequence 1 started by removing the remaining non-graph
helper dependency on `evidence_graph.py` and shrinking the new `phase_eval` owner under budget.

Implementation tasks:

1. Move the remaining non-graph helper family currently imported from `evidence_graph.py` into the
   `phase_eval` owner boundary or a small neutral helper module:
   - `_read_json`
   - `_read_json_if_exists`
   - `_read_jsonl`
   - `_write_json`
   - `_dict`
   - `_dict_list`
   - `_extraction_summary_is_complete`
   - `_int_from_summary`
   - `_safe_int`
   - `_current_queue_item_count`
   - `_selector_value`
   - `_source_set_id_from_catalog`
   - `_utc_now`
2. Leave `src/usfs_r1_ea_sources/evidence_graph.py` with graph-build concerns only:
   - `build_evidence_graph(...)`
   - graph record assembly
   - graph validation
   - graph metrics
   - graph SQLite writes
   - graph-specific helper functions used only by graph build
3. Preserve reuse of `phase_eval_direct_eval.py` and `replay_context.py` from the new owner instead
   of duplicating direct-eval or replay-context logic.
4. Split `src/usfs_r1_ea_sources/phase_eval.py` if needed so the canonical owner is no larger than
   `1800` lines at closeout, for example by moving optional phase summaries into a small sibling
   owner such as `phase_eval_optional_phases.py`.
5. Extend the boundary gate so future sessions cannot reintroduce a `phase_eval -> evidence_graph`
   helper dependency after this cleanup lands.

Acceptance signals:

- `phase_eval.py` no longer imports helper functions from `evidence_graph.py`
- `evidence_graph.py` is graph-only and contains only graph-build helpers
- the canonical phase-eval owner still consumes the direct-eval helper seam instead of duplicating
  it
- `evidence_graph.py` remains at least `700` lines smaller than the Sequence 0 baseline and no
  larger than `2800` lines
- the canonical phase-eval owner is no larger than `1800` lines after any sibling split

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_boundary_contract.py tests/test_architecture_contract.py tests/test_cli.py -q
rg -n "from \\.evidence_graph import" src/usfs_r1_ea_sources/phase_eval.py
wc -l src/usfs_r1_ea_sources/evidence_graph.py src/usfs_r1_ea_sources/phase_eval.py
git diff --check
```

Stop conditions:

- the helper cleanup requires a broad rewrite of optional phase owners instead of a bounded split
- the graph owner cannot stay graph-only without changing external command behavior
- the new phase-eval owner exceeds the line budget and cannot be split safely inside the milestone

### Sequence 3 - Re-scope Tests To The New Owner Boundary

Outcome label: reduced

Purpose: make the test layout match the new code boundary so future changes do not re-couple the
graph owner and phase-eval owner.

Implementation tasks:

1. Create `tests/test_phase_eval.py` and move `phase-eval`-specific coverage there.
2. Trim `tests/test_evidence_graph.py` so it owns only graph-build and graph-validation behaviors.
3. Keep repo-local callers on the new canonical owner import and remove any remaining hidden
   `phase-eval` ownership from test modules that still treat `tests/test_evidence_graph.py` as the
   primary home for readiness orchestration coverage.
4. Keep cross-lane assertions where they belong, but do not leave phase-eval ownership hidden
   inside `tests/test_evidence_graph.py`.
5. Prove no coverage was weakened during the move by preserving or strengthening:
   - missing-direct-eval failure coverage
   - replay-context mismatch coverage
   - optional phase inclusion coverage
   - source-set and review-scoped output-path coverage

Acceptance signals:

- `tests/test_evidence_graph.py` no longer imports or exercises `run_phase_aligned_eval`
- `tests/test_phase_eval.py` owns the focused phase-eval boundary coverage
- repo-local callers no longer treat `evidence_graph.py` as the phase-eval owner
- moved negative-path tests remain present and green

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval.py tests/test_evidence_graph.py tests/test_claim_extraction.py tests/test_applicability_eval.py tests/test_nepa_knowledge_graph_export.py tests/test_compliance_phase_eval.py tests/test_cli.py tests/test_architecture_contract.py -q
git diff --check
```

Stop conditions:

- coverage can be preserved only by deleting or narrowing existing negative-path assertions
- a cross-lane consumer still needs the old owner path for reasons not documented in the contract

### Sequence 4 - Docs, Handoff, And Atomic Closeout

Outcome label: resolved

Purpose: close the architectural issue only after the code, docs, tests, and commit all describe the
same owner boundary.

Implementation tasks:

1. Update durable docs to describe the new owner split:
   - `docs/ARCHITECTURE.md`
   - `docs/architecture_contract.toml`
   - `docs/OUTPUT_SCHEMAS.md`
   - `docs/CURRENT_SYSTEM_STATE.md`
   - `docs/SESSION_HANDOFF.md`
   - this milestone plan with closeout notes if the repo’s practice is to close plans in place
2. Record the post-closeout size baseline for:
   - `src/usfs_r1_ea_sources/evidence_graph.py`
   - `src/usfs_r1_ea_sources/phase_eval.py`
   - `tests/test_evidence_graph.py`
   - `tests/test_phase_eval.py`
3. Record the local commit hash and the exact verification commands in the handoff.
4. Stage only the verified boundary slice and make one local atomic commit.

Acceptance signals:

- all durable docs name `phase_eval.py` as the canonical owner for `phase-eval`
- the boundary tests, focused behavior tests, and architecture contract all pass
- the handoff includes the moved owner surfaces, the verification stack, the post-closeout line
  counts, the commit hash, and any residual risks
- the milestone closes with a local atomic commit; without that commit the status is not complete

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_boundary_contract.py tests/test_phase_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_claim_extraction.py tests/test_applicability_eval.py tests/test_nepa_knowledge_graph_export.py tests/test_compliance_phase_eval.py tests/test_cli.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown
wc -l src/usfs_r1_ea_sources/evidence_graph.py src/usfs_r1_ea_sources/phase_eval.py tests/test_evidence_graph.py tests/test_phase_eval.py
git diff --check
```

Stop conditions:

- required verification fails
- the docs cannot be aligned without reopening the direct-eval predecessor lane
- overlapping dirty work cannot be separated safely for one atomic commit
- the only way to go green is to weaken tests, loosen the architecture contract, or keep hidden
  fallback imports

## Required Implementation Artifacts

- `src/usfs_r1_ea_sources/phase_eval.py`
- updated `src/usfs_r1_ea_sources/evidence_graph.py`
- updated `src/usfs_r1_ea_sources/cli_eval.py`
- updated `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` only if needed for owner clarity; do
  not broaden its scope
- updated `src/usfs_r1_ea_sources/replay_context.py` ownership and imports
- `tests/test_phase_eval.py`
- `tests/test_phase_eval_boundary_contract.py`
- updated focused caller tests and architecture contract tests

## Required Documentation And Handoff Updates

- `docs/ARCHITECTURE.md`: separate graph build from phase-eval orchestration in the container map
- `docs/architecture_contract.toml`: create the dedicated `phase_eval` layer and tighten
  `evidence_graph` ownership
- `docs/OUTPUT_SCHEMAS.md`: keep the `phase-eval` schema current under the new owner description
- `docs/CURRENT_SYSTEM_STATE.md`: record the owner-boundary change only if the current-state notes
  mention `phase-eval` ownership or architecture readiness
- `docs/SESSION_HANDOFF.md`: add the completed milestone summary, verification commands, line-count
  baseline, commit hash, residual risks, and next routing

## Required Verification Gates

- architecture contract passes with the new layer ownership
- dedicated phase-eval boundary test passes
- graph-build tests and phase-eval tests both pass from their new owner files
- CLI tests pass with the stable `phase-eval` command surface
- repo-local cross-lane consumers stay green after import migration
- `ruff`, `compileall`, and `git diff --check` all pass
- the post-closeout line-count budget passes

## Acceptance Criteria

- `src/usfs_r1_ea_sources/evidence_graph.py` no longer defines `run_phase_aligned_eval(...)` or
  `PhaseEvalResult`.
- `src/usfs_r1_ea_sources/evidence_graph.py` no longer imports replay-context, direct-eval,
  decision-support, compliance, applicability, or knowledge-graph phase-assembly concerns.
- `src/usfs_r1_ea_sources/phase_eval.py` is the canonical repo-local owner for the `phase-eval`
  command behavior.
- `docs/architecture_contract.toml` contains a dedicated `phase_eval` owner boundary and a tighter
  graph-build boundary.
- `tests/test_evidence_graph.py` is graph-only, and `tests/test_phase_eval.py` owns the
  phase-eval behavior coverage.
- Repo-local callers no longer import `run_phase_aligned_eval` from `evidence_graph.py`.
- `evidence_graph.py` is at least `700` lines smaller than the Sequence 0 baseline and no larger
  than `2800` lines.
- `phase_eval.py` is no larger than `1800` lines at closeout.
- No tests, gates, or docs were weakened to make the split pass.
- The milestone closes with one local atomic commit that stages only the verified slice.

## Stop Conditions

- the predecessor direct-eval lane is still unresolved and overlaps the same files
- the split requires changing public CLI behavior
- the only way to preserve compatibility is through hidden dynamic imports or contract exceptions
- the move cannot meet the line-budget or owner-boundary gates without a second split that should be
  its own milestone
- unrelated dirty files would need to be staged to complete the milestone

## Local Commit Closeout Policy

- Stage only the verified milestone slice.
- Leave unrelated dirty and untracked files alone, including the root-level East Crazies draft
  exports and unrelated viewer work unless the user explicitly broadens scope.
- Include implementation, tests, docs, and handoff updates in the same commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until the local atomic commit exists.
- Stop before committing if verification fails or overlapping dirty work cannot be separated safely.

## Residual Risks And Next Milestone Routing

- If `phase_eval.py` exceeds the line budget even after the extraction, write a follow-on milestone
  to split optional phase families by owner rather than accepting a renamed hotspot.
- If `tests/test_compliance_phase_eval.py` becomes the dominant active hotspot after the owner move,
  route the next architecture plan to a focused phase-eval test-boundary packet rather than
  reopening the graph owner.
- If the direct-eval predecessor lane lands a different helper or replay-context owner shape than
  this plan assumes, refresh this plan in Sequence 0 rather than forcing the old naming onto the
  repo.
