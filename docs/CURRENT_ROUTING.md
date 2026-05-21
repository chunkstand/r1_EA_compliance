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

- Milestone 9 is active after Sequence 50.
- `config/replay_contexts/west-reservoir-67436.json` now uses the repo-relative cached package path
  `source_library/reviews/west-reservoir-67436/package` instead of a user-home path.
- The remaining West Reservoir blocker is broader-EA artifact drift:
  `v1-ea-eval --review-id west-reservoir-67436` still reports missing
  `authority_explanation_paths.json`, and a cache-backed `compliance-review` reentry is blocked
  because the archived `source-set-5e65d845ce77e1a0` retrieval index is not reviewer-ready in this
  checkout.
- Next slice: restore that archived broader-EA artifact from a repo-local replay path or
  explicitly retire/quarantine the stale reviewer-ready contract before Milestone 10 rebaseline.

## Deep Reads

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
