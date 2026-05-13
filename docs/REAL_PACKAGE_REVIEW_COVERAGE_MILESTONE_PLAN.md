# Real-Package Review Coverage Milestone Plan

Date: 2026-05-13

Status: Implemented 2026-05-13

Owner context: This is a fresh standalone stacked follow-on milestone plan. It starts only after
`docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md` closes green and is committed. That earlier plan
may already add some of the same contract files or routing artifacts named here. Milestone 0 of
this plan must therefore re-evaluate the live repo state before code changes begin, adopt any
equivalent artifacts already landed by the earlier milestone, and narrow the remaining work instead
of duplicating it under new names.

## Closeout

Milestone 0 adopted the equivalent real-review surfaces that the gold-coverage milestone had
already shipped, then narrowed the remaining work to the still-open ownership gap:

- `config/v1_real_package_review_coverage_v1.json` now owns the three governed review slots,
  coverage classes, thresholds, and package-authority declarations for East Crazies current
  promotion, West Reservoir, and South Plateau.
- `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py` plus
  `real-package-review-coverage-eval` now provide the fail-closed aggregate coverage gate for those
  slots.
- `v1-ea-eval` now resolves tracked per-review contracts from that manifest when `--review-id` is
  supplied, rather than silently defaulting to an ECID-only contract.
- `gold-coverage-eval` now reuses the manifest-owned real-package aggregate instead of carrying a
  second embedded review roster.
- Live bounded verification on 2026-05-13 reran `v1-ea-eval` for East Crazies, West Reservoir, and
  South Plateau, reran `real-package-review-coverage-eval`, and replayed `gold-coverage-eval`
  against the current gold result artifacts plus the fresh real-package aggregate. The closeout
  stayed green with `3/3` covered slots, `2` forests, `3` package styles, `2`
  reviewer-ready slots, `1` typed-blocked slot, and `0` package-authority misses.

## Purpose

Close the remaining real-package review coverage gap so this system no longer depends on one East
Crazies contract as the only shipped V1 real-review coverage surface.

Today the repo has one shipped per-review V1 contract, but it already has three meaningful live
review lanes with different readiness semantics:

- East Crazies current promotion is the promoted reviewer-ready lane.
- West Reservoir is the reviewer-ready Flathead live-package proving lane.
- South Plateau is the typed blocked expansion lane whose broader review is useful coverage even
  while forest-plan component readiness remains open.

This milestone exists to convert those three package styles into a governed, executable,
multi-package real-review coverage surface with tracked package authority, per-review contracts,
explicit ready-versus-blocked expectations, and a single aggregate gate that fails closed if
coverage collapses back to one package or one review style.

This milestone is not complete until the rebaseline, contract inventory, per-review review
contracts, aggregate coverage gate, register/docs/handoff updates, verification, and one local
atomic commit per milestone all land together. A verified but uncommitted slice is only
ready-to-close.

## Dependency And Milestone 0 Refresh Rule

- Start only after the gold-coverage milestone closes green and is locally committed.
- If the gold-coverage milestone lands equivalent artifacts under different names, Milestone 0 must
  adopt those artifacts and rewrite the remaining milestones before implementation continues.
- If West Reservoir, South Plateau, or East Crazies review IDs, package authorities, or review
  locations drift before implementation starts, Milestone 0 must refresh them in tracked config
  before any contract or CLI work begins.
- If South Plateau is no longer blocked when this plan starts, Milestone 0 must upgrade it from a
  typed blocked slot to a reviewer-ready slot and remove no-longer-relevant blocked-state logic
  from later milestones.
- If South Plateau remains blocked, later milestones must keep that blocked state explicit and
  governed; they must not omit the slot, silently downgrade it to an informational lane, or force a
  fake green result.

## Historical Baseline Evidence

- `config/v1_ecid_real_ea_eval.json` is still the only shipped real-package V1 review contract.
- `src/usfs_r1_ea_sources/v1_ea_eval.py` still defaults `DEFAULT_V1_EA_EVAL_PATH` to
  `config/v1_ecid_real_ea_eval.json`, so the shipped single-review default remains East
  Crazies-centric.
- `docs/OUTPUT_SCHEMAS.md` still documents that same ECID-only default contract for
  `v1-ea-eval`.
- `config/v1_west_reservoir_real_ea_eval.json` and
  `config/v1_south_plateau_real_ea_eval.json` do not exist at the current baseline.
- `config/replay_contexts/` currently contains `west-reservoir-67436.json` and
  `v1-cg-ecid-source-delta-review.json`, but there is no tracked replay-context file for the South
  Plateau review and no tracked current-promotion replay-context file for the East Crazies review.
- `docs/CURRENT_SYSTEM_STATE.md` records `west-reservoir-67436` as reviewer-ready with review-bound
  `phase-eval` passing `17/17`.
- The same current-state doc records South Plateau review
  `region1-expansion-south-plateau-landscape-treatment` as intentionally blocked on
  `forest_plan_reviewer_not_ready` while broader applicability/compliance review artifacts remain
  useful and current promotion stays green.
- `docs/EVALUATION_COVERAGE_REGISTER.md` currently has no explicit row for `v1-ea-eval` or an
  aggregate real-package review coverage owner, so this lane is not yet governed alongside the
  upstream/downstream direct-eval surfaces.

## Scope

- tracked real-package review coverage for East Crazies current promotion, West Reservoir, and
  South Plateau
- tracked package-authority ownership for those review lanes
- per-review V1 real-review contracts for the three named lanes
- review-slot readiness semantics that distinguish reviewer-ready from typed blocked coverage
- an aggregate real-package coverage manifest and executable gate
- coverage-register, schema-doc, README, current-state, and handoff routing for this lane

## Out Of Scope

- resolving the South Plateau `31`-item forest-plan component adjudication queue itself
- broadening beyond the minimum three named package lanes unless Milestone 0 proves the repo has
  already moved past that boundary
- downloader, extraction, retrieval, rule-claim, or gold-coverage redesign unrelated to this lane
- weakening `phase-eval`, promotion-suite, applicability, compliance, or forest-plan gates just to
  get new coverage artifacts green
- staging ignored `source_library/` outputs unless repository policy changes

## Owner Surfaces

- Single-review V1 eval owner:
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `tests/test_v1_ea_eval.py`
- Review-slot inventory and package-authority owner:
  `src/usfs_r1_ea_sources/replay_context.py`,
  `config/replay_contexts/`,
  `config/v1_real_package_review_coverage_v1.json`,
  `tests/test_replay_context.py`
- Per-review contract owner:
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`
- Aggregate real-package coverage owner:
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `config/v1_real_package_review_coverage_v1.json`,
  `tests/test_real_package_review_coverage_eval.py`
- Docs and routing owner:
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- Keep per-review package scoring in `v1_ea_eval.py`. Do not overload that module with multi-slot
  coverage ownership or repo-wide routing logic.
- Move multi-package coverage ownership into a focused module such as
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py` and register it in `cli_eval.py`.
- Do not leave `v1-ea-eval` on an implicit ECID-only default once tracked multi-package coverage
  exists. Either resolve the contract from a tracked review manifest or fail closed unless the
  caller passes `--eval-file`.
- Keep package-location authority in tracked config or tracked intake ownership only. Do not rely on
  chat history, handoff prose, or raw `source_library/` directory guessing.
- Keep South Plateau blocked-state semantics generic and typed. If a slot is expected to be blocked,
  encode expected lane state and blocker category in tracked config rather than review-ID-specific
  branches.
- If the gold-coverage milestone already introduces a shared manifest or aggregate gate that can own
  this lane cleanly, extend that artifact instead of creating a redundant second manifest.

## Weak-Point Prevention Contract

- Weak point forecast: the repo gains more config files, but only East Crazies actually runs, so
  coverage still effectively rests on one package.
  Owner surface: `config/v1_real_package_review_coverage_v1.json`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`
  Prevention gate: the aggregate gate must require all tracked review slots to be present and must
  report exact slot coverage by review ID, package style, forest profile, and expected readiness
  state.
  Fail threshold: the aggregate gate passes when any required slot is missing, duplicated, or not
  evaluated.
  Controlled violation: remove the West Reservoir or South Plateau slot from the manifest; the
  aggregate gate must fail.
  Future-Codex misuse scenario: a later session adds another ECID-like ready review and claims the
  lane is diverse; duplicate-style or missing-slot checks must fail.

- Weak point forecast: South Plateau disappears from coverage because it is blocked, so the repo
  loses evaluation signal for blocked-but-real review behavior.
  Owner surface: `config/v1_real_package_review_coverage_v1.json`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`
  Prevention gate: the manifest must encode whether each slot is expected reviewer-ready or expected
  blocked, and expected blocked slots must name their allowed blocker categories and lane-state
  expectations.
  Fail threshold: a blocked slot is silently skipped, treated as optional, or reported as fully
  ready without matching live evidence.
  Controlled violation: mark South Plateau as optional or omit its expected blocker category; the
  aggregate gate must fail.
  Future-Codex misuse scenario: a later session hides a blocked lane to keep the suite green; the
  coverage gate must fail closed.

- Weak point forecast: package identity drifts because review IDs, replay contexts, or intake paths
  change outside tracked config.
  Owner surface: `config/replay_contexts/`,
  `config/v1_real_package_review_coverage_v1.json`,
  `tests/test_replay_context.py`
  Prevention gate: every tracked slot must declare one durable package-authority surface and the
  aggregate gate must fail if that authority is missing or inconsistent with the declared review ID.
  Fail threshold: a slot passes with no durable package authority or with review/package identity
  inferred from ad hoc local paths.
  Controlled violation: rename a declared review ID or remove its authority file/path mapping; the
  gate must fail.
  Future-Codex misuse scenario: a later session points the contract at a different local review
  folder without updating tracked authority; manifest validation must fail.

- Weak point forecast: docs and the evaluation register claim multi-package direct coverage, but the
  repo still has only an ECID-only default and no executable aggregate signal.
  Owner surface: `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`
  Prevention gate: the register row, schema docs, and README commands must name the aggregate
  command or manifest-owned per-review resolution path and must match the shipped CLI behavior.
  Fail threshold: docs claim broader real-package coverage while the CLI still defaults only to
  ECID with no aggregate governed path.
  Controlled violation: leave the README or schema docs on the ECID-only default after changing the
  code; doc checks and focused tests must fail or the milestone is not complete.
  Future-Codex misuse scenario: a later session updates code but leaves the register row stale; the
  docs/handoff closeout gate must catch it.

## Milestone Sequence

### Milestone 0 - Post-Gold Rebaseline And Scope Tightening

Outcome label: reduced

Purpose: re-evaluate the live repo after the prior gold-coverage milestone closes, adopt any
equivalent artifacts it already created, and rewrite the remaining scope to match the actual
current system instead of the pre-closeout snapshot.

Implementation:

1. Confirm the prerequisite gold-coverage milestone is closed green and committed, then inspect
   which of the following artifacts already exist or have equivalent replacements:
   - `config/v1_west_reservoir_real_ea_eval.json`
   - `config/v1_south_plateau_real_ea_eval.json`
   - any aggregate gold or real-package coverage manifest/gate
   - any new evaluation-register row for this lane
2. Rebaseline the three tracked review lanes from current repo artifacts and local review outputs:
   - East Crazies current-promotion review ID and package-authority surface
   - West Reservoir review ID, package-authority surface, and current ready state
   - South Plateau review ID, package-authority surface, and current blocked-or-ready state
3. Re-check whether South Plateau still carries only the typed
   `forest_plan_reviewer_not_ready` blocker or whether later work resolved it.
4. Refresh this plan before Milestone 1 if any prerequisite names, review IDs, package authorities,
   coverage classes, or freshness assumptions drifted.
5. If the earlier gold-coverage milestone already implemented equivalent real-package coverage
   routing, reduce this plan to the still-open deltas instead of creating a second parallel lane.

Acceptance criteria:

- This plan or a paired closeout note records the exact active review IDs, package-authority
  surfaces, and expected slot states that the remaining milestones will govern.
- No later milestone duplicates artifacts that the prerequisite milestone already shipped under an
  equivalent governed name.
- If the live repo moved beyond the original gap shape, the remaining milestones are rewritten
  before implementation continues.

Verification:

```bash
git status -sb
rg --files config | rg 'v1_.*real_ea_eval|v1_real_package_review_coverage|gold_coverage'
rg -n "v1-ea-eval|real-package|West Reservoir|South Plateau|ECID" README.md docs/CURRENT_SYSTEM_STATE.md docs/EVALUATION_COVERAGE_REGISTER.md docs/OUTPUT_SCHEMAS.md
```

Docs and handoff updates required before closeout:

- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 0 stop conditions:

- The prerequisite gold-coverage milestone is not actually closed and committed.
- Review IDs or package-authority paths have drifted but no tracked config owner exists yet.
- The live repo already has an equivalent governed lane and this plan has not been narrowed to the
  remaining deltas.

### Milestone 1 - Track Review Slots And Package Authority

Outcome label: resolved

Purpose: make the required multi-package review inventory explicit and fail closed when any tracked
slot loses its package-authority owner.

Implementation:

1. Add or adopt a tracked manifest such as `config/v1_real_package_review_coverage_v1.json` that
   declares the minimum governed slot set:
   - East Crazies current promotion
   - West Reservoir reviewer-ready proving lane
   - South Plateau typed blocked or reviewer-ready expansion lane
2. For each slot, record:
   - review ID
   - package name or stable package label
   - package style or coverage class
   - forest profile
   - per-review contract path
   - package-authority mode and location
   - expected phase-eval or lane-state semantics
   - whether the slot is required for aggregate real-package coverage
3. Add any missing replay-context files or equivalent tracked package-authority mappings for East
   Crazies current promotion and South Plateau if Milestone 0 confirms they are still absent.
4. Add focused validation so missing authority paths, duplicate slot IDs, duplicate coverage
   classes, or incomplete slot metadata fail before any review eval runs.

Acceptance criteria:

- The repo has one governed manifest that names all required review slots and their package-authority
  owners.
- Every required slot has exactly one durable package-authority surface.
- Duplicate slot IDs, duplicate required coverage classes, or missing authority mappings fail
  validation.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_real_package_review_coverage_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 1 stop conditions:

- Any slot still depends on chat-only package identity or an untracked local path guess.
- The manifest can pass without the South Plateau slot when South Plateau remains part of the
  governed coverage boundary.

### Milestone 2 - Expand Per-Review Contracts And Remove ECID-Only Defaulting

Outcome label: resolved

Purpose: ensure the shipped single-review V1 path no longer depends on an implicit ECID-only
contract and that each governed slot has its own explicit review contract.

Implementation:

1. Add or refresh per-review V1 contract files for the governed slots:
   - `config/v1_ecid_real_ea_eval.json`
   - `config/v1_west_reservoir_real_ea_eval.json`
   - `config/v1_south_plateau_real_ea_eval.json`
2. Keep review-specific expectations in those files instead of copying the ECID contract with only
   renamed metadata. The West Reservoir and South Plateau files must carry their own section,
   authority-source, document-role, conditional, and forest-plan expectations.
3. Change `v1_ea_eval.py` and CLI wiring so a single-review invocation no longer silently defaults
   to ECID-only coverage. The supported behavior must become one of:
   - resolve the contract from the tracked review-slot manifest when `--review-id` is provided; or
   - fail closed unless `--eval-file` is provided explicitly.
4. Preserve the broader-EA versus forest-plan lane split. If South Plateau remains blocked,
   represent that by genuine lane results plus manifest-owned expectations, not by suppressing the
   forest-plan lane.
5. Add or extend focused tests proving:
   - West Reservoir resolves and evaluates through its own contract
   - South Plateau resolves and evaluates through its own contract
   - ECID-only implicit defaulting no longer exists
   - malformed or missing contract resolution fails closed

Acceptance criteria:

- Each required review slot has its own governed contract file or an adopted equivalent created by
  Milestone 0.
- `v1-ea-eval` no longer relies on a hidden ECID-only default path for tracked review coverage.
- West Reservoir and South Plateau contract resolution is test-covered and generic.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_v1_ea_eval.py tests/test_real_package_review_coverage_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 2 stop conditions:

- Any new contract is just an ECID clone with mismatched package/source expectations.
- The implementation keeps an ECID-only fallback path that still passes without manifest or
  explicit contract resolution.
- South Plateau blocked-state coverage is hidden instead of represented honestly.

### Milestone 3 - Add Aggregate Real-Package Coverage Gate

Outcome label: resolved

Purpose: give the repo one executable coverage truth surface for this lane instead of three
uncoordinated per-review files.

Implementation:

1. Add or adopt a focused aggregate command such as `real-package-review-coverage-eval` that reads
   the tracked review-slot manifest, evaluates or loads each per-review result, and writes one
   aggregate coverage artifact.
2. Require the aggregate gate to report at minimum:
   - required slot count and covered slot count
   - covered review IDs
   - covered package styles or coverage classes
   - ready slot count
   - blocked slot count
   - expected versus actual blocker categories
   - stale or missing contract/package-authority/result failures
3. Define the minimum governed coverage classes as:
   - one current-promotion reviewer-ready slot
   - one alternate-package reviewer-ready slot
   - one typed blocked or reviewer-ready expansion slot, depending on the Milestone 0 baseline
4. Make the gate fail closed when:
   - coverage collapses back to one package or one coverage class
   - a required slot is missing
   - a blocked slot is hidden or misclassified
   - review/package identity or contract freshness drifts
5. Add focused controlled-violation tests proving the gate fails when a slot is removed, a contract
   path is wrong, a coverage class is duplicated, or South Plateau's expected blocked state is
   mislabeled.

Acceptance criteria:

- The repo has one governed aggregate artifact for real-package review coverage.
- The aggregate gate passes only when all required slots are represented with correct ready or
  blocked semantics.
- The gate fails on the controlled violations above without weakening any existing readiness gates.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_real_package_review_coverage_eval.py tests/test_v1_ea_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 3 stop conditions:

- The aggregate gate can pass while any required slot is absent or stale.
- The gate reports only green counts and hides the specific blocked-slot semantics.
- The implementation weakens `phase-eval`, promotion-suite, or per-review contract checks to make
  the aggregate result pass.

### Milestone 4 - Register And Closeout Routing

Outcome label: resolved

Purpose: make this coverage lane durable in docs and readiness routing so future work improves it
through governed artifacts rather than through memory or handoff prose.

Implementation:

1. Add or update the `docs/EVALUATION_COVERAGE_REGISTER.md` row for this lane so it explicitly owns
   the real-package review coverage command, manifest, categories, and direct-eval status.
2. Update `README.md` and `docs/OUTPUT_SCHEMAS.md` so the documented default path matches the
   shipped behavior after Milestone 2. If `v1-ea-eval` now requires tracked review resolution or
   explicit `--eval-file`, the docs must say so directly.
3. Update `docs/CURRENT_SYSTEM_STATE.md` with the live baseline captured during this milestone:
   - which slots are ready
   - whether South Plateau remains typed blocked or has become ready
   - the governed aggregate coverage command and manifest
4. Append a durable routing note to `docs/SESSION_HANDOFF.md` that names the aggregate lane,
   current slot states, and the next follow-on only if a gap remains after closeout.
5. Prove the docs are not overstating readiness. If South Plateau remains blocked, closeout docs
   must preserve that blocked status while still marking the coverage lane itself resolved.

Acceptance criteria:

- The evaluation register now has a governed row for this lane.
- README and output schema docs no longer imply ECID-only shipped coverage.
- Current-state and handoff docs match the actual ready-versus-blocked slot states proven by the
  live commands.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 4 stop conditions:

- Docs or the register still overstate South Plateau readiness.
- The closeout depends on ignored `source_library/` artifacts without durable tracked routing.

## Verification And Anti-Weakening Rules

- Do not get this milestone green by dropping the South Plateau slot, marking it informational, or
  weakening its blocker semantics.
- Do not get this milestone green by keeping an implicit ECID-only fallback while only documenting a
  broader path.
- Do not weaken tests, evals, or gates just to reach a green result. Any replacement coverage must
  be equivalent or stronger, and the closeout evidence must prove coverage did not get easier.
- When tests or gate logic change, add negative or controlled-violation coverage showing the lane is
  harder to fake, not easier to pass.
- For code milestones, run focused tests, `tests/test_architecture_contract.py`, `ruff check src
  tests`, `python -m compileall src`, and `git diff --check`.
- For live review coverage claims, rerun only the bounded review-scoped commands required for the
  three tracked slots. Do not rerun downloader, full corpus rebuild, or broad extraction workflows
  unless Milestone 0 proves freshness cannot otherwise be established.

## Commit Policy

- Complete one local atomic commit per milestone after the milestone's verification passes.
- Stage only the verified slice for that milestone: code, tests, config, docs, and any tracked
  helper artifacts needed to explain the change.
- Do not stage ignored `source_library/` outputs unless repository policy changes.
- If a milestone reaches verified code and docs but is not yet committed, report it as
  ready-to-close, not complete.

## Global Stop Conditions

- The required implementation would weaken `phase-eval`, promotion-suite, forest-plan, or existing
  applicability/compliance gates.
- The required implementation would replace tracked package-authority config with chat-only routing.
- The required implementation needs a broader forest-plan or South Plateau component-resolution
  milestone to proceed; in that case, stop and route the blocker instead of faking package coverage.
