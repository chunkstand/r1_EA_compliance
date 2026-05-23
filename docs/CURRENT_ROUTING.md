# Current Routing
Date: 2026-05-23
Use this file as the short current route before opening the large append-only docs.

## First Stops

- Document-routing work: `docs/AGENT_START_HERE.md`
- Live system truth: `README.md`, then `docs/CURRENT_SYSTEM_STATE.md`
- Recent closeout and next slice: `docs/SESSION_HANDOFF.md`
- Recent upstream closeout:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`
- Recent source-truth closeout: `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- Recent gold closeout: `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`
- Next executable packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`

## Live Facts

- Active workbook/table/catalog: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` /
  `Document_Register_Master` / `source-set-3f7d4578cafb0704`
- Active source-truth packet status: the full canonical source-truth
  rebaseline remains historically resolved in commit `93a23b0`
  (`Resolve source-truth archive boundary rebaseline`); the queue Milestone 2
  follow-on now strengthens that live boundary from the older `634/581`
  baseline to a governed `638/585` successor while keeping the `53`
  `currentness_supersession_archive` rows explicit lineage outside verified
  admission
- Active canonical-source truth: the live source set now proves `638/638`
  extracted `Document_Register_Master` rows on
  `source-set-3f7d4578cafb0704`; the refreshed
  `canonical-source-register-active-current-admission` boundary admits all
  `585/585` `active_review_corpus` rows while explicitly keeping `53`
  archive/currentness rows outside the verified-admission roster;
  `authority-currentness` reports
  `current_authority_source_record_count=585` and `authority_family_count=456`;
  `retrieval-build` reports `validation_passed=true`,
  `reviewer_ready=true`,
  `verified_extraction_admitted_source_count=585`,
  `verified_extraction_required_source_count=585`, and
  `verified_extraction_explicitly_non_admitted_source_count=53`; and
  `promotion-suite` again reports `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`, `expansion_ready=true`, and
  `promotion_ready=true` with `10/10` required full-canonical results passing
- Architecture gate: `462` code files, `0` above `800` lines, no Python or
  JS/TS cycles, no local module above the `20`-import fan-out gate, and the
  oversized-file inventory is empty
- Under-`800` follow-on: Milestones `0-9` are resolved; the repo remains at
  `0` oversized code files, and this packet is now historical closeout only
- The overall architecture umbrella is resolved after Milestone 10 Sequence 52.
- West Reservoir stays an explicit `typed_blocked` replay quarantine.
- Downstream gold packet status: the earlier full-canonical compliance-gold
  rebaseline remains historically resolved in commit `8e0e02b`
  (`Resolve full canonical compliance gold rebaseline`) on the pre-queue
  `source-set-f775524ab233ff27` baseline; this Milestone 2 slice did not
  rerun full-canonical claim extraction, rule-claim binding, or compliance
  review on `source-set-3f7d4578cafb0704`
- Default `compliance-gold-eval` still passes `14/14` adjudicated cases with
  `status_match_rate=1.0`, `source_record_match_rate=1.0`,
  `source_document_role_match_rate=1.0`,
  `source_claim_link_match_rate=1.0`, and
  `package_evidence_match_rate=1.0`; the five still-unmapped authorities
  remain explicit `uncertain` package-only adjudication rather than false
  source-backed misses, and `promotion_ready=false` there only because the
  base `nepa-ea-v0` rule pack is diagnostic rather than reviewer-ready
- Default `gold-coverage-eval` still passes with `7/7` required themes,
  `19/19` mapped high-priority families, `3` required review contracts,
  `2` forests, `3` package styles, `2 reviewer_ready + 1 typed_blocked`
  tracked reviews, and zero threshold failures
- Recent upstream closeout: the extraction-fidelity packet remains resolved
  locally through Milestone `4`. The dedicated
  `extraction-fidelity-eval --manifest config/extraction_fidelity_eval_v1.json --output-dir source_library`
  replay remains green with `12` governed families, `24` tracked cases,
  `matched_case_count=24`, `parser_route_mismatch_count=1`,
  `anchor_mismatch_count=13`, `span_mismatch_count=10`,
  `boundary_mismatch_count=4`, and `negative_case_pass_count=12`; the live
  `extraction-accuracy-audit --output-dir source_library --source-set-id source-set-3f7d4578cafb0704`
  rerun is now green at `585/585` admitted active-current rows with `0`
  blocked rows and `53` explicit archive/currentness rows; the narrowed
  `upstream-eval` replay remains green at `16/16`; and full-canonical
  `promotion-suite` stays green at `10/10` required full-canonical results
  with `full_canonical_source_set_id=source-set-3f7d4578cafb0704`. The
  Milestone `4` closeout itself landed in commit `abd0e4d`
  (`Resolve extraction fidelity Milestone 4`).
- Direct-file capture packet status: Milestones `0`, `1`, and `2` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  are now resolved locally. The tracked
  `config/source_register_queue_resolution_ledger_v1.json` enumerates all
  `51` queue rows, `4` are now governed `resolved` promotions
  (`FINAL-Q-HLC-001`, `FINAL-Q-HLC-002`, `FINAL-Q-HLC-003`, `PROG-010`),
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"planned":47,"resolved":4}`,
  `unresolved_current_or_project_applicable_count=45`, and the same `2`
  historical/noncurrent rows (`FPS-380`, `SUP-007`); the next routed slice
  is now Milestone `3` for export-backed families and named blockers. West
  Reservoir remains an intentional `typed_blocked` replay quarantine rather
  than a promotion blocker
- Ad hoc full-canonical `phase-eval` status: do not treat the
  `source-set-3f7d4578cafb0704` ad hoc `phase-eval` replay as the live
  promotion gate; it still lacks extraction, retrieval, claim-extraction,
  and rule-claim direct-eval coverage on the strengthened full-canonical
  source set and remains outside this packet's acceptance boundary
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
