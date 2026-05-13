# Gold Coverage Expansion Milestone Plan

Date: 2026-05-12

Status: Proposed

Owner context: This is a fresh standalone follow-on milestone plan. It does not append to
`docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`; it starts only after that milestone
is closed green and committed. Because the downstream-direct-eval plan itself depends on the
upstream evaluation-coverage plan, this milestone also assumes the upstream-created
`docs/EVALUATION_COVERAGE_REGISTER.md` and the direct-eval-aware readiness route already exist.
If those prerequisite closeouts land equivalent artifacts under different names, Sequence 0 of this
plan must refresh the routing before code changes begin.

## Purpose

Close the gold-coverage gap between the current authority universe and the repo's adjudicated gold
and real-package review surfaces.

Today the repo has working gold gates, but the governed universe is much narrower than the actual
authority surface:

- applicability gold already has the required five profile types, but it still operates over a tiny
  three-source-chunk / three-candidate-rule core plus one narrow expanded water-family example;
- compliance gold exists, but the governing package set still needs broader named-family coverage;
- the default real-package review contract remains East Crazies only, so broad authority drift can
  hide if one review stays green while other forest/package styles are untracked.

This milestone exists to make gold coverage broad enough, adjudicated enough, and package-diverse
enough that authority drift across FLPMA, wetlands, MBTA, NHPA, roadless, tribal/cultural, and
multi-forest plan triggers fails closed.

This milestone is not complete until the widened gold contracts, required real-package review
contracts, aggregate gold-coverage gate, readiness/register wiring, docs, handoff updates, and one
local atomic commit all land together. A verified but uncommitted slice is only ready-to-close.

## Current Evidence

- `config/applicability_gold_eval_v0.json` currently carries `5` profile cases, but only `3`
  `source_chunks`, a `3`-rule candidate universe for the core positive/mixed/negative coverage,
  and one narrow expanded-family unresolved/adjudicated water example.
- `src/usfs_r1_ea_sources/applicability_eval.py` already computes
  `authority_family_template_coverage`, `required_real_package_coverage_tags`, and required gold
  profile checks, but the actual adjudicated gold payload is still thin relative to the `19`
  declared high-priority authority families.
- `config/promotion_suite_v1.json` currently checks
  `applicability_gold_eval_case_count >= 5` and
  `authority_family_template_coverage.adjudicated_covered_family_count >= 1`, which is too weak to
  prove broad authority coverage.
- `config/v1_ecid_real_ea_eval.json` is the only shipped real-package V1 review contract, and
  `src/usfs_r1_ea_sources/v1_ea_eval.py` defaults to it through `DEFAULT_V1_EA_EVAL_PATH`.
- `config/replay_contexts/` currently contains tracked replay context for
  `west-reservoir-67436` and `v1-cg-ecid-source-delta-review`, but not for the promoted
  East-Crazies current-promotion review or the South Plateau expansion review.
- `docs/CURRENT_SYSTEM_STATE.md` records three live named package surfaces that are relevant to
  this gap:
  - East Crazies current-promotion review at
    `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`
  - West Reservoir live Flathead proving review via
    `config/replay_contexts/west-reservoir-67436.json`
  - South Plateau expansion review at
    `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`
- `docs/CURRENT_SYSTEM_STATE.md` also records that South Plateau is a real package with a known,
  typed blocker shape rather than a missing-package placeholder:
  `broader_ea` artifacts are present, but forest-plan component adjudication remains the blocking
  lane.

## Goal

Resolve the scoped gold-coverage weakness by broadening adjudicated applicability gold, compliance
gold, and real-package review-contract coverage to the point where named authority-family drift and
package-style drift are both visible and gated.

Completion means all of the following are true:

- the repo has a tracked gold-coverage contract that names required authority families, required
  real-package review contracts, required forest diversity, and required package-style diversity;
- applicability gold covers the named family set for FLPMA, wetlands, MBTA, NHPA, roadless,
  tribal/cultural, and multi-forest plan triggers through adjudicated cases, not only through
  declared tags;
- compliance gold likewise carries named-family case coverage for those themes;
- the repo has at least `3` tracked real-package review contracts spanning at least `2` forests and
  at least `3` package-style tags:
  clean baseline, live external/noisier proving package, and blocked-but-typed expansion package;
- the aggregate gold-coverage gate fails closed when required families, required real-package
  contracts, or freshness assumptions drift.

## Non-Goals

- Do not reopen the upstream capture/catalog/extraction lane or the downstream direct-eval ranking
  lane beyond consuming their completed register/readiness outputs.
- Do not treat this milestone as a mandate to make every real package fully reviewer-ready. The gap
  is missing contract coverage; a typed, explicitly declared blocked package can still be valuable
  coverage if the blocker shape is governed and fresh.
- Do not resolve South Plateau's existing forest-plan reviewer queue in this milestone unless that
  is strictly necessary to preserve declared blocker semantics. Keep the blocker typed if it still
  exists.
- Do not invent review-specific heuristics keyed to one package or one review ID.
- Do not weaken existing promotion-suite, applicability, compliance, or V1 tests to get green.
  Any replacement coverage must be equivalent or broader.

## Scope

- adjudicated applicability gold coverage
- adjudicated compliance gold coverage
- real-package V1 review contract coverage across East Crazies, West Reservoir, and South Plateau
- tracked replay-context or declared intake ownership for those package surfaces
- an aggregate gold-coverage contract and executable gate
- promotion-suite and evaluation-coverage-register wiring for the widened gold surfaces

## Out Of Scope

- broad authority-universe redesign
- new downloader, extraction, retrieval, or rule-link ranking work
- closing every active forest-plan blocker in South Plateau
- adding more than the minimum required real-package review set for this milestone unless a later
  follow-on is explicitly routed

## Owner Surfaces

- Applicability gold owner:
  `src/usfs_r1_ea_sources/applicability_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `config/applicability_gold_eval_v0.json`,
  `config/applicability_gold_eval_v1.json`,
  `tests/test_applicability_eval.py`
- Compliance gold owner:
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/cli_compliance.py`,
  `config/compliance_gold_eval_v0.json`,
  `config/compliance_gold_eval_v1.json`,
  `tests/test_compliance_review.py`
- Real-package review contract owner:
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/replay_context.py`,
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `config/replay_contexts/`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_replay_context.py`
- Aggregate gold-coverage gate owner:
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `config/gold_coverage_v1.json`,
  `tests/test_gold_coverage_eval.py`
- Promotion/docs/routing owner:
  `config/promotion_suite_v1.json`,
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep applicability-gold-specific checks in `applicability_eval.py`. Do not move applicability
  adjudication semantics into a generic aggregate gate.
- Keep compliance-gold-specific checks in `compliance_gold_eval.py`. Do not overload
  `compliance_review_eval.py` with gold-contract ownership.
- Keep real-package review-contract evaluation in `v1_ea_eval.py`. If the contract needs to express
  expected blocked lane states or allowed blocker categories, add those fields there instead of
  writing review-ID-specific post-process filters elsewhere.
- If an aggregate gate is added, place it in a focused module such as
  `src/usfs_r1_ea_sources/gold_coverage_eval.py` and register it in `cli_eval.py`. The aggregate
  gate must feed the existing evaluation coverage register and promotion suite; do not create a
  detached report family with no readiness owner.
- Use `config/replay_contexts/<review_id>.json` or tracked intake paths under
  `source_library/reviews/_intake/` as the only durable package-location authority. Do not leave
  required package boundaries implicit in chat history or handoff prose.
- Preserve `config/*_v0.json` gold files only if backward compatibility is intentionally maintained
  and test-covered. The shipped default inputs for widened gold coverage should move to explicit
  v1-owned contracts.

## Weak-Point Prevention Contract

- Weak point forecast: the new gold suites grow in case count but still concentrate on one narrow
  family, so the named authority gap survives behind larger numbers.
  Owner surface: `config/applicability_gold_eval_v1.json`,
  `config/compliance_gold_eval_v1.json`,
  `config/gold_coverage_v1.json`,
  `tests/test_gold_coverage_eval.py`
  Prevention gate: the aggregate contract must name required family/theme coverage for FLPMA,
  wetlands, MBTA, NHPA, roadless, tribal/cultural, and multi-forest plan triggers, and the lane
  contracts must report exact covered family IDs.
  Fail threshold: a gold suite passes without one of the named themes or without explicit covered
  family IDs for that theme.
  Controlled violation: remove one named theme such as MBTA or roadless from the widened gold file;
  the aggregate gate must fail.
  Future-Codex misuse scenario: a later session adds more NEPA-only cases and claims broad gold
  coverage; the named-theme gate must fail.

- Weak point forecast: the new real-package coverage still effectively depends on one forest or one
  package style, so multi-forest or noisy-package drift remains invisible.
  Owner surface: `config/gold_coverage_v1.json`,
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `tests/test_gold_coverage_eval.py`
  Prevention gate: the aggregate contract must require at least `3` real-package review contracts,
  at least `2` distinct forests, and at least `3` package-style tags.
  Fail threshold: the aggregate gate passes with only East Crazies-like Custer Gallatin coverage or
  with only one package-style pattern.
  Controlled violation: drop West Reservoir or South Plateau from the manifest; the gate must fail.
  Future-Codex misuse scenario: a later session keeps only the clean East Crazies review because it
  is easier to keep green; the diversity gate must fail.

- Weak point forecast: South Plateau's current blocker is hidden or normalized away to make the
  multi-review set look greener than reality.
  Owner surface: `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `tests/test_v1_ea_eval.py`
  Prevention gate: real-package contracts must be able to declare expected lane states and allowed
  blocker categories. A typed blocked contract is acceptable only when the blocker remains explicit
  and matched.
  Fail threshold: South Plateau coverage is claimed green by dropping the forest-plan blocker from
  the contract or by ignoring lane-level failure categories.
  Controlled violation: remove the expected `forest_plan_reviewer_not_ready` blocker policy from the
  South Plateau contract while keeping the actual review artifacts blocked; the eval must fail.
  Future-Codex misuse scenario: a later session changes the contract to match a wishful green state
  without rerunning the review artifacts; the lane-state/blocker gate must fail.

- Weak point forecast: external or local package paths drift out of tracked config, making reruns
  impossible or ambiguous.
  Owner surface: `config/replay_contexts/`,
  `source_library/reviews/_intake/`,
  `tests/test_replay_context.py`,
  `docs/SESSION_HANDOFF.md`
  Prevention gate: every required real-package contract must have a tracked replay context or a
  tracked intake path recorded in the aggregate gold contract.
  Fail threshold: a required review contract depends on a package surface named only in prose or in
  a stale local shell command.
  Controlled violation: remove the West Reservoir replay context or the South Plateau intake
  declaration from the contract; the aggregate gate must fail.
  Future-Codex misuse scenario: a later session assumes a local package path still exists because
  it was true in one handoff; the package-authority gate must fail before claiming coverage.

- Weak point forecast: the widened gold coverage lands as raw configs and tests, but promotion and
  the evaluation coverage register still only enforce the old `case_count >= 5` / `adjudicated >= 1`
  thresholds.
  Owner surface: `config/promotion_suite_v1.json`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `docs/OUTPUT_SCHEMAS.md`
  Prevention gate: promotion and register wiring must use the widened gold-coverage outputs and
  stronger thresholds, not only the legacy applicability-gold summary.
  Fail threshold: a milestone lands with broader gold files but unchanged low-value promotion
  thresholds.
  Controlled violation: keep the old promotion-suite checks while widening the gold files; the
  aggregate gate test must fail.
  Future-Codex misuse scenario: a later session claims the gap is closed because configs got larger,
  but the governing gate still only checks five cases and one adjudicated family; the promotion and
  register gates must fail.

## Milestone Sequence

### Sequence 0 - Post-Downstream Preflight And Gold-Coverage Contract Baseline

Outcome label: reduced

Purpose: start this lane only after the previous evaluation-coverage milestones are truly complete,
and declare the exact gold-coverage contract before widening cases or review contracts.

Implementation tasks:

1. Verify the prerequisite closeouts exist and are green:
   - `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md` is closed and committed
   - `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md` is closed and committed
   - `docs/EVALUATION_COVERAGE_REGISTER.md` exists
   - the existing readiness route distinguishes validation, direct eval, and gold coverage
2. Add `config/gold_coverage_v1.json` with:
   - required widened gold input paths
   - required real-package review contracts
   - required named theme coverage:
     `land_exchange`, `water_wetlands`, `migratory_birds`, `cultural_tribal`, `roadless`,
     `forest_plan_consistency`, `multi_forest_plan_trigger`
   - required real-package review IDs:
     `v1-cg-ecid-compliance-review`,
     `west-reservoir-67436`,
     `region1-expansion-south-plateau-landscape-treatment`
   - required review diversity floors:
     `distinct_forest_count >= 2`,
     `distinct_package_style_count >= 3`,
     `required_review_contract_count = 3`
   - freshness and ownership fields for replay-context or intake-path authorities
3. Extend `docs/EVALUATION_COVERAGE_REGISTER.md` with baseline rows for:
   `applicability_gold_eval`, `compliance_gold_eval`, `v1_real_review_contracts`,
   and `gold_coverage_eval`
4. Add failing-or-baseline tests in `tests/test_gold_coverage_eval.py` that reject:
   - missing named theme coverage
   - missing required review contracts
   - insufficient forest/style diversity
   - undeclared package authority boundaries
5. Confirm the three declared package surfaces still exist or are still intentionally external:
   - East Crazies intake path in repo
   - West Reservoir replay context with external package path
   - South Plateau intake path in repo

Acceptance signals:

- The milestone has one explicit gold-coverage contract and one register extension, not a set of
  ad hoc widened fixtures with no aggregate owner.
- Missing package authority boundaries or missing named themes fail before broader implementation.
- The real-package target set is declared up front rather than inferred from old handoffs.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_gold_coverage_eval.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The prerequisite upstream or downstream evaluation-coverage milestones are not actually complete.
- One of the required package surfaces is unavailable and there is no tracked replacement path.
- The only way to proceed is to weaken the required theme set or drop the multi-review diversity
  floors.

### Sequence 1 - Expand Applicability Gold To Named Authority-Family Coverage

Outcome label: resolved

Purpose: make applicability gold broad enough that named authority-family drift fails before
promotion.

Implementation tasks:

1. Add `config/applicability_gold_eval_v1.json` and move the shipped default applicability-gold
   path to it.
2. Expand the adjudicated gold payload to include:
   - at least `12` cases
   - at least `12` `source_chunks`
   - positive, negative, unresolved, and adjudicated coverage across the named themes:
     FLPMA/land exchange, wetlands/water permits, MBTA/migratory birds, NHPA/cultural,
     tribal/sacred sites, roadless, and multi-forest plan triggers
3. Require at least these exact widened gold coverage floors:
   - `case_count >= 12`
   - `source_chunk_count >= 12`
   - `positive_covered_family_count >= 7`
   - `negative_covered_family_count >= 7`
   - `unresolved_covered_family_count >= 3`
   - `adjudicated_covered_family_count >= 3`
   - `required_real_package_coverage_tags` must include the named theme set
4. Extend `run_applicability_gold_eval(...)` so it fails when the widened family/theme floors are
   missed, not only when the five profile types are missing.
5. Update `config/promotion_suite_v1.json` so the applicability-gold gate checks the widened case
   count and the widened covered-family floors rather than only `case_count >= 5` and one
   adjudicated family.

Acceptance signals:

- Applicability gold no longer proves promotion over only three source chunks and a one-family
  adjudicated expansion.
- The widened applicability-gold contract covers the named family set through adjudicated cases.
- Promotion checks fail when a named family theme is removed.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval --output-dir source_library --gold-file config/applicability_gold_eval_v1.json
git diff --check
```

Stop conditions:

- Applicability gold can only pass by lowering the widened family floors or by collapsing back to
  NEPA-only cases.
- The widened gold file depends on untracked review-local artifacts instead of governed fixtures or
  declared package surfaces.

### Sequence 2 - Expand Compliance Gold To Named Review-Family Coverage

Outcome label: resolved

Purpose: widen the adjudicated compliance-gold gate so named rule-family drift across the target
themes becomes visible.

Implementation tasks:

1. Add `config/compliance_gold_eval_v1.json` and move the shipped default compliance-gold path to
   it.
2. Expand the compliance-gold case set to include:
   - at least `14` cases
   - the existing required profiles `positive`, `mixed`, and `negative`
   - explicit named coverage tags for:
     `land_exchange`, `water_wetlands`, `migratory_birds`, `cultural_tribal`, `roadless`,
     `forest_plan_consistency`, and `multi_forest_plan_trigger`
   - clean and noisy package styles, not only all-authorities control text
3. Extend `run_compliance_gold_eval(...)` to validate:
   - required coverage tags
   - required named source-record families by case
   - minimum real-package-like case count
   - required generated/base rule-pack mapping expectations where used
4. Keep `compliance_gold_eval` aligned with `compliance_review_eval` and the widened downstream
   direct-eval contracts so gold coverage does not drift onto stale lower-layer assumptions.
5. Update promotion gating so the widened compliance-gold coverage contract is visible in the same
   readiness surfaces as other gold coverage.

Acceptance signals:

- Compliance gold no longer passes on a narrow proving set that omits the named authority themes.
- Removing FLPMA, wetlands, MBTA, NHPA, roadless, tribal/cultural, or multi-forest plan cases
  fails the gold gate.
- The widened compliance-gold contract records both clean and noisy package-style coverage.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json
git diff --check
```

Stop conditions:

- Compliance gold only goes green by deleting noisy package-style cases.
- Named family coverage exists only as loose tags rather than source-record and rule-coverage
  expectations.

### Sequence 3 - Add Multi-Review Real-Package Contracts With Tracked Package Authority

Outcome label: resolved

Purpose: stop treating East Crazies as the only real-package truth surface and make real-package
coverage durable across multiple forests and package styles.

Implementation tasks:

1. Keep `config/v1_ecid_real_ea_eval.json` as the clean baseline contract and add:
   - `config/v1_west_reservoir_real_ea_eval.json`
   - `config/v1_south_plateau_real_ea_eval.json`
2. Add tracked package authority for each review contract:
   - `config/replay_contexts/v1-cg-ecid-compliance-review.json`
   - keep `config/replay_contexts/west-reservoir-67436.json`
   - `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`
     or an equivalent tracked intake-path declaration owned by the aggregate gold contract
3. Extend `v1_ea_eval.py` contract handling so review contracts can declare:
   - `forest_unit_id`
   - `package_style_tags`
   - expected lane states such as `broader_ea_passed` and `forest_plan_passed`
   - allowed blocker categories when a noisy package is intentionally typed-blocked rather than
     reviewer-ready
4. Declare the target review set for this milestone:
   - East Crazies:
     `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`
     with style tag `clean_baseline`
   - West Reservoir:
     `west-reservoir-67436` via replay context, `flathead-nf`, style tag `live_external_noisy`
   - South Plateau:
     `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`,
     `custer-gallatin-nf`, style tag `typed_blocked_expansion`
5. Preserve South Plateau's typed blocker rather than forcing false green:
   - broader EA lane should remain governed by its actual review outputs
   - forest-plan blocker expectations must stay explicit if they still exist

Acceptance signals:

- The repo has `3` tracked real-package review contracts with declared package authority.
- The real-package set spans at least `2` forests and `3` package styles.
- South Plateau remains useful coverage even if it is still blocked, because the blocker shape is
  typed and governed rather than silently ignored.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_v1_ea_eval.py tests/test_replay_context.py tests/test_gold_coverage_eval.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436 --eval-file config/v1_west_reservoir_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment --eval-file config/v1_south_plateau_real_ea_eval.json
git diff --check
```

Stop conditions:

- A required package boundary is not durable in tracked config or tracked intake paths.
- South Plateau can only be included by hiding or deleting the currently typed forest-plan blocker.
- The new real-package set falls back to one forest or one package style.

### Sequence 4 - Add Aggregate Gold-Coverage Gate And Wire Promotion/Register Truth

Outcome label: resolved

Purpose: make the widened gold and real-package coverage visible as one executable gate rather than
scattered config truth.

Implementation tasks:

1. Add `src/usfs_r1_ea_sources/gold_coverage_eval.py` and register
   `gold-coverage-eval` in `src/usfs_r1_ea_sources/cli_eval.py`.
2. Have the aggregate gate read `config/gold_coverage_v1.json`, run or validate:
   - `applicability-gold-eval`
   - `compliance-gold-eval`
   - the three required `v1-ea-eval` contracts
3. Write `source_library/reviews/gold_coverage_eval/gold_coverage_eval_results.json` with:
   - named theme coverage
   - distinct forest and package-style counts
   - per-review contract freshness and package-authority ownership
   - reviewer-ready versus typed-blocked review counts
   - failure categories when a family, review contract, or package authority is missing
4. Extend `config/promotion_suite_v1.json` and `docs/EVALUATION_COVERAGE_REGISTER.md` to consume
   the aggregate gold-coverage output rather than the legacy low-value thresholds alone.
5. Update docs and handoff so operators can tell which gold families and which real-package review
   contracts currently govern authority drift.

Aggregate threshold contract for `gold-coverage-eval`:

- `required_theme_count = 7`
- `applicability_gold_case_count >= 12`
- `compliance_gold_case_count >= 14`
- `required_review_contract_count = 3`
- `distinct_forest_count >= 2`
- `distinct_package_style_count >= 3`
- `reviewer_ready_review_count >= 2`
- `typed_blocked_review_count >= 1`
- `missing_required_review_contract_count = 0`
- `missing_package_authority_count = 0`

Acceptance signals:

- Gold coverage is governed by one executable aggregate gate.
- Promotion and the evaluation coverage register both fail when named themes or review diversity
  drift.
- The milestone closes the coverage gap without pretending every package is green.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_gold_coverage_eval.py tests/test_applicability_eval.py tests/test_compliance_review.py tests/test_v1_ea_eval.py tests/test_replay_context.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval --output-dir source_library --manifest config/gold_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

Stop conditions:

- The aggregate gate becomes a detached report that promotion and the evaluation register do not
  use.
- The only way to pass is to lower review diversity or named-theme thresholds.

## Required Implementation Artifacts

- `config/gold_coverage_v1.json`
- `config/applicability_gold_eval_v1.json`
- `config/compliance_gold_eval_v1.json`
- `config/v1_west_reservoir_real_ea_eval.json`
- `config/v1_south_plateau_real_ea_eval.json`
- `config/replay_contexts/v1-cg-ecid-compliance-review.json`
- `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`
  or an explicit contract-owned equivalent
- `src/usfs_r1_ea_sources/gold_coverage_eval.py`
- `tests/test_gold_coverage_eval.py`

## Required Documentation And Handoff Updates

- `README.md`
  add the widened gold-coverage and real-package review-contract summary
- `docs/OUTPUT_SCHEMAS.md`
  document the widened gold-input contract fields and the `gold_coverage_eval_results.json` schema
- `docs/EVALUATION_COVERAGE_REGISTER.md`
  add gold-coverage subsystem rows, thresholds, and current status
- `docs/CURRENT_SYSTEM_STATE.md`
  update only if the live named review-contract set or aggregate gold-coverage truth changes
- `docs/SESSION_HANDOFF.md`
  route the next session to the first incomplete sequence and record the declared package surfaces

## Required Verification Gates

Minimum closeout gates for the full milestone:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_gold_coverage_eval.py tests/test_applicability_eval.py tests/test_compliance_review.py tests/test_v1_ea_eval.py tests/test_replay_context.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval --output-dir source_library --gold-file config/applicability_gold_eval_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436 --eval-file config/v1_west_reservoir_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment --eval-file config/v1_south_plateau_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval --output-dir source_library --manifest config/gold_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

If one of the real-package reviews needs a fresh compliance replay before `v1-ea-eval` is valid,
rerun the declared review command against its tracked package authority before closeout and record
the exact command in `docs/SESSION_HANDOFF.md`.

## Acceptance Criteria

- The repo has one explicit gold-coverage contract and one executable aggregate gold gate.
- Applicability gold broadens from the narrow three-source-chunk core to a named family/theme set
  covering FLPMA, wetlands, MBTA, NHPA, roadless, tribal/cultural, and multi-forest plan triggers.
- Compliance gold likewise covers the named family/theme set.
- The repo has `3` required real-package review contracts:
  `v1-cg-ecid-compliance-review`,
  `west-reservoir-67436`,
  `region1-expansion-south-plateau-landscape-treatment`.
- The real-package set spans at least `2` forests and at least `3` package-style tags.
- Each required real-package contract has tracked package authority through replay context or a
  tracked intake path.
- West Reservoir and East Crazies remain reviewer-ready review contracts; South Plateau may remain
  typed-blocked only if the blocker stays explicit and matches the declared contract.
- Promotion and the evaluation coverage register consume the widened gold-coverage truth rather than
  the legacy low-value thresholds alone.
- Replacement coverage is equivalent or broader. Do not weaken tests, drop noisy packages, or lower
  named-theme thresholds just to get green.

## Stop Conditions

- The previous upstream or downstream evaluation-coverage milestones are not actually complete.
- One or more required package surfaces are unavailable with no tracked replacement authority.
- South Plateau's blocker shape becomes ambiguous or broader than the contract can govern.
- The only path to green is to remove a named authority theme, drop a review contract, or lower the
  forest/style diversity floors.
- The implementation starts creating a detached gold report that promotion and the evaluation
  coverage register do not use.

## Local Commit Closeout Policy

This milestone is not complete until:

1. all required verification gates pass;
2. the widened gold configs, real-package contracts, aggregate gate, tests, docs, register, and
   handoff are updated together;
3. only the verified gold-coverage slice is staged; and
4. one local atomic commit lands the milestone.

Do not stage unrelated dirty files already present in the worktree. If unrelated files remain
dirty, leave them untouched and call them out in the final handoff. Do not weaken tests or lower
coverage thresholds to get a passing result; any replacement coverage must be equivalent or broader.

## Residual Risks And Next Milestone Routing

- This milestone resolves the gold-coverage gap for the named authority themes and the declared
  three-review package set, but it does not make every future Region 1 package contract-adjudicated.
- If the widened gold gate exposes missing authority families outside the named theme set, route the
  next milestone to a further authority-family gold expansion rather than silently broadening this
  milestone after closeout.
- If South Plateau's forest-plan blocker remains after this milestone, keep it as a typed,
  declared expansion blocker and route the actual closure work to the South Plateau forest-plan lane
  instead of weakening the real-package contract.
