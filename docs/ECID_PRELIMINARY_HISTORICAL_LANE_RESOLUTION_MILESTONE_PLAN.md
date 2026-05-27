# ECID Preliminary Historical Lane Resolution Milestone Plan

Date: 2026-05-26

Status: Historical blocked parent packet after Sequence 1 rebaseline proving (`Sequence 0`
complete locally; live route now continues through the exact Lolo
replacement-feasibility blocker child packet`)

Owner context: This is a fresh standalone follow-on milestone plan. It starts only after
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` closed locally and committed. It owns
only the remaining strict-expansion blocker for
`region1-expansion-ecid-preliminary-ea`, which is currently typed
`selected_not_ready` under `historical_source_set_split`. It does not reopen ECID current
promotion, the South Plateau reviewer-ready expansion slot, the slot-driven promotion-suite
architecture packet, or the West Reservoir typed-blocked quarantine. If the live slot roster,
package authority, or source-set IDs drift before implementation starts, Sequence 0 must refresh
this plan before code or config changes begin.

Latest execution note on 2026-05-26:

- Sequence 0 is now implemented. The promotion-suite runtime now fails ready expansion slots
  closed when any JSON `expected_gate_artifact` proves a different `source_set_id` than the slot's
  declared contract, and focused promotion-suite tests now enforce that gate.
- Fresh Sequence 1 rebaseline proving invalidated the older closure assumptions recorded when this
  plan was opened:
  - `source-set-4fb59e9eb43045cb` is still not a viable rebuild lane under the current code. Its
    source-set `phase_eval_results.json` remains `passed=false` with `passed_phase_count=10/33`.
  - `source-set-ba8d0feae79501b8` is no longer a clean rebuild lane under current live artifacts.
    A fresh
    `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8`
    now fails with `source_set_stale=398`, `partition_gap=329`,
    `missing_candidate_decision=4`, `unresolved_authority=4`, and
    `provenance_gap=1`, so rule-pack regeneration stops before compliance review can restart.
  - The tracked governed replacement candidate
    `region1-example-lolo-tylers-kitchen-66344` is not currently ready to replace the ECID
    historical slot. At that stop-condition checkpoint its review
    `phase_eval_results.json` had only been re-read at `passed=false` with
    `passed_phase_count=19/23`; the successor blocker has since rerun it to a
    `v1-ea-eval` identity mismatch plus review `phase-eval` `12/29`, as
    recorded in the newer blocker packet.
- Current packet truth: the plan is blocked at its own stop condition. Do not flip
  `region1-real-ea-slot-1` to `ready`, do not weaken the manifest floor, and do not swap in
  another non-ready placeholder. The live successor route is now
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  which owns the dedicated blocker follow-on for rebaseline drift and
  replacement-lane readiness.
- The docs-only blocker-opening closeout that moved live routing to that
  successor landed in `8cb20fb` (`Open ECID historical blocker follow-on`).
- The successor blocker packet has since completed Milestones 1-2 by ruling
  out both a bounded historical-source-set rebuild path on `4fb...` / `ba8...`
  and any currently tracked governed replacement path under current artifacts.
  Milestone 3 is now also closed locally: fresh tracked Lolo readback showed
  that the replay context and tracked `v1-ea-eval` contract still point at
  `4fb...`, the live `v1_ea_eval_results.json` now reports `5e65...`, and
  the live review `phase-eval` remains red at `12/29` on `4fb...`. The exact
  live child route is now
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  with
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  preserved as the predecessor closeout packet.

This plan now remains as the blocked historical parent record for the
fail-closed ready-slot gate and the stop-condition evidence above. Continue
live work in
`docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
rather than resuming runtime implementation sequences here.

## Purpose

Resolve the remaining ECID preliminary-EA strict-expansion blocker truthfully.

Today the governed current-promotion lane is already green and the governed South Plateau expansion
slot is already green. The only remaining red is the historical ECID preliminary-EA slot, which is
selected but not ready because its artifact family is split across
`source-set-ba8d0feae79501b8` and `source-set-4fb59e9eb43045cb`.

This milestone exists to close that last gap by doing exactly one of these:

- rebuilding the ECID preliminary historical lane on one coherent source set; or
- replacing that governed expansion slot with a different truthful ready package slot without
  lowering the manifest contract.

This milestone is not complete until the chosen path is verified, the current docs and handoff are
updated, and one local atomic commit lands the tracked implementation slice. A verified but
uncommitted result is only ready-to-close.

## Dependency And Sequence 0 Refresh Rule

- The predecessor packet `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` is resolved
  locally and must stay closed. Do not reopen it as a runtime repair packet.
- If `config/promotion_suite_v1.json`, `docs/CURRENT_ROUTING.md`, or
  `docs/CURRENT_SYSTEM_STATE.md` no longer show the ECID preliminary slot as the only remaining
  strict-expansion blocker when work begins, Sequence 0 must refresh the baseline and narrow this
  plan before implementation continues.
- If a tracked replay context, adjudication file, or replacement review contract already lands
  under a different name before implementation starts, Sequence 0 must adopt that artifact instead
  of recreating the same ownership under new names.
- If the lane cannot be rebuilt on one coherent source set and no truthful replacement slot is
  available without reducing the governed slot floor, stop and route the remaining weakness as a
  new blocker rather than weakening the manifest in place.

## Current Evidence

- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the top of
  `docs/SESSION_HANDOFF.md` all agree that the live next slice is no longer inside the resolved
  replay-repair packet; the remaining work is now the standalone blocker
  follow-on for the ECID preliminary historical lane.
- `config/promotion_suite_v1.json` currently declares review case
  `region1-expansion-ecid-preliminary-ea` plus expansion slot `region1-real-ea-slot-1` with:
  - `status="selected_not_ready"`
  - `failure_category="historical_source_set_split"`
  - `source_set_id="source-set-4fb59e9eb43045cb"`
  - `next_action="Keep this historical ECID expansion slot selected but not ready until a fresh
    follow-on rebuilds the lane on one coherent source set or formally replaces the split
    historical contract."`
  - `acceptance_signal="The preliminary-EA slot may return to ready only after applicability,
    generated rule-pack, phase-eval, and downstream compliance/provenance artifacts all agree on
    one historical source set."`
- The slot's current `last_local_signal` records the exact split:
  - applicability validation and phase eval still bind to
    `source-set-ba8d0feae79501b8`
  - generated rule-pack validation and slot identity still bind to
    `source-set-4fb59e9eb43045cb`
  - the six absent downstream artifacts are
    `compliance_validation`,
    `compliance_review`,
    `compliance_matrix`,
    `compliance_matrix_pdf`,
    `authority_family_provenance`, and
    `non_applicable_authority_appendix`
- The same slot still expects these expansion artifact owners:
  `package_manifest`,
  `applicability_validation`,
  `generated_rule_pack_validation`,
  `compliance_validation`,
  `compliance_review`,
  `compliance_matrix`,
  `compliance_matrix_pdf`,
  `authority_family_provenance`,
  `non_applicable_authority_appendix`,
  `forest_plan_component_adjudication_template`,
  `forest_plan_component_adjudication_eval`, and
  `phase_eval`.
- Non-strict aggregate truth is already green:
  `real-package-review-coverage-eval` reports `passed=true`,
  `reviewer_ready_slot_count=2`, and `missing_required_slot_count=0`; non-strict
  `promotion-suite` reports `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `open_expansion_slot_count=1`, `open_expansion_artifact_count=0`, and
  `expansion_failure_category_counts={"historical_source_set_split":1}`.
- Strict expansion still fails closed only on that slot:
  `failure_category_counts={"historical_source_set_split":1}`,
  `open_expansion_slot_count=1`, and `open_expansion_artifact_count=0`.
- `config/replay_contexts/` currently has no tracked replay-context file for
  `region1-expansion-ecid-preliminary-ea`, so package identity for this lane still lives primarily
  in `config/promotion_suite_v1.json` plus ignored local review outputs. If the rebuild path is
  chosen, Sequence 0 must decide whether that identity needs a stronger tracked owner.

## Goal

Return the live post-V1 strict-expansion contract to truthful green without regressing the already
green current-promotion lane.

Completion means all of the following are true:

- the ECID preliminary historical issue is closed either by a coherent one-source-set rebuild or by
  a governed ready-slot replacement;
- strict-expansion `promotion-suite` passes with `expansion_ready=true`,
  `open_expansion_slot_count=0`, and `open_expansion_artifact_count=0`;
- non-strict `promotion-suite` remains `current_promotion_ready=true` and `promotion_ready=true`;
- `real-package-review-coverage-eval` remains green for the governed slot roster; and
- the current docs, handoff, and predecessor plan all name the exact committed resolution.

## Non-Goals

- Do not reopen ECID current-promotion replay or South Plateau reviewer-ready repair work unless a
  change here directly breaks those already-green lanes.
- Do not lower required expansion slot counts, weaken quorum rules, make the slot optional, or
  relax failure categories just to make strict expansion green.
- Do not treat a different selected-not-ready placeholder as a valid replacement. The chosen
  replacement path must end with a truthful ready slot.
- Do not rerun downloader, catalog, or full-canonical corpus workflows unless a focused
  review-local replay proves they are strictly required.
- Do not stage ignored `source_library/` outputs unless repository policy changes or the user
  explicitly expands scope.
- Do not widen this packet into architecture refactors, forest-profile backlog, or unrelated
  example-package promotion.

## Scope

- the review case `region1-expansion-ecid-preliminary-ea`
- expansion slot `region1-real-ea-slot-1` and any truthful replacement slot selected in its place
- the slot's package authority, source-set identity, and required expansion artifact contract
- focused review-local replay commands needed to prove or disprove one-source-set rebuild viability
- aggregate manifest, tests, and docs needed to close strict expansion truthfully

## Out Of Scope

- redesigning slot-driven promotion-suite architecture
- reducing the number of declared real-package expansion slots
- changing West Reservoir's typed-blocked semantics
- broad source-truth rebinds unrelated to the chosen historical source set or replacement slot
- global review/compliance refactors outside the surfaces needed to close this lane

## Owner Surfaces

- slot and review-case contract:
  `config/promotion_suite_v1.json`
- aggregate review-slot roster if replacement path changes the governed review set:
  `config/v1_real_package_review_coverage_v1.json`
- tracked identity surfaces if rebuild or replacement requires stronger package ownership:
  `config/replay_contexts/`,
  `config/applicability_adjudications/`,
  `config/forest_plan_component_adjudications/`,
  and any per-review contract files added under `config/`
- aggregate runtime owners:
  `src/usfs_r1_ea_sources/promotion_suite.py`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  and the CLI entrypoints they expose
- review-local replay owners used only if the rebuild path is supportable:
  the artifact producers behind
  `applicability-validate`,
  `applicability-generate-rule-pack`,
  `compliance-review`,
  `forest-plan-component-adjudication-eval`, and
  `phase-eval`
- local ignored review artifacts:
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/`
- current package authority path recorded in the slot contract:
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)/Preliminary Environmental Assessment`
- focused tests:
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_expansion_slots.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_cli_eval.py`,
  and any review-local focused tests touched by the chosen path
- docs and routing:
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  and this plan

## Placement Rules

- Keep slot roster semantics in tracked manifests and focused tests. Do not hide the resolution in
  special-case code branches with no manifest ownership.
- If the rebuild path needs stronger package identity than the current slot stanza provides, add a
  tracked replay-context or equivalent config owner under `config/` instead of relying on
  `source_library/` path guessing.
- If the replacement path is chosen, the new slot must be equivalent or stronger at the governed
  manifest level: same required slot floor, explicit package authority, explicit source set,
  explicit expected gate artifacts, and focused tests.
- Do not modify the ECID current-promotion slot or South Plateau slot unless a prevention gate
  proves the chosen change would otherwise reopen them.
- Keep ignored generated review outputs under `source_library/`; commit only tracked config, code,
  tests, and docs that govern the chosen path.
- Keep the chosen historical source-set ID or replacement review ID visible in tracked config,
  tests, and docs. Do not leave it only in chat or handoff prose.

## Weak-Point Prevention Contract

- Weak point forecast: a later session flips the ECID preliminary slot back to `ready` while the
  artifact family is still split between `ba8...` and `4fb...`.
  Owner surface: `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_expansion_slots.py`
  Prevention gate: focused slot-contract tests plus strict-expansion `promotion-suite` must fail if
  a ready slot keeps mismatched source-set IDs, missing required expansion artifacts, or a leftover
  `failure_category`.
  Fail threshold: `region1-real-ea-slot-1` or its replacement is `ready` while any required
  artifact still points at a different source set or remains absent.
  Controlled violation: set the slot to `ready` without rebuilding the split artifact family; the
  tests and strict gate must fail.
  Future-Codex misuse scenario: an agent edits only the manifest status field to get green; the
  focused slot tests must catch it.

- Weak point forecast: the chosen repair reopens ECID current promotion or the South Plateau slot
  while trying to clear the historical lane.
  Owner surface: `config/v1_real_package_review_coverage_v1.json`,
  `config/promotion_suite_v1.json`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`
  Prevention gate: non-strict `promotion-suite` and `real-package-review-coverage-eval` must stay
  green throughout the packet; run ECID current-promotion and South Plateau focused replay checks if
  manifest or aggregate-runtime surfaces move.
  Fail threshold: `current_promotion_ready` flips false, reviewer-ready slot coverage drops below
  `2`, or South Plateau stops reporting `reviewer_ready`.
  Controlled violation: change slot-count or source-set routing for ECID current or South; the
  aggregate gates must fail.
  Future-Codex misuse scenario: an agent "fixes" strict expansion by loosening shared aggregate
  logic; the current-promotion and coverage gates must catch the regression.

- Weak point forecast: the replacement path quietly weakens the governed roster by removing the
  troublesome slot, lowering counts, or accepting another blocked placeholder.
  Owner surface: `config/promotion_suite_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `tests/test_promotion_suite.py`,
  `tests/test_real_package_review_coverage_eval.py`
  Prevention gate: manifest validation and focused tests must prove the same required slot floor
  remains in place and that any replacement slot is ready, explicit, and package-authority-backed.
  Fail threshold: required expansion slot count drops, the slot becomes optional, or the
  replacement ends in any non-ready state.
  Controlled violation: delete the selected slot or downgrade it to informational-only; the tests
  and strict aggregate gate must fail.
  Future-Codex misuse scenario: an agent routes the issue away by shrinking the manifest; the slot
  floor assertions must stop that.

- Weak point forecast: the rebuild path depends on untracked local-only package or adjudication
  identity, so later reruns cannot reproduce the result.
  Owner surface: `config/replay_contexts/`,
  `config/applicability_adjudications/`,
  `config/forest_plan_component_adjudications/`,
  and `config/promotion_suite_v1.json`
  Prevention gate: the chosen path must have one tracked identity owner for package path,
  adjudication file, and review contract rather than relying on untracked operator memory.
  Fail threshold: the committed route still requires a hand-entered local path or unstated
  adjudication file outside tracked config to reproduce the ready slot.
  Controlled violation: rename the current local intake path or omit the adjudication file from the
  tracked route; the review-local replay or focused tests must fail.
  Future-Codex misuse scenario: an agent copies a local artifact family but forgets the tracked
  contract surface; the identity gate must catch it.

- Weak point forecast: the plan lands, but the current-route docs still tell future sessions only
  to "open a follow-on" instead of naming the exact packet.
  Owner surface: `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`
  Prevention gate: the live routing docs must point to this plan by exact filename until the packet
  resolves.
  Fail threshold: a current-facing doc leaves the next packet generic or still points at the
  resolved replay-repair packet as the active runtime slice.
  Controlled violation: leave one current-facing doc on the generic follow-on wording; doc review
  and `git diff --check` do not complete the milestone.
  Future-Codex misuse scenario: an agent starts in the wrong packet and reopens closed work; the
  doc-routing set must make that mistake obvious.

## Milestone Sequence

### Sequence 0 - Rebaseline And Resolution-Path Lock

Outcome label: reduced

Purpose: refresh the live slot baseline, lock the current source-set and package-authority truth,
and install the first fail-closed gates before broader implementation.

Implementation:

1. Re-read `docs/CURRENT_ROUTING.md`, the top of `docs/SESSION_HANDOFF.md`,
   `docs/CURRENT_SYSTEM_STATE.md`, and `config/promotion_suite_v1.json`, then update this plan if
   the blocker count, source-set IDs, expected artifact roster, or package path drift.
2. Inventory the current ECID preliminary artifact family and identify which owners already exist in
   tracked config versus only in ignored `source_library/`.
3. Add or strengthen focused tests so a slot cannot move to `ready` unless one coherent source set
   owns applicability validation, generated rule-pack validation, downstream compliance/provenance,
   forest-plan adjudication, and phase-eval; and so a replacement slot cannot land by lowering the
   governed floor.

Acceptance criteria:

- The plan and route docs are refreshed if any live baseline drift is discovered.
- Focused tests fail if a split-source-set ready slot or a weakened replacement manifest is
  introduced.
- The packet leaves Sequence 0 with one explicit next branch: `Sequence 1` viability proving.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_expansion_slots.py \
  tests/test_real_package_review_coverage_eval.py -q

git diff --check
```

### Sequence 1 - Historical-Lane Viability Proving

Outcome label: reduced

Purpose: prove whether the ECID preliminary lane can be rebuilt truthfully on one historical source
set, or whether the packet must move to governed slot replacement.

Implementation:

1. Run focused review-local validations against each candidate historical source set:
   `source-set-ba8d0feae79501b8` and `source-set-4fb59e9eb43045cb`.
2. For each candidate, prove or disprove whether the full review-local chain can align:
   applicability validation, generated rule-pack validation, forest-plan component adjudication
   eval, downstream compliance/provenance artifacts, and phase-eval.
3. Record the result in tracked docs:
   - if one candidate can carry the full chain, lock it as `<chosen_historical_source_set_id>` and
     continue to Sequence 2;
   - if neither candidate can carry the chain truthfully, record that failure explicitly and
     continue to Sequence 3.

Acceptance criteria:

- The packet exits Sequence 1 with exactly one committed truth:
  either a chosen coherent historical source set, or an explicit committed finding that the rebuild
  path is not supportable.
- No aggregate current-promotion or governed reviewer-ready slot signal regresses during proving.
- The chosen next branch is visible in tracked docs and not left implicit in operator memory.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <candidate_source_set_id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <candidate_source_set_id>

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --adjudication-file <tracked_or_local_adjudication_file>

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)/Preliminary Environmental Assessment" \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <candidate_source_set_id> \
  --rule-pack source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/generated_rule_pack.json \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

### Sequence 2 - Coherent Historical-Lane Rebuild

Outcome label: resolved

Purpose: execute the historical rebuild path if Sequence 1 proves one source set can own the full
lane truthfully.

Implementation:

1. Add or adopt any tracked replay-context, adjudication, or per-review config owner that is
   required to make the chosen lane reproducible.
2. Rebuild the full required artifact family for
   `region1-expansion-ecid-preliminary-ea` on `<chosen_historical_source_set_id>`:
   `applicability_validation`,
   `generated_rule_pack_validation`,
   `compliance_validation`,
   `compliance_review`,
   `compliance_matrix`,
   `compliance_matrix_pdf`,
   `authority_family_provenance`,
   `non_applicable_authority_appendix`,
   `forest_plan_component_adjudication_template`,
   `forest_plan_component_adjudication_eval`, and
   `phase_eval`.
3. Update `config/promotion_suite_v1.json` and focused tests so the review case and expansion slot
   all point at the same chosen source set and ready-state expectations.

Acceptance criteria:

- `region1-real-ea-slot-1` returns to `status="ready"` with no `failure_category`.
- Every required expansion artifact for the slot exists and proves the same chosen source set.
- Strict expansion passes without lowering any governed slot or quorum rule.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <chosen_historical_source_set_id>

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <chosen_historical_source_set_id>

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --adjudication-file <tracked_adjudication_file>

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)/Preliminary Environmental Assessment" \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <chosen_historical_source_set_id> \
  --rule-pack source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/generated_rule_pack.json \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion
```

### Sequence 3 - Governed Ready-Slot Replacement

Outcome label: resolved

Purpose: execute the replacement path if Sequence 1 proves the historical split lane cannot be
rebuilt truthfully on one source set.

Implementation:

1. Select a replacement real-package expansion review with durable package authority, reproducible
   review-local artifacts, and a viable ready-state path. Do not reuse ECID current promotion or
   West Reservoir typed-blocked coverage as the replacement.
2. Add the tracked config owners the replacement needs:
   review contract, package authority, replay context if required, and slot manifest stanza with
   explicit expected gate artifacts.
3. Update `config/promotion_suite_v1.json`, any supporting coverage manifest, and focused tests so
   the historical ECID preliminary lane is retired from the selected expansion roster and replaced
   by a truthful ready slot of equal or stronger governed value.

Acceptance criteria:

- Strict expansion passes without reducing the required expansion slot floor.
- The replacement slot is `ready`, package-authority-backed, source-set-explicit, and fully
  validated by focused tests.
- The historical ECID preliminary lane no longer appears as the selected current blocker.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id <replacement_review_id>
```

### Sequence 4 - Aggregate Strict-Expansion Closeout

Outcome label: resolved

Purpose: prove the live production-facing contract after the chosen path lands, then close the
packet with aligned docs and one atomic commit.

Implementation:

1. Re-run the aggregate governed coverage and both promotion-suite modes.
2. Update the live routing docs, handoff, post-V1 promotion doc, and predecessor packet with the
   exact committed outcome, commands, and residual risks.
3. Stage only the verified tracked slice and create one local atomic commit.

Acceptance criteria:

- `real-package-review-coverage-eval` passes with no reviewer-ready slot mismatch.
- Non-strict `promotion-suite` remains `current_promotion_ready=true` and `promotion_ready=true`.
- Strict-expansion `promotion-suite` passes with `expansion_ready=true`,
  `open_expansion_slot_count=0`, `open_expansion_artifact_count=0`, and no
  `historical_source_set_split` failure category.
- The current docs point to the next real packet, or explicitly say none remains if this lane is
  fully closed.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_expansion_slots.py \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_cli_eval.py -q

git diff --check
```

## Required Implementation Artifacts

- one committed resolution choice:
  coherent historical rebuild or governed ready-slot replacement
- tracked config updates that make the chosen path reproducible
- focused tests that fail closed on split-source-set ready slots or weakened replacement manifests
- aligned current docs and handoff that record the exact final strict-expansion truth

## Required Documentation And Handoff Updates

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- this plan
- `README.md` only if the public command guidance or route summary changes materially

## Required Verification Gates

- `real-package-review-coverage-eval`
- non-strict `promotion-suite`
- strict-expansion `promotion-suite`
- focused slot-contract tests in
  `tests/test_promotion_suite.py` and `tests/test_promotion_suite_expansion_slots.py`
- if the rebuild path executes:
  `applicability-validate`,
  `applicability-generate-rule-pack`,
  `forest-plan-component-adjudication-eval`,
  `compliance-review`, and
  `phase-eval`
- if the replacement path executes:
  the replacement review's declared per-review artifact gates plus focused manifest tests
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py -q` if the chosen
  path introduces new modules, CLI registration, or dependency-boundary changes
- `git diff --check`

## Acceptance Criteria

- There is no longer a selected ECID preliminary slot blocked on
  `historical_source_set_split`.
- The final strict-expansion result is green without lowering the manifest contract.
- The already-green ECID current-promotion lane and South Plateau reviewer-ready lane remain green.
- The chosen path is reproducible from tracked config, code, tests, and named commands rather than
  operator memory.
- The committed docs tell a future session exactly what resolved the lane and where to continue next
  if anything still remains open.

## Stop Conditions

- Stop if neither historical source set can carry a truthful rebuild and no ready replacement slot
  can be introduced without reducing the governed slot floor.
- Stop if the only apparent way to pass strict expansion is to delete the slot, weaken tests,
  lower counts, or reclassify blocked lanes as ready.
- Stop if the required tracked identity surface for the chosen path cannot be separated cleanly from
  unrelated dirty worktree changes.
- Stop if the chosen path requires broad downloader, catalog, or full-canonical corpus reruns that
  exceed this packet's narrow review-local boundary.

## Local Commit Closeout Policy

- Stage only the verified tracked slice for this packet.
- Leave unrelated dirty or untracked files alone.
- Keep ignored `source_library/` evidence local unless repository policy changes.
- Include the chosen config, code, tests, docs, and handoff updates in the same commit.
- Record the commit hash and exact verification bundle in `docs/SESSION_HANDOFF.md`.
- Treat the packet as incomplete until the local commit exists.

## Residual Risks And Next Milestone Routing

- If Sequence 1 proves the historical lane is unrebuildable and no ready replacement exists, route
  the remaining issue into a new blocker packet focused on package identity or source-truth
  feasibility. Do not reopen the resolved replay-repair parent packet.
- If the lane closes through a ready replacement slot, any later work specific to that replacement
  review belongs in its own review-local packet rather than in this generic resolution packet.
- Once this packet resolves, the next live work should return to whatever packet
  `docs/CURRENT_ROUTING.md` names at that time rather than reviving this lane.

## Closeout Checklist

- [ ] Sequence 0 refreshed the live baseline and installed fail-closed slot tests.
- [ ] Sequence 1 proved either coherent rebuild viability or rebuild impossibility.
- [ ] Exactly one resolution path executed: Sequence 2 rebuild or Sequence 3 replacement.
- [ ] `real-package-review-coverage-eval`, non-strict `promotion-suite`, and strict-expansion
      `promotion-suite` all passed.
- [ ] Current docs, handoff, and the predecessor packet record the exact committed outcome.
- [ ] The verified tracked slice was committed atomically.
