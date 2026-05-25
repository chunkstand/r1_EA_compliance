# Promotion Suite Slot-Driven Contract Milestone Plan

Date: 2026-05-24

Status: Milestone 2 reduced locally

Owner context: This is a fresh standalone follow-on packet for the promotion-suite contract. It
does not replace the active Lolo example packet in `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
and it does not reopen the already-closed full-canonical source-set rebind. Milestone 0 now
records that the 2026-05-24 rebaseline found a clean checkout, no equivalent slot-driven selector
or canary implementation already landed under another name, and the governed roster still exposes
exactly one `current_promotion_reviewer_ready` slot at implementation start. This packet is
complete only after the contract refactor, focused tests, durable docs, handoff updates, and one
local atomic closeout commit land together. A verified but uncommitted slice is only
ready-to-close.

## Purpose

Remove the brittle coupling where `promotion-suite` treats one named review package as the
load-bearing proof for current promotion readiness across a large artifact surface.

Today the repo already has the right abstraction for breadth: the real-package review coverage
manifest owns coverage classes and slot thresholds across East Crazies, West Reservoir, and South
Plateau. But current promotion readiness in `promotion-suite` is still wired through one ECID
review case, and the aggregate tests still lock packet-specific counts and filenames into the suite
contract. This packet exists to make current promotion slot-driven and layered:

- suite-wide readiness stays owned by suite-level aggregate artifacts
- review-facing current promotion is selected from governed coverage slots rather than a hard-coded
  review ID
- fixed packet canaries remain available, but they no longer define the whole promotion gate
- packet-specific semantic counts stay in packet-local validators and tests rather than the
  aggregate promotion contract

This packet resolves structural brittleness in the promotion contract. It does not claim that the
repo suddenly has multiple reviewer-ready current-promotion packages if the live roster still has
only one such slot.

## Current Evidence

- `config/promotion_suite_v1.json` currently has exactly one
  `required_for_current_promotion` review case:
  `v1-cg-ecid-compliance-review`.
- `src/usfs_r1_ea_sources/promotion_suite.py` computes `current_promotion_ready` by requiring the
  rule pack plus all required current review results plus all required current suite results to
  pass, which makes the single current review case the whole current-promotion gate.
- `config/v1_real_package_review_coverage_v1.json` already owns the broader slot abstraction with
  the required coverage classes `current_promotion_reviewer_ready`,
  `alternate_package_typed_blocked`, and `expansion_reviewer_ready`.
- `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py` already produces a governed summary
  of covered slots, covered coverage classes, distinct forests, package-style counts, and threshold
  failures.
- `tests/test_promotion_suite.py` currently asserts ECID-specific aggregate paths, packet-local
  counts, and `manifest["review_cases"][0]`, which locks the aggregate contract to one review
  packet instead of a slot-driven selector.
- The short route in `docs/CURRENT_ROUTING.md` already records that the full-canonical source-set
  contract is green on `source-set-4fb59e9eb43045cb` and the remaining live blocker is the ECID
  review-local current-promotion lane, not the source-set lane itself.

## Goal

Make `promotion-suite` stable against packet identity churn by separating:

1. suite-level readiness truth
2. slot-driven current-promotion readiness
3. packet-specific canary or regression truth

Completion means all of the following are true:

- `promotion-suite` resolves eligible current-promotion candidates from governed coverage-slot
  results rather than a hard-coded review ID
- the aggregate contract can express artifact families and quorum rules for current-promotion
  readiness
- fixed packet canaries such as ECID are reported separately from the slot-driven
  `current_promotion_ready` gate
- packet-specific semantic counts remain enforced, but only in packet-local validators, fixtures,
  and tests
- the aggregate contract and focused tests fail if a later session reintroduces hard-coded
  single-review coupling

## Non-Goals

- Do not reopen full-canonical source-set rebinding; that contract is already green.
- Do not mutate workbook rows, catalog rows, extraction, retrieval, or other upstream corpus
  artifacts just to make the promotion contract easier to refactor.
- Do not claim that a second reviewer-ready current-promotion slot exists unless live governed
  coverage actually proves one.
- Do not weaken packet-local validation such as final QA, decision-support, review-packet, or
  compliance matrix checks just to move them out of the aggregate suite.
- Do not stage ignored `source_library/` artifacts unless repository policy changes or the user
  explicitly expands scope.
- Do not fold Lolo, queue, or unrelated forest-plan example work into this packet.

## Scope

- promotion-suite manifest schema and validation
- promotion-suite runtime routing and summary semantics
- current-promotion slot selection from governed review coverage results
- aggregate artifact-family and quorum semantics
- separation of current-promotion versus reference-canary results
- promotion-suite tests, fixtures, and focused docs that describe the contract
- architecture-contract and boundary-test updates if a new module or owner surface is introduced

## Out Of Scope

- ECID review-local artifact refresh itself
- adding new real-package slots to the coverage manifest unless Milestone 0 finds the repo has
  already done so
- expanding the live reviewer-ready roster beyond what governed coverage already proves
- review-packet content redesign, new final QA semantics, or decision-support content redesign
- source-library network/download workflows

## Owner Surfaces

- aggregate promotion contract owner:
  `config/promotion_suite_v1.json`,
  `src/usfs_r1_ea_sources/promotion_suite.py`,
  `src/usfs_r1_ea_sources/promotion_suite_validation.py`,
  `src/usfs_r1_ea_sources/promotion_suite_report.py`,
  `src/usfs_r1_ea_sources/promotion_suite_summary.py`
- current-promotion slot resolution owner:
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `config/v1_real_package_review_coverage_v1.json`,
  and any new focused promotion-suite slot-resolution helper added in this packet
- packet-local validator owners that must retain semantic-count coverage:
  `config/ea_consistency_decision_support_v1.json`,
  `config/east_crazies_final_qa_certification_v1.json`,
  `tests/test_ea_consistency_decision_support.py`,
  `tests/test_final_qa_certification.py`,
  `tests/test_phase_eval.py`
- aggregate contract tests and fixtures:
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_full_canonical.py`,
  `tests/support/promotion_suite_fixtures.py`,
  `tests/test_cli_eval.py`
- architecture and docs owners:
  `docs/architecture_contract.toml`,
  `tests/test_architecture_contract.py`,
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- Keep `src/usfs_r1_ea_sources/promotion_suite.py` as orchestration, not as the long-term home for
  slot selection, selector parsing, quorum policy, and packet-canary branching.
- If new current-promotion selector or family-resolution logic is needed, place it in a focused
  sibling owner such as `promotion_suite_current.py` or `promotion_suite_slots.py` and add the
  matching architecture-contract coverage in the same milestone.
- Keep slot roster truth in `config/v1_real_package_review_coverage_v1.json`; do not duplicate a
  second hand-maintained list of eligible current-promotion review IDs inside the promotion-suite
  manifest.
- Keep fixed review-ID canaries explicit and typed. They may remain in the manifest, but they must
  not define `current_promotion_ready`.
- Move packet-specific semantic counts out of the aggregate promotion manifest only when equivalent
  or stronger packet-local coverage is present in focused validators or tests in the same slice.
- Preserve the existing separation among `current_promotion_ready`,
  `full_canonical_corpus_ready`, and `expansion_ready`. This packet is about how current promotion
  is proven, not about collapsing those lanes back together.

## Weak-Point Prevention Contract

- Weak point forecast: a future session reintroduces a fixed ECID-style review ID as the aggregate
  current-promotion truth because it is easier than implementing slot selection.
  Owner surface: `config/promotion_suite_v1.json`,
  `src/usfs_r1_ea_sources/promotion_suite_validation.py`,
  `tests/test_promotion_suite.py`
  Prevention gate: the manifest schema and focused tests must require current-promotion selection
  to come from governed coverage classes or slot selectors rather than from a fixed required review
  case.
  Fail threshold: aggregate `current_promotion_ready` still depends on one named review ID or on
  `review_cases[0]`.
  Controlled violation: construct a fixture where the first review case changes order or is absent;
  aggregate current-promotion resolution must still work or fail with a typed contract error.
  Future-Codex misuse scenario: a later agent swaps in a new proving packet by renaming the first
  review case; schema and tests must fail.

- Weak point forecast: artifact-family quorum becomes too weak and allows mixed artifacts from
  different reviews to satisfy one current-promotion lane.
  Owner surface: the new slot/family resolver plus `tests/test_promotion_suite_full_canonical.py`
  and `tests/test_promotion_suite.py`
  Prevention gate: family semantics must prove that all artifacts for one passing family come from
  the same eligible slot and match the active source-set contract unless the manifest explicitly
  declares a suite-level artifact.
  Fail threshold: a synthetic fixture can pass `current_promotion_ready` by combining artifacts
  from different review IDs or mismatched source sets.
  Controlled violation: build a fixture with one slot providing final QA and another slot providing
  compliance review; the family gate must fail.
  Future-Codex misuse scenario: a later agent paperclips together partial outputs from multiple
  reviews to keep current promotion green; the family gate must fail closed.

- Weak point forecast: removing packet-specific counts from the aggregate suite silently weakens the
  review-packet, decision-support, or final-QA boundary.
  Owner surface: packet-local validator configs and tests plus promotion-suite tests
  Prevention gate: every count or packet-specific invariant removed from aggregate promotion-suite
  tests must remain enforced in a packet-local validator or focused packet-local test in the same
  slice.
  Fail threshold: aggregate tests are simplified but no equivalent packet-local assertion exists.
  Controlled violation: drop the packet-local count assertion from the focused validator test; the
  milestone must be considered incomplete.
  Future-Codex misuse scenario: a later session deletes the ECID-specific count checks from the
  aggregate suite and never rehomes them; packet-local tests must catch the loss.

- Weak point forecast: ECID canary coverage disappears entirely once it stops being the load-bearing
  current-promotion proof.
  Owner surface: `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite.py`,
  `docs/POST_V1_PROMOTION_SUITE.md`
  Prevention gate: the manifest and report must preserve a typed reference-canary lane for fixed
  packet regression checks.
  Fail threshold: ECID-specific regression truth disappears or is only recoverable from prose.
  Controlled violation: remove the canary section from the manifest; focused tests must fail.
  Future-Codex misuse scenario: a later agent treats slot-driven readiness as sufficient and drops
  the fixed proving packet; the canary gate must fail.

- Weak point forecast: the refactor creates a new hotspot by burying slot selection, family
  semantics, and report rendering inside the existing orchestration module.
  Owner surface: `src/usfs_r1_ea_sources/promotion_suite.py`,
  any new sibling helper,
  `docs/architecture_contract.toml`,
  `tests/test_architecture_contract.py`
  Prevention gate: new owner boundaries must be declared in `docs/architecture_contract.toml`, and
  focused contract tests must fail on undeclared imports or boundary drift.
  Fail threshold: the refactor introduces a new owner without updating the architecture contract, or
  `promotion_suite.py` becomes the only owner of selector, slot, and canary logic.
  Controlled violation: place slot resolution in the orchestration module without the boundary
  declaration; architecture-contract verification must fail.
  Future-Codex misuse scenario: a later session appends more selector branches to the orchestration
  file instead of using the focused owner; the contract test must catch it.

## Milestone Sequence

### Milestone 0 - Freshness And Overlap Rebaseline

Outcome label: reduced

Purpose: refresh this packet against the live repo state before implementation begins, especially
because the current checkout already contains uncommitted promotion-suite and source-set refresh
edits.

Implementation:

1. Confirm the active short route, handoff, and committed current promotion truth.
2. Inspect whether the dirty checkout has already landed equivalent selector, slot, or canary work
   under a different name.
3. Re-check the live governed slot roster from
   `config/v1_real_package_review_coverage_v1.json` and its current result semantics.
4. Record whether the live roster still has only one
   `current_promotion_reviewer_ready` slot or whether later work added more.
5. Rewrite the remaining milestones before code changes if equivalent work already exists or if the
   roster changed.

Acceptance criteria:

- The plan records the exact live slot roster and whether the current-promotion quorum can only be
  `1` at implementation start.
- No later milestone duplicates equivalent in-flight or already-committed selector/canary work.
- The remaining milestones are refreshed before implementation continues if the live roster or
  dirty overlap changed.

Verification:

```bash
git status -sb
rg -n "current_promotion_reviewer_ready|required_for_current_promotion|reference|canary" \
  config/promotion_suite_v1.json config/v1_real_package_review_coverage_v1.json \
  src/usfs_r1_ea_sources tests
git diff --check
```

### Milestone 1 - Gate-First Contract Shape

Outcome label: reduced

Purpose: introduce the contract shape and failing tests before broad runtime refactoring so the
anti-brittleness rules are executable.

Implementation:

1. Upgrade the manifest/result schema to a version that can express:
   - suite-level aggregate results
   - slot-driven current-promotion selection from review-coverage classes
   - artifact families with same-slot and source-set constraints
   - quorum rules
   - fixed reference-canary review cases
2. Add focused validation errors for:
   - current-promotion selectors that are hard-coded by review ID
   - family definitions that can mix artifacts across slots
   - aggregate packet-specific counts that belong in packet-local validators
3. Add failing or baseline tests proving the intended boundary before runtime behavior changes.

Acceptance criteria:

- The manifest can represent slot-driven current-promotion truth without a fixed proving review ID.
- The schema rejects invalid selector or family shapes that would recreate single-review coupling or
  mixed-slot false passes.
- Focused tests exist for selector resolution, canary separation, and packet-local-count migration.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_full_canonical.py \
  tests/test_cli_eval.py \
  tests/test_architecture_contract.py -q

jq empty config/promotion_suite_v1.json config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

### Milestone 2 - Slot-Driven Runtime Separation

Outcome label: reduced

Purpose: move the runtime from fixed review-case aggregation to governed slot-driven current
promotion, while keeping full-canonical and expansion semantics intact.

Implementation:

1. Resolve eligible current-promotion slots from the governed review-coverage results rather than
   from a fixed review case list.
2. Evaluate current-promotion artifact families against those eligible slots with same-slot and
   source-set matching.
3. Report reference-canary results separately from slot-driven current-promotion results.
4. Keep full-canonical and expansion lanes independent from the new current-promotion resolution.
5. If a new helper owner is added, update `docs/architecture_contract.toml` and focused contract
   tests in the same slice.

Acceptance criteria:

- `current_promotion_ready` is computed from governed slot results plus current-promotion family
  results, not from one fixed review case.
- The result summary exposes enough detail to explain which slots were eligible, which families
  passed, and whether the canary lane passed separately.
- Full-canonical and expansion semantics remain unchanged except where documentation explicitly
  records the current-promotion refactor.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_full_canonical.py \
  tests/test_cli_eval.py \
  tests/test_architecture_contract.py -q

jq empty config/promotion_suite_v1.json config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

### Milestone 3 - Manifest And Packet-Local Coverage Migration

Outcome label: reduced

Purpose: remove packet-specific invariants from the aggregate suite only after they are preserved in
packet-local validators and focused tests.

Implementation:

1. Rewrite `config/promotion_suite_v1.json` so aggregate current-promotion checks use slot-driven
   family selectors and canary sections rather than ECID-specific packet counts.
2. Move ECID-specific count and filename assertions to packet-local owners where they belong.
3. Update promotion-suite fixtures and tests so aggregate failures remain typed and honest.
4. Add at least one controlled negative case proving:
   - mixed-slot family artifacts fail
   - canary failure does not silently disappear
   - a packet-local invariant still fails in its focused owner after aggregate migration

Acceptance criteria:

- Aggregate promotion-suite tests no longer rely on `manifest["review_cases"][0]` or ECID-specific
  semantic counts to define current promotion readiness.
- Every moved ECID-specific invariant is still enforced by a packet-local validator or focused
  packet-local test.
- Failure categories stay explicit and truthful for stale source-set, mixed-slot, and canary
  regressions.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_full_canonical.py \
  tests/test_ea_consistency_decision_support.py \
  tests/test_final_qa_certification.py \
  tests/test_phase_eval.py \
  tests/test_cli_eval.py -q

jq empty config/promotion_suite_v1.json config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

### Milestone 4 - Live Replay, Docs, And Closeout

Outcome label: resolved

Purpose: prove the new contract against the live local artifacts, then land the durable docs and
handoff updates together.

Implementation:

1. Replay the governed review-coverage aggregate and the refactored promotion suite against the
   local `source_library` state.
2. Update operator docs and schema docs to explain the new layered contract:
   suite-level truth, slot-driven current promotion, and reference canary.
3. Record the live result, residual risk, and next routing in the handoff and short route.
4. Stage only the verified packet-local slice and close it with one local atomic commit.

Acceptance criteria:

- Live replay proves the refactored promotion suite runs against the current local artifact set.
- The docs no longer describe ECID as the sole structural owner of current promotion readiness.
- The handoff records the closeout commit, exact verification commands, residual risk, and next
  routed packet.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_full_canonical.py \
  tests/test_ea_consistency_decision_support.py \
  tests/test_final_qa_certification.py \
  tests/test_phase_eval.py \
  tests/test_cli_eval.py \
  tests/test_architecture_contract.py -q

jq empty config/promotion_suite_v1.json config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Required Implementation Artifacts

- upgraded promotion-suite manifest and result schema with slot-driven current-promotion contract
- focused current-promotion slot/family resolver owner if the logic would otherwise collapse back
  into `promotion_suite.py`
- updated aggregate report fields for eligible current-promotion slots, family results, and
  reference-canary results
- focused negative fixtures for mixed-slot and hard-coded-review regression cases
- updated packet-local validator tests that retain any ECID-specific invariants removed from the
  aggregate suite
- architecture-contract updates if a new owner surface is introduced

## Required Documentation And Handoff Updates

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/architecture_contract.toml` and the focused contract tests if a new code owner is added
- this plan

## Required Verification Gates

- focused promotion-suite contract tests
- focused packet-local validator tests for any moved invariants
- `tests/test_cli_eval.py`
- `tests/test_architecture_contract.py` when new modules or boundaries are added
- `ruff check src tests`
- `python -m compileall src`
- live local replay of `real-package-review-coverage-eval` and `promotion-suite`
- `git diff --check`

## Acceptance Criteria

- Structural current-promotion truth is slot-driven rather than one-review-driven.
- Fixed canaries remain explicit, but they do not define `current_promotion_ready`.
- Packet-specific semantic counts remain tested at packet-local owners with equal or stronger
  coverage than before.
- The aggregate suite can expand to additional governed current-promotion-ready slots through
  manifest and coverage updates rather than another runtime rewrite.
- The closeout leaves no docs claiming that ECID is still the sole structural promotion proof when
  the contract has already been generalized.

## Stop Conditions

- Stop if Milestone 0 finds that equivalent slot-driven current-promotion work already landed under
  different names; rewrite the packet to the true remaining delta instead of duplicating it.
- Stop if implementing the slot-driven contract would require weakening packet-local validators,
  deleting packet-local counts without replacement, or broadening this packet into ECID artifact
  regeneration.
- Stop if the live repo still only has one reviewer-ready current-promotion slot and a proposed
  change tries to claim broader empirical coverage without a new governed slot.
- Stop if live `source_library` replay failures turn out to be review-local artifact staleness
  rather than contract behavior; route that remaining replay debt separately instead of hiding it
  inside this refactor.

## Local Commit Closeout Policy

- Stage only the verified promotion-suite contract slice for each milestone.
- Leave unrelated dirty `config/`, `src/`, `tests/`, viewer, and docs edits alone.
- Include implementation, tests, docs, and handoff updates for the completed milestone in the same
  local commit.
- Record the closeout commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until the verification passes and the local atomic commit
  exists.

## Residual Risks And Next Milestone Routing

- If this packet resolves the structural brittleness but the live governed roster still has only
  one `current_promotion_reviewer_ready` slot, the remaining risk is empirical breadth, not
  contract shape. That follow-on should route through the governed example-depth and real-package
  expansion owners rather than reopening this contract packet.
- The active queue and example-work packets remain unchanged by this plan. Do not treat this packet
  as permission to fold in Lolo, Flathead, NPC, or other queued review work.
- If a later session needs a second or third reviewer-ready current-promotion slot, route that work
  from the current example-depth owner in
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` or through a new standalone
  current-promotion slot-expansion packet rather than rebuilding the promotion contract again.
