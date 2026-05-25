# Real Package Review Replay Repair Milestone Plan

Date: 2026-05-25

Status: Milestone 1 reduced locally

Owner context: this is a fresh standalone follow-on packet opened after
`docs/PROMOTION_SUITE_SLOT_DRIVEN_CONTRACT_MILESTONE_PLAN.md` closed through
Milestone `4`. It owns review-local replay repair for the governed real-package
slots on active source set `source-set-4fb59e9eb43045cb`. It does not reopen
the slot-driven promotion-suite contract architecture, the full-canonical
source-set contract, or the West Reservoir typed-blocked quarantine. This
packet is complete only after the required review-local slots are replayed back
to truthful reviewer-ready state, the aggregate replays are rerun, durable docs
and handoff are updated, and one local atomic closeout commit lands. A verified
but uncommitted slice is only ready-to-close.

## Purpose

Repair the live review-local replay debt now exposed by the slot-driven
contract closeout.

The promotion-suite contract packet is done: the aggregate gate now chooses the
current-promotion lane from governed slots instead of one hard-coded review
packet. The remaining red is no longer contract architecture drift. It is
review-local replay drift inside the governed reviewer-ready slots:

- East Crazies current promotion no longer satisfies its tracked
  `v1-ea-eval` contract on the active source set
- South Plateau no longer satisfies its governed reviewer-ready expansion slot
- the aggregate real-package and promotion-suite replays stay red until those
  packet-local artifacts are refreshed or honestly fail closed

This packet exists to repair those review-local artifact families without
weakening the governed slot roster or reopening the contract refactor.

## Current Evidence

- `source_library/reviews/real_package_review_coverage_eval/real_package_review_coverage_eval_results.json`
  reports `passed=false`, `reviewer_ready_slot_count=0`,
  `missing_required_slot_count=2`, and
  `failure_category_counts={"insufficient_reviewer_ready_slots":1,"missing_required_coverage_class":2,"missing_required_slot":1,"slot_contract_status_mismatch":2}`.
- The ECID governed slot `east-crazies-current-promotion` currently reports
  `actual_contract_status="mismatch"`, `broader_ea_passed=false`,
  `forest_plan_passed=false`, and
  `failure_category_counts={"baseline_source_record_missing":26,"citation_requirement_miss":4,"forest_plan_matrix_miss":1,"review_artifact_missing":4,"rule_section_mismatch":8}`.
- The South Plateau governed slot `south-plateau-reviewer-ready` currently
  reports `actual_contract_status="mismatch"`, `broader_ea_passed=false`,
  `forest_plan_passed=false`, and
  `failure_category_counts={"forest_plan_matrix_miss":1,"review_artifact_missing":4}`.
- West Reservoir still truthfully reports
  `actual_contract_status="typed_blocked"` and remains outside the repair
  target for this packet.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  reports `full_canonical_corpus_ready=true`,
  `current_promotion_ready=false`, `promotion_ready=false`,
  `expansion_ready=false`, `passed_required_current_result_count=11`,
  `required_current_result_count=32`, and
  `failure_category_counts={"adjudication_needed":1,"graph_stale_artifact":1,"missing_matrix_render_row":1,"missing_packet_index_row":1,"stale_artifact":5,"unsupported_package_evidence":2}`.
- The same promotion-suite result now fails closed at the selector layer
  because the governed reviewer-ready slot result itself is mismatched:
  `current_promotion_contract.selector_passed=false`,
  `matched_slot_count=0`, `eligible_slot_count=0`,
  `passing_slot_count=0`, `quorum_passed=false`,
  `reference_canary_ready=false`, and
  `failure_category_counts={"stale_artifact":1,"unsupported_package_evidence":1}`.
  The red state still belongs to review-local replay debt, not to selector or
  quorum code drift.

## Goal

Restore truthful reviewer-ready replay status for the governed ECID and South
Plateau slots on `source-set-4fb59e9eb43045cb` so the aggregate
`real-package-review-coverage-eval` and non-strict `promotion-suite` replays
stop failing on stale or missing packet-local artifacts.

Completion means all of the following are true:

- `v1-ea-eval --review-id v1-cg-ecid-compliance-review` again satisfies the
  governed reviewer-ready contract on the active source set.
- `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment`
  again satisfies the governed reviewer-ready expansion contract on the active
  source set.
- `real-package-review-coverage-eval` no longer reports reviewer-ready slot
  mismatches for those governed slots.
- non-strict `promotion-suite` reports current-promotion truth from the active
  replayed artifacts rather than stale review-local failures.

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

- ECID review-local replay repair on the active source set
- South Plateau review-local replay repair on the active source set
- tracked replay-context and review-eval config alignment for those two slots
- aggregate replay confirmation for
  `real-package-review-coverage-eval` and non-strict `promotion-suite`
- focused docs and handoff updates that describe the repaired live result

## Out Of Scope

- a broader roster redesign for `config/v1_real_package_review_coverage_v1.json`
- changing expansion policy or strict-expansion semantics
- Lolo, queue, downloader, or forest-specific example-package work
- full-canonical source-set rebinds or corpus refreshes

## Owner Surfaces

- governed review-slot contracts:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`
- tracked replay context:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`
- packet-local review owners that may need focused replay or contract repair:
  `config/ea_consistency_decision_support_v1.json`,
  `config/east_crazies_final_qa_certification_v1.json`,
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/promotion_suite.py`,
  and the matching review-local artifact families under
  `source_library/reviews/<review_id>/`
- focused tests and fixtures:
  `tests/test_v1_ea_eval.py`,
  `tests/test_v1_ea_eval_contracts.py`,
  `tests/test_v1_ea_eval_forest_plan.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`,
  `tests/test_promotion_suite_current_runtime.py`,
  `tests/test_promotion_suite_full_canonical.py`,
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

- Weak point forecast: ECID is repaired but South Plateau is left mismatched,
  so the repo reports a smaller blocker while the governed coverage gate stays
  red.
  Owner surface:
  `source_library/reviews/real_package_review_coverage_eval/`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `tests/test_real_package_review_coverage_eval.py`
  Prevention gate: packet closeout requires both governed reviewer-ready slots
  to satisfy their contracts, not only the current-promotion slot.
  Fail threshold: ECID is green but `real-package-review-coverage-eval` still
  reports a South Plateau mismatch.
  Controlled violation: rerun the aggregate after only ECID repair; the packet
  must remain open.
  Future-Codex misuse scenario: a future agent optimizes for current promotion
  only and leaves aggregate slot truth broken; the aggregate gate must fail.

- Weak point forecast: the repair work expands into unnecessary corpus or
  downloader reruns and obscures the review-local root cause.
  Owner surface: this plan, `docs/SESSION_HANDOFF.md`, and the replay-context
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

- Weak point forecast: regenerated review artifacts still point at stale source
  set or package-authority context, so the same mismatch returns on the next
  replay.
  Owner surface:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`,
  `tests/test_v1_ea_eval_contracts.py`,
  `tests/test_phase_eval.py`
  Prevention gate: packet-local replay verification must prove the repaired
  artifacts bind to `source-set-4fb59e9eb43045cb` and the tracked package
  authority before aggregate closeout.
  Fail threshold: slot-level reruns pass locally but still emit stale
  source-set or package-authority signals into aggregate gates.
  Controlled violation: point a replay-context fixture at the wrong source set;
  the contract tests must fail closed.
  Future-Codex misuse scenario: a later agent refreshes files in place without
  checking replay-context binding; the contract tests must catch the drift.

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
  `current_suite_baseline` -> `phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review` and `compliance-review-eval --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb --eval-file config/compliance_review_eval_seed.json`
- `current_review_core_artifacts` -> `v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review` plus the ECID replay-context-backed `compliance-review` artifact family when the review outputs themselves are stale
- `current_review_packet_contract` -> `review-packet-index --output-dir source_library --review-id v1-cg-ecid-compliance-review`
- `current_review_decision_support` -> `ea-consistency-document --output-dir source_library --review-id v1-cg-ecid-compliance-review`
- `current_review_final_qa` -> `final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review`
- `current_review_supporting_outputs` -> ECID `compliance-review` for provenance/appendix/resolution/risk artifacts plus `nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb --review-id v1-cg-ecid-compliance-review`
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
   is truthful again on `source-set-4fb59e9eb43045cb`.

Acceptance criteria:

- `v1-ea-eval --review-id v1-cg-ecid-compliance-review` reports
  `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `phase-eval --review-id v1-cg-ecid-compliance-review` no longer reports the
  stale current-promotion core artifacts that feed the aggregate suite-level
  checks.
- The repaired packet-local artifacts bind to
  `source-set-4fb59e9eb43045cb` and the tracked replay-context package
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

Milestone 1 reduction on 2026-05-25:

- The applicability universe owner now correctly narrows the active Region 1
  batch component inventory to the ECID review forest and now resolves mapped
  legacy authority source IDs against the active catalog surface.
- `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now rebuilds `candidate_authority_count=396` with
  `forest_plan_component_candidate_count=329` on
  `source-set-4fb59e9eb43045cb`, so the old `0`-component universe bug is no
  longer the blocker.
- The packet still cannot continue truthfully to reviewer-ready replay because
  the active authority-universe validation now fails only on
  `candidates_have_source_evidence_available` (`failure_count=21`) and
  `authority_family_template_candidates_cover_config`
  (`missing_source_record_count=19`).
- Milestone `0` of
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md` is now
  resolved locally; it freezes that blocker inventory as `21` failing
  source-evidence candidates and `19` missing source-record template groups.
- The next truthful slice is now Milestone `1` of
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`, which
  owns governed blocker classification upstream of packet-local replay.

### Milestone 2 - South Plateau Reviewer-Ready Replay Repair

Outcome label: resolved

Purpose: restore the governed South Plateau reviewer-ready expansion slot to
truthful reviewer-ready status on the active source set.

Implementation:

1. Repair or regenerate the South Plateau review-local artifact families that
   currently fail the governed slot, especially the review-artifact and
   forest-plan matrix surfaces.
2. Update the tracked South Plateau replay-context or review-eval config only
   when the repair proves the contract is still right but the local replay
   state was stale.
3. Re-run the South Plateau packet-local gate until the reviewer-ready slot is
   truthful again on `source-set-4fb59e9eb43045cb`.

Acceptance criteria:

- `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment`
  reports `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- The slot no longer reports `forest_plan_matrix_miss` or
  `review_artifact_missing` in the aggregate coverage gate.
- If the slot cannot be restored with focused replay repair, the packet stops
  and opens a fresh contract/routing follow-on instead of weakening the
  governed roster in place.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_v1_ea_eval.py \
  tests/test_v1_ea_eval_contracts.py \
  tests/test_v1_ea_eval_forest_plan.py \
  tests/test_real_package_review_coverage_eval.py -q
```

### Milestone 3 - Aggregate Replay, Docs, And Closeout

Outcome label: resolved

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

## Required Implementation Artifacts

- repaired ECID review-local artifact family on the active source set
- repaired South Plateau review-local artifact family on the active source set
- any tracked replay-context or review-eval config updates required to keep the
  reviewer-ready slots truthful
- focused regression coverage for any repaired slot-contract edge case
- updated docs and handoff that record the repaired aggregate result

## Required Documentation And Handoff Updates

- `README.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan

## Required Verification Gates

- slot-level `v1-ea-eval` replays for ECID and South Plateau
- ECID `phase-eval --review-id` replay when its suite-level artifact family is
  touched
- `real-package-review-coverage-eval`
- non-strict `promotion-suite`
- focused `pytest` coverage for `v1_ea_eval`, real-package coverage, promotion
  suite, CLI, phase-eval, and architecture boundaries when touched
- `ruff check src tests`, `compileall`, and `git diff --check`

## Acceptance Criteria

- The packet closes only if the governed reviewer-ready slots again tell the
  truth on `source-set-4fb59e9eb43045cb`.
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

- Keep the repair packet review-local and atomic.
- Stage only the verified replay-repair slice: tracked config, focused code or
  tests if needed, docs, and handoff updates.
- Do not stage ignored `source_library/` outputs unless repository policy
  changes or the user explicitly approves it.
- Commit locally at the end of the repaired milestone sequence. Do not leave a
  verified but uncommitted milestone behind.

## Residual Risks And Next Routing

- ECID and South Plateau may expose different repair depths even though they
  currently surface together at the aggregate layer.
- If either slot proves no longer reviewer-ready for truthful reasons, open a
  fresh contract or roster-routing packet rather than weakening this replay
  repair plan in place.
