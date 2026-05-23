# Current Routing
Date: 2026-05-22
Use this file as the short current route before opening the large append-only docs.
## First Stops

- Document-routing work: `docs/AGENT_START_HERE.md`
- Live system truth: `README.md`, then `docs/CURRENT_SYSTEM_STATE.md`
- Recent closeout and next slice: `docs/SESSION_HANDOFF.md`
- Active source-truth packet: `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
## Live Facts

- Active workbook/table/catalog: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` /
  `Document_Register_Master` / `source-set-f775524ab233ff27`
- Active source-truth packet status: Milestone `2` remains reduced; a follow-on
  handbook-wrapper slice now admits `9` additional legacy USFS directive rows,
  and the next routed slice remains Milestone `2` on the remaining `13`
  direct-document blockers through local commit `4650837`
  (`Reduce source-truth Milestone 2 handbook wrapper blockers`)
- Active canonical-source mismatch: the live source set proves `634/634` extracted
  `Document_Register_Master` rows, and the current worktree now rebaselines verified admission to
  all `582` `active_review_corpus` rows through
  `canonical-source-register-active-current-admission`; the latest refreshed audit and retrieval
  replays record `569` admitted, `582` required, and `13` explicitly blocked active-current rows:
  `12` Official USFS manual/source-page wrappers plus `USFS-026`, whose live directives entry now
  exposes only a transmittal link rather than a current contents page,
  while `51` `Direct_File_Capture_Queue` rows remain outside the active load-bearing surface and
  the `52` archive rows still await Milestone `3` lineage closure
- Architecture gate: `462` code files, `0` above `800` lines, no Python or JS/TS cycles, no
  local module above the `20`-import fan-out gate, and the oversized-file inventory is empty
- Under-`800` follow-on: Milestones `0-9` are resolved; the repo remains at `0` oversized code
  files, and this packet is now historical closeout only
- The overall architecture umbrella is resolved after Milestone 10 Sequence 52.
- West Reservoir stays an explicit `typed_blocked` replay quarantine.
- Downstream gold packet truth: generated diagnostic gold cases now build non-zero rule-claim-link
  artifacts, while the base `nepa-ea-v0` rule-claim-link summary remains a separate zero-link
  structural surface
- Fresh bounded `compliance-gold-eval` replay on `source-set-f775524ab233ff27` remains red at
  `0/14`; `authority_trace_coverage_rate=1.0`; `gold-all-authorities-supported` still scores
  `39 pass / 20 uncertain` and now records `rule_claim_link_count=200`.
- Remaining owner is the five still-unmapped live authorities only
  (`apa_final_agency_action`, `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`, `organic_act_16usc_475`,
  and `seven_county_nepa_scope`); the earlier review-time source-claim-link expectation drift is
  closed, but that packet is now downstream of the source-truth rebaseline because the live
  verified-admission target is still blocked at `569/582` admitted current rows rather than a
  fully admitted canonical Region 1 corpus.
## Deep Reads

- `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`
- `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md` for the zero-oversized architecture closeout
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
