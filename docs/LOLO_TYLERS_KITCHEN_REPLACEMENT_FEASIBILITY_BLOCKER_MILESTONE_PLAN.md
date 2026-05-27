# Lolo Tyler's Kitchen Replacement Feasibility Blocker Milestone Plan

Date: 2026-05-26

Status: Historical reduced predecessor packet (`Milestone 1 is now reduced
locally; the remaining tracked blocker no longer has one coherent owner here,
and live work now routes through
docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`)

Owner context: standalone follow-on opened after
`docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
completed exact child-route closeout and proved that no bounded historical
source-set rebuild path remains for the ECID preliminary historical slot and
no tracked governed replacement is currently proven. This packet is now the
historical predecessor that narrowed the remaining review-local replacement
debt for `region1-example-lolo-tylers-kitchen-66344` into the stricter
source-set contract blocker. It does not reopen the broader Lolo
package-authority packet, change the ECID manifest floor, scout new
replacement candidates, or claim a ready slot before its own gates pass.

Opening closeout commit:
`6a4e87d` (`Open Lolo replacement feasibility blocker`)

## Latest Local Implementation

- Milestone 1 is now reduced locally. Fresh tracked readback proved that this
  packet no longer owns one coherent replacement-feasibility path.
- `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  and `config/v1_lolo_tylers_kitchen_real_ea_eval.json` still bind the review
  to `source-set-4fb59e9eb43045cb`, while the live
  `v1_ea_eval_results.json` reports
  `source-set-5e65d845ce77e1a0` with
  `contract_status="mismatch"`, representative review-local artifacts also
  report `5e65...`, `applicability/generated_rule_pack_validation.json` still
  reports `4fb...`, and review `phase_eval_results.json` remains red at
  `12/29` on `4fb...`. `downstream_direct_evaluation` also still depends on
  stale `compliance_review_eval` coverage on `source-set-f70ea11e04ae3d53`.
- The exact next owner is now
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`.
- This packet now remains as the exact predecessor that reduced the broader
  replacement-feasibility lane into the narrower source-set contract blocker.

## Purpose

Determine whether the tracked Lolo Tyler's Kitchen review can become the exact
governed replacement path for the ECID preliminary historical slot under one
coherent source-set contract, or whether the remaining debt belongs to a
narrower blocker owner.

Freshness check rule:
before any runtime proving begins, re-read `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, the top of `docs/SESSION_HANDOFF.md`,
`config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
`config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
`config/promotion_suite_v1.json`,
`config/v1_real_package_review_coverage_v1.json`, and the live
`source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
`v1_ea_eval_results.json` plus `phase_eval_results.json`. If the tracked
source-set IDs, phase counts, or governed roster membership drift, update this
packet and the current-routing docs before implementation continues.

## Current Evidence

- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the top of
  `docs/SESSION_HANDOFF.md` now route the remaining tracked replacement work
  here, with
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  preserved as the exact predecessor closeout and
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` preserved as
  the broader package-authority and registry parent record only.
- The tracked replay context
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  still declares `source_set_id="source-set-4fb59e9eb43045cb"` and the local
  package path `source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344`.
- The tracked review contract
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json` also still declares
  `source_set_id="source-set-4fb59e9eb43045cb"`.
- The live review result
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
  now reports `source_set_id="source-set-5e65d845ce77e1a0"`,
  `contract_status="mismatch"`, `passed=false`, and one failing check:
  `review_identity_matches_contract`, with the contract still on `4fb...`
  while the live review artifact reports `5e65...`.
- The live review phase result
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
  still reports `source_set_id="source-set-4fb59e9eb43045cb"`,
  `passed=false`, `passed_phase_count=12/29`,
  `missing_direct_eval_phase_count=3`, and failing phases spanning
  `retrieval`, `claim_extraction`, `rule_claim_binding`,
  `downstream_direct_evaluation`, `source_register_contract`,
  `authority_ontology`, `authority_relationships`, `citation_aliases`,
  `graph_health`, `graph_accuracy`, `authority_universe`,
  `package_fact_graph`, `applicability_validation`, `compliance_review`,
  `forest_plan_component_eval`, `forest_plan_component_adjudication`, and
  `evaluation_coverage`.
- The governed aggregates remain stable and still do not admit the tracked
  Lolo review as a ready replacement: fresh coverage and promotion routing
  continue to admit only East Crazies, West Reservoir, and South Plateau, and
  the ECID historical slot remains the only open strict-expansion blocker
  under `historical_source_set_split`.
- The broader Lolo example packet's older local claim that
  `v1-ea-eval` was green and `phase-eval` was inherited-red on `5e65...` is
  now historical-only context. Current tracked evidence must be read from the
  files above rather than that older packet-local checkpoint.

## Goal

Leave the repository with one exact bounded next owner for the tracked Lolo
replacement path:

- either one coherent review contract and source-set alignment path that can
  be executed without weakening the governed slot floor; or
- one explicit narrower feasibility blocker that owns the remaining debt.

Completion means all of the following are true:

- tracked docs no longer blur the remaining replacement blocker into the
  broader historical ECID packet or the broader Lolo example packet;
- one coherent source-set owner is either identified or explicitly rejected;
- no governed roster, slot-floor, or ready-state contract is weakened; and
- the next owner after this packet, or the narrower feasibility stop, is
  named explicitly in tracked docs and handoff.

## Non-Goals

- Do not flip the ECID historical slot to `ready`, delete it, or lower the
  governed expansion floor.
- Do not admit the tracked Lolo review into
  `config/v1_real_package_review_coverage_v1.json` or
  `config/promotion_suite_v1.json` while `v1-ea-eval` or `phase-eval` remain
  red.
- Do not reopen broad package intake, `FOR-029` queue reroute, or forest
  registry promotion work from
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
- Do not manually patch generated `source_library/` JSON to force contract
  agreement.
- Do not scout new replacement candidates in this packet.

## Scope

- the tracked replacement candidate
  `region1-example-lolo-tylers-kitchen-66344`
- review contract, replay context, and source-set identity for that review
- review-scoped `phase-eval` and its failing direct-eval or review-local
  families only as needed to classify bounded feasibility
- current-routing and packet-lineage docs for the exact live blocker route

## Out Of Scope

- package-authority intake or byte refresh for Tyler's Kitchen
- forest-specific registry promotion for `lolo-nf`
- ECID slot semantics, manifest-floor redesign, or current-promotion reroute
- broad full-canonical source-set rebuilds or open-ended candidate scouting
- unrelated Lolo queue, Pinyon, or forest-profile backlog work

## Owner Surfaces

- live blocker docs:
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`
- historical lineage docs:
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- tracked review identity surfaces:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/forest_plan_component_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
- live ignored review outputs:
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
- aggregate governed contracts:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/promotion_suite_v1.json`
- command owners and focused tests if code or contract changes become
  necessary:
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_phase_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`,
  `tests/test_cli_eval.py`

## Placement Rules

- Keep broader Tyler's Kitchen package-authority, queue-boundary, and forest
  registry history in
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`. Do not resume
  live runtime work there while this blocker remains active.
- Keep source-set owner truth declarative in tracked config and eval-contract
  surfaces. Do not hide it in ad hoc runtime branches or manual result edits.
- Keep the governed roster and slot floor unchanged until the tracked Lolo
  review is actually reviewer-ready under one coherent source set.
- If the replacement path splits into a source-set contract owner and a
  review-readiness owner, open the narrower child packet before making code or
  manifest changes.
- Keep generated review evidence local under `source_library/`; commit only
  tracked docs, config, code, and tests.

## Weak-Point Prevention Contract

- Weak point forecast: a future session treats the broader Lolo example packet
  as the live owner again and resumes stale `5e65...` assumptions.
  Owner surface: `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  Prevention gate: the current-facing docs must point here by exact filename
  and preserve the broader Lolo plan only as historical package-authority and
  registry context.
  Fail threshold: any current-facing doc still presents the broader Lolo plan
  as the next runtime packet.
  Controlled violation: leave one current-facing doc on the older
  `phase-eval`-on-`5e65...` story; readback review does not complete the
  milestone.
  Future-Codex misuse scenario: an agent opens the broader packet and assumes
  the only remaining work is generic Milestone 3 promotion; the route docs
  must make that mistake obvious.

- Weak point forecast: a future session patches only one tracked identity
  surface and leaves the review split across `4fb...` and `5e65...`.
  Owner surface:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`, and the live review
  outputs
  Prevention gate: Milestone 1 must read the replay context, the eval
  contract, the live `v1_ea_eval_results.json`, and the live
  `phase_eval_results.json` together before declaring a bounded path.
  Fail threshold: a later slice claims coherent review identity while those
  surfaces still disagree on `source_set_id`.
  Controlled violation: change only the eval contract or only the replay
  context while live results still disagree; contract readback must reject the
  path.
  Future-Codex misuse scenario: an agent edits whichever file made the last
  command red without checking the whole owner chain; this packet forces
  end-to-end source-set readback first.

- Weak point forecast: the ECID historical slot gets "repaired" by admitting
  Lolo into the governed roster while `phase-eval` is still red.
  Owner surface: `config/v1_real_package_review_coverage_v1.json`,
  `config/promotion_suite_v1.json`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`
  Prevention gate: any later child packet that changes roster or slot surfaces
  must keep non-strict `promotion-suite` green, strict expansion fail-closed
  until the replacement is truly ready, and the governed slot floor unchanged.
  Fail threshold: the tracked Lolo review is admitted while
  `phase-eval` remains red or while `v1-ea-eval` still reports
  `contract_status="mismatch"`.
  Controlled violation: add the Lolo review to the governed roster before the
  review stack is reviewer-ready; focused tests and aggregate evals must fail.
  Future-Codex misuse scenario: an agent tries to prove progress by editing
  the roster first; the aggregate gates must stop that shortcut.

## Milestone Sequence

### Milestone 1 - Contract And Review-Identity Classification

Outcome label: reduced

Purpose: determine whether one coherent tracked source-set owner can bound the
Lolo review, or whether the identity split already belongs to a narrower
source-set contract blocker.

Implementation:

1. Re-read the tracked replay context, the tracked `v1-ea-eval` contract, the
   live `v1_ea_eval_results.json`, and the live `phase_eval_results.json`.
2. Determine whether `source-set-4fb59e9eb43045cb` or
   `source-set-5e65d845ce77e1a0` is the truthful governed owner for the
   tracked review, or whether the split itself now requires a narrower source
   contract blocker outside this packet.
3. If a bounded alignment path exists, record the exact owner surfaces and
   continue to Milestone 2. If not, open
   `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
   and route this packet to it.

Acceptance criteria:

- The packet exits Milestone 1 with one exact contract-identity conclusion,
  not mixed assumptions.
- No governed roster or slot changes land during this classification step.
- The tracked docs record the exact source-set owner surfaces for the next
  slice.

Verification:

```bash
jq '{review_id, source_set_id, package_path, catalog_dir, source_manifest_path}' \
  config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json

jq '{review_id, source_set_id, package_path, required_review_artifact_ids, expected_summary}' \
  config/v1_lolo_tylers_kitchen_real_ea_eval.json

jq '{review_id: .summary.review_id, source_set_id: .summary.source_set_id, passed: .summary.passed, contract_status: .summary.contract_status, failed_checks: [.summary.checks[] | select(.passed == false) | {name, details}]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json

jq '{review_id, source_set_id, passed, passed_phase_count, phase_count, reviewer_ready, missing_direct_eval_phase_count, threshold_failed_phase_count, failed_phase_names: [.phases[] | select(.passed == false) | .name]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json
```

### Milestone 2 - Source-Set Aligned Review-Readiness Classification

Outcome label: reduced

Purpose: on one coherent source-set owner, determine whether the remaining red
is bounded review-local work or broader corpus/runtime debt.

Implementation:

1. Rebaseline the tracked review on the source-set owner chosen in Milestone 1
   without widening into open-ended candidate scouting.
2. Require explicit owner explanations for the remaining `phase-eval`
   failures, especially direct-eval gaps and review-local downstream phases,
   before calling the replacement path supportable.
3. If the remaining work is bounded and review-local, continue to Milestone 3.
   If not, open the exact narrower blocker that owns the remaining debt rather
   than broadening this packet.

Acceptance criteria:

- The packet exits Milestone 2 with one exact classification of the remaining
  red phases.
- No candidate is treated as reviewer-ready while `phase-eval` remains red.
- The governed slot floor remains unchanged.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

### Milestone 3 - Exact Child-Route Or Feasibility-Stop Closeout

Outcome label: resolved

Purpose: leave the tracked Lolo replacement lane with one exact next owner,
then close this blocker packet truthfully.

Implementation:

1. Update the current docs, handoff, and this plan with the exact child packet
   chosen in Milestone 1 or Milestone 2, or with the exact narrower
   feasibility blocker if the candidate still is not supportable.
2. Preserve the ECID blocker and the broader Lolo example packet as historical
   lineage only.
3. Stage only the verified tracked docs and any child-packet file created in
   this closeout, then create one atomic local commit.

Acceptance criteria:

- Current-facing docs no longer leave the next owner generic.
- The blocker either routes to one named child packet or records one explicit
  feasibility stop condition.
- The handoff records the exact verification bundle.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

## Required Implementation Artifacts

- this blocker plan
- exact current-facing routing to this packet
- preserved ECID blocker and broader Lolo example packet lineage
- one named child packet or one narrower feasibility blocker before this
  packet closes

## Required Documentation And Handoff Updates

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- this plan

## Required Verification Gates

- plan lint for any touched milestone plan docs
- `git diff --check`
- if Milestone 1 executes live proving:
  the tracked replay-context and review-contract readbacks plus the live
  `v1_ea_eval_results.json` and `phase_eval_results.json`
- if Milestone 2 executes live proving:
  the tracked replacement review's `v1-ea-eval`, `phase-eval`,
  `real-package-review-coverage-eval`, and non-strict `promotion-suite`
- if any later child packet changes roster, manifest, or runtime surfaces:
  focused `promotion-suite`, coverage, and review-stack tests plus the repo's
  stricter gates for the touched surface

## Acceptance Criteria

- The repository no longer routes future sessions to a generic replacement
  blocker or to the broader Lolo example packet as live runtime work.
- The tracked Lolo review's contract and live source-set split are frozen in
  tracked docs and tied to an exact next owner decision.
- The governed expansion slot floor and fail-closed slot contract remain
  unchanged while routing the blocker.
- The next packet after this blocker, or the narrower feasibility stop, is
  named explicitly in tracked docs and handoff.

## Stop Conditions

- Stop if the only apparent way forward is to admit Lolo into the governed
  roster before `phase-eval` and `v1-ea-eval` both close green.
- Stop if the tracked review identity split requires broad downloader,
  catalog, or full-canonical work outside a narrow review-local boundary.
- Stop if the remaining review-red phases depend on broad unrelated runtime
  work and no narrower owner can be named.
- Stop if no exact child packet can be named from current evidence; in that
  case, open the narrower feasibility blocker rather than broadening this
  packet.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked
  complete, `resolved`, or `reduced` until verification passes, durable
  docs/handoff updates land, and the local atomic commit exists. A verified
  but uncommitted slice is only ready-to-close.
- Stage only the verified tracked slice for this blocker packet.
- Leave unrelated dirty or untracked files alone.
- Keep ignored `source_library/` evidence local.
- Include this blocker plan, the touched routing docs, and any named child
  packet opened during closeout in the same commit.
- Record the commit hash and exact verification bundle in
  `docs/SESSION_HANDOFF.md`.
- Preserve anti-test-weakening rules: do not weaken or loosen gates, skip
  checks, or lower the governed slot floor to make replacement routing look
  green.

## Residual Risks And Next Milestone Routing

- If Milestone 1 finds that the tracked review identity cannot be reconciled
  within a bounded review-local owner chain, the next live work should move to
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`.
- If Milestone 2 finds one coherent source-set owner but the remaining
  red phases still span broad runtime debt, the next live work should open the
  exact narrower blocker that owns those failing phase families.
- If the tracked Lolo review eventually becomes supportable as a governed
  replacement path, the next live packet after this blocker should be a ready
  replacement-path packet rather than a return to generic ECID blocker
  classification.
