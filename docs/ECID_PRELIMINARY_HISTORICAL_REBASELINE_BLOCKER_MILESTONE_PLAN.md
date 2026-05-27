# ECID Preliminary Historical Rebaseline Blocker Milestone Plan

Date: 2026-05-26

Status: Resolved locally (`Milestones 0-3 resolved locally; no bounded
historical-source-set rebuild path remains under current artifacts; no
tracked governed replacement is currently proven; exact live work now routes
to the Lolo source-set contract blocker through the historical
replacement-feasibility predecessor`)

Owner context: standalone blocker follow-on opened after the parent ECID
historical-lane packet proved that none of the three currently visible closure
paths is ready under live artifacts. `source-set-4fb59e9eb43045cb` still fails
source-set `phase-eval` at `10/33`, `source-set-ba8d0feae79501b8` now fails
fresh `applicability-validate` with `source_set_stale=398`,
`partition_gap=329`, `missing_candidate_decision=4`,
`unresolved_authority=4`, and `provenance_gap=1`; fresh
`v1-ea-eval --review-id region1-example-lolo-tylers-kitchen-66344 --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json`
now fails `contract_status="mismatch"` because the eval contract expects
`source-set-4fb59e9eb43045cb` while the live review artifacts report
`source-set-5e65d845ce77e1a0`; and fresh review `phase-eval` for that tracked
replacement candidate remains red at `12/29`. This packet owns exact blocker
classification and the next truthful owner route only. It does not flip the
ECID historical slot to `ready`, lower the governed expansion floor, reopen
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, or claim a
replacement is ready before its own gates pass.

## Latest Local Implementation

- Milestone 3 is now closed locally. Fresh tracked Lolo readback showed that
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  and `config/v1_lolo_tylers_kitchen_real_ea_eval.json` still bind the
  tracked review to `source-set-4fb59e9eb43045cb`, while the live
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
  `v1_ea_eval_results.json` now reports
  `source-set-5e65d845ce77e1a0` and fails only
  `review_identity_matches_contract`, and the live
  `phase_eval_results.json` remains red at `12/29` on `4fb...`.
- That evidence proved the remaining replacement debt was no longer a generic
  ECID blocker-classification problem and first routed live work into
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`.
- That successor then reduced Milestone 1 further: tracked config remained on
  `4fb...`, most live review-local artifacts remained on `5e65...`, and stale
  `downstream_direct_evaluation` coverage still remained on `f70...`, so the
  exact live owner is now
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`.
  That narrower reroute closeout landed in `013b5d1`
  (`Open Lolo source-set contract blocker`). The active child packet then
  realigned the tracked replay context and review eval contract to `5e65...`,
  reduced Milestone 2 locally in `e2b6941`
  (`Reduce Lolo source-set blocker Milestone 2`), and resolved Milestone 3 by
  routing the residual red into
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`.
- This packet now remains as the older predecessor closeout that routed live
  work away from generic ECID blocker classification and into the narrower
  Lolo lineage.

## Purpose

Route the remaining ECID preliminary historical strict-expansion blocker to
one truthful next owner.

The parent lane-resolution packet already exhausted its two closure branches
under current artifacts:

- no coherent historical-source-set rebuild is currently proven on either
  known source set; and
- no tracked governed ready-slot replacement is currently proven.

This blocker packet exists to keep that fact explicit, freeze the evidence that
forced the stop condition, and open exactly one narrower implementation owner
from current repo truth:

- a historical source-set rebuild packet, if bounded rebaseline repair is
  still supportable; or
- a governed ready-slot replacement readiness packet, if a tracked candidate
  can be made ready without weakening the manifest floor.

If neither path is supportable within the narrow review-local boundary, this
packet must stop by routing a more specific feasibility blocker rather than
blurring the scope back into the parent plan.

Freshness check rule:
before any Milestone 1 or Milestone 2 runtime proving begins, re-read
`docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, the top of
`docs/SESSION_HANDOFF.md`, `config/promotion_suite_v1.json`, and the live
`4fb...`, `ba8...`, and tracked replacement-review result files. If any
source-set IDs, counts, replacement candidates, or slot-contract expectations
drift, update this blocker plan and the current-routing docs before
implementation continues.

## Current Evidence

- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the top of
  `docs/SESSION_HANDOFF.md` now agree that this blocker packet is the exact
  predecessor closeout and that
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  is the active route, with
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  preserved as the intermediate predecessor.
- The parent packet
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
  completed its Sequence 0 guard successfully: ready expansion slots now fail
  closed if any JSON `expected_gate_artifact` proves a different
  `source_set_id` than the slot contract.
- Aggregate post-V1 truth remains stable:
  `real-package-review-coverage-eval` is still green with
  `reviewer_ready_slot_count=2` and `missing_required_slot_count=0`; non-strict
  `promotion-suite` remains `current_promotion_ready=true` and
  `promotion_ready=true`; strict expansion still fails only because the ECID
  preliminary historical slot is `selected_not_ready` under
  `historical_source_set_split`, with `open_expansion_slot_count=1` and
  `open_expansion_artifact_count=0`.
- The historical rebuild branch is currently unproven on both known source
  sets, and Milestone 1 now confirms that neither remains a bounded rebuild
  path under current artifacts:
  - `source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`
    remains `passed=false` with `passed_phase_count=10/33`.
  - A fresh
    `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8`
    now fails under current artifacts with `source_set_stale=398`,
    `partition_gap=329`, `missing_candidate_decision=4`,
    `unresolved_authority=4`, and `provenance_gap=1`.
- The tracked governed replacement branch is also currently unproven:
  fresh `v1-ea-eval` on
  `region1-example-lolo-tylers-kitchen-66344` now fails
  `contract_status="mismatch"` because the tracked eval contract still points
  at `source-set-4fb59e9eb43045cb` while the live review artifacts report
  `source-set-5e65d845ce77e1a0`, and fresh
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
  now remains `passed=false` with `passed_phase_count=12/29`.
- The governed replacement roster is still unchanged under current manifests:
  `real-package-review-coverage-eval` remains green with covered reviews
  limited to East Crazies, West Reservoir, and South Plateau, and
  non-strict `promotion-suite` still reports only the ECID historical slot and
  South Plateau in the expansion roster.
- The current slot contract remains unchanged and must stay fail-closed during
  blocker routing:
  `config/promotion_suite_v1.json` still records
  `region1-real-ea-slot-1` as `status="selected_not_ready"` with
  `failure_category="historical_source_set_split"` and explicit split-source
  evidence on `source-set-ba8d0feae79501b8` and
  `source-set-4fb59e9eb43045cb`.

## Goal

Leave the repository with one exact next implementation owner for the ECID
preliminary historical strict-expansion blocker and no ambiguity about why the
parent lane-resolution packet stopped.

Completion means all of the following are true:

- current-facing docs point to this blocker packet until a narrower owner is
  opened and routed forward;
- the parent ECID historical-lane plan remains preserved as the blocked
  historical record rather than the live runtime packet;
- the packet exits with exactly one named next owner:
  a historical-source-set rebuild packet, a replacement-ready-slot packet, or a
  narrower feasibility blocker if neither path is supportable; and
- no governed slot-floor, quorum, or ready-state contract is weakened while
  routing the blocker.

## Non-Goals

- Do not make strict expansion green inside this blocker packet by relabeling
  status fields, deleting the slot, or shrinking manifest requirements.
- Do not rerun downloader, catalog-build, or full-canonical source capture as
  part of this packet.
- Do not treat the tracked Lolo candidate or any other candidate as a ready
  replacement while review `phase-eval` is still red.
- Do not reopen
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` or continue live
  runtime work inside
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`.
- Do not stage ignored `source_library/` outputs unless repository policy
  changes or the user explicitly expands scope.

## Scope

- blocker classification for the ECID preliminary historical strict-expansion
  lane
- exact source-set and replacement-candidate evidence that triggered the parent
  packet stop condition
- current-routing, current-state, handoff, and packet-lineage docs for the
  active blocker route
- naming and routing of the next narrower implementation owner

## Out Of Scope

- executing the full historical-source-set rebuild itself
- making a replacement review reviewer-ready inside this packet
- changing the governed expansion slot floor or aggregate quorum semantics
- reopening ECID current-promotion or South Plateau reviewer-ready replay
  repair
- broad architecture, downloader, queue, or full-canonical source-truth work

## Owner Surfaces

- active blocker and parent packet docs:
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- current-routing docs:
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`
- aggregate governed slot contracts:
  `config/promotion_suite_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`
- live historical-source-set evidence:
  `source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`,
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/`
- tracked replacement-review identity and current evidence:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
- focused contract tests if a later child packet touches manifest or slot
  behavior:
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_expansion_slots.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_cli_eval.py`

## Placement Rules

- Keep the parent ECID historical-lane plan as the blocked historical parent.
  Do not continue live runtime implementation there after this blocker route is
  opened.
- Keep this packet docs-first until one narrower owner is chosen. Do not mix
  historical-source-set rebuild work and replacement-readiness work in the same
  first implementation slice.
- Keep the governed slot floor, slot count, and fail-closed ready-slot
  contracts unchanged in this packet.
- If a bounded historical-source-set repair path is supportable, open a named
  child packet before changing runtime or manifest surfaces.
- If a governed replacement path is supportable, open a named child packet
  before changing runtime or manifest surfaces.
- Keep generated evidence local under `source_library/`; commit only tracked
  docs, config, code, and tests.

## Weak-Point Prevention Contract

- Weak point forecast: a future session keeps using the blocked parent packet or
  the resolved replay-repair packet as the live route because the current docs
  never name this blocker packet exactly.
  Owner surface: `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
  Prevention gate: the current-facing docs must point to this packet by exact
  filename and preserve the parent packet only as historical blocked context.
  Fail threshold: any current-facing doc still leaves the next packet generic,
  keeps the parent ECID plan as active runtime work, or points back to the
  resolved replay-repair packet as the next owner.
  Controlled violation: leave one current-facing doc on the old generic
  "open a dedicated blocker follow-on" wording; readback and `git diff --check`
  do not complete the milestone.
  Future-Codex misuse scenario: an agent opens the wrong packet and resumes
  stale work because the blocker route is unnamed; the current docs must make
  that mistake obvious.

- Weak point forecast: a future session treats one of the three red signals as
  implicitly close enough and skips the explicit blocker classification step.
  Owner surface: this blocker plan, the parent ECID plan, and
  `docs/POST_V1_PROMOTION_SUITE.md`
  Prevention gate: any child packet opened from this plan must cite exact live
  evidence for either historical-source-set viability or replacement readiness
  before runtime changes begin.
  Fail threshold: a child packet claims rebuild or replacement viability
  without a passing governing signal for the path it selects.
  Controlled violation: route directly to a ready replacement while the tracked
  Lolo candidate still fails `v1-ea-eval` on the `4fb...` versus `5e65...`
  identity split and fresh review `phase-eval` remains red at `12/29`; the
  blocker classification review must reject it.
  Future-Codex misuse scenario: an agent assumes the nearest candidate is ready
  because it is already tracked; this packet forces explicit evidence instead
  of wishful routing.

- Weak point forecast: strict expansion gets "fixed" by weakening the manifest
  floor, deleting the slot, or relabeling a blocked slot as ready during
  blocker routing.
  Owner surface: `config/promotion_suite_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_expansion_slots.py`,
  `tests/test_real_package_review_coverage_eval.py`
  Prevention gate: any later child packet that changes slot or manifest
  surfaces must keep non-strict `promotion-suite` green, strict expansion
  fail-closed until the blocker is truly closed, and the governed slot floor
  unchanged.
  Fail threshold: required expansion slot count drops, the ECID historical slot
  becomes `ready` with split-source evidence, or the replacement ends in any
  non-ready state.
  Controlled violation: delete `region1-real-ea-slot-1` or set it to `ready`
  while keeping `historical_source_set_split`; focused tests and strict
  expansion must fail.
  Future-Codex misuse scenario: an agent tries to get green by editing manifest
  status only; the governed slot-floor tests and strict gate must stop that.

- Weak point forecast: the next implementation slice starts changing both the
  historical-source-set lane and the replacement candidate in one milestone,
  making the blocker owner boundary impossible to verify.
  Owner surface: this blocker plan and any child packet it opens
  Prevention gate: the first runtime implementation after this packet must open
  exactly one named child packet and commit only that owner slice.
  Fail threshold: one milestone changes both historical-source-set replay and
  replacement-review readiness without an explicit narrower owner boundary.
  Controlled violation: mix `source-set-ba8...` / `source-set-4fb...` replay
  changes with Lolo replacement readiness edits in one slice; blocker routing
  review must reject the milestone boundary.
  Future-Codex misuse scenario: an agent broadens scope because both paths look
  related; the child-packet requirement keeps the next slice narrow.

## Milestone Sequence

### Milestone 0 - Exact Blocker Packet And Routing Reset

Outcome label: resolved

Purpose: open this blocker packet, preserve the parent packet's stop-condition
evidence, and move the current-facing docs to exact routing.

Implementation:

1. Create this blocker plan with the exact live evidence that exhausted the
   parent ECID historical-lane packet.
2. Update the current-routing, current-state, handoff, promotion-suite, parent
   ECID plan, and replay-repair lineage docs so they name this packet exactly.
3. Preserve the parent ECID plan as historical blocked context rather than
   deleting or rewriting its stop-condition evidence.

Acceptance criteria:

- The active packet in current-facing docs is this blocker plan by exact
  filename.
- The parent ECID plan is no longer presented as active runtime work.
- No manifest, slot, or runtime contract changes are made in this routing-only
  milestone.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md

python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md

python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md

git diff --check
```

Milestone 0 resolution on 2026-05-26:

- closing commit hash:
  `8cb20fb` (`Open ECID historical blocker follow-on`)
- resolution truth:
  the blocker packet is now open as the exact active route, the parent ECID
  historical-lane plan is preserved as blocked historical context, and the
  current-facing docs no longer leave the next owner generic.
- focused verification:
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  and `git diff --check`
- next routing:
  continue with Milestone 1 in this blocker packet.

### Milestone 1 - Historical Source-Set Feasibility Classification

Outcome label: reduced

Purpose: decide whether the blocker still belongs to a bounded
historical-source-set rebuild packet under current artifacts.

Implementation:

1. Re-read the live `4fb...` source-set `phase-eval` result and the live
   `ba8...` `applicability-validate` result.
2. Determine whether either historical source set can progress within the
   narrow review-local or source-set-local boundary, or whether both now depend
   on broader source-truth or adjudication work outside this packet.
3. If one bounded rebuild path exists, open
   `docs/ECID_PRELIMINARY_HISTORICAL_SOURCE_SET_REBUILD_MILESTONE_PLAN.md`
   and route this blocker to it. If not, record that historical rebuild
   remains infeasible under current artifacts and continue to Milestone 2.

Acceptance criteria:

- The packet exits Milestone 1 with one exact historical-source-set conclusion,
  not an implicit hunch.
- No strict-expansion or slot-roster contract changes land during the
  classification step.
- The next branch is recorded in tracked docs rather than operator memory.

Verification:

```bash
jq '{source_set_id, passed, passed_phase_count, phase_count}' \
  source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8 \
  --validation-path /tmp/<temp>/applicability_validation.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id <candidate_historical_source_set_id>
```

Milestone 1 resolution on 2026-05-26:

- closing commit hash:
  `2149825` (`Route ECID historical blocker to Milestone 2`)
- outcome label:
  `reduced locally`; no bounded historical-source-set rebuild path remains
  under current artifacts, so the blocker advances to Milestone 2 instead of
  opening `docs/ECID_PRELIMINARY_HISTORICAL_SOURCE_SET_REBUILD_MILESTONE_PLAN.md`
- resolution truth:
  `source-set-4fb59e9eb43045cb` remains source-set `phase-eval` red at
  `10/33`, and its failing phases still span upstream and downstream families
  including `extraction`, `retrieval`, `claim_extraction`,
  `rule_claim_binding`, `downstream_direct_evaluation`,
  `generated_rule_pack`, `compliance_review`, `review_packet_index`, and
  `evaluation_coverage`. That makes `4fb...` a broad source-set/runtime lane,
  not a narrow historical review-case rebuild. `source-set-ba8d0feae79501b8`
  also remains infeasible under current artifacts: fresh
  `applicability-validate` still fails on `missing_candidate_decision=4`,
  `partition_gap=329`, `provenance_gap=1`, and `source_set_stale=398`, with
  the validation artifact still showing four missing land-exchange
  rule-template authorities plus a large unexpected Custer Gallatin
  forest-plan component family. Fresh
  `applicability-generate-rule-pack` still fails closed on `ba8...` because
  `applicability_validation.json` is stale for current artifacts
- focused verification:
  `jq '{source_set_id, passed, passed_phase_count, phase_count}' source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`,
  `jq '.phases | map(select(.passed == false) | {name, reviewer_ready, failure_reasons})' source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8 --validation-path /tmp/ecid_preliminary_ba8_applicability_validation_20260526.json`,
  `jq '{source_set_id, passed, reviewer_ready, failed_checks: [.checks[] | select(.passed == false) | .details]}' /tmp/ecid_preliminary_ba8_applicability_validation_20260526.json`,
  and
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8`
- next routing:
  continue with Milestone 2 in this blocker packet.

### Milestone 2 - Governed Replacement-Readiness Classification

Outcome label: reduced

Purpose: if historical rebuild remains infeasible, determine whether a tracked
governed replacement can become the next narrow owner without weakening the
manifest floor.

Implementation:

1. Rebaseline the tracked Lolo candidate
   `region1-example-lolo-tylers-kitchen-66344` and only any equivalent
   already-tracked governed candidate that current docs or manifests already
   name. Do not start broad open-ended scouting.
2. Require package authority, replay context, review contract, and
   review-scoped `phase-eval` readiness before any candidate can be named
   viable for replacement routing.
3. If one candidate is viable, open
   `docs/ECID_PRELIMINARY_HISTORICAL_REPLACEMENT_READY_SLOT_MILESTONE_PLAN.md`
   and route this blocker to it. If none are viable, continue to Milestone 3.

Acceptance criteria:

- The packet exits Milestone 2 with one exact candidate route or an explicit
  committed finding that no tracked ready replacement path is currently proven.
- No candidate is treated as ready while review `phase-eval` remains red.
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

Milestone 2 resolution on 2026-05-26:

- closing commit hash:
  `191fc3e` (`Close ECID blocker Milestone 2`)
- outcome label:
  `reduced locally`; no tracked governed replacement is currently proven
  under live artifacts, so the blocker advances to Milestone 3 instead of
  opening `docs/ECID_PRELIMINARY_HISTORICAL_REPLACEMENT_READY_SLOT_MILESTONE_PLAN.md`
- resolution truth:
  fresh Lolo candidate proving fails on both contract identity and readiness.
  `v1-ea-eval` now exits red with `contract_status="mismatch"` because
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json` still expects
  `source-set-4fb59e9eb43045cb` while the live review artifacts report
  `source-set-5e65d845ce77e1a0`. Fresh review `phase-eval` also remains red
  at `12/29` on `source-set-4fb59e9eb43045cb`, with failing phases spanning
  missing direct-eval coverage (`retrieval`, `claim_extraction`,
  `rule_claim_binding`, `evaluation_coverage`) plus review-local
  source-set-mismatch phases including `applicability_validation`,
  `compliance_review`, `forest_plan_component_eval`, and
  `forest_plan_component_adjudication`. The governed aggregate roster remains
  unchanged under current manifests: fresh
  `real-package-review-coverage-eval` is still green with covered reviews
  limited to East Crazies, West Reservoir, and South Plateau, and fresh
  non-strict `promotion-suite` still keeps only the ECID historical slot and
  South Plateau in the expansion roster while failing closed only on
  `historical_source_set_split`
- focused verification:
  `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-lolo-tylers-kitchen-66344 --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-lolo-tylers-kitchen-66344`,
  `jq '{review_id: .summary.review_id, source_set_id: .summary.source_set_id, passed: .summary.passed, contract_status: .summary.contract_status, actual_overall_passed: .summary.actual_overall_passed, broader_ea_passed: .summary.broader_ea_passed, forest_plan_passed: .summary.forest_plan_passed, failed_checks: [.summary.checks[] | select(.passed == false) | {name, details}]}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`,
  `jq '{review_id, source_set_id, passed, passed_phase_count, phase_count, reviewer_ready, missing_direct_eval_phase_count, proxy_only_phase_count, failed_phase_names: [.phases[] | select(.passed == false) | .name]}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  and
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- next routing:
  continue with Milestone 3 in this blocker packet.

### Milestone 3 - Exact Child-Route Or Feasibility-Stop Closeout

Outcome label: resolved

Purpose: leave the blocker with one exact next packet or one exact feasibility
stop, then close this routing packet truthfully.

Implementation:

1. Update the current docs, handoff, and this plan with the exact named child
   packet chosen in Milestone 1 or Milestone 2, or with the exact narrower
   feasibility blocker if neither path is currently supportable.
2. Preserve the parent ECID historical-lane plan and the replay-repair packet
   as historical lineage only.
3. Stage only the verified tracked docs and any child-packet file created in
   this closeout, then create one atomic local commit.

Acceptance criteria:

- Current-facing docs no longer leave the next owner generic.
- The blocker either routes to one named child packet or records one explicit
  feasibility stop condition.
- The handoff records the commit hash and exact verification bundle.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

Milestone 3 live closeout note on 2026-05-26:

- closing commit hash:
  `6a4e87d` (`Open Lolo replacement feasibility blocker`)
- outcome label:
  `resolved locally`; this blocker now exits with one exact next owner rather
  than a generic feasibility stop
- resolution truth:
  the tracked Lolo candidate now narrows the remaining replacement debt to a
  review-local contract and source-set feasibility blocker. The replay context
  and tracked `v1-ea-eval` contract remain on `4fb...`, the live
  `v1_ea_eval_results.json` reports `5e65...` and fails
  `review_identity_matches_contract`, and the live review
  `phase-eval` remains red at `12/29` on `4fb...`
- next routing:
  continue in
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 1. Treat this packet as historical predecessor closeout only
- focused verification:
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  and `git diff --check`

## Required Implementation Artifacts

- this blocker plan
- the preserved parent ECID historical-lane plan marked as historical blocked
  context
- exact current-facing doc routing to this packet
- one named child packet or one narrower feasibility blocker before this packet
  closes

## Required Documentation And Handoff Updates

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
- this plan
- `README.md` only if the public route summary changes materially

## Required Verification Gates

- plan lint for any touched milestone plan docs
- `git diff --check`
- if Milestone 1 executes live proving:
  `jq` readback of `4fb...` source-set `phase_eval_results.json`,
  `applicability-validate`, and any bounded follow-on gate needed to prove or
  reject the historical rebuild path
- if Milestone 2 executes live proving:
  the tracked replacement review's `v1-ea-eval`, `phase-eval`,
  `real-package-review-coverage-eval`, and non-strict `promotion-suite`
- if any later child packet changes manifest or runtime surfaces:
  focused `promotion-suite` and coverage tests plus the repo's stricter gates
  for the touched surface

## Acceptance Criteria

- The repository no longer routes future sessions to a generic unnamed blocker
  or to the blocked parent packet as live runtime work.
- The blocker evidence for `4fb...`, `ba8...`, and the tracked Lolo candidate
  is frozen in tracked docs and tied to an exact next owner decision.
- The governed expansion slot floor and fail-closed slot contract remain
  unchanged while routing the blocker.
- The next packet after this blocker, or the narrower feasibility stop, is
  named explicitly in tracked docs and handoff.

## Stop Conditions

- Stop if the only apparent way forward is to relabel the historical ECID slot
  as `ready`, delete it, lower counts, or weaken tests.
- Stop if either historical-source-set path now requires broad downloader,
  catalog, or full-canonical reruns outside the narrow review-local boundary.
- Stop if replacement readiness depends on a candidate that is still
  review-`phase-eval` red and no narrower owner can make it green without
  broad unrelated work.
- Stop if no exact child packet can be named from current evidence; in that
  case, open a narrower feasibility blocker rather than broadening this packet.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked
  complete, `resolved`, or `reduced` until verification passes, durable
  docs/handoff updates land, and the local atomic commit exists. A verified
  but uncommitted slice is only ready-to-close.
- Stage only the verified tracked slice for this blocker packet.
- Leave unrelated dirty or untracked files alone.
- Keep ignored `source_library/` evidence local.
- Include the blocker plan, the touched routing docs, and any named child
  packet opened during closeout in the same commit.
- Record the commit hash and exact verification bundle in
  `docs/SESSION_HANDOFF.md`.
- Treat the blocker route as incomplete until the local commit exists.
- Preserve anti-test-weakening rules: do not weaken or loosen gates, skip
  checks, delete negative coverage, or lower the governed slot floor to make
  blocker routing look green.

## Residual Risks And Next Milestone Routing

- If Milestone 1 finds a bounded historical-source-set path, the next live work
  should move to
  `docs/ECID_PRELIMINARY_HISTORICAL_SOURCE_SET_REBUILD_MILESTONE_PLAN.md`
  rather than continuing mixed blocker classification here.
- If Milestone 2 finds a viable governed replacement candidate, the next live
  work should move to
  `docs/ECID_PRELIMINARY_HISTORICAL_REPLACEMENT_READY_SLOT_MILESTONE_PLAN.md`.
- If Milestone 2 does not find a viable governed replacement candidate,
  Milestone 3 must route the next live work into a narrower feasibility
  blocker instead of reopening the parent lane or the replay-repair packet.
- Once this blocker packet routes onward, `docs/CURRENT_ROUTING.md` should name
  the child packet directly and this blocker should become historical context.

## Closeout Checklist

- [x] Milestone 0 opened this blocker packet and reset current-facing routing.
- [x] Milestone 1 recorded an exact historical-source-set feasibility result.
- [x] Milestone 2 recorded an exact replacement-readiness result if needed.
- [x] Milestone 3 named one exact next owner or one narrower feasibility stop.
- [x] The verified tracked slice was committed atomically.
