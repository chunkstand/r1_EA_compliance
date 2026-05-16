# Forest Plan Component Eval Coverage Milestone Plan

Date: 2026-05-13

Status: Proposed 2026-05-16 (Milestone 0 resolved through local commit `8fdcf25`; Milestone 1 resolved; Milestone 2 next)

Milestone 1 closeout summary on 2026-05-16:

- The repo now ships the standalone component-retrieval eval contract at
  `config/forest_plan_component_retrieval_eval_v1.json`.
- The new owner command is `forest-plan-component-retrieval-eval`, implemented in
  `src/usfs_r1_ea_sources/forest_plan_component_retrieval_eval.py` and registered through
  `src/usfs_r1_ea_sources/cli_eval.py`.
- The producer writes
  `source_library/evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_results.json`
  and
  `source_library/evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_report.md`.
- The shipped contract binds to active source set `source-set-5e65d845ce77e1a0`, requires `4`
  expected-pass cases plus `2` hard negatives across Beaverhead-Deerlodge, Custer Gallatin, and
  Flathead, and currently measures an exact top-hit retrieval surface with `top_k=1`.
- The exact top-hit scope is intentional for Milestone 1. Focused tests still fail when required
  components are missing, wrong-forest components are selected under higher-`top_k` fixture
  pressure, or hard-negative queries return components. Broader multi-hit review coverage remains
  Milestone 2 work.
- The latest live replay on active source set `source-set-5e65d845ce77e1a0` is green and
  fail-closed with `case_count=6`, `expected_pass_case_count=4`, `hard_negative_case_count=2`,
  `component_retrieval_precision=1.0`, `component_retrieval_recall=1.0`,
  `applicable_standard_component_recall=1.0`, `wrong_forest_component_rate=0.0`, and
  `hard_negative_zero_match_rate=1.0`.
- With the standalone retrieval producer now live, the next executable slice in this packet is
  Milestone 2: expand review-scoped component eval coverage beyond ECID.

Milestone 0 closeout summary on 2026-05-15:

- The Milestone 0 closeout checkpoint is local commit `8fdcf25`
  (`docs: close component eval coverage milestone 0`).
- The predecessor chain is now confirmed under its live names. The cross-forest predecessor packet
  is resolved through local commits `a958dc8` and alignment pass `59875ec`, the direct-eval-aware
  source-set `phase-eval` seam exists under `config/phase_eval_direct_eval_v1.json`, and the
  predecessor aggregate profile-eval route exists under
  `config/region1_forest_plan_profile_eval_coverage_v1.json` plus
  `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json`.
- The current component-eval contract roster is exact and still ECID-only:
  `config/forest_plan_component_eval_seed.json`
  (`review_id="v1-cg-ecid-compliance-review"`,
  `source_set_id="source-set-ba8d0feae79501b8"`) and
  `config/forest_plan_component_evals/v1-cg-ecid-source-delta-review.json`
  (`review_id="v1-cg-ecid-source-delta-review"`,
  `source_set_id="source-set-8a4005c8a083af1a"`).
- The current component-eval result roster is exact:
  `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json`
  exists and passes with `35` cases on `source-set-ba8d0feae79501b8`;
  `source_library/reviews/v1-cg-ecid-source-delta-review/forest_plan_component_eval_results.json`
  exists and passes with `36` cases on `source-set-8a4005c8a083af1a`;
  `source_library/reviews/west-reservoir-67436/forest_plan_component_eval_results.json` is absent.
- West Reservoir is confirmed in-scope for later milestones in this packet because it is one of
  the current non-Custer proving reviews on active full-canonical source set
  `source-set-5e65d845ce77e1a0`, but it still lacks both a tracked component-eval contract and a
  component-eval result artifact.
- South Plateau is explicitly routed out of this coverage boundary for now. Its live review on
  `source-set-ba8d0feae79501b8` carries `forest_plan_component_adjudication_eval.json`,
  `compliance_review.json`, and green review-scoped `phase-eval`, but it does not carry a tracked
  component-eval contract or `forest_plan_component_eval_results.json`. Milestones 1-2 in this
  packet therefore keep the minimum governed review set at ECID current promotion, ECID replay,
  and West Reservoir unless a later milestone adds South Plateau as an explicit typed slot.
- The missing-surface baseline is now locked: there is still no standalone component-retrieval
  eval producer under live code or config, there is still no
  `config/forest_plan_component_evals/west-reservoir-67436.json`, and
  `src/usfs_r1_ea_sources/forest_plan_component_eval.py` still defaults to
  `config/forest_plan_component_eval_seed.json` when `--eval-file` is not supplied.
- With the live baseline now pinned, the next executable slice in this packet is Milestone 1: add
  the standalone component-retrieval eval producer.

Owner context: This is a fresh standalone follow-on milestone plan. It does not append to
`docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`, which remains the earlier broad NFMA
implementation and historical design artifact. This plan starts only after
`docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md` closes green and is committed.
Because that cross-forest profile-eval milestone depends on the phase-eval direct-eval milestone,
the real-package coverage milestone, the gold-coverage milestone, and the upstream/downstream
evaluation-coverage milestones, this plan assumes the earlier chain already delivered the
evaluation coverage register, the direct-eval-aware `phase-eval` seam, and the tracked Region 1
profile-eval route. If those predecessor closeouts land equivalent artifacts under different
names, Milestone 0 of this plan must refresh the routing before code changes begin rather than
duplicating the same ownership under new names.

## Purpose

Close the gap between a strong local East Crazies forest-plan component eval and governed
multi-forest component-eval coverage.

Today the repo has a tight adjudicated component-eval surface for one proving review:

- `config/forest_plan_component_eval_seed.json` governs the East Crazies current-promotion review
  with `35` cases, all applicable standards required, and strict `1.0` precision/recall/citation
  thresholds;
- `config/forest_plan_component_evals/v1-cg-ecid-source-delta-review.json` governs the replay
  review variant; and
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json`
  exists and passes.

The remaining weakness is coverage breadth and evaluation shape:

- there is no standalone component-retrieval precision/recall eval producer;
- the shipped single-review component-eval path still defaults to the East Crazies seed contract;
- `config/forest_plan_component_evals/` currently contains only the ECID replay contract;
- `config/forest_plan_component_evals/west-reservoir-67436.json` is absent; and
- the current non-Custer live-package proving lane has no governed component-eval contract/result
  even though it is now one of the main proving reviews.

This milestone exists to add a standalone component-retrieval eval lane, broaden review-scoped
component eval beyond the ECID proving slice, and wire the resulting coverage into the repo's
direct-eval and promotion routing without overstating that every forest or review is
reviewer-ready.

This milestone is not complete until the component-retrieval eval contract, review-scoped
component-eval coverage manifest, West Reservoir contract surface, aggregate coverage gate,
phase-eval/promotion routing, docs, handoff updates, and one local atomic commit per milestone all
land together. A verified but uncommitted slice is only ready-to-close.

## Dependency And Milestone 0 Refresh Rule

- Start this milestone only after `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`
  is closed green and committed.
- If the predecessor milestone lands its aggregate profile-eval producer, phase-eval direct-eval
  inputs, or coverage-register rows under different names, Milestone 0 must adopt those artifacts
  and rewrite this plan's later commands before implementation continues.
- If the live review roster, active source set, or component artifact family drift before
  implementation starts, Milestone 0 must refresh the target contract set before code changes
  begin.
- If the live review roster shows that South Plateau's forest-plan component lane now belongs in
  this coverage boundary, Milestone 0 must either adopt it as an explicit typed blocked slot or
  route it out by name. The plan must not leave that decision implicit.
- This plan is component-eval coverage work, not a broad reviewer-ready or live-package expansion
  claim for every forest.

## Current Evidence

- `config/forest_plan_component_eval_seed.json` is still the default shipped component-eval
  contract. It is bound to `review_id="v1-cg-ecid-compliance-review"` and
  `source_set_id="source-set-ba8d0feae79501b8"`.
- `config/forest_plan_component_evals/` currently contains only
  `v1-cg-ecid-source-delta-review.json`.
- `src/usfs_r1_ea_sources/forest_plan_component_eval.py` still defaults tracked runs to
  `config/forest_plan_component_eval_seed.json` unless `--eval-file` is supplied explicitly.
- `config/forest_plan_component_evals/west-reservoir-67436.json` does not exist at the current
  baseline.
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json`
  exists and records the ECID current-promotion component eval as passing with `35` cases.
- `source_library/reviews/v1-cg-ecid-source-delta-review/forest_plan_component_eval_results.json`
  exists and records the ECID replay component eval as passing with `36` cases.
- `source_library/reviews/west-reservoir-67436/forest_plan_component_eval_results.json` is missing
  at the current baseline even though `docs/CURRENT_SYSTEM_STATE.md` says the West Reservoir review
  now passes package checklist, applicability validation, generated-rule-pack validation,
  forest-plan context validation, component adjudication, review-local compliance gold, and
  review-bound `phase-eval`.
- `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/` currently has
  component adjudication and green review-scoped `phase-eval`, but it still lacks both
  `forest_plan_component_eval_results.json` and a tracked review contract. Milestone 0 therefore
  routes South Plateau out of the minimum governed review set for this packet.
- Repo search confirms there is no standalone component-retrieval eval producer or config artifact:
  searches for `component_retrieval_eval`, `forest-plan-component-retrieval`, and
  `component retrieval eval` only hit the older milestone prose rather than live code or config.
- `README.md` and `docs/OUTPUT_SCHEMAS.md` currently document the default component-eval path as
  `config/forest_plan_component_eval_seed.json` plus the ECID replay contract. They do not
  document a multi-review coverage manifest or a standalone retrieval-eval producer for this lane.
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md` still explicitly says there is no
  standalone component retrieval precision/recall eval artifact and that future forests still need
  their own generated inventories and coverage.
- `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md` now exists as the immediate
  predecessor eval-coverage lane and is now resolved through local commit `a958dc8` plus
  alignment pass `59875ec`. This component milestone should reuse that roster and its covered
  profile set instead of inventing a second forest roster.

## Scope

- standalone forest-plan component-retrieval eval coverage
- review-scoped forest-plan component-eval coverage beyond the ECID current-promotion slice
- tracked component-eval contract resolution for declared review IDs
- aggregate component-eval coverage reporting
- direct-eval-aware phase-eval and promotion routing for the new component producers
- docs, current-state, and handoff alignment for component coverage semantics

## Out Of Scope

- making every Region 1 forest reviewer-ready or live-package-proven
- reopening the earlier broad NFMA implementation plan as the active milestone surface
- downloader, catalog, or broad extraction work unless Milestone 0 proves a real dependency
- staging ignored `source_library/` outputs unless repository policy changes
- weakening existing forest-plan component, adjudication, phase-eval, or promotion gates

## Owner Surfaces

- Standalone component-retrieval eval owner:
  `config/forest_plan_component_retrieval_eval_v1.json`,
  `src/usfs_r1_ea_sources/forest_plan_component_retrieval_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `tests/test_forest_plan_component_retrieval_eval.py`
- Review-scoped component-eval coverage owner:
  `config/forest_plan_component_eval_coverage_v1.json`,
  `config/forest_plan_component_eval_seed.json`,
  `config/forest_plan_component_evals/`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval.py`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py`,
  `src/usfs_r1_ea_sources/cli_review.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `tests/test_forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`
- Component artifact producer owner:
  `src/usfs_r1_ea_sources/forest_plan_components.py`,
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`,
  `tests/test_compliance_review.py`
- Direct-eval and promotion routing owner:
  `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `config/promotion_suite_v1.json`,
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_promotion_suite.py`
- Docs and routing owner:
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- Keep component-retrieval evaluation separate from final component compliance scoring. Do not fake a
  retrieval eval by re-reporting only the downstream component-eval pass/fail numbers.
- Keep review-specific component coverage in tracked config or manifest ownership, not in
  `if review_id == ...` branches.
- Do not leave the tracked multi-review component path on an implicit ECID-only default once a
  review coverage manifest exists. Either resolve the contract from tracked review coverage or fail
  closed unless `--eval-file` is provided explicitly.
- Reuse the predecessor cross-forest profile-eval roster and direct-eval routing where possible.
  Do not create a second hand-maintained forest or review roster for component coverage.
- Preserve the distinction between:
  - component-retrieval eval coverage,
  - review-scoped component compliance eval coverage,
  - reviewer-ready component adjudication closure, and
  - live-package proof.
  Closing this milestone must not blur those layers together.

## Weak-Point Prevention Contract

- Weak point forecast: the repo gains more component-eval config files, but coverage is still
  effectively ECID-only because the default path and passing live result remain tied to the East
  Crazies proving review.
  Owner surface: `config/forest_plan_component_eval_coverage_v1.json`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py`,
  `tests/test_forest_plan_component_eval_coverage.py`
  Prevention gate: the aggregate coverage contract must require the declared review set and report
  exact covered review IDs, eval IDs, source-set bindings, and result presence.
  Fail threshold: the aggregate gate passes while a required non-ECID review slot is missing or has
  no result.
  Controlled violation: remove `west-reservoir-67436` from the coverage manifest or leave its
  contract path empty; the aggregate gate must fail.
  Future-Codex misuse scenario: a later session adds another ECID replay variant and claims the
  lane is broader; duplicate-slice coverage must not count as multi-review breadth.

- Weak point forecast: component retrieval remains unmeasured, so apparent component-eval quality
  can still hide retrieval or selection misses.
  Owner surface: `config/forest_plan_component_retrieval_eval_v1.json`,
  `src/usfs_r1_ea_sources/forest_plan_component_retrieval_eval.py`,
  `tests/test_forest_plan_component_retrieval_eval.py`
  Prevention gate: the repo must have one standalone retrieval-oriented producer with explicit
  precision/recall thresholds and hard negatives.
  Fail threshold: the milestone closes with only the review-scoped component compliance eval and no
  separate retrieval artifact.
  Controlled violation: delete the retrieval-eval contract or reduce it to a placeholder file with
  no metric thresholds; focused contract tests must fail.
  Future-Codex misuse scenario: a later session points to the ECID component-eval metrics and says
  retrieval is covered; the missing standalone retrieval artifact gate must fail.

- Weak point forecast: West Reservoir or the next non-Custer review is relabeled as covered without
  its own component-eval contract.
  Owner surface: `config/forest_plan_component_evals/`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`
  Prevention gate: each declared covered review must resolve to its own contract file or adopted
  equivalent and must not silently consume the ECID seed contract.
  Fail threshold: `forest-plan-component-eval --review-id west-reservoir-67436` can pass only by
  defaulting to `config/forest_plan_component_eval_seed.json`.
  Controlled violation: run the tracked review path without an explicit West Reservoir contract and
  expect the command or coverage gate to fail.
  Future-Codex misuse scenario: a later session leaves the default ECID contract in place and only
  changes docs; the resolution tests must fail.

- Weak point forecast: the new component lane becomes a detached report and never feeds the
  direct-eval-aware readiness path.
  Owner surface: `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `config/promotion_suite_v1.json`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`
  Prevention gate: once the new producers exist, phase-eval and promotion must consume their
  summary identities, pass/fail states, and missing/stale counters for the relevant scopes.
  Fail threshold: the component coverage producer can fail while phase-eval or promotion stays green
  for the same roster or review claim.
  Controlled violation: keep phase counts green but set the component coverage summary missing or
  below floor; phase-eval and promotion tests must fail.
  Future-Codex misuse scenario: a later session updates only the standalone producer and leaves
  routing unchanged; the direct-eval and promotion checks must fail before commit.

- Weak point forecast: this milestone overclaims that all covered profiles are now
  reviewer-ready or live-package-proven.
  Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, this plan
  Prevention gate: docs and handoff updates must state exactly what the new lane proves and what it
  does not prove.
  Fail threshold: closeout docs imply all forests or all reviews are reviewer-ready because the
  component coverage lane is broader.
  Controlled violation: if docs say the broader component coverage milestone makes the full Region 1
  roster operationally proven, the milestone is not complete.
  Future-Codex misuse scenario: a later session uses eval coverage to oversell operational
  readiness; the docs closeout gate must catch the semantic drift.

## Milestone Sequence

### Milestone 0 - Post-Cross-Forest Preflight And Component-Coverage Baseline

Outcome label: reduced

Purpose: start this lane only after the predecessor cross-forest profile-eval work is truly
complete, then lock the live component-coverage baseline before code changes begin.

Implementation tasks:

1. Verify the predecessor chain exists and is green:
   - `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md` is closed and committed
   - the direct-eval-aware `phase-eval` route exists under its implemented names
   - the predecessor profile-eval lane exists under its implemented names
2. Rebaseline the current component-coverage roster from live repo artifacts:
   - existing component-eval contracts under `config/forest_plan_component_evals/`
   - existing review result files under `source_library/reviews/*/forest_plan_component_eval_results.json`
   - current active source-set IDs and review IDs for the ECID and West Reservoir lanes
   - whether South Plateau belongs in this coverage boundary now or remains explicitly routed out
3. Confirm the current missing surfaces:
   - no standalone component-retrieval eval producer
   - no West Reservoir component-eval contract
   - whether review-scoped component coverage still defaults to the ECID seed path
4. If predecessor milestone outputs or active review IDs drifted, refresh this plan, the handoff
   note, and later verification commands before Milestone 1 begins.

Acceptance criteria:

- This plan or its Milestone 0 closeout note records the exact current contract roster, current
  result roster, and whether South Plateau is in or out of scope for this milestone.
- Later milestones do not duplicate predecessor artifacts under new names.
- If the live system drifted, the plan is rewritten before implementation continues.

Verification:

```bash
git status -sb
ls -1 config/forest_plan_component_evals 2>/dev/null || true
python - <<'PY'
import json
from pathlib import Path
for path in [
    Path('source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json'),
    Path('source_library/reviews/west-reservoir-67436/forest_plan_component_eval_results.json'),
]:
    print(path, path.exists())
    if path.exists():
        obj = json.loads(path.read_text())
        print(obj.get('schema_version'), obj.get('review_id'), obj.get('passed'))
PY
rg -n "forest_plan_component_eval|component_retrieval_eval|west-reservoir-67436" README.md docs/CURRENT_SYSTEM_STATE.md docs/OUTPUT_SCHEMAS.md
```

Docs and handoff updates required before closeout:

- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 0 stop conditions:

- The predecessor cross-forest profile-eval milestone is not actually complete.
- The live review or source-set identities drifted and the plan has not been refreshed.
- The only way to proceed is to duplicate the predecessor roster or direct-eval routing by hand.

### Milestone 1 - Add The Standalone Component-Retrieval Eval Producer

Outcome label: resolved

Purpose: close the missing retrieval-eval artifact gap so component evidence quality is measured
before final component compliance scoring.

Implementation tasks:

1. Add `config/forest_plan_component_retrieval_eval_v1.json` with:
   - `schema_version`
   - `contract_id`
   - source-set binding or freshness expectations
   - fixture query cases
   - expected forest-unit IDs
   - expected component IDs or component families
   - hard negatives
   - precision/recall thresholds
2. Add `src/usfs_r1_ea_sources/forest_plan_component_retrieval_eval.py` plus a `cli_eval.py`
   entry point such as `forest-plan-component-retrieval-eval`.
3. Emit a governed retrieval-eval result artifact that reports at minimum:
   - case counts
   - hard-negative counts
   - component retrieval precision
   - component retrieval recall
   - applicable-standard component recall
   - wrong-forest component rate
4. Add focused tests proving:
   - missing required components fail recall
   - wrong-forest components fail precision
   - hard negatives remain zero-match cases when expected

Acceptance criteria:

- The repo has one explicit standalone component-retrieval eval contract and producer.
- The new producer is not a proxy summary of the downstream component compliance eval.
- Missing retrieval evidence or wrong-forest retrieval now fails a governed artifact.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_retrieval_eval.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 1 stop conditions:

- The retrieval producer can only exist as prose or as a copied metric block from the downstream
  component compliance eval.
- The only path to green is to drop hard negatives or remove precision/recall thresholds.

### Milestone 2 - Expand Review-Scoped Component Eval Coverage Beyond ECID

Outcome label: resolved

Purpose: make review-scoped component coverage explicit and multi-review instead of leaving the lane
effectively tied to one ECID default contract.

Implementation tasks:

1. Add `config/forest_plan_component_eval_coverage_v1.json` with the minimum governed review set:
   - current-promotion ECID review
   - ECID source-delta replay review
   - West Reservoir review
   - optional typed South Plateau slot only if Milestone 0 confirms it belongs in this boundary
2. Add `config/forest_plan_component_evals/west-reservoir-67436.json` with review-specific
   component cases, source-set binding, and coverage floors appropriate to the current West
   Reservoir component findings and adjudication outputs.
3. Add a focused coverage helper such as
   `src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py` that validates the declared
   review roster, contract paths, result paths, and identity matches.
4. Update `forest_plan_component_eval.py` and CLI routing so declared tracked review IDs no longer
   silently fall back to the ECID seed contract. Supported behavior must become one of:
   - resolve the contract from the tracked review coverage manifest when `--review-id` is provided;
     or
   - fail closed unless `--eval-file` is provided explicitly.
5. Add focused tests proving:
   - West Reservoir resolves to its own contract
   - declared tracked reviews do not consume the ECID default implicitly
   - missing contract paths or stale result identities fail closed

Acceptance criteria:

- The repo has a tracked review-scoped component coverage manifest and a West Reservoir contract.
- Declared tracked review IDs no longer rely on a hidden ECID-only default.
- The aggregate review roster fails when a required review slot is missing, stale, or unresolved.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_compliance_review.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id west-reservoir-67436
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 2 stop conditions:

- West Reservoir is relabeled covered without a review-specific contract.
- The only way to run tracked review coverage is to keep the ECID seed as a hidden default.

### Milestone 3 - Add The Aggregate Component-Coverage Gate And Future-Forest Routing

Outcome label: resolved

Purpose: make the broader component-eval surface one governed lane rather than a set of unrelated
contracts and live review files.

Implementation tasks:

1. Extend `src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py` or a sibling aggregate
   entry point so the repo can emit one component-coverage summary artifact with:
   - required review slot count and covered slot count
   - component-retrieval eval status
   - review-scoped component-eval coverage status
   - missing contract count
   - missing result count
   - stale identity count
   - blocked typed-slot count, if South Plateau belongs in scope after Milestone 0
2. Require the aggregate lane to fail when:
   - the standalone retrieval producer is missing or below threshold
   - a required review-scoped component-eval slot is missing
   - West Reservoir lacks a valid result or contract
   - tracked review identity drifts from contract or result
3. Make future forest expansion explicit:
   - no future non-ECID review may count as covered without its own review contract
   - future additions must land one review at a time through the coverage manifest rather than by
     broadening the claim to all forests at once
4. Add focused controlled-violation tests proving each of those failures closes the gate.

Acceptance criteria:

- The repo has one aggregate component-coverage summary.
- The lane fails closed on missing retrieval coverage, missing West Reservoir coverage, or identity
  drift.
- Future forest additions are manifest-owned one review at a time, not implied by broader prose.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_retrieval_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
git diff --check
```

Docs and handoff updates required before closeout:

- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 3 stop conditions:

- The new aggregate lane is only a report and does not actually fail on missing component coverage.
- The implementation broadens the claim to all future forests without per-review contract ownership.

### Milestone 4 - Wire The New Component Lane Into Phase-Eval, Promotion, And Coverage Docs

Outcome label: resolved

Purpose: make the new component producers part of the repo's governed readiness system instead of a
detached sidecar.

Implementation tasks:

1. Extend `config/phase_eval_direct_eval_v1.json` and the normalized loader so the standalone
   component-retrieval producer and the aggregate component-coverage producer are consumed for the
   relevant source-set and review claims.
2. Update `evidence_graph.py` / `phase_eval_direct_eval.py` so source-set or review-scoped
   `phase-eval` records the new component coverage fields, identities, and failure reasons.
3. Extend `config/promotion_suite_v1.json` so the relevant promotion-facing claims fail when the
   new component producers are missing, stale, or below floor.
4. Add or update the evaluation coverage register row for this lane and document:
   - what the standalone retrieval producer proves
   - what the review-scoped component coverage producer proves
   - what neither of them proves about reviewer-ready or live-package status by themselves
5. Update `README.md`, `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
   `docs/SESSION_HANDOFF.md` so future sessions know the component coverage lane exists and what
   remains outside its scope.

Acceptance criteria:

- The evaluation coverage register has an explicit component-coverage row.
- Phase-eval and promotion can no longer ignore a failed or stale component-coverage producer.
- Docs preserve the distinction between component eval coverage, component adjudication closure,
  reviewer-ready review status, and live-package proof.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_retrieval_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
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

- The new component producers can fail while phase-eval or promotion still stays green for the same
  claim.
- Closeout docs blur broader component coverage into reviewer-ready or live-package readiness.

## Required Implementation Artifacts

- `config/forest_plan_component_retrieval_eval_v1.json`
- `src/usfs_r1_ea_sources/forest_plan_component_retrieval_eval.py`
- `tests/test_forest_plan_component_retrieval_eval.py`
- `config/forest_plan_component_eval_coverage_v1.json`
- `config/forest_plan_component_evals/west-reservoir-67436.json`
- `src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py`
- focused updates to:
  `src/usfs_r1_ea_sources/forest_plan_component_eval.py`,
  `src/usfs_r1_ea_sources/cli_review.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `tests/test_forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `config/phase_eval_direct_eval_v1.json`,
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite.py`

## Required Documentation And Handoff Updates

- `README.md`
  document the standalone component-retrieval eval producer, the review-scoped component coverage
  manifest, and the fact that the ECID default is no longer the only governed path
- `docs/OUTPUT_SCHEMAS.md`
  define both new producer contracts and result schemas, plus any new phase-eval detail fields
- `docs/EVALUATION_COVERAGE_REGISTER.md`
  add the component-coverage row and direct-eval status
- `docs/CURRENT_SYSTEM_STATE.md`
  update the live component coverage roster and preserve what remains outside the lane
- `docs/SESSION_HANDOFF.md`
  route the next session to the first incomplete milestone and record any remaining review slots or
  blocked typed slots
- this plan with implementation status and closeout evidence

## Required Verification Gates

Minimum closeout gates for the full milestone:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_retrieval_eval.py tests/test_forest_plan_component_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_compliance_review.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id west-reservoir-67436
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

If predecessor milestones publish the needed direct-eval or profile-eval artifacts under different
commands or paths than this plan currently names, Milestone 0 must update the closeout commands in
`docs/SESSION_HANDOFF.md` before implementation continues.

## Verification And Anti-Weakening Rules

- Do not weaken tests, evals, or gates just to make broader component coverage go green. Any
  replacement coverage must be equivalent or stronger, and the closeout evidence must prove
  coverage did not get easier.
- Do not get this milestone green by relabeling a review as covered without a review-specific
  component-eval contract.
- Do not get this milestone green by pointing at ECID-only component-eval metrics and claiming the
  missing standalone retrieval-eval artifact no longer matters.
- Do not get this milestone green by blurring broader component coverage into reviewer-ready or
  live-package readiness.
- When tests, evals, or gates change, add negative or controlled-violation coverage showing the new
  lane is harder to fake, not easier to pass.

## Acceptance Criteria

- The repo has one explicit standalone component-retrieval eval contract and producer.
- The repo has one tracked multi-review component-eval coverage manifest and aggregate summary.
- West Reservoir has its own governed review-scoped component-eval contract or an adopted
  equivalent selected during Milestone 0.
- Declared tracked review IDs no longer rely on an implicit ECID-only component-eval default.
- The new component producers are wired into the direct-eval-aware phase-eval and promotion route
  where appropriate.
- No closeout may reduce any declared retrieval threshold, remove a required hard-negative family,
  or drop an existing component, phase-eval, or promotion gate just to make the new lane pass.

## Commit Policy

- Complete one local atomic commit per milestone after that milestone's verification passes.
- Stage only the verified slice for that milestone: code, tests, config, docs, and any tracked
  helper artifacts needed to explain the change.
- Do not stage ignored `source_library/` outputs unless repository policy changes.
- If a milestone reaches verified code and docs but is not yet committed, report it as
  ready-to-close, not complete.

## Stop Conditions

- The predecessor cross-forest profile-eval milestone is not actually complete.
- The only path to green is to keep an implicit ECID-only contract default or to skip the standalone
  retrieval-eval producer.
- The only path to green is to widen coverage claims without review-specific contract ownership.
- The new producers cannot be wired into phase-eval or promotion without creating a second detached
  readiness path.
