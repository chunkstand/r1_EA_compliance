# Current Routing

Date: 2026-05-21

Use this file as the short current route before opening the large append-only docs.

## First Stops

- Document-routing work: `docs/AGENT_START_HERE.md`
- Live system truth: `README.md`, then `docs/CURRENT_SYSTEM_STATE.md`
- Recent closeout and next slice: `docs/SESSION_HANDOFF.md`
- Active architecture packet: `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`

## Live Facts

- Active workbook: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Active workbook table: `Document_Register_Master`
- Live local catalog: `source-set-f775524ab233ff27`
- Architecture gate: `344` code files, `24` above `800` lines, no Python or JS/TS cycles, and no
  local module above the `20`-import fan-out gate

## Current Architecture Route

- The overall architecture umbrella is resolved after Milestone 10 Sequence 52.
- `config/replay_contexts/west-reservoir-67436.json` now uses the repo-relative cached package path
  `source_library/reviews/west-reservoir-67436/package` instead of a user-home path.
- West Reservoir is now an explicit `typed_blocked` replay quarantine rather than a claimed
  reviewer-ready replay contract because the broader-EA and forest-plan review artifact families are
  not reproducible from current repo-local state.
- Fresh full-canonical `compliance-gold-eval` replay on `source-set-f775524ab233ff27` is red on
  `14/14` cases even though the required coverage and package-style tags are present.
- Next routed packet: `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`.

## Deep Reads

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
