# Current Routing
Date: 2026-05-27
Use this file as the short current route before opening the append-only docs.
## New Session Start
- Read this file first, then the top of `docs/SESSION_HANDOFF.md`, then `docs/CURRENT_SYSTEM_STATE.md`.
- Active packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- Historical lineage only:
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
## Active Route
- Source-set contract blocker Milestone 3 and aligned-runtime Milestones 0-1
  are now resolved/reduced locally.
- Tracked Lolo replay context and review eval contract stay aligned to the
  `5e65...` owner path, and fresh `v1-ea-eval` remains `reviewer_ready`.
- Milestone 1 of the aligned-runtime packet refreshed the governed
  review-local applicability chain and forest-plan component eval on
  `5e65...`; `phase-eval` improved to `18/23`.
- Source-register currentness Milestones 0-2 are resolved locally by stop:
  no exact current `5e65...` manifest exists, the historical `5e65...`
  currentness report points at a missing historical manifest hash, and the
  current-workbook `f70...` catalog gate is not source-set compatible with the
  `5e65...` derived artifacts.
- Current-workbook source-set rebaseline Milestone 0 is reduced locally:
  `f70...` is a current-workbook catalog candidate, not a drop-in owner for
  `5e65...`; `5e65...` selected `350` source-record IDs while `f70...`
  catalogs `708`, with an `R1EA-*` versus `FED-*` identity split.
- Current-workbook source-set rebaseline Milestone 1 is reduced locally by exact
  stop: the applicability replay CLI rejects an ad hoc `f70...` source-set
  override while tracked Lolo replay context remains on `5e65...`, and the
  remaining blocker is split source-record identity. The Lolo v1 eval contract
  expects 60 source-record IDs; 8 are direct `f70...` catalog hits, 51 absent
  IDs are covered by compliance source-record reconciliation, and
  `R1PLAN-lolo-nf-02` is separately covered by forest-plan identity
  reconciliation as `FPS-298`; five compliance-covered IDs are still
  multi-target mappings that need a replay-facing identity rule.
- Source-record identity reconciliation Milestone 1 is resolved locally: the
  generic `source-record-identity-gate` now owns replay-facing identity
  resolution across direct catalog IDs, compliance source-record aliases, and
  forest-plan source aliases. `config/compliance_source_record_reconciliation_v1.json`
  now uses explicit `identity_source_record_id` selectors for the five former
  multi-target mappings: `R1EA-018 -> USDA-007`, `R1EA-028 -> USDA-008`,
  `R1EA-124 -> FED-011`, `R1EA-137 -> FED-032`, and
  `R1EA-150 -> USFS-035`.
- Against the current `f70...` catalog, the Lolo gate now returns
  `passed=true`, with all `60` expected IDs covered and exactly resolved, no
  unmapped IDs, no absent mapped targets, and `ambiguous_mappings={}`.
- Next slice remains inside the source-record identity reconciliation packet at
  Milestone 2: update the tracked Lolo replay/eval config surfaces to consume
  the current-workbook identity owner, or stop at the exact replay/eval command
  that cannot consume it. Tracked replay context, eval config, adjudication
  config, and ignored generated review artifacts still have not moved from
  `5e65...` to `f70...`.
- Remaining live debt:
  `retrieval-eval` on `5e65...` is both contract-stale and semantically red;
  `rule-claim-eval` on `5e65...` is contract-stale but otherwise green; shared
  `compliance-review-eval` still passes only on `f70...`;
  `source_register_contract` still fails active-workbook SHA currentness
  against the global `4fb...` manifest; `evaluation_coverage` remains red
  because retrieval and rule-claim direct-eval identity still mismatch.
- Aggregate truth:
  ECID current promotion and South Plateau reviewer-ready expansion remain
  green; strict expansion remains blocked only on the ECID historical slot
  under `historical_source_set_split`.
- Do not flip the ECID historical slot to `ready`, admit Lolo into the
  governed roster, or reopen the older Lolo or replay-repair packets as live
  runtime work.
## Deep Reads
- Core:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Architecture and document routing:
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`, `docs/AGENT_START_HERE.md`
