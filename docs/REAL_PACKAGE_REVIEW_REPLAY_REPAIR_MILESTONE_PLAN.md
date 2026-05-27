# Real Package Review Replay Repair Milestone Plan

Date: 2026-05-25

Status: Resolved locally (`Milestone 0` baseline inventory is historical,
reviewer-facing source-set alignment is now resolved locally, ECID aligned
forest-plan inventory plus compliance replay are now reduced locally, ECID
current-promotion replay is now green on reviewer-facing
`source-set-f70ea11e04ae3d53`, South Plateau reviewer-ready expansion is now
also green there, and the historical ECID preliminary-EA lane is now
truthfully rerouted as a selected-not-ready strict-expansion slot on its split
historical source-set contract. Any future work there should open a fresh
follow-on rather than reopening this packet to reassert missing downstream
artifacts. The live routed successor is now
`docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
with
`docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
preserved as the intermediate predecessor, with
`docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
preserved as the exact predecessor closeout and
`docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
preserved as the blocked historical parent record)

Owner context: this standalone follow-on packet opened after
`docs/PROMOTION_SUITE_SLOT_DRIVEN_CONTRACT_MILESTONE_PLAN.md` closed through
Milestone `4`. It owns the review-local replay-repair lane and the scoped
replay-precondition rebuild on `source-set-f70ea11e04ae3d53`. The
reviewer-facing source-set alignment blocker is now historical closeout in
`docs/REVIEWER_FACING_SOURCE_SET_ALIGNMENT_BLOCKER_MILESTONE_PLAN.md`, and
this packet is active again for the remaining ECID preliminary-EA historical
expansion lane plus aggregate closeout. The aligned reviewer-facing source-set
repairs for ECID current promotion and South Plateau are now historical
completed slices inside this packet. It does not reopen the slot-driven
promotion-suite contract architecture, the full-canonical source-set contract,
or the West Reservoir typed-blocked quarantine.

## Latest Local Implementation

- The scoped replay-precondition chain on `source-set-f70ea11e04ae3d53`
  remains green through `applicability-authority-universe` with
  `authority_universe_sha256=33355dce05cb0141840bf5ad6463570173294e6e1a368d0e24f8910961a04554`.
- Reviewer-facing replay contexts plus ECID and South `v1-ea-eval` contracts
  now also point at that same governed `source-set-f70ea11e04ae3d53` truth.
- Both reviewer-facing `applicability-authority-universe` reruns now pass on
  the aligned source set with `candidate_authority_count=396` and
  `forest_plan_component_candidate_count=329`.
- `applicability-context-build` and `applicability-retrieve` now pass for
  both reviews on the aligned source set, and governed replay adjudication is
  now also green there: current-review applicability adjudications now live at
  `config/applicability_adjudications/v1-cg-ecid-compliance-review.json` and
  `config/applicability_adjudications/region1-expansion-south-plateau-landscape-treatment.json`,
  `applicability-validate` now passes for both reviews
  (`55 applicable / 341 non-applicable` for ECID and
  `64 applicable / 332 non-applicable` for South), and
  `applicability-generate-rule-pack` now passes with `55` ECID generated rules
  and `64` South generated rules on `source-set-f70ea11e04ae3d53`.
- `src/usfs_r1_ea_sources/forest_plan_inventory_build_manifest.py` and
  `src/usfs_r1_ea_sources/forest_plan_components_inventory_build.py` now let
  one governed forest-plan inventory profile row match multiple explicit
  source sets. `config/r1_forest_plan_component_inventory_build_manifest.json`
  now binds the Custer Gallatin profile to both
  `source-set-4fb59e9eb43045cb` and `source-set-f70ea11e04ae3d53` through the
  shared `FOR-009` source-record mapping, with focused regressions in
  `tests/test_forest_plan_inventory_build_manifest.py` and
  `tests/test_forest_plan_components_manifest.py`.
- ECID aligned forest-plan replay is now reduced locally rather than still
  fully red: `forest-plan-components-build` on
  `source-set-f70ea11e04ae3d53` now rebuilds the Custer inventory through
  `FOR-009` with `component_count=329`, `standard_count=58`,
  `coverage_passed=true`, and `component_source_accuracy_passed=true`;
  `forest_plan_context_summary.json` there reports `reviewer_ready=true` with
  `component_count=329`, `applicable_count=79`,
  `reviewer_resolution_count=0`, and `applied_standard_count=12/12`;
  `forest-plan-component-eval --review-id v1-cg-ecid-compliance-review` now
  passes `35/35`; and `forest-plan-component-eval-coverage` now covers that
  current slot with `passed=true`, `stale_identity=false`, and
  `unresolved_review=false`.
- ECID aligned compliance replay is now also green on the reviewer-facing
  source set: the committed zero-item adjudication template now lives at
  `config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.json`
  with companion worklist
  `config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.md`,
  `forest-plan-component-adjudication-eval` now passes with
  `pending_adjudication_count=0`, and `compliance-review --review-id
  v1-cg-ecid-compliance-review` now passes with `reviewer_ready=true`,
  `validation_passed=true`, and forest-plan component adjudication/evaluation
  subchecks both `reviewer_ready=true`.
- South Plateau no longer carries the live replay blocker there:
  `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment`
  now reports `contract_status="reviewer_ready"` with
  `broader_ea_passed=true`, `forest_plan_passed=true`, and no blocker
  categories; review `phase-eval` now passes `27/27` with
  `review_direct_eval_status="direct_eval_present"`.
- ECID `v1-ea-eval` now also closes green on the aligned source set with
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`,
  `forest_plan_passed=true`, and no remaining failure categories.
- ECID review `phase-eval` now also closes green there with `33/33` passed
  phases, `reviewer_ready=true`,
  `review_direct_eval_status="direct_eval_present"`,
  `missing_direct_eval_phase_count=0`, and
  `threshold_failed_phase_count=0`.
- Non-strict `promotion-suite` is now truthful again for current promotion:
  `current_promotion_ready=true`, `promotion_ready=true`, and
  `passed_required_current_result_count=32/32`.
- `real-package-review-coverage-eval` is now green with
  `passed=true`, `reviewer_ready_slot_count=2`,
  `missing_required_slot_count=0`, and `missing_coverage_class_ids=[]`.
- The remaining strict-expansion red is now routed truthfully through the
  historical ECID preliminary-EA slot rather than through six false live
  artifact requirements. Non-strict `promotion-suite` now reports
  `open_expansion_slot_count=1`, `open_expansion_artifact_count=0`, and
  `expansion_failure_category_counts={"historical_source_set_split":1}`.
  Strict expansion now fails closed only because
  `region1-expansion-ecid-preliminary-ea` is a selected-not-ready slot on a
  split historical lane: applicability validation and phase eval remain on
  `source-set-ba8d0feae79501b8`, while the generated rule pack and slot
  identity remain on `source-set-4fb59e9eb43045cb`

## Purpose

Repair the live review-local replay debt now exposed by the slot-driven
contract closeout.

The promotion-suite contract packet is done: the aggregate gate now chooses the
current-promotion lane from governed slots instead of one hard-coded review
packet. The remaining red is no longer contract architecture drift or South
replay debt. It is the historical ECID preliminary-EA expansion review-case
artifact family:

- East Crazies current promotion now satisfies its tracked `v1-ea-eval`
  contract on the active source set
- South Plateau now satisfies its governed reviewer-ready expansion slot
- the aggregate real-package coverage gate is green, but the strict-expansion
  promotion path stays red until the ECID preliminary-EA historical artifact
  family is refreshed or honestly rerouted

This packet exists to repair those review-local artifact families without
weakening the governed slot roster or reopening the contract refactor.

## Current Evidence

- `source_library/reviews/real_package_review_coverage_eval/real_package_review_coverage_eval_results.json`
  now reports `passed=true`, `reviewer_ready_slot_count=2`,
  `missing_required_slot_count=0`, and `failure_category_counts={}`.
- The ECID governed slot `east-crazies-current-promotion` now reports
  `actual_contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, `forest_plan_passed=true`, and
  `failure_category_counts={}`.
- The South Plateau governed slot `south-plateau-reviewer-ready` now reports
  `actual_contract_status="reviewer_ready"`, `broader_ea_passed=true`,
  `forest_plan_passed=true`, and `failure_category_counts={}`.
- West Reservoir still truthfully reports
  `actual_contract_status="typed_blocked"` and remains outside the repair
  target for this packet.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  now reports `full_canonical_corpus_ready=true`,
  `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `open_expansion_slot_count=1`,
  `open_expansion_artifact_count=0`,
  `passed_required_current_result_count=32`,
  `required_current_result_count=32`,
  `passed_required_expansion_result_count=19`,
  `required_expansion_result_count=20`, and `failure_category_counts={}`.
- Strict-expansion `promotion-suite` now fails closed only on the ECID
  preliminary-EA historical selected-not-ready slot with
  `current_promotion_ready=true`, `promotion_ready=false`,
  `expansion_ready=false`,
  `failure_category_counts={"historical_source_set_split":1}`,
  `open_expansion_slot_count=1`, and `open_expansion_artifact_count=0`.
- The scoped replay-precondition chain is now green on
  `source-set-f70ea11e04ae3d53` under
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`:
  `applicability-authority-universe` there now reports
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `rule_template_candidate_count=48`,
  `authority_family_rule_template_candidate_count=19`, and
  `authority_universe_sha256=33355dce05cb0141840bf5ad6463570173294e6e1a368d0e24f8910961a04554`.
- Reviewer-facing source-set alignment is no longer the blocker. Both ECID and
  South Plateau `applicability-authority-universe` reruns now pass on aligned
  `source-set-f70ea11e04ae3d53`, and ECID broader-EA plus review-direct-eval
  replay are now also green there. South replay is also green; strict
  expansion now truthfully routes the remaining historical ECID preliminary-EA
  work through a selected-not-ready slot on its split legacy source-set
  surfaces.
- `source_library/evaluations/forest_plan_component_eval_coverage/forest_plan_component_eval_coverage_results.json`
  now reports `covered_review_count=1`,
  `covered_review_ids=["v1-cg-ecid-compliance-review"]`,
  `stale_identity_count=2`, and `unresolved_review_count=3`: the ECID
  current-promotion component slot is now covered and green, while
  source-delta, West Reservoir, and Lolo still keep the aggregate lane red.

## Goal

Keep the now-green South Plateau and ECID current-promotion lanes stable while
closing the remaining aggregate replay packet around the historical ECID
preliminary-EA expansion review-case artifact family.

Completion means all of the following are true:

- South Plateau remains `reviewer_ready` on
  `source-set-f70ea11e04ae3d53`.
- `real-package-review-coverage-eval` stays green for the governed slot set.
- the ECID preliminary-EA historical review case either has its missing
  downstream compliance/provenance artifacts rebuilt truthfully, or the strict
  expansion contract is rerouted truthfully so it no longer claims those
  missing artifacts exist.
- the aggregate promotion signals remain truthful: non-strict current
  promotion stays green, while strict expansion closes only when the remaining
  ECID preliminary-EA historical lane is truly ready.

## Non-Goals

- Do not reopen slot-driven promotion-suite architecture, selector semantics,
  same-slot family rules, or canary routing.
- Do not lower required coverage-class counts, delete required slots, or change
  reviewer-ready slots to easier contract states just to make the aggregate
  replays green.
- Do not rerun downloader, catalog, extraction, retrieval, or other
  full-canonical corpus workflows unless a focused review-local replay command
  proves they are strictly required.
- Do not change West Reservoir's typed-blocked status in this packet.
- Do not stage ignored `source_library/` outputs unless repository policy
  changes or the user explicitly expands scope.

## Scope

- ECID preliminary-EA historical expansion review-case artifact family on its
  split `source-set-ba8d0feae79501b8` / `source-set-4fb59e9eb43045cb` lane
- truthful strict-expansion contract or routing updates for that historical
  review case when repair is not supportable
- aggregate replay confirmation that
  `real-package-review-coverage-eval` stays green and `promotion-suite`
  remains truthful for both non-strict and strict-expansion modes
- focused docs and handoff updates that describe the repaired or rerouted live
  result without reopening already-green reviewer-ready slots

## Out Of Scope

- a broader roster redesign for `config/v1_real_package_review_coverage_v1.json`
- changing expansion policy or strict-expansion semantics
- Lolo, queue, downloader, or forest-specific example-package work
- full-canonical source-set rebinds or corpus refreshes

## Owner Surfaces

- governed aggregate contracts:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/promotion_suite_v1.json`
- preserved reviewer-ready slot contracts that must stay green while the
  historical lane is handled:
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`
- historical expansion review-case owners that may need focused replay repair
  or truthful reroute:
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/promotion_suite.py`,
  and the review-local artifact family under
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/`
- focused tests and fixtures:
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_current_runtime.py`,
  `tests/test_promotion_suite_full_canonical.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_v1_ea_eval_contracts.py`,
  `tests/test_phase_eval.py`,
  `tests/test_cli_eval.py`,
  `tests/test_architecture_contract.py`
- durable docs and routing:
  `README.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- Fix reviewer-ready slot drift in the packet-local review owners and tracked
  replay configs first, not by weakening aggregate thresholds.
- Keep `config/v1_real_package_review_coverage_v1.json` as the governed slot
  owner. Do not create a second hand-maintained roster elsewhere.
- Preserve the separation among
  `real-package-review-coverage-eval`, current-promotion readiness, and
  strict-expansion semantics. This packet repairs replay truth; it does not
  redesign the contract layers.
- If a slot cannot be restored to reviewer-ready truth with focused packet-local
  replay work, stop and route a new contract packet instead of silently
  relaxing the governed roster inside this replay-repair packet.

## Weak-Point Prevention Contract

- Weak point forecast: a future session makes the aggregate replays green by
  deleting required coverage classes, lowering thresholds, or rewriting slot
  contract statuses instead of repairing the review-local artifacts.
  Owner surface: `config/v1_real_package_review_coverage_v1.json`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`
  Prevention gate: aggregate tests and live replays must still require the
  governed reviewer-ready slots and fail closed on missing or mismatched slot
  status.
  Fail threshold: the aggregate result turns green only because required slot
  counts or reviewer-ready status requirements became easier.
  Controlled violation: change a required reviewer-ready slot to a looser
  status in fixtures without repairing the review-local artifacts; the eval and
  promotion-suite tests must fail.
  Future-Codex misuse scenario: a later agent edits the manifest instead of the
  review-local artifacts; the gate must catch the shortcut.

- Weak point forecast: a later agent handles the ECID preliminary historical
  lane by reopening South Plateau or ECID current-promotion drift, so the repo
  reports progress while the governed reviewer-ready slots stop being truthful.
  Owner surface:
  `source_library/reviews/real_package_review_coverage_eval/`,
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `tests/test_real_package_review_coverage_eval.py`
  Prevention gate: packet closeout requires both governed reviewer-ready slots
  to stay green while the ECID preliminary lane is repaired or rerouted.
  Fail threshold: strict-expansion work regresses either current reviewer-ready
  slot.
  Controlled violation: change the historical preliminary lane but leave
  either governed reviewer-ready slot mismatched; the aggregate gate must
  reopen.
  Future-Codex misuse scenario: a future agent treats the historical expansion
  lane as permission to ignore the already-green current slots; the aggregate
  gate must fail.

- Weak point forecast: the repair work expands into unnecessary corpus or
  downloader reruns and obscures the review-local root cause.
  Owner surface: this plan, `docs/SESSION_HANDOFF.md`, and the historical-lane
  owners above
  Prevention gate: each milestone must name the exact review-local command or
  artifact family being repaired before broader workflows are considered.
  Fail threshold: the packet mutates downloader/catalog/full-canonical state
  without evidence that a review-local command cannot repair the blocker.
  Controlled violation: propose a full-corpus rerun before reviewing the slot
  mismatch evidence; the packet must stop.
  Future-Codex misuse scenario: a later agent reaches for a broad rebuild
  because it is easier than tracing the review-local artifact family; the plan
  keeps the packet focused.

- Weak point forecast: the historical ECID preliminary lane is refreshed on
  mismatched `source-set-ba8d0feae79501b8` / `source-set-4fb59e9eb43045cb`
  identities, or the contract is rerouted without making that split explicit,
  so strict expansion looks repaired while the lane remains incoherent.
  Owner surface:
  `config/promotion_suite_v1.json`,
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/`,
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_full_canonical.py`
  Prevention gate: packet-local verification must prove either a coherent
  historical-lane identity or an explicit truthful reroute before aggregate
  closeout.
  Fail threshold: the aggregate gate changes color while the preliminary lane
  still mixes source-set identities or claims missing artifacts exist.
  Controlled violation: reroute the historical slot without updating the
  manifest-declared artifact expectations; the promotion-suite tests must fail
  closed.
  Future-Codex misuse scenario: a later agent patches the aggregate result
  without resolving or declaring the split historical identity; the gate must
  catch the shortcut.

## Milestone Sequence

### Milestone 0 - Baseline Replay Inventory

Outcome label: reduced

Purpose: freeze the exact live blocker set before any repair work begins.

Implementation:

1. Re-run or inspect the aggregate coverage and promotion-suite results for the
   active source set.
2. Record the failing ECID and South Plateau artifact families, source-set
   bindings, and package-authority surfaces.
3. Map each failing family to its review-local owner command or tracked config
   before broader edits begin.

Acceptance criteria:

- The packet records the exact live red counts and slot-level failure
  categories for ECID and South Plateau.
- The packet identifies the review-local owner surfaces for every failing
  family before any contract or doc rewrite is attempted.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

Milestone 0 live baseline on 2026-05-25:

- `real-package-review-coverage-eval` is now red at
  `reviewer_ready_slot_count=0`,
  `missing_required_slot_count=2`, and
  `missing_coverage_class_ids=["current_promotion_reviewer_ready","expansion_reviewer_ready"]`.
- ECID current promotion currently reports
  `actual_contract_status="mismatch"`,
  `broader_ea_passed=false`, `forest_plan_passed=false`, and
  `failure_category_counts={"baseline_source_record_missing":26,"citation_requirement_miss":4,"forest_plan_matrix_miss":1,"review_artifact_missing":4,"rule_section_mismatch":8}`.
- South Plateau reviewer-ready expansion currently reports
  `actual_contract_status="mismatch"`,
  `broader_ea_passed=false`, `forest_plan_passed=false`, and
  `failure_category_counts={"forest_plan_matrix_miss":1,"review_artifact_missing":4}`.
- West Reservoir remains the accepted typed-blocked quarantine at
  `actual_contract_status="typed_blocked"`.
- Non-strict `promotion-suite` remains red at
  `passed_required_current_result_count=11/32`, but its current-promotion
  contract now fails earlier than the previous snapshot:
  `selector_passed=false`, `matched_slot_count=0`,
  `eligible_slot_count=0`, `passing_slot_count=0`,
  `quorum_passed=false`, and `reference_canary_ready=false`.
- The only suite-level stale artifacts are now
  `phase_eval_core` and `compliance_review_eval`; the same current-promotion
  packet still also lacks passing families for
  `current_review_core_artifacts`,
  `current_review_packet_contract`,
  `current_review_decision_support`,
  `current_review_final_qa`, and
  `current_review_supporting_outputs`.
- Owner-command map recorded for the next repair slice:
  `current_suite_baseline` -> `phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review` and `compliance-review-eval --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --eval-file config/compliance_review_eval_seed.json`
- `current_review_core_artifacts` -> `v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review` plus the ECID replay-context-backed `compliance-review` artifact family when the review outputs themselves are stale
- `current_review_packet_contract` -> `review-packet-index --output-dir source_library --review-id v1-cg-ecid-compliance-review`
- `current_review_decision_support` -> `ea-consistency-document --output-dir source_library --review-id v1-cg-ecid-compliance-review`
- `current_review_final_qa` -> `final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review`
- `current_review_supporting_outputs` -> ECID `compliance-review` for provenance/appendix/resolution/risk artifacts plus `nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id v1-cg-ecid-compliance-review`
- South Plateau slot repair entrypoint -> `v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment` plus the tracked South Plateau replay-context-backed `compliance-review` family when reviewer-ready outputs are stale

### Milestone 1 - ECID Reviewer-Ready Replay Repair

Outcome label: resolved

Purpose: restore the governed ECID current-promotion slot to truthful
reviewer-ready status on the active source set.

Implementation:

1. Repair or regenerate the ECID review-local artifact families that currently
   fail `v1-ea-eval`, including the compliance, matrix/render, packet-index,
   decision-support, final-QA, provenance, review-graph, and phase-eval-linked
   surfaces that feed the governed slot family checks.
2. Update the tracked ECID replay-context or review-eval config only when the
   repair proves the contract itself is correct but the local replay inputs were
   stale.
3. Re-run the ECID packet-local gates until the governed reviewer-ready slot
   is truthful again on aligned reviewer-facing
   `source-set-f70ea11e04ae3d53`.

Acceptance criteria:

- `v1-ea-eval --review-id v1-cg-ecid-compliance-review` reports
  `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `phase-eval --review-id v1-cg-ecid-compliance-review` no longer reports the
  stale current-promotion core artifacts that feed the aggregate suite-level
  checks.
- The repaired packet-local artifacts bind to aligned reviewer-facing
  `source-set-f70ea11e04ae3d53` and the tracked replay-context package
  authority.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_v1_ea_eval.py \
  tests/test_v1_ea_eval_contracts.py \
  tests/test_v1_ea_eval_forest_plan.py \
  tests/test_phase_eval.py -q
```

Milestone 1 live next-slice baseline on 2026-05-26:

- Reviewer-facing source-set alignment is now complete: the ECID replay
  context, `v1-ea-eval` contract, and applicability CLI catalog resolution
  all bind to `source-set-f70ea11e04ae3d53`.
- `applicability-authority-universe --review-id
  v1-cg-ecid-compliance-review` now passes on that aligned source set with
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`, and
  `authority_universe_sha256=33355dce05cb0141840bf5ad6463570173294e6e1a368d0e24f8910961a04554`.
- `applicability-context-build` and `applicability-retrieve` now also pass for
  ECID on the aligned source set.
- Governed replay adjudication is now green for ECID on the aligned source
  set: committed current-review adjudication now lives at
  `config/applicability_adjudications/v1-cg-ecid-compliance-review.json`,
  `applicability-validate --review-id v1-cg-ecid-compliance-review` now
  passes with
  `decision_status_counts={"applicable":55,"not_applicable":341}`,
  `needs_adjudication_authority_count=0`,
  `unresolved_authority_count=0`, and
  `generated_rule_pack_ready=true`, and
  `applicability-generate-rule-pack --review-id v1-cg-ecid-compliance-review`
  now passes with `generated_rule_count=55`.
- ECID `forest_plan_context_summary.json` on the aligned source set is now
  green at the component lane: `reviewer_ready=true`,
  `component_count=329`, `applicable_count=79`,
  `reviewer_resolution_count=0`, `applied_standard_count=12/12`,
  and `validation_passed=true`.
- `forest-plan-components-build --source-set-id source-set-f70ea11e04ae3d53
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  now rebuilds the aligned Custer inventory through `FOR-009` with
  `component_count=329`, `standard_count=58`,
  `coverage_passed=true`, and `component_source_accuracy_passed=true`.
- `forest-plan-component-eval --review-id v1-cg-ecid-compliance-review` now
  passes `35/35`, and `forest-plan-component-eval-coverage` now covers that
  current slot with `passed=true`, `stale_identity=false`, and
  `unresolved_review=false`.
- The committed zero-item ECID adjudication template now lives at
  `config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.json`
  with companion worklist
  `config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.md`,
  and `forest-plan-component-adjudication-eval` now passes with
  `pending_adjudication_count=0`.
- `compliance-review --review-id v1-cg-ecid-compliance-review` now passes on
  `source-set-f70ea11e04ae3d53` with `reviewer_ready=true`,
  `validation_passed=true`, and forest-plan component adjudication/evaluation
  both `reviewer_ready=true`.
- `v1-ea-eval --review-id v1-cg-ecid-compliance-review` now runs on
  `source-set-f70ea11e04ae3d53` and remains `contract_status="mismatch"` with
  `forest_plan_passed=true`, `broader_ea_passed=false`,
  `failure_category_counts={"baseline_source_record_mismatch":26,"conditional_expectation_missing":18,"source_record_mismatch":17}`,
  and `forest_plan_failure_category_counts={}`.
- `phase-eval --review-id v1-cg-ecid-compliance-review` now also runs on
  `source-set-f70ea11e04ae3d53`; it remains red at `15/31` passed phases with
  `review_direct_eval_status="direct_eval_identity_mismatch"`. The remaining
  blocker phases are retrieval, claim extraction, rule-claim binding,
  downstream direct evaluation, decision support, review packet, final QA, and
  aggregate evaluation coverage plus the downstream graph/export families;
  `compliance_review`, `applicability_validation`, generated rule-pack truth,
  and the current ECID component-eval slot are no longer the blocker.
- The next truthful slice is ECID broader-EA review-local artifact /
  source-record alignment on aligned `source-set-f70ea11e04ae3d53`, then
  South Plateau forest-plan replay / adjudication refresh and the remaining
  reviewer-facing packet families.

Milestone 1 closeout update on 2026-05-26:

- ECID broader-EA replay is now also green on reviewer-facing
  `source-set-f70ea11e04ae3d53`: `v1-ea-eval --review-id
  v1-cg-ecid-compliance-review` now reports
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`, and
  `forest_plan_passed=true` with no remaining failure categories.
- The review-local direct-eval family is now present and passing on that same
  source set. Fresh retrieval, claim, and rule-claim direct eval outputs now
  let `phase-eval --review-id v1-cg-ecid-compliance-review` close green at
  `33/33` passed phases with `reviewer_ready=true`,
  `review_direct_eval_status="direct_eval_present"`,
  `missing_direct_eval_phase_count=0`, and
  `threshold_failed_phase_count=0`.
- The remaining packet-local artifact families are now aligned to the live
  ECID packet truth: `review-packet-index` validation is green with
  `failed_check_count=0`; `ea-consistency-document` is green against the live
  `55 applicable / 341 non-applicable / 396 candidate` authority boundary;
  source-set graph evals now pass with `authority_path_count=17`,
  `relationship_type_count=7`, `orphan_node_count=0`, and
  `disconnected_component_count=1`; `draft-generation-eval` now passes `5/5`;
  `final-qa-certification` reruns green with `198` passing checks and
  `machine_replay_status="passed"`; and non-strict `promotion-suite` now
  reports `current_promotion_ready=true`,
  `promotion_ready=true`, and `passed_required_current_result_count=32/32`.
- Promotion truth is now explicit rather than optimistic: the current
  `source-set-f70ea11e04ae3d53` graph is still packet-scoped rather than
  region-complete, so the governed source-set graph contract now expects the
  live `region1_forest_plan_blocked_profile_count=9` instead of the old fake
  zero-blocker assumption.
- Focused regression coverage now also keeps the review-scoped synthetic
  compliance-phase fixtures honest: the shared fixture materializes the
  required extraction-fidelity direct eval so phase-eval tests keep matching
  the governed runtime rather than relying on proxy-only extraction coverage.
- The next truthful slice is now Milestone `2` ECID preliminary-EA
  historical expansion artifact repair or truthful contract reroute, followed
  by Milestone `3` aggregate docs and closeout.

### Milestone 2 - ECID Preliminary Expansion Artifact Repair

Outcome label: reduced

Purpose: repair or truthfully reroute the remaining ECID preliminary-EA
historical expansion review-case artifact family without reopening the now
green South reviewer-ready slot.

Implementation:

1. Repair or regenerate the missing ECID preliminary-EA downstream artifact
   family: `compliance_validation.json`, `compliance_review.json`,
   `compliance_matrix.json`, `compliance_matrix.pdf`,
   `authority_family_provenance.json`, and
   `non_applicable_authority_appendix.json`.
2. If those artifacts cannot be rebuilt truthfully on the historical split
   source-set lane, update the strict-expansion contract/routing surfaces to
   stop claiming they exist while preserving current-promotion and South green
   truth.
3. Re-run the ECID preliminary review case and strict-expansion aggregate gate
   until the remaining blocker is either repaired or explicitly rerouted.

Acceptance criteria:

- `region1-expansion-ecid-preliminary-ea` no longer fails the six missing
  downstream artifacts in `promotion-suite`, or the strict-expansion contract
  is updated truthfully so those artifacts are no longer required there.
- `real-package-review-coverage-eval` remains green throughout the repair.
- If the historical lane cannot be restored with focused replay repair, the
  packet stops and routes a truthful follow-on rather than weakening the
  governed roster in place.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_promotion_suite.py \
  tests/test_real_package_review_coverage_eval.py -q
```

Milestone 2 live next-slice baseline on 2026-05-26:

- South Plateau is no longer the blocker: its governed slot now reports
  `contract_status="reviewer_ready"` and the aggregate coverage gate is green.
- The remaining strict-expansion failure is entirely concentrated in
  `region1-expansion-ecid-preliminary-ea`.
- That historical ECID preliminary lane still carries a split identity:
  `applicability_validation.json` and `phase_eval_results.json` point at
  `source-set-ba8d0feae79501b8`, while
  `generated_rule_pack_validation.json` and the expansion slot contract point
  at `source-set-4fb59e9eb43045cb`.
- The remaining missing artifacts are
  `compliance_validation.json`, `compliance_review.json`,
  `compliance_matrix.json`, `compliance_matrix.pdf`,
  `authority_family_provenance.json`, and
  `non_applicable_authority_appendix.json`.
- A direct `applicability-validate` rerun against today's derived corpus
  reopens broad stale-source-set failures there, so the next truthful slice is
  coherent historical-lane rebuild or strict-expansion contract reroute, not a
  fake local pass.

Milestone 2 closeout update on 2026-05-26:

- The historical ECID preliminary-EA lane is now truthfully rerouted instead
  of falsely reported as a ready slot with six live required artifact misses.
- `config/promotion_suite_v1.json` now keeps applicability validation,
  generated rule-pack validation, forest-plan component adjudication
  template/eval, and review-scoped phase eval as the live required expansion
  evidence for `region1-expansion-ecid-preliminary-ea`, while demoting the six
  absent downstream compliance/provenance artifacts from active
  required-expansion counting on this packet.
- Expansion slot `region1-real-ea-slot-1` now reports
  `status="selected_not_ready"` with
  `failure_category="historical_source_set_split"`, explicit
  `source-set-ba8d0feae79501b8` / `source-set-4fb59e9eb43045cb` split-signal
  evidence, and a next action that routes any future work into a fresh
  standalone follow-on.
- Strict-expansion `promotion-suite` now fails closed only on that selected
  slot with `open_expansion_slot_count=1`, `open_expansion_artifact_count=0`,
  and `failure_category_counts={"historical_source_set_split":1}`.

### Milestone 3 - Aggregate Replay, Docs, And Closeout

Outcome label: reduced

Purpose: prove the repaired review-local slots at the aggregate layer and land
the durable closeout.

Implementation:

1. Re-run the governed real-package review coverage gate and non-strict
   promotion suite.
2. Update operator docs, current-state docs, routing docs, and handoff with the
   repaired live result and any residual risks.
3. Stage only the verified replay-repair slice and close it with one local
   atomic commit.

Acceptance criteria:

- `real-package-review-coverage-eval` passes on the active source set without
  reviewer-ready slot mismatches.
- non-strict `promotion-suite` reports the repaired current-promotion result
  from live review-local artifacts rather than stale slot failures.
- The closeout docs name the exact replay commands, results, residual risks,
  and next routed packet if anything remains open.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_promotion_suite.py \
  tests/test_promotion_suite_current_runtime.py \
  tests/test_promotion_suite_full_canonical.py \
  tests/test_v1_ea_eval.py \
  tests/test_v1_ea_eval_contracts.py \
  tests/test_v1_ea_eval_forest_plan.py \
  tests/test_phase_eval.py \
  tests/test_cli_eval.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
jq empty config/v1_real_package_review_coverage_v1.json config/promotion_suite_v1.json
git diff --check
```

Milestone 3 live alignment update on 2026-05-26:

- `real-package-review-coverage-eval` is now green with
  `reviewer_ready_slot_count=2`, `missing_required_slot_count=0`, and
  `missing_coverage_class_ids=[]`.
- Non-strict `promotion-suite` is again truthful for current promotion with
  `current_promotion_ready=true`, `promotion_ready=true`, and
  `passed_required_current_result_count=32/32`; strict expansion remains red
  only on the ECID preliminary-EA historical selected-not-ready slot with
  `failure_category_counts={"historical_source_set_split":1}`,
  `open_expansion_slot_count=1`, and `open_expansion_artifact_count=0`.
- The durable doc set now reflects that live state:
  `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, `docs/POST_V1_PROMOTION_SUITE.md`, and this plan
  now record the truthful reroute closeout and route any future historical-lane
  blocker work into
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  instead of this packet, while
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  now remains the intermediate predecessor,
  while
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  now remains the exact predecessor closeout and
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
  remains the blocked parent stop-condition record. That successor blocker has
  now completed Milestones 1-3 by ruling out both a bounded historical
  source-set rebuild path and any currently tracked governed replacement path
  under current artifacts, and the replacement-feasibility successor has since
  reduced further into the exact live Lolo source-set contract owner through
  `013b5d1` (`Open Lolo source-set contract blocker`). That active child
  packet then realigned the tracked replay context and review eval contract to
  `5e65...`, reduced Milestone 2 locally in `e2b6941`
  (`Reduce Lolo source-set blocker Milestone 2`), and resolved Milestone 3 by
  routing the remaining red into
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`.
  `README.md` was checked and remains intentionally unchanged because it
  delegates volatile replay truth to the current-state docs instead of
  duplicating it.

## Required Implementation Artifacts

- repaired or truthfully rerouted ECID preliminary-EA historical expansion
  review-case artifact family
- any manifest or contract updates required to keep ECID current promotion and
  South Plateau reviewer-ready truth stable while the historical lane is
  handled
- focused regression coverage for any repaired or rerouted aggregate-contract
  edge case
- updated docs and handoff that record the repaired or rerouted aggregate
  result

## Required Documentation And Handoff Updates

- `README.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan

## Required Verification Gates

- `real-package-review-coverage-eval`
- non-strict `promotion-suite`
- strict-expansion `promotion-suite`
- targeted `region1-expansion-ecid-preliminary-ea` replay or contract checks
  when the historical review-case lane is touched
- slot-level `v1-ea-eval` or `phase-eval` replays for ECID and South only if a
  change risks reopening the already-green reviewer-ready slots
- focused `pytest` coverage for real-package coverage, promotion suite,
  `v1_ea_eval`, phase-eval, CLI, and architecture boundaries when touched
- `ruff check src tests`, `compileall`, and `git diff --check` when code or
  config owners change; `git diff --check` always

## Acceptance Criteria

- The packet closes only if the governed reviewer-ready slots again tell the
  truth on aligned reviewer-facing `source-set-f70ea11e04ae3d53`.
- Aggregate green must come from repaired review-local evidence, not easier
  slot requirements.
- West Reservoir remains an explicit typed-blocked quarantine and does not
  silently absorb the reviewer-ready gap.
- Docs and handoff describe the repaired live replay result without claiming
  the contract refactor itself was the blocker.

## Stop Conditions

- Stop if the truthful fix requires lowering reviewer-ready requirements,
  deleting required coverage classes, or otherwise reopening the real-package
  contract instead of repairing the review-local artifacts.
- Stop if packet-local replay repair would require a broader downloader/catalog
  or full-canonical corpus rerun that exceeds this packet's scope.
- Stop if the repaired artifacts cannot be rebound to the active source set or
  tracked package authority.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked
  complete, `resolved`, or `reduced` until verification passes, durable
  docs/handoff updates land, and the local atomic commit exists. A verified
  but uncommitted slice is only ready-to-close.
- Keep the repair packet review-local and atomic.
- Stage only the verified replay-repair slice: tracked config, focused code or
  tests if needed, docs, and handoff updates.
- Do not stage ignored `source_library/` outputs unless repository policy
  changes or the user explicitly approves it.
- Commit locally at the end of the repaired milestone sequence. Do not leave a
  verified but uncommitted milestone behind.
- Preserve anti-test-weakening rules: do not weaken or loosen gates, skip
  checks, or delete negative coverage to make the closeout pass.

## Residual Risks And Next Routing

- ECID and South Plateau may expose different repair depths even though they
  currently surface together at the aggregate layer.
- If either slot proves no longer reviewer-ready for truthful reasons, open a
  fresh contract or roster-routing packet rather than weakening this replay
  repair plan in place.
