# Full Canonical Compliance Gold Rebaseline Milestone Plan

Date: 2026-05-23

Status: Resolved locally; Milestone 0 resolved 2026-05-21 through
`compliance_gold_eval_seq52_fix1` and `gold_coverage_eval_seq52_fix1`;
Milestone 1 resolved 2026-05-21 through generated-case routing repair and
owner-family split; Milestone 2 resolved 2026-05-23 through refreshed claims,
source-backed expectation scoping, and adjudicated gold-contract rebaseline;
Milestone 3 resolved 2026-05-23 through default `compliance-gold-eval`,
canonical `gold_coverage_eval`, and manifest-owned `promotion-suite`
alignment. Routed docs now reflect that the five still-unmapped live
authorities remain governed as explicit `uncertain` package-only adjudication
on `source-set-f775524ab233ff27`, default `compliance-gold-eval` passes
`14/14`, default `gold_coverage_eval` passes `7/7`, and `promotion-suite`
now reports `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
`expansion_ready=true`, and `promotion_ready=true`. The Milestone 3 closeout
commit is `8e0e02b` (`Resolve full canonical compliance gold rebaseline`).

Owner context: the overall architecture umbrella is now closed on truthful
routing, and the downstream full-canonical gold lane is now also resolved
locally on the active catalog `source-set-f775524ab233ff27`. The source-truth
packet is already resolved locally:
the latest refreshed audit and retrieval replays prove `581` required
active-current rows under
`canonical-source-register-active-current-admission`, with `581` admitted,
`0` blocked, and `reviewer_ready=true`, while the explicit full-canonical
archive boundary now preserves `53`
`currentness_supersession_archive` rows as governed lineage outside verified
admission. The upstream source-truth closeout commit is `93a23b0`
(`Resolve source-truth archive boundary rebaseline`). This packet is now a
resolved closeout reference rather than an active routed owner.

## Purpose

Rebaseline the shipped `compliance_gold_eval` and `gold_coverage_eval` claims against the live
full-canonical source set without weakening adjudication, rule-pack, review-contract, or package-
authority gates.

## Current Evidence

- Fresh claim refresh on 2026-05-23:
  `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-f775524ab233ff27`
  now records `claim_count=124458`, `source_record_count=539`,
  `validation_passed=true`, and `reviewer_ready=true`.
- Fresh default replay on 2026-05-23:
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json`
  now passes `14/14` adjudicated cases on `source-set-f775524ab233ff27`.
  The five authorities with no current canonical row remain governed as
  explicit `uncertain` package-only adjudication, so the lane no longer
  treats them as false source-backed misses. The result now records
  `authority_trace_coverage_rate=1.0`, `status_match_rate=1.0`,
  `source_record_match_rate=1.0`, `source_document_role_match_rate=1.0`,
  `source_claim_link_match_rate=1.0`, and
  `package_evidence_match_rate=1.0`, while
  `promotion_ready=false` remains explained only by
  `reviewer_ready_rule_pack=false` on the base `nepa-ea-v0` pack.
- Canonical aggregate truth on 2026-05-23:
  the default-path `gold_coverage_eval_results.json` now records
  `passed=true`, `required_theme_count=7`, `passed_theme_count=7`,
  `required_review_contract_count=3`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_review_count=2`,
  `typed_blocked_review_count=1`,
  `missing_required_review_contract_count=0`,
  `missing_package_authority_count=0`, and
  `unmapped_high_priority_family_count=0`.
- Promotion truth on 2026-05-23:
  the manifest-owned default `promotion_suite_results.json` now records
  `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `expansion_ready=true`, `promotion_ready=true`,
  `passed_required_current_result_count=32/32`,
  `passed_required_full_canonical_result_count=9/9`, and
  `failure_category_counts={}`.
- Artifact alignment truth:
  generated diagnostic gold rule packs still emit non-zero rule-claim-link
  artifacts under
  `source_library/derived/source-set-f775524ab233ff27/rule_claim_links/generated-diagnostic-*/`,
  while the base `nepa-ea-v0` summary remains a separate zero-link structural
  surface. The all-authorities-supported replay still records
  `rule_claim_link_count=200`, but that surface is now green rather than a
  routed blocker.

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
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-f775524ab233ff27
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
PYTHONPATH=src python - <<'PY'
# canonical gold-coverage replay using explicit results_path inputs that point
# at the default applicability/compliance/review-coverage artifacts
PY
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_rule_claim_binding_runtime.py tests/test_rule_claim_binding.py tests/test_ea_review.py tests/test_compliance_review_eval.py tests/test_compliance_review_contracts.py tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/compliance_review_eval.py src/usfs_r1_ea_sources/compliance_review_eval_scoring.py tests/test_compliance_review_eval.py tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src python -m compileall src
git diff --check
```

## Stop Conditions

- Stop if the only way forward is to mark failing live canonical cases as passed without new
  adjudication.
- Stop if the packet would need to reopen the closed West Reservoir proving lane.
- Stop if fixing the full-canonical gold lane would require unplanned workbook or corpus policy
  changes that belong to a different governing packet.
