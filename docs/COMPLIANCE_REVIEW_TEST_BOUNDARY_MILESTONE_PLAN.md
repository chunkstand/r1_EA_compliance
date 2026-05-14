# Compliance Review Test Boundary Milestone Plan

Date: 2026-05-13

Status: Proposed 2026-05-13 (standalone hotspot follow-on; starts only after overlapping dirty
`tests/test_compliance_review.py` work is committed or explicitly parked)

Owner context: This is a fresh standalone milestone plan for the P2 architecture finding that
compliance verification is concentrated in one oversized test file instead of boundary-sized suites.
It does not reopen the production compliance module splits that already reduced
`src/usfs_r1_ea_sources/compliance_review.py`. It targets the lagging test surface that still owns
orchestration, eval, coverage, gold-eval, phase-eval integration, and synthetic source-library
builders in one file.

## Purpose

Resolve the broad-suite smell where `tests/test_compliance_review.py` has become the repo's hottest
single file and now obscures which compliance behavior actually failed.

The goal is not to reduce test volume or to chase line-count aesthetics. The goal is to align the
test suite with the already-split production owners so failures localize to the right surface:

- `run_compliance_review(...)` core orchestration and gate behavior
- `run_compliance_review_eval(...)`
- `run_compliance_coverage(...)`
- `run_compliance_gold_eval(...)`
- compliance-derived `phase-eval` integration
- shared synthetic source-library and artifact builders

This milestone is complete only after the new owner suites, shared fixture support, boundary gate,
docs and handoff updates, and one local atomic commit all land together. A verified but
uncommitted slice is only ready-to-close.

## Current Evidence

- `tests/test_compliance_review.py` is currently `4937` lines.
- The fresh architecture probe on 2026-05-13 reports `tests/test_compliance_review.py` as the top
  hotspot in the repo: `48` revisions, `4937` lines, hotspot score `236976`.
- `src/usfs_r1_ea_sources/compliance_review.py` is currently only `424` lines, which means the
  production compliance owner has already been split more aggressively than the tests that claim to
  verify it.
- The current test file imports production surfaces from multiple owners at once:
  `compliance_review`, `compliance_review_eval`, `compliance_coverage`,
  `compliance_gold_eval`, `evidence_graph`, `claim_extraction`, `retrieval`,
  `rule_claim_binding`, `ea_review`, and `forest_plan_components`.
- The current file owns one monolithic `ComplianceReviewTests` class plus a large helper family:
  `_build_source_library(...)`, forest-specific source-library builders, graph-phase writers,
  direct-eval result writers, rule-pack writers, package writers, and review runner helpers from
  roughly line `3303` through the end of the file.
- The current test categories naturally map to already-split production owners:
  - core compliance-review and rule-pack gates: roughly lines `35` through `1482`
  - compliance-review eval harness: roughly lines `1548` through `1823`
  - compliance coverage: roughly lines `1884` through `2056`
  - compliance-derived phase-eval behavior: lines including `2106`, `2268`, `2317`, `2520`,
    `2551`, `2608`, `2679`, `2715`, `2758`, `2803`, `2855`, `2894`, `2931`, `2971`, `3004`,
    and `3037`
  - compliance gold eval: roughly lines `2158` through `2494`
- The repo already has adjacent focused test files such as `tests/test_retrieval.py`,
  `tests/test_rule_claim_binding.py`, `tests/test_claim_extraction.py`,
  `tests/test_real_package_review_coverage_eval.py`, and `tests/test_gold_coverage_eval.py`, so
  the current compliance test hotspot is not justified by a repo-wide "one file per lane" pattern.
- Many active durable docs and plans still cite `tests/test_compliance_review.py` as the focused
  verification surface for gold, downstream direct-eval, Flathead/Beaverhead profile, and
  phase-eval work. If this file is split without doc routing updates, future sessions will use the
  wrong focused commands.
- The current worktree already has overlapping dirty changes in `tests/test_compliance_review.py`
  and new planning work that still references that file, including
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`.

## Goal

Resolve the scoped hotspot by turning the current catch-all compliance test file into a narrow core
suite and moving the other behaviors into dedicated owner suites backed by shared fixture support
and an executable boundary contract.

Completion means all of the following are true:

- `tests/test_compliance_review.py` becomes the narrow owner for core
  `run_compliance_review(...)` orchestration, rule-pack gate, generated review gate, and component
  gate behavior only.
- dedicated suites exist for compliance-review eval, compliance coverage, compliance gold eval, and
  compliance-derived phase-eval behavior.
- synthetic source-library and artifact builders move out of the owner suites into a shared test
  support module.
- the repo has a focused boundary test that fails if `tests/test_compliance_review.py` regains the
  mixed-owner imports or helper families that caused the hotspot.
- active docs and handoff routes point to the new focused test commands rather than the old
  catch-all file.

## Non-Goals

- Do not change production compliance behavior, schemas, output paths, or CLI names just to make
  the test split easier.
- Do not delete, loosen, or narrow negative-path coverage to make the new smaller suites pass.
- Do not convert focused unit-style fixture tests into live source-library or network workflows.
- Do not reopen the already-completed production compliance owner splits unless a narrowly scoped
  import or fixture update is required.
- Do not split historical closed milestone docs merely for cleanup. Update only current durable
  routing surfaces and active open plans that would otherwise point to the wrong test file.
- Do not solve the separate `phase-eval` owner move in the same milestone except for whatever
  import-path refresh is needed if that predecessor lands first.

## Scope

- `tests/test_compliance_review.py`
- new focused compliance test suites
- shared compliance test-support builders
- active docs and handoff updates required to route future focused verification to the new suites
- a focused hotspot-prevention gate for the compliance test surface

## Out Of Scope

- production code refactors beyond narrow import or fixture compatibility updates
- new eval themes or new gold package authoring beyond what is required to preserve existing
  coverage during the split
- new source-library captures, catalog builds, or package replays
- broad cleanup of other large test files such as `tests/test_promotion_suite.py` or
  `tests/test_forest_plan_resolver.py`

## Owner Surfaces

- core compliance orchestration test owner to preserve:
  `tests/test_compliance_review.py`
- new dedicated test owners:
  `tests/test_compliance_review_eval.py`,
  `tests/test_compliance_coverage.py`,
  `tests/test_compliance_gold_eval.py`,
  `tests/test_compliance_phase_eval.py`
- shared fixture and synthetic artifact builders:
  `tests/support/compliance_review_fixtures.py`
- boundary-contract gate:
  `tests/test_compliance_review_test_boundary.py`
- touched production surfaces for import alignment only:
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/compliance_coverage.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py` or
  `src/usfs_r1_ea_sources/phase_eval.py` depending on the landed phase-eval owner
- durable docs and routing artifacts:
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/HOTSPOT_REPORT_2026_05_04.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`,
  `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`,
  `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`,
  this milestone plan

## Placement Rules

- Keep `tests/test_compliance_review.py` as the narrow core owner so the familiar path survives,
  but remove all non-core owner behaviors from it.
- `tests/test_compliance_review.py` should own only:
  - base-rule-pack and generated-rule-pack gate behavior
  - authority integration and finding-graph behavior emitted directly by `run_compliance_review(...)`
  - component gate and adjudication gate behavior that belongs to review orchestration
  - rule-pack contract and package search-routing behavior that still directly proves the core
    review owner
- Move eval-harness cases to `tests/test_compliance_review_eval.py`.
- Move coverage-matrix and source-claim alignment cases to `tests/test_compliance_coverage.py`.
- Move gold-eval and adjudicated package cases to `tests/test_compliance_gold_eval.py`.
- Move compliance-derived `phase-eval` cases to `tests/test_compliance_phase_eval.py`. If the
  phase-eval owner move lands first, this new suite must import the canonical phase-eval owner
  rather than keeping old `evidence_graph.py` imports.
- Move source-library builders, package writers, rule-pack writers, graph-phase writers, and other
  synthetic artifact helpers into `tests/support/compliance_review_fixtures.py`.
- Do not keep `_build_*`, `_write_*`, `_run_generated_compliance_review(...)`, or similar fixture
  builders inside `tests/test_compliance_review.py` after closeout.
- If `tests/support/compliance_review_fixtures.py` would exceed `1200` lines, split it into
  sibling owners such as `tests/support/compliance_review_core_fixtures.py` and
  `tests/support/compliance_phase_eval_fixtures.py` before commit. Do not replace one hotspot with
  another unnamed hotspot.
- Do not create a single umbrella `tests/test_compliance_all.py` or similar replacement file. The
  point of this milestone is owner-aligned suites, not another catch-all path under a new name.

## Weak-Point Prevention Contract

- Weak point forecast: the file is split by line range only, but the new suites still mix
  unrelated owner modules so failures remain expensive to localize.
  Owner surface: `tests/test_compliance_review.py`,
  `tests/test_compliance_review_eval.py`,
  `tests/test_compliance_coverage.py`,
  `tests/test_compliance_gold_eval.py`,
  `tests/test_compliance_phase_eval.py`,
  `tests/test_compliance_review_test_boundary.py`
  Prevention gate: the boundary test must lock a suite-to-owner map and fail if the core suite
  imports eval, coverage, gold-eval, or phase-eval owners directly.
  Fail threshold: `tests/test_compliance_review.py` still imports
  `run_compliance_review_eval`, `run_compliance_coverage`, `run_compliance_gold_eval`,
  `run_phase_aligned_eval`, or the lower-level retrieval/claim/rule-link builder helpers that only
  exist to support non-core test families.
  Controlled violation: re-add a `run_compliance_gold_eval` or `run_phase_aligned_eval` import to
  `tests/test_compliance_review.py`; the boundary test must fail.
  Future-Codex misuse scenario: a later session adds one more "quick" gold or phase-eval case back
  into the core file because it is convenient; the boundary gate must fail before commit.

- Weak point forecast: helper duplication or local fixture writers remain in the owner suites, so
  the hotspot just moves around without clarifying ownership.
  Owner surface: `tests/support/compliance_review_fixtures.py`,
  `tests/test_compliance_review.py`,
  `tests/test_compliance_phase_eval.py`,
  `tests/test_compliance_review_test_boundary.py`
  Prevention gate: the boundary test must fail if `_build_*`, `_write_*`, or
  `_run_generated_compliance_review(...)` helpers remain in `tests/test_compliance_review.py`, and
  the shared fixture module must stay under the explicit line budget.
  Fail threshold: the core suite still defines large builder helpers, or the shared fixture owner
  exceeds `1200` lines without being split again.
  Controlled violation: leave `_write_graph_phase_outputs(...)` in the core suite or grow the
  support module past the budget; the boundary and line-budget check must fail.
  Future-Codex misuse scenario: a later session copies fixture writers into the gold or phase-eval
  suite instead of reusing support helpers; the boundary gate must fail.

- Weak point forecast: coverage is weakened during the split because negative-path or cross-lane
  cases are deleted instead of relocated.
  Owner surface: the five focused compliance suites plus `docs/SESSION_HANDOFF.md`
  Prevention gate: the boundary test must lock sentinel case ownership for at least these behaviors:
  - generated rule-pack reviewer-ready gate
  - compliance-review eval scoring
  - compliance coverage matrix/link scoring
  - compliance gold eval adjudicated profiles
  - compliance-derived phase-eval missing/stale artifact failures
  Fail threshold: any of those sentinel behaviors disappears or is no longer owned by a focused
  suite after the split.
  Controlled violation: delete the phase-eval missing-compliance-matrix assertion or the gold eval
  adjudicated-profile assertion while keeping the rest green; the boundary test must fail.
  Future-Codex misuse scenario: a later session reduces the hotspot by deleting hard tests and
  keeping only happy-path smoke cases; the sentinel ownership gate must fail.

- Weak point forecast: the split lands while the current dirty direct-eval or phase-eval planning
  lanes still overlap the same file, producing unstable imports and stale routing.
  Owner surface: `tests/test_compliance_review.py`,
  `docs/SESSION_HANDOFF.md`,
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`
  Prevention gate: Sequence 0 must rebaseline the landed or parked `phase-eval` owner and stop if
  overlapping dirty work in `tests/test_compliance_review.py` cannot be separated safely.
  Fail threshold: implementation starts while the same file still has unresolved overlapping dirty
  work from another milestone.
  Controlled violation: begin the split before the active dirty `tests/test_compliance_review.py`
  changes are committed or parked; the preflight must fail.
  Future-Codex misuse scenario: a later session assumes a planned owner move already landed and
  patches tests against the wrong import path; the rebaseline step prevents that.

- Weak point forecast: active docs and handoff commands keep pointing at the old catch-all suite, so
  future sessions keep running the wrong focused verification.
  Owner surface: `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/HOTSPOT_REPORT_2026_05_04.md`,
  `docs/SESSION_HANDOFF.md`,
  active open milestone plans that name `tests/test_compliance_review.py`
  Prevention gate: closeout must update active durable routing docs and active proposed plans that
  still treat `tests/test_compliance_review.py` as the focused owner for eval, gold-eval, or
  compliance-derived phase-eval behavior.
  Fail threshold: the code split lands but active docs still direct future work to the old
  catch-all test command.
  Controlled violation: move the gold eval tests into a new suite without updating the active gold
  or phase-eval plans; docs review must fail.
  Future-Codex misuse scenario: a later session follows a stale plan and reintroduces mixed-owner
  tests into the core suite; the docs gate keeps the routing current.

## Milestone Sequence

### Sequence 0 - Baseline Lock And Overlap Rebaseline

Outcome label: reduced

Purpose: start the hotspot work from current landed reality rather than from stale assumptions about
which `phase-eval` or direct-eval owner names are active.

Implementation tasks:

1. Run `git status -sb` and stop if overlapping dirty work in `tests/test_compliance_review.py`
   cannot be separated from this milestone.
2. Refresh the live baseline:
   - `wc -l tests/test_compliance_review.py`
   - `wc -l src/usfs_r1_ea_sources/compliance_review.py`
   - `wc -l src/usfs_r1_ea_sources/compliance_review_eval.py`
   - `wc -l src/usfs_r1_ea_sources/compliance_coverage.py`
   - `wc -l src/usfs_r1_ea_sources/compliance_gold_eval.py`
   - `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown`
3. Run a freshness check on the hotspot measurements and active doc-routing references before any
   suite motion begins. If line counts, owner names, or active plan references have changed during
   the current dirty work, rewrite the implementation packet to the fresh values before continuing.
4. Re-read the current `phase-eval` routing truth:
   - if the `phase-eval` owner still lives in `evidence_graph.py`, use that owner for the current
     split
   - if the owner has moved to `phase_eval.py`, route the new phase-eval suite there instead
5. Search the repo for active references to `tests/test_compliance_review.py` and record which of
   those are active durable docs or active proposed plans that must be updated at closeout.

Acceptance signals:

- the plan is grounded on current owner names and current hotspot measurements
- the split does not start on top of unresolved overlapping dirty work
- the docs-update scope is explicit before code changes begin

Required verification:

```bash
git status -sb
wc -l tests/test_compliance_review.py src/usfs_r1_ea_sources/compliance_review.py src/usfs_r1_ea_sources/compliance_review_eval.py src/usfs_r1_ea_sources/compliance_coverage.py src/usfs_r1_ea_sources/compliance_gold_eval.py
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown
rg -n "tests/test_compliance_review.py" docs README.md tests src
git diff --check
```

Stop conditions:

- overlapping dirty work in `tests/test_compliance_review.py` cannot be isolated safely
- the `phase-eval` owner is mid-move and cannot be refreshed to a single current truth
- the split would require updating historical closed docs as a prerequisite instead of only active
  routing surfaces

### Sequence 1 - Add The Compliance Test Boundary Gate

Outcome label: reduced

Purpose: create the owner and sentinel gate before broad test motion begins.

Implementation tasks:

1. Add `tests/test_compliance_review_test_boundary.py`.
2. Lock the intended owner mapping:
   - `tests/test_compliance_review.py` for core orchestration
   - `tests/test_compliance_review_eval.py` for eval harness
   - `tests/test_compliance_coverage.py` for coverage
   - `tests/test_compliance_gold_eval.py` for gold eval
   - `tests/test_compliance_phase_eval.py` for compliance-derived phase-eval
3. Lock forbidden imports in the core suite:
   `run_compliance_review_eval`, `run_compliance_coverage`, `run_compliance_gold_eval`,
   `run_phase_aligned_eval`, `build_retrieval_index`, `build_claim_extraction`,
   `build_rule_claim_links`, and `build_forest_plan_component_inventory`
4. Lock sentinel test ownership for at least these cases:
   - `test_generated_rule_pack_gate_makes_review_reviewer_ready`
   - `test_compliance_review_eval_scores_package_fixtures`
   - `test_compliance_coverage_scores_matrix_links_and_eval_cases`
   - `test_compliance_gold_eval_runs_adjudicated_profiles`
   - `test_phase_eval_can_include_compliance_review_phase`
5. Lock the milestone-local line budgets:
   - `tests/test_compliance_review.py` no larger than `1400` lines at closeout
   - no new focused compliance suite larger than `1200` lines
   - `tests/support/compliance_review_fixtures.py` no larger than `1200` lines unless split again

Acceptance signals:

- the owner boundary is executable before the big split starts
- a future session cannot silently re-mix core, eval, coverage, gold, and phase-eval cases
- the hotspot line budgets are explicit and testable

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review_test_boundary.py -q
git diff --check
```

Stop conditions:

- the owner map cannot be expressed without keeping mixed imports in the core suite
- the boundary gate would need hidden allowlists or manual review instead of executable assertions

### Sequence 2 - Extract Shared Fixture Builders

Outcome label: reduced

Purpose: remove the synthetic source-library and artifact builders from the core owner file before
splitting the behavior suites.

Implementation tasks:

1. Add `tests/support/compliance_review_fixtures.py`.
2. Move the helper families out of `tests/test_compliance_review.py`, including:
   - `_build_source_library(...)`
   - forest-specific source-library builders
   - extraction and chunk writers
   - catalog and graph-phase writers
   - direct-eval payload and rule-pack writers
   - package writers
   - generated review runner helpers
3. Keep tiny assertion helpers local only if they are owner-specific and remain short.
4. If phase-eval-specific builders dominate the support module after extraction, split them into a
   sibling support file before closeout rather than leaving one giant support module.

Acceptance signals:

- `tests/test_compliance_review.py` no longer owns large `_build_*` or `_write_*` helpers
- new focused suites can reuse the same support helpers without copy-paste
- the support module stays within the explicit budget or is deliberately split again

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review_test_boundary.py tests/test_compliance_review.py -q
wc -l tests/test_compliance_review.py tests/support/compliance_review_fixtures.py
git diff --check
```

Stop conditions:

- the support module becomes a new hotspot and cannot be split safely
- helper extraction would require production behavior changes rather than test support motion

### Sequence 3 - Split Focused Suites By Production Owner

Outcome label: reduced

Purpose: align the compliance test suite layout with the already-split production owners.

Implementation tasks:

1. Keep `tests/test_compliance_review.py` as the narrow core suite for:
   - base-rule-pack and generated-rule-pack gate behavior
   - authority-integration artifact assertions
   - rule-pack contract and package search behavior
   - forest-plan component gate and adjudication behavior that still belongs to review orchestration
2. Create `tests/test_compliance_review_eval.py` and move eval-harness cases there.
3. Create `tests/test_compliance_coverage.py` and move coverage-specific cases there.
4. Create `tests/test_compliance_gold_eval.py` and move gold-eval cases there.
5. Create `tests/test_compliance_phase_eval.py` and move compliance-derived `phase-eval` cases
   there.
6. Refresh imports for the landed `phase-eval` owner path if the predecessor owner move has landed
   before this milestone closes.
7. Update any focused helper or sentinel names in the boundary gate to match the landed suite
   names, but do not weaken the sentinel coverage set.

Acceptance signals:

- the new suites exist under the intended owner names
- the core suite no longer owns eval, coverage, gold, or phase-eval behavior
- the moved suites pass with equivalent or broader negative-path coverage
- the core suite meets the `1400`-line budget

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review_test_boundary.py tests/test_compliance_review.py tests/test_compliance_review_eval.py tests/test_compliance_coverage.py tests/test_compliance_gold_eval.py tests/test_compliance_phase_eval.py tests/test_cli.py tests/test_architecture_contract.py -q
wc -l tests/test_compliance_review.py tests/test_compliance_review_eval.py tests/test_compliance_coverage.py tests/test_compliance_gold_eval.py tests/test_compliance_phase_eval.py tests/support/compliance_review_fixtures.py
git diff --check
```

Stop conditions:

- negative-path coverage can be preserved only by keeping mixed-owner tests in the core suite
- the phase-eval owner path is still unstable and blocks the new phase-eval suite from settling on
  one import truth

### Sequence 4 - Cross-Lane Verification, Docs, And Atomic Closeout

Outcome label: resolved

Purpose: close the hotspot only after the suite split, docs routing, and local commit all agree.

Implementation tasks:

1. Run the focused new suites plus the affected cross-lane consumers that depend on the same helper
   or phase-eval paths.
2. Update the current durable routing docs and active open milestone plans that still name
   `tests/test_compliance_review.py` as the focused owner for eval, gold-eval, or compliance-derived
   phase-eval behavior.
3. Record the post-closeout line counts and verification stack in `docs/SESSION_HANDOFF.md`.
4. Stage only the verified hotspot slice and create one local atomic commit.

Acceptance signals:

- the focused new suites and affected cross-lane suites all pass
- active durable docs route future work to the correct focused suites
- `tests/test_compliance_review.py` is no longer the top-level mixed-owner catch-all
- the hotspot closes with one local atomic commit

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review_test_boundary.py tests/test_compliance_review.py tests/test_compliance_review_eval.py tests/test_compliance_coverage.py tests/test_compliance_gold_eval.py tests/test_compliance_phase_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_claim_extraction.py tests/test_applicability_eval.py tests/test_nepa_knowledge_graph_export.py tests/test_cli.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown
wc -l tests/test_compliance_review.py tests/test_compliance_review_eval.py tests/test_compliance_coverage.py tests/test_compliance_gold_eval.py tests/test_compliance_phase_eval.py tests/support/compliance_review_fixtures.py
git diff --check
```

Stop conditions:

- required verification fails
- active doc routing cannot be updated without reopening unrelated historical milestone docs
- the only way to pass is to weaken or delete sentinel coverage
- overlapping dirty work would need to be staged in the same commit

## Required Implementation Artifacts

- `tests/test_compliance_review_test_boundary.py`
- `tests/support/compliance_review_fixtures.py`
- updated `tests/test_compliance_review.py`
- `tests/test_compliance_review_eval.py`
- `tests/test_compliance_coverage.py`
- `tests/test_compliance_gold_eval.py`
- `tests/test_compliance_phase_eval.py`
- narrow import-alignment updates in affected test modules only if required by the settled
  `phase-eval` owner path

## Required Documentation And Handoff Updates

- `docs/CURRENT_SYSTEM_STATE.md`: refresh any current-state claims that point at the old
  catch-all test file or old focused commands
- `docs/HOTSPOT_REPORT_2026_05_04.md`: record that the test hotspot moved from one broad suite to
  owner-aligned suites
- `docs/SESSION_HANDOFF.md`: add the completed milestone summary, verification commands, line
  counts, commit hash, and residual risks
- `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`: if still active, update the
  compliance-phase verification file names to the new suite names
- `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`: if still active, update focused
  compliance-review-eval verification to the new suite name
- `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`: if still active, update focused compliance-gold
  verification to the new suite name

Historical closed plans may remain unchanged unless they are still used as active routing truth.

## Required Verification Gates

- the compliance test boundary gate passes
- the focused compliance suites pass under their new owner files
- affected cross-lane phase-eval consumers stay green
- `ruff`, `compileall`, and `git diff --check` pass
- the post-closeout line budgets pass
- the architecture probe still reports the hotspot movement accurately enough to show that
  `tests/test_compliance_review.py` is no longer the single broad-suite bottleneck

## Acceptance Criteria

- `tests/test_compliance_review.py` is no larger than `1400` lines at closeout.
- No new focused compliance suite is larger than `1200` lines.
- `tests/support/compliance_review_fixtures.py` is no larger than `1200` lines, or it is split
  again before closeout.
- `tests/test_compliance_review.py` no longer imports `run_compliance_review_eval`,
  `run_compliance_coverage`, `run_compliance_gold_eval`, or the compliance-derived `phase-eval`
  owner.
- `tests/test_compliance_review.py` no longer defines the large `_build_*`, `_write_*`, or
  `_run_generated_compliance_review(...)` helper family.
- Focused suites exist for compliance-review eval, compliance coverage, compliance gold eval, and
  compliance-derived `phase-eval`.
- Sentinel negative-path behaviors remain present and green in the intended owner suites.
- Active durable docs route future verification to the new focused suite names.
- The milestone closes with one local atomic commit that stages only the verified hotspot slice.

## Stop Conditions

- unresolved overlapping dirty work in `tests/test_compliance_review.py`
- unstable `phase-eval` owner routing blocks the new focused phase-eval suite from settling
- the split requires production behavior changes outside narrow import/fixture compatibility
- the only way to pass is to delete or weaken hard negative, missing-artifact, or stale-artifact
  coverage
- unrelated dirty work would need to be committed with this milestone

## Local Commit Closeout Policy

- Stage only the verified milestone slice.
- Leave unrelated dirty and untracked files alone, including the viewer work, root-level East
  Crazies draft exports, and unrelated phase-eval/direct-eval work unless the user explicitly
  broadens scope.
- Include the suite split, boundary gate, docs updates, and handoff update in the same commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until the local atomic commit exists.
- Stop before committing if verification fails or if overlapping dirty work cannot be separated
  safely.

## Residual Risks And Next Milestone Routing

- If `tests/test_compliance_phase_eval.py` becomes the next dominant hotspot because the separate
  phase-eval owner move lands more cross-lane cases there, route the next plan to compliance-phase
  test support and optional fixture-owner splitting rather than re-expanding the core suite.
- If the shared support module becomes the new hotspot even after the first split, route a follow-on
  to split support builders by core review versus phase-eval artifact families.
- If active plans beyond the ones named here still rely on the old test path for current routing,
  refresh those specific active plans at implementation time rather than rewriting historical closed
  docs wholesale.
