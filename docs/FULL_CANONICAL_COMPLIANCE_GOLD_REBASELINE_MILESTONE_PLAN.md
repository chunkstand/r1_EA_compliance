# Full Canonical Compliance Gold Rebaseline Milestone Plan

Date: 2026-05-22

Status: Active; Milestone 0 resolved 2026-05-21 through `compliance_gold_eval_seq52_fix1` and `gold_coverage_eval_seq52_fix1`; Milestone 1 resolved 2026-05-21 through generated-case routing repair and owner-family split; Milestone 2 reduced 2026-05-21 through `compliance_gold_eval_seq52_fix6` and `gold_coverage_eval_seq52_fix6`; routed docs are aligned on the generated-vs-base rule-claim-link split, the narrower review-time source-claim drift is closed, and the packet remains active on five still-unmapped live authorities, but it is now explicitly downstream of the source-truth rebaseline packet while the live canonical admission boundary remains only `559/582` admitted current rows

Owner context: the overall architecture umbrella is now closed on truthful routing, but the live
full-canonical gold lane remains red on the active local catalog
`source-set-f775524ab233ff27`. The source-truth packet now owns the admission-boundary rebaseline:
the latest refreshed audit and retrieval replays prove `582` required active-current rows under
`canonical-source-register-active-current-admission`, with `559` admitted and `23` blocked.
This packet stays downstream while the source-truth lane resolves those remaining direct-document
gaps and re-establishes the truthful canonical target.

## Purpose

Rebaseline the shipped `compliance_gold_eval` and `gold_coverage_eval` claims against the live
full-canonical source set without weakening adjudication, rule-pack, review-contract, or package-
authority gates.

## Current Evidence

- Fresh isolated replay after the generated-case routing repair on 2026-05-21:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52_fix1`
  no longer produces the earlier `rule_claim_binding_miss` / `rule_wording_issue` /
  `source_applicability_miss` / `source_retrieval_miss` bundle. It now fails earlier because
  synthetic review `compliance-eval-gold-all-authorities-supported` cannot pass applicability
  validation: `candidate_universe_partitioned_without_unresolved_authorities` reports
  `candidate_authority_count=67`, `applicable_partition_count=0`,
  `non_applicable_partition_count=0`, and `67` unresolved candidate authorities, so
  `compliance_review_eval` does not run and `passed_case_count` remains `0/14`.
- Fresh Milestone 2 diagnostic generated-pack replay on 2026-05-21:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52_fix3`
  now drives all `14` synthetic reviews through `generated_rule_pack_diagnostic` instead of
  failing before scoring. `compliance_review_eval_error` is now `null`,
  `validation_match_rate=1.0`, and `reviewer_ready_match_rate=1.0`, but all `14` cases still
  fail closed on live all-`uncertain` findings with failure-category counts
  `{"authority_trace_coverage_miss": 14, "rule_claim_binding_miss": 14, "rule_wording_issue": 14, "source_applicability_miss": 14, "source_retrieval_miss": 14}`.
- Fresh Milestone 2 legacy/current source-record reconciliation replay on 2026-05-21:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52_fix4`
  keeps the lane red at `0/14`, but it removes the old broad canonical source-ID drift. The
  replay now records `authority_trace_coverage_rate=1.0`; aggregate finding statuses are
  `226 pass`, `166 gap`, and `268 uncertain`; and
  `gold-all-authorities-supported` now scores `39` live `pass` findings instead of collapsing to
  all `uncertain`. The remaining source-record and source-document-role mismatches are narrowed to
  the five authorities with no current canonical row:
  `apa_final_agency_action`,
  `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`,
  `organic_act_16usc_475`, and
  `seven_county_nepa_scope`.
  Review-time source-claim-link mismatches now remain on a smaller set:
  the same unresolved authorities plus
  `montana_shpo_review` as a missing positive link and
  `land_exchange_statutory_authorities_authority_template` /
  `region1_forest_plan_source_records_authority_template` as unexpected positive links.
- Fresh Milestone 2 source-claim narrowing slice on 2026-05-21:
  `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-f775524ab233ff27`
  raises the active claim summary to `claim_count=122655`, `source_record_count=548`, and
  `document_role_counts.state_requirement=298`; `STP-026` now emits `6` claims, including the
  Montana SHPO duty statements that had been missing from the live source-claim surface.
- Fresh Milestone 2 source-claim-link narrowing replay on 2026-05-21:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52_fix6`
  keeps the lane red at `0/14`, but it closes the remaining review-time generated-link drift.
  `gold-all-authorities-supported` still scores `39` live `pass` findings and `20`
  `uncertain` findings, now records `rule_claim_link_count=200`, and the only remaining
  status / claim-type / source-evidence / source-claim-link / source-record /
  source-document-role mismatches are:
  `apa_final_agency_action`,
  `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`,
  `organic_act_16usc_475`, and
  `seven_county_nepa_scope`.
- Artifact alignment truth on 2026-05-21:
  the base canonical `rule-claim-link` summary for `nepa-ea-v0/0.4.0` still records
  `link_count=0` and remains a separate zero-link structural surface, but the generated diagnostic
  gold rule packs now emit non-zero rule-claim-link artifacts under
  `source_library/derived/source-set-f775524ab233ff27/rule_claim_links/generated-diagnostic-*/`.
  The generated diagnostic all-authorities-supported summary, for example, now records
  `link_count=200`, `source_record_count=32`, and `linked_rule_count=41`. This packet therefore
  remains routed on five still-unmapped live authorities, not on a hidden generated-link collapse.
- The same isolated replay still proves the coverage contract is present:
  `coverage_tags=["cultural_tribal", "forest_plan_consistency", "land_exchange",
  "migratory_birds", "multi_forest_plan_trigger", "roadless", "water_wetlands"]` and
  `package_style_tags=["clean_baseline", "live_external_noisy", "typed_blocked_expansion"]`.
- Fresh tracked review-contract replay on 2026-05-21 remains green:
  `real-package-review-coverage-eval` passes with `covered_slot_count=3`,
  `reviewer_ready_slot_count=2`, `typed_blocked_slot_count=1`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, and `missing_package_authority_count=0`.
- Fresh bounded aggregate replay on 2026-05-21 using:
  global applicability gold results,
  isolated `compliance_gold_eval_seq52_fix6`,
  and fresh `real_package_review_coverage_eval_results.json`
  stays red only because `compliance_gold_failed=1`; it still records
  `required_theme_count=7`, `passed_theme_count=7`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_review_count=2`,
  and `typed_blocked_review_count=1` with no threshold failures.
- Fresh owner-family split on 2026-05-21:
  the generated-case routing regression and the synthetic-case early-abort path are now fixed in
  code and verified by focused tests, and the source-claim narrowing slice closes the remaining
  review-time generated-link expectation drift. The active blocker is now only the five still-
  unmapped live authorities with no current canonical row.

## Goal

Make the live full-canonical compliance gold and bounded aggregate gold results truthful and
replayable on the active source set.

Success means one of these two outcomes is proven and documented:

1. The live full-canonical pipeline is repaired until `compliance-gold-eval` and bounded
   `gold-coverage-eval` both pass on fresh outputs; or
2. The shipped gold contracts are explicitly rebaselined through adjudicated, test-covered,
   documented changes that match the live full-canonical outputs without weakening protection.

## Non-Goals

- Do not reopen the closed architecture umbrella for this lane.
- Do not reclassify West Reservoir back to reviewer-ready.
- Do not weaken gold expectations with skips, relaxed assertions, or silent contract narrowing.
- Do not change current package-authority routing or the tracked real-package slot roster unless the
  packet explicitly proves that a contract owner was wrong.

## Milestones

### Milestone 0 - Freshness Lock

Outcome label: `resolved`

1. Re-run the isolated `compliance-gold-eval` and bounded `gold-coverage-eval` replays against the
   active local catalog.
2. Record the exact source set, failure families, and bounded aggregate counts in
   `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md`.

### Milestone 1 - Failure Family Ownership

Outcome label: `resolved`

1. Separate the current red lane into owner families:
   applicability source selection,
   retrieval support,
   rule-claim binding,
   and rule-wording/adjudication drift.
2. Decide which failures are runtime regressions versus stale adjudication-contract assumptions.
3. Route any non-overlapping owner families into narrower follow-on packets if one milestone cannot
   close all four without crossing boundaries.

### Milestone 2 - Contract Or Runtime Repair

Outcome label: `resolved`

1. Repair the owning runtime surfaces or adjudicated contracts.
2. Re-run isolated `compliance-gold-eval` until the result is either green or fail-closed on an
   explicitly justified adjudication delta.
3. Re-run bounded `gold-coverage-eval` on the same fresh nested results.

### Milestone 3 - Closeout

Outcome label: `resolved`

1. Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/EVALUATION_COVERAGE_REGISTER.md`,
   this plan, and `docs/SESSION_HANDOFF.md`.
2. Record whether the live aggregate is green or remains intentionally red, why, and what packet
   owns any remaining work.
3. Commit the verified slice atomically.

## Owner Surfaces

- `src/usfs_r1_ea_sources/compliance_gold_eval.py`
- `src/usfs_r1_ea_sources/compliance_inputs.py`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/compliance_review_eval.py`
- `src/usfs_r1_ea_sources/records.py`
- `src/usfs_r1_ea_sources/rule_claim_binding*.py`
- `src/usfs_r1_ea_sources/applicability*.py`
- `src/usfs_r1_ea_sources/retrieval.py`
- `src/usfs_r1_ea_sources/gold_coverage_eval.py`
- `config/compliance_source_record_reconciliation_v1.json`
- `config/compliance_gold_eval_v1.json`
- `config/gold_coverage_v1.json`
- `tests/test_retrieval.py`
- `tests/test_rule_claim_binding_runtime.py`
- `tests/test_rule_claim_binding.py`
- `tests/test_ea_review.py`
- `tests/test_compliance_gold_eval.py`
- `tests/test_compliance_review.py`
- `tests/test_gold_coverage_eval.py`
- `tests/test_promotion_suite.py`

## Weak-Point Forecasts

- A historical green claim is preserved in routed docs after live replay turns red again.
- Gold coverage is made to look green by swapping in unrelated review-local gold artifacts.
- Adjudication drift is hidden by narrowing case expectations instead of proving the live source set.
- Repairing compliance gold silently regresses the already-green tracked review-contract lane.

## Required Verification

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52_fix4
PYTHONPATH=src python - <<'PY'
# bounded gold-coverage replay using explicit results_path inputs
PY
PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_rule_claim_binding_runtime.py tests/test_rule_claim_binding.py tests/test_ea_review.py tests/test_compliance_review_eval.py tests/test_compliance_review_contracts.py tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/records.py src/usfs_r1_ea_sources/retrieval.py src/usfs_r1_ea_sources/ea_review.py src/usfs_r1_ea_sources/rule_claim_binding_runtime.py src/usfs_r1_ea_sources/rule_claim_binding_validation.py src/usfs_r1_ea_sources/compliance_review_eval.py tests/test_retrieval.py tests/test_rule_claim_binding_runtime.py tests/test_rule_claim_binding.py tests/test_ea_review.py tests/test_compliance_review_eval.py tests/test_compliance_review_contracts.py
PYTHONPATH=src python -m compileall src
git diff --check
```

## Stop Conditions

- Stop if the only way forward is to mark failing live canonical cases as passed without new
  adjudication.
- Stop if the packet would need to reopen the closed West Reservoir proving lane.
- Stop if fixing the full-canonical gold lane would require unplanned workbook or corpus policy
  changes that belong to a different governing packet.
