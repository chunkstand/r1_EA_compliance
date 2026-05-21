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
- The gold packet now routes `expected_generated_*` gold cases into the generated-rule-pack eval
  path again; the older `14/14` rule/retrieval failure bundle was diagnostic noise from the
  base-rule-pack rerun path.
- Fresh full-canonical `compliance-gold-eval` replay on `source-set-f775524ab233ff27` now fails
  through a scored `generated_rule_pack_diagnostic` lane instead of aborting at applicability
  validation. The legacy-to-canonical source-record reconciliation slice now drives
  `authority_trace_coverage_rate=1.0`, and `gold-all-authorities-supported` no longer collapses to
  all `uncertain`: it now scores `39` live `pass` findings and `20` `uncertain` findings.
  The remaining source-record/document-role mismatches are limited to five still-unmapped
  authorities:
  `apa_final_agency_action`,
  `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`,
  `organic_act_16usc_475`, and
  `seven_county_nepa_scope`.
  Review-time source-claim-link mismatches remain routed next, and the bounded
  `gold_coverage_eval_seq52_fix4` replay still remains red only because `compliance_gold_failed=1`.
- Next routed packet: `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`.

## Deep Reads

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
