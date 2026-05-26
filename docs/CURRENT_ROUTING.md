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
  start with Sequence 0 in
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`:
  rebaseline the split `ba8...` / `4fb...` ECID preliminary historical lane,
  then choose one truthful closure path: coherent one-source-set rebuild or
  governed ready-slot replacement
- Aggregate truth:
  ECID current promotion and South Plateau reviewer-ready expansion are
  green; non-strict `promotion-suite` is `current_promotion_ready=true` and
  `promotion_ready=true`; strict expansion now fails only because the ECID
  preliminary-EA historical slot is truthfully `selected_not_ready` with
  `failure_category="historical_source_set_split"` (`1` open expansion slot,
  `0` open expansion artifacts)
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
