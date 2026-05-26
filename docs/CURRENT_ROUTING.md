# Current Routing
Date: 2026-05-26
Use this file as the short current route before opening the append-only docs.
## New Session Start
- Read this file first, then the top of `docs/SESSION_HANDOFF.md`, then
  `docs/CURRENT_SYSTEM_STATE.md`.
- Open `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
  when continuing implementation on the remaining ECID preliminary historical
  lane. Open
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` only as the
  resolved predecessor packet when you need its historical closeout context.
## Active Route
- Active packet:
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
- Live next slice:
  Sequence 0 fail-closed slot gating is now landed, but the packet is
  currently blocked after fresh rebaseline proving on 2026-05-26. The next
  truthful slice is to open a dedicated blocker follow-on for the ECID
  preliminary historical lane rather than flipping the slot to `ready`,
  shrinking the manifest, or reopening
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- Aggregate truth:
  ECID current promotion and South Plateau reviewer-ready expansion are
  green; non-strict `promotion-suite` is `current_promotion_ready=true` and
  `promotion_ready=true`; strict expansion now fails only because the ECID
  preliminary-EA historical slot is truthfully `selected_not_ready` with
  `failure_category="historical_source_set_split"` (`1` open expansion slot,
  `0` open expansion artifacts`). Fresh Sequence 1 proving also found that the
  old `ba8...` closure assumption is stale under current artifacts, `4fb...`
  remains phase-eval red, and the tracked Lolo replacement candidate is not
  phase-eval-ready
- Document-routing entrypoint: `docs/AGENT_START_HERE.md`
- Live architecture state:
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `docs/ARCHITECTURE.md`, and `config/architecture_large_file_inventory_v1.json`
## Deep Reads
- Core: `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `docs/ARCHITECTURE.md`
- Follow-ons:
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`,
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`,
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
