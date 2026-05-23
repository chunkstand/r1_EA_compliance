# Current Routing
Date: 2026-05-23
Use this file as the short current route before opening the large append-only docs.
## First Stops

- Document-routing work: `docs/AGENT_START_HERE.md`
- Live system truth: `README.md`, then `docs/CURRENT_SYSTEM_STATE.md`
- Recent closeout and next slice: `docs/SESSION_HANDOFF.md`
- Active upstream packet: `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`
- Recent source-truth closeout: `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- Recent gold closeout: `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`
- Active queue follow-on:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
## Live Facts

- Active workbook/table/catalog: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` /
  `Document_Register_Master` / `source-set-f775524ab233ff27`
- Active source-truth packet status: the full canonical source-truth
  rebaseline is now resolved locally; the latest worktree slice makes the `53`
  `currentness_supersession_archive` rows explicit governed full-canonical
  lineage outside verified admission, keeps `USFS-026` archived with
  replacement `USFS-023`, closes in commit `93a23b0`
  (`Resolve source-truth archive boundary rebaseline`)
- Active canonical-source truth: the live source set proves `634/634`
  extracted `Document_Register_Master` rows, and the refreshed
  `canonical-source-register-active-current-admission` boundary now admits all
  `581/581` `active_review_corpus` rows while explicitly keeping `53`
  archive/currentness rows outside the verified-admission roster;
  `retrieval-build` now reports `validation_passed=true`,
  `reviewer_ready=true`,
  `verified_extraction_explicitly_non_admitted_source_count=53`, and
  `promotion-suite` now reports `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`, `expansion_ready=true`, and
  `promotion_ready=true`
- Architecture gate: `462` code files, `0` above `800` lines, no Python or JS/TS cycles, no
  local module above the `20`-import fan-out gate, and the oversized-file inventory is empty
- Under-`800` follow-on: Milestones `0-9` are resolved; the repo remains at `0` oversized code
  files, and this packet is now historical closeout only
- The overall architecture umbrella is resolved after Milestone 10 Sequence 52.
- West Reservoir stays an explicit `typed_blocked` replay quarantine.
- Downstream gold packet status: the full canonical compliance-gold
  rebaseline is now resolved locally on `source-set-f775524ab233ff27`;
  refreshed claims record `claim_count=124458`, `source_record_count=539`,
  `validation_passed=true`, `reviewer_ready=true`, and the closeout lands in
  commit `8e0e02b` (`Resolve full canonical compliance gold rebaseline`)
- Default `compliance-gold-eval` now passes `14/14` adjudicated cases with
  `status_match_rate=1.0`, `source_record_match_rate=1.0`,
  `source_document_role_match_rate=1.0`,
  `source_claim_link_match_rate=1.0`, and
  `package_evidence_match_rate=1.0`; the five still-unmapped authorities now
  remain explicit `uncertain` package-only adjudication rather than false
  source-backed misses, and `promotion_ready=false` only because the base
  `nepa-ea-v0` rule pack is diagnostic rather than reviewer-ready
- Default `gold-coverage-eval` now passes with `7/7` required themes,
  `19/19` mapped high-priority families, `3` required review contracts,
  `2` forests, `3` package styles, `2 reviewer_ready + 1 typed_blocked`
  tracked reviews, and zero threshold failures
- Next routed follow-on: `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`
  owns the next standard raise for import/extraction truth. Milestones `0`
  through `3` are now resolved locally: the contract substrate still defines
  `12` governed fidelity families and `24` tracked cases under
  `config/extraction_fidelity_eval_v1.json`, the dedicated
  `extraction-fidelity-eval` producer still writes durable results under
  `source_library/evaluations/extraction_fidelity/`, `upstream-eval` is now
  narrowed to the capture/catalog umbrella with `required_lane_count=2`,
  `required_category_count=8`, `case_count=16`, and
  `matched_case_count=16`, and full-canonical `promotion-suite` now requires
  the dedicated extraction-fidelity artifact directly, raising the live
  full-canonical baseline to `10/10` required results passing. The current
  green replay still records `matched_case_count=24`,
  `parser_route_mismatch_count=1`, `anchor_mismatch_count=13`,
  `span_mismatch_count=10`, `boundary_mismatch_count=4`, and
  `negative_case_pass_count=12`, while the live `extraction-accuracy-audit`
  remains green at `581/581` admitted active-current rows. Milestone `4` is
  the next routed slice: rerun the live audit plus the strengthened
  upstream/promotion route and finish packet closeout/alignment.
- Active queue follow-on: the source-truth/gold lane remains resolved, but
  `51` `Direct_File_Capture_Queue` rows still remain outside the active
  load-bearing surface by workbook contract. That work is now explicitly
  routed through
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  rather than left as an ownerless boundary. West Reservoir remains an
  intentional `typed_blocked` replay quarantine rather than a promotion
  blocker
- Historical `source-set-cac9c7d02b280825` / `source-set-9e7d85759951c279`
  downstream packets in
  `docs/FULL_CANONICAL_DOWNSTREAM_FRESHNESS_REFRESH_MILESTONE_PLAN.md` and
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md` are
  preserved blocker context only; do not treat their reduced status lines as
  live routing. The latest docs-only retirement closeout is `4cf9451`
  (`Retire stale downstream freshness routing`)
## Deep Reads

- `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`
- `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md` for the zero-oversized architecture closeout
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
