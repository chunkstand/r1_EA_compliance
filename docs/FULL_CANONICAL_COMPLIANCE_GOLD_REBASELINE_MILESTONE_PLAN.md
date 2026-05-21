# Full Canonical Compliance Gold Rebaseline Milestone Plan

Date: 2026-05-21

Status: Active; spawned from overall architecture Milestone 10 Sequence 52

Owner context: the overall architecture umbrella is now closed on truthful routing, but the live
full-canonical gold lane remains red on the active local catalog
`source-set-f775524ab233ff27`. This packet owns the next bounded recovery.

## Purpose

Rebaseline the shipped `compliance_gold_eval` and `gold_coverage_eval` claims against the live
full-canonical source set without weakening adjudication, rule-pack, review-contract, or package-
authority gates.

## Current Evidence

- Fresh isolated replay on 2026-05-21:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52`
  finished on `source-set-f775524ab233ff27` with `passed=false`, `passed_case_count=0`,
  `failed_case_count=14`, and `failure_category_counts={"rule_claim_binding_miss": 14,
  "rule_wording_issue": 14, "source_applicability_miss": 14, "source_retrieval_miss": 14}`.
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
  isolated `compliance_gold_eval_seq52`,
  and fresh `real_package_review_coverage_eval_results.json`
  stays red only because `compliance_gold.passed=false`; it still records
  `required_theme_count=7`, `passed_theme_count=7`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_review_count=2`,
  and `typed_blocked_review_count=1` with no threshold failures.

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
- `src/usfs_r1_ea_sources/compliance_review_eval.py`
- `src/usfs_r1_ea_sources/rule_claim_binding*.py`
- `src/usfs_r1_ea_sources/applicability*.py`
- `src/usfs_r1_ea_sources/retrieval.py`
- `src/usfs_r1_ea_sources/gold_coverage_eval.py`
- `config/compliance_gold_eval_v1.json`
- `config/gold_coverage_v1.json`
- `tests/test_compliance_gold_eval.py`
- `tests/test_gold_coverage_eval.py`
- `tests/test_promotion_suite.py`

## Weak-Point Forecasts

- A historical green claim is preserved in routed docs after live replay turns red again.
- Gold coverage is made to look green by swapping in unrelated review-local gold artifacts.
- Adjudication drift is hidden by narrowing case expectations instead of proving the live source set.
- Repairing compliance gold silently regresses the already-green tracked review-contract lane.

## Required Verification

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --results-dir source_library/reviews/compliance_gold_eval_seq52
PYTHONPATH=src python - <<'PY'
# bounded gold-coverage replay using explicit results_path inputs
PY
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Stop Conditions

- Stop if the only way forward is to mark failing live canonical cases as passed without new
  adjudication.
- Stop if the packet would need to reopen the closed West Reservoir proving lane.
- Stop if fixing the full-canonical gold lane would require unplanned workbook or corpus policy
  changes that belong to a different governing packet.
