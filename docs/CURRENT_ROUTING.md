# Current Routing
Date: 2026-05-27
Use this file as the short current route before opening the append-only docs.
## New Session Start
- Read this file first, then the top of `docs/SESSION_HANDOFF.md`, then `docs/CURRENT_SYSTEM_STATE.md`.
- Active packet:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- Historical lineage only:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
## Active Route
- Source-record identity reconciliation Milestones 2-3 are resolved locally in
  `e28b373` (`Rebaseline Lolo replay on current source set`). The tracked Lolo replay context,
  `v1-ea-eval` contract, applicability adjudication, forest-plan component eval
  contract, and forest-plan component adjudication now consume
  `source-set-f70ea11e04ae3d53` through
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`.
- The final Lolo source-record identity gate on the current `f70...` catalog
  returns `passed=true`, `expected_source_record_count=59`,
  `catalog_covered_source_record_count=59`,
  `identity_resolved_source_record_count=59`, no unmapped IDs, no absent mapped
  targets, and `ambiguous_mappings={}`. The expected count is now `59` because
  the Lolo v1 eval contract removed the legacy duplicate forest-plan source
  `R1PLAN-lolo-nf-02`; current replay uses `FPS-298`.
- The governed replay chain is green on `source-set-f70ea11e04ae3d53`:
  applicability validates with `54` applicable and `342` non-applicable
  authorities; the generated rule pack has `54` rules; compliance review is
  `reviewer_ready=true` with `scope_status="lolo_nf"`; forest-plan component
  eval and component adjudication eval pass; `v1-ea-eval` reports
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`, and
  `forest_plan_passed=true`; review `phase-eval` passes `28/28` with
  `blockers=[]`, `identity_mismatch_phase_count=0`, and
  `review_direct_eval_status="not_required_for_ad_hoc_review"`.
- The source-register currentness, current-workbook source-set rebaseline,
  source-record identity, and aligned-runtime blocker family is now historical
  for Lolo. Do not route new work back there unless a future command regresses
  one of the verified gates.
- The next Lolo owner, if continuing this lane, is the broader
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` Milestone 3:
  registry promotion, aggregate threshold ratchet, and queue/coverage updates
  needed to move `lolo-nf` out of `profile_eval_guidance_only`. That promotion
  is not part of this closeout and must run the governed aggregate gates before
  any roster/status change.
- Forest-plan component eval coverage is not a blocker for this Lolo replay
  closeout: the Lolo slot is now aligned and passes on `f70...`. The aggregate
  `forest-plan-component-eval-coverage` command still fails on non-Lolo
  source-delta and West Reservoir slots (`covered_review_count=2/4`,
  `stale_identity_count=1`, `unresolved_review_count=2`), so do not describe
  aggregate component coverage as green.
- Aggregate truth:
  ECID current promotion and South Plateau reviewer-ready expansion remain
  green; strict expansion remains blocked only on the ECID historical slot
  under `historical_source_set_split`.
- Do not flip the ECID historical slot to `ready`, admit Lolo into the
  governed roster without the next parent-packet aggregate gates, or reopen the
  older Lolo or replay-repair packets as live runtime work.
## Deep Reads
- Core:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Architecture and document routing:
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`, `docs/AGENT_START_HERE.md`
